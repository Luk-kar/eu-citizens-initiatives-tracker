"""
End-to-end test suite for validating that the Commission responses 
scraper correctly creates files and directories.

Similar to initiatives end-to-end tests, this uses a limited scope to:
- Extract response links from existing initiative pages
- Download a limited number of response pages (e.g., first 3)
- Validate file creation, structure, and content

The test focuses on critical outcomes:
- Files created in correct locations
- Valid content
- Proper naming conventions
- CSV generation with correct structure

This simplified approach reduces:
- Server load on ECI website
- Maintenance overhead
- Test execution time

Expected execution time: 30-60 seconds
"""

# Standard library
import csv
import shutil
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

# Third party
import pytest
from bs4 import BeautifulSoup

# Local imports
from ECI_initiatives.scraper.responses import __main__ as responses_main
from ECI_initiatives.scraper.responses.downloader import ResponseDownloader
from ECI_initiatives.tests.consts import (
    DATA_DIR_NAME,
    LOG_DIR_NAME,
    RESPONSES_DIR_NAME,
    RESPONSES_CSV_FILENAME,
    RESPONSES_CSV_FIELDNAMES,
    MAX_RESPONSE_DOWNLOADS_E2E_TEST,
    RESPONSE_PAGE_FILENAME_PATTERN,
)


class TestCreatedFiles:
    """
    Test suite for validating created files from Commission 
    responses scraping.
    """
    
    @classmethod
    def setup_class(cls, data_dir=None):
        """
        Setup class-level resources that runs once before all tests.
        
        Uses existing initiative pages from a previous scraper run
        or creates minimal test data. Limits downloads to first 3
        response pages to avoid server overload.
        """
        
        # Get data_dir from pytest request context
        request = pytest._current_request if hasattr(pytest, '_current_request') else None
        if request:
            real_data_dir = request.getfixturevalue('data_dir')
        else:
            # Fallback: calculate manually
            script_dir = Path(__file__).parent.parent.parent.parent.parent.absolute()
            real_data_dir = script_dir / "data"
        
        cls.data_dir = real_data_dir
        
        # Find the most recent timestamp directory with initiative data
        latest_timestamp_dir = Path(responses_main._find_latest_timestamp_directory())
        cls.timestamp_dir = latest_timestamp_dir
        cls.pages_dir = latest_timestamp_dir / "initiatives"
        
        # Verify pages directory exists
        if not cls.pages_dir.exists():
            raise FileNotFoundError(
                f"Initiative pages directory not found: {cls.pages_dir}. "
                "Run the initiatives scraper first."
            )
        
        # Clean up any existing responses directory from previous test runs
        responses_dir_to_clean = cls.timestamp_dir / RESPONSES_DIR_NAME

        if responses_dir_to_clean.exists():
            
            shutil.rmtree(responses_dir_to_clean)
            print(f"\nCleaned previous responses directory: {responses_dir_to_clean}")
        
        # Store original download function
        original_download = ResponseDownloader.download_single_response
        
        # Track download attempts
        cls.download_count = 0
        cls.downloaded_files = []
        
        def mock_download_limited(self, url, year, reg_number, max_retries=3):
            """
            Download responses but limit to first MAX_RESPONSE_DOWNLOADS_E2E_TEST items.
            """

            if cls.download_count >= MAX_RESPONSE_DOWNLOADS_E2E_TEST:
                # Return failure for items beyond limit
                return False, ""
            
            # Call original download function
            cls.download_count += 1
            success, timestamp = original_download(self, url, year, reg_number, max_retries)
            
            if success:
                cls.downloaded_files.append((year, reg_number))
            
            return success, timestamp
        
        # Apply mock to limit downloads
        with patch.object(
            ResponseDownloader,
            'download_single_response',
            mock_download_limited
        ):
            # Run the scraping function
            try:
                responses_main.scrape_commission_responses()

            except Exception as e:
                # If scraping fails completely, store the error
                cls.scraping_error = str(e)
            else:
                cls.scraping_error = None
        
        # Store paths for tests
        cls.responses_dir = cls.timestamp_dir / RESPONSES_DIR_NAME
        cls.csv_file = cls.responses_dir / RESPONSES_CSV_FILENAME
        cls.logs_dir = cls.timestamp_dir / LOG_DIR_NAME

    @classmethod
    def teardown_class(cls):
        """
        Cleanup class-level resources that runs once after all tests.
        
        Note: Actual directory cleanup handled by conftest.py fixture.
        """

        print(f"\n\nTest completed. Files created in:\n{cls.responses_dir}")
        print("Note: Files will be cleaned up by the session fixture.")
    
    def test_debug_fixture(self):
        """Debug test to verify setup output."""

        print(f"\nDebug - setup completed successfully")
        print(f"Timestamp directory: {self.timestamp_dir}")
        print(f"Pages directory: {self.pages_dir}")
        print(f"Responses directory: {self.responses_dir}")
        print(f"Download count: {self.download_count}")
        
        if self.scraping_error:
            print(f"Scraping error: {self.scraping_error}")
    
    def test_responses_directory_structure_created(self):
        """
        Verify responses directory and year-based 
        subdirectories are created, along with CSV file.
        """

        # Check responses directory exists
        assert self.responses_dir.exists(), \
            f"Responses directory not created: {self.responses_dir}"
        assert self.responses_dir.is_dir(), \
            "Responses path is not a directory"
        
        # Check CSV file exists
        assert self.csv_file.exists(), \
            f"CSV file not created: {self.csv_file}"
        
        # Check year subdirectories exist (at least one)
        year_dirs = [d for d in self.responses_dir.iterdir() if d.is_dir()]
        assert len(year_dirs) > 0, \
            "No year subdirectories created"
        
        # Verify year directories have valid names (4-digit years)
        for year_dir in year_dirs:
            assert year_dir.name.isdigit() and len(year_dir.name) == 4, \
                f"Invalid year directory name: {year_dir.name}"
    
    def test_response_links_extracted_correctly(self):
        """
        Verify only initiatives with response links 
        are processed and all year directories are scanned.
        """

        # Extract response links using actual function
        response_links = responses_main._extract_response_links(str(self.pages_dir))
        
        # Verify at least some links were found
        assert len(response_links) > 0, \
            "No response links extracted from initiative pages"
        
        # Verify each link has required structure
        required_fields = ['url', 'year', 'reg_number', 'title', 'datetime']

        for link in response_links:

            for field in required_fields:
                assert field in link, \
                    f"Response link missing required field: {field}"
        
        # Verify year directories were scanned
        years_found = {link['year'] for link in response_links}

        assert len(years_found) > 0, \
            "No years found in response links"
        
        # Verify all years have 4-digit format
        for year in years_found:

            assert year.isdigit() and len(year) == 4, \
                f"Invalid year format: {year}"
    
    def test_csv_file_structure_and_content(self):
        """
        Verify CSV contains required columns and 
        registration numbers are in slash format.
        """

        # Check CSV exists
        assert self.csv_file.exists(), \
            "CSV file not created"
        
        # Read CSV content
        with open(self.csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            rows = list(reader)
        
        # Verify required columns exist
        assert headers == RESPONSES_CSV_FIELDNAMES, \
            f"CSV headers incorrect. Expected: {RESPONSES_CSV_FIELDNAMES}, Got: {headers}"
        
        # Verify at least some rows exist
        assert len(rows) > 0, \
            "CSV file is empty (no data rows)"
        
        # Verify registration numbers use slash format
        for row in rows:

            reg_number = row['registration_number']
            assert '/' in reg_number, \
                f"Registration number should use slash format: {reg_number}"
            assert '_' not in reg_number, \
                f"Registration number should not contain underscores: {reg_number}"
        
        # Verify successful downloads have timestamps
        rows_with_timestamps = [row for row in rows if row['datetime']]
        assert len(rows_with_timestamps) > 0, \
            "No successful downloads found (all timestamps empty)"
        
        # Verify timestamp format (YYYY-MM-DD HH:MM:SS)
        for row in rows_with_timestamps:
            timestamp = row['datetime']

            try:
                datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')

            except ValueError as e:
                raise AssertionError(
                    f"Invalid timestamp format: {timestamp}. "
                    f"Expected format: YYYY-MM-DD HH:MM:SS. Error: {e}"
                )
    
    def test_response_html_files_downloaded(self):
        """
        Verify HTML files contain valid 
        Commission response content, are prettified, and use UTF-8 
        encoding.
        """

        # Count HTML files in year directories
        html_files_found = []
        
        for year_dir in self.responses_dir.iterdir():

            if year_dir.is_dir() and year_dir.name.isdigit():

                for file in year_dir.iterdir():

                    if file.suffix == '.html':
                        html_files_found.append(file)
        
        # Verify at least some HTML files were downloaded
        # (Should be limited by MAX_RESPONSE_DOWNLOADS_E2E_TEST)
        assert len(html_files_found) > 0, \
            "No HTML response files downloaded"
        
        assert len(html_files_found) <= MAX_RESPONSE_DOWNLOADS_E2E_TEST, \
            f"Too many files downloaded. Expected max {MAX_RESPONSE_DOWNLOADS_E2E_TEST}, got {len(html_files_found)}"
        
        # Verify each HTML file
        import re
        for html_file in html_files_found:
            # Check file naming pattern (YYYY_NNNNNN_en.html)

            assert re.match(RESPONSE_PAGE_FILENAME_PATTERN, html_file.name), \
                f"Invalid filename pattern: {html_file.name}"
            
            # Read file content
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Verify content is substantial
            assert len(content) > 1000, \
                f"HTML file too short: {html_file.name} ({len(content)} bytes)"
            
            # Verify HTML structure
            assert '<html' in content.lower(), \
                f"No HTML tag found in: {html_file.name}"

            assert '</html>' in content.lower(), \
                f"No closing HTML tag in: {html_file.name}"
            
            # Verify Commission response content
            assert 'Commission' in content, \
                f"No Commission content found in: {html_file.name}"
            
            # Verify prettification by comparing with BeautifulSoup's prettify output
            soup = BeautifulSoup(content, 'html.parser')
            prettified_content = soup.prettify()
            
            # If the file was already prettified, it should match (or be very close to) 
            # the prettified version
            # We strip whitespace from both to handle minor formatting differences
            assert content.strip() == prettified_content.strip(), \
                f"HTML file is not prettified: {html_file.name}"
            
            # Verify no error indicators
            content_lower = content.lower()
            assert 'rate limited' not in content_lower, \
                f"Rate limit error in: {html_file.name}"

            error_indicators = [
                'we apologise for any inconvenience',
                'please try again later'
            ]

            assert not any(indicator in content_lower for indicator in error_indicators), \
                f"Server error page in: {html_file.name}"
    
    def test_completion_summary_accuracy(self):
        """
        Verify completion summary shows correct 
        counts and file paths.
        """

        # Read CSV to get counts
        with open(self.csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        total_links = len(rows)
        successful_downloads = len([row for row in rows if row['datetime']])
        failed_downloads = len([row for row in rows if not row['datetime']])
        
        # Verify counts are consistent
        assert total_links == (successful_downloads + failed_downloads), \
            "Total links count doesn't match successful + failed"
        
        # Count actual HTML files
        html_file_count = 0

        for year_dir in self.responses_dir.iterdir():

            if year_dir.is_dir() and year_dir.name.isdigit():
                html_files = list(year_dir.glob('*.html'))
                html_file_count += len(html_files)
        
        # Verify HTML file count matches successful downloads
        assert html_file_count == successful_downloads, \
            f"HTML file count ({html_file_count}) doesn't match successful downloads ({successful_downloads})"
        
        # Verify responses directory path
        assert self.responses_dir.exists(), \
            f"Responses directory not found: {self.responses_dir}"
    
    def test_integration_with_initiatives_scraper(self):
        """
        Verify responses scraper uses the most recent 
        timestamp directory from initiatives scraper.
        """

        # Find all timestamp directories in data dir
        timestamp_dirs = []

        for item in self.data_dir.iterdir():
            if item.is_dir() and '_' in item.name:

                # Check if it matches timestamp pattern (YYYY-MM-DD_HH-MM-SS)
                try:
                    # Validate using datetime.strptime
                    datetime.strptime(item.name, '%Y-%m-%d_%H-%M-%S')
                    timestamp_dirs.append(item)

                except ValueError:
                    # Not a valid timestamp directory, skip it
                    pass
        
        # Verify at least one timestamp directory exists
        assert len(timestamp_dirs) > 0, \
            "No timestamp directories found in data directory"
        
        # Sort by directory name (which includes timestamp)
        timestamp_dirs.sort(key=lambda x: x.name, reverse=True)
        most_recent = timestamp_dirs[0]
        
        # Verify the scraper used the most recent directory
        assert self.timestamp_dir.name == most_recent.name, \
            f"Scraper didn't use most recent directory. Expected: {most_recent.name}, Got: {self.timestamp_dir.name}"
        
        # Verify pages directory exists in that timestamp
        pages_dir = most_recent / "initiatives"
        assert pages_dir.exists(), \
            f"Pages directory not found in most recent timestamp: {pages_dir}"
        
        # Verify responses directory was created in same timestamp
        responses_dir = most_recent / RESPONSES_DIR_NAME
        assert responses_dir.exists(), \
            f"Responses directory not created in timestamp directory: {responses_dir}"


# Inject fixture into setup_class using pytest hook
@pytest.fixture(scope="class")
def inject_data_dir(request, data_dir):
    """Inject data_dir fixture into TestCreatedFiles class."""
    
    request.cls.setup_class(data_dir=data_dir)
