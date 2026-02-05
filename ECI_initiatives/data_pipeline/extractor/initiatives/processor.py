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
from .model import ECIInitiativeDetailsRecord
from .parser import ECIHTMLParser
from .initiatives_logger import InitiativesExtractorLogger


class ECIDataProcessor:
    """Main processor for ECI data extraction"""

    def __init__(
        self, data_root: str = "/data", logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the data processor

        Args:
            data_root: Root directory for ECI data
            logger: Optional logger instance. If None, will be initialized in run()
        """
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent.parent  # Move 3 directories up
        self.data_root = project_root / data_root.lstrip("/")
        self.last_session_scraping_dir = None

        # Logger can be passed or initialized later
        self.logger = logger
        self.parser = None

    def find_latest_scrape_session(self) -> Optional[Path]:
        """Find the most recent scraping session directory"""

        try:
            session_dirs = [
                d
                for d in self.data_root.iterdir()
                if d.is_dir()
                and re.match(r"\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}", d.name)
            ]

            if session_dirs:
                last_session = max(session_dirs, key=lambda x: x.name)
                return last_session

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error finding scrape sessions: {e}")
            else:
                print(f"Error finding scrape sessions: {e}")

        return None

    def process_initiative_pages(
        self, session_path: Path
    ) -> List[ECIInitiativeDetailsRecord]:
        """Process all initiative HTML pages in a session"""

        initiatives = []
        initiative_pages_dir = session_path / "initiatives"

        if not initiative_pages_dir.exists():
            self.logger.error(
                f"Initiative pages directory not found: {initiative_pages_dir}"
            )
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

    def save_to_csv(
        self, initiatives: List[ECIInitiativeDetailsRecord], output_path: Path
    ) -> None:
        """Save initiatives data to CSV file"""

        try:
            with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
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
            output_filename = (
                f"eci_initiatives_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv"
            )

        output_path = session_path / output_filename
        self.save_to_csv(initiatives, output_path)

        self.logger.info("Processing completed successfully")
