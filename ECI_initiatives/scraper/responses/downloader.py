"""
Download Commission response pages using Selenium.
"""
import datetime
import random
import time
import logging
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
from .file_operations.page import save_response_html_file


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
        self.logger = logging.getLogger("ECIResponsesScraper")
    
    def download_all_responses(self, response_links: List[Dict[str, str]]) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
        """
        Download all Commission response pages with retry logic for failures.
        
        Args:
            response_links: List of dictionaries with 'url', 'year', 'reg_number', 'title'
            
        Returns:
            Tuple of (updated_response_data, failed_items)
        """
        updated_data = []
        failed_items = []
        
        try:
            # Initialize browser once for all downloads
            self._initialize_driver()
            
            # Download each response page
            self.logger.info("Starting download pass...")

            for link_data in response_links:

                url = link_data['url']
                year = link_data['year']
                reg_number = link_data['reg_number']
                
                success, timestamp = self.download_single_response(url, year, reg_number)
                
                # Update data with timestamp
                updated_item = {
                    'url_find_initiative': url,
                    'registration_number': reg_number,
                    'title': link_data.get('title', ''),
                    'datetime': timestamp if success else ''
                }
                
                if success:
                    updated_data.append(updated_item)
                else:
                    failed_items.append(link_data)
                
                # Wait between downloads
                wait_time = random.uniform(*WAIT_BETWEEN_DOWNLOADS)
                time.sleep(wait_time)
            
        finally:
            self._close_driver()
        
        return updated_data, failed_items

    
    def download_single_response(
        self, 
        url: str, 
        year: str, 
        reg_number: str,
        max_retries: int = DEFAULT_MAX_RETRIES
    ) -> Tuple[bool, str]:
        """
        Download a single Commission response page with retry logic.
        
        Args:
            url: Full URL to the response page
            year: Year of the initiative
            reg_number: Registration number
            max_retries: Maximum number of retry attempts
        
        Returns:
            Tuple of (success: bool, timestamp: str)
        """
        actual_url = url
        
        for attempt in range(max_retries):
            try:
                # On first attempt, check if URL redirects
                if attempt == 0:

                    self.driver.get(url)
                    time.sleep(1)
                    actual_url = self.driver.current_url
                    
                    if actual_url != url:

                        self.logger.info(f"URL redirected: {url} -> {actual_url}")
                else:
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
                filename = save_response_html_file(self.responses_dir, year, reg_number, page_source)
                
                # Get current timestamp
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                self.logger.info(LOG_MESSAGES["download_success"].format(filename=filename))
                return True, timestamp
                
            except Exception as e:
                self.logger.warning(f"Download attempt {attempt + 1}/{max_retries} failed for {url}: {str(e)}")
                
                if attempt < max_retries - 1:
                    base_wait = random.uniform(*RETRY_WAIT_BASE)
                    wait_time = base_wait * (2 ** attempt)
                    self.logger.info(LOG_MESSAGES["rate_limit_retry"].format(
                        retry=attempt + 1,
                        max_retries=max_retries,
                        wait_time=wait_time
                    ))
                    time.sleep(wait_time)
        
        self.logger.error(LOG_MESSAGES["download_failed"].format(url=url))
        return False, ""

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
                    self.logger.debug(f"Page loaded - found element: {selector}")
                    return  # Success - exit method
                except Exception:
                    continue  # Try next selector
            
            # If we get here, no selectors worked but page might still be loaded
            self.logger.warning("Could not verify page load with expected selectors, proceeding anyway")
            
        except Exception as e:
            self.logger.warning(f"Timeout waiting for page content: {str(e)}")
    
    def _initialize_driver(self) -> None:
        """Initialize the WebDriver if not already initialized."""

        if self.driver is None:
            self.driver = initialize_browser()
    
    def _close_driver(self) -> None:
        """Close the WebDriver and clean up resources."""

        if self.driver:
            try:
                self.driver.quit()
                self.logger.info(LOG_MESSAGES["browser_closed"])
            except Exception as e:
                self.logger.error(f"Error closing browser: {str(e)}")
            finally:
                self.driver = None
