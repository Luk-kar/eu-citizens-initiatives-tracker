"""
Constants and configuration for followup website scraper.
"""

from pathlib import Path

# Directory Structure
DATA_DIR_NAME = "data"
LOG_DIR_NAME = "logs"
RESPONSES_FOLLOWUP_WEBSITE_DIR_NAME = "responses_followup_website"

# Script directory (3 levels up from this file)
SCRIPT_DIR = Path(__file__).parent.parent.parent.absolute()

# CSV Configuration
ECI_RESPONSES_CSV_PATTERN = "eci_responses_*.csv"
FOLLOWUP_WEBSITE_COLUMN = "followup_dedicated_website"
REGISTRATION_NUMBER_COLUMN = "registration_number"

# Timing Configuration (in seconds)
WAIT_DYNAMIC_CONTENT = (1.5, 1.9)
WAIT_BETWEEN_DOWNLOADS = (1.5, 1.9)
RETRY_WAIT_BASE = (2.0, 2.5)

# Timeout Configuration (in seconds)
WEBDRIVER_TIMEOUT_DEFAULT = 30
WEBDRIVER_TIMEOUT_CONTENT = 15

# Browser Configuration
CHROME_OPTIONS = [
    "--headless",
    "--no-sandbox",
    "--disable-dev-shm-usage",
]

# File Naming Patterns
FOLLOWUP_WEBSITE_FILENAME_PATTERN = "{year}/{registration_number}_en.html"

# Retry and validation
DEFAULT_MAX_RETRIES = 3
MIN_HTML_LENGTH = 50

# Rate limiting indicators
RATE_LIMIT_INDICATORS = [
    "Server inaccessibility",
    "429 - Too Many Requests",
    "HTTP 429",
    "Too Many Requests",
    "Rate limited",
]

# Log messages
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
