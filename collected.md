`./ECI_initiatives/scraper/responses/browser.py`:
```
"""
Browser initialization and management for Commission responses scraper.
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from .consts import CHROME_OPTIONS, LOG_MESSAGES
from .scraper_logger import logger


def initialize_browser() -> webdriver.Chrome:
    """
    Initialize Chrome WebDriver with headless options.

    Returns:
        webdriver.Chrome: Configured Chrome WebDriver instance
    """
    chrome_options = Options()

    # Add all configured options
    for option in CHROME_OPTIONS:
        chrome_options.add_argument(option)

    logger.info(LOG_MESSAGES["browser_init"])

    driver = webdriver.Chrome(options=chrome_options)

    logger.debug(LOG_MESSAGES["browser_success"])

    return driver

```

`./ECI_initiatives/scraper/responses/consts.py`:
```
"""
Constants and configuration for Commission responses scraper.
"""
import datetime
from pathlib import Path

# Timing - start of scraping session
START_SCRAPING = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

# URLs and Routes
BASE_URL = "https://citizens-initiative.europa.eu"

# Directory Structure
DATA_DIR_NAME = "data"
LOG_DIR_NAME = "logs"
RESPONSES_DIR_NAME = "responses"
INITIATIVE_PAGES_DIR_NAME = "initiative_pages"

# Script directory (3 levels up from this file: responses -> scraper -> ECI_initiatives)
SCRIPT_DIR = Path(__file__).parent.parent.parent.absolute()

# Timing Configuration (in seconds)
WAIT_DYNAMIC_CONTENT = (1.5, 1.9)
WAIT_BETWEEN_DOWNLOADS = (1.5, 1.9)
RETRY_WAIT_BASE = (2.0, 2.5)

# Timeout Configuration (in seconds)
WEBDRIVER_TIMEOUT_DEFAULT = 30
WEBDRIVER_TIMEOUT_CONTENT = 15

# Browser Configuration
CHROME_OPTIONS = [
    "--headless",
    "--no-sandbox",
    "--disable-dev-shm-usage",
]

# File Naming Patterns
RESPONSE_PAGE_FILENAME_PATTERN = "{year}/{number}_en.html"

# Retry and validation
DEFAULT_MAX_RETRIES = 3
MIN_HTML_LENGTH = 50

# Rate limiting indicators
RATE_LIMIT_INDICATORS = [
    "Server inaccessibility",
    "429 - Too Many Requests",
    "HTTP 429",
    "Too Many Requests",
    "Rate limited"
]

# Log messages
LOG_MESSAGES = {
    # Scraping lifecycle
    "scraping_start": "Starting Commission responses scraping at {timestamp} directory",
    "scraping_complete": "COMMISSION RESPONSES SCRAPING FINISHED!",

    # Browser
    "browser_init": "Initializing browser...",
    "browser_success": "Browser initialized successfully",
    "browser_closed": "Browser closed",

    # Link extraction
    "links_found": "Found {count} Commission response links",
    "no_links_found": "No Commission response links found",

    # Download
    "download_success": "Successfully downloaded {filename}",
    "download_failed": "Failed to download {url}",
    "rate_limit_retry": "Received rate limiting. Retrying ({retry}/{max_retries}) in {wait_time:.1f} seconds...",

    # Summary
    "completion_timestamp": "Scraping completed at {timestamp}",
    "start_time": "Start time: {start_scraping}",
    "total_links_found": "Total response links found: {count}",
    "pages_downloaded": "Pages downloaded: {downloaded_count}/{total_count}",
    "failed_downloads": "Failed downloads: {failed_count}",
    "failed_url": "  - {failed_url}",
    "all_downloads_successful": "All downloads successful!",
    "files_saved_in": "Files saved in: {path}",
    "divider_line": "=" * 60
}

```

`./ECI_initiatives/scraper/responses/css_selectors.py`:
```
"""
CSS selectors for Commission response pages.
"""


class ResponsePageSelectors:
    """CSS selectors for Commission response page elements."""

    # Main content area
    PAGE_HEADER_TITLE = "h1.ecl-page-header-core__title"

    # Content sections (to verify page loaded)
    MAIN_CONTENT = "div.ecl-container"

    # Timeline or status information
    INITIATIVE_PROGRESS = "ol.ecl-timeline"

```

`./ECI_initiatives/scraper/responses/downloader.py`:
```
"""
Download Commission response pages using Selenium.
"""
import datetime
import random
import time
from typing import List, Dict, Tuple

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .browser import initialize_browser
from .css_selectors import ResponsePageSelectors
from .consts import (
    WAIT_DYNAMIC_CONTENT,
    WAIT_BETWEEN_DOWNLOADS,
    RETRY_WAIT_BASE,
    WEBDRIVER_TIMEOUT_CONTENT,
    DEFAULT_MAX_RETRIES,
    RATE_LIMIT_INDICATORS,
    LOG_MESSAGES
)
from .file_operations import save_response_page
from .scraper_logger import logger


class ResponseDownloader:
    """Download Commission response pages with retry logic and error handling."""

    def __init__(self, responses_dir: str):
        """
        Initialize the downloader.

        Args:
            responses_dir: Base directory for saving response HTML files
        """

        self.responses_dir = responses_dir
        self.driver = None

    def download_all_responses(self, response_links: List[Dict[str, str]]) -> Tuple[int, List[str]]:
        """
        Download all Commission response pages with retry logic for failures.
        
        Args:
            response_links: List of dictionaries with 'url', 'year', 'reg_number'
            
        Returns:
            Tuple of (downloaded_count, failed_urls_list)
        """
        downloaded_count = 0
        failed_items = []
        
        try:
            # Initialize browser once for all downloads
            self._initialize_driver()
            
            # First pass: Download each response page
            logger.info("Starting first download pass...")
            for link_data in response_links:
                
                url = link_data['url']
                year = link_data['year']
                reg_number = link_data['reg_number']
                
                success = self.download_single_response(url, year, reg_number)
                
                if success:
                    downloaded_count += 1
                else:
                    # Store full link_data for retry
                    failed_items.append(link_data)
                
                # Wait between downloads to avoid rate limiting
                wait_time = random.uniform(*WAIT_BETWEEN_DOWNLOADS)
                time.sleep(wait_time)
            
        finally:
            # Clean up browser
            self._close_driver()

        return downloaded_count, failed_items

    def download_single_response(
        self, 
        url: str, 
        year: str, 
        reg_number: str,
        max_retries: int = DEFAULT_MAX_RETRIES
    ) -> bool:
        """
        Download a single Commission response page with retry logic.

        Args:
            url: Full URL to the response page
            year: Year of the initiative
            reg_number: Registration number
            max_retries: Maximum number of retry attempts

        Returns:
            True if successful, False if failed
        """

        actual_url = url

        for attempt in range(max_retries):

            try:

                # On first attempt, check if URL redirects
                if attempt == 0:
                    self.driver.get(url)
                    time.sleep(1)  # Wait for redirect
                    actual_url = self.driver.current_url
                    
                    # Log redirect if it occurred
                    if actual_url != url:
                        logger.info(f"URL redirected: {url} -> {actual_url}")
                else:
                    # Use actual URL for retry attempts
                    self.driver.get(actual_url)

                # Wait for page content to load
                self._wait_for_page_content()

                # Check for rate limiting
                self._check_rate_limiting()

                # Wait for dynamic content
                wait_time = random.uniform(*WAIT_DYNAMIC_CONTENT)
                time.sleep(wait_time)

                # Get page source
                page_source = self.driver.page_source

                # Save to file
                filename = save_response_page(self.responses_dir, year, reg_number, page_source)

                logger.info(LOG_MESSAGES["download_success"].format(filename=filename))
                return True

            except Exception as e:
                logger.warning(f"Download attempt {attempt + 1}/{max_retries} failed for {url}: {str(e)}")

                if attempt < max_retries - 1:

                    # Calculate exponential backoff wait time
                    base_wait = random.uniform(*RETRY_WAIT_BASE)
                    wait_time = base_wait * (2 ** attempt)
                    logger.info(LOG_MESSAGES["rate_limit_retry"].format(
                        retry=attempt + 1,
                        max_retries=max_retries,
                        wait_time=wait_time
                    ))
                    time.sleep(wait_time)

        logger.error(LOG_MESSAGES["download_failed"].format(url=url))
        return False

    def _check_rate_limiting(self) -> None:
        """
        Check if the current page shows rate limiting errors.

        Raises:
            Exception: If rate limiting is detected
        """

        page_source = self.driver.page_source.lower()

        for indicator in RATE_LIMIT_INDICATORS:
            if indicator.lower() in page_source:
                raise Exception(f"Rate limiting detected: {indicator}")

    def _wait_for_page_content(self) -> None:
        """
        Wait for response page content to load.
        
        Uses explicit waits for specific page elements with fallback selectors.
        """
        
        try:
            # Try multiple selectors in order of preference
            selectors_to_try = [
                ResponsePageSelectors.MAIN_CONTENT,  # div.ecl-container
                ResponsePageSelectors.PAGE_HEADER_TITLE,  # h1.ecl-page-header__title  
                "main#main-content",  # Main content area
                "body"  # Last resort fallback
            ]
            
            for selector in selectors_to_try:
                try:
                    WebDriverWait(self.driver, WEBDRIVER_TIMEOUT_CONTENT).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    logger.debug(f"Page loaded - found element: {selector}")
                    return  # Success - exit method
                except Exception:
                    continue  # Try next selector
            
            # If we get here, no selectors worked but page might still be loaded
            logger.warning("Could not verify page load with expected selectors, proceeding anyway")
            
        except Exception as e:
            logger.warning(f"Timeout waiting for page content: {str(e)}")

    def _initialize_driver(self) -> None:
        """Initialize the WebDriver if not already initialized."""

        if self.driver is None:
            self.driver = initialize_browser()

    def _close_driver(self) -> None:
        """Close the WebDriver and clean up resources."""

        if self.driver:
            try:
                self.driver.quit()
                logger.info(LOG_MESSAGES["browser_closed"])
            except Exception as e:
                logger.error(f"Error closing browser: {str(e)}")
            finally:
                self.driver = None

```

`./ECI_initiatives/scraper/responses/file_operations.py`:
```
"""
File operations for saving Commission response pages.
"""
import os
from typing import Optional

from bs4 import BeautifulSoup

from .consts import MIN_HTML_LENGTH, RATE_LIMIT_INDICATORS
from .scraper_logger import logger


class FileOperations:
    """Handle file and directory operations for response pages."""
    
    def __init__(self, base_dir: str):
        """
        Initialize file operations handler.
        
        Args:
            base_dir: Base directory for saving files
        """
        self.base_dir = base_dir
    
    def setup_directories(self) -> None:
        """
        Create necessary directory structure for responses.
        Creates: base_dir/ and subdirectories as needed.
        Logs only when directory is actually created.
        """
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir, exist_ok=True)
            logger.info(f"Created responses directory: {self.base_dir}")
    
    def save_response_page(
        self, 
        page_source: str, 
        year: str, 
        reg_number: str
    ) -> str:
        """
        Save Commission response page HTML to file.
        
        Args:
            page_source: HTML content to save
            year: Year of the initiative
            reg_number: Registration number
            
        Returns:
            Filename of saved file
            
        Raises:
            Exception: If rate limiting content detected or save fails
        """

        # Validate HTML
        self._validate_html(page_source)
        
        # Create year directory
        year_dir = self._create_year_directory(year)
        
        # Generate filename
        filename = self._generate_filename(year, reg_number)
        full_path = os.path.join(self.base_dir, filename)
        
        # Prettify HTML
        soup = BeautifulSoup(page_source, 'html.parser')
        pretty_html = soup.prettify()
        
        # Save to file
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(pretty_html)
        
        logger.debug(f"Saved response page: {filename}")
        
        return filename
    
    def _validate_html(self, page_source: str) -> bool:
        """
        Validate HTML content for rate limiting and malformed content.
        
        Args:
            page_source: HTML content to validate
            
        Returns:
            True if valid, False otherwise
            
        Raises:
            Exception: If rate limiting detected
        """

        # Check minimum length
        if len(page_source) < MIN_HTML_LENGTH:
            raise Exception(f"HTML content too short: {len(page_source)} characters")
        
        # Check for error page (multilingual "Sorry" page)
        error_page_indicators = [
            "We apologise for any inconvenience",
            "Veuillez nous excuser pour ce désagrément",
            "Ci scusiamo per il disagio arrecato"
        ]
        
        page_lower = page_source.lower()
        
        for indicator in error_page_indicators:
            if indicator.lower() in page_lower:
                raise Exception(f"Error page detected: {indicator}")
        
        # Check for rate limiting indicators
        for indicator in RATE_LIMIT_INDICATORS:
            if indicator.lower() in page_lower:
                raise Exception(f"Rate limiting detected in content: {indicator}")
        
        return True
    
    def _create_year_directory(self, year: str) -> str:
        """
        Create year-specific subdirectory.
        
        Args:
            year: Year string
            
        Returns:
            Full path to year directory
        """

        year_dir = os.path.join(self.base_dir, year)
        os.makedirs(year_dir, exist_ok=True)

        return year_dir
    
    def _generate_filename(self, year: str, reg_number: str) -> str:
        """
        Generate filename for response page.
        
        Args:
            year: Year of initiative
            reg_number: Registration number
            
        Returns:
            Filename in format: {year}/{reg_number}_en.html
        """

        return f"{year}/{reg_number}_en.html"


def save_response_page(responses_dir: str, year: str, reg_number: str, page_source: str) -> str:
    """
    Convenience function to save response page.
    
    Args:
        responses_dir: Base directory for responses
        year: Year of initiative
        reg_number: Registration number
        page_source: HTML content
        
    Returns:
        Filename of saved file
    """
    
    file_ops = FileOperations(responses_dir)
    return file_ops.save_response_page(page_source, year, reg_number)

```

`./ECI_initiatives/scraper/responses/html_parser.py`:
```
"""
HTML parser for extracting Commission response links from initiative pages.
"""
import re
from typing import List, Dict, Optional
from pathlib import Path
from bs4 import BeautifulSoup

from .scraper_logger import logger


class ResponseLinkExtractor:
    """Extract Commission response links from initiative page HTML files."""
    
    def __init__(self):
        """Initialize the link extractor."""
        pass
    
    def extract_links_from_file(self, file_path: str) -> Optional[Dict[str, str]]:
        """
        Extract Commission response link from a single initiative HTML file.
        
        Args:
            file_path: Path to the initiative HTML file
            
        Returns:
            Dictionary with 'url', 'year', 'reg_number' or None if no link found
        """

        try:
            # Read HTML file
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Parse HTML for link
            url = self._parse_html_for_link(html_content, file_path)
            
            if not url:
                return None
            
            # Extract metadata from file path
            metadata = self._extract_metadata_from_path(file_path)
            
            return {
                'url': url,
                'year': metadata['year'],
                'reg_number': metadata['reg_number']
            }
            
        except Exception as e:
            logger.error(f"Error extracting link from {file_path}: {str(e)}")
            return None
    
    def extract_links_from_directory(self, base_dir: str) -> List[Dict[str, str]]:
        """
        Extract all Commission response links from initiative pages directory.
        
        Args:
            base_dir: Base directory containing initiative_pages/<year>/<reg_number>_en.html
            
        Returns:
            List of dictionaries with response link information
        """

        response_links = []
        base_path = Path(base_dir)
        
        # Traverse all year directories
        for year_dir in base_path.iterdir():

            if not year_dir.is_dir():
                continue
            
            # Process all HTML files in year directory
            for html_file in year_dir.glob("*_en.html"):

                link_data = self.extract_links_from_file(str(html_file))
                if link_data:
                    response_links.append(link_data)
        
        return response_links
    
    def _parse_html_for_link(self, html_content: str, file_path: str) -> Optional[str]:
        """
        Parse HTML content and extract Commission response link.
        
        Args:
            html_content: HTML content as string
            file_path: Path to the file (for logging purposes)
            
        Returns:
            Full URL to Commission response page or None
        """
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find Commission response link using text matching
            url = self._extract_response_commission_url(soup)
            
            if url:
                logger.debug(f"Found Commission response link in {file_path}: {url}")
            
            return url
            
        except Exception as e:
            logger.error(f"Error parsing HTML from {file_path}: {str(e)}")
            return None
    
    def _extract_metadata_from_path(self, file_path: str) -> Dict[str, str]:
        """
        Extract year and registration number from file path.
        
        Args:
            file_path: Path like 'initiative_pages/2019/000007_en.html'
            
        Returns:
            Dictionary with 'year' and 'reg_number'
        """
        path = Path(file_path)
        year = path.parent.name  # Get year from directory name
        reg_number = path.stem.replace('_en', '')  # Get reg number from filename
        
        return {
            'year': year,
            'reg_number': reg_number
        }
    
    def _extract_response_commission_url(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Extract the Commission's answer and follow-up page URL.
        
        Finds the <a> tag containing text "Commission's answer and follow-up"
        and returns its href attribute. Handles both regular apostrophe and Unicode right single quotation mark.
        
        Args:
            soup: BeautifulSoup parsed HTML
            
        Returns:
            URL to the initiative's follow-up page, or None if not found
        """

        # Find the link with text containing "Commission's answer and follow-up"
        # Pattern handles both regular apostrophe (') and Unicode right single quotation mark (\u2019)
        link = soup.find('a', string=re.compile(r"Commission['\u2019]s answer and follow-up", re.I))
        
        if link and link.get('href'):
            return link.get('href')
        
        return None

```

`./ECI_initiatives/scraper/responses/__init__.py`:
```

```

`./ECI_initiatives/scraper/responses/__main__.py`:
```
"""
Main entry point for Commission responses scraper.
"""
import os
import time
from typing import List, Tuple
from pathlib import Path
import logging

from .html_parser import ResponseLinkExtractor
from .downloader import ResponseDownloader
from .file_operations import FileOperations
from .statistics import display_completion_summary
from .consts import (
    START_SCRAPING,
    SCRIPT_DIR,
    DATA_DIR_NAME,
    RESPONSES_DIR_NAME,
    INITIATIVE_PAGES_DIR_NAME,
    LOG_DIR_NAME,
    LOG_MESSAGES
)


def scrape_commission_responses() -> str:
    """
    Main function to scrape Commission response pages.
    
    Returns:
        Timestamp string of when scraping started
    """
    
    # Step 1: Find the last timestamp directory FIRST
    try:
        timestamp_dir = _find_latest_timestamp_directory()
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        raise
    
    # Step 2: Setup log directory and initialize logger
    log_dir = os.path.join(timestamp_dir, LOG_DIR_NAME)
    print(f"Creating log file in: {log_dir}")
    
    # Import and initialize logger AFTER finding timestamp_dir
    from .scraper_logger import initialize_logger
    logger = initialize_logger(log_dir)
    
    logger.info(LOG_MESSAGES["scraping_start"].format(timestamp=timestamp_dir))
    
    # Step 3: Find latest initiative pages directory using the timestamp_dir
    initiative_pages_dir = _find_latest_initiative_pages_directory(timestamp_dir)
    
    if not initiative_pages_dir:
        logger.error("No initiative pages directory found in the timestamp directory.")
        return START_SCRAPING
    
    # Step 4: Setup responses output directory
    responses_dir = os.path.join(timestamp_dir, RESPONSES_DIR_NAME)
    file_ops = FileOperations(responses_dir)
    file_ops.setup_directories()
    
    # Step 5: Extract Commission response links from initiative pages
    response_links = _extract_response_links(initiative_pages_dir)
    
    if not response_links:
        logger.warning(LOG_MESSAGES["no_links_found"])
        return START_SCRAPING
    
    logger.info(LOG_MESSAGES["links_found"].format(count=len(response_links)))
    
    # Step 6: Download response pages
    downloaded_count, failed_items = _download_responses(responses_dir, response_links)

    # Step 7: Display completion summary
    display_completion_summary(START_SCRAPING, response_links, failed_items, downloaded_count, responses_dir)
        
    return START_SCRAPING


def _find_latest_timestamp_directory() -> str:
    """
    Find the most recent timestamp directory in the data folder.
    
    Returns:
        Full path to the latest timestamp directory
        
    Raises:
        FileNotFoundError: If no timestamp directory is found
    """
    data_dir = os.path.join(SCRIPT_DIR, DATA_DIR_NAME)
    
    if not os.path.exists(data_dir):
        raise FileNotFoundError(f"Data directory does not exist: {data_dir}")
    
    # Find all timestamp directories
    timestamp_dirs = [
        d for d in os.listdir(data_dir) 
        if os.path.isdir(os.path.join(data_dir, d))
    ]
    
    if not timestamp_dirs:
        raise FileNotFoundError(f"No timestamp directories found in: {data_dir}")
    
    # Sort to get latest (most recent timestamp)
    timestamp_dirs.sort(reverse=True)
    latest_timestamp_dir = os.path.join(data_dir, timestamp_dirs[0])
    
    return latest_timestamp_dir


def _find_latest_initiative_pages_directory(timestamp_dir: str) -> str:
    """
    Find the initiative pages directory within a given timestamp directory.
    
    Args:
        timestamp_dir: Path to the timestamp directory
    
    Returns:
        Path to initiative_pages directory or empty string if not found
    """
    initiative_pages_path = os.path.join(timestamp_dir, INITIATIVE_PAGES_DIR_NAME)
    
    if os.path.exists(initiative_pages_path):
        return initiative_pages_path
    
    return ""


def _extract_response_links(initiative_pages_dir: str) -> List[dict]:
    """
    Extract Commission response links from initiative pages.
    
    Args:
        initiative_pages_dir: Directory containing initiative HTML files
        
    Returns:
        List of response link dictionaries
    """
    extractor = ResponseLinkExtractor()
    return extractor.extract_links_from_directory(initiative_pages_dir)


def _download_responses(
    responses_dir: str,
    response_links: List[dict]
) -> Tuple[int, List[str]]:
    """
    Download all Commission response pages.
    
    Args:
        responses_dir: Directory to save response pages
        response_links: List of response link dictionaries
        
    Returns:
        Tuple of (downloaded_count, failed_urls)
    """
    downloader = ResponseDownloader(responses_dir)
    return downloader.download_all_responses(response_links)


if __name__ == "__main__":
    scrape_commission_responses()

```

`./ECI_initiatives/scraper/responses/scraper_logger.py`:
```
"""
Logger implementation for Commission responses scraper.
"""
import logging
import os
import datetime


def initialize_logger(log_dir: str):
    """
    Initialize and return a logger instance with file and console handlers.
    
    Args:
        log_dir: Directory for log files
        
    Returns:
        Logger instance
    """
    # Create logger
    logger = logging.getLogger("ECIResponsesScraper")
    logger.setLevel(logging.DEBUG)
    
    # Clear existing handlers to avoid duplicates
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Create log directory
    os.makedirs(log_dir, exist_ok=True)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file = os.path.join(log_dir, f"scraper_responses_{timestamp}.log")
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    logger.info(f"Log file created: {log_file}")
    
    return logger


# Global logger instance (will be initialized in __main__.py)
logger = None

```

`./ECI_initiatives/scraper/responses/statistics.py`:
```
"""
Statistics gathering and display for scraping completion summary.
"""
import datetime
from typing import List, Dict
import logging

from .consts import LOG_MESSAGES


class ScrapingStatistics:
    """Gather and display statistics for scraping session."""
    
    def __init__(self, start_scraping: str, responses_dir: str):
        """
        Initialize statistics tracker.
        
        Args:
            start_scraping: Timestamp when scraping started
            responses_dir: Directory where responses were saved
        """
        self.start_scraping = start_scraping
        self.responses_dir = responses_dir
        self.logger = logging.getLogger("ECIResponsesScraper")

    def display_completion_summary(
        self,
        response_links: List[Dict[str, str]],
        failed_urls: List[str],
        downloaded_count: int
    ) -> None:
        """
        Display comprehensive completion summary.
        
        Args:
            response_links: List of all response link dictionaries
            failed_urls: List of URLs that failed to download
            downloaded_count: Number of successfully downloaded pages
        """
        self._display_summary_header()
        self._display_download_results(len(response_links), downloaded_count, failed_urls)
        self._display_file_locations()
    
    def _display_summary_header(self) -> None:
        """Display summary header with completion timestamp."""
        self.logger.info(LOG_MESSAGES["divider_line"])
        self.logger.info(LOG_MESSAGES["scraping_complete"])
        self.logger.info(LOG_MESSAGES["divider_line"])
        
        completion_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.logger.info(LOG_MESSAGES["completion_timestamp"].format(timestamp=completion_time))
        self.logger.info(LOG_MESSAGES["start_time"].format(start_scraping=self.start_scraping))
    
    def _display_download_results(
        self,
        total_links: int,
        downloaded_count: int,
        failed_urls: List[str]
    ) -> None:
        """
        Display download results statistics.
        
        Args:
            total_links: Total number of response links found
            downloaded_count: Number of successful downloads
            failed_urls: List of failed URLs
        """
        self.logger.info(LOG_MESSAGES["total_links_found"].format(count=total_links))
        self.logger.info(LOG_MESSAGES["pages_downloaded"].format(
            downloaded_count=downloaded_count,
            total_count=total_links
        ))
        
        if failed_urls:
            self.logger.warning(LOG_MESSAGES["failed_downloads"].format(failed_count=len(failed_urls)))
            for url in failed_urls:
                self.logger.warning(LOG_MESSAGES["failed_url"].format(failed_url=url))
        else:
            self.logger.info(LOG_MESSAGES["all_downloads_successful"])
    
    def _display_file_locations(self) -> None:
        """Display information about where files were saved."""
        self.logger.info(LOG_MESSAGES["files_saved_in"].format(path=self.responses_dir))
        self.logger.info(LOG_MESSAGES["divider_line"])


def display_completion_summary(
    start_scraping: str,
    response_links: List[Dict[str, str]],
    failed_urls: List[str],
    downloaded_count: int,
    responses_dir: str
) -> None:
    """
    Convenience function to display completion summary.
    
    Args:
        start_scraping: Timestamp when scraping started
        response_links: List of all response link dictionaries
        failed_urls: List of URLs that failed to download
        downloaded_count: Number of successfully downloaded pages
        responses_dir: Directory where responses were saved
    """
    stats = ScrapingStatistics(start_scraping, responses_dir)
    stats.display_completion_summary(response_links, failed_urls, downloaded_count)

```

