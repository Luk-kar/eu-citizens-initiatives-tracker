"""
Test suite for validating data extraction from HTML files.

Tests focus on behavior of extraction methods:
 - Registration number extraction from filenames
 - Title extraction with fallback logic
 - Objective extraction with character limit
 - Timeline data extraction
 - Signatures data extraction
 - Organizer data extraction
 - Funding data extraction
 - Current status extraction
 - URL construction
"""

# Standard library
from pathlib import Path
import json

# Third party
import pytest
from bs4 import BeautifulSoup

# Local
from ECI_initiatives.extractor.initiatives.parser import ECIHTMLParser
from ECI_initiatives.extractor.initiatives.initiatives_logger import InitiativesExtractorLogger


class TestRegistrationNumberExtraction:
    """Tests for registration number extraction."""
    
    @classmethod
    def setup_class(cls):
        """Setup parser instance."""

        logger = InitiativesExtractorLogger().setup()
        cls.parser = ECIHTMLParser(logger=logger)
    
    def test_valid_filename_format(self):
        """Test extraction from valid filename format (YYYY_NNNNNN_en.html)."""

        filename = "2024_000005_en.html"
        reg_number = self.parser._extract_registration_number(filename)
        assert reg_number == "2024/000005", \
            f"Expected '2024/000005', got '{reg_number}'"
    
    def test_registration_number_formatting(self):
        """Test that registration number is formatted correctly (YYYY/NNNNNN)."""

        filename = "2019_000007_en.html"
        reg_number = self.parser._extract_registration_number(filename)
        assert "/" in reg_number, "Registration number should contain '/'"
        assert len(reg_number) == 11, "Registration number should be 11 characters (YYYY/NNNNNN)"


class TestTitleExtraction:
    """Tests for title extraction."""
    
    @classmethod
    def setup_class(cls):
        """Setup parser instance."""

        logger = InitiativesExtractorLogger().setup()
        cls.parser = ECIHTMLParser(logger=logger)
    
    def test_title_from_meta_tag(self):
        """Test extraction from meta tag when present."""

        html = '''
        <html>
            <head>
                <meta name="dcterms.title" content="Test Initiative Title" />
            </head>
            <body></body>
        </html>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        title = self.parser._extract_title(soup)
        assert title == "Test Initiative Title", f"Expected 'Test Initiative Title', got '{title}'"
    
    def test_title_fallback_to_h1(self):
        """Test fallback to h1 element when meta tag is missing."""

        html = '''
        <html>
            <body>
                <h1 class="ecl-page-header-core__title">Fallback Title</h1>
            </body>
        </html>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        title = self.parser._extract_title(soup)
        assert title == "Fallback Title", f"Expected 'Fallback Title', got '{title}'"
    
    def test_title_text_is_stripped(self):
        """Test that title text is properly stripped of whitespace."""

        html = '''
        <html>
            <head>
                <meta name="dcterms.title" content="  Title With Spaces  " />
            </head>
        </html>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        title = self.parser._extract_title(soup)
        assert title == "Title With Spaces", "Title should be stripped"


class TestObjectiveExtraction:
    """Tests for objective extraction."""
    
    @classmethod
    def setup_class(cls):
        """Setup parser instance."""

        logger = InitiativesExtractorLogger().setup()
        cls.parser = ECIHTMLParser(logger=logger)
    
    def test_objective_character_limit(self):
        """Test that objective is truncated at 1,100 characters."""

        long_text = "A" * 1500
        html = f'''
        <html>
            <body>
                <h2>Objectives</h2>
                <p>{long_text}</p>
            </body>
        </html>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        objective = self.parser._extract_objective(soup)
        assert len(objective) == 1100, f"Objective should be 1100 chars, got {len(objective)}"
    
    def test_objective_multi_paragraph(self):
        """Test extraction of multi-paragraph objective text."""

        html = '''
        <html>
            <body>
                <h2>Objectives</h2>
                <p>First paragraph.</p>
                <p>Second paragraph.</p>
            </body>
        </html>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        objective = self.parser._extract_objective(soup)
        assert "First paragraph" in objective, "Should contain first paragraph"
        assert "Second paragraph" in objective, "Should contain second paragraph"


class TestURLConstruction:
    """Tests for URL construction."""
    
    @classmethod
    def setup_class(cls):
        """Setup parser instance."""

        logger = InitiativesExtractorLogger().setup()
        cls.parser = ECIHTMLParser(logger=logger)
    
    def test_url_construction_format(self):
        """Test that URL is constructed in correct Europa.eu format."""

        reg_number = "2024/000005"
        url = self.parser._construct_url(reg_number)
        expected = "https://citizens-initiative.europa.eu/initiatives/details/2024/000005_en"
        assert url == expected, f"Expected '{expected}', got '{url}'"
    
    def test_url_contains_registration_parts(self):
        """Test that URL contains year and number components."""

        reg_number = "2019/000007"
        url = self.parser._construct_url(reg_number)
        assert "2019" in url, "URL should contain year"
        assert "000007" in url, "URL should contain initiative number"


class TestCurrentStatusExtraction:
    """Tests for current status extraction."""
    
    @classmethod
    def setup_class(cls):
        """Setup parser instance."""

        logger = InitiativesExtractorLogger().setup()
        cls.parser = ECIHTMLParser(logger=logger)
    
    def test_current_status_from_timeline(self):
        """Test extraction of current status from timeline items."""

        html = '''
        <html>
            <body>
                <ol class="ecl-timeline">
                    <li class="ecl-timeline__item ecl-timeline__item--current">
                        <div class="ecl-timeline__title">Collection ongoing</div>
                    </li>
                </ol>
            </body>
        </html>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        status = self.parser._extract_current_status(soup)
        assert status == "Collection ongoing", f"Expected 'Collection ongoing', got '{status}'"


class TestSignaturesExtraction:
    """Tests for signatures data extraction."""
    
    @classmethod
    def setup_class(cls):
        """Setup parser instance."""

        logger = InitiativesExtractorLogger().setup()
        cls.parser = ECIHTMLParser(logger=logger)
    
    def test_signatures_collected_from_table(self):
        """Test extraction of total signatures from table."""

        html = '''
        <html>
            <body>
                <table class="ecl-table ecl-table--zebra">
                    <tr class="ecl-table__row">
                        <td class="ecl-table__cell">Total number of signatories</td>
                        <td class="ecl-table__cell">1,234,567</td>
                    </tr>
                </table>
            </body>
        </html>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        signatures = self.parser._extract_signatures_collected(soup)
        assert signatures == "1,234,567", f"Expected '1,234,567', got '{signatures}'"
    
    def test_signatures_by_country_json_format(self, program_root_dir, tmp_path):
        """Test that signatures by country data is valid JSON."""

        html = '''
        <html>
            <body>
                <table class="ecl-table ecl-table--zebra">
                    <tr class="ecl-table__row">
                        <td class="ecl-table__cell">Germany</td>
                        <td class="ecl-table__cell">500,000</td>
                        <td class="ecl-table__cell">72,000</td>
                        <td class="ecl-table__cell">694.4%</td>
                    </tr>
                </table>
            </body>
        </html>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        filepath = tmp_path / "test.html"
        filepath.write_text(html)
        
        signatures_json = self.parser._extract_signatures_by_country(
            soup, filepath, "Test Initiative", "http://example.com"
        )
        
        if signatures_json:
            # Should be valid JSON
            data = json.loads(signatures_json)
            assert isinstance(data, dict), "Should be a dictionary"
            assert "Germany" in data, "Should contain Germany"


class TestOrganizerExtraction:
    """Tests for organizer data extraction."""
    
    @classmethod
    def setup_class(cls):
        """Setup parser instance."""

        logger = InitiativesExtractorLogger().setup()
        cls.parser = ECIHTMLParser(logger=logger)
    
    def test_organizer_representative_json_format(self, tmp_path):
        """Test that organizer representative data is valid JSON."""

        html = '''
        <html>
            <body>
                <h2>Organisers</h2>
                <h3>Representative</h3>
                <ul>
                    <li>John Doe - john@example.com - Country of residence: Germany</li>
                </ul>
            </body>
        </html>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        organizers_data = self.parser.extract_organisers_data(soup)
        
        filepath = tmp_path / "test.html"
        rep, entity, others = self.parser._split_organiser_data(
            organizers_data, filepath, "Test", "http://example.com"
        )
        
        if rep:
            data = json.loads(rep)
            assert isinstance(data, dict), "Should be a dictionary"


class TestFundingExtraction:
    """Tests for funding data extraction."""
    
    @classmethod
    def setup_class(cls):
        """Setup parser instance."""

        logger = InitiativesExtractorLogger().setup()
        cls.parser = ECIHTMLParser(logger=logger)
    
    def test_funding_total_extraction(self):
        """Test extraction of total funding amount."""
        
        html = '''
        <html>
            <body>
                <p>Total amount of support and funding: €50,000</p>
            </body>
        </html>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        total = self.parser._extract_funding_total(soup)
        assert total == "50,000", f"Expected '50,000', got '{total}'"
