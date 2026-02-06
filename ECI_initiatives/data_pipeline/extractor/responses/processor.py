"""
ECI Responses Data Processor

Main orchestration class for processing response HTML files
"""

import re
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import logging

from .parser import ECIResponseHTMLParser
from .model import ECICommissionResponseRecord
from .responses_logger import ResponsesExtractorLogger
from .const import (
    SCRIPT_DIR,
    CSV_FILENAME,
    RESPONSE_PAGE_FILENAME_PATTERN,
    FilePatterns,
    DirectoryStructure,
)


class ECIResponseDataProcessor:
    """Main processor for ECI response data extraction"""

    def __init__(
        self,
        data_root: Optional[Path] = None,
        responses_list_csv: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the processor

        Args:
            data_root: Root directory for ECI data (contains date-time session directories).
                      If None, defaults to SCRIPT_DIR / DATA_DIR_NAME
            responses_list_csv: Filename of responses list CSV with metadata.
                               If None, defaults to CSV_FILENAME from const
            logger: Optional logger instance. If None, will be initialized in run()
        """
        # Use constants for default paths
        self.data_root = (
            data_root if data_root else SCRIPT_DIR / DirectoryStructure.DATA_DIR_NAME
        )
        self.responses_list_csv_name = responses_list_csv or CSV_FILENAME

        # Generate output filename with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.output_csv_name = f"eci_responses_{timestamp}.csv"

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

        return None

    def run(self):
        """Main execution method

        Raises:
            FileNotFoundError: If session_path, html_dir, or responses_list_csv do not exist
        """
        # Find latest scraping session
        session_path = self.find_latest_scrape_session()
        self.last_session_scraping_dir = session_path

        if not session_path:
            raise FileNotFoundError(
                f"No scraping session found in: {self.data_root}\n"
                f"Expected directory format: YYYY-MM-DD_HH-MM-SS"
            )

        # Validate session path exists
        if not session_path.exists():
            raise FileNotFoundError(f"Session directory does not exist: {session_path}")

        # Initialize unified logger if not already provided
        if self.logger is None:
            log_dir = self.last_session_scraping_dir / DirectoryStructure.LOG_DIR_NAME
            eci_logger = ResponsesExtractorLogger()
            self.logger = eci_logger.setup(log_dir=log_dir)

        # Initialize parser with shared logger
        self.parser = ECIResponseHTMLParser(self.logger)

        self.logger.info("Starting ECI responses data extraction")
        self.logger.info(f"Processing session: {session_path.name}")

        # Update paths to be relative to session directory (use constants)
        responses_dir_name = DirectoryStructure.RESPONSES_DIR_NAME
        html_dir = session_path / responses_dir_name
        responses_list_csv = html_dir / self.responses_list_csv_name
        output_csv = session_path / self.output_csv_name

        # Validate html_dir exists
        if not html_dir.exists():
            raise FileNotFoundError(
                f"HTML responses directory does not exist: {html_dir}\n"
                f"Expected location: {session_path}/{responses_dir_name}"
            )

        if not html_dir.is_dir():
            raise NotADirectoryError(f"Path is not a directory: {html_dir}")

        # Validate responses_list.csv exists
        if not responses_list_csv.exists():
            raise FileNotFoundError(
                f"Responses list CSV file does not exist: {responses_list_csv}\n"
                f"Expected file: {html_dir}/{self.responses_list_csv_name}"
            )

        # Load responses_list.csv metadata
        responses_metadata = self._load_responses_metadata(responses_list_csv)
        self.logger.info(f"Loaded metadata for {len(responses_metadata)} responses")

        # Find all HTML files (pattern from constant)
        html_files = sorted(html_dir.glob("**/*_en.html"))
        if not html_files:
            raise FileNotFoundError(
                f"No HTML response files found in: {html_dir}\n"
                f"Expected files matching pattern: *_en.html"
            )

        self.logger.info(f"Found {len(html_files)} HTML files to process")

        # Process each file
        results = []
        for html_file in html_files:
            try:
                self.logger.info(f"Processing {html_file.name}")

                # Get metadata for this response
                reg_num = self._extract_reg_num_from_filename(html_file.name)
                metadata = responses_metadata.get(reg_num, {})

                # Parse the file
                response_data = self.parser.parse_file(html_file, metadata)

                if response_data:
                    results.append(response_data)
                    self.logger.info(f"Successfully processed {html_file.name}")

            except Exception as e:
                self.logger.error(
                    f"Error processing {html_file.name}: {e}", exc_info=True
                )

        # Write results to CSV
        self._write_csv(results, output_csv)
        self.logger.info(f"Extraction complete. Processed {len(results)} responses")
        self.logger.info(f"Output written to {output_csv}")

    def _load_responses_metadata(self, responses_list_csv: Path) -> Dict[str, Dict]:
        """
        Load responses_list.csv and create lookup dictionary

        Returns:
            Dictionary mapping registration_number to metadata dict
        """
        metadata = {}

        with open(responses_list_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                reg_num = row.get("registration_number", "")
                if reg_num:
                    metadata[reg_num] = row

        return metadata

    def _extract_reg_num_from_filename(self, filename: str) -> str:
        """Extract registration number from filename (YYYY_NNNNNN_en.html -> YYYY/NNNNNN)"""
        # Use pattern from constant: "{year}_{number}_en.html"

        pattern = FilePatterns.FILENAME_REGEX
        match = re.match(pattern, filename)
        if match:
            year, number = match.groups()
            return f"{year}/{number}"
        return ""

    def _write_csv(self, results: List[ECICommissionResponseRecord], output_csv: Path):
        """Write results to CSV file"""

        if not results:
            raise ValueError("No results to write")

        # Ensure output directory exists
        output_csv.parent.mkdir(parents=True, exist_ok=True)

        # Get fieldnames from first result
        fieldnames = list(results[0].to_dict().keys())

        with open(output_csv, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for result in results:
                writer.writerow(result.to_dict())

        self.logger.info(f"Wrote {len(results)} rows to {output_csv}")
