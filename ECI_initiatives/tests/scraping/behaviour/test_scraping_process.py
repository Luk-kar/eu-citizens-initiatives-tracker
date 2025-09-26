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

# Local
program_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")

sys.path.append(program_dir)

from ECI_initiatives.scraper.browser import (
    initialize_browser,
)
from ECI_initiatives.scraper.crawler import (
    navigate_to_next_page,
    wait_for_listing_page_content,
    scrape_single_listing_page,
    scrape_all_initiatives_on_all_pages,
)
from ECI_initiatives.scraper.downloader import (
    download_single_initiative,
    download_initiative_pages,
    wait_for_page_content,
    check_rate_limiting,
    save_initiative_page,
)
from ECI_initiatives.scraper.file_ops import save_listing_page
from ECI_initiatives.scraper.data_parser import parse_initiatives_list_data

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

    @pytest.fixture
    def mock_driver(self):
        """Create a mock driver for testing."""
        mock_driver = Mock(spec=webdriver.Chrome)
        mock_driver.page_source = ""
        return mock_driver

    @pytest.fixture
    def sample_listing_html(self):
        """Load sample listing HTML from test data."""
        test_dir = os.path.join(
            os.path.dirname(__file__), "..", "..", "data", "example_htmls", "listings"
        )
        first_page_path = os.path.join(LISTINGS_HTML_DIR, SAMPLE_LISTING_FILES[0])

        if os.path.exists(first_page_path):
            with open(first_page_path, "r", encoding="utf-8") as f:
                return f.read()
        return '<html><body><div class="card">Test content</div></body></html>'

    @pytest.fixture
    def last_page_html(self):
        """Load last page HTML from test data."""
        test_dir = os.path.join(
            os.path.dirname(__file__), "..", "..", "data", "example_htmls", "listings"
        )
        last_page_path = os.path.join(LISTINGS_HTML_DIR, SAMPLE_LISTING_FILES[1])

        if os.path.exists(last_page_path):
            with open(last_page_path, "r", encoding="utf-8") as f:
                return f.read()
        return '<html><body><div class="card">Last page content</div></body></html>'

    @patch("ECI_initiatives.scraper.crawler.logger")
    @patch("ECI_initiatives.scraper.crawler.time.sleep")
    @patch("ECI_initiatives.scraper.crawler.random.uniform", return_value=1.0)
    def test_multiple_pages_handling(
        self, mock_uniform, mock_sleep, mock_logger, mock_driver, sample_listing_html
    ):
        """Test behavior when there are multiple pages of listings."""

        # Mock finding next button on first call, then not finding it
        mock_next_button = Mock()
        mock_driver.find_element.side_effect = [
            mock_next_button,
            NoSuchElementException(),
        ]
        mock_driver.page_source = sample_listing_html

        # First call should return True (next button found)
        result1 = navigate_to_next_page(mock_driver, 1)
        assert result1 is True

        # Second call should return False (no next button)
        result2 = navigate_to_next_page(mock_driver, 2)
        assert result2 is False

        # Verify execute_script was called for the first page
        mock_driver.execute_script.assert_called_once()

    @patch("ECI_initiatives.scraper.crawler.logger")
    def test_stops_at_last_page(self, mock_logger, mock_driver):
        """Verify that scraping stops correctly when reaching the last page."""

        # Simulate no next button found (last page scenario)
        mock_driver.find_element.side_effect = NoSuchElementException()

        result = navigate_to_next_page(mock_driver, 5)
        assert result is False

        # Ensure execute_script was not called since no button was found
        mock_driver.execute_script.assert_not_called()

    @patch("ECI_initiatives.scraper.file_ops.logger")
    @patch("ECI_initiatives.scraper.file_ops.time.sleep")
    @patch("ECI_initiatives.scraper.file_ops.random.uniform", return_value=1.0)
    def test_page_numbering_correspondence(
        self, mock_uniform, mock_sleep, mock_logger, mock_driver, tmp_path
    ):
        """Check that page numbering in saved files corresponds to actual pages scraped."""

        mock_driver.page_source = "<html><body>Page content</body></html>"

        # Test saving different page numbers
        for page_num in [1, 2, 10]:

            page_source, page_path = save_listing_page(
                mock_driver, str(tmp_path), page_num
            )

            expected_filename = f"{LISTING_HTML_PATTERN}{page_num:03d}.html"
            assert expected_filename in page_path
            assert os.path.exists(page_path)

    @patch("ECI_initiatives.scraper.__main__.logger")
    @patch(
        "ECI_initiatives.scraper.crawler.parse_initiatives_list_data",
        return_value=[
            {
                REQUIRED_CSV_COLUMNS.URL: "test",
                REQUIRED_CSV_COLUMNS.CURRENT_STATUS: "active",
            }
        ],
    )
    @patch("ECI_initiatives.scraper.crawler.wait_for_listing_page_content")
    @patch("ECI_initiatives.scraper.crawler.save_listing_page")
    def test_all_pages_processed_without_skipping(
        self, mock_save, mock_wait, mock_parse, mock_logger, mock_driver
    ):
        """Ensure all pages are processed without skipping any."""

        # Mock save_listing_page to return different content for each page
        mock_save.side_effect = [
            ("page1_content", "/path/page1.html"),
            ("page2_content", "/path/page2.html"),
            ("page3_content", "/path/page3.html"),
        ]

        # Simulate 3 pages total - next button available twice, then not available
        mock_driver.find_element.side_effect = [
            Mock(),  # Page 1 -> 2
            Mock(),  # Page 2 -> 3
            NoSuchElementException(),  # Page 3 (last page)
        ]

        with patch(
            "ECI_initiatives.scraper.crawler.navigate_to_next_page",
            side_effect=[True, True, False],
        ):
            all_data, saved_paths = scrape_all_initiatives_on_all_pages(
                mock_driver, "http://base.url", "/test/dir"
            )

        # Verify all 3 pages were processed
        assert len(saved_paths) == 3
        assert len(all_data) == 3  # Each page returns 1 initiative
        assert mock_save.call_count == 3

    @patch("ECI_initiatives.scraper.crawler.logger")
    @patch("ECI_initiatives.scraper.crawler.time.sleep")
    def test_navigate_to_next_page_functionality(
        self, mock_sleep, mock_logger, mock_driver
    ):
        """Test the navigate_to_next_page function behavior."""

        mock_next_button = Mock()
        mock_driver.find_element.return_value = mock_next_button

        result = navigate_to_next_page(mock_driver, 1)

        assert result is True

        mock_driver.find_element.assert_called_once()
        mock_driver.execute_script.assert_called_once_with(
            "arguments[0].click();", mock_next_button
        )

        mock_sleep.assert_called_once()


class TestErrorRecoveryAndResilience:
    """Test error handling and recovery mechanisms."""

    @pytest.fixture
    def mock_driver(self):
        """Create a mock driver for testing."""
        return Mock(spec=webdriver.Chrome)

    @patch("ECI_initiatives.scraper.downloader.logger")
    def test_individual_page_download_failure_handling(
        self, mock_logger, mock_driver, tmp_path
    ):
        """Test behavior when individual initiative pages fail to download."""

        # Simulate a WebDriver exception during page load
        mock_driver.get.side_effect = WebDriverException("Connection failed")

        url = f"{BASE_URL}/initiatives/details/2024/000001_en"

        result = download_single_initiative(
            mock_driver, str(tmp_path), url, max_retries=1
        )

        assert result is False
        mock_driver.get.assert_called_with(url)

    @patch("ECI_initiatives.scraper.downloader.logger")
    @patch("ECI_initiatives.scraper.downloader.download_single_initiative")
    @patch("ECI_initiatives.scraper.downloader.initialize_browser")
    @patch("ECI_initiatives.scraper.downloader.time.sleep")
    @patch("ECI_initiatives.scraper.downloader.random.uniform", return_value=1.0)
    def test_failed_downloads_recorded_properly(
        self, mock_uniform, mock_sleep, mock_init_browser, mock_download, mock_logger
    ):
        """Verify that failed downloads are properly recorded and reported."""

        mock_driver = Mock()
        mock_init_browser.return_value = mock_driver

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

        updated_data, failed_urls = download_initiative_pages("/tmp", test_data)

        assert len(failed_urls) == 2
        assert "http://test2.com" in failed_urls
        assert "http://test4.com" in failed_urls
        assert len(updated_data) == 4

    @patch("ECI_initiatives.scraper.downloader.logger")
    @patch("ECI_initiatives.scraper.downloader.time.sleep")
    @patch("ECI_initiatives.scraper.downloader.random.uniform", return_value=1.0)
    def test_rate_limiting_handling(self, mock_uniform, mock_sleep, mock_driver):
        """Check that rate limiting is handled gracefully with appropriate retries."""

        # Test rate limiting detection in page content
        mock_driver.page_source = f"<html><head><title>{RATE_LIMIT_INDICATORS.SERVER_INACCESSIBILITY}</title></head><body>{RATE_LIMIT_INDICATORS.TOO_MANY_REQUESTS}</body></html>"

        url = f"{FULL_FIND_INITIATIVE_URL}/details/2024/000001_en"

        with patch(
            "ECI_initiatives.scraper.downloader.check_rate_limiting"
        ) as mock_check:
            mock_check.side_effect = Exception(
                f"{RATE_LIMIT_INDICATORS.RATE_LIMITED} (HTML response)"
            )

            result = download_single_initiative(mock_driver, "/tmp", url, max_retries=1)
            assert result is False

    @patch("ECI_initiatives.scraper.crawler.logger")
    def test_continues_after_non_critical_errors(self, mock_driver):
        """Ensure scraping continues after encountering non-critical errors."""

        # Test that timeout on waiting for elements doesn't stop the process
        with patch("ECI_initiatives.scraper.crawler.WebDriverWait") as mock_wait:

            mock_wait.return_value.until.side_effect = TimeoutException()

            # This should not raise an exception, just log a warning
            wait_for_listing_page_content(mock_driver, 1)

            # The method should complete without raising an exception
            assert True

    @patch("ECI_initiatives.scraper.downloader.logger")
    @patch("ECI_initiatives.scraper.downloader.time.sleep")
    def test_retry_logic_for_failed_requests(self, mock_sleep, mock_driver, tmp_path):
        """Test the retry mechanism for failed requests."""

        # First two calls fail with rate limiting, third succeeds
        mock_driver.get.side_effect = [
            Exception(RATE_LIMIT_INDICATORS.TOO_MANY_REQUESTS),
            Exception(RATE_LIMIT_INDICATORS.RATE_LIMITED),
            None,  # Success
        ]
        mock_driver.page_source = "<html><body>Success</body></html>"

        with patch("ECI_initiatives.scraper.downloader.check_rate_limiting"):

            with patch("ECI_initiatives.scraper.downloader.wait_for_page_content"):

                with patch(
                    "ECI_initiatives.scraper.downloader.save_initiative_page",
                    return_value="test.html",
                ):
                    url = "https://test.com/details/2024/000001_en"

                    result = download_single_initiative(
                        mock_driver, str(tmp_path), url, max_retries=3
                    )

        assert result is True
        assert mock_driver.get.call_count == 3  # Two failed attempts, one success


class TestScrapingProcessFlow:
    """Test overall scraping process flow."""

    @pytest.fixture
    def mock_driver(self):
        """Create a mock driver for testing."""

        return Mock(spec=webdriver.Chrome)

    @patch("ECI_initiatives.scraper.crawler.logger")
    @patch("ECI_initiatives.scraper.crawler.WebDriverWait")
    def test_wait_for_listing_page_content(
        self, mock_wait_class, mock_logger, mock_driver
    ):
        """Test waiting for listing page content to load."""

        mock_wait = Mock()
        mock_wait_class.return_value = mock_wait

        # Test successful wait
        wait_for_listing_page_content(mock_driver, 1)

        mock_wait_class.assert_called_with(mock_driver, DEFAULT_WEBDRIVER_TIMEOUT)
        mock_wait.until.assert_called_once()

    @patch("ECI_initiatives.scraper.downloader.logger")
    @patch("ECI_initiatives.scraper.downloader.WebDriverWait")
    def test_wait_for_page_content(self, mock_wait_class, mock_logger, mock_driver):
        """Test waiting for individual page content to load."""

        mock_wait = Mock()
        mock_wait_class.return_value = mock_wait
        # Simulate successful wait for first selector, others fail
        mock_wait.until.side_effect = [None, TimeoutException(), TimeoutException()]

        wait_for_page_content(mock_driver)

        mock_wait_class.assert_called_with(mock_driver, PAGE_CONTENT_TIMEOUT)
        # Should be called multiple times as it tries different selectors
        assert mock_wait.until.call_count >= 1

    def test_check_rate_limiting_detection(self, mock_driver):
        """Test rate limiting detection functionality."""

        # Test case: Rate limiting detected
        mock_element = Mock()
        mock_element.text = f"{RATE_LIMIT_INDICATORS.SERVER_INACCESSIBILITY} - 429"
        mock_driver.find_element.return_value = mock_element

        with pytest.raises(Exception, match=RATE_LIMIT_INDICATORS.RATE_LIMITED):
            check_rate_limiting(mock_driver)

        # Test case: No rate limiting
        mock_element.text = "Normal page content"
        check_rate_limiting(mock_driver)  # Should not raise

    @patch("ECI_initiatives.scraper.crawler.parse_initiatives_list_data")
    @patch("ECI_initiatives.scraper.crawler.save_listing_page")
    @patch("ECI_initiatives.scraper.crawler.wait_for_listing_page_content")
    def test_scrape_single_listing_page(
        self, mock_wait, mock_save, mock_parse, mock_driver
    ):
        """Test scraping a single listing page."""

        # Setup mocks
        mock_save.return_value = ("page_source", "/path/to/page.html")
        mock_parse.return_value = [
            SAMPLE_INITIATIVE_DATA | {REQUIRED_CSV_COLUMNS.URL: "test1.com"},
            SAMPLE_INITIATIVE_DATA | {REQUIRED_CSV_COLUMNS.URL: "test2.com"},
        ]

        base_url = BASE_URL
        list_dir = "/test/dir"
        current_page = 1

        page_data, page_path = scrape_single_listing_page(
            mock_driver, base_url, list_dir, current_page
        )

        # Verify all functions were called
        mock_wait.assert_called_once_with(mock_driver, current_page)
        mock_save.assert_called_once_with(mock_driver, list_dir, current_page)
        mock_parse.assert_called_once_with("page_source", base_url)

        # Verify return values
        assert len(page_data) == 2
        assert page_path == "/path/to/page.html"

    @patch("ECI_initiatives.scraper.crawler.logger")
    @patch("ECI_initiatives.scraper.crawler.navigate_to_next_page")
    @patch("ECI_initiatives.scraper.crawler.scrape_single_listing_page")
    def test_scrape_all_initiatives_on_all_pages(
        self, mock_scrape_single, mock_navigate, mock_logger
    ):
        """Test scraping all initiatives across all pages."""

        mock_driver = Mock()

        # Mock scraping single page to return different data for each page
        mock_scrape_single.side_effect = [
            (
                [
                    SAMPLE_INITIATIVE_DATA | {REQUIRED_CSV_COLUMNS.URL: "page1_init1"},
                    SAMPLE_INITIATIVE_DATA | {REQUIRED_CSV_COLUMNS.URL: "page1_init2"},
                ],
                "/path/page1.html",
            ),
            (
                [SAMPLE_INITIATIVE_DATA | {REQUIRED_CSV_COLUMNS.URL: "page2_init1"}],
                "/path/page2.html",
            ),
            (
                [
                    SAMPLE_INITIATIVE_DATA | {REQUIRED_CSV_COLUMNS.URL: "page3_init1"},
                    SAMPLE_INITIATIVE_DATA | {REQUIRED_CSV_COLUMNS.URL: "page3_init2"},
                    SAMPLE_INITIATIVE_DATA | {REQUIRED_CSV_COLUMNS.URL: "page3_init3"},
                ],
                "/path/page3.html",
            ),
        ]

        # Mock navigation: True for first 2 pages, False for last page
        mock_navigate.side_effect = [True, True, False]

        all_data, saved_paths = scrape_all_initiatives_on_all_pages(
            mock_driver, "https://base.url", "/list/dir"
        )

        # Verify results
        assert len(all_data) == 6  # 2 + 1 + 3 initiatives total
        assert len(saved_paths) == 3  # 3 pages scraped

        # Verify navigation was attempted 3 times
        assert mock_navigate.call_count == 3

        # Verify single page scraping was called 3 times
        assert mock_scrape_single.call_count == 3


class TestDataParsing:
    """Test data parsing functionality."""

    @patch("ECI_initiatives.scraper.data_parser.logger")
    def test_parse_initiatives_with_real_data(self, mock_logger):
        """
        This test specifically uses actual saved HTML files from the ECI website rather
        than mocked or synthetic data
        """

        test_dir = os.path.join(
            os.path.dirname(__file__), "..", "..", "data", "example_htmls", "listings"
        )
        first_page_path = os.path.join(test_dir, "first_page.html")

        if os.path.exists(first_page_path):

            with open(first_page_path, "r", encoding="utf-8") as f:
                html_content = f.read()

            base_url = "https://citizens-initiative.europa.eu"
            initiatives = parse_initiatives_list_data(html_content, base_url)

            # Basic validation - should find some initiatives
            assert isinstance(initiatives, list)

            if initiatives:  # If HTML contains valid initiative data

                for initiative in initiatives:

                    assert REQUIRED_CSV_COLUMNS.URL in initiative
                    assert REQUIRED_CSV_COLUMNS.CURRENT_STATUS in initiative
                    assert initiative[REQUIRED_CSV_COLUMNS.URL].startswith(base_url)
