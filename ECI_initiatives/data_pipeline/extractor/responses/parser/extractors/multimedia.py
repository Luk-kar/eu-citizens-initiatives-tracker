"""
Extracts multimedia resources and documentation links including
Commission factsheets and campaign website information.
"""

import re
from typing import Optional

from bs4 import BeautifulSoup

from ..base.base_extractor import BaseExtractor


class MultimediaDocumentationExtractor(BaseExtractor):
    """Extracts multimedia and documentation links"""

    def extract_commission_factsheet_url(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract the URL of the Commission factsheet PDF (English version)

        Returns:
            Optional[str]: URL to the factsheet PDF document, or None if no factsheet exists

        Raises:
            ValueError: If factsheet element exists but download link is missing or invalid
        """

        try:
            # Find all ecl-file divs (file download components)
            ecl_files = soup.find_all("div", class_=lambda x: x and "ecl-file" in x)

            # Look for the one with "Factsheet" in the title
            for file_div in ecl_files:
                # Find the title element
                title_div = file_div.find(
                    "div", class_=lambda x: x and "ecl-file__title" in x
                )

                if title_div:
                    title_text = title_div.get_text(strip=True)

                    # Check if this is a factsheet (case-insensitive)
                    if "factsheet" in title_text.lower():
                        factsheet_found = True

                        # Find the download link
                        download_link = file_div.find(
                            "a", class_=lambda x: x and "ecl-file__download" in x
                        )

                        if not download_link:
                            raise ValueError(
                                f"Factsheet element found but download link is "
                                f"missing for {self.registration_number}"
                            )

                        href = download_link.get("href", "").strip()

                        if not href:
                            raise ValueError(
                                f"Factsheet download link found but href is empty "
                                f"for {self.registration_number}"
                            )

                        # Successfully found factsheet with valid URL
                        return href

            # No factsheet found at all - this is OK, return None
            return None

        except ValueError:
            # Re-raise ValueError as-is
            raise
        except Exception as e:
            raise ValueError(
                f"Error extracting factsheet URL for {self.registration_number}: {str(e)}"
            ) from e

    def extract_followup_dedicated_website(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract the URL of the dedicated follow-up website for an ECI initiative.

        Searches for anchor tags with href attributes matching the pattern:
        https://.../eci/eci-{identifier}_en

        Note: Other referenced sites have too unpredictable a structure to enable
        reliable and maintainable extraction.

        This pattern identifies official EU Citizens' Initiative dedicated websites
        that provide detailed follow-up information about the initiative.

        Args:
            soup: BeautifulSoup parsed HTML document

        Returns:
            URL string of the dedicated website if found, None otherwise.
            Example return value: "https://ec.europa.eu/info/law/better-regulation/
            initiatives/eci/eci-water_en"

        Raises:
            ValueError: If critical error occurs during URL extraction

        Examples:
            Matching URLs:
            - https://ec.europa.eu/citizens-initiative/initiatives/details/eci/eci-water_en
            - https://example.com/eci/eci-animal-welfare_en

            Non-matching URLs:
            - https://example.com/eci/eci-something_de (wrong language code)
            - https://example.com/citizens-initiative_en (missing "eci-" prefix)
        """
        # Regex pattern explanation:
        # - ^https://     : URL must start with https://
        # - .*eci/        : followed by any characters, then "eci/"
        # - eci-          : literal "eci-" prefix for initiative identifier
        # - [^/]+         : one or more non-slash characters (the initiative ID)
        # - _en$          : ends with "_en" (English language code)
        DEDICATED_WEBSITE_URL_PATTERN = re.compile(
            r"^https://.*eci/eci-[^/]+_en$", re.IGNORECASE
        )

        try:
            # Find all anchor tags with href attributes
            links = soup.find_all("a", href=True)

            # Iterate through links to find matching dedicated website URL
            for link in links:
                href = link.get("href", "").strip()

                # Skip empty or missing hrefs
                if not href:
                    continue

                # Check if href matches the dedicated website pattern
                if DEDICATED_WEBSITE_URL_PATTERN.search(href):
                    # Return the first matching URL found
                    return href

            # No matching dedicated website link found (this is acceptable)
            return None

        except Exception as e:
            raise ValueError(
                f"Error extracting dedicated website URL for {self.registration_number}: {str(e)}"
            ) from e
