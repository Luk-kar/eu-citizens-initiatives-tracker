"""Base test classes and utilities for ECI response extraction tests."""

# Standard library
from typing import Optional

# Third party
from bs4 import BeautifulSoup

# Local
from ECI_initiatives.data_pipeline.extractor.responses.parser.main_parser import (
    ECIResponseHTMLParser,
)
from ECI_initiatives.data_pipeline.extractor.responses.responses_logger import (
    ResponsesExtractorLogger,
)


class BaseParserTest:
    """Base test class with common test utilities."""

    @classmethod
    def setup_class(cls):
        """Setup parser instance."""
        logger = ResponsesExtractorLogger().setup()
        cls.parser = ECIResponseHTMLParser(logger=logger)

    @staticmethod
    def create_soup(html: str) -> BeautifulSoup:
        """Create BeautifulSoup object from HTML string.

        Args:
            html: HTML string to parse

        Returns:
            BeautifulSoup object
        """
        return BeautifulSoup(html, "html.parser")

    def assert_url_matches(
        self, actual: str, expected: str, message: Optional[str] = None
    ) -> None:
        """Assert that actual URL matches expected URL.

        Args:
            actual: Actual URL returned from parser
            expected: Expected URL
            message: Optional custom error message
        """
        default_message = f"Expected URL '{expected}', got '{actual}'"
        assert actual == expected, message or default_message

    def assert_url_contains(
        self, url: str, substring: str, message: Optional[str] = None
    ) -> None:
        """Assert that URL contains substring.

        Args:
            url: URL to check
            substring: Substring to find
            message: Optional custom error message
        """
        default_message = f"Expected URL to contain '{substring}', got '{url}'"
        assert substring in url, message or default_message

    def assert_url_ends_with(
        self, url: str, suffix: str, message: Optional[str] = None
    ) -> None:
        """Assert that URL ends with suffix.

        Args:
            url: URL to check
            suffix: Expected suffix
            message: Optional custom error message
        """
        default_message = f"Expected URL to end with '{suffix}', got '{url}'"
        assert url.endswith(suffix), message or default_message
