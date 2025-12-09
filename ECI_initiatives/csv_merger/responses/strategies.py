"""
Field merging strategies for combining base and followup CSV data.
"""

from typing import Dict, Callable


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
    pass


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
    pass


def merge_by_concatenation(
    base_value: str, followup_value: str, field_name: str, registration_number: str
) -> str:
    """
    Concatenate both values if both are non-empty.

    Use for fields that can accumulate information (e.g., notes, descriptions).

    Args:
        base_value: Value from base CSV
        followup_value: Value from followup CSV
        field_name: Field name
        registration_number: Registration number

    Returns:
        Merged value (concatenated)
    """
    pass


def merge_dates_by_latest(
    base_value: str, followup_value: str, field_name: str, registration_number: str
) -> str:
    """
    Compare dates and return the latest one.

    Use for date fields where the most recent date is preferred.

    Args:
        base_value: Date string from base CSV
        followup_value: Date string from followup CSV
        field_name: Field name
        registration_number: Registration number

    Returns:
        Latest date
    """
    pass


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
    pass


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
    pass


def merge_json_objects(
    base_value: str, followup_value: str, field_name: str, registration_number: str
) -> str:
    """
    Merge JSON object structures, with followup values overriding base values.

    Use for fields containing JSON objects (dictionaries).

    Args:
        base_value: JSON string from base CSV
        followup_value: JSON string from followup CSV
        field_name: Field name
        registration_number: Registration number

    Returns:
        Merged JSON string
    """
    pass


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
    pass


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
    pass


def merge_urls_list(
    base_value: str, followup_value: str, field_name: str, registration_number: str
) -> str:
    """
    Merge URL lists, removing duplicates while preserving order.

    Use for fields containing multiple URLs.

    Args:
        base_value: URL list from base CSV
        followup_value: URL list from followup CSV
        field_name: Field name
        registration_number: Registration number

    Returns:
        Merged URL list
    """
    pass


def merge_keep_base_only(
    base_value: str, followup_value: str, field_name: str, registration_number: str
) -> str:
    """
    Always keep base value, ignore followup value.

    Use for immutable fields that should never be updated.

    Args:
        base_value: Value from base CSV
        followup_value: Value from followup CSV (ignored)
        field_name: Field name
        registration_number: Registration number

    Returns:
        Base value
    """
    pass


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
    pass


# ============================================================================
# Field Mapping Configuration
# ============================================================================


def get_merge_strategy_for_field(field_name: str) -> Callable:
    """
    Return the appropriate merge strategy function for a given field.

    This function maps field names to their specific merge strategies.

    Args:
        field_name: Name of the field to merge

    Returns:
        Merge strategy function for the field

    TODO: Implement field-to-strategy mapping based on business requirements.
    Example mapping:
    {
        'registration_number': merge_keep_base_only,
        'initiative_title': merge_keep_base_only,
        'commission_answer_text': merge_by_preferring_followup,
        'followup_latest_date': merge_dates_by_latest,
        'commission_submission_date': merge_dates_by_earliest,
        'has_followup_section': merge_boolean_or,
        'official_communication_document_urls': merge_json_objects,
        'laws_actions': merge_json_lists,
        ...
    }
    """
    pass


# ============================================================================
# Main Merge Function
# ============================================================================


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

    Notes:
        Current placeholder behavior:
        - If followup_value is non-empty, prefer it over base_value
        - Otherwise, keep base_value

        TODO: Implement by calling get_merge_strategy_for_field() and applying
        the appropriate strategy for each field.
    """
    # Placeholder implementation: prefer followup if non-empty, else base
    if followup_value and followup_value.strip():
        return followup_value
    return base_value


# ============================================================================
# Field Categories (for documentation/reference)
# ============================================================================

# Immutable fields (keep base only):
IMMUTABLE_FIELDS = [
    "registration_number",
    "initiative_title",
    "initiative_url",
    "response_url",
]

# Followup-preferred fields (followup data is more recent):
FOLLOWUP_PREFERRED_FIELDS = [
    "commission_answer_text",
    "official_communication_document_urls",
    "final_outcome_status",
    "law_implementation_date",
    "commission_promised_new_law",
    "commission_deadlines",
    "commission_rejected_initiative",
    "commission_rejection_reason",
    "laws_actions",
    "policies_actions",
    "has_roadmap",
    "has_workshop",
    "has_partnership_programs",
    "court_cases_referenced",
    "followup_latest_date",
    "followup_most_future_date",
    "referenced_legislation_by_id",
    "referenced_legislation_by_name",
    "followup_events_with_dates",
    "followup_dedicated_website",
]

# Base-preferred fields (base data is authoritative):
BASE_PREFERRED_FIELDS = [
    "submission_text",
    "commission_submission_date",
    "submission_news_url",
    "commission_meeting_date",
    "commission_officials_met",
    "parliament_hearing_date",
    "parliament_hearing_video_urls",
    "plenary_debate_date",
    "plenary_debate_video_urls",
    "official_communication_adoption_date",
    "commission_factsheet_url",
    "has_followup_section",
]

# Date fields:
DATE_FIELDS = [
    "commission_submission_date",
    "commission_meeting_date",
    "parliament_hearing_date",
    "plenary_debate_date",
    "official_communication_adoption_date",
    "law_implementation_date",
    "followup_latest_date",
    "followup_most_future_date",
]

# Boolean fields:
BOOLEAN_FIELDS = [
    "commission_promised_new_law",
    "commission_rejected_initiative",
    "has_followup_section",
    "has_roadmap",
    "has_workshop",
    "has_partnership_programs",
]

# JSON/structured fields:
JSON_FIELDS = [
    "official_communication_document_urls",
    "parliament_hearing_video_urls",
    "plenary_debate_video_urls",
    "commission_deadlines",
    "laws_actions",
    "policies_actions",
    "referenced_legislation_by_id",
    "referenced_legislation_by_name",
    "followup_events_with_dates",
]
