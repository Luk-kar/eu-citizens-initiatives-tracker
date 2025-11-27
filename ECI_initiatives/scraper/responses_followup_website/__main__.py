"""
Main entry point for followup website scraper.
"""

import datetime
import os
from typing import List, Tuple
from pathlib import Path
import logging

from .errors import MissingDataDirectoryError, MissingCSVFileError
from .file_operations.csv_reader import (
    find_latest_csv_file,
    extract_followup_website_urls,
)
from .downloader import FollowupWebsiteDownloader
from .file_operations.page import PageFileManager
from .statistics import display_completion_summary
from .consts import (
    SCRIPT_DIR,
    DATA_DIR_NAME,
    RESPONSES_FOLLOWUP_WEBSITE_DIR_NAME,
    LOG_DIR_NAME,
    LOG_MESSAGES,
)


def scrape_followup_websites() -> str:
    """
    Main function to scrape followup website pages.

    Returns:
        Timestamp string of when scraping started
    """

    # Step 1: Find the last timestamp directory FIRST
    try:
        timestamp_dir = _find_latest_timestamp_directory()

    except FileNotFoundError as e:
        raise MissingDataDirectoryError(
            expected_path=os.path.join(SCRIPT_DIR, DATA_DIR_NAME),
            hint="Run the initiatives scraper first to create the timestamp directory.",
        ) from e

    # Step 2: Setup log directory and initialize logger
    log_dir = os.path.join(timestamp_dir, LOG_DIR_NAME)
    print(f"Creating log file in: {log_dir}")

    # Import and initialize logger AFTER finding timestamp_dir
    from .scraper_logger import initialize_logger

    logger = initialize_logger(log_dir)

    logger.info(LOG_MESSAGES["scraping_start"].format(timestamp=timestamp_dir))
    start_scraping = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # Step 3: Find the latest eci_responses CSV file in the timestamp directory
    try:
        csv_path = find_latest_csv_file(timestamp_dir)
    except MissingCSVFileError as e:
        logger.error(str(e))
        return start_scraping

    # Step 4: Extract followup website URLs from the CSV
    followup_urls = extract_followup_website_urls(csv_path)

    if not followup_urls:
        logger.warning(LOG_MESSAGES["no_urls_found"])
        return start_scraping

    logger.info(LOG_MESSAGES["urls_extracted"].format(count=len(followup_urls)))

    # Step 5: Setup followup website output directory
    followup_website_dir = os.path.join(
        timestamp_dir, RESPONSES_FOLLOWUP_WEBSITE_DIR_NAME
    )
    file_ops = PageFileManager(followup_website_dir)
    file_ops.setup_directories()

    # Step 6: Download followup website pages
    successful_items, failed_items = _download_followup_websites(
        followup_website_dir, followup_urls
    )

    # Step 7: Display completion summary
    downloaded_count = len(successful_items)
    display_completion_summary(
        start_scraping,
        followup_urls,
        failed_items,
        downloaded_count,
        followup_website_dir,
    )

    return start_scraping


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
        d for d in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, d))
    ]

    if not timestamp_dirs:
        raise FileNotFoundError(f"No timestamp directories found in: {data_dir}")

    # Sort to get latest (most recent timestamp)
    timestamp_dirs.sort(reverse=True)
    latest_timestamp_dir = os.path.join(data_dir, timestamp_dirs[0])

    return latest_timestamp_dir


def _download_followup_websites(
    followup_website_dir: str, followup_urls: List[dict]
) -> Tuple[List[dict], List[dict]]:
    """
    Download all followup website pages.

    Args:
        followup_website_dir: Directory to save followup website pages
        followup_urls: List of followup URL dictionaries

    Returns:
        Tuple of (successful_items, failed_items)
    """
    downloader = FollowupWebsiteDownloader(followup_website_dir)
    return downloader.download_all_followup_websites(followup_urls)


if __name__ == "__main__":
    scrape_followup_websites()
