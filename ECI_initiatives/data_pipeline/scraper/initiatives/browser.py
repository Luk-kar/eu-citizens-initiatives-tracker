# Browser initialization and management
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Local
from .consts import CHROME_OPTIONS, LOG_MESSAGES
from .scraper_logger import logger


def initialize_browser() -> webdriver.Chrome:
    """Initialize Chrome WebDriver with headless options."""

    chrome_options = Options()
    for option in CHROME_OPTIONS:
        chrome_options.add_argument(option)

    logger.info(LOG_MESSAGES["browser_init"])
    driver = webdriver.Chrome(options=chrome_options)
    logger.debug(LOG_MESSAGES["browser_success"])

    return driver
