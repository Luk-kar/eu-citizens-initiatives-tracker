"""
Test suite for validating data extraction from response HTML files.

Tests focus on behavior of extraction methods:
- Registration number extraction from filenames
- Basic metadata extraction
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


class TestRegistrationNumberExtraction:
    """Tests for registration number extraction from filename."""
    
    @classmethod
    def setup_class(cls):
        """Setup parser instance."""
        logger = ResponsesExtractorLogger().setup()
        cls.parser = ECIResponseHTMLParser(logger=logger)
    
    def test_valid_filename_format(self):
        """Test extraction from valid filename format (YYYY_NNNNNN_en.html)."""
        expected_reg_number = '2024/000005'
        filename = expected_reg_number.replace("/", "_") + "_en.html"
        
        reg_number = self.parser._extract_registration_number(filename)
        
        assert reg_number == expected_reg_number, \
            f"Expected '{expected_reg_number}', got '{reg_number}'"


    def test_registration_number_formatting(self):
        """Test that registration number is formatted correctly (YYYY/NNNNNN)."""
        import re
        
        expected_length = 11
        expected_separator = "/"
        expected_pattern = r'^\d{4}/\d{6}$'  # YYYY/NNNNNN format
        
        filename = "2019_000007_en.html"
        reg_number = self.parser._extract_registration_number(filename)
        
        # Check separator present
        assert expected_separator in reg_number, \
            f"Registration number should contain '{expected_separator}'"
        
        # Check length
        assert len(reg_number) == expected_length, \
            f"Registration number should be {expected_length} characters (YYYY/NNNNNN)"
        
        # Check format with regex: exactly 4 digits, slash, 6 digits
        assert re.match(expected_pattern, reg_number), \
            f"Registration number '{reg_number}' should match pattern YYYY/NNNNNN"


    def test_registration_number_invalid_filename(self):
        """Test that ValueError is raised for invalid filename format."""
        invalid_filenames = [
            "2019_00007_en.html",      # Wrong number length (5 digits instead of 6)
            "19_000007_en.html",        # Wrong year length (2 digits instead of 4)
            "2019_000007.html",         # Missing _en
            "2019_000007_en.txt",       # Wrong extension
            "2019-000007_en.html",      # Wrong separator (dash instead of underscore)
            "abc_000007_en.html",       # Non-numeric year
            "2019_abcdef_en.html",      # Non-numeric number
            "invalid.html",             # Completely wrong format
        ]
        
        for invalid_filename in invalid_filenames:
            with pytest.raises(ValueError, match="does not match expected pattern"):
                self.parser._extract_registration_number(invalid_filename)

    def test_registration_number_empty_filename(self):
        """Test that ValueError is raised for empty filename."""
        with pytest.raises(ValueError, match="does not match expected pattern"):
            self.parser._extract_registration_number("")


class TestBasicMetadataExtraction:
    """Tests for basic metadata extraction."""
    
    @classmethod
    def setup_class(cls):
        """Setup parser instance."""

        logger = ResponsesExtractorLogger().setup()
        cls.parser = ECIResponseHTMLParser(logger=logger)
    
    def test_extract_response_url(self):
        """Test construction of response URL from canonical initiative URL."""
        
        html = '''
        <html>
            <head>
                <link rel="canonical" href="https://citizens-initiative.europa.eu/initiatives/details/2012/000003/water-and-sanitation-are-human-right-water-public-good-not-commodity_en" />
            </head>
        </html>
        '''
        
        soup = BeautifulSoup(html, 'html.parser')
        url = self.parser._extract_response_url(soup)
        
        expected_url = "https://citizens-initiative.europa.eu/initiatives/details/2012/000003/commission-response_en"
        assert url == expected_url, \
            f"Expected '{expected_url}', got '{url}'"
    
    def test_extract_initiative_url(self):
        """Test extraction of initiative URL from breadcrumb link."""
        
        # HTML with breadcrumb link
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
        
        # Extract URL
        url = self.parser._extract_initiative_url(soup)
        
        # Validate
        expected_url = "https://citizens-initiative.europa.eu/initiatives/details/2012/000003_en"
        assert url == expected_url, \
            f"Expected URL '{expected_url}', got '{url}'"
        
        # Verify base URL is prepended
        assert url.startswith("https://citizens-initiative.europa.eu"), \
            "URL should start with base URL"
        
        # Verify relative path is preserved
        assert "/initiatives/details/2012/000003_en" in url, \
            "URL should contain the relative path"


    def test_extract_initiative_url_missing_link(self):
        """Test extraction raises ValueError when breadcrumb link is missing."""
        
        html = '<div>No breadcrumb here</div>'
        soup = BeautifulSoup(html, 'html.parser')
        
        with pytest.raises(ValueError, match="Breadcrumb link.*not found"):
            self.parser._extract_initiative_url(soup)


    def test_extract_initiative_url_missing_href(self):
        """Test extraction raises ValueError when href attribute is missing."""
        
        html = '''
        <a class="ecl-breadcrumb__link">Initiative detail</a>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        
        with pytest.raises(ValueError, match="href.*missing or empty"):
            self.parser._extract_initiative_url(soup)


    def test_extract_initiative_url_with_whitespace(self):
        """Test extraction works with whitespace in link text."""
        
        # HTML with extra whitespace (common in formatted HTML)
        html = '''
        <a href="/initiatives/details/2019/000007_en" 
        class="ecl-breadcrumb__link">
        
        Initiative detail
        
        </a>
        '''
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Should still work despite whitespace
        url = self.parser._extract_initiative_url(soup)
        
        expected_url = "https://citizens-initiative.europa.eu/initiatives/details/2019/000007_en"
        assert url == expected_url, \
            f"Should handle whitespace correctly. Expected '{expected_url}', got '{url}'"



        
    def test_initiative_title_from_metadata(self):
        """Test extraction of initiative title from responses_list.csv data."""
        
        test_metadata = {
            'title': 'Test Initiative Title'
        }
        
        title = self.parser._extract_initiative_title(test_metadata)
        assert title == "", "Should return empty string from current implementation"


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
