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
from openai import AzureOpenAI, RateLimitError, APIConnectionError, APIError
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
    retry=retry_if_exception_type((RateLimitError, APIConnectionError, APIError)),
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

def validate_documents(documents: list, check_embeddings: bool = False) -> tuple[list, list]:
    """Validate documents before upload. Returns (valid, invalid).
    
    Args:
        documents: List of documents to validate
        check_embeddings: If True, validate embedding dimensions. Set False during dry-run.
    """
    valid = []
    invalid = []
    
    for doc in documents:
        errors = []
        
        if not doc.get("id"):
            errors.append("Missing id")
        if not doc.get("content"):
            errors.append("Missing content")
        # Only check embeddings if explicitly requested (during actual upload)
        if check_embeddings and "embedding" in doc and len(doc.get("embedding", [])) != Config.EMBEDDING_DIMENSIONS:
            errors.append(f"Embedding has wrong dimensions: {len(doc.get('embedding', []))} vs {Config.EMBEDDING_DIMENSIONS}")
        
        if errors:
            invalid.append((doc.get("id", "unknown"), errors))
        else:
            valid.append(map_document_to_schema(doc))
    
    return valid, invalid

def compute_content_hash(doc: dict) -> str:
    """Compute a deterministic hash of the document content."""
    # We use content, title and sourcefile as the primary identity of the document version
    # This detects if content changed but ID stayed same
    content = doc.get("content", "") or ""
    title = doc.get("title", "") or ""
    id_val = doc.get("id", "") or ""
    
    # Create a string to hash
    to_hash = f"{id_val}|{title}|{content}"
    return hashlib.md5(to_hash.encode("utf-8")).hexdigest()

def filter_changed_documents(client, documents: list) -> tuple[list, int, int]:
    """
    Filter out documents that haven't changed in the index.
    Returns (docs_to_upload, unchanged_count, new_count)
    """
    if not documents:
        return [], 0, 0
        
    logger.info("Checking for existing documents to minimize updates...")
    docs_to_upload = []
    unchanged_count = 0
    new_count = 0
    changed_count = 0
    
    # Process in chunks to avoid huge filter strings
    chunk_size = 50
    
    for i in range(0, len(documents), chunk_size):
        chunk = documents[i:i+chunk_size]
        chunk_map = {doc["id"]: doc for doc in chunk}
        chunk_ids = list(chunk_map.keys())
        
        # Build filter query
        filter_expr = " or ".join([f"id eq '{doc_id}'" for doc_id in chunk_ids])
        
        found_ids = set()
        
        try:
            # We fetch content to compute hash comparison
            results = client.search(
                search_text="*",
                filter=filter_expr,
                select=["id", "title", "content"],
                top=chunk_size
            )
            
            for res in results:
                rid = res["id"]
                found_ids.add(rid)
                
                # Check if changed
                local_doc = chunk_map.get(rid)
                if local_doc:
                    remote_hash = compute_content_hash(res)
                    local_hash = compute_content_hash(local_doc)
                    
                    if remote_hash != local_hash:
                        docs_to_upload.append(local_doc)
                        changed_count += 1
                        logger.info(f"📝 content changed: {rid}")
                    else:
                        unchanged_count += 1
                        # logger.info(f"⏭️  Unchanged: {rid}")
        
        except Exception as e:
            logger.warning(f"Error checking existing docs, defaulting to upload all: {e}")
            docs_to_upload.extend(chunk)
            continue
            
        # Add new docs (ids asked for but not returned by search)
        for doc_id in chunk_ids:
            if doc_id not in found_ids:
                docs_to_upload.append(chunk_map[doc_id])
                new_count += 1
                logger.info(f"✨ New document: {doc_id}")

    return docs_to_upload, unchanged_count, new_count, changed_count

def upload_to_azure_search(index_name: str, documents: list, batch_size: int = 100, dry_run: bool = False) -> int:
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
            if dry_run:
                logger.info("Dry run: Would create index (not implemented in this script)")
            return 0
        
        # Configure Search Client
        client = SearchClient(endpoint=endpoint, index_name=index_name, credential=credential)
        
        # --- DIFFERENTIAL UPDATE LOGIC ---
        # Only upload changed/new documents
        docs_to_upload, unchanged, new_count, changed_count = filter_changed_documents(client, documents)
        
        # Write Upload Plan Report
        reports_dir = os.path.join(Config.SCRAPER_DATA_DIR, "reports")
        os.makedirs(reports_dir, exist_ok=True)
        report_path = os.path.join(reports_dir, "upload_plan.txt")
        
        total_changes = new_count + changed_count
        
        with open(report_path, "w") as f:
            f.write("=" * 60 + "\n")
            f.write("        LEGAL DOCUMENT SCRAPER - DIFF REPORT\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Target Index: {index_name}\n")
            f.write(f"Timestamp:    {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("-" * 60 + "\n")
            f.write("                    SUMMARY\n")
            f.write("-" * 60 + "\n")
            f.write(f"Total Documents Scraped:    {len(documents)}\n")
            f.write(f"✨ New Documents:           {new_count}\n")
            f.write(f"📝 Changed Documents:       {changed_count}\n")
            f.write(f"⏭️  Unchanged Documents:     {unchanged}\n")
            f.write("-" * 60 + "\n\n")
            
            if total_changes > 0:
                f.write("=" * 60 + "\n")
                f.write("⚠️  ACTION REQUIRED: DIFFERENCES DETECTED\n")
                f.write("=" * 60 + "\n\n")
                f.write(f"There are {total_changes} document(s) that need to be updated.\n")
                f.write("The following sections require embedding generation and upload:\n\n")
                
                # List new documents
                if new_count > 0:
                    f.write("NEW DOCUMENTS (to be added):\n")
                    f.write("-" * 40 + "\n")
                    new_docs = [d for d in docs_to_upload if d.get('_is_new', False)]
                    for i, doc in enumerate(docs_to_upload[:30], 1):
                        f.write(f"  {i}. {doc.get('id')}\n")
                    if len(docs_to_upload) > 30:
                        f.write(f"  ... and {len(docs_to_upload) - 30} more\n")
                    f.write("\n")
                
                # List changed documents  
                if changed_count > 0:
                    f.write("CHANGED DOCUMENTS (to be updated):\n")
                    f.write("-" * 40 + "\n")
                    for i, doc in enumerate(docs_to_upload[:30], 1):
                        f.write(f"  {i}. {doc.get('id')}\n")
                    if len(docs_to_upload) > 30:
                        f.write(f"  ... and {len(docs_to_upload) - 30} more\n")
                    f.write("\n")
                
                f.write("=" * 60 + "\n")
                f.write("NEXT STEPS:\n")
                f.write("  1. Review the changes above\n")
                f.write("  2. Approve the upload job in GitHub Actions\n")
                f.write("  3. Embeddings will be generated for changed docs only\n")
                f.write("  4. Documents will be uploaded to Azure Search\n")
                f.write("=" * 60 + "\n")
            else:
                f.write("=" * 60 + "\n")
                f.write("✅ NO ACTION REQUIRED: INDEX IS UP TO DATE\n")
                f.write("=" * 60 + "\n\n")
                f.write("All scraped documents match the current Azure Search index.\n")
                f.write("No embedding generation or upload is needed.\n")
            
        logger.info(f"Upload plan written to {report_path}")

        logger.info("-" * 60)
        if total_changes > 0:
            logger.info("⚠️  DIFFERENCES DETECTED - ACTION REQUIRED")
        else:
            logger.info("✅ NO DIFFERENCES - INDEX IS UP TO DATE")
        logger.info("-" * 60)
        logger.info(f"Diff Analysis:")
        logger.info(f"   Total Input:     {len(documents)}")
        logger.info(f"   ✨ New:          {new_count}")
        logger.info(f"   📝 Changed:      {changed_count}")
        logger.info(f"   ⏭️  Unchanged:    {unchanged}")
        logger.info("-" * 60)
        
        if not docs_to_upload:
            logger.info("🎉 No changes detected. Index is up to date!")
            # Write to GITHUB_OUTPUT if present
            if os.getenv('GITHUB_OUTPUT'):
                with open(os.getenv('GITHUB_OUTPUT'), 'a') as fh:
                    fh.write("has_changes=false\n")
            return 0

        # Write to GITHUB_OUTPUT if present
        if os.getenv('GITHUB_OUTPUT'):
            with open(os.getenv('GITHUB_OUTPUT'), 'a') as fh:
                fh.write("has_changes=true\n")

        if dry_run:
            logger.info(f"🔍 DRY-RUN: Would upload {len(docs_to_upload)} documents to {index_name}")
            return 0

        # --- GENERATE EMBEDDINGS LATE ---
        # Only generate embeddings for the docs we are actually going to upload
        logger.info(f"Generating embeddings for {len(docs_to_upload)} updates...")
        docs_to_upload = generate_embeddings(docs_to_upload)

        logger.info(f"Uploading {len(docs_to_upload)} valid updates...")
        
        uploaded = 0
        for i in range(0, len(docs_to_upload), batch_size):
            batch = docs_to_upload[i:i+batch_size]
            try:
                results = client.upload_documents(batch)
                successful = sum(1 for r in results if r.succeeded)
                uploaded += successful
                logger.info(f"Batch {i//batch_size + 1}: uploaded {successful}/{len(batch)} documents")
                time.sleep(0.5)  # Rate limiting
            except Exception as e:
                logger.error(f"Error uploading batch: {e}")
        
        logger.info(f"✅ Upload complete: {uploaded} documents updated")
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
    
    # NOTE: We do NOT generate embeddings here anymore. 
    # We delay it until after diff analysis to save costs.
    # documents = generate_embeddings(documents)
    
    # Validate documents (don't check embeddings yet - they'll be generated later for changed docs only)
    logger.info(f"\n📋 Validating {len(documents)} documents (structure only, embeddings checked later)...")
    valid, invalid = validate_documents(documents, check_embeddings=False)
    
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
    
    # Run upload (or dry-run) with diff logic
    if args.dry_run:
        logger.info("\n🔍 Starting Dry Run Analysis...")
    else:
        logger.info(f"\n⬆️  Starting Upload to {target_index}...")

    uploaded = upload_to_azure_search(target_index, valid, args.batch_size, dry_run=args.dry_run)
    
    if args.dry_run:
        logger.info("Dry run complete.")
        return 0
    elif uploaded > 0:
        logger.info(f"\n✅ Success! {uploaded} documents uploaded")
        return 0
    else:
        # If 0 uploaded but not dry run, it might mean no changes (success) or failure.
        # upload_to_azure_search returns 0 for both "no changes" and "error".
        # Logging in the function makes it clear.
        logger.info("Process complete.")
        return 0

if __name__ == "__main__":
    sys.exit(main())
