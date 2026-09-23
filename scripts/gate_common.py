"""Shared helpers for v4 candidate application gates."""

from __future__ import annotations

import argparse
import asyncio
import json
from collections.abc import Awaitable, Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

try:
    from .application_gate import validate_candidate_url, validate_provenance
except ImportError:
    from application_gate import validate_candidate_url, validate_provenance


class GateFailure(ValueError):
    """Raised when a candidate behavior gate cannot be proven."""


def gate_parser(description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--candidate-url", required=True)
    parser.add_argument("--provenance", type=Path, required=True)
    parser.add_argument("--provenance-token", default="")
    parser.add_argument("--output", type=Path, required=True)
    return parser


def load_provenance(path: Path) -> dict[str, str]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise GateFailure(f"Cannot load candidate provenance: {path}") from error
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise GateFailure("Candidate provenance must be a schema version 1 object")
    fields = (
        "release_id",
        "git_sha",
        "deployment_id",
        "artifact_sha256",
        "search_snapshot_sha256",
        "search_service",
        "search_index",
        "knowledge_base",
        "image_digest",
        "revision_name",
        "agentic_mode",
    )
    missing = [field for field in fields if not str(payload.get(field) or "").strip()]
    if missing:
        raise GateFailure(f"Candidate provenance is missing: {', '.join(missing)}")
    return {field: str(payload[field]).strip() for field in fields}


async def fetch_live_provenance(base_url: str, expected: dict[str, str], token: str) -> dict[str, str]:
    headers = {"X-V4-Provenance-Token": token} if token.strip() else {}
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(f"{base_url}/api/provenance", headers=headers)
            response.raise_for_status()
            payload = response.json()
    except (httpx.HTTPError, ValueError) as error:
        raise GateFailure(f"Candidate provenance request failed: {error}") from error
    try:
        return validate_provenance(payload, expected)
    except ValueError as error:
        raise GateFailure(str(error)) from error


async def post_chat(
    client: httpx.AsyncClient,
    base_url: str,
    question: str,
    category: str = "",
    top: int = 5,
    use_agentic_retrieval: bool = False,
) -> dict[str, Any]:
    payload = {
        "messages": [{"role": "user", "content": question}],
        "context": {
            "overrides": {
                "retrieval_mode": "hybrid",
                "semantic_ranker": True,
                "semantic_captions": False,
                "top": top,
                "include_category": category,
                "send_text_sources": True,
                "suggest_followup_questions": False,
                "seed": 42,
                "use_agentic_knowledgebase": use_agentic_retrieval,
            }
        },
    }
    try:
        response = await client.post(f"{base_url}/chat", json=payload)
        response.raise_for_status()
        result = response.json()
    except (httpx.HTTPError, ValueError) as error:
        raise GateFailure(f"Chat request failed: {error}") from error
    if not isinstance(result, dict):
        raise GateFailure("Chat response must be a JSON object")
    return result


def response_answer(result: dict[str, Any]) -> str:
    answer = result.get("message", {}).get("content", "")
    if not isinstance(answer, str) or not answer.strip():
        raise GateFailure("Chat response contains no answer")
    return answer


def response_sources(result: dict[str, Any]) -> list[dict[str, Any]]:
    data_points = result.get("context", {}).get("data_points", {})
    values = data_points.get("text", []) if isinstance(data_points, dict) else []
    sources = [value for value in values if isinstance(value, dict)]
    if not sources:
        raise GateFailure("Chat response contains no text sources")
    return sources


def passing_report(
    gate: str,
    checks: list[dict[str, Any]],
    details: Any = None,
    provenance: dict[str, str] | None = None,
) -> dict[str, Any]:
    report: dict[str, Any] = {
        "schema_version": 1,
        "status": "PASS",
        "gate": gate,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
    }
    if provenance is not None:
        report["provenance"] = provenance
    if details is not None:
        report["details"] = details
    return report


def failing_report(gate: str, error: Exception) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "status": "FAIL",
        "gate": gate,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "error": str(error),
    }


def run_gate(
    gate: str,
    output: Path,
    operation: Callable[[str, dict[str, str]], Awaitable[dict[str, Any]]],
    base_url: str,
    provenance_path: Path,
    provenance_token: str = "",
) -> int:
    try:
        provenance = load_provenance(provenance_path)
        live_url = validate_candidate_url(base_url)
        live_provenance = asyncio.run(fetch_live_provenance(live_url, provenance, provenance_token))
        report = asyncio.run(operation(live_url, live_provenance))
    except (GateFailure, httpx.HTTPError, ValueError) as error:
        report = failing_report(gate, error)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"gate": gate, "output": str(output), "status": report["status"]}, sort_keys=True))
    return 0 if report["status"] == "PASS" else 1