"""
Test suite for ECI model data quality: Actions data structure validation.

These tests validate actions data structure validation in extracted
European Citizens' Initiative response data.
"""

from datetime import datetime, date, timedelta
from typing import List, Optional, Any, Set
from urllib.parse import urlparse, ParseResult
import json
import pytest
import re

from ECI_initiatives.extractor.responses.model import ECICommissionResponseRecord


class TestActionsDataStructure:
    """Test structure and quality of laws_actions and policies_actions"""

    # ISO 8601 date format pattern (YYYY-MM-DD)
    ISO_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")

    def _parse_json_safely(self, json_string: Optional[str]) -> Optional[any]:
        """
        Parse JSON string, returning None if invalid or empty.

        Args:
            json_string: JSON string to parse

        Returns:
            Parsed object or None
        """
        if json_string is None:
            return None

        if isinstance(json_string, str):
            if json_string.strip() in ("", "null", "[]", "{}"):
                return None

        try:
            parsed = json.loads(json_string)
            if not parsed:
                return None
            return parsed
        except (json.JSONDecodeError, TypeError):
            return None

    def _validate_date_format(self, date_string: str) -> bool:
        """
        Validate that a date string follows ISO 8601 format (YYYY-MM-DD).

        Args:
            date_string: Date string to validate

        Returns:
            True if valid ISO date format
        """
        if not self.ISO_DATE_PATTERN.match(date_string):
            return False

        # Also validate it's a real date (not 2024-13-45)
        try:
            datetime.strptime(date_string, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    def _validate_url_structure(self, url: str) -> bool:
        """
        Validate that a URL has proper structure.

        Args:
            url: URL string to validate

        Returns:
            True if valid URL structure
        """
        if not url or not isinstance(url, str):
            return False

        try:
            parsed = urlparse(url)
            # Must have scheme (http/https) and netloc (domain)
            return bool(parsed.scheme in ("http", "https") and parsed.netloc)

        except Exception:
            return False

    def test_action_dates_are_valid_when_present(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """
        Verify date fields within action objects follow ISO format.

        Both laws_actions and policies_actions can contain date fields (e.g., 'date',
        'implementation_date', 'adoption_date') that must follow ISO 8601 format
        (YYYY-MM-DD) for consistency and parseability.
        """
        invalid_dates = []

        for record in complete_dataset:

            # Check laws_actions
            laws = self._parse_json_safely(record.laws_actions)

            if laws and isinstance(laws, list):
                for i, action in enumerate(laws):
                    if isinstance(action, dict):
                        # Check common date fields in law actions
                        date_fields = [
                            "date",
                            "implementation_date",
                            "adoption_date",
                            "entry_into_force",
                        ]

                        for field_name in date_fields:
                            if field_name in action and action[field_name]:
                                date_value = action[field_name]
                                if not self._validate_date_format(date_value):
                                    invalid_dates.append(
                                        (
                                            record.registration_number,
                                            f"laws_actions[{i}].{field_name}",
                                            date_value,
                                        )
                                    )

            # Check policies_actions
            policies = self._parse_json_safely(record.policies_actions)

            if policies and isinstance(policies, list):
                for i, action in enumerate(policies):
                    if isinstance(action, dict):
                        # Check common date fields in policy actions
                        date_fields = [
                            "date",
                            "implementation_date",
                            "adoption_date",
                            "deadline",
                        ]

                        for field_name in date_fields:
                            if field_name in action and action[field_name]:
                                date_value = action[field_name]
                                if not self._validate_date_format(date_value):
                                    invalid_dates.append(
                                        (
                                            record.registration_number,
                                            f"policies_actions[{i}].{field_name}",
                                            date_value,
                                        )
                                    )

        assert not invalid_dates, (
            f"Found {len(invalid_dates)} action date fields with invalid ISO format:\n"
            + "\n".join(
                f"  - {reg_num} {field}: '{date_value}' (expected YYYY-MM-DD)"
                for reg_num, field, date_value in invalid_dates
            )
            + "\n\nAll dates must follow ISO 8601 format (YYYY-MM-DD) for consistency."
        )

    def test_action_document_urls_are_valid_when_present(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """
        Verify document_url fields in action objects are valid URLs.

        Actions may reference supporting documents (legislation texts, policy papers,
        etc.) via URL fields. These URLs must be properly formatted with http/https
        scheme and valid domain for accessibility and verification.
        """
        invalid_urls = []

        for record in complete_dataset:

            # Check laws_actions
            laws = self._parse_json_safely(record.laws_actions)

            if laws and isinstance(laws, list):

                for i, action in enumerate(laws):
                    if isinstance(action, dict):

                        # Check common URL fields in law actions
                        url_fields = ["document_url", "url", "link", "legislation_url"]

                        for field_name in url_fields:

                            if field_name in action and action[field_name]:

                                url_value = action[field_name]

                                if not self._validate_url_structure(url_value):

                                    invalid_urls.append(
                                        (
                                            record.registration_number,
                                            f"laws_actions[{i}].{field_name}",
                                            (
                                                url_value[:100]
                                                if isinstance(url_value, str)
                                                else str(url_value)
                                            ),
                                        )
                                    )

            # Check policies_actions
            policies = self._parse_json_safely(record.policies_actions)

            if policies and isinstance(policies, list):

                for i, action in enumerate(policies):

                    if isinstance(action, dict):

                        # Check common URL fields in policy actions
                        url_fields = ["document_url", "url", "link", "policy_url"]

                        for field_name in url_fields:

                            if field_name in action and action[field_name]:

                                url_value = action[field_name]

                                if not self._validate_url_structure(url_value):
                                    invalid_urls.append(
                                        (
                                            record.registration_number,
                                            f"policies_actions[{i}].{field_name}",
                                            (
                                                url_value[:100]
                                                if isinstance(url_value, str)
                                                else str(url_value)
                                            ),
                                        )
                                    )

        assert not invalid_urls, (
            f"Found {len(invalid_urls)} action URL fields with invalid format:\n"
            + "\n".join(
                f"  - {reg_num} {field}: '{url_value}'"
                for reg_num, field, url_value in invalid_urls
            )
            + "\n\nAll URLs must have proper structure (http/https scheme and valid domain)."
        )
