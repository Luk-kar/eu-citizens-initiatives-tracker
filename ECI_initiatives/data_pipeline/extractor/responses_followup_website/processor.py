# Python
import os
import glob
import csv
import logging
from pathlib import Path
from datetime import datetime
from typing import List
import re


# Local
from .model import ECIFollowupWebsiteRecord
from .parser.extractors import FollowupWebsiteExtractor

# TODO
# conflicts with ath calculations in:
# extractor/responses_followup_website/end_to_end/test_created_files
from .consts import (
    SCRIPT_DIR,
    DATA_DIR_NAME,
    LOG_DIR_NAME,
    RESPONSES_FOLLOWUP_WEBSITE_DIR_NAME,
    TIMESTAMP_FORMAT,
    TIMESTAMP_DIR_PATTERN,
    INPUT_CSV_PATTERN,
    INPUT_CSV_EXCLUDE_KEYWORD,
    OUTPUT_CSV_PREFIX,
    LOG_FILE_PREFIX,
    LOG_FORMAT_DETAILED,
    FILE_ENCODING,
    HTML_FILE_GLOB_PATTERN,
    CSV_FIELD_REGISTRATION_NUMBER,
    CSV_FIELD_INITIATIVE_TITLE,
    CSV_FIELD_FOLLOWUP_DEDICATED_WEBSITE,
)


class ECIFollowupWebsiteProcessor:

    def __init__(self):
        # Find latest timestamped directory under data
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent.parent
        data_root = "ECI_initiatives/data"
        data_base = project_root / data_root
        # data_base = SCRIPT_DIR / DATA_DIR_NAME

        # Use regex pattern to find timestamped directories
        all_dirs = [
            d
            for d in data_base.iterdir()
            if d.is_dir() and re.match(TIMESTAMP_DIR_PATTERN, d.name)
        ]

        if not all_dirs:
            raise FileNotFoundError(
                f"No timestamped data directories found in {data_base}. "
                f"Expected format: YYYY-MM-DD_HH-MM-SS"
            )

        self.input_dir = max(all_dirs, key=lambda x: x.name)  # use latest
        self.output_dir = self.input_dir
        self.extractor_run_datetime = datetime.now().strftime(TIMESTAMP_FORMAT)

        # Setup logging first
        self._setup_logging()

        # Load response data early - will raise FileNotFoundError if CSV missing
        self.response_data = self._load_response_data()

        # Find HTML files early - will raise FileNotFoundError if none found
        self.html_files = self._find_html_files()

        self.output_csv = (
            self.output_dir / f"{OUTPUT_CSV_PREFIX}_{self.extractor_run_datetime}.csv"
        )

        self.logger.info(f"Initialized ECIFollowupWebsiteProcessor")
        self.logger.info(f"Input directory: {self.input_dir}")
        self.logger.info(f"Output CSV: {self.output_csv}")

    def _setup_logging(self):
        """Configure logging with file and console handlers."""
        logs_dir = self.output_dir / LOG_DIR_NAME
        logs_dir.mkdir(parents=True, exist_ok=True)

        log_file = logs_dir / f"{LOG_FILE_PREFIX}_{self.extractor_run_datetime}.log"

        logging.basicConfig(
            level=logging.INFO,
            format=LOG_FORMAT_DETAILED,
            handlers=[
                logging.FileHandler(log_file, encoding=FILE_ENCODING),
                logging.StreamHandler(),
            ],
        )

        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Log file: {log_file}")

    def _load_response_data(self) -> "ECIResponseDataLoader":
        """Load responses list CSV to get initiative metadata."""
        responses_csv_files = [
            csv_file
            for csv_file in self.input_dir.glob(INPUT_CSV_PATTERN)
            if INPUT_CSV_EXCLUDE_KEYWORD not in csv_file.name
        ]

        if not responses_csv_files:
            raise FileNotFoundError(
                f"No responses CSV file found in {self.input_dir}. "
                f"Expected file matching pattern: {INPUT_CSV_PATTERN} "
                f"(excluding files with '{INPUT_CSV_EXCLUDE_KEYWORD}' in name)"
            )

        responses_csv_path = max(responses_csv_files, key=lambda x: x.name)
        self.logger.info(f"Loading responses data from: {responses_csv_path}")

        response_data = ECIResponseDataLoader(responses_csv_path)
        self.logger.info(
            f"Loaded {len(response_data.records)} records from responses CSV"
        )

        return response_data

    def _find_html_files(self) -> List[Path]:
        """Find all HTML files in the responses_followup_website directory."""
        html_dir = self.input_dir / RESPONSES_FOLLOWUP_WEBSITE_DIR_NAME
        html_files = list(html_dir.glob(HTML_FILE_GLOB_PATTERN))

        self.logger.info(f"In the directory:\n{html_dir}")
        self.logger.info(f"Found {len(html_files)} HTML files to process")

        if not html_files:
            raise FileNotFoundError(
                f"No HTML files found in {html_dir}. "
                f"Expected HTML files matching pattern: {HTML_FILE_GLOB_PATTERN}"
            )

        return html_files

    def run(self):
        """Process all HTML files and generate output CSV."""
        records = []

        for idx, path in enumerate(self.html_files, 1):
            self.logger.info(
                f"Processing file {idx}/{len(self.html_files)}: {path.name}"
            )

            try:
                record = self._process_html_file(path, self.response_data)
                records.append(record)
                self.logger.info(
                    f"Successfully processed: {record.registration_number}"
                )
            except Exception as e:
                self.logger.error(f"Error processing {path}: {e}", exc_info=True)
                continue

        self._write_output_csv(records)
        self.logger.info(f"Processing complete. Output written to {self.output_csv}")

    def _process_html_file(
        self, path: Path, response_data: "ECIResponseDataLoader"
    ) -> ECIFollowupWebsiteRecord:
        """Process a single HTML file and return extracted record."""
        with open(path, encoding=FILE_ENCODING) as f:
            html_content = f.read()

        html_file_name = path.name

        # Create extractor with logger
        extractor = FollowupWebsiteExtractor(html_content, logger=self.logger)

        # Extract and set registration number
        registration_number = extractor.extract_registration_number(html_file_name)

        # Validate registration number exists in responses CSV
        if registration_number not in response_data.records:
            raise ValueError(
                f"Registration number {registration_number} not found in responses CSV. "
                f"Cannot process file: {html_file_name}"
            )

        # Get metadata from responses CSV
        initiative_title = response_data.get_title(registration_number)
        followup_dedicated_website = response_data.get_website_url(registration_number)

        # Create and return record with all extracted data
        return ECIFollowupWebsiteRecord(
            # Basic Initiative Metadata
            registration_number=registration_number,
            initiative_title=initiative_title,
            followup_dedicated_website=followup_dedicated_website,
            # Commission Response Content
            commission_answer_text=extractor.extract_commission_answer_text(),
            official_communication_document_urls=extractor.extract_official_communication_document_urls(),
            # SECTION 1: Final Outcome
            final_outcome_status=extractor.extract_final_outcome_status(),
            law_implementation_date=extractor.extract_law_implementation_date(),
            # SECTION 2: Commission's Initial Response
            commission_promised_new_law=extractor.extract_commission_promised_new_law(),
            commission_deadlines=extractor.extract_commissions_deadlines(),
            commission_rejected_initiative=extractor.extract_commission_rejected_initiative(),
            commission_rejection_reason=extractor.extract_commission_rejection_reason(),
            # SECTION 3: Actions Taken
            laws_actions=extractor.extract_laws_actions(),
            policies_actions=extractor.extract_policies_actions(),
            # Follow-up Activities Section
            has_roadmap=extractor.extract_has_roadmap(),
            has_workshop=extractor.extract_has_workshop(),
            has_partnership_programs=extractor.extract_has_partnership_programs(),
            court_cases_referenced=extractor.extract_court_cases_referenced(),
            followup_latest_date=extractor.extract_followup_latest_date(),
            followup_most_future_date=extractor.extract_followup_most_future_date(),
            # Structural Analysis Flags
            referenced_legislation_by_id=extractor.extract_referenced_legislation_by_id(),
            referenced_legislation_by_name=extractor.extract_referenced_legislation_by_name(),
            followup_events_with_dates=extractor.extract_followup_events_with_dates(),
        )

    def _write_output_csv(self, records: List[ECIFollowupWebsiteRecord]):
        """Write extracted records to output CSV file."""
        self.logger.info(f"Writing {len(records)} records to CSV: {self.output_csv}")

        with open(self.output_csv, mode="w", encoding=FILE_ENCODING, newline="") as f:
            writer = csv.DictWriter(
                f, fieldnames=list(ECIFollowupWebsiteRecord.__dataclass_fields__.keys())
            )
            writer.writeheader()
            for r in records:
                writer.writerow(r.to_dict())


class ECIResponseDataLoader:
    """Loads and provides access to ECI response data from CSV files."""

    def __init__(self, csv_path: Path):
        """Load response data from CSV file into memory."""
        self.records = self._load_from_csv(csv_path)

    def _load_from_csv(self, csv_path: Path) -> dict:
        """Parse CSV file and return dictionary keyed by registration number."""
        responses_data = {}

        with open(csv_path, mode="r", encoding=FILE_ENCODING) as f:
            reader = csv.DictReader(f)
            for row in reader:
                reg_num = row[CSV_FIELD_REGISTRATION_NUMBER]
                responses_data[reg_num] = {
                    CSV_FIELD_INITIATIVE_TITLE: row[CSV_FIELD_INITIATIVE_TITLE],
                    CSV_FIELD_FOLLOWUP_DEDICATED_WEBSITE: row[
                        CSV_FIELD_FOLLOWUP_DEDICATED_WEBSITE
                    ],
                }

        return responses_data

    def get_title(self, registration_number: str) -> str:
        """Retrieve initiative title for given registration number."""
        return self.records[registration_number][CSV_FIELD_INITIATIVE_TITLE]

    def get_website_url(self, registration_number: str) -> str:
        """Retrieve followup dedicated website URL for given registration number."""
        return self.records[registration_number][CSV_FIELD_FOLLOWUP_DEDICATED_WEBSITE]
