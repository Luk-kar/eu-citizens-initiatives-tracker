"""
Test suite for CSV reading and followup website URL extraction.

Tests extraction of followup website URLs from eci_responses CSV file,
including URL validation, registration number parsing, and year extraction.
"""

# Standard library
import csv

# Third party
import pytest

# Local imports
from ECI_initiatives.scraper.responses_followup_website.file_operations.csv_reader import (
    find_latest_csv_file,
    extract_followup_website_urls,
)
from ECI_initiatives.scraper.responses_followup_website.errors import (
    MissingCSVFileError,
)


class TestCSVReader:
    """Test CSV file reading and URL extraction."""

    @pytest.fixture
    def temp_data_dir(self, tmp_path):
        """Create temporary data directory for testing."""
        return tmp_path / "data"

    @pytest.fixture
    def sample_responses_csv(self, temp_data_dir):
        """Create sample eci_responses CSV file."""
        temp_data_dir.mkdir(parents=True)
        csv_path = temp_data_dir / "eci_responses_2024-10-09_14-30-00.csv"

        data = [
            {
                "registration_number": "2019/009001",
                "title": "Some Non-Existing ECI",
                "followup_dedicated_website": "https://food.ec.europa.eu/animals/animal-welfare/eci/eci-some-non-existing-eci_en",
                "other_field": "some_value",
            },
            {
                "registration_number": "2020/000001",
                "title": "Save Bees and Farmers",
                "followup_dedicated_website": "",  # Empty - should be skipped
                "other_field": "some_value",
            },
            {
                "registration_number": "2021/000006",
                "title": "End the Cage Age",
                "followup_dedicated_website": "https://food.ec.europa.eu/animals/animal-welfare/eci/eci-end-cage-age_en",
                "other_field": "some_value",
            },
            {
                "registration_number": "2022/000002",
                "title": "Fur Free Europe",
                "followup_dedicated_website": "https://food.ec.europa.eu/animals/animal-welfare/eci/eci-fur-free-europe_en",
                "other_field": "some_value",
            },
        ]

        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)

        return csv_path

    def test_extract_followup_urls_from_csv(self, sample_responses_csv):
        """
        When reading the CSV file, verify that followup website URLs
        are extracted correctly with registration numbers and years.
        """
        # Act
        followup_urls = extract_followup_website_urls(str(sample_responses_csv))

        # Assert
        assert len(followup_urls) == 3, "Should extract 3 URLs (excluding empty one)"

        # Verify structure of extracted data
        required_fields = ["url", "registration_number", "year"]
        for url_data in followup_urls:
            for field in required_fields:
                assert field in url_data, f"Missing required field: {field}"

        # Verify specific URLs were extracted
        urls = [item["url"] for item in followup_urls]
        assert (
            "https://food.ec.europa.eu/animals/animal-welfare/eci/eci-some-non-existing-eci_en"
            in urls
        )
        assert (
            "https://food.ec.europa.eu/animals/animal-welfare/eci/eci-end-cage-age_en"
            in urls
        )
        assert (
            "https://food.ec.europa.eu/animals/animal-welfare/eci/eci-fur-free-europe_en"
            in urls
        )

    def test_registration_numbers_converted_to_underscore_format(
        self, sample_responses_csv
    ):
        """
        When extracting followup URLs, verify that registration numbers
        are converted from slash format (2019/000007) to underscore format
        (2019_000007) for filename compatibility.
        """
        # Act
        followup_urls = extract_followup_website_urls(str(sample_responses_csv))

        # Assert
        for url_data in followup_urls:
            reg_number = url_data["registration_number"]
            assert (
                "_" in reg_number
            ), f"Registration number should use underscore format: {reg_number}"
            assert (
                "/" not in reg_number
            ), f"Registration number should not contain slash: {reg_number}"

        # Verify specific conversions
        reg_numbers = [item["registration_number"] for item in followup_urls]
        assert "2019_009001" in reg_numbers
        assert "2021_000006" in reg_numbers
        assert "2022_000002" in reg_numbers

    def test_year_extracted_from_registration_number(self, sample_responses_csv):
        """
        When extracting followup URLs, verify that the year is correctly
        parsed from the registration number.
        """
        # Act
        followup_urls = extract_followup_website_urls(str(sample_responses_csv))

        # Assert
        for url_data in followup_urls:
            year = url_data["year"]
            assert year.isdigit(), f"Year should be numeric: {year}"
            assert len(year) == 4, f"Year should be 4 digits: {year}"

            # Year should match first part of registration number
            reg_number = url_data["registration_number"]
            assert reg_number.startswith(
                year
            ), f"Year {year} doesn't match reg number {reg_number}"

    def test_empty_followup_urls_skipped(self, sample_responses_csv):
        """
        When reading the CSV, verify that rows with empty followup_dedicated_website
        fields are skipped (not included in results).
        """
        # Act
        followup_urls = extract_followup_website_urls(str(sample_responses_csv))

        # Assert - "Save Bees and Farmers" (2020/000001) should be excluded
        reg_numbers = [item["registration_number"] for item in followup_urls]
        assert "2020/000001" not in reg_numbers, "Empty followup URL should be skipped"

        # Verify we got 3 URLs instead of 4
        assert len(followup_urls) == 3

    def test_find_latest_csv_file(self, temp_data_dir):
        """
        When multiple CSV files exist, verify that the most recent one
        (based on timestamp in filename) is selected.
        """
        # Arrange - Create multiple CSV files with different timestamps
        temp_data_dir.mkdir(parents=True)

        csv_files = [
            "eci_responses_2024-10-01_10-00-00.csv",
            "eci_responses_2024-10-09_14-30-00.csv",  # Most recent
            "eci_responses_2024-10-05_12-00-00.csv",
        ]

        for csv_file in csv_files:
            (temp_data_dir / csv_file).touch()

        # Act
        latest_csv = find_latest_csv_file(str(temp_data_dir))

        # Assert
        assert "2024-10-09_14-30-00" in latest_csv, "Should select most recent CSV"

    def test_missing_csv_file_raises_error(self, temp_data_dir):
        """
        When no CSV file exists in the data directory, verify that
        MissingCSVFileError is raised with appropriate message.
        """
        # Arrange
        temp_data_dir.mkdir(parents=True)

        # Act & Assert
        with pytest.raises(MissingCSVFileError) as exc_info:
            find_latest_csv_file(str(temp_data_dir))

        error = exc_info.value
        assert error.search_dir == str(temp_data_dir)
        assert "Cannot find eci_responses CSV file" in str(error)
