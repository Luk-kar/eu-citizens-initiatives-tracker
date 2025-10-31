"""
Test suite for validating data extraction from response HTML files.

Tests focus on behavior of extraction methods:
- Response URL extraction
- Initiative URL extraction
- Submission and verification data
- Procedural timeline milestones
- Commission response content
- Follow-up activities
- Multimedia and documentation
- Structural analysis
"""

# Standard library
from pathlib import Path
import json

# Third party
import pytest
from bs4 import BeautifulSoup

# Local
from ECI_initiatives.extractor.responses.parser import ECIResponseHTMLParser, LegislativeOutcomeExtractor
from ECI_initiatives.extractor.responses.responses_logger import ResponsesExtractorLogger


from typing import Optional
from datetime import date as date_type
import pytest
from bs4 import BeautifulSoup


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
        return BeautifulSoup(html, 'html.parser')
    
    def assert_url_matches(self, actual: str, expected: str, message: Optional[str] = None) -> None:
        """Assert that actual URL matches expected URL.
        
        Args:
            actual: Actual URL returned from parser
            expected: Expected URL
            message: Optional custom error message
        """
        default_message = f"Expected URL '{expected}', got '{actual}'"
        assert actual == expected, message or default_message
    
    def assert_url_contains(self, url: str, substring: str, message: Optional[str] = None) -> None:
        """Assert that URL contains substring.
        
        Args:
            url: URL to check
            substring: Substring to find
            message: Optional custom error message
        """
        default_message = f"Expected URL to contain '{substring}', got '{url}'"
        assert substring in url, message or default_message
    
    def assert_url_ends_with(self, url: str, suffix: str, message: Optional[str] = None) -> None:
        """Assert that URL ends with suffix.
        
        Args:
            url: URL to check
            suffix: Expected suffix
            message: Optional custom error message
        """
        default_message = f"Expected URL to end with '{suffix}', got '{url}'"
        assert url.endswith(suffix), message or default_message


class TestResponseURLExtraction(BaseParserTest):
    """Tests for response URL extraction from HTML."""
    
    def test_extract_response_url_from_active_language_link(self):
        """Test extraction of response URL from active language link."""
        html = '''
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
        '''
        
        soup = self.create_soup(html)
        url = self.parser.basic_metadata.extract_response_url(soup)
        
        expected_url = "https://citizens-initiative.europa.eu/initiatives/details/2020/000001/stop-finning-stop-the-trade_en"
        self.assert_url_matches(url, expected_url)

    def test_extract_response_url_with_multiple_languages(self):
        """Test extraction when multiple language links exist."""
        html = '''
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
        '''
        
        soup = self.create_soup(html)
        url = self.parser.basic_metadata.extract_response_url(soup)
        
        # Should extract the active (en) link, not the others
        self.assert_url_contains(url, "_en", "Should extract the active English language link")
        self.assert_url_ends_with(url, "_en", "URL should end with _en language code")

    def test_extract_response_url_fallback_to_en_hreflang(self):
        """Test fallback to hreflang='en' when active class is missing."""
        html = '''
        <html>
            <header>
                <a href="https://citizens-initiative.europa.eu/initiatives/details/2012/000003/water-sanitation_en" 
                   class="ecl-site-header__language-link" 
                   hreflang="en">
                    <span>English</span>
                </a>
            </header>
        </html>
        '''
        
        soup = self.create_soup(html)
        url = self.parser.basic_metadata.extract_response_url(soup)
        
        expected_url = "https://citizens-initiative.europa.eu/initiatives/details/2012/000003/water-sanitation_en"
        self.assert_url_matches(url, expected_url, "Should fallback to hreflang='en' link when active class is missing")

    def test_extract_response_url_from_canonical_fallback(self):
        """Test fallback to canonical link when language links are missing."""
        html = '''
        <html>
            <head>
                <link rel="canonical" href="https://citizens-initiative.europa.eu/cohesion-policy-equality-regions_en" />
            </head>
        </html>
        '''
        
        soup = self.create_soup(html)
        url = self.parser.basic_metadata.extract_response_url(soup)
        
        expected_url = "https://citizens-initiative.europa.eu/cohesion-policy-equality-regions_en"
        self.assert_url_matches(url, expected_url, "Should fallback to canonical link")

    def test_extract_response_url_handles_relative_urls(self):
        """Test that relative URLs are converted to absolute URLs."""
        html = '''
        <html>
            <head>
                <link rel="canonical" href="/fur-free-europe_en" />
            </head>
        </html>
        '''
        
        soup = self.create_soup(html)
        url = self.parser.basic_metadata.extract_response_url(soup)
        
        expected_url = "https://citizens-initiative.europa.eu/fur-free-europe_en"
        self.assert_url_matches(url, expected_url, "Should convert relative URL to absolute")

    def test_extract_response_url_missing_all_methods(self):
        """Test that ValueError is raised when no URL sources are found."""
        html = '''
        <html>
            <head></head>
            <body>No URL sources</body>
        </html>
        '''
        
        soup = self.create_soup(html)
        
        with pytest.raises(ValueError, match="Response URL not found"):
            self.parser.basic_metadata.extract_response_url(soup)


class TestInitiativeURLExtraction(BaseParserTest):
    """Tests for initiative URL extraction from HTML."""
    
    def test_extract_initiative_url_from_breadcrumb(self):
        """Test extraction of initiative URL from breadcrumb link."""
        html = '''
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
        '''
        
        soup = self.create_soup(html)
        url = self.parser.basic_metadata.extract_initiative_url(soup)
        
        expected_url = "https://citizens-initiative.europa.eu/initiatives/details/2012/000003_en"
        self.assert_url_matches(url, expected_url)

    def test_extract_initiative_url_with_whitespace(self):
        """Test extraction works with whitespace in breadcrumb text."""
        html = '''
        <a href="/initiatives/details/2019/000007_en" 
           class="ecl-breadcrumb__link">
           
           Initiative detail
           
        </a>
        '''
        
        soup = self.create_soup(html)
        url = self.parser.basic_metadata.extract_initiative_url(soup)
        
        expected_url = "https://citizens-initiative.europa.eu/initiatives/details/2019/000007_en"
        self.assert_url_matches(url, expected_url, "Should handle whitespace correctly")

    def test_extract_initiative_url_from_page_link(self):
        """Test fallback to searching page links for initiatives/details pattern."""
        html = '''
        <html>
            <body>
                <nav>
                    <a href="https://citizens-initiative.europa.eu/initiatives/details/2017/000002_en">
                        Ban glyphosate and protect people and the environment from toxic pesticides
                    </a>
                </nav>
            </body>
        </html>
        '''
        
        soup = self.create_soup(html)
        url = self.parser.basic_metadata.extract_initiative_url(soup)
        
        expected_url = "https://citizens-initiative.europa.eu/initiatives/details/2017/000002_en"
        self.assert_url_matches(url, expected_url)

    def test_extract_initiative_url_skips_empty_links(self):
        """Test that links without text are skipped."""
        html = '''
        <html>
            <body>
                <a href="/initiatives/details/2022/000002_en"></a>  <!-- Empty, should skip -->
                <a href="/initiatives/details/2022/000002_en">Fur Free Europe</a>  <!-- This one should match -->
            </body>
        </html>
        '''
        
        soup = self.create_soup(html)
        url = self.parser.basic_metadata.extract_initiative_url(soup)
        
        expected_url = "https://citizens-initiative.europa.eu/initiatives/details/2022/000002_en"
        self.assert_url_matches(url, expected_url, "Should find link with text content and skip empty links")

    def test_extract_initiative_url_only_matches_english(self):
        """Test that only _en language URLs are matched."""
        html = '''
        <html>
            <body>
                <a href="/initiatives/details/2020/000001_de">German version</a>
                <a href="/initiatives/details/2020/000001_en">English version</a>
            </body>
        </html>
        '''
        
        soup = self.create_soup(html)
        url = self.parser.basic_metadata.extract_initiative_url(soup)
        
        # Should match English version only
        self.assert_url_ends_with(url, "_en", "Should only match English (_en) URL")
        expected_url = "https://citizens-initiative.europa.eu/initiatives/details/2020/000001_en"
        self.assert_url_matches(url, expected_url)

    def test_extract_initiative_url_missing(self):
        """Test that ValueError is raised when no initiative URL is found."""
        html = '''
        <html>
            <body>No initiative URL here</body>
        </html>
        '''
        
        soup = self.create_soup(html)
        
        with pytest.raises(ValueError, match="Initiative URL not found"):
            self.parser.basic_metadata.extract_initiative_url(soup)


class TestSubmissionDataExtraction(BaseParserTest):
    """Tests for submission and verification data extraction."""
    
    def _create_submission_html(self, submission_text: str) -> str:
        """Helper to create HTML with submission section.
        
        Args:
            submission_text: Text content for submission paragraph
            
        Returns:
            Complete HTML string with submission section
        """
        return f'''
        <html>
            <body>
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>{submission_text}</p>
            </body>
        </html>
        '''
    
    def test_commission_submission_date_extraction(self):
        """Test extraction of submission date."""
        # Test Case 1: DD Month YYYY format (most common)
        html = self._create_submission_html('''
            <a href="https://citizens-initiative.europa.eu/initiatives/details/2017/000002_en">
                Ban glyphosate and protect people and the environment from toxic pesticides
            </a>
            was submitted to the Commission on 6 October 2017, having gathered 1,070,865 statements of support.
        ''')
        
        soup = self.create_soup(html)
        date = self.parser.submission_data.extract_commission_submission_date(soup)
        
        expected_date = date_type(2017, 10, 6)
        assert date == expected_date, f"Expected date {expected_date}, got {date}"
        assert isinstance(date, date_type), "Should return datetime.date object"

        # Test Case 2: DD/MM/YYYY format
        html_ddmmyyyy = self._create_submission_html(
            'One of us was submitted to the Commission on 28/02/2014 having gathered 1,721,626 statements of support.'
        )
        
        soup = self.create_soup(html_ddmmyyyy)
        date = self.parser.submission_data.extract_commission_submission_date(soup)
        
        expected_date = date_type(2014, 2, 28)
        assert date == expected_date, f"Expected date {expected_date}, got {date}"

        # Test Case 3: With "European Commission" variation
        html_european = self._create_submission_html(
            "The 'Cohesion policy' initiative was submitted to the European Commission on 4 March 2025, "
            "after having gathered 1,269,351 verified statements of support."
        )
        
        soup = self.create_soup(html_european)
        date = self.parser.submission_data.extract_commission_submission_date(soup)
        
        expected_date = date_type(2025, 3, 4)
        assert date == expected_date, f"Expected date {expected_date}, got {date}"

        # Test Case 4: Missing date should raise ValueError
        html_no_date = self._create_submission_html('No date information here.')
        
        soup = self.create_soup(html_no_date)
        
        # Mock the registration_number instance variable
        self.parser.registration_number = "2099/999999"

        with pytest.raises(ValueError, match="No submission date found for initiative 2099/999999"):
            self.parser.submission_data.extract_commission_submission_date(soup)

    def test_submission_news_url(self):
        """Test extraction of submission news URL."""
        test_cases = [
            # (description, submission_text, expected_url)
            (
                "Standard press release with presscorner URL",
                '''
                <a href="https://citizens-initiative.europa.eu/initiatives/details/2012/000003_en">Right2Water</a>
                was submitted to the Commission on 20 December 2013. See
                <a href="https://ec.europa.eu/commission/presscorner/detail/en/mex_13_1223">press release</a>.
                ''',
                "https://ec.europa.eu/commission/presscorner/detail/en/mex_13_1223"
            ),
            (
                "Press announcement variation",
                '''
                The 'Stop Finning' initiative was submitted to the Commission on 11 January 2023. See
                <a href="https://ec.europa.eu/commission/presscorner/detail/en/mex_23_143">press announcement</a>.
                ''',
                "https://ec.europa.eu/commission/presscorner/detail/en/mex_23_143"
            ),
            (
                "European Commission news variation",
                '''
                The initiative was submitted to the European Commission on 4 March 2025. See
                <a href="https://ec.europa.eu/commission/presscorner/detail/en/mex_25_680">European Commission news</a>.
                ''',
                "https://ec.europa.eu/commission/presscorner/detail/en/mex_25_680"
            ),
            (
                "Old europa.eu/rapid format",
                '''
                Ban glyphosate was submitted to the Commission on 6 October 2017. See
                <a href="http://europa.eu/rapid/press-release_MEX-17-3748_en.htm">press release</a>.
                ''',
                "http://europa.eu/rapid/press-release_MEX-17-3748_en.htm"
            ),
            (
                "Case insensitive matching",
                '''
                Initiative submitted. See
                <a href="https://ec.europa.eu/commission/presscorner/detail/en/mex_20_1000">PRESS RELEASE</a>.
                ''',
                "https://ec.europa.eu/commission/presscorner/detail/en/mex_20_1000"
            )
        ]
        
        for description, submission_text, expected_url in test_cases:
            html = self._create_submission_html(submission_text)
            soup = self.create_soup(html)
            url = self.parser.submission_data.extract_submission_news_url(soup)
            
            self.assert_url_matches(url, expected_url, f"Failed for: {description}")

        # Test Case: Multiple links - should skip initiative link and get press link
        html_multiple = self._create_submission_html('''
            <a href="https://citizens-initiative.europa.eu/initiatives/details/2018/000004_en">'End the Cage Age'</a>
            initiative was submitted to the Commission on 2 October 2020. See
            <a href="https://ec.europa.eu/commission/presscorner/detail/en/MEX_20_1810">press release</a>.
        ''')
        
        soup = self.create_soup(html_multiple)
        url = self.parser.submission_data.extract_submission_news_url(soup)
        
        # Should get the presscorner URL, not the initiative URL
        self.assert_url_contains(url, 'presscorner', "Should extract presscorner URL, not initiative URL")
        self.assert_url_matches(url, "https://ec.europa.eu/commission/presscorner/detail/en/MEX_20_1810")

        # Test Case: Missing news URL should raise ValueError
        html_no_news = self._create_submission_html('''
            <a href="https://citizens-initiative.europa.eu/initiatives/details/2020/000001_en">Initiative</a>
            was submitted but no press release link here.
        ''')
        
        soup = self.create_soup(html_no_news)

        with pytest.raises(ValueError, match="No submission news URL found for initiative"):
            self.parser.submission_data.extract_submission_news_url(soup)


class TestProceduralTimelineExtraction:
    """Tests for procedural timeline milestones extraction."""
    
    @classmethod
    def setup_class(cls):
        """Setup parser instance."""
        logger = ResponsesExtractorLogger().setup()
        cls.parser = ECIResponseHTMLParser(logger=logger)
    
    def test_commission_meeting_date(self):
        """Test extraction of Commission meeting date."""
        
        test_cases = [
            # Test case 1: Post-2020 format with Article 15 and month name
            (
                """
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>The initiative was submitted to the Commission on 4 March 2025.</p>
                <p>On 25 March 2025, the initiative organisers were given the opportunity to present 
                the objectives of their initiative in the meeting with Executive Vice-President 
                Raffaele Fitto and European Commission officials, in line with Article 15 of the 
                ECI Regulation. See the photo news.</p>
                <p>A public hearing took place at the European Parliament on 25 June 2025.</p>
                """,
                "2025-03-25",
                "post_2020_article_15",
                False  # should not raise
            ),
            # Test case 2: Pre-2020 format with month name at end
            (
                """
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>Right2Water was submitted to the Commission on 20 December 2013.</p>
                <p>The organisers met with Commission Vice-President Maroš Šefčovič on 17 February 2014. 
                See press release.</p>
                <p>A public hearing took place at the European Parliament on 17 February 2014.</p>
                """,
                "2014-02-17",
                "pre_2020_month_name",
                False
            ),
            # Test case 3: Slash format DD/MM/YYYY
            (
                """
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>One of us was submitted to the Commission on 28/02/2014.</p>
                <p>The organisers met with the Commissioner responsible for Research, Innovation and Science, 
                Ms Geoghegan-Quinn, and the Deputy Director-General responsible for Development and Cooperation, 
                Mr. Cornaro on 09/04/2014. See press release.</p>
                <p>A public hearing took place at the European Parliament on 10/04/2014.</p>
                """,
                "2014-04-09",
                "slash_format",
                False
            ),
            # Test case 4: Multiple officials mentioned
            (
                """
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>The initiative was submitted on 6 October 2017.</p>
                <p>The organisers met with European Commission First Vice-President Frans Timmermans 
                and Commissioner for Health & Food Safety Vytenis Andriukaitis on 23/10/2017. 
                See press release.</p>
                """,
                "2017-10-23",
                "multiple_officials",
                False
            ),
            # Test case 5: Recent format with European Commission officials
            (
                """
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>The initiative was submitted to the Commission on 14 June 2023.</p>
                <p>The organisers met with the European Commission Vice-President for Values and Transparency, 
                Věra Jourová and the Commissioner for Health and Food Safety, Stella Kyriakides on 20 July 2023. 
                See press announcement and photos.</p>
                """,
                "2023-07-20",
                "recent_format",
                False
            ),
            # Test case 6: No commission meeting (raises ValueError)
            (
                """
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>The initiative was submitted to the Commission on 15 May 2024.</p>
                <p>A public hearing took place at the European Parliament on 20 June 2024.</p>
                """,
                None,
                "no_meeting",
                True  # should_raise
            ),
            # Test case 7: No submission section (raises ValueError)
            (
                """
                <h2 id="Other-section">Other section</h2>
                <p>Some content here.</p>
                """,
                None,
                "no_section",
                True  # should_raise
            ),
            # Test case 8: Long format with responsibilities
            (
                """
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>Stop Vivisection was submitted to the Commission on 3 March 2015.</p>
                <p>The organisers met with European Commission Vice-President Jyrki Katainen, 
                responsible for Jobs, Growth, Investment and Competitiveness and Director-General 
                Karl Falkenberg, responsible for DG Environment, on 11 May 2015. See press release.</p>
                """,
                "2015-05-11",
                "long_format_with_responsibilities",
                False
            ),
        ]
        
        for html, expected, test_id, should_raise in test_cases:

            soup = BeautifulSoup(html, 'html.parser')
            parser = ECIResponseHTMLParser(soup)
            parser.registration_number = "2024/000001"
            
            if should_raise:

                # Expect ValueError to be raised
                with pytest.raises(ValueError) as exc_info:
                    parser.procedural_timeline.extract_commission_meeting_date(soup)
                assert "commission meeting date" in str(exc_info.value).lower(), f"Failed for test case: {test_id}"

            else:
                # Normal case - should return expected value
                result = parser.procedural_timeline.extract_commission_meeting_date(soup)
                assert result == expected, f"Failed for test case: {test_id}"

    def test_submission_text(self):
        """Test extraction of submission section text."""
        
        test_cases = [
            # Test case 1: Simple single paragraph
            (
                """
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>The initiative was submitted to the Commission on 14 June 2023.</p>
                """,
                "The initiative was submitted to the Commission on 14 June 2023.",
                "single_paragraph"
            ),
            # Test case 2: Multiple paragraphs
            (
                """
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>The initiative was submitted on 14 June 2023, having gathered 1,502,319 statements of support.</p>
                <p>The organisers met with Commission officials on 20 July 2023.</p>
                <p>A public hearing took place on 10 October 2023.</p>
                """,
                "The initiative was submitted on 14 June 2023, having gathered 1,502,319 statements of support. The organisers met with Commission officials on 20 July 2023. A public hearing took place on 10 October 2023.",
                "multiple_paragraphs"
            ),
            # Test case 3: Paragraphs with links (space preservation)
            (
                """
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p><a href="/url">Right2Water</a> was the first <a href="/url2">European Citizens' Initiative</a> having gathered signatures.</p>
                """,
                "Right2Water was the first European Citizens' Initiative having gathered signatures.",
                "with_links"
            ),
            # Test case 4: Multiple spaces and newlines normalization
            (
                """
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>The initiative    was   submitted
                on 14 June  2023.</p>
                """,
                "The initiative was submitted on 14 June 2023.",
                "whitespace_normalization"
            ),
            # Test case 5: Stops at next section
            (
                """
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>First paragraph in submission section.</p>
                <p>Second paragraph in submission section.</p>
                <h2 id="Answer">Answer of the Commission</h2>
                <p>This should not be included.</p>
                """,
                "First paragraph in submission section. Second paragraph in submission section.",
                "stops_at_next_section"
            ),
            # Test case 6: Empty paragraphs ignored
            (
                """
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>First paragraph.</p>
                <p>   </p>
                <p>Third paragraph.</p>
                """,
                "First paragraph. Third paragraph.",
                "empty_paragraphs_ignored"
            ),
        ]
        
        for html, expected, test_id in test_cases:
            soup = BeautifulSoup(html, 'html.parser')
            parser = ECIResponseHTMLParser(soup)
            parser.registration_number = "2024/000001"
            
            try:
                result = parser.submission_data.extract_submission_text(soup)
                assert result == expected, (
                    f"Failed for test case: {test_id}\n"
                    f"Expected: {expected}\n"
                    f"Got: {result}\n"
                    f"HTML:\n{html}"
                )
            except Exception as e:
                raise AssertionError(
                    f"Error in test case: {test_id}\n"
                    f"Expected: {expected}\n"
                    f"HTML:\n{html}\n"
                    f"Error: {str(e)}\n"
                ) from e


    def test_commission_officials_met(self):
        """Test extraction of Commission officials who met organizers."""
        
        test_cases = [
            # Test case 1: Simple format - single Vice-President
            (
                """
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>The organisers met with Commission Vice-President Maroš Šefčovič on 17 February 2014.</p>
                """,
                "Vice-President Maroš Šefčovič",
                "single_vice_president",
                False
            ),
            # Test case 2: Post-2020 format with Executive Vice-President
            (
                """
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>  On 25 March 2025, the initiative organisers were given the opportunity to present the objectives of their initiative in the meeting with Executive Vice-President Raffaele Fitto and European Commission officials, in line with Article 15 of the ECI Regulation.</p>
                """,
                "Executive Vice-President Raffaele Fitto",
                "executive_vp_post_2020",
                False
            ),
            # Test case 3: Multiple officials with portfolios
            (
                """
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>The organisers met with the European Commission Vice-President for Values and Transparency, Věra Jourová and the Commissioner for Health and Food Safety, Stella Kyriakides on 30 October 2020.</p>
                """,
                "Vice-President for Values and Transparency, Věra Jourová; Commissioner for Health and Food Safety, Stella Kyriakides",
                "multiple_with_portfolios",
                False
            ),
            # Test case 4: Officials with responsibilities
            (
                """
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>The organisers met with European Commission Vice-President Jyrki Katainen, responsible for Jobs, Growth, Investment and Competitiveness and Director-General Karl Falkenberg, responsible for DG Environment, on 11 May 2015. See press release.</p>
                """,
                "Vice-President Jyrki Katainen, responsible for Jobs, Growth, Investment and Competitiveness; Director-General Karl Falkenberg, responsible for DG Environment",
                "with_responsibilities",
                False
            ),
            # Test case 5: Slash date format
            (
                """
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>The organisers met with the Commissioner responsible for Research, Innovation and Science, 
                The organisers met with the Commissioner responsible for Research, Innovation and Science, Ms Geoghegan-Quinn, and the Deputy Director-General responsible for Development and Cooperation, Mr. Cornaro on 09/04/2014. See press release.</p>
                """,
                "the Commissioner responsible for Research, Innovation and Science, Ms Geoghegan-Quinn; Deputy Director-General responsible for Development and Cooperation, Mr. Cornaro",
                "slash_date_format",
                False
            ),
            # Test case 6: First Vice-President (normalized)
            (
                """
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>The organisers met with European Commission First Vice-President Frans Timmermans and Commissioner for Health & Food Safety Vytenis Andriukaitis on 23/10/2017.</p>
                """,
                "Vice-President Frans Timmermans; Commissioner for Health & Food Safety Vytenis Andriukaitis",
                "first_vp_normalized",
                False
            ),
            # Test case 7: Two Commissioners
            (
                """
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>The organisers met with the European Commission Vice-President for Values and Transparency, Věra Jourová and the Commissioner for Environment, Oceans and Fisheries, Virginijus Sinkevičius on 6 February 2023.</p>
                """,
                "Vice-President for Values and Transparency, Věra Jourová; Commissioner for Environment, Oceans and Fisheries, Virginijus Sinkevičius",
                "two_commissioners",
                False
            ),
            (
                """
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>The initiative was submitted to the Commission on 15 May 2024.</p>
                <p>A public hearing took place at the European Parliament on 20 June 2024.</p>
                """,
                None,
                "no_meeting",
                True
            ),
            # Test case 9: No submission section (raises error)
            (
                """
                <h2 id="Other-section">Other section</h2>
                <p>Some content here.</p>
                """,
                None,
                "no_section",
                True
            ),
        ]
        
        for html, expected, test_id, should_raise in test_cases:
            soup = BeautifulSoup(html, 'html.parser')
            parser = ECIResponseHTMLParser(soup)
            parser.registration_number = "2024/000001"
            
            if should_raise:
                # Expect ValueError to be raised
                with pytest.raises(ValueError) as exc_info:
                    parser.procedural_timeline.extract_commission_officials_met(soup)
                assert "commission official" in str(exc_info.value).lower(), f"Failed for test case: {test_id}"
            else:
                # Normal case - should return expected value
                try:
                    result = parser.procedural_timeline.extract_commission_officials_met(soup)
                    assert result == expected, (
                        f"Failed for test case: {test_id}\n"
                        f"Expected: {expected}\n"
                        f"Got: {result}\n"
                        f"HTML:\n{html}"
                    )
                except Exception as e:
                    # Re-raise with HTML context
                    raise AssertionError(
                        f"Error in test case: {test_id}\n"
                        f"Expected: {expected}\n"
                        f"HTML:\n{html}\n"
                        f"Error: {str(e)}\n"
                    ) from e

    
    def test_parliament_hearing_date(self):
        """Test extraction of Parliament hearing date."""
        
        test_cases = [
            # Test case 1: Standard format with full month name
            (
                """
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>A public hearing took place at the European Parliament on 24 January 2023.</p>
                """,
                "24-01-2023",
                "standard_full_month",
                False
            ),
            # Test case 2: Slash date format
            (
                """
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>A public hearing took place at the European Parliament on 17/02/2014.</p>
                """,
                "17-02-2014",
                "slash_date_format",
                False
            ),
            # Test case 3: New format - "The presentation of this initiative..."
            (
                """
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>The presentation of this initiative in a public hearing at the European Parliament took place on 25 June 2025.</p>
                """,
                "25-06-2025",
                "new_presentation_format",
                False
            ),
            # Test case 4: Single digit day
            (
                """
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>A public hearing took place at the European Parliament on 5 April 2023.</p>
                """,
                "05-04-2023",
                "single_digit_day",
                False
            ),
            # Test case 5: Case insensitive month name
            (
                """
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>A public hearing took place at the European Parliament on 10 OCTOBER 2023.</p>
                """,
                "10-10-2023",
                "uppercase_month",
                False
            ),
            # Test case 6: Mixed case
            (
                """
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>A public hearing took place at the European Parliament on 15 February 2020.</p>
                """,
                "15-02-2020",
                "mixed_case_month",
                False
            ),
            # Test case 7: Slash format with new phrasing
            (
                """
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>The presentation of this initiative in a public hearing at the European Parliament took place on 11/05/2015.</p>
                """,
                "11-05-2015",
                "new_format_slash",
                False
            ),
            # Test case 8: Multiple paragraphs, hearing in second paragraph
            (
                """
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>The initiative was submitted on 10 January 2020.</p>
                <p>A public hearing took place at the European Parliament on 15 October 2020.</p>
                """,
                "15-10-2020",
                "multiple_paragraphs",
                False
            ),
            # Test case 9: No hearing date found (raises error)
            (
                """
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>The initiative was submitted to the Commission on 15 May 2024.</p>
                <p>The organisers met with Commission officials on 20 June 2024.</p>
                """,
                None,
                "no_hearing_date",
                True
            ),
            # Test case 11: No submission section (raises error)
            (
                """
                <h2 id="Other-section">Other section</h2>
                <p>Some content here.</p>
                """,
                None,
                "no_section",
                True
            ),
        ]
        
        for html, expected, test_id, should_raise in test_cases:
            soup = BeautifulSoup(html, 'html.parser')
            parser = ECIResponseHTMLParser(soup)
            parser.registration_number = "2024/000001"
            
            if should_raise:
                # Expect ValueError to be raised
                with pytest.raises(ValueError) as exc_info:
                    parser.parliament_activity.extract_parliament_hearing_date(soup)
                assert "parliament hearing date" in str(exc_info.value).lower(), f"Failed for test case: {test_id}"
            else:
                # Normal case - should return expected value
                try:
                    result = parser.parliament_activity.extract_parliament_hearing_date(soup)
                    assert result == expected, (
                        f"Failed for test case: {test_id}\n"
                        f"Expected: {expected}\n"
                        f"Got: {result}\n"
                        f"HTML:\n{html}"
                    )
                except Exception as e:
                    # Re-raise with HTML context
                    raise AssertionError(
                        f"Error in test case: {test_id}\n"
                        f"Expected: {expected}\n"
                        f"HTML:\n{html}\n"
                        f"Error: {str(e)}\n"
                    ) from e
    
    def test_parliament_hearing_video_urls(self):
        """Test extraction of Parliament hearing video URLs (as dict)."""

        test_cases = [
            # Test case 1: Link wrapping "public hearing" text
            (
                """
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>A <a href="http://www.europarl.europa.eu/news/en/news-room/20140210IPR35552/hearing">public hearing</a> took place at the European Parliament on 17 February 2014.</p>
                """,
                {"public hearing": "http://www.europarl.europa.eu/news/en/news-room/20140210IPR35552/hearing"},
                "link_wrapping_public_hearing",
                False
            ),
            # Test case 2: "See recording" pattern
            (
                """
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>A public hearing took place at the European Parliament on 24 January 2023. See <a href="https://multimedia.europarl.europa.eu/video/recording123">recording</a>.</p>
                """,
                {"recording": "https://multimedia.europarl.europa.eu/video/recording123"},
                "see_recording_pattern",
                False
            ),
            # Test case 3: "Watch the recording" pattern
            (
                """
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>The presentation of this initiative in a public hearing at the European Parliament took place on 25 June 2025. Watch the <a href="https://multimedia.europarl.europa.eu/video/recording456">recording</a>.</p>
                """,
                {"recording": "https://multimedia.europarl.europa.eu/video/recording456"},
                "watch_recording_pattern",
                False
            ),
            # Test case 4: Multiple links (recording + extracts)
            (
                """
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>A&nbsp;public hearing&nbsp;took place at the European Parliament on 25 May 2023. See
                <a href="https://multimedia.europarl.europa.eu/en/webstreaming/peti-envi-agri-committee-meeting_20230525-0900-COMMITTEE-ENVI-AGRI-PETI">recording</a>
                and
                <a href="https://multimedia.europarl.europa.eu/en/video/extracts_I241450">extracts</a>.</p>
                """,
                {
                    "recording": "https://multimedia.europarl.europa.eu/en/webstreaming/peti-envi-agri-committee-meeting_20230525-0900-COMMITTEE-ENVI-AGRI-PETI",
                    "extracts": "https://multimedia.europarl.europa.eu/en/video/extracts_I241450"
                },
                "multiple_links_recording_extracts",
                False
            ),
            # Test case 5: Error when no relevant link
            (
                """
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>The initiative was submitted to the Commission on 15 May 2024.</p>
                """,
                None,
                "no_links",
                True
            ),
        ]

        for html, expected, test_id, should_raise in test_cases:
            soup = BeautifulSoup(html, "html.parser")
            parser = ECIResponseHTMLParser(soup)
            parser.registration_number = "2024/000001"

            if should_raise:
                with pytest.raises(ValueError):
                    parser.parliament_activity.extract_parliament_hearing_video_urls(soup)
            else:
                result = parser.parliament_activity.extract_parliament_hearing_video_urls(soup)
                assert result == expected, (
                    f"Failed for test case: {test_id}\n"
                    f"Expected: {expected}\n"
                    f"Got: {result}\n"
                    f"HTML:\n{html}"
                )

    def test_plenary_debate_date(self):
        """Test extraction of plenary debate date."""
        
        # Test case 1: Standard format "initiative was debated at the European Parliament's plenary session on"
        html_1 = """
        <html>
            <h2 id="Submission-and-examination">Submission and examination</h2>
            <p>Some other text.</p>
            <p>
                The initiative was debated at the European Parliament's plenary session on 10 June 2021. In the
                <a href="https://example.com">resolution</a>
                adopted on the same day, the European Parliament expressed its support for the initiative.
            </p>
        </html>
        """
        soup_1 = BeautifulSoup(html_1, 'html.parser')
        parser_1 = ECIResponseHTMLParser(soup_1)
        result_1 = parser_1.parliament_activity.extract_plenary_debate_date(soup_1)
        assert result_1 == "10-06-2021"
        
        # Test case 2: Alternative format "A debate on this initiative was held"
        html_2 = """
        <html>
            <h2 id="Submission-and-examination">Submission and examination</h2>
            <p>
                A debate on this initiative was held in the plenary session of the&nbsp;European Parliament on 10 July 2025. See the
                <a href="https://example.com">video recording</a>.
            </p>
        </html>
        """
        soup_2 = BeautifulSoup(html_2, 'html.parser')
        parser_2 = ECIResponseHTMLParser(soup_2)
        result_2 = parser_2.parliament_activity.extract_plenary_debate_date(soup_2)
        assert result_2 == "10-07-2025"
        
        # Test case 3: With various month names
        html_3 = """
        <html>
            <h2 id="Submission-and-examination">Submission and examination</h2>
            <p>
                The initiative was debated at the European Parliament's plenary session on 16 March 2023.
                See <a href="https://example.com">recording</a>.
            </p>
        </html>
        """
        soup_3 = BeautifulSoup(html_3, 'html.parser')
        parser_3 = ECIResponseHTMLParser(soup_3)
        result_3 = parser_3.parliament_activity.extract_plenary_debate_date(soup_3)
        assert result_3 == "16-03-2023"
        
        # Test case 4: Single digit day
        html_4 = """
        <html>
            <h2 id="Submission-and-examination">Submission and examination</h2>
            <p>
                The initiative was debated at the European Parliament's plenary session on 5 April 2023.
            </p>
        </html>
        """
        soup_4 = BeautifulSoup(html_4, 'html.parser')
        parser_4 = ECIResponseHTMLParser(soup_4)
        result_4 = parser_4.parliament_activity.extract_plenary_debate_date(soup_4)
        assert result_4 == "05-04-2023"
        
        # Test case 5: No plenary debate date (older initiatives from 2017 and earlier)
        html_5 = """
        <html>
            <h2 id="Submission-and-examination">Submission and examination</h2>
            <p>
                The organisers met with Commission Vice-President on 17 February 2014.
                A public hearing took place at the European Parliament on 17 February 2014.
            </p>
        </html>
        """
        soup_5 = BeautifulSoup(html_5, 'html.parser')
        parser_5 = ECIResponseHTMLParser(soup_5)
        result_5 = parser_5.parliament_activity.extract_plenary_debate_date(soup_5)
        assert result_5 is None
        
        # Test case 6: Slash format (if exists)
        html_6 = """
        <html>
            <h2 id="Submission-and-examination">Submission and examination</h2>
            <p>
                The initiative was debated at the European Parliament's plenary session on 14/12/2020.
            </p>
        </html>
        """
        soup_6 = BeautifulSoup(html_6, 'html.parser')
        parser_6 = ECIResponseHTMLParser(soup_6)
        result_6 = parser_6.parliament_activity.extract_plenary_debate_date(soup_6)
        assert result_6 == "14-12-2020"

    def test_plenary_debate_video_urls(self):
        """Test extraction of plenary debate recording URLs."""
        
        # Test case 1: Single recording link
        html_1 = """
        <html>
            <h2 id="Submission-and-examination">Submission and examination</h2>
            <p>
                The initiative was debated at the European Parliament's plenary session on 11 May 2023. See
                <a href="https://multimedia.europarl.europa.eu/en/video/example">recording</a>.
            </p>
        </html>
        """
        soup_1 = BeautifulSoup(html_1, 'html.parser')
        parser_1 = ECIResponseHTMLParser(soup_1)
        result_1 = parser_1.parliament_activity.extract_plenary_debate_video_urls(soup_1)
        expected_1 = json.dumps({"recording": "https://multimedia.europarl.europa.eu/en/video/example"})
        assert result_1 == expected_1
        
        # Test case 2: Multiple links (resolution and press release)
        html_2 = """
        <html>
            <h2 id="Submission-and-examination">Submission and examination</h2>
            <p>
                The initiative was debated at the European Parliament's plenary session on 10 June 2021. In the
                <a href="https://www.europarl.europa.eu/doceo/document/TA-9-2021-0295_EN.html">resolution</a>
                adopted on the same day, the European Parliament expressed its support for the initiative. See European Parliament's
                <a href="https://www.europarl.europa.eu/news/en/press-room/20210604IPR05532/meps-endorse-eu-citizens-call-for-gradual-end-to-caged-farming">press release</a>.
            </p>
        </html>
        """
        soup_2 = BeautifulSoup(html_2, 'html.parser')
        parser_2 = ECIResponseHTMLParser(soup_2)
        result_2 = parser_2.parliament_activity.extract_plenary_debate_video_urls(soup_2)
        expected_2 = json.dumps({
            "resolution": "https://www.europarl.europa.eu/doceo/document/TA-9-2021-0295_EN.html",
            "press release": "https://www.europarl.europa.eu/news/en/press-room/20210604IPR05532/meps-endorse-eu-citizens-call-for-gradual-end-to-caged-farming"
        })
        assert result_2 == expected_2
        
        # Test case 3: Alternative format with video recording link
        html_3 = """
        <html>
            <h2 id="Submission-and-examination">Submission and examination</h2>
            <p>
                A debate on this initiative was held in the plenary session of the&nbsp;European Parliament on 10 July 2025. See the
                <a href="https://www.europarl.europa.eu/plenary/en/vod.html?mode=chapter">video recording</a>.
            </p>
        </html>
        """
        soup_3 = BeautifulSoup(html_3, 'html.parser')
        parser_3 = ECIResponseHTMLParser(soup_3)
        result_3 = parser_3.parliament_activity.extract_plenary_debate_video_urls(soup_3)
        expected_3 = json.dumps({"video recording": "https://www.europarl.europa.eu/plenary/en/vod.html?mode=chapter"})
        assert result_3 == expected_3
        
        # Test case 4: Multiple links with "part 1 and part 2"
        html_4 = """
        <html>
            <h2 id="Submission-and-examination">Submission and examination</h2>
            <p>
                The initiative was debated at the European Parliament's plenary session on 19 October 2023. See recording (
                <a href="https://example.com/part1">part 1</a> and
                <a href="https://example.com/part2">part 2</a>).
            </p>
        </html>
        """
        soup_4 = BeautifulSoup(html_4, 'html.parser')
        parser_4 = ECIResponseHTMLParser(soup_4)
        result_4 = parser_4.parliament_activity.extract_plenary_debate_video_urls(soup_4)
        expected_4 = json.dumps({
            "part 1": "https://example.com/part1",
            "part 2": "https://example.com/part2"
        })
        assert result_4 == expected_4
        
        # Test case 5: No links in debate paragraph
        html_5 = """
        <html>
            <h2 id="Submission-and-examination">Submission and examination</h2>
            <p>
                The initiative was debated at the European Parliament's plenary session on 14 December 2020.
            </p>
        </html>
        """
        soup_5 = BeautifulSoup(html_5, 'html.parser')
        parser_5 = ECIResponseHTMLParser(soup_5)
        result_5 = parser_5.parliament_activity.extract_plenary_debate_video_urls(soup_5)
        assert result_5 is None
        
        # Test case 6: No plenary debate paragraph at all
        html_6 = """
        <html>
            <h2 id="Submission-and-examination">Submission and examination</h2>
            <p>
                The organisers met with Commission Vice-President on 17 February 2014.
            </p>
        </html>
        """
        soup_6 = BeautifulSoup(html_6, 'html.parser')
        parser_6 = ECIResponseHTMLParser(soup_6)
        result_6 = parser_6.parliament_activity.extract_plenary_debate_video_urls(soup_6)
        assert result_6 is None

    def test_official_communication_adoption_date(self):
        """Test extraction of Commission communication date."""
        
        # Test case 1: Text format with full month name
        html_1 = """
        <html>
            <h2 id="Submission-and-examination">Submission and examination</h2>
            <p>
                The Commission adopted a Communication on 19 March 2014 setting out the actions it intends to take in response to the initiative.
                See <a href="https://example.com">press release</a>.
            </p>
        </html>
        """
        soup_1 = BeautifulSoup(html_1, 'html.parser')
        parser_1 = ECIResponseHTMLParser(soup_1)
        result_1 = parser_1.commission_response.extract_official_communication_adoption_date(soup_1)
        assert result_1 == "19-03-2014"
        
        # Test case 2: Slash format
        html_2 = """
        <html>
            <h2 id="Submission-and-examination">Submission and examination</h2>
            <p>
                The Commission adopted a Communication on 12/12/2017 setting out the actions it intends to take in response to the initiative.
            </p>
        </html>
        """
        soup_2 = BeautifulSoup(html_2, 'html.parser')
        parser_2 = ECIResponseHTMLParser(soup_2)
        result_2 = parser_2.commission_response.extract_official_communication_adoption_date(soup_2)
        assert result_2 == "12-12-2017"
        
        # Test case 3: Different month name
        html_3 = """
        <html>
            <h2 id="Submission-and-examination">Submission and examination</h2>
            <p>
                The Commission adopted a Communication on 30 June 2021 setting out the actions it intends to take in response to the initiative 'End the Cage Age'.
                See <a href="https://example.com">press release</a> and <a href="https://example.com">Questions & Answers</a>.
            </p>
        </html>
        """
        soup_3 = BeautifulSoup(html_3, 'html.parser')
        parser_3 = ECIResponseHTMLParser(soup_3)
        result_3 = parser_3.commission_response.extract_official_communication_adoption_date(soup_3)
        assert result_3 == "30-06-2021"
        
        # Test case 4: Single digit day
        html_4 = """
        <html>
            <h2 id="Submission-and-examination">Submission and examination</h2>
            <p>
                The Commission adopted a Communication on 5 April 2023 setting out its response to the initiative.
            </p>
        </html>
        """
        soup_4 = BeautifulSoup(html_4, 'html.parser')
        parser_4 = ECIResponseHTMLParser(soup_4)
        result_4 = parser_4.commission_response.extract_official_communication_adoption_date(soup_4)
        assert result_4 == "05-04-2023"
        
        # Test case 5: Recent format with "its response"
        html_5 = """
        <html>
            <h2 id="Submission-and-examination">Submission and examination</h2>
            <p>
                The Commission adopted a Communication on 3 September 2025 setting out its response to this initiative.
                See the <a href="https://example.com">Commission's news</a>.
            </p>
        </html>
        """
        soup_5 = BeautifulSoup(html_5, 'html.parser')
        parser_5 = ECIResponseHTMLParser(soup_5)
        result_5 = parser_5.commission_response.extract_official_communication_adoption_date(soup_5)
        assert result_5 == "03-09-2025"
        
        # Test case 6: No Commission communication (some older initiatives)
        html_6 = """
        <html>
            <h2 id="Submission-and-examination">Submission and examination</h2>
            <p>
                The organisers met with Commission Vice-President on 17 February 2014.
                A public hearing took place at the European Parliament on 17 February 2014.
            </p>
        </html>
        """
        soup_6 = BeautifulSoup(html_6, 'html.parser')
        parser_6 = ECIResponseHTMLParser(soup_6)
        result_6 = parser_6.commission_response.extract_official_communication_adoption_date(soup_6)
        assert result_6 is None

    
    def test_official_communication_document_urls(self):
        """Test extraction of Commission Communication PDF URL."""
        
        # Test case 1: Single press release link
        html_1 = """
        <html>
            <h2 id="Submission-and-examination">Submission and examination</h2>
            <p>
                The Commission adopted a Communication on 19 March 2014 setting out the actions it intends to take in response to the initiative.
                See <a href="http://europa.eu/rapid/press-release_IP-14-277_en.htm">press release</a>.
            </p>
        </html>
        """
        soup_1 = BeautifulSoup(html_1, 'html.parser')
        parser_1 = ECIResponseHTMLParser(soup_1)
        result_1 = parser_1.commission_response.extract_official_communication_document_urls(soup_1)
        expected_1 = json.dumps({"press release": "http://europa.eu/rapid/press-release_IP-14-277_en.htm"})
        assert result_1 == expected_1
        
        # Test case 2: Multiple links (press release and Q&A)
        html_2 = """
        <html>
            <h2 id="Submission-and-examination">Submission and examination</h2>
            <p>
                The Commission adopted a Communication on 30 June 2021 setting out the actions it intends to take in response to the initiative 'End the Cage Age'.
                See <a href="https://ec.europa.eu/commission/presscorner/detail/en/ip_21_3297">press release</a> and 
                <a href="https://ec.europa.eu/commission/presscorner/detail/en/qanda_21_3298">Questions & Answers.</a>
            </p>
        </html>
        """
        soup_2 = BeautifulSoup(html_2, 'html.parser')
        parser_2 = ECIResponseHTMLParser(soup_2)
        result_2 = parser_2.commission_response.extract_official_communication_document_urls(soup_2)
        expected_2 = json.dumps({
            "press release": "https://ec.europa.eu/commission/presscorner/detail/en/ip_21_3297",
            "Questions & Answers.": "https://ec.europa.eu/commission/presscorner/detail/en/qanda_21_3298"
        })
        assert result_2 == expected_2
        
        # Test case 3: Commission's news link
        html_3 = """
        <html>
            <h2 id="Submission-and-examination">Submission and examination</h2>
            <p>
                The Commission adopted a Communication on 3 September 2025 setting out its response to this initiative.
                See the <a href="https://ec.europa.eu/commission/presscorner/detail/en/mex_25_2018">Commission's news</a>.
            </p>
        </html>
        """
        soup_3 = BeautifulSoup(html_3, 'html.parser')
        parser_3 = ECIResponseHTMLParser(soup_3)
        result_3 = parser_3.commission_response.extract_official_communication_document_urls(soup_3)
        expected_3 = json.dumps({"Commission's news": "https://ec.europa.eu/commission/presscorner/detail/en/mex_25_2018"})
        assert result_3 == expected_3
        
        # Test case 4: Filter out initiative name link (old URL format) - keep press release
        html_4 = """
        <html>
            <h2 id="Submission-and-examination">Submission and examination</h2>
            <p>
                The Commission adopted a Communication on 12/12/2017 setting out the actions it intends to take in response to the initiative
                <a href="http://ec.citizens-initiative.europa.eu/public/initiatives/successful/details/2017/000002">
                Ban glyphosate and protect people and the environment from toxic pesticides
                </a>. See
                <a href="http://europa.eu/rapid/press-release_IP-17-5191_en.htm">press release</a>.
            </p>
        </html>
        """
        soup_4 = BeautifulSoup(html_4, 'html.parser')
        parser_4 = ECIResponseHTMLParser(soup_4)
        result_4 = parser_4.commission_response.extract_official_communication_document_urls(soup_4)
        expected_4 = json.dumps({"press release": "http://europa.eu/rapid/press-release_IP-17-5191_en.htm"})
        assert result_4 == expected_4
        
        # Test case 5: Filter out initiative name link (new URL format) - keep press release
        html_5 = """
        <html>
            <h2 id="Submission-and-examination">Submission and examination</h2>
            <p>
                The Commission adopted a Communication on 14 January 2021 setting out how existing and recently adopted EU legislation supports the different aspects of the
                <a href="https://citizens-initiative.europa.eu/initiatives/details/2017/000004_en">Minority SafePack</a>
                Initiative. The reply outlined further follow-up actions. See
                <a href="https://ec.europa.eu/commission/presscorner/detail/en/ip_21_81">press release</a>.
            </p>
        </html>
        """
        soup_5 = BeautifulSoup(html_5, 'html.parser')
        parser_5 = ECIResponseHTMLParser(soup_5)
        result_5 = parser_5.commission_response.extract_official_communication_document_urls(soup_5)
        expected_5 = json.dumps({"press release": "https://ec.europa.eu/commission/presscorner/detail/en/ip_21_81"})
        assert result_5 == expected_5
        
        # Test case 6: Press release and questions and answers (lowercase)
        html_6 = """
        <html>
            <h2 id="Submission-and-examination">Submission and examination</h2>
            <p>
                The Commission adopted a Communication on 7 December 2023 setting out its response to the initiative 'Fur Free Europe'.
                See <a href="https://ec.europa.eu/commission/presscorner/detail/en/ip_23_6251">press release</a> and 
                <a href="https://ec.europa.eu/commission/presscorner/detail/en/QANDA_23_6254">questions and answers</a>.
            </p>
        </html>
        """
        soup_6 = BeautifulSoup(html_6, 'html.parser')
        parser_6 = ECIResponseHTMLParser(soup_6)
        result_6 = parser_6.commission_response.extract_official_communication_document_urls(soup_6)
        expected_6 = json.dumps({
            "press release": "https://ec.europa.eu/commission/presscorner/detail/en/ip_23_6251",
            "questions and answers": "https://ec.europa.eu/commission/presscorner/detail/en/QANDA_23_6254"
        })
        assert result_6 == expected_6
        
        # Test case 7: No links in commission paragraph
        html_7 = """
        <html>
            <h2 id="Submission-and-examination">Submission and examination</h2>
            <p>
                The Commission adopted a Communication on 12/12/2017 setting out the actions it intends to take in response to the initiative.
            </p>
        </html>
        """
        soup_7 = BeautifulSoup(html_7, 'html.parser')
        parser_7 = ECIResponseHTMLParser(soup_7)
        result_7 = parser_7.commission_response.extract_official_communication_document_urls(soup_7)
        assert result_7 is None
        
        # Test case 8: No commission communication paragraph
        html_8 = """
        <html>
            <h2 id="Submission-and-examination">Submission and examination</h2>
            <p>
                The organisers met with Commission Vice-President on 17 February 2014.
            </p>
        </html>
        """
        soup_8 = BeautifulSoup(html_8, 'html.parser')
        parser_8 = ECIResponseHTMLParser(soup_8)
        result_8 = parser_8.commission_response.extract_official_communication_document_urls(soup_8)
        assert result_8 is None
        
        # Test case 9: Only initiative detail link (should return None after filtering)
        html_9 = """
        <html>
            <h2 id="Submission-and-examination">Submission and examination</h2>
            <p>
                The Commission adopted a Communication on 19 March 2014 about
                <a href="https://citizens-initiative.europa.eu/initiatives/details/2012/000003_en">Right2Water</a>.
            </p>
        </html>
        """
        soup_9 = BeautifulSoup(html_9, 'html.parser')
        parser_9 = ECIResponseHTMLParser(soup_9)
        result_9 = parser_9.commission_response.extract_official_communication_document_urls(soup_9)
        assert result_9 is None


class TestCommissionResponseContent:
    """Tests for Commission response content extraction."""
    
    @classmethod
    def setup_class(cls):
        """Setup parser instance."""
        logger = ResponsesExtractorLogger().setup()
        cls.parser = ECIResponseHTMLParser(logger=logger)
    
    def test_commission_answer_text(self):
        """Test extraction of main conclusions from Communication."""
        
        # Test case 1: Standard format with Decision date and official documents
        html_1 = """
        <html>
            <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
            <p>Decision date: 19/03/2014</p>
            <p>Official documents related to the decision:</p>
            <ul>
                <li><a href="https://ec.europa.eu/transparency/documents-register/detail?ref=COM(2014)177&lang=en">Communication</a></li>
                <li><a href="https://ec.europa.eu/transparency/documents-register/detail?ref=COM(2014)177&lang=en">Annex</a></li>
            </ul>
            <p><strong>Main conclusions of the Communication</strong>:</p>
            <p>The Commission committed, in particular, to taking the following actions:</p>
            <ul>
                <li>reinforcing implementation of EU water quality legislation;</li>
                <li>launching an EU-wide public consultation on the Drinking Water Directive;</li>
            </ul>
            <h2 id="Follow-up">Follow-up</h2>
            <p>Follow-up content here.</p>
        </html>
        """
        
        soup_1 = BeautifulSoup(html_1, 'html.parser')
        parser_1 = ECIResponseHTMLParser(soup_1)
        parser_1.registration_number = "2012/000003"
        
        result_1 = parser_1.commission_response.extract_commission_answer_text(soup_1)
        
        # Should include decision date, official documents, and main conclusions
        assert "Decision date: 19/03/2014" in result_1
        assert "Official documents" in result_1
        assert "[Communication]" in result_1
        assert "Main conclusions" in result_1
        assert "reinforcing implementation of EU water quality legislation" in result_1
        # Should NOT include Follow-up content
        assert "Follow-up content here" not in result_1
        
        # Test case 2: Format with Main conclusions paragraph only
        html_2 = """
        <html>
            <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
            <p>Decision date: 03/06/2015</p>
            <p>Official documents related to the decision:</p>
            <ul>
                <li><a href="https://ec.europa.eu/transparency/documents-register/detail?ref=C(2015)3773&lang=en">Communication</a></li>
                <li><a href="https://ec.europa.eu/transparency/documents-register/detail?ref=C(2015)3773&lang=en">Annex</a></li>
            </ul>
            <p><strong>Main conclusions of the Communication</strong>:</p>
            <p>While the Commission does share the conviction that animal testing should be phased out in Europe, 
            its approach for achieving that objective differs from the one proposed in this Citizens' Initiative.</p>
            <p>The Commission considers that the Directive on the protection of animals used for scientific purposes 
            (Directive 2010/63/EU), which the Initiative seeks to repeal, is the right legislation to achieve 
            the underlying objectives of the Initiative.</p>
            <h2 id="Follow-up">Follow-up</h2>
        </html>
        """
        
        soup_2 = BeautifulSoup(html_2, 'html.parser')
        parser_2 = ECIResponseHTMLParser(soup_2)
        parser_2.registration_number = "2012/000007"
        
        result_2 = parser_2.commission_response.extract_commission_answer_text(soup_2)
        
        assert "Decision date: 03/06/2015" in result_2
        assert "Main conclusions of the Communication" in result_2
        assert "animal testing should be phased out" in result_2
        assert "Directive 2010/63/EU" in result_2
        
        # Test case 3: Recent format without Decision date, with direct conclusions
        html_3 = """
        <html>
            <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
            <p>Official documents:</p>
            <ul>
                <li><a href="https://ec.europa.eu/transparency/documents-register/detail?ref=C(2017)8414">Communication</a></li>
                <li><a href="https://ec.europa.eu/transparency/documents-register/api/files/C(2017)8414_1/de00000000208522?rendition=false">Annex</a></li>
            </ul>
            <p><strong>Main conclusions of the Communication</strong>:</p>
            <p>On the first aim, to 'ban glyphosate-based herbicides', the Commission concluded that there are 
            neither scientific nor legal grounds to justify a ban of glyphosate, and will not make a legislative 
            proposal to that effect.</p>
            <p>On the second aim, to "ensure that the scientific evaluation of pesticides for EU regulatory 
            approval is based only on published studies", the Commission committed to come forward with a 
            legislative proposal by May 2018.</p>
            <h2 id="Follow-up">Follow-up</h2>
        </html>
        """
        
        soup_3 = BeautifulSoup(html_3, 'html.parser')
        parser_3 = ECIResponseHTMLParser(soup_3)
        parser_3.registration_number = "2017/000002"
        
        result_3 = parser_3.commission_response.extract_commission_answer_text(soup_3)
        
        assert "Official documents" in result_3
        assert "glyphosate-based herbicides" in result_3
        assert "legislative proposal by May 2018" in result_3
        
        # Test case 4: Format with Communication link inline
        html_4 = """
        <html>
            <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
            <p>Main conclusions of the <a href="https://ec.europa.eu/transparency/documents-register/detail?ref=C(2021)4747&lang=en">Communication</a>:</p>
            <p>In its response to the ECI, the Commission communicated its intention to table a legislative 
            proposal, by the end of 2023, to phase out, and finally prohibit, the use of cages for all animals 
            mentioned in the ECI.</p>
            <h2 id="Follow-up">Follow-up</h2>
        </html>
        """
        
        soup_4 = BeautifulSoup(html_4, 'html.parser')
        parser_4 = ECIResponseHTMLParser(soup_4)
        parser_4.registration_number = "2018/000004"
        
        result_4 = parser_4.commission_response.extract_commission_answer_text(soup_4)
        result_4 = " ".join(result_4.split())
        
        assert "Main conclusions" in result_4
        assert "[Communication]" in result_4
        assert "legislative proposal" in result_4
        assert "by the end of 2023" in result_4
        
        # Test case 5: Excludes factsheet downloads (ecl-file divs)
        html_5 = """
        <html>
            <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
            <div class="ecl-file ecl-file--has-translation">
                <div class="ecl-file__container">
                    <a href="https://citizens-initiative.europa.eu/sites/default/files/factsheet.pdf" 
                       class="ecl-link ecl-file__download">
                        Factsheet – Successful Initiatives – Save bees and farmers English (4.89 MB - PDF)
                        <span>Download</span>
                    </a>
                </div>
                <div class="ecl-file__translation-container">
                    <button class="ecl-file__translation-toggle">Available translations (23)</button>
                    <ul class="ecl-file__translation-list">
                        <li class="ecl-file__translation-item">
                            <a href="https://example.com/bg.pdf">български (1.27 MB - PDF)</a>
                        </li>
                    </ul>
                </div>
            </div>
            <p>In its response to the ECI, the Commission welcomes the initiative.</p>
            <h2 id="Follow-up">Follow-up</h2>
        </html>
        """
        
        soup_5 = BeautifulSoup(html_5, 'html.parser')
        parser_5 = ECIResponseHTMLParser(soup_5)
        parser_5.registration_number = "2019/000016"
        
        result_5 = parser_5.commission_response.extract_commission_answer_text(soup_5)
        
        # Should include the Commission's response
        assert "Commission welcomes the initiative" in result_5
        # Should NOT include factsheet download information
        assert "Factsheet" not in result_5
        assert "Available translations" not in result_5
        assert "български" not in result_5
        assert "Download" not in result_5
        
        # Test case 6: Error when section not found
        html_6 = """
        <html>
            <h2 id="Submission-and-examination">Submission and examination</h2>
            <p>Some content here.</p>
            <h2 id="Follow-up">Follow-up</h2>
        </html>
        """
        
        soup_6 = BeautifulSoup(html_6, 'html.parser')
        parser_6 = ECIResponseHTMLParser(soup_6)
        parser_6.registration_number = "2099/999999"
        
        with pytest.raises(ValueError, match="Could not find 'Answer of the European Commission' section for 2099/999999"):
            parser_6.commission_response.extract_commission_answer_text(soup_6)
        
        # Test case 7: Error when section exists but has no content
        html_7 = """
        <html>
            <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
            <h2 id="Follow-up">Follow-up</h2>
        </html>
        """
        
        soup_7 = BeautifulSoup(html_7, 'html.parser')
        parser_7 = ECIResponseHTMLParser(soup_7)
        parser_7.registration_number = "2099/999998"
        
        with pytest.raises(ValueError, match="No content found in 'Answer of the European Commission' section for 2099/999998"):
            parser_7.commission_response.extract_commission_answer_text(soup_7)
        
        # Test case 8: Multiple paragraphs with links preserved in markdown format
        html_8 = """
        <html>
            <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
            <p>The Commission welcomes this initiative and acknowledges its importance.</p>
            <p>Since 2019, the Commission has been engaged in intensive work under the 
            <a href="https://ec.europa.eu/info/strategy/priorities-2019-2024/european-green-deal_en">European Green Deal</a> 
            to ensure the sustainability of food systems.</p>
            <p>The <a href="https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A52022PC0305">proposal for a regulation</a> 
            sets out an ambitious path to reduce chemical pesticides by 50% by 2030.</p>
            <h2 id="Follow-up">Follow-up</h2>
        </html>
        """
        
        soup_8 = BeautifulSoup(html_8, 'html.parser')
        parser_8 = ECIResponseHTMLParser(soup_8)
        parser_8.registration_number = "2019/000016"
        
        result_8 = parser_8.commission_response.extract_commission_answer_text(soup_8)
        
        # Check that links are preserved in markdown format
        assert "[European Green Deal](https://ec.europa.eu/info/strategy/priorities-2019-2024/european-green-deal_en)" in result_8
        assert "[proposal for a regulation](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A52022PC0305)" in result_8
        assert "reduce chemical pesticides by 50% by 2030" in result_8

    def test_highest_status_reached(self):
        """Test extraction of highest status reached by initiative."""
        
        # Test case 1: applicable - Law became applicable
        html_1 = """
        <html>
            <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
            <h2 id="Follow-up">Follow-up</h2>
            <p>Legislative action:</p>
            <p>The revised Drinking Water Directive entered into force on 12 January 2021. 
            Member States had until 12 January 2023 to transpose it into national legislation.</p>
            <p>The Regulation based on this proposal entered into force in June 2020. 
            The new rules became applicable from 26 June 2023.</p>
        </html>
        """
        
        soup_1 = BeautifulSoup(html_1, 'html.parser')
        extractor_1 = LegislativeOutcomeExtractor(registration_number="2012/000003")
        result_1 = extractor_1.extract_highest_status_reached(soup_1)
        assert result_1 == "Law Active"
        
        # Test case 2: committed - Commission committed to legislative proposal
        html_2 = """
        <html>
            <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
            <p>Main conclusions of the Communication:</p>
            <p>In its response to the ECI, the Commission communicated its intention to table a 
            legislative proposal, by the end of 2023, to phase out, and finally prohibit, 
            the use of cages for all animals mentioned in the ECI.</p>
        </html>
        """
        
        soup_2 = BeautifulSoup(html_2, 'html.parser')
        extractor_2 = LegislativeOutcomeExtractor(registration_number="2018/000004")
        result_2 = extractor_2.extract_highest_status_reached(soup_2)
        assert result_2 == "Law Promised"
        
        # Test case 3: assessment_pending - EFSA scientific opinion requested
        html_3 = """
        <html>
            <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
            <p>Main conclusions of the Communication:</p>
            <p>The Commission has tasked the European Food Safety Authority (EFSA) to provide 
            a scientific opinion on the welfare of animals farmed for fur.</p>
            <p>Building further on this scientific input, and on an assessment of economic and 
            social impacts, the Commission will then communicate, by March 2026, on the most 
            appropriate action.</p>
        </html>
        """
        
        soup_3 = BeautifulSoup(html_3, 'html.parser')
        extractor_3 = LegislativeOutcomeExtractor(registration_number="2022/000002")
        result_3 = extractor_3.extract_highest_status_reached(soup_3)
        assert result_3 == "Being Studied"
        
        # Test case 4: roadmap_development - Roadmap being developed
        html_4 = """
        <html>
            <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
            <p>Main conclusions of the Communication:</p>
            <p>Transform EU chemicals legislation: The Commission will work together with all 
            relevant parties on a roadmap towards chemical safety assessments that are free from 
            animal testing. The roadmap will serve as a guiding framework for future actions and 
            initiatives aimed at reducing and ultimately eliminating animal testing in the context 
            of chemicals legislation within the European Union.</p>
        </html>
        """
        
        soup_4 = BeautifulSoup(html_4, 'html.parser')
        extractor_4 = LegislativeOutcomeExtractor(registration_number="2021/000006")
        result_4 = extractor_4.extract_highest_status_reached(soup_4)
        assert result_4 == "Action Plan Created"
        
        # Test case 5: rejected_already_covered - Rejected due to existing legislation
        html_5 = """
        <html>
            <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
            <p>Decision date: 28/05/2014</p>
            <h2 id="Follow-up">Follow-up</h2>
            <p>In the Communication adopted on 28/05/2014, the Commission explains that it has 
            decided not to submit a legislative proposal, given that Member States and the European 
            Parliament had only recently discussed and decided EU policy in this regard. The Commission 
            has concluded that the existing funding framework, which had been recently debated and 
            agreed by EU Member States and the European Parliament, is the appropriate one.</p>
        </html>
        """
        
        soup_5 = BeautifulSoup(html_5, 'html.parser')
        extractor_5 = LegislativeOutcomeExtractor(registration_number="2012/000005")
        result_5 = extractor_5.extract_highest_status_reached(soup_5)
        assert result_5 == "Rejected - Already Covered"
        
        # Test case 6: rejected_with_actions - Rejected but with alternative actions
        html_6 = """
        <html>
            <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
            <p>Main conclusions of the Communication:</p>
            <p>While the Commission does share the conviction that animal testing should be phased 
            out in Europe, its approach for achieving that objective differs from the one proposed 
            in this Citizens' Initiative.</p>
            <p>The Commission considers that the Directive on the protection of animals used for 
            scientific purposes (Directive 2010/63/EU), which the Initiative seeks to repeal, is 
            the right legislation to achieve the underlying objectives of the Initiative. Therefore, 
            no repeal of that legislation was proposed.</p>
            <p>Moreover, the Communication sets out four further Commission's actions to be taken 
            towards the goal of phasing out animal testing. The Commission commits to active 
            monitoring of compliance and enforcement of the legislation, and will continue supporting 
            the development and validation of alternative approaches.</p>
        </html>
        """
        
        soup_6 = BeautifulSoup(html_6, 'html.parser')
        extractor_6 = LegislativeOutcomeExtractor(registration_number="2012/000007")
        result_6 = extractor_6.extract_highest_status_reached(soup_6)
        assert result_6 == "Rejected - Alternative Actions"
        
        # Test case 7: rejected - Plain rejection
        html_7 = """
        <html>
            <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
            <p>Main conclusions of the Communication:</p>
            <p>On the first aim, to 'ban glyphosate-based herbicides', the Commission concluded 
            that there are neither scientific nor legal grounds to justify a ban of glyphosate, 
            and will not make a legislative proposal to that effect.</p>
        </html>
        """
        
        soup_7 = BeautifulSoup(html_7, 'html.parser')
        extractor_7 = LegislativeOutcomeExtractor(registration_number="2017/000002")
        result_7 = extractor_7.extract_highest_status_reached(soup_7)
        assert result_7 == "Rejected"
        
        # Test case 8: proposal_pending_adoption - Existing proposals under review
        html_8 = """
        <html>
            <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
            <p>In its response to the ECI, the Commission welcomes the initiative.</p>
            <p>The proposal for a regulation on the sustainable use of plant protection products 
            tabled in June 2022 sets out an ambitious path to reduce the risk and use of chemical 
            pesticides in EU agriculture by 50% by 2030.</p>
            <p>The proposal for a Nature Restoration Law tabled in June 2022 combines an overarching 
            restoration objective for the long-term recovery of nature in the EU's land and sea areas.</p>
            <p>In its reply, the Commission underlined that rather than proposing new legislative acts, 
            the priority is to ensure that the proposals currently being negotiated by the co-legislators 
            are timely adopted and then implemented.</p>
        </html>
        """
        
        soup_8 = BeautifulSoup(html_8, 'html.parser')
        extractor_8 = LegislativeOutcomeExtractor(registration_number="2019/000016")
        result_8 = extractor_8.extract_highest_status_reached(soup_8)
        assert result_8 == "Proposals Under Review"
        
        # Test case 9: adopted - Law approved but not yet applicable
        html_9 = """
        <html>
            <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
            <h2 id="Follow-up">Follow-up</h2>
            <p>Legislative action:</p>
            <p>Following the agreement of the European Parliament on the text (on 27 February 2024), 
            the Council of the EU adopted the regulation on 17 June 2024. It was published in the 
            Official Journal of the EU on 28 July 2024.</p>
        </html>
        """
        
        soup_9 = BeautifulSoup(html_9, 'html.parser')
        extractor_9 = LegislativeOutcomeExtractor(registration_number="2019/000016")
        result_9 = extractor_9.extract_highest_status_reached(soup_9)
        assert result_9 == "Law Approved"
        
        # Test case 10: non_legislative_action - Policy changes only
        html_10 = """
        <html>
            <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
            <p>The Commission committed, in particular, to taking the following actions:</p>
            <ul>
                <li>reinforcing implementation of EU water quality legislation;</li>
                <li>launching an EU-wide public consultation on the Drinking Water Directive;</li>
                <li>improving transparency for urban wastewater and drinking water data management;</li>
                <li>establishing harmonised risk indicators to enable the monitoring of trends.</li>
            </ul>
        </html>
        """
        
        soup_10 = BeautifulSoup(html_10, 'html.parser')
        extractor_10 = LegislativeOutcomeExtractor(registration_number="2012/000003")
        result_10 = extractor_10.extract_highest_status_reached(soup_10)
        assert result_10 == "Policy Changes Only"
        
        # Test case 11: Error when Answer section not found
        html_11 = """
        <html>
            <h2 id="Submission-and-examination">Submission and examination</h2>
            <p>Some content here.</p>
        </html>
        """
        
        soup_11 = BeautifulSoup(html_11, 'html.parser')
        extractor_11 = LegislativeOutcomeExtractor(registration_number="2099/999999")
        
        with pytest.raises(ValueError, match="Could not extract legislative content for initiative 2099/999999"):
            extractor_11.extract_highest_status_reached(soup_11)
                
        # Test case 12: Error when no status patterns match
        html_12 = """
        <html>
            <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
            <p>This is some random text that doesn't match any known status patterns.</p>
            <p>Just some generic information about the initiative.</p>
        </html>
        """
        
        soup_12 = BeautifulSoup(html_12, 'html.parser')
        extractor_12 = LegislativeOutcomeExtractor(registration_number="2099/999998")
        
        with pytest.raises(ValueError, match="Could not determine legislative status for initiative:\n2099/999998"):
            extractor_12.extract_highest_status_reached(soup_12)
        
        # Test case 13: Priority check - applicable takes priority over committed
        html_13 = """
        <html>
            <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
            <p>The Commission communicated its intention to table a legislative proposal by May 2018.</p>
            <h2 id="Follow-up">Follow-up</h2>
            <p>The Regulation was published in the Official Journal of the EU on 6 September 2019. 
            Following its entry into force 20 days after publication, it became applicable 18 months 
            later, i.e. on 27 March 2021.</p>
        </html>
        """
        
        soup_13 = BeautifulSoup(html_13, 'html.parser')
        extractor_13 = LegislativeOutcomeExtractor(registration_number="2017/000002")
        result_13 = extractor_13.extract_highest_status_reached(soup_13)
        assert result_13 == "Law Active"
        
        # Test case 14: Handles "became applicable immediately"
        html_14 = """
        <html>
            <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
            <h2 id="Updates-on-the-Commissions-proposals">Updates on the Commission's proposals</h2>
            <p>Proposal for the Nature Restoration Law: following the agreement of the European 
            Parliament on the text (on 27 February 2024), the Council of the EU adopted the regulation 
            on 17 June 2024. It entered into force on 18 August 2024 (20 days after its publication 
            in the Official Journal of the EU) and became applicable immediately.</p>
        </html>
        """
        
        soup_14 = BeautifulSoup(html_14, 'html.parser')
        extractor_14 = LegislativeOutcomeExtractor(registration_number="2019/000016")
        result_14 = extractor_14.extract_highest_status_reached(soup_14)
        assert result_14 == "Law Active"
        
        # Test case 15: Handles impact assessment (assessment_pending)
        html_15 = """
        <html>
            <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
            <p>The Commission commits to:</p>
            <p>Start without delay preparatory work with a view to launch, by the end of 2023, 
            an impact assessment on the environmental, social and economic consequences of applying 
            the "fins naturally attached" policy to the placing on the EU market of sharks.</p>
        </html>
        """
        
        soup_15 = BeautifulSoup(html_15, 'html.parser')
        extractor_15 = LegislativeOutcomeExtractor(registration_number="2020/000001")
        result_15 = extractor_15.extract_highest_status_reached(soup_15)
        assert result_15 == "Being Studied"
        
    def test_proposal_commitment_stated(self):
        """Test extraction of whether Commission committed to legislative proposal."""
        
        # Test case 1: Clear commitment with deadline
        html_1 = """
        <html>
            <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
            <p>Main conclusions of the Communication:</p>
            <p>In its response to the ECI, the Commission communicated its intention to table a 
            legislative proposal, by the end of 2023, to phase out, and finally prohibit, 
            the use of cages for all animals mentioned in the ECI.</p>
        </html>
        """
        
        soup_1 = BeautifulSoup(html_1, 'html.parser')
        extractor_1 = LegislativeOutcomeExtractor(registration_number="2018/000004")
        result_1 = extractor_1.extract_proposal_commitment_stated(soup_1)
        assert result_1 is True, "Should detect commitment to table legislative proposal"
        
        # Test case 2: Commitment with specific date
        html_2 = """
        <html>
            <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
            <p>On the second aim, the Commission committed to come forward with a 
            legislative proposal by May 2018.</p>
        </html>
        """
        
        soup_2 = BeautifulSoup(html_2, 'html.parser')
        extractor_2 = LegislativeOutcomeExtractor(registration_number="2017/000002")
        result_2 = extractor_2.extract_proposal_commitment_stated(soup_2)
        assert result_2 is True, "Should detect commitment with specific deadline"
        
        # Test case 3: Rejection - no commitment
        html_3 = """
        <html>
            <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
            <p>The Commission concluded that there are neither scientific nor legal grounds 
            to justify a ban of glyphosate, and will not make a legislative proposal to that effect.</p>
        </html>
        """
        
        soup_3 = BeautifulSoup(html_3, 'html.parser')
        extractor_3 = LegislativeOutcomeExtractor(registration_number="2017/000002")
        result_3 = extractor_3.extract_proposal_commitment_stated(soup_3)
        assert result_3 is False, "Should return False when proposal is rejected"
        
        # Test case 4: Already addressed - no new commitment
        html_4 = """
        <html>
            <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
            <p>The Commission has decided not to submit a legislative proposal, given that 
            Member States and the European Parliament had only recently discussed and decided EU 
            policy in this regard. The existing funding framework is the appropriate one.</p>
        </html>
        """
        
        soup_4 = BeautifulSoup(html_4, 'html.parser')
        extractor_4 = LegislativeOutcomeExtractor(registration_number="2012/000005")
        result_4 = extractor_4.extract_proposal_commitment_stated(soup_4)
        assert result_4 is False, "Should return False for existing legislation"
        
        # Test case 5: Non-legislative actions only
        html_5 = """
        <html>
            <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
            <p>The Commission committed, in particular, to taking the following actions:</p>
            <ul>
                <li>reinforcing implementation of EU water quality legislation;</li>
                <li>launching an EU-wide public consultation on the Drinking Water Directive;</li>
                <li>improving transparency for urban wastewater management;</li>
            </ul>
        </html>
        """
        
        soup_5 = BeautifulSoup(html_5, 'html.parser')
        extractor_5 = LegislativeOutcomeExtractor(registration_number="2012/000003")
        result_5 = extractor_5.extract_proposal_commitment_stated(soup_5)
        assert result_5 is False, "Should return False for non-legislative actions without proposal commitment"
        
        # Test case 6: Existing proposals (no new commitment)
        html_6 = """
        <html>
            <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
            <p>The proposal for a regulation on the sustainable use of plant protection products 
            tabled in June 2022 sets out an ambitious path to reduce chemical pesticides.</p>
            <p>Rather than proposing new legislative acts, the priority is to ensure that the 
            proposals currently being negotiated are timely adopted.</p>
        </html>
        """
        
        soup_6 = BeautifulSoup(html_6, 'html.parser')
        extractor_6 = LegislativeOutcomeExtractor(registration_number="2019/000016")
        result_6 = extractor_6.extract_proposal_commitment_stated(soup_6)
        assert result_6 is False, "Should return False when referring to existing proposals, not committing to new ones"
        
        # Test case 7: Commitment in follow-up section
        html_7 = """
        <html>
            <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
            <p>The Commission welcomes the initiative.</p>
            <h2 id="Follow-up">Follow-up</h2>
            <p>Following further assessment, the Commission communicated its intention to 
            table a legislative proposal by the end of 2024.</p>
        </html>
        """
        
        soup_7 = BeautifulSoup(html_7, 'html.parser')
        extractor_7 = LegislativeOutcomeExtractor(registration_number="2020/000001")
        result_7 = extractor_7.extract_proposal_commitment_stated(soup_7)
        assert result_7 is True, "Should detect commitment in follow-up section"
        
        # Test case 8: Alternative approach without commitment
        html_8 = """
        <html>
            <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
            <p>The Commission does share the conviction that animal testing should be phased out, 
            but its approach differs from the one proposed in this Citizens' Initiative.</p>
            <p>The Commission will continue supporting the development of alternative approaches.</p>
        </html>
        """
        
        soup_8 = BeautifulSoup(html_8, 'html.parser')
        extractor_8 = LegislativeOutcomeExtractor(registration_number="2012/000007")
        result_8 = extractor_8.extract_proposal_commitment_stated(soup_8)
        assert result_8 is False, "Should return False for alternative actions without legislative proposal"
        
        # Test case 9: No Answer section - returns None
        html_9 = """
        <html>
            <h2 id="Submission-and-examination">Submission and examination</h2>
            <p>Some procedural content.</p>
        </html>
        """
        
        soup_9 = BeautifulSoup(html_9, 'html.parser')
        extractor_9 = LegislativeOutcomeExtractor(registration_number="2099/999999")

        with pytest.raises(ValueError, match="Could not extract legislative content for initiative 2099/999999"):
            extractor_9.extract_proposal_commitment_stated(soup_9)
        
        # Test case 10: Roadmap/assessment without commitment
        html_10 = """
        <html>
            <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
            <p>The Commission commits to start preparatory work with a view to launch, 
            by the end of 2023, an impact assessment on the environmental, social and economic 
            consequences of the policy.</p>
        </html>
        """
        
        soup_10 = BeautifulSoup(html_10, 'html.parser')
        extractor_10 = LegislativeOutcomeExtractor(registration_number="2020/000001")
        result_10 = extractor_10.extract_proposal_commitment_stated(soup_10)
        assert result_10 is False, "Should return False for assessment commitment without legislative proposal commitment"
        
        # Test case 11: Mixed response - partial rejection, partial commitment
        html_11 = """
        <html>
            <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
            <p>On the first aim, to ban glyphosate, the Commission will not make a legislative proposal.</p>
            <p>On the second aim, to improve transparency, the Commission committed to come forward 
            with a legislative proposal by May 2018.</p>
        </html>
        """
        
        soup_11 = BeautifulSoup(html_11, 'html.parser')
        extractor_11 = LegislativeOutcomeExtractor(registration_number="2017/000002")
        result_11 = extractor_11.extract_proposal_commitment_stated(soup_11)
        assert result_11 is True, "Should return True when at least one commitment exists, even if other parts rejected"

    def test_proposal_rejected(self):
        """Test extraction of whether Commission rejected legislative proposal."""
        
        # Test case 1: Plain rejection
        html_1 = """
        <html>
            <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
            <p>The Commission will not make a legislative proposal to ban glyphosate.</p>
        </html>
        """
        soup_1 = BeautifulSoup(html_1, 'html.parser')
        extractor_1 = LegislativeOutcomeExtractor(registration_number="2017/000002")
        result_1 = extractor_1.extract_proposal_rejected(soup_1)

        assert result_1 is True, "Should detect plain rejection"
        
        # Test case 2: Rejected - already covered
        html_2 = """
        <html>
            <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
            <p>The Commission has decided not to submit a legislative proposal. 
            The existing funding framework is the appropriate one.</p>
        </html>
        """
        soup_2 = BeautifulSoup(html_2, 'html.parser')
        extractor_2 = LegislativeOutcomeExtractor(registration_number="2012/000005")
        result_2 = extractor_2.extract_proposal_rejected(soup_2)

        assert result_2 is True, "Should detect rejection when existing legislation applies"
        
        # Test case 3: Commitment (no rejection)
        html_3 = """
        <html>
            <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
            <p>The Commission committed to table a legislative proposal by May 2018.</p>
        </html>
        """
        soup_3 = BeautifulSoup(html_3, 'html.parser')
        extractor_3 = LegislativeOutcomeExtractor(registration_number="2018/000004")
        result_3 = extractor_3.extract_proposal_rejected(soup_3)

        assert result_3 is False, "Should return False when there is commitment, not rejection"
        
        # Test case 4: Rejected with alternative actions
        html_4 = """
        <html>
            <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
            <p>The Commission considers that the existing Directive is the right legislation, 
            therefore no repeal was proposed.</p>
            <p>However, the Commission commits to monitoring compliance and enforcement.</p>
        </html>
        """
        soup_4 = BeautifulSoup(html_4, 'html.parser')
        extractor_4 = LegislativeOutcomeExtractor(registration_number="2012/000007")
        result_4 = extractor_4.extract_proposal_rejected(soup_4)

        assert result_4 is True, "Should detect rejection even when alternative actions are offered"
        
        # Test case 5: Non-legislative response without rejection
        html_5 = """
        <html>
            <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
            <p>The Commission will strengthen implementation of existing legislation 
            and improve transparency measures.</p>
        </html>
        """
        soup_5 = BeautifulSoup(html_5, 'html.parser')
        extractor_5 = LegislativeOutcomeExtractor(registration_number="2012/000003")
        result_5 = extractor_5.extract_proposal_rejected(soup_5)

        assert result_5 is False, "Should return False for non-legislative actions without explicit rejection"
        
        # Test case 6: Mixed response - partial rejection
        html_6 = """
        <html>
            <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
            <p>On the first aim, the Commission will not make a legislative proposal.</p>
            <p>On the second aim, the Commission committed to table a proposal by May 2018.</p>
        </html>
        """
        soup_6 = BeautifulSoup(html_6, 'html.parser')
        extractor_6 = LegislativeOutcomeExtractor(registration_number="2017/000002")
        result_6 = extractor_6.extract_proposal_rejected(soup_6)

        assert result_6 is True, "Should return True when any rejection is present, even in mixed response"
        
        # Test case 7: Existing proposals (implicit rejection of new proposal)
        html_7 = """
        <html>
            <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
            <p>Rather than proposing new legislative acts, the priority is to ensure 
            that the proposals currently being negotiated are adopted.</p>
        </html>
        """
        soup_7 = BeautifulSoup(html_7, 'html.parser')
        extractor_7 = LegislativeOutcomeExtractor(registration_number="2019/000016")
        result_7 = extractor_7.extract_proposal_rejected(soup_7)

        assert result_7 is False, "Should return False for existing proposals (not explicit rejection)"
        
        # Test case 8: Roadmap/assessment without rejection
        html_8 = """
        <html>
            <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
            <p>The Commission will launch an impact assessment by the end of 2023 
            to evaluate appropriate actions.</p>
        </html>
        """
        soup_8 = BeautifulSoup(html_8, 'html.parser')
        extractor_8 = LegislativeOutcomeExtractor(registration_number="2020/000001")
        result_8 = extractor_8.extract_proposal_rejected(soup_8)

        assert result_8 is False, "Should return False for assessment commitment without rejection"
        
        # Test case 9: Error when Answer section not found
        html_9 = """
        <html>
            <h2 id="Submission-and-examination">Submission and examination</h2>
            <p>Some procedural content.</p>
        </html>
        """
        soup_9 = BeautifulSoup(html_9, 'html.parser')
        extractor_9 = LegislativeOutcomeExtractor(registration_number="2099/999999")
        
        with pytest.raises(ValueError, match="Could not extract legislative content for initiative 2099/999999"):
            extractor_9.extract_proposal_rejected(soup_9)
        
        # Test case 10: Rejection with reasoning
        html_10 = """
        <html>
            <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
            <p>The Commission concluded that there are neither scientific nor legal grounds 
            to justify the proposed legislation, and will not make a legislative proposal.</p>
        </html>
        """
        soup_10 = BeautifulSoup(html_10, 'html.parser')
        extractor_10 = LegislativeOutcomeExtractor(registration_number="2017/000002")
        result_10 = extractor_10.extract_proposal_rejected(soup_10)
        
        assert result_10 is True, "Should detect rejection with reasoning"
        
    def test_rejection_reasoning(self):
        """Test extraction of rejection reasoning text."""
        
        # Test case 1: No rejection - Law Active (no reasoning expected)
        html_1 = """
        <html>
            <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
            <p>The Commission committed to table a legislative proposal by the end of 2023.</p>
            <h2 id="Follow-up">Follow-up</h2>
            <p>The regulation became applicable from 26 June 2023.</p>
        </html>
        """
        soup_1 = BeautifulSoup(html_1, 'html.parser')
        extractor_1 = LegislativeOutcomeExtractor(registration_number="2012/000003")
        result_1 = extractor_1.extract_rejection_reasoning(soup_1)
        
        assert result_1 is None, "Should return None when there is no rejection"
        
        # Test case 2: Rejected - Already Covered (fallback reasoning)
        html_2 = """
        <html>
            <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
            <p>Decision date: 28/05/2014</p>
            <p>The Commission has decided not to submit a legislative proposal, given that 
            Member States and the European Parliament had only recently discussed and decided 
            EU policy in this regard.</p>
        </html>
        """
        soup_2 = BeautifulSoup(html_2, 'html.parser')
        extractor_2 = LegislativeOutcomeExtractor(registration_number="2012/000005")
        result_2 = extractor_2.extract_rejection_reasoning(soup_2)
        
        assert result_2 is not None, "Should extract rejection reasoning"
        assert "decided not to submit" in result_2 or "The Commission decided not to make a legislative proposal" in result_2
        
        # Test case 3: Rejected - Alternative Actions (detailed reasoning)
        html_3 = """
        <html>
            <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
            <p><strong>Main conclusions of the Communication</strong>:</p>
            <p>While the Commission does share the conviction that animal testing should be phased 
            out in Europe, its approach for achieving that objective differs from the one proposed 
            in this Citizens' Initiative.</p>
            <p>The Commission considers that the Directive on the protection of animals used for 
            scientific purposes (Directive 2010/63/EU), which the Initiative seeks to repeal, is 
            the right legislation to achieve the underlying objectives of the Initiative. It sets 
            full replacement of animals as its ultimate goal as soon as it is scientifically possibly, 
            and provides a legally binding stepwise approach as non-animal alternatives become available. 
            Therefore, no repeal of that legislation was proposed.</p>
        </html>
        """
        soup_3 = BeautifulSoup(html_3, 'html.parser')
        extractor_3 = LegislativeOutcomeExtractor(registration_number="2012/000007")
        result_3 = extractor_3.extract_rejection_reasoning(soup_3)
        
        assert result_3 is not None, "Should extract rejection reasoning"
        assert "differs from" in result_3 or "no repeal" in result_3
        assert "Directive 2010/63/EU" in result_3
        
        # Test case 4: Mixed response - rejection on first aim, commitment on second (list items)
        html_4 = """
        <html>
            <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
            <p>Official documents:</p>
            <ul>
                <li><a href="https://example.com/comm.pdf">Communication</a></li>
                <li><a href="https://example.com/annex.pdf">Annex</a></li>
            </ul>
            <p><strong>Main conclusions of the Communication</strong>:</p>
            <ul>
                <li>On the first aim, to 'ban glyphosate-based herbicides', the Commission concluded 
                that there are neither scientific nor legal grounds to justify a ban of glyphosate, 
                and will not make a legislative proposal to that effect.</li>
                <li>On the second aim, to "ensure that the scientific evaluation of pesticides for 
                EU regulatory approval is based only on published studies, which are commissioned by 
                competent public authorities instead of the pesticide industry", the Commission 
                committed to come forward with a legislative proposal by May 2018, amongst others, 
                to strengthen the transparency of the EU risk assessment in the food chain and 
                enhance – through a series of measures – the governance for the conduct of industry 
                studies submitted to the European Food Safety Authority (EFSA) for risk assessment. 
                See details below under 'Follow-up'.</li>
            </ul>
            <h2 id="Follow-up">Follow-up</h2>
        </html>
        """
        soup_4 = BeautifulSoup(html_4, 'html.parser')
        extractor_4 = LegislativeOutcomeExtractor(registration_number="2017/000002")
        result_4 = extractor_4.extract_rejection_reasoning(soup_4)
        
        assert result_4 is not None, "Should extract rejection reasoning for mixed response"
        assert "legislative proposal" in result_4.lower()
        assert "glyphosate" in result_4.lower() or "scientific evaluation" in result_4.lower()
        # Should contain both the rejection and commitment parts mentioning legislative proposal
        assert len(result_4) > 100, "Should contain comprehensive text from both list items"
        
        # Test case 5: Pure rejection with detailed reasoning in paragraphs
        html_5 = """
        <html>
            <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
            <p><strong>Main conclusions of the Communication</strong>:</p>
            <p>The Commission concluded that there are neither scientific nor legal grounds 
            to justify the proposed legislation.</p>
            <p>The Commission will not make a legislative proposal to that effect.</p>
            <p>The existing legislation already covers the objectives of this initiative.</p>
        </html>
        """
        soup_5 = BeautifulSoup(html_5, 'html.parser')
        extractor_5 = LegislativeOutcomeExtractor(registration_number="2017/000004")
        result_5 = extractor_5.extract_rejection_reasoning(soup_5)
        
        assert result_5 is not None, "Should extract rejection reasoning"
        assert "will not make" in result_5 or "neither scientific nor legal grounds" in result_5
        
        # Test case 6: No rejection - Law Promised
        html_6 = """
        <html>
            <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
            <p>In its response to the ECI, the Commission communicated its intention to 
            table a legislative proposal, by the end of 2023, to phase out cages.</p>
        </html>
        """
        soup_6 = BeautifulSoup(html_6, 'html.parser')
        extractor_6 = LegislativeOutcomeExtractor(registration_number="2018/000004")
        result_6 = extractor_6.extract_rejection_reasoning(soup_6)
        
        assert result_6 is None, "Should return None when there is commitment without rejection"
        
        # Test case 7: Rejected with competence reasoning
        html_7 = """
        <html>
            <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
            <p>The Commission carefully analysed the citizens' proposals and concluded that 
            while some proposals fall outside of EU competence, as they would interfere with 
            the existing constitutional setup of the concerned Member States, others are 
            already covered under the current Cohesion policy thanks to its robust safeguards 
            promoting inclusion and equal treatment of minorities, as well as the respect for 
            cultural and linguistic diversity.</p>
        </html>
        """
        soup_7 = BeautifulSoup(html_7, 'html.parser')
        extractor_7 = LegislativeOutcomeExtractor(registration_number="2019/000007")
        result_7 = extractor_7.extract_rejection_reasoning(soup_7)
        
        assert result_7 is not None, "Should extract rejection reasoning"
        assert "fall outside of EU competence" in result_7.lower() or "already covered" in result_7.lower()
        
        # Test case 8: No rejection - Law Active (no reasoning)
        html_8 = """
        <html>
            <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
            <p>The Commission welcomes the initiative.</p>
            <h2 id="Follow-up">Follow-up</h2>
            <p>The regulation became applicable immediately after publication.</p>
        </html>
        """
        soup_8 = BeautifulSoup(html_8, 'html.parser')
        extractor_8 = LegislativeOutcomeExtractor(registration_number="2019/000016")
        result_8 = extractor_8.extract_rejection_reasoning(soup_8)
        
        assert result_8 is None, "Should return None for Law Active without rejection"
        
        # Test case 9: No rejection - Being Studied
        html_9 = """
        <html>
            <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
            <p>The Commission has tasked the European Food Safety Authority (EFSA) to 
            provide a scientific opinion. The Commission will then communicate by March 2026 
            on the most appropriate action.</p>
        </html>
        """
        soup_9 = BeautifulSoup(html_9, 'html.parser')
        extractor_9 = LegislativeOutcomeExtractor(registration_number="2020/000001")
        result_9 = extractor_9.extract_rejection_reasoning(soup_9)
        
        assert result_9 is None, "Should return None for Being Studied status"
        
        # Test case 10: No rejection - Action Plan Created
        html_10 = """
        <html>
            <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
            <p>The Commission will work together with all relevant parties on a roadmap 
            towards chemical safety assessments. The roadmap will serve as a guiding 
            framework for future actions.</p>
        </html>
        """
        soup_10 = BeautifulSoup(html_10, 'html.parser')
        extractor_10 = LegislativeOutcomeExtractor(registration_number="2021/000006")
        result_10 = extractor_10.extract_rejection_reasoning(soup_10)
        
        assert result_10 is None, "Should return None for Action Plan Created status"
        
        # Test case 11: No rejection - Being Studied (second case)
        html_11 = """
        <html>
            <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
            <p>The Commission commits to launch an impact assessment on the environmental, 
            social and economic consequences by the end of 2023.</p>
        </html>
        """
        soup_11 = BeautifulSoup(html_11, 'html.parser')
        extractor_11 = LegislativeOutcomeExtractor(registration_number="2022/000002")
        result_11 = extractor_11.extract_rejection_reasoning(soup_11)
        
        assert result_11 is None, "Should return None for Being Studied status"
        
        # Test case 12: Rejection with existing funding framework reasoning
        html_12 = """
        <html>
            <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
            <p>The Commission has concluded that the existing funding framework, which had 
            been recently debated and agreed by EU Member States and the European Parliament, 
            is the appropriate one. Therefore, the Commission will not propose new legislation.</p>
        </html>
        """
        soup_12 = BeautifulSoup(html_12, 'html.parser')
        extractor_12 = LegislativeOutcomeExtractor(registration_number="2012/000005")
        result_12 = extractor_12.extract_rejection_reasoning(soup_12)
        
        assert result_12 is not None, "Should extract rejection reasoning"
        assert "existing funding framework" in result_12.lower() or "will not propose" in result_12.lower()
        
        # Test case 13: Skips factsheet divs in extraction
        html_13 = """
        <html>
            <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
            <div class="ecl-file ecl-file--has-translation">
                <div class="ecl-file__container">
                    <a href="https://example.com/factsheet.pdf" class="ecl-link ecl-file__download">
                        Factsheet Download (4.89 MB - PDF)
                    </a>
                </div>
            </div>
            <p>The Commission will not make a legislative proposal because the existing 
            legislation already addresses these concerns.</p>
        </html>
        """
        soup_13 = BeautifulSoup(html_13, 'html.parser')
        extractor_13 = LegislativeOutcomeExtractor(registration_number="2017/000004")
        result_13 = extractor_13.extract_rejection_reasoning(soup_13)
        
        assert result_13 is not None, "Should extract rejection reasoning"
        assert "Factsheet" not in result_13, "Should not include factsheet download text"
        assert "will not make" in result_13 or "existing legislation" in result_13
        
        # Test case 14: Error when Answer section not found
        html_14 = """
        <html>
            <h2 id="Submission-and-examination">Submission and examination</h2>
            <p>Some content here.</p>
        </html>
        """
        soup_14 = BeautifulSoup(html_14, 'html.parser')
        extractor_14 = LegislativeOutcomeExtractor(registration_number="2099/999999")
        
        with pytest.raises(ValueError, match="Could not extract legislative content for initiative 2099/999999"):
            extractor_14.extract_rejection_reasoning(soup_14)
        
        # Test case 15: Mixed response with nested list structure
        html_15 = """
        <html>
            <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
            <p><strong>Main conclusions of the Communication</strong>:</p>
            <ol>
                <li>On the first aim, to ban certain substances, the Commission concluded that 
                there are no scientific grounds and will not make a legislative proposal.</li>
                <li>On the second aim, the Commission committed to table a legislative proposal 
                by December 2024 to strengthen regulatory frameworks.</li>
                <li>On the third aim, the Commission will not propose new measures as existing 
                legislation adequately covers these objectives.</li>
            </ol>
            <h2 id="Follow-up">Follow-up</h2>
        </html>
        """
        soup_15 = BeautifulSoup(html_15, 'html.parser')
        extractor_15 = LegislativeOutcomeExtractor(registration_number="2017/000002")
        result_15 = extractor_15.extract_rejection_reasoning(soup_15)
        
        assert result_15 is not None, "Should extract rejection reasoning from mixed response"
        assert "legislative proposal" in result_15.lower()
        # Should capture all relevant items mentioning legislative proposal
        assert len([item for item in result_15.split('.') if 'legislative proposal' in item.lower()]) >= 2

    def test_rejection_reasoning_debug(self):
        """Test extraction of rejection reasoning text."""

        # Test case 7: Rejected with competence reasoning
        html_7 = """
        <html>
            <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
            <p>The Commission carefully analysed the citizens' proposals and concluded that 
            while some proposals fall outside of EU competence, as they would interfere with 
            the existing constitutional setup of the concerned Member States, others are 
            already covered under the current Cohesion policy thanks to its robust safeguards 
            promoting inclusion and equal treatment of minorities, as well as the respect for 
            cultural and linguistic diversity.</p>
        </html>
        """
        soup_7 = BeautifulSoup(html_7, 'html.parser')
        extractor_7 = LegislativeOutcomeExtractor(registration_number="2019/000007")
        result_7 = extractor_7.extract_rejection_reasoning(soup_7)
 
    def test_applicable_date(self):
        """Test extraction of date when regulation became applicable."""
        
        # Test case 1: Specific date - "became applicable on 27 March 2021"
        html_1 = """
        <html>
            <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
            <p>The Commission committed to table a legislative proposal.</p>
            <p>The regulation became applicable 18 months later, i.e. on 27 March 2021.</p>
            <h2 id="Follow-up">Follow-up</h2>
            <p>The regulation was adopted by the Commission and it became applicable 
            18 months later, i.e. on 27 March 2021.</p>
        </html>
        """
        soup_1 = BeautifulSoup(html_1, 'html.parser')
        extractor_1 = LegislativeOutcomeExtractor(registration_number="2017/000002")
        result_1 = extractor_1.extract_applicable_date(soup_1)
        
        assert result_1 == "2021-03-27", f"Expected '2021-03-27', got '{result_1}'"
        
        # Test case 2: Became applicable immediately (use entry into force date)
        html_2 = """
        <html>
            <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
            <p>The Commission proposed new legislation.</p>
            <h2 id="Follow-up">Follow-up</h2>
            <p>It entered into force on 18 August 2024 (20 days after its publication 
            in the Official Journal of the EU) and became applicable immediately.</p>
        </html>
        """
        soup_2 = BeautifulSoup(html_2, 'html.parser')
        extractor_2 = LegislativeOutcomeExtractor(registration_number="2019/000016")
        result_2 = extractor_2.extract_applicable_date(soup_2)
        
        assert result_2 == "2024-08-18", f"Expected '2024-08-18', got '{result_2}'"
        
        # Test case 3: "applicable from" pattern
        html_3 = """
        <html>
            <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
            <p>The Commission adopted the regulation.</p>
            <h2 id="Follow-up">Follow-up</h2>
            <p>The regulation was published in the Official Journal and 
            became applicable from 26 June 2023.</p>
        </html>
        """
        soup_3 = BeautifulSoup(html_3, 'html.parser')
        extractor_3 = LegislativeOutcomeExtractor(registration_number="2018/000004")
        result_3 = extractor_3.extract_applicable_date(soup_3)
        
        assert result_3 == "2023-06-26", f"Expected '2023-06-26', got '{result_3}'"
        
        # Test case 4: "and applicable from" pattern
        html_4 = """
        <html>
            <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
            <p>The Commission committed to legislation.</p>
            <h2 id="Follow-up">Follow-up</h2>
            <p>The regulation entered into force in July 2023 
            and applicable from 15 September 2023.</p>
        </html>
        """
        soup_4 = BeautifulSoup(html_4, 'html.parser')
        extractor_4 = LegislativeOutcomeExtractor(registration_number="2012/000003")
        result_4 = extractor_4.extract_applicable_date(soup_4)
        
        assert result_4 == "2023-09-15", f"Expected '2023-09-15', got '{result_4}'"
        
        # Test case 5: "applies from" pattern
        html_5 = """
        <html>
            <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
            <p>Legislative proposal was tabled.</p>
            <h2 id="Follow-up">Follow-up</h2>
            <p>The new regulation applies from 1 January 2024.</p>
        </html>
        """
        soup_5 = BeautifulSoup(html_5, 'html.parser')
        extractor_5 = LegislativeOutcomeExtractor(registration_number="2020/000001")
        result_5 = extractor_5.extract_applicable_date(soup_5)
        
        assert result_5 == "2024-01-01", f"Expected '2024-01-01', got '{result_5}'"
        
        # Test case 6: No applicable date (not in applicable status)
        html_6 = """
        <html>
            <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
            <p>The Commission will not make a legislative proposal.</p>
            <p>The existing legislation already covers the objectives.</p>
        </html>
        """
        soup_6 = BeautifulSoup(html_6, 'html.parser')
        extractor_6 = LegislativeOutcomeExtractor(registration_number="2012/000005")
        result_6 = extractor_6.extract_applicable_date(soup_6)
        
        assert result_6 is None, "Should return None when not in applicable status"
        
        # Test case 7: No applicable date (commitment only, not yet applicable)
        html_7 = """
        <html>
            <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
            <p>The Commission committed to table a legislative proposal by the end of 2023.</p>
        </html>
        """
        soup_7 = BeautifulSoup(html_7, 'html.parser')
        extractor_7 = LegislativeOutcomeExtractor(registration_number="2021/000006")
        result_7 = extractor_7.extract_applicable_date(soup_7)
        
        assert result_7 is None, "Should return None when committed but not yet applicable"
        
        # Test case 8: Date in Answer section (not just Follow-up)
        html_8 = """
        <html>
            <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
            <p>The regulation became applicable on 10 May 2022 following publication 
            in the Official Journal of the EU.</p>
            <h2 id="Follow-up">Follow-up</h2>
            <p>Further updates will be provided.</p>
        </html>
        """
        soup_8 = BeautifulSoup(html_8, 'html.parser')
        extractor_8 = LegislativeOutcomeExtractor(registration_number="2017/000004")
        result_8 = extractor_8.extract_applicable_date(soup_8)
        
        assert result_8 == "2022-05-10", f"Expected '2022-05-10', got '{result_8}'"
        
        # Test case 9: Short month name format
        html_9 = """
        <html>
            <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
            <p>Commitment to legislation.</p>
            <h2 id="Follow-up">Follow-up</h2>
            <p>The directive became applicable from 5 Dec 2023.</p>
        </html>
        """
        soup_9 = BeautifulSoup(html_9, 'html.parser')
        extractor_9 = LegislativeOutcomeExtractor(registration_number="2019/000007")
        result_9 = extractor_9.extract_applicable_date(soup_9)
        
        assert result_9 == "2023-12-05", f"Expected '2023-12-05', got '{result_9}'"
        
        # Test case 10: Error when Answer section missing
        html_10 = """
        <html>
            <h2 id="Submission-and-examination">Submission and examination</h2>
            <p>Some content here.</p>
        </html>
        """
        soup_10 = BeautifulSoup(html_10, 'html.parser')
        extractor_10 = LegislativeOutcomeExtractor(registration_number="9999/999999")
        
        with pytest.raises(ValueError, match="Could not find Answer section"):
            extractor_10.extract_applicable_date(soup_10)
        
        # Test case 11: Multiple dates - should extract first applicable date found
        html_11 = """
        <html>
            <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
            <p>The Commission made progress.</p>
            <h2 id="Follow-up">Follow-up</h2>
            <p>The regulation was published on 15 March 2023.</p>
            <p>It became applicable on 1 April 2023 after a transition period.</p>
        </html>
        """
        soup_11 = BeautifulSoup(html_11, 'html.parser')
        extractor_11 = LegislativeOutcomeExtractor(registration_number="2022/000002")
        result_11 = extractor_11.extract_applicable_date(soup_11)
        
        assert result_11 == "2023-04-01", f"Expected '2023-04-01', got '{result_11}'"
        
        # Test case 12: Date with "apply from" (singular form)
        html_12 = """
        <html>
            <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
            <p>New rules were adopted.</p>
            <h2 id="Follow-up">Follow-up</h2>
            <p>The new provisions will apply from 20 November 2024.</p>
        </html>
        """
        soup_12 = BeautifulSoup(html_12, 'html.parser')
        extractor_12 = LegislativeOutcomeExtractor(registration_number="2023/000001")
        result_12 = extractor_12.extract_applicable_date(soup_12)
        
        assert result_12 == "2024-11-20", f"Expected '2024-11-20', got '{result_12}'"

    def test_commission_deadlines(self):
        """Test extraction of Commission deadlines with various date formats and phrasings."""
        
        # Test 1: Single deadline with "by [month year]" format
        html_single_deadline = """
        <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
        <p>The Commission committed to come forward with a legislative proposal by May 2018, 
        amongst others, to strengthen the transparency of the EU risk assessment in the food chain.</p>
        """
        soup = BeautifulSoup(html_single_deadline, 'html.parser')
        extractor = LegislativeOutcomeExtractor("2017/000002")
        result = extractor.extract_commissions_deadlines(soup)
        
        assert result is not None
        result_dict = json.loads(result)
        assert "2018-05-31" in result_dict
        assert "committed to come forward with a legislative proposal by May 2018" in result_dict["2018-05-31"]
        
        # Test 2: Multiple deadlines in same initiative
        html_multiple_deadlines = """
        <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
        <p>● Start without delay preparatory work with a view to launch, by the end of 2023, 
        an impact assessment on the environmental, social and economic consequences.</p>
        <p>● By end 2024, provide more detailed EU's import and export information to 
        improve statistics on trade in shark products.</p>
        """
        soup = BeautifulSoup(html_multiple_deadlines, 'html.parser')
        extractor = LegislativeOutcomeExtractor("2020/000001")
        result = extractor.extract_commissions_deadlines(soup)
        
        assert result is not None
        result_dict = json.loads(result)
        assert len(result_dict) == 2
        assert "2023-12-31" in result_dict
        assert "2024-12-31" in result_dict
        assert "by the end of 2023" in result_dict["2023-12-31"]
        assert "By end 2024, provide" in result_dict["2024-12-31"]
        
        # Test 3: Deadline with "early [year]" format
        html_early_year = """
        <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
        <p>Building further on this scientific input, and on an assessment of economic and 
        social impacts, the Commission will then communicate, by March 2026, on the most 
        appropriate action.</p>
        """
        soup = BeautifulSoup(html_early_year, 'html.parser')
        extractor = LegislativeOutcomeExtractor("2022/000002")
        result = extractor.extract_commissions_deadlines(soup)
        
        assert result is not None
        result_dict = json.loads(result)
        assert "2026-03-31" in result_dict
        assert "by March 2026" in result_dict["2026-03-31"]
        
        # Test 4: Report to be produced with standalone year
        html_report_year = """
        <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
        <ul>
            <li>The Commission will re-evaluate the situation, initially in a report to 
            Council and the Parliament on the implementation of the Directive to be 
            produced in 2019.</li>
        </ul>
        """
        soup = BeautifulSoup(html_report_year, 'html.parser')
        extractor = LegislativeOutcomeExtractor("2017/000002")
        result = extractor.extract_commissions_deadlines(soup)
        
        assert result is not None
        result_dict = json.loads(result)
        assert "2019-12-31" in result_dict
        assert "to be produced in 2019" in result_dict["2019-12-31"]
        
        # Test 5: Intention to table legislative proposal
        html_intention = """
        <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
        <p>In its response to the ECI, the Commission communicated its intention to table 
        a legislative proposal, by the end of 2023, to phase out, and finally prohibit, 
        the use of cages for all animals mentioned in the ECI.</p>
        """
        soup = BeautifulSoup(html_intention, 'html.parser')
        extractor = LegislativeOutcomeExtractor("2018/000004")
        result = extractor.extract_commissions_deadlines(soup)
        
        assert result is not None
        result_dict = json.loads(result)
        assert "2023-12-31" in result_dict
        assert "intention to table a legislative proposal" in result_dict["2023-12-31"]
        
        # Test 6: No deadlines mentioned
        html_no_deadlines = """
        <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
        <p>The Commission decided not to submit a legislative proposal as the existing 
        legislation already covers this matter adequately.</p>
        """
        soup = BeautifulSoup(html_no_deadlines, 'html.parser')
        extractor = LegislativeOutcomeExtractor("2012/000003")
        result = extractor.extract_commissions_deadlines(soup)
        
        assert result is None
        
        # Test 7: Impact assessment deadline
        html_impact_assessment = """
        <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
        <p>The Commission will launch an impact assessment by the end of 2024 to evaluate 
        the environmental and social consequences of the proposed measures.</p>
        """
        soup = BeautifulSoup(html_impact_assessment, 'html.parser')
        extractor = LegislativeOutcomeExtractor("2021/000001")
        result = extractor.extract_commissions_deadlines(soup)
        
        assert result is not None
        result_dict = json.loads(result)
        assert "2024-12-31" in result_dict
        assert "launch an impact assessment" in result_dict["2024-12-31"]
        
        # Test 8: EFSA scientific opinion deadline
        html_efsa = """
        <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
        <p>The Commission has tasked the European Food Safety Authority (EFSA) to provide 
        a scientific opinion by end of 2025 on the welfare of animals farmed for fur.</p>
        """
        soup = BeautifulSoup(html_efsa, 'html.parser')
        extractor = LegislativeOutcomeExtractor("2022/000001")
        result = extractor.extract_commissions_deadlines(soup)
        
        assert result is not None
        result_dict = json.loads(result)
        assert "2025-12-31" in result_dict
        assert "scientific opinion" in result_dict["2025-12-31"]
        
        # Test 9: Roadmap deadline
        html_roadmap = """
        <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
        <p>Finalisation of the work on the roadmap is planned by early 2026 to outline 
        the Commission's strategy for the next steps.</p>
        """
        soup = BeautifulSoup(html_roadmap, 'html.parser')
        extractor = LegislativeOutcomeExtractor("2023/000001")
        result = extractor.extract_commissions_deadlines(soup)
        
        assert result is not None
        result_dict = json.loads(result)
        assert "2026-03-31" in result_dict
        assert "roadmap is planned by early 2026" in result_dict["2026-03-31"]
        
        # Test 10: Deadline-first format (By [date], [action])
        html_deadline_first = """
        <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
        <p>● By end 2024, provide more detailed EU's import and export information to 
        improve statistics on trade in shark products.</p>
        """
        soup = BeautifulSoup(html_deadline_first, 'html.parser')
        extractor = LegislativeOutcomeExtractor("2020/000001")
        result = extractor.extract_commissions_deadlines(soup)
        
        assert result is not None
        result_dict = json.loads(result)
        assert "2024-12-31" in result_dict
        assert "By end 2024, provide" in result_dict["2024-12-31"]
        
        # Test 11: Multiple deadlines on same date (should concatenate)
        html_same_date = """
        <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
        <p>The Commission will launch an impact assessment by end of 2023.</p>
        <p>The Commission will also provide a report by end of 2023 on the implementation status.</p>
        """
        soup = BeautifulSoup(html_same_date, 'html.parser')
        extractor = LegislativeOutcomeExtractor("2021/000002")
        result = extractor.extract_commissions_deadlines(soup)
        
        assert result is not None
        result_dict = json.loads(result)
        assert "2023-12-31" in result_dict
        # Should contain both commitments separated by semicolon
        assert "impact assessment" in result_dict["2023-12-31"]
        assert "report" in result_dict["2023-12-31"]
        
        # Test 12: Missing Answer section (should raise ValueError)
        html_no_answer = """
        <h2 id="Some-Other-Section">Some Other Section</h2>
        <p>Some content without Answer section.</p>
        """
        soup = BeautifulSoup(html_no_answer, 'html.parser')
        extractor = LegislativeOutcomeExtractor("2012/000001")
        
        with pytest.raises(ValueError) as exc_info:
            extractor.extract_commissions_deadlines(soup)
        assert "Could not find Answer section" in str(exc_info.value)
        
        # Test 13: Stop at next h2 section
        html_multiple_sections = """
        <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
        <p>The Commission will communicate by May 2024 on the appropriate action.</p>
        <h2 id="Next-Section">Next Section</h2>
        <p>The Commission will also do something by December 2025.</p>
        """
        soup = BeautifulSoup(html_multiple_sections, 'html.parser')
        extractor = LegislativeOutcomeExtractor("2023/000002")
        result = extractor.extract_commissions_deadlines(soup)
        
        assert result is not None
        result_dict = json.loads(result)
        # Should only capture the May 2024 deadline, not December 2025
        assert "2024-05-31" in result_dict
        assert "2025-12-31" not in result_dict
        
        # Test 14: Complex sentence with complete extraction
        html_complex = """
        <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
        <p>On the second aim, to "ensure that the scientific evaluation of pesticides for 
        EU regulatory approval is based only on published studies, which are commissioned 
        by competent public authorities instead of the pesticide industry", the Commission 
        committed to come forward with a legislative proposal by May 2018, amongst others, 
        to strengthen the transparency of the EU risk assessment in the food chain and 
        enhance – through a series of measures – the governance for the conduct of industry 
        studies submitted to the European Food Safety Authority (EFSA) for risk assessment.</p>
        """
        soup = BeautifulSoup(html_complex, 'html.parser')
        extractor = LegislativeOutcomeExtractor("2017/000002")
        result = extractor.extract_commissions_deadlines(soup)
        
        assert result is not None
        result_dict = json.loads(result)
        assert "2018-05-31" in result_dict
        # Should extract complete sentence
        assert "On the second aim" in result_dict["2018-05-31"]
        assert "EFSA" in result_dict["2018-05-31"]
        assert "for risk assessment." in result_dict["2018-05-31"]

    def test_legislative_action(self):
        """Test extraction of legislative action JSON array."""
        
        # Test 1: Multiple legislative actions with different statuses (2012/000003)
        html_water_directive = """
        <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
        <p>The Commission will address the concerns raised by this initiative.</p>
        <h2 id="Follow-up">Follow-up</h2>
        <ul>
            <li>As a first step following the European Citizens' Initiative Right2Water, an
            <strong>amendment to the</strong>
            <a href="http://eur-lex.europa.eu/legal-content/EN/TXT/?uri=uriserv:OJ.L_.2015.260.01.0006.01.ENG">
            Drinking Water Directive</a>
            aimed at improving the monitoring of drinking water across Europe came into force on 28 October 2015.</li>
            <li><a href="http://ec.europa.eu/environment/water/water-drink/pdf/revised_drinking_water_directive.pdf">
            <strong>A proposal for the revision of the Directive on drinking water</strong></a>
            was adopted by the Commission on 01 February 2018. The Directive entered into force on 12 January 2021.</li>
            <li>A <a href="https://ec.europa.eu/environment/water/pdf/water_reuse_regulation.pdf">
            proposal for a regulation on minimum requirements for water reuse</a>
            was adopted by the Commission in May 2018. The Regulation entered into force in June 2020. 
            The new rules apply from 26 June 2023.</li>
            <li>In January 2024, the Commission adopted
            <a href="https://environment.ec.europa.eu/publications/delegated-acts-drinking-water-directive_en">
            <strong>new minimum hygiene standards</strong></a>
            <strong>for materials and products that come into contact with drinking water</strong>. 
            They will apply as of 31 December 2026.</li>
        </ul>
        """

        soup = BeautifulSoup(html_water_directive, 'html.parser')
        extractor = LegislativeOutcomeExtractor("2012/000003")
        result = extractor.extract_legislative_action(soup)
        
        assert result is not None
        result_list = json.loads(result)
        assert len(result_list) == 4
        
        # Check amendment
        amendment = next((a for a in result_list if a['type'] == 'Amendment'), None)
        assert amendment is not None
        assert amendment['status'] == 'in_force'
        assert amendment['date'] == '2015-10-28'
        
        # Check directive revision
        directive = next((a for a in result_list if 'Directive Revision' in a['type']), None)
        assert directive is not None
        assert directive['status'] == 'in_force'
        assert directive['date'] == '2021-01-12'
        
        # Check water reuse regulation
        water_reuse = next((a for a in result_list if 'reuse' in a['description'].lower()), None)
        assert water_reuse is not None
        assert water_reuse['status'] == 'in_force'
        assert water_reuse['date'] == '2023-06-26'
        
        # Check standards adoption
        standards = next((a for a in result_list if a['type'] == 'Standards Adoption'), None)
        assert standards is not None
        assert standards['status'] == 'planned'
        assert standards['date'] == '2026-12-31'
        
        # Test 2: Tariff codes creation (2020/000001)
        html_tariff_codes = """
        <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
        <p>The Commission will address the concerns raised by this initiative.</p>
        <h2 id="Follow-up">Follow-up</h2>
        <p>Following up on its commitment to develop more detailed EU import and export data to 
        improve statistics on trade in shark products, the Commission created 13 new 
        <a href="https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:32024R2522">
        tariff codes for sharks and their fins</a>. These codes will enable the tracking of the 
        most traded shark species, including the blue shark and shortfin mako. The codes enter 
        in application in January 2025.</p>
        """
        soup = BeautifulSoup(html_tariff_codes, 'html.parser')
        extractor = LegislativeOutcomeExtractor("2020/000001")
        result = extractor.extract_legislative_action(soup)
        
        assert result is not None
        result_list = json.loads(result)
        assert len(result_list) == 1
        assert result_list[0]['type'] == 'Tariff Codes Creation'
        assert result_list[0]['status'] == 'planned'
        assert 'tariff codes' in result_list[0]['description'].lower()
        
        # Test 3: Proposal and adoption cycle (2017/000002)
        html_transparency_reg = """
        <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
        <p>The Commission will address the concerns raised by this initiative.</p>
        <h2 id="Follow-up">Follow-up</h2>
        <p>A proposal for a Regulation of the European Parliament and the Council on the 
        transparency and sustainability of the EU risk assessment in the food chain was 
        adopted by the Commission on 11 April 2018.</p>
        <p>Following the agreement of the European Parliament and the Council, the Regulation 
        was published in the Official Journal of the EU on 6 September 2019 and entered into 
        force on 27 March 2021.</p>
        """
        
        soup = BeautifulSoup(html_transparency_reg, 'html.parser')
        extractor = LegislativeOutcomeExtractor("2017/000002")
        result = extractor.extract_legislative_action(soup)
        
        assert result is not None
        result_list = json.loads(result)
        assert len(result_list) >= 2
        
        # Check proposal
        proposal = next((a for a in result_list if a['status'] == 'proposed'), None)
        assert proposal is not None
        assert proposal['date'] == '2018-04-11'
        
        # Check in force
        in_force = next((a for a in result_list if a['status'] == 'in_force'), None)
        assert in_force is not None
        
        # Test 4: Withdrawn proposal (2019/000016)
        html_withdrawn = """
        <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
        <p>The Commission will address the concerns raised by this initiative.</p>
        <h2 id="Updates-on-the-Commissions-proposals">Updates on the Commission's proposals</h2>
        <p>In view of the rejection by the European Parliament of the proposal in November 2023, 
        and a lack of progress of the discussions in the Council, the Commission withdrew the 
        proposal for a Regulation on the Sustainable Use of Plant Protection Products on 
        27 March 2024.</p>
        <p>The proposal for a Nature Restoration Law was adopted by the Council and entered 
        into force on 18 August 2024.</p>
        """

        soup = BeautifulSoup(html_withdrawn, 'html.parser')
        extractor = LegislativeOutcomeExtractor("2019/000016")
        result = extractor.extract_legislative_action(soup)
        
        assert result is not None
        result_list = json.loads(result)
        
        # Check withdrawn proposal
        withdrawn = next((a for a in result_list if a['status'] == 'withdrawn'), None)
        assert withdrawn is not None
        assert withdrawn['date'] == '2024-03-27'
        
        # Check adopted nature restoration
        nature_law = next((a for a in result_list if 'nature' in a['description'].lower()), None)
        assert nature_law is not None
        assert nature_law['status'] == 'in_force'
        assert nature_law['date'] == '2024-08-18'
        
        # Test 5: Rejected initiative - should return None (2012/000005)
        html_rejected = """
        <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
        <p>The Commission decided not to submit a legislative proposal as the existing 
        legislation already covers this matter adequately.</p>
        """
        soup = BeautifulSoup(html_rejected, 'html.parser')
        extractor = LegislativeOutcomeExtractor("2012/000005")
        result = extractor.extract_legislative_action(soup)
        
        assert result is None
        
        # Test 6: Roadmap only - should return None (2021/000006)
        html_roadmap_only = """
        <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
        <p>The Commission will address the concerns raised by this initiative.</p>
        <h2 id="Follow-up">Follow-up</h2>
        <p>In the second half of 2023, the Commission started work on a roadmap to phase out 
        animal testing for chemical safety assessments that was announced in its reply to 
        the ECI.</p>
        <p>The Commission will carefully consider the Court's judgments in view of any 
        potential future measures.</p>
        """
        soup = BeautifulSoup(html_roadmap_only, 'html.parser')
        extractor = LegislativeOutcomeExtractor("2021/000006")
        result = extractor.extract_legislative_action(soup)
        
        assert result is None
        
        # Test 7: Commitment without actual proposal - should return None (2018/000004 if no follow-up)
        html_commitment_only = """
        <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
        <p>The Commission communicated its intention to table a legislative proposal, 
        by the end of 2023, to phase out the use of cages for all animals.</p>
        """
        soup = BeautifulSoup(html_commitment_only, 'html.parser')
        extractor = LegislativeOutcomeExtractor("2018/000004")
        result = extractor.extract_legislative_action(soup)
        
        assert result is None
        
        # Test 8: Non-legislative activities should be filtered out
        html_non_legislative = """
        <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
        <p>The Commission will address the concerns raised by this initiative.</p>
        <h2 id="Follow-up">Follow-up</h2>
        <p>The Commission will launch an impact assessment by the end of 2023.</p>
        <p>The Commission organized a consultation with stakeholders in 2024.</p>
        <p>A workshop on alternative approaches was held in April 2025.</p>
        <p>The Commission is working towards better enforcement of existing rules.</p>
        <p>In parallel to the legislation, the Commission will seek specific supporting 
        measures in key related policy areas.</p>
        """
        soup = BeautifulSoup(html_non_legislative, 'html.parser')
        extractor = LegislativeOutcomeExtractor("2023/000001")
        result = extractor.extract_legislative_action(soup)
        
        assert result is None
        
        # Test 9: Mixed content with actual legislation
        html_mixed = """
        <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
        <p>The Commission will address the concerns raised by this initiative.</p>
        <h2 id="Follow-up">Follow-up</h2>
        <p>The Commission launched a consultation in January 2023.</p>
        <p>A proposal for a new regulation on animal welfare was adopted by the Commission 
        on 15 June 2023.</p>
        <p>Several stakeholder workshops were organized throughout 2024.</p>
        """
        soup = BeautifulSoup(html_mixed, 'html.parser')
        extractor = LegislativeOutcomeExtractor("2023/000002")
        result = extractor.extract_legislative_action(soup)
        
        assert result is not None
        result_list = json.loads(result)
        assert len(result_list) == 1
        assert result_list[0]['type'] == 'Regulation Proposal'
        assert result_list[0]['date'] == '2023-06-15'
        
        # Test 10: No duplicate actions
        html_duplicates = """
        <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
        <p>The Commission adopted a proposal for a regulation on 10 May 2023.</p>
        <h2 id="Follow-up">Follow-up</h2>
        <p>The Commission adopted a proposal for a regulation on 10 May 2023.</p>
        """
        soup = BeautifulSoup(html_duplicates, 'html.parser')
        extractor = LegislativeOutcomeExtractor("2024/000001")
        result = extractor.extract_legislative_action(soup)
        
        assert result is not None
        result_list = json.loads(result)
        # Should only have one action, not two duplicates
        assert len(result_list) == 1
        
        # Test 11: Updates section takes priority
        html_updates_priority = """
        <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
        <p>The Commission committed to table a proposal.</p>
        <h2 id="Follow-up">Follow-up</h2>
        <p>The Commission is working on the proposal.</p>
        <h2 id="Updates-on-the-Commissions-proposals">Updates on the Commission's proposals</h2>
        <p>The proposal was adopted on 20 January 2024 and entered into force on 1 March 2024.</p>
        """
        soup = BeautifulSoup(html_updates_priority, 'html.parser')
        extractor = LegislativeOutcomeExtractor("2024/000002")
        result = extractor.extract_legislative_action(soup)
        
        assert result is not None
        result_list = json.loads(result)
        # Should extract from all sections
        assert len(result_list) >= 1
        
        # Test 12: Date extraction from various formats
        # TODO: <li>Directive adopted in May 2024.</li>
        # As far it works until to 2022/000002
        html_date_formats = """
        <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
        <p>The Commission will address the concerns raised by this initiative.</p>
        <h2 id="Follow-up">Follow-up</h2>
        <ul>
            <li>Regulation entered into force on 12 January 2023.</li>
            <li>New standards will apply from 2026.</li>
            <li>Better standards will apply in May 2024.</li>
            <li>Amendment came into force on 15/03/2022.</li>
        </ul>
        """
        soup = BeautifulSoup(html_date_formats, 'html.parser')
        extractor = LegislativeOutcomeExtractor("2024/000003")
        result = extractor.extract_legislative_action(soup)
        
        assert result is not None
        result_list = json.loads(result)
        assert len(result_list) >= 2
        
        # Check various date formats were extracted
        dates = [a.get('date') for a in result_list if 'date' in a]
        assert any('2023-01-12' in str(d) for d in dates)
        assert any('2024' in str(d) for d in dates)

    def test_non_legislative_action(self):
        """Test extraction of non-legislative action JSON array."""
        
        # Test case 1: Multiple non-legislative actions from Follow-up section
        html1 = """
        <html>
            <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
            <p>The Commission will address the concerns raised by this initiative.</p>
            
            <h2 id="Follow-up">Follow-up</h2>
            <p>The Commission will launch an impact assessment by the end of 2023 to evaluate policy options.</p>
            <p>A scientific conference on alternative approaches was held at the European Commission on 6-7 December 2024.</p>
            <p>The Commission will continue monitoring compliance with existing legislation through regular audits.</p>
            <p>Stakeholder meetings on water quality took place on 09/09/2023 in Brussels.</p>
            <p>The Commission implements funding programmes in the areas of education, notably Erasmus+, which are fully accessible.</p>
        </html>
        """
        soup1 = BeautifulSoup(html1, 'html.parser')
        extractor1 = LegislativeOutcomeExtractor(registration_number='2023/000001')
        result1 = extractor1.extract_non_legislative_action(soup1)
        
        assert result1 is not None, "Should extract non-legislative actions"
        result_list1 = json.loads(result1)
        assert len(result_list1) >= 4, "Should extract multiple actions"
        
        # Check action types are present
        types1 = [action['type'] for action in result_list1]
        assert 'Impact Assessment and Consultation' in types1
        assert 'Scientific Activity' in types1
        assert 'Monitoring and Enforcement' in types1
        assert 'Stakeholder Dialogue' in types1
        assert 'Funding Programme' in types1
        
        # Check dates are extracted
        dated_actions1 = [a for a in result_list1 if 'date' in a]
        assert len(dated_actions1) >= 2, "Should extract dates from actions"
        
        # Test case 2: Actions from Answer section only (no Follow-up)
        html2 = """
        <html>
            <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
            <p>The Commission monitors the implementation of existing EU initiatives which are directly relevant.</p>
            <p>The Commission will strengthen enforcement of EU law through regular inspections.</p>
            <p>Transparency and benchmarking initiatives will be established in 2024.</p>
        </html>
        """
        soup2 = BeautifulSoup(html2, 'html.parser')
        extractor2 = LegislativeOutcomeExtractor(registration_number='2023/000002')
        result2 = extractor2.extract_non_legislative_action(soup2)
        
        assert result2 is not None, "Should extract from Answer section"
        result_list2 = json.loads(result2)
        assert len(result_list2) >= 2
        
        types2 = [action['type'] for action in result_list2]
        assert 'Monitoring and Enforcement' in types2
        assert 'Data Collection and Transparency' in types2
        
        # Test case 3: List items with non-legislative actions
        html3 = """
        <html>
            <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
            <p>The Commission committed to taking the following actions:</p>
            <ul>
                <li>reinforcing implementation of EU water quality legislation;</li>
                <li>launching an EU-wide public consultation on the Drinking Water Directive;</li>
                <li>improving transparency for urban wastewater data management;</li>
                <li>bringing about a more structured dialogue between stakeholders;</li>
                <li>cooperating with existing initiatives to provide benchmarks;</li>
            </ul>
        </html>
        """
        soup3 = BeautifulSoup(html3, 'html.parser')
        extractor3 = LegislativeOutcomeExtractor(registration_number='2012/000003')
        result3 = extractor3.extract_non_legislative_action(soup3)
        
        assert result3 is not None, "Should extract from list items"
        result_list3 = json.loads(result3)
        assert len(result_list3) >= 4, "Should extract multiple list items"
        
        types3 = [action['type'] for action in result_list3]
        assert 'Policy Implementation' in types3
        assert 'Impact Assessment and Consultation' in types3
        assert 'Data Collection and Transparency' in types3
        assert 'Stakeholder Dialogue' in types3
        
        # Test case 4: Roadmap and strategy actions
        html4 = """
        <html>
            <h2 id="Follow-up">Follow-up</h2>
            <p>In the second half of 2023, the Commission started work on a roadmap to phase out animal testing.</p>
            <p>The strategic plan of Horizon Europe includes alternatives to animal testing for 2025-2027.</p>
            <p>The Commission will work on mechanisms to ensure compliance with fundamental rights in EU funds.</p>
        </html>
        """
        soup4 = BeautifulSoup(html4, 'html.parser')
        extractor4 = LegislativeOutcomeExtractor(registration_number='2021/000006')
        result4 = extractor4.extract_non_legislative_action(soup4)
        
        assert result4 is not None
        result_list4 = json.loads(result4)
        
        types4 = [action['type'] for action in result_list4]
        assert 'Policy Roadmap and Strategy' in types4
        
        # Test case 5: International cooperation actions
        html5 = """
        <html>
            <h2 id="Follow-up">Follow-up</h2>
            <p>At the international level, the Commission is reaching out to international partners with a view to achieve a worldwide ban.</p>
            <p>The Commission will advocate universal access to safe drinking water as a priority for Sustainable Development Goals.</p>
            <p>High-level dialogue with China, US, Japan was conducted in 2024.</p>
        </html>
        """
        soup5 = BeautifulSoup(html5, 'html.parser')
        extractor5 = LegislativeOutcomeExtractor(registration_number='2020/000001')
        result5 = extractor5.extract_non_legislative_action(soup5)
        
        assert result5 is not None
        result_list5 = json.loads(result5)
        
        types5 = [action['type'] for action in result_list5]
        assert 'International Cooperation' in types5
        
        # Test case 6: No non-legislative actions (only legislative)
        html6 = """
        <html>
            <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
            <p>The Commission adopted a proposal for a regulation on 10 May 2023.</p>
            <h2 id="Follow-up">Follow-up</h2>
            <p>The regulation entered into force on 27 March 2024.</p>
        </html>
        """
        soup6 = BeautifulSoup(html6, 'html.parser')
        extractor6 = LegislativeOutcomeExtractor(registration_number='2023/000003')
        result6 = extractor6.extract_non_legislative_action(soup6)
        
        assert result6 is None, "Should return None when only legislative actions present"
        
        # Test case 7: Duplicate actions should be removed
        html7 = """
        <html>
            <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
            <p>The Commission will monitor compliance with existing legislation.</p>
            <h2 id="Follow-up">Follow-up</h2>
            <p>The Commission will monitor compliance with existing legislation.</p>
        </html>
        """
        soup7 = BeautifulSoup(html7, 'html.parser')
        extractor7 = LegislativeOutcomeExtractor(registration_number='2023/000004')
        result7 = extractor7.extract_non_legislative_action(soup7)
        
        assert result7 is not None
        result_list7 = json.loads(result7)
        assert len(result_list7) == 1, "Should remove duplicate actions"
        
        # Test case 8: No Answer or Follow-up section
        html8 = """
        <html>
            <h2 id="Submission-and-examination">Submission and examination</h2>
            <p>Some procedural content.</p>
        </html>
        """
        soup8 = BeautifulSoup(html8, 'html.parser')
        extractor8 = LegislativeOutcomeExtractor(registration_number='2099/999999')
        result8 = extractor8.extract_non_legislative_action(soup8)
        
        assert result8 is None, "Should return None when no relevant sections found"
        
        # Test case 9: Mixed with EFSA scientific opinions
        html9 = """
        <html>
            <h2 id="Follow-up">Follow-up</h2>
            <p>EFSA scientific opinions have been published concerning welfare risks in October 2021.</p>
            <p>The Commission organised a workshop on alternative approaches on 10-11 April 2025.</p>
        </html>
        """
        soup9 = BeautifulSoup(html9, 'html.parser')
        extractor9 = LegislativeOutcomeExtractor(registration_number='2018/000004')
        result9 = extractor9.extract_non_legislative_action(soup9)
        
        assert result9 is not None
        result_list9 = json.loads(result9)
        
        types9 = [action['type'] for action in result_list9]
        assert 'Scientific Activity' in types9
        
        # Verify dates are in correct format
        dated9 = [a for a in result_list9 if 'date' in a]
        assert len(dated9) >= 1
        assert any('2021' in a.get('date', '') for a in dated9)
        assert any('2025' in a.get('date', '') for a in dated9)
        
        # Test case 10: Actions with specific date formats
        html10 = """
        <html>
            <h2 id="Follow-up">Follow-up</h2>
            <p>A public consultation was carried out from 15 October 2021 to 21 January 2022.</p>
            <p>The report was published in January 2024.</p>
            <p>A colloquium was co-organised in November 2023.</p>
            <p>The Commission will take action by the end of 2026.</p>
        </html>
        """
        soup10 = BeautifulSoup(html10, 'html.parser')
        extractor10 = LegislativeOutcomeExtractor(registration_number='2017/000004')
        result10 = extractor10.extract_non_legislative_action(soup10)
        
        assert result10 is not None
        result_list10 = json.loads(result10)
        
        # Check various date formats are extracted
        dates10 = [a.get('date') for a in result_list10 if 'date' in a]
        assert len(dates10) == 3, "Should extract dates from different formats"
        assert any('2021' in str(d) for d in dates10)
        assert any('2024' in str(d) for d in dates10)
        assert any('2023' in str(d) for d in dates10)
        
        # Test case 11: Section headers should be filtered out
        html11 = """
        <html>
            <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>

            <p><strong>Implementation and review of existing EU legislation:</strong></p>
            <ul>
                <li>Subsequent implementation reports were published in 2015, 2019 and 2021.</li>
            </ul>

            <p><strong>Transparency and benchmarking:</strong></p>
            <ul>
                <li>Stakeholder meetings on benchmarking took place on 09/09/2014 in Brussels.</li>
            </ul>

            <p><strong>International cooperation:</strong></p>
            <p>The Commission is working with international partners.</p>

            <p><strong>Monitoring activities:</strong></p>
            <p>The Commission will monitor compliance with existing legislation.</p>
        </html>
        """

        soup11 = BeautifulSoup(html11, 'html.parser')
        extractor11 = LegislativeOutcomeExtractor(registration_number='2012/000003')
        result11 = extractor11.extract_non_legislative_action(soup11)

        assert result11 is not None, "Should extract actions"
        result_list11 = json.loads(result11)

        # Check that section headers are NOT in the results
        descriptions11 = [action['description'] for action in result_list11]

        # These should NOT be in results (they are section headers ending with ':')
        assert not any('Implementation and review of existing EU legislation:' == desc 
                      for desc in descriptions11), "Section header should be filtered out"
        assert not any('Transparency and benchmarking:' == desc 
                      for desc in descriptions11), "Section header should be filtered out"
        assert not any('International cooperation:' == desc 
                      for desc in descriptions11), "Section header should be filtered out"
        assert not any('Monitoring activities:' == desc 
                      for desc in descriptions11), "Section header should be filtered out"

        # These SHOULD be in results (actual actions, not headers)
        assert any('implementation reports were published' in desc.lower() 
                  for desc in descriptions11), "Actual action should be extracted"
        assert any('stakeholder meetings' in desc.lower() 
                  for desc in descriptions11), "Actual action should be extracted"
        assert any('working with international partners' in desc.lower() 
                  for desc in descriptions11), "Actual action should be extracted"
        assert any('monitor compliance' in desc.lower() 
                  for desc in descriptions11), "Actual action should be extracted"

        # Verify we have exactly 4 actions (not 8 with headers included)
        assert len(result_list11) == 4, f"Should have 4 actions, not {len(result_list11)} - section headers should be filtered"

        # Additional check: No description should end with ':' and be < 100 chars (section header pattern)
        for action in result_list11:
            desc = action['description']
            if desc.endswith(':'):
                assert len(desc) >= 100, f"Short text ending with ':' should be filtered: {desc}"

class TestFollowUpActivities:
    """Tests for follow-up activities extraction."""
    
    @classmethod
    def setup_class(cls):
        """Setup parser instance."""
        logger = ResponsesExtractorLogger().setup()
        cls.parser = ECIResponseHTMLParser(logger=logger)
    
    def test_has_followup_section_detection(self):
        """Test detection of follow-up section presence."""
        # Placeholder - implement when HTML structure is known
        pass
    
    def test_followup_events_extraction(self):
        """Test extraction of follow-up events information."""
        # Placeholder - implement when HTML structure is known
        pass
    
    def test_has_roadmap_detection(self):
        """Test detection of roadmap presence."""
        # Placeholder - implement when HTML structure is known
        pass
    
    def test_has_workshop_detection(self):
        """Test detection of workshop activities."""
        # Placeholder - implement when HTML structure is known
        pass
    
    def test_partnership_programs_extraction(self):
        """Test extraction of partnership programs information."""
        # Placeholder - implement when HTML structure is known
        pass
    
    def test_court_cases_referenced(self):
        """Test extraction of Court of Justice case numbers."""
        # Placeholder - implement when HTML structure is known
        pass
    
    def test_latest_update_date_extraction(self):
        """Test extraction of most recent date from follow-up section."""
        # Placeholder - implement when HTML structure is known
        pass


class TestMultimediaDocumentation:
    """Tests for multimedia and documentation extraction."""
    
    @classmethod
    def setup_class(cls):
        """Setup parser instance."""
        logger = ResponsesExtractorLogger().setup()
        cls.parser = ECIResponseHTMLParser(logger=logger)
    
    def test_commission_factsheet_url(self):
        """Test extraction of Commission factsheet PDF URL."""
        
        # Test case 1: Standard factsheet with valid download link
        html_1 = """
        <html>
            <div class="ecl-file" data-ecl-file="">
                <div class="ecl-file__container">
                    <picture class="ecl-picture ecl-file__picture">
                        <img alt="Picture of the first page of the factsheet" 
                            src="https://citizens-initiative.europa.eu/sites/default/files/thumbnail.png"/>
                    </picture>
                    <div class="ecl-file__info">
                        <div class="ecl-file__title">Factsheet - Successful Initiatives - Fur Free Europe</div>
                        <div class="ecl-file__language">English</div>
                        <div class="ecl-file__meta">(234.58 KB - PDF)</div>
                    </div>
                    <div class="ecl-file__action">
                        <a href="https://citizens-initiative.europa.eu/sites/default/files/2023-12/Factsheet.pdf" 
                        class="ecl-link ecl-link--standalone ecl-link--icon ecl-file__download">
                            Download
                        </a>
                    </div>
                </div>
            </div>
        </html>
        """
        
        soup_1 = BeautifulSoup(html_1, 'html.parser')
        parser_1 = ECIResponseHTMLParser(soup_1)
        parser_1.registration_number = "2022/000002"
        
        result_1 = parser_1.multimedia_docs.extract_commission_factsheet_url(soup_1)
        
        assert result_1 is not None
        assert result_1 == "https://citizens-initiative.europa.eu/sites/default/files/2023-12/Factsheet.pdf"
        assert "citizens-initiative.europa.eu" in result_1
        assert result_1.endswith(".pdf")
        
        # Test case 2: No factsheet element present (returns None)
        html_2 = """
        <html>
            <div class="ecl-file">
                <div class="ecl-file__container">
                    <div class="ecl-file__info">
                        <div class="ecl-file__title">Communication Document</div>
                        <div class="ecl-file__language">English</div>
                    </div>
                    <div class="ecl-file__action">
                        <a href="https://ec.europa.eu/transparency/documents-register/detail?ref=COM(2023)123" 
                        class="ecl-file__download">
                            Download
                        </a>
                    </div>
                </div>
            </div>
        </html>
        """
        
        soup_2 = BeautifulSoup(html_2, 'html.parser')
        parser_2 = ECIResponseHTMLParser(soup_2)
        parser_2.registration_number = "2012/000003"
        
        result_2 = parser_2.multimedia_docs.extract_commission_factsheet_url(soup_2)
        
        assert result_2 is None
        
        # Test case 3: Factsheet title exists but download link is missing (error)
        html_3 = """
        <html>
            <div class="ecl-file">
                <div class="ecl-file__container">
                    <div class="ecl-file__info">
                        <div class="ecl-file__title">Factsheet - Save Bees and Farmers</div>
                        <div class="ecl-file__language">English</div>
                    </div>
                    <div class="ecl-file__action">
                        <!-- No download link here -->
                    </div>
                </div>
            </div>
        </html>
        """
        
        soup_3 = BeautifulSoup(html_3, 'html.parser')
        parser_3 = ECIResponseHTMLParser(soup_3)
        parser_3.registration_number = "2019/000016"
        
        with pytest.raises(ValueError, match="Factsheet element found but download link is missing for 2019/000016"):
            parser_3.multimedia_docs.extract_commission_factsheet_url(soup_3)
        
        # Test case 4: Factsheet exists but href is empty (error)
        html_4 = """
        <html>
            <div class="ecl-file">
                <div class="ecl-file__container">
                    <div class="ecl-file__info">
                        <div class="ecl-file__title">Factsheet - End Cage Age</div>
                        <div class="ecl-file__language">English</div>
                    </div>
                    <div class="ecl-file__action">
                        <a href="" class="ecl-link ecl-file__download">
                            Download
                        </a>
                    </div>
                </div>
            </div>
        </html>
        """
        
        soup_4 = BeautifulSoup(html_4, 'html.parser')
        parser_4 = ECIResponseHTMLParser(soup_4)
        parser_4.registration_number = "2018/000004"
        
        with pytest.raises(ValueError, match="Factsheet download link found but href is empty for 2018/000004"):
            parser_4.multimedia_docs.extract_commission_factsheet_url(soup_4)
        
        # Test case 5: Multiple file divs, only one is factsheet
        html_5 = """
        <html>
            <div class="ecl-file">
                <div class="ecl-file__container">
                    <div class="ecl-file__info">
                        <div class="ecl-file__title">Communication Document</div>
                    </div>
                    <div class="ecl-file__action">
                        <a href="https://ec.europa.eu/transparency/documents-register/communication.pdf" 
                        class="ecl-file__download">Download</a>
                    </div>
                </div>
            </div>
            <div class="ecl-file">
                <div class="ecl-file__container">
                    <div class="ecl-file__info">
                        <div class="ecl-file__title">Annex Document</div>
                    </div>
                    <div class="ecl-file__action">
                        <a href="https://ec.europa.eu/transparency/documents-register/annex.pdf" 
                        class="ecl-file__download">Download</a>
                    </div>
                </div>
            </div>
            <div class="ecl-file">
                <div class="ecl-file__container">
                    <div class="ecl-file__info">
                        <div class="ecl-file__title">Factsheet - Minority SafePack</div>
                        <div class="ecl-file__language">English</div>
                    </div>
                    <div class="ecl-file__action">
                        <a href="https://citizens-initiative.europa.eu/sites/default/files/factsheet_minority.pdf" 
                        class="ecl-file__download">Download</a>
                    </div>
                </div>
            </div>
        </html>
        """
        
        soup_5 = BeautifulSoup(html_5, 'html.parser')
        parser_5 = ECIResponseHTMLParser(soup_5)
        parser_5.registration_number = "2017/000004"
        
        result_5 = parser_5.multimedia_docs.extract_commission_factsheet_url(soup_5)
        
        assert result_5 is not None
        assert "factsheet_minority.pdf" in result_5
        # Should return the factsheet, not the other documents
        assert "communication.pdf" not in result_5
        assert "annex.pdf" not in result_5
        
        # Test case 6: Case-insensitive factsheet detection
        html_6 = """
        <html>
            <div class="ecl-file">
                <div class="ecl-file__container">
                    <div class="ecl-file__info">
                        <div class="ecl-file__title">FACTSHEET - Stop Finning</div>
                    </div>
                    <div class="ecl-file__action">
                        <a href="https://citizens-initiative.europa.eu/sites/default/files/stop_finning.pdf" 
                        class="ecl-file__download">Download</a>
                    </div>
                </div>
            </div>
        </html>
        """
        
        soup_6 = BeautifulSoup(html_6, 'html.parser')
        parser_6 = ECIResponseHTMLParser(soup_6)
        parser_6.registration_number = "2020/000001"
        
        result_6 = parser_6.multimedia_docs.extract_commission_factsheet_url(soup_6)
        
        assert result_6 is not None
        assert "stop_finning.pdf" in result_6
        
        # Test case 7: Factsheet with translations (should only get main English version)
        html_7 = """
        <html>
            <div class="ecl-file ecl-file--has-translation">
                <div class="ecl-file__container">
                    <div class="ecl-file__info">
                        <div class="ecl-file__title">Factsheet - Save Cruelty Free Cosmetics</div>
                        <div class="ecl-file__language">English</div>
                        <div class="ecl-file__meta">(1.31 MB - PDF)</div>
                    </div>
                    <div class="ecl-file__action">
                        <a href="https://citizens-initiative.europa.eu/sites/default/files/2023-08/factsheet_EN.pdf" 
                        class="ecl-link ecl-file__download">Download</a>
                    </div>
                </div>
                <div class="ecl-file__translation-container">
                    <button class="ecl-file__translation-toggle">Available translations (23)</button>
                    <ul class="ecl-file__translation-list">
                        <li class="ecl-file__translation-item">
                            <a href="https://citizens-initiative.europa.eu/sites/default/files/2023-08/factsheet_BG.pdf" 
                            class="ecl-link ecl-file__translation-download">
                                <div class="ecl-file__language" lang="bg">български</div>
                            </a>
                        </li>
                        <li class="ecl-file__translation-item">
                            <a href="https://citizens-initiative.europa.eu/sites/default/files/2023-08/factsheet_ES.pdf" 
                            class="ecl-link ecl-file__translation-download">
                                <div class="ecl-file__language" lang="es">Español</div>
                            </a>
                        </li>
                    </ul>
                </div>
            </div>
        </html>
        """
        
        soup_7 = BeautifulSoup(html_7, 'html.parser')
        parser_7 = ECIResponseHTMLParser(soup_7)
        parser_7.registration_number = "2021/000006"
        
        result_7 = parser_7.multimedia_docs.extract_commission_factsheet_url(soup_7)
        
        assert result_7 is not None
        assert "factsheet_EN.pdf" in result_7
        # Should not return translations
        assert "factsheet_BG.pdf" not in result_7
        assert "factsheet_ES.pdf" not in result_7
        
        # Test case 8: Empty page (no ecl-file divs at all)
        html_8 = """
        <html>
            <body>
                <h2>Submission and examination</h2>
                <p>The initiative was submitted on some date.</p>
            </body>
        </html>
        """
        
        soup_8 = BeautifulSoup(html_8, 'html.parser')
        parser_8 = ECIResponseHTMLParser(soup_8)
        parser_8.registration_number = "2012/000005"
        
        result_8 = parser_8.multimedia_docs.extract_commission_factsheet_url(soup_8)
        
        assert result_8 is None

    def test_dedicated_website_detection(self):
        """Test detection of dedicated campaign website."""
        html = '<html><body></body></html>'
        soup = BeautifulSoup(html, 'html.parser')
        
        result = self.parser.multimedia_docs.extract_has_dedicated_website(soup)
        assert result == False, "Should return False by default"


class TestStructuralAnalysis:
    """Tests for structural analysis fields."""
    
    @classmethod
    def setup_class(cls):
        """Setup parser instance."""
        logger = ResponsesExtractorLogger().setup()
        cls.parser = ECIResponseHTMLParser(logger=logger)
    
    def test_related_eu_legislation(self):
        """Test extraction of related EU legislation references."""
        # Placeholder - implement when HTML structure is known
        pass
    
    def test_petition_platforms_used(self):
        """Test extraction of petition platforms mentioned."""
        # Placeholder - implement when HTML structure is known
        pass
    
    def test_follow_up_duration_calculation(self):
        """Test calculation of follow-up duration in months."""
        # Placeholder - implement when date parsing is implemented
        pass


class TestHelperMethods:
    """Tests for helper methods."""
    
    @classmethod
    def setup_class(cls):
        """Setup parser instance."""
        logger = ResponsesExtractorLogger().setup()
        cls.parser = ECIResponseHTMLParser(logger=logger)
    
    def test_parse_date_iso_format(self):
        """Test date parsing to ISO format."""
        # Placeholder - implement when date parsing is implemented
        pass
    
    def test_clean_text_whitespace_removal(self):
        """Test text cleaning removes extra whitespace."""
        # Placeholder - implement when text cleaning is implemented
        pass
    
    def test_extract_all_video_urls(self):
        """Test extraction of all video URLs from page."""
        # Placeholder - implement when HTML structure is known
        pass
