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
from typing import Dict, Optional

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

    def extract_official_communication_adoption_date(self, soup: BeautifulSoup) -> Optional[str]:
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

    def extract_official_communication_document_urls(self, soup: BeautifulSoup) -> Optional[str]:
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

    def extract_commission_answer_text(self, soup: BeautifulSoup) -> str:
        """Extract main conclusions text from Communication, excluding factsheet downloads
        
        Raises:
            ValueError: If the Commission answer section cannot be found or extracted
        """
        try:
            # Find the "Answer of the European Commission" header
            answer_header = soup.find('h2', id='Answer-of-the-European-Commission')
            
            if not answer_header:
                # Alternative: find h2 containing the text
                answer_header = soup.find('h2', string=lambda text: text and 'Answer of the European Commission' in text)
            
            if not answer_header:
                raise ValueError(
                    f"Could not find 'Answer of the European Commission' section for {self.registration_number}"
                )
            
            # Collect all content between this header and the Follow-up header
            content_parts = []
            current = answer_header.find_next_sibling()
            
            while current:
                # Stop if we hit Follow-up or another major section
                if current.name == 'h2':
                    h2_id = current.get('id', '')
                    h2_text = current.get_text(strip=True)
                    if 'Follow-up' in h2_text or h2_id == 'Follow-up':
                        break
                    # Also stop at other major sections
                    if h2_id and h2_id != 'Answer-of-the-European-Commission':
                        break
                
                # Skip factsheet file download components (ecl-file divs)
                if current.name == 'div' and 'ecl-file' in current.get('class', []):
                    current = current.find_next_sibling()
                    continue
                
                # Extract and format content from this element
                if current.name:
                    element_text = self._extract_element_with_links(current)
                    if element_text:
                        content_parts.append(element_text)
                
                current = current.find_next_sibling()
            
            if not content_parts:
                raise ValueError(
                    f"No content found in 'Answer of the European Commission' section for {self.registration_number}"
                )
            
            return '\n'.join(content_parts).strip()
            
        except ValueError:
            # Re-raise ValueError as-is
            raise
        except Exception as e:
            raise ValueError(
                f"Error extracting communication main conclusion for {self.registration_number}: {str(e)}"
            ) from e

    def _extract_element_with_links(self, element) -> str:
        """Helper to extract text while preserving links in markdown format"""

        if not element.name:
            return ''
        
        # Skip ecl-file components completely
        if element.name == 'div' and 'ecl-file' in element.get('class', []):
            return ''
        
        # For elements with links, convert to markdown
        if element.name == 'a':
            link_text = element.get_text(strip=True)
            href = element.get('href', '')
            return f'[{link_text}]({href})'
        
        # For list items, extract with links
        if element.name == 'li':
            text_parts = []
            for child in element.children:
                if hasattr(child, 'name'):
                    if child.name == 'a':
                        link_text = child.get_text(strip=True)
                        href = child.get('href', '')
                        text_parts.append(f'[{link_text}]({href})')
                    else:
                        child_text = child.get_text(strip=True)
                        if child_text:
                            text_parts.append(child_text)
                else:
                    child_text = str(child).strip()
                    if child_text:
                        text_parts.append(child_text)
            return ' '.join(text_parts)
        
        # For paragraphs and other elements, process children to preserve links
        if element.find('a'):
            text_parts = []
            for child in element.descendants:
                if isinstance(child, str):
                    text = child.strip()
                    if text and text not in ['', '\n']:
                        text_parts.append(text)
                elif hasattr(child, 'name') and child.name == 'a':
                    link_text = child.get_text(strip=True)
                    href = child.get('href', '')
                    if link_text:
                        text_parts.append(f'[{link_text}]({href})')
            return ' '.join(text_parts)
        
        # Default: return plain text
        return element.get_text(strip=True)


from typing import Optional


class LegislativeOutcomeClassifier:
    """Helper class for matching legislative status patterns in ECI response text"""
    
    # Pattern constants for status detection
    APPLICABLE_PATTERNS = [
        'became applicable',
        'became applicable immediately',
        'and applicable from'
    ]
    
    ADOPTION_EVIDENCE = [
        'council of the eu adopted',
        'council adopted the regulation',
        'published in the official journal',
        'following the agreement of the european parliament'
    ]
    
    COMMITMENT_PATTERNS = [
        'committed to come forward with a legislative proposal',
        'communicated its intention to table a legislative proposal',
        'intention to table a legislative proposal'
    ]
    
    REJECTION_PATTERNS = [
        'will not make a legislative proposal',
        'decided not to submit a legislative proposal',
        'has decided not to submit a legislative proposal'
    ]
    
    EXISTING_FRAMEWORK_PATTERNS = [
        'existing funding framework',
        'existing legislation',
        'already covered',
        'already in place',
        'legislation and policies already in place',
        'recently debated and agreed',
        'is the appropriate one',
        'policies already in place'
    ]
    
    ASSESSMENT_INDICATORS = [
        'launch',
        'started working on',
        'external study to be carried out',
        'call for evidence',
        'preparatory work',
        'with a view to launch'
    ]
    
    # Citizen-friendly status names mapping
    STATUS_CITIZEN_NAMES = {
        'applicable': 'New Law in Force',
        'adopted': 'Law Approved',
        'committed': 'Law Promised',
        'assessment_pending': 'Being Studied',
        'roadmap_development': 'Action Plan Being Created',
        'rejected_already_covered': 'Already Addressed',
        'rejected_with_actions': 'Alternative Actions Taken',
        'rejected': 'Rejected',
        'non_legislative_action': 'Policy Changes Only',
        'proposal_pending_adoption': 'Existing Proposals Under Review',
    }
    
    def __init__(self, content: str):
        """
        Initialize with normalized content string
        
        Args:
            content: Text content from ECI Commission response
        """

        self.content = content.lower()
    
    def check_applicable(self) -> bool:
        """
        Check if initiative reached applicable status (law is in force)
        
        Returns:
            True if law became applicable, False otherwise
        """

        # Direct applicable phrases
        if any(phrase in self.content for phrase in self.APPLICABLE_PATTERNS):
            return True
        
        # "Entered into force" with adoption evidence
        if 'entered into force' in self.content:
            if any(phrase in self.content for phrase in self.ADOPTION_EVIDENCE):
                return True
        
        # "Applies from" with legislation context
        if 'applies from' in self.content or 'apply from' in self.content:
            if any(word in self.content for word in ['adopted', 'regulation', 'directive']):
                return True
        
        return False
    
    def check_adopted(self) -> bool:
        """
        Check if proposal was adopted but not yet applicable
        
        Returns:
            True if adopted but not yet in force, False otherwise
        """

        # Published in Official Journal (but not applicable yet)
        if 'published in the official journal' in self.content or 'official journal of the eu' in self.content:
            if 'became applicable' not in self.content and 'applies from' not in self.content:
                return True
        
        # Adopted by Commission or Council
        if any(phrase in self.content for phrase in [
            'was adopted by the commission',
            'council of the eu adopted',
            'council adopted the regulation'
        ]):
            return True
        
        return False
    
    def check_committed(self) -> bool:
        """
        Check if Commission committed to legislative proposal
        
        Returns:
            True if commitment to legislation exists, False otherwise
        """

        # Standard commitment patterns
        if any(phrase in self.content for phrase in self.COMMITMENT_PATTERNS):
            return True
        
        # "To table a legislative proposal by [date]"
        if 'to table a legislative proposal' in self.content and 'by' in self.content:
            return True
        
        return False
    
    def check_assessment_pending(self) -> bool:
        """
        Check if initiative is in assessment phase
        
        Returns:
            True if assessment ongoing, False otherwise
        """

        # Avoid false positives with higher status
        if 'intention to table a legislative proposal' in self.content or 'became applicable' in self.content:
            return False
        
        # EFSA scientific opinion pending
        if 'tasked' in self.content and 'efsa' in self.content and 'scientific opinion' in self.content:
            return True
        
        # Impact assessment ongoing
        if 'impact assessment' in self.content:
            if any(phrase in self.content for phrase in self.ASSESSMENT_INDICATORS):
                return True
        
        # Future communication expected
        if 'will communicate' in self.content and ('by' in self.content or 'after' in self.content):
            return True
        
        return False
    
    def check_roadmap_development(self) -> bool:
        """
        Check if roadmap is being developed
        
        Returns:
            True if roadmap in development, False otherwise
        """

        if 'became applicable' in self.content:
            return False
        
        # Check for roadmap with various development verbs
        if 'roadmap' not in self.content:
            return False
        
        # Roadmap action indicators
        roadmap_indicators = [
            'develop',           # "develop a roadmap"
            'work on',           # "work on a roadmap"
            'work together',     # "work together on a roadmap"
            'work with',         # "work with parties on a roadmap"
            'launched',          # "launched a roadmap"
            'started work',      # "started work on a roadmap"
            'will work',         # "will work on a roadmap"
            'working on',        # "working on a roadmap"
            'preparing',         # "preparing a roadmap"
            'towards',           # "roadmap towards" (specific pattern)
        ]
        
        return any(indicator in self.content for indicator in roadmap_indicators)

    def check_rejection_type(self) -> Optional[str]:
        """
        Determine rejection type if initiative was rejected
        
        Returns:
            'rejected', 'rejected_with_actions', 'rejected_already_covered', or None
        """

        # Check for primary rejection phrases
        has_primary_rejection = any(phrase in self.content for phrase in self.REJECTION_PATTERNS)
        
        # Check for alternative rejection patterns
        has_no_legal_acts = (
            'no further legal acts are proposed' in self.content or 
            'no new legislation will be proposed' in self.content
        )
        has_no_repeal = 'no repeal' in self.content and 'was proposed' in self.content
        
        if not (has_primary_rejection or has_no_legal_acts or has_no_repeal):
            return None
        
        # Special case: no repeal with actions
        if has_no_repeal:
            if 'committed' in self.content or 'will continue' in self.content:
                return 'rejected_with_actions'
            return 'rejected'
        
        # Determine rejection subtype
        if any(phrase in self.content for phrase in self.EXISTING_FRAMEWORK_PATTERNS):
            return 'rejected_already_covered'
        
        if any(word in self.content for word in ['committed', 'will continue', 'monitor', 'support']):
            return 'rejected_with_actions'
        
        return 'rejected'
    
    def check_non_legislative_action(self) -> bool:
        """
        Check if only non-legislative actions were taken
        
        Returns:
            True if only policy actions (no legislation), False otherwise
        """

        # Check for non-legislative focus without proposals
        if 'intends to focus on' in self.content or 'implementation of' in self.content:
            if 'proposal' not in self.content:
                return True
        
        # Specific non-legislative action patterns
        action_patterns = [
            'committed, in particular, to taking the following actions',
            'launch an eu-wide public consultation',
            'improve transparency',
            'establish harmonised'
        ]
        
        if any(phrase in self.content for phrase in action_patterns):
            if 'legislative proposal' not in self.content and 'proposal' not in self.content:
                return True
        
        return False
    
    def check_proposal_pending(self) -> bool:
        """
        Check if existing proposals are pending adoption
        
        Returns:
            True if proposals under negotiation, False otherwise
        """

        has_tabled = 'proposal' in self.content and 'tabled' in self.content
        has_context = 'rather than proposing new legislative acts' in self.content
        not_completed = 'became applicable' not in self.content and 'entered into force' not in self.content
        
        return has_tabled and has_context and not_completed
    
    def extract_technical_status(self) -> str:
        """
        Extract technical status code by checking all patterns in priority order
        
        Status hierarchy (highest to lowest):
        1. applicable
        2. adopted
        3. committed
        4. assessment_pending
        5. roadmap_development
        6. rejected_already_covered / rejected_with_actions / rejected
        7. non_legislative_action
        8. proposal_pending_adoption
        
        Returns:
            Technical status code (e.g., 'applicable', 'committed', etc.)
            
        Raises:
            ValueError: If no status pattern matches
        """

        # Define status checks in priority order (highest to lowest)
        status_checks = [
            ('applicable', self.check_applicable),
            ('adopted', self.check_adopted),
            ('committed', self.check_committed),
            ('assessment_pending', self.check_assessment_pending),
            ('roadmap_development', self.check_roadmap_development),
            (None, self.check_rejection_type),  # Returns status name directly
            ('non_legislative_action', self.check_non_legislative_action),
            ('proposal_pending_adoption', self.check_proposal_pending),
        ]
        
        # Check each status in priority order
        for status_name, check_func in status_checks:
            result = check_func()
            
            # Handle rejection check (returns status name or None)
            if status_name is None and result:
                return result
            
            # Handle boolean checks
            if status_name and result:
                return status_name
        
        # No status matched
        raise ValueError("No known status patterns matched")
    
    def translate_to_citizen_friendly(self, technical_status: str) -> str:
        """
        Translate technical status to citizen-friendly name
        
        Args:
            technical_status: Technical status code (e.g., 'applicable')
            
        Returns:
            Citizen-friendly status name (e.g., 'New Law in Force')
        """
        return self.STATUS_CITIZEN_NAMES.get(technical_status, technical_status)
    

class LegislativeOutcomeExtractor(BaseExtractor):
    """Extractor for legislative outcome and proposal status data"""

    def __init__(self, registration_number: Optional[str] = None):
        """
        Initialize extractor
        
        Args:
            registration_number: ECI registration number for error messages
        """
        self.registration_number = registration_number

    def _extract_legislative_content(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Extract all text content after Answer section
        Returns normalized lowercase string or None if section not found
        """

        # Find Answer section with fallback for combined headers
        answer_section = (
            soup.find('h2', id='Answer-of-the-European-Commission') or
            soup.find('h2', id='Answer-of-the-European-Commission-and-follow-up')
        )
        
        if not answer_section:
            return None
        
        # Collect all text, excluding factsheet downloads
        all_text = []
        for sibling in answer_section.find_next_siblings():
            # Skip factsheet download divs
            if self._is_factsheet_div(sibling):
                continue
            all_text.append(sibling.get_text(strip=False))
        
        # Join text, convert to lowercase, and normalize whitespace
        content = ' '.join(all_text).lower()
        content = re.sub(r'\s+', ' ', content).strip()
        
        return content
    
    def _is_factsheet_div(self, element) -> bool:
        """Check if element is a factsheet download div to exclude"""
        return (
            element.name == 'div' and 
            element.get('class') and 
            'ecl-file' in element.get('class')
        )
    
    def extract_highest_status_reached(self, soup: BeautifulSoup) -> str:
        """
        Extract the highest status reached by the initiative
        
        This method combines two steps:
        1. Extract technical status from HTML content
        2. Translate to citizen-friendly name
        
        Status hierarchy (highest to lowest):
        1. applicable - New Law in Force
        2. adopted - Law Approved
        3. committed - Law Promised
        4. assessment_pending - Being Studied
        5. roadmap_development - Action Plan Being Created
        6. rejected_already_covered - Already Addressed
        7. rejected_with_actions - Alternative Actions Taken
        8. rejected - Rejected
        9. non_legislative_action - Policy Changes Only
        10. proposal_pending_adoption - Existing Proposals Under Review
        
        Args:
            soup: BeautifulSoup object containing ECI response HTML
            
        Returns:
            Citizen-friendly status name (e.g., "New Law in Force")
        
        Raises:
            ValueError: If error occurs during extraction or no status can be determined
        """

        try:
            # Extract content from HTML
            content = self._extract_legislative_content(soup)
            if not content:
                raise ValueError(
                    f"Could not extract legislative content for initiative {self.registration_number}. "
                    f"Answer section may be missing or empty."
                )
            
            # Initialize status matcher with extracted content
            matcher = LegislativeOutcomeClassifier(content)
            
            # Step 1: Extract technical status
            technical_status = matcher.extract_technical_status()
            
            # Step 2: Translate to citizen-friendly format
            citizen_friendly = matcher.translate_to_citizen_friendly(technical_status)
            
            return citizen_friendly
            
        except ValueError as e:
            # Add context to ValueError from LegislativeOutcomeClassifier
            if "No known status patterns matched" in str(e):
                content_preview = content[:500] + "..." if len(content) > 500 else content
                raise ValueError(
                    f"Could not determine legislative status for initiative:\n{self.registration_number}\n"
                    f"No known status patterns matched. Content preview:\n{content_preview}\n"
                ) from e
            raise
        except Exception as e:
            raise ValueError(
                f"Error extracting highest status reached for {self.registration_number}: {str(e)}"
            ) from e

    def extract_proposal_commitment_stated(self, soup: BeautifulSoup) -> Optional[bool]:
        """
        Extract whether Commission explicitly committed to propose legislation
        Returns True if commitment found, False otherwise
        """

        try:
            pass
        except Exception as e:
            raise ValueError(f"Error extracting proposal commitment status for {self.registration_number}: {str(e)}") from e

    def extract_proposal_rejected(self, soup: BeautifulSoup) -> Optional[bool]:
        """
        Extract whether Commission explicitly rejected making a legislative proposal
        Returns True if rejection stated, False otherwise
        """
        try:
            pass
        except Exception as e:
            raise ValueError(f"Error extracting proposal rejection status for {self.registration_number}: {str(e)}") from e


    def extract_rejection_reasoning(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Extract the reasoning provided by Commission for rejecting legislative proposal
        Returns full text explanation or None if not rejected
        """
        try:
            pass
        except Exception as e:
            raise ValueError(f"Error extracting rejection reasoning for {self.registration_number}: {str(e)}") from e


    def extract_applicable_date(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Extract the date when regulation/directive became applicable (implementation deadline)
        Format: YYYY-MM-DD
        """
        try:
            pass
        except Exception as e:
            raise ValueError(f"Error extracting applicable date for {self.registration_number}: {str(e)}") from e


    def extract_proposal_commitment_deadline(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Extract the deadline by which Commission committed to table proposal
        Format: free text like "May 2018", "end of 2023", "March 2026"
        """
        try:
            pass
        except Exception as e:
            raise ValueError(f"Error extracting proposal commitment deadline for {self.registration_number}: {str(e)}") from e


    def extract_legislative_action(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Extract legislative actions as JSON array
        Each item contains: type, action (full text with links), status, deadline
        Returns JSON string or None
        """
        try:
            pass
        except Exception as e:
            raise ValueError(f"Error extracting legislative action for {self.registration_number}: {str(e)}") from e


    def extract_non_legislative_action(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Extract non-legislative actions as JSON array
        Each item contains: type, action (full text with links), status, deadline
        Returns JSON string or None
        """
        try:
            pass
        except Exception as e:
            raise ValueError(f"Error extracting non-legislative action for {self.registration_number}: {str(e)}") from e


    def extract_official_journal_publication_date(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Extract the date when regulation/directive was published in Official Journal
        This is when the law officially comes into existence
        Format: YYYY-MM-DD
        """
        try:
            pass
        except Exception as e:
            raise ValueError(f"Error extracting official journal publication date for {self.registration_number}: {str(e)}") from e


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

    def extract_commission_factsheet_url(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract the URL of the Commission factsheet PDF (English version)
        
        Returns:
            Optional[str]: URL to the factsheet PDF document, or None if no factsheet exists
            
        Raises:
            ValueError: If factsheet element exists but download link is missing or invalid
        """

        try:
            # Find all ecl-file divs (file download components)
            ecl_files = soup.find_all('div', class_=lambda x: x and 'ecl-file' in x)
            
            # Track if we found a factsheet element
            factsheet_found = False
            
            # Look for the one with "Factsheet" in the title
            for file_div in ecl_files:

                # Find the title element
                title_div = file_div.find('div', class_=lambda x: x and 'ecl-file__title' in x)
                
                if title_div:
                    title_text = title_div.get_text(strip=True)
                    
                    # Check if this is a factsheet (case-insensitive)
                    if 'factsheet' in title_text.lower():
                        factsheet_found = True
                        
                        # Find the download link
                        download_link = file_div.find('a', class_=lambda x: x and 'ecl-file__download' in x)
                        
                        if not download_link:
                            raise ValueError(
                                f"Factsheet element found but download link is missing for {self.registration_number}"
                            )
                        
                        href = download_link.get('href', '').strip()
                        
                        if not href:
                            raise ValueError(
                                f"Factsheet download link found but href is empty for {self.registration_number}"
                            )
                        
                        # Successfully found factsheet with valid URL
                        return href
            
            # No factsheet found at all - this is OK, return None
            return None
            
        except ValueError:
            # Re-raise ValueError as-is
            raise
        except Exception as e:
            raise ValueError(
                f"Error extracting factsheet URL for {self.registration_number}: {str(e)}"
            ) from e

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
        self.legislative_outcome = LegislativeOutcomeExtractor(registration_number=self.registration_number)
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
                            self.parliament_activity, self.commission_response, self.legislative_outcome,
                            self.followup_activity, self.multimedia_docs, self.structural_analysis]:
                extractor.set_registration_number(self.registration_number)

            # Read and parse HTML file
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()

            soup = BeautifulSoup(html_content, 'html.parser')

            current_timestamp = datetime.now().isoformat()

            # Extract commission communication date for follow-up calculation
            official_communication_adoption_date = self.commission_response.extract_official_communication_adoption_date(soup)
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
                official_communication_adoption_date=official_communication_adoption_date,
                official_communication_document_urls=self.commission_response.extract_official_communication_document_urls(soup),

                # Commission Response Content
                commission_answer_text=self.commission_response.extract_commission_answer_text(soup),

                # Legislative Outcome Assessment (Priority Columns)
                highest_status_reached=self.legislative_outcome.extract_highest_status_reached(soup),
                proposal_commitment_stated=self.legislative_outcome.extract_proposal_commitment_stated(soup),
                proposal_rejected=self.legislative_outcome.extract_proposal_rejected(soup),
                rejection_reasoning=self.legislative_outcome.extract_rejection_reasoning(soup),
                proposal_commitment_deadline=self.legislative_outcome.extract_proposal_commitment_deadline(soup),
                applicable_date=self.legislative_outcome.extract_applicable_date(soup),
                official_journal_publication_date=self.legislative_outcome.extract_official_journal_publication_date(soup),
                legislative_action=self.legislative_outcome.extract_legislative_action(soup),
                non_legislative_action=self.legislative_outcome.extract_non_legislative_action(soup),

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
                commission_factsheet_url=self.multimedia_docs.extract_commission_factsheet_url(soup),
                dedicated_website=self.multimedia_docs.extract_has_dedicated_website(soup),

                # Structural Analysis Flags
                related_eu_legislation=self.structural_analysis.extract_related_eu_legislation(soup),
                petition_platforms_used=self.structural_analysis.extract_petition_platforms_used(soup),
                follow_up_duration_months=self.structural_analysis.calculate_follow_up_duration_months(
                    official_communication_adoption_date, 
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