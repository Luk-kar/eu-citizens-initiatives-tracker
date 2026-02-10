"""
Shared constants and configuration for all ECI scrapers.

Contains browser settings, validation rules, rate limiting detection,
and other configuration values common to all scraper modules (initiatives, responses,
responses_followup_website).
"""

from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.parent.parent.parent.absolute()

# Base URL
BASE_URL = "https://citizens-initiative.europa.eu"

# Directory Structure (shared directory names)
DATA_DIR_NAME = "data"
LOG_DIR_NAME = "logs"

# Browser Configuration
CHROME_OPTIONS = [
    "--headless",
    "--no-sandbox",
    "--disable-dev-shm-usage",
]

# Timing Configuration (in seconds)
WAIT_DYNAMIC_CONTENT = (1.5, 1.9)  # Time to wait for JavaScript content to load

# Timeout Configuration (in seconds)
WEBDRIVER_TIMEOUT_DEFAULT = 30  # Default timeout for page loads
WEBDRIVER_TIMEOUT_CONTENT = 15  # Timeout for waiting for specific content elements

# HTML Validation
MIN_HTML_LENGTH = 50  # Minimum acceptable length for HTML content (characters)

# Rate Limiting Detection
RATE_LIMIT_INDICATORS = [
    "Server inaccessibility",
    "429 - Too Many Requests",
    # "429", # To avoid false positive (e.g., press release URLs)
    "HTTP 429",
    "Too Many Requests",
    "Rate limited",
]
