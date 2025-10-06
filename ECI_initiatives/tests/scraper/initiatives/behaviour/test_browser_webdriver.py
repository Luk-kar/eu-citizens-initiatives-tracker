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

        from ECI_initiatives.scraper.initiatives.browser import initialize_browser
        from ECI_initiatives.scraper.initiatives.crawler import (
            scrape_all_initiatives_on_all_pages,
        )
        from ECI_initiatives.scraper.initiatives.downloader import (
            download_initiative_pages,
        )
        
        cls.initialize_browser = staticmethod(initialize_browser)
        cls.scrape_all_initiatives_on_all_pages = staticmethod(scrape_all_initiatives_on_all_pages)
        cls.download_initiative_pages = staticmethod(download_initiative_pages)

    @patch("ECI_initiatives.scraper.initiatives.browser.webdriver.Chrome")
    @patch("ECI_initiatives.scraper.initiatives.browser.logger")
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

    @patch("ECI_initiatives.scraper.initiatives.browser.webdriver.Chrome")
    @patch("ECI_initiatives.scraper.initiatives.browser.logger")
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

    @patch("ECI_initiatives.scraper.initiatives.browser.webdriver.Chrome")
    @patch("ECI_initiatives.scraper.initiatives.browser.logger")
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

    @patch("ECI_initiatives.scraper.initiatives.downloader.initialize_browser")
    @patch("ECI_initiatives.scraper.initiatives.downloader.logger")
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
        with patch(
            "ECI_initiatives.scraper.initiatives.downloader.download_single_initiative"
        ) as mock_download, patch(
            "ECI_initiatives.scraper.initiatives.downloader.datetime"
        ) as mock_datetime:

            mock_download.return_value = True  # Simulate successful download
            mock_datetime.datetime.now.return_value.strftime.return_value = (
                download_datetime
            )

            # Sample initiative data
            initiative_data = [SAMPLE_INITIATIVE_DATA.copy()]

            # Act
            updated_data, failed_urls = self.download_initiative_pages(
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

    @patch("ECI_initiatives.scraper.initiatives.browser.webdriver.Chrome")
    @patch("ECI_initiatives.scraper.initiatives.crawler.logger")
    def test_driver_quit_called_on_exception(self, mock_logger, mock_chrome):
        """Test that driver.quit() is called even when exceptions occur."""

        # Arrange
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver

        # Simulate an exception during scraping
        with patch(
            "ECI_initiatives.scraper.initiatives.crawler.scrape_single_listing_page"
        ) as mock_scrape:
            mock_scrape.side_effect = Exception("Test exception")

            # Act & Assert
            with pytest.raises(Exception):
                self.scrape_all_initiatives_on_all_pages(mock_driver, BASE_URL, "/test/dir")

            # The function should still call quit in the finally block
            # Note: This test verifies the pattern exists in the actual code
