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

from ECI_initiatives.scraper.__main__ import (
    save_and_download_initiatives,
)
from ECI_initiatives.scraper.data_parser import (
    parse_initiatives_list_data,
)
from ECI_initiatives.scraper.crawler import (
    scrape_all_initiatives_on_all_pages,
)

# Consts

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
    with patch("ECI_initiatives.scraper.data_parser.logger"):
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

    @patch("ECI_initiatives.scraper.__main__.download_initiative_pages")
    @patch("ECI_initiatives.scraper.__main__.logger")
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
            save_and_download_initiatives(list_dir, pages_dir, test_initiative_data)

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

    @patch("ECI_initiatives.scraper.__main__.logger")
    @patch("ECI_initiatives.scraper.__main__.download_initiative_pages")
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
            save_and_download_initiatives(
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

    def test_initiative_count_matches_reference(self, parsed_test_data, reference_data):
        """Compare initiative count with reference data."""
        assert len(parsed_test_data) >= len(
            reference_data
        ), f"Found {len(parsed_test_data)} initiatives, expected at least {len(reference_data)}"

    @patch("ECI_initiatives.scraper.browser.initialize_browser")
    @patch("ECI_initiatives.scraper.__main__.logger")
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
            "ECI_initiatives.scraper.crawler.wait_for_listing_page_content"
        ), patch(
            "ECI_initiatives.scraper.file_ops.save_listing_page"
        ) as mock_save, patch(
            "ECI_initiatives.scraper.data_parser.parse_initiatives_list_data"
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
                all_data, saved_paths = scrape_all_initiatives_on_all_pages(
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

                initiatives = parse_initiatives_list_data(page_content, BASE_URL)

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
