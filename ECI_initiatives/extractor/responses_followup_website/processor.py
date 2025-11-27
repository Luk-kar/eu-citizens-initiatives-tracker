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
        html_files = glob.glob(os.path.join(html_dir, "*.html"))

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
                    registration_number=extractor.extract_registration_number(),
                    commission_answer_text=extractor.extract_commission_answer_text(),
                    followup_latest_date=extractor.extract_followup_latest_date(),
                    followup_most_future_date=extractor.extract_followup_most_future_date(),
                    commission_deadlines=extractor.extract_commission_deadlines(),
                    official_communication_document_urls=extractor.extract_official_communication_document_urls(),
                    followup_dedicated_website=extractor.extract_followup_dedicated_website(),
                    laws_actions=extractor.extract_laws_actions(),
                    policies_actions=extractor.extract_policies_actions(),
                    followup_events_with_dates=extractor.extract_followup_events_with_dates(),
                    referenced_legislation_by_name=extractor.extract_referenced_legislation_by_name(),
                    referenced_legislation_by_id=extractor.extract_referenced_legislation_by_id(),
                    final_outcome_status=extractor.extract_final_outcome_status(),
                    commission_promised_new_law=extractor.extract_commission_promised_new_law(),
                    commission_rejected_initiative=extractor.extract_commission_rejected_initiative(),
                    commission_rejection_reason=extractor.extract_commission_rejection_reason(),
                    has_followup_section=extractor.extract_has_followup_section(),
                    has_roadmap=extractor.extract_has_roadmap(),
                    has_workshop=extractor.extract_has_workshop(),
                    has_partnership_programs=extractor.extract_has_partnership_programs(),
                    court_cases_referenced=extractor.extract_court_cases_referenced(),
                    law_implementation_date=extractor.extract_law_implementation_date(),
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
