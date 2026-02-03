"""
Test suite for browser initialization and management.

Tests Chrome WebDriver initialization with headless configuration,
options application, and proper cleanup after scraping sessions.
"""

# Standard library
from unittest.mock import patch, MagicMock

# Local imports
from ECI_initiatives.data_pipeline.scraper.responses_followup_website.browser import (
    initialize_browser,
)
from ECI_initiatives.data_pipeline.scraper.responses_followup_website.consts import (
    CHROME_OPTIONS,
)

# pylint: disable=unused-variable
# Rationale: Mock objects (mock_chrome) are created as byproducts of patch context
# managers but are not directly referenced in test logic. The patches themselves are
# required to replace browser initialization behavior, while the returned mock objects
# remain unused. This is an acceptable pattern when testing side effects of patches
# rather than mock interactions.


class TestBrowserInitialization:
    """Test browser initialization and configuration."""

    def test_browser_initialized_with_chrome_options(self):
        """
        When initializing the browser, verify that all configured
        Chrome options are applied to the WebDriver instance.
        """
        # Arrange
        with patch(
            "ECI_initiatives.data_pipeline.scraper.responses_followup_website.browser.webdriver.Chrome"
        ) as mock_chrome, patch(
            "ECI_initiatives.data_pipeline.scraper.responses_followup_website.browser.Options"
        ) as mock_options:

            mock_options_instance = MagicMock()
            mock_options.return_value = mock_options_instance
            mock_driver = MagicMock()
            mock_chrome.return_value = mock_driver

            # Act
            driver = initialize_browser()

            # Assert - Verify all CHROME_OPTIONS were added
            assert mock_options_instance.add_argument.call_count == len(
                CHROME_OPTIONS
            ), f"Should add {len(CHROME_OPTIONS)} Chrome options"

            # Verify each specific option was added
            for option in CHROME_OPTIONS:
                mock_options_instance.add_argument.assert_any_call(option)

            # Verify Chrome was initialized with options
            mock_chrome.assert_called_once_with(options=mock_options_instance)

            # Verify driver was returned
            assert driver == mock_driver

    def test_browser_initialization_headless_mode(self):
        """
        Verify that the browser is initialized in headless mode
        (required for server environments without display).
        """
        # Arrange
        with patch(
            "ECI_initiatives.data_pipeline.scraper.responses_followup_website.browser.webdriver.Chrome"
        ) as mock_chrome, patch(
            "ECI_initiatives.data_pipeline.scraper.responses_followup_website.browser.Options"
        ) as mock_options:

            mock_options_instance = MagicMock()
            mock_options.return_value = mock_options_instance

            # Act
            initialize_browser()

            # Assert - Verify headless option is set
            mock_options_instance.add_argument.assert_any_call("--headless")

    def test_browser_initialization_no_sandbox_mode(self):
        """
        Verify that the browser is initialized with --no-sandbox option
        (required for Docker and CI environments).
        """
        # Arrange
        with patch(
            "ECI_initiatives.data_pipeline.scraper.responses_followup_website.browser.webdriver.Chrome"
        ) as mock_chrome, patch(
            "ECI_initiatives.data_pipeline.scraper.responses_followup_website.browser.Options"
        ) as mock_options:

            mock_options_instance = MagicMock()
            mock_options.return_value = mock_options_instance

            # Act
            initialize_browser()

            # Assert
            mock_options_instance.add_argument.assert_any_call("--no-sandbox")

    def test_browser_initialization_disable_dev_shm(self):
        """
        Verify that the browser disables /dev/shm usage
        (prevents crashes in Docker with limited shared memory).
        """
        # Arrange
        with patch(
            "ECI_initiatives.data_pipeline.scraper.responses_followup_website.browser.webdriver.Chrome"
        ) as mock_chrome, patch(
            "ECI_initiatives.data_pipeline.scraper.responses_followup_website.browser.Options"
        ) as mock_options:

            mock_options_instance = MagicMock()
            mock_options.return_value = mock_options_instance

            # Act
            initialize_browser()

            # Assert
            mock_options_instance.add_argument.assert_any_call(
                "--disable-dev-shm-usage"
            )
