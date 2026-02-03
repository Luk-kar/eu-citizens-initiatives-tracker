"""
Command-line interface for the CSV merger.
"""

from .merger import ResponsesAndFollowupMerger
from .exceptions import MergerError


def main() -> None:
    """
    CLI entry point for the merger.

    Usage:
        python -m ECI_initiatives.csv_merger.responses
    """
    try:
        print("\n" + "=" * 80)
        print("ECI Responses and Follow-up CSV Merger")
        print("=" * 80 + "\n")

        # Create merger (this performs validation)
        merger = ResponsesAndFollowupMerger()

        # Execute merge
        merger.merge()

        print("\nMerge completed successfully!\n")

    except MergerError as e:
        print(f"\nERROR: {e}\n", flush=True)
        raise
    except Exception as e:
        print(f"\nUNEXPECTED ERROR: {e}\n", flush=True)
        raise
