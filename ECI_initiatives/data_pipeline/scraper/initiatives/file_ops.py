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
