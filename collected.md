`./ECI_initiatives/scraper/initiatives/browser.py`:
```
# Browser initialization and management
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Local
from .consts import CHROME_OPTIONS, LOG_MESSAGES
from .scraper_logger import logger


def initialize_browser() -> webdriver.Chrome:
    """Initialize Chrome WebDriver with headless options."""

    chrome_options = Options()
    for option in CHROME_OPTIONS:
        chrome_options.add_argument(option)

    logger.info(LOG_MESSAGES["browser_init"])
    driver = webdriver.Chrome(options=chrome_options)
    logger.debug(LOG_MESSAGES["browser_success"])

    return driver

```

`./ECI_initiatives/scraper/initiatives/consts.py`:
```
# python
import datetime
import os
from pathlib import Path

# The program is so small that we can treat it as init during running it
START_SCRAPING = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

# URLs and Routes
BASE_URL = "https://citizens-initiative.europa.eu"
ROUTE_FIND_INITIATIVE = "/find-initiative_en"

# Directory Structure
DATA_DIR_NAME = "data"
LOG_DIR_NAME = "logs"
LISTINGS_DIR_NAME = "listings"
PAGES_DIR_NAME = "initiative_pages"
SCRIPT_DIR = Path(__file__).parent.parent.parent.absolute()
LOG_DIR = os.path.join(SCRIPT_DIR, DATA_DIR_NAME, START_SCRAPING, LOG_DIR_NAME)

# Timing Configuration (in seconds)
WAIT_DYNAMIC_CONTENT = (1.5, 1.9)
WAIT_BETWEEN_PAGES = (1.0, 2.0)
WAIT_BETWEEN_DOWNLOADS = (0.5, 1.5)
RETRY_WAIT_BASE = (1.0, 1.2)

# Timeout Configuration (in seconds)
WEBDRIVER_TIMEOUT_DEFAULT = 30
WEBDRIVER_TIMEOUT_CONTENT = 15

# Browser Configuration
CHROME_OPTIONS = ["--headless", "--no-sandbox", "--disable-dev-shm-usage"]

# File Naming Patterns
LISTING_PAGE_FILENAME_PATTERN = (
    "Find_initiative_European_Citizens_Initiative_page_{:03d}.html"
)
LISTING_PAGE_MAIN_FILENAME = "Find_initiative_European_Citizens_Initiative.html"
INITIATIVE_PAGE_FILENAME_PATTERN = "{year}_{number}.html"

CSV_FIELDNAMES = [
    "url",
    "current_status",
    "registration_number",
    "signature_collection",
    "datetime",
]
CSV_FILENAME = "initiatives_list.csv"

DEFAULT_MAX_RETRIES = 5

MIN_HTML_LENGTH = 50

RATE_LIMIT_INDICATORS = [
    "Server inaccessibility",
    "429 - Too Many Requests",
    "429",
    "Too Many Requests",
    "Rate limited",
]

LOG_MESSAGES = {
    "scraping_start": "Starting scraping at: {timestamp}",
    "browser_init": "Initializing browser...",
    "browser_success": "Browser initialized successfully",
    "browser_closed": "Browser closed",
    "page_loaded": "Initiatives loaded successfully on page {page}",
    "page_saved": "Page {page} saved to: {path}",
    "next_button_found": "Found 'Next' button on page {page}, navigating to page {next_page}",
    "last_page": "No 'Next' button found on page {page}. This appears to be the last page.",
    "download_success": "✅ Successfully downloaded: {filename}",
    "rate_limit_retry": "⚠️  Received rate limiting. Retrying {retry}/{max_retries} in {wait_time:.1f} seconds...",
    "pages_browser_closed": "Individual pages browser closed",
    "summary_scraping": {
        "scraping_complete": "🎉 SCRAPING FINISHED! 🎉",
        "completion_timestamp": "Scraping completed at: {timestamp}",
        "start_time": "Start time: {start_scraping}",
        "total_pages_scraped": "Total pages scraped: {page_count}",
        "total_initiatives_found": "Total initiatives found: {total_initiatives}",
        "initiatives_by_category": "Initiatives by category (current_status):",
        "registered_status": "- Registered: {count}",
        "collection_ongoing_status": "- Collection ongoing: {count}",
        "valid_initiative_status": "- Valid initiative: {count}",
        "pages_downloaded": "Pages downloaded: {downloaded_count}/{total_initiatives}",
        "failed_downloads": "Failed downloads: {failed_count}",
        "failed_url": " - {failed_url}",
        "all_downloads_successful": "✅ All downloads successful!",
        "files_saved_in": "Files saved in: initiatives/{start_scraping}",
        "main_page_sources": "Main page sources:",
        "page_source": "  Page {page_num}: {path}",
        "divider_line": "=" * 60,
    },
}
```

`./ECI_initiatives/scraper/initiatives/crawler.py`:
```
# Python Standard Library
import random
import time
from typing import Dict, Tuple

# Third-party
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# Local
from .browser import initialize_browser
from .file_ops import save_listing_page
from .data_parser import parse_initiatives_list_data
from .css_selectors import ECIlistingSelectors
from .consts import (
    ROUTE_FIND_INITIATIVE,
    WAIT_DYNAMIC_CONTENT,
    WAIT_BETWEEN_PAGES,
    WEBDRIVER_TIMEOUT_DEFAULT,
    LOG_MESSAGES,
)
from .scraper_logger import logger


def scrape_all_initiatives_on_all_pages(
    driver: webdriver.Chrome, base_url: str, list_dir: str
) -> Tuple[list, list]:
    """Scrape all pages of initiatives on the listings by iterating through pagination.

    Args:
        driver: Chrome WebDriver instance
        base_url: Base URL of the site
        list_dir: Directory to save page HTML files

    Returns:
        Tuple containing:
        - List of all initiative data from all pages
        - List of paths to saved HTML files
    """
    url_find_initiative = base_url + ROUTE_FIND_INITIATIVE
    all_initiative_pages = []
    saved_page_paths = []
    current_page = 1

    logger.info(f"Starting pagination scraping from: {url_find_initiative}")

    # Load the first page
    logger.info(f"Loading page {current_page}: {url_find_initiative}")
    driver.get(url_find_initiative)

    while True:

        # Scrape current page
        page_initiative_data, page_path = scrape_single_listing_page(
            driver, base_url, list_dir, current_page
        )

        # Add to accumulated data
        all_initiative_pages.extend(page_initiative_data)
        saved_page_paths.append(page_path)

        # Try to navigate to next page
        if navigate_to_next_page(driver, current_page):
            current_page += 1
        else:
            break

    logger.info(
        f"Completed scraping {current_page} pages with total of "
        f"{len(all_initiative_pages)} initiatives"
    )
    return all_initiative_pages, saved_page_paths


def scrape_single_listing_page(
    driver: webdriver.Chrome, base_url: str, list_dir: str, current_page: int
) -> Tuple[list, str]:
    """Scrape a single listing page and return initiative data and saved page path."""

    # Wait for page elements to load
    wait_for_listing_page_content(driver, current_page)

    # Save page source
    page_source, page_path = save_listing_page(driver, list_dir, current_page)

    # Parse initiatives from current page
    page_initiative_data = parse_initiatives_list_data(page_source, base_url)

    return page_initiative_data, page_path


def wait_for_listing_page_content(driver: webdriver.Chrome, current_page: int) -> None:
    """Wait for listing page elements to load."""

    wait = WebDriverWait(driver, WEBDRIVER_TIMEOUT_DEFAULT)
    try:
        cards_initiative_selector = ECIlistingSelectors.INITIATIVE_CARDS
        wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, cards_initiative_selector))
        )
        logger.info(LOG_MESSAGES["page_loaded"].format(page=current_page))
    except Exception as e:
        logger.warning(
            f"No initiatives found or timeout on page {current_page}: "
            f"{e} - continuing with current content"
        )


def navigate_to_next_page(driver: webdriver.Chrome, current_page: int) -> bool:
    """Check for next button and navigate to next page.

    Returns:
        bool: True if successfully navigated to next page, False if no more pages
    """
    next_button_selector = ECIlistingSelectors.NEXT_BUTTON

    try:

        next_button = driver.find_element(By.CSS_SELECTOR, next_button_selector)
        logger.info(
            LOG_MESSAGES["next_button_found"].format(
                page=current_page, next_page=current_page + 1
            )
        )
        # Click the next button
        driver.execute_script("arguments[0].click();", next_button)
        # Wait a bit for the page to start loading
        time.sleep(random.uniform(*WAIT_BETWEEN_PAGES))
        return True

    except Exception:
        logger.info(LOG_MESSAGES["last_page"].format(page=current_page))
        return False


def scrape_initiatives_page(
    driver: webdriver.Chrome, base_url: str, list_dir: str
) -> Tuple[str, str]:
    """Load page, wait for elements, and save HTML source."""

    url_find_initiative = base_url + ROUTE_FIND_INITIATIVE

    logger.info(f"Loading page: {url_find_initiative}")
    driver.get(url_find_initiative)

    wait = WebDriverWait(driver, WEBDRIVER_TIMEOUT_DEFAULT)

    try:
        cards_initiative_selector = ECIlistingSelectors.INITIATIVE_CARDS
        wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, cards_initiative_selector))
        )

        pagination_for_other_cards = ECIlistingSelectors.PAGINATION_LINKS
        wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, pagination_for_other_cards)
            )
        )
        logger.info("Initiatives loaded successfully")
    except Exception as e:
        logger.warning(
            f"No initiatives found or timeout: {e} - continuing with current content"
        )

    # Additional wait to ensure all dynamic content is loaded
    random_time = random.uniform(*WAIT_DYNAMIC_CONTENT)
    logger.debug(f"Waiting {random_time:.1f}s for dynamic content...")
    time.sleep(random_time)

    page_source = driver.page_source
    main_page_path = os.path.join(list_dir, LISTING_PAGE_MAIN_FILENAME)

    with open(main_page_path, "w", encoding="utf-8") as f:
        pretty_html = BeautifulSoup(page_source, "html.parser").prettify()
        f.write(pretty_html)

    logger.info(f"Main page saved to: {main_page_path}")
    return page_source, main_page_path

```

`./ECI_initiatives/scraper/initiatives/css_selectors.py`:
```
class ECIinitiativeSelectors:
    """
    CSS selectors for European Citizens' Initiative (ECI) individual page elements
    """

    # Page structure and timeline
    INITIATIVE_PROGRESS = "ol.ecl-timeline"

    # Content section headings
    OBJECTIVES = "//h2[@class='ecl-u-type-heading-2' and text()='Objectives']"
    ANNEX = "//h2[@class='ecl-u-type-heading-2' and text()='Annex']"
    SOURCES_OF_FUNDING = (
        "//h2[@class='ecl-u-type-heading-2' and text()='Sources of funding']"
    )

    # Organizational information
    ORGANISERS = "//h2[@class='ecl-u-type-heading-2' and text()='Organisers']"
    REPRESENTATIVE = "//h3[@class='ecl-u-type-heading-3' and text()='Representative']"

    # UI elements
    SOCIAL_SHARE = "div.ecl-social-media-share"

    # Error handling
    PAGE_HEADER_TITLE = "h1.ecl-page-header-core__title"


class ECIlistingSelectors:

    # Navigation and pagination
    NEXT_BUTTON = 'li.ecl-pagination__item--next a[aria-label="Go to next page"]'
    PAGINATION_LINKS = (
        "ul.ecl-pagination__list li.ecl-pagination__item a.ecl-pagination__link"
    )

    # Content parsing
    CONTENT_BLOCKS = "div.ecl-content-block.ecl-content-item__content-block"
    INITIATIVE_CARDS = "div.ecl-content-block__title a.ecl-link"  # Same as TITLE_LINKS
    META_LABELS = "span.ecl-content-block__secondary-meta-label"

```

`./ECI_initiatives/scraper/initiatives/data_parser.py`:
```
# Python Standard Library
from collections import Counter
from typing import Dict, List

# Third-party
from bs4 import BeautifulSoup

# Local
from .css_selectors import ECIlistingSelectors
from .scraper_logger import logger

# Consts
from .consts import (
    BASE_URL,
    ROUTE_FIND_INITIATIVE,
    DATA_DIR_NAME,
    LOG_DIR_NAME,
    LISTINGS_DIR_NAME,
    PAGES_DIR_NAME,
    WAIT_DYNAMIC_CONTENT,
    WAIT_BETWEEN_PAGES,
    WAIT_BETWEEN_DOWNLOADS,
    RETRY_WAIT_BASE,
    WEBDRIVER_TIMEOUT_DEFAULT,
    WEBDRIVER_TIMEOUT_CONTENT,
    CHROME_OPTIONS,
    LISTING_PAGE_FILENAME_PATTERN,
    LISTING_PAGE_MAIN_FILENAME,
    CSV_FIELDNAMES,
    CSV_FILENAME,
    DEFAULT_MAX_RETRIES,
    MIN_HTML_LENGTH,
    RATE_LIMIT_INDICATORS,
    LOG_MESSAGES,
)


def parse_initiatives_list_data(
    page_source: str, base_url: str
) -> list[Dict[str, str]]:
    """Parse HTML page source and extract initiatives data."""

    logger.info("Parsing saved listing page for initiatives links...")

    soup = BeautifulSoup(page_source, "html.parser")
    initiative_data = []

    for content_block in soup.select(ECIlistingSelectors.CONTENT_BLOCKS):

        title_link = content_block.select_one(ECIlistingSelectors.INITIATIVE_CARDS)
        if not title_link or not title_link.get("href"):
            continue

        href = title_link.get("href")
        if not href.startswith("/initiatives/details/"):
            continue

        full_url = base_url + href

        current_status = ""
        registration_number = ""
        signature_collection = ""

        meta_labels = content_block.select(ECIlistingSelectors.META_LABELS)

        for label in meta_labels:

            text = label.get_text(strip=True)

            if text.startswith("Current status:"):
                current_status = text.replace("Current status:", "").strip()

            elif text.startswith("Registration number:"):
                registration_number = text.replace("Registration number:", "").strip()

            elif "signature collection" in text.lower():
                signature_collection = text.strip()

        initiative_data.append(
            {
                "url": full_url,
                "current_status": current_status,
                "registration_number": registration_number,
                "signature_collection": signature_collection,
                "datetime": "",
            }
        )

    logger.info(f"Found {len(initiative_data)} initiative entries")
    return initiative_data

```

`./ECI_initiatives/scraper/initiatives/downloader.py`:
```
# Python Standard Library
import datetime
import os
import random
import time
from typing import Tuple

# Third-party
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# Local
from .browser import initialize_browser
from .css_selectors import ECIinitiativeSelectors
from .consts import (
    WAIT_DYNAMIC_CONTENT,
    WAIT_BETWEEN_DOWNLOADS,
    RETRY_WAIT_BASE,
    WEBDRIVER_TIMEOUT_CONTENT,
    DEFAULT_MAX_RETRIES,
    MIN_HTML_LENGTH,
    RATE_LIMIT_INDICATORS,
    LOG_MESSAGES,
)
from .file_ops import save_initiative_page
from .scraper_logger import logger


def download_initiative_pages(
    pages_dir: str, initiative_data: list
) -> Tuple[list, list]:
    """Download individual initiative pages using Selenium.

    Args:
        pages_dir: Directory path for saving HTML pages
        initiative_data: List of initiative dictionaries

    Returns:
        Tuple containing updated data list and list of failed URLs
    """
    updated_data = []
    failed_urls = []

    driver = initialize_browser()

    try:

        for i, row in enumerate(initiative_data):

            url = row["url"]
            logger.info(f"Processing {i+1}/{len(initiative_data)}: {url}")

            success = download_single_initiative(driver, pages_dir, url)

            if success:

                row["datetime"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                time.sleep(random.uniform(*WAIT_BETWEEN_DOWNLOADS))

            else:
                failed_urls.append(url)

            updated_data.append(row)

    finally:
        driver.quit()
        logger.info(LOG_MESSAGES["pages_browser_closed"])

    logger.info(f"Download completed. Failed URLs: {len(failed_urls)}")
    return updated_data, failed_urls


def download_single_initiative(
    driver: webdriver.Chrome,
    pages_dir: str,
    url: str,
    max_retries: int = DEFAULT_MAX_RETRIES,
) -> bool:
    """Download a single initiative page with retry logic.

    Returns:
        bool: True if successful, False if failed
    """

    retry_wait_base = 1 * random.uniform(*RETRY_WAIT_BASE)
    retry_count = 0

    while retry_count <= max_retries:
        try:
            logger.info("Downloading the html file...")
            driver.get(url)

            # Check for rate limiting
            check_rate_limiting(driver)

            # Wait for page content to load
            wait_for_page_content(driver)

            # Additional wait for dynamic content
            time.sleep(random.uniform(*WAIT_DYNAMIC_CONTENT))

            # Get page source and save
            page_source = driver.page_source
            file_name = save_initiative_page(pages_dir, url, page_source)

            logger.info(LOG_MESSAGES["download_success"].format(filename=file_name))
            return True

        except Exception as e:

            error_msg = str(e)
            is_rate_limited = any(
                indicator in error_msg for indicator in RATE_LIMIT_INDICATORS
            )

            logger.debug(
                f"🔍 Exception details for {url}: {type(e).__name__}: {error_msg}"
            )

            if is_rate_limited:

                retry_count += 1

                if retry_count <= max_retries:

                    wait_time = retry_wait_base * (retry_count**2)
                    logger.warning(
                        LOG_MESSAGES["rate_limit_retry"].format(
                            retry=retry_count,
                            max_retries=max_retries,
                            wait_time=wait_time,
                        )
                    )
                    time.sleep(wait_time)

                else:

                    error_type = type(e).__name__

                    # Categorize different types of errors for better logging
                    if (
                        "chrome not reachable" in error_msg.lower()
                        or "session not created" in error_msg.lower()
                    ):
                        logger.error(
                            f"❌ Browser crash/connection error downloading:\n{url}:\n{error_type}:\n{error_msg}"
                        )

                    elif "timeout" in error_msg.lower():
                        logger.error(
                            f"❌ Timeout error downloading:\n{url}:\n{error_type}:\n{error_msg}"
                        )

                    elif (
                        "permission" in error_msg.lower()
                        or "access" in error_msg.lower()
                    ):
                        logger.error(
                            f"❌ Permission/access error downloading:\n{url}:\n{error_type}:\n{error_msg}"
                        )

                    elif (
                        "network" in error_msg.lower()
                        or "connection" in error_msg.lower()
                    ):
                        logger.error(
                            f"❌ Network error downloading:\n{url}:\n{error_type}:\n{error_msg}"
                        )

                    elif "disk" in error_msg.lower() or "space" in error_msg.lower():
                        logger.error(
                            f"❌ Disk space error downloading:\n{url}:\n{error_type}:\n{error_msg}"
                        )

                    else:
                        logger.error(
                            f"❌ Error downloading:\n{url}:\n{error_type}:\n{error_msg}"
                        )

                    return False

            else:
                logger.error(f"❌ Error downloading:\n{url}:\n{e}")
                return False

    logger.error(f"❌ Exhausted all {max_retries} retries for: {url}")
    return False


def check_rate_limiting(driver: webdriver.Chrome) -> None:
    """Check if the current page shows rate limiting errors."""

    try:
        rate_limit_title = driver.find_element(
            By.CSS_SELECTOR, ECIinitiativeSelectors.PAGE_HEADER_TITLE
        )

        if rate_limit_title and any(
            indicator in rate_limit_title.text for indicator in RATE_LIMIT_INDICATORS
        ):
            raise Exception("429 - Rate limited (HTML response)")

    except Exception as rate_check_error:

        if any(
            indicator in str(rate_check_error) for indicator in RATE_LIMIT_INDICATORS
        ):
            raise rate_check_error

        # If it's not a rate limit check error, continue normally
        pass


def wait_for_page_content(driver: webdriver.Chrome) -> None:
    """Wait for initiative page content to load."""

    wait = WebDriverWait(driver, WEBDRIVER_TIMEOUT_CONTENT)

    # Wait for initiative progress timeline
    try:
        wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, ECIinitiativeSelectors.INITIATIVE_PROGRESS)
            )
        )
        logger.debug("Initiative progress timeline loaded")
    except:
        logger.warning(
            "Initiative progress timeline not found, "
            "Should be in all initiatives."
            "\ncontinuing..."
        )

    # Wait for at least one of the main content sections
    content_selectors_to_wait = [
        ECIinitiativeSelectors.OBJECTIVES,
        ECIinitiativeSelectors.ANNEX,
        ECIinitiativeSelectors.ORGANISERS,
        ECIinitiativeSelectors.REPRESENTATIVE,
        ECIinitiativeSelectors.SOURCES_OF_FUNDING,
        ECIinitiativeSelectors.SOCIAL_SHARE,
    ]

    element_found = False

    for selector in content_selectors_to_wait:

        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
            logger.debug(f"Content loaded: {selector}")
            element_found = True

            break

        except:
            continue

    if not element_found:
        logger.warning("No main content other elements found, but proceeding...")

```

`./ECI_initiatives/scraper/initiatives/file_ops.py`:
```
# Python Standard Library
import csv
import os
import random
import time
from typing import Dict, List, Tuple

# Third-party
from bs4 import BeautifulSoup
from selenium import webdriver

# Local
from .consts import (
    WAIT_DYNAMIC_CONTENT,
    CSV_FIELDNAMES,
    MIN_HTML_LENGTH,
    RATE_LIMIT_INDICATORS,
    LISTING_PAGE_FILENAME_PATTERN,
    LOG_MESSAGES,
)
from .scraper_logger import logger


def setup_scraping_dirs(list_dir: str, pages_dir: str) -> None:
    """Create necessary directories for scraping output."""

    os.makedirs(list_dir, exist_ok=True)
    os.makedirs(pages_dir, exist_ok=True)
    logger.debug(f"Created directories: {list_dir}, {pages_dir}")


def save_listing_page(
    driver: webdriver.Chrome, list_dir: str, current_page: int
) -> Tuple[str, str]:
    """Save listing page source and return page source and file path."""

    # Additional wait for dynamic content
    random_time = random.uniform(*WAIT_DYNAMIC_CONTENT)
    logger.debug(f"Waiting {random_time:.1f}s for dynamic content...")
    time.sleep(random_time)

    # Get page source and save it
    page_source = driver.page_source
    page_filename = LISTING_PAGE_FILENAME_PATTERN.format(current_page)
    page_path = os.path.join(list_dir, page_filename)

    with open(page_path, "w", encoding="utf-8") as f:
        pretty_html = BeautifulSoup(page_source, "html.parser").prettify()
        f.write(pretty_html)

    logger.info(LOG_MESSAGES["page_saved"].format(page=current_page, path=page_path))
    return page_source, page_path


def save_initiative_page(pages_dir: str, url: str, page_source: str) -> str:
    """Save initiative page source to file and return filename."""

    # Double-check page source for rate limiting content
    if any(indicator in page_source for indicator in RATE_LIMIT_INDICATORS[:2]):
        raise Exception("429 - Rate limited (found in page source)")

    # Extract year and number from URL for filename
    parts = url.rstrip("/").split("/")
    year = parts[-2]
    number = parts[-1]

    # Generate directory under pages_dir for year
    year_dir = os.path.join(pages_dir, year)
    os.makedirs(year_dir, exist_ok=True)

    # Create filename with year and number to avoid overwriting
    file_name = f"{year}_{number}.html"
    file_path = os.path.join(year_dir, file_name)

    try:
        # Check for obvious signs of malformed HTML
        original_length = len(page_source)

        # Common malformed HTML indicators
        malformed_indicators = [
            page_source.count("<") != page_source.count(">"),  # Unmatched brackets
            page_source.count('"') % 2 != 0,  # Unmatched quotes
            "</html>" not in page_source.lower()
            and "<html" in page_source.lower(),  # Missing closing html tag
            original_length < MIN_HTML_LENGTH,  # Suspiciously short HTML
        ]

        if any(malformed_indicators):
            logger.warning(
                f"⚠️  Potential malformed HTML detected in {file_name}: "
                f"length={original_length}, unmatched_brackets={malformed_indicators[0]}, "
                f"unmatched_quotes={malformed_indicators[1]}"
            )

        # Parse with BeautifulSoup and detect if it had to fix issues
        soup = BeautifulSoup(page_source, "html.parser")
        pretty_html = soup.prettify()

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(pretty_html)

    except Exception as e:
        # BeautifulSoup rarely throws exceptions, but if it does, the HTML is severely malformed
        logger.warning(
            f"⚠️  Failed to parse HTML for {file_name}: {str(e)}. "
            f"Saving raw HTML without prettification."
        )

        # Save raw HTML as fallback
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(page_source)

    return file_name


def write_initiatives_csv(
    file_path: str, initiative_data: list[Dict[str, str]]
) -> None:
    """Write initiative data to CSV file.

    Args:
        file_path: Full path to the CSV file
        initiative_data: List of initiative dictionaries to write
    """
    with open(file_path, "w", encoding="utf-8", newline="") as f:

        writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
        writer.writeheader()
        writer.writerows(initiative_data)

```

`./ECI_initiatives/scraper/initiatives/__main__.py`:
```
# Python Standard Library
import datetime
from typing import Dict, Tuple
import os

# Local
from .crawler import scrape_all_initiatives_on_all_pages
from .downloader import download_initiative_pages
from .file_ops import setup_scraping_dirs, write_initiatives_csv
from .statistics import display_completion_summary, gather_scraping_statistics
from .browser import initialize_browser
from .consts import (
    START_SCRAPING,
    SCRIPT_DIR,
    BASE_URL,
    DATA_DIR_NAME,
    LISTINGS_DIR_NAME,
    PAGES_DIR_NAME,
    CSV_FILENAME,
    LOG_MESSAGES,
)
from .scraper_logger import logger


def scrape_eci_initiatives() -> str:
    """Main function to scrape European Citizens' Initiative data.

    Returns:
        str: Timestamp string of when scraping started
    """


    logger.info(LOG_MESSAGES["scraping_start"].format(timestamp=START_SCRAPING))

    base_url = BASE_URL

    # Create directories relative to script location
    list_dir = os.path.join(
        SCRIPT_DIR, DATA_DIR_NAME, START_SCRAPING, LISTINGS_DIR_NAME
    )
    pages_dir = os.path.join(SCRIPT_DIR, DATA_DIR_NAME, START_SCRAPING, PAGES_DIR_NAME)
    setup_scraping_dirs(list_dir, pages_dir)

    driver = initialize_browser()

    try:
        # Scrape all pages and get accumulated initiative data
        all_initiative_pages_catalog, saved_page_listing_paths = (
            scrape_all_initiatives_on_all_pages(driver, base_url, list_dir)
        )
    finally:
        driver.quit()
        logger.info(LOG_MESSAGES["browser_closed"])

    if all_initiative_pages_catalog:
        failed_urls = save_and_download_initiatives(
            list_dir, pages_dir, all_initiative_pages_catalog
        )
    else:
        logger.warning("No initiatives found to classify or download")
        failed_urls = []

    display_completion_summary(
        START_SCRAPING,
        all_initiative_pages_catalog,
        saved_page_listing_paths,
        failed_urls,
    )

    return START_SCRAPING


def save_and_download_initiatives(
    list_dir: str, pages_dir: str, initiative_data: list[Dict[str, str]]
) -> Tuple[int, list]:
    """Save initiative data to CSV and download individual pages.

    Args:
        list_dir: Directory path for saving CSV files
        pages_dir: Directory path for saving HTML pages
        initiative_data: List of initiative dictionaries

    Returns:
        Tuple containing number of successful downloads and list of failed URLs
    """

    url_list_file = os.path.join(list_dir, CSV_FILENAME)

    # Save initial data to CSV
    write_initiatives_csv(url_list_file, initiative_data)
    logger.info(f"Initiative data saved to: {url_list_file}")

    logger.info("Starting individual initiative pages download...")
    updated_data, failed_urls = download_initiative_pages(pages_dir, initiative_data)

    # Update CSV with download timestamps
    write_initiatives_csv(url_list_file, updated_data)
    logger.info(f"Updated CSV with download timestamps: {url_list_file}")

    return failed_urls


if __name__ == "__main__":
    scrape_eci_initiatives()
```

`./ECI_initiatives/scraper/initiatives/scraper_logger.py`:
```
# python
import logging
import os
import datetime

# scraper
from .consts import LOG_DIR

class ScraperLogger:
    """
    Logger class for ECI scraper with file and console output.
    (Singleton) - ensures only one logger instance exists across the application.
    """
    _instance = None
    _initialized = False

    def __new__(cls, log_dir: str = None):
        if cls._instance is None:
            cls._instance = super(ScraperLogger, cls).__new__(cls)
        return cls._instance

    def __init__(self, log_dir: str = None):
        # Prevent re-initialization of singleton
        if ScraperLogger._initialized:
            return
            
        self.logger = logging.getLogger("ECIScraper")
        self.logger.setLevel(logging.DEBUG)
        self.log_dir = log_dir or LOG_DIR

        # Clear existing handlers to avoid duplicates
        if self.logger.hasHandlers():
            self.logger.handlers.clear()

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        os.makedirs(self.log_dir, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_file = os.path.join(self.log_dir, f"scraper_initiatives{timestamp}.log")

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)

        # File formatter (more detailed)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)

        # Console formatter (simpler)
        console_formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # Mark as initialized
        ScraperLogger._initialized = True

    def debug(self, message: str):
        self.logger.debug(message)

    def info(self, message: str):
        self.logger.info(message)

    def warning(self, message: str):
        self.logger.warning(message)

    def error(self, message: str):
        self.logger.error(message)

    def critical(self, message: str):
        self.logger.critical(message)

logger = ScraperLogger(LOG_DIR)
```

`./ECI_initiatives/scraper/initiatives/statistics.py`:
```
# Python Standard Library
import csv
import datetime
import os
from collections import Counter
from typing import Dict, List

# Local modules
from .consts import CSV_FILENAME, LOG_MESSAGES
from .scraper_logger import logger


def display_completion_summary(
    start_scraping: str,
    initiative_data: list[Dict[str, str]],
    saved_page_paths: list,
    failed_urls: list,
) -> None:
    """Display final completion summary with statistics."""
    stats = gather_scraping_statistics(start_scraping, initiative_data, failed_urls)
    display_summary_info(start_scraping, saved_page_paths, stats)
    display_results_and_files(start_scraping, saved_page_paths, failed_urls, stats)


LOG_SUMMARY = LOG_MESSAGES["summary_scraping"]


def gather_scraping_statistics(
    start_scraping: str, initiative_data: list, failed_urls: list
) -> dict:
    """Gather all statistics needed for the completion summary."""

    # Count initiatives by status from CSV
    current_status_counter = Counter()
    url_list_file = f"initiatives/{start_scraping}/list/{CSV_FILENAME}"

    if os.path.exists(url_list_file):

        with open(url_list_file, "r", encoding="utf-8") as file:

            reader = csv.DictReader(file)

            for row in reader:
                if row["current_status"]:
                    current_status_counter[row["current_status"]] += 1

    # Count downloaded files
    pages_dir = f"initiatives/{start_scraping}/initiative_pages"

    downloaded_files_count = 0

    if os.path.exists(pages_dir):

        # Iterate through year directories and count HTML files
        for year_dir in os.listdir(pages_dir):

            year_path = os.path.join(pages_dir, year_dir)

            if os.path.isdir(year_path):

                html_files = [f for f in os.listdir(year_path) if f.endswith(".html")]
                downloaded_files_count += len(html_files)

    return {
        "status_counter": current_status_counter,
        "downloaded_count": downloaded_files_count,
        "total_initiatives": len(initiative_data) if initiative_data else 0,
        "failed_count": len(failed_urls),
    }


def display_summary_info(
    start_scraping: str, saved_page_paths: list, stats: dict
) -> None:
    """Display the main summary information and statistics."""
    logger.info(LOG_SUMMARY["divider_line"])
    logger.info(LOG_SUMMARY["scraping_complete"])
    logger.info(LOG_SUMMARY["divider_line"])

    logger.info(
        LOG_SUMMARY["completion_timestamp"].format(
            timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
    )
    logger.info(LOG_SUMMARY["start_time"].format(start_scraping=start_scraping))
    logger.info(
        LOG_SUMMARY["total_pages_scraped"].format(page_count=len(saved_page_paths))
    )
    logger.info(
        LOG_SUMMARY["total_initiatives_found"].format(
            total_initiatives=stats["total_initiatives"]
        )
    )

    logger.info(LOG_SUMMARY["initiatives_by_category"])
    for status, count in stats["status_counter"].items():
        logger.info(f"- {status}: {count}")


def display_results_and_files(
    start_scraping: str, saved_page_paths: list, failed_urls: list, stats: dict
) -> None:
    """Display download results and file location information."""
    logger.info(
        LOG_SUMMARY["pages_downloaded"].format(
            downloaded_count=stats["downloaded_count"],
            total_initiatives=stats["total_initiatives"],
        )
    )

    if stats["failed_count"]:
        logger.error(
            LOG_SUMMARY["failed_downloads"].format(failed_count=stats["failed_count"])
        )
        for failed_url in failed_urls:
            logger.error(LOG_SUMMARY["failed_url"].format(failed_url=failed_url))
    else:
        logger.info(LOG_SUMMARY["all_downloads_successful"])

    logger.info(LOG_SUMMARY["files_saved_in"].format(start_scraping=start_scraping))
    logger.info(LOG_SUMMARY["main_page_sources"])
    for i, path in enumerate(saved_page_paths, 1):
        logger.info(LOG_SUMMARY["page_source"].format(page_num=i, path=path))

    logger.info(LOG_SUMMARY["divider_line"])

```

