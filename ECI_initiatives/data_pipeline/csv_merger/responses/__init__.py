"""
CSV Merger for ECI Responses and Follow-up Data

This package merges `eci_responses_*.csv` with `eci_responses_followup_website_*.csv`
from the latest timestamped data directory.

Usage:
    python -m ECI_initiatives.csv_merger.responses

Or programmatically:
    from ECI_initiatives.csv_merger.responses import ResponsesAndFollowupMerger

    merger = ResponsesAndFollowupMerger()
    merger.merge()
"""

from .merger import ResponsesAndFollowupMerger
from .exceptions import (
    MergerError,
    DataDirectoryNotFoundError,
    NoTimestampDirectoryError,
    MissingInputFileError,
    EmptyDataError,
    FollowupRowCountExceedsBaseError,
    RegistrationNumberMismatchError,
    MissingColumnsError,
)
from .strategies import merge_field_values
from .cli import main

__all__ = [
    "ResponsesAndFollowupMerger",
    "MergerError",
    "DataDirectoryNotFoundError",
    "NoTimestampDirectoryError",
    "MissingInputFileError",
    "EmptyDataError",
    "FollowupRowCountExceedsBaseError",
    "RegistrationNumberMismatchError",
    "MissingColumnsError",
    "merge_field_values",
    "main",
]
