import re
import tiktoken
from typing import List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)

class LegalDocumentChunker:
    """
    Intelligent chunker for legal documents that respects legal structure
    and maintains semantic meaning while staying within token limits.
    """
    
    def __init__(self, max_tokens: int = 7000, overlap_tokens: int = 200):
        """
        Initialize the chunker with token limits.
        
        Args:
            max_tokens: Maximum tokens per chunk (leave buffer for embedding model)
            overlap_tokens: Tokens to overlap between chunks for context
        """
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens
        self.encoding = tiktoken.encoding_for_model("text-embedding-3-large")
        
    def count_tokens(self, text: str) -> int:
        """Count tokens in text using the embedding model's tokenizer."""
        return len(self.encoding.encode(text))
    
    def find_legal_boundaries(self, text: str) -> List[Tuple[int, str, str]]:
        """
        Find logical boundaries in legal text for chunking.
        
        Returns:
            List of (position, boundary_type, header_text) tuples
        """
        boundaries = []
        
        # Legal document boundary patterns (in order of preference)
        patterns = [
            # Major sections (highest priority)
            (r'\n\s*([IVX]+)\s+([A-Z][A-Z\s]+)\s*\n', 'major_section'),
            (r'\n\s*(PART\s+\d+\s*[-–]\s*[A-Z][A-Z\s]+)\s*\n', 'part'),
            (r'\n\s*(PRACTICE DIRECTION\s+\d+[A-Z]?\s*[-–]\s*[A-Z][A-Z\s]+)\s*\n', 'practice_direction'),
            
            # Rules and sub-rules
            (r'\n\s*([A-Z][a-z]+\s+\d+(?:\.\d+)*(?:\s*[A-Z]\s*\d*)?)\s*\n', 'rule'),
            (r'\n\s*(\d+\.\d+(?:\.\d+)*)\s+([A-Z][^.]+)\s*\n', 'sub_rule'),
            (r'\n\s*(\d+\.)\s+([A-Z][^.]+)\s*\n', 'numbered_section'),
            
            # Paragraphs with legal structure
            (r'\n\s*\(([a-z])\)\s+([A-Z][^.]+)', 'paragraph'),
            (r'\n\s*\((\d+)\)\s+([A-Z][^.]+)', 'numbered_paragraph'),
            
            # Headers and important markers
            (r'\n\s*(To the top)\s*\n', 'section_end'),
            (r'\n\s*([A-Z][a-z]+(?:\s+[a-z]+)*)\s*\n(?=\d+\.)', 'topic_header'),
        ]
        
        for pattern, boundary_type in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE):
                start_pos = match.start()
                header_text = match.group(0).strip()
                boundaries.append((start_pos, boundary_type, header_text))
        
        # Sort by position
        boundaries.sort(key=lambda x: x[0])
        
        return boundaries
    
    def create_chunk_with_context(self, text: str, start: int, end: int, 
                                 chunk_index: int, total_chunks: int,
                                 rule_title: str, section_context: str = "") -> str:
        """
        Create a chunk with proper context and metadata.
        
        Args:
            text: Full text
            start: Start position in text
            end: End position in text
            chunk_index: Index of this chunk
            total_chunks: Total number of chunks for this document
            rule_title: Title of the rule/document
            section_context: Context about which section this chunk belongs to
        
        Returns:
            Formatted chunk with context
        """
        chunk_text = text[start:end].strip()
        
        # Add context header for multi-chunk documents
        if total_chunks > 1:
            context_header = f"Document: {rule_title}"
            if section_context:
                context_header += f"\nSection: {section_context}"
            context_header += f"\nPart {chunk_index + 1} of {total_chunks}"
            context_header += "\n" + "="*50 + "\n"
            chunk_text = context_header + chunk_text
        
        return chunk_text
    
    def chunk_legal_document(self, text: str, document_id: str, 
                           rule_title: str) -> List[Dict]:
        """
        Chunk a legal document intelligently, respecting legal boundaries.
        
        Args:
            text: Full document text
            document_id: Base document ID
            rule_title: Title of the rule/document
            
        Returns:
            List of document chunks in Azure Search format
        """
        token_count = self.count_tokens(text)
        
        # If document is within token limit, return as single chunk
        if token_count <= self.max_tokens:
            return [{
                'text': text,
                'token_count': token_count,
                'chunk_index': 0,
                'total_chunks': 1,
                'needs_chunking': False
            }]
        
        logger.info(f"Document {document_id} has {token_count} tokens, chunking required")
        
        # Find legal boundaries
        boundaries = self.find_legal_boundaries(text)
        
        if not boundaries:
            # Fallback to sentence-based chunking if no legal boundaries found
            return self._fallback_sentence_chunking(text, document_id, rule_title)
        
        chunks = []
        current_start = 0
        current_section_context = ""
        
        for i, (boundary_pos, boundary_type, header_text) in enumerate(boundaries):
            # Calculate potential chunk from current_start to this boundary
            potential_chunk = text[current_start:boundary_pos]
            potential_tokens = self.count_tokens(potential_chunk)
            
            # If this chunk would exceed token limit, create a chunk
            if potential_tokens > self.max_tokens:
                # Try to find a good breaking point before the boundary
                break_point = self._find_safe_break_point(
                    text, current_start, boundary_pos, current_section_context
                )
                
                if break_point > current_start:
                    chunk_text = text[current_start:break_point].strip()
                    if chunk_text:
                        chunks.append({
                            'text': chunk_text,
                            'token_count': self.count_tokens(chunk_text),
                            'section_context': current_section_context,
                            'start_pos': current_start,
                            'end_pos': break_point
                        })
                    current_start = break_point
            
            # Update section context for major boundaries
            if boundary_type in ['major_section', 'part', 'practice_direction', 'rule']:
                current_section_context = header_text
        
        # Handle remaining text
        if current_start < len(text):
            remaining_text = text[current_start:].strip()
            if remaining_text:
                remaining_tokens = self.count_tokens(remaining_text)
                if remaining_tokens > self.max_tokens:
                    # Split remaining text if still too large
                    remaining_chunks = self._split_large_text(
                        remaining_text, current_section_context
                    )
                    chunks.extend(remaining_chunks)
                else:
                    chunks.append({
                        'text': remaining_text,
                        'token_count': remaining_tokens,
                        'section_context': current_section_context,
                        'start_pos': current_start,
                        'end_pos': len(text)
                    })
        
        # Format chunks with proper context
        formatted_chunks = []
        total_chunks = len(chunks)
        
        for i, chunk_data in enumerate(chunks):
            formatted_text = self.create_chunk_with_context(
                chunk_data['text'], 0, len(chunk_data['text']),
                i, total_chunks, rule_title, chunk_data.get('section_context', '')
            )
            
            formatted_chunks.append({
                'text': formatted_text,
                'token_count': self.count_tokens(formatted_text),
                'chunk_index': i,
                'total_chunks': total_chunks,
                'needs_chunking': True,
                'section_context': chunk_data.get('section_context', '')
            })
        
        logger.info(f"Split document {document_id} into {len(formatted_chunks)} chunks")
        return formatted_chunks
    
    def _find_safe_break_point(self, text: str, start: int, end: int, 
                              section_context: str) -> int:
        """Find a safe place to break text while preserving legal meaning."""
        # Look for paragraph breaks, sentence endings, etc.
        search_text = text[start:end]
        
        # Priority breaking points
        break_patterns = [
            r'\n\s*\n',  # Double line breaks
            r'\.\s*\n',  # Sentence ending with newline
            r'\n\s*\([a-z]\)',  # Before paragraph markers
            r'\n\s*\(\d+\)',  # Before numbered items
            r'\.\s+',  # Sentence boundaries
        ]
        
        for pattern in break_patterns:
            matches = list(re.finditer(pattern, search_text))
            if matches:
                # Find the match closest to our target position
                target_pos = len(search_text) * 0.7  # Prefer breaks around 70% through
                best_match = min(matches, key=lambda m: abs(m.end() - target_pos))
                break_point = start + best_match.end()
                
                # Ensure we don't create too small chunks
                if break_point - start > self.max_tokens * 0.3:
                    return break_point
        
        # Fallback to hard limit
        return min(end, start + self.max_tokens * 4)  # Rough character estimate
    
    def _split_large_text(self, text: str, section_context: str) -> List[Dict]:
        """Split text that's still too large after boundary detection."""
        chunks = []
        current_pos = 0
        
        while current_pos < len(text):
            # Estimate chunk size (rough character to token ratio)
            estimated_end = current_pos + (self.max_tokens * 4)
            estimated_end = min(estimated_end, len(text))
            
            # Find safe break point
            break_point = self._find_safe_break_point(
                text, current_pos, estimated_end, section_context
            )
            
            chunk_text = text[current_pos:break_point].strip()
            if chunk_text:
                chunks.append({
                    'text': chunk_text,
                    'token_count': self.count_tokens(chunk_text),
                    'section_context': section_context,
                    'start_pos': current_pos,
                    'end_pos': break_point
                })
            
            current_pos = break_point
        
        return chunks
    
    def _fallback_sentence_chunking(self, text: str, document_id: str, 
                                   rule_title: str) -> List[Dict]:
        """Fallback chunking method when no legal boundaries are found."""
        logger.warning(f"No legal boundaries found for {document_id}, using sentence chunking")
        
        # Split by sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            potential_chunk = current_chunk + " " + sentence if current_chunk else sentence
            if self.count_tokens(potential_chunk) > self.max_tokens:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                current_chunk = potential_chunk
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        # Format chunks
        formatted_chunks = []
        total_chunks = len(chunks)
        
        for i, chunk_text in enumerate(chunks):
            formatted_text = self.create_chunk_with_context(
                chunk_text, 0, len(chunk_text), i, total_chunks, rule_title
            )
            
            formatted_chunks.append({
                'text': formatted_text,
                'token_count': self.count_tokens(formatted_text),
                'chunk_index': i,
                'total_chunks': total_chunks,
                'needs_chunking': True
            })
        
        return formatted_chunks
