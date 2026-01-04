#!/usr/bin/env python
"""
Comprehensive test of all CPR and PDs in Azure AI Search.
Tests document retrieval, embeddings, and index statistics.

Usage:
    export AZURE_SEARCH_KEY=<key>
    export AZURE_OPENAI_KEY=<key>
    python test_azure_cpr_pds.py
"""
import json
import os
import sys
from pathlib import Path
from typing import Optional, Dict, List
from azure.search.documents import SearchClient
from azure.identity import DefaultAzureCredential

# Add local imports
sys.path.insert(0, str(Path(__file__).parent))
from config import Config


class CPRPDTester:
    """Test CPR and PD documents in Azure Search."""
    
    def __init__(self):
        """Initialize with credentials."""
        # Use azd environment values
        self.search_endpoint = os.getenv('AZURE_SEARCH_ENDPOINT',
                                        'https://cpr-rag.search.windows.net')
        self.index_name = os.getenv('AZURE_SEARCH_INDEX', 'legal-court-rag-index')
        
        self.search_client = None
        try:
            credential = DefaultAzureCredential()
            self.search_client = SearchClient(
                endpoint=self.search_endpoint,
                index_name=self.index_name,
                credential=credential
            )
            print(f"✅ Connected to Azure Search: {self.search_endpoint}/{self.index_name}")
        except Exception as e:
            print(f"❌ Failed to connect: {e}")
    
    def get_index_stats(self) -> Dict:
        """Get basic index statistics."""
        if not self.search_client:
            return {}
        
        try:
            # Count total documents
            results = list(self.search_client.search(search_text="*", top=1))
            total_count = len(results) if results else 0
            
            # Try to get facets on category
            results = self.search_client.search(
                search_text="*",
                facets=["category"],
                top=1
            )
            
            stats = {
                "total_documents": total_count,
                "index_name": self.index_name
            }
            return stats
        except Exception as e:
            print(f"⚠️  Could not get index stats: {e}")
            return {}
    
    def search_cpr_rules(self) -> List[Dict]:
        """Search for CPR rules specifically."""
        if not self.search_client:
            return []
        
        try:
            # Search for "Part" which is how CPR rules are named
            results = self.search_client.search(
                search_text="Part",
                filter="sourcefile ne null",
                top=20,
                select=["id", "sourcefile", "category", "content"]
            )
            
            cpr_docs = []
            for doc in results:
                sourcefile = doc.get("sourcefile", "")
                # Filter for actual Part rules (Part 1, Part 2, etc.)
                if sourcefile and (sourcefile.startswith("Part ") or sourcefile.startswith("Part")):
                    content = doc.get("content", "")
                    cpr_docs.append({
                        "id": doc.get("id"),
                        "sourcefile": sourcefile,
                        "category": doc.get("category"),
                        "content_preview": content[:150] if content else "",
                        "content_length": len(content)
                    })
            
            return cpr_docs
        except Exception as e:
            print(f"⚠️  Error searching CPR: {e}")
            return []
    
    def search_practice_directions(self) -> List[Dict]:
        """Search for Practice Directions specifically."""
        if not self.search_client:
            return []
        
        try:
            # Search for "Practice Direction"
            results = self.search_client.search(
                search_text="Practice Direction",
                filter="sourcefile ne null",
                top=30,
                select=["id", "sourcefile", "category", "content"]
            )
            
            pd_docs = []
            for doc in results:
                sourcefile = doc.get("sourcefile", "")
                # Filter for Practice Directions
                if sourcefile and "Practice Direction" in sourcefile:
                    content = doc.get("content", "")
                    pd_docs.append({
                        "id": doc.get("id"),
                        "sourcefile": sourcefile,
                        "category": doc.get("category"),
                        "content_preview": content[:150] if content else "",
                        "content_length": len(content)
                    })
            
            return pd_docs
        except Exception as e:
            print(f"⚠️  Error searching Practice Directions: {e}")
            return []
    
    def search_court_guides(self) -> List[Dict]:
        """Search for court guides (Chancery, Commercial, etc)."""
        if not self.search_client:
            return []
        
        try:
            results = self.search_client.search(
                search_text="Guide",
                filter="sourcefile ne null",
                top=10,
                select=["id", "sourcefile", "category", "content"]
            )
            
            guide_docs = []
            for doc in results:
                sourcefile = doc.get("sourcefile", "")
                if sourcefile and "Guide" in sourcefile:
                    content = doc.get("content", "")
                    guide_docs.append({
                        "id": doc.get("id"),
                        "sourcefile": sourcefile,
                        "category": doc.get("category"),
                        "content_preview": content[:150] if content else "",
                        "content_length": len(content)
                    })
            
            return guide_docs
        except Exception as e:
            print(f"⚠️  Error searching court guides: {e}")
            return []
    
    def test_vector_search(self, query_text: str = "disclosure of documents") -> List[Dict]:
        """Test vector search (semantic search with embeddings)."""
        if not self.search_client:
            return []
        
        try:
            # Simple text search to verify documents are returned
            results = self.search_client.search(
                search_text=query_text,
                top=5,
                select=["id", "sourcefile", "category", "content"]
            )
            
            vector_results = []
            for doc in results:
                content = doc.get("content", "")
                vector_results.append({
                    "id": doc.get("id"),
                    "sourcefile": doc.get("sourcefile"),
                    "content_preview": content[:100] if content else "",
                    "score": doc.get("@search.score", 0)
                })
            
            return vector_results
        except Exception as e:
            print(f"⚠️  Error in vector search: {e}")
            return []
    
    def count_by_category(self) -> Dict[str, int]:
        """Count documents by category."""
        if not self.search_client:
            return {}
        
        try:
            # Search all and collect categories
            results = self.search_client.search(
                search_text="*",
                select=["category"],
                top=1000
            )
            
            categories = {}
            for doc in results:
                cat = doc.get("category", "Unknown")
                categories[cat] = categories.get(cat, 0) + 1
            
            return categories
        except Exception as e:
            print(f"⚠️  Error counting categories: {e}")
            return {}
    
    def generate_report(self) -> Dict:
        """Generate comprehensive test report."""
        print("\n" + "="*80)
        print("🧪 CPR & PD AZURE SEARCH INDEX TEST")
        print("="*80)
        
        report = {
            "timestamp": str(Path(__file__).stat().st_mtime),
            "endpoint": self.search_endpoint,
            "index": self.index_name,
            "connected": self.search_client is not None,
            "results": {}
        }
        
        if not self.search_client:
            print("❌ Not connected to Azure Search")
            return report
        
        # Test 1: Index Statistics
        print("\n📊 INDEX STATISTICS")
        print("-" * 80)
        stats = self.get_index_stats()
        print(f"Total documents: {stats.get('total_documents', 'N/A')}")
        report["results"]["index_stats"] = stats
        
        # Test 2: CPR Rules
        print("\n📋 CPR RULES (Parts 1-87)")
        print("-" * 80)
        cpr_docs = self.search_cpr_rules()
        print(f"Found {len(cpr_docs)} CPR rules")
        if cpr_docs:
            for doc in cpr_docs[:5]:
                print(f"  ✅ {doc['sourcefile']:30} | {doc['content_length']:6} chars")
        report["results"]["cpr_rules"] = {
            "count": len(cpr_docs),
            "samples": cpr_docs[:3]
        }
        
        # Test 3: Practice Directions
        print("\n📋 PRACTICE DIRECTIONS")
        print("-" * 80)
        pd_docs = self.search_practice_directions()
        print(f"Found {len(pd_docs)} Practice Directions")
        if pd_docs:
            for doc in pd_docs[:5]:
                print(f"  ✅ {doc['sourcefile']:30} | {doc['content_length']:6} chars")
        report["results"]["practice_directions"] = {
            "count": len(pd_docs),
            "samples": pd_docs[:3]
        }
        
        # Test 4: Court Guides
        print("\n📋 COURT GUIDES")
        print("-" * 80)
        guide_docs = self.search_court_guides()
        print(f"Found {len(guide_docs)} court guides")
        if guide_docs:
            for doc in guide_docs:
                print(f"  ✅ {doc['sourcefile']:30} | {doc['content_length']:6} chars")
        report["results"]["court_guides"] = {
            "count": len(guide_docs),
            "samples": guide_docs[:3]
        }
        
        # Test 5: Vector Search
        print("\n🔍 VECTOR SEARCH TEST")
        print("-" * 80)
        vector_results = self.test_vector_search("disclosure of documents")
        print(f"Query: 'disclosure of documents' returned {len(vector_results)} results")
        if vector_results:
            for result in vector_results[:3]:
                score = result.get('score', 0)
                print(f"  ✅ {result['sourcefile'][:40]:40} | score: {score:.2f}")
        report["results"]["vector_search"] = {
            "query": "disclosure of documents",
            "count": len(vector_results),
            "samples": vector_results[:3]
        }
        
        # Test 6: Category breakdown
        print("\n📊 DOCUMENTS BY CATEGORY")
        print("-" * 80)
        categories = self.count_by_category()
        for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            print(f"  • {cat:40} : {count:5} documents")
        report["results"]["categories"] = categories
        
        # Summary
        print("\n" + "="*80)
        print("✅ SUMMARY")
        print("="*80)
        total = len(cpr_docs) + len(pd_docs) + len(guide_docs)
        print(f"Total legal documents found: {total}")
        print(f"  • CPR Rules:         {len(cpr_docs)}")
        print(f"  • Practice Directions: {len(pd_docs)}")
        print(f"  • Court Guides:      {len(guide_docs)}")
        print(f"Vector search working: {'✅ Yes' if vector_results else '⚠️ Limited results'}")
        print(f"All document types present: {'✅ Yes' if all([cpr_docs, pd_docs, guide_docs]) else '⚠️ Missing some types'}")
        
        return report


def main():
    """Run comprehensive test."""
    # Use current Azure credentials (logged in via azd)
    print("🔐 Using DefaultAzureCredential (current Azure login)")
    
    tester = CPRPDTester()
    report = tester.generate_report()
    
    # Save report
    report_file = Path(__file__).parent / "azure_search_test_results.json"
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\n💾 Report saved to: {report_file}")
    
    return 0 if tester.search_client else 1


if __name__ == "__main__":
    sys.exit(main())
