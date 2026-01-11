"""Unit tests for legal SourceProcessor.

These tests target the custom structured source processing used by the backend
approach logic (subsection splitting, ordering, and metadata shaping).
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock


def test_process_documents_splits_multi_subsection_document_in_order():
    from customizations.approaches.source_processor import SourceProcessor

    citation_builder = Mock()
    citation_builder.extract_multiple_subsections.return_value = [
        {"subsection": "2.1", "content": "Section 2.1 content"},
        {"subsection": "1.2", "content": "Section 1.2 content"},
    ]
    citation_builder.get_subsection_sort_key.side_effect = lambda s: tuple(int(p) for p in s.split("."))

    processor = SourceProcessor(citation_builder=citation_builder)

    doc = SimpleNamespace(
        id="doc1",
        content="irrelevant (splits come from citation_builder)",
        sourcepage="CPR Part 1#page=10",
        sourcefile="CPR Part 1",
        category="CPR",
        storage_url="https://storage/doc1",
        oids=["oid1"],
        groups=["group1"],
        score=1.23,
        reranker_score=4.56,
        updated="2026-01-11",
    )

    results = processor.process_documents([doc], use_semantic_captions=False)

    assert len(results) == 2
    assert results[0]["subsection_id"] == "1.2"
    assert results[1]["subsection_id"] == "2.1"

    first = results[0]
    assert first["is_subsection"] is True
    assert first["original_doc_id"] == "doc1"
    assert first["total_subsections"] == 2
    assert first["sourcepage"] == "CPR Part 1#page=10"
    assert first["sourcefile"] == "CPR Part 1"
    assert first["category"] == "CPR"
    assert first["storageUrl"] == "https://storage/doc1"
    assert first["citation"] == "1.2, CPR Part 1#page=10, CPR Part 1"


def test_process_documents_single_document_uses_citation_builder_and_metadata():
    from customizations.approaches.source_processor import SourceProcessor

    citation_builder = Mock()
    citation_builder.extract_multiple_subsections.return_value = []
    citation_builder.build_enhanced_citation.return_value = "1.1, p. 3, CPR Part 1"

    processor = SourceProcessor(citation_builder=citation_builder)

    doc = SimpleNamespace(
        id="doc2",
        content="1.1 Something\nBody",
        sourcepage="p. 3",
        sourcefile="CPR Part 1",
        category="",
        storage_url="",
    )

    results = processor.process_documents([doc], use_semantic_captions=False)

    assert len(results) == 1
    result = results[0]
    assert result["id"] == "doc2"
    assert result["is_subsection"] is False
    assert result["original_doc_id"] == "doc2"
    assert result["citation"] == "1.1, p. 3, CPR Part 1"

    citation_builder.build_enhanced_citation.assert_called_once()


def test_process_documents_includes_semantic_captions_and_summary():
    from customizations.approaches.source_processor import SourceProcessor

    citation_builder = Mock()
    citation_builder.extract_multiple_subsections.return_value = []
    citation_builder.build_enhanced_citation.return_value = "CPR"
    processor = SourceProcessor(citation_builder=citation_builder)

    captions = [
        SimpleNamespace(text="Caption one", highlights="hi", additional_properties={"k": "v"}),
        SimpleNamespace(text="Caption two", highlights="", additional_properties={}),
    ]
    doc = SimpleNamespace(
        id="doc3",
        content="Body",
        sourcepage="p. 1",
        sourcefile="Guide",
        captions=captions,
    )

    results = processor.process_documents([doc], use_semantic_captions=True)

    assert len(results) == 1
    result = results[0]
    assert "captions" in result
    assert len(result["captions"]) == 2
    assert result["captions"][0]["text"] == "Caption one"
    assert result["caption_summary"] == "Caption one . Caption two"
