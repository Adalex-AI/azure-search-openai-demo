#!/usr/bin/env python3
"""Convert practical_test_questions.json to ground_truth.jsonl format"""
import json

# Load practical questions
with open('evals/practical_test_questions.json', 'r') as f:
    data = json.load(f)

# Convert to ground truth format (questions only, no truth answers since we'll compare to actual responses)
ground_truth_entries = []

for category_name, category_data in data['categories'].items():
    for question in category_data['questions']:
        # For evaluation without pre-defined answers, we just need the question
        # The evaluation metrics will compare the response to the actual retrieved content
        ground_truth_entries.append({
            "question": question,
            "truth": ""  # Empty truth means we'll evaluate based on retrieval quality only
        })

# Write to ground_truth.jsonl
with open('evals/ground_truth_practical.jsonl', 'w') as f:
    for entry in ground_truth_entries:
        f.write(json.dumps(entry) + '\n')

print(f"✅ Created ground_truth_practical.jsonl with {len(ground_truth_entries)} questions")
