"""
End-to-end test suite for validating that the followup website
scraper correctly downloads and saves followup website pages.

This test:
- Uses a real CSV file with response data
- Extracts a followup website URL from the CSV (random choice from existing)
- Downloads the actual page from the web
- Validates file creation, structure, and content

The test focuses on critical outcomes:
- Files created in correct locations
- Valid content with proper HTML structure
- Proper naming conventions
- Correct year-based directory structure

Expected execution time: 15-30 seconds (downloads 1 real page)
"""

# Standard library
import csv
import shutil
import os
from pathlib import Path
from unittest.mock import patch
import random

# Third party
import pytest
from bs4 import BeautifulSoup

# Local imports
from ECI_initiatives.scraper.responses_followup_website import __main__ as followup_main
from ECI_initiatives.scraper.responses_followup_website.downloader import (
    FollowupWebsiteDownloader,
)
from ECI_initiatives.tests.consts import (
    DATA_DIR_NAME,
    LOG_DIR_NAME,
)

# Constants for followup website tests
RESPONSES_FOLLOWUP_WEBSITE_DIR_NAME = "responses_followup_website"
FOLLOWUP_WEBSITE_FILENAME_PATTERN = r"^\d{4}_\d{6}_en\.html$"

# Test data file location
TEST_CSV_FILENAME = "eci_responses_2025-11-17_14-50-27.csv"
tests_dir = Path(__file__).parent.parent.parent.parent.absolute()
source_csv = tests_dir / "data" / "example_htmls" / "responses" / TEST_CSV_FILENAME


def validate_test_csv_file(source_csv: Path, tests_dir: Path) -> None:
    """
    Validate test CSV file existence, format, structure, and content.

    Performs comprehensive validation of the test CSV file to ensure it meets
    all requirements for the followup website end-to-end test:

    1. File existence and type validation
    2. File extension validation (.csv required)
    3. CSV structure validation (parseable format)
    4. Required column validation ('followup_dedicated_website')
    5. Content validation (at least one non-empty URL)

    Args:
        source_csv: Path object pointing to the CSV file to validate
        tests_dir: Path object pointing to the tests directory (for error messages)

    Example:
        >>> tests_dir = Path(__file__).parent.parent.parent.parent.absolute()
        >>> source_csv = tests_dir / "data" / "example_htmls" / "responses" / "test.csv"
        >>> validate_test_csv_file(source_csv, tests_dir)
        CSV validation passed: 5 followup URL(s) found
    """
    # Validate that the CSV file exists and is a file
    if not source_csv.exists():
        raise FileNotFoundError(
            f"Test CSV file not found: {source_csv}\n"
            f"Expected location: tests/data/example_htmls/responses/{TEST_CSV_FILENAME}\n"
            f"Tests directory: {tests_dir}\n"
            f"Please ensure the test data file exists before running this test."
        )

    if not source_csv.is_file():
        raise ValueError(
            f"Test CSV path exists but is not a file: {source_csv}\n"
            f"Expected a file, got: {source_csv.stat()}"
        )

    # Validate CSV file extension
    if source_csv.suffix.lower() != ".csv":
        raise ValueError(
            f"Test data file must have .csv extension\n"
            f"Got: {source_csv.suffix}\n"
            f"File: {source_csv}"
        )

    # Validate CSV structure and content
    try:
        with open(source_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames

            # Check for required column
            if "followup_dedicated_website" not in headers:
                raise ValueError(
                    f"CSV file missing required column: 'followup_dedicated_website'\n"
                    f"Found columns: {', '.join(headers)}\n"
                    f"File: {source_csv}"
                )

            # Check for at least one non-empty followup URL
            rows = list(reader)
            followup_urls = [
                row.get("followup_dedicated_website", "").strip() for row in rows
            ]
            valid_urls = [url for url in followup_urls if url and url != ""]

            if not valid_urls:
                raise ValueError(
                    f"CSV file contains no valid followup website URLs\n"
                    f"Column 'followup_dedicated_website' exists but all values are empty\n"
                    f"Total rows: {len(rows)}\n"
                    f"File: {source_csv}"
                )

            print(f"CSV validation passed: {len(valid_urls)} followup URL(s) found")

    except csv.Error as e:
        raise ValueError(
            f"Failed to parse CSV file: {e}\n"
            f"File may be corrupted or not a valid CSV\n"
            f"File: {source_csv}"
        )


validate_test_csv_file(source_csv, tests_dir)


class TestFollowupWebsiteCreatedFiles:
    """
    Test suite for validating created files from followup website scraping.
    """

    @classmethod
    def setup_class(cls):
        """
        Setup class-level resources that runs once before all tests.

        Uses a real CSV file to extract one random followup website URL
        and downloads the actual page to validate end-to-end functionality.
        Limits downloads to 1 page to avoid server overload.
        """

        # Get data_dir from pytest request context
        request = (
            pytest._current_request if hasattr(pytest, "_current_request") else None
        )
        if request:
            real_data_dir = request.getfixturevalue("data_dir")
        else:
            # Fallback: calculate manually
            script_dir = Path(__file__).parent.parent.parent.parent.parent.absolute()
            real_data_dir = script_dir / "data"

        cls.data_dir = real_data_dir

        # Find the most recent timestamp directory
        latest_timestamp_dir = Path(followup_main._find_latest_timestamp_directory())
        cls.source_timestamp_dir = latest_timestamp_dir

        # Create temporary directory for test output
        import tempfile

        cls.temp_dir = Path(tempfile.mkdtemp(prefix="eci_followup_website_test_"))

        # Copy the timestamp directory structure to temp location
        cls.test_timestamp_dir = cls.temp_dir / latest_timestamp_dir.name
        cls.test_timestamp_dir.mkdir(parents=True)

        print(f"\nCreated temporary test directory: {cls.temp_dir}")
        print(f"Test timestamp directory: {cls.test_timestamp_dir}")

        # Copy the real CSV file to test directory
        script_dir = Path(__file__).parent.parent.parent.parent.parent.absolute()

        if not source_csv.exists():
            raise FileNotFoundError(
                f"Test CSV file not found: {source_csv}. "
                "Ensure the test data file exists before running this test."
            )

        cls.test_csv = cls.test_timestamp_dir / source_csv.name
        shutil.copy(source_csv, cls.test_csv)

        print(f"Copied CSV file to: {cls.test_csv}")

        # Extract one followup website URL from CSV
        cls.followup_url_data = cls._extract_one_followup_url()

        if not cls.followup_url_data:
            raise ValueError("No followup website URL found in CSV file")

        print(f"Extracted followup URL: {cls.followup_url_data['url']}")
        print(f"Registration number: {cls.followup_url_data['registration_number']}")

        # Track download attempts
        cls.download_count = 0
        cls.downloaded_files = []

        # Store original download function
        original_download = FollowupWebsiteDownloader.download_single_followup_website

        def mock_download_limited(self, url, year, reg_number, max_retries=3):
            """
            Download followup websites but limit to first 1 item.
            """
            if cls.download_count >= 1:
                # Return failure for items beyond limit
                return False

            # Call original download function
            cls.download_count += 1
            success = original_download(self, url, year, reg_number, max_retries)

            if success:
                cls.downloaded_files.append((year, reg_number))

            return success

        # Setup followup website directory
        cls.followup_website_dir = (
            cls.test_timestamp_dir / RESPONSES_FOLLOWUP_WEBSITE_DIR_NAME
        )
        cls.followup_website_dir.mkdir(parents=True, exist_ok=True)

        # Patch to use test directory and download only one page
        with patch.object(
            followup_main,
            "_find_latest_timestamp_directory",
            return_value=str(cls.test_timestamp_dir),
        ):
            with patch.object(
                FollowupWebsiteDownloader,
                "download_single_followup_website",
                mock_download_limited,
            ):
                # Download the single followup website page
                downloader = FollowupWebsiteDownloader(str(cls.followup_website_dir))
                try:
                    downloader.download_all_followup_websites([cls.followup_url_data])
                except Exception as e:
                    # If scraping fails completely, store the error
                    cls.scraping_error = str(e)
                else:
                    cls.scraping_error = None

        # Store paths for tests
        cls.logs_dir = cls.test_timestamp_dir / LOG_DIR_NAME

    @classmethod
    def _extract_one_followup_url(cls):
        """Extract a random followup website URL from the test CSV file."""

        with open(cls.test_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Filter rows with valid URLs
        valid_rows = [
            row for row in rows if row.get("followup_dedicated_website", "").strip()
        ]

        if not valid_rows:
            return None

        # Pick random row
        row = random.choice(valid_rows)

        followup_url = row.get("followup_dedicated_website", "").strip()
        registration_number = row.get("registration_number", "").strip()
        year = registration_number.split("/")[0] if "/" in registration_number else ""
        reg_number_for_filename = registration_number.replace("/", "_")

        return {
            "url": followup_url,
            "registration_number": reg_number_for_filename,
            "year": year,
        }

    @classmethod
    def teardown_class(cls):
        """
        Cleanup class-level resources that runs once after all tests.

        Remove temporary directory created for testing.
        """
        print(f"\n\nTest completed. Files were created in temporary directory:")
        print(f"{cls.followup_website_dir}")

        # Clean up temporary directory
        if hasattr(cls, "temp_dir") and cls.temp_dir.exists():
            shutil.rmtree(cls.temp_dir)
            print(f"Cleaned up temporary directory: {cls.temp_dir}")

    def test_debug_fixture(self):
        """Debug test to verify setup output."""
        print(f"\nDebug - setup completed successfully")
        print(f"Source timestamp directory: {self.source_timestamp_dir}")
        print(f"Test timestamp directory: {self.test_timestamp_dir}")
        print(f"Followup website directory: {self.followup_website_dir}")
        print(f"Download count: {self.download_count}")
        print(f"Followup URL data: {self.followup_url_data}")

        if self.scraping_error:
            print(f"Scraping error: {self.scraping_error}")

    def test_followup_website_directory_structure_created(self):
        """
        Verify followup website directory and year-based
        subdirectories are created.
        """
        # Check followup website directory exists
        assert (
            self.followup_website_dir.exists()
        ), f"Followup website directory not created: {self.followup_website_dir}"
        assert (
            self.followup_website_dir.is_dir()
        ), "Followup website path is not a directory"

        # Check year subdirectories exist (at least one)
        year_dirs = [d for d in self.followup_website_dir.iterdir() if d.is_dir()]
        assert len(year_dirs) > 0, "No year subdirectories created"

        # Verify year directories have valid names (4-digit years)
        for year_dir in year_dirs:
            assert (
                year_dir.name.isdigit() and len(year_dir.name) == 4
            ), f"Invalid year directory name: {year_dir.name}"

    def test_followup_url_extracted_correctly(self):
        """
        Verify followup URL was extracted from CSV with correct structure.
        """
        # Verify followup URL data has required fields
        required_fields = ["url", "year", "registration_number"]
        for field in required_fields:
            assert (
                field in self.followup_url_data
            ), f"Followup URL data missing required field: {field}"

        # Verify URL is valid
        assert self.followup_url_data["url"].startswith(
            "http"
        ), f"Invalid URL format: {self.followup_url_data['url']}"

        # Verify year has 4-digit format
        year = self.followup_url_data["year"]
        assert year.isdigit() and len(year) == 4, f"Invalid year format: {year}"

        # Verify registration number format (YYYY_NNNNNN)
        reg_number = self.followup_url_data["registration_number"]
        assert (
            "_" in reg_number
        ), f"Registration number should contain underscore: {reg_number}"
        assert (
            "/" not in reg_number
        ), f"Registration number should not contain slash: {reg_number}"

    def test_followup_html_file_downloaded(self):
        """
        Verify HTML file was downloaded with valid content,
        is prettified, and uses UTF-8 encoding.
        """
        # Count HTML files in year directories
        html_files_found = []

        for year_dir in self.followup_website_dir.iterdir():
            if year_dir.is_dir() and year_dir.name.isdigit():
                for file in year_dir.iterdir():
                    if file.suffix == ".html":
                        html_files_found.append(file)

        # Verify exactly one HTML file was downloaded
        assert (
            len(html_files_found) == 1
        ), f"Expected 1 HTML file, found {len(html_files_found)}"

        html_file = html_files_found[0]

        # Check file naming pattern (YYYY_NNNNNN_en.html)
        import re

        assert re.match(
            FOLLOWUP_WEBSITE_FILENAME_PATTERN, html_file.name
        ), f"Invalid filename pattern: {html_file.name}"

        # Verify file is in correct year directory
        expected_year = self.followup_url_data["year"]
        assert (
            html_file.parent.name == expected_year
        ), f"File in wrong year directory. Expected {expected_year}, got {html_file.parent.name}"

        # Read file content
        with open(html_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Verify content is substantial
        assert (
            len(content) > 1000
        ), f"HTML file too short: {html_file.name} ({len(content)} bytes)"

        # Verify HTML structure
        assert "<html" in content.lower(), f"No HTML tag found in: {html_file.name}"
        assert "</html>" in content.lower(), f"No closing HTML tag in: {html_file.name}"

        # Verify prettification by checking indentation
        soup = BeautifulSoup(content, "html.parser")
        prettified_content = soup.prettify()

        # Compare stripped versions (to handle minor formatting differences)
        assert (
            content.strip() == prettified_content.strip()
        ), f"HTML file is not prettified: {html_file.name}"

        # Verify no error indicators
        content_lower = content.lower()
        assert (
            "rate limited" not in content_lower
        ), f"Rate limit error in: {html_file.name}"

        error_indicators = [
            "we apologise for any inconvenience",
            "please try again later",
            "server inaccessibility",
        ]
        assert not any(
            indicator in content_lower for indicator in error_indicators
        ), f"Server error page in: {html_file.name}"

    def test_file_saved_in_correct_location(self):
        """
        Verify file is saved with correct filename in correct directory.
        """
        expected_year = self.followup_url_data["year"]
        expected_reg_number = self.followup_url_data["registration_number"]
        expected_filename = f"{expected_reg_number}_en.html"
        expected_path = self.followup_website_dir / expected_year / expected_filename

        # Check file exists at expected location
        assert (
            expected_path.exists()
        ), f"File not found at expected location: {expected_path}"

        # Verify it's a file, not a directory
        assert expected_path.is_file(), f"Expected path is not a file: {expected_path}"

    def test_download_count_accurate(self):
        """
        Verify that exactly one page was downloaded.
        """
        assert (
            self.download_count == 1
        ), f"Expected 1 download attempt, got {self.download_count}"

        assert (
            len(self.downloaded_files) == 1
        ), f"Expected 1 successful download, got {len(self.downloaded_files)}"

    def test_uses_temporary_directory(self):
        """
        Verify that the test uses a temporary directory and doesn't
        modify the actual data directory.
        """
        # Verify test directory is in temp location
        assert str(self.test_timestamp_dir).startswith(
            str(self.temp_dir)
        ), "Test should use temporary directory"

        # Verify followup website files are in temp location
        assert (
            self.followup_website_dir.parent == self.test_timestamp_dir
        ), "Followup website directory should be in temporary directory"


# Inject fixture into setup_class using pytest hook
@pytest.fixture(scope="class")
def inject_data_dir(request, data_dir):
    """Inject data_dir fixture into TestFollowupWebsiteCreatedFiles class."""
    request.cls.setup_class()
