"""
Test suite for ECI model data quality: JSON field parsing and structure validation.

These tests validate json field parsing and structure validation in extracted
European Citizens' Initiative response data.
"""

from typing import List, Optional, Any
import json
import pytest

from ECI_initiatives.data_pipeline.extractor.responses.model import (
    ECICommissionResponseRecord,
)


class TestJSONFieldsValidity:
    """Test data quality of JSON-encoded fields"""

    def _validate_json_parseable(
        self,
        json_string: Optional[str],
        field_name: str,
        registration_number: str,
    ) -> Optional[Any]:
        """
        Validate that a string contains valid, parseable JSON.

        Args:
            json_string: The JSON string to validate (or None)
            field_name: Name of the field being validated (for error messages)
            registration_number: Initiative registration number (for error messages)

        Returns:
            Parsed JSON object (dict, list, etc.) or None if json_string is None

        Raises:
            AssertionError: If JSON is invalid or cannot be parsed
        """
        if json_string is None:
            return None

        try:
            parsed = json.loads(json_string)
            return parsed

        except json.JSONDecodeError as e:
            pytest.fail(
                f"Invalid JSON in {field_name} for {registration_number}:\n"
                f"  Error: {e}\n"
                f"  Position: line {e.lineno}, column {e.colno}\n"
                f"  JSON preview: {json_string[:200]}..."
            )

    def _validate_json_type(
        self,
        parsed_json: Any,
        expected_type: type,
        field_name: str,
        registration_number: str,
    ) -> None:
        """
        Validate that parsed JSON matches expected type.

        Args:
            parsed_json: The parsed JSON object
            expected_type: Expected Python type (dict, list, etc.)
            field_name: Name of the field being validated (for error messages)
            registration_number: Initiative registration number (for error messages)

        Raises:
            AssertionError: If type doesn't match
        """

        # Skip type validation if no deadlines found (JSON "null" → Python None)
        if parsed_json is not None:
            assert isinstance(parsed_json, expected_type), (
                f"Invalid JSON type in {field_name} for {registration_number}:\n"
                f"  Expected: {expected_type.__name__}\n"
                f"  Got: {type(parsed_json).__name__}\n"
                f"  Value: {str(parsed_json)[:200]}..."
            )

    def test_parliament_hearing_video_urls_are_valid_json(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """Verify parliament_hearing_video_urls contains valid JSON when not None"""
        for record in complete_dataset:
            if record.parliament_hearing_video_urls is not None:
                self._validate_json_parseable(
                    json_string=record.parliament_hearing_video_urls,
                    field_name="parliament_hearing_video_urls",
                    registration_number=record.registration_number,
                )

    def test_plenary_debate_video_urls_are_valid_json(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """Verify plenary_debate_video_urls contains valid JSON when not None"""
        for record in complete_dataset:
            if record.plenary_debate_video_urls is not None:
                self._validate_json_parseable(
                    json_string=record.plenary_debate_video_urls,
                    field_name="plenary_debate_video_urls",
                    registration_number=record.registration_number,
                )

    def test_official_communication_document_urls_are_valid_json(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """Verify official_communication_document_urls contains valid JSON when not None"""
        for record in complete_dataset:
            if record.official_communication_document_urls is not None:
                self._validate_json_parseable(
                    json_string=record.official_communication_document_urls,
                    field_name="official_communication_document_urls",
                    registration_number=record.registration_number,
                )

    def test_commission_deadlines_are_valid_json(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """Verify commission_deadlines contains valid JSON dict when not None"""
        for record in complete_dataset:
            if record.commission_deadlines is not None:
                parsed = self._validate_json_parseable(
                    json_string=record.commission_deadlines,
                    field_name="commission_deadlines",
                    registration_number=record.registration_number,
                )

                self._validate_json_type(
                    parsed_json=parsed,
                    expected_type=dict,
                    field_name="commission_deadlines",
                    registration_number=record.registration_number,
                )

    def test_laws_actions_are_valid_json_list(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """Verify laws_actions contains valid JSON array when not None"""
        for record in complete_dataset:
            if record.laws_actions is not None:
                parsed = self._validate_json_parseable(
                    json_string=record.laws_actions,
                    field_name="laws_actions",
                    registration_number=record.registration_number,
                )

                # Validate it's a list
                self._validate_json_type(
                    parsed_json=parsed,
                    expected_type=list,
                    field_name="laws_actions",
                    registration_number=record.registration_number,
                )

    def test_policies_actions_are_valid_json_list(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """Verify policies_actions contains valid JSON array when not None"""
        for record in complete_dataset:
            if record.policies_actions is not None:
                parsed = self._validate_json_parseable(
                    json_string=record.policies_actions,
                    field_name="policies_actions",
                    registration_number=record.registration_number,
                )

                # Validate it's a list
                self._validate_json_type(
                    parsed_json=parsed,
                    expected_type=list,
                    field_name="policies_actions",
                    registration_number=record.registration_number,
                )

    def test_court_cases_referenced_are_valid_json(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """Verify court_cases_referenced contains valid JSON when not None"""
        for record in complete_dataset:
            if record.court_cases_referenced is not None:
                self._validate_json_parseable(
                    json_string=record.court_cases_referenced,
                    field_name="court_cases_referenced",
                    registration_number=record.registration_number,
                )

    def test_referenced_legislation_by_id_are_valid_json(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """Verify referenced_legislation_by_id contains valid JSON when not None"""
        for record in complete_dataset:
            if record.referenced_legislation_by_id is not None:
                self._validate_json_parseable(
                    json_string=record.referenced_legislation_by_id,
                    field_name="referenced_legislation_by_id",
                    registration_number=record.registration_number,
                )

    def test_referenced_legislation_by_name_are_valid_json(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """Verify referenced_legislation_by_name contains valid JSON when not None"""
        for record in complete_dataset:
            if record.referenced_legislation_by_name is not None:
                self._validate_json_parseable(
                    json_string=record.referenced_legislation_by_name,
                    field_name="referenced_legislation_by_name",
                    registration_number=record.registration_number,
                )

    def test_followup_events_with_dates_are_valid_json(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """Verify followup_events_with_dates contains valid JSON list when not None"""
        for record in complete_dataset:
            if record.followup_events_with_dates is not None:
                parsed = self._validate_json_parseable(
                    json_string=record.followup_events_with_dates,
                    field_name="followup_events_with_dates",
                    registration_number=record.registration_number,
                )

                # Validate it's a list
                self._validate_json_type(
                    parsed_json=parsed,
                    expected_type=list,
                    field_name="followup_events_with_dates",
                    registration_number=record.registration_number,
                )

    def test_json_fields_contain_expected_structure(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """Verify JSON fields contain dictionaries/lists with expected keys/structure"""
        for record in complete_dataset:
            # Test laws_actions structure (list of dict with specific keys)
            if record.laws_actions is not None:
                parsed = self._parse_and_validate_json_field(
                    json_string=record.laws_actions,
                    field_name="laws_actions",
                    expected_type=list,
                    registration_number=record.registration_number,
                )

                if parsed:
                    self._validate_list_items_have_keys(
                        items=parsed,
                        expected_keys={"type", "description"},
                        field_name="laws_actions",
                        registration_number=record.registration_number,
                    )

            # Test policies_actions structure (list of dict with specific keys)
            if record.policies_actions is not None:
                parsed = self._parse_and_validate_json_field(
                    json_string=record.policies_actions,
                    field_name="policies_actions",
                    expected_type=list,
                    registration_number=record.registration_number,
                )

                if parsed:
                    self._validate_list_items_have_keys(
                        items=parsed,
                        expected_keys={"type", "description"},
                        field_name="policies_actions",
                        registration_number=record.registration_number,
                    )

            # Test followup_events_with_dates structure (list of dict with dates and action)
            if record.followup_events_with_dates is not None:
                parsed = self._parse_and_validate_json_field(
                    json_string=record.followup_events_with_dates,
                    field_name="followup_events_with_dates",
                    expected_type=list,
                    registration_number=record.registration_number,
                )

                if parsed:
                    self._validate_list_items_have_keys(
                        items=parsed,
                        expected_keys={"dates", "action"},
                        field_name="followup_events_with_dates",
                        registration_number=record.registration_number,
                    )

                    # Additional validation: 'dates' must be a list
                    for i, event in enumerate(parsed):
                        assert isinstance(event["dates"], list), (
                            f"followup_events_with_dates[{i}]['dates'] must be list "
                            f"for {record.registration_number}"
                        )

    def _parse_and_validate_json_field(
        self,
        json_string: Optional[str],
        field_name: str,
        expected_type: type,
        registration_number: str,
    ) -> Optional[Any]:
        """
        Parse JSON string and validate it matches expected type.

        Args:
            json_string: JSON string to parse
            field_name: Name of the field (for error messages)
            expected_type: Expected Python type (list, dict, etc.)
            registration_number: Initiative registration number

        Returns:
            Parsed JSON object or None if empty/null

        Raises:
            AssertionError: If parsed type doesn't match expected type
        """
        # Parse JSON string to Python object
        parsed = self._validate_json_parseable(
            json_string=json_string,
            field_name=field_name,
            registration_number=registration_number,
        )

        # Return None if empty (None, [], {})
        if not parsed:
            return None

        # Validate type matches expectation
        assert isinstance(parsed, expected_type), (
            f"{field_name} must be {expected_type.__name__} for {registration_number}, "
            f"got {type(parsed).__name__}"
        )

        return parsed

    def _validate_list_items_have_keys(
        self,
        items: List[dict],
        expected_keys: set,
        field_name: str,
        registration_number: str,
    ) -> None:
        """
        Validate that all items in a list are dicts with expected keys.

        Args:
            items: List of items to validate
            expected_keys: Set of required keys each item must have
            field_name: Name of the field (for error messages)
            registration_number: Initiative registration number

        Raises:
            AssertionError: If any item is not a dict or missing required keys
        """
        for i, item in enumerate(items):
            # Validate each item is a dict
            assert isinstance(
                item, dict
            ), f"{field_name}[{i}] must be dict for {registration_number}"

            # Validate required keys are present
            missing_keys = expected_keys - set(item.keys())
            assert not missing_keys, (
                f"{field_name}[{i}] missing keys {missing_keys} "
                f"for {registration_number}"
            )
