"""
Shared validation and normalization utilities for ECI data quality tests.

This module provides common helper functions used across multiple data quality
test classes for European Citizens' Initiative (ECI) response data validation.
These utilities handle JSON parsing, date validation, boolean normalization,
and URL structure validation.
"""

# Standard libs
from datetime import datetime
import json
import re
from typing import Any, Optional, List
from urllib.parse import urlparse, ParseResult

# ISO 8601 date format pattern (YYYY-MM-DD)
ISO_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def parse_json_safely(json_string: Optional[str]) -> Optional[Any]:
    """Parse JSON string, returning None if invalid or empty."""

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


def validate_date_format(date_string: str) -> bool:
    """Validate that a date string follows ISO 8601 format (YYYY-MM-DD)."""

    if not ISO_DATE_PATTERN.match(date_string):
        return False

    try:
        datetime.strptime(date_string, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def normalize_boolean(value: Any) -> Optional[bool]:
    """Normalize boolean-like values to actual booleans."""

    if value is None:
        return None

    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        value_lower = value.lower().strip()
        if value_lower in ("true", "1", "yes"):
            return True
        elif value_lower in ("false", "0", "no", ""):
            return False

    if isinstance(value, (int, float)):
        return bool(value)

    return None


def is_empty_value(value: Any) -> bool:
    """Check if a value is considered empty."""

    if value is None:
        return True

    if isinstance(value, str):
        return value.strip() in ("", "null", "[]", "{}")

    if isinstance(value, (list, dict, set, tuple)):
        return len(value) == 0

    return False


def validate_url_structure(
    url: str,
    field_name: str,
    registration_number: str,
) -> ParseResult:
    """Validate URL structure - HTTPS only."""
    parsed = urlparse(url)

    assert parsed.scheme in ["https", "http"], (
        f"{field_name} must use HTTPS or HTTP for {registration_number}: "
        f"got '{parsed.scheme}'"
    )

    assert parsed.netloc, f"Missing domain in {field_name} for {registration_number}"

    return parsed
