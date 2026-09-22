import json

import pytest

from scripts import generate_highlight_oracle


def write_snapshot(snapshot_dir, name, *, oracle_version):
    (snapshot_dir / name).write_text(json.dumps({
        "status": "ok",
        "identity": name,
        "content_sha256": "a" * 64,
        "oracle_version": oracle_version,
        "category": "Civil Procedure Rules and Practice Directions",
        "sourcefile": f"{name}.html",
        "schema_census": {"blocks": [
            {"kind": "heading", "locator": "h-1", "text": "1.1 First rule"},
            {"kind": "p", "locator": "p-1", "text": "The first rule applies."},
        ]},
    }), encoding="utf-8")


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