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

It should take between 3.5 and 4 minutes to complete.

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

from ECI_initiatives.__main__ import (
    scrape_eci_initiatives,
    parse_initiatives_list_data,
    scrape_all_initiatives_on_all_pages,
    navigate_to_next_page,
)


class TestCreatedFiles:
    """Test suite for validating created files from ECI scraping."""

    @pytest.fixture(scope="class")
    def setup_scraping(self):
        """Setup fixture that runs scraping once and provides results."""

        # Create temporary directories for testing
        self.temp_base_dir = tempfile.mkdtemp(prefix="eci_test_")
        self.temp_data_dir = os.path.join(self.temp_base_dir, "data")

        # Store original functions for later restoration
        original_parse_initiatives = parse_initiatives_list_data
        original_navigate_to_next_page = navigate_to_next_page

        def mock_parse_initiatives_limited(page_source, base_url):
            """
            Parse initiatives but limit to first 3 items.
            To limit the time that the test takes.
            """

            full_data = original_parse_initiatives(page_source, base_url)
            return full_data[:3]  # Return only first 3 initiatives

        def mock_navigate_to_next_page_first_only(driver, current_page):
            """
            Always return False to stop at first page.
            Mocked to just scrape the first page.
            """

            return False

        # Apply mocks and run scraping
        with patch.object(
            sys.modules["ECI_initiatives.__main__"],
            "parse_initiatives_list_data",
            side_effect=mock_parse_initiatives_limited,
        ), patch.object(
            sys.modules["ECI_initiatives.__main__"],
            "navigate_to_next_page",
            side_effect=mock_navigate_to_next_page_first_only,
        ), patch(
            "ECI_initiatives.__main__.os.path.dirname"
        ) as mock_dirname:

            # Mock the script directory to use our temp directory
            mock_dirname.return_value = self.temp_base_dir

            # Run the scraping function
            timestamp = scrape_eci_initiatives()

        # Store results for tests
        self.timestamp = timestamp
        self.data_path = os.path.join(self.temp_base_dir, "data", timestamp)
        self.listings_path = os.path.join(self.data_path, "listings")
        self.pages_path = os.path.join(self.data_path, "initiative_pages")

        # Yield test data to all test methods - this creates the handoff point
        # between setup and teardown phases. The dictionary contains all paths
        # and metadata that test methods need to validate file creation results.
        yield {
            "timestamp": timestamp,  # When scraping started (for reference)
            "data_path": self.data_path,  # Main data directory path
            "listings_path": self.listings_path,  # CSV and HTML listing files path
            "pages_path": self.pages_path,  # Individual initiative pages path
        }

        # Cleanup after all tests
        if os.path.exists(self.temp_base_dir):
            shutil.rmtree(self.temp_base_dir)

    def test_directory_structure_created(self, setup_scraping):
        """Test that all required directories are created."""

        paths = setup_scraping

        # Check main directories exist
        assert os.path.exists(paths["data_path"]), "Main data directory not created"
        assert os.path.exists(paths["listings_path"]), "Listings directory not created"
        assert os.path.exists(paths["pages_path"]), "Pages directory not created"

        # Check logs directory exists
        logs_path = os.path.join(paths["data_path"], "logs")
        assert os.path.exists(logs_path), "Logs directory not created"

    def test_listing_files_created(self, setup_scraping):
        """Test that listing page files are created with correct content."""

        paths = setup_scraping

        # Check CSV file exists
        csv_file = os.path.join(paths["listings_path"], "initiatives_list.csv")
        assert os.path.exists(csv_file), "initiatives_list.csv not created"

        # Check HTML listing file exists (should be exactly 1 since we only scrape first page)
        html_files = [
            f for f in os.listdir(paths["listings_path"]) if f.endswith(".html")
        ]
        assert (
            len(html_files) == 1
        ), f"Expected 1 HTML listing file, found {len(html_files)}"

        # Check HTML file name pattern
        html_file = html_files[0]

        assert html_file.startswith(
            "Find_initiative_European_Citizens_Initiative_page_"
        ), f"HTML file name pattern incorrect: {html_file}"

    def test_csv_content_structure(self, setup_scraping):
        """Test CSV file has correct structure and limited content."""

        paths = setup_scraping
        csv_file = os.path.join(paths["listings_path"], "initiatives_list.csv")

        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Should have exactly 3 rows (limited by our mock)
        assert len(rows) == 3, f"Expected exactly 3 initiatives, found {len(rows)}"

        # Check required columns exist
        required_columns = [
            "url",
            "current_status",
            "registration_number",
            "signature_collection",
            "datetime",
        ]

        if rows:
            for col in required_columns:

                assert (
                    col in rows[0].keys()
                ), f"Required column '{col}' missing from CSV"

            # Check URL format
            for row in rows:

                assert row["url"].startswith(
                    "https://citizens-initiative.europa.eu/initiatives/details/"
                ), f"URL format incorrect: {row['url']}"

    def test_initiative_pages_downloaded(self, setup_scraping):
        """Test that individual initiative pages are downloaded."""

        paths = setup_scraping

        # Count HTML files in year directories
        html_count = 0

        if os.path.exists(paths["pages_path"]):

            for item in os.listdir(paths["pages_path"]):

                year_path = os.path.join(paths["pages_path"], item)

                if os.path.isdir(year_path):

                    html_files = [
                        f for f in os.listdir(year_path) if f.endswith(".html")
                    ]

                    html_count += len(html_files)

        # Should have exactly 3 HTML files (one for each initiative)
        assert html_count == 3, f"Expected 3 initiative HTML files, found {html_count}"

    def test_initiative_html_content(self, setup_scraping):
        """Test that downloaded HTML files contain valid content."""

        paths = setup_scraping

        html_files = []

        # Collect all HTML files from year directories
        for item in os.listdir(paths["pages_path"]):

            year_path = os.path.join(paths["pages_path"], item)

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

    def test_file_naming_convention(self, setup_scraping):
        """Test that files follow the expected naming conventions."""

        paths = setup_scraping

        # Check listing HTML file naming
        html_files = [
            f for f in os.listdir(paths["listings_path"]) if f.endswith(".html")
        ]

        for html_file in html_files:

            assert html_file.startswith(
                "Find_initiative_European_Citizens_Initiative_page_"
            ), f"Listing HTML file naming incorrect: {html_file}"

            assert html_file.endswith(
                ".html"
            ), f"Listing file should end with .html: {html_file}"

        # Check initiative page file naming (should be <year>_<number_initiative>.html format)
        for item in os.listdir(paths["pages_path"]):

            year_path = os.path.join(paths["pages_path"], item)

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
