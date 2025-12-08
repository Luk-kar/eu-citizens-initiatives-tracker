# Python
from datetime import datetime, date
from pathlib import Path
import re
from typing import Optional, Dict, List, Union, Callable
import logging

# Third-party
from bs4 import BeautifulSoup

# Local
from ...responses.parser.extractors.outcome import (
    LegislativeOutcomeExtractor,
    APPLICABLE_DATE_PATTERNS,
    REJECTION_REASONING_KEYWORDS,
    parse_date_string,
    DEADLINE_PATTERNS,
    convert_deadline_to_date,
    LegislativeStatus,
)
from ...responses.parser.extractors.followup import (
    FollowUpActivityExtractor,
    parse_any_date_format,
)
from ...responses.parser.extractors.structural import StructuralAnalysisExtractor
from ...responses.parser.base.text_utilities import normalize_whitespace
from ...responses.parser.extractors.legislative_references import LegislativeReferences


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
        content_copy = content_div.__copy__()

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
            r"https?://ec\.citizens-initiative\.europa\.eu/public/initiatives/successful/details/\d{4}/\d{6}(_[a-z]{2})?/?$",
            r"https?://citizens-initiative\.europa\.eu/initiatives/details/\d{4}/\d{6}[_]?[a-z]{2}/?$",
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


class FollowupWebsiteLegislativeOutcomeExtractor(LegislativeOutcomeExtractor):
    """
    Custom extractor for followup website pages.

    Overrides content extraction to handle the nested div structure
    used in followup website pages, where h2 headers and content
    are wrapped in separate <div class="ecl"> containers.
    """

    # Class constant for standard content tags (excludes "ul" to avoid duplicates with "li")
    DEFAULT_CONTENT_TAGS = ["li", "p", "ol", "pre"]

    def _find_answer_section(self, soup: BeautifulSoup):
        """
        Find the Answer section header in followup website HTML.

        Followup websites only use 'response-of-the-commission' as the section ID.
        """
        return soup.find("h2", id="response-of-the-commission")

    def _extract_legislative_content(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Extract all text content from Response and Follow-up sections.

        Followup website pages have critical status information scattered
        across multiple sections:
        - "Response of the Commission"
        - "Follow-up on the Commission's actions"
        - "Next steps"

        Returns:
            Normalized lowercase string or None if section not found.
        """
        all_text = []

        # Define sections to extract from (in order)
        section_ids = [
            "response-of-the-commission",
            "follow-up-on-the-commissions-actions",
            "next-steps",
        ]

        for section_id in section_ids:
            # Find the section header
            section_header = soup.find("h2", id=section_id)

            if not section_header:
                # Try alternative patterns
                if section_id == "follow-up-on-the-commissions-actions":
                    section_header = soup.find(
                        "h2", string=lambda t: t and "follow-up" in t.lower()
                    )
                elif section_id == "next-steps":
                    section_header = soup.find(
                        "h2", string=lambda t: t and "next steps" in t.lower()
                    )

            if not section_header:
                continue

            # Get parent div of the h2
            parent = section_header.find_parent("div")
            if not parent:
                continue

            # Get the next sibling div after the parent (contains content)
            content_container = parent.find_next_sibling("div")

            if content_container:
                section_text = []

                # Get this container's text
                section_text.append(content_container.get_text(strip=False))

                # Check following sibling divs
                next_sibling = content_container.find_next_sibling("div")
                while next_sibling:
                    # Stop if we hit another h2 section
                    if next_sibling.find("h2"):
                        found_h2 = next_sibling.find("h2")
                        h2_id = found_h2.get("id", "") if found_h2 else ""

                        if h2_id and h2_id not in section_ids:
                            break
                        elif h2_id in section_ids:
                            break

                    if not self._should_skip_element(next_sibling):
                        section_text.append(next_sibling.get_text(strip=False))

                    next_sibling = next_sibling.find_next_sibling("div")

                if section_text:
                    all_text.extend(section_text)

        if not all_text:
            return None

        content = " ".join(all_text).lower()
        content = normalize_whitespace(content)

        return content

    # ========================================================================
    # TEMPLATE METHODS FOR CONTENT GATHERING & ITERATION
    # ========================================================================

    def _process_content_elements(
        self,
        soup: BeautifulSoup,
        processor_func: Callable,
        allowed_tags: Optional[List[str]] = None,
        check_non_empty: bool = True,
        accumulate_results: bool = True,
        early_exit_on_match: bool = False,
    ) -> any:
        """
        Template method for content gathering and processing pattern.

        Handles the common workflow of:
        1. Finding answer section
        2. Gathering content elements
        3. Iterating and processing with callback
        4. Returning results

        Args:
            soup: BeautifulSoup parsed HTML document
            processor_func: Callback function that processes each element.
                           Signature: processor_func(element, **context) -> result
                           - For accumulate_results=True: returns items to accumulate (list/dict/value)
                           - For accumulate_results=False: returns bool (for early exit patterns)
            allowed_tags: List of HTML tags to collect. Defaults to DEFAULT_CONTENT_TAGS
            check_non_empty: If True, only include elements with non-empty text
            accumulate_results: If True, accumulates results from processor_func into a list.
                               If False, used for boolean checks (returns first True)
            early_exit_on_match: If True, stops processing when processor_func returns truthy value
                                (only applies when accumulate_results=False)

        Returns:
            - If accumulate_results=True: List of accumulated results from processor_func
            - If accumulate_results=False: Boolean (True if any processor_func returned True)

        Raises:
            ValueError: If answer section not found or no content elements found
        """
        try:
            # Step 1: Find answer section
            answer_section = self._find_answer_section(soup)
            if not answer_section:
                raise ValueError(
                    f"Answer section not found for {self.registration_number}"
                )

            # Step 2: Use provided tags or default
            tags_to_use = (
                allowed_tags if allowed_tags is not None else self.DEFAULT_CONTENT_TAGS
            )

            # Step 3: Gather content elements
            content_elements = self._gather_content_elements(
                answer_section, tags_to_use, check_non_empty=check_non_empty
            )

            if not content_elements:
                if check_non_empty:
                    raise ValueError(
                        f"Expected at least one element with tags: {tags_to_use} "
                        f"for {self.registration_number}"
                    )
                # If not checking non-empty, empty list is acceptable
                return [] if accumulate_results else False

            # Step 4: Process elements
            if accumulate_results:
                # Accumulation mode: collect all results
                results = []
                for element in content_elements:
                    result = processor_func(element)
                    if result is not None:
                        # Handle different return types
                        if isinstance(result, list):
                            results.extend(result)
                        elif isinstance(result, dict):
                            results.append(result)
                        else:
                            results.append(result)
                return results
            else:
                # Boolean/early-exit mode: return True on first match
                for element in content_elements:
                    result = processor_func(element)
                    if result and early_exit_on_match:
                        return True
                return False

        except Exception as e:
            raise ValueError(
                f"Error processing content elements for {self.registration_number}: {str(e)}"
            ) from e

    def _process_content_with_text_extraction(
        self,
        soup: BeautifulSoup,
        processor_func: Callable,
        allowed_tags: Optional[List[str]] = None,
        check_non_empty: bool = False,
    ) -> any:
        """
        Convenience wrapper for common pattern of extracting and normalizing text.

        Automatically extracts and normalizes text from each element before passing
        to processor_func.

        Args:
            soup: BeautifulSoup parsed HTML document
            processor_func: Callback function that processes normalized text.
                           Signature: processor_func(text, text_normalized, text_lower, element) -> result
            allowed_tags: List of HTML tags to collect
            check_non_empty: If True, only include elements with non-empty text

        Returns:
            Results from _process_content_elements
        """

        def text_processor(element):
            # Extract and normalize text
            text = element.get_text(strip=False)
            text_normalized = normalize_whitespace(text)
            text_lower = text_normalized.lower()

            # Call user's processor with normalized text
            return processor_func(text, text_normalized, text_lower, element)

        return self._process_content_elements(
            soup,
            text_processor,
            allowed_tags=allowed_tags,
            check_non_empty=check_non_empty,
            accumulate_results=True,
        )

    def _check_keywords_in_content(
        self,
        soup: BeautifulSoup,
        keywords: List[str],
        allowed_tags: Optional[List[str]] = None,
    ) -> bool:
        """
        Check if any keyword regex pattern matches in content elements.

        Args:
            soup: BeautifulSoup parsed HTML document
            keywords: List of regex patterns to search for
            allowed_tags: List of HTML tags to collect

        Returns:
            True if any keyword found, False otherwise
        """

        def check_keywords(text, text_normalized, text_lower, element):
            """Check if text contains any keywords."""
            for keyword in keywords:
                if re.search(keyword, text_lower):
                    return True
            return False

        return self._process_content_elements(
            soup,
            lambda elem: check_keywords(
                elem.get_text(strip=False),
                normalize_whitespace(elem.get_text(strip=False)),
                normalize_whitespace(elem.get_text(strip=False)).lower(),
                elem,
            ),
            allowed_tags=allowed_tags,
            check_non_empty=False,
            accumulate_results=False,
            early_exit_on_match=True,
        )

    # ========================================================================
    # EXTRACTION METHODS (REFACTORED TO USE TEMPLATES)
    # ========================================================================

    def extract_applicable_date(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Extract the date when regulation/directive became applicable.

        Overrides parent to handle followup website nested div structure.

        Returns:
            Date string in YYYY-MM-DD format or None if not applicable

        Raises:
            ValueError: If Answer section not found
        """
        try:
            answer_section = self._find_answer_section(soup)
            if not answer_section:
                raise ValueError(
                    f"Could not find Answer section for initiative {self.registration_number}"
                )

            # Check if this initiative has applicable status
            matcher = self._get_classifier(soup)
            if not matcher.check_applicable():
                return None

            # Followup website structure: get parent div, then its siblings
            parent = answer_section.find_parent("div")
            if not parent:
                return None

            # Get content container (next sibling after parent)
            content_container = parent.find_next_sibling("div")

            # Search through content and following divs
            current = content_container

            while current:

                if not self._should_skip_element(current):
                    text = current.get_text(strip=False)

                    # Check for "immediately" case first
                    if "became applicable immediately" in text.lower():

                        force_match = re.search(
                            r"entered into force on\s+(\d{1,2}\s+[A-Za-z]+\s+\d{4})",
                            text,
                            re.IGNORECASE,
                        )

                        if force_match:
                            date_str = force_match.group(1).strip()
                            parsed_date = parse_date_string(date_str)
                            if parsed_date:
                                return parsed_date

                    # Check each pattern
                    for pattern in APPLICABLE_DATE_PATTERNS:
                        match = re.search(pattern, text, re.IGNORECASE)
                        if match:
                            if match.groups():
                                date_str = match.group(1).strip()
                                parsed_date = parse_date_string(date_str)
                                if parsed_date:
                                    return parsed_date

                current = current.find_next_sibling("div")

            return None

        except Exception as e:
            raise ValueError(
                f"Error extracting applicable date for {self.registration_number}: {str(e)}"
            ) from e

    def extract_commissions_deadlines(self, soup: BeautifulSoup) -> Optional[dict]:
        """
        Extract all Commission deadlines mentioned in the response as JSON.

        Returns a dictionary where keys are dates (YYYY-MM-DD) and
        values are phrases connected to those dates.

        Format: dict like:
        {
            "2018-05-31": "committed to come forward with a legislative proposal",
            "2026-03-31": "will communicate on the most appropriate action",
        }

        Returns:
            dict with date->phrase mapping or None if no deadlines found

        Raises:
            ValueError: If Answer section not found
        """
        try:
            deadlines_dict = {}

            def process_deadline_element(text, text_normalized, text_lower, element):
                """Process each element for deadline patterns."""
                # Check each pattern
                for pattern in DEADLINE_PATTERNS:
                    for match in re.finditer(pattern, text_lower, re.IGNORECASE):
                        deadline_text = match.group(1).strip()

                        if deadline_text:
                            deadline_cleaned = self._clean_deadline_text(deadline_text)
                            if deadline_cleaned:
                                deadline_date = convert_deadline_to_date(
                                    deadline_cleaned
                                )
                                if deadline_date:
                                    full_text = text_normalized

                                    # Append or create entry
                                    if deadline_date in deadlines_dict:
                                        if (
                                            full_text
                                            not in deadlines_dict[deadline_date]
                                        ):
                                            deadlines_dict[
                                                deadline_date
                                            ] += f"; {full_text}"
                                    else:
                                        deadlines_dict[deadline_date] = full_text
                return None  # We accumulate in deadlines_dict directly

            # Use the template method
            self._process_content_with_text_extraction(
                soup,
                process_deadline_element,
                allowed_tags=["li", "p", "ol", "pre"],  # Explicit tags for deadlines
                check_non_empty=False,
            )

            return deadlines_dict if deadlines_dict else None

        except Exception as e:
            raise ValueError(
                f"Error extracting commission deadlines for {self.registration_number}: {str(e)}"
            ) from e

    def _extract_mixed_response_reasoning(self, answer_section) -> str:
        """
        Extract reasoning for mixed response (both commitment and rejection).
        Finds all text mentioning 'legislative proposal'.

        Args:
            answer_section: BeautifulSoup element of Answer section (h2 element)

        Returns:
            Combined text of all relevant paragraphs

        Raises:
            ValueError: If no relevant text found
        """
        legislative_proposal_paragraphs = []

        # Get the parent div of the h2, then find its siblings
        parent_div = answer_section.parent
        siblings = parent_div.find_next_siblings() if parent_div else []

        for sibling in siblings:
            if self._should_skip_element(sibling):
                if sibling.name == "h2":
                    break
                continue

            # Handle div containers (e.g., <div class="ecl">)
            if sibling.name == "div":
                # Look for paragraphs inside the div
                for element in sibling.find_all(
                    ["p", "li", "ul", "ol"], recursive=True
                ):
                    extracted_text = self._extract_text_with_keyword_filter(
                        element, ["legislative proposal"]
                    )
                    if extracted_text:
                        legislative_proposal_paragraphs.append(extracted_text)
            else:
                # Direct paragraph or list element
                extracted_text = self._extract_text_with_keyword_filter(
                    sibling, ["legislative proposal"]
                )
                if extracted_text:
                    legislative_proposal_paragraphs.append(extracted_text)

        if legislative_proposal_paragraphs:
            return " ".join(legislative_proposal_paragraphs)

        raise ValueError(
            "Failed to extract rejection reasoning for mixed response: "
            f"{self.registration_number}.\n"
            f"The Commission committed to some legislative action but rejected other aims.\n"
            f"No paragraphs containing 'legislative proposal' were found in the Answer section.\n"
            f"legislative_proposal_paragraphs:\n{legislative_proposal_paragraphs}\n"
            f"answer_section:\n{answer_section}\n"
        )

    def _extract_pure_rejection_reasoning(self, answer_section) -> str:
        """
        Extract reasoning for pure rejection (no commitment).
        Finds all text containing rejection keywords.

        Args:
            answer_section: BeautifulSoup element of Answer section (h2 element)

        Returns:
            Combined text of all relevant paragraphs or fallback message
        """
        rejection_sentences = []

        # Get the parent div of the h2, then find its siblings
        parent_div = answer_section.parent
        siblings = parent_div.find_next_siblings() if parent_div else []

        for sibling in siblings:
            if self._should_skip_element(sibling):
                if sibling.name == "h2":
                    break
                continue

            # Handle div containers (e.g., <div class="ecl">)
            if sibling.name == "div":
                # Look for paragraphs inside the div
                for element in sibling.find_all(
                    ["p", "li", "ul", "ol"], recursive=True
                ):
                    extracted_text = self._extract_text_with_keyword_filter(
                        element, REJECTION_REASONING_KEYWORDS
                    )
                    if extracted_text:
                        rejection_sentences.append(extracted_text)
            else:
                # Direct paragraph or list element
                extracted_text = self._extract_text_with_keyword_filter(
                    sibling, REJECTION_REASONING_KEYWORDS
                )
                if extracted_text:
                    rejection_sentences.append(extracted_text)

        if rejection_sentences:
            return " ".join(rejection_sentences)

        return "The Commission decided not to make a legislative proposal."

    def extract_legislative_action(self, soup: BeautifulSoup) -> Optional[dict]:
        """
        Extract LEGISLATIVE actions - proposals, adoptions, laws, regulations, directives.

        Excludes: rejection statements, enforcement activities, policy actions.

        Returns JSON string with list of legislative actions or None

        Each action contains:
        - type: Type of action (e.g., "Regulation Proposal", "Directive Revision")
        - description: Brief description of the action
        - status: Status of action ("proposed", "adopted", "in_force", "withdrawn", "planned")
        - date: Date in YYYY-MM-DD format (when applicable)
        - document_url: URL to official document (optional)
        """
        try:

            def process_legislative_element(element):
                """Extract legislative actions from element."""
                return self._extract_actions_from_section(element)

            # Use the template method
            actions = self._process_content_elements(
                soup,
                process_legislative_element,
                allowed_tags=None,  # Uses DEFAULT_CONTENT_TAGS
                check_non_empty=True,
                accumulate_results=True,
            )

            if not actions:
                return None

            # Remove duplicates
            unique_actions = self._deduplicate_actions(
                actions, key_fields=["type", "description", "date"]
            )

            return unique_actions

        except Exception as e:
            raise ValueError(
                f"Error extracting legislative action for {self.registration_number}: {str(e)}"
            ) from e

    def _extract_actions_from_section(self, section) -> list:
        """
        Extract legislative actions from a specific element.

        Args:
            section: BeautifulSoup element (can be p, div, li, etc.)

        Returns:
            List of action dictionaries
        """
        actions = []

        # Build action patterns from LegislativeStatus
        action_patterns = []
        for status in LegislativeStatus.ALL_STATUSES:
            for pattern in status.action_patterns:
                action_patterns.append(
                    {
                        "pattern": pattern,
                        "status_obj": status,
                    }
                )

        # Process THE ELEMENT ITSELF (not its siblings)
        if section.name in ["p", "li"]:
            # Direct text element - process it
            self._process_element_for_legislative_action(
                section, action_patterns, actions
            )
        else:
            # Container element (div, ul, ol) - find text elements within
            for elem in section.find_all(["p", "li"], recursive=False):
                self._process_element_for_legislative_action(
                    elem, action_patterns, actions
                )

        return actions

    def extract_non_legislative_action(self, soup: BeautifulSoup) -> Optional[dict]:
        """
        Extract non-legislative actions as JSON array.

        Each item contains: type, description, date

        Returns dict or None
        """
        try:

            def process_non_legislative_element(element):
                """Extract non-legislative actions from element."""
                return self._extract_non_legislative_actions_from_section(element)

            # Use the template method
            actions = self._process_content_elements(
                soup,
                process_non_legislative_element,
                allowed_tags=None,  # Uses DEFAULT_CONTENT_TAGS
                check_non_empty=True,
                accumulate_results=True,
            )

            if not actions:
                return None

            # Remove duplicates
            unique_actions = self._deduplicate_actions(
                actions, key_fields=["type", "description", "date"]
            )

            return unique_actions

        except Exception as e:
            raise ValueError(
                f"Error extracting non-legislative action for {self.registration_number}: {str(e)}"
            ) from e

    def _gather_content_elements(
        self, start_section, allowed_tags: list, check_non_empty: bool = True
    ) -> list:
        """
        Gather content elements following a section until social media share element.

        Args:
            start_section: BeautifulSoup element to start from (e.g., h2 section header)
            allowed_tags: List of tag names to collect (e.g., ["li", "p", "ol"])
            check_non_empty: If True, only include elements with non-empty text

        Returns:
            List of BeautifulSoup elements matching the criteria
        """
        content_elements = []

        # Start from section and iterate through ALL following elements
        current = start_section.find_next()

        while current:
            # Stop when we find the social media share element
            if "ecl-social-media-share__description" in current.get("class", []):
                break

            # Only process allowed tags with optional non-empty text check
            if current.name in allowed_tags and not self._should_skip_element(current):
                if check_non_empty:
                    # Check for non-empty text
                    if current.get_text(strip=True):
                        content_elements.append(current)
                else:
                    content_elements.append(current)

            # Move to next element in document order
            current = current.find_next()

        return content_elements

    def _extract_non_legislative_actions_from_section(self, section) -> list:
        """
        Extract non-legislative actions from a specific element or section.

        Args:
            section: BeautifulSoup element (can be p, li, h2, div, etc.)

        Returns:
            List of action dictionaries
        """
        actions = []

        # If section is a text element (p, li), process it directly
        if section.name in ["p", "li"]:
            self._process_element_for_non_legislative_action(section, actions)
            return actions

        # If section is a container (ul, ol), process its direct children
        if section.name in ["ul", "ol"]:
            list_items = section.find_all("li", recursive=False)
            for li in list_items:
                self._process_element_for_non_legislative_action(li, actions)
            return actions

        # Otherwise (e.g., h2 section header), iterate through siblings after it
        current = section.next_sibling

        while current:
            # Stop at next h2 section
            if hasattr(current, "name") and current.name == "h2":
                break

            if not hasattr(current, "name"):
                current = current.next_sibling
                continue

            # Process paragraph elements
            if current.name == "p":
                self._process_element_for_non_legislative_action(current, actions)

            # Process unordered lists
            elif current.name == "ul":
                list_items = current.find_all("li", recursive=False)
                for li in list_items:
                    self._process_element_for_non_legislative_action(li, actions)

            # Process ordered lists
            elif current.name == "ol":
                list_items = current.find_all("li", recursive=False)
                for li in list_items:
                    self._process_element_for_non_legislative_action(li, actions)

            current = current.next_sibling

        return actions

    def extract_has_roadmap(self, soup: BeautifulSoup) -> Optional[bool]:
        """
        Check if initiative has a roadmap mentioned in follow-up.

        Looks for keywords like "roadmap", "roadmap to phase out", etc.

        Args:
            soup: BeautifulSoup parsed HTML document

        Returns:
            True if roadmap is mentioned, False otherwise

        Raises:
            ValueError: If critical error occurs during detection
        """
        try:
            roadmap_keywords = [r"\broadmaps?\b", r"\broad maps?\b"]
            return self._check_keywords_in_content(soup, roadmap_keywords)

        except Exception as e:
            raise ValueError(
                f"Error checking roadmap for {self.registration_number}: {str(e)}"
            ) from e

    def extract_has_workshop(self, soup: BeautifulSoup) -> Optional[bool]:
        """
        Check if initiative has workshops/conferences mentioned in follow-up.

        Args:
            soup: BeautifulSoup parsed HTML document

        Returns:
            True if workshop/conference mentioned, False otherwise

        Raises:
            ValueError: If critical error occurs during detection
        """
        try:
            workshop_keywords = [
                r"\bworkshops?\b",
                r"\bconferences?\b",
                r"\bscientific conferences?\b",
                r"\bscientific debates?\b",
                r"\bstakeholder meetings?\b",
                r"\bstakeholder conferences?\b",
                r"\bstakeholder debates?\b",
                r"\borgani[sz]ed workshops?\b",
                r"\borgani[sz]ed conferences?\b",
                r"\bseries of workshops?\b",
                r"\bseries of conferences?\b",
                r"\broundtables?\b",
                r"\bsymposia\b",
                r"\bsymposiums?\b",
                r"\bseminars?\b",
            ]
            return self._check_keywords_in_content(soup, workshop_keywords)

        except Exception as e:
            raise ValueError(
                f"Error checking workshop for {self.registration_number}: {str(e)}"
            ) from e

    def extract_has_partnership_programs(self, soup: BeautifulSoup) -> Optional[bool]:
        """
        Check if initiative has partnership programs mentioned in follow-up.

        Args:
            soup: BeautifulSoup parsed HTML document

        Returns:
            True if partnership programs mentioned, False otherwise

        Raises:
            ValueError: If critical error occurs during detection
        """
        try:
            partnership_keywords = [
                r"\bpartnership programs?\b",
                r"\bpartnership programmes?\b",
                r"\bpartnership plans?\b",
                r"\bpublic-public partnerships?\b",
                r"\beuropean partnerships? for\b",
                r"\bpartnership between\b",
                r"\bpartnerships between\b",
                r"\bsupport to partnerships?\b",
                r"\bcooperation programmes?\b",
                r"\bcollaboration programmes?\b",
                r"\bjoint programmes?\b",
                r"\bformal partnerships?\b",
                r"\bestablished partnerships?\b",
                r"\binternational partners?\b",
            ]
            return self._check_keywords_in_content(soup, partnership_keywords)

        except Exception as e:
            raise ValueError(
                f"Error checking partnership programs for {self.registration_number}: {str(e)}"
            ) from e

    def _extract_dates_from_content_elements(
        self, content_elements: list
    ) -> Optional[list]:
        """
        Extract all date strings from content elements.

        Date formats matched:
            - "27 March 2021" (full month name)
            - "27 Mar 2021" (abbreviated month name)
            - "27/03/2021" (slash-separated)
            - "27-03-2021" (dash-separated)
            - "2021-03-27" (ISO format)
            - "February 2024" (month and year only)
            - "Mar 2024" (abbreviated month and year)
            - "2024" (year only)

        Args:
            content_elements: List of BeautifulSoup elements to extract dates from

        Returns:
            List of date strings found, or None if no content elements provided.
            Returns empty list if elements exist but no dates found.

        Raises:
            ValueError: If critical error occurs during extraction
        """
        try:
            if not content_elements:
                return None

            # Extract all text from gathered content elements
            full_text = ""
            for element in content_elements:
                full_text += element.get_text(separator=" ", strip=True) + " "

            # Regex pattern to find all potential dates
            date_pattern = (
                r"(?:(?:\d{1,2}\s+)?(?:January|February|March|April|May|June|"
                r"July|August|September|October|November|December|"
                r"Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4})|"
                r"(?:\d{1,2}[-/]\d{1,2}[-/]\d{2,4})|"
                r"(?:\d{4}[-/]\d{1,2}[-/]\d{1,2})|"
                r"(?:\b\d{4}\b)"
            )

            date_matches = re.findall(date_pattern, full_text, re.IGNORECASE)

            return date_matches if date_matches else []

        except Exception as e:
            raise ValueError(
                f"Error extracting dates from content elements for {self.registration_number}: {str(e)}"
            ) from e

    def _parse_date_strings(self, date_matches: list) -> Optional[list]:
        """
        Parse raw date strings into standardized YYYY-MM-DD format.

        Args:
            date_matches: List of raw date strings to parse

        Returns:
            List of successfully parsed date strings in YYYY-MM-DD format.
            Returns None if input is empty or no dates could be parsed.

        Raises:
            ValueError: If critical error occurs during parsing
        """
        try:
            if not date_matches:
                return None

            # Parse all found dates and keep track of valid ones
            parsed_dates = []

            for date_str in date_matches:
                parsed = parse_any_date_format(date_str)
                if parsed:
                    parsed_dates.append(parsed)

            return parsed_dates if parsed_dates else None

        except Exception as e:
            raise ValueError(
                f"Error parsing date strings for {self.registration_number}: {str(e)}"
            ) from e

    def _get_today_date(self) -> date:
        """Return today's date. Can be mocked for testing."""
        return datetime.now().date()

    def _filter_latest_date_by_today(self, parsed_dates: list) -> Optional[str]:
        """
        Filter dates to only those <= today and return the latest.

        Args:
            parsed_dates: List of date strings in YYYY-MM-DD format

        Returns:
            Latest date that is <= today, or None if no valid dates
        """
        today = self._get_today_date()

        # Convert strings to date objects and filter
        valid_dates = []
        for date_str in parsed_dates:
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
                if date_obj <= today:
                    valid_dates.append(date_obj)
            except ValueError:
                continue

        if not valid_dates:
            return None

        # Return the latest (maximum) date
        latest = max(valid_dates)
        return latest.strftime("%Y-%m-%d")

    def _filter_most_future_date_by_today(self, parsed_dates: list) -> Optional[str]:
        """
        Filter dates to only those > today and return the furthest future date.

        Args:
            parsed_dates: List of date strings in YYYY-MM-DD format

        Returns:
            Furthest future date that is > today, or None if no valid dates
        """
        today = self._get_today_date()

        # Convert strings to date objects and filter
        future_dates = []
        for date_str in parsed_dates:
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
                if date_obj > today:
                    future_dates.append(date_obj)
            except ValueError:
                continue

        if not future_dates:
            return None

        # Return the furthest future (maximum) date
        furthest = max(future_dates)
        return furthest.strftime("%Y-%m-%d")

    def extract_followup_latest_date(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Extract most recent date from follow-up section that is not later than today.

        Args:
            soup: BeautifulSoup parsed HTML document

        Returns:
            Latest date found in YYYY-MM-DD format that is <= today's date.
            Returns None if no valid dates found.

        Raises:
            ValueError: If critical error occurs during extraction
        """
        try:
            # Find Answer section (acts as starting point for followup content)
            answer_section = self._find_answer_section(soup)

            if not answer_section:
                raise ValueError(
                    f"Answer section not found for {self.registration_number}."
                )

            # Step 1: Gather all relevant content elements
            content_elements = self._gather_content_elements(
                answer_section, self.DEFAULT_CONTENT_TAGS, check_non_empty=False
            )

            if not content_elements:
                raise ValueError(
                    f"Expected at least one element with tags: {self.DEFAULT_CONTENT_TAGS} "
                    f"for {self.registration_number}"
                )

            # Step 2: Extract date strings from content elements
            date_matches = self._extract_dates_from_content_elements(content_elements)

            if not date_matches:
                return None

            # Step 3: Parse date strings to YYYY-MM-DD format
            parsed_dates = self._parse_date_strings(date_matches)

            if not parsed_dates:
                return None

            # Step 4: Filter dates to only those <= today and return the latest
            latest_date = self._filter_latest_date_by_today(parsed_dates)

            return latest_date

        except Exception as e:
            raise ValueError(
                f"Error extracting latest update date for {self.registration_number}: {str(e)}"
            ) from e

    def extract_followup_most_future_date(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Extract the furthest future date from follow-up section.

        Args:
            soup: BeautifulSoup parsed HTML document

        Returns:
            Furthest future date found in YYYY-MM-DD format that is > today's date.
            Returns None if no future dates found.

        Raises:
            ValueError: If Answer section not found or critical error occurs
        """
        try:
            # Find Answer section (acts as starting point for followup content)
            answer_section = self._find_answer_section(soup)

            if not answer_section:
                raise ValueError(
                    f"Answer section not found for {self.registration_number}."
                )

            # Step 1: Gather all relevant content elements
            content_elements = self._gather_content_elements(
                answer_section, self.DEFAULT_CONTENT_TAGS, check_non_empty=False
            )

            if not content_elements:
                raise ValueError(
                    f"Expected at least one element with tags: {self.DEFAULT_CONTENT_TAGS} "
                    f"for {self.registration_number}"
                )

            # Step 2: Extract date strings from content elements
            date_matches = self._extract_dates_from_content_elements(content_elements)

            if not date_matches:
                return None

            # Step 3: Parse date strings to YYYY-MM-DD format
            parsed_dates = self._parse_date_strings(date_matches)

            if not parsed_dates:
                return None

            # Step 4: Filter dates to only those > today and return the furthest
            most_future_date = self._filter_most_future_date_by_today(parsed_dates)

            return most_future_date

        except Exception as e:
            raise ValueError(
                f"Error extracting most future date for {self.registration_number}: {str(e)}"
            ) from e

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _deduplicate_actions(
        self,
        actions: List[dict],
        key_fields: List[str] = ["type", "description", "date"],
    ) -> List[dict]:
        """
        Remove duplicate actions based on specified key fields.

        Args:
            actions: List of action dictionaries
            key_fields: Fields to use for deduplication key

        Returns:
            List of unique actions preserving original order
        """
        unique_actions = []
        seen = set()

        for action in actions:
            key = tuple(action.get(field, "") for field in key_fields)
            if key not in seen:
                seen.add(key)
                unique_actions.append(action)

        return unique_actions


class FollowupWebsiteFollowUpExtractor(FollowUpActivityExtractor):
    """
    Extended extractor that extracts follow-up events from the
    'Response of the Commission' section instead of the 'Follow-up' section.
    """

    def extract_followup_events_with_dates(
        self, soup: BeautifulSoup
    ) -> Optional[List[Dict[str, Union[List[str], str]]]]:
        """
        Extract follow-up actions with associated dates from Response of the Commission section.

        Extracts content from after 'Response of the Commission' h2 until
        hitting stop sections like 'Related links', 'Press release', etc.

        Args:
            soup: BeautifulSoup object of the HTML document

        Returns:
            List of dictionaries with structure:
                [{"dates": ["2020-01-01", "2021-01-01"], "action": "Following up on its commitment..."}, ...]
            Returns None if no Response of the Commission section exists or no valid actions are found

        Raises:
            ValueError: If critical error occurs during extraction
        """
        try:
            # Step 1: Locate the target section
            response_h2 = soup.find("h2", id="response-of-the-commission")
            if not response_h2:
                raise ValueError(
                    f"No 'Response of the Commission' section found for {self.registration_number}"
                )

            # Step 2: Define the extraction boundary - find the next h2 after response
            start_h2 = response_h2.find_next("h2", class_="ecl-u-type-heading-2")
            if not start_h2:
                raise ValueError(
                    f"No content section found after 'Response of the Commission' for {self.registration_number}"
                )

            # Define stop section IDs
            stop_section_ids = [
                "related-links",
                "press-release",
                "video",
            ]

            # Step 3: Extract content elements between start_h2 and stop sections
            content_elements = []
            current_element = start_h2.find_next()

            while current_element:
                # Check if we've hit a stopping h2
                if (
                    current_element.name == "h2"
                    and current_element.get("class")
                    and "ecl-u-type-heading-2" in current_element.get("class", [])
                ):
                    h2_id = current_element.get("id")

                    if h2_id in stop_section_ids:
                        break

                # Collect <p> and <li> elements (include all, not just direct children)
                if current_element.name in ["p", "li"]:
                    # Use _extract_text_with_links to preserve link URLs
                    text_with_links = self._extract_text_with_links(current_element)
                    if text_with_links and not self._should_skip_text(text_with_links):
                        content_elements.append(text_with_links)

                # Move to next element in the document tree
                current_element = current_element.find_next()

            # Step 4: Process the extracted elements
            if not content_elements:
                raise ValueError(
                    f"No valid follow-up actions found in 'Response of the Commission' section "
                    f"for {self.registration_number}"
                )

            followup_actions = []
            for element_text in content_elements:
                # Normalize whitespace
                action_text_normalized = re.sub(r"\s+", " ", element_text)

                # Extract dates from the text
                dates = self._extract_dates_from_text(action_text_normalized)

                followup_actions.append(
                    {"dates": dates, "action": action_text_normalized}
                )

            return followup_actions

        except Exception as e:
            raise ValueError(
                f"Error extracting follow-up events with dates for {self.registration_number}: {str(e)}"
            ) from e
