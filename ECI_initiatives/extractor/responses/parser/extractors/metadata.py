"""Basic metadata extraction: URLs and titles"""

import re
from bs4 import BeautifulSoup

from ..base.base_extractor import BaseExtractor

class BasicMetadataExtractor(BaseExtractor):
    """Extracts basic initiative metadata: URLs and titles"""

    def extract_response_url(self, soup: BeautifulSoup) -> str:
        """Extract the response page URL from HTML

        Tries multiple methods to find the URL:
        1. Active language link in site header
        2. Link with hreflang="en"
        3. Canonical link from head
        4. og:url meta tag
        """
        try:
            # Method 1: Find the active language link in the site header
            active_language_link = soup.find(
                'a',
                class_='ecl-site-header__language-link--active'
            )

            if active_language_link and active_language_link.get('href'):
                response_url = active_language_link['href']
                if response_url.startswith('http'):
                    return response_url
                elif response_url.startswith('/'):
                    return f"https://citizens-initiative.europa.eu{response_url}"
                else:
                    return f"https://citizens-initiative.europa.eu/{response_url}"

            # Method 2: Try finding link with hreflang="en"
            en_language_link = soup.find('a', attrs={'hreflang': 'en'})
            if en_language_link and en_language_link.get('href'):
                response_url = en_language_link['href']
                if response_url.startswith('http'):
                    return response_url
                elif response_url.startswith('/'):
                    return f"https://citizens-initiative.europa.eu{response_url}"
                else:
                    return f"https://citizens-initiative.europa.eu/{response_url}"

            # Method 3: Try canonical link from head
            canonical_link = soup.find('link', attrs={'rel': 'canonical'})
            if canonical_link and canonical_link.get('href'):
                response_url = canonical_link['href']
                if response_url.startswith('http'):
                    return response_url
                elif response_url.startswith('/'):
                    return f"https://citizens-initiative.europa.eu{response_url}"
                else:
                    return f"https://citizens-initiative.europa.eu/{response_url}"

            # Method 4: Try og:url meta tag
            og_url = soup.find('meta', attrs={'property': 'og:url'})
            if og_url and og_url.get('content'):
                response_url = og_url['content']
                if response_url.startswith('http'):
                    return response_url
                elif response_url.startswith('/'):
                    return f"https://citizens-initiative.europa.eu{response_url}"
                else:
                    return f"https://citizens-initiative.europa.eu/{response_url}"

            raise ValueError(
                f"Response URL not found for initiative {self.registration_number}. "
                "Expected one of: active language link, link with hreflang='en', "
                "canonical link tag, or og:url meta tag"
            )

        except Exception as e:
            raise ValueError(f"Error extracting response URL for initiative {self.registration_number}: {str(e)}") from e

    def extract_initiative_url(self, soup: BeautifulSoup) -> str:
        """Extract initiative URL from breadcrumb link or page links"""
        try:
            # Method 1: Find the breadcrumb link with text "Initiative detail"
            breadcrumb_link = soup.find(
                'a', 
                class_='ecl-breadcrumb__link', 
                string=lambda text: text and text.strip() == 'Initiative detail'
            )

            if breadcrumb_link and breadcrumb_link.get('href'):
                href = breadcrumb_link['href']

                if href.startswith('http'):
                    return href
                elif href.startswith('/'):
                    initiative_url = f"https://citizens-initiative.europa.eu{href}"
                    return initiative_url

            # Method 2: Search for any link matching /initiatives/details/YYYY/NNNNNN_en pattern
            all_links = soup.find_all('a', href=True, string=True)

            for link in all_links:
                href = link['href']
                link_text = link.get_text(strip=True)

                if not link_text:
                    continue

                if re.search(r'/initiatives/details/\d{4}/\d{6}_en$', href):
                    if href.startswith('http'):
                        self.logger.info(f"Found initiative URL in page link with text '{link_text}': {href}")
                        return href
                    elif href.startswith('/'):
                        initiative_url = f"https://citizens-initiative.europa.eu{href}"
                        self.logger.info(f"Found initiative URL in page link with text '{link_text}': {initiative_url}")
                        return initiative_url

            raise ValueError(
                f"Initiative URL not found for {self.registration_number}. "
                "Expected breadcrumb link with text 'Initiative detail' "
                "or link matching pattern /initiatives/details/YYYY/NNNNNN_en with text content"
            )

        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"Error extracting initiative URL for {self.registration_number}: {str(e)}") from e