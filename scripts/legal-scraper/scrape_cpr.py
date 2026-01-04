#!/usr/bin/env python
"""
Wrapper for Civil Procedure Rules scraper.

For Phase 1, this wraps the original scraper from legal-rag-scraper-deployment.
Once fully integrated, the original scraper code will be moved here directly.

Usage:
    python scrape_cpr.py                 # Scrape all CPR rules
    python scrape_cpr.py --test-single   # Test with first rule
    python scrape_cpr.py --test-few 5    # Test with first 5 rules
"""
import os
import sys
import shutil
import subprocess

# Get project root
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(script_dir))

# Path to original scraper
original_scraper = os.path.join(
    project_root,
    "legal-rag-scraper-deployment",
    "scripts",
    "scrape",
    "scrape_cpr.py"
)

# Update config to use our config module
sys.path.insert(0, script_dir)

def main():
    """Run the original scraper with adapted configuration."""
    if not os.path.exists(original_scraper):
        print(f"❌ Original scraper not found at: {original_scraper}")
        print("\nPhase 1 requires the original scraper to be present.")
        print("Please ensure legal-rag-scraper-deployment/ folder exists in the project root.")
        return 1
    
    # Add original scraper path to sys.path so it can find src.config
    original_dir = os.path.dirname(os.path.dirname(original_scraper))
    sys.path.insert(0, original_dir)
    
    # Import and run the original scraper
    try:
        # Replace the config import to use our adapted version
        import importlib.util
        spec = importlib.util.spec_from_file_location("scrape_cpr_original", original_scraper)
        scraper_module = importlib.util.module_from_spec(spec)
        
        # Pre-import our config to override the original
        import config as our_config
        sys.modules['config'] = our_config
        
        # Execute the original scraper
        spec.loader.exec_module(scraper_module)
        
        # Call main if it exists
        if hasattr(scraper_module, 'main'):
            return scraper_module.main()
        
    except Exception as e:
        print(f"❌ Error running scraper: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
