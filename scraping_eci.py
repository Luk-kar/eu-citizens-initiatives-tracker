# Python
import os
import datetime
import requests
from bs4 import BeautifulSoup
import time
import random
import csv
from typing import Dict, Tuple

# Selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

# Scraper
from scraper_logger import ScraperLogger
from css_selectors import ECIPageSelectors

logger = None


def scrape_eci_initiatives() -> str:
    """Main function to scrape European Citizens' Initiative data.

    Returns:
        str: Timestamp string of when scraping started
    """

    global logger

    start_scraping = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # Initialize logger with log directory
    log_dir = f"initiatives/{start_scraping}/logs"
    logger = ScraperLogger(log_dir)

    logger.info(f"Starting scraping at: {start_scraping}")

    base_url = "https://citizens-initiative.europa.eu"

    list_dir = f"initiatives/{start_scraping}/list"
    pages_dir = f"initiatives/{start_scraping}/pages"
    setup_scraping_dirs(list_dir, pages_dir)

    driver = initialize_browser()

    try:
        page_source, main_page_path = scrape_initiatives_page(
            driver, base_url, list_dir
        )
    finally:
        driver.quit()
        logger.info("Browser closed")

    initiative_data = parse_initiatives_list_data(page_source, base_url)

    if initiative_data:
        failed_urls = save_and_download_initiatives(
            list_dir, pages_dir, initiative_data
        )
    else:
        logger.warning("No initiatives found to classify or download")
        failed_urls = []

    display_completion_summary(
        start_scraping, initiative_data, main_page_path, failed_urls
    )

    return start_scraping


def initialize_browser() -> webdriver.Chrome:
    """Initialize Chrome WebDriver with headless options."""

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    logger.info("Initializing browser...")
    driver = webdriver.Chrome(options=chrome_options)
    logger.debug("Browser initialized successfully")

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

    url_list_file = os.path.join(list_dir, "initiatives_list.csv")

    with open(url_list_file, "w", encoding="utf-8", newline="") as f:
        header = [
            "url",
            "current_status",
            "registration_number",
            "signature_collection",
            "datetime",
        ]
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerows(initiative_data)

    logger.info(f"Initiative data saved to: {url_list_file}")

    logger.info("Starting individual initiative pages download...")
    updated_data, failed_urls = download_initiative_pages(pages_dir, initiative_data)

    # Update CSV with download timestamps
    with open(url_list_file, "w", encoding="utf-8", newline="") as f:
        header = [
            "url",
            "current_status",
            "registration_number",
            "signature_collection",
            "datetime",
        ]
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerows(updated_data)

    logger.info(f"Updated CSV with download timestamps: {url_list_file}")
    return failed_urls


def download_initiative_pages(pages_dir: str, initiative_data: list):
    """Download individual initiative pages using Selenium with proper waiting and update datetime stamps with retry logic.
    Args:
        pages_dir: Directory path for saving HTML pages
        initiative_data: List of initiative dictionaries
    Returns:
        Tuple containing updated data list and list of failed URLs
    """
    updated_data = []
    failed_urls = []

    # Initialize browser for downloading individual pages
    driver = initialize_browser()

    try:
        for i, row in enumerate(initiative_data):
            url = row["url"]
            max_retries = 5
            retry_wait_base = 1 * random.uniform(1.0, 1.2)
            retry_count = 0
            success = False

            while retry_count <= max_retries and not success:
                try:
                    logger.info(f"Downloading {i+1}/{len(initiative_data)}: {url}")

                    # Load page with Selenium
                    driver.get(url)

                    # Wait for key elements to load
                    wait = WebDriverWait(driver, 20)

                    # Wait for the main content to load - checking for initiative progress timeline
                    try:
                        wait.until(
                            EC.presence_of_element_located(
                                (By.CSS_SELECTOR, ECIPageSelectors.INITIATIVE_PROGRESS)
                            )
                        )
                        logger.debug("Initiative progress timeline loaded")
                    except:
                        logger.warning(
                            "Initiative progress timeline not found, continuing..."
                        )

                    # Wait for at least one of the main content sections
                    content_selectors_to_wait = [
                        ECIPageSelectors.INITIATIVE_PROGRESS,
                        ECIPageSelectors.OBJECTIVES,
                        ECIPageSelectors.ANNEX,
                        ECIPageSelectors.ORGANISERS,
                        ECIPageSelectors.REPRESENTATIVE,
                        ECIPageSelectors.SOURCES_OF_FUNDING,
                        ECIPageSelectors.SOCIAL_SHARE,
                    ]

                    element_found = False
                    for selector in content_selectors_to_wait:
                        try:
                            wait.until(
                                EC.presence_of_element_located(
                                    (By.CSS_SELECTOR, selector)
                                )
                            )
                            logger.debug(f"Content loaded: {selector}")
                            element_found = True
                            break
                        except:
                            continue

                    if not element_found:
                        logger.warning(
                            "No main content elements found, but proceeding..."
                        )

                    # Additional wait for dynamic content
                    time.sleep(random.uniform(1.0, 2.0))

                    # Get page source after elements have loaded
                    page_source = driver.page_source

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

                    # Save the page source
                    with open(file_path, "w", encoding="utf-8") as f:
                        # Prettify the HTML for better readability
                        pretty_html = BeautifulSoup(
                            page_source, "html.parser"
                        ).prettify()
                        f.write(pretty_html)

                    successful_download_time = datetime.datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    row["datetime"] = successful_download_time
                    success = True
                    logger.info(f"✅ Successfully downloaded: {file_name}")

                except Exception as e:
                    error_msg = str(e)
                    if "429" in error_msg or "Too Many Requests" in error_msg:
                        retry_count += 1
                        if retry_count <= max_retries:
                            wait_time = retry_wait_base * retry_count
                            logger.warning(
                                f"⚠️  Received rate limiting. Retrying {retry_count}/{max_retries} in {wait_time:.1f} seconds..."
                            )
                            time.sleep(wait_time)
                        else:
                            logger.error(
                                f"❌ Failed to download after {max_retries} retries (rate limited): {url}"
                            )
                            failed_urls.append(url)
                    else:
                        logger.error(f"❌ Error downloading {url}: {e}")
                        failed_urls.append(url)
                        break

            if not success and retry_count > max_retries:
                logger.error(f"❌ Exhausted all {max_retries} retries for: {url}")
                if url not in failed_urls:
                    failed_urls.append(url)

            updated_data.append(row)

            if success:
                # Wait between successful downloads to be respectful
                time.sleep(random.uniform(0.5, 1.5))

    finally:
        driver.quit()
        logger.info("Individual pages browser closed")

    logger.info(f"Download completed. Failed URLs: {len(failed_urls)}")
    return updated_data, failed_urls


def scrape_initiatives_page(
    driver: webdriver.Chrome, base_url: str, list_dir: str
) -> Tuple[str, str]:
    """Load page, wait for elements, and save HTML source."""

    route_find_initiative = "/find-initiative_en"
    url_find_initiative = base_url + route_find_initiative

    logger.info(f"Loading page: {url_find_initiative}")
    driver.get(url_find_initiative)

    wait = WebDriverWait(driver, 30)

    try:
        cards_initiative_selector = "div.ecl-content-block__title a.ecl-link"
        wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, cards_initiative_selector))
        )

        pagination_for_other_cards = (
            "ul.ecl-pagination__list li.ecl-pagination__item a.ecl-pagination__link"
        )
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
    random_time = random.uniform(1.5, 1.9)
    logger.debug(f"Waiting {random_time:.1f}s for dynamic content...")
    time.sleep(random_time)

    page_source = driver.page_source
    initiative_list_page_name = "Find_initiative_European_Citizens_Initiative"
    main_page_path = os.path.join(list_dir, f"{initiative_list_page_name}.html")

    with open(main_page_path, "w", encoding="utf-8") as f:
        pretty_html = BeautifulSoup(page_source, "html.parser").prettify()
        f.write(pretty_html)

    logger.info(f"Main page saved to: {main_page_path}")
    return page_source, main_page_path


def parse_initiatives_list_data(
    page_source: str, base_url: str
) -> list[Dict[str, str]]:
    """Parse HTML page source and extract initiatives data."""
    logger.info("Parsing saved main page for initiatives links...")

    soup = BeautifulSoup(page_source, "html.parser")
    initiative_data = []

    for content_block in soup.select(
        "div.ecl-content-block.ecl-content-item__content-block"
    ):
        title_link = content_block.select_one("div.ecl-content-block__title a.ecl-link")
        if not title_link or not title_link.get("href"):
            continue

        href = title_link.get("href")
        if not href.startswith("/initiatives/details/"):
            continue

        full_url = base_url + href

        current_status = ""
        registration_number = ""
        signature_collection = ""

        meta_labels = content_block.select(
            "span.ecl-content-block__secondary-meta-label"
        )

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


def display_completion_summary(
    start_scraping: str,
    initiative_data: list[Dict[str, str]],
    main_page_path: str,
    failed_urls: list,
) -> None:
    """Display final completion summary with statistics.

    Args:
        start_scraping: Start time timestamp string
        initiative_data: List of initiative data dictionaries
        main_page_path: Path to the saved main page file
        failed_urls: List of URLs that failed to download
    """
    from collections import Counter

    # Display total of initiatives by categories as `current_status` from the csv file
    current_status_counter = Counter()
    url_list_file = f"initiatives/{start_scraping}/list/initiatives_list.csv"

    if os.path.exists(url_list_file):
        with open(url_list_file, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row["current_status"]:
                    current_status_counter[row["current_status"]] += 1

    pages_dir = f"initiatives/{start_scraping}/pages"
    downloaded_files_count = 0

    if os.path.exists(pages_dir):
        downloaded_files_count = len(
            [
                f
                for subdir, _, files in os.walk(pages_dir)
                for f in files
                if f.endswith(".html")
            ]
        )

    total_initiatives_count = len(initiative_data) if initiative_data else 0
    failed_downloads_count = len(failed_urls)
    div_line = "=" * 60

    logger.info("\n" + div_line)
    logger.info("🎉 SCRAPING FINISHED! 🎉")
    logger.info(div_line)
    logger.info(
        f"Scraping completed at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    logger.info(f"Start time: {start_scraping}")
    logger.info(f"Total initiatives found: {total_initiatives_count}")

    logger.info("Initiatives by category (current_status):")
    for status, count in current_status_counter.items():
        logger.info(f"- {status}: {count}")

    logger.info(f"Pages downloaded: {downloaded_files_count}/{total_initiatives_count}")

    if failed_downloads_count:
        logger.error(f"Failed downloads: {failed_downloads_count}")
        for failed_url in failed_urls:
            logger.error(f" - {failed_url}")
    else:
        logger.info("✅ All downloads successful!")

    logger.info(f"Files saved in: initiatives/{start_scraping}")
    logger.info(f"Main page source: {main_page_path}")
    logger.info(div_line)


if __name__ == "__main__":
    scrape_eci_initiatives()
