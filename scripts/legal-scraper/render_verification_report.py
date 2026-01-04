#!/usr/bin/env python
"""Render a human-readable report from fresh_vs_index_verification.json.

Outputs:
- docs/fresh_vs_index_verification_summary.md

The JSON produced by verify_fresh_vs_index.py is intentionally compact and does
not include content diffs. This script re-loads local docs and re-fetches the
corresponding Azure documents (when available) to produce a review-friendly
markdown report with diff excerpts.
"""

from __future__ import annotations

import json
import re
import difflib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient


ROOT = Path(__file__).resolve().parents[2]
UPLOAD_DIR = ROOT / "data/legal-scraper/processed/Upload"
VERIFY_JSON = ROOT / "data/legal-scraper/processed/fresh_vs_index_verification.json"
OUT_MD = ROOT / "docs/fresh_vs_index_verification_summary.md"

SEARCH_ENDPOINT = "https://cpr-rag.search.windows.net"
INDEX_NAME = "legal-court-rag-index"

SKIP_FILES = {"civil_procedure_rules_flattened.json", "civil_procedure_rules_review.json"}


def normalize_text(text: str) -> str:
    if not text:
        return ""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = []
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        line = re.sub(r"\s+", " ", line)
        lines.append(line)
    return "\n".join(lines)


def load_local_by_sourcefile(sourcefile: str) -> Optional[Dict[str, Any]]:
    if not sourcefile:
        return None
    path = UPLOAD_DIR / f"{sourcefile}.json"
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def get_local_primary_content(doc: Dict[str, Any]) -> Tuple[str, str]:
    if doc.get("chunks"):
        chunk0 = doc["chunks"][0]
        return str(chunk0.get("id", "")), str(chunk0.get("content", ""))
    return str(doc.get("id", "")), str(doc.get("content", ""))


def fetch_azure_doc(search_client: SearchClient, doc_id: str) -> Optional[Dict[str, Any]]:
    if not doc_id:
        return None
    # Attempt direct lookup by key.
    try:
        return search_client.get_document(key=doc_id)
    except Exception:
        pass

    # Fallback: filter by id
    try:
        doc_id_escaped = doc_id.replace("'", "''")
        res = list(
            search_client.search(
                search_text="*",
                filter=f"id eq '{doc_id_escaped}'",
                select=["id", "content", "updated", "sourcefile", "sourcepage"],
                top=1,
            )
        )
        return dict(res[0]) if res else None
    except Exception:
        return None


def diff_excerpt(azure_text: str, local_text: str, max_lines: int = 80) -> str:
    a = normalize_text(azure_text).splitlines()
    b = normalize_text(local_text).splitlines()
    d = list(
        difflib.unified_diff(a, b, fromfile="Azure", tofile="Local (Fresh)", lineterm="")
    )
    if not d:
        return ""
    if len(d) > max_lines:
        d = d[:max_lines] + ["... (diff truncated)"]
    return "\n".join(d)


def md_escape(value: str) -> str:
    return (value or "").replace("|", "\\|")


def main() -> int:
    if not VERIFY_JSON.exists():
        print(f"❌ Missing verifier json: {VERIFY_JSON}")
        return 2

    credential = DefaultAzureCredential()
    search_client = SearchClient(endpoint=SEARCH_ENDPOINT, index_name=INDEX_NAME, credential=credential)

    data: List[Dict[str, Any]] = json.loads(VERIFY_JSON.read_text(encoding="utf-8"))

    total = len(data)
    found = [r for r in data if r.get("found")]
    missing = [r for r in data if not r.get("found")]
    substantive = [r for r in data if r.get("found") and r.get("normalized_match") is False]
    strict_matches = [r for r in data if r.get("found") and r.get("strict_match") is True]

    lines: List[str] = []
    lines.append("# Fresh vs Azure Index — Verification Report (Jan 4, 2026)")
    lines.append("")
    lines.append("This report is generated from `data/legal-scraper/processed/fresh_vs_index_verification.json` and re-fetches Azure documents to show diffs.")
    lines.append("")
    lines.append("## Summary")
    lines.append(f"- Total local docs checked: **{total}**")
    lines.append(f"- Found in Azure: **{len(found)}**")
    lines.append(f"- Strict matches: **{len(strict_matches)}**")
    lines.append(f"- Substantive mismatches (normalized !=): **{len(substantive)}**")
    lines.append(f"- Missing from Azure (confirmed): **{len(missing)}**")
    lines.append("")

    lines.append("## Missing from Azure (confirmed)")
    if not missing:
        lines.append("None.")
    else:
        lines.append("| sourcefile | local.updated | storageUrl |")
        lines.append("|---|---|---|")
        for r in sorted(missing, key=lambda x: (x.get("sourcefile") or "")):
            sf = str(r.get("sourcefile") or "")
            local_doc = load_local_by_sourcefile(sf)
            storage_url = str((local_doc or {}).get("storageUrl") or "")
            local_updated = str(r.get("local_updated") or "")
            lines.append(
                f"| {md_escape(sf)} | {md_escape(local_updated)} | {md_escape(storage_url)} |"
            )
    lines.append("")

    lines.append("## Substantive mismatches (normalized !=)")
    lines.append("| sourcefile | local.updated | azure.updated | lookup | azure.id |")
    lines.append("|---|---|---|---|---|")
    for r in sorted(substantive, key=lambda x: (x.get("sourcefile") or "")):
        lines.append(
            "| "
            + " | ".join(
                [
                    md_escape(str(r.get("sourcefile") or "")),
                    md_escape(str(r.get("local_updated") or "")),
                    md_escape(str(r.get("azure_updated") or "")),
                    md_escape(str(r.get("lookup_method") or "")),
                    md_escape(str(r.get("azure_id") or "")),
                ]
            )
            + " |"
        )
    lines.append("")

    lines.append("## Diff excerpts (review)")
    lines.append("Each section below shows a *truncated* unified diff between the Azure content and the local fresh scrape for the chosen Azure doc id (usually chunk 001).")
    lines.append("")

    for r in sorted(substantive, key=lambda x: (x.get("sourcefile") or "")):
        sf = str(r.get("sourcefile") or "")
        azure_id = str(r.get("azure_id") or "")
        local_doc = load_local_by_sourcefile(sf)
        if not local_doc:
            continue
        local_chunk_id, local_text = get_local_primary_content(local_doc)

        azure_doc = fetch_azure_doc(search_client, azure_id)
        if not azure_doc:
            continue

        azure_text = str(azure_doc.get("content") or "")

        excerpt = diff_excerpt(azure_text, local_text, max_lines=80)
        lines.append(f"### {sf}")
        lines.append("")
        lines.append(f"- local.updated: `{r.get('local_updated')}`")
        lines.append(f"- azure.updated: `{r.get('azure_updated')}`")
        lines.append(f"- local.chunk_id: `{local_chunk_id}`")
        lines.append(f"- azure.id: `{azure_id}`")
        lines.append("")
        if excerpt:
            lines.append("```diff")
            lines.append(excerpt)
            lines.append("```")
        else:
            lines.append("(No diff excerpt available.)")
        lines.append("")

    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"✅ Wrote report: {OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
