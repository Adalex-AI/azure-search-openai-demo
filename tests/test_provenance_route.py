import pytest
from quart import Quart

from customizations.routes.provenance import _configured_provenance, provenance_bp


def configure_complete_provenance(monkeypatch):
    for name, value in {
        "V4_RELEASE_ID": "release-1",
        "GIT_SHA": "git-1",
        "DEPLOYMENT_ID": "deployment-1",
        "V4_ARTIFACT_SHA256": "artifact-1",
        "V4_SEARCH_SNAPSHOT_SHA256": "snapshot-1",
        "AZURE_SEARCH_SERVICE": "search-1",
        "V4_IMAGE_DIGEST": "registry.example.test/legal-rag@sha256:" + "a" * 64,
        "V4_REVISION_NAME": "legal-rag--release-1",
    }.items():
        monkeypatch.setenv(name, value)


def provenance_app():
    app = Quart(__name__)
    app.config.update(
        PROVENANCE_SEARCH_INDEX="index-v4-staging",
        PROVENANCE_KNOWLEDGE_BASE="kb-v4-staging",
        PROVENANCE_AGENTIC_MODE="agentic",
    )
    app.register_blueprint(provenance_bp)
    return app


@pytest.mark.asyncio
async def test_provenance_uses_container_app_revision_when_override_is_absent(monkeypatch):
    app = Quart(__name__)
    app.config.update(
        PROVENANCE_SEARCH_INDEX="index-v4-staging",
        PROVENANCE_KNOWLEDGE_BASE="kb-v4-staging",
    )
    for name, value in {
        "V4_RELEASE_ID": "release-1",
        "GIT_SHA": "git-1",
        "DEPLOYMENT_ID": "deployment-1",
        "V4_ARTIFACT_SHA256": "artifact-1",
        "V4_SEARCH_SNAPSHOT_SHA256": "snapshot-1",
        "AZURE_SEARCH_SERVICE": "search-1",
        "V4_IMAGE_DIGEST": "registry.example.test/legal-rag@sha256:" + "a" * 64,
    }.items():
        monkeypatch.setenv(name, value)
    monkeypatch.delenv("V4_REVISION_NAME", raising=False)
    monkeypatch.setenv("CONTAINER_APP_REVISION_NAME", "legal-rag--release-1")

    context = app.app_context()
    await context.push()
    try:
        assert _configured_provenance()["revision_name"] == "legal-rag--release-1"
    finally:
        await context.pop()


@pytest.mark.asyncio
async def test_provenance_endpoint_returns_complete_candidate_identity(monkeypatch):
    configure_complete_provenance(monkeypatch)
    client = provenance_app().test_client()

    response = await client.get("/api/provenance")

    assert response.status_code == 200
    assert (await response.get_json())["revision_name"] == "legal-rag--release-1"


@pytest.mark.asyncio
async def test_provenance_endpoint_requires_configured_token(monkeypatch):
    configure_complete_provenance(monkeypatch)
    monkeypatch.setenv("V4_PROVENANCE_TOKEN", "proof")
    client = provenance_app().test_client()

    unauthenticated = await client.get("/api/provenance")
    authenticated = await client.get("/api/provenance", headers={"X-V4-Provenance-Token": "proof"})

    assert unauthenticated.status_code == 401
    assert authenticated.status_code == 200


@pytest.mark.asyncio
async def test_provenance_endpoint_reports_missing_runtime_identity(monkeypatch):
    monkeypatch.delenv("V4_PROVENANCE_TOKEN", raising=False)
    client = provenance_app().test_client()

    response = await client.get("/api/provenance")

    assert response.status_code == 503
    assert "release_id" in (await response.get_json())["missing"]
