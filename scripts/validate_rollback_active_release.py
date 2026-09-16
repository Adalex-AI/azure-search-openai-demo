"""Validate the live application identity restored by a paired rollback."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


class RollbackValidationError(ValueError):
    """Raised when the live application does not match the rollback plan."""


def _expected(plan: dict[str, Any]) -> dict[str, str]:
    fields = {
        key: str(plan.get(key) or "").strip()
        for key in ("image_digest", "revision_name", "release_id", "search_index", "knowledge_base", "platform")
    }
    if any(not fields[key] for key in fields):
        raise RollbackValidationError("Rollback plan is missing a required identity field")
    if "@sha256:" not in fields["image_digest"]:
        raise RollbackValidationError("Rollback image is not immutable")
    return fields


def _environment(app: Any, platform: str) -> dict[str, str]:
    if platform == "appservice":
        if not isinstance(app, list):
            raise RollbackValidationError("App Service settings response must be a JSON array")
        return {
            str(item.get("name")): str(item.get("value") or "")
            for item in app
            if isinstance(item, dict) and item.get("name")
        }
    if not isinstance(app, dict):
        raise RollbackValidationError("Container App response must be a JSON object")
    containers = app.get("properties", {}).get("template", {}).get("containers", [])
    if not isinstance(containers, list) or not containers or not isinstance(containers[0], dict):
        raise RollbackValidationError("Container App has no deployed containers")
    environment = containers[0].get("env", [])
    values = {
        str(item.get("name")): str(item.get("value") or "")
        for item in environment
        if isinstance(item, dict) and item.get("name")
    }
    values["V4_IMAGE_DIGEST"] = str(containers[0].get("image") or "")
    values["V4_REVISION_NAME"] = str(app.get("properties", {}).get("latestRevisionName") or "")
    traffic = app.get("properties", {}).get("configuration", {}).get("ingress", {}).get("traffic")
    revision = values["V4_REVISION_NAME"]
    if (
        not isinstance(traffic, list)
        or sum(
            int(item.get("weight") or 0)
            for item in traffic
            if isinstance(item, dict) and item.get("revisionName") == revision
        )
        != 100
    ):
        raise RollbackValidationError("Restored Container App revision does not receive 100% traffic")
    return values


def validate_active_rollback(app: Any, plan: dict[str, Any], platform: str) -> str:
    expected = _expected(plan)
    if expected["platform"] != platform:
        raise RollbackValidationError("Rollback platform does not match the deployment target")
    actual = _environment(app, platform)
    for field in ("image_digest", "revision_name", "release_id", "search_index", "knowledge_base"):
        actual_key = {
            "image_digest": "V4_IMAGE_DIGEST",
            "revision_name": "V4_REVISION_NAME",
            "release_id": "V4_RELEASE_ID",
            "search_index": "AZURE_SEARCH_INDEX",
            "knowledge_base": "AZURE_SEARCH_KNOWLEDGEBASE_NAME",
        }[field]
        if actual.get(actual_key, "").strip() != expected[field]:
            raise RollbackValidationError(f"Restored {field} does not match rollback plan")
    return expected["release_id"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app-json", type=Path, required=True)
    parser.add_argument("--rollback-json", type=Path, required=True)
    parser.add_argument("--platform", choices=("containerapps", "appservice"), required=True)
    args = parser.parse_args()
    try:
        app = json.loads(args.app_json.read_text(encoding="utf-8"))
        plan = json.loads(args.rollback_json.read_text(encoding="utf-8"))
        if not isinstance(plan, dict):
            raise RollbackValidationError("Rollback plan must be a JSON object")
        print(validate_active_rollback(app, plan, args.platform))
    except (OSError, json.JSONDecodeError, RollbackValidationError) as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
