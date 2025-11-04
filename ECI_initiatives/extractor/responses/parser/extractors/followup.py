"""
Extracts follow-up activity information including
roadmaps, workshops, partnership programs, and
court case references from post-response sections.
"""

import re
from typing import Optional, Tuple, Union, Dict, List

from bs4 import BeautifulSoup, Tag

from ..base.base_extractor import BaseExtractor


import re
from typing import Optional, Tuple, Union, Dict, List
from bs4 import BeautifulSoup, Tag, NavigableString
from ..base.base_extractor import BaseExtractor


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
        followup_section = soup.find("h2", id="Follow-up")
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

    def extract_partnership_programs(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract partnership programs information"""
        try:
            return None
        except Exception as e:
            raise ValueError(
                f"Error extracting partnership programs for {self.registration_number}: {str(e)}"
            ) from e

    def extract_court_cases_referenced(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract Court of Justice case numbers"""
        try:
            return None
        except Exception as e:
            raise ValueError(
                f"Error extracting court cases for {self.registration_number}: {str(e)}"
            ) from e

    def extract_latest_update_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract most recent date from follow-up section"""
        try:
            return None
        except Exception as e:
            raise ValueError(
                f"Error extracting latest update date for {self.registration_number}: {str(e)}"
            ) from e
