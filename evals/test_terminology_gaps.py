#!/usr/bin/env python3
"""
Legal Terminology Mismatch Detection

This evaluation script detects when users might search using terminology
that doesn't match the official CPR (Civil Procedure Rules) wording in documents.

It does this by:
1. Analyzing common legal search queries from logs or predefined test cases
2. Comparing results when using colloquial vs official terminology
3. Identifying potential gaps that need synonym map updates

Usage:
    python evals/test_terminology_gaps.py --verbose
    python evals/test_terminology_gaps.py --analyze-logs
    python evals/test_terminology_gaps.py --suggest-synonyms

This helps maintain the synonym map as new terminology gaps are discovered.
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from dataclasses import dataclass
from typing import Optional

# Add paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app", "backend"))

from load_azd_env import load_azd_env

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class TerminologyTestCase:
    """Test case for terminology matching."""
    colloquial_term: str  # What users might search for
    official_terms: list[str]  # Official CPR terminology in documents
    expected_cpr_parts: list[str]  # Expected CPR parts that should be found
    description: str  # What this test validates


# Test cases for known terminology variations
TERMINOLOGY_TEST_CASES = [
    TerminologyTestCase(
        colloquial_term="pre-action disclosure",
        official_terms=["disclosure before proceedings have started"],
        expected_cpr_parts=["CPR 31.16"],
        description="Pre-action disclosure terminology"
    ),
    TerminologyTestCase(
        colloquial_term="third party disclosure",
        official_terms=["disclosure by a person who is not a party"],
        expected_cpr_parts=["CPR 31.17"],
        description="Third party disclosure terminology"
    ),
    TerminologyTestCase(
        colloquial_term="freezing order",
        official_terms=["freezing injunction"],
        expected_cpr_parts=["Part 25", "Practice Direction 25A"],
        description="Freezing order terminology"
    ),
    TerminologyTestCase(
        colloquial_term="mareva injunction",
        official_terms=["freezing injunction"],
        expected_cpr_parts=["Part 25"],
        description="Historical Mareva terminology"
    ),
    TerminologyTestCase(
        colloquial_term="anton piller order",
        official_terms=["search order", "search and seizure"],
        expected_cpr_parts=["Part 25", "Practice Direction 25A"],
        description="Historical Anton Piller terminology"
    ),
    TerminologyTestCase(
        colloquial_term="unless order",
        official_terms=["conditional order", "unless order"],
        expected_cpr_parts=["CPR 3.1", "Part 3"],
        description="Unless order terminology"
    ),
    TerminologyTestCase(
        colloquial_term="default judgment",
        official_terms=["judgment in default"],
        expected_cpr_parts=["Part 12"],
        description="Default judgment terminology"
    ),
    TerminologyTestCase(
        colloquial_term="summary judgment",
        official_terms=["judgment without trial"],
        expected_cpr_parts=["Part 24"],
        description="Summary judgment terminology"
    ),
    TerminologyTestCase(
        colloquial_term="wasted costs",
        official_terms=["wasted costs order", "wasted costs"],
        expected_cpr_parts=["CPR 46", "Part 46"],
        description="Wasted costs terminology"
    ),
    TerminologyTestCase(
        colloquial_term="security for costs",
        official_terms=["security for costs"],
        expected_cpr_parts=["CPR 25.12", "Part 25"],
        description="Security for costs terminology"
    ),
    TerminologyTestCase(
        colloquial_term="litigation friend",
        official_terms=["litigation friend", "next friend"],
        expected_cpr_parts=["Part 21"],
        description="Litigation friend terminology"
    ),
    TerminologyTestCase(
        colloquial_term="witness statement",
        official_terms=["witness statement", "witness evidence"],
        expected_cpr_parts=["Part 32"],
        description="Witness statement terminology"
    ),
    TerminologyTestCase(
        colloquial_term="expert witness",
        official_terms=["expert", "expert evidence"],
        expected_cpr_parts=["Part 35"],
        description="Expert witness terminology"
    ),
    TerminologyTestCase(
        colloquial_term="costs budgeting",
        official_terms=["costs budget", "costs management", "precedent H"],
        expected_cpr_parts=["Part 3", "CPR 3.12"],
        description="Costs budgeting terminology"
    ),
]


@dataclass
class SearchResult:
    """Result from a search query."""
    query: str
    total_hits: int
    top_sources: list[str]
    relevant_cpr_parts: list[str]


async def search_query(search_client, query: str, top: int = 5) -> SearchResult:
    """Execute a search query and return structured results."""
    results = search_client.search(query, top=top)
    hits = list(results)
    
    sources = []
    cpr_parts = []
    
    for hit in hits:
        # Extract source info
        source = hit.get("sourcepage", hit.get("title", "Unknown"))
        sources.append(source)
        
        # Extract CPR parts from source names
        content = hit.get("content", "") + " " + source
        import re
        parts = re.findall(r'(?:CPR|Part)\s*[\d.]+', content, re.IGNORECASE)
        cpr_parts.extend(parts)
    
    return SearchResult(
        query=query,
        total_hits=len(hits),
        top_sources=sources[:5],
        relevant_cpr_parts=list(set(cpr_parts))[:5]
    )


async def run_terminology_test(test_case: TerminologyTestCase, search_client, verbose: bool = False) -> dict:
    """Run a single terminology test case."""
    
    # Search with colloquial term
    colloquial_result = await search_query(search_client, test_case.colloquial_term)
    
    # Search with official term(s)
    official_results = []
    for official_term in test_case.official_terms:
        result = await search_query(search_client, official_term)
        official_results.append(result)
    
    # Analyze results
    max_official_hits = max(r.total_hits for r in official_results)
    
    # Terminology gap detection
    has_gap = False
    gap_severity = "none"
    
    if colloquial_result.total_hits == 0 and max_official_hits > 0:
        has_gap = True
        gap_severity = "critical"  # Users get no results
    elif colloquial_result.total_hits < max_official_hits * 0.5:
        has_gap = True
        gap_severity = "significant"  # Users get fewer than half the results
    elif colloquial_result.total_hits < max_official_hits * 0.8:
        has_gap = True
        gap_severity = "minor"  # Users get somewhat fewer results
    
    # Check if expected CPR parts are found
    found_expected = False
    all_cpr_parts = colloquial_result.relevant_cpr_parts
    for r in official_results:
        all_cpr_parts.extend(r.relevant_cpr_parts)
    
    for expected_part in test_case.expected_cpr_parts:
        if any(expected_part.lower() in p.lower() for p in all_cpr_parts):
            found_expected = True
            break
    
    result = {
        "test_name": test_case.description,
        "colloquial_term": test_case.colloquial_term,
        "official_terms": test_case.official_terms,
        "colloquial_hits": colloquial_result.total_hits,
        "official_hits": max_official_hits,
        "has_terminology_gap": has_gap,
        "gap_severity": gap_severity,
        "found_expected_cpr": found_expected,
        "colloquial_sources": colloquial_result.top_sources[:3],
        "passed": not has_gap or gap_severity == "none"
    }
    
    if verbose:
        status = "✅" if result["passed"] else "❌"
        logger.info(f"{status} {test_case.description}")
        logger.info(f"   Colloquial '{test_case.colloquial_term}': {colloquial_result.total_hits} hits")
        logger.info(f"   Official '{test_case.official_terms[0]}': {max_official_hits} hits")
        if has_gap:
            logger.info(f"   ⚠️ GAP DETECTED ({gap_severity}): Consider adding synonym mapping")
    
    return result


async def run_all_tests(search_client, verbose: bool = False) -> dict:
    """Run all terminology tests and return summary."""
    results = []
    
    for test_case in TERMINOLOGY_TEST_CASES:
        result = await run_terminology_test(test_case, search_client, verbose)
        results.append(result)
    
    # Summary statistics
    passed = sum(1 for r in results if r["passed"])
    critical_gaps = sum(1 for r in results if r["gap_severity"] == "critical")
    significant_gaps = sum(1 for r in results if r["gap_severity"] == "significant")
    
    summary = {
        "total_tests": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "critical_gaps": critical_gaps,
        "significant_gaps": significant_gaps,
        "pass_rate": passed / len(results) if results else 0,
        "results": results
    }
    
    return summary


def suggest_synonyms(results: list[dict]) -> list[str]:
    """Generate synonym suggestions for failed tests."""
    suggestions = []
    
    for result in results:
        if result["gap_severity"] in ("critical", "significant"):
            terms = [result["colloquial_term"]] + result["official_terms"]
            suggestion = ", ".join(terms)
            suggestions.append(f"# {result['test_name']}\n{suggestion}")
    
    return suggestions


async def main():
    parser = argparse.ArgumentParser(
        description="Detect legal terminology mismatches in search"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--output", "-o", type=str, help="Output file for results JSON")
    parser.add_argument("--suggest-synonyms", action="store_true", help="Output synonym suggestions")
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
        logger.info("LEGAL TERMINOLOGY MISMATCH DETECTION")
        logger.info("=" * 60)
        
        summary = await run_all_tests(search_client, args.verbose)
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total Tests: {summary['total_tests']}")
        logger.info(f"Passed: {summary['passed']}")
        logger.info(f"Failed: {summary['failed']}")
        logger.info(f"Pass Rate: {summary['pass_rate']:.1%}")
        logger.info(f"Critical Gaps: {summary['critical_gaps']}")
        logger.info(f"Significant Gaps: {summary['significant_gaps']}")
        
        if args.suggest_synonyms and summary["failed"] > 0:
            suggestions = suggest_synonyms(summary["results"])
            logger.info("")
            logger.info("SUGGESTED SYNONYM ADDITIONS:")
            logger.info("-" * 40)
            for suggestion in suggestions:
                logger.info(suggestion)
        
        if args.output:
            with open(args.output, "w") as f:
                json.dump(summary, f, indent=2)
            logger.info(f"\nResults saved to {args.output}")
        
        # Exit with error if critical gaps found
        if summary["critical_gaps"] > 0:
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
