"""Tests for scraping process behavior and flow."""

import pytest
import os
import csv
import time

from unittest.mock import Mock, patch, MagicMock, call

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    WebDriverException,
)

from bs4 import BeautifulSoup

# Import the functions we want to test
import sys

program_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")

print(program_dir)
sys.path.append(program_dir)

from ECI_initiatives.__main__ import (
    navigate_to_next_page,
    wait_for_listing_page_content,
    wait_for_page_content,
    check_rate_limiting,
    scrape_single_listing_page,
    scrape_all_initiatives_on_all_pages,
    save_listing_page,
    parse_initiatives_list_data,
    download_single_initiative,
    save_initiative_page,
    initialize_browser,
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
        first_page_path = os.path.join(test_dir, "first_page.html")

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
        last_page_path = os.path.join(test_dir, "last_page.html")

        if os.path.exists(last_page_path):
            with open(last_page_path, "r", encoding="utf-8") as f:
                return f.read()
        return '<html><body><div class="card">Last page content</div></body></html>'

    @patch("ECI_initiatives.__main__.logger")
    @patch("ECI_initiatives.__main__.time.sleep")
    @patch("ECI_initiatives.__main__.random.uniform", return_value=1.0)
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

    @patch("ECI_initiatives.__main__.logger")
    def test_stops_at_last_page(self, mock_logger, mock_driver):
        """Verify that scraping stops correctly when reaching the last page."""

        # Simulate no next button found (last page scenario)
        mock_driver.find_element.side_effect = NoSuchElementException()

        result = navigate_to_next_page(mock_driver, 5)
        assert result is False

        # Ensure execute_script was not called since no button was found
        mock_driver.execute_script.assert_not_called()

    @patch("ECI_initiatives.__main__.logger")
    @patch("ECI_initiatives.__main__.time.sleep")
    @patch("ECI_initiatives.__main__.random.uniform", return_value=1.0)
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

            expected_filename = (
                f"Find_initiative_European_Citizens_Initiative_page_{page_num:03d}.html"
            )
            assert expected_filename in page_path
            assert os.path.exists(page_path)

    @patch("ECI_initiatives.__main__.logger")
    @patch(
        "ECI_initiatives.__main__.parse_initiatives_list_data",
        return_value=[{"url": "test", "status": "active"}],
    )
    @patch("ECI_initiatives.__main__.wait_for_listing_page_content")
    @patch("ECI_initiatives.__main__.save_listing_page")
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
            "ECI_initiatives.__main__.navigate_to_next_page",
            side_effect=[True, True, False],
        ):
            all_data, saved_paths = scrape_all_initiatives_on_all_pages(
                mock_driver, "http://base.url", "/test/dir"
            )

        # Verify all 3 pages were processed
        assert len(saved_paths) == 3
        assert len(all_data) == 3  # Each page returns 1 initiative
        assert mock_save.call_count == 3

    @patch("ECI_initiatives.__main__.logger")
    @patch("ECI_initiatives.__main__.time.sleep")
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

    @patch("ECI_initiatives.__main__.logger")
    def test_individual_page_download_failure_handling(
        self, mock_logger, mock_driver, tmp_path
    ):
        """Test behavior when individual initiative pages fail to download."""

        # Simulate a WebDriver exception during page load
        mock_driver.get.side_effect = WebDriverException("Connection failed")

        url = "https://citizens-initiative.europa.eu/initiatives/details/2024/000001_en"

        result = download_single_initiative(
            mock_driver, str(tmp_path), url, max_retries=1
        )

        assert result is False
        mock_driver.get.assert_called_with(url)

    @patch("ECI_initiatives.__main__.logger")
    @patch("ECI_initiatives.__main__.download_single_initiative")
    @patch("ECI_initiatives.__main__.initialize_browser")
    @patch("ECI_initiatives.__main__.time.sleep")
    @patch("ECI_initiatives.__main__.random.uniform", return_value=1.0)
    def test_failed_downloads_recorded_properly(
        self, mock_uniform, mock_sleep, mock_init_browser, mock_download, mock_logger
    ):
        """Verify that failed downloads are properly recorded and reported."""

        from ECI_initiatives.__main__ import download_initiative_pages

        mock_driver = Mock()
        mock_init_browser.return_value = mock_driver

        # Simulate some successful and some failed downloads
        mock_download.side_effect = [True, False, True, False]

        test_data = [
            {"url": "http://test1.com", "status": "active"},
            {"url": "http://test2.com", "status": "active"},
            {"url": "http://test3.com", "status": "active"},
            {"url": "http://test4.com", "status": "active"},
        ]

        updated_data, failed_urls = download_initiative_pages("/tmp", test_data)

        assert len(failed_urls) == 2
        assert "http://test2.com" in failed_urls
        assert "http://test4.com" in failed_urls
        assert len(updated_data) == 4

    @patch("ECI_initiatives.__main__.logger")
    @patch("ECI_initiatives.__main__.time.sleep")
    @patch("ECI_initiatives.__main__.random.uniform", return_value=1.0)
    def test_rate_limiting_handling(self, mock_uniform, mock_sleep, mock_driver):
        """Check that rate limiting is handled gracefully with appropriate retries."""

        # Test rate limiting detection in page content
        mock_driver.page_source = "<html><head><title>Server inaccessibility</title></head><body>429 - Too Many Requests</body></html>"

        url = "https://citizens-initiative.europa.eu/initiatives/details/2024/000001_en"

        with patch("ECI_initiatives.__main__.check_rate_limiting") as mock_check:
            mock_check.side_effect = Exception("429 - Rate limited (HTML response)")

            result = download_single_initiative(mock_driver, "/tmp", url, max_retries=1)
            assert result is False

    @patch("ECI_initiatives.__main__.logger")
    def test_continues_after_non_critical_errors(self, mock_driver):
        """Ensure scraping continues after encountering non-critical errors."""

        # Test that timeout on waiting for elements doesn't stop the process
        with patch("ECI_initiatives.__main__.WebDriverWait") as mock_wait:

            mock_wait.return_value.until.side_effect = TimeoutException()

            # This should not raise an exception, just log a warning
            wait_for_listing_page_content(mock_driver, 1)

            # The method should complete without raising an exception
            assert True

    @patch("ECI_initiatives.__main__.logger")
    @patch("ECI_initiatives.__main__.time.sleep")
    def test_retry_logic_for_failed_requests(self, mock_sleep, mock_driver, tmp_path):
        """Test the retry mechanism for failed requests."""

        # First two calls fail with rate limiting, third succeeds
        mock_driver.get.side_effect = [
            Exception("429 - Too Many Requests"),
            Exception("429 - Rate limited"),
            None,  # Success
        ]
        mock_driver.page_source = "<html><body>Success</body></html>"

        with patch("ECI_initiatives.__main__.check_rate_limiting"):

            with patch("ECI_initiatives.__main__.wait_for_page_content"):

                with patch(
                    "ECI_initiatives.__main__.save_initiative_page",
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

    @patch("ECI_initiatives.__main__.logger")
    @patch("ECI_initiatives.__main__.WebDriverWait")
    def test_wait_for_listing_page_content(
        self, mock_wait_class, mock_logger, mock_driver
    ):
        """Test waiting for listing page content to load."""
        mock_wait = Mock()
        mock_wait_class.return_value = mock_wait

        # Test successful wait
        wait_for_listing_page_content(mock_driver, 1)

        mock_wait_class.assert_called_with(mock_driver, 30)
        mock_wait.until.assert_called_once()

    @patch("ECI_initiatives.__main__.logger")
    @patch("ECI_initiatives.__main__.WebDriverWait")
    def test_wait_for_page_content(self, mock_wait_class, mock_logger, mock_driver):
        """Test waiting for individual page content to load."""
        mock_wait = Mock()
        mock_wait_class.return_value = mock_wait
        # Simulate successful wait for first selector, others fail
        mock_wait.until.side_effect = [None, TimeoutException(), TimeoutException()]

        wait_for_page_content(mock_driver)

        mock_wait_class.assert_called_with(mock_driver, 15)
        # Should be called multiple times as it tries different selectors
        assert mock_wait.until.call_count >= 1

    def test_check_rate_limiting_detection(self, mock_driver):
        """Test rate limiting detection functionality."""

        # Test case: Rate limiting detected
        mock_element = Mock()
        mock_element.text = "Server inaccessibility - 429"
        mock_driver.find_element.return_value = mock_element

        with pytest.raises(Exception, match="429 - Rate limited"):
            check_rate_limiting(mock_driver)

        # Test case: No rate limiting
        mock_element.text = "Normal page content"
        check_rate_limiting(mock_driver)  # Should not raise

    @patch("ECI_initiatives.__main__.parse_initiatives_list_data")
    @patch("ECI_initiatives.__main__.save_listing_page")
    @patch("ECI_initiatives.__main__.wait_for_listing_page_content")
    def test_scrape_single_listing_page(
        self, mock_wait, mock_save, mock_parse, mock_driver
    ):
        """Test scraping a single listing page."""

        # Setup mocks
        mock_save.return_value = ("page_source", "/path/to/page.html")
        mock_parse.return_value = [{"url": "test1.com"}, {"url": "test2.com"}]

        base_url = "https://citizens-initiative.europa.eu"
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

    @patch("ECI_initiatives.__main__.logger")
    @patch("ECI_initiatives.__main__.navigate_to_next_page")
    @patch("ECI_initiatives.__main__.scrape_single_listing_page")
    def test_scrape_all_initiatives_on_all_pages(
        self, mock_scrape_single, mock_navigate, mock_logger
    ):
        """Test scraping all initiatives across all pages."""

        mock_driver = Mock()

        # Mock scraping single page to return different data for each page
        mock_scrape_single.side_effect = [
            ([{"url": "page1_init1"}, {"url": "page1_init2"}], "/path/page1.html"),
            ([{"url": "page2_init1"}], "/path/page2.html"),
            (
                [
                    {"url": "page3_init1"},
                    {"url": "page3_init2"},
                    {"url": "page3_init3"},
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


# TODO: not here
# Fixture for loading test data
# @pytest.fixture
# def test_data_csv():
#     """Load test data from CSV file."""

#     test_dir = os.path.join(
#         os.path.dirname(__file__), "..", "..", "data", "example_htmls", "initiatives"
#     )
#     csv_path = os.path.join(test_dir, "eci_status_initiatives.csv")

#     if os.path.exists(csv_path):

#         with open(csv_path, "r", encoding="utf-8") as f:
#             reader = csv.DictReader(f)
#             return list(reader)

#     return []


@patch("ECI_initiatives.__main__.logger")
def test_parse_initiatives_with_real_data(mock_logger):
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

                assert "url" in initiative
                assert "current_status" in initiative
                assert initiative["url"].startswith(base_url)
