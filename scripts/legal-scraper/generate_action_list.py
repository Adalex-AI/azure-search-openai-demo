import json
from pathlib import Path
from typing import Any


def parse_causality_table(causality_md: str) -> dict[str, dict[str, str]]:
    rows: list[dict[str, str]] = []
    in_table = False

    for line in causality_md.splitlines():
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

        sourcefile, local_updated, azure_updated, classification = parts[:4]
        rows.append(
            {
                "sourcefile": sourcefile,
                "local_updated": local_updated,
                "azure_updated": azure_updated,
                "classification": classification,
            }
        )

    return {r["sourcefile"]: r for r in rows}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def build_storage_url_map(upload_dir: Path) -> dict[str, str]:
    storage_by_sourcefile: dict[str, str] = {}

    if not upload_dir.exists():
        return storage_by_sourcefile

    for p in upload_dir.glob("*.json"):
        try:
            doc = load_json(p)
        except Exception:
            continue

        if not isinstance(doc, dict):
            continue

        sourcefile = doc.get("sourcefile")
        storage_url = doc.get("storageUrl")
        if isinstance(sourcefile, str) and isinstance(storage_url, str) and sourcefile and storage_url:
            storage_by_sourcefile.setdefault(sourcefile, storage_url)

    return storage_by_sourcefile


def render_mismatch_table(items: list[dict[str, str]]) -> list[str]:
    if not items:
        return ["_None_"]

    lines = [
        "| sourcefile | local.updated | azure.updated | azure id | storageUrl |",
        "|---|---:|---:|---|---|",
    ]
    for it in items:
        lines.append(
            f"| {it['sourcefile']} | {it['local_updated']} | {it['azure_updated']} | {it['azure_id']} | {it['storageUrl']} |"
        )
    return lines


def main() -> None:
    causality_path = Path("docs/fresh_vs_index_causality.md")
    verification_path = Path("data/legal-scraper/processed/fresh_vs_index_verification.json")
    upload_dir = Path("data/legal-scraper/processed/Upload")
    out_path = Path("docs/fresh_vs_index_action_list.md")

    causality_by_sourcefile = parse_causality_table(causality_path.read_text(encoding="utf-8"))

    verification = load_json(verification_path)
    if not isinstance(verification, list):
        raise SystemExit("Verification JSON format unexpected (expected list)")

    storage_by_sourcefile = build_storage_url_map(upload_dir)

    checked = len(verification)
    found = sum(1 for r in verification if r.get("found") is True)
    strict_matches = sum(
        1 for r in verification if r.get("found") is True and r.get("strict_match") is True
    )
    substantive_mismatches = sum(
        1 for r in verification if r.get("found") is True and r.get("strict_match") is False
    )

    missing = [r for r in verification if r.get("found") is False]
    mismatches = [r for r in verification if r.get("found") is True and r.get("strict_match") is False]

    website_changed: list[dict[str, str]] = []
    scraper_issue: list[dict[str, str]] = []
    inconclusive: list[dict[str, str]] = []

    for r in mismatches:
        sourcefile = r.get("sourcefile")
        if not isinstance(sourcefile, str) or not sourcefile:
            continue

        causality = causality_by_sourcefile.get(sourcefile, {})
        classification = causality.get("classification", "mixed_or_inconclusive")

        item = {
            "sourcefile": sourcefile,
            "local_updated": r.get("local_updated") or causality.get("local_updated") or "",
            "azure_updated": r.get("azure_updated") or causality.get("azure_updated") or "",
            "azure_id": r.get("azure_id") or "",
            "storageUrl": storage_by_sourcefile.get(sourcefile, ""),
        }

        if classification == "website_changed (live matches local)":
            website_changed.append(item)
        elif classification == "scraper/extraction issue (live matches azure)":
            scraper_issue.append(item)
        else:
            inconclusive.append(item)

    website_changed.sort(key=lambda x: x["sourcefile"].lower())
    scraper_issue.sort(key=lambda x: x["sourcefile"].lower())
    inconclusive.sort(key=lambda x: x["sourcefile"].lower())
    missing.sort(key=lambda x: (x.get("sourcefile") or "").lower())

    lines: list[str] = []
    lines.append("# Fresh Scrape -> Azure Index: Action List")
    lines.append("")
    lines.append("This file turns the verification + causality reports into a concrete remediation checklist.")
    lines.append("")
    lines.append("## Snapshot")
    lines.append("")
    lines.append(f"- Checked: **{checked}**")
    lines.append(f"- Found in Azure: **{found}**")
    lines.append(f"- Strict matches: **{strict_matches}**")
    lines.append(f"- Substantive mismatches: **{substantive_mismatches}**")
    lines.append(f"- Missing in Azure: **{len(missing)}**")
    lines.append("")
    lines.append("Source reports:")
    lines.append("- Causality: `docs/fresh_vs_index_causality.md`")
    lines.append("- Verification: `docs/fresh_vs_index_verification_summary.md`")
    lines.append("")

    lines.append("## A. Update Azure Index (live matches local)")
    lines.append("These look like genuine website text drift relative to what is currently indexed.")
    lines.append("")
    lines.append(f"Count: **{len(website_changed)}**")
    lines.append("")
    lines.extend(render_mismatch_table(website_changed))
    lines.append("")

    lines.append("## B. Investigate Scraper/Extraction (live matches azure)")
    lines.append("These are candidates for scraper logic issues or extraction differences.")
    lines.append("")
    lines.append(f"Count: **{len(scraper_issue)}**")
    lines.append("")
    lines.extend(render_mismatch_table(scraper_issue))
    lines.append("")

    lines.append("## C. Needs Manual Confirmation (mixed/inconclusive)")
    lines.append("The heuristic did not find strong signal lines; review before changing the index or scraper.")
    lines.append("")
    lines.append(f"Count: **{len(inconclusive)}**")
    lines.append("")
    lines.extend(render_mismatch_table(inconclusive))
    lines.append("")

    lines.append("## D. Missing in Azure Index")
    lines.append("These sourcefiles were not found in the Azure index during verification.")
    lines.append("")
    lines.append(f"Count: **{len(missing)}**")
    lines.append("")
    if missing:
        lines.append("| sourcefile | local.updated | storageUrl |")
        lines.append("|---|---:|---|")
        for r in missing:
            sourcefile = r.get("sourcefile") or ""
            local_updated = r.get("local_updated") or ""
            lines.append(f"| {sourcefile} | {local_updated} | {storage_by_sourcefile.get(sourcefile, '')} |")
    else:
        lines.append("_None_")
    lines.append("")

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(
        f"Wrote {out_path} (A={len(website_changed)}, B={len(scraper_issue)}, C={len(inconclusive)}, D={len(missing)})"
    )


if __name__ == "__main__":
    main()
