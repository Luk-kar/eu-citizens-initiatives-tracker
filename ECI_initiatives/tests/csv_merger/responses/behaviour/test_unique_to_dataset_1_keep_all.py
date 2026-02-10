"""
Behavioural tests for unique Response Data column merging.

This module tests merging of 14 columns unique to Response Data that should always
keep base values (immutable historical and structural metadata).

IMPORTANT: These columns do NOT exist in the Follow-up dataset, so followup values
are always empty in real-world merging scenarios and are ignored by the strategy.

Based on the ECICommissionResponseRecord data model and merge validation rules:

REQUIRED fields unique to Response Data (mandatory in base dataset):
- response_url: str
- initiative_url: str
- submission_text: str

OPTIONAL fields unique to Response Data (base may be empty):
- commission_submission_date: Optional[str]
- submission_news_url: Optional[str]
- commission_meeting_date: Optional[str]
- commission_officials_met: Optional[str]
- parliament_hearing_date: Optional[str]
- parliament_hearing_video_urls: Optional[str]
- plenary_debate_date: Optional[str]
- plenary_debate_video_urls: Optional[str]
- official_communication_adoption_date: Optional[str]
- commission_factsheet_url: Optional[str]
- has_followup_section: Optional[bool]
"""

import pytest

from ECI_initiatives.data_pipeline.csv_merger.responses.strategies import (
    merge_field_values,
    merge_keep_base_only,
    get_merge_strategy_for_field,
)
from ECI_initiatives.data_pipeline.csv_merger.responses.exceptions import (
    MandatoryFieldMissingError,
    ImmutableFieldConflictError,
)


class TestUniqueDataset1ColumnsMerging:
    """
    Tests for unique Response Data column merge strategies.

    These fields only exist in Response Data, not in Follow-up Data.
    In real merging, followup is ALWAYS null/empty for these fields.
    """

    # ========== REQUIRED FIELDS (mandatory in base dataset) ==========
    # These fields are in MANDATORY_BASE_FIELD and must have non-empty base values

    def test_response_url_keeps_base_with_null_followup(self):
        """Test response_url (required field) keeps base when followup is null."""

        base = (
            "https://citizens-initiative.europa.eu/initiatives/details/2022/000001_en"
        )
        followup = ""

        result = merge_field_values(base, followup, "response_url", "2022/000001")
        assert result == base

    def test_initiative_url_keeps_base_with_null_followup(self):
        """Test initiative_url (required field) keeps base when followup is null."""

        base = "https://citizens-initiative.europa.eu/initiatives/details/2022/000001"
        followup = ""

        result = merge_field_values(base, followup, "initiative_url", "2022/000001")
        assert result == base

    def test_submission_text_keeps_base_with_null_followup(self):
        """Test submission_text (required field) keeps base when followup is null."""

        base = """On 29 September 2021, the organisers submitted the European Citizens'
        Initiative (ECI) 'End the Cage Age' to the European Commission."""
        followup = ""

        result = merge_field_values(base, followup, "submission_text", "2022/000001")
        assert result == base

    def test_required_fields_reject_empty_base(self):
        """Test that required fields reject empty base values."""

        required_fields = ["response_url", "initiative_url", "submission_text"]

        for field in required_fields:
            with pytest.raises(MandatoryFieldMissingError) as exc_info:
                merge_field_values("", "", field, "2022/000001")

            error_msg = str(exc_info.value)
            assert field in error_msg
            assert "base" in error_msg.lower()

    # ========== OPTIONAL FIELDS (can be empty in base) ==========
    # These fields are NOT in MANDATORY_BASE_FIELD or MANDATORY_BOTH_FIELDS

    def test_commission_submission_date_keeps_base_with_null_followup(self):
        """Test commission_submission_date (Optional) keeps base when followup is null."""

        base = "2021-09-29"
        followup = None

        result = merge_field_values(
            base, followup, "commission_submission_date", "2022/000001"
        )
        assert result == base

    def test_commission_submission_date_can_be_empty(self):
        """Test commission_submission_date (Optional) can be empty in base."""

        base = ""
        followup = None

        result = merge_field_values(
            base, followup, "commission_submission_date", "2022/000001"
        )
        assert result == ""

    def test_submission_news_url_keeps_base_with_null_followup(self):
        """Test submission_news_url (Optional) keeps base when followup is null."""

        base = "https://ec.europa.eu/commission/presscorner/detail/en/ip_21_4747"
        followup = None

        result = merge_field_values(
            base, followup, "submission_news_url", "2022/000001"
        )
        assert result == base

    def test_submission_news_url_can_be_empty(self):
        """Test submission_news_url (Optional) can be empty in base."""

        base = ""
        followup = None

        result = merge_field_values(
            base, followup, "submission_news_url", "2022/000001"
        )
        assert result == ""

    def test_commission_meeting_date_keeps_base_with_null_followup(self):
        """Test commission_meeting_date (Optional) keeps base when followup is null."""

        base = "2021-10-14"
        followup = None

        result = merge_field_values(
            base, followup, "commission_meeting_date", "2022/000001"
        )
        assert result == base

    def test_commission_officials_met_keeps_base_with_null_followup(self):
        """Test commission_officials_met (Optional) keeps base when followup is null."""

        base = "Stella Kyriakides, Commissioner for Health and Food Safety; Sandra Gallina, Deputy Director-General, DG SANTE"
        followup = None

        result = merge_field_values(
            base, followup, "commission_officials_met", "2022/000001"
        )
        assert result == base

    def test_parliament_hearing_date_keeps_base_with_null_followup(self):
        """Test parliament_hearing_date (Optional) keeps base when followup is null."""

        base = "2021-11-15"
        followup = None

        result = merge_field_values(
            base, followup, "parliament_hearing_date", "2022/000001"
        )
        assert result == base

    def test_parliament_hearing_video_urls_keeps_base_with_null_followup(self):
        """Test parliament_hearing_video_urls (Optional JSON) keeps base when followup is null."""

        base = '["https://multimedia.europarl.europa.eu/video1", "https://multimedia.europarl.europa.eu/video2"]'
        followup = None

        result = merge_field_values(
            base, followup, "parliament_hearing_video_urls", "2022/000001"
        )
        assert result == base

    def test_plenary_debate_date_keeps_base_with_null_followup(self):
        """Test plenary_debate_date (Optional) keeps base when followup is null."""

        # When plenary debate happened
        base = "2022-03-09"
        followup = None

        result = merge_field_values(
            base, followup, "plenary_debate_date", "2022/000001"
        )
        assert result == base

    def test_plenary_debate_date_can_be_empty(self):
        """Test plenary_debate_date (Optional) can be empty when no debate held."""

        # No plenary debate held for this ECI
        base = ""
        followup = None

        result = merge_field_values(
            base, followup, "plenary_debate_date", "2022/000002"
        )
        assert result == ""

    def test_plenary_debate_video_urls_keeps_base_with_null_followup(self):
        """Test plenary_debate_video_urls (Optional JSON) keeps base when followup is null."""

        base = '["https://multimedia.europarl.europa.eu/plenary/debate"]'
        followup = None

        result = merge_field_values(
            base, followup, "plenary_debate_video_urls", "2022/000001"
        )
        assert result == base

    def test_official_communication_adoption_date_keeps_base_with_null_followup(self):
        """Test official_communication_adoption_date (Optional) keeps base when followup is null."""

        base = "2022-06-22"
        followup = None

        result = merge_field_values(
            base, followup, "official_communication_adoption_date", "2022/000001"
        )
        assert result == base

    def test_commission_factsheet_url_keeps_base_with_null_followup(self):
        """Test commission_factsheet_url (Optional) keeps base when followup is null."""

        base = (
            "https://ec.europa.eu/info/sites/default/files/factsheet_end_cage_age.pdf"
        )
        followup = None

        result = merge_field_values(
            base, followup, "commission_factsheet_url", "2022/000001"
        )
        assert result == base

    def test_has_followup_section_keeps_base_with_null_followup(self):
        """Test has_followup_section (Optional[bool]) keeps base when followup is null."""

        # Test with True
        base = "True"
        followup = None

        result = merge_field_values(
            base, followup, "has_followup_section", "2022/000001"
        )
        assert result == "True"

        # Test with False
        base = "False"
        followup = None

        result = merge_field_values(
            base, followup, "has_followup_section", "2022/000002"
        )
        assert result == "False"

    def test_has_followup_section_can_be_empty(self):
        """Test has_followup_section (Optional[bool]) can be empty."""

        base = ""
        followup = None

        result = merge_field_values(
            base, followup, "has_followup_section", "2022/000003"
        )
        assert result == ""

    # ========== BATCH TESTS ==========

    def test_all_optional_fields_can_be_empty(self):
        """Test that all optional fields accept empty base values with null followup."""

        optional_fields = [
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

        for field in optional_fields:
            result = merge_field_values("", None, field, "2022/000001")
            assert result == "", f"Optional field {field} should accept empty base"

    def test_multiple_optional_fields_with_values_batch(self):
        """Batch test: multiple optional fields with null followup keep base values."""

        test_cases = [
            ("commission_submission_date", "2022-01-15"),
            ("submission_news_url", "https://ec.europa.eu/news/example"),
            ("commission_meeting_date", "2021-10-14"),
            ("parliament_hearing_date", "2021-11-15"),
            ("plenary_debate_date", "2022-03-09"),
            ("commission_factsheet_url", "https://ec.europa.eu/factsheet.pdf"),
            ("has_followup_section", "True"),
        ]

        for field, base_value in test_cases:
            result = merge_field_values(base_value, None, field, "2022/000001")
            assert (
                result == base_value
            ), f"{field} should keep base when followup is null"

    def test_json_optional_fields_with_null_followup(self):
        """Test that optional JSON fields handle null followup correctly."""

        # parliament_hearing_video_urls (Optional[str] - JSON)
        result = merge_field_values(
            '["https://video1.eu", "https://video2.eu"]',
            None,
            "parliament_hearing_video_urls",
            "2022/000001",
        )
        assert result == '["https://video1.eu", "https://video2.eu"]'

        # plenary_debate_video_urls (Optional[str] - JSON)
        result = merge_field_values(
            '["https://debate-video.eu"]',
            None,
            "plenary_debate_video_urls",
            "2022/000001",
        )
        assert result == '["https://debate-video.eu"]'

        # Empty JSON arrays (valid for Optional fields)
        result = merge_field_values(
            "[]", None, "parliament_hearing_video_urls", "2022/000002"
        )
        assert result == "[]"

    # ========== STRATEGY MAPPING ==========

    def test_all_unique_fields_use_keep_base_strategy(self):
        """Test that all 14 unique Response Data fields are mapped to merge_keep_base_only."""

        unique_fields = [
            # Required
            "response_url",
            "initiative_url",
            "submission_text",
            # Optional
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

    # ========== REALISTIC ECI EXAMPLE ==========

    def test_realistic_eci_example_end_the_cage_age(self):
        """
        Test realistic ECI data: End the Cage Age initiative (2022/000001).

        Demonstrates real-world values for fields unique to Response Data.
        Mix of required and optional fields.
        """

        registration_number = "2022/000001"

        # === REQUIRED FIELDS IN BASE, NOT FOLLOWUP===

        # response_url
        result = merge_field_values(
            "https://citizens-initiative.europa.eu/initiatives/details/2022/000001_en",
            "",  # Changed from None
            "response_url",
            registration_number,
        )
        assert (
            result
            == "https://citizens-initiative.europa.eu/initiatives/details/2022/000001_en"
        )

        # initiative_url
        result = merge_field_values(
            "https://citizens-initiative.europa.eu/initiatives/details/2022/000001",
            "",  # Changed from None
            "initiative_url",
            registration_number,
        )
        assert (
            result
            == "https://citizens-initiative.europa.eu/initiatives/details/2022/000001"
        )

        # submission_text
        submission_text = """On 29 September 2021, the organisers submitted the European Citizens' 
        Initiative (ECI) 'End the Cage Age' to the European Commission. A delegation of organisers 
        met with Commission representatives on 14 October 2021. The European Parliament held a 
        public hearing on 15 November 2021."""

        result = merge_field_values(
            submission_text,
            "",  # Changed from None
            "submission_text",
            registration_number,
        )
        assert result == submission_text

        # === OPTIONAL FIELDS (keep base with null followup) ===

        # commission_submission_date
        result = merge_field_values(
            "2021-09-29", None, "commission_submission_date", registration_number
        )
        assert result == "2021-09-29"

        # submission_news_url
        result = merge_field_values(
            "https://ec.europa.eu/commission/presscorner/detail/en/ip_21_4747",
            None,
            "submission_news_url",
            registration_number,
        )
        assert (
            result == "https://ec.europa.eu/commission/presscorner/detail/en/ip_21_4747"
        )

        # commission_meeting_date
        result = merge_field_values(
            "2021-10-14", None, "commission_meeting_date", registration_number
        )
        assert result == "2021-10-14"

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

        # has_followup_section
        result = merge_field_values(
            "True", None, "has_followup_section", registration_number
        )
        assert result == "True"

    def test_realistic_eci_example_with_missing_optional_fields(self):
        """
        Test realistic ECI with some optional fields empty.

        Not all ECIs have plenary debates or factsheet URLs.
        """

        registration_number = "2019/000006"

        # Optional fields can be empty
        result = merge_field_values(
            "", None, "plenary_debate_date", registration_number
        )
        assert result == ""

        result = merge_field_values(
            "", None, "plenary_debate_video_urls", registration_number
        )
        assert result == ""

        result = merge_field_values(
            "", None, "commission_factsheet_url", registration_number
        )
        assert result == ""

    # ========== HYPOTHETICAL ERROR CASES ==========

    def test_conflict_error_if_followup_has_different_value(self):
        """
        Test that if followup somehow has a different value, error is raised.

        NOTE: This shouldn't happen in real data since these columns don't exist
        in follow-up dataset, but tests the immutable field validation logic.
        """

        # Required field conflict (would be caught by mandatory validation first)
        base = (
            "https://citizens-initiative.europa.eu/initiatives/details/2022/000001_en"
        )
        followup = "https://different-url.eu"

        with pytest.raises(ImmutableFieldConflictError):
            merge_field_values(base, followup, "response_url", "2022/000001")

        # Optional field conflict
        base = "2021-09-29"
        followup = "2021-09-30"

        with pytest.raises(ImmutableFieldConflictError):
            merge_field_values(
                base, followup, "commission_submission_date", "2022/000001"
            )
