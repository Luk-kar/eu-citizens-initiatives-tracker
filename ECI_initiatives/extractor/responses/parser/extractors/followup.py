"""
Extracts follow-up activity information including
roadmaps, workshops, partnership programs, and
court case references from post-response sections.
"""

from typing import Optional

from bs4 import BeautifulSoup
import re

from ..base.base_extractor import BaseExtractor


class FollowUpActivityExtractor(BaseExtractor):
    """Extracts follow-up activities data"""

    def extract_has_followup_section(self, soup: BeautifulSoup) -> Optional[bool]:
        """Check if page includes follow-up activities section"""

        try:
            # Primary search: <h2 id="Follow-up">
            followup_section = soup.find("h2", id="Follow-up")

            if followup_section:
                return True

            # Fallback: Search by text content (case-insensitive)
            # Handles variations like <h2><strong>Follow-up</strong></h2>

            followup_section = soup.find(
                "h4", string=re.compile(r"^\s*follow-up\s*$", re.IGNORECASE)
            )

            if followup_section:
                return True

            # No Follow-up section found
            return False

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
            followup_section = None
            section_marker = None

            # Primary pattern: h2 with id="Follow-up"
            followup_section = soup.find("h2", id="Follow-up")
            if followup_section:
                section_marker = "h2"

            # Fallback pattern: h4 with text "Follow-up"
            if not followup_section:
                followup_section = soup.find(
                    "h4", string=re.compile(r"^\s*follow-up\s*$", re.IGNORECASE)
                )
                if followup_section:
                    section_marker = "h4"

            if not followup_section:
                # No Follow-up section exists
                return None

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
