from types import SimpleNamespace

from scripts.audit_html_transition import audit_snapshot


def test_audit_snapshot_uses_saved_oracle_html_with_current_scraper_signature():
    source = SimpleNamespace(identity="civil::Part 1", sourcefile="Part 1")
    action = {"sourcefile": "Part 1", "url": "https://example.test/part-1"}
    snapshot = {
        "status": "ok",
        "final_url": action["url"],
        "redirect_count": 0,
        "html": "<main><h1>Part 1 Overriding Objective</h1><p>Deal with cases justly.</p></main>",
    }

    result = audit_snapshot(snapshot, source, action)

    assert result["status"] == "PASS"
    assert result["chunk_count"] == 1