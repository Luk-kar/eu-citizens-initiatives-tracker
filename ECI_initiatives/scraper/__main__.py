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
    BASE_URL,
    DATA_DIR_NAME,
    LOG_DIR_NAME,
    LISTINGS_DIR_NAME,
    PAGES_DIR_NAME,
    CSV_FILENAME,
    LOG_MESSAGES,
)
from .logger import logger


def scrape_eci_initiatives() -> str:
    """Main function to scrape European Citizens' Initiative data.

    Returns:
        str: Timestamp string of when scraping started
    """

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
        start_scraping,
        all_initiative_pages_catalog,
        saved_page_listing_paths,
        failed_urls,
    )

    return start_scraping


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
