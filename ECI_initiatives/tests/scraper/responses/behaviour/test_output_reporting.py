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
from ECI_initiatives.scraper.responses.consts import (
    LOG_MESSAGES
)


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
        log_calls = [str(call) for call in mock_logger.info.call_args_list]
        log_output = ' '.join(log_calls)

        # Check for success indicators
        assert mock_logger.info.called, "Logger should be called"
        assert any("5" in str(call) for call in log_calls), "Should log total count of 5"
        
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

        # Verify total count
        assert any("10" in str(call) for call in info_calls), "Should log total count of 10"
        
        # Verify successful count
        assert any("7" in str(call) for call in info_calls), "Should log successful count of 7"
        
        # Verify failed count in warnings
        assert any("3" in str(call) for call in warning_calls), "Should log 3 failures"

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

        # Assert - Verify save path is logged
        log_calls = [str(call) for call in mock_logger.info.call_args_list]
        assert any(save_path in str(call) for call in log_calls), \
            f"Should log save path: {save_path}"

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

        # Assert - Verify all failed URLs are logged as warnings
        warning_calls = [str(call) for call in mock_logger.warning.call_args_list]
        
        for failed_url in sample_failed_urls:
            assert any(failed_url in str(call) for call in warning_calls), \
                f"Failed URL should be logged: {failed_url}"

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
        
        # Should contain some indication of all successful
        # (exact message depends on LOG_MESSAGES constants)
        assert mock_logger.info.called
        assert mock_logger.warning.call_count == 0
        assert LOG_MESSAGES["download_success"] in info_calls

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

        # Assert - Verify timestamps in logs
        log_calls = [str(call) for call in mock_logger.info.call_args_list]
        
        # Should log start time
        assert any(start_time in str(call) for call in log_calls), \
            "Should log start timestamp"
        
        # Should log completion time
        assert any("2024-10-09 15:00:00" in str(call) or "15:00:00" in str(call) 
                  for call in log_calls), \
            "Should log completion timestamp"
