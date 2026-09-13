import pytest
from quart import Quart

from customizations.routes.provenance import _configured_provenance


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