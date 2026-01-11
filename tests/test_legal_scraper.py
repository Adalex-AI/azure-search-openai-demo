import sys
import os
import pytest
from pathlib import Path
import importlib.util

# Add scripts/legal-scraper to path
SCRAPER_DIR = Path(__file__).parent.parent / "scripts" / "legal-scraper"

def load_module_from_path(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

try:
    # Explicitly load modules from paths to avoid collision with app.backend.config
    config_module = load_module_from_path("scraper_config", SCRAPER_DIR / "config.py")
    validation_module = load_module_from_path("scraper_validation", SCRAPER_DIR / "validation.py")
    chunker_module = load_module_from_path("scraper_chunker", SCRAPER_DIR / "token_chunker.py")
    
    DocumentValidator = validation_module.DocumentValidator
    LegalDocumentChunker = chunker_module.LegalDocumentChunker
    Config = config_module.Config
except (ImportError, FileNotFoundError) as e:
    # Fallback or skip
    pass


class MockConfig:
    MIN_CONTENT_LENGTH = 10
    REQUIRED_METADATA = ["title", "source_url", "scraped_at"]
    MAX_CONTENT_LENGTH = 100000
    LEGAL_TERMS = {"valid", "content", "document"}
    MIN_LEGAL_TERMS = 1

@pytest.fixture
def validator():
    return DocumentValidator(MockConfig())

@pytest.fixture
def chunker():
    return LegalDocumentChunker(max_tokens=100, overlap_tokens=10)

class TestDocumentValidator:
    def test_validate_valid_document(self, validator):
        doc = {
            "id": "doc1",
            "title": "Valid Doc",
            "source_url": "http://example.com",
            "scraped_at": "2023-01-01",
            "content": "This is a valid document with enough content to pass validation.",
            "category": "Rules",
            "sourcepage": "Page 1",
            "sourcefile": "doc.pdf"
        }
        is_valid, errors = validator.validate_document(doc)
        assert is_valid, f"Validation failed: {errors}"
        assert len(errors) == 0

    def test_validate_missing_metadata(self, validator):
        doc = {
            "content": "This content is fine but metadata is missing."
        }
        is_valid, errors = validator.validate_document(doc)
        assert not is_valid
        assert any("Missing" in e for e in errors)

    def test_validate_short_content(self, validator):
        doc = {
            "title": "Short Doc",
            "source_url": "http://example.com",
            "scraped_at": "2023-01-01",
            "content": "Too short" # Less than 10 chars
        }
        # Override config slightly for this test if needed, or rely on "Too short" being short
        # MockConfig.MIN_CONTENT_LENGTH is 10. "Too short" is 9 chars.
        is_valid, errors = validator.validate_document(doc)
        assert not is_valid

class TestLegalDocumentChunker:
    def test_chunk_small_document(self, chunker):
        text = "Small document."
        # chunk_legal_document(text, document_id, rule_title)
        chunks = chunker.chunk_legal_document(text, "doc1", "Title")
        assert len(chunks) == 1
        assert chunks[0]['text'] == text

    def test_chunk_preserves_structure(self, chunker):
        # Create text that forces a split but has section headers
        text = "SECTION 1\n" + ("content " * 20) + "\nSECTION 2\n" + ("content " * 20)
        chunks = chunker.chunk_legal_document(text, "doc1", "Title")
        assert len(chunks) >= 1
        # Check that we didn't lose text logic (simplified)
        assert isinstance(chunks[0], dict)
        assert 'text' in chunks[0]

    def test_token_counting(self, chunker):
        text = "word " * 50
        count = chunker.count_tokens(text)
        assert count > 0
        assert isinstance(count, int)
