# Python Standard Library
import csv
import datetime
import os
import random
import time
from collections import Counter
from typing import Dict, Tuple

# BeautifulSoup
from bs4 import BeautifulSoup

# Selenium
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# Scraper
from scraper_logger import ScraperLogger
from css_selectors import ECIinitiativeSelectors, ECIlistingSelectors

logger = None

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


def scrape_eci_initiatives() -> str:
    """Main function to scrape European Citizens' Initiative data.

    Returns:
        str: Timestamp string of when scraping started
    """

    global logger

    start_scraping = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Initialize logger with log directory relative to script location
    log_dir = os.path.join(script_dir, DATA_DIR_NAME, start_scraping, LOG_DIR_NAME)
    logger = ScraperLogger(log_dir)
    logger.info(LOG_MESSAGES["scraping_start"].format(timestamp=start_scraping))

    base_url = BASE_URL

    # Create directories relative to script location
    list_dir = os.path.join(
        script_dir, DATA_DIR_NAME, start_scraping, LISTINGS_DIR_NAME
    )
    pages_dir = os.path.join(script_dir, DATA_DIR_NAME, start_scraping, PAGES_DIR_NAME)
    setup_scraping_dirs(list_dir, pages_dir)

    driver = initialize_browser()

    try:
        # Scrape all pages and get accumulated initiative data
        all_initiative_data, saved_page_paths = scrape_all_initiatives_on_all_pages(
            driver, base_url, list_dir
        )
    finally:
        driver.quit()
        logger.info(LOG_MESSAGES["browser_closed"])

    if all_initiative_data:
        failed_urls = save_and_download_initiatives(
            list_dir, pages_dir, all_initiative_data
        )
    else:
        logger.warning("No initiatives found to classify or download")
        failed_urls = []

    display_completion_summary(
        start_scraping, all_initiative_data, saved_page_paths, failed_urls
    )

    return start_scraping


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


def scrape_all_initiatives_on_all_pages(
    driver: webdriver.Chrome, base_url: str, list_dir: str
) -> Tuple[list, list]:
    """Scrape all pages of initiatives by iterating through pagination.

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
    all_initiative_data = []
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
        all_initiative_data.extend(page_initiative_data)
        saved_page_paths.append(page_path)

        # Try to navigate to next page
        if navigate_to_next_page(driver, current_page):
            current_page += 1
        else:
            break

    logger.info(
        f"Completed scraping {current_page} pages with total of "
        f"{len(all_initiative_data)} initiatives"
    )
    return all_initiative_data, saved_page_paths


def initialize_browser() -> webdriver.Chrome:
    """Initialize Chrome WebDriver with headless options."""

    chrome_options = Options()
    for option in CHROME_OPTIONS:
        chrome_options.add_argument(option)

    logger.info(LOG_MESSAGES["browser_init"])
    driver = webdriver.Chrome(options=chrome_options)
    logger.debug(LOG_MESSAGES["browser_success"])

    return driver


def setup_scraping_dirs(list_dir: str, pages_dir: str) -> None:
    """Create necessary directories for scraping output."""

    os.makedirs(list_dir, exist_ok=True)
    os.makedirs(pages_dir, exist_ok=True)
    logger.debug(f"Created directories: {list_dir}, {pages_dir}")


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
        logger.info("Individual pages browser closed")

    logger.info(f"Download completed. Failed URLs: {len(failed_urls)}")
    return updated_data, failed_urls


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
    div_line = "=" * 60
    logger.info(div_line)
    logger.info(LOG_MESSAGES["scraping_complete"])
    logger.info(div_line)

    logger.info(
        f"Scraping completed at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    logger.info(f"Start time: {start_scraping}")
    logger.info(f"Total pages scraped: {len(saved_page_paths)}")
    logger.info(f"Total initiatives found: {stats['total_initiatives']}")

    logger.info("Initiatives by category (current_status):")
    for status, count in stats["status_counter"].items():
        logger.info(f"- {status}: {count}")


def display_results_and_files(
    start_scraping: str, saved_page_paths: list, failed_urls: list, stats: dict
) -> None:
    """Display download results and file location information."""
    logger.info(
        f"Pages downloaded: {stats['downloaded_count']}/{stats['total_initiatives']}"
    )

    if stats["failed_count"]:
        logger.error(f"Failed downloads: {stats['failed_count']}")
        for failed_url in failed_urls:
            logger.error(f" - {failed_url}")
    else:
        logger.info("✅ All downloads successful!")

    logger.info(f"Files saved in: initiatives/{start_scraping}")
    logger.info("Main page sources:")
    for i, path in enumerate(saved_page_paths, 1):
        logger.info(f"  Page {i}: {path}")

    logger.info("=" * 60)


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


if __name__ == "__main__":
    scrape_eci_initiatives()
