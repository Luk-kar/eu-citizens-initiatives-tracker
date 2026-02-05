"""
Constants and configuration for the Commission responses scraper.

Module-specific settings for scraping Commission response pages.
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

# Module-specific Directory Names
RESPONSES_DIR_NAME = "responses"
INITIATIVE_PAGES_DIR_NAME = "initiatives"

# CSV Configuration
CSV_FILENAME = "responses_list.csv"
CSV_FIELDNAMES = [
    "url_find_initiative",
    "registration_number",
    "title",
    "datetime",
]

# Module-specific Timing Configuration (in seconds)
# Fine-tune these based on server response times and rate limiting behavior
WAIT_BETWEEN_DOWNLOADS = (1.5, 1.9)  # Delay between downloading response pages
RETRY_WAIT_BASE = (2.0, 2.5)  # Base time for retry exponential backoff

# Module-specific File Naming Patterns
RESPONSE_PAGE_FILENAME_PATTERN = "{year}/{number}_en.html"

# Retry Configuration
# Adjust based on network stability and server reliability
DEFAULT_MAX_RETRIES = 5

# Log Messages (responses-specific)
LOG_MESSAGES = {
    # Scraping lifecycle
    "scraping_start": "Starting Commission responses scraping at {timestamp} directory",
    "scraping_complete": "COMMISSION RESPONSES SCRAPING FINISHED!",
    # Browser
    "browser_init": "Initializing browser...",
    "browser_success": "Browser initialized successfully",
    "browser_closed": "Browser closed",
    # Link extraction
    "links_found": "Found {count} Commission response links",
    "no_links_found": "No Commission response links found",
    # Download
    "download_success": "Successfully downloaded {filename}",
    "download_failed": "Failed to download {url}",
    "rate_limit_retry": "Received rate limiting. Retrying ({retry}/{max_retries}) in {wait_time:.1f} seconds...",
    # Summary
    "completion_timestamp": "Scraping completed at {timestamp}",
    "start_time": "Start time: {start_scraping}",
    "total_links_found": "Total response links found: {count}",
    "pages_downloaded": "Pages downloaded: {downloaded_count}/{total_count}",
    "failed_downloads": "Failed downloads: {failed_count}",
    "failed_url": "  - {failed_url}",
    "all_downloads_successful": "All downloads successful!",
    "files_saved_in": "Files saved in: {path}",
    "divider_line": "=" * 60,
}
