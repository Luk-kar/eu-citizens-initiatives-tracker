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

# Local imports (handled by conftest fixture)
from ECI_initiatives.tests.consts import (
    COMMON_STATUSES,
    REQUIRED_CSV_COLUMNS,
    CSV_FILENAME,
    PAGES_DIR_NAME,
    LOG_MESSAGES,
)


class TestCompletionSummaryAccuracy:
    """Test completion summary and statistics accuracy."""

    @classmethod
    def setup_class(cls):
        """
        Import modules and set up class attributes.
        
        Imports are done here rather than at module level to avoid
        log file creation during module loading, allowing the session
        fixture to properly track and clean up test artifacts.
        """
        from ECI_initiatives.scraper.initiatives.statistics import (
            display_completion_summary,
            gather_scraping_statistics,
            display_summary_info,
            display_results_and_files,
        )
        
        cls.display_completion_summary = staticmethod(display_completion_summary)
        cls.gather_scraping_statistics = staticmethod(gather_scraping_statistics)
        cls.display_summary_info = staticmethod(display_summary_info)
        cls.display_results_and_files = staticmethod(display_results_and_files)

    @patch("ECI_initiatives.scraper.initiatives.statistics.logger")
    @patch("ECI_initiatives.scraper.initiatives.statistics.gather_scraping_statistics")
    @patch("ECI_initiatives.scraper.initiatives.statistics.display_summary_info")
    @patch("ECI_initiatives.scraper.initiatives.statistics.display_results_and_files")
    def test_final_statistics_match_actual_results(
        self, mock_display_results, mock_display_summary, mock_gather_stats, mock_logger
    ):
        """Verify that final statistics match actual results (total initiatives, downloads, failures)."""

        # Arrange
        start_scraping = "2025-09-21_17-13-00"
        initiative_data = [
            {
                REQUIRED_CSV_COLUMNS.URL: "https://example.com/1",
                REQUIRED_CSV_COLUMNS.CURRENT_STATUS: "Registered",
            },
            {
                REQUIRED_CSV_COLUMNS.URL: "https://example.com/2",
                REQUIRED_CSV_COLUMNS.CURRENT_STATUS: "Collection ongoing",
            },
            {
                REQUIRED_CSV_COLUMNS.URL: "https://example.com/3",
                REQUIRED_CSV_COLUMNS.CURRENT_STATUS: "Valid initiative",
            },
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
        self.display_completion_summary(
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

    @patch("ECI_initiatives.scraper.initiatives.statistics.logger")
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

        test_csv_data = []
        expected_counts = {}

        for status in COMMON_STATUSES:
            test_csv_data.append({REQUIRED_CSV_COLUMNS.CURRENT_STATUS: status})
            expected_counts[status] = 1

        # Add extra "Answered initiative" to test multiple counts
        test_csv_data.append(
            {"current_status": COMMON_STATUSES[0]}
        )  # "Answered initiative"
        expected_counts[COMMON_STATUSES[0]] = 2

        # Mock CSV reading using the example data from user's CSV file
        with patch("csv.DictReader") as mock_csv_reader:
            mock_csv_reader.return_value = test_csv_data
            # Act
            stats = self.gather_scraping_statistics(start_scraping, [], [])

            # Assert
            expected_counter = Counter(expected_counts)

            assert stats["status_counter"] == expected_counter

    @patch("ECI_initiatives.scraper.initiatives.statistics.logger")
    @patch("datetime.datetime")
    @patch("ECI_initiatives.scraper.initiatives.statistics.gather_scraping_statistics")
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
        self.display_summary_info(start_scraping, saved_page_paths, stats)

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

    @patch("ECI_initiatives.scraper.initiatives.statistics.logger")
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
        self.display_results_and_files(start_scraping, saved_page_paths, failed_urls, stats)

        # Assert
        # Verify that the saved paths are reported correctly
        mock_logger.info.assert_any_call(
            f"Files saved in: initiatives/{start_scraping}"
        )
        mock_logger.info.assert_any_call(
            LOG_MESSAGES["summary_scraping"]["main_page_sources"]
        )

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
            {REQUIRED_CSV_COLUMNS.URL: "https://example.com/1"},
            {REQUIRED_CSV_COLUMNS.URL: "https://example.com/2"},
            {REQUIRED_CSV_COLUMNS.URL: "https://example.com/3"},
        ]
        failed_urls = ["https://example.com/failed1", "https://example.com/failed2"]

        # Mock file system for CSV reading and directory counting
        def side_effect(path):

            if path.endswith(CSV_FILENAME):
                return True

            elif path.endswith(PAGES_DIR_NAME):
                return True

            return False

        mock_exists.side_effect = side_effect

        # Mock CSV reading
        with patch("csv.DictReader") as mock_csv_reader:
            mock_csv_reader.return_value = [
                {REQUIRED_CSV_COLUMNS.CURRENT_STATUS: "Registered"},
                {REQUIRED_CSV_COLUMNS.CURRENT_STATUS: "Collection ongoing"},
                {REQUIRED_CSV_COLUMNS.CURRENT_STATUS: "Valid initiative"},
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
            result = self.gather_scraping_statistics(
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

    @patch("ECI_initiatives.scraper.initiatives.statistics.logger")
    def test_display_results_with_failed_downloads(self, mock_logger):
        """Test display_results_and_files function with failed downloads."""

        # Arrange
        start_scraping = "2025-09-21_17-13-00"
        saved_page_paths = ["page1.html", "page2.html"]
        failed_urls = ["https://example.com/failed1", "https://example.com/failed2"]
        stats = {"downloaded_count": 2, "total_initiatives": 4, "failed_count": 2}

        # Act
        self.display_results_and_files(start_scraping, saved_page_paths, failed_urls, stats)

        # Assert
        mock_logger.info.assert_any_call(
            LOG_MESSAGES["summary_scraping"]["pages_downloaded"].format(
                downloaded_count=2, total_initiatives=4
            )
        )
        mock_logger.error.assert_any_call(
            LOG_MESSAGES["summary_scraping"]["failed_downloads"].format(failed_count=2)
        )
        mock_logger.error.assert_any_call(" - https://example.com/failed1")
        mock_logger.error.assert_any_call(" - https://example.com/failed2")

    @patch("ECI_initiatives.scraper.initiatives.statistics.logger")
    def test_display_results_no_failures(self, mock_logger):
        """Test display_results_and_files function with no failed downloads."""

        # Arrange
        start_scraping = "2025-09-21_17-13-00"
        saved_page_paths = ["page1.html", "page2.html"]
        failed_urls = []
        stats = {"downloaded_count": 2, "total_initiatives": 2, "failed_count": 0}

        # Act
        self.display_results_and_files(start_scraping, saved_page_paths, failed_urls, stats)

        # Assert
        mock_logger.info.assert_any_call(
            LOG_MESSAGES["summary_scraping"]["pages_downloaded"].format(
                downloaded_count=2, total_initiatives=2
            )
        )
        mock_logger.info.assert_any_call(
            LOG_MESSAGES["summary_scraping"]["all_downloads_successful"]
        )
        # Should not call error methods
        assert not mock_logger.error.called

    @patch("ECI_initiatives.scraper.initiatives.statistics.logger")
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
            self.display_summary_info(start_scraping, saved_page_paths, stats)

            # Assert
            mock_logger.info.assert_any_call(
                LOG_MESSAGES["summary_scraping"]["scraping_complete"]
            )
            mock_logger.info.assert_any_call(
                f"Total pages scraped: {len(saved_page_paths)}"
            )
            mock_logger.info.assert_any_call(
                f"Total initiatives found: {stats['total_initiatives']}"
            )
            mock_logger.info.assert_any_call(
                "Initiatives by category (current_status):"
            )

            mock_logger.info.assert_any_call(
                LOG_MESSAGES["summary_scraping"]["registered_status"].format(count=2)
            )
            mock_logger.info.assert_any_call(
                LOG_MESSAGES["summary_scraping"]["collection_ongoing_status"].format(
                    count=1
                )
            )
            mock_logger.info.assert_any_call(
                LOG_MESSAGES["summary_scraping"]["valid_initiative_status"].format(
                    count=1
                )
            )
