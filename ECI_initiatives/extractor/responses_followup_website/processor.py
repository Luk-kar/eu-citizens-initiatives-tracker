import os
import glob
import csv
import logging
from pathlib import Path
from datetime import datetime
from .model import ECIFollowupWebsiteRecord
from .parser.extractors import FollowupWebsiteExtractor


class ECIFollowupWebsiteProcessor:
    def __init__(self):
        # Find latest timestamped directory under data
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent.parent
        data_root = "ECI_initiatives/data"
        data_base = project_root / data_root

        all_dirs = [
            d
            for d in glob.glob(os.path.join(data_base, "20*-*-*_*-*-*"))
            if os.path.isdir(d)
        ]

        if not all_dirs:
            raise FileNotFoundError(
                f"No timestamped data directories found in {data_base}. "
                f"Expected format: YYYY-MM-DD_HH-MM-SS"
            )

        self.input_dir = max(all_dirs)  # use latest
        self.output_dir = self.input_dir

        # Setup logging
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logs_dir = os.path.join(self.output_dir, "logs")
        os.makedirs(logs_dir, exist_ok=True)

        log_file = os.path.join(
            logs_dir, f"extractor_responses_followup_website_{timestamp}.log"
        )

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(log_file, encoding="utf-8"),
                logging.StreamHandler(),
            ],
        )
        self.logger = logging.getLogger(__name__)

        self.output_csv = os.path.join(
            self.output_dir,
            f"eci_responses_followup_website_{os.path.basename(self.output_dir)}.csv",
        )

        self.logger.info(f"Initialized ECIFollowupWebsiteProcessor")
        self.logger.info(f"Input directory: {self.input_dir}")
        self.logger.info(f"Output CSV: {self.output_csv}")
        self.logger.info(f"Log file: {log_file}")

    def run(self):
        # Find all HTML files in the source directory
        html_dir = os.path.join(self.input_dir, "responses_followup_website")
        html_files = glob.glob(os.path.join(html_dir, "**", "*.html"), recursive=True)

        self.logger.info(f"In the directory:\n{html_dir}")
        self.logger.info(f"Found {len(html_files)} HTML files to process")

        records = []
        for idx, path in enumerate(html_files, 1):
            self.logger.info(
                f"Processing file {idx}/{len(html_files)}: {os.path.basename(path)}"
            )

            try:
                with open(path, encoding="utf-8") as f:
                    html_content = f.read()

                extractor = FollowupWebsiteExtractor(html_content)
                record = ECIFollowupWebsiteRecord(
                    # Basic Initiative Metadata
                    registration_number=extract_registration_number(html_file_name),
                    initiative_title="",  # responses_list_data["initiative_title"]
                    followup_dedicated_website="",  # responses_list_data["followup_dedicated_website"]
                    # Commission Response Content
                    commission_answer_text=extractor.extract_commission_answer_text(
                        soup
                    ),
                    official_communication_document_urls=extractor.extract_official_communication_document_urls(
                        soup
                    ),
                    # SECTION 1: Final Outcome
                    final_outcome_status=extractor.extract_final_outcome_status(soup),
                    law_implementation_date=extractor.extract_law_implementation_date(
                        soup
                    ),
                    # SECTION 2: Commission's Initial Response
                    commission_promised_new_law=extractor.extract_commission_promised_new_law(
                        soup
                    ),
                    commission_deadlines=extractor.extract_commission_deadlines(soup),
                    commission_rejected_initiative=extractor.extract_commission_rejected_initiative(
                        soup
                    ),
                    commission_rejection_reason=extractor.extract_commission_rejection_reason(
                        soup
                    ),
                    # SECTION 3: Actions Taken
                    laws_actions=extractor.extract_laws_actions(soup),
                    policies_actions=extractor.extract_policies_actions(soup),
                    # Follow-up Activities Section
                    has_roadmap=extractor.extract_has_roadmap(soup),
                    has_workshop=extractor.extract_has_workshop(soup),
                    has_partnership_programs=extractor.extract_has_partnership_programs(
                        soup
                    ),
                    court_cases_referenced=extractor.extract_court_cases_referenced(
                        soup
                    ),
                    followup_latest_date=extractor.extract_followup_latest_date(soup),
                    followup_most_future_date=extractor.extract_followup_most_future_date(
                        soup
                    ),
                    # Structural Analysis Flags
                    referenced_legislation_by_id=extractor.extract_referenced_legislation_by_id(
                        soup
                    ),
                    referenced_legislation_by_name=extractor.extract_referenced_legislation_by_name(
                        soup
                    ),
                    followup_events_with_dates=extractor.extract_followup_events_with_dates(
                        soup
                    ),
                )
                records.append(record)
                self.logger.info(
                    f"Successfully processed: {record.registration_number}"
                )

            except Exception as e:
                self.logger.error(f"Error processing {path}: {e}", exc_info=True)
                continue

        # Write to CSV
        self.logger.info(f"Writing {len(records)} records to CSV: {self.output_csv}")

        with open(self.output_csv, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(
                f, fieldnames=list(ECIFollowupWebsiteRecord.__dataclass_fields__.keys())
            )
            writer.writeheader()
            for r in records:
                writer.writerow(r.to_dict())

        self.logger.info(f"Processing complete. Output written to {self.output_csv}")
