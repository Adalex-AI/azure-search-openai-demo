# Import sub-modules if they exist 
from .pdf_processor import PdfProcessor
from .json_processor import JsonProcessor
from .indexer import Indexer

# Import and expose the IndexingService class
from .service import IndexingService

__all__ = ['IndexingService', 'PdfProcessor', 'JsonProcessor', 'Indexer']