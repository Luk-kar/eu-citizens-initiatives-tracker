"""
Performs structural analysis by extracting related
EU legislation references, petition platforms used, and
calculating follow-up durations.
"""

import re
import json
from typing import Optional, Dict, List

from bs4 import BeautifulSoup

from ..base.base_extractor import BaseExtractor


class StructuralAnalysisExtractor(BaseExtractor):
    """Extracts structural analysis data"""

    def extract_referenced_legislation_by_id(
        self, soup: BeautifulSoup
    ) -> Optional[str]:
        """Extract references to specific Regulations or Directives by number/id"""
        try:
            from urllib.parse import unquote

            # Get text content from the soup
            text = soup.get_text()

            # FIRST: Extract CELEX numbers from href attributes in links (with URL decoding)
            celex_from_links = []
            celex_links = soup.find_all("a", href=re.compile(r"CELEX", re.IGNORECASE))
            for link in celex_links:
                href = link.get("href", "")
                # DECODE URL to handle %3A, %26, etc.
                decoded_href = unquote(href)
                match = re.search(
                    r"CELEX[=:]([0-9]{5}[A-Z]{1,2}[0-9]{4}[A-Z]?[0-9]{0,4})",
                    decoded_href,
                    re.IGNORECASE,
                )
                if match:
                    celex_from_links.append(match.group(1))

            # SECOND: Extract Official Journal references from href attributes
            legislation_refs = []
            information_refs = []
            oj_pattern = r"uri=uriserv:OJ\.(L|C)_\.(\d{4})\.(\d{1,3})\.\d{2}\.\d{4}"
            all_oj_links = soup.find_all(
                "a", href=re.compile(r"uriserv:OJ", re.IGNORECASE)
            )
            for link in all_oj_links:
                href = link.get("href", "")
                # DECODE URL to handle encoded characters
                decoded_href = unquote(href)
                match = re.search(oj_pattern, decoded_href, re.IGNORECASE)
                if match:
                    series = match.group(1).upper()
                    year = match.group(2)
                    issue = match.group(3)
                    ref_string = f"{year}, {issue}"

                    if series == "L":
                        legislation_refs.append(ref_string)
                    elif series == "C":
                        information_refs.append(ref_string)

            # Define regex patterns for text extraction
            patterns = {
                "Regulation": r"Regulation\s+\((?:EU|EC)\)\s+(?:No\.?\s*)?(\d{1,4}/\d{4})",
                "Directive": r"Directive\s+(\d{4}/\d{1,3}(?:/(?:EU|EC))?)",
                "Decision": r"(?:(?:Council|Commission)\s+)?Decision\s+(?:\((?:EU|EC|EEC)\)\s+)?(?:No\.?\s+)?(\d+/\d+)",
                "CELEX": r"CELEX[=:]\s*([0-9]{5}[A-Z]{1,2}[0-9]{4}[A-Z]?[0-9]{0,4})",
                "Article": r"Article\s+(\d{1,3}(?:\([a-z0-9]+\))?)",
            }

            # Extract matches for each pattern
            results: Dict[str, List[str]] = {}

            for key, pattern in patterns.items():
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    # Remove duplicates while preserving order
                    unique_matches = list(dict.fromkeys(matches))
                    results[key] = unique_matches

            # Add CELEX numbers from links (merge with text-based CELEX if exists)
            if celex_from_links:
                celex_from_links_unique = list(dict.fromkeys(celex_from_links))
                if "CELEX" in results:
                    # Merge and remove duplicates
                    combined = results["CELEX"] + celex_from_links_unique
                    results["CELEX"] = list(dict.fromkeys(combined))
                else:
                    results["CELEX"] = celex_from_links_unique

            # Add Official Journal references with nested structure
            if legislation_refs or information_refs:
                official_journal = {}

                if legislation_refs:
                    legislation_refs_unique = list(dict.fromkeys(legislation_refs))
                    official_journal["legislation"] = legislation_refs_unique

                if information_refs:
                    information_refs_unique = list(dict.fromkeys(information_refs))
                    official_journal["information_and_notices"] = (
                        information_refs_unique
                    )

                if official_journal:
                    results["official_journal"] = official_journal

            # Return None if no matches found, otherwise return JSON
            if not results:
                return None

            return json.dumps(results, ensure_ascii=False)

        except Exception as e:
            raise ValueError(
                f"Error extracting related EU legislation for {self.registration_number}: {str(e)}"
            ) from e

    def extract_referenced_legislation_by_name(
        self, soup: BeautifulSoup
    ) -> Optional[str]:
        """
        Extract references to specific Regulations or Directives by name.

        Returns JSON string with keys: treaty, charter, directives, regulations
        Each key contains a list of unique legislation references found.

        Args:
            soup: BeautifulSoup object of the HTML document

        Returns:
            JSON string with extracted legislation, or None if no legislation found
        """
        # Get all text from the document
        text = soup.get_text(separator=" ", strip=True)

        # Initialize result structure
        result: Dict[str, List[str]] = {
            "treaty": [],
            "charter": [],
            "directives": [],
            "regulations": [],
        }

        # Define regex patterns (using NON-GREEDY quantifiers {0,6}?)
        patterns = {
            "regulations": [
                r"\b([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+){0,6}?)\s+Regulation\b"
            ],
            "directives": [
                r"\b([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+){0,6}?)\s+Directive\b"
            ],
            "treaty": [
                r"Treaty\s+on\s+(?:the\s+)?(?:European\s+Union|Functioning\s+of\s+the\s+European\s+Union)",
                r"\b(TEU|TFEU)\b",
                r"\b([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+){0,5}?)\s+Treaty\b",
            ],
            "charter": [
                r"Charter\s+of\s+(?:the\s+)?Fundamental\s+Rights(?:\s+of\s+the\s+European\s+Union)?"
            ],
        }

        # Extract each type of legislation
        for category, pattern_list in patterns.items():
            matches = []

            for pattern in pattern_list:
                # Find all matches (case-insensitive)
                found = re.findall(pattern, text, re.IGNORECASE)

                # Handle both capture groups and full matches
                for match in found:
                    if isinstance(match, tuple):
                        # If pattern has multiple capture groups, take first non-empty
                        match_text = next((m for m in match if m), None)
                    else:
                        match_text = match

                    if match_text:
                        matches.append(match_text.strip())

            # Post-process: filter and deduplicate
            filtered_matches = []
            for match in matches:
                # Skip empty matches
                if not match or not match.strip():
                    continue

                # Skip if starts with articles
                if match.startswith(("The ", "the ", "A ", "a ", "An ", "an ")):
                    continue

                # Skip very short matches (likely noise)
                if len(match) < 3:
                    continue

                # Skip if all lowercase
                if match.islower():
                    continue

                # For regulations/directives: additional filtering
                if category in ["regulations", "directives"]:
                    # Must start with uppercase
                    if not match[0].isupper():
                        continue

                    # Skip if too long (more than 7 words)
                    if len(match.split()) > 7:
                        continue

                    # Skip if contains too many connector words
                    words = match.split()
                    connectors = ["and", "the", "of", "or", "for", "in", "on", "to"]
                    if sum(1 for w in words if w.lower() in connectors) > 3:
                        continue

                # Add if not already in list (case-insensitive deduplication)
                if not any(m.lower() == match.lower() for m in filtered_matches):
                    filtered_matches.append(match)

            result[category] = sorted(filtered_matches)

        # Return None if nothing found
        if not any(result.values()):
            return None

        # Remove empty keys from result
        result = {key: value for key, value in result.items() if value}

        # Return as JSON string
        return json.dumps(result, indent=2, ensure_ascii=False)

    def calculate_follow_up_duration_months(
        self, commission_date: Optional[str], latest_update: Optional[str]
    ) -> Optional[int]:
        """Calculate months between Commission response and latest follow-up"""
        try:
            return None
        except Exception as e:
            raise ValueError(
                f"Error calculating follow-up duration for {self.registration_number}: {str(e)}"
            ) from e
