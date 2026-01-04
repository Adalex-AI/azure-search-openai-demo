import re
from typing import List, Dict, Any

def chunk_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
    """
    Split text into chunks of specified size with overlap.
    
    Args:
        text: Text to split
        chunk_size: Maximum size of each chunk
        chunk_overlap: Overlap between chunks
    
    Returns:
        List of text chunks
    """
    if not text or chunk_size <= 0:
        return []
        
    # If text is shorter than chunk_size, return it as is
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # If we're not at the end of the text, try to break at a sentence
        if end < len(text):
            # Look for a sentence break (., !, ?) followed by whitespace
            # within the last 100 characters of the current chunk
            search_start = max(end - 100, start)
            search_text = text[search_start:end]
            
            # Find last sentence break in the search area
            sentence_breaks = list(re.finditer(r'[.!?]\s', search_text))
            
            if sentence_breaks:
                # Adjust end to the last sentence break found
                last_break = sentence_breaks[-1]
                end = search_start + last_break.end()
        
        # Add the chunk
        chunks.append(text[start:end])
        
        # Move to next chunk with overlap
        start = max(start + 1, end - chunk_overlap)
    
    return chunks

def clean_text(text: str) -> str:
    """
    Clean and normalize text.
    
    Args:
        text: Text to clean
    
    Returns:
        Cleaned text
    """
    # Replace multiple whitespaces with a single space
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters but keep essential punctuation
    text = re.sub(r'[^\w\s.,:;?!()[\]{}"-]', '', text)
    
    return text.strip()

def extract_metadata(text: str, document_type: str) -> Dict[str, Any]:
    """
    Extract metadata from document text based on document type.
    
    Args:
        text: Document text
        document_type: Type of document (e.g., 'civil_rules', 'court_guides')
    
    Returns:
        Dictionary of metadata
    """
    metadata = {
        "document_type": document_type
    }
    
    # Extract section numbers if present
    section_match = re.search(r'(?:Rule|Section|Part)\s+(\d+\.\d+|\d+)', text[:200])
    if section_match:
        metadata["section_number"] = section_match.group(1)
    
    # Extract headings - usually the first line or a line with all caps
    lines = text.split('\n')
    if lines and lines[0].strip():
        heading = lines[0].strip()
        if len(heading) < 100:  # Reasonable heading length
            metadata["section_heading"] = heading
    
    return metadata

def tokenize(text: str) -> List[str]:
    """Tokenizes the input text into a list of words."""
    return text.split()

def extract_court_relevance(text: str) -> str:
    """Extracts court relevance from the text based on specific keywords."""
    court_keywords = ['Commercial Court', 'Kings Bench Division', 'Technology and Construction Court']
    for keyword in court_keywords:
        if keyword.lower() in text.lower():
            return keyword
    return 'General'  # Default category if no specific court is found

def process_pdf_text(pdf_text: str) -> dict:
    """Processes the text extracted from a PDF file."""
    cleaned_text = clean_text(pdf_text)
    tokens = tokenize(cleaned_text)
    court_relevance = extract_court_relevance(cleaned_text)
    
    return {
        'cleaned_text': cleaned_text,
        'tokens': tokens,
        'court_relevance': court_relevance
    }

def process_json_data(json_data: dict) -> dict:
    """Processes the JSON data to extract relevant information."""
    # Assuming json_data has a structure that includes 'content' and 'court_info'
    content = json_data.get('content', '')
    court_info = json_data.get('court_info', 'General')
    
    cleaned_content = clean_text(content)
    tokens = tokenize(cleaned_content)
    
    return {
        'cleaned_content': cleaned_content,
        'tokens': tokens,
        'court_info': court_info
    }