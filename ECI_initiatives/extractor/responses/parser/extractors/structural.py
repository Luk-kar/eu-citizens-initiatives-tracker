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

        name_extractor = LegislationNameExtractor()
        return name_extractor.extract_referenced_legislation_by_name(soup)

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


class LegislationNameExtractor:
    """
    Extracts EU legislation references by name from HTML content.
    Focuses on treaties, charters, directives, and regulations.
    """

    def _create_legislative_pattern(self, type_legislation: str) -> str:
        """
        Creates a regex pattern for extracting legislative names
        based on title case words and common EU prepositions.

        Args:
            type_legislation: The type of legislation ("Directive", "Regulation", etc.)

        Returns:
            Regex pattern string for matching legislative names
        """
        EU_LEGISLATION_PREPOSITIONS = r"(?:of|and|the|for|on|in|to)"
        EU_PUNCTUATION_LINKS = r"\s*[\'\‐]\s*"
        EU_NAME_SPACERS = (
            rf"(?:\s+{EU_LEGISLATION_PREPOSITIONS}|{EU_PUNCTUATION_LINKS})"
        )
        TITLE_CASE_WORD = r"[A-Z]\w*"

        return rf"\b{TITLE_CASE_WORD}(?:{EU_NAME_SPACERS}?\s*{TITLE_CASE_WORD})*(?:{EU_NAME_SPACERS}?\s*{type_legislation})\b"

    def _extract_pattern_matches(
        self,
        filtered_parts: List[str],
        patterns: List[str],
        result_key: str,
        result: Dict[str, List[str]],
    ) -> None:
        """
        Generic pattern extraction helper for treaties, charters, and similar categories.

        Args:
            filtered_parts: List of text parts to search through
            patterns: List of regex patterns to match
            result_key: Key in result dict to store matches
            result: Dictionary to store extracted matches
        """
        for part in filtered_parts:
            for pattern in patterns:
                matches = re.findall(pattern, part)

                for match in matches:
                    # Handle tuple matches from capturing groups
                    if isinstance(match, tuple):
                        # For patterns with multiple groups, take first non-empty group
                        # This handles cases like (group1, group2) where one might be empty
                        match = (
                            match[0]
                            if match[0]
                            else match[1] if len(match) > 1 and match[1] else ""
                        )

                    # Only add non-empty matches that aren't already present
                    if match and match and match not in result[result_key]:
                        result[result_key].append(match.strip())

    def _clean_leading_articles(self, items: List[str]) -> List[str]:
        """Remove leading articles from each item ('The', 'the', 'A', 'a', etc.)"""
        cleaned = []
        articles = ("The ", "the ", "A ", "a ", "An ", "an ")

        for item in items:
            cleaned_item = item
            for article in articles:
                if cleaned_item.startswith(article):
                    cleaned_item = cleaned_item[len(article) :]
                    break
            if cleaned_item:
                cleaned.append(cleaned_item)

        return cleaned

    def _filter_standalone_keywords(self, items: List[str], keyword: str) -> List[str]:
        """
        Remove items that are just the keyword alone or with common generic prefixes.
        Filters out overly generic references like "EU Directive" or "Proposal for Regulation".

        Args:
            items: List of items to filter
            keyword: The legislation keyword to filter against ("Directive", "Regulation", etc.)

        Returns:
            Filtered list excluding standalone/generic keywords
        """
        filtered = []

        # Standalone variations (just the keyword with articles)
        standalone_variations = [
            keyword,
            f"the {keyword}",
            f"The {keyword}",
            f"a {keyword}",
            f"A {keyword}",
            f"an {keyword}",
            f"An {keyword}",
        ]

        # Common prefixes that make the item too generic
        generic_prefixes = [
            "Proposal for",
            "proposal for",
            "Revised",
            "revised",
            "New",
            "new",
            "Draft",
            "draft",
        ]

        for item in items:
            item_stripped = item.strip()
            item_lower = item_stripped.lower()

            # Check if item is exactly a standalone keyword (case-insensitive)
            if item_lower in [variation.lower() for variation in standalone_variations]:
                continue  # Skip this item

            # Check EU separately with word boundary
            if re.match(
                r"^EU\s+" + re.escape(keyword) + r"$", item_stripped, re.IGNORECASE
            ):
                continue  # Skip only exact "EU Regulation" matches

            # Check if item is just a generic prefix + keyword
            is_generic = False
            for prefix in generic_prefixes:
                # Pattern: "Proposal for Regulation" or "Proposal for the Regulation"
                if item_lower == f"{prefix.lower()} {keyword.lower()}":
                    is_generic = True
                    break
                if item_lower == f"{prefix.lower()} the {keyword.lower()}":
                    is_generic = True
                    break
                if item_lower == f"{prefix.lower()} a {keyword.lower()}":
                    is_generic = True
                    break

            if not is_generic:
                filtered.append(item)

        return filtered

    def _deduplicate_items(self, items: List[str]) -> List[str]:
        """Remove duplicates (case-insensitive) and return sorted unique items"""
        seen = set()
        unique = []

        for item in items:
            item_lower = item.lower()
            if item_lower not in seen:
                seen.add(item_lower)
                unique.append(item)

        return sorted(unique)

    def _split_multiple_legislations(self, items: List[str], keyword: str) -> List[str]:
        """
        Split items that contain multiple legislations connected by 'and', 'or', or newlines.
        Removes the original combined items and reconstructs individual references.

        Example:
            Input: ["Water Framework Directive and Floods Directive", "Birds Directive"]
            Output: ["Water Framework Directive", "Floods Directive", "Birds Directive"]

        Args:
            items: List of legislation strings
            keyword: The legislation keyword to split on ("Directive", "Regulation", etc.)

        Returns:
            List of split individual legislation references
        """
        split_items = []

        for item in items:
            # First split by newlines
            newline_parts = item.split("\n")

            for newline_part in newline_parts:
                newline_part = newline_part.strip()
                if not newline_part:
                    continue

                # Count how many times the keyword appears in this part
                keyword_count = len(
                    re.findall(
                        rf"\b{re.escape(keyword)}\b", newline_part, re.IGNORECASE
                    )
                )

                if keyword_count > 1:
                    # Multiple keywords found - split and DON'T keep the original
                    parts = re.split(
                        rf"\b{re.escape(keyword)}\b",
                        newline_part,
                        flags=re.IGNORECASE,
                    )

                    for i in range(len(parts) - 1):
                        # Each part (except the last) should be followed by the keyword
                        part = parts[i].strip()

                        # Remove trailing conjunction from the part
                        part = re.sub(
                            r"\s*(?:and|or)\s*$", "", part, flags=re.IGNORECASE
                        )

                        # Remove leading conjunction from the part
                        part = re.sub(
                            r"^\s*(?:and|or)\s*", "", part, flags=re.IGNORECASE
                        )

                        if part:
                            # Reconstruct with keyword
                            split_items.append(f"{part} {keyword}".strip())
                    # NOTE: We do NOT append the original combined item
                else:
                    # Single keyword - keep as is
                    split_items.append(newline_part)

        return split_items

    def _process_legislation_category(
        self, key: str, result: Dict[str, List[str]], keyword_map: Dict[str, str]
    ) -> None:
        """
        Process a single legislation category: clean articles, split multiples,
        filter standalone keywords, and deduplicate items.

        Args:
            key: The category key ("directives", "regulations", etc.)
            result: The result dictionary containing the category list
            keyword_map: Mapping of category keys to their processing keywords
        """
        if key not in result or not result[key]:
            return

        keyword = keyword_map.get(key, key.capitalize())

        # Clean leading articles
        result[key] = self._clean_leading_articles(result[key])

        # Split multiple legislations and filter standalone keywords
        items = self._split_multiple_legislations(result[key], keyword)
        items = self._filter_standalone_keywords(items, keyword)
        result[key] = items

        # Deduplicate and sort
        result[key] = self._deduplicate_items(result[key])

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
        # Unwrap all <strong> tags (removes tag but keeps text)
        for strong_tag in soup.find_all("strong"):
            strong_tag.unwrap()

        # Now apply newline separator to all remaining tags
        text = soup.get_text(separator="\n", strip=True)

        # Initialize result structure
        result: Dict[str, List[str]] = {
            "treaties": [],
            "charters": [],
            "directives": [],
            "regulations": [],
        }

        # Step 1: Divide text into parts by sentence dividers (. ; ,)
        sentence_parts = re.split(r"[.;,]", text)

        # Step 2: Filter out parts containing legislation keywords
        keywords = ["Directive", "Regulation", "Law", "Treaty", "Charter"]
        filtered_parts = []

        for part in sentence_parts:
            if any(keyword in part for keyword in keywords):
                filtered_parts.append(part.strip())

        # Step 3: Extract directives and regulations using regex
        directive_pattern = self._create_legislative_pattern("Directive")
        regulation_pattern = self._create_legislative_pattern("Regulation")

        for part in filtered_parts:
            # Extract directives
            directive_matches = re.findall(directive_pattern, part)
            for match in directive_matches:
                result["directives"].append(match.strip())

            # Extract regulations
            regulation_matches = re.findall(regulation_pattern, part)
            for match in regulation_matches:
                result["regulations"].append(match.strip())

        # Extract treaties using specific patterns
        treaty_patterns = [
            r"Treaty\s+on\s+(?:the\s+)?(?:European\s+Union|Functioning\s+of\s+the\s+European\s+Union)",
            r"\b(TEU|TFEU)\b",
            r"\b([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+){0,5})\s+Treaty\b",
        ]

        self._extract_pattern_matches(
            filtered_parts=filtered_parts,
            patterns=treaty_patterns,
            result_key="treaties",
            result=result,
        )

        # Extract charters using specific patterns
        charter_patterns = [
            r"Charter\s+of\s+(?:the\s+)?Fundamental\s+Rights(?:\s+of\s+the\s+European\s+Union)?",
            r"\b([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+){0,5})\s+Charter\b",
        ]

        self._extract_pattern_matches(
            filtered_parts=filtered_parts,
            patterns=charter_patterns,
            result_key="charters",
            result=result,
        )

        # Process each category using the extracted helper method
        keyword_mapping = {
            "directives": "Directive",
            "regulations": "Regulation",
            "treaties": "Treaty",
            "charters": "Charter",
        }

        # Clean, filter standalone keywords, and deduplicate all categories
        for key in ["directives", "regulations", "treaties", "charters"]:
            self._process_legislation_category(key, result, keyword_mapping)

        # Remove empty keys from result
        result = {key: value for key, value in result.items() if value}

        if not result:
            return None

        return json.dumps(result, indent=2, ensure_ascii=False)
