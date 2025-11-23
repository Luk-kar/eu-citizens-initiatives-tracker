"""
Test suite for ECI model data quality: Commission response field coherence.

These tests validate commission response field coherence in extracted
European Citizens' Initiative response data.
"""

from datetime import datetime, date, timedelta
from typing import List, Optional, Any, Set
import pytest

from ECI_initiatives.extractor.responses.model import ECICommissionResponseRecord


class TestCommissionResponseFieldsCoherence:
    """Test coherence between Commission response fields"""

    def _is_empty_or_none(self, value: any) -> bool:
        """
        Check if a value is None or empty (for strings, lists, etc.).

        Args:
            value: Value to check

        Returns:
            True if value is None, empty string, empty list, "null", etc.
        """
        if value is None:
            return True

        # Handle string "null" from JSON serialization
        if isinstance(value, str):
            return value.strip() in ("", "null", "[]", "{}")

        # Handle empty containers
        if isinstance(value, (list, dict, set, tuple)):
            return len(value) == 0

        return False

    def test_commission_officials_met_when_meeting_date_exists(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """
        Verify commission_officials_met is populated when commission_meeting_date exists.

        If a Commission meeting took place (indicated by commission_meeting_date),
        there should be information about which officials participated in that meeting.
        Missing official names suggests incomplete data extraction.
        """
        missing_officials = []

        for record in complete_dataset:

            # If meeting date exists, officials should be listed
            if record.commission_meeting_date is not None:

                if self._is_empty_or_none(record.commission_officials_met):
                    missing_officials.append(
                        (
                            record.registration_number,
                            record.commission_meeting_date,
                            record.initiative_title,
                        )
                    )

        assert not missing_officials, (
            f"Found {len(missing_officials)} records with commission_meeting_date "
            f"but missing commission_officials_met:\n"
            + "\n".join(
                f"  - {reg_num} (meeting: {date}): {title[:60]}..."
                for reg_num, date, title in missing_officials
            )
            + "\n\nWhen a Commission meeting occurred, official names should be recorded."
        )

    def test_communication_urls_exist_when_adoption_date_exists(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """
        Verify official_communication_document_urls exists when adoption date is set.

        If the Commission adopted an official communication (indicated by
        official_communication_adoption_date), there should be document URLs
        linking to that communication. Missing URLs means the communication
        cannot be accessed or verified.
        """
        missing_urls = []

        for record in complete_dataset:

            # If communication was adopted, document URLs should exist
            if record.official_communication_adoption_date is not None:

                if self._is_empty_or_none(record.official_communication_document_urls):
                    missing_urls.append(
                        (
                            record.registration_number,
                            record.official_communication_adoption_date,
                            record.initiative_title,
                        )
                    )

        assert not missing_urls, (
            f"Found {len(missing_urls)} records with official_communication_adoption_date "
            f"but missing official_communication_document_urls:\n"
            + "\n".join(
                f"  - {reg_num} (adopted: {date}): {title[:60]}..."
                for reg_num, date, title in missing_urls
            )
            + "\n\nAdopted communications should have accessible document URLs for transparency."
        )

    def test_hearing_videos_exist_when_hearing_date_exists(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """
        Verify parliament_hearing_video_urls exists when hearing date is set.

        If a European Parliament hearing took place (indicated by
        parliament_hearing_date), there should be video recording URLs.
        Parliament hearings are public events that are typically recorded
        and made available online for transparency.
        """
        missing_videos = []

        for record in complete_dataset:
            # If hearing occurred, video URLs should exist
            if record.parliament_hearing_date is not None:
                if self._is_empty_or_none(record.parliament_hearing_video_urls):
                    missing_videos.append(
                        (
                            record.registration_number,
                            record.parliament_hearing_date,
                            record.initiative_title,
                        )
                    )

        assert not missing_videos, (
            f"Found {len(missing_videos)} records with parliament_hearing_date "
            f"but missing parliament_hearing_video_urls:\n"
            + "\n".join(
                f"  - {reg_num} (hearing: {date}): {title[:60]}..."
                for reg_num, date, title in missing_videos
            )
            + "\n\nParliament hearings should have accessible video URLs for transparency."
        )

    def test_plenary_videos_exist_when_debate_date_exists(
        self, complete_dataset: List[ECICommissionResponseRecord]
    ):
        """
        Verify plenary_debate_video_urls exists when debate date is set.

        If a European Parliament plenary debate took place (indicated by
        plenary_debate_date), there should be video recording URLs.
        Plenary sessions are major public events that are always recorded
        and broadcast online for citizen access.
        """
        missing_videos = []

        for record in complete_dataset:
            # If plenary debate occurred, video URLs should exist
            if record.plenary_debate_date is not None:
                if self._is_empty_or_none(record.plenary_debate_video_urls):
                    missing_videos.append(
                        (
                            record.registration_number,
                            record.plenary_debate_date,
                            record.initiative_title,
                        )
                    )

        assert not missing_videos, (
            f"Found {len(missing_videos)} records with plenary_debate_date "
            f"but missing plenary_debate_video_urls:\n"
            + "\n".join(
                f"  - {reg_num} (debate: {date}): {title[:60]}..."
                for reg_num, date, title in missing_videos
            )
            + "\n\nPlenary debates are always recorded and should have accessible video URLs."
        )
