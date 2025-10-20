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
from ECI_initiatives.extractor.responses.parser import ECIResponseHTMLParser
from ECI_initiatives.extractor.responses.responses_logger import ResponsesExtractorLogger


class TestResponseURLExtraction:
    """Tests for response URL extraction from HTML."""
    
    @classmethod
    def setup_class(cls):
        """Setup parser instance."""
        logger = ResponsesExtractorLogger().setup()
        cls.parser = ECIResponseHTMLParser(logger=logger)
    
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
        
        soup = BeautifulSoup(html, 'html.parser')
        url = self.parser._extract_response_url(soup)
        
        expected_url = "https://citizens-initiative.europa.eu/initiatives/details/2020/000001/stop-finning-stop-the-trade_en"
        assert url == expected_url, \
            f"Expected '{expected_url}', got '{url}'"

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
        
        soup = BeautifulSoup(html, 'html.parser')
        url = self.parser._extract_response_url(soup)
        
        # Should extract the active (en) link, not the others
        assert "_en" in url, \
            "Should extract the active English language link"
        assert url.endswith("_en"), \
            "URL should end with _en language code"

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
        
        soup = BeautifulSoup(html, 'html.parser')
        url = self.parser._extract_response_url(soup)
        
        expected_url = "https://citizens-initiative.europa.eu/initiatives/details/2012/000003/water-sanitation_en"
        assert url == expected_url, \
            "Should fallback to hreflang='en' link when active class is missing"

    def test_extract_response_url_from_canonical_fallback(self):
        """Test fallback to canonical link when language links are missing."""
        
        html = '''
        <html>
            <head>
                <link rel="canonical" href="https://citizens-initiative.europa.eu/cohesion-policy-equality-regions_en" />
            </head>
        </html>
        '''
        
        soup = BeautifulSoup(html, 'html.parser')
        url = self.parser._extract_response_url(soup)
        
        expected_url = "https://citizens-initiative.europa.eu/cohesion-policy-equality-regions_en"
        assert url == expected_url, \
            f"Should fallback to canonical link. Expected '{expected_url}', got '{url}'"

    def test_extract_response_url_handles_relative_urls(self):
        """Test that relative URLs are converted to absolute URLs."""
        
        html = '''
        <html>
            <head>
                <link rel="canonical" href="/fur-free-europe_en" />
            </head>
        </html>
        '''
        
        soup = BeautifulSoup(html, 'html.parser')
        url = self.parser._extract_response_url(soup)
        
        expected_url = "https://citizens-initiative.europa.eu/fur-free-europe_en"
        assert url == expected_url, \
            f"Should convert relative URL to absolute. Expected '{expected_url}', got '{url}'"

    def test_extract_response_url_missing_all_methods(self):
        """Test that ValueError is raised when no URL sources are found."""
        
        html = '''
        <html>
            <head></head>
            <body>No URL sources</body>
        </html>
        '''
        
        soup = BeautifulSoup(html, 'html.parser')
        
        with pytest.raises(ValueError, match="Response URL not found"):
            self.parser._extract_response_url(soup)


class TestInitiativeURLExtraction:
    """Tests for initiative URL extraction from HTML."""
    
    @classmethod
    def setup_class(cls):
        """Setup parser instance."""
        logger = ResponsesExtractorLogger().setup()
        cls.parser = ECIResponseHTMLParser(logger=logger)
    
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
        
        soup = BeautifulSoup(html, 'html.parser')
        url = self.parser._extract_initiative_url(soup)
        
        expected_url = "https://citizens-initiative.europa.eu/initiatives/details/2012/000003_en"
        assert url == expected_url, \
            f"Expected URL '{expected_url}', got '{url}'"

    def test_extract_initiative_url_with_whitespace(self):
        """Test extraction works with whitespace in breadcrumb text."""
        
        html = '''
        <a href="/initiatives/details/2019/000007_en" 
           class="ecl-breadcrumb__link">
           
           Initiative detail
           
        </a>
        '''
        
        soup = BeautifulSoup(html, 'html.parser')
        url = self.parser._extract_initiative_url(soup)
        
        expected_url = "https://citizens-initiative.europa.eu/initiatives/details/2019/000007_en"
        assert url == expected_url, \
            f"Should handle whitespace correctly. Expected '{expected_url}', got '{url}'"

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
        
        soup = BeautifulSoup(html, 'html.parser')
        url = self.parser._extract_initiative_url(soup)
        
        expected_url = "https://citizens-initiative.europa.eu/initiatives/details/2017/000002_en"
        assert url == expected_url, \
            f"Expected '{expected_url}', got '{url}'"

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
        
        soup = BeautifulSoup(html, 'html.parser')
        url = self.parser._extract_initiative_url(soup)
        
        expected_url = "https://citizens-initiative.europa.eu/initiatives/details/2022/000002_en"
        assert url == expected_url, \
            "Should find link with text content and skip empty links"

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
        
        soup = BeautifulSoup(html, 'html.parser')
        url = self.parser._extract_initiative_url(soup)
        
        # Should match English version only
        assert url.endswith("_en"), \
            "Should only match English (_en) URL"
        expected_url = "https://citizens-initiative.europa.eu/initiatives/details/2020/000001_en"
        assert url == expected_url, \
            f"Expected '{expected_url}', got '{url}'"

    def test_extract_initiative_url_missing(self):
        """Test that ValueError is raised when no initiative URL is found."""
        
        html = '''
        <html>
            <body>No initiative URL here</body>
        </html>
        '''
        
        soup = BeautifulSoup(html, 'html.parser')
        
        with pytest.raises(ValueError, match="Initiative URL not found"):
            self.parser._extract_initiative_url(soup)


class TestSubmissionDataExtraction:
    """Tests for submission and verification data extraction."""
    
    @classmethod
    def setup_class(cls):
        """Setup parser instance."""
        logger = ResponsesExtractorLogger().setup()
        cls.parser = ECIResponseHTMLParser(logger=logger)
    
    def test_submission_date_extraction(self):
        """Test extraction of submission date."""
        
        # Test Case 1: DD Month YYYY format (most common)
        html = '''
        <html>
            <body>
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>
                    <a href="https://citizens-initiative.europa.eu/initiatives/details/2017/000002_en">
                        Ban glyphosate and protect people and the environment from toxic pesticides
                    </a>
                    was submitted to the Commission on 6 October 2017, having gathered 1,070,865 statements of support.
                </p>
            </body>
        </html>
        '''
        
        soup = BeautifulSoup(html, 'html.parser')
        date = self.parser._extract_submission_date(soup)
        
        from datetime import date as date_type
        expected_date = date_type(2017, 10, 6)
        assert date == expected_date, \
            f"Expected date {expected_date}, got {date}"
        assert isinstance(date, date_type), \
            "Should return datetime.date object"


        # Test Case 2: DD/MM/YYYY format
        html_ddmmyyyy = '''
        <html>
            <body>
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>
                    One of us was submitted to the Commission on 28/02/2014 having gathered 1,721,626 statements of support.
                </p>
            </body>
        </html>
        '''
        
        soup = BeautifulSoup(html_ddmmyyyy, 'html.parser')
        date = self.parser._extract_submission_date(soup)
        
        expected_date = date_type(2014, 2, 28)
        assert date == expected_date, \
            f"Expected date {expected_date}, got {date}"


        # Test Case 3: With "European Commission" variation
        html_european = '''
        <html>
            <body>
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>
                    The 'Cohesion policy' initiative was submitted to the European Commission on 4 March 2025,
                    after having gathered 1,269,351 verified statements of support.
                </p>
            </body>
        </html>
        '''
        
        soup = BeautifulSoup(html_european, 'html.parser')
        date = self.parser._extract_submission_date(soup)
        
        expected_date = date_type(2025, 3, 4)
        assert date == expected_date, \
            f"Expected date {expected_date}, got {date}"


        # Test Case 4: Missing date should raise ValueError
        html_no_date = '''
        <html>
            <body>
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>
                    No date information here.
                </p>
            </body>
        </html>
        '''
        
        soup = BeautifulSoup(html_no_date, 'html.parser')
        
        # Mock the registration_number instance variable
        self.parser.registration_number = "2099/999999"

        with pytest.raises(ValueError, match="No submission date found for initiative 2099/999999"):
            self.parser._extract_submission_date(soup)


    def test_submission_news_url(self):
        """Test extraction of submission news URL."""
        
        # Test Case 1: Standard "press release" link with presscorner URL
        html = '''
        <html>
            <body>
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>
                    <a href="https://citizens-initiative.europa.eu/initiatives/details/2012/000003_en">
                        Right2Water
                    </a>
                    was submitted to the Commission on 20 December 2013. See
                    <a href="https://ec.europa.eu/commission/presscorner/detail/en/mex_13_1223">
                        press release
                    </a>.
                </p>
            </body>
        </html>
        '''
        
        soup = BeautifulSoup(html, 'html.parser')
        url = self.parser._extract_submission_news_url(soup)
        
        expected_url = "https://ec.europa.eu/commission/presscorner/detail/en/mex_13_1223"
        assert url == expected_url, \
            f"Expected URL '{expected_url}', got '{url}'"


        # Test Case 2: "press announcement" variation
        html_announcement = '''
        <html>
            <body>
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>
                    The 'Stop Finning' initiative was submitted to the Commission on 11 January 2023. See
                    <a href="https://ec.europa.eu/commission/presscorner/detail/en/mex_23_143">
                        press announcement
                    </a>.
                </p>
            </body>
        </html>
        '''
        
        soup = BeautifulSoup(html_announcement, 'html.parser')
        url = self.parser._extract_submission_news_url(soup)
        
        expected_url = "https://ec.europa.eu/commission/presscorner/detail/en/mex_23_143"
        assert url == expected_url, \
            f"Expected URL '{expected_url}', got '{url}'"


        # Test Case 3: "European Commission news" variation
        html_news = '''
        <html>
            <body>
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>
                    The initiative was submitted to the European Commission on 4 March 2025. See
                    <a href="https://ec.europa.eu/commission/presscorner/detail/en/mex_25_680">
                        European Commission news
                    </a>.
                </p>
            </body>
        </html>
        '''
        
        soup = BeautifulSoup(html_news, 'html.parser')
        url = self.parser._extract_submission_news_url(soup)
        
        expected_url = "https://ec.europa.eu/commission/presscorner/detail/en/mex_25_680"
        assert url == expected_url, \
            f"Expected URL '{expected_url}', got '{url}'"


        # Test Case 4: Old europa.eu/rapid format
        html_rapid = '''
        <html>
            <body>
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>
                    Ban glyphosate was submitted to the Commission on 6 October 2017. See
                    <a href="http://europa.eu/rapid/press-release_MEX-17-3748_en.htm">
                        press release
                    </a>.
                </p>
            </body>
        </html>
        '''
        
        soup = BeautifulSoup(html_rapid, 'html.parser')
        url = self.parser._extract_submission_news_url(soup)
        
        expected_url = "http://europa.eu/rapid/press-release_MEX-17-3748_en.htm"
        assert url == expected_url, \
            f"Expected URL '{expected_url}', got '{url}'"


        # Test Case 5: Multiple links - should skip initiative link and get press link
        html_multiple = '''
        <html>
            <body>
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>
                    <a href="https://citizens-initiative.europa.eu/initiatives/details/2018/000004_en">
                        'End the Cage Age'
                    </a>
                    initiative was submitted to the Commission on 2 October 2020. See
                    <a href="https://ec.europa.eu/commission/presscorner/detail/en/MEX_20_1810">
                        press release
                    </a>.
                </p>
            </body>
        </html>
        '''
        
        soup = BeautifulSoup(html_multiple, 'html.parser')
        url = self.parser._extract_submission_news_url(soup)
        
        # Should get the presscorner URL, not the initiative URL
        assert 'presscorner' in url, \
            "Should extract presscorner URL, not initiative URL"
        assert url == "https://ec.europa.eu/commission/presscorner/detail/en/MEX_20_1810", \
            "Should extract correct press release URL"


        # Test Case 6: Missing news URL should return None
        html_no_news = '''
        <html>
            <body>
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>
                    <a href="https://citizens-initiative.europa.eu/initiatives/details/2020/000001_en">
                        Initiative
                    </a>
                    was submitted but no press release link here.
                </p>
            </body>
        </html>
        '''
        
        soup = BeautifulSoup(html_no_news, 'html.parser')

        with pytest.raises(ValueError, match="No submission news URL found for initiative"):
            self.parser._extract_submission_news_url(soup)


        # Test Case 7: Case insensitive matching for link text
        html_case = '''
        <html>
            <body>
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>
                    Initiative submitted. See
                    <a href="https://ec.europa.eu/commission/presscorner/detail/en/mex_20_1000">
                        PRESS RELEASE
                    </a>.
                </p>
            </body>
        </html>
        '''
        
        soup = BeautifulSoup(html_case, 'html.parser')
        url = self.parser._extract_submission_news_url(soup)
        
        assert url is not None, \
            "Should match 'PRESS RELEASE' (case insensitive)"
        assert url == "https://ec.europa.eu/commission/presscorner/detail/en/mex_20_1000"



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
                    parser._extract_commission_meeting_date(soup)
                assert "commission meeting date" in str(exc_info.value).lower(), f"Failed for test case: {test_id}"

            else:
                # Normal case - should return expected value
                result = parser._extract_commission_meeting_date(soup)
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
                result = parser._extract_submission_text(soup)
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
                    parser._extract_commission_officials_met(soup)
                assert "commission official" in str(exc_info.value).lower(), f"Failed for test case: {test_id}"
            else:
                # Normal case - should return expected value
                try:
                    result = parser._extract_commission_officials_met(soup)
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
                    parser._extract_parliament_hearing_date(soup)
                assert "parliament hearing date" in str(exc_info.value).lower(), f"Failed for test case: {test_id}"
            else:
                # Normal case - should return expected value
                try:
                    result = parser._extract_parliament_hearing_date(soup)
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
    
    def test_parliament_hearing_recording_url(self):
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
                    parser._extract_parliament_hearing_recording_url(soup)
            else:
                result = parser._extract_parliament_hearing_recording_url(soup)
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
        result_1 = parser_1._extract_plenary_debate_date(soup_1)
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
        result_2 = parser_2._extract_plenary_debate_date(soup_2)
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
        result_3 = parser_3._extract_plenary_debate_date(soup_3)
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
        result_4 = parser_4._extract_plenary_debate_date(soup_4)
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
        result_5 = parser_5._extract_plenary_debate_date(soup_5)
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
        result_6 = parser_6._extract_plenary_debate_date(soup_6)
        assert result_6 == "14-12-2020"

    def test_plenary_debate_recording_url(self):
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
        result_1 = parser_1._extract_plenary_debate_recording_url(soup_1)
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
        result_2 = parser_2._extract_plenary_debate_recording_url(soup_2)
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
        result_3 = parser_3._extract_plenary_debate_recording_url(soup_3)
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
        result_4 = parser_4._extract_plenary_debate_recording_url(soup_4)
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
        result_5 = parser_5._extract_plenary_debate_recording_url(soup_5)
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
        result_6 = parser_6._extract_plenary_debate_recording_url(soup_6)
        assert result_6 is None

    def test_commission_communication_date(self):
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
        result_1 = parser_1._extract_commission_communication_date(soup_1)
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
        result_2 = parser_2._extract_commission_communication_date(soup_2)
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
        result_3 = parser_3._extract_commission_communication_date(soup_3)
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
        result_4 = parser_4._extract_commission_communication_date(soup_4)
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
        result_5 = parser_5._extract_commission_communication_date(soup_5)
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
        result_6 = parser_6._extract_commission_communication_date(soup_6)
        assert result_6 is None

    
    def test_commission_communication_url(self):
        """Test extraction of Commission Communication PDF URL."""
        # Placeholder - implement when HTML structure is known
        pass


class TestCommissionResponseContent:
    """Tests for Commission response content extraction."""
    
    @classmethod
    def setup_class(cls):
        """Setup parser instance."""
        logger = ResponsesExtractorLogger().setup()
        cls.parser = ECIResponseHTMLParser(logger=logger)
    
    def test_communication_main_conclusion(self):
        """Test extraction of main conclusions from Communication."""
        # Placeholder - implement when HTML structure is known
        pass
    
    def test_legislative_proposal_status(self):
        """Test extraction of legislative proposal status."""
        # Placeholder - implement when HTML structure is known
        pass
    
    def test_commission_response_summary(self):
        """Test extraction of Commission response summary."""
        # Placeholder - implement when HTML structure is known
        pass


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
    
    def test_followup_meeting_date(self):
        """Test extraction of follow-up meeting date."""
        # Placeholder - implement when HTML structure is known
        pass
    
    def test_roadmap_launched_detection(self):
        """Test detection of roadmap launch."""
        # Placeholder - implement when HTML structure is known
        pass
    
    def test_workshop_conference_dates_json_format(self):
        """Test that workshop dates are returned as valid JSON array."""
        # Placeholder - implement when HTML structure is known
        pass
    
    def test_court_cases_referenced(self):
        """Test extraction of Court of Justice case numbers."""
        # Placeholder - implement when HTML structure is known
        pass


class TestMultimediaDocumentation:
    """Tests for multimedia and documentation extraction."""
    
    @classmethod
    def setup_class(cls):
        """Setup parser instance."""
        logger = ResponsesExtractorLogger().setup()
        cls.parser = ECIResponseHTMLParser(logger=logger)
    
    def test_factsheet_url_extraction(self):
        """Test extraction of factsheet PDF URL."""
        # Placeholder - implement when HTML structure is known
        pass
    
    def test_video_recording_count(self):
        """Test counting of video recording links."""
        # Placeholder - implement when HTML structure is known
        pass
    
    def test_dedicated_website_detection(self):
        """Test detection of dedicated campaign website."""
        html = '<html><body></body></html>'
        soup = BeautifulSoup(html, 'html.parser')
        
        result = self.parser._extract_has_dedicated_website(soup)
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
