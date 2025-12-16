# Legal Domain Customizations for RAG Approaches
#
# This module contains custom extensions for the upstream RAG approaches.
# These classes use composition to provide legal-domain-specific functionality.
#
# Architecture:
#   Upstream: approaches/chatreadretrieveread.py (ChatReadRetrieveReadApproach)
#   Helpers:  customizations/approaches/citation_builder.py (CitationBuilder)
#             customizations/approaches/source_processor.py (SourceProcessor)
#
# The helper classes provide:
# 1. CitationBuilder: Enhanced legal citations with subsection extraction
# 2. SourceProcessor: Structured source content with metadata enrichment
#
# Usage in approaches:
#   from customizations.approaches import citation_builder, source_processor
#   
#   citation = citation_builder.build_enhanced_citation(doc, 1)
#   sources = source_processor.process_documents(results)

from .citation_builder import CitationBuilder, citation_builder
from .source_processor import SourceProcessor, source_processor

__all__ = [
    "CitationBuilder",
    "citation_builder",
    "SourceProcessor",
    "source_processor",
]
