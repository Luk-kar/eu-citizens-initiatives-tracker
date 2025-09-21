"""Tests for data extraction and accuracy validation."""

import pytest
import csv
import os
import tempfile
import re
import copy
from typing import List, Dict
from unittest.mock import patch, MagicMock, mock_open, call
from bs4 import BeautifulSoup
import datetime
from collections import Counter


# Test data directory path relative to this test file
TEST_DATA_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "example_htmls"
)
INITIATIVES_HTML_DIR = os.path.join(TEST_DATA_DIR, "initiatives")
LISTINGS_HTML_DIR = os.path.join(TEST_DATA_DIR, "listings")
CSV_FILE_PATH = os.path.join(LISTINGS_HTML_DIR, "initiatives_list.csv")

# Base URL for testing
BASE_URL = "https://citizens-initiative.europa.eu"

# Import the functions we want to test
import sys

program_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")

print(program_dir)
sys.path.append(program_dir)

from ECI_initiatives.__main__ import (
    save_and_download_initiatives,
    parse_initiatives_list_data,
    scrape_all_initiatives_on_all_pages,
)


class TestCSVDataValidation:
    """Test CSV data validation functionality."""

    @patch("ECI_initiatives.__main__.download_initiative_pages")
    @patch("ECI_initiatives.__main__.logger")
    def test_csv_created_with_correct_headers(self, mock_logger, mock_download_pages):
        """
        Verify that initiatives_list.csv is created with correct headers:
        url, current_status, registration_number, signature_collection, datetime.
        """

        # Sample initiative data
        test_initiative_data = [
            {
                "url": "https://citizens-initiative.europa.eu/initiatives/details/2019/000007_en",
                "current_status": "Answered initiative",
                "registration_number": "ECI(2019)000007",
                "signature_collection": "Collection completed",
                "datetime": "",
            }
        ]

        # Mock download_initiative_pages to return the same data with updated datetime
        updated_data = copy.deepcopy(test_initiative_data)
        updated_data[0]["datetime"] = "2025-09-21 11:24:00"

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
                    "url",
                    "current_status",
                    "registration_number",
                    "signature_collection",
                    "datetime",
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
                    data_row[0] == test_initiative_data[0]["url"]
                ), "URL not correctly written to CSV:\n" + str(data_row[0])

    @patch("ECI_initiatives.__main__.logger")
    def test_url_format_validation(self, mock_logger):
        """Validate that all extracted URLs follow the expected format (/initiatives/details/YYYY/number)."""

        # Load test HTML file to parse
        first_page_path = os.path.join(LISTINGS_HTML_DIR, "first_page.html")

        with open(first_page_path, "r", encoding="utf-8") as f:
            page_source = f.read()

        # Parse the page using the main module function
        initiative_data = parse_initiatives_list_data(page_source, BASE_URL)

        # URL pattern: /initiatives/details/YYYY/NNNNNN_lang
        url_pattern = r"https://citizens-initiative\.europa\.eu/initiatives/details/\d{4}/\d{6}_[a-z]{2}"

        for initiative in initiative_data:

            url = initiative["url"]

            assert re.match(
                url_pattern, url
            ), f"URL does not match expected format:\n{url}"

    @patch("ECI_initiatives.__main__.logger")
    def test_extracted_data_matches_web_pages(self, mock_logger):
        """
        Check that extracted data fields (status, registration numbers)
        match what's visible on the actual web pages.
        """

        # Load the reference CSV to get expected data
        with open(CSV_FILE_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            expected_data = {row["url"]: row["current_status"] for row in reader}

        # Load test listing page
        first_page_path = os.path.join(LISTINGS_HTML_DIR, "first_page.html")

        with open(first_page_path, "r", encoding="utf-8") as f:
            page_source = f.read()

        # Extract data using main module function
        initiative_data = parse_initiatives_list_data(page_source, BASE_URL)

        print(initiative_data)

        # Compare extracted status with expected (if URLs match)
        for initiative in initiative_data:

            url = initiative["url"]

            if url in expected_data:

                expected_status = expected_data[url]
                extracted_status = initiative["current_status"]

                assert (
                    extracted_status == expected_status
                ), f"Status mismatch for {url}: expected '{expected_status}', got '{extracted_status}'"

    @patch("ECI_initiatives.__main__.logger")
    @patch("ECI_initiatives.__main__.download_initiative_pages")
    def test_no_duplicate_initiatives(self, mock_download_pages, mock_logger):
        """Ensure no duplicate initiatives are recorded in the CSV when scraping produces duplicates."""

        # Create test data with duplicates (simulating what parse_initiatives_list_data might return)
        test_initiative_data_with_duplicates = [
            {
                "url": "https://citizens-initiative.europa.eu/initiatives/details/2019/000007_en",
                "current_status": "Answered initiative",
                "registration_number": "ECI(2019)000007",
                "signature_collection": "Collection completed",
                "datetime": "",
            },
            {
                "url": "https://citizens-initiative.europa.eu/initiatives/details/2024/000004_en",
                "current_status": "Valid initiative",
                "registration_number": "ECI(2024)000004",
                "signature_collection": "Collection closed",
                "datetime": "",
            },
            {
                "url": "https://citizens-initiative.europa.eu/initiatives/details/2019/000007_en",  # DUPLICATE
                "current_status": "Answered initiative",
                "registration_number": "ECI(2019)000007",
                "signature_collection": "Collection completed",
                "datetime": "",
            },
        ]

        # Mock download_initiative_pages to return data without duplicates
        unique_data = []
        seen_urls = set()

        for item in test_initiative_data_with_duplicates:

            if item["url"] not in seen_urls:

                unique_data.append(item.copy())
                seen_urls.add(item["url"])

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
            csv_urls = [row["url"] for row in csv_data]
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


class TestDataCompleteness:
    """Test data completeness and accuracy."""

    @patch("ECI_initiatives.__main__.logger")
    def test_initiative_count_matches_website(self, mock_logger):
        """Compare the number of initiatives found against manual count on the website."""

        # Load test listing pages and count unique initiatives
        all_initiatives = []

        for page_file in ["first_page.html", "last_page.html"]:
            page_path = os.path.join(LISTINGS_HTML_DIR, page_file)

            with open(page_path, "r", encoding="utf-8") as f:
                page_source = f.read()

            initiative_data = parse_initiatives_list_data(page_source, BASE_URL)

            # Add URLs to set to avoid duplicates
            for initiative in initiative_data:
                all_initiatives.append(initiative["url"])

        total_initiatives = len(all_initiatives)

        with open(CSV_FILE_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            expected_count = sum(1 for _ in reader)

        assert (
            total_initiatives >= expected_count
        ), f"Found {total_initiatives} unique initiatives, expected at least {expected_count}"

    @patch("ECI_initiatives.__main__.initialize_browser")
    @patch("ECI_initiatives.__main__.logger")
    def test_all_listing_pages_processed(self, mock_logger, mock_browser):
        """Verify that all pages of listings are processed (pagination handling)."""

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

        # Mock find_element for next button - return button for first 2 pages, raise exception for 3rd
        def mock_find_element_side_effect(*args, **kwargs):
            """
            Mock the browser's find_element behavior for pagination.

            Returns a mock button element for the first 2 calls (pages 1-2 have Next buttons),
            then raises an exception on the 3rd call (page 3 has no Next button).
            This simulates reaching the last page of results.
            """

            if mock_find_element_side_effect.call_count <= 2:

                mock_button = MagicMock()
                return mock_button

            else:
                raise Exception("No next button found")

        mock_find_element_side_effect.call_count = 0

        def increment_and_side_effect(*args, **kwargs):
            """
            Wrapper function that increments the call counter and delegates to the main side effect.

            This tracks how many times find_element has been called to simulate
            the pagination logic checking for Next buttons on each page.
            """

            mock_find_element_side_effect.call_count += 1

            return mock_find_element_side_effect(*args, **kwargs)

        mock_driver.find_element.side_effect = increment_and_side_effect

        # Mock page source updates
        def update_page_source():
            """
            Update the mock driver's page_source to simulate navigating to the next page.

            Changes the HTML content to the next page in the sequence when the
            Next button is clicked, simulating how a real browser would load new content.
            """

            if mock_find_element_side_effect.call_count <= len(page_sources):

                mock_driver.page_source = page_sources[
                    mock_find_element_side_effect.call_count - 1
                ]

        mock_driver.execute_script.side_effect = (
            lambda script, element: update_page_source()
        )

        # Mock other required methods
        with patch("ECI_initiatives.__main__.wait_for_listing_page_content"), patch(
            "ECI_initiatives.__main__.save_listing_page"
        ) as mock_save, patch(
            "ECI_initiatives.__main__.parse_initiatives_list_data"
        ) as mock_parse, patch(
            "time.sleep"
        ):

            mock_save.return_value = ("", "test_path")
            mock_parse.return_value = [
                {
                    "url": "test",
                    "current_status": "",
                    "registration_number": "",
                    "signature_collection": "",
                    "datetime": "",
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
                    mock_driver.find_element.call_count == 3
                ), f"Should have checked for next button {expected_page_count} times"

    @patch("ECI_initiatives.__main__.logger")
    def test_all_available_fields_extracted(self, mock_logger):
        """Ensure all initiative fields are extracted when available on source pages."""

        def load_expected_statuses():
            """Load status distribution from reference CSV file."""

            with open(CSV_FILE_PATH, "r", encoding="utf-8") as f:

                reader = csv.DictReader(f)
                return Counter(row["current_status"] for row in reader)

        def parse_test_pages():
            """Parse all test HTML pages and extract statuses."""

            all_statuses = []

            for page_file in ["first_page.html", "last_page.html"]:

                page_path = os.path.join(LISTINGS_HTML_DIR, page_file)

                with open(page_path, "r", encoding="utf-8") as f:
                    page_content = f.read()

                initiatives = parse_initiatives_list_data(page_content, BASE_URL)

                # Extract non-empty statuses
                page_statuses = [
                    init["current_status"]
                    for init in initiatives
                    if init["current_status"]
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
