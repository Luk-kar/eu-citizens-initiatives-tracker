"""
HTML parser for extracting Commission response links from initiative pages.
"""
import re
from typing import List, Dict, Optional
from pathlib import Path
from bs4 import BeautifulSoup

from .scraper_logger import logger


class ResponseLinkExtractor:
    """Extract Commission response links from initiative page HTML files."""
    
    def __init__(self):
        """Initialize the link extractor."""
        pass
    
    def extract_links_from_file(self, file_path: str) -> Optional[Dict[str, str]]:
        """
        Extract Commission response link from a single initiative HTML file.
        
        Args:
            file_path: Path to the initiative HTML file
            
        Returns:
            Dictionary with 'url', 'year', 'reg_number' or None if no link found
        """

        try:
            # Read HTML file
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Parse HTML for link
            url = self._parse_html_for_link(html_content, file_path)
            
            if not url:
                return None
            
            # Extract metadata from file path
            metadata = self._extract_metadata_from_path(file_path)
            
            return {
                'url': url,
                'year': metadata['year'],
                'reg_number': metadata['reg_number']
            }
            
        except Exception as e:
            logger.error(f"Error extracting link from {file_path}: {str(e)}")
            return None
    
    def extract_links_from_directory(self, base_dir: str) -> List[Dict[str, str]]:
        """
        Extract all Commission response links from initiative pages directory.
        
        Args:
            base_dir: Base directory containing initiative_pages/<year>/<reg_number>_en.html
            
        Returns:
            List of dictionaries with response link information
        """

        response_links = []
        base_path = Path(base_dir)
        
        # Traverse all year directories
        for year_dir in base_path.iterdir():

            if not year_dir.is_dir():
                continue
            
            # Process all HTML files in year directory
            for html_file in year_dir.glob("*_en.html"):

                link_data = self.extract_links_from_file(str(html_file))
                if link_data:
                    response_links.append(link_data)
        
        return response_links
    
    def _parse_html_for_link(self, html_content: str, file_path: str) -> Optional[str]:
        """
        Parse HTML content and extract Commission response link.
        
        Args:
            html_content: HTML content as string
            file_path: Path to the file (for logging purposes)
            
        Returns:
            Full URL to Commission response page or None
        """
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find Commission response link using text matching
            url = self._extract_response_commission_url(soup)
            
            if url:
                logger.debug(f"Found Commission response link in {file_path}: {url}")
            
            return url
            
        except Exception as e:
            logger.error(f"Error parsing HTML from {file_path}: {str(e)}")
            return None
    
    def _extract_metadata_from_path(self, file_path: str) -> Dict[str, str]:
        """
        Extract year and registration number from file path.
        
        Args:
            file_path: Path like 'initiative_pages/2019/000007_en.html'
            
        Returns:
            Dictionary with 'year' and 'reg_number'
        """
        path = Path(file_path)
        year = path.parent.name  # Get year from directory name
        reg_number = path.stem.replace('_en', '')  # Get reg number from filename
        
        return {
            'year': year,
            'reg_number': reg_number
        }
    
    def _extract_response_commission_url(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Extract the Commission's answer and follow-up page URL.
        
        Finds the <a> tag containing text "Commission's answer and follow-up"
        and returns its href attribute. Handles both regular apostrophe and Unicode right single quotation mark.
        
        Args:
            soup: BeautifulSoup parsed HTML
            
        Returns:
            URL to the initiative's follow-up page, or None if not found
        """

        # Find the link with text containing "Commission's answer and follow-up"
        # Pattern handles both regular apostrophe (') and Unicode right single quotation mark (\u2019)
        link = soup.find('a', string=re.compile(r"Commission['\u2019]s answer and follow-up", re.I))
        
        if link and link.get('href'):
            return link.get('href')
        
        return None
