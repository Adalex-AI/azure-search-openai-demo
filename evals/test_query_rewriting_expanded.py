#!/usr/bin/env python3
"""
Expanded Query Rewriting Evaluation

Adds a wider set of queries to validate whether Azure semantic query
rewriting improves search results for the legal RAG dataset.

Usage:
    python evals/test_query_rewriting_expanded.py
"""

import os
import sys
import asyncio
import logging
from dataclasses import dataclass

# allow importing helper that loads azd env
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from load_azd_env import load_azd_env

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class TestCase:
    query: str
    description: str
    category: str
    expected_topics: list[str]


# A broader set of test cases covering more edge-cases and paraphrases
TEST_CASES = [
    # Natural language paraphrases and conversational queries
    TestCase(
        query="how can i stop someone selling property while the case is pending",
        description="Paraphrase of freezing/order request",
        category="natural_language",
        expected_topics=["freezing", "injunction", "order", "assets"],
    ),
    TestCase(
        query="can i get money from the other side before trial finishes",
        description="Paraphrase of interim payments",
        category="natural_language",
        expected_topics=["interim payment", "Part 25", "security for costs"],
    ),
    TestCase(
        query="urgent court order to pause eviction",
        description="Interim relief for eviction context",
        category="natural_language",
        expected_topics=["injunction", "interim", "possession"],
    ),
    TestCase(
        query="what's the process to compel the other side to disclose emails",
        description="Disclosure: compel production of documents",
        category="natural_language",
        expected_topics=["disclosure", "Part 31", "electronic discovery"],
    ),

    # Short legal jargon that synonym map should cover
    TestCase(
        query="mareva",
        description="Historic term single token",
        category="historical_term",
        expected_topics=["freezing", "injunction"],
    ),
    TestCase(
        query="discovery",
        description="Single token covered by synonyms",
        category="historical_term",
        expected_topics=["disclosure", "Part 31"],
    ),

    # Ambiguous or multi-topic queries
    TestCase(
        query="claim for breach and interim relief",
        description="Multi-topic: claim + interim relief",
        category="complex",
        expected_topics=["claim", "interim", "injunction", "statement of case"],
    ),
    TestCase(
        query="ignoring service of proceedings consequences",
        description="Default judgment and service",
        category="complex",
        expected_topics=["default", "judgment", "service", "acknowledgment"],
    ),

    # Misspellings and transpositions beyond trivial typos
    TestCase(
        query="frzing order to stop sale of aset",
        description="Misspellings for freezing order",
        category="typos",
        expected_topics=["freezing", "injunction", "assets"],
    ),
    TestCase(
        query="disc losure of emal attachments",
        description="Misspelt disclosure + email",
        category="typos",
        expected_topics=["disclosure", "documents", "email", "attachments"],
    ),

    # Long-form and verbose queries where rewriting could help
    TestCase(
        query=(
            "i need to know the steps and forms required to get an interim injunction "
            "in order to preserve assets while proceedings continue"
        ),
        description="Long-form natural language freezing injunction",
        category="natural_language",
        expected_topics=["injunction", "freezing", "interim", "order"],
    ),
    TestCase(
        query=(
            "if the defendant does not respond to the claim form what remedies are available "
            "to the claimant"
        ),
        description="Verbose default judgment + remedies",
        category="complex",
        expected_topics=["default", "judgment", "remedies", "relief"],
    ),

    # Edge: abbreviations and legal shorthand
    TestCase(
        query="CPR Part 31 when to disclose",
        description="Shorthand referencing procedural rules",
        category="historical_term",
        expected_topics=["Part 31", "disclosure", "CPR"],
    ),
    TestCase(
        query="what is the test for strike out under CPR 3.4",
        description="Reference to strike-out rule",
        category="historical_term",
        expected_topics=["strike out", "CPR 3.4", "strike-out"],
    ),

    # Query that previously worsened results in the short set
    TestCase(
        query="asking for money before trial ends",
        description="Re-run previously WORSE case",
        category="natural_language",
        expected_topics=["interim payment", "Part 25"],
    ),
]


async def search_with_options(client, query: str, use_rewriting: bool) -> list[dict]:
    from azure.search.documents.models import QueryType

    try:
        results = await client.search(
            search_text=query,
            top=10,
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
                "content": r.get("content", "")[:1000],
                "score": r.get("@search.score", 0),
            })
        return docs
    except Exception as e:
        logger.error(f"Search error: {e}")
        return []


def check_topics_found(results: list[dict], expected_topics: list[str]) -> tuple[int, list[str]]:
    combined_text = " ".join([r.get("content", "") + " " + r.get("sourcepage", "") for r in results]).lower()
    found = [t for t in expected_topics if t.lower() in combined_text]
    return len(found), found


async def run_expanded():
    from azure.identity import AzureDeveloperCliCredential
    from azure.search.documents.aio import SearchClient

    load_azd_env()

    endpoint = f'https://{os.environ["AZURE_SEARCH_SERVICE"]}.search.windows.net'
    index = os.environ['AZURE_SEARCH_INDEX']
    cred = AzureDeveloperCliCredential(tenant_id=os.environ.get('AZURE_TENANT_ID'))

    logger.info("=" * 70)
    logger.info("AZURE AI SEARCH QUERY REWRITING - EXPANDED COMPARISON")
    logger.info("=" * 70)
    logger.info(f"Index: {index}")

    results_summary = {}
    for tc in TEST_CASES:
        results_summary.setdefault(tc.category, {"improved": 0, "same": 0, "worse": 0, "total": 0})

    async with SearchClient(endpoint, index, cred) as client:
        for tc in TEST_CASES:
            logger.info(f"\nQuery: '{tc.query}'")
            logger.info(f"Category: {tc.category} | {tc.description}")

            without = await search_with_options(client, tc.query, use_rewriting=False)
            without_count, without_found = check_topics_found(without, tc.expected_topics)

            with_rewrite = await search_with_options(client, tc.query, use_rewriting=True)
            with_count, with_found = check_topics_found(with_rewrite, tc.expected_topics)

            if with_count > without_count:
                status = "IMPROVED"
                results_summary[tc.category]["improved"] += 1
            elif with_count < without_count:
                status = "WORSE"
                results_summary[tc.category]["worse"] += 1
            else:
                status = "SAME"
                results_summary[tc.category]["same"] += 1

            results_summary[tc.category]["total"] += 1

            logger.info(f"  Without rewriting: {without_count}/{len(tc.expected_topics)} topics | {without_found}")
            logger.info(f"  With rewriting:    {with_count}/{len(tc.expected_topics)} topics | {with_found}")
            logger.info(f"  Result: {status}")

    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("EXPANDED SUMMARY BY CATEGORY")
    logger.info("=" * 70)

    total_improved = total_same = total_worse = total = 0
    for cat, stats in results_summary.items():
        logger.info(f"{cat:20} | Improved: {stats['improved']} | Same: {stats['same']} | Worse: {stats['worse']} | Total: {stats['total']}")
        total_improved += stats['improved']
        total_same += stats['same']
        total_worse += stats['worse']
        total += stats['total']

    logger.info("-" * 70)
    logger.info(f"{'TOTAL':20} | Improved: {total_improved} | Same: {total_same} | Worse: {total_worse} | Total: {total}")

    improvement_rate = (total_improved / total * 100) if total > 0 else 0
    logger.info(f"\nImprovement rate: {improvement_rate:.1f}%")

    if total_improved > total_worse:
        logger.info("\n✅ RECOMMENDATION: Query rewriting provides net improvement on expanded set")
    elif total_improved < total_worse:
        logger.info("\n⚠️ RECOMMENDATION: Query rewriting may degrade results on expanded set")
    else:
        logger.info("\n➡️ RECOMMENDATION: Query rewriting provides minimal net change on expanded set")


if __name__ == '__main__':
    asyncio.run(run_expanded())
