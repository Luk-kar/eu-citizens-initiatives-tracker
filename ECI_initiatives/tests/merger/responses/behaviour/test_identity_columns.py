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
    get_merge_strategy_for_field,
)


class TestIdentityColumnsMerging:
    """Tests for identity column merge strategies."""

    def test_registration_number_always_keeps_base(self):
        """Test that registration_number always keeps base value regardless of followup."""

        # Test case 1: Both values present and identical
        base_1 = "ECI(2022)000001"
        followup_1 = "ECI(2022)000001"
        result_1 = merge_field_values(
            base_1, followup_1, "registration_number", "ECI(2022)000001"
        )
        assert result_1 == base_1, "Should keep base value when both identical"

        # Test case 2: Both values present but different (should never happen, but test anyway)
        base_2 = "ECI(2022)000001"
        followup_2 = "ECI(2022)000002"
        result_2 = merge_field_values(
            base_2, followup_2, "registration_number", "ECI(2022)000001"
        )
        assert result_2 == base_2, "Should keep base value even if followup differs"

        # Test case 3: Base present, followup empty
        base_3 = "ECI(2022)000001"
        followup_3 = ""
        result_3 = merge_field_values(
            base_3, followup_3, "registration_number", "ECI(2022)000001"
        )
        assert result_3 == base_3, "Should keep base value when followup is empty"

        # Test case 4: Base present, followup None
        base_4 = "ECI(2022)000001"
        followup_4 = None
        result_4 = merge_field_values(
            base_4, followup_4, "registration_number", "ECI(2022)000001"
        )
        assert result_4 == base_4, "Should keep base value when followup is None"

        # Test case 5: Base present, followup whitespace
        base_5 = "ECI(2022)000001"
        followup_5 = "   "
        result_5 = merge_field_values(
            base_5, followup_5, "registration_number", "ECI(2022)000001"
        )
        assert result_5 == base_5, "Should keep base value when followup is whitespace"

    def test_initiative_title_always_keeps_base(self):
        """Test that initiative_title always keeps base value regardless of followup."""

        # Test case 1: Both values present and identical
        base_1 = "End the Cage Age"
        followup_1 = "End the Cage Age"
        result_1 = merge_field_values(
            base_1, followup_1, "initiative_title", "ECI(2022)000001"
        )
        assert result_1 == base_1, "Should keep base value when both identical"

        # Test case 2: Both values present but different (minor variation)
        base_2 = "Minority SafePack - one million signatures for diversity in Europe"
        followup_2 = "Minority SafePack"
        result_2 = merge_field_values(
            base_2, followup_2, "initiative_title", "ECI(2017)000004"
        )
        assert (
            result_2 == base_2
        ), "Should keep full base title even if followup has shortened version"

        # Test case 3: Base present, followup empty
        base_3 = "Save Bees and Farmers"
        followup_3 = ""
        result_3 = merge_field_values(
            base_3, followup_3, "initiative_title", "ECI(2019)000006"
        )
        assert result_3 == base_3, "Should keep base value when followup is empty"

        # Test case 4: Base with special characters
        base_4 = "Stop Vivisection – Let's choose progress without animal testing"
        followup_4 = "Stop Vivisection"
        result_4 = merge_field_values(
            base_4, followup_4, "initiative_title", "ECI(2012)000007"
        )
        assert result_4 == base_4, "Should keep base value with special characters"

        # Test case 5: Base with multilingual elements
        base_5 = "Wir sind mit dem Grundeinkommen dabei - in der ganzen EU!"
        followup_5 = "Basic Income Initiative"
        result_5 = merge_field_values(
            base_5, followup_5, "initiative_title", "ECI(2013)000001"
        )
        assert result_5 == base_5, "Should keep base value with non-English characters"

    def test_strategy_mapping_for_identity_columns(self):
        """Test that identity columns are correctly mapped to merge_keep_base_only strategy."""

        # Test registration_number mapping
        strategy_reg = get_merge_strategy_for_field("registration_number")
        assert (
            strategy_reg == merge_keep_base_only
        ), "registration_number should use merge_keep_base_only"

        # Test initiative_title mapping
        strategy_title = get_merge_strategy_for_field("initiative_title")
        assert (
            strategy_title == merge_keep_base_only
        ), "initiative_title should use merge_keep_base_only"

    def test_identity_columns_are_immutable(self):
        """Test that identity columns never change regardless of input."""

        # Test with various edge cases for registration_number
        test_cases = [
            ("ECI(2022)000001", "ECI(2022)000999", "ECI(2022)000001"),  # Wrong followup
            ("ECI(2022)000001", "", "ECI(2022)000001"),  # Empty followup
            ("ECI(2022)000001", None, "ECI(2022)000001"),  # None followup
            ("ECI(2022)000001", "null", "ECI(2022)000001"),  # String null
        ]

        for base, followup, expected in test_cases:
            result = merge_field_values(base, followup, "registration_number", base)
            assert result == expected, f"Failed for base={base}, followup={followup}"

    def test_direct_strategy_function_call(self):
        """Test calling merge_keep_base_only strategy function directly."""

        # Test case 1: Registration number
        result_1 = merge_keep_base_only(
            "ECI(2022)000001",
            "ECI(2022)000002",
            "registration_number",
            "ECI(2022)000001",
        )
        assert result_1 == "ECI(2022)000001", "Should always return base value"

        # Test case 2: Initiative title
        result_2 = merge_keep_base_only(
            "Original Title", "Modified Title", "initiative_title", "ECI(2022)000001"
        )
        assert result_2 == "Original Title", "Should always return base value"

        # Test case 3: Empty base (edge case - shouldn't happen for identity columns)
        result_3 = merge_keep_base_only(
            "", "Some Value", "registration_number", "ECI(2022)000001"
        )
        assert result_3 == "", "Should return empty base even if followup has value"
