"""
High-level extractors for follow-up activity information on
European Citizens’ Initiative (ECI) response pages.

It focuses on what happens after the Commission’s initial response:
concrete actions, events, and
timelines described on the follow-up page.
"""

# Python
import re
from typing import Optional, Dict, List, Union

# Third-party
from bs4 import BeautifulSoup

# Local
from ....responses.parser.extractors.followup import (
    FollowUpActivityExtractor,
)


class FollowupWebsiteFollowUpExtractor(FollowUpActivityExtractor):
    """
    Extended extractor that extracts follow-up events from the
    'Response of the Commission' section instead of the 'Follow-up' section.
    """

    def extract_followup_events_with_dates(
        self, soup: BeautifulSoup
    ) -> Optional[List[Dict[str, Union[List[str], str]]]]:
        """
        Extract follow-up actions with associated dates from Response of the Commission section.

        Extracts content from after 'Response of the Commission' h2 until
        hitting stop sections like 'Related links', 'Press release', etc.

        Args:
            soup: BeautifulSoup object of the HTML document

        Returns:
            List of dictionaries with structure:
                [
                {"dates": ["2020-01-01", "2021-01-01"],
                "action": "Following up on its commitment..."}
                , ...
                ]
            Returns None if no Response of the Commission section exists or
            no valid actions are found

        Raises:
            ValueError: If critical error occurs during extraction
        """
        try:
            # Step 1: Locate the target section
            response_h2 = soup.find("h2", id="response-of-the-commission")
            if not response_h2:
                raise ValueError(
                    f"No 'Response of the Commission' section found for {self.registration_number}"
                )

            # Step 2: Define the extraction boundary - find the next h2 after response
            start_h2 = response_h2.find_next("h2", class_="ecl-u-type-heading-2")
            if not start_h2:
                raise ValueError(
                    "No content section found after 'Response of the Commission' for "
                    f"{self.registration_number}"
                )

            # Define stop section IDs
            stop_section_ids = [
                "related-links",
                "press-release",
                "video",
            ]

            # Step 3: Extract content elements between start_h2 and stop sections
            content_elements = []
            current_element = start_h2.find_next()

            while current_element:
                # Check if we've hit a stopping h2
                if (
                    current_element.name == "h2"
                    and current_element.get("class")
                    and "ecl-u-type-heading-2" in current_element.get("class", [])
                ):
                    h2_id = current_element.get("id")

                    if h2_id in stop_section_ids:
                        break

                # Collect <p> and <li> elements (include all, not just direct children)
                if current_element.name in ["p", "li"]:
                    # Use _extract_text_with_links to preserve link URLs
                    text_with_links = self._extract_text_with_links(current_element)
                    if text_with_links and not self._should_skip_text(text_with_links):
                        content_elements.append(text_with_links)

                # Move to next element in the document tree
                current_element = current_element.find_next()

            # Step 4: Process the extracted elements
            if not content_elements:
                raise ValueError(
                    f"No valid follow-up actions found in 'Response of the Commission' section "
                    f"for {self.registration_number}"
                )

            followup_actions = []
            for element_text in content_elements:
                # Normalize whitespace
                action_text_normalized = re.sub(r"\s+", " ", element_text)

                # Extract dates from the text
                dates = self._extract_dates_from_text(action_text_normalized)

                followup_actions.append(
                    {"dates": dates, "action": action_text_normalized}
                )

            return followup_actions

        except Exception as e:
            raise ValueError(
                "Error extracting follow-up events with dates for "
                f"{self.registration_number}: {str(e)}"
            ) from e
