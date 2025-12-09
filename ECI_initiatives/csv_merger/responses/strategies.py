"""
Field merging strategies for combining base and followup CSV data.
"""


def merge_field_values(
    base_value: str, followup_value: str, field_name: str, registration_number: str
) -> str:
    """
    Merge a single field from base and followup CSVs.

    This is a placeholder implementation. The actual merging strategy
    should be implemented based on business requirements.

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

        TODO: Implement proper field-specific merging logic:
        - Some fields should concatenate
        - Some fields should prefer one source over another
        - Some fields may need special handling (dates, JSON, etc.)
    """

    # Placeholder implementation: prefer followup if non-empty, else base
    if followup_value and followup_value.strip():
        return followup_value
    return base_value
