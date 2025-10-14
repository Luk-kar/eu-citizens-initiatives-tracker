"""
ECI Responses HTML Parser
Parses ECI Commission response HTML pages and extracts structured data
"""

import re
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from bs4 import BeautifulSoup

from .model import ECIResponse


class ECIResponseHTMLParser:
    """Parser for ECI Commission response HTML pages"""
    
    def __init__(self, logger: logging.Logger):
        """
        Initialize parser with shared logger
        
        Args:
            logger: Shared logger instance from ResponsesExtractorLogger
        """
        self.logger = logger
    
    def parse_file(self, html_path: Path, responses_list_data: Dict) -> Optional[ECIResponse]:
        """
        Parse a single ECI response HTML file and extract data
        
        Args:
            html_path: Path to HTML file
            responses_list_data: Metadata from responses_list.csv with keys:
                - url_find_initiative: Initiative URL (not used)
                - registration_number: Registration number (YYYY/NNNNNN format)
                - title: Initiative title
                - datetime: Scrape datetime
                
        Returns:
            ECIResponse object or None if parsing fails
        """
        try:
            self.logger.info(f"Parsing response file: {html_path.name}")
            
            # Read and parse HTML file
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Get current timestamp for metadata
            current_timestamp = datetime.now().isoformat()
        
            # Extract commission communication date for follow-up calculation
            commission_communication_date = self._extract_commission_communication_date(soup)
            latest_update_date = self._extract_latest_update_date(soup)
            
            # Create and return ECIResponse object
            response = ECIResponse(
                # Basic Initiative Metadata
                response_url=self._extract_response_url(soup),
                initiative_url=self._extract_initiative_url(soup),
                initiative_title=responses_list_data.get('title'),
                registration_number=responses_list_data.get('registration_number'),

                
                # Submission and Verification Data
                submission_date=self._extract_submission_date(soup),
                verified_signatures_count=self._extract_verified_signatures_count(soup),
                number_member_states_threshold=self._extract_number_member_states_threshold(soup),
                submission_news_url=self._extract_submission_news_url(soup),
                
                # Procedural Timeline Milestones
                commission_meeting_date=self._extract_commission_meeting_date(soup),
                commission_officials_met=self._extract_commission_officials_met(soup),
                parliament_hearing_date=self._extract_parliament_hearing_date(soup),
                parliament_hearing_recording_url=self._extract_parliament_hearing_recording_url(soup),
                plenary_debate_date=self._extract_plenary_debate_date(soup),
                plenary_debate_recording_url=self._extract_plenary_debate_recording_url(soup),
                commission_communication_date=commission_communication_date,
                commission_communication_url=self._extract_commission_communication_url(soup),
                commission_response_news_url=self._extract_commission_response_news_url(soup),
                
                # Commission Response Content
                communication_main_conclusion=self._extract_communication_main_conclusion(soup),
                legislative_proposal_status=self._extract_legislative_proposal_status(soup),
                commission_response_summary=self._extract_commission_response_summary(soup),
                
                # Follow-up Activities Section
                has_followup_section=self._extract_has_followup_section(soup),
                followup_meeting_date=self._extract_followup_meeting_date(soup),
                followup_meeting_officials=self._extract_followup_meeting_officials(soup),
                roadmap_launched=self._extract_roadmap_launched(soup),
                roadmap_description=self._extract_roadmap_description(soup),
                roadmap_completion_target=self._extract_roadmap_completion_target(soup),
                workshop_conference_dates=self._extract_workshop_conference_dates(soup),
                partnership_programs=self._extract_partnership_programs(soup),
                court_cases_referenced=self._extract_court_cases_referenced(soup),
                court_judgment_dates=self._extract_court_judgment_dates(soup),
                court_judgment_summary=self._extract_court_judgment_summary(soup),
                latest_update_date=latest_update_date,
                
                # Multimedia and Documentation Links
                factsheet_url=self._extract_factsheet_url(soup),
                video_recording_count=self._extract_video_recording_count(soup),
                dedicated_website=self._extract_has_dedicated_website(soup),
                
                # Structural Analysis Flags
                related_eu_legislation=self._extract_related_eu_legislation(soup),
                petition_platforms_used=self._extract_petition_platforms_used(soup),
                follow_up_duration_months=self._calculate_follow_up_duration_months(
                    commission_communication_date, 
                    latest_update_date
                ),
                
                # Metadata
                created_timestamp=current_timestamp,
                last_updated=current_timestamp
            )
            
            self.logger.info(f"Successfully parsed response: {response.registration_number}")
            return response
            
        except FileNotFoundError:
            self.logger.error(f"File not found: {html_path}")
            return None
        except Exception as e:
            self.logger.error(f"Error parsing {html_path.name}: {str(e)}", exc_info=True)
            return None

    def _extract_response_url(self, soup: BeautifulSoup) -> str:
        """Extract the response page URL from HTML
        
        Tries multiple methods to find the URL:
        1. Active language link in site header
        2. Link with hreflang="en"
        3. Canonical link from head
        4. og:url meta tag
        
        Args:
            soup: BeautifulSoup object containing parsed HTML
            
        Returns:
            Full response page URL
            
        Raises:
            ValueError: If response URL cannot be found
        """
        try:

            # Method 1: Find the active language link in the site header
            active_language_link = soup.find(
                'a',
                class_='ecl-site-header__language-link--active'
            )
            
            if active_language_link and active_language_link.get('href'):
                response_url = active_language_link['href']
                # Ensure it's a full URL
                if response_url.startswith('http'):
                    return response_url
                elif response_url.startswith('/'):
                    return f"https://citizens-initiative.europa.eu{response_url}"
                else:
                    return f"https://citizens-initiative.europa.eu/{response_url}"
            
            # Method 2: Try finding link with hreflang="en"
            en_language_link = soup.find('a', attrs={'hreflang': 'en'})
            if en_language_link and en_language_link.get('href'):
                response_url = en_language_link['href']
                if response_url.startswith('http'):
                    return response_url
                elif response_url.startswith('/'):
                    return f"https://citizens-initiative.europa.eu{response_url}"
                else:
                    return f"https://citizens-initiative.europa.eu/{response_url}"
            
            # Method 3: Try canonical link from head
            canonical_link = soup.find('link', attrs={'rel': 'canonical'})
            if canonical_link and canonical_link.get('href'):
                response_url = canonical_link['href']
                if response_url.startswith('http'):
                    return response_url
                elif response_url.startswith('/'):
                    return f"https://citizens-initiative.europa.eu{response_url}"
                else:
                    return f"https://citizens-initiative.europa.eu/{response_url}"
            
            # Method 4: Try og:url meta tag
            og_url = soup.find('meta', attrs={'property': 'og:url'})
            if og_url and og_url.get('content'):

                response_url = og_url['content']
                if response_url.startswith('http'):
                    return response_url
                elif response_url.startswith('/'):
                    return f"https://citizens-initiative.europa.eu{response_url}"
                else:
                    return f"https://citizens-initiative.europa.eu/{response_url}"


            raise ValueError(
                "Response URL not found in HTML. Expected one of: "
                "active language link (class='ecl-site-header__language-link--active'), "
                "link with hreflang='en', "
                "canonical link tag (<link rel='canonical'>), "
                "or og:url meta tag (<meta property='og:url'>)"
            )

        except Exception as e:
            raise ValueError(f"Error extracting response URL: {str(e)}") from e
            
    def _extract_initiative_url(self, soup: BeautifulSoup) -> str:
        """Extract initiative URL from breadcrumb link or page links
        
        Tries multiple methods to find the initiative URL:
        1. Breadcrumb link with text "Initiative detail"
        2. Any link matching /initiatives/details/YYYY/NNNNNN_en pattern with text content
        
        Args:
            soup: BeautifulSoup object containing parsed HTML
            
        Returns:
            Full initiative URL
            
        Raises:
            ValueError: If initiative URL cannot be found
            
        Examples:
            Finds URLs like:
            - https://citizens-initiative.europa.eu/initiatives/details/2017/000002_en
            - /initiatives/details/2017/000002_en (converted to full URL)
        """
        try:
            
            # Method 1: Find the breadcrumb link with text "Initiative detail"
            breadcrumb_link = soup.find(
                'a', 
                class_='ecl-breadcrumb__link', 
                string=lambda text: text and text.strip() == 'Initiative detail'
            )
            
            if breadcrumb_link and breadcrumb_link.get('href'):
                href = breadcrumb_link['href']
                
                # Build full URL if relative
                if href.startswith('http'):
                    return href

                elif href.startswith('/'):
                    initiative_url = f"https://citizens-initiative.europa.eu{href}"
                    return initiative_url
            
            # Method 2: Search for any link matching /initiatives/details/YYYY/NNNNNN_en pattern
            # Look for links with text content (not empty/icon-only links)
            all_links = soup.find_all('a', href=True, string=True)
            
            for link in all_links:
                href = link['href']
                link_text = link.get_text(strip=True)
                
                # Skip if link has no meaningful text
                if not link_text:
                    continue
                
                # Check if href matches the pattern
                # Pattern: /initiatives/details/YYYY/NNNNNN_en (specifically English version)
                if re.search(r'/initiatives/details/\d{4}/\d{6}_en$', href):

                    if href.startswith('http'):
                        self.logger.info(f"Found initiative URL in page link with text '{link_text}': {href}")
                        return href
                    elif href.startswith('/'):
                        initiative_url = f"https://citizens-initiative.europa.eu{href}"
                        self.logger.info(f"Found initiative URL in page link with text '{link_text}': {initiative_url}")
                        return initiative_url
            
            # If no URL found, raise error
            raise ValueError(
                "Initiative URL not found. Expected breadcrumb link with text 'Initiative detail' "
                "or link matching pattern /initiatives/details/YYYY/NNNNNN_en with text content"
            )
            
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"Error extracting initiative URL: {str(e)}") from e
    # Submission and Verification Section
    def _extract_submission_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract submission date from 'Submission and examination' section"""
        pass
    
    def _extract_verified_signatures_count(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract verified statements of support count"""
        pass
    
    def _extract_number_member_states_threshold(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract number of Member States where threshold was met"""
        pass
    
    def _extract_submission_news_url(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract Commission news announcement URL about submission"""
        pass
    
    # Procedural Timeline Milestones
    def _extract_commission_meeting_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract date of meeting with Commission officials (Article 15)"""
        pass
    
    def _extract_commission_officials_met(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract names and titles of Commissioners/Vice-Presidents who met"""
        pass
    
    def _extract_parliament_hearing_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract date of European Parliament public hearing"""
        pass
    
    def _extract_parliament_hearing_recording_url(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract video recording URL of Parliament hearing"""
        pass
    
    def _extract_plenary_debate_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract date of plenary debate in Parliament"""
        pass
    
    def _extract_plenary_debate_recording_url(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract video recording URL of plenary debate"""
        pass
    
    def _extract_commission_communication_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract date Commission adopted official Communication"""
        pass
    
    def _extract_commission_communication_url(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract link to full PDF of Commission Communication"""
        pass
    
    def _extract_commission_response_news_url(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract press release/news URL about Commission response"""
        pass
    
    # Commission Response Content
    def _extract_communication_main_conclusion(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract main conclusions text from Communication"""
        pass
    
    def _extract_legislative_proposal_status(self, soup: BeautifulSoup) -> Optional[str]:
        """Determine if Commission proposed legislation, alternatives, or no action"""
        pass
    
    def _extract_commission_response_summary(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract overall Commission position summary"""
        pass
    
    # Follow-up Activities Section
    def _extract_has_followup_section(self, soup: BeautifulSoup) -> Optional[bool]:
        """Check if page includes follow-up activities section"""
        pass
    
    def _extract_followup_meeting_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract date of follow-up meetings after initial response"""
        pass
    
    def _extract_followup_meeting_officials(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract names of officials in follow-up meetings"""
        pass
    
    def _extract_roadmap_launched(self, soup: BeautifulSoup) -> Optional[bool]:
        """Check if roadmap or action plan was initiated"""
        pass
    
    def _extract_roadmap_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract roadmap objectives description"""
        pass
    
    def _extract_roadmap_completion_target(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract target date for roadmap completion"""
        pass
    
    def _extract_workshop_conference_dates(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract dates of workshops/conferences as JSON array"""
        pass
    
    def _extract_partnership_programs(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract names of partnership programs established"""
        pass
    
    def _extract_court_cases_referenced(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract Court of Justice case numbers"""
        pass
    
    def _extract_court_judgment_dates(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract dates of court judgments"""
        pass
    
    def _extract_court_judgment_summary(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract brief court ruling descriptions"""
        pass
    
    def _extract_latest_update_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract most recent date from follow-up section"""
        pass
    
    # Multimedia and Documentation
    def _extract_factsheet_url(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract factsheet PDF URL"""
        pass
    
    def _extract_video_recording_count(self, soup: BeautifulSoup) -> Optional[int]:
        """Count number of video recordings linked"""
        pass
    
    def _extract_has_dedicated_website(self, soup: BeautifulSoup) -> Optional[bool]:
        """Check if organizers maintained campaign website"""
        return False
    
    # Structural Analysis
    def _extract_related_eu_legislation(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract references to specific Regulations or Directives"""
        pass
    
    def _extract_petition_platforms_used(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract external platforms mentioned"""
        pass
    
    def _calculate_follow_up_duration_months(self, commission_date: Optional[str], 
                                            latest_update: Optional[str]) -> Optional[int]:
        """Calculate months between Commission response and latest follow-up"""
        pass
    
    # Helper Methods
    def _parse_date(self, date_string: str) -> Optional[str]:
        """Parse and normalize date strings to ISO format"""
        pass
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text (remove extra whitespace, normalize)"""
        pass
    
    def _extract_all_video_urls(self, soup: BeautifulSoup) -> List[str]:
        """Extract all video recording URLs from page"""
        pass
