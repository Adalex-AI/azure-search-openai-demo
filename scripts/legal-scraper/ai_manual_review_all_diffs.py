import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class DiffReview:
    sourcefile: str
    local_updated: str
    azure_updated: str
    azure_id: str
    causality: str
    impact: str
    score: int
    signals: list[str]
    removed_snippets: list[str]
    added_snippets: list[str]


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


def parse_missing_table(md_text: str) -> list[dict[str, str]]:
    missing: list[dict[str, str]] = []

    # Find the "## Missing from Azure" block, then parse the markdown table rows until blank.
    lines = md_text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.strip() == "## Missing from Azure (confirmed)":
            start = i
            break
    if start is None:
        return missing

    # Find the table header
    i = start
    while i < len(lines) and not lines[i].startswith("| sourcefile |"):
        i += 1
    if i >= len(lines):
        return missing

    i += 2  # skip header + separator
    while i < len(lines):
        line = lines[i]
        if not line.startswith("|"):
            break
        parts = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(parts) >= 3:
            missing.append({"sourcefile": parts[0], "local_updated": parts[1], "storageUrl": parts[2]})
        i += 1

    return missing


def iter_diff_sections(md_text: str) -> Iterable[tuple[str, str]]:
    # Returns (sourcefile, section_text)
    # Sections start with "### <name>" and continue until next "###" or EOF.
    matches = list(re.finditer(r"^###\s+(.+?)\s*$", md_text, flags=re.MULTILINE))
    for idx, m in enumerate(matches):
        name = m.group(1).strip()
        start = m.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(md_text)
        yield name, md_text[start:end]


def extract_backticked_value(section: str, label: str) -> str:
    # Example line: - local.updated: `2023-10-01T00:00:00Z`
    pattern = rf"^\-\s+{re.escape(label)}:\s+`([^`]+)`\s*$"
    m = re.search(pattern, section, flags=re.MULTILINE)
    return m.group(1).strip() if m else ""


def extract_azure_id(section: str) -> str:
    return extract_backticked_value(section, "azure.id")


def extract_diff_block(section: str) -> list[str]:
    # First ```diff block in the section
    m = re.search(r"```diff\n(.*?)\n```", section, flags=re.DOTALL)
    if not m:
        return []
    return m.group(1).splitlines()


def extract_change_lines(diff_lines: list[str]) -> tuple[list[str], list[str]]:
    removed: list[str] = []
    added: list[str] = []

    for line in diff_lines:
        if line.startswith("---") or line.startswith("+++ ") or line.startswith("@@"):
            continue
        if line.startswith("-") and not line.startswith("---"):
            removed.append(line[1:].strip())
        elif line.startswith("+") and not line.startswith("+++"):
            added.append(line[1:].strip())

    # Keep short, high-signal snippets
    removed = [s for s in removed if s]
    added = [s for s in added if s]
    return removed[:8], added[:8]


def score_impact(removed: list[str], added: list[str], local_updated: str, azure_updated: str) -> tuple[int, list[str]]:
    text = "\n".join(removed + added).lower()

    signals: list[str] = []
    score = 0

    def bump(cond: bool, points: int, signal: str) -> None:
        nonlocal score
        if cond:
            score += points
            signals.append(signal)

    bump(local_updated and azure_updated and local_updated != azure_updated, 3, "updated date differs (local vs azure)")

    # Deadlines/time limits
    bump(bool(re.search(r"\b(within|no later|at least|clear days|period of time)\b", text)), 2, "time-limit language changed")
    bump(bool(re.search(r"\b\d+\s*(day|days|month|months|hour|hours)\b", text)), 2, "explicit time quantity changed")

    # Modal verbs / obligations
    bump(" must " in f" {text} ", 2, "obligation language (must) changed")
    bump(" shall " in f" {text} ", 2, "obligation language (shall) changed")
    bump(" may " in f" {text} ", 1, "discretion language (may) changed")

    # Procedural/legal mechanics
    bump(bool(re.search(r"\b(service|served|notice)\b", text)), 2, "service/notice mechanics changed")
    bump(bool(re.search(r"\b(cost|costs|assessment)\b", text)), 2, "costs/assessment mechanics changed")
    bump(bool(re.search(r"\b(appeal|permission)\b", text)), 2, "appeals/permission mechanics changed")
    bump(bool(re.search(r"\b(disclosure|inspection)\b", text)), 2, "disclosure/inspection mechanics changed")
    bump(bool(re.search(r"\b(disapply|modify)\b", text)), 1, "rule disapplication/modification changed")
    bump(bool(re.search(r"\b(electronic filing|case management system|e-file|facsimile)\b", text)), 1, "e-filing / filing method changed")

    # References to newer legislation
    bump("2024" in text or "digital markets" in text, 2, "new legislation reference added/changed")

    return score, signals


def impact_label(score: int) -> str:
    if score >= 7:
        return "HIGH"
    if score >= 4:
        return "MEDIUM"
    return "LOW"


def render_markdown(reviews: list[DiffReview], missing: list[dict[str, str]]) -> str:
    by_impact: dict[str, int] = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    by_cause: dict[str, int] = {}

    for r in reviews:
        by_impact[r.impact] += 1
        by_cause[r.causality] = by_cause.get(r.causality, 0) + 1

    lines: list[str] = []
    lines.append("# AI Manual Review — Fresh vs Azure Differences (Jan 4, 2026)")
    lines.append("")
    lines.append("This report is an automated, AI-assisted triage of the diff excerpts in `docs/fresh_vs_index_verification_summary.md`. It is not legal advice.")
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
    lines.append("| sourcefile | impact | cause | local.updated | azure.updated | azure.id |")
    lines.append("|---|---:|---|---:|---:|---|")
    for r in reviews:
        lines.append(
            f"| {r.sourcefile} | {r.impact} | {r.causality} | {r.local_updated} | {r.azure_updated} | {r.azure_id} |"
        )
    lines.append("")

    lines.append("## B. Mismatches — Per-Document Notes")
    lines.append("")
    for r in reviews:
        lines.append(f"### {r.sourcefile}")
        lines.append("")
        lines.append(f"- Impact: **{r.impact}** (score {r.score})")
        lines.append(f"- Cause (live-HTML heuristic): {r.causality}")
        if r.signals:
            lines.append(f"- Signals: {', '.join(r.signals)}")
        lines.append(f"- local.updated: `{r.local_updated}`")
        lines.append(f"- azure.updated: `{r.azure_updated}`")
        if r.azure_id:
            lines.append(f"- azure.id: `{r.azure_id}`")
        lines.append("")

        if r.removed_snippets or r.added_snippets:
            lines.append("Key excerpt (truncated):")
            lines.append("")
            if r.removed_snippets:
                lines.append("Removed (Azure-only):")
                for s in r.removed_snippets[:5]:
                    lines.append(f"- {s}")
            if r.added_snippets:
                lines.append("Added (Local-only):")
                for s in r.added_snippets[:5]:
                    lines.append(f"- {s}")
            lines.append("")

        if r.causality == "website_changed (live matches local)":
            lines.append("Recommended action: update/re-index the Azure document(s) from the fresh scrape for this sourcefile.")
        elif r.causality == "scraper/extraction issue (live matches azure)":
            lines.append("Recommended action: inspect the scraper extraction for this page; the live page looked closer to Azure than to local.")
        else:
            lines.append("Recommended action: do a quick manual spot-check against the live `storageUrl` + Azure content; then decide whether to re-index or adjust extraction.")
        lines.append("")

    lines.append("## C. Missing in Azure (confirmed)")
    lines.append("")
    lines.append("These have no matching `sourcefile` found in the Azure index (per verifier).")
    lines.append("")
    lines.append("| sourcefile | local.updated | storageUrl |")
    lines.append("|---|---:|---|")
    for m in missing:
        lines.append(f"| {m.get('sourcefile','')} | {m.get('local_updated','')} | {m.get('storageUrl','')} |")
    lines.append("")
    lines.append("Recommended action: ingest/upload these into the Azure index (staging first if you have that workflow), then re-run the verifier.")
    lines.append("")

    return "\n".join(lines) + "\n"


def main() -> None:
    verification_summary_path = Path("docs/fresh_vs_index_verification_summary.md")
    causality_path = Path("docs/fresh_vs_index_causality.md")
    out_path = Path("docs/fresh_vs_index_ai_manual_review.md")

    md_text = verification_summary_path.read_text(encoding="utf-8")
    causality_text = causality_path.read_text(encoding="utf-8") if causality_path.exists() else ""
    causality_by_sourcefile = parse_causality_table(causality_text) if causality_text else {}

    missing = parse_missing_table(md_text)

    reviews: list[DiffReview] = []
    for sourcefile, section in iter_diff_sections(md_text):
        local_updated = extract_backticked_value(section, "local.updated")
        azure_updated = extract_backticked_value(section, "azure.updated")
        azure_id = extract_azure_id(section)
        diff_lines = extract_diff_block(section)
        removed, added = extract_change_lines(diff_lines)

        # Skip sections without diffs (defensive)
        if not diff_lines:
            continue

        score, signals = score_impact(removed, added, local_updated, azure_updated)
        causality = causality_by_sourcefile.get(sourcefile, "mixed_or_inconclusive")

        reviews.append(
            DiffReview(
                sourcefile=sourcefile,
                local_updated=local_updated,
                azure_updated=azure_updated,
                azure_id=azure_id,
                causality=causality,
                impact=impact_label(score),
                score=score,
                signals=signals,
                removed_snippets=removed,
                added_snippets=added,
            )
        )

    # Stable ordering: highest impact first, then name
    impact_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    reviews.sort(key=lambda r: (impact_order.get(r.impact, 9), r.sourcefile.lower()))

    out_path.write_text(render_markdown(reviews, missing), encoding="utf-8")
    print(f"Wrote {out_path} ({len(reviews)} mismatch reviews, {len(missing)} missing)")


if __name__ == "__main__":
    main()
