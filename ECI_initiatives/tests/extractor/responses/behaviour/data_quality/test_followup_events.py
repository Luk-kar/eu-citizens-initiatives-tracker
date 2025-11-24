"""
Test suite for ECI model data quality: Follow-up events structure validation.

These tests validate follow-up events structure validation in extracted
European Citizens' Initiative response data.
"""

import json
import re
from datetime import datetime
from typing import Any, List, Optional

from ECI_initiatives.extractor.responses.model import ECICommissionResponseRecord
from .validation_helpers import (
    parse_json_safely,
    validate_date_format,
)


class TestFollowupEventsStructure:
    """Test structure of followup_events_with_dates field"""

    # ISO 8601 date format pattern (YYYY-MM-DD)
    ISO_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")

    def _validate_date_format(self, date_string: str) -> bool:
        """
        Validate that a date string follows ISO 8601 format (YYYY-MM-DD).

        Args:
            date_string: Date string to validate

        Returns:
            True if valid ISO date format
        """
        if not isinstance(date_string, str):
            return False

        if not self.ISO_DATE_PATTERN.match(date_string):
            return False

        # Also validate it's a real date (not 2024-13-45)
        try:
            datetime.strptime(date_string, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    def test_followup_event_dates_are_valid_iso_format(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """
        Verify dates in followup events follow ISO format.

        The followup_events_with_dates field contains a list of events, where each
        event has a 'dates' field (list of date strings) and an 'action' field
        (description string).

        Expected structure:
        [
            {
                "dates": ["2015-10-28", "2016-05-12"],
                "action": "Amendment to the Drinking Water Directive..."
            },
            {
                "dates": [],
                "action": "For further updates, check the dedicated web page."
            }
        ]

        All dates must follow ISO 8601 format (YYYY-MM-DD) for consistency
        and machine readability.
        """
        invalid_dates = []
        structural_issues = []

        for record in complete_dataset:
            # Skip if no followup events
            if not record.followup_events_with_dates:
                continue

            # Parse JSON
            events = parse_json_safely(record.followup_events_with_dates)

            if events is None:
                continue

            # Validate it's a list
            if not isinstance(events, list):
                structural_issues.append(
                    (
                        record.registration_number,
                        f"followup_events_with_dates must be list, got {type(events).__name__}",
                    )
                )
                continue

            # Validate each event
            for i, event in enumerate(events):
                # Event must be a dictionary
                if not isinstance(event, dict):
                    structural_issues.append(
                        (
                            record.registration_number,
                            f"followup_events_with_dates[{i}] must be dict, got {type(event).__name__}",
                        )
                    )
                    continue

                # Event must have 'dates' field
                if "dates" not in event:
                    structural_issues.append(
                        (
                            record.registration_number,
                            f"followup_events_with_dates[{i}] missing 'dates' field",
                        )
                    )
                    continue

                # Event must have 'action' field
                if "action" not in event:
                    structural_issues.append(
                        (
                            record.registration_number,
                            f"followup_events_with_dates[{i}] missing 'action' field",
                        )
                    )
                    continue

                # 'dates' must be a list
                dates_field = event["dates"]
                if not isinstance(dates_field, list):
                    structural_issues.append(
                        (
                            record.registration_number,
                            f"followup_events_with_dates[{i}]['dates'] must be list, got {type(dates_field).__name__}",
                        )
                    )
                    continue

                # Validate each date in the list
                for j, date_string in enumerate(dates_field):
                    if not validate_date_format(date_string):
                        invalid_dates.append(
                            (
                                record.registration_number,
                                f"followup_events_with_dates[{i}]['dates'][{j}]",
                                (
                                    date_string
                                    if isinstance(date_string, str)
                                    else str(date_string)
                                ),
                            )
                        )

        # Assert no structural issues
        assert not structural_issues, (
            f"Found {len(structural_issues)} followup_events_with_dates with structural issues:\n"
            + "\n".join(
                f"  - {reg_num}: {issue}" for reg_num, issue in structural_issues
            )
            + '\n\nExpected structure: [{"dates": ["YYYY-MM-DD"], "action": "..."}]'
        )

        # Assert no invalid dates
        assert not invalid_dates, (
            f"Found {len(invalid_dates)} followup event dates with invalid ISO format:\n"
            + "\n".join(
                f"  - {reg_num} {field}: '{date_value}' (expected YYYY-MM-DD)"
                for reg_num, field, date_value in invalid_dates
            )
            + "\n\nAll dates must follow ISO 8601 format (YYYY-MM-DD) for consistency."
        )

    def test_followup_event_actions_are_not_empty(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """
        Verify action descriptions in followup events are not empty.

        Each followup event must have a meaningful action description explaining
        what happened or what is planned. Empty action fields suggest incomplete
        data extraction.
        """
        empty_actions = []

        for record in complete_dataset:

            if not record.followup_events_with_dates:
                continue

            events = parse_json_safely(record.followup_events_with_dates)

            if not events or not isinstance(events, list):
                continue

            for i, event in enumerate(events):

                if isinstance(event, dict):
                    action = event.get("action", "")

                    # Action should be a non-empty string
                    if not action or not isinstance(action, str) or not action.strip():
                        empty_actions.append(
                            (
                                record.registration_number,
                                i,
                            )
                        )

        assert not empty_actions, (
            f"Found {len(empty_actions)} followup events with empty action descriptions:\n"
            + "\n".join(
                f"  - {reg_num}: followup_events_with_dates[{index}]['action'] is empty"
                for reg_num, index in empty_actions
            )
            + "\n\nAll followup events must have meaningful action descriptions."
        )
