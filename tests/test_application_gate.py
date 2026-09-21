import json

import pytest

from scripts.application_gate import (
    ApplicationGateError,
    validate_candidate_url,
    validate_provenance,
)
from scripts.gate_common import (
    GateFailure,
    auth_headers,
    candidate_url,
    failing_report,
    fetch_live_provenance,
    gate_parser,
    load_provenance,
    passing_report,
    post_chat,
    response_answer,
    response_sources,
    run_gate,
)

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


@pytest.mark.parametrize(
    "value, expected",
    [
        ("https://candidate.example.test/", "https://candidate.example.test"),
        ("http://localhost:50505", "http://localhost:50505"),
    ],
)
def test_candidate_url_normalizes_http_urls(value, expected):
    assert candidate_url(value) == expected


@pytest.mark.parametrize("value", ["candidate.example.test", "ftp://candidate.example.test"])
def test_candidate_url_rejects_non_http_urls(value):
    with pytest.raises(GateFailure, match="HTTP or HTTPS"):
        candidate_url(value)


def test_load_provenance_accepts_complete_schema_v1_payload(tmp_path):
    provenance_path = tmp_path / "provenance.json"
    provenance_path.write_text(json.dumps(VALID_PROVENANCE), encoding="utf-8")

    assert load_provenance(provenance_path) == EXPECTED


@pytest.mark.parametrize("payload", [[], {"schema_version": 2}, {**VALID_PROVENANCE, "release_id": ""}])
def test_load_provenance_rejects_incompatible_or_incomplete_payloads(tmp_path, payload):
    provenance_path = tmp_path / "provenance.json"
    provenance_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(GateFailure, match="provenance"):
        load_provenance(provenance_path)


def test_load_provenance_rejects_invalid_json(tmp_path):
    provenance_path = tmp_path / "provenance.json"
    provenance_path.write_text("not json", encoding="utf-8")

    with pytest.raises(GateFailure, match="Cannot load"):
        load_provenance(provenance_path)


@pytest.mark.asyncio
async def test_post_chat_builds_agentic_request_and_validates_result():
    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {"message": {"content": "answer"}}

    class Client:
        async def post(self, url, json):
            assert url == "https://candidate.example.test/chat"
            assert json["messages"] == [{"role": "user", "content": "question"}]
            assert json["context"]["overrides"]["include_category"] == "Guide"
            assert json["context"]["overrides"]["top"] == 3
            assert json["context"]["overrides"]["use_agentic_knowledgebase"] is True
            return Response()

    assert await post_chat(Client(), "https://candidate.example.test", "question", "Guide", 3, True) == {
        "message": {"content": "answer"}
    }


@pytest.mark.parametrize(
    "result, helper, message",
    [
        ({}, response_answer, "no answer"),
        ({"message": {"content": 1}}, response_answer, "no answer"),
        ({}, response_sources, "no text sources"),
        ({"context": {"data_points": {"text": ["not-a-source"]}}}, response_sources, "no text sources"),
    ],
)
def test_response_helpers_reject_incomplete_chat_payloads(result, helper, message):
    with pytest.raises(GateFailure, match=message):
        helper(result)


def test_response_helpers_return_answer_and_dict_sources():
    result = {
        "message": {"content": " answer "},
        "context": {"data_points": {"text": [{"source": "one"}, "not-a-source"]}},
    }
    assert response_answer(result) == " answer "
    assert response_sources(result) == [{"source": "one"}]


def test_reports_capture_pass_and_failure_context():
    report = passing_report("retrieval", [{"status": "PASS"}], details={"count": 1}, provenance=EXPECTED)

    assert report["status"] == "PASS"
    assert report["details"] == {"count": 1}
    assert report["provenance"] == EXPECTED
    assert failing_report("retrieval", GateFailure("unavailable"))["error"] == "unavailable"


def test_gate_parser_accepts_candidate_gate_arguments(tmp_path):
    args = gate_parser("candidate gate").parse_args(
        ["--provenance", str(tmp_path / "provenance.json"), "--output", str(tmp_path / "output.json")]
    )

    assert args.candidate_url == "http://localhost:50505"
    assert args.provenance == tmp_path / "provenance.json"
    assert args.output == tmp_path / "output.json"


@pytest.mark.asyncio
async def test_post_chat_wraps_transport_and_non_object_response_errors():
    class FailingClient:
        async def post(self, *_args, **_kwargs):
            import httpx

            raise httpx.ConnectError("unavailable")

    with pytest.raises(GateFailure, match="Chat request failed"):
        await post_chat(FailingClient(), "https://candidate.example.test", "question")

    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return []

    class Client:
        async def post(self, *_args, **_kwargs):
            return Response()

    with pytest.raises(GateFailure, match="JSON object"):
        await post_chat(Client(), "https://candidate.example.test", "question")


def test_run_gate_writes_a_fail_closed_report_when_provenance_is_invalid(tmp_path):
    provenance_path = tmp_path / "provenance.json"
    provenance_path.write_text("{}", encoding="utf-8")
    output = tmp_path / "gate.json"

    result = run_gate(
        "retrieval",
        output,
        operation=lambda *_: None,
        base_url="https://candidate.example.test",
        provenance_path=provenance_path,
    )

    assert result == 1
    assert json.loads(output.read_text(encoding="utf-8"))["status"] == "FAIL"


def test_run_gate_writes_success_report_for_verified_candidate(monkeypatch, tmp_path):
    provenance_path = tmp_path / "provenance.json"
    provenance_path.write_text(json.dumps(VALID_PROVENANCE), encoding="utf-8")
    output = tmp_path / "nested" / "gate.json"

    async def fetch(*_args):
        return EXPECTED

    async def operation(url, provenance, headers):
        assert url == "https://candidate.example.test"
        assert provenance == EXPECTED
        assert headers == {"Authorization": "Bearer token"}
        return passing_report("retrieval", [{"status": "PASS"}], provenance=provenance)

    monkeypatch.setattr("scripts.gate_common.fetch_live_provenance", fetch)
    assert (
        run_gate(
            "retrieval",
            output,
            operation,
            "https://candidate.example.test",
            provenance_path,
            auth_token="token",
        )
        == 0
    )
    assert json.loads(output.read_text(encoding="utf-8"))["status"] == "PASS"
