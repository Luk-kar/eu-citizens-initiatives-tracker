"""
CSV file operations for reading ECI responses data.
"""

import csv
import os
import logging
from typing import List, Dict, Optional
from pathlib import Path

from ..consts import (
    ECI_RESPONSES_CSV_PATTERN,
    FOLLOWUP_WEBSITE_COLUMN,
    REGISTRATION_NUMBER_COLUMN,
)
from ..errors import MissingCSVFileError


def find_latest_csv_file(data_dir: str) -> str:
    """
    Find the most recent eci_responses CSV file in the data directory.

    Args:
        data_dir: Path to the timestamp data directory

    Returns:
        Full path to the latest CSV file

    Raises:
        MissingCSVFileError: If no CSV file is found
    """
    logger = logging.getLogger("ECIFollowupWebsiteScraper")

    # Search for CSV files matching the pattern
    data_path = Path(data_dir)
    csv_files = list(data_path.glob(ECI_RESPONSES_CSV_PATTERN))

    if not csv_files:
        raise MissingCSVFileError(data_dir)

    # Sort to get the latest (most recent timestamp)
    csv_files.sort(reverse=True)
    latest_csv = str(csv_files[0])

    logger.info(f"Found CSV file: {latest_csv}")
    return latest_csv


def extract_followup_website_urls(csv_path: str) -> List[Dict[str, str]]:
    """
    Extract followup website URLs from the eci_responses CSV file.

    Args:
        csv_path: Path to the eci_responses CSV file

    Returns:
        List of dictionaries with 'url', 'registration_number', 'year'
    """
    logger = logging.getLogger("ECIFollowupWebsiteScraper")

    followup_urls = []

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            followup_url = row.get(FOLLOWUP_WEBSITE_COLUMN, "").strip()
            registration_number = row.get(REGISTRATION_NUMBER_COLUMN, "").strip()

            # Skip if no followup website URL
            if not followup_url or followup_url == "":
                continue

            # Extract year from registration number (format: YYYY/NNNNNN)
            year = (
                registration_number.split("/")[0] if "/" in registration_number else ""
            )

            # Format registration number for filename (YYYY_NNNNNN)
            reg_number_for_filename = registration_number.replace("/", "_")

            followup_urls.append(
                {
                    "url": followup_url,
                    "registration_number": reg_number_for_filename,
                    "year": year,
                }
            )

    return followup_urls
