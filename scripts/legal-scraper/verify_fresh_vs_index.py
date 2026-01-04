#!/usr/bin/env python
"""Verify fresh-scraped CPR JSON files against Azure Search index.

What this script checks:
1) For each local JSON, attempts to find a corresponding document in Azure Search using:
   - exact filter: sourcefile eq '<sourcefile>'
   - fallback: full-text search for sourcefile and sourcepage
2) Compares content at two levels:
   - strict: raw strings
   - normalized: whitespace/newline normalization to detect formatting-only diffs
3) Reports:
   - missing (confirmed)
   - mismatches (strict)
   - mismatches (normalized)
   - examples of formatting-only vs substantive diffs

Notes:
- Azure Search index often stores chunked docs; we compare against chunk_001 when available.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient


UPLOAD_DIR = Path(
    "/Users/HasithB/Downloads/PROJECTS/azure-search-openai-demo-2/data/legal-scraper/processed/Upload"
)
SEARCH_ENDPOINT = "https://cpr-rag.search.windows.net"
INDEX_NAME = "legal-court-rag-index"

SKIP_FILES = {"civil_procedure_rules_flattened.json", "civil_procedure_rules_review.json"}


@dataclass
class CompareResult:
    filename: str
    sourcefile: str
    sourcepage: str
    local_updated: str
    azure_updated: Optional[str]
    found: bool
    strict_match: Optional[bool]
    normalized_match: Optional[bool]
    lookup_method: Optional[str]
    azure_id: Optional[str]


def normalize_text(text: str) -> str:
    if not text:
        return ""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # collapse whitespace inside lines, trim, remove empty lines
    lines = []
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        line = re.sub(r"\s+", " ", line)
        lines.append(line)
    return "\n".join(lines)


def canonical_key(value: str) -> str:
    """Reduce a string to a comparable key (case-insensitive, alnum only)."""
    if not value:
        return ""
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def extract_identifier(value: str) -> Tuple[Optional[str], Optional[str]]:
    """Extract a stable identifier like ("part", "48") or ("pd", "5c")."""
    if not value:
        return None, None
    v = value.strip().lower()
    v = re.sub(r"\s+", " ", v)

    m = re.search(r"\bpart\s+(\d+[a-z]?)\b", v)
    if m:
        return "part", m.group(1)

    m = re.search(r"\bpractice direction\s+([0-9]+[a-z]?)\b", v)
    if m:
        return "pd", m.group(1)

    m = re.search(r"\bpra?ctice\s+direction\s+([0-9]+[a-z]?)\b", v)
    if m:
        return "pd", m.group(1)

    m = re.search(r"\bcyfarwyddyd\s+ymarfer\s+([0-9]+[a-z]?)\b", v)
    if m:
        return "pd-cy", m.group(1)

    return None, None


def load_local_docs() -> List[Dict[str, Any]]:
    docs: List[Dict[str, Any]] = []
    for p in sorted(UPLOAD_DIR.glob("*.json")):
        if p.name in SKIP_FILES:
            continue
        with p.open("r", encoding="utf-8") as f:
            docs.append(json.load(f))
    return docs


def get_local_primary_chunk(doc: Dict[str, Any]) -> Tuple[str, str]:
    """Return (chunk_id, content) for comparison."""
    if doc.get("chunks"):
        chunk0 = doc["chunks"][0]
        return str(chunk0.get("id", "")), str(chunk0.get("content", ""))
    return str(doc.get("id", "")), str(doc.get("content", ""))


def azure_exact_lookup(search_client: SearchClient, sourcefile: str) -> List[Dict[str, Any]]:
    sourcefile_escaped = sourcefile.replace("'", "''")
    return list(
        search_client.search(
            search_text="*",
            filter=f"sourcefile eq '{sourcefile_escaped}'",
            select=["id", "content", "updated", "sourcefile", "sourcepage"],
            top=50,
        )
    )


def azure_fuzzy_lookup(search_client: SearchClient, sourcefile: str, sourcepage: str) -> List[Dict[str, Any]]:
    # Use search_text to find candidates even if filter key differs.
    query_terms = [t for t in [sourcefile, sourcepage] if t]
    query = " OR ".join([f'"{t}"' for t in query_terms if len(t) <= 200])
    if not query:
        query = sourcefile

    return list(
        search_client.search(
            search_text=query,
            select=["id", "content", "updated", "sourcefile", "sourcepage"],
            top=50,
        )
    )


def score_candidate(local_sourcefile: str, local_sourcepage: str, cand: Dict[str, Any]) -> float:
    cand_sourcefile = str(cand.get("sourcefile", "") or "")
    cand_sourcepage = str(cand.get("sourcepage", "") or "")

    # If both sides have a recognisable identifier (Part/PD), require it to match.
    lt, lc = extract_identifier(local_sourcefile)
    ct, cc = extract_identifier(cand_sourcefile)
    if lt and ct and lt == ct and lc and cc and lc != cc:
        return 0.0

    # Some docs have the identifier in sourcepage rather than sourcefile.
    ct2, cc2 = extract_identifier(cand_sourcepage)
    # IMPORTANT: don't do this for "part" because source pages often reference other Parts (e.g. "Part 1 of ...").
    if lt in {"pd", "pd-cy"} and ct2 == lt and lc and cc2 and lc != cc2:
        return 0.0

    # Strong signal: canonical sourcefile matches
    if canonical_key(local_sourcefile) and canonical_key(local_sourcefile) == canonical_key(cand_sourcefile):
        return 1.0

    # Medium signal: canonical sourcepage matches
    if canonical_key(local_sourcepage) and canonical_key(local_sourcepage) == canonical_key(cand_sourcepage):
        return 0.92

    # Otherwise, approximate similarity
    import difflib

    scores: List[float] = []
    if local_sourcefile and cand_sourcefile:
        scores.append(difflib.SequenceMatcher(None, local_sourcefile.lower(), cand_sourcefile.lower()).ratio())
    if local_sourcepage and cand_sourcepage:
        scores.append(difflib.SequenceMatcher(None, local_sourcepage.lower(), cand_sourcepage.lower()).ratio())
    if local_sourcefile and cand_sourcepage:
        scores.append(difflib.SequenceMatcher(None, local_sourcefile.lower(), cand_sourcepage.lower()).ratio())
    if local_sourcepage and cand_sourcefile:
        scores.append(difflib.SequenceMatcher(None, local_sourcepage.lower(), cand_sourcefile.lower()).ratio())
    return max(scores) if scores else 0.0


def pick_best_azure_doc(
    candidates: List[Dict[str, Any]],
    desired_chunk_id: str,
    local_sourcefile: str,
    local_sourcepage: str,
    min_score: float,
) -> Optional[Dict[str, Any]]:
    if not candidates:
        return None

    # If there's an exact chunk id match, still verify it's the right document.
    for c in candidates:
        if c.get("id") == desired_chunk_id and score_candidate(local_sourcefile, local_sourcepage, c) >= min_score:
            return c

    # Otherwise pick best scoring candidate, prefer chunk_001 when scores tie.
    scored: List[Tuple[float, int, Dict[str, Any]]] = []
    for c in candidates:
        score = score_candidate(local_sourcefile, local_sourcepage, c)
        is_chunk_001 = 1 if str(c.get("id", "")).endswith("chunk_001") else 0
        scored.append((score, is_chunk_001, c))

    scored.sort(key=lambda t: (t[0], t[1]), reverse=True)
    best_score, _, best = scored[0]
    if best_score < min_score:
        return None
    return best


def main() -> int:
    if not UPLOAD_DIR.exists():
        print(f"❌ Upload dir not found: {UPLOAD_DIR}")
        return 2

    credential = DefaultAzureCredential()
    search_client = SearchClient(endpoint=SEARCH_ENDPOINT, index_name=INDEX_NAME, credential=credential)

    local_docs = load_local_docs()

    results: List[CompareResult] = []
    missing_confirmed: List[CompareResult] = []
    mismatch_substantive: List[CompareResult] = []
    mismatch_format_only: List[CompareResult] = []

    for doc in local_docs:
        sourcefile = str(doc.get("sourcefile", "")).strip()
        sourcepage = str(doc.get("sourcepage", "")).strip()
        local_updated = str(doc.get("updated", "")).strip()

        chunk_id, local_content = get_local_primary_chunk(doc)

        candidates = azure_exact_lookup(search_client, sourcefile) if sourcefile else []
        lookup_method = "exact" if candidates else None

        if not candidates:
            candidates = azure_fuzzy_lookup(search_client, sourcefile, sourcepage)
            lookup_method = "fuzzy" if candidates else None

        chosen = pick_best_azure_doc(
            candidates=candidates,
            desired_chunk_id=chunk_id,
            local_sourcefile=sourcefile,
            local_sourcepage=sourcepage,
            min_score=0.85,
        )

        if not chosen:
            r = CompareResult(
                filename=str(doc.get("sourcefile", "")),
                sourcefile=sourcefile,
                sourcepage=sourcepage,
                local_updated=local_updated,
                azure_updated=None,
                found=False,
                strict_match=None,
                normalized_match=None,
                lookup_method=lookup_method,
                azure_id=None,
            )
            results.append(r)
            missing_confirmed.append(r)
            continue

        azure_content = str(chosen.get("content", ""))
        azure_updated = chosen.get("updated")

        strict_match = local_content == azure_content
        normalized_match = normalize_text(local_content) == normalize_text(azure_content)

        r = CompareResult(
            filename=str(doc.get("sourcefile", "")),
            sourcefile=sourcefile,
            sourcepage=sourcepage,
            local_updated=local_updated,
            azure_updated=str(azure_updated) if azure_updated is not None else None,
            found=True,
            strict_match=strict_match,
            normalized_match=normalized_match,
            lookup_method=lookup_method,
            azure_id=str(chosen.get("id")) if chosen.get("id") is not None else None,
        )
        results.append(r)

        if not strict_match:
            if normalized_match:
                mismatch_format_only.append(r)
            else:
                mismatch_substantive.append(r)

    total = len(results)
    found = sum(1 for r in results if r.found)
    strict_matches = sum(1 for r in results if r.found and r.strict_match)
    norm_matches = sum(1 for r in results if r.found and r.normalized_match)

    print("\n=== Verification Summary ===")
    print(f"Total local docs checked: {total}")
    print(f"Found in Azure (any method): {found}")
    print(f"Strict matches: {strict_matches}")
    print(f"Normalized matches: {norm_matches}")
    print(f"Formatting-only mismatches (strict !=, normalized ==): {len(mismatch_format_only)}")
    print(f"Substantive mismatches (normalized !=): {len(mismatch_substantive)}")
    print(f"Missing (confirmed after fuzzy search): {len(missing_confirmed)}")

    def print_examples(title: str, items: List[CompareResult], limit: int = 10) -> None:
        if not items:
            return
        print(f"\n--- {title} (showing up to {limit}) ---")
        for r in items[:limit]:
            print(
                f"- {r.sourcefile} | local.updated={r.local_updated or 'N/A'} | azure.updated={r.azure_updated or 'N/A'} | method={r.lookup_method} | azure.id={r.azure_id}"
            )

    print_examples("Missing", missing_confirmed)
    print_examples("Formatting-only mismatches", mismatch_format_only)
    print_examples("Substantive mismatches", mismatch_substantive)

    # Save a machine-readable report
    out_path = UPLOAD_DIR.parent / "fresh_vs_index_verification.json"
    payload = [r.__dict__ for r in results]
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"\nWrote detailed results: {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
