"""
Test suite for error handling and retry mechanisms.

Tests retry logic for failed downloads, rate limiting detection,
and proper error logging.
"""

# Standard library
import tempfile
from unittest.mock import Mock, patch, MagicMock

# Third party
import pytest

# Local imports
from ECI_initiatives.scraper.responses_followup_website.downloader import (
    FollowupWebsiteDownloader,
)

# pylint: disable=protected-access
# Rationale: Unit tests require access to protected members (_initialize_driver,
# _close_driver, _check_rate_limiting) to properly set up test conditions,
# verify internal state, and test error handling behavior in isolation.


class TestRetryMechanism:
    """Test retry logic for failed downloads."""

    def test_rate_limit_detection_and_retry(self):
        """
        Verify that download succeeds after retrying through rate limit.

        Sequence: Rate limit error -> Success
        """

        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:

            rate_limit_html = "<html><body>Rate limited - please wait</body></html>"
            valid_html = (
                "<html><body>Valid followup website content here</body></html>" * 100
            )

            response_sequence = [rate_limit_html, valid_html]

            with patch(
                "ECI_initiatives.scraper.responses_followup_website.downloader.initialize_browser"
            ) as mock_init_browser, patch(
                "ECI_initiatives.scraper.responses_followup_website.downloader.time.sleep"
            ), patch(
                "ECI_initiatives.scraper.responses_followup_website.downloader.random.uniform",
                return_value=0.1,
            ):

                mock_driver = self._create_mock_driver_with_response_sequence(
                    response_sequence
                )
                mock_init_browser.return_value = mock_driver

                downloader = FollowupWebsiteDownloader(tmpdir)
                downloader.logger = Mock()
                downloader._initialize_driver()

                with patch(
                    "ECI_initiatives.scraper.responses_followup_website.downloader.save_followup_website_html_file",
                    return_value="test.html",
                ):

                    # Act
                    success = downloader.download_single_followup_website(
                        url="https://test.com/followup",
                        year="2019",
                        reg_number="2019_000007",
                        max_retries=3,
                    )

                # Assert
                assert success is True, "Should eventually succeed after retries"
                assert downloader.logger.warning.call_count >= 1

    def _create_mock_driver_with_response_sequence(self, response_sequence):
        """Helper: Create a mock WebDriver that returns responses in sequence."""

        page_source_call_count = 0

        def get_page_source():
            """
            Return HTML response that changes based on call count.

            Simulates a web server that initially rate-limits requests (first 2 calls)
            and then returns valid content (subsequent calls). This mimics real-world
            behavior where retrying after rate limiting eventually succeeds.

            Returns:
                str: Rate limit HTML for calls 0-1, valid HTML for calls 2+.
            """

            # Calculate response index: use 0 for first two calls (rate limit),
            # then 1 for remaining calls (valid content), capped at max index
            nonlocal page_source_call_count

            response_index = min(
                len(response_sequence) - 1, page_source_call_count // 2
            )

            page_source_call_count += 1
            return response_sequence[response_index]

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

            with patch(
                "ECI_initiatives.scraper.responses_followup_website.downloader.initialize_browser"
            ) as mock_init_browser, patch(
                "ECI_initiatives.scraper.responses_followup_website.downloader.time.sleep"
            ):

                mock_driver = MagicMock()
                mock_driver.get.side_effect = Exception("Network timeout")
                mock_init_browser.return_value = mock_driver

                downloader = FollowupWebsiteDownloader(tmpdir)
                downloader.logger = Mock()
                downloader._initialize_driver()

                max_retries = 3

                # Act
                success = downloader.download_single_followup_website(
                    url="https://example.com/followup",
                    year="2019",
                    reg_number="2019_000007",
                    max_retries=max_retries,
                )

                # Assert
                assert success is False, "Download should fail"
                assert mock_driver.get.call_count == max_retries
                downloader.logger.error.assert_called_once()

    def test_rate_limit_detection_raises_exception(self):
        """
        Verify that _check_rate_limiting raises exception when rate limit indicators are found.
        """

        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch(
                "ECI_initiatives.scraper.responses_followup_website.downloader.initialize_browser"
            ) as mock_init_browser:

                mock_driver = MagicMock()
                mock_driver.page_source = (
                    "<html><body>Rate limited - too many requests</body></html>"
                )
                mock_init_browser.return_value = mock_driver

                downloader = FollowupWebsiteDownloader(tmpdir)
                downloader._initialize_driver()

                # Act & Assert
                with pytest.raises(Exception, match="Rate limiting detected"):
                    downloader._check_rate_limiting()

    def test_browser_cleanup_after_errors(self):
        """
        Verify that browser resources are properly cleaned up even if errors occurred.
        """

        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch(
                "ECI_initiatives.scraper.responses_followup_website.downloader.initialize_browser"
            ) as mock_init_browser:

                mock_driver = MagicMock()
                mock_quit = Mock()
                mock_driver.quit = mock_quit
                mock_driver.get.side_effect = Exception("Connection error")
                mock_init_browser.return_value = mock_driver

                downloader = FollowupWebsiteDownloader(tmpdir)
                downloader.logger = Mock()
                downloader._initialize_driver()

                # Act - Attempt download that will fail
                try:
                    downloader.download_single_followup_website(
                        url="https://test-url.com",
                        year="2019",
                        reg_number="000007",
                        max_retries=1,
                    )
                except Exception:
                    pass

                # Close driver
                downloader._close_driver()

                # Assert
                mock_quit.assert_called_once()
