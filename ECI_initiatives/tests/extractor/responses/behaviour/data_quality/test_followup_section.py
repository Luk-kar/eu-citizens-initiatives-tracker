"""
Test suite for ECI model data quality: Follow-up section data consistency.

These tests validate follow-up section data consistency in extracted
European Citizens' Initiative response data.
"""

from typing import List, Optional
import json

import pytest

from ECI_initiatives.extractor.responses.model import ECICommissionResponseRecord
from .validation_helpers import (
    parse_json_safely,
    normalize_boolean,
)


class TestFollowupSectionConsistency:
    """Test consistency of follow-up section flags and data"""

    def _is_empty_or_none(self, value: any) -> bool:
        """
        Check if a value is None or empty (for strings, lists, etc.).

        Args:
            value: Value to check

        Returns:
            True if value is None, empty string, empty list, "null", etc.
        """
        if value is None:
            return True

        # Handle string "null" from JSON serialization
        if isinstance(value, str):
            return value.strip() in ("", "null", "[]", "{}")

        # Handle empty containers
        if isinstance(value, (list, dict, set, tuple)):
            return len(value) == 0

        return False

    def _normalize_boolean(self, value: any) -> Optional[bool]:
        """
        Normalize boolean-like values to actual booleans.

        Args:
            value: Value to normalize (bool, str, None)

        Returns:
            True, False, or None
        """
        if value is None:
            return None

        if isinstance(value, bool):
            return value

        # Handle string representations
        if isinstance(value, str):
            value_lower = value.lower().strip()
            if value_lower in ("true", "1", "yes"):
                return True
            elif value_lower in ("false", "0", "no", ""):
                return False

        # Handle numeric (pandas may convert to 1/0)
        if isinstance(value, (int, float)):
            return bool(value)

        return None

    def test_followup_section_implies_followup_data(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """
        Verify has_followup_section=True when any followup data exists.

        If the initiative has follow-up data (events, latest dates, future dates),
        the has_followup_section flag should be True. Conversely, if the flag is True,
        at least some follow-up data should exist.
        """
        inconsistencies = []

        for record in complete_dataset:
            flag_value = normalize_boolean(record.has_followup_section)

            # Check if any followup data exists
            has_followup_data = (
                not self._is_empty_or_none(record.followup_events_with_dates)
                or record.followup_latest_date is not None
                or record.followup_most_future_date is not None
                or not self._is_empty_or_none(record.followup_dedicated_website)
            )

            # If flag says True, data should exist
            if flag_value is True and not has_followup_data:

                inconsistencies.append(
                    (
                        record.registration_number,
                        "has_followup_section=True but no followup data found",
                    )
                )

            # If data exists, flag should be True
            if has_followup_data and flag_value is not True:

                inconsistencies.append(
                    (
                        record.registration_number,
                        f"has_followup_section={flag_value} but followup data exists",
                    )
                )

        assert not inconsistencies, (
            f"Found {len(inconsistencies)} records with has_followup_section flag inconsistencies:\n"
            + "\n".join(f"  - {reg_num}: {issue}" for reg_num, issue in inconsistencies)
        )

    def test_roadmap_flag_aligns_with_actions(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """
        Verify has_roadmap=True correlates with roadmap entries in policies_actions.

        If has_roadmap is True, there should be policy actions that reference
        a roadmap, action plan, or strategy document. This ensures the flag
        accurately reflects the content.
        """
        inconsistencies = []

        # Keywords that indicate roadmap-related actions
        roadmap_keywords = [
            "roadmap",
            "action plan",
            "strategy",
            "road map",
            "implementation plan",
            "work programme",
        ]

        for record in complete_dataset:
            flag_value = normalize_boolean(record.has_roadmap)

            # Flag must be explicitly set (True or False), not None
            if flag_value is None:
                pytest.fail(
                    f"has_roadmap must be boolean (True/False), got None for {record.registration_number}\n"
                    f"Initiative: {record.initiative_title[:80]}...\n"
                    f"This boolean flag must be explicitly set during scraping to indicate "
                    f"whether the Commission response includes a roadmap or action plan.\n"
                    f"Check the roadmap extraction logic in the scraper."
                )

            # Parse policies_actions to check for roadmap content
            policies = parse_json_safely(record.policies_actions)
            has_roadmap_content = False

            if policies and isinstance(policies, list):

                for policy in policies:

                    if isinstance(policy, dict):
                        # Check description for roadmap keywords
                        description = policy.get("description", "").lower()
                        policy_type = policy.get("type", "").lower()

                        if any(
                            keyword in description or keyword in policy_type
                            for keyword in roadmap_keywords
                        ):
                            has_roadmap_content = True
                            break

            # If flag is True, should have roadmap content
            if flag_value is True and not has_roadmap_content:
                inconsistencies.append(
                    (
                        record.registration_number,
                        "has_roadmap=True but no roadmap-related policies found",
                    )
                )

        assert not inconsistencies, (
            f"Found {len(inconsistencies)} records with has_roadmap flag inconsistencies:\n"
            + "\n".join(f"  - {reg_num}: {issue}" for reg_num, issue in inconsistencies)
            + "\n\nNote: This test checks if policies_actions contain roadmap-related keywords."
        )

    def test_workshop_flag_aligns_with_events(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """
        Verify has_workshop=True correlates with workshop events in followup data.

        If has_workshop is True, there should be follow-up events that reference
        workshops, seminars, or similar participatory events. This validates that
        the workshop flag reflects actual events in the data.
        """
        inconsistencies = []

        # Keywords that indicate workshop-related events
        workshop_keywords = [
            # Workshops
            "workshop",
            "workshops",
            # Conferences
            "conference",
            "conferences",
            # Scientific/academic engagement events
            "scientific conference",
            "scientific debate",
            # Stakeholder engagement events
            "stakeholder meeting",
            "stakeholder meetings",
            "stakeholder conference",
            "stakeholder debate",
            # Organized/planned events (suggests intentional activity)
            "organised workshop",
            "organized workshop",
            "organised conference",
            "organized conference",
            # Series/multiple events
            "series of workshops",
            "series of conferences",
            # Other formal engagement formats
            "roundtable",
            "symposium",
            "seminar",
            "seminars",
        ]

        for record in complete_dataset:
            flag_value = normalize_boolean(record.has_workshop)

            # Flag must be explicitly set (True or False), not None
            if flag_value is None:
                pytest.fail(
                    f"has_workshop must be boolean (True/False), got None for {record.registration_number}\n"
                    f"Initiative: {record.initiative_title[:80]}...\n"
                    f"This boolean flag must be explicitly set during scraping to indicate "
                    f"whether the Commission response includes workshops or similar participatory events.\n"
                    f"Check the workshop extraction logic in the scraper."
                )

            # Parse followup_events_with_dates to check for workshop content
            events = parse_json_safely(record.followup_events_with_dates)
            has_workshop_content = False

            if events and isinstance(events, list):
                for event in events:
                    if isinstance(event, dict):
                        # Check action description for workshop keywords
                        action = event.get("action", "").lower()

                        if any(keyword in action for keyword in workshop_keywords):
                            has_workshop_content = True
                            break

            # If flag is True, should have workshop content
            if flag_value is True and not has_workshop_content:
                inconsistencies.append(
                    (
                        record.registration_number,
                        "has_workshop=True but no workshop-related events found",
                    )
                )

        assert not inconsistencies, (
            f"Found {len(inconsistencies)} records with has_workshop flag inconsistencies:\n"
            + "\n".join(f"  - {reg_num}: {issue}" for reg_num, issue in inconsistencies)
            + "\n\nNote: This test checks if followup_events_with_dates contain workshop-related keywords."
        )

    def test_partnership_programs_flag_aligns_with_data(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """
        Verify has_partnership_programs=True when partnership data exists.

        If has_partnership_programs is True, there should be follow-up events or
        policy actions that reference partnerships, collaboration programs, or
        multi-stakeholder initiatives. This ensures the flag is accurately set.
        """
        inconsistencies = []

        # Keywords that indicate partnership-related content
        partnership_keywords = [
            "partnership program",
            "partnership plans",
            "partnership programmes",
            "public-public partnership",
            "public-public partnerships",
            "european partnership for",
            "partnership between",
            "partnerships between",
            "support to partnerships",
            "cooperation programme",
            "collaboration programme",
            "joint programme",
            "formal partnership",
            "established partnership",
            "international partners",
        ]

        for record in complete_dataset:
            flag_value = normalize_boolean(record.has_partnership_programs)

            # Flag must be explicitly set (True or False), not None
            if flag_value is None:
                pytest.fail(
                    f"has_partnership_programs must be boolean (True/False), got None for {record.registration_number}\n"
                    f"Initiative: {record.initiative_title[:80]}...\n"
                    f"This boolean flag must be explicitly set during scraping to indicate "
                    f"whether the Commission response includes partnership programs or collaboration initiatives.\n"
                    f"Check the partnership program extraction logic in the scraper."
                )

            has_partnership_content = False

            # Check followup events for partnership content
            events = parse_json_safely(record.followup_events_with_dates)

            if events and isinstance(events, list):

                for event in events:
                    if isinstance(event, dict):
                        action = event.get("action", "").lower()
                        if any(keyword in action for keyword in partnership_keywords):
                            has_partnership_content = True
                            break

            # Also check policies for partnership content
            if not has_partnership_content:

                policies = parse_json_safely(record.policies_actions)

                if policies and isinstance(policies, list):

                    for policy in policies:

                        if isinstance(policy, dict):

                            description = policy.get("description", "").lower()
                            if any(
                                keyword in description
                                for keyword in partnership_keywords
                            ):
                                has_partnership_content = True
                                break

            # If flag is True, should have partnership content
            if flag_value is True and not has_partnership_content:
                inconsistencies.append(
                    (
                        record.registration_number,
                        "has_partnership_programs=True but no partnership-related content found",
                    )
                )

        assert not inconsistencies, (
            f"Found {len(inconsistencies)} records with has_partnership_programs flag inconsistencies:\n"
            + "\n".join(f"  - {reg_num}: {issue}" for reg_num, issue in inconsistencies)
            + "\n\nNote: This test checks if events/policies contain partnership-related keywords."
        )

    def test_followup_dates_exist_when_followup_section_exists(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """
        Verify followup dates are populated when has_followup_section=True.

        If an initiative has a follow-up section (has_followup_section=True),
        it should have either followup_latest_date or followup_most_future_date
        (or both) populated. These dates provide temporal context for follow-up
        actions and are key metadata for tracking implementation progress.
        """
        missing_dates = []

        for record in complete_dataset:
            flag_value = normalize_boolean(record.has_followup_section)

            # Flag must be explicitly set (True or False), not None
            if flag_value is None:
                pytest.fail(
                    f"has_followup_section must be boolean (True/False), got None for {record.registration_number}\n"
                    f"Initiative: {record.initiative_title[:80]}...\n"
                    f"This boolean flag must be explicitly set during scraping to indicate "
                    f"whether the Commission response includes a follow-up section with implementation updates.\n"
                    f"Check the follow-up section detection logic in the scraper."
                )

            # If followup section exists, at least one date should exist
            if flag_value is True:
                has_dates = (
                    record.followup_latest_date is not None
                    or record.followup_most_future_date is not None
                )

                if not has_dates:
                    missing_dates.append(
                        (
                            record.registration_number,
                            record.initiative_title,
                        )
                    )

        assert not missing_dates, (
            f"Found {len(missing_dates)} records with has_followup_section=True "
            f"but missing both followup_latest_date and followup_most_future_date:\n"
            + "\n".join(
                f"  - {reg_num}: {title[:60]}..." for reg_num, title in missing_dates
            )
            + "\n\nFollow-up sections should have at least one temporal reference date."
        )
