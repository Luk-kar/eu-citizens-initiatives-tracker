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
