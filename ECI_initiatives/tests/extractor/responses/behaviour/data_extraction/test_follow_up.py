"""Tests for extracting follow-up activities from ECI response pages."""

# Standard library
from unittest.mock import patch
from datetime import date as date_type

# Third party
import pytest
from bs4 import BeautifulSoup

# Local
from ECI_initiatives.extractor.responses.parser.main_parser import ECIResponseHTMLParser
from ECI_initiatives.extractor.responses.responses_logger import (
    ResponsesExtractorLogger,
)


class TestFollowUpActivities:
    """Tests for follow-up activities extraction."""

    @classmethod
    def setup_class(cls):
        """Setup parser instance."""
        logger = ResponsesExtractorLogger().setup()
        cls.parser = ECIResponseHTMLParser(logger=logger)

    def test_has_followup_section_detection(self):
        """Test detection of follow-up section presence."""

        # Test 1: Standard Follow-up section with id attribute (h2 pattern)
        html_with_id = """
        <html>
            <body>
                <h2 id="Follow-up">Follow-up</h2>
                <p>This section provides regularly updated information...</p>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_with_id, "html.parser")
        result = self.parser.followup_activity.extract_has_followup_section(soup)
        assert result is True, "Should detect Follow-up section with id attribute"

        # Test 2: Follow-up section with strong tags (h2 pattern variant)
        html_with_strong = """
        <html>
            <body>
                <h2 id="Follow-up"><strong>Follow-up</strong></h2>
                <p>On 9 February 2024, Commissioner Stella Kyriakides met...</p>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_with_strong, "html.parser")
        result = self.parser.followup_activity.extract_has_followup_section(soup)
        assert result is True, "Should detect Follow-up section with strong tags"

        # Test 3: h4 Follow-up with whitespace and newlines (Minority SafePack pattern)
        html_h4_with_whitespace = """
        <html>
            <body>
                <h2 id="Answer-of-the-European-Commission-and-follow-up">
                    Answer of the European Commission and follow-up
                </h2>
                <h4>
                    Follow-up
                </h4>
                <p>The Commission monitors the implementation...</p>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_h4_with_whitespace, "html.parser")
        result = self.parser.followup_activity.extract_has_followup_section(soup)
        assert (
            result is True
        ), "Should detect h4 Follow-up with whitespace/newlines (regex pattern)"

        # Test 4: Case-insensitive matching with h4
        html_h4_lowercase = """
        <html>
            <body>
                <h4>follow-up</h4>
                <p>Follow-up activities content...</p>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_h4_lowercase, "html.parser")
        result = self.parser.followup_activity.extract_has_followup_section(soup)
        assert result is True, "Should handle case-insensitive Follow-up text in h4"

        # Test 5: Case-insensitive matching with h2 (legacy test)
        html_h2_lowercase = """
        <html>
            <body>
                <h2>follow-up</h2>
                <p>Follow-up activities content...</p>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_h2_lowercase, "html.parser")
        result = self.parser.followup_activity.extract_has_followup_section(soup)
        assert (
            result is False
        ), "Should NOT detect h2 without id (not a primary pattern)"

        # Test 6: No Follow-up section present
        html_no_followup = """
        <html>
            <body>
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>Initiative was submitted on 14 June 2023...</p>
                <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
                <p>The Commission adopted a Communication...</p>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_no_followup, "html.parser")
        result = self.parser.followup_activity.extract_has_followup_section(soup)
        assert result is False, "Should return False when no Follow-up section exists"

        # Test 7: Follow-up as h3 heading (should not match)
        html_wrong_heading = """
        <html>
            <body>
                <h2>Answer of the European Commission</h2>
                <h3>Follow-up</h3>
                <p>Subsection content...</p>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_wrong_heading, "html.parser")
        result = self.parser.followup_activity.extract_has_followup_section(soup)
        assert result is False, "Should only match h2 id or h4 tags, not h3"

        # Test 8: Real-world example from 2022_000002_en.html (Fur Free Europe - h2 pattern)
        html_real_world_1 = """
        <html>
            <body>
                <h2 id="Follow-up">Follow-up</h2>
                <p>On 9 February 2024, Commissioner Stella Kyriakides met with the organisers 
                of 'Fur Free Europe' to discuss the Commission's reply to the initiative.</p>
                <p>The Commission's work on the accompanying actions, as announced in the 
                Communication, has been progressing. See the 
                <a href="https://example.com">dedicated website</a> for details.</p>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_real_world_1, "html.parser")
        result = self.parser.followup_activity.extract_has_followup_section(soup)
        assert (
            result is True
        ), "Should detect real-world Follow-up section from Fur Free Europe"

        # Test 9: Real-world example from 2012_000003_en.html (Right2Water - h2 with strong)
        html_real_world_2 = """
        <html>
            <body>
                <h2 id="Follow-up"><strong>Follow-up</strong></h2>
                <p>This section provides regularly updated information on the follow-up 
                actions by the European Commission.</p>
                <p><strong>Legislative action:</strong></p>
                <ul>
                    <li>Amendment details with dates and links...</li>
                    <li>Proposal for revision with dates and links...</li>
                </ul>
                <p><strong>Implementation and review of existing EU legislation:</strong></p>
                <ul>
                    <li>Implementation reports...</li>
                </ul>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_real_world_2, "html.parser")
        result = self.parser.followup_activity.extract_has_followup_section(soup)
        assert (
            result is True
        ), "Should detect real-world Follow-up section from Right2Water"

        # Test 10: Real-world example from 2017_000004_en.html (Minority SafePack - h4 pattern)
        html_real_world_3 = """
        <html>
            <body>
                <h2 id="Answer-of-the-European-Commission-and-follow-up">
                    Answer of the European Commission and follow-up
                </h2>
                <h4>
                    Official document:
                </h4>
                <ul>
                    <li><a href="https://ec.europa.eu/transparency/...">Communication</a></li>
                </ul>
                <p>Main conclusions of the Communication:</p>
                <p>Inclusion and respect for the rich cultural diversity...</p>
                <h4>
                    Follow-up
                </h4>
                <p>The Commission monitors the implementation of a number of EU initiatives...</p>
                <ul>
                    <li>List item 1</li>
                    <li>List item 2</li>
                </ul>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_real_world_3, "html.parser")
        result = self.parser.followup_activity.extract_has_followup_section(soup)
        assert (
            result is True
        ), "Should detect real-world Follow-up section from Minority SafePack (h4 with whitespace)"

        # Test 11: Empty HTML document
        html_empty = "<html><body></body></html>"
        soup = BeautifulSoup(html_empty, "html.parser")
        result = self.parser.followup_activity.extract_has_followup_section(soup)
        assert result is False, "Should return False for empty document"

        # Test 12: Similar text but not exact match (boundary test)
        html_similar_text = """
        <html>
            <body>
                <h2>Follow-up Actions</h2>
                <p>Description of follow-up activities...</p>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_similar_text, "html.parser")
        result = self.parser.followup_activity.extract_has_followup_section(soup)
        assert (
            result is False
        ), "Should not match 'Follow-up Actions' - requires exact 'Follow-up' match"

        # Test 13: h4 with extra text (should not match - exact match required)
        html_h4_with_extra = """
        <html>
            <body>
                <h4>Follow-up Information</h4>
                <p>Content here...</p>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_h4_with_extra, "html.parser")
        result = self.parser.followup_activity.extract_has_followup_section(soup)
        assert (
            result is False
        ), "Should not match h4 with extra text - regex requires exact 'Follow-up'"

    def test_followup_events_extraction(self):
        """Test extraction of follow-up events information."""

        # Test 1: Simple Follow-up section without subsections (returns List[str])
        html_simple = """
        <html>
            <body>
                <h2 id="Follow-up">Follow-up</h2>
                <p>On 9 February 2024, Commissioner Stella Kyriakides met with the organisers.</p>
                <p>The Commission's work has been progressing.</p>
                <ul>
                    <li>First update on implementation</li>
                    <li>Second update on consultation</li>
                </ul>
                <h2 id="More-information">More information</h2>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_simple, "html.parser")
        result = self.parser.followup_activity.extract_followup_events(soup)

        assert isinstance(
            result, list
        ), "Should return list for simple Follow-up section"
        assert len(result) == 4, "Should extract 2 paragraphs and 2 list items"
        assert "Commissioner Stella Kyriakides" in result[0]
        assert "First update on implementation" in result[2]

        # Test 2: Follow-up section with subsections (returns Dict[str, List[str]])
        html_with_subsections = """
        <html>
            <body>
                <h2 id="Follow-up">Follow-up</h2>
                <p>This section provides regularly updated information...</p>
                
                <p><strong>Legislative action:</strong></p>
                <ul>
                    <li>Amendment to the Drinking Water Directive was adopted</li>
                    <li>Proposal for revision was submitted</li>
                </ul>
                
                <p><strong>Implementation and review:</strong></p>
                <ul>
                    <li>Implementation reports on the Water Framework Directive</li>
                </ul>
                
                <h2 id="More-information">More information</h2>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_with_subsections, "html.parser")
        result = self.parser.followup_activity.extract_followup_events(soup)

        assert isinstance(
            result, dict
        ), "Should return dict for Follow-up with subsections"
        assert (
            "Legislative action:" in result
        ), "Should have 'Legislative action:' subsection"
        assert (
            "Implementation and review:" in result
        ), "Should have 'Implementation and review:' subsection"
        assert (
            len(result["Legislative action:"]) == 2
        ), "Legislative action should have 2 items"
        assert (
            len(result["Implementation and review:"]) == 1
        ), "Implementation should have 1 item"
        assert (
            "Amendment to the Drinking Water Directive"
            in result["Legislative action:"][0]
        )

        # Test 3: Follow-up section with links preserved
        html_with_links = """
        <html>
            <body>
                <h2 id="Follow-up">Follow-up</h2>
                <p>
                    The Commission adopted a Communication on 7 December 2023. See 
                    <a href="https://ec.europa.eu/press/ip_23_6045">press release</a> 
                    and 
                    <a href="https://ec.europa.eu/qanda_23_6046">questions and answers</a>
                </p>
                <ul>
                    <li>
                        Several examples can be found in the 
                        <a href="https://op.europa.eu/en/publication/2024">2024 publication</a>.
                    </li>
                </ul>
                <h2 id="More-information">More information</h2>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_with_links, "html.parser")
        result = self.parser.followup_activity.extract_followup_events(soup)

        assert isinstance(result, list), "Should return list"
        assert len(result) == 2, "Should have 1 paragraph and 1 list item"
        assert "press release (https://ec.europa.eu/press/ip_23_6045)" in result[0]
        assert "questions and answers (https://ec.europa.eu/qanda_23_6046)" in result[0]
        assert (
            "2024 publication (https://op.europa.eu/en/publication/2024)" in result[1]
        )

        # Test 4: h4 Follow-up pattern (Minority SafePack)
        html_h4_pattern = """
        <html>
            <body>
                <h2 id="Answer-of-the-European-Commission-and-follow-up">
                    Answer of the European Commission and follow-up
                </h2>
                <h4>
                    Follow-up
                </h4>
                <p>The Commission monitors the implementation of EU initiatives.</p>
                <ul>
                    <li>The Commission implements funding programmes</li>
                    <li>Research opportunities in Horizon Europe</li>
                </ul>
                <h4>Other document</h4>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_h4_pattern, "html.parser")
        result = self.parser.followup_activity.extract_followup_events(soup)

        assert isinstance(result, list), "Should return list for h4 pattern"
        assert len(result) == 3, "Should have 1 paragraph and 2 list items"
        assert "Commission monitors" in result[0]

        # Test 5: "Other information" boundary marker
        html_with_boundary = """
        <html>
            <body>
                <h2 id="Follow-up">Follow-up</h2>
                <p>Implementation progressing as planned.</p>
                <ul>
                    <li>First action completed</li>
                </ul>
                <p><strong>Other information</strong></p>
                <p>This should not be included in extraction</p>
                <h2 id="More-information">More information</h2>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_with_boundary, "html.parser")
        result = self.parser.followup_activity.extract_followup_events(soup)

        assert isinstance(result, list), f"Should return list:\n{result}"
        assert len(result) == 2, "Should stop at 'Other information' marker"
        assert "This should not be included" not in str(result)

        # Test 6: No Follow-up section exists
        html_no_followup = """
        <html>
            <body>
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>Initiative was submitted on 14 June 2023...</p>
                <h2 id="Answer-of-the-European-Commission">Answer of the European Commission</h2>
                <p>The Commission adopted a Communication...</p>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_no_followup, "html.parser")
        result = self.parser.followup_activity.extract_followup_events(soup)

        assert result is None, "Should return None when no Follow-up section exists"

        # Test 7: Empty Follow-up section
        html_empty_followup = """
        <html>
            <body>
                <h2 id="Follow-up">Follow-up</h2>
                <h2 id="More-information">More information</h2>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_empty_followup, "html.parser")
        result = self.parser.followup_activity.extract_followup_events(soup)

        assert result is None, "Should return None for empty Follow-up section"

        # Test 8: Complex subsections with mixed content
        html_complex = """
        <html>
            <body>
                <h2 id="Follow-up">Follow-up</h2>
                <p>General introduction paragraph.</p>
                
                <p><strong>Legislative action:</strong></p>
                <p>Additional context for legislative actions.</p>
                <ul>
                    <li>Amendment adopted on <a href="https://eur-lex.europa.eu/123">1 February 2018</a></li>
                    <li>Proposal submitted to Parliament</li>
                </ul>
                
                <p><strong>Transparency and benchmarking:</strong></p>
                <ul>
                    <li>Stakeholder meetings held quarterly</li>
                </ul>
                
                <p><strong>Development cooperation:</strong></p>
                <p>The Commission identified water as a key priority.</p>
                
                <h2 id="More-information">More information</h2>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_complex, "html.parser")
        result = self.parser.followup_activity.extract_followup_events(soup)

        assert isinstance(result, dict), "Should return dict for complex subsections"
        assert len(result) == 3, "Should have 3 subsections"
        assert "Legislative action:" in result
        assert "Transparency and benchmarking:" in result
        assert "Development cooperation:" in result
        assert (
            len(result["Legislative action:"]) == 3
        ), "Should include context paragraph and 2 list items"
        assert (
            "1 February 2018 (https://eur-lex.europa.eu/123)"
            in result["Legislative action:"][1]
        )
        assert "key priority" in result["Development cooperation:"][0]

        # Test 9: Subsection with no content (edge case)
        html_empty_subsection = """
        <html>
            <body>
                <h2 id="Follow-up">Follow-up</h2>
                <p><strong>Empty subsection:</strong></p>
                <p><strong>Non-empty subsection:</strong></p>
                <ul>
                    <li>Item 1</li>
                </ul>
                <h2 id="More-information">More information</h2>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_empty_subsection, "html.parser")
        result = self.parser.followup_activity.extract_followup_events(soup)

        assert isinstance(result, dict), "Should return dict"
        assert "Non-empty subsection:" in result, "Should include non-empty subsection"
        assert "Empty subsection:" not in result, "Should not include empty subsection"

        # Test 10: Real-world example from Right2Water (extensive subsections)
        html_right2water = """
        <html>
            <body>
                <h2 id="Follow-up">Follow-up</h2>
                <p>This section provides regularly updated information on follow-up actions.</p>
                
                <p><strong>Legislative action:</strong></p>
                <ul>
                    <li>As a first step, an amendment to the Drinking Water Directive entered into force.</li>
                    <li>A proposal for revision was adopted on 01 February 2018. See <a href="https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=COM:2017:753:FIN">proposal</a>.</li>
                </ul>
                
                <p><strong>Implementation and review of existing EU legislation:</strong></p>
                <ul>
                    <li>Implementation reports on the Water Framework Directive published.</li>
                </ul>
                
                <p><strong>The European Pilar of Social Rights:</strong></p>
                <ul>
                    <li>The European Pillar proclaimed on 17 November 2017 includes access to water.</li>
                </ul>
                
                <h2 id="More-information">More information</h2>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_right2water, "html.parser")
        result = self.parser.followup_activity.extract_followup_events(soup)

        assert isinstance(result, dict), "Should return dict for real-world example"
        assert len(result) == 3, "Should have 3 subsections"
        assert "Legislative action:" in result
        assert "Implementation and review of existing EU legislation:" in result
        assert "The European Pilar of Social Rights:" in result
        assert len(result["Legislative action:"]) == 2
        assert (
            "proposal (https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=COM:2017:753:FIN)"
            in result["Legislative action:"][1]
        )

        # Test 11: Mixed inline formatting with links
        html_inline_formatting = """
        <html>
            <body>
                <h2 id="Follow-up">Follow-up</h2>
                <p>
                    The <strong>Commission</strong> published a 
                    <a href="https://ec.europa.eu/report">report</a> on 
                    <em>implementation progress</em>.
                </p>
                <h2>Next section</h2>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_inline_formatting, "html.parser")
        result = self.parser.followup_activity.extract_followup_events(soup)

        assert isinstance(result, list), "Should return list"
        assert len(result) == 1
        assert "Commission" in result[0]
        assert "report (https://ec.europa.eu/report)" in result[0]
        assert "implementation progress" in result[0]

    def test_has_roadmap_detection(self):
        """Test detection of roadmap presence in follow-up section."""

        # Test 1: Roadmap detected with keyword "roadmap"
        html_with_roadmap = """
        <html>
            <body>
                <h2 id="Follow-up">Follow-up</h2>
                <p>The Commission started work on a roadmap to phase out animal testing.</p>
                <p>This roadmap will be implemented over the next 5 years.</p>
                <h2 id="More-information">More information</h2>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_with_roadmap, "html.parser")
        result = self.parser.followup_activity.extract_has_roadmap(soup)
        assert result is True, "Should detect 'roadmap' keyword in Follow-up section"

        # Test 2: Roadmap detected with space variant "road map"
        html_with_road_map = """
        <html>
            <body>
                <h2 id="Follow-up">Follow-up</h2>
                <p>The Commission issued a road map for implementation.</p>
                <h2 id="More-information">More information</h2>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_with_road_map, "html.parser")
        result = self.parser.followup_activity.extract_has_roadmap(soup)
        assert result is True, "Should detect 'road map' variant"

        # Test 3: Roadmap detected with plural "roadmaps"
        html_with_roadmaps = """
        <html>
            <body>
                <h2 id="Follow-up">Follow-up</h2>
                <p>Multiple roadmaps have been developed to address the initiative.</p>
                <h2 id="More-information">More information</h2>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_with_roadmaps, "html.parser")
        result = self.parser.followup_activity.extract_has_roadmap(soup)
        assert result is True, "Should detect plural 'roadmaps'"

        # Test 4: No roadmap in Follow-up section
        html_no_roadmap = """
        <html>
            <body>
                <h2 id="Follow-up">Follow-up</h2>
                <p>The Commission implemented legislative measures.</p>
                <p>Stakeholder meetings were held to discuss implementation.</p>
                <h2 id="More-information">More information</h2>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_no_roadmap, "html.parser")
        result = self.parser.followup_activity.extract_has_roadmap(soup)
        assert result is False, "Should return False when no roadmap mentioned"

        # Test 5: Case-insensitive detection (uppercase)
        html_roadmap_uppercase = """
        <html>
            <body>
                <h2 id="Follow-up">Follow-up</h2>
                <p>A ROADMAP was adopted for phasing out practices.</p>
                <h2 id="More-information">More information</h2>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_roadmap_uppercase, "html.parser")
        result = self.parser.followup_activity.extract_has_roadmap(soup)
        assert result is True, "Should detect roadmap case-insensitively"

        # Test 6: No Follow-up section exists
        html_no_followup = """
        <html>
            <body>
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>Initiative submitted on 1 January 2020.</p>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_no_followup, "html.parser")
        result = self.parser.followup_activity.extract_has_roadmap(soup)
        assert result is False, "Should return False when no Follow-up section"

        # Test 7: h4 Follow-up pattern with roadmap
        html_h4_roadmap = """
        <html>
            <body>
                <h2 id="Answer-of-the-European-Commission-and-follow-up">
                    Answer and Follow-up
                </h2>
                <h4>Follow-up</h4>
                <p>The Commission developed a roadmap for sustainable implementation.</p>
                <h4>Other information</h4>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_h4_roadmap, "html.parser")
        result = self.parser.followup_activity.extract_has_roadmap(soup)
        assert result is True, "Should detect roadmap in h4 Follow-up pattern"

        # Test 8: Roadmap word appears but outside Follow-up section
        html_roadmap_outside = """
        <html>
            <body>
                <h2 id="Answer-of-the-European-Commission">Answer</h2>
                <p>The roadmap was mentioned in the answer section.</p>
                <h2 id="Follow-up">Follow-up</h2>
                <p>No additional information provided.</p>
                <h2 id="More-information">More information</h2>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_roadmap_outside, "html.parser")
        result = self.parser.followup_activity.extract_has_roadmap(soup)
        assert result is False, "Should only check content within Follow-up section"

    def test_has_workshop_detection(self):
        """Test detection of workshop activities in follow-up section."""

        # Test 1: Workshop detected with keyword "workshop"
        html_with_workshop = """
        <html>
            <body>
                <h2 id="Follow-up">Follow-up</h2>
                <p>A workshop on innovative partnerships was organized in November 2023.</p>
                <h2 id="More-information">More information</h2>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_with_workshop, "html.parser")
        result = self.parser.followup_activity.extract_has_workshop(soup)
        assert result is True, "Should detect 'workshop' keyword"

        # Test 2: Workshop detected with plural "workshops"
        html_with_workshops = """
        <html>
            <body>
                <h2 id="Follow-up">Follow-up</h2>
                <p>Multiple workshops were held throughout 2023 and 2024.</p>
                <h2 id="More-information">More information</h2>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_with_workshops, "html.parser")
        result = self.parser.followup_activity.extract_has_workshop(soup)
        assert result is True, "Should detect plural 'workshops'"

        # Test 3: Conference detected as workshop activity
        html_with_conference = """
        <html>
            <body>
                <h2 id="Follow-up">Follow-up</h2>
                <p>An international conference on biodiversity was held in Brussels.</p>
                <h2 id="More-information">More information</h2>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_with_conference, "html.parser")
        result = self.parser.followup_activity.extract_has_workshop(soup)
        assert result is True, "Should detect 'conference' as workshop-type activity"

        # Test 4: Stakeholder meeting detected
        html_with_stakeholder_meeting = """
        <html>
            <body>
                <h2 id="Follow-up">Follow-up</h2>
                <p>Stakeholder meetings were organized in quarterly intervals.</p>
                <h2 id="More-information">More information</h2>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_with_stakeholder_meeting, "html.parser")
        result = self.parser.followup_activity.extract_has_workshop(soup)
        assert result is True, "Should detect 'stakeholder meeting'"

        # Test 5: Multiple stakeholder meetings
        html_with_stakeholder_meetings = """
        <html>
            <body>
                <h2 id="Follow-up">Follow-up</h2>
                <p>Stakeholder meetings were conducted quarterly to review progress.</p>
                <h2 id="More-information">More information</h2>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_with_stakeholder_meetings, "html.parser")
        result = self.parser.followup_activity.extract_has_workshop(soup)
        assert result is True, "Should detect 'stakeholder meetings' plural"

        # Test 6: No workshop activity in Follow-up
        html_no_workshop = """
        <html>
            <body>
                <h2 id="Follow-up">Follow-up</h2>
                <p>The Commission published implementation guidelines.</p>
                <p>Legislative measures were adopted in 2023.</p>
                <h2 id="More-information">More information</h2>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_no_workshop, "html.parser")
        result = self.parser.followup_activity.extract_has_workshop(soup)
        assert result is False, "Should return False when no workshop mentioned"

        # Test 7: Case-insensitive detection
        html_workshop_uppercase = """
        <html>
            <body>
                <h2 id="Follow-up">Follow-up</h2>
                <p>A WORKSHOP and CONFERENCE were organized in 2024.</p>
                <h2 id="More-information">More information</h2>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_workshop_uppercase, "html.parser")
        result = self.parser.followup_activity.extract_has_workshop(soup)
        assert result is True, "Should detect workshop case-insensitively"

        # Test 8: No Follow-up section
        html_no_followup = """
        <html>
            <body>
                <h2 id="Answer-of-the-European-Commission">Answer</h2>
                <p>A workshop was discussed in the answer section.</p>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_no_followup, "html.parser")
        result = self.parser.followup_activity.extract_has_workshop(soup)
        assert result is False, "Should return False when no Follow-up section"

        # Test 9: h4 Follow-up with workshop
        html_h4_workshop = """
        <html>
            <body>
                <h2 id="Answer-of-the-European-Commission-and-follow-up">
                    Answer and Follow-up
                </h2>
                <h4>Follow-up</h4>
                <p>A dedicated workshop on Strengthening support to regional languages occurred in November 2023.</p>
                <h4>Other information</h4>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_h4_workshop, "html.parser")
        result = self.parser.followup_activity.extract_has_workshop(soup)
        assert result is True, "Should detect workshop in h4 Follow-up pattern"

        # Test 10: Scientific conference detected (scientific/academic engagement)
        html_scientific_conference = """
        <html>
            <body>
                <h2 id="Follow-up">Follow-up</h2>
                <p>A scientific conference engaging the scientific community and relevant 
                stakeholders was organized in December 2023 to discuss alternatives.</p>
                <h2 id="More-information">More information</h2>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_scientific_conference, "html.parser")
        result = self.parser.followup_activity.extract_has_workshop(soup)
        assert (
            result is True
        ), "Should detect 'scientific conference' as workshop activity"

        # Test 11: Series of workshops detected (series/multiple events)
        html_series_workshops = """
        <html>
            <body>
                <h2 id="Follow-up">Follow-up</h2>
                <p>Information on related workshops and conferences, organised since 2023. 
                A series of workshops has been planned to engage stakeholders.</p>
                <h2 id="More-information">More information</h2>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_series_workshops, "html.parser")
        result = self.parser.followup_activity.extract_has_workshop(soup)
        assert (
            result is True
        ), "Should detect 'series of workshops' as sustained engagement"

        # Test 12: Roundtable detected (other formal engagement formats)
        html_roundtable = """
        <html>
            <body>
                <h2 id="Follow-up">Follow-up</h2>
                <p>The Commission organized a roundtable with industry representatives 
                and civil society organizations to discuss implementation.</p>
                <h2 id="More-information">More information</h2>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_roundtable, "html.parser")
        result = self.parser.followup_activity.extract_has_workshop(soup)
        assert result is True, "Should detect 'roundtable' as formal engagement format"

        # Test 13: Symposium detected (other formal engagement formats)
        html_symposium = """
        <html>
            <body>
                <h2 id="Follow-up">Follow-up</h2>
                <p>An international symposium on animal welfare brought together experts 
                from academia and industry in June 2024.</p>
                <h2 id="More-information">More information</h2>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_symposium, "html.parser")
        result = self.parser.followup_activity.extract_has_workshop(soup)
        assert result is True, "Should detect 'symposium' as formal engagement format"

        # Test 14: Organized conference detected (organized/planned events)
        html_organized_conference = """
        <html>
            <body>
                <h2 id="Follow-up">Follow-up</h2>
                <p>The Commission organised conferences in collaboration with Member States 
                to discuss best practices for implementation.</p>
                <h2 id="More-information">More information</h2>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_organized_conference, "html.parser")
        result = self.parser.followup_activity.extract_has_workshop(soup)
        assert result is True, "Should detect 'organised conference' (UK spelling)"

        # Test 15: Standard ECI meeting NOT detected (negative test - important!)
        html_standard_meeting = """
        <html>
            <body>
                <h2 id="Follow-up">Follow-up</h2>
                <p>The organisers met with European Commission Vice-President 
                Věra Jourová and Commissioner Stella Kyriakides on 30 October 2020.</p>
                <p>A public hearing took place at the European Parliament.</p>
                <h2 id="More-information">More information</h2>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_standard_meeting, "html.parser")
        result = self.parser.followup_activity.extract_has_workshop(soup)
        assert (
            result is False
        ), "Should NOT detect standard 'met with' or 'public hearing' as workshop"

    def test_partnership_programs_extraction(self):
        """Test detection of partnership programs in follow-up section."""

        # Test 1: Partnership detected with keyword "partnership"
        html_with_partnership = """
        <html>
            <body>
                <h2 id="Follow-up">Follow-up</h2>
                <p>The Commission provided support to partnerships between water operators.</p>
                <h2 id="More-information">More information</h2>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_with_partnership, "html.parser")
        result = self.parser.followup_activity.extract_has_partnership_programs(soup)
        assert result is True, "Should detect 'partnership' keyword"

        # Test 2: Multiple partnerships detected
        html_with_partnerships = """
        <html>
            <body>
                <h2 id="Follow-up">Follow-up</h2>
                <p>Multiple partnerships and collaborative agreements were established.</p>
                <h2 id="More-information">More information</h2>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_with_partnerships, "html.parser")
        result = self.parser.followup_activity.extract_has_partnership_programs(soup)
        assert result is True, "Should detect plural 'partnerships'"

        # Test 3: Public-public partnership detected
        html_with_ppp = """
        <html>
            <body>
                <h2 id="Follow-up">Follow-up</h2>
                <p>Support to public-public partnerships in the water sector was provided.</p>
                <h2 id="More-information">More information</h2>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_with_ppp, "html.parser")
        result = self.parser.followup_activity.extract_has_partnership_programs(soup)
        assert result is True, "Should detect 'public-public partnership'"

        # Test 4: Water operators partnership detected
        html_with_water_operators = """
        <html>
            <body>
                <h2 id="Follow-up">Follow-up</h2>
                <p>Partnerships between water operators were fostered through capacity building.</p>
                <h2 id="More-information">More information</h2>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_with_water_operators, "html.parser")
        result = self.parser.followup_activity.extract_has_partnership_programs(soup)
        assert result is True, "Should detect 'water operators' keyword"

        # Test 5: Generic "partner" keyword detected
        html_with_partner = """
        <html>
            <body>
                <h2 id="Follow-up">Follow-up</h2>
                <p>The Commission partnered with international organizations.</p>
                <h2 id="More-information">More information</h2>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_with_partner, "html.parser")
        result = self.parser.followup_activity.extract_has_partnership_programs(soup)
        assert result is True, "Should detect 'partner' keyword"

        # Test 6: No partnership programs mentioned
        html_no_partnership = """
        <html>
            <body>
                <h2 id="Follow-up">Follow-up</h2>
                <p>The Commission adopted legislative measures.</p>
                <p>Implementation guidelines were published.</p>
                <h2 id="More-information">More information</h2>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_no_partnership, "html.parser")
        result = self.parser.followup_activity.extract_has_partnership_programs(soup)
        assert result is False, "Should return False when no partnership mentioned"

        # Test 7: Case-insensitive detection
        html_partnership_uppercase = """
        <html>
            <body>
                <h2 id="Follow-up">Follow-up</h2>
                <p>PARTNERSHIPS with international actors were established in 2023.</p>
                <h2 id="More-information">More information</h2>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_partnership_uppercase, "html.parser")
        result = self.parser.followup_activity.extract_has_partnership_programs(soup)
        assert result is True, "Should detect partnership case-insensitively"

        # Test 8: No Follow-up section
        html_no_followup = """
        <html>
            <body>
                <h2 id="Answer-of-the-European-Commission">Answer</h2>
                <p>Partnerships are mentioned in the answer section.</p>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_no_followup, "html.parser")
        result = self.parser.followup_activity.extract_has_partnership_programs(soup)
        assert result is False, "Should return False when no Follow-up section"

        # Test 9: h4 Follow-up with partnership
        html_h4_partnership = """
        <html>
            <body>
                <h2 id="Answer-of-the-European-Commission-and-follow-up">
                    Answer and Follow-up
                </h2>
                <h4>Follow-up</h4>
                <p>The Commission fostered partnerships between water operators in developing countries.</p>
                <h4>Other information</h4>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_h4_partnership, "html.parser")
        result = self.parser.followup_activity.extract_has_partnership_programs(soup)
        assert result is True, "Should detect partnership in h4 Follow-up pattern"

        # Test 10: Partnership mentioned but in subsection list
        html_partnership_in_list = """
        <html>
            <body>
                <h2 id="Follow-up">Follow-up</h2>
                <p><strong>Implementation actions:</strong></p>
                <ul>
                    <li>Support to partnerships between water operators and facilitating technology transfer</li>
                    <li>Capacity building for public-public partnerships in water services</li>
                </ul>
                <h2 id="More-information">More information</h2>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_partnership_in_list, "html.parser")
        result = self.parser.followup_activity.extract_has_partnership_programs(soup)
        assert (
            result is True
        ), "Should detect partnership even when mentioned in subsection lists"

    def test_court_cases_referenced(self):
        """Test extraction of Court of Justice case numbers."""

        # Test Case 1: Save Cruelty Free Cosmetics (2021_000006)
        # Contains General Court cases: T-655/20, T-656/20
        soup_2021_000006 = BeautifulSoup(
            """
            <html>
                <body>
                    <p>Judgments of the General Court on the relationship between REACH 
                    and the Cosmetic Products Regulation</p>
                    <p>T-655/20 and T-656/20</p>
                    <p>As stated in the response to the first objective of the initiative – 
                    'protect and strengthen the cosmetics animal testing ban' - the interface 
                    between the REACH Regulation and the Cosmetic Products Regulation was at 
                    the time being assessed by the Court of Justice of the European Union. 
                    The General Court issued its judgments on 22 November 2023 and clarified...</p>
                </body>
            </html>
            """,
            "html.parser",
        )
        result = self.parser.followup_activity.extract_court_cases_referenced(
            soup_2021_000006
        )
        assert result is not None
        assert "general_court" in result
        assert set(result["general_court"]) == {"T-655/20", "T-656/20"}
        assert "court_of_justice" not in result
        assert "ombudsman_decisions" not in result

        # Test Case 2: Minority SafePack (2017_000004)
        # Contains General Court case and Court of Justice case
        soup_2017_000004 = BeautifulSoup(
            """
            <html>
                <body>
                    <p>In a judgement of 9 November 2022 (case T-158/21), the General Court 
                    of the Court of Justice of the European Union dismissed the request of 
                    the organisers' group of 'Minority SafePack' to annul the Commission 
                    Communication C(2021) 171. The court held that the Commission has not 
                    erred in law nor infringed its obligations to state sufficient reasons 
                    in its communication, in which the Commission stated that no further 
                    legislation was necessary at this stage to achieve the objectives sought 
                    by the ECI.</p>
                    <p>The organisers filed an appeal against this judgment with the Court 
                    of Justice on 21 January 2023. The appeal was dismissed by the Court 
                    judgment of 5 June 2025. Case C-26/23 dismissed.</p>
                </body>
            </html>
            """,
            "html.parser",
        )
        result = self.parser.followup_activity.extract_court_cases_referenced(
            soup_2017_000004
        )
        assert result is not None
        assert "general_court" in result
        assert "court_of_justice" in result
        assert result["general_court"] == ["T-158/21"]
        assert result["court_of_justice"] == ["C-26/23"]
        assert "ombudsman_decisions" not in result

        # Test Case 3: Stop Vivisection (2012_000007)
        # Contains Ombudsman decision: 78/182
        soup_2012_000007 = BeautifulSoup(
            """
            <html>
                <body>
                    <p>On 18 April 2017, the European Ombudsman issued a decision 
                    concerning the initiative 'Stop Vivisection'. The Ombudsman concluded 
                    that there was no maladministration by the Commission. Case 78/182 
                    was concluded.</p>
                </body>
            </html>
            """,
            "html.parser",
        )
        result = self.parser.followup_activity.extract_court_cases_referenced(
            soup_2012_000007
        )
        assert result is not None
        assert "ombudsman_decisions" in result
        assert result["ombudsman_decisions"] == ["78/182"]
        assert "general_court" not in result
        assert "court_of_justice" not in result

        # Test Case 4: No court cases present
        soup_no_cases = BeautifulSoup(
            """
            <html>
                <body>
                    <p>This initiative has no court cases referenced.</p>
                    <p>It contains some text but no case numbers like T-123/45 or C-45/67.</p>
                </body>
            </html>
            """,
            "html.parser",
        )
        result = self.parser.followup_activity.extract_court_cases_referenced(
            soup_no_cases
        )
        assert "general_court" in result
        assert result["general_court"] == ["T-123/45"]
        assert "court_of_justice" in result
        assert result["court_of_justice"] == ["C-45/67"]

        # Test Case 5: Multiple cases of same type with duplicates
        soup_duplicates = BeautifulSoup(
            """
            <html>
                <body>
                    <p>As mentioned in case T-100/20, the court found...</p>
                    <p>This was related to T-100/20 again.</p>
                    <p>Also case T-200/21 was decided.</p>
                </body>
            </html>
            """,
            "html.parser",
        )
        result = self.parser.followup_activity.extract_court_cases_referenced(
            soup_duplicates
        )
        assert result is not None
        assert "general_court" in result
        assert len(result["general_court"]) == 2
        assert result["general_court"] == ["T-100/20", "T-200/21"]

        # Test Case 6: All three types of cases together
        soup_all_cases = BeautifulSoup(
            """
            <html>
                <body>
                    <p>Case T-655/20 and T-656/20 were General Court cases.</p>
                    <p>An appeal was filed as case C-26/23.</p>
                    <p>Additionally, the Ombudsman decision 78/182 was relevant.</p>
                </body>
            </html>
            """,
            "html.parser",
        )
        result = self.parser.followup_activity.extract_court_cases_referenced(
            soup_all_cases
        )
        assert result is not None
        assert set(result["general_court"]) == {"T-655/20", "T-656/20"}
        assert result["court_of_justice"] == ["C-26/23"]
        assert result["ombudsman_decisions"] == ["78/182"]

        # Test Case 7: En-dash variant (–) instead of hyphen (-)
        soup_endash = BeautifulSoup(
            """
            <html>
                <body>
                    <p>Case T–655/20 and C–26/23 with en-dashes.</p>
                </body>
            </html>
            """,
            "html.parser",
        )
        result = self.parser.followup_activity.extract_court_cases_referenced(
            soup_endash
        )
        assert result is not None
        assert "general_court" in result
        assert "court_of_justice" in result

        # Test Case 8: Exception handling
        with pytest.raises(ValueError, match="Error extracting court cases"):
            # Pass invalid input (not BeautifulSoup object)
            self.parser.followup_activity.extract_court_cases_referenced(None)

    def test_followup_latest_date(self):
        """Test extraction of most recent date from follow-up section.

        Tests multiple date formats and ensures the latest date is returned
        when multiple dates are present. Also verifies filtering of future dates.
        """

        # Mock today's date to 2025-11-06 for consistent testing
        mock_today = date_type(2025, 11, 6)

        with patch.object(
            self.parser.followup_activity, "_get_today_date", return_value=mock_today
        ):

            # Test case 1: Multiple dates with various formats - should return latest
            html_multiple_dates = """
            <html>
                <body>
                    <h2 id="Follow-up">Follow-up</h2>
                    <p>The Commission published a report on 15 January 2020.</p>
                    <p>A workshop was held on 27 March 2021.</p>
                    <p>The roadmap was updated in February 2024.</p>
                    <p>Final review scheduled for 2028.</p>
                </body>
            </html>
            """
            soup = BeautifulSoup(html_multiple_dates, "html.parser")
            result = self.parser.followup_activity.extract_followup_latest_date(soup)

            # 2025 as year-only becomes 2025-12-31, but should be filtered as future
            # Latest valid date is February 2024 -> 2024-02-29
            assert result == "2024-02-29", f"Expected '2024-02-29', got '{result}'"

            # Test case 2: Single date with full month name
            html_single_date = """
            <html>
                <body>
                    <h2 id="Follow-up">Follow-up</h2>
                    <p>The report was published on 27 March 2021.</p>
                </body>
            </html>
            """
            soup = BeautifulSoup(html_single_date, "html.parser")
            result = self.parser.followup_activity.extract_followup_latest_date(soup)
            assert result == "2021-03-27", f"Expected '2021-03-27', got '{result}'"

            # Test case 3: Abbreviated month name
            html_abbreviated = """
            <html>
                <body>
                    <h2 id="Follow-up">Follow-up</h2>
                    <p>Updated on 15 Apr 2023.</p>
                </body>
            </html>
            """
            soup = BeautifulSoup(html_abbreviated, "html.parser")
            result = self.parser.followup_activity.extract_followup_latest_date(soup)
            assert result == "2023-04-15", f"Expected '2023-04-15', got '{result}'"

            # Test case 4: Slash-separated date format
            html_slash_format = """
            <html>
                <body>
                    <h2 id="Follow-up">Follow-up</h2>
                    <p>Published 27/03/2021</p>
                </body>
            </html>
            """
            soup = BeautifulSoup(html_slash_format, "html.parser")
            result = self.parser.followup_activity.extract_followup_latest_date(soup)
            assert result == "2021-03-27", f"Expected '2021-03-27', got '{result}'"

            # Test case 5: ISO date format
            html_iso_format = """
            <html>
                <body>
                    <h2 id="Follow-up">Follow-up</h2>
                    <p>Effective from 2021-03-27</p>
                </body>
            </html>
            """
            soup = BeautifulSoup(html_iso_format, "html.parser")
            result = self.parser.followup_activity.extract_followup_latest_date(soup)
            assert result == "2021-03-27", f"Expected '2021-03-27', got '{result}'"

            # Test case 6: Month and year only
            html_month_year = """
            <html>
                <body>
                    <h2 id="Follow-up">Follow-up</h2>
                    <p>Expected by February 2024</p>
                </body>
            </html>
            """
            soup = BeautifulSoup(html_month_year, "html.parser")
            result = self.parser.followup_activity.extract_followup_latest_date(soup)
            assert result == "2024-02-29", f"Expected '2024-02-29', got '{result}'"

            # Test case 7: No Follow-up section
            html_no_section = """
            <html>
                <body>
                    <h2>Other Section</h2>
                    <p>Some content with a date 27 March 2021</p>
                </body>
            </html>
            """
            soup = BeautifulSoup(html_no_section, "html.parser")
            result = self.parser.followup_activity.extract_followup_latest_date(soup)
            assert result is None, f"Expected None, got '{result}'"

            # Test case 8: Follow-up section with no dates
            html_no_dates = """
            <html>
                <body>
                    <h2 id="Follow-up">Follow-up</h2>
                    <p>The Commission is monitoring the situation.</p>
                </body>
            </html>
            """
            soup = BeautifulSoup(html_no_dates, "html.parser")
            result = self.parser.followup_activity.extract_followup_latest_date(soup)
            assert result is None, f"Expected None, got '{result}'"

            # Test case 9: Future date filtering - should exclude dates after mocked today (2025-11-06)
            html_future_dates = """
            <html>
                <body>
                    <h2 id="Follow-up">Follow-up</h2>
                    <p>Past update on 15 January 2020.</p>
                    <p>Future deadline in 2027.</p>
                </body>
            </html>
            """
            soup = BeautifulSoup(html_future_dates, "html.parser")
            result = self.parser.followup_activity.extract_followup_latest_date(soup)
            # Should return the past date, not the future one
            assert result == "2020-01-15", f"Expected '2020-01-15', got '{result}'"

            # Test case 10: h4 Follow-up subsection format
            html_h4_format = """
            <html>
                <body>
                    <h2>Answer of the European Commission and follow-up</h2>
                    <p>Some answer content.</p>
                    <h4>Follow-up</h4>
                    <p>The roadmap was published on 10 June 2022.</p>
                </body>
            </html>
            """
            soup = BeautifulSoup(html_h4_format, "html.parser")
            result = self.parser.followup_activity.extract_followup_latest_date(soup)
            assert result == "2022-06-10", f"Expected '2022-06-10', got '{result}'"

            # Test case 11: Mixed date formats - latest should win
            html_mixed_formats = """
            <html>
                <body>
                    <h2 id="Follow-up">Follow-up</h2>
                    <p>Initial report 15/01/2020</p>
                    <p>Update on 27 March 2021</p>
                    <p>Final version March 2023</p>
                    <p>Published 2022-06-10</p>
                </body>
            </html>
            """
            soup = BeautifulSoup(html_mixed_formats, "html.parser")
            result = self.parser.followup_activity.extract_followup_latest_date(soup)
            assert result == "2023-03-31", f"Expected '2023-03-31', got '{result}'"

            # Test case 12: Dates in nested elements (lists, paragraphs)
            html_nested = """
            <html>
                <body>
                    <h2 id="Follow-up">Follow-up</h2>
                    <ul>
                        <li>Workshop held on 5 May 2021</li>
                        <li>Report published <strong>10 December 2022</strong></li>
                    </ul>
                    <p>Additional consultation in <em>January 2023</em></p>
                </body>
            </html>
            """
            soup = BeautifulSoup(html_nested, "html.parser")
            result = self.parser.followup_activity.extract_followup_latest_date(soup)
            assert result == "2023-01-31", f"Expected '2023-01-31', got '{result}'"

            # Test case 13: All future dates - should return None
            html_all_future = """
            <html>
                <body>
                    <h2 id="Follow-up">Follow-up</h2>
                    <p>Scheduled for 2027</p>
                    <p>Expected by 2028</p>
                </body>
            </html>
            """
            soup = BeautifulSoup(html_all_future, "html.parser")
            result = self.parser.followup_activity.extract_followup_latest_date(soup)
            assert result is None, f"Expected None for all future dates, got '{result}'"

            # Test case 14: Date on the boundary (exact mock today)
            html_today_date = """
            <html>
                <body>
                    <h2 id="Follow-up">Follow-up</h2>
                    <p>Updated on 6 November 2025.</p>
                </body>
            </html>
            """
            soup = BeautifulSoup(html_today_date, "html.parser")
            result = self.parser.followup_activity.extract_followup_latest_date(soup)
            # Today's date should be included (<=)
            assert result == "2025-11-06", f"Expected '2025-11-06', got '{result}'"

            # Test case 15: Alternative H2 ID - "Updates-on-the-Commissions-proposals"
            html_alt_h2_id = """
            <html>
                <body>
                    <h2 id="Updates-on-the-Commissions-proposals">Updates on the Commission's proposals</h2>
                    <p>The Commission published a report on 15 January 2020.</p>
                    <p>A workshop was held on 27 March 2021.</p>
                    <p>The roadmap was updated in February 2024.</p>
                </body>
            </html>
            """
            soup = BeautifulSoup(html_alt_h2_id, "html.parser")
            result = self.parser.followup_activity.extract_followup_latest_date(soup)
            assert result == "2024-02-29", f"Expected '2024-02-29', got '{result}'"

    def test_followup_most_future_date(self):
        """Test extraction of most future (latest) date from follow-up section.

        Tests multiple date formats and ensures the absolute latest date is returned
        regardless of whether it's in the past or future.
        """

        # Test case 1: Multiple dates with various formats - should return absolute latest
        html_multiple_dates = """
        <html>
            <body>
                <h2 id="Follow-up">Follow-up</h2>
                <p>The Commission published a report on 15 January 2020.</p>
                <p>A workshop was held on 27 March 2021.</p>
                <p>The roadmap was updated in February 2024.</p>
                <p>Final review scheduled for 2027.</p>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_multiple_dates, "html.parser")
        result = self.parser.followup_activity.extract_followup_most_future_date(soup)
        # Should return the latest date regardless of future/past
        assert result == "2027-12-31", f"Expected '2027-12-31', got '{result}'"

        # Test case 2: Single date with full month name
        html_single_date = """
        <html>
            <body>
                <h2 id="Follow-up">Follow-up</h2>
                <p>The report was published on 27 March 2021.</p>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_single_date, "html.parser")
        result = self.parser.followup_activity.extract_followup_most_future_date(soup)
        assert result == "2021-03-27", f"Expected '2021-03-27', got '{result}'"

        # Test case 3: Abbreviated month name
        html_abbreviated = """
        <html>
            <body>
                <h2 id="Follow-up">Follow-up</h2>
                <p>Updated on 15 Apr 2023.</p>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_abbreviated, "html.parser")
        result = self.parser.followup_activity.extract_followup_most_future_date(soup)
        assert result == "2023-04-15", f"Expected '2023-04-15', got '{result}'"

        # Test case 4: Slash-separated date format
        html_slash_format = """
        <html>
            <body>
                <h2 id="Follow-up">Follow-up</h2>
                <p>Published 27/03/2021</p>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_slash_format, "html.parser")
        result = self.parser.followup_activity.extract_followup_most_future_date(soup)
        assert result == "2021-03-27", f"Expected '2021-03-27', got '{result}'"

        # Test case 5: ISO date format
        html_iso_format = """
        <html>
            <body>
                <h2 id="Follow-up">Follow-up</h2>
                <p>Effective from 2021-03-27</p>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_iso_format, "html.parser")
        result = self.parser.followup_activity.extract_followup_most_future_date(soup)
        assert result == "2021-03-27", f"Expected '2021-03-27', got '{result}'"

        # Test case 6: Month and year only
        html_month_year = """
        <html>
            <body>
                <h2 id="Follow-up">Follow-up</h2>
                <p>Expected by February 2024</p>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_month_year, "html.parser")
        result = self.parser.followup_activity.extract_followup_most_future_date(soup)
        assert result == "2024-02-29", f"Expected '2024-02-29', got '{result}'"

        # Test case 7: No Follow-up section
        html_no_section = """
        <html>
            <body>
                <h2>Other Section</h2>
                <p>Some content with a date 27 March 2021</p>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_no_section, "html.parser")
        result = self.parser.followup_activity.extract_followup_most_future_date(soup)
        assert result is None, f"Expected None, got '{result}'"

        # Test case 8: Follow-up section with no dates
        html_no_dates = """
        <html>
            <body>
                <h2 id="Follow-up">Follow-up</h2>
                <p>The Commission is monitoring the situation.</p>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_no_dates, "html.parser")
        result = self.parser.followup_activity.extract_followup_most_future_date(soup)
        assert result is None, f"Expected None, got '{result}'"

        # Test case 9: Future dates - should return the most future one
        html_future_dates = """
        <html>
            <body>
                <h2 id="Follow-up">Follow-up</h2>
                <p>Past update on 15 January 2020.</p>
                <p>Near future deadline in 2027.</p>
                <p>Far future target in 2030.</p>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_future_dates, "html.parser")
        result = self.parser.followup_activity.extract_followup_most_future_date(soup)
        # Should return the latest date (2030)
        assert result == "2030-12-31", f"Expected '2030-12-31', got '{result}'"

        # Test case 10: h4 Follow-up subsection format
        html_h4_format = """
        <html>
            <body>
                <h2>Answer of the European Commission and follow-up</h2>
                <p>Some answer content.</p>
                <h4>Follow-up</h4>
                <p>The roadmap was published on 10 June 2022.</p>
                <p>Next review scheduled for December 2028.</p>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_h4_format, "html.parser")
        result = self.parser.followup_activity.extract_followup_most_future_date(soup)
        assert result == "2028-12-31", f"Expected '2028-12-31', got '{result}'"

        # Test case 11: Mixed date formats - latest should win
        html_mixed_formats = """
        <html>
            <body>
                <h2 id="Follow-up">Follow-up</h2>
                <p>Initial report 15/01/2020</p>
                <p>Update on 27 March 2021</p>
                <p>Final version March 2023</p>
                <p>Published 2022-06-10</p>
                <p>Future deadline 2029</p>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_mixed_formats, "html.parser")
        result = self.parser.followup_activity.extract_followup_most_future_date(soup)
        assert result == "2029-12-31", f"Expected '2029-12-31', got '{result}'"

        # Test case 12: Dates in nested elements (lists, paragraphs)
        html_nested = """
        <html>
            <body>
                <h2 id="Follow-up">Follow-up</h2>
                <ul>
                    <li>Workshop held on 5 May 2021</li>
                    <li>Report published <strong>10 December 2022</strong></li>
                    <li>Target year <em>2026</em></li>
                </ul>
                <p>Additional consultation in <em>January 2023</em></p>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_nested, "html.parser")
        result = self.parser.followup_activity.extract_followup_most_future_date(soup)
        assert result == "2026-12-31", f"Expected '2026-12-31', got '{result}'"

        # Test case 13: Deadline-style dates
        html_deadline_dates = """
        <html>
            <body>
                <h2 id="Follow-up">Follow-up</h2>
                <p>Initial deadline: end of 2024</p>
                <p>Extended to early 2026</p>
                <p>Final target: May 2028</p>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_deadline_dates, "html.parser")
        result = self.parser.followup_activity.extract_followup_most_future_date(soup)
        assert result == "2028-05-31", f"Expected '2028-05-31', got '{result}'"

        # Test case 14: Mix of past and far future dates
        html_mixed_timeline = """
        <html>
            <body>
                <h2 id="Follow-up">Follow-up</h2>
                <p>Proposal submitted 1 January 2019</p>
                <p>First review 15 June 2020</p>
                <p>Implementation deadline: end 2035</p>
                <p>Interim report March 2025</p>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_mixed_timeline, "html.parser")
        result = self.parser.followup_activity.extract_followup_most_future_date(soup)
        assert result == "2035-12-31", f"Expected '2035-12-31', got '{result}'"

        # Test case 15: Only past dates
        html_only_past = """
        <html>
            <body>
                <h2 id="Follow-up">Follow-up</h2>
                <p>Report published 10 January 2020</p>
                <p>Workshop held 15 March 2021</p>
                <p>Final update December 2022</p>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_only_past, "html.parser")
        result = self.parser.followup_activity.extract_followup_most_future_date(soup)
        # Should still return the latest past date
        assert result == "2022-12-31", f"Expected '2022-12-31', got '{result}'"

        # Test case 16: Alternative H2 ID - "Updates-on-the-Commissions-proposals"
        html_alt_h2_id = """
        <html>
            <body>
                <h2 id="Updates-on-the-Commissions-proposals">Updates on the Commission's proposals</h2>
                <p>The Commission published a report on 15 January 2020.</p>
                <p>A workshop was held on 27 March 2021.</p>
                <p>Final review scheduled for 2027.</p>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_alt_h2_id, "html.parser")
        result = self.parser.followup_activity.extract_followup_most_future_date(soup)
        assert result == "2027-12-31", f"Expected '2027-12-31', got '{result}'"

        # Test case 17: Alternative H2 ID with single date
        html_alt_h2_single = """
        <html>
            <body>
                <h2 id="Updates-on-the-Commissions-proposals">Updates on the Commission's proposals</h2>
                <p>Report published on 10 June 2022.</p>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_alt_h2_single, "html.parser")
        result = self.parser.followup_activity.extract_followup_most_future_date(soup)
        assert result == "2022-06-10", f"Expected '2022-06-10', got '{result}'"
