from pathlib import Path
from types import SimpleNamespace

import requests
import pytest
from azure.core.exceptions import HttpResponseError

from scripts import capture_html_oracle
from scripts import create_v4_staging_index


WORKFLOW = Path(".github/workflows/update-index-v4.yml")


def test_staging_index_collision_fails_without_reuse(monkeypatch):
    class FakeSearchIndexClient:
        def __init__(self, **kwargs):
            self.get_index_called = False

        def create_index(self, index):
            raise HttpResponseError(message="(ResourceNameAlreadyInUse) index already exists")

        def get_index(self, index_name):
            self.get_index_called = True
            raise AssertionError("existing staging indexes must never be reused")

    client = FakeSearchIndexClient()
    monkeypatch.setattr(create_v4_staging_index, "build_index", lambda _: object())
    monkeypatch.setattr(create_v4_staging_index, "validate_index_schema", lambda _: None)
    monkeypatch.setattr(
        "azure.search.documents.indexes.SearchIndexClient",
        lambda **kwargs: client,
    )

    with pytest.raises(RuntimeError, match="choose a fresh release_id"):
        create_v4_staging_index.provision("legal-court-rag-v4-staging-release-1", "search")

    assert not client.get_index_called


def test_html_oracle_capture_retries_transient_failures_eight_times():
    workflow = WORKFLOW.read_text()

    capture = workflow[workflow.index("- name: Recapture canonical HTML oracle") :]
    capture = capture[:capture.index("- name: Recapture canonical PDF oracle")]
    assert "--retries 8" in capture


def test_candidate_revision_updates_preserve_explicit_image():
    workflow = WORKFLOW.read_text()

    deployment_step = workflow[
        workflow.index("- name: Configure dedicated candidate app revision") :
        workflow.index("- name: Provision paired staging knowledge base")
    ]
    audit_step = workflow[
        workflow.index("- name: Bind candidate revision to Search snapshot") :
        workflow.index("- name: Wait for candidate provenance readiness")
    ]

    for update in (deployment_step, audit_step):
        assert 'candidate_image=$(az containerapp show' in update
        assert '--image "${candidate_image}"' in update


def test_html_oracle_retries_transient_timeout(monkeypatch, tmp_path):
    source = SimpleNamespace(
        identity="Example source",
        source_type="html",
        sourcefile="Example",
        category="Guide",
        manifest_key="example",
        url="https://example.test/source",
    )
    attempts = 0

    def capture(session, url, timeout):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise requests.Timeout("temporary timeout")
        return {"url": url}

    monkeypatch.setattr(capture_html_oracle, "capture_html_snapshot", capture)
    monkeypatch.setattr(capture_html_oracle.time, "sleep", lambda _: None)

    result = capture_html_oracle.capture_source(
        requests.Session(), source, tmp_path, timeout=1, retries=8, retry_delay=0
    )

    assert attempts == 2
    assert result["status"] == "ok"