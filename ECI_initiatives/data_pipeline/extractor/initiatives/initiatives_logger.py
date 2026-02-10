"""

Unified Logger for ECI initiatives extractor

"""

# python

import logging

from pathlib import Path

from datetime import datetime

from typing import Optional

from .const import LoggingConfig


class InitiativesExtractorLogger:
    """Centralized logger for ECI initiatives data processing"""

    _instance = None

    _logger = None

    def __new__(cls):
        """Singleton pattern to ensure only one logger instance exists"""

        if cls._instance is None:

            cls._instance = super().__new__(cls)

        return cls._instance

    def __init__(self):
        """Initialize logger only once"""

        if self._logger is None:

            self._logger = logging.getLogger(LoggingConfig.LOGGER_NAME)

            self._logger.setLevel(logging.INFO)

            # Prevent duplicate handlers if __init__ is called multiple times

            self._logger.handlers = []

    def setup(self, log_dir: Optional[Path] = None) -> logging.Logger:
        """

        Configure logging with file and console handlers

        Args:

            log_dir: Directory for log files. If None, only console logging is used.

        Returns:

            Configured logger instance

        """

        # Clear existing handlers to prevent duplicates

        self._logger.handlers = []

        # Console handler (always active)

        console_handler = logging.StreamHandler()

        console_handler.setLevel(logging.INFO)

        console_formatter = logging.Formatter(LoggingConfig.FORMAT_CONSOLE)

        console_handler.setFormatter(console_formatter)

        self._logger.addHandler(console_handler)

        # File handler (optional, only if log_dir is provided)

        if log_dir:

            log_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

            log_filename = LoggingConfig.LOG_FILENAME_TEMPLATE.format(
                timestamp=timestamp
            )

            log_file = log_dir / log_filename

            file_handler = logging.FileHandler(log_file)

            file_handler.setLevel(logging.INFO)

            file_formatter = logging.Formatter(LoggingConfig.FORMAT_FILE)

            file_handler.setFormatter(file_formatter)

            self._logger.addHandler(file_handler)

        return self._logger

    def get_logger(self) -> logging.Logger:
        """Get the configured logger instance"""

        if self._logger is None:

            raise RuntimeError("Logger not initialized. Call setup() first.")

        return self._logger
