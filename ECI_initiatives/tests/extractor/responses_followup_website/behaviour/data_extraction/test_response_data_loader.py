"""
Unit tests for ECIResponseDataLoader class.

This module tests:
- Loading CSV data into memory
- Retrieving initiative titles and website URLs
- Error handling for missing or malformed data
"""

# Standard library
import csv

# Third party
import pytest

# Local
from ECI_initiatives.extractor.responses_followup_website.processor import (
    ECIResponseDataLoader,
)


class TestECIResponseDataLoader:
    """Tests for ECIResponseDataLoader functionality."""

    @pytest.fixture
    def sample_csv_file(self, tmp_path):
        """Create a temporary CSV file with sample ECI response data."""
        csv_file = tmp_path / "test_responses.csv"

        headers = [
            "registration_number",
            "initiative_title",
            "followup_dedicated_website",
        ]
        rows = [
            {
                "registration_number": "2018/000004",
                "initiative_title": "Fair Transport Europe",
                "followup_dedicated_website": "https://example.com/fair-transport",
            },
            {
                "registration_number": "2022/000002",
                "initiative_title": "Save Bees and Farmers",
                "followup_dedicated_website": "https://example.com/save-bees",
            },
            {
                "registration_number": "2019/000001",
                "initiative_title": "Minority SafePack",
                "followup_dedicated_website": "",
            },
        ]

        with open(csv_file, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(rows)

        return str(csv_file)

    @pytest.fixture
    def empty_csv_file(self, tmp_path):
        """Create a temporary empty CSV file with headers only."""
        csv_file = tmp_path / "empty_responses.csv"

        headers = [
            "registration_number",
            "initiative_title",
            "followup_dedicated_website",
        ]

        with open(csv_file, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()

        return str(csv_file)

    @pytest.fixture
    def malformed_csv_file(self, tmp_path):
        """Create a CSV file with missing required columns."""
        csv_file = tmp_path / "malformed_responses.csv"

        headers = [
            "registration_number",
            "initiative_title",
        ]  # Missing followup_dedicated_website
        rows = [
            {
                "registration_number": "2018/000004",
                "initiative_title": "Fair Transport Europe",
            }
        ]

        with open(csv_file, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(rows)

        return str(csv_file)

    def test_load_valid_csv(self, sample_csv_file):
        """Test loading a valid CSV file populates records dictionary."""
        loader = ECIResponseDataLoader(sample_csv_file)

        assert len(loader.records) == 3
        assert "2018/000004" in loader.records
        assert "2022/000002" in loader.records
        assert "2019/000001" in loader.records

    def test_get_title_existing_record(self, sample_csv_file):
        """Test retrieving initiative title for existing registration number."""
        loader = ECIResponseDataLoader(sample_csv_file)

        title = loader.get_title("2018/000004")
        assert title == "Fair Transport Europe"

        title = loader.get_title("2022/000002")
        assert title == "Save Bees and Farmers"

    def test_get_website_url_existing_record(self, sample_csv_file):
        """Test retrieving website URL for existing registration number."""
        loader = ECIResponseDataLoader(sample_csv_file)

        url = loader.get_website_url("2018/000004")
        assert url == "https://example.com/fair-transport"

        url = loader.get_website_url("2022/000002")
        assert url == "https://example.com/save-bees"

    def test_get_website_url_empty_value(self, sample_csv_file):
        """Test retrieving empty website URL returns empty string."""
        loader = ECIResponseDataLoader(sample_csv_file)

        url = loader.get_website_url("2019/000001")
        assert url == ""

    def test_get_title_missing_registration_number(self, sample_csv_file):
        """Test KeyError raised when registration number not found."""
        loader = ECIResponseDataLoader(sample_csv_file)

        with pytest.raises(KeyError):
            loader.get_title("9999/999999")

    def test_get_website_url_missing_registration_number(self, sample_csv_file):
        """Test KeyError raised when registration number not found."""
        loader = ECIResponseDataLoader(sample_csv_file)

        with pytest.raises(KeyError):
            loader.get_website_url("9999/999999")

    def test_load_empty_csv(self, empty_csv_file):
        """Test loading empty CSV file creates empty records dictionary."""
        loader = ECIResponseDataLoader(empty_csv_file)

        assert len(loader.records) == 0
        assert loader.records == {}

    def test_load_malformed_csv_missing_column(self, malformed_csv_file):
        """Test KeyError raised when CSV missing required column."""
        with pytest.raises(KeyError, match="followup_dedicated_website"):
            ECIResponseDataLoader(malformed_csv_file)

    def test_load_nonexistent_file(self):
        """Test FileNotFoundError raised when CSV file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            ECIResponseDataLoader("/nonexistent/path/to/file.csv")

    def test_records_structure(self, sample_csv_file):
        """Test loaded records have correct nested dictionary structure."""
        loader = ECIResponseDataLoader(sample_csv_file)

        record = loader.records["2018/000004"]
        assert isinstance(record, dict)
        assert "initiative_title" in record
        assert "followup_dedicated_website" in record
        assert len(record) == 2
