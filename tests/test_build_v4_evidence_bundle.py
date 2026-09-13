import hashlib
import json

import pytest

from scripts.build_v4_evidence_bundle import (
    EvidenceError,
    application_gate_gate,
    candidate_validation_matches_snapshot,
    extraction_manifest_gate,
    fidelity_gate,
)

PROVENANCE = {
    "release_id": "release-1",
    "git_sha": "git-1",
    "deployment_id": "deployment-1",
    "artifact_sha256": "artifact-1",
    "search_snapshot_sha256": "snapshot-1",
    "search_service": "search-1",
    "search_index": "index-1",
    "knowledge_base": "kb-1",
    "agentic_mode": "agentic",
    "image_digest": "registry.example.test/legal-rag@sha256:" + "a" * 64,
    "revision_name": "legal-rag--release-1",
}


def application_report(highlight):
    gates = {name: {"status": "PASS"} for name in ("retrieval", "category", "source_hierarchy", "citation", "acl")}
    gates["highlight"] = highlight
    return {"schema_version": 1, "status": "PASS", "provenance": PROVENANCE, "gates": gates}


def producer_browser_evidence():
    return {
        "browser": {
            "supporting_content_visible": True,
            "highlight_visible": True,
            "citation_path_present": True,
        },
        "case_id": "case-24.2",
        "subsection_id": "24.2",
    }


def test_application_gate_requires_live_browser_highlight_evidence():
    with pytest.raises(EvidenceError, match="live browser evidence"):
        application_gate_gate(application_report({"status": "PASS"}), "index-1", "kb-1", "artifact-1", "snapshot-1")


def test_application_gate_accepts_live_browser_highlight_evidence():
    report = application_report({"status": "PASS", "browser_evidence": producer_browser_evidence()})
    assert application_gate_gate(report, "index-1", "kb-1", "artifact-1", "snapshot-1") is report


def test_application_gate_rejects_mixed_artifact_release():
    report = application_report({"status": "PASS", "browser_evidence": producer_browser_evidence()})

    with pytest.raises(EvidenceError, match="artifact release_id"):
        application_gate_gate(report, "index-1", "kb-1", "artifact-1", "snapshot-1", expected_release_id="release-2")


def test_application_gate_rejects_incompatible_browser_evidence_shape():
    report = application_report({"status": "PASS", "browser_evidence": {"highlight_visible": True}})

    with pytest.raises(EvidenceError, match="run_browser_gate shape"):
        application_gate_gate(report, "index-1", "kb-1", "artifact-1", "snapshot-1")


def test_application_gate_rejects_unexpected_deployment_provenance():
    report = application_report({"status": "PASS", "browser_evidence": producer_browser_evidence()})

    with pytest.raises(EvidenceError, match="deployment_id"):
        application_gate_gate(
            report,
            "index-1",
            "kb-1",
            "artifact-1",
            "snapshot-1",
            expected_provenance={**PROVENANCE, "deployment_id": "deployment-2"},
        )


def test_candidate_validation_accepts_snapshot_envelope_metadata():
    snapshot = {
        "schema_version": 1,
        "service": "search-1",
        "index": "index-1",
        "captured_at_utc": "2026-09-11T00:00:00Z",
        "selected_fields": ["id", "content"],
        "document_count": 1,
        "documents_sha256": "documents-1",
    }
    report = {
        "provenance": {
            **snapshot,
            "verified": True,
            "format": "envelope",
        }
    }

    candidate_validation_matches_snapshot(report, snapshot)


def fidelity_report(snapshot, source_count=1, source_identity_digest="sources-1"):
    source = {
        "source_type": "pdf",
        "category": "Guide",
        "sourcefile": "guide.pdf",
        "status": "PASS",
        "remediation_status": "verified",
        "metrics": {
            "substantive_blocks": {
                "source_block_count": 1,
                "matched_block_count": 1,
                "unmatched_block_count": 0,
                "ambiguous_block_count": 0,
                "cross_document_overlap_count": 0,
                "occurrence_ledger": [{}],
            }
        },
    }
    return {
        "schema_version": 2,
        "run_id": "run-1",
        "started_at_utc": "2026-09-11T00:00:00Z",
        "completed_at_utc": "2026-09-11T00:01:00Z",
        "complete": True,
        "snapshot_provenance": {**snapshot, "verified": True, "format": "envelope"},
        "summary": {"source_count": source_count, "statuses": {"PASS": source_count}},
        "expected_source_count": source_count,
        "processed_source_count": source_count,
        "source_identity_digest": source_identity_digest,
        "sources": [source for _ in range(source_count)],
        "remediation": {"verified": source_count},
    }


def test_fidelity_gate_rejects_foreign_snapshot_provenance():
    snapshot = {"schema_version": 1, "service": "search-1", "index": "index-1", "documents_sha256": "docs-1"}
    report = fidelity_report({**snapshot, "documents_sha256": "foreign"})

    with pytest.raises(EvidenceError, match="does not match Search snapshot"):
        fidelity_gate(report, expected_snapshot=snapshot)


def test_fidelity_gate_rejects_filtered_source_set():
    snapshot = {"schema_version": 1, "service": "search-1", "index": "index-1", "documents_sha256": "docs-1"}
    report = fidelity_report(snapshot)

    with pytest.raises(EvidenceError, match="complete canonical source set"):
        fidelity_gate(report, expected_snapshot=snapshot, expected_source_count=2)


def test_fidelity_gate_rejects_missing_source_identity_digest():
    snapshot = {"schema_version": 1, "service": "search-1", "index": "index-1", "documents_sha256": "docs-1"}
    report = fidelity_report(snapshot)
    report.pop("source_identity_digest")

    with pytest.raises(EvidenceError, match="missing source identity digest"):
        fidelity_gate(report, expected_snapshot=snapshot, expected_source_count=1, expected_source_identity_digest="sources-1")


def test_extraction_manifest_binds_packaged_processed_guides(tmp_path):
    processed = tmp_path / "Guide_processed.json"
    processed.write_text(json.dumps([{"id": "guide-1"}]) + "\n")
    extraction = tmp_path / "court_guides_extraction_manifest.json"
    extraction_payload = {
        "schema_version": 1,
        "processed_guide_count": 1,
        "processed_document_count": 1,
        "guides": {
            "Guide": {
                "processed_json": processed.name,
                "processed_json_sha256": hashlib.sha256(processed.read_bytes()).hexdigest(),
                "document_count": 1,
            }
        },
    }
    extraction.write_text(json.dumps(extraction_payload) + "\n")
    manifest = {
        "court_guides_extraction_manifest_sha256": hashlib.sha256(extraction.read_bytes()).hexdigest(),
    }

    result = extraction_manifest_gate(tmp_path / "manifest.json", manifest)

    assert result["guide_count"] == 1
    assert result["document_count"] == 1


def test_extraction_manifest_rejects_hash_drift(tmp_path):
    extraction = tmp_path / "court_guides_extraction_manifest.json"
    extraction.write_text(json.dumps({"schema_version": 1, "guides": {}}) + "\n")
    manifest = {"court_guides_extraction_manifest_sha256": "stale"}

    with pytest.raises(EvidenceError, match="not bound"):
        extraction_manifest_gate(tmp_path / "manifest.json", manifest)