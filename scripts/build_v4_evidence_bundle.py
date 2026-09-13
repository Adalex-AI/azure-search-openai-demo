"""Build a deterministic, fail-closed v4 release evidence bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from gate_highlight_browser import BrowserGateError, validate_browser_evidence
else:
    try:
        from scripts.gate_highlight_browser import (
            BrowserGateError,
            validate_browser_evidence,
        )
    except ImportError:
        from gate_highlight_browser import BrowserGateError, validate_browser_evidence


class EvidenceError(ValueError):
    """Raised when release evidence is incomplete or fails the fidelity gate."""


SEARCH_FIELDS = (
    "id",
    "content",
    "category",
    "sourcepage",
    "sourcefile",
    "storageUrl",
    "updated",
    "parent_id",
    "subsection_id",
    "subsections",
)

APPLICATION_PROVENANCE_FIELDS = (
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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _evidence_root(paths: tuple[Path, ...]) -> Path:
    return Path(os.path.commonpath([str(path.resolve()) for path in paths]))


def _evidence_manifest(paths: tuple[Path, ...], root: Path) -> list[dict[str, str]]:
    return [
        {
            "name": path.name,
            "path": path.resolve().relative_to(root.resolve()).as_posix(),
            "sha256": sha256_file(path),
        }
        for path in paths
    ]


def _load_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise EvidenceError(f"Evidence input must be a JSON object: {path}")
    return payload


def fidelity_gate(
    report: dict[str, Any],
    expected_snapshot: dict[str, Any] | None = None,
    expected_source_count: int | None = None,
    expected_source_identity_digest: str | None = None,
) -> dict[str, Any]:
    if report.get("schema_version") != 2:
        raise EvidenceError("Fidelity report must use schema version 2")
    if report.get("complete") is not True:
        raise EvidenceError("Fidelity report is incomplete")
    for field in ("run_id", "started_at_utc", "completed_at_utc"):
        if not isinstance(report.get(field), str) or not report[field].strip():
            raise EvidenceError(f"Fidelity report is missing {field}")
    try:
        started_at = datetime.fromisoformat(report["started_at_utc"].replace("Z", "+00:00"))
        completed_at = datetime.fromisoformat(report["completed_at_utc"].replace("Z", "+00:00"))
    except ValueError as error:
        raise EvidenceError("Fidelity report timestamps are invalid") from error
    if started_at.tzinfo is None or completed_at.tzinfo is None or completed_at < started_at:
        raise EvidenceError("Fidelity report timestamp ordering is invalid")
    snapshot_provenance = report.get("snapshot_provenance")
    if not isinstance(snapshot_provenance, dict) or snapshot_provenance.get("verified") is not True:
        raise EvidenceError("Fidelity report requires a verified Search snapshot provenance envelope")
    if expected_snapshot is not None:
        for field in ("schema_version", "service", "index", "documents_sha256"):
            if snapshot_provenance.get(field) != expected_snapshot.get(field):
                raise EvidenceError(f"Fidelity snapshot provenance does not match Search snapshot: {field}")
    summary = report.get("summary")
    if not isinstance(summary, dict):
        raise EvidenceError("Fidelity report is missing summary")
    statuses = summary.get("statuses")
    if not isinstance(statuses, dict):
        raise EvidenceError("Fidelity report is missing status counts")
    sources = report.get("sources")
    if not isinstance(sources, list):
        raise EvidenceError("Fidelity report is missing source-level evidence required for 100% coverage")
    source_count = int(summary.get("source_count", 0) or 0)
    if source_count <= 0 or report.get("expected_source_count") != source_count or report.get("processed_source_count") != source_count:
        raise EvidenceError("Fidelity report source completion counts are incomplete")
    if expected_source_count is not None and source_count != expected_source_count:
        raise EvidenceError("Fidelity report does not cover the complete canonical source set")
    report_source_identity_digest = str(report.get("source_identity_digest") or "").strip()
    if not report_source_identity_digest:
        raise EvidenceError("Fidelity report is missing source identity digest")
    if not expected_source_identity_digest:
        raise EvidenceError("Artifact manifest is missing source identity digest")
    if report_source_identity_digest != expected_source_identity_digest:
        raise EvidenceError("Fidelity report source identity digest does not match the artifact")
    if source_count != len(sources):
        raise EvidenceError("Fidelity source count does not match source-level evidence")
    source_keys = [
        (str(source.get("source_type") or ""), str(source.get("category") or ""), str(source.get("sourcefile") or ""))
        for source in sources
        if isinstance(source, dict)
    ]
    if any(not all(key_value for key_value in source_key) for source_key in source_keys):
        raise EvidenceError("Fidelity source-level evidence contains an incomplete source identity")
    if len(source_keys) != len(sources) or len(set(source_keys)) != len(source_keys):
        raise EvidenceError("Fidelity source-level evidence is not a unique one-to-one reconciliation")
    if int(statuses.get("PASS", 0) or 0) != sum(source.get("status") == "PASS" for source in sources):
        raise EvidenceError("Fidelity status counts do not match source-level evidence")
    pass_count = sum(source.get("status") == "PASS" for source in sources)
    coverage = pass_count / source_count if source_count else 0.0
    unmatched = 0
    ambiguous = 0
    substantive_block_count = 0
    remediation_counts: dict[str, int] = {}
    for source in sources:
        if not isinstance(source, dict):
            raise EvidenceError("Fidelity source evidence must be an object")
        if source.get("status") not in {"PASS"}:
            raise EvidenceError("Fidelity report contains a non-passing source")
        remediation = source.get("remediation_status")
        if not isinstance(remediation, str) or not remediation:
            raise EvidenceError("Fidelity source is missing remediation disposition")
        remediation_counts[remediation] = remediation_counts.get(remediation, 0) + 1
        blocks = source.get("metrics", {}).get("substantive_blocks", {})
        if not isinstance(blocks, dict):
            raise EvidenceError("Fidelity source is missing substantive block evidence")
        unmatched += int(blocks.get("unmatched_block_count", 0) or 0)
        ambiguous += int(blocks.get("ambiguous_block_count", 0) or 0)
        source_blocks = int(blocks.get("source_block_count", 0) or 0)
        matched_blocks = int(blocks.get("matched_block_count", 0) or 0)
        unmatched_blocks = int(blocks.get("unmatched_block_count", 0) or 0)
        ambiguous_blocks = int(blocks.get("ambiguous_block_count", 0) or 0)
        overlap_blocks = int(blocks.get("cross_document_overlap_count", 0) or 0)
        if source_blocks <= 0 or matched_blocks + unmatched_blocks + ambiguous_blocks + overlap_blocks != source_blocks:
            raise EvidenceError("Fidelity substantive block counts do not reconcile")
        if len(blocks.get("occurrence_ledger", [])) != source_blocks:
            raise EvidenceError("Fidelity occurrence ledger does not match source block count")
        substantive_block_count += source_blocks
    if report.get("remediation") != remediation_counts:
        raise EvidenceError("Fidelity remediation counts do not match source-level evidence")
    if substantive_block_count <= 0:
        raise EvidenceError("Fidelity report contains no substantive block evidence")
    gate = {
        "substantive_coverage": coverage,
        "unmatched": unmatched,
        "ambiguous": ambiguous,
        "unavailable": int(statuses.get("UNAVAILABLE", 0) or 0) + int(statuses.get("MISSING_FROM_INDEX", 0) or 0),
        "unclassified": int(statuses.get("INDEX_ONLY", 0) or 0) + int(statuses.get("UNMAPPED", 0) or 0),
        "substantive_block_count": substantive_block_count,
        "dispositions": remediation_counts,
    }
    if coverage != 1.0 or any(statuses.get(status, 0) for status in ("WARN", "FAIL", "UNAVAILABLE", "MISSING_FROM_INDEX", "INDEX_ONLY", "UNMAPPED")) or any(
        gate[field] for field in ("unmatched", "ambiguous", "unavailable", "unclassified")
    ):
        raise EvidenceError(f"Fidelity gate is not clean or 100% substantive: {gate}")
    return gate


def transition_gate(report: dict[str, Any]) -> dict[str, int]:
    if not isinstance(report, dict):
        raise EvidenceError("HTML transition report must be a JSON object")
    gate = {
        "snapshot_count": int(report.get("snapshot_count", 0) or 0),
        "failed_count": int(report.get("failed_count", 0) or 0),
        "blocked_count": int(report.get("blocked_count", 0) or 0),
    }
    if not gate["snapshot_count"] or gate["failed_count"] or gate["blocked_count"]:
        raise EvidenceError(f"HTML transition gate is not clean: {gate}")
    return gate


def artifact_search_gate(artifact_path: Path, snapshot: dict[str, Any]) -> dict[str, Any]:
    documents_path = artifact_path.parent / "documents_with_embeddings.jsonl"
    if not documents_path.exists():
        raise EvidenceError(f"Artifact documents are missing: {documents_path}")
    artifact_documents = [
        json.loads(line)
        for line in documents_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    snapshot_documents = snapshot.get("documents")
    if not isinstance(snapshot_documents, list):
        raise EvidenceError("Search snapshot has no documents for artifact equality")

    def project(document: dict[str, Any]) -> dict[str, Any]:
        return {field: document.get(field) for field in SEARCH_FIELDS}

    artifact_by_id = {str(document.get("id") or ""): project(document) for document in artifact_documents}
    snapshot_by_id = {str(document.get("id") or ""): project(document) for document in snapshot_documents}
    missing = sorted(set(artifact_by_id) - set(snapshot_by_id))
    extra = sorted(set(snapshot_by_id) - set(artifact_by_id))
    mismatched = sorted(
        document_id
        for document_id in set(artifact_by_id) & set(snapshot_by_id)
        if artifact_by_id[document_id] != snapshot_by_id[document_id]
    )
    result = {
        "artifact_document_count": len(artifact_by_id),
        "search_document_count": len(snapshot_by_id),
        "missing_count": len(missing),
        "extra_count": len(extra),
        "mismatched_count": len(mismatched),
        "missing_ids": missing[:100],
        "extra_ids": extra[:100],
        "mismatched_ids": mismatched[:100],
    }
    if missing or extra or mismatched or len(artifact_by_id) != len(artifact_documents):
        raise EvidenceError(f"Artifact/Search equality gate is not clean: {result}")
    return result


def extraction_manifest_gate(artifact_manifest_path: Path, artifact_manifest: dict[str, Any]) -> dict[str, Any]:
    """Bind packaged court-guide JSON files to their captured source manifest."""
    extraction_path = artifact_manifest_path.parent / "court_guides_extraction_manifest.json"
    if not extraction_path.exists():
        raise EvidenceError(f"Court-guide extraction manifest is missing: {extraction_path}")
    extraction_manifest = _load_object(extraction_path)
    if extraction_manifest.get("schema_version") != 1:
        raise EvidenceError("Court-guide extraction manifest has an unsupported schema")
    expected_hash = str(artifact_manifest.get("court_guides_extraction_manifest_sha256") or "").strip()
    actual_hash = sha256_file(extraction_path)
    if not expected_hash or expected_hash != actual_hash:
        raise EvidenceError("Artifact manifest is not bound to the packaged court-guide extraction manifest")
    guides = extraction_manifest.get("guides")
    if not isinstance(guides, dict) or not guides:
        raise EvidenceError("Court-guide extraction manifest contains no processed guides")
    processed_document_count = 0
    for guide_name, entry in guides.items():
        if not isinstance(entry, dict):
            raise EvidenceError(f"Court-guide extraction entry is invalid: {guide_name}")
        processed_name = str(entry.get("processed_json") or "").strip()
        expected_processed_hash = str(entry.get("processed_json_sha256") or "").strip()
        expected_count = int(entry.get("document_count", 0) or 0)
        processed_path = artifact_manifest_path.parent / processed_name
        if not processed_name or not expected_processed_hash or expected_count <= 0 or not processed_path.exists():
            raise EvidenceError(f"Court-guide extraction entry is incomplete: {guide_name}")
        if sha256_file(processed_path) != expected_processed_hash:
            raise EvidenceError(f"Court-guide processed artifact hash mismatch: {processed_name}")
        try:
            documents = json.loads(processed_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise EvidenceError(f"Court-guide processed artifact is not valid JSON: {processed_name}") from error
        if not isinstance(documents, list) or len(documents) != expected_count:
            raise EvidenceError(f"Court-guide processed document count mismatch: {processed_name}")
        processed_document_count += expected_count
    if int(extraction_manifest.get("processed_guide_count", 0) or 0) != len(guides):
        raise EvidenceError("Court-guide extraction guide count does not reconcile")
    if int(extraction_manifest.get("processed_document_count", 0) or 0) != processed_document_count:
        raise EvidenceError("Court-guide extraction document count does not reconcile")
    return {
        "manifest_path": str(extraction_path),
        "manifest_sha256": actual_hash,
        "guide_count": len(guides),
        "document_count": processed_document_count,
    }


def candidate_validation_gate(report: dict[str, Any]) -> dict[str, Any]:
    candidate = report.get("candidate")
    if not isinstance(candidate, dict) or candidate.get("status") != "PASS":
        raise EvidenceError("Candidate Search validation gate is not clean")
    return candidate


def candidate_validation_matches_snapshot(report: dict[str, Any], snapshot: dict[str, Any]) -> None:
    provenance = report.get("provenance")
    if not isinstance(provenance, dict):
        raise EvidenceError("Candidate validation report is missing provenance")
    expected = {
        key: snapshot.get(key)
        for key in ("schema_version", "service", "index", "captured_at_utc", "selected_fields", "document_count", "documents_sha256")
    }
    mismatched = [field for field, value in expected.items() if provenance.get(field) != value]
    if mismatched:
        raise EvidenceError("Candidate validation provenance does not match the Search snapshot: " + ", ".join(mismatched))


def application_gate_gate(
    report: dict[str, Any],
    candidate_index: str,
    candidate_knowledgebase: str,
    artifact_sha256: str,
    search_snapshot_sha256: str,
    expected_release_id: str | None = None,
    expected_provenance: dict[str, str] | None = None,
) -> dict[str, Any]:
    if report.get("schema_version") != 1 or report.get("status") != "PASS":
        raise EvidenceError("Application-gate report is not a passing version 1 report")
    provenance = report.get("provenance")
    if not isinstance(provenance, dict):
        raise EvidenceError("Application-gate report is missing provenance")
    missing = [field for field in APPLICATION_PROVENANCE_FIELDS if not str(provenance.get(field) or "").strip()]
    if missing:
        raise EvidenceError("Application-gate provenance is missing: " + ", ".join(missing))
    expected = {
        "search_index": candidate_index,
        "knowledge_base": candidate_knowledgebase,
        "artifact_sha256": artifact_sha256,
        "search_snapshot_sha256": search_snapshot_sha256,
    }
    mismatched = [field for field, value in expected.items() if provenance.get(field) != value]
    if mismatched:
        raise EvidenceError("Application-gate provenance mismatch: " + ", ".join(mismatched))
    if expected_release_id is not None and provenance.get("release_id") != expected_release_id:
        raise EvidenceError("Application-gate provenance does not match artifact release_id")
    if expected_provenance is not None:
        mismatched = [
            field
            for field, value in expected_provenance.items()
            if str(provenance.get(field) or "").strip() != str(value).strip()
        ]
        if mismatched:
            raise EvidenceError("Application-gate provenance does not match expected release: " + ", ".join(mismatched))
    gates = report.get("gates")
    if not isinstance(gates, dict) or set(gates) != {"retrieval", "category", "source_hierarchy", "citation", "acl", "highlight"}:
        raise EvidenceError("Application-gate report must contain all required gates")
    if any(not isinstance(gate, dict) or gate.get("status") != "PASS" for gate in gates.values()):
        raise EvidenceError("Application-gate report contains a non-passing gate")
    highlight = gates["highlight"]
    browser_evidence = highlight.get("browser_evidence")
    try:
        validate_browser_evidence(browser_evidence)
    except BrowserGateError as error:
        raise EvidenceError(f"Application-gate highlight is missing live browser evidence: {error}") from error
    return report


def build_bundle(
    artifact_manifest_path: Path,
    search_snapshot_path: Path,
    fidelity_report_path: Path,
    transition_report_path: Path,
    candidate_validation_path: Path,
    candidate_index: str,
    candidate_knowledgebase: str,
    rollback_index: str,
    rollback_knowledgebase: str,
    application_gate_path: Path,
    rollback_application_path: Path,
    highlight_oracle_path: Path | None = None,
    approved: bool = False,
    approval_environment: str = "",
    expected_provenance: dict[str, str] | None = None,
) -> dict[str, Any]:
    evidence_paths = (
        artifact_manifest_path,
        search_snapshot_path,
        fidelity_report_path,
        transition_report_path,
        candidate_validation_path,
        application_gate_path,
        rollback_application_path,
    )
    for path in evidence_paths:
        if not path.exists():
            raise EvidenceError(f"Missing release evidence input: {path}")
    if highlight_oracle_path is not None and not highlight_oracle_path.exists():
        raise EvidenceError(f"Missing highlight oracle evidence: {highlight_oracle_path}")

    manifest = _load_object(artifact_manifest_path)
    artifact_documents_path = artifact_manifest_path.parent / "documents_with_embeddings.jsonl"
    if not artifact_documents_path.exists():
        raise EvidenceError(f"Artifact documents are missing: {artifact_documents_path}")
    snapshot = _load_object(search_snapshot_path)
    report = _load_object(fidelity_report_path)
    transition_report = _load_object(transition_report_path)
    candidate_validation_report = _load_object(candidate_validation_path)
    if manifest.get("embedding_dimensions") != 3072 or manifest.get("embedding_model") != "text-embedding-3-large":
        raise EvidenceError("Artifact embedding metadata is not the approved configuration")
    release_id = str(manifest.get("release_id") or "").strip()
    if not release_id:
        raise EvidenceError("Artifact manifest is missing release_id")
    source_identity_digest = str(manifest.get("source_identity_digest") or "").strip()
    if not source_identity_digest:
        raise EvidenceError("Artifact manifest is missing source identity digest")
    if snapshot.get("documents_sha256") is None:
        raise EvidenceError("Search snapshot is not a verified provenance envelope")
    artifact_source_count = int(manifest.get("source_count", 0) or 0)
    if artifact_source_count <= 0:
        raise EvidenceError("Artifact manifest is missing source_count")
    fidelity = fidelity_gate(
        report,
        expected_snapshot=snapshot,
        expected_source_count=artifact_source_count,
        expected_source_identity_digest=manifest.get("source_identity_digest"),
    )
    extraction = extraction_manifest_gate(artifact_manifest_path, manifest)
    transition = transition_gate(transition_report)
    artifact_search = artifact_search_gate(artifact_manifest_path, snapshot)
    candidate_validation = candidate_validation_gate(candidate_validation_report)
    candidate_validation_matches_snapshot(candidate_validation_report, snapshot)
    application_gate_report = _load_object(application_gate_path)
    rollback_application = _load_object(rollback_application_path)
    rollback_image = str(rollback_application.get("image_digest") or "").strip()
    rollback_revision = str(rollback_application.get("revision_name") or "").strip()
    rollback_release_id = str(rollback_application.get("release_id") or "").strip()
    if "@sha256:" not in rollback_image:
        raise EvidenceError("Rollback application image must be immutable")
    if not rollback_revision:
        raise EvidenceError("Rollback application snapshot is missing revision_name")
    if not rollback_release_id or rollback_release_id == release_id:
        raise EvidenceError("Rollback application snapshot must identify a previous release")
    if rollback_application.get("search_index") != rollback_index:
        raise EvidenceError("Rollback application Search index does not match rollback_index")
    if rollback_application.get("knowledge_base") != rollback_knowledgebase:
        raise EvidenceError("Rollback application knowledge base does not match rollback_knowledgebase")
    application_gates = application_gate_gate(
        application_gate_report,
        candidate_index,
        candidate_knowledgebase,
        sha256_file(artifact_documents_path),
        sha256_file(search_snapshot_path),
        expected_release_id=release_id,
        expected_provenance=expected_provenance,
    )
    manifest_paths = evidence_paths + ((highlight_oracle_path,) if highlight_oracle_path else ())
    manifest_root = _evidence_root(manifest_paths)
    bundle = {
        "schema_version": 1,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "approved": approved,
        "approval_environment": approval_environment,
        "release_id": release_id,
        "candidate_index": candidate_index,
        "candidate_knowledgebase": candidate_knowledgebase,
        "rollback_index": rollback_index,
        "rollback_knowledgebase": rollback_knowledgebase,
        "rollback_application": rollback_application,
        "artifact_path": str(artifact_documents_path),
        "artifact_manifest_path": str(artifact_manifest_path),
        "artifact_sha256": sha256_file(artifact_documents_path),
        "search_snapshot_path": str(search_snapshot_path),
        "search_snapshot_sha256": sha256_file(search_snapshot_path),
        "search_snapshot_documents_sha256": snapshot["documents_sha256"],
        "fidelity_report_path": str(fidelity_report_path),
        "fidelity": fidelity,
        "transition": transition,
        "artifact_search": artifact_search,
        "candidate_validation": candidate_validation,
        "application_gates": application_gates,
        "application_provenance": application_gates["provenance"],
        "highlight_oracle_path": str(highlight_oracle_path) if highlight_oracle_path else "",
        "evidence_manifest": _evidence_manifest(manifest_paths, manifest_root),
        "artifact": {
            "document_count": manifest.get("document_count"),
            "source_count": manifest.get("source_count"),
            "snapshot_count": manifest.get("snapshot_count"),
            "source_snapshot_hashes": manifest.get("source_snapshot_hashes", {}),
            "court_guides_extraction_manifest_sha256": extraction["manifest_sha256"],
        },
    }
    canonical = json.dumps(
        {key: value for key, value in bundle.items() if key not in {"created_at_utc", "approved", "approval_environment"}},
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )
    bundle["evidence_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return bundle


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-manifest", type=Path, required=True)
    parser.add_argument("--search-snapshot", type=Path, required=True)
    parser.add_argument("--fidelity-report", type=Path, required=True)
    parser.add_argument("--transition-report", type=Path, required=True)
    parser.add_argument("--candidate-validation", type=Path, required=True)
    parser.add_argument("--application-gates", type=Path, required=True)
    parser.add_argument("--rollback-application", type=Path, required=True)
    parser.add_argument("--highlight-oracle", type=Path)
    parser.add_argument("--candidate-index", required=True)
    parser.add_argument("--candidate-knowledgebase", required=True)
    parser.add_argument("--rollback-index", default="legal-court-rag-index-v3")
    parser.add_argument("--rollback-knowledgebase", default="legal-court-rag-index-v3-agent-upgrade")
    parser.add_argument("--approved", action="store_true")
    parser.add_argument("--approval-environment", default="")
    for field in APPLICATION_PROVENANCE_FIELDS:
        parser.add_argument(f"--expected-{field.replace('_', '-')}")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    bundle = build_bundle(
        args.artifact_manifest,
        args.search_snapshot,
        args.fidelity_report,
        args.transition_report,
        args.candidate_validation,
        args.candidate_index,
        args.candidate_knowledgebase,
        args.rollback_index,
        args.rollback_knowledgebase,
        application_gate_path=args.application_gates,
        rollback_application_path=args.rollback_application,
        highlight_oracle_path=args.highlight_oracle,
        approved=args.approved,
        approval_environment=args.approval_environment,
        expected_provenance={
            field: getattr(args, f"expected_{field}")
            for field in APPLICATION_PROVENANCE_FIELDS
            if getattr(args, f"expected_{field}") is not None
        },
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "artifact_sha256": bundle["artifact_sha256"], "search_snapshot_sha256": bundle["search_snapshot_sha256"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
