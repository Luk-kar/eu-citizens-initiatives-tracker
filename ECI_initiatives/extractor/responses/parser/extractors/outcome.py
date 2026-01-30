"""
Extracts legislative outcome data by
classifying Commission responses, determining proposal status, and
identifying legislative actions taken.
"""

import calendar
import json
import re
from datetime import datetime
from typing import Optional

from bs4 import BeautifulSoup

from ..base.base_extractor import BaseExtractor
from .classifiers.status_matcher import LegislativeOutcomeClassifier
from ..base.date_parser import (
    parse_date_string,
    convert_deadline_to_date,
)
from ..base.text_utilities import normalize_whitespace, remove_leading_punctuation

from ..consts import (
    REJECTION_REASONING_KEYWORDS,
    NonLegislativeAction,
    DEADLINE_PATTERNS,
    APPLICABLE_DATE_PATTERNS,
    LegislativeStatus,
)


class LegislativeOutcomeExtractor(BaseExtractor):
    """Extractor for legislative outcome and proposal status data"""

    # Keywords that indicate rejection reasoning

    def __init__(self, registration_number: Optional[str] = None):
        """
        Initialize extractor

        Args:
            registration_number: ECI registration number for error messages
        """
        self.registration_number = registration_number

    def _find_answer_section(self, soup: BeautifulSoup):
        """Find the Answer section header in the HTML."""
        return soup.find("h2", id="Answer-of-the-European-Commission") or soup.find(
            "h2", id="Answer-of-the-European-Commission-and-follow-up"
        )

    def _extract_legislative_content(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Extract all text content after Answer section.
        Returns normalized lowercase string or None if section not found.
        """
        answer_section = self._find_answer_section(soup)

        if not answer_section:
            return None

        all_text = []
        for sibling in answer_section.find_next_siblings():
            if not self._should_skip_element(sibling):
                all_text.append(sibling.get_text(strip=False))

        content = " ".join(all_text).lower()
        content = normalize_whitespace(content)

        return content

    def _should_skip_element(self, element) -> bool:
        """Check if element should be skipped during extraction."""
        if element.name == "h2":
            return True
        if (
            element.name == "div"
            and element.get("class")
            and "ecl-file" in element.get("class")
        ):
            return True
        return False

    def _get_classifier(self, soup: BeautifulSoup) -> LegislativeOutcomeClassifier:
        """
        Create and return a LegislativeOutcomeClassifier for the given HTML.

        Args:
            soup: BeautifulSoup object containing ECI response HTML

        Returns:
            LegislativeOutcomeClassifier instance

        Raises:
            ValueError: If Answer section is not found or is empty
        """
        content = self._extract_legislative_content(soup)
        if not content:
            raise ValueError(
                "Could not extract legislative content for "
                f"initiative {self.registration_number}.\n"
                f"Answer section may be missing or empty."
            )
        return LegislativeOutcomeClassifier(content)

    def extract_highest_status_reached(self, soup: BeautifulSoup) -> str:
        """
        Extract the highest status reached by the initiative.

        Status hierarchy (highest to lowest):
        1. applicable - Law Active
        2. adopted - Law Approved
        3. committed - Law Promised
        4. assessment_pending - Being Studied
        5. roadmap_development - Action Plan Created
        6. rejected_already_covered - Rejected - Already Covered
        7. rejected_with_actions - Rejected - Alternative Actions
        8. rejected - Rejected
        9. non_legislative_action - Policy Changes Only
        10. proposal_pending_adoption - Proposals Under Review

        Args:
            soup: BeautifulSoup object containing ECI response HTML

        Returns:
            Citizen-friendly status name (e.g., "Law Active")

        Raises:
            ValueError: If error occurs during extraction or no status can be determined
        """
        try:
            matcher = self._get_classifier(soup)
            technical_status = matcher.extract_technical_status()
            return matcher.translate_to_citizen_friendly(technical_status)

        except ValueError as e:
            if "No known status patterns matched" in str(e):
                content_preview = self._extract_legislative_content(soup)

                raise ValueError(
                    "Could not determine legislative status for initiative:"
                    f"\n{self.registration_number}\n"
                    f"No known status patterns matched. Content preview:"
                    f"\n{content_preview}\n"
                ) from e
            raise
        except Exception as e:
            raise ValueError(
                f"Error extracting highest status reached for {self.registration_number}: {str(e)}"
            ) from e

    def extract_proposal_commitment_stated(self, soup: BeautifulSoup) -> Optional[bool]:
        """
        Extract whether Commission explicitly committed to propose legislation.

        Returns:
            True if commitment found, False otherwise
        """
        try:
            matcher = self._get_classifier(soup)
            return matcher.check_committed()

        except Exception as e:
            raise ValueError(
                "Error extracting proposal commitment status for "
                f"{self.registration_number}: {str(e)}"
            ) from e

    def extract_proposal_rejected(self, soup: BeautifulSoup) -> Optional[bool]:
        """
        Extract whether Commission explicitly rejected making a legislative proposal.

        Returns:
            True if rejection stated, False otherwise
        """
        try:
            matcher = self._get_classifier(soup)
            rejection_type = matcher.check_rejection_type()
            return bool(rejection_type)

        except Exception as e:
            raise ValueError(
                "Error extracting proposal rejection status for "
                f"{self.registration_number}: {str(e)}"
            ) from e

    def _extract_text_with_keyword_filter(
        self, sibling, keywords: list
    ) -> Optional[str]:
        """
        Extract text from element if it contains any of the keywords.

        Args:
            sibling: BeautifulSoup element to extract from
            keywords: List of keywords to filter by

        Returns:
            Extracted text or None if no keyword match
        """
        if sibling.name not in ["p", "li", "ul", "ol"]:
            return None

        if sibling.name in ["ul", "ol"]:
            list_items = sibling.find_all("li")
            matching_texts = []
            for li in list_items:
                text = li.get_text(strip=True)
                if any(keyword in text.lower() for keyword in keywords):
                    matching_texts.append(text)
            return " ".join(matching_texts) if matching_texts else None
        else:
            text = sibling.get_text(strip=True)
            if any(keyword in text.lower() for keyword in keywords):
                return text
            return None

    def _extract_mixed_response_reasoning(self, answer_section) -> str:
        """
        Extract reasoning for mixed response (both commitment and rejection).
        Finds all text mentioning 'legislative proposal'.

        Args:
            answer_section: BeautifulSoup element of Answer section

        Returns:
            Combined text of all relevant paragraphs

        Raises:
            ValueError: If no relevant text found
        """
        legislative_proposal_paragraphs = []

        for sibling in answer_section.find_next_siblings():
            if self._should_skip_element(sibling):
                if sibling.name == "h2":
                    break
                continue

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
            answer_section: BeautifulSoup element of Answer section

        Returns:
            Combined text of all relevant paragraphs or fallback message
        """
        rejection_sentences = []

        for sibling in answer_section.find_next_siblings():
            if self._should_skip_element(sibling):
                if sibling.name == "h2":
                    break
                continue

            extracted_text = self._extract_text_with_keyword_filter(
                sibling, REJECTION_REASONING_KEYWORDS
            )
            if extracted_text:
                rejection_sentences.append(extracted_text)

        if rejection_sentences:
            return " ".join(rejection_sentences)

        return "The Commission decided not to make a legislative proposal."

    def extract_rejection_reasoning(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Extract the reasoning provided by Commission for rejecting legislative proposal.
        Returns full text explanation or None if not rejected.
        For mixed responses (both commitment and rejection), extracts all relevant context.

        Returns:
            String containing rejection reasoning, or None if no rejection found

        Raises:
            ValueError: If Answer section is not found or is empty
        """
        try:
            matcher = self._get_classifier(soup)
            rejection_type = matcher.check_rejection_type()

            if not rejection_type:
                return None

            answer_section = self._find_answer_section(soup)
            if not answer_section:
                return None

            has_commitment = matcher.check_committed()

            if has_commitment:
                return self._extract_mixed_response_reasoning(answer_section)
            else:
                return self._extract_pure_rejection_reasoning(answer_section)

        except Exception as e:
            raise ValueError(
                f"Error extracting rejection reasoning for {self.registration_number}: {str(e)}"
            ) from e

    def extract_applicable_date(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Extract the date when regulation/directive became applicable (implementation deadline).
        Format: YYYY-MM-DD

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

            # Search through all siblings after Answer section
            for sibling in answer_section.find_next_siblings():
                if self._should_skip_element(sibling):
                    continue

                text = sibling.get_text(strip=False)

                # Check for "immediately" case first
                if "became applicable immediately" in text.lower():
                    # Try to find entry into force date nearby
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
                        if match.groups():  # Has captured group
                            date_str = match.group(1).strip()
                            parsed_date = parse_date_string(date_str)
                            if parsed_date:
                                return parsed_date

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

            # Search through all siblings after Answer section
            for sibling in answer_section.find_next_siblings():

                if self._should_skip_element(sibling):
                    if sibling.name == "h2":
                        break
                    continue

                text = sibling.get_text(strip=False)
                text_lower = text.lower()

                # Check each pattern
                for pattern in DEADLINE_PATTERNS:
                    # Find all matches in this element (handles multiple deadlines per element)
                    for match in re.finditer(pattern, text_lower, re.IGNORECASE):
                        deadline_text = match.group(1).strip()

                        if deadline_text:

                            # Clean and convert the deadline
                            deadline_cleaned = self._clean_deadline_text(deadline_text)
                            if deadline_cleaned:
                                deadline_date = convert_deadline_to_date(
                                    deadline_cleaned
                                )
                                if deadline_date:
                                    # Extract the complete sentence containing this deadline
                                    sentence = self._extract_complete_sentence(
                                        text, match.start()
                                    )

                                    if sentence:
                                        # Clean up whitespace
                                        sentence = normalize_whitespace(sentence)

                                        # If we already have this date, append to existing phrase
                                        if deadline_date in deadlines_dict:
                                            # Only append if it's different content
                                            if (
                                                sentence
                                                not in deadlines_dict[deadline_date]
                                            ):
                                                deadlines_dict[
                                                    deadline_date
                                                ] += f"; {sentence}"
                                        else:
                                            deadlines_dict[deadline_date] = sentence

            # Return None if no deadlines found, otherwise return JSON string
            if not deadlines_dict:
                return None

            return deadlines_dict

        except Exception as e:
            raise ValueError(
                f"Error extracting commission deadlines for {self.registration_number}: {str(e)}"
            ) from e

    def _extract_complete_sentence(
        self, text: str, match_position: int
    ) -> Optional[str]:
        """
        Extract the complete sentence containing the deadline match.

        Args:
            text: Full text to search within
            match_position: Position of the regex match in the text

        Returns:
            Complete sentence or None if extraction fails
        """
        # Find the start of the sentence (look backwards for sentence boundary)
        sentence_start = 0

        # Look backwards from match position for sentence start markers
        for i in range(match_position - 1, -1, -1):
            char = text[i]

            # Sentence boundaries: period, question mark, exclamation, or start of text
            if char in ".!?":
                # Make sure it's not an abbreviation (check for space after)
                if i + 1 < len(text) and text[i + 1].isspace():
                    sentence_start = i + 1
                    break
            # Also break at bullet points or list markers
            elif char == "•" or (char == "\n" and i > 0 and text[i - 1] == "\n"):
                sentence_start = i + 1
                break

        # Find the end of the sentence (look forwards for sentence boundary)
        sentence_end = len(text)

        # Look forwards from match position for sentence end markers
        for i in range(match_position, len(text)):
            char = text[i]

            # Sentence boundaries: period, question mark, exclamation
            if char in ".!?":
                # Include the punctuation and stop
                sentence_end = i + 1
                break
            # Also break at newlines indicating paragraph breaks
            elif char == "\n" and i + 1 < len(text) and text[i + 1] == "\n":
                sentence_end = i
                break

        # Extract and clean the sentence
        sentence = text[sentence_start:sentence_end].strip()

        # Remove leading punctuation or whitespace
        sentence = remove_leading_punctuation(sentence)

        return sentence if sentence else None

    def _clean_deadline_text(self, deadline: str) -> Optional[str]:
        """
        Clean deadline text by removing trailing words that aren't part of the date.

        Args:
            deadline: Raw deadline text

        Returns:
            Cleaned deadline text or None if invalid
        """
        # Remove common trailing phrases
        deadline = re.sub(
            r"\s+(?:to|for|in order to|with|amongst|among).*$",
            "",
            deadline,
            flags=re.IGNORECASE,
        )

        # Remove trailing commas, semicolons, periods
        deadline = deadline.rstrip(".,;")

        # Validate it contains a year (4 digits)
        if not re.search(r"\d{4}", deadline):
            return None

        return deadline.strip()

    # TODO: need a refactor
    def extract_legislative_action(self, soup: BeautifulSoup) -> Optional[dict]:
        """
        Extract LEGISLATIVE actions - proposals, adoptions, laws, regulations, directives.
        Excludes: rejection statements, enforcement activities, policy actions.
        Returns JSON string with list of legislative actions or None

        Each action contains:
        - type: Type of action (e.g., "Regulation Proposal", "Directive Revision", "Tariff Codes Creation")
        - description: Brief description of the action
        - status: Status of action ("proposed", "adopted", "in_vacatio_legis", "withdrawn", "planned")
        - date: Date in YYYY-MM-DD format (when applicable)
        - document_url: URL to official document (optional)
        """

        try:
            # Check if proposal was rejected
            matcher = self._get_classifier(soup)
            rejection_type = matcher.check_rejection_type()

            # If rejected with no commitment, return None
            if rejection_type and not matcher.check_committed():
                return None

            # If only commitment stated but no actual proposals, return None
            if matcher.check_committed() and not (
                matcher.check_adopted() or matcher.check_applicable()
            ):
                # Check if there are actual proposals mentioned in follow-up section
                follow_up_section = soup.find("h2", id="Follow-up")
                if not follow_up_section:
                    return None

            # Extract all legislative actions
            actions = []

            # Find Answer and Follow-up sections
            answer_section = self._find_answer_section(soup)
            follow_up_section = soup.find("h2", id="Follow-up") or soup.find(
                "h2", string=re.compile(r"Follow[- ]up", re.IGNORECASE)
            )
            updates_section = soup.find(
                "h2", id="Updates-on-the-Commissions-proposals"
            ) or soup.find("h2", string=re.compile(r"Updates.*proposal", re.IGNORECASE))

            # Section priorities: Updates > Follow-up > Answer
            search_sections = []
            if updates_section:
                search_sections.append(updates_section)
            if follow_up_section:
                search_sections.append(follow_up_section)
            if answer_section:
                search_sections.append(answer_section)

            # Extract actions from each section
            for section in search_sections:
                section_actions = self._extract_actions_from_section(section)
                actions.extend(section_actions)

            # If no actions found, return None
            if not actions:
                return None

            # Remove duplicates (same type, description, and date)
            unique_actions = []
            seen = set()
            for action in actions:
                key = (
                    action.get("type", ""),
                    action.get("description", ""),
                    action.get("date", ""),
                )
                if key not in seen:
                    seen.add(key)
                    unique_actions.append(action)

            return unique_actions

        except Exception as e:
            raise ValueError(
                f"Error extracting legislative action for {self.registration_number}: {str(e)}"
            ) from e

    def _extract_actions_from_section(self, section) -> list:
        """
        Extract legislative actions from a specific section

        Args:
            section: BeautifulSoup element of the section
            section_type: Type of section ('answer', 'follow_up', 'updates')

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
                        "status_obj": status,  # Store the Status object
                    }
                )

        # Iterate through siblings after section header
        for sibling in section.find_next_siblings():
            # Stop at next h2 section
            if sibling.name == "h2":
                break

            # Process paragraphs and standalone list items
            if sibling.name in ["p", "li"]:
                self._process_element_for_legislative_action(
                    sibling, action_patterns, actions
                )

            elif sibling.name in ["ul", "ol"]:
                # Process each list item individually
                for li in sibling.find_all("li", recursive=False):
                    self._process_element_for_legislative_action(
                        li, action_patterns, actions
                    )

        return actions

    def _process_element_for_legislative_action(
        self, element, action_patterns: list, actions: list
    ):
        """Process a single HTML element (p or li) for legislative actions"""

        # Get text with newlines separating each tag
        text = element.get_text(separator=" ", strip=True)

        # NORMALIZE WHITESPACE: Replace multiple whitespace (including newlines) with single space
        text = normalize_whitespace(text)

        text_lower = text.lower()

        # Find ALL matching patterns, then pick the most specific status
        matches = []
        for pattern_info in action_patterns:
            if re.search(
                pattern_info["pattern"], text_lower, re.IGNORECASE | re.DOTALL
            ):
                matches.append(pattern_info)

        if not matches:
            return

        # Pick the pattern with highest priority status (lower priority number = higher priority)
        best_match = min(matches, key=lambda p: p["status_obj"].priority)

        action = self._parse_legislative_action(element, text, best_match)
        if action:
            actions.append(action)

    def _parse_legislative_action(
        self, element, text: str, pattern_info: dict
    ) -> Optional[dict]:
        """
        Parse a legislative action from text element.

        Args:
            element: BeautifulSoup element containing the action
            text: Text content
            pattern_info: Pattern information dictionary with status_obj

        Returns:
            Action dictionary or None
        """
        MONTH_NAMES_PATTERN = "|".join(calendar.month_name[1:])

        # Extract dates from text
        date_patterns = [
            rf"(\d{{1,2}}\s+(?:{MONTH_NAMES_PATTERN})\s+\d{{4}})",  # 12 January 2023
            rf"(?:in|by|from)\s+((?:{MONTH_NAMES_PATTERN})\s+\d{{4}})",  # in May 2024
            r"(\d{1,2}/\d{1,2}/\d{4})",  # 15/03/2022
            r"(\d{4}-\d{2}-\d{2})",  # 2023-01-12
            r"(?:by|in|from)\s+(\d{{4}})",  # in 2024
            r"(?:by|in|from)\s+(?:end\s+of\s+)?(\d{{4}})",  # by end of 2024
        ]

        found_date = None
        status_obj = pattern_info["status_obj"]

        text_lower = text.lower()

        # Get keywords from the Status object
        keywords = status_obj.keywords

        # Try to find date in context of status keyword
        for keyword in keywords:

            if keyword not in text_lower:
                continue

            # Find the position of the keyword
            keyword_pos = text_lower.find(keyword)

            # Extract text starting from keyword position
            text_from_keyword = text[keyword_pos:]

            # Find the end of the sentence/clause (., ; or end of text)
            clause_end = len(text_from_keyword)

            for delimiter in [". ", "; "]:
                pos = text_from_keyword.find(delimiter)
                if pos != -1 and pos < clause_end:
                    clause_end = pos

            # Extract the clause containing the keyword
            clause = text_from_keyword[: clause_end + 1]

            # Try to find a date in this clause
            for date_pattern in date_patterns:
                match = re.search(date_pattern, clause, re.IGNORECASE)
                if match:
                    date_str = match.group(1)
                    parsed = parse_date_string(date_str)
                    if parsed:
                        found_date = parsed
                        break

            # If we found a date with this keyword, stop searching
            if found_date:
                break

        # Fallback: if no date found near status keyword, try the whole text
        if not found_date:
            for date_pattern in date_patterns:
                match = re.search(date_pattern, text, re.IGNORECASE)
                if match:
                    date_str = match.group(1)
                    parsed = parse_date_string(date_str)
                    if parsed:
                        found_date = parsed
                        break

        # Extract action type and description
        action_type = self._extract_action_type(text)
        description = normalize_whitespace(text)

        # Get ALL document URLs
        doc_urls = []
        links = element.find_all("a", href=True)
        for link in links:
            href = link.get("href", "")
            if "eur-lex" in href or "europa.eu" in href:
                doc_urls.append(href)

        action = {
            "type": action_type,
            "description": description,
            "status": status_obj.name,  # Use the status name from Status object
        }

        if found_date:
            action["date"] = found_date

        if doc_urls:
            action["document_urls"] = doc_urls

        return action

    def _extract_action_type(self, text: str) -> str:
        """Extract the type of legislative action"""
        text_lower = text.lower()

        # Specific type patterns
        if "tariff codes" in text_lower or "tariff code" in text_lower:
            return "Tariff Codes Creation"

        elif "standards" in text_lower and (
            "minimum" in text_lower or "hygiene" in text_lower
        ):
            return "Standards Adoption"

        elif (
            "revision" in text_lower
            or "revised" in text_lower
            or "recast" in text_lower
        ):
            if "directive" in text_lower:
                return "Directive Revision"
            elif "regulation" in text_lower:
                return "Regulation Revision"
            else:
                return "Legislative Revision"

        elif "amendment" in text_lower:
            return "Amendment"

        elif "proposal" in text_lower or "proposed" in text_lower:
            if "regulation" in text_lower:
                return "Regulation Proposal"
            elif "directive" in text_lower:
                return "Directive Proposal"
            elif "law" in text_lower:
                return "Law Proposal"
            else:
                return "Legislative Proposal"

        elif "adopted" in text_lower or "adoption" in text_lower:
            if "regulation" in text_lower:
                return "Regulation Adoption"
            elif "directive" in text_lower:
                return "Directive Adoption"
            elif "law" in text_lower:
                return "Law Adoption"
            else:
                return "Legislative Adoption"

        elif "entered into force" in text_lower or "became applicable" in text_lower:
            return "Law Entered Into Force"

        elif "withdrawn" in text_lower or "withdraw" in text_lower:
            if "regulation" in text_lower:
                return "Regulation Withdrawal"
            elif "directive" in text_lower:
                return "Directive Withdrawal"
            else:
                return "Proposal Withdrawal"
        else:
            return "Legislative Action"

    def extract_non_legislative_action(self, soup: BeautifulSoup) -> Optional[dict]:
        """
        Extract non-legislative actions as JSON array
        Each item contains: type, description, date
        Returns dict or None
        """
        try:

            # Find Answer and Follow-up sections
            answer_section = self._find_answer_section(soup)
            follow_up_section = soup.find("h2", id="Follow-up") or soup.find(
                "h2", string=re.compile(r"Follow[- ]up", re.IGNORECASE)
            )

            # Section priorities: Follow-up > Answer
            search_sections = []
            if follow_up_section:
                search_sections.append(follow_up_section)
            if answer_section:
                search_sections.append(answer_section)

            if not search_sections:
                return None

            # Extract actions from each section
            actions = []
            for section in search_sections:
                section_actions = self._extract_non_legislative_actions_from_section(
                    section
                )
                actions.extend(section_actions)

            # If no actions found, return None
            if not actions:
                return None

            # Remove duplicates (same type, description, and date)
            unique_actions = []
            seen = set()
            for action in actions:
                key = (
                    action.get("type", ""),
                    action.get("description", ""),
                    action.get("date", ""),
                )
                if key not in seen:
                    seen.add(key)
                    unique_actions.append(action)

            return unique_actions

        except Exception as e:
            raise ValueError(
                f"Error extracting non-legislative action for {self.registration_number}: {str(e)}"
            ) from e

    def _extract_non_legislative_actions_from_section(self, section) -> list:
        """
        Extract non-legislative actions from a specific section

        Args:
            section: BeautifulSoup element of the section

        Returns:
            List of action dictionaries
        """
        actions = []

        # Iterate through siblings after section header
        current = section.next_sibling

        while current:  # TODO refacor
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

    def _process_element_for_non_legislative_action(self, element, actions: list):
        """Process a single HTML element (p or li) for non-legislative actions"""

        # Get text with normalized whitespace
        text = element.get_text(separator=" ", strip=True)
        text = normalize_whitespace(text)
        text_lower = text.lower()

        # Skip if empty or too short
        if len(text) < 20:
            return

        # Section headers end with ':' and are short (< 100 chars)
        if text.endswith(":") and len(text) < 100:
            return

        # Skip legislative keywords (these belong to legislative actions)
        legislative_keywords = [
            r"\bentered into force\b",
            r"\bbecame applicable\b",
            r"\bwithdrawal\b",
            r"\bdecided not to submit a legislative proposal\b",
            r"\bcome forward with a legislative proposal\b",
            r"\btable a legislative proposal\b",
            r"\bno new legislation\b",
            r"\bcame into force on\b",
            r"\bamendment to the directive\b",
            r"\bamendment to the regulation\b",
            r"\bamending directive\b",
            r"\bamending regulation\b",
            r"\brevision of legislation\b",
            r"\blabelling requirements\b",
            r"\bmandatory labelling\b",
            r"\bsets out plans for a legislative proposal\b",
        ]

        header_sections = [
            "transparency and benchmarking:",
            "Implementation and review of existing EU legislation:",
        ]

        # If contains legislative keywords, skip (unless it's about enforcement)
        if any(re.search(keyword, text_lower) for keyword in legislative_keywords):
            return

        # other trouble phrases
        if any(keyword in text_lower for keyword in header_sections):
            return

        # Classify the text using NonLegislativeAction
        action_type = NonLegislativeAction.classify_text(text)

        # If no pattern matched, skip
        if not action_type:
            return

        # Parse the action
        action = self._parse_non_legislative_action(text, action_type)
        if action:
            actions.append(action)

    def _parse_non_legislative_action(
        self, text: str, pattern_info: dict
    ) -> Optional[dict]:
        """
        Parse a non-legislative action from text element.

        Args:
            text: Text content
            pattern_info: Pattern information dictionary

        Returns:
            Action dictionary or None
        """

        MONTH_NAMES_PATTERN = "|".join(calendar.month_name[1:])

        # Extract dates from text
        date_patterns = [
            rf"(\d{{1,2}}\s+(?:{MONTH_NAMES_PATTERN})\s+\d{{4}})",  # 12 January 2023
            rf"(?:in|by|from)\s+((?:{MONTH_NAMES_PATTERN})\s+\d{{4}})",  # in May 2024
            r"(\d{1,2}/\d{1,2}/\d{4})",  # 15/03/2022
            r"(\d{4}-\d{2}-\d{2})",  # 2023-01-12
            r"(?:by|in|from)\s+(\d{{4}})",  # in 2024
            r"(?:by|in|from)\s+(?:end\s+of\s+)?(\d{{4}})",  # by end of 2024
        ]

        found_date = None

        # Try to find date in text
        for date_pattern in date_patterns:
            match = re.search(date_pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                parsed = parse_date_string(date_str)
                if parsed:
                    found_date = parsed
                    break

        # Extract clean description (first sentence or up to 300 chars)
        description = normalize_whitespace(text)

        # Build action dictionary
        action = {"type": pattern_info.name, "description": description}

        if found_date:
            action["date"] = found_date

        return action
