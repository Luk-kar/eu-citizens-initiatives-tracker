"""
Test suite for ECI model data quality: Registration number format and uniqueness.

These tests validate registration number format and uniqueness in extracted
European Citizens' Initiative response data.
"""

from collections import Counter
import re
from typing import List

from ECI_initiatives.extractor.responses.model import ECICommissionResponseRecord


class TestRegistrationNumberFormat:
    """Test data quality of registration_number field"""

    # ECI registration number pattern: YYYY/NNNNNN
    # Year: 4 digits (typically 2012-present)
    # Sequential number: 6 digits zero-padded (e.g., 000001, 000003, 000005)
    REGISTRATION_NUMBER_PATTERN = re.compile(r"^(\d{4})/(\d{6})$")

    def test_registration_numbers_follow_pattern(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """Verify registration_number follows YYYY/NNNNNN pattern"""
        for record in complete_dataset:
            assert record.registration_number is not None, (
                f"registration_number is None for record with title: "
                f"{record.initiative_title}"
            )

            match = self.REGISTRATION_NUMBER_PATTERN.match(record.registration_number)

            assert match is not None, (
                f"Invalid registration_number format: {record.registration_number}\n"
                f"Expected format: YYYY/NNNNNN (e.g., 2012/000003)\n"
                f"Where YYYY is 4-digit year and NNNNNN is 6-digit zero-padded number"
            )

            # Extract components for additional validation
            year_str, sequential_str = match.groups()
            year = int(year_str)
            sequential = int(sequential_str)

            # Validate year is reasonable (ECI system started in 2012)
            assert 2012 <= year <= 2030, (
                f"Registration year {year} is outside expected range (2012-2030) "
                f"for {record.registration_number}"
            )

            # Validate sequential number is positive
            assert (
                sequential > 0
            ), f"Sequential number must be positive in {record.registration_number}"

    def test_registration_numbers_are_unique(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """Verify all registration numbers are unique across records"""
        registration_numbers: List[str] = [
            record.registration_number for record in complete_dataset
        ]

        # Count occurrences of each registration number
        counts = Counter(registration_numbers)
        duplicates = {reg_num: count for reg_num, count in counts.items() if count > 1}

        assert not duplicates, "Found duplicate registration numbers:\n" + "\n".join(
            f"  - {reg_num}: appears {count} times"
            for reg_num, count in duplicates.items()
        )

        # Alternative validation: ensure set size equals list size
        unique_count = len(set(registration_numbers))
        total_count = len(registration_numbers)

        assert unique_count == total_count, (
            f"Registration numbers are not unique: "
            f"{total_count} records but only {unique_count} unique registration numbers"
        )

    def test_registration_year_matches_submission_year(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """Verify registration number year component matches submission date year"""
        for record in complete_dataset:
            # Skip if submission date is missing
            if record.commission_submission_date is None:
                continue

            # Extract year from registration number
            match = self.REGISTRATION_NUMBER_PATTERN.match(record.registration_number)
            assert (
                match is not None
            ), f"Invalid registration format: {record.registration_number}"

            registration_year = int(match.group(1))

            # Extract year from submission date (ISO format: YYYY-MM-DD)
            submission_year = int(record.commission_submission_date[:4])

            # Note: Registration year may not always match submission year
            # Source: https://citizens-initiative.europa.eu/how-it-works_en
            #
            # An initiative can be registered in one year but submitted YEARS later.
            # We allow a tolerance of ±6 years based on observed real-world cases.
            #
            # According to ECI regulations, the normal process timeline is:
            # - Signature collection period: up to 12 months
            # - Submission for verification: within 3 months after collection
            # - Verification by national authorities: up to 3 months
            # Total expected timeline: ~18 months from registration to submission
            #
            # However, in practice, initiatives can take much longer due to:
            # - Organizers pausing/restarting signature collection campaigns
            # - COVID-19 pandemic delays (2020-2021)
            # - Technical or logistical challenges in collecting signatures
            # - Strategic timing decisions by organizers
            #
            # Real-world example: Initiative 2019/000007 "Cohesion policy for equality of regions"
            # - Registered: 2019
            # - Submitted: 4 March 2025 (6 years later)
            # - Source: https://citizens-initiative.europa.eu/initiatives/details/2019/000007_en
            # - This is legitimate, not a data quality issue

            year_difference = abs(registration_year - submission_year)

            assert year_difference <= 6, (
                f"Registration year mismatch for {record.registration_number}:\n"
                f"  Registration year: {registration_year}\n"
                f"  Submission year:   {submission_year}\n"
                f"  Difference:        {year_difference} years\n"
                f"  (Initiative: {record.initiative_title})\n\n"
                f"Note: Small differences are normal (registration vs submission),\n"
                f"but {year_difference} years suggests a data quality issue."
            )
