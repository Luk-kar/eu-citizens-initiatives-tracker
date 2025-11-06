"""
Extracts multimedia resources and documentation links including
Commission factsheets and campaign website information.
"""

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

    def extract_followup_dedicated_website(self, soup: BeautifulSoup) -> Optional[bool]:
        """Check if organizers maintained campaign website"""
        return False
