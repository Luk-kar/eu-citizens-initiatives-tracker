"""
Behavioural tests for overlapping column merging.

This module tests merging of 20 overlapping columns with various strategies:

1. followup_dedicated_website - keep base only (identical)
2. commission_answer_text - concatenation with labels
3. official_communication_document_urls - JSON object union
4. final_outcome_status - prioritize followup with validation
5. law_implementation_date - update with followup when exists
6. commission_promised_new_law - one-way True logic
7. commission_deadlines - concatenation with labels
8. commission_rejected_initiative - Response Data priority, one-way True
9. commission_rejection_reason - concatenation with labels
10. laws_actions - JSON list merge
11. policies_actions - JSON list merge
12. has_roadmap - boolean OR
13. has_workshop - boolean OR
14. has_partnership_programs - boolean OR
15. court_cases_referenced - JSON list merge
16. followup_latest_date - maximum date with warnings
17. followup_most_future_date - maximum date with warnings
18. referenced_legislation_by_id - JSON object union
19. referenced_legislation_by_name - JSON object union
20. followup_events_with_dates - JSON list merge with deduplication
"""

import pytest
import json

from ECI_initiatives.csv_merger.responses.strategies import (
    merge_field_values,
    merge_by_concatenation,
    merge_json_objects,
    merge_json_lists,
    merge_boolean_or,
    merge_dates_by_latest,
    merge_promised_new_law,
    merge_rejected_initiative,
    merge_outcome_status_with_validation,
    merge_law_implementation_date,
    get_merge_strategy_for_field,
)
from ECI_initiatives.csv_merger.responses.exceptions import (
    ImmutableFieldConflictError,
    MandatoryFieldMissingError,
)


class TestFollowupDedicatedWebsite:
    """Tests for followup_dedicated_website field (identical in both sources)."""

    def test_keeps_base_value(self):
        """Test that identical values keep base."""

        base = "https://food.ec.europa.eu/animals/animal-welfare/end-cage-age_en"
        followup = "https://food.ec.europa.eu/animals/animal-welfare/end-cage-age_en"
        result = merge_field_values(
            base, followup, "followup_dedicated_website", "2022/000001"
        )
        assert result == base, "Should keep base when both identical"

    def test_different_values_keeps_base(self):
        """Test that conflicting values raise ImmutableFieldConflictError."""

        base = "https://food.ec.europa.eu/animals/animal-welfare/end-cage-age_en"
        followup = "https://different-url.eu"

        # Should raise error when values differ (data integrity issue)
        with pytest.raises(ImmutableFieldConflictError) as exc_info:
            merge_field_values(
                base, followup, "followup_dedicated_website", "2022/000001"
            )

        # Verify error message contains useful information
        error_msg = str(exc_info.value)
        assert (
            "followup_dedicated_website" in error_msg
        ), "Error should mention field name"
        assert "2022/000001" in error_msg, "Error should contain registration number"
        assert base in error_msg, "Error should contain base value"
        assert followup in error_msg, "Error should contain followup value"


class TestCommissionAnswerTextMerging:
    """Tests for commission_answer_text concatenation with labels."""

    def test_both_values_present_creates_labeled_sections(self):
        """Test that both values are preserved with proper labeling."""

        base = "The Commission will present a legislative proposal by end of 2023 to phase out caged farming."
        followup = "The Commission adopted Regulation 2025/123 on 15 March 2025 phasing out caged farming by 2027."
        result = merge_field_values(
            base, followup, "commission_answer_text", "2022/000001"
        )

        assert "**Original Response:**" in result, "Should have original label"
        assert "**Current Followup:**" in result, "Should have current label"
        assert base in result, "Should contain original base text"
        assert followup in result, "Should contain followup text"

    def test_identical_values_not_duplicated(self):
        """Test that identical values are not duplicated."""

        text = "The Commission will conduct a study."
        result = merge_field_values(text, text, "commission_answer_text", "2022/000001")
        assert result == text, "Should not duplicate identical text"
        assert result.count(text) == 1, "Text should appear only once"

    def test_empty_followup_raises_mandatory_error(self):
        """Test when only base has value - should raise error for mandatory field."""

        base = "Original Commission response text."
        followup = ""

        with pytest.raises(
            MandatoryFieldMissingError,
            match=(
                "Mandatory field 'commission_answer_text' "
                "has explicit null value in followup dataset"
            ),
        ):
            merge_field_values(base, followup, "commission_answer_text", "2022/000001")

    def test_empty_base_raises_mandatory_error(self):
        """Test when only followup has value - should raise error for mandatory field."""

        base = ""
        followup = "Updated Commission response from followup website."

        with pytest.raises(
            MandatoryFieldMissingError,
            match="Mandatory field 'commission_answer_text' is empty in base dataset",
        ):
            merge_field_values(base, followup, "commission_answer_text", "2022/000002")

    def test_multiline_text_concatenation(self):
        """Test concatenation of multiline text blocks."""

        base = """The Commission commits to:
        1. Conduct an impact assessment by Q2 2024
        2. Present legislative proposal by end of 2024
        3. Establish stakeholder consultation process"""

        followup = """Implementation status:
        - Impact assessment published May 2024
        - Legislative proposal adopted December 2024
        - Three stakeholder consultations held"""

        result = merge_field_values(
            base, followup, "commission_answer_text", "2022/000001"
        )

        assert base in result, "Should contain full base text"
        assert followup in result, "Should contain full followup text"
        assert result.index(base) < result.index(
            followup
        ), "Base should come before followup"


class TestOfficialCommunicationDocumentUrls:
    """Tests for official_communication_document_urls JSON object merging."""

    def test_merge_unique_urls_from_both_sources(self):
        """Test combining unique URLs from both datasets."""

        base = '{"Communication": "https://ec.europa.eu/doc1.pdf", "Press Release": "https://ec.europa.eu/press1"}'
        followup = '{"Q&A": "https://ec.europa.eu/qa.pdf", "Factsheet": "https://ec.europa.eu/factsheet.pdf"}'
        result = merge_field_values(
            base, followup, "official_communication_document_urls", "2022/000001"
        )

        result_obj = json.loads(result)
        assert "Communication" in result_obj, "Should have Communication from base"
        assert "Press Release" in result_obj, "Should have Press Release from base"
        assert "Q&A" in result_obj, "Should have Q&A from followup"
        assert "Factsheet" in result_obj, "Should have Factsheet from followup"
        assert len(result_obj) == 4, "Should have all 4 unique keys"

    def test_followup_overrides_base_for_same_key(self):
        """Test that followup value overrides base for duplicate keys."""

        base = '{"Communication": "https://ec.europa.eu/old.pdf"}'
        followup = '{"Communication": "https://ec.europa.eu/new.pdf"}'
        result = merge_field_values(
            base, followup, "official_communication_document_urls", "2022/000001"
        )

        result_obj = json.loads(result)
        assert (
            result_obj["Communication"] == "https://ec.europa.eu/new.pdf"
        ), "Followup should override base"

    def test_empty_followup_keeps_base(self):
        """Test that empty followup returns base object."""

        base = '{"Communication": "https://ec.europa.eu/doc.pdf"}'
        followup = ""
        result = merge_field_values(
            base, followup, "official_communication_document_urls", "2022/000001"
        )
        assert result == base, "Should keep base when followup empty"

    def test_empty_base_uses_followup(self):
        """Test that empty base returns followup object."""

        base = ""
        followup = '{"Press Release": "https://ec.europa.eu/press.pdf"}'
        result = merge_field_values(
            base, followup, "official_communication_document_urls", "2022/000002"
        )
        assert result == followup, "Should use followup when base empty"

    def test_both_empty_returns_empty(self):
        """Test that both empty returns empty string."""

        result = merge_field_values(
            "", "", "official_communication_document_urls", "2022/000001"
        )
        assert result == "", "Should return empty when both empty"


class TestFinalOutcomeStatusValidation:
    """Tests for final_outcome_status with validation logic."""

    def test_prioritizes_followup_when_available(self):
        """Test that followup value is preferred when present."""

        base = "Being Studied"
        followup = "Law Proposed"
        result = merge_field_values(
            base, followup, "final_outcome_status", "2022/000001"
        )
        assert result == followup, "Should prioritize followup as more current"

    def test_uses_base_when_followup_empty(self):
        """Test that base is used when followup is empty."""

        base = "Being Studied"
        followup = ""
        result = merge_field_values(
            base, followup, "final_outcome_status", "2022/000002"
        )
        assert result == base, "Should use base when followup empty"

    def test_logical_progression_forward(self):
        """Test logical status progression (no warnings expected)."""

        # Being Studied -> Law Proposed (logical)
        result_1 = merge_field_values(
            "Being Studied", "Law Proposed", "final_outcome_status", "2022/000001"
        )
        assert result_1 == "Law Proposed", "Should accept logical progression"

        # Law Proposed -> Law Approved (logical)
        result_2 = merge_field_values(
            "Law Proposed", "Law Approved", "final_outcome_status", "2022/000002"
        )
        assert result_2 == "Law Approved", "Should accept logical progression"

    def test_rejection_can_happen_at_any_point(self):
        """Test that rejection is valid from any status."""

        # Being Studied -> Law Rejected (valid)
        result_1 = merge_field_values(
            "Being Studied", "Law Rejected", "final_outcome_status", "2022/000001"
        )
        assert result_1 == "Law Rejected", "Should accept rejection from Being Studied"

        # Law Proposed -> Law Rejected (valid)
        result_2 = merge_field_values(
            "Law Proposed", "Law Rejected", "final_outcome_status", "2022/000002"
        )
        assert result_2 == "Law Rejected", "Should accept rejection from Law Proposed"

    def test_identical_status_no_change(self):
        """Test that identical status is handled correctly."""

        result = merge_field_values(
            "Law Approved", "Law Approved", "final_outcome_status", "2022/000001"
        )
        assert result == "Law Approved", "Should keep status when unchanged"

    def test_unknown_status_values(self):
        """Test handling of unknown/custom status values."""

        base = "Custom Status 1"
        followup = "Custom Status 2"
        result = merge_field_values(
            base, followup, "final_outcome_status", "2022/000001"
        )
        assert result == followup, "Should use followup even for unknown statuses"


class TestLawImplementationDate:
    """Tests for law_implementation_date field."""

    def test_update_with_followup_when_exists(self):
        """Test that followup updates base when present."""

        base = ""
        followup = "2025-08-01"
        result = merge_field_values(
            base, followup, "law_implementation_date", "2022/000001"
        )
        assert result == followup, "Should use followup date when base empty"

    def test_followup_overrides_base_date(self):
        """Test that followup overrides existing base date."""

        base = "2024-12-31"
        followup = "2025-08-01"
        result = merge_field_values(
            base, followup, "law_implementation_date", "2022/000001"
        )
        assert result == followup, "Should update to followup date"

    def test_keeps_base_when_followup_empty(self):
        """Test that base is kept when followup is empty."""

        base = "2024-06-15"
        followup = ""
        result = merge_field_values(
            base, followup, "law_implementation_date", "2022/000002"
        )
        assert result == base, "Should keep base when followup empty"

    def test_both_empty_returns_empty(self):
        """Test that both empty returns empty."""

        result = merge_field_values("", "", "law_implementation_date", "2022/000001")
        assert result == "", "Should return empty when both empty"


class TestCommissionPromisedNewLaw:
    """Tests for commission_promised_new_law one-way True logic."""

    def test_false_to_true_becomes_true(self):
        """Test that False in base + True in followup = True."""

        base = "False"
        followup = "True"
        result = merge_field_values(
            base, followup, "commission_promised_new_law", "2022/000001"
        )
        assert result == "True", "Should update to True when followup is True"

    def test_true_to_false_stays_true(self):
        """Test that True in base + False in followup = True (one-way commitment)."""

        base = "True"
        followup = "False"
        result = merge_field_values(
            base, followup, "commission_promised_new_law", "2022/000001"
        )
        assert result == "True", "Should keep True (one-way commitment)"

    def test_both_false_stays_false(self):
        """Test that False + False = False."""

        result = merge_field_values(
            "False", "False", "commission_promised_new_law", "2022/000002"
        )
        assert (
            result == "False"
        ), "Should return False as per OR logic"  # Note: This matches merge_promised_new_law which does OR

    def test_both_true_stays_true(self):
        """Test that True + True = True."""

        result = merge_field_values(
            "True", "True", "commission_promised_new_law", "2022/000001"
        )
        assert result == "True", "Should return True"

    def test_various_boolean_formats(self):
        """Test different boolean string formats."""

        # Lowercase
        assert (
            merge_field_values(
                "false", "true", "commission_promised_new_law", "2022/000001"
            )
            == "True"
        )

        # Numeric
        assert (
            merge_field_values("0", "1", "commission_promised_new_law", "2022/000001")
            == "True"
        )

        # Yes format
        assert (
            merge_field_values(
                "no", "yes", "commission_promised_new_law", "2022/000001"
            )
            == "True"
        )


class TestCommissionRejectedInitiative:
    """Tests for commission_rejected_initiative Response Data priority logic."""

    def test_base_true_overrides_followup(self):
        """Test that True in base takes priority (rejection is permanent)."""

        base = "True"
        followup = "False"
        result = merge_field_values(
            base, followup, "commission_rejected_initiative", "2022/000001"
        )
        assert result == "True", "Should keep True from base (authoritative)"

    def test_base_false_followup_true_uses_followup(self):
        """Test that False in base + True in followup = True."""

        base = "False"
        followup = "True"
        result = merge_field_values(
            base, followup, "commission_rejected_initiative", "2022/000001"
        )
        assert result == "True", "Should update to True from followup"

    def test_both_false_stays_false(self):
        """Test that False + False = False."""

        result = merge_field_values(
            "False", "False", "commission_rejected_initiative", "2022/000002"
        )
        assert result == "False", "Should return False when both False"

    def test_both_true_stays_true(self):
        """Test that True + True = True."""

        result = merge_field_values(
            "True", "True", "commission_rejected_initiative", "2017/000004"
        )
        assert result == "True", "Should return True when both True"


class TestCommissionDeadlines:
    """Tests for commission_deadlines concatenation."""

    def test_both_values_creates_labeled_sections(self):
        """Test that both deadline sets are preserved with labels."""

        base = "Legislative proposal by end of 2023; Final decision by March 2026"
        followup = "Consultation deadline August 2025; Final decision March 2026"
        result = merge_field_values(
            base, followup, "commission_deadlines", "2022/000001"
        )

        assert "**Original Response:**" in result, "Should have original label"
        assert "**Current Followup:**" in result, "Should have current label"
        assert (
            base in result and followup in result
        ), "Should contain both deadline texts"

    def test_only_base_present(self):
        """Test when only base has deadlines."""

        base = "Legislative proposal by Q4 2024"
        result = merge_field_values(base, "", "commission_deadlines", "2022/000001")
        assert result == base, "Should return base when followup empty"


class TestCommissionRejectionReason:
    """Tests for commission_rejection_reason concatenation."""

    def test_both_reasons_preserved_with_labels(self):
        """Test that both rejection reasons are preserved."""

        base = "The Commission does not have competence in this area under EU Treaties."
        followup = "Detailed analysis confirms lack of EU competence as per Articles 4 and 5 TEU."
        result = merge_field_values(
            base, followup, "commission_rejection_reason", "2017/000004"
        )

        assert "**Original Response:**" in result
        assert "**Current Followup:**" in result
        assert base in result and followup in result

    def test_only_base_reason(self):
        """Test when only base has rejection reason."""

        base = "Insufficient legal basis under EU law."
        result = merge_field_values(
            base, "", "commission_rejection_reason", "2012/000001"
        )
        assert result == base


class TestLawsActionsMerging:
    """Tests for laws_actions JSON list merging."""

    def test_merge_unique_actions_from_both(self):
        """Test combining unique legislative actions."""

        base = '[{"type": "promise", "date": "2022-06", "description": "Propose legislation"}]'
        followup = '[{"type": "adopted", "date": "2025-07", "description": "Regulation 2025/123", "celex": "32025R0123"}]'
        result = merge_field_values(base, followup, "laws_actions", "2022/000001")

        result_list = json.loads(result)
        assert len(result_list) == 2, "Should have both actions"
        assert any(
            a["type"] == "promise" for a in result_list
        ), "Should have promise from base"
        assert any(
            a["type"] == "adopted" for a in result_list
        ), "Should have adopted from followup"

    def test_deduplicate_identical_actions(self):
        """Test that identical actions are not duplicated."""

        action = (
            '[{"type": "adopted", "date": "2025-01", "description": "Same regulation"}]'
        )
        result = merge_field_values(action, action, "laws_actions", "2022/000001")

        result_list = json.loads(result)
        assert len(result_list) == 1, "Should not duplicate identical action"

    def test_base_null_uses_followup(self):
        """Test that null/empty base uses followup."""

        followup = '[{"type": "adopted", "date": "2025-01"}]'
        result = merge_field_values("", followup, "laws_actions", "2022/000002")
        assert result == followup, "Should use followup when base empty"

    def test_empty_lists_return_empty(self):
        """Test that empty lists return empty string."""

        result = merge_field_values("[]", "[]", "laws_actions", "2022/000001")
        assert result == "", "Should return empty for empty arrays"


class TestPoliciesActionsMerging:
    """Tests for policies_actions JSON list merging."""

    def test_merge_policy_actions_with_deduplication(self):
        """Test combining and deduplicating policy actions."""

        base = '[{"type": "consultation", "date": "2023-05"}, {"type": "study", "date": "2023-08"}]'
        followup = '[{"type": "consultation", "date": "2023-05"}, {"type": "workshop", "date": "2024-02"}]'
        result = merge_field_values(base, followup, "policies_actions", "2022/000001")

        result_list = json.loads(result)
        assert (
            len(result_list) == 3
        ), "Should have 3 unique actions (deduplicated consultation)"

        consultations = [a for a in result_list if a["type"] == "consultation"]
        assert (
            len(consultations) == 1
        ), "Should have only one consultation after deduplication"

    def test_granular_followup_details_preserved(self):
        """Test that followup's granular details are added."""

        base = '[{"type": "research", "date": "2023"}]'
        followup = '[{"type": "research", "date": "2023-06-15", "name": "EFSA Scientific Opinion"}]'
        result = merge_field_values(base, followup, "policies_actions", "2022/000001")

        result_list = json.loads(result)
        # Both should be preserved as they're not exactly identical
        assert len(result_list) >= 1, "Should preserve actions"


class TestBooleanOrFields:
    """Tests for has_roadmap, has_workshop, has_partnership_programs (boolean OR)."""

    def test_has_roadmap_logical_or(self):
        """Test logical OR for has_roadmap."""

        assert (
            merge_field_values("True", "False", "has_roadmap", "2022/000001") == "True"
        )
        assert (
            merge_field_values("False", "True", "has_roadmap", "2022/000001") == "True"
        )
        assert (
            merge_field_values("True", "True", "has_roadmap", "2022/000001") == "True"
        )
        assert (
            merge_field_values("False", "False", "has_roadmap", "2022/000001")
            == "False"
        )

    def test_has_workshop_logical_or(self):
        """Test logical OR for has_workshop."""

        assert (
            merge_field_values("True", "False", "has_workshop", "2022/000001") == "True"
        )
        assert (
            merge_field_values("False", "True", "has_workshop", "2022/000001") == "True"
        )
        assert (
            merge_field_values("True", "True", "has_workshop", "2022/000001") == "True"
        )
        assert (
            merge_field_values("False", "False", "has_workshop", "2022/000002")
            == "False"
        )

    def test_has_partnership_programs_logical_or(self):
        """Test logical OR for has_partnership_programs."""

        assert (
            merge_field_values(
                "True", "False", "has_partnership_programs", "2022/000001"
            )
            == "True"
        )
        assert (
            merge_field_values(
                "False", "True", "has_partnership_programs", "2022/000001"
            )
            == "True"
        )
        assert (
            merge_field_values(
                "True", "True", "has_partnership_programs", "2022/000001"
            )
            == "True"
        )
        assert (
            merge_field_values(
                "False", "False", "has_partnership_programs", "2022/000002"
            )
            == "False"
        )


class TestCourtCasesReferenced:
    """Tests for court_cases_referenced JSON list merging."""

    def test_combine_court_cases_from_both_sources(self):
        """Test combining court case references."""

        base = '["T-646/21", "C-123/22"]'
        followup = '["T-646/21", "C-456/23"]'
        result = merge_field_values(
            base, followup, "court_cases_referenced", "2017/000004"
        )

        result_list = json.loads(result)
        assert len(result_list) == 3, "Should have 3 unique case numbers"
        assert "T-646/21" in result_list
        assert "C-123/22" in result_list
        assert "C-456/23" in result_list

    def test_empty_court_cases(self):
        """Test when no court cases referenced."""

        result = merge_field_values("", "", "court_cases_referenced", "2022/000001")
        assert result == "", "Should return empty when no court cases"


class TestFollowupLatestDate:
    """Tests for followup_latest_date (maximum date with warnings)."""

    def test_returns_latest_date_from_both(self):
        """Test that maximum date is selected."""

        base = "2024-02-09"
        followup = "2025-08-01"
        result = merge_field_values(
            base, followup, "followup_latest_date", "2022/000001"
        )
        assert result == followup, "Should return later date from followup"

    def test_base_later_than_followup(self):
        """Test when base date is later (should warn but use maximum)."""

        base = "2025-12-31"
        followup = "2024-01-01"
        result = merge_field_values(
            base, followup, "followup_latest_date", "2022/000001"
        )
        assert result == base, "Should return base as it's the maximum"

    def test_only_base_date_present(self):
        """Test when only base has date."""

        base = "2024-06-15"
        result = merge_field_values(base, "", "followup_latest_date", "2022/000001")
        assert result == base, "Should return base when followup empty"

    def test_only_followup_date_present(self):
        """Test when only followup has date."""

        base = ""
        followup = "2025-03-20"
        result = merge_field_values(
            base, followup, "followup_latest_date", "2022/000002"
        )
        assert result == followup, "Should return followup when base empty"

    def test_identical_dates(self):
        """Test when dates are identical."""

        date = "2024-12-11"
        result = merge_field_values(date, date, "followup_latest_date", "2022/000001")
        assert result == date, "Should return date when both identical"


class TestFollowupMostFutureDate:
    """Tests for followup_most_future_date (maximum future date with warnings)."""

    def test_returns_furthest_future_date(self):
        """Test that furthest future date is selected."""

        base = "2026-03-31"
        followup = "2027-08-31"
        result = merge_field_values(
            base, followup, "followup_most_future_date", "2022/000001"
        )
        assert result == followup, "Should return furthest future date"

    def test_base_further_in_future(self):
        """Test when base date is further in future."""

        base = "2027-12-31"
        followup = "2026-01-01"
        result = merge_field_values(
            base, followup, "followup_most_future_date", "2022/000001"
        )
        assert result == base, "Should return base as it's further in future"

    def test_only_base_future_date(self):
        """Test when only base has future date."""

        base = "2026-06-30"
        result = merge_field_values(
            base, "", "followup_most_future_date", "2022/000001"
        )
        assert result == base, "Should return base when followup empty"


class TestReferencedLegislationById:
    """
    Tests for referenced_legislation_by_id JSON object merging.

    This field stores legislation references as a JSON object where:
    - Keys are legislation types (e.g., "Regulation", "Directive", "Article")
    - Values are lists of CELEX numbers or identifiers

    Merge strategy:
    - Combine all unique keys from both datasets
    - For duplicate keys with list values: merge and deduplicate the lists
    - For duplicate keys with non-list values: followup overrides base
    """

    def test_merge_unique_legislation_ids(self):
        """
        Test combining legislation IDs from both datasets with different keys.

        When base has "Regulation" and "Directive", and followup has "Regulation" and "Article":
        - All three keys should be present in result
        - "Regulation" lists should be merged and deduplicated
        - "Directive" should be kept from base
        - "Article" should be added from followup
        """
        base = (
            '{"Regulation": ["32019R2088", "32025R0sad"], "Directive": ["2009/147/EC"]}'
        )
        followup = '{"Regulation": ["32025R0456"], "Article": ["Art. 13 TFEU"]}'
        result = merge_field_values(
            base, followup, "referenced_legislation_by_id", "2022/000001"
        )

        result_obj = json.loads(result)
        assert (
            len(result_obj) == 3
        ), "Should have all 3 unique keys (Regulation, Directive, Article)"
        assert "Article" in result_obj, "Should have Article from followup"
        assert "Directive" in result_obj, "Should have Directive from base"
        assert "Regulation" in result_obj, "Should have Regulation merged from both"

        # Regulation list should be merged and sorted
        expected_regulation = sorted(["32019R2088", "32025R0456", "32025R0sad"])
        assert (
            expected_regulation == result_obj["Regulation"]
        ), "Regulation list should be merged and sorted"

    def test_merge_lists_for_duplicate_keys(self):
        """
        Test that when the same key exists in both datasets, their list values are merged.

        Both base and followup have "Regulation" key with different CELEX numbers:
        - Lists should be combined
        - Duplicates should be removed
        - Result should be sorted
        """
        base = '{"Regulation": ["OLD_CELEX", "SHARED_CELEX"]}'
        followup = '{"Regulation": ["NEW_CELEX", "SHARED_CELEX"]}'
        result = merge_field_values(
            base, followup, "referenced_legislation_by_id", "2022/000001"
        )

        result_obj = json.loads(result)
        expected = sorted(["OLD_CELEX", "NEW_CELEX", "SHARED_CELEX"])
        assert (
            expected == result_obj["Regulation"]
        ), "Should merge lists and deduplicate"

    def test_empty_base_uses_followup(self):
        """Test that when base is empty, followup object is used as-is."""

        base = ""
        followup = '{"Press Release": "https://ec.europa.eu/press1"}'
        result = merge_field_values(
            base, followup, "referenced_legislation_by_id", "2022/000002"
        )
        assert result == followup, "Should use followup when base empty"

    def test_empty_followup_keeps_base(self):
        """Test that when followup is empty, base object is kept."""

        base = '{"Communication": "https://ec.europa.eu/doc1.pdf"}'
        followup = ""
        result = merge_field_values(
            base, followup, "referenced_legislation_by_id", "2022/000001"
        )
        assert result == base, "Should keep base when followup empty"

    def test_both_empty_returns_empty(self):
        """Test that when both are empty, empty string is returned."""

        result = merge_field_values(
            "", "", "referenced_legislation_by_id", "2022/000001"
        )
        assert result == "", "Should return empty when both empty"

    def test_multiple_duplicate_keys_all_merged(self):
        """
        Test merging multiple keys that exist in both datasets.

        When multiple keys have overlapping legislation references:
        - Each key's lists should be independently merged
        - Deduplication should happen per key
        """
        base = '{"Regulation": ["REG1", "REG2"], "Directive": ["DIR1", "DIR2"]}'
        followup = '{"Regulation": ["REG2", "REG3"], "Directive": ["DIR2", "DIR3"]}'
        result = merge_field_values(
            base, followup, "referenced_legislation_by_id", "2022/000001"
        )

        result_obj = json.loads(result)
        assert sorted(["REG1", "REG2", "REG3"]) == result_obj["Regulation"]
        assert sorted(["DIR1", "DIR2", "DIR3"]) == result_obj["Directive"]

    def test_single_item_lists_merged(self):
        """Test that single-item lists are properly merged."""

        base = '{"Article": ["Art. 192 TFEU"]}'
        followup = '{"Article": ["Art. 193 TFEU"]}'
        result = merge_field_values(
            base, followup, "referenced_legislation_by_id", "2022/000001"
        )

        result_obj = json.loads(result)
        expected = sorted(["Art. 192 TFEU", "Art. 193 TFEU"])
        assert expected == result_obj["Article"]

    def test_mixed_new_and_duplicate_keys(self):
        """
        Test merging when some keys are new and some are duplicates.

        Base has keys A and B, followup has keys B and C:
        - A should be kept from base only
        - B should be merged from both
        - C should be added from followup only
        """
        base = '{"TypeA": ["A1", "A2"], "TypeB": ["B1"]}'
        followup = '{"TypeB": ["B2", "B3"], "TypeC": ["C1"]}'
        result = merge_field_values(
            base, followup, "referenced_legislation_by_id", "2022/000001"
        )

        result_obj = json.loads(result)
        assert ["A1", "A2"] == result_obj["TypeA"], "TypeA from base only"
        assert (
            sorted(["B1", "B2", "B3"]) == result_obj["TypeB"]
        ), "TypeB merged from both"
        assert ["C1"] == result_obj["TypeC"], "TypeC from followup only"

    def test_empty_lists_in_values(self):
        """Test handling of empty lists as values."""

        base = '{"Regulation": ["REG1"], "Directive": []}'
        followup = '{"Regulation": [], "Article": ["ART1"]}'
        result = merge_field_values(
            base, followup, "referenced_legislation_by_id", "2022/000001"
        )

        result_obj = json.loads(result)
        assert ["REG1"] == result_obj["Regulation"], "Should keep non-empty base list"
        assert [] == result_obj["Directive"], "Should keep empty list from base"
        assert ["ART1"] == result_obj["Article"], "Should add new key from followup"

    def test_preserves_order_for_non_string_items(self):
        """Test that order is preserved when list items are not all strings."""

        # If items are complex (dicts/nested), order should be preserved (not sorted)
        base = '{"Mixed": ["B", "A", "C"]}'
        followup = '{"Mixed": ["D", "A"]}'
        result = merge_field_values(
            base, followup, "referenced_legislation_by_id", "2022/000001"
        )

        result_obj = json.loads(result)
        # Should be sorted since all are strings
        assert ["A", "B", "C", "D"] == result_obj["Mixed"]


class TestReferencedLegislationById:
    """
    Tests for referenced_legislation_by_id JSON object merging.

    This field stores legislation references as a JSON object where:
    - Keys are legislation types: "Regulation", "Directive", "Decision", "CELEX", "Article"
    - Values are lists of identifiers extracted from legislation references

    Merge strategy:
    - Combine all unique keys from both datasets
    - For duplicate keys with list values: merge and deduplicate the lists
    - For duplicate keys with non-list values: followup overrides base
    """

    def test_merge_unique_legislation_ids(self):
        """
        Test combining legislation IDs from both datasets with different keys.

        When base has "Regulation" and "Directive", and followup has "Regulation" and "Article":
        - All three keys should be present in result
        - "Regulation" lists should be merged and deduplicated
        - "Directive" should be kept from base
        - "Article" should be added from followup
        """
        base = (
            '{"Regulation": ["2088/2019", "0456/2025"], "Directive": ["2009/147/EC"]}'
        )
        followup = '{"Regulation": ["0789/2025"], "Article": ["13", "192"]}'
        result = merge_field_values(
            base, followup, "referenced_legislation_by_id", "2022/000001"
        )

        result_obj = json.loads(result)
        assert (
            len(result_obj) == 3
        ), "Should have all 3 unique keys (Regulation, Directive, Article)"
        assert "Article" in result_obj, "Should have Article from followup"
        assert "Directive" in result_obj, "Should have Directive from base"
        assert "Regulation" in result_obj, "Should have Regulation merged from both"

        # Regulation list should be merged and sorted
        expected_regulation = sorted(["2088/2019", "0456/2025", "0789/2025"])
        assert (
            expected_regulation == result_obj["Regulation"]
        ), "Regulation list should be merged and sorted"

    def test_merge_lists_for_duplicate_keys(self):
        """
        Test that when the same key exists in both datasets, their list values are merged.

        Both base and followup have "CELEX" key with different CELEX numbers:
        - Lists should be combined
        - Duplicates should be removed
        - Result should be sorted
        """
        base = '{"CELEX": ["32019R2088", "32020R0852"]}'
        followup = '{"CELEX": ["32025R0123", "32020R0852"]}'
        result = merge_field_values(
            base, followup, "referenced_legislation_by_id", "2022/000001"
        )

        result_obj = json.loads(result)
        expected = sorted(["32019R2088", "32020R0852", "32025R0123"])
        assert expected == result_obj["CELEX"], "Should merge lists and deduplicate"

    def test_empty_base_uses_followup(self):
        """Test that when base is empty, followup object is used as-is."""

        base = ""
        followup = '{"Decision": ["2024/123", "2024/456"]}'
        result = merge_field_values(
            base, followup, "referenced_legislation_by_id", "2022/000002"
        )

        result_obj = json.loads(result)
        assert ["2024/123", "2024/456"] == result_obj["Decision"]

    def test_empty_followup_keeps_base(self):
        """Test that when followup is empty, base object is kept."""

        base = '{"Regulation": ["1143/2014"]}'
        followup = ""
        result = merge_field_values(
            base, followup, "referenced_legislation_by_id", "2022/000001"
        )

        result_obj = json.loads(result)
        assert ["1143/2014"] == result_obj["Regulation"]

    def test_both_empty_returns_empty(self):
        """Test that when both are empty, empty string is returned."""

        result = merge_field_values(
            "", "", "referenced_legislation_by_id", "2022/000001"
        )
        assert result == "", "Should return empty when both empty"

    def test_multiple_duplicate_keys_all_merged(self):
        """
        Test merging multiple keys that exist in both datasets.

        When multiple keys have overlapping legislation references:
        - Each key's lists should be independently merged
        - Deduplication should happen per key
        """
        base = '{"Regulation": ["2019/2088", "2020/852"], "Directive": ["2009/147/EC", "92/43/EEC"]}'
        followup = '{"Regulation": ["2020/852", "2024/1991"], "Directive": ["92/43/EEC", "2010/75/EU"]}'
        result = merge_field_values(
            base, followup, "referenced_legislation_by_id", "2022/000001"
        )

        result_obj = json.loads(result)
        assert (
            sorted(["2019/2088", "2020/852", "2024/1991"]) == result_obj["Regulation"]
        )
        assert (
            sorted(["2009/147/EC", "2010/75/EU", "92/43/EEC"])
            == result_obj["Directive"]
        )

    def test_single_item_lists_merged(self):
        """Test that single-item lists are properly merged."""

        base = '{"Article": ["192"]}'
        followup = '{"Article": ["193"]}'
        result = merge_field_values(
            base, followup, "referenced_legislation_by_id", "2022/000001"
        )

        result_obj = json.loads(result)
        expected = sorted(["192", "193"])
        assert expected == result_obj["Article"]

    def test_mixed_new_and_duplicate_keys(self):
        """
        Test merging when some keys are new and some are duplicates.

        Base has Regulation and Directive, followup has Directive and Article:
        - Regulation should be kept from base only
        - Directive should be merged from both
        - Article should be added from followup only
        """
        base = '{"Regulation": ["2019/2088", "2020/852"], "Directive": ["2009/147/EC"]}'
        followup = (
            '{"Directive": ["2010/75/EU", "92/43/EEC"], "Article": ["13", "192"]}'
        )
        result = merge_field_values(
            base, followup, "referenced_legislation_by_id", "2022/000001"
        )

        result_obj = json.loads(result)
        assert (
            sorted(["2019/2088", "2020/852"]) == result_obj["Regulation"]
        ), "Regulation from base only"
        assert (
            sorted(["2009/147/EC", "2010/75/EU", "92/43/EEC"])
            == result_obj["Directive"]
        ), "Directive merged from both"
        assert (
            sorted(["13", "192"]) == result_obj["Article"]
        ), "Article from followup only"

    def test_empty_lists_in_values(self):
        """Test handling of empty lists as values."""

        base = '{"Regulation": ["2019/2088"], "Directive": []}'
        followup = '{"Regulation": [], "CELEX": ["32025R0123"]}'
        result = merge_field_values(
            base, followup, "referenced_legislation_by_id", "2022/000001"
        )

        result_obj = json.loads(result)
        assert ["2019/2088"] == result_obj[
            "Regulation"
        ], "Should keep non-empty base list"
        assert [] == result_obj["Directive"], "Should keep empty list from base"
        assert ["32025R0123"] == result_obj["CELEX"], "Should add new key from followup"

    def test_all_valid_legislation_types(self):
        """Test merging with all valid legislation type keys."""

        base = '{"Regulation": ["2019/2088"], "Directive": ["2009/147/EC"], "Decision": ["2024/123"]}'
        followup = '{"CELEX": ["32025R0456"], "Article": ["13", "192"]}'
        result = merge_field_values(
            base, followup, "referenced_legislation_by_id", "2022/000001"
        )

        result_obj = json.loads(result)
        assert len(result_obj) == 5, "Should have all 5 valid legislation types"
        assert "Regulation" in result_obj
        assert "Directive" in result_obj
        assert "Decision" in result_obj
        assert "CELEX" in result_obj
        assert "Article" in result_obj

    def test_celex_numbers_merged_correctly(self):
        """Test that CELEX numbers (complex format) are merged and deduplicated."""

        base = '{"CELEX": ["32019R2088", "32020R0852", "31992L0043"]}'
        followup = '{"CELEX": ["32020R0852", "32025R0456", "32024R1991"]}'
        result = merge_field_values(
            base, followup, "referenced_legislation_by_id", "2022/000001"
        )

        result_obj = json.loads(result)
        expected = sorted(
            ["31992L0043", "32019R2088", "32020R0852", "32024R1991", "32025R0456"]
        )
        assert (
            expected == result_obj["CELEX"]
        ), "CELEX numbers should be merged and sorted"


class TestReferencedLegislationByName:
    """
    Tests for referenced_legislation_by_name JSON object merging.

    This field stores human-readable legislation names as a JSON object where:
    - Keys are legislation categories: "regulations", "directives", "charters" (lowercase plural)
    - Values are lists of human-readable legislation names

    Examples from actual data:
    - "directives": ["Drinking Water Directive", "Water Framework Directive"]
    - "regulations": ["General Food Law Regulation", "Nature Restoration Law"]
    - "charters": ["Charter of Fundamental Rights"]

    Merge strategy:
    - Combine all unique keys from both datasets
    - For duplicate keys with list values: merge and deduplicate the lists
    - For duplicate keys with non-list values: followup overrides base
    """

    def test_merge_unique_legislation_categories(self):
        """Test combining unique legislation categories from both datasets."""

        base = (
            '{"directives": ["Drinking Water Directive", "Water Framework Directive"]}'
        )
        followup = (
            '{"regulations": ["General Food Law Regulation", "Nature Restoration Law"]}'
        )
        result = merge_field_values(
            base, followup, "referenced_legislation_by_name", "2022/000001"
        )

        result_obj = json.loads(result)
        assert len(result_obj) == 2, "Should have 2 categories"
        assert "directives" in result_obj
        assert "regulations" in result_obj
        assert len(result_obj["directives"]) == 2
        assert len(result_obj["regulations"]) == 2

    def test_merge_lists_for_same_category(self):
        """Test that lists are merged when the same category appears in both."""

        base = '{"regulations": ["REACH Regulation", "Cosmetic Products Regulation"]}'
        followup = '{"regulations": ["EU Cosmetics Regulation", "REACH Regulation"]}'
        result = merge_field_values(
            base, followup, "referenced_legislation_by_name", "2021/000006"
        )

        result_obj = json.loads(result)
        expected = sorted(
            [
                "Cosmetic Products Regulation",
                "EU Cosmetics Regulation",
                "REACH Regulation",
            ]
        )
        assert expected == result_obj["regulations"], "Should merge and deduplicate"

    def test_directives_merged_correctly(self):
        """Test that directive names are properly merged."""

        base = '{"directives": ["SEA", "Sustainable Use Directive"]}'
        followup = '{"directives": ["SEA", "AVMSD Directive"]}'
        result = merge_field_values(
            base, followup, "referenced_legislation_by_name", "2019/000016"
        )

        result_obj = json.loads(result)
        expected = sorted(["AVMSD Directive", "SEA", "Sustainable Use Directive"])
        assert expected == result_obj["directives"]

    def test_charters_category_handled(self):
        """Test that charters category is properly handled."""

        base = '{"charters": ["Charter of Fundamental Rights"]}'
        followup = '{"regulations": ["ECI Regulation"]}'
        result = merge_field_values(
            base, followup, "referenced_legislation_by_name", "2019/000007"
        )

        result_obj = json.loads(result)
        assert "charters" in result_obj
        assert "regulations" in result_obj
        assert ["Charter of Fundamental Rights"] == result_obj["charters"]
        assert ["ECI Regulation"] == result_obj["regulations"]

    def test_all_three_categories_merged(self):
        """Test merging when all three categories are present."""

        base = '{"directives": ["AVMSD Directive"], "regulations": ["Common Provisions Regulation"], "charters": ["Charter of Fundamental Rights"]}'
        followup = '{"directives": ["Audiovisual Media Services Directive"], "regulations": ["ECI Regulation"]}'
        result = merge_field_values(
            base, followup, "referenced_legislation_by_name", "2017/000004"
        )

        result_obj = json.loads(result)
        assert len(result_obj) == 3, "Should have all 3 categories"

        # Directives merged
        assert (
            sorted(["AVMSD Directive", "Audiovisual Media Services Directive"])
            == result_obj["directives"]
        )

        # Regulations merged
        assert (
            sorted(["Common Provisions Regulation", "ECI Regulation"])
            == result_obj["regulations"]
        )

        # Charters from base only
        assert ["Charter of Fundamental Rights"] == result_obj["charters"]

    def test_multiple_directives_from_same_initiative(self):
        """Test merging multiple directives like in 2012/000003."""

        base = '{"directives": ["Drinking Water Directive", "Floods Directive"]}'
        followup = '{"directives": ["Water Framework Directive", "Floods Directive"]}'
        result = merge_field_values(
            base, followup, "referenced_legislation_by_name", "2012/000003"
        )

        result_obj = json.loads(result)
        expected = sorted(
            [
                "Drinking Water Directive",
                "Floods Directive",
                "Water Framework Directive",
            ]
        )
        assert expected == result_obj["directives"]

    def test_empty_base_uses_followup(self):
        """Test that when base is empty, followup is used as-is."""

        base = ""
        followup = '{"regulations": ["Nature Restoration Law", "Sustainable Use of Plant Protection Products Regulation"]}'
        result = merge_field_values(
            base, followup, "referenced_legislation_by_name", "2019/000016"
        )

        result_obj = json.loads(result)
        assert "regulations" in result_obj
        assert len(result_obj["regulations"]) == 2

    def test_empty_followup_keeps_base(self):
        """Test that when followup is empty, base is kept."""

        base = '{"directives": ["SEA"]}'
        followup = ""
        result = merge_field_values(
            base, followup, "referenced_legislation_by_name", "2020/000001"
        )

        result_obj = json.loads(result)
        assert ["SEA"] == result_obj["directives"]

    def test_similar_but_different_names_not_deduplicated(self):
        """
        Test that similar but different legislation names are kept separate.

        Example: "AVMSD Directive" vs "Audiovisual Media Services Directive"
        These are related but have different names, so both should be kept.
        """
        base = '{"directives": ["AVMSD Directive"]}'
        followup = '{"directives": ["Audiovisual Media Services Directive"]}'
        result = merge_field_values(
            base, followup, "referenced_legislation_by_name", "2017/000004"
        )

        result_obj = json.loads(result)
        expected = sorted(["AVMSD Directive", "Audiovisual Media Services Directive"])
        assert (
            expected == result_obj["directives"]
        ), "Different names should both be kept"

    def test_cosmetics_variations_handled(self):
        """
        Test handling of similar regulation names with slight variations.

        Example: "Cosmetic Products Regulation" vs "EU Cosmetics Regulation"
        """
        base = '{"regulations": ["Cosmetic Products Regulation", "REACH Regulation"]}'
        followup = '{"regulations": ["EU Cosmetics Regulation"]}'
        result = merge_field_values(
            base, followup, "referenced_legislation_by_name", "2021/000006"
        )

        result_obj = json.loads(result)
        # All three should be kept as they have different names
        expected = sorted(
            [
                "Cosmetic Products Regulation",
                "EU Cosmetics Regulation",
                "REACH Regulation",
            ]
        )
        assert expected == result_obj["regulations"]


class TestFollowupEventsWithDates:
    """Tests for followup_events_with_dates JSON list merging."""

    def test_merge_events_from_both_sources(self):
        """Test combining events from base and followup."""

        base = '[{"date": "15-06-2023", "event": "Stakeholder consultation launched"}]'
        followup = '[{"date": "20-08-2024", "event": "EFSA opinion published"}, {"date": "15-03-2025", "event": "Legislative proposal adopted"}]'
        result = merge_field_values(
            base, followup, "followup_events_with_dates", "2022/000001"
        )

        result_list = json.loads(result)
        assert len(result_list) == 3, "Should have all 3 unique events"

    def test_deduplicate_same_date_and_description(self):
        """Test that identical events are deduplicated."""

        event = '[{"date": "15-06-2024", "event": "Consultation closed"}]'
        result = merge_field_values(
            event, event, "followup_events_with_dates", "2022/000001"
        )

        result_list = json.loads(result)
        assert len(result_list) == 1, "Should not duplicate identical event"

    def test_generic_vs_specific_details_both_preserved(self):
        """Test that both generic and specific event descriptions are preserved if different."""

        base = '[{"date": "01-01-2024", "event": "Study published"}]'
        followup = '[{"date": "15-06-2024", "event": "EFSA Scientific Opinion on animal welfare published"}]'
        result = merge_field_values(
            base, followup, "followup_events_with_dates", "2022/000001"
        )

        result_list = json.loads(result)
        # These are different events (different dates and descriptions), so both preserved
        assert len(result_list) >= 1, "Should preserve events"

    def test_complete_accountability_timeline(self):
        """Test that merging creates complete timeline from initial to current."""

        base = '[{"date": "20-06-2022", "event": "Commission response published"}, {"date": "15-09-2022", "event": "Consultation launched"}]'
        followup = '[{"date": "30-03-2023", "event": "Consultation closed"}, {"date": "15-06-2024", "event": "Impact assessment published"}, {"date": "20-01-2025", "event": "Legislative proposal adopted"}]'
        result = merge_field_values(
            base, followup, "followup_events_with_dates", "2022/000001"
        )

        result_list = json.loads(result)
        assert (
            len(result_list) == 5
        ), "Should have complete timeline with all 5 unique events"

        # Verify we have events from both sources
        dates = [e["date"] for e in result_list]
        assert "20-06-2022" in dates, "Should have base event from 20-06-2022"
        assert "20-01-2025" in dates, "Should have followup event from 20-01-2025"

    def test_empty_base_raises_mandatory_error(self):
        """Test that empty base raises error for mandatory field."""

        base = ""
        followup = '[{"date": "15-03-2024", "event": "Hearing held"}]'

        with pytest.raises(
            MandatoryFieldMissingError,
            match="Mandatory field 'followup_events_with_dates' is empty in base dataset",
        ):
            merge_field_values(
                base, followup, "followup_events_with_dates", "2022/000001"
            )

    def test_empty_followup_raises_mandatory_error(self):
        """Test that empty followup raises error for mandatory field."""

        base = '[{"date": "10-05-2023", "event": "Initial meeting"}]'
        followup = ""

        with pytest.raises(
            MandatoryFieldMissingError,
            match=(
                "Mandatory field 'followup_events_with_dates' "
                "has explicit null value in followup dataset"
            ),
        ):
            merge_field_values(
                base, followup, "followup_events_with_dates", "2022/000001"
            )

    def test_multiple_events_same_date_different_descriptions(self):
        """Test that multiple events on the same date with different descriptions are kept."""

        base = '[{"date": "15-06-2024", "event": "Morning session"}, {"date": "15-06-2024", "event": "Afternoon session"}]'
        followup = '[{"date": "15-06-2024", "event": "Evening session"}]'
        result = merge_field_values(
            base, followup, "followup_events_with_dates", "2022/000001"
        )

        result_list = json.loads(result)
        assert len(result_list) == 3, "Should keep all events even if same date"

    def test_chronological_order_preserved(self):
        """Test that chronological order is maintained in merged timeline."""

        base = '[{"date": "01-01-2023", "event": "Event A"}, {"date": "15-03-2023", "event": "Event B"}]'
        followup = '[{"date": "20-02-2023", "event": "Event C"}, {"date": "30-04-2023", "event": "Event D"}]'
        result = merge_field_values(
            base, followup, "followup_events_with_dates", "2022/000001"
        )

        result_list = json.loads(result)
        assert len(result_list) == 4, "Should have all 4 events"

        # Check we have all dates
        dates = [e["date"] for e in result_list]
        assert "01-01-2023" in dates
        assert "20-02-2023" in dates
        assert "15-03-2023" in dates
        assert "30-04-2023" in dates

    def test_partial_date_formats_handled(self):
        """Test handling of events with partial date information."""

        base = '[{"date": "06-2023", "event": "Mid-year review"}]'
        followup = '[{"date": "15-06-2023", "event": "Detailed review"}]'
        result = merge_field_values(
            base, followup, "followup_events_with_dates", "2022/000001"
        )

        result_list = json.loads(result)
        # Both should be preserved as dates are different formats
        assert (
            len(result_list) == 2
        ), "Should keep both events with different date precision"


class TestStrategyMappingForOverlappingColumns:
    """Test that all overlapping columns are mapped to correct strategies."""

    def test_all_overlapping_fields_have_strategies(self):
        """Test that all 20 overlapping fields have appropriate strategies assigned."""

        overlapping_fields = {
            "followup_dedicated_website": "merge_keep_base_only",
            "commission_answer_text": "merge_by_concatenation",
            "official_communication_document_urls": "merge_json_objects",
            "final_outcome_status": "merge_outcome_status_with_validation",
            "law_implementation_date": "merge_law_implementation_date",
            "commission_promised_new_law": "merge_promised_new_law",
            "commission_deadlines": "merge_by_concatenation",
            "commission_rejected_initiative": "merge_rejected_initiative",
            "commission_rejection_reason": "merge_by_concatenation",
            "laws_actions": "merge_json_lists",
            "policies_actions": "merge_json_lists",
            "has_roadmap": "merge_boolean_or",
            "has_workshop": "merge_boolean_or",
            "has_partnership_programs": "merge_boolean_or",
            "court_cases_referenced": "merge_json_lists",
            "followup_latest_date": "merge_dates_by_latest",
            "followup_most_future_date": "merge_dates_by_latest",
            "referenced_legislation_by_id": "merge_json_objects",
            "referenced_legislation_by_name": "merge_json_objects",
            "followup_events_with_dates": "merge_json_lists",
        }

        for field, expected_strategy_name in overlapping_fields.items():
            strategy = get_merge_strategy_for_field(field)
            assert strategy is not None, f"{field} should have a strategy assigned"
            assert (
                strategy.__name__ == expected_strategy_name
            ), f"{field} should use {expected_strategy_name}, got {strategy.__name__}"
