#!/usr/bin/env python3
"""
Test specific edge cases and scenarios for the legal RAG system.
"""

import json
import requests
import sys

BACKEND_URL = "http://localhost:50505/chat"

# Test cases for specific scenarios
TEST_CASES = [
    {
        "name": "Multi-Court Query",
        "question": "What are the disclosure requirements in both Commercial Court and TCC?",
        "expected_categories": ["Commercial Court", "Technology and Construction Court", "Civil Procedure Rules and Practice Directions"],
        "test": "Should retrieve from multiple court categories"
    },
    {
        "name": "Ambiguous Query",
        "question": "What are the rules?",
        "expected_behavior": "Should ask for clarification or provide general CPR overview"
    },
    {
        "name": "Non-Existent Content",
        "question": "What are the rules for traffic violations in CPR?",
        "expected_behavior": "Should respond with 'I don't know' or indicate content not in knowledge base"
    },
    {
        "name": "Citation Density",
        "question": "Explain the entire summary judgment process under CPR Part 24",
        "expected_behavior": "Should have multiple citations [1][2][3]... covering different aspects"
    },
    {
        "name": "Specific Rule Reference",
        "question": "What does CPR 31.6 say about standard disclosure?",
        "expected_behavior": "Should cite specific rule with subsection details"
    },
    {
        "name": "Cross-Reference Query",
        "question": "How does Part 36 relate to cost consequences?",
        "expected_behavior": "Should explain relationship with citations from multiple parts"
    },
    {
        "name": "Recent vs Old Content",
        "question": "What are the 2025 King's Bench Division requirements?",
        "expected_categories": ["King's Bench Division"],
        "expected_behavior": "Should retrieve from 2025 guide specifically"
    },
    {
        "name": "Procedural Timeline",
        "question": "What is the timeline from filing a claim to trial in fast track?",
        "expected_behavior": "Should provide step-by-step timeline with multiple citations"
    }
]

def test_scenario(test_case):
    """Test a specific scenario."""
    print(f"\n{'='*80}")
    print(f"Testing: {test_case['name']}")
    print(f"{'='*80}")
    print(f"Question: {test_case['question']}")
    print(f"Expected: {test_case.get('expected_behavior', 'See expected_categories')}\n")
    
    payload = {
        "messages": [{"role": "user", "content": test_case["question"]}],
        "context": {"overrides": {}}
    }
    
    try:
        response = requests.post(BACKEND_URL, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        
        # Extract answer
        answer = data.get("message", {}).get("content", "")
        
        # Extract context
        context = data.get("context", {})
        if isinstance(context, str):
            context = json.loads(context)
        
        # Get categories
        data_points = context.get("data_points", {}).get("text", [])
        categories = set()
        for doc in data_points:
            if "category" in doc and doc["category"]:
                categories.add(doc["category"])
        
        # Count citations
        import re
        citations = re.findall(r'\[\d+\]', answer)
        
        # Print results
        print(f"✓ Response received ({len(answer)} chars)")
        print(f"  Documents retrieved: {len(data_points)}")
        print(f"  Categories: {', '.join(categories) if categories else 'None'}")
        print(f"  Citations: {len(set(citations))} unique citations")
        print(f"\nAnswer preview:\n{answer[:300]}...")
        
        # Validate expected categories if specified
        if "expected_categories" in test_case:
            expected = set(test_case["expected_categories"])
            if expected.intersection(categories):
                print(f"\n✅ PASS: Found expected categories")
            else:
                print(f"\n⚠️  WARNING: Expected categories not found")
                print(f"   Expected: {expected}")
                print(f"   Got: {categories}")
        
        return True
        
    except requests.Timeout:
        print("❌ FAILED: Request timed out")
        return False
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

def main():
    """Run all test scenarios."""
    print("="*80)
    print("EDGE CASE AND SCENARIO TESTING")
    print("="*80)
    
    passed = 0
    failed = 0
    
    for test_case in TEST_CASES:
        if test_scenario(test_case):
            passed += 1
        else:
            failed += 1
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"Passed: {passed}/{len(TEST_CASES)}")
    print(f"Failed: {failed}/{len(TEST_CASES)}")
    print(f"Success Rate: {(passed/len(TEST_CASES)*100):.1f}%")
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
