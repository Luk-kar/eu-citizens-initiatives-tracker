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
from ECI_initiatives.data_pipeline.scraper.responses.file_operations.csv import (
    write_responses_csv,
)
from ECI_initiatives.data_pipeline.scraper.responses.consts import CSV_FIELDNAMES


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
            assert (
                "/" in reg_number
            ), f"Registration number should use slash format: {reg_number}"
            assert (
                "_" not in reg_number
            ), f"Registration number should not contain underscores: {reg_number}"

        # Verify specific normalized values
        expected_reg_numbers = ["2019/000007", "2020/000001", "2021/000006"]
        actual_reg_numbers = [row["registration_number"] for row in rows]
        assert (
            actual_reg_numbers == expected_reg_numbers
        ), "Registration numbers not properly normalized"

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
        assert (
            len(successful_rows) == 2
        ), "Expected 2 successful downloads with timestamps"

        # Verify timestamp format (YYYY-MM-DD HH:MM:SS)
        for row in successful_rows:
            timestamp = row["datetime"]
            assert (
                len(timestamp) > 0
            ), "Timestamp should not be empty for successful downloads"
            assert (
                "-" in timestamp and ":" in timestamp
            ), f"Invalid timestamp format: {timestamp}"

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
        assert (
            len(failed_rows) == 2
        ), "Expected 2 failed downloads with empty timestamps"

        # Verify failed rows still have other data
        for row in failed_rows:
            assert row["url_find_initiative"], "Failed row should have URL"
            assert row[
                "registration_number"
            ], "Failed row should have registration number"
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
        assert (
            headers == required_columns
        ), f"CSV headers don't match required columns. Expected: {required_columns}, Got: {headers}"

        # Verify column order matches expected order
        expected_order = [
            "url_find_initiative",
            "registration_number",
            "title",
            "datetime",
        ]
        assert (
            list(headers) == expected_order
        ), f"CSV column order incorrect. Expected: {expected_order}, Got: {list(headers)}"

        # Verify no extra columns
        assert len(headers) == len(
            expected_order
        ), f"CSV should have exactly {len(expected_order)} columns, got {len(headers)}"

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

        assert (
            headers == CSV_FIELDNAMES
        ), "Headers should be present even with empty data"
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
            },
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
