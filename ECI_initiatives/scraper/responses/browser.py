"""
Browser initialization and management for Commission responses scraper.
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from .consts import CHROME_OPTIONS, LOG_MESSAGES
from .scraper_logger import logger


def initialize_browser() -> webdriver.Chrome:
    """
    Initialize Chrome WebDriver with headless options.

    Returns:
        webdriver.Chrome: Configured Chrome WebDriver instance
    """
    chrome_options = Options()

    # Add all configured options
    for option in CHROME_OPTIONS:
        chrome_options.add_argument(option)

    logger.info(LOG_MESSAGES["browser_init"])

    driver = webdriver.Chrome(options=chrome_options)

    logger.debug(LOG_MESSAGES["browser_success"])

    return driver
