#!/usr/bin/env python3
"""
ECI Data Scraper - European Citizens' Initiative HTML Parser
Processes scraped HTML files and extracts structured data to CSV
"""

import os
import csv
import re
import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Union, Tuple
from dataclasses import dataclass, asdict
from bs4 import BeautifulSoup


@dataclass
class ECIInitiative:
    """Data structure for ECI initiative information"""

    registration_number: str
    title: str
    objective: str
    annex: Optional[str]
    current_status: str
    url: str

    timeline_registered: Optional[str]
    timeline_collection_start_date: Optional[str]
    timeline_collection_closed: Optional[str] 
    timeline_verification: Optional[str]
    timeline_valid_initiative: Optional[str]

    organizer_representative: Optional[str]  # JSON with representative data
    organizer_entity: Optional[str]         # JSON with legal entity data
    organizer_others: Optional[str]         # JSON with members, substitutes, others, DPO data

    funding_total: Optional[str]
    funding_by: Optional[str]

    signatures_collected: Optional[str]
    signatures_collected_by_country: Optional[str]
    signatures_threshold_met: Optional[str]

    commission_response_date: Optional[str]
    commission_response: Optional[str]

    hearing_date: Optional[str]
    final_outcome: Optional[str]
    languages_available: Optional[str]
    created_timestamp: str
    last_updated: str


class ECIHTMLParser:
    """Parser for ECI initiative HTML pages"""

    def __init__(self):
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """Configure logging for the parser"""

        logger = logging.getLogger('eci_parser')
        logger.setLevel(logging.INFO)

        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    def parse_html_file(self, file_path: Path) -> Optional[ECIInitiative]:
        """Parse a single ECI HTML file and extract initiative data"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            soup = BeautifulSoup(content, 'html.parser')

            reg_number = self._extract_registration_number(file_path.name)
            timeline_data = self._extract_timeline_data(soup)
            title = self._extract_title(soup)
            url = self._construct_url(reg_number)

            # Extract organiser data and split into separate fields
            organiser_data = self.extract_organisers_data(soup)
            organizer_representative, organizer_entity, organizer_others = self._split_organiser_data(
                organiser_data, file_path, title, url
            )

            initiative_data = ECIInitiative(
                registration_number=reg_number,
                title=self._extract_title(soup),
                objective=self._extract_objective(soup),
                annex=self._extract_annex(soup),
                current_status=self._extract_current_status(soup),
                url=self._construct_url(reg_number),

                timeline_registered=timeline_data.get('timeline_registered'),
                timeline_collection_start_date=timeline_data.get('timeline_collection_start_date'),
                timeline_collection_closed=timeline_data.get('timeline_collection_closed'),
                timeline_verification=timeline_data.get('timeline_verification'),
                timeline_valid_initiative=timeline_data.get('timeline_valid_initiative'),

                organizer_representative=organizer_representative,
                organizer_entity=organizer_entity,
                organizer_others=organizer_others,

                signatures_collected=self._extract_signatures_collected(soup),
                signatures_collected_by_country=self._extract_signatures_by_country(soup, file_path, title, url),
                signatures_threshold_met=self._extract_signatures_threshold_met(soup),

                funding_total=self._extract_funding_total(soup),
                funding_by=self._extract_funding_by(soup, file_path, title, url), 

                commission_response_date=self._extract_commission_response_date(soup),
                commission_response=self._extract_commission_response(soup),
                hearing_date=self._extract_hearing_date(soup),
                final_outcome=self._extract_final_outcome(soup),
                languages_available=self._extract_languages_available(soup),
                created_timestamp=datetime.now().isoformat(),
                last_updated=self._extract_last_updated(soup)
            )

            self.logger.info(f"Successfully parsed {file_path.name}")
            return initiative_data

        except Exception as e:
            raise ValueError(f"Error parsing {file_path}:\n{str(e)}") from e
            # self.logger.error(f"Error parsing {file_path}: {str(e)}")
            return None

    def _find_signatures_table(self, soup: BeautifulSoup) -> Optional[BeautifulSoup]:
        """Common inner function to find the signatures table with zebra styling"""
        # Look for table with specific classes
        signatures_table = soup.find('table', class_='ecl-table ecl-table--zebra ecl-u-type-paragraph')

        # Fallback to basic ecl-table if not found
        if not signatures_table:
            signatures_table = soup.find('table', class_='ecl-table')

        return signatures_table

    def _get_signature_table_rows(self, soup: BeautifulSoup, skip_total: bool = True) -> List[Tuple]:
        """
        Extract rows from the signature collection table.
        
        Each row contains: country name, number of signatures, required threshold, and percentage achieved.
        
        Args:
            soup: BeautifulSoup parsed HTML document
            skip_total: If True, exclude the "Total number of signatories" summary row
            
        Returns:
            List of tuples, each containing (country_name, signatures_count, threshold_required, percentage_achieved)
        """
        
        # Find the signatures table in the HTML
        signatures_table = self._find_signatures_table(soup)
        if not signatures_table:
            return []
        
        # Store extracted data from each country row
        country_data = []
        
        # Find all table rows in the signatures table
        table_rows = signatures_table.find_all('tr', class_='ecl-table__row')

        for row in table_rows:

            cells = row.find_all('td', class_='ecl-table__cell')
            
            # Validate that row has exactly 4 columns (country, signatures, threshold, percentage)
            if len(cells) != 4:
                continue
            
            # Extract the country name from the first column
            country_name = cells[0].get_text().strip()
            
            # Skip the total summary row if requested
            if skip_total and 'total number of signatories' in country_name.lower():
                continue
            
            # Skip rows with empty country names
            if not country_name:
                continue
            
            # Extract signature collection data from the remaining columns
            signatures_count = cells[1].get_text().strip()
            threshold_required = cells[2].get_text().strip()
            percentage_achieved = cells[3].get_text().strip()
            
            # Add this country's data to our results
            country_data.append((country_name, signatures_count, threshold_required, percentage_achieved))
        
        return country_data


    def extract_organisers_data(self, soup: BeautifulSoup) -> Optional[Dict]:
        """Extract organiser data from the HTML including representatives, substitutes, members, etc."""

        # Find the Organisers section
        organisers_h2 = soup.find('h2', string=re.compile(r'\s*Organisers\s*$', re.I))
        if not organisers_h2:
            return None

        result = {}

        # Helper function to extract text from next element after a heading
        def get_text_after_heading(heading_text: str) -> List[str]:
            heading = soup.find('h3', string=re.compile(rf'\s*{heading_text}\s*$', re.I))
            if not heading:
                return []

            next_element = heading.find_next_sibling()
            if not next_element or next_element.name != 'ul':
                return []

            items = []
            for li in next_element.find_all('li'):
                text = li.get_text(strip=True)
                if text:
                    items.append(text)
            return items

        # Extract Legal Entity information
        # Look for the exact heading "Legal entity created for the purpose of managing the initiative"
        legal_entity_heading = soup.find('h3', string=re.compile(r'^\s*Legal entity created for the purpose of managing the initiative\s*$', re.I))

        result['legal_entity'] = {
            'name': None,
            'country_of_residence': None
        }

        if legal_entity_heading:
            # Find the next sibling which should be a <ul> element
            next_element = legal_entity_heading.find_next_sibling()
            if next_element and next_element.name == 'ul':
                # Find the <li> element within the <ul>
                li_element = next_element.find('li')
                if li_element:
                    # Get the full text content
                    full_text = li_element.get_text(separator=' ', strip=True)

                    # Split on "Country of the seat:" to separate name and country
                    if 'Country of the seat:' in full_text:
                        parts = full_text.split('Country of the seat:', 1)
                        if len(parts) == 2:
                            result['legal_entity']['name'] = parts[0].strip()
                            result['legal_entity']['country_of_residence'] = parts[1].strip()
                    else:
                        # Fallback: use the entire text as name if no country pattern found
                        result['legal_entity']['name'] = full_text

        # Extract Representative information
        representatives = get_text_after_heading('Representative')
        result['representative'] = {
            'number_of_people': len(representatives),
            'countries_of_residence': {}
        }

        for rep in representatives:
            # Extract country information from the representative text
            # Pattern: "Name - email Country of residence: CountryName"
            country_match = re.search(r'Country of residence[:\s]+([A-Za-z\s]+)', rep)
            if country_match:
                country = country_match.group(1).strip()
                if country in result['representative']['countries_of_residence']:
                    result['representative']['countries_of_residence'][country] += 1
                else:
                    result['representative']['countries_of_residence'][country] = 1

        # Extract Substitute information
        substitutes = get_text_after_heading('Substitute')
        result['substitute'] = {
            'number_of_people': len(substitutes)
        }

        # Extract Members information
        members = get_text_after_heading('Members')
        result['members'] = {
            'number_of_people': len(members)
        }

        # Extract Others information
        others = get_text_after_heading('Others')
        result['others'] = {
            'number_of_people': len(others)
        }

        # Extract DPO information (Data Protection Officer)
        dpo = get_text_after_heading('DPO')
        if not dpo:
            # Also try alternative headings
            dpo = get_text_after_heading('Data Protection Officer')

        result['dpo'] = {
            'number_of_people': len(dpo)
        }

        return result

    def _split_organiser_data(self, organisers_data: Optional[Dict], file_path: Path, title: str, url: str) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """Split organiser data into three separate JSON fields"""

        if not organisers_data:
            return None, None, None

        try:
            # Extract representative data
            organizer_representative = None
            if 'representative' in organisers_data:
                organizer_representative = json.dumps(
                    organisers_data['representative'], 
                    ensure_ascii=False, 
                    separators=(',', ':')
                )

            # Extract legal entity data
            organizer_entity = None
            if 'legal_entity' in organisers_data:
                organizer_entity = json.dumps(
                    organisers_data['legal_entity'], 
                    ensure_ascii=False, 
                    separators=(',', ':')
                )

            # Extract others data (substitute, members, others, dpo)
            organizer_others = None
            others_data = {}
            for key in ['substitute', 'members', 'others', 'dpo']:
                if key in organisers_data:
                    others_data[key] = organisers_data[key]

            if others_data:
                organizer_others = json.dumps(
                    others_data, 
                    ensure_ascii=False, 
                    separators=(',', ':')
                )

            return organizer_representative, organizer_entity, organizer_others

        except Exception as e:
            self.logger.error(
                f"Error splitting organiser data - "
                f"URL: {url}, Initiative: {title}, File: {file_path.name}, "
                f"Error: {str(e)}"
            )
            return None, None, None

    def _extract_registration_number(self, filename: str) -> str:
        """Extract registration number from filename pattern YYYY_NNNNNN_en.html"""

        pattern = r'(\d{4})_(\d{6})_en\.html'
        match = re.match(pattern, filename)
        if match:
            year, number = match.groups()
            return f"{year}/{number}"
        return ""

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract initiative title"""

        # Try meta tag first
        meta_title = soup.find('meta', {'name': 'dcterms.title'})
        if meta_title and meta_title.get('content'):
            return meta_title['content'].strip()

        # Fall back to h1 tag
        h1_title = soup.find('h1', class_='ecl-page-header-core__title')
        if h1_title:
            return h1_title.get_text().strip()

        return ""

    def _extract_objective(self, soup: BeautifulSoup) -> str:
        """Extract initiative objectives (max 1,100 characters)"""

        # Find objectives section
        objectives_section = soup.find('h2', string=re.compile(r'Objectives?', re.I))
        if objectives_section:
            objective_text = ""
            next_element = objectives_section.find_next_sibling()
            while next_element and next_element.name != 'h2':
                if next_element.name == 'p':
                    objective_text += next_element.get_text().strip() + " "
                next_element = next_element.find_next_sibling()

            return objective_text.strip()[:1100]

        return ""

    def _extract_current_status(self, soup: BeautifulSoup) -> str:
        """Extract current initiative current_status"""

        # Find the currently active timeline item
        current_status_element = soup.find(class_='ecl-timeline__item--current')
        
        if current_status_element:
            # Extract the status title from the timeline item
            status_title = current_status_element.find(class_='ecl-timeline__title')
            
            if status_title:
                # Return the raw status text without any mapping
                return status_title.get_text().strip()
        
        # No current status found in timeline
        return ""

    def _construct_url(self, reg_number: str) -> str:
        """Construct English URL from registration number"""

        if reg_number:
            year, number = reg_number.split('/')
            return f"https://citizens-initiative.europa.eu/initiatives/details/{year}/{number}_en"
        return ""

    def _extract_signatures_collected(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Extract the total number of signatures collected for the initiative.
    
        This function attempts to find the total signature count using two methods:
        1. Primary: Searches for the "Total number of signatories" row in the signatures table
        2. Fallback: Looks for a standalone counter element on the page
        
        Note:
            The returned string preserves commas for readability but removes spaces.
            This matches the format displayed on the ECI website.
        """

        # Use common function to get table
        signatures_table = self._find_signatures_table(soup)

        if signatures_table:

            # Find all table rows
            rows = signatures_table.find_all('tr', class_='ecl-table__row')

            for row in rows:

                first_cell = row.find('td', class_='ecl-table__cell')
                if first_cell and 'total number of signatories' in first_cell.get_text().lower():

                    cells = row.find_all('td', class_='ecl-table__cell')

                    if len(cells) >= 2:

                        # Second cell contains the number
                        signatures_text = cells[1].get_text().strip()
                        if signatures_text and re.match(r'^[\d,\s]+$', signatures_text):
                            return signatures_text.replace(' ', '')  # Keep commas for readability

        # Fallback to original counter method
        signatures_element = soup.find(class_='ecl-counter__value')

        if signatures_element:
            signatures_text = signatures_element.get_text().strip()
            numbers = re.findall(r'\d+', signatures_text.replace(',', '').replace(' ', ''))

            if numbers:
                return ''.join(numbers)

        return None

    def _extract_signatures_threshold_met(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Extract number of countries with threshold met (percentage >= 100%)
        Uses common inner function to extract signature table data
        """
        try:
            # Get all rows from signature table
            rows_data = self._get_signature_table_rows(soup, skip_total=True)

            if not rows_data:
                return None

            # Count countries with percentage >= 100%
            countries_met_threshold = 0

            for country, statements, threshold, percentage in rows_data:

                # Extract numeric percentage value
                percentage_match = re.search(r'([\d.]+)%', percentage)

                if percentage_match:

                    percentage_value = float(percentage_match.group(1))

                    if percentage_value >= 100.0:
                        countries_met_threshold += 1

            return str(countries_met_threshold) if countries_met_threshold > 0 else "0"

        except Exception as e:
            self.logger.error(f"Error extracting threshold met countries: {str(e)}")
            return None

    def _extract_commission_response_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract Commission response date"""

        # Implementation depends on HTML structure
        return None

    def _extract_commission_response(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract Commission response date"""

        # Implementation depends on HTML structure
        return None

    def _extract_hearing_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract public hearing date"""

        # Implementation depends on HTML structure
        return None

    def _extract_final_outcome(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract final outcome"""

        # Implementation depends on HTML structure
        return None

    def _extract_languages_available(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract available languages"""

        language_links = soup.find_all(class_='ecl-site-header__language-link')
        if language_links:
            languages = []
            for link in language_links:
                href = link.get('href', '')
                if '_' in href:
                    lang_code = href.split('_')[-1]
                    if len(lang_code) == 2:
                        languages.append(lang_code)
            return ','.join(sorted(set(languages))) if languages else None
        return None

    def _extract_last_updated(self, soup: BeautifulSoup) -> str:
        """Extract last updated timestamp"""

        meta_modified = soup.find('meta', {'name': 'dcterms.modified'})
        if meta_modified and meta_modified.get('content'):
            return meta_modified['content']
        return datetime.now().isoformat()

    def _extract_timeline_data(self, soup: BeautifulSoup) -> Dict[str, Optional[str]]:
        """Extract timeline information from ECL timeline"""

        timeline_data = {}

        # Find the timeline container
        timeline = soup.find('ol', class_='ecl-timeline')
        if not timeline:
            return timeline_data

        # Extract all timeline items
        timeline_items = timeline.find_all('li', class_='ecl-timeline__item')

        for item in timeline_items:
            # Extract title
            title_element = item.find('div', class_='ecl-timeline__title')
            if not title_element:
                continue

            title = title_element.get_text().strip()

            # Extract content (date) if available
            content_element = item.find('div', class_='ecl-timeline__content')
            content = content_element.get_text().strip() if content_element else None

            # Normalize title to match our field names
            normalized_title = self._normalize_timeline_title(title)

            if normalized_title:
                timeline_data[normalized_title] = content

        return timeline_data

    def _normalize_timeline_title(self, title: str) -> Optional[str]:
        """Normalize timeline titles to standard field names"""

        title_mapping = {
            'Registered': 'timeline_registered',
            'Collection start date': 'timeline_collection_start_date',
            'Collection closed': 'timeline_collection_closed',
            'Verification': 'timeline_verification',
            'Valid initiative': 'timeline_valid_initiative',
            # Add more mappings as needed
            'Collection ongoing': 'timeline_collection_start_date',  # Map ongoing to start date
            'Registration': 'timeline_registered',
        }

        return title_mapping.get(title)

    def _extract_signatures_by_country(self, soup: BeautifulSoup, file_path: Path, title: str, url: str) -> Optional[str]:
        """Extract country-level signature data as JSON using common function"""

        try:
            # Use common function to get table rows
            rows_data = self._get_signature_table_rows(soup, skip_total=True)

            if not rows_data:
                return None

            country_data = {}

            for country_text, statements_of_support, threshold, percentage in rows_data:
                # Check for missing data and log warnings
                missing_fields = []
                if not statements_of_support:
                    missing_fields.append("statements_of_support")
                if not threshold:
                    missing_fields.append("threshold")
                if not percentage:
                    missing_fields.append("percentage")

                if missing_fields:
                    self.logger.warning(
                        f"Missing signature data - Country: {country_text}, "
                        f"URL: {url}, Initiative: {title}, File: {file_path.name}, "
                        f"Missing fields: {', '.join(missing_fields)}"
                    )

                # Add country data (even if some fields are missing)
                country_data[country_text] = {
                    "statements_of_support": statements_of_support,
                    "threshold": threshold,
                    "percentage": percentage
                }

            # Return JSON string if we have data
            if country_data:
                return json.dumps(country_data, ensure_ascii=False, separators=(',', ':'))

        except Exception as e:
            self.logger.error(
                f"Error serializing country data to JSON - "
                f"URL: {url}, Initiative: {title}, File: {file_path.name}, "
                f"Error: {str(e)}"
            )

        return None

    def _extract_funding_total(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract total funding amount from paragraph"""

        # Look for paragraph containing total funding text
        funding_paragraph = soup.find('p', string=re.compile(r'Total amount of support and funding:', re.I))
        if not funding_paragraph:
            # Try alternative search in paragraph content
            paragraphs = soup.find_all('p', class_='ecl-u-type-paragraph')
            for p in paragraphs:
                if 'total amount of support and funding' in p.get_text().lower():
                    funding_paragraph = p
                    break

        if funding_paragraph:
            text = funding_paragraph.get_text()
            # Extract amount using regex - matches €followed by numbers, commas, dots
            amount_match = re.search(r'€([\d,]+\.?\d*)', text)
            if amount_match:
                return amount_match.group(1)  # Return just the number part without €

        return None

    def _extract_funding_by(self, soup: BeautifulSoup, file_path: Path, title: str, url: str) -> Optional[str]:
        """Extract funding sponsors data as JSON"""

        # Find funding table - look for table with sponsor headers
        funding_tables = soup.find_all('table', class_='ecl-table')
        funding_table = None

        for table in funding_tables:
            headers = table.find_all('th', class_='ecl-table__header')
            header_texts = [h.get_text().strip().lower() for h in headers]

            # Check if this is the funding table by looking for expected headers
            if ('name of sponsor' in ' '.join(header_texts) and 
                'amount in eur' in ' '.join(header_texts)):
                funding_table = table
                break

        if not funding_table:
            return None

        sponsors_data = []

        # Extract table rows (skip header)
        rows = funding_table.find_all('tr', class_='ecl-table__row')

        for row in rows:
            cells = row.find_all('td', class_='ecl-table__cell')

            if len(cells) != 3:  # Should have 3 cells: Name, Date, Amount
                continue

            sponsor_name = cells[0].get_text().strip()
            date = cells[1].get_text().strip()
            amount = cells[2].get_text().strip()

            # Check for missing data and log warnings
            missing_fields = []
            if not sponsor_name:
                missing_fields.append("name_of_sponsor")
            if not date:
                missing_fields.append("date")
            if not amount:
                missing_fields.append("amount_in_eur")

            if missing_fields:
                self.logger.warning(
                    f"Missing funding data - Sponsor: {sponsor_name or 'UNKNOWN'}, "
                    f"URL: {url}, Initiative: {title}, File: {file_path.name}, "
                    f"Missing fields: {', '.join(missing_fields)}"
                )

            # Clean sponsor name (remove superscript references)
            clean_sponsor_name = re.sub(r'<sup>.*?</sup>', '', sponsor_name)
            clean_sponsor_name = re.sub(r'\s*\[\d+\]\s*', '', clean_sponsor_name).strip()

            # Add sponsor data (even if some fields are missing)
            sponsor_entry = {
                "name_of_sponsor": clean_sponsor_name,
                "date": date,
                "amount_in_eur": amount
            }

            sponsors_data.append(sponsor_entry)

        # Return JSON string if we have data
        if sponsors_data:
            try:
                return json.dumps(sponsors_data, ensure_ascii=False, separators=(',', ':'))
            except Exception as e:
                self.logger.error(
                    f"Error serializing funding data to JSON - "
                    f"URL: {url}, Initiative: {title}, File: {file_path.name}, "
                    f"Error: {str(e)}"
                )
                return None

        return None

    def _extract_annex(self, soup: BeautifulSoup) -> Optional[str]:
        """Return full Annex text (concatenated paragraphs) or None."""

        # Find the Annex h2 header (case insensitive)
        annex_h2 = soup.find('h2', string=re.compile(r'^\s*Annex\s*$', re.I))

        if not annex_h2:
            return None

        texts: List[str] = []
        node = annex_h2.find_next_sibling()

        while node and not (node.name == 'h2'):
            # grab paragraph–level text, skip empty / whitespace nodes
            if node.name in {'p', 'ul', 'ol'}:
                txt = node.get_text(' ', strip=True)

                if txt:
                    texts.append(txt)

            node = node.find_next_sibling()

        joined = ' '.join(texts).strip()
        return joined or None

class ECIDataProcessor:
    """Main processor for ECI data extraction"""

    def __init__(self, data_root: str = "/ECI_initiatives/data"):

        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent  # Move 3 directories up
        self.data_root = project_root / data_root.lstrip('/')
        self.last_session_scraping_dir = None

        self.parser = ECIHTMLParser()
        self.logger = None

    def _setup_logger(self) -> logging.Logger:
        """Configure logging"""

        logger = logging.getLogger('eci_processor')
        logger.setLevel(logging.INFO)

        # Create logs directory if it doesn't exist
        log_dir = self.last_session_scraping_dir / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        # File handler
        log_file = log_dir / f"processor_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        return logger

    def find_latest_scrape_session(self) -> Optional[Path]:
        """Find the most recent scraping session directory"""

        try:
            session_dirs = [d for d in self.data_root.iterdir() 
                           if d.is_dir() and re.match(r'\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}', d.name)]

            if session_dirs:

                last_session = max(session_dirs, key=lambda x: x.name)
                self.last_session_scraping_dir = last_session

                return last_session

        except Exception as e:
            self.logger.error(f"Error finding scrape sessions: {e}")

        return None

    def process_initiative_pages(self, session_path: Path) -> List[ECIInitiative]:
        """Process all initiative HTML pages in a session"""

        initiatives = []
        initiative_pages_dir = session_path / "initiative_pages"

        if not initiative_pages_dir.exists():
            self.logger.error(f"Initiative pages directory not found: {initiative_pages_dir}")
            return initiatives

        # Process each year directory
        for year_dir in sorted(initiative_pages_dir.iterdir()):

            if not year_dir.is_dir():
                continue

            self.logger.info(f"Processing year: {year_dir.name}")

            # Process each HTML file in the year directory
            for html_file in sorted(year_dir.glob("*.html")):
                initiative = self.parser.parse_html_file(html_file)
                if initiative:
                    initiatives.append(initiative)

        self.logger.info(f"Successfully processed {len(initiatives)} initiatives")
        return initiatives

    def save_to_csv(self, initiatives: List[ECIInitiative], output_path: Path) -> None:
        """Save initiatives data to CSV file"""

        try:
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                if not initiatives:
                    self.logger.warning("No initiatives to save")
                    return

                fieldnames = list(asdict(initiatives[0]).keys())
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()
                for initiative in initiatives:
                    writer.writerow(asdict(initiative))

            self.logger.info(f"Saved {len(initiatives)} initiatives to {output_path}")

        except Exception as e:
            self.logger.error(f"Error saving CSV: {e}")

    def run(self, output_filename: str = None) -> None:
        """Main processing pipeline"""

        # Find latest scraping session
        session_path = self.find_latest_scrape_session()

        if not session_path:
            print("No scraping session found in:\n"+ str(self.last_session_scraping_dir))
            return

        self.logger = self._setup_logger()
        self.logger.info("Starting ECI data processing")
        self.logger.info(f"Processing session: {session_path.name}")

        # Process all initiative pages
        initiatives = self.process_initiative_pages(session_path)

        # Save to CSV
        if not output_filename:
            output_filename = f"eci_initiatives_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv"

        output_path = session_path / output_filename
        self.save_to_csv(initiatives, output_path)

        self.logger.info("Processing completed successfully")


def main():
    """Main entry point"""

    processor = ECIDataProcessor()
    processor.run()


if __name__ == "__main__":
    main()
