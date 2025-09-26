# Python Standard Library
import random
import time
from typing import Dict, Tuple

# Third-party
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# Local
from .browser import initialize_browser
from .file_ops import save_listing_page
from .data_parser import parse_initiatives_list_data
from .css_selectors import ECIlistingSelectors
from .consts import (
    ROUTE_FIND_INITIATIVE,
    WAIT_DYNAMIC_CONTENT,
    WAIT_BETWEEN_PAGES,
    WEBDRIVER_TIMEOUT_DEFAULT,
    LOG_MESSAGES,
)
from .logger import logger


def scrape_all_initiatives_on_all_pages(
    driver: webdriver.Chrome, base_url: str, list_dir: str
) -> Tuple[list, list]:
    """Scrape all pages of initiatives on the listings by iterating through pagination.

    Args:
        driver: Chrome WebDriver instance
        base_url: Base URL of the site
        list_dir: Directory to save page HTML files

    Returns:
        Tuple containing:
        - List of all initiative data from all pages
        - List of paths to saved HTML files
    """
    url_find_initiative = base_url + ROUTE_FIND_INITIATIVE
    all_initiative_pages = []
    saved_page_paths = []
    current_page = 1

    logger.info(f"Starting pagination scraping from: {url_find_initiative}")

    # Load the first page
    logger.info(f"Loading page {current_page}: {url_find_initiative}")
    driver.get(url_find_initiative)

    while True:

        # Scrape current page
        page_initiative_data, page_path = scrape_single_listing_page(
            driver, base_url, list_dir, current_page
        )

        # Add to accumulated data
        all_initiative_pages.extend(page_initiative_data)
        saved_page_paths.append(page_path)

        # Try to navigate to next page
        if navigate_to_next_page(driver, current_page):
            current_page += 1
        else:
            break

    logger.info(
        f"Completed scraping {current_page} pages with total of "
        f"{len(all_initiative_pages)} initiatives"
    )
    return all_initiative_pages, saved_page_paths


def scrape_single_listing_page(
    driver: webdriver.Chrome, base_url: str, list_dir: str, current_page: int
) -> Tuple[list, str]:
    """Scrape a single listing page and return initiative data and saved page path."""

    # Wait for page elements to load
    wait_for_listing_page_content(driver, current_page)

    # Save page source
    page_source, page_path = save_listing_page(driver, list_dir, current_page)

    # Parse initiatives from current page
    page_initiative_data = parse_initiatives_list_data(page_source, base_url)

    return page_initiative_data, page_path


def wait_for_listing_page_content(driver: webdriver.Chrome, current_page: int) -> None:
    """Wait for listing page elements to load."""

    wait = WebDriverWait(driver, WEBDRIVER_TIMEOUT_DEFAULT)
    try:
        cards_initiative_selector = ECIlistingSelectors.INITIATIVE_CARDS
        wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, cards_initiative_selector))
        )
        logger.info(LOG_MESSAGES["page_loaded"].format(page=current_page))
    except Exception as e:
        logger.warning(
            f"No initiatives found or timeout on page {current_page}: "
            f"{e} - continuing with current content"
        )


def navigate_to_next_page(driver: webdriver.Chrome, current_page: int) -> bool:
    """Check for next button and navigate to next page.

    Returns:
        bool: True if successfully navigated to next page, False if no more pages
    """
    next_button_selector = ECIlistingSelectors.NEXT_BUTTON

    try:

        next_button = driver.find_element(By.CSS_SELECTOR, next_button_selector)
        logger.info(
            LOG_MESSAGES["next_button_found"].format(
                page=current_page, next_page=current_page + 1
            )
        )
        # Click the next button
        driver.execute_script("arguments[0].click();", next_button)
        # Wait a bit for the page to start loading
        time.sleep(random.uniform(*WAIT_BETWEEN_PAGES))
        return True

    except Exception:
        logger.info(LOG_MESSAGES["last_page"].format(page=current_page))
        return False


def scrape_initiatives_page(
    driver: webdriver.Chrome, base_url: str, list_dir: str
) -> Tuple[str, str]:
    """Load page, wait for elements, and save HTML source."""

    url_find_initiative = base_url + ROUTE_FIND_INITIATIVE

    logger.info(f"Loading page: {url_find_initiative}")
    driver.get(url_find_initiative)

    wait = WebDriverWait(driver, WEBDRIVER_TIMEOUT_DEFAULT)

    try:
        cards_initiative_selector = ECIlistingSelectors.INITIATIVE_CARDS
        wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, cards_initiative_selector))
        )

        pagination_for_other_cards = ECIlistingSelectors.PAGINATION_LINKS
        wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, pagination_for_other_cards)
            )
        )
        logger.info("Initiatives loaded successfully")
    except Exception as e:
        logger.warning(
            f"No initiatives found or timeout: {e} - continuing with current content"
        )

    # Additional wait to ensure all dynamic content is loaded
    random_time = random.uniform(*WAIT_DYNAMIC_CONTENT)
    logger.debug(f"Waiting {random_time:.1f}s for dynamic content...")
    time.sleep(random_time)

    page_source = driver.page_source
    main_page_path = os.path.join(list_dir, LISTING_PAGE_MAIN_FILENAME)

    with open(main_page_path, "w", encoding="utf-8") as f:
        pretty_html = BeautifulSoup(page_source, "html.parser").prettify()
        f.write(pretty_html)

    logger.info(f"Main page saved to: {main_page_path}")
    return page_source, main_page_path
