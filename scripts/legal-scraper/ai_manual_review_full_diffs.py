#!/usr/bin/env python
"""AI-assisted manual review over FULL diffs (not excerpt-only).

Reads:
- data/legal-scraper/processed/fresh_vs_index_verification.json (output of verify_fresh_vs_index.py)
- data/legal-scraper/processed/Upload/*.json (fresh scrape outputs)
- docs/fresh_vs_index_causality.md (live-HTML cause classification)

Fetches Azure docs by azure.id and compares normalized text line-by-line.
Outputs:
- docs/fresh_vs_index_ai_manual_review_full.md

Notes:
- This is heuristic triage. It does not call an LLM.
- It is designed to make ALL differences reviewable without opening JSON.
"""

from __future__ import annotations

import difflib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Optional

from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient


ROOT = Path(__file__).resolve().parents[2]
UPLOAD_DIR = ROOT / "data/legal-scraper/processed/Upload"
PROCESSED_DIR = ROOT / "data/legal-scraper/processed"
VERIFICATION_JSON = PROCESSED_DIR / "fresh_vs_index_verification.json"
CAUSALITY_MD = ROOT / "docs/fresh_vs_index_causality.md"
OUT_MD = ROOT / "docs/fresh_vs_index_ai_manual_review_full.md"

SEARCH_ENDPOINT = "https://cpr-rag.search.windows.net"
INDEX_NAME = "legal-court-rag-index"

SKIP_FILES = {"civil_procedure_rules_flattened.json", "civil_procedure_rules_review.json"}


@dataclass(frozen=True)
class VerificationRow:
    sourcefile: str
    sourcepage: str
    local_updated: str
    azure_updated: str
    found: bool
    strict_match: Optional[bool]
    normalized_match: Optional[bool]
    azure_id: str


@dataclass(frozen=True)
class FullDiffReview:
    sourcefile: str
    sourcepage: str
    local_updated: str
    azure_updated: str
    azure_id: str
    causality: str

    impact: str
    score: int
    signals: list[str]

    removed_count: int
    added_count: int
    change_ratio: float

    removed_top: list[str]
    added_top: list[str]


def normalize_text(text: str) -> str:
    if not text:
        return ""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines: list[str] = []
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        line = re.sub(r"\s+", " ", line)
        lines.append(line)
    return "\n".join(lines)


def parse_causality_table(md_text: str) -> dict[str, str]:
    by_sourcefile: dict[str, str] = {}
    in_table = False

    for line in md_text.splitlines():
        if line.startswith("| sourcefile | local.updated | azure.updated | classification |"):
            in_table = True
            continue
        if not in_table:
            continue

        if not line.startswith("|"):
            break
        if line.startswith("|---"):
            continue

        parts = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(parts) < 4:
            continue

        sourcefile = parts[0]
        classification = parts[3]
        if sourcefile:
            by_sourcefile[sourcefile] = classification

    return by_sourcefile


def get_local_primary_chunk(doc: dict[str, Any]) -> tuple[str, str]:
    if doc.get("chunks"):
        chunk0 = doc["chunks"][0]
        return str(chunk0.get("id", "")), str(chunk0.get("content", ""))
    return str(doc.get("id", "")), str(doc.get("content", ""))


def load_local_docs_by_sourcefile() -> dict[str, dict[str, Any]]:
    docs: dict[str, dict[str, Any]] = {}
    for p in sorted(UPLOAD_DIR.glob("*.json")):
        if p.name in SKIP_FILES:
            continue
        with p.open("r", encoding="utf-8") as f:
            d = json.load(f)
        sourcefile = str(d.get("sourcefile", "")).strip()
        if sourcefile:
            docs[sourcefile] = d
    return docs


def load_verification_rows() -> list[VerificationRow]:
    raw = json.loads(VERIFICATION_JSON.read_text(encoding="utf-8"))
    rows: list[VerificationRow] = []
    for r in raw:
        rows.append(
            VerificationRow(
                sourcefile=str(r.get("sourcefile", "") or "").strip(),
                sourcepage=str(r.get("sourcepage", "") or "").strip(),
                local_updated=str(r.get("local_updated", "") or "").strip(),
                azure_updated=str(r.get("azure_updated", "") or "").strip(),
                found=bool(r.get("found")),
                strict_match=r.get("strict_match"),
                normalized_match=r.get("normalized_match"),
                azure_id=str(r.get("azure_id", "") or "").strip(),
            )
        )
    return rows


def score_line(line: str) -> int:
    t = f" {line.lower()} "
    score = 0

    # High-signal legal mechanics
    if re.search(r"\b(must|shall)\b", t):
        score += 3
    if re.search(r"\bmay\b", t):
        score += 2
    if re.search(r"\b(within|no later|not later|at least|clear days|period of time)\b", t):
        score += 3
    if re.search(r"\b\d+\s*(day|days|month|months|hour|hours|week|weeks)\b", t):
        score += 3

    if re.search(r"\b(service|served|notice|deemed service)\b", t):
        score += 2
    if re.search(r"\b(cost|costs|assessment)\b", t):
        score += 2
    if re.search(r"\b(appeal|permission)\b", t):
        score += 2
    if re.search(r"\b(disclosure|inspection)\b", t):
        score += 2
    if re.search(r"\b(disapply|modify|var(y|ied|ies))\b", t):
        score += 2

    # Tech / procedure changes
    if re.search(r"\b(electronic filing|e-?file|portal|online|case management system)\b", t):
        score += 1

    # Pure citations tend to be lower value unless paired with other signals
    if re.fullmatch(r"\s*\(?[0-9]+\.?[0-9a-zA-Z().\- ]*\)?\s*", line.strip()):
        score -= 1

    # Longer lines are often substantive
    if len(line) >= 140:
        score += 1

    return max(score, 0)


def score_impact(removed: list[str], added: list[str], local_updated: str, azure_updated: str) -> tuple[int, list[str]]:
    signals: list[str] = []
    score = 0

    def bump(cond: bool, points: int, signal: str) -> None:
        nonlocal score
        if cond:
            score += points
            signals.append(signal)

    bump(local_updated and azure_updated and local_updated != azure_updated, 3, "updated date differs (local vs azure)")

    # Summarise strongest diff-line signals
    top_removed_score = max((score_line(s) for s in removed), default=0)
    top_added_score = max((score_line(s) for s in added), default=0)
    bump(top_removed_score >= 5 or top_added_score >= 5, 3, "high-signal procedural language changed")
    bump(top_removed_score >= 3 or top_added_score >= 3, 2, "moderate-signal legal language changed")

    # Broad themes from the union of lines
    text = "\n".join(removed + added).lower()
    bump(bool(re.search(r"\b(service|served|notice)\b", text)), 2, "service/notice mechanics changed")
    bump(bool(re.search(r"\b(cost|costs|assessment)\b", text)), 2, "costs/assessment mechanics changed")
    bump(bool(re.search(r"\b(appeal|permission)\b", text)), 2, "appeals/permission mechanics changed")
    bump(bool(re.search(r"\b(disclosure|inspection)\b", text)), 2, "disclosure/inspection mechanics changed")
    bump(bool(re.search(r"\b(within|no later|not later|clear days)\b", text)), 2, "time-limit language changed")

    return score, signals


def impact_label(score: int) -> str:
    if score >= 9:
        return "HIGH"
    if score >= 5:
        return "MEDIUM"
    return "LOW"


def iter_change_lines(azure_lines: list[str], local_lines: list[str]) -> tuple[list[str], list[str]]:
    """Return (removed_from_azure, added_in_local) using ndiff."""
    removed: list[str] = []
    added: list[str] = []

    for d in difflib.ndiff(azure_lines, local_lines):
        # ndiff prefixes: '  ' equal, '- ' azure-only, '+ ' local-only, '? ' intraline hints
        if d.startswith("- "):
            s = d[2:].strip()
            if s:
                removed.append(s)
        elif d.startswith("+ "):
            s = d[2:].strip()
            if s:
                added.append(s)

    return removed, added


def top_k_by_signal(lines: list[str], k: int) -> list[str]:
    # Prefer high-signal lines; tie-breaker by length.
    scored = [(score_line(s), len(s), s) for s in lines]
    scored.sort(key=lambda t: (t[0], t[1]), reverse=True)
    top = [s for _, _, s in scored[:k] if s]

    # De-duplicate while preserving order
    seen: set[str] = set()
    out: list[str] = []
    for s in top:
        key = s.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(s)
    return out


def safe_get_document(search_client: SearchClient, azure_id: str) -> Optional[dict[str, Any]]:
    if not azure_id:
        return None
    try:
        return search_client.get_document(key=azure_id, selected_fields=["id", "content", "updated", "sourcefile", "sourcepage"])
    except Exception:
        # Fallback: try a search by id.
        try:
            hits = list(
                search_client.search(
                    search_text="*",
                    filter=f"id eq '{azure_id.replace("'", "''")}'",
                    select=["id", "content", "updated", "sourcefile", "sourcepage"],
                    top=1,
                )
            )
            return hits[0] if hits else None
        except Exception:
            return None


def render_markdown(reviews: list[FullDiffReview], missing: list[VerificationRow]) -> str:
    by_impact: dict[str, int] = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    by_cause: dict[str, int] = {}

    for r in reviews:
        by_impact[r.impact] += 1
        by_cause[r.causality] = by_cause.get(r.causality, 0) + 1

    lines: list[str] = []
    lines.append("# AI Manual Review — FULL Diffs (Jan 4, 2026)")
    lines.append("")
    lines.append(
        "This report is an automated, AI-assisted triage over the FULL normalized Azure-vs-local text (not excerpt-only). It does not call an LLM and is not legal advice."
    )
    lines.append("")

    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Substantive mismatches reviewed: **{len(reviews)}**")
    lines.append(f"- Missing in Azure (confirmed): **{len(missing)}**")
    lines.append(f"- Impact split: **{by_impact['HIGH']} HIGH**, **{by_impact['MEDIUM']} MEDIUM**, **{by_impact['LOW']} LOW**")
    if by_cause:
        lines.append("- Causality split (from live-HTML check):")
        for k, v in sorted(by_cause.items(), key=lambda kv: (-kv[1], kv[0])):
            lines.append(f"  - **{v}**: {k}")
    lines.append("")

    lines.append("## A. Mismatches — Triage Table")
    lines.append("")
    lines.append("| sourcefile | impact | cause | removed | added | change.ratio | local.updated | azure.updated | azure.id |")
    lines.append("|---|---:|---|---:|---:|---:|---:|---:|---|")
    for r in reviews:
        lines.append(
            f"| {r.sourcefile} | {r.impact} | {r.causality} | {r.removed_count} | {r.added_count} | {r.change_ratio:.3f} | {r.local_updated} | {r.azure_updated} | {r.azure_id} |"
        )
    lines.append("")

    lines.append("## B. Mismatches — Per-Document Notes")
    lines.append("")
    for r in reviews:
        lines.append(f"### {r.sourcefile}")
        lines.append("")
        lines.append(f"- Impact: **{r.impact}** (score {r.score})")
        lines.append(f"- Cause (live-HTML heuristic): {r.causality}")
        lines.append(f"- sourcepage: `{r.sourcepage}`")
        lines.append(f"- local.updated: `{r.local_updated}`")
        lines.append(f"- azure.updated: `{r.azure_updated}`")
        if r.azure_id:
            lines.append(f"- azure.id: `{r.azure_id}`")
        if r.signals:
            lines.append(f"- Signals: {', '.join(r.signals)}")
        lines.append(f"- Full-diff stats: removed={r.removed_count}, added={r.added_count}, change.ratio={r.change_ratio:.3f}")
        lines.append("")

        if r.removed_top:
            lines.append("Top removed (Azure-only) lines:")
            for s in r.removed_top[:10]:
                lines.append(f"- {s}")
            lines.append("")

        if r.added_top:
            lines.append("Top added (Local-only) lines:")
            for s in r.added_top[:10]:
                lines.append(f"- {s}")
            lines.append("")

        if r.causality == "website_changed (live matches local)":
            lines.append("Recommended action: update/re-index the Azure document(s) from the fresh scrape for this sourcefile.")
        elif r.causality == "scraper/extraction issue (live matches azure)":
            lines.append("Recommended action: inspect the scraper extraction for this page; the live page looked closer to Azure than to local.")
        else:
            lines.append("Recommended action: manually spot-check live `storageUrl` vs Azure content; then decide whether to re-index or adjust extraction.")
        lines.append("")

    lines.append("## C. Missing in Azure (confirmed)")
    lines.append("")
    lines.append("These have no matching `sourcefile` found in the Azure index (per verifier).")
    lines.append("")
    lines.append("| sourcefile | sourcepage | local.updated |")
    lines.append("|---|---|---:|")
    for m in missing:
        lines.append(f"| {m.sourcefile} | {m.sourcepage} | {m.local_updated} |")
    lines.append("")
    lines.append("Recommended action: ingest/upload these into the Azure index (staging first if you have that workflow), then re-run the verifier.")
    lines.append("")

    return "\n".join(lines) + "\n"


def main() -> int:
    if not VERIFICATION_JSON.exists():
        raise SystemExit(f"Missing verification JSON: {VERIFICATION_JSON}")
    if not UPLOAD_DIR.exists():
        raise SystemExit(f"Missing Upload dir: {UPLOAD_DIR}")

    causality_by_sourcefile: dict[str, str] = {}
    if CAUSALITY_MD.exists():
        causality_by_sourcefile = parse_causality_table(CAUSALITY_MD.read_text(encoding="utf-8"))

    local_by_sourcefile = load_local_docs_by_sourcefile()
    verification_rows = load_verification_rows()

    mismatches = [r for r in verification_rows if r.found and r.normalized_match is False]
    missing = [r for r in verification_rows if not r.found]

    credential = DefaultAzureCredential()
    search_client = SearchClient(endpoint=SEARCH_ENDPOINT, index_name=INDEX_NAME, credential=credential)

    reviews: list[FullDiffReview] = []

    for r in mismatches:
        local_doc = local_by_sourcefile.get(r.sourcefile)
        if not local_doc:
            # Shouldn't happen, but keep the report moving.
            local_content = ""
        else:
            _, local_content = get_local_primary_chunk(local_doc)

        azure_doc = safe_get_document(search_client, r.azure_id)
        azure_content = str((azure_doc or {}).get("content", ""))

        local_norm = normalize_text(local_content)
        azure_norm = normalize_text(azure_content)

        local_lines = local_norm.splitlines()
        azure_lines = azure_norm.splitlines()

        removed, added = iter_change_lines(azure_lines=azure_lines, local_lines=local_lines)

        removed_top = top_k_by_signal(removed, k=12)
        added_top = top_k_by_signal(added, k=12)

        score, signals = score_impact(removed_top, added_top, r.local_updated, r.azure_updated)

        # incorporate overall magnitude (but keep it bounded)
        magnitude = min((len(removed) + len(added)) // 40, 4)
        if magnitude:
            score += magnitude
            signals.append(f"diff magnitude (removed+added lines) ~= {len(removed)+len(added)}")

        impact = impact_label(score)

        denom = max(len(local_lines), len(azure_lines), 1)
        change_ratio = (len(removed) + len(added)) / denom

        causality = causality_by_sourcefile.get(r.sourcefile, "unknown")

        reviews.append(
            FullDiffReview(
                sourcefile=r.sourcefile,
                sourcepage=r.sourcepage,
                local_updated=r.local_updated,
                azure_updated=r.azure_updated,
                azure_id=r.azure_id,
                causality=causality,
                impact=impact,
                score=score,
                signals=signals,
                removed_count=len(removed),
                added_count=len(added),
                change_ratio=change_ratio,
                removed_top=removed_top,
                added_top=added_top,
            )
        )

    # Sort: highest impact, then biggest change, then name.
    impact_rank = {"HIGH": 2, "MEDIUM": 1, "LOW": 0}
    reviews.sort(key=lambda x: (impact_rank.get(x.impact, -1), x.change_ratio, x.score, x.sourcefile), reverse=True)

    OUT_MD.write_text(render_markdown(reviews, missing), encoding="utf-8")

    print(f"Wrote {OUT_MD} ({len(reviews)} mismatches, {len(missing)} missing)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
