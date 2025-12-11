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
    IMMUTABLE_FIELDS,
)


class TestUniqueDataset1ColumnsMerging:
    """Tests for unique Dataset 1 column merge strategies."""

    def test_response_url_keeps_base(self):
        """Test that response_url always keeps base value."""

        # Test case 1: Valid URL in base
        base_1 = (
            "https://citizens-initiative.europa.eu/initiatives/details/2022/000001_en"
        )
        followup_1 = ""
        result_1 = merge_field_values(
            base_1, followup_1, "response_url", "ECI(2022)000001"
        )
        assert result_1 == base_1, "Should keep base URL when followup empty"

        # Test case 2: Both have values (shouldn't happen)
        base_2 = (
            "https://citizens-initiative.europa.eu/initiatives/details/2022/000001_en"
        )
        followup_2 = "https://different-url.eu"
        result_2 = merge_field_values(
            base_2, followup_2, "response_url", "ECI(2022)000001"
        )
        assert (
            result_2 == base_2
        ), "Should keep base URL even if followup has different value"

    def test_initiative_url_keeps_base(self):
        """Test that initiative_url always keeps base value."""

        base = "https://citizens-initiative.europa.eu/initiatives/details/2022/000001"
        followup = "https://different-url.eu"
        result = merge_field_values(base, followup, "initiative_url", "ECI(2022)000001")
        assert result == base, "Should keep canonical base initiative URL"

    def test_submission_text_keeps_base(self):
        """Test that submission_text (historical narrative) always keeps base value."""

        # Test case 1: Long submission text
        base_1 = """On 29 September 2021, the organisers submitted the European Citizens' 
        Initiative (ECI) 'End the Cage Age' to the European Commission. A delegation of organisers 
        met with Commission representatives on 14 October 2021. The European Parliament held a 
        public hearing on 15 November 2021."""
        followup_1 = "Updated submission information"
        result_1 = merge_field_values(
            base_1, followup_1, "submission_text", "ECI(2022)000001"
        )
        assert result_1 == base_1, "Should keep original historical submission text"

        # Test case 2: Empty followup
        base_2 = "Brief submission narrative."
        followup_2 = ""
        result_2 = merge_field_values(
            base_2, followup_2, "submission_text", "ECI(2022)000002"
        )
        assert result_2 == base_2, "Should keep base submission text"

    def test_commission_submission_date_keeps_base(self):
        """Test that commission_submission_date (fixed historical date) keeps base value."""

        # Test case 1: ISO date format
        base_1 = "2021-09-29"
        followup_1 = "2021-09-30"
        result_1 = merge_field_values(
            base_1, followup_1, "commission_submission_date", "ECI(2022)000001"
        )
        assert result_1 == base_1, "Should keep original submission date, not revised"

        # Test case 2: Empty followup
        base_2 = "2019-12-15"
        followup_2 = ""
        result_2 = merge_field_values(
            base_2, followup_2, "commission_submission_date", "ECI(2019)000006"
        )
        assert result_2 == base_2, "Should keep base date when followup empty"

    def test_submission_news_url_keeps_base(self):
        """Test that submission_news_url (press release link) keeps base value."""

        base = "https://ec.europa.eu/commission/presscorner/detail/en/ip_21_4747"
        followup = "https://different-press-release.eu"
        result = merge_field_values(
            base, followup, "submission_news_url", "ECI(2022)000001"
        )
        assert result == base, "Should keep original press release URL"

    def test_commission_meeting_date_keeps_base(self):
        """Test that commission_meeting_date (procedural milestone) keeps base value."""

        base = "2021-10-14"
        followup = "2021-10-15"
        result = merge_field_values(
            base, followup, "commission_meeting_date", "ECI(2022)000001"
        )
        assert result == base, "Should keep original meeting date"

    def test_commission_officials_met_keeps_base(self):
        """Test that commission_officials_met (historical record) keeps base value."""

        base = "Stella Kyriakides, Commissioner for Health and Food Safety; Sandra Gallina, Deputy Director-General, DG SANTE"
        followup = "Different officials"
        result = merge_field_values(
            base, followup, "commission_officials_met", "ECI(2022)000001"
        )
        assert result == base, "Should keep original officials list"

    def test_parliament_hearing_date_keeps_base(self):
        """Test that parliament_hearing_date (mandatory procedural date) keeps base value."""

        base = "2021-11-15"
        followup = "2021-11-16"
        result = merge_field_values(
            base, followup, "parliament_hearing_date", "ECI(2022)000001"
        )
        assert result == base, "Should keep original Parliament hearing date"

    def test_parliament_hearing_video_urls_keeps_base(self):
        """Test that parliament_hearing_video_urls (archival links) keeps base value."""

        # Test case 1: JSON list of URLs
        base_1 = '["https://multimedia.europarl.europa.eu/video1", "https://multimedia.europarl.europa.eu/video2"]'
        followup_1 = '["https://different-video.eu"]'
        result_1 = merge_field_values(
            base_1, followup_1, "parliament_hearing_video_urls", "ECI(2022)000001"
        )
        assert result_1 == base_1, "Should keep original video URLs"

        # Test case 2: Empty list in followup
        base_2 = '["https://multimedia.europarl.europa.eu/video"]'
        followup_2 = "[]"
        result_2 = merge_field_values(
            base_2, followup_2, "parliament_hearing_video_urls", "ECI(2022)000002"
        )
        assert (
            result_2 == base_2
        ), "Should keep base URLs even if followup is empty array"

    def test_plenary_debate_date_keeps_base(self):
        """Test that plenary_debate_date (optional procedural milestone) keeps base value."""

        # Test case 1: Date present
        base_1 = "2022-03-09"
        followup_1 = "2022-03-10"
        result_1 = merge_field_values(
            base_1, followup_1, "plenary_debate_date", "ECI(2022)000001"
        )
        assert result_1 == base_1, "Should keep original plenary debate date"

        # Test case 2: Empty (no plenary debate held)
        base_2 = ""
        followup_2 = "2022-05-15"
        result_2 = merge_field_values(
            base_2, followup_2, "plenary_debate_date", "ECI(2022)000002"
        )
        assert result_2 == base_2, "Should keep empty base even if followup has date"

    def test_plenary_debate_video_urls_keeps_base(self):
        """Test that plenary_debate_video_urls (archival multimedia) keeps base value."""

        base = '["https://multimedia.europarl.europa.eu/plenary/debate"]'
        followup = '["https://different-debate-video.eu"]'
        result = merge_field_values(
            base, followup, "plenary_debate_video_urls", "ECI(2022)000001"
        )
        assert result == base, "Should keep original plenary debate video URLs"

    def test_official_communication_adoption_date_keeps_base(self):
        """Test that official_communication_adoption_date (legal timestamp) keeps base value."""

        # Test case 1: Official adoption date
        base_1 = "2022-06-22"
        followup_1 = "2022-06-23"
        result_1 = merge_field_values(
            base_1,
            followup_1,
            "official_communication_adoption_date",
            "ECI(2022)000001",
        )
        assert result_1 == base_1, "Should keep definitive legal adoption date"

        # Test case 2: Different formats (should still keep base)
        base_2 = "2019-12-15T10:30:00"
        followup_2 = "2019-12-15"
        result_2 = merge_field_values(
            base_2,
            followup_2,
            "official_communication_adoption_date",
            "ECI(2019)000006",
        )
        assert result_2 == base_2, "Should keep base date format"

    def test_commission_factsheet_url_keeps_base(self):
        """Test that commission_factsheet_url (structural metadata) keeps base value."""

        base = (
            "https://ec.europa.eu/info/sites/default/files/factsheet_end_cage_age.pdf"
        )
        followup = "https://different-factsheet.eu"
        result = merge_field_values(
            base, followup, "commission_factsheet_url", "ECI(2022)000001"
        )
        assert result == base, "Should keep original Commission factsheet URL"

    def test_has_followup_section_keeps_base(self):
        """Test that has_followup_section (page structure metadata) keeps base value."""

        # Test case 1: True in base
        base_1 = "True"
        followup_1 = "False"
        result_1 = merge_field_values(
            base_1, followup_1, "has_followup_section", "ECI(2022)000001"
        )
        assert result_1 == base_1, "Should keep base value for page structure metadata"

        # Test case 2: False in base
        base_2 = "False"
        followup_2 = "True"
        result_2 = merge_field_values(
            base_2, followup_2, "has_followup_section", "ECI(2022)000002"
        )
        assert result_2 == base_2, "Should keep base False even if followup is True"

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

    def test_immutable_fields_constant_includes_unique_fields(self):
        """Test that IMMUTABLE_FIELDS constant includes all unique Dataset 1 fields."""

        expected_unique_fields = [
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

        for field in expected_unique_fields:
            assert (
                field in IMMUTABLE_FIELDS
            ), f"{field} should be in IMMUTABLE_FIELDS constant"

    def test_null_and_empty_handling_for_unique_fields(self):
        """Test that unique fields handle null/empty values correctly."""

        test_cases = [
            ("response_url", "https://example.eu", None),
            ("response_url", "https://example.eu", ""),
            ("response_url", "https://example.eu", "null"),
            ("response_url", "https://example.eu", "   "),
            ("commission_submission_date", "2022-01-15", ""),
            ("submission_text", "Original text", None),
            ("has_followup_section", "True", "False"),
        ]

        for field, base, followup in test_cases:
            result = merge_field_values(base, followup, field, "ECI(2022)000001")
            assert (
                result == base
            ), f"{field} should keep base '{base}' when followup is '{followup}'"

    def test_edge_case_empty_base_values(self):
        """Test edge case where base is empty (shouldn't happen for most unique fields)."""

        # Even if base is empty, should still return base (not followup)
        result_1 = merge_field_values(
            "", "https://followup-url.eu", "response_url", "ECI(2022)000001"
        )
        assert result_1 == "", "Should return empty base even if followup has value"

        result_2 = merge_field_values(
            "", "2022-01-15", "commission_submission_date", "ECI(2022)000001"
        )
        assert result_2 == "", "Should return empty base for date fields"
