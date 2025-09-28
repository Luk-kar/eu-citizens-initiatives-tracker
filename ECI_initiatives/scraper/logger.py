# python
import logging
import os
import datetime

# scraper
from .consts import LOG_DIR

class ScraperLogger:
    """
    Logger class for ECI scraper with file and console output.
    (Singleton) - ensures only one logger instance exists across the application.
    """
    _instance = None
    _initialized = False

    def __new__(cls, log_dir: str = None):
        if cls._instance is None:
            cls._instance = super(ScraperLogger, cls).__new__(cls)
        return cls._instance

    def __init__(self, log_dir: str = None):
        # Prevent re-initialization of singleton
        if ScraperLogger._initialized:
            return
            
        self.logger = logging.getLogger("ECIScraper")
        self.logger.setLevel(logging.DEBUG)
        self.log_dir = log_dir or LOG_DIR

        # Clear existing handlers to avoid duplicates
        if self.logger.hasHandlers():
            self.logger.handlers.clear()

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        os.makedirs(self.log_dir, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_file = os.path.join(self.log_dir, f"scraper_{timestamp}.log")

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)

        # File formatter (more detailed)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)

        # Console formatter (simpler)
        console_formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # Mark as initialized
        ScraperLogger._initialized = True

    def debug(self, message: str):
        self.logger.debug(message)

    def info(self, message: str):
        self.logger.info(message)

    def warning(self, message: str):
        self.logger.warning(message)

    def error(self, message: str):
        self.logger.error(message)

    def critical(self, message: str):
        self.logger.critical(message)

logger = ScraperLogger(LOG_DIR)