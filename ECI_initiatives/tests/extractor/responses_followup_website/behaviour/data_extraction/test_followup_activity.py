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
from datetime import date
from unittest.mock import patch

# Local
from ECI_initiatives.extractor.responses_followup_website.parser.extractors import (
    FollowupWebsiteExtractor,
    FollowupWebsiteLegislativeOutcomeExtractor,
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

        # Test case 1: Partnership program (singular)
        html_partnership_program = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>
                    The Commission launched a partnership program with Member States 
                    to facilitate implementation of the new framework.
                </p>
            </div>
            <p class="ecl-social-media-share__description">Share this page</p>
        </div>
        """

        extractor_1 = FollowupWebsiteExtractor(html_partnership_program)
        result_1 = extractor_1.extract_has_partnership_programs()

        assert result_1 is True, "Should detect 'partnership program'"

        # Test case 2: Partnership programmes (plural, UK spelling)
        html_partnership_programmes = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>
                    Several partnership programmes have been established to support 
                    the transition to sustainable farming practices.
                </p>
            </div>
            <p class="ecl-social-media-share__description">Share this page</p>
        </div>
        """

        extractor_2 = FollowupWebsiteExtractor(html_partnership_programmes)
        result_2 = extractor_2.extract_has_partnership_programs()

        assert result_2 is True, "Should detect 'partnership programmes' (UK spelling)"

        # Test case 3: Partnership plans
        html_partnership_plans = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>
                    The Commission developed partnership plans to engage with 
                    international organizations and industry stakeholders.
                </p>
            </div>
            <p class="ecl-social-media-share__description">Share this page</p>
        </div>
        """

        extractor_3 = FollowupWebsiteExtractor(html_partnership_plans)
        result_3 = extractor_3.extract_has_partnership_programs()

        assert result_3 is True, "Should detect 'partnership plans'"

        # Test case 4: Public-public partnership
        html_public_public = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>
                    A public-public partnership between EU agencies will coordinate 
                    research efforts in this area.
                </p>
            </div>
            <p class="ecl-social-media-share__description">Share this page</p>
        </div>
        """

        extractor_4 = FollowupWebsiteExtractor(html_public_public)
        result_4 = extractor_4.extract_has_partnership_programs()

        assert result_4 is True, "Should detect 'public-public partnership'"

        # Test case 5: European partnership for
        html_european_partnership = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>
                    The Commission supports the European partnership for animal health 
                    and welfare research under Horizon Europe.
                </p>
            </div>
            <p class="ecl-social-media-share__description">Share this page</p>
        </div>
        """

        extractor_5 = FollowupWebsiteExtractor(html_european_partnership)
        result_5 = extractor_5.extract_has_partnership_programs()

        assert result_5 is True, "Should detect 'European partnership for'"

        # Test case 6: Partnership between
        html_partnership_between = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>
                    A partnership between the Commission and EFSA will strengthen 
                    scientific capacity in the field.
                </p>
            </div>
            <p class="ecl-social-media-share__description">Share this page</p>
        </div>
        """

        extractor_6 = FollowupWebsiteExtractor(html_partnership_between)
        result_6 = extractor_6.extract_has_partnership_programs()

        assert result_6 is True, "Should detect 'partnership between'"

        # Test case 7: Partnerships between (plural)
        html_partnerships_between = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>
                    Partnerships between Member States and third countries will 
                    facilitate knowledge exchange.
                </p>
            </div>
            <p class="ecl-social-media-share__description">Share this page</p>
        </div>
        """

        extractor_7 = FollowupWebsiteExtractor(html_partnerships_between)
        result_7 = extractor_7.extract_has_partnership_programs()

        assert result_7 is True, "Should detect 'partnerships between'"

        # Test case 8: Support to partnerships
        html_support_partnerships = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>
                    The Commission provides support to partnerships aimed at 
                    improving animal welfare standards.
                </p>
            </div>
            <p class="ecl-social-media-share__description">Share this page</p>
        </div>
        """

        extractor_8 = FollowupWebsiteExtractor(html_support_partnerships)
        result_8 = extractor_8.extract_has_partnership_programs()

        assert result_8 is True, "Should detect 'support to partnerships'"

        # Test case 9: Cooperation programme
        html_cooperation_programme = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>
                    A cooperation programme with international organizations will 
                    enhance research capacity.
                </p>
            </div>
            <p class="ecl-social-media-share__description">Share this page</p>
        </div>
        """

        extractor_9 = FollowupWebsiteExtractor(html_cooperation_programme)
        result_9 = extractor_9.extract_has_partnership_programs()

        assert result_9 is True, "Should detect 'cooperation programme'"

        # Test case 10: Collaboration programme
        html_collaboration_programme = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>
                    The Commission established a collaboration programme to work 
                    with Member States on implementation.
                </p>
            </div>
            <p class="ecl-social-media-share__description">Share this page</p>
        </div>
        """

        extractor_10 = FollowupWebsiteExtractor(html_collaboration_programme)
        result_10 = extractor_10.extract_has_partnership_programs()

        assert result_10 is True, "Should detect 'collaboration programme'"

        # Test case 11: Joint programme
        html_joint_programme = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>
                    A joint programme between EU and national authorities will 
                    coordinate monitoring activities.
                </p>
            </div>
            <p class="ecl-social-media-share__description">Share this page</p>
        </div>
        """

        extractor_11 = FollowupWebsiteExtractor(html_joint_programme)
        result_11 = extractor_11.extract_has_partnership_programs()

        assert result_11 is True, "Should detect 'joint programme'"

        # Test case 12: Formal partnership
        html_formal_partnership = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>
                    The Commission entered into a formal partnership with the World 
                    Organisation for Animal Health.
                </p>
            </div>
            <p class="ecl-social-media-share__description">Share this page</p>
        </div>
        """

        extractor_12 = FollowupWebsiteExtractor(html_formal_partnership)
        result_12 = extractor_12.extract_has_partnership_programs()

        assert result_12 is True, "Should detect 'formal partnership'"

        # Test case 13: Established partnership
        html_established_partnership = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>
                    An established partnership with research institutions will 
                    provide scientific evidence for policy development.
                </p>
            </div>
            <p class="ecl-social-media-share__description">Share this page</p>
        </div>
        """

        extractor_13 = FollowupWebsiteExtractor(html_established_partnership)
        result_13 = extractor_13.extract_has_partnership_programs()

        assert result_13 is True, "Should detect 'established partnership'"

        # Test case 14: International partners
        html_international_partners = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>
                    The Commission is working with international partners to align 
                    animal welfare standards globally.
                </p>
            </div>
            <p class="ecl-social-media-share__description">Share this page</p>
        </div>
        """

        extractor_14 = FollowupWebsiteExtractor(html_international_partners)
        result_14 = extractor_14.extract_has_partnership_programs()

        assert result_14 is True, "Should detect 'international partners'"

        # Test case 15: No partnership keywords
        html_no_partnership = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>
                    The Commission will conduct a comprehensive assessment and 
                    propose new measures based on stakeholder feedback.
                </p>
            </div>
            <p class="ecl-social-media-share__description">Share this page</p>
        </div>
        """

        extractor_15 = FollowupWebsiteExtractor(html_no_partnership)
        result_15 = extractor_15.extract_has_partnership_programs()

        assert (
            result_15 is False
        ), "Should return False when no partnership keywords present"

        # Test case 16: Case insensitivity - uppercase
        html_uppercase = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>
                    The Commission launched a PARTNERSHIP PROGRAM to support Member States.
                </p>
            </div>
            <p class="ecl-social-media-share__description">Share this page</p>
        </div>
        """

        extractor_16 = FollowupWebsiteExtractor(html_uppercase)
        result_16 = extractor_16.extract_has_partnership_programs()

        assert result_16 is True, "Should detect uppercase 'PARTNERSHIP PROGRAM'"

        # Test case 17: Case insensitivity - mixed case
        html_mixed_case = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>
                    A Joint Programme between agencies will coordinate research efforts.
                </p>
            </div>
            <p class="ecl-social-media-share__description">Share this page</p>
        </div>
        """

        extractor_17 = FollowupWebsiteExtractor(html_mixed_case)
        result_17 = extractor_17.extract_has_partnership_programs()

        assert result_17 is True, "Should detect mixed case 'Joint Programme'"

        # Test case 18: Partnership in list items
        html_list = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <ul>
                    <li>Stakeholder consultation</li>
                    <li>Development of partnership programmes</li>
                    <li>Implementation monitoring</li>
                </ul>
            </div>
            <p class="ecl-social-media-share__description">Share this page</p>
        </div>
        """

        extractor_18 = FollowupWebsiteExtractor(html_list)
        result_18 = extractor_18.extract_has_partnership_programs()

        assert result_18 is True, "Should detect partnership in list items"

        # Test case 19: Multiple partnership keywords
        html_multiple = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>
                    The Commission launched a partnership program with Member States.
                </p>
                <p>
                    Additionally, a cooperation programme with international partners 
                    will be established.
                </p>
            </div>
            <p class="ecl-social-media-share__description">Share this page</p>
        </div>
        """

        extractor_19 = FollowupWebsiteExtractor(html_multiple)
        result_19 = extractor_19.extract_has_partnership_programs()

        assert result_19 is True, "Should detect multiple partnership keywords"

        # Test case 20: Empty content
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

        extractor_20 = FollowupWebsiteExtractor(html_empty)
        result_20 = extractor_20.extract_has_partnership_programs()

        assert result_20 is False, "Should return False for empty content"

        # Test case 21: Partnership in context
        html_context = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>
                    The Commission is committed to establishing a formal partnership 
                    with international organizations to develop global standards for 
                    animal welfare. This partnership programme will facilitate knowledge 
                    exchange and coordinate research efforts across borders.
                </p>
            </div>
            <p class="ecl-social-media-share__description">Share this page</p>
        </div>
        """

        extractor_21 = FollowupWebsiteExtractor(html_context)
        result_21 = extractor_21.extract_has_partnership_programs()

        assert result_21 is True, "Should detect partnership in longer contextual text"

        # Test case 22: False positive check - "partnerships" not followed by relevant words
        html_false_positive = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>
                    The Commission encourages partnerships. This will improve outcomes.
                </p>
            </div>
            <p class="ecl-social-media-share__description">Share this page</p>
        </div>
        """

        extractor_22 = FollowupWebsiteExtractor(html_false_positive)
        result_22 = extractor_22.extract_has_partnership_programs()

        assert (
            result_22 is False
        ), "Should not match standalone 'partnerships' without context"

        # Test case 23: Public-public partnerships (plural)
        html_public_public_plural = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>
                    Several public-public partnerships have been formed to address 
                    cross-border animal health issues.
                </p>
            </div>
            <p class="ecl-social-media-share__description">Share this page</p>
        </div>
        """

        extractor_23 = FollowupWebsiteExtractor(html_public_public_plural)
        result_23 = extractor_23.extract_has_partnership_programs()

        assert result_23 is True, "Should detect 'public-public partnerships' (plural)"

    def test_extract_court_cases_referenced(self):
        """Test extraction of court case references."""

        # Test case 1: No court cases - returns None or empty
        html_no_cases = """
        <div>
            <div class="ecl">
                <h2 class="ecl-u-type-heading-2" id="response-of-the-commission">
                    Response of the Commission
                </h2>
            </div>
            <div class="ecl">
                <p>
                    The Commission published the response to this initiative on 7 December 2023.
                    No legal proceedings have been initiated.
                </p>
            </div>
        </div>
        """
        extractor_1 = FollowupWebsiteExtractor(html_no_cases)
        result_1 = extractor_1.extract_court_cases_referenced()

        assert (
            result_1 is None or result_1 == []
        ), f"Expected None or empty list, got {result_1}"

        # Test case 2: Single court case referenced
        html_single_case = """
        <div>
            <div class="ecl">
                <h2 class="ecl-u-type-heading-2" id="response-of-the-commission">
                    Response of the Commission
                </h2>
            </div>
            <div class="ecl">
                <p>
                    The Commission's decision was challenged before the European Court of Justice 
                    in Case C-123/23. The Court ruled on 15 March 2024 that the Commission's 
                    assessment was lawful.
                </p>
            </div>
        </div>
        """
        extractor_2 = FollowupWebsiteExtractor(html_single_case)
        result_2 = extractor_2.extract_court_cases_referenced()

        assert result_2 is not None, "Should find court case reference"
        assert isinstance(
            result_2, (list, dict)
        ), "Should return list or dict structure"
        if isinstance(result_2, list):
            assert len(result_2) >= 1, "Should contain at least one court case"

        # Test case 3: Multiple court cases
        html_multiple_cases = """
        <div>
            <div class="ecl">
                <h2 class="ecl-u-type-heading-2" id="follow-up-on-the-commissions-actions">
                    Follow-up on the Commission's actions
                </h2>
            </div>
            <div class="ecl">
                <p>
                    Legal challenges were brought in Case C-456/22 and Case C-789/23.
                    The General Court delivered its judgment in Case T-111/23 on 10 June 2024.
                </p>
            </div>
        </div>
        """
        extractor_3 = FollowupWebsiteExtractor(html_multiple_cases)
        result_3 = extractor_3.extract_court_cases_referenced()

        assert result_3 is not None, "Should find multiple court case references"
        # Result is a dict with structure: {"court_of_justice": [...], "general_court": [...]}
        if isinstance(result_3, dict):
            total_cases = sum(len(v) for v in result_3.values())
            assert (
                total_cases >= 2
            ), f"Should contain at least 2 court cases, found {total_cases}"

        # Test case 4: Court case with detailed information
        html_detailed_case = """
        <div>
            <div class="ecl">
                <h2 class="ecl-u-type-heading-2" id="response-of-the-commission">
                    Response of the Commission
                </h2>
            </div>
            <div class="ecl">
                <p>
                    An action for annulment was filed with the European Court of Justice 
                    (Case C-234/24) challenging the Commission's decision. The proceedings 
                    are ongoing, with a hearing scheduled for December 2025.
                </p>
            </div>
        </div>
        """
        extractor_4 = FollowupWebsiteExtractor(html_detailed_case)
        result_4 = extractor_4.extract_court_cases_referenced()

        assert result_4 is not None, "Should find court case with details"
        assert isinstance(result_4, dict), "Should return dict structure"
        assert "court_of_justice" in result_4, "Should identify Court of Justice case"

        # Test case 5: Court names without case numbers
        html_court_no_number = """
        <div>
            <div class="ecl">
                <h2 class="ecl-u-type-heading-2" id="response-of-the-commission">
                    Response of the Commission
                </h2>
            </div>
            <div class="ecl">
                <p>
                    The matter was referred to the European Court of Justice for a preliminary 
                    ruling. The Court's decision is expected in 2025.
                </p>
            </div>
        </div>
        """
        extractor_5 = FollowupWebsiteExtractor(html_court_no_number)
        result_5 = extractor_5.extract_court_cases_referenced()

        # May return None if implementation requires case numbers
        # This tests the edge case of court mentions without formal case numbers
        assert result_5 is None or isinstance(
            result_5, dict
        ), "Should handle court mentions without case numbers gracefully"

    def test_extract_followup_latest_date(self):
        """Test extraction of most recent follow-up date."""
        from datetime import date
        from unittest.mock import patch
        from bs4 import BeautifulSoup

        # Use a fixed "today" date for all tests
        test_today = date(2024, 12, 5)

        # Test 1: Normal case - multiple dates, returns latest that is <= today
        html_multiple_dates = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>The Commission published a report on 15 March 2024.</p>

                <p>A workshop was held on 20 June 2024.</p>
                <p>The latest update was made on 10 September 2024.</p>
            </div>
            <p class="ecl-social-media-share__description">Share this page</p>
        </div>
        """

        extractor_1 = FollowupWebsiteLegislativeOutcomeExtractor("TEST_001")
        with patch.object(extractor_1, "_get_today_date", return_value=test_today):
            soup_1 = BeautifulSoup(html_multiple_dates, "html.parser")
            result_1 = extractor_1.extract_followup_latest_date(soup_1)
            assert (
                result_1 == "2024-09-10"
            ), "Should return latest date that is not in the future"

        # Test 2: Future dates filtered out - only returns dates <= today
        html_with_future = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>Past event on 15 March 2024.</p>
                <p>Current event on 1 December 2024.</p>
                <p>Future deadline on 15 December 2024.</p>
            </div>
            <p class="ecl-social-media-share__description">Share this page</p>
        </div>
        """

        extractor_2 = FollowupWebsiteLegislativeOutcomeExtractor("TEST_002")
        with patch.object(extractor_2, "_get_today_date", return_value=test_today):
            soup_2 = BeautifulSoup(html_with_future, "html.parser")
            result_2 = extractor_2.extract_followup_latest_date(soup_2)
            assert (
                result_2 == "2024-12-01"
            ), "Should filter out future dates (Dec 15) and return Dec 1"

        # Test 3: No dates found - returns None
        html_no_dates = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
                <p>The Commission is working on this initiative.</p>
                <p>No specific dates mentioned in this content.</p>
            </div>
            <p class="ecl-social-media-share__description">Share this page</p>
        </div>
        """

        extractor_3 = FollowupWebsiteLegislativeOutcomeExtractor("TEST_003")
        with patch.object(extractor_3, "_get_today_date", return_value=test_today):
            soup_3 = BeautifulSoup(html_no_dates, "html.parser")
            result_3 = extractor_3.extract_followup_latest_date(soup_3)
            assert (
                result_3 is None
            ), "Should return None when no dates are found in content"

        # Test 4: No Answer section - returns None
        html_no_section = """
        <div>
            <div class="ecl">
                <h2 id="some-other-section">Some Other Section</h2>
            </div>
            <div class="ecl">
                <p>Content with date 15 March 2024.</p>
            </div>
            <p class="ecl-social-media-share__description">Share this page</p>
        </div>
        """

        extractor_4 = FollowupWebsiteLegislativeOutcomeExtractor("TEST_004")
        with patch.object(extractor_4, "_get_today_date", return_value=test_today):
            soup_4 = BeautifulSoup(html_no_section, "html.parser")
            try:
                extractor_4.extract_followup_latest_date(soup_4)
                assert False, "Should raise ValueError when Answer section is not found"
            except ValueError as e:
                assert (
                    "answer section not found for" in str(e).lower()
                ), "ValueError should mention Answer section not found"

        # Test 5: Various date formats
        html_various_formats = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>Full month: 15 March 2024</p>
                <p>Abbreviated: 20 Jun 2024</p>
                <p>ISO format: 2024-09-10</p>
                <p>Slash format: 25/11/2024</p>
                <p>Month only: February 2024</p>
            </div>
            <p class="ecl-social-media-share__description">Share this page</p>
        </div>
        """

        extractor_5 = FollowupWebsiteLegislativeOutcomeExtractor("TEST_005")
        with patch.object(extractor_5, "_get_today_date", return_value=test_today):
            soup_5 = BeautifulSoup(html_various_formats, "html.parser")
            result_5 = extractor_5.extract_followup_latest_date(soup_5)
            assert (
                result_5 == "2024-11-25"
            ), "Should parse various date formats and return latest"

        # Test 6: All dates are in future - returns None
        html_all_future = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>Upcoming event on 15 March 2025.</p>
            </div>
            <div class="ecl">
                <p>Future deadline on 20 June 2025.</p>
            </div>
            <p class="ecl-social-media-share__description">Share this page</p>
        </div>
        """

        extractor_6 = FollowupWebsiteLegislativeOutcomeExtractor("TEST_006")
        with patch.object(extractor_6, "_get_today_date", return_value=test_today):
            soup_6 = BeautifulSoup(html_all_future, "html.parser")
            result_6 = extractor_6.extract_followup_latest_date(soup_6)
            assert (
                result_6 is None
            ), "Should return None when all dates are in the future"

        # Test 7: Date equals today - should be included
        html_today = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>Published today: 5 December 2024</p>
            </div>
            <p class="ecl-social-media-share__description">Share this page</p>
        </div>
        """

        extractor_7 = FollowupWebsiteLegislativeOutcomeExtractor("TEST_007")
        with patch.object(extractor_7, "_get_today_date", return_value=test_today):
            soup_7 = BeautifulSoup(html_today, "html.parser")
            result_7 = extractor_7.extract_followup_latest_date(soup_7)
            assert (
                result_7 == "2024-12-05"
            ), "Should include dates equal to today (boundary case)"

        # Test 8: Empty content elements - raises ValueError
        html_no_content = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <p class="ecl-social-media-share__description">Share this page</p>
        </div>
        """

        extractor_8 = FollowupWebsiteLegislativeOutcomeExtractor("TEST_008")
        with patch.object(extractor_8, "_get_today_date", return_value=test_today):
            soup_8 = BeautifulSoup(html_no_content, "html.parser")
            try:
                extractor_8.extract_followup_latest_date(soup_8)
                assert False, "Should raise ValueError when no content elements found"
            except ValueError as e:
                error_msg = str(e).lower()
                assert (
                    "expected at least one element with tags" in error_msg
                ), f"ValueError should mention expected element tags, but got: {str(e)}"

        # Test 9: Unparseable date formats ignored
        html_mixed_valid_invalid = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>Valid date: 15 March 2024</p>
                <p>Invalid: sometime in spring</p>
                <p>Another valid: 20 June 2024</p>
            </div>
            <p class="ecl-social-media-share__description">Share this page</p>
        </div>
        """

        extractor_9 = FollowupWebsiteLegislativeOutcomeExtractor("TEST_009")
        with patch.object(extractor_9, "_get_today_date", return_value=test_today):
            soup_9 = BeautifulSoup(html_mixed_valid_invalid, "html.parser")
            result_9 = extractor_9.extract_followup_latest_date(soup_9)
            assert (
                result_9 == "2024-06-20"
            ), "Should ignore unparseable dates and return latest valid date"

        # Test 10: Real-world example - End the Cage Age scenario
        html_real_world = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>As established by the Vision for Agriculture adopted on 19 February 2024.</p>
                <p>Further to the call for evidence launched on 18 March 2024 
                (and closed on 16 May 2024), the Commission published on 19 September 2024 
                a public consultation which will run until 12 December 2024.</p>
            </div>
            <p class="ecl-social-media-share__description">Share this page</p>
        </div>
        """

        extractor_10 = FollowupWebsiteLegislativeOutcomeExtractor("TEST_010")
        with patch.object(extractor_10, "_get_today_date", return_value=test_today):
            soup_10 = BeautifulSoup(html_real_world, "html.parser")
            result_10 = extractor_10.extract_followup_latest_date(soup_10)
            assert (
                result_10 == "2024-09-19"
            ), "Should return Sept 19, filtering out future Dec 12 deadline"

    def test_extract_followup_most_future_date(self):
        """Test extraction of most future follow-up date."""
        from datetime import date
        from unittest.mock import patch
        from bs4 import BeautifulSoup

        # Use a fixed "today" date for all tests
        test_today = date(2024, 12, 5)

        # Test 1: Normal case - multiple future dates, returns furthest future
        html_multiple_future = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>Upcoming deadline on 15 January 2025.</p>
                <p>Future workshop on 20 March 2025.</p>
                <p>Final deadline on 30 June 2025.</p>
            </div>
            <p class="ecl-social-media-share__description">Share this page</p>
        </div>
        """

        extractor_1 = FollowupWebsiteLegislativeOutcomeExtractor("TEST_001")
        with patch.object(extractor_1, "_get_today_date", return_value=test_today):
            soup_1 = BeautifulSoup(html_multiple_future, "html.parser")
            result_1 = extractor_1.extract_followup_most_future_date(soup_1)
            assert result_1 == "2025-06-30", "Should return furthest future date"

        # Test 2: Past dates filtered out - only returns dates > today
        html_mixed_dates = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>Past event on 15 March 2024.</p>
                <p>Today's event on 5 December 2024.</p>
                <p>Future deadline on 15 January 2025.</p>
            </div>
            <p class="ecl-social-media-share__description">Share this page</p>
        </div>
        """

        extractor_2 = FollowupWebsiteLegislativeOutcomeExtractor("TEST_002")
        with patch.object(extractor_2, "_get_today_date", return_value=test_today):
            soup_2 = BeautifulSoup(html_mixed_dates, "html.parser")
            result_2 = extractor_2.extract_followup_most_future_date(soup_2)
            assert (
                result_2 == "2025-01-15"
            ), "Should filter out past/present dates and return future date"

        # Test 3: No dates found - returns None
        html_no_dates = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
                <p>The Commission is working on this initiative.</p>
                <p>No specific dates mentioned in this content.</p>
            </div>
            <p class="ecl-social-media-share__description">Share this page</p>
        </div>
        """

        extractor_3 = FollowupWebsiteLegislativeOutcomeExtractor("TEST_003")
        with patch.object(extractor_3, "_get_today_date", return_value=test_today):
            soup_3 = BeautifulSoup(html_no_dates, "html.parser")
            result_3 = extractor_3.extract_followup_most_future_date(soup_3)
            assert (
                result_3 is None
            ), "Should return None when no dates are found in content"

        # Test 4: No Answer section - raises ValueError
        html_no_section = """
        <div>
            <div class="ecl">
                <h2 id="some-other-section">Some Other Section</h2>
            </div>
            <div class="ecl">
                <p>Content with date 15 March 2025.</p>
            </div>
            <p class="ecl-social-media-share__description">Share this page</p>
        </div>
        """

        extractor_4 = FollowupWebsiteLegislativeOutcomeExtractor("TEST_004")
        with patch.object(extractor_4, "_get_today_date", return_value=test_today):
            soup_4 = BeautifulSoup(html_no_section, "html.parser")
            try:
                extractor_4.extract_followup_most_future_date(soup_4)
                assert False, "Should raise ValueError when Answer section is not found"
            except ValueError as e:
                assert (
                    "answer section not found for" in str(e).lower()
                ), "ValueError should mention Answer section not found"

        # Test 5: Various date formats for future dates
        html_various_formats = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>Full month: 15 March 2025</p>
                <p>Abbreviated: 20 Jun 2025</p>
                <p>ISO format: 2025-09-10</p>
                <p>Slash format: 25/12/2025</p>
                <p>Month only: February 2025</p>
            </div>
            <p class="ecl-social-media-share__description">Share this page</p>
        </div>
        """

        extractor_5 = FollowupWebsiteLegislativeOutcomeExtractor("TEST_005")
        with patch.object(extractor_5, "_get_today_date", return_value=test_today):
            soup_5 = BeautifulSoup(html_various_formats, "html.parser")
            result_5 = extractor_5.extract_followup_most_future_date(soup_5)
            assert (
                result_5 == "2025-12-25"
            ), "Should parse various date formats and return furthest future"

        # Test 6: All dates are in past - returns None
        html_all_past = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>Past event on 15 March 2024.</p>
                <p>Old deadline on 20 June 2024.</p>
            </div>
            <p class="ecl-social-media-share__description">Share this page</p>
        </div>
        """

        extractor_6 = FollowupWebsiteLegislativeOutcomeExtractor("TEST_006")
        with patch.object(extractor_6, "_get_today_date", return_value=test_today):
            soup_6 = BeautifulSoup(html_all_past, "html.parser")
            result_6 = extractor_6.extract_followup_most_future_date(soup_6)
            assert result_6 is None, "Should return None when all dates are in the past"

        # Test 7: Date equals today - should NOT be included (must be > today)
        html_today = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>Published today: 5 December 2024</p>
            </div>
            <p class="ecl-social-media-share__description">Share this page</p>
        </div>
        """

        extractor_7 = FollowupWebsiteLegislativeOutcomeExtractor("TEST_007")
        with patch.object(extractor_7, "_get_today_date", return_value=test_today):
            soup_7 = BeautifulSoup(html_today, "html.parser")
            result_7 = extractor_7.extract_followup_most_future_date(soup_7)
            assert (
                result_7 is None
            ), "Should NOT include dates equal to today (must be strictly > today)"

        # Test 8: Empty content elements - raises ValueError
        html_no_content = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <p class="ecl-social-media-share__description">Share this page</p>
        </div>
        """

        extractor_8 = FollowupWebsiteLegislativeOutcomeExtractor("TEST_008")
        with patch.object(extractor_8, "_get_today_date", return_value=test_today):
            soup_8 = BeautifulSoup(html_no_content, "html.parser")
            try:
                extractor_8.extract_followup_most_future_date(soup_8)
                assert False, "Should raise ValueError when no content elements found"
            except ValueError as e:
                error_msg = str(e).lower()
                assert (
                    "expected at least one element with tags" in error_msg
                ), f"ValueError should mention expected element tags, but got: {str(e)}"

        # Test 9: Unparseable date formats ignored
        html_mixed_valid_invalid = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>Valid future date: 15 March 2025</p>
                <p>Invalid: sometime next year</p>
                <p>Another valid future: 20 June 2025</p>
            </div>
            <p class="ecl-social-media-share__description">Share this page</p>
        </div>
        """

        extractor_9 = FollowupWebsiteLegislativeOutcomeExtractor("TEST_009")
        with patch.object(extractor_9, "_get_today_date", return_value=test_today):
            soup_9 = BeautifulSoup(html_mixed_valid_invalid, "html.parser")
            result_9 = extractor_9.extract_followup_most_future_date(soup_9)
            assert (
                result_9 == "2025-06-20"
            ), "Should ignore unparseable dates and return furthest valid future date"

        # Test 10: Real-world example - End the Cage Age scenario (inverted)
        html_real_world = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>As established by the Vision for Agriculture adopted on 19 February 2024.</p>
                <p>Further to the call for evidence launched on 18 March 2024 
                (and closed on 16 May 2024), the Commission published on 19 September 2024 
                a public consultation which will run until 12 December 2024.</p>
            </div>
            <p class="ecl-social-media-share__description">Share this page</p>
        </div>
        """

        extractor_10 = FollowupWebsiteLegislativeOutcomeExtractor("TEST_010")
        with patch.object(extractor_10, "_get_today_date", return_value=test_today):
            soup_10 = BeautifulSoup(html_real_world, "html.parser")
            result_10 = extractor_10.extract_followup_most_future_date(soup_10)
            assert (
                result_10 == "2024-12-12"
            ), "Should return Dec 12 as it's the only future deadline (today is Dec 5)"

    def test_extract_followup_events_with_dates(self):
        """Test extraction of structured follow-up events."""
        # TODO: Test single date extraction
        # TODO: Test multiple dates per event
        # TODO: Test date format parsing
        # TODO: Test event description extraction
        pass
