import asyncio

import pytest

from scripts import gate_acl


def test_search_credential_uses_azure_cli_for_workflow(monkeypatch):
    monkeypatch.setenv("V4_SEARCH_CREDENTIAL", "azure-cli")
    monkeypatch.setattr(gate_acl, "AzureCliCredential", lambda **kwargs: ("azure-cli", kwargs))

    assert gate_acl.create_search_credential("tenant-1") == ("azure-cli", {"tenant_id": "tenant-1"})


def test_unknown_search_credential_fails_closed(monkeypatch):
    monkeypatch.setenv("V4_SEARCH_CREDENTIAL", "unknown")

    with pytest.raises(gate_acl.GateFailure, match="V4_SEARCH_CREDENTIAL"):
        gate_acl.create_search_credential("tenant-1")


def test_search_token_failure_propagates_and_closes_credential(monkeypatch):
    class FailingCredential:
        closed = False

        async def get_token(self, *scopes):
            raise RuntimeError("token failure")

        async def close(self):
            self.closed = True

    credential = FailingCredential()
    monkeypatch.setattr(gate_acl, "create_search_credential", lambda tenant_id: credential)

    with pytest.raises(RuntimeError, match="token failure"):
        asyncio.run(gate_acl.search_counts("search-service", "index-name", "tenant-1"))

    assert credential.closed is True
