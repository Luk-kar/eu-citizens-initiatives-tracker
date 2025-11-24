"""
Test suite for ECI model data quality: Date format and chronological order validation.

These tests validate date format and chronological order validation in extracted
European Citizens' Initiative response data.
"""

from datetime import datetime, date, timedelta
from typing import List, Optional, Any, Set
import re

import pytest

from ECI_initiatives.extractor.responses.model import ECICommissionResponseRecord

from .validation_helpers import (
    ISO_DATE_PATTERN,
)

# Once when the test starts
TODAY = date.today()


class TestDateFieldsConsistency:
    """Test data quality and consistency of date-related fields"""

    def _parse_date(
        self, date_string: Optional[str], field_name: str, registration_number: str
    ) -> Optional[date]:
        """
        Parse ISO date string to date object with validation.

        Args:
            date_string: Date string in ISO format (YYYY-MM-DD) or None
            field_name: Name of the field being parsed (for error messages)
            registration_number: Initiative registration number (for error messages)

        Returns:
            date object or None if date_string is None

        Raises:
            AssertionError: If date format is invalid
        """
        if date_string is None:
            return None

        assert ISO_DATE_PATTERN.match(date_string), (
            f"Invalid date format in {field_name} for {registration_number}: "
            f"expected YYYY-MM-DD, got '{date_string}'"
        )

        try:
            return datetime.strptime(date_string, "%Y-%m-%d").date()
        except ValueError as e:
            pytest.fail(
                f"Invalid date value in {field_name} for {registration_number}: "
                f"{date_string} - {e}"
            )

    def _assert_date_before(
        self,
        earlier_date: Optional[str],
        later_date: Optional[str],
        earlier_field: str,
        later_field: str,
        registration_number: str,
    ) -> None:
        """
        Assert that earlier_date comes before later_date (when both are present).

        Args:
            earlier_date: Date that should come first
            later_date: Date that should come after
            earlier_field: Name of the earlier field (for error messages)
            later_field: Name of the later field (for error messages)
            registration_number: Initiative registration number (for error messages)

        Raises:
            AssertionError: If chronological order is violated
        """
        # Skip if either date is None
        if earlier_date is None or later_date is None:
            return

        date1 = self._parse_date(earlier_date, earlier_field, registration_number)
        date2 = self._parse_date(later_date, later_field, registration_number)

        assert date1 <= date2, (
            f"Chronological inconsistency for {registration_number}: "
            f"{earlier_field} ({earlier_date}) should be before or equal to "
            f"{later_field} ({later_date})"
        )

    def _get_date_fields(
        self, record: ECICommissionResponseRecord
    ) -> List[tuple[str, Optional[str]]]:
        """
        Get all date fields from record as (field_name, value) tuples.

        Args:
            record: The ECI response record

        Returns:
            List of (field_name, date_value) tuples
        """
        return [
            ("commission_submission_date", record.commission_submission_date),
            ("commission_meeting_date", record.commission_meeting_date),
            ("parliament_hearing_date", record.parliament_hearing_date),
            ("plenary_debate_date", record.plenary_debate_date),
            (
                "official_communication_adoption_date",
                record.official_communication_adoption_date,
            ),
            ("law_implementation_date", record.law_implementation_date),
            ("followup_latest_date", record.followup_latest_date),
            ("followup_most_future_date", record.followup_most_future_date),
        ]

    def test_all_dates_follow_iso_format(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """Verify all date fields follow ISO 8601 format (YYYY-MM-DD)"""
        for record in complete_dataset:
            date_fields = self._get_date_fields(record)

            for field_name, date_value in date_fields:
                if date_value is not None:
                    # This will raise AssertionError if format is invalid
                    self._parse_date(date_value, field_name, record.registration_number)

    def test_commission_submission_date_before_meeting_date(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """Verify submission date precedes commission meeting date"""
        for record in complete_dataset:
            self._assert_date_before(
                earlier_date=record.commission_submission_date,
                later_date=record.commission_meeting_date,
                earlier_field="commission_submission_date",
                later_field="commission_meeting_date",
                registration_number=record.registration_number,
            )

    def test_commission_meeting_date_before_parliament_hearing(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """Verify meeting date precedes parliament hearing date"""
        for record in complete_dataset:
            self._assert_date_before(
                earlier_date=record.commission_meeting_date,
                later_date=record.parliament_hearing_date,
                earlier_field="commission_meeting_date",
                later_field="parliament_hearing_date",
                registration_number=record.registration_number,
            )

    def test_parliament_hearing_before_plenary_debate(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """Verify parliament hearing date precedes plenary debate date"""
        for record in complete_dataset:
            self._assert_date_before(
                earlier_date=record.parliament_hearing_date,
                later_date=record.plenary_debate_date,
                earlier_field="parliament_hearing_date",
                later_field="plenary_debate_date",
                registration_number=record.registration_number,
            )

    def test_plenary_debate_before_communication_adoption(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """Verify plenary debate date precedes communication adoption date"""
        for record in complete_dataset:
            self._assert_date_before(
                earlier_date=record.plenary_debate_date,
                later_date=record.official_communication_adoption_date,
                earlier_field="plenary_debate_date",
                later_field="official_communication_adoption_date",
                registration_number=record.registration_number,
            )

    def test_law_implementation_date_after_communication_adoption(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """Verify law implementation date comes after communication adoption"""
        for record in complete_dataset:
            self._assert_date_before(
                earlier_date=record.official_communication_adoption_date,
                later_date=record.law_implementation_date,
                earlier_field="official_communication_adoption_date",
                later_field="law_implementation_date",
                registration_number=record.registration_number,
            )

    def test_followup_latest_date_is_chronologically_sound(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """Verify followup_latest_date is after communication adoption date"""
        for record in complete_dataset:
            self._assert_date_before(
                earlier_date=record.official_communication_adoption_date,
                later_date=record.followup_latest_date,
                earlier_field="official_communication_adoption_date",
                later_field="followup_latest_date",
                registration_number=record.registration_number,
            )

    def test_followup_most_future_date_is_after_latest_date(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """Verify followup_most_future_date is >= followup_latest_date when both present"""
        for record in complete_dataset:
            self._assert_date_before(
                earlier_date=record.followup_latest_date,
                later_date=record.followup_most_future_date,
                earlier_field="followup_latest_date",
                later_field="followup_most_future_date",
                registration_number=record.registration_number,
            )

    def test_dates_are_not_in_future(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """Verify historical dates are not set in the future"""
        today = TODAY

        # Fields that should not be in the future (exclude future deadlines)
        historical_fields = [
            "commission_submission_date",
            "commission_meeting_date",
            "parliament_hearing_date",
            "plenary_debate_date",
            "official_communication_adoption_date",
        ]

        for record in complete_dataset:
            for field_name in historical_fields:
                date_value = getattr(record, field_name)

                if date_value is not None:
                    parsed_date = self._parse_date(
                        date_value, field_name, record.registration_number
                    )

                    assert parsed_date <= today, (
                        f"Future date in {field_name} for {record.registration_number}: "
                        f"{date_value} is after today ({today})"
                    )
