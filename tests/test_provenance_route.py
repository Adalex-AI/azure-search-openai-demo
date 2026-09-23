import pytest
from quart import Quart

from customizations.routes.provenance import _configured_provenance, provenance_bp


@pytest.mark.asyncio
async def test_provenance_returns_configured_candidate_identity(monkeypatch):
    app = Quart(__name__)
    app.register_blueprint(provenance_bp)
    app.config.update(
        PROVENANCE_SEARCH_INDEX="legal-court-rag-v4-staging-release-1",
        PROVENANCE_KNOWLEDGE_BASE="legal-court-rag-v4-staging-release-1-agent-upgrade",
    )
    for name, value in {
        "V4_RELEASE_ID": "release-1",
        "GIT_SHA": "git-1",
        "DEPLOYMENT_ID": "deployment-1",
        "V4_ARTIFACT_SHA256": "artifact-1",
        "V4_SEARCH_SNAPSHOT_SHA256": "snapshot-1",
        "V4_IMAGE_DIGEST": "registry.example/legal-rag@sha256:" + "a" * 64,
        "V4_REVISION_NAME": "legal-rag--release-1",
        "V4_AGENTIC_MODE": "agentic",
        "AZURE_SEARCH_SERVICE": "search-1",
    }.items():
        monkeypatch.setenv(name, value)

    async with app.test_client() as client:
        response = await client.get("/api/provenance")
        payload = await response.get_json()

    assert response.status_code == 200
    assert payload["schema_version"] == 1
    assert payload["search_index"] == "legal-court-rag-v4-staging-release-1"
    assert payload["knowledge_base"].endswith("-agent-upgrade")


@pytest.mark.asyncio
async def test_provenance_rejects_missing_identity(monkeypatch):
    app = Quart(__name__)
    app.register_blueprint(provenance_bp)
    app.config.update(PROVENANCE_SEARCH_INDEX="", PROVENANCE_KNOWLEDGE_BASE="")
    monkeypatch.delenv("V4_PROVENANCE_TOKEN", raising=False)

    async with app.test_client() as client:
        response = await client.get("/api/provenance")

    assert response.status_code == 503
