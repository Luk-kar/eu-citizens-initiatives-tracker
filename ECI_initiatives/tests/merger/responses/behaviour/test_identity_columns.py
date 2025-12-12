"""
Behavioural tests for identity column merging.

This module tests merging of:
- registration_number (primary key)
- initiative_title (human-readable identifier)

Both fields are immutable and should always keep Response Data values.
Both fields are also mandatory and must have non-empty values in BOTH datasets.
"""

import pytest
from ECI_initiatives.csv_merger.responses.strategies import (
    merge_field_values,
    merge_keep_base_only,
    validate_mandatory_many_fields,
)
from ECI_initiatives.csv_merger.responses.exceptions import (
    ImmutableFieldConflictError,
    MandatoryFieldMissingError,
)


class TestIdentityColumnsMerging:
    """Tests for identity column merge strategies."""

    def test_registration_number_always_keeps_base(self):
        """Test that registration_number always keeps base value regardless of followup."""

        # Test case 1: Both values present and identical
        base_1 = "2022/000001"
        followup_1 = "2022/000001"
        result_1 = merge_field_values(
            base_1, followup_1, "registration_number", "2022/000001"
        )
        assert result_1 == base_1, "Should keep base value when both identical"

        # Test case 2: Both present with different valid values (will raise ImmutableFieldConflictError)
        # This is tested in test_registration_number_raises_error_on_conflict

    def test_registration_number_raises_error_on_conflict(self):
        """Test that conflicting registration numbers raise ImmutableFieldConflictError."""

        # Test case: Both values present but different (should raise error)
        base = "2022/000001"
        followup = "2022/000002"

        with pytest.raises(ImmutableFieldConflictError) as exc_info:
            merge_field_values(base, followup, "registration_number", "2022/000001")

        # Verify error message contains useful information
        error_msg = str(exc_info.value)
        assert "registration_number" in error_msg, "Error should mention field name"
        assert "2022/000001" in error_msg, "Error should contain base value"
        assert "2022/000002" in error_msg, "Error should contain followup value"
        assert "Immutable" in error_msg, "Error should indicate immutability violation"

    def test_initiative_title_always_keeps_base(self):
        """Test that initiative_title always keeps base value regardless of followup."""

        # Test case 1: Both values present and identical
        base_1 = "End the Cage Age"
        followup_1 = "End the Cage Age"
        result_1 = merge_field_values(
            base_1, followup_1, "initiative_title", "2022/000001"
        )
        assert result_1 == base_1, "Should keep base value when both identical"

        # Test case 2: Different initiative titles with special characters
        base_2 = "Stop Vivisection – Let's choose progress without animal testing"
        followup_2 = "Stop Vivisection – Let's choose progress without animal testing"
        result_2 = merge_field_values(
            base_2, followup_2, "initiative_title", "2012/000007"
        )
        assert result_2 == base_2, "Should keep base value with special characters"

        # Test case 3: Initiative title with proper noun containing non-English characters
        base_3 = "Support the François Mitterrand European Education Program"
        followup_3 = "Support the François Mitterrand European Education Program"
        result_3 = merge_field_values(
            base_3, followup_3, "initiative_title", "2013/000001"
        )
        assert (
            result_3 == base_3
        ), "Should keep base value with non-English characters in proper noun"

        # NOTE: Empty followup is no longer allowed for mandatory fields

    def test_initiative_title_raises_error_on_conflict(self):
        """Test that conflicting initiative titles raise ImmutableFieldConflictError."""

        # Test case: Different titles (minor variation) should raise error
        base = "Minority SafePack - one million signatures for diversity in Europe"
        followup = "Minority SafePack"  # Shortened version - this is a conflict

        with pytest.raises(ImmutableFieldConflictError) as exc_info:
            merge_field_values(base, followup, "initiative_title", "2017/000004")

        error_msg = str(exc_info.value)
        assert "initiative_title" in error_msg
        assert "2017/000004" in error_msg

    def test_identity_columns_require_both_values(self):
        """Test that identity columns require non-empty values in both base and followup."""

        # NEW BEHAVIOR: Both base and followup must have values for mandatory fields
        # Test with identical values - should work
        result = merge_field_values(
            "2022/000001", "2022/000001", "registration_number", "2022/000001"
        )
        assert result == "2022/000001", "Should work when both have identical values"

    def test_direct_strategy_function_call(self):
        """Test calling merge_keep_base_only strategy function directly."""

        # Test case 1: Registration number - identical values
        result_1 = merge_keep_base_only(
            "2022/000001", "2022/000001", "registration_number", "2022/000001"
        )
        assert result_1 == "2022/000001", "Should return base value when identical"

        # Test case 2: Initiative title - identical values
        result_2 = merge_keep_base_only(
            "Original Title", "Original Title", "initiative_title", "2022/000001"
        )
        assert result_2 == "Original Title", "Should return base value when identical"

        # NOTE: merge_keep_base_only itself doesn't validate mandatory fields
        # That validation happens in merge_field_values before calling the strategy

    def test_direct_strategy_function_raises_error(self):
        """Test that merge_keep_base_only raises error for conflicts."""

        # Direct call should raise exception for conflicting values
        with pytest.raises(ImmutableFieldConflictError):
            merge_keep_base_only(
                "2022/000001", "2022/000002", "registration_number", "2022/000001"
            )

        # Another test with title
        with pytest.raises(ImmutableFieldConflictError):
            merge_keep_base_only(
                "Original Title", "Modified Title", "initiative_title", "2022/000001"
            )

    def test_error_message_quality(self):
        """Test that error messages provide sufficient debugging information."""

        base = "2022/000001"
        followup = "2023/999999"

        with pytest.raises(ImmutableFieldConflictError) as exc_info:
            merge_keep_base_only(base, followup, "registration_number", base)

        error_msg = str(exc_info.value)

        # Error should be informative
        assert "registration_number" in error_msg, "Should mention field name"
        assert base in error_msg, "Should show base value"
        assert followup in error_msg, "Should show followup value"
        assert (
            "Immutable" in error_msg or "immutable" in error_msg
        ), "Should explain immutability"
        assert len(error_msg) > 50, "Error message should be descriptive"


class TestMandatoryFieldValidation:
    """Tests for mandatory field validation on identity columns."""

    def test_registration_number_both_empty_raises_error(self):
        """Test that both base and followup being empty raises MandatoryFieldMissingError."""

        with pytest.raises(MandatoryFieldMissingError) as exc_info:
            merge_field_values("", "", "registration_number", "UNKNOWN")

        error_msg = str(exc_info.value)
        assert "both" in error_msg.lower(), "Should mention both datasets"
        assert "registration_number" in error_msg
        assert "Mandatory" in error_msg or "mandatory" in error_msg

    def test_registration_number_empty_base_raises_error(self):
        """Test that empty base with valid followup raises MandatoryFieldMissingError."""

        with pytest.raises(MandatoryFieldMissingError) as exc_info:
            merge_field_values("", "2022/000001", "registration_number", "2022/000001")

        error_msg = str(exc_info.value)
        assert "base" in error_msg.lower()
        assert "registration_number" in error_msg

    def test_registration_number_empty_followup_raises_error(self):
        """Test that empty followup with valid base raises MandatoryFieldMissingError."""

        # NEW BEHAVIOR: Empty followup also raises error for mandatory fields
        with pytest.raises(MandatoryFieldMissingError) as exc_info:
            merge_field_values("2022/000001", "", "registration_number", "2022/000001")

        error_msg = str(exc_info.value)
        assert "followup" in error_msg.lower()
        assert "registration_number" in error_msg

    def test_registration_number_none_base_raises_error(self):
        """Test that None in base raises MandatoryFieldMissingError."""

        with pytest.raises(MandatoryFieldMissingError):
            merge_field_values(
                None, "2022/000001", "registration_number", "2022/000001"
            )

    def test_registration_number_null_string_base_raises_error(self):
        """Test that 'null' string in base raises MandatoryFieldMissingError."""

        with pytest.raises(MandatoryFieldMissingError):
            merge_field_values(
                "null", "2022/000001", "registration_number", "2022/000001"
            )

    def test_registration_number_explicit_null_followup_raises_error(self):
        """Test that explicit 'null' or 'None' in followup raises MandatoryFieldMissingError."""

        # Explicit 'null' string not allowed
        with pytest.raises(MandatoryFieldMissingError) as exc_info:
            merge_field_values(
                "2022/000001", "null", "registration_number", "2022/000001"
            )

        error_msg = str(exc_info.value)
        assert "followup" in error_msg.lower()
        assert "null" in error_msg.lower()

        # Explicit 'None' string not allowed
        with pytest.raises(MandatoryFieldMissingError):
            merge_field_values(
                "2022/000001", "None", "registration_number", "2022/000001"
            )

    def test_registration_number_whitespace_base_raises_error(self):
        """Test that whitespace-only base raises MandatoryFieldMissingError."""

        with pytest.raises(MandatoryFieldMissingError):
            merge_field_values(
                "   ", "2022/000001", "registration_number", "2022/000001"
            )

        with pytest.raises(MandatoryFieldMissingError):
            merge_field_values(
                "\t\n  ", "2022/000001", "registration_number", "2022/000001"
            )

    def test_registration_number_whitespace_followup_raises_error(self):
        """Test that whitespace-only followup raises MandatoryFieldMissingError."""

        with pytest.raises(MandatoryFieldMissingError):
            merge_field_values(
                "2022/000001", "   ", "registration_number", "2022/000001"
            )

    def test_initiative_title_both_empty_raises_error(self):
        """Test that empty initiative_title in both datasets raises error."""

        with pytest.raises(MandatoryFieldMissingError) as exc_info:
            merge_field_values("", "", "initiative_title", "2022/000001")

        error_msg = str(exc_info.value)
        assert "both" in error_msg.lower()
        assert "initiative_title" in error_msg

    def test_initiative_title_empty_base_raises_error(self):
        """Test that empty base with valid followup raises error."""

        with pytest.raises(MandatoryFieldMissingError):
            merge_field_values("", "Some Title", "initiative_title", "2022/000001")

    def test_initiative_title_empty_followup_raises_error(self):
        """Test that empty followup with valid base raises error."""

        # NEW BEHAVIOR: Empty followup also raises error
        with pytest.raises(MandatoryFieldMissingError):
            merge_field_values("Valid Title", "", "initiative_title", "2022/000001")

    def test_initiative_title_explicit_null_followup_raises_error(self):
        """Test that explicit null in followup raises error."""

        with pytest.raises(MandatoryFieldMissingError):
            merge_field_values("Valid Title", "null", "initiative_title", "2022/000001")

    def test_valid_values_in_both_passes(self):
        """Test that valid values in both base and followup pass validation."""

        # Both must have valid values for mandatory fields
        result_1 = merge_field_values(
            "2022/000001", "2022/000001", "registration_number", "2022/000001"
        )
        assert result_1 == "2022/000001"

        result_2 = merge_field_values(
            "Title", "Title", "initiative_title", "2022/000001"
        )
        assert result_2 == "Title"

    def test_validate_mandatory_field_direct_call(self):
        """Test calling validate_mandatory_field function directly."""

        # Both empty should raise
        with pytest.raises(MandatoryFieldMissingError):
            validate_mandatory_many_fields("", "", "registration_number", "2022/000001")

        # Empty base should raise
        with pytest.raises(MandatoryFieldMissingError):
            validate_mandatory_many_fields(
                "", "value", "registration_number", "2022/000001"
            )

        # Empty followup should raise (NEW BEHAVIOR)
        with pytest.raises(MandatoryFieldMissingError):
            validate_mandatory_many_fields(
                "2022/000001", "", "registration_number", "2022/000001"
            )

        # Explicit null in followup should raise
        with pytest.raises(MandatoryFieldMissingError):
            validate_mandatory_many_fields(
                "2022/000001", "null", "registration_number", "2022/000001"
            )

        # Both valid should pass
        validate_mandatory_many_fields(
            "2022/000001", "2022/000001", "registration_number", "2022/000001"
        )

    def test_mandatory_validation_happens_before_immutable_check(self):
        """Test that mandatory validation occurs before immutability check."""

        # If base is empty, should raise MandatoryFieldMissingError (not ImmutableFieldConflictError)
        with pytest.raises(MandatoryFieldMissingError):
            merge_field_values("", "2022/000002", "registration_number", "2022/000001")

    def test_error_messages_are_descriptive(self):
        """Test that mandatory field error messages provide clear context."""

        # Test both empty error message
        with pytest.raises(MandatoryFieldMissingError) as exc_info:
            validate_mandatory_many_fields("", "", "registration_number", "2022/000001")

        error_msg = str(exc_info.value)
        assert "registration_number" in error_msg
        assert "2022/000001" in error_msg
        assert "both" in error_msg.lower()
        assert len(error_msg) > 50, "Error should be descriptive"

        # Test base empty error message
        with pytest.raises(MandatoryFieldMissingError) as exc_info:
            validate_mandatory_many_fields(
                "", "value", "initiative_title", "2022/000001"
            )

        error_msg = str(exc_info.value)
        assert "initiative_title" in error_msg
        assert "base" in error_msg.lower()

        # Test followup empty error message
        with pytest.raises(MandatoryFieldMissingError) as exc_info:
            validate_mandatory_many_fields(
                "2022/000001", "", "registration_number", "2022/000001"
            )

        error_msg = str(exc_info.value)
        assert "followup" in error_msg.lower()
