"""
Extracts follow-up activity information including
roadmaps, workshops, partnership programs, and
court case references from post-response sections.
"""

from typing import Optional

from bs4 import BeautifulSoup
import re

from ..base.base_extractor import BaseExtractor


import re
from typing import Optional, Tuple
from bs4 import BeautifulSoup, Tag
from ..base.base_extractor import BaseExtractor


class FollowUpActivityExtractor(BaseExtractor):
    """Extracts follow-up activities data"""

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

        Examples:
            >>> tag, marker = self._find_followup_section(soup)
            >>> if tag:
            >>>     print(f"Found {marker} tag")
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

    def extract_followup_events(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Extract follow-up events information.

        Extracts all content from the Follow-up section. The Follow-up content can appear:
        1. As a separate <h2 id="Follow-up"> section
        2. As an <h4>Follow-up</h4> subsection within "Answer of the European Commission
           and follow-up" section

        When a Follow-up section exists, extraction continues until:
        - Next h2 tag (main section boundary)
        - Next h4 tag (subsection boundary) - only for h4 pattern
        - "Other information" marker (section conclusion)
        - End of content

        Args:
            soup: BeautifulSoup parsed HTML document

        Returns:
            String containing all Follow-up section text, or None if section not found

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

            # Collect all content until boundary marker or "Other information"
            content_parts = []
            current_element = followup_section.find_next_sibling()

            while current_element:
                # Stop at next h2 or h4 marker (depending on which pattern found section)
                if current_element.name == "h2":
                    break
                if section_marker == "h4" and current_element.name == "h4":
                    break

                if current_element.name:  # Only process actual HTML tags
                    text = current_element.get_text(separator=" ", strip=True)

                    if text:
                        # Stop if we encounter "Other information" marker
                        if text.strip().startswith("Other information"):
                            break

                        content_parts.append(text)

                current_element = current_element.find_next_sibling()

            if content_parts:
                # Join all paragraphs and lists with double newlines for readability
                return "\n\n".join(content_parts)

            # Follow-up section exists but is empty
            return None

        except Exception as e:
            raise ValueError(
                f"Error extracting followup events for {self.registration_number}: {str(e)}"
            ) from e

    def extract_has_partnership_programs(self, soup: BeautifulSoup) -> Optional[bool]:
        try:
            return None
        except Exception as e:
            raise ValueError(
                f"Error checking roadmap for {self.registration_number}: {str(e)}"
            ) from e

    def extract_has_roadmap(self, soup: BeautifulSoup) -> Optional[bool]:
        """Check if initiative has a roadmap"""
        try:
            return None
        except Exception as e:
            raise ValueError(
                f"Error checking roadmap for {self.registration_number}: {str(e)}"
            ) from e

    def extract_has_workshop(self, soup: BeautifulSoup) -> Optional[bool]:
        """Check if initiative has workshop activities"""
        try:
            return None
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
