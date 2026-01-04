#!/usr/bin/env python
"""Update Azure AI Search documents from fresh-scraped CPR outputs.

Purpose
- Bring the Azure Search index content in sync with the latest local scrape under
  data/legal-scraper/processed/Upload.

What it updates
- Only the sourcefiles that are either:
  - substantive mismatches (normalized_match == False)
  - missing (found == False)
  as recorded in data/legal-scraper/processed/fresh_vs_index_verification.json

How it updates
- For each affected sourcefile:
  - fetch existing Azure docs by `sourcefile` (typically chunked: *_chunk_###)
  - update every chunk where a local chunk exists with the same chunk suffix
  - create missing chunks if Azure doesn't already have them

Notes
- Uses `merge_or_upload_documents` so it won't wipe other fields.
- Does NOT generate embeddings. If your index relies on precomputed vectors,
  embeddings will remain as-is for updated docs unless your index/vectorizer/indexer recomputes them.

Defaults
- Endpoint: https://cpr-rag.search.windows.net
- Index: legal-court-rag-index

You can override via env vars:
- AZURE_SEARCH_ENDPOINT
- AZURE_SEARCH_INDEX
"""

from __future__ import annotations

import json
import os
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

SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT", "https://cpr-rag.search.windows.net")
INDEX_NAME = os.getenv("AZURE_SEARCH_INDEX", "legal-court-rag-index")

SKIP_FILES = {"civil_procedure_rules_flattened.json", "civil_procedure_rules_review.json"}

CHUNK_SUFFIX_RE = re.compile(r"chunk_\d{3}$", flags=re.IGNORECASE)


@dataclass(frozen=True)
class VerificationRow:
    sourcefile: str
    found: bool
    normalized_match: Optional[bool]
    azure_id: str


def sanitize_id(value: str) -> str:
    """Sanitize a doc id so Azure Search accepts it reliably."""
    if not value:
        return value
    s = re.sub(r"[^A-Za-z0-9_\-=]+", "_", value)
    s = re.sub(r"_+", "_", s).strip("_")
    return s


def chunk_suffix(doc_id: str) -> Optional[str]:
    if not doc_id:
        return None
    m = re.search(r"chunk_\d{3}$", doc_id, flags=re.IGNORECASE)
    return m.group(0).lower() if m else None


def load_verification_rows() -> list[VerificationRow]:
    raw = json.loads(VERIFICATION_JSON.read_text(encoding="utf-8"))
    rows: list[VerificationRow] = []
    for r in raw:
        rows.append(
            VerificationRow(
                sourcefile=str(r.get("sourcefile", "") or "").strip(),
                found=bool(r.get("found")),
                normalized_match=r.get("normalized_match"),
                azure_id=str(r.get("azure_id", "") or "").strip(),
            )
        )
    return rows


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


def iter_local_chunks(doc: dict[str, Any]) -> Iterable[dict[str, Any]]:
    """Yield chunk-like dicts each with id/content."""
    chunks = doc.get("chunks")
    if isinstance(chunks, list) and chunks:
        for c in chunks:
            if isinstance(c, dict) and c.get("id") and c.get("content"):
                yield {"id": str(c.get("id")), "content": str(c.get("content"))}
        return

    # Fallback to top-level single-doc
    if doc.get("id") and doc.get("content"):
        yield {"id": str(doc.get("id")), "content": str(doc.get("content"))}


def azure_docs_for_sourcefile(search_client: SearchClient, sourcefile: str) -> list[dict[str, Any]]:
    sf = sourcefile.replace("'", "''")
    return list(
        search_client.search(
            search_text="*",
            filter=f"sourcefile eq '{sf}'",
            select=["id", "sourcefile", "sourcepage", "storageUrl", "category", "updated", "parent_id"],
            top=200,
        )
    )


def main() -> int:
    if not VERIFICATION_JSON.exists():
        raise SystemExit(f"Missing verification JSON: {VERIFICATION_JSON}")
    if not UPLOAD_DIR.exists():
        raise SystemExit(f"Missing Upload dir: {UPLOAD_DIR}")

    local_by_sourcefile = load_local_docs_by_sourcefile()
    verification_rows = load_verification_rows()

    target_sourcefiles: set[str] = set()
    for r in verification_rows:
        if not r.sourcefile:
            continue
        if not r.found:
            target_sourcefiles.add(r.sourcefile)
        elif r.normalized_match is False:
            target_sourcefiles.add(r.sourcefile)

    if not target_sourcefiles:
        print("No mismatches/missing found in verification JSON; nothing to update.")
        return 0

    credential = DefaultAzureCredential()
    search_client = SearchClient(endpoint=SEARCH_ENDPOINT, index_name=INDEX_NAME, credential=credential)

    total_updates = 0
    total_sourcefiles = 0

    for sourcefile in sorted(target_sourcefiles):
        local_doc = local_by_sourcefile.get(sourcefile)
        if not local_doc:
            print(f"⚠️  Local doc not found for sourcefile: {sourcefile}")
            continue

        azure_docs = azure_docs_for_sourcefile(search_client, sourcefile)
        azure_by_suffix: dict[str, str] = {}
        for a in azure_docs:
            aid = str(a.get("id", "") or "")
            suf = chunk_suffix(aid)
            if suf:
                azure_by_suffix[suf] = aid

        # Common metadata (use local)
        base = {
            "sourcefile": str(local_doc.get("sourcefile", "") or ""),
            "sourcepage": str(local_doc.get("sourcepage", "") or ""),
            "storageUrl": str(local_doc.get("storageUrl", "") or ""),
            "category": str(local_doc.get("category", "") or ""),
            "updated": str(local_doc.get("updated", "") or ""),
            "parent_id": str(local_doc.get("parent_id", "") or ""),
            # Preserve ACL fields if present
            "oids": local_doc.get("oids") or [],
            "groups": local_doc.get("groups") or [],
        }

        updates: list[dict[str, Any]] = []
        for c in iter_local_chunks(local_doc):
            local_id = str(c.get("id", ""))
            suf = chunk_suffix(local_id) or "chunk_001"
            azure_id = azure_by_suffix.get(suf)

            # If Azure has an existing doc for this chunk suffix, update it; otherwise create a new id.
            if not azure_id:
                azure_id = sanitize_id(local_id)
                if not CHUNK_SUFFIX_RE.search(azure_id):
                    azure_id = f"{azure_id}_{suf}"

            updates.append({"id": azure_id, "content": str(c.get("content", "")), **base})

        # Batch merge-or-upload
        if not updates:
            print(f"⚠️  No chunks found to update for sourcefile: {sourcefile}")
            continue

        # Azure SDK prefers <= 1000 but keep conservative
        batch_size = 100
        uploaded_for_source = 0
        for i in range(0, len(updates), batch_size):
            batch = updates[i : i + batch_size]
            results = search_client.merge_or_upload_documents(batch)
            succeeded = sum(1 for r in results if getattr(r, "succeeded", False))
            failed = [r for r in results if not getattr(r, "succeeded", False)]
            uploaded_for_source += succeeded
            total_updates += succeeded
            if failed:
                first = failed[0]
                msg = getattr(first, "error_message", "") or getattr(first, "error", "")
                print(f"❌ {sourcefile}: {len(failed)} failed in batch; example: {msg}")

        total_sourcefiles += 1
        print(f"✅ Updated {uploaded_for_source} docs for {sourcefile} (azure had {len(azure_docs)} docs)")

    print(f"\nDone. Updated docs: {total_updates} across {total_sourcefiles} sourcefiles")
    print(f"Endpoint: {SEARCH_ENDPOINT}")
    print(f"Index: {INDEX_NAME}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
