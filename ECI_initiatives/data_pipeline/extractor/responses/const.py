"""
Constants and configuration for the Commission responses scraper.

Module-specific settings for scraping Commission response pages.
Common settings are imported from scraper.shared.const.
"""

from pathlib import Path

from ..consts import SCRIPT_DIR, DirectoryStructure, FilePatterns

# ============================================================================
# Module-specific constants
# ============================================================================

# CSV Configuration
CSV_FILENAME = "responses_list.csv"
CSV_FIELDNAMES = ["url_find_initiative", "registration_number", "title", "datetime"]

# Module-specific File Naming Patterns
RESPONSE_PAGE_FILENAME_PATTERN = "{year}_{number}_en.html"
