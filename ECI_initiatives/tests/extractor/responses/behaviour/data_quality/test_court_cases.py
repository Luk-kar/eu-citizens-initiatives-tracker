"""
Test suite for ECI model data quality: Court cases JSON structure validation.

These tests validate court cases json structure validation in extracted
European Citizens' Initiative response data.
"""

import json
import re
from typing import Any, List, Optional

from ECI_initiatives.extractor.responses.model import ECICommissionResponseRecord
from .validation_helpers import (
    parse_json_safely,
)


class TestCourtCasesStructure:
    """Test structure of court_cases_referenced field"""

    # Common EU court identifiers
    VALID_COURT_NAMES = {
        "general_court",  # General Court (T- cases)
        "court_of_justice",  # Court of Justice (C- cases)
        "civil_service_tribunal",  # Former Civil Service Tribunal (F- cases, abolished 2016)
        "european_court_of_human_rights",  # ECHR (external to EU but sometimes referenced)
    }

    # EU case number patterns
    # General Court: T-123/21
    # Court of Justice: C-123/21
    # Civil Service Tribunal: F-123/21
    CASE_NUMBER_PATTERN = re.compile(r"^[A-Z]-\d+/\d{2}$")

    def test_court_cases_json_structure_is_consistent(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """
        Verify court_cases_referenced JSON follows consistent structure.

        Expected structure:
        {
            "court_name": ["case_id_1", "case_id_2", ...],
            "another_court": ["case_id_3"]
        }

        Where:
        - Keys are court names (string)
        - Values are lists of case identifiers (list of strings)
        - Case identifiers follow EU court numbering format (e.g., T-158/21, C-123/22)

        This structure allows tracking which court cases are referenced in the
        Commission's response to each initiative.
        """
        structural_issues = []
        format_issues = []

        for record in complete_dataset:
            # Skip if no court cases referenced
            if not record.court_cases_referenced:
                continue

            # Parse JSON
            court_cases = parse_json_safely(record.court_cases_referenced)

            if court_cases is None:
                continue

            # Validate top-level structure is a dictionary
            if not isinstance(court_cases, dict):

                structural_issues.append(
                    (
                        record.registration_number,
                        f"Expected dict, got {type(court_cases).__name__}",
                        str(court_cases)[:100],
                    )
                )
                continue

            # Validate each court entry
            for court_name, case_list in court_cases.items():

                # Court name should be a string
                if not isinstance(court_name, str):
                    structural_issues.append(
                        (
                            record.registration_number,
                            f"Court name must be string, got {type(court_name).__name__}",
                            str(court_name),
                        )
                    )
                    continue

                # Case list should be a list
                if not isinstance(case_list, list):

                    structural_issues.append(
                        (
                            record.registration_number,
                            f"Court '{court_name}' cases must be list, got {type(case_list).__name__}",
                            str(case_list)[:100],
                        )
                    )
                    continue

                # Validate each case identifier
                for case_id in case_list:

                    # Case ID should be a string
                    if not isinstance(case_id, str):
                        structural_issues.append(
                            (
                                record.registration_number,
                                f"Case ID in '{court_name}' must be string, got {type(case_id).__name__}",
                                str(case_id),
                            )
                        )
                        continue

                    # Validate case ID format (e.g., T-158/21, C-123/22)
                    if not self.CASE_NUMBER_PATTERN.match(case_id):
                        format_issues.append(
                            (
                                record.registration_number,
                                court_name,
                                case_id,
                            )
                        )

        # Assert no structural issues
        assert not structural_issues, (
            f"Found {len(structural_issues)} court_cases_referenced with structural issues:\n"
            + "\n".join(
                f"  - {reg_num}: {issue}\n    Value: {value}"
                for reg_num, issue, value in structural_issues
            )
            + '\n\nExpected structure: {"court_name": ["case_id_1", "case_id_2"]}'
        )

        # Assert no format issues
        assert not format_issues, (
            f"Found {len(format_issues)} court case IDs with invalid format:\n"
            + "\n".join(
                f"  - {reg_num} [{court}]: '{case_id}' (expected format: X-NNN/YY, e.g., T-158/21)"
                for reg_num, court, case_id in format_issues
            )
            + "\n\nEU court case numbers follow pattern: [Court Letter]-[Case Number]/[Year]"
            + "\n  - T-###/## = General Court"
            + "\n  - C-###/## = Court of Justice"
            + "\n  - F-###/## = Civil Service Tribunal (abolished 2016)"
        )

    def test_court_case_identifiers_are_unique_per_record(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """
        Verify that case identifiers are not duplicated within a single record.

        Each case should appear only once in the court_cases_referenced structure,
        even if referenced multiple times in the text. Duplicates suggest
        data extraction issues.
        """
        duplicate_issues = []

        for record in complete_dataset:

            if not record.court_cases_referenced:
                continue

            court_cases = parse_json_safely(record.court_cases_referenced)

            if not court_cases or not isinstance(court_cases, dict):
                continue

            # Collect all case IDs across all courts
            all_case_ids = []

            for court_name, case_list in court_cases.items():
                if isinstance(case_list, list):
                    all_case_ids.extend(case_list)

            # Check for duplicates
            seen = set()
            duplicates = []

            for case_id in all_case_ids:

                if case_id in seen:
                    duplicates.append(case_id)
                seen.add(case_id)

            if duplicates:
                duplicate_issues.append(
                    (
                        record.registration_number,
                        duplicates,
                    )
                )

        assert not duplicate_issues, (
            f"Found {len(duplicate_issues)} records with duplicate court case IDs:\n"
            + "\n".join(
                f"  - {reg_num}: duplicates = {dupes}"
                for reg_num, dupes in duplicate_issues
            )
            + "\n\nEach case ID should appear only once per initiative."
        )

    def test_recognized_court_names_are_used(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """
        Verify that court names use consistent, recognized terminology.

        Court names should follow standardized naming conventions to enable
        consistent querying and analysis. This test checks that court names
        match known EU court identifiers.
        """
        unrecognized_courts = []

        for record in complete_dataset:
            if not record.court_cases_referenced:
                continue

            court_cases = parse_json_safely(record.court_cases_referenced)
            if not court_cases or not isinstance(court_cases, dict):
                continue

            for court_name in court_cases.keys():
                if court_name not in self.VALID_COURT_NAMES:
                    unrecognized_courts.append(
                        (
                            record.registration_number,
                            court_name,
                        )
                    )

        assert not unrecognized_courts, (
            f"Found {len(unrecognized_courts)} unrecognized court names:\n"
            + "\n".join(
                f"  - {reg_num}: '{court_name}'"
                for reg_num, court_name in unrecognized_courts
            )
            + f"\n\nRecognized court names: {', '.join(sorted(self.VALID_COURT_NAMES))}"
            + "\n\nIf this is a new/valid court, add it to VALID_COURT_NAMES in the test."
        )
