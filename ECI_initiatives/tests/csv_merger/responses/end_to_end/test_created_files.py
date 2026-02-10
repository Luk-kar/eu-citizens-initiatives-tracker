"""
End-to-end tests for ResponsesAndFollowupMerger.

Tests core behaviours:
- Finding the latest timestamped data directory
- Loading the latest responses CSV and followup CSV
- Validating input files (row counts, registration numbers, columns)
- Creating a merged CSV with correct structure
- Creating a log file in logs/
"""

# Standard library
import csv
import importlib
from datetime import datetime
from pathlib import Path

# Third-party
import pytest

# Local
from ECI_initiatives.data_pipeline.csv_merger.responses.merger import (
    ResponsesAndFollowupMerger,
)
from ECI_initiatives.data_pipeline.csv_merger.responses.exceptions import (
    MissingInputFileError,
    EmptyDataError,
    FollowupRowCountExceedsBaseError,
)


class TestMergerCreatedFiles:
    """
    End-to-end tests for the responses and followup CSV merger pipeline.
    """

    @pytest.fixture
    def project_structure(self, tmp_path: Path) -> tuple[Path, Path]:
        """
        Setup test project structure.

        Returns:
            Tuple of (project_root, data_root)
        """
        project_root = tmp_path / "ECI_initiatives"
        data_root = project_root / "data"
        data_root.mkdir(parents=True, exist_ok=True)

        return project_root, data_root

    @pytest.fixture
    def data_root(
        self, project_structure: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch
    ) -> Path:
        """
        Setup and patch merger file resolution, return data_root.

        NOTE WHY: The merger's __init__ uses Path(__file__).resolve() to automatically
        discover the data directory by navigating from its own file location:
          merger.py -> responses/ -> csv_merger/ -> ECI_initiatives/ -> data/
        In tests, we're using a temporary directory (tmp_path), not the real repo.
        We must trick the merger into thinking it's running from our fake test
        structure by patching the module's __file__ attribute to point to our
        temporary processor_file. This makes the path resolution work correctly
        with our test data_root instead of trying to find the real installation.
        """
        project_root, data_root_path = project_structure

        # Patch __file__ resolution
        processor_module = ResponsesAndFollowupMerger.__module__
        processor_file = project_root / "csv_merger" / "responses" / "merger.py"
        processor_file.parent.mkdir(parents=True, exist_ok=True)
        processor_file.write_text("# dummy file to satisfy Path(__file__) resolution")

        module_obj = importlib.import_module(processor_module)
        monkeypatch.setattr(module_obj, "__file__", str(processor_file))

        return data_root_path

    @pytest.fixture
    def session_dir(self, data_root: Path) -> Path:
        """
        Create a timestamped session directory.
        """
        session_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        session_dir = data_root / session_name
        session_dir.mkdir(parents=True, exist_ok=True)

        return session_dir

    @pytest.fixture
    def responses_csv_path(self, session_dir: Path) -> Path:
        """
        Write a responses CSV with 3 rows of real ECI data.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        csv_path = session_dir / f"eci_responses_{timestamp}.csv"

        fieldnames = [
            "registration_number",
            "initiative_title",
            "response_url",
            "initiative_url",
            "submission_text",
            "followup_dedicated_website",
            "commission_answer_text",
            "commission_promised_new_law",
            "commission_rejected_initiative",
            "has_roadmap",
            "has_workshop",
            "has_partnership_programs",
            "followup_events_with_dates",
        ]

        with csv_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerow(
                {
                    "registration_number": "2018/000004",
                    "initiative_title": "End the Cage Age",
                    "response_url": "https://citizens-initiative.europa.eu/initiatives/details/2018/000004_en",
                    "initiative_url": "https://citizens-initiative.europa.eu/initiatives/details/2018/000004",
                    "submission_text": "The End the Cage Age initiative was submitted to the Commission on 2 October 2020...",
                    "followup_dedicated_website": "https://food.ec.europa.eu/animals/animal-welfare/eci/eci-end-cage-age_en",
                    "commission_answer_text": "In its response to the ECI, the Commission communicated its intention to table...",
                    "commission_promised_new_law": "True",
                    "commission_rejected_initiative": "False",
                    "has_roadmap": "False",
                    "has_workshop": "False",
                    "has_partnership_programs": "False",
                    "followup_events_with_dates": '[{"date": "2021-10-15", "action": "EFSA scientific opinions published"}]',
                }
            )
            writer.writerow(
                {
                    "registration_number": "2022/000002",
                    "initiative_title": "Fur Free Europe",
                    "response_url": "https://citizens-initiative.europa.eu/initiatives/details/2022/000002_en",
                    "initiative_url": "https://citizens-initiative.europa.eu/initiatives/details/2022/000002",
                    "submission_text": "The Fur Free Europe initiative was submitted to the European Commission on 14 June 2023...",
                    "followup_dedicated_website": "https://food.ec.europa.eu/animals/animal-welfare/eci/eci-fur-free-europe_en",
                    "commission_answer_text": "The Commission published the response to this initiative on 7 December 2023...",
                    "commission_promised_new_law": "False",
                    "commission_rejected_initiative": "False",
                    "has_roadmap": "False",
                    "has_workshop": "False",
                    "has_partnership_programs": "False",
                    "followup_events_with_dates": '[{"dates": "2023-08-31", "action": "The Commission launched a review..."}]',
                }
            )
            writer.writerow(
                {
                    "registration_number": "2012/000003",
                    "initiative_title": "Water and sanitation are a human right!",
                    "response_url": "https://citizens-initiative.europa.eu/initiatives/details/2012/000003_en",
                    "initiative_url": "https://citizens-initiative.europa.eu/initiatives/details/2012/000003",
                    "submission_text": "Right2Water was the first European Citizens Initiative having gathered the required...",
                    "followup_dedicated_website": "https://ec.europa.eu/environment/water/water-drink/",
                    "commission_answer_text": "The Commission committed to taking actions to reinforce implementation of EU water...",
                    "commission_promised_new_law": "True",
                    "commission_rejected_initiative": "False",
                    "has_roadmap": "True",
                    "has_workshop": "True",
                    "has_partnership_programs": "True",
                    "followup_events_with_dates": '[{"date": "2015-10-28", "action": "Amendment to Drinking Water Directive..."}]',
                }
            )

        return csv_path

    @pytest.fixture
    def followup_csv_path(self, session_dir: Path) -> Path:
        """
        Write a followup CSV with 2 rows of real ECI data.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        csv_path = session_dir / f"eci_responses_followup_website_{timestamp}.csv"

        fieldnames = [
            "registration_number",
            "initiative_title",
            "followup_dedicated_website",
            "commission_answer_text",
            "commission_promised_new_law",
            "commission_rejected_initiative",
            "has_roadmap",
            "has_workshop",
            "has_partnership_programs",
            "followup_events_with_dates",
        ]

        with csv_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerow(
                {
                    "registration_number": "2018/000004",
                    "initiative_title": "End the Cage Age",
                    "followup_dedicated_website": "https://food.ec.europa.eu/animals/animal-welfare/eci/eci-end-cage-age_en",
                    "commission_answer_text": "On 30 June 2021, the Commission decided to positively respond to the ECI...",
                    "commission_promised_new_law": "True",
                    "commission_rejected_initiative": "False",
                    "has_roadmap": "False",
                    "has_workshop": "False",
                    "has_partnership_programs": "False",
                    "followup_events_with_dates": '[{"dates": "2025-06-18", "action": "Further to the call for evidence..."}]',
                }
            )
            writer.writerow(
                {
                    "registration_number": "2022/000002",
                    "initiative_title": "Fur Free Europe",
                    "followup_dedicated_website": "https://food.ec.europa.eu/animals/animal-welfare/eci/eci-fur-free-europe_en",
                    "commission_answer_text": "The Commission published the response to this initiative on 7 December 2023...",
                    "commission_promised_new_law": "False",
                    "commission_rejected_initiative": "False",
                    "has_roadmap": "False",
                    "has_workshop": "False",
                    "has_partnership_programs": "False",
                    "followup_events_with_dates": '[{"dates": "2025-07-04", "action": "On 4 July 2025, the Commission launched..."}]',
                }
            )

        return csv_path

    def test_merger_creates_log_and_csv_with_rows(
        self,
        data_root: Path,
        session_dir: Path,
        responses_csv_path: Path,
        followup_csv_path: Path,
    ):
        """
        Full pipeline smoke test:
        - Create a fake data root (ECI_initiatives/data style)
        - Create one timestamped session with responses CSV and followup CSV
        - Ensure merger uses the latest session
        - Verify that a merged CSV and log file are created
        - Verify that merged CSV has correct number of rows
        """
        # Run merger
        merger = ResponsesAndFollowupMerger(base_data_dir=data_root)
        merger.merge()

        # Assert log file is created under latest session logs/
        logs_dir = session_dir / "logs"
        log_files = list(logs_dir.glob("merger_responses_and_followup*.log"))
        assert log_files, "Expected at least one merger log file in logs/"

        # Assert merged CSV file is created in sessiondir with the expected prefix
        csv_files = list(session_dir.glob("eci_merger_responses_and_followup*.csv"))
        assert csv_files, "Expected merged CSV file to be created"

        # Read CSV and check that there are exactly 3 data rows (matching base)
        csv_path = csv_files[0]
        with csv_path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 3, "Merged CSV should contain 3 data rows (same as base)"

        # Verify registration numbers are preserved
        reg_numbers = {row["registration_number"] for row in rows}
        assert reg_numbers == {"2018/000004", "2022/000002", "2012/000003"}

        # Verify mandatory fields are present and non-empty in all rows
        mandatory_fields = [
            "registration_number",
            "initiative_title",
            "response_url",
            "initiative_url",
            "submission_text",
        ]
        for field in mandatory_fields:
            assert all(
                row.get(field, "").strip() for row in rows
            ), f"Mandatory field '{field}' must have data in all rows"

    def test_merger_raises_when_no_responses_csv(
        self, data_root: Path, session_dir: Path, followup_csv_path: Path
    ):
        """
        Verify that ResponsesAndFollowupMerger raises MissingInputFileError
        when no eci_responses_*.csv exists in the latest data directory.
        """
        # Only followup CSV exists (via fixture)

        # Should raise MissingInputFileError during initialization
        with pytest.raises(MissingInputFileError) as exc_info:
            ResponsesAndFollowupMerger(base_data_dir=data_root)

        assert "eci_responses" in str(exc_info.value).lower()

    def test_merger_raises_when_no_followup_csv(
        self, data_root: Path, session_dir: Path, responses_csv_path: Path
    ):
        """
        Verify that ResponsesAndFollowupMerger raises MissingInputFileError
        when no eci_responses_followup_website_*.csv exists in the latest data directory.
        """
        # Only responses CSV exists (via fixture)

        # Should raise MissingInputFileError during initialization
        with pytest.raises(MissingInputFileError) as exc_info:
            ResponsesAndFollowupMerger(base_data_dir=data_root)

        assert "followup" in str(exc_info.value).lower()

    def test_merger_raises_when_empty_responses_csv(
        self, data_root: Path, session_dir: Path, followup_csv_path: Path
    ):
        """
        Verify that ResponsesAndFollowupMerger raises EmptyDataError
        when the responses CSV has only headers but no data rows.
        """
        # Write empty responses CSV (header only)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        responses_csv = session_dir / f"eci_responses_{timestamp}.csv"

        with responses_csv.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["registration_number", "initiative_title"])

        # Should raise EmptyDataError during validation
        with pytest.raises(EmptyDataError) as exc_info:
            ResponsesAndFollowupMerger(base_data_dir=data_root)

        assert "no data rows" in str(exc_info.value).lower()

    def test_merger_raises_when_followup_exceeds_base_rows(
        self, data_root: Path, session_dir: Path
    ):
        """
        Verify that ResponsesAndFollowupMerger raises FollowupRowCountExceedsBaseError
        when followup CSV has more rows than base CSV.
        """

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        # Write base CSV with 1 row
        responses_csv = session_dir / f"eci_responses_{timestamp}.csv"
        with responses_csv.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "registration_number",
                    "initiative_title",
                    "response_url",
                    "initiative_url",
                    "submission_text",
                    "followup_dedicated_website",
                    "commission_answer_text",
                    "commission_promised_new_law",
                    "commission_rejected_initiative",
                    "has_roadmap",
                    "has_workshop",
                    "has_partnership_programs",
                    "followup_events_with_dates",
                ],
            )
            writer.writeheader()
            writer.writerow(
                {
                    "registration_number": "2018/000004",
                    "initiative_title": "Test",
                    "response_url": "https://example.com",
                    "initiative_url": "https://example.com",
                    "submission_text": "Test",
                    "followup_dedicated_website": "https://example.com",
                    "commission_answer_text": "Test",
                    "commission_promised_new_law": "False",
                    "commission_rejected_initiative": "False",
                    "has_roadmap": "False",
                    "has_workshop": "False",
                    "has_partnership_programs": "False",
                    "followup_events_with_dates": "[]",
                }
            )

        # Write followup CSV with 3 rows (exceeds base)
        followup_csv = session_dir / f"eci_responses_followup_website_{timestamp}.csv"
        with followup_csv.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "registration_number",
                    "initiative_title",
                    "followup_dedicated_website",
                    "commission_answer_text",
                    "commission_promised_new_law",
                    "commission_rejected_initiative",
                    "has_roadmap",
                    "has_workshop",
                    "has_partnership_programs",
                    "followup_events_with_dates",
                ],
            )
            writer.writeheader()
            for i in range(3):
                writer.writerow(
                    {
                        "registration_number": f"2018/00000{i}",
                        "initiative_title": "Test",
                        "followup_dedicated_website": "https://example.com",
                        "commission_answer_text": "Test",
                        "commission_promised_new_law": "False",
                        "commission_rejected_initiative": "False",
                        "has_roadmap": "False",
                        "has_workshop": "False",
                        "has_partnership_programs": "False",
                        "followup_events_with_dates": "[]",
                    }
                )

        # Should raise FollowupRowCountExceedsBaseError during validation
        with pytest.raises(FollowupRowCountExceedsBaseError) as exc_info:
            ResponsesAndFollowupMerger(base_data_dir=data_root)

        error_msg = str(exc_info.value).lower()
        assert "followup csv has 3 rows" in error_msg
        assert "base csv only has 1 rows" in error_msg
