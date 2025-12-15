"""
Field merging strategies for combining base and followup CSV data.
"""

import json
import logging
from typing import Dict, Callable, List
from datetime import datetime

from .exceptions import ImmutableFieldConflictError, MandatoryFieldMissingError

# Setup logger
logger = logging.getLogger(__name__)

# ============================================================================
# JSON Parsing Utility Functions
# ============================================================================


import json
from typing import Any, Callable, Iterable, Type, TypeVar

T = TypeVar("T", list, dict)


def _safe_parse_json_container(
    value: str,
    source: str,
    field_name: str,
    registration_number: str,
    parse_as: Type[T],  # list or dict type object
) -> T:
    """Parse JSON or Python-repr container string.

    Args:
        parse_as: The type to parse as (list or dict)
    """
    empty_values = {"", "{}", "null", "None", "NaN", "nan"}

    # Determine default and container label based on type
    if parse_as is list:
        default = []
        container_label = "list"
    elif parse_as is dict:
        default = {}
        container_label = "dict"
    else:
        raise ValueError(f"Unsupported parse_as type: {parse_as}")

    if value is None:
        return default

    value_stripped = value.strip()
    if not value_stripped or value_stripped in empty_values:
        return default

    # 1) Try strict JSON
    try:
        parsed = json.loads(value_stripped)
        return parsed if isinstance(parsed, parse_as) else default
    except json.JSONDecodeError:
        pass

    # 2) Fallback: attempt to coerce Python repr-ish strings to JSON
    try:
        json_compatible = value_stripped.replace("'", '"')
        parsed = json.loads(json_compatible)
        if isinstance(parsed, parse_as):
            logger.info(
                f"{registration_number} - {field_name}: {source} had Python syntax, converted to JSON"
            )
            return parsed
        return default
    except Exception as e:
        logger.warning(
            f"{registration_number} - {field_name}: Could not parse {source} JSON {container_label}: {e}"
        )
        return default


def safe_parse_json_list(
    value: str, source: str, field_name: str, registration_number: str
) -> list:
    """Parse JSON or Python-repr list string."""
    return _safe_parse_json_container(
        value,
        source,
        field_name,
        registration_number,
        list,
    )


def safe_parse_json_object(
    value: str, source: str, field_name: str, registration_number: str
) -> dict:
    """Parse JSON or Python-repr dict string."""
    return _safe_parse_json_container(
        value,
        source,
        field_name,
        registration_number,
        dict,
    )


# ============================================================================
# Field-Specific Merge Strategies
# ============================================================================


def merge_by_preferring_followup(
    base_value: str, followup_value: str, field_name: str, registration_number: str
) -> str:
    """
    Prefer followup value if non-empty, otherwise use base value.
    Use for fields where followup data is more recent/authoritative.

    Args:
        base_value: Value from base CSV
        followup_value: Value from followup CSV
        field_name: Field name
        registration_number: Registration number

    Returns:
        Merged value
    """
    if (
        followup_value
        and followup_value.strip()
        and followup_value.strip() not in ["", "None", "null"]
    ):
        logger.debug(f"{registration_number} - {field_name}: Using followup value")
        return followup_value
    logger.debug(
        f"{registration_number} - {field_name}: Using base value (followup empty)"
    )
    return base_value


def merge_by_preferring_base(
    base_value: str, followup_value: str, field_name: str, registration_number: str
) -> str:
    """
    Prefer base value if non-empty, otherwise use followup value.
    Use for fields where base data is more authoritative.

    Args:
        base_value: Value from base CSV
        followup_value: Value from followup CSV
        field_name: Field name
        registration_number: Registration number

    Returns:
        Merged value
    """
    if (
        base_value
        and base_value.strip()
        and base_value.strip() not in ["", "None", "null"]
    ):
        logger.debug(f"{registration_number} - {field_name}: Using base value")
        return base_value
    logger.debug(
        f"{registration_number} - {field_name}: Using followup value (base empty)"
    )
    return followup_value


def merge_by_concatenation(
    base_value: str, followup_value: str, field_name: str, registration_number: str
) -> str:
    """
    Concatenate both values if both are non-empty, with proper labeling.
    Use for fields that can accumulate information (e.g., notes, descriptions).

    Args:
        base_value: Value from base CSV
        followup_value: Value from followup CSV
        field_name: Field name
        registration_number: Registration number

    Returns:
        Merged value (concatenated with labels)
    """
    base_clean = base_value.strip() if base_value else ""
    followup_clean = followup_value.strip() if followup_value else ""

    if base_clean and followup_clean:
        if base_clean == followup_clean:
            logger.debug(
                f"{registration_number} - {field_name}: Values identical, keeping single copy"
            )
            return base_clean
        logger.info(
            f"{registration_number} - {field_name}: Concatenating base and followup values"
        )
        return f"**Original Response:**\n{base_clean}\n\n**Current Followup:**\n{followup_clean}"
    elif followup_clean:
        logger.debug(f"{registration_number} - {field_name}: Using followup value only")
        return followup_clean
    else:
        logger.debug(f"{registration_number} - {field_name}: Using base value only")
        return base_clean


def merge_dates_by_latest(
    base_value: str, followup_value: str, field_name: str, registration_number: str
) -> str:
    """
    Compare dates and return the latest one.
    Use for date fields where the most recent date is preferred.
    Warns if followup date is earlier than base date.

    Args:
        base_value: Date string from base CSV
        followup_value: Date string from followup CSV
        field_name: Field name
        registration_number: Registration number

    Returns:
        Latest date
    """
    base_clean = base_value.strip() if base_value else ""
    followup_clean = followup_value.strip() if followup_value else ""

    if not base_clean and not followup_clean:
        return ""
    elif not base_clean:
        logger.debug(
            f"{registration_number} - {field_name}: Using followup date (base empty)"
        )
        return followup_clean
    elif not followup_clean:
        logger.debug(
            f"{registration_number} - {field_name}: Using base date (followup empty)"
        )
        return base_clean

    # Try to parse dates
    try:
        base_date = datetime.fromisoformat(base_clean)
        followup_date = datetime.fromisoformat(followup_clean)

        if followup_date < base_date:
            logger.warning(
                f"{registration_number} - {field_name}: Followup date ({followup_clean}) "
                f"is earlier than base date ({base_clean})"
            )

        latest = max(base_date, followup_date)
        result = latest.date().isoformat()
        logger.debug(
            f"{registration_number} - {field_name}: Selected latest date: {result}"
        )
        return result
    except ValueError as e:
        logger.warning(
            f"{registration_number} - {field_name}: Could not parse dates "
            f"(base: {base_clean}, followup: {followup_clean}), keeping followup"
        )
        return followup_clean


def merge_dates_by_earliest(
    base_value: str, followup_value: str, field_name: str, registration_number: str
) -> str:
    """
    Compare dates and return the earliest one.
    Use for date fields where the earliest date is preferred (e.g., submission dates).

    Args:
        base_value: Date string from base CSV
        followup_value: Date string from followup CSV
        field_name: Field name
        registration_number: Registration number

    Returns:
        Earliest date
    """
    base_clean = base_value.strip() if base_value else ""
    followup_clean = followup_value.strip() if followup_value else ""

    if not base_clean and not followup_clean:
        return ""
    elif not base_clean:
        logger.debug(
            f"{registration_number} - {field_name}: Using followup date (base empty)"
        )
        return followup_clean
    elif not followup_clean:
        logger.debug(
            f"{registration_number} - {field_name}: Using base date (followup empty)"
        )
        return base_clean

    # Try to parse dates
    try:
        base_date = datetime.fromisoformat(base_clean)
        followup_date = datetime.fromisoformat(followup_clean)

        earliest = min(base_date, followup_date)
        result = earliest.isoformat()
        logger.debug(
            f"{registration_number} - {field_name}: Selected earliest date: {result}"
        )
        return result
    except ValueError:
        logger.warning(
            f"{registration_number} - {field_name}: Could not parse dates "
            f"(base: {base_clean}, followup: {followup_clean}), keeping base"
        )
        return base_clean


def merge_json_lists(
    base_value: str, followup_value: str, field_name: str, registration_number: str
) -> str:
    """
    Merge JSON list structures, removing duplicates.
    Use for fields containing JSON arrays that should be combined.

    Args:
        base_value: JSON string from base CSV
        followup_value: JSON string from followup CSV
        field_name: Field name
        registration_number: Registration number

    Returns:
        Merged JSON string
    """

    base_clean = base_value.strip() if base_value else ""
    followup_clean = followup_value.strip() if followup_value else ""

    # Parse JSON lists
    base_list = []
    followup_list = []

    base_list = safe_parse_json_list(
        base_clean, "base", field_name, registration_number
    )
    followup_list = safe_parse_json_list(
        followup_clean, "followup", field_name, registration_number
    )

    # Combine and deduplicate
    merged = base_list.copy()
    for item in followup_list:
        if item not in merged:
            merged.append(item)

    if merged:
        logger.debug(
            f"{registration_number} - {field_name}: Merged {len(base_list)} + "
            f"{len(followup_list)} -> {len(merged)} items"
        )

    return json.dumps(merged) if merged else ""


def merge_json_objects(
    base_value: str, followup_value: str, field_name: str, registration_number: str
) -> str:
    """
    Merge JSON object structures, with smart merging for list values.

    For duplicate keys:
    - If both values are lists: merge and deduplicate the lists
    - Otherwise: followup values override base values

    Use for fields containing JSON objects (dictionaries).

    Args:
        base_value: JSON string from base CSV
        followup_value: JSON string from followup CSV
        field_name: Field name
        registration_number: Registration number

    Returns:
        Merged JSON string
    """

    base_clean = base_value.strip() if base_value else ""
    followup_clean = followup_value.strip() if followup_value else ""

    # Parse JSON objects
    base_obj = safe_parse_json_object(
        base_clean, "base", field_name, registration_number
    )
    followup_obj = safe_parse_json_object(
        followup_clean, "followup", field_name, registration_number
    )

    # Merge: start with base
    merged = base_obj.copy()

    # Merge in followup with smart list handling
    for key, followup_val in followup_obj.items():
        if key in merged:
            base_val = merged[key]

            # If both are lists, merge them
            if isinstance(base_val, list) and isinstance(followup_val, list):
                # Combine lists and deduplicate while preserving order
                combined = base_val + followup_val
                # Remove duplicates while preserving order
                seen = set()
                deduped = []
                for item in combined:
                    # For complex items, convert to string for comparison
                    item_key = (
                        json.dumps(item, sort_keys=True)
                        if isinstance(item, (dict, list))
                        else item
                    )
                    if item_key not in seen:
                        seen.add(item_key)
                        deduped.append(item)
                # Sort if all items are strings, otherwise preserve order
                merged[key] = (
                    sorted(deduped)
                    if all(isinstance(x, str) for x in deduped)
                    else deduped
                )
            else:
                # For non-list values, followup takes precedence
                merged[key] = followup_val
        else:
            # New key from followup
            merged[key] = followup_val

    if merged:
        logger.debug(
            f"{registration_number} - {field_name}: Merged {len(base_obj)} + {len(followup_obj)} -> {len(merged)} keys"
        )

    return json.dumps(merged) if merged else ""


def merge_boolean_or(
    base_value: str, followup_value: str, field_name: str, registration_number: str
) -> str:
    """
    Logical OR for boolean fields (True/False strings).
    Returns True if either value is True.

    Args:
        base_value: Boolean string from base CSV
        followup_value: Boolean string from followup CSV
        field_name: Field name
        registration_number: Registration number

    Returns:
        Boolean string result
    """
    base_bool = str(base_value).strip().lower() in ["true", "1", "yes"]
    followup_bool = str(followup_value).strip().lower() in ["true", "1", "yes"]

    result = base_bool or followup_bool
    logger.debug(
        f"{registration_number} - {field_name}: OR({base_bool}, {followup_bool}) = {result}"
    )
    return str(result)


def merge_boolean_and(
    base_value: str, followup_value: str, field_name: str, registration_number: str
) -> str:
    """
    Logical AND for boolean fields (True/False strings).
    Returns True only if both values are True.

    Args:
        base_value: Boolean string from base CSV
        followup_value: Boolean string from followup CSV
        field_name: Field name
        registration_number: Registration number

    Returns:
        Boolean string result
    """
    base_bool = str(base_value).strip().lower() in ["true", "1", "yes"]
    followup_bool = str(followup_value).strip().lower() in ["true", "1", "yes"]

    result = base_bool and followup_bool
    logger.debug(
        f"{registration_number} - {field_name}: AND({base_bool}, {followup_bool}) = {result}"
    )
    return str(result)


def merge_document_urls_list(
    base_value: str, followup_value: str, field_name: str, registration_number: str
) -> str:
    """
    Merge document URL lists (list of {"text": "...", "url": "..."} objects).

    Removes duplicates based on URL field while preserving order.
    If both lists have the same URL, the first occurrence (from base) is kept.
    Only includes items that have both "text" and "url" fields.

    Use for fields containing lists of document link objects.

    Args:
        base_value: JSON string from base CSV
        followup_value: JSON string from followup CSV
        field_name: Field name
        registration_number: Registration number

    Returns:
        Merged JSON string with deduplicated URLs
    """
    base_clean = base_value.strip() if base_value else ""
    followup_clean = followup_value.strip() if followup_value else ""

    base_list = safe_parse_json_list(
        base_clean, "base", field_name, registration_number
    )
    followup_list = safe_parse_json_list(
        followup_clean, "followup", field_name, registration_number
    )

    # Track seen URLs to remove duplicates
    seen_urls = set()
    merged = []

    # Add base items first
    for item in base_list:
        if isinstance(item, dict) and "url" in item and "text" in item:
            url = item["url"]
            if url not in seen_urls:
                seen_urls.add(url)
                merged.append(item)
        else:
            # Handle malformed items
            logger.warning(
                f"{registration_number} - {field_name}: "
                f"Skipping malformed base item (missing 'text' or 'url'): {item}"
            )

    # Add followup items only if URL not already seen
    for item in followup_list:
        if isinstance(item, dict) and "url" in item and "text" in item:
            url = item["url"]
            if url not in seen_urls:
                seen_urls.add(url)
                merged.append(item)
        else:
            # Handle malformed items
            logger.warning(
                f"{registration_number} - {field_name}: "
                f"Skipping malformed followup item (missing 'text' or 'url'): {item}"
            )

    if merged:
        logger.debug(
            f"{registration_number} - {field_name}: "
            f"Merged {len(base_list)} + {len(followup_list)} = {len(merged)} URLs "
            f"({len(base_list) + len(followup_list) - len(merged)} duplicates removed)"
        )
        return json.dumps(merged)

    return ""


def merge_keep_base_only(
    base_value: str, followup_value: str, field_name: str, registration_number: str
) -> str:
    """
    Always keep base value, ignore followup value.
    Use for immutable fields that should never be updated.

    Raises ImmutableFieldConflictError if followup has a different non-null value,
    indicating a data integrity issue.

    Args:
        base_value: Value from base CSV
        followup_value: Value from followup CSV (should be None, empty, or same as base)
        field_name: Field name
        registration_number: Registration number

    Returns:
        Base value

    Raises:
        ImmutableFieldConflictError: When followup has a different non-null value
    """
    # Check if followup value is non-empty and different from base
    followup_clean = followup_value.strip() if followup_value else ""
    base_clean = base_value.strip() if base_value else ""

    # Followup should be empty, None, 'null', or identical to base
    if followup_clean and followup_clean not in ["", "None", "null"]:
        if followup_clean != base_clean:
            logger.error(
                f"{registration_number} - {field_name}: Immutable field conflict detected. "
                f"Base: '{base_value}', Followup: '{followup_value}'"
            )
            raise ImmutableFieldConflictError(
                f"Immutable field '{field_name}' has conflicting values for {registration_number}. "
                f"Base: '{base_value}', Followup: '{followup_value}'. "
                f"Immutable fields should never differ between datasets."
            )

    logger.debug(
        f"{registration_number} - {field_name}: Keeping base value (immutable field)"
    )
    return base_value


def merge_keep_followup_only(
    base_value: str, followup_value: str, field_name: str, registration_number: str
) -> str:
    """
    Always keep followup value, ignore base value.
    Use for fields that should always be overridden by followup data.

    Args:
        base_value: Value from base CSV (ignored)
        followup_value: Value from followup CSV
        field_name: Field name
        registration_number: Registration number

    Returns:
        Followup value
    """
    logger.debug(
        f"{registration_number} - {field_name}: Keeping followup value (override field)"
    )
    return followup_value


def merge_promised_new_law(
    base_value: str, followup_value: str, field_name: str, registration_number: str
) -> str:
    """
    Special logic for commission_promised_new_law:
    - If Response Data is False and Followup Data is True, set True
    - If both False, then False
    - If Response Data is True and Followup Data is False, keep True

    A Commission promise is one-way - once made, it doesn't become unmade.
    """
    base_bool = str(base_value).strip().lower() in ["true", "1", "yes"]
    followup_bool = str(followup_value).strip().lower() in ["true", "1", "yes"]

    # Once promised (True in either), always promised
    result = base_bool or followup_bool

    if base_bool and not followup_bool:
        logger.debug(
            f"{registration_number} - {field_name}: Keeping True from base (one-way commitment)"
        )
    elif not base_bool and followup_bool:
        logger.info(
            f"{registration_number} - {field_name}: Updated to True from followup"
        )

    return str(result)


def merge_rejected_initiative(
    base_value: str, followup_value: str, field_name: str, registration_number: str
) -> str:
    """
    Special logic for commission_rejected_initiative:
    - If Response Data is True, keep it (Response Data overwrites Followup Data)
    - If Response Data is False and Followup Data is True, keep Followup Data

    Rejection is permanent - Response Data is authoritative source.
    """
    base_bool = str(base_value).strip().lower() in ["true", "1", "yes"]
    followup_bool = str(followup_value).strip().lower() in ["true", "1", "yes"]

    # Response Data takes priority
    if base_bool:
        logger.debug(
            f"{registration_number} - {field_name}: Keeping True from base (authoritative)"
        )
        return str(True)

    # If base is False, use followup
    if followup_bool:
        logger.info(f"{registration_number} - {field_name}: Using True from followup")
        return str(True)

    logger.debug(f"{registration_number} - {field_name}: Both False")
    return str(False)


def merge_outcome_status_with_validation(
    base_value: str, followup_value: str, field_name: str, registration_number: str
) -> str:
    """
    Prioritize Followup Data (followup) when available, with validation.
    Flag illogical transitions for manual review.
    """
    base_clean = base_value.strip() if base_value else ""
    followup_clean = followup_value.strip() if followup_value else ""

    if not followup_clean:
        logger.debug(
            f"{registration_number} - {field_name}: Using base value (followup empty)"
        )
        return base_clean

    # Check for illogical transitions
    if base_clean and followup_clean and base_clean != followup_clean:
        # Define status progression order
        status_order = ["Being Studied", "Law Proposed", "Law Approved", "Law Rejected"]

        try:
            base_idx = (
                status_order.index(base_clean) if base_clean in status_order else -1
            )
            followup_idx = (
                status_order.index(followup_clean)
                if followup_clean in status_order
                else -1
            )

            # Warn if status appears to go backwards (except rejection can happen at any point)
            if base_idx != -1 and followup_idx != -1:
                if followup_clean == "Law Rejected":
                    logger.info(
                        f"{registration_number} - {field_name}: Status changed to rejected: {base_clean} -> {followup_clean}"
                    )
                elif followup_idx < base_idx:
                    logger.warning(
                        f"{registration_number} - {field_name}: ILLOGICAL STATUS TRANSITION "
                        f"(backwards): {base_clean} -> {followup_clean} - MANUAL REVIEW NEEDED"
                    )
                else:
                    logger.info(
                        f"{registration_number} - {field_name}: Status progressed: {base_clean} -> {followup_clean}"
                    )
        except ValueError:
            pass

    logger.debug(
        f"{registration_number} - {field_name}: Using followup value (more current)"
    )
    return followup_clean


def merge_law_implementation_date(
    base_value: str, followup_value: str, field_name: str, registration_number: str
) -> str:
    """
    Keep Response Data if Followup Data is null; update with Followup Data when exists.
    """
    followup_clean = followup_value.strip() if followup_value else ""
    base_clean = base_value.strip() if base_value else ""

    if followup_clean and followup_clean not in ["", "None", "null"]:
        if base_clean and base_clean != followup_clean:
            logger.info(
                f"{registration_number} - {field_name}: Updated from {base_clean} to {followup_clean}"
            )
        return followup_clean

    logger.debug(f"{registration_number} - {field_name}: Keeping base value")
    return base_clean


# ============================================================================
# Field Mapping Configuration
# ============================================================================


def get_merge_strategy_for_field(field_name: str) -> Callable:
    """
    Return the appropriate merge strategy function for a given field.
    This function maps field names to their specific merge strategies based on
    the detailed merge strategy document.

    Args:
        field_name: Name of the field to merge

    Returns:
        Merge strategy function for the field
    """
    # Mapping based on merging_strategy.txt
    strategy_map = {
        # Identity columns (immutable)
        "registration_number": merge_keep_base_only,
        "initiative_title": merge_keep_base_only,
        # Unique to Response Data - keep all (immutable)
        "response_url": merge_keep_base_only,
        "initiative_url": merge_keep_base_only,
        "submission_text": merge_keep_base_only,
        "commission_submission_date": merge_keep_base_only,
        "submission_news_url": merge_keep_base_only,
        "commission_meeting_date": merge_keep_base_only,
        "commission_officials_met": merge_keep_base_only,
        "parliament_hearing_date": merge_keep_base_only,
        "parliament_hearing_video_urls": merge_keep_base_only,
        "plenary_debate_date": merge_keep_base_only,
        "plenary_debate_video_urls": merge_keep_base_only,
        "official_communication_adoption_date": merge_keep_base_only,
        "commission_factsheet_url": merge_keep_base_only,
        "has_followup_section": merge_keep_base_only,
        # Overlapping columns with specific strategies
        "followup_dedicated_website": merge_keep_base_only,  # Identical in both
        "commission_answer_text": merge_by_concatenation,  # Merge with labels
        "official_communication_document_urls": merge_document_urls_list,  # Append unique links
        "final_outcome_status": merge_outcome_status_with_validation,  # Prioritize Followup Data with validation
        "law_implementation_date": merge_law_implementation_date,  # Update with Followup Data when exists
        "commission_promised_new_law": merge_promised_new_law,  # One-way True logic
        "commission_deadlines": merge_by_concatenation,  # Merge with labels
        "commission_rejected_initiative": merge_rejected_initiative,  # Response Data priority, one-way True
        "commission_rejection_reason": merge_by_concatenation,  # Combine with labels
        "laws_actions": merge_json_lists,  # Append unique actions
        "policies_actions": merge_json_lists,  # Append with deduplication
        "has_roadmap": merge_boolean_or,  # Logical OR
        "has_workshop": merge_boolean_or,  # Logical OR
        "has_partnership_programs": merge_boolean_or,  # Logical OR
        "court_cases_referenced": merge_json_lists,  # Combine, deduplicate
        "followup_latest_date": merge_dates_by_latest,  # Maximum with warning
        "followup_most_future_date": merge_dates_by_latest,  # Maximum with warning
        "referenced_legislation_by_id": merge_json_objects,  # Union
        "referenced_legislation_by_name": merge_json_objects,  # Union
        "followup_events_with_dates": merge_json_lists,  # Merge, deduplicate
    }

    # Return the specific strategy or default to preferring followup
    return strategy_map.get(field_name, merge_by_preferring_followup)


# ============================================================================
# Main Merge Function
# ============================================================================

# Mandatory fields that must be present in base dataset only
MANDATORY_BASE_FIELD = [
    "response_url",
    "initiative_url",
    "submission_text",
]

# Mandatory fields that must be present in followup dataset only
MANDATORY_FOLLOWUP_FIELD = [
    "registration_number",
    "initiative_title",
    "followup_dedicated_website",
    "commission_answer_text",
    "commission_promised_new_law",
    "commission_rejected_initiative",
    "has_roadmap",
    "has_workshop",
    "has_partnership_programs",
    "followup_events_with_dates",
]

# Construct mandatory fields that must be present in BOTH datasets
MANDATORY_BOTH_FIELDS = list(set(MANDATORY_FOLLOWUP_FIELD))


def merge_field_values(
    base_value: str, followup_value: str, field_name: str, registration_number: str
) -> str:
    """
    Merge a single field from base and followup CSVs.
    This is the main entry point that delegates to field-specific strategies.

    Args:
        base_value: Value from the base CSV (eci_responses_*.csv)
        followup_value: Value from the followup CSV (eci_responses_followup_website_*.csv)
        field_name: Name of the field being merged
        registration_number: Registration number for the current row (for logging/debugging)

    Returns:
        The merged value for this field
    """
    # First, validate mandatory fields
    validate_mandatory_many_fields(
        base_value, followup_value, field_name, registration_number
    )

    # Second validate base mandatory field
    validate_mandatory_field(
        base_value, field_name, registration_number, MANDATORY_BASE_FIELD
    )

    # Get the appropriate strategy for this field
    strategy_func = get_merge_strategy_for_field(field_name)

    # Apply the strategy
    try:
        result = strategy_func(
            base_value, followup_value, field_name, registration_number
        )
        return result
    except ImmutableFieldConflictError:
        # Re-raise immutable field conflicts - these are data integrity errors
        raise
    except Exception as e:
        logger.error(
            f"{registration_number} - {field_name}: Error during merge: {e}. "
            f"Falling back to base value."
        )
        return base_value


def validate_mandatory_many_fields(
    base_value: str, followup_value: str, field_name: str, registration_number: str
) -> None:
    """
    Validate that mandatory fields have non-empty values in both datasets.

    Args:
        base_value: Value from base CSV
        followup_value: Value from followup CSV
        field_name: Field name
        registration_number: Registration number for error reporting

    Raises:
        MandatoryFieldMissingError: When a mandatory field is empty/None
    """
    # Only validate if this is a mandatory field
    if field_name not in MANDATORY_BOTH_FIELDS:
        return

    # Clean values
    base_clean = base_value.strip() if base_value else ""
    followup_clean = followup_value.strip() if followup_value else ""

    # Check if base is empty or null
    base_is_empty = not base_clean or base_clean in ["None", "null", ""]

    # Check if followup is empty or null
    followup_is_null = followup_clean in ["None", "null", ""]

    # Case 1: Both are empty/null - most critical
    if base_is_empty and (not followup_clean or followup_is_null):
        logger.error(
            f"{registration_number} - {field_name}: Mandatory field is empty in both datasets"
        )
        raise MandatoryFieldMissingError(
            f"Mandatory fields '{field_name}' are empty in both base and followup datasets for {registration_number}. "
            f"Base: '{base_value}', Followup: '{followup_value}'. "
            f"At least one dataset must have a non-empty value for mandatory fields."
        )

    # Case 2: Only base is empty
    if base_is_empty:
        logger.error(
            f"{registration_number} - {field_name}: Mandatory field is empty in base dataset"
        )
        raise MandatoryFieldMissingError(
            f"Mandatory field '{field_name}' is empty in base dataset for {registration_number}. "
            f"Value: '{base_value}'. All mandatory fields must have non-empty values in base dataset."
        )

    # Case 3: Followup has explicit null
    if followup_is_null:
        logger.error(
            f"{registration_number} - {field_name}: Mandatory field has explicit null in followup dataset"
        )
        raise MandatoryFieldMissingError(
            f"Mandatory field '{field_name}' has explicit null value in followup dataset for {registration_number}. "
            f"Value: '{followup_value}'. Use empty string instead of 'null' or 'None'."
        )


def validate_mandatory_field(
    base_value: str,
    field_name: str,
    registration_number: str,
    mandatory_fields: List[str],
) -> None:
    """
    Validate that mandatory fields have non-empty values.

    This validates fields that only exist in the selected dataset
    and are required to be non-empty.
    """
    if field_name not in mandatory_fields:
        return

    value_clean = base_value.strip() if base_value else ""
    field_is_empty = not value_clean or value_clean in ["None", "null", ""]

    if field_is_empty:
        logger.error(
            f"{registration_number} - {field_name}: Mandatory base field is empty"
        )
        raise MandatoryFieldMissingError(
            f"Mandatory base field '{field_name}' is empty for {registration_number}. "
            f"Value: '{base_value}'. This field is required in the Response Data dataset."
        )
