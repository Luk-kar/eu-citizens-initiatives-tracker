"""Tests for scraping process behavior and flow."""

# Standard library
import csv
import os
import sys
import time
from unittest.mock import Mock, patch, MagicMock, call

# Third party
import pytest
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.common.by import By

# Local imports (handled by conftest fixture)
from ECI_initiatives.tests.consts import (
    BASE_URL,
    LISTINGS_HTML_DIR,
    SAMPLE_LISTING_FILES,
    REQUIRED_CSV_COLUMNS,
    DEFAULT_WEBDRIVER_TIMEOUT,
    PAGE_CONTENT_TIMEOUT,
    LISTING_HTML_PATTERN,
    RATE_LIMIT_INDICATORS,
    SAMPLE_INITIATIVE_DATA,
    FULL_FIND_INITIATIVE_URL,
)


class TestPaginationHandling:
    """Test pagination functionality."""

    @classmethod
    def setup_class(cls):
        """
        Import modules and set up class attributes.

        Imports are done here rather than at module level to avoid
        log file creation during module loading, allowing the session
        fixture to properly track and clean up test artifacts.
        """
        from ECI_initiatives.data_pipeline.scraper.initiatives import crawler
        from ECI_initiatives.data_pipeline.scraper.initiatives import file_ops

        cls.navigate_to_next_page = staticmethod(crawler.navigate_to_next_page)
        cls.wait_for_listing_page_content = staticmethod(
            crawler.wait_for_listing_page_content
        )
        cls.scrape_single_listing_page = staticmethod(
            crawler.scrape_single_listing_page
        )
        cls.scrape_all_initiatives_on_all_pages = staticmethod(
            crawler.scrape_all_initiatives_on_all_pages
        )
        cls.save_listing_page = staticmethod(file_ops.save_listing_page)

    @pytest.fixture
    def mock_driver(self):
        """Create a mock driver for testing."""
        mock_driver = Mock(spec=webdriver.Chrome)
        mock_driver.page_source = ""
        return mock_driver

    @pytest.fixture
    def sample_listing_html(self):
        """Load sample listing HTML from test data."""
        first_page_path = os.path.join(LISTINGS_HTML_DIR, SAMPLE_LISTING_FILES[0])
        if os.path.exists(first_page_path):
            with open(first_page_path, "r", encoding="utf-8") as f:
                return f.read()
        return ""

    @patch("ECI_initiatives.data_pipeline.scraper.initiatives.crawler.logger")
    @patch(
        "ECI_initiatives.data_pipeline.scraper.initiatives.crawler.time"
    )  # Mock time module in crawler
    def test_navigate_to_next_page_success(self, mock_time, mock_logger, mock_driver):
        """Test successful navigation to next page."""

        # Import to get crawler constants
        from ECI_initiatives.data_pipeline.scraper.initiatives import crawler

        # Arrange
        mock_next_button = Mock()
        mock_driver.find_element.return_value = mock_next_button

        # Act
        result = self.navigate_to_next_page(mock_driver, 1)

        # Assert
        assert result is True
        mock_driver.find_element.assert_called_with(
            By.CSS_SELECTOR, crawler.ECIlistingSelectors.NEXT_BUTTON
        )
        mock_driver.execute_script.assert_called_with(
            "arguments[0].click();", mock_next_button
        )
        mock_time.sleep.assert_called()  # Check sleep called on time module mock

    @patch("ECI_initiatives.data_pipeline.scraper.initiatives.crawler.logger")
    def test_navigate_to_next_page_not_found(self, mock_logger, mock_driver):
        """Test behavior when next button is not found (last page)."""

        # Import to get crawler constants
        from ECI_initiatives.data_pipeline.scraper.initiatives import crawler

        # Arrange
        mock_driver.find_element.side_effect = NoSuchElementException("No next button")

        # Act
        result = self.navigate_to_next_page(mock_driver, 5)

        # Assert
        assert result is False
        mock_logger.info.assert_called_with(
            crawler.LOG_MESSAGES["last_page"].format(page=5)
        )

    @patch("ECI_initiatives.data_pipeline.scraper.initiatives.crawler.logger")
    @patch("ECI_initiatives.data_pipeline.scraper.initiatives.crawler.WebDriverWait")
    def test_wait_for_content_success(self, mock_wait, mock_logger, mock_driver):
        """Test successful wait for page content."""

        # Arrange
        mock_wait_instance = Mock()
        mock_wait.return_value = mock_wait_instance

        # Act
        self.wait_for_listing_page_content(mock_driver, 1)

        # Assert
        mock_wait_instance.until.assert_called()
        mock_logger.info.assert_called()

    @patch("ECI_initiatives.data_pipeline.scraper.initiatives.crawler.logger")
    @patch("ECI_initiatives.data_pipeline.scraper.initiatives.crawler.WebDriverWait")
    def test_wait_for_content_timeout(self, mock_wait, mock_logger, mock_driver):
        """Test handling of timeout when waiting for content."""

        # Arrange
        mock_wait_instance = Mock()
        mock_wait.return_value = mock_wait_instance
        mock_wait_instance.until.side_effect = TimeoutException("Timed out")

        # Act
        self.wait_for_listing_page_content(mock_driver, 1)

        # Assert
        mock_logger.warning.assert_called()


class TestErrorRecoveryAndResilience:
    """Test error handling and recovery mechanisms."""

    @classmethod
    def setup_class(cls):
        """
        Import modules and set up class attributes.

        Imports are done here rather than at module level to avoid
        log file creation during module loading, allowing the session
        fixture to properly track and clean up test artifacts.
        """
        from ECI_initiatives.data_pipeline.scraper.initiatives import downloader
        from ECI_initiatives.data_pipeline.scraper.initiatives import browser

        cls.download_single_initiative = staticmethod(
            downloader.download_single_initiative
        )
        cls.download_initiatives = staticmethod(downloader.download_initiatives)
        cls.check_rate_limiting = staticmethod(downloader.check_rate_limiting)
        cls.initialize_browser = staticmethod(browser.initialize_browser)

    @pytest.fixture
    def mock_driver(self):
        """Create a mock driver for testing."""
        return Mock(spec=webdriver.Chrome)

    @patch("ECI_initiatives.data_pipeline.scraper.initiatives.downloader.logger")
    def test_individual_page_download_failure_handling(
        self, mock_logger, mock_driver, tmp_path
    ):
        """Test behavior when individual initiative pages fail to download."""

        # Simulate a WebDriver exception during page load
        mock_driver.get.side_effect = WebDriverException("Connection failed")

        url = f"{BASE_URL}/initiatives/details/2024/000001_en"
        result = self.download_single_initiative(
            mock_driver, str(tmp_path), url, max_retries=1
        )

        assert result is False
        mock_driver.get.assert_called_with(url)

    @patch("ECI_initiatives.data_pipeline.scraper.initiatives.downloader.logger")
    @patch(
        "ECI_initiatives.data_pipeline.scraper.initiatives.downloader.download_single_initiative"
    )
    @patch(
        "ECI_initiatives.data_pipeline.scraper.initiatives.downloader.initialize_browser"
    )
    @patch("ECI_initiatives.data_pipeline.scraper.initiatives.downloader.time")
    @patch("ECI_initiatives.data_pipeline.scraper.initiatives.downloader.random")
    def test_failed_downloads_recorded_properly(
        self, mock_random, mock_sleep, mock_init_browser, mock_download, mock_logger
    ):
        """Verify that failed downloads are properly recorded and reported."""

        mock_driver = Mock()
        mock_init_browser.return_value = mock_driver
        mock_random.uniform.return_value = 1.0

        # Simulate some successful and some failed downloads
        mock_download.side_effect = [True, False, True, False]

        test_data = [
            {
                REQUIRED_CSV_COLUMNS.URL: "http://test1.com",
                REQUIRED_CSV_COLUMNS.CURRENT_STATUS: "active",
            },
            {
                REQUIRED_CSV_COLUMNS.URL: "http://test2.com",
                REQUIRED_CSV_COLUMNS.CURRENT_STATUS: "active",
            },
            {
                REQUIRED_CSV_COLUMNS.URL: "http://test3.com",
                REQUIRED_CSV_COLUMNS.CURRENT_STATUS: "active",
            },
            {
                REQUIRED_CSV_COLUMNS.URL: "http://test4.com",
                REQUIRED_CSV_COLUMNS.CURRENT_STATUS: "active",
            },
        ]

        updated_data, failed_urls = self.download_initiatives("/tmp", test_data)

        assert len(failed_urls) == 2
        assert "http://test2.com" in failed_urls
        assert "http://test4.com" in failed_urls
        assert len(updated_data) == 4

    @patch("ECI_initiatives.data_pipeline.scraper.initiatives.downloader.logger")
    @patch("ECI_initiatives.data_pipeline.scraper.initiatives.downloader.time")
    @patch(
        "ECI_initiatives.data_pipeline.scraper.initiatives.downloader.random.uniform",
        return_value=1.0,
    )
    def test_rate_limiting_handling(
        self, mock_uniform, mock_sleep, mock_logger, mock_driver
    ):
        """Check that rate limiting is handled gracefully with appropriate retries."""

        # Test rate limiting detection in page content
        mock_driver.page_source = f"<html><head><title>{RATE_LIMIT_INDICATORS.SERVER_INACCESSIBILITY}</title></head><body>{RATE_LIMIT_INDICATORS.TOO_MANY_REQUESTS}</body></html>"

        url = f"{FULL_FIND_INITIATIVE_URL}/details/2024/000001_en"

        with patch(
            "ECI_initiatives.data_pipeline.scraper.initiatives.downloader.check_rate_limiting"
        ) as mock_check:
            mock_check.side_effect = Exception(
                f"{RATE_LIMIT_INDICATORS.RATE_LIMITED} (HTML response)"
            )

            result = self.download_single_initiative(
                mock_driver, "/tmp", url, max_retries=1
            )
            assert result is False
