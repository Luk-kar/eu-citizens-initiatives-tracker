"""
Configuration constants for ECI (European Citizens' Initiative) scraper.
"""

# URLs and Routes
BASE_URL = "https://citizens-initiative.europa.eu"
ROUTE_FIND_INITIATIVE = "/find-initiative_en"

# Directory Structure
DATA_DIR_NAME = "data"
LOG_DIR_NAME = "logs"
LISTINGS_DIR_NAME = "listings"
PAGES_DIR_NAME = "initiative_pages"

# Timing Configuration (in seconds)
WAIT_DYNAMIC_CONTENT = (1.5, 1.9)
WAIT_BETWEEN_PAGES = (1.0, 2.0)
WAIT_BETWEEN_DOWNLOADS = (0.5, 1.5)
RETRY_WAIT_BASE = (1.0, 1.2)

# Timeout Configuration (in seconds)
WEBDRIVER_TIMEOUT_DEFAULT = 30
WEBDRIVER_TIMEOUT_CONTENT = 15

# Browser Configuration
CHROME_OPTIONS = ["--headless", "--no-sandbox", "--disable-dev-shm-usage"]

# File Naming Patterns
LISTING_PAGE_FILENAME_PATTERN = (
    "Find_initiative_European_Citizens_Initiative_page_{:03d}.html"
)
LISTING_PAGE_MAIN_FILENAME = "Find_initiative_European_Citizens_Initiative.html"
INITIATIVE_PAGE_FILENAME_PATTERN = "{year}_{number}.html"

CSV_FIELDNAMES = [
    "url",
    "current_status",
    "registration_number",
    "signature_collection",
    "datetime",
]
CSV_FILENAME = "initiatives_list.csv"

DEFAULT_MAX_RETRIES = 5

MIN_HTML_LENGTH = 50

RATE_LIMIT_INDICATORS = [
    "Server inaccessibility",
    "429 - Too Many Requests",
    "429",
    "Too Many Requests",
    "Rate limited",
]

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
    "scraping_complete": "🎉 SCRAPING FINISHED! 🎉",
}
