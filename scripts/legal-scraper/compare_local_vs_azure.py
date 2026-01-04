#!/usr/bin/env python
"""
Simple test: Compare local scraped documents against Azure Search index.
Shows: 1) What was scraped locally, 2) What's in Azure Search, 3) Differences
"""
import json
import sys
from pathlib import Path
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

# Add paths
sys.path.insert(0, str(Path(__file__).parent))
from config import Config


def scan_upload_folder():
    """Find actual uploaded documents."""
    upload_dir = Path(
        "/Users/HasithB/Downloads/PROJECTS/azure-search-openai-demo-2/"
        "legal-rag-scraper-deployment/data/processed/Upload"
    )
    
    documents = []
    if upload_dir.exists():
        for json_file in upload_dir.glob("*.json"):
            try:
                with open(json_file) as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        documents.extend([{
                            "file": json_file.name,
                            "id": doc.get("id"),
                            "sourcefile": doc.get("sourcefile"),
                            "content_len": len(doc.get("content", ""))
                        } for doc in data[:3]])  # Sample first 3 from each file
                    else:
                        # Summary file - skip
                        pass
            except Exception as e:
                print(f"⚠️  Could not parse {json_file.name}: {e}")
    
    return documents


def query_azure_search(search_text="civil", limit=5):
    """Query Azure Search."""
    try:
        if not Config.AZURE_SEARCH_SERVICE or not Config.AZURE_SEARCH_KEY:
            print("❌ Azure Search not configured")
            return []
        
        client = SearchClient(
            endpoint=f"https://{Config.AZURE_SEARCH_SERVICE}.search.windows.net",
            index_name=Config.AZURE_SEARCH_INDEX,
            credential=AzureKeyCredential(Config.AZURE_SEARCH_KEY)
        )
        
        results = client.search(search_text=search_text, top=limit)
        docs = []
        for doc in results:
            docs.append({
                "id": doc.get("id"),
                "sourcefile": doc.get("sourcefile"),
                "category": doc.get("category"),
                "content_len": len(doc.get("content", ""))
            })
        return docs
    except Exception as e:
        print(f"❌ Azure Search error: {e}")
        return []


def main():
    print("\n" + "="*70)
    print("📊 LOCAL vs AZURE SEARCH COMPARISON")
    print("="*70)
    
    # Scan local documents
    print("\n📁 SCANNING LOCAL DOCUMENTS...")
    local_docs = scan_upload_folder()
    print(f"Found {len(local_docs)} document samples in Upload folder")
    if local_docs:
        print("\nSample local documents:")
        for doc in local_docs[:3]:
            print(f"  • {doc['sourcefile'][:40]:40} | {doc['content_len']:6} chars")
    
    # Query Azure Search
    print("\n🔍 QUERYING AZURE SEARCH...")
    azure_docs = query_azure_search(search_text="civil", limit=5)
    
    if azure_docs:
        print(f"Found {len(azure_docs)} documents in Azure Search (searching 'civil')")
        print("\nSample Azure Search documents:")
        for doc in azure_docs:
            print(f"  • {doc['sourcefile'][:40]:40} | {doc['id'][:15]:15} | {doc['content_len']:6} chars")
    else:
        print("⚠️  No results from Azure Search (not configured or empty)")
    
    # Comparison
    print("\n" + "="*70)
    print("✅ COMPARISON SUMMARY")
    print("="*70)
    print(f"Local documents found:     {len(local_docs)}")
    print(f"Azure Search accessible:   {'✅ Yes' if azure_docs else '❌ No'}")
    print(f"Index has documents:       {'✅ Yes' if azure_docs else '❌ Unknown'}")
    
    if local_docs and azure_docs:
        local_ids = {d['id'] for d in local_docs}
        azure_ids = {d['id'] for d in azure_docs}
        overlap = len(local_ids & azure_ids)
        print(f"Docs in both:              {overlap}/{min(len(local_ids), len(azure_ids))}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
