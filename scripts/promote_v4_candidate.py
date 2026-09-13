"""Validate an approved v4 candidate before a blue/green application cutover.

This command is deliberately non-destructive. It validates the release evidence
bundle and emits the exact target pair that a separately approved deployment may
switch to; it never mutates Search, deletes an index, or changes application
configuration.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

LEGACY_INDEX = "legal-court-rag-index-v3"


class PromotionError(ValueError):
    """Raised when a candidate is not eligible for production promotion."""


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as error:
        raise PromotionError(f"Evidence file cannot be read: {path}") from error
    return digest.hexdigest()


def _require_string(bundle: dict[str, Any], field: str) -> str:
    value = str(bundle.get(field) or "").strip()
    if not value:
        raise PromotionError(f"Evidence bundle is missing {field}")
    return value


def _validate_rollback_pair(index_name: str, knowledgebase_name: str) -> None:
    """Allow the bootstrap v3 pair or a structurally matching v4 pair."""
    if index_name.casefold() == LEGACY_INDEX.casefold():
        if "v3" not in knowledgebase_name.casefold():
            raise PromotionError("Rollback knowledge base must identify the v3 production pair")
        return
    if "v4" not in index_name.casefold() or "v4" not in knowledgebase_name.casefold():
        raise PromotionError("Rollback target must be the v3 fallback or a v4 release pair")
    if index_name.casefold() not in knowledgebase_name.casefold():
        raise PromotionError("Rollback knowledge-base target must identify the rollback index")


def validate_evidence_bundle(bundle: dict[str, Any], expected_release_id: str | None = None) -> dict[str, str]:
    if bundle.get("approved") is not True:
        raise PromotionError("Evidence bundle is not approved")
    if str(bundle.get("approval_environment") or "") != "Production":
        raise PromotionError("Evidence bundle requires Production approval")

    index_name = _require_string(bundle, "candidate_index")
    knowledgebase_name = _require_string(bundle, "candidate_knowledgebase")
    artifact_sha256 = _require_string(bundle, "artifact_sha256")
    snapshot_sha256 = _require_string(bundle, "search_snapshot_sha256")
    rollback_index = _require_string(bundle, "rollback_index")
    rollback_knowledgebase = _require_string(bundle, "rollback_knowledgebase")
    fidelity = bundle.get("fidelity")
    if not isinstance(fidelity, dict):
        raise PromotionError("Evidence bundle is missing fidelity results")
    if any(int(fidelity.get(field, 0) or 0) for field in ("unmatched", "ambiguous", "unavailable", "unclassified")):
        raise PromotionError("Fidelity gate is not clean")
    if fidelity.get("substantive_coverage") != 1.0:
        raise PromotionError("Fidelity gate does not report 100% substantive coverage")
    artifact_search = bundle.get("artifact_search")
    if not isinstance(artifact_search, dict) or any(
        int(artifact_search.get(field, 0) or 0) for field in ("missing_count", "extra_count", "mismatched_count")
    ):
        raise PromotionError("Artifact/Search equality gate is not clean")
    candidate_validation = bundle.get("candidate_validation")
    if not isinstance(candidate_validation, dict) or candidate_validation.get("status") != "PASS":
        raise PromotionError("Candidate Search validation gate is not clean")
    if any(LEGACY_INDEX.casefold() in target.casefold() for target in (index_name, knowledgebase_name)):
        raise PromotionError("Refusing to promote or mutate the legacy v3 target")
    if "v4" not in index_name.casefold() or "v4" not in knowledgebase_name.casefold():
        raise PromotionError("Candidate targets must contain v4")
    if index_name.casefold() not in knowledgebase_name.casefold():
        raise PromotionError("Knowledge-base target must identify the candidate index")
    application_gates = bundle.get("application_gates")
    if (
        not isinstance(application_gates, dict)
        or application_gates.get("schema_version") != 1
        or application_gates.get("status") != "PASS"
    ):
        raise PromotionError("Application-gate validation is not clean")
    gates = application_gates.get("gates")
    required_gates = {"retrieval", "category", "source_hierarchy", "citation", "acl", "highlight"}
    if not isinstance(gates, dict) or set(gates) != required_gates:
        raise PromotionError("Application-gate evidence must contain all six required gates")
    for gate_name, gate in gates.items():
        if not isinstance(gate, dict) or gate.get("status") != "PASS" or gate.get("gate") != gate_name:
            raise PromotionError(f"Application-gate evidence is missing a passing {gate_name} gate")
    highlight_gate = gates["highlight"]
    if int(highlight_gate.get("case_count", 0) or 0) <= 0 or int(highlight_gate.get("source_count", 0) or 0) <= 0:
        raise PromotionError("Application-gate highlight evidence is empty")
    application_provenance = application_gates.get("provenance")
    if not isinstance(application_provenance, dict):
        raise PromotionError("Application-gate evidence is missing provenance")
    for field in (
        "release_id",
        "git_sha",
        "deployment_id",
        "search_service",
        "image_digest",
        "revision_name",
        "agentic_mode",
    ):
        if not str(application_provenance.get(field) or "").strip():
            raise PromotionError(f"Application-gate provenance is missing {field}")
    if "@sha256:" not in application_provenance["image_digest"]:
        raise PromotionError("Application-gate provenance image_digest must be immutable")
    for field, expected in {
        "search_index": index_name,
        "knowledge_base": knowledgebase_name,
        "artifact_sha256": artifact_sha256,
        "search_snapshot_sha256": snapshot_sha256,
    }.items():
        if application_provenance.get(field) != expected:
            raise PromotionError(f"Application-gate provenance does not match {field}")
    if expected_release_id is not None and application_provenance.get("release_id") != expected_release_id:
        raise PromotionError("Application-gate provenance does not match release_id")
    bundle_release_id = _require_string(bundle, "release_id")
    if application_provenance.get("release_id") != bundle_release_id:
        raise PromotionError("Evidence bundle release_id does not match application provenance")

    evidence_paths = {
        "artifact_path": "artifact_sha256",
        "search_snapshot_path": "search_snapshot_sha256",
    }
    for path_field, hash_field in evidence_paths.items():
        path_value = bundle.get(path_field)
        if path_value:
            path = Path(str(path_value))
            if _sha256_file(path) != bundle[hash_field]:
                raise PromotionError(f"Evidence hash does not match {path_field}")
    if bundle.get("evidence_sha256"):
        canonical = json.dumps(
            {
                key: value
                for key, value in bundle.items()
                if key not in {"created_at_utc", "approved", "approval_environment", "evidence_sha256"}
            },
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        )
        expected_evidence_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        if bundle["evidence_sha256"] != expected_evidence_hash:
            raise PromotionError("Evidence bundle digest does not match its contents")
    _validate_rollback_pair(rollback_index, rollback_knowledgebase)
    if rollback_index == index_name or rollback_knowledgebase == knowledgebase_name:
        raise PromotionError("Rollback target must be distinct from the candidate target")
    rollback_application = bundle.get("rollback_application")
    if not isinstance(rollback_application, dict):
        raise PromotionError("Evidence bundle is missing rollback application identity")
    rollback_image = str(rollback_application.get("image_digest") or "").strip()
    rollback_revision = str(rollback_application.get("revision_name") or "").strip()
    rollback_release_id = str(rollback_application.get("release_id") or "").strip()
    if "@sha256:" not in rollback_image:
        raise PromotionError("Rollback application image must be immutable")
    if not rollback_revision:
        raise PromotionError("Rollback application identity is missing revision_name")
    if not rollback_release_id or rollback_release_id == bundle_release_id:
        raise PromotionError("Rollback application identity is missing a valid release_id")
    if rollback_application.get("search_index") != rollback_index:
        raise PromotionError("Rollback application identity does not match rollback_index")
    if rollback_application.get("knowledge_base") != rollback_knowledgebase:
        raise PromotionError("Rollback application identity does not match rollback_knowledgebase")

    return {
        "candidate_index": index_name,
        "candidate_knowledgebase": knowledgebase_name,
        "artifact_sha256": artifact_sha256,
        "search_snapshot_sha256": snapshot_sha256,
        "image_digest": application_provenance["image_digest"],
        "revision_name": application_provenance["revision_name"],
        "rollback_index": rollback_index,
        "rollback_knowledgebase": rollback_knowledgebase,
        "rollback_image_digest": rollback_image,
        "rollback_revision_name": rollback_revision,
        "rollback_release_id": rollback_release_id,
        "rollback_platform": str(rollback_application.get("platform") or "containerapps"),
    }


def load_and_validate(path: Path, expected_release_id: str | None = None) -> dict[str, str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise PromotionError("Evidence bundle must be a JSON object")
    evidence_manifest = payload.get("evidence_manifest")
    if evidence_manifest is not None:
        if not isinstance(evidence_manifest, list) or not evidence_manifest:
            raise PromotionError("Evidence manifest is empty")
        base_path = path.parent.resolve()
        for entry in evidence_manifest:
            if not isinstance(entry, dict) or not all(
                str(entry.get(field) or "").strip() for field in ("name", "path", "sha256")
            ):
                raise PromotionError("Evidence manifest contains an invalid entry")
            relative_path = Path(str(entry["path"]))
            if relative_path.is_absolute() or ".." in relative_path.parts:
                raise PromotionError("Evidence manifest contains an unsafe relative path")
            evidence_path = (base_path / relative_path).resolve()
            if base_path not in evidence_path.parents or _sha256_file(evidence_path) != entry["sha256"]:
                raise PromotionError(f"Evidence manifest hash does not match {entry['path']}")
    return validate_evidence_bundle(payload, expected_release_id=expected_release_id)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--release-id")
    args = parser.parse_args()
    print(json.dumps(load_and_validate(args.evidence, expected_release_id=args.release_id), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
