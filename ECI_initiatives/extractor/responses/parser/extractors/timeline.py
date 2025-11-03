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
