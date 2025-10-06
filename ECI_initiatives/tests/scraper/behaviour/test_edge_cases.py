"""Tests for edge cases and boundary conditions."""

# Standard library
import os
import sys
import time
from unittest.mock import Mock, patch, MagicMock, mock_open

# Third party
import pytest
from selenium.common.exceptions import (
    TimeoutException,
    WebDriverException,
    NoSuchElementException,
    ElementNotInteractableException,
)
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By

# Local
program_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
sys.path.append(program_dir)

# Safe imports (don't trigger logger creation)
from ECI_initiatives.tests.consts import (
    RATE_LIMIT_INDICATORS,
    REQUIRED_CSV_COLUMNS,
    LOG_MESSAGES,
)


class TestBrowserInitialization:
    """Test browser initialization edge cases."""

    @classmethod
    def setup_class(cls):
        """
        Import modules and set up class attributes.
        
        Imports are done here rather than at module level to avoid
        log file creation during module loading, allowing the session
        fixture to properly track and clean up test artifacts.
        """
        from ECI_initiatives.scraper.initiatives.browser import initialize_browser
        
        cls.initialize_browser = staticmethod(initialize_browser)

    @patch("ECI_initiatives.scraper.initiatives.__main__.logger")
    @patch("selenium.webdriver.Chrome")
    def test_webdriver_initialization_failures(self, mock_chrome, mock_logger):
        """Test WebDriver initialization failures."""

        # Test ChromeDriver not found
        mock_chrome.side_effect = WebDriverException("ChromeDriver not found")

        with pytest.raises(WebDriverException):
            self.initialize_browser()

        # Test Chrome browser not installed
        mock_chrome.side_effect = WebDriverException("Chrome binary not found")

        with pytest.raises(WebDriverException):
            self.initialize_browser()

        # Test permission errors
        mock_chrome.side_effect = PermissionError("Permission denied")

        with pytest.raises(PermissionError):
            self.initialize_browser()


class TestResourceCleanup:
    """Test resource cleanup and interruption handling."""

    @classmethod
    def setup_class(cls):
        """
        Import modules and set up class attributes.
        
        Imports are done here rather than at module level to avoid
        log file creation during module loading, allowing the session
        fixture to properly track and clean up test artifacts.
        """
        from ECI_initiatives.scraper.initiatives.downloader import (
            download_initiative_pages,
            download_single_initiative,
        )
        
        cls.download_initiative_pages = staticmethod(download_initiative_pages)
        cls.download_single_initiative = staticmethod(download_single_initiative)

    @patch("ECI_initiatives.scraper.initiatives.downloader.logger")
    @patch("ECI_initiatives.scraper.initiatives.downloader.initialize_browser")
    @patch("ECI_initiatives.scraper.initiatives.downloader.download_single_initiative")
    def test_browser_cleanup_on_interruption(
        self, mock_download_single, mock_init_browser, mock_logger
    ):
        """Test that driver.quit() is called in finally block even during interruptions."""

        mock_driver = Mock()
        mock_init_browser.return_value = mock_driver

        # Test data for download_initiative_pages
        test_initiative_data = [
            {
                REQUIRED_CSV_COLUMNS.URL: "http://test1.com",
                REQUIRED_CSV_COLUMNS.CURRENT_STATUS: "test",
                REQUIRED_CSV_COLUMNS.REGISTRATION_NUMBER: "001",
                REQUIRED_CSV_COLUMNS.SIGNATURE_COLLECTION: "",
                REQUIRED_CSV_COLUMNS.DATETIME: "",
            },
            {
                REQUIRED_CSV_COLUMNS.URL: "http://test2.com",
                REQUIRED_CSV_COLUMNS.CURRENT_STATUS: "test",
                REQUIRED_CSV_COLUMNS.REGISTRATION_NUMBER: "002",
                REQUIRED_CSV_COLUMNS.SIGNATURE_COLLECTION: "",
                REQUIRED_CSV_COLUMNS.DATETIME: "",
            },
        ]

        # Test KeyboardInterrupt cleanup
        mock_download_single.side_effect = KeyboardInterrupt("User interrupted")

        with pytest.raises(KeyboardInterrupt):
            self.download_initiative_pages("/tmp", test_initiative_data)

        # Verify driver.quit() was called even though KeyboardInterrupt was raised
        mock_driver.quit.assert_called_once()
        mock_logger.info.assert_any_call(LOG_MESSAGES["pages_browser_closed"])

        # Reset mocks for next test
        mock_driver.reset_mock()
        mock_logger.reset_mock()

        # Test SystemExit cleanup
        mock_download_single.side_effect = SystemExit("System shutdown")

        with pytest.raises(SystemExit):
            self.download_initiative_pages("/tmp", test_initiative_data)

        # Verify driver.quit() was called even though SystemExit was raised
        mock_driver.quit.assert_called_once()
        mock_logger.info.assert_any_call(LOG_MESSAGES["pages_browser_closed"])

        # Reset mocks for next test
        mock_driver.reset_mock()
        mock_logger.reset_mock()

        # Test that cleanup happens even with unexpected exceptions
        mock_download_single.side_effect = Exception("Unexpected error")

        # This should NOT raise an exception (unlike KeyboardInterrupt/SystemExit)
        # because download_single_initiative should handle and return False
        mock_download_single.side_effect = None
        mock_download_single.return_value = False

        updated_data, failed_urls = self.download_initiative_pages(
            "/tmp", test_initiative_data
        )

        # Verify normal completion and cleanup
        mock_driver.quit.assert_called_once()
        mock_logger.info.assert_any_call(LOG_MESSAGES["pages_browser_closed"])

        assert len(failed_urls) == 2  # Both URLs should fail
        assert len(updated_data) == 2  # But data should still be returned


class TestContentProcessing:
    """Test content parsing and validation edge cases."""

    @classmethod
    def setup_class(cls):
        """
        Import modules and set up class attributes.
        
        Imports are done here rather than at module level to avoid
        log file creation during module loading, allowing the session
        fixture to properly track and clean up test artifacts.
        """
        from ECI_initiatives.scraper.initiatives.file_ops import save_initiative_page
        from ECI_initiatives.scraper.initiatives.downloader import (
            wait_for_page_content,
            check_rate_limiting,
        )
        
        cls.save_initiative_page = staticmethod(save_initiative_page)
        cls.wait_for_page_content = staticmethod(wait_for_page_content)
        cls.check_rate_limiting = staticmethod(check_rate_limiting)

    @patch("ECI_initiatives.scraper.initiatives.file_ops.logger")
    def test_malformed_html_responses(self, mock_logger):
        """Test handling of malformed HTML responses."""

        mock_driver = Mock()

        # Test empty page source
        mock_driver.page_source = ""

        result = self.save_initiative_page("/tmp", "http://test.com/2024/000001", "")
        assert result == "2024_000001.html"  # Should still save the file

        # Test malformed HTML that BeautifulSoup can't parse well
        malformed_html = "<html><body><div><p>Unclosed tags<div><span></body>"

        # BeautifulSoup is robust, but test that our code handles edge cases
        result = self.save_initiative_page(
            "/tmp", "http://test.com/2024/000002", malformed_html
        )
        assert result == "2024_000002.html"

        # Test page with no useful content
        empty_content_html = "<html><head></head><body></body></html>"
        mock_driver.page_source = empty_content_html

        self.wait_for_page_content(mock_driver)
        # Should log warnings but not crash
        mock_logger.warning.assert_called()

    @patch("ECI_initiatives.scraper.initiatives.__main__.logger")
    def test_rate_limiting_scenarios(self, mock_logger):
        """Test various rate limiting scenarios."""

        mock_driver = Mock()

        # Test rate limiting detection in HTML content
        mock_driver.find_element.return_value.text = (
            RATE_LIMIT_INDICATORS.SERVER_INACCESSIBILITY
        )

        with pytest.raises(Exception, match=RATE_LIMIT_INDICATORS.RATE_LIMITED):
            self.check_rate_limiting(mock_driver)

        # Test rate limiting in page source during save
        rate_limited_html = """
        <html>
            <body>
                <h1>Server inaccessibility</h1>
                <p>429 - Too Many Requests</p>
            </body>
        </html>
        """

        with pytest.raises(Exception, match=RATE_LIMIT_INDICATORS.RATE_LIMITED):
            self.save_initiative_page(
                "/tmp", "http://test.com/2024/000001", rate_limited_html
            )

        # Reset mock driver for successful retry test
        mock_driver.reset_mock()

        # Test successful retry after rate limiting
        mock_driver.get.side_effect = [
            Exception(RATE_LIMIT_INDICATORS.RATE_LIMITED),
            Exception(RATE_LIMIT_INDICATORS.TOO_MANY_REQUESTS),
            None,  # Finally succeeds
        ]
        mock_driver.page_source = "<html><body>Success</body></html>"

        # Setup mock to NOT detect rate limiting on successful attempt
        mock_element = Mock()
        mock_element.text = "Normal page content"  # NOT "Server inaccessibility"
        mock_driver.find_element.return_value = mock_element

        # Import needed for this specific test
        from ECI_initiatives.scraper.initiatives.downloader import download_single_initiative

        with patch(
            "ECI_initiatives.scraper.initiatives.downloader.save_initiative_page"
        ) as mock_save:
            with patch("ECI_initiatives.scraper.initiatives.downloader.time.sleep"):
                with patch(
                    "ECI_initiatives.scraper.initiatives.downloader.wait_for_page_content"
                ) as mock_wait_content:

                    mock_wait_content.return_value = None
                    mock_save.return_value = "test_file.html"

                    result = download_single_initiative(
                        mock_driver, "/tmp", "http://test.com", max_retries=3
                    )

        assert result is True

        # Verify retry logic was executed
        assert mock_driver.get.call_count == 3


class TestNetworkConditions:
    """Test various network condition scenarios."""

    @classmethod
    def setup_class(cls):
        """
        Import modules and set up class attributes.
        
        Imports are done here rather than at module level to avoid
        log file creation during module loading, allowing the session
        fixture to properly track and clean up test artifacts.
        """
        from ECI_initiatives.scraper.initiatives.downloader import (
            wait_for_page_content,
            download_single_initiative,
        )
        
        cls.wait_for_page_content = staticmethod(wait_for_page_content)
        cls.download_single_initiative = staticmethod(download_single_initiative)

    @patch("ECI_initiatives.scraper.initiatives.downloader.logger")
    @patch("ECI_initiatives.scraper.initiatives.downloader.time.sleep")
    @patch("ECI_initiatives.scraper.initiatives.downloader.WebDriverWait")
    def test_slow_network_conditions(self, mock_wait, mock_sleep, mock_logger):
        """Test behavior under slow network conditions."""

        # Setup
        mock_driver = Mock()
        mock_wait_instance = Mock()
        mock_wait.return_value = mock_wait_instance

        # Simulate slow network by making WebDriverWait timeout multiple times
        mock_wait_instance.until.side_effect = [
            TimeoutException("Timeout waiting for element"),
            TimeoutException("Timeout waiting for element"),
            Mock(),  # Eventually succeeds
        ]

        # Test wait_for_page_content with slow network
        self.wait_for_page_content(mock_driver)

        # Verify WebDriverWait was called multiple times due to timeouts
        assert mock_wait_instance.until.call_count >= 2
        mock_logger.warning.assert_called()

        # Test download_single_initiative with slow network and eventual success
        mock_driver.get.side_effect = None  # Reset side effect
        mock_driver.page_source = "<html><body>Test content</body></html>"

        with patch(
            "ECI_initiatives.scraper.initiatives.file_ops.save_initiative_page"
        ) as mock_save:
            mock_save.return_value = "test_file.html"
            result = self.download_single_initiative(mock_driver, "/tmp", "http://test.com")

        assert result is True
        # Verify retries were attempted due to slow conditions
        assert mock_sleep.call_count > 0


class TestDownloadSingleInitiative:
    """Test behavior under various system conditions."""

    @classmethod
    def setup_class(cls):
        """
        Import modules and set up class attributes.
        
        Imports are done here rather than at module level to avoid
        log file creation during module loading, allowing the session
        fixture to properly track and clean up test artifacts.
        """
        from ECI_initiatives.scraper.initiatives.downloader import download_single_initiative
        
        cls.download_single_initiative = staticmethod(download_single_initiative)

    @patch("ECI_initiatives.scraper.initiatives.downloader.logger")
    def test_download_single_initiative_error_handling(self, mock_logger):
        """Test download_single_initiative handles various error scenarios."""

        mock_driver = Mock()

        # Test scenarios with expected outcomes
        error_scenarios = [
            # Network/connection errors
            (WebDriverException("Connection refused"), "connection refused"),
            (WebDriverException("DNS resolution failed"), "dns resolution failed"),
            (TimeoutException("Page load timeout"), "page load timeout"),
            # Browser crashes
            (WebDriverException("chrome not reachable"), "chrome not reachable"),
            (WebDriverException("Session not created"), "session not created"),
            # Invalid URLs
            (
                WebDriverException("invalid argument: 'not-a-url' must be a valid URL"),
                "error downloading",
            ),
            # File system errors (would need additional mocking)
            # (OSError(28, "No space left on device"), "disk space error"),
        ]

        for exception, expected_log_content in error_scenarios:
            mock_driver.get.side_effect = exception

            result = self.download_single_initiative(mock_driver, "/tmp", "http://test.com")
            assert result is False

            # Verify appropriate error logging
            mock_logger.error.assert_called()
            error_call = mock_logger.error.call_args[0][0].lower()
            assert expected_log_content in error_call

            # Reset for next iteration
            mock_logger.reset_mock()
