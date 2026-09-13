import pytest

from scripts.validate_rollback_active_release import (
    RollbackValidationError,
    validate_active_rollback,
)


def plan(platform="containerapps"):
    return {
        "platform": platform,
        "image_digest": "registry.example/legal-rag@sha256:" + "b" * 64,
        "revision_name": "production-v3",
        "release_id": "release-0",
        "search_index": "legal-court-rag-index-v3",
        "knowledge_base": "legal-court-rag-index-v3-agent-upgrade",
    }


def container_app():
    return {
        "properties": {
            "latestRevisionName": "production-v3",
            "template": {"containers": [{"image": plan()["image_digest"], "env": [
                {"name": "V4_RELEASE_ID", "value": "release-0"},
                {"name": "AZURE_SEARCH_INDEX", "value": "legal-court-rag-index-v3"},
                {"name": "AZURE_SEARCH_KNOWLEDGEBASE_NAME", "value": "legal-court-rag-index-v3-agent-upgrade"},
            ]}]},
            "configuration": {"ingress": {"traffic": [{"revisionName": "production-v3", "weight": 100}]}},
        }
    }


def test_validates_container_app_rollback():
    assert validate_active_rollback(container_app(), plan(), "containerapps") == "release-0"


def test_rejects_non_v3_search_pair():
    rollback = plan()
    rollback["search_index"] = "other"
    with pytest.raises(RollbackValidationError, match="does not match rollback plan"):
        validate_active_rollback(container_app(), rollback, "containerapps")


def test_validates_previous_v4_pair():
    rollback = plan()
    rollback.update({
        "revision_name": "production-v4-previous",
        "release_id": "release-previous",
        "search_index": "legal-court-rag-v4-release-previous",
        "knowledge_base": "legal-court-rag-v4-release-previous-agent-upgrade",
    })
    app = container_app()
    app["properties"]["latestRevisionName"] = rollback["revision_name"]
    app["properties"]["template"]["containers"][0]["env"] = [
        {"name": "V4_RELEASE_ID", "value": rollback["release_id"]},
        {"name": "AZURE_SEARCH_INDEX", "value": rollback["search_index"]},
        {"name": "AZURE_SEARCH_KNOWLEDGEBASE_NAME", "value": rollback["knowledge_base"]},
    ]
    app["properties"]["configuration"]["ingress"]["traffic"][0]["revisionName"] = rollback["revision_name"]
    assert validate_active_rollback(app, rollback, "containerapps") == "release-previous"


def test_validates_appservice_settings():
    settings = [
        {"name": "V4_RELEASE_ID", "value": "release-0"},
        {"name": "V4_IMAGE_DIGEST", "value": plan("appservice")["image_digest"]},
        {"name": "V4_REVISION_NAME", "value": "production-v3"},
        {"name": "AZURE_SEARCH_INDEX", "value": "legal-court-rag-index-v3"},
        {"name": "AZURE_SEARCH_KNOWLEDGEBASE_NAME", "value": "legal-court-rag-index-v3-agent-upgrade"},
    ]
    assert validate_active_rollback(settings, plan("appservice"), "appservice") == "release-0"


def test_rejects_partial_container_app_traffic():
    app = container_app()
    app["properties"]["configuration"]["ingress"]["traffic"][0]["weight"] = 50
    with pytest.raises(RollbackValidationError, match="100% traffic"):
        validate_active_rollback(app, plan(), "containerapps")