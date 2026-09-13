"""Validate and optionally execute a paired V4 rollback plan.

The default operation is non-destructive: it validates approved evidence and
prints the exact Container Apps command required to restore the previous
immutable application revision and its previous Search pair. Azure mutation
requires both --execute and --confirm-rollback ROLLBACK-PREVIOUS.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from promote_v4_candidate import PromotionError, load_and_validate
else:
    try:
        from scripts.promote_v4_candidate import PromotionError, load_and_validate
    except ImportError:
        from promote_v4_candidate import PromotionError, load_and_validate


class RollbackError(ValueError):
    """Raised when a paired rollback cannot be safely planned."""


CONFIRMATION = "ROLLBACK-PREVIOUS"


def _containerapp_revision_suffix(revision_name: str, application_name: str) -> str:
    prefix = f"{application_name}--"
    suffix = revision_name[len(prefix) :] if revision_name.startswith(prefix) else revision_name
    if not suffix or len(suffix) > 63 or not suffix.replace("-", "").isalnum():
        raise RollbackError("Rollback revision name does not contain a valid Container Apps suffix")
    return suffix


def build_rollback_plan(
    evidence_path: Path,
    resource_group: str,
    application_name: str,
    expected_release_id: str | None = None,
) -> dict[str, Any]:
    if not resource_group.strip() or not application_name.strip():
        raise RollbackError("Rollback requires a resource group and application name")
    try:
        targets = load_and_validate(evidence_path, expected_release_id=expected_release_id)
    except (OSError, json.JSONDecodeError, PromotionError) as error:
        raise RollbackError(f"Rollback evidence is not eligible: {error}") from error
    rollback_image = targets["rollback_image_digest"]
    rollback_revision = targets["rollback_revision_name"]
    rollback_release_id = targets["rollback_release_id"]
    rollback_platform = targets.get("rollback_platform", "containerapps")
    if rollback_platform not in {"containerapps", "appservice"}:
        raise RollbackError("Rollback application platform must be appservice or containerapps")
    if rollback_platform == "containerapps":
        rollback_revision_suffix = _containerapp_revision_suffix(rollback_revision, application_name.strip())
        rollback_revision = f"{application_name.strip()}--{rollback_revision_suffix}"
    if rollback_platform == "appservice":
        command = [
            [
                "az",
                "webapp",
                "config",
                "container",
                "set",
                "--resource-group",
                resource_group.strip(),
                "--name",
                application_name.strip(),
                "--docker-custom-image-name",
                rollback_image,
            ],
            [
                "az",
                "webapp",
                "config",
                "appsettings",
                "set",
                "--resource-group",
                resource_group.strip(),
                "--name",
                application_name.strip(),
            ],
        ]
    else:
        command = [
            [
                "az",
                "containerapp",
                "update",
                "--resource-group",
                resource_group.strip(),
                "--name",
                application_name.strip(),
                "--image",
                rollback_image,
                "--revision-suffix",
                rollback_revision_suffix,
                "--set-env-vars",
            ]
        ]
    settings = [
        f"AZURE_SEARCH_INDEX={targets['rollback_index']}",
        f"AZURE_SEARCH_KNOWLEDGEBASE_NAME={targets['rollback_knowledgebase']}",
        f"V4_IMAGE_DIGEST={rollback_image}",
        f"V4_REVISION_NAME={rollback_revision}",
        f"V4_RELEASE_ID={rollback_release_id}",
        "RUNNING_IN_PRODUCTION=true",
    ]
    if rollback_platform == "appservice":
        command[1].extend(["--settings", *settings])
    else:
        command[0].extend(settings)
    return {
        "action": "rollback",
        "candidate_release_id": expected_release_id or "",
        "resource_group": resource_group.strip(),
        "application_name": application_name.strip(),
        "search_index": targets["rollback_index"],
        "knowledge_base": targets["rollback_knowledgebase"],
        "image_digest": rollback_image,
        "revision_name": rollback_revision,
        "release_id": rollback_release_id,
        "platform": rollback_platform,
        "command": command,
    }


def execute_plan(plan: dict[str, Any]) -> None:
    for command in plan["command"]:
        subprocess.run(command, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--resource-group", required=True)
    parser.add_argument("--application-name", required=True)
    parser.add_argument("--release-id")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--confirm-rollback", default="")
    args = parser.parse_args()
    plan = build_rollback_plan(args.evidence, args.resource_group, args.application_name, args.release_id)
    if args.execute:
        if args.confirm_rollback != CONFIRMATION:
            raise SystemExit(f"Refusing rollback execution; pass --confirm-rollback {CONFIRMATION}")
        execute_plan(plan)
        plan["executed"] = True
    else:
        plan["executed"] = False
    print(json.dumps(plan, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
