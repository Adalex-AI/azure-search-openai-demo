import os
import json
import logging
from datetime import datetime
import sys

# Add the project root to the path so we can import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.config import Config

logger = logging.getLogger('json_processor')

class JsonProcessor:
    """
    Class to process JSON files, particularly the Civil Procedure Rules and Practice Directions.
    """
    
    def __init__(self, file_path, config=None):
        """
        Initialize the JSON processor with the file path and configuration.
        
        Args:
            file_path (str): Path to the JSON file
            config (dict, optional): Configuration settings. If None, uses Config.PDF_PROCESSING_CONFIG.
        """
        self.file_path = file_path
        self.config = config or Config.PDF_PROCESSING_CONFIG
        self.data = self.load_json()
        self.filename = os.path.basename(file_path)
        
    def load_json(self):
        """Load and parse the JSON file."""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except Exception as e:
            logger.error(f"Error loading JSON file {self.file_path}: {str(e)}")
            raise
    
    def extract_text_and_metadata(self):
        """
        Extract text and metadata from the JSON file.
        For Civil Procedure Rules, this consolidates rule text and metadata.
        
        Returns:
            tuple: (text, metadata) where text is the extracted content
                  and metadata is a dictionary of metadata information
        """
        # Initialize metadata
        metadata = {
            "filename": self.filename,
            "source_path": self.file_path,
            "processed_date": datetime.now().isoformat(),
            "document_type": "civil_procedure_rules",
            "is_court_specific": False  # Flag indicating this is general, not court-specific
        }
        
        # Process content based on structure
        if "Civil Procedure Rules" in self.filename:
            # Handle Civil Procedure Rules structure
            all_text, rules_metadata = self._process_civil_procedure_rules()
            metadata["title"] = "Civil Procedure Rules and Practice Directions"
            metadata["description"] = "General civil procedure rules applicable across all courts"
            metadata.update(rules_metadata)
        else:
            # Generic handling for other JSON structures
            all_text = json.dumps(self.data, indent=2)
            
        return all_text, metadata
    
    def _process_civil_procedure_rules(self):
        """
        Process Civil Procedure Rules JSON into formatted text.
        The Civil Procedure Rules JSON is an array of objects with
        'id', 'title', 'url', 'content_chunks', and 'updated' fields.
        
        Returns:
            tuple: (text, metadata) where text is formatted content and metadata contains additional info
        """
        text = "# CIVIL PROCEDURE RULES AND PRACTICE DIRECTIONS\n\n"
        rules_metadata = {
            "parts": [],
            "latest_update": None
        }
        
        # Process each part/section of the rules
        for rule_part in self.data:
            if not isinstance(rule_part, dict):
                continue
                
            # Extract key information
            part_id = rule_part.get('id', '')
            part_title = rule_part.get('title', '')
            part_url = rule_part.get('url', '')
            part_updated = rule_part.get('updated', '')
            content_chunks = rule_part.get('content_chunks', [])
            
            # Track parts for metadata
            rules_metadata["parts"].append({
                "id": part_id,
                "title": part_title,
                "url": part_url,
                "updated": part_updated
            })
            
            # Track latest update date
            if part_updated and (not rules_metadata["latest_update"] or part_updated > rules_metadata["latest_update"]):
                rules_metadata["latest_update"] = part_updated
            
            # Format the text for this part
            text += f"## {part_title}\n\n"
            text += f"URL: {part_url}\n"
            text += f"Last Updated: {part_updated}\n\n"
            
            # Add all content chunks
            for chunk in content_chunks:
                text += f"{chunk}\n\n"
            
            text += "---\n\n"  # Separator between parts
                
        return text, rules_metadata
    
    def chunk_text(self, text, chunk_size=None, overlap=None):
        """
        Split the text into overlapping chunks, with rule-aware chunking
        to preserve the structure of legal content.
        
        Args:
            text (str): The text to chunk
            chunk_size (int, optional): The maximum size of each chunk. If None, uses config.
            overlap (int, optional): The overlap between chunks. If None, uses config.
            
        Returns:
            list: List of text chunks with appropriate metadata
        """
        # Use provided parameters or get from config
        chunk_size = chunk_size or self.config.get("chunk_size", 1000)
        overlap = overlap or self.config.get("chunk_overlap", 100)
        
        if not text:
            return []
        
        # First split by rule parts (## headings)
        rule_parts = []
        current_part = ""
        current_heading = "General"
        
        for line in text.split('\n'):
            if line.startswith('## '):
                # Save previous part if it exists
                if current_part:
                    rule_parts.append((current_heading, current_part))
                # Start new part
                current_heading = line[3:].strip()
                current_part = line + "\n"
            else:
                current_part += line + "\n"
                
        # Add the last part
        if current_part:
            rule_parts.append((current_heading, current_part))
        
        # Now chunk each part, preserving headings
        chunks = []
        for heading, part_text in rule_parts:
            # Split part into paragraphs
            paragraphs = [p for p in part_text.split('\n\n') if p.strip()]
            
            current_chunk = ""
            for para in paragraphs:
                # If adding this paragraph would exceed the chunk size, 
                # store the current chunk and start a new one
                if len(current_chunk) + len(para) > chunk_size and current_chunk:
                    chunks.append({
                        "text": current_chunk,
                        "part": heading
                    })
                    # Start new chunk with heading and overlap from the end
                    words = current_chunk.split()
                    if len(words) > overlap/5:  # Approximate 5 chars per word
                        overlap_text = ' '.join(words[-int(overlap/5):])
                        current_chunk = f"## {heading} (continued)\n\n{overlap_text}"
                    else:
                        current_chunk = f"## {heading} (continued)\n\n"
                
                current_chunk += "\n\n" + para if current_chunk else para
            
            # Add the last chunk if it's not empty
            if current_chunk:
                chunks.append({
                    "text": current_chunk,
                    "part": heading
                })
        
        return chunks