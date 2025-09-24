"""Common configuration and constants for all ECI initiative tests."""

import os

# ===== PATH CONFIGURATIONS =====

# Base paths relative to test files
TEST_BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # ECI_initiatives/tests/
PROGRAM_DIR = os.path.join(TEST_BASE_DIR, "..")  # ECI_initiatives/

# Test data directories
TEST_DATA_DIR = os.path.join(TEST_BASE_DIR, "data", "example_htmls")
INITIATIVES_HTML_DIR = os.path.join(TEST_DATA_DIR, "initiatives")
LISTINGS_HTML_DIR = os.path.join(TEST_DATA_DIR, "listings")

# Reference files
CSV_FILE_PATH = os.path.join(LISTINGS_HTML_DIR, "initiatives_list.csv")

# ===== URL CONFIGURATIONS =====

# Base URL for ECI website
BASE_URL = "https://citizens-initiative.europa.eu"
ROUTE_FIND_INITIATIVE = "/find-initiative_en"
FULL_FIND_INITIATIVE_URL = BASE_URL + ROUTE_FIND_INITIATIVE

# ===== TEST DATA CONFIGURATIONS =====

# Sample HTML files for testing
SAMPLE_LISTING_FILES = ["first_page.html", "last_page.html"]


# CSV columns expected in output
class REQUIRED_CSV_COLUMNS:

    URL = "url"
    CURRENT_STATUS = "current_status"
    REGISTRATION_NUMBER = "registration_number"
    SIGNATURE_COLLECTION = "signature_collection"
    DATETIME = "datetime"


# ===== TEST LIMITS AND CONSTRAINTS =====

# Limits for end-to-end tests to avoid server overload
MAX_PAGES_E2E_TEST = 1  # Only scrape first page
MAX_INITIATIVES_E2E_TEST = 3  # Only download first 3 initiatives

# Timeout values for tests
DEFAULT_WEBDRIVER_TIMEOUT = 30
PAGE_CONTENT_TIMEOUT = 15

# ===== EXPECTED FILE PATTERNS =====

# File naming patterns
LISTING_HTML_PATTERN = "Find_initiative_European_Citizens_Initiative_page_"
INITIATIVE_HTML_PATTERN = r"\d{4}_\d+\.html"
CSV_FILENAME = "initiatives_list.csv"

# Directory names
DATA_DIR_NAME = "data"
LISTINGS_DIR_NAME = "listings"
PAGES_DIR_NAME = "initiative_pages"
LOG_DIR_NAME = "logs"

# ===== MOCK RESPONSES FOR TESTING =====

# Sample initiative data for mocking
SAMPLE_INITIATIVE_DATA = {
    REQUIRED_CSV_COLUMNS.URL: "https://citizens-initiative.europa.eu/initiatives/details/2019/000007_en",
    REQUIRED_CSV_COLUMNS.CURRENT_STATUS: "Answered initiative",
    REQUIRED_CSV_COLUMNS.REGISTRATION_NUMBER: "ECI(2019)000007",
    REQUIRED_CSV_COLUMNS.SIGNATURE_COLLECTION: "Collection completed",
    REQUIRED_CSV_COLUMNS.DATETIME: "",
}


# Rate limiting patterns to detect
class RATE_LIMIT_INDICATORS:
    SERVER_INACCESSIBILITY = "Server inaccessibility"
    TOO_MANY_REQUESTS = "429 - Too Many Requests"
    RATE_LIMITED = "429 - Rate limited"


# ===== STATUS CATEGORIES =====

# Common ECI initiative statuses
COMMON_STATUSES = [
    "Answered initiative",
    "Unsuccessful collection",
    "Withdrawn",
    "Registered",
    "Collection ongoing",
    "Verification",
    "Valid initiative",
    "Collection closed",
]
