"""
Custom exceptions for the CSV merger.
"""


class MergerError(Exception):
    """Base exception for merger errors."""

    pass


class DataDirectoryNotFoundError(MergerError):
    """Raised when the base data directory does not exist."""

    pass


class NoTimestampDirectoryError(MergerError):
    """Raised when no timestamp subdirectory is found under data."""

    pass


class MissingInputFileError(MergerError):
    """Raised when a required input CSV file is not found."""

    pass


class EmptyDataError(MergerError):
    """Raised when a CSV file has no data rows (header-only)."""

    pass


class FollowupRowCountExceedsBaseError(MergerError):
    """Raised when followup CSV has more rows than base CSV."""

    pass


class RegistrationNumberMismatchError(MergerError):
    """Raised when followup CSV contains registration_number not in base CSV."""

    pass


class MissingColumnsError(MergerError):
    """Raised when followup CSV is missing columns that exist in base CSV."""

    pass


class ImmutableFieldConflictError(MergerError):
    """Raised when an immutable field has different values in base and followup datasets."""

    pass
