"""
ECI Responses Data Processor
Main orchestration class for processing response HTML files
"""

import re
import csv
from pathlib import Path
from typing import Dict, List, Optional
import logging

from .parser import ECIResponseHTMLParser
from .model import ECIResponse
from .responses_logger import ResponsesExtractorLogger


class ECIResponseDataProcessor:
    """Main processor for ECI response data extraction"""
    
    def __init__(
        self,
        data_root: str = "ECI_initiatives/data",
        responses_list_csv: str = "responses_list.csv",
        output_csv: str = "eci_responses_date.csv",
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the processor
        
        Args:
            data_root: Root directory for ECI data (contains date-time session directories)
            responses_list_csv: Path to responses_list.csv with metadata (relative to session dir)
            output_csv: Path to output CSV file (relative to session dir)
            logger: Optional logger instance. If None, will be initialized in run()
        """
        # Determine project root (4 directories up from current file)
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent.parent

        self.data_root = project_root / data_root.lstrip('/')
        
        print("root", project_root)
        self.responses_list_csv_name = responses_list_csv
        self.output_csv_name = output_csv
        self.last_session_scraping_dir = None
        
        # Logger can be passed or initialized later
        self.logger = logger
        self.parser = None

    def find_latest_scrape_session(self) -> Optional[Path]:
        """Find the most recent scraping session directory"""
        try:
            session_dirs = [
                d for d in self.data_root.iterdir() 
                if d.is_dir() and re.match(r'\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}', d.name)
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
    
    def run(self):
        """Main execution method"""
        # Find latest scraping session
        session_path = self.find_latest_scrape_session()
        self.last_session_scraping_dir = session_path
        
        if not session_path:
            print(f"No scraping session found in:\n{self.data_root}")
            return
        
        # Initialize unified logger if not already provided
        if self.logger is None:
            log_dir = self.last_session_scraping_dir / "logs"
            eci_logger = ResponsesExtractorLogger()
            self.logger = eci_logger.setup(log_dir=log_dir)
        
        # Initialize parser with shared logger
        self.parser = ECIResponseHTMLParser(self.logger)
        
        self.logger.info("Starting ECI responses data extraction")
        self.logger.info(f"Processing session: {session_path.name}")
        
        # Update paths to be relative to session directory
        html_dir = session_path / "responses"
        responses_list_csv = html_dir / self.responses_list_csv_name
        output_csv = session_path / self.output_csv_name
        
        # Load responses_list.csv metadata
        responses_metadata = self._load_responses_metadata(responses_list_csv)
        self.logger.info(f"Loaded metadata for {len(responses_metadata)} responses")
        
        # Find all HTML files
        html_files = sorted(html_dir.glob("*_en.html")) if html_dir.exists() else []
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
                self.logger.error(f"Error processing {html_file.name}: {e}", exc_info=True)
        
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
        
        if not responses_list_csv.exists():
            self.logger.warning(f"responses_list.csv not found at {responses_list_csv}")
            return metadata
        
        with open(responses_list_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                reg_num = row.get('registration_number', '')
                if reg_num:
                    metadata[reg_num] = row
        
        return metadata
    
    def _extract_reg_num_from_filename(self, filename: str) -> str:
        """Extract registration number from filename (YYYY_NNNNNN_en.html -> YYYY/NNNNNN)"""
        pattern = r'(\d{4})_(\d{6})_en\.html'
        match = re.match(pattern, filename)
        if match:
            year, number = match.groups()
            return f"{year}/{number}"
        return ""
    
    def _write_csv(self, results: List[ECIResponse], output_csv: Path):
        """Write results to CSV file"""
        
        if not results:
            self.logger.warning("No results to write")
            return
        
        # Ensure output directory exists
        output_csv.parent.mkdir(parents=True, exist_ok=True)
        
        # Get fieldnames from first result
        fieldnames = list(results[0].to_dict().keys())
        
        with open(output_csv, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for result in results:
                writer.writerow(result.to_dict())
        
        self.logger.info(f"Wrote {len(results)} rows to {output_csv}")
