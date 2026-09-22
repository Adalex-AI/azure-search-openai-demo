from pathlib import Path
from types import SimpleNamespace

import requests

from scripts import capture_html_oracle


WORKFLOW = Path(".github/workflows/update-index-v4.yml")


def test_html_oracle_capture_retries_transient_failures_eight_times():
    workflow = WORKFLOW.read_text()

    capture = workflow[workflow.index("- name: Recapture canonical HTML oracle") :]
    capture = capture[:capture.index("- name: Recapture canonical PDF oracle")]
    assert "--retries 8" in capture


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