"""
Custom exceptions for followup website scraper.
"""


class MissingDataDirectoryError(FileNotFoundError):
    """
    Raised when the required data directory structure is not found.

    This typically occurs when the followup website scraper is run before
    the ECI responses parser has created the necessary CSV file.
    """

    def __init__(self, expected_path: str, hint: str = None):
        """
        Initialize the exception with context.

        Args:
            expected_path: The path that was expected but not found
            hint: Optional suggestion for how to fix the issue
        """
        self.expected_path = expected_path
        self.hint = hint or "Run the ECI responses parser first to create the CSV file."

        message = (
            f"Cannot find required data directory or CSV file.\n"
            f"Expected: {expected_path}\n"
            f"Hint: {self.hint}"
        )

        super().__init__(message)


class MissingCSVFileError(FileNotFoundError):
    """
    Raised when the required eci_responses CSV file is not found.
    """

    def __init__(self, search_dir: str):
        """
        Initialize the exception with context.

        Args:
            search_dir: The directory that was searched
        """
        self.search_dir = search_dir

        message = (
            f"Cannot find eci_responses CSV file.\n"
            f"Searched in: {search_dir}\n"
            f"Expected pattern: eci_responses_YYYY-MM-DD_HH-MM-SS.csv\n"
            f"Hint: Run the ECI responses parser first."
        )

        super().__init__(message)
