"""
Constants and configuration for the Commission responses scraper.

Module-specific settings for scraping Commission response pages.
Common settings are imported from scraper.shared.const.
"""

from pathlib import Path

from ..consts import SCRIPT_DIR, DirectoryStructure, HTMLParsingConfig, FilePatterns

# Directory names
DATA_DIR_NAME = DirectoryStructure.DATA_DIR_NAME
LOG_DIR_NAME = DirectoryStructure.LOG_DIR_NAME

# HTML validation
MIN_HTML_LENGTH = HTMLParsingConfig.MIN_HTML_LENGTH

# ============================================================================
# Module-specific constants
# ============================================================================

# Module-specific Directory Names
RESPONSES_DIR_NAME = DirectoryStructure.RESPONSES_DIR_NAME
INITIATIVE_PAGES_DIR_NAME = DirectoryStructure.INITIATIVES_DIR_NAME

# CSV Configuration
CSV_FILENAME = "responses_list.csv"
CSV_FIELDNAMES = ["url_find_initiative", "registration_number", "title", "datetime"]

# Module-specific File Naming Patterns
RESPONSE_PAGE_FILENAME_PATTERN = "{year}_{number}_en.html"
