#!/usr/bin/env python
"""
Validate scraped legal documents using the DocumentValidator.
"""
import os
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import List

# Add script directory to path to allow importing local modules
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

try:
    from validation import DocumentValidator
    from config import Config
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def validate_directory(input_dir_name: str) -> bool:
    """
    Validate all JSON files in the specified directory name under processed/
    
    Args:
        input_dir_name: Name of the directory in data/legal-scraper/processed/ (e.g., 'Upload')
        
    Returns:
        bool: True if all documents are valid, False otherwise
    """
    input_path = os.path.join(Config.PROCESSED_DIR, input_dir_name)
    
    if not os.path.exists(input_path):
        logger.error(f"Directory not found: {input_path}")
        return False
        
    logger.info(f"Validating documents in: {input_path}")
    
    validator = DocumentValidator(Config)
    files = list(Path(input_path).glob("*.json"))
    
    if not files:
        logger.warning(f"No JSON files found in {input_path}")
        return True
        
    validation_passed = True
    stats = {"valid": 0, "invalid": 0, "total": len(files)}
    
    for file_path in files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                doc = json.load(f)
            
            # Skip list files (aggregates)
            if isinstance(doc, list):
                if Config.VERBOSE:
                    logger.info(f"⏭️  Skipped (Aggregate List): {file_path.name}")
                continue
                
            is_valid, errors = validator.validate_document(doc, str(file_path))
            
            if is_valid:
                stats["valid"] += 1
                if Config.VERBOSE:
                    logger.info(f"✅ Valid: {file_path.name}")
            else:
                stats["invalid"] += 1
                validation_passed = False
                logger.error(f"❌ Invalid: {file_path.name}")
                for error in errors:
                    logger.error(f"   - {error}")
                    
        except json.JSONDecodeError:
            stats["invalid"] += 1
            validation_passed = False
            logger.error(f"❌ JSON Error: {file_path.name} is not valid JSON")
        except Exception as e:
            stats["invalid"] += 1
            validation_passed = False
            logger.error(f"❌ Error processing {file_path.name}: {str(e)}")
            
    logger.info("="*40)
    logger.info(f"Validation Summary for {input_dir_name}")
    logger.info(f"Total Files: {stats['total']}")
    logger.info(f"✅ Valid:      {stats['valid']}")
    logger.info(f"❌ Invalid:    {stats['invalid']}")
    logger.info("="*40)
    
    return validation_passed

def main():
    parser = argparse.ArgumentParser(description="Validate scraped legal documents")
    parser.add_argument("--input", default="Upload", help="Input directory name under processed/")
    args = parser.parse_args()
    
    success = validate_directory(args.input)
    
    if success:
        logger.info("🎉 Validation passed!")
        sys.exit(0)
    else:
        logger.error("💥 Validation failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
