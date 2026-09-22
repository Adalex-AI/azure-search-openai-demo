import pytest

import scripts.create_knowledgebase as create_knowledgebase_module


def test_create_credential_uses_supported_default_credential_options(monkeypatch):
    calls = []
    credential = object()

    def credential_factory(**kwargs):
        calls.append(kwargs)
        return credential

    monkeypatch.setattr(create_knowledgebase_module, "DefaultAzureCredential", credential_factory)

    assert create_knowledgebase_module.create_credential() is credential
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
    monkeypatch.setattr(create_knowledgebase_module, "create_credential", lambda: credential)
    monkeypatch.setattr(create_knowledgebase_module, "SearchIndexClient", FakeClient)
    monkeypatch.setattr(create_knowledgebase_module, "load_azd_env", lambda: {})
    for key, value in {
        "AZURE_SEARCH_SERVICE": "search",
        "AZURE_SEARCH_INDEX": "index-v4-staging-test",
        "AZURE_SEARCH_KNOWLEDGEBASE_NAME": "kb-v4-staging-test",
        "AZURE_OPENAI_SERVICE": "openai",
        "AZURE_OPENAI_ENDPOINT": "https://canonical.openai.azure.com",
        "AZURE_OPENAI_KNOWLEDGEBASE_DEPLOYMENT": "deployment",
        "AZURE_OPENAI_KNOWLEDGEBASE_MODEL": "model",
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
    assert knowledgebase.models[0].azure_open_ai_parameters.resource_url == "https://canonical.openai.azure.com/"


@pytest.mark.asyncio
async def test_create_knowledgebase_accepts_a_verified_endpoint_without_service(monkeypatch):
    credential = object()

    class FakeClient:
        def __init__(self, *, endpoint, credential):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, traceback):
            return None

        async def create_or_update_knowledge_source(self, *, knowledge_source):
            pass

        async def create_or_update_knowledge_base(self, *, knowledge_base):
            assert (
                knowledge_base.models[0].azure_open_ai_parameters.resource_url == "https://canonical.openai.azure.com/"
            )

    monkeypatch.setattr(create_knowledgebase_module, "create_credential", lambda: credential)
    monkeypatch.setattr(create_knowledgebase_module, "SearchIndexClient", FakeClient)
    monkeypatch.setattr(create_knowledgebase_module, "load_azd_env", lambda: {})
    monkeypatch.delenv("AZURE_OPENAI_SERVICE", raising=False)
    for key, value in {
        "AZURE_SEARCH_SERVICE": "search",
        "AZURE_SEARCH_INDEX": "index-v4-staging-test",
        "AZURE_SEARCH_KNOWLEDGEBASE_NAME": "kb-v4-staging-test",
        "AZURE_OPENAI_ENDPOINT": "https://canonical.openai.azure.com",
        "AZURE_OPENAI_KNOWLEDGEBASE_DEPLOYMENT": "deployment",
        "AZURE_OPENAI_KNOWLEDGEBASE_MODEL": "model",
    }.items():
        monkeypatch.setenv(key, value)

    await create_knowledgebase_module.create_knowledgebase()
