# Python Standard Library
from collections import Counter
from typing import Dict, List

# Third-party
from bs4 import BeautifulSoup

# Local
from .css_selectors import ECIlistingSelectors
from .scraper_logger import ScraperLogger

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
