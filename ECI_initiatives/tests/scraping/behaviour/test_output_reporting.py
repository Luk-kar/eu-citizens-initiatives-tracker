"""Tests for output and reporting functionality."""

# Standard library
import csv
import datetime
import os
import sys
from collections import Counter
from unittest.mock import Mock, patch, mock_open, MagicMock

# Third party
import pytest

# Local
program_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")

sys.path.append(program_dir)

from ECI_initiatives.__main__ import (
    display_completion_summary,
    gather_scraping_statistics,
    display_summary_info,
    display_results_and_files,
)


class TestCompletionSummaryAccuracy:
    """Test completion summary and statistics accuracy."""

    @patch("ECI_initiatives.__main__.logger")
    @patch("ECI_initiatives.__main__.gather_scraping_statistics")
    @patch("ECI_initiatives.__main__.display_summary_info")
    @patch("ECI_initiatives.__main__.display_results_and_files")
    def test_final_statistics_match_actual_results(
        self, mock_display_results, mock_display_summary, mock_gather_stats, mock_logger
    ):
        """Verify that final statistics match actual results (total initiatives, downloads, failures)."""

        # Arrange
        start_scraping = "2025-09-21_17-13-00"
        initiative_data = [
            {"url": "https://example.com/1", "current_status": "Registered"},
            {"url": "https://example.com/2", "current_status": "Collection ongoing"},
            {"url": "https://example.com/3", "current_status": "Valid initiative"},
        ]
        saved_page_paths = ["page1.html", "page2.html", "page3.html"]
        failed_urls = ["https://example.com/failed"]

        expected_stats = {
            "status_counter": Counter(
                {"Registered": 1, "Collection ongoing": 1, "Valid initiative": 1}
            ),
            "downloaded_count": 3,
            "total_initiatives": 3,
            "failed_count": 1,
        }

        mock_gather_stats.return_value = expected_stats

        # Act
        display_completion_summary(
            start_scraping, initiative_data, saved_page_paths, failed_urls
        )

        # Assert
        mock_gather_stats.assert_called_once_with(
            start_scraping, initiative_data, failed_urls
        )
        mock_display_summary.assert_called_once_with(
            start_scraping, saved_page_paths, expected_stats
        )
        mock_display_results.assert_called_once_with(
            start_scraping, saved_page_paths, failed_urls, expected_stats
        )

    @patch("ECI_initiatives.__main__.logger")
    @patch("os.path.exists")
    @patch("os.path.isdir")
    @patch("os.listdir")
    @patch("builtins.open", new_callable=mock_open)
    def test_status_distribution_counts_accurate(
        self,
        mock_file,
        mock_listdir,
        mock_isdir,
        mock_exists,
        mock_logger,
    ):
        """Check that status distribution counts are accurate."""

        # Arrange
        start_scraping = "2025-09-21_17-13-00"
        mock_exists.return_value = True

        # Mock CSV reading using the example data from user's CSV file
        with patch("csv.DictReader") as mock_csv_reader:
            mock_csv_reader.return_value = [
                {"current_status": "Answered initiative"},
                {"current_status": "Unsuccessful collection"},
                {"current_status": "Withdrawn"},
                {"current_status": "Registered"},
                {"current_status": "Collection ongoing"},
                {"current_status": "Verification"},
                {"current_status": "Valid initiative"},
                {"current_status": "Answered initiative"},  # Second occurrence
            ]

            # Act
            stats = gather_scraping_statistics(start_scraping, [], [])

            # Assert
            expected_counter = Counter(
                {
                    "Answered initiative": 2,
                    "Unsuccessful collection": 1,
                    "Withdrawn": 1,
                    "Registered": 1,
                    "Collection ongoing": 1,
                    "Verification": 1,
                    "Valid initiative": 1,
                }
            )

            assert stats["status_counter"] == expected_counter

    @patch("ECI_initiatives.__main__.logger")
    @patch("datetime.datetime")
    @patch("ECI_initiatives.__main__.gather_scraping_statistics")
    def test_completion_timestamps_accurate(
        self, mock_gather_stats, mock_datetime, mock_logger
    ):
        """Ensure completion timestamps and duration reporting are correct."""

        # Arrange
        mock_now = Mock()
        mock_now.strftime.return_value = "2025-09-21 17:13:45"
        mock_datetime.now.return_value = mock_now

        start_scraping = "2025-09-21_17-13-00"
        saved_page_paths = ["page1.html", "page2.html"]
        stats = {"status_counter": Counter({"Registered": 2}), "total_initiatives": 2}

        # Act
        display_summary_info(start_scraping, saved_page_paths, stats)

        # Assert
        mock_datetime.now.assert_called_once()
        mock_now.strftime.assert_called_with("%Y-%m-%d %H:%M:%S")

        # Verify the logger was called with the correct timestamp
        assert any(
            "Scraping completed at: 2025-09-21 17:13:45" in str(call)
            for call in mock_logger.info.call_args_list
        )
        assert any(
            f"Start time: {start_scraping}" in str(call)
            for call in mock_logger.info.call_args_list
        )

    @patch("ECI_initiatives.__main__.logger")
    def test_file_path_reporting_matches_saved_locations(self, mock_logger):
        """Validate that file path reporting matches actual saved locations."""

        # Arrange
        start_scraping = "2025-09-21_17-13-00"
        saved_page_paths = [
            "initiatives/2025-09-21_17-13-00/list/page_1.html",
            "initiatives/2025-09-21_17-13-00/list/page_2.html",
            "initiatives/2025-09-21_17-13-00/list/page_3.html",
        ]
        failed_urls = []
        stats = {"downloaded_count": 3, "total_initiatives": 3, "failed_count": 0}

        # Act
        display_results_and_files(start_scraping, saved_page_paths, failed_urls, stats)

        # Assert
        # Verify that the saved paths are reported correctly
        mock_logger.info.assert_any_call(
            f"Files saved in: initiatives/{start_scraping}"
        )
        mock_logger.info.assert_any_call("Main page sources:")

        # Check that each path is logged with correct numbering
        for i, path in enumerate(saved_page_paths, 1):
            mock_logger.info.assert_any_call(f"  Page {i}: {path}")

    @patch("os.path.exists")
    @patch("os.path.isdir")
    @patch("os.listdir")
    @patch("builtins.open", new_callable=mock_open)
    def test_gather_scraping_statistics_function(
        self, mock_file, mock_listdir, mock_isdir, mock_exists
    ):
        """Test the gather_scraping_statistics function."""

        # Arrange
        start_scraping = "2025-09-21_17-13-00"
        initiative_data = [
            {"url": "https://example.com/1"},
            {"url": "https://example.com/2"},
            {"url": "https://example.com/3"},
        ]
        failed_urls = ["https://example.com/failed1", "https://example.com/failed2"]

        # Mock file system for CSV reading and directory counting
        def side_effect(path):

            if path.endswith("initiatives_list.csv"):
                return True

            elif path.endswith("initiative_pages"):
                return True

            return False

        mock_exists.side_effect = side_effect

        # Mock CSV reading
        with patch("csv.DictReader") as mock_csv_reader:
            mock_csv_reader.return_value = [
                {"current_status": "Registered"},
                {"current_status": "Collection ongoing"},
                {"current_status": "Valid initiative"},
            ]

            # Mock directory structure for counting files
            mock_listdir.side_effect = [
                ["2019", "2020", "2021"],  # Year directories
                ["initiative1.html", "initiative2.html"],  # 2019 files
                ["initiative3.html"],  # 2020 files
                [],  # 2021 files (empty)
            ]
            mock_isdir.return_value = True

            # Act
            result = gather_scraping_statistics(
                start_scraping, initiative_data, failed_urls
            )

            # Assert
            expected_result = {
                "status_counter": Counter(
                    {"Registered": 1, "Collection ongoing": 1, "Valid initiative": 1}
                ),
                "downloaded_count": 3,  # Files per year: 2019(2) + 2020(1) + 2021(0) = 3 total
                "total_initiatives": 3,
                "failed_count": 2,
            }

            assert result["status_counter"] == expected_result["status_counter"]
            assert result["downloaded_count"] == expected_result["downloaded_count"]
            assert result["total_initiatives"] == expected_result["total_initiatives"]
            assert result["failed_count"] == expected_result["failed_count"]

    @patch("ECI_initiatives.__main__.logger")
    def test_display_results_with_failed_downloads(self, mock_logger):
        """Test display_results_and_files function with failed downloads."""

        # Arrange
        start_scraping = "2025-09-21_17-13-00"
        saved_page_paths = ["page1.html", "page2.html"]
        failed_urls = ["https://example.com/failed1", "https://example.com/failed2"]
        stats = {"downloaded_count": 2, "total_initiatives": 4, "failed_count": 2}

        # Act
        display_results_and_files(start_scraping, saved_page_paths, failed_urls, stats)

        # Assert
        mock_logger.info.assert_any_call("Pages downloaded: 2/4")
        mock_logger.error.assert_any_call("Failed downloads: 2")
        mock_logger.error.assert_any_call(" - https://example.com/failed1")
        mock_logger.error.assert_any_call(" - https://example.com/failed2")

    @patch("ECI_initiatives.__main__.logger")
    def test_display_results_no_failures(self, mock_logger):
        """Test display_results_and_files function with no failed downloads."""

        # Arrange
        start_scraping = "2025-09-21_17-13-00"
        saved_page_paths = ["page1.html", "page2.html"]
        failed_urls = []
        stats = {"downloaded_count": 2, "total_initiatives": 2, "failed_count": 0}

        # Act
        display_results_and_files(start_scraping, saved_page_paths, failed_urls, stats)

        # Assert
        mock_logger.info.assert_any_call("Pages downloaded: 2/2")
        mock_logger.info.assert_any_call("✅ All downloads successful!")
        # Should not call error methods
        assert not mock_logger.error.called

    @patch("ECI_initiatives.__main__.logger")
    def test_display_summary_info_content(self, mock_logger):
        """Test that display_summary_info outputs correct summary content."""

        # Arrange
        start_scraping = "2025-09-21_17-13-00"
        saved_page_paths = ["page1.html", "page2.html", "page3.html"]
        stats = {
            "status_counter": Counter(
                {"Registered": 2, "Collection ongoing": 1, "Valid initiative": 1}
            ),
            "total_initiatives": 4,
        }

        with patch("datetime.datetime") as mock_datetime:

            mock_now = Mock()
            mock_now.strftime.return_value = "2025-09-21 17:15:00"
            mock_datetime.now.return_value = mock_now

            # Act
            display_summary_info(start_scraping, saved_page_paths, stats)

            # Assert
            mock_logger.info.assert_any_call("🎉 SCRAPING FINISHED! 🎉")
            mock_logger.info.assert_any_call(
                f"Total pages scraped: {len(saved_page_paths)}"
            )
            mock_logger.info.assert_any_call(
                f"Total initiatives found: {stats['total_initiatives']}"
            )
            mock_logger.info.assert_any_call(
                "Initiatives by category (current_status):"
            )
            mock_logger.info.assert_any_call("- Registered: 2")
            mock_logger.info.assert_any_call("- Collection ongoing: 1")
            mock_logger.info.assert_any_call("- Valid initiative: 1")
