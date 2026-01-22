"""
CELEX Translator Module

Translates various EU legislation references (Directives, Regulations) to CELEX format.
"""

import json
import pandas as pd
from typing import List, Dict, Optional


class CelexTranslator:
    """
    Translates various EU legislation references to CELEX format.
    """

    def __init__(self, referenced_legislation_by_id: List):
        """
        Initialize the translator with legislation references.

        Args:
            referenced_legislation_by_id: List of JSON strings with legislation references
        """
        self.referenced_legislation_by_id = referenced_legislation_by_id
        self.celex_ids: List[str] = []
        self.unresolved_references: List[Dict] = []

    @staticmethod
    def parse_referenced_legislation(json_str: str) -> Dict[str, List[str]]:
        """
        Parse JSON string of referenced legislation into a dictionary.

        Args:
            json_str: JSON string containing legislation references

        Returns:
            Dictionary with keys like 'CELEX', 'Article', 'Directive', etc.
        """
        if pd.isna(json_str):
            return {}

        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            return {}

    @staticmethod
    def convert_directive_to_celex(directive: str) -> Optional[str]:
        """
        Convert Directive reference to CELEX format.
        Directive format: YYYY/XX/EU -> 3YYYYL00XX

        Args:
            directive: Directive number (e.g., "2010/63/EU")

        Returns:
            CELEX number or None if conversion fails
        """
        parts = directive.replace("/EU", "").split("/")
        if len(parts) == 2:
            year, num = parts
            return f"3{year}L{num.zfill(4)}"
        return None

    @staticmethod
    def convert_regulation_to_celex(regulation: str) -> Optional[str]:
        """
        Convert Regulation reference to CELEX format.
        Regulation format: XXX/YYYY -> 3YYYYRXXXX

        Args:
            regulation: Regulation number (e.g., "178/2002")

        Returns:
            CELEX number or None if conversion fails
        """
        parts = regulation.split("/")
        if len(parts) == 2:
            num, year = parts
            return f"3{year}R{num.zfill(4)}"
        return None

    def extract_all_celex_ids(self) -> tuple[List[str], List[Dict]]:
        """
        Extract all CELEX IDs including conversions from Directives/Regulations.

        Returns:
            Tuple of (unique CELEX IDs, unresolved references)
        """
        celex_ids = []
        unresolved_references = []

        for item in self.referenced_legislation_by_id:
            parsed = self.parse_referenced_legislation(item)

            if "CELEX" in parsed:
                celex_ids.extend(parsed["CELEX"])

            if "Directive" in parsed:
                for directive in parsed["Directive"]:
                    converted = self.convert_directive_to_celex(directive)
                    if converted:
                        celex_ids.append(converted)
                    else:
                        unresolved_references.append(
                            {"type": "Directive", "value": directive}
                        )

            if "Regulation" in parsed:
                for regulation in parsed["Regulation"]:
                    converted = self.convert_regulation_to_celex(regulation)
                    if converted:
                        celex_ids.append(converted)
                    else:
                        unresolved_references.append(
                            {"type": "Regulation", "value": regulation}
                        )

            if (
                "Article" in parsed
                and "CELEX" not in parsed
                and "Directive" not in parsed
                and "Regulation" not in parsed
            ):
                for article in parsed["Article"]:
                    unresolved_references.append({"type": "Article", "value": article})

        self.celex_ids = list(set(celex_ids))
        self.unresolved_references = unresolved_references

        return self.celex_ids, self.unresolved_references
