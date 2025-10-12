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