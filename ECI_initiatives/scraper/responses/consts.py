"""
Constants and configuration for Commission responses scraper.
"""
import datetime
import os
from pathlib import Path

# Timing - start of scraping session
START_SCRAPING = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

# URLs and Routes
BASE_URL = "https://citizens-initiative.europa.eu"

# Directory Structure
DATA_DIR_NAME = "data"
LOG_DIR_NAME = "logs"
RESPONSES_DIR_NAME = "responses"
INITIATIVE_PAGES_DIR_NAME = "initiative_pages"

# Script directory (3 levels up from this file: responses -> scraper -> ECI_initiatives)
SCRIPT_DIR = Path(__file__).parent.parent.parent.absolute()

# Output directories
LOG_DIR = os.path.join(SCRIPT_DIR, DATA_DIR_NAME, START_SCRAPING, LOG_DIR_NAME)
RESPONSES_DIR = os.path.join(SCRIPT_DIR, DATA_DIR_NAME, START_SCRAPING, RESPONSES_DIR_NAME)

# Timing Configuration (in seconds)
WAIT_DYNAMIC_CONTENT = (1.5, 1.9)
WAIT_BETWEEN_DOWNLOADS = (0.5, 1.5)
RETRY_WAIT_BASE = (1.0, 1.2)

# Timeout Configuration (in seconds)
WEBDRIVER_TIMEOUT_DEFAULT = 30
WEBDRIVER_TIMEOUT_CONTENT = 15

# Browser Configuration
CHROME_OPTIONS = [
    "--headless",
    "--no-sandbox",
    "--disable-dev-shm-usage"
]

# File Naming Patterns
RESPONSE_PAGE_FILENAME_PATTERN = "{year}/{number}_en.html"

# Retry and validation
DEFAULT_MAX_RETRIES = 5
MIN_HTML_LENGTH = 50

# Rate limiting indicators
RATE_LIMIT_INDICATORS = [
    "Server inaccessibility",
    "429 - Too Many Requests",
    "429",
    "Too Many Requests",
    "Rate limited"
]

# Log messages
LOG_MESSAGES = {
    # Scraping lifecycle
    "scraping_start": "Starting Commission responses scraping at {timestamp}",
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
    "divider_line": "=" * 60
}
