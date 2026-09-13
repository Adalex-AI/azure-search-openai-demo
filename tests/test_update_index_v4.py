import hashlib
import json
import sys
from pathlib import Path

import pytest

from scripts.court_guides_processing_pipeline.scripts import (
    extract_court_guides_azure_di as extractor,
)

WORKFLOW = Path(".github/workflows/update-index-v4.yml")
AZD_WORKFLOW = Path(".github/workflows/azure-dev.yml")
MAIN_BICEP = Path("infra/main.bicep")
MAIN_PARAMETERS = Path("infra/main.parameters.json")


def test_v4_workflow_verifies_document_intelligence_before_extraction():
    workflow = WORKFLOW.read_text()

    assert '[[ "${V4_RELEASE_ID}" =~ ^[a-z0-9][a-z0-9-]{0,40}$ ]]' in workflow
    assert workflow.index("Verify Document Intelligence access before extraction") < workflow.index(
        "Capture and extract canonical court guides"
    )
    assert "roleDefinitionName == 'Cognitive Services User'" in workflow
    assert '--scope "${document_intelligence_id}"' in workflow
    assert '--assignee "${AZURE_RELEASE_PIPELINE_PRINCIPAL_ID}"' in workflow
    assert 'az ad sp show --id "${AZURE_CLIENT_ID}" --query id -o tsv' in workflow
    assert '"${active_principal_id}" == "${AZURE_RELEASE_PIPELINE_PRINCIPAL_ID}"' in workflow
    assert 'echo "AZURE_DOCUMENTINTELLIGENCE_ENDPOINT=${document_intelligence_endpoint}" >> "${GITHUB_ENV}"' in workflow


def test_release_pipeline_rbac_uses_a_service_principal_object_id():
    bicep = MAIN_BICEP.read_text()
    parameters = MAIN_PARAMETERS.read_text()

    assert "param releasePipelinePrincipalId string = ''" in bicep
    assert "principalId: releasePipelinePrincipalId" in bicep
    assert "roleDefinitionId: 'a97b65f3-24c7-4388-baec-2e87135dc908'" in bicep
    assert '"releasePipelinePrincipalId"' in parameters
    assert "AZURE_RELEASE_PIPELINE_PRINCIPAL_ID" in parameters


def test_promotion_is_bound_to_the_workflow_release_id():
    workflow = WORKFLOW.read_text()

    assert (
        'python scripts/promote_v4_candidate.py \\\n            --evidence reports/v4_evidence.json \\\n            --release-id "${V4_RELEASE_ID}"'
        in workflow
    )


def test_candidate_gate_verifies_immutable_serving_image_identity():
    workflow = WORKFLOW.read_text()

    assert "V4_CANDIDATE_IMAGE_DIGEST:?Build job did not produce an immutable image reference" in workflow
    assert "az acr build" in workflow
    assert "image_digest: ${{ steps.image.outputs.image_digest }}" in workflow
    assert "V4_CANDIDATE_IMAGE_DIGEST: ${{ needs.build-candidate.outputs.image_digest }}" in workflow
    assert "vars.V4_CANDIDATE_IMAGE_DIGEST" not in workflow
    assert '--image "${V4_CANDIDATE_IMAGE_DIGEST}"' in workflow
    assert '--image-digest "${V4_CANDIDATE_IMAGE_DIGEST}"' in workflow
    assert 'properties.get("template", {}).get("containers"' in workflow
    assert "candidate image mismatch" in workflow
    assert "candidate image is not bound to workflow commit" in workflow
    assert "EXPECTED_GIT_SHA: ${{ github.sha }}" in workflow
    assert '              GIT_SHA="${GITHUB_SHA}" \\\n' in workflow
    assert "V4_REVISION_NAME" in workflow
    assert 'payload["image_digest"] == os.environ["V4_CANDIDATE_IMAGE_DIGEST"]' in workflow
    assert "expected_image_digest=expected" in workflow
    assert "expected_revision_name=revision" in workflow
    assert '--revision-name "${V4_REVISION_NAME}"' in workflow


def test_candidate_workflow_binds_required_environment_and_uploads_transition_audit():
    workflow = WORKFLOW.read_text()

    assert "V4_CANDIDATE_IMAGE_DIGEST: ${{ needs.build-candidate.outputs.image_digest }}" in workflow
    assert "EXPECTED_RELEASE_ID: ${{ inputs.release_id || github.run_number }}" in workflow
    assert "            reports/html_transition_audit.json" in workflow


def test_html_oracle_failure_preserves_diagnostics_for_always_upload():
    workflow = WORKFLOW.read_text()

    capture = workflow[workflow.index("- name: Recapture canonical HTML oracle") :]
    capture = capture[: capture.index("- name: Recapture canonical PDF oracle")]
    assert "rm -rf reports/html_oracle_snapshots" in capture
    assert "mkdir -p reports/html_oracle_snapshots" in capture
    assert "name: Summarize HTML oracle diagnostics" in capture
    assert "if: always()" in capture
    assert '"${GITHUB_STEP_SUMMARY}"' in capture
    assert "name: Upload HTML oracle diagnostics" in capture
    assert "if-no-files-found: warn" in capture


def test_candidate_image_build_includes_frontend_assets():
    workflow = WORKFLOW.read_text()

    frontend_build = workflow[workflow.index("- name: Build frontend assets for immutable image") :]
    image_build = frontend_build[frontend_build.index("- name: Build immutable application image") :]
    assert "actions/setup-node@v4" in workflow
    assert "cache-dependency-path: app/frontend/package-lock.json" in workflow
    assert "working-directory: app/frontend" in frontend_build
    assert "run: npm ci && npm run build" in frontend_build
    assert frontend_build.index("run: npm ci && npm run build") < image_build.index("az acr build")


def test_candidate_provenance_poll_binds_all_release_fields():
    workflow = WORKFLOW.read_text()

    for field in (
        '"release_id": os.environ["V4_RELEASE_ID"]',
        '"git_sha": os.environ["GITHUB_SHA"]',
        '"deployment_id": os.environ["GITHUB_RUN_ID"]',
        '"artifact_sha256": os.environ["ARTIFACT_SHA256"]',
        '"search_snapshot_sha256": os.environ["snapshot_sha256"]',
        '"search_service": os.environ["AZURE_SEARCH_SERVICE"]',
        '"search_index": os.environ["SEARCH_INDEX"]',
        '"knowledge_base": os.environ["SEARCH_KNOWLEDGEBASE"]',
        '"image_digest": os.environ["V4_CANDIDATE_IMAGE_DIGEST"]',
        '"revision_name": os.environ["V4_REVISION_NAME"]',
    ):
        assert field in workflow


def test_production_evidence_rebuild_reconstructs_cross_job_provenance():
    workflow = WORKFLOW.read_text()

    assert (
        'artifact_documents="reports/index_v4_artifacts_${V4_RELEASE_ID}/documents_with_embeddings.jsonl"' in workflow
    )
    assert 'ARTIFACT_SHA256:=$(sha256sum "${artifact_documents}"' in workflow
    assert "snapshot_sha256:=$(sha256sum reports/v4_search_snapshot.json" in workflow
    assert "reports/candidate_provenance.json" in workflow
    assert "V4_CANDIDATE_IMAGE_DIGEST:=$(python -c" in workflow
    assert "V4_REVISION_NAME:=$(python -c" in workflow
    assert "name: Rebuild evidence with Production approval" in workflow
    assert (
        workflow.index(
            "AZURE_SEARCH_SERVICE: ${{ secrets.AZURE_SEARCH_SERVICE }}",
            workflow.index("name: Rebuild evidence with Production approval"),
        )
        > 0
    )
    assert "reports/index_v4_artifacts_${{ inputs.release_id || github.run_number }}/*_processed.json" in workflow


def test_production_promotion_validates_live_container_app_identity():
    workflow = WORKFLOW.read_text()

    assert "name: Validate promoted production identity" in workflow
    assert "az containerapp show" in workflow
    assert "az webapp config appsettings list" in workflow
    assert "az webapp config container show" in workflow
    assert "--query dockerCustomImageName --output tsv" in workflow
    assert "Active App Service container image mismatch" in workflow
    assert "platform_args=(--platform appservice)" in workflow
    assert "AZURE_DEPLOYMENT_TARGET: ${{ vars.AZURE_DEPLOYMENT_TARGET }}" in workflow
    assert "python scripts/validate_v4_active_release.py" in workflow
    assert '--expected-image-digest "${PROMOTION_IMAGE_DIGEST}"' in workflow
    assert "EXPECTED_DIGEST: ${{ needs.build-candidate.outputs.image_digest }}" in workflow
    promotion_validation = workflow[workflow.index("name: Validate promoted production identity") :]
    assert '--expected-revision-name "${PROMOTION_REVISION_NAME}"' not in promotion_validation
    assert 'properties.get("latestRevisionName", "")' not in promotion_validation


def test_scheduled_promotion_is_explicitly_opt_in():
    workflow = WORKFLOW.read_text()

    assert "github.event_name == 'schedule' && vars.V4_AUTO_PROMOTE == 'true'" in workflow
    assert "inputs.rollback != true" in workflow


def test_workflow_has_manually_gated_rollback_and_post_rollback_validation():
    workflow = WORKFLOW.read_text()
    rollback_workflow = workflow[workflow.index("\n  rollback:\n") + 1 :]

    assert "rollback:" in workflow
    assert "if: inputs.rollback == true && inputs.promote != true" in workflow
    assert "environment: Production" in workflow
    assert "--execute" in workflow
    assert "--confirm-rollback ROLLBACK-PREVIOUS" in workflow
    assert "scripts/validate_rollback_active_release.py" in workflow
    assert "Restored App Service container image mismatch" in workflow
    assert "v4-rollback-${{ inputs.release_id || github.run_number }}" in workflow
    assert "needs:" not in rollback_workflow.split("    if:", 1)[0]
    assert "name: ${{ vars.V4_ROLLBACK_EVIDENCE_ARTIFACT }}" in rollback_workflow
    assert "name: Validate historical rollback evidence" in rollback_workflow
    assert "V4_ROLLBACK_EVIDENCE_ARTIFACT:?Set the Production repository variable" in rollback_workflow
    assert "Configured rollback artifact did not contain ${evidence_path}" in rollback_workflow
    assert "Rollback evidence must identify a previous release" in rollback_workflow
    assert 'historical_release_id}" != "${V4_RELEASE_ID}' in rollback_workflow
    assert "actions: read" in workflow
    for job in ("preflight", "build-candidate", "provision-and-upload", "deploy-candidate-app", "audit-candidate"):
        assert f"  {job}:\n    if: inputs.rollback != true" in workflow
    assert "V4_ROLLBACK_RUN_ID" in rollback_workflow
    assert "github-token: ${{ github.token }}" in rollback_workflow
    assert "repository: ${{ github.repository }}" in rollback_workflow
    assert "run-id: ${{ vars.V4_ROLLBACK_RUN_ID }}" in rollback_workflow
    assert "V4_ROLLBACK_RUN_ID must be a numeric historical workflow run ID" in rollback_workflow
    download_step = rollback_workflow[rollback_workflow.index("      - uses: actions/download-artifact@v4") :]
    download_step = download_step[: download_step.index("      - uses: actions/setup-python@v5")]
    assert "name: v4-evidence-${{ inputs.release_id || github.run_number }}" not in download_step


def test_workflow_serializes_production_actions_and_rejects_conflicting_inputs():
    workflow = WORKFLOW.read_text()

    assert "group: update-index-v4-production" in workflow
    assert "cancel-in-progress: false" in workflow
    assert "Promotion and rollback cannot be requested together" in workflow
    assert (
        "if: inputs.rollback != true && (inputs.promote == true || (github.event_name == 'schedule' && vars.V4_AUTO_PROMOTE == 'true'))"
        in workflow
    )


def test_promotion_persists_approved_evidence_and_enables_agentic_mode():
    workflow = WORKFLOW.read_text()

    promotion = workflow[workflow.index("  promote:\n") : workflow.index("\n  rollback:\n")]
    assert "name: Persist approved release evidence" in promotion
    assert "name: v4-approved-evidence-${{ inputs.release_id || github.run_number }}" in promotion
    assert 'V4_AGENTIC_MODE="${V4_AGENTIC_MODE}"' in promotion
    assert "USE_AGENTIC_KNOWLEDGEBASE=true" in promotion
    assert "USE_AGENTIC_RETRIEVAL=true" in promotion


def test_ordinary_azd_workflow_cannot_bypass_v4_release_gates():
    workflow = AZD_WORKFLOW.read_text()

    assert "if: ${{ false }}" in workflow
    assert "azd provision" not in workflow
    assert "azd deploy" not in workflow


def test_workflow_uses_fail_closed_canonical_capture():
    workflow = WORKFLOW.read_text()

    assert "--capture-canonical" in workflow
    assert "court_guides_extraction_manifest.json" in workflow
    assert "Validate canonical extraction manifest" in workflow
    assert "actual != expected" in workflow
    assert "invalid SHA-256" in workflow


def test_unknown_guide_metadata_is_rejected(tmp_path):
    unknown_pdf = tmp_path / "unregistered-guide.pdf"
    unknown_pdf.write_bytes(b"%PDF-1.7")

    with pytest.raises(ValueError, match="No registered metadata"):
        extractor.process_pdf(str(unknown_pdf), str(tmp_path))


def test_empty_source_directory_fails_closed(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "argv", ["extractor", "--sources-dir", str(tmp_path)])

    with pytest.raises(SystemExit, match="No PDF sources found"):
        extractor.main()


def test_canonical_capture_writes_source_hash_manifest(monkeypatch, tmp_path):
    content = b"%PDF-1.7\ncanonical source"

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        def read(self):
            return content

    monkeypatch.setattr(extractor, "urlopen", lambda request, timeout: Response())
    manifest = extractor.capture_canonical_sources(tmp_path / "sources", tmp_path / "manifest.json")

    assert manifest["source_count"] == len(extractor.GUIDE_METADATA)
    assert all(
        source["sha256"] == "0b78606e581f1f3ed040db6748d38c1ea3d29d67748b9004fe8a3948f13f2c60"
        for source in manifest["sources"]
    )
    assert (tmp_path / "manifest.json").exists()


def test_canonical_capture_rejects_non_pdf_response(monkeypatch, tmp_path):
    class Response:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        def read(self):
            return b"<html>not a PDF</html>"

    monkeypatch.setattr(extractor, "urlopen", lambda request, timeout: Response())

    with pytest.raises(ValueError, match="Canonical source is not a PDF"):
        extractor.capture_canonical_sources(tmp_path / "sources", tmp_path / "manifest.json")


def test_processed_guide_manifest_records_artifact_hash(monkeypatch, tmp_path):
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "sources": [
                    {
                        "filename": "guide.pdf",
                        "sourcefile": "Guide",
                        "storageUrl": "https://example.test/guide.pdf",
                        "sha256": "source-hash",
                    }
                ],
            }
        )
    )
    artifact = tmp_path / "guide_processed.json"
    artifact.write_text("[]")

    manifest = extractor.update_extraction_manifest(manifest_path, "guide.pdf", 0)

    assert manifest["guides"]["Guide"]["processed_json"] == "guide_processed.json"
    assert manifest["guides"]["Guide"]["processed_json_sha256"] == hashlib.sha256(b"[]").hexdigest()
    assert manifest["guides"]["Guide"]["document_count"] == 0
