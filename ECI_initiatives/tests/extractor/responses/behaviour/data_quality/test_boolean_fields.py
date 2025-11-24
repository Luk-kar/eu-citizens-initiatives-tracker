"""
Test suite for ECI model data quality: Boolean field validation and consistency.

These tests validate boolean field validation and consistency in extracted
European Citizens' Initiative response data.
"""

from typing import List, Any

from ECI_initiatives.extractor.responses.model import ECICommissionResponseRecord
from .validation_helpers import normalize_boolean, is_empty_value


class TestBooleanFieldsConsistency:
    """Test consistency of boolean flag fields"""

    # Define all boolean fields in the data model
    BOOLEAN_FIELDS = {
        "commission_promised_new_law",
        "commission_rejected_initiative",
        "has_followup_section",
        "has_roadmap",
        "has_workshop",
        "has_partnership_programs",
    }

    def _get_field_value_type(self, value: Any) -> str:
        """
        Get a descriptive type name for error reporting.

        Args:
            value: Value to describe

        Returns:
            Human-readable type description
        """
        if value is None:
            return "None"

        elif value is True:
            return "True (bool)"

        elif value is False:
            return "False (bool)"

        elif isinstance(value, str):
            return f"'{value}' (string)"

        elif isinstance(value, int):
            return f"{value} (int)"

        elif isinstance(value, float):
            return f"{value} (float)"

        else:
            return f"{type(value).__name__}"

    def test_boolean_fields_are_true_or_false(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """
        Verify boolean fields contain only True or False values after normalization.

        Boolean flags from CSV may be stored as strings ("True", "False") which is
        acceptable as long as they can be normalized to proper Python booleans.
        This test validates that all boolean field values are normalizable to
        True or False. None is not accepted.
        """
        invalid_boolean_values = []

        for record in complete_dataset:
            for field_name in self.BOOLEAN_FIELDS:
                raw_value = getattr(record, field_name, None)

                try:
                    normalized_value = normalize_boolean(raw_value)
                    # Verify it's actually a boolean
                    if not isinstance(normalized_value, bool):
                        invalid_boolean_values.append(
                            (
                                record.registration_number,
                                field_name,
                                raw_value,
                                self._get_field_value_type(raw_value),
                            )
                        )
                except (ValueError, TypeError):
                    # Normalization failed - invalid value
                    invalid_boolean_values.append(
                        (
                            record.registration_number,
                            field_name,
                            raw_value,
                            self._get_field_value_type(raw_value),
                        )
                    )

        assert not invalid_boolean_values, (
            f"Found {len(invalid_boolean_values)} boolean fields with "
            "invalid/non-normalizable values:\n"
            + "\n".join(
                f"  - {reg_num}.{field}: {value_type}"
                for reg_num, field, value, value_type in invalid_boolean_values
            )
            + "\n\nBoolean fields must be normalizable to True or False (not None).\n"
            + "Acceptable formats: True/False (bool), 'True'/'False' (string), '1'/'0', 'yes'/'no'"
        )

    def test_rejection_flag_implies_rejection_reason(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """
        Verify commission_rejected_initiative=True correlates with rejection_reason.

        If commission_rejected_initiative is True, there should be a
        commission_rejection_reason explaining why the initiative was rejected.
        Missing rejection reasons indicate incomplete data extraction.

        Note: The Commission can reject an ECI while still promising new legislation
        to address some of the underlying issues. These are not contradictory positions.
        """
        missing_reasons = []

        for record in complete_dataset:
            # Normalize boolean value
            rejected = normalize_boolean(record.commission_rejected_initiative)

            # If rejected flag is True, reason should exist
            if rejected is True:
                if not record.commission_rejection_reason or (
                    isinstance(record.commission_rejection_reason, str)
                    and not record.commission_rejection_reason.strip()
                ):
                    missing_reasons.append(
                        (
                            record.registration_number,
                            record.initiative_title,
                        )
                    )

        assert not missing_reasons, (
            f"Found {len(missing_reasons)} records with commission_rejected_initiative=True "
            f"but missing commission_rejection_reason:\n"
            + "\n".join(
                f"  - {reg_num}: {title[:60]}..." for reg_num, title in missing_reasons
            )
            + "\n\nRejected initiatives must have a rejection reason for transparency."
        )

    def test_promised_law_flag_distribution(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """
        Verify commission_promised_new_law has reasonable value distribution.

        This test checks that the promised_new_law flag isn't stuck on a single
        value (all True or all False), which would suggest a scraping bug.
        We expect a mix of True and False values.
        """
        value_counts = {
            True: 0,
            False: 0,
        }

        for record in complete_dataset:
            # Normalize the value
            normalized_value = normalize_boolean(record.commission_promised_new_law)
            if normalized_value in value_counts:
                value_counts[normalized_value] += 1

        total = len(complete_dataset)

        # Generate distribution report
        print("\n" + "=" * 70)
        print("COMMISSION_PROMISED_NEW_LAW DISTRIBUTION")
        print("=" * 70)
        print(f"\nTotal initiatives: {total}")
        print("\nValue distribution:")
        print(
            f"  - True (promised new law):  {value_counts[True]:3d} ({value_counts[True]/total:.1%})"
        )
        print(
            f"  - False (no new law):       {value_counts[False]:3d} ({value_counts[False]/total:.1%})"
        )
        print("=" * 70 + "\n")

        # Fail if all values are the same (suggests scraper bug)
        unique_values = sum(1 for count in value_counts.values() if count > 0)

        assert unique_values == 2, (
            f"commission_promised_new_law has only {unique_values} unique value(s):\n"
            f"  - True: {value_counts[True]}\n"
            f"  - False: {value_counts[False]}\n\n"
            f"This suggests a scraping bug where the field isn't being properly extracted.\n"
            f"Expected both True and False values."
        )

    def test_followup_section_flag_consistency(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """
        Verify has_followup_section flag is consistent with presence of followup data.

        If has_followup_section=True, at least one of these should exist:
        - followup_events_with_dates
        - followup_latest_date
        - followup_most_future_date
        - followup_dedicated_website

        Conversely, if any followup data exists, flag should be True.
        """
        inconsistencies = []

        for record in complete_dataset:
            # Normalize the boolean flag
            has_flag = normalize_boolean(record.has_followup_section)

            # Check if any followup data exists
            has_followup_data = (
                not is_empty_value(record.followup_events_with_dates)
                or not is_empty_value(record.followup_latest_date)
                or not is_empty_value(record.followup_most_future_date)
                or not is_empty_value(record.followup_dedicated_website)
            )

            # Flag=True but no data
            if has_flag is True and not has_followup_data:
                inconsistencies.append(
                    (
                        record.registration_number,
                        "has_followup_section=True but no followup data found",
                    )
                )

            # Data exists but flag is False
            if has_followup_data and has_flag is not True:
                inconsistencies.append(
                    (
                        record.registration_number,
                        "has_followup_section=False but followup data exists",
                    )
                )

        assert not inconsistencies, (
            f"Found {len(inconsistencies)} records with has_followup_section inconsistencies:\n"
            + "\n".join(f"  - {reg_num}: {issue}" for reg_num, issue in inconsistencies)
            + "\n\nThe has_followup_section flag should accurately reflect presence of followup data."
        )

    def test_all_boolean_fields_present_and_valid(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """
        Verify all boolean fields are present and set to True or False.

        Every boolean field must be explicitly set - no missing or None values allowed.
        This ensures complete data extraction for all boolean flags.
        """
        records_with_missing_flags = []

        for record in complete_dataset:
            missing_fields = []

            for field_name in self.BOOLEAN_FIELDS:
                raw_value = getattr(record, field_name, None)

                # Check if field is missing or None
                if raw_value is None:
                    missing_fields.append(field_name)
                else:
                    # Try to normalize - will raise error if invalid
                    try:
                        normalize_boolean(raw_value)
                    except (ValueError, TypeError):
                        missing_fields.append(f"{field_name} (invalid value)")

            if missing_fields:
                records_with_missing_flags.append(
                    (
                        record.registration_number,
                        record.initiative_title,
                        missing_fields,
                    )
                )

        assert not records_with_missing_flags, (
            f"Found {len(records_with_missing_flags)} records with missing/invalid boolean flags:\n"
            + "\n".join(
                f"  - {reg_num}: {title[:50]}... | Missing: {', '.join(fields)}"
                for reg_num, title, fields in records_with_missing_flags
            )
            + "\n\nAll boolean flags must be explicitly set to True or False.\n"
            + "This suggests the scraper isn't extracting boolean field data for these initiatives."
        )

    def test_rejected_records_have_rejection_flag(
        self, records_rejected: List[ECICommissionResponseRecord]
    ):
        """
        Verify records in the 'rejected' category have commission_rejected_initiative=True.

        Uses the records_rejected fixture which identifies initiatives known to be rejected.
        All of these should have the rejection flag set to True.
        """
        missing_flag = []

        for record in records_rejected:
            rejected = normalize_boolean(record.commission_rejected_initiative)

            if rejected is not True:
                missing_flag.append(
                    (
                        record.registration_number,
                        f"Expected rejected=True, got {rejected}",
                    )
                )

        assert not missing_flag, (
            f"Found {len(missing_flag)} rejected records without rejection flag set to True:\n"
            + "\n".join(f"  - {reg_num}: {issue}" for reg_num, issue in missing_flag)
            + "\n\nRecords in 'rejected' category must have commission_rejected_initiative=True."
        )
