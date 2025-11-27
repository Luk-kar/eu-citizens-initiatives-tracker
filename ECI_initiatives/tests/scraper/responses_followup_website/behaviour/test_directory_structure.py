"""
Test suite for directory structure creation and validation.

Tests that followup website HTML files are saved in year-based subdirectories
and that directory structure is created correctly.
"""

# Standard library
from pathlib import Path
from unittest.mock import patch

# Third party
import pytest

# Local imports
from ECI_initiatives.scraper.responses_followup_website.file_operations.page import (
    PageFileManager,
)
from ECI_initiatives.scraper.responses_followup_website.__main__ import (
    _find_latest_timestamp_directory,
    scrape_followup_websites,
)
from ECI_initiatives.scraper.responses_followup_website.errors import (
    MissingDataDirectoryError,
)


class TestDirectoryStructure:
    """Test directory and file structure creation."""

    @pytest.fixture
    def temp_base_dir(self, tmp_path):
        """Create temporary base directory for testing."""

        return tmp_path / "followup_websites"

    @pytest.fixture
    def sample_html_content(self):
        """Provide sample HTML content for testing."""

        return (
            "<html><body><h1>Followup Website Content</h1>"
            + "x" * 1000
            + "</body></html>"
        )

    def test_followup_website_files_in_year_subdirectories(
        self, temp_base_dir, sample_html_content
    ):
        """
        When the scraper runs successfully, verify that followup website HTML
        files are saved in the correct year-based subdirectory structure.
        """

        # Arrange
        file_ops = PageFileManager(str(temp_base_dir))
        file_ops.setup_directories()

        # Act - Save files for different years
        years_and_regs = [
            ("2019", "2019_000007"),
            ("2020", "2020_000001"),
        ]

        for year, reg_number in years_and_regs:
            file_ops.save_followup_website_page(sample_html_content, year, reg_number)

        # Assert - Check year directories exist
        for year, _ in years_and_regs:
            year_dir = temp_base_dir / year
            assert year_dir.exists(), f"Year directory {year} was not created"
            assert year_dir.is_dir(), f"Year path {year} is not a directory"

        # Assert - Check files are in correct year directories
        for year, reg_number in years_and_regs:
            expected_file = temp_base_dir / year / f"{reg_number}_en.html"
            assert (
                expected_file.exists()
            ), f"Followup website file not found: {expected_file}"

        # Assert - Verify no files are in the root directory
        files_in_root = [
            f for f in temp_base_dir.iterdir() if f.is_file() and f.suffix == ".html"
        ]
        assert len(files_in_root) == 0, "HTML files should not be in root directory"

    def test_uses_most_recent_timestamp_directory(self, tmp_path):
        """
        When running the scraper, verify that files are created
        in the most recent timestamp directory from the data folder.
        """

        data_dir = tmp_path / "data"
        data_dir.mkdir(parents=True)

        timestamps = [
            "2024-10-01_10-00-00",
            "2024-10-09_16-45-00",  # Most recent
            "2024-10-05_14-30-00",
        ]

        for timestamp in timestamps:
            (data_dir / timestamp).mkdir()

        # Act - Patch SCRIPT_DIR and call the function
        with patch(
            "ECI_initiatives.scraper.responses_followup_website.__main__.SCRIPT_DIR",
            str(tmp_path),
        ):
            most_recent_path = _find_latest_timestamp_directory()

        # Assert
        most_recent = Path(most_recent_path)
        assert (
            most_recent.name == "2024-10-09_16-45-00"
        ), "Did not select most recent timestamp"
        assert most_recent.parent == data_dir

    def test_followup_website_directory_creation(self, temp_base_dir):
        """
        Verify that the followup_websites directory is created if it doesn't exist.
        """

        # Arrange
        assert not temp_base_dir.exists()
        file_ops = PageFileManager(str(temp_base_dir))

        # Act
        file_ops.setup_directories()

        # Assert
        assert temp_base_dir.exists(), "Followup websites directory was not created"
        assert temp_base_dir.is_dir(), "Path is not a directory"

    def test_missing_data_directory_error(self, tmp_path):
        """
        When the data directory doesn't exist, verify that the scraper raises
        an appropriate error.
        """

        # Arrange

        # Patch SCRIPT_DIR to point to temp directory with no data
        with patch(
            "ECI_initiatives.scraper.responses_followup_website.__main__.SCRIPT_DIR",
            str(tmp_path),
        ):

            # Ensure no data directory exists
            data_dir = tmp_path / "data"
            if data_dir.exists():
                raise RuntimeError(f"Test setup failed: {data_dir} should not exist")

            # Act & Assert
            with pytest.raises(MissingDataDirectoryError) as exc_info:
                scrape_followup_websites()

            error = exc_info.value
            assert error.expected_path is not None
            assert "data" in error.expected_path.lower()
