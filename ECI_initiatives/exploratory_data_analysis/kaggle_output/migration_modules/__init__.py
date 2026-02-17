"""
Migration modules package for Kaggle notebook migration
"""

from .constants import (
    IMAGE_REPLACEMENTS,
    KAGGLE_SETUP_CODE,
    DATASET_METADATA_TEMPLATE,
    MIGRATION_REPORT_TEMPLATE,
    SUCCESS_LOG_MESSAGES,
    ProjectPaths,
    setup_project_paths,
    PROJECT_PATHS,  # New: pre-configured default paths
)
from .data_finder import DataFinder
from .notebook_processor import NotebookProcessor
from .report_generator import ReportGenerator

__all__ = [
    "IMAGE_REPLACEMENTS",
    "KAGGLE_SETUP_CODE",
    "DATASET_METADATA_TEMPLATE",
    "MIGRATION_REPORT_TEMPLATE",
    "SUCCESS_LOG_MESSAGES",
    "ProjectPaths",
    "setup_project_paths",
    "PROJECT_PATHS",  # New export
    "DataFinder",
    "NotebookProcessor",
    "ReportGenerator",
]
