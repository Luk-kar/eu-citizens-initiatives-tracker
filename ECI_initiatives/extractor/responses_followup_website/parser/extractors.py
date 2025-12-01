from pathlib import Path
import re
from typing import Optional, Dict

from bs4 import BeautifulSoup

from ...responses.parser.extractors.outcome import (
    LegislativeOutcomeExtractor,
    APPLICABLE_DATE_PATTERNS,
    REJECTION_REASONING_KEYWORDS,
    parse_date_string,
    DEADLINE_PATTERNS,
    convert_deadline_to_date,
)
from ...responses.parser.base.text_utilities import normalize_whitespace


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

    def extract_official_communication_document_urls(self) -> Optional[Dict[str, str]]:
        """
        Extract links to official Commission Communication documents.

        Searches for links containing 'Communication' or 'Annex' in the text,
        or links pointing to EC transparency register or presscorner.

        Returns:
            Dictionary of {link_text: url} or None if no documents found.
        """
        try:
            all_links = []

            # Search through ALL links in the document
            for link in self.soup.find_all("a", href=True):
                link_text = link.get_text(strip=True)
                href = link.get("href", "")

                # Strategy 1: Match links with Communication/Annex in text
                if re.search(
                    r"(Communication|Annex|Annexes)", link_text, re.IGNORECASE
                ):
                    all_links.append(link)
                    continue

                # Strategy 2: Match EC transparency register URLs (official Communications)
                if re.search(
                    r"ec\.europa\.eu/transparency/documents-register",
                    href,
                    re.IGNORECASE,
                ):
                    all_links.append(link)
                    continue

                # Strategy 3: Match EC presscorner URLs (press releases about Communications)
                if re.search(
                    r"ec\.europa\.eu/commission/presscorner", href, re.IGNORECASE
                ):
                    all_links.append(link)
                    continue

            if not all_links:
                return None

            # Build dictionary of {text: url}
            links_dict = {}
            for link in all_links:
                text = link.get_text(strip=True)
                url = link.get("href", "")

                # Skip empty text or urls
                if not text or not url:
                    continue

                links_dict[text] = url

            # Exclusion patterns - remove initiative overview pages
            exclude_patterns = [
                r"https?://ec\.citizens-initiative\.europa\.eu/public/initiatives/successful/details/\d{4}/\d{6}(_[a-z]{2})?/?$",
                r"https?://citizens-initiative\.europa\.eu/initiatives/details/\d{4}/\d{6}[_]?[a-z]{2}/?$",
            ]

            # Remove duplicates by URL and apply exclusion patterns
            seen_urls = set()
            filtered_links_dict = {}

            for text, url in links_dict.items():
                if url in seen_urls:
                    continue

                should_exclude = False
                for pattern in exclude_patterns:
                    if re.match(pattern, url):
                        should_exclude = True
                        break

                if not should_exclude:
                    filtered_links_dict[text] = url
                    seen_urls.add(url)

            return filtered_links_dict if filtered_links_dict else None

        except Exception as e:
            raise ValueError(
                f"Error extracting official communication document URLs: {str(e)}"
            ) from e

    def extract_final_outcome_status(self) -> Optional[str]:
        """
        Extract the final outcome status of the initiative.

        Uses a custom LegislativeOutcomeExtractor for followup website structure
        to determine the highest status reached by the initiative
        (e.g., "Law Active", "Law Promised", "Rejected").

        Returns:
            Citizen-friendly status string or None if status cannot be determined.
        """

        # Use custom extractor for followup website structure
        outcome_extractor = FollowupWebsiteLegislativeOutcomeExtractor(
            registration_number=(
                self.registration_number
                if hasattr(self, "registration_number")
                else None
            )
        )

        # Extract status using the existing method
        status = outcome_extractor.extract_highest_status_reached(self.soup)

        return status

    def extract_law_implementation_date(self) -> Optional[str]:
        """
        Extract the date when regulation/directive became applicable.

        Uses the FollowupWebsiteLegislativeOutcomeExtractor to extract the
        implementation deadline/applicable date from the followup website.

        Returns:
            Date string in YYYY-MM-DD format or None if not applicable.
        """

        # Create extractor instance
        outcome_extractor = FollowupWebsiteLegislativeOutcomeExtractor(
            registration_number=(
                self.registration_number
                if hasattr(self, "registration_number")
                else None
            )
        )

        # Extract applicable date using the existing method
        date = outcome_extractor.extract_applicable_date(self.soup)

        return date

    def extract_commission_promised_new_law(self):

        # Create extractor instance
        outcome_extractor = FollowupWebsiteLegislativeOutcomeExtractor(
            registration_number=(
                self.registration_number
                if hasattr(self, "registration_number")
                else None
            )
        )

        # Extract applicable boolean using the existing method
        is_new_law = outcome_extractor.extract_proposal_commitment_stated(self.soup)

        return is_new_law

    def extract_commissions_deadlines(self):

        # Create extractor instance
        outcome_extractor = FollowupWebsiteLegislativeOutcomeExtractor(
            registration_number=(
                self.registration_number
                if hasattr(self, "registration_number")
                else None
            )
        )

        # Extract applicable boolean using the existing method
        commissions_deadlines = outcome_extractor.extract_commissions_deadlines(
            self.soup
        )

        return commissions_deadlines

    def extract_commission_rejected_initiative(self):

        # Create extractor instance
        outcome_extractor = FollowupWebsiteLegislativeOutcomeExtractor(
            registration_number=(
                self.registration_number
                if hasattr(self, "registration_number")
                else None
            )
        )

        # Extract applicable boolean using the existing method
        commissions_deadlines = outcome_extractor.extract_proposal_rejected(self.soup)

        return commissions_deadlines

    def extract_commission_rejection_reason(self):

        # Create extractor instance
        outcome_extractor = FollowupWebsiteLegislativeOutcomeExtractor(
            registration_number=(
                self.registration_number
                if hasattr(self, "registration_number")
                else None
            )
        )

        # Extract applicable boolean using the existing method
        commissions_deadlines = outcome_extractor.extract_rejection_reasoning(self.soup)

        return commissions_deadlines

    def extract_followup_latest_date(self):
        pass

    def extract_followup_most_future_date(self):
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


class FollowupWebsiteLegislativeOutcomeExtractor(LegislativeOutcomeExtractor):
    """
    Custom extractor for followup website pages.

    Overrides content extraction to handle the nested div structure
    used in followup website pages, where h2 headers and content
    are wrapped in separate <div class="ecl"> containers.
    """

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
                    # Try variations
                    section_header = soup.find(
                        "h2", string=lambda t: t and "follow-up" in t.lower()
                    )
                elif section_id == "next-steps":
                    section_header = soup.find(
                        "h2", string=lambda t: t and "next steps" in t.lower()
                    )

            if not section_header:
                continue  # Skip this section if not found

            # Get parent div of the h2
            parent = section_header.find_parent("div")
            if not parent:
                continue

            # Get the next sibling div after the parent (contains content)
            content_container = parent.find_next_sibling("div")

            if content_container:
                # Extract text until we hit another major section or end
                section_text = []

                # Get this container's text
                section_text.append(content_container.get_text(strip=False))

                # Check following sibling divs
                next_sibling = content_container.find_next_sibling("div")
                while next_sibling:
                    # Stop if we hit another h2 section (new major section)
                    if next_sibling.find("h2"):
                        # But only stop if it's one of our tracked sections or a major section
                        found_h2 = next_sibling.find("h2")
                        h2_id = found_h2.get("id", "") if found_h2 else ""

                        # Stop if it's a different major section
                        if h2_id and h2_id not in section_ids:
                            break
                        elif h2_id in section_ids:
                            break  # Hit next section we'll process separately

                    if not self._should_skip_element(next_sibling):
                        section_text.append(next_sibling.get_text(strip=False))

                    next_sibling = next_sibling.find_next_sibling("div")

                # Add section text to overall text
                if section_text:
                    all_text.extend(section_text)

        if not all_text:
            return None

        content = " ".join(all_text).lower()
        content = normalize_whitespace(content)

        return content

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
        Returns None if no deadlines are mentioned.

        Format: dict like:
        {
            "2018-05-31": "committed to come forward with a legislative proposal",
            "2026-03-31": "will communicate on the most appropriate action",
            "2024-12-31": "complete the impact assessment"
        }

        Returns:
            dict with date->phrase mapping or None if no deadlines found

        Raises:
            ValueError: If Answer section not found
        """
        try:
            answer_section = self._find_answer_section(soup)

            if not answer_section:
                raise ValueError(
                    f"Could not find Answer section for initiative {self.registration_number}"
                )

            # Comprehensive deadline patterns covering various commitment types
            deadlines_dict = {}

            # Allowed tags for text extraction
            ALLOWED_TAGS = ["li", "p", "ol", "pre"]

            # Start from answer_section and iterate through ALL following elements
            current = answer_section.find_next()

            while current:
                # Stop when we find the social media share element
                if current.find(class_="ecl-social-media-share__description"):
                    break

                # Only process allowed tags
                if current.name in ALLOWED_TAGS and not self._should_skip_element(
                    current
                ):
                    # Get text and normalize immediately
                    text = current.get_text(strip=False)
                    text_normalized = normalize_whitespace(text)
                    text_lower = text_normalized.lower()

                    # Check each pattern
                    for pattern in DEADLINE_PATTERNS:
                        # Find all matches in this element (handles multiple deadlines per element)
                        for match in re.finditer(pattern, text_lower, re.IGNORECASE):
                            deadline_text = match.group(1).strip()

                            if deadline_text:
                                deadline_cleaned = self._clean_deadline_text(
                                    deadline_text
                                )
                                # Clean and convert the deadline
                                if deadline_cleaned:
                                    deadline_date = convert_deadline_to_date(
                                        deadline_cleaned
                                    )
                                    if deadline_date:
                                        # Use the entire normalized text from the tag
                                        full_text = normalize_whitespace(
                                            text_normalized
                                        )

                                        # If we already have this date, append to existing phrase
                                        if deadline_date in deadlines_dict:
                                            # Only append if it's different content
                                            if (
                                                full_text
                                                not in deadlines_dict[deadline_date]
                                            ):
                                                deadlines_dict[
                                                    deadline_date
                                                ] += f"; {full_text}"
                                        else:
                                            deadlines_dict[deadline_date] = full_text

                # Move to next element in document order
                current = current.find_next()

            # Return None if no deadlines found, otherwise return dict
            if not deadlines_dict:
                return None

            return deadlines_dict

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
