"""
End-to-end tests for ECIFollowupWebsiteProcessor.

Tests core behaviours:

- Finding the latest timestamped data directory
- Loading the latest non-followup responses CSV
- Discovering HTML files under responses_followup_website/<year>/
- Creating a followup CSV with at least one row
- Creating a log file in logs/
"""

# Standard library
import csv
import glob
import os
import shutil
from datetime import datetime
from pathlib import Path
import importlib

# Third-party
import pytest

# Local
from ECI_initiatives.data_pipeline.extractor.responses_followup_website.processor import (
    ECIFollowupWebsiteProcessor,
)


class TestFollowupCreatedFiles:
    """End-to-end tests for the followup website extraction pipeline."""

    def _create_timestamped_session_dir(self, base_dir: Path) -> Path:
        """Create a timestamped session directory under base_dir/data-like root."""

        session_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        session_dir = base_dir / session_name
        session_dir.mkdir(parents=True, exist_ok=True)
        return session_dir

    def _write_dummy_responses_csv(self, session_dir: Path) -> Path:
        """
        Write a minimal responses CSV (non-followup) in session_dir.

        The filename emulates actual responses output:
        eci_responses_YYYY-MM-DD_HH-MM-SS.csv
        and contains only the columns needed by ECIFollowupWebsiteProcessor.
        """

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        csv_path = session_dir / f"eci_responses_{timestamp}.csv"

        fieldnames = [
            "registration_number",
            "initiative_title",
            "followup_dedicated_website",
        ]

        with csv_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            # 2018 and 2022 initiatives used by the HTML fixtures
            writer.writerow(
                {
                    "registration_number": "2018/000004",
                    "initiative_title": "Test 2018 initiative",
                    "followup_dedicated_website": "https://example.com/2018/000004",
                }
            )
            writer.writerow(
                {
                    "registration_number": "2022/000002",
                    "initiative_title": "Test 2022 initiative",
                    "followup_dedicated_website": "https://example.com/2022/000002",
                }
            )

        return csv_path

    def _copy_example_htmls(self, session_dir: Path, program_root_dir: Path) -> None:
        """
        Copy example followup HTMLs into the session's responses_followup_website/<year>/ dirs.
        """

        source_base = (
            program_root_dir
            / "tests"
            / "data"
            / "example_htmls"
            / "responses_followup_website"
        )

        # 2018
        src_2018 = source_base / "2018" / "2018_000004_en.html"
        dst_2018_dir = session_dir / "responses_followup_website" / "2018"
        dst_2018_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(src_2018, dst_2018_dir / src_2018.name)

        # 2022
        src_2022 = source_base / "2022" / "2022_000002_en.html"
        dst_2022_dir = session_dir / "responses_followup_website" / "2022"
        dst_2022_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(src_2022, dst_2022_dir / src_2022.name)

    def test_processor_creates_log_and_csv_with_rows(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, program_root_dir: Path
    ):
        """
        Full pipeline smoke test:

        - Create a fake data root (ECI_initiatives/data style)
        - Create one timestamped session with HTML and a responses CSV
        - Ensure processor uses the latest session
        - Verify that a followup CSV and log file are created
        - Verify that CSV has at least one data row (not counting header)
        """

        # Emulate project root and data root: <tmp>/ECI_initiatives/data
        project_root = tmp_path / "ECI_initiatives"
        data_root = project_root / "data"
        data_root.mkdir(parents=True, exist_ok=True)

        # Create timestamped session and populate with CSV + HTML
        session_dir = self._create_timestamped_session_dir(data_root)
        self._write_dummy_responses_csv(session_dir)
        self._copy_example_htmls(session_dir, program_root_dir)

        # Patch __file__ resolution inside ECIFollowupWebsiteProcessor
        # so that it uses our temporary project_root instead of the real repo path.
        processor_module = ECIFollowupWebsiteProcessor.__module__
        processor_file = (
            project_root / "extractor" / "responses_followup_website" / "processor.py"
        )
        processor_file.parent.mkdir(parents=True, exist_ok=True)
        processor_file.write_text("# dummy file to satisfy Path(__file__) resolution\n")

        module_obj = importlib.import_module(processor_module)
        monkeypatch.setattr(module_obj, "__file__", str(processor_file))

        # Run processor
        processor = ECIFollowupWebsiteProcessor()
        processor.run()

        # Assert log file is created under latest session logs/
        logs_dir = session_dir / "logs"
        log_files = list(logs_dir.glob("extractor_responses_followup_website_*.log"))
        assert log_files, "Expected at least one followup log file in logs/"

        # Assert CSV file is created in session_dir with the expected prefix
        csv_files = list(session_dir.glob("eci_responses_followup_website_*.csv"))
        assert csv_files, "Expected followup CSV file to be created"

        # Read CSV and check that there is at least one non-empty row
        csv_path = csv_files[0]
        with csv_path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Do not assert particular columns; only check presence of data rows
        assert len(rows) > 0, "Followup CSV should contain at least one data row"

        # Basic sanity: ensure at least one row is not completely empty
        has_non_empty_row = any(any(v for v in row.values()) for row in rows)
        assert has_non_empty_row, "At least one row in followup CSV should have data"

    def test_processor_raises_when_no_responses_csv(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        """
        Verify that ECIFollowupWebsiteProcessor raises FileNotFoundError when
        no non-followup eci_responses_*.csv exists in the latest data directory.
        """
        # Emulate project root and data root: <tmp>/ECI_initiatives/data
        project_root = tmp_path / "ECI_initiatives"
        data_root = project_root / "data"
        data_root.mkdir(parents=True, exist_ok=True)

        # Create timestamped session WITHOUT the responses CSV
        session_dir = self._create_timestamped_session_dir(data_root)

        # Patch __file__ resolution inside ECIFollowupWebsiteProcessor
        processor_module = ECIFollowupWebsiteProcessor.__module__
        processor_file = (
            project_root / "extractor" / "responses_followup_website" / "processor.py"
        )
        processor_file.parent.mkdir(parents=True, exist_ok=True)
        processor_file.write_text("# dummy file to satisfy Path(__file__) resolution\n")

        module_obj = importlib.import_module(processor_module)
        monkeypatch.setattr(module_obj, "__file__", str(processor_file))

        # Should raise FileNotFoundError during initialization when loading CSV
        with pytest.raises(FileNotFoundError) as exc_info:
            ECIFollowupWebsiteProcessor()

        assert "No responses CSV file found" in str(exc_info.value)

    def test_processor_raises_when_no_html_files(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        """
        Verify that ECIFollowupWebsiteProcessor raises FileNotFoundError when
        no HTML files exist in responses_followup_website directory.
        """
        # Emulate project root and data root: <tmp>/ECI_initiatives/data
        project_root = tmp_path / "ECI_initiatives"
        data_root = project_root / "data"
        data_root.mkdir(parents=True, exist_ok=True)

        # Create timestamped session with CSV but WITHOUT HTML files
        session_dir = self._create_timestamped_session_dir(data_root)
        self._write_dummy_responses_csv(session_dir)

        # Create empty responses_followup_website directory
        html_dir = session_dir / "responses_followup_website"
        html_dir.mkdir(parents=True, exist_ok=True)

        # Patch __file__ resolution inside ECIFollowupWebsiteProcessor
        processor_module = ECIFollowupWebsiteProcessor.__module__
        processor_file = (
            project_root / "extractor" / "responses_followup_website" / "processor.py"
        )
        processor_file.parent.mkdir(parents=True, exist_ok=True)
        processor_file.write_text("# dummy file to satisfy Path(__file__) resolution\n")

        module_obj = importlib.import_module(processor_module)
        monkeypatch.setattr(module_obj, "__file__", str(processor_file))

        # Should raise FileNotFoundError during initialization when finding HTML files
        with pytest.raises(FileNotFoundError) as exc_info:
            ECIFollowupWebsiteProcessor()

        assert "No HTML files found" in str(exc_info.value)
