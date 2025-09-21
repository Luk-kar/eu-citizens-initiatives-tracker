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
CSV_FILE_PATH = os.path.join(INITIATIVES_HTML_DIR, "eci_status_initiatives.csv")

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
            expected_data = {row["example_url"]: row["status"] for row in reader}

        # Load test listing page
        first_page_path = os.path.join(LISTINGS_HTML_DIR, "first_page.html")

        with open(first_page_path, "r", encoding="utf-8") as f:
            page_source = f.read()

        # Extract data using main module function
        initiative_data = parse_initiatives_list_data(page_source, BASE_URL)

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

    def test_initiative_count_matches_website(self):
        """Compare the number of initiatives found against manual count on the website."""
        pass

    def test_all_listing_pages_processed(self):
        """Verify that all pages of listings are processed (pagination handling)."""
        pass

    def test_status_distribution_accuracy(self):
        """Check that initiative counts by status match expected distributions."""
        pass

    def test_all_available_fields_extracted(self):
        """Ensure all initiative fields are extracted when available on source pages."""
        pass
