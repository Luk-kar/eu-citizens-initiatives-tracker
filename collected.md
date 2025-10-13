`./ECI_initiatives/extractor/initiatives/initiatives_logger.py`:
```
"""
Unified Logger for ECI initiatives extractor
"""

# python
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional


class InitiativesExtractorLogger:
    """Centralized logger for ECI initiatives data processing"""

    _instance = None
    _logger = None

    def __new__(cls):
        """Singleton pattern to ensure only one logger instance exists"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)

        return cls._instance

    def __init__(self):
        """Initialize logger only once"""
        if self._logger is None:

            self._logger = logging.getLogger('eci_initiatives_extractor')
            self._logger.setLevel(logging.INFO)

            # Prevent duplicate handlers if __init__ is called multiple times
            self._logger.handlers = []

    def setup(self, log_dir: Optional[Path] = None) -> logging.Logger:
        """
        Configure logging with file and console handlers

        Args:
            log_dir: Directory for log files. If None, only console logging is used.

        Returns:
            Configured logger instance
        """
        # Clear existing handlers to prevent duplicates
        self._logger.handlers = []

        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # Console handler (always active)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self._logger.addHandler(console_handler)

        # File handler (optional, only if log_dir is provided)
        if log_dir:

            log_dir.mkdir(parents=True, exist_ok=True)

            log_file = log_dir / f"processor_initiatives_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"

            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(formatter)

            self._logger.addHandler(file_handler)

        return self._logger

    def get_logger(self) -> logging.Logger:
        """Get the configured logger instance"""

        if self._logger is None:
            raise RuntimeError("Logger not initialized. Call setup() first.")

        return self._logger

```

`./ECI_initiatives/extractor/initiatives/__init__.py`:
```

```

`./ECI_initiatives/extractor/initiatives/__main__.py`:
```
#!/usr/bin/env python3
"""
ECI Data Scraper - European Citizens' Initiative HTML Parser
Processes scraped HTML files and extracts structured data to CSV
"""

# python
import os
import csv
import re
import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Union, Tuple
from dataclasses import dataclass, asdict

# third-party
from bs4 import BeautifulSoup

# initiatives extractor
from .initiatives_logger import InitiativesExtractorLogger
from .processor import ECIDataProcessor


def main():
    """Main entry point"""

    processor = ECIDataProcessor()
    processor.run()


if __name__ == "__main__":
    main()

```

`./ECI_initiatives/extractor/initiatives/model.py`:
```
#!/usr/bin/env python3
"""
ECI Data Models
Data structures for ECI initiative information
"""

from dataclasses import dataclass
from typing import Optional


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
    timeline_verification_start: Optional[str]
    timeline_verification_end: Optional[str]
    timeline_response_commission_date:  Optional[str]

    timeline: Optional[str]

    organizer_representative: Optional[str]  # JSON with representative data
    organizer_entity: Optional[str]         # JSON with legal entity data
    organizer_others: Optional[str]         # JSON with members, substitutes, others, DPO data

    funding_total: Optional[str]
    funding_by: Optional[str]

    signatures_collected: Optional[str]
    signatures_collected_by_country: Optional[str]
    signatures_threshold_met: Optional[str]

    response_commission_url: Optional[str]

    final_outcome: Optional[str]
    languages_available: Optional[str]
    created_timestamp: str
    last_updated: str

```

`./ECI_initiatives/extractor/initiatives/parser.py`:
```
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

```

`./ECI_initiatives/extractor/initiatives/processor.py`:
```
"""
ECI Data Processor
Main processor for ECI data extraction and CSV generation
"""

# Standard library
import re
import csv
from pathlib import Path
from datetime import datetime
from typing import List, Optional
from dataclasses import asdict
import logging

# Local
from .model import ECIInitiative
from .parser import ECIHTMLParser
from .initiatives_logger import InitiativesExtractorLogger


class ECIDataProcessor:
    """Main processor for ECI data extraction"""

    def __init__(self, data_root: str = "/initiatives/data", logger: Optional[logging.Logger] = None):
        """
        Initialize the data processor
        
        Args:
            data_root: Root directory for ECI data
            logger: Optional logger instance. If None, will be initialized in run()
        """
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent.parent  # Move 4 directories up
        self.data_root = project_root / data_root.lstrip('/')
        self.last_session_scraping_dir = None

        # Logger can be passed or initialized later
        self.logger = logger
        self.parser = None

    def find_latest_scrape_session(self) -> Optional[Path]:
        """Find the most recent scraping session directory"""

        try:
            session_dirs = [d for d in self.data_root.iterdir() 
                           if d.is_dir() and re.match(r'\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}', d.name)]

            if session_dirs:
                last_session = max(session_dirs, key=lambda x: x.name)
                return last_session

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error finding scrape sessions: {e}")
            else:
                print(f"Error finding scrape sessions: {e}")

        return None

    def process_initiative_pages(self, session_path: Path) -> List[ECIInitiative]:
        """Process all initiative HTML pages in a session"""

        initiatives = []
        initiative_pages_dir = session_path / "initiatives"

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
        self.last_session_scraping_dir = session_path
        
        if not session_path:
            print("No scraping session found in:\n" + str(self.data_root))
            return
        
        # Initialize unified logger if not already provided
        if self.logger is None:

            log_dir = self.last_session_scraping_dir / "logs"
            eci_logger = InitiativesExtractorLogger()
            self.logger = eci_logger.setup(log_dir=log_dir)
        
        # Initialize parser with shared logger
        self.parser = ECIHTMLParser(logger=self.logger)
        
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
```

