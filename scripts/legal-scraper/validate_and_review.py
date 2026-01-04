#!/usr/bin/env python
"""
Validate scraped JSON files and display changes against current Azure Search index.
Requires explicit user approval before proceeding with upload.

Usage:
    python validate_and_review.py --input Upload [--staging]
"""
import os
import sys
import json
import glob
import argparse
import logging
from pathlib import Path

# Add scripts to path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

from config import Config
from validation import DocumentValidator, ValidationReport

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class AzureSearchComparer:
    """Compare local JSON documents against Azure Search index."""
    
    def __init__(self, config):
        self.config = config
        self._init_search_client()
    
    def _init_search_client(self):
        """Initialize Azure Search client."""
        try:
            from azure.search.documents import SearchClient
            from azure.core.credentials import AzureKeyCredential
            
            endpoint = self.config.AZURE_SEARCH_SERVICE
            if not endpoint or not self.config.AZURE_SEARCH_KEY:
                raise ValueError("Azure Search credentials not configured")
            
            self.client = SearchClient(
                endpoint=endpoint,
                index_name=self.config.AZURE_SEARCH_INDEX,
                credential=AzureKeyCredential(self.config.AZURE_SEARCH_KEY)
            )
            logger.info(f"✅ Connected to Azure Search index: {self.config.AZURE_SEARCH_INDEX}")
        except Exception as e:
            logger.warning(f"⚠️  Could not connect to Azure Search: {e}")
            logger.warning("Continuing with validation only (no comparison)")
            self.client = None
    
    def get_document_count(self) -> int:
        """Get count of documents currently in index."""
        if not self.client:
            return 0
        try:
            results = self.client.search(search_text="*", top=1)
            return results.get_count()
        except Exception as e:
            logger.warning(f"Could not get document count: {e}")
            return 0
    
    def get_document_ids(self, limit: int = 10000) -> set:
        """Get all document IDs currently in index."""
        if not self.client:
            return set()
        try:
            results = self.client.search(search_text="*", top=limit, select=["id"])
            return {doc["id"] for doc in results}
        except Exception as e:
            logger.warning(f"Could not fetch document IDs: {e}")
            return set()
    
    def compare_documents(self, new_documents: list) -> dict:
        """
        Compare new documents against existing index.
        
        Returns:
            {
                "new": list of new document IDs,
                "updated": list of updated document IDs,
                "unchanged": list of unchanged document IDs,
                "index_count": current index document count,
                "new_count": count of new documents to upload
            }
        """
        if not self.client:
            return {
                "new": len(new_documents),
                "updated": 0,
                "unchanged": 0,
                "index_count": "unknown",
                "new_count": len(new_documents)
            }
        
        try:
            existing_ids = self.get_document_ids()
            index_count = self.get_document_count()
            
            new_ids = set()
            updated_ids = set()
            unchanged_ids = set()
            
            for doc in new_documents:
                doc_id = doc.get("id")
                if doc_id in existing_ids:
                    updated_ids.add(doc_id)
                else:
                    new_ids.add(doc_id)
            
            # Detect unchanged (not in new upload but in index)
            unchanged_ids = existing_ids - new_ids - updated_ids
            
            return {
                "new": list(new_ids),
                "new_count": len(new_ids),
                "updated": list(updated_ids),
                "updated_count": len(updated_ids),
                "unchanged": list(unchanged_ids),
                "unchanged_count": len(unchanged_ids),
                "index_count": index_count
            }
        except Exception as e:
            logger.error(f"Error comparing documents: {e}")
            return {
                "new": len(new_documents),
                "updated": 0,
                "unchanged": 0,
                "index_count": "error",
                "new_count": len(new_documents)
            }

def load_json_documents(input_dir: str) -> list:
    """Load all JSON files from input directory."""
    documents = []
    json_files = glob.glob(os.path.join(input_dir, "*.json"))
    
    logger.info(f"Found {len(json_files)} JSON files in {input_dir}")
    
    for json_file in sorted(json_files):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Handle both single document and array of documents
                if isinstance(data, list):
                    documents.extend(data)
                else:
                    documents.append(data)
                    
        except Exception as e:
            logger.error(f"Error loading {json_file}: {e}")
    
    logger.info(f"Loaded {len(documents)} documents from {len(json_files)} files")
    return documents

def prompt_for_approval(comparison: dict, validation_report: dict) -> bool:
    """Prompt user for approval to proceed with upload."""
    print("\n" + "="*70)
    print("REVIEW BEFORE UPLOAD")
    print("="*70)
    
    # Validation summary
    print(f"\n📋 VALIDATION SUMMARY:")
    print(f"   ✅ Passed: {validation_report['passed']}")
    print(f"   ❌ Failed: {validation_report['failed']}")
    if validation_report.get('duplicates'):
        print(f"   ⚠️  Duplicates: {len(validation_report['duplicates'])}")
    
    # Document changes
    print(f"\n📊 DOCUMENT CHANGES:")
    print(f"   📝 Current index: {comparison.get('index_count', '?')} documents")
    print(f"   ➕ New documents: {comparison.get('new_count', 0)}")
    print(f"   🔄 Updated documents: {comparison.get('updated_count', 0)}")
    
    # Validation failures require approval
    if validation_report['failed'] > 0:
        print(f"\n⚠️  WARNING: {validation_report['failed']} document(s) failed validation!")
        print("   Review the validation report above before proceeding.")
    
    # Show sample of new documents
    if comparison.get('new') and len(comparison['new']) <= 10:
        print(f"\n📌 New documents to be uploaded:")
        for doc_id in comparison['new'][:10]:
            print(f"   - {doc_id}")
    elif comparison.get('new_count', 0) > 10:
        print(f"\n📌 First 10 of {comparison.get('new_count')} new documents:")
        for doc_id in comparison.get('new', [])[:10]:
            print(f"   - {doc_id}")
    
    print("\n" + "="*70)
    
    if validation_report['failed'] > 0:
        response = input(
            "\n⚠️  VALIDATION FAILED - Type 'OVERRIDE' to proceed anyway, or 'ABORT': "
        ).strip().upper()
        return response == 'OVERRIDE'
    else:
        response = input(
            "\n✅ Ready to upload. Type 'APPROVE' to proceed, or 'ABORT': "
        ).strip().upper()
        return response == 'APPROVE'

def main():
    parser = argparse.ArgumentParser(
        description="Validate scraped JSON files and review against Azure Search"
    )
    parser.add_argument(
        "--input",
        default="Upload",
        help="Input directory name under data/legal-scraper/processed/ (default: Upload)"
    )
    parser.add_argument(
        "--staging",
        action="store_true",
        help="Compare against staging index instead of production"
    )
    parser.add_argument(
        "--no-approve",
        action="store_true",
        help="Run validation and comparison but don't prompt for approval"
    )
    
    args = parser.parse_args()
    
    # Validate config
    is_valid, errors = Config.validate_azure_config()
    if not is_valid:
        logger.error("❌ Azure configuration incomplete:")
        for error in errors:
            logger.error(f"   - {error}")
        logger.error("\nPlease configure using: azd env set <VAR> <VALUE>")
        return 1
    
    # Load documents
    input_dir = os.path.join(Config.PROCESSED_DIR, args.input)
    if not os.path.isdir(input_dir):
        logger.error(f"Input directory not found: {input_dir}")
        return 1
    
    documents = load_json_documents(input_dir)
    if not documents:
        logger.error("No documents to validate")
        return 1
    
    # Validate documents
    logger.info("\n📋 Running validation checks...")
    validator = DocumentValidator(Config)
    report_gen = ValidationReport(Config)
    validation_report = report_gen.generate_report(documents, validator)
    report_gen.print_report(validation_report)
    
    # Save validation report
    report_path = os.path.join(
        Config.VALIDATION_REPORT_DIR,
        f"validation_report_{Path(input_dir).name}.json"
    )
    report_gen.save_report(validation_report, report_path)
    
    # Compare against Azure Search
    logger.info("\n🔍 Comparing against Azure Search index...")
    comparer = AzureSearchComparer(Config)
    comparison = comparer.compare_documents(documents)
    
    print(f"\n📊 Index Comparison:")
    print(f"   Current index: {comparison.get('index_count', '?')} documents")
    print(f"   New: {comparison.get('new_count', 0)}")
    print(f"   Updated: {comparison.get('updated_count', 0)}")
    
    # Prompt for approval
    if args.no_approve:
        logger.info("✅ Validation complete (--no-approve flag set)")
        return 0
    
    approved = prompt_for_approval(comparison, validation_report)
    
    if not approved:
        logger.warning("❌ Upload cancelled")
        return 1
    
    logger.info("\n✅ Approved! You can now run the upload script:")
    logger.info(f"   python scripts/legal-scraper/upload_with_embeddings.py --input {args.input}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
