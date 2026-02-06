"""
Shared constants and configuration for the ECI responses CSV merger.

This module centralizes directory paths, file patterns, timestamp formats,
and mandatory field configuration used by the merger and strategy code.
"""

from pathlib import Path
from datetime import datetime

# ============================================================================
# Project Structure
# ============================================================================


# Base directory for the project, resolved from this file:
# csv_merger/responses/const.py -> responses -> csv_merger -> ECI_initiatives
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Base data directory (ECI_initiatives/data)
DATA_DIR = PROJECT_ROOT / "data"


# ============================================================================
# Directory and File Patterns
# ============================================================================


class DirectoryNames:
    """Standard directory names used by the merger."""

    DATA = "data"
    LOGS = "logs"


class FilenamePatterns:
    """Filename prefixes and patterns for input and output CSV files."""

    # Input CSV prefixes (from latest timestamp directory)
    RESPONSES_PREFIX = "eci_responses_"
    FOLLOWUP_PREFIX = "eci_responses_followup_website_"

    # Output CSV filename pattern (in latest timestamp directory)
    OUTPUT_PREFIX = "eci_merger_responses_and_followup_"
    OUTPUT_PATTERN = OUTPUT_PREFIX + "{timestamp}.csv"

    # Log filename pattern (under latest_dir/logs/)
    LOG_PREFIX = "merger_responses_and_followup_"
    LOG_PATTERN = LOG_PREFIX + "{timestamp}.log"


class TimestampPatterns:
    """Timestamp formats and patterns used for directories and files."""

    # Directory name format and pattern: YYYY-MM-DD_HH-MM-SS
    DIR_FORMAT = "%Y-%m-%d_%H-%M-%S"

    # Regex-equivalent pattern used in merger._is_timestamp_dirname logic
    DIR_EXAMPLE_PATTERN = r"\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}"

    # Convenience: now() formatted for filenames
    @staticmethod
    def now_timestamp() -> str:
        return datetime.now().strftime(TimestampPatterns.DIR_FORMAT)


# ============================================================================
# File Encoding
# ============================================================================


FILE_ENCODING = "utf-8"
CSV_NEWLINE = ""  # for csv.open(newline="") usage


# ============================================================================
# Mandatory Fields Configuration
# ============================================================================


# Mandatory fields that must be present in base dataset only
MANDATORY_BASE_FIELDS = [
    "response_url",
    "initiative_url",
    "submission_text",
]

# Mandatory fields that must be present in followup dataset only
MANDATORY_FOLLOWUP_FIELDS = [
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

# Mandatory fields that must be present in BOTH datasets
MANDATORY_BOTH_FIELDS = list(set(MANDATORY_FOLLOWUP_FIELDS))


# ============================================================================
# Logging Configuration
# ============================================================================


class LoggingConfig:
    """Standard logging configuration for the merger."""

    LEVEL = "INFO"
    FORMAT_CONSOLE = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    FORMAT_FILE = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
