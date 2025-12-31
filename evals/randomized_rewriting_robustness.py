#!/usr/bin/env python3
"""
Randomized evaluation for query rewriting robustness.

Approach:
 - Sample questions from `evals/ground_truth_cpr.jsonl` (or all if fewer than N)
 - For each question, obtain a baseline top-5 result set using the original question (no rewriting)
 - Generate several perturbed query variants (paraphrase, typo, shuffle, long-form)
 - For each variant, run search with and without query rewriting and check overlap with baseline top-5
 - Aggregate statistics: improved / same / worse for rewritten vs non-rewritten

Usage:
    python evals/randomized_rewriting_robustness.py
"""

import argparse
import os
import sys
import json
import random
import asyncio
import logging
from typing import List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from load_azd_env import load_azd_env

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def load_ground_truth(path: str) -> List[dict]:
    items = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                items.append(json.loads(line))
            except Exception:
                continue
    return items


def perturbations(question: str) -> List[str]:
    q = question.strip()
    pert = []

    # paraphrase: prepend conversational prefix
    pert.append(f"How do I {q.lower()}")

    # long-form: expand with purpose clause
    pert.append(q + " -- I need step-by-step guidance and relevant rules")

    # shuffle a subset of words (small perturbation)
    words = q.split()
    if len(words) > 4:
        w = words[:]
        i, j = random.sample(range(len(w)), 2)
        w[i], w[j] = w[j], w[i]
        pert.append(" ".join(w))
    else:
        pert.append(q + " please")

    # typo: randomly drop or swap a character in a random word
    tokens = q.split()
    idx = random.randrange(len(tokens))
    tok = list(tokens[idx])
    if len(tok) > 1:
        a = random.randrange(len(tok))
        b = a-1 if a>0 else a+1 if a < len(tok)-1 else a
        tok[a], tok[b] = tok[b], tok[a]
        tokens[idx] = "".join(tok)
    pert.append(" ".join(tokens))

    # abbreviation variant
    pert.append(q.replace("Part", "CPR Part"))

    # limit and deduplicate
    seen = set()
    out = []
    for p in pert:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


async def get_top_ids(client, query: str, use_rewriting: bool, query_rewrites: str | None, top: int = 5) -> List[str]:
    from azure.search.documents.models import QueryType
    try:
        results = await client.search(
            search_text=query,
            top=top,
            select=["id"],
            query_type=QueryType.SEMANTIC,
            semantic_configuration_name="default",
            query_language="en-GB",
            query_rewrites=query_rewrites if use_rewriting else None,
        )
        ids = []
        async for r in results:
            ids.append(r.get("id"))
        return ids
    except Exception as e:
        logger.error(f"search error for '{query}': {e}")
        return []


async def run_randomized(sample_n: int = 100, variants_per_q: int = 3, query_rewrites: str = "generative|count-5"):
    from azure.identity import AzureDeveloperCliCredential
    from azure.search.documents.aio import SearchClient

    load_azd_env()
    endpoint = f'https://{os.environ["AZURE_SEARCH_SERVICE"]}.search.windows.net'
    index = os.environ['AZURE_SEARCH_INDEX']
    cred = AzureDeveloperCliCredential(tenant_id=os.environ.get('AZURE_TENANT_ID'))

    gt = load_ground_truth(os.path.join(os.path.dirname(__file__), 'ground_truth_cpr.jsonl'))
    if not gt:
        logger.error("No ground truth found")
        return

    sample = gt if len(gt) <= sample_n else random.sample(gt, sample_n)

    stats = {"improved": 0, "same": 0, "worse": 0, "total_variants": 0}

    async with SearchClient(endpoint, index, cred) as client:
        for item in sample:
            question = item.get('question')
            if not question:
                continue

            # baseline top ids using original question (no rewriting)
            baseline_ids = await get_top_ids(client, question, use_rewriting=False, query_rewrites=query_rewrites, top=5)

            # generate variants and evaluate
            variants = perturbations(question)[:variants_per_q]
            for v in variants:
                stats['total_variants'] += 1

                ids_no = await get_top_ids(client, v, use_rewriting=False, query_rewrites=query_rewrites, top=5)
                ids_yes = await get_top_ids(client, v, use_rewriting=True, query_rewrites=query_rewrites, top=5)

                overlap_no = len(set(ids_no) & set(baseline_ids))
                overlap_yes = len(set(ids_yes) & set(baseline_ids))

                if overlap_yes > overlap_no:
                    stats['improved'] += 1
                elif overlap_yes < overlap_no:
                    stats['worse'] += 1
                else:
                    stats['same'] += 1

    # report
    logger.info("\nRandomized evaluation summary")
    logger.info(f"Sampled questions: {len(sample)}")
    logger.info(f"Variants evaluated: {stats['total_variants']}")
    logger.info(f"Improved: {stats['improved']} | Same: {stats['same']} | Worse: {stats['worse']}")
    improvement_rate = (stats['improved'] / stats['total_variants'] * 100) if stats['total_variants'] else 0
    logger.info(f"Improvement rate: {improvement_rate:.1f}%")


def parse_args():
    parser = argparse.ArgumentParser(description="Randomized query rewriting robustness test")
    parser.add_argument("--samples", type=int, default=100, help="Number of ground-truth questions to sample")
    parser.add_argument("--variants-per-question", type=int, default=3, help="Variants to generate per question")
    parser.add_argument("--query-rewrites", type=str, default="generative|count-5", help="Query rewrite parameter to pass to Azure Search")
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    asyncio.run(run_randomized(sample_n=args.samples, variants_per_q=args.variants_per_question, query_rewrites=args.query_rewrites))
