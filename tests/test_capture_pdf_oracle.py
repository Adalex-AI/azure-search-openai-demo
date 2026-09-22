from scripts import capture_pdf_oracle


class Source:
    identity = "civil procedure rules and practice directions::pre-action protocol for debt claims"
    source_type = "html"
    sourcefile = "Pre-Action Protocol for Debt Claims"
    category = "Civil Procedure Rules and Practice Directions"
    manifest_key = "Pre-Action Protocol for Debt Claims"
    url = "DISCOVER_FROM_PROTOCOL_PAGE"


def test_run_captures_sentinel_source_after_resolving_its_pdf_url(tmp_path, monkeypatch):
    resolved_url = "https://example.test/debt-claims.pdf"
    monkeypatch.setattr(capture_pdf_oracle, "load_web_sources", lambda: [Source()])
    monkeypatch.setattr(capture_pdf_oracle, "resolve_protocol_page_url", lambda session, url, timeout: resolved_url)
    monkeypatch.setattr(
        capture_pdf_oracle,
        "capture_pdf_snapshot",
        lambda session, source, url, timeout: {"identity": source.identity, "requested_url": source.url, "resolved_url": url},
    )

    result = capture_pdf_oracle.run(tmp_path, None, 10)

    assert result["source_count"] == 1
    assert result["ok_count"] == 1
    assert result["results"][0]["identity"] == Source.identity