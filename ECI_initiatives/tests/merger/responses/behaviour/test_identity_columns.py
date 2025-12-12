"""
Behavioural tests for identity column merging.

This module tests merging of:
- registration_number (primary key)
- initiative_title (human-readable identifier)

Both fields are immutable and should always keep Dataset 1 values.
"""

import pytest
from ECI_initiatives.csv_merger.responses.strategies import (
    merge_field_values,
    merge_keep_base_only,
)
from ECI_initiatives.csv_merger.responses.exceptions import (
    ImmutableFieldConflictError,
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

        # Test case 2: Base present, followup empty
        base_3 = "2022/000001"
        followup_3 = ""
        result_3 = merge_field_values(
            base_3, followup_3, "registration_number", "2022/000001"
        )
        assert result_3 == base_3, "Should keep base value when followup is empty"

        # Test case 3: Base present, followup None
        base_4 = "2022/000001"
        followup_4 = None
        result_4 = merge_field_values(
            base_4, followup_4, "registration_number", "2022/000001"
        )
        assert result_4 == base_4, "Should keep base value when followup is None"

        # Test case 4: Base present, followup whitespace
        base_5 = "2022/000001"
        followup_5 = "   "
        result_5 = merge_field_values(
            base_5, followup_5, "registration_number", "2022/000001"
        )
        assert result_5 == base_5, "Should keep base value when followup is whitespace"

        # Test case 5: Base present, followup "null" string
        base_6 = "2022/000001"
        followup_6 = "null"
        result_6 = merge_field_values(
            base_6, followup_6, "registration_number", "2022/000001"
        )
        assert (
            result_6 == base_6
        ), "Should keep base value when followup is 'null' string"

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

        # Test case 2: Base present, followup empty
        base_3 = "Save Bees and Farmers"
        followup_3 = ""
        result_3 = merge_field_values(
            base_3, followup_3, "initiative_title", "2019/000006"
        )
        assert result_3 == base_3, "Should keep base value when followup is empty"

        # Test case 3: Base with special characters
        base_4 = "Stop Vivisection – Let's choose progress without animal testing"
        followup_4 = ""
        result_4 = merge_field_values(
            base_4, followup_4, "initiative_title", "2012/000007"
        )
        assert result_4 == base_4, "Should keep base value with special characters"

        # Test case 4: Base with multilingual elements
        base_5 = "Wir sind mit dem Grundeinkommen dabei - in der ganzen EU!"
        followup_5 = ""
        result_5 = merge_field_values(
            base_5, followup_5, "initiative_title", "2013/000001"
        )
        assert result_5 == base_5, "Should keep base value with non-English characters"

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

    def test_identity_columns_accept_null_followup(self):
        """Test that identity columns accept various null representations in followup."""

        # Test with various null-like values for registration_number
        test_cases = [
            ("2022/000001", "", "2022/000001"),  # Empty string
            ("2022/000001", None, "2022/000001"),  # None
            ("2022/000001", "null", "2022/000001"),  # String "null"
            ("2022/000001", "   ", "2022/000001"),  # Whitespace
        ]

        for base, followup, expected in test_cases:
            result = merge_field_values(base, followup, "registration_number", base)
            assert result == expected, f"Failed for base={base}, followup={followup}"

    def test_direct_strategy_function_call(self):
        """Test calling merge_keep_base_only strategy function directly."""

        # Test case 1: Registration number - identical values
        result_1 = merge_keep_base_only(
            "2022/000001", "2022/000001", "registration_number", "2022/000001"
        )
        assert result_1 == "2022/000001", "Should return base value when identical"

        # Test case 2: Initiative title - empty followup
        result_2 = merge_keep_base_only(
            "Original Title", "", "initiative_title", "2022/000001"
        )
        assert (
            result_2 == "Original Title"
        ), "Should return base value when followup empty"

        # Test case 3: Empty base (edge case - shouldn't happen for identity columns)
        result_3 = merge_keep_base_only("", "", "registration_number", "2022/000001")
        assert result_3 == "", "Should return empty base even when both empty"

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
