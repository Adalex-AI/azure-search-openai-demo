#!/usr/bin/env python3
"""
Comprehensive Legal Search Quality Evaluation

This evaluation script detects multiple types of search issues that affect
source retrieval quality, including:

1. **Terminology Mismatches** - Colloquial vs official CPR wording
2. **Spelling Errors/Typos** - Common misspellings of legal terms
3. **Abbreviation Handling** - CPR, C.P.R., PD, etc.
4. **British/American Spelling** - defence/defense, judgement/judgment
5. **Hyphenation Variations** - pre-action vs preaction vs pre action
6. **Case Sensitivity** - cpr vs CPR
7. **Word Order Variations** - "costs security" vs "security for costs"
8. **Partial Term Matching** - "disclosure" vs "pre-action disclosure"

Usage:
    python evals/test_search_quality.py --verbose          # Run all tests
    python evals/test_search_quality.py --category typos   # Run specific category
    python evals/test_search_quality.py --suggest          # Get synonym suggestions
    python evals/test_search_quality.py --output results/  # Save detailed results

This helps identify gaps in synonym mapping and search configuration.
"""

import argparse
import asyncio
import json
import logging
import os
import re
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Optional

# Add paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app", "backend"))

from load_azd_env import load_azd_env

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class TestCategory(Enum):
    """Categories of search quality tests."""
    TERMINOLOGY = "terminology"      # Colloquial vs official terms (synonym map)
    TYPOS = "typos"                  # Common spelling errors (fuzzy search)
    ABBREVIATIONS = "abbreviations"  # Acronyms and short forms (synonym map)
    SPELLING = "spelling"            # British vs American spelling (synonym map)
    HYPHENATION = "hyphenation"      # Hyphen variations (synonym map)
    CASE = "case"                    # Case sensitivity (handled by analyzers)
    WORD_ORDER = "word_order"        # Inverted word order (synonym map)
    PARTIAL = "partial"              # Partial vs full terms (no fix needed)


# Which categories need which solution
CATEGORY_SOLUTIONS = {
    TestCategory.TERMINOLOGY: "synonym_map",
    TestCategory.TYPOS: "fuzzy_search",  # Typos need fuzzy search, not synonym maps
    TestCategory.ABBREVIATIONS: "synonym_map",
    TestCategory.SPELLING: "synonym_map",
    TestCategory.HYPHENATION: "synonym_map",
    TestCategory.CASE: "analyzer",  # Handled by search analyzers
    TestCategory.WORD_ORDER: "synonym_map",
    TestCategory.PARTIAL: "none",  # Expected behavior
}


@dataclass
class SearchTestCase:
    """Test case for search quality."""
    query: str                        # The test query
    expected_query: str               # The "correct" query that should return results
    category: TestCategory            # Type of issue being tested
    description: str                  # Human-readable description
    expected_cpr_parts: list[str] = field(default_factory=list)  # Expected CPR references
    severity: str = "medium"          # low, medium, high, critical
    known_limitation: bool = False    # True if this is a known limitation that can't be fixed


# ============================================================================
# TEST CASES: Organized by category
# ============================================================================

# 1. TERMINOLOGY MISMATCHES
TERMINOLOGY_TESTS = [
    SearchTestCase(
        query="pre-action disclosure",
        expected_query="disclosure before proceedings have started",
        category=TestCategory.TERMINOLOGY,
        description="Pre-action disclosure (colloquial)",
        expected_cpr_parts=["CPR 31.16"],
        severity="high"
    ),
    SearchTestCase(
        query="third party disclosure",
        expected_query="disclosure by a person who is not a party",
        category=TestCategory.TERMINOLOGY,
        description="Third party disclosure (colloquial)",
        expected_cpr_parts=["CPR 31.17"],
        severity="high"
    ),
    SearchTestCase(
        query="freezing order",
        expected_query="freezing injunction",
        category=TestCategory.TERMINOLOGY,
        description="Freezing order vs injunction",
        expected_cpr_parts=["Part 25"],
        severity="high"
    ),
    SearchTestCase(
        query="mareva injunction",
        expected_query="freezing injunction",
        category=TestCategory.TERMINOLOGY,
        description="Historical Mareva terminology",
        expected_cpr_parts=["Part 25"],
        severity="medium"
    ),
    SearchTestCase(
        query="anton piller order",
        expected_query="search order",
        category=TestCategory.TERMINOLOGY,
        description="Historical Anton Piller terminology",
        expected_cpr_parts=["Part 25"],
        severity="medium"
    ),
    SearchTestCase(
        query="default judgment",
        expected_query="judgment in default",
        category=TestCategory.TERMINOLOGY,
        description="Default judgment terminology",
        expected_cpr_parts=["Part 12"],
        severity="high"
    ),
    SearchTestCase(
        query="summary judgment",
        expected_query="judgment without trial",
        category=TestCategory.TERMINOLOGY,
        description="Summary judgment terminology",
        expected_cpr_parts=["Part 24"],
        severity="high"
    ),
    SearchTestCase(
        query="striking out",
        expected_query="strike out",
        category=TestCategory.TERMINOLOGY,
        description="Strike out variations",
        expected_cpr_parts=["Part 3"],
        severity="medium"
    ),
    SearchTestCase(
        query="interlocutory injunction",
        expected_query="interim injunction",
        category=TestCategory.TERMINOLOGY,
        description="Historical interlocutory terminology",
        expected_cpr_parts=["Part 25"],
        severity="medium"
    ),
    SearchTestCase(
        query="discovery",
        expected_query="disclosure",
        category=TestCategory.TERMINOLOGY,
        description="Old discovery terminology (historical - rare in CPR)",
        expected_cpr_parts=["Part 31"],
        severity="low"  # Low because CPR uses 'disclosure', not 'discovery'
    ),
    SearchTestCase(
        query="plaintiff",
        expected_query="claimant",
        category=TestCategory.TERMINOLOGY,
        description="Old plaintiff terminology (historical - rare in CPR)",
        expected_cpr_parts=["Part 2"],
        severity="low"  # Low because CPR uses 'claimant', not 'plaintiff'
    ),
    SearchTestCase(
        query="leave to appeal",
        expected_query="permission to appeal",
        category=TestCategory.TERMINOLOGY,
        description="Leave vs permission terminology",
        expected_cpr_parts=["Part 52"],
        severity="medium"
    ),
    # ========================================================================
    # PHASE 2 ADDITIONS: INTERIM REMEDIES, GROUP LITIGATION, COSTS MANAGEMENT
    # ========================================================================
    SearchTestCase(
        query="privacy injunction",
        expected_query="non-disclosure order",
        category=TestCategory.TERMINOLOGY,
        description="Privacy injunction vs non-disclosure order",
        expected_cpr_parts=["Part 25"],
        severity="high"
    ),
    SearchTestCase(
        query="super-injunction",
        expected_query="non-publication order",
        category=TestCategory.TERMINOLOGY,
        description="Super-injunction (modern non-publication order)",
        expected_cpr_parts=["Part 25"],
        severity="medium"
    ),
    SearchTestCase(
        query="ex parte injunction",
        expected_query="interim injunction without notice",
        category=TestCategory.TERMINOLOGY,
        description="Ex parte injunction vs without notice application",
        expected_cpr_parts=["Part 25"],
        severity="medium"
    ),
    SearchTestCase(
        query="Precedent H",
        expected_query="costs budget",
        category=TestCategory.TERMINOLOGY,
        description="Precedent H (costs form) vs costs budget",
        expected_cpr_parts=["Part 3"],
        severity="high"
    ),
    SearchTestCase(
        query="costs schedule",
        expected_query="costs budget",
        category=TestCategory.TERMINOLOGY,
        description="Costs schedule vs costs budget",
        expected_cpr_parts=["Part 3"],
        severity="medium"
    ),
    SearchTestCase(
        query="CMO",
        expected_query="costs management order",
        category=TestCategory.TERMINOLOGY,
        description="CMO abbreviation for costs management order",
        expected_cpr_parts=["Part 3"],
        severity="medium"
    ),
    SearchTestCase(
        query="test claim",
        expected_query="lead claim",
        category=TestCategory.TERMINOLOGY,
        description="Test claim vs lead claim (group litigation terminology)",
        expected_cpr_parts=["Part 19"],
        severity="medium"
    ),
    SearchTestCase(
        query="GLO",
        expected_query="group litigation order",
        category=TestCategory.TERMINOLOGY,
        description="GLO abbreviation for group litigation order",
        expected_cpr_parts=["Part 19"],
        severity="medium"
    ),
    SearchTestCase(
        query="indemnity basis",
        expected_query="indemnity standard",
        category=TestCategory.TERMINOLOGY,
        description="Indemnity basis vs indemnity standard",
        expected_cpr_parts=["Part 44"],
        severity="medium"
    ),
    SearchTestCase(
        query="detailed assessment",
        expected_query="costs taxing",
        category=TestCategory.TERMINOLOGY,
        description="Detailed assessment vs costs taxing",
        expected_cpr_parts=["Part 47"],
        severity="medium"
    ),
    # ========================================================================
    # PHASE 3 ADDITIONS: TRIAL PROCEDURE, DEFECTS, SPECIALIZED CLAIMS
    # ========================================================================
    SearchTestCase(
        query="trial bundle",
        expected_query="court bundle",
        category=TestCategory.TERMINOLOGY,
        description="Trial bundle vs court bundle",
        expected_cpr_parts=["Part 29"],
        severity="medium"
    ),
    SearchTestCase(
        query="authorities bundle",
        expected_query="bundle of authorities",
        category=TestCategory.TERMINOLOGY,
        description="Authorities bundle terminology",
        expected_cpr_parts=["Part 35"],
        severity="low"
    ),
    SearchTestCase(
        query="striking out",
        expected_query="strike-out",
        category=TestCategory.TERMINOLOGY,
        description="Striking out (verb) vs strike-out (noun)",
        expected_cpr_parts=["Part 3"],
        severity="low"
    ),
    SearchTestCase(
        query="abuse of process",
        expected_query="vexatious claim",
        category=TestCategory.TERMINOLOGY,
        description="Abuse of process vs vexatious claim",
        expected_cpr_parts=["Part 3"],
        severity="medium"
    ),
    SearchTestCase(
        query="relief from sanction",
        expected_query="relief from default",
        category=TestCategory.TERMINOLOGY,
        description="Relief from sanction vs relief from default",
        expected_cpr_parts=["Part 3"],
        severity="medium"
    ),
    SearchTestCase(
        query="totally without merit",
        expected_query="manifestly unfounded",
        category=TestCategory.TERMINOLOGY,
        description="TWM (totally without merit) vs manifestly unfounded",
        expected_cpr_parts=["Part 23"],
        severity="high"
    ),
    SearchTestCase(
        query="RTA claim",
        expected_query="road traffic accident claim",
        category=TestCategory.TERMINOLOGY,
        description="RTA abbreviation for road traffic accident",
        expected_cpr_parts=["Part 45"],
        severity="high"
    ),
    SearchTestCase(
        query="low value claim",
        expected_query="low value personal injury",
        category=TestCategory.TERMINOLOGY,
        description="Low-value claims procedure",
        expected_cpr_parts=["Part 45"],
        severity="medium"
    ),
    SearchTestCase(
        query="defamation claim",
        expected_query="libel claim",
        category=TestCategory.TERMINOLOGY,
        description="Defamation vs libel terminology",
        expected_cpr_parts=["Part 53"],
        severity="medium"
    ),
    SearchTestCase(
        query="qualified privilege",
        expected_query="privilege defence",
        category=TestCategory.TERMINOLOGY,
        description="Qualified privilege as a defence",
        expected_cpr_parts=["Part 53"],
        severity="medium"
    ),
    SearchTestCase(
        query="judicial review",
        expected_query="JR application",
        category=TestCategory.TERMINOLOGY,
        description="Judicial review abbreviated as JR",
        expected_cpr_parts=["Part 54"],
        severity="high"
    ),
    SearchTestCase(
        query="media and communications list",
        expected_query="MCL",
        category=TestCategory.TERMINOLOGY,
        description="Media and Communications List abbreviated as MCL",
        expected_cpr_parts=["Part 39"],
        severity="medium"
    ),
    SearchTestCase(
        query="OIC portal",
        expected_query="official injury claims portal",
        category=TestCategory.TERMINOLOGY,
        description="Official Injury Claims portal (April 2025 update)",
        expected_cpr_parts=["Part 45"],
        severity="high"
    ),
    SearchTestCase(
        query="data protection claim",
        expected_query="GDPR claim",
        category=TestCategory.TERMINOLOGY,
        description="Data protection vs GDPR terminology",
        expected_cpr_parts=["Part 68"],
        severity="medium"
    ),
]

# 2. COMMON TYPOS AND SPELLING ERRORS
TYPO_TESTS = [
    # Disclosure typos
    SearchTestCase(
        query="discloure",
        expected_query="disclosure",
        category=TestCategory.TYPOS,
        description="Disclosure misspelling (missing 's')",
        expected_cpr_parts=["Part 31"],
        severity="high"
    ),
    SearchTestCase(
        query="disclousure",
        expected_query="disclosure",
        category=TestCategory.TYPOS,
        description="Disclosure misspelling (extra 'u')",
        expected_cpr_parts=["Part 31"],
        severity="high"
    ),
    SearchTestCase(
        query="diclosure",
        expected_query="disclosure",
        category=TestCategory.TYPOS,
        description="Disclosure misspelling (missing 's')",
        expected_cpr_parts=["Part 31"],
        severity="medium"
    ),
    # Injunction typos
    SearchTestCase(
        query="injuction",
        expected_query="injunction",
        category=TestCategory.TYPOS,
        description="Injunction misspelling (missing 'n')",
        expected_cpr_parts=["Part 25"],
        severity="high"
    ),
    SearchTestCase(
        query="injuntion",
        expected_query="injunction",
        category=TestCategory.TYPOS,
        description="Injunction misspelling (missing 'c')",
        expected_cpr_parts=["Part 25"],
        severity="medium"
    ),
    SearchTestCase(
        query="freezeing order",
        expected_query="freezing order",
        category=TestCategory.TYPOS,
        description="Freezing misspelling (extra 'e')",
        expected_cpr_parts=["Part 25"],
        severity="medium"
    ),
    # Judgment typos
    SearchTestCase(
        query="judgement",
        expected_query="judgment",
        category=TestCategory.TYPOS,
        description="Judgment with 'e' (common error)",
        expected_cpr_parts=["Part 12", "Part 24"],
        severity="high"
    ),
    SearchTestCase(
        query="jugdment",
        expected_query="judgment",
        category=TestCategory.TYPOS,
        description="Judgment transposition error",
        expected_cpr_parts=["Part 12"],
        severity="medium"
    ),
    SearchTestCase(
        query="sumary judgment",
        expected_query="summary judgment",
        category=TestCategory.TYPOS,
        description="Summary missing 'm'",
        expected_cpr_parts=["Part 24"],
        severity="medium"
    ),
    # Defendant/Claimant typos
    SearchTestCase(
        query="defendent",
        expected_query="defendant",
        category=TestCategory.TYPOS,
        description="Defendant misspelling",
        expected_cpr_parts=["Part 10"],
        severity="medium"
    ),
    SearchTestCase(
        query="claiment",
        expected_query="claimant",
        category=TestCategory.TYPOS,
        description="Claimant misspelling",
        expected_cpr_parts=["Part 7"],
        severity="medium"
    ),
    # Particulars typos
    SearchTestCase(
        query="particulars of cliam",
        expected_query="particulars of claim",
        category=TestCategory.TYPOS,
        description="Claim transposition error",
        expected_cpr_parts=["Part 16"],
        severity="medium"
    ),
    SearchTestCase(
        query="particualrs of claim",
        expected_query="particulars of claim",
        category=TestCategory.TYPOS,
        description="Particulars transposition error",
        expected_cpr_parts=["Part 16"],
        severity="medium"
    ),
    # Witness typos
    SearchTestCase(
        query="witnes statement",
        expected_query="witness statement",
        category=TestCategory.TYPOS,
        description="Witness missing 's'",
        expected_cpr_parts=["Part 32"],
        severity="medium"
    ),
    SearchTestCase(
        query="witness statment",
        expected_query="witness statement",
        category=TestCategory.TYPOS,
        description="Statement missing 'e'",
        expected_cpr_parts=["Part 32"],
        severity="medium"
    ),
    # Acknowledgment typos
    SearchTestCase(
        query="acknowlegement of service",
        expected_query="acknowledgment of service",
        category=TestCategory.TYPOS,
        description="Acknowledgement misspelling",
        expected_cpr_parts=["Part 10"],
        severity="medium"
    ),
    # Costs typos
    SearchTestCase(
        query="securty for costs",
        expected_query="security for costs",
        category=TestCategory.TYPOS,
        description="Security misspelling",
        expected_cpr_parts=["CPR 25.12"],
        severity="medium"
    ),
    SearchTestCase(
        query="watsed costs",
        expected_query="wasted costs",
        category=TestCategory.TYPOS,
        description="Wasted transposition",
        expected_cpr_parts=["Part 46"],
        severity="medium"
    ),
    # Procedural typos
    SearchTestCase(
        query="proceedigns",
        expected_query="proceedings",
        category=TestCategory.TYPOS,
        description="Proceedings misspelling",
        expected_cpr_parts=["Part 7"],
        severity="medium"
    ),
    SearchTestCase(
        query="appplication",
        expected_query="application",
        category=TestCategory.TYPOS,
        description="Application double 'p'",
        expected_cpr_parts=["Part 23"],
        severity="medium"
    ),
    SearchTestCase(
        query="aplication notice",
        expected_query="application notice",
        category=TestCategory.TYPOS,
        description="Application missing 'p'",
        expected_cpr_parts=["Part 23"],
        severity="medium"
    ),
]

# 3. ABBREVIATION HANDLING
ABBREVIATION_TESTS = [
    SearchTestCase(
        query="CPR Part 31",
        expected_query="Civil Procedure Rules Part 31",
        category=TestCategory.ABBREVIATIONS,
        description="CPR abbreviation",
        expected_cpr_parts=["Part 31"],
        severity="high"
    ),
    SearchTestCase(
        query="C.P.R. 31",
        expected_query="CPR Part 31",
        category=TestCategory.ABBREVIATIONS,
        description="CPR with dots",
        expected_cpr_parts=["Part 31"],
        severity="medium"
    ),
    SearchTestCase(
        query="PD 31",
        expected_query="Practice Direction 31",
        category=TestCategory.ABBREVIATIONS,
        description="Practice Direction abbreviation",
        expected_cpr_parts=["Part 31"],
        severity="medium"
    ),
    SearchTestCase(
        query="P.D. 31A",
        expected_query="Practice Direction 31A",
        category=TestCategory.ABBREVIATIONS,
        description="PD with dots",
        expected_cpr_parts=["Part 31"],
        severity="medium"
    ),
    SearchTestCase(
        query="CMC",
        expected_query="case management conference",
        category=TestCategory.ABBREVIATIONS,
        description="CMC abbreviation",
        expected_cpr_parts=["Part 29"],
        severity="medium"
    ),
    SearchTestCase(
        query="PTR",
        expected_query="pre-trial review",
        category=TestCategory.ABBREVIATIONS,
        description="PTR abbreviation",
        expected_cpr_parts=["Part 29"],
        severity="medium"
    ),
    SearchTestCase(
        query="GLO",
        expected_query="group litigation order",
        category=TestCategory.ABBREVIATIONS,
        description="GLO abbreviation",
        expected_cpr_parts=["Part 19"],
        severity="medium"
    ),
    SearchTestCase(
        query="JR",
        expected_query="judicial review",
        category=TestCategory.ABBREVIATIONS,
        description="JR abbreviation",
        expected_cpr_parts=["Part 54"],
        severity="medium"
    ),
    SearchTestCase(
        query="ADR",
        expected_query="alternative dispute resolution",
        category=TestCategory.ABBREVIATIONS,
        description="ADR abbreviation",
        expected_cpr_parts=["Part 1"],
        severity="medium"
    ),
    SearchTestCase(
        query="r. 31.6",
        expected_query="rule 31.6",
        category=TestCategory.ABBREVIATIONS,
        description="Rule abbreviation with period (known limitation - tokenizer issue)",
        expected_cpr_parts=["Part 31"],
        severity="low",  # Low priority - requires custom analyzer to fix
        known_limitation=True
    ),
]

# 4. BRITISH VS AMERICAN SPELLING
SPELLING_TESTS = [
    SearchTestCase(
        query="defense",
        expected_query="defence",
        category=TestCategory.SPELLING,
        description="American 'defense' spelling",
        expected_cpr_parts=["Part 15"],
        severity="high"
    ),
    SearchTestCase(
        query="judgment",
        expected_query="judgement",  # Both are used in UK
        category=TestCategory.SPELLING,
        description="Judgment vs judgement (both valid)",
        expected_cpr_parts=["Part 12"],
        severity="low"
    ),
    SearchTestCase(
        query="acknowledgement of service",
        expected_query="acknowledgment of service",
        category=TestCategory.SPELLING,
        description="Acknowledgement variant",
        expected_cpr_parts=["Part 10"],
        severity="medium"
    ),
    SearchTestCase(
        query="honor",
        expected_query="honour",
        category=TestCategory.SPELLING,
        description="American 'honor' spelling",
        expected_cpr_parts=[],
        severity="low"
    ),
    SearchTestCase(
        query="favor",
        expected_query="favour",
        category=TestCategory.SPELLING,
        description="American 'favor' spelling",
        expected_cpr_parts=[],
        severity="low"
    ),
    SearchTestCase(
        query="authorized",
        expected_query="authorised",
        category=TestCategory.SPELLING,
        description="American 'z' spelling",
        expected_cpr_parts=[],
        severity="low"
    ),
]

# 5. HYPHENATION VARIATIONS
HYPHENATION_TESTS = [
    SearchTestCase(
        query="preaction disclosure",
        expected_query="pre-action disclosure",
        category=TestCategory.HYPHENATION,
        description="Pre-action without hyphen",
        expected_cpr_parts=["CPR 31.16"],
        severity="high"
    ),
    SearchTestCase(
        query="pre action disclosure",
        expected_query="pre-action disclosure",
        category=TestCategory.HYPHENATION,
        description="Pre-action with space",
        expected_cpr_parts=["CPR 31.16"],
        severity="high"
    ),
    SearchTestCase(
        query="thirdparty disclosure",
        expected_query="third party disclosure",
        category=TestCategory.HYPHENATION,
        description="Third party without space",
        expected_cpr_parts=["CPR 31.17"],
        severity="medium"
    ),
    SearchTestCase(
        query="third-party disclosure",
        expected_query="third party disclosure",
        category=TestCategory.HYPHENATION,
        description="Third-party with hyphen",
        expected_cpr_parts=["CPR 31.17"],
        severity="medium"
    ),
    SearchTestCase(
        query="pretrial review",
        expected_query="pre-trial review",
        category=TestCategory.HYPHENATION,
        description="Pre-trial without hyphen",
        expected_cpr_parts=["Part 29"],
        severity="medium"
    ),
    SearchTestCase(
        query="multitrack",
        expected_query="multi-track",
        category=TestCategory.HYPHENATION,
        description="Multi-track without hyphen",
        expected_cpr_parts=["Part 29"],
        severity="low"
    ),
    SearchTestCase(
        query="fasttrack",
        expected_query="fast track",
        category=TestCategory.HYPHENATION,
        description="Fast track without space",
        expected_cpr_parts=["Part 28"],
        severity="low"
    ),
    SearchTestCase(
        query="counter-claim",
        expected_query="counterclaim",
        category=TestCategory.HYPHENATION,
        description="Counterclaim with hyphen",
        expected_cpr_parts=["Part 20"],
        severity="low"
    ),
    SearchTestCase(
        query="set-off",
        expected_query="set off",
        category=TestCategory.HYPHENATION,
        description="Set-off hyphen variation",
        expected_cpr_parts=["Part 16"],
        severity="low"
    ),
]

# 6. CASE SENSITIVITY
CASE_TESTS = [
    SearchTestCase(
        query="cpr part 31",
        expected_query="CPR Part 31",
        category=TestCategory.CASE,
        description="Lowercase 'cpr'",
        expected_cpr_parts=["Part 31"],
        severity="low"
    ),
    SearchTestCase(
        query="DISCLOSURE RULES",
        expected_query="disclosure rules",
        category=TestCategory.CASE,
        description="All caps query",
        expected_cpr_parts=["Part 31"],
        severity="low"
    ),
    SearchTestCase(
        query="Freezing Injunction",
        expected_query="freezing injunction",
        category=TestCategory.CASE,
        description="Title case query",
        expected_cpr_parts=["Part 25"],
        severity="low"
    ),
]

# 7. WORD ORDER VARIATIONS
WORD_ORDER_TESTS = [
    SearchTestCase(
        query="costs security",
        expected_query="security for costs",
        category=TestCategory.WORD_ORDER,
        description="Inverted word order",
        expected_cpr_parts=["CPR 25.12"],
        severity="medium"
    ),
    SearchTestCase(
        query="service acknowledgment",
        expected_query="acknowledgment of service",
        category=TestCategory.WORD_ORDER,
        description="Inverted acknowledgment order",
        expected_cpr_parts=["Part 10"],
        severity="medium"
    ),
    SearchTestCase(
        query="statement witness",
        expected_query="witness statement",
        category=TestCategory.WORD_ORDER,
        description="Inverted witness order",
        expected_cpr_parts=["Part 32"],
        severity="low"
    ),
    SearchTestCase(
        query="costs wasted",
        expected_query="wasted costs",
        category=TestCategory.WORD_ORDER,
        description="Inverted wasted costs",
        expected_cpr_parts=["Part 46"],
        severity="low"
    ),
    SearchTestCase(
        query="claim particulars",
        expected_query="particulars of claim",
        category=TestCategory.WORD_ORDER,
        description="Inverted particulars order",
        expected_cpr_parts=["Part 16"],
        severity="low"
    ),
]

# 8. PARTIAL TERM MATCHING
PARTIAL_TESTS = [
    SearchTestCase(
        query="disclosure",
        expected_query="standard disclosure",
        category=TestCategory.PARTIAL,
        description="Generic disclosure (should find all types)",
        expected_cpr_parts=["Part 31"],
        severity="low"
    ),
    SearchTestCase(
        query="injunction",
        expected_query="interim injunction",
        category=TestCategory.PARTIAL,
        description="Generic injunction",
        expected_cpr_parts=["Part 25"],
        severity="low"
    ),
    SearchTestCase(
        query="costs",
        expected_query="costs order",
        category=TestCategory.PARTIAL,
        description="Generic costs",
        expected_cpr_parts=["Part 44"],
        severity="low"
    ),
    SearchTestCase(
        query="judgment",
        expected_query="judgment in default",
        category=TestCategory.PARTIAL,
        description="Generic judgment",
        expected_cpr_parts=["Part 12", "Part 24"],
        severity="low"
    ),
]

# Combine all tests
ALL_TESTS = (
    TERMINOLOGY_TESTS + 
    TYPO_TESTS + 
    ABBREVIATION_TESTS + 
    SPELLING_TESTS + 
    HYPHENATION_TESTS + 
    CASE_TESTS + 
    WORD_ORDER_TESTS + 
    PARTIAL_TESTS
)


@dataclass
class TestResult:
    """Result of a single test case."""
    test_case: SearchTestCase
    query_hits: int
    expected_hits: int
    has_gap: bool
    gap_severity: str  # none, minor, significant, critical
    passed: bool
    sources_found: list[str]
    suggested_synonym: Optional[str] = None
    fuzzy_hits: Optional[int] = None  # Hits with fuzzy search (for typo tests)


async def search_query(
    search_client, 
    query: str, 
    top: int = 5, 
    use_fuzzy: bool = False
) -> tuple[int, list[str]]:
    """Execute a search query and return hit count and sources."""
    try:
        if use_fuzzy:
            # Add fuzzy operator ~1 (edit distance 1) to each word for typo tolerance
            words = query.split()
            fuzzy_query = " ".join(f"{word}~1" for word in words if len(word) > 2)
            if not fuzzy_query:
                fuzzy_query = query
            results = search_client.search(fuzzy_query, top=top, query_type="full")
        else:
            results = search_client.search(query, top=top)
        
        hits = list(results)
        sources = [hit.get("sourcepage", hit.get("title", "Unknown")) for hit in hits]
        return len(hits), sources
    except Exception as e:
        logger.warning(f"Search error for '{query}': {e}")
        return 0, []


async def run_test(test_case: SearchTestCase, search_client) -> TestResult:
    """Run a single test case."""
    query_hits, query_sources = await search_query(search_client, test_case.query)
    expected_hits, expected_sources = await search_query(search_client, test_case.expected_query)
    
    # For typo tests, also test with fuzzy search to see if that helps
    fuzzy_hits = None
    if test_case.category == TestCategory.TYPOS:
        fuzzy_hits, _ = await search_query(search_client, test_case.query, use_fuzzy=True)
    
    # Determine gap severity
    has_gap = False
    gap_severity = "none"
    
    if query_hits == 0 and expected_hits > 0:
        has_gap = True
        gap_severity = "critical"
    elif expected_hits > 0 and query_hits < expected_hits * 0.5:
        has_gap = True
        gap_severity = "significant"
    elif expected_hits > 0 and query_hits < expected_hits * 0.8:
        has_gap = True
        gap_severity = "minor"
    
    # Determine pass/fail based on category
    # For typos, we pass if fuzzy search works (even if regular search fails)
    # For known limitations, we always pass (they're documented as unfixable)
    if test_case.known_limitation:
        passed = True
    elif test_case.category == TestCategory.TYPOS:
        # Typos pass if either regular search or fuzzy search finds results
        passed = (query_hits > 0 or (fuzzy_hits is not None and fuzzy_hits > 0)) or expected_hits == 0
    else:
        passed = not has_gap or gap_severity == "none"
    
    # Generate synonym suggestion
    suggested_synonym = None
    if has_gap and gap_severity in ("critical", "significant") and not test_case.known_limitation:
        suggested_synonym = f"{test_case.query}, {test_case.expected_query}"
    
    return TestResult(
        test_case=test_case,
        query_hits=query_hits,
        expected_hits=expected_hits,
        has_gap=has_gap,
        gap_severity=gap_severity,
        passed=passed,
        sources_found=query_sources[:3],
        suggested_synonym=suggested_synonym,
        fuzzy_hits=fuzzy_hits
    )


async def run_tests(
    search_client, 
    categories: Optional[list[TestCategory]] = None,
    verbose: bool = False
) -> dict:
    """Run all tests and return summary."""
    
    # Filter by category if specified
    tests_to_run = ALL_TESTS
    if categories:
        tests_to_run = [t for t in ALL_TESTS if t.category in categories]
    
    results: list[TestResult] = []
    
    for test_case in tests_to_run:
        result = await run_test(test_case, search_client)
        results.append(result)
        
        if verbose:
            status = "✅" if result.passed else "❌"
            logger.info(f"{status} [{test_case.category.value}] {test_case.description}")
            logger.info(f"   Query '{test_case.query}': {result.query_hits} hits")
            if result.fuzzy_hits is not None:
                logger.info(f"   Fuzzy '{test_case.query}~1': {result.fuzzy_hits} hits")
            logger.info(f"   Expected '{test_case.expected_query}': {result.expected_hits} hits")
            if result.has_gap:
                solution = CATEGORY_SOLUTIONS.get(test_case.category, "unknown")
                logger.info(f"   ⚠️  Gap: {result.gap_severity} (fix: {solution})")
    
    # Calculate summary statistics
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    failed = total - passed
    
    # By category
    by_category = {}
    for cat in TestCategory:
        cat_results = [r for r in results if r.test_case.category == cat]
        if cat_results:
            solution = CATEGORY_SOLUTIONS.get(cat, "unknown")
            by_category[cat.value] = {
                "total": len(cat_results),
                "passed": sum(1 for r in cat_results if r.passed),
                "failed": sum(1 for r in cat_results if not r.passed),
                "critical_gaps": sum(1 for r in cat_results if r.gap_severity == "critical"),
                "solution": solution,
            }
    
    # By severity
    critical_gaps = [r for r in results if r.gap_severity == "critical"]
    significant_gaps = [r for r in results if r.gap_severity == "significant"]
    
    # Count typos that need fuzzy search
    typo_needs_fuzzy = sum(
        1 for r in results 
        if r.test_case.category == TestCategory.TYPOS 
        and r.query_hits == 0 
        and r.fuzzy_hits is not None 
        and r.fuzzy_hits > 0
    )
    
    # Generate suggestions
    suggestions = []
    for result in results:
        if result.suggested_synonym:
            suggestions.append({
                "category": result.test_case.category.value,
                "description": result.test_case.description,
                "synonym": result.suggested_synonym,
                "severity": result.gap_severity,
                "solution": CATEGORY_SOLUTIONS.get(result.test_case.category, "unknown")
            })
    
    summary = {
        "timestamp": datetime.now().isoformat(),
        "total_tests": total,
        "passed": passed,
        "failed": failed,
        "pass_rate": passed / total if total > 0 else 0,
        "critical_gaps": len(critical_gaps),
        "significant_gaps": len(significant_gaps),
        "typos_need_fuzzy_search": typo_needs_fuzzy,
        "by_category": by_category,
        "suggestions": suggestions,
        "detailed_results": [
            {
                "query": r.test_case.query,
                "expected": r.test_case.expected_query,
                "category": r.test_case.category.value,
                "description": r.test_case.description,
                "query_hits": r.query_hits,
                "fuzzy_hits": r.fuzzy_hits,
                "expected_hits": r.expected_hits,
                "passed": r.passed,
                "gap_severity": r.gap_severity,
                "solution": CATEGORY_SOLUTIONS.get(r.test_case.category, "unknown"),
                "sources": r.sources_found
            }
            for r in results
        ]
    }
    
    return summary


def print_suggestions(suggestions: list[dict]):
    """Print synonym suggestions in a format ready for the synonym map."""
    logger.info("")
    logger.info("=" * 60)
    logger.info("SUGGESTED SYNONYM ADDITIONS")
    logger.info("=" * 60)
    logger.info("Add these to scripts/manage_synonym_map.py LEGAL_SYNONYMS:")
    logger.info("")
    
    # Group by category
    by_cat = {}
    for s in suggestions:
        cat = s["category"]
        if cat not in by_cat:
            by_cat[cat] = []
        by_cat[cat].append(s)
    
    for cat, items in by_cat.items():
        logger.info(f"# {cat.upper()}")
        for item in items:
            severity_marker = "⚠️ " if item["severity"] == "critical" else ""
            logger.info(f"{severity_marker}{item['synonym']}  # {item['description']}")
        logger.info("")


async def main():
    parser = argparse.ArgumentParser(
        description="Comprehensive legal search quality evaluation"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--output", "-o", type=str, help="Output directory for results")
    parser.add_argument("--suggest", "-s", action="store_true", help="Show synonym suggestions")
    parser.add_argument(
        "--category", "-c", 
        type=str, 
        choices=[c.value for c in TestCategory],
        help="Run only specific category"
    )
    args = parser.parse_args()
    
    try:
        from azure.identity import AzureDeveloperCliCredential
        from azure.search.documents import SearchClient
        
        load_azd_env()
        
        search_service = os.environ.get("AZURE_SEARCH_SERVICE")
        search_index = os.environ.get("AZURE_SEARCH_INDEX")
        
        if not search_service or not search_index:
            raise ValueError("AZURE_SEARCH_SERVICE and AZURE_SEARCH_INDEX must be set")
        
        endpoint = f"https://{search_service}.search.windows.net"
        credential = AzureDeveloperCliCredential(tenant_id=os.environ.get("AZURE_TENANT_ID"))
        
        search_client = SearchClient(endpoint=endpoint, index_name=search_index, credential=credential)
        
        logger.info("=" * 60)
        logger.info("LEGAL SEARCH QUALITY EVALUATION")
        logger.info("=" * 60)
        logger.info(f"Testing {len(ALL_TESTS)} scenarios across {len(TestCategory)} categories")
        logger.info("")
        
        # Determine categories to test
        categories = None
        if args.category:
            categories = [TestCategory(args.category)]
            logger.info(f"Running only: {args.category}")
        
        # Run tests
        summary = await run_tests(
            search_client, 
            categories=categories,
            verbose=args.verbose
        )
        
        # Print summary
        logger.info("")
        logger.info("=" * 60)
        logger.info("SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total Tests:      {summary['total_tests']}")
        logger.info(f"Passed:           {summary['passed']}")
        logger.info(f"Failed:           {summary['failed']}")
        logger.info(f"Pass Rate:        {summary['pass_rate']:.1%}")
        logger.info(f"Critical Gaps:    {summary['critical_gaps']}")
        logger.info(f"Significant Gaps: {summary['significant_gaps']}")
        logger.info("")
        logger.info("BY CATEGORY:")
        for cat, stats in summary["by_category"].items():
            status = "✅" if stats["failed"] == 0 else "❌"
            solution = stats.get("solution", "")
            solution_hint = f" (fix: {solution})" if stats["failed"] > 0 else ""
            logger.info(f"  {status} {cat}: {stats['passed']}/{stats['total']} passed{solution_hint}")
        
        # Show recommendations
        if summary.get("typos_need_fuzzy_search", 0) > 0:
            logger.info("")
            logger.info("💡 RECOMMENDATION: Enable fuzzy search for typo tolerance")
            logger.info(f"   {summary['typos_need_fuzzy_search']} typo(s) would be fixed by enabling fuzzy search")
            logger.info("   See docs/legal_synonyms.md for implementation details")
        
        # Show suggestions if requested
        if args.suggest and summary["suggestions"]:
            print_suggestions(summary["suggestions"])
        
        # Save results if output specified
        if args.output:
            os.makedirs(args.output, exist_ok=True)
            output_file = os.path.join(args.output, f"search_quality_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            with open(output_file, "w") as f:
                json.dump(summary, f, indent=2)
            logger.info(f"\nResults saved to {output_file}")
        
        # Exit with error code if critical gaps
        if summary["critical_gaps"] > 0:
            logger.info(f"\n⚠️  {summary['critical_gaps']} critical gap(s) found - run with --suggest for fixes")
            sys.exit(1)
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
