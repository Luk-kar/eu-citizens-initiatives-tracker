"""
ECI Responses HTML Parser - Refactored with Separated Extractor Classes
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


class BaseExtractor:
    """Base class for all extractors with common utilities"""

    def __init__(self, logger: logging.Logger, registration_number: Optional[str] = None):
        self.logger = logger
        self.registration_number = registration_number

    def set_registration_number(self, registration_number: str):
        """Update registration number for error reporting"""
        self.registration_number = registration_number


class BasicMetadataExtractor(BaseExtractor):
    """Extracts basic initiative metadata: URLs and titles"""

    def extract_response_url(self, soup: BeautifulSoup) -> str:
        """Extract the response page URL from HTML

        Tries multiple methods to find the URL:
        1. Active language link in site header
        2. Link with hreflang="en"
        3. Canonical link from head
        4. og:url meta tag
        """
        try:
            # Method 1: Find the active language link in the site header
            active_language_link = soup.find(
                'a',
                class_='ecl-site-header__language-link--active'
            )

            if active_language_link and active_language_link.get('href'):
                response_url = active_language_link['href']
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
                "Expected one of: active language link, link with hreflang='en', "
                "canonical link tag, or og:url meta tag"
            )

        except Exception as e:
            raise ValueError(f"Error extracting response URL for initiative {self.registration_number}: {str(e)}") from e

    def extract_initiative_url(self, soup: BeautifulSoup) -> str:
        """Extract initiative URL from breadcrumb link or page links"""
        try:
            # Method 1: Find the breadcrumb link with text "Initiative detail"
            breadcrumb_link = soup.find(
                'a', 
                class_='ecl-breadcrumb__link', 
                string=lambda text: text and text.strip() == 'Initiative detail'
            )

            if breadcrumb_link and breadcrumb_link.get('href'):
                href = breadcrumb_link['href']

                if href.startswith('http'):
                    return href
                elif href.startswith('/'):
                    initiative_url = f"https://citizens-initiative.europa.eu{href}"
                    return initiative_url

            # Method 2: Search for any link matching /initiatives/details/YYYY/NNNNNN_en pattern
            all_links = soup.find_all('a', href=True, string=True)

            for link in all_links:
                href = link['href']
                link_text = link.get_text(strip=True)

                if not link_text:
                    continue

                if re.search(r'/initiatives/details/\d{4}/\d{6}_en$', href):
                    if href.startswith('http'):
                        self.logger.info(f"Found initiative URL in page link with text '{link_text}': {href}")
                        return href
                    elif href.startswith('/'):
                        initiative_url = f"https://citizens-initiative.europa.eu{href}"
                        self.logger.info(f"Found initiative URL in page link with text '{link_text}': {initiative_url}")
                        return initiative_url

            raise ValueError(
                f"Initiative URL not found for {self.registration_number}. "
                "Expected breadcrumb link with text 'Initiative detail' "
                "or link matching pattern /initiatives/details/YYYY/NNNNNN_en with text content"
            )

        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"Error extracting initiative URL for {self.registration_number}: {str(e)}") from e


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


class ProceduralTimelineExtractor(BaseExtractor):
    """Extracts procedural timeline milestones"""

    def extract_commission_meeting_date(self, soup: BeautifulSoup) -> str:
        """Extract date of meeting with Commission officials (Article 15)"""
        try:
            submission_section = soup.find('h2', id='Submission-and-examination')

            if not submission_section:
                submission_section = soup.find('h2', string=re.compile(r'Submission and examination', re.IGNORECASE))

            if not submission_section:
                raise ValueError(f"No submission section for {self.registration_number}")

            paragraphs = []
            for sibling in submission_section.find_next_siblings():
                if sibling.name == 'h2':
                    break
                if sibling.name == 'p':
                    paragraphs.append(sibling)

            month_names = '|'.join(calendar.month_name[1:])
            date_pattern_month_name = rf'(?:On|on)\s+(\d{{1,2}}\s+(?:{month_names})\s+\d{{4}})'
            date_pattern_slash = rf'(?:On|on)\s+(\d{{2}}/\d{{2}}/\d{{4}})'

            for p in paragraphs:
                text = p.get_text(strip=True)

                if ('organisers met with' in text or 
                    'organisers were given the opportunity' in text):

                    if ('Commission' in text and 
                        ('Vice-President' in text or 'Commissioner' in text or 'officials' in text)):

                        match = re.search(date_pattern_month_name, text, re.IGNORECASE)
                        if match:
                            date_str = match.group(1)
                            try:
                                date_obj = datetime.strptime(date_str, '%d %B %Y')
                                return date_obj.strftime('%Y-%m-%d')
                            except ValueError:
                                return date_str

                        match = re.search(date_pattern_slash, text, re.IGNORECASE)
                        if match:
                            date_str = match.group(1)
                            try:
                                date_obj = datetime.strptime(date_str, '%d/%m/%Y')
                                return date_obj.strftime('%Y-%m-%d')
                            except ValueError:
                                return date_str

            raise ValueError(f"No commission meeting date found in submission section for {self.registration_number}.")

        except Exception as e:
            raise ValueError(f"Error extracting commission meeting date for {self.registration_number}: {str(e)}") from e

    def extract_commission_officials_met(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract names and titles of Commissioners/Vice-Presidents who met"""
        try:
            submission_section = soup.find('h2', id='Submission-and-examination')

            if not submission_section:
                submission_section = soup.find('h2', string=re.compile(r'Submission and examination', re.IGNORECASE))

            if not submission_section:
                raise ValueError(f"No submission section for {self.registration_number}")

            paragraphs = []
            for sibling in submission_section.find_next_siblings():
                if sibling.name == 'h2':
                    break
                if sibling.name == 'p':
                    paragraphs.append(sibling)

            month_names = '|'.join(calendar.month_name[1:])
            date_pattern_month = rf'\d{{1,2}}\s+(?:{month_names})\s+\d{{4}}'
            date_pattern_slash = r'\d{2}/\d{2}/\d{4}'
            combined_date_pattern = f'(?:{date_pattern_month}|{date_pattern_slash})'

            for p in paragraphs:
                text = p.get_text(strip=True)

                if ('organisers met with' in text or 
                    'organisers were given the opportunity' in text):

                    if ('Commission' in text and 
                        ('Vice-President' in text or 'Commissioner' in text or 'officials' in text)):

                        officials_text = None

                        if 'met with' in text:
                            pattern = rf'met with\s+(.+?)\s+on\s+{combined_date_pattern}'
                            match = re.search(pattern, text, re.IGNORECASE)
                            if match:
                                officials_text = match.group(1).strip()

                        if not officials_text and 'meeting with' in text:
                            match = re.search(r'meeting with\s+(.+?)\s+and European Commission officials', text, re.IGNORECASE)
                            if match:
                                officials_text = match.group(1).strip()

                        if officials_text:
                            officials_text = re.sub(r'^the\s+European\s+Commission\s+', '', officials_text, flags=re.IGNORECASE)
                            officials_text = re.sub(r'^European\s+Commission\s+', '', officials_text, flags=re.IGNORECASE)
                            officials_text = re.sub(r'^Commission\s+', '', officials_text, flags=re.IGNORECASE)
                            officials_text = re.sub(r'\bFirst\s+Vice-President\b', 'Vice-President', officials_text)

                            officials_parts = re.split(
                                r'\s+and\s+(?:the\s+)?(?=(?:Executive\s+)?Vice-President|Commissioner|Director-General|Deputy\s+Director-General)', 
                                officials_text
                            )

                            cleaned_officials = []
                            for official in officials_parts:
                                official = official.strip().rstrip(',')
                                if official:
                                    cleaned_officials.append(official)

                            result = '; '.join(cleaned_officials)
                            return result if result else None

            raise ValueError(f"No commission meeting found in submission section for {self.registration_number}")

        except Exception as e:
            raise ValueError(f"Error extracting commission officials for {self.registration_number}: {str(e)}") from e


class ParliamentActivityExtractor(BaseExtractor):
    """Extracts Parliament hearing and plenary debate data"""

    def extract_parliament_hearing_date(self, soup: BeautifulSoup) -> str:
        """Extracts and normalizes the European Parliament hearing date"""
        try:
            submission_text_extractor = SubmissionDataExtractor(self.logger, self.registration_number)
            submission_text = submission_text_extractor.extract_submission_text(soup)

            if not submission_text or not submission_text.strip():
                raise ValueError("No submission text found in HTML.")

            text = submission_text.lower()
            text = re.sub(r'\s+', ' ', text).strip()

            key_phrases = [
                'public hearing took place',
                'public hearing at the european parliament',
                'presentation of this initiative in a public hearing',
                'public hearing',
            ]

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

            idx = target_sentence.find(matched_phrase)
            segment_after = target_sentence[idx + len(matched_phrase):]

            month_names = [m.lower() for m in calendar.month_name if m]
            month_abbrs = [m.lower() for m in calendar.month_abbr if m]
            all_months = month_names + month_abbrs

            # Pattern 1: Matches date format "24 January 2023" or "5 April 2023"
            # Pattern 2: Matches date format "17/02/2014" or "5-3-2020"
            # Pattern 3: Matches ISO date format "2023-01-24" or "2020/12/31"
            patterns = [
                rf'\b(\d{{1,2}})\s+({"|".join(all_months)})\s+(\d{{4}})\b',  
                r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b',                  
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

            month_map = {calendar.month_name[i].lower(): str(i).zfill(2) for i in range(1, 13)}
            month_map.update({calendar.month_abbr[i].lower(): str(i).zfill(2) for i in range(1, 13)})

            if pattern == patterns[0]:
                day, month_name, year = date_match.groups()
                month = month_map.get(month_name.lower())
                if not month:
                    raise ValueError(f"Invalid month name: {month_name}")
                date_str = f"{day.zfill(2)}-{month}-{year}"
            elif pattern == patterns[1]:
                day, month, year = date_match.groups()
                date_str = f"{day.zfill(2)}-{month.zfill(2)}-{year}"
            else:
                year, month, day = date_match.groups()
                date_str = f"{day.zfill(2)}-{month.zfill(2)}-{year}"

            return date_str

        except Exception as e:
            raise ValueError(
                f"Error extracting parliament hearing date for {self.registration_number}: {str(e)}"
            ) from e

    def extract_parliament_hearing_video_urls(self, soup: BeautifulSoup) -> dict:
        """Extracts all relevant video recording URLs from the 'public hearing' paragraph"""
        try:
            submission_section = soup.find('h2', id='Submission-and-examination')
            if not submission_section:
                submission_section = soup.find('h2', string=re.compile(r'Submission and examination', re.IGNORECASE))
            if not submission_section:
                raise ValueError(f"No submission section found for {self.registration_number}")

            for sibling in submission_section.find_next_siblings():
                if sibling.name == 'h2':
                    break
                if sibling.name != 'p':
                    continue

                paragraph_text = html.unescape(' '.join(sibling.stripped_strings)).lower()

                key_phrases = [
                    'public hearing took place',
                    'public hearing at the european parliament',
                    'presentation of this initiative in a public hearing',
                    'public hearing',
                ]

                if not any(phrase in paragraph_text for phrase in key_phrases):
                    continue

                links_data = {}
                for link in sibling.find_all('a', href=True):
                    link_text = html.unescape(link.get_text(strip=True)).lower()
                    href = html.unescape(link['href'].strip())

                    if link_text and href:
                        links_data[link_text] = href

                if links_data:
                    return links_data

            raise ValueError(f"No parliament hearing paragraph with links found for {self.registration_number}")

        except Exception as e:
            raise ValueError(
                f"Error extracting parliament hearing recording URLs for {self.registration_number}: {str(e)}"
            ) from e

    def extract_plenary_debate_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract date of plenary debate in Parliament"""
        try:
            submission_section = soup.find('h2', id='Submission-and-examination')
            if not submission_section:
                submission_section = soup.find('h2', string=re.compile(r'Submission and examination', re.IGNORECASE))
            if not submission_section:
                raise ValueError(f"No submission section found for {self.registration_number}")

            paragraphs = submission_section.find_next_siblings('p')

            debate_keywords = [
                'initiative was debated at the European Parliament',
                'debate on this initiative was held in the plenary session'
            ]

            debate_paragraph = None
            for p in paragraphs:
                text = p.get_text(separator=' ', strip=True)
                text = re.sub(r'\s+', ' ', text)

                if any(keyword in text for keyword in debate_keywords):
                    debate_paragraph = text
                    break

            if not debate_paragraph:
                return None

            month_dict = {calendar.month_name[i].lower(): str(i).zfill(2) for i in range(1, 13)}

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

            date_pattern_slash = r'plenary session\s+(?:of\s+the\s+)?(?:European\s+Parliament\s+)?on\s+(\d{1,2})/(\d{1,2})/(\d{4})'
            match = re.search(date_pattern_slash, debate_paragraph, re.IGNORECASE)

            if match:
                day = match.group(1).zfill(2)
                month = match.group(2).zfill(2)
                year = match.group(3)
                return f"{day}-{month}-{year}"

            return None

        except Exception as e:
            raise ValueError(f"Error extracting plenary debate date for {self.registration_number}: {str(e)}") from e

    def extract_plenary_debate_video_urls(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract video recording URL of plenary debate as JSON"""
        try:
            submission_section = soup.find('h2', id='Submission-and-examination')
            if not submission_section:
                submission_section = soup.find('h2', string=re.compile(r'Submission and examination', re.IGNORECASE))
            if not submission_section:
                raise ValueError(f"No submission section found for {self.registration_number}")

            paragraphs = submission_section.find_next_siblings('p')

            debate_keywords = [
                'initiative was debated at the European Parliament',
                'debate on this initiative was held in the plenary session'
            ]

            debate_paragraph = None
            for p in paragraphs:
                text = p.get_text(separator=' ', strip=True)
                text = re.sub(r'\s+', ' ', text)

                if any(keyword in text for keyword in debate_keywords):
                    debate_paragraph = p
                    break

            if not debate_paragraph:
                return None

            links = debate_paragraph.find_all('a')

            if not links:
                return None

            links_dict = {}
            for link in links:
                link_text = link.get_text(strip=True)
                link_url = link.get('href', '')

                if link_text and link_url:
                    links_dict[link_text] = link_url

            if not links_dict:
                return None

            return json.dumps(links_dict)

        except Exception as e:
            raise ValueError(f"Error extracting plenary debate recording URL for {self.registration_number}: {str(e)}") from e


class CommissionResponseExtractor(BaseExtractor):
    """Extracts Commission communication and response data"""

    def extract_commission_communication_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract date Commission adopted official Communication"""
        try:
            submission_section = soup.find('h2', id='Submission-and-examination')
            if not submission_section:
                submission_section = soup.find('h2', string=re.compile(r'Submission and examination', re.IGNORECASE))
            if not submission_section:
                raise ValueError(f"No submission section found for {self.registration_number}")

            paragraphs = submission_section.find_next_siblings('p')

            commission_paragraph = None
            for p in paragraphs:
                text = p.get_text(separator=' ', strip=True)
                text = re.sub(r'\s+', ' ', text)

                if 'Commission adopted a Communication on' in text:
                    commission_paragraph = text
                    break

            if not commission_paragraph:
                return None

            month_dict = {calendar.month_name[i].lower(): str(i).zfill(2) for i in range(1, 13)}

            date_pattern = r'Commission adopted a Communication on\s+(\d{1,2})\s+(\w+)\s+(\d{4})'
            match = re.search(date_pattern, commission_paragraph, re.IGNORECASE)

            if match:
                day = match.group(1).zfill(2)
                month_name = match.group(2).lower()
                year = match.group(3)

                month_str = month_dict.get(month_name)
                if month_str is None:
                    raise ValueError(f"Invalid month name: {month_name}")

                return f"{day}-{month_str}-{year}"

            date_pattern_slash = r'Commission adopted a Communication on\s+(\d{1,2})/(\d{1,2})/(\d{4})'
            match = re.search(date_pattern_slash, commission_paragraph, re.IGNORECASE)

            if match:
                day = match.group(1).zfill(2)
                month = match.group(2).zfill(2)
                year = match.group(3)
                return f"{day}-{month}-{year}"

            return None

        except Exception as e:
            raise ValueError(f"Error extracting commission communication date for {self.registration_number}: {str(e)}") from e

    def extract_commission_communication_url(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract link to full PDF of Commission Communication as JSON"""
        try:
            submission_section = soup.find('h2', id='Submission-and-examination')
            if not submission_section:
                submission_section = soup.find('h2', string=re.compile(r'Submission and examination', re.IGNORECASE))
            if not submission_section:
                raise ValueError(f"No submission section found for {self.registration_number}")

            paragraphs = submission_section.find_next_siblings('p')

            commission_paragraph_element = None
            for p in paragraphs:
                text = p.get_text(separator=' ', strip=True)
                text = re.sub(r'\s+', ' ', text)

                if re.search(r'Commission\s+adopted\s+a\s+Communication\s+on', text, re.IGNORECASE):
                    commission_paragraph_element = p
                    break

            if not commission_paragraph_element:
                return None

            links = commission_paragraph_element.find_all('a')

            if not links:
                return None

            links_dict = {}
            for link in links:
                link_text = link.get_text(strip=True)
                link_url = link.get('href', '')

                if link_text and link_url:
                    links_dict[link_text] = link_url

            if not links_dict:
                return None

            exclude_patterns = [
                r'https?://ec\.citizens-initiative\.europa\.eu/public/initiatives/successful/details/\d{4}/\d{6}(_[a-z]{2})?/?$',
                r'https?://citizens-initiative\.europa\.eu/initiatives/details/\d{4}/\d{6}[_]?[a-z]{2}/?$'
            ]

            filtered_links_dict = {}
            for text, url in links_dict.items():
                should_exclude = False
                for pattern in exclude_patterns:
                    if re.match(pattern, url):
                        should_exclude = True
                        break

                if not should_exclude:
                    filtered_links_dict[text] = url

            if not filtered_links_dict:
                return None

            return json.dumps(filtered_links_dict)

        except Exception as e:
            raise ValueError(f"Error extracting commission communication URL for {self.registration_number}: {str(e)}") from e

    def extract_communication_main_conclusion(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract main conclusions text from Communication"""
        try:
            return None
        except Exception as e:
            raise ValueError(f"Error extracting communication main conclusion for {self.registration_number}: {str(e)}") from e

    def extract_legislative_proposal_status(self, soup: BeautifulSoup) -> Optional[str]:
        """Determine if Commission proposed legislation, alternatives, or no action"""
        try:
            return None
        except Exception as e:
            raise ValueError(f"Error extracting legislative proposal status for {self.registration_number}: {str(e)}") from e

    def extract_commission_response_summary(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract overall Commission position summary"""
        try:
            return None
        except Exception as e:
            raise ValueError(f"Error extracting commission response summary for {self.registration_number}: {str(e)}") from e


class FollowUpActivityExtractor(BaseExtractor):
    """Extracts follow-up activities data"""

    def extract_has_followup_section(self, soup: BeautifulSoup) -> Optional[bool]:
        """Check if page includes follow-up activities section"""
        try:
            return None
        except Exception as e:
            raise ValueError(f"Error checking followup section for {self.registration_number}: {str(e)}") from e

    def extract_followup_meeting_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract date of follow-up meetings after initial response"""
        try:
            return None
        except Exception as e:
            raise ValueError(f"Error extracting followup meeting date for {self.registration_number}: {str(e)}") from e

    def extract_followup_meeting_officials(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract names of officials in follow-up meetings"""
        try:
            return None
        except Exception as e:
            raise ValueError(f"Error extracting followup meeting officials for {self.registration_number}: {str(e)}") from e

    def extract_roadmap_launched(self, soup: BeautifulSoup) -> Optional[bool]:
        """Check if roadmap or action plan was initiated"""
        try:
            return None
        except Exception as e:
            raise ValueError(f"Error checking roadmap status for {self.registration_number}: {str(e)}") from e

    def extract_roadmap_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract roadmap objectives description"""
        try:
            return None
        except Exception as e:
            raise ValueError(f"Error extracting roadmap description for {self.registration_number}: {str(e)}") from e

    def extract_roadmap_completion_target(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract target date for roadmap completion"""
        try:
            return None
        except Exception as e:
            raise ValueError(f"Error extracting roadmap completion target for {self.registration_number}: {str(e)}") from e

    def extract_workshop_conference_dates(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract dates of workshops/conferences as JSON array"""
        try:
            return None
        except Exception as e:
            raise ValueError(f"Error extracting workshop/conference dates for {self.registration_number}: {str(e)}") from e

    def extract_partnership_programs(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract names of partnership programs established"""
        try:
            return None
        except Exception as e:
            raise ValueError(f"Error extracting partnership programs for {self.registration_number}: {str(e)}") from e

    def extract_court_cases_referenced(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract Court of Justice case numbers"""
        try:
            return None
        except Exception as e:
            raise ValueError(f"Error extracting court cases for {self.registration_number}: {str(e)}") from e

    def extract_court_judgment_dates(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract dates of court judgments"""
        try:
            return None
        except Exception as e:
            raise ValueError(f"Error extracting court judgment dates for {self.registration_number}: {str(e)}") from e

    def extract_court_judgment_summary(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract brief court ruling descriptions"""
        try:
            return None
        except Exception as e:
            raise ValueError(f"Error extracting court judgment summary for {self.registration_number}: {str(e)}") from e

    def extract_latest_update_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract most recent date from follow-up section"""
        try:
            return None
        except Exception as e:
            raise ValueError(f"Error extracting latest update date for {self.registration_number}: {str(e)}") from e


class MultimediaDocumentationExtractor(BaseExtractor):
    """Extracts multimedia and documentation links"""

    def extract_factsheet_url(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract factsheet PDF URL"""
        try:
            return None
        except Exception as e:
            raise ValueError(f"Error extracting factsheet URL for {self.registration_number}: {str(e)}") from e

    def extract_video_recording_count(self, soup: BeautifulSoup) -> Optional[int]:
        """Count number of video recordings linked"""
        try:
            return None
        except Exception as e:
            raise ValueError(f"Error counting video recordings for {self.registration_number}: {str(e)}") from e

    def extract_has_dedicated_website(self, soup: BeautifulSoup) -> Optional[bool]:
        """Check if organizers maintained campaign website"""
        return False


class StructuralAnalysisExtractor(BaseExtractor):
    """Extracts structural analysis data"""

    def extract_related_eu_legislation(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract references to specific Regulations or Directives"""
        try:
            return None
        except Exception as e:
            raise ValueError(f"Error extracting related EU legislation for {self.registration_number}: {str(e)}") from e

    def extract_petition_platforms_used(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract external platforms mentioned"""
        try:
            return None
        except Exception as e:
            raise ValueError(f"Error extracting petition platforms for {self.registration_number}: {str(e)}") from e

    def calculate_follow_up_duration_months(self, commission_date: Optional[str], 
                                           latest_update: Optional[str]) -> Optional[int]:
        """Calculate months between Commission response and latest follow-up"""
        try:
            return None
        except Exception as e:
            raise ValueError(f"Error calculating follow-up duration for {self.registration_number}: {str(e)}") from e


class ECIResponseHTMLParser:
    """Main parser that orchestrates all extractor classes"""

    def __init__(self, logger: logging.Logger):
        """Initialize parser with shared logger"""
        self.logger = logger
        self._registration_number = None  # Sets private field directly, no setter called

        # Initialize all extractor instances
        self.basic_metadata = BasicMetadataExtractor(logger)
        self.submission_data = SubmissionDataExtractor(logger)
        self.procedural_timeline = ProceduralTimelineExtractor(logger)
        self.parliament_activity = ParliamentActivityExtractor(logger)
        self.commission_response = CommissionResponseExtractor(logger)
        self.followup_activity = FollowUpActivityExtractor(logger)
        self.multimedia_docs = MultimediaDocumentationExtractor(logger)
        self.structural_analysis = StructuralAnalysisExtractor(logger)

    @property
    def registration_number(self):
        """Get registration number"""

        return self._registration_number
    
    @registration_number.setter
    def registration_number(self, value):
        """Set registration number and propagate to all extractors"""

        self._registration_number = value

        # Automatically update ALL extractors
        for extractor in [self.basic_metadata, self.submission_data, 
                         self.procedural_timeline, self.parliament_activity, 
                         self.commission_response, self.followup_activity,
                         self.multimedia_docs, self.structural_analysis]:
            extractor.set_registration_number(value)

    def parse_file(self, html_path: Path, responses_list_data: Dict) -> Optional[ECICommissionResponseRecord]:
        """Parse a single ECI response HTML file and extract data"""
        try:
            self.logger.info(f"Parsing response file: {html_path.name}")

            self.registration_number = responses_list_data['registration_number']

            # Update registration number in all extractors
            for extractor in [self.basic_metadata, self.submission_data, self.procedural_timeline,
                            self.parliament_activity, self.commission_response, self.followup_activity,
                            self.multimedia_docs, self.structural_analysis]:
                extractor.set_registration_number(self.registration_number)

            # Read and parse HTML file
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()

            soup = BeautifulSoup(html_content, 'html.parser')

            current_timestamp = datetime.now().isoformat()

            # Extract commission communication date for follow-up calculation
            commission_communication_date = self.commission_response.extract_commission_communication_date(soup)
            latest_update_date = self.followup_activity.extract_latest_update_date(soup)

            # Create and return ECI Response object using extractors
            response = ECICommissionResponseRecord(
                # Basic Initiative Metadata
                response_url=self.basic_metadata.extract_response_url(soup),
                initiative_url=self.basic_metadata.extract_initiative_url(soup),
                initiative_title=responses_list_data.get('title'),
                registration_number=self.registration_number,

                # Submission text
                submission_text=self.submission_data.extract_submission_text(soup),

                # Submission and Verification Data
                commission_submission_date=self.submission_data.extract_commission_submission_date(soup),
                submission_news_url=self.submission_data.extract_submission_news_url(soup),

                # Procedural Timeline Milestones
                commission_meeting_date=self.procedural_timeline.extract_commission_meeting_date(soup),
                commission_officials_met=self.procedural_timeline.extract_commission_officials_met(soup),
                parliament_hearing_date=self.parliament_activity.extract_parliament_hearing_date(soup),
                parliament_hearing_video_urls=self.parliament_activity.extract_parliament_hearing_video_urls(soup),
                plenary_debate_date=self.parliament_activity.extract_plenary_debate_date(soup),
                plenary_debate_video_urls=self.parliament_activity.extract_plenary_debate_video_urls(soup),
                commission_communication_date=commission_communication_date,
                commission_communication_url=self.commission_response.extract_commission_communication_url(soup),

                # Commission Response Content
                communication_main_conclusion=self.commission_response.extract_communication_main_conclusion(soup),
                legislative_proposal_status=self.commission_response.extract_legislative_proposal_status(soup),
                commission_response_summary=self.commission_response.extract_commission_response_summary(soup),

                # Follow-up Activities Section
                has_followup_section=self.followup_activity.extract_has_followup_section(soup),
                followup_meeting_date=self.followup_activity.extract_followup_meeting_date(soup),
                followup_meeting_officials=self.followup_activity.extract_followup_meeting_officials(soup),
                roadmap_launched=self.followup_activity.extract_roadmap_launched(soup),
                roadmap_description=self.followup_activity.extract_roadmap_description(soup),
                roadmap_completion_target=self.followup_activity.extract_roadmap_completion_target(soup),
                workshop_conference_dates=self.followup_activity.extract_workshop_conference_dates(soup),
                partnership_programs=self.followup_activity.extract_partnership_programs(soup),
                court_cases_referenced=self.followup_activity.extract_court_cases_referenced(soup),
                court_judgment_dates=self.followup_activity.extract_court_judgment_dates(soup),
                court_judgment_summary=self.followup_activity.extract_court_judgment_summary(soup),
                latest_update_date=latest_update_date,

                # Multimedia and Documentation Links
                factsheet_url=self.multimedia_docs.extract_factsheet_url(soup),
                video_recording_count=self.multimedia_docs.extract_video_recording_count(soup),
                dedicated_website=self.multimedia_docs.extract_has_dedicated_website(soup),

                # Structural Analysis Flags
                related_eu_legislation=self.structural_analysis.extract_related_eu_legislation(soup),
                petition_platforms_used=self.structural_analysis.extract_petition_platforms_used(soup),
                follow_up_duration_months=self.structural_analysis.calculate_follow_up_duration_months(
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
