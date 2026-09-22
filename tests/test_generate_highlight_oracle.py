import json

import pytest

from scripts import generate_highlight_oracle
from scripts.generate_highlight_oracle import load_snapshot_cases


def test_load_snapshot_cases_uses_numbered_rule_after_semantic_heading(tmp_path, monkeypatch):
    snapshot = {
        "status": "ok",
        "oracle_version": "v1",
        "identity": "cpr::part-24",
        "content_sha256": "source-hash",
        "sourcefile": "Part 24",
        "category": "Civil Procedure Rules and Practice Directions",
        "schema_census": {
            "blocks": [
                {"kind": "heading", "locator": "h1", "text": "Scope of this Part"},
                {"kind": "p", "locator": "p1", "text": "24.1 This Part applies."},
                {"kind": "p", "locator": "p2", "text": "It governs summary judgment."},
                {"kind": "heading", "locator": "h2", "text": "Next rule"},
            ]
        },
    }
    (tmp_path / "part-24.json").write_text(json.dumps(snapshot), encoding="utf-8")
    monkeypatch.setattr(generate_highlight_oracle, "ROOT", tmp_path)

    cases = load_snapshot_cases(tmp_path)

    assert len(cases) == 1
    assert cases[0]["subsection_id"] == "24.1"
    assert cases[0]["expected_heading"] == "Scope of this Part"
    assert cases[0]["next_heading"] == "Next rule"


def write_snapshot(snapshot_dir, name, *, oracle_version):
    (snapshot_dir / name).write_text(
        json.dumps(
            {
                "status": "ok",
                "identity": name,
                "content_sha256": "a" * 64,
                "oracle_version": oracle_version,
                "category": "Civil Procedure Rules and Practice Directions",
                "sourcefile": f"{name}.html",
                "schema_census": {
                    "blocks": [
                        {"kind": "heading", "locator": "h-1", "text": "1.1 First rule"},
                        {"kind": "p", "locator": "p-1", "text": "The first rule applies."},
                    ]
                },
            }
        ),
        encoding="utf-8",
    )


def test_build_report_binds_every_case_to_one_snapshot_oracle_version(tmp_path, monkeypatch):
    snapshot_dir = tmp_path / "snapshots"
    snapshot_dir.mkdir()
    (snapshot_dir / "manifest.json").write_text("{}", encoding="utf-8")
    write_snapshot(snapshot_dir, "first.json", oracle_version="2")
    write_snapshot(snapshot_dir, "second.json", oracle_version="2")
    monkeypatch.setattr(generate_highlight_oracle, "ROOT", tmp_path)

    report = generate_highlight_oracle.build_report(snapshot_dir)

    assert report["oracle_version"] == "2"
    assert {case["oracle_version"] for case in report["cases"]} == {"2"}


def test_build_report_rejects_inconsistent_snapshot_oracle_versions(tmp_path, monkeypatch):
    snapshot_dir = tmp_path / "snapshots"
    snapshot_dir.mkdir()
    (snapshot_dir / "manifest.json").write_text("{}", encoding="utf-8")
    write_snapshot(snapshot_dir, "html.json", oracle_version="2")
    write_snapshot(snapshot_dir, "pdf.json", oracle_version="")
    monkeypatch.setattr(generate_highlight_oracle, "ROOT", tmp_path)

    with pytest.raises(ValueError, match="inconsistent oracle versions"):
        generate_highlight_oracle.build_report(snapshot_dir)


def test_build_report_extracts_cases_from_pdf_snapshot_text(tmp_path, monkeypatch):
    snapshot_dir = tmp_path / "snapshots"
    snapshot_dir.mkdir()
    (snapshot_dir / "manifest.json").write_text("{}", encoding="utf-8")
    (snapshot_dir / "pdf.json").write_text(
        json.dumps(
            {
                "status": "ok",
                "identity": "PDF source",
                "source_sha256": "b" * 64,
                "oracle_version": "2",
                "category": "Civil Procedure Rules and Practice Directions",
                "sourcefile": "source.pdf",
                "source_type": "pdf",
                "schema_census": {"blocks": []},
                "extracted_text": "24.2 Summary judgment\nThe court may give summary judgment.",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(generate_highlight_oracle, "ROOT", tmp_path)

    report = generate_highlight_oracle.build_report(snapshot_dir)

    assert report["cases"][0]["heading_locator"] == "pdf-line[1]"
