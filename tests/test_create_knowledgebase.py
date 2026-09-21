import pytest

import scripts.create_knowledgebase as create_knowledgebase_module


def test_create_credential_forwards_tenant(monkeypatch):
    calls = []
    credential = object()

    def credential_factory(**kwargs):
        calls.append(kwargs)
        return credential

    monkeypatch.setattr(create_knowledgebase_module, "DefaultAzureCredential", credential_factory)

    assert create_knowledgebase_module.create_credential("tenant-1") is credential
    assert calls == [{"process_timeout": 60, "tenant_id": "tenant-1"}]


def test_create_credential_without_tenant_uses_default_credential(monkeypatch):
    calls = []

    def credential_factory(**kwargs):
        calls.append(kwargs)
        return object()

    monkeypatch.setattr(create_knowledgebase_module, "DefaultAzureCredential", credential_factory)

    create_knowledgebase_module.create_credential("")

    assert calls == [{"process_timeout": 60}]


@pytest.mark.asyncio
async def test_create_knowledgebase_creates_source_then_knowledgebase(monkeypatch):
    calls = []
    credential = object()

    class FakeClient:
        def __init__(self, *, endpoint, credential):
            assert endpoint == "https://search.search.windows.net"
            assert credential is credential_instance

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, traceback):
            return None

        async def create_or_update_knowledge_source(self, *, knowledge_source):
            calls.append(("source", knowledge_source))

        async def create_or_update_knowledge_base(self, *, knowledge_base):
            calls.append(("knowledgebase", knowledge_base))

    credential_instance = credential
    monkeypatch.setattr(create_knowledgebase_module, "create_credential", lambda tenant_id: credential)
    monkeypatch.setattr(create_knowledgebase_module, "SearchIndexClient", FakeClient)
    monkeypatch.setattr(create_knowledgebase_module, "load_azd_env", lambda: {})
    for key, value in {
        "AZURE_SEARCH_SERVICE": "search",
        "AZURE_SEARCH_INDEX": "index-v4-staging-test",
        "AZURE_SEARCH_KNOWLEDGEBASE_NAME": "kb-v4-staging-test",
        "AZURE_OPENAI_SERVICE": "openai",
        "AZURE_OPENAI_KNOWLEDGEBASE_DEPLOYMENT": "deployment",
        "AZURE_OPENAI_KNOWLEDGEBASE_MODEL": "model",
        "AZURE_TENANT_ID": "tenant-1",
    }.items():
        monkeypatch.setenv(key, value)

    await create_knowledgebase_module.create_knowledgebase()

    assert [operation for operation, _ in calls] == ["source", "knowledgebase"]
    source = calls[0][1]
    knowledgebase = calls[1][1]
    assert source.name == "index-v4-staging-test"
    assert knowledgebase.name == "kb-v4-staging-test"
    assert knowledgebase.knowledge_sources[0].name == source.name
    assert knowledgebase.models[0].azure_open_ai_parameters.deployment_name == "deployment"
    assert knowledgebase.models[0].azure_open_ai_parameters.model_name == "model"
