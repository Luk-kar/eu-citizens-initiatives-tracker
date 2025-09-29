#!/usr/bin/env python3
"""
ECI Data Scraper - European Citizens' Initiative HTML Parser
Processes scraped HTML files and extracts structured data to CSV
"""

import os
import csv
import re
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Union
from dataclasses import dataclass, asdict
from bs4 import BeautifulSoup


@dataclass
class ECIInitiative:
    """Data structure for ECI initiative information"""

    registration_number: str
    title: str
    title_en: str
    objective: str
    objective_en: str
    status: str
    registration_date: Optional[str]
    collection_start_date: Optional[str]
    collection_end_date: Optional[str]
    url_en: str
    organizer_representative: Optional[str]
    organizer_country: Optional[str]
    legal_entity: Optional[str]
    funding_sources: Optional[str]
    signatures_collected: Optional[str]
    countries_threshold_met: Optional[str]
    commission_response_date: Optional[str]
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
            
            # Extract registration number from filename
            reg_number = self._extract_registration_number(file_path.name)
            
            initiative_data = ECIInitiative(
                registration_number=reg_number,
                title=self._extract_title(soup),
                title_en=self._extract_title_en(soup),
                objective=self._extract_objective(soup),
                objective_en=self._extract_objective_en(soup),
                status=self._extract_status(soup),
                registration_date=self._extract_registration_date(soup),
                collection_start_date=self._extract_collection_start_date(soup),
                collection_end_date=self._extract_collection_end_date(soup),
                url_en=self._construct_url_en(reg_number),
                organizer_representative=self._extract_organizer_representative(soup),
                organizer_country=self._extract_organizer_country(soup),
                legal_entity=self._extract_legal_entity(soup),
                funding_sources=self._extract_funding_sources(soup),
                signatures_collected=self._extract_signatures_collected(soup),
                countries_threshold_met=self._extract_countries_threshold_met(soup),
                commission_response_date=self._extract_commission_response_date(soup),
                hearing_date=self._extract_hearing_date(soup),
                final_outcome=self._extract_final_outcome(soup),
                languages_available=self._extract_languages_available(soup),
                created_timestamp=datetime.now().isoformat(),
                last_updated=self._extract_last_updated(soup)
            )
            
            self.logger.info(f"Successfully parsed {file_path.name}")
            return initiative_data
            
        except Exception as e:
            self.logger.error(f"Error parsing {file_path}: {str(e)}")
            return None
    
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
    
    def _extract_title_en(self, soup: BeautifulSoup) -> str:
        """Extract English title (same as title for _en pages)"""
        return self._extract_title(soup)
    
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
    
    def _extract_objective_en(self, soup: BeautifulSoup) -> str:
        """Extract English objective (same as objective for _en pages)"""
        return self._extract_objective(soup)
    
    def _extract_status(self, soup: BeautifulSoup) -> str:
        """Extract current initiative status"""
        # Look for timeline current item
        current_status = soup.find(class_='ecl-timeline__item--current')
        if current_status:
            status_title = current_status.find(class_='ecl-timeline__title')
            if status_title:
                status_text = status_title.get_text().strip()
                # Map to standardized status values
                status_mapping = {
                    'Registered': 'Open',
                    'Registration': 'Registered',
                    'Collection': 'Open',
                    'Withdrawn': 'Withdrawn',
                    'Successful': 'Successful',
                    'Closed': 'Closed'
                }
                return status_mapping.get(status_text, status_text)
        
        return ""
    
    def _extract_registration_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract registration date from timeline"""
        first_timeline_item = soup.find(class_='ecl-timeline__item')
        if first_timeline_item:
            date_element = first_timeline_item.find(class_='ecl-timeline__content')
            if date_element:
                return self._parse_date(date_element.get_text())
        return None
    
    def _extract_collection_start_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract collection start date"""
        collection_item = soup.find('li', {'id': '1'})  # Usually second timeline item
        if collection_item:
            date_element = collection_item.find(class_='ecl-timeline__content')
            if date_element:
                return self._parse_date(date_element.get_text())
        return None
    
    def _extract_collection_end_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract or calculate collection end date"""
        # Implementation depends on HTML structure
        # Usually calculated as start_date + 12 months
        return None
    
    def _construct_url_en(self, reg_number: str) -> str:
        """Construct English URL from registration number"""
        if reg_number:
            year, number = reg_number.split('/')
            return f"https://citizens-initiative.europa.eu/initiatives/details/{year}/{number}_en"
        return ""
    
    def _extract_organizer_representative(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract organizer representative name"""
        # Implementation depends on HTML structure
        return None
    
    def _extract_organizer_country(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract organizer country"""
        # Implementation depends on HTML structure
        return None
    
    def _extract_legal_entity(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract legal entity information"""
        # Implementation depends on HTML structure
        return None
    
    def _extract_funding_sources(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract funding sources"""
        # Implementation depends on HTML structure
        return None
    
    def _extract_signatures_collected(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract number of signatures collected"""
        signatures_element = soup.find(class_='ecl-counter__value')
        if signatures_element:
            signatures_text = signatures_element.get_text().strip()
            # Extract numeric value
            numbers = re.findall(r'\d+', signatures_text.replace(',', '').replace(' ', ''))
            if numbers:
                return numbers[0]
        return None
    
    def _extract_countries_threshold_met(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract number of countries with threshold met"""
        # Implementation depends on HTML structure
        return None
    
    def _extract_commission_response_date(self, soup: BeautifulSoup) -> Optional[str]:
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
    
    def _parse_date(self, date_text: str) -> Optional[str]:
        """Parse date from various formats to ISO format"""
        # Implementation for date parsing
        # Handle various European date formats
        return None


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
            print("No scraping session found in:\n"+ self.last_session_scraping_dir)
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
