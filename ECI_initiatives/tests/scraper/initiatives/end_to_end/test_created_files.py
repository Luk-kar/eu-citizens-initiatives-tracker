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
