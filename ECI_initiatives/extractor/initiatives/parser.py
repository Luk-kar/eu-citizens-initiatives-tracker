"""
ECI Responses HTML Parser
Parses individual response HTML files and extracts Commission response data
"""

import re
from typing import Dict, List, Optional, Union, Tuple
from pathlib import Path
from bs4 import BeautifulSoup

from .model import ECIResponseData


class ECIResponseHTMLParser:
    """Parser for ECI Commission response HTML pages"""
    
    def __init__(self):
        """Initialize the parser"""
        pass
    
    def parse_file(self, html_path: Path, responses_list_data: Dict) -> ECIResponseData:
        """
        Parse a single response HTML file and extract all data
        
        Args:
            html_path: Path to the HTML file
            responses_list_data: Dictionary with metadata from responses_list.csv
            
        Returns:
            ECIResponseData object with all extracted fields
        """
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        filename = html_path.name
        
        # Extract all fields
        return ECIResponseData(
            registration_number=self._extract_registration_number(filename),
            response_url=self._extract_response_url(soup),
            initiative_url=self._extract_initiative_url(responses_list_data),
            initiative_title=self._extract_initiative_title(responses_list_data)
        )
    
    def _extract_registration_number(self, filename: str) -> str:
        """Extract registration number from filename pattern YYYY_NNNNNN_en.html"""
        
        pattern = r'(\d{4})_(\d{6})_en\.html'
        match = re.match(pattern, filename)
        
        if match:
            year, number = match.groups()
            return f"{year}/{number}"
            
        return ""
    
    def _extract_response_url(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract the current page URL from meta tags or canonical link"""
        
        # Try canonical link first
        canonical = soup.find('link', {'rel': 'canonical'})
        if canonical and canonical.get('href'):
            return canonical['href']
        
        # Try og:url meta tag
        og_url = soup.find('meta', {'property': 'og:url'})
        if og_url and og_url.get('content'):
            return og_url['content']
        
        # Try dcterms.identifier meta tag
        dcterms_id = soup.find('meta', {'name': 'dcterms.identifier'})
        if dcterms_id and dcterms_id.get('content'):
            return dcterms_id['content']
        
        return None
    
    def _extract_initiative_url(self, responses_list_data: Dict) -> Optional[str]:
        """Get initiative URL from responses_list.csv data"""
        
        return responses_list_data.get('initiative_url')
    
    def _extract_initiative_title(self, responses_list_data: Dict) -> Optional[str]:
        """Get initiative title from responses_list.csv data"""
        
        return responses_list_data.get('initiative_title')
