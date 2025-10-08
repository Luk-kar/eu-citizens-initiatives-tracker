"""
Main entry point for Commission responses scraper.
"""
import os
import time
from typing import List, Tuple
from pathlib import Path

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
    LOG_MESSAGES,
    RESPONSES_DIR
)
from .scraper_logger import logger


def scrape_commission_responses() -> str:
    """
    Main function to scrape Commission response pages.
    
    Returns:
        Timestamp string of when scraping started
    """
    logger.info(LOG_MESSAGES["scraping_start"].format(timestamp=START_SCRAPING))
    
    # Setup directories
    responses_dir = _setup_output_directory()
    
    # Find latest initiative pages data directory
    initiative_pages_dir = _find_latest_initiative_pages_directory()
    
    if not initiative_pages_dir:
        logger.error("No initiative pages directory found. Run initiative scraper first.")
        return START_SCRAPING
    
    # Extract Commission response links from initiative pages
    response_links = _extract_response_links(initiative_pages_dir)
    
    if not response_links:
        logger.warning(LOG_MESSAGES["no_links_found"])
        return START_SCRAPING
    
    logger.info(LOG_MESSAGES["links_found"].format(count=len(response_links)))
    
    # Download response pages
    downloaded_count, failed_items = _download_responses(responses_dir, response_links)

    # Display completion summary
    display_completion_summary(START_SCRAPING, response_links, failed_items, downloaded_count)
        
    return START_SCRAPING


def _setup_output_directory() -> str:
    """
    Setup output directory for response pages.
    
    Returns:
        Path to responses directory
    """
    file_ops = FileOperations(RESPONSES_DIR)
    file_ops.setup_directories()
    return RESPONSES_DIR


def _find_latest_initiative_pages_directory() -> str:
    """
    Find the most recent initiative pages directory.
    
    Returns:
        Path to latest initiative_pages directory or empty string if not found
    """
    data_dir = os.path.join(SCRIPT_DIR, DATA_DIR_NAME)
    
    if not os.path.exists(data_dir):
        return ""
    
    # Find all timestamp directories
    timestamp_dirs = [d for d in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, d))]
    
    if not timestamp_dirs:
        return ""
    
    # Sort to get latest
    timestamp_dirs.sort(reverse=True)
    
    # Check each for initiative_pages directory
    for ts_dir in timestamp_dirs:
        initiative_pages_path = os.path.join(data_dir, ts_dir, INITIATIVE_PAGES_DIR_NAME)
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
