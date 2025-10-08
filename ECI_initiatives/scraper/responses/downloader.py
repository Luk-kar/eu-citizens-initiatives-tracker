"""
Download Commission response pages using Selenium.
"""
import datetime
import random
import time
from typing import List, Dict, Tuple

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .browser import initialize_browser
from .css_selectors import ResponsePageSelectors
from .consts import (
    WAIT_DYNAMIC_CONTENT,
    WAIT_BETWEEN_DOWNLOADS,
    RETRY_WAIT_BASE,
    WEBDRIVER_TIMEOUT_CONTENT,
    DEFAULT_MAX_RETRIES,
    RATE_LIMIT_INDICATORS,
    LOG_MESSAGES
)
from .file_operations import save_response_page
from .scraper_logger import logger


class ResponseDownloader:
    """Download Commission response pages with retry logic and error handling."""

    def __init__(self, responses_dir: str):
        """
        Initialize the downloader.

        Args:
            responses_dir: Base directory for saving response HTML files
        """

        self.responses_dir = responses_dir
        self.driver = None

    def download_all_responses(self, response_links: List[Dict[str, str]]) -> Tuple[int, List[str]]:
        """
        Download all Commission response pages with retry logic for failures.
        
        Args:
            response_links: List of dictionaries with 'url', 'year', 'reg_number'
            
        Returns:
            Tuple of (downloaded_count, failed_urls_list)
        """
        downloaded_count = 0
        failed_items = []
        
        try:
            # Initialize browser once for all downloads
            self._initialize_driver()
            
            # First pass: Download each response page
            logger.info("Starting first download pass...")
            for link_data in response_links:
                
                url = link_data['url']
                year = link_data['year']
                reg_number = link_data['reg_number']
                
                success = self.download_single_response(url, year, reg_number)
                
                if success:
                    downloaded_count += 1
                else:
                    # Store full link_data for retry
                    failed_items.append(link_data)
                
                # Wait between downloads to avoid rate limiting
                wait_time = random.uniform(*WAIT_BETWEEN_DOWNLOADS)
                time.sleep(wait_time)
            
        finally:
            # Clean up browser
            self._close_driver()

        return downloaded_count, failed_items

    def download_single_response(
        self, 
        url: str, 
        year: str, 
        reg_number: str,
        max_retries: int = DEFAULT_MAX_RETRIES
    ) -> bool:
        """
        Download a single Commission response page with retry logic.

        Args:
            url: Full URL to the response page
            year: Year of the initiative
            reg_number: Registration number
            max_retries: Maximum number of retry attempts

        Returns:
            True if successful, False if failed
        """

        actual_url = url

        for attempt in range(max_retries):

            try:

                # On first attempt, check if URL redirects
                if attempt == 0:
                    self.driver.get(url)
                    time.sleep(1)  # Wait for redirect
                    actual_url = self.driver.current_url
                    
                    # Log redirect if it occurred
                    if actual_url != url:
                        logger.info(f"URL redirected: {url} -> {actual_url}")
                else:
                    # Use actual URL for retry attempts
                    self.driver.get(actual_url)

                # Wait for page content to load
                self._wait_for_page_content()

                # Check for rate limiting
                self._check_rate_limiting()

                # Wait for dynamic content
                wait_time = random.uniform(*WAIT_DYNAMIC_CONTENT)
                time.sleep(wait_time)

                # Get page source
                page_source = self.driver.page_source

                # Save to file
                filename = save_response_page(self.responses_dir, year, reg_number, page_source)

                logger.info(LOG_MESSAGES["download_success"].format(filename=filename))
                return True

            except Exception as e:
                logger.warning(f"Download attempt {attempt + 1}/{max_retries} failed for {url}: {str(e)}")

                if attempt < max_retries - 1:

                    # Calculate exponential backoff wait time
                    base_wait = random.uniform(*RETRY_WAIT_BASE)
                    wait_time = base_wait * (2 ** attempt)
                    logger.info(LOG_MESSAGES["rate_limit_retry"].format(
                        retry=attempt + 1,
                        max_retries=max_retries,
                        wait_time=wait_time
                    ))
                    time.sleep(wait_time)

        logger.error(LOG_MESSAGES["download_failed"].format(url=url))
        return False

    def _check_rate_limiting(self) -> None:
        """
        Check if the current page shows rate limiting errors.

        Raises:
            Exception: If rate limiting is detected
        """

        page_source = self.driver.page_source.lower()

        for indicator in RATE_LIMIT_INDICATORS:
            if indicator.lower() in page_source:
                raise Exception(f"Rate limiting detected: {indicator}")

    def _wait_for_page_content(self) -> None:
        """
        Wait for response page content to load.
        
        Uses explicit waits for specific page elements with fallback selectors.
        """
        
        try:
            # Try multiple selectors in order of preference
            selectors_to_try = [
                ResponsePageSelectors.MAIN_CONTENT,  # div.ecl-container
                ResponsePageSelectors.PAGE_HEADER_TITLE,  # h1.ecl-page-header__title  
                "main#main-content",  # Main content area
                "body"  # Last resort fallback
            ]
            
            for selector in selectors_to_try:
                try:
                    WebDriverWait(self.driver, WEBDRIVER_TIMEOUT_CONTENT).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    logger.debug(f"Page loaded - found element: {selector}")
                    return  # Success - exit method
                except Exception:
                    continue  # Try next selector
            
            # If we get here, no selectors worked but page might still be loaded
            logger.warning("Could not verify page load with expected selectors, proceeding anyway")
            
        except Exception as e:
            logger.warning(f"Timeout waiting for page content: {str(e)}")

    def _initialize_driver(self) -> None:
        """Initialize the WebDriver if not already initialized."""

        if self.driver is None:
            self.driver = initialize_browser()

    def _close_driver(self) -> None:
        """Close the WebDriver and clean up resources."""

        if self.driver:
            try:
                self.driver.quit()
                logger.info(LOG_MESSAGES["browser_closed"])
            except Exception as e:
                logger.error(f"Error closing browser: {str(e)}")
            finally:
                self.driver = None
