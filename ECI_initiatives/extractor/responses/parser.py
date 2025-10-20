"""
ECI Responses HTML Parser
Parses ECI Commission response HTML pages and extracts structured data
"""

import calendar
import html
import re
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from bs4 import BeautifulSoup

from .model import ECICommissionResponseRecord

class ECIResponseHTMLParser:
    """Parser for ECI Commission response HTML pages"""
    
    def __init__(self, logger: logging.Logger):
        """
        Initialize parser with shared logger
        
        Args:
            logger: Shared logger instance from ResponsesExtractorLogger
        """
        self.logger = logger
        self.registration_number = None  # Temporary state during parsing
    
    def parse_file(self, html_path: Path, responses_list_data: Dict) -> Optional[ECICommissionResponseRecord]:
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
            ECICommissionResponseRecord object or None if parsing fails
        """
        try:
            self.logger.info(f"Parsing response file: {html_path.name}")
            
            # Store registration_number as instance variable for error reporting
            self.registration_number = responses_list_data['registration_number']
            
            # Read and parse HTML file
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Get current timestamp for metadata
            current_timestamp = datetime.now().isoformat()
        
            # Extract commission communication date for follow-up calculation
            commission_communication_date = self._extract_commission_communication_date(soup)
            latest_update_date = self._extract_latest_update_date(soup)
            
            # Create and return ECI Response object
            response = ECICommissionResponseRecord(
                # Basic Initiative Metadata
                response_url=self._extract_response_url(soup),
                initiative_url=self._extract_initiative_url(soup),
                initiative_title=responses_list_data.get('title'),
                registration_number=self.registration_number,

                # Submission text
                submission_text=self._extract_submission_text(soup),

                # Submission and Verification Data
                submission_date=self._extract_submission_date(soup),
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
        finally:
            self.registration_number = None

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
                f"Response URL not found for initiative {self.registration_number}. "
                "Expected one of: active language link (class='ecl-site-header__language-link--active'), "
                "link with hreflang='en', canonical link tag (<link rel='canonical'>), "
                "or og:url meta tag (<meta property='og:url'>)"
            )

        except Exception as e:
            raise ValueError(f"Error extracting response URL for initiative {self.registration_number}: {str(e)}") from e
            
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
                f"Initiative URL not found for {self.registration_number}. "
                "Expected breadcrumb link with text 'Initiative detail' "
                "or link matching pattern /initiatives/details/YYYY/NNNNNN_en with text content"
            )
            
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"Error extracting initiative URL for {self.registration_number}: {str(e)}") from e

    def _extract_submission_text(self, soup: BeautifulSoup) -> str:
        """Extract normalized text from all paragraphs in the submission section"""
        try:
            # Find the "Submission and examination" section
            submission_section = soup.find('h2', id='Submission-and-examination')
            
            if not submission_section:
                submission_section = soup.find('h2', string=re.compile(r'Submission and examination', re.IGNORECASE))
            
            if not submission_section:
                raise ValueError(f"No submission section found for {self.registration_number}")
            
            # Get all paragraphs until the next h2 (or end of siblings)
            paragraphs = []
            for sibling in submission_section.find_next_siblings():
                if sibling.name == 'h2':
                    # Reached next section - stop
                    break
                if sibling.name == 'p':
                    # Get text and normalize whitespace
                    text = sibling.get_text(separator=' ', strip=True)
                    text = ' '.join(text.split())  # Normalize whitespace
                    if text:  # Only add non-empty paragraphs
                        paragraphs.append(text)
            
            if not paragraphs:
                raise ValueError(f"No paragraphs found in submission section for {self.registration_number}")
            
            # Join all paragraphs with a space
            full_text = ' '.join(paragraphs)
            
            return full_text
            
        except Exception as e:
            raise ValueError(f"Error extracting submission text for {self.registration_number}: {str(e)}") from e

    # Submission and Verification Section
    def _extract_submission_date(self, soup: BeautifulSoup) -> datetime.date:
        """Extract submission date from 'Submission and examination' section"""
        # Find the Submission section
        h2 = soup.find('h2', id='Submission-and-examination')
        
        if h2:
            # Get first paragraph after heading
            first_p = h2.find_next_sibling('p')
            
            if first_p:
                text = first_p.get_text()

                # Pattern 1: DD Month YYYY format (e.g., "10 January 2020")
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

        # If no date found, raise an error
        raise ValueError(f"No submission date found for initiative {self.registration_number}")

    
    def _extract_submission_news_url(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract Commission news announcement URL about submission"""
        h2 = soup.find('h2', id='Submission-and-examination')
        
        if h2:
            first_p = h2.find_next_sibling('p')
            
            if first_p:
                links = first_p.find_all('a')
                
                for link in links:
                    href = link.get('href', '')
                    link_text = link.get_text().strip().lower()
                    
                    # Check if it's a press/news link
                    if any(keyword in link_text for keyword in ['press', 'announcement', 'news']):
                        if 'presscorner' in href or 'europa.eu/rapid' in href:
                            return href
        
        # If no news URL found, raise an error
        raise ValueError(f"No submission news URL found for initiative {self.registration_number}")
        
    # Procedural Timeline Milestones
    def _extract_commission_meeting_date(self, soup: BeautifulSoup) -> str:
        """Extract date of meeting with Commission officials (Article 15)"""
        try:
            # Find the "Submission and examination" section
            submission_section = soup.find('h2', id='Submission-and-examination')
            
            if not submission_section:
                # Try alternative heading formats
                submission_section = soup.find('h2', string=re.compile(r'Submission and examination', re.IGNORECASE))
            
            if not submission_section:
                raise ValueError(f"No submission section  for {self.registration_number}")
            
            # Get all paragraphs after the submission section
            paragraphs = []
            for sibling in submission_section.find_next_siblings():
                if sibling.name == 'h2':  # Stop at next section
                    break
                if sibling.name == 'p':
                    paragraphs.append(sibling)
            
            # Pattern 1: "On DD Month YYYY" or "on DD Month YYYY" (e.g., "on 25 March 2025")
            month_names = '|'.join(calendar.month_name[1:])
            date_pattern_month_name = rf'(?:On|on)\s+(\d{{1,2}}\s+(?:{month_names})\s+\d{{4}})'
            
            # Pattern 2: "on DD/MM/YYYY" (e.g., "on 09/04/2014")
            date_pattern_slash = rf'(?:On|on)\s+(\d{{2}}/\d{{2}}/\d{{4}})'
            
            # Look for the meeting sentence
            for p in paragraphs:
                text = p.get_text(strip=True)
                
                # Check if this is a commission meeting sentence
                if ('organisers met with' in text or 
                    'organisers were given the opportunity' in text):
                    
                    # Check if it mentions Commission officials
                    if ('Commission' in text and 
                        ('Vice-President' in text or 'Commissioner' in text or 'officials' in text)):
                        
                        # Try to extract the date with month name first
                        match = re.search(date_pattern_month_name, text, re.IGNORECASE)
                        if match:
                            date_str = match.group(1)
                            try:
                                date_obj = datetime.strptime(date_str, '%d %B %Y')
                                return date_obj.strftime('%Y-%m-%d')
                            except ValueError:
                                # If parsing fails, return the original date string
                                return date_str
                        
                        # Try to extract the date with slash format
                        match = re.search(date_pattern_slash, text, re.IGNORECASE)
                        if match:
                            date_str = match.group(1)
                            try:
                                # Parse DD/MM/YYYY format
                                date_obj = datetime.strptime(date_str, '%d/%m/%Y')
                                return date_obj.strftime('%Y-%m-%d')
                            except ValueError:
                                # If parsing fails, return the original date string
                                return date_str
            
            raise ValueError(f"No commission meeting date found in submission section for {self.registration_number}.")
            
        except Exception as e:
            raise ValueError(f"Error extracting commission meeting date for {self.registration_number}: {str(e)}") from e

    
    def _extract_commission_officials_met(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract names and titles of Commissioners/Vice-Presidents who met"""

        try:
            # Find the "Submission and examination" section
            submission_section = soup.find('h2', id='Submission-and-examination')
            
            if not submission_section:
                submission_section = soup.find('h2', string=re.compile(r'Submission and examination', re.IGNORECASE))
            
            if not submission_section:
                raise ValueError(f"No submission section for {self.registration_number}")
            
            # Get all paragraphs after the submission section
            paragraphs = []
            for sibling in submission_section.find_next_siblings():
                if sibling.name == 'h2':
                    break
                if sibling.name == 'p':
                    paragraphs.append(sibling)
            
            # Build date patterns (same as commission_meeting_date extraction)
            month_names = '|'.join(calendar.month_name[1:])
            date_pattern_month = rf'\d{{1,2}}\s+(?:{month_names})\s+\d{{4}}'
            date_pattern_slash = r'\d{2}/\d{2}/\d{4}'
            combined_date_pattern = f'(?:{date_pattern_month}|{date_pattern_slash})'
            
            # Look for the meeting sentence
            for p in paragraphs:
                text = p.get_text(strip=True)
                
                # Check if this is a commission meeting sentence
                if ('organisers met with' in text or 
                    'organisers were given the opportunity' in text):
                    
                    if ('Commission' in text and 
                        ('Vice-President' in text or 'Commissioner' in text or 'officials' in text)):
                        
                        officials_text = None
                        
                        # Pattern 1: "met with [OFFICIALS] on [DATE]"
                        if 'met with' in text:
                            pattern = rf'met with\s+(.+?)\s+on\s+{combined_date_pattern}'
                            match = re.search(pattern, text, re.IGNORECASE)
                            if match:
                                officials_text = match.group(1).strip()
                        
                        # Pattern 2: "meeting with [OFFICIALS] and European Commission officials"
                        if not officials_text and 'meeting with' in text:
                            match = re.search(r'meeting with\s+(.+?)\s+and European Commission officials', text, re.IGNORECASE)
                            if match:
                                officials_text = match.group(1).strip()
                        
                        if officials_text:

                            # Clean up the text
                            # Remove "the European Commission" prefix
                            officials_text = re.sub(r'^the\s+European\s+Commission\s+', '', officials_text, flags=re.IGNORECASE)
                            officials_text = re.sub(r'^European\s+Commission\s+', '', officials_text, flags=re.IGNORECASE)
                            officials_text = re.sub(r'^Commission\s+', '', officials_text, flags=re.IGNORECASE)
                            
                            # Remove "First" from "First Vice-President"
                            officials_text = re.sub(r'\bFirst\s+Vice-President\b', 'Vice-President', officials_text)
                            
                            # Split by " and " before title keywords
                            officials_parts = re.split(
                                r'\s+and\s+(?:the\s+)?(?=(?:Executive\s+)?Vice-President|Commissioner|Director-General|Deputy\s+Director-General)', 
                                officials_text
                                )
                            
                            # Clean each official entry
                            cleaned_officials = []

                            for official in officials_parts:
                                official = official.strip().rstrip(',')
                                if official:
                                    cleaned_officials.append(official)
                            
                            # Join with semicolon
                            result = '; '.join(cleaned_officials)
                            return result if result else None
            
            raise ValueError(f"No commission meeting found in submission section for {self.registration_number}")
            
        except Exception as e:
            raise ValueError(f"Error extracting commission officials for {self.registration_number}: {str(e)}") from e

    def _extract_parliament_hearing_date(self, soup) -> str:
        """Extracts and normalizes the European Parliament hearing date (DD-MM-YYYY)."""
        try:
            # 1. Extract submission text
            submission_text = self._extract_submission_text(soup)
            if not submission_text or not submission_text.strip():
                raise ValueError("No submission text found in HTML.")

            # 2. Lowercase and normalize whitespace
            text = submission_text.lower()
            text = re.sub(r'\s+', ' ', text).strip()

            # 3. Find sentence containing any of the key phrases (exact order)
            key_phrases = [
                'public hearing took place',
                'public hearing at the european parliament',
                'presentation of this initiative in a public hearing',
                'public hearing',
            ]

            # Split into sentences (simplified)
            sentences = re.split(r'(?<=[.!?])\s+', text)
            target_sentence = None
            matched_phrase = None

            for sent in sentences:
                for phrase in key_phrases:
                    if phrase in sent:
                        target_sentence = sent
                        matched_phrase = phrase
                        break
                if target_sentence:
                    break

            if not target_sentence:
                raise ValueError("No sentence found containing any key phrase.")

            # 4. Search for date AFTER the key phrase
            idx = target_sentence.find(matched_phrase)
            segment_after = target_sentence[idx + len(matched_phrase):]

            # Build list of valid month names and abbreviations using calendar
            month_names = [m.lower() for m in calendar.month_name if m]
            month_abbrs = [m.lower() for m in calendar.month_abbr if m]
            all_months = month_names + month_abbrs

            # Date regexes
            patterns = [
                # e.g. 24 january 2023
                rf'\b(\d{{1,2}})\s+({"|".join(all_months)})\s+(\d{{4}})\b',
                # e.g. 24/01/2023 or 24-01-2023
                r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b',
                # e.g. 2023-01-24
                r'\b(\d{4})[/-](\d{1,2})[/-](\d{1,2})\b',
            ]

            date_match = None
            for pat in patterns:
                m = re.search(pat, segment_after)
                if m:
                    date_match = m
                    pattern = pat
                    break

            if not date_match:
                raise ValueError("No date found after key phrase.")

            # 5. Normalize the found date
            # Create month mapping
            month_map = {calendar.month_name[i].lower(): str(i).zfill(2) for i in range(1, 13)}
            month_map.update({calendar.month_abbr[i].lower(): str(i).zfill(2) for i in range(1, 13)})

            # Normalize formats
            if pattern == patterns[0]:
                day, month_name, year = date_match.groups()
                month = month_map.get(month_name.lower())
                if not month:
                    raise ValueError(f"Invalid month name: {month_name}")
                date_str = f"{day.zfill(2)}-{month}-{year}"
            elif pattern == patterns[1]:
                day, month, year = date_match.groups()
                date_str = f"{day.zfill(2)}-{month.zfill(2)}-{year}"
            else:  # ISO 2023-01-24
                year, month, day = date_match.groups()
                date_str = f"{day.zfill(2)}-{month.zfill(2)}-{year}"

            # 6. Return normalized date
            return date_str

        except Exception as e:
            raise ValueError(
                f"Error extracting parliament hearing date for {self.registration_number}: {str(e)}"
            ) from e
    
    def _extract_parliament_hearing_recording_url(self, soup: BeautifulSoup) -> dict:
        """Extracts all relevant video recording URLs from the 'public hearing' paragraph.
        Returns a dict where keys are link texts (e.g. 'recording', 'extracts', 'public hearing')
        and values are absolute URLs.
        """

        try:
            # 1. Locate the "Submission and examination" section
            submission_section = soup.find('h2', id='Submission-and-examination')
            if not submission_section:
                submission_section = soup.find('h2', string=re.compile(r'Submission and examination', re.IGNORECASE))
            if not submission_section:
                raise ValueError(f"No submission section found for {self.registration_number}")

            # 2. Search paragraphs after the section for one describing a public hearing
            for sibling in submission_section.find_next_siblings():
                if sibling.name == 'h2':  # stop scanning at the next section
                    break
                if sibling.name != 'p':
                    continue

                # Normalize paragraph text (handle &nbsp;, etc.)
                paragraph_text = html.unescape(' '.join(sibling.stripped_strings)).lower()

                key_phrases = [
                    'public hearing took place',
                    'public hearing at the european parliament',
                    'presentation of this initiative in a public hearing',
                    'public hearing',
                ]

                if not any(phrase in paragraph_text for phrase in key_phrases):
                    continue  # skip irrelevant paragraphs

                # 3. Extract all <a> links and map text → href
                links_data = {}
                for link in sibling.find_all('a', href=True):
                    link_text = html.unescape(link.get_text(strip=True)).lower()
                    href = html.unescape(link['href'].strip())

                    if link_text and href:
                        links_data[link_text] = href

                # 4. If found any links, return JSON-style dict
                if links_data:
                    return links_data

            # 5. Nothing found
            raise ValueError(f"No parliament hearing paragraph with links found for {self.registration_number}")

        except Exception as e:
            raise ValueError(
                f"Error extracting parliament hearing recording URLs for {self.registration_number}: {str(e)}"
            ) from e

    def _extract_plenary_debate_date(self, soup: BeautifulSoup) -> str:
        """Extract date of plenary debate in Parliament
        
        Note: Plenary debates did not take place for initiatives registered in 2017 and earlier.
        Returns None when no plenary debate date is found (typically for older initiatives).
        """

        try:
            # 1. Locate the "Submission and examination" section
            submission_section = soup.find('h2', id='Submission-and-examination')
            if not submission_section:
                submission_section = soup.find('h2', string=re.compile(r'Submission and examination', re.IGNORECASE))
            if not submission_section:
                raise ValueError(f"No submission section found for {self.registration_number}")
            
            # 2. Find all paragraphs in the submission section
            paragraphs = submission_section.find_next_siblings('p')
            
            # Keywords that indicate plenary debate
            debate_keywords = [
                'initiative was debated at the European Parliament',
                'debate on this initiative was held in the plenary session'
            ]
            
            # 3. Find the paragraph containing plenary debate information
            debate_paragraph = None
            for p in paragraphs:
                # Use separator=' ' to ensure spaces between elements
                text = p.get_text(separator=' ', strip=True)
                # Normalize whitespace: replace non-breaking spaces and multiple spaces
                text = re.sub(r'\s+', ' ', text)
                
                if any(keyword in text for keyword in debate_keywords):
                    debate_paragraph = text
                    break
            
            if not debate_paragraph:
                return None
            
            # 4. Create month name to number mapping
            month_dict = {calendar.month_name[i].lower(): str(i).zfill(2) for i in range(1, 13)}
            
            # 5. Extract date - try text format first (e.g., "16 March 2023" or "10 June 2021")
            date_pattern = r'plenary session\s+(?:of\s+the\s+)?(?:European\s+Parliament\s+)?on\s+(\d{1,2})\s+(\w+)\s+(\d{4})'
            match = re.search(date_pattern, debate_paragraph, re.IGNORECASE)
            
            if match:
                day = match.group(1).zfill(2)
                month_name = match.group(2).lower()
                year = match.group(3)
                
                month_str = month_dict.get(month_name)
                if month_str is None:
                    raise ValueError(f"Invalid month name: {month_name}")
                
                return f"{day}-{month_str}-{year}"
            
            # 6. Try slash format (e.g., "16/03/2023")
            date_pattern_slash = r'plenary session\s+(?:of\s+the\s+)?(?:European\s+Parliament\s+)?on\s+(\d{1,2})/(\d{1,2})/(\d{4})'
            match = re.search(date_pattern_slash, debate_paragraph, re.IGNORECASE)
            
            if match:
                day = match.group(1).zfill(2)
                month = match.group(2).zfill(2)
                year = match.group(3)
                return f"{day}-{month}-{year}"
            
            # No date found in debate paragraph
            return None
            
        except Exception as e:
            raise ValueError(f"Error extracting plenary debate date for {self.registration_number}: {str(e)}") from e

            
    def _extract_plenary_debate_recording_url(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract video recording URL of plenary debate"""
        try:
            # Implementation here
            pass
        except Exception as e:
            raise ValueError(f"Error extracting plenary debate recording URL for {self.registration_number}: {str(e)}") from e
    
    def _extract_commission_communication_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract date Commission adopted official Communication"""
        try:
            # Implementation here
            pass
        except Exception as e:
            raise ValueError(f"Error extracting commission communication date for {self.registration_number}: {str(e)}") from e
    
    def _extract_commission_communication_url(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract link to full PDF of Commission Communication"""
        try:
            # Implementation here
            pass
        except Exception as e:
            raise ValueError(f"Error extracting commission communication URL for {self.registration_number}: {str(e)}") from e
    
    def _extract_commission_response_news_url(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract press release/news URL about Commission response"""
        try:
            # Implementation here
            pass
        except Exception as e:
            raise ValueError(f"Error extracting commission response news URL for {self.registration_number}: {str(e)}") from e
    
    # Commission Response Content
    def _extract_communication_main_conclusion(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract main conclusions text from Communication"""
        try:
            # Implementation here
            pass
        except Exception as e:
            raise ValueError(f"Error extracting communication main conclusion for {self.registration_number}: {str(e)}") from e
    
    def _extract_legislative_proposal_status(self, soup: BeautifulSoup) -> Optional[str]:
        """Determine if Commission proposed legislation, alternatives, or no action"""
        try:
            # Implementation here
            pass
        except Exception as e:
            raise ValueError(f"Error extracting legislative proposal status for {self.registration_number}: {str(e)}") from e
    
    def _extract_commission_response_summary(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract overall Commission position summary"""
        try:
            # Implementation here
            pass
        except Exception as e:
            raise ValueError(f"Error extracting commission response summary for {self.registration_number}: {str(e)}") from e
    
    # Follow-up Activities Section
    def _extract_has_followup_section(self, soup: BeautifulSoup) -> Optional[bool]:
        """Check if page includes follow-up activities section"""
        try:
            # Implementation here
            pass
        except Exception as e:
            raise ValueError(f"Error checking followup section for {self.registration_number}: {str(e)}") from e
    
    def _extract_followup_meeting_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract date of follow-up meetings after initial response"""
        try:
            # Implementation here
            pass
        except Exception as e:
            raise ValueError(f"Error extracting followup meeting date for {self.registration_number}: {str(e)}") from e
    
    def _extract_followup_meeting_officials(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract names of officials in follow-up meetings"""
        try:
            # Implementation here
            pass
        except Exception as e:
            raise ValueError(f"Error extracting followup meeting officials for {self.registration_number}: {str(e)}") from e
    
    def _extract_roadmap_launched(self, soup: BeautifulSoup) -> Optional[bool]:
        """Check if roadmap or action plan was initiated"""
        try:
            # Implementation here
            pass
        except Exception as e:
            raise ValueError(f"Error checking roadmap status for {self.registration_number}: {str(e)}") from e
    
    def _extract_roadmap_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract roadmap objectives description"""
        try:
            # Implementation here
            pass
        except Exception as e:
            raise ValueError(f"Error extracting roadmap description for {self.registration_number}: {str(e)}") from e
    
    def _extract_roadmap_completion_target(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract target date for roadmap completion"""
        try:
            # Implementation here
            pass
        except Exception as e:
            raise ValueError(f"Error extracting roadmap completion target for {self.registration_number}: {str(e)}") from e
    
    def _extract_workshop_conference_dates(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract dates of workshops/conferences as JSON array"""
        try:
            # Implementation here
            pass
        except Exception as e:
            raise ValueError(f"Error extracting workshop/conference dates for {self.registration_number}: {str(e)}") from e
    
    def _extract_partnership_programs(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract names of partnership programs established"""
        try:
            # Implementation here
            pass
        except Exception as e:
            raise ValueError(f"Error extracting partnership programs for {self.registration_number}: {str(e)}") from e
    
    def _extract_court_cases_referenced(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract Court of Justice case numbers"""
        try:
            # Implementation here
            pass
        except Exception as e:
            raise ValueError(f"Error extracting court cases for {self.registration_number}: {str(e)}") from e
    
    def _extract_court_judgment_dates(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract dates of court judgments"""
        try:
            # Implementation here
            pass
        except Exception as e:
            raise ValueError(f"Error extracting court judgment dates for {self.registration_number}: {str(e)}") from e
    
    def _extract_court_judgment_summary(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract brief court ruling descriptions"""
        try:
            # Implementation here
            pass
        except Exception as e:
            raise ValueError(f"Error extracting court judgment summary for {self.registration_number}: {str(e)}") from e
    
    def _extract_latest_update_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract most recent date from follow-up section"""
        try:
            # Implementation here
            pass
        except Exception as e:
            raise ValueError(f"Error extracting latest update date for {self.registration_number}: {str(e)}") from e
    
    # Multimedia and Documentation
    def _extract_factsheet_url(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract factsheet PDF URL"""
        try:
            # Implementation here
            pass
        except Exception as e:
            raise ValueError(f"Error extracting factsheet URL for {self.registration_number}: {str(e)}") from e
    
    def _extract_video_recording_count(self, soup: BeautifulSoup) -> Optional[int]:
        """Count number of video recordings linked"""
        try:
            # Implementation here
            pass
        except Exception as e:
            raise ValueError(f"Error counting video recordings for {self.registration_number}: {str(e)}") from e
    
    def _extract_has_dedicated_website(self, soup: BeautifulSoup) -> Optional[bool]:
        """Check if organizers maintained campaign website"""
        return False
    
    # Structural Analysis
    def _extract_related_eu_legislation(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract references to specific Regulations or Directives"""
        try:
            # Implementation here
            pass
        except Exception as e:
            raise ValueError(f"Error extracting related EU legislation for {self.registration_number}: {str(e)}") from e
    
    def _extract_petition_platforms_used(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract external platforms mentioned"""
        try:
            # Implementation here
            pass
        except Exception as e:
            raise ValueError(f"Error extracting petition platforms for {self.registration_number}: {str(e)}") from e
    
    def _calculate_follow_up_duration_months(self, commission_date: Optional[str], 
                                            latest_update: Optional[str]) -> Optional[int]:
        """Calculate months between Commission response and latest follow-up"""
        try:
            # Implementation here
            pass
        except Exception as e:
            raise ValueError(f"Error calculating follow-up duration for {self.registration_number}: {str(e)}") from e
    
    # Helper Methods
    def _parse_date(self, date_string: str) -> Optional[str]:
        """Parse and normalize date strings to ISO format"""
        try:
            # Implementation here
            pass
        except Exception as e:
            raise ValueError(f"Error parsing date for {self.registration_number}: {str(e)}") from e
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text (remove extra whitespace, normalize)"""
        try:
            # Implementation here
            pass
        except Exception as e:
            raise ValueError(f"Error cleaning text for {self.registration_number}: {str(e)}") from e
    
    def _extract_all_video_urls(self, soup: BeautifulSoup) -> List[str]:
        """Extract all video recording URLs from page"""
        try:
            # Implementation here
            pass
        except Exception as e:
            raise ValueError(f"Error extracting video URLs for {self.registration_number}: {str(e)}") from e
