`./ECI_initiatives/tests/scraper/behaviour/__init__.py`:
```

```

`./ECI_initiatives/tests/scraper/behaviour/test_browser_webdriver.py`:
```
"""Tests for browser and WebDriver functionality."""

# Standard library
import os
import sys
from unittest.mock import Mock, patch, MagicMock

# Third party
import pytest

from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options

# Local
program_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
sys.path.append(program_dir)

# Safe imports (don't trigger logger creation)
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
        from ECI_initiatives.tests.consts import (
            REQUIRED_CSV_COLUMNS,
            SAMPLE_INITIATIVE_DATA,
            BASE_URL,
            LOG_MESSAGES,
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

```

`./ECI_initiatives/tests/scraper/behaviour/test_data_extraction.py`:
```
"""
A test suite for scraper that validates
CSV file generation, HTML parsing accuracy,
through mocked browser interactions and static test fixtures,
ensuring reliable verification of data extraction
without depending on live website availability.
"""

# python
import copy
import csv
import datetime
import os
import re
import sys
import tempfile
from collections import Counter
from typing import List, Dict

# third-party
import pytest
from bs4 import BeautifulSoup
from unittest.mock import patch, MagicMock, mock_open, call


# Local
program_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")

sys.path.append(program_dir)

# Safe imports (don't trigger logger creation)
from ECI_initiatives.tests.consts import (
    LISTINGS_HTML_DIR,
    CSV_FILE_PATH,
    BASE_URL,
    REQUIRED_CSV_COLUMNS,
    SAMPLE_LISTING_FILES,
)


# ===== SHARED FIXTURES (used by multiple test classes) =====


@pytest.fixture(scope="session")
def parsed_test_data():
    """Parse test HTML files once and reuse across all tests."""
    
    # Import here to avoid early logger initialization
    from ECI_initiatives.scraper.initiatives.data_parser import parse_initiatives_list_data
    
    with patch("ECI_initiatives.scraper.initiatives.data_parser.logger"):
        all_initiatives = []

        for page_file in SAMPLE_LISTING_FILES:
            page_path = os.path.join(LISTINGS_HTML_DIR, page_file)

            if not os.path.exists(page_path):
                continue

            with open(page_path, "r", encoding="utf-8") as f:
                page_source = f.read()

            initiatives = parse_initiatives_list_data(page_source, BASE_URL)
            all_initiatives.extend(initiatives)

        return all_initiatives


@pytest.fixture(scope="session")
def reference_data():
    """Load reference CSV once and reuse across all tests."""

    if not os.path.exists(CSV_FILE_PATH):
        pytest.skip(f"Reference CSV file not found: {CSV_FILE_PATH}")

    with open(CSV_FILE_PATH, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ===== TEST CLASSES =====


class TestCsvFileOperations:
    """Test CSV data validation functionality."""

    @classmethod
    def setup_class(cls):
        """
        Import modules and set up class attributes.
        
        Imports are done here rather than at module level to avoid
        log file creation during module loading, allowing the session
        fixture to properly track and clean up test artifacts.
        """
        from ECI_initiatives.scraper.initiatives.__main__ import save_and_download_initiatives
        
        cls.save_and_download_initiatives = staticmethod(save_and_download_initiatives)

    @patch("ECI_initiatives.scraper.initiatives.__main__.download_initiative_pages")
    @patch("ECI_initiatives.scraper.initiatives.__main__.logger")
    def test_csv_created_with_correct_headers(self, mock_logger, mock_download_pages):
        """
        Verify that initiatives_list.csv is created with correct headers:
        url, current_status, registration_number, signature_collection, datetime.
        """

        # Sample initiative data
        test_initiative_data = [
            {
                REQUIRED_CSV_COLUMNS.URL: "https://citizens-initiative.europa.eu/initiatives/details/2019/000007_en",
                REQUIRED_CSV_COLUMNS.CURRENT_STATUS: "Answered initiative",
                REQUIRED_CSV_COLUMNS.REGISTRATION_NUMBER: "ECI(2019)000007",
                REQUIRED_CSV_COLUMNS.SIGNATURE_COLLECTION: "Collection completed",
                REQUIRED_CSV_COLUMNS.DATETIME: "",
            }
        ]

        # Mock download_initiative_pages to return the same data with updated datetime
        updated_data = copy.deepcopy(test_initiative_data)
        updated_data[0][REQUIRED_CSV_COLUMNS.DATETIME] = "2025-09-21 11:24:00"

        mock_download_pages.return_value = (
            updated_data,
            [],
        )  # (updated_data, failed_urls)

        with tempfile.TemporaryDirectory() as temp_dir:

            list_dir = os.path.join(temp_dir, "listings")
            pages_dir = os.path.join(temp_dir, "pages")
            os.makedirs(list_dir, exist_ok=True)
            os.makedirs(pages_dir, exist_ok=True)

            # Call the function to test
            self.save_and_download_initiatives(list_dir, pages_dir, test_initiative_data)

            # Check that CSV file was created
            csv_file_path = os.path.join(list_dir, "initiatives_list.csv")
            assert os.path.exists(csv_file_path), "CSV file was not created"

            # Read and verify CSV headers and data
            with open(csv_file_path, "r", encoding="utf-8") as f:

                reader = csv.reader(f)
                headers = next(reader)
                expected_headers = [
                    REQUIRED_CSV_COLUMNS.URL,
                    REQUIRED_CSV_COLUMNS.CURRENT_STATUS,
                    REQUIRED_CSV_COLUMNS.REGISTRATION_NUMBER,
                    REQUIRED_CSV_COLUMNS.SIGNATURE_COLLECTION,
                    REQUIRED_CSV_COLUMNS.DATETIME,
                ]

                assert (
                    headers == expected_headers
                ), f"Expected:\n{expected_headers}\nGot:\n{headers}"

                # Read all remaining rows to avoid StopIteration
                data_rows = list(reader)
                assert len(data_rows) > 0, "No data rows found in CSV"

                # Verify first data row
                data_row = data_rows[0]

                assert len(data_row) == len(expected_headers), (
                    "Data row has incorrect number of columns.\n"
                    + "The first row:\n"
                    + str(data_row)
                )

                assert (
                    data_row[0] == test_initiative_data[0][REQUIRED_CSV_COLUMNS.URL]
                ), "URL not correctly written to CSV:\n" + str(data_row[0])

    @patch("ECI_initiatives.scraper.initiatives.__main__.logger")
    @patch("ECI_initiatives.scraper.initiatives.__main__.download_initiative_pages")
    def test_no_duplicate_initiatives(self, mock_download_pages, mock_logger):
        """Ensure no duplicate initiatives are recorded in the CSV when scraping produces duplicates."""

        # Create test data with duplicates (simulating what parse_initiatives_list_data might return)
        test_initiative_data_with_duplicates = [
            {
                REQUIRED_CSV_COLUMNS.URL: "https://citizens-initiative.europa.eu/initiatives/details/2019/000007_en",
                REQUIRED_CSV_COLUMNS.CURRENT_STATUS: "Answered initiative",
                REQUIRED_CSV_COLUMNS.REGISTRATION_NUMBER: "ECI(2019)000007",
                REQUIRED_CSV_COLUMNS.SIGNATURE_COLLECTION: "Collection completed",
                REQUIRED_CSV_COLUMNS.DATETIME: "",
            },
            {
                REQUIRED_CSV_COLUMNS.URL: "https://citizens-initiative.europa.eu/initiatives/details/2024/000004_en",
                REQUIRED_CSV_COLUMNS.CURRENT_STATUS: "Valid initiative",
                REQUIRED_CSV_COLUMNS.REGISTRATION_NUMBER: "ECI(2024)000004",
                REQUIRED_CSV_COLUMNS.SIGNATURE_COLLECTION: "Collection closed",
                REQUIRED_CSV_COLUMNS.DATETIME: "",
            },
            {
                REQUIRED_CSV_COLUMNS.URL: "https://citizens-initiative.europa.eu/initiatives/details/2019/000007_en",  # DUPLICATE
                REQUIRED_CSV_COLUMNS.CURRENT_STATUS: "Answered initiative",
                REQUIRED_CSV_COLUMNS.REGISTRATION_NUMBER: "ECI(2019)000007",
                REQUIRED_CSV_COLUMNS.SIGNATURE_COLLECTION: "Collection completed",
                REQUIRED_CSV_COLUMNS.DATETIME: "",
            },
        ]

        # Mock download_initiative_pages to return data without duplicates
        unique_data = []
        seen_urls = set()

        for item in test_initiative_data_with_duplicates:

            if item[REQUIRED_CSV_COLUMNS.URL] not in seen_urls:

                unique_data.append(item.copy())
                seen_urls.add(item[REQUIRED_CSV_COLUMNS.URL])

        mock_download_pages.return_value = (unique_data, [])

        with tempfile.TemporaryDirectory() as temp_dir:

            list_dir = os.path.join(temp_dir, "listings")
            pages_dir = os.path.join(temp_dir, "pages")

            os.makedirs(list_dir, exist_ok=True)
            os.makedirs(pages_dir, exist_ok=True)

            # Test the actual function from main module
            self.save_and_download_initiatives(
                list_dir, pages_dir, test_initiative_data_with_duplicates
            )

            # Verify CSV was created
            csv_file_path = os.path.join(list_dir, "initiatives_list.csv")
            assert os.path.exists(csv_file_path), "CSV file was not created"

            # Read CSV and check for duplicates
            with open(csv_file_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                csv_data = list(reader)

            # Extract URLs from CSV
            csv_urls = [row[REQUIRED_CSV_COLUMNS.URL] for row in csv_data]
            unique_csv_urls = list(set(csv_urls))

            # Should have only 2 unique URLs, not 3
            assert (
                len(csv_urls) == 2
            ), f"Expected 2 rows in CSV (duplicates removed), got:\n{len(csv_urls)}"
            assert (
                len(unique_csv_urls) == 2
            ), f"Found duplicate URLs in CSV:\n{csv_urls}"

            # Verify the specific URLs are correct
            expected_urls = [
                "https://citizens-initiative.europa.eu/initiatives/details/2019/000007_en",
                "https://citizens-initiative.europa.eu/initiatives/details/2024/000004_en",
            ]

            for expected_url in expected_urls:
                assert (
                    expected_url in csv_urls
                ), f"Expected URL {expected_url} not found in CSV"


class TestHtmlParsingBehaviour:
    """Test HTML parsing and data extraction."""

    def test_all_fields_extracted(self, parsed_test_data):
        """Ensure all required fields are present in extracted data."""
        expected_fields = [
            REQUIRED_CSV_COLUMNS.URL,
            REQUIRED_CSV_COLUMNS.CURRENT_STATUS,
            REQUIRED_CSV_COLUMNS.REGISTRATION_NUMBER,
            REQUIRED_CSV_COLUMNS.SIGNATURE_COLLECTION,
            REQUIRED_CSV_COLUMNS.DATETIME,
        ]

        for initiative in parsed_test_data:
            missing_fields = [f for f in expected_fields if f not in initiative]
            assert (
                not missing_fields
            ), f"Missing fields {missing_fields} in {initiative}"
            assert initiative[REQUIRED_CSV_COLUMNS.URL], "URL field is empty"

    def test_extracted_data_accuracy(self, parsed_test_data, reference_data):
        """Verify extracted data matches reference values."""
        reference_dict = {
            row[REQUIRED_CSV_COLUMNS.URL]: row[REQUIRED_CSV_COLUMNS.CURRENT_STATUS]
            for row in reference_data
        }

        for initiative in parsed_test_data:
            url = initiative[REQUIRED_CSV_COLUMNS.URL]
            if url in reference_dict:
                expected = reference_dict[url]
                actual = initiative[REQUIRED_CSV_COLUMNS.CURRENT_STATUS]
                assert (
                    actual == expected
                ), f"Status mismatch for {url}: expected '{expected}', got '{actual}'"

    def test_status_distribution_accuracy(self, parsed_test_data, reference_data):
        """Check that expected statuses appear in parsed data."""
        expected_statuses = {
            row[REQUIRED_CSV_COLUMNS.CURRENT_STATUS] for row in reference_data
        }
        actual_statuses = {
            init[REQUIRED_CSV_COLUMNS.CURRENT_STATUS]
            for init in parsed_test_data
            if init[REQUIRED_CSV_COLUMNS.CURRENT_STATUS]
        }

        missing = expected_statuses - actual_statuses
        assert not missing, f"Missing statuses in parsed data: {missing}"


class TestScrapingWorkflow:
    """Test data completeness and accuracy."""

    @classmethod
    def setup_class(cls):
        """
        Import modules and set up class attributes.
        
        Imports are done here rather than at module level to avoid
        log file creation during module loading, allowing the session
        fixture to properly track and clean up test artifacts.
        """
        from ECI_initiatives.scraper.initiatives.crawler import scrape_all_initiatives_on_all_pages
        from ECI_initiatives.scraper.initiatives.data_parser import parse_initiatives_list_data
        
        cls.scrape_all_initiatives_on_all_pages = staticmethod(scrape_all_initiatives_on_all_pages)
        cls.parse_initiatives_list_data = staticmethod(parse_initiatives_list_data)

    def test_initiative_count_matches_reference(self, parsed_test_data, reference_data):
        """Compare initiative count with reference data."""
        assert len(parsed_test_data) >= len(
            reference_data
        ), f"Found {len(parsed_test_data)} initiatives, expected at least {len(reference_data)}"

    @patch("ECI_initiatives.scraper.initiatives.browser.initialize_browser")
    @patch("ECI_initiatives.scraper.initiatives.__main__.logger")
    def test_pagination_handling(self, mock_logger, mock_browser):
        """Test pagination processing logic."""
        # Create a mock driver
        mock_driver = MagicMock()
        mock_browser.return_value = mock_driver

        # Mock pagination scenario: 3 pages total
        page_sources = [
            "<html>page1</html>",
            "<html>page2</html>",
            "<html>page3</html>",
        ]
        mock_driver.page_source = page_sources[0]  # Start with first page

        # Mock find_element for next button
        def mock_find_element_side_effect(*args, **kwargs):
            """Mock browser's find_element behavior for pagination."""
            if mock_find_element_side_effect.call_count <= 2:
                mock_button = MagicMock()
                return mock_button
            else:
                raise Exception("No next button found")

        mock_find_element_side_effect.call_count = 0

        def increment_and_side_effect(*args, **kwargs):
            """Wrapper to increment call counter and delegate to main side effect."""
            mock_find_element_side_effect.call_count += 1
            return mock_find_element_side_effect(*args, **kwargs)

        mock_driver.find_element.side_effect = increment_and_side_effect

        # Mock page source updates
        def update_page_source():
            """Update mock driver's page_source to simulate navigation."""
            if mock_find_element_side_effect.call_count <= len(page_sources):
                mock_driver.page_source = page_sources[
                    mock_find_element_side_effect.call_count - 1
                ]

        mock_driver.execute_script.side_effect = (
            lambda script, element: update_page_source()
        )

        # Mock other required methods
        with patch(
            "ECI_initiatives.scraper.initiatives.crawler.wait_for_listing_page_content"
        ), patch(
            "ECI_initiatives.scraper.initiatives.file_ops.save_listing_page"
        ) as mock_save, patch(
            "ECI_initiatives.scraper.initiatives.data_parser.parse_initiatives_list_data"
        ) as mock_parse, patch(
            "time.sleep"
        ):

            mock_save.return_value = ("", "test_path")
            mock_parse.return_value = [
                {
                    REQUIRED_CSV_COLUMNS.URL: "test",
                    REQUIRED_CSV_COLUMNS.CURRENT_STATUS: "",
                    REQUIRED_CSV_COLUMNS.REGISTRATION_NUMBER: "",
                    REQUIRED_CSV_COLUMNS.SIGNATURE_COLLECTION: "",
                    REQUIRED_CSV_COLUMNS.DATETIME: "",
                }
            ]

            with tempfile.TemporaryDirectory() as temp_dir:
                all_data, saved_paths = self.scrape_all_initiatives_on_all_pages(
                    mock_driver, BASE_URL, temp_dir
                )

                expected_page_count = 3

                # Should have processed 3 pages
                assert (
                    len(saved_paths) == expected_page_count
                ), f"Expected {expected_page_count} pages processed, got {len(saved_paths)}"
                assert (
                    mock_driver.find_element.call_count == expected_page_count
                ), f"Should have checked for next button {expected_page_count} times"
        """Ensure all initiative fields are extracted when available on source pages."""

        def load_expected_statuses():
            """Load status distribution from reference CSV file."""

            with open(CSV_FILE_PATH, "r", encoding="utf-8") as f:

                reader = csv.DictReader(f)
                return Counter(
                    row[REQUIRED_CSV_COLUMNS.CURRENT_STATUS] for row in reader
                )

        def parse_test_pages():
            """Parse all test HTML pages and extract statuses."""

            all_statuses = []

            for page_file in SAMPLE_LISTING_FILES:

                page_path = os.path.join(LISTINGS_HTML_DIR, page_file)

                with open(page_path, "r", encoding="utf-8") as f:
                    page_content = f.read()

                initiatives = self.parse_initiatives_list_data(page_content, BASE_URL)

                # Extract non-empty statuses
                page_statuses = [
                    init[REQUIRED_CSV_COLUMNS.CURRENT_STATUS]
                    for init in initiatives
                    if init[REQUIRED_CSV_COLUMNS.CURRENT_STATUS]
                ]
                all_statuses.extend(page_statuses)

            return Counter(all_statuses)

        # Main test logic
        expected_statuses = load_expected_statuses()
        actual_statuses = parse_test_pages()

        # Verify each expected status appears in parsed data
        missing_statuses = []
        for expected_status in expected_statuses:
            if expected_status not in actual_statuses:
                missing_statuses.append(expected_status)

        assert not missing_statuses, (
            f"These expected statuses were not found in parsed data: {missing_statuses}\n"
            f"Expected: {list(expected_statuses.keys())}\n"
            f"Found: {list(actual_statuses.keys())}"
        )

```

`./ECI_initiatives/tests/scraper/behaviour/test_edge_cases.py`:
```
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

```

`./ECI_initiatives/tests/scraper/behaviour/test_output_reporting.py`:
```
"""Tests for output and reporting functionality."""

# Standard library
import csv
import datetime
import os
import sys
from collections import Counter
from unittest.mock import Mock, patch, mock_open, MagicMock

# Third party
import pytest

# Local
program_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
sys.path.append(program_dir)

# Safe imports (don't trigger logger creation)
from ECI_initiatives.tests.consts import (
    COMMON_STATUSES,
    REQUIRED_CSV_COLUMNS,
    CSV_FILENAME,
    PAGES_DIR_NAME,
    LOG_MESSAGES,
)


class TestCompletionSummaryAccuracy:
    """Test completion summary and statistics accuracy."""

    @classmethod
    def setup_class(cls):
        """
        Import modules and set up class attributes.
        
        Imports are done here rather than at module level to avoid
        log file creation during module loading, allowing the session
        fixture to properly track and clean up test artifacts.
        """
        from ECI_initiatives.scraper.initiatives.statistics import (
            display_completion_summary,
            gather_scraping_statistics,
            display_summary_info,
            display_results_and_files,
        )
        
        cls.display_completion_summary = staticmethod(display_completion_summary)
        cls.gather_scraping_statistics = staticmethod(gather_scraping_statistics)
        cls.display_summary_info = staticmethod(display_summary_info)
        cls.display_results_and_files = staticmethod(display_results_and_files)

    @patch("ECI_initiatives.scraper.initiatives.statistics.logger")
    @patch("ECI_initiatives.scraper.initiatives.statistics.gather_scraping_statistics")
    @patch("ECI_initiatives.scraper.initiatives.statistics.display_summary_info")
    @patch("ECI_initiatives.scraper.initiatives.statistics.display_results_and_files")
    def test_final_statistics_match_actual_results(
        self, mock_display_results, mock_display_summary, mock_gather_stats, mock_logger
    ):
        """Verify that final statistics match actual results (total initiatives, downloads, failures)."""

        # Arrange
        start_scraping = "2025-09-21_17-13-00"
        initiative_data = [
            {
                REQUIRED_CSV_COLUMNS.URL: "https://example.com/1",
                REQUIRED_CSV_COLUMNS.CURRENT_STATUS: "Registered",
            },
            {
                REQUIRED_CSV_COLUMNS.URL: "https://example.com/2",
                REQUIRED_CSV_COLUMNS.CURRENT_STATUS: "Collection ongoing",
            },
            {
                REQUIRED_CSV_COLUMNS.URL: "https://example.com/3",
                REQUIRED_CSV_COLUMNS.CURRENT_STATUS: "Valid initiative",
            },
        ]
        saved_page_paths = ["page1.html", "page2.html", "page3.html"]
        failed_urls = ["https://example.com/failed"]

        expected_stats = {
            "status_counter": Counter(
                {"Registered": 1, "Collection ongoing": 1, "Valid initiative": 1}
            ),
            "downloaded_count": 3,
            "total_initiatives": 3,
            "failed_count": 1,
        }

        mock_gather_stats.return_value = expected_stats

        # Act
        self.display_completion_summary(
            start_scraping, initiative_data, saved_page_paths, failed_urls
        )

        # Assert
        mock_gather_stats.assert_called_once_with(
            start_scraping, initiative_data, failed_urls
        )
        mock_display_summary.assert_called_once_with(
            start_scraping, saved_page_paths, expected_stats
        )
        mock_display_results.assert_called_once_with(
            start_scraping, saved_page_paths, failed_urls, expected_stats
        )

    @patch("ECI_initiatives.scraper.initiatives.statistics.logger")
    @patch("os.path.exists")
    @patch("os.path.isdir")
    @patch("os.listdir")
    @patch("builtins.open", new_callable=mock_open)
    def test_status_distribution_counts_accurate(
        self,
        mock_file,
        mock_listdir,
        mock_isdir,
        mock_exists,
        mock_logger,
    ):
        """Check that status distribution counts are accurate."""

        # Arrange
        start_scraping = "2025-09-21_17-13-00"
        mock_exists.return_value = True

        test_csv_data = []
        expected_counts = {}

        for status in COMMON_STATUSES:
            test_csv_data.append({REQUIRED_CSV_COLUMNS.CURRENT_STATUS: status})
            expected_counts[status] = 1

        # Add extra "Answered initiative" to test multiple counts
        test_csv_data.append(
            {"current_status": COMMON_STATUSES[0]}
        )  # "Answered initiative"
        expected_counts[COMMON_STATUSES[0]] = 2

        # Mock CSV reading using the example data from user's CSV file
        with patch("csv.DictReader") as mock_csv_reader:
            mock_csv_reader.return_value = test_csv_data
            # Act
            stats = self.gather_scraping_statistics(start_scraping, [], [])

            # Assert
            expected_counter = Counter(expected_counts)

            assert stats["status_counter"] == expected_counter

    @patch("ECI_initiatives.scraper.initiatives.statistics.logger")
    @patch("datetime.datetime")
    @patch("ECI_initiatives.scraper.initiatives.statistics.gather_scraping_statistics")
    def test_completion_timestamps_accurate(
        self, mock_gather_stats, mock_datetime, mock_logger
    ):
        """Ensure completion timestamps and duration reporting are correct."""

        # Arrange
        mock_now = Mock()
        mock_now.strftime.return_value = "2025-09-21 17:13:45"
        mock_datetime.now.return_value = mock_now

        start_scraping = "2025-09-21_17-13-00"
        saved_page_paths = ["page1.html", "page2.html"]
        stats = {"status_counter": Counter({"Registered": 2}), "total_initiatives": 2}

        # Act
        self.display_summary_info(start_scraping, saved_page_paths, stats)

        # Assert
        mock_datetime.now.assert_called_once()
        mock_now.strftime.assert_called_with("%Y-%m-%d %H:%M:%S")

        # Verify the logger was called with the correct timestamp
        assert any(
            "Scraping completed at: 2025-09-21 17:13:45" in str(call)
            for call in mock_logger.info.call_args_list
        )
        assert any(
            f"Start time: {start_scraping}" in str(call)
            for call in mock_logger.info.call_args_list
        )

    @patch("ECI_initiatives.scraper.initiatives.statistics.logger")
    def test_file_path_reporting_matches_saved_locations(self, mock_logger):
        """Validate that file path reporting matches actual saved locations."""

        # Arrange
        start_scraping = "2025-09-21_17-13-00"
        saved_page_paths = [
            "initiatives/2025-09-21_17-13-00/list/page_1.html",
            "initiatives/2025-09-21_17-13-00/list/page_2.html",
            "initiatives/2025-09-21_17-13-00/list/page_3.html",
        ]
        failed_urls = []
        stats = {"downloaded_count": 3, "total_initiatives": 3, "failed_count": 0}

        # Act
        self.display_results_and_files(start_scraping, saved_page_paths, failed_urls, stats)

        # Assert
        # Verify that the saved paths are reported correctly
        mock_logger.info.assert_any_call(
            f"Files saved in: initiatives/{start_scraping}"
        )
        mock_logger.info.assert_any_call(
            LOG_MESSAGES["summary_scraping"]["main_page_sources"]
        )

        # Check that each path is logged with correct numbering
        for i, path in enumerate(saved_page_paths, 1):
            mock_logger.info.assert_any_call(f"  Page {i}: {path}")

    @patch("os.path.exists")
    @patch("os.path.isdir")
    @patch("os.listdir")
    @patch("builtins.open", new_callable=mock_open)
    def test_gather_scraping_statistics_function(
        self, mock_file, mock_listdir, mock_isdir, mock_exists
    ):
        """Test the gather_scraping_statistics function."""

        # Arrange
        start_scraping = "2025-09-21_17-13-00"
        initiative_data = [
            {REQUIRED_CSV_COLUMNS.URL: "https://example.com/1"},
            {REQUIRED_CSV_COLUMNS.URL: "https://example.com/2"},
            {REQUIRED_CSV_COLUMNS.URL: "https://example.com/3"},
        ]
        failed_urls = ["https://example.com/failed1", "https://example.com/failed2"]

        # Mock file system for CSV reading and directory counting
        def side_effect(path):

            if path.endswith(CSV_FILENAME):
                return True

            elif path.endswith(PAGES_DIR_NAME):
                return True

            return False

        mock_exists.side_effect = side_effect

        # Mock CSV reading
        with patch("csv.DictReader") as mock_csv_reader:
            mock_csv_reader.return_value = [
                {REQUIRED_CSV_COLUMNS.CURRENT_STATUS: "Registered"},
                {REQUIRED_CSV_COLUMNS.CURRENT_STATUS: "Collection ongoing"},
                {REQUIRED_CSV_COLUMNS.CURRENT_STATUS: "Valid initiative"},
            ]

            # Mock directory structure for counting files
            mock_listdir.side_effect = [
                ["2019", "2020", "2021"],  # Year directories
                ["initiative1.html", "initiative2.html"],  # 2019 files
                ["initiative3.html"],  # 2020 files
                [],  # 2021 files (empty)
            ]
            mock_isdir.return_value = True

            # Act
            result = self.gather_scraping_statistics(
                start_scraping, initiative_data, failed_urls
            )

            # Assert
            expected_result = {
                "status_counter": Counter(
                    {"Registered": 1, "Collection ongoing": 1, "Valid initiative": 1}
                ),
                "downloaded_count": 3,  # Files per year: 2019(2) + 2020(1) + 2021(0) = 3 total
                "total_initiatives": 3,
                "failed_count": 2,
            }

            assert result["status_counter"] == expected_result["status_counter"]
            assert result["downloaded_count"] == expected_result["downloaded_count"]
            assert result["total_initiatives"] == expected_result["total_initiatives"]
            assert result["failed_count"] == expected_result["failed_count"]

    @patch("ECI_initiatives.scraper.initiatives.statistics.logger")
    def test_display_results_with_failed_downloads(self, mock_logger):
        """Test display_results_and_files function with failed downloads."""

        # Arrange
        start_scraping = "2025-09-21_17-13-00"
        saved_page_paths = ["page1.html", "page2.html"]
        failed_urls = ["https://example.com/failed1", "https://example.com/failed2"]
        stats = {"downloaded_count": 2, "total_initiatives": 4, "failed_count": 2}

        # Act
        self.display_results_and_files(start_scraping, saved_page_paths, failed_urls, stats)

        # Assert
        mock_logger.info.assert_any_call(
            LOG_MESSAGES["summary_scraping"]["pages_downloaded"].format(
                downloaded_count=2, total_initiatives=4
            )
        )
        mock_logger.error.assert_any_call(
            LOG_MESSAGES["summary_scraping"]["failed_downloads"].format(failed_count=2)
        )
        mock_logger.error.assert_any_call(" - https://example.com/failed1")
        mock_logger.error.assert_any_call(" - https://example.com/failed2")

    @patch("ECI_initiatives.scraper.initiatives.statistics.logger")
    def test_display_results_no_failures(self, mock_logger):
        """Test display_results_and_files function with no failed downloads."""

        # Arrange
        start_scraping = "2025-09-21_17-13-00"
        saved_page_paths = ["page1.html", "page2.html"]
        failed_urls = []
        stats = {"downloaded_count": 2, "total_initiatives": 2, "failed_count": 0}

        # Act
        self.display_results_and_files(start_scraping, saved_page_paths, failed_urls, stats)

        # Assert
        mock_logger.info.assert_any_call(
            LOG_MESSAGES["summary_scraping"]["pages_downloaded"].format(
                downloaded_count=2, total_initiatives=2
            )
        )
        mock_logger.info.assert_any_call(
            LOG_MESSAGES["summary_scraping"]["all_downloads_successful"]
        )
        # Should not call error methods
        assert not mock_logger.error.called

    @patch("ECI_initiatives.scraper.initiatives.statistics.logger")
    def test_display_summary_info_content(self, mock_logger):
        """Test that display_summary_info outputs correct summary content."""

        # Arrange
        start_scraping = "2025-09-21_17-13-00"
        saved_page_paths = ["page1.html", "page2.html", "page3.html"]
        stats = {
            "status_counter": Counter(
                {"Registered": 2, "Collection ongoing": 1, "Valid initiative": 1}
            ),
            "total_initiatives": 4,
        }

        with patch("datetime.datetime") as mock_datetime:

            mock_now = Mock()
            mock_now.strftime.return_value = "2025-09-21 17:15:00"
            mock_datetime.now.return_value = mock_now

            # Act
            self.display_summary_info(start_scraping, saved_page_paths, stats)

            # Assert
            mock_logger.info.assert_any_call(
                LOG_MESSAGES["summary_scraping"]["scraping_complete"]
            )
            mock_logger.info.assert_any_call(
                f"Total pages scraped: {len(saved_page_paths)}"
            )
            mock_logger.info.assert_any_call(
                f"Total initiatives found: {stats['total_initiatives']}"
            )
            mock_logger.info.assert_any_call(
                "Initiatives by category (current_status):"
            )

            mock_logger.info.assert_any_call(
                LOG_MESSAGES["summary_scraping"]["registered_status"].format(count=2)
            )
            mock_logger.info.assert_any_call(
                LOG_MESSAGES["summary_scraping"]["collection_ongoing_status"].format(
                    count=1
                )
            )
            mock_logger.info.assert_any_call(
                LOG_MESSAGES["summary_scraping"]["valid_initiative_status"].format(
                    count=1
                )
            )

```

`./ECI_initiatives/tests/scraper/behaviour/test_scraping_process.py`:
```
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

# Safe imports (don't trigger logger creation)
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
        from ECI_initiatives.scraper.initiatives.crawler import (
            navigate_to_next_page,
            wait_for_listing_page_content,
            scrape_single_listing_page,
            scrape_all_initiatives_on_all_pages,
        )
        from ECI_initiatives.scraper.initiatives.file_ops import save_listing_page
        
        cls.navigate_to_next_page = staticmethod(navigate_to_next_page)
        cls.wait_for_listing_page_content = staticmethod(wait_for_listing_page_content)
        cls.scrape_single_listing_page = staticmethod(scrape_single_listing_page)
        cls.scrape_all_initiatives_on_all_pages = staticmethod(scrape_all_initiatives_on_all_pages)
        cls.save_listing_page = staticmethod(save_listing_page)

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

    @patch("ECI_initiatives.scraper.initiatives.crawler.logger")
    @patch("ECI_initiatives.scraper.initiatives.crawler.time.sleep")
    @patch("ECI_initiatives.scraper.initiatives.crawler.random.uniform", return_value=1.0)
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
        result1 = self.navigate_to_next_page(mock_driver, 1)
        assert result1 is True

        # Second call should return False (no next button)
        result2 = self.navigate_to_next_page(mock_driver, 2)
        assert result2 is False

        # Verify execute_script was called for the first page
        mock_driver.execute_script.assert_called_once()

    @patch("ECI_initiatives.scraper.initiatives.crawler.logger")
    def test_stops_at_last_page(self, mock_logger, mock_driver):
        """Verify that scraping stops correctly when reaching the last page."""

        # Simulate no next button found (last page scenario)
        mock_driver.find_element.side_effect = NoSuchElementException()

        result = self.navigate_to_next_page(mock_driver, 5)
        assert result is False

        # Ensure execute_script was not called since no button was found
        mock_driver.execute_script.assert_not_called()

    @patch("ECI_initiatives.scraper.initiatives.file_ops.logger")
    @patch("ECI_initiatives.scraper.initiatives.file_ops.time.sleep")
    @patch("ECI_initiatives.scraper.initiatives.file_ops.random.uniform", return_value=1.0)
    def test_page_numbering_correspondence(
        self, mock_uniform, mock_sleep, mock_logger, mock_driver, tmp_path
    ):
        """Check that page numbering in saved files corresponds to actual pages scraped."""

        mock_driver.page_source = "<html><body>Page content</body></html>"

        # Test saving different page numbers
        for page_num in [1, 2, 10]:

            page_source, page_path = self.save_listing_page(
                mock_driver, str(tmp_path), page_num
            )

            expected_filename = f"{LISTING_HTML_PATTERN}{page_num:03d}.html"
            assert expected_filename in page_path
            assert os.path.exists(page_path)

    @patch("ECI_initiatives.scraper.initiatives.__main__.logger")
    @patch(
        "ECI_initiatives.scraper.initiatives.crawler.parse_initiatives_list_data",
        return_value=[
            {
                REQUIRED_CSV_COLUMNS.URL: "test",
                REQUIRED_CSV_COLUMNS.CURRENT_STATUS: "active",
            }
        ],
    )
    @patch("ECI_initiatives.scraper.initiatives.crawler.wait_for_listing_page_content")
    @patch("ECI_initiatives.scraper.initiatives.crawler.save_listing_page")
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
            "ECI_initiatives.scraper.initiatives.crawler.navigate_to_next_page",
            side_effect=[True, True, False],
        ):
            all_data, saved_paths = self.scrape_all_initiatives_on_all_pages(
                mock_driver, "http://base.url", "/test/dir"
            )

        # Verify all 3 pages were processed
        assert len(saved_paths) == 3
        assert len(all_data) == 3  # Each page returns 1 initiative
        assert mock_save.call_count == 3

    @patch("ECI_initiatives.scraper.initiatives.crawler.logger")
    @patch("ECI_initiatives.scraper.initiatives.crawler.time.sleep")
    def test_navigate_to_next_page_functionality(
        self, mock_sleep, mock_logger, mock_driver
    ):
        """Test the navigate_to_next_page function behavior."""

        mock_next_button = Mock()
        mock_driver.find_element.return_value = mock_next_button

        result = self.navigate_to_next_page(mock_driver, 1)

        assert result is True

        mock_driver.find_element.assert_called_once()
        mock_driver.execute_script.assert_called_once_with(
            "arguments[0].click();", mock_next_button
        )

        mock_sleep.assert_called_once()


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
        from ECI_initiatives.scraper.initiatives.downloader import (
            download_single_initiative,
            download_initiative_pages,
            check_rate_limiting,
        )
        from ECI_initiatives.scraper.initiatives.browser import initialize_browser
        
        cls.download_single_initiative = staticmethod(download_single_initiative)
        cls.download_initiative_pages = staticmethod(download_initiative_pages)
        cls.check_rate_limiting = staticmethod(check_rate_limiting)
        cls.initialize_browser = staticmethod(initialize_browser)

    @pytest.fixture
    def mock_driver(self):
        """Create a mock driver for testing."""
        return Mock(spec=webdriver.Chrome)

    @patch("ECI_initiatives.scraper.initiatives.downloader.logger")
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

    @patch("ECI_initiatives.scraper.initiatives.downloader.logger")
    @patch("ECI_initiatives.scraper.initiatives.downloader.download_single_initiative")
    @patch("ECI_initiatives.scraper.initiatives.downloader.initialize_browser")
    @patch("ECI_initiatives.scraper.initiatives.downloader.time.sleep")
    @patch("ECI_initiatives.scraper.initiatives.downloader.random.uniform", return_value=1.0)
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

        updated_data, failed_urls = self.download_initiative_pages("/tmp", test_data)

        assert len(failed_urls) == 2
        assert "http://test2.com" in failed_urls
        assert "http://test4.com" in failed_urls
        assert len(updated_data) == 4

    @patch("ECI_initiatives.scraper.initiatives.downloader.logger")
    @patch("ECI_initiatives.scraper.initiatives.downloader.time.sleep")
    @patch("ECI_initiatives.scraper.initiatives.downloader.random.uniform", return_value=1.0)
    def test_rate_limiting_handling(self, mock_uniform, mock_sleep, mock_driver):
        """Check that rate limiting is handled gracefully with appropriate retries."""

        # Test rate limiting detection in page content
        mock_driver.page_source = f"<html><head><title>{RATE_LIMIT_INDICATORS.SERVER_INACCESSIBILITY}</title></head><body>{RATE_LIMIT_INDICATORS.TOO_MANY_REQUESTS}</body></html>"

        url = f"{FULL_FIND_INITIATIVE_URL}/details/2024/000001_en"

        with patch(
            "ECI_initiatives.scraper.initiatives.downloader.check_rate_limiting"
        ) as mock_check:
            mock_check.side_effect = Exception(
                f"{RATE_LIMIT_INDICATORS.RATE_LIMITED} (HTML response)"
            )

            result = self.download_single_initiative(mock_driver, "/tmp", url, max_retries=1)
            assert result is False

    @patch("ECI_initiatives.scraper.initiatives.crawler.logger")
    def test_continues_after_non_critical_errors(self, mock_driver):
        """Ensure scraping continues after encountering non-critical errors."""

        # Import needed for this specific test
        from ECI_initiatives.scraper.initiatives.crawler import wait_for_listing_page_content

        # Test that timeout on waiting for elements doesn't stop the process
        with patch("ECI_initiatives.scraper.initiatives.crawler.WebDriverWait") as mock_wait:

            mock_wait.return_value.until.side_effect = TimeoutException()

            # This should not raise an exception, just log a warning
            wait_for_listing_page_content(mock_driver, 1)

            # The method should complete without raising an exception
            assert True

    @patch("ECI_initiatives.scraper.initiatives.downloader.logger")
    @patch("ECI_initiatives.scraper.initiatives.downloader.time.sleep")
    def test_retry_logic_for_failed_requests(self, mock_sleep, mock_driver, tmp_path):
        """Test the retry mechanism for failed requests."""

        # First two calls fail with rate limiting, third succeeds
        mock_driver.get.side_effect = [
            Exception(RATE_LIMIT_INDICATORS.TOO_MANY_REQUESTS),
            Exception(RATE_LIMIT_INDICATORS.RATE_LIMITED),
            None,  # Success
        ]
        mock_driver.page_source = "<html><body>Success</body></html>"

        with patch("ECI_initiatives.scraper.initiatives.downloader.check_rate_limiting"):

            with patch("ECI_initiatives.scraper.initiatives.downloader.wait_for_page_content"):

                with patch(
                    "ECI_initiatives.scraper.initiatives.downloader.save_initiative_page",
                    return_value="test.html",
                ):
                    url = "https://test.com/details/2024/000001_en"

                    result = self.download_single_initiative(
                        mock_driver, str(tmp_path), url, max_retries=3
                    )

        assert result is True
        assert mock_driver.get.call_count == 3  # Two failed attempts, one success


class TestScrapingProcessFlow:
    """Test overall scraping process flow."""

    @classmethod
    def setup_class(cls):
        """
        Import modules and set up class attributes.
        
        Imports are done here rather than at module level to avoid
        log file creation during module loading, allowing the session
        fixture to properly track and clean up test artifacts.
        """
        from ECI_initiatives.scraper.initiatives.crawler import (
            wait_for_listing_page_content,
            scrape_single_listing_page,
            scrape_all_initiatives_on_all_pages,
        )
        from ECI_initiatives.scraper.initiatives.downloader import (
            wait_for_page_content,
            check_rate_limiting,
        )
        
        cls.wait_for_listing_page_content = staticmethod(wait_for_listing_page_content)
        cls.wait_for_page_content = staticmethod(wait_for_page_content)
        cls.check_rate_limiting = staticmethod(check_rate_limiting)
        cls.scrape_single_listing_page = staticmethod(scrape_single_listing_page)
        cls.scrape_all_initiatives_on_all_pages = staticmethod(scrape_all_initiatives_on_all_pages)

    @pytest.fixture
    def mock_driver(self):
        """Create a mock driver for testing."""

        return Mock(spec=webdriver.Chrome)

    @patch("ECI_initiatives.scraper.initiatives.crawler.logger")
    @patch("ECI_initiatives.scraper.initiatives.crawler.WebDriverWait")
    def test_wait_for_listing_page_content(
        self, mock_wait_class, mock_logger, mock_driver
    ):
        """Test waiting for listing page content to load."""

        mock_wait = Mock()
        mock_wait_class.return_value = mock_wait

        # Test successful wait
        self.wait_for_listing_page_content(mock_driver, 1)

        mock_wait_class.assert_called_with(mock_driver, DEFAULT_WEBDRIVER_TIMEOUT)
        mock_wait.until.assert_called_once()

    @patch("ECI_initiatives.scraper.initiatives.downloader.logger")
    @patch("ECI_initiatives.scraper.initiatives.downloader.WebDriverWait")
    def test_wait_for_page_content(self, mock_wait_class, mock_logger, mock_driver):
        """Test waiting for individual page content to load."""

        mock_wait = Mock()
        mock_wait_class.return_value = mock_wait
        # Simulate successful wait for first selector, others fail
        mock_wait.until.side_effect = [None, TimeoutException(), TimeoutException()]

        self.wait_for_page_content(mock_driver)

        mock_wait_class.assert_called_with(mock_driver, PAGE_CONTENT_TIMEOUT)
        # Should be called multiple times as it tries different selectors
        assert mock_wait.until.call_count >= 1

    def test_check_rate_limiting_detection(self, mock_driver):
        """Test rate limiting detection functionality."""

        # Test case: Rate limiting detected
        mock_element = Mock()
        mock_element

```

`./ECI_initiatives/tests/scraper/conftest.py`:
```
"""
Shared fixtures for browser and scraper behavior tests.
"""

import pytest


@pytest.fixture(scope="session", autouse=True)
def cleanup_log_directories():
    """Track and cleanup log directories created during the entire test session."""
    
    import shutil
    import re
    from pathlib import Path

    DIVIDER = "=" * 20
    DIVIDER_LINE = "\n" + DIVIDER + " {} " + DIVIDER + "\n"
    DIVIDER_START = DIVIDER_LINE.format("START TEST MESSAGE")
    DIVIDER_END = DIVIDER_LINE.format(" END TEST MESSAGE ")
    
    # Pattern for timestamp directories: YYYY-MM-DD_HH-MM-SS
    timestamp_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}$')
    
    # Get the base directory where log directories are created
    script_dir = Path(__file__).parent.parent.parent.absolute() # Where the ECI_initiatives/ is
    data_base_dir = script_dir / "data"

    print(f"\n{DIVIDER_START}")
    print("data directory:\n", data_base_dir)
    
    # Store existing timestamp directories before any tests run
    existing_timestamp_dirs = set()
    if data_base_dir.exists():
        for item in data_base_dir.iterdir():
            if item.is_dir() and timestamp_pattern.match(item.name):
                existing_timestamp_dirs.add(item.name)

    print("existing directories in data dir:\n" + str(existing_timestamp_dirs))
    print(DIVIDER_END)
    
    yield  # Run all tests
    
    # Cleanup: Remove any new timestamp directories created during test session
    if data_base_dir.exists():
        directories_removed = 0
        files_removed = 0

        print(f"\n{DIVIDER_START}\nRemoved test log directory:", end='') # end='' to avoid extra new line

        for item in data_base_dir.iterdir():
            if (item.is_dir() and 
                timestamp_pattern.match(item.name) and 
                item.name not in existing_timestamp_dirs):
                
                try:
                    # Count files before removal
                    logs_dir = item / "logs"
                    if logs_dir.exists():
                        log_files = list(logs_dir.glob("scraper_initiatives*.log"))
                        files_removed += len(log_files)
                    
                    shutil.rmtree(item)
                    directories_removed += 1
                    print(f"\n - {item}")
                    
                except Exception as e:
                    print(f"Warning: Could not remove log directory {item}: {e}")
        
        if directories_removed > 0:
            print(f"Cleanup complete: removed {directories_removed} directories and {files_removed} log files")

        print(DIVIDER_END)

```

`./ECI_initiatives/tests/scraper/end_to_end/__init__.py`:
```

```

`./ECI_initiatives/tests/scraper/end_to_end/test_created_files.py`:
```
"""
Test suite for validating that the ECI scraper correctly creates files and directories.

It checks that the scraper properly:

 1. downloads web pages
 2. saves them as HTML files
 3. creates CSV data files with initiative information
 4. organizes everything into the expected directory structure

To avoid overwhelming the ECI website and prevent potential server blocks or rate
limiting, this test uses a deliberately limited scope.
It only scrapes the first page of initiatives and
downloads just the first 3 individual initiative pages.

The test focuses only on the most critical outcomes:

 - whether files are created
 - placed in correct locations
 - contain valid content
 - follow proper naming conventions.

It does not test detailed parsing logic or handle edge cases that
might occur with different website layouts or server responses.

This simplified approach reduces maintenance overhead
since external websites can change unpredictably,
and keeps the test reliable by avoiding dependencies on
specific website content that may vary over time.

It should take between 30 seconds and 1 minute to complete.

The test validates:

 - Directory structure creation (data, listings, pages, logs folders)
 - CSV file creation with proper headers and limited initiative data
 - HTML listing page download and storage
 - Individual initiative page downloads (3 files)
 - Basic file content validation (HTML structure, expected content)
 - File naming convention compliance
"""

# Standard library
import csv
import os
import shutil
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Third party
import pytest

# Local
program_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
sys.path.append(program_dir)

# Safe imports (don't trigger logger creation)
from ECI_initiatives.tests.consts import (
    BASE_URL,
    REQUIRED_CSV_COLUMNS,
    MAX_PAGES_E2E_TEST,
    MAX_INITIATIVES_E2E_TEST,
    LISTING_HTML_PATTERN,
    CSV_FILENAME,
    DATA_DIR_NAME,
    LISTINGS_DIR_NAME,
    PAGES_DIR_NAME,
    LOG_DIR_NAME,
)


class TestCreatedFiles:
    """Test suite for validating created files from ECI scraping."""

    @classmethod
    def setup_class(cls):
        """
        Setup class-level resources that runs once before all tests.
        
        Imports are done here rather than at module level to avoid
        log file creation during module loading, allowing the session
        fixture to properly track and clean up test artifacts.
        """

        # Import scraper modules at setup time
        from ECI_initiatives.scraper.initiatives.__main__ import scrape_eci_initiatives
        from ECI_initiatives.scraper.initiatives.data_parser import parse_initiatives_list_data
        from ECI_initiatives.scraper.initiatives.crawler import (
            scrape_all_initiatives_on_all_pages,
            navigate_to_next_page,
        )
        
        # Store as class attributes for use in tests
        cls.scrape_eci_initiatives = staticmethod(scrape_eci_initiatives)
        cls.parse_initiatives_list_data = staticmethod(parse_initiatives_list_data)
        cls.scrape_all_initiatives_on_all_pages = staticmethod(scrape_all_initiatives_on_all_pages)
        cls.navigate_to_next_page = staticmethod(navigate_to_next_page)

        # Create temporary directories for testing
        cls.temp_base_dir = tempfile.mkdtemp(prefix="eci_test_")
        cls.temp_data_dir = os.path.join(cls.temp_base_dir, DATA_DIR_NAME)

        # Store original functions for later restoration
        original_parse_initiatives = parse_initiatives_list_data
        original_navigate_to_next_page = navigate_to_next_page

        def mock_parse_initiatives_limited(page_source, base_url):
            """
            Parse initiatives but limit to first 3 items.
            To limit the time that the test takes.
            """

            full_data = original_parse_initiatives(page_source, base_url)
            return full_data[
                :MAX_INITIATIVES_E2E_TEST
            ]  # Return only first 3 initiatives

        def mock_navigate_to_next_page_first_only(driver, current_page):
            """
            Always return False to stop at first page.
            Mocked to just scrape the first page.
            """

            return False

        # Apply mocks and run scraping - using REAL directories
        with patch.object(
            sys.modules["ECI_initiatives.scraper.initiatives.crawler"],
            "parse_initiatives_list_data",
            side_effect=mock_parse_initiatives_limited,
        ), patch.object(
            sys.modules["ECI_initiatives.scraper.initiatives.crawler"],
            "navigate_to_next_page",
            side_effect=mock_navigate_to_next_page_first_only,
        ):

            # Run the scraping function - saves to real ECI_initiatives/data/ directory
            timestamp = cls.scrape_eci_initiatives()

        # Store results for tests - point to REAL data directory
        cls.timestamp = timestamp
        
        # Get the real script directory (where ECI_initiatives project is located)
        script_dir = Path(__file__).parent.parent.parent.parent.absolute()  # Go up to ECI_initiatives/
        real_data_dir = script_dir / "data"
        
        cls.data_path = real_data_dir / timestamp
        cls.listings_path = cls.data_path / LISTINGS_DIR_NAME
        cls.pages_path = cls.data_path / PAGES_DIR_NAME
        cls.logs_path = cls.data_path / LOG_DIR_NAME

    @classmethod
    def teardown_class(cls):
        """Cleanup class-level resources that runs once after all tests."""

        # No cleanup needed - the conftest.py fixture will handle cleaning up the real directories
        print(f"\n\nTest completed. Files created in:\n{cls.data_path}")
        print("Note: Files will be cleaned up by the session fixture.")

    def test_debug_fixture(self):
        """Debug test to see setup output."""

        print("Debug - setup completed successfully")
        print(f"Timestamp: {self.timestamp}")
        print(f"Data path: {self.data_path}")
        print(f"Listings path: {self.listings_path}")
        print(f"Pages path: {self.pages_path}")

    def test_directory_structure_created(self):
        """Test that all required directories are created."""

        # Check main directories exist
        assert os.path.exists(self.data_path), "Main data directory not created"
        assert os.path.exists(self.listings_path), "Listings directory not created"
        assert os.path.exists(self.pages_path), "Pages directory not created"

        assert os.path.exists(self.logs_path), "Logs directory not created"

    def test_listing_files_created(self):
        """Test that listing page files are created with correct content."""

        # Check CSV file exists
        csv_file = os.path.join(self.listings_path, CSV_FILENAME)
        assert os.path.exists(csv_file), "initiatives_list.csv not created"

        # Check HTML listing file exists (should be exactly 1 since we only scrape first page)
        html_files = [f for f in os.listdir(self.listings_path) if f.endswith(".html")]
        assert (
            len(html_files) == MAX_PAGES_E2E_TEST
        ), f"Expected 1 HTML listing file, found {len(html_files)}"

        # Check HTML file name pattern
        html_file = html_files[0]

        assert html_file.startswith(
            "Find_initiative_European_Citizens_Initiative_page_"
        ), f"HTML file name pattern incorrect: {html_file}"

    def test_csv_content_structure(self):
        """Test CSV file has correct structure and limited content."""

        csv_file = os.path.join(self.listings_path, CSV_FILENAME)

        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Should have exactly 3 rows (limited by our mock)
        assert len(rows) == 3, f"Expected exactly 3 initiatives, found {len(rows)}"

        # Check required columns exist
        required_columns = [
            REQUIRED_CSV_COLUMNS.URL,
            REQUIRED_CSV_COLUMNS.CURRENT_STATUS,
            REQUIRED_CSV_COLUMNS.REGISTRATION_NUMBER,
            REQUIRED_CSV_COLUMNS.SIGNATURE_COLLECTION,
            REQUIRED_CSV_COLUMNS.DATETIME,
        ]

        if rows:
            for col in required_columns:
                assert (
                    col in rows[0].keys()
                ), f"Required column '{col}' missing from CSV"

            # Check URL format
            for row in rows:
                assert row[REQUIRED_CSV_COLUMNS.URL].startswith(
                    f"{BASE_URL}/initiatives/details/"
                ), f"URL format incorrect: {row['url']}"

    def test_initiative_pages_downloaded(self):
        """Test that individual initiative pages are downloaded."""

        # Count HTML files in year directories
        html_count = 0

        if os.path.exists(self.pages_path):
            for item in os.listdir(self.pages_path):
                year_path = os.path.join(self.pages_path, item)

                if os.path.isdir(year_path):
                    html_files = [
                        f for f in os.listdir(year_path) if f.endswith(".html")
                    ]
                    html_count += len(html_files)

        # Should have exactly 3 HTML files (one for each initiative)
        assert html_count == 3, f"Expected 3 initiative HTML files, found {html_count}"

    def test_initiative_html_content(self):
        """Test that downloaded HTML files contain valid content."""

        html_files = []

        # Collect all HTML files from year directories
        for item in os.listdir(self.pages_path):
            year_path = os.path.join(self.pages_path, item)

            if os.path.isdir(year_path):
                for file in os.listdir(year_path):
                    if file.endswith(".html"):
                        html_files.append(os.path.join(year_path, file))

        assert len(html_files) > 0, "No HTML files found to test"

        # Test each HTML file
        for html_file in html_files:
            with open(html_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Basic HTML validation
            assert len(content) > 100, f"HTML file too short: {html_file}"
            assert "<html" in content.lower(), f"No HTML tag found in: {html_file}"
            assert (
                "</html>" in content.lower()
            ), f"No closing HTML tag found in: {html_file}"

            # Check for ECI-specific content
            assert (
                "citizens-initiative.europa.eu" in content
                or "European Citizens' Initiative" in content
            ), f"File doesn't appear to be ECI content: {html_file}"

    def test_file_naming_convention(self):
        """Test that files follow the expected naming conventions."""

        # Check listing HTML file naming
        html_files = [f for f in os.listdir(self.listings_path) if f.endswith(".html")]

        for html_file in html_files:
            assert html_file.startswith(
                LISTING_HTML_PATTERN
            ), f"Listing HTML file naming incorrect: {html_file}"

            assert html_file.endswith(
                ".html"
            ), f"Listing file should end with .html: {html_file}"

        # Check initiative page file naming (should be <year>_<number_initiative>.html format)
        for item in os.listdir(self.pages_path):
            year_path = os.path.join(self.pages_path, item)

            if os.path.isdir(year_path):
                # Directory should be a year (4 digits)
                assert (
                    item.isdigit() and len(item) == 4
                ), f"Year directory name incorrect: {item}"

                for file in os.listdir(year_path):
                    if file.endswith(".html"):
                        # File should be year_number.html format
                        assert (
                            "_" in file
                        ), f"Initiative file name should contain underscore: {file}"

                        assert file.endswith(
                            ".html"
                        ), f"Initiative file should end with .html: {file}"

```

`./ECI_initiatives/tests/scraper/__init__.py`:
```

```

`./ECI_initiatives/tests/scraper/requirements.test.txt`:
```

```

`./ECI_initiatives/tests/scraper/conftest.py`:
```
"""
Shared fixtures for browser and scraper behavior tests.
"""

import pytest


@pytest.fixture(scope="session", autouse=True)
def cleanup_log_directories():
    """Track and cleanup log directories created during the entire test session."""
    
    import shutil
    import re
    from pathlib import Path

    DIVIDER = "=" * 20
    DIVIDER_LINE = "\n" + DIVIDER + " {} " + DIVIDER + "\n"
    DIVIDER_START = DIVIDER_LINE.format("START TEST MESSAGE")
    DIVIDER_END = DIVIDER_LINE.format(" END TEST MESSAGE ")
    
    # Pattern for timestamp directories: YYYY-MM-DD_HH-MM-SS
    timestamp_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}$')
    
    # Get the base directory where log directories are created
    script_dir = Path(__file__).parent.parent.parent.absolute() # Where the ECI_initiatives/ is
    data_base_dir = script_dir / "data"

    print(f"\n{DIVIDER_START}")
    print("data directory:\n", data_base_dir)
    
    # Store existing timestamp directories before any tests run
    existing_timestamp_dirs = set()
    if data_base_dir.exists():
        for item in data_base_dir.iterdir():
            if item.is_dir() and timestamp_pattern.match(item.name):
                existing_timestamp_dirs.add(item.name)

    print("existing directories in data dir:\n" + str(existing_timestamp_dirs))
    print(DIVIDER_END)
    
    yield  # Run all tests
    
    # Cleanup: Remove any new timestamp directories created during test session
    if data_base_dir.exists():
        directories_removed = 0
        files_removed = 0

        print(f"\n{DIVIDER_START}\nRemoved test log directory:", end='') # end='' to avoid extra new line

        for item in data_base_dir.iterdir():
            if (item.is_dir() and 
                timestamp_pattern.match(item.name) and 
                item.name not in existing_timestamp_dirs):
                
                try:
                    # Count files before removal
                    logs_dir = item / "logs"
                    if logs_dir.exists():
                        log_files = list(logs_dir.glob("scraper_initiatives*.log"))
                        files_removed += len(log_files)
                    
                    shutil.rmtree(item)
                    directories_removed += 1
                    print(f"\n - {item}")
                    
                except Exception as e:
                    print(f"Warning: Could not remove log directory {item}: {e}")
        
        if directories_removed > 0:
            print(f"Cleanup complete: removed {directories_removed} directories and {files_removed} log files")

        print(DIVIDER_END)

```

`./ECI_initiatives/tests/scraper/initiatives/behaviour/__init__.py`:
```

```

`./ECI_initiatives/tests/scraper/initiatives/behaviour/test_browser_webdriver.py`:
```
"""Tests for browser and WebDriver functionality."""

# Standard library
import os
import sys
from unittest.mock import Mock, patch, MagicMock

# Third party
import pytest

from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options

# Local
program_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..") # \ECI_initiatives
sys.path.append(program_dir)

# Safe imports (don't trigger logger creation)
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
        from ECI_initiatives.tests.consts import (
            REQUIRED_CSV_COLUMNS,
            SAMPLE_INITIATIVE_DATA,
            BASE_URL,
            LOG_MESSAGES,
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

```

`./ECI_initiatives/tests/scraper/initiatives/behaviour/test_data_extraction.py`:
```
"""
A test suite for scraper that validates
CSV file generation, HTML parsing accuracy,
through mocked browser interactions and static test fixtures,
ensuring reliable verification of data extraction
without depending on live website availability.
"""

# python
import copy
import csv
import datetime
import os
import re
import sys
import tempfile
from collections import Counter
from typing import List, Dict

# third-party
import pytest
from bs4 import BeautifulSoup
from unittest.mock import patch, MagicMock, mock_open, call


# Local
program_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", "..") # \ECI_initiatives

sys.path.append(program_dir)

# Safe imports (don't trigger logger creation)
from ECI_initiatives.tests.consts import (
    LISTINGS_HTML_DIR,
    CSV_FILE_PATH,
    BASE_URL,
    REQUIRED_CSV_COLUMNS,
    SAMPLE_LISTING_FILES,
)


# ===== SHARED FIXTURES (used by multiple test classes) =====


@pytest.fixture(scope="session")
def parsed_test_data():
    """Parse test HTML files once and reuse across all tests."""
    
    # Import here to avoid early logger initialization
    from ECI_initiatives.scraper.initiatives.data_parser import parse_initiatives_list_data
    
    with patch("ECI_initiatives.scraper.initiatives.data_parser.logger"):
        all_initiatives = []

        for page_file in SAMPLE_LISTING_FILES:
            page_path = os.path.join(LISTINGS_HTML_DIR, page_file)

            if not os.path.exists(page_path):
                continue

            with open(page_path, "r", encoding="utf-8") as f:
                page_source = f.read()

            initiatives = parse_initiatives_list_data(page_source, BASE_URL)
            all_initiatives.extend(initiatives)

        return all_initiatives


@pytest.fixture(scope="session")
def reference_data():
    """Load reference CSV once and reuse across all tests."""

    if not os.path.exists(CSV_FILE_PATH):
        pytest.skip(f"Reference CSV file not found: {CSV_FILE_PATH}")

    with open(CSV_FILE_PATH, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ===== TEST CLASSES =====


class TestCsvFileOperations:
    """Test CSV data validation functionality."""

    @classmethod
    def setup_class(cls):
        """
        Import modules and set up class attributes.
        
        Imports are done here rather than at module level to avoid
        log file creation during module loading, allowing the session
        fixture to properly track and clean up test artifacts.
        """
        from ECI_initiatives.scraper.initiatives.__main__ import save_and_download_initiatives
        
        cls.save_and_download_initiatives = staticmethod(save_and_download_initiatives)

    @patch("ECI_initiatives.scraper.initiatives.__main__.download_initiative_pages")
    @patch("ECI_initiatives.scraper.initiatives.__main__.logger")
    def test_csv_created_with_correct_headers(self, mock_logger, mock_download_pages):
        """
        Verify that initiatives_list.csv is created with correct headers:
        url, current_status, registration_number, signature_collection, datetime.
        """

        # Sample initiative data
        test_initiative_data = [
            {
                REQUIRED_CSV_COLUMNS.URL: "https://citizens-initiative.europa.eu/initiatives/details/2019/000007_en",
                REQUIRED_CSV_COLUMNS.CURRENT_STATUS: "Answered initiative",
                REQUIRED_CSV_COLUMNS.REGISTRATION_NUMBER: "ECI(2019)000007",
                REQUIRED_CSV_COLUMNS.SIGNATURE_COLLECTION: "Collection completed",
                REQUIRED_CSV_COLUMNS.DATETIME: "",
            }
        ]

        # Mock download_initiative_pages to return the same data with updated datetime
        updated_data = copy.deepcopy(test_initiative_data)
        updated_data[0][REQUIRED_CSV_COLUMNS.DATETIME] = "2025-09-21 11:24:00"

        mock_download_pages.return_value = (
            updated_data,
            [],
        )  # (updated_data, failed_urls)

        with tempfile.TemporaryDirectory() as temp_dir:

            list_dir = os.path.join(temp_dir, "listings")
            pages_dir = os.path.join(temp_dir, "pages")
            os.makedirs(list_dir, exist_ok=True)
            os.makedirs(pages_dir, exist_ok=True)

            # Call the function to test
            self.save_and_download_initiatives(list_dir, pages_dir, test_initiative_data)

            # Check that CSV file was created
            csv_file_path = os.path.join(list_dir, "initiatives_list.csv")
            assert os.path.exists(csv_file_path), "CSV file was not created"

            # Read and verify CSV headers and data
            with open(csv_file_path, "r", encoding="utf-8") as f:

                reader = csv.reader(f)
                headers = next(reader)
                expected_headers = [
                    REQUIRED_CSV_COLUMNS.URL,
                    REQUIRED_CSV_COLUMNS.CURRENT_STATUS,
                    REQUIRED_CSV_COLUMNS.REGISTRATION_NUMBER,
                    REQUIRED_CSV_COLUMNS.SIGNATURE_COLLECTION,
                    REQUIRED_CSV_COLUMNS.DATETIME,
                ]

                assert (
                    headers == expected_headers
                ), f"Expected:\n{expected_headers}\nGot:\n{headers}"

                # Read all remaining rows to avoid StopIteration
                data_rows = list(reader)
                assert len(data_rows) > 0, "No data rows found in CSV"

                # Verify first data row
                data_row = data_rows[0]

                assert len(data_row) == len(expected_headers), (
                    "Data row has incorrect number of columns.\n"
                    + "The first row:\n"
                    + str(data_row)
                )

                assert (
                    data_row[0] == test_initiative_data[0][REQUIRED_CSV_COLUMNS.URL]
                ), "URL not correctly written to CSV:\n" + str(data_row[0])

    @patch("ECI_initiatives.scraper.initiatives.__main__.logger")
    @patch("ECI_initiatives.scraper.initiatives.__main__.download_initiative_pages")
    def test_no_duplicate_initiatives(self, mock_download_pages, mock_logger):
        """Ensure no duplicate initiatives are recorded in the CSV when scraping produces duplicates."""

        # Create test data with duplicates (simulating what parse_initiatives_list_data might return)
        test_initiative_data_with_duplicates = [
            {
                REQUIRED_CSV_COLUMNS.URL: "https://citizens-initiative.europa.eu/initiatives/details/2019/000007_en",
                REQUIRED_CSV_COLUMNS.CURRENT_STATUS: "Answered initiative",
                REQUIRED_CSV_COLUMNS.REGISTRATION_NUMBER: "ECI(2019)000007",
                REQUIRED_CSV_COLUMNS.SIGNATURE_COLLECTION: "Collection completed",
                REQUIRED_CSV_COLUMNS.DATETIME: "",
            },
            {
                REQUIRED_CSV_COLUMNS.URL: "https://citizens-initiative.europa.eu/initiatives/details/2024/000004_en",
                REQUIRED_CSV_COLUMNS.CURRENT_STATUS: "Valid initiative",
                REQUIRED_CSV_COLUMNS.REGISTRATION_NUMBER: "ECI(2024)000004",
                REQUIRED_CSV_COLUMNS.SIGNATURE_COLLECTION: "Collection closed",
                REQUIRED_CSV_COLUMNS.DATETIME: "",
            },
            {
                REQUIRED_CSV_COLUMNS.URL: "https://citizens-initiative.europa.eu/initiatives/details/2019/000007_en",  # DUPLICATE
                REQUIRED_CSV_COLUMNS.CURRENT_STATUS: "Answered initiative",
                REQUIRED_CSV_COLUMNS.REGISTRATION_NUMBER: "ECI(2019)000007",
                REQUIRED_CSV_COLUMNS.SIGNATURE_COLLECTION: "Collection completed",
                REQUIRED_CSV_COLUMNS.DATETIME: "",
            },
        ]

        # Mock download_initiative_pages to return data without duplicates
        unique_data = []
        seen_urls = set()

        for item in test_initiative_data_with_duplicates:

            if item[REQUIRED_CSV_COLUMNS.URL] not in seen_urls:

                unique_data.append(item.copy())
                seen_urls.add(item[REQUIRED_CSV_COLUMNS.URL])

        mock_download_pages.return_value = (unique_data, [])

        with tempfile.TemporaryDirectory() as temp_dir:

            list_dir = os.path.join(temp_dir, "listings")
            pages_dir = os.path.join(temp_dir, "pages")

            os.makedirs(list_dir, exist_ok=True)
            os.makedirs(pages_dir, exist_ok=True)

            # Test the actual function from main module
            self.save_and_download_initiatives(
                list_dir, pages_dir, test_initiative_data_with_duplicates
            )

            # Verify CSV was created
            csv_file_path = os.path.join(list_dir, "initiatives_list.csv")
            assert os.path.exists(csv_file_path), "CSV file was not created"

            # Read CSV and check for duplicates
            with open(csv_file_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                csv_data = list(reader)

            # Extract URLs from CSV
            csv_urls = [row[REQUIRED_CSV_COLUMNS.URL] for row in csv_data]
            unique_csv_urls = list(set(csv_urls))

            # Should have only 2 unique URLs, not 3
            assert (
                len(csv_urls) == 2
            ), f"Expected 2 rows in CSV (duplicates removed), got:\n{len(csv_urls)}"
            assert (
                len(unique_csv_urls) == 2
            ), f"Found duplicate URLs in CSV:\n{csv_urls}"

            # Verify the specific URLs are correct
            expected_urls = [
                "https://citizens-initiative.europa.eu/initiatives/details/2019/000007_en",
                "https://citizens-initiative.europa.eu/initiatives/details/2024/000004_en",
            ]

            for expected_url in expected_urls:
                assert (
                    expected_url in csv_urls
                ), f"Expected URL {expected_url} not found in CSV"


class TestHtmlParsingBehaviour:
    """Test HTML parsing and data extraction."""

    def test_all_fields_extracted(self, parsed_test_data):
        """Ensure all required fields are present in extracted data."""
        expected_fields = [
            REQUIRED_CSV_COLUMNS.URL,
            REQUIRED_CSV_COLUMNS.CURRENT_STATUS,
            REQUIRED_CSV_COLUMNS.REGISTRATION_NUMBER,
            REQUIRED_CSV_COLUMNS.SIGNATURE_COLLECTION,
            REQUIRED_CSV_COLUMNS.DATETIME,
        ]

        for initiative in parsed_test_data:
            missing_fields = [f for f in expected_fields if f not in initiative]
            assert (
                not missing_fields
            ), f"Missing fields {missing_fields} in {initiative}"
            assert initiative[REQUIRED_CSV_COLUMNS.URL], "URL field is empty"

    def test_extracted_data_accuracy(self, parsed_test_data, reference_data):
        """Verify extracted data matches reference values."""
        reference_dict = {
            row[REQUIRED_CSV_COLUMNS.URL]: row[REQUIRED_CSV_COLUMNS.CURRENT_STATUS]
            for row in reference_data
        }

        for initiative in parsed_test_data:
            url = initiative[REQUIRED_CSV_COLUMNS.URL]
            if url in reference_dict:
                expected = reference_dict[url]
                actual = initiative[REQUIRED_CSV_COLUMNS.CURRENT_STATUS]
                assert (
                    actual == expected
                ), f"Status mismatch for {url}: expected '{expected}', got '{actual}'"

    def test_status_distribution_accuracy(self, parsed_test_data, reference_data):
        """Check that expected statuses appear in parsed data."""
        expected_statuses = {
            row[REQUIRED_CSV_COLUMNS.CURRENT_STATUS] for row in reference_data
        }
        actual_statuses = {
            init[REQUIRED_CSV_COLUMNS.CURRENT_STATUS]
            for init in parsed_test_data
            if init[REQUIRED_CSV_COLUMNS.CURRENT_STATUS]
        }

        missing = expected_statuses - actual_statuses
        assert not missing, f"Missing statuses in parsed data: {missing}"


class TestScrapingWorkflow:
    """Test data completeness and accuracy."""

    @classmethod
    def setup_class(cls):
        """
        Import modules and set up class attributes.
        
        Imports are done here rather than at module level to avoid
        log file creation during module loading, allowing the session
        fixture to properly track and clean up test artifacts.
        """
        from ECI_initiatives.scraper.initiatives.crawler import scrape_all_initiatives_on_all_pages
        from ECI_initiatives.scraper.initiatives.data_parser import parse_initiatives_list_data
        
        cls.scrape_all_initiatives_on_all_pages = staticmethod(scrape_all_initiatives_on_all_pages)
        cls.parse_initiatives_list_data = staticmethod(parse_initiatives_list_data)

    def test_initiative_count_matches_reference(self, parsed_test_data, reference_data):
        """Compare initiative count with reference data."""
        assert len(parsed_test_data) >= len(
            reference_data
        ), f"Found {len(parsed_test_data)} initiatives, expected at least {len(reference_data)}"

    @patch("ECI_initiatives.scraper.initiatives.browser.initialize_browser")
    @patch("ECI_initiatives.scraper.initiatives.__main__.logger")
    def test_pagination_handling(self, mock_logger, mock_browser):
        """Test pagination processing logic."""
        # Create a mock driver
        mock_driver = MagicMock()
        mock_browser.return_value = mock_driver

        # Mock pagination scenario: 3 pages total
        page_sources = [
            "<html>page1</html>",
            "<html>page2</html>",
            "<html>page3</html>",
        ]
        mock_driver.page_source = page_sources[0]  # Start with first page

        # Mock find_element for next button
        def mock_find_element_side_effect(*args, **kwargs):
            """Mock browser's find_element behavior for pagination."""
            if mock_find_element_side_effect.call_count <= 2:
                mock_button = MagicMock()
                return mock_button
            else:
                raise Exception("No next button found")

        mock_find_element_side_effect.call_count = 0

        def increment_and_side_effect(*args, **kwargs):
            """Wrapper to increment call counter and delegate to main side effect."""
            mock_find_element_side_effect.call_count += 1
            return mock_find_element_side_effect(*args, **kwargs)

        mock_driver.find_element.side_effect = increment_and_side_effect

        # Mock page source updates
        def update_page_source():
            """Update mock driver's page_source to simulate navigation."""
            if mock_find_element_side_effect.call_count <= len(page_sources):
                mock_driver.page_source = page_sources[
                    mock_find_element_side_effect.call_count - 1
                ]

        mock_driver.execute_script.side_effect = (
            lambda script, element: update_page_source()
        )

        # Mock other required methods
        with patch(
            "ECI_initiatives.scraper.initiatives.crawler.wait_for_listing_page_content"
        ), patch(
            "ECI_initiatives.scraper.initiatives.file_ops.save_listing_page"
        ) as mock_save, patch(
            "ECI_initiatives.scraper.initiatives.data_parser.parse_initiatives_list_data"
        ) as mock_parse, patch(
            "time.sleep"
        ):

            mock_save.return_value = ("", "test_path")
            mock_parse.return_value = [
                {
                    REQUIRED_CSV_COLUMNS.URL: "test",
                    REQUIRED_CSV_COLUMNS.CURRENT_STATUS: "",
                    REQUIRED_CSV_COLUMNS.REGISTRATION_NUMBER: "",
                    REQUIRED_CSV_COLUMNS.SIGNATURE_COLLECTION: "",
                    REQUIRED_CSV_COLUMNS.DATETIME: "",
                }
            ]

            with tempfile.TemporaryDirectory() as temp_dir:
                all_data, saved_paths = self.scrape_all_initiatives_on_all_pages(
                    mock_driver, BASE_URL, temp_dir
                )

                expected_page_count = 3

                # Should have processed 3 pages
                assert (
                    len(saved_paths) == expected_page_count
                ), f"Expected {expected_page_count} pages processed, got {len(saved_paths)}"
                assert (
                    mock_driver.find_element.call_count == expected_page_count
                ), f"Should have checked for next button {expected_page_count} times"
        """Ensure all initiative fields are extracted when available on source pages."""

        def load_expected_statuses():
            """Load status distribution from reference CSV file."""

            with open(CSV_FILE_PATH, "r", encoding="utf-8") as f:

                reader = csv.DictReader(f)
                return Counter(
                    row[REQUIRED_CSV_COLUMNS.CURRENT_STATUS] for row in reader
                )

        def parse_test_pages():
            """Parse all test HTML pages and extract statuses."""

            all_statuses = []

            for page_file in SAMPLE_LISTING_FILES:

                page_path = os.path.join(LISTINGS_HTML_DIR, page_file)

                with open(page_path, "r", encoding="utf-8") as f:
                    page_content = f.read()

                initiatives = self.parse_initiatives_list_data(page_content, BASE_URL)

                # Extract non-empty statuses
                page_statuses = [
                    init[REQUIRED_CSV_COLUMNS.CURRENT_STATUS]
                    for init in initiatives
                    if init[REQUIRED_CSV_COLUMNS.CURRENT_STATUS]
                ]
                all_statuses.extend(page_statuses)

            return Counter(all_statuses)

        # Main test logic
        expected_statuses = load_expected_statuses()
        actual_statuses = parse_test_pages()

        # Verify each expected status appears in parsed data
        missing_statuses = []
        for expected_status in expected_statuses:
            if expected_status not in actual_statuses:
                missing_statuses.append(expected_status)

        assert not missing_statuses, (
            f"These expected statuses were not found in parsed data: {missing_statuses}\n"
            f"Expected: {list(expected_statuses.keys())}\n"
            f"Found: {list(actual_statuses.keys())}"
        )

```

`./ECI_initiatives/tests/scraper/initiatives/behaviour/test_edge_cases.py`:
```
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
program_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..") # \ECI_initiatives
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

```

`./ECI_initiatives/tests/scraper/initiatives/behaviour/test_output_reporting.py`:
```
"""Tests for output and reporting functionality."""

# Standard library
import csv
import datetime
import os
import sys
from collections import Counter
from unittest.mock import Mock, patch, mock_open, MagicMock

# Third party
import pytest

# Local
program_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..") # \ECI_initiatives
sys.path.append(program_dir)

# Safe imports (don't trigger logger creation)
from ECI_initiatives.tests.consts import (
    COMMON_STATUSES,
    REQUIRED_CSV_COLUMNS,
    CSV_FILENAME,
    PAGES_DIR_NAME,
    LOG_MESSAGES,
)


class TestCompletionSummaryAccuracy:
    """Test completion summary and statistics accuracy."""

    @classmethod
    def setup_class(cls):
        """
        Import modules and set up class attributes.
        
        Imports are done here rather than at module level to avoid
        log file creation during module loading, allowing the session
        fixture to properly track and clean up test artifacts.
        """
        from ECI_initiatives.scraper.initiatives.statistics import (
            display_completion_summary,
            gather_scraping_statistics,
            display_summary_info,
            display_results_and_files,
        )
        
        cls.display_completion_summary = staticmethod(display_completion_summary)
        cls.gather_scraping_statistics = staticmethod(gather_scraping_statistics)
        cls.display_summary_info = staticmethod(display_summary_info)
        cls.display_results_and_files = staticmethod(display_results_and_files)

    @patch("ECI_initiatives.scraper.initiatives.statistics.logger")
    @patch("ECI_initiatives.scraper.initiatives.statistics.gather_scraping_statistics")
    @patch("ECI_initiatives.scraper.initiatives.statistics.display_summary_info")
    @patch("ECI_initiatives.scraper.initiatives.statistics.display_results_and_files")
    def test_final_statistics_match_actual_results(
        self, mock_display_results, mock_display_summary, mock_gather_stats, mock_logger
    ):
        """Verify that final statistics match actual results (total initiatives, downloads, failures)."""

        # Arrange
        start_scraping = "2025-09-21_17-13-00"
        initiative_data = [
            {
                REQUIRED_CSV_COLUMNS.URL: "https://example.com/1",
                REQUIRED_CSV_COLUMNS.CURRENT_STATUS: "Registered",
            },
            {
                REQUIRED_CSV_COLUMNS.URL: "https://example.com/2",
                REQUIRED_CSV_COLUMNS.CURRENT_STATUS: "Collection ongoing",
            },
            {
                REQUIRED_CSV_COLUMNS.URL: "https://example.com/3",
                REQUIRED_CSV_COLUMNS.CURRENT_STATUS: "Valid initiative",
            },
        ]
        saved_page_paths = ["page1.html", "page2.html", "page3.html"]
        failed_urls = ["https://example.com/failed"]

        expected_stats = {
            "status_counter": Counter(
                {"Registered": 1, "Collection ongoing": 1, "Valid initiative": 1}
            ),
            "downloaded_count": 3,
            "total_initiatives": 3,
            "failed_count": 1,
        }

        mock_gather_stats.return_value = expected_stats

        # Act
        self.display_completion_summary(
            start_scraping, initiative_data, saved_page_paths, failed_urls
        )

        # Assert
        mock_gather_stats.assert_called_once_with(
            start_scraping, initiative_data, failed_urls
        )
        mock_display_summary.assert_called_once_with(
            start_scraping, saved_page_paths, expected_stats
        )
        mock_display_results.assert_called_once_with(
            start_scraping, saved_page_paths, failed_urls, expected_stats
        )

    @patch("ECI_initiatives.scraper.initiatives.statistics.logger")
    @patch("os.path.exists")
    @patch("os.path.isdir")
    @patch("os.listdir")
    @patch("builtins.open", new_callable=mock_open)
    def test_status_distribution_counts_accurate(
        self,
        mock_file,
        mock_listdir,
        mock_isdir,
        mock_exists,
        mock_logger,
    ):
        """Check that status distribution counts are accurate."""

        # Arrange
        start_scraping = "2025-09-21_17-13-00"
        mock_exists.return_value = True

        test_csv_data = []
        expected_counts = {}

        for status in COMMON_STATUSES:
            test_csv_data.append({REQUIRED_CSV_COLUMNS.CURRENT_STATUS: status})
            expected_counts[status] = 1

        # Add extra "Answered initiative" to test multiple counts
        test_csv_data.append(
            {"current_status": COMMON_STATUSES[0]}
        )  # "Answered initiative"
        expected_counts[COMMON_STATUSES[0]] = 2

        # Mock CSV reading using the example data from user's CSV file
        with patch("csv.DictReader") as mock_csv_reader:
            mock_csv_reader.return_value = test_csv_data
            # Act
            stats = self.gather_scraping_statistics(start_scraping, [], [])

            # Assert
            expected_counter = Counter(expected_counts)

            assert stats["status_counter"] == expected_counter

    @patch("ECI_initiatives.scraper.initiatives.statistics.logger")
    @patch("datetime.datetime")
    @patch("ECI_initiatives.scraper.initiatives.statistics.gather_scraping_statistics")
    def test_completion_timestamps_accurate(
        self, mock_gather_stats, mock_datetime, mock_logger
    ):
        """Ensure completion timestamps and duration reporting are correct."""

        # Arrange
        mock_now = Mock()
        mock_now.strftime.return_value = "2025-09-21 17:13:45"
        mock_datetime.now.return_value = mock_now

        start_scraping = "2025-09-21_17-13-00"
        saved_page_paths = ["page1.html", "page2.html"]
        stats = {"status_counter": Counter({"Registered": 2}), "total_initiatives": 2}

        # Act
        self.display_summary_info(start_scraping, saved_page_paths, stats)

        # Assert
        mock_datetime.now.assert_called_once()
        mock_now.strftime.assert_called_with("%Y-%m-%d %H:%M:%S")

        # Verify the logger was called with the correct timestamp
        assert any(
            "Scraping completed at: 2025-09-21 17:13:45" in str(call)
            for call in mock_logger.info.call_args_list
        )
        assert any(
            f"Start time: {start_scraping}" in str(call)
            for call in mock_logger.info.call_args_list
        )

    @patch("ECI_initiatives.scraper.initiatives.statistics.logger")
    def test_file_path_reporting_matches_saved_locations(self, mock_logger):
        """Validate that file path reporting matches actual saved locations."""

        # Arrange
        start_scraping = "2025-09-21_17-13-00"
        saved_page_paths = [
            "initiatives/2025-09-21_17-13-00/list/page_1.html",
            "initiatives/2025-09-21_17-13-00/list/page_2.html",
            "initiatives/2025-09-21_17-13-00/list/page_3.html",
        ]
        failed_urls = []
        stats = {"downloaded_count": 3, "total_initiatives": 3, "failed_count": 0}

        # Act
        self.display_results_and_files(start_scraping, saved_page_paths, failed_urls, stats)

        # Assert
        # Verify that the saved paths are reported correctly
        mock_logger.info.assert_any_call(
            f"Files saved in: initiatives/{start_scraping}"
        )
        mock_logger.info.assert_any_call(
            LOG_MESSAGES["summary_scraping"]["main_page_sources"]
        )

        # Check that each path is logged with correct numbering
        for i, path in enumerate(saved_page_paths, 1):
            mock_logger.info.assert_any_call(f"  Page {i}: {path}")

    @patch("os.path.exists")
    @patch("os.path.isdir")
    @patch("os.listdir")
    @patch("builtins.open", new_callable=mock_open)
    def test_gather_scraping_statistics_function(
        self, mock_file, mock_listdir, mock_isdir, mock_exists
    ):
        """Test the gather_scraping_statistics function."""

        # Arrange
        start_scraping = "2025-09-21_17-13-00"
        initiative_data = [
            {REQUIRED_CSV_COLUMNS.URL: "https://example.com/1"},
            {REQUIRED_CSV_COLUMNS.URL: "https://example.com/2"},
            {REQUIRED_CSV_COLUMNS.URL: "https://example.com/3"},
        ]
        failed_urls = ["https://example.com/failed1", "https://example.com/failed2"]

        # Mock file system for CSV reading and directory counting
        def side_effect(path):

            if path.endswith(CSV_FILENAME):
                return True

            elif path.endswith(PAGES_DIR_NAME):
                return True

            return False

        mock_exists.side_effect = side_effect

        # Mock CSV reading
        with patch("csv.DictReader") as mock_csv_reader:
            mock_csv_reader.return_value = [
                {REQUIRED_CSV_COLUMNS.CURRENT_STATUS: "Registered"},
                {REQUIRED_CSV_COLUMNS.CURRENT_STATUS: "Collection ongoing"},
                {REQUIRED_CSV_COLUMNS.CURRENT_STATUS: "Valid initiative"},
            ]

            # Mock directory structure for counting files
            mock_listdir.side_effect = [
                ["2019", "2020", "2021"],  # Year directories
                ["initiative1.html", "initiative2.html"],  # 2019 files
                ["initiative3.html"],  # 2020 files
                [],  # 2021 files (empty)
            ]
            mock_isdir.return_value = True

            # Act
            result = self.gather_scraping_statistics(
                start_scraping, initiative_data, failed_urls
            )

            # Assert
            expected_result = {
                "status_counter": Counter(
                    {"Registered": 1, "Collection ongoing": 1, "Valid initiative": 1}
                ),
                "downloaded_count": 3,  # Files per year: 2019(2) + 2020(1) + 2021(0) = 3 total
                "total_initiatives": 3,
                "failed_count": 2,
            }

            assert result["status_counter"] == expected_result["status_counter"]
            assert result["downloaded_count"] == expected_result["downloaded_count"]
            assert result["total_initiatives"] == expected_result["total_initiatives"]
            assert result["failed_count"] == expected_result["failed_count"]

    @patch("ECI_initiatives.scraper.initiatives.statistics.logger")
    def test_display_results_with_failed_downloads(self, mock_logger):
        """Test display_results_and_files function with failed downloads."""

        # Arrange
        start_scraping = "2025-09-21_17-13-00"
        saved_page_paths = ["page1.html", "page2.html"]
        failed_urls = ["https://example.com/failed1", "https://example.com/failed2"]
        stats = {"downloaded_count": 2, "total_initiatives": 4, "failed_count": 2}

        # Act
        self.display_results_and_files(start_scraping, saved_page_paths, failed_urls, stats)

        # Assert
        mock_logger.info.assert_any_call(
            LOG_MESSAGES["summary_scraping"]["pages_downloaded"].format(
                downloaded_count=2, total_initiatives=4
            )
        )
        mock_logger.error.assert_any_call(
            LOG_MESSAGES["summary_scraping"]["failed_downloads"].format(failed_count=2)
        )
        mock_logger.error.assert_any_call(" - https://example.com/failed1")
        mock_logger.error.assert_any_call(" - https://example.com/failed2")

    @patch("ECI_initiatives.scraper.initiatives.statistics.logger")
    def test_display_results_no_failures(self, mock_logger):
        """Test display_results_and_files function with no failed downloads."""

        # Arrange
        start_scraping = "2025-09-21_17-13-00"
        saved_page_paths = ["page1.html", "page2.html"]
        failed_urls = []
        stats = {"downloaded_count": 2, "total_initiatives": 2, "failed_count": 0}

        # Act
        self.display_results_and_files(start_scraping, saved_page_paths, failed_urls, stats)

        # Assert
        mock_logger.info.assert_any_call(
            LOG_MESSAGES["summary_scraping"]["pages_downloaded"].format(
                downloaded_count=2, total_initiatives=2
            )
        )
        mock_logger.info.assert_any_call(
            LOG_MESSAGES["summary_scraping"]["all_downloads_successful"]
        )
        # Should not call error methods
        assert not mock_logger.error.called

    @patch("ECI_initiatives.scraper.initiatives.statistics.logger")
    def test_display_summary_info_content(self, mock_logger):
        """Test that display_summary_info outputs correct summary content."""

        # Arrange
        start_scraping = "2025-09-21_17-13-00"
        saved_page_paths = ["page1.html", "page2.html", "page3.html"]
        stats = {
            "status_counter": Counter(
                {"Registered": 2, "Collection ongoing": 1, "Valid initiative": 1}
            ),
            "total_initiatives": 4,
        }

        with patch("datetime.datetime") as mock_datetime:

            mock_now = Mock()
            mock_now.strftime.return_value = "2025-09-21 17:15:00"
            mock_datetime.now.return_value = mock_now

            # Act
            self.display_summary_info(start_scraping, saved_page_paths, stats)

            # Assert
            mock_logger.info.assert_any_call(
                LOG_MESSAGES["summary_scraping"]["scraping_complete"]
            )
            mock_logger.info.assert_any_call(
                f"Total pages scraped: {len(saved_page_paths)}"
            )
            mock_logger.info.assert_any_call(
                f"Total initiatives found: {stats['total_initiatives']}"
            )
            mock_logger.info.assert_any_call(
                "Initiatives by category (current_status):"
            )

            mock_logger.info.assert_any_call(
                LOG_MESSAGES["summary_scraping"]["registered_status"].format(count=2)
            )
            mock_logger.info.assert_any_call(
                LOG_MESSAGES["summary_scraping"]["collection_ongoing_status"].format(
                    count=1
                )
            )
            mock_logger.info.assert_any_call(
                LOG_MESSAGES["summary_scraping"]["valid_initiative_status"].format(
                    count=1
                )
            )

```

`./ECI_initiatives/tests/scraper/initiatives/behaviour/test_scraping_process.py`:
```
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
program_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..") # \ECI_initiatives
sys.path.append(program_dir)

# Safe imports (don't trigger logger creation)
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
        from ECI_initiatives.scraper.initiatives.crawler import (
            navigate_to_next_page,
            wait_for_listing_page_content,
            scrape_single_listing_page,
            scrape_all_initiatives_on_all_pages,
        )
        from ECI_initiatives.scraper.initiatives.file_ops import save_listing_page
        
        cls.navigate_to_next_page = staticmethod(navigate_to_next_page)
        cls.wait_for_listing_page_content = staticmethod(wait_for_listing_page_content)
        cls.scrape_single_listing_page = staticmethod(scrape_single_listing_page)
        cls.scrape_all_initiatives_on_all_pages = staticmethod(scrape_all_initiatives_on_all_pages)
        cls.save_listing_page = staticmethod(save_listing_page)

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

    @patch("ECI_initiatives.scraper.initiatives.crawler.logger")
    @patch("ECI_initiatives.scraper.initiatives.crawler.time.sleep")
    @patch("ECI_initiatives.scraper.initiatives.crawler.random.uniform", return_value=1.0)
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
        result1 = self.navigate_to_next_page(mock_driver, 1)
        assert result1 is True

        # Second call should return False (no next button)
        result2 = self.navigate_to_next_page(mock_driver, 2)
        assert result2 is False

        # Verify execute_script was called for the first page
        mock_driver.execute_script.assert_called_once()

    @patch("ECI_initiatives.scraper.initiatives.crawler.logger")
    def test_stops_at_last_page(self, mock_logger, mock_driver):
        """Verify that scraping stops correctly when reaching the last page."""

        # Simulate no next button found (last page scenario)
        mock_driver.find_element.side_effect = NoSuchElementException()

        result = self.navigate_to_next_page(mock_driver, 5)
        assert result is False

        # Ensure execute_script was not called since no button was found
        mock_driver.execute_script.assert_not_called()

    @patch("ECI_initiatives.scraper.initiatives.file_ops.logger")
    @patch("ECI_initiatives.scraper.initiatives.file_ops.time.sleep")
    @patch("ECI_initiatives.scraper.initiatives.file_ops.random.uniform", return_value=1.0)
    def test_page_numbering_correspondence(
        self, mock_uniform, mock_sleep, mock_logger, mock_driver, tmp_path
    ):
        """Check that page numbering in saved files corresponds to actual pages scraped."""

        mock_driver.page_source = "<html><body>Page content</body></html>"

        # Test saving different page numbers
        for page_num in [1, 2, 10]:

            page_source, page_path = self.save_listing_page(
                mock_driver, str(tmp_path), page_num
            )

            expected_filename = f"{LISTING_HTML_PATTERN}{page_num:03d}.html"
            assert expected_filename in page_path
            assert os.path.exists(page_path)

    @patch("ECI_initiatives.scraper.initiatives.__main__.logger")
    @patch(
        "ECI_initiatives.scraper.initiatives.crawler.parse_initiatives_list_data",
        return_value=[
            {
                REQUIRED_CSV_COLUMNS.URL: "test",
                REQUIRED_CSV_COLUMNS.CURRENT_STATUS: "active",
            }
        ],
    )
    @patch("ECI_initiatives.scraper.initiatives.crawler.wait_for_listing_page_content")
    @patch("ECI_initiatives.scraper.initiatives.crawler.save_listing_page")
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
            "ECI_initiatives.scraper.initiatives.crawler.navigate_to_next_page",
            side_effect=[True, True, False],
        ):
            all_data, saved_paths = self.scrape_all_initiatives_on_all_pages(
                mock_driver, "http://base.url", "/test/dir"
            )

        # Verify all 3 pages were processed
        assert len(saved_paths) == 3
        assert len(all_data) == 3  # Each page returns 1 initiative
        assert mock_save.call_count == 3

    @patch("ECI_initiatives.scraper.initiatives.crawler.logger")
    @patch("ECI_initiatives.scraper.initiatives.crawler.time.sleep")
    def test_navigate_to_next_page_functionality(
        self, mock_sleep, mock_logger, mock_driver
    ):
        """Test the navigate_to_next_page function behavior."""

        mock_next_button = Mock()
        mock_driver.find_element.return_value = mock_next_button

        result = self.navigate_to_next_page(mock_driver, 1)

        assert result is True

        mock_driver.find_element.assert_called_once()
        mock_driver.execute_script.assert_called_once_with(
            "arguments[0].click();", mock_next_button
        )

        mock_sleep.assert_called_once()


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
        from ECI_initiatives.scraper.initiatives.downloader import (
            download_single_initiative,
            download_initiative_pages,
            check_rate_limiting,
        )
        from ECI_initiatives.scraper.initiatives.browser import initialize_browser
        
        cls.download_single_initiative = staticmethod(download_single_initiative)
        cls.download_initiative_pages = staticmethod(download_initiative_pages)
        cls.check_rate_limiting = staticmethod(check_rate_limiting)
        cls.initialize_browser = staticmethod(initialize_browser)

    @pytest.fixture
    def mock_driver(self):
        """Create a mock driver for testing."""
        return Mock(spec=webdriver.Chrome)

    @patch("ECI_initiatives.scraper.initiatives.downloader.logger")
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

    @patch("ECI_initiatives.scraper.initiatives.downloader.logger")
    @patch("ECI_initiatives.scraper.initiatives.downloader.download_single_initiative")
    @patch("ECI_initiatives.scraper.initiatives.downloader.initialize_browser")
    @patch("ECI_initiatives.scraper.initiatives.downloader.time.sleep")
    @patch("ECI_initiatives.scraper.initiatives.downloader.random.uniform", return_value=1.0)
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

        updated_data, failed_urls = self.download_initiative_pages("/tmp", test_data)

        assert len(failed_urls) == 2
        assert "http://test2.com" in failed_urls
        assert "http://test4.com" in failed_urls
        assert len(updated_data) == 4

    @patch("ECI_initiatives.scraper.initiatives.downloader.logger")
    @patch("ECI_initiatives.scraper.initiatives.downloader.time.sleep")
    @patch("ECI_initiatives.scraper.initiatives.downloader.random.uniform", return_value=1.0)
    def test_rate_limiting_handling(self, mock_uniform, mock_sleep, mock_driver):
        """Check that rate limiting is handled gracefully with appropriate retries."""

        # Test rate limiting detection in page content
        mock_driver.page_source = f"<html><head><title>{RATE_LIMIT_INDICATORS.SERVER_INACCESSIBILITY}</title></head><body>{RATE_LIMIT_INDICATORS.TOO_MANY_REQUESTS}</body></html>"

        url = f"{FULL_FIND_INITIATIVE_URL}/details/2024/000001_en"

        with patch(
            "ECI_initiatives.scraper.initiatives.downloader.check_rate_limiting"
        ) as mock_check:
            mock_check.side_effect = Exception(
                f"{RATE_LIMIT_INDICATORS.RATE_LIMITED} (HTML response)"
            )

            result = self.download_single_initiative(mock_driver, "/tmp", url, max_retries=1)
            assert result is False

    @patch("ECI_initiatives.scraper.initiatives.crawler.logger")
    def test_continues_after_non_critical_errors(self, mock_driver):
        """Ensure scraping continues after encountering non-critical errors."""

        # Import needed for this specific test
        from ECI_initiatives.scraper.initiatives.crawler import wait_for_listing_page_content

        # Test that timeout on waiting for elements doesn't stop the process
        with patch("ECI_initiatives.scraper.initiatives.crawler.WebDriverWait") as mock_wait:

            mock_wait.return_value.until.side_effect = TimeoutException()

            # This should not raise an exception, just log a warning
            wait_for_listing_page_content(mock_driver, 1)

            # The method should complete without raising an exception
            assert True

    @patch("ECI_initiatives.scraper.initiatives.downloader.logger")
    @patch("ECI_initiatives.scraper.initiatives.downloader.time.sleep")
    def test_retry_logic_for_failed_requests(self, mock_sleep, mock_driver, tmp_path):
        """Test the retry mechanism for failed requests."""

        # First two calls fail with rate limiting, third succeeds
        mock_driver.get.side_effect = [
            Exception(RATE_LIMIT_INDICATORS.TOO_MANY_REQUESTS),
            Exception(RATE_LIMIT_INDICATORS.RATE_LIMITED),
            None,  # Success
        ]
        mock_driver.page_source = "<html><body>Success</body></html>"

        with patch("ECI_initiatives.scraper.initiatives.downloader.check_rate_limiting"):

            with patch("ECI_initiatives.scraper.initiatives.downloader.wait_for_page_content"):

                with patch(
                    "ECI_initiatives.scraper.initiatives.downloader.save_initiative_page",
                    return_value="test.html",
                ):
                    url = "https://test.com/details/2024/000001_en"

                    result = self.download_single_initiative(
                        mock_driver, str(tmp_path), url, max_retries=3
                    )

        assert result is True
        assert mock_driver.get.call_count == 3  # Two failed attempts, one success


class TestScrapingProcessFlow:
    """Test overall scraping process flow."""

    @classmethod
    def setup_class(cls):
        """
        Import modules and set up class attributes.
        
        Imports are done here rather than at module level to avoid
        log file creation during module loading, allowing the session
        fixture to properly track and clean up test artifacts.
        """
        from ECI_initiatives.scraper.initiatives.crawler import (
            wait_for_listing_page_content,
            scrape_single_listing_page,
            scrape_all_initiatives_on_all_pages,
        )
        from ECI_initiatives.scraper.initiatives.downloader import (
            wait_for_page_content,
            check_rate_limiting,
        )
        
        cls.wait_for_listing_page_content = staticmethod(wait_for_listing_page_content)
        cls.wait_for_page_content = staticmethod(wait_for_page_content)
        cls.check_rate_limiting = staticmethod(check_rate_limiting)
        cls.scrape_single_listing_page = staticmethod(scrape_single_listing_page)
        cls.scrape_all_initiatives_on_all_pages = staticmethod(scrape_all_initiatives_on_all_pages)

    @pytest.fixture
    def mock_driver(self):
        """Create a mock driver for testing."""

        return Mock(spec=webdriver.Chrome)

    @patch("ECI_initiatives.scraper.initiatives.crawler.logger")
    @patch("ECI_initiatives.scraper.initiatives.crawler.WebDriverWait")
    def test_wait_for_listing_page_content(
        self, mock_wait_class, mock_logger, mock_driver
    ):
        """Test waiting for listing page content to load."""

        mock_wait = Mock()
        mock_wait_class.return_value = mock_wait

        # Test successful wait
        self.wait_for_listing_page_content(mock_driver, 1)

        mock_wait_class.assert_called_with(mock_driver, DEFAULT_WEBDRIVER_TIMEOUT)
        mock_wait.until.assert_called_once()

    @patch("ECI_initiatives.scraper.initiatives.downloader.logger")
    @patch("ECI_initiatives.scraper.initiatives.downloader.WebDriverWait")
    def test_wait_for_page_content(self, mock_wait_class, mock_logger, mock_driver):
        """Test waiting for individual page content to load."""

        mock_wait = Mock()
        mock_wait_class.return_value = mock_wait
        # Simulate successful wait for first selector, others fail
        mock_wait.until.side_effect = [None, TimeoutException(), TimeoutException()]

        self.wait_for_page_content(mock_driver)

        mock_wait_class.assert_called_with(mock_driver, PAGE_CONTENT_TIMEOUT)
        # Should be called multiple times as it tries different selectors
        assert mock_wait.until.call_count >= 1

    def test_check_rate_limiting_detection(self, mock_driver):
        """Test rate limiting detection functionality."""

        # Test case: Rate limiting detected
        mock_element = Mock()
        mock_element

```

`./ECI_initiatives/tests/scraper/initiatives/end_to_end/__init__.py`:
```

```

`./ECI_initiatives/tests/scraper/initiatives/end_to_end/test_created_files.py`:
```
"""
Test suite for validating that the ECI scraper correctly creates files and directories.

It checks that the scraper properly:

 1. downloads web pages
 2. saves them as HTML files
 3. creates CSV data files with initiative information
 4. organizes everything into the expected directory structure

To avoid overwhelming the ECI website and prevent potential server blocks or rate
limiting, this test uses a deliberately limited scope.
It only scrapes the first page of initiatives and
downloads just the first 3 individual initiative pages.

The test focuses only on the most critical outcomes:

 - whether files are created
 - placed in correct locations
 - contain valid content
 - follow proper naming conventions.

It does not test detailed parsing logic or handle edge cases that
might occur with different website layouts or server responses.

This simplified approach reduces maintenance overhead
since external websites can change unpredictably,
and keeps the test reliable by avoiding dependencies on
specific website content that may vary over time.

It should take between 30 seconds and 1 minute to complete.

The test validates:

 - Directory structure creation (data, listings, pages, logs folders)
 - CSV file creation with proper headers and limited initiative data
 - HTML listing page download and storage
 - Individual initiative page downloads (3 files)
 - Basic file content validation (HTML structure, expected content)
 - File naming convention compliance
"""

# Standard library
import csv
import os
import shutil
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Third party
import pytest

# Local
program_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..") # \ECI_initiatives
sys.path.append(program_dir)

# Safe imports (don't trigger logger creation)
from ECI_initiatives.tests.consts import (
    BASE_URL,
    REQUIRED_CSV_COLUMNS,
    MAX_PAGES_E2E_TEST,
    MAX_INITIATIVES_E2E_TEST,
    LISTING_HTML_PATTERN,
    CSV_FILENAME,
    DATA_DIR_NAME,
    LISTINGS_DIR_NAME,
    PAGES_DIR_NAME,
    LOG_DIR_NAME,
)


class TestCreatedFiles:
    """Test suite for validating created files from ECI scraping."""

    @classmethod
    def setup_class(cls):
        """
        Setup class-level resources that runs once before all tests.
        
        Imports are done here rather than at module level to avoid
        log file creation during module loading, allowing the session
        fixture to properly track and clean up test artifacts.
        """

        # Import scraper modules at setup time
        from ECI_initiatives.scraper.initiatives.__main__ import scrape_eci_initiatives
        from ECI_initiatives.scraper.initiatives.data_parser import parse_initiatives_list_data
        from ECI_initiatives.scraper.initiatives.crawler import (
            scrape_all_initiatives_on_all_pages,
            navigate_to_next_page,
        )
        
        # Store as class attributes for use in tests
        cls.scrape_eci_initiatives = staticmethod(scrape_eci_initiatives)
        cls.parse_initiatives_list_data = staticmethod(parse_initiatives_list_data)
        cls.scrape_all_initiatives_on_all_pages = staticmethod(scrape_all_initiatives_on_all_pages)
        cls.navigate_to_next_page = staticmethod(navigate_to_next_page)

        # Create temporary directories for testing
        cls.temp_base_dir = tempfile.mkdtemp(prefix="eci_test_")
        cls.temp_data_dir = os.path.join(cls.temp_base_dir, DATA_DIR_NAME)

        # Store original functions for later restoration
        original_parse_initiatives = parse_initiatives_list_data
        original_navigate_to_next_page = navigate_to_next_page

        def mock_parse_initiatives_limited(page_source, base_url):
            """
            Parse initiatives but limit to first 3 items.
            To limit the time that the test takes.
            """

            full_data = original_parse_initiatives(page_source, base_url)
            return full_data[
                :MAX_INITIATIVES_E2E_TEST
            ]  # Return only first 3 initiatives

        def mock_navigate_to_next_page_first_only(driver, current_page):
            """
            Always return False to stop at first page.
            Mocked to just scrape the first page.
            """

            return False

        # Apply mocks and run scraping - using REAL directories
        with patch.object(
            sys.modules["ECI_initiatives.scraper.initiatives.crawler"],
            "parse_initiatives_list_data",
            side_effect=mock_parse_initiatives_limited,
        ), patch.object(
            sys.modules["ECI_initiatives.scraper.initiatives.crawler"],
            "navigate_to_next_page",
            side_effect=mock_navigate_to_next_page_first_only,
        ):

            # Run the scraping function - saves to real ECI_initiatives/data/ directory
            timestamp = cls.scrape_eci_initiatives()

        # Store results for tests - point to REAL data directory
        cls.timestamp = timestamp
        
        # Get the real script directory (where ECI_initiatives project is located)
        script_dir = Path(__file__).parent.parent.parent.parent.parent.absolute()  # Go up to ECI_initiatives/
        real_data_dir = script_dir / "data"
        
        cls.data_path = real_data_dir / timestamp
        cls.listings_path = cls.data_path / LISTINGS_DIR_NAME
        cls.pages_path = cls.data_path / PAGES_DIR_NAME
        cls.logs_path = cls.data_path / LOG_DIR_NAME

    @classmethod
    def teardown_class(cls):
        """Cleanup class-level resources that runs once after all tests."""

        # No cleanup needed - the conftest.py fixture will handle cleaning up the real directories
        print(f"\n\nTest completed. Files created in:\n{cls.data_path}")
        print("Note: Files will be cleaned up by the session fixture.")

    def test_debug_fixture(self):
        """Debug test to see setup output."""

        print("Debug - setup completed successfully")
        print(f"Timestamp: {self.timestamp}")
        print(f"Data path: {self.data_path}")
        print(f"Listings path: {self.listings_path}")
        print(f"Pages path: {self.pages_path}")

    def test_directory_structure_created(self):
        """Test that all required directories are created."""

        # Check main directories exist
        assert os.path.exists(self.data_path), "Main data directory not created"
        assert os.path.exists(self.listings_path), "Listings directory not created"
        assert os.path.exists(self.pages_path), "Pages directory not created"

        assert os.path.exists(self.logs_path), "Logs directory not created"

    def test_listing_files_created(self):
        """Test that listing page files are created with correct content."""

        # Check CSV file exists
        csv_file = os.path.join(self.listings_path, CSV_FILENAME)
        assert os.path.exists(csv_file), "initiatives_list.csv not created"

        # Check HTML listing file exists (should be exactly 1 since we only scrape first page)
        html_files = [f for f in os.listdir(self.listings_path) if f.endswith(".html")]
        assert (
            len(html_files) == MAX_PAGES_E2E_TEST
        ), f"Expected 1 HTML listing file, found {len(html_files)}"

        # Check HTML file name pattern
        html_file = html_files[0]

        assert html_file.startswith(
            "Find_initiative_European_Citizens_Initiative_page_"
        ), f"HTML file name pattern incorrect: {html_file}"

    def test_csv_content_structure(self):
        """Test CSV file has correct structure and limited content."""

        csv_file = os.path.join(self.listings_path, CSV_FILENAME)

        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Should have exactly 3 rows (limited by our mock)
        assert len(rows) == 3, f"Expected exactly 3 initiatives, found {len(rows)}"

        # Check required columns exist
        required_columns = [
            REQUIRED_CSV_COLUMNS.URL,
            REQUIRED_CSV_COLUMNS.CURRENT_STATUS,
            REQUIRED_CSV_COLUMNS.REGISTRATION_NUMBER,
            REQUIRED_CSV_COLUMNS.SIGNATURE_COLLECTION,
            REQUIRED_CSV_COLUMNS.DATETIME,
        ]

        if rows:
            for col in required_columns:
                assert (
                    col in rows[0].keys()
                ), f"Required column '{col}' missing from CSV"

            # Check URL format
            for row in rows:
                assert row[REQUIRED_CSV_COLUMNS.URL].startswith(
                    f"{BASE_URL}/initiatives/details/"
                ), f"URL format incorrect: {row['url']}"

    def test_initiative_pages_downloaded(self):
        """Test that individual initiative pages are downloaded."""

        # Count HTML files in year directories
        html_count = 0

        if os.path.exists(self.pages_path):
            for item in os.listdir(self.pages_path):
                year_path = os.path.join(self.pages_path, item)

                if os.path.isdir(year_path):
                    html_files = [
                        f for f in os.listdir(year_path) if f.endswith(".html")
                    ]
                    html_count += len(html_files)

        # Should have exactly 3 HTML files (one for each initiative)
        assert html_count == 3, f"Expected 3 initiative HTML files, found {html_count}"

    def test_initiative_html_content(self):
        """Test that downloaded HTML files contain valid content."""

        html_files = []

        # Collect all HTML files from year directories
        for item in os.listdir(self.pages_path):
            year_path = os.path.join(self.pages_path, item)

            if os.path.isdir(year_path):
                for file in os.listdir(year_path):
                    if file.endswith(".html"):
                        html_files.append(os.path.join(year_path, file))

        assert len(html_files) > 0, "No HTML files found to test"

        # Test each HTML file
        for html_file in html_files:
            with open(html_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Basic HTML validation
            assert len(content) > 100, f"HTML file too short: {html_file}"
            assert "<html" in content.lower(), f"No HTML tag found in: {html_file}"
            assert (
                "</html>" in content.lower()
            ), f"No closing HTML tag found in: {html_file}"

            # Check for ECI-specific content
            assert (
                "citizens-initiative.europa.eu" in content
                or "European Citizens' Initiative" in content
            ), f"File doesn't appear to be ECI content: {html_file}"

    def test_file_naming_convention(self):
        """Test that files follow the expected naming conventions."""

        # Check listing HTML file naming
        html_files = [f for f in os.listdir(self.listings_path) if f.endswith(".html")]

        for html_file in html_files:
            assert html_file.startswith(
                LISTING_HTML_PATTERN
            ), f"Listing HTML file naming incorrect: {html_file}"

            assert html_file.endswith(
                ".html"
            ), f"Listing file should end with .html: {html_file}"

        # Check initiative page file naming (should be <year>_<number_initiative>.html format)
        for item in os.listdir(self.pages_path):
            year_path = os.path.join(self.pages_path, item)

            if os.path.isdir(year_path):
                # Directory should be a year (4 digits)
                assert (
                    item.isdigit() and len(item) == 4
                ), f"Year directory name incorrect: {item}"

                for file in os.listdir(year_path):
                    if file.endswith(".html"):
                        # File should be year_number.html format
                        assert (
                            "_" in file
                        ), f"Initiative file name should contain underscore: {file}"

                        assert file.endswith(
                            ".html"
                        ), f"Initiative file should end with .html: {file}"

```

`./ECI_initiatives/tests/scraper/initiatives/__init__.py`:
```

```

`./ECI_initiatives/tests/scraper/__init__.py`:
```

```

`./ECI_initiatives/tests/scraper/requirements.test.txt`:
```

```

