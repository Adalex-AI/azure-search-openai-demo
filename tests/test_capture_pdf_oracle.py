from types import SimpleNamespace

from scripts import capture_pdf_oracle
from scripts.html_schema_oracle import ORACLE_VERSION


def test_capture_pdf_snapshot_uses_canonical_oracle_version(monkeypatch):
    class Response:
        content = b"%PDF-1.7"
        url = "https://example.test/source.pdf"
        status_code = 200
        headers = {"Content-Type": "application/pdf"}
        history = []

        def raise_for_status(self):
            return None

    class Session:
        def get(self, url, *, timeout, allow_redirects):
            assert url == "https://example.test/source.pdf"
            assert timeout == 30
            assert allow_redirects is True
            return Response()

    monkeypatch.setattr(
        capture_pdf_oracle.pypdf,
        "PdfReader",
        lambda _: SimpleNamespace(pages=[SimpleNamespace(extract_text=lambda: "x" * 200)]),
    )
    source = SimpleNamespace(
        identity="source-1",
        source_type="pdf",
        sourcefile="source.pdf",
        category="Civil Procedure Rules and Practice Directions",
        manifest_key="source-1",
        url="https://example.test/source.pdf",
    )

    snapshot = capture_pdf_oracle.capture_pdf_snapshot(Session(), source)

    assert snapshot["oracle_version"] == ORACLE_VERSION