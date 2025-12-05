"""
Behavioural tests for follow-up activity extraction.

This module tests extraction of:
- Follow-up section presence detection
- Roadmap indicators
- Workshop indicators
- Partnership program indicators
- Court case references
- Follow-up event dates (latest and most future)
- Structured follow-up events with dates
"""

# Third party
import pytest
from bs4 import BeautifulSoup

# Local
from ECI_initiatives.extractor.responses_followup_website.parser.extractors import (
    FollowupWebsiteExtractor,
)


class TestFollowupActivityExtraction:
    """Tests for follow-up activity extraction."""

    @classmethod
    def setup_class(cls):
        """Setup extractor instance."""
        pass

    def test_extract_has_roadmap(self):
        """Test detection of roadmap indicators."""

        # Test case 1: Roadmap keyword present (lowercase)
        html_roadmap_present = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>
                    The Commission will develop a roadmap to phase out the use of 
                    caged farming systems by 2027, in consultation with stakeholders.
                </p>
            </div>
            <p class="ecl-social-media-share__description">Share this page</p>
        </div>
        """

        extractor_1 = FollowupWebsiteExtractor(html_roadmap_present)
        result_1 = extractor_1.extract_has_roadmap()

        assert result_1 is True, "Should detect 'roadmap' keyword"

        # Test case 2: Road map with space
        html_road_map_space = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>
                    The Commission has published a comprehensive road map outlining 
                    the steps to achieve these objectives over the next decade.
                </p>
            </div>
            <p class="ecl-social-media-share__description">Share this page</p>
        </div>
        """

        extractor_2 = FollowupWebsiteExtractor(html_road_map_space)
        result_2 = extractor_2.extract_has_roadmap()

        assert result_2 is True, "Should detect 'road map' with space"

        # Test case 3: No roadmap keywords
        html_no_roadmap = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>
                    The Commission will conduct a comprehensive assessment of current 
                    policies and propose new measures based on stakeholder feedback.
                </p>
            </div>
            <p class="ecl-social-media-share__description">Share this page</p>
        </div>
        """

        extractor_3 = FollowupWebsiteExtractor(html_no_roadmap)
        result_3 = extractor_3.extract_has_roadmap()

        assert result_3 is False, "Should return False when no roadmap keywords present"

        # Test case 4: Case insensitivity - uppercase
        html_uppercase = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>
                    The ROADMAP will be published in Q1 2025 to outline the transition strategy.
                </p>
            </div>
            <p class="ecl-social-media-share__description">Share this page</p>
        </div>
        """

        extractor_4 = FollowupWebsiteExtractor(html_uppercase)
        result_4 = extractor_4.extract_has_roadmap()

        assert result_4 is True, "Should detect uppercase 'ROADMAP'"

        # Test case 5: Case insensitivity - mixed case
        html_mixed_case = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>
                    A strategic RoadMap has been developed to guide implementation efforts.
                </p>
            </div>
            <p class="ecl-social-media-share__description">Share this page</p>
        </div>
        """

        extractor_5 = FollowupWebsiteExtractor(html_mixed_case)
        result_5 = extractor_5.extract_has_roadmap()

        assert result_5 is True, "Should detect mixed case 'RoadMap'"

        # Test case 6: Roadmap in multiple paragraphs
        html_multiple_paragraphs = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>
                    The Commission has initiated several policy measures.
                </p>
                <p>
                    A detailed roadmap will be established to coordinate these efforts.
                </p>
                <p>
                    Implementation will begin in 2026.
                </p>
            </div>
            <p class="ecl-social-media-share__description">Share this page</p>
        </div>
        """

        extractor_6 = FollowupWebsiteExtractor(html_multiple_paragraphs)
        result_6 = extractor_6.extract_has_roadmap()

        assert result_6 is True, "Should detect roadmap in second paragraph"

        # Test case 7: Roadmap in list items
        html_list = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <ul>
                    <li>Stakeholder consultation</li>
                    <li>Development of a comprehensive roadmap</li>
                    <li>Implementation monitoring</li>
                </ul>
            </div>
            <p class="ecl-social-media-share__description">Share this page</p>
        </div>
        """

        extractor_7 = FollowupWebsiteExtractor(html_list)
        result_7 = extractor_7.extract_has_roadmap()

        assert result_7 is True, "Should detect roadmap in list items"

        # Test case 8: False positive - "broad map" should not match
        html_false_positive = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>
                    The Commission has developed a broad map of policy interventions 
                    across Member States to address these challenges.
                </p>
            </div>
            <p class="ecl-social-media-share__description">Share this page</p>
        </div>
        """

        extractor_8 = FollowupWebsiteExtractor(html_false_positive)
        result_8 = extractor_8.extract_has_roadmap()

        assert result_8 is False, "Should not match 'broad map'"

        # Test case 9: Empty content
        html_empty = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
            </div>
            <p class="ecl-social-media-share__description">Share this page</p>
        </div>
        """

        extractor_9 = FollowupWebsiteExtractor(html_empty)
        result_9 = extractor_9.extract_has_roadmap()

        assert result_9 is False, "Should return False for empty content"

        # Test case 10: Roadmap in context
        html_context = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>
                    The Commission is committed to working with Member States to develop 
                    a roadmap to phase out harmful practices by 2030, ensuring a gradual 
                    and sustainable transition that takes into account the economic impact 
                    on affected industries.
                </p>
            </div>
            <p class="ecl-social-media-share__description">Share this page</p>
        </div>
        """

        extractor_10 = FollowupWebsiteExtractor(html_context)
        result_10 = extractor_10.extract_has_roadmap()

        assert result_10 is True, "Should detect roadmap in longer contextual text"

    def test_extract_has_workshop(self):
        """Test detection of workshop indicators."""

        # Test case 1: Workshop keyword present (singular)
        html_workshop_singular = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>
                    The Commission organized a workshop with stakeholders to discuss 
                    the implementation of new animal welfare standards.
                </p>
            </div>
            <p class="ecl-social-media-share__description">Share this page</p>
        </div>
        """

        extractor_1 = FollowupWebsiteExtractor(html_workshop_singular)
        result_1 = extractor_1.extract_has_workshop()

        assert result_1 is True, "Should detect 'workshop' keyword"

        # Test case 2: Workshops (plural)
        html_workshops_plural = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>
                    Several workshops were held across Member States to gather input 
                    from industry representatives and civil society organizations.
                </p>
            </div>
            <p class="ecl-social-media-share__description">Share this page</p>
        </div>
        """

        extractor_2 = FollowupWebsiteExtractor(html_workshops_plural)
        result_2 = extractor_2.extract_has_workshop()

        assert result_2 is True, "Should detect 'workshops' plural"

        # Test case 3: Conference keyword
        html_conference = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>
                    A major conference on sustainable agriculture will be hosted 
                    by the Commission in Brussels next year.
                </p>
            </div>
            <p class="ecl-social-media-share__description">Share this page</p>
        </div>
        """

        extractor_3 = FollowupWebsiteExtractor(html_conference)
        result_3 = extractor_3.extract_has_workshop()

        assert result_3 is True, "Should detect 'conference' keyword"

        # Test case 4: Scientific conference
        html_scientific_conference = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>
                    EFSA will present findings at a scientific conference to be held in 2026.
                </p>
            </div>
            <p class="ecl-social-media-share__description">Share this page</p>
        </div>
        """

        extractor_4 = FollowupWebsiteExtractor(html_scientific_conference)
        result_4 = extractor_4.extract_has_workshop()

        assert result_4 is True, "Should detect 'scientific conference'"

        # Test case 5: Stakeholder meeting
        html_stakeholder_meeting = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>
                    The Commission conducted stakeholder meetings throughout 2024 to 
                    gather feedback on proposed measures.
                </p>
            </div>
            <p class="ecl-social-media-share__description">Share this page</p>
        </div>
        """

        extractor_5 = FollowupWebsiteExtractor(html_stakeholder_meeting)
        result_5 = extractor_5.extract_has_workshop()

        assert result_5 is True, "Should detect 'stakeholder meetings'"

        # Test case 6: Organized workshop (UK spelling)
        html_organised_workshop = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>
                    The Commission organised workshops in collaboration with Member States.
                </p>
            </div>
            <p class="ecl-social-media-share__description">Share this page</p>
        </div>
        """

        extractor_6 = FollowupWebsiteExtractor(html_organised_workshop)
        result_6 = extractor_6.extract_has_workshop()

        assert result_6 is True, "Should detect 'organised workshops' (UK spelling)"

        # Test case 7: Organized conference (US spelling)
        html_organized_conference = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>
                    An organized conference brought together experts from across the EU.
                </p>
            </div>
            <p class="ecl-social-media-share__description">Share this page</p>
        </div>
        """

        extractor_7 = FollowupWebsiteExtractor(html_organized_conference)
        result_7 = extractor_7.extract_has_workshop()

        assert result_7 is True, "Should detect 'organized conference' (US spelling)"

        # Test case 8: Series of workshops
        html_series_workshops = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>
                    A series of workshops is planned to engage with various stakeholders.
                </p>
            </div>
            <p class="ecl-social-media-share__description">Share this page</p>
        </div>
        """

        extractor_8 = FollowupWebsiteExtractor(html_series_workshops)
        result_8 = extractor_8.extract_has_workshop()

        assert result_8 is True, "Should detect 'series of workshops'"

        # Test case 9: Roundtable
        html_roundtable = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>
                    The Commission hosted a roundtable discussion with industry leaders.
                </p>
            </div>
            <p class="ecl-social-media-share__description">Share this page</p>
        </div>
        """

        extractor_9 = FollowupWebsiteExtractor(html_roundtable)
        result_9 = extractor_9.extract_has_workshop()

        assert result_9 is True, "Should detect 'roundtable'"

        # Test case 10: Symposium
        html_symposium = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>
                    An international symposium on animal welfare will take place in June.
                </p>
            </div>
            <p class="ecl-social-media-share__description">Share this page</p>
        </div>
        """

        extractor_10 = FollowupWebsiteExtractor(html_symposium)
        result_10 = extractor_10.extract_has_workshop()

        assert result_10 is True, "Should detect 'symposium'"

        # Test case 11: Symposia (plural)
        html_symposia = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>
                    Multiple symposia were organized to discuss various aspects of the policy.
                </p>
            </div>
            <p class="ecl-social-media-share__description">Share this page</p>
        </div>
        """

        extractor_11 = FollowupWebsiteExtractor(html_symposia)
        result_11 = extractor_11.extract_has_workshop()

        assert result_11 is True, "Should detect 'symposia'"

        # Test case 12: Seminar
        html_seminar = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>
                    A technical seminar was held to present the latest research findings.
                </p>
            </div>
            <p class="ecl-social-media-share__description">Share this page</p>
        </div>
        """

        extractor_12 = FollowupWebsiteExtractor(html_seminar)
        result_12 = extractor_12.extract_has_workshop()

        assert result_12 is True, "Should detect 'seminar'"

        # Test case 13: No workshop keywords
        html_no_workshop = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>
                    The Commission will conduct a comprehensive assessment of current 
                    policies and propose new measures based on feedback.
                </p>
            </div>
            <p class="ecl-social-media-share__description">Share this page</p>
        </div>
        """

        extractor_13 = FollowupWebsiteExtractor(html_no_workshop)
        result_13 = extractor_13.extract_has_workshop()

        assert (
            result_13 is False
        ), "Should return False when no workshop keywords present"

        # Test case 14: Case insensitivity - uppercase
        html_uppercase = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>
                    The WORKSHOP will be held in Brussels to discuss implementation strategies.
                </p>
            </div>
            <p class="ecl-social-media-share__description">Share this page</p>
        </div>
        """

        extractor_14 = FollowupWebsiteExtractor(html_uppercase)
        result_14 = extractor_14.extract_has_workshop()

        assert result_14 is True, "Should detect uppercase 'WORKSHOP'"

        # Test case 15: Case insensitivity - mixed case
        html_mixed_case = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>
                    A high-level Conference will bring together policymakers and experts.
                </p>
            </div>
            <p class="ecl-social-media-share__description">Share this page</p>
        </div>
        """

        extractor_15 = FollowupWebsiteExtractor(html_mixed_case)
        result_15 = extractor_15.extract_has_workshop()

        assert result_15 is True, "Should detect mixed case 'Conference'"

        # Test case 16: Workshop in list items
        html_list = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <ul>
                    <li>Stakeholder consultation</li>
                    <li>Technical workshop on implementation</li>
                    <li>Impact assessment</li>
                </ul>
            </div>
            <p class="ecl-social-media-share__description">Share this page</p>
        </div>
        """

        extractor_16 = FollowupWebsiteExtractor(html_list)
        result_16 = extractor_16.extract_has_workshop()

        assert result_16 is True, "Should detect workshop in list items"

        # Test case 17: Multiple workshop keywords in different paragraphs
        html_multiple = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>
                    The Commission initiated several consultations.
                </p>
                <p>
                    A workshop was organized in March 2024.
                </p>
                <p>
                    Additionally, a conference is planned for 2025.
                </p>
            </div>
            <p class="ecl-social-media-share__description">Share this page</p>
        </div>
        """

        extractor_17 = FollowupWebsiteExtractor(html_multiple)
        result_17 = extractor_17.extract_has_workshop()

        assert result_17 is True, "Should detect workshop in multiple paragraphs"

        # Test case 18: Empty content
        html_empty = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
            </div>
            <p class="ecl-social-media-share__description">Share this page</p>
        </div>
        """

        extractor_18 = FollowupWebsiteExtractor(html_empty)
        result_18 = extractor_18.extract_has_workshop()

        assert result_18 is False, "Should return False for empty content"

        # Test case 20: Scientific debate
        html_scientific_debate = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>
                    EFSA facilitated a scientific debate on the welfare implications 
                    of current farming practices.
                </p>
            </div>
            <p class="ecl-social-media-share__description">Share this page</p>
        </div>
        """

        extractor_20 = FollowupWebsiteExtractor(html_scientific_debate)
        result_20 = extractor_20.extract_has_workshop()

        assert result_20 is True, "Should detect 'scientific debate'"

    def test_extract_has_partnership_programs(self):
        """Test detection of partnership programs."""
        # TODO: Implement test
        pass

    def test_extract_court_cases_referenced(self):
        """Test extraction of court case references."""
        # TODO: Implement test for court case JSON structure
        pass

    def test_extract_followup_latest_date(self):
        """Test extraction of most recent follow-up date."""
        # TODO: Implement test
        pass

    def test_extract_followup_most_future_date(self):
        """Test extraction of most future follow-up date."""
        # TODO: Implement test
        pass

    def test_extract_followup_events_with_dates(self):
        """Test extraction of structured follow-up events."""
        # TODO: Test single date extraction
        # TODO: Test multiple dates per event
        # TODO: Test date format parsing
        # TODO: Test event description extraction
        pass
