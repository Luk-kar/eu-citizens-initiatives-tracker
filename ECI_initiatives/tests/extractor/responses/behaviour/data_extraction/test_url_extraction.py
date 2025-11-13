"""
Behavioural tests for extracting response and initiative URLs.

This module contains tests for parsing the HTML of European Citizens'
Initiative (ECI) response pages to extract key URLs. It verifies the
correct identification and extraction of:

- The URL of the response page itself, using various fallback mechanisms.
- The URL of the main initiative page, typically found in breadcrumbs or
  other navigation elements.
"""

# Third party
import pytest

# Local
from .test_base import BaseParserTest


class TestResponseURLExtraction(BaseParserTest):
    """Tests for response URL extraction from HTML."""

    def test_extract_response_url_from_active_language_link(self):
        """Test extraction of response URL from active language link."""
        html = """
        <html>
            <header>
                <a href="https://citizens-initiative.europa.eu/initiatives/details/2020/000001/stop-finning-stop-the-trade_en" 
                   class="ecl-link ecl-link--standalone ecl-site-header__language-link ecl-site-header__language-link--active" 
                   hreflang="en">
                    <span class="ecl-site-header__language-link-code">en</span>
                    <span class="ecl-site-header__language-link-label" lang="en">English</span>
                </a>
            </header>
        </html>
        """

        soup = self.create_soup(html)
        url = self.parser.basic_metadata.extract_response_url(soup)

        expected_url = "https://citizens-initiative.europa.eu/initiatives/details/2020/000001/stop-finning-stop-the-trade_en"
        self.assert_url_matches(url, expected_url)

    def test_extract_response_url_with_multiple_languages(self):
        """Test extraction when multiple language links exist."""
        html = """
        <html>
            <header>
                <a href="https://citizens-initiative.europa.eu/initiatives/details/2019/000007/initiative_de" 
                   class="ecl-site-header__language-link" 
                   hreflang="de">
                    <span>de</span>
                </a>
                <a href="https://citizens-initiative.europa.eu/initiatives/details/2019/000007/initiative_en" 
                   class="ecl-site-header__language-link ecl-site-header__language-link--active" 
                   hreflang="en">
                    <span>en</span>
                </a>
                <a href="https://citizens-initiative.europa.eu/initiatives/details/2019/000007/initiative_fr" 
                   class="ecl-site-header__language-link" 
                   hreflang="fr">
                    <span>fr</span>
                </a>
            </header>
        </html>
        """

        soup = self.create_soup(html)
        url = self.parser.basic_metadata.extract_response_url(soup)

        # Should extract the active (en) link, not the others
        self.assert_url_contains(
            url, "_en", "Should extract the active English language link"
        )
        self.assert_url_ends_with(url, "_en", "URL should end with _en language code")

    def test_extract_response_url_fallback_to_en_hreflang(self):
        """Test fallback to hreflang='en' when active class is missing."""
        html = """
        <html>
            <header>
                <a href="https://citizens-initiative.europa.eu/initiatives/details/2012/000003/water-sanitation_en" 
                   class="ecl-site-header__language-link" 
                   hreflang="en">
                    <span>English</span>
                </a>
            </header>
        </html>
        """

        soup = self.create_soup(html)
        url = self.parser.basic_metadata.extract_response_url(soup)

        expected_url = "https://citizens-initiative.europa.eu/initiatives/details/2012/000003/water-sanitation_en"
        self.assert_url_matches(
            url,
            expected_url,
            "Should fallback to hreflang='en' link when active class is missing",
        )

    def test_extract_response_url_from_canonical_fallback(self):
        """Test fallback to canonical link when language links are missing."""
        html = """
        <html>
            <head>
                <link rel="canonical" href="https://citizens-initiative.europa.eu/cohesion-policy-equality-regions_en" />
            </head>
        </html>
        """

        soup = self.create_soup(html)
        url = self.parser.basic_metadata.extract_response_url(soup)

        expected_url = (
            "https://citizens-initiative.europa.eu/cohesion-policy-equality-regions_en"
        )
        self.assert_url_matches(url, expected_url, "Should fallback to canonical link")

    def test_extract_response_url_handles_relative_urls(self):
        """Test that relative URLs are converted to absolute URLs."""
        html = """
        <html>
            <head>
                <link rel="canonical" href="/fur-free-europe_en" />
            </head>
        </html>
        """

        soup = self.create_soup(html)
        url = self.parser.basic_metadata.extract_response_url(soup)

        expected_url = "https://citizens-initiative.europa.eu/fur-free-europe_en"
        self.assert_url_matches(
            url, expected_url, "Should convert relative URL to absolute"
        )

    def test_extract_response_url_missing_all_methods(self):
        """Test that ValueError is raised when no URL sources are found."""
        html = """
        <html>
            <head></head>
            <body>No URL sources</body>
        </html>
        """

        soup = self.create_soup(html)

        with pytest.raises(ValueError, match="Response URL not found"):
            self.parser.basic_metadata.extract_response_url(soup)


class TestInitiativeURLExtraction(BaseParserTest):
    """Tests for initiative URL extraction from HTML."""

    def test_extract_initiative_url_from_breadcrumb(self):
        """Test extraction of initiative URL from breadcrumb link."""
        html = """
        <nav class="ecl-breadcrumb">
            <ol class="ecl-breadcrumb__container">
                <li class="ecl-breadcrumb__segment">
                    <a href="/initiatives/details/2012/000003_en" 
                       class="ecl-link ecl-link--standalone ecl-link--no-visited ecl-breadcrumb__link">
                       Initiative detail
                    </a>
                </li>
            </ol>
        </nav>
        """

        soup = self.create_soup(html)
        url = self.parser.basic_metadata.extract_initiative_url(soup)

        expected_url = (
            "https://citizens-initiative.europa.eu/initiatives/details/2012/000003_en"
        )
        self.assert_url_matches(url, expected_url)

    def test_extract_initiative_url_with_whitespace(self):
        """Test extraction works with whitespace in breadcrumb text."""
        html = """
        <a href="/initiatives/details/2019/000007_en" 
           class="ecl-breadcrumb__link">
           
           Initiative detail
           
        </a>
        """

        soup = self.create_soup(html)
        url = self.parser.basic_metadata.extract_initiative_url(soup)

        expected_url = (
            "https://citizens-initiative.europa.eu/initiatives/details/2019/000007_en"
        )
        self.assert_url_matches(url, expected_url, "Should handle whitespace correctly")

    def test_extract_initiative_url_from_page_link(self):
        """Test fallback to searching page links for initiatives/details pattern."""
        html = """
        <html>
            <body>
                <nav>
                    <a href="https://citizens-initiative.europa.eu/initiatives/details/2017/000002_en">
                        Ban glyphosate and protect people and the environment from toxic pesticides
                    </a>
                </nav>
            </body>
        </html>
        """

        soup = self.create_soup(html)
        url = self.parser.basic_metadata.extract_initiative_url(soup)

        expected_url = (
            "https://citizens-initiative.europa.eu/initiatives/details/2017/000002_en"
        )
        self.assert_url_matches(url, expected_url)

    def test_extract_initiative_url_skips_empty_links(self):
        """Test that links without text are skipped."""
        html = """
        <html>
            <body>
                <a href="/initiatives/details/2022/000002_en"></a>  <!-- Empty, should skip -->
                <a href="/initiatives/details/2022/000002_en">Fur Free Europe</a>  <!-- This one should match -->
            </body>
        </html>
        """

        soup = self.create_soup(html)
        url = self.parser.basic_metadata.extract_initiative_url(soup)

        expected_url = (
            "https://citizens-initiative.europa.eu/initiatives/details/2022/000002_en"
        )
        self.assert_url_matches(
            url, expected_url, "Should find link with text content and skip empty links"
        )

    def test_extract_initiative_url_only_matches_english(self):
        """Test that only _en language URLs are matched."""
        html = """
        <html>
            <body>
                <a href="/initiatives/details/2020/000001_de">German version</a>
                <a href="/initiatives/details/2020/000001_en">English version</a>
            </body>
        </html>
        """

        soup = self.create_soup(html)
        url = self.parser.basic_metadata.extract_initiative_url(soup)

        # Should match English version only
        self.assert_url_ends_with(url, "_en", "Should only match English (_en) URL")
        expected_url = (
            "https://citizens-initiative.europa.eu/initiatives/details/2020/000001_en"
        )
        self.assert_url_matches(url, expected_url)

    def test_extract_initiative_url_missing(self):
        """Test that ValueError is raised when no initiative URL is found."""
        html = """
        <html>
            <body>No initiative URL here</body>
        </html>
        """

        soup = self.create_soup(html)

        with pytest.raises(ValueError, match="Initiative URL not found"):
            self.parser.basic_metadata.extract_initiative_url(soup)
