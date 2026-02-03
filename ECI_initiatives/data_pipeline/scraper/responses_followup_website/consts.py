"""
Constants and configuration for the responses followup website scraper.

Module-specific settings for scraping dedicated followup website pages.
Common settings are imported from scraper_shared.const.

Note on Fine-Tuning:
    The timing configurations (WAIT_BETWEEN_DOWNLOADS, RETRY_WAIT_BASE) and retry
    limits (DEFAULT_MAX_RETRIES) can be adjusted based on:
    - Server load and response times
    - Rate limiting policies of the target website
    - Network conditions and infrastructure changes
    - Other development teams' usage patterns

    If you experience frequent rate limiting or timeouts, consider increasing
    wait times and retry intervals. For faster, more stable servers, you may
    reduce these values to speed up scraping.
"""

from pathlib import Path

# Import shared constants
from ..scraper_shared.const import (
    BASE_URL,
    SCRIPT_DIR,
    DATA_DIR_NAME,
    LOG_DIR_NAME,
    CHROME_OPTIONS,
    WAIT_DYNAMIC_CONTENT,
    WEBDRIVER_TIMEOUT_DEFAULT,
    WEBDRIVER_TIMEOUT_CONTENT,
    MIN_HTML_LENGTH,
    RATE_LIMIT_INDICATORS,
)

# Directory Structure
RESPONSES_FOLLOWUP_WEBSITE_DIR_NAME = "responses_followup_website"

# Module-specific Directory Names
FOLLOWUP_WEBSITE_DIR_NAME = "responses_followup_website"
RESPONSES_DIR_NAME = "responses"

# CSV Configuration
ECI_RESPONSES_CSV_PATTERN = "eci_responses_*.csv"
FOLLOWUP_WEBSITE_COLUMN = "followup_dedicated_website"
REGISTRATION_NUMBER_COLUMN = "registration_number"
CSV_FILENAME = "responses_list.csv"  # Read from responses scraper output
CSV_FIELDNAME_FOLLOWUP_URL = "followup_dedicated_website"

# Module-specific Timing Configuration (in seconds)
# Fine-tune these based on server response times and rate limiting behavior
WAIT_BETWEEN_DOWNLOADS = (1.5, 2.0)  # Delay between downloading followup pages
RETRY_WAIT_BASE = (2.0, 3.0)  # Base time for retry exponential backoff

# Module-specific File Naming Patterns
FOLLOWUP_PAGE_FILENAME_PATTERN = "{year}/{reg_number}_en.html"

# Retry Configuration
# Adjust based on network stability and server reliability
DEFAULT_MAX_RETRIES = 3

# Error Page Detection (in addition to shared RATE_LIMIT_INDICATORS)
# These multilingual error messages indicate server issues
ERROR_PAGE_INDICATORS = [
    "We apologise for any inconvenience",
    "Veuillez nous excuser pour ce désagrément",
    "Ci scusiamo per il disagio arrecato",
]

# Log Messages (followup-website-specific)
LOG_MESSAGES = {
    # Scraping lifecycle
    "scraping_start": "Starting followup website scraping at {timestamp} directory",
    "scraping_complete": "FOLLOWUP WEBSITE SCRAPING FINISHED!",
    # Browser
    "browser_init": "Initializing browser...",
    "browser_success": "Browser initialized successfully",
    "browser_closed": "Browser closed",
    # CSV reading
    "csv_found": "Found CSV file: {csv_path}",
    "urls_extracted": "Extracted {count} followup website URLs",
    "no_urls_found": "No followup website URLs found",
    # Download
    "download_start": "Downloading {reg_number} from {url}",
    "download_success": "Successfully downloaded {filename}",
    "download_failed": "Failed to download {url}",
    "rate_limit_retry": "Received rate limiting. Retrying ({retry}/{max_retries}) in {wait_time:.1f} seconds...",
    # Summary
    "completion_timestamp": "Scraping completed at {timestamp}",
    "start_time": "Start time: {start_scraping}",
    "total_urls_found": "Total followup website URLs found: {count}",
    "pages_downloaded": "Pages downloaded: {downloaded_count}/{total_count}",
    "failed_downloads": "Failed downloads: {failed_count}",
    "failed_url": "  - {failed_url}",
    "all_downloads_successful": "All downloads successful!",
    "files_saved_in": "Files saved in: {path}",
    "divider_line": "=" * 60,
}
