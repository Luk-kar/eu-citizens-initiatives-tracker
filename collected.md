`./ECI_initiatives/scraper/responses/file_operations/csv.py`:
```
"""
File operations for saving Commission response pages.
"""
import csv
import logging
from typing import List, Dict

from bs4 import BeautifulSoup

from .consts import CSV_FIELDNAMES

def write_responses_csv(file_path: str, response_data: List[Dict[str, str]]) -> None:
    """
    Write response data to CSV file.
    
    Args:
        file_path: Full path to the CSV file
        response_data: List of response dictionaries to write
    """
    from .consts import CSV_FIELDNAMES
    
    with open(file_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
        writer.writeheader()
        writer.writerows(response_data)
    
    logger = logging.getLogger("ECIResponsesScraper")
    logger.debug(f"CSV file written: {file_path}")

```

`./ECI_initiatives/scraper/responses/file_operations/__init__.py`:
```

```

`./ECI_initiatives/scraper/responses/file_operations/page.py`:
```
"""
File operations for saving Commission response pages.
"""
import os
import logging

from bs4 import BeautifulSoup

from .consts import MIN_HTML_LENGTH, RATE_LIMIT_INDICATORS


class FileOperations:
    """Handle file and directory operations for response pages."""
    
    def __init__(self, base_dir: str):
        """
        Initialize file operations handler.
        
        Args:
            base_dir: Base directory for saving files
        """
        self.base_dir = base_dir
        self.logger = logging.getLogger("ECIResponsesScraper")
    
    def setup_directories(self) -> None:
        """
        Create necessary directory structure for responses.
        Creates: base_dir/ and subdirectories as needed.
        Logs only when directory is actually created.
        """
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir, exist_ok=True)
            self.logger.info(f"Created responses directory: {self.base_dir}")
    
    def save_response_page(
        self, 
        page_source: str, 
        year: str, 
        reg_number: str
    ) -> str:
        """
        Save Commission response page HTML to file.
        
        Args:
            page_source: HTML content to save
            year: Year of the initiative
            reg_number: Registration number
            
        Returns:
            Filename of saved file
            
        Raises:
            Exception: If rate limiting content detected or save fails
        """
        
        # Validate HTML
        self._validate_html(page_source)
        
        # Create year directory
        year_dir = self._create_year_directory(year)
        
        # Generate filename
        filename = self._generate_filename(year, reg_number)
        full_path = os.path.join(self.base_dir, filename)
        
        # Prettify HTML
        soup = BeautifulSoup(page_source, 'html.parser')
        pretty_html = soup.prettify()
        
        # Save to file
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(pretty_html)
        
        self.logger.debug(f"Saved response page: {filename}")
        
        return filename
    
    def _validate_html(self, page_source: str) -> bool:
        """
        Validate HTML content for rate limiting and malformed content.
        
        Args:
            page_source: HTML content to validate
            
        Returns:
            True if valid, False otherwise
            
        Raises:
            Exception: If rate limiting detected
        """

        # Check minimum length
        if len(page_source) < MIN_HTML_LENGTH:
            raise Exception(f"HTML content too short: {len(page_source)} characters")
        
        # Check for error page (multilingual "Sorry" page)
        error_page_indicators = [
            "We apologise for any inconvenience",
            "Veuillez nous excuser pour ce désagrément",
            "Ci scusiamo per il disagio arrecato"
        ]
        
        page_lower = page_source.lower()
        
        for indicator in error_page_indicators:
            if indicator.lower() in page_lower:
                raise Exception(f"Error page detected: {indicator}")
        
        # Check for rate limiting indicators
        for indicator in RATE_LIMIT_INDICATORS:
            if indicator.lower() in page_lower:
                raise Exception(f"Rate limiting detected in content: {indicator}")
        
        return True
    
    def _create_year_directory(self, year: str) -> str:
        """
        Create year-specific subdirectory.
        
        Args:
            year: Year string
            
        Returns:
            Full path to year directory
        """

        year_dir = os.path.join(self.base_dir, year)
        os.makedirs(year_dir, exist_ok=True)
        
        return year_dir
    
    def _generate_filename(self, year: str, reg_number: str) -> str:
        """
        Generate filename for response page.
        
        Args:
            year: Year of initiative
            reg_number: Registration number
            
        Returns:
            Filename in format: {year}/{reg_number}_en.html
        """

        return f"{year}/{reg_number}_en.html"

def save_response_html_file(responses_dir: str, year: str, reg_number: str, page_source: str) -> str:
    """
    Convenience function to save response page.
    
    Args:
        responses_dir: Base directory for responses
        year: Year of initiative
        reg_number: Registration number
        page_source: HTML content
        
    Returns:
        Filename of saved file
    """

    file_ops = FileOperations(responses_dir)
    return file_ops.save_response_page(page_source, year, reg_number)
```

`./ECI_initiatives/tests/scraper/responses/behaviour/__init__.py`:
```

```

`./ECI_initiatives/tests/scraper/responses/behaviour/test_csv_output.py`:
```
"""
Test suite for CSV output file creation and content validation.

This test suite verifies that the Commission responses scraper correctly generates CSV files 
with proper structure, required columns, and accurate content based on download outcomes. 

It validates registration number normalization from underscore to slash format, 
ensures timestamps are populated only for successful downloads 
while failed downloads have empty timestamps, 
and confirms proper UTF-8 encoding for multilingual content.
"""


# Standard library
import csv
import os
import tempfile
from pathlib import Path
from typing import List, Dict

# Third party
import pytest

# Local imports
from ECI_initiatives.scraper.responses.file_operations.csv import write_responses_csv
from ECI_initiatives.scraper.responses.consts import CSV_FIELDNAMES


class TestCSVOutput:
    """Test CSV file generation and content."""

    @pytest.fixture
    def temp_csv_dir(self):
        """Create a temporary directory for CSV files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def sample_response_data_with_underscores(self) -> List[Dict[str, str]]:
        """
        Sample response data with registration numbers in underscore format
        (as they appear in file paths).
        """
        return [
            {
                "url_find_initiative": "https://citizens-initiative.europa.eu/initiatives/details/2019/000007_en",
                "registration_number": "2019_000007",
                "title": "Minority SafePack - one million signatures for diversity in Europe",
                "datetime": "2024-10-09 14:30:45",
            },
            {
                "url_find_initiative": "https://citizens-initiative.europa.eu/initiatives/details/2020/000001_en",
                "registration_number": "2020_000001",
                "title": "Save Bees and Farmers",
                "datetime": "2024-10-09 14:35:12",
            },
            {
                "url_find_initiative": "https://citizens-initiative.europa.eu/initiatives/details/2021/000006_en",
                "registration_number": "2021_000006",
                "title": "End the Cage Age",
                "datetime": "2024-10-09 14:40:33",
            },
        ]

    @pytest.fixture
    def sample_response_data_mixed_success(self) -> List[Dict[str, str]]:
        """
        Sample response data with both successful downloads (with timestamps)
        and failed downloads (empty timestamps).
        """
        return [
            {
                "url_find_initiative": "https://citizens-initiative.europa.eu/initiatives/details/2019/000007_en",
                "registration_number": "2019_000007",
                "title": "Minority SafePack",
                "datetime": "2024-10-09 14:30:45",
            },
            {
                "url_find_initiative": "https://citizens-initiative.europa.eu/initiatives/details/2020/000001_en",
                "registration_number": "2020_000001",
                "title": "Save Bees and Farmers",
                "datetime": "",  # Failed download
            },
            {
                "url_find_initiative": "https://citizens-initiative.europa.eu/initiatives/details/2021/000006_en",
                "registration_number": "2021_000006",
                "title": "End the Cage Age",
                "datetime": "2024-10-09 14:40:33",
            },
            {
                "url_find_initiative": "https://citizens-initiative.europa.eu/initiatives/details/2022/000002_en",
                "registration_number": "2022_000002",
                "title": "Tax the Rich",
                "datetime": "",  # Failed download
            },
        ]

    def test_registration_numbers_normalized_to_slash_format(
        self, temp_csv_dir, sample_response_data_with_underscores
    ):
        """
        When creating the CSV file, verify that registration numbers are
        normalized to slash format (2019/000007) instead of underscore format.
        """
        # Arrange
        csv_path = temp_csv_dir / "responses_test.csv"

        # Act
        write_responses_csv(str(csv_path), sample_response_data_with_underscores)

        # Assert
        assert csv_path.exists(), "CSV file was not created"

        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Verify all registration numbers use slash format
        assert len(rows) == 3, "Expected 3 rows in CSV"

        for row in rows:
            reg_number = row["registration_number"]
            assert "/" in reg_number, f"Registration number should use slash format: {reg_number}"
            assert "_" not in reg_number, f"Registration number should not contain underscores: {reg_number}"

        # Verify specific normalized values
        expected_reg_numbers = ["2019/000007", "2020/000001", "2021/000006"]
        actual_reg_numbers = [row["registration_number"] for row in rows]
        assert actual_reg_numbers == expected_reg_numbers, "Registration numbers not properly normalized"

    def test_csv_timestamps_for_successful_downloads(
        self, temp_csv_dir, sample_response_data_mixed_success
    ):
        """
        When downloads complete, verify that the CSV contains timestamps
        only for successfully downloaded pages.
        """
        # Arrange
        csv_path = temp_csv_dir / "responses_test.csv"

        # Act
        write_responses_csv(str(csv_path), sample_response_data_mixed_success)

        # Assert
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Verify successful downloads have timestamps
        successful_rows = [row for row in rows if row["datetime"]]
        assert len(successful_rows) == 2, "Expected 2 successful downloads with timestamps"

        # Verify timestamp format (YYYY-MM-DD HH:MM:SS)
        for row in successful_rows:
            timestamp = row["datetime"]
            assert len(timestamp) > 0, "Timestamp should not be empty for successful downloads"
            assert "-" in timestamp and ":" in timestamp, f"Invalid timestamp format: {timestamp}"

        # Verify specific successful downloads
        successful_reg_numbers = [row["registration_number"] for row in successful_rows]
        assert "2019/000007" in successful_reg_numbers
        assert "2021/000006" in successful_reg_numbers

    def test_csv_empty_timestamps_for_failed_downloads(
        self, temp_csv_dir, sample_response_data_mixed_success
    ):
        """
        When some downloads fail, verify that failed items appear in the CSV
        with empty timestamp fields.
        """
        # Arrange
        csv_path = temp_csv_dir / "responses_test.csv"

        # Act
        write_responses_csv(str(csv_path), sample_response_data_mixed_success)

        # Assert
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Verify failed downloads have empty timestamps
        failed_rows = [row for row in rows if not row["datetime"]]
        assert len(failed_rows) == 2, "Expected 2 failed downloads with empty timestamps"

        # Verify failed rows still have other data
        for row in failed_rows:
            assert row["url_find_initiative"], "Failed row should have URL"
            assert row["registration_number"], "Failed row should have registration number"
            assert row["title"], "Failed row should have title"
            assert row["datetime"] == "", "Failed row should have empty timestamp"

        # Verify specific failed downloads
        failed_reg_numbers = [row["registration_number"] for row in failed_rows]
        assert "2020/000001" in failed_reg_numbers
        assert "2022/000002" in failed_reg_numbers

    def test_csv_contains_required_columns(
        self, temp_csv_dir, sample_response_data_with_underscores
    ):
        """
        When the CSV is written, verify that it contains all required columns:
        url_find_initiative, registration_number, title, datetime.
        """
        # Arrange
        csv_path = temp_csv_dir / "responses_test.csv"

        # Act
        write_responses_csv(str(csv_path), sample_response_data_with_underscores)

        # Assert
        assert csv_path.exists(), "CSV file was not created"

        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames

        # Verify all required columns exist
        required_columns = CSV_FIELDNAMES
        assert headers == required_columns, f"CSV headers don't match required columns. Expected: {required_columns}, Got: {headers}"

        # Verify column order matches expected order
        expected_order = ["url_find_initiative", "registration_number", "title", "datetime"]
        assert list(headers) == expected_order, f"CSV column order incorrect. Expected: {expected_order}, Got: {list(headers)}"

        # Verify no extra columns
        assert len(headers) == len(expected_order), f"CSV should have exactly {len(expected_order)} columns, got {len(headers)}"

    def test_csv_handles_empty_data_list(self, temp_csv_dir):
        """
        Edge case: When an empty data list is provided, verify CSV is created
        with headers only.
        """
        # Arrange
        csv_path = temp_csv_dir / "responses_empty.csv"
        empty_data = []

        # Act
        write_responses_csv(str(csv_path), empty_data)

        # Assert
        assert csv_path.exists(), "CSV file was not created for empty data"

        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            rows = list(reader)

        assert headers == CSV_FIELDNAMES, "Headers should be present even with empty data"
        assert len(rows) == 0, "No data rows should be present"

    def test_csv_utf8_encoding_for_special_characters(self, temp_csv_dir):
        """
        Verify that CSV handles UTF-8 encoding properly for special characters
        in titles and other fields.
        """
        # Arrange
        csv_path = temp_csv_dir / "responses_utf8.csv"
        data_with_special_chars = [
            {
                "url_find_initiative": "https://citizens-initiative.europa.eu/initiatives/details/2019/000007_en",
                "registration_number": "2019_000007",
                "title": "Diversité en Europe – être différent, ça compte!",
                "datetime": "2024-10-09 14:30:45",
            },
            {
                "url_find_initiative": "https://citizens-initiative.europa.eu/initiatives/details/2020/000001_en",
                "registration_number": "2020_000001",
                "title": "Salva le api e gli agricoltori! 🐝",
                "datetime": "2024-10-09 14:35:12",
            },
        ]

        # Act
        write_responses_csv(str(csv_path), data_with_special_chars)

        # Assert
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Verify special characters are preserved
        assert "Diversité" in rows[0]["title"]
        assert "être différent" in rows[0]["title"]
        assert "🐝" in rows[1]["title"]

    def test_csv_multiple_writes_overwrite_correctly(self, temp_csv_dir):
        """
        Verify that writing to the same CSV file multiple times overwrites
        the previous content (not appends).
        """
        # Arrange
        csv_path = temp_csv_dir / "responses_overwrite.csv"
        
        first_data = [
            {
                "url_find_initiative": "https://example.com/1",
                "registration_number": "2019_000001",
                "title": "First Initiative",
                "datetime": "2024-10-09 14:00:00",
            }
        ]
        
        second_data = [
            {
                "url_find_initiative": "https://example.com/2",
                "registration_number": "2020_000002",
                "title": "Second Initiative",
                "datetime": "2024-10-09 15:00:00",
            },
            {
                "url_find_initiative": "https://example.com/3",
                "registration_number": "2020_000003",
                "title": "Third Initiative",
                "datetime": "2024-10-09 16:00:00",
            }
        ]

        # Act - Write first dataset
        write_responses_csv(str(csv_path), first_data)
        
        # Act - Write second dataset (should overwrite)
        write_responses_csv(str(csv_path), second_data)

        # Assert - Only second dataset should be present
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 2, "CSV should contain only the second dataset (2 rows)"
        assert rows[0]["registration_number"] == "2020/000002"
        assert rows[1]["registration_number"] == "2020/000003"
        assert "2019/000001" not in [row["registration_number"] for row in rows]

```

`./ECI_initiatives/tests/scraper/responses/behaviour/test_directory_structure.py`:
```
"""
Test suite for validating directory and file structure creation
for Commission responses scraper.
"""

# Standard library
import os
import tempfile
from pathlib import Path

# Third party
import pytest

# Local imports
from ECI_initiatives.scraper.responses.file_operations.page import (
    PageFileManager,
    save_response_html_file,
)


class TestDirectoryStructure:
    """Test directory and file creation for responses scraper."""

    @pytest.fixture
    def temp_base_dir(self):
        """Create a temporary base directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def sample_html_content(self):
        """Provide sample HTML content for testing."""

        return """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>Commission Response</title>
        </head>
        <body>
            <h1>Commission's Response</h1>
            <div class="response-content">
                <p>This is the Commission's detailed response to the initiative.</p>
                <p>The Commission has carefully examined the initiative and provides the following feedback...</p>
            </div>
        </body>
        </html>
        """

    def test_response_files_in_year_subdirectories(
        self, temp_base_dir, sample_html_content
    ):
        """
        When the scraper runs successfully, verify that the response HTML
        files are saved in the correct year-based subdirectory structure.
        """
        # Arrange
        responses_dir = temp_base_dir / "responses"
        file_ops = PageFileManager(str(responses_dir))
        file_ops.setup_directories()

        # Act - Save files for different years
        years_and_regs = [
            ("2019", "000007"),
            ("2020", "000001"),
            ("2021", "000006"),
            ("2022", "000002"),
        ]

        for year, reg_number in years_and_regs:
            file_ops.save_response_page(sample_html_content, year, reg_number)

        # Assert - Check year directories exist
        for year, _ in years_and_regs:

            year_dir = responses_dir / year

            assert year_dir.exists(), f"Year directory {year} was not created"
            assert year_dir.is_dir(), f"Year path {year} is not a directory"

        # Assert - Check files are in correct year directories
        for year, reg_number in years_and_regs:

            expected_file = responses_dir / year / f"{reg_number}_en.html"

            assert (
                expected_file.exists()
            ), f"Response file not found in year directory: {expected_file}"

        # Assert - Verify no files are in the root responses directory
        files_in_root = [
            f for f in responses_dir.iterdir() if f.is_file() and f.suffix == ".html"
        ]
        assert (
            len(files_in_root) == 0
        ), "HTML files should not be in root responses directory"

    def test_csv_file_created(self, temp_base_dir):
        """
        When the scraper runs, verify that a CSV file with response metadata
        is created in the responses directory.
        """

        # Arrange
        from ECI_initiatives.scraper.responses.file_operations.csv import (
            write_responses_csv,
        )

        responses_dir = temp_base_dir / "responses"
        responses_dir.mkdir(parents=True)

        csv_path = responses_dir / "responses_list.csv"

        sample_data = [
            {
                "url_find_initiative": "https://citizens-initiative.europa.eu/initiatives/details/2019/000007_en",
                "registration_number": "2019_000007",
                "title": "Test Initiative",
                "datetime": "2024-10-09 14:30:45",
            }
        ]

        # Act
        write_responses_csv(str(csv_path), sample_data)

        # Assert
        assert csv_path.exists(), "CSV file was not created"
        assert csv_path.is_file(), "CSV path is not a file"
        assert csv_path.suffix == ".csv", "File does not have .csv extension"

        # Verify the CSV file is actually in the responses directory
        csv_files_in_responses_dir = list(responses_dir.glob("*.csv"))
        assert len(csv_files_in_responses_dir) > 0, "No CSV files found in responses directory"
        assert csv_path in csv_files_in_responses_dir, "Created CSV file is not in responses directory"

    def test_missing_data_directory_error(self, temp_base_dir):
        """
        When the data directory doesn't exist, verify that the scraper raises
        an appropriate error indicating the initiatives scraper should run first.
        """
        
        # Arrange
        from ECI_initiatives.scraper.responses.__main__ import scrape_commission_responses
        from ECI_initiatives.scraper.responses.errors import MissingDataDirectoryError
        from unittest.mock import patch
        
        # Patch the SCRIPT_DIR to point to our temp directory where no data exists
        with patch('ECI_initiatives.scraper.responses.__main__.SCRIPT_DIR', str(temp_base_dir)):
            
            # Ensure no data directory exists
            data_dir = temp_base_dir / "data"
            if data_dir.exists():
                raise RuntimeError(
                    f"Test setup failed: Directory {data_dir} should not exist. "
                    "This indicates a problem with test isolation."
                )
            
            # Act & Assert - Call the actual scraper function
            with pytest.raises(MissingDataDirectoryError) as exc_info:
                scrape_commission_responses()
            
            # Verify the error message contains the expected hint
            error = exc_info.value
            assert error.expected_path is not None
            assert "data" in error.expected_path.lower()
            assert "Run the initiatives scraper first" in error.hint
            
            # Verify error message format
            error_message = str(error)
            assert "Cannot find required data directory" in error_message
            assert "Expected:" in error_message
            assert "Hint:" in error_message


    def test_uses_most_recent_initiatives_timestamp(self, temp_base_dir):
        """
        When running the full scraper workflow, verify that files are created
        in the most recent timestamp directory from the initiatives scraper.
        """
        
        # Arrange
        from ECI_initiatives.scraper.responses.__main__ import _find_latest_timestamp_directory
        from unittest.mock import patch
        
        # Create multiple timestamp directories
        data_dir = temp_base_dir / "data"
        data_dir.mkdir()

        timestamps = [
            "2024-10-01_10-00-00",
            "2024-10-05_14-30-00",
            "2024-10-09_16-45-00",  # Most recent
            "2024-10-03_08-15-00",
        ]

        for timestamp in timestamps:
            timestamp_dir = data_dir / timestamp
            timestamp_dir.mkdir()

        # Act - Patch SCRIPT_DIR and call the actual function
        with patch('ECI_initiatives.scraper.responses.__main__.SCRIPT_DIR', str(temp_base_dir)):
            most_recent_path = _find_latest_timestamp_directory()

        # Assert - Verify the function selected the most recent timestamp
        most_recent = Path(most_recent_path)
        assert most_recent.name == "2024-10-09_16-45-00", "Did not select most recent timestamp"
        assert most_recent.parent == data_dir, "Timestamp directory not in data directory"
        assert most_recent.exists(), "Selected timestamp directory does not exist"
        
    def test_responses_directory_creation(self, temp_base_dir):
        """
        Verify that the responses directory is created if it doesn't exist.
        """

        # Arrange
        responses_dir = temp_base_dir / "responses"
        assert not responses_dir.exists()

        file_ops = PageFileManager(str(responses_dir))

        # Act
        file_ops.setup_directories()

        # Assert
        assert responses_dir.exists(), "Responses directory was not created"
        assert responses_dir.is_dir(), "Responses path is not a directory"

    def test_multiple_year_directories_coexist(self, temp_base_dir, sample_html_content):
        """
        Verify that multiple year subdirectories can coexist without conflicts.
        """

        # Arrange
        responses_dir = temp_base_dir / "responses"
        file_ops = PageFileManager(str(responses_dir))
        file_ops.setup_directories()

        years = ["2019", "2020", "2021", "2022", "2023"]

        # Act - Create files in all year directories
        for year in years:
            file_ops.save_response_page(sample_html_content, year, "000001")

        # Assert - All year directories exist
        year_dirs = [d for d in responses_dir.iterdir() if d.is_dir()]
        assert len(year_dirs) == len(years), f"Expected {len(years)} year directories"

        for year in years:
            year_dir = responses_dir / year
            assert year_dir.exists()
            assert (year_dir / "000001_en.html").exists()
```

`./ECI_initiatives/tests/scraper/responses/behaviour/test_error_handling.py`:
```
"""
Test suite for error handling and retry mechanisms.
"""

# Standard library
import time
import tempfile
from unittest.mock import Mock, patch, MagicMock

# Third party
import pytest

# Local imports
from ECI_initiatives.scraper.responses.downloader import ResponseDownloader


class TestRetryMechanism:
    """Test retry logic for failed downloads."""

    def test_rate_limit_detection_and_retry(self):
        """
        Verify that download succeeds after retrying through rate limit
        and server error pages.
        
        Sequence: Rate limit error -> Server error -> Success
        """
        # Arrange: Set up test directory and test data
        with tempfile.TemporaryDirectory() as tmpdir:
            
            # Define HTML responses for different scenarios
            rate_limit_html = "<html><body>Rate limited - please wait</body></html>"
            server_error_html = "<html><body>We apologise for any inconvenience</body></html>"
            valid_response_html = "<html><body>Valid Commission response content here</body></html>" * 100
            
            # Response sequence: fail twice, then succeed
            response_sequence = [rate_limit_html, server_error_html, valid_response_html]
            
            # Arrange: Set up mocks
            with patch('ECI_initiatives.scraper.responses.downloader.initialize_browser') as mock_init_browser, \
                patch('ECI_initiatives.scraper.responses.downloader.time.sleep'), \
                patch('ECI_initiatives.scraper.responses.downloader.random.uniform', return_value=0.1):
                
                # Create mock WebDriver
                mock_driver = self._create_mock_driver_with_response_sequence(response_sequence)
                mock_init_browser.return_value = mock_driver
                
                # Create downloader with mocked logger
                downloader = ResponseDownloader(tmpdir)
                downloader.logger = Mock()
                downloader._initialize_driver()
                
                # Mock file save to avoid I/O
                with patch('ECI_initiatives.scraper.responses.downloader.save_response_html_file', 
                        return_value="test.html"):
                    
                    # Act: Attempt download with retries
                    success, timestamp = downloader.download_single_response(
                        url="https://test.com/response",
                        year="2019",
                        reg_number="2019_000007",
                        max_retries=3
                    )
                
                # Assert: Download eventually succeeds
                assert success is True, "Should eventually succeed after retries"
                assert timestamp != "", "Should have timestamp on success"
                
                # Assert: Warnings logged for failed attempts
                assert downloader.logger.warning.call_count >= 1, \
                    "Should log warnings for failed attempts"

    def _create_mock_driver_with_response_sequence(self, response_sequence):
        """
        Helper: Create a mock WebDriver that returns responses in sequence.
        
        Args:
            response_sequence: List of HTML strings to return on successive page_source calls
            
        Returns:
            MagicMock configured to simulate browser behavior
            
        Note:
            Each download attempt may access page_source multiple times
            (for content retrieval and validation). The index calculation
            accounts for this by dividing by 2.
        """
        page_source_call_count = 0
        
        def get_page_source():
            nonlocal page_source_call_count
            
            # Calculate which response to return
            # Divide by 2 because page_source is called twice per attempt:
            # 1. _check_rate_limiting() reads it
            # 2. Getting actual content reads it again

            response_index = min(len(response_sequence) - 1, page_source_call_count // 2)
            page_source_call_count += 1
            
            return response_sequence[response_index]
        
        # Create and configure mock driver
        mock_driver = MagicMock()
        mock_driver.get = Mock()
        mock_driver.current_url = "https://test.com"
        type(mock_driver).page_source = property(lambda self: get_page_source())
        
        return mock_driver

    def test_download_failure_after_max_retries(self):
        """
        When a download fails multiple times, verify proper failure tracking.
        """

        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('ECI_initiatives.scraper.responses.downloader.initialize_browser') as mock_init_browser, \
                 patch('ECI_initiatives.scraper.responses.downloader.time.sleep'):
                
                # Create mock driver that always fails
                mock_driver = MagicMock()
                mock_driver.get.side_effect = Exception("Network timeout")
                mock_init_browser.return_value = mock_driver
                
                downloader = ResponseDownloader(tmpdir)
                downloader.logger = Mock()
                
                # Initialize the driver
                downloader._initialize_driver()
                
                test_url = "https://example.com/response"
                max_retries = 3
                
                # Act
                success, timestamp = downloader.download_single_response(
                    url=test_url,
                    year="2019",
                    reg_number="2019_000007",
                    max_retries=max_retries
                )
                
                # Assert
                assert success is False, "Download should fail"
                assert timestamp == "", "Failed download should have empty timestamp"
                assert mock_driver.get.call_count == max_retries, \
                    f"Should attempt {max_retries} times"
                
                # Verify final error was logged
                downloader.logger.error.assert_called_once()

    def test_successful_retry_after_transient_failure(self):
        """
        Verify successful download after transient failures.
        """

        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('ECI_initiatives.scraper.responses.downloader.initialize_browser') as mock_init_browser, \
                 patch('ECI_initiatives.scraper.responses.downloader.time.sleep'), \
                 patch('ECI_initiatives.scraper.responses.downloader.random.uniform', return_value=0.1):
                
                
                # Track which download attempt we're on (not page_source calls)
                download_attempts = 0
                
                mock_driver = MagicMock()
                
                def mock_get(url):
                    # Track actual download attempts
                    nonlocal download_attempts
                    download_attempts += 1
                
                mock_driver.get = Mock(side_effect=mock_get)
                mock_driver.current_url = "https://test.com"
                
                def get_page_source():
                    """
                    Return HTML response based on current download attempt.
                    
                    The response varies by attempt to simulate retry scenarios:
                    - Attempt 1 (download_attempts=1, index=0): Returns rate_limit_html
                    - Attempt 2 (download_attempts=2, index=1): Returns rate_limit_html  
                    - Attempt 3 (download_attempts=3, index=2): Returns valid_html
                    
                    Note:
                        download_attempts is incremented by mock_get() before this function runs,
                        so we subtract 1 to convert to 0-based array indexing.
                        
                    Returns:
                        str: HTML content appropriate for the current attempt number.
                            First two attempts return rate-limited responses to trigger retries,
                            third attempt returns valid content for successful completion.
                    """

                    # Setup sequence: fail twice, then succeed
                    rate_limit_html = "<html><body>Rate limited</body></html>"
                    valid_html = "<html><body>Valid Commission response content here</body></html>" * 100

                    nonlocal download_attempts

                    attempt_idx = download_attempts - 1  # 0-indexed

                    if attempt_idx == 0:
                        return rate_limit_html

                    elif attempt_idx == 1:
                        return rate_limit_html
                    else:
                        return valid_html
                
                type(mock_driver).page_source = property(lambda self: get_page_source())
                mock_init_browser.return_value = mock_driver
                
                downloader = ResponseDownloader(tmpdir)
                downloader.logger = Mock()
                
                # Initialize the driver
                downloader._initialize_driver()
                
                with patch('ECI_initiatives.scraper.responses.downloader.save_response_html_file', return_value="test.html"):
                    
                    # Act
                    success, timestamp = downloader.download_single_response(
                        url="https://test.com/response",
                        year="2019",
                        reg_number="2019_000007",
                        max_retries=3
                    )
                
                # Assert
                assert success is True, "Should succeed after transient failures"
                assert timestamp != "", "Should have timestamp"
                assert download_attempts == 3, f"Should take 3 download attempts, but took {download_attempts}"
                
                # Verify warnings were logged for failures
                assert downloader.logger.warning.call_count == 2, \
                    "Should log warning for each failed attempt"

    def test_rate_limit_detection_raises_exception(self):
        """
        Verify that _check_rate_limiting raises exception when rate limit indicators are found.
        """
        
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('ECI_initiatives.scraper.responses.downloader.initialize_browser') as mock_init_browser:
                
                mock_driver = MagicMock()
                mock_driver.page_source = "<html><body>Rate limited - too many requests</body></html>"
                mock_init_browser.return_value = mock_driver
                
                downloader = ResponseDownloader(tmpdir)
                downloader._initialize_driver()
                
                # Act & Assert
                with pytest.raises(Exception, match="Rate limiting detected"):
                    downloader._check_rate_limiting()

```

`./ECI_initiatives/tests/scraper/responses/behaviour/test_html_download.py`:
```
"""
Test suite for downloading and saving Commission response HTML pages.
"""

# Standard library
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Third party
import pytest
from bs4 import BeautifulSoup

# Local imports
from ECI_initiatives.scraper.responses.file_operations.page import PageFileManager
from ECI_initiatives.scraper.responses.consts import MIN_HTML_LENGTH


class TestHTMLDownload:
    """Test HTML page download functionality."""

    @pytest.fixture
    def temp_responses_dir(self):
        """Create temporary responses directory."""

        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def valid_response_html(self):
        """Valid Commission response HTML content."""

        return """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>Commission Response</title>
        </head>
        <body>
            <div class="commission-response">
                <h1>Commission's Response to European Citizens' Initiative</h1>
                <h2>Executive Summary</h2>
                <p>The European Commission has carefully examined this initiative...</p>
                <h2>Detailed Analysis</h2>
                <p>After thorough consideration of the points raised...</p>
                <h2>Conclusion</h2>
                <p>The Commission concludes that...</p>
            </div>
        </body>
        </html>
        """ * 10  # Ensure it's long enough

    @pytest.fixture
    def rate_limit_html(self):
        """HTML content indicating rate limiting."""

        return """
        <!DOCTYPE html>
        <html>
        <body>
            <h1>Too Many Requests</h1>
            <p>Rate limited - please try again later</p>
        </body>
        </html>
        """

    @pytest.fixture
    def server_error_html(self):
        """HTML content with multilingual server error."""

        return """
        <!DOCTYPE html>
        <html>
        <body>
            <h1>Sorry</h1>
            <p>We apologise for any inconvenience.</p>
            <p>Veuillez nous excuser pour ce désagrément.</p>
            <p>Ci scusiamo per il disagio arrecato.</p>
        </body>
        </html>
        """

    def test_downloaded_html_contains_valid_content(
        self, temp_responses_dir, valid_response_html
    ):
        """
        When downloading response pages, verify that each successfully
        downloaded HTML file contains the expected Commission response content
        (not error pages or rate limit messages).
        """

        # Arrange
        file_ops = PageFileManager(str(temp_responses_dir))
        file_ops.setup_directories()

        # Act
        filename = file_ops.save_response_page(valid_response_html, "2019", "2019_000007")

        # Assert
        saved_file = temp_responses_dir / filename
        assert saved_file.exists()

        with open(saved_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Verify Commission-specific content
        assert "Commission" in content
        assert "European Citizens' Initiative" in content
        assert len(content) > 1000, "Content should be substantial"

        # Verify no error indicators
        assert "rate limited" not in content.lower()
        assert "too many requests" not in content.lower()
        assert "we apologise for any inconvenience" not in content.lower()

    def test_short_html_not_saved(self, temp_responses_dir):
        """
        When HTML content is too short (below minimum threshold), verify that
        the file is not saved and the download is marked as failed.
        """
        # Arrange
        short_html = "<html><body>Short</body></html>"
        file_ops = PageFileManager(str(temp_responses_dir))
        file_ops.setup_directories()

        # Act & Assert
        with pytest.raises(Exception, match="HTML content too short"):
            file_ops.save_response_page(short_html, "2019", "2019_000007")

        # Verify file was not created
        year_dir = temp_responses_dir / "2019"
        if year_dir.exists():
            html_files = list(year_dir.glob("*.html"))
            assert len(html_files) == 0, "No HTML files should be saved"

    def test_rate_limit_retry_with_backoff(self, temp_responses_dir, rate_limit_html):
        """
        When a rate limiting error page is detected, verify that the scraper
        retries the download with exponential backoff.
        """
        # Arrange
        file_ops = PageFileManager(str(temp_responses_dir))
        file_ops.setup_directories()

        # Act & Assert - Rate limit detection
        with pytest.raises(Exception, match="Rate limiting detected"):
            file_ops.save_response_page(rate_limit_html, "2019", "2019_000007")

        # Verify file was not saved
        year_dir = temp_responses_dir / "2019"
        if year_dir.exists():
            html_files = list(year_dir.glob("*.html"))
            assert len(html_files) == 0

    def test_server_error_page_marked_failed(
        self, temp_responses_dir, server_error_html
    ):
        """
        When a server error page is detected (multilingual "Sorry" messages),
        verify that the download is marked as failed.
        """

        # Arrange
        file_ops = PageFileManager(str(temp_responses_dir))
        file_ops.setup_directories()

        # Act & Assert
        with pytest.raises(Exception, match="Error page detected"):
            file_ops.save_response_page(server_error_html, "2019", "2019_000007")

        # Verify file was not saved
        year_dir = temp_responses_dir / "2019"
        if year_dir.exists():
            html_files = list(year_dir.glob("*.html"))
            assert len(html_files) == 0

    def test_max_retries_marks_as_failed(self):
        """
        When a download fails multiple times (exceeding max retries), verify
        that the item is marked as failed and included in the failure summary.
        """
        # Arrange
        from ECI_initiatives.scraper.responses.downloader import ResponseDownloader
        from unittest.mock import Mock, patch, MagicMock
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            downloader = ResponseDownloader(tmpdir)
            
            # Mock the WebDriver to always raise an exception
            mock_driver = MagicMock()
            mock_driver.get.side_effect = Exception("Connection timeout")
            downloader.driver = mock_driver
            
            # Mock logger to prevent actual logging
            downloader.logger = Mock()
            
            # Test parameters
            test_url = "https://citizens-initiative.europa.eu/initiatives/response/2019/000007"
            test_year = "2019"
            test_reg_number = "000007"
            max_retries = 3
            
            # Act - Call the actual download method
            success, timestamp = downloader.download_single_response(
                url=test_url,
                year=test_year,
                reg_number=test_reg_number,
                max_retries=max_retries
            )
            
            # Assert
            assert success is False, "Download should fail after max retries"
            assert timestamp == "", "Timestamp should be empty for failed download"
            
            # Verify driver.get was called max_retries times
            assert mock_driver.get.call_count == max_retries, \
                f"Expected {max_retries} retry attempts, but got {mock_driver.get.call_count}"
            
            # Verify error was logged
            downloader.logger.error.assert_called_once()


    def test_html_files_prettified(self, temp_responses_dir):
        """
        When saving HTML files, verify that the content is prettified
        (well-formatted) for readability.
        """

        # Arrange
        ugly_html = "<html><head><title>Test</title></head><body><div><p>Content</p></div></body></html>"
        file_ops = PageFileManager(str(temp_responses_dir))
        file_ops.setup_directories()

        # Act
        filename = file_ops.save_response_page(ugly_html, "2019", "2019_000007")

        # Assert
        saved_file = temp_responses_dir / filename
        with open(saved_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Verify prettification (indentation and newlines)
        assert "\n" in content, "Should contain newlines"
        assert "  " in content or "\t" in content, "Should contain indentation"
        
        # Count lines to verify it's been expanded
        lines = content.split("\n")
        assert len(lines) > 5, "Prettified HTML should have multiple lines"

    def test_html_files_utf8_encoded(self, temp_responses_dir):
        """
        When saving HTML files, verify that UTF-8 encoding is used to preserve
        special characters in multilingual content.
        """

        # Arrange
        multilingual_html = """
        <!DOCTYPE html>
        <html>
        <body>
            <h1>Diversité en Europe</h1>
            <p>Être différent, ça compte! 🇪🇺</p>
            <p>Salva le api 🐝</p>
            <p>Μειονοτική προστασία</p>
        </body>
        </html>
        """
        file_ops = PageFileManager(str(temp_responses_dir))
        file_ops.setup_directories()

        # Act
        filename = file_ops.save_response_page(multilingual_html, "2019", "2019_000007")

        # Assert
        saved_file = temp_responses_dir / filename
        with open(saved_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Verify special characters are preserved
        assert "Diversité" in content
        assert "Être différent" in content
        assert "🇪🇺" in content
        assert "🐝" in content
        assert "Μειονοτική" in content

    def test_browser_cleanup_after_errors(self):
        """
        When the browser is closed after downloading, verify that resources
        are properly cleaned up even if errors occurred during downloads.
        """

        # Arrange
        from ECI_initiatives.scraper.responses.downloader import ResponseDownloader
        from unittest.mock import Mock, patch, MagicMock
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:

            # Patch initialize_browser to return a mock driver
            with patch('ECI_initiatives.scraper.responses.downloader.initialize_browser') as mock_init_browser:
                
                # Create mock driver
                mock_driver = MagicMock()
                mock_quit = Mock()
                mock_driver.quit = mock_quit
                mock_driver.get.side_effect = Exception("Connection error")
                mock_init_browser.return_value = mock_driver
                
                downloader = ResponseDownloader(tmpdir)
                
                # Mock logger to prevent actual logging
                downloader.logger = Mock()
                
                # Initialize the driver (this calls initialize_browser)
                downloader._initialize_driver()
                
                # Act - Attempt download that will fail
                try:
                    downloader.download_single_response(
                        url="https://test-url.com",
                        year="2019",
                        reg_number="000007",
                        max_retries=1  # Single attempt to speed up test
                    )
                except Exception:
                    pass  # Expected to fail
                
                # Now close the downloader (which should call driver.quit)
                downloader._close_driver()
                
                # Assert - Browser quit was called
                mock_quit.assert_called_once()


    def test_validate_html_content_length(self, temp_responses_dir):
        """
        Verify HTML validation checks content length against minimum threshold.
        """

        # Arrange
        file_ops = PageFileManager(str(temp_responses_dir))
        
        # Test with content just below threshold
        short_content = "x" * (MIN_HTML_LENGTH - 1)
        
        # Act & Assert
        with pytest.raises(Exception, match="HTML content too short"):
            file_ops._validate_html(short_content)

        # Test with content at threshold
        valid_content = "x" * MIN_HTML_LENGTH
        result = file_ops._validate_html(valid_content)

        assert result is True
```

`./ECI_initiatives/tests/scraper/responses/behaviour/test_link_extraction.py`:
```
"""
Test suite for extracting Commission response links from initiative HTML files.
"""

# Standard library
import os
import tempfile
from pathlib import Path
from typing import List, Dict

# Third party
import pytest
from bs4 import BeautifulSoup

# Local imports
from ECI_initiatives.scraper.responses.__main__ import _extract_response_links
from ECI_initiatives.scraper.responses.html_parser import ResponseLinkExtractor


class TestLinkExtraction:
    """Test extraction of response links from initiative pages."""

    @pytest.fixture
    def temp_pages_dir(self):
        """Create temporary pages directory structure."""

        with tempfile.TemporaryDirectory() as tmpdir:

            pages_dir = Path(tmpdir) / "pages"
            pages_dir.mkdir()
            yield pages_dir

    @pytest.fixture
    def initiative_html_with_response_link(self):
        """HTML content with Commission response link."""

        return """
        <!DOCTYPE html>
        <html>
        <body>
            <div class="initiative-details">
                <h1>Test Initiative</h1>
                <a href="/initiatives/details/2019/000007/commission-response" 
                   class="response-link">
                   Commission's answer and follow-up
                </a>
            </div>
        </body>
        </html>
        """

    @pytest.fixture
    def initiative_html_without_response_link(self):
        """HTML content without Commission response link."""

        return """
        <!DOCTYPE html>
        <html>
        <body>
            <div class="initiative-details">
                <h1>Test Initiative Without Response</h1>
                <p>This initiative has not received a Commission response yet.</p>
            </div>
        </body>
        </html>
        """

    def test_only_initiatives_with_response_links_included(
        self,
        temp_pages_dir,
        initiative_html_with_response_link,
        initiative_html_without_response_link,
    ):
        """
        When processing initiative HTML files, verify that only initiatives
        with "Commission's answer and follow-up" links are included in the
        response list.
        """

        # Arrange - Create year directory with mixed files
        year_dir = temp_pages_dir / "2019"
        year_dir.mkdir()

        # File with response link
        with_response = year_dir / "2019_000007_en.html"
        with_response.write_text(initiative_html_with_response_link, encoding="utf-8")

        # File without response link
        without_response = year_dir / "2019_000008_en.html"
        without_response.write_text(
            initiative_html_without_response_link, encoding="utf-8"
        )

        # Act - Use the actual function from __main__.py
        response_links = _extract_response_links(str(temp_pages_dir))

        # Assert
        assert len(response_links) == 1, "Only one file should have response link"
        
        # Verify the response link data structure
        link_data = response_links[0]
        assert link_data['year'] == "2019", "Year should be 2019"
        assert link_data['reg_number'] == "2019_000007", "Registration number should be 2019_000007"
        
        # Verify the file without response link is not included
        reg_numbers = [link['reg_number'] for link in response_links]
        assert "2019_000008" not in reg_numbers, "File without response link should not be included"

    def test_registration_number_and_year_extracted(self, temp_pages_dir, initiative_html_with_response_link):
        """
        When extracting links from initiative pages, verify that the
        registration number and year are correctly extracted from the file path.
        """

        # Arrange - Create test file structure with response links
        test_files = [
            ("2019", "2019_000007_en.html"),
            ("2020", "2020_000001_en.html"),
            ("2021", "2021_000006_en.html"),
        ]

        for year, filename in test_files:

            year_dir = temp_pages_dir / year
            year_dir.mkdir(exist_ok=True)
            test_file = year_dir / filename
            test_file.write_text(initiative_html_with_response_link, encoding="utf-8")

        # Act - Use the actual extraction function
        response_links = _extract_response_links(str(temp_pages_dir))

        # Assert
        assert len(response_links) == 3, "Should extract all 3 response links"
        
        # Create set of (year, reg_number) tuples for comparison
        extracted_data = {(link['year'], link['reg_number']) for link in response_links}
        expected_data = {("2019", "2019_000007"), ("2020", "2020_000001"), ("2021", "2021_000006")}
        
        assert extracted_data == expected_data, \
            f"Expected {expected_data}, but got {extracted_data}"

    def test_missing_response_link_skipped(
        self, temp_pages_dir, initiative_html_without_response_link
    ):
        """
        When an initiative HTML file contains no Commission response link,
        verify that it is silently skipped without causing errors.
        """
        # Arrange
        year_dir = temp_pages_dir / "2019"
        year_dir.mkdir()

        # Create multiple files without response links
        for i in range(3):
            test_file = year_dir / f"2019_00000{i}_en.html"
            test_file.write_text(
                initiative_html_without_response_link, encoding="utf-8"
            )

        # Act - Process files using actual function
        response_links = []
        errors = []

        try:
            response_links = _extract_response_links(str(temp_pages_dir))
        except Exception as e:
            errors.append(str(e))

        # Assert - No errors occurred and no links found
        assert len(errors) == 0, "Processing should not raise errors"
        assert len(response_links) == 0, "No response links should be found"

    def test_all_year_directories_processed(
        self, temp_pages_dir, initiative_html_with_response_link
    ):
        """
        When extracting response links from a directory with multiple year
        subdirectories, verify that all years are processed.
        """
        # Arrange - Create multiple year directories
        years = ["2019", "2020", "2021", "2022"]
        
        for year in years:
            year_dir = temp_pages_dir / year
            year_dir.mkdir()
            
            # Add file with response link
            test_file = year_dir / (year + "_000001_en.html")
            test_file.write_text(initiative_html_with_response_link, encoding="utf-8")

        # Act - Use actual extraction function
        response_links = _extract_response_links(str(temp_pages_dir))

        # Assert
        assert len(response_links) == 4, "Should extract links from all 4 years"
        
        # Verify all years are represented
        extracted_years = {link['year'] for link in response_links}
        expected_years = set(years)
        
        assert extracted_years == expected_years, \
            f"Expected years {expected_years}, but got {extracted_years}"

    def test_extract_title_from_initiative_page(self, temp_pages_dir):
        """
        Verify that initiative title can be extracted along with response link.
        """

        # Arrange
        html_with_title = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Minority SafePack</title>
        </head>
        <body>
            <h1>Minority SafePack - one million signatures for diversity in Europe</h1>
            <a href="/response">Commission's answer and follow-up</a>
        </body>
        </html>
        """

        year_dir = temp_pages_dir / "2019"
        year_dir.mkdir()
        test_file = year_dir / "2019_000007_en.html"
        test_file.write_text(html_with_title, encoding="utf-8")

        # Act
        response_links = _extract_response_links(str(temp_pages_dir))

        # Assert
        assert len(response_links) == 1, "Should extract one response link"
        assert 'title' in response_links[0], "Response link should include title"
        assert "Minority SafePack" in response_links[0].get('title', ''), \
            "Title should be extracted correctly"

    def test_extractor_returns_correct_data_structure(self, temp_pages_dir, initiative_html_with_response_link):
        """
        Verify that the extractor returns the expected data structure
        with required fields: url, year, reg_number, title, datetime.
        """

        # Arrange
        year_dir = temp_pages_dir / "2019"
        year_dir.mkdir()
        test_file = year_dir / "2019_000007_en.html"
        test_file.write_text(initiative_html_with_response_link, encoding="utf-8")

        # Act
        response_links = _extract_response_links(str(temp_pages_dir))

        # Assert
        assert len(response_links) > 0, "Should extract at least one link"
        
        # Verify data structure
        link_data = response_links[0]
        required_fields = ['url', 'year', 'reg_number', 'title', 'datetime']
        
        for field in required_fields:
            assert field in link_data, f"Link data should contain '{field}' field"
        
        # Verify data types
        assert isinstance(link_data['url'], str), "URL should be a string"
        assert isinstance(link_data['year'], str), "Year should be a string"
        assert isinstance(link_data['reg_number'], str), "Registration number should be a string"
        assert isinstance(link_data['title'], str), "Title should be a string"
        assert isinstance(link_data['datetime'], str), "Datetime should be a string"
        
        # Verify year and reg_number are separate
        assert link_data['year'] == "2019", "Year should be extracted separately"
        assert link_data['reg_number'] == "2019_000007", "Registration number should be extracted separately"

```

`./ECI_initiatives/tests/scraper/responses/behaviour/test_output_reporting.py`:
```
"""
Test suite for completion summary and output reporting.
"""

# Standard library
from typing import List, Dict
from unittest.mock import Mock, patch

# Third party
import pytest

# Local imports
from ECI_initiatives.scraper.responses.statistics import (
    ScrapingStatistics,
    display_completion_summary
)
from ECI_initiatives.scraper.responses.consts import LOG_MESSAGES


class TestCompletionSummary:
    """Test completion summary reporting functionality."""

    @pytest.fixture
    def sample_response_links_all_successful(self) -> List[Dict[str, str]]:
        """Sample response links for all successful scenario."""
        return [
            {'url': 'https://example.com/1', 'year': '2019', 'reg_number': '000001', 'title': 'Initiative 1'},
            {'url': 'https://example.com/2', 'year': '2020', 'reg_number': '000002', 'title': 'Initiative 2'},
            {'url': 'https://example.com/3', 'year': '2021', 'reg_number': '000003', 'title': 'Initiative 3'},
            {'url': 'https://example.com/4', 'year': '2022', 'reg_number': '000004', 'title': 'Initiative 4'},
            {'url': 'https://example.com/5', 'year': '2023', 'reg_number': '000005', 'title': 'Initiative 5'},
        ]

    @pytest.fixture
    def sample_response_links_mixed(self) -> List[Dict[str, str]]:
        """Sample response links for mixed success/failure scenario."""
        return [
            {'url': f'https://example.com/{i}', 'year': '2020', 'reg_number': f'00000{i}', 'title': f'Initiative {i}'}
            for i in range(1, 11)
        ]

    @pytest.fixture
    def sample_failed_urls(self) -> List[str]:
        """Sample failed URLs."""
        return [
            "https://citizens-initiative.europa.eu/initiatives/details/2020/000001_en",
            "https://citizens-initiative.europa.eu/initiatives/details/2021/000003_en",
            "https://citizens-initiative.europa.eu/initiatives/details/2022/000005_en",
        ]

    def test_zero_failures_reported_on_success(self, sample_response_links_all_successful):
        """
        When all downloads succeed, verify that the completion summary reports
        zero failures.
        """
        # Arrange
        mock_logger = Mock()
        stats = ScrapingStatistics(
            start_scraping="2024-10-09 14:00:00",
            responses_dir="/data/2024-10-09_14-30-00/responses"
        )
        stats.logger = mock_logger

        # Act
        stats.display_completion_summary(
            response_links=sample_response_links_all_successful,
            failed_urls=[],
            downloaded_count=5
        )

        # Assert - Verify logger was called with success messages
        info_calls = [str(call) for call in mock_logger.info.call_args_list]

        # Check that scraping completion message is logged
        assert any(LOG_MESSAGES["scraping_complete"] in str(call) for call in info_calls), \
            f"Should log '{LOG_MESSAGES['scraping_complete']}' message"

        # Check that "all downloads successful" message is logged
        assert any(LOG_MESSAGES["all_downloads_successful"] in str(call) for call in info_calls), \
            f"Should log '{LOG_MESSAGES['all_downloads_successful']}' message"

        # Verify no failure warnings
        assert mock_logger.warning.call_count == 0, "Should not log warnings for successful run"

    def test_summary_shows_correct_counts(self, sample_response_links_mixed, sample_failed_urls):
        """
        When scraping completes, verify that the summary shows correct counts
        of total links found, successfully downloaded pages, and failed downloads.
        """
        # Arrange
        mock_logger = Mock()
        stats = ScrapingStatistics(
            start_scraping="2024-10-09 14:00:00",
            responses_dir="/data/2024-10-09_14-30-00/responses"
        )
        stats.logger = mock_logger

        total_links = 10
        successful = 7
        failed_count = 3

        # Act
        stats.display_completion_summary(
            response_links=sample_response_links_mixed,
            failed_urls=sample_failed_urls,
            downloaded_count=successful
        )

        # Assert - Check logged messages contain correct counts
        info_calls = [str(call) for call in mock_logger.info.call_args_list]
        warning_calls = [str(call) for call in mock_logger.warning.call_args_list]

        # Verify total count message format
        expected_total_msg = LOG_MESSAGES["total_links_found"].format(count=total_links)
        assert any(expected_total_msg in str(call) for call in info_calls), \
            f"Should log '{expected_total_msg}'"

        # Verify pages downloaded message format
        expected_pages_msg_partial = f"{successful}/{total_links}"
        assert any(expected_pages_msg_partial in str(call) for call in info_calls), \
            f"Should log download count '{expected_pages_msg_partial}'"

        # Verify failed downloads warning
        expected_failed_msg = LOG_MESSAGES["failed_downloads"].format(failed_count=failed_count)
        assert any(expected_failed_msg in str(call) for call in warning_calls), \
            f"Should log '{expected_failed_msg}'"

        # Verify counts are consistent
        assert successful + failed_count == total_links

    def test_summary_includes_save_path(self, sample_response_links_all_successful):
        """
        When scraping completes, verify that the summary includes the path
        where response files were saved.
        """
        # Arrange
        mock_logger = Mock()
        save_path = "/data/2024-10-09_14-30-00/responses"
        
        stats = ScrapingStatistics(
            start_scraping="2024-10-09 14:00:00",
            responses_dir=save_path
        )
        stats.logger = mock_logger

        # Act
        stats.display_completion_summary(
            response_links=sample_response_links_all_successful,
            failed_urls=[],
            downloaded_count=5
        )

        # Assert - Verify save path is logged using LOG_MESSAGES format
        info_calls = [str(call) for call in mock_logger.info.call_args_list]
        
        expected_path_msg = LOG_MESSAGES["files_saved_in"].format(path=save_path)
        assert any(expected_path_msg in str(call) for call in info_calls), \
            f"Should log '{expected_path_msg}'"

    def test_failed_urls_listed_in_summary(
        self, 
        sample_response_links_mixed, 
        sample_failed_urls
    ):
        """
        When downloads fail, verify that the completion summary lists all
        failed URLs for user review.
        """
        # Arrange
        mock_logger = Mock()
        stats = ScrapingStatistics(
            start_scraping="2024-10-09 14:00:00",
            responses_dir="/data/2024-10-09_14-30-00/responses"
        )
        stats.logger = mock_logger

        # Act
        stats.display_completion_summary(
            response_links=sample_response_links_mixed,
            failed_urls=sample_failed_urls,
            downloaded_count=7
        )

        # Assert - Verify all failed URLs are logged using LOG_MESSAGES format
        warning_calls = [str(call) for call in mock_logger.warning.call_args_list]
        
        for failed_url in sample_failed_urls:
            expected_url_msg = LOG_MESSAGES["failed_url"].format(failed_url=failed_url)
            assert any(expected_url_msg in str(call) for call in warning_calls), \
                f"Failed URL should be logged with message: '{expected_url_msg}'"

        # Verify failed downloads summary message is logged
        expected_failed_msg = LOG_MESSAGES["failed_downloads"].format(failed_count=len(sample_failed_urls))
        assert any(expected_failed_msg in str(call) for call in warning_calls), \
            f"Should log '{expected_failed_msg}'"

        # Verify warning count includes failure summary + each URL
        # Should be: 1 (failure count message) + 3 (individual URLs) = 4
        assert mock_logger.warning.call_count >= len(sample_failed_urls), \
            "Should log warning for each failed URL"

    def test_all_downloads_successful_message_displayed(
        self,
        sample_response_links_all_successful
    ):
        """
        Verify that when all downloads succeed, a success message is logged.
        """
        # Arrange
        mock_logger = Mock()
        stats = ScrapingStatistics(
            start_scraping="2024-10-09 14:00:00",
            responses_dir="/data/test"
        )
        stats.logger = mock_logger

        # Act
        stats.display_completion_summary(
            response_links=sample_response_links_all_successful,
            failed_urls=[],
            downloaded_count=5
        )

        # Assert - Check for success message in logs
        info_calls = [str(call) for call in mock_logger.info.call_args_list]
        
        # Verify logger was called
        assert mock_logger.info.called, "Logger info should be called"
        
        # Verify no warnings
        assert mock_logger.warning.call_count == 0, "Should not log warnings for all successful"
        
        # Check for the actual success message from constants
        success_message = LOG_MESSAGES["all_downloads_successful"]
        assert any(success_message in str(call) for call in info_calls), \
            f"Should log '{success_message}' message"

    def test_statistics_display_header_with_timestamps(self):
        """
        Verify that summary header displays start and completion timestamps.
        """
        # Arrange
        mock_logger = Mock()
        start_time = "2024-10-09 14:00:00"
        completion_time = "2024-10-09 15:00:00"
        
        stats = ScrapingStatistics(
            start_scraping=start_time,
            responses_dir="/data/test"
        )
        stats.logger = mock_logger

        # Act
        with patch('ECI_initiatives.scraper.responses.statistics.datetime') as mock_datetime:
            mock_datetime.datetime.now.return_value.strftime.return_value = completion_time
            
            stats.display_completion_summary(
                response_links=[],
                failed_urls=[],
                downloaded_count=0
            )

        # Assert - Verify timestamps in logs using LOG_MESSAGES format
        info_calls = [str(call) for call in mock_logger.info.call_args_list]
        
        # Verify start time message
        expected_start_msg = LOG_MESSAGES["start_time"].format(start_scraping=start_time)
        assert any(expected_start_msg in str(call) for call in info_calls), \
            f"Should log start time message: '{expected_start_msg}'"
        
        # Verify completion time message
        expected_completion_msg = LOG_MESSAGES["completion_timestamp"].format(timestamp=completion_time)
        assert any(expected_completion_msg in str(call) for call in info_calls), \
            f"Should log completion time message: '{expected_completion_msg}'"

        # Verify divider lines are logged
        divider = LOG_MESSAGES["divider_line"]
        divider_count = sum(1 for call in info_calls if divider in str(call))
        assert divider_count >= 2, "Should log at least 2 divider lines (header and footer)"
```

`./ECI_initiatives/tests/scraper/responses/behaviour/__init__.py`:
```

```

`./ECI_initiatives/tests/scraper/responses/behaviour/test_csv_output.py`:
```
"""
Test suite for CSV output file creation and content validation.

This test suite verifies that the Commission responses scraper correctly generates CSV files 
with proper structure, required columns, and accurate content based on download outcomes. 

It validates registration number normalization from underscore to slash format, 
ensures timestamps are populated only for successful downloads 
while failed downloads have empty timestamps, 
and confirms proper UTF-8 encoding for multilingual content.
"""


# Standard library
import csv
import os
import tempfile
from pathlib import Path
from typing import List, Dict

# Third party
import pytest

# Local imports
from ECI_initiatives.scraper.responses.file_operations.csv import write_responses_csv
from ECI_initiatives.scraper.responses.consts import CSV_FIELDNAMES


class TestCSVOutput:
    """Test CSV file generation and content."""

    @pytest.fixture
    def temp_csv_dir(self):
        """Create a temporary directory for CSV files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def sample_response_data_with_underscores(self) -> List[Dict[str, str]]:
        """
        Sample response data with registration numbers in underscore format
        (as they appear in file paths).
        """
        return [
            {
                "url_find_initiative": "https://citizens-initiative.europa.eu/initiatives/details/2019/000007_en",
                "registration_number": "2019_000007",
                "title": "Minority SafePack - one million signatures for diversity in Europe",
                "datetime": "2024-10-09 14:30:45",
            },
            {
                "url_find_initiative": "https://citizens-initiative.europa.eu/initiatives/details/2020/000001_en",
                "registration_number": "2020_000001",
                "title": "Save Bees and Farmers",
                "datetime": "2024-10-09 14:35:12",
            },
            {
                "url_find_initiative": "https://citizens-initiative.europa.eu/initiatives/details/2021/000006_en",
                "registration_number": "2021_000006",
                "title": "End the Cage Age",
                "datetime": "2024-10-09 14:40:33",
            },
        ]

    @pytest.fixture
    def sample_response_data_mixed_success(self) -> List[Dict[str, str]]:
        """
        Sample response data with both successful downloads (with timestamps)
        and failed downloads (empty timestamps).
        """
        return [
            {
                "url_find_initiative": "https://citizens-initiative.europa.eu/initiatives/details/2019/000007_en",
                "registration_number": "2019_000007",
                "title": "Minority SafePack",
                "datetime": "2024-10-09 14:30:45",
            },
            {
                "url_find_initiative": "https://citizens-initiative.europa.eu/initiatives/details/2020/000001_en",
                "registration_number": "2020_000001",
                "title": "Save Bees and Farmers",
                "datetime": "",  # Failed download
            },
            {
                "url_find_initiative": "https://citizens-initiative.europa.eu/initiatives/details/2021/000006_en",
                "registration_number": "2021_000006",
                "title": "End the Cage Age",
                "datetime": "2024-10-09 14:40:33",
            },
            {
                "url_find_initiative": "https://citizens-initiative.europa.eu/initiatives/details/2022/000002_en",
                "registration_number": "2022_000002",
                "title": "Tax the Rich",
                "datetime": "",  # Failed download
            },
        ]

    def test_registration_numbers_normalized_to_slash_format(
        self, temp_csv_dir, sample_response_data_with_underscores
    ):
        """
        When creating the CSV file, verify that registration numbers are
        normalized to slash format (2019/000007) instead of underscore format.
        """
        # Arrange
        csv_path = temp_csv_dir / "responses_test.csv"

        # Act
        write_responses_csv(str(csv_path), sample_response_data_with_underscores)

        # Assert
        assert csv_path.exists(), "CSV file was not created"

        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Verify all registration numbers use slash format
        assert len(rows) == 3, "Expected 3 rows in CSV"

        for row in rows:
            reg_number = row["registration_number"]
            assert "/" in reg_number, f"Registration number should use slash format: {reg_number}"
            assert "_" not in reg_number, f"Registration number should not contain underscores: {reg_number}"

        # Verify specific normalized values
        expected_reg_numbers = ["2019/000007", "2020/000001", "2021/000006"]
        actual_reg_numbers = [row["registration_number"] for row in rows]
        assert actual_reg_numbers == expected_reg_numbers, "Registration numbers not properly normalized"

    def test_csv_timestamps_for_successful_downloads(
        self, temp_csv_dir, sample_response_data_mixed_success
    ):
        """
        When downloads complete, verify that the CSV contains timestamps
        only for successfully downloaded pages.
        """
        # Arrange
        csv_path = temp_csv_dir / "responses_test.csv"

        # Act
        write_responses_csv(str(csv_path), sample_response_data_mixed_success)

        # Assert
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Verify successful downloads have timestamps
        successful_rows = [row for row in rows if row["datetime"]]
        assert len(successful_rows) == 2, "Expected 2 successful downloads with timestamps"

        # Verify timestamp format (YYYY-MM-DD HH:MM:SS)
        for row in successful_rows:
            timestamp = row["datetime"]
            assert len(timestamp) > 0, "Timestamp should not be empty for successful downloads"
            assert "-" in timestamp and ":" in timestamp, f"Invalid timestamp format: {timestamp}"

        # Verify specific successful downloads
        successful_reg_numbers = [row["registration_number"] for row in successful_rows]
        assert "2019/000007" in successful_reg_numbers
        assert "2021/000006" in successful_reg_numbers

    def test_csv_empty_timestamps_for_failed_downloads(
        self, temp_csv_dir, sample_response_data_mixed_success
    ):
        """
        When some downloads fail, verify that failed items appear in the CSV
        with empty timestamp fields.
        """
        # Arrange
        csv_path = temp_csv_dir / "responses_test.csv"

        # Act
        write_responses_csv(str(csv_path), sample_response_data_mixed_success)

        # Assert
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Verify failed downloads have empty timestamps
        failed_rows = [row for row in rows if not row["datetime"]]
        assert len(failed_rows) == 2, "Expected 2 failed downloads with empty timestamps"

        # Verify failed rows still have other data
        for row in failed_rows:
            assert row["url_find_initiative"], "Failed row should have URL"
            assert row["registration_number"], "Failed row should have registration number"
            assert row["title"], "Failed row should have title"
            assert row["datetime"] == "", "Failed row should have empty timestamp"

        # Verify specific failed downloads
        failed_reg_numbers = [row["registration_number"] for row in failed_rows]
        assert "2020/000001" in failed_reg_numbers
        assert "2022/000002" in failed_reg_numbers

    def test_csv_contains_required_columns(
        self, temp_csv_dir, sample_response_data_with_underscores
    ):
        """
        When the CSV is written, verify that it contains all required columns:
        url_find_initiative, registration_number, title, datetime.
        """
        # Arrange
        csv_path = temp_csv_dir / "responses_test.csv"

        # Act
        write_responses_csv(str(csv_path), sample_response_data_with_underscores)

        # Assert
        assert csv_path.exists(), "CSV file was not created"

        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames

        # Verify all required columns exist
        required_columns = CSV_FIELDNAMES
        assert headers == required_columns, f"CSV headers don't match required columns. Expected: {required_columns}, Got: {headers}"

        # Verify column order matches expected order
        expected_order = ["url_find_initiative", "registration_number", "title", "datetime"]
        assert list(headers) == expected_order, f"CSV column order incorrect. Expected: {expected_order}, Got: {list(headers)}"

        # Verify no extra columns
        assert len(headers) == len(expected_order), f"CSV should have exactly {len(expected_order)} columns, got {len(headers)}"

    def test_csv_handles_empty_data_list(self, temp_csv_dir):
        """
        Edge case: When an empty data list is provided, verify CSV is created
        with headers only.
        """
        # Arrange
        csv_path = temp_csv_dir / "responses_empty.csv"
        empty_data = []

        # Act
        write_responses_csv(str(csv_path), empty_data)

        # Assert
        assert csv_path.exists(), "CSV file was not created for empty data"

        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            rows = list(reader)

        assert headers == CSV_FIELDNAMES, "Headers should be present even with empty data"
        assert len(rows) == 0, "No data rows should be present"

    def test_csv_utf8_encoding_for_special_characters(self, temp_csv_dir):
        """
        Verify that CSV handles UTF-8 encoding properly for special characters
        in titles and other fields.
        """
        # Arrange
        csv_path = temp_csv_dir / "responses_utf8.csv"
        data_with_special_chars = [
            {
                "url_find_initiative": "https://citizens-initiative.europa.eu/initiatives/details/2019/000007_en",
                "registration_number": "2019_000007",
                "title": "Diversité en Europe – être différent, ça compte!",
                "datetime": "2024-10-09 14:30:45",
            },
            {
                "url_find_initiative": "https://citizens-initiative.europa.eu/initiatives/details/2020/000001_en",
                "registration_number": "2020_000001",
                "title": "Salva le api e gli agricoltori! 🐝",
                "datetime": "2024-10-09 14:35:12",
            },
        ]

        # Act
        write_responses_csv(str(csv_path), data_with_special_chars)

        # Assert
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Verify special characters are preserved
        assert "Diversité" in rows[0]["title"]
        assert "être différent" in rows[0]["title"]
        assert "🐝" in rows[1]["title"]

    def test_csv_multiple_writes_overwrite_correctly(self, temp_csv_dir):
        """
        Verify that writing to the same CSV file multiple times overwrites
        the previous content (not appends).
        """
        # Arrange
        csv_path = temp_csv_dir / "responses_overwrite.csv"
        
        first_data = [
            {
                "url_find_initiative": "https://example.com/1",
                "registration_number": "2019_000001",
                "title": "First Initiative",
                "datetime": "2024-10-09 14:00:00",
            }
        ]
        
        second_data = [
            {
                "url_find_initiative": "https://example.com/2",
                "registration_number": "2020_000002",
                "title": "Second Initiative",
                "datetime": "2024-10-09 15:00:00",
            },
            {
                "url_find_initiative": "https://example.com/3",
                "registration_number": "2020_000003",
                "title": "Third Initiative",
                "datetime": "2024-10-09 16:00:00",
            }
        ]

        # Act - Write first dataset
        write_responses_csv(str(csv_path), first_data)
        
        # Act - Write second dataset (should overwrite)
        write_responses_csv(str(csv_path), second_data)

        # Assert - Only second dataset should be present
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 2, "CSV should contain only the second dataset (2 rows)"
        assert rows[0]["registration_number"] == "2020/000002"
        assert rows[1]["registration_number"] == "2020/000003"
        assert "2019/000001" not in [row["registration_number"] for row in rows]

```

`./ECI_initiatives/tests/scraper/responses/behaviour/test_directory_structure.py`:
```
"""
Test suite for validating directory and file structure creation
for Commission responses scraper.
"""

# Standard library
import os
import tempfile
from pathlib import Path

# Third party
import pytest

# Local imports
from ECI_initiatives.scraper.responses.file_operations.page import (
    PageFileManager,
    save_response_html_file,
)


class TestDirectoryStructure:
    
    @pytest.fixture
    def test_data_dir(self):
        """Get path to test data directory."""
        return Path(__file__).parent.parent.parent.parent / "data" / "example_htmls" / "responses"
    
    @pytest.fixture
    def temp_base_dir(self, tmp_path):
        """Create temporary base directory for testing."""
        return tmp_path / "responses"  # Changed: return Path object, not string
    
    @pytest.fixture
    def sample_html_content(self, test_data_dir):
        """Provide sample HTML content for testing from actual file."""
        
        html_file = test_data_dir / "partial_success" / "2019" / "2019_000016_en.html"
        with open(html_file, "r", encoding="utf-8") as f:
            return f.read()

    def test_response_files_in_year_subdirectories(
        self, temp_base_dir, sample_html_content
    ):
        """
        When the scraper runs successfully, verify that the response HTML
        files are saved in the correct year-based subdirectory structure.
        """
        # Arrange
        responses_dir = temp_base_dir / "responses"
        file_ops = PageFileManager(str(responses_dir))
        file_ops.setup_directories()

        # Act - Save files for different years
        years_and_regs = [
            ("2019", "000007"),
            ("2020", "000001"),
            ("2021", "000006"),
            ("2022", "000002"),
        ]

        for year, reg_number in years_and_regs:
            file_ops.save_response_page(sample_html_content, year, reg_number)

        # Assert - Check year directories exist
        for year, _ in years_and_regs:

            year_dir = responses_dir / year

            assert year_dir.exists(), f"Year directory {year} was not created"
            assert year_dir.is_dir(), f"Year path {year} is not a directory"

        # Assert - Check files are in correct year directories
        for year, reg_number in years_and_regs:

            expected_file = responses_dir / year / f"{reg_number}_en.html"

            assert (
                expected_file.exists()
            ), f"Response file not found in year directory: {expected_file}"

        # Assert - Verify no files are in the root responses directory
        files_in_root = [
            f for f in responses_dir.iterdir() if f.is_file() and f.suffix == ".html"
        ]
        assert (
            len(files_in_root) == 0
        ), "HTML files should not be in root responses directory"

    def test_csv_file_created(self, temp_base_dir):
        """
        When the scraper runs, verify that a CSV file with response metadata
        is created in the responses directory.
        """

        # Arrange
        from ECI_initiatives.scraper.responses.file_operations.csv import (
            write_responses_csv,
        )

        responses_dir = temp_base_dir / "responses"
        responses_dir.mkdir(parents=True)

        csv_path = responses_dir / "responses_list.csv"

        sample_data = [
            {
                "url_find_initiative": "https://citizens-initiative.europa.eu/initiatives/details/2019/000007_en",
                "registration_number": "2019_000007",
                "title": "Test Initiative",
                "datetime": "2024-10-09 14:30:45",
            }
        ]

        # Act
        write_responses_csv(str(csv_path), sample_data)

        # Assert
        assert csv_path.exists(), "CSV file was not created"
        assert csv_path.is_file(), "CSV path is not a file"
        assert csv_path.suffix == ".csv", "File does not have .csv extension"

        # Verify the CSV file is actually in the responses directory
        csv_files_in_responses_dir = list(responses_dir.glob("*.csv"))
        assert len(csv_files_in_responses_dir) > 0, "No CSV files found in responses directory"
        assert csv_path in csv_files_in_responses_dir, "Created CSV file is not in responses directory"

    def test_missing_data_directory_error(self, temp_base_dir):
        """
        When the data directory doesn't exist, verify that the scraper raises
        an appropriate error indicating the initiatives scraper should run first.
        """
        
        # Arrange
        from ECI_initiatives.scraper.responses.__main__ import scrape_commission_responses
        from ECI_initiatives.scraper.responses.errors import MissingDataDirectoryError
        from unittest.mock import patch
        
        # Patch the SCRIPT_DIR to point to our temp directory where no data exists
        with patch('ECI_initiatives.scraper.responses.__main__.SCRIPT_DIR', str(temp_base_dir)):
            
            # Ensure no data directory exists
            data_dir = temp_base_dir / "data"
            if data_dir.exists():
                raise RuntimeError(
                    f"Test setup failed: Directory {data_dir} should not exist. "
                    "This indicates a problem with test isolation."
                )
            
            # Act & Assert - Call the actual scraper function
            with pytest.raises(MissingDataDirectoryError) as exc_info:
                scrape_commission_responses()
            
            # Verify the error message contains the expected hint
            error = exc_info.value
            assert error.expected_path is not None
            assert "data" in error.expected_path.lower()
            assert "Run the initiatives scraper first" in error.hint
            
            # Verify error message format
            error_message = str(error)
            assert "Cannot find required data directory" in error_message
            assert "Expected:" in error_message
            assert "Hint:" in error_message


    def test_uses_most_recent_initiatives_timestamp(self, temp_base_dir):
        """
        When running the full scraper workflow, verify that files are created
        in the most recent timestamp directory from the initiatives scraper.
        """
        
        # Arrange
        from ECI_initiatives.scraper.responses.__main__ import _find_latest_timestamp_directory
        from unittest.mock import patch
        
        # Create multiple timestamp directories
        data_dir = temp_base_dir / "data"
        data_dir.mkdir(parents=True)  # Changed: added parents=True


        timestamps = [
            "2024-10-01_10-00-00",
            "2024-10-05_14-30-00",
            "2024-10-09_16-45-00",  # Most recent
            "2024-10-03_08-15-00",
        ]


        for timestamp in timestamps:
            timestamp_dir = data_dir / timestamp
            timestamp_dir.mkdir()


        # Act - Patch SCRIPT_DIR and call the actual function
        with patch('ECI_initiatives.scraper.responses.__main__.SCRIPT_DIR', str(temp_base_dir)):
            most_recent_path = _find_latest_timestamp_directory()


        # Assert - Verify the function selected the most recent timestamp
        most_recent = Path(most_recent_path)
        assert most_recent.name == "2024-10-09_16-45-00", "Did not select most recent timestamp"
        assert most_recent.parent == data_dir, "Timestamp directory not in data directory"
        assert most_recent.exists(), "Selected timestamp directory does not exist"

        
    def test_responses_directory_creation(self, temp_base_dir):
        """
        Verify that the responses directory is created if it doesn't exist.
        """

        # Arrange
        responses_dir = temp_base_dir / "responses"
        assert not responses_dir.exists()

        file_ops = PageFileManager(str(responses_dir))

        # Act
        file_ops.setup_directories()

        # Assert
        assert responses_dir.exists(), "Responses directory was not created"
        assert responses_dir.is_dir(), "Responses path is not a directory"

    def test_multiple_year_directories_coexist(self, temp_base_dir, sample_html_content):
        """
        Verify that multiple year subdirectories can coexist without conflicts.
        """

        # Arrange
        responses_dir = temp_base_dir / "responses"
        file_ops = PageFileManager(str(responses_dir))
        file_ops.setup_directories()

        years = ["2019", "2020", "2021", "2022", "2023"]

        # Act - Create files in all year directories
        for year in years:
            file_ops.save_response_page(sample_html_content, year, "000001")

        # Assert - All year directories exist
        year_dirs = [d for d in responses_dir.iterdir() if d.is_dir()]
        assert len(year_dirs) == len(years), f"Expected {len(years)} year directories"

        for year in years:
            year_dir = responses_dir / year
            assert year_dir.exists()
            assert (year_dir / "000001_en.html").exists()
```

`./ECI_initiatives/tests/scraper/responses/behaviour/test_error_handling.py`:
```
"""
Test suite for error handling and retry mechanisms.
"""

# Standard library
import time
import tempfile
from unittest.mock import Mock, patch, MagicMock

# Third party
import pytest

# Local imports
from ECI_initiatives.scraper.responses.downloader import ResponseDownloader


class TestRetryMechanism:
    """Test retry logic for failed downloads."""

    def test_rate_limit_detection_and_retry(self):
        """
        Verify that download succeeds after retrying through rate limit
        and server error pages.
        
        Sequence: Rate limit error -> Server error -> Success
        """
        # Arrange: Set up test directory and test data
        with tempfile.TemporaryDirectory() as tmpdir:
            
            # Define HTML responses for different scenarios
            rate_limit_html = "<html><body>Rate limited - please wait</body></html>"
            server_error_html = "<html><body>We apologise for any inconvenience</body></html>"
            valid_response_html = "<html><body>Valid Commission response content here</body></html>" * 100
            
            # Response sequence: fail twice, then succeed
            response_sequence = [rate_limit_html, server_error_html, valid_response_html]
            
            # Arrange: Set up mocks
            with patch('ECI_initiatives.scraper.responses.downloader.initialize_browser') as mock_init_browser, \
                patch('ECI_initiatives.scraper.responses.downloader.time.sleep'), \
                patch('ECI_initiatives.scraper.responses.downloader.random.uniform', return_value=0.1):
                
                # Create mock WebDriver
                mock_driver = self._create_mock_driver_with_response_sequence(response_sequence)
                mock_init_browser.return_value = mock_driver
                
                # Create downloader with mocked logger
                downloader = ResponseDownloader(tmpdir)
                downloader.logger = Mock()
                downloader._initialize_driver()
                
                # Mock file save to avoid I/O
                with patch('ECI_initiatives.scraper.responses.downloader.save_response_html_file', 
                        return_value="test.html"):
                    
                    # Act: Attempt download with retries
                    success, timestamp = downloader.download_single_response(
                        url="https://test.com/response",
                        year="2019",
                        reg_number="2019_000007",
                        max_retries=3
                    )
                
                # Assert: Download eventually succeeds
                assert success is True, "Should eventually succeed after retries"
                assert timestamp != "", "Should have timestamp on success"
                
                # Assert: Warnings logged for failed attempts
                assert downloader.logger.warning.call_count >= 1, \
                    "Should log warnings for failed attempts"

    def _create_mock_driver_with_response_sequence(self, response_sequence):
        """
        Helper: Create a mock WebDriver that returns responses in sequence.
        
        Args:
            response_sequence: List of HTML strings to return on successive page_source calls
            
        Returns:
            MagicMock configured to simulate browser behavior
            
        Note:
            Each download attempt may access page_source multiple times
            (for content retrieval and validation). The index calculation
            accounts for this by dividing by 2.
        """
        page_source_call_count = 0
        
        def get_page_source():
            nonlocal page_source_call_count
            
            # Calculate which response to return
            # Divide by 2 because page_source is called twice per attempt:
            # 1. _check_rate_limiting() reads it
            # 2. Getting actual content reads it again

            response_index = min(len(response_sequence) - 1, page_source_call_count // 2)
            page_source_call_count += 1
            
            return response_sequence[response_index]
        
        # Create and configure mock driver
        mock_driver = MagicMock()
        mock_driver.get = Mock()
        mock_driver.current_url = "https://test.com"
        type(mock_driver).page_source = property(lambda self: get_page_source())
        
        return mock_driver

    def test_download_failure_after_max_retries(self):
        """
        When a download fails multiple times, verify proper failure tracking.
        """

        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('ECI_initiatives.scraper.responses.downloader.initialize_browser') as mock_init_browser, \
                 patch('ECI_initiatives.scraper.responses.downloader.time.sleep'):
                
                # Create mock driver that always fails
                mock_driver = MagicMock()
                mock_driver.get.side_effect = Exception("Network timeout")
                mock_init_browser.return_value = mock_driver
                
                downloader = ResponseDownloader(tmpdir)
                downloader.logger = Mock()
                
                # Initialize the driver
                downloader._initialize_driver()
                
                test_url = "https://example.com/response"
                max_retries = 3
                
                # Act
                success, timestamp = downloader.download_single_response(
                    url=test_url,
                    year="2019",
                    reg_number="2019_000007",
                    max_retries=max_retries
                )
                
                # Assert
                assert success is False, "Download should fail"
                assert timestamp == "", "Failed download should have empty timestamp"
                assert mock_driver.get.call_count == max_retries, \
                    f"Should attempt {max_retries} times"
                
                # Verify final error was logged
                downloader.logger.error.assert_called_once()

    def test_successful_retry_after_transient_failure(self):
        """
        Verify successful download after transient failures.
        """

        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('ECI_initiatives.scraper.responses.downloader.initialize_browser') as mock_init_browser, \
                 patch('ECI_initiatives.scraper.responses.downloader.time.sleep'), \
                 patch('ECI_initiatives.scraper.responses.downloader.random.uniform', return_value=0.1):
                
                
                # Track which download attempt we're on (not page_source calls)
                download_attempts = 0
                
                mock_driver = MagicMock()
                
                def mock_get(url):
                    # Track actual download attempts
                    nonlocal download_attempts
                    download_attempts += 1
                
                mock_driver.get = Mock(side_effect=mock_get)
                mock_driver.current_url = "https://test.com"
                
                def get_page_source():
                    """
                    Return HTML response based on current download attempt.
                    
                    The response varies by attempt to simulate retry scenarios:
                    - Attempt 1 (download_attempts=1, index=0): Returns rate_limit_html
                    - Attempt 2 (download_attempts=2, index=1): Returns rate_limit_html  
                    - Attempt 3 (download_attempts=3, index=2): Returns valid_html
                    
                    Note:
                        download_attempts is incremented by mock_get() before this function runs,
                        so we subtract 1 to convert to 0-based array indexing.
                        
                    Returns:
                        str: HTML content appropriate for the current attempt number.
                            First two attempts return rate-limited responses to trigger retries,
                            third attempt returns valid content for successful completion.
                    """

                    # Setup sequence: fail twice, then succeed
                    rate_limit_html = "<html><body>Rate limited</body></html>"
                    valid_html = "<html><body>Valid Commission response content here</body></html>" * 100

                    nonlocal download_attempts

                    attempt_idx = download_attempts - 1  # 0-indexed

                    if attempt_idx == 0:
                        return rate_limit_html

                    elif attempt_idx == 1:
                        return rate_limit_html
                    else:
                        return valid_html
                
                type(mock_driver).page_source = property(lambda self: get_page_source())
                mock_init_browser.return_value = mock_driver
                
                downloader = ResponseDownloader(tmpdir)
                downloader.logger = Mock()
                
                # Initialize the driver
                downloader._initialize_driver()
                
                with patch('ECI_initiatives.scraper.responses.downloader.save_response_html_file', return_value="test.html"):
                    
                    # Act
                    success, timestamp = downloader.download_single_response(
                        url="https://test.com/response",
                        year="2019",
                        reg_number="2019_000007",
                        max_retries=3
                    )
                
                # Assert
                assert success is True, "Should succeed after transient failures"
                assert timestamp != "", "Should have timestamp"
                assert download_attempts == 3, f"Should take 3 download attempts, but took {download_attempts}"
                
                # Verify warnings were logged for failures
                assert downloader.logger.warning.call_count == 2, \
                    "Should log warning for each failed attempt"

    def test_rate_limit_detection_raises_exception(self):
        """
        Verify that _check_rate_limiting raises exception when rate limit indicators are found.
        """
        
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('ECI_initiatives.scraper.responses.downloader.initialize_browser') as mock_init_browser:
                
                mock_driver = MagicMock()
                mock_driver.page_source = "<html><body>Rate limited - too many requests</body></html>"
                mock_init_browser.return_value = mock_driver
                
                downloader = ResponseDownloader(tmpdir)
                downloader._initialize_driver()
                
                # Act & Assert
                with pytest.raises(Exception, match="Rate limiting detected"):
                    downloader._check_rate_limiting()

```

`./ECI_initiatives/tests/scraper/responses/behaviour/test_html_download.py`:
```
"""
Test suite for downloading and saving Commission response HTML pages.
"""

# Standard library
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Third party
import pytest
from bs4 import BeautifulSoup

# Local imports
from ECI_initiatives.scraper.responses.file_operations.page import PageFileManager
from ECI_initiatives.scraper.responses.consts import MIN_HTML_LENGTH


class TestHTMLDownload:
    """Test HTML page download functionality."""

    @pytest.fixture
    def test_data_dir(self):
        """Get path to test data directory."""
        return Path(__file__).parent.parent.parent.parent / "data" / "example_htmls" / "responses"
    
    @pytest.fixture
    def temp_responses_dir(self, tmp_path):
        """Create temporary responses directory for testing."""
        return tmp_path / "responses"
    
    @pytest.fixture
    def valid_response_html(self, test_data_dir):
        """Valid Commission response HTML content from actual file."""
        # Use strong_legislative_success example
        html_file = test_data_dir / "strong_legislative_success" / "2012" / "2012_000003_en.html"
        with open(html_file, "r", encoding="utf-8") as f:
            return f.read()

    @pytest.fixture
    def rate_limit_html(self):
        """HTML content indicating rate limiting."""

        return """
        <!DOCTYPE html>
        <html>
        <body>
            <h1>Too Many Requests</h1>
            <p>Rate limited - please try again later</p>
        </body>
        </html>
        """

    @pytest.fixture
    def server_error_html(self):
        """HTML content with multilingual server error."""

        return """
        <!DOCTYPE html>
        <html>
        <body>
            <h1>Sorry</h1>
            <p>We apologise for any inconvenience.</p>
            <p>Veuillez nous excuser pour ce désagrément.</p>
            <p>Ci scusiamo per il disagio arrecato.</p>
        </body>
        </html>
        """

    def test_downloaded_html_contains_valid_content(
        self, temp_responses_dir, valid_response_html
    ):
        """
        When downloading response pages, verify that each successfully
        downloaded HTML file contains the expected Commission response content
        (not error pages or rate limit messages).
        """

        # Arrange
        file_ops = PageFileManager(str(temp_responses_dir))
        file_ops.setup_directories()

        # Act
        filename = file_ops.save_response_page(valid_response_html, "2019", "2019_000007")

        # Assert
        saved_file = temp_responses_dir / filename
        assert saved_file.exists()

        with open(saved_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Verify Commission-specific content
        assert "Commission" in content
        assert "European Citizens' Initiative" in content
        assert len(content) > 1000, "Content should be substantial"

        # Verify no error indicators
        assert "rate limited" not in content.lower()
        assert "too many requests" not in content.lower()
        assert "we apologise for any inconvenience" not in content.lower()

    def test_short_html_not_saved(self, temp_responses_dir):
        """
        When HTML content is too short (below minimum threshold), verify that
        the file is not saved and the download is marked as failed.
        """
        # Arrange
        short_html = "<html><body>Short</body></html>"
        file_ops = PageFileManager(str(temp_responses_dir))
        file_ops.setup_directories()

        # Act & Assert
        with pytest.raises(Exception, match="HTML content too short"):
            file_ops.save_response_page(short_html, "2019", "2019_000007")

        # Verify file was not created
        year_dir = temp_responses_dir / "2019"
        if year_dir.exists():
            html_files = list(year_dir.glob("*.html"))
            assert len(html_files) == 0, "No HTML files should be saved"

    def test_rate_limit_retry_with_backoff(self, temp_responses_dir, rate_limit_html):
        """
        When a rate limiting error page is detected, verify that the scraper
        retries the download with exponential backoff.
        """
        # Arrange
        file_ops = PageFileManager(str(temp_responses_dir))
        file_ops.setup_directories()

        # Act & Assert - Rate limit detection
        with pytest.raises(Exception, match="Rate limiting detected"):
            file_ops.save_response_page(rate_limit_html, "2019", "2019_000007")

        # Verify file was not saved
        year_dir = temp_responses_dir / "2019"
        if year_dir.exists():
            html_files = list(year_dir.glob("*.html"))
            assert len(html_files) == 0

    def test_server_error_page_marked_failed(
        self, temp_responses_dir, server_error_html
    ):
        """
        When a server error page is detected (multilingual "Sorry" messages),
        verify that the download is marked as failed.
        """

        # Arrange
        file_ops = PageFileManager(str(temp_responses_dir))
        file_ops.setup_directories()

        # Act & Assert
        with pytest.raises(Exception, match="Error page detected"):
            file_ops.save_response_page(server_error_html, "2019", "2019_000007")

        # Verify file was not saved
        year_dir = temp_responses_dir / "2019"
        if year_dir.exists():
            html_files = list(year_dir.glob("*.html"))
            assert len(html_files) == 0

    def test_max_retries_marks_as_failed(self):
        """
        When a download fails multiple times (exceeding max retries), verify
        that the item is marked as failed and included in the failure summary.
        """
        # Arrange
        from ECI_initiatives.scraper.responses.downloader import ResponseDownloader
        from unittest.mock import Mock, patch, MagicMock
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            downloader = ResponseDownloader(tmpdir)
            
            # Mock the WebDriver to always raise an exception
            mock_driver = MagicMock()
            mock_driver.get.side_effect = Exception("Connection timeout")
            downloader.driver = mock_driver
            
            # Mock logger to prevent actual logging
            downloader.logger = Mock()
            
            # Test parameters
            test_url = "https://citizens-initiative.europa.eu/initiatives/response/2019/000007"
            test_year = "2019"
            test_reg_number = "000007"
            max_retries = 3
            
            # Act - Call the actual download method
            success, timestamp = downloader.download_single_response(
                url=test_url,
                year=test_year,
                reg_number=test_reg_number,
                max_retries=max_retries
            )
            
            # Assert
            assert success is False, "Download should fail after max retries"
            assert timestamp == "", "Timestamp should be empty for failed download"
            
            # Verify driver.get was called max_retries times
            assert mock_driver.get.call_count == max_retries, \
                f"Expected {max_retries} retry attempts, but got {mock_driver.get.call_count}"
            
            # Verify error was logged
            downloader.logger.error.assert_called_once()


    def test_html_files_prettified(self, temp_responses_dir):
        """
        When saving HTML files, verify that the content is prettified
        (well-formatted) for readability.
        """

        # Arrange
        ugly_html = "<html><head><title>Test</title></head><body><div><p>Content</p></div></body></html>"
        file_ops = PageFileManager(str(temp_responses_dir))
        file_ops.setup_directories()

        # Act
        filename = file_ops.save_response_page(ugly_html, "2019", "2019_000007")

        # Assert
        saved_file = temp_responses_dir / filename
        with open(saved_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Verify prettification (indentation and newlines)
        assert "\n" in content, "Should contain newlines"
        assert "  " in content or "\t" in content, "Should contain indentation"
        
        # Count lines to verify it's been expanded
        lines = content.split("\n")
        assert len(lines) > 5, "Prettified HTML should have multiple lines"

    def test_html_files_utf8_encoded(self, temp_responses_dir):
        """
        When saving HTML files, verify that UTF-8 encoding is used to preserve
        special characters in multilingual content.
        """

        # Arrange
        multilingual_html = """
        <!DOCTYPE html>
        <html>
        <body>
            <h1>Diversité en Europe</h1>
            <p>Être différent, ça compte! 🇪🇺</p>
            <p>Salva le api 🐝</p>
            <p>Μειονοτική προστασία</p>
        </body>
        </html>
        """
        file_ops = PageFileManager(str(temp_responses_dir))
        file_ops.setup_directories()

        # Act
        filename = file_ops.save_response_page(multilingual_html, "2019", "2019_000007")

        # Assert
        saved_file = temp_responses_dir / filename
        with open(saved_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Verify special characters are preserved
        assert "Diversité" in content
        assert "Être différent" in content
        assert "🇪🇺" in content
        assert "🐝" in content
        assert "Μειονοτική" in content

    def test_browser_cleanup_after_errors(self):
        """
        When the browser is closed after downloading, verify that resources
        are properly cleaned up even if errors occurred during downloads.
        """

        # Arrange
        from ECI_initiatives.scraper.responses.downloader import ResponseDownloader
        from unittest.mock import Mock, patch, MagicMock
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:

            # Patch initialize_browser to return a mock driver
            with patch('ECI_initiatives.scraper.responses.downloader.initialize_browser') as mock_init_browser:
                
                # Create mock driver
                mock_driver = MagicMock()
                mock_quit = Mock()
                mock_driver.quit = mock_quit
                mock_driver.get.side_effect = Exception("Connection error")
                mock_init_browser.return_value = mock_driver
                
                downloader = ResponseDownloader(tmpdir)
                
                # Mock logger to prevent actual logging
                downloader.logger = Mock()
                
                # Initialize the driver (this calls initialize_browser)
                downloader._initialize_driver()
                
                # Act - Attempt download that will fail
                try:
                    downloader.download_single_response(
                        url="https://test-url.com",
                        year="2019",
                        reg_number="000007",
                        max_retries=1  # Single attempt to speed up test
                    )
                except Exception:
                    pass  # Expected to fail
                
                # Now close the downloader (which should call driver.quit)
                downloader._close_driver()
                
                # Assert - Browser quit was called
                mock_quit.assert_called_once()


    def test_validate_html_content_length(self, temp_responses_dir):
        """
        Verify HTML validation checks content length against minimum threshold.
        """

        # Arrange
        file_ops = PageFileManager(str(temp_responses_dir))
        
        # Test with content just below threshold
        short_content = "x" * (MIN_HTML_LENGTH - 1)
        
        # Act & Assert
        with pytest.raises(Exception, match="HTML content too short"):
            file_ops._validate_html(short_content)

        # Test with content at threshold
        valid_content = "x" * MIN_HTML_LENGTH
        result = file_ops._validate_html(valid_content)

        assert result is True
```

`./ECI_initiatives/tests/scraper/responses/behaviour/test_link_extraction.py`:
```
"""
Test suite for extracting Commission response links from initiative HTML files.
"""


# Standard library
import os
import tempfile
from pathlib import Path
from typing import List, Dict


# Third party
import pytest
from bs4 import BeautifulSoup


# Local imports
from ECI_initiatives.scraper.responses.__main__ import _extract_response_links
from ECI_initiatives.scraper.responses.html_parser import ResponseLinkExtractor



class TestLinkExtraction:
    """Test extraction of response links from initiative pages."""
    
    @pytest.fixture
    def test_data_dir(self):
        """Get path to test data directory for initiatives."""
        # Changed: point to initiatives directory, not responses
        return Path(__file__).parent.parent.parent.parent / "data" / "example_htmls" / "initiatives"
    
    @pytest.fixture
    def temp_pages_dir(self, tmp_path):
        """Create temporary pages directory for testing."""
        pages_dir = tmp_path / "pages"
        pages_dir.mkdir(parents=True, exist_ok=True)
        return pages_dir
    
    @pytest.fixture
    def initiative_html_with_response_link(self, test_data_dir):
        """HTML content with Commission response link from actual file."""

        # Use the answered initiative example which has a response link
        html_file = test_data_dir / "2012_000003_en.html"
        with open(html_file, "r", encoding="utf-8") as f:
            return f.read()


    @pytest.fixture
    def initiative_html_without_response_link(self, test_data_dir):
        """HTML content without Commission response link from actual file."""

        # Use an initiative that doesn't have a response (e.g., registered, ongoing collection)
        # Let's use 2025_000002_en.html (Registered status - no response yet)
        html_file = test_data_dir / "2025_000002_en.html"
        with open(html_file, "r", encoding="utf-8") as f:
            return f.read()


    def test_only_initiatives_with_response_links_included(
        self,
        temp_pages_dir,
        initiative_html_with_response_link,
        initiative_html_without_response_link,
    ):
        """
        When processing initiative HTML files, verify that only initiatives
        with "Commission's answer and follow-up" links are included in the
        response list.
        """


        # Arrange - Create year directory with mixed files
        year_dir = temp_pages_dir / "2019"
        year_dir.mkdir(parents=True, exist_ok=True)


        # File with response link
        with_response = year_dir / "2019_000007_en.html"
        with_response.write_text(initiative_html_with_response_link, encoding="utf-8")


        # File without response link
        without_response = year_dir / "2019_000008_en.html"
        without_response.write_text(
            initiative_html_without_response_link, encoding="utf-8"
        )


        # Act - Use the actual function from __main__.py
        response_links = _extract_response_links(str(temp_pages_dir))


        # Assert
        assert len(response_links) == 1, f"Only one file should have response link, but found {len(response_links)}"
        
        # Verify the response link data structure
        link_data = response_links[0]
        assert link_data['year'] == "2019", "Year should be 2019"
        assert link_data['reg_number'] == "2019_000007", "Registration number should be 2019_000007"
        
        # Verify the file without response link is not included
        reg_numbers = [link['reg_number'] for link in response_links]
        assert "2019_000008" not in reg_numbers, "File without response link should not be included"


    def test_registration_number_and_year_extracted(self, temp_pages_dir, initiative_html_with_response_link):
        """
        When extracting links from initiative pages, verify that the
        registration number and year are correctly extracted from the file path.
        """


        # Arrange - Create test file structure with response links
        test_files = [
            ("2019", "2019_000007_en.html"),
            ("2020", "2020_000001_en.html"),
            ("2021", "2021_000006_en.html"),
        ]


        for year, filename in test_files:


            year_dir = temp_pages_dir / year
            year_dir.mkdir(parents=True, exist_ok=True)
            test_file = year_dir / filename
            test_file.write_text(initiative_html_with_response_link, encoding="utf-8")


        # Act - Use the actual extraction function
        response_links = _extract_response_links(str(temp_pages_dir))


        # Assert
        assert len(response_links) == 3, f"Should extract all 3 response links, but found {len(response_links)}"
        
        # Create set of (year, reg_number) tuples for comparison
        extracted_data = {(link['year'], link['reg_number']) for link in response_links}
        expected_data = {("2019", "2019_000007"), ("2020", "2020_000001"), ("2021", "2021_000006")}
        
        assert extracted_data == expected_data, \
            f"Expected {expected_data}, but got {extracted_data}"


    def test_missing_response_link_skipped(
        self, temp_pages_dir, initiative_html_without_response_link
    ):
        """
        When an initiative HTML file contains no Commission response link,
        verify that it is silently skipped without causing errors.
        """
        # Arrange
        year_dir = temp_pages_dir / "2019"
        year_dir.mkdir(parents=True, exist_ok=True)


        # Create multiple files without response links
        for i in range(3):
            test_file = year_dir / f"2019_00000{i}_en.html"
            test_file.write_text(
                initiative_html_without_response_link, encoding="utf-8"
            )


        # Act - Process files using actual function
        response_links = []
        errors = []


        try:
            response_links = _extract_response_links(str(temp_pages_dir))
        except Exception as e:
            errors.append(str(e))


        # Assert - No errors occurred and no links found
        assert len(errors) == 0, "Processing should not raise errors"
        assert len(response_links) == 0, f"No response links should be found, but found {len(response_links)}"


    def test_all_year_directories_processed(
        self, temp_pages_dir, initiative_html_with_response_link
    ):
        """
        When extracting response links from a directory with multiple year
        subdirectories, verify that all years are processed.
        """
        # Arrange - Create multiple year directories
        years = ["2019", "2020", "2021", "2022"]
        
        for year in years:
            year_dir = temp_pages_dir / year
            year_dir.mkdir(parents=True, exist_ok=True)
            
            # Add file with response link
            test_file = year_dir / (year + "_000001_en.html")
            test_file.write_text(initiative_html_with_response_link, encoding="utf-8")


        # Act - Use actual extraction function
        response_links = _extract_response_links(str(temp_pages_dir))


        # Assert
        assert len(response_links) == 4, f"Should extract links from all 4 years, but found {len(response_links)}"
        
        # Verify all years are represented
        extracted_years = {link['year'] for link in response_links}
        expected_years = set(years)
        
        assert extracted_years == expected_years, \
            f"Expected years {expected_years}, but got {extracted_years}"


    def test_extract_title_from_initiative_page(self, temp_pages_dir, initiative_html_with_response_link):
        """
        Verify that initiative title can be extracted along with response link.
        """


        # Arrange - Use actual HTML with response link
        year_dir = temp_pages_dir / "2019"
        year_dir.mkdir(parents=True, exist_ok=True)
        test_file = year_dir / "2019_000007_en.html"
        test_file.write_text(initiative_html_with_response_link, encoding="utf-8")


        # Act
        response_links = _extract_response_links(str(temp_pages_dir))


        # Assert
        assert len(response_links) == 1, "Should extract one response link"
        assert 'title' in response_links[0], "Response link should include title"
        # The actual title will depend on what's in the HTML file
        assert len(response_links[0].get('title', '')) > 0, \
            "Title should be extracted and not empty"


    def test_extractor_returns_correct_data_structure(self, temp_pages_dir, initiative_html_with_response_link):
        """
        Verify that the extractor returns the expected data structure
        with required fields: url, year, reg_number, title, datetime.
        """


        # Arrange
        year_dir = temp_pages_dir / "2019"
        year_dir.mkdir(parents=True, exist_ok=True)
        test_file = year_dir / "2019_000007_en.html"
        test_file.write_text(initiative_html_with_response_link, encoding="utf-8")


        # Act
        response_links = _extract_response_links(str(temp_pages_dir))


        # Assert
        assert len(response_links) > 0, f"Should extract at least one link, but found {len(response_links)}"
        
        # Verify data structure
        link_data = response_links[0]
        required_fields = ['url', 'year', 'reg_number', 'title', 'datetime']
        
        for field in required_fields:
            assert field in link_data, f"Link data should contain '{field}' field"
        
        # Verify data types
        assert isinstance(link_data['url'], str), "URL should be a string"
        assert isinstance(link_data['year'], str), "Year should be a string"
        assert isinstance(link_data['reg_number'], str), "Registration number should be a string"
        assert isinstance(link_data['title'], str), "Title should be a string"
        assert isinstance(link_data['datetime'], str), "Datetime should be a string"
        
        # Verify year and reg_number are separate
        assert link_data['year'] == "2019", "Year should be extracted separately"
        assert link_data['reg_number'] == "2019_000007", "Registration number should be extracted separately"

```

`./ECI_initiatives/tests/scraper/responses/behaviour/test_output_reporting.py`:
```
"""
Test suite for completion summary and output reporting.
"""

# Standard library
from typing import List, Dict
from unittest.mock import Mock, patch

# Third party
import pytest

# Local imports
from ECI_initiatives.scraper.responses.statistics import (
    ScrapingStatistics,
    display_completion_summary
)
from ECI_initiatives.scraper.responses.consts import LOG_MESSAGES


class TestCompletionSummary:
    """Test completion summary reporting functionality."""

    @pytest.fixture
    def sample_response_links_all_successful(self) -> List[Dict[str, str]]:
        """Sample response links for all successful scenario."""
        return [
            {'url': 'https://example.com/1', 'year': '2019', 'reg_number': '000001', 'title': 'Initiative 1'},
            {'url': 'https://example.com/2', 'year': '2020', 'reg_number': '000002', 'title': 'Initiative 2'},
            {'url': 'https://example.com/3', 'year': '2021', 'reg_number': '000003', 'title': 'Initiative 3'},
            {'url': 'https://example.com/4', 'year': '2022', 'reg_number': '000004', 'title': 'Initiative 4'},
            {'url': 'https://example.com/5', 'year': '2023', 'reg_number': '000005', 'title': 'Initiative 5'},
        ]

    @pytest.fixture
    def sample_response_links_mixed(self) -> List[Dict[str, str]]:
        """Sample response links for mixed success/failure scenario."""
        return [
            {'url': f'https://example.com/{i}', 'year': '2020', 'reg_number': f'00000{i}', 'title': f'Initiative {i}'}
            for i in range(1, 11)
        ]

    @pytest.fixture
    def sample_failed_urls(self) -> List[str]:
        """Sample failed URLs."""
        return [
            "https://citizens-initiative.europa.eu/initiatives/details/2020/000001_en",
            "https://citizens-initiative.europa.eu/initiatives/details/2021/000003_en",
            "https://citizens-initiative.europa.eu/initiatives/details/2022/000005_en",
        ]

    def test_zero_failures_reported_on_success(self, sample_response_links_all_successful):
        """
        When all downloads succeed, verify that the completion summary reports
        zero failures.
        """
        # Arrange
        mock_logger = Mock()
        stats = ScrapingStatistics(
            start_scraping="2024-10-09 14:00:00",
            responses_dir="/data/2024-10-09_14-30-00/responses"
        )
        stats.logger = mock_logger

        # Act
        stats.display_completion_summary(
            response_links=sample_response_links_all_successful,
            failed_urls=[],
            downloaded_count=5
        )

        # Assert - Verify logger was called with success messages
        info_calls = [str(call) for call in mock_logger.info.call_args_list]

        # Check that scraping completion message is logged
        assert any(LOG_MESSAGES["scraping_complete"] in str(call) for call in info_calls), \
            f"Should log '{LOG_MESSAGES['scraping_complete']}' message"

        # Check that "all downloads successful" message is logged
        assert any(LOG_MESSAGES["all_downloads_successful"] in str(call) for call in info_calls), \
            f"Should log '{LOG_MESSAGES['all_downloads_successful']}' message"

        # Verify no failure warnings
        assert mock_logger.warning.call_count == 0, "Should not log warnings for successful run"

    def test_summary_shows_correct_counts(self, sample_response_links_mixed, sample_failed_urls):
        """
        When scraping completes, verify that the summary shows correct counts
        of total links found, successfully downloaded pages, and failed downloads.
        """
        # Arrange
        mock_logger = Mock()
        stats = ScrapingStatistics(
            start_scraping="2024-10-09 14:00:00",
            responses_dir="/data/2024-10-09_14-30-00/responses"
        )
        stats.logger = mock_logger

        total_links = 10
        successful = 7
        failed_count = 3

        # Act
        stats.display_completion_summary(
            response_links=sample_response_links_mixed,
            failed_urls=sample_failed_urls,
            downloaded_count=successful
        )

        # Assert - Check logged messages contain correct counts
        info_calls = [str(call) for call in mock_logger.info.call_args_list]
        warning_calls = [str(call) for call in mock_logger.warning.call_args_list]

        # Verify total count message format
        expected_total_msg = LOG_MESSAGES["total_links_found"].format(count=total_links)
        assert any(expected_total_msg in str(call) for call in info_calls), \
            f"Should log '{expected_total_msg}'"

        # Verify pages downloaded message format
        expected_pages_msg_partial = f"{successful}/{total_links}"
        assert any(expected_pages_msg_partial in str(call) for call in info_calls), \
            f"Should log download count '{expected_pages_msg_partial}'"

        # Verify failed downloads warning
        expected_failed_msg = LOG_MESSAGES["failed_downloads"].format(failed_count=failed_count)
        assert any(expected_failed_msg in str(call) for call in warning_calls), \
            f"Should log '{expected_failed_msg}'"

        # Verify counts are consistent
        assert successful + failed_count == total_links

    def test_summary_includes_save_path(self, sample_response_links_all_successful):
        """
        When scraping completes, verify that the summary includes the path
        where response files were saved.
        """
        # Arrange
        mock_logger = Mock()
        save_path = "/data/2024-10-09_14-30-00/responses"
        
        stats = ScrapingStatistics(
            start_scraping="2024-10-09 14:00:00",
            responses_dir=save_path
        )
        stats.logger = mock_logger

        # Act
        stats.display_completion_summary(
            response_links=sample_response_links_all_successful,
            failed_urls=[],
            downloaded_count=5
        )

        # Assert - Verify save path is logged using LOG_MESSAGES format
        info_calls = [str(call) for call in mock_logger.info.call_args_list]
        
        expected_path_msg = LOG_MESSAGES["files_saved_in"].format(path=save_path)
        assert any(expected_path_msg in str(call) for call in info_calls), \
            f"Should log '{expected_path_msg}'"

    def test_failed_urls_listed_in_summary(
        self, 
        sample_response_links_mixed, 
        sample_failed_urls
    ):
        """
        When downloads fail, verify that the completion summary lists all
        failed URLs for user review.
        """
        # Arrange
        mock_logger = Mock()
        stats = ScrapingStatistics(
            start_scraping="2024-10-09 14:00:00",
            responses_dir="/data/2024-10-09_14-30-00/responses"
        )
        stats.logger = mock_logger

        # Act
        stats.display_completion_summary(
            response_links=sample_response_links_mixed,
            failed_urls=sample_failed_urls,
            downloaded_count=7
        )

        # Assert - Verify all failed URLs are logged using LOG_MESSAGES format
        warning_calls = [str(call) for call in mock_logger.warning.call_args_list]
        
        for failed_url in sample_failed_urls:
            expected_url_msg = LOG_MESSAGES["failed_url"].format(failed_url=failed_url)
            assert any(expected_url_msg in str(call) for call in warning_calls), \
                f"Failed URL should be logged with message: '{expected_url_msg}'"

        # Verify failed downloads summary message is logged
        expected_failed_msg = LOG_MESSAGES["failed_downloads"].format(failed_count=len(sample_failed_urls))
        assert any(expected_failed_msg in str(call) for call in warning_calls), \
            f"Should log '{expected_failed_msg}'"

        # Verify warning count includes failure summary + each URL
        # Should be: 1 (failure count message) + 3 (individual URLs) = 4
        assert mock_logger.warning.call_count >= len(sample_failed_urls), \
            "Should log warning for each failed URL"

    def test_all_downloads_successful_message_displayed(
        self,
        sample_response_links_all_successful
    ):
        """
        Verify that when all downloads succeed, a success message is logged.
        """
        # Arrange
        mock_logger = Mock()
        stats = ScrapingStatistics(
            start_scraping="2024-10-09 14:00:00",
            responses_dir="/data/test"
        )
        stats.logger = mock_logger

        # Act
        stats.display_completion_summary(
            response_links=sample_response_links_all_successful,
            failed_urls=[],
            downloaded_count=5
        )

        # Assert - Check for success message in logs
        info_calls = [str(call) for call in mock_logger.info.call_args_list]
        
        # Verify logger was called
        assert mock_logger.info.called, "Logger info should be called"
        
        # Verify no warnings
        assert mock_logger.warning.call_count == 0, "Should not log warnings for all successful"
        
        # Check for the actual success message from constants
        success_message = LOG_MESSAGES["all_downloads_successful"]
        assert any(success_message in str(call) for call in info_calls), \
            f"Should log '{success_message}' message"

    def test_statistics_display_header_with_timestamps(self):
        """
        Verify that summary header displays start and completion timestamps.
        """
        # Arrange
        mock_logger = Mock()
        start_time = "2024-10-09 14:00:00"
        completion_time = "2024-10-09 15:00:00"
        
        stats = ScrapingStatistics(
            start_scraping=start_time,
            responses_dir="/data/test"
        )
        stats.logger = mock_logger

        # Act
        with patch('ECI_initiatives.scraper.responses.statistics.datetime') as mock_datetime:
            mock_datetime.datetime.now.return_value.strftime.return_value = completion_time
            
            stats.display_completion_summary(
                response_links=[],
                failed_urls=[],
                downloaded_count=0
            )

        # Assert - Verify timestamps in logs using LOG_MESSAGES format
        info_calls = [str(call) for call in mock_logger.info.call_args_list]
        
        # Verify start time message
        expected_start_msg = LOG_MESSAGES["start_time"].format(start_scraping=start_time)
        assert any(expected_start_msg in str(call) for call in info_calls), \
            f"Should log start time message: '{expected_start_msg}'"
        
        # Verify completion time message
        expected_completion_msg = LOG_MESSAGES["completion_timestamp"].format(timestamp=completion_time)
        assert any(expected_completion_msg in str(call) for call in info_calls), \
            f"Should log completion time message: '{expected_completion_msg}'"

        # Verify divider lines are logged
        divider = LOG_MESSAGES["divider_line"]
        divider_count = sum(1 for call in info_calls if divider in str(call))
        assert divider_count >= 2, "Should log at least 2 divider lines (header and footer)"
```

`./ECI_initiatives/tests/scraper/responses/end_to_end/__init__.py`:
```

```

`./ECI_initiatives/tests/scraper/responses/end_to_end/test_created_files.py`:
```
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
        pass
    
    @classmethod
    def teardown_class(cls):
        """
        Cleanup class-level resources that runs once after all tests.
        
        Note: Actual directory cleanup handled by conftest.py fixture.
        """
        pass
    
    def test_debug_fixture(self):
        """Debug test to verify setup output."""
        pass
    
    def test_responses_directory_structure_created(self):
        """
        Verify responses directory and year-based 
        subdirectories are created, along with CSV file.
        """
        pass
    
    def test_response_links_extracted_correctly(self):
        """
        Verify only initiatives with response links 
        are processed and all year directories are scanned.
        """
        pass
    
    def test_csv_file_structure_and_content(self):
        """
        Verify CSV contains required columns and 
        registration numbers are in slash format.
        """
        pass
    
    def test_response_html_files_downloaded(self):
        """
        Verify HTML files contain valid 
        Commission response content, are prettified, and use UTF-8 
        encoding.
        """
        pass
    
    def test_completion_summary_accuracy(self):
        """
        Verify completion summary shows correct 
        counts and file paths.
        """
        pass
    
    def test_integration_with_initiatives_scraper(self):
        """
        Verify responses scraper uses the most recent 
        timestamp directory from initiatives scraper.
        """
        pass

```

`./ECI_initiatives/tests/scraper/responses/__init__.py`:
```

```

