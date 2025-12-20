#!/usr/bin/env python3
"""Quick test to verify category filtering is working."""

import json
import requests
import sys

def test_single_query():
    """Test a single query to verify backend is responding correctly."""
    backend_url = "http://localhost:50505/chat"
    
    # Simple test query
    payload = {
        "messages": [{"role": "user", "content": "What is CPR Part 1?"}],
        "context": {"overrides": {}}
    }
    
    print("Testing backend with simple query...")
    print(f"Query: {payload['messages'][0]['content']}")
    print("Waiting for response (60s timeout)...\n")
    
    try:
        response = requests.post(backend_url, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        
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
        
        # Print results
        print("✅ SUCCESS - Backend responded")
        print(f"Response length: {len(data.get('message', {}).get('content', ''))} chars")
        print(f"Retrieved from {len(data_points)} documents")
        print(f"Categories: {', '.join(categories) if categories else 'None found'}")
        
        # Show first few documents
        if data_points:
            print("\nFirst 3 documents:")
            for i, doc in enumerate(data_points[:3], 1):
                print(f"{i}. Category: {doc.get('category', 'N/A')}")
                print(f"   Source: {doc.get('sourcefile', 'N/A')}")
                print(f"   Content: {doc.get('content', '')[:80]}...")
        
        return True
        
    except requests.Timeout:
        print("❌ FAILED - Backend timed out after 60 seconds")
        return False
    except requests.RequestException as e:
        print(f"❌ FAILED - Request error: {e}")
        return False
    except Exception as e:
        print(f"❌ FAILED - Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_single_query()
    sys.exit(0 if success else 1)
