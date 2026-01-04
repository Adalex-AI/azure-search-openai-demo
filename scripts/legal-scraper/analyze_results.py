import json
from collections import Counter

with open("data/legal-scraper/processed/comprehensive_test_results.json") as f:
    results = json.load(f)

print(f"Total Local: {results['total_local']}")
print(f"Found: {results['found']}")
print(f"Not Found: {results['not_found']}")
print(f"Mismatch: {results['mismatch']}")

not_found_files = [item['sourcefile'] for item in results['details']['not_found']]
mismatch_files = [item['sourcefile'] for item in results['details']['mismatch']]

print("\n--- Top 20 Not Found Sourcefiles ---")
for name, count in Counter(not_found_files).most_common(20):
    print(f"{name}: {count}")

print("\n--- Top 20 Mismatch Sourcefiles ---")
for name, count in Counter(mismatch_files).most_common(20):
    print(f"{name}: {count}")
