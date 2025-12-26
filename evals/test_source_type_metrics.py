#!/usr/bin/env python3
"""
Source-Type Specific Metrics Test
==================================
Tests that the evaluation metrics work correctly when applied to 
different source types (CPR, PD, Court Guide).

CUSTOM: This file is part of the merge-safe customizations for legal RAG.
"""

import json
import sys
from pathlib import Path

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent))

from evaluate import (
    CPR_RULE_REGEX,
    PRACTICE_DIRECTION_REGEX,
    COURT_GUIDE_REGEX,
    CASE_CITATION_REGEX,
    STATUTE_REGEX,
    StatuteCitationAccuracyMetric,
    CaseLawCitationMetric,
    LegalTerminologyMetric,
    CitationFormatComplianceMetric,
    PrecedentMatchingMetric,
)


def load_ground_truth():
    """Load ground truth and group by source type."""
    gt_path = Path(__file__).parent / "ground_truth_cpr.jsonl"
    entries = []
    with open(gt_path) as f:
        for line in f:
            if line.strip():
                entries.append(json.loads(line))
    return entries


def test_cpr_questions():
    """Test that CPR questions correctly identify CPR references."""
    entries = load_ground_truth()
    cpr_entries = [e for e in entries if e.get("source_type") == "CPR"]
    
    print(f"\n=== Testing CPR Questions ({len(cpr_entries)} entries) ===")
    
    for entry in cpr_entries:
        question = entry["question"]
        truth = entry["truth"]
        
        # Check for CPR references in truth
        cpr_matches = CPR_RULE_REGEX.findall(truth)
        
        print(f"\nQ: {question[:60]}...")
        print(f"  CPR refs found: {len(cpr_matches)}")
        if cpr_matches:
            for match in cpr_matches[:3]:
                print(f"    - Part {match[0]}" + (f".{match[1]}" if match[1] else ""))
        
        # Simulate a response
        mock_response = f"According to CPR Part 44, {truth}"
        metric_fn = StatuteCitationAccuracyMetric.evaluator_fn()
        result = metric_fn(response=mock_response, ground_truth=truth)
        print(f"  Statute Citation Accuracy: {result['statute_citation_accuracy']}")


def test_pd_questions():
    """Test that PD questions correctly identify Practice Direction references."""
    entries = load_ground_truth()
    pd_entries = [e for e in entries if e.get("source_type") == "PD"]
    
    print(f"\n=== Testing Practice Direction Questions ({len(pd_entries)} entries) ===")
    
    for entry in pd_entries:
        question = entry["question"]
        truth = entry["truth"]
        
        # Check for PD references in truth
        pd_matches = PRACTICE_DIRECTION_REGEX.findall(truth)
        
        print(f"\nQ: {question[:60]}...")
        print(f"  PD refs found: {len(pd_matches)}")
        if pd_matches:
            for match in pd_matches[:3]:
                print(f"    - PD {match}")
        
        # Simulate a response
        mock_response = truth
        metric_fn = StatuteCitationAccuracyMetric.evaluator_fn()
        result = metric_fn(response=mock_response, ground_truth=truth)
        print(f"  Statute Citation Accuracy: {result['statute_citation_accuracy']}")


def test_court_guide_questions():
    """Test that Court Guide questions correctly identify guide references."""
    entries = load_ground_truth()
    cg_entries = [e for e in entries if e.get("source_type") == "Court Guide"]
    
    print(f"\n=== Testing Court Guide Questions ({len(cg_entries)} entries) ===")
    
    # Group by category
    by_category = {}
    for entry in cg_entries:
        cat = entry.get("category", "Unknown")
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(entry)
    
    for category, entries in by_category.items():
        print(f"\n--- {category} ({len(entries)} questions) ---")
        
        for entry in entries[:2]:  # Show first 2 per category
            question = entry["question"]
            truth = entry["truth"]
            
            # Check for court guide references
            cg_matches = COURT_GUIDE_REGEX.findall(truth)
            
            print(f"\nQ: {question[:60]}...")
            print(f"  Court Guide refs: {len(cg_matches)}")
            
            # Check for legal terminology
            metric_fn = LegalTerminologyMetric.evaluator_fn()
            result = metric_fn(response=truth, ground_truth=truth)
            print(f"  Legal Terminology: {result['legal_terminology_accuracy']}")


def test_metric_applicability():
    """Test which metrics are most applicable per source type."""
    entries = load_ground_truth()
    
    print("\n=== Metric Applicability by Source Type ===")
    
    source_types = ["CPR", "PD", "Court Guide"]
    
    for st in source_types:
        st_entries = [e for e in entries if e.get("source_type") == st]
        print(f"\n{st} ({len(st_entries)} entries):")
        
        # Check which references are present
        cpr_count = 0
        pd_count = 0
        cg_count = 0
        statute_count = 0
        case_count = 0
        
        for entry in st_entries:
            truth = entry["truth"]
            if CPR_RULE_REGEX.search(truth):
                cpr_count += 1
            if PRACTICE_DIRECTION_REGEX.search(truth):
                pd_count += 1
            if COURT_GUIDE_REGEX.search(truth):
                cg_count += 1
            if STATUTE_REGEX.search(truth):
                statute_count += 1
            if CASE_CITATION_REGEX.search(truth):
                case_count += 1
        
        print(f"  CPR references: {cpr_count}/{len(st_entries)}")
        print(f"  PD references: {pd_count}/{len(st_entries)}")
        print(f"  Court Guide refs: {cg_count}/{len(st_entries)}")
        print(f"  Statute refs: {statute_count}/{len(st_entries)}")
        print(f"  Case citations: {case_count}/{len(st_entries)}")


def test_citation_format_compliance():
    """Test citation format compliance across all entries."""
    entries = load_ground_truth()
    
    print("\n=== Citation Format Compliance Test ===")
    
    metric_fn = CitationFormatComplianceMetric.evaluator_fn()
    
    for st in ["CPR", "PD", "Court Guide"]:
        st_entries = [e for e in entries if e.get("source_type") == st]
        
        compliant = 0
        neutral = 0
        malformed = 0
        
        for entry in st_entries:
            result = metric_fn(response=entry["truth"])
            score = result["citation_format_compliance"]
            if score == 1.0:
                compliant += 1
            elif score == 0.5:
                neutral += 1
            else:
                malformed += 1
        
        print(f"\n{st}:")
        print(f"  Compliant: {compliant}")
        print(f"  Neutral (no citations): {neutral}")
        print(f"  Malformed: {malformed}")


def test_precedent_matching():
    """Test precedent matching with document references."""
    entries = load_ground_truth()
    
    print("\n=== Precedent Matching Test ===")
    
    metric_fn = PrecedentMatchingMetric.evaluator_fn()
    
    # Test with perfect match
    entry = entries[0]
    result = metric_fn(response=entry["truth"], ground_truth=entry["truth"])
    print(f"\nPerfect match test: {result['precedent_matching']}")
    
    # Test with partial match
    result = metric_fn(
        response="According to [Commercial Court Guide.pdf], the procedure is...",
        ground_truth="The Commercial Court Guide [Commercial Court Guide.pdf] states..."
    )
    print(f"Partial match test: {result['precedent_matching']}")
    
    # Test with no match
    result = metric_fn(
        response="The response mentions nothing relevant.",
        ground_truth="According to [TCC Guide.pdf#page=5], the procedure is..."
    )
    print(f"No match test: {result['precedent_matching']}")


def main():
    print("=" * 60)
    print("Source-Type Specific Metrics Test")
    print("=" * 60)
    
    test_cpr_questions()
    test_pd_questions()
    test_court_guide_questions()
    test_metric_applicability()
    test_citation_format_compliance()
    test_precedent_matching()
    
    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
