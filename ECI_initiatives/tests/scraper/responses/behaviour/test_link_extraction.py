"""
Test suite for extracting Commission response links from initiative HTML files.
"""


# Standard library
import os
import tempfile
from pathlib import Path
from typing import List, Dict


# Third party
import pytest
from bs4 import BeautifulSoup


# Local imports
from ECI_initiatives.scraper.responses.__main__ import _extract_response_links
from ECI_initiatives.scraper.responses.html_parser import ResponseLinkExtractor



class TestLinkExtraction:
    """Test extraction of response links from initiative pages."""
    
    @pytest.fixture
    def test_data_dir(self):
        """Get path to test data directory for initiatives."""
        # Changed: point to initiatives directory, not responses
        return Path(__file__).parent.parent.parent.parent / "data" / "example_htmls" / "initiatives"
    
    @pytest.fixture
    def temp_pages_dir(self, tmp_path):
        """Create temporary pages directory for testing."""
        pages_dir = tmp_path / "pages"
        pages_dir.mkdir(parents=True, exist_ok=True)
        return pages_dir
    
    @pytest.fixture
    def initiative_html_with_response_link(self, test_data_dir):
        """HTML content with Commission response link from actual file."""

        # Use the answered initiative example which has a response link
        html_file = test_data_dir / "2012_000003_en.html"
        with open(html_file, "r", encoding="utf-8") as f:
            return f.read()


    @pytest.fixture
    def initiative_html_without_response_link(self, test_data_dir):
        """HTML content without Commission response link from actual file."""

        # Use an initiative that doesn't have a response (e.g., registered, ongoing collection)
        # Let's use 2025_000002_en.html (Registered status - no response yet)
        html_file = test_data_dir / "2025_000002_en.html"
        with open(html_file, "r", encoding="utf-8") as f:
            return f.read()


    def test_only_initiatives_with_response_links_included(
        self,
        temp_pages_dir,
        initiative_html_with_response_link,
        initiative_html_without_response_link,
    ):
        """
        When processing initiative HTML files, verify that only initiatives
        with "Commission's answer and follow-up" links are included in the
        response list.
        """


        # Arrange - Create year directory with mixed files
        year_dir = temp_pages_dir / "2019"
        year_dir.mkdir(parents=True, exist_ok=True)


        # File with response link
        with_response = year_dir / "2019_000007_en.html"
        with_response.write_text(initiative_html_with_response_link, encoding="utf-8")


        # File without response link
        without_response = year_dir / "2019_000008_en.html"
        without_response.write_text(
            initiative_html_without_response_link, encoding="utf-8"
        )


        # Act - Use the actual function from __main__.py
        response_links = _extract_response_links(str(temp_pages_dir))


        # Assert
        assert len(response_links) == 1, f"Only one file should have response link, but found {len(response_links)}"
        
        # Verify the response link data structure
        link_data = response_links[0]
        assert link_data['year'] == "2019", "Year should be 2019"
        assert link_data['reg_number'] == "2019_000007", "Registration number should be 2019_000007"
        
        # Verify the file without response link is not included
        reg_numbers = [link['reg_number'] for link in response_links]
        assert "2019_000008" not in reg_numbers, "File without response link should not be included"


    def test_registration_number_and_year_extracted(self, temp_pages_dir, initiative_html_with_response_link):
        """
        When extracting links from initiative pages, verify that the
        registration number and year are correctly extracted from the file path.
        """


        # Arrange - Create test file structure with response links
        test_files = [
            ("2019", "2019_000007_en.html"),
            ("2020", "2020_000001_en.html"),
            ("2021", "2021_000006_en.html"),
        ]


        for year, filename in test_files:


            year_dir = temp_pages_dir / year
            year_dir.mkdir(parents=True, exist_ok=True)
            test_file = year_dir / filename
            test_file.write_text(initiative_html_with_response_link, encoding="utf-8")


        # Act - Use the actual extraction function
        response_links = _extract_response_links(str(temp_pages_dir))


        # Assert
        assert len(response_links) == 3, f"Should extract all 3 response links, but found {len(response_links)}"
        
        # Create set of (year, reg_number) tuples for comparison
        extracted_data = {(link['year'], link['reg_number']) for link in response_links}
        expected_data = {("2019", "2019_000007"), ("2020", "2020_000001"), ("2021", "2021_000006")}
        
        assert extracted_data == expected_data, \
            f"Expected {expected_data}, but got {extracted_data}"


    def test_missing_response_link_skipped(
        self, temp_pages_dir, initiative_html_without_response_link
    ):
        """
        When an initiative HTML file contains no Commission response link,
        verify that it is silently skipped without causing errors.
        """
        # Arrange
        year_dir = temp_pages_dir / "2019"
        year_dir.mkdir(parents=True, exist_ok=True)


        # Create multiple files without response links
        for i in range(3):
            test_file = year_dir / f"2019_00000{i}_en.html"
            test_file.write_text(
                initiative_html_without_response_link, encoding="utf-8"
            )


        # Act - Process files using actual function
        response_links = []
        errors = []


        try:
            response_links = _extract_response_links(str(temp_pages_dir))
        except Exception as e:
            errors.append(str(e))


        # Assert - No errors occurred and no links found
        assert len(errors) == 0, "Processing should not raise errors"
        assert len(response_links) == 0, f"No response links should be found, but found {len(response_links)}"


    def test_all_year_directories_processed(
        self, temp_pages_dir, initiative_html_with_response_link
    ):
        """
        When extracting response links from a directory with multiple year
        subdirectories, verify that all years are processed.
        """
        # Arrange - Create multiple year directories
        years = ["2019", "2020", "2021", "2022"]
        
        for year in years:
            year_dir = temp_pages_dir / year
            year_dir.mkdir(parents=True, exist_ok=True)
            
            # Add file with response link
            test_file = year_dir / (year + "_000001_en.html")
            test_file.write_text(initiative_html_with_response_link, encoding="utf-8")


        # Act - Use actual extraction function
        response_links = _extract_response_links(str(temp_pages_dir))


        # Assert
        assert len(response_links) == 4, f"Should extract links from all 4 years, but found {len(response_links)}"
        
        # Verify all years are represented
        extracted_years = {link['year'] for link in response_links}
        expected_years = set(years)
        
        assert extracted_years == expected_years, \
            f"Expected years {expected_years}, but got {extracted_years}"


    def test_extract_title_from_initiative_page(self, temp_pages_dir, initiative_html_with_response_link):
        """
        Verify that initiative title can be extracted along with response link.
        """


        # Arrange - Use actual HTML with response link
        year_dir = temp_pages_dir / "2019"
        year_dir.mkdir(parents=True, exist_ok=True)
        test_file = year_dir / "2019_000007_en.html"
        test_file.write_text(initiative_html_with_response_link, encoding="utf-8")


        # Act
        response_links = _extract_response_links(str(temp_pages_dir))


        # Assert
        assert len(response_links) == 1, "Should extract one response link"
        assert 'title' in response_links[0], "Response link should include title"
        # The actual title will depend on what's in the HTML file
        assert len(response_links[0].get('title', '')) > 0, \
            "Title should be extracted and not empty"


    def test_extractor_returns_correct_data_structure(self, temp_pages_dir, initiative_html_with_response_link):
        """
        Verify that the extractor returns the expected data structure
        with required fields: url, year, reg_number, title, datetime.
        """


        # Arrange
        year_dir = temp_pages_dir / "2019"
        year_dir.mkdir(parents=True, exist_ok=True)
        test_file = year_dir / "2019_000007_en.html"
        test_file.write_text(initiative_html_with_response_link, encoding="utf-8")


        # Act
        response_links = _extract_response_links(str(temp_pages_dir))


        # Assert
        assert len(response_links) > 0, f"Should extract at least one link, but found {len(response_links)}"
        
        # Verify data structure
        link_data = response_links[0]
        required_fields = ['url', 'year', 'reg_number', 'title', 'datetime']
        
        for field in required_fields:
            assert field in link_data, f"Link data should contain '{field}' field"
        
        # Verify data types
        assert isinstance(link_data['url'], str), "URL should be a string"
        assert isinstance(link_data['year'], str), "Year should be a string"
        assert isinstance(link_data['reg_number'], str), "Registration number should be a string"
        assert isinstance(link_data['title'], str), "Title should be a string"
        assert isinstance(link_data['datetime'], str), "Datetime should be a string"
        
        # Verify year and reg_number are separate
        assert link_data['year'] == "2019", "Year should be extracted separately"
        assert link_data['reg_number'] == "2019_000007", "Registration number should be extracted separately"
