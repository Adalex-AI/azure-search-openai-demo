#!/usr/bin/env python3
"""
Test script to directly query Azure AI Search index.

This script allows you to:
1. List documents in the index
2. Search with semantic ranking
3. Test category filtering
4. Validate document metadata
5. Export sample results for evaluation ground truth

Usage:
    # Load azd environment and run
    source .venv/bin/activate
    python evals/test_search_index.py --action list
    python evals/test_search_index.py --action search --query "CPR Part 36 settlement"
    python evals/test_search_index.py --action categories
    python evals/test_search_index.py --action export --query "disclosure fast track" --output results.json
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional

# Add scripts directory to path for load_azd_env
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

try:
    from azure.identity import AzureDeveloperCliCredential, DefaultAzureCredential
    from azure.search.documents import SearchClient
    from azure.search.documents.models import VectorizedQuery
except ImportError:
    print("Error: Azure SDK not installed. Run:")
    print("  pip install azure-search-documents azure-identity")
    sys.exit(1)


def load_environment():
    """Load Azure environment variables from azd."""
    try:
        from load_azd_env import load_azd_env
        load_azd_env()
        print("✅ Loaded azd environment")
    except Exception as e:
        print(f"⚠️  Could not load azd env: {e}")
        print("   Trying to use existing environment variables...")
    
    # Verify required variables
    required = ["AZURE_SEARCH_SERVICE", "AZURE_SEARCH_INDEX"]
    missing = [v for v in required if not os.getenv(v)]
    if missing:
        print(f"❌ Missing required environment variables: {missing}")
        print("\nSet these manually or run 'azd env select <env-name>' first")
        sys.exit(1)
    
    return {
        "service": os.getenv("AZURE_SEARCH_SERVICE"),
        "index": os.getenv("AZURE_SEARCH_INDEX"),
        "tenant_id": os.getenv("AZURE_TENANT_ID"),
    }


def get_search_client(config: dict) -> SearchClient:
    """Create authenticated search client."""
    endpoint = f"https://{config['service']}.search.windows.net"
    
    # Try AzureDeveloperCliCredential first, then DefaultAzureCredential
    if config.get("tenant_id"):
        credential = AzureDeveloperCliCredential(tenant_id=config["tenant_id"])
    else:
        credential = DefaultAzureCredential()
    
    client = SearchClient(
        endpoint=endpoint,
        index_name=config["index"],
        credential=credential
    )
    
    print(f"✅ Connected to: {endpoint}")
    print(f"   Index: {config['index']}")
    
    return client


def list_documents(client: SearchClient, limit: int = 10):
    """List sample documents from the index."""
    print(f"\n📄 Listing first {limit} documents...")
    print("=" * 80)
    
    results = client.search(
        search_text="*",
        top=limit,
        select=["id", "category", "sourcefile", "sourcepage"]
    )
    
    for i, doc in enumerate(results, 1):
        print(f"\n{i}. {doc.get('sourcefile', 'Unknown')}")
        print(f"   ID: {doc.get('id', 'N/A')}")
        print(f"   Category: {doc.get('category', 'N/A')}")
        print(f"   Page: {doc.get('sourcepage', 'N/A')}")


def search_documents(client: SearchClient, query: str, top: int = 5, 
                     use_semantic: bool = True, category: Optional[str] = None):
    """Search documents with optional semantic ranking and category filter."""
    print(f"\n🔍 Searching for: '{query}'")
    if category:
        print(f"   Category filter: {category}")
    print("=" * 80)
    
    # Build filter
    filter_expr = None
    if category:
        filter_expr = f"category eq '{category}'"
    
    # Search with semantic ranking if available
    search_params = {
        "search_text": query,
        "top": top,
        "filter": filter_expr,
        "select": ["id", "content", "category", "sourcefile", "sourcepage"],
        "include_total_count": True,
    }
    
    if use_semantic:
        search_params["query_type"] = "semantic"
        search_params["semantic_configuration_name"] = "default"
        search_params["query_caption"] = "extractive"
    
    try:
        results = client.search(**search_params)
        
        print(f"Total matching: {results.get_count()}")
        
        for i, doc in enumerate(results, 1):
            print(f"\n{'─' * 80}")
            print(f"Result {i}: {doc.get('sourcefile', 'Unknown')}")
            print(f"   Score: {doc.get('@search.score', 'N/A')}")
            if use_semantic:
                print(f"   Reranker Score: {doc.get('@search.reranker_score', 'N/A')}")
            print(f"   Category: {doc.get('category', 'N/A')}")
            print(f"   Source: {doc.get('sourcefile', 'N/A')}#page={doc.get('sourcepage', 'N/A')}")
            
            # Show content snippet
            content = doc.get("content", "")[:500]
            print(f"\n   Content preview:")
            for line in content.split("\n")[:5]:
                print(f"   │ {line[:100]}")
            
            # Show captions if available
            captions = doc.get("@search.captions")
            if captions:
                print(f"\n   Semantic caption: {captions[0].text[:200]}...")
                
    except Exception as e:
        if "semantic" in str(e).lower():
            print(f"⚠️  Semantic search not available: {e}")
            print("   Falling back to keyword search...")
            search_params.pop("query_type", None)
            search_params.pop("semantic_configuration_name", None)
            search_params.pop("query_caption", None)
            results = client.search(**search_params)
            for i, doc in enumerate(results, 1):
                print(f"\n{i}. {doc.get('sourcefile', 'Unknown')} ({doc.get('category', 'N/A')})")
        else:
            raise


def list_categories(client: SearchClient):
    """List all unique categories in the index."""
    print("\n📂 Categories in index:")
    print("=" * 80)
    
    # Search all documents and aggregate categories
    results = client.search(
        search_text="*",
        top=1000,
        select=["category"]
    )
    
    categories = {}
    for doc in results:
        cat = doc.get("category", "Uncategorized")
        categories[cat] = categories.get(cat, 0) + 1
    
    print(f"Found {len(categories)} categories:\n")
    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        print(f"  {count:4d} documents: {cat}")
    
    return categories


def export_search_results(client: SearchClient, query: str, output_file: str, 
                          top: int = 10, category: Optional[str] = None):
    """Export search results to JSON for ground truth creation."""
    print(f"\n📤 Exporting search results for: '{query}'")
    
    filter_expr = f"category eq '{category}'" if category else None
    
    try:
        results = client.search(
            search_text=query,
            top=top,
            filter=filter_expr,
            select=["id", "content", "category", "sourcefile", "sourcepage"],
            query_type="semantic",
            semantic_configuration_name="default",
        )
    except Exception:
        # Fallback without semantic
        results = client.search(
            search_text=query,
            top=top,
            filter=filter_expr,
            select=["id", "content", "category", "sourcefile", "sourcepage"],
        )
    
    export_data = {
        "query": query,
        "category_filter": category,
        "results": []
    }
    
    for doc in results:
        export_data["results"].append({
            "id": doc.get("id"),
            "sourcefile": doc.get("sourcefile"),
            "category": doc.get("category"),
            "source": f"{doc.get('sourcefile', '')}#page={doc.get('sourcepage', '')}",
            "content": doc.get("content", "")[:1000],  # First 1000 chars
            "score": doc.get("@search.reranker_score") or doc.get("@search.score"),
        })
    
    with open(output_file, "w") as f:
        json.dump(export_data, f, indent=2)
    
    print(f"✅ Exported {len(export_data['results'])} results to {output_file}")


def test_legal_queries(client: SearchClient):
    """Run a suite of legal-specific test queries."""
    print("\n⚖️  Running Legal Domain Test Queries")
    print("=" * 80)
    
    test_queries = [
        ("CPR Part 36 settlement offers", None),
        ("disclosure requirements fast track", None),
        ("summary judgment application", None),
        ("limitation period contract", None),
        ("skeleton argument requirements", "King's Bench Division"),
        ("case management conference", "Commercial Court"),
        ("expert evidence TCC", "Technology and Construction Court"),
        ("Circuit Commercial Court disclosure", "Circuit Commercial Court"),
        ("Patents Court procedure", "Patents Court"),
    ]
    
    for query, category in test_queries:
        print(f"\n{'─' * 60}")
        print(f"Query: {query}")
        if category:
            print(f"Category: {category}")
        
        filter_expr = f"category eq '{category}'" if category else None
        
        try:
            try:
                results = list(client.search(
                    search_text=query,
                    top=3,
                    filter=filter_expr,
                    select=["category", "sourcefile", "sourcepage"],
                    query_type="semantic",
                    semantic_configuration_name="default",
                ))
            except Exception:
                # Fallback without semantic
                results = list(client.search(
                    search_text=query,
                    top=3,
                    filter=filter_expr,
                    select=["category", "sourcefile", "sourcepage"],
                ))
            
            if results:
                print(f"✅ Found {len(results)} results:")
                for doc in results:
                    source = f"{doc.get('sourcefile', 'Unknown')}#page={doc.get('sourcepage', '')}"
                    print(f"   • {source} [{doc.get('category', 'N/A')}]")
            else:
                print("⚠️  No results found")
                
        except Exception as e:
            print(f"❌ Error: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Test Azure AI Search index for legal RAG",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --action list                           # List sample documents
  %(prog)s --action search --query "CPR Part 36"   # Search documents
  %(prog)s --action categories                     # List all categories
  %(prog)s --action test                           # Run legal test queries
  %(prog)s --action export --query "disclosure" --output results.json
        """
    )
    
    parser.add_argument("--action", required=True,
                        choices=["list", "search", "categories", "test", "export"],
                        help="Action to perform")
    parser.add_argument("--query", "-q", help="Search query")
    parser.add_argument("--category", "-c", help="Filter by category")
    parser.add_argument("--top", "-n", type=int, default=5, help="Number of results")
    parser.add_argument("--output", "-o", help="Output file for export")
    parser.add_argument("--no-semantic", action="store_true", help="Disable semantic search")
    
    args = parser.parse_args()
    
    # Load environment and create client
    config = load_environment()
    client = get_search_client(config)
    
    # Execute action
    if args.action == "list":
        list_documents(client, args.top)
    
    elif args.action == "search":
        if not args.query:
            parser.error("--query is required for search action")
        search_documents(client, args.query, args.top, 
                        not args.no_semantic, args.category)
    
    elif args.action == "categories":
        list_categories(client)
    
    elif args.action == "test":
        test_legal_queries(client)
    
    elif args.action == "export":
        if not args.query or not args.output:
            parser.error("--query and --output are required for export action")
        export_search_results(client, args.query, args.output, 
                             args.top, args.category)


if __name__ == "__main__":
    main()
