"""
Extracts follow-up activity information including
roadmaps, workshops, partnership programs, and
court case references from post-response sections.
"""

from datetime import date, datetime
import re
from typing import Optional, Tuple, Union, Dict, List

from bs4 import BeautifulSoup, Tag, NavigableString

from ..base.base_extractor import BaseExtractor
from ..base.date_parser import parse_any_date_format


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

    def extract_followup_events(
        self, soup: BeautifulSoup
    ) -> Optional[Union[List[str], Dict[str, List[str]]]]:
        """
        Extract follow-up events information as structured JSON with links preserved.

        Extracts content from the Follow-up section and returns it in one of three formats:
        1. List[str] - Simple list of text items (no subsections)
        2. Dict[str, List[str]] - Dictionary with subsection names as keys and lists of items as values
        3. None - If no Follow-up section exists

        The Follow-up content can appear:
        1. As a separate <h2 id="Follow-up"> section
        2. As an <h4>Follow-up</h4> subsection within "Answer of the European Commission
        and follow-up" section

        Subsections are identified by <strong> tags that contain the ONLY content of a paragraph,
        typically ending with a colon (e.g., "<p><strong>Legislative action:</strong></p>").
        Links are preserved in the format: "link text (url)"

        Returns:
            - List[str] if section has no subsections, e.g.:
            ["Item 1", "Item 2 (https://example.com)", "Item 3"]

            - Dict[str, List[str]] if section has subsections, e.g.:
            {
                "Legislative action": [
                    "Amendment to Directive... (https://url1)",
                    "Proposal for revision... (https://url2)"
                ],
                "Implementation and review": [
                    "Report 1... (https://url3)"
                ]
            }

            - None if no Follow-up section exists

        Raises:
            ValueError: If critical error occurs during extraction
        """
        try:
            # Use the shared lookup method
            result = self._find_followup_section(soup)

            if not result:
                # No Follow-up section exists
                return None

            followup_section, section_marker = result

            # Collect all content with subsection awareness
            content_parts = []
            subsections = {}
            current_subsection = None
            current_subsection_items = []
            current_element = followup_section.find_next_sibling()

            while current_element:
                # Stop at next h2 or h4 marker (depending on which pattern found section)
                if current_element.name == "h2":
                    break
                if section_marker == "h4" and current_element.name == "h4":
                    break

                if current_element.name:  # Only process actual HTML tags
                    # Check if this is a subsection header (paragraph with strong tag)
                    if current_element.name == "p":
                        strong_tag = current_element.find("strong")

                        # Check if this is a SUBSECTION HEADER pattern:
                        # The paragraph contains ONLY a <strong> tag (possibly with colon/punctuation)
                        # and nothing else of substance
                        is_subsection_header = False
                        if strong_tag:
                            # Get the full paragraph text
                            para_text = self._extract_text_with_links(
                                current_element
                            ).strip()
                            strong_text = strong_tag.get_text(strip=True)

                            # A subsection header has the strong text as its primary content
                            # (allowing for trailing colons or punctuation)
                            # Check if the full text is essentially just the strong text
                            if (
                                para_text.rstrip(":").rstrip()
                                == strong_text.rstrip(":").rstrip()
                            ):
                                is_subsection_header = True

                        if is_subsection_header:
                            strong_tag = current_element.find("strong")
                            subsection_text = strong_tag.get_text(strip=True)

                            # Check for boundary marker BEFORE processing as subsection
                            if subsection_text.startswith("Other information"):
                                break

                            # Save previous subsection if exists
                            if current_subsection and current_subsection_items:
                                subsections[current_subsection] = (
                                    current_subsection_items
                                )
                                current_subsection_items = []

                            # Start new subsection
                            current_subsection = subsection_text
                            # IMPORTANT: Must move to next sibling BEFORE continue
                            current_element = current_element.find_next_sibling()
                            continue

                        # Regular paragraph (could have inline strong tags)
                        # Use link-preserving extraction
                        text = self._extract_text_with_links(current_element)

                        if text:
                            if current_subsection:
                                current_subsection_items.append(text)
                            else:
                                content_parts.append(text)

                    elif current_element.name == "ul":
                        # Process list items with link preservation
                        for li in current_element.find_all("li", recursive=False):
                            text = self._extract_text_with_links(li)
                            if text:
                                if current_subsection:
                                    current_subsection_items.append(text)
                                else:
                                    content_parts.append(text)

                current_element = current_element.find_next_sibling()

            # Save last subsection if exists
            if current_subsection and current_subsection_items:
                subsections[current_subsection] = current_subsection_items

            # Return structured data
            if subsections:
                # Has subsections: return dict
                return subsections if subsections else None
            elif content_parts:
                # No subsections: return list
                return content_parts
            else:
                # Empty follow-up section
                return None

        except Exception as e:
            raise ValueError(
                f"Error extracting followup events for {self.registration_number}: {str(e)}"
            ) from e

    def extract_has_partnership_programs(self, soup: BeautifulSoup) -> Optional[bool]:
        """
        Check if initiative has partnership programs mentioned in follow-up.

        Looks for keywords like "partnerships", "partnership programs", "public-public partnerships",
        etc. in the Follow-up section.

        Args:
            soup: BeautifulSoup parsed HTML document

        Returns:
            True if partnership programs are mentioned, False otherwise, None on error

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

            # Check for partnership-related keywords
            partnership_keywords = [
                "partnership",
                "partnerships",
                "public-public partnership",
                "water operators",
                "partner",
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
                "workshop",
                "workshops",
                "conference",
                "conferences",
                "stakeholder meeting",
                "stakeholder meetings",
                "dedicated workshop",
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
