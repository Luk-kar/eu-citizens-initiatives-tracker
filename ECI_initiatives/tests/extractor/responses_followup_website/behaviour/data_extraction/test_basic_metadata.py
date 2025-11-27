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

    def test_extract_registration_number_file_name(self):
        """Test extraction of registration number from filename patterns."""
        extractor = FollowupWebsiteExtractor("")

        # Test standard format: YYYY_NNNNNN_en.html -> YYYY/NNNNNN
        result = extractor.extract_registration_number("2018_000004_en.html")
        assert result == "2018/000004"

        result = extractor.extract_registration_number("2022_000002_en.html")
        assert result == "2022/000002"

    def test_extract_registration_number_missing(self):
        """Test error handling when registration number not found."""
        extractor = FollowupWebsiteExtractor("")

        # Test invalid filename format raises ValueError
        with pytest.raises(ValueError, match="Invalid filename format"):
            extractor.extract_registration_number("invalid_filename.html")

        with pytest.raises(ValueError, match="Invalid filename format"):
            extractor.extract_registration_number("2018_0004_en.html")  # Wrong
