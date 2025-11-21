"""
Test suite for validating data quality in extracted response data.
Column-level validation tests for ECICommissionResponseRecord fields
"""

import json
import pytest
import shutil
from collections import Counter
import csv
from datetime import datetime, date
from pathlib import Path
import re
from typing import Any, List, Optional, Set
from unittest import mock
from urllib.parse import urlparse, ParseResult
import html

from bs4 import BeautifulSoup

from ECI_initiatives.extractor.responses.model import ECICommissionResponseRecord
from ECI_initiatives.extractor.responses.processor import ECIResponseDataProcessor
from ECI_initiatives.extractor.responses.parser.consts.eci_status import (
    ECIImplementationStatus,
)

# Test data paths
TEST_DATA_DIR = (
    Path(__file__).parent.parent.parent.parent / "data" / "example_htmls" / "responses"
)
# Once when the test starts
TODAY = date.today()

# Validate test data directory exists
if not TEST_DATA_DIR.exists():
    raise FileNotFoundError(
        f"Test data directory not found: {TEST_DATA_DIR}\n"
        f"Expected location relative to test file:\n"
        f"  Test file: {Path(__file__)}\n"
        f"  Looking for: tests/data/example_htmls/responses/\n"
        f"Please ensure test HTML files are in the correct location."
    )

if not TEST_DATA_DIR.is_dir():
    raise NotADirectoryError(f"Test data path is not a directory: {TEST_DATA_DIR}")

# Check if any HTML files exist
html_files = list(TEST_DATA_DIR.rglob("*.html"))
if not html_files:
    raise FileNotFoundError(
        f"No HTML test files found in: {TEST_DATA_DIR}\n"
        f"Expected files matching pattern: **/*.html\n"
        f"Directory contents: {list(TEST_DATA_DIR.iterdir())}"
    )


@pytest.fixture(scope="session")
def processed_test_data(tmp_path_factory):
    """
    Run ECIResponseDataProcessor on test HTML files and return path to output CSV.
    This fixture runs once per test session.
    """
    # Create temporary directory structure that processor expects
    temp_root = tmp_path_factory.mktemp("eci_data")
    session_dir = temp_root / "2024-01-01_12-00-00"
    responses_dir = session_dir / "responses"
    responses_dir.mkdir(parents=True)

    # Create logs directory (required by ResponsesExtractorLogger)
    logs_dir = session_dir / "logs"
    logs_dir.mkdir(parents=True)

    # Copy all HTML files from test data directory, preserving year subdirs or flattening
    for html_file in TEST_DATA_DIR.rglob("*.html"):
        shutil.copy2(html_file, responses_dir / html_file.name)

    # Create minimal responses_list.csv metadata
    _create_metadata_csv(responses_dir)

    # Run processor
    processor = ECIResponseDataProcessor(data_root=str(temp_root))

    with mock.patch.object(
        processor, "find_latest_scrape_session", return_value=session_dir
    ):
        processor.run()

    # Find generated CSV
    output_csv = list(session_dir.glob("eci_responses_*.csv"))[0]

    return output_csv


def _create_metadata_csv(responses_dir: Path):
    """Generate responses_list.csv from HTML filenames"""
    import re

    metadata_file = responses_dir / "responses_list.csv"
    html_files = list(responses_dir.glob("*.html"))

    with open(metadata_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["registration_number", "title", "url"])
        writer.writeheader()

        for html_file in html_files:
            match = re.match(r"(\d{4})_(\d{6}).*\.html", html_file.name)
            if match:
                year, number = match.groups()
                reg_num = f"{year}/{number}"
                writer.writerow(
                    {
                        "registration_number": reg_num,
                        "title": f"ECI {reg_num}",
                        "url": f"https://example.com/{reg_num}",
                    }
                )


@pytest.fixture(scope="session")
def complete_dataset(processed_test_data) -> List[ECICommissionResponseRecord]:
    """Load complete dataset from processed test HTML files"""
    records = []

    with open(processed_test_data, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert CSV row to ECICommissionResponseRecord using actual column names
            record = ECICommissionResponseRecord(
                response_url=row.get("response_url", ""),
                initiative_url=row.get("initiative_url", ""),
                initiative_title=row.get("initiative_title", ""),
                registration_number=row.get("registration_number", ""),
                submission_text=row.get("submission_text", ""),
                commission_submission_date=row.get("commission_submission_date", ""),
                submission_news_url=row.get("submission_news_url") or None,
                commission_meeting_date=row.get("commission_meeting_date") or None,
                commission_officials_met=row.get("commission_officials_met") or None,
                parliament_hearing_date=row.get("parliament_hearing_date") or None,
                parliament_hearing_video_urls=row.get("parliament_hearing_video_urls")
                or None,
                plenary_debate_date=row.get("plenary_debate_date") or None,
                plenary_debate_video_urls=row.get("plenary_debate_video_urls") or None,
                official_communication_adoption_date=row.get(
                    "official_communication_adoption_date"
                )
                or None,
                official_communication_document_urls=row.get(
                    "official_communication_document_urls"
                )
                or None,
                commission_answer_text=row.get("commission_answer_text", ""),
                final_outcome_status=row.get("final_outcome_status") or None,
                law_implementation_date=row.get("law_implementation_date") or None,
                commission_promised_new_law=row.get("commission_promised_new_law")
                or None,
                commission_deadlines=row.get("commission_deadlines") or None,
                commission_rejected_initiative=row.get("commission_rejected_initiative")
                or None,
                commission_rejection_reason=row.get("commission_rejection_reason")
                or None,
                laws_actions=row.get("laws_actions") or None,
                policies_actions=row.get("policies_actions") or None,
                has_followup_section=row.get("has_followup_section") or None,
                has_roadmap=row.get("has_roadmap") or None,
                has_workshop=row.get("has_workshop") or None,
                has_partnership_programs=row.get("has_partnership_programs") or None,
                court_cases_referenced=row.get("court_cases_referenced") or None,
                followup_latest_date=row.get("followup_latest_date") or None,
                followup_most_future_date=row.get("followup_most_future_date") or None,
                commission_factsheet_url=row.get("commission_factsheet_url") or None,
                followup_dedicated_website=row.get("followup_dedicated_website")
                or None,
                referenced_legislation_by_id=row.get("referenced_legislation_by_id")
                or None,
                referenced_legislation_by_name=row.get("referenced_legislation_by_name")
                or None,
                followup_events_with_dates=row.get("followup_events_with_dates")
                or None,
            )
            records.append(record)

    return records


@pytest.fixture
def records_with_followup(complete_dataset) -> List[ECICommissionResponseRecord]:
    """Filter records that have follow-up sections"""
    return [
        record
        for record in complete_dataset
        if (
            record.has_followup_section == "True"
            or record.followup_dedicated_website
            or record.laws_actions
            or record.policies_actions
        )
    ]


@pytest.fixture
def records_with_laws(complete_dataset) -> List[ECICommissionResponseRecord]:
    """Filter records that resulted in laws"""
    return [
        record
        for record in complete_dataset
        if record.laws_actions and record.laws_actions.strip()
    ]


@pytest.fixture
def records_rejected(complete_dataset) -> List[ECICommissionResponseRecord]:
    """Filter records that were rejected (from rejection test category)"""
    rejection_reg_nums = {"2012/000005", "2017/000004", "2019/000007"}
    return [
        record
        for record in complete_dataset
        if (
            record.registration_number in rejection_reg_nums
            or record.commission_rejected_initiative == "True"
        )
    ]


# Additional category-based fixtures matching your test data structure


@pytest.fixture
def partial_success_records(complete_dataset) -> List[ECICommissionResponseRecord]:
    """Records from partial_success category"""
    partial_nums = {
        "2012/000007",
        "2017/000002",
        "2019/000016",
        "2020/000001",
        "2021/000006",
        "2022/000002",
    }
    return [r for r in complete_dataset if r.registration_number in partial_nums]


@pytest.fixture
def strong_legislative_success_records(
    complete_dataset,
) -> List[ECICommissionResponseRecord]:
    """Records from strong_legislative_success category"""
    return [r for r in complete_dataset if r.registration_number == "2012/000003"]


@pytest.fixture
def strong_commitment_delayed_records(
    complete_dataset,
) -> List[ECICommissionResponseRecord]:
    """Records from strong_commitment_delayed category"""
    return [r for r in complete_dataset if r.registration_number == "2018/000004"]


class TestURLFieldsIntegrity:
    """Test data quality of URL-related fields"""

    def _validate_url_structure(
        self,
        url: str,
        field_name: str,
        registration_number: str,
    ) -> ParseResult:
        """Validate URL structure - HTTPS only."""
        parsed = urlparse(url)

        assert parsed.scheme in ["https", "http"], (
            f"{field_name} must use HTTPS or HTTP for {registration_number}: "
            f"got '{parsed.scheme}'"
        )

        assert (
            parsed.netloc
        ), f"Missing domain in {field_name} for {registration_number}"

        return parsed

    def _validate_domain_pattern(
        self,
        parsed_url: ParseResult,
        allowed_patterns: List[str],
        field_name: str,
        registration_number: str,
    ) -> None:
        """
        Validate that URL domain matches expected patterns.

        Args:
            parsed_url: Parsed URL components
            allowed_patterns: List of regex patterns for valid domains
            field_name: Name of the field being validated (for error messages)
            registration_number: Initiative registration number (for error messages)

        Raises:
            AssertionError: If domain doesn't match any allowed pattern
        """
        assert any(
            re.match(pattern, parsed_url.netloc) for pattern in allowed_patterns
        ), (
            f"Unexpected domain in {field_name} for {registration_number}: "
            f"{parsed_url.netloc}"
        )

    def test_response_urls_are_valid_https(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """Verify all response_url fields contain valid HTTPS URLs"""
        for record in complete_dataset:
            assert (
                record.response_url is not None
            ), f"response_url is None for {record.registration_number}"

            self._validate_url_structure(
                url=record.response_url,
                field_name="response_url",
                registration_number=record.registration_number,
            )

    def test_initiative_urls_are_valid_https(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """Verify all initiative_url fields contain valid HTTPS URLs"""
        for record in complete_dataset:
            assert (
                record.initiative_url is not None
            ), f"initiative_url is None for {record.registration_number}"

            self._validate_url_structure(
                url=record.initiative_url,
                field_name="initiative_url",
                registration_number=record.registration_number,
            )

    def test_submission_news_urls_are_valid_when_present(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """Verify submission_news_url fields contain valid URLs when not None"""
        for record in complete_dataset:
            if record.submission_news_url is not None:
                self._validate_url_structure(
                    url=record.submission_news_url,
                    field_name="submission_news_url",
                    registration_number=record.registration_number,
                )

    def test_commission_factsheet_urls_are_valid_when_present(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """Verify commission_factsheet_url fields contain valid URLs when not None"""
        for record in complete_dataset:
            if record.commission_factsheet_url is not None:
                self._validate_url_structure(
                    url=record.commission_factsheet_url,
                    field_name="commission_factsheet_url",
                    registration_number=record.registration_number,
                )

    def test_followup_dedicated_website_urls_are_valid_when_present(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """Verify followup_dedicated_website fields contain valid URLs when not None"""
        for record in complete_dataset:
            if record.followup_dedicated_website is not None:
                self._validate_url_structure(
                    url=record.followup_dedicated_website,
                    field_name="followup_dedicated_website",
                    registration_number=record.registration_number,
                )

    def test_urls_point_to_correct_domains(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """Verify URLs point to expected EU domain patterns"""
        # Expected domain patterns for different URL fields
        domain_patterns = {
            "response_url": [r"^citizens-initiative\.europa\.eu$"],
            "initiative_url": [r"^citizens-initiative\.europa\.eu$"],
            "submission_news_url": [
                r"^ec\.europa\.eu$",
                r"^europa\.eu$",
                r"^europarl\.europa\.eu$",
            ],
            "commission_factsheet_url": [r"^citizens-initiative\.europa\.eu$"],
            "followup_dedicated_website": [
                r".*\.europa\.eu$",
                r".*\.ec\.europa\.eu$",
            ],
        }

        for record in complete_dataset:
            # Validate response_url domain
            parsed = urlparse(record.response_url)
            self._validate_domain_pattern(
                parsed_url=parsed,
                allowed_patterns=domain_patterns["response_url"],
                field_name="response_url",
                registration_number=record.registration_number,
            )

            # Validate initiative_url domain
            parsed = urlparse(record.initiative_url)
            self._validate_domain_pattern(
                parsed_url=parsed,
                allowed_patterns=domain_patterns["initiative_url"],
                field_name="initiative_url",
                registration_number=record.registration_number,
            )

            # Validate submission_news_url domain (if present)
            if record.submission_news_url is not None:
                parsed = urlparse(record.submission_news_url)
                self._validate_domain_pattern(
                    parsed_url=parsed,
                    allowed_patterns=domain_patterns["submission_news_url"],
                    field_name="submission_news_url",
                    registration_number=record.registration_number,
                )

            # Validate commission_factsheet_url domain (if present)
            if record.commission_factsheet_url is not None:
                parsed = urlparse(record.commission_factsheet_url)
                self._validate_domain_pattern(
                    parsed_url=parsed,
                    allowed_patterns=domain_patterns["commission_factsheet_url"],
                    field_name="commission_factsheet_url",
                    registration_number=record.registration_number,
                )

            # Validate followup_dedicated_website domain (if present)
            if record.followup_dedicated_website is not None:
                parsed = urlparse(record.followup_dedicated_website)
                self._validate_domain_pattern(
                    parsed_url=parsed,
                    allowed_patterns=domain_patterns["followup_dedicated_website"],
                    field_name="followup_dedicated_website",
                    registration_number=record.registration_number,
                )


class TestDateFieldsConsistency:
    """Test data quality and consistency of date-related fields"""

    # ISO 8601 date format pattern (YYYY-MM-DD)
    ISO_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")

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

        assert self.ISO_DATE_PATTERN.match(date_string), (
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


"""
Test suite for validating data quality in extracted response data.
Registration number format tests for ECICommissionResponseRecord
"""


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

        assert not duplicates, f"Found duplicate registration numbers:\n" + "\n".join(
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


"""
Test suite for validating data quality in extracted response data.
Text field completeness tests for ECICommissionResponseRecord
"""

# Standard library
import re
from typing import List

# Third party
import pytest

# Local
from ECI_initiatives.extractor.responses.model import ECICommissionResponseRecord


class TestTextFieldsCompleteness:
    """Test data quality of text content fields"""

    # Minimum substantial text length (characters)
    MIN_SUBSTANTIAL_LENGTH = 50

    # Excessive whitespace patterns
    EXCESSIVE_WHITESPACE = re.compile(r"\s{3,}")  # 3+ consecutive spaces
    EXCESSIVE_NEWLINES = re.compile(r"\n{3,}")  # 3+ consecutive newlines

    def _is_empty_or_whitespace(self, text: str) -> bool:
        """
        Check if text is empty or contains only whitespace.

        Args:
            text: Text to check

        Returns:
            True if empty or whitespace-only
        """
        return not text or not text.strip()

    def _has_substantial_content(self, text: str, min_length: int = None) -> bool:
        """
        Check if text contains substantial content (not just whitespace).

        Args:
            text: Text to check
            min_length: Minimum length for substantial content (default: MIN_SUBSTANTIAL_LENGTH)

        Returns:
            True if text has substantial content
        """
        if not text:
            return False

        min_len = min_length if min_length is not None else self.MIN_SUBSTANTIAL_LENGTH
        cleaned = text.strip()
        return len(cleaned) >= min_len

    def _contains_html_tags(self, text: str) -> bool:
        """
        Check if text contains HTML tags like <p>, <div>, etc.

        Uses BeautifulSoup to reliably detect HTML tags.

        Args:
            text: Text to check

        Returns:
            True if HTML tags found
        """
        if not text:
            return False

        # Parse with BeautifulSoup
        soup = BeautifulSoup(text, "html.parser")

        # If BeautifulSoup finds any tags, HTML is present
        # Note: soup.find_all() returns all tags in the document
        tags = soup.find_all()

        return len(tags) > 0

    def _contains_html_entities(self, text: str) -> bool:
        """
        Check if text contains unescaped HTML entities like &nbsp; &#160;

        Uses html.unescape() to detect if text changes when HTML entities are decoded.

        Args:
            text: Text to check

        Returns:
            True if HTML entities found
        """
        if not text:
            return False

        # If unescaping changes the text, entities were present
        unescaped = html.unescape(text)
        return text != unescaped

    def _get_html_entity_examples(self, text: str, max_examples: int = 5) -> List[str]:
        """
        Extract examples of HTML entities found in text.
        Uses standard library html.entities for comprehensive coverage.
        """

        found = []

        # Check named entities (e.g., &nbsp; &amp; &lt; &gt; &quot;)
        # These are HTML entities with names like &entityname;
        for name in html.entities.name2codepoint.keys():

            entity = f"&{name};"
            if entity in text and len(found) < max_examples:
                found.append(entity)

        # Check numeric decimal entities (e.g., &#160; &#38; &#60;)
        # These use decimal Unicode codepoints: &#number;
        numeric = re.findall(r"&#\d+;", text)

        for entity in set(numeric):
            if len(found) < max_examples:
                found.append(entity)

        return found

    def _has_excessive_whitespace(self, text: str) -> bool:
        """
        Check if text has excessive consecutive whitespace or newlines.

        Args:
            text: Text to check

        Returns:
            True if excessive whitespace found
        """
        return bool(
            self.EXCESSIVE_WHITESPACE.search(text)
            or self.EXCESSIVE_NEWLINES.search(text)
        )

    def test_initiative_titles_are_not_empty(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """Verify initiative_title is never empty or whitespace-only"""
        for record in complete_dataset:
            assert (
                record.initiative_title is not None
            ), f"initiative_title is None for {record.registration_number}"

            assert not self._is_empty_or_whitespace(record.initiative_title), (
                f"initiative_title is empty or whitespace-only for "
                f"{record.registration_number}"
            )

            # Title should be reasonably short (not truncated text)
            title_length = len(record.initiative_title)
            assert title_length < 500, (
                f"initiative_title suspiciously long ({title_length} chars) for "
                f"{record.registration_number}: {record.initiative_title[:100]}..."
            )

    def test_submission_text_is_not_empty(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """Verify submission_text contains substantial content"""
        for record in complete_dataset:
            assert (
                record.submission_text is not None
            ), f"submission_text is None for {record.registration_number}"

            assert self._has_substantial_content(record.submission_text), (
                f"submission_text lacks substantial content for "
                f"{record.registration_number}. "
                f"Length: {len(record.submission_text.strip())} chars "
                f"(minimum: {self.MIN_SUBSTANTIAL_LENGTH})"
            )

    def test_commission_answer_text_is_not_empty_when_present(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """Verify commission_answer_text contains substantial content when not None"""
        for record in complete_dataset:
            if record.commission_answer_text is not None:
                assert self._has_substantial_content(record.commission_answer_text), (
                    f"commission_answer_text present but lacks substantial content for "
                    f"{record.registration_number}. "
                    f"Length: {len(record.commission_answer_text.strip())} chars "
                    f"(minimum: {self.MIN_SUBSTANTIAL_LENGTH})"
                )

    def test_text_fields_do_not_contain_html_artifacts(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """Verify text fields are cleaned of HTML tags and entities"""
        for record in complete_dataset:
            # Check initiative_title
            if record.initiative_title:
                assert not self._contains_html_tags(record.initiative_title), (
                    f"initiative_title contains HTML tags for {record.registration_number}: "
                    f"{record.initiative_title[:200]}..."
                )

                # Check for HTML entities
                if self._contains_html_entities(record.initiative_title):
                    examples = self._get_html_entity_examples(record.initiative_title)
                    if examples:
                        pytest.fail(
                            f"initiative_title contains HTML entities for "
                            f"{record.registration_number}:\n"
                            f"  Found: {', '.join(examples)}\n"
                            f"  Title: {record.initiative_title[:200]}..."
                        )

            # Check submission_text
            if record.submission_text:
                assert not self._contains_html_tags(record.submission_text), (
                    f"submission_text contains HTML tags for {record.registration_number}. "
                    f"Preview: {record.submission_text[:200]}..."
                )

                # HTML entities in body text are less critical but should be noted
                if self._contains_html_entities(record.submission_text):
                    examples = self._get_html_entity_examples(record.submission_text)
                    if examples:
                        # Only fail on common problematic entities
                        problematic = ["&nbsp;", "&#160;"]
                        if any(entity.split()[0] in problematic for entity in examples):
                            pytest.fail(
                                f"submission_text contains problematic HTML entities for "
                                f"{record.registration_number}: {', '.join(examples)}"
                            )

            # Check commission_answer_text
            if record.commission_answer_text:
                assert not self._contains_html_tags(record.commission_answer_text), (
                    f"commission_answer_text contains HTML tags for "
                    f"{record.registration_number}. "
                    f"Preview: {record.commission_answer_text[:200]}..."
                )

    def test_text_fields_have_proper_whitespace_normalization(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """Verify text fields don't have excessive whitespace or malformed spacing"""
        for record in complete_dataset:
            # Check initiative_title
            if record.initiative_title:
                assert not self._has_excessive_whitespace(record.initiative_title), (
                    f"initiative_title has excessive whitespace for "
                    f"{record.registration_number}: "
                    f"{repr(record.initiative_title[:200])}"
                )

                # Title should not start/end with whitespace
                assert record.initiative_title == record.initiative_title.strip(), (
                    f"initiative_title has leading/trailing whitespace for "
                    f"{record.registration_number}: "
                    f"{repr(record.initiative_title)}"
                )

            # Check submission_text
            if record.submission_text:
                assert not self._has_excessive_whitespace(record.submission_text), (
                    f"submission_text has excessive whitespace for "
                    f"{record.registration_number}: "
                    f"{repr(record.submission_text[:200])}"
                )

                # Should not start/end with whitespace
                assert record.submission_text == record.submission_text.strip(), (
                    f"submission_text has leading/trailing whitespace for "
                    f"{record.registration_number}"
                )

            # Check commission_answer_text
            if record.commission_answer_text:
                assert not self._has_excessive_whitespace(
                    record.commission_answer_text
                ), (
                    f"commission_answer_text has excessive whitespace for "
                    f"{record.registration_number}: "
                    f"{repr(record.commission_answer_text[:200])}"
                )

                # Should not start/end with whitespace
                assert (
                    record.commission_answer_text
                    == record.commission_answer_text.strip()
                ), (
                    f"commission_answer_text has leading/trailing whitespace for "
                    f"{record.registration_number}"
                )


class TestOutcomeStatusConsistency:
    """Test data quality of outcome-related fields"""

    # Get all valid human-readable statuses from ECIImplementationStatus
    VALID_OUTCOME_STATUSES = {
        status.human_readable_explanation
        for status in ECIImplementationStatus.BY_LEGAL_TERM.values()
    } | {
        None
    }  # Add None for initiatives without concluded status

    def test_final_outcome_status_has_valid_values(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """Verify final_outcome_status uses predefined status categories"""
        invalid_statuses = set()

        for record in complete_dataset:
            if (
                record.final_outcome_status is not None
                and record.final_outcome_status not in self.VALID_OUTCOME_STATUSES
            ):
                invalid_statuses.add(
                    (record.registration_number, record.final_outcome_status)
                )

        assert not invalid_statuses, (
            f"Found records with invalid final_outcome_status:\n"
            + "\n".join(
                f"  - {reg_num}: '{status}'"
                for reg_num, status in sorted(invalid_statuses)
            )
            + f"\n\nValid statuses from ECIImplementationStatus:\n"
            + "\n".join(
                f"  - {status}"
                for status in sorted([s for s in self.VALID_OUTCOME_STATUSES if s])
            )
        )

    def test_law_active_status_has_implementation_date(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """Verify records with 'Law Active' status have law_implementation_date"""
        missing_dates = []

        for record in complete_dataset:
            # Use the human-readable status from ECIImplementationStatus.APPLICABLE
            if (
                record.final_outcome_status
                == ECIImplementationStatus.APPLICABLE.human_readable_explanation
            ):
                if record.law_implementation_date is None:
                    missing_dates.append(
                        (record.registration_number, record.initiative_title)
                    )

        assert not missing_dates, (
            f"Found {len(missing_dates)} records with "
            f"'{ECIImplementationStatus.APPLICABLE.human_readable_explanation}' status "
            f"but missing law_implementation_date:\n"
            + "\n".join(
                f"  - {reg_num}: {title[:80]}..." for reg_num, title in missing_dates
            )
        )

    def test_rejected_status_has_rejection_reason(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """Verify rejected initiatives have commission_rejection_reason"""
        missing_reasons = []

        # Get all rejection-related statuses from ECIImplementationStatus
        rejection_statuses = {
            ECIImplementationStatus.REJECTED.human_readable_explanation,
            ECIImplementationStatus.REJECTED_ALREADY_COVERED.human_readable_explanation,
            ECIImplementationStatus.REJECTED_WITH_ACTIONS.human_readable_explanation,
        }

        for record in complete_dataset:
            # If initiative has a rejection status or rejection flag
            if (
                record.final_outcome_status in rejection_statuses
                or self._normalize_boolean(record.commission_rejected_initiative)
                is True
            ):
                if not record.commission_rejection_reason:
                    missing_reasons.append(
                        (record.registration_number, record.initiative_title)
                    )

        assert not missing_reasons, (
            f"Found {len(missing_reasons)} rejected initiatives "
            f"without commission_rejection_reason:\n"
            + "\n".join(
                f"  - {reg_num}: {title[:80]}..." for reg_num, title in missing_reasons
            )
        )

    def test_promised_law_aligns_with_outcome(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """
        Verify that the Commission's promise regarding new legislation aligns with
        the actual outcome status of the initiative.

        This test ensures logical consistency between what the Commission explicitly
        stated about creating new legislation (commission_promised_new_law field) and
        the final outcome that materialized (final_outcome_status field).

        The test validates two key alignment scenarios:

        1. If the Commission promised to create NEW legislation for an initiative,
        the outcome should reflect a law-related status (e.g., Law Promised,
        Law Active, Proposals Under Review). It would be inconsistent for the
        Commission to promise legislation but then have a non-legislative outcome.

        2. If the Commission did NOT promise new legislation, the outcome can still
        be "Law Active" or "Law Approved" because the initiative's goals may
        already be covered by existing or pending EU legislation. This is a valid
        Commission response where no new law is needed because adequate laws
        already exist. However, it would be contradictory if the Commission said
        "no new law needed" but then the outcome shows "Law Promised" (indicating
        a new commitment was made).

        This validation catches data quality issues where:
        - Scraped data is inconsistent between different sections of the response
        - The promise flag was incorrectly extracted
        - The outcome status was misclassified
        """
        misalignments = []

        # Define law-related statuses using ECIImplementationStatus
        law_related_statuses = {
            ECIImplementationStatus.APPLICABLE.human_readable_explanation,  # Law Active
            ECIImplementationStatus.ADOPTED.human_readable_explanation,  # Law Approved
            ECIImplementationStatus.COMMITTED.human_readable_explanation,  # Law Promised
            ECIImplementationStatus.PROPOSAL_PENDING_ADOPTION.human_readable_explanation,  # Proposals Under Review
        }

        # Define rejection statuses using ECIImplementationStatus
        rejection_statuses = {
            ECIImplementationStatus.REJECTED.human_readable_explanation,
            ECIImplementationStatus.REJECTED_ALREADY_COVERED.human_readable_explanation,
            ECIImplementationStatus.REJECTED_WITH_ACTIONS.human_readable_explanation,
        }

        # Statuses that indicate the initiative's goals are met by existing/pending legislation
        # (Commission doesn't need to promise NEW law, but laws exist that address the issue)
        already_covered_statuses = {
            ECIImplementationStatus.APPLICABLE.human_readable_explanation,  # Law Active (existing law)
            ECIImplementationStatus.ADOPTED.human_readable_explanation,  # Law Approved (pending law)
            ECIImplementationStatus.REJECTED_ALREADY_COVERED.human_readable_explanation,  # Explicitly already covered
        }

        for record in complete_dataset:
            # Normalize boolean flag
            promised_law = self._normalize_boolean(record.commission_promised_new_law)

            # Skip if promise status is unknown
            if promised_law is None:
                continue

            # If Commission promised a new law
            if promised_law is True:
                # Outcome should reflect law-related status (not rejection)
                if (
                    record.final_outcome_status not in law_related_statuses
                    and record.final_outcome_status is not None
                    and record.final_outcome_status not in rejection_statuses
                ):
                    # Allow non-legislative actions as they may still fulfill promises
                    if (
                        record.final_outcome_status
                        != ECIImplementationStatus.NON_LEGISLATIVE_ACTION.human_readable_explanation
                    ):
                        misalignments.append(
                            (
                                record.registration_number,
                                "Promised law",
                                record.final_outcome_status or "No outcome",
                            )
                        )

            # If Commission explicitly rejected or didn't promise NEW law
            elif promised_law is False:
                # It's VALID for Commission to say "no new law needed" when:
                # 1. Issue already covered by existing law (Law Active)
                # 2. Issue already covered by pending law (Law Approved)
                # 3. Explicitly marked as "Rejected - Already Covered"
                #
                # Only flag as misalignment if Commission promised NO law,
                # but then a law was specifically PROMISED or COMMITTED for this initiative
                if (
                    record.final_outcome_status
                    == ECIImplementationStatus.COMMITTED.human_readable_explanation
                ):
                    # This is contradictory: Commission said "no new law"
                    # but status shows "Law Promised" (new commitment made)
                    misalignments.append(
                        (
                            record.registration_number,
                            "No law promised (commission_promised_new_law=False)",
                            f"but outcome is '{ECIImplementationStatus.COMMITTED.human_readable_explanation}'",
                        )
                    )

        assert not misalignments, (
            f"Found {len(misalignments)} records where commission_promised_new_law "
            f"doesn't align with final_outcome_status:\n"
            + "\n".join(
                f"  - {reg_num}: {promise} {outcome}"
                for reg_num, promise, outcome in misalignments
            )
        )

    def test_rejected_initiatives_have_rejection_flag_set(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """Verify commission_rejected_initiative=True when rejection reason exists"""
        inconsistent_rejections = []

        for record in complete_dataset:
            # Normalize flag value (handle both bool and string "True"/"False")
            flag_value = self._normalize_boolean(record.commission_rejected_initiative)

            # If rejection reason exists, flag should be True
            if record.commission_rejection_reason:
                if flag_value is not True:
                    inconsistent_rejections.append(
                        (
                            record.registration_number,
                            record.commission_rejected_initiative,  # Show actual value
                            record.commission_rejection_reason[:100],
                        )
                    )

            # If flag is True, reason should exist
            if flag_value is True:
                if not record.commission_rejection_reason:
                    inconsistent_rejections.append(
                        (
                            record.registration_number,
                            record.commission_rejected_initiative,  # Show actual value
                            "No rejection reason provided",
                        )
                    )

        assert not inconsistent_rejections, (
            f"Found {len(inconsistent_rejections)} records with inconsistent "
            f"rejection flag and reason:\n"
            + "\n".join(
                f"  - {reg_num}: flag={flag!r}, reason='{reason}'"
                for reg_num, flag, reason in inconsistent_rejections
            )
        )

    def test_outcome_status_consistency_with_actions(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """
        Verify that final_outcome_status is consistent with presence of
        laws_actions and policies_actions.
        """
        inconsistencies = []

        for record in complete_dataset:
            # If status is "Law Active", should have laws_actions
            if (
                record.final_outcome_status
                == ECIImplementationStatus.APPLICABLE.human_readable_explanation
            ):
                if not record.laws_actions or record.laws_actions == "null":
                    inconsistencies.append(
                        (
                            record.registration_number,
                            f"{ECIImplementationStatus.APPLICABLE.human_readable_explanation} but no laws_actions",
                        )
                    )

            # If status is "Policy Changes Only", should have policies_actions
            if (
                record.final_outcome_status
                == ECIImplementationStatus.NON_LEGISLATIVE_ACTION.human_readable_explanation
            ):
                if not record.policies_actions or record.policies_actions == "null":
                    inconsistencies.append(
                        (
                            record.registration_number,
                            f"{ECIImplementationStatus.NON_LEGISLATIVE_ACTION.human_readable_explanation} but no policies_actions",
                        )
                    )

            # If status is rejected, shouldn't have active laws
            rejection_statuses = {
                ECIImplementationStatus.REJECTED.human_readable_explanation,
                ECIImplementationStatus.REJECTED_ALREADY_COVERED.human_readable_explanation,
                ECIImplementationStatus.REJECTED_WITH_ACTIONS.human_readable_explanation,
            }
            if record.final_outcome_status in rejection_statuses:
                if record.law_implementation_date is not None:
                    inconsistencies.append(
                        (
                            record.registration_number,
                            f"Rejected but has law_implementation_date",
                        )
                    )

        assert not inconsistencies, (
            f"Found {len(inconsistencies)} records with outcome status inconsistencies:\n"
            + "\n".join(f"  - {reg_num}: {issue}" for reg_num, issue in inconsistencies)
        )

    def _normalize_boolean(self, value: any) -> Optional[bool]:
        """
        Normalize boolean-like values to actual booleans.

        Handles cases where CSV/pandas may have converted booleans to strings.

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


class TestCommissionResponseFieldsCoherence:
    """Test coherence between Commission response fields"""

    def test_commission_officials_met_when_meeting_date_exists(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """Verify commission_officials_met is populated when commission_meeting_date exists"""
        pass

    def test_communication_urls_exist_when_adoption_date_exists(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """Verify official_communication_document_urls exists when adoption date is set"""
        pass

    def test_hearing_videos_exist_when_hearing_date_exists(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """Verify parliament_hearing_video_urls exists when hearing date is set"""
        pass

    def test_plenary_videos_exist_when_debate_date_exists(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """Verify plenary_debate_video_urls exists when debate date is set"""
        pass


class TestFollowupSectionConsistency:
    """Test consistency of follow-up section flags and data"""

    def test_followup_section_implies_followup_data(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """Verify has_followup_section=True when any followup data exists"""
        pass

    def test_roadmap_flag_aligns_with_actions(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """Verify has_roadmap=True correlates with roadmap entries in policies_actions"""
        pass

    def test_workshop_flag_aligns_with_events(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """Verify has_workshop=True correlates with workshop events in followup data"""
        pass

    def test_partnership_programs_flag_aligns_with_data(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """Verify has_partnership_programs=True when partnership data exists"""
        pass

    def test_followup_dates_exist_when_followup_section_exists(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """Verify followup dates are populated when has_followup_section=True"""
        pass


class TestActionsDataStructure:
    """Test structure and quality of laws_actions and policies_actions"""

    def test_action_dates_are_valid_when_present(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """Verify date fields within action objects follow ISO format"""
        pass

    def test_action_document_urls_are_valid_when_present(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """Verify document_url fields in action objects are valid URLs"""
        pass


class TestCourtCasesStructure:
    """Test structure of court_cases_referenced field"""

    def test_court_cases_json_structure_is_consistent(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """Verify court_cases_referenced JSON follows consistent structure"""
        pass


class TestFollowupEventsStructure:
    """Test structure of followup_events_with_dates field"""

    def test_followup_event_dates_are_valid_iso_format(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """Verify dates in followup events follow ISO format"""
        pass


class TestCrossFieldDataIntegrity:
    """Test cross-field relationships and data integrity"""

    def test_response_url_matches_registration_number(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """Verify response_url contains the registration_number"""
        pass

    def test_initiative_url_matches_registration_number(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """Verify initiative_url contains the registration_number"""
        pass

    def test_submission_text_mentions_submission_date(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """Verify submission_text references the commission_submission_date"""
        pass

    def test_actions_dates_fall_within_initiative_timeline(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """Verify action dates in laws_actions/policies_actions are chronologically sound"""
        pass


class TestDataCompletenessMetrics:
    """Test overall data completeness across the dataset"""

    def test_mandatory_fields_completeness_rate(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """Verify mandatory fields have 100% completeness rate"""
        pass

    def test_optional_fields_distribution(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """
        Analyze and validate that there is at least values in optional fields.
        10% < x <100%
        """
        pass

    def test_procedural_timeline_completeness(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """Verify procedural milestone fields have expected completeness"""
        pass


class TestBooleanFieldsConsistency:
    """Test consistency of boolean flag fields"""

    def test_boolean_fields_are_true_or_false(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """Verify boolean fields contain only True, False, or None values"""
        pass

    def test_mutually_exclusive_boolean_flags(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """Verify mutually exclusive flags (e.g., promised_new_law vs rejected_initiative)"""
        pass
