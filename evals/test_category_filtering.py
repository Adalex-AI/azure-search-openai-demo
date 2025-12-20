#!/usr/bin/env python3
"""
Test category filtering and retrieval quality.
Validates that when users specify a court category, the system retrieves
documents from the correct category.
"""

import json
import requests
from typing import List, Dict

# Test cases organized by expected category
CATEGORY_TESTS = {
    "Commercial Court": [
        {
            "question": "What are the Commercial Court CMC requirements?",
            "expected_categories": ["Commercial Court", "Civil Procedure Rules and Practice Directions"],
            "must_not_include": ["Circuit Commercial Court", "Technology and Construction Court"]
        },
        {
            "question": "What is the Commercial Court approach to case management bundles?",
            "expected_categories": ["Commercial Court"],
            "must_not_include": ["Patents Court", "Chancery Division"]
        }
    ],
    "Circuit Commercial Court": [
        {
            "question": "What disclosure requirements apply in Circuit Commercial Court?",
            "expected_categories": ["Circuit Commercial Court", "Civil Procedure Rules and Practice Directions"],
            "must_not_include": ["Commercial Court", "King's Bench Division"]
        },
        {
            "question": "When must I file directions questionnaire in Circuit Commercial Court?",
            "expected_categories": ["Circuit Commercial Court", "Civil Procedure Rules and Practice Directions"],
            "must_not_include": ["Technology and Construction Court"]
        }
    ],
    "Technology and Construction Court": [
        {
            "question": "What are TCC expert evidence requirements?",
            "expected_categories": ["Technology and Construction Court", "Civil Procedure Rules and Practice Directions"],
            "must_not_include": ["Commercial Court", "Chancery Division"]
        }
    ],
    "CPR General": [
        {
            "question": "What is the limitation period for breach of contract?",
            "expected_categories": ["Civil Procedure Rules and Practice Directions"],
            "may_include_any": True  # General CPR question may pull from any guide
        },
        {
            "question": "When must I serve my defence under CPR Part 15?",
            "expected_categories": ["Civil Procedure Rules and Practice Directions"],
            "may_include_any": True
        }
    ]
}

def test_category_filtering(backend_url: str = "http://localhost:50505/chat"):
    """
    Test that category filtering returns documents from correct courts.
    
    Args:
        backend_url: URL of the backend /chat endpoint
    """
    results = {
        "total_tests": 0,
        "passed": 0,
        "failed": 0,
        "failures": []
    }
    
    for expected_category, test_cases in CATEGORY_TESTS.items():
        print(f"\n{'='*80}")
        print(f"Testing: {expected_category}")
        print(f"{'='*80}")
        
        for test_case in test_cases:
            results["total_tests"] += 1
            question = test_case["question"]
            
            # Send request to backend
            payload = {
                "messages": [{"role": "user", "content": question}],
                "context": {"overrides": {}}
            }
            
            try:
                print(f"   Sending query: {question[:80]}...")
                response = requests.post(backend_url, json=payload, timeout=60)
                print(f"   Got response (status {response.status_code})")
                response.raise_for_status()
                data = response.json()
                
                # Extract categories from retrieved documents
                context = data.get("context", {})
                if isinstance(context, str):
                    context = json.loads(context)
                
                retrieved_categories = set()
                data_points = context.get("data_points", {}).get("text", [])
                for doc in data_points:
                    if "category" in doc and doc["category"]:
                        retrieved_categories.add(doc["category"])
                
                # Validate categories
                passed = True
                failure_reason = []
                
                # Check expected categories are present
                expected = test_case.get("expected_categories", [])
                for exp_cat in expected:
                    if exp_cat not in retrieved_categories:
                        passed = False
                        failure_reason.append(f"Missing expected category: {exp_cat}")
                
                # Check prohibited categories are absent
                if not test_case.get("may_include_any", False):
                    prohibited = test_case.get("must_not_include", [])
                    for prohib_cat in prohibited:
                        if prohib_cat in retrieved_categories:
                            passed = False
                            failure_reason.append(f"Found prohibited category: {prohib_cat}")
                
                # Record result
                if passed:
                    results["passed"] += 1
                    print(f"✅ PASS: {question}")
                    print(f"   Retrieved from: {', '.join(retrieved_categories)}")
                else:
                    results["failed"] += 1
                    results["failures"].append({
                        "question": question,
                        "expected": expected,
                        "retrieved": list(retrieved_categories),
                        "reason": failure_reason
                    })
                    print(f"❌ FAIL: {question}")
                    print(f"   Expected: {expected}")
                    print(f"   Retrieved from: {', '.join(retrieved_categories)}")
                    print(f"   Reason: {'; '.join(failure_reason)}")
                    
            except Exception as e:
                results["failed"] += 1
                results["failures"].append({
                    "question": question,
                    "error": str(e)
                })
                print(f"❌ ERROR: {question}")
                print(f"   Error: {str(e)}")
    
    # Print summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"Total tests: {results['total_tests']}")
    print(f"Passed: {results['passed']} ({results['passed']/results['total_tests']*100:.1f}%)")
    print(f"Failed: {results['failed']} ({results['failed']/results['total_tests']*100:.1f}%)")
    
    if results["failures"]:
        print(f"\nFailures:")
        for i, failure in enumerate(results["failures"], 1):
            print(f"\n{i}. {failure.get('question', 'Unknown')}")
            if "reason" in failure:
                print(f"   Reasons: {'; '.join(failure['reason'])}")
            if "error" in failure:
                print(f"   Error: {failure['error']}")
    
    return results

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Test category filtering in RAG system")
    parser.add_argument("--url", default="http://localhost:50505/chat", help="Backend URL")
    args = parser.parse_args()
    
    results = test_category_filtering(args.url)
    
    # Exit with error code if any tests failed
    exit(0 if results["failed"] == 0 else 1)
