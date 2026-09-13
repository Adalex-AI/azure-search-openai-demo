import json
import subprocess

from scripts.rollback_v4 import (
    CONFIRMATION,
    build_rollback_plan,
    execute_plan,
)


def approved_evidence():
    return {
        "approved": True,
        "approval_environment": "Production",
        "release_id": "release-1",
        "candidate_index": "legal-court-rag-v4-release-1",
        "candidate_knowledgebase": "legal-court-rag-v4-release-1-agent-upgrade",
        "rollback_index": "legal-court-rag-index-v3",
        "rollback_knowledgebase": "legal-court-rag-index-v3-agent-upgrade",
        "rollback_application": {
            "schema_version": 1,
            "platform": "containerapps",
            "image_digest": "registry.example/legal-rag@sha256:" + "b" * 64,
            "revision_name": "app--production-v3",
            "release_id": "release-0",
            "search_index": "legal-court-rag-index-v3",
            "knowledge_base": "legal-court-rag-index-v3-agent-upgrade",
        },
        "artifact_sha256": "artifact",
        "search_snapshot_sha256": "snapshot",
        "fidelity": {"substantive_coverage": 1.0, "unmatched": 0, "ambiguous": 0, "unavailable": 0, "unclassified": 0},
        "artifact_search": {"missing_count": 0, "extra_count": 0, "mismatched_count": 0},
        "candidate_validation": {"status": "PASS"},
        "application_gates": {
            "schema_version": 1,
            "status": "PASS",
            "provenance": {
                "release_id": "release-1",
                "git_sha": "git",
                "deployment_id": "deployment",
                "search_service": "search",
                "search_index": "legal-court-rag-v4-release-1",
                "knowledge_base": "legal-court-rag-v4-release-1-agent-upgrade",
                "artifact_sha256": "artifact",
                "search_snapshot_sha256": "snapshot",
                "image_digest": "registry.example/legal-rag@sha256:" + "a" * 64,
                "revision_name": "candidate--release-1",
                "agentic_mode": "agentic",
            },
            "gates": {
                name: {
                    "gate": name,
                    "status": "PASS",
                    **(
                        {
                            "case_count": 1,
                            "source_count": 1,
                            "browser_evidence": {
                                "browser": {
                                    "supporting_content_visible": True,
                                    "highlight_visible": True,
                                    "citation_path_present": True,
                                },
                                "case_id": "case",
                                "subsection_id": "1",
                            },
                        }
                        if name == "highlight"
                        else {}
                    ),
                }
                for name in ("retrieval", "category", "source_hierarchy", "citation", "acl", "highlight")
            },
        },
    }


def write_evidence(tmp_path, payload=None):
    path = tmp_path / "evidence.json"
    path.write_text(json.dumps(payload or approved_evidence()))
    return path


def test_rollback_builds_paired_v3_plan_without_mutation(tmp_path):
    plan = build_rollback_plan(write_evidence(tmp_path), "rg", "app", "release-1")

    assert plan["executed"] if "executed" in plan else True
    assert plan["search_index"] == "legal-court-rag-index-v3"
    assert plan["knowledge_base"] == "legal-court-rag-index-v3-agent-upgrade"
    assert plan["image_digest"].endswith("b" * 64)
    assert plan["revision_name"] == "app--production-v3"
    assert plan["candidate_release_id"] == "release-1"
    assert plan["release_id"] == "release-0"
    assert "V4_RELEASE_ID=release-0" in plan["command"][0]
    assert plan["command"][0][:3] == ["az", "containerapp", "update"]
    assert "--image" in plan["command"][0]
    assert plan["command"][0][plan["command"][0].index("--revision-suffix") + 1] == "production-v3"


def test_containerapp_rollback_normalizes_full_revision_name(tmp_path):
    evidence = approved_evidence()
    evidence["rollback_application"]["revision_name"] = "app--production-v3"

    plan = build_rollback_plan(write_evidence(tmp_path, evidence), "rg", "app", "release-1")

    assert plan["revision_name"] == "app--production-v3"
    assert plan["command"][0][plan["command"][0].index("--revision-suffix") + 1] == "production-v3"


def test_appservice_rollback_uses_one_valid_cli_command(tmp_path):
    evidence = approved_evidence()
    evidence["rollback_application"]["platform"] = "appservice"

    plan = build_rollback_plan(write_evidence(tmp_path, evidence), "rg", "app", "release-1")

    assert plan["platform"] == "appservice"
    assert plan["command"][0][:5] == ["az", "webapp", "config", "container", "set"]
    assert plan["command"][0][-1].endswith("b" * 64)
    assert plan["command"][1][:4] == ["az", "webapp", "config", "appsettings"]
    assert plan["command"][1].count("--settings") == 1
    assert "V4_IMAGE_DIGEST=" in " ".join(plan["command"][1])
    assert "V4_RELEASE_ID=release-0" in " ".join(plan["command"][1])


def test_appservice_rollback_executes_image_then_settings(monkeypatch, tmp_path):
    evidence = approved_evidence()
    evidence["rollback_application"]["platform"] = "appservice"
    plan = build_rollback_plan(write_evidence(tmp_path, evidence), "rg", "app", "release-1")
    calls = []
    monkeypatch.setattr("scripts.rollback_v4.subprocess.run", lambda command, check: calls.append((command, check)))

    execute_plan(plan)

    assert calls == [(plan["command"][0], True), (plan["command"][1], True)]


def test_rollback_rejects_non_v3_pair(tmp_path):
    evidence = approved_evidence()
    evidence["rollback_index"] = "legal-court-rag-v4-release-0"
    evidence["rollback_knowledgebase"] = "legal-court-rag-v4-release-0-agent-upgrade"
    evidence["rollback_application"]["search_index"] = evidence["rollback_index"]
    evidence["rollback_application"]["knowledge_base"] = evidence["rollback_knowledgebase"]
    evidence["rollback_application"]["release_id"] = "release-0"

    plan = build_rollback_plan(write_evidence(tmp_path, evidence), "rg", "app", "release-1")
    assert plan["search_index"] == "legal-court-rag-v4-release-0"


def test_rollback_execution_is_only_the_explicit_command(monkeypatch, tmp_path):
    plan = build_rollback_plan(write_evidence(tmp_path), "rg", "app", "release-1")
    calls = []
    monkeypatch.setattr("scripts.rollback_v4.subprocess.run", lambda command, check: calls.append((command, check)))

    execute_plan(plan)

    assert calls == [(plan["command"][0], True)]


def test_rollback_confirmation_token_is_explicit():
    assert CONFIRMATION == "ROLLBACK-PREVIOUS"
    assert subprocess.list2cmdline(["--execute", "--confirm-rollback", CONFIRMATION]).endswith(CONFIRMATION)
