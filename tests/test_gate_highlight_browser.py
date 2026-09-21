import pytest

from scripts.gate_highlight_browser import (
    BrowserGateError,
    choose_case,
    normalize,
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


def test_choose_case_prefers_cpr_part_24_subsection_24_2():
    preferred = {"case_id": "preferred", "subsection_id": "24.2", "sourcepage": "CPR Part 24", "body_text": "long"}
    fallback = {"case_id": "fallback", "subsection_id": "1", "sourcepage": "Other", "body_text": "short"}

    assert choose_case({"cases": [fallback, preferred]}) is preferred
    assert choose_case({"cases": [fallback]}) is fallback


def test_choose_case_rejects_empty_oracle_and_normalizes_text():
    with pytest.raises(BrowserGateError, match="no browser-checkable"):
        choose_case({"cases": ["invalid"]})
    assert normalize("  CPR\n Part 24  ") == "cpr part 24"
