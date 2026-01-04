#!/usr/bin/env python
"""
Script to generate embeddings for legal document chunks using Azure OpenAI.
Enhanced to handle content_chunks structure and flatten documents properly.
Uses Azure SDK with Azure Identity authentication.
"""
import os
import sys
import json
import time
import argparse
import glob
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path and load environment variables FIRST
project_root = Path(__file__).parents[2]
sys.path.append(str(project_root))

# Load .env file explicitly and force reload
env_path = project_root / '.env'
print(f"🔎 Loading environment from: {env_path}")
load_dotenv(env_path, override=True)

# Azure SDK imports
try:
    from azure.identity import DefaultAzureCredential, AzureCliCredential, ChainedTokenCredential
    from azure.core.credentials import AzureKeyCredential
    from openai import AzureOpenAI
except ImportError as e:
    print(f"ERROR: Missing required Azure SDK packages: {e}")
    print("\nPlease install the required packages:")
    print("pip install azure-identity azure-core openai")
    sys.exit(1)

# Get configuration from environment variables
openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
openai_key = os.getenv("AZURE_OPENAI_KEY") 
openai_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
openai_api_version = os.getenv("AZURE_OPENAI_EMBEDDING_API_VERSION", "2024-06-01")

# For text-embedding-3-large, use 3072 dimensions for maximum precision
embedding_dimensions = int(os.getenv("AZURE_OPENAI_EMBEDDING_DIMENSIONS", "3072"))  # Updated default for text-embedding-3-large

# Validate configuration
print(f"🔎 Configuration loaded:")
print(f"   Endpoint: {openai_endpoint}")
print(f"   Deployment: {openai_deployment}")
print(f"   API Version: {openai_api_version}")
print(f"   Embedding Dimensions: {embedding_dimensions}")

if not openai_endpoint:
    print("❌ AZURE_OPENAI_ENDPOINT not found in environment")
    sys.exit(1)
if not openai_deployment:
    print("❌ AZURE_OPENAI_EMBEDDING_DEPLOYMENT not found in environment")
    sys.exit(1)

# Validate endpoint format - handle both Azure OpenAI and Azure AI Services
if not (openai_endpoint.endswith('.openai.azure.com') or openai_endpoint.endswith('.cognitiveservices.azure.com/')):
    print(f"❌ Invalid endpoint format: {openai_endpoint}")
    print("   Should end with '.openai.azure.com' or '.cognitiveservices.azure.com/'")
    sys.exit(1)

def get_openai_client():
    """
    Get Azure OpenAI client using Azure Identity with fallback to API key.
    
    Returns:
        AzureOpenAI: Configured client instance
    """
    # Try Azure Identity first (recommended approach)
    try:
        # Chain multiple credential types for better compatibility
        credential = ChainedTokenCredential(
            DefaultAzureCredential(),
            AzureCliCredential()
        )
        
        # Test the credential by creating a client
        client = AzureOpenAI(
            azure_endpoint=openai_endpoint,
            azure_ad_token_provider=credential,
            api_version=openai_api_version
        )
        
        # Test the client with a simple call
        test_response = client.embeddings.create(
            input=["test"],
            model=openai_deployment,
            dimensions=embedding_dimensions
        )
        
        print(f"✅ Successfully authenticated with Azure OpenAI using Azure Identity")
        return client
        
    except Exception as e:
        print(f"⚠️ Azure Identity authentication failed: {str(e)}")
        print("🔄 Falling back to API key authentication...")
        
        # Fallback to API key authentication
        if not openai_key:
            raise ValueError("No valid authentication method available. Please configure Azure Identity or provide AZURE_OPENAI_KEY.")
        
        try:
            client = AzureOpenAI(
                azure_endpoint=openai_endpoint,
                api_key=openai_key,
                api_version=openai_api_version
            )
            
            # Test the client
            test_response = client.embeddings.create(
                input=["test"],
                model=openai_deployment,
                dimensions=embedding_dimensions
            )
            
            print(f"✅ Successfully authenticated with Azure OpenAI using API key")
            return client
            
        except Exception as e:
            print(f"❌ API key authentication also failed: {e}")
            raise

# Initialize Azure OpenAI client
try:
    client = get_openai_client()
    print(f"✅ Azure OpenAI client initialized successfully")
    print(f"   Using endpoint: {openai_endpoint}")
    print(f"   Using deployment: {openai_deployment}")
except Exception as e:
    print(f"❌ Failed to initialize Azure OpenAI client: {e}")
    print("\nPlease ensure you have either:")
    print("1. Azure CLI logged in: az login")
    print("2. Valid API key in environment variable AZURE_OPENAI_KEY")
    print("3. Managed identity configured (if running in Azure)")
    sys.exit(1)

def generate(text):
    """Generate embeddings for the given text using Azure OpenAI."""
    if not text or not text.strip():
        return []
    
    try:
        resp = client.embeddings.create(
            input=[text], 
            model=openai_deployment,
            dimensions=embedding_dimensions  # This controls output vector size
        )
        return resp.data[0].embedding if resp.data else []
    except Exception as e:
        print(f"  ⚠ Error generating embedding: {e}")
        print(f"  ⚠ Using endpoint: {openai_endpoint}")
        print(f"  ⚠ Using deployment: {openai_deployment}")
        print(f"  ⚠ Using dimensions: {embedding_dimensions}")
        print("  ⚠ Verify deployment exists in Azure OpenAI Studio")
        return []

def extract_content_from_document(doc):
    """
    Extract content from a document optimized for legal documents.
    """
    # Primary content field for legal documents
    if 'content' in doc and doc['content']:
        content = str(doc['content']).strip()
        if content:
            # For legal documents, enhance content with metadata for better embeddings
            enhanced_content = content
            
            # Add legal context from metadata
            if doc.get('category'):
                enhanced_content = f"Legal Category: {doc['category']}\n\n{enhanced_content}"
            
            if doc.get('sourcepage'):
                enhanced_content = f"Section: {doc['sourcepage']}\n\n{enhanced_content}"
            
            return enhanced_content, 'content_enhanced'
    
    # Fallback content field names (for backward compatibility)
    content_fields = [
        'chunk', 'chunk_content', 'text', 'body', 
        'description', 'summary', 'paragraph_text', 'section_content'
    ]
    
    for field in content_fields:
        if field in doc and doc[field]:
            content = str(doc[field]).strip()
            if content:
                return content, field
    
    # Try nested structures
    if 'text' in doc and isinstance(doc['text'], dict):
        for field in content_fields:
            if field in doc['text'] and doc['text'][field]:
                content = str(doc['text'][field]).strip()
                if content:
                    return content, f"text.{field}"
    
    # Try to construct content from title + other fields
    title = doc.get('title', '').strip()
    if title:
        # For Azure Search OpenAI demo format, title might be supplementary
        sourcefile = doc.get('sourcefile', '').strip()
        if sourcefile and sourcefile != title:
            combined = f"{title}. {sourcefile}"
            return combined, 'title+sourcefile'
        return title, 'title'
    
    # Last resort: try to find any text-like field
    for key, value in doc.items():
        if isinstance(value, str) and len(value.strip()) > 10:
            return value.strip(), key
    
    return None, None

def flatten_content_chunks(doc):
    """
    Flatten documents with content_chunks structure into individual chunk documents.
    Handles the specific structure where content_chunks contains string arrays.
    
    Args:
        doc: Document that may contain content_chunks array
        
    Returns:
        List of flattened documents, each representing a chunk
    """
    if 'content_chunks' not in doc:
        return [doc]  # Return as-is if no content_chunks
    
    content_chunks = doc.get('content_chunks', [])
    if not isinstance(content_chunks, list):
        print(f"  ⚠ content_chunks is not a list in document {doc.get('id', 'unknown')}")
        return [doc]
    
    if not content_chunks:
        print(f"  ⚠ Empty content_chunks array in document {doc.get('id', 'unknown')}")
        return [doc]
    
    flattened_docs = []
    base_metadata = {k: v for k, v in doc.items() if k != 'content_chunks'}
    
    for i, chunk in enumerate(content_chunks):
        # Handle string chunks (which is what we found in your data)
        if isinstance(chunk, str):
            chunk_content = chunk.strip()
            if not chunk_content:
                continue  # Skip empty chunks
                
            # Create a new document for this chunk
            chunk_doc = base_metadata.copy()
            chunk_doc['chunk'] = chunk_content  # Primary content field
            chunk_doc['content'] = chunk_content  # Alternative content field
            chunk_doc['chunk_content'] = chunk_content  # Another alternative
            
            # Generate a unique ID for this chunk
            parent_id = doc.get('id', f'unknown_{i}')
            chunk_doc['id'] = f"{parent_id}_chunk_{i}"
            chunk_doc['parent_id'] = parent_id
            chunk_doc['chunk_id'] = f'chunk_{i}'
            
            flattened_docs.append(chunk_doc)
            
        elif isinstance(chunk, dict):
            # Handle dictionary chunks (fallback for other data structures)
            chunk_doc = base_metadata.copy()
            chunk_doc.update(chunk)
            
            # Generate a unique ID for this chunk
            parent_id = doc.get('id', f'unknown_{i}')
            chunk_id = chunk.get('chunk_id', f'chunk_{i}')
            chunk_doc['id'] = f"{parent_id}_{chunk_id}"
            chunk_doc['parent_id'] = parent_id
            chunk_doc['chunk_id'] = chunk_id
            
            flattened_docs.append(chunk_doc)
        else:
            print(f"  ⚠ Unexpected chunk type in {doc.get('id', 'unknown')}: {type(chunk)}")
    
    print(f"  📄 Flattened {len(content_chunks)} chunks from document {doc.get('id', 'unknown')} -> {len(flattened_docs)} valid chunks")
    return flattened_docs

def normalize_json_data(data):
    """
    Normalize JSON data to a consistent list of documents format.
    """
    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        # Check for common wrapper structures
        if 'documents' in data and isinstance(data['documents'], list):
            return data['documents']
        elif 'data' in data and isinstance(data['data'], list):
            return data['data']
        elif 'items' in data and isinstance(data['items'], list):
            return data['items']
        else:
            # Treat as single document
            return [data]
    else:
        print(f"  ⚠ Unexpected data structure type: {type(data)}")
        return []

def validate_legal_document_structure(doc):
    """
    Validate that legal documents have required structure for effective embeddings.
    """
    required_fields = ['id', 'content', 'category', 'sourcepage']
    missing_fields = [field for field in required_fields if not doc.get(field)]
    
    if missing_fields:
        print(f"  ⚠️ Missing legal metadata: {missing_fields}")
        return False
    
    # Check content length for legal documents
    content = doc.get('content', '')
    if len(content.split()) < 50:
        print(f"  ⚠️ Content too short for meaningful legal embedding: {len(content.split())} words")
        return False
    
    if len(content.split()) > 2000:
        print(f"  ⚠️ Content very long, may need chunking: {len(content.split())} words")
    
    return True

def process_file(file_path, analyze_only=False, flatten_chunks=False):
    """Process a single JSON file with legal document validation."""
    print(f"Processing: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
        
        if analyze_only:
            analyze_json_structure(file_path)
            return False
        
        # Normalize data structure
        docs = normalize_json_data(raw_data)
        
        if not docs:
            print(f"  ⚠ No documents found in file")
            return False
        
        print(f"  📄 Found {len(docs)} documents")
        
        # Note: flatten_chunks is disabled for Azure Search OpenAI demo format
        # since documents are already in the correct individual format
        if flatten_chunks:
            print("  ℹ Flattening disabled - documents already in Azure Search OpenAI demo format")
        
        updated = False
        processed_count = 0
        error_count = 0
        embeddings_generated = 0
        
        for i, doc in enumerate(docs):
            if not isinstance(doc, dict):
                print(f"  ⚠ Document {i} is not a dictionary, skipping")
                error_count += 1
                continue

            # Always regenerate if embedding is missing or wrong length
            embedding = doc.get("embedding") or []
            if isinstance(embedding, list) and len(embedding) == embedding_dimensions:
                processed_count += 1
                continue
            
            # Extract content from document
            content, field_used = extract_content_from_document(doc)
            
            if content:
                t0 = time.time()
                new_embedding = generate(content)
                dt = time.time() - t0
                
                if new_embedding:
                    doc["embedding"] = new_embedding  # Use Azure Search OpenAI demo field name
                    doc_id = doc.get('id', f'doc_{i}')
                    print(f"  ✅ Generated embedding for id={doc_id} from '{field_used}' ({len(new_embedding)}‑d, {dt:.2f}s)")
                    updated = True
                    processed_count += 1
                    embeddings_generated += 1
                else:
                    doc_id = doc.get('id', f'doc_{i}')
                    print(f"  ⚠ Failed to generate embedding for id={doc_id}")
                    error_count += 1
            else:
                doc_id = doc.get('id', f'doc_{i}')
                print(f"  ⚠ No content found for id={doc_id}")
                error_count += 1

        print(f"  📊 Summary: {processed_count} processed, {embeddings_generated} new embeddings, {error_count} errors")

        if updated:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(docs, f, indent=2, ensure_ascii=False)
            print(f"✅ File updated: {file_path}")
        else:
            print(f"ℹ No updates needed: {file_path}")
            
        return updated
        
    except json.JSONDecodeError as e:
        print(f"  ⚠ JSON decode error in {file_path}: {e}")
        return False
    except Exception as e:
        print(f"  ⚠ Error processing {file_path}: {e}")
        return False

def analyze_json_structure(file_path):
    """Analyze the structure of a JSON file to understand its format."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"  📊 Analyzing structure of: {os.path.basename(file_path)}")
        
        if isinstance(data, list):
            print(f"    - Array with {len(data)} items")
            if data:
                sample_doc = data[0]
                print(f"    - Sample document keys: {list(sample_doc.keys())[:10]}")
                
                # Check for content_chunks
                if 'content_chunks' in sample_doc:
                    chunks = sample_doc['content_chunks']
                    if isinstance(chunks, list):
                        print(f"    - Found content_chunks array with {len(chunks)} chunks")
                        if chunks and isinstance(chunks[0], dict):
                            print(f"    - Sample chunk keys: {list(chunks[0].keys())}")
                            content, field = extract_content_from_document(chunks[0])
                            if content:
                                print(f"    - Chunk content found in field: '{field}' (preview: '{content[:50]}...')")
                    else:
                        print(f"    - content_chunks is not an array: {type(chunks)}")
                
                content, field = extract_content_from_document(sample_doc)
                if content:
                    print(f"    - Document content found in field: '{field}' (preview: '{content[:50]}...')")
                else:
                    print(f"    - ⚠ No content field identified in sample document")
        elif isinstance(data, dict):
            if 'documents' in data:
                docs = data['documents']
                print(f"    - Object with 'documents' array ({len(docs)} items)")
            elif 'data' in data:
                docs = data['data']
                print(f"    - Object with 'data' array ({len(docs)} items)")
            else:
                print(f"    - Single document object with keys: {list(data.keys())[:10]}")
                
                # Check for content_chunks in single document
                if 'content_chunks' in data:
                    chunks = data['content_chunks']
                    if isinstance(chunks, list):
                        print(f"    - Found content_chunks array with {len(chunks)} chunks")
                
                content, field = extract_content_from_document(data)
                if content:
                    print(f"    - Content found in field: '{field}'")
                else:
                    print(f"    - ⚠ No content field identified")
        else:
            print(f"    - Unexpected data type: {type(data)}")
            
    except Exception as e:
        print(f"  ⚠ Error analyzing structure: {e}")

def validate_upload_directory():
    """
    Validate that the upload directory contains compatible JSON files.
    """
    upload_dir = project_root / "data" / "processed" / "Upload"
    if not upload_dir.exists():
        print(f"❌ Upload directory not found: {upload_dir}")
        return False
    
    json_files = list(upload_dir.glob("*.json"))
    if not json_files:
        print(f"❌ No JSON files found in upload directory: {upload_dir}")
        return False
    
    print(f"✅ Found {len(json_files)} JSON files in upload directory")
    
    # Sample a few files to check structure
    sample_files = json_files[:3]  # Check first 3 files
    compatible_count = 0
    
    for file_path in sample_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            docs = normalize_json_data(data)
            if docs and isinstance(docs[0], dict):
                content, field = extract_content_from_document(docs[0])
                if content:
                    compatible_count += 1
                    print(f"  ✅ {file_path.name}: Compatible (content found in '{field}')")
                else:
                    print(f"  ⚠️ {file_path.name}: No extractable content found")
            else:
                print(f"  ⚠️ {file_path.name}: Invalid document structure")
                
        except Exception as e:
            print(f"  ❌ {file_path.name}: Error reading file - {e}")
    
    if compatible_count == 0:
        print(f"❌ No compatible files found in sample")
        return False
    elif compatible_count < len(sample_files):
        print(f"⚠️ Only {compatible_count}/{len(sample_files)} sample files are compatible")
    else:
        print(f"✅ All sampled files are compatible")
    
    return True

def main():
    parser = argparse.ArgumentParser(description="Generate embeddings for legal document chunks")
    parser.add_argument("path", nargs='?', help="Path to JSON file or directory pattern")
    parser.add_argument("--upload-dir", help="Process all JSON files in Upload directory", action="store_true")
    parser.add_argument("--analyze", help="Only analyze file structures without generating embeddings", action="store_true")
    parser.add_argument("--pattern", help="File pattern within Upload directory (default: **/*.json)", default="**/*.json")
    parser.add_argument("--validate", help="Validate upload directory compatibility", action="store_true")
    
    args = parser.parse_args()

    # Print configuration summary
    print("\n" + "="*60)
    print("AZURE OPENAI CONFIGURATION")
    print("="*60)
    print(f"Endpoint: {openai_endpoint}")
    print(f"Deployment: {openai_deployment}")
    print(f"API Version: {openai_api_version}")
    print(f"Embedding Dimensions: {embedding_dimensions}")
    print(f"Authentication: Azure Identity with API key fallback")
    print("="*60)
    print("📋 Processing documents in Azure Search OpenAI demo format")
    print("="*60 + "\n")

    # Note: No flattening needed for Azure Search OpenAI demo format
    flatten_chunks = False

    pattern = args.pattern if args.pattern else "**/*.json"

    if args.upload_dir or not args.path:
        # Process all JSON files in the Upload directory
        upload_dir = project_root / "data" / "processed" / "Upload"
        json_files = list(upload_dir.glob(pattern))
        if not validate_upload_directory():
            print("❌ Upload directory validation failed. Use --validate to check compatibility.")
            sys.exit(1)
        if not json_files:
            print("❌ No JSON files found in upload directory.")
            sys.exit(1)
        print(f"Found {len(json_files)} JSON files in Upload directory")
        print(f"Flatten chunks: {'Yes' if flatten_chunks else 'No'}")
        updated_count = 0
        if args.analyze:
            print("\n=== ANALYZING FILE STRUCTURES ===")
            for json_file in json_files:
                process_file(str(json_file), analyze_only=True)
                print()  # Add spacing between files
        else:
            for json_file in json_files:
                if process_file(str(json_file), flatten_chunks=flatten_chunks):
                    updated_count += 1
            print(f"✅ Processing complete: {updated_count}/{len(json_files)} files updated")
    else:
        # Process a single file or pattern
        path = Path(args.path)
        if not path.exists():
            print(f"File not found: {args.path}")
            sys.exit(1)
        if path.is_file():
            if args.analyze:
                process_file(str(path), analyze_only=True)
            else:
                if process_file(str(path), flatten_chunks=flatten_chunks):
                    print("✅ Processing complete: File updated")
                else:
                    print("ℹ Processing complete: No updates needed")
        elif path.is_dir():
            json_files = list(path.glob(pattern))
            if not json_files:
                print(f"No JSON files found in directory: {path}")
                sys.exit(1)
            updated_count = 0
            if args.analyze:
                print("\n=== ANALYZING FILE STRUCTURES ===")
                for json_file in json_files:
                    process_file(str(json_file), analyze_only=True)
                    print()
            else:
                for json_file in json_files:
                    if process_file(str(json_file), flatten_chunks=flatten_chunks):
                        updated_count += 1
                print(f"✅ Processing complete: {updated_count}/{len(json_files)} files updated")
        else:
            print(f"Path is not a file or directory: {args.path}")
            sys.exit(1)

if __name__ == "__main__":
    main()