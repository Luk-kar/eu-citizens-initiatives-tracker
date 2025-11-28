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

    def test_extract_final_outcome_status(self):
        """Test extraction of final outcome status."""
        # TODO: Implement test for status classification
        pass

    def test_extract_commission_promised_new_law(self):
        """Test detection of Commission commitment to new legislation."""
        # TODO: Implement test
        pass

    def test_extract_commission_rejected_initiative(self):
        """Test detection of Commission rejection."""
        # TODO: Implement test
        pass

    def test_extract_commission_rejection_reason(self):
        """Test extraction of rejection reasoning."""
        # TODO: Implement test
        pass

    def test_extract_commission_deadlines(self):
        """Test extraction of Commission deadline commitments."""
        # TODO: Implement test for deadline patterns
        pass

    def test_extract_laws_actions(self):
        """Test extraction of legislative actions JSON."""
        # TODO: Implement test
        pass

    def test_extract_policies_actions(self):
        """Test extraction of non-legislative policy actions JSON."""
        # TODO: Implement test
        pass

    def test_extract_law_implementation_date(self):
        """Test extraction of law implementation/applicable date."""
        # TODO: Implement test
        pass
