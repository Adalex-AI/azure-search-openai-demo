#!/usr/bin/env python
"""
Upload legal documents with embeddings to Azure Search.
Supports dry-run mode for validation and staging index uploads.

Usage:
    python upload_with_embeddings.py --input Upload [--dry-run] [--staging]
"""
import os
import sys
import json
import glob
import argparse
import logging
import hashlib
import time
import re
from pathlib import Path
from openai import AzureOpenAI, RateLimitError
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Add scripts to path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

from config import Config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def load_documents_from_files(input_dir: str) -> list:
    """Load all JSON documents from input directory."""
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

@retry(
    retry=retry_if_exception_type(RateLimitError),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    stop=stop_after_attempt(5)
)
def create_embeddings_with_retry(client, texts: list, model: str):
    """Create embeddings with automatic retry on rate limit errors."""
    return client.embeddings.create(input=texts, model=model)

def generate_embeddings(documents: list) -> list:
    """Generate embeddings for documents that are missing them."""
    
    docs_to_embed = [doc for doc in documents if not doc.get("embedding")]
    if not docs_to_embed:
        return documents
        
    logger.info(f"Generating embeddings for {len(docs_to_embed)} documents...")
    
    endpoint = Config.AZURE_OPENAI_SERVICE
    if not endpoint.startswith("https://"):
        endpoint = f"https://{endpoint}.openai.azure.com"
        
    deployment = Config.AZURE_OPENAI_EMB_DEPLOYMENT
    
    if Config.AZURE_OPENAI_KEY:
        client = AzureOpenAI(
            api_key=Config.AZURE_OPENAI_KEY,
            api_version="2023-05-15",
            azure_endpoint=endpoint,
            max_retries=3,  # Built-in retry mechanism
            timeout=120.0
        )
    else:
        token_provider = get_bearer_token_provider(
            DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
        )
        client = AzureOpenAI(
            azure_ad_token_provider=token_provider,
            api_version="2023-05-15",
            azure_endpoint=endpoint,
            max_retries=3,
            timeout=120.0
        )
        
    # Process in batches with aggressive rate limiting
    batch_size = 3  # Very small batches to minimize rate limit issues
    success_count = 0
    for i in range(0, len(docs_to_embed), batch_size):
        batch = docs_to_embed[i:i+batch_size]
        texts = [doc["content"].replace("\n", " ")[:8000] for doc in batch]  # Truncate to token limit
        
        try:
            response = create_embeddings_with_retry(client, texts, deployment)
            for j, data in enumerate(response.data):
                batch[j]["embedding"] = data.embedding
            success_count += len(batch)
            logger.info(f"✅ Generated embeddings: {success_count}/{len(docs_to_embed)} ({(success_count/len(docs_to_embed)*100):.1f}%)")
            
            # Aggressive rate limiting: wait longer between batches
            if i + batch_size < len(docs_to_embed):
                time.sleep(10)  # 10 second delay between batches
        except Exception as e:
            logger.error(f"❌ Error generating embeddings for batch {i//batch_size + 1}: {e}")
            logger.warning(f"Skipping {len(batch)} documents in this batch")
            
    logger.info(f"Embedding generation complete: {success_count}/{len(docs_to_embed)} successful")
    return documents

def sanitize_id(doc_id: str) -> str:
    """Sanitize document ID for Azure Search."""
    # Lowercase
    s = doc_id.lower()
    # Replace invalid chars with underscore
    s = re.sub(r'[^a-z0-9_\-=]', '_', s)
    # Remove duplicate underscores
    s = re.sub(r'_+', '_', s)
    # Strip leading/trailing underscores
    s = s.strip('_')
    return s

def map_document_to_schema(doc: dict) -> dict:
    """Map document to Azure Search schema."""
    doc_id = doc.get("id", "")
    sanitized_id = sanitize_id(doc_id)
    
    if doc_id != sanitized_id:
        logger.info(f"Sanitized ID: '{doc_id}' -> '{sanitized_id}'")
        
    return {
        "id": sanitized_id,
        "content": doc.get("content", ""),
        "embedding": doc.get("embedding", []),
        "category": doc.get("category", "Legal Document"),
        "sourcepage": doc.get("sourcepage", ""),
        "sourcefile": doc.get("sourcefile", ""),
        "storageUrl": doc.get("storageUrl", ""),
        "oids": doc.get("oids", []) if doc.get("oids") else [],
        "groups": doc.get("groups", []) if doc.get("groups") else [],
        "parent_id": doc.get("parent_id", ""),
    }

def validate_documents(documents: list) -> tuple[list, list]:
    """Validate documents before upload. Returns (valid, invalid)."""
    valid = []
    invalid = []
    
    for doc in documents:
        errors = []
        
        if not doc.get("id"):
            errors.append("Missing id")
        if not doc.get("content"):
            errors.append("Missing content")
        if "embedding" in doc and len(doc.get("embedding", [])) != Config.EMBEDDING_DIMENSIONS:
            errors.append(f"Embedding has wrong dimensions: {len(doc.get('embedding', []))} vs {Config.EMBEDDING_DIMENSIONS}")
        
        if errors:
            invalid.append((doc.get("id", "unknown"), errors))
        else:
            valid.append(map_document_to_schema(doc))
    
    return valid, invalid

def upload_to_azure_search(index_name: str, documents: list, batch_size: int = 100) -> int:
    """Upload documents to Azure Search."""
    try:
        from azure.search.documents import SearchClient
        from azure.search.documents.indexes import SearchIndexClient
        from azure.core.credentials import AzureKeyCredential
        from azure.identity import DefaultAzureCredential
        from azure.core.exceptions import ResourceNotFoundError
        
        endpoint = Config.AZURE_SEARCH_SERVICE
        key = Config.AZURE_SEARCH_KEY
        
        if key:
            credential = AzureKeyCredential(key)
        else:
            logger.info("Using DefaultAzureCredential for authentication")
            credential = DefaultAzureCredential()
        
        if not endpoint:
            logger.error("Azure Search endpoint not configured")
            return 0
        
        # Verify index exists
        index_client = SearchIndexClient(endpoint=endpoint, credential=credential)
        try:
            index_client.get_index(index_name)
            logger.info(f"✅ Index '{index_name}' found")
        except ResourceNotFoundError:
            logger.error(f"❌ Index '{index_name}' does not exist")
            return 0
        
        # Upload documents in batches
        client = SearchClient(endpoint=endpoint, index_name=index_name, credential=credential)
        
        uploaded = 0
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i+batch_size]
            try:
                results = client.upload_documents(batch)
                successful = sum(1 for r in results if r.succeeded)
                uploaded += successful
                logger.info(f"Batch {i//batch_size + 1}: uploaded {successful}/{len(batch)} documents")
                time.sleep(0.5)  # Rate limiting
            except Exception as e:
                logger.error(f"Error uploading batch: {e}")
        
        logger.info(f"✅ Upload complete: {uploaded}/{len(documents)} documents")
        return uploaded
        
    except ImportError as e:
        logger.error(f"Azure SDK not available: {e}")
        return 0
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        return 0

def main():
    parser = argparse.ArgumentParser(description="Upload legal documents to Azure Search")
    parser.add_argument("--input", default="Upload", help="Input directory name (default: Upload)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be uploaded without uploading")
    parser.add_argument("--staging", action="store_true", help="Upload to staging index instead of production")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size for uploads")
    
    args = parser.parse_args()
    
    # Validate config
    is_valid, errors = Config.validate_azure_config()
    if not is_valid:
        logger.error("❌ Azure configuration incomplete:")
        for error in errors:
            logger.error(f"   - {error}")
        return 1
    
    # Load documents
    input_dir = os.path.join(Config.PROCESSED_DIR, args.input)
    if not os.path.isdir(input_dir):
        logger.error(f"Input directory not found: {input_dir}")
        return 1
    
    documents = load_documents_from_files(input_dir)
    if not documents:
        logger.error("No documents to upload")
        return 1
    
    # Generate embeddings if missing
    documents = generate_embeddings(documents)
    
    # Validate documents
    logger.info(f"\n📋 Validating {len(documents)} documents...")
    valid, invalid = validate_documents(documents)
    
    if invalid:
        logger.error(f"❌ {len(invalid)} documents failed validation:")
        for doc_id, errors in invalid[:10]:
            logger.error(f"   {doc_id}: {', '.join(errors)}")
        if len(invalid) > 10:
            logger.error(f"   ... and {len(invalid)-10} more")
    
    logger.info(f"✅ {len(valid)} documents passed validation")
    
    # Select target index
    target_index = Config.AZURE_SEARCH_INDEX_STAGING if args.staging else Config.AZURE_SEARCH_INDEX
    logger.info(f"📍 Target index: {target_index}")
    
    # Dry-run mode
    if args.dry_run:
        logger.info("\n🔍 DRY-RUN MODE (no documents uploaded)")
        logger.info(f"Would upload {len(valid)} documents to {target_index}")
        return 0
    
    # Upload
    logger.info(f"\n⬆️  Uploading {len(valid)} documents to {target_index}...")
    uploaded = upload_to_azure_search(target_index, valid, args.batch_size)
    
    if uploaded > 0:
        logger.info(f"\n✅ Success! {uploaded} documents uploaded")
        return 0
    else:
        logger.error("\n❌ Upload failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
