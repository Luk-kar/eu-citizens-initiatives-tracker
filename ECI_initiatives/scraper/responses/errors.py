"""
Custom exceptions for Commission responses scraper.
"""


class MissingDataDirectoryError(FileNotFoundError):
    """
    Raised when the required data directory structure is not found.
    
    This typically occurs when the responses scraper is run before
    the initiatives scraper has created the timestamp directory.
    """
    
    def __init__(self, expected_path: str, hint: str = None):
        """
        Initialize the exception with context.
        
        Args:
            expected_path: The path that was expected but not found
            hint: Optional suggestion for how to fix the issue
        """
        self.expected_path = expected_path
        self.hint = hint or "Run the initiatives scraper first to create the timestamp directory."
        
        message = (
            f"Cannot find required data directory.\n"
            f"Expected: {expected_path}\n"
            f"Hint: {self.hint}"
        )
        
        super().__init__(message)
