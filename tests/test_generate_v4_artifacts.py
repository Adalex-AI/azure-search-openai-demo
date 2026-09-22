import json

import pytest

from scripts import generate_v4_artifacts as artifacts
from scripts import update_cpr_index_v3 as updater
from scripts.audit_source_documents import CanonicalSource
from scripts.generate_v4_artifacts import (
    GUIDE_FILES,
    ROOT,
    content_hash,
    deduplicate_sources_by_url,
    enrich_retrieval_metadata,
    expand_oversized_embedding_windows,
    snapshot_hash,
    split_content_for_embedding_budget,
    validate_source_snapshot,
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


def test_oversized_no_boundary_sentence_is_losslessly_split_within_embedding_budget():
    document = {
        "id": "Practice_Direction_49E___Alternative_Procedure_For_Claims_chunk_000",
        "content": "AlternativeProcedure" * 12000,
        "sourcefile": "Practice Direction 49E",
        "sourcepage": "Alternative Procedure For Claims",
        "category": "Civil Procedure Rules and Practice Directions",
        "subsection_id": "49E.1",
        "subsections": ["49E.1"],
    }
    enrich_retrieval_metadata(document)

    chunker = updater.LegalDocumentChunker()
    windows = split_content_for_embedding_budget(document, document["content"], 8100, chunker)
    children = expand_oversized_embedding_windows([document])

    assert "".join(windows) == document["content"]
    assert len(children) > 1
    assert all(child["content"] == document["content"] for child in children)
    assert all(chunker.count_tokens(child["embedding_text"]) <= 8100 for child in children)
    assert all(child["sourcefile"] == document["sourcefile"] for child in children)
    assert all(child["category"] == document["category"] for child in children)
    assert all(child["subsections"] == document["subsections"] for child in children)
    assert [child["id"] for child in children] == [
        f"{document['id']}__window_{index}" for index in range(1, len(children) + 1)
    ]


COURT_GUIDES_DIR = ROOT / "scripts" / "court_guides_processing_pipeline" / "outputs_azure_di"


def test_all_configured_court_guides_have_processed_artifacts():
    for guide in GUIDE_FILES.values():
        path = COURT_GUIDES_DIR / guide["file"]
        assert path.exists(), path
        documents = json.loads(path.read_text(encoding="utf-8"))
        assert documents
        assert all(document.get("sourcefile") == guide["sourcefile"] for document in documents)
        assert all(document.get("category") == guide["category"] for document in documents)


def test_commercial_court_processed_artifact_is_release_ready():
    guide = GUIDE_FILES["Commercial Court"]
    path = COURT_GUIDES_DIR / guide["file"]
    documents = json.loads(path.read_text(encoding="utf-8"))

    assert documents
    assert all(document.get("content") for document in documents)
    assert all(document.get("storageUrl") for document in documents)


def test_source_snapshot_hash_is_deterministic():
    first = {"identity": "cpr::part 1", "html": "<p>one</p>", "status": "ok"}
    second = {"status": "ok", "html": "<p>one</p>", "identity": "cpr::part 1"}

    assert snapshot_hash(first) == snapshot_hash(second)


def test_content_hash_is_stable_for_list_or_string_content():
    document = {
        "id": "doc-1",
        "sourcefile": "Part 31",
        "sourcepage": "31.16",
        "category": "CPR",
        "storageUrl": "https://example.test/part-31",
        "updated": "2026-09-20",
        "content": ["first", "second"],
        "embedding_text": "metadata",
    }

    list_hash = content_hash(document)
    document["content"] = "first\nsecond"

    assert content_hash(document) == list_hash


def test_no_boundary_document_within_budget_is_not_expanded():
    document = {
        "id": "small-doc",
        "content": "unbroken legal prose",
        "sourcefile": "Guide",
        "sourcepage": "Section",
        "category": "Court Guide",
    }
    enrich_retrieval_metadata(document)

    assert expand_oversized_embedding_windows([document], max_embedding_tokens=8100) == [document]


def test_embedding_metadata_cannot_consume_the_full_budget():
    document = {
        "id": "metadata-overflow",
        "content": "content",
        "sourcefile": "Guide",
        "sourcepage": "Section",
        "category": "Court Guide",
        "hierarchy_path": "very long metadata " * 100,
    }
    chunker = updater.LegalDocumentChunker()

    with pytest.raises(ValueError, match="Embedding metadata exceeds"):
        split_content_for_embedding_budget(document, document["content"], 1, chunker)


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


@pytest.mark.parametrize(
    "snapshot, message",
    [
        ({"status": "failed", "source_type": "html", "html": "<p>x</p>"}, "not ok"),
        ({"status": "ok", "source_type": "pdf", "html": "<p>x</p>"}, "type mismatch"),
        ({"status": "ok", "source_type": "html"}, "no transformed HTML"),
    ],
)
def test_source_snapshot_rejects_invalid_common_contract(tmp_path, snapshot, message):
    source = CanonicalSource(
        source_type="html",
        sourcefile="Part 31",
        category="Civil Procedure Rules and Practice Directions",
    )

    with pytest.raises(ValueError, match=message):
        validate_source_snapshot(snapshot, source, tmp_path / "snapshot.json")


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


def test_generate_builds_release_bound_artifact_from_local_oracles(monkeypatch, tmp_path):
    source = CanonicalSource(
        source_type="html",
        sourcefile="Test Part",
        category="Civil Procedure Rules and Practice Directions",
        url="https://example.test/test-part",
    )
    snapshot_dir = tmp_path / "snapshots"
    guides_dir = tmp_path / "guides"
    snapshot_dir.mkdir()
    guides_dir.mkdir()
    snapshot = {
        "status": "ok",
        "identity": source.identity,
        "source_type": "html",
        "sourcefile": source.sourcefile,
        "requested_url": source.url,
        "final_url": source.url,
        "html": "<p>Test Part 1.1 body</p>",
    }
    (snapshot_dir / "test-part.json").write_text(json.dumps(snapshot))

    guide = {
        "file": "test-guide.json",
        "sourcefile": "Test Court Guide",
        "category": "Court Guide",
    }
    guide_path = guides_dir / guide["file"]
    raw_guide_document = {"sourcefile": guide["sourcefile"], "content": "Guide body"}
    guide_path.write_text(json.dumps([raw_guide_document]))
    extraction_manifest = {
        "schema_version": 1,
        "guides": {
            "test": {
                "processed_json": guide["file"],
                "processed_json_sha256": __import__("hashlib").sha256(guide_path.read_bytes()).hexdigest(),
            }
        },
    }
    (guides_dir / "court_guides_extraction_manifest.json").write_text(json.dumps(extraction_manifest))
    monkeypatch.setattr(artifacts, "load_web_sources", lambda: [source])
    monkeypatch.setattr(artifacts, "GUIDE_FILES", {"Test Guide": guide})
    monkeypatch.setattr(artifacts.updater, "ACTION_LIST", [])
    monkeypatch.setattr(artifacts.updater, "scrape_page", lambda *args, **kwargs: {"body": "source"})
    monkeypatch.setattr(
        artifacts.updater,
        "build_index_docs",
        lambda action, scraped: [
            {
                "id": "source-doc",
                "parent_id": "source-doc",
                "content": "Test Part 1.1 body",
                "sourcefile": action["sourcefile"],
                "sourcepage": "1.1",
                "category": source.category,
                "storageUrl": action["url"],
                "subsection_id": "1.1",
                "subsections": ["1.1"],
            }
        ],
    )
    monkeypatch.setattr(
        artifacts,
        "map_doc",
        lambda raw, id_prefix: {
            "id": f"{id_prefix}-doc",
            "content": raw["content"],
            "sourcefile": raw["sourcefile"],
            "sourcepage": "Guide section",
            "category": guide["category"],
            "storageUrl": "https://example.test/guide",
        },
    )

    documents, manifest = artifacts.generate(snapshot_dir, guides_dir, "release-1")

    assert [document["id"] for document in documents] == ["source-doc", "Test_Guide-doc"]
    assert manifest["release_id"] == "release-1"
    assert manifest["snapshot_count"] == 2
    assert manifest["source_counts"] == {"Test Part": 1, "Test Court Guide": 1}
    assert all(document["artifact_content_sha256"] for document in documents)


def test_generate_requires_snapshot_for_every_canonical_source(monkeypatch, tmp_path):
    source = CanonicalSource(
        source_type="html",
        sourcefile="Missing Part",
        category="Civil Procedure Rules and Practice Directions",
        url="https://example.test/missing-part",
    )
    snapshot_dir = tmp_path / "snapshots"
    snapshot_dir.mkdir()
    monkeypatch.setattr(artifacts, "load_web_sources", lambda: [source])
    monkeypatch.setattr(artifacts, "GUIDE_FILES", {})

    with pytest.raises(ValueError, match="Missing canonical source snapshots"):
        artifacts.generate(snapshot_dir, tmp_path / "guides", "release-1")
