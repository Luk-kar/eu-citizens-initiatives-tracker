"""
Shared constants and configuration for ECI initiatives extractor.

Contains directory paths, file patterns, URL construction, and other
configuration values used across the extractor modules.
"""

from pathlib import Path

from ..consts import (
    SCRIPT_DIR,
    DirectoryStructure,
    FilePatterns,
    URLConfig,
    LoggingConfig,
    ContentLimits,
)


# CSV Configuration
class CSVConfig:
    """CSV output configuration."""

    OUTPUT_FILENAME_TEMPLATE = "eci_initiatives_{timestamp}.csv"


# Logging Configuration
class LoggingConfig:
    """Logging settings and format strings."""

    LOGGER_NAME = "eci_initiatives_extractor"
    LOG_FILENAME_TEMPLATE = "extractor_initiatives_{timestamp}.log"
    FORMAT_CONSOLE = LoggingConfig.FORMAT_CONSOLE
    FORMAT_FILE = LoggingConfig.FORMAT_DETAILED


# Content Extraction Limits
OBJECTIVE_MAX_LENGTH = (
    ContentLimits.OBJECTIVE_MAX_LENGTH
)  # Maximum characters for objective field
