from bs4 import BeautifulSoup

from scripts import update_cpr_index_v3 as updater


def test_scrape_page_preserves_long_and_lower_level_headings(monkeypatch):
    html = """
    <main>
      <h1>Practice Direction 44</h1>
      <h2>Section II - Additional provisions for applications for permission to apply for judicial review in immigration and asylum cases</h2>
      <h5>2.8</h5>
      <p>Deal with this application according to the applicable rules.</p>
      <h6>This practice direction supplements CPR rule 70.7</h6>
    </main>
    """
    monkeypatch.setattr(updater, "fetch_soup", lambda session, url: BeautifulSoup(html, "html.parser"))

    result = updater.scrape_page(updater.requests.Session(), "https://example.test/practice-direction")

    assert result is not None
    assert "## Section II - Additional provisions" in result["content"]
    assert "## 2.8" in result["content"]
    assert "## This practice direction supplements CPR rule 70.7" in result["content"]


def test_scrape_page_preserves_nested_list_lead_in(monkeypatch):
    html = """
    <main>
      <h1>Practice Direction 57AD</h1>
      <ol>
        <li>The Less Complex Claims Disclosure Review Document (<strong>LCCDRD</strong>) is intended to:
          <ol>
            <li>facilitate the exchange of information.</li>
          </ol>
        </li>
      </ol>
    </main>
    """
    monkeypatch.setattr(updater, "fetch_soup", lambda session, url: BeautifulSoup(html, "html.parser"))

    result = updater.scrape_page(updater.requests.Session(), "https://example.test/practice-direction")

    assert result is not None
    assert "The Less Complex Claims Disclosure Review Document ( LCCDRD ) is intended to:" in result["content"]
    assert "facilitate the exchange of information." in result["content"]