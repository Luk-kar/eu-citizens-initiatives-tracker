"""
Test suite for ECI model data quality: Cross-field data integrity checks.

These tests validate cross-field data integrity checks in extracted
European Citizens' Initiative response data.
"""

# Standard library
import json
from datetime import datetime, timedelta
from typing import Any, List, Optional
from urllib.parse import unquote

# Third-party
import pytest

# Local
from ECI_initiatives.extractor.responses.model import ECICommissionResponseRecord
from .validation_helpers import (
    parse_json_safely,
)


class TestCrossFieldDataIntegrity:
    """Test cross-field relationships and data integrity"""

    def _normalize_registration_number_for_url(self, reg_num: str) -> List[str]:
        """
        Generate possible URL representations of a registration number.

        Args:
            reg_num: Registration number like "2012/000003"

        Returns:
            List of possible URL encodings
        """
        # Original: 2012/000003
        # URL encoded: 2012%2F000003
        # Underscore: 2012_000003
        # Dash: 2012-000003
        variations = [
            reg_num,  # Original
            reg_num.replace("/", "%2F"),  # URL encoded
            reg_num.replace("/", "_"),  # Underscore
            reg_num.replace("/", "-"),  # Dash
        ]
        return variations

    def test_initiative_url_matches_registration_number(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """
        Verify initiative_url contains the registration_number.

        The initiative URL should include the registration number to link to
        the correct initiative detail page. This ensures proper cross-referencing
        between response data and initiative metadata.
        """
        mismatches = []

        for record in complete_dataset:
            if not record.initiative_url or not record.registration_number:
                continue

            # Check if any variation of the registration number appears in URL
            url_variations = self._normalize_registration_number_for_url(
                record.registration_number
            )

            # Decode URL to handle percent encoding
            decoded_url = unquote(record.initiative_url)

            # Check if any variation is in the URL
            found = any(variation in decoded_url for variation in url_variations)

            if not found:
                mismatches.append(
                    (
                        record.registration_number,
                        record.initiative_url,
                    )
                )

        assert not mismatches, (
            f"Found {len(mismatches)} records where initiative_url doesn't contain registration_number:\n"
            + "\n".join(f"  - {reg_num}\n    URL: {url}" for reg_num, url in mismatches)
            + "\n\nInitiative URLs should contain the initiative's registration number."
        )

    def test_submission_text_mentions_submission_date(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """
        Verify submission_text references the commission_submission_date.

        The submission text typically mentions when the initiative was submitted
        to the Commission. This test validates that the extracted submission date
        matches what's stated in the submission text, catching potential date
        extraction errors.

        Note: This test allows some flexibility as dates may be formatted
        differently in text (e.g., "4 March 2025" vs "2025-03-04").
        """
        date_mismatches = []

        for record in complete_dataset:
            if not record.submission_text or not record.commission_submission_date:
                continue

            # Parse the submission date
            try:
                submission_date = datetime.strptime(
                    record.commission_submission_date, "%Y-%m-%d"
                )
            except ValueError:
                continue

            # Generate possible date representations in text
            # e.g., "4 March 2025", "March 4, 2025", "04/03/2025", "2025-03-04"
            date_patterns = [
                submission_date.strftime("%d %B %Y"),  # 04 March 2025
                submission_date.strftime("%-d %B %Y"),  # 4 March 2025 (no leading zero)
                submission_date.strftime("%B %d, %Y"),  # March 04, 2025
                submission_date.strftime("%B %-d, %Y"),  # March 4, 2025
                submission_date.strftime("%Y-%m-%d"),  # 2025-03-04
                submission_date.strftime("%d/%m/%Y"),  # 04/03/2025
                str(submission_date.year),  # At least the year should appear
            ]

            # Check if any date pattern appears in submission text
            text_lower = record.submission_text.lower()
            found = any(pattern.lower() in text_lower for pattern in date_patterns)

            if not found:
                date_mismatches.append(
                    (
                        record.registration_number,
                        record.commission_submission_date,
                        record.submission_text[:150],
                    )
                )

        # Note: This test may have false positives if submission text doesn't mention dates
        # Only fail if there are many mismatches (suggests systematic issue)
        if len(date_mismatches) > len(complete_dataset) * 0.3:  # More than 30%
            pytest.fail(
                f"Found {len(date_mismatches)} records where submission_text doesn't mention submission_date:\n"
                + "\n".join(
                    f"  - {reg_num} (date: {date})\n    Text preview: {text}..."
                    for reg_num, date, text in date_mismatches[:10]  # Show first 10
                )
                + f"\n\n... and {len(date_mismatches) - 10} more"
                if len(date_mismatches) > 10
                else ""
            )

    def test_actions_dates_fall_within_initiative_timeline(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """
        Verify action dates in laws_actions/policies_actions are chronologically sound.

        Action dates should fall within a reasonable timeframe:
        - Not before 2012 (when the ECI system started)
        - Not more than 10 years in the future (unrealistic planning horizon)

        Note: Action dates CAN predate the initiative's submission date, as the
        Commission may reference existing or already-proposed legislation that
        addresses the initiative's goals. This is a common and valid response pattern.
        """
        chronological_issues = []

        # ECI system started in 2012
        eci_start_date = datetime(2012, 1, 1)
        # Reasonable future horizon (10 years from now)
        reasonable_future = datetime.now() + timedelta(days=365 * 10)

        for record in complete_dataset:

            # Check laws_actions dates
            laws = parse_json_safely(record.laws_actions)

            if laws and isinstance(laws, list):

                for i, action in enumerate(laws):

                    if isinstance(action, dict):

                        # Check various date fields
                        date_fields = [
                            "date",
                            "implementation_date",
                            "adoption_date",
                            "entry_into_force",
                        ]

                        for field_name in date_fields:

                            if field_name in action and action[field_name]:

                                try:
                                    action_date = datetime.strptime(
                                        action[field_name], "%Y-%m-%d"
                                    )

                                    # The legal action CAN BE COVERED BEFORE SUBMISSION!

                                    # Check if date is before ECI started
                                    if action_date < eci_start_date:
                                        chronological_issues.append(
                                            (
                                                record.registration_number,
                                                f"laws_actions[{i}].{field_name}",
                                                action[field_name],
                                                "Date before ECI system started (2012)",
                                            )
                                        )

                                    # Check if date is too far in future
                                    elif action_date > reasonable_future:
                                        chronological_issues.append(
                                            (
                                                record.registration_number,
                                                f"laws_actions[{i}].{field_name}",
                                                action[field_name],
                                                "Date more than 10 years in future",
                                            )
                                        )

                                except ValueError:
                                    pass  # Invalid date format caught by other tests

            # Check policies_actions dates
            policies = parse_json_safely(record.policies_actions)

            if policies and isinstance(policies, list):

                for i, action in enumerate(policies):

                    if isinstance(action, dict):
                        date_fields = [
                            "date",
                            "implementation_date",
                            "adoption_date",
                            "deadline",
                        ]

                        for field_name in date_fields:
                            if field_name in action and action[field_name]:
                                try:
                                    action_date = datetime.strptime(
                                        action[field_name], "%Y-%m-%d"
                                    )

                                    # The policies action CAN BE COVERED BEFORE SUBMISSION!

                                    # Check if date is before ECI started
                                    if action_date < eci_start_date:
                                        chronological_issues.append(
                                            (
                                                record.registration_number,
                                                f"policies_actions[{i}].{field_name}",
                                                action[field_name],
                                                "Date before ECI system started (2012)",
                                            )
                                        )

                                    # Check if date is too far in future
                                    elif action_date > reasonable_future:
                                        chronological_issues.append(
                                            (
                                                record.registration_number,
                                                f"policies_actions[{i}].{field_name}",
                                                action[field_name],
                                                "Date more than 10 years in future",
                                            )
                                        )

                                except ValueError:
                                    pass

        assert not chronological_issues, (
            f"Found {len(chronological_issues)} action dates with chronological issues:\n"
            + "\n".join(
                f"  - {reg_num} {field}: {date} ({issue})"
                for reg_num, field, date, issue in chronological_issues
            )
            + "\n\nAction dates should fall within reasonable ECI timeline (2012 - present + 10 years)."
        )
