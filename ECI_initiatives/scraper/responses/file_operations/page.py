"""
File operations for saving Commission response pages.
"""
import os
import logging

from bs4 import BeautifulSoup

from ..consts import MIN_HTML_LENGTH, RATE_LIMIT_INDICATORS


class PageFileManager:
    """Handle file and directory operations for response pages."""
    
    def __init__(self, base_dir: str):
        """
        Initialize file operations handler.
        
        Args:
            base_dir: Base directory for saving files
        """
        self.base_dir = base_dir
        self.logger = logging.getLogger("ECIResponsesScraper")
    
    def setup_directories(self) -> None:
        """
        Create necessary directory structure for responses.
        Creates: base_dir/ and subdirectories as needed.
        Logs only when directory is actually created.
        """
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir, exist_ok=True)
            self.logger.info(f"Created responses directory: {self.base_dir}")
    
    def save_response_page(
        self, 
        page_source: str, 
        year: str, 
        reg_number: str
    ) -> str:
        """
        Save Commission response page HTML to file.
        
        Args:
            page_source: HTML content to save
            year: Year of the initiative
            reg_number: Registration number
            
        Returns:
            Filename of saved file
            
        Raises:
            Exception: If rate limiting content detected or save fails
        """
        
        # Validate HTML
        self._validate_html(page_source)
        
        # Create year directory
        year_dir = self._create_year_directory(year)
        
        # Generate filename
        filename = self._generate_filename(year, reg_number)
        full_path = os.path.join(self.base_dir, filename)
        
        # Prettify HTML
        soup = BeautifulSoup(page_source, 'html.parser')
        pretty_html = soup.prettify()
        
        # Save to file
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(pretty_html)
        
        self.logger.debug(f"Saved response page: {filename}")
        
        return filename
    
    def _validate_html(self, page_source: str) -> bool:
        """
        Validate HTML content for rate limiting and malformed content.
        
        Args:
            page_source: HTML content to validate
            
        Returns:
            True if valid, False otherwise
            
        Raises:
            Exception: If rate limiting detected
        """

        # Check minimum length
        if len(page_source) < MIN_HTML_LENGTH:
            raise Exception(f"HTML content too short: {len(page_source)} characters")
        
        # Check for error page (multilingual "Sorry" page)
        error_page_indicators = [
            "We apologise for any inconvenience",
            "Veuillez nous excuser pour ce désagrément",
            "Ci scusiamo per il disagio arrecato"
        ]
        
        page_lower = page_source.lower()
        
        for indicator in error_page_indicators:
            if indicator.lower() in page_lower:
                raise Exception(f"Error page detected: {indicator}")
        
        # Check for rate limiting indicators
        for indicator in RATE_LIMIT_INDICATORS:
            if indicator.lower() in page_lower:
                raise Exception(f"Rate limiting detected in content: {indicator}")
        
        return True
    
    def _create_year_directory(self, year: str) -> str:
        """
        Create year-specific subdirectory.
        
        Args:
            year: Year string
            
        Returns:
            Full path to year directory
        """

        year_dir = os.path.join(self.base_dir, year)
        os.makedirs(year_dir, exist_ok=True)
        
        return year_dir
    
    def _generate_filename(self, year: str, reg_number: str) -> str:
        """
        Generate filename for response page.
        
        Args:
            year: Year of initiative
            reg_number: Registration number
            
        Returns:
            Filename in format: {year}/{reg_number}_en.html
        """

        return f"{year}/{reg_number}_en.html"

def save_response_html_file(responses_dir: str, year: str, reg_number: str, page_source: str) -> str:
    """
    Convenience function to save response page.
    
    Args:
        responses_dir: Base directory for responses
        year: Year of initiative
        reg_number: Registration number
        page_source: HTML content
        
    Returns:
        Filename of saved file
    """

    file_ops = PageFileManager(responses_dir)
    return file_ops.save_response_page(page_source, year, reg_number)