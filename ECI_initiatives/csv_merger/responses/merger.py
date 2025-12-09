"""
Main merger class for combining ECI responses and followup data.
"""

import csv
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Callable

from .exceptions import (
    DataDirectoryNotFoundError,
    NoTimestampDirectoryError,
    MissingInputFileError,
    EmptyDataError,
    FollowupRowCountExceedsBaseError,
    RegistrationNumberMismatchError,
    MissingColumnsError,
)
from .strategies import merge_field_values


class ResponsesAndFollowupMerger:
    """
    Merges ECI responses CSV with followup website CSV data.

    This class handles:
    - Discovery of the latest data directory and input files
    - Validation of input data
    - Merging of CSV files using a pluggable field merging strategy
    - Logging of the merge process
    """

    def __init__(
        self,
        base_data_dir: Optional[Path] = None,
        merge_strategy: Optional[Callable[[str, str, str, str], str]] = None,
    ):
        """
        Initialize the merger.

        Args:
            base_data_dir: Path to the base data directory. If None, automatically
                          resolves to ECI_initiatives/data relative to this file.
            merge_strategy: Function to merge field values. If None, uses default.

        Raises:
            Various MergerError subclasses if validation fails
        """

        # Resolve base_data_dir
        if base_data_dir is None:
            # Get the absolute path of this file (merger.py)
            current_file = Path(__file__).resolve()
            # Navigate from ECI_initiatives/csv_merger/responses/merger.py
            # to ECI_initiatives/data
            # merger.py -> responses/ -> csv_merger/ -> ECI_initiatives/ -> data/
            base_data_dir = current_file.parent.parent.parent / "data"

        self.base_data_dir = base_data_dir
        self.merge_strategy = merge_strategy or merge_field_values

        # Discover paths
        self._validate_base_dir()
        self.latest_dir = self._find_latest_timestamp_dir()
        self.base_csv_path = self._find_latest_csv("eci_responses_")
        self.followup_csv_path = self._find_latest_csv(
            "eci_responses_followup_website_"
        )

        # Setup output paths
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.output_csv_path = (
            self.latest_dir / f"eci_merger_responses_and_followup_{timestamp}.csv"
        )
        self.log_path = (
            self.latest_dir / "logs" / f"merger_responses_and_followup_{timestamp}.log"
        )

        # Setup logging
        self._setup_logging()

        # Validate input files
        self._validate_input_files()

    def _validate_base_dir(self) -> None:
        """Validate that the base data directory exists."""

        if not self.base_data_dir.exists():
            raise DataDirectoryNotFoundError(
                f"Base data directory does not exist:\n{self.base_data_dir}"
            )
        if not self.base_data_dir.is_dir():
            raise DataDirectoryNotFoundError(
                f"Base data path is not a directory:\n{self.base_data_dir}"
            )

    def _find_latest_timestamp_dir(self) -> Path:
        """
        Find the latest timestamp subdirectory under base_data_dir.

        Returns:
            Path to the latest timestamp directory

        Raises:
            NoTimestampDirectoryError: If no timestamp directory is found
        """
        timestamp_dirs = [
            d
            for d in self.base_data_dir.iterdir()
            if d.is_dir() and self._is_timestamp_dirname(d.name)
        ]

        if not timestamp_dirs:
            raise NoTimestampDirectoryError(
                f"No timestamp subdirectories found in {self.base_data_dir}"
            )

        # Sort by directory name (timestamp format ensures lexicographic = chronological)
        latest = sorted(timestamp_dirs, key=lambda d: d.name)[-1]
        return latest

    @staticmethod
    def _is_timestamp_dirname(name: str) -> bool:
        """Check if directory name matches timestamp pattern YYYY-MM-DD_HH-MM-SS."""

        try:
            datetime.strptime(name, "%Y-%m-%d_%H-%M-%S")
            return True
        except ValueError:
            return False

    def _find_latest_csv(self, prefix: str) -> Path:
        """
        Find the latest CSV file with the given prefix in latest_dir.

        The prefix should match the exact pattern: prefix + timestamp + .csv
        For example:
        - "eci_responses_" matches "eci_responses_2025-11-17_14-50-27.csv"
        - "eci_responses_followup_website_" matches "eci_responses_followup_website_2025-12-09_13-11-34.csv"

        Args:
            prefix: CSV filename prefix (e.g., "eci_responses_", "eci_responses_followup_website_")

        Returns:
            Path to the latest matching CSV file

        Raises:
            MissingInputFileError: If no matching CSV is found
        """

        # Create regex pattern: prefix + timestamp pattern + .csv
        # Timestamp pattern: YYYY-MM-DD_HH-MM-SS
        pattern = re.compile(
            rf"^{re.escape(prefix)}\d{{4}}-\d{{2}}-\d{{2}}_\d{{2}}-\d{{2}}-\d{{2}}\.csv$"
        )

        matching_files = [
            f
            for f in self.latest_dir.iterdir()
            if f.is_file() and pattern.match(f.name)
        ]

        if not matching_files:
            raise MissingInputFileError(
                f"No CSV file matching pattern '{prefix}YYYY-MM-DD_HH-MM-SS.csv' found in {self.latest_dir}"
            )

        # Sort by filename (timestamp in name ensures correct ordering)
        latest = sorted(matching_files, key=lambda f: f.name)[-1]
        return latest

    def _setup_logging(self) -> None:
        """Setup logging to both file and console."""

        # Ensure logs directory exists
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

        # Create logger
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        # Remove existing handlers to avoid duplicates
        self.logger.handlers.clear()

        # File handler
        file_handler = logging.FileHandler(self.log_path, mode="w", encoding="utf-8")
        file_handler.setLevel(logging.INFO)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def _validate_input_files(self) -> None:
        """
        Validate input CSV files according to requirements.

        Raises:
            Various MergerError subclasses if validation fails
        """

        self.logger.info("Starting input file validation...")

        # Load data
        base_data = self._load_csv(self.base_csv_path)
        followup_data = self._load_csv(self.followup_csv_path)

        # Check for empty data
        if len(base_data) == 0:
            raise EmptyDataError(
                f"Base CSV has no data rows: {self.base_csv_path.name}"
            )

        if len(followup_data) == 0:
            raise EmptyDataError(
                f"Followup CSV has no data rows: {self.followup_csv_path.name}"
            )

        # Check row counts
        if len(followup_data) > len(base_data):
            raise FollowupRowCountExceedsBaseError(
                f"Followup CSV has {len(followup_data)} rows, "
                f"but base CSV only has {len(base_data)} rows"
            )

        # Check registration numbers
        base_reg_numbers = {row["registration_number"] for row in base_data}
        followup_reg_numbers = {row["registration_number"] for row in followup_data}

        missing_reg_numbers = followup_reg_numbers - base_reg_numbers
        if missing_reg_numbers:
            raise RegistrationNumberMismatchError(
                f"Followup CSV contains registration_numbers not in base CSV: "
                f"{sorted(missing_reg_numbers)}"
            )

        # Check columns
        base_columns = set(base_data[0].keys()) if base_data else set()
        followup_columns = set(followup_data[0].keys()) if followup_data else set()

        missing_columns = followup_columns - base_columns
        if missing_columns:
            raise MissingColumnsError(
                f"Followup CSV is missing columns that exist in base CSV: "
                f"{sorted(missing_columns)}"
            )

        self.logger.info("Input file validation passed")
        self.logger.info(
            f"Base CSV: {len(base_data)} rows, {len(base_columns)} columns"
        )
        self.logger.info(
            f"Followup CSV: {len(followup_data)} rows, {len(followup_columns)} columns"
        )

    def _load_csv(self, path: Path) -> List[Dict[str, str]]:
        """Load CSV file and return list of row dictionaries."""

        with open(path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            return list(reader)

    def merge(self) -> None:
        """
        Execute the merge operation.

        This method:
        1. Loads both CSV files
        2. Creates a lookup for followup data by registration_number
        3. Merges each base row with its corresponding followup row
        4. Writes the merged data to the output CSV
        """

        self.logger.info("=" * 80)
        self.logger.info("Starting merge operation")
        self.logger.info(f"Base CSV: {self.base_csv_path.name}")
        self.logger.info(f"Followup CSV: {self.followup_csv_path.name}")
        self.logger.info(f"Output CSV: {self.output_csv_path.name}")
        self.logger.info("=" * 80)

        # Load data
        self.logger.info("Loading CSV files...")
        base_data = self._load_csv(self.base_csv_path)
        followup_data = self._load_csv(self.followup_csv_path)

        # Create followup lookup by registration_number
        followup_lookup = {row["registration_number"]: row for row in followup_data}

        # Get all columns (base columns define the schema)
        base_columns = list(base_data[0].keys())

        # Merge rows
        self.logger.info(
            (
                f"Merging {len(followup_data)} rows "
                f"into base data {len(base_data)} "
                "..."
            )
        )
        merged_data = []

        for base_row in base_data:
            reg_number = base_row["registration_number"]
            followup_row = followup_lookup.get(reg_number)

            if followup_row:
                # Merge this row using the merge strategy
                merged_row = self._merge_rows(
                    base_row, followup_row, base_columns, reg_number
                )
            else:
                # No followup data for this registration number
                merged_row = base_row

            merged_data.append(merged_row)

        # Write output
        self.logger.info(f"Writing merged data to {self.output_csv_path}...")
        self._write_csv(self.output_csv_path, merged_data, base_columns)

        self.logger.info("=" * 80)
        self.logger.info(f"Merge completed successfully")
        self.logger.info(f"Output: {self.output_csv_path}")
        self.logger.info(f"Log: {self.log_path}")
        self.logger.info("=" * 80)

    def _merge_rows(
        self,
        base_row: Dict[str, str],
        followup_row: Dict[str, str],
        columns: List[str],
        reg_number: str,
    ) -> Dict[str, str]:
        """
        Merge a single base row with its corresponding followup row.

        Args:
            base_row: Row from base CSV
            followup_row: Row from followup CSV
            columns: List of all columns to include in output
            reg_number: Registration number for this row

        Returns:
            Merged row dictionary
        """

        merged_row = {}

        for col in columns:
            base_value = base_row.get(col, "")
            followup_value = followup_row.get(col, "")

            # Use merge strategy to combine values
            merged_row[col] = self.merge_strategy(
                base_value, followup_value, col, reg_number
            )

        return merged_row

    def _write_csv(
        self, path: Path, data: List[Dict[str, str]], columns: List[str]
    ) -> None:
        """Write data to CSV file."""

        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            writer.writerows(data)
