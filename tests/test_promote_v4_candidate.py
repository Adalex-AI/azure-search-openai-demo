import json

import pytest

from scripts.build_v4_evidence_bundle import (
    EvidenceError,
    artifact_search_gate,
    build_bundle,
)
from scripts.promote_v4_candidate import (
    PromotionError,
    load_and_validate,
    validate_evidence_bundle,
)

VALID_BUNDLE = {
    "approved": True,
    "approval_environment": "Production",
    "release_id": "20260713-r3",
    "candidate_index": "legal-court-rag-v4-prod-20260713",
    "candidate_knowledgebase": "legal-court-rag-v4-prod-20260713-agent-upgrade",
    "rollback_index": "legal-court-rag-index-v3",
    "rollback_knowledgebase": "legal-court-rag-index-v3-agent-upgrade",
    "rollback_application": {
        "release_id": "20260301-r12",
        "image_digest": "registry.example.test/legal-rag@sha256:" + "b" * 64,
        "revision_name": "legal-rag--production-v3",
        "search_index": "legal-court-rag-index-v3",
        "knowledge_base": "legal-court-rag-index-v3-agent-upgrade",
    },
    "artifact_sha256": "artifact-hash",
    "search_snapshot_sha256": "snapshot-hash",
    "fidelity": {
        "substantive_coverage": 1.0,
        "unmatched": 0,
        "ambiguous": 0,
        "unavailable": 0,
        "unclassified": 0,
    },
    "artifact_search": {"missing_count": 0, "extra_count": 0, "mismatched_count": 0},
    "candidate_validation": {"status": "PASS"},
    "application_gates": {
        "schema_version": 1,
        "status": "PASS",
        "provenance": {
            "release_id": "20260713-r3",
            "git_sha": "git-hash",
            "deployment_id": "deployment-1",
            "search_service": "search-service",
            "search_index": "legal-court-rag-v4-prod-20260713",
            "knowledge_base": "legal-court-rag-v4-prod-20260713-agent-upgrade",
            "artifact_sha256": "artifact-hash",
            "search_snapshot_sha256": "snapshot-hash",
            "image_digest": "registry.example.test/legal-rag@sha256:" + "a" * 64,
            "revision_name": "legal-rag--20260713-r3",
            "agentic_mode": "agentic",
        },
        "gates": {
            "retrieval": {"gate": "retrieval", "status": "PASS", "case_count": 4},
            "category": {"gate": "category", "status": "PASS", "case_count": 4},
            "source_hierarchy": {"gate": "source_hierarchy", "status": "PASS", "case_count": 3},
            "citation": {"gate": "citation", "status": "PASS", "case_count": 4},
            "acl": {"gate": "acl", "status": "PASS", "case_count": 1},
            "highlight": {
                "gate": "highlight",
                "status": "PASS",
                "case_count": 1650,
                "source_count": 178,
            },
        },
    },
}


def test_valid_evidence_bundle_returns_exact_cutover_targets():
    targets = validate_evidence_bundle(VALID_BUNDLE)

    assert targets["candidate_index"] == VALID_BUNDLE["candidate_index"]
    assert targets["candidate_knowledgebase"] == VALID_BUNDLE["candidate_knowledgebase"]
    assert targets["artifact_sha256"] == "artifact-hash"


def test_promotion_accepts_previous_v4_rollback_identity():
    bundle = {
        **VALID_BUNDLE,
        "rollback_index": "legal-court-rag-v4-previous-release",
        "rollback_knowledgebase": "legal-court-rag-v4-previous-release-agent-upgrade",
        "rollback_application": {
            **VALID_BUNDLE["rollback_application"],
            "release_id": "20260712-r2",
            "search_index": "legal-court-rag-v4-previous-release",
            "knowledge_base": "legal-court-rag-v4-previous-release-agent-upgrade",
        },
    }

    targets = validate_evidence_bundle(bundle)

    assert targets["rollback_index"] == "legal-court-rag-v4-previous-release"
    assert targets["rollback_release_id"] == "20260712-r2"


def test_promotion_rejects_evidence_for_a_different_release():
    with pytest.raises(PromotionError, match="does not match release_id"):
        validate_evidence_bundle(VALID_BUNDLE, expected_release_id="20260714-r4")


@pytest.mark.parametrize(
    "change, message",
    [
        ({"approved": False}, "not approved"),
        ({"approval_environment": "Staging"}, "Production approval"),
        ({"candidate_index": "legal-court-rag-index-v3"}, "legacy v3"),
        ({"candidate_knowledgebase": "legal-court-rag-index-v3-agent-upgrade"}, "legacy v3"),
        ({"fidelity": {"substantive_coverage": 1.0, "ambiguous": 1}}, "not clean"),
        ({"fidelity": {"substantive_coverage": 0.99}}, "100%"),
        ({"application_gates": {"schema_version": 1, "status": "FAIL"}}, "Application-gate"),
        (
            {"application_gates": {"schema_version": 1, "status": "PASS", "provenance": {}, "gates": {}}},
            "all six required gates",
        ),
    ],
)
def test_invalid_evidence_bundle_cannot_promote(change, message):
    bundle = {**VALID_BUNDLE, **change}

    with pytest.raises(PromotionError, match=message):
        validate_evidence_bundle(bundle)


def test_candidate_knowledgebase_must_identify_index():
    bundle = {**VALID_BUNDLE, "candidate_knowledgebase": "legal-court-rag-v4-other-agent-upgrade"}

    with pytest.raises(PromotionError, match="identify the candidate index"):
        validate_evidence_bundle(bundle)


def test_promotion_rejects_candidate_as_rollback_target():
    bundle = {
        **VALID_BUNDLE,
        "rollback_index": VALID_BUNDLE["candidate_index"],
        "rollback_knowledgebase": VALID_BUNDLE["candidate_knowledgebase"],
        "rollback_application": {
            **VALID_BUNDLE["rollback_application"],
            "search_index": VALID_BUNDLE["candidate_index"],
            "knowledge_base": VALID_BUNDLE["candidate_knowledgebase"],
        },
    }

    with pytest.raises(PromotionError, match="distinct from the candidate"):
        validate_evidence_bundle(bundle)


def test_promotion_recomputes_file_backed_evidence_hashes(tmp_path):
    artifact = tmp_path / "artifact.jsonl"
    snapshot = tmp_path / "snapshot.json"
    artifact.write_text("artifact\n")
    snapshot.write_text("snapshot\n")
    bundle = {
        **VALID_BUNDLE,
        "artifact_path": str(artifact),
        "search_snapshot_path": str(snapshot),
        "artifact_sha256": __import__("hashlib").sha256(artifact.read_bytes()).hexdigest(),
        "search_snapshot_sha256": __import__("hashlib").sha256(snapshot.read_bytes()).hexdigest(),
    }
    bundle["application_gates"] = {
        **VALID_BUNDLE["application_gates"],
        "provenance": {
            **VALID_BUNDLE["application_gates"]["provenance"],
            "artifact_sha256": bundle["artifact_sha256"],
            "search_snapshot_sha256": bundle["search_snapshot_sha256"],
        },
    }
    assert validate_evidence_bundle(bundle)["candidate_index"] == bundle["candidate_index"]

    artifact.write_text("replayed artifact\n")
    with pytest.raises(PromotionError, match="artifact_path"):
        validate_evidence_bundle(bundle)


def test_promotion_validates_portable_evidence_manifest(tmp_path):
    evidence = tmp_path / "evidence.json"
    artifact = tmp_path / "artifact.jsonl"
    snapshot = tmp_path / "snapshot.json"
    artifact.write_text("artifact\n")
    snapshot.write_text("snapshot\n")
    bundle = {
        **VALID_BUNDLE,
        "evidence_manifest": [
            {
                "name": artifact.name,
                "path": artifact.name,
                "sha256": __import__("hashlib").sha256(artifact.read_bytes()).hexdigest(),
            },
            {
                "name": snapshot.name,
                "path": snapshot.name,
                "sha256": __import__("hashlib").sha256(snapshot.read_bytes()).hexdigest(),
            },
        ],
    }
    evidence.write_text(json.dumps(bundle))
    assert load_and_validate(evidence)["candidate_index"] == bundle["candidate_index"]

    artifact.write_text("changed\n")
    with pytest.raises(PromotionError, match="manifest hash"):
        load_and_validate(evidence)


def test_promotion_rejects_mutable_application_image():
    bundle = {
        **VALID_BUNDLE,
        "application_gates": {
            **VALID_BUNDLE["application_gates"],
            "provenance": {
                **VALID_BUNDLE["application_gates"]["provenance"],
                "image_digest": "registry.example.test/legal-rag:latest",
            },
        },
    }

    with pytest.raises(PromotionError, match="image_digest must be immutable"):
        validate_evidence_bundle(bundle)


@pytest.mark.parametrize(
    "field",
    [
        "candidate_index",
        "candidate_knowledgebase",
        "artifact_sha256",
        "search_snapshot_sha256",
        "rollback_index",
        "rollback_knowledgebase",
        "release_id",
    ],
)
def test_promotion_requires_all_release_identity_strings(field):
    bundle = {**VALID_BUNDLE, field: ""}

    with pytest.raises(PromotionError, match=f"missing {field}"):
        validate_evidence_bundle(bundle)


@pytest.mark.parametrize(
    "mutation, message",
    [
        (lambda bundle: bundle.update(candidate_index="legal-court-rag-production"), "must contain v4"),
        (lambda bundle: bundle["artifact_search"].update(extra_count=1), "equality gate"),
        (lambda bundle: bundle["candidate_validation"].update(status="FAIL"), "validation gate"),
        (lambda bundle: bundle["application_gates"]["gates"]["citation"].update(gate="wrong"), "passing citation"),
        (
            lambda bundle: bundle["application_gates"]["gates"]["highlight"].update(case_count=0),
            "highlight evidence is empty",
        ),
    ],
)
def test_promotion_rejects_inconsistent_candidate_gate_contract(mutation, message):
    bundle = json.loads(json.dumps(VALID_BUNDLE))
    mutation(bundle)

    with pytest.raises(PromotionError, match=message):
        validate_evidence_bundle(bundle)


@pytest.mark.parametrize(
    "field, value, message",
    [
        ("image_digest", "registry.example.test/legal-rag:latest", "Rollback application image"),
        ("revision_name", "", "missing revision_name"),
        ("release_id", "20260713-r3", "valid release_id"),
        ("search_index", "other-index", "match rollback_index"),
        ("knowledge_base", "other-kb", "match rollback_knowledgebase"),
    ],
)
def test_promotion_rejects_incomplete_rollback_application_identity(field, value, message):
    bundle = json.loads(json.dumps(VALID_BUNDLE))
    bundle["rollback_application"][field] = value

    with pytest.raises(PromotionError, match=message):
        validate_evidence_bundle(bundle)


def test_promotion_rejects_invalid_rollback_pair_shape():
    bundle = {**VALID_BUNDLE, "rollback_knowledgebase": "legal-court-rag-index-v4-agent"}
    bundle["rollback_application"] = {
        **VALID_BUNDLE["rollback_application"],
        "knowledge_base": bundle["rollback_knowledgebase"],
    }

    with pytest.raises(PromotionError, match="v3 production pair"):
        validate_evidence_bundle(bundle)


@pytest.mark.parametrize(
    "manifest, message",
    [
        ([], "manifest is empty"),
        ([{"name": "artifact", "path": "../artifact", "sha256": "hash"}], "unsafe relative path"),
        ([{"name": "artifact", "path": "artifact"}], "invalid entry"),
    ],
)
def test_promotion_rejects_invalid_portable_evidence_manifest(tmp_path, manifest, message):
    evidence = tmp_path / "evidence.json"
    evidence.write_text(json.dumps({**VALID_BUNDLE, "evidence_manifest": manifest}))

    with pytest.raises(PromotionError, match=message):
        load_and_validate(evidence)


def test_evidence_builder_requires_clean_fidelity(tmp_path):
    artifact = tmp_path / "manifest.json"
    snapshot = tmp_path / "search.json"
    fidelity = tmp_path / "fidelity.json"
    transition = tmp_path / "transition.json"
    artifact.write_text(
        json.dumps(
            {
                "release_id": "legal-court-rag-v4",
                "embedding_model": "text-embedding-3-large",
                "embedding_dimensions": 3072,
                "document_count": 1,
                "source_count": 1,
                "snapshot_count": 1,
                "source_identity_digest": "sources-1",
            }
        )
    )
    (tmp_path / "documents_with_embeddings.jsonl").write_text(json.dumps({"id": "doc-1"}) + "\n")
    snapshot.write_text(json.dumps({"documents_sha256": "docs"}))
    fidelity.write_text(json.dumps({"summary": {"source_count": 2, "statuses": {"PASS": 1, "WARN": 1}}}))
    transition.write_text(json.dumps({"snapshot_count": 1, "failed_count": 0, "blocked_count": 0}))
    candidate_validation = tmp_path / "candidate-validation.json"
    candidate_validation.write_text(
        json.dumps(
            {
                "candidate": {"status": "PASS"},
                "provenance": {
                    "schema_version": 1,
                    "service": "search.test",
                    "index": "v4",
                    "captured_at_utc": "2026-07-13T00:00:00Z",
                    "selected_fields": [
                        "id",
                        "content",
                        "category",
                        "sourcepage",
                        "sourcefile",
                        "storageUrl",
                        "updated",
                        "parent_id",
                        "subsection_id",
                        "subsections",
                    ],
                    "document_count": 1,
                    "documents_sha256": "snapshot-hash",
                },
            }
        )
    )

    with pytest.raises(EvidenceError, match="schema version 2"):
        application_gates = tmp_path / "application-gates.json"
        rollback_application = tmp_path / "rollback-application.json"
        rollback_application.write_text(
            json.dumps(
                {
                    "release_id": "20260301-r12",
                    "image_digest": "registry.example.test/legal-rag@sha256:" + "b" * 64,
                    "revision_name": "legal-rag--production-v3",
                    "search_index": "v3",
                    "knowledge_base": "v3-agent",
                }
            )
        )
        application_gates.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "status": "PASS",
                    "provenance": {
                        "search_index": "legal-court-rag-v4",
                        "knowledge_base": "legal-court-rag-v4-agent",
                        "artifact_sha256": "placeholder",
                        "search_snapshot_sha256": "placeholder",
                    },
                    "gates": {
                        name: {"status": "PASS"}
                        for name in ("retrieval", "category", "source_hierarchy", "citation", "acl")
                    },
                }
            )
        )
        build_bundle(
            artifact,
            snapshot,
            fidelity,
            transition,
            candidate_validation,
            "legal-court-rag-v4",
            "legal-court-rag-v4-agent",
            "v3",
            "v3-agent",
            application_gates,
            rollback_application,
        )


def test_artifact_search_equality_gate_accepts_exact_selected_fields(tmp_path):
    manifest = tmp_path / "manifest.json"
    documents = tmp_path / "documents_with_embeddings.jsonl"
    document = {
        "id": "doc-1",
        "content": "The court must act",
        "category": "Civil Procedure Rules and Practice Directions",
        "sourcepage": "Part 1",
        "sourcefile": "Part 1",
        "storageUrl": "https://example.test/part1",
        "updated": "2026-07-13",
        "parent_id": "parent-1",
        "subsection_id": "1.1",
        "subsections": ["1.1"],
    }
    manifest.write_text("{}")
    documents.write_text(json.dumps(document) + "\n")

    result = artifact_search_gate(
        manifest,
        {"documents": [document]},
    )

    assert result["artifact_document_count"] == 1
    assert result["missing_count"] == 0
    assert result["extra_count"] == 0
    assert result["mismatched_count"] == 0


def test_artifact_search_equality_gate_rejects_content_mismatch(tmp_path):
    manifest = tmp_path / "manifest.json"
    documents = tmp_path / "documents_with_embeddings.jsonl"
    document = {"id": "doc-1", "content": "Canonical text"}
    manifest.write_text("{}")
    documents.write_text(json.dumps(document) + "\n")

    with pytest.raises(EvidenceError, match="Artifact/Search equality gate"):
        artifact_search_gate(manifest, {"documents": [{"id": "doc-1", "content": "Changed text"}]})


def test_artifact_search_equality_gate_rejects_duplicate_artifact_ids(tmp_path):
    manifest = tmp_path / "manifest.json"
    documents = tmp_path / "documents_with_embeddings.jsonl"
    manifest.write_text("{}")
    documents.write_text(
        json.dumps({"id": "doc-1", "content": "one"}) + "\n" + json.dumps({"id": "doc-1", "content": "two"}) + "\n"
    )

    with pytest.raises(EvidenceError, match="Artifact/Search equality gate"):
        artifact_search_gate(manifest, {"documents": [{"id": "doc-1", "content": "one"}]})
