from pathlib import Path
import re


# Extraction stubs (no implementation included)
class FollowupWebsiteExtractor:
    def __init__(self, html_content):
        self.html_content = html_content

    def extract_registration_number(self, html_file_name: str):
        """
        Extract registration number from filename.

        Expected filename format: YYYY_NNNNNN_en.html
        Returns format: YYYY/NNNNNN

        Args:
            html_file_name: Filename or full path to HTML file

        Returns:
            Registration number in YYYY/NNNNNN format

        Raises:
            ValueError: If filename doesn't match expected pattern
        """
        # Get just the filename if full path provided
        filename = Path(html_file_name).name

        # Pattern: YYYY_NNNNNN_en.html
        pattern = r"^(\d{4})_(\d{6})_[a-z]{2}\.html$"
        match = re.match(pattern, filename)

        if not match:
            raise ValueError(
                f"Invalid filename format: {filename}. "
                f"Expected format: YYYY_NNNNNN_en.html"
            )

        year = match.group(1)
        number = match.group(2)

        return f"{year}/{number}"

    def extract_commission_answer_text(self):
        pass

    def extract_followup_latest_date(self):
        pass

    def extract_followup_most_future_date(self):
        pass

    def extract_commission_deadlines(self):
        pass

    def extract_official_communication_document_urls(self):
        pass

    def extract_followup_dedicated_website(self):
        pass

    def extract_laws_actions(self):
        pass

    def extract_policies_actions(self):
        pass

    def extract_followup_events_with_dates(self):
        pass

    def extract_referenced_legislation_by_name(self):
        pass

    def extract_referenced_legislation_by_id(self):
        pass

    def extract_final_outcome_status(self):
        pass

    def extract_commission_promised_new_law(self):
        pass

    def extract_commission_rejected_initiative(self):
        pass

    def extract_commission_rejection_reason(self):
        pass

    def extract_has_followup_section(self):
        pass

    def extract_has_roadmap(self):
        pass

    def extract_has_workshop(self):
        pass

    def extract_has_partnership_programs(self):
        pass

    def extract_court_cases_referenced(self):
        pass

    def extract_law_implementation_date(self):
        pass
