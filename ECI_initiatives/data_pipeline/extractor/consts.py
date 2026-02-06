"""
Shared constants and configuration for ECI data extractors.
"""

from pathlib import Path


# ============================================================================
# Project Structure
# ============================================================================

# Script directory (project root detection)
# Note: This is 3 levels up from extractor/consts.py -> data_pipeline -> ECI_initiatives -> project_root
SCRIPT_DIR = Path(__file__).resolve().parent.parent.parent


# ============================================================================
# Directory Structure
# ============================================================================


class DirectoryStructure:
    """Standard directory names used across extractors."""

    DATA_DIR_NAME = "data"
    LOG_DIR_NAME = "logs"

    # Module-specific directories (defined here for reference)
    INITIATIVES_DIR_NAME = "initiatives"
    RESPONSES_DIR_NAME = "responses"
    RESPONSES_FOLLOWUP_WEBSITE_DIR_NAME = "responses_followup_website"


# ============================================================================
# File Patterns and Naming
# ============================================================================


class FilePatterns:
    """Common file naming patterns and regex for matching files."""

    # HTML file patterns
    HTML_FILE_PATTERN = "*.html"
    HTML_FILE_GLOB_PATTERN = "**/*.html"
    HTML_FILE_EXTENSION = ".html"

    # HTML filename regex for extracting registration number
    # Matches: YYYY_NNNNNN_en.html (e.g., 2019_000007_en.html)
    FILENAME_REGEX = r"(\d{4})_(\d{6})_en\.html"
    HTML_FILENAME_PATTERN = r"(\d{4})_(\d{6})_([a-z]{2})\.html"  # More flexible version

    # Timestamp directory pattern for finding scraper session directories
    # Matches: YYYY-MM-DD_HH-MM-SS (e.g., 2026-02-05_18-30-45)
    TIMESTAMP_DIR_PATTERN = r"\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}"


# ============================================================================
# Time and Date Formats
# ============================================================================


class TimeFormats:
    """Standard timestamp and date format strings."""

    # Timestamp format for generated files and directories
    TIMESTAMP_FORMAT = "%Y-%m-%d_%H-%M-%S"

    # Date format for data fields
    DATE_FORMAT = "%Y-%m-%d"


# ============================================================================
# File Encoding
# ============================================================================

FILE_ENCODING = "utf-8"


# ============================================================================
# URL Configuration
# ============================================================================


class URLConfig:
    """Base URLs and URL templates for EU Citizens' Initiative website."""

    BASE_URL = "https://citizens-initiative.europa.eu"

    # URL template for initiative details page
    INITIATIVE_DETAILS_URL_TEMPLATE = (
        "{base_url}/initiatives/details/{year}/{number}_en"
    )


# ============================================================================
# CSV Configuration
# ============================================================================


class CSVConfig:
    """Common CSV configuration across extractors."""

    # Common CSV field name for registration numbers across all modules
    FIELD_REGISTRATION_NUMBER = "registration_number"

    # Common CSV field name for initiative titles
    FIELD_INITIATIVE_TITLE = "initiative_title"

    # CSV newline setting (empty string for universal newlines mode)
    NEWLINE = ""


# ============================================================================
# Logging Configuration
# ============================================================================


class LoggingConfig:
    """Standard logging settings for all extractors."""

    # Log level
    LOG_LEVEL = "INFO"

    # Log format strings
    FORMAT_SIMPLE = "%(levelname)s - %(message)s"
    FORMAT_CONSOLE = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    FORMAT_DETAILED = (
        "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
    )

    # Date format for log timestamps
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


# ============================================================================
# HTML Parsing Configuration
# ============================================================================


class HTMLParsingConfig:
    """HTML parsing configuration."""

    # BeautifulSoup parser
    PARSER = "html.parser"

    # Minimum acceptable HTML length (for validation)
    MIN_HTML_LENGTH = 1000


# ============================================================================
# Registration Number Format
# ============================================================================


class RegistrationNumberFormat:
    """Standard format for ECI registration numbers."""

    # Format: YYYY/NNNNNN (e.g., 2019/000007)
    SEPARATOR = "/"
    FORMAT_TEMPLATE = "{year}{separator}{number}"

    # Regex pattern to match registration numbers
    PATTERN = r"(\d{4})/(\d{6})"


# ============================================================================
# Content Extraction Limits
# ============================================================================


class ContentLimits:
    """Character limits for extracted content fields."""

    # Maximum characters for objective/description fields
    OBJECTIVE_MAX_LENGTH = 1100

    # Maximum characters for summary fields
    SUMMARY_MAX_LENGTH = 500
