import re
from datetime import datetime
from typing import Optional

from bs4 import BeautifulSoup

from ..base.base_extractor import BaseExtractor

class SubmissionDataExtractor(BaseExtractor):
    """Extracts submission text and verification data"""

    def extract_submission_text(self, soup: BeautifulSoup) -> str:
        """Extract normalized text from all paragraphs in the submission section"""
        try:
            submission_section = soup.find('h2', id='Submission-and-examination')

            if not submission_section:
                submission_section = soup.find('h2', string=re.compile(r'Submission and examination', re.IGNORECASE))

            if not submission_section:
                raise ValueError(f"No submission section found for {self.registration_number}")

            paragraphs = []
            for sibling in submission_section.find_next_siblings():
                if sibling.name == 'h2':
                    break
                if sibling.name == 'p':
                    text = sibling.get_text(separator=' ', strip=True)
                    text = ' '.join(text.split())
                    if text:
                        paragraphs.append(text)

            if not paragraphs:
                raise ValueError(f"No paragraphs found in submission section for {self.registration_number}")

            full_text = ' '.join(paragraphs)
            return full_text

        except Exception as e:
            raise ValueError(f"Error extracting submission text for {self.registration_number}: {str(e)}") from e

    def extract_commission_submission_date(self, soup: BeautifulSoup) -> datetime.date:
        """Extract submission date from 'Submission and examination' section
        
        Handles two formats:
        1. DD Month YYYY (e.g., "6 October 2017")
        2. DD/MM/YYYY (e.g., "28/02/2014")
        
        Both formats look for text like "submitted to the [European] Commission on [DATE]"
        """
        try:
            h2 = soup.find('h2', id='Submission-and-examination')
            
            if h2:
                first_p = h2.find_next_sibling('p')
                
                if first_p:
                    text = first_p.get_text()

                    # Pattern 1: DD Month YYYY format (e.g., "6 October 2017")
                    match1 = re.search(
                        r'submitted to the (?:European )?Commission on (\d{1,2} [A-Za-z]+ \d{4})', 
                        text, 
                        re.IGNORECASE
                    )
                    
                    if match1:
                        date_str = match1.group(1)
                        date_time = datetime.strptime(date_str, '%d %B %Y')
                        return date_time.date()

                    # Pattern 2: DD/MM/YYYY format (e.g., "28/02/2014")
                    match2 = re.search(
                        r'submitted to the (?:European )?Commission on (\d{2}/\d{2}/\d{4})', 
                        text, 
                        re.IGNORECASE
                    )
                    
                    if match2:
                        date_str = match2.group(1)
                        date_time = datetime.strptime(date_str, '%d/%m/%Y')
                        return date_time.date()

            raise ValueError(f"No submission date found for initiative {self.registration_number}")
            
        except ValueError:
            # Re-raise ValueError as-is (includes our custom message for test assertions)
            raise
        except Exception as e:
            # Wrap other exceptions with context
            raise ValueError(f"Error extracting submission date for {self.registration_number}: {str(e)}") from e

    def extract_submission_news_url(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract Commission news announcement URL about submission"""
        h2 = soup.find('h2', id='Submission-and-examination')

        if h2:
            first_p = h2.find_next_sibling('p')

            if first_p:
                links = first_p.find_all('a')

                for link in links:
                    href = link.get('href', '')
                    link_text = link.get_text().strip().lower()

                    if any(keyword in link_text for keyword in ['press', 'announcement', 'news']):
                        if 'presscorner' in href or 'europa.eu/rapid' in href:
                            return href

        raise ValueError(f"No submission news URL found for initiative {self.registration_number}")