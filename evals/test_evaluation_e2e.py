"""
End-to-end test of evaluation pipeline with synthetic data.
Validates all 5 custom metrics work correctly without requiring backend.
"""

import json
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Import the custom metrics
from evaluate import (
    any_citation,
    citations_matched,
    citation_format_compliance,
    subsection_extraction_accuracy,
    category_coverage
)

# Mock responses with various citation patterns
test_cases = [
    {
        "name": "Perfect Response - All metrics pass",
        "response": """The key provisions of CPR Part 31 regarding disclosure are:

**Standard Disclosure** [1]
Under CPR 31.6, standard disclosure requires each party to disclose documents on which it relies [2], documents which adversely affect its own case or another party's case, or support another party's case. This is covered in CPR 31.1.

**Timing of Disclosure** [3]
Disclosure must generally occur within 14 days after the CMC unless the court orders otherwise under CPR 31.5.""",
        "context": {
            "data_points": {
                "text": [
                    {
                        "content": "31.1 Scope of Part. CPR Part 31 sets out rules about disclosure and inspection...",
                        "sourcepage": "CPR Part 31.1",
                        "sourcefile": "Civil_Procedure_Rules_Part_31.pdf",
                        "category": "Civil Procedure Rules"
                    },
                    {
                        "content": "31.6 Standard disclosure requires a party to disclose documents on which he relies...",
                        "sourcepage": "CPR Part 31.6",
                        "sourcefile": "Civil_Procedure_Rules_Part_31.pdf",
                        "category": "Civil Procedure Rules"
                    },
                    {
                        "content": "31.5 Timing. Disclosure must occur within 14 days after case management conference...",
                        "sourcepage": "CPR Part 31.5",
                        "sourcefile": "Civil_Procedure_Rules_Part_31.pdf",
                        "category": "Civil Procedure Rules"
                    }
                ]
            }
        },
        "expected": {
            "any_citation": True,
            "citations_matched": 1.0,  # 3/3 = 100%
            "citation_format_compliance": True,
            "subsection_extraction": True,  # Has 31.6, 31.1, 31.5
            "category_coverage": True  # Has Civil Procedure Rules
        }
    },
    {
        "name": "Format Violation - Comma in citations",
        "response": """CPR Part 31 covers disclosure [1, 2, 3] and inspection rights.""",
        "context": {
            "data_points": {
                "text": [
                    {"content": "31.1 test", "sourcepage": "CPR 31.1", "sourcefile": "test.pdf", "category": "Civil Procedure Rules"}
                ]
            }
        },
        "expected": {
            "any_citation": True,  # Still has citation pattern
            "citations_matched": 1.0,  # 1/1 = 100% (only [1] valid)
            "citation_format_compliance": False,  # Has [1, 2, 3] violation
            "subsection_extraction": True,  # Has 31
            "category_coverage": True
        }
    },
    {
        "name": "Missing Citations",
        "response": """CPR Part 31 requires disclosure within 14 days. No citations provided.""",
        "context": {
            "data_points": {
                "text": [
                    {"content": "test", "sourcepage": "CPR 31.1", "sourcefile": "test.pdf", "category": "Civil Procedure Rules"}
                ]
            }
        },
        "expected": {
            "any_citation": False,  # No citations
            "citations_matched": 0.0,  # 0/1 = 0%
            "citation_format_compliance": True,  # No violations (no citations to violate)
            "subsection_extraction": True,  # Has 31
            "category_coverage": True
        }
    },
    {
        "name": "Multi-category Coverage",
        "response": """Commercial Court procedures [1] differ from Patents Court [2] and require CPR Part 58.1 compliance.""",
        "context": {
            "data_points": {
                "text": [
                    {"content": "test", "sourcepage": "CPR 58.1", "sourcefile": "commercial.pdf", "category": "Commercial Court"},
                    {"content": "test", "sourcepage": "Patents 1", "sourcefile": "patents.pdf", "category": "Patents Court"}
                ]
            }
        },
        "expected": {
            "any_citation": True,
            "citations_matched": 1.0,  # 2/2 = 100%
            "citation_format_compliance": True,
            "subsection_extraction": True,  # Has 58.1
            "category_coverage": True  # Multiple categories
        }
    }
]

print("=" * 70)
print("END-TO-END EVALUATION TEST WITH CUSTOM METRICS")
print("=" * 70)

passed = 0
failed = 0

for i, test_case in enumerate(test_cases, 1):
    print(f"\n{'=' * 70}")
    print(f"TEST CASE {i}: {test_case['name']}")
    print("=" * 70)
    
    response = test_case['response']
    context = test_case['context']
    expected = test_case['expected']
    
    # Test 1: AnyCitationMetric
    print("\n1. AnyCitationMetric")
    result = any_citation(response, context)
    print(f"   Result: {result}")
    print(f"   Expected: {expected['any_citation']}")
    if result == expected['any_citation']:
        print("   ✓ PASS")
        passed += 1
    else:
        print("   ✗ FAIL")
        failed += 1
    
    # Test 2: CitationsMatchedMetric
    print("\n2. CitationsMatchedMetric")
    result = citations_matched(response, context)
    print(f"   Result: {result:.2%}")
    print(f"   Expected: {expected['citations_matched']:.2%}")
    if abs(result - expected['citations_matched']) < 0.01:  # Allow 1% tolerance
        print("   ✓ PASS")
        passed += 1
    else:
        print("   ✗ FAIL")
        failed += 1
    
    # Test 3: CitationFormatComplianceMetric
    print("\n3. CitationFormatComplianceMetric")
    result = citation_format_compliance(response, context)
    print(f"   Result: {result}")
    print(f"   Expected: {expected['citation_format_compliance']}")
    if result == expected['citation_format_compliance']:
        print("   ✓ PASS")
        passed += 1
    else:
        print("   ✗ FAIL")
        failed += 1
    
    # Test 4: SubsectionExtractionMetric
    print("\n4. SubsectionExtractionMetric")
    result = subsection_extraction_accuracy(response, context)
    print(f"   Result: {result}")
    print(f"   Expected: {expected['subsection_extraction']}")
    # This is boolean for presence check
    has_subsection = result > 0 if isinstance(result, (int, float)) else bool(result)
    if has_subsection == expected['subsection_extraction']:
        print("   ✓ PASS")
        passed += 1
    else:
        print("   ✗ FAIL")
        failed += 1
    
    # Test 5: CategoryCoverageMetric
    print("\n5. CategoryCoverageMetric")
    result = category_coverage(response, context)
    print(f"   Result: {result}")
    print(f"   Expected: {expected['category_coverage']}")
    has_category = result > 0 if isinstance(result, (int, float)) else bool(result)
    if has_category == expected['category_coverage']:
        print("   ✓ PASS")
        passed += 1
    else:
        print("   ✗ FAIL")
        failed += 1

print("\n" + "=" * 70)
print("FINAL RESULTS")
print("=" * 70)
print(f"Total Tests: {passed + failed}")
print(f"Passed: {passed} ✓")
print(f"Failed: {failed} ✗")
print(f"Success Rate: {passed / (passed + failed) * 100:.1f}%")

if failed == 0:
    print("\n🎉 ALL TESTS PASSED! All 5 custom metrics working correctly.")
    print("✓ Ready to run full evaluation once backend responds.")
else:
    print(f"\n⚠️  {failed} test(s) failed. Review metric implementations.")
    sys.exit(1)
