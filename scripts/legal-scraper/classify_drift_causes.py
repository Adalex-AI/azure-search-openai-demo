#!/usr/bin/env python
"""Classify Azure-vs-local mismatches as likely website-change vs scraper/extraction issue.

Method (heuristic):
- For each substantive mismatch (normalized content differs), compute a unified diff
  between Azure content and local content (normalized).
- Extract a handful of representative removed lines (Azure-only) and added lines (Local-only).
- Fetch live HTML from the local document's storageUrl.
- Convert HTML -> visible text, normalize.
- Check presence of those lines in live HTML text.

Classification:
- website_changed: local-added lines appear in live HTML and azure-removed do not.
- scraper_issue_or_extraction: azure-removed lines appear and local-added do not.
- mixed_or_inconclusive: otherwise.

Outputs:
- docs/fresh_vs_index_causality.md
"""

from __future__ import annotations

import difflib
import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup
from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient


ROOT = Path(__file__).resolve().parents[2]
UPLOAD_DIR = ROOT / "data/legal-scraper/processed/Upload"
VERIFY_JSON = ROOT / "data/legal-scraper/processed/fresh_vs_index_verification.json"
OUT_MD = ROOT / "docs/fresh_vs_index_causality.md"

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


def load_local_doc(sourcefile: str) -> Optional[Dict[str, Any]]:
    path = UPLOAD_DIR / f"{sourcefile}.json"
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def get_local_primary_content(doc: Dict[str, Any]) -> str:
    if doc.get("chunks"):
        return str(doc["chunks"][0].get("content", ""))
    return str(doc.get("content", ""))


def fetch_azure_doc(search_client: SearchClient, doc_id: str) -> Optional[Dict[str, Any]]:
    if not doc_id:
        return None
    try:
        return search_client.get_document(key=doc_id)
    except Exception:
        pass
    # fallback filter
    doc_id_escaped = doc_id.replace("'", "''")
    try:
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


def pick_signal_lines(azure_text: str, local_text: str, max_each: int = 4) -> Tuple[List[str], List[str]]:
    a = normalize_text(azure_text).splitlines()
    b = normalize_text(local_text).splitlines()

    diff = difflib.unified_diff(a, b, lineterm="")

    removed: List[str] = []
    added: List[str] = []

    for line in diff:
        if line.startswith("---") or line.startswith("+++") or line.startswith("@@"):
            continue
        if line.startswith("-") and not line.startswith("---"):
            content = line[1:].strip()
            if content and len(content) >= 25:
                removed.append(content)
        elif line.startswith("+") and not line.startswith("+++"):
            content = line[1:].strip()
            if content and len(content) >= 25:
                added.append(content)

        if len(removed) >= max_each and len(added) >= max_each:
            break

    # De-dup while preserving order
    def dedup(xs: List[str]) -> List[str]:
        seen = set()
        out = []
        for x in xs:
            k = x.lower()
            if k in seen:
                continue
            seen.add(k)
            out.append(x)
        return out

    return dedup(removed)[:max_each], dedup(added)[:max_each]


def html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    # Remove script/style
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = soup.get_text("\n")
    return normalize_text(text)


def fetch_live_text(url: str, timeout: int = 30) -> Optional[str]:
    if not url:
        return None
    try:
        resp = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        return html_to_text(resp.text)
    except Exception:
        return None


def presence_score(live_text: str, lines: List[str]) -> int:
    if not live_text:
        return 0
    score = 0
    for line in lines:
        # Use a shorter probe to reduce false negatives when punctuation differs
        probe = line
        if len(probe) > 160:
            probe = probe[:160]
        probe = re.sub(r"\s+", " ", probe).strip()
        if len(probe) < 20:
            continue
        if probe.lower() in live_text.lower():
            score += 1
    return score


def classify(removed_hits: int, added_hits: int, removed_total: int, added_total: int) -> str:
    # Avoid dividing; just use simple thresholds.
    if added_total and (added_hits >= max(1, added_total // 2)) and (removed_hits == 0 or removed_hits < added_hits):
        return "website_changed (live matches local)"
    if removed_total and (removed_hits >= max(1, removed_total // 2)) and (added_hits == 0 or added_hits < removed_hits):
        return "scraper/extraction issue (live matches azure)"
    return "mixed_or_inconclusive"


def main() -> int:
    if not VERIFY_JSON.exists():
        print(f"❌ Missing: {VERIFY_JSON}")
        return 2

    credential = DefaultAzureCredential()
    search_client = SearchClient(endpoint=SEARCH_ENDPOINT, index_name=INDEX_NAME, credential=credential)

    rows: List[Dict[str, Any]] = json.loads(VERIFY_JSON.read_text(encoding="utf-8"))
    mismatches = [r for r in rows if r.get("found") and r.get("normalized_match") is False]
    missing = [r for r in rows if not r.get("found")]

    md: List[str] = []
    md.append("# Fresh vs Azure Index — Cause Analysis (Jan 4, 2026)")
    md.append("")
    md.append("This report attempts to distinguish **website changes** vs **scraper/extraction differences**.")
    md.append("Heuristic: fetch current HTML from `storageUrl` and check whether the diff lines appear in live HTML text.")
    md.append("")
    md.append("## Summary")
    md.append(f"- Substantive mismatches analyzed: **{len(mismatches)}**")
    md.append(f"- Missing from Azure (confirmed): **{len(missing)}**")
    md.append("")

    md.append("## Missing from Azure")
    md.append("These are **index coverage gaps** (not a scraper vs HTML question).")
    md.append("| sourcefile | local.updated | storageUrl |")
    md.append("|---|---|---|")
    for r in sorted(missing, key=lambda x: (x.get("sourcefile") or "")):
        sf = str(r.get("sourcefile") or "")
        local_doc = load_local_doc(sf) or {}
        md.append(f"| {sf} | {local_doc.get('updated','')} | {local_doc.get('storageUrl','')} |")
    md.append("")

    md.append("## Mismatch classifications")
    md.append("| sourcefile | local.updated | azure.updated | classification | added_hits | removed_hits | live_url_ok |")
    md.append("|---|---|---|---|---:|---:|---|")

    details: List[Tuple[str, List[str]]] = []

    for r in sorted(mismatches, key=lambda x: (x.get("sourcefile") or "")):
        sf = str(r.get("sourcefile") or "")
        local_doc = load_local_doc(sf)
        if not local_doc:
            continue
        url = str(local_doc.get("storageUrl") or "")
        local_updated = str(local_doc.get("updated") or "")
        azure_updated = str(r.get("azure_updated") or "")
        azure_id = str(r.get("azure_id") or "")

        azure_doc = fetch_azure_doc(search_client, azure_id)
        if not azure_doc:
            continue

        azure_text = str(azure_doc.get("content") or "")
        local_text = get_local_primary_content(local_doc)

        removed_lines, added_lines = pick_signal_lines(azure_text, local_text, max_each=4)

        live_text = fetch_live_text(url)
        live_ok = "yes" if live_text else "no"

        removed_hits = presence_score(live_text or "", removed_lines)
        added_hits = presence_score(live_text or "", added_lines)

        classification = classify(removed_hits, added_hits, len(removed_lines), len(added_lines))

        md.append(
            f"| {sf} | {local_updated} | {azure_updated} | {classification} | {added_hits}/{len(added_lines)} | {removed_hits}/{len(removed_lines)} | {live_ok} |"
        )

        # Add a short per-doc detail section for review
        det: List[str] = []
        det.append(f"### {sf}")
        det.append("")
        det.append(f"- storageUrl: {url}")
        det.append(f"- local.updated: `{local_updated}`")
        det.append(f"- azure.updated: `{azure_updated}`")
        det.append(f"- classification: **{classification}**")
        det.append("")
        if added_lines:
            det.append("Local-only signal lines (should appear in live HTML if website changed):")
            for x in added_lines:
                det.append(f"- {x}")
            det.append("")
        if removed_lines:
            det.append("Azure-only signal lines (should appear in live HTML if scraper issue):")
            for x in removed_lines:
                det.append(f"- {x}")
            det.append("")
        details.append((sf, det))

        # Be polite to the MoJ site
        time.sleep(0.3)

    md.append("")
    md.append("## Per-document details")
    md.append("(Signal lines are truncated/heuristic; use as indicators, not proof.)")
    md.append("")
    for _, det in details:
        md.extend(det)
        md.append("")

    OUT_MD.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"✅ Wrote: {OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
