`./ECI_initiatives/extractor/responses/parser/extractors/classifiers/__init__.py`:
```

```

`./ECI_initiatives/extractor/responses/parser/extractors/classifiers/status_matcher.py`:
```
"""Status classification and matching logic"""

from typing import Optional

from ...consts import ECIImplementationStatus


class LegislativeOutcomeClassifier:
    """Helper class for matching legislative status patterns in ECI response text"""

    # Pattern constants for status detection
    APPLICABLE_PATTERNS = [
        "became applicable",
        "became applicable immediately",
        "and applicable from",
    ]

    ADOPTION_EVIDENCE = [
        "council of the eu adopted",
        "council adopted the regulation",
        "published in the official journal",
        "following the agreement of the european parliament",
    ]

    COMMITMENT_PATTERNS = [
        "committed to come forward with a legislative proposal",
        "communicated its intention to table a legislative proposal",
        "intention to table a legislative proposal",
        "will table a legislative proposal",  # "will table" - UK\EU idiom phrase
        "committed to table a legislative proposal",
        "to table a legislative proposal",
    ]

    REJECTION_PATTERNS = [
        "will not make a legislative proposal",
        "not propose new legislation",
        "decided not to submit a legislative proposal",
        "has decided not to submit a legislative proposal",
        "no further legal acts are proposed",
        "no new legislation will be proposed",
        "no legislative proposal",
        "neither scientific nor legal grounds",
        "already covered",
        "proposals fall outside",
        "outside of eu competence",
        "outside the eu competence",
        "not within eu competence",
        "beyond eu competence",
    ]

    # Special rejection pattern requiring two keywords
    NO_REPEAL_PATTERN = ("no repeal", "was proposed")

    EXISTING_FRAMEWORK_PATTERNS = [
        "existing funding framework",
        "existing legislation",
        "already covered",
        "already in place",
        "legislation and policies already in place",
        "recently debated and agreed",
        "is the appropriate one",
        "policies already in place",
    ]

    REJECTION_WITH_ACTIONS_INDICATORS = [
        "committed",
        "will continue",
        "monitor",
        "support",
    ]

    ASSESSMENT_INDICATORS = [
        "launch",
        "started working on",
        "external study to be carried out",
        "call for evidence",
        "preparatory work",
        "with a view to launch",
    ]

    def __init__(self, content: str):
        """
        Initialize with normalized content string

        Args:
            content: Text content from ECI Commission response
        """

        self.content = content.lower()

    def check_applicable(self) -> bool:
        """
        Check if initiative reached applicable status (law is in force)

        Returns:
            True if law became applicable, False otherwise
        """

        # Direct applicable phrases
        if any(phrase in self.content for phrase in self.APPLICABLE_PATTERNS):
            return True

        # "Entered into force" with adoption evidence
        if "entered into force" in self.content:
            if any(phrase in self.content for phrase in self.ADOPTION_EVIDENCE):
                return True

        # "Applies from" with legislation context
        if "applies from" in self.content or "apply from" in self.content:
            if any(
                word in self.content for word in ["adopted", "regulation", "directive"]
            ):
                return True

        return False

    def check_adopted(self) -> bool:
        """
        Check if proposal was adopted but not yet applicable

        Returns:
            True if adopted but not yet in force, False otherwise
        """

        # Published in Official Journal (but not applicable yet)
        if (
            "published in the official journal" in self.content
            or "official journal of the eu" in self.content
        ):
            if (
                "became applicable" not in self.content
                and "applies from" not in self.content
            ):
                return True

        # Adopted by Commission or Council
        if any(
            phrase in self.content
            for phrase in [
                "was adopted by the commission",
                "council of the eu adopted",
                "council adopted the regulation",
            ]
        ):
            return True

        return False

    def check_committed(self) -> bool:
        """
        Check if Commission committed to legislative proposal

        Returns:
            True if commitment to legislation exists, False otherwise
        """

        # Standard commitment patterns
        if any(phrase in self.content for phrase in self.COMMITMENT_PATTERNS):
            return True

        # "To table a legislative proposal by [date]"
        if "to table a legislative proposal" in self.content and "by" in self.content:
            return True

        return False

    def check_assessment_pending(self) -> bool:
        """
        Check if initiative is in assessment phase

        Returns:
            True if assessment ongoing, False otherwise
        """

        # Avoid false positives with higher status
        if (
            "intention to table a legislative proposal" in self.content
            or "became applicable" in self.content
        ):
            return False

        # EFSA scientific opinion pending
        if (
            "tasked" in self.content
            and "efsa" in self.content
            and "scientific opinion" in self.content
        ):
            return True

        # Impact assessment ongoing
        if "impact assessment" in self.content:
            if any(phrase in self.content for phrase in self.ASSESSMENT_INDICATORS):
                return True

        # Future communication expected
        if "will communicate" in self.content and (
            "by" in self.content or "after" in self.content
        ):
            return True

        return False

    def check_roadmap_development(self) -> bool:
        """
        Check if roadmap is being developed

        Returns:
            True if roadmap in development, False otherwise
        """

        if "became applicable" in self.content:
            return False

        # Check for roadmap with various development verbs
        if "roadmap" not in self.content:
            return False

        # Roadmap action indicators
        roadmap_indicators = [
            "develop",  # "develop a roadmap"
            "work on",  # "work on a roadmap"
            "work together",  # "work together on a roadmap"
            "work with",  # "work with parties on a roadmap"
            "launched",  # "launched a roadmap"
            "started work",  # "started work on a roadmap"
            "will work",  # "will work on a roadmap"
            "working on",  # "working on a roadmap"
            "preparing",  # "preparing a roadmap"
            "towards",  # "roadmap towards" (specific pattern)
        ]

        return any(indicator in self.content for indicator in roadmap_indicators)

    def check_rejection_type(self) -> Optional[str]:
        """
        Determine rejection type if initiative was rejected

        Returns:
            'rejected', 'rejected_with_actions', 'rejected_already_covered', or None
        """

        has_primary_rejection = any(
            phrase in self.content for phrase in self.REJECTION_PATTERNS
        )
        has_no_repeal = all(
            keyword in self.content for keyword in self.NO_REPEAL_PATTERN
        )

        if not (has_primary_rejection or has_no_repeal):
            return None

        if has_no_repeal:
            if any(
                word in self.content for word in self.REJECTION_WITH_ACTIONS_INDICATORS
            ):
                return "rejected_with_actions"
            return "rejected"

        if any(phrase in self.content for phrase in self.EXISTING_FRAMEWORK_PATTERNS):
            return "rejected_already_covered"

        if any(word in self.content for word in self.REJECTION_WITH_ACTIONS_INDICATORS):
            return "rejected_with_actions"

        return "rejected"

    def check_non_legislative_action(self) -> bool:
        """
        Check if only non-legislative actions were taken

        Returns:
            True if only policy actions (no legislation), False otherwise
        """

        # Check for non-legislative focus without proposals
        if "intends to focus on" in self.content or "implementation of" in self.content:
            if "proposal" not in self.content:
                return True

        # Specific non-legislative action patterns
        action_patterns = [
            "committed, in particular, to taking the following actions",
            "launch an eu-wide public consultation",
            "improve transparency",
            "establish harmonised",
        ]

        if any(phrase in self.content for phrase in action_patterns):
            if (
                "legislative proposal" not in self.content
                and "proposal" not in self.content
            ):
                return True

        return False

    def check_proposal_pending(self) -> bool:
        """
        Check if existing proposals are pending adoption

        Returns:
            True if proposals under negotiation, False otherwise
        """

        has_tabled = "proposal" in self.content and "tabled" in self.content
        has_context = "rather than proposing new legislative acts" in self.content
        not_completed = (
            "became applicable" not in self.content
            and "entered into force" not in self.content
        )

        return has_tabled and has_context and not_completed

    def extract_technical_status(self) -> str:
        """
        Extract technical status code by checking all patterns in priority order

        Status hierarchy (highest to lowest priority):
        1. applicable (Law Active)
        2. adopted (Law Approved)
        3. committed (Law Promised)
        4. assessment_pending (Being Studied)
        5. roadmap_development (Action Plan Created)
        6. rejected_already_covered / rejected_with_actions / rejected
        7. non_legislative_action (Policy Changes Only)
        8. proposal_pending_adoption (Proposals Under Review)

        Returns:
            Technical status code (e.g., 'applicable', 'committed', etc.)

        Raises:
            ValueError: If no status pattern matches
        """

        # Define status checks in priority order (highest to lowest)
        status_checks = [
            (ECIImplementationStatus.APPLICABLE.legal_term, self.check_applicable),
            (ECIImplementationStatus.ADOPTED.legal_term, self.check_adopted),
            (ECIImplementationStatus.COMMITTED.legal_term, self.check_committed),
            (
                ECIImplementationStatus.ASSESSMENT_PENDING.legal_term,
                self.check_assessment_pending,
            ),
            (
                ECIImplementationStatus.ROADMAP_DEVELOPMENT.legal_term,
                self.check_roadmap_development,
            ),
            (None, self.check_rejection_type),  # Returns status name directly
            (
                ECIImplementationStatus.NON_LEGISLATIVE_ACTION.legal_term,
                self.check_non_legislative_action,
            ),
            (
                ECIImplementationStatus.PROPOSAL_PENDING_ADOPTION.legal_term,
                self.check_proposal_pending,
            ),
        ]

        # Check each status in priority order
        for status_name, check_func in status_checks:
            result = check_func()

            # Handle rejection check (returns status name or None)
            if status_name is None and result:
                return result

            # Handle boolean checks
            if status_name and result:
                return status_name

        # No status matched
        raise ValueError("No known status patterns matched")

    def translate_to_citizen_friendly(self, technical_status: str) -> str:
        """
        Translate technical status to citizen-friendly name

        Args:
            technical_status: Technical status code (e.g., 'applicable')

        Returns:
            Citizen-friendly status name (e.g., 'Law Active')
        """
        status = ECIImplementationStatus.get_status_by_term(technical_status)

        if status:
            return status.human_readable_explanation

        return technical_status

```

`./ECI_initiatives/extractor/responses/parser/extractors/followup.py`:
```
"""
Extracts follow-up activity information including
roadmaps, workshops, partnership programs, and
court case references from post-response sections.
"""

from typing import Optional

from bs4 import BeautifulSoup

from ..base.base_extractor import BaseExtractor


class FollowUpActivityExtractor(BaseExtractor):
    """Extracts follow-up activities data"""

    def extract_has_followup_section(self, soup: BeautifulSoup) -> Optional[bool]:
        """Check if page includes follow-up activities section"""
        try:
            return None
        except Exception as e:
            raise ValueError(
                f"Error checking followup section for {self.registration_number}: {str(e)}"
            ) from e

    def extract_followup_events(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract follow-up events information"""
        try:
            return None
        except Exception as e:
            raise ValueError(
                f"Error extracting followup events for {self.registration_number}: {str(e)}"
            ) from e

    def extract_has_partnership_programs(self, soup: BeautifulSoup) -> Optional[bool]:
        try:
            return None
        except Exception as e:
            raise ValueError(
                f"Error checking roadmap for {self.registration_number}: {str(e)}"
            ) from e

    def extract_has_roadmap(self, soup: BeautifulSoup) -> Optional[bool]:
        """Check if initiative has a roadmap"""
        try:
            return None
        except Exception as e:
            raise ValueError(
                f"Error checking roadmap for {self.registration_number}: {str(e)}"
            ) from e

    def extract_has_workshop(self, soup: BeautifulSoup) -> Optional[bool]:
        """Check if initiative has workshop activities"""
        try:
            return None
        except Exception as e:
            raise ValueError(
                f"Error checking workshop for {self.registration_number}: {str(e)}"
            ) from e

    def extract_partnership_programs(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract partnership programs information"""
        try:
            return None
        except Exception as e:
            raise ValueError(
                f"Error extracting partnership programs for {self.registration_number}: {str(e)}"
            ) from e

    def extract_court_cases_referenced(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract Court of Justice case numbers"""
        try:
            return None
        except Exception as e:
            raise ValueError(
                f"Error extracting court cases for {self.registration_number}: {str(e)}"
            ) from e

    def extract_latest_update_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract most recent date from follow-up section"""
        try:
            return None
        except Exception as e:
            raise ValueError(
                f"Error extracting latest update date for {self.registration_number}: {str(e)}"
            ) from e

```

`./ECI_initiatives/extractor/responses/parser/extractors/__init__.py`:
```

```

`./ECI_initiatives/extractor/responses/parser/extractors/metadata.py`:
```
"""
Extracts basic initiative metadata including
response page URLs and
initiative detail page URLs from HTML structure.
"""

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
                "a", class_="ecl-site-header__language-link--active"
            )

            if active_language_link and active_language_link.get("href"):
                response_url = active_language_link["href"]
                if response_url.startswith("http"):
                    return response_url
                elif response_url.startswith("/"):
                    return f"https://citizens-initiative.europa.eu{response_url}"
                else:
                    return f"https://citizens-initiative.europa.eu/{response_url}"

            # Method 2: Try finding link with hreflang="en"
            en_language_link = soup.find("a", attrs={"hreflang": "en"})
            if en_language_link and en_language_link.get("href"):
                response_url = en_language_link["href"]
                if response_url.startswith("http"):
                    return response_url
                elif response_url.startswith("/"):
                    return f"https://citizens-initiative.europa.eu{response_url}"
                else:
                    return f"https://citizens-initiative.europa.eu/{response_url}"

            # Method 3: Try canonical link from head
            canonical_link = soup.find("link", attrs={"rel": "canonical"})
            if canonical_link and canonical_link.get("href"):
                response_url = canonical_link["href"]
                if response_url.startswith("http"):
                    return response_url
                elif response_url.startswith("/"):
                    return f"https://citizens-initiative.europa.eu{response_url}"
                else:
                    return f"https://citizens-initiative.europa.eu/{response_url}"

            # Method 4: Try og:url meta tag
            og_url = soup.find("meta", attrs={"property": "og:url"})
            if og_url and og_url.get("content"):
                response_url = og_url["content"]
                if response_url.startswith("http"):
                    return response_url
                elif response_url.startswith("/"):
                    return f"https://citizens-initiative.europa.eu{response_url}"
                else:
                    return f"https://citizens-initiative.europa.eu/{response_url}"

            raise ValueError(
                f"Response URL not found for initiative {self.registration_number}. "
                "Expected one of: active language link, link with hreflang='en', "
                "canonical link tag, or og:url meta tag"
            )

        except Exception as e:
            raise ValueError(
                f"Error extracting response URL for initiative {self.registration_number}: {str(e)}"
            ) from e

    def extract_initiative_url(self, soup: BeautifulSoup) -> str:
        """Extract initiative URL from breadcrumb link or page links"""
        try:
            # Method 1: Find the breadcrumb link with text "Initiative detail"
            breadcrumb_link = soup.find(
                "a",
                class_="ecl-breadcrumb__link",
                string=lambda text: text and text.strip() == "Initiative detail",
            )

            if breadcrumb_link and breadcrumb_link.get("href"):
                href = breadcrumb_link["href"]

                if href.startswith("http"):
                    return href
                elif href.startswith("/"):
                    initiative_url = f"https://citizens-initiative.europa.eu{href}"
                    return initiative_url

            # Method 2: Search for any link matching /initiatives/details/YYYY/NNNNNN_en pattern
            all_links = soup.find_all("a", href=True, string=True)

            for link in all_links:
                href = link["href"]
                link_text = link.get_text(strip=True)

                if not link_text:
                    continue

                if re.search(r"/initiatives/details/\d{4}/\d{6}_en$", href):
                    if href.startswith("http"):
                        self.logger.info(
                            f"Found initiative URL in page link with text '{link_text}': {href}"
                        )
                        return href
                    elif href.startswith("/"):
                        initiative_url = f"https://citizens-initiative.europa.eu{href}"
                        self.logger.info(
                            f"Found initiative URL in page link with text '{link_text}': "
                            f"{initiative_url}"
                        )
                        return initiative_url

            raise ValueError(
                f"Initiative URL not found for {self.registration_number}. "
                "Expected breadcrumb link with text 'Initiative detail' "
                "or link matching pattern /initiatives/details/YYYY/NNNNNN_en with text content"
            )

        except ValueError:
            raise
        except Exception as e:
            raise ValueError(
                f"Error extracting initiative URL for {self.registration_number}: {str(e)}"
            ) from e

```

`./ECI_initiatives/extractor/responses/parser/extractors/multimedia.py`:
```
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

    def extract_has_dedicated_website(self, soup: BeautifulSoup) -> Optional[bool]:
        """Check if organizers maintained campaign website"""
        return False

```

`./ECI_initiatives/extractor/responses/parser/extractors/outcome.py`:
```
"""
Extracts legislative outcome data by
classifying Commission responses, determining proposal status, and
identifying legislative actions taken.
"""

import calendar
import json
import re
from datetime import datetime
from typing import Optional

from bs4 import BeautifulSoup

from ..base.base_extractor import BaseExtractor
from .classifiers.status_matcher import LegislativeOutcomeClassifier
from ..base.date_parser import (
    parse_date_string,
    convert_deadline_to_date,
)

from ..consts import (
    REJECTION_REASONING_KEYWORDS,
    NonLegislativeAction,
    DEADLINE_PATTERNS,
    APPLICABLE_DATE_PATTERNS,
    LegislativeStatus,
)


class LegislativeOutcomeExtractor(BaseExtractor):
    """Extractor for legislative outcome and proposal status data"""

    # Keywords that indicate rejection reasoning

    def __init__(self, registration_number: Optional[str] = None):
        """
        Initialize extractor

        Args:
            registration_number: ECI registration number for error messages
        """
        self.registration_number = registration_number

    def _find_answer_section(self, soup: BeautifulSoup):
        """Find the Answer section header in the HTML."""
        return soup.find("h2", id="Answer-of-the-European-Commission") or soup.find(
            "h2", id="Answer-of-the-European-Commission-and-follow-up"
        )

    def _extract_legislative_content(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Extract all text content after Answer section.
        Returns normalized lowercase string or None if section not found.
        """
        answer_section = self._find_answer_section(soup)

        if not answer_section:
            return None

        all_text = []
        for sibling in answer_section.find_next_siblings():
            if not self._should_skip_element(sibling):
                all_text.append(sibling.get_text(strip=False))

        content = " ".join(all_text).lower()
        content = re.sub(r"\s+", " ", content).strip()

        return content

    def _should_skip_element(self, element) -> bool:
        """Check if element should be skipped during extraction."""
        if element.name == "h2":
            return True
        if (
            element.name == "div"
            and element.get("class")
            and "ecl-file" in element.get("class")
        ):
            return True
        return False

    def _get_classifier(self, soup: BeautifulSoup) -> LegislativeOutcomeClassifier:
        """
        Create and return a LegislativeOutcomeClassifier for the given HTML.

        Args:
            soup: BeautifulSoup object containing ECI response HTML

        Returns:
            LegislativeOutcomeClassifier instance

        Raises:
            ValueError: If Answer section is not found or is empty
        """
        content = self._extract_legislative_content(soup)
        if not content:
            raise ValueError(
                "Could not extract legislative content for "
                f"initiative {self.registration_number}.\n"
                f"Answer section may be missing or empty."
            )
        return LegislativeOutcomeClassifier(content)

    def extract_highest_status_reached(self, soup: BeautifulSoup) -> str:
        """
        Extract the highest status reached by the initiative.

        Status hierarchy (highest to lowest):
        1. applicable - Law Active
        2. adopted - Law Approved
        3. committed - Law Promised
        4. assessment_pending - Being Studied
        5. roadmap_development - Action Plan Created
        6. rejected_already_covered - Rejected - Already Covered
        7. rejected_with_actions - Rejected - Alternative Actions
        8. rejected - Rejected
        9. non_legislative_action - Policy Changes Only
        10. proposal_pending_adoption - Proposals Under Review

        Args:
            soup: BeautifulSoup object containing ECI response HTML

        Returns:
            Citizen-friendly status name (e.g., "Law Active")

        Raises:
            ValueError: If error occurs during extraction or no status can be determined
        """
        try:
            matcher = self._get_classifier(soup)
            technical_status = matcher.extract_technical_status()
            return matcher.translate_to_citizen_friendly(technical_status)

        except ValueError as e:
            if "No known status patterns matched" in str(e):
                content = self._extract_legislative_content(soup)
                content_preview = (
                    content[:500] + "..." if len(content) > 500 else content
                )
                raise ValueError(
                    "Could not determine legislative status for initiative:"
                    f"\n{self.registration_number}\n"
                    f"No known status patterns matched. Content preview:"
                    f"\n{content_preview}\n"
                ) from e
            raise
        except Exception as e:
            raise ValueError(
                f"Error extracting highest status reached for {self.registration_number}: {str(e)}"
            ) from e

    def extract_proposal_commitment_stated(self, soup: BeautifulSoup) -> Optional[bool]:
        """
        Extract whether Commission explicitly committed to propose legislation.

        Returns:
            True if commitment found, False otherwise
        """
        try:
            matcher = self._get_classifier(soup)
            return matcher.check_committed()

        except Exception as e:
            raise ValueError(
                "Error extracting proposal commitment status for "
                f"{self.registration_number}: {str(e)}"
            ) from e

    def extract_proposal_rejected(self, soup: BeautifulSoup) -> Optional[bool]:
        """
        Extract whether Commission explicitly rejected making a legislative proposal.

        Returns:
            True if rejection stated, False otherwise
        """
        try:
            matcher = self._get_classifier(soup)
            rejection_type = matcher.check_rejection_type()
            return bool(rejection_type)

        except Exception as e:
            raise ValueError(
                "Error extracting proposal rejection status for "
                f"{self.registration_number}: {str(e)}"
            ) from e

    def _extract_text_with_keyword_filter(
        self, sibling, keywords: list
    ) -> Optional[str]:
        """
        Extract text from element if it contains any of the keywords.

        Args:
            sibling: BeautifulSoup element to extract from
            keywords: List of keywords to filter by

        Returns:
            Extracted text or None if no keyword match
        """
        if sibling.name not in ["p", "li", "ul", "ol"]:
            return None

        if sibling.name in ["ul", "ol"]:
            list_items = sibling.find_all("li")
            matching_texts = []
            for li in list_items:
                text = li.get_text(strip=True)
                if any(keyword in text.lower() for keyword in keywords):
                    matching_texts.append(text)
            return " ".join(matching_texts) if matching_texts else None
        else:
            text = sibling.get_text(strip=True)
            if any(keyword in text.lower() for keyword in keywords):
                return text
            return None

    def _extract_mixed_response_reasoning(self, answer_section) -> str:
        """
        Extract reasoning for mixed response (both commitment and rejection).
        Finds all text mentioning 'legislative proposal'.

        Args:
            answer_section: BeautifulSoup element of Answer section

        Returns:
            Combined text of all relevant paragraphs

        Raises:
            ValueError: If no relevant text found
        """
        legislative_proposal_paragraphs = []

        for sibling in answer_section.find_next_siblings():
            if self._should_skip_element(sibling):
                if sibling.name == "h2":
                    break
                continue

            extracted_text = self._extract_text_with_keyword_filter(
                sibling, ["legislative proposal"]
            )
            if extracted_text:
                legislative_proposal_paragraphs.append(extracted_text)

        if legislative_proposal_paragraphs:
            return " ".join(legislative_proposal_paragraphs)

        raise ValueError(
            "Failed to extract rejection reasoning for mixed response: "
            f"{self.registration_number}.\n"
            f"The Commission committed to some legislative action but rejected other aims.\n"
            f"No paragraphs containing 'legislative proposal' were found in the Answer section.\n"
            f"legislative_proposal_paragraphs:\n{legislative_proposal_paragraphs}\n"
            f"answer_section:\n{answer_section}\n"
        )

    def _extract_pure_rejection_reasoning(self, answer_section) -> str:
        """
        Extract reasoning for pure rejection (no commitment).
        Finds all text containing rejection keywords.

        Args:
            answer_section: BeautifulSoup element of Answer section

        Returns:
            Combined text of all relevant paragraphs or fallback message
        """
        rejection_sentences = []

        for sibling in answer_section.find_next_siblings():
            if self._should_skip_element(sibling):
                if sibling.name == "h2":
                    break
                continue

            extracted_text = self._extract_text_with_keyword_filter(
                sibling, REJECTION_REASONING_KEYWORDS
            )
            if extracted_text:
                rejection_sentences.append(extracted_text)

        if rejection_sentences:
            return " ".join(rejection_sentences)

        return "The Commission decided not to make a legislative proposal."

    def extract_rejection_reasoning(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Extract the reasoning provided by Commission for rejecting legislative proposal.
        Returns full text explanation or None if not rejected.
        For mixed responses (both commitment and rejection), extracts all relevant context.

        Returns:
            String containing rejection reasoning, or None if no rejection found

        Raises:
            ValueError: If Answer section is not found or is empty
        """
        try:
            matcher = self._get_classifier(soup)
            rejection_type = matcher.check_rejection_type()

            if not rejection_type:
                return None

            answer_section = self._find_answer_section(soup)
            if not answer_section:
                return None

            has_commitment = matcher.check_committed()

            if has_commitment:
                return self._extract_mixed_response_reasoning(answer_section)
            else:
                return self._extract_pure_rejection_reasoning(answer_section)

        except Exception as e:
            raise ValueError(
                f"Error extracting rejection reasoning for {self.registration_number}: {str(e)}"
            ) from e

    def extract_applicable_date(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Extract the date when regulation/directive became applicable (implementation deadline).
        Format: YYYY-MM-DD

        Returns:
            Date string in YYYY-MM-DD format or None if not applicable

        Raises:
            ValueError: If Answer section not found
        """
        try:
            answer_section = self._find_answer_section(soup)
            if not answer_section:
                raise ValueError(
                    f"Could not find Answer section for initiative {self.registration_number}"
                )

            # Check if this initiative has applicable status
            matcher = self._get_classifier(soup)
            if not matcher.check_applicable():
                return None

            # Patterns to search for applicable dates
            applicable_patterns = [
                # "became applicable 18 months later, i.e. on 27 March 2021"
                r"became applicable.*?on\s+(\d{1,2}\s+[A-Za-z]+\s+\d{4})",
                # "became applicable immediately"
                r"became applicable immediately",
                # "applicable from 27 March 2021"
                r"applicable from\s+(\d{1,2}\s+[A-Za-z]+\s+\d{4})",
                # "and applicable from 27 March 2021"
                r"and applicable from\s+(\d{1,2}\s+[A-Za-z]+\s+\d{4})",
                # "applies from 27 March 2021"
                r"applies from\s+(\d{1,2}\s+[A-Za-z]+\s+\d{4})",
                # "apply from 27 March 2021"
                r"apply from\s+(\d{1,2}\s+[A-Za-z]+\s+\d{4})",
            ]

            # Search through all siblings after Answer section
            for sibling in answer_section.find_next_siblings():
                if self._should_skip_element(sibling):
                    if sibling.name == "h2":
                        continue  # Don't break, check other sections too
                    continue

                text = sibling.get_text(strip=False)

                # Check for "immediately" case first
                if "became applicable immediately" in text.lower():
                    # Try to find entry into force date nearby
                    force_match = re.search(
                        r"entered into force on\s+(\d{1,2}\s+[A-Za-z]+\s+\d{4})",
                        text,
                        re.IGNORECASE,
                    )
                    if force_match:
                        date_str = force_match.group(1).strip()
                        parsed_date = parse_date_string(date_str)
                        if parsed_date:
                            return parsed_date

                # Check each pattern
                for pattern in applicable_patterns:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        if match.groups():  # Has captured group
                            date_str = match.group(1).strip()
                            parsed_date = parse_date_string(date_str)
                            if parsed_date:
                                return parsed_date

            return None

        except Exception as e:
            raise ValueError(
                f"Error extracting applicable date for {self.registration_number}: {str(e)}"
            ) from e

    def extract_commissions_deadlines(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Extract all Commission deadlines mentioned in the response as JSON.
        Returns a dictionary where keys are dates (YYYY-MM-DD) and
        values are phrases connected to those dates.
        Returns None if no deadlines are mentioned.

        Format: JSON string like:
        {
            "2018-05-31": "committed to come forward with a legislative proposal",
            "2026-03-31": "will communicate on the most appropriate action",
            "2024-12-31": "complete the impact assessment"
        }

        Returns:
            JSON string with date->phrase mapping or None if no deadlines found

        Raises:
            ValueError: If Answer section not found
        """
        try:

            answer_section = self._find_answer_section(soup)
            if not answer_section:
                raise ValueError(
                    f"Could not find Answer section for initiative {self.registration_number}"
                )

            # Comprehensive deadline patterns covering various commitment types
            deadlines_dict = {}

            # Search through all siblings after Answer section
            for sibling in answer_section.find_next_siblings():
                if self._should_skip_element(sibling):
                    if sibling.name == "h2":
                        break
                    continue

                text = sibling.get_text(strip=False)
                text_lower = text.lower()

                # Check each pattern
                for pattern in DEADLINE_PATTERNS:
                    # Find all matches in this element (handles multiple deadlines per element)
                    for match in re.finditer(pattern, text_lower, re.IGNORECASE):
                        deadline_text = match.group(1).strip()

                        if deadline_text:
                            # Clean and convert the deadline
                            deadline_cleaned = self._clean_deadline_text(deadline_text)
                            if deadline_cleaned:
                                deadline_date = convert_deadline_to_date(
                                    deadline_cleaned
                                )
                                if deadline_date:
                                    # Extract the complete sentence containing this deadline
                                    sentence = self._extract_complete_sentence(
                                        text, match.start()
                                    )

                                    if sentence:
                                        # Clean up whitespace
                                        sentence = re.sub(r"\s+", " ", sentence).strip()

                                        # If we already have this date, append to existing phrase
                                        if deadline_date in deadlines_dict:
                                            # Only append if it's different content
                                            if (
                                                sentence
                                                not in deadlines_dict[deadline_date]
                                            ):
                                                deadlines_dict[
                                                    deadline_date
                                                ] += f"; {sentence}"
                                        else:
                                            deadlines_dict[deadline_date] = sentence

            # Return None if no deadlines found, otherwise return JSON string
            if not deadlines_dict:
                return None

            return json.dumps(deadlines_dict, ensure_ascii=False, indent=2)

        except Exception as e:
            raise ValueError(
                f"Error extracting commission deadlines for {self.registration_number}: {str(e)}"
            ) from e

    def _extract_complete_sentence(
        self, text: str, match_position: int
    ) -> Optional[str]:
        """
        Extract the complete sentence containing the deadline match.

        Args:
            text: Full text to search within
            match_position: Position of the regex match in the text

        Returns:
            Complete sentence or None if extraction fails
        """
        # Find the start of the sentence (look backwards for sentence boundary)
        sentence_start = 0

        # Look backwards from match position for sentence start markers
        for i in range(match_position - 1, -1, -1):
            char = text[i]

            # Sentence boundaries: period, question mark, exclamation, or start of text
            if char in ".!?":
                # Make sure it's not an abbreviation (check for space after)
                if i + 1 < len(text) and text[i + 1].isspace():
                    sentence_start = i + 1
                    break
            # Also break at bullet points or list markers
            elif char == "•" or (char == "\n" and i > 0 and text[i - 1] == "\n"):
                sentence_start = i + 1
                break

        # Find the end of the sentence (look forwards for sentence boundary)
        sentence_end = len(text)

        # Look forwards from match position for sentence end markers
        for i in range(match_position, len(text)):
            char = text[i]

            # Sentence boundaries: period, question mark, exclamation
            if char in ".!?":
                # Include the punctuation and stop
                sentence_end = i + 1
                break
            # Also break at newlines indicating paragraph breaks
            elif char == "\n" and i + 1 < len(text) and text[i + 1] == "\n":
                sentence_end = i
                break

        # Extract and clean the sentence
        sentence = text[sentence_start:sentence_end].strip()

        # Remove leading punctuation or whitespace
        sentence = sentence.lstrip(".,;:•\n\r\t ")

        return sentence if sentence else None

    def _clean_deadline_text(self, deadline: str) -> Optional[str]:
        """
        Clean deadline text by removing trailing words that aren't part of the date.

        Args:
            deadline: Raw deadline text

        Returns:
            Cleaned deadline text or None if invalid
        """
        # Remove common trailing phrases
        deadline = re.sub(
            r"\s+(?:to|for|in order to|with|amongst|among).*$",
            "",
            deadline,
            flags=re.IGNORECASE,
        )

        # Remove trailing commas, semicolons, periods
        deadline = deadline.rstrip(".,;")

        # Validate it contains a year (4 digits)
        if not re.search(r"\d{4}", deadline):
            return None

        return deadline.strip()

    # TODO: need a refactor
    def extract_legislative_action(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Extract LEGISLATIVE actions - proposals, adoptions, laws, regulations, directives.
        Excludes: rejection statements, enforcement activities, policy actions.
        Returns JSON string with list of legislative actions or None

        Each action contains:
        - type: Type of action (e.g., "Regulation Proposal", "Directive Revision", "Tariff Codes Creation")
        - description: Brief description of the action
        - status: Status of action ("proposed", "adopted", "in_force", "withdrawn", "planned")
        - date: Date in YYYY-MM-DD format (when applicable)
        - document_url: URL to official document (optional)
        """
        try:
            # Check if proposal was rejected
            matcher = self._get_classifier(soup)
            rejection_type = matcher.check_rejection_type()

            # If rejected with no commitment, return None
            if rejection_type and not matcher.check_committed():
                return None

            # If only commitment stated but no actual proposals, return None
            if matcher.check_committed() and not (
                matcher.check_adopted() or matcher.check_applicable()
            ):
                # Check if there are actual proposals mentioned in follow-up section
                follow_up_section = soup.find("h2", id="Follow-up")
                if not follow_up_section:
                    return None

            # Extract all legislative actions
            actions = []

            # Find Answer and Follow-up sections
            answer_section = self._find_answer_section(soup)
            follow_up_section = soup.find("h2", id="Follow-up") or soup.find(
                "h2", string=re.compile(r"Follow[- ]up", re.IGNORECASE)
            )
            updates_section = soup.find(
                "h2", id="Updates-on-the-Commissions-proposals"
            ) or soup.find("h2", string=re.compile(r"Updates.*proposal", re.IGNORECASE))

            # Section priorities: Updates > Follow-up > Answer
            search_sections = []
            if updates_section:
                search_sections.append(updates_section)
            if follow_up_section:
                search_sections.append(follow_up_section)
            if answer_section:
                search_sections.append(answer_section)

            # Extract actions from each section
            for section in search_sections:
                section_actions = self._extract_actions_from_section(section)
                actions.extend(section_actions)

            # If no actions found, return None
            if not actions:
                return None

            # Remove duplicates (same type, description, and date)
            unique_actions = []
            seen = set()
            for action in actions:
                key = (
                    action.get("type", ""),
                    action.get("description", ""),
                    action.get("date", ""),
                )
                if key not in seen:
                    seen.add(key)
                    unique_actions.append(action)

            return json.dumps(unique_actions, ensure_ascii=False, indent=2)

        except Exception as e:
            raise ValueError(
                f"Error extracting legislative action for {self.registration_number}: {str(e)}"
            ) from e

    def _extract_actions_from_section(self, section) -> list:
        """
        Extract legislative actions from a specific section

        Args:
            section: BeautifulSoup element of the section
            section_type: Type of section ('answer', 'follow_up', 'updates')

        Returns:
            List of action dictionaries
        """
        actions = []

        # Build action patterns from LegislativeStatus
        action_patterns = []
        for status in LegislativeStatus.ALL_STATUSES:
            for pattern in status.action_patterns:
                action_patterns.append(
                    {
                        "pattern": pattern,
                        "status_obj": status,  # Store the Status object
                    }
                )

        # Iterate through siblings after section header
        for sibling in section.find_next_siblings():
            # Stop at next h2 section
            if sibling.name == "h2":
                break

            # Process paragraphs and standalone list items
            if sibling.name in ["p", "li"]:
                self._process_element_for_legislative_action(
                    sibling, action_patterns, actions
                )

            elif sibling.name in ["ul", "ol"]:
                # Process each list item individually
                for li in sibling.find_all("li", recursive=False):
                    self._process_element_for_legislative_action(
                        li, action_patterns, actions
                    )

        return actions

    def _process_element_for_legislative_action(
        self, element, action_patterns: list, actions: list
    ):
        """Process a single HTML element (p or li) for legislative actions"""

        # Get text with newlines separating each tag
        text = element.get_text(separator="\n", strip=True)

        # NORMALIZE WHITESPACE: Replace multiple whitespace (including newlines) with single space
        text = re.sub(r"\s+", " ", text).strip()

        # Skip non-legislative content using the class method
        if NonLegislativeAction.should_skip_for_legislative(text):
            return

        text_lower = text.lower()

        # Find ALL matching patterns, then pick the most specific status
        matches = []
        for pattern_info in action_patterns:
            if re.search(
                pattern_info["pattern"], text_lower, re.IGNORECASE | re.DOTALL
            ):
                matches.append(pattern_info)

        if not matches:
            return

        # Pick the pattern with highest priority status (lower priority number = higher priority)
        best_match = min(matches, key=lambda p: p["status_obj"].priority)

        action = self._parse_legislative_action(element, text, best_match)
        if action:
            actions.append(action)

    def _parse_legislative_action(
        self, element, text: str, pattern_info: dict
    ) -> Optional[dict]:
        """
        Parse a legislative action from text element.

        Args:
            element: BeautifulSoup element containing the action
            text: Text content
            pattern_info: Pattern information dictionary with status_obj

        Returns:
            Action dictionary or None
        """
        MONTH_NAMES_PATTERN = "|".join(calendar.month_name[1:])

        # Extract dates from text
        date_patterns = [
            rf"(\d{{1,2}}\s+(?:{MONTH_NAMES_PATTERN})\s+\d{{4}})",  # 12 January 2023
            rf"(?:in|by|from)\s+((?:{MONTH_NAMES_PATTERN})\s+\d{{4}})",  # in May 2024
            r"(\d{1,2}/\d{1,2}/\d{4})",  # 15/03/2022
            r"(\d{4}-\d{2}-\d{2})",  # 2023-01-12
            r"(?:by|in|from)\s+(\d{{4}})",  # in 2024
            r"(?:by|in|from)\s+(?:end\s+of\s+)?(\d{{4}})",  # by end of 2024
        ]

        found_date = None
        status_obj = pattern_info["status_obj"]

        text_lower = text.lower()

        # Get keywords from the Status object
        keywords = status_obj.keywords

        # Try to find date in context of status keyword
        best_date = None
        best_priority = 0

        for keyword, priority in keywords:
            if keyword not in text_lower:
                continue

            # Find the position of the keyword
            keyword_pos = text_lower.find(keyword)

            # Extract text starting from keyword position
            text_from_keyword = text[keyword_pos:]

            # Find the end of the sentence/clause (., ; or end of text)
            clause_end = len(text_from_keyword)
            for delimiter in [". ", "; "]:
                pos = text_from_keyword.find(delimiter)
                if pos != -1 and pos < clause_end:
                    clause_end = pos

            # Extract the clause containing the keyword
            clause = text_from_keyword[: clause_end + 1]

            # Try to find a date in this clause
            for date_pattern in date_patterns:
                match = re.search(date_pattern, clause, re.IGNORECASE)
                if match:
                    date_str = match.group(1)
                    parsed = parse_date_string(date_str)
                    if parsed:
                        # Update if this is higher priority
                        if priority > best_priority:
                            best_date = parsed
                            best_priority = priority
                        break

        found_date = best_date

        # Fallback: if no date found near status keyword, try the whole text
        if not found_date:
            for date_pattern in date_patterns:
                match = re.search(date_pattern, text, re.IGNORECASE)
                if match:
                    date_str = match.group(1)
                    parsed = parse_date_string(date_str)
                    if parsed:
                        found_date = parsed
                        break

        # Extract action type and description
        action_type = self._extract_action_type(text)
        description = self._extract_action_description(text)

        # Get document URLs if any
        doc_url = None
        link = element.find("a", href=True)
        if link:
            href = link.get("href", "")
            if "eur-lex" in href or "europa.eu" in href:
                doc_url = href

        action = {
            "type": action_type,
            "description": description,
            "status": status_obj.name,  # Use the status name from Status object
        }

        if found_date:
            action["date"] = found_date

        if doc_url:
            action["document_url"] = doc_url

        return action

    def _extract_action_type(self, text: str) -> str:
        """Extract the type of legislative action"""
        text_lower = text.lower()

        # Specific type patterns
        if "tariff codes" in text_lower or "tariff code" in text_lower:
            return "Tariff Codes Creation"

        elif "standards" in text_lower and (
            "minimum" in text_lower or "hygiene" in text_lower
        ):
            return "Standards Adoption"

        elif (
            "revision" in text_lower
            or "revised" in text_lower
            or "recast" in text_lower
        ):
            if "directive" in text_lower:
                return "Directive Revision"
            elif "regulation" in text_lower:
                return "Regulation Revision"
            else:
                return "Legislative Revision"

        elif "amendment" in text_lower:
            return "Amendment"

        elif "proposal" in text_lower or "proposed" in text_lower:
            if "regulation" in text_lower:
                return "Regulation Proposal"
            elif "directive" in text_lower:
                return "Directive Proposal"
            elif "law" in text_lower:
                return "Law Proposal"
            else:
                return "Legislative Proposal"

        elif "adopted" in text_lower or "adoption" in text_lower:
            if "regulation" in text_lower:
                return "Regulation Adoption"
            elif "directive" in text_lower:
                return "Directive Adoption"
            elif "law" in text_lower:
                return "Law Adoption"
            else:
                return "Legislative Adoption"

        elif "entered into force" in text_lower or "became applicable" in text_lower:
            return "Law Entered Into Force"

        elif "withdrawn" in text_lower or "withdraw" in text_lower:
            if "regulation" in text_lower:
                return "Regulation Withdrawal"
            elif "directive" in text_lower:
                return "Directive Withdrawal"
            else:
                return "Proposal Withdrawal"
        else:
            return "Legislative Action"

    def _extract_action_description(self, text: str) -> str:
        """Extract a clean description of the action"""
        # Clean up the text
        text = re.sub(r"\s+", " ", text).strip()

        return text.strip()

    def extract_non_legislative_action(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Extract non-legislative actions as JSON array
        Each item contains: type, description, date
        Returns JSON string or None
        """
        try:

            # Find Answer and Follow-up sections
            answer_section = self._find_answer_section(soup)
            follow_up_section = soup.find("h2", id="Follow-up") or soup.find(
                "h2", string=re.compile(r"Follow[- ]up", re.IGNORECASE)
            )

            # Section priorities: Follow-up > Answer
            search_sections = []
            if follow_up_section:
                search_sections.append(follow_up_section)
            if answer_section:
                search_sections.append(answer_section)

            if not search_sections:
                return None

            # Extract actions from each section
            actions = []
            for section in search_sections:
                section_actions = self._extract_non_legislative_actions_from_section(
                    section
                )
                actions.extend(section_actions)

            # If no actions found, return None
            if not actions:
                return None

            # Remove duplicates (same type, description, and date)
            unique_actions = []
            seen = set()
            for action in actions:
                key = (
                    action.get("type", ""),
                    action.get("description", ""),
                    action.get("date", ""),
                )
                if key not in seen:
                    seen.add(key)
                    unique_actions.append(action)

            return json.dumps(unique_actions, ensure_ascii=False, indent=2)

        except Exception as e:
            raise ValueError(
                f"Error extracting non-legislative action for {self.registration_number}: {str(e)}"
            ) from e

    def _extract_non_legislative_actions_from_section(self, section) -> list:
        """
        Extract non-legislative actions from a specific section

        Args:
            section: BeautifulSoup element of the section

        Returns:
            List of action dictionaries
        """
        actions = []

        # Iterate through siblings after section header
        current = section.next_sibling

        while current:
            # Stop at next h2 section
            if hasattr(current, "name") and current.name == "h2":
                break

            if not hasattr(current, "name"):
                current = current.next_sibling
                continue

            # Process paragraph elements
            if current.name == "p":
                self._process_element_for_non_legislative_action(current, actions)

            # Process unordered lists
            elif current.name == "ul":
                list_items = current.find_all("li", recursive=False)
                for li in list_items:
                    self._process_element_for_non_legislative_action(li, actions)

            # Process ordered lists
            elif current.name == "ol":
                list_items = current.find_all("li", recursive=False)
                for li in list_items:
                    self._process_element_for_non_legislative_action(li, actions)

            current = current.next_sibling

        return actions

    def _process_element_for_non_legislative_action(self, element, actions: list):
        """Process a single HTML element (p or li) for non-legislative actions"""

        # Get text with normalized whitespace
        text = element.get_text(separator=" ", strip=True)
        text = re.sub(r"\s+", " ", text).strip()
        text_lower = text.lower()

        # Skip if empty or too short
        if len(text) < 20:
            return

        # Section headers end with ':' and are short (< 100 chars)
        if text.endswith(":") and len(text) < 100:
            return

        # Skip legislative keywords (these belong to legislative actions)
        legislative_keywords = [
            "entered into force",
            "became applicable",
            "withdrawal",
            "decided not to submit a legislative proposal",
            "come forward with a legislative proposal",
            "table a legislative proposal",
            "no new legislation",
            "came into force on",
            "amendment to the directive",
            "amendment to the regulation",
            "amending directive",
            "amending regulation",
            "revision of legislation",
            "labelling requirements",
            "mandatory labelling",
        ]

        header_sections = [
            "transparency and benchmarking:",
            "Implementation and review of existing EU legislation:",
        ]

        # If contains legislative keywords, skip (unless it's about enforcement)
        if any(keyword in text_lower for keyword in legislative_keywords):
            return

        # other trouble phrases
        if any(keyword in text_lower for keyword in header_sections):
            return

        # Classify the text using NonLegislativeAction
        action_type = NonLegislativeAction.classify_text(text)

        # If no pattern matched, skip
        if not action_type:
            return

        # Parse the action
        action = self._parse_non_legislative_action(text, action_type)
        if action:
            actions.append(action)

    def _parse_non_legislative_action(
        self, text: str, pattern_info: dict
    ) -> Optional[dict]:
        """
        Parse a non-legislative action from text element.

        Args:
            text: Text content
            pattern_info: Pattern information dictionary

        Returns:
            Action dictionary or None
        """

        MONTH_NAMES_PATTERN = "|".join(calendar.month_name[1:])

        # Extract dates from text
        date_patterns = [
            rf"(\d{{1,2}}\s+(?:{MONTH_NAMES_PATTERN})\s+\d{{4}})",  # 12 January 2023
            rf"(?:in|by|from)\s+((?:{MONTH_NAMES_PATTERN})\s+\d{{4}})",  # in May 2024
            r"(\d{1,2}/\d{1,2}/\d{4})",  # 15/03/2022
            r"(\d{4}-\d{2}-\d{2})",  # 2023-01-12
            r"(?:by|in|from)\s+(\d{{4}})",  # in 2024
            r"(?:by|in|from)\s+(?:end\s+of\s+)?(\d{{4}})",  # by end of 2024
        ]

        found_date = None

        # Try to find date in text
        for date_pattern in date_patterns:
            match = re.search(date_pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                parsed = parse_date_string(date_str)
                if parsed:
                    found_date = parsed
                    break

        # Extract clean description (first sentence or up to 300 chars)
        description = self._extract_action_description(text)

        # Build action dictionary
        action = {"type": pattern_info.name, "description": description}

        if found_date:
            action["date"] = found_date

        return action

```

`./ECI_initiatives/extractor/responses/parser/extractors/parliament.py`:
```
"""
Extracts European Parliament engagement data including
hearing dates, plenary debate information,
and associated video recording URLs.
"""

import calendar
import html
import re
import json
from typing import Optional

from bs4 import BeautifulSoup

from ..base.base_extractor import BaseExtractor
from ..consts.dates import month_map

from .submission import SubmissionDataExtractor


class ParliamentActivityExtractor(BaseExtractor):
    """Extracts Parliament hearing and plenary debate data"""

    def extract_parliament_hearing_date(self, soup: BeautifulSoup) -> str:
        """Extracts and normalizes the European Parliament hearing date"""
        try:
            submission_text_extractor = SubmissionDataExtractor(
                self.logger, self.registration_number
            )
            submission_text = submission_text_extractor.extract_submission_text(soup)

            if not submission_text or not submission_text.strip():
                raise ValueError("No submission text found in HTML.")

            text = submission_text.lower()
            text = re.sub(r"\s+", " ", text).strip()

            key_phrases = [
                "public hearing took place",
                "public hearing at the european parliament",
                "presentation of this initiative in a public hearing",
                "public hearing",
            ]

            sentences = re.split(r"(?<=[.!?])\s+", text)
            target_sentence = None
            matched_phrase = None

            for sent in sentences:
                for phrase in key_phrases:
                    if phrase in sent:
                        target_sentence = sent
                        matched_phrase = phrase
                        break
                if target_sentence:
                    break

            if not target_sentence:
                raise ValueError("No sentence found containing any key phrase.")

            idx = target_sentence.find(matched_phrase)
            segment_after = target_sentence[idx + len(matched_phrase) :]

            month_names = [m.lower() for m in calendar.month_name if m]
            month_abbrs = [m.lower() for m in calendar.month_abbr if m]
            all_months = month_names + month_abbrs

            # Pattern 1: Matches date format "24 January 2023" or "5 April 2023"
            # Pattern 2: Matches date format "17/02/2014" or "5-3-2020"
            # Pattern 3: Matches ISO date format "2023-01-24" or "2020/12/31"
            patterns = [
                rf'\b(\d{{1,2}})\s+({"|".join(all_months)})\s+(\d{{4}})\b',
                r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b",
                r"\b(\d{4})[/-](\d{1,2})[/-](\d{1,2})\b",
            ]

            date_match = None
            for pat in patterns:
                m = re.search(pat, segment_after)
                if m:
                    date_match = m
                    pattern = pat
                    break

            if not date_match:
                raise ValueError("No date found after key phrase.")

            if pattern == patterns[0]:
                day, month_name, year = date_match.groups()
                month = month_map.get(month_name.lower())
                if not month:
                    raise ValueError(f"Invalid month name: {month_name}")
                date_str = f"{day.zfill(2)}-{month}-{year}"
            elif pattern == patterns[1]:
                day, month, year = date_match.groups()
                date_str = f"{day.zfill(2)}-{month.zfill(2)}-{year}"
            else:
                year, month, day = date_match.groups()
                date_str = f"{day.zfill(2)}-{month.zfill(2)}-{year}"

            return date_str

        except Exception as e:
            raise ValueError(
                f"Error extracting parliament hearing date for {self.registration_number}: {str(e)}"
            ) from e

    def extract_parliament_hearing_video_urls(self, soup: BeautifulSoup) -> dict:
        """Extracts all relevant video recording URLs from the 'public hearing' paragraph"""
        try:
            submission_section = soup.find("h2", id="Submission-and-examination")
            if not submission_section:
                submission_section = soup.find(
                    "h2",
                    string=re.compile(r"Submission and examination", re.IGNORECASE),
                )
            if not submission_section:
                raise ValueError(
                    f"No submission section found for {self.registration_number}"
                )

            for sibling in submission_section.find_next_siblings():
                if sibling.name == "h2":
                    break
                if sibling.name != "p":
                    continue

                paragraph_text = html.unescape(
                    " ".join(sibling.stripped_strings)
                ).lower()

                key_phrases = [
                    "public hearing took place",
                    "public hearing at the european parliament",
                    "presentation of this initiative in a public hearing",
                    "public hearing",
                ]

                if not any(phrase in paragraph_text for phrase in key_phrases):
                    continue

                links_data = {}
                for link in sibling.find_all("a", href=True):
                    link_text = html.unescape(link.get_text(strip=True)).lower()
                    href = html.unescape(link["href"].strip())

                    if link_text and href:
                        links_data[link_text] = href

                if links_data:
                    return links_data

            raise ValueError(
                f"No parliament hearing paragraph with links found for {self.registration_number}"
            )

        except Exception as e:
            raise ValueError(
                "Error extracting parliament hearing recording URLs for "
                f"{self.registration_number}: {str(e)}"
            ) from e

    def extract_plenary_debate_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract date of plenary debate in Parliament"""
        try:
            submission_section = soup.find("h2", id="Submission-and-examination")
            if not submission_section:
                submission_section = soup.find(
                    "h2",
                    string=re.compile(r"Submission and examination", re.IGNORECASE),
                )
            if not submission_section:
                raise ValueError(
                    f"No submission section found for {self.registration_number}"
                )

            paragraphs = submission_section.find_next_siblings("p")

            debate_keywords = [
                "initiative was debated at the European Parliament",
                "debate on this initiative was held in the plenary session",
            ]

            debate_paragraph = None
            for p in paragraphs:
                text = p.get_text(separator=" ", strip=True)
                text = re.sub(r"\s+", " ", text)

                if any(keyword in text for keyword in debate_keywords):
                    debate_paragraph = text
                    break

            if not debate_paragraph:
                return None

            month_dict = {
                calendar.month_name[i].lower(): str(i).zfill(2) for i in range(1, 13)
            }

            date_pattern = (
                r"plenary session\s+"
                r"(?:of\s+the\s+)?"
                r"(?:European\s+Parliament\s+)?on\s+"
                r"(\d{1,2})\s+(\w+)\s+(\d{4})"
            )
            match = re.search(date_pattern, debate_paragraph, re.IGNORECASE)

            if match:
                day = match.group(1).zfill(2)
                month_name = match.group(2).lower()
                year = match.group(3)

                month_str = month_dict.get(month_name)
                if month_str is None:
                    raise ValueError(f"Invalid month name: {month_name}")

                return f"{day}-{month_str}-{year}"

            date_pattern_slash = (
                r"plenary session\s+"
                r"(?:of\s+the\s+)?"
                r"(?:European\s+Parliament\s+)?on\s+"
                r"(\d{1,2})/(\d{1,2})/(\d{4})"
            )
            match = re.search(date_pattern_slash, debate_paragraph, re.IGNORECASE)

            if match:
                day = match.group(1).zfill(2)
                month = match.group(2).zfill(2)
                year = match.group(3)
                return f"{day}-{month}-{year}"

            return None

        except Exception as e:
            raise ValueError(
                f"Error extracting plenary debate date for {self.registration_number}: {str(e)}"
            ) from e

    def extract_plenary_debate_video_urls(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract video recording URL of plenary debate as JSON"""
        try:
            submission_section = soup.find("h2", id="Submission-and-examination")
            if not submission_section:
                submission_section = soup.find(
                    "h2",
                    string=re.compile(r"Submission and examination", re.IGNORECASE),
                )
            if not submission_section:
                raise ValueError(
                    f"No submission section found for {self.registration_number}"
                )

            paragraphs = submission_section.find_next_siblings("p")

            debate_keywords = [
                "initiative was debated at the European Parliament",
                "debate on this initiative was held in the plenary session",
            ]

            debate_paragraph = None
            for p in paragraphs:
                text = p.get_text(separator=" ", strip=True)
                text = re.sub(r"\s+", " ", text)

                if any(keyword in text for keyword in debate_keywords):
                    debate_paragraph = p
                    break

            if not debate_paragraph:
                return None

            links = debate_paragraph.find_all("a")

            if not links:
                return None

            links_dict = {}
            for link in links:
                link_text = link.get_text(strip=True)
                link_url = link.get("href", "")

                if link_text and link_url:
                    links_dict[link_text] = link_url

            if not links_dict:
                return None

            return json.dumps(links_dict)

        except Exception as e:
            raise ValueError(
                "Error extracting plenary debate recording URL for "
                f"{self.registration_number}: {str(e)}"
            ) from e

```

`./ECI_initiatives/extractor/responses/parser/extractors/response.py`:
```
"""
Extracts European Commission response details including
communication adoption dates, document URLs, and
answer text from successful ECI pages.
"""

import calendar
import re
import json
from typing import Optional

from bs4 import BeautifulSoup

from ..base.base_extractor import BaseExtractor
from ..consts.dates import month_map


class CommissionResponseExtractor(BaseExtractor):
    """Extracts Commission communication and response data"""

    def extract_official_communication_adoption_date(
        self, soup: BeautifulSoup
    ) -> Optional[str]:
        """Extract date Commission adopted official Communication"""
        try:
            submission_section = soup.find("h2", id="Submission-and-examination")

            if not submission_section:
                submission_section = soup.find(
                    "h2",
                    string=re.compile(r"Submission and examination", re.IGNORECASE),
                )
            if not submission_section:
                raise ValueError(
                    f"No submission section found for {self.registration_number}"
                )

            paragraphs = submission_section.find_next_siblings("p")

            commission_paragraph = None
            for p in paragraphs:
                text = p.get_text(separator=" ", strip=True)
                text = re.sub(r"\s+", " ", text)

                if "Commission adopted a Communication on" in text:
                    commission_paragraph = text
                    break

            if not commission_paragraph:
                return None

            date_pattern = (
                r"Commission adopted a Communication on\s+(\d{1,2})\s+(\w+)\s+(\d{4})"
            )
            match = re.search(date_pattern, commission_paragraph, re.IGNORECASE)

            if match:
                day = match.group(1).zfill(2)
                month_name = match.group(2).lower()
                year = match.group(3)

                month_str = month_map.get(month_name)
                if month_str is None:
                    raise ValueError(f"Invalid month name: {month_name}")

                return f"{day}-{month_str}-{year}"

            date_pattern_slash = (
                r"Commission adopted a Communication on\s+(\d{1,2})/(\d{1,2})/(\d{4})"
            )
            match = re.search(date_pattern_slash, commission_paragraph, re.IGNORECASE)

            if match:
                day = match.group(1).zfill(2)
                month = match.group(2).zfill(2)
                year = match.group(3)
                return f"{day}-{month}-{year}"

            return None

        except Exception as e:
            raise ValueError(
                "Error extracting commission communication date for "
                f"{self.registration_number}: {str(e)}"
            ) from e

    def extract_official_communication_document_urls(
        self, soup: BeautifulSoup
    ) -> Optional[str]:
        """Extract link to full PDF of Commission Communication as JSON"""
        try:
            submission_section = soup.find("h2", id="Submission-and-examination")
            if not submission_section:
                submission_section = soup.find(
                    "h2",
                    string=re.compile(r"Submission and examination", re.IGNORECASE),
                )
            if not submission_section:
                raise ValueError(
                    f"No submission section found for {self.registration_number}"
                )

            paragraphs = submission_section.find_next_siblings("p")

            commission_paragraph_element = None
            for p in paragraphs:
                text = p.get_text(separator=" ", strip=True)
                text = re.sub(r"\s+", " ", text)

                if re.search(
                    r"Commission\s+adopted\s+a\s+Communication\s+on",
                    text,
                    re.IGNORECASE,
                ):
                    commission_paragraph_element = p
                    break

            if not commission_paragraph_element:
                return None

            links = commission_paragraph_element.find_all("a")

            if not links:
                return None

            links_dict = {}
            for link in links:
                link_text = link.get_text(strip=True)
                link_url = link.get("href", "")

                if link_text and link_url:
                    links_dict[link_text] = link_url

            if not links_dict:
                return None

            exclude_patterns = [
                r"https?://ec\.citizens-initiative\.europa\.eu/public/initiatives/successful/details/\d{4}/\d{6}(_[a-z]{2})?/?$",
                r"https?://citizens-initiative\.europa\.eu/initiatives/details/\d{4}/\d{6}[_]?[a-z]{2}/?$",
            ]

            filtered_links_dict = {}
            for text, url in links_dict.items():
                should_exclude = False
                for pattern in exclude_patterns:
                    if re.match(pattern, url):
                        should_exclude = True
                        break

                if not should_exclude:
                    filtered_links_dict[text] = url

            if not filtered_links_dict:
                return None

            return json.dumps(filtered_links_dict)

        except Exception as e:
            raise ValueError(
                "Error extracting commission communication URL for "
                f"{self.registration_number}: {str(e)}"
            ) from e

    def extract_commission_answer_text(self, soup: BeautifulSoup) -> str:
        """Extract main conclusions text from Communication, excluding factsheet downloads

        Raises:
            ValueError: If the Commission answer section cannot be found or extracted
        """
        try:
            # Find the "Answer of the European Commission" header
            answer_header = soup.find("h2", id="Answer-of-the-European-Commission")

            if not answer_header:
                # Alternative: find h2 containing the text
                answer_header = soup.find(
                    "h2",
                    string=lambda text: text
                    and "Answer of the European Commission" in text,
                )

            if not answer_header:
                raise ValueError(
                    "Could not find 'Answer of the European Commission' section for "
                    f"{self.registration_number}"
                )

            # Collect all content between this header and the Follow-up header
            content_parts = []
            current = answer_header.find_next_sibling()

            while current:
                # Stop if we hit Follow-up or another major section
                if current.name == "h2":
                    h2_id = current.get("id", "")
                    h2_text = current.get_text(strip=True)
                    if "Follow-up" in h2_text or h2_id == "Follow-up":
                        break
                    # Also stop at other major sections
                    if h2_id and h2_id != "Answer-of-the-European-Commission":
                        break

                # Skip factsheet file download components (ecl-file divs)
                if current.name == "div" and "ecl-file" in current.get("class", []):
                    current = current.find_next_sibling()
                    continue

                # Extract and format content from this element
                if current.name:
                    element_text = self._extract_element_with_links(current)
                    if element_text:
                        content_parts.append(element_text)

                current = current.find_next_sibling()

            if not content_parts:
                raise ValueError(
                    "No content found in 'Answer of the European Commission' section for "
                    f"{self.registration_number}"
                )

            return "\n".join(content_parts).strip()

        except ValueError:
            # Re-raise ValueError as-is
            raise
        except Exception as e:
            raise ValueError(
                "Error extracting communication main conclusion for "
                f"{self.registration_number}: {str(e)}"
            ) from e

    def _extract_element_with_links(self, element) -> str:
        """Helper to extract text while preserving links in markdown format"""

        if not element.name:
            return ""

        # Skip ecl-file components completely
        if element.name == "div" and "ecl-file" in element.get("class", []):
            return ""

        # For elements with links, convert to markdown
        if element.name == "a":
            link_text = element.get_text(strip=True)
            href = element.get("href", "")
            return f"[{link_text}]({href})"

        # For list items, extract with links
        if element.name == "li":
            text_parts = []
            for child in element.children:
                if hasattr(child, "name"):
                    if child.name == "a":
                        link_text = child.get_text(strip=True)
                        href = child.get("href", "")
                        text_parts.append(f"[{link_text}]({href})")
                    else:
                        child_text = child.get_text(strip=True)
                        if child_text:
                            text_parts.append(child_text)
                else:
                    child_text = str(child).strip()
                    if child_text:
                        text_parts.append(child_text)
            return " ".join(text_parts)

        # For paragraphs and other elements, process children to preserve links
        if element.find("a"):
            text_parts = []
            for child in element.descendants:
                if isinstance(child, str):
                    text = child.strip()
                    if text and text not in ["", "\n"]:
                        text_parts.append(text)
                elif hasattr(child, "name") and child.name == "a":
                    link_text = child.get_text(strip=True)
                    href = child.get("href", "")
                    if link_text:
                        text_parts.append(f"[{link_text}]({href})")
            return " ".join(text_parts)

        # Default: return plain text
        return element.get_text(strip=True)

```

`./ECI_initiatives/extractor/responses/parser/extractors/structural.py`:
```
"""
Performs structural analysis by extracting related
EU legislation references, petition platforms used, and
calculating follow-up durations.
"""

from typing import Optional

from bs4 import BeautifulSoup

from ..base.base_extractor import BaseExtractor


class StructuralAnalysisExtractor(BaseExtractor):
    """Extracts structural analysis data"""

    def extract_related_eu_legislation(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract references to specific Regulations or Directives"""
        try:
            return None
        except Exception as e:
            raise ValueError(
                f"Error extracting related EU legislation for {self.registration_number}: {str(e)}"
            ) from e

    def extract_petition_platforms_used(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract external platforms mentioned"""
        try:
            return None
        except Exception as e:
            raise ValueError(
                f"Error extracting petition platforms for {self.registration_number}: {str(e)}"
            ) from e

    def calculate_follow_up_duration_months(
        self, commission_date: Optional[str], latest_update: Optional[str]
    ) -> Optional[int]:
        """Calculate months between Commission response and latest follow-up"""
        try:
            return None
        except Exception as e:
            raise ValueError(
                f"Error calculating follow-up duration for {self.registration_number}: {str(e)}"
            ) from e

```

`./ECI_initiatives/extractor/responses/parser/extractors/submission.py`:
```
"""
Extracts submission-related data including
the submission date, normalized text content, and
news announcement URLs from the submission section.
"""

import re
from datetime import datetime
from typing import Optional

from bs4 import BeautifulSoup

from ..base.base_extractor import BaseExtractor


class SubmissionDataExtractor(BaseExtractor):
    """Extracts submission text and verification data"""

    def extract_submission_text(self, soup: BeautifulSoup) -> str:
        """Extract normalized text from all paragraphs in the submission section"""
        try:
            submission_section = soup.find("h2", id="Submission-and-examination")

            if not submission_section:
                submission_section = soup.find(
                    "h2",
                    string=re.compile(r"Submission and examination", re.IGNORECASE),
                )

            if not submission_section:
                raise ValueError(
                    f"No submission section found for {self.registration_number}"
                )

            paragraphs = []
            for sibling in submission_section.find_next_siblings():
                if sibling.name == "h2":
                    break
                if sibling.name == "p":
                    text = sibling.get_text(separator=" ", strip=True)
                    text = " ".join(text.split())
                    if text:
                        paragraphs.append(text)

            if not paragraphs:
                raise ValueError(
                    f"No paragraphs found in submission section for {self.registration_number}"
                )

            full_text = " ".join(paragraphs)
            return full_text

        except Exception as e:
            raise ValueError(
                f"Error extracting submission text for {self.registration_number}: {str(e)}"
            ) from e

    def extract_commission_submission_date(self, soup: BeautifulSoup) -> datetime.date:
        """Extract submission date from 'Submission and examination' section

        Handles two formats:
        1. DD Month YYYY (e.g., "6 October 2017")
        2. DD/MM/YYYY (e.g., "28/02/2014")

        Both formats look for text like "submitted to the [European] Commission on [DATE]"
        """
        try:
            h2 = soup.find("h2", id="Submission-and-examination")

            if h2:
                first_p = h2.find_next_sibling("p")

                if first_p:
                    text = first_p.get_text()

                    # Pattern 1: DD Month YYYY format (e.g., "6 October 2017")
                    match1 = re.search(
                        r"submitted to the (?:European )?Commission on (\d{1,2} [A-Za-z]+ \d{4})",
                        text,
                        re.IGNORECASE,
                    )

                    if match1:
                        date_str = match1.group(1)
                        date_time = datetime.strptime(date_str, "%d %B %Y")
                        return date_time.date()

                    # Pattern 2: DD/MM/YYYY format (e.g., "28/02/2014")
                    match2 = re.search(
                        r"submitted to the (?:European )?Commission on (\d{2}/\d{2}/\d{4})",
                        text,
                        re.IGNORECASE,
                    )

                    if match2:
                        date_str = match2.group(1)
                        date_time = datetime.strptime(date_str, "%d/%m/%Y")
                        return date_time.date()

            raise ValueError(
                f"No submission date found for initiative {self.registration_number}"
            )

        except ValueError:
            # Re-raise ValueError as-is (includes our custom message for test assertions)
            raise
        except Exception as e:
            # Wrap other exceptions with context
            raise ValueError(
                f"Error extracting submission date for {self.registration_number}: {str(e)}"
            ) from e

    def extract_submission_news_url(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract Commission news announcement URL about submission"""
        h2 = soup.find("h2", id="Submission-and-examination")

        if h2:
            first_p = h2.find_next_sibling("p")

            if first_p:
                links = first_p.find_all("a")

                for link in links:
                    href = link.get("href", "")
                    link_text = link.get_text().strip().lower()

                    if any(
                        keyword in link_text
                        for keyword in ["press", "announcement", "news"]
                    ):
                        if "presscorner" in href or "europa.eu/rapid" in href:
                            return href

        raise ValueError(
            f"No submission news URL found for initiative {self.registration_number}"
        )

```

`./ECI_initiatives/extractor/responses/parser/extractors/timeline.py`:
```
"""
Extracts procedural timeline milestones including
Commission meeting dates and
officials met during the Article 15 consultation process.
"""

import calendar
import re
from datetime import datetime
from typing import Optional

from bs4 import BeautifulSoup

from ..base.base_extractor import BaseExtractor


class ProceduralTimelineExtractor(BaseExtractor):
    """Extracts procedural timeline milestones"""

    def extract_commission_meeting_date(self, soup: BeautifulSoup) -> str:
        """Extract date of meeting with Commission officials (Article 15)"""
        try:
            submission_section = soup.find("h2", id="Submission-and-examination")

            if not submission_section:
                submission_section = soup.find(
                    "h2",
                    string=re.compile(r"Submission and examination", re.IGNORECASE),
                )

            if not submission_section:
                raise ValueError(
                    f"No submission section for {self.registration_number}"
                )

            paragraphs = []
            for sibling in submission_section.find_next_siblings():
                if sibling.name == "h2":
                    break
                if sibling.name == "p":
                    paragraphs.append(sibling)

            month_names = "|".join(calendar.month_name[1:])
            date_pattern_month_name = (
                rf"(?:On|on)\s+(\d{{1,2}}\s+(?:{month_names})\s+\d{{4}})"
            )
            # error if not f-string
            date_pattern_slash = rf"(?:On|on)\s+(\d{{2}}/\d{{2}}/\d{{4}})"

            for p in paragraphs:
                text = p.get_text(strip=True)

                if (
                    "organisers met with" in text
                    or "organisers were given the opportunity" in text
                ):
                    if "Commission" in text and (
                        "Vice-President" in text
                        or "Commissioner" in text
                        or "officials" in text
                    ):
                        match = re.search(date_pattern_month_name, text, re.IGNORECASE)
                        if match:
                            date_str = match.group(1)
                            try:
                                date_obj = datetime.strptime(date_str, "%d %B %Y")
                                return date_obj.strftime("%Y-%m-%d")
                            except ValueError:
                                return date_str

                        match = re.search(date_pattern_slash, text, re.IGNORECASE)
                        if match:
                            date_str = match.group(1)
                            try:
                                date_obj = datetime.strptime(date_str, "%d/%m/%Y")
                                return date_obj.strftime("%Y-%m-%d")
                            except ValueError:
                                return date_str

            raise ValueError(
                "No commission meeting date found in submission section for "
                f"{self.registration_number}."
            )

        except Exception as e:
            raise ValueError(
                "Error extracting commission meeting date for "
                f"{self.registration_number}:{str(e)}"
            ) from e

    def extract_commission_officials_met(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract names and titles of Commissioners/Vice-Presidents who met"""
        try:
            submission_section = soup.find("h2", id="Submission-and-examination")

            if not submission_section:
                submission_section = soup.find(
                    "h2",
                    string=re.compile(r"Submission and examination", re.IGNORECASE),
                )

            if not submission_section:
                raise ValueError(
                    f"No submission section for {self.registration_number}"
                )

            paragraphs = []
            for sibling in submission_section.find_next_siblings():
                if sibling.name == "h2":
                    break
                if sibling.name == "p":
                    paragraphs.append(sibling)

            month_names = "|".join(calendar.month_name[1:])
            date_pattern_month = rf"\d{{1,2}}\s+(?:{month_names})\s+\d{{4}}"
            date_pattern_slash = r"\d{2}/\d{2}/\d{4}"
            combined_date_pattern = f"(?:{date_pattern_month}|{date_pattern_slash})"

            for p in paragraphs:
                text = p.get_text(strip=True)

                if (
                    "organisers met with" in text
                    or "organisers were given the opportunity" in text
                ):
                    if "Commission" in text and (
                        "Vice-President" in text
                        or "Commissioner" in text
                        or "officials" in text
                    ):
                        officials_text = None

                        if "met with" in text:
                            pattern = (
                                rf"met with\s+(.+?)\s+on\s+{combined_date_pattern}"
                            )
                            match = re.search(pattern, text, re.IGNORECASE)
                            if match:
                                officials_text = match.group(1).strip()

                        if not officials_text and "meeting with" in text:
                            match = re.search(
                                r"meeting with\s+(.+?)\s+and European Commission officials",
                                text,
                                re.IGNORECASE,
                            )
                            if match:
                                officials_text = match.group(1).strip()

                        if officials_text:
                            officials_text = re.sub(
                                r"^the\s+European\s+Commission\s+",
                                "",
                                officials_text,
                                flags=re.IGNORECASE,
                            )
                            officials_text = re.sub(
                                r"^European\s+Commission\s+",
                                "",
                                officials_text,
                                flags=re.IGNORECASE,
                            )
                            officials_text = re.sub(
                                r"^Commission\s+",
                                "",
                                officials_text,
                                flags=re.IGNORECASE,
                            )
                            officials_text = re.sub(
                                r"\bFirst\s+Vice-President\b",
                                "Vice-President",
                                officials_text,
                            )

                            officials_parts = re.split(
                                r"\s+and\s+(?:the\s+)?(?=(?:Executive\s+)?Vice-President|Commissioner|Director-General|Deputy\s+Director-General)",
                                officials_text,
                            )

                            cleaned_officials = []
                            for official in officials_parts:
                                official = official.strip().rstrip(",")
                                if official:
                                    cleaned_officials.append(official)

                            result = "; ".join(cleaned_officials)
                            return result if result else None

            raise ValueError(
                f"No commission meeting found in submission section for {self.registration_number}"
            )

        except Exception as e:
            raise ValueError(
                f"Error extracting commission officials for {self.registration_number}: {str(e)}"
            ) from e

```

