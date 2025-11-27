"""
Behavioural tests for structural analysis of follow-up website pages.

This module tests extraction of:
- Referenced EU legislation by formal identifiers (CELEX, Official Journal)
- Referenced EU legislation by their common names
"""

# Third party
import pytest
from bs4 import BeautifulSoup

# Local
from ECI_initiatives.extractor.responses_followup_website.parser.extractors import (
    FollowupWebsiteExtractor,
)


class TestLegislativeReferences:
    """Tests for structural analysis fields."""

    @classmethod
    def setup_class(cls):
        """Setup extractor instance."""
        pass

    def test_extract_referenced_legislation_by_id(self):
        """Test extraction of related EU legislation references."""
        # TODO: Test CELEX links
        # TODO: Test Directive references
        # TODO: Test Official Journal references
        # TODO: Test Article references
        pass

    def test_extract_referenced_legislation_by_name(self):
        """Test extraction of referenced EU legislation by name."""
        # TODO: Test Directive names
        # TODO: Test Regulation names
        # TODO: Test Treaty names
        # TODO: Test Charter names
        pass
