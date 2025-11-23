"""
Shared fixtures for ECI model data quality tests.

This module contains pytest fixtures that are shared across all data quality test files.
Column and row level validation tests for ECICommissionResponseRecord fields.
"""

# Python
import csv
import html
import json
import re
import shutil
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, List, Optional, Set
from unittest import mock
from urllib.parse import ParseResult, unquote, urlparse

# Third-party
from bs4 import BeautifulSoup
import pytest

# Eci app extractor
from ECI_initiatives.extractor.responses.model import ECICommissionResponseRecord
from ECI_initiatives.extractor.responses.processor import ECIResponseDataProcessor
from ECI_initiatives.extractor.responses.parser.consts.eci_status import (
    ECIImplementationStatus,
)

# Test data paths
TEST_DATA_DIR = (
    Path(__file__).parent.parent.parent.parent.parent
    / "data"
    / "example_htmls"
    / "responses"
)


def validate_test_data_directory_exists():
    """Validate that TEST_DATA_DIR exists and is a valid directory."""

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


def check_if_any_HTML_files_exist():
    """Verify that at least one HTML test file exists in TEST_DATA_DIR."""

    html_files = list(TEST_DATA_DIR.rglob("*.html"))
    if not html_files:
        raise FileNotFoundError(
            f"No HTML test files found in: {TEST_DATA_DIR}\n"
            f"Expected files matching pattern: **/*.html\n"
            f"Directory contents: {list(TEST_DATA_DIR.iterdir())}"
        )


validate_test_data_directory_exists()
check_if_any_HTML_files_exist()


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

    metadata_file = responses_dir / "responses_list.csv"
    html_files_tests = list(responses_dir.glob("*.html"))

    with open(metadata_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["registration_number", "title", "url"])
        writer.writeheader()

        for html_file in html_files_tests:
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
