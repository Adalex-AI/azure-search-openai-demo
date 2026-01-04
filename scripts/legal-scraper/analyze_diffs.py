#!/usr/bin/env python
"""
Analyze differences between local fresh scrape and Azure Search index.
"""
import json
import sys
import difflib
from pathlib import Path
from azure.search.documents import SearchClient
from azure.identity import DefaultAzureCredential

class DiffAnalyzer:
    def __init__(self):
        credential = DefaultAzureCredential()
        self.search_client = SearchClient(
            endpoint="https://cpr-rag.search.windows.net",
            index_name="legal-court-rag-index",
            credential=credential
        )
        self.upload_dir = Path("/Users/HasithB/Downloads/PROJECTS/azure-search-openai-demo-2/data/legal-scraper/processed/Upload")

    def normalize_text(self, text: str) -> str:
        """Normalize text for comparison."""
        if not text:
            return ""
        # Remove carriage returns and normalize newlines
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        # Normalize whitespace
        lines = [line.strip() for line in text.split('\n')]
        return '\n'.join(line for line in lines if line)

    def analyze_file(self, filename: str):
        print(f"\n{'='*80}")
        print(f"Analyzing {filename}")
        print(f"{'='*80}")

        local_path = self.upload_dir / f"{filename}.json"
        if not local_path.exists():
            print(f"❌ Local file not found: {local_path}")
            return

        with open(local_path, 'r', encoding='utf-8') as f:
            local_doc = json.load(f)

        sourcefile = local_doc.get('sourcefile')
        print(f"Sourcefile: {sourcefile}")
        print(f"Local Updated Date: {local_doc.get('updated')}")

        # Fetch from Azure
        results = list(self.search_client.search(
            search_text="*",
            filter=f"sourcefile eq '{sourcefile}'",
            select=["id", "content", "updated", "sourcefile"]
        ))

        if not results:
            print("❌ Document NOT found in Azure Search.")
            return

        print(f"✅ Found {len(results)} chunks in Azure Search.")
        
        # Combine Azure chunks to reconstruct full content (approximation)
        # Or just compare the first chunk if IDs match
        
        # Let's try to find a matching chunk ID first
        azure_doc = None
        # Try exact ID match first (assuming chunk_001)
        target_id = f"{sourcefile}_chunk_001"
        
        # Check if local doc has chunks
        if 'chunks' in local_doc and local_doc['chunks']:
            local_content = local_doc['chunks'][0]['content']
            target_id = local_doc['chunks'][0]['id']
        else:
            local_content = local_doc.get('content', '')

        # Find corresponding Azure chunk
        for res in results:
            if res['id'] == target_id:
                azure_doc = res
                break
        
        if not azure_doc:
            print(f"⚠️ Exact chunk ID {target_id} not found in Azure. Using first result: {results[0]['id']}")
            azure_doc = results[0]

        print(f"Azure Updated Date: {azure_doc.get('updated')}")
        
        azure_content = azure_doc.get('content', '')
        
        norm_local = self.normalize_text(local_content)
        norm_azure = self.normalize_text(azure_content)

        if norm_local == norm_azure:
            print("✅ Content matches exactly (normalized).")
        else:
            print("⚠️ Content MISMATCH.")
            print("Generating diff (first 20 lines of diff)...")
            
            diff = difflib.unified_diff(
                norm_azure.splitlines(),
                norm_local.splitlines(),
                fromfile='Azure',
                tofile='Local (Fresh)',
                lineterm=''
            )
            
            for i, line in enumerate(diff):
                if i < 20:
                    print(line)
                else:
                    print("... (diff truncated)")
                    break

if __name__ == "__main__":
    print("Starting analysis script...")
    analyzer = DiffAnalyzer()
    # Analyze specific files of interest
    files_to_check = ["Part 52", "Part 44", "Part 6", "Part 48"]
    
    for f in files_to_check:
        analyzer.analyze_file(f)
