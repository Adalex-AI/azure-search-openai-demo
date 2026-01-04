import concurrent.futures
import requests
from bs4 import BeautifulSoup
import re
import json
import time
import uuid
import os
import sys
import hashlib
from pathlib import Path
from datetime import datetime
import argparse
import subprocess

# Try to import websocket-client (required for Selenium 4+)
try:
    import websocket
except ImportError:
    print("Warning: websocket module not found. Will try to import later or install manually.")

# Import Selenium with error handling
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    # Also add Firefox as a fallback option
    from selenium.webdriver.firefox.service import Service as FirefoxService
    from webdriver_manager.firefox import GeckoDriverManager
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException
except ImportError as e:
    print(f"Error importing Selenium related modules: {e}")
    print("Will attempt to import later with proper error handling.")

# Add project root to path to use the same config as process_civil_rules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

try:
    from src.config import Config, CIVIL_RULES_DIR, PROCESSED_DIR
    from src.utils.token_chunker import LegalDocumentChunker
except ImportError:
    # Fallback if import fails
    CIVIL_RULES_DIR = "data/civil_rules"
    PROCESSED_DIR = "data/processed"
    print("Warning: Could not import from src.config or token_chunker, using default paths")
    # Create a simple fallback chunker
    class LegalDocumentChunker:
        def __init__(self, max_tokens=7000, overlap_tokens=200):
            self.max_tokens = max_tokens
            self.overlap_tokens = overlap_tokens
        
        def count_tokens(self, text):
            # Simple approximation: ~4 chars per token
            return len(text) // 4
        
        def chunk_legal_document(self, text, document_id, rule_title):
            # Always split by max_tokens (not max_tokens*3)
            tokens = text.split()
            approx_tokens_per_word = 1  # fallback: 1 word ~ 1 token (for splitting)
            chunk_size = self.max_tokens * approx_tokens_per_word
            overlap = self.overlap_tokens * approx_tokens_per_word

            if self.count_tokens(text) <= self.max_tokens:
                return [{
                    'text': text,
                    'token_count': self.count_tokens(text),
                    'chunk_index': 0,
                    'total_chunks': 1,
                    'needs_chunking': False
                }]

            chunks = []
            start = 0
            chunk_index = 0
            while start < len(tokens):
                end = min(start + chunk_size, len(tokens))
                chunk_words = tokens[start:end]
                chunk_text = ' '.join(chunk_words)
                chunks.append({
                    'text': chunk_text,
                    'token_count': self.count_tokens(chunk_text),
                    'chunk_index': chunk_index,
                    'total_chunks': 0,  # Will be updated
                    'needs_chunking': True
                })
                chunk_index += 1
                start = end - overlap if end < len(tokens) else end

            # Update total_chunks
            for chunk in chunks:
                chunk['total_chunks'] = len(chunks)

            return chunks

BASE_URL = "https://www.justice.gov.uk/courts/procedure-rules/civil/rules"
# Update output directory to match process_civil_rules.py
INPUT_DIR = CIVIL_RULES_DIR
# Explicitly set the output directory for processed files
PROCESSED_CIVIL_RULES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/processed/civil_rules"))

# File to track rule changes
CHANGES_FILE = os.path.join(INPUT_DIR, "civil_rules_changes.json")

# Exact cookie text to remove - directly from the problematic documents
PROBLEMATIC_COOKIE_TEXT = "We use small files called 'cookies' on www.justice.gov.uk. Some are essential to make the site work, some help us to understand how we can improve your experience, and some are set by third parties. You can choose to turn off the non-essential cookies."

# Exact cookie text to remove (for direct string matching)
EXACT_COOKIE_TEXT = [
    "We use small files called 'cookies' on www.justice.gov.uk. Some are essential to make the site work, some help us to understand how we can improve your experience, and some are set by third parties. You can choose to turn off the non-essential cookies.",
    "We use Google Analytics to measure how you use the website so we can improve it based on user needs. We do not allow Google Analytics to use or share the data about how you use this site.",
    "We use Google Analytics events to measure clicks within the pages and extended usage of the site",
    "These cookies will always need to be on because they make our site work.",
    "These cookies apply when users log in. They will always be on because they make our site work.",
]

# Patterns to identify and remove
COOKIE_PATTERNS = [
    r"We use small files called ['']cookies[''] on www\.justice\.gov\.uk\.?\s*Some are essential to make the site work.*?non-essential cookies\.",
    r"We use Google Analytics to measure how you use the website.*",
    r"We use Google Analytics events to measure clicks.*",
    r"These cookies will always need to be on.*",
    r"These cookies apply when users log in\..*",
    r"Cookie\s*Settings.*?Save cookie preferences",
    r"Which cookies are you happy for us to use\?.*",
]

# Other patterns for standard text to remove
# More specific patterns targeting the start and end junk
START_JUNK_PATTERN = r"^\.\s*Home\s*Search\s*Home\s*»\s*Courts\s*»\s*Procedure\s*rules\s*»\s*Civil\s*»\s*Rules\s*&\s*Practice\s*Directions\s*»\s*PART\s*\d+\s*–\s*.*?Menu\s*≡\s*PART\s*\d+\s*–\s*.*?(ContentsofthisPartTitleNumber|ContentsofthisPracticeDirectionTitleNumber)?"
END_JUNK_PATTERN = r"Updated\s*:.*?©\s*Crown\s*copyright$"

# Specific known joined words/phrases to remove if they appear isolated after initial cleaning
SPECIFIC_JUNK_PHRASES = [
    "Contentsofthis Part Title Number",
    "Contentsofthis Practice Direction Title Number",
    "Menu ≡",
    "Top ↑",
    "Back to text"
]

# Patterns to identify and remove
NAVIGATION_PATTERNS = [
    r"Home Courts Procedure rules Offenders Search Courts Procedure rules Civil.*? Menu ≡",
    r"Home » Courts » Procedure rules » Civil » Rules & Practice Directions.*? ≡",
    r"To the top$"
]

def setup_selenium_driver():
    """Sets up the Selenium WebDriver."""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run browser in headless mode (no UI)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def accept_cookies(driver):
    """Accepts cookies on the webpage using Selenium."""
    try:
        # Find and click the accept button for cookies
        accept_button = driver.find_element(By.XPATH, '//button[contains(text(),"I am OK with cookies")]')
        accept_button.click()
        print("Cookies accepted.")
    except Exception as e:
        print("Could not accept cookies or already accepted:", e)

def get_page_content(url, driver=None):
    """Fetches the webpage content using Selenium or requests."""
    if driver:
        # Using Selenium (for pages requiring JavaScript)
        print(f"Navigating to: {url}")
        driver.get(url)
        
        # Wait a bit for page to fully load
        time.sleep(2)
        
        try:
            # Wait until the page is fully loaded by checking for a known element
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
        except TimeoutException:
            print(f"Timed out while waiting for page {url} to load.")
        
        # Check if we actually navigated to the expected URL
        current_url = driver.current_url
        print(f"Current URL after navigation: {current_url}")
        
        if current_url != url and not url.endswith(current_url.split('/')[-1]):
            print(f"WARNING: URL mismatch! Requested: {url}, Got: {current_url}")
        
        return driver.page_source
    else:
        # Using requests (for static pages)
        response = requests.get(url)
        return response.text

def scrape_links(driver, base_url):
    """Scrapes all links from the CPR Rules page."""
    print(f"Scraping links from {base_url}")
    
    # Using the improved approach that successfully finds links in tables
    page_content = get_page_content(base_url, driver)
    soup = BeautifulSoup(page_content, "html.parser")

    tables = soup.find_all("figure", {"class": "wp-block-table"})
    links = []
    for table in tables:
        for row in table.find_all("tr"):
            a_tag = row.find("a", href=True)
            if a_tag:
                link = a_tag["href"]
                full_url = link if link.startswith("http") else f"https://www.justice.gov.uk{link}"
                links.append({"title": a_tag.get_text(strip=True), "url": full_url})
    
    print(f"Found {len(links)} links.")
    return links

def remove_cookies_from_html(html_content):
    """Pre-process HTML to remove cookie consent elements before parsing."""
    # Try to identify and remove cookie notice divs from the HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove cookie banner divs (these may have various IDs/classes)
    for div in soup.find_all('div', class_=lambda c: c and ('cookie' in c.lower() or 'consent' in c.lower())):
        div.decompose()
    
    # Remove any script elements that might be related to cookies - FIX DEPRECATION WARNING
    for script in soup.find_all('script', string=lambda t: t and 'cookie' in t.lower()):
        script.decompose()
    
    return str(soup)

def extract_content_chunks(html_content, rule_url=None):
    """Extracts content from HTML and returns it as a single cleaned string with preserved structure."""
    # Pre-process HTML to remove cookie elements
    html_content = remove_cookies_from_html(html_content)
    
    soup = BeautifulSoup(html_content, 'html.parser')

    # Remove cookie banners, scripts, nav, header, footer as before
    for div in soup.find_all('div', class_=lambda c: c and ('cookie' in c.lower() or 'consent' in c.lower())):
        div.decompose()
    for script in soup.find_all('script', string=lambda t: t and 'cookie' in t.lower()):
        script.decompose()
    for element in soup.find_all(['script', 'style', 'nav', 'header', 'footer']):
        element.decompose()

    # --- IMPROVED: Find the article container first ---
    article_container = None
    
    # Look for the article element first
    article_container = soup.find('article')
    
    if not article_container:
        # Fallback selectors for main content
        content_selectors = [
            'div.article',  # Based on your HTML example
            '#main-content',
            'main',
            '.entry-content',
            '.content'
        ]
        
        for selector in content_selectors:
            article_container = soup.select_one(selector)
            if article_container:
                print(f"Found content using selector: {selector}")
                break
    else:
        print("Found content using article element")
    
    if not article_container:
        print("Warning: Could not find article or main content container")
        return ""

    # --- Extract title from h1.title if present ---
    title_element = article_container.find('h1', class_='title')
    page_title = title_element.get_text(strip=True) if title_element else ""
    
    # --- Find the main article content div ---
    article_div = article_container.find('div', class_='article')
    
    if not article_div:
        # Fallback to the article container itself
        article_div = article_container
        print("Using article container directly (no div.article found)")
    else:
        print("Found div.article container")
    
    # --- Remove unwanted elements ---
    for unwanted in article_div.find_all(['nav', 'header', 'footer', 'aside']):
        unwanted.decompose()
    
    # Remove share buttons and other navigation
    for element in article_div.find_all(class_=lambda c: c and any(
        word in ' '.join(c).lower() for word in ['share-this', 'breadcrumb', 'navigation', 'menu']
    )):
        element.decompose()
    
    # Remove anchor tags that are just bookmarks (empty or just contain name/id)
    for a_tag in article_div.find_all('a'):
        if not a_tag.get_text(strip=True) and (a_tag.get('name') or a_tag.get('id')):
            a_tag.decompose()

    # --- Extract content with HTML structure-based sectioning ---
    content_sections = []
    
    # Add title as first section if present
    if page_title:
        content_sections.append(page_title)
        content_sections.append('\n\n---SECTION---\n\n')
    
    # Process all paragraphs and headings in order
    for element in article_div.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'ul', 'ol', 'blockquote', 'div']):
        # Skip if element is empty or contains only anchor bookmarks
        text = element.get_text(strip=True)
        if not text or len(text) < 3:
            continue
        
        # Skip if element only contains anchor names/ids (bookmarks)
        if element.name == 'p':
            # Check if paragraph only contains empty anchor tags
            anchors = element.find_all('a')
            if anchors and all(not a.get_text(strip=True) for a in anchors):
                if len(text) < 10:  # Very short text with just anchors
                    continue
        
        # Skip elements that are likely navigation or metadata
        if element.get('class'):
            classes = ' '.join(element.get('class', [])).lower()
            if any(skip in classes for skip in ['nav', 'menu', 'breadcrumb', 'meta', 'share']):
                continue
        
        # Handle different element types
        if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            # Headings start new sections
            if content_sections and not content_sections[-1].endswith('---SECTION---\n\n'):
                content_sections.append('\n\n---SECTION---\n\n')
            content_sections.append(text)
            content_sections.append('\n\n')
        elif element.name == 'p':
            # Paragraphs are the main content - each paragraph is naturally a section
            content_sections.append(text)
            content_sections.append('\n\n')
        elif element.name in ['ul', 'ol']:
            # Process list items
            list_items = []
            for li in element.find_all('li', recursive=False):
                li_text = li.get_text(strip=True)
                if li_text:
                    list_items.append(f"• {li_text}")
            if list_items:
                content_sections.append('\n'.join(list_items))
                content_sections.append('\n\n')
        elif element.name == 'blockquote':
            content_sections.append(f"> {text}")
            content_sections.append('\n\n')
        elif element.name == 'div':
            # Only process divs that don't contain other block elements
            if not element.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'ul', 'ol', 'blockquote']):
                if len(text) > 20:  # Only substantial text
                    content_sections.append(text)
                    content_sections.append('\n\n')
    
    # Join all content
    text = ''.join(content_sections)
    
    # If we got very little content, try a simpler extraction
    if len(text) < 200:
        print("Minimal structured content found, trying simpler extraction...")
        # Just get all paragraph text
        paragraphs = []
        for p in article_div.find_all('p'):
            p_text = p.get_text(strip=True)
            if p_text and len(p_text) > 10:
                paragraphs.append(p_text)
        
        if paragraphs:
            text = '\n\n'.join(paragraphs)
    
    # Clean the extracted text
    text = clean_text(text)
    
    # Final validation
    if len(text) < 50:
        print(f"Warning: Content too short ({len(text)} chars) for {rule_url or 'unknown URL'}")
        return ""
    
    print(f"Successfully extracted {len(text)} characters of content")
    return text

def clean_text(text):
    """Clean text by removing cookie notices, navigation elements, and other unwanted content."""
    
    # 1. Replace specific problematic unicode chars
    text = text.replace('\u00bb', ' ')  # »
    text = text.replace('\u2013', '-')  # – (en dash)
    text = text.replace('\u2014', '-')  # — (em dash)
    text = text.replace('\u2018', "'")  # '
    text = text.replace('\u2019', "'")  # '
    text = text.replace('\u201c', '"')  # "
    text = text.replace('\u201d', '"')  # "
    text = text.replace('\u2261', ' ')  # ≡
    text = text.replace('\u2191', ' ')  # ↑
    text = text.replace('\u00a0', ' ')  # Non-breaking space

    # 2. Remove cookie text first (before header/footer removal)
    if PROBLEMATIC_COOKIE_TEXT in text:
        text = text.replace(PROBLEMATIC_COOKIE_TEXT, "")
    for cookie_text in EXACT_COOKIE_TEXT:
        text = text.replace(cookie_text, "")
    for pattern in COOKIE_PATTERNS:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE | re.DOTALL)
    
    # 3. Remove navigation breadcrumbs and menu items
    nav_patterns = [
        r"^Home Courts Procedure rules Civil Rules & Practice Directions.*?Menu.*?(?=\([0-9]\.?\)|\w)",
        r"^Home Courts Procedure rules Civil Rules & Practice Directions.*?Practice Directions.*?(?=\([0-9]\.?\)|\w)",
        r"^Home Courts Procedure rules Civil Rules & Practice Directions.*?(?=\([0-9]\.?\)|\w)",
        r"Menu\s*≡.*?(?=\([0-9]\.?\)|\w)",
        r"Practice Directions Menu Practice Directions",
        r"Home\s+Courts\s+Procedure rules\s+Civil.*?PRACTICE DIRECTION",
        r"•\s+Home\s+•\s+•\s+Courts\s+•.*?•",  # Remove bullet navigation
    ]
    
    for pattern in nav_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE | re.DOTALL).strip()
    
    # 4. Don't collapse newlines - preserve them!
    # Just normalize excessive newlines
    text = re.sub(r'\n{4,}', '\n\n\n', text)  # Max 3 newlines
    
    # 5. Remove start/end junk and specific phrases
    text = re.sub(START_JUNK_PATTERN, "", text, flags=re.IGNORECASE | re.DOTALL).strip()
    text = re.sub(END_JUNK_PATTERN, "", text, flags=re.IGNORECASE | re.DOTALL).strip()
    for phrase in SPECIFIC_JUNK_PHRASES:
        text = re.sub(r'\s*' + re.escape(phrase) + r'\s*', ' ', text, flags=re.IGNORECASE).strip()

    # 6. Clean up spaces on each line (but preserve line structure)
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        # Clean spaces within the line
        line = re.sub(r'[ \t]+', ' ', line).strip()
        cleaned_lines.append(line)
    text = '\n'.join(cleaned_lines)

    # 7. Split camelCase or joined tokens
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
    text = re.sub(r'([0-9])([a-zA-Z])', r'\1 \2', text)
    text = re.sub(r'([a-zA-Z])([0-9])', r'\1 \2', text)

    # 8. Remove any leading dots or spaces
    text = text.lstrip('. ')

    # Remove the specific prefix only if it is at the very start
    prefix = "Home Courts Procedure rules Civil Rules & Practice Directions"
    if text.strip().lower().startswith(prefix.lower()):
        text = text[len(prefix):].lstrip(" -–:").lstrip()

    return text

def is_cookie_notice(text):
    """Check if the text is entirely a cookie notice."""
    # Check for the most problematic text first
    if PROBLEMATIC_COOKIE_TEXT in text:
        return True
    
    # First check exact matches
    for cookie_text in EXACT_COOKIE_TEXT:
        if cookie_text in text:
            return True
    
    # Then use regex patterns
    for pattern in COOKIE_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL):
            return True
    
    # Look for key cookie phrases
    cookie_keywords = [
        "we use cookies",
        "cookie settings",
        "cookies on www.justice.gov.uk",
        "which cookies are you happy",
        "google analytics",
        "Some are essential to make the site work",
        "You can choose to turn off the non-essential cookies"
    ]
    
    for keyword in cookie_keywords:
        if keyword.lower() in text.lower():
            return True
            
    return False

def remove_remaining_cookie_text(chunks):
    """Last-resort method to forcibly remove any remaining cookie notices."""
    clean_chunks = []
    
    for chunk in chunks:
        # Skip the chunk entirely if it's very similar to a cookie notice
        if len(chunk) < 300 and any(cookie_text in chunk for cookie_text in EXACT_COOKIE_TEXT):
            continue
        
        # For longer chunks that might have cookie text embedded, use prefix removal
        if chunk.startswith("We use small files called 'cookies'"):
            # Find the first period after "non-essential cookies."
            cookie_end = chunk.find(".", chunk.find("non-essential cookies")) + 1
            if cookie_end > 0:
                clean_chunk = chunk[cookie_end:].strip()
                if clean_chunk:  # Only add if there's content left
                    clean_chunks.append(clean_chunk)
                continue
        
        # Only add chunks that don't have cookie text
        if not is_cookie_notice(chunk):
            clean_chunks.append(chunk)
    
    return clean_chunks

def is_spaced_noise(text):
    """Detect noise where single letters are space‑separated (e.g. 'H o m e C o u r t s ...')."""
    tokens = text.split()
    # Make this less aggressive - only flag if MOST tokens are single letters AND it's long enough
    if len(tokens) >= 30 and sum(1 for t in tokens[:30] if len(t)==1) > 20:
        return True
    return False

def extract_update_date(html_content):
    """Attempt to extract the last update date from the page."""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Look for the update div first
    updated_info = soup.find("div", {"class": "share-this bottom"})
    updated_text = updated_info.get_text(" ", strip=True) if updated_info else ""
    
    # Extract date using pattern matching
    match = re.search(r"Updated:\s*(.*)", updated_text)
    if match:
        date_str = match.group(1).strip()
        try:
            dt = datetime.strptime(date_str, "%A, %d %B %Y")
            return dt.strftime("%Y-%m-%dT00:00:00Z")
        except ValueError:
            try:
                dt = datetime.strptime(date_str, "%d %B %Y")
                return dt.strftime("%Y-%m-%dT00:00:00Z")
            except ValueError:
                pass
    
    # If we can't find the update date, use a reasonable default
    return datetime.now().strftime("%Y-%m-%dT00:00:00Z")

def extract_topic_name(rule_title):
    """Extract the main topic name from the rule title for sourcepage field."""
    # Remove "Practice Direction" or "Part" prefix and numbers to get topic
    
    # For Practice Directions, extract the topic after the identifier
    pd_match = re.search(r'Practice Direction\s+\d+[A-Z]?\s*[-–]\s*(.+)', rule_title, re.IGNORECASE)
    if pd_match:
        return pd_match.group(1).strip()
    
    # For Parts, extract the topic after the identifier  
    part_match = re.search(r'Part\s+\d+\s*[-–]\s*(.+)', rule_title, re.IGNORECASE)
    if part_match:
        return part_match.group(1).strip()
    
    # For other titles, try to extract meaningful topic
    # Remove common prefixes and clean up
    topic = rule_title
    
    # Remove "Notes on" prefix if present
    topic = re.sub(r'^Notes on\s+', '', topic, flags=re.IGNORECASE)
    
    # If no clear pattern, return the title as-is
    return topic.strip()

def extract_rule_identifier(rule_title):
    """
    Extracts just the rule identifier (e.g., 'Practice Direction 2A', 'Part 14') from the full rule title.
    """
    # Match "Practice Direction X" (with optional letter) or "Part X"
    pd_match = re.match(r'(Practice Direction\s+\d+[A-Z]?)', rule_title, re.IGNORECASE)
    if pd_match:
        return pd_match.group(1).strip()
    part_match = re.match(r'(Part\s+\d+)', rule_title, re.IGNORECASE)
    if part_match:
        return part_match.group(1).strip()
    # Fallback: return the first part before a dash or en dash
    dash_split = re.split(r'\s*[-–]\s*', rule_title)
    if dash_split:
        return dash_split[0].strip()
    return rule_title.strip()

def extract_sourcepage_topic(rule_title):
    """
    Extract only the topic/title for sourcepage, not including the identifier.
    E.g., "Practice Direction 1A - participation of vulnerable parties or witnesses"
    -> "participation of vulnerable parties or witnesses"
    """
    # For Practice Directions, extract after the identifier and dash
    pd_match = re.match(r'Practice Direction\s+\d+[A-Z]?\s*[-–:]\s*(.+)', rule_title, re.IGNORECASE)
    if pd_match:
        return pd_match.group(1).strip()
    # For Parts, extract after the identifier and dash
    part_match = re.match(r'Part\s+\d+\s*[-–:]\s*(.+)', rule_title, re.IGNORECASE)
    if part_match:
        return part_match.group(1).strip()
    # If no match, fallback to previous logic (but avoid identifier)
    dash_split = re.split(r'\s*[-–:]\s*', rule_title, maxsplit=1)
    if len(dash_split) == 2:
        return dash_split[1].strip()
    return rule_title.strip()

def detect_and_preserve_sections(text):
    """
    Detect sections based on HTML structure markers and create section delimiters.
    Returns both flattened content (for embeddings) and sectioned content (for review).
    """
    if not text or len(text) < 10:
        return "", []
        
    # Check if we already have section markers from HTML extraction
    if '---SECTION---' in text:
        # We have explicit section markers from HTML structure
        sections = [s.strip() for s in text.split('---SECTION---') if s.strip()]
    else:
        # Create sections based on paragraph breaks (double newlines)
        # This preserves the natural structure of legal documents
        potential_sections = text.split('\n\n')
        sections = []
        
        for section in potential_sections:
            section = section.strip()
            if section and len(section) > 10:  # Only substantial sections
                sections.append(section)
    
    # If we have too many tiny sections, group them logically
    if len(sections) > 20:
        grouped_sections = []
        current_group = []
        current_length = 0
        max_group_length = 500  # Target length for grouped sections
        
        for section in sections:
            # If adding this section would exceed max length and we have content, start new group
            if current_length + len(section) > max_group_length and current_group:
                grouped_sections.append('\n\n'.join(current_group))
                current_group = [section]
                current_length = len(section)
            else:
                current_group.append(section)
                current_length += len(section) + 2  # +2 for \n\n
        
        # Add final group
        if current_group:
            grouped_sections.append('\n\n'.join(current_group))
        
        sections = grouped_sections
    
    # Create flattened content with section delimiters for frontend parsing
    flattened_content = '\n\n---\n\n'.join(section.strip() for section in sections if section.strip())
    
    # Return sections as list for review formatting
    sectioned_content = sections if sections else [text] if text else []
    
    return flattened_content, sectioned_content

def format_content_for_review(content):
    """
    Format content as a JSON array of sections for easy review.
    Each array element should be a distinct, readable section with proper line breaks.
    """
    if not content:
        return []
    
    # If content is already a list, return it cleaned
    if isinstance(content, list):
        return [str(s).strip() for s in content if str(s).strip()]
    
    # Split by section delimiters
    if '\n\n---\n\n' in content:
        sections = content.split('\n\n---\n\n')
    elif '---SECTION---' in content:
        sections = content.split('---SECTION---')
    else:
        # If no section delimiters, split by double newlines for reasonable chunks
        sections = content.split('\n\n')
    
    # Clean and filter sections
    formatted_sections = []
    for section in sections:
        section = section.strip()
        if section and len(section) > 10:  # Only substantial sections
            formatted_sections.append(section)
    
    # If we ended up with too many tiny sections, group them logically
    if len(formatted_sections) > 50:
        # Group small sections together
        grouped_sections = []
        current_group = []
        
        for section in formatted_sections:
            if len(section) < 100 and current_group:
                current_group.append(section)
            else:
                if current_group:
                    grouped_sections.append('\n\n'.join(current_group))
                    current_group = []
                grouped_sections.append(section)
        
        if current_group:
            grouped_sections.append('\n\n'.join(current_group))
        
        formatted_sections = grouped_sections
    
    return formatted_sections

def create_safe_filename(text, max_length=100):
    """Create a safe filename from text, handling length limits and invalid characters."""
    # Remove any invalid characters for filenames
    safe_text = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '_', text)
    
    # Truncate to max_length if necessary, ensuring not to cut off words
    if len(safe_text) > max_length:
        safe_text = re.sub(r'_[^_]*$', '', safe_text[:max_length])  # Remove last segment after underscore
        safe_text = safe_text.rstrip('_')  # Remove trailing underscore if any
    
    return safe_text

def create_azure_search_documents_from_rule(rule_title, rule_url, rule_id, last_updated, content):
    """
    Create document(s) in Azure Search OpenAI demo format from rule content.
    Only chunks content if it exceeds text-embedding-3-large token limit (8191 tokens).
    
    Args:
        rule_title: Full rule title
        rule_url: Rule URL
        rule_id: Base rule ID
        last_updated: Last update timestamp
        content: Complete rule content
        
    Returns:
        List of documents in Azure Search OpenAI demo format
    """
    # Initialize chunker with text-embedding-3-large limits (8191 tokens with safety margin)
    chunker = LegalDocumentChunker(max_tokens=7500, overlap_tokens=200)
    
    # Use only the topic/title for sourcepage
    sourcepage = extract_sourcepage_topic(rule_title)
    # Use only the identifier for sourcefile
    sourcefile = extract_rule_identifier(rule_title)
    
    # Detect sections and create both flattened and sectioned content
    flattened_content, sectioned_content = detect_and_preserve_sections(content)
    
    # Check if content needs chunking using flattened content
    token_count = chunker.count_tokens(flattened_content)
    
    # Always chunk if token_count > max_tokens, otherwise single doc
    if token_count > chunker.max_tokens:
        # Content exceeds limits - chunk it using flattened content
        # For chunking, temporarily remove section delimiters to get clean text
        clean_content_for_chunking = flattened_content.replace('\n\n---\n\n', ' ')
        chunks = chunker.chunk_legal_document(clean_content_for_chunking, rule_id, rule_title)
        
        documents = []
        
        for i, chunk_data in enumerate(chunks):
            # Create document ID for chunks
            doc_id = f"{rule_id}_chunk_{i+1:03d}"
            
            # Create document
            document = {
                # Core Azure Search OpenAI demo fields
                "id": doc_id,
                "content": chunk_data['text'],  # Chunked content (no section delimiters)
                "category": "Civil Procedure Rules and Practice Directions",
                "sourcepage": sourcepage,
                "sourcefile": sourcefile,
                "storageUrl": rule_url,
                "oids": [],
                "groups": [],
                "parent_id": rule_id,
                
                # Additional metadata
                "embedding": [],
                "updated": last_updated,
                # Store sectioned content for review formatting (internal use only)
                "_sectioned_content": sectioned_content if i == 0 else None
            }
            
            documents.append(document)
        
        return documents
    else:
        # Content fits within limits - create single document with section delimiters
        document = {
            # Core Azure Search OpenAI demo fields
            "id": rule_id,
            "content": flattened_content,  # Full content with section delimiters for frontend parsing
            "category": "Civil Procedure Rules and Practice Directions",
            "sourcepage": sourcepage,
            "sourcefile": sourcefile,
            "storageUrl": rule_url,
            "oids": [],
            "groups": [],
            "parent_id": rule_id,
            
            # Additional metadata
            "embedding": [],
            "updated": last_updated,
            # Store sectioned content for review formatting (internal use only)
            "_sectioned_content": sectioned_content
        }
        
        return [document]

def scrape_rule_content(link, driver=None):
    """Scrapes the content of a specific rule page and returns document(s)."""
    rule_title = link['title']
    rule_url = link['url']
    rule_id = create_safe_filename(rule_title)
    
    print(f"\n{'='*100}")
    print(f"PROCESSING: {rule_title}")
    print(f"URL: {rule_url}")
    print(f"Expected unique content for: {rule_title}")
    
    # Fetch page content with better debugging
    html_content = get_page_content(rule_url, driver)
    if not html_content:
        print(f"Failed to retrieve content for {rule_url}")
        return []
    
    # Check for common content patterns that suggest wrong page
    if "PRACTICE DIRECTION 1 A - PARTICIPATION OF VULNERABLE PARTIES" in html_content:
        if rule_title not in ["Practice Direction 1A: participation of vulnerable parties or witnesses", "Practice Direction 1A"]:
            print(f"WARNING: Found Practice Direction 1A content on page that should be '{rule_title}'")
            print("This suggests URL redirection or incorrect page loading")
    
    # Extract update date
    last_updated = extract_update_date(html_content)
    
    # Extract main content
    content = extract_content_chunks(html_content, rule_url)
    
    if len(content) < 50:
        print(f"Skipped {rule_title}: content too short after extraction")
        return []
    
    # Check if content matches expected rule
    content_lower = content.lower()
    title_words = rule_title.lower().replace('–', ' ').replace(':', '').split()
    
    # Remove common words
    significant_words = [word for word in title_words if word not in 
                        ['practice', 'direction', 'part', 'notes', 'on', 'of', 'the', 'a', 'an', 'and', 'or']]
    
    if significant_words:
        matches = sum(1 for word in significant_words if word in content_lower)
        match_ratio = matches / len(significant_words)
        
        print(f"Content match analysis:")
        print(f"  Significant words from title: {significant_words}")
        print(f"  Words found in content: {matches}/{len(significant_words)} ({match_ratio:.1%})")
        
        if match_ratio < 0.3 and rule_title != "Notes on Practice Directions":
            print(f"WARNING: Low content match for '{rule_title}' - may be wrong content")
    
    # Show content preview with hash for uniqueness tracking
    content_hash = hashlib.md5(content.encode()).hexdigest()[:12]
    preview = content[:300].replace('\n', '\\n')
    print(f"Content hash: {content_hash}")
    print(f"Content preview (300 chars): {preview}...")
    
    # Create documents
    documents = create_azure_search_documents_from_rule(rule_title, rule_url, rule_id, last_updated, content)
    
    print(f"Created {len(documents)} document(s) for {rule_title}")
    print(f"Content length: {len(content)} characters")
    
    return documents

def scrape_all_rules(links, driver=None):
    """Scrapes content from all rule pages and returns list of documents."""
    all_documents = []
    content_hashes = {}  # Track content hashes to detect duplicates
    
    # Don't use threading for now to better debug the issue
    print("Processing rules sequentially for better debugging...")
    
    for i, link in enumerate(links, 1):
        print(f"\n[{i}/{len(links)}] Processing: {link['title']}")
        
        try:
            documents = scrape_rule_content(link, driver)
            
            if documents:
                # Check for duplicate content
                main_doc = documents[0]
                content_hash = hashlib.md5(main_doc['content'].encode()).hexdigest()[:12]
                
                if content_hash in content_hashes:
                    print(f"⚠️  DUPLICATE CONTENT DETECTED!")
                    print(f"   Same content as: {content_hashes[content_hash]}")
                    print(f"   Current document: {link['title']}")
                else:
                    content_hashes[content_hash] = link['title']
                    print(f"✅ Unique content confirmed for: {link['title']}")
                
                all_documents.extend(documents)
            else:
                print(f"❌ No documents extracted from {link['title']}")
                
        except Exception as e:
            print(f"❌ Error processing {link['title']}: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\nContent uniqueness summary:")
    print(f"Total unique content hashes: {len(content_hashes)}")
    print(f"Total documents processed: {len(links)}")
    
    if len(content_hashes) < len(links):
        print(f"⚠️  WARNING: Found duplicate content! {len(links) - len(content_hashes)} duplicates detected")
    
    return all_documents

def create_individual_files_from_documents(all_documents, output_dir=None):
    """Create individual JSON files for each parent document, grouping chunks together."""
    output_dir = output_dir or PROCESSED_CIVIL_RULES_DIR
    os.makedirs(output_dir, exist_ok=True)
    files_created = 0

    # Group documents by parent_id
    parent_groups = {}
    for document in all_documents:
        parent_id = document.get('parent_id', document.get('id'))
        if parent_id not in parent_groups:
            parent_groups[parent_id] = []
        parent_groups[parent_id].append(document)

    for parent_id, documents in parent_groups.items():
        documents.sort(key=lambda x: x.get('id', ''))
        main_doc = next((doc for doc in documents if doc['id'] == parent_id), documents[0])
        individual_doc = main_doc.copy()

        # Use the same content as in main_doc (which has section delimiters)
        # Don't reformat it - it already has line breaks and section delimiters
        individual_doc['content'] = main_doc.get('content', '')

        individual_doc.pop('_sectioned_content', None)

        if len(documents) > 1:
            individual_doc['chunks'] = []
            for doc in documents:
                if doc['id'] != parent_id:
                    chunk_info = {
                        'id': doc['id'],
                        'content': doc.get('content', ''),
                        'updated': doc.get('updated')
                    }
                    individual_doc['chunks'].append(chunk_info)

        safe_filename = create_safe_filename(main_doc.get('sourcefile', main_doc.get('id', 'unknown')))
        file_path = os.path.join(output_dir, f"{safe_filename}.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(individual_doc, f, indent=2, ensure_ascii=False)
        files_created += 1
        chunk_info = f" ({len(documents)} chunks)" if len(documents) > 1 else ""
        print(f"Created: {file_path}{chunk_info}")
    return files_created

def create_flattened_output_file(all_documents, output_dir=None):
    """Create a single flattened JSON file with all documents."""
    output_dir = output_dir or PROCESSED_CIVIL_RULES_DIR
    os.makedirs(output_dir, exist_ok=True)

    embedding_documents = []
    for doc in all_documents:
        embedding_doc = doc.copy()
        embedding_doc.pop('_sectioned_content', None)
        embedding_documents.append(embedding_doc)

    flattened_output_path = os.path.join(output_dir, "civil_procedure_rules_flattened.json")
    with open(flattened_output_path, 'w', encoding='utf-8') as f:
        json.dump(embedding_documents, f, indent=2, ensure_ascii=False)

    # Review version: keep content as a single string with line breaks
    review_documents = []
    for doc in all_documents:
        review_doc = doc.copy()
        # format into array of sections with preserved line breaks
        if '_sectioned_content' in doc and doc['_sectioned_content']:
            review_doc['content'] = format_content_for_review(doc['_sectioned_content'])
        else:
            # if no sectioned content, split the flattened content
            review_doc['content'] = format_content_for_review(doc.get('content', ''))
        review_doc.pop('_sectioned_content', None)
        review_documents.append(review_doc)

    review_output_path = os.path.join(output_dir, "civil_procedure_rules_review.json")
    with open(review_output_path, 'w', encoding='utf-8') as f:
        json.dump(review_documents, f, indent=2, ensure_ascii=False)

    # Calculate statistics
    chunked_docs = [doc for doc in all_documents if doc['id'] != doc['parent_id']]
    unique_parents = set(doc['parent_id'] for doc in all_documents)
    chunked_parents = set(doc['parent_id'] for doc in chunked_docs)
    
    print(f"Created flattened output file (for embeddings): {flattened_output_path}")
    print(f"Created readable review file: {review_output_path}")
    print(f"Total documents: {len(all_documents)}")
    print(f"Unique source documents: {len(unique_parents)}")
    print(f"Documents that were chunked: {len(chunked_parents)}")
    print(f"Total chunks created: {len(chunked_docs)}")
    
    # Show sample document structure for verification
    if all_documents:
        sample_doc = all_documents[0]
        print(f"\nSample document structure:")
        print(f"  ID: {sample_doc.get('id', 'N/A')}")
        print(f"  Parent ID: {sample_doc.get('parent_id', 'N/A')}")
        print(f"  Content length: {len(sample_doc.get('content', ''))}")
        print(f"  Content type: {type(sample_doc.get('content', 'N/A'))}")
        print(f"  Category: {sample_doc.get('category', 'N/A')}")
        print(f"  Sourcepage: {sample_doc.get('sourcepage', 'N/A')}")
        print(f"  Sourcefile: {sample_doc.get('sourcefile', 'N/A')}")
        print(f"  Is chunked: {sample_doc['id'] != sample_doc['parent_id']}")
        
        # Show content sample with line breaks
        content = sample_doc.get('content', '')
        if content:
            lines = content.split('\n')[:5]  # First 5 lines
            print(f"  Content preview (first 5 lines):")
            for line in lines:
                print(f"    {line[:80]}..." if len(line) > 80 else f"    {line}")
    
    return flattened_output_path

def main():
    """Main function to run the scraper."""
    print("Starting civil rules scraping script...")
    print("Only chunking documents that exceed text-embedding-3-large token limits (7500 tokens with safety margin)!")
    print("Creating JSON files with content as strings containing line breaks...")
    print("Adding section delimiters (\\n\\n---\\n\\n) for frontend parsing...")
    
    # Create directories
    os.makedirs(INPUT_DIR, exist_ok=True)
    os.makedirs(PROCESSED_CIVIL_RULES_DIR, exist_ok=True)
    print(f"Input directory: {INPUT_DIR}")
    print(f"Output directory: {PROCESSED_CIVIL_RULES_DIR}")
    
    parser = argparse.ArgumentParser(description="Scrape Civil Procedure Rules")
    parser.add_argument("--force-all", action="store_true", help="Process all rules even if unchanged")
    parser.add_argument("--test-url", help="URL of single rule page to scrape for testing")
    parser.add_argument("--test-single", action="store_true", help="Test by processing only the first rule found")
    parser.add_argument("--test-few", type=int, help="Test by processing first N rules")
    args = parser.parse_args()
    print(f"DEBUG: parsed args = {args}")

    driver = setup_selenium_driver()
    try:
        # Accept cookies
        driver.get(BASE_URL)
        accept_cookies(driver)
        
        # Scrape links
        if args.test_url:
            print(f"Test mode: scraping only {args.test_url}")
            links = [{"title": "Test URL", "url": args.test_url}]
        else:
            links = scrape_links(driver, BASE_URL)
            
            # If test_single flag is set, only process the first rule
            if args.test_single and links:
                print(f"Test single mode: processing only the first rule - {links[0]['title']}")
                links = [links[0]]
            elif args.test_few is not None and links:
                num_to_process = min(args.test_few, len(links))
                print(f"Test few mode: processing first {num_to_process} rules")
                for i, link in enumerate(links[:num_to_process]):
                    print(f"  {i+1}. {link['title']}")
                links = links[:num_to_process]

        if links:
            print(f"Processing {len(links)} rule(s)...")
            
            # Scrape content from each link - now returns list of documents (potentially chunked)
            all_documents = scrape_all_rules(links, driver)
            
            if all_documents:
                print(f"Total documents extracted: {len(all_documents)}")
                
                # Show chunking statistics
                chunked_docs = [doc for doc in all_documents if doc['id'] != doc['parent_id']]
                unique_parents = set(doc['parent_id'] for doc in all_documents)
                chunked_parents = set(doc['parent_id'] for doc in chunked_docs)
                
                if chunked_docs:
                    print(f"Documents that required chunking: {len(chunked_parents)}")
                    print(f"Total chunks created: {len(chunked_docs)}")
                else:
                    print("No documents required chunking - all fit within token limits")
                
                # Create individual files based on parent document
                files_created = create_individual_files_from_documents(all_documents)
                
                # Create flattened output file
                flattened_output_path = create_flattened_output_file(all_documents)
                
                # Create summary with chunking information
                summary_path = os.path.join(PROCESSED_DIR, "civil_rules_summary.json")
                summary_data = {
                    "source_count": len(links),
                    "document_count": len(all_documents),
                    "chunked_document_count": len(chunked_docs),
                    "unique_source_count": len(unique_parents),
                    "chunked_source_count": len(chunked_parents),
                    "files_created": files_created,
                    "document_type": "civil_procedure_rules",
                    "category": "Civil Procedure Rules and Practice Directions",
                    "description": "The civil procedure rules and its practice directions make up a procedural code whose overriding aim is to enable the courts to deal with cases justly. Documents are only chunked if they exceed text-embedding-3-large token limits (7500 tokens with safety margin).",
                    "output_file": flattened_output_path,
                    "review_file": os.path.join(PROCESSED_CIVIL_RULES_DIR, "civil_procedure_rules_review.json"),
                    "individual_files_directory": PROCESSED_CIVIL_RULES_DIR,
                    "format": "azure_search_openai_demo_compatible",
                    "structure": "minimal_chunking_only_when_necessary",
                    "chunking_strategy": "text_embedding_3_large_token_limit_based",
                    "max_tokens_per_chunk": 7500,
                    "embedding_model": "text-embedding-3-large",
                    "content_format": "string_with_line_breaks_and_section_delimiters",
                    "section_delimiters": "\\n\\n---\\n\\n for frontend parsing",
                    "test_mode": args.test_single or bool(args.test_url) or (args.test_few is not None)
                }
                
                with open(summary_path, 'w', encoding='utf-8') as f:
                    json.dump(summary_data, f, indent=2)
                
                print(f"✅ Processing complete!")
                print(f"📄 Generated {len(all_documents)} documents from {len(unique_parents)} sources")
                if chunked_docs:
                    print(f"🔄 {len(chunked_parents)} documents were chunked due to token limits")
                else:
                    print(f"✨ All documents fit within token limits - no chunking needed")
                print(f"📁 Created {files_created} individual files")
                print(f"💾 Flattened file (embeddings): {flattened_output_path}")
                print(f"📖 Review file: {os.path.join(PROCESSED_CIVIL_RULES_DIR, 'civil_procedure_rules_review.json')}")
                print(f"📂 Individual files: {PROCESSED_CIVIL_RULES_DIR}")
                print(f"📊 Summary: {summary_path}")
                print(f"🏷️  Category: Civil Procedure Rules and Practice Directions")
                print(f"🔍 Content format: Single string with line breaks and section delimiters")
                print(f"📝 Frontend parsing: Use document.content.split('\\n\\n---\\n\\n') to get sections")
                print(f"🧠 Ready for Azure Search indexing with text-embedding-3-large compatible documents")
    
    finally:
        # Always close the driver
        if driver:
            driver.quit()
            print("Browser driver closed.")

def install_missing_packages():
    """Install any missing packages required for the scraper to run."""
    required_packages = [
        "websocket-client",
        "requests",
        "beautifulsoup4",
        "selenium",
        "webdriver-manager"
    ]
    
    # Install each package using pip
    for package in required_packages:
        try:
            print(f"Installing package: {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"Successfully installed {package}")
        except Exception as e:
            print(f"Failed to install {package}: {e}")
            print("Please install it manually using: pip install " + package)

# --- MAIN SCRIPT EXECUTION ---
if __name__ == "__main__":
    try:
        import requests
        from bs4 import BeautifulSoup
        try:
            # Try traditional import
            import websocket
        except ImportError:
            try:
                # Try alternate approach for importing websocket
                from websocket import WebSocketApp
                print("Found WebSocketApp through direct import.")
            except ImportError:
                print("Installing websocket-client package...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", "websocket-client"])
                import websocket
                print("Successfully installed and imported websocket")
        
        # Try to import selenium
        try:
            from selenium import webdriver
            from webdriver_manager.chrome import ChromeDriverManager
        except ImportError:
            print("Selenium not found. Installing selenium and webdriver-manager...")
            import subprocess
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "selenium", "webdriver-manager"])
                print("Successfully installed selenium and webdriver-manager")
                from selenium import webdriver
                from webdriver_manager.chrome import ChromeDriverManager
            except Exception as e:
                print(f"Failed to install selenium: {e}")
                print("Please install manually:")
                print("  pip install selenium webdriver-manager")
                sys.exit(1)
        
        # --- ADD THIS TO DEBUG SCRIPT EXECUTION ---
        print("Script started. If you see this, the script is running.")
        main()
        
    except ImportError as e:
        print(f"Missing module: {e.name if hasattr(e, 'name') else str(e)}.")
        print("Please activate your virtual environment and install dependencies with:")
        print("  pip install websocket-client requests beautifulsoup4 selenium webdriver-manager")
        # Fix the requirements.txt path
        req_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../requirements.txt"))
        print(f"  pip install -r {req_path}")
        
        # Try to auto-install if possible
        try:
            print("\nAttempting to auto-install dependencies...")
            install_missing_packages()
            print("Dependencies installed. Please run the script again.")
        except Exception as install_error:
            print(f"Auto-installation failed: {install_error}")
            print("Please install dependencies manually.")
        
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)