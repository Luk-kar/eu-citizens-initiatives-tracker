"""
Extracts European Commission response details including
communication adoption dates, document URLs, and
answer text from successful ECI pages.
"""

import calendar
import re
import json
from typing import Optional

from bs4 import BeautifulSoup

from ..base.base_extractor import BaseExtractor
from ..consts.dates import month_map
from ..base.date_parser import format_date_from_match

from .html_sections import find_submission_section, build_links_dict


class CommissionResponseExtractor(BaseExtractor):
    """Extracts Commission communication and response data"""

    def extract_official_communication_adoption_date(
        self, soup: BeautifulSoup
    ) -> Optional[str]:
        """Extract date Commission adopted official Communication"""

        try:
            submission_section = find_submission_section(soup, self.registration_number)

            paragraphs = submission_section.find_next_siblings("p")

            adoption_phrase = "Commission adopted a Communication on"

            commission_paragraph = None
            for p in paragraphs:
                text = p.get_text(separator=" ", strip=True)
                text = re.sub(r"\s+", " ", text)

                if adoption_phrase in text:
                    commission_paragraph = text
                    break

            if not commission_paragraph:
                return None

            date_pattern = adoption_phrase + r"\s+(\d{1,2})\s+(\w+)\s+(\d{4})"
            match = re.search(date_pattern, commission_paragraph, re.IGNORECASE)

            if match:
                day = match.group(1).zfill(2)
                month_name = match.group(2).lower()
                year = match.group(3)

                month_str = month_map.get(month_name)
                if month_str is None:
                    raise ValueError(f"Invalid month name: {month_name}")

                return f"{day}-{month_str}-{year}"

            date_pattern_slash = adoption_phrase + r"\s+(\d{1,2})/(\d{1,2})/(\d{4})"
            match = re.search(date_pattern_slash, commission_paragraph, re.IGNORECASE)

            return format_date_from_match(match)

        except Exception as e:
            raise ValueError(
                "Error extracting commission communication date for "
                f"{self.registration_number}: {str(e)}"
            ) from e

    def extract_official_communication_document_urls(
        self, soup: BeautifulSoup
    ) -> Optional[str]:
        """Extract link to full PDF of Commission Communication as JSON"""
        try:
            submission_section = find_submission_section(soup, self.registration_number)

            paragraphs = submission_section.find_next_siblings("p")

            commission_paragraph_element = None
            for p in paragraphs:
                text = p.get_text(separator=" ", strip=True)
                text = re.sub(r"\s+", " ", text)

                if re.search(
                    r"Commission\s+adopted\s+a\s+Communication\s+on",
                    text,
                    re.IGNORECASE,
                ):
                    commission_paragraph_element = p
                    break

            if not commission_paragraph_element:
                return None

            links = commission_paragraph_element.find_all("a")

            links_dict = build_links_dict(links)

            if not links_dict:
                return None

            exclude_patterns = [
                r"https?://ec\.citizens-initiative\.europa\.eu/public/initiatives/successful/details/\d{4}/\d{6}(_[a-z]{2})?/?$",
                r"https?://citizens-initiative\.europa\.eu/initiatives/details/\d{4}/\d{6}[_]?[a-z]{2}/?$",
            ]

            filtered_links_dict = {}
            for text, url in links_dict.items():
                should_exclude = False
                for pattern in exclude_patterns:
                    if re.match(pattern, url):
                        should_exclude = True
                        break

                if not should_exclude:
                    filtered_links_dict[text] = url

            if not filtered_links_dict:
                return None

            return json.dumps(filtered_links_dict)

        except Exception as e:
            raise ValueError(
                "Error extracting commission communication URL for "
                f"{self.registration_number}: {str(e)}"
            ) from e

    def extract_commission_answer_text(self, soup: BeautifulSoup) -> str:
        """Extract main conclusions text from Communication, excluding factsheet downloads

        Raises:
            ValueError: If the Commission answer section cannot be found or extracted
        """
        try:
            # Find the "Answer of the European Commission" header
            answer_header = soup.find("h2", id="Answer-of-the-European-Commission")

            if not answer_header:
                # Alternative: find h2 containing the text
                answer_header = soup.find(
                    "h2",
                    string=lambda text: text
                    and "Answer of the European Commission" in text,
                )

            if not answer_header:
                raise ValueError(
                    "Could not find 'Answer of the European Commission' section for "
                    f"{self.registration_number}"
                )

            # Collect all content between this header and the Follow-up header
            content_parts = []
            current = answer_header.find_next_sibling()

            while current:
                # Stop if we hit Follow-up or another major section
                if current.name == "h2":
                    h2_id = current.get("id", "")
                    h2_text = current.get_text(strip=True)
                    if "Follow-up" in h2_text or h2_id == "Follow-up":
                        break
                    # Also stop at other major sections
                    if h2_id and h2_id != "Answer-of-the-European-Commission":
                        break

                # Skip factsheet file download components (ecl-file divs)
                if current.name == "div" and "ecl-file" in current.get("class", []):
                    current = current.find_next_sibling()
                    continue

                # Extract and format content from this element
                if current.name:
                    element_text = self._extract_element_with_links(current)
                    if element_text:
                        content_parts.append(element_text)

                current = current.find_next_sibling()

            if not content_parts:
                raise ValueError(
                    "No content found in 'Answer of the European Commission' section for "
                    f"{self.registration_number}"
                )

            return "\n".join(content_parts).strip()

        except ValueError:
            # Re-raise ValueError as-is
            raise
        except Exception as e:
            raise ValueError(
                "Error extracting communication main conclusion for "
                f"{self.registration_number}: {str(e)}"
            ) from e

    def _extract_element_with_links(self, element) -> str:
        """Helper to extract text while preserving links in markdown format"""

        if not element.name:
            return ""

        # Skip ecl-file components completely
        if element.name == "div" and "ecl-file" in element.get("class", []):
            return ""

        # For elements with links, convert to markdown
        if element.name == "a":
            link_text = element.get_text(strip=True)
            href = element.get("href", "")
            return f"[{link_text}]({href})"

        # For list items, extract with links
        if element.name == "li":
            text_parts = []
            for child in element.children:
                if hasattr(child, "name"):
                    if child.name == "a":
                        link_text = child.get_text(strip=True)
                        href = child.get("href", "")
                        text_parts.append(f"[{link_text}]({href})")
                    else:
                        child_text = child.get_text(strip=True)
                        if child_text:
                            text_parts.append(child_text)
                else:
                    child_text = str(child).strip()
                    if child_text:
                        text_parts.append(child_text)
            return " ".join(text_parts)

        # For paragraphs and other elements, process children to preserve links
        if element.find("a"):
            text_parts = []
            for child in element.descendants:
                if isinstance(child, str):
                    text = child.strip()
                    if text and text not in ["", "\n"]:
                        text_parts.append(text)
                elif hasattr(child, "name") and child.name == "a":
                    link_text = child.get_text(strip=True)
                    href = child.get("href", "")
                    if link_text:
                        text_parts.append(f"[{link_text}]({href})")
            return " ".join(text_parts)

        # Default: return plain text
        return element.get_text(strip=True)
