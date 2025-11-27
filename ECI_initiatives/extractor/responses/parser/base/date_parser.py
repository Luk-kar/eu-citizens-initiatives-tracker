"""
Centralized date parsing for ECI responses

This class provides core date parsing functionality:
- Standard date format conversion to YYYY-MM-DD
- Deadline text conversion ("May 2018", "end of 2023", "early 2026")
- Utility methods for month name handling
"""

import re
import calendar
from datetime import datetime
from typing import Optional


def parse_date_string(date_str: str) -> Optional[str]:
    """
    Parse various date formats to YYYY-MM-DD.

    Args:
        date_str: Date string in formats like "27 March 2021", "27/03/2021"

    Returns:
        Date in YYYY-MM-DD format or None if parsing fails

    Supported formats:
        - "27 March 2021" (full month name)
        - "27 Mar 2021" (abbreviated month name)
        - "27/03/2021" (slash-separated)
        - "27-03-2021" (dash-separated)
        - "2021-03-27" (ISO format)
        - "February 2024" (month and year only)
        - "Mar 2024" (abbreviated month and year)
        - "2024" (year only)
    """
    # Common date formats in ECI responses
    date_formats = [
        "%d %B %Y",  # 27 March 2021
        "%d/%m/%Y",  # 27/03/2021
        "%d-%m-%Y",  # 27-03-2021
        "%Y-%m-%d",  # 2021-03-27 (already in target format)
        "%d %b %Y",  # 27 Mar 2021
        "%B %Y",  # February 2024 (month and year only)
        "%b %Y",  # Mar 2024 (abbreviated month and year)
        "%Y",  # Year only
    ]

    for fmt in date_formats:
        try:
            parsed = datetime.strptime(date_str.strip(), fmt)
            return parsed.strftime("%Y-%m-%d")
        except ValueError:
            continue

    return None


def convert_deadline_to_date(deadline: str) -> Optional[str]:
    """
    Convert deadline text to YYYY-MM-DD format (last day of month/year).

    Args:
        deadline: Cleaned deadline text like "may 2018", "the end of 2023",
                    "end 2024", "2019", "early 2026"

    Returns:
        Date string in YYYY-MM-DD format (last day of period) or None if parsing fails

    Examples:
        - "May 2018" → "2018-05-31"
        - "the end of 2023" → "2023-12-31"
        - "end of 2024" → "2024-12-31"
        - "end 2024" → "2024-12-31"
        - "2019" → "2019-12-31"
        - "March 2026" → "2026-03-31"
        - "early 2026" → "2026-03-31"
    """
    deadline_lower = deadline.lower().strip()

    # Validate it contains a year (4 digits)
    if not re.search(r"\d{4}", deadline_lower):
        return None

    # Pattern 1: "the end of YYYY" or "end of YYYY"
    endof_match = re.match(r"(?:the\s+)?end\s+of\s+(\d{4})", deadline_lower)
    if endof_match:
        year = int(endof_match.group(1))
        return f"{year}-12-31"

    # Pattern 1b: "end YYYY" (without "of")
    end_match = re.match(r"end\s+(\d{4})", deadline_lower)
    if end_match:
        year = int(end_match.group(1))
        return f"{year}-12-31"

    # Pattern 2: "early YYYY" (interpret as end of Q1 = March 31)
    early_match = re.match(r"early\s+(\d{4})", deadline_lower)
    if early_match:
        year = int(early_match.group(1))
        return f"{year}-03-31"

    # Pattern 3: "Month YYYY" (e.g., "May 2018", "march 2026")
    monthyear_match = re.match(r"([a-z]+)\s+(\d{4})", deadline_lower)
    if monthyear_match:
        month_name = monthyear_match.group(1).capitalize()
        year = int(monthyear_match.group(2))

        # Parse month name to month number
        try:
            month_date = datetime.strptime(month_name, "%B")  # Full month name
            month_num = month_date.month
        except ValueError:
            try:
                month_date = datetime.strptime(
                    month_name, "%b"
                )  # Abbreviated month name
                month_num = month_date.month
            except ValueError:
                return None

        # Get last day of the month
        last_day = calendar.monthrange(year, month_num)[1]
        return f"{year}-{month_num:02d}-{last_day:02d}"

    # Pattern 4: Just a year "YYYY" (e.g., "2019")
    year_only_match = re.match(r"^(\d{4})$", deadline_lower)
    if year_only_match:
        year = int(year_only_match.group(1))
        return f"{year}-12-31"

    return None


def parse_any_date_format(date_str: str) -> Optional[str]:
    """
    Parse any date format to YYYY-MM-DD, including exact dates and deadline-style dates.

    Combines functionality of parse_date_string() and convert_deadline_to_date()
    to handle all date formats found in ECI responses.

    Args:
        date_str: Date string in various formats

    Returns:
        Date in YYYY-MM-DD format or None if parsing fails

    Supported formats:
        Exact dates:
        - "27 March 2021" (full month name)
        - "27 Mar 2021" (abbreviated month name)
        - "27/03/2021" (slash-separated)
        - "27-03-2021" (dash-separated)
        - "2021-03-27" (ISO format)

        Month/Year dates (returns last day of month):
        - "February 2024" → "2024-02-29"
        - "Mar 2024" → "2024-03-31"

        Year-only dates (returns last day of year):
        - "2024" → "2024-12-31"

        Deadline-style dates:
        - "May 2018" → "2018-05-31"
        - "the end of 2023" → "2023-12-31"
        - "end of 2024" → "2024-12-31"
        - "end 2024" → "2024-12-31"
        - "early 2026" → "2026-03-31"
    """
    date_str_clean = date_str.strip()
    date_str_lower = date_str_clean.lower()

    # First, try exact date formats (with specific day)
    exact_date_formats = [
        "%d %B %Y",  # 27 March 2021
        "%d/%m/%Y",  # 27/03/2021
        "%d-%m-%Y",  # 27-03-2021
        "%Y-%m-%d",  # 2021-03-27 (ISO format)
        "%d %b %Y",  # 27 Mar 2021
    ]

    for fmt in exact_date_formats:
        try:
            parsed = datetime.strptime(date_str_clean, fmt)
            return parsed.strftime("%Y-%m-%d")
        except ValueError:
            continue

    # Check for deadline-style patterns before trying month/year formats

    # Pattern: "the end of YYYY" or "end of YYYY"
    endof_match = re.match(r"(?:the\s+)?end\s+of\s+(\d{4})", date_str_lower)
    if endof_match:
        year = int(endof_match.group(1))
        return f"{year}-12-31"

    # Pattern: "end YYYY" (without "of")
    end_match = re.match(r"end\s+(\d{4})", date_str_lower)
    if end_match:
        year = int(end_match.group(1))
        return f"{year}-12-31"

    # Pattern: "early YYYY" (interpret as end of Q1 = March 31)
    early_match = re.match(r"early\s+(\d{4})", date_str_lower)
    if early_match:
        year = int(early_match.group(1))
        return f"{year}-03-31"

    # Pattern: "Month YYYY" (e.g., "May 2018", "March 2026")
    # This handles both full and abbreviated month names
    monthyear_match = re.match(r"([a-z]+)\s+(\d{4})", date_str_lower)
    if monthyear_match:
        month_name = monthyear_match.group(1).capitalize()
        year = int(monthyear_match.group(2))

        # Parse month name to month number
        try:
            month_date = datetime.strptime(month_name, "%B")  # Full month name
            month_num = month_date.month
        except ValueError:
            try:
                month_date = datetime.strptime(month_name, "%b")  # Abbreviated
                month_num = month_date.month
            except ValueError:
                return None

        # Get last day of the month
        last_day = calendar.monthrange(year, month_num)[1]
        return f"{year}-{month_num:02d}-{last_day:02d}"

    # Pattern: Just a year "YYYY" (e.g., "2019", "2024")
    year_only_match = re.match(r"^(\d{4})$", date_str_lower)
    if year_only_match:
        year = int(year_only_match.group(1))
        return f"{year}-12-31"

    return None


def get_month_names_pattern() -> str:
    """
    Get regex pattern string for all month names.

    Returns:
        Pipe-separated string of month names suitable for regex

    Example:
        "January|February|March|April|May|June|July|August|September|October|November|December"
    """
    return "|".join(calendar.month_name[1:])


def format_date_from_match(
    match, day_group=1, month_group=2, year_group=3
) -> Optional[str]:
    """
    Format date from regex match in ISO 8601 format (YYYY-MM-DD)

    Args:
        match: Regex match object with date components
        day_group: Group index for day (default 1)
        month_group: Group index for month (default 2)
        year_group: Group index for year (default 3)

    Returns:
        Formatted date string in YYYY-MM-DD format, or None if match is None
    """
    if not match:
        return None

    day = match.group(day_group).zfill(2)
    month = match.group(month_group).zfill(2)
    year = match.group(year_group)
    return f"{year}-{month}-{day}"
