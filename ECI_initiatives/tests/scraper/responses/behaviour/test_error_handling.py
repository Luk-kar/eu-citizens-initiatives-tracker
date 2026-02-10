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
from ECI_initiatives.data_pipeline.scraper.responses.downloader import (
    ResponseDownloader,
)


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
            server_error_html = (
                "<html><body>We apologise for any inconvenience</body></html>"
            )
            valid_response_html = (
                "<html><body>Valid Commission response content here</body></html>" * 100
            )

            # Response sequence: fail twice, then succeed
            response_sequence = [
                rate_limit_html,
                server_error_html,
                valid_response_html,
            ]

            # Arrange: Set up mocks
            with patch(
                "ECI_initiatives.data_pipeline.scraper.responses.downloader.initialize_browser"
            ) as mock_init_browser, patch(
                "ECI_initiatives.data_pipeline.scraper.responses.downloader.time.sleep"
            ), patch(
                "ECI_initiatives.data_pipeline.scraper.responses.downloader.random.uniform",
                return_value=0.1,
            ):

                # Create mock WebDriver
                mock_driver = self._create_mock_driver_with_response_sequence(
                    response_sequence
                )
                mock_init_browser.return_value = mock_driver

                # Create downloader with mocked logger
                downloader = ResponseDownloader(tmpdir)
                downloader.logger = Mock()
                downloader._initialize_driver()

                # Mock file save to avoid I/O
                with patch(
                    "ECI_initiatives.data_pipeline.scraper.responses.downloader.save_response_html_file",
                    return_value="test.html",
                ):

                    # Act: Attempt download with retries
                    success, timestamp = downloader.download_single_response(
                        url="https://test.com/response",
                        year="2019",
                        reg_number="2019_000007",
                        max_retries=3,
                    )

                # Assert: Download eventually succeeds
                assert success is True, "Should eventually succeed after retries"
                assert timestamp != "", "Should have timestamp on success"

                # Assert: Warnings logged for failed attempts
                assert (
                    downloader.logger.warning.call_count >= 1
                ), "Should log warnings for failed attempts"

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

            response_index = min(
                len(response_sequence) - 1, page_source_call_count // 2
            )
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
            with patch(
                "ECI_initiatives.data_pipeline.scraper.responses.downloader.initialize_browser"
            ) as mock_init_browser, patch(
                "ECI_initiatives.data_pipeline.scraper.responses.downloader.time.sleep"
            ):

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
                    max_retries=max_retries,
                )

                # Assert
                assert success is False, "Download should fail"
                assert timestamp == "", "Failed download should have empty timestamp"
                assert (
                    mock_driver.get.call_count == max_retries
                ), f"Should attempt {max_retries} times"

                # Verify final error was logged
                downloader.logger.error.assert_called_once()

    def test_successful_retry_after_transient_failure(self):
        """
        Verify successful download after transient failures.
        """

        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch(
                "ECI_initiatives.data_pipeline.scraper.responses.downloader.initialize_browser"
            ) as mock_init_browser, patch(
                "ECI_initiatives.data_pipeline.scraper.responses.downloader.time.sleep"
            ), patch(
                "ECI_initiatives.data_pipeline.scraper.responses.downloader.random.uniform",
                return_value=0.1,
            ):

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
                    valid_html = (
                        "<html><body>Valid Commission response content here</body></html>"
                        * 100
                    )

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

                with patch(
                    "ECI_initiatives.data_pipeline.scraper.responses.downloader.save_response_html_file",
                    return_value="test.html",
                ):

                    # Act
                    success, timestamp = downloader.download_single_response(
                        url="https://test.com/response",
                        year="2019",
                        reg_number="2019_000007",
                        max_retries=3,
                    )

                # Assert
                assert success is True, "Should succeed after transient failures"
                assert timestamp != "", "Should have timestamp"
                assert (
                    download_attempts == 3
                ), f"Should take 3 download attempts, but took {download_attempts}"

                # Verify warnings were logged for failures
                assert (
                    downloader.logger.warning.call_count == 2
                ), "Should log warning for each failed attempt"

    def test_rate_limit_detection_raises_exception(self):
        """
        Verify that _check_rate_limiting raises exception when rate limit indicators are found.
        """

        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch(
                "ECI_initiatives.data_pipeline.scraper.responses.downloader.initialize_browser"
            ) as mock_init_browser:

                mock_driver = MagicMock()
                mock_driver.page_source = (
                    "<html><body>Rate limited - too many requests</body></html>"
                )
                mock_init_browser.return_value = mock_driver

                downloader = ResponseDownloader(tmpdir)
                downloader._initialize_driver()

                # Act & Assert
                with pytest.raises(Exception, match="Rate limiting detected"):
                    downloader._check_rate_limiting()
