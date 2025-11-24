"""
Logger implementation for followup website scraper.
"""

import logging
import os
import datetime


def initialize_logger(log_dir: str):
    """
    Initialize and return a logger instance with file and console handlers.

    Args:
        log_dir: Directory for log files

    Returns:
        Logger instance
    """
    # Create logger
    logger = logging.getLogger("ECIFollowupWebsiteScraper")
    logger.setLevel(logging.DEBUG)

    # Clear existing handlers to avoid duplicates
    if logger.hasHandlers():
        logger.handlers.clear()

    # Create log directory
    os.makedirs(log_dir, exist_ok=True)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file = os.path.join(log_dir, f"scraper_followup_website_{timestamp}.log")
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    logger.info(f"Log file created: {log_file}")

    return logger


# Global logger instance (will be initialized in __main__.py)
logger = None
