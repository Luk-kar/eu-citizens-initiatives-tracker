"""
File operations for saving Commission response pages.
"""
import csv
import logging
from typing import List, Dict

from bs4 import BeautifulSoup

from ..consts import CSV_FIELDNAMES


def write_responses_csv(file_path: str, response_data: List[Dict[str, str]]) -> None:
    """
    Write response data to CSV file.
    
    Args:
        file_path: Full path to the CSV file
        response_data: List of response dictionaries to write
    """
    
    # IMPORTANT: Normalize registration numbers to match initiatives CSV format
    # Convert underscore format to slash format (2019_000007 → 2019/000007)
    # This ensures the registration_number field matches the format from the
    # initiatives scraper, enabling proper data joins between datasets

    normalized_data = []

    for record in response_data:

        normalized_record = record.copy()

        if 'registration_number' in normalized_record:

            # Replace underscores with slashes for consistency
            normalized_record['registration_number'] = normalized_record['registration_number'].replace('_', '/')
            
        normalized_data.append(normalized_record)
    
    with open(file_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
        writer.writeheader()
        writer.writerows(normalized_data)
    
    logger = logging.getLogger("ECIResponsesScraper")
    logger.debug(f"CSV file written: {file_path}")
