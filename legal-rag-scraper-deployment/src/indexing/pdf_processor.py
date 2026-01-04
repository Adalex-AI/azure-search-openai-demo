import os
import logging
from PyPDF2 import PdfReader
import re
import traceback
from ..config import Config

logger = logging.getLogger('pdf_processor')

class PdfProcessor:
    """
    Class to extract text and metadata from PDF files.
    """
    
    def __init__(self, config=None):
        """
        Initialize the PDF processor with configuration settings.
        
        Args:
            config (dict, optional): Custom configuration settings.
                                   If None, uses Config.PDF_PROCESSING_CONFIG.
        """
        # Use provided config or get from the global config
        self.config = config or Config.PDF_PROCESSING_CONFIG
        
        # Extract settings from config
        self.use_ocr = self.config.get("use_ocr", False)
        self.min_text_length_for_ocr = self.config.get("min_text_length_for_ocr", 50)
        self.ocr_language = self.config.get("ocr_language", "eng")
        self.include_page_numbers = self.config.get("include_page_numbers", True)
        self.extract_court_references = self.config.get("extract_court_references", True)
        self.court_patterns = self.config.get("court_reference_patterns", [
            r'(Commercial Court)',
            r'(Circuit Commercial Court)',
            r'(Chancery Division)',
            r'(Administrative Court)',
            r'(King\'s Bench Division)',
            r'(Queen\'s Bench Division)',
            r'(Technology and Construction Court)',
        ])
        
        # Initialize OCR if enabled
        if self.use_ocr:
            try:
                import pytesseract
                from PIL import Image
                self.pytesseract = pytesseract
                self.Image = Image
                # Set OCR language if specified
                if self.ocr_language:
                    self.pytesseract.pytesseract.tesseract_cmd = "tesseract"
                logger.info(f"OCR support initialized with language: {self.ocr_language}")
            except ImportError:
                logger.warning("OCR libraries not available. Install pytesseract and Pillow for OCR support.")
                self.use_ocr = False
    
    def extract_text(self, pdf_path):
        """
        Extract text and metadata from a PDF file.
        
        Args:
            pdf_path (str): Path to the PDF file
            
        Returns:
            tuple: (text, metadata) where text is the extracted text content
                  and metadata is a dictionary of metadata information
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        try:
            # Open the PDF file
            pdf = PdfReader(pdf_path)
            
            # Extract metadata
            metadata = self._extract_metadata(pdf)
            
            # Extract text from each page
            text = ""
            for page_num, page in enumerate(pdf.pages):
                try:
                    page_text = page.extract_text()
                    
                    # If page text is empty or very short and OCR is enabled, try OCR
                    if self.use_ocr and (not page_text or len(page_text) < self.min_text_length_for_ocr):
                        page_text = self._extract_text_with_ocr(pdf_path, page_num)
                    
                    if page_text:
                        if self.include_page_numbers:
                            text += f"\n\n--- Page {page_num + 1} ---\n\n"
                        else:
                            text += "\n\n"
                        text += page_text
                except Exception as e:
                    logger.error(f"Error extracting text from page {page_num + 1}: {str(e)}")
                    if self.include_page_numbers:
                        text += f"\n\n--- Page {page_num + 1} (Error: {str(e)}) ---\n\n"
            
            # Extract potential court references from text if enabled
            if self.extract_court_references:
                court_refs = self._extract_court_references(text)
                if court_refs:
                    metadata['court_references'] = court_refs
            
            return text, metadata
            
        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {str(e)}\n{traceback.format_exc()}")
            raise
    
    def _extract_metadata(self, pdf):
        """Extract metadata from the PDF."""
        metadata = {
            'page_count': len(pdf.pages),
        }
        
        # Extract document info if available
        if pdf.metadata:
            info = pdf.metadata
            if info.get('/Title'):
                metadata['title'] = info.get('/Title')
            if info.get('/Author'):
                metadata['author'] = info.get('/Author')
            if info.get('/CreationDate'):
                metadata['creation_date'] = info.get('/CreationDate')
            if info.get('/Producer'):
                metadata['producer'] = info.get('/Producer')
        
        return metadata
    
    def _extract_court_references(self, text):
        """Extract potential court references from the text."""
        references = []
        for pattern in self.court_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            references.extend(matches)
        
        # Remove duplicates while preserving order
        seen = set()
        return [x for x in references if not (x.lower() in seen or seen.add(x.lower()))]
    
    def _extract_text_with_ocr(self, pdf_path, page_num):
        """
        Extract text from a PDF page using OCR (if available).
        This is a placeholder for OCR functionality.
        """
        if not self.use_ocr:
            return ""
        
        logger.info(f"OCR processing for {pdf_path}, page {page_num + 1} using language: {self.ocr_language}")
        # Implementation would convert PDF page to image and use pytesseract
        # This would require additional libraries and configuration
        return "[OCR text would be extracted here]"
    
    def chunk_text(self, text, chunk_size=None, overlap=None):
        """
        Split the text into overlapping chunks.
        
        Args:
            text (str): The text to chunk
            chunk_size (int, optional): The maximum size of each chunk. If None, uses config.
            overlap (int, optional): The overlap between chunks. If None, uses config.
            
        Returns:
            list: List of text chunks
        """
        # Use provided parameters or get from config
        chunk_size = chunk_size or self.config.get("chunk_size", 1000)
        overlap = overlap or self.config.get("chunk_overlap", 100)
        
        if not text:
            return []
        
        # Split text into paragraphs
        paragraphs = [p for p in text.split('\n\n') if p.strip()]
        
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            # If adding this paragraph would exceed the chunk size, 
            # store the current chunk and start a new one
            if len(current_chunk) + len(para) > chunk_size and current_chunk:
                chunks.append(current_chunk)
                # Start new chunk with overlap from the end of the previous chunk
                words = current_chunk.split()
                if len(words) > overlap/5:  # Approximate 5 chars per word
                    overlap_text = ' '.join(words[-int(overlap/5):])
                    current_chunk = overlap_text
                else:
                    current_chunk = ""
            
            current_chunk += "\n\n" + para if current_chunk else para
        
        # Add the last chunk if it's not empty
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks