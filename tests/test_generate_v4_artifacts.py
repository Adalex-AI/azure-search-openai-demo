import json
from pathlib import Path

import pytest

from scripts.audit_source_documents import CanonicalSource
import scripts.generate_v4_artifacts as artifacts
from scripts.generate_v4_artifacts import (
    GUIDE_FILES,
    ROOT,
    deduplicate_sources_by_url,
    enrich_retrieval_metadata,
    snapshot_hash,
    validate_source_snapshot,
    expand_oversized_embedding_windows,
)


def test_retrieval_metadata_preserves_content_and_builds_hierarchy():
    document = {
        "content": "Rule 31.16 permits an application for specific disclosure.",
        "sourcefile": "Part 31",
        "sourcepage": "Part 31 Disclosure",
        "category": "Civil Procedure Rules and Practice Directions",
        "subsection_id": "31.16",
    }

    enrich_retrieval_metadata(document)

    assert document["content"].startswith("Rule 31.16")
    assert document["section_title"] == "31.16"
    assert document["hierarchy_path"] == "Part 31 > Part 31 Disclosure > 31.16"
    assert "31.16" in document["legal_references"]
    assert "HIERARCHY: Part 31 > Part 31 Disclosure > 31.16" in document["embedding_text"]


def test_oversized_embedding_windows_preserve_canonical_content():
    document = {
        "id": "part-31",
        "content": "## 31.1 Heading\n" + ("Disclosure detail. " * 6000),
        "sourcefile": "Part 31",
        "sourcepage": "Part 31 Disclosure",
        "category": "Civil Procedure Rules and Practice Directions",
        "subsection_id": "31.1",
    }
    enrich_retrieval_metadata(document)

    children = expand_oversized_embedding_windows([document])

    assert len(children) > 1
    assert all(child["content"] == document["content"] for child in children)
    assert all(child["parent_id"] == "part-31" for child in children)
    assert [child["child_window"] for child in children] == list(range(1, len(children) + 1))


COURT_GUIDES_DIR = ROOT / "scripts" / "court_guides_processing_pipeline" / "outputs_azure_di"


def test_all_configured_court_guides_have_processed_artifacts():
    for guide in GUIDE_FILES.values():
        path = COURT_GUIDES_DIR / guide["file"]
        assert path.exists(), path
        documents = json.loads(path.read_text(encoding="utf-8"))
        assert documents
        assert all(document.get("sourcefile") == guide["sourcefile"] for document in documents)
        assert all(document.get("category") == guide["category"] for document in documents)


def test_ipec_processed_artifact_is_release_ready():
    guide = GUIDE_FILES["Intellectual Property Enterprise Court"]
    path = COURT_GUIDES_DIR / guide["file"]
    documents = json.loads(path.read_text(encoding="utf-8"))

    assert len(documents) == 73
    assert all(document.get("content") for document in documents)
    assert all(document.get("storageUrl") for document in documents)


def test_source_snapshot_hash_is_deterministic():
    first = {"identity": "cpr::part 1", "html": "<p>one</p>", "status": "ok"}
    second = {"status": "ok", "html": "<p>one</p>", "identity": "cpr::part 1"}

    assert snapshot_hash(first) == snapshot_hash(second)


def test_duplicate_url_sources_prefer_descriptive_identity():
    short = CanonicalSource(
        source_type="html",
        sourcefile="Part 83",
        category="CPR",
        url="https://example.test/part-83",
    )
    descriptive = CanonicalSource(
        source_type="html",
        sourcefile="Part 83 Writs and Warrants",
        category="CPR",
        url="https://example.test/part-83",
    )

    selected = deduplicate_sources_by_url([short, descriptive])

    assert list(selected) == [descriptive.identity]


def test_pdf_source_snapshot_requires_verified_provenance(tmp_path):
    source = CanonicalSource(
        source_type="pdf",
        sourcefile="Pre-Action Protocol for Debt Claims",
        category="Civil Procedure Rules and Practice Directions",
        url="https://example.test/debt-pap.pdf",
    )
    snapshot = {
        "status": "ok",
        "source_type": "pdf",
        "content_type": "application/pdf",
        "source_sha256": "abc123",
        "extracted_text": "Debt Claims content",
        "html": "<html><body>Debt Claims content</body></html>",
    }

    validate_source_snapshot(snapshot, source, tmp_path / "debt.json")


@pytest.mark.parametrize("missing", ["source_sha256", "extracted_text", "html"])
def test_pdf_source_snapshot_rejects_missing_provenance(tmp_path, missing):
    source = CanonicalSource(
        source_type="pdf",
        sourcefile="Pre-Action Protocol for Debt Claims",
        category="Civil Procedure Rules and Practice Directions",
    )
    snapshot = {
        "status": "ok",
        "source_type": "pdf",
        "content_type": "application/pdf",
        "source_sha256": "abc123",
        "extracted_text": "Debt Claims content",
        "html": "<html><body>Debt Claims content</body></html>",
    }
    snapshot.pop(missing)

    with pytest.raises(ValueError, match="PDF snapshot|Source snapshot"):
        validate_source_snapshot(snapshot, source, tmp_path / "debt.json")


def test_generate_uses_snapshot_html_with_current_scraper_api(monkeypatch, tmp_path):
    source = CanonicalSource(
        source_type="html",
        sourcefile="Part 1",
        category="Civil Procedure Rules and Practice Directions",
        url="https://example.test/part-1",
    )
    snapshot_dir = tmp_path / "snapshots"
    snapshot_dir.mkdir()
    (snapshot_dir / "part-1.json").write_text(
        json.dumps(
            {
                "status": "ok",
                "identity": source.identity,
                "source_type": "html",
                "sourcefile": source.sourcefile,
                "requested_url": source.url,
                "final_url": source.url,
                "html": "<main><p>Snapshot-only legal content.</p></main>",
            }
        ),
        encoding="utf-8",
    )
    court_guides_dir = tmp_path / "court-guides"
    court_guides_dir.mkdir()
    (court_guides_dir / "court_guides_extraction_manifest.json").write_text(
        json.dumps({"schema_version": 1, "guides": {}}), encoding="utf-8"
    )

    monkeypatch.setattr(artifacts, "load_web_sources", lambda: [source])
    monkeypatch.setattr(artifacts, "GUIDE_FILES", {})

    def scrape_snapshot(session, action):
        soup = artifacts.updater.fetch_soup(session, action["url"])
        return {"content": soup.get_text(" ", strip=True)}

    monkeypatch.setattr(artifacts.updater, "scrape_page", scrape_snapshot)
    monkeypatch.setattr(
        artifacts.updater,
        "build_index_docs",
        lambda action, scraped: [
            {
                "id": "part-1",
                "content": scraped["content"],
                "sourcefile": action["sourcefile"],
                "sourcepage": "Part 1",
                "category": source.category,
                "storageUrl": action["url"],
                "updated": "2026-01-01T00:00:00Z",
                "parent_id": "part-1",
                "subsection_id": "1.1",
                "subsections": ["1.1"],
            }
        ],
    )

    documents, manifest = artifacts.generate(snapshot_dir, court_guides_dir, "test-release")

    assert documents[0]["content"] == "Snapshot-only legal content."
    assert manifest["snapshot_count"] == 1
