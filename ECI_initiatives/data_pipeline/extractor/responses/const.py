"""
Constants and configuration for the Commission responses scraper.

Module-specific settings for scraping Commission response pages.
Common settings are imported from scraper.shared.const.
"""

from pathlib import Path

# ============================================================================
# Shared constants (from scraper.shared.const)
# ============================================================================

# Base URL for EU Citizens' Initiative website
BASE_URL = "https://citizens-initiative.europa.eu"

# Script directory (project root detection)
SCRIPT_DIR = Path(__file__).resolve().parent.parent.parent.parent

# Directory names
DATA_DIR_NAME = "data"
LOG_DIR_NAME = "logs"

# HTML validation
MIN_HTML_LENGTH = 1000  # Minimum acceptable HTML length

# ============================================================================
# Module-specific constants
# ============================================================================

# Module-specific Directory Names
RESPONSES_DIR_NAME = "responses"
INITIATIVE_PAGES_DIR_NAME = "initiatives"

# CSV Configuration
CSV_FILENAME = "responses_list.csv"
CSV_FIELDNAMES = ["url_find_initiative", "registration_number", "title", "datetime"]

# Module-specific File Naming Patterns
RESPONSE_PAGE_FILENAME_PATTERN = "{year}_{number}_en.html"


# File Patterns
class FilePatterns:
    """File naming patterns and regex for matching files."""

    HTML_FILE_PATTERN = "*.html"
    FILENAME_REGEX = r"(\d{4})_(\d{6})_en\.html"  # Matches YYYY_NNNNNN_en.html
    TIMESTAMP_DIR_REGEX = (
        r"\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}"  # Matches scraper timestamp dirs
    )
