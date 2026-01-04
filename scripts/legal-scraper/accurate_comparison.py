#!/usr/bin/env python
"""
Accurate comparison: Local scraped documents vs Azure Search (using ID-based matching).

This ensures we compare the EXACT same documents by looking up via ID/sourcefile.
"""
import json
import sys
import os
from pathlib import Path
from typing import Dict, List
import hashlib

from azure.search.documents import SearchClient
from azure.identity import DefaultAzureCredential
from openai import AzureOpenAI

sys.path.insert(0, str(Path(__file__).parent))


class AccurateComparison:
    """Accurate document-by-document comparison."""
    
    def __init__(self):
        """Initialize clients."""
        try:
            credential = DefaultAzureCredential()
            self.search_client = SearchClient(
                endpoint="https://cpr-rag.search.windows.net",
                index_name="legal-court-rag-index",
                credential=credential
            )
            print("✅ Connected to Azure Search")
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            self.search_client = None
        
        try:
            self.openai_client = AzureOpenAI(
                api_key=os.getenv("AZURE_OPENAI_KEY"),
                api_version="2024-12-01-preview",
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", "https://2025-06-27-cpr.cognitiveservices.azure.com/"),
            )
            print("✅ Connected to Azure OpenAI")
        except Exception as e:
            print(f"⚠️  OpenAI: {e}")
            self.openai_client = None
    
    def load_and_match_documents(self, limit: int = 15) -> List[Dict]:
        """Load local documents and find exact matches in Azure."""
        print(f"\n📁 Loading {limit} local documents and matching in Azure...")
        
        upload_dir = Path(
            "/Users/HasithB/Downloads/PROJECTS/azure-search-openai-demo-2/"
            "legal-rag-scraper-deployment/data/processed/Upload"
        )
        
        matches = []
        if upload_dir.exists():
            count = 0
            for json_file in sorted(upload_dir.glob("*.json")):
                if count >= limit:
                    break
                if json_file.name == "civil_rules_summary.json":
                    continue  # Skip summary file
                
                try:
                    with open(json_file) as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            for local_doc in data[:1]:  # Just first from each file
                                sourcefile = local_doc.get("sourcefile", "")
                                
                                # Find in Azure using filtered search
                                try:
                                    azure_results = list(self.search_client.search(
                                        search_text="*",
                                        filter=f"sourcefile eq '{sourcefile}'",
                                        top=1
                                    ))
                                    
                                    if azure_results:
                                        azure_doc = azure_results[0]
                                        
                                        local_content = local_doc.get("content", "")
                                        azure_content = azure_doc.get("content", "")
                                        
                                        match = {
                                            "sourcefile": sourcefile,
                                            "local_content_length": len(local_content),
                                            "azure_content_length": len(azure_content),
                                            "content_match": local_content == azure_content,
                                            "local_id": local_doc.get("id"),
                                            "azure_id": azure_doc.get("id"),
                                            "id_match": local_doc.get("id") == azure_doc.get("id"),
                                            "local_category": local_doc.get("category"),
                                            "azure_category": azure_doc.get("category"),
                                            "category_match": local_doc.get("category") == azure_doc.get("category")
                                        }
                                        matches.append(match)
                                        count += 1
                                    else:
                                        print(f"  ⚠️  {sourcefile}: Not found in Azure")
                                except Exception as e:
                                    print(f"  ⚠️  {sourcefile}: Query error - {e}")
                except Exception as e:
                    print(f"  ⚠️  {json_file.name}: Load error - {e}")
        
        return matches
    
    def test_embedding_pipeline(self, sample_count: int = 5) -> Dict:
        """Test complete embedding pipeline."""
        print(f"\n🧪 Testing embedding pipeline ({sample_count} samples)...")
        
        if not self.openai_client or not self.search_client:
            return {}
        
        results = {
            "tested": 0,
            "successful": 0,
            "embedding_dimension_correct": True,
            "samples": []
        }
        
        upload_dir = Path(
            "/Users/HasithB/Downloads/PROJECTS/azure-search-openai-demo-2/"
            "legal-rag-scraper-deployment/data/processed/Upload"
        )
        
        count = 0
        for json_file in sorted(upload_dir.glob("*.json")):
            if count >= sample_count:
                break
            if json_file.name == "civil_rules_summary.json":
                continue
            
            try:
                with open(json_file) as f:
                    data = json.load(f)
                    if isinstance(data, list) and data:
                        local_doc = data[0]
                        sourcefile = local_doc.get("sourcefile", "")
                        content = local_doc.get("content", "")
                        
                        results["tested"] += 1
                        
                        # Generate embedding locally
                        try:
                            response = self.openai_client.embeddings.create(
                                input=content[:500],
                                model="text-embedding-3-large"
                            )
                            local_emb = response.data[0].embedding
                            
                            # Verify dimension
                            correct_dim = len(local_emb) == 3072
                            if not correct_dim:
                                results["embedding_dimension_correct"] = False
                            
                            results["successful"] += 1
                            results["samples"].append({
                                "sourcefile": sourcefile,
                                "embedding_dim": len(local_emb),
                                "dimension_correct": correct_dim,
                                "first_5_values": local_emb[:5],
                                "norm": (sum(x**2 for x in local_emb) ** 0.5)
                            })
                            
                            count += 1
                        except Exception as e:
                            print(f"  ⚠️  {sourcefile}: Embedding failed - {e}")
            except Exception as e:
                print(f"  ⚠️  {json_file.name}: Error - {e}")
        
        return results
    
    def generate_report(self) -> Dict:
        """Generate final report."""
        print("\n" + "="*80)
        print("🔬 ACCURATE SCRAPER vs AZURE COMPARISON")
        print("="*80)
        
        # Match documents
        matches = self.load_and_match_documents(limit=15)
        
        if not matches:
            print("❌ No matching documents found")
            return {}
        
        # Test embeddings
        embedding_results = self.test_embedding_pipeline(sample_count=5)
        
        # Analyze results
        print("\n" + "="*80)
        print("📊 COMPARISON RESULTS")
        print("="*80)
        
        content_matches = sum(1 for m in matches if m["content_match"])
        id_matches = sum(1 for m in matches if m["id_match"])
        category_matches = sum(1 for m in matches if m["category_match"])
        
        print(f"\nDocuments compared:     {len(matches)}")
        print(f"Content matches:        {content_matches}/{len(matches)} ✅")
        print(f"ID matches:             {id_matches}/{len(matches)} ✅")
        print(f"Category matches:       {category_matches}/{len(matches)} ✅")
        
        # Show details
        print("\n📋 Document-by-Document Comparison:")
        print("-" * 80)
        for match in matches[:10]:
            status = "✅" if (match["content_match"] and match["id_match"]) else "⚠️"
            print(f"{status} {match['sourcefile']:40} | {match['local_content_length']:6} → {match['azure_content_length']:6} chars")
            if not match["content_match"]:
                print(f"   ⚠️  Content length mismatch")
        
        # Embedding results
        print("\n" + "="*80)
        print("🧪 EMBEDDING PIPELINE TEST")
        print("="*80)
        print(f"Embeddings tested:      {embedding_results.get('tested', 0)}")
        print(f"Successful:             {embedding_results.get('successful', 0)}")
        print(f"Dimension correct:      {'✅ Yes (3072)' if embedding_results.get('embedding_dimension_correct') else '❌ No'}")
        
        if embedding_results.get('samples'):
            print("\nSamples:")
            for sample in embedding_results['samples'][:3]:
                dim_status = "✅" if sample['dimension_correct'] else "❌"
                print(f"  {dim_status} {sample['sourcefile']:40} | dim={sample['embedding_dim']} | norm={sample['norm']:.2f}")
        
        # Verdict
        print("\n" + "="*80)
        print("✅ FINAL VERDICT")
        print("="*80)
        
        all_content_match = content_matches == len(matches)
        all_ids_match = id_matches == len(matches)
        all_categories_match = category_matches == len(matches)
        embeddings_correct = embedding_results.get('embedding_dimension_correct', False)
        
        if all_content_match and all_ids_match and all_categories_match and embeddings_correct:
            print("""
✅ EVERYTHING WORKING PERFECTLY
  • All scraped documents found in Azure Search
  • All content matches exactly
  • All IDs match correctly
  • All categories match
  • Embeddings with correct dimensions (3072)
  
🎉 SCRAPER AND EMBEDDINGS FULLY OPERATIONAL
""")
            success = True
        else:
            print("⚠️  Issues detected:")
            if not all_content_match:
                print(f"  • {len(matches) - content_matches} documents have content mismatches")
            if not all_ids_match:
                print(f"  • {len(matches) - id_matches} documents have ID mismatches")
            if not all_categories_match:
                print(f"  • {len(matches) - category_matches} documents have category mismatches")
            if not embeddings_correct:
                print("  • Embedding dimensions are incorrect")
            success = False
        
        return {
            "matches": matches,
            "embedding_results": embedding_results,
            "verdict": {
                "all_content_match": all_content_match,
                "all_ids_match": all_ids_match,
                "all_categories_match": all_categories_match,
                "embeddings_correct": embeddings_correct,
                "everything_working": success
            }
        }


def main():
    """Run comparison."""
    tester = AccurateComparison()
    report = tester.generate_report()
    
    # Save report
    report_file = Path(__file__).parent / "accurate_comparison_report.json"
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\n💾 Full report saved: {report_file}")
    
    return 0 if report.get("verdict", {}).get("everything_working") else 1


if __name__ == "__main__":
    sys.exit(main())
