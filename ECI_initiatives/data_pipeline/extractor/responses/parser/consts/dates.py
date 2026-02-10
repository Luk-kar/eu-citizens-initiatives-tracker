"""
Provides centralized month name-to-number mappings
for consistent date parsing across ECI response extractors.
"""

import calendar


def build_month_dict() -> dict:
    """
    Build a dictionary mapping month names to their numeric values.

    Returns:
        Dictionary with lowercase month names/abbreviations as keys and
        zero-padded month numbers as values

    Example:
        {
            'january': '01', 'jan': '01',
            'february': '02', 'feb': '02',
            ...
        }
    """
    month_dict = {calendar.month_name[i].lower(): str(i).zfill(2) for i in range(1, 13)}
    month_dict.update(
        {calendar.month_abbr[i].lower(): str(i).zfill(2) for i in range(1, 13)}
    )
    return month_dict


month_map = build_month_dict()
