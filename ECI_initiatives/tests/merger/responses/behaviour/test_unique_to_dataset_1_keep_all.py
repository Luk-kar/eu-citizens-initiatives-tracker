"""
Behavioural tests for unique Dataset 1 column merging.

This module tests merging of 14 columns unique to Dataset 1 that should always
keep base values (immutable historical and structural metadata):
- response_url
- initiative_url
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
- has_followup_section
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
    """Tests for unique Dataset 1 column merge strategies."""

    def test_response_url_keeps_base(self):
        """Test that response_url always keeps base value when followup is identical."""

        # Test case 1: Valid URL in both (identical)
        base_1 = (
            "https://citizens-initiative.europa.eu/initiatives/details/2022/000001_en"
        )
        followup_1 = base_1  # Must be identical for mandatory field
        result_1 = merge_field_values(base_1, followup_1, "response_url", "2022/000001")
        assert result_1 == base_1, "Should keep base URL when both are identical"

        # Test case 2: Another example
        base_2 = (
            "https://citizens-initiative.europa.eu/initiatives/details/2019/000006_en"
        )
        followup_2 = base_2
        result_2 = merge_field_values(base_2, followup_2, "response_url", "2019/000006")
        assert result_2 == base_2, "Should keep base URL when both match"

    def test_response_url_conflict_raises_error(self):
        """Test that different response_url raises ImmutableFieldConflictError."""

        base = (
            "https://citizens-initiative.europa.eu/initiatives/details/2022/000001_en"
        )
        followup = "https://different-url.eu"

        with pytest.raises(ImmutableFieldConflictError) as exc_info:
            merge_field_values(base, followup, "response_url", "2022/000001")

        error_msg = str(exc_info.value)
        assert "response_url" in error_msg
        assert "Immutable" in error_msg

    def test_initiative_url_keeps_base(self):
        """Test that initiative_url always keeps base value when followup is identical."""

        base = "https://citizens-initiative.europa.eu/initiatives/details/2022/000001"
        followup = base  # Must be identical for mandatory field
        result = merge_field_values(base, followup, "initiative_url", "2022/000001")
        assert result == base, "Should keep canonical base initiative URL"

    def test_initiative_url_conflict_raises_error(self):
        """Test that different initiative_url raises ImmutableFieldConflictError."""

        base = "https://citizens-initiative.europa.eu/initiatives/details/2022/000001"
        followup = "https://different-url.eu"

        with pytest.raises(ImmutableFieldConflictError):
            merge_field_values(base, followup, "initiative_url", "2022/000001")

    def test_submission_text_keeps_base(self):
        """Test that submission_text (historical narrative) always keeps base value."""

        # Test case 1: Long submission text, empty followup
        base_1 = """On 29 September 2021, the organisers submitted the European Citizens'
        Initiative (ECI) 'End the Cage Age' to the European Commission. A delegation of organisers
        met with Commission representatives on 14 October 2021. The European Parliament held a
        public hearing on 15 November 2021."""
        followup_1 = ""
        result_1 = merge_field_values(
            base_1, followup_1, "submission_text", "2022/000001"
        )
        assert result_1 == base_1, "Should keep original historical submission text"

        # Test case 2: Both have same value
        base_2 = "Brief submission narrative."
        followup_2 = base_2
        result_2 = merge_field_values(
            base_2, followup_2, "submission_text", "2022/000002"
        )
        assert result_2 == base_2, "Should keep base submission text"

    def test_submission_text_conflict_raises_error(self):
        """Test that different submission_text raises ImmutableFieldConflictError."""

        base = "Original submission text"
        followup = "Updated submission information"

        with pytest.raises(ImmutableFieldConflictError):
            merge_field_values(base, followup, "submission_text", "2022/000001")

    def test_commission_submission_date_keeps_base(self):
        """Test that commission_submission_date (fixed historical date) keeps base value."""

        # Test case 1: ISO date format, empty followup
        base_1 = "2021-09-29"
        followup_1 = ""
        result_1 = merge_field_values(
            base_1, followup_1, "commission_submission_date", "2022/000001"
        )
        assert result_1 == base_1, "Should keep original submission date"

        # Test case 2: Both have same date
        base_2 = "2019-12-15"
        followup_2 = "2019-12-15"
        result_2 = merge_field_values(
            base_2, followup_2, "commission_submission_date", "2019/000006"
        )
        assert result_2 == base_2, "Should keep base date when both match"

    def test_commission_submission_date_conflict_raises_error(self):
        """Test that different dates raise ImmutableFieldConflictError."""

        base = "2021-09-29"
        followup = "2021-09-30"

        with pytest.raises(ImmutableFieldConflictError):
            merge_field_values(
                base, followup, "commission_submission_date", "2022/000001"
            )

    def test_submission_news_url_keeps_base(self):
        """Test that submission_news_url (press release link) keeps base value."""

        base = "https://ec.europa.eu/commission/presscorner/detail/en/ip_21_4747"
        followup = ""
        result = merge_field_values(
            base, followup, "submission_news_url", "2022/000001"
        )
        assert result == base, "Should keep original press release URL"

    def test_submission_news_url_conflict_raises_error(self):
        """Test that different URLs raise ImmutableFieldConflictError."""

        base = "https://ec.europa.eu/commission/presscorner/detail/en/ip_21_4747"
        followup = "https://different-press-release.eu"

        with pytest.raises(ImmutableFieldConflictError):
            merge_field_values(base, followup, "submission_news_url", "2022/000001")

    def test_commission_meeting_date_keeps_base(self):
        """Test that commission_meeting_date (procedural milestone) keeps base value."""

        base = "2021-10-14"
        followup = ""
        result = merge_field_values(
            base, followup, "commission_meeting_date", "2022/000001"
        )
        assert result == base, "Should keep original meeting date"

    def test_commission_meeting_date_conflict_raises_error(self):
        """Test that different dates raise ImmutableFieldConflictError."""

        base = "2021-10-14"
        followup = "2021-10-15"

        with pytest.raises(ImmutableFieldConflictError):
            merge_field_values(base, followup, "commission_meeting_date", "2022/000001")

    def test_commission_officials_met_keeps_base(self):
        """Test that commission_officials_met (historical record) keeps base value."""

        base = "Stella Kyriakides, Commissioner for Health and Food Safety; Sandra Gallina, Deputy Director-General, DG SANTE"
        followup = ""
        result = merge_field_values(
            base, followup, "commission_officials_met", "2022/000001"
        )
        assert result == base, "Should keep original officials list"

    def test_commission_officials_met_conflict_raises_error(self):
        """Test that different officials raise ImmutableFieldConflictError."""

        base = "Stella Kyriakides, Commissioner for Health and Food Safety"
        followup = "Different officials"

        with pytest.raises(ImmutableFieldConflictError):
            merge_field_values(
                base, followup, "commission_officials_met", "2022/000001"
            )

    def test_parliament_hearing_date_keeps_base(self):
        """Test that parliament_hearing_date (mandatory procedural date) keeps base value."""

        base = "2021-11-15"
        followup = ""
        result = merge_field_values(
            base, followup, "parliament_hearing_date", "2022/000001"
        )
        assert result == base, "Should keep original Parliament hearing date"

    def test_parliament_hearing_date_conflict_raises_error(self):
        """Test that different dates raise ImmutableFieldConflictError."""

        base = "2021-11-15"
        followup = "2021-11-16"

        with pytest.raises(ImmutableFieldConflictError):
            merge_field_values(base, followup, "parliament_hearing_date", "2022/000001")

    def test_parliament_hearing_video_urls_keeps_base(self):
        """Test that parliament_hearing_video_urls (archival links) keeps base value."""

        # Test case 1: JSON list of URLs, identical followup
        base_1 = '["https://multimedia.europarl.europa.eu/video1", "https://multimedia.europarl.europa.eu/video2"]'
        followup_1 = base_1  # Must be identical (immutable)
        result_1 = merge_field_values(
            base_1, followup_1, "parliament_hearing_video_urls", "2022/000001"
        )
        assert result_1 == base_1, "Should keep original video URLs"

        # Test case 2: Empty list in both (no hearing videos)
        base_2 = "[]"
        followup_2 = "[]"
        result_2 = merge_field_values(
            base_2, followup_2, "parliament_hearing_video_urls", "2022/000002"
        )
        assert result_2 == base_2, "Should keep empty array when both are empty"

    def test_parliament_hearing_video_urls_conflict_raises_error(self):
        """Test that different video URLs raise ImmutableFieldConflictError."""

        base = '["https://multimedia.europarl.europa.eu/video1"]'
        followup = '["https://different-video.eu"]'

        with pytest.raises(ImmutableFieldConflictError):
            merge_field_values(
                base, followup, "parliament_hearing_video_urls", "2022/000001"
            )

    def test_plenary_debate_date_keeps_base(self):
        """Test that plenary_debate_date (optional procedural milestone) keeps base value."""

        # Test case 1: Date present, empty followup
        base_1 = "2022-03-09"
        followup_1 = ""
        result_1 = merge_field_values(
            base_1, followup_1, "plenary_debate_date", "2022/000001"
        )
        assert result_1 == base_1, "Should keep original plenary debate date"

        # Test case 2: Empty (no plenary debate held)
        base_2 = ""
        followup_2 = ""
        result_2 = merge_field_values(
            base_2, followup_2, "plenary_debate_date", "2022/000002"
        )
        assert result_2 == base_2, "Should keep empty base when followup also empty"

    def test_plenary_debate_date_conflict_raises_error(self):
        """Test that conflicting dates raise ImmutableFieldConflictError."""

        # Empty base with non-empty followup
        base = ""
        followup = "2022-05-15"

        with pytest.raises(ImmutableFieldConflictError):
            merge_field_values(base, followup, "plenary_debate_date", "2022/000002")

        # Different dates
        base2 = "2022-03-09"
        followup2 = "2022-03-10"

        with pytest.raises(ImmutableFieldConflictError):
            merge_field_values(base2, followup2, "plenary_debate_date", "2022/000001")

    def test_plenary_debate_video_urls_keeps_base(self):
        """Test that plenary_debate_video_urls (archival multimedia) keeps base value."""

        base = '["https://multimedia.europarl.europa.eu/plenary/debate"]'
        followup = ""
        result = merge_field_values(
            base, followup, "plenary_debate_video_urls", "2022/000001"
        )
        assert result == base, "Should keep original plenary debate video URLs"

    def test_plenary_debate_video_urls_conflict_raises_error(self):
        """Test that different video URLs raise ImmutableFieldConflictError."""

        base = '["https://multimedia.europarl.europa.eu/plenary/debate"]'
        followup = '["https://different-debate-video.eu"]'

        with pytest.raises(ImmutableFieldConflictError):
            merge_field_values(
                base, followup, "plenary_debate_video_urls", "2022/000001"
            )

    def test_official_communication_adoption_date_keeps_base(self):
        """Test that official_communication_adoption_date (legal timestamp) keeps base value."""

        # Test case 1: Official adoption date, empty followup
        base_1 = "2022-06-22"
        followup_1 = ""
        result_1 = merge_field_values(
            base_1,
            followup_1,
            "official_communication_adoption_date",
            "2022/000001",
        )
        assert result_1 == base_1, "Should keep definitive legal adoption date"

        # Test case 2: Both have same date
        base_2 = "2019-12-15T10:30:00"
        followup_2 = "2019-12-15T10:30:00"
        result_2 = merge_field_values(
            base_2,
            followup_2,
            "official_communication_adoption_date",
            "2019/000006",
        )
        assert result_2 == base_2, "Should keep base date format"

    def test_official_communication_adoption_date_conflict_raises_error(self):
        """Test that different dates raise ImmutableFieldConflictError."""

        base = "2022-06-22"
        followup = "2022-06-23"

        with pytest.raises(ImmutableFieldConflictError):
            merge_field_values(
                base, followup, "official_communication_adoption_date", "2022/000001"
            )

    def test_commission_factsheet_url_keeps_base(self):
        """Test that commission_factsheet_url (structural metadata) keeps base value."""

        base = (
            "https://ec.europa.eu/info/sites/default/files/factsheet_end_cage_age.pdf"
        )
        followup = ""
        result = merge_field_values(
            base, followup, "commission_factsheet_url", "2022/000001"
        )
        assert result == base, "Should keep original Commission factsheet URL"

    def test_commission_factsheet_url_conflict_raises_error(self):
        """Test that different URLs raise ImmutableFieldConflictError."""

        base = (
            "https://ec.europa.eu/info/sites/default/files/factsheet_end_cage_age.pdf"
        )
        followup = "https://different-factsheet.eu"

        with pytest.raises(ImmutableFieldConflictError):
            merge_field_values(
                base, followup, "commission_factsheet_url", "2022/000001"
            )

    def test_has_followup_section_keeps_base_when_identical(self):
        """Test that has_followup_section keeps base value when both datasets have same value."""

        # Both True
        result = merge_field_values(
            "True", "True", "has_followup_section", "2022/000001"
        )
        assert result == "True"

        # Both False
        result = merge_field_values(
            "False", "False", "has_followup_section", "2022/000002"
        )
        assert result == "False"

    def test_has_followup_section_conflict_raises_error(self):
        """Test that different has_followup_section values raise ImmutableFieldConflictError."""

        # True → False: conflict
        with pytest.raises(ImmutableFieldConflictError):
            merge_field_values("True", "False", "has_followup_section", "2022/000001")

        # False → True: conflict
        with pytest.raises(ImmutableFieldConflictError):
            merge_field_values("False", "True", "has_followup_section", "2022/000002")

    def test_has_followup_section_empty_raises_mandatory_error(self):
        """Test that missing has_followup_section raises MandatoryFieldMissingError."""

        # Empty followup (mandatory field must be present)
        with pytest.raises(MandatoryFieldMissingError):
            merge_field_values("True", "", "has_followup_section", "2022/000001")

        # Empty base (mandatory field must be present)
        with pytest.raises(MandatoryFieldMissingError):
            merge_field_values("", "True", "has_followup_section", "2022/000002")

    def test_all_unique_fields_use_keep_base_strategy(self):
        """Test that all 14 unique Dataset 1 fields are mapped to merge_keep_base_only."""

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

    def test_null_and_empty_handling_for_unique_fields(self):
        """Test that unique fields handle null/empty values correctly (no conflict)."""

        # Test cases where followup is empty/whitespace (no conflict)
        # Using NON-MANDATORY fields only, as mandatory fields have stricter validation
        test_cases = [
            ("commission_submission_date", "2022-01-15", ""),
            ("submission_text", "Original text", ""),
            ("submission_text", "Original text", "   "),
            ("submission_news_url", "https://news.eu", ""),
            ("commission_officials_met", "John Doe", ""),
            ("commission_meeting_date", "2021-10-14", ""),
            ("parliament_hearing_date", "2021-11-15", ""),
            ("plenary_debate_date", "2022-03-09", ""),
            ("commission_factsheet_url", "https://factsheet.eu", ""),
        ]

        for field, base, followup in test_cases:
            result = merge_field_values(base, followup, field, "2022/000001")
            assert (
                result == base
            ), f"{field} should keep base '{base}' when followup is '{followup}'"

    def test_edge_case_empty_base_with_value_followup_raises_error(self):
        """Test edge case where base is empty but followup has value - raises error."""

        # Empty base with non-empty followup = conflict for immutable fields
        with pytest.raises(ImmutableFieldConflictError) as exc_info:
            merge_field_values(
                "", "Some followup text", "submission_text", "2022/000001"
            )

        error_msg = str(exc_info.value)
        assert "submission_text" in error_msg
        assert "Immutable" in error_msg

        # Another example
        with pytest.raises(ImmutableFieldConflictError):
            merge_field_values(
                "", "https://news-url.eu", "submission_news_url", "2022/000001"
            )

    def test_edge_case_both_empty_returns_empty(self):
        """Test that when both base and followup are empty, empty is returned."""

        # Both empty - no conflict, should return empty
        result_1 = merge_field_values("", "", "submission_text", "2022/000001")
        assert result_1 == "", "Should return empty when both empty"

        result_2 = merge_field_values("", "", "submission_news_url", "2022/000001")
        assert result_2 == "", "Should return empty when both empty"

        # Empty followup with empty base - OK
        result_3 = merge_field_values("", "", "commission_meeting_date", "2022/000001")
        assert result_3 == "", "Should return empty when both empty"

    def test_mandatory_unique_fields_empty_base_raises_error(self):
        """Test that mandatory unique Dataset 1 fields raise error when base is empty."""

        # response_url is mandatory, so empty base should raise error
        with pytest.raises(MandatoryFieldMissingError) as exc_info:
            merge_field_values(
                "", "https://followup-url.eu", "response_url", "2022/000001"
            )

        error_msg = str(exc_info.value)
        assert "response_url" in error_msg
        assert "base" in error_msg.lower()

        # initiative_url is also mandatory
        with pytest.raises(MandatoryFieldMissingError):
            merge_field_values(
                "", "https://initiative-url.eu", "initiative_url", "2022/000001"
            )
