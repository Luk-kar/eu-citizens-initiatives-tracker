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
# Shared Project Structure Constants
# ============================================================================

# Directory names
DATA_DIR_NAME = DirectoryStructure.DATA_DIR_NAME
LOG_DIR_NAME = DirectoryStructure.LOG_DIR_NAME
RESPONSES_FOLLOWUP_WEBSITE_DIR_NAME = (
    DirectoryStructure.RESPONSES_FOLLOWUP_WEBSITE_DIR_NAME
)

# ============================================================================
# File Patterns and Naming
# ============================================================================

# Timestamp format for generated files
TIMESTAMP_FORMAT = TimeFormats.TIMESTAMP_FORMAT

# Timestamp directory pattern (regex) for finding session directories
TIMESTAMP_DIR_PATTERN = FilePatterns.TIMESTAMP_DIR_PATTERN

# Input CSV patterns
INPUT_CSV_PATTERN = "eci_responses_*.csv"
INPUT_CSV_EXCLUDE_KEYWORD = "followup_website"  # Exclude files containing this

# Output CSV filename pattern
OUTPUT_CSV_PREFIX = "eci_responses_followup_website"
OUTPUT_CSV_PATTERN = f"{OUTPUT_CSV_PREFIX}_{{timestamp}}.csv"

# Log filename pattern
LOG_FILE_PREFIX = "extractor_responses_followup_website"
LOG_FILE_PATTERN = f"{LOG_FILE_PREFIX}_{{timestamp}}.log"

# HTML file patterns
HTML_FILE_EXTENSION = FilePatterns.HTML_FILENAME_PATTERN
HTML_FILE_GLOB_PATTERN = FilePatterns.HTML_FILE_GLOB_PATTERN

# HTML filename regex pattern for extracting registration number
# Expected format: YYYY_NNNNNN_en.html
HTML_FILENAME_PATTERN = FilePatterns.HTML_FILENAME_PATTERN

# ============================================================================
# CSV Configuration
# ============================================================================

# Input CSV field names (from responses extractor)
CSV_FIELD_REGISTRATION_NUMBER = CSVConfig.FIELD_REGISTRATION_NUMBER
CSV_FIELD_INITIATIVE_TITLE = CSVConfig.FIELD_INITIATIVE_TITLE
CSV_FIELD_FOLLOWUP_DEDICATED_WEBSITE = "followup_dedicated_website"

# ============================================================================
# HTML Parsing Configuration
# ============================================================================

# BeautifulSoup parser
HTML_PARSER = HTMLParsingConfig.PARSER

# ============================================================================
# Logging Configuration
# ============================================================================

# Log level
LOG_LEVEL = LoggingConfig.LOG_LEVEL

# Log format
LOG_FORMAT_DETAILED = LoggingConfig.FORMAT_DETAILED

# ============================================================================
# Registration Number Format
# ============================================================================

# Format for registration numbers: YYYY/NNNNNN
REGISTRATION_NUMBER_SEPARATOR = RegistrationNumberFormat.SEPARATOR
REGISTRATION_NUMBER_FORMAT = RegistrationNumberFormat.FORMAT_TEMPLATE
