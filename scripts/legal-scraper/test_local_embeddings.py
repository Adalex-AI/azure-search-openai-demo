#!/usr/bin/env python
"""
Test embeddings generation locally and compare against Azure Search.
This script:
1. Tests local embedding generation
2. Checks scraped documents
3. Queries Azure Search to compare results
"""
import json
import os
import sys
from pathlib import Path

# Add paths
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from config import Config
from validation import DocumentValidator
from azure.search.documents import SearchClient
from azure.identity import DefaultAzureCredential
from azure.core.credentials import AzureKeyCredential
from openai import AzureOpenAI


def get_azure_search_client():
    """Initialize Azure Search client."""
    if not Config.AZURE_SEARCH_SERVICE or not Config.AZURE_SEARCH_KEY:
        print("❌ Azure Search credentials not configured")
        return None
    
    search_client = SearchClient(
        endpoint=f"https://{Config.AZURE_SEARCH_SERVICE}.search.windows.net",
        index_name=Config.AZURE_SEARCH_INDEX,
        credential=AzureKeyCredential(Config.AZURE_SEARCH_KEY)
    )
    return search_client


def get_embedding_client():
    """Initialize Azure OpenAI embedding client."""
    if not Config.AZURE_OPENAI_SERVICE or not Config.AZURE_OPENAI_KEY:
        print("❌ Azure OpenAI credentials not configured")
        return None
    
    client = AzureOpenAI(
        api_key=Config.AZURE_OPENAI_KEY,
        api_version=Config.AZURE_OPENAI_API_VERSION,
        azure_endpoint=f"https://{Config.AZURE_OPENAI_SERVICE}.openai.azure.com/",
    )
    return client


def test_local_embeddings():
    """Test embedding generation locally."""
    print("\n" + "="*60)
    print("🧪 TESTING LOCAL EMBEDDINGS")
    print("="*60)
    
    client = get_embedding_client()
    if not client:
        return None
    
    # Test texts
    test_texts = [
        "Rules of evidence in civil procedure",
        "Disclosure of documents in court proceedings",
        "Service of legal documents and pleadings"
    ]
    
    embeddings = {}
    for text in test_texts:
        try:
            response = client.embeddings.create(
                input=text,
                model=Config.AZURE_OPENAI_EMB_DEPLOYMENT
            )
            embedding = response.data[0].embedding
            embeddings[text] = {
                "embedding_dim": len(embedding),
                "first_5_values": embedding[:5],
                "magnitude": sum(x**2 for x in embedding) ** 0.5
            }
            print(f"✅ {text[:50]:50} | dim={len(embedding)}")
        except Exception as e:
            print(f"❌ {text[:50]:50} | Error: {str(e)[:40]}")
    
    return embeddings


def check_scraped_documents():
    """Check for scraped documents in output folder."""
    print("\n" + "="*60)
    print("📄 CHECKING SCRAPED DOCUMENTS")
    print("="*60)
    
    # Check in legal-rag-scraper-deployment
    original_output = Path(
        "/Users/HasithB/Downloads/PROJECTS/azure-search-openai-demo-2/"
        "legal-rag-scraper-deployment/data/processed"
    )
    
    # Also check scripts output
    script_output = Path(
        "/Users/HasithB/Downloads/PROJECTS/azure-search-openai-demo-2/"
        "data/legal-scraper/processed"
    )
    
    scraped_docs = []
    
    for output_dir in [original_output, script_output]:
        if output_dir.exists():
            print(f"\n📁 Checking: {output_dir}")
            for json_file in output_dir.glob("**/*.json"):
                try:
                    with open(json_file) as f:
                        doc = json.load(f)
                        content_len = len(doc.get("content", ""))
                        scraped_docs.append({
                            "file": json_file.name,
                            "content_length": content_len,
                            "has_required_fields": all(
                                k in doc for k in ["content", "id", "sourcefile", "category"]
                            )
                        })
                        print(f"  ✅ {json_file.name[:40]:40} | {content_len:6} chars")
                except Exception as e:
                    print(f"  ❌ {json_file.name[:40]:40} | Error: {str(e)[:30]}")
        else:
            print(f"  ⚠️  Not found: {output_dir}")
    
    return scraped_docs


def check_azure_search_index():
    """Query Azure Search to see what's in the index."""
    print("\n" + "="*60)
    print("🔍 CHECKING AZURE SEARCH INDEX")
    print("="*60)
    
    client = get_azure_search_client()
    if not client:
        return None
    
    try:
        # Get document count
        from azure.search.documents.models import SearchItemsPageIterator
        results = client.search(search_text="*", select=["id"], top=1)
        total_count = results.get_count() if hasattr(results, 'get_count') else "Unknown"
        print(f"📊 Total documents in index: {total_count}")
        
        # Sample a few documents
        results = client.search(search_text="civil procedure", top=3)
        sample_docs = []
        print(f"\n📋 Sample documents matching 'civil procedure':")
        for doc in results:
            doc_data = {
                "id": doc.get("id"),
                "sourcefile": doc.get("sourcefile"),
                "category": doc.get("category"),
                "content_preview": (doc.get("content", "")[:80] + "...")
            }
            sample_docs.append(doc_data)
            print(f"  • {doc.get('sourcefile', 'Unknown')[:30]:30} | {doc.get('id', 'N/A')[:10]:10}")
        
        return {
            "total_count": total_count,
            "sample_docs": sample_docs
        }
        
    except Exception as e:
        print(f"❌ Error querying Azure Search: {str(e)}")
        return None


def compare_results(embeddings, scraped_docs, azure_search_info):
    """Generate comparison report."""
    print("\n" + "="*60)
    print("📊 COMPARISON RESULTS")
    print("="*60)
    
    report = {
        "embeddings_tested": len(embeddings) if embeddings else 0,
        "scraped_documents_found": len(scraped_docs) if scraped_docs else 0,
        "azure_search_reachable": azure_search_info is not None,
        "findings": []
    }
    
    if embeddings:
        report["findings"].append(f"✅ {len(embeddings)} embeddings generated successfully")
        for text, emb_info in embeddings.items():
            report["findings"].append(
                f"   - Embedding dimension: {emb_info['embedding_dim']} (expected 3072)"
            )
    
    if scraped_docs:
        report["findings"].append(f"✅ {len(scraped_docs)} scraped documents found")
        valid_docs = sum(1 for d in scraped_docs if d["has_required_fields"])
        report["findings"].append(f"   - Valid schema: {valid_docs}/{len(scraped_docs)}")
    else:
        report["findings"].append("⚠️  No scraped documents found yet (still scraping?)")
    
    if azure_search_info:
        report["findings"].append(f"✅ Azure Search reachable")
        report["findings"].append(f"   - Index size: {azure_search_info.get('total_count', 'Unknown')} docs")
        if azure_search_info.get("sample_docs"):
            report["findings"].append(f"   - Sample queries work: {len(azure_search_info['sample_docs'])} results")
    else:
        report["findings"].append("❌ Azure Search not reachable or not configured")
    
    # Print report
    for finding in report["findings"]:
        print(finding)
    
    return report


def main():
    """Run all tests."""
    print("\n🚀 LOCAL EMBEDDINGS & AZURE SEARCH COMPARISON TEST")
    print("=" * 60)
    
    # Test embeddings
    embeddings = test_local_embeddings()
    
    # Check scraped documents
    scraped_docs = check_scraped_documents()
    
    # Check Azure Search
    azure_search_info = check_azure_search_index()
    
    # Compare results
    report = compare_results(embeddings, scraped_docs, azure_search_info)
    
    # Save report
    report_file = Path(__file__).parent / "test_results.json"
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\n💾 Report saved to: {report_file}")
    
    return 0 if report["azure_search_reachable"] else 1


if __name__ == "__main__":
    sys.exit(main())
