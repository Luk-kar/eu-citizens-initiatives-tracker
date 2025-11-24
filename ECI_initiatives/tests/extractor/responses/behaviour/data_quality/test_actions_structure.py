"""
Test suite for ECI model data quality: Actions data structure validation.

These tests validate actions data structure validation in extracted
European Citizens' Initiative response data.
"""

# Standard library
from typing import Any, Callable, List, Tuple, Optional
from urllib.parse import urlparse

# Local
from ECI_initiatives.extractor.responses.model import ECICommissionResponseRecord
from .validation_helpers import (
    parse_json_safely,
    validate_date_format,
)


class TestActionsDataStructure:
    """Test structure and quality of laws_actions and policies_actions"""

    def _is_valid_url(self, url: str) -> bool:
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
            laws = parse_json_safely(record.laws_actions)
            invalid_dates.extend(
                validate_action_fields_in_list(
                    laws,
                    record.registration_number,
                    field_names=[
                        "date",
                        "implementation_date",
                        "adoption_date",
                        "entry_into_force",
                    ],
                    source_name="laws_actions",
                    validator_func=validate_date_format,
                )
            )

            # Check policies_actions
            policies = parse_json_safely(record.policies_actions)
            invalid_dates.extend(
                validate_action_fields_in_list(
                    policies,
                    record.registration_number,
                    field_names=[
                        "date",
                        "implementation_date",
                        "adoption_date",
                        "deadline",
                    ],
                    source_name="policies_actions",
                    validator_func=validate_date_format,
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

        # Value transformer to truncate long URLs for error reporting
        def truncate_url(url):
            return url[:100] if isinstance(url, str) else str(url)

        for record in complete_dataset:

            # Check laws_actions
            laws = parse_json_safely(record.laws_actions)
            invalid_urls.extend(
                validate_action_fields_in_list(
                    laws,
                    record.registration_number,
                    field_names=["document_url", "url", "link", "legislation_url"],
                    source_name="laws_actions",
                    validator_func=self._is_valid_url,
                    value_transformer=truncate_url,
                )
            )

            # Check policies_actions
            policies = parse_json_safely(record.policies_actions)
            invalid_urls.extend(
                validate_action_fields_in_list(
                    policies,
                    record.registration_number,
                    field_names=["document_url", "url", "link", "policy_url"],
                    source_name="policies_actions",
                    validator_func=self._is_valid_url,
                    value_transformer=truncate_url,
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


def validate_action_fields_in_list(
    actions_list: Optional[List[dict]],
    registration_number: str,
    field_names: List[str],
    source_name: str,
    validator_func: Callable[[Any], bool],
    value_transformer: Optional[Callable[[Any], Any]] = None,
) -> List[Tuple[str, str, Any]]:
    """
    Validate specified fields within a list of action dictionaries.

    This helper iterates through action objects, checks specified fields,
    and collects validation errors for any invalid values.

    Args:
        actions_list: List of action dictionaries (already parsed from JSON)
        registration_number: Initiative registration number for error reporting
        field_names: List of field names to validate within each action dict
        source_name: Name of source field for error messages (e.g., 'laws_actions')
        validator_func: Function that takes a field value and returns True if valid
        value_transformer: Optional function to transform value for error reporting
                          (e.g., truncate long URLs)

    Returns:
        List of error tuples: (registration_number, field_path, field_value)

    Example:
        ```
        laws = parse_json_safely(record.laws_actions)
        errors = validate_action_fields_in_list(
            laws,
            record.registration_number,
            ['date', 'adoption_date'],
            'laws_actions',
            validate_date_format
        )
        ```
    """
    errors = []

    if not actions_list or not isinstance(actions_list, list):
        return errors

    for i, action in enumerate(actions_list):
        if not isinstance(action, dict):
            continue

        for field_name in field_names:
            if field_name in action and action[field_name]:
                field_value = action[field_name]

                if not validator_func(field_value):
                    # Transform value for error reporting if transformer provided
                    error_value = (
                        value_transformer(field_value)
                        if value_transformer
                        else field_value
                    )

                    errors.append(
                        (
                            registration_number,
                            f"{source_name}[{i}].{field_name}",
                            error_value,
                        )
                    )

    return errors
