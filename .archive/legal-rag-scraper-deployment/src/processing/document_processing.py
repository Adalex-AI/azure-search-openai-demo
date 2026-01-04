import os
import json
import logging
import glob
from typing import List, Dict, Any

# Set up logging
logger = logging.getLogger(__name__)

def create_text_files_from_json(data_dir: str) -> List[str]:
    """
    Create text files for all JSON files in the directory.
    
    Args:
        data_dir: Directory containing JSON files
        
    Returns:
        List of created text file paths
    """
    logger.info(f"Creating text files for JSON files in {data_dir}...")
    
    created_files = []
    
    # Find all JSON files
    json_files = glob.glob(os.path.join(data_dir, "**/*.json"), recursive=True)
    
    for json_path in json_files:
        # Determine the text file path by replacing .json with _text.txt
        text_path = json_path.replace(".json", "_text.txt")
        
        # If the text file doesn't exist, create it
        if not os.path.exists(text_path):
            logger.info(f"Creating text file for {os.path.basename(json_path)}...")
            
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Handle both single document and document arrays
                if isinstance(data, list):
                    # Extract text from multiple documents
                    texts = []
                    for doc in data:
                        if isinstance(doc, dict):
                            # Look for text content in "chunk", "content", or "text" fields
                            text = doc.get("chunk") or doc.get("content") or doc.get("text", "")
                            title = doc.get("title", "")
                            if title and text:
                                texts.append(f"--- {title} ---\n\n{text}")
                            else:
                                texts.append(text)
                    
                    combined_text = "\n\n".join(texts)
                else:
                    # Extract text from a single document
                    combined_text = data.get("chunk") or data.get("content") or data.get("text", "")
                
                # Write the text to the output file
                with open(text_path, 'w', encoding='utf-8') as f:
                    f.write(combined_text)
                
                created_files.append(text_path)
                logger.info(f"Created text file: {text_path}")
                
            except Exception as e:
                logger.error(f"Error creating text file for {json_path}: {e}")
    
    return created_files

def process_document_metadata(json_path: str) -> Dict[str, Any]:
    """
    Extract metadata from a document JSON file.
    
    Args:
        json_path: Path to JSON file
        
    Returns:
        Document metadata dictionary
    """
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle both single document and document arrays
        if isinstance(data, list) and len(data) > 0:
            doc = data[0]  # Use first document for metadata
        elif isinstance(data, dict):
            doc = data
        else:
            return {}
        
        # Extract common metadata fields
        metadata = {
            "document_type": doc.get("document_type", "unknown"),
            "title": doc.get("title", ""),
            "court_name": doc.get("court_name", "Not Applicable"),
            "last_updated": doc.get("last_updated", ""),
        }
        
        # Add document specific fields if they exist
        for field in ["url", "document_url", "section_title", "pdf_url"]:
            if field in doc:
                metadata[field] = doc[field]
        
        return metadata
    
    except Exception as e:
        logger.error(f"Error processing metadata for {json_path}: {e}")
        return {}
