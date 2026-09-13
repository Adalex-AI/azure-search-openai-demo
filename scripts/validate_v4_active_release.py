"""Fail closed when a deployed v4 app has an unexpected release identity."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


class ActiveReleaseError(ValueError):
    """Raised when the deployed app has an unsafe release identity."""


def _template_environment(app: dict[str, Any]) -> dict[str, str]:
    containers = app.get("properties", {}).get("template", {}).get("containers", [])
    if not isinstance(containers, list) or not containers:
        raise ActiveReleaseError("Container App has no deployed containers")
    environment = containers[0].get("env", [])
    if not isinstance(environment, list):
        raise ActiveReleaseError("Container App template environment is invalid")
    return {
        str(item.get("name")): str(item.get("value") or "")
        for item in environment
        if isinstance(item, dict) and item.get("name")
    }


def _serving_identity(app: dict[str, Any]) -> tuple[str, str]:
    template = app.get("properties", {}).get("template", {})
    containers = template.get("containers", [])
    if not isinstance(containers, list) or not containers or not isinstance(containers[0], dict):
        raise ActiveReleaseError("Container App has no deployed containers")
    image = str(containers[0].get("image") or "").strip()
    revision = str(app.get("properties", {}).get("latestRevisionName") or "").strip()
    if "@sha256:" not in image:
        raise ActiveReleaseError("Deployed Container App image is not immutable")
    if not revision:
        raise ActiveReleaseError("Deployed Container App has no latest revision name")
    return image, revision


def _validate_active_traffic(app: dict[str, Any], revision: str) -> None:
    traffic = app.get("properties", {}).get("configuration", {}).get("ingress", {}).get("traffic")
    if not isinstance(traffic, list) or not traffic:
        raise ActiveReleaseError("Container App active traffic configuration is invalid")
    matching_weight = sum(
        int(item.get("weight") or 0)
        for item in traffic
        if isinstance(item, dict) and item.get("revisionName") == revision
    )
    if matching_weight != 100:
        raise ActiveReleaseError(f"Latest revision {revision!r} does not receive 100% active traffic")


def validate_active_release(
    app: dict[str, Any],
    expected_release_id: str,
    *,
    expected_image_digest: str | None = None,
    expected_revision_name: str | None = None,
) -> str:
    expected = expected_release_id.strip()
    if not expected:
        raise ActiveReleaseError("Expected release ID must not be empty")
    if any(label in expected.casefold() for label in ("r4", "v3", "legacy")):
        raise ActiveReleaseError(f"Refusing a legacy release ID: {expected}")
    actual = _template_environment(app).get("V4_RELEASE_ID", "").strip()
    if not actual:
        raise ActiveReleaseError("Deployed Container App has no active V4 release ID")
    if any(label in actual.casefold() for label in ("r4", "v3", "legacy")):
        raise ActiveReleaseError(f"Deployed Container App advertises a legacy release ID: {actual}")
    if actual != expected:
        raise ActiveReleaseError(f"Active V4 release mismatch: deployed {actual!r}, expected {expected!r}")
    image, revision = _serving_identity(app)
    if expected_image_digest and image != expected_image_digest.strip():
        raise ActiveReleaseError(f"Active image mismatch: deployed {image!r}, expected {expected_image_digest!r}")
    if expected_revision_name and revision != expected_revision_name.strip():
        raise ActiveReleaseError(
            f"Active revision mismatch: deployed {revision!r}, expected {expected_revision_name!r}"
        )
    _validate_active_traffic(app, revision)
    return actual


def validate_appservice_release(
    settings: list[dict[str, Any]],
    expected_release_id: str,
    *,
    expected_image_digest: str | None = None,
    expected_revision_name: str | None = None,
) -> str:
    environment = {
        str(item.get("name")): str(item.get("value") or "")
        for item in settings
        if isinstance(item, dict) and item.get("name")
    }
    expected = expected_release_id.strip()
    if not expected or any(label in expected.casefold() for label in ("r4", "v3", "legacy")):
        raise ActiveReleaseError(f"Refusing a legacy App Service release ID: {expected}")
    actual = environment.get("V4_RELEASE_ID", "").strip()
    if not actual or any(label in actual.casefold() for label in ("r4", "v3", "legacy")) or actual != expected:
        raise ActiveReleaseError(f"Active App Service release mismatch: deployed {actual!r}, expected {expected!r}")
    image = environment.get("V4_IMAGE_DIGEST", "").strip()
    revision = environment.get("V4_REVISION_NAME", "").strip()
    if "@sha256:" not in image:
        raise ActiveReleaseError("Active App Service image is not immutable")
    if not revision:
        raise ActiveReleaseError("Active App Service has no revision name")
    if expected_image_digest and image != expected_image_digest.strip():
        raise ActiveReleaseError(f"Active image mismatch: deployed {image!r}, expected {expected_image_digest!r}")
    if expected_revision_name and revision != expected_revision_name.strip():
        raise ActiveReleaseError(
            f"Active revision mismatch: deployed {revision!r}, expected {expected_revision_name!r}"
        )
    return actual


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app-json", type=Path, required=True)
    parser.add_argument("--expected-release-id", required=True)
    parser.add_argument("--platform", choices=("containerapps", "appservice"), default="containerapps")
    parser.add_argument("--expected-image-digest")
    parser.add_argument("--expected-revision-name")
    args = parser.parse_args()
    try:
        app = json.loads(args.app_json.read_text(encoding="utf-8"))
        if args.platform == "appservice":
            if not isinstance(app, list):
                raise ActiveReleaseError("App Service settings response must be a JSON array")
            result = validate_appservice_release(
                app,
                args.expected_release_id,
                expected_image_digest=args.expected_image_digest,
                expected_revision_name=args.expected_revision_name,
            )
        else:
            if not isinstance(app, dict):
                raise ActiveReleaseError("Container App response must be a JSON object")
            result = validate_active_release(
                app,
                args.expected_release_id,
                expected_image_digest=args.expected_image_digest,
                expected_revision_name=args.expected_revision_name,
            )
        print(result)
    except (OSError, json.JSONDecodeError, ActiveReleaseError) as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
