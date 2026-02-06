"""
Constants and configuration for the Follow-up Website Extractor.

This module processes HTML files from dedicated follow-up websites
and extracts structured data about Commission responses and follow-up actions.
"""

from pathlib import Path

from ..consts import (
    SCRIPT_DIR,
    DirectoryStructure,
    TimeFormats,
    FilePatterns,
    FILE_ENCODING,
    CSVConfig,
    HTMLParsingConfig,
    LoggingConfig,
    RegistrationNumberFormat,
)

# ============================================================================
# File Patterns and Naming
# ============================================================================

# Input CSV patterns
INPUT_CSV_PATTERN = "eci_responses_*.csv"
INPUT_CSV_EXCLUDE_KEYWORD = "followup_website"  # Exclude files containing this

# Output CSV filename pattern
OUTPUT_CSV_PREFIX = "eci_responses_followup_website"
OUTPUT_CSV_PATTERN = f"{OUTPUT_CSV_PREFIX}_{{timestamp}}.csv"

# Log filename pattern
LOG_FILE_PREFIX = "extractor_responses_followup_website"
LOG_FILE_PATTERN = f"{LOG_FILE_PREFIX}_{{timestamp}}.log"

# ============================================================================
# CSV Configuration
# ============================================================================

CSV_FIELD_FOLLOWUP_DEDICATED_WEBSITE = "followup_dedicated_website"
