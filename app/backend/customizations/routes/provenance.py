"""Release provenance endpoint for candidate application validation."""

import hmac
import os

from quart import Blueprint, current_app, jsonify, request

provenance_bp = Blueprint("provenance", __name__, url_prefix="/api")

_PROVENANCE_FIELDS = {
    "release_id": "V4_RELEASE_ID",
    "git_sha": "GIT_SHA",
    "deployment_id": "DEPLOYMENT_ID",
    "artifact_sha256": "V4_ARTIFACT_SHA256",
    "search_snapshot_sha256": "V4_SEARCH_SNAPSHOT_SHA256",
    "image_digest": "V4_IMAGE_DIGEST",
}


def _configured_provenance() -> dict[str, str]:
    values = {field: os.getenv(name, "").strip() for field, name in _PROVENANCE_FIELDS.items()}
    values["revision_name"] = os.getenv("V4_REVISION_NAME", "").strip() or os.getenv(
        "CONTAINER_APP_REVISION_NAME", ""
    ).strip()
    values["search_service"] = os.getenv("AZURE_SEARCH_SERVICE", "").strip()
    values["search_index"] = str(current_app.config.get("PROVENANCE_SEARCH_INDEX", "")).strip()
    values["knowledge_base"] = str(current_app.config.get("PROVENANCE_KNOWLEDGE_BASE", "")).strip()
    values["agentic_mode"] = str(
        current_app.config.get("PROVENANCE_AGENTIC_MODE") or os.getenv("V4_AGENTIC_MODE", "agentic")
    ).strip()
    return values


@provenance_bp.get("/provenance")
async def get_provenance():
    expected_token = os.getenv("V4_PROVENANCE_TOKEN", "")
    if expected_token:
        supplied_token = request.headers.get("X-V4-Provenance-Token", "")
        if not hmac.compare_digest(supplied_token, expected_token):
            return jsonify({"error": "Unauthorized provenance request"}), 401
    values = _configured_provenance()
    missing = [field for field, value in values.items() if not value]
    if missing:
        current_app.logger.error("Candidate provenance is incomplete: %s", ", ".join(missing))
        return jsonify({"error": "Candidate provenance is incomplete", "missing": missing}), 503
    return jsonify({"schema_version": 1, **values}), 200