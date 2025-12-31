#!/usr/bin/env python3
"""
Test Azure AI Search Query Rewriting Feature

This script compares search results with and without query rewriting to evaluate
whether it provides additional value on top of synonym maps.

Query Rewriting is an Azure AI Search preview feature that uses a fine-tuned SLM
to generate alternative query formulations.

Usage:
    python evals/test_query_rewriting.py
"""

import os
import sys
import asyncio
import logging
from dataclasses import dataclass
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from load_azd_env import load_azd_env

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class TestCase:
    """A test case for query rewriting evaluation."""
    query: str
    description: str
    category: str
    expected_topics: list[str]  # Topics we expect to find in results


# Test cases organized by type
TEST_CASES = [
    # Legal terminology not in synonym map (natural language)
    TestCase(
        query="suing someone for breach of contract",
        description="Natural language - should find claims procedures",
        category="natural_language",
        expected_topics=["claim", "statement of case", "particulars"]
    ),
    TestCase(
        query="how to get an urgent order from the court",
        description="Natural language - should find interim applications",
        category="natural_language",
        expected_topics=["interim", "application", "injunction", "without notice"]
    ),
    TestCase(
        query="making the other side show their documents",
        description="Natural language - should find disclosure",
        category="natural_language",
        expected_topics=["disclosure", "inspection", "Part 31"]
    ),
    TestCase(
        query="asking for money before trial ends",
        description="Natural language - should find interim payments",
        category="natural_language",
        expected_topics=["interim payment", "Part 25"]
    ),
    
    # Historical legal terms (in synonym map - baseline)
    TestCase(
        query="mareva injunction requirements",
        description="Historical term (in synonym map)",
        category="historical_term",
        expected_topics=["freezing", "injunction", "order"]
    ),
    TestCase(
        query="discovery process in civil cases",
        description="Historical term (in synonym map)",
        category="historical_term",
        expected_topics=["disclosure", "Part 31"]
    ),
    
    # Complex multi-concept queries
    TestCase(
        query="stopping someone from selling assets while waiting for trial",
        description="Complex - freezing orders concept",
        category="complex",
        expected_topics=["freezing", "order", "assets", "injunction"]
    ),
    TestCase(
        query="what happens if defendant ignores court papers",
        description="Complex - default judgment concept",
        category="complex",
        expected_topics=["default", "judgment", "failure", "acknowledge"]
    ),
    
    # Typos and misspellings
    TestCase(
        query="discloure of documetnss",
        description="Typos - disclosure of documents",
        category="typos",
        expected_topics=["disclosure", "documents"]
    ),
]


async def search_with_options(client, query: str, use_rewriting: bool) -> list[dict]:
    """Execute a search with or without query rewriting."""
    from azure.search.documents.models import QueryType
    
    try:
        results = await client.search(
            search_text=query,
            top=5,
            select=["id", "sourcepage", "content"],
            query_type=QueryType.SEMANTIC,
            semantic_configuration_name="default",
            query_language="en-GB",
            query_rewrites="generative|count-5" if use_rewriting else None,
        )
        
        docs = []
        async for r in results:
            docs.append({
                "sourcepage": r.get("sourcepage", ""),
                "content": r.get("content", "")[:500],
                "score": r.get("@search.score", 0),
                "reranker_score": r.get("@search.rerankerScore", 0)
            })
        return docs
    except Exception as e:
        logger.error(f"Search error: {e}")
        return []


def check_topics_found(results: list[dict], expected_topics: list[str]) -> tuple[int, list[str]]:
    """Check how many expected topics are found in results."""
    found = []
    combined_text = " ".join([
        r.get("content", "") + " " + r.get("sourcepage", "") 
        for r in results
    ]).lower()
    
    for topic in expected_topics:
        if topic.lower() in combined_text:
            found.append(topic)
    
    return len(found), found


async def run_comparison():
    """Run comparison between with and without query rewriting."""
    from azure.identity import AzureDeveloperCliCredential
    from azure.search.documents.aio import SearchClient
    
    load_azd_env()
    
    endpoint = f'https://{os.environ["AZURE_SEARCH_SERVICE"]}.search.windows.net'
    index = os.environ['AZURE_SEARCH_INDEX']
    cred = AzureDeveloperCliCredential(tenant_id=os.environ.get('AZURE_TENANT_ID'))
    
    logger.info("=" * 70)
    logger.info("AZURE AI SEARCH QUERY REWRITING COMPARISON")
    logger.info("=" * 70)
    logger.info(f"Index: {index}")
    logger.info("")
    
    results_summary = {
        "natural_language": {"improved": 0, "same": 0, "worse": 0},
        "historical_term": {"improved": 0, "same": 0, "worse": 0},
        "complex": {"improved": 0, "same": 0, "worse": 0},
        "typos": {"improved": 0, "same": 0, "worse": 0},
    }
    
    async with SearchClient(endpoint, index, cred) as client:
        for tc in TEST_CASES:
            logger.info(f"\nQuery: '{tc.query}'")
            logger.info(f"Category: {tc.category} | {tc.description}")
            
            # Search without rewriting
            without = await search_with_options(client, tc.query, use_rewriting=False)
            without_count, without_found = check_topics_found(without, tc.expected_topics)
            
            # Search with rewriting
            with_rewrite = await search_with_options(client, tc.query, use_rewriting=True)
            with_count, with_found = check_topics_found(with_rewrite, tc.expected_topics)
            
            # Compare
            if with_count > without_count:
                status = "✅ IMPROVED"
                results_summary[tc.category]["improved"] += 1
            elif with_count < without_count:
                status = "❌ WORSE"
                results_summary[tc.category]["worse"] += 1
            else:
                status = "➡️ SAME"
                results_summary[tc.category]["same"] += 1
            
            logger.info(f"  Without rewriting: {without_count}/{len(tc.expected_topics)} topics | {without_found}")
            logger.info(f"  With rewriting:    {with_count}/{len(tc.expected_topics)} topics | {with_found}")
            logger.info(f"  Result: {status}")
    
    # Print summary
    logger.info("\n" + "=" * 70)
    logger.info("SUMMARY BY CATEGORY")
    logger.info("=" * 70)
    
    total_improved = 0
    total_same = 0
    total_worse = 0
    
    for category, stats in results_summary.items():
        total = stats["improved"] + stats["same"] + stats["worse"]
        if total > 0:
            logger.info(f"{category:20} | Improved: {stats['improved']} | Same: {stats['same']} | Worse: {stats['worse']}")
            total_improved += stats["improved"]
            total_same += stats["same"]
            total_worse += stats["worse"]
    
    logger.info("-" * 70)
    total = total_improved + total_same + total_worse
    logger.info(f"{'TOTAL':20} | Improved: {total_improved} | Same: {total_same} | Worse: {total_worse}")
    
    improvement_rate = total_improved / total * 100 if total > 0 else 0
    logger.info(f"\nImprovement rate: {improvement_rate:.1f}%")
    
    if total_improved > total_worse:
        logger.info("\n✅ RECOMMENDATION: Query rewriting provides value for natural language queries")
    elif total_improved < total_worse:
        logger.info("\n⚠️ RECOMMENDATION: Query rewriting may degrade results - investigate further")
    else:
        logger.info("\n➡️ RECOMMENDATION: Query rewriting provides minimal additional value")
        logger.info("   The synonym map is already handling terminology well.")


if __name__ == "__main__":
    asyncio.run(run_comparison())
