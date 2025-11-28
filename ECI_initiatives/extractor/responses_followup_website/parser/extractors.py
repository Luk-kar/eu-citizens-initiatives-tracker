from pathlib import Path
import re

from bs4 import BeautifulSoup


# Extraction stubs (no implementation included)
class FollowupWebsiteExtractor:
    def __init__(self, html_content):
        self.soup = BeautifulSoup(html_content, "html.parser")

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

    def extract_commission_answer_text(self) -> str:
        """
        Extract the Commission's response text content with links preserved.

        Finds the section under "Response of the Commission" heading
        and extracts all text content with hyperlinks in markdown format.

        Returns:
            Text content with links in [text](url) format, or empty string if not found.
        """
        # Find the "Response of the Commission" header
        header = self.soup.find("h2", id="response-of-the-commission")

        if not header:
            header = self.soup.find(
                "h2", string=lambda text: text and "Response of the Commission" in text
            )

        if not header:
            return ""

        # Get the parent container and content div
        header_parent = header.find_parent("div")
        if not header_parent:
            return ""

        content_div = header_parent.find_next_sibling("div", class_="ecl")
        if not content_div:
            return ""

        # Create a copy to modify
        content_copy = content_div.__copy__()

        # Remove unwanted elements
        for button in content_copy.find_all("button"):
            button.decompose()

        for svg in content_copy.find_all("svg"):
            svg.decompose()

        # Convert links to markdown format [text](url)
        for link in content_copy.find_all("a", href=True):
            link_text = link.get_text(strip=True)
            link_url = link.get("href")
            # Replace the link with markdown format
            link.replace_with(f"[{link_text}]({link_url})")

        # Extract text
        text_parts = []
        for element in content_copy.find_all(["p", "li"]):
            text = element.get_text(separator=" ", strip=True)
            if text:
                text_parts.append(text)

        full_text = "\n".join(text_parts)
        full_text = " ".join(full_text.split())

        return full_text

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
