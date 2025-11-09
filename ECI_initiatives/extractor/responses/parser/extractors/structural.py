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

        # EU Legislation Components
        EU_LEGISLATION_PREPOSITIONS = r"(?:of|and|the|for|on|in|to)"
        EU_NAME_SPACERS = r"(?:\s+(?:of|and|the|for|on|in|to)|\s*[\'‐]\s*)"
        EU_PUNCTUATION_LINKS = r"\s*[\'\-]\s*"

        # Title case patterns for directive/regulation names
        TITLE_CASE_WORD = r"[A-Z]\w*"
        LEGISLATION_NAME_ENDING = rf"(?:{EU_NAME_SPACERS}|{EU_PUNCTUATION_LINKS})"

        # Core pattern for EU legislation names, catches:
        #
        # "Drinking Water Directive", "Floods Directive", "Water Framework Directive",
        # "Sustainable Use Directive", "AVMSD Directive", "Audiovisual Media Services Directive",
        # "Cosmetic Products Regulation", "EU Cosmetics Regulation", "REACH Regulation",
        # "General Food Law Regulation", "Common Provisions Regulation", "ECI Regulation",
        # "Nature Restoration Law", "Sustainable Use of Plant Protection Products Regulation"

        EU_LEGISLATION_NAME_PATTERN = (
            rf"\b{TITLE_CASE_WORD}(?:{EU_NAME_SPACERS}?{TITLE_CASE_WORD})*"
            rf"(?:{LEGISLATION_NAME_ENDING}?{TITLE_CASE_WORD})*"
        )

        # Regex patterns for treaty extraction, catches:
        #
        # "TEU", "TFEU", "Treaty on the European Union",
        # "Treaty on Functioning of the European Union", "Lisbon Treaty", "Maastricht Treaty"
        TREATY_PATTERNS = [
            r"Treaty\s+on\s+(?:the\s+)?(?:European\s+Union|Functioning\s+of\s+the\s+European\s+Union)",
            r"\b(TEU|TFEU)\b",
            r"\b([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+){{0,5}})\s+Treaty\b",
        ]

        # Regex patterns for charter extraction, catches:
        #
        # "Charter of Fundamental Rights", "Charter of Fundamental Rights of the European Union",
        # "European Social Charter", "Youth Charter"
        CHARTER_PATTERNS = [
            r"Charter\s+of\s+(?:the\s+)?Fundamental\s+Rights(?:\s+of\s+the\s+European\s+Union)?",
            r"\b([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+){{0,5}})\s+Charter\b",
        ]

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
                filtered_parts: List of text parts containing legislation keywords
                patterns: List of regex patterns to match against
                result_key: The key in result dict to store matches (e.g., "treaties", "charters")
                result: The result dictionary to append matches to
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

        # Clean up: remove leading articles
        def clean_leading_articles(items: List[str]) -> List[str]:
            """Remove leading articles from each item"""
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

        def filter_standalone_keywords(items: List[str], keyword: str) -> List[str]:
            """Remove items that are just the keyword alone or with common prefixes"""
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
                if item_lower in [
                    variation.lower() for variation in standalone_variations
                ]:
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

        # Deduplicate (case-insensitive)
        def deduplicate_items(items: List[str]) -> List[str]:
            """Remove duplicates (case-insensitive)"""

            seen = set()
            unique = []

            for item in items:
                item_lower = item.lower()

                if item_lower not in seen:
                    seen.add(item_lower)
                    unique.append(item)

            return sorted(unique)

        def split_multiple_legislations(items: List[str], keyword: str) -> List[str]:
            """
            Split items that contain multiple legislations connected by 'and', 'or', or newlines.
            Removes the original combined items.

            Example:
                Input: ["Water Framework Directive and Floods Directive", "Birds Directive"]
                Output: ["Water Framework Directive", "Floods Directive", "Birds Directive"]
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
                            rf"\b{{{re.escape(keyword)}}}\b",
                            newline_part,
                            re.IGNORECASE,
                        )
                    )

                    if keyword_count > 1:

                        # Multiple keywords found - split and DON'T keep the original
                        parts = re.split(
                            rf"\b{{{re.escape(keyword)}}}\b",
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

        # Step 1: Process HTML and extract text
        def _process_html_to_text(self, soup: BeautifulSoup) -> str:
            """Unwrap strong tags and extract text with newlines."""
            # Unwrap all <strong> tags (removes tag but keeps text)
            for strong_tag in soup.find_all("strong"):
                strong_tag.unwrap()

            # Now apply newline separator to all remaining tags
            return soup.get_text(separator="\n", strip=True)

        # Step 2: Split text into sentence parts
        def _split_into_sentence_parts(self, text: str) -> List[str]:
            """Split text by sentence dividers (. ; ,)."""
            return re.split(r"[.;,]", text)

        # Step 3: Filter parts containing legislation keywords
        def _filter_legislation_parts(self, sentence_parts: List[str]) -> List[str]:
            """Filter sentence parts that contain legislation keywords."""
            keywords = ["Directive", "Regulation", "Law", "Treaty", "Charter"]
            filtered_parts = []

            for part in sentence_parts:
                if any(keyword in part for keyword in keywords):
                    filtered_parts.append(part.strip())

            return filtered_parts

        # Step 4: Create directive and regulation patterns
        def _create_legislation_patterns(
            self, base_pattern: str, ending_pattern: str
        ) -> tuple[str, str]:
            """Create regex patterns for directives and regulations."""
            directive_pattern = base_pattern + rf"(?:{ending_pattern}?\s*Directive)\b"

            regulation_pattern = base_pattern + rf"(?:{ending_pattern}?\s*Regulation)\b"

            return directive_pattern, regulation_pattern

        # Step 5: Extract directives and regulations
        def _extract_directives_and_regulations(
            self,
            filtered_parts: List[str],
            directive_pattern: str,
            regulation_pattern: str,
            result: Dict[str, List[str]],
        ) -> None:
            """Extract directive and regulation references from filtered parts."""
            for part in filtered_parts:
                # Extract directives
                directive_matches = re.findall(directive_pattern, part)
                for match in directive_matches:
                    result["directives"].append(match.strip())

                # Extract regulations
                regulation_matches = re.findall(regulation_pattern, part)
                for match in regulation_matches:
                    result["regulations"].append(match.strip())

        # Step 6: Extract pattern-based references (treaties, charters)
        def _extract_pattern_based_references(
            self, filtered_parts: List[str], result: Dict[str, List[str]]
        ) -> None:
            """Extract treaty and charter references using pattern matching."""
            # Extract treaties using specific patterns
            _extract_pattern_matches(
                filtered_parts=filtered_parts,
                patterns=TREATY_PATTERNS,
                result_key="treaties",
                result=result,
            )

            # Extract charters using specific patterns
            _extract_pattern_matches(
                filtered_parts=filtered_parts,
                patterns=CHARTER_PATTERNS,
                result_key="charters",
                result=result,
            )

        # Step 7: Process and clean results
        def _process_and_clean_results(
            self, result: Dict[str, List[str]]
        ) -> Dict[str, List[str]]:
            """Apply cleaning, filtering, and deduplication to all result categories."""
            for key in ["directives", "regulations", "treaties", "charters"]:
                # Clean leading articles
                result[key] = clean_leading_articles(result[key])

                # Apply category-specific processing
                if key == "directives":
                    items = split_multiple_legislations(result[key], "Directive")
                    items = filter_standalone_keywords(items, "Directive")
                    result[key] = items
                elif key == "regulations":
                    items = split_multiple_legislations(result[key], "Regulation")
                    items = filter_standalone_keywords(items, "Regulation")
                    result[key] = items
                elif key == "treaties":
                    items = split_multiple_legislations(result[key], "Treaty")
                    items = filter_standalone_keywords(items, "Treaty")
                    result[key] = items
                elif key == "charters":
                    items = split_multiple_legislations(result[key], "Charter")
                    items = filter_standalone_keywords(items, "Charter")
                    result[key] = items

                # Deduplicate items
                result[key] = deduplicate_items(result[key])

            # Remove empty keys from result
            return {key: value for key, value in result.items() if value}

        result = {
            "treaties": [],
            "charters": [],
            "directives": [],
            "regulations": [],
        }

        text = _process_html_to_text(soup)

        sentence_parts = _split_into_sentence_parts(text)

        filtered_parts = _filter_legislation_parts(sentence_parts)

        directive_pattern, regulation_pattern = _create_legislation_patterns(
            base_pattern, ending_pattern
        )

        _extract_directives_and_regulations(
            filtered_parts, directive_pattern, regulation_pattern, result
        )

        _extract_pattern_based_references(filtered_parts, result)

        cleaned_result = _process_and_clean_results(result)

        # Return JSON or None if no results
        if not cleaned_result:
            return None

        return json.dumps(cleaned_result, indent=2, ensure_ascii=False)

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
