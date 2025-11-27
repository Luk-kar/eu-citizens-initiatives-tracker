"""
Behavioural tests for basic metadata extraction from follow-up websites.

This module tests extraction of:
- Registration numbers from URLs or page content
- Page structure identification
"""

# Third party
import pytest
from bs4 import BeautifulSoup

# Local
from ECI_initiatives.extractor.responses_followup_website.parser.extractors import (
    FollowupWebsiteExtractor,
)


class TestBasicMetadataExtraction:
    """Tests for basic metadata extraction."""

    @classmethod
    def setup_class(cls):
        """Setup extractor instance."""
        # TODO: Initialize extractor with mock HTML
        pass

    def test_extract_registration_number_from_url(self):
        """Test extraction of registration number from URL patterns."""
        # TODO: Implement test
        pass

    def test_extract_registration_number_from_content(self):
        """Test extraction of registration number from page content."""
        # TODO: Implement test
        pass

    def test_extract_registration_number_missing(self):
        """Test error handling when registration number not found."""
        # TODO: Implement test
        pass
