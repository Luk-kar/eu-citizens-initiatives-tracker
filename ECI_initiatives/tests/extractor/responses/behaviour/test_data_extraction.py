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
        # Placeholder - implement when HTML structure is known
        pass
    
    def test_verified_signatures_count(self):
        """Test extraction of verified signatures count."""
        # Placeholder - implement when HTML structure is known
        pass
    
    def test_member_states_threshold(self):
        """Test extraction of member states threshold count."""
        # Placeholder - implement when HTML structure is known
        pass
    
    def test_submission_news_url(self):
        """Test extraction of submission news URL."""
        # Placeholder - implement when HTML structure is known
        pass


class TestProceduralTimelineExtraction:
    """Tests for procedural timeline milestones extraction."""
    
    @classmethod
    def setup_class(cls):
        """Setup parser instance."""
        logger = ResponsesExtractorLogger().setup()
        cls.parser = ECIResponseHTMLParser(logger=logger)
    
    def test_commission_meeting_date(self):
        """Test extraction of Commission meeting date."""
        # Placeholder - implement when HTML structure is known
        pass
    
    def test_commission_officials_met(self):
        """Test extraction of Commission officials who met organizers."""
        # Placeholder - implement when HTML structure is known
        pass
    
    def test_parliament_hearing_date(self):
        """Test extraction of Parliament hearing date."""
        # Placeholder - implement when HTML structure is known
        pass
    
    def test_parliament_hearing_recording_url(self):
        """Test extraction of Parliament hearing video URL."""
        # Placeholder - implement when HTML structure is known
        pass
    
    def test_plenary_debate_date(self):
        """Test extraction of plenary debate date."""
        # Placeholder - implement when HTML structure is known
        pass
    
    def test_commission_communication_date(self):
        """Test extraction of Commission Communication date."""
        # Placeholder - implement when HTML structure is known
        pass
    
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
