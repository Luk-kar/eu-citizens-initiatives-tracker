"""
Performs structural analysis by extracting related
EU legislation references, petition platforms used, and
calculating follow-up durations.
"""

import re
import json
from typing import Optional, Dict, List, Union
from urllib.parse import unquote

from bs4 import BeautifulSoup

from ..base.base_extractor import BaseExtractor


class StructuralAnalysisExtractor(BaseExtractor):
    """Extracts structural analysis data"""

    def extract_referenced_legislation_by_id(
        self, soup: BeautifulSoup
    ) -> Optional[str]:
        """Extract references to specific Regulations or Directives by number/id"""
        try:

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
                "a", href=re.compile(r"uriserv", re.IGNORECASE)
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

    def calculate_follow_up_duration_months(self, soup: BeautifulSoup) -> Optional[str]:
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
            JSON string with follow-up actions and dates, or None if no follow-up section exists

        Raises:
            ValueError: If critical error occurs during extraction
        """
        try:
            # Find the Follow-up section
            followup_section = self._find_followup_section(soup)
            if not followup_section:
                return None

            section_marker = followup_section["marker"]
            section_element = followup_section["element"]

            # Collect and process follow-up actions
            follow_up_actions = self._extract_followup_actions(
                section_element, section_marker
            )

            if not follow_up_actions:
                return None

            return json.dumps(follow_up_actions, ensure_ascii=False)

        except Exception as e:
            raise ValueError(
                f"Error calculating follow-up duration for {self.registration_number}: {str(e)}"
            ) from e

    def _find_followup_section(self, soup: BeautifulSoup) -> Optional[Dict[str, str]]:
        """
        Find the Follow-up section in the HTML.

        Args:
            soup: BeautifulSoup object of the HTML document

        Returns:
            Dictionary with 'element' and 'marker' keys, or None if not found
        """
        # Try h2 first (primary pattern)
        for h2 in soup.find_all("h2"):
            if "Follow-up" in h2.get_text():
                return {"element": h2, "marker": "h2"}

        # If not found, try h4 (secondary pattern)
        for h4 in soup.find_all("h4"):
            if "Follow-up" in h4.get_text():
                return {"element": h4, "marker": "h4"}

        return None

    def _extract_followup_actions(
        self, section_element, section_marker: str
    ) -> List[Dict[str, Union[List[str], str]]]:
        """
        Extract follow-up actions from the Follow-up section.

        Args:
            section_element: BeautifulSoup element of the Follow-up header
            section_marker: Type of header ('h2' or 'h4')

        Returns:
            List of dictionaries with 'dates' and 'action' keys
        """
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
        action_text = element.get_text(separator=" ", strip=True)
        action_text = re.sub(r"\s+", " ", action_text)

        # Skip very short content
        if len(action_text) < 30:
            return None

        # Skip generic intro paragraphs or subsection headers
        if self._should_skip_text(action_text):
            return None

        # Extract dates from the text
        dates = self._extract_dates_from_text(action_text)

        return {"dates": dates, "action": action_text}

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
            action_text = re.sub(r"\s+", " ", action_text)

            # Skip very short items
            if len(action_text) < 30:
                continue

            # Extract dates from the text
            dates = self._extract_dates_from_text(action_text)

            actions.append({"dates": dates, "action": action_text})

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

        # Also skip if it's just a subsection header (ends with colon and is short)
        if text.endswith(":") and len(text) < 100:
            return True

        return False

    def _extract_dates_from_text(self, text: str) -> List[str]:
        """
        Extract and normalize dates from text to ISO 8601 format.

        Only keeps the most specific date at each text position to avoid duplicates
        (e.g., if "01 February 2018" is found, "February 2018" won't be extracted).

        Supported formats:
        - DD Month YYYY (e.g., "28 October 2015") → YYYY-MM-DD
        - Month YYYY (e.g., "February 2018") → YYYY-MM-01
        - YYYY (e.g., "2021") → YYYY-01-01

        Args:
            text: Text content to extract dates from

        Returns:
            List of ISO 8601 formatted date strings
        """
        from datetime import datetime
        import calendar

        # Date patterns ordered by specificity (most specific first)
        date_patterns = [
            # DD Month YYYY (e.g., "28 October 2015", "01 February 2018")
            (
                r"\b(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})\b",
                "dmy",
            ),
            # Month YYYY (e.g., "February 2018", "October 2015")
            (
                r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})\b",
                "my",
            ),
            # YYYY only (e.g., "2021", "2023")
            (r"\b(20\d{2})\b", "y"),
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
            date_type: Type of date format ('dmy', 'my', or 'y')

        Returns:
            ISO 8601 formatted date string (YYYY-MM-DD), or None if parsing fails
        """
        from datetime import datetime
        import calendar

        try:
            if date_type == "dmy":
                # DD Month YYYY format
                day = int(match.group(1))
                month_name = match.group(2).capitalize()
                year = int(match.group(3))

                # Convert month name to number using datetime
                month = datetime.strptime(month_name, "%B").month

                # Validate day is within valid range for the month
                max_day = calendar.monthrange(year, month)[1]
                if day > max_day:
                    return None

                return f"{year:04d}-{month:02d}-{day:02d}"

            elif date_type == "my":
                # Month YYYY format
                month_name = match.group(1).capitalize()
                year = int(match.group(2))

                # Convert month name to number using datetime
                month = datetime.strptime(month_name, "%B").month

                return f"{year:04d}-{month:02d}-01"

            elif date_type == "y":
                # YYYY format
                year = int(match.group(1))
                return f"{year:04d}-01-01"

        except (ValueError, AttributeError):
            return None

        return None


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

                # print([item, item_lower, prefix.lower(), keyword.lower()])

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

    def _deduplicate_items(self, category: str, items: List[str]) -> List[str]:
        """
        Remove duplicates (case-insensitive) and return sorted unique items.
        Also removes abbreviation + type duplicates (e.g., "REACH" when "REACH Regulation" exists).

        Args:
            category: The category key ("treaties", "charters", "directives", "regulations")
            items: List of legislation strings

        Returns:
            Sorted list of unique items
        """
        if not items:
            return []

        # 1. Remove exact duplicates (case-insensitive)
        seen = set()
        unique = []

        for item in items:
            item_stripped = item.strip()  # Strip whitespace first
            item_lower = item_stripped.lower()

            if item_lower not in seen and item_stripped:  # Also check non-empty
                seen.add(item_lower)
                unique.append(item_stripped)  # Append stripped version

        # 2. Remove duplicates with abbreviation + legislative_type
        # like in "REACH", "REACH Regulation"
        # remove the standalone "REACH" and keep "REACH Regulation"
        category_to_type = {
            "treaties": "Treaty",
            "charters": "Charter",
            "directives": "Directive",
            "regulations": "Regulation",
        }

        legislative_type = category_to_type.get(category, "")

        if not legislative_type:
            # If category not recognized, just return unique items sorted
            return sorted(unique)

        items_to_remove = []

        for item in unique:
            # Check if this item appears with the legislative type suffix in the list
            # e.g., if item is "REACH", check if "REACH Regulation" exists
            potential_full_form = f"{item} {legislative_type}"

            # Check if the full form exists in the list (case-insensitive)
            for other_item in unique:
                if (
                    other_item.lower() == potential_full_form.lower()
                    and other_item != item
                ):
                    # Found "REACH Regulation" when checking "REACH"
                    # Mark the standalone abbreviation for removal
                    items_to_remove.append(item)
                    break

        # Remove the marked items
        final_items = [item for item in unique if item not in items_to_remove]

        return sorted(final_items)

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
                            r"\s*\b(?:and|or)\b\s*$", "", part, flags=re.IGNORECASE
                        )

                        # Remove leading conjunction from the part
                        part = re.sub(
                            r"^\s*\b(?:and|or)\b\s*", "", part, flags=re.IGNORECASE
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

    def _preprocess_html(self, soup: BeautifulSoup) -> BeautifulSoup:
        """
        Preprocess HTML by unwrapping strong tags to flatten text structure.

        Args:
            soup: BeautifulSoup object of the HTML document

        Returns:
            Modified BeautifulSoup object with unwrapped strong tags
        """
        for strong_tag in soup.find_all("strong"):
            strong_tag.unwrap()
        return soup

    def _extract_text_parts(self, soup: BeautifulSoup) -> tuple[List[str], List[str]]:
        """
        Extract text from HTML and split into sentence parts.

        Args:
            soup: Preprocessed BeautifulSoup object

        Returns:
            Tuple of (all sentence parts, filtered parts containing legislation keywords)
        """
        # Extract text with newline separation
        full_text = soup.get_text(separator="\n", strip=True)

        # Step 1: Divide text into parts by sentence dividers (. ; ,)
        sentence_parts = re.split(r"[.;,]", full_text)

        # Step 2: Filter out parts containing legislation keywords
        keywords = ["Directive", "Regulation", "Law", "Treaty", "Charter"]
        filtered_parts = []

        for part in sentence_parts:
            if any(keyword in part for keyword in keywords):
                filtered_parts.append(part.strip())

        return full_text, filtered_parts

    def _extract_directives_and_regulations(
        self, filtered_parts: List[str], result: Dict[str, List[str]]
    ) -> None:
        """
        Extract directives and regulations using dynamic regex patterns.

        Args:
            filtered_parts: Filtered text parts containing potential legislation
            result: Result dictionary to populate with matches
        """
        # Create patterns for directives and regulations
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

    def _extract_treaty_abbreviations(
        self, full_text: str, result: Dict[str, List[str]]
    ) -> None:
        """
        Extract direct treaty abbreviations (TEU, TFEU) from full text.
        This ensures critical treaty codes aren't missed by complex patterns.

        Args:
            full_text: Complete document text to search
            result: Result dictionary to add matches to treaties category
        """
        primary_treaties = [
            "TEU",  # Treaty on European Union
            "TFEU",  # Treaty on the Functioning of the European Union
        ]

        # Historical treaties (Maastricht, Amsterdam, Nice, Lisbon)
        historical_treaties = [
            "MA",  # Maastricht Treaty
            "AM",  # Amsterdam Treaty
            "NI",  # Nice Treaty
            "LI",  # Lisbon Treaty
        ]

        # Other important EU treaty references
        # but no relevance to the ECI functioning
        # avoid it not to create false positive cases
        #   - Single European Act
        #   - Treaty establishing the European Community
        #   - Treaty establishing the European Atomic Energy Community

        # Combine all treaty abbreviation lists
        all_treaty_abbreviations = primary_treaties + historical_treaties

        # Construct the alternation pattern dynamically
        # Escape special regex characters and join with | (OR operator)
        escaped_abbreviations = [re.escape(abbr) for abbr in all_treaty_abbreviations]
        alternation_pattern = "|".join(escaped_abbreviations)

        # Build the complete word boundary pattern
        treaty_abbr_pattern = rf"\b({alternation_pattern})\b"

        # Find all treaty abbreviations in the full text
        matches = re.findall(treaty_abbr_pattern, full_text, re.IGNORECASE)

        # Add unique matches to treaties category
        for match in matches:
            abbr = match.upper().strip()
            if abbr not in result["treaties"]:
                result["treaties"].append(abbr)

    def _extract_charter_abbreviations(
        self, full_text: str, result: Dict[str, List[str]]
    ) -> None:
        """
        Extract direct charter abbreviations (CFR, etc.) from full text.
        This ensures critical charter codes aren't missed by complex patterns.

        Args:
            full_text: Complete document text to search
            result: Result dictionary to add matches to charters category
        """
        # Primary EU charter abbreviations
        primary_charters = [
            "CFR",  # Charter of Fundamental Rights
        ]

        # Other important charter references
        other_charters = [
            "ECHR",  # European Convention on Human Rights (often referenced alongside CFR)
        ]

        # Combine all charter abbreviation lists
        all_charter_abbreviations = primary_charters + other_charters

        # Construct the alternation pattern dynamically
        # Escape special regex characters and join with | (OR operator)
        escaped_abbreviations = [re.escape(abbr) for abbr in all_charter_abbreviations]
        alternation_pattern = "|".join(escaped_abbreviations)

        # Build the complete word boundary pattern
        charter_abbr_pattern = rf"\b({alternation_pattern})\b"

        # Find all charter abbreviations in the full text
        matches = re.findall(charter_abbr_pattern, full_text, re.IGNORECASE)

        # Add unique matches to charters category
        for match in matches:
            abbr = match.upper().strip()
            if abbr and abbr not in result["charters"]:
                result["charters"].append(abbr)

    def _extract_directive_abbreviations(
        self, full_text: str, result: Dict[str, List[str]]
    ) -> None:
        """
        Extract direct directive abbreviations (WFD, BHD, etc.) from full text.
        This ensures critical directive codes aren't missed by complex patterns.

        Args:
            full_text: Complete document text to search
            result: Result dictionary to add matches to directives category
        """
        # Primary environmental directives
        environmental_directives = [
            "WFD",  # Water Framework Directive (2000/60/EC)
            "BHD",  # Birds and Habitats Directives
            "FWD",  # Floods Directive (2007/60/EC)
            "NWD",  # Nitrates Directive (91/676/EEC)
            "UWWTD",  # Urban Waste Water Treatment Directive (91/271/EEC)
        ]

        # Air quality and emissions directives
        air_quality_directives = [
            "AQD",  # Ambient Air Quality Directive (2008/50/EC)
            "NEC",  # National Emission Ceilings Directive (2016/2284/EU)
            "IED",  # Industrial Emissions Directive (2010/75/EU)
        ]

        # Other important directives
        other_directives = [
            "Aarhus",  # Aarhus Convention Implementation (2003/4/EC)
            "EIA",  # Environmental Impact Assessment Directive (2011/92/EU)
            "SEA",  # Strategic Environmental Assessment Directive (2001/42/EC)
            "IPPC",  # Integrated Pollution Prevention and Control (now IED)
        ]

        # Combine all directive abbreviation lists
        all_directive_abbreviations = (
            environmental_directives + air_quality_directives + other_directives
        )

        # Construct the alternation pattern dynamically
        escaped_abbreviations = [
            re.escape(abbr) for abbr in all_directive_abbreviations
        ]
        alternation_pattern = "|".join(escaped_abbreviations)

        # Build the complete word boundary pattern
        directive_abbr_pattern = rf"\b({alternation_pattern})\b"

        # Find all directive abbreviations in the full text
        matches = re.findall(directive_abbr_pattern, full_text, re.IGNORECASE)

        # Add unique matches to directives category
        for match in matches:
            abbr = match.upper().strip()
            if abbr and abbr not in result["directives"]:
                result["directives"].append(abbr)

    def _extract_regulation_abbreviations(
        self, full_text: str, result: Dict[str, List[str]]
    ) -> None:
        """
        Extract direct regulation abbreviations (REACH, GDPR, etc.) from full text.
        This ensures critical regulation codes aren't missed by complex patterns.

        Args:
            full_text: Complete document text to search
            result: Result dictionary to add matches to regulations category
        """
        # Primary data protection and chemicals regulations
        data_chemicals_regs = [
            "GDPR",  # General Data Protection Regulation (2016/679)
            "REACH",  # Registration, Evaluation, Authorisation and Restriction of Chemicals (1907/2006)
            "RoHS",  # Restriction of Hazardous Substances (2011/65/EU)
            "WEEE",  # Waste Electrical and Electronic Equipment (2012/19/EU)
        ]

        # Financial regulations
        financial_regs = [
            "EMIR",  # European Market Infrastructure Regulation (648/2012)
            "MiFIR",  # Markets in Financial Instruments Regulation (600/2014)
            "CRR",  # Capital Requirements Regulation (575/2013)
            "CRD",  # Capital Requirements Directive (but often referenced as regulation)
        ]

        # Environmental and climate regulations
        environmental_regs = [
            "ETS",  # Emissions Trading System Regulation
            "FQD",  # Fuel Quality Directive (but often treated as regulation context)
            "LULUCF",  # Land Use, Land-Use Change and Forestry Regulation
        ]

        # Other important regulations
        other_regulations = [
            "PIC",  # Prior Informed Consent Regulation (649/2012)
            "POPs",  # Persistent Organic Pollutants Regulation (850/2004)
            "CLP",  # Classification, Labelling and Packaging Regulation (1272/2008)
            "Biocides",  # Biocidal Products Regulation (528/2012)
        ]

        # Combine all regulation abbreviation lists
        all_regulation_abbreviations = (
            data_chemicals_regs
            + financial_regs
            + environmental_regs
            + other_regulations
        )

        # Construct the alternation pattern dynamically
        escaped_abbreviations = [
            re.escape(abbr) for abbr in all_regulation_abbreviations
        ]
        alternation_pattern = "|".join(escaped_abbreviations)

        # Build the complete word boundary pattern
        regulation_abbr_pattern = rf"\b({alternation_pattern})\b"

        # Find all regulation abbreviations in the full text
        matches = re.findall(regulation_abbr_pattern, full_text, re.IGNORECASE)

        # Add unique matches to regulations category
        for match in matches:
            abbr = match.upper().strip()
            if abbr and abbr not in result["regulations"]:
                result["regulations"].append(abbr)

    def _extract_treaties(
        self, filtered_parts: List[str], result: Dict[str, List[str]]
    ) -> None:
        """
        Extract treaty references using specific treaty patterns.

        Args:
            filtered_parts: Filtered text parts containing potential legislation
            result: Result dictionary to populate with matches
        """
        treaty_patterns = [
            r"Treaty\s+on\s+(?:the\s+)?(?:European\s+Union|Functioning\s+of\s+the\s+European\s+Union)",
            r"\b((?:[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+){0,5})\s+Treaty)\b",
        ]

        self._extract_pattern_matches(
            filtered_parts=filtered_parts,
            patterns=treaty_patterns,
            result_key="treaties",
            result=result,
        )

    def _extract_charters(
        self, filtered_parts: List[str], result: Dict[str, List[str]]
    ) -> None:
        """
        Extract charter references using specific charter patterns.

        Args:
            filtered_parts: Filtered text parts containing potential legislation
            result: Result dictionary to populate with matches
        """
        charter_patterns = [
            r"Charter\s+of\s+(?:the\s+)?Fundamental\s+Rights(?:\s+of\s+the\s+European\s+Union)?",
            r"\b((?:[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+){0,5})\s+Charter)\b",
        ]

        self._extract_pattern_matches(
            filtered_parts=filtered_parts,
            patterns=charter_patterns,
            result_key="charters",
            result=result,
        )

    def _postprocess_legislation_categories(
        self, result: Dict[str, List[str]]
    ) -> Dict[str, List[str]]:
        """
        Process all legislation categories: clean, filter, and deduplicate.

        Args:
            result: Result dictionary with raw extracted matches

        Returns:
            Processed result dictionary with cleaned and deduplicated categories
        """
        keyword_mapping = {
            "directives": "Directive",
            "regulations": "Regulation",
            "treaties": "Treaty",
            "charters": "Charter",
        }

        # Clean, filter standalone keywords, and deduplicate all categories
        for key in keyword_mapping.keys():
            self._process_legislation_category(key, result, keyword_mapping)

        # Remove empty keys from result
        result = {key: value for key, value in result.items() if value}
        return result

    def _serialize_result(self, result: Dict[str, List[str]]) -> Optional[str]:
        """
        Serialize the processed result to JSON, or return None if empty.

        Args:
            result: Processed result dictionary

        Returns:
            JSON string representation or None if no results
        """
        if not result:
            return None

        return json.dumps(result, indent=2, ensure_ascii=False)

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
        soup = self._preprocess_html(soup)

        full_text, filtered_parts = self._extract_text_parts(soup)

        result: Dict[str, List[str]] = {
            "treaties": [],
            "charters": [],
            "directives": [],
            "regulations": [],
        }

        # Extract treaty abbreviations directly (before complex patterns)
        self._extract_treaty_abbreviations(full_text, result)
        self._extract_charter_abbreviations(full_text, result)
        self._extract_directive_abbreviations(full_text, result)
        self._extract_regulation_abbreviations(full_text, result)

        # Extract specific legislation types results
        self._extract_directives_and_regulations(filtered_parts, result)
        self._extract_treaties(filtered_parts, result)
        self._extract_charters(filtered_parts, result)

        # Normalize
        result = self._postprocess_legislation_categories(result)

        # Remove duplicates
        for category, items in result.items():
            result[category] = self._deduplicate_items(category, items)

        return self._serialize_result(result)
