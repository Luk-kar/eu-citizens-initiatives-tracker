"""
Behavioural tests for unique Response Data column merging.

This module tests merging of 14 columns unique to Response Data that should always
keep base values (immutable historical and structural metadata).

IMPORTANT: These columns do NOT exist in the Follow-up dataset, so followup values
are ALWAYS null/empty in real-world merging scenarios.

Unique to Response Data:
- response_url (mandatory)
- initiative_url (mandatory)
- has_followup_section (mandatory)
- submission_text
- commission_submission_date
- submission_news_url
- commission_meeting_date
- commission_officials_met
- parliament_hearing_date
- parliament_hearing_video_urls
- plenary_debate_date
- plenary_debate_video_urls
- official_communication_adoption_date
- commission_factsheet_url
"""

import pytest

from ECI_initiatives.csv_merger.responses.strategies import (
    merge_field_values,
    merge_keep_base_only,
    get_merge_strategy_for_field,
)
from ECI_initiatives.csv_merger.responses.exceptions import (
    MandatoryFieldMissingError,
    ImmutableFieldConflictError,
)


class TestUniqueDataset1ColumnsMerging:
    """
    Tests for unique Response Data column merge strategies.

    These fields only exist in Response Data, not in Follow-up Data.
    In real merging, followup is ALWAYS null/empty for these fields.
    """

    # ========== MANDATORY FIELDS (must be non-empty in Response Data) ==========

    def test_response_url_keeps_base_with_null_followup(self):
        """Test response_url keeps base when followup is null (real-world scenario)."""

        base = (
            "https://citizens-initiative.europa.eu/initiatives/details/2022/000001_en"
        )
        followup = None  # Followup dataset doesn't have this column

        # This should raise MandatoryFieldMissingError because followup is null
        with pytest.raises(MandatoryFieldMissingError) as exc_info:
            merge_field_values(base, followup, "response_url", "2022/000001")

        assert "response_url" in str(exc_info.value)
        assert "followup" in str(exc_info.value).lower()

    def test_initiative_url_keeps_base_with_null_followup(self):
        """Test initiative_url keeps base when followup is null (real-world scenario)."""

        base = "https://citizens-initiative.europa.eu/initiatives/details/2022/000001"
        followup = None  # Followup dataset doesn't have this column

        # This should raise MandatoryFieldMissingError
        with pytest.raises(MandatoryFieldMissingError):
            merge_field_values(base, followup, "initiative_url", "2022/000001")

    def test_has_followup_section_keeps_base_with_null_followup(self):
        """Test has_followup_section keeps base when followup is null (real-world scenario)."""

        # Test with True
        base = "True"
        followup = None  # Followup dataset doesn't have this column

        with pytest.raises(MandatoryFieldMissingError):
            merge_field_values(base, followup, "has_followup_section", "2022/000001")

    def test_mandatory_fields_reject_empty_base(self):
        """Test that mandatory fields reject empty base values."""

        mandatory_fields = ["response_url", "initiative_url", "has_followup_section"]

        for field in mandatory_fields:
            with pytest.raises(MandatoryFieldMissingError) as exc_info:
                merge_field_values("", None, field, "2022/000001")

            error_msg = str(exc_info.value)
            assert field in error_msg
            assert "base" in error_msg.lower()

    # ========== NON-MANDATORY FIELDS (can be empty in Response Data) ==========

    def test_submission_text_keeps_base_with_null_followup(self):
        """Test submission_text keeps base when followup is null (real-world scenario)."""

        base = """On 29 September 2021, the organisers submitted the European Citizens'
        Initiative (ECI) 'End the Cage Age' to the European Commission."""
        followup = None  # Followup dataset doesn't have this column

        result = merge_field_values(base, followup, "submission_text", "2022/000001")
        assert result == base

    def test_commission_submission_date_keeps_base_with_null_followup(self):
        """Test commission_submission_date keeps base when followup is null."""

        base = "2021-09-29"
        followup = None

        result = merge_field_values(
            base, followup, "commission_submission_date", "2022/000001"
        )
        assert result == base

    def test_submission_news_url_keeps_base_with_null_followup(self):
        """Test submission_news_url keeps base when followup is null."""

        base = "https://ec.europa.eu/commission/presscorner/detail/en/ip_21_4747"
        followup = None

        result = merge_field_values(
            base, followup, "submission_news_url", "2022/000001"
        )
        assert result == base

    def test_commission_meeting_date_keeps_base_with_null_followup(self):
        """Test commission_meeting_date keeps base when followup is null."""

        base = "2021-10-14"
        followup = None

        result = merge_field_values(
            base, followup, "commission_meeting_date", "2022/000001"
        )
        assert result == base

    def test_commission_officials_met_keeps_base_with_null_followup(self):
        """Test commission_officials_met keeps base when followup is null."""

        base = "Stella Kyriakides, Commissioner for Health and Food Safety; Sandra Gallina, Deputy Director-General, DG SANTE"
        followup = None

        result = merge_field_values(
            base, followup, "commission_officials_met", "2022/000001"
        )
        assert result == base

    def test_parliament_hearing_date_keeps_base_with_null_followup(self):
        """Test parliament_hearing_date keeps base when followup is null."""

        base = "2021-11-15"
        followup = None

        result = merge_field_values(
            base, followup, "parliament_hearing_date", "2022/000001"
        )
        assert result == base

    def test_parliament_hearing_video_urls_keeps_base_with_null_followup(self):
        """Test parliament_hearing_video_urls keeps base when followup is null."""

        base = '["https://multimedia.europarl.europa.eu/video1", "https://multimedia.europarl.europa.eu/video2"]'
        followup = None

        result = merge_field_values(
            base, followup, "parliament_hearing_video_urls", "2022/000001"
        )
        assert result == base

    def test_plenary_debate_date_keeps_base_with_null_followup(self):
        """Test plenary_debate_date keeps base when followup is null."""

        # When plenary debate happened
        base = "2022-03-09"
        followup = None

        result = merge_field_values(
            base, followup, "plenary_debate_date", "2022/000001"
        )
        assert result == base

    def test_plenary_debate_date_empty_base_with_null_followup(self):
        """Test plenary_debate_date when no debate held (empty in both)."""

        # No plenary debate held for this ECI
        base = ""
        followup = None

        result = merge_field_values(
            base, followup, "plenary_debate_date", "2022/000002"
        )
        assert result == ""

    def test_plenary_debate_video_urls_keeps_base_with_null_followup(self):
        """Test plenary_debate_video_urls keeps base when followup is null."""

        base = '["https://multimedia.europarl.europa.eu/plenary/debate"]'
        followup = None

        result = merge_field_values(
            base, followup, "plenary_debate_video_urls", "2022/000001"
        )
        assert result == base

    def test_official_communication_adoption_date_keeps_base_with_null_followup(self):
        """Test official_communication_adoption_date keeps base when followup is null."""

        base = "2022-06-22"
        followup = None

        result = merge_field_values(
            base, followup, "official_communication_adoption_date", "2022/000001"
        )
        assert result == base

    def test_commission_factsheet_url_keeps_base_with_null_followup(self):
        """Test commission_factsheet_url keeps base when followup is null."""

        base = (
            "https://ec.europa.eu/info/sites/default/files/factsheet_end_cage_age.pdf"
        )
        followup = None

        result = merge_field_values(
            base, followup, "commission_factsheet_url", "2022/000001"
        )
        assert result == base

    # ========== EDGE CASES: Empty base values ==========

    def test_non_mandatory_fields_with_empty_base_and_null_followup(self):
        """Test non-mandatory fields can be empty in both datasets."""

        non_mandatory_fields = [
            "submission_text",
            "commission_submission_date",
            "submission_news_url",
            "commission_meeting_date",
            "commission_officials_met",
            "parliament_hearing_date",
            "parliament_hearing_video_urls",
            "plenary_debate_date",
            "plenary_debate_video_urls",
            "official_communication_adoption_date",
            "commission_factsheet_url",
        ]

        for field in non_mandatory_fields:
            result = merge_field_values("", None, field, "2022/000001")
            assert result == "", f"{field} should return empty when both are empty"

    # ========== HYPOTHETICAL ERROR CASES (shouldn't happen in real data) ==========

    def test_conflict_error_if_followup_has_different_value(self):
        """
        Test that if followup somehow has a different value, error is raised.

        NOTE: This shouldn't happen in real data since these columns don't exist
        in follow-up dataset, but tests the immutable field validation logic.
        """

        # response_url conflict (hypothetical - would be caught by mandatory validation first)
        base = (
            "https://citizens-initiative.europa.eu/initiatives/details/2022/000001_en"
        )
        followup = "https://different-url.eu"

        with pytest.raises(ImmutableFieldConflictError):
            merge_field_values(base, followup, "response_url", "2022/000001")

        # submission_text conflict
        base = "Original text"
        followup = "Different text"

        with pytest.raises(ImmutableFieldConflictError):
            merge_field_values(base, followup, "submission_text", "2022/000001")

    # ========== STRATEGY MAPPING ==========

    def test_all_unique_fields_use_keep_base_strategy(self):
        """Test that all 14 unique Response Data fields are mapped to merge_keep_base_only."""

        unique_fields = [
            "response_url",
            "initiative_url",
            "submission_text",
            "commission_submission_date",
            "submission_news_url",
            "commission_meeting_date",
            "commission_officials_met",
            "parliament_hearing_date",
            "parliament_hearing_video_urls",
            "plenary_debate_date",
            "plenary_debate_video_urls",
            "official_communication_adoption_date",
            "commission_factsheet_url",
            "has_followup_section",
        ]

        for field in unique_fields:
            strategy = get_merge_strategy_for_field(field)
            assert (
                strategy == merge_keep_base_only
            ), f"{field} should use merge_keep_base_only strategy"

    # ========== BATCH TESTS ==========

    def test_multiple_non_mandatory_fields_batch(self):
        """Batch test: multiple non-mandatory fields with null followup keep base values."""

        test_cases = [
            ("commission_submission_date", "2022-01-15"),
            ("submission_text", "Historical narrative text"),
            ("submission_news_url", "https://ec.europa.eu/news/example"),
            ("commission_meeting_date", "2021-10-14"),
            ("parliament_hearing_date", "2021-11-15"),
            ("plenary_debate_date", "2022-03-09"),
            ("commission_factsheet_url", "https://ec.europa.eu/factsheet.pdf"),
        ]

        for field, base_value in test_cases:
            result = merge_field_values(base_value, None, field, "2022/000001")
            assert (
                result == base_value
            ), f"{field} should keep base when followup is null"

    def test_json_fields_with_null_followup(self):
        """Test that JSON list fields handle null followup correctly."""

        # parliament_hearing_video_urls
        result = merge_field_values(
            '["https://video1.eu", "https://video2.eu"]',
            None,
            "parliament_hearing_video_urls",
            "2022/000001",
        )
        assert result == '["https://video1.eu", "https://video2.eu"]'

        # plenary_debate_video_urls
        result = merge_field_values(
            '["https://debate-video.eu"]',
            None,
            "plenary_debate_video_urls",
            "2022/000001",
        )
        assert result == '["https://debate-video.eu"]'

        # Empty JSON arrays
        result = merge_field_values(
            "[]", None, "parliament_hearing_video_urls", "2022/000002"
        )
        assert result == "[]"

    def test_realistic_eci_example(self):
        """
        Test realistic ECI data: End the Cage Age initiative.

        Demonstrates real-world values for fields unique to Response Data.
        """

        registration_number = "2022/000001"

        # response_url - mandatory
        with pytest.raises(MandatoryFieldMissingError):
            merge_field_values(
                "https://citizens-initiative.europa.eu/initiatives/details/2022/000001_en",
                None,
                "response_url",
                registration_number,
            )

        # submission_text - long narrative
        submission_text = """On 29 September 2021, the organisers submitted the European Citizens' 
        Initiative (ECI) 'End the Cage Age' to the European Commission. A delegation of organisers 
        met with Commission representatives on 14 October 2021. The European Parliament held a 
        public hearing on 15 November 2021."""

        result = merge_field_values(
            submission_text, None, "submission_text", registration_number
        )
        assert result == submission_text

        # parliament_hearing_date
        result = merge_field_values(
            "2021-11-15", None, "parliament_hearing_date", registration_number
        )
        assert result == "2021-11-15"

        # plenary_debate_date
        result = merge_field_values(
            "2022-03-09", None, "plenary_debate_date", registration_number
        )
        assert result == "2022-03-09"
