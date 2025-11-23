"""
Data quality test suite for ECI Commission Response extraction.

This package contains comprehensive data quality tests organized into focused modules:

URL Validation:
    - test_url_fields: URL format, HTTPS, and domain validation

Date Validation:
    - test_date_fields: ISO format and chronological consistency

Field Format Validation:
    - test_registration_numbers: Registration number format (YYYY/NNNNNN)
    - test_text_fields: Text completeness and HTML artifact detection
    - test_json_fields: JSON parsing and structure validation

Structured Data Validation:
    - test_actions_structure: Laws and policies action structure
    - test_court_cases: Court case reference structure
    - test_followup_events: Follow-up event structure

Logical Consistency:
    - test_outcome_status: Outcome status alignment
    - test_commission_response: Commission field coherence
    - test_followup_section: Follow-up section consistency
    - test_boolean_fields: Boolean field consistency

High-Level Validation:
    - test_cross_field_integrity: Cross-field relationships
    - test_completeness_metrics: Data completeness rates

All tests use fixtures defined in conftest.py which are automatically
available to all test modules.
"""
