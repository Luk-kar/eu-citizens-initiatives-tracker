"""
Extracts follow-up activity information including
roadmaps, workshops, partnership programs, and
court case references from post-response sections.
"""

import calendar
import copy
from datetime import date, datetime
import re
import json
from typing import Any, Optional, Tuple, Union, Dict, List

from bs4 import BeautifulSoup, Tag, NavigableString

from ..base.base_extractor import BaseExtractor
from ..base.date_parser import parse_any_date_format, convert_deadline_to_date


class FollowUpActivityExtractor(BaseExtractor):
    """Extracts follow-up activities data"""

    def _extract_text_with_links(self, element: Tag, separator: str = " ") -> str:
        """
        Extract text from element while preserving link URLs.

        Links are formatted as: "link text (url)"

        Args:
            element: BeautifulSoup Tag to extract text from
            separator: String to use between text parts (default: space)

        Returns:
            Extracted text with links preserved in format "text (url)"

        Example:
            >>> html = '<p>See <a href="https://example.com">press release</a></p>'
            >>> text = self._extract_text_with_links(soup.find('p'))
            >>> print(text)
            'See press release (https://example.com)'
        """
        parts = []

        for child in element.children:
            if isinstance(child, NavigableString):
                # Text node
                text = str(child).strip()
                if text:
                    parts.append(text)
            else:
                # Tag
                if child.name == "a":
                    # Link tag: extract text and href
                    link_text = child.get_text(strip=True)
                    href = child.get("href", "")
                    if link_text and href:
                        parts.append(f"{link_text} ({href})")
                    elif link_text:
                        parts.append(link_text)
                elif child.name in ["strong", "em", "span", "b", "i"]:
                    # Inline formatting tags: just get text
                    text = child.get_text(strip=True)
                    if text:
                        parts.append(text)
                else:
                    # Other tags (br, nested elements, etc): recursively process
                    text = child.get_text(separator=separator, strip=True)
                    if text:
                        parts.append(text)

        return separator.join(parts)

    def _find_followup_section(self, soup: BeautifulSoup) -> Optional[Tuple[Tag, str]]:
        """
        Find Follow-up section and return both the tag and section type.

        This private helper method encapsulates the logic for locating the Follow-up
        section in either h2 or h4 format.

        Args:
            soup: BeautifulSoup parsed HTML document

        Returns:
            Tuple of (section_tag, section_marker) where:
            - section_tag: BeautifulSoup Tag object for the Follow-up heading
            - section_marker: String "h2" or "h4" indicating the heading type
            Returns None if no Follow-up section is found
        """
        # Primary pattern: <h2 id="Follow-up">
        followup_section = soup.find(
            "h2", id=["Follow-up", "Updates-on-the-Commissions-proposals"]
        )
        if followup_section:
            return (followup_section, "h2")

        # Fallback pattern: <h4>Follow-up</h4> (handles whitespace and case variations)
        followup_section = soup.find(
            "h4", string=re.compile(r"^\s*follow-up\s*$", re.IGNORECASE)
        )
        if followup_section:
            return (followup_section, "h4")

        # No Follow-up section found
        return None

    def extract_has_followup_section(self, soup: BeautifulSoup) -> Optional[bool]:
        """
        Check if page includes follow-up activities section.

        Detects Follow-up sections in two formats:
        1. <h2 id="Follow-up"> - standard format
        2. <h4>Follow-up</h4> - subsection format (handles whitespace)

        Args:
            soup: BeautifulSoup parsed HTML document

        Returns:
            True if Follow-up section exists, False otherwise

        Raises:
            ValueError: If critical error occurs during detection
        """
        try:
            result = self._find_followup_section(soup)
            return result is not None

        except Exception as e:
            raise ValueError(
                f"Error checking followup section for {self.registration_number}: {str(e)}"
            ) from e

    def extract_has_partnership_programs(self, soup: BeautifulSoup) -> Optional[bool]:
        """
        Check if initiative has partnership programs mentioned in follow-up or response sections.

        Searches in multiple relevant sections:
        - "Follow-up" (primary section for follow-up information)
        - "Answer of the European Commission" (alternative section name)
        - "Commission Response" (alternative section name)
        - "European Commission's response" (alternative section name)

        Args:
            soup: BeautifulSoup parsed HTML document

        Returns:
            True if partnership programs are mentioned, False otherwise, None on error
        """
        try:
            # Define section names to search (in priority order)
            section_names = [
                "Follow-up",
                "Answer of the European Commission",
                "Commission Response",
                "Commission's response",
                "European Commission's response",
            ]

            # Try to find any of the relevant sections
            followup_section = None
            section_marker = None

            for section_name in section_names:

                # Try h2 first - use get_text() because headers may contain nested tags
                for h2 in soup.find_all("h2"):

                    if section_name in h2.get_text(strip=True):
                        followup_section = h2
                        section_marker = "h2"
                        break

                if followup_section:
                    break

                # Try h4 if h2 not found
                for h4 in soup.find_all("h4"):

                    if section_name in h4.get_text(strip=True):
                        followup_section = h4
                        section_marker = "h4"
                        break

                if followup_section:
                    break

            # If no section found, return False
            if not followup_section:
                return False

            # Extract all text from the found section
            followup_text = followup_section.find_next_sibling()
            full_text = ""

            while followup_text and followup_text.name != "h2":
                if section_marker == "h4" and followup_text.name == "h4":
                    break
                if followup_text.name:
                    full_text += followup_text.get_text(
                        separator=" ", strip=True
                    ).lower()
                followup_text = followup_text.find_next_sibling()

            # Check for partnership-related keywords
            partnership_keywords = [
                "partnership program",
                "partnership plans",
                "partnership programmes",
                "public-public partnership",
                "public-public partnerships",
                "european partnership for",
                "partnership between",
                "partnerships between",
                "support to partnerships",
                "cooperation programme",
                "collaboration programme",
                "joint programme",
                "formal partnership",
                "established partnership",
                "international partners",
            ]

            for keyword in partnership_keywords:
                if keyword in full_text:
                    return True

            return False

        except Exception as e:
            raise ValueError(
                f"Error checking partnership programs for {self.registration_number}: {str(e)}"
            ) from e

    def extract_has_roadmap(self, soup: BeautifulSoup) -> Optional[bool]:
        """
        Check if initiative has a roadmap mentioned in follow-up.

        Looks for keywords like "roadmap", "roadmap to phase out", etc. in the Follow-up section.

        Args:
            soup: BeautifulSoup parsed HTML document

        Returns:
            True if roadmap is mentioned, False otherwise, None on error

        Raises:
            ValueError: If critical error occurs during detection
        """
        try:
            # Use shared lookup method to find Follow-up section
            result = self._find_followup_section(soup)

            if not result:
                return False

            followup_section, section_marker = result

            # Extract all text from Follow-up section
            followup_text = followup_section.find_next_sibling()
            full_text = ""

            while followup_text and followup_text.name != "h2":
                if section_marker == "h4" and followup_text.name == "h4":
                    break

                if followup_text.name:
                    full_text += followup_text.get_text(
                        separator=" ", strip=True
                    ).lower()

                followup_text = followup_text.find_next_sibling()

            # Check for roadmap-related keywords
            roadmap_keywords = ["roadmap", "road map", "roadmaps"]

            for keyword in roadmap_keywords:
                if keyword in full_text:
                    return True

            return False

        except Exception as e:
            raise ValueError(
                f"Error checking roadmap for {self.registration_number}: {str(e)}"
            ) from e

    def extract_has_workshop(self, soup: BeautifulSoup) -> Optional[bool]:
        """
        Check if initiative has workshop activities mentioned in follow-up.

        Looks for keywords like "workshop", "conference", "stakeholder meeting", etc.
        in the Follow-up section.

        Args:
            soup: BeautifulSoup parsed HTML document

        Returns:
            True if workshop activities are mentioned, False otherwise, None on error

        Raises:
            ValueError: If critical error occurs during detection
        """
        try:
            # Use shared lookup method to find Follow-up section
            result = self._find_followup_section(soup)

            if not result:
                return False

            followup_section, section_marker = result

            # Extract all text from Follow-up section
            followup_text = followup_section.find_next_sibling()
            full_text = ""

            while followup_text and followup_text.name != "h2":
                if section_marker == "h4" and followup_text.name == "h4":
                    break

                if followup_text.name:
                    full_text += followup_text.get_text(
                        separator=" ", strip=True
                    ).lower()

                followup_text = followup_text.find_next_sibling()

            # Check for workshop-related keywords
            workshop_keywords = [
                # Workshops
                "workshop",
                "workshops",
                # Conferences
                "conference",
                "conferences",
                # Scientific/academic engagement events
                "scientific conference",
                "scientific debate",
                # Stakeholder engagement events
                "stakeholder meeting",
                "stakeholder meetings",
                "stakeholder conference",
                "stakeholder debate",
                # Organized/planned events (suggests intentional activity)
                "organised workshop",
                "organized workshop",
                "organised conference",
                "organized conference",
                # Series/multiple events
                "series of workshops",
                "series of conferences",
                # Other formal engagement formats
                "roundtable",
                "symposium",
                "seminar",
                "seminars",
            ]

            for keyword in workshop_keywords:
                if keyword in full_text:
                    return True

            return False

        except Exception as e:
            raise ValueError(
                f"Error checking workshop for {self.registration_number}: {str(e)}"
            ) from e

    def extract_court_cases_referenced(self, soup: BeautifulSoup) -> Optional[dict]:
        """Extract Court of Justice case numbers categorized by court type

        Returns JSON with structure:
        {
            "general_court": ["T-655/20", "T-656/20"],
            "court_of_justice": ["C-26/23"],
            "ombudsman_decisions": ["78/182"]
        }

        Returns None if no court cases are found.
        """
        try:
            # Get all text content from the page
            text = soup.get_text()

            # Regex patterns for each court type
            general_court_pattern = r"\b[T][-–]\d{2,6}/\d{2}\b"
            court_of_justice_pattern = r"\b[C][-–]\d{2,6}/\d{2}\b"
            ombudsman_pattern = r"\b\d{2,4}/\d{3}\b"

            # Find all matches for each type
            general_court_matches = re.findall(general_court_pattern, text)
            court_of_justice_matches = re.findall(court_of_justice_pattern, text)
            ombudsman_matches = re.findall(ombudsman_pattern, text)

            # Remove duplicates while preserving order
            def deduplicate(matches: list[str]) -> list[str]:
                seen = set()
                result = []
                for match in matches:
                    if match not in seen:
                        result.append(match)
                        seen.add(match)
                return result

            general_court = deduplicate(general_court_matches)
            court_of_justice = deduplicate(court_of_justice_matches)
            ombudsman = deduplicate(ombudsman_matches)

            # Return None if no cases found
            if not (general_court or court_of_justice or ombudsman):
                return None

            # Build result dictionary with only non-empty categories
            result = {}
            if general_court:
                result["general_court"] = general_court
            if court_of_justice:
                result["court_of_justice"] = court_of_justice
            if ombudsman:
                result["ombudsman_decisions"] = ombudsman

            return result

        except Exception as e:
            raise ValueError(
                f"Error extracting court cases for {self.registration_number}: {str(e)}"
            ) from e

    def _extract_dates_from_followup_section(
        self, soup: BeautifulSoup
    ) -> Optional[list[str]]:
        """
        Extract all date strings from the Follow-up section.

        This private helper method finds all potential date strings in common formats
        within the Follow-up section and returns them as a list for further processing.

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
            soup: BeautifulSoup parsed HTML document

        Returns:
            List of date strings found in the Follow-up section, or None if no
            Follow-up section exists. Returns empty list if section exists but
            no dates are found.

        Raises:
            ValueError: If critical error occurs during extraction
        """
        try:
            # Use shared lookup method to find Follow-up section
            result = self._find_followup_section(soup)

            if not result:
                # No Follow-up section exists
                return None

            followup_section, section_marker = result

            # Extract all text from Follow-up section
            followup_text = followup_section.find_next_sibling()
            full_text = ""

            while followup_text and followup_text.name != "h2":
                if section_marker == "h4" and followup_text.name == "h4":
                    break

                if followup_text.name:
                    full_text += followup_text.get_text(separator=" ", strip=True) + " "

                followup_text = followup_text.find_next_sibling()

            # Regex pattern to find all potential dates
            # Matches patterns like: "27 March 2021", "March 2021", "27/03/2021", etc.
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
                f"Error extracting dates from followup section for {self.registration_number}: {str(e)}"
            ) from e

    def _get_today_date(self) -> date:
        """Return today's date."""

        return datetime.now().date()

    def extract_followup_latest_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract most recent date from follow-up section that is not later than today.

        Finds the most recent date in the Follow-up section that does not exceed
        the current date, filtering out any future-dated entries.

        Args:
            soup: BeautifulSoup parsed HTML document

        Returns:
            Latest date found in YYYY-MM-DD format that is <= today's date.
            Returns None if no valid dates are found, no dates exist in the Follow-up
            section, or if the Follow-up section doesn't exist.

        Raises:
            ValueError: If critical error occurs during extraction
        """
        try:

            # Use shared helper to extract all dates from Follow-up section
            date_matches = self._extract_dates_from_followup_section(soup)

            if not date_matches:
                return None

            # Parse all found dates and keep track of valid ones
            parsed_dates = []

            for date_str in date_matches:
                parsed = parse_any_date_format(date_str)
                if parsed:
                    parsed_dates.append(parsed)

            if not parsed_dates:
                return None

            # Get current date
            today = self._get_today_date()

            # Filter dates to only include those not later than today
            valid_dates = []
            for date_str in parsed_dates:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
                if date_obj <= today:
                    valid_dates.append(date_str)

            if not valid_dates:
                return None

            # Sort dates and return the latest valid date
            valid_dates.sort()
            return valid_dates[-1]

        except Exception as e:
            raise ValueError(
                f"Error extracting latest update date for {self.registration_number}: {str(e)}"
            ) from e

    def extract_followup_most_future_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract most recent date from follow-up section.


        Searches the Follow-up section for any date strings in common formats
        and returns the most recent (latest) date found.


        Date formats supported:
            - "27 March 2021" (full month name)
            - "27 Mar 2021" (abbreviated month name)
            - "27/03/2021" (slash-separated)
            - "27-03-2021" (dash-separated)
            - "2021-03-27" (ISO format)
            - "February 2024" (month and year only)
            - "Mar 2024" (abbreviated month and year)
            - "2024" (year only)


        Args:
            soup: BeautifulSoup parsed HTML document


        Returns:
            Latest date found in YYYY-MM-DD format, or None if no dates are found
            or if the Follow-up section doesn't exist


        Raises:
            ValueError: If critical error occurs during extraction
        """
        try:
            # Use shared helper to extract all dates from Follow-up section
            date_matches = self._extract_dates_from_followup_section(soup)

            if not date_matches:
                return None

            # Parse all found dates and keep track of valid ones
            parsed_dates = []

            for date_str in date_matches:
                parsed = parse_any_date_format(date_str)
                if parsed:
                    parsed_dates.append(parsed)

            if not parsed_dates:
                return None

            # Sort dates and return the latest (maximum date)
            parsed_dates.sort()
            return parsed_dates[-1]

        except Exception as e:
            raise ValueError(
                f"Error extracting latest update date for {self.registration_number}: {str(e)}"
            ) from e

    def extract_followup_events_with_dates(self, soup: BeautifulSoup) -> Optional[dict]:
        """
        Extract follow-up actions with associated dates in structured JSON format.

        Returns JSON array with structure:
        [
            {
                "dates": ["2020-01-01", "2021-01-01"],
                "action": "Following up on its commitment..."
            },
            ...
        ]

        Each action corresponds to a paragraph, list item, or div following the Follow-up header.
        Dates are extracted from the text and normalized to ISO 8601 format (YYYY-MM-DD).
        If no dates are found in the action text, the dates array will be empty.

        Args:
            soup: BeautifulSoup object of the HTML document

        Returns:
            dict with follow-up actions and dates, or None if no follow-up section exists
            or no valid actions are found

        Raises:
            ValueError: If critical error occurs during extraction
        """
        try:
            # Find the Follow-up section
            result = self._find_followup_section(soup)

            if not result:
                return None

            # Unpack tuple and pass to extraction
            follow_up_actions = self._extract_followup_actions(result)

            if not follow_up_actions:
                raise ValueError(
                    f"No valid follow-up actions found for initiative {self.registration_number}"
                )

            return follow_up_actions

        except Exception as e:
            raise ValueError(
                f"Error calculating follow-up duration for {self.registration_number}: {str(e)}"
            ) from e

    def _extract_followup_actions(
        self, followup_section: Tuple[Tag, str]
    ) -> List[Dict[str, Union[List[str], str]]]:
        """
        Extract follow-up actions from the Follow-up section.

        Args:
            followup_section: Tuple with (element, marker)
                            - element: BeautifulSoup element of the Follow-up header
                            - marker: Type of header ('h2' or 'h4')

        Returns:
            List of dictionaries with 'dates' and 'action' keys
        """

        # Unpack the tuple
        section_element, section_marker = followup_section

        follow_up_actions = []
        current_element = section_element.find_next_sibling()

        while current_element:
            # Stop at next major heading
            if self._should_stop_extraction(current_element, section_marker):
                break

            # Process paragraphs and divs
            if current_element.name in ["p", "div"]:
                action = self._process_text_element(current_element)
                if action:
                    follow_up_actions.append(action)

            # Process unordered/ordered lists - extract individual list items
            elif current_element.name in ["ul", "ol"]:
                actions = self._process_list_element(current_element)
                follow_up_actions.extend(actions)

            current_element = current_element.find_next_sibling()

        return follow_up_actions

    def _should_stop_extraction(self, element, section_marker: str) -> bool:
        """
        Check if we should stop extracting follow-up actions.

        Args:
            element: Current BeautifulSoup element
            section_marker: Type of Follow-up header ('h2' or 'h4')

        Returns:
            True if extraction should stop, False otherwise
        """

        if element.name == "h2":
            return True
        if section_marker == "h4" and element.name == "h4":
            return True
        return False

    def _format_links_as_markdown(self, element: Tag) -> str:
        """
        Convert anchor tags to Markdown format [text](url) before extracting text.

        Args:
            element: BeautifulSoup element

        Returns:
            Text with links formatted as Markdown
        """
        # Create a copy to avoid modifying the original
        element_copy = copy.copy(element)

        # Find all anchor tags
        for link in element_copy.find_all("a", href=True):
            link_text = link.get_text(strip=True)
            link_url = link.get("href", "")

            # Replace the link tag with Markdown format
            markdown_link = f"[{link_text}]({link_url})"
            link.replace_with(markdown_link)

        return element_copy.get_text(separator=" ", strip=True)

    def _process_text_element(
        self, element
    ) -> Optional[Dict[str, Union[List[str], str]]]:
        """
        Process a paragraph or div element.

        Args:
            element: BeautifulSoup element

        Returns:
            Dictionary with 'dates' and 'action' keys, or None if should be skipped
        """
        # Extract text while preserving links in Markdown format
        action_text = self._format_links_as_markdown(element)
        action_text_normalized = re.sub(r"\s+", " ", action_text)

        # Skip very short content
        if len(action_text_normalized) < 30:
            return None

        # Skip generic intro paragraphs or subsection headers
        if self._should_skip_text(action_text_normalized):
            return None

        # Extract dates from the text
        dates = self._extract_dates_from_text(action_text_normalized)

        return {"dates": dates, "action": action_text_normalized}

    def _process_list_element(
        self, list_element
    ) -> List[Dict[str, Union[List[str], str]]]:
        """
        Process a list element (ul or ol) and extract individual list items.

        Args:
            list_element: BeautifulSoup list element

        Returns:
            List of dictionaries with 'dates' and 'action' keys
        """

        actions = []

        for li in list_element.find_all("li", recursive=False):

            action_text = li.get_text(separator=" ", strip=True)
            action_text_normalized_spaces = re.sub(r"\s+", " ", action_text)

            # Skip very short items
            if len(action_text_normalized_spaces) < 30:
                continue

            # Extract dates from the text
            dates = self._extract_dates_from_text(action_text_normalized_spaces)

            actions.append({"dates": dates, "action": action_text_normalized_spaces})

        return actions

    def _should_skip_text(self, text: str) -> bool:
        """
        Determine if text should be skipped (generic intro or subsection header).

        Args:
            text: Text content to check

        Returns:
            True if text should be skipped, False otherwise
        """

        skip_patterns = [
            "provides regularly updated information",
            "provides information on the follow-up",
            "this section provides",
        ]

        text_lower = text.lower()

        for pattern in skip_patterns:

            if pattern in text_lower:
                return True

        # Also skip if it's just a subsection header (ends with colon)
        if text.endswith(":"):
            return True

        return False

    def _extract_dates_from_text(self, text: str) -> List[str]:
        """
        Extract and normalize dates from text to ISO 8601 format.

        Only keeps the most specific date at each text position to avoid duplicates.

        Supported formats:
        - ISO: 2025-09-10
        - Numeric: 09/09/2014, 12.10.2015, 27-03-2021
        - DMY: 28 October 2015, 15 Mar 2021
        - Deadline: "early 2026", "end of 2023"
        - MY: February 2018, Mar 2024
        - Year: 2021 (strictly standalone)

        Args:
            text: Text content to extract dates from

        Returns:
            List of ISO 8601 formatted date strings
        """

        # 1. Remove URLs to prevent false positives from file paths/links containing dates
        # e.g., ".../2022-11/cp220179en.pdf" -> ""
        text = re.sub(r"https?://\S+|www\.\S+", "", text)

        # 2. Remove known proper names/titles containing years to prevent false positives
        # These are labels for programs/agendas, not specific event dates.
        ignored_phrases = [
            r"2030 Agenda",
            r"Agenda 2030",
            r"Europe 2020",
            r"Horizon 2020",
            r"Natura 2000",
            r"Vision 2025",  # e.g., "2025 Vision for Agriculture"
            r"Vision 2030",
            r"Vision 2050",
            r"Industrie 4\.0",
            r"Industry 4\.0",
            r"2020 Farm to Fork Strategy",
        ]
        # Join into a single regex pattern (case-insensitive)
        ignored_pattern = "|".join(ignored_phrases)
        text = re.sub(ignored_pattern, "", text, flags=re.IGNORECASE)

        # Generate month names pattern from calendar module
        month_names_full = "|".join(calendar.month_name[1:])
        month_names_abbr = "|".join(calendar.month_abbr[1:])
        month_names_pattern = f"(?:{month_names_full}|{month_names_abbr})"

        # Date patterns ordered by specificity (most specific first)
        date_patterns = [
            # 1. ISO format YYYY-MM-DD (e.g., "2025-09-10")
            (r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b", "iso"),
            # 2. Numeric formats (e.g., "09/09/2014", "12.10.2015", "27-03-2021")
            # Uses backreference \2 to ensure separators match
            (r"\b(\d{1,2})([./-])(\d{1,2})\2(\d{4})\b", "numeric"),
            # 3. DD Month YYYY (e.g., "28 October 2015", "15 Mar 2021")
            (rf"\b(\d{{1,2}})\s+({month_names_pattern})\s+(\d{{4}})\b", "dmy"),
            # 4. Deadline expressions (e.g., "early 2026", "end of 2023", "end 2024")
            (
                rf"\b(?:early|end(?:\s+of)?)\s+(?:({month_names_pattern})\s+)?(\d{{4}})\b",
                "deadline",
            ),
            # 5. Month YYYY (e.g., "February 2018", "Mar 2024")
            (rf"\b({month_names_pattern})\s+(\d{{4}})\b", "deadline"),
            # 6. YYYY only (e.g., "2021")
            # Lookbehind/Lookahead to avoid:
            # - IDs/Fractions: "2022/0002"
            # - Directives: "2010/63/EU"
            # - Parentheses: "C(2021)"
            # - Ranges: "2021-2027"
            (r"(?<![\d\/\(\-])\b(20\d{2})\b(?![\d\/\-])", "y"),
        ]

        found_dates = []
        used_positions: set = set()

        # Process patterns in order of specificity
        for pattern, date_type in date_patterns:
            matches = list(re.finditer(pattern, text, re.IGNORECASE))

            for match in matches:
                # Check if this position overlaps with already used position
                match_range = range(match.start(), match.end())

                if any(pos in used_positions for pos in match_range):
                    continue

                try:
                    if date_type == "deadline":
                        # Use convert_deadline_to_date for flexible deadline parsing
                        deadline_text = match.group(0)
                        iso_date = convert_deadline_to_date(deadline_text)
                    else:
                        # Use existing parsing for exact dates
                        iso_date = self._parse_date_match(match, date_type)

                    if iso_date:
                        found_dates.append(iso_date)

                        # Mark this position as used
                        for pos in match_range:
                            used_positions.add(pos)

                except (ValueError, AttributeError):
                    continue

        # Remove duplicates while preserving order
        return list(dict.fromkeys(found_dates))

    def _parse_date_match(self, match: re.Match, date_type: str) -> Optional[str]:
        """
        Parse a regex match into an ISO 8601 date string.

        Args:
            match: Regex match object
            date_type: Type of date format ('iso', 'numeric', 'dmy', 'my', or 'y')

        Returns:
            ISO 8601 formatted date string (YYYY-MM-DD), or None if parsing fails
        """
        try:
            if date_type == "iso":
                year, month, day = (
                    int(match.group(1)),
                    int(match.group(2)),
                    int(match.group(3)),
                )
                return self._validate_and_format(year, month, day)

            elif date_type == "numeric":
                # Matches: Group 1 (Day), Group 2 (Sep), Group 3 (Month), Group 4 (Year)
                day = int(match.group(1))
                month = int(match.group(3))
                year = int(match.group(4))
                return self._validate_and_format(year, month, day)

            elif date_type == "dmy":
                day = int(match.group(1))
                month_name = match.group(2).capitalize()
                year = int(match.group(3))

                month = self._get_month_number(month_name)
                if not month:
                    return None

                return self._validate_and_format(year, month, day)

            elif date_type == "my":
                # Legacy handler if not caught by "deadline" logic, defaults to 1st of month
                month_name = match.group(1).capitalize()
                year = int(match.group(2))

                month = self._get_month_number(month_name)
                if not month:
                    return None

                return f"{year:04d}-{month:02d}-01"

            elif date_type == "y":
                # YYYY format
                year = int(match.group(1))
                return f"{year:04d}-01-01"

        except (ValueError, AttributeError):
            return None
        return None

    def _get_month_number(self, month_name: str) -> Optional[int]:
        """Helper to convert full or abbr month name to number."""
        try:
            return datetime.strptime(month_name, "%B").month
        except ValueError:
            try:
                return datetime.strptime(month_name, "%b").month
            except ValueError:
                return None

    def _validate_and_format(self, year: int, month: int, day: int) -> Optional[str]:
        """Helper to validate date validity and return ISO string."""
        if not (1 <= month <= 12):
            return None

        try:
            max_day = calendar.monthrange(year, month)[1]
            if not (1 <= day <= max_day):
                return None
            return f"{year:04d}-{month:02d}-{day:02d}"
        except (ValueError, IndexError):
            return None
