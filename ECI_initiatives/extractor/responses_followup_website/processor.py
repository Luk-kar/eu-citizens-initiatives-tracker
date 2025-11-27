import os
import glob
import csv
from datetime import datetime
from .model import ECIFollowupWebsiteRecord
from .parser.extractors import FollowupWebsiteExtractor


class ECIFollowupWebsiteProcessor:
    def __init__(self):
        # Find latest timestamped directory under data
        data_base = os.path.join(os.path.dirname(__file__), "../../../data")

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

        self.input_dir = max(all_dirs, default=None)  # use latest
        self.output_dir = self.input_dir
        self.output_csv = os.path.join(
            self.output_dir,
            f"eci_responses_followup_website_{os.path.basename(self.output_dir)}.csv",
        )

    def run(self):
        # Find all HTML files in the source directory
        html_files = glob.glob(
            os.path.join(self.input_dir, "responses_followup_website", "*.html")
        )
        records = []
        for path in html_files:
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

        # Write to CSV
        with open(self.output_csv, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(
                f, fieldnames=list(ECIFollowupWebsiteRecord.__dataclass_fields__.keys())
            )
            writer.writeheader()
            for r in records:
                writer.writerow(r.to_dict())
