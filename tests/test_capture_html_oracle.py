from pathlib import Path

from scripts.capture_html_oracle import capture_source, snapshot_filename


class Source:
    identity = "civil procedure rules and practice directions::Part 1"
    source_type = "html"
    sourcefile = "Part 1"
    category = "Civil Procedure Rules and Practice Directions"
    manifest_key = "part-1"
    url = "https://example.test/part-1"


def test_snapshot_filename_is_stable_and_safe():
    assert snapshot_filename(Source.identity) == snapshot_filename(Source.identity)
    assert Path(snapshot_filename(Source.identity)).suffix == ".json"


def test_capture_source_persists_manifest_metadata_and_skips_existing(tmp_path):
    class Response:
        content = b"<main><h1>Part 1</h1><p>Rule text.</p></main>"
        encoding = "utf-8"
        url = "https://example.test/part-1"
        status_code = 200
        headers = {"Content-Type": "text/html"}
        history = []

        def raise_for_status(self):
            return None

    class Session:
        def get(self, url, *, timeout, allow_redirects):
            assert url == Source.url
            return Response()

    first = capture_source(Session(), Source(), tmp_path, 10)
    second = capture_source(Session(), Source(), tmp_path, 10)
    payload = (tmp_path / snapshot_filename(Source.identity)).read_text(encoding="utf-8")

    assert first["status"] == "ok"
    assert second["status"] == "skipped"
    assert '"identity": "civil procedure rules and practice directions::Part 1"' in payload
    assert '"status": "ok"' in payload


def test_capture_source_writes_explicit_failure_record(tmp_path):
    class Session:
        def get(self, url, *, timeout, allow_redirects):
            raise TimeoutError("request timed out")

    result = capture_source(Session(), Source(), tmp_path, 10)
    payload = (tmp_path / snapshot_filename(Source.identity)).read_text(encoding="utf-8")

    assert result["status"] == "unavailable"
    assert '"error_type": "TimeoutError"' in payload


def test_capture_source_resolves_manifest_discovery_sentinel(tmp_path, monkeypatch):
    source = Source()
    source.url = "DISCOVER_FROM_PROTOCOL_PAGE"

    class Response:
        content = b'<a href="debt-claims">Debt Claims Pre-Action Protocol</a>'

        def raise_for_status(self):
            return None

    class Session:
        def get(self, url, *, timeout, allow_redirects):
            assert url == "https://www.justice.gov.uk/courts/procedure-rules/civil/protocol"
            return Response()

    monkeypatch.setattr(
        "scripts.capture_html_oracle.capture_html_snapshot",
        lambda session, url, timeout: {"content": "Debt Claims"},
    )

    result = capture_source(Session(), source, tmp_path, 10)
    payload = (tmp_path / snapshot_filename(Source.identity)).read_text(encoding="utf-8")

    assert result["status"] == "ok"
    assert '"resolved_url": "https://www.justice.gov.uk/courts/procedure-rules/civil/debt-claims"' in payload