"""Common configuration and constants for all ECI initiative tests."""

# python
import os

from ..scraper.initiatives.consts import (
    BASE_URL,
    ROUTE_FIND_INITIATIVE,
    CSV_FILENAME,
    CSV_FIELDNAMES,
    DATA_DIR_NAME,
    LISTINGS_DIR_NAME,
    PAGES_DIR_NAME,
    LOG_DIR_NAME,
    LOG_MESSAGES,
    WEBDRIVER_TIMEOUT_DEFAULT as DEFAULT_WEBDRIVER_TIMEOUT,
    WEBDRIVER_TIMEOUT_CONTENT as PAGE_CONTENT_TIMEOUT,
    LISTING_PAGE_FILENAME_PATTERN,
    INITIATIVE_PAGE_FILENAME_PATTERN,
    RATE_LIMIT_INDICATORS as MAIN_RATE_LIMIT_INDICATORS,
)

# ===============================
#       SCRAPER INITIATIVES
# ===============================

# ===== PATH CONFIGURATIONS =====

# Base paths relative to test files
TEST_BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # ECI_initiatives/tests/
PROGRAM_DIR = os.path.join(TEST_BASE_DIR, "..")  # ECI_initiatives/

# Test data directories
TEST_DATA_DIR = os.path.join(TEST_BASE_DIR, "data", "example_htmls")
INITIATIVES_HTML_DIR = os.path.join(TEST_DATA_DIR, "initiatives")
LISTINGS_HTML_DIR = os.path.join(TEST_DATA_DIR, "listings")

# Reference files
CSV_FILE_PATH = os.path.join(LISTINGS_HTML_DIR, CSV_FILENAME)

# ===== URL CONFIGURATIONS =====

# Base URL for ECI website
FULL_FIND_INITIATIVE_URL = BASE_URL + ROUTE_FIND_INITIATIVE

# ===== TEST DATA CONFIGURATIONS =====

# Sample HTML files for testing
SAMPLE_LISTING_FILES = ["first_page.html", "last_page.html"]


# CSV columns expected in output
class REQUIRED_CSV_COLUMNS:

    URL = CSV_FIELDNAMES[0]  # "url"
    CURRENT_STATUS = CSV_FIELDNAMES[1]  # "current_status"
    REGISTRATION_NUMBER = CSV_FIELDNAMES[2]  # "registration_number"
    SIGNATURE_COLLECTION = CSV_FIELDNAMES[3]  # "signature_collection"
    DATETIME = CSV_FIELDNAMES[4]  # "datetime"


# ===== TEST LIMITS AND CONSTRAINTS =====

# Limits for end-to-end tests to avoid server overload
MAX_PAGES_E2E_TEST = 1  # Only scrape first page
MAX_INITIATIVES_E2E_TEST = 3  # Only download first 3 initiatives

# ===== EXPECTED FILE PATTERNS =====

# File naming patterns
LISTING_HTML_PATTERN = "Find_initiative_European_Citizens_Initiative_page_"
INITIATIVE_HTML_PATTERN = r"\d{4}_\d+\.html"

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
    SERVER_INACCESSIBILITY = MAIN_RATE_LIMIT_INDICATORS[0]  # "Server inaccessibility"
    TOO_MANY_REQUESTS = MAIN_RATE_LIMIT_INDICATORS[1]  # "429 - Too Many Requests"
    RATE_LIMITED = MAIN_RATE_LIMIT_INDICATORS[4]  # "Rate limited"


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

# ===============================
#       EXTRACTOR INITIATIVES
# ===============================

REQUIRED_EXTRACTOR_CSV_COLUMNS = [
    'registration_number',
    'title',
    'objective',
    'annex',
    'current_status',
    'url',
    'timeline_registered',
    'timeline_collection_start_date',
    'timeline_collection_closed',
    'timeline_verification_start',
    'timeline_verification_end',
    'timeline_response_commission_date',
    'timeline',
    'organizer_representative',
    'organizer_entity',
    'organizer_others',
    'funding_total',
    'funding_by',
    'signatures_collected',
    'signatures_collected_by_country',
    'signatures_threshold_met',
    'response_commission_url',
    'final_outcome',
    'languages_available',
    'created_timestamp',
    'last_updated'
]

# ===============================
#       SCRAPER RESPONSES
# ===============================

# Directory names
RESPONSES_DIR_NAME = "responses"

# CSV configuration
RESPONSES_CSV_FILENAME = "responses_list.csv"
RESPONSES_CSV_FIELDNAMES = [
    "url_find_initiative",
    "registration_number", 
    "title",
    "datetime"
]

# Test limits
MAX_RESPONSE_DOWNLOADS_E2E_TEST = 3  # Only download first 3 responses

# File naming patterns
RESPONSE_PAGE_FILENAME_PATTERN = r"\d{4}_\d+_en\.html"

# ===============================
#       EXTRACTOR RESPONSES
# ===============================

REQUIRED_RESPONSES_CSV_COLUMNS = [
    'response_url',
    'initiative_url',
    'initiative_title',
    'registration_number',
    'commission_submission_date',
    'submission_news_url',
    'commission_meeting_date',
    'commission_officials_met',
    'parliament_hearing_date',
    'parliament_hearing_recording_url',
    'plenary_debate_date',
    'plenary_debate_recording_url',
    'commission_communication_date',
    'commission_communication_url',
    'communication_main_conclusion',
    'legislative_proposal_status',
    'commission_response_summary',
    'has_followup_section',
    'followup_meeting_date',
    'followup_meeting_officials',
    'roadmap_launched',
    'roadmap_description',
    'roadmap_completion_target',
    'workshop_conference_dates',
    'partnership_programs',
    'court_cases_referenced',
    'court_judgment_dates',
    'court_judgment_summary',
    'latest_update_date',
    'factsheet_url',
    'video_recording_count',
    'dedicated_website',
    'related_eu_legislation',
    'petition_platforms_used',
    'follow_up_duration_months',
    'created_timestamp',
    'last_updated'
]
