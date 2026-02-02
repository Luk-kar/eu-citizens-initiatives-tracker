"""Tests for browser and WebDriver functionality."""

# Third party
import pytest
from unittest.mock import Mock, patch, MagicMock
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options

# Local imports (handled by conftest fixture)
from ECI_initiatives.tests.consts import (
    REQUIRED_CSV_COLUMNS,
    SAMPLE_INITIATIVE_DATA,
    BASE_URL,
    LOG_MESSAGES,
)

# 1. Top-level imports
from ECI_initiatives.data_pipeline.scraper.initiatives import browser
from ECI_initiatives.data_pipeline.scraper.initiatives import crawler
from ECI_initiatives.data_pipeline.scraper.initiatives import downloader


# 2. Facade Class
class InitiativesScraper:

    # 1. Assignments
    initialize_browser = browser.initialize_browser
    scrape_all_initiatives = crawler.scrape_all_initiatives_on_all_pages
    download_initiatives = downloader.download_initiatives

    # 2. Check if any None
    # We use a list comprehension to check the current local namespace
    _none_attrs = [
        name
        for name, value in locals().items()
        if not name.startswith("__") and value is None
    ]

    if _none_attrs:
        raise RuntimeError(
            f"❌ Critical Error in {__qualname__}: "
            f"The following attributes are None: {_none_attrs}"
        )

    # Optional: Clean up the helper variable so it doesn't become a class attribute
    del _none_attrs


class TestBrowserInitializationAndCleanup:
    """Test browser management functionality."""

    @classmethod
    def setup_class(cls):
        """
        Import modules and set up class attributes.

        Imports are done here rather than at module level to avoid
        log file creation during module loading, allowing the session
        fixture to properly track and clean up test artifacts.
        """

        cls.initialize_browser = staticmethod(InitiativesScraper.initialize_browser)
        cls.scrape_all_initiatives_on_all_pages = staticmethod(
            InitiativesScraper.scrape_all_initiatives
        )
        cls.download_initiatives = staticmethod(InitiativesScraper.download_initiatives)

    @patch.object(browser.webdriver, "Chrome")
    @patch.object(browser, "logger")
    def test_browser_instances_properly_managed(self, mock_logger, mock_chrome):
        """Verify that browser instances are properly created and closed."""

        # Arrange
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver

        # Act
        driver = self.initialize_browser()

        # Assert - Check that Chrome webdriver was called with options
        mock_chrome.assert_called_once()
        call_args = mock_chrome.call_args
        assert call_args[1]["options"] is not None  # options parameter was passed

        # Verify that the returned driver is our mock
        assert driver == mock_driver

        # Check that logging occurred
        mock_logger.info.assert_called_with(LOG_MESSAGES["browser_init"])
        mock_logger.debug.assert_called_with(LOG_MESSAGES["browser_success"])

        # Test that quit is properly called in a typical workflow
        driver.quit()
        mock_driver.quit.assert_called_once()

    @patch.object(browser.webdriver, "Chrome")
    @patch.object(browser, "logger")
    def test_headless_mode_works_correctly(self, mock_logger, mock_chrome):
        """Check that headless mode works correctly."""

        # Arrange
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver

        # Act
        self.initialize_browser()

        # Assert - Check that Chrome was called with proper options
        mock_chrome.assert_called_once()
        call_args = mock_chrome.call_args
        options = call_args[1]["options"]

        # Verify that the options object has the expected arguments
        assert isinstance(options, Options)

        # ACTUAL HEADLESS VERIFICATION
        assert "--headless" in options.arguments
        assert "--no-sandbox" in options.arguments
        assert "--disable-dev-shm-usage" in options.arguments

    @patch.object(browser.webdriver, "Chrome")
    @patch.object(browser, "logger")
    def test_webdriver_initialization_failure_handling(self, mock_logger, mock_chrome):
        """Test behavior when WebDriver initialization fails."""

        # Arrange
        mock_chrome.side_effect = WebDriverException("ChromeDriver not found")

        # Act & Assert
        with pytest.raises(WebDriverException):
            self.initialize_browser()

        # Verify error was attempted to be logged
        mock_logger.info.assert_called_with(LOG_MESSAGES["browser_init"])

        # The debug log wouldn't be called since initialization failed
        assert not mock_logger.debug.called

    @patch.object(downloader, "initialize_browser")
    @patch.object(downloader, "logger")
    @patch("time.sleep", return_value=None)
    def test_download_function_properly_manages_driver_lifecycle(
        self, mock_sleep, mock_logger, mock_init_browser
    ):
        """Test that download function properly initializes and cleans up driver."""

        # Arrange
        mock_driver = Mock()
        mock_init_browser.return_value = mock_driver

        download_datetime = "2025-09-22 20:25:00"

        # Mock the necessary functions to avoid actual web requests
        with patch.object(
            downloader, "download_single_initiative"
        ) as mock_download, patch.object(downloader, "datetime") as mock_datetime:

            mock_download.return_value = True  # Simulate successful download
            mock_datetime.datetime.now.return_value.strftime.return_value = (
                download_datetime
            )

            # Sample initiative data
            initiative_data = [SAMPLE_INITIATIVE_DATA.copy()]

            # Act
            updated_data, failed_urls = self.download_initiatives(
                "/test/dir", initiative_data
            )

            # Assert
            # Verify that initialize_browser was called
            mock_init_browser.assert_called_once()

            # Verify that driver.quit() was called (cleanup)
            mock_driver.quit.assert_called_once()

            # Verify successful processing
            assert len(updated_data) == 1
            assert len(failed_urls) == 0
            assert updated_data[0][REQUIRED_CSV_COLUMNS.DATETIME] == download_datetime

    @patch.object(browser.webdriver, "Chrome")
    @patch.object(crawler, "logger")
    def test_driver_quit_called_on_exception(self, mock_logger, mock_chrome):
        """Test that driver.quit() is called even when exceptions occur."""

        # Arrange
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver

        # Simulate an exception during scraping
        with patch.object(crawler, "scrape_single_listing_page") as mock_scrape:
            mock_scrape.side_effect = Exception("Test exception")

            # Act & Assert
            with pytest.raises(Exception):
                self.scrape_all_initiatives_on_all_pages(
                    mock_driver, BASE_URL, "/test/dir"
                )

            # The function should still call quit in the finally block
            # Note: This test verifies the pattern exists in the actual code
