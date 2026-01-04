#!/usr/bin/env python
"""
Script to upload legal document chunks with embeddings to Azure Search.
Only uploads files that have changed since last upload.
Uses Azure SDK with Azure Identity authentication.
"""
import os
import sys
import argparse
import json
import logging
import glob
import hashlib
import time
import base64
from pathlib import Path

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

# Try to import config and Azure SDK
try:
    from src.config import Config, PROCESSED_DIR
except ImportError as e:
    print(f"ERROR: Cannot import configuration: {e}")
    print("Please ensure you're running this script from the project root directory.")
    print("Current working directory:", os.getcwd())
    print("Script location:", os.path.abspath(__file__))
    sys.exit(1)

# Azure SDK imports
try:
    from azure.search.documents.indexes import SearchIndexClient
    from azure.search.documents import SearchClient
    from azure.identity import DefaultAzureCredential, AzureCliCredential, ChainedTokenCredential
    from azure.core.credentials import AzureKeyCredential
    from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError, HttpResponseError

    # If the above import fails, ensure azure-search-documents is installed/upgraded:
    # pip install --upgrade azure-search-documents
except ImportError as e:
    print(f"ERROR: Missing required Azure SDK packages: {e}")
    print("\nPlease install the required packages:")
    print("pip install azure-search-documents azure-identity azure-core")
    sys.exit(1)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create a cache directory if it doesn't exist
CACHE_DIR = os.path.join(project_root, "data", "cache")
os.makedirs(CACHE_DIR, exist_ok=True)
UPLOAD_CACHE_FILE = os.path.join(CACHE_DIR, "upload_hashes.json")

def get_search_credentials():
    """Get Azure Search credentials using Azure best practices."""
    try:
        from azure.identity import DefaultAzureCredential
        from azure.core.credentials import AzureKeyCredential
        
        endpoint = Config.AZURE_SEARCH_SERVICE
        
        # Azure best practice: Try Azure Identity first
        try:
            credential = DefaultAzureCredential()
            # Test the credential
            from azure.search.documents.indexes import SearchIndexClient
            test_client = SearchIndexClient(endpoint=endpoint, credential=credential)
            list(test_client.list_indexes())  # This will fail if credential doesn't work
            
            logger.info("✅ Using Azure Identity (Best Practice)")
            return endpoint, credential
            
        except Exception:
            # Fallback to API key
            logger.info("Using API Key authentication")
            return endpoint, AzureKeyCredential(Config.AZURE_SEARCH_KEY)
            
    except Exception as e:
        logger.error(f"Authentication setup failed: {e}")
        raise

def load_upload_cache():
    """Load the file upload hash cache from disk."""
    try:
        if os.path.exists(UPLOAD_CACHE_FILE):
            with open(UPLOAD_CACHE_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Could not load upload hash cache: {e}")
    return {}

def save_upload_cache(upload_cache):
    """Save the file upload hash cache to disk."""
    try:
        with open(UPLOAD_CACHE_FILE, 'w') as f:
            json.dump(upload_cache, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save upload hash cache: {e}")

def compute_file_hash(file_path):
    """Compute a hash for a file based on its content and modification time."""
    try:
        # Get file stats for size and modification time
        file_stats = os.stat(file_path)
        file_size = file_stats.st_size
        file_mtime = file_stats.st_mtime
        
        # For small files (< 1MB), hash the entire content
        if file_size < 1024 * 1024:
            with open(file_path, 'rb') as f:
                file_content = f.read()
                content_hash = hashlib.sha256(file_content).hexdigest()
        else:
            # For larger files, hash first 100KB + middle 100KB + last 100KB + metadata
            with open(file_path, 'rb') as f:
                head = f.read(102400)  # First 100KB
                
                # Move to the middle of the file
                f.seek(file_size // 2 - 51200)
                middle = f.read(102400)  # Middle 100KB
                
                # Move to near the end of the file
                f.seek(-102400, 2)
                tail = f.read(102400)  # Last 100KB
                
                content_hash = hashlib.sha256(head + middle + tail).hexdigest()
        
        # Combine content hash with metadata for a complete hash
        combined_hash = f"{content_hash}_{file_size}_{int(file_mtime)}"
        return hashlib.md5(combined_hash.encode()).hexdigest()
    
    except Exception as e:
        logger.error(f"Error computing hash for {file_path}: {e}")
        # Return a timestamp-based hash as fallback to force processing
        return f"error_hash_{int(time.time())}"

def file_has_changed(file_path, upload_cache):
    """Check if a file has changed since last upload."""
    current_hash = compute_file_hash(file_path)
    previous_hash = upload_cache.get(file_path)

    if previous_hash != current_hash:
        if previous_hash:
            logger.info(f"File hash changed since last upload: {file_path} (Previous: {previous_hash[:8]}..., Current: {current_hash[:8]}...). Marked for upload.")
        else:
            logger.info(f"File is new or not found in cache: {file_path}. Marked for upload.")
        upload_cache[file_path] = current_hash # Update cache with the new hash
        return True
    else:
        logger.info(f"File hash unchanged since last upload, skipping: {file_path} (Hash: {current_hash[:8]}...)")
        return False

def find_json_files(base_processed_dir, file_pattern):
    """
    Find JSON files based on the pattern.
    Updated to handle both flattened and regular JSON files.
    """
    logger.info(f"Base processed directory: {base_processed_dir}")
    logger.info(f"Input file pattern: {file_pattern}")
    
    # Handle different patterns
    if file_pattern.endswith("-flattened"):
        # Remove the -flattened suffix to get the actual directory name
        pattern_name = file_pattern.replace("-flattened", "")
        target_dir = os.path.join(base_processed_dir, pattern_name)
        
        if os.path.isdir(target_dir):
            # Look for files with _flattened suffix first
            glob_pattern = os.path.join(target_dir, "*_flattened.json")
            logger.info(f"Flattened files pattern detected. Using: {glob_pattern}")
            files = glob.glob(glob_pattern, recursive=False)
            
            if not files:
                logger.warning(f"No flattened files found. Looking for all JSON files in: {target_dir}")
                # Fallback to all JSON files in the directory
                glob_pattern = os.path.join(target_dir, "*.json")
                files = glob.glob(glob_pattern, recursive=False)
        else:
            logger.error(f"Directory not found: {target_dir}")
            return []
    else:
        # Direct pattern matching
        if file_pattern == "Upload":
            # Special case for Upload directory - get all JSON files
            target_dir = os.path.join(base_processed_dir, "Upload")
            glob_pattern = os.path.join(target_dir, "*.json")
            logger.info(f"Upload directory pattern. Using: {glob_pattern}")
        else:
            # Look for specific pattern
            glob_pattern = os.path.join(base_processed_dir, f"{file_pattern}*.json")
            logger.info(f"Specific pattern. Using: {glob_pattern}")
        
        files = glob.glob(glob_pattern, recursive=False)
    
    logger.info(f"Using glob pattern: {glob_pattern} (Recursive: False)")
    
    # Filter out non-JSON files and summary files if needed
    json_files = [f for f in files if f.endswith('.json') and not f.endswith('_summary.json')]
    
    if not json_files:
        logger.warning(f"No files found matching pattern: {file_pattern} (resolved to: {glob_pattern})")
        
        # Debug: List directory contents
        if file_pattern.endswith("-flattened"):
            debug_dir = os.path.join(base_processed_dir, file_pattern.replace("-flattened", ""))
        else:
            debug_dir = os.path.join(base_processed_dir, file_pattern) if file_pattern != "Upload" else os.path.join(base_processed_dir, "Upload")
            
        logger.info(f"Listing contents of directory for debugging: {debug_dir}")
        try:
            if os.path.exists(debug_dir):
                contents = os.listdir(debug_dir)
                json_contents = [f for f in contents if f.endswith('.json')]
                logger.info(f"  JSON files found: {json_contents}")
                
                # If we found JSON files but none matched our pattern, use them all
                if json_contents and not json_files:
                    logger.info("Using all JSON files found in directory")
                    json_files = [os.path.join(debug_dir, f) for f in json_contents if not f.endswith('_summary.json')]
            else:
                logger.error(f"Directory does not exist: {debug_dir}")
                
        except Exception as e:
            logger.error(f"Error listing directory contents: {e}")
    
    logger.info(f"Found {len(json_files)} matching files.")
    return json_files

def validate_index_exists(index_name):
    """
    Validate that the specified index exists in Azure Search using Azure SDK.
    """
    try:
        # Get credentials using Azure Identity
        search_endpoint, credential = get_search_credentials()
        
        # Create index client
        index_client = SearchIndexClient(search_endpoint, credential)
        
        # Try to get the index
        index_data = index_client.get_index(index_name)
        logger.info(f"Index '{index_name}' exists and is accessible.")
        
        # Validate vector field exists
        fields = index_data.fields
        vector_fields = [f for f in fields if f.name == 'embedding']
        if vector_fields:
            vector_field = vector_fields[0]
            dimensions = getattr(vector_field, 'vector_search_dimensions', 'unknown')
            logger.info(f"Vector field 'embedding' found with {dimensions} dimensions")
        else:
            logger.warning("No 'embedding' field found in index")
        
        return True
        
    except ResourceNotFoundError:
        logger.error(f"Index '{index_name}' does not exist.")
        logger.info(f"Create it first using:")
        logger.info(f"python scripts/indexing/create_index.py --index {index_name} --recreate")
        return False
    except HttpResponseError as e:
        logger.error(f"Azure Search API error: {e}")
        if e.status_code == 403:
            logger.info("Authentication failed. Check your Azure Search permissions.")
        return False
    except Exception as e:
        logger.error(f"Index '{index_name}' validation failed: {e}")
        logger.info("Check your Azure Search service endpoint and credentials.")
        return False

def load_documents_from_file(file_path):
    """Load documents from a JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle both array and single document formats
        if isinstance(data, list):
            return data
        else:
            return [data]
    except Exception as e:
        logger.error(f"Error loading {file_path}: {e}")
        return []

def verify_embeddings(documents):
    """
    Verify that documents have embeddings.
    
    Args:
        documents: List of document dictionaries
        
    Returns:
        tuple: (documents with embeddings, documents missing embeddings)
    """
    with_embeddings = []
    missing_embeddings = []
    
    for doc in documents:
        if "chunk_vector" in doc and doc["chunk_vector"]:
            with_embeddings.append(doc)
        else:
            missing_embeddings.append(doc)
    
    return with_embeddings, missing_embeddings

def sanitize_keys(documents, method='simple', key_field='id'):
    """Sanitizes document keys for Azure Search compatibility."""
    sanitized_documents = []
    logger.debug(f"Sanitizing keys for {len(documents)} documents using method '{method}' on field '{key_field}'")
    for i, doc in enumerate(documents):
        doc_copy = doc.copy()
        if key_field not in doc_copy:
            logger.warning(f"Document at index {i} missing key field '{key_field}'. Skipping sanitization for this doc.")
            sanitized_documents.append(doc_copy)
            continue

        original_key = str(doc_copy[key_field])
        
        # Use simple sanitization instead of base64 for better readability
        if method == 'simple':
            # Replace problematic characters but keep it readable
            sanitized_key = ''.join(c if c.isalnum() or c in '_-' else '_' for c in original_key)
            # Ensure it doesn't start with underscore
            if sanitized_key.startswith('_'):
                sanitized_key = 'doc' + sanitized_key
            # Ensure it's not too long (Azure Search key limit is 1024 chars)
            if len(sanitized_key) > 900:
                sanitized_key = sanitized_key[:900] + '_' + str(hash(original_key))[-8:]
        else:
            # Fallback to base64 if needed
            try:
                sanitized_key = base64.urlsafe_b64encode(original_key.encode('utf-8')).rstrip(b'=').decode('utf-8')
            except Exception as e:
                logger.error(f"Base64 encoding failed for key '{original_key}': {e}. Using original key.")
                sanitized_key = original_key

        if sanitized_key != original_key:
            logger.debug(f"Sanitized key ({method}): '{original_key}' -> '{sanitized_key}'")

        doc_copy[key_field] = sanitized_key
        sanitized_documents.append(doc_copy)

    return sanitized_documents

def map_legal_doc_to_standard_schema(doc):
    """Map legal document fields to Azure Search OpenAI demo compatible schema."""
    # Extract and preserve existing values, don't override with defaults
    existing_category = doc.get("category", "")
    existing_sourcepage = doc.get("sourcepage", "")
    existing_sourcefile = doc.get("sourcefile", "")
    existing_storage_url = doc.get("storageUrl", "")
    
    mapped_doc = {
        # Core Azure Search OpenAI demo fields - preserve existing values
        "id": doc.get("id", "unknown_doc"),
        "content": doc.get("content", ""),
        "embedding": doc.get("embedding", []),
        
        # Preserve existing category - don't override with default
        "category": existing_category if existing_category else "Legal Document",
        
        # Preserve existing sourcepage - don't override with default  
        "sourcepage": existing_sourcepage if existing_sourcepage else "Unknown Section",
        
        # Preserve existing sourcefile - don't override with default
        "sourcefile": existing_sourcefile if existing_sourcefile else "Unknown Document",
        
        # Preserve existing storage URL
        "storageUrl": existing_storage_url,
        
        # Handle arrays properly - ensure they're not None
        "oids": doc.get("oids", []) if doc.get("oids") is not None else [],
        "groups": doc.get("groups", []) if doc.get("groups") is not None else [],
        "parent_id": doc.get("parent_id", ""),
        "updated": doc.get("updated", "2024-01-01T00:00:00Z")
    }
    
    # Ensure content is not empty
    if not mapped_doc["content"]:
        mapped_doc["content"] = f"Legal document: {mapped_doc['sourcefile']} - {mapped_doc['sourcepage']}"
    
    # Remove None values but keep empty strings and empty arrays
    cleaned_doc = {}
    for k, v in mapped_doc.items():
        if v is not None:
            cleaned_doc[k] = v
    
    return cleaned_doc

def upload_documents(index_name, documents, batch_size=1000):
    """Enhanced document upload using Azure SDK with better error handling and progress tracking."""
    try:
        # Get credentials using Azure Identity
        search_endpoint, credential = get_search_credentials()
        
        # Create search client for document operations
        search_client = SearchClient(search_endpoint, index_name, credential)
        
        batch_count = 0
        batch = []
        total_uploaded = 0
        total_docs = len(documents)
        logger.info(f"Starting upload of {total_docs} documents...")

        for i, doc in enumerate(documents):
            batch.append(doc)
            
            if len(batch) >= batch_size or (i + 1) == total_docs:
                batch_count += 1
                logger.info(f"Uploading batch {batch_count} with {len(batch)} documents (Docs {total_uploaded + 1} to {i + 1}).")
                
                # Log first few IDs in the batch for tracing
                batch_ids = [d.get('id', 'MISSING_ID') for d in batch[:3]]
                logger.debug(f"Sample IDs in batch {batch_count}: {batch_ids}")
                
                try:
                    # Upload using Azure SDK
                    results = search_client.upload_documents(batch)
                    
                    # Analyze results
                    successful_uploads = sum(1 for result in results if result.succeeded)
                    failed_uploads = len(batch) - successful_uploads
                    total_uploaded += successful_uploads
                    
                    logger.info(f"Batch {batch_count} complete: {successful_uploads} succeeded, {failed_uploads} failed")
                    
                    # Log errors in detail
                    if failed_uploads > 0:
                        errors = [result for result in results if not result.succeeded]
                        for error_result in errors[:3]:  # Show first 3 errors
                            logger.error(f"  Failed ID: {error_result.key}")
                            logger.error(f"  Status: {error_result.status_code}")
                            logger.error(f"  Message: {error_result.error_message}")
                        
                        if len(errors) > 3:
                            logger.error(f"  ... and {len(errors) - 3} more errors in this batch")

                except Exception as e:
                    logger.error(f"Exception uploading batch {batch_count}: {e}")
                    
                    # Provide specific error guidance
                    if "413" in str(e):
                        logger.info("Batch too large. Try reducing --batch-size parameter")
                    elif "429" in str(e):
                        logger.info("Rate limited. Waiting before retry...")
                        time.sleep(5)
                    elif "400" in str(e):
                        logger.info("Bad request. Check document format and field mappings")
                    
                    # Log sample document structure for debugging
                    if batch:
                        sample_doc = batch[0]
                        logger.debug(f"Sample document structure: {list(sample_doc.keys())}")

                batch = []  # Reset batch

        logger.info(f"Upload complete: {total_uploaded}/{total_docs} documents uploaded successfully")
        return total_uploaded
        
    except Exception as e:
        logger.error(f"Failed to upload documents: {e}")
        return 0

def compute_document_fingerprint(doc):
    """
    Compute a fingerprint for document content to identify duplicates.
    Uses relevant fields that determine document uniqueness, excluding the 'id'.

    Args:
        doc: Document dictionary

    Returns:
        str: Document fingerprint as hash
    """
    content_fields = ['content', 'chunk_content', 'text', 'chunk']
    metadata_fields = ['title', 'source', 'case_number', 'document_type', 'section_title', 'parent_id', 'chunk_id']

    content = ""
    for field in content_fields:
        if field in doc and doc[field]:
            content = str(doc[field])
            break

    metadata = ""
    for field in metadata_fields:
        if field in doc and doc[field]:
            metadata += str(doc[field]) + "|"

    fingerprint_str = f"{content}||{metadata}"
    return hashlib.md5(fingerprint_str.encode('utf-8')).hexdigest()

def find_duplicates_in_azure_search(index_name, local_documents=None):
    """
    Find duplicate documents within Azure Search or between local documents and Azure Search using Azure SDK.
    """
    logger.info("Checking for duplicates in Azure Search index...")
    
    try:
        # Get credentials using Azure Identity
        search_endpoint, credential = get_search_credentials()
        
        # Create search client for document operations
        search_client = SearchClient(search_endpoint, index_name, credential)
        
        azure_docs = []
        
        # Get all documents from the index
        try:
            results = search_client.search(
                search_text="*",
                select=["id", "content", "title", "category", "sourcefile"],
                include_total_count=True,
                top=1000
            )
            
            # Process results in batches
            for result in results:
                azure_docs.append(result)
                
        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")
            return {"azure_duplicates": {}, "local_vs_azure_duplicates": {}}
        
        logger.info(f"Retrieved {len(azure_docs)} documents from Azure Search")
        
        azure_fingerprints = {}
        azure_duplicates = {}
        
        for doc in azure_docs:
            fingerprint = compute_document_fingerprint(doc)
            
            if fingerprint not in azure_fingerprints:
                azure_fingerprints[fingerprint] = []
            
            azure_fingerprints[fingerprint].append({
                "id": doc.get("id", "unknown"),
                "title": doc.get("title", ""),
                "content_preview": doc.get("content", "")[:100] if doc.get("content") else ""
            })
            
            if len(azure_fingerprints[fingerprint]) > 1:
                azure_duplicates[fingerprint] = azure_fingerprints[fingerprint]
        
        local_vs_azure_duplicates = {}
        
        if local_documents:
            logger.info(f"Comparing {len(local_documents)} local documents against Azure Search...")
            
            for doc in local_documents:
                fingerprint = compute_document_fingerprint(doc)
                
                if fingerprint in azure_fingerprints:
                    local_vs_azure_duplicates[fingerprint] = {
                        "local_doc": {
                            "id": doc.get("id", "unknown"),
                            "title": doc.get("title", ""),
                            "content_preview": doc.get("content", "")[:100] if doc.get("content") else ""
                        },
                        "azure_docs": azure_fingerprints[fingerprint]
                    }
        
        return {
            "azure_duplicates": azure_duplicates,
            "local_vs_azure_duplicates": local_vs_azure_duplicates
        }
        
    except ResourceNotFoundError:
        logger.error(f"Index '{index_name}' not found.")
        return {"azure_duplicates": {}, "local_vs_azure_duplicates": {}}
    except Exception as e:
        logger.error(f"Error checking duplicates: {e}")
        return {"azure_duplicates": {}, "local_vs_azure_duplicates": {}}

def generate_duplicates_report(duplicates):
    """
    Generate a human-readable report of duplicate documents.
    
    Args:
        duplicates: Dict containing duplicate information
        
    Returns:
        str: Formatted report
    """
    report = []
    
    if duplicates["azure_duplicates"]:
        report.append("\n=== DUPLICATES WITHIN AZURE SEARCH ===")
        report.append(f"Found {len(duplicates['azure_duplicates'])} sets of duplicate documents:")
        
        for i, (fingerprint, docs) in enumerate(duplicates["azure_duplicates"].items(), 1):
            report.append(f"\nDuplicate Set #{i} (fingerprint: {fingerprint[:8]}...):")
            report.append(f"Found {len(docs)} duplicate documents with the same content:")
            
            for j, doc in enumerate(docs, 1):
                content_preview = doc["content_preview"]
                if len(content_preview) > 50:
                    content_preview = content_preview[:50] + "..."
                
                report.append(f"  {j}. ID: {doc['id']}")
                report.append(f"     Title: {doc['title']}")
                report.append(f"     Preview: {content_preview}")
    else:
        report.append("\n=== NO DUPLICATES FOUND WITHIN AZURE SEARCH ===")
    
    if "local_vs_azure_duplicates" in duplicates and duplicates["local_vs_azure_duplicates"]:
        report.append("\n=== LOCAL FILES DUPLICATED IN AZURE SEARCH ===")
        report.append(f"Found {len(duplicates['local_vs_azure_duplicates'])} local documents duplicated in Azure Search:")
        
        for i, (fingerprint, info) in enumerate(duplicates["local_vs_azure_duplicates"].items(), 1):
            local_doc = info["local_doc"]
            azure_docs = info["azure_docs"]
            
            local_preview = local_doc["content_preview"]
            if len(local_preview) > 50:
                local_preview = local_preview[:50] + "..."
            
            report.append(f"\nDuplicate #{i} (fingerprint: {fingerprint[:8]}...):")
            report.append(f"Local document:")
            report.append(f"  ID: {local_doc['id']}")
            report.append(f"  Title: {local_doc['title']}")
            report.append(f"  Preview: {local_preview}")
            
            report.append(f"Duplicate in Azure Search ({len(azure_docs)} instances):")
            for j, doc in enumerate(azure_docs, 1):
                report.append(f"  {j}. ID: {doc['id']}")
    elif "local_vs_azure_duplicates" in duplicates:
        report.append("\n=== NO LOCAL FILES DUPLICATED IN AZURE SEARCH ===")
    
    return "\n".join(report)

def delete_duplicate_documents(index_name, duplicates, strategy="keep_first"):
    """
    Delete duplicate documents from Azure Search using Azure SDK.
    """
    logger.info(f"Deleting duplicate documents using strategy: {strategy}")
    
    try:
        # Get credentials using Azure Identity
        search_endpoint, credential = get_search_credentials()
        
        # Create search client for document operations
        search_client = SearchClient(search_endpoint, index_name, credential)
        
        docs_to_delete = []
        
        for fingerprint, docs in duplicates["azure_duplicates"].items():
            if len(docs) <= 1:
                continue
                
            if strategy == "keep_first":
                docs_to_delete.extend([doc["id"] for doc in docs[1:]])
            elif strategy == "keep_last":
                docs_to_delete.extend([doc["id"] for doc in docs[:-1]])
        
        deleted_count = 0
        batch_size = 100
        
        for i in range(0, len(docs_to_delete), batch_size):
            batch = docs_to_delete[i:i+batch_size]
            
            try:
                delete_docs = [{"id": doc_id} for doc_id in batch]
                results = search_client.delete_documents(delete_docs)
                
                success_count = sum(1 for r in results if r.succeeded)
                deleted_count += success_count
                
                logger.info(f"Deleted batch {i//batch_size + 1}: {success_count} documents")
                
                time.sleep(0.2)
                
            except Exception as e:
                logger.error(f"Error deleting batch starting at index {i}: {e}")
        
        logger.info(f"Total documents deleted: {deleted_count}")
        return deleted_count
        
    except Exception as e:
        logger.error(f"Failed to delete duplicate documents: {e}")
        return 0

def map_legal_doc_to_standard_schema(doc):
    """Map legal document fields to Azure Search OpenAI demo compatible schema."""
    # Extract and preserve existing values, don't override with defaults
    existing_category = doc.get("category", "")
    existing_sourcepage = doc.get("sourcepage", "")
    existing_sourcefile = doc.get("sourcefile", "")
    existing_storage_url = doc.get("storageUrl", "")
    
    mapped_doc = {
        # Core Azure Search OpenAI demo fields - preserve existing values
        "id": doc.get("id", "unknown_doc"),
        "content": doc.get("content", ""),
        "embedding": doc.get("embedding", []),
        
        # Preserve existing category - don't override with default
        "category": existing_category if existing_category else "Legal Document",
        
        # Preserve existing sourcepage - don't override with default  
        "sourcepage": existing_sourcepage if existing_sourcepage else "Unknown Section",
        
        # Preserve existing sourcefile - don't override with default
        "sourcefile": existing_sourcefile if existing_sourcefile else "Unknown Document",
        
        # Preserve existing storage URL
        "storageUrl": existing_storage_url,
        
        # Handle arrays properly - ensure they're not None
        "oids": doc.get("oids", []) if doc.get("oids") is not None else [],
        "groups": doc.get("groups", []) if doc.get("groups") is not None else [],
        "parent_id": doc.get("parent_id", ""),
        "updated": doc.get("updated", "2024-01-01T00:00:00Z")
    }
    
    # Ensure content is not empty
    if not mapped_doc["content"]:
        mapped_doc["content"] = f"Legal document: {mapped_doc['sourcefile']} - {mapped_doc['sourcepage']}"
    
    # Remove None values but keep empty strings and empty arrays
    cleaned_doc = {}
    for k, v in mapped_doc.items():
        if v is not None:
            cleaned_doc[k] = v
    
    return cleaned_doc

def validate_document_schema(documents, index_name):
    """
    Validate and filter document fields against the actual index schema.
    Only keeps fields that exist in the target index.
    """
    try:
        # Get credentials and index schema
        search_endpoint, credential = get_search_credentials()
        index_client = SearchIndexClient(search_endpoint, credential)
        index_schema = index_client.get_index(index_name)
        
        # Get valid field names from the index
        valid_fields = set(field.name for field in index_schema.fields)
        logger.info(f"Valid fields in index '{index_name}': {sorted(valid_fields)}")
        
        # Filter documents to only include valid fields
        filtered_documents = []
        for doc in documents:
            filtered_doc = {k: v for k, v in doc.items() if k in valid_fields}
            
            # Log removed fields for debugging
            removed_fields = set(doc.keys()) - valid_fields
            if removed_fields:
                logger.debug(f"Removed invalid fields from document {doc.get('id', 'unknown')}: {sorted(removed_fields)}")
            
            filtered_documents.append(filtered_doc)
        
        logger.info(f"✅ Filtered {len(documents)} documents to match index schema")
        return filtered_documents
        
    except Exception as e:
        logger.error(f"Failed to validate document schema: {e}")
        logger.warning("Proceeding with original documents - may cause upload errors")
        return documents

def validate_json_documents(documents, embedding_dim=3072):  # Updated default
    """
    Validate all documents before upload.
    Checks for required fields and correct embedding dimension.
    Returns (is_valid, error_messages)
    """
    errors = []
    for i, doc in enumerate(documents):
        doc_id = doc.get("id", f"doc_{i}")
        # Check required fields
        if "id" not in doc or not doc["id"]:
            errors.append(f"Document {i} missing 'id' field.")
        if "content" not in doc or not doc["content"]:
            errors.append(f"Document {doc_id} missing or empty 'content' field.")
        if "embedding" not in doc or not isinstance(doc["embedding"], list):
            errors.append(f"Document {doc_id} missing or invalid 'embedding' field.")
        elif len(doc["embedding"]) != embedding_dim:
            errors.append(f"Document {doc_id} embedding length {len(doc['embedding'])} != {embedding_dim}.")
    return (len(errors) == 0), errors

def process_file(file_path, index_name, batch_size=100, skip_missing_vectors=False, upload_cache=None, 
                check_azure_duplicates=False, force=False, embedding_dim=3072):  # Updated default
    """Enhanced file processing with field mapping to standard schema."""
    if upload_cache is None:
        upload_cache = {}
    
    # Only check hash if not forcing
    if not force and not file_has_changed(file_path, upload_cache):
        return 0, 0
    # If force, update the cache with the current hash so future runs are correct
    if force:
        upload_cache[file_path] = compute_file_hash(file_path)

    documents = load_documents_from_file(file_path)
    if not documents:
        logger.warning(f"No documents found in {file_path}")
        return 0, 0

    logger.info(f"Loaded {len(documents)} documents from {file_path}")
    
    # Enhanced document validation and mapping
    valid_documents = []
    invalid_count = 0
    
    for i, doc in enumerate(documents):
        if not isinstance(doc, dict):
            logger.warning(f"Document {i} is not a dictionary, skipping")
            invalid_count += 1
            continue
            
        if 'id' not in doc:
            logger.warning(f"Document {i} missing 'id' field, skipping")
            invalid_count += 1
            continue
        
        # Map to standard schema
        try:
            mapped_doc = map_legal_doc_to_standard_schema(doc)
            valid_documents.append(mapped_doc)
        except Exception as e:
            logger.warning(f"Failed to map document {i}: {e}")
            invalid_count += 1
            continue
    
    documents = valid_documents
    
    if invalid_count > 0:
        logger.warning(f"Skipped {invalid_count} invalid documents")
    
    logger.info(f"✅ Mapped {len(documents)} documents to Azure Search OpenAI demo schema")
    
    # Log sample document for debugging
    if documents:
        sample_doc = documents[0]
        logger.info(f"Sample document fields: {list(sample_doc.keys())}")
        logger.info(f"Sample ID: {sample_doc.get('id')}")
        logger.info(f"Sample category: {sample_doc.get('category')}")
        logger.info(f"Sample sourcepage: {sample_doc.get('sourcepage')}")
        logger.info(f"Sample sourcefile: {sample_doc.get('sourcefile')}")
    
    # Check for duplicates if requested
    if check_azure_duplicates:
        duplicates = find_duplicates_in_azure_search(index_name, documents)
        
        if duplicates["local_vs_azure_duplicates"]:
            logger.warning(f"Found {len(duplicates['local_vs_azure_duplicates'])} documents already in Azure Search")
            
            duplicate_ids = set()
            for info in duplicates["local_vs_azure_duplicates"].values():
                duplicate_ids.add(info["local_doc"]["id"])
            
            logger.info(f"Filtering out {len(duplicate_ids)} duplicate documents")
            documents = [doc for doc in documents if doc.get("id") not in duplicate_ids]
    
    # Verify embeddings using the mapped field name
    docs_with_vectors = [doc for doc in documents if doc.get("embedding") and len(doc.get("embedding", [])) > 0]
    docs_missing_vectors = [doc for doc in documents if not doc.get("embedding") or len(doc.get("embedding", [])) == 0]
    
    if docs_missing_vectors:
        logger.warning(f"{len(docs_missing_vectors)} documents missing embeddings")
        if skip_missing_vectors:
            logger.info(f"Skipping documents without embeddings")
            documents = docs_with_vectors
        else:
            logger.info(f"Including documents without embeddings (they won't be vector searchable)")
    
    if not documents:
        logger.warning(f"No valid documents to upload from {file_path}")
        return 0, 0
    
    # Sanitize keys before uploading - use simple method for readability
    documents = sanitize_keys(documents, method='simple')
    
    # Validate document schema against index before upload
    documents = validate_document_schema(documents, index_name)

    # --- Check embedding field dimension before upload ---
    wrong_dim_docs = []
    for doc in documents:
        emb = doc.get("embedding")
        if emb is not None and isinstance(emb, list) and len(emb) > 0 and len(emb) != embedding_dim:
            wrong_dim_docs.append((doc.get("id", "unknown"), len(emb)))
    if wrong_dim_docs:
        logger.error(f"❌ Found {len(wrong_dim_docs)} documents with incorrect embedding dimension (expected {embedding_dim}):")
        for doc_id, dim in wrong_dim_docs[:5]:
            logger.error(f"  Document {doc_id} embedding length: {dim}")
        logger.error("Aborting upload for this file due to embedding dimension mismatch.")
        return 0, len(documents)

    # --- DEBUG: Check embedding field before upload ---
    if documents:
        sample_doc = documents[0]
        logger.debug(f"Sample document keys before upload: {list(sample_doc.keys())}")
        embedding = sample_doc.get("embedding")
        logger.debug(f"Sample 'embedding' field type: {type(embedding)}, length: {len(embedding) if isinstance(embedding, list) else 'N/A'}")
        # Warn if embedding is missing or empty
        if embedding is None or (isinstance(embedding, list) and not embedding):
            logger.warning(f"Sample document is missing or has empty 'embedding' field before upload!")

    # Warn if any document is missing or has empty embedding
    for doc in documents:
        if "embedding" not in doc or not isinstance(doc["embedding"], list) or not doc["embedding"]:
            logger.warning(f"Document {doc.get('id', 'unknown')} is missing or has empty 'embedding' field before upload!")

    # Upload documents using REST API
    try:
        success_count = upload_documents(index_name, documents, batch_size)
        error_count = len(documents) - success_count
        
        return success_count, error_count
        
    except Exception as e:
        logger.error(f"Failed to upload documents: {e}")
        return 0, len(documents)

def upload_documents_with_embeddings(index_name, base_processed_dir, file_pattern, batch_size=100, 
                                    force_upload=False, embedding_model="text-embedding-3-large", 
                                    max_tokens=8191):
    """
    Upload documents with embeddings to Azure Search.
    
    Args:
        index_name: Name of the Azure Search index
        base_processed_dir: Base directory containing processed files
        file_pattern: Pattern to match files (e.g., "Upload", "Upload-flattened")
        batch_size: Number of documents to upload in each batch
        force_upload: Force upload even if files haven't changed
        embedding_model: OpenAI embedding model to use
        max_tokens: Maximum tokens per document
    """
    logger.info(f"Starting upload to index: {index_name}")
    logger.info(f"File pattern: {file_pattern}")
    logger.info(f"Base processed directory: {base_processed_dir}")
    
    # Find JSON files
    json_files = find_json_files(base_processed_dir, file_pattern)
    
    if not json_files:
        logger.error(f"No JSON files found matching pattern: {file_pattern}")
        return
    
    logger.info(f"Found {len(json_files)} JSON files to process")
    
    # Load upload cache
    upload_cache = load_upload_cache()
    
    total_success = 0
    total_errors = 0
    files_processed = 0
    
    try:
        for file_path in json_files:
            logger.info(f"📄 Processing file: {os.path.basename(file_path)}")
            
            success_count, error_count = process_file(
                file_path, 
                index_name, 
                batch_size, 
                skip_missing_vectors=False,
                upload_cache=upload_cache,
                check_azure_duplicates=False,
                force=force_upload
            )
            
            total_success += success_count
            total_errors += error_count
            files_processed += 1
            
            logger.info(f"✅ File complete: {success_count} uploaded, {error_count} errors")
            
            # Save cache after each file
            save_upload_cache(upload_cache)
            
    except KeyboardInterrupt:
        logger.info("\n🛑 Upload interrupted by user")
        save_upload_cache(upload_cache)
        return
    
    logger.info(f"\n🎉 Upload complete!")
    logger.info(f"📊 Summary: {files_processed} files processed, {total_success} documents uploaded, {total_errors} errors")

def main():
    parser = argparse.ArgumentParser(description="Upload legal document chunks with embeddings to Azure Search")
    parser.add_argument("--input", default="Upload-flattened", help="Input file pattern (e.g., 'Upload-flattened', 'Upload', 'civil_rules')")
    parser.add_argument("--index", default="legal-court-rag-index", help="Azure Search index name")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size for uploading")
    parser.add_argument("--processed-dir", help="Directory containing processed files")
    parser.add_argument("--skip-missing-vectors", action="store_true", help="Skip documents without vector embeddings")
    parser.add_argument("--force", action="store_true", help="Force upload even if file unchanged")
    parser.add_argument("--find-azure-duplicates", action="store_true", help="Find duplicate documents in Azure Search")
    parser.add_argument("--check-azure-duplicates", action="store_true", help="Check for duplicates in Azure before uploading")
    parser.add_argument("--delete-duplicates", choices=["keep_first", "keep_last"], help="Delete duplicate documents in Azure Search, keeping either first or last occurrence")
    parser.add_argument("--report-file", help="Save duplicate report to a file")
    parser.add_argument("--upload-flattened", action="store_true", help="Upload flattened files from Upload directory")
    
    args = parser.parse_args()
    
    # Handle upload-flattened flag
    if args.upload_flattened:
        args.input = "*_flattened.json"
    
    logger.info("🔄 Starting upload with Azure Search OpenAI demo compatible format")
    logger.info("🔐 Using Azure SDK with Azure Identity authentication")
    
    # Validate index exists
    if not validate_index_exists(args.index):
        logger.error(f"❌ Index validation failed for '{args.index}'")
        sys.exit(1)
    
    # Handle duplicate checking/deletion operations
    if args.find_azure_duplicates or args.delete_duplicates:
        duplicates = find_duplicates_in_azure_search(args.index)
        
        if duplicates["azure_duplicates"]:
            report = generate_duplicates_report(duplicates)
            print(report)
            
            if args.report_file:
                with open(args.report_file, 'w') as f:
                    f.write(report)
                logger.info(f"📄 Duplicate report saved to: {args.report_file}")
            
            if args.delete_duplicates:
                delete_duplicate_documents(args.index, duplicates, args.delete_duplicates)
        else:
            logger.info("✅ No duplicates found in Azure Search")
        
        return
    
    # Get the base processed directory
    base_processed_dir = args.processed_dir or os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "data", "processed"
    )
    
    # Use the new upload function
    upload_documents_with_embeddings(
        index_name=args.index,
        base_processed_dir=base_processed_dir,
        file_pattern=args.input,
        batch_size=args.batch_size,
        force_upload=args.force
    )

if __name__ == "__main__":
    sys.exit(main())