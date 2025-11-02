"""Base extractor class with shared utilities"""

import logging
from typing import Optional


class BaseExtractor:
    """Base class for all extractors with common utilities"""

    def __init__(self, logger: logging.Logger, registration_number: Optional[str] = None):
        self.logger = logger
        self.registration_number = registration_number

    def set_registration_number(self, registration_number: str):
        """Update registration number for error reporting"""
        self.registration_number = registration_number
