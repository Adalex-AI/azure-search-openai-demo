from pathlib import Path


WORKFLOW = Path(".github/workflows/update-index-v4.yml")


def test_html_oracle_capture_retries_transient_failures_eight_times():
    workflow = WORKFLOW.read_text()

    capture = workflow[workflow.index("- name: Recapture canonical HTML oracle") :]
    capture = capture[:capture.index("- name: Recapture canonical PDF oracle")]
    assert "--retries 8" in capture