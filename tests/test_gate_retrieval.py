import pytest

from scripts import gate_retrieval

PROVENANCE = {"release_id": "release-1"}


def chat_result(answer="CPR Part 31 disclosure", *, agentic=True):
    thoughts = [{"title": "Agentic retrieval response"}] if agentic else []
    return {
        "message": {"content": answer},
        "context": {
            "data_points": {"text": [{"source": "guide"}]},
            "thoughts": thoughts,
        },
    }


@pytest.mark.asyncio
async def test_run_records_each_agentic_retrieval_case(monkeypatch):
    async def post_chat(_client, _candidate, question, **_kwargs):
        answers = {
            "Part 31": "CPR Part 31 disclosure",
            "Part 52": "CPR Part 52 appeal",
            "Commercial Court": "Commercial Court case management",
            "31.16": "CPR 31.16 pre-action disclosure",
        }
        return chat_result(next(answer for key, answer in answers.items() if key in question))

    monkeypatch.setattr(gate_retrieval, "post_chat", post_chat)
    report = await gate_retrieval.run("https://candidate.example.test", PROVENANCE, {"Authorization": "Bearer token"})

    assert report["status"] == "PASS"
    assert report["gate"] == "retrieval"
    assert [check["id"] for check in report["checks"]] == [case[0] for case in gate_retrieval.CASES]
    assert all(check["retrieval_mode"] == "agentic" for check in report["checks"])


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "result, message",
    [
        (chat_result("unrelated answer"), "answer lacks"),
        (chat_result(agentic=False), "does not prove agentic"),
    ],
)
async def test_run_rejects_unproven_retrieval_evidence(monkeypatch, result, message):
    async def post_chat(*_args, **_kwargs):
        return result

    monkeypatch.setattr(gate_retrieval, "post_chat", post_chat)
    with pytest.raises(ValueError, match=message):
        await gate_retrieval.run("https://candidate.example.test", PROVENANCE, {})
