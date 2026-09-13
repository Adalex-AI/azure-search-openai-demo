import pytest

from scripts.application_gate import ApplicationGateError, validate_candidate_url, validate_provenance
from scripts.gate_common import GateFailure, auth_headers, fetch_live_provenance


VALID_PROVENANCE = {
    "schema_version": 1,
    "release_id": "release-123",
    "git_sha": "abc123",
    "deployment_id": "candidate-456",
    "artifact_sha256": "artifact-hash",
    "search_snapshot_sha256": "snapshot-hash",
    "search_service": "search-service",
    "search_index": "legal-court-rag-v4-release-123",
    "knowledge_base": "legal-court-rag-v4-release-123-agent-upgrade",
    "image_digest": "registry.example.test/legal-rag@sha256:" + "a" * 64,
    "revision_name": "legal-rag--release-123",
    "agentic_mode": "agentic",
}

EXPECTED = {field: VALID_PROVENANCE[field] for field in VALID_PROVENANCE if field != "schema_version"}


def test_validate_candidate_url_accepts_explicit_staging_https_url():
    assert validate_candidate_url("https://candidate.example.test/") == "https://candidate.example.test"


@pytest.mark.parametrize(
    "candidate_url, message",
    [
        ("", "HTTPS URL"),
        ("http://candidate.example.test", "HTTPS URL"),
        ("https://localhost:50505", "must not be local"),
        ("https://legal-rag-v3.example.test", "must not identify a v3"),
    ],
)
def test_validate_candidate_url_rejects_unsafe_fallbacks(candidate_url, message):
    with pytest.raises(ApplicationGateError, match=message):
        validate_candidate_url(candidate_url)


def test_validate_provenance_accepts_complete_matching_payload():
    assert validate_provenance(VALID_PROVENANCE, EXPECTED) == EXPECTED


@pytest.mark.parametrize(
    "change, message",
    [
        ({"schema_version": 2}, "schema version"),
        ({"release_id": ""}, "missing: release_id"),
        ({"search_index": "legal-court-rag-index-v3"}, "mismatch: search_index"),
    ],
)
def test_validate_provenance_rejects_untrusted_payloads(change, message):
    payload = {**VALID_PROVENANCE, **change}
    with pytest.raises(ApplicationGateError, match=message):
        validate_provenance(payload, EXPECTED)


def test_auth_headers_forward_explicit_token_and_cookie():
    assert auth_headers("token-1", "session=abc") == {
        "Authorization": "Bearer token-1",
        "Cookie": "session=abc",
    }


@pytest.mark.asyncio
async def test_live_provenance_rejects_auth_failure_and_mismatch(monkeypatch):
    class Response:
        def __init__(self, status_code, payload=None):
            self.status_code = status_code
            self._payload = payload

        def raise_for_status(self):
            if self.status_code >= 400:
                import httpx

                raise httpx.HTTPStatusError("auth failure", request=None, response=None)

        def json(self):
            return self._payload

    class Client:
        response = Response(401)

        def __init__(self, *args, **kwargs):
            self.headers = kwargs["headers"]

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def get(self, url):
            assert self.headers["Authorization"] == "Bearer token-1"
            return self.response

    monkeypatch.setattr("scripts.gate_common.httpx.AsyncClient", Client)
    with pytest.raises(GateFailure, match="provenance request failed"):
        await fetch_live_provenance("https://candidate.example.test", EXPECTED, "proof", auth_headers("token-1"))

    Client.response = Response(200, {**VALID_PROVENANCE, "search_index": "other-index"})
    with pytest.raises(GateFailure, match="provenance mismatch: search_index"):
        await fetch_live_provenance("https://candidate.example.test", EXPECTED, "proof", auth_headers("token-1"))