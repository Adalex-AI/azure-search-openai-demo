import pytest
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from scripts.gate_highlight_browser import (
    CITATION_DISCOVERY_TIMEOUT_MS,
    BrowserGateError,
    choose_case,
    normalize,
    question_for_case,
    validate_browser_evidence,
)


def evidence():
    return {
        "browser": {
            "supporting_content_visible": True,
            "highlight_visible": True,
            "citation_path_present": True,
        },
        "case_id": "case-24.2",
        "subsection_id": "24.2",
    }


def test_validate_browser_evidence_requires_all_live_signals():
    assert validate_browser_evidence(evidence()) == evidence()

    for field in ("supporting_content_visible", "highlight_visible", "citation_path_present"):
        incomplete = evidence()
        incomplete["browser"][field] = False
        with pytest.raises(BrowserGateError, match=field):
            validate_browser_evidence(incomplete)


@pytest.mark.parametrize("payload", [None, {}, {"browser": {}}, {"browser": evidence()["browser"]}])
def test_validate_browser_evidence_rejects_incomplete_shapes(payload):
    with pytest.raises(BrowserGateError, match="shape"):
        validate_browser_evidence(payload)


def test_choose_case_prefers_cpr_part_24_sourcefile():
    preferred = {
        "case_id": "preferred",
        "sourcefile": "Part 24",
        "subsection_id": "PART 24",
        "body_text": "longer canonical body",
    }
    fallback = {"case_id": "fallback", "subsection_id": "1", "sourcepage": "Other", "body_text": "short"}

    assert choose_case({"cases": [fallback, preferred]}) is preferred
    assert choose_case({"cases": [fallback]}) is fallback


def test_choose_case_rejects_empty_oracle_and_normalizes_text():
    with pytest.raises(BrowserGateError, match="no browser-checkable"):
        choose_case({"cases": ["invalid"]})
    assert normalize("  CPR\n Part 24  ") == "cpr part 24"


def test_question_for_case_targets_the_selected_canonical_document_and_subsection():
    case = {
        "sourcefile": "Devolution Issues and Crown Office Applications in Wales (Welsh)",
        "subsection_id": "7.6",
        "body_text": "7.6 The court may set a longer date in exceptional circumstances.",
    }

    assert question_for_case(case) == (
        "In Devolution Issues and Crown Office Applications in Wales (Welsh), what does section 7.6 say about: "
        "7.6 the court may set a longer date in exceptional circumstances?"
    )


@pytest.mark.parametrize(
    "case",
    [{}, {"sourcefile": "Part 24"}, {"subsection_id": "24.2"}, {"body_text": "A rule"}],
)
def test_question_for_case_rejects_incomplete_case(case):
    with pytest.raises(BrowserGateError, match="cannot produce"):
        question_for_case(case)


def test_citation_discovery_timeout_leaves_time_to_write_failure_evidence():
    assert CITATION_DISCOVERY_TIMEOUT_MS == 60_000


def test_citation_discovery_uses_the_bounded_timeout(monkeypatch):
    from scripts import gate_highlight_browser

    timeouts = []
    clicked = []

    class Locator:
        first = None

        def __init__(self, fail=False, visible=True):
            self.fail = fail
            self.visible = visible
            self.first = self

        def wait_for(self, **kwargs):
            if self.fail:
                timeouts.append(kwargs["timeout"])
                raise PlaywrightTimeoutError("citation did not render")
            if not self.visible:
                raise PlaywrightTimeoutError("splash is not displayed")
            return None

        def fill(self, value):
            return None

        def click(self):
            clicked.append(self)
            return None

    class Page:
        def goto(self, *args, **kwargs):
            return None

        def locator(self, selector):
            if selector.startswith(".supContainer"):
                return Locator(fail=True)
            return Locator(visible=False)

        def get_by_placeholder(self, *args, **kwargs):
            return Locator()

        def get_by_role(self, *args, **kwargs):
            return Locator()

        def get_by_text(self, *args, **kwargs):
            return Locator()

    class Browser:
        def new_page(self):
            return Page()

        def close(self):
            return None

    class Playwright:
        chromium = type("Chromium", (), {"launch": staticmethod(lambda **kwargs: Browser())})()

    class PlaywrightContext:
        def __enter__(self):
            return Playwright()

        def __exit__(self, *args):
            return None

    monkeypatch.setattr(gate_highlight_browser, "sync_playwright", PlaywrightContext)

    with pytest.raises(PlaywrightTimeoutError, match="citation did not render"):
        gate_highlight_browser.run_browser_gate(
            "https://candidate.example.test",
            {
                "cases": [
                    {
                        "case_id": "case-24.2",
                        "subsection_id": "24.2",
                        "sourcepage": "CPR Part 24",
                        "body_text": "test",
                        "expected_heading": "24.2",
                    }
                ]
            },
            "What is CPR Part 24 rule 24.2?",
        )

    assert timeouts == [CITATION_DISCOVERY_TIMEOUT_MS]
    assert len(clicked) == 2
