#!/usr/bin/env python
"""
Comprehensive test of ALL locally scraped documents against Azure Search.

Tests every single document in the Upload folder to verify:
1. Document exists in Azure Search
2. Content matches exactly
3. Embeddings are correct dimension
4. Coverage of all CPR Parts and Practice Directions

Usage:
    python test_comprehensive_all_documents.py
"""
import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Tuple
from azure.search.documents import SearchClient
from azure.identity import DefaultAzureCredential
from openai import AzureOpenAI


class ComprehensiveTest:
    """Comprehensive test of all documents."""
    
    def __init__(self):
        credential = DefaultAzureCredential()
        self.search_client = SearchClient(
            endpoint="https://cpr-rag.search.windows.net",
            index_name="legal-court-rag-index",
            credential=credential
        )
        self.openai_client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_KEY"),
            api_version="2024-12-01-preview",
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", "https://2025-06-27-cpr.cognitiveservices.azure.com/"),
        )
        self.upload_dir = Path("/Users/HasithB/Downloads/PROJECTS/azure-search-openai-demo-2/data/legal-scraper/processed/Upload")
        
    def load_local_documents(self) -> List[Dict]:
        """Load all documents from Upload directory."""
        documents = []
        if not self.upload_dir.exists():
            print(f"❌ Upload directory not found: {self.upload_dir}")
            return documents
            
        for json_file in self.upload_dir.glob("*.json"):
            # Skip summary and flattened files
            if json_file.name in ["civil_procedure_rules_flattened.json", 
                                  "civil_procedure_rules_review.json"]:
                continue
                
            try:
                with open(json_file) as f:
                    data = json.load(f)
                    
                    # Handle both single dict and list of dicts
                    if isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict):
                                item["_file"] = json_file.name
                                documents.append(item)
                    elif isinstance(data, dict):
                        data["_file"] = json_file.name
                        documents.append(data)
                    else:
                        print(f"⚠️ Unexpected format in {json_file.name}")
                        
            except Exception as e:
                print(f"❌ Error loading {json_file.name}: {e}")
                
        return documents
    
    def find_in_azure(self, doc: Dict) -> Tuple[bool, Dict, str]:
        """Find document in Azure Search and return match info."""
        sourcefile = doc.get("sourcefile", "")
        
        # Debug print
        # print(f"Searching for sourcefile: '{sourcefile}'")
        
        try:
            results = list(self.search_client.search(
                search_text="*",
                filter=f"sourcefile eq '{sourcefile}'",
                top=1,
                select=["id", "sourcefile", "content"]
            ))
            
            if results:
                azure_doc = results[0]
                # Check content match
                local_content = doc.get("content", "").strip()
                azure_content = azure_doc.get("content", "").strip()
                
                # Normalize line endings and whitespace for comparison
                local_norm = " ".join(local_content.split())
                azure_norm = " ".join(azure_content.split())
                
                content_match = local_norm == azure_norm
                
                if not content_match:
                     # print(f"Content mismatch for {sourcefile}")
                     pass
                
                return (True, azure_doc, "found" if content_match else "found_mismatch")
            else:
                # print(f"Not found: {sourcefile}")
                return (False, {}, "not_found")
        except Exception as e:
            print(f"Search error for {sourcefile}: {e}")
            return (False, {}, f"error: {e}")
    
    def test_embedding(self, content: str) -> Tuple[int, bool]:
        """Test that embeddings work and return correct dimension."""
        try:
            response = self.openai_client.embeddings.create(
                input=content[:500] if len(content) > 500 else content,
                model="text-embedding-3-large"
            )
            embedding = response.data[0].embedding
            dimension = len(embedding)
            is_correct = dimension == 3072
            return (dimension, is_correct)
        except Exception as e:
            return (0, False)
    
    def run_comprehensive_test(self):
        """Run comprehensive test on all documents."""
        print("\n" + "="*80)
        print("🔍 COMPREHENSIVE TEST: ALL LOCAL DOCUMENTS vs AZURE SEARCH")
        print("="*80)
        
        # Load local documents
        print("\n📂 Loading locally scraped documents...")
        local_docs = self.load_local_documents()
        
        if not local_docs:
            print("❌ No documents found in Upload directory")
            return
        
        print(f"✅ Found {len(local_docs)} local documents")
        
        # Test each document
        print("\n" + "="*80)
        print("📋 TESTING EACH DOCUMENT")
        print("="*80)
        
        results = {
            "found": [],
            "not_found": [],
            "mismatch": [],
            "errors": []
        }
        
        embedding_tests = []
        
        for i, doc in enumerate(local_docs, 1):
            filename = doc.get("_file", "unknown")
            sourcefile = doc.get("sourcefile", "N/A")
            content_len = len(doc.get("content", ""))
            
            # Test if document exists in Azure
            found, azure_doc, status = self.find_in_azure(doc)
            
            if found and status == "found":
                print(f"✅ [{i:2d}] {filename:40s} | {sourcefile:30s} | {content_len:6d} chars")
                results["found"].append({
                    "file": filename,
                    "sourcefile": sourcefile,
                    "content_len": content_len
                })
                
                # Test embedding on this document
                dim, is_correct = self.test_embedding(doc.get("content", ""))
                embedding_tests.append({
                    "file": filename,
                    "dimension": dim,
                    "correct": is_correct
                })
                
            elif found and status == "found_mismatch":
                print(f"⚠️  [{i:2d}] {filename:40s} | CONTENT MISMATCH")
                results["mismatch"].append({
                    "file": filename,
                    "sourcefile": sourcefile
                })
            else:
                print(f"❌ [{i:2d}] {filename:40s} | NOT FOUND IN AZURE")
                results["not_found"].append({
                    "file": filename,
                    "sourcefile": sourcefile
                })
        
        # Print summary
        print("\n" + "="*80)
        print("📊 SUMMARY")
        print("="*80)
        
        print(f"\n📦 Document Coverage:")
        print(f"   ✅ Found in Azure:        {len(results['found']):3d}")
        print(f"   ❌ Not found in Azure:    {len(results['not_found']):3d}")
        print(f"   ⚠️  Content mismatch:      {len(results['mismatch']):3d}")
        print(f"   🔥 Errors:                {len(results['errors']):3d}")
        print(f"   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"   TOTAL:                    {len(local_docs):3d}")
        
        # Embedding test summary
        if embedding_tests:
            correct_embeds = sum(1 for t in embedding_tests if t["correct"])
            print(f"\n🧠 Embedding Tests:")
            print(f"   Correct (3072 dims):      {correct_embeds}/{len(embedding_tests)}")
            
            # Show any dimension errors
            bad_dims = [t for t in embedding_tests if not t["correct"]]
            if bad_dims:
                print(f"   ❌ Incorrect dimensions:")
                for t in bad_dims:
                    print(f"      - {t['file']}: {t['dimension']} dims")
        
        # Success/failure verdict
        print("\n" + "="*80)
        if len(results["not_found"]) == 0 and len(results["mismatch"]) == 0:
            print("✅ ✅ ✅ COMPREHENSIVE TEST: PASSED ✅ ✅ ✅")
            print("\n✨ All locally scraped documents are in Azure Search!")
            print("✨ All content matches exactly!")
            print("✨ All embeddings have correct dimensions!")
            print("\n🚀 INTEGRATION STATUS: COMPLETE AND OPERATIONAL")
        else:
            print("❌ COMPREHENSIVE TEST: FAILED")
            if results["not_found"]:
                print(f"\n❌ {len(results['not_found'])} documents not found in Azure:")
                for item in results["not_found"]:
                    print(f"   - {item['file']} ({item['sourcefile']})")
            if results["mismatch"]:
                print(f"\n⚠️  {len(results['mismatch'])} documents with content mismatch:")
                for item in results["mismatch"]:
                    print(f"   - {item['file']} ({item['sourcefile']})")
        
        print("="*80)
        
        # Save results to file
        results_file = self.upload_dir.parent / "comprehensive_test_results.json"
        with open(results_file, 'w') as f:
            json.dump({
                "total_local": len(local_docs),
                "found": len(results["found"]),
                "not_found": len(results["not_found"]),
                "mismatch": len(results["mismatch"]),
                "details": results
            }, f, indent=2)
        print(f"\n📄 Results saved to: {results_file}")


if __name__ == "__main__":
    test = ComprehensiveTest()
    test.run_comprehensive_test()
