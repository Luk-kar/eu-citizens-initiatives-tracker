"""
Behavioural tests for extracting legislative and non-legislative outcomes.

This module tests extraction of:
- Final outcome status classification
- Commission commitments and deadlines
- Commission rejections and reasoning
- Legislative actions with dates and statuses
- Non-legislative policy actions
- Law implementation dates
"""

# Third party
import pytest
from bs4 import BeautifulSoup

# Local
from ECI_initiatives.extractor.responses_followup_website.parser.extractors import (
    FollowupWebsiteExtractor,
)


class TestOutcomeExtraction:
    """Tests for outcome classification and extraction."""

    @pytest.fixture
    def html_applicable(self):
        """HTML for Law Active status (regulation became applicable)."""
        return """
        <div>
            <div class="ecl">
                <h2 class="ecl-u-type-heading-2" id="response-of-the-commission">
                    Response of the Commission
                </h2>
            </div>
            <div class="ecl">
                <p>
                    The Regulation was adopted by the Council on 15 March 2023 
                    and became applicable on 1 January 2024.
                </p>
            </div>
        </div>
        """

    @pytest.fixture
    def html_adopted(self):
        """HTML for Law Approved status (adopted but not yet applicable)."""
        return """
        <div>
            <div class="ecl">
                <h2 class="ecl-u-type-heading-2" id="response-of-the-commission">
                    Response of the Commission
                </h2>
            </div>
            <div class="ecl">
                <p>
                    Through an Implementing Regulation adopted on 17 July 2025, 
                    American mink (Neovison vison) is now listed under the 
                    Invasive Alien Species Regulation. The listing of this species 
                    will enter into force in August 2027.
                </p>
            </div>
        </div>
        """

    @pytest.fixture
    def html_committed(self):
        """HTML for Law Promised status (Commission committed to propose)."""
        return """
        <div>
            <div class="ecl">
                <h2 class="ecl-u-type-heading-2" id="response-of-the-commission">
                    Response of the Commission
                </h2>
            </div>
            <div class="ecl">
                <p>
                    On 30 June 2021, the Commission decided to positively respond to the ECI. 
                    In its communication the Commission sets out plans for a legislative 
                    proposal to prohibit cages for the species and categories of animals 
                    covered by the ECI.
                </p>
            </div>
            <div class="ecl">
                <h2 class="ecl-u-type-heading-2" id="next-steps">
                    Next steps
                </h2>
            </div>
            <div class="ecl">
                <p>
                    The Commission will present proposals on the revision of the existing 
                    EU animal welfare legislation, including its commitment to phase out cages.
                </p>
            </div>
        </div>
        """

    @pytest.fixture
    def html_assessment_pending(self):
        """HTML for Being Studied status (assessment ongoing with future decision)."""
        return """
        <div>
            <div class="ecl">
                <h2 class="ecl-u-type-heading-2" id="response-of-the-commission">
                    Response of the Commission
                </h2>
            </div>
            <div class="ecl">
                <p>
                    The Commission published the response to this initiative on 7 December 2023 
                    in the form of a Communication, setting out the Commission's legal and 
                    political conclusions on the initiative.
                </p>
            </div>
            <div class="ecl">
                <h2 class="ecl-u-type-heading-2" id="follow-up-on-the-commissions-actions">
                    Follow-up on the Commission's actions
                </h2>
            </div>
            <div class="ecl">
                <p>
                    Taking into account the EFSA opinion and the outcomes of its own assessment, 
                    the Commission will communicate, by March 2026, whether it considers it 
                    appropriate to propose a prohibition.
                </p>
            </div>
        </div>
        """

    @pytest.fixture
    def html_roadmap_development(self):
        """HTML for Action Plan Created status (roadmap being developed)."""
        return """
        <div>
            <div class="ecl">
                <h2 class="ecl-u-type-heading-2" id="response-of-the-commission">
                    Response of the Commission
                </h2>
            </div>
            <div class="ecl">
                <p>
                    The Commission acknowledged the concerns raised and has started work on 
                    a roadmap to address the issues outlined in the initiative. The roadmap 
                    will be developed in consultation with stakeholders.
                </p>
            </div>
        </div>
        """

    @pytest.fixture
    def html_rejected(self):
        """HTML for Rejected status (no legislative proposal)."""
        return """
        <div>
            <div class="ecl">
                <h2 class="ecl-u-type-heading-2" id="response-of-the-commission">
                    Response of the Commission
                </h2>
            </div>
            <div class="ecl">
                <p>
                    After careful consideration, the Commission has decided not to submit 
                    a legislative proposal in response to this initiative. The Commission 
                    considers that the proposal falls outside of EU competence.
                </p>
            </div>
        </div>
        """

    @pytest.fixture
    def html_rejected_already_covered(self):
        """HTML for Rejected - Already Covered status."""
        return """
        <div>
            <div class="ecl">
                <h2 class="ecl-u-type-heading-2" id="response-of-the-commission">
                    Response of the Commission
                </h2>
            </div>
            <div class="ecl">
                <p>
                    The Commission will not make a legislative proposal as the issues 
                    raised are already covered by existing legislation. The current 
                    framework already addresses the concerns outlined in the initiative.
                </p>
            </div>
        </div>
        """

    @pytest.fixture
    def html_rejected_with_actions(self):
        """HTML for Rejected - Alternative Actions status."""
        return """
        <div>
            <div class="ecl">
                <h2 class="ecl-u-type-heading-2" id="response-of-the-commission">
                    Response of the Commission
                </h2>
            </div>
            <div class="ecl">
                <p>
                    The Commission decided not to submit a legislative proposal. However, 
                    the Commission is committed to supporting alternative measures and will 
                    continue to monitor the situation closely.
                </p>
            </div>
        </div>
        """

    @pytest.fixture
    def html_non_legislative_action(self):
        """HTML for Policy Changes Only status."""
        return """
        <div>
            <div class="ecl">
                <h2 class="ecl-u-type-heading-2" id="response-of-the-commission">
                    Response of the Commission
                </h2>
            </div>
            <div class="ecl">
                <p>
                    The Commission intends to focus on non-legislative measures and the 
                    implementation of existing policies. No new legislative proposal is 
                    planned at this time.
                </p>
            </div>
        </div>
        """

    @pytest.fixture
    def html_proposal_pending(self):
        """HTML for Proposals Under Review status."""
        return """
        <div>
            <div class="ecl">
                <h2 class="ecl-u-type-heading-2" id="response-of-the-commission">
                    Response of the Commission
                </h2>
            </div>
            <div class="ecl">
                <p>
                    The Commission has already tabled a proposal addressing these concerns 
                    rather than proposing new legislative acts. The proposal is currently 
                    under negotiation with the European Parliament and Council.
                </p>
            </div>
        </div>
        """

    @pytest.fixture
    def html_no_status_patterns(self):
        """HTML with no recognizable status patterns (should return None)."""
        return """
        <div>
            <div class="ecl">
                <h2 class="ecl-u-type-heading-2" id="response-of-the-commission">
                    Response of the Commission
                </h2>
            </div>
            <div class="ecl">
                <p>
                    This is some generic text about the initiative that contains no 
                    recognizable legislative status patterns or keywords.
                </p>
            </div>
        </div>
        """

    def test_extract_final_outcome_status_applicable(self, html_applicable):
        """Test extraction of 'Law Active' status."""
        extractor = FollowupWebsiteExtractor(html_applicable)

        result = extractor.extract_final_outcome_status()

        assert result == "Law Active"

    def test_extract_final_outcome_status_adopted(self, html_adopted):
        """Test extraction of 'Law Approved' status."""
        extractor = FollowupWebsiteExtractor(html_adopted)

        result = extractor.extract_final_outcome_status()

        assert result == "Law Approved"

    def test_extract_final_outcome_status_committed(self, html_committed):
        """Test extraction of 'Law Promised' status."""
        extractor = FollowupWebsiteExtractor(html_committed)

        result = extractor.extract_final_outcome_status()

        assert result == "Law Promised"

    def test_extract_final_outcome_status_assessment_pending(
        self, html_assessment_pending
    ):
        """Test extraction of 'Being Studied' status."""
        extractor = FollowupWebsiteExtractor(html_assessment_pending)

        result = extractor.extract_final_outcome_status()

        assert result == "Being Studied"

    def test_extract_final_outcome_status_roadmap_development(
        self, html_roadmap_development
    ):
        """Test extraction of 'Action Plan Created' status."""
        extractor = FollowupWebsiteExtractor(html_roadmap_development)

        result = extractor.extract_final_outcome_status()

        assert result == "Action Plan Created"

    def test_extract_final_outcome_status_rejected(self, html_rejected):
        """Test extraction of 'Rejected' status."""
        extractor = FollowupWebsiteExtractor(html_rejected)

        result = extractor.extract_final_outcome_status()

        assert result == "Rejected"

    def test_extract_final_outcome_status_rejected_already_covered(
        self, html_rejected_already_covered
    ):
        """Test extraction of 'Rejected - Already Covered' status."""
        extractor = FollowupWebsiteExtractor(html_rejected_already_covered)

        result = extractor.extract_final_outcome_status()

        assert result == "Rejected - Already Covered"

    def test_extract_final_outcome_status_rejected_with_actions(
        self, html_rejected_with_actions
    ):
        """Test extraction of 'Rejected - Alternative Actions' status."""
        extractor = FollowupWebsiteExtractor(html_rejected_with_actions)

        result = extractor.extract_final_outcome_status()

        assert result == "Rejected - Alternative Actions"

    def test_extract_final_outcome_status_non_legislative_action(
        self, html_non_legislative_action
    ):
        """Test extraction of 'Policy Changes Only' status."""
        extractor = FollowupWebsiteExtractor(html_non_legislative_action)

        result = extractor.extract_final_outcome_status()

        assert result == "Policy Changes Only"

    def test_extract_final_outcome_status_proposal_pending(self, html_proposal_pending):
        """Test extraction of 'Proposals Under Review' status."""
        extractor = FollowupWebsiteExtractor(html_proposal_pending)

        result = extractor.extract_final_outcome_status()

        assert result == "Proposals Under Review"

    def test_extract_final_outcome_status_no_patterns_returns_none(
        self, html_no_status_patterns
    ):
        """Test that extraction returns None when no status patterns are found."""
        extractor = FollowupWebsiteExtractor(html_no_status_patterns)

        with pytest.raises(
            ValueError, match="Could not determine legislative status for initiative"
        ):
            extractor.extract_final_outcome_status()

    def test_extract_law_implementation_date(self):
        """Test extraction of law implementation/applicable date."""

        # Test case 1: Law became applicable - specific date
        html_applicable = """
        <div>
            <div class="ecl">
                <h2 class="ecl-u-type-heading-2" id="response-of-the-commission">
                    Response of the Commission
                </h2>
            </div>
            <div class="ecl">
                <p>
                    The Regulation was adopted by the Council on 15 March 2023 
                    and became applicable on 1 January 2024.
                </p>
            </div>
        </div>
        """
        extractor_1 = FollowupWebsiteExtractor(html_applicable)
        result_1 = extractor_1.extract_law_implementation_date()

        assert result_1 == "2024-01-01", f"Expected '2024-01-01', got '{result_1}'"

        # Test case 2: Law not yet applicable - returns None
        html_committed = """
        <div>
            <div class="ecl">
                <h2 class="ecl-u-type-heading-2" id="response-of-the-commission">
                    Response of the Commission
                </h2>
            </div>
            <div class="ecl">
                <p>
                    The Commission sets out plans for a legislative proposal 
                    to be presented by the end of 2025.
                </p>
            </div>
        </div>
        """
        extractor_2 = FollowupWebsiteExtractor(html_committed)
        result_2 = extractor_2.extract_law_implementation_date()

        assert result_2 is None, "Should return None when law not yet applicable"

        # Test case 3: "Became applicable immediately" using entry into force date
        html_immediate = """
        <div>
            <div class="ecl">
                <h2 class="ecl-u-type-heading-2" id="response-of-the-commission">
                    Response of the Commission
                </h2>
            </div>
            <div class="ecl">
                <p>
                    The regulation entered into force on 18 August 2024 and 
                    became applicable immediately.
                </p>
            </div>
        </div>
        """
        extractor_3 = FollowupWebsiteExtractor(html_immediate)
        result_3 = extractor_3.extract_law_implementation_date()

        assert result_3 == "2024-08-18", f"Expected '2024-08-18', got '{result_3}'"

    def test_extract_commission_promised_new_law(self):
        """Test extraction of whether Commission promised new legislation (True/False)."""

        # Test case 1: Clear promise - End the Cage Age
        html_1 = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>
                    On 30 June 2021, the Commission decided to positively respond to the ECI. 
                    In its communication the Commission sets out plans for a legislative 
                    proposal to prohibit cages for the species and categories of animals 
                    covered by the ECI.
                </p>
            </div>
        </div>
        """

        extractor_1 = FollowupWebsiteExtractor(html_1)
        result_1 = extractor_1.extract_commission_promised_new_law()
        assert result_1 is True, "Should detect promise for End the Cage Age"

        # Test case 2: Conditional future decision - Fur Free Europe
        html_2 = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>
                    The Commission published the response to this initiative on 7 December 2023.
                </p>
            </div>
            <div class="ecl">
                <h2 id="follow-up-on-the-commissions-actions">Follow-up on the Commission's actions</h2>
            </div>
            <div class="ecl">
                <p>
                    Taking into account the EFSA opinion and the outcomes of its own assessment, 
                    the Commission will communicate, by March 2026, whether it considers it 
                    appropriate to propose a prohibition.
                </p>
            </div>
        </div>
        """

        extractor_2 = FollowupWebsiteExtractor(html_2)
        result_2 = extractor_2.extract_commission_promised_new_law()
        assert (
            result_2 is False
        ), "Should return False for conditional future decision without commitment"

        # Test case 3: Assessment for decision if create a new law or not with deadline - Glyphosate (aim 2)
        html_3 = """
        <div>
            <div class="ecl">
                <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
            </div>
            <div class="ecl">
                <p>
                    On the second aim, to ensure that the scientific evaluation of pesticides 
                    for EU regulatory approval is based only on published studies, the Commission 
                    committed to come forward with a legislative proposal by May 2018.
                </p>
            </div>
                <div class="ecl">
                <h2 id="follow-up-on-the-commissions-actions">Follow-up on the Commission's actions</h2>
            </div>
                <div class="ecl">
                <p>
                    ...
                </p>
            </div>
        </div>
        """

        extractor_3 = FollowupWebsiteExtractor(html_3)
        result_3 = extractor_3.extract_commission_promised_new_law()
        assert result_3 is False, "Should detect commitment with specific deadline"

        # Test case 4: Explicit rejection - Glyphosate (aim 1)
        html_4 = """
        <div>
            <div class="ecl">
                <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
            </div>
            <div class="ecl">
                <p>
                    On the first aim, to ban glyphosate-based herbicides, the Commission 
                    concluded that there are neither scientific nor legal grounds to justify 
                    a ban of glyphosate, and will not make a legislative proposal to that effect.
                </p>
            </div>
            </div>
                <div class="ecl">
                <h2 id="follow-up-on-the-commissions-actions">Follow-up on the Commission's actions</h2>
            </div>
                <div class="ecl">
                <p>
                    ...
                </p>
            </div>
        </div>
        """

        extractor_4 = FollowupWebsiteExtractor(html_4)
        result_4 = extractor_4.extract_commission_promised_new_law()
        assert (
            result_4 is False
        ), "Should return False when proposal is explicitly rejected"

        # Test case 5: EFSA mandate without legislative commitment
        html_5 = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>
                    The European Commission mandated the European Food Safety Authority (EFSA) 
                    to give an independent view on the protection of animals kept for fur production.
                </p>
                <p>
                    Building further on this scientific input, and on an assessment of economic 
                    and social impacts, the Commission will then communicate, by March 2026, 
                    on the most appropriate action.
                </p>
            </div>
            </div>
                <div class="ecl">
                <h2 id="follow-up-on-the-commissions-actions">Follow-up on the Commission's actions</h2>
            </div>
                <div class="ecl">
                <p>
                    ...
                </p>
            </div>
        </div>
        """

        extractor_5 = FollowupWebsiteExtractor(html_5)
        result_5 = extractor_5.extract_commission_promised_new_law()
        assert (
            result_5 is False
        ), "Should return False for mandate to assess without commitment to propose"

    def test_extract_commission_deadlines(self):
        """Test extraction of Commission deadline commitments."""

        # # Test case 1: Consultation deadline with "will run until" - End the Cage Age
        html_1 = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>
                    Further to the call for evidence launched on 18 June 2025 (and closed
                    on 16 July 2025), the Commission published on 19 September 2025 a
                    public consultation which will run until 12 December 2025.
                </p>
            </div>
        </div>
        """

        extractor_1 = FollowupWebsiteExtractor(html_1)
        result_1 = extractor_1.extract_commissions_deadlines()

        assert result_1 is not None, "Should extract deadline"
        assert "2025-12-12" in result_1, "Should contain 2025-12-12"
        assert (
            "consultation" in result_1["2025-12-12"].lower()
        ), "Should mention consultation"

        # Test case 2: Call for evidence with "runs...until" - Fur Free Europe
        html_2 = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <h2 id="follow-up-on-the-commissions-actions">Follow-up on the Commission's actions</h2>
            </div>
            <div class="ecl">
                <p>
                    On 4 July 2025, the Commission launched a Call for evidence requesting 
                    input from stakeholders and citizens. The Call for evidence runs for 
                    four weeks, until 1 August 2025 and the feedback received are publicly 
                    available.
                </p>
            </div>
        </div>
        """

        extractor_2 = FollowupWebsiteExtractor(html_2)
        result_2 = extractor_2.extract_commissions_deadlines()

        assert result_2 is not None, "Should extract deadline"
        assert "2025-08-01" in result_2, "Should contain 2025-08-01"
        assert (
            "call for evidence" in result_2["2025-08-01"].lower()
        ), "Should mention call for evidence"

        # Test case 3: Communication deadline with "by" - Fur Free Europe
        html_3 = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <h2 id="follow-up-on-the-commissions-actions">Follow-up on the Commission's actions</h2>
            </div>
            <div class="ecl">
                <p>
                    Taking into account the EFSA opinion and the outcomes of its own assessment, 
                    the Commission will communicate, by March 2026, whether it considers it 
                    appropriate to propose a prohibition, after a transition period, on the 
                    keeping in farms and killing of farmed mink, foxes, raccoon dogs or chinchilla.
                </p>
            </div>
        </div>
        """

        extractor_3 = FollowupWebsiteExtractor(html_3)
        result_3 = extractor_3.extract_commissions_deadlines()

        assert result_3 is not None, "Should extract deadline"
        assert (
            "2026-03-31" in result_3
        ), "Should contain 2026-03-31 (March 2026 end of month)"
        assert (
            "communicate" in result_3["2026-03-31"].lower()
        ), "Should mention communicate"

        # Test case 4: Multiple deadlines in same document
        html_4 = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>
                    The Commission published on 19 September 2025 a public consultation 
                    which will run until 12 December 2025.
                </p>
            </div>
            <div class="ecl">
                <h2 id="follow-up-on-the-commissions-actions">Follow-up</h2>
            </div>
            <div class="ecl">
                <p>
                    The Commission will communicate, by March 2026, whether it considers 
                    it appropriate to propose a prohibition.
                </p>
            </div>
        </div>
        """

        extractor_4 = FollowupWebsiteExtractor(html_4)
        result_4 = extractor_4.extract_commissions_deadlines()

        assert result_4 is not None, "Should extract multiple deadlines"
        assert len(result_4) == 2, "Should contain exactly 2 deadlines"
        assert "2025-12-12" in result_4, "Should contain first deadline"
        assert "2026-03-31" in result_4, "Should contain second deadline"

        # Test case 5: Legislative proposal with specific date
        html_5 = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>
                    The Commission committed to come forward with a legislative proposal 
                    by May 2018 to ensure that the scientific evaluation of pesticides 
                    for EU regulatory approval is based only on published studies.
                </p>
            </div>
        </div>
        """

        extractor_5 = FollowupWebsiteExtractor(html_5)
        result_5 = extractor_5.extract_commissions_deadlines()

        assert result_5 is not None, "Should extract deadline"
        assert "2018-05-31" in result_5, "Should contain 2018-05-31"
        assert (
            "legislative proposal" in result_5["2018-05-31"].lower()
        ), "Should mention legislative proposal"

        # Test case 6: No deadlines present
        html_6 = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>
                    The Commission decided to positively respond to the ECI. In its 
                    communication the Commission sets out plans for a legislative proposal.
                </p>
            </div>
        </div>
        """

        extractor_6 = FollowupWebsiteExtractor(html_6)
        result_6 = extractor_6.extract_commissions_deadlines()

        assert result_6 is None, "Should return None when no deadlines found"

        # Test case 7: Past deadline (closed date) should still be captured
        html_7 = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>
                    The call for evidence launched on 18 June 2025 and closed on 16 July 2025.
                </p>
            </div>
        </div>
        """

        extractor_7 = FollowupWebsiteExtractor(html_7)
        result_7 = extractor_7.extract_commissions_deadlines()

        # This depends on whether you want to capture "closed on" dates
        # If not capturing past dates, this should be None
        # If capturing, adjust assertion accordingly
        assert result_7 is None, "Should not capture 'closed on' dates (past deadlines)"

    def test_extract_commission_rejected_initiative(self):
        """Test detection of Commission rejection."""

        # Test case 1: Explicit rejection - will not make a legislative proposal
        html_1 = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>
                    The Commission has carefully examined this initiative and 
                    will not make a legislative proposal at this time. The existing 
                    framework already addresses the key concerns raised.
                </p>
            </div>
        </div>
        """

        extractor_1 = FollowupWebsiteExtractor(html_1)
        result_1 = extractor_1.extract_commission_rejected_initiative()

        assert result_1 is True, "Should detect explicit rejection"

        # Test case 2: Rejection - decided not to submit a legislative proposal
        html_2 = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>
                    After thorough analysis, the Commission has decided not to 
                    submit a legislative proposal on this matter. The current 
                    legislative framework is adequate.
                </p>
            </div>
        </div>
        """

        extractor_2 = FollowupWebsiteExtractor(html_2)
        result_2 = extractor_2.extract_commission_rejected_initiative()

        assert result_2 is True, "Should detect rejection decision"

        # Test case 3: Rejection - outside EU competence
        html_3 = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>
                    The Commission recognizes the importance of this issue, however 
                    the proposals fall outside the EU competence. Therefore, no 
                    legislative proposal will be brought forward.
                </p>
            </div>
        </div>
        """

        extractor_3 = FollowupWebsiteExtractor(html_3)
        result_3 = extractor_3.extract_commission_rejected_initiative()

        assert result_3 is True, "Should detect competence-based rejection"

        # Test case 4: Rejection with "no repeal" pattern
        html_4 = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>
                    Following the assessment, no repeal of the existing directive 
                    was proposed. The Commission will continue to monitor the 
                    situation and support Member States in implementation.
                </p>
            </div>
        </div>
        """

        extractor_4 = FollowupWebsiteExtractor(html_4)
        result_4 = extractor_4.extract_commission_rejected_initiative()

        assert result_4 is True, "Should detect no repeal rejection pattern"

        # Test case 5: Rejection - already covered by existing legislation
        html_5 = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>
                    The Commission notes that the concerns raised are already covered 
                    by existing legislation. The current policies already in place 
                    provide the necessary framework, and no new legislation will be proposed.
                </p>
            </div>
        </div>
        """

        extractor_5 = FollowupWebsiteExtractor(html_5)
        result_5 = extractor_5.extract_commission_rejected_initiative()

        assert result_5 is True, "Should detect rejection based on existing framework"

        # Test case 6: Rejection with actions - committed to non-legislative measures
        html_6 = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>
                    While the Commission will not make a legislative proposal on this 
                    matter, it is committed to supporting Member States through guidance 
                    and best practice sharing. The Commission will monitor the situation 
                    closely.
                </p>
            </div>
        </div>
        """

        extractor_6 = FollowupWebsiteExtractor(html_6)
        result_6 = extractor_6.extract_commission_rejected_initiative()

        assert result_6 is True, "Should detect rejection with non-legislative actions"

        # Test case 7: No rejection - Commission committed to proposal
        html_7 = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>
                    The Commission has committed to come forward with a legislative 
                    proposal by the end of 2025. This proposal will address the key 
                    concerns raised by the initiative.
                </p>
            </div>
        </div>
        """

        extractor_7 = FollowupWebsiteExtractor(html_7)
        result_7 = extractor_7.extract_commission_rejected_initiative()

        assert (
            result_7 is False
        ), "Should not detect rejection when committed to proposal"

        # Test case 8: No rejection - law already applicable
        html_8 = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>
                    Following the adoption of the regulation in 2024, the new rules 
                    became applicable on 1 January 2025. This addresses the core 
                    objectives of the initiative.
                </p>
            </div>
        </div>
        """

        extractor_8 = FollowupWebsiteExtractor(html_8)
        result_8 = extractor_8.extract_commission_rejected_initiative()

        assert (
            result_8 is False
        ), "Should not detect rejection for applicable legislation"

        # Test case 9: Rejection - no new legislation will be proposed
        html_9 = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>
                    The Commission appreciates the concerns raised. However, given 
                    the recently debated and agreed legislation on this topic, no 
                    new legislation will be proposed at this stage.
                </p>
            </div>
        </div>
        """

        extractor_9 = FollowupWebsiteExtractor(html_9)
        result_9 = extractor_9.extract_commission_rejected_initiative()

        assert (
            result_9 is True
        ), "Should detect rejection with 'no new legislation' phrase"

        # Test case 10: Rejection - neither scientific nor legal grounds
        html_10 = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>
                    After careful examination, the Commission concludes that there are 
                    neither scientific nor legal grounds to proceed with new legislation 
                    on this matter.
                </p>
            </div>
        </div>
        """

        extractor_10 = FollowupWebsiteExtractor(html_10)
        result_10 = extractor_10.extract_commission_rejected_initiative()

        assert (
            result_10 is True
        ), "Should detect rejection based on scientific/legal grounds"

        # Test case 1: Empty response section
        html_empty = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p></p>
            </div>
        </div>
        """

        extractor_empty = FollowupWebsiteExtractor(html_empty)

        # Should raise ValueError due to empty content
        with pytest.raises(ValueError, match="Could not extract legislative content"):
            extractor_empty.extract_commission_rejected_initiative()

        # Test case 2: Missing response section
        html_missing = """
        <div>
            <div class="ecl">
                <h2 id="some-other-section">Other Section</h2>
            </div>
            <div class="ecl">
                <p>Some content that is not a Commission response.</p>
            </div>
        </div>
        """

        extractor_missing = FollowupWebsiteExtractor(html_missing)

        # Should raise ValueError due to missing Answer section
        with pytest.raises(ValueError, match="Could not extract legislative content"):
            extractor_missing.extract_commission_rejected_initiative()

        # Test case 3: Mixed signals - rejection phrase but also commitment
        html_mixed = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>
                    While no new legislation will be proposed specifically for this 
                    initiative, the Commission has committed to come forward with a 
                    legislative proposal on the broader regulatory framework.
                </p>
            </div>
        </div>
        """

        extractor_mixed = FollowupWebsiteExtractor(html_mixed)
        result_mixed = extractor_mixed.extract_commission_rejected_initiative()

        # Should still detect rejection due to explicit rejection phrase
        assert (
            result_mixed is True
        ), "Should detect rejection even with commitment mentioned"

        # Test case 4: Case insensitivity test
        html_case = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>
                    The COMMISSION will NOT MAKE A LEGISLATIVE PROPOSAL on this matter.
                </p>
            </div>
        </div>
        """

        extractor_case = FollowupWebsiteExtractor(html_case)
        result_case = extractor_case.extract_commission_rejected_initiative()

        assert result_case is True, "Should handle case-insensitive rejection detection"

    def test_extract_commission_rejection_reason(self):
        """Test extraction of rejection reasoning."""
        # TODO: Implement test
        pass

    def test_extract_laws_actions(self):
        """Test extraction of legislative actions JSON."""
        # TODO: Implement test
        pass

    def test_extract_policies_actions(self):
        """Test extraction of non-legislative policy actions JSON."""
        # TODO: Implement test
        pass
