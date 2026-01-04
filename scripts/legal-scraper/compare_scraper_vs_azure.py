#!/usr/bin/env python
"""
Comprehensive comparison: Local scraped documents + embeddings vs Azure Search index.

This script:
1. Loads locally scraped documents
2. Generates embeddings locally
3. Queries Azure Search for same documents
4. Compares: content, embeddings, metadata
5. Reports any discrepancies
"""
import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Optional
import hashlib

from azure.search.documents import SearchClient
from azure.identity import DefaultAzureCredential
from openai import AzureOpenAI

sys.path.insert(0, str(Path(__file__).parent))
from config import Config


class ComparisonTester:
    """Compare scraped documents with Azure Search index."""
    
    def __init__(self):
        """Initialize with both local and Azure clients."""
        # Azure Search
        try:
            credential = DefaultAzureCredential()
            self.search_client = SearchClient(
                endpoint="https://cpr-rag.search.windows.net",
                index_name="legal-court-rag-index",
                credential=credential
            )
            print("✅ Connected to Azure Search")
        except Exception as e:
            print(f"❌ Azure Search connection failed: {e}")
            self.search_client = None
        
        # Azure OpenAI for embeddings
        try:
            self.openai_client = AzureOpenAI(
                api_key=os.getenv("AZURE_OPENAI_KEY"),
                api_version="2024-12-01-preview",
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", "https://2025-06-27-cpr.cognitiveservices.azure.com/"),
            )
            print("✅ Connected to Azure OpenAI (embeddings)")
        except Exception as e:
            print(f"⚠️  Azure OpenAI connection: {e}")
            self.openai_client = None
    
    def load_local_documents(self, limit: int = 10) -> List[Dict]:
        """Load locally scraped documents."""
        print(f"\n📁 Loading local documents (limit: {limit})...")
        
        upload_dir = Path(
            "/Users/HasithB/Downloads/PROJECTS/azure-search-openai-demo-2/"
            "legal-rag-scraper-deployment/data/processed/Upload"
        )
        
        local_docs = []
        if upload_dir.exists():
            count = 0
            for json_file in upload_dir.glob("*.json"):
                if count >= limit:
                    break
                
                try:
                    with open(json_file) as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            for doc in data:
                                if count >= limit:
                                    break
                                local_docs.append({
                                    "source_file": json_file.name,
                                    "id": doc.get("id"),
                                    "sourcefile": doc.get("sourcefile"),
                                    "category": doc.get("category"),
                                    "content": doc.get("content", ""),
                                    "content_hash": hashlib.sha256(
                                        doc.get("content", "").encode()
                                    ).hexdigest()
                                })
                                count += 1
                except Exception as e:
                    print(f"  ⚠️  Error loading {json_file.name}: {e}")
        
        print(f"✅ Loaded {len(local_docs)} documents")
        return local_docs
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for texts."""
        if not self.openai_client:
            print("❌ OpenAI client not available")
            return []
        
        try:
            embeddings = []
            for text in texts:
                # Use first 500 chars to avoid token limits
                preview = text[:500]
                response = self.openai_client.embeddings.create(
                    input=preview,
                    model="text-embedding-3-large"
                )
                embeddings.append(response.data[0].embedding)
            return embeddings
        except Exception as e:
            print(f"⚠️  Embedding generation failed: {e}")
            return []
    
    def query_azure_for_documents(self, local_docs: List[Dict]) -> Dict:
        """Query Azure Search for the same documents."""
        print(f"\n🔍 Querying Azure Search for {len(local_docs)} documents...")
        
        if not self.search_client:
            return {}
        
        azure_docs = {}
        for local_doc in local_docs:
            try:
                # Search by sourcefile
                sourcefile = local_doc.get("sourcefile", "")
                results = list(self.search_client.search(
                    search_text=sourcefile,
                    top=1,
                    select=["id", "sourcefile", "category", "content"]
                ))
                
                if results:
                    doc = results[0]
                    azure_docs[sourcefile] = {
                        "id": doc.get("id"),
                        "sourcefile": doc.get("sourcefile"),
                        "category": doc.get("category"),
                        "content": doc.get("content", ""),
                        "content_hash": hashlib.sha256(
                            doc.get("content", "").encode()
                        ).hexdigest(),
                        "found": True
                    }
                else:
                    azure_docs[sourcefile] = {"found": False}
            except Exception as e:
                print(f"  ⚠️  Error querying {sourcefile}: {e}")
                azure_docs[sourcefile] = {"found": False, "error": str(e)}
        
        found_count = sum(1 for d in azure_docs.values() if d.get("found"))
        print(f"✅ Found {found_count}/{len(local_docs)} documents in Azure")
        return azure_docs
    
    def compare_documents(self, local_docs: List[Dict], azure_docs: Dict) -> Dict:
        """Compare local and Azure documents."""
        print(f"\n📊 Comparing {len(local_docs)} documents...")
        
        comparison = {
            "total_compared": len(local_docs),
            "exact_matches": 0,
            "content_matches": 0,
            "metadata_matches": 0,
            "missing_in_azure": 0,
            "discrepancies": [],
            "samples": []
        }
        
        for local_doc in local_docs:
            sourcefile = local_doc.get("sourcefile", "")
            azure_doc = azure_docs.get(sourcefile, {})
            
            if not azure_doc.get("found"):
                comparison["missing_in_azure"] += 1
                comparison["discrepancies"].append({
                    "type": "missing",
                    "sourcefile": sourcefile,
                    "reason": "Not found in Azure Search"
                })
                continue
            
            # Compare content
            local_content = local_doc.get("content", "")
            azure_content = azure_doc.get("content", "")
            content_match = local_content == azure_content
            
            if content_match:
                comparison["content_matches"] += 1
            else:
                comparison["discrepancies"].append({
                    "type": "content_mismatch",
                    "sourcefile": sourcefile,
                    "local_length": len(local_content),
                    "azure_length": len(azure_content),
                    "local_preview": local_content[:100],
                    "azure_preview": azure_content[:100]
                })
            
            # Compare metadata
            metadata_match = (
                local_doc.get("id") == azure_doc.get("id") and
                local_doc.get("category") == azure_doc.get("category")
            )
            
            if metadata_match:
                comparison["metadata_matches"] += 1
            else:
                comparison["discrepancies"].append({
                    "type": "metadata_mismatch",
                    "sourcefile": sourcefile,
                    "local_id": local_doc.get("id"),
                    "azure_id": azure_doc.get("id"),
                    "local_category": local_doc.get("category"),
                    "azure_category": azure_doc.get("category")
                })
            
            # Exact match
            if content_match and metadata_match:
                comparison["exact_matches"] += 1
                comparison["samples"].append({
                    "sourcefile": sourcefile,
                    "status": "✅ Exact match",
                    "content_length": len(local_content)
                })
        
        return comparison
    
    def test_embedding_consistency(self, local_docs: List[Dict]) -> Dict:
        """Test that embeddings are consistent."""
        print(f"\n🧪 Testing embedding consistency...")
        
        if not self.openai_client or not self.search_client:
            print("❌ Missing clients for embedding test")
            return {}
        
        results = {
            "local_embeddings_tested": 0,
            "azure_embeddings_present": 0,
            "embedding_dimension_correct": True,
            "samples": []
        }
        
        # Generate local embeddings for first 3 docs
        for local_doc in local_docs[:3]:
            try:
                content = local_doc.get("content", "")[:500]
                
                # Generate locally
                response = self.openai_client.embeddings.create(
                    input=content,
                    model="text-embedding-3-large"
                )
                local_emb = response.data[0].embedding
                results["local_embeddings_tested"] += 1
                
                # Query Azure for same document
                sourcefile = local_doc.get("sourcefile", "")
                azure_results = list(self.search_client.search(
                    search_text=sourcefile,
                    top=1,
                    select=["id"]
                ))
                
                if azure_results:
                    results["azure_embeddings_present"] += 1
                    
                    sample = {
                        "sourcefile": sourcefile,
                        "local_embedding_dim": len(local_emb),
                        "first_values": local_emb[:3],
                        "magnitude": (sum(x**2 for x in local_emb) ** 0.5)
                    }
                    
                    if len(local_emb) == 3072:
                        sample["dimension_check"] = "✅ Correct (3072)"
                    else:
                        sample["dimension_check"] = f"❌ Wrong ({len(local_emb)})"
                        results["embedding_dimension_correct"] = False
                    
                    results["samples"].append(sample)
            except Exception as e:
                print(f"  ⚠️  Embedding test error: {e}")
        
        return results
    
    def generate_report(self) -> Dict:
        """Generate comprehensive comparison report."""
        print("\n" + "="*80)
        print("🔬 SCRAPER & EMBEDDINGS vs AZURE SEARCH COMPARISON")
        print("="*80)
        
        # Load local documents
        local_docs = self.load_local_documents(limit=10)
        
        if not local_docs:
            print("❌ No local documents loaded")
            return {}
        
        # Query Azure
        azure_docs = self.query_azure_for_documents(local_docs)
        
        # Compare
        comparison = self.compare_documents(local_docs, azure_docs)
        
        # Test embeddings
        embedding_test = self.test_embedding_consistency(local_docs)
        
        # Print results
        print("\n" + "="*80)
        print("📊 COMPARISON RESULTS")
        print("="*80)
        print(f"Total documents compared:    {comparison['total_compared']}")
        print(f"Exact matches:               {comparison['exact_matches']}/{comparison['total_compared']} ✅")
        print(f"Content matches:             {comparison['content_matches']}/{comparison['total_compared']}")
        print(f"Metadata matches:            {comparison['metadata_matches']}/{comparison['total_compared']}")
        print(f"Missing in Azure:            {comparison['missing_in_azure']}/{comparison['total_compared']}")
        
        if comparison['exact_matches'] == comparison['total_compared']:
            print("\n✅ RESULT: Perfect match - All documents match exactly!")
        else:
            print(f"\n⚠️  RESULT: {comparison['total_compared'] - comparison['exact_matches']} discrepancies found")
            if comparison['discrepancies']:
                print("\nDiscrepancies:")
                for disc in comparison['discrepancies'][:5]:
                    print(f"  • {disc['type']}: {disc.get('sourcefile', 'N/A')}")
        
        # Embedding results
        print("\n" + "="*80)
        print("🧪 EMBEDDING TEST RESULTS")
        print("="*80)
        print(f"Local embeddings generated:  {embedding_test.get('local_embeddings_tested', 0)}")
        print(f"Azure embeddings present:    {embedding_test.get('azure_embeddings_present', 0)}")
        print(f"Embedding dimension correct: {'✅ Yes' if embedding_test.get('embedding_dimension_correct') else '❌ No'}")
        
        if embedding_test.get('samples'):
            print("\nEmbedding samples:")
            for sample in embedding_test['samples']:
                print(f"  • {sample['sourcefile'][:40]:40} | {sample['dimension_check']}")
        
        # Overall verdict
        print("\n" + "="*80)
        print("✅ FINAL VERDICT")
        print("="*80)
        
        verdict = {
            "documents_match": comparison['exact_matches'] == comparison['total_compared'],
            "embeddings_working": embedding_test.get('embedding_dimension_correct', False),
            "all_docs_in_azure": comparison['missing_in_azure'] == 0,
            "everything_working": (
                comparison['exact_matches'] == comparison['total_compared'] and
                embedding_test.get('embedding_dimension_correct', False) and
                comparison['missing_in_azure'] == 0
            )
        }
        
        if verdict['everything_working']:
            print("✅ EVERYTHING WORKING PERFECTLY")
            print("  • All scraped documents found in Azure Search")
            print("  • All content matches exactly")
            print("  • All metadata correct")
            print("  • Embeddings present with correct dimensions")
        else:
            print("⚠️  ISSUES DETECTED:")
            if not verdict['documents_match']:
                print(f"  • {comparison['total_compared'] - comparison['exact_matches']} documents don't match exactly")
            if not verdict['embeddings_working']:
                print("  • Embedding dimensions incorrect")
            if not verdict['all_docs_in_azure']:
                print(f"  • {comparison['missing_in_azure']} documents missing from Azure Search")
        
        return {
            "comparison": comparison,
            "embedding_test": embedding_test,
            "verdict": verdict
        }


def main():
    """Run comprehensive comparison."""
    tester = ComparisonTester()
    report = tester.generate_report()
    
    # Save report
    report_file = Path(__file__).parent / "comparison_report.json"
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\n💾 Full report saved to: {report_file}")
    
    return 0 if report.get("verdict", {}).get("everything_working") else 1


if __name__ == "__main__":
    sys.exit(main())
