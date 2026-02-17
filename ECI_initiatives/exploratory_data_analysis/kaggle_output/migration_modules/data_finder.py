"""
Data file discovery and validation utilities
"""

import csv
import logging
from pathlib import Path
from typing import Tuple


class DataFinder:
    """Handles finding and validating ECI data files"""

    def __init__(self, data_path: Path, logger: logging.Logger):
        self.data_path = data_path
        self.logger = logger

    def get_latest_data_folder(self) -> Path:
        """
        Find the latest timestamped data folder from ECI_initiatives/data/

        Returns:
            Path object to the most recent data folder (e.g., 2026-02-16_10-23-16)
        """
        data_folders = [d for d in self.data_path.iterdir() if d.is_dir()]
        if not data_folders:
            raise FileNotFoundError(
                f"No data folders found in {self.data_path}\n"
                f"Expected timestamped folders like: 2026-02-16_10-23-16"
            )

        # Sort by folder name (timestamp format ensures chronological order)
        latest = max(data_folders, key=lambda d: d.name)
        self.logger.info(f"Found latest data folder: {latest.name}")
        return latest

    def validate_csv(self, csv_path: Path) -> bool:
        """
        Validate that a CSV file is not empty and has valid format

        Args:
            csv_path: Path to the CSV file

        Returns:
            True if valid, raises ValueError if invalid
        """
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        if csv_path.stat().st_size == 0:
            raise ValueError(f"CSV file is empty: {csv_path.name}")

        try:
            with open(csv_path, "r", encoding="utf-8", newline="") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                if not header:
                    raise ValueError(f"CSV file has no header: {csv_path.name}")

                if len(header) < 2:
                    self.logger.warning(
                        f"CSV {csv_path.name} has only {len(header)} columns, suspicious format"
                    )

                try:
                    next(reader)
                except csv.Error:
                    pass
        except UnicodeDecodeError:
            raise ValueError(f"CSV file is not valid UTF-8: {csv_path.name}")
        except Exception as e:
            raise ValueError(f"CSV file error: {csv_path.name} ({e})")

        return True

    def find_most_recent_csv(self, data_folder: Path, pattern: str) -> Path:
        """
        Find the most recent CSV file matching a pattern in the data folder
        """
        csv_files = list(data_folder.glob(f"{pattern}*.csv"))
        if not csv_files:
            raise FileNotFoundError(
                f"No CSV files found matching pattern '{pattern}' in {data_folder}"
            )

        most_recent = max(csv_files, key=lambda f: f.name)
        self.validate_csv(most_recent)
        self.logger.info(f"Found most recent {pattern}CSV: {most_recent.name}")
        return most_recent

    def find_required_csvs(self, data_folder: Path) -> Tuple[Path, Path]:
        """
        Find the most recent required CSV files in the data folder
        """
        try:
            initiatives_csv = self.find_most_recent_csv(data_folder, "eci_initiatives_")
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Could not find eci_initiatives CSV in {data_folder}\n"
                f"Expected file like: eci_initiatives_2026-02-16_10-33-56.csv"
            )

        try:
            responses_csv = self.find_most_recent_csv(
                data_folder, "eci_merger_responses_and_followup_"
            )
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Could not find eci_merger_responses CSV in {data_folder}\n"
                f"Expected file like: eci_merger_responses_and_followup_2026-02-16_10-35-18.csv"
            )

        return initiatives_csv, responses_csv
