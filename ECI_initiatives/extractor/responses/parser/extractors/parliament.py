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
from ..base.date_parser import build_month_dict

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

            month_map = build_month_dict()

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
