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


def download_initiatives(pages_dir: str, initiative_data: list) -> Tuple[list, list]:
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
            raise Exception(RATE_LIMIT_INDICATORS[3])

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
