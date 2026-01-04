#!/usr/bin/env python
"""
Validation utilities for legal document scraper.
Validates scraped documents for quality before upload to Azure Search.
"""
import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class DocumentValidator:
    """Validates scraped legal documents for quality and correctness."""
    
    def __init__(self, config):
        self.config = config
        self.min_content_length = config.MIN_CONTENT_LENGTH
        self.legal_terms = config.LEGAL_TERMS
        self.min_legal_terms = config.MIN_LEGAL_TERMS
    
    def validate_document(self, doc: dict, doc_path: str = "") -> Tuple[bool, List[str]]:
        """
        Validate a single document.
        
        Args:
            doc: Document dictionary (from JSON)
            doc_path: Path to document file (for context)
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check required fields
        if not doc.get("id"):
            errors.append("Missing 'id' field")
        
        if not doc.get("content"):
            errors.append("Missing 'content' field")
        elif not isinstance(doc["content"], str):
            errors.append(f"'content' field must be string, got {type(doc['content'])}")
        else:
            # Content quality checks
            content = doc["content"]
            content_errors = self._validate_content(content)
            errors.extend(content_errors)
        
        # Check embedding if present
        if "embedding" in doc:
            if not isinstance(doc["embedding"], list):
                errors.append(f"'embedding' must be a list, got {type(doc['embedding'])}")
            elif len(doc["embedding"]) != self.config.EMBEDDING_DIMENSIONS:
                errors.append(
                    f"Embedding has {len(doc['embedding'])} dimensions, "
                    f"expected {self.config.EMBEDDING_DIMENSIONS}"
                )
        
        # Check other expected fields
        for field in ["category", "sourcepage", "sourcefile"]:
            if field not in doc:
                errors.append(f"Missing '{field}' field")
        
        return len(errors) == 0, errors
    
    def _validate_content(self, content: str) -> List[str]:
        """Validate content quality."""
        errors = []
        
        # Length validation
        if len(content) < self.min_content_length:
            errors.append(
                f"Content too short: {len(content)} characters "
                f"(minimum {self.min_content_length})"
            )
        
        # Legal terminology validation
        content_lower = content.lower()
        legal_term_count = sum(1 for term in self.legal_terms if term in content_lower)
        
        if legal_term_count < self.min_legal_terms:
            errors.append(
                f"Insufficient legal terminology: found {legal_term_count} terms, "
                f"minimum {self.min_legal_terms} required"
            )
        
        # Character encoding validation
        try:
            content.encode('utf-8')
        except UnicodeEncodeError:
            errors.append("Content contains invalid UTF-8 characters")
        
        # Check for common scraping failures
        boilerplate_phrases = [
            "page not found",
            "404 error",
            "cookie",
            "javascript required",
            "please enable javascript",
            "access denied"
        ]
        
        for phrase in boilerplate_phrases:
            if phrase in content_lower:
                errors.append(f"Content contains boilerplate phrase: '{phrase}'")
                break
        
        return errors
    
    def compute_content_hash(self, content: str) -> str:
        """Compute SHA-256 hash of content."""
        return hashlib.sha256(content.encode()).hexdigest()
    
    def detect_duplicates(self, documents: List[dict]) -> List[Tuple[int, int, str]]:
        """
        Detect duplicate content across documents.
        
        Returns:
            List of (doc_index1, doc_index2, duplicate_id) tuples
        """
        duplicates = []
        content_hashes = {}
        
        for i, doc in enumerate(documents):
            content_hash = self.compute_content_hash(doc.get("content", ""))
            doc_id = doc.get("id", f"doc_{i}")
            
            if content_hash in content_hashes:
                prev_idx, prev_id = content_hashes[content_hash]
                duplicates.append((prev_idx, i, f"{prev_id} == {doc_id}"))
            else:
                content_hashes[content_hash] = (i, doc_id)
        
        return duplicates

class ValidationReport:
    """Generates human-readable validation reports."""
    
    def __init__(self, config):
        self.config = config
        self.timestamp = datetime.now().isoformat()
    
    def generate_report(self, documents: List[dict], validator: DocumentValidator) -> Dict:
        """
        Generate comprehensive validation report for all documents.
        
        Returns:
            Dictionary containing report data
        """
        report = {
            "timestamp": self.timestamp,
            "total_documents": len(documents),
            "passed": 0,
            "failed": 0,
            "warnings": 0,
            "errors": [],
            "duplicates": [],
            "issues_by_document": {},
            "summary": {}
        }
        
        # Validate each document
        for i, doc in enumerate(documents):
            doc_id = doc.get("id", f"document_{i}")
            is_valid, errors = validator.validate_document(doc)
            
            if is_valid:
                report["passed"] += 1
            else:
                report["failed"] += 1
                report["issues_by_document"][doc_id] = errors
                report["errors"].extend([
                    f"  {doc_id}: {error}" for error in errors
                ])
        
        # Check for duplicates
        duplicates = validator.detect_duplicates(documents)
        if duplicates:
            report["warnings"] += len(duplicates)
            report["duplicates"] = [
                f"Documents {dup[0]} and {dup[1]} have identical content: {dup[2]}"
                for dup in duplicates
            ]
        
        # Generate summary
        report["summary"] = {
            "total": len(documents),
            "valid": report["passed"],
            "invalid": report["failed"],
            "duplicate_pairs": len(duplicates),
            "success_rate": f"{100.0 * report['passed'] / len(documents):.1f}%"
        }
        
        return report
    
    def print_report(self, report: Dict, verbose: bool = True) -> None:
        """Print report to console."""
        print("\n" + "="*60)
        print("VALIDATION REPORT")
        print("="*60)
        print(f"Timestamp: {report['timestamp']}")
        print(f"\nSummary:")
        for key, value in report["summary"].items():
            print(f"  {key}: {value}")
        
        if report["failed"] > 0:
            print(f"\n❌ {report['failed']} document(s) failed validation:")
            for doc_id, errors in report["issues_by_document"].items():
                print(f"\n  {doc_id}:")
                for error in errors:
                    print(f"    - {error}")
        else:
            print("\n✅ All documents passed validation")
        
        if report["duplicates"]:
            print(f"\n⚠️  {len(report['duplicates'])} duplicate pairs detected:")
            for dup in report["duplicates"]:
                print(f"  - {dup}")
        
        print("\n" + "="*60)
    
    def save_report(self, report: Dict, output_path: str) -> None:
        """Save report to JSON file."""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"✅ Validation report saved to {output_path}")
