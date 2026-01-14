#!/usr/bin/env python
"""
Scraper for UK Civil Procedure Rules (CPR).
Scrapes rules from justice.gov.uk and saves them as JSON for indexing.
"""
import os
import sys
import json
import time
import argparse
import random
import re
import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from typing import List, Dict, Optional

# Add script directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

try:
    from config import Config
except ImportError:
    # Fallback if config not found (e.g. running standalone)
    class Config:
        UPLOAD_DIR = "data/legal-scraper/processed/Upload"
        VERBOSE = True

# Configure logging
logging.basicConfig(
    level=logging.INFO if Config.VERBOSE else logging.WARNING,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

BASE_URL = "https://www.justice.gov.uk/courts/procedure-rules/civil/rules"

class CPRScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.output_dir = Config.UPLOAD_DIR
        os.makedirs(self.output_dir, exist_ok=True)

    def get_soup(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch URL and return BeautifulSoup object."""
        try:
            time.sleep(random.uniform(0.5, 1.5))  # Be polite
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None

    def get_cpr_links(self) -> List[Dict[str, str]]:
        """Scrape the main index page for CPR Part links."""
        logger.info(f"Fetching index: {BASE_URL}")
        soup = self.get_soup(BASE_URL)
        if not soup:
            return []

        links = []
        # Find the main content area - usually in 'content' div or similar
        # On justice.gov.uk, looking for specific link patterns
        # Look for links that contain 'part' in text or 'part' in href
        
        main_content = soup.find('div', id='content') or soup.find('main') or soup.body
        
        for a in main_content.find_all('a', href=True):
            href = a['href']
            text = a.get_text(strip=True)
            
            # Normalize URL
            full_url = urljoin(BASE_URL, href)
            
            # Filter for likely CPR Part links
            # Usually format: .../part01, .../part-01, or text "Part 1"
            if "procedure-rules/civil/rules/" in full_url and ("part" in full_url.lower() or "part" in text.lower()):
                links.append({
                    "url": full_url,
                    "title": text,
                    "id": self._generate_id_from_url(full_url)
                })
        
        # Deduplicate by URL
        unique_links = {l['url']: l for l in links}.values()
        return list(unique_links)

    def _generate_id_from_url(self, url: str) -> str:
        """Generate a clean ID from the URL."""
        # Extract the last part of the URL (e.g., 'part01')
        basename = url.strip('/').split('/')[-1]
        # Clean up
        clean_name = re.sub(r'[^a-zA-Z0-9_-]', '_', basename)
        return f"cpr_{clean_name}"

    def scrape_rule_page(self, link_info: Dict[str, str]) -> bool:
        """Scrape a single rule page and save to JSON."""
        url = link_info['url']
        doc_id = link_info['id']
        logger.info(f"Scraping: {url}")
        
        soup = self.get_soup(url)
        if not soup:
            return False

        # Extract content
        # Try to find the specific article content
        content_div = soup.find('div', class_='article-content') or \
                      soup.find('div', id='content') or \
                      soup.find('main') or \
                      soup.body
                      
        if not content_div:
            logger.warning(f"No content found for {url}")
            return False

        # Remove script and style elements
        for script in content_div(["script", "style", "nav", "header", "footer"]):
            script.decompose()

        # Get text
        text = content_div.get_text(separator="\n\n", strip=True)
        
        # Clean text
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        if len(text) < 100:
            logger.warning(f"Content too short for {url} ({len(text)} chars)")
            return False

        # Create document object
        doc = {
            "id": doc_id,
            "content": text,
            "category": "Civil Procedure Rules",
            "sourcepage": url,
            "sourcefile": f"{doc_id}.json",
            "title": link_info['title']
        }

        # Save to file
        output_path = os.path.join(self.output_dir, f"{doc_id}.json")
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(doc, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save {output_path}: {e}")
            return False

    def run(self, limit: Optional[int] = None):
        """Run the scraper."""
        links = self.get_cpr_links()
        logger.info(f"Found {len(links)} potential CPR pages")
        
        if not links:
            logger.error("No links found. Check the scraper logic or website structure.")
            return

        if limit:
            links = links[:limit]
            logger.info(f"Limiting to first {limit} pages")

        success_count = 0
        for link in links:
            if self.scrape_rule_page(link):
                success_count += 1
            
        logger.info(f"Scraping complete. Successfully scraped {success_count}/{len(links)} pages.")

def main():
    parser = argparse.ArgumentParser(description="Scrape UK Civil Procedure Rules")
    parser.add_argument("--test-single", action="store_true", help="Test scraping a single page")
    parser.add_argument("--test-few", type=int, help="Test scraping a specific number of pages")
    args = parser.parse_args()

    scraper = CPRScraper()
    
    limit = None
    if args.test_single:
        limit = 1
    elif args.test_few:
        limit = args.test_few
        
    scraper.run(limit=limit)

if __name__ == "__main__":
    main()
