"""
Shared constants and configuration for ECI initiatives extractor.

Contains directory paths, file patterns, URL construction, and other
configuration values used across the extractor modules.
"""

from pathlib import Path

# Project Structure
SCRIPT_DIR = Path(__file__).parent.parent.parent.parent.absolute()


# Directory Structure
class DirectoryStructure:
    """Directory names and paths for the extractor."""

    DATA_DIR_NAME = "data"
    LOG_DIR_NAME = "logs"
    INITIATIVES_DIR_NAME = "initiatives"


# File Patterns
class FilePatterns:
    """File naming patterns and regex for matching files."""

    HTML_FILE_PATTERN = "*.html"
    FILENAME_REGEX = r"(\d{4})_(\d{6})_en\.html"  # Matches YYYY_NNNNNN_en.html
    TIMESTAMP_DIR_REGEX = (
        r"\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}"  # Matches scraper timestamp dirs
    )


# URL Configuration
class URLConfig:
    """URL templates and base URLs."""

    BASE_URL = "https://citizens-initiative.europa.eu"
    INITIATIVE_DETAILS_URL_TEMPLATE = (
        "{base_url}/initiatives/details/{year}/{number}_en"
    )


# CSV Configuration
class CSVConfig:
    """CSV output configuration."""

    OUTPUT_FILENAME_TEMPLATE = "eci_initiatives_{timestamp}.csv"


# Logging Configuration
class LoggingConfig:
    """Logging settings and format strings."""

    LOGGER_NAME = "eci_initiatives_extractor"
    LOG_FILENAME_TEMPLATE = "extractor_initiatives_{timestamp}.log"
    FORMAT_CONSOLE = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    FORMAT_FILE = (
        "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
    )


# Content Extraction Limits
OBJECTIVE_MAX_LENGTH = 1100  # Maximum characters for objective field
