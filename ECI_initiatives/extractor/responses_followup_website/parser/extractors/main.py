"""
Main extractor class for parsing European Citizens' Initiative
follow-up website HTML
into structured data records.
"""

# Python
from copy import copy
from pathlib import Path
import re
from typing import Optional, Dict, List
import logging

# Third-party
from bs4 import BeautifulSoup

# Local
from ....responses.parser.extractors.followup import (
    FollowUpActivityExtractor,
)
from ....responses.parser.extractors.structural import StructuralAnalysisExtractor
from ....responses.parser.extractors.legislative_references import LegislativeReferences
from .followup import FollowupWebsiteFollowUpExtractor
from .outcome import FollowupWebsiteLegislativeOutcomeExtractor


class FollowupWebsiteExtractor:
    """Extracts structured data from European Citizens' Initiative followup website HTML."""

    def __init__(self, html_content: str, logger: Optional[logging.Logger] = None):
        self.soup = BeautifulSoup(html_content, "html.parser")
        self.logger = logger or logging.getLogger(__name__)
        self.registration_number = None

        # Initialize extractors once (lazy loading via properties)
        self._outcome_extractor = None
        self._activity_extractor = None
        self._structural_extractor = None
        self._legislative_ref_extractor = None

    @property
    def outcome_extractor(self):
        """Lazy initialization of outcome extractor."""
        if self._outcome_extractor is None:
            self._outcome_extractor = FollowupWebsiteLegislativeOutcomeExtractor(
                registration_number=self.registration_number
            )
        return self._outcome_extractor

    @property
    def activity_extractor(self):
        """Lazy initialization of activity extractor."""
        if self._activity_extractor is None:
            self._activity_extractor = FollowUpActivityExtractor(logger=self.logger)
        return self._activity_extractor

    @property
    def structural_extractor(self):
        """Lazy initialization of structural extractor."""
        if self._structural_extractor is None:
            self._structural_extractor = StructuralAnalysisExtractor(logger=self.logger)
        return self._structural_extractor

    @property
    def legislative_ref_extractor(self):
        """Lazy initialization of legislative references extractor."""
        if self._legislative_ref_extractor is None:
            self._legislative_ref_extractor = LegislativeReferences(logger=self.logger)
        return self._legislative_ref_extractor

    @property
    def followup_extractor(self):
        """Lazy initialization of followup-specific extractor."""
        if not hasattr(self, "_followup_extractor") or self._followup_extractor is None:
            self._followup_extractor = FollowupWebsiteFollowUpExtractor(
                logger=self.logger, registration_number=self.registration_number
            )
        return self._followup_extractor

    def extract_registration_number(self, html_file_name: str) -> str:
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
        filename = Path(html_file_name).name
        pattern = r"^(\d{4})_(\d{6})_[a-z]{2}\.html$"
        match = re.match(pattern, filename)

        if not match:
            raise ValueError(
                f"Invalid filename format: {filename}. "
                f"Expected format: YYYY_NNNNNN_en.html"
            )

        year, number = match.groups()
        self.registration_number = f"{year}/{number}"
        return self.registration_number

    def extract_commission_answer_text(self) -> str:
        """
        Extract the Commission's response text content with links preserved.

        Finds the section under "Response of the Commission" heading
        and extracts all text content with hyperlinks in markdown format.

        Returns:
            Text content with links in [text](url) format, or empty string if not found.
        """
        header = self._find_commission_header()
        if not header:
            return ""

        content_div = self._get_commission_content_div(header)
        if not content_div:
            return ""

        return self._extract_text_with_links(content_div)

    def _find_commission_header(self):
        """Find the 'Response of the Commission' header element."""
        header = self.soup.find("h2", id="response-of-the-commission")
        if not header:
            header = self.soup.find(
                "h2", string=lambda text: text and "Response of the Commission" in text
            )
        return header

    def _get_commission_content_div(self, header):
        """Get the content div following the commission header."""
        header_parent = header.find_parent("div")
        if not header_parent:
            return None
        return header_parent.find_next_sibling("div", class_="ecl")

    def _extract_text_with_links(self, content_div):
        """Extract text from content div with links converted to markdown."""

        content_copy = copy(content_div)

        # Remove unwanted elements
        for element in content_copy.find_all(["button", "svg"]):
            element.decompose()

        # Convert links to markdown format
        for link in content_copy.find_all("a", href=True):
            link_text = link.get_text(strip=True)
            link_url = link.get("href")
            link.replace_with(f"[{link_text}]({link_url})")

        # Extract text from paragraphs and list items
        text_parts = [
            element.get_text(separator=" ", strip=True)
            for element in content_copy.find_all(["p", "li"])
            if element.get_text(strip=True)
        ]

        return " ".join(" ".join(text_parts).split())

    def extract_official_communication_document_urls(self) -> Optional[Dict[str, str]]:
        """
        Extract links to official Commission Communication documents.

        Searches for links containing 'Communication' or 'Annex' in the text,
        or links pointing to EC transparency register or presscorner.

        Returns:
            Dictionary of {link_text: url} or None if no documents found.
        """
        try:
            all_links = self._collect_communication_links()
            if not all_links:
                return None

            links_dict = self._build_links_dictionary(all_links)
            filtered_links = self._filter_excluded_urls(links_dict)

            return filtered_links if filtered_links else None

        except Exception as e:
            raise ValueError(
                f"Error extracting official communication document URLs: {str(e)}"
            ) from e

    def _collect_communication_links(self) -> List:
        """Collect all links matching communication criteria."""
        all_links = []

        for link in self.soup.find_all("a", href=True):
            link_text = link.get_text(strip=True)
            href = link.get("href", "")

            if self._is_communication_link(link_text, href):
                all_links.append(link)

        return all_links

    def _is_communication_link(self, link_text: str, href: str) -> bool:
        """Check if link matches communication criteria."""
        # Match links with Communication/Annex in text
        if re.search(r"(Communication|Annex|Annexes)", link_text, re.IGNORECASE):
            return True

        # Match EC transparency register URLs
        if re.search(
            r"ec\.europa\.eu/transparency/documents-register", href, re.IGNORECASE
        ):
            return True

        # Match EC presscorner URLs
        if re.search(r"ec\.europa\.eu/commission/presscorner", href, re.IGNORECASE):
            return True

        return False

    def _build_links_dictionary(self, links: List) -> Dict[str, str]:
        """Build dictionary from link elements."""
        return {
            link.get_text(strip=True): link.get("href", "")
            for link in links
            if link.get_text(strip=True) and link.get("href", "")
        }

    def _filter_excluded_urls(self, links_dict: Dict[str, str]) -> Dict[str, str]:
        """Remove duplicate and excluded URLs."""
        exclude_patterns = [
            r"https?://ec\.citizens-initiative\.europa\.eu/public/initiatives/successful/details/"
            r"\d{4}/\d{6}(_[a-z]{2})?/?$",
            r"https?://citizens-initiative\.europa\.eu/initiatives/details/"
            r"\d{4}/\d{6}[_]?[a-z]{2}/?$",
        ]

        seen_urls = set()
        filtered_links = {}

        for text, url in links_dict.items():
            if url in seen_urls:
                continue

            if not any(re.match(pattern, url) for pattern in exclude_patterns):
                filtered_links[text] = url
                seen_urls.add(url)

        return filtered_links

    # Outcome extraction methods (delegating to outcome_extractor)
    def extract_final_outcome_status(self) -> Optional[str]:
        """Extract the final outcome status of the initiative."""
        return self.outcome_extractor.extract_highest_status_reached(self.soup)

    def extract_law_implementation_date(self) -> Optional[str]:
        """Extract the date when regulation/directive became applicable."""
        return self.outcome_extractor.extract_applicable_date(self.soup)

    def extract_commission_promised_new_law(self):
        """Check if Commission promised new law."""
        return self.outcome_extractor.extract_proposal_commitment_stated(self.soup)

    def extract_commissions_deadlines(self):
        """Extract Commission's deadlines."""
        return self.outcome_extractor.extract_commissions_deadlines(self.soup)

    def extract_commission_rejected_initiative(self):
        """Check if Commission rejected the initiative."""
        return self.outcome_extractor.extract_proposal_rejected(self.soup)

    def extract_commission_rejection_reason(self):
        """Extract Commission's rejection reasoning."""
        return self.outcome_extractor.extract_rejection_reasoning(self.soup)

    def extract_laws_actions(self):
        """Extract legislative actions."""
        return self.outcome_extractor.extract_legislative_action(self.soup)

    def extract_policies_actions(self):
        """Extract non-legislative actions."""
        return self.outcome_extractor.extract_non_legislative_action(self.soup)

    def extract_has_roadmap(self):
        """Check if initiative has a roadmap."""
        return self.outcome_extractor.extract_has_roadmap(self.soup)

    def extract_has_workshop(self):
        """Check if initiative has workshops."""
        return self.outcome_extractor.extract_has_workshop(self.soup)

    def extract_has_partnership_programs(self):
        """Check if initiative has partnership programs."""
        return self.outcome_extractor.extract_has_partnership_programs(self.soup)

    # Activity extraction methods (delegating to activity_extractor)
    def extract_court_cases_referenced(self):
        """Extract referenced court cases."""
        return self.activity_extractor.extract_court_cases_referenced(self.soup)

    def extract_followup_latest_date(self):
        """Extract latest followup date."""
        return self.outcome_extractor.extract_followup_latest_date(self.soup)

    def extract_followup_most_future_date(self):
        """Extract most future followup date."""
        return self.outcome_extractor.extract_followup_most_future_date(self.soup)

    # Legislative reference extraction methods
    def extract_referenced_legislation_by_id(self):
        """Extract referenced legislation by ID."""
        return self.structural_extractor.extract_referenced_legislation_by_id(self.soup)

    def extract_referenced_legislation_by_name(self):
        """Extract referenced legislation by name."""
        return self.legislative_ref_extractor.extract_referenced_legislation_by_name(
            self.soup
        )

    def extract_followup_events_with_dates(self):
        """Extract followup events with their dates."""
        return self.followup_extractor.extract_followup_events_with_dates(self.soup)
