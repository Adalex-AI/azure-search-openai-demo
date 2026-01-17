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
from datetime import datetime
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
        """Generate a clean ID from the URL.
        
        Note: This is a fallback ID. The actual ID will be generated
        from the page title after scraping to match existing index format.
        """
        # Extract the last part of the URL (e.g., 'part01')
        basename = url.strip('/').split('/')[-1]
        # Clean up
        clean_name = re.sub(r'[^a-zA-Z0-9_-]', '_', basename)
        return f"cpr_{clean_name}"

    def _generate_id_from_title(self, title: str, content: str) -> str:
        """Generate an ID from the page title to match existing index format.
        
        The existing index uses IDs like "Part 44 – General Rules about Costs"
        which get sanitized to "Part_44___General_Rules_about_Costs".
        
        We need to extract the Part/Rule number and full title.
        """
        # Try to extract the PART title from content (usually in format "PART X - TITLE")
        import re
        
        # Match "PART X - TITLE" or "PART X – TITLE" at the start of content
        part_match = re.search(r'^(PART\s+\d+[A-Z]?)\s*[-–]\s*([A-Z][A-Z\s]+)', content, re.MULTILINE)
        if part_match:
            part_num = part_match.group(1).title()  # e.g., "Part 44"
            part_title = part_match.group(2).strip().title()  # e.g., "General Rules About Costs"
            return f"{part_num} – {part_title}"
        
        # Try Practice Direction format
        pd_match = re.search(r'^(PRACTICE\s+DIRECTION\s+\d+[A-Z]*)\s*[-–]\s*([A-Z][A-Z\s]+)', content, re.MULTILINE | re.IGNORECASE)
        if pd_match:
            pd_num = pd_match.group(1).title()
            pd_title = pd_match.group(2).strip().title()
            return f"{pd_num} – {pd_title}"
        
        # Fallback: use the link title with em dash
        if title:
            # Clean up the title
            clean_title = title.strip()
            if ' - ' in clean_title:
                clean_title = clean_title.replace(' - ', ' – ')  # Use em dash
            return clean_title
        
        # Last resort: use URL-based ID
        return None

    def scrape_rule_page(self, link_info: Dict[str, str]) -> bool:
        """Scrape a single rule page and save to JSON."""
        url = link_info['url']
        fallback_id = link_info['id']
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

        # Generate title-based ID to match existing index format
        title_based_id = self._generate_id_from_title(link_info['title'], text)
        doc_id = title_based_id if title_based_id else fallback_id
        
        # Extract sourcefile (Part number) from the ID
        # e.g., "Part 44 – General Rules about Costs" -> "Part 44"
        sourcefile = doc_id.split('–')[0].strip() if '–' in doc_id else doc_id.split('-')[0].strip() if '-' in doc_id else doc_id
        
        # Create document object matching existing schema
        doc = {
            "id": doc_id,
            "content": text,
            "category": "Civil Procedure Rules and Practice Directions",
            "sourcepage": link_info['title'],  # Human-readable page name
            "sourcefile": sourcefile,  # Part number (e.g., "Part 44")
            "storageUrl": url,  # Original URL
            "oids": [],
            "groups": [],
            "parent_id": doc_id,
            "embedding": [],  # Will be generated during upload
            "updated": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        }

        # Save to file using sanitized filename
        safe_filename = re.sub(r'[^a-zA-Z0-9_-]', '_', doc_id)[:100]  # Limit filename length
        output_path = os.path.join(self.output_dir, f"{safe_filename}.json")
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(doc, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved: {output_path} (ID: {doc_id})")
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

        import concurrent.futures
        
        logger.info(f"Starting parallel scrape with 5 workers...")
        success_count = 0
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            results = list(executor.map(self.scrape_rule_page, links))
            success_count = sum(1 for r in results if r)
            
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
