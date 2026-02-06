"""
Constants and configuration for the Follow-up Website Extractor.

This module processes HTML files from dedicated follow-up websites
and extracts structured data about Commission responses and follow-up actions.
"""

from pathlib import Path

# ============================================================================
# Shared Project Structure Constants
# ============================================================================

# Script directory (project root detection)
SCRIPT_DIR = Path(__file__).resolve().parent.parent.parent.parent

# Directory names
DATA_DIR_NAME = "data"
LOG_DIR_NAME = "logs"
RESPONSES_FOLLOWUP_WEBSITE_DIR_NAME = "responses_followup_website"

# ============================================================================
# File Patterns and Naming
# ============================================================================

# Timestamp format for generated files
TIMESTAMP_FORMAT = "%Y-%m-%d_%H-%M-%S"

# Timestamp directory pattern (regex) for finding session directories
TIMESTAMP_DIR_PATTERN = r"\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}"

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
HTML_FILE_EXTENSION = ".html"
HTML_FILE_GLOB_PATTERN = f"**/*{HTML_FILE_EXTENSION}"

# HTML filename regex pattern for extracting registration number
# Expected format: YYYY_NNNNNN_en.html
HTML_FILENAME_PATTERN = r"(\d{4})_(\d{6})_([a-z]{2})\.html"

# ============================================================================
# File Encoding
# ============================================================================

FILE_ENCODING = "utf-8"

# ============================================================================
# CSV Configuration
# ============================================================================

# Input CSV field names (from responses extractor)
CSV_FIELD_REGISTRATION_NUMBER = "registration_number"
CSV_FIELD_INITIATIVE_TITLE = "initiative_title"
CSV_FIELD_FOLLOWUP_DEDICATED_WEBSITE = "followup_dedicated_website"

# ============================================================================
# HTML Parsing Configuration
# ============================================================================

# BeautifulSoup parser
HTML_PARSER = "html.parser"

# ============================================================================
# Logging Configuration
# ============================================================================

# Log level
LOG_LEVEL = "INFO"

# Log format
LOG_FORMAT_DETAILED = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# ============================================================================
# Registration Number Format
# ============================================================================

# Format for registration numbers: YYYY/NNNNNN
REGISTRATION_NUMBER_SEPARATOR = "/"
REGISTRATION_NUMBER_FORMAT = "{year}{separator}{number}"
