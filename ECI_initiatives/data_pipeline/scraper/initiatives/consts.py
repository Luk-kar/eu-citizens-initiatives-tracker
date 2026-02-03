"""
Constants and configuration for Commission initiatives scraper.

Module-specific settings for scraping the main ECI initiatives listings.
Common settings are imported from scraper_shared.const.py

Note on Fine-Tuning:
    The timing configurations (WAIT_BETWEEN_*, RETRY_WAIT_BASE) and retry limits
    (DEFAULT_MAX_RETRIES) can be adjusted based on:
    - Server load and response times
    - Rate limiting policies of the target website
    - Network conditions and infrastructure changes
    - Other development teams' usage patterns

    If you experience frequent rate limiting or timeouts, consider increasing
    wait times and retry intervals. For faster, more stable servers, you may
    reduce these values to speed up scraping.
"""

import datetime
import os
from pathlib import Path

from ..scraper_shared.const import (
    BASE_URL,
    DATA_DIR_NAME,
    LOG_DIR_NAME,
    CHROME_OPTIONS,
    WAIT_DYNAMIC_CONTENT,
    WEBDRIVER_TIMEOUT_DEFAULT,
    WEBDRIVER_TIMEOUT_CONTENT,
    MIN_HTML_LENGTH,
    RATE_LIMIT_INDICATORS,
    SCRIPT_DIR,
)

# Scraping timestamp (unique to initiatives scraper as it runs first)
START_SCRAPING = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

# Routes (initiatives-specific)
ROUTE_FIND_INITIATIVE = "/find-initiative_en"

# Module-specific Directory Names
LISTINGS_DIR_NAME = "listings"
PAGES_DIR_NAME = "initiatives"

# Log directory path
LOG_DIR = os.path.join(SCRIPT_DIR, DATA_DIR_NAME, START_SCRAPING, LOG_DIR_NAME)

# Module-specific Timing Configuration (in seconds)
# Fine-tune these based on server response times and rate limiting behavior
WAIT_BETWEEN_PAGES = (1.0, 2.0)  # Delay between pagination clicks
WAIT_BETWEEN_DOWNLOADS = (0.5, 1.5)  # Delay between downloading individual pages
RETRY_WAIT_BASE = (1.0, 1.2)  # Base time for retry exponential backoff

# Module-specific File Naming Patterns
LISTING_PAGE_FILENAME_PATTERN = (
    "Find_initiative_European_Citizens_Initiative_page_{:03d}.html"
)
LISTING_PAGE_MAIN_FILENAME = "Find_initiative_European_Citizens_Initiative.html"
INITIATIVE_PAGE_FILENAME_PATTERN = "{year}_{number}.html"

# CSV Configuration
CSV_FIELDNAMES = [
    "url",
    "current_status",
    "registration_number",
    "signature_collection",
    "datetime",
]
CSV_FILENAME = "initiatives_list.csv"

# Retry Configuration
# Adjust based on network stability and server reliability
DEFAULT_MAX_RETRIES = 5

# Log Messages (initiatives-specific)
LOG_MESSAGES = {
    "scraping_start": "Starting scraping at: {timestamp}",
    "browser_init": "Initializing browser...",
    "browser_success": "Browser initialized successfully",
    "browser_closed": "Browser closed",
    "page_loaded": "Initiatives loaded successfully on page {page}",
    "page_saved": "Page {page} saved to: {path}",
    "next_button_found": "Found 'Next' button on page {page}, navigating to page {next_page}",
    "last_page": "No 'Next' button found on page {page}. This appears to be the last page.",
    "download_success": "✅ Successfully downloaded: {filename}",
    "rate_limit_retry": "⚠️  Received rate limiting. Retrying {retry}/{max_retries} in {wait_time:.1f} seconds...",
    "pages_browser_closed": "Individual pages browser closed",
    "summary_scraping": {
        "scraping_complete": "🎉 SCRAPING FINISHED! 🎉",
        "completion_timestamp": "Scraping completed at: {timestamp}",
        "start_time": "Start time: {start_scraping}",
        "total_pages_scraped": "Total pages scraped: {page_count}",
        "total_initiatives_found": "Total initiatives found: {total_initiatives}",
        "initiatives_by_category": "Initiatives by category (current_status):",
        "registered_status": "- Registered: {count}",
        "collection_ongoing_status": "- Collection ongoing: {count}",
        "valid_initiative_status": "- Valid initiative: {count}",
        "pages_downloaded": "Pages downloaded: {downloaded_count}/{total_initiatives}",
        "failed_downloads": "Failed downloads: {failed_count}",
        "failed_url": " - {failed_url}",
        "all_downloads_successful": "✅ All downloads successful!",
        "files_saved_in": "Files saved in: initiatives/{start_scraping}",
        "main_page_sources": "Main page sources:",
        "page_source": "  Page {page_num}: {path}",
        "divider_line": "=" * 60,
    },
}
