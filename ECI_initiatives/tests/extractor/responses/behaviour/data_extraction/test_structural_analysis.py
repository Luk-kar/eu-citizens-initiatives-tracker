"""
Behavioural tests for structural analysis of ECI response pages.

This module contains tests for extracting structured data based on the
HTML and text content of European Citizens' Initiative response pages.
It verifies the correct identification and extraction of:

- Referenced EU legislation by formal identifiers (CELEX, Official Journal).
- Referenced EU legislation by their common names (e.g., "Water Framework Directive").
- Referenced articles of legislation.
- Calculation of follow-up duration (placeholder).
"""

# Standard library
import json

# Third party
from bs4 import BeautifulSoup
import pytest

# Local
from ECI_initiatives.extractor.responses.parser.main_parser import ECIResponseHTMLParser
from ECI_initiatives.extractor.responses.responses_logger import (
    ResponsesExtractorLogger,
)


class TestStructuralAnalysis:
    """Tests for structural analysis fields."""

    @classmethod
    def setup_class(cls):
        """Setup parser instance."""
        logger = ResponsesExtractorLogger().setup()
        cls.parser = ECIResponseHTMLParser(logger=logger)

    def test_referenced_legislation_by_id(self):
        """Test extraction of related EU legislation references."""

        # TEST 1: CELEX links with standard format
        html1 = """
        <a href="https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:32024R2522">
            Tariff codes for sharks
        </a>
        """
        soup1 = BeautifulSoup(html1, "html.parser")
        result1 = self.parser.structural_analysis.extract_referenced_legislation_by_id(
            soup1
        )
        result1_dict = json.loads(result1)
        assert "CELEX" in result1_dict
        assert result1_dict["CELEX"] == ["32024R2522"]

        # TEST 2: CELEX links with URL encoding (%3A instead of :)
        html2 = """
        <a href="https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A52018PC0179&qid=1616683628859">
            A proposal for a Regulation
        </a>
        """
        soup2 = BeautifulSoup(html2, "html.parser")
        result2 = self.parser.structural_analysis.extract_referenced_legislation_by_id(
            soup2
        )
        result2_dict = json.loads(result2)
        assert "CELEX" in result2_dict
        assert result2_dict["CELEX"] == ["52018PC0179"]

        # TEST 3: Directive references with standard format in text
        html3 = """
        <div>Directive 2010/63/EU on the protection of animals used for scientific purposes</div>
        """
        soup3 = BeautifulSoup(html3, "html.parser")
        result3 = self.parser.structural_analysis.extract_referenced_legislation_by_id(
            soup3
        )
        result3_dict = json.loads(result3)
        assert "Directive" in result3_dict
        assert result3_dict["Directive"] == ["2010/63/EU"]

        # TEST 4: Official Journal L series (legislation)
        html4 = """
        <a href="http://eur-lex.europa.eu/legal-content/EN/TXT/?uri=uriserv:OJ.L_.2015.260.01.0006.01.ENG">
            Drinking Water Directive
        </a>
        """
        soup4 = BeautifulSoup(html4, "html.parser")
        result4 = self.parser.structural_analysis.extract_referenced_legislation_by_id(
            soup4
        )
        result4_dict = json.loads(result4)
        assert "official_journal" in result4_dict
        assert "legislation" in result4_dict["official_journal"]
        assert result4_dict["official_journal"]["legislation"] == ["2015, 260"]

        # TEST 5: Official Journal C series (information and notices)
        html5 = """
        <a href="http://eur-lex.europa.eu/legal-content/EN/TXT/?uri=uriserv:OJ.C_.2020.145.02.0003.02.ENG">
            Commission Notice
        </a>
        """
        soup5 = BeautifulSoup(html5, "html.parser")
        result5 = self.parser.structural_analysis.extract_referenced_legislation_by_id(
            soup5
        )
        result5_dict = json.loads(result5)
        assert "official_journal" in result5_dict
        assert "information_and_notices" in result5_dict["official_journal"]
        assert result5_dict["official_journal"]["information_and_notices"] == [
            "2020, 145"
        ]

        # TEST 6: Article references in text
        html6 = """
        <div>Pursuant to Article 19(2) and Article 15 of the Regulation</div>
        """
        soup6 = BeautifulSoup(html6, "html.parser")
        result6 = self.parser.structural_analysis.extract_referenced_legislation_by_id(
            soup6
        )
        result6_dict = json.loads(result6)
        assert "Article" in result6_dict
        assert result6_dict["Article"] == ["19(2)", "15"]

        # TEST 7: Multiple CELEX references (deduplication)
        html7 = """
        <a href="https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R2522">First</a>
        <a href="https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R2522">Duplicate</a>
        <a href="https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32010L0063">Second</a>
        """
        soup7 = BeautifulSoup(html7, "html.parser")
        result7 = self.parser.structural_analysis.extract_referenced_legislation_by_id(
            soup7
        )
        result7_dict = json.loads(result7)
        assert "CELEX" in result7_dict
        assert len(result7_dict["CELEX"]) == 2
        assert result7_dict["CELEX"] == ["32024R2522", "32010L0063"]

        # TEST 8: Mixed content (directives, regulations, CELEX, articles, OJ references)
        html8 = """
        <div>
            <p>Directive 2010/13/EU on audiovisual media services</p>
            <p>Regulation (EU) 1234/2020 on transparency</p>
            <a href="https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32020R0852">
                Taxonomy Regulation
            </a>
            <a href="http://eur-lex.europa.eu/legal-content/EN/TXT/?uri=uriserv:OJ.L_.2020.45.01.0001.01.ENG">
                OJ L 2020</a>
            <p>Pursuant to Article 15</p>
        </div>
        """
        soup8 = BeautifulSoup(html8, "html.parser")
        result8 = self.parser.structural_analysis.extract_referenced_legislation_by_id(
            soup8
        )
        result8_dict = json.loads(result8)

        assert "Directive" in result8_dict
        assert result8_dict["Directive"] == ["2010/13/EU"]

        assert "Regulation" in result8_dict
        assert result8_dict["Regulation"] == ["1234/2020"]

        assert "CELEX" in result8_dict
        assert "32020R0852" in result8_dict["CELEX"]

        assert "official_journal" in result8_dict
        assert "legislation" in result8_dict["official_journal"]
        assert result8_dict["official_journal"]["legislation"] == ["2020, 45"]

        assert "Article" in result8_dict
        assert result8_dict["Article"] == ["15"]

        # TEST 9: No matches - should return None
        html9 = """
        <div>This text contains no legislative references whatsoever.</div>
        """
        soup9 = BeautifulSoup(html9, "html.parser")
        result9 = self.parser.structural_analysis.extract_referenced_legislation_by_id(
            soup9
        )
        assert result9 is None

        # TEST 10: Empty soup - should return None
        soup10 = BeautifulSoup("", "html.parser")
        result10 = self.parser.structural_analysis.extract_referenced_legislation_by_id(
            soup10
        )
        assert result10 is None

        # TEST 11: URL-encoded Official Journal reference
        html11 = """
        <a href="http://eur-lex.europa.eu/legal-content/EN/TXT/?uri=uriserv%3AOJ.L_.2015.260.01.0006.01.ENG">
            OJ Link encoded
        </a>
        """
        soup11 = BeautifulSoup(html11, "html.parser")
        result11 = self.parser.structural_analysis.extract_referenced_legislation_by_id(
            soup11
        )
        result11_dict = json.loads(result11)
        assert "official_journal" in result11_dict
        assert "legislation" in result11_dict["official_journal"]

        # TEST 12: Only OJ L series (no C series)
        html12 = """
        <a href="http://eur-lex.europa.eu/legal-content/EN/TXT/?uri=uriserv:OJ.L_.2015.260.01.0006.01.ENG">L</a>
        <a href="http://eur-lex.europa.eu/legal-content/EN/TXT/?uri=uriserv:OJ.L_.2020.45.01.0001.01.ENG">L2</a>
        """
        soup12 = BeautifulSoup(html12, "html.parser")
        result12 = self.parser.structural_analysis.extract_referenced_legislation_by_id(
            soup12
        )
        result12_dict = json.loads(result12)
        assert "official_journal" in result12_dict
        assert "legislation" in result12_dict["official_journal"]
        assert "information_and_notices" not in result12_dict["official_journal"]

        # TEST 13: Only OJ C series (no L series)
        html13 = """
        <a href="http://eur-lex.europa.eu/legal-content/EN/TXT/?uri=uriserv:OJ.C_.2020.145.02.0003.02.ENG">C</a>
        """
        soup13 = BeautifulSoup(html13, "html.parser")
        result13 = self.parser.structural_analysis.extract_referenced_legislation_by_id(
            soup13
        )
        result13_dict = json.loads(result13)
        assert "official_journal" in result13_dict
        assert "legislation" not in result13_dict["official_journal"]
        assert "information_and_notices" in result13_dict["official_journal"]

        # TEST 14: Directive without /EU suffix
        html14 = """
        <div>Directive 2010/63 applies here</div>
        """
        soup14 = BeautifulSoup(html14, "html.parser")
        result14 = self.parser.structural_analysis.extract_referenced_legislation_by_id(
            soup14
        )
        result14_dict = json.loads(result14)
        assert "Directive" in result14_dict
        assert result14_dict["Directive"] == ["2010/63"]

        # TEST 15: Regulation with standard format
        html15 = """
        <div>Regulation (EU) No. 1234/2020 on transparency requirements</div>
        """
        soup15 = BeautifulSoup(html15, "html.parser")
        result15 = self.parser.structural_analysis.extract_referenced_legislation_by_id(
            soup15
        )
        result15_dict = json.loads(result15)
        assert "Regulation" in result15_dict
        assert result15_dict["Regulation"] == ["1234/2020"]

    def test_referenced_legislation_by_name(self):
        """
        Test extraction of referenced EU legislation by name from text.

        This test verifies that the parser can correctly identify and extract
        references to EU legislation (Directives, Regulations, Decisions)
        mentioned by their title or name within the text content of a response page.

        It covers various formats, including:
        - Standard "Directive [year]/[number]/[group]" format.
        - "Regulation (EU) [year]/[number]" format.
        - Case-insensitive matching.
        - Multiple references within the same text.
        - Handling of surrounding text and HTML tags.
        """

        # 1. Basic extraction - Directive
        html1 = (
            "<div>This proposal is in line with the Water Framework Directive.</div>"
        )
        soup1 = BeautifulSoup(html1, "html.parser")
        result1 = (
            self.parser.structural_analysis.extract_referenced_legislation_by_name(
                soup1
            )
        )
        assert result1 is not None
        res1 = json.loads(result1)
        assert res1["directives"] == ["Water Framework Directive"]

        # 2. Basic extraction - Regulation and Charter
        html2 = "<div>This complies with the General Data Protection Regulation and the Charter of Fundamental Rights.</div>"
        soup2 = BeautifulSoup(html2, "html.parser")
        result2 = (
            self.parser.structural_analysis.extract_referenced_legislation_by_name(
                soup2
            )
        )
        assert result2 is not None
        res2 = json.loads(result2)
        assert "regulations" in res2 and res2["regulations"] == [
            "General Data Protection Regulation"
        ]
        assert "charters" in res2 and res2["charters"] == [
            "Charter of Fundamental Rights"
        ]

        # 3. Orchids Regulation and multiple directives (conjunction splitting)
        html3 = (
            "<p>The Habitats Directive and Birds Directive have been considered.</p>"
            "<p>See also Orchids Regulation.</p>"
        )
        soup3 = BeautifulSoup(html3, "html.parser")
        result3 = (
            self.parser.structural_analysis.extract_referenced_legislation_by_name(
                soup3
            )
        )
        res3 = json.loads(result3)
        assert sorted(res3["directives"]) == ["Birds Directive", "Habitats Directive"]
        assert res3["regulations"] == ["Orchids Regulation"]

        # 4. Treaties - TFEU and named
        html4 = (
            "<div>Actions are subject to TEU, TFEU, the Treaty on the Functioning of the European Union, "
            "and Lisbon Treaty. Refer also to Charter of Fundamental Rights.</div>"
        )
        soup4 = BeautifulSoup(html4, "html.parser")
        result4 = (
            self.parser.structural_analysis.extract_referenced_legislation_by_name(
                soup4
            )
        )
        res4 = json.loads(result4)
        assert sorted(res4["treaties"]) == [
            "Lisbon Treaty",
            "TEU",
            "TFEU",
            "Treaty on the Functioning of the European Union",
        ]
        assert res4["charters"] == ["Charter of Fundamental Rights"]

        # 5. Remove empty/standalone/generic - only real Directive kept
        html5 = "<div>Proposal for a Directive, the Directive, and the Animal Welfare Directive.</div>"
        soup5 = BeautifulSoup(html5, "html.parser")
        result5 = (
            self.parser.structural_analysis.extract_referenced_legislation_by_name(
                soup5
            )
        )
        res5 = json.loads(result5)
        assert res5["directives"] == ["Animal Welfare Directive"]

        # 6. Leading articles removed
        html6 = "<div>The Water Framework Directive, a Floods Directive and an Allergy Regulation.</div>"
        soup6 = BeautifulSoup(html6, "html.parser")
        result6 = (
            self.parser.structural_analysis.extract_referenced_legislation_by_name(
                soup6
            )
        )
        res6 = json.loads(result6)
        assert sorted(res6["directives"]) == [
            "Floods Directive",
            "Water Framework Directive",
        ]
        assert res6["regulations"] == ["Allergy Regulation"]

        # 7. Deduplication and non-inclusion of generic
        html7 = "<div>General Food Law Regulation and General Food Law Regulation and Proposal for Regulation</div>"
        soup7 = BeautifulSoup(html7, "html.parser")
        result7 = (
            self.parser.structural_analysis.extract_referenced_legislation_by_name(
                soup7
            )
        )
        res7 = json.loads(result7)
        assert res7["regulations"] == ["General Food Law Regulation"]

        # 8. Compound with newlines and conjunctions
        html8 = (
            "<div>Water Framework Directive\nBirds Directive and Floods Directive</div>"
        )
        soup8 = BeautifulSoup(html8, "html.parser")
        result8 = (
            self.parser.structural_analysis.extract_referenced_legislation_by_name(
                soup8
            )
        )
        res8 = json.loads(result8)
        assert sorted(res8["directives"]) == [
            "Birds Directive",
            "Floods Directive",
            "Water Framework Directive",
        ]

        # 9. Charter alternative capture (named)
        html9 = "<div>European Social Charter and Youth Charter were mentioned.</div>"
        soup9 = BeautifulSoup(html9, "html.parser")
        result9 = (
            self.parser.structural_analysis.extract_referenced_legislation_by_name(
                soup9
            )
        )
        res9 = json.loads(result9)
        assert sorted(res9["charters"]) == ["European Social Charter", "Youth Charter"]

        # 10. No match returns None
        html10 = "<div>This sentence contains no legislation references at all.</div>"
        soup10 = BeautifulSoup(html10, "html.parser")
        result10 = (
            self.parser.structural_analysis.extract_referenced_legislation_by_name(
                soup10
            )
        )
        assert result10 is None

        # 11. Empty soup returns None
        soup11 = BeautifulSoup("", "html.parser")
        result11 = (
            self.parser.structural_analysis.extract_referenced_legislation_by_name(
                soup11
            )
        )
        assert result11 is None

        # 12. Tags inside strong are unwrapped and counted
        html12 = "<div><strong>Biodiversity Regulation</strong> is critical. The Water Framework Directive applies.</div>"
        soup12 = BeautifulSoup(html12, "html.parser")
        result12 = (
            self.parser.structural_analysis.extract_referenced_legislation_by_name(
                soup12
            )
        )
        res12 = json.loads(result12)
        assert res12["regulations"] == ["Biodiversity Regulation"]
        assert res12["directives"] == ["Water Framework Directive"]

        # 13. Charter and Treaty in same sentence
        html13 = (
            "<div>By the Charter of Fundamental Rights and the Maastricht Treaty.</div>"
        )
        soup13 = BeautifulSoup(html13, "html.parser")
        result13 = (
            self.parser.structural_analysis.extract_referenced_legislation_by_name(
                soup13
            )
        )
        res13 = json.loads(result13)
        assert res13["charters"] == ["Charter of Fundamental Rights"]
        assert res13["treaties"] == ["Maastricht Treaty"]

        # 14. Case-insensitivity, weird spacing/hyphens
        html14 = "<div>The habitat   Directive and the general-data-protection Regulation apply.</div>"
        soup14 = BeautifulSoup(html14, "html.parser")
        result14 = (
            self.parser.structural_analysis.extract_referenced_legislation_by_name(
                soup14
            )
        )

        assert result14 is None, "Generic legislation terms should be filtered out"

    def test_followup_actions_with_dates(self):
        """
        Test calculation of follow-up duration and timeline extraction.

        This test verifies that the parser can correctly extract follow-up actions
        with associated dates from the Follow-up section of ECI response pages.

        It covers:
        - Extraction of actions with single dates
        - Extraction of actions with multiple dates
        - Extraction of actions without dates
        - Different date formats (DD Month YYYY, Month YYYY, YYYY)
        - Deadline expressions (early YYYY, end of YYYY, end YYYY)
        - Date normalization to ISO 8601 format
        - Handling of list items and paragraphs
        - Filtering of generic intro text and subsection headers
        - Proper JSON structure with "dates" and "action" fields
        """

        # TEST 1: Single action with full date (DD Month YYYY)
        html1 = """
        <h2>Follow-up</h2>
        <p>On 9 February 2024, Commissioner Stella Kyriakides met with the organisers 
        to discuss the Commission's reply to the initiative.</p>
        """
        soup1 = BeautifulSoup(html1, "html.parser")
        result1 = self.parser.structural_analysis.extract_followup_actions_with_dates(
            soup1
        )
        res1 = json.loads(result1)
        assert len(res1) == 1
        assert res1[0]["dates"] == ["2024-02-09"]
        assert "Commissioner Stella Kyriakides" in res1[0]["action"]

        # TEST 2: Multiple actions with different date formats
        html2 = """
        <h2>Follow-up</h2>
        <ul>
            <li>A proposal was adopted by the Commission on 01 February 2018.</li>
            <li>The Directive entered into force in February 2020.</li>
            <li>Member States have until 2023 to transpose it into national legislation.</li>
        </ul>
        """
        soup2 = BeautifulSoup(html2, "html.parser")
        result2 = self.parser.structural_analysis.extract_followup_actions_with_dates(
            soup2
        )
        res2 = json.loads(result2)
        assert len(res2) == 3
        # First action: full date
        assert res2[0]["dates"] == ["2018-02-01"]
        assert "proposal was adopted" in res2[0]["action"]
        # Second action: month-year (converted to last day of month)
        assert res2[1]["dates"] == ["2020-02-29"]  # Leap year - last day
        assert "entered into force" in res2[1]["action"]
        # Third action: year only
        assert res2[2]["dates"] == ["2023-01-01"]
        assert "transpose it" in res2[2]["action"]

        # TEST 3: Action without dates
        html3 = """
        <h2>Follow-up</h2>
        <p>The Commission is working towards better enforcement of the existing rules.</p>
        """
        soup3 = BeautifulSoup(html3, "html.parser")
        result3 = self.parser.structural_analysis.extract_followup_actions_with_dates(
            soup3
        )
        res3 = json.loads(result3)
        assert len(res3) == 1
        assert res3[0]["dates"] == []
        assert "better enforcement" in res3[0]["action"]

        # TEST 4: Multiple dates in single action
        html4 = """
        <h2>Follow-up</h2>
        <p>The Directive entered into force on 12 January 2021. Member States had until 
        12 January 2023 to transpose it. The new rules apply from 26 June 2023.</p>
        """
        soup4 = BeautifulSoup(html4, "html.parser")
        result4 = self.parser.structural_analysis.extract_followup_actions_with_dates(
            soup4
        )
        res4 = json.loads(result4)
        assert len(res4) == 1
        assert len(res4[0]["dates"]) == 3
        assert "2021-01-12" in res4[0]["dates"]
        assert "2023-01-12" in res4[0]["dates"]
        assert "2023-06-26" in res4[0]["dates"]

        # TEST 5: Generic intro text is filtered out
        html5 = """
        <h2>Follow-up</h2>
        <p>This section provides regularly updated information on the follow-up actions.</p>
        <p>A proposal for a Regulation was adopted on 11 April 2018.</p>
        """
        soup5 = BeautifulSoup(html5, "html.parser")
        result5 = self.parser.structural_analysis.extract_followup_actions_with_dates(
            soup5
        )
        res5 = json.loads(result5)
        # Generic intro should be filtered out
        assert len(res5) == 1
        assert "proposal for a Regulation" in res5[0]["action"]
        assert res5[0]["dates"] == ["2018-04-11"]

        # TEST 6: Subsection headers are filtered out
        html6 = """
        <h2>Follow-up</h2>
        <p>Legislative action:</p>
        <ul>
            <li>The Commission adopted a Communication on 03 June 2015 setting out actions.</li>
        </ul>
        """
        soup6 = BeautifulSoup(html6, "html.parser")
        result6 = self.parser.structural_analysis.extract_followup_actions_with_dates(
            soup6
        )
        res6 = json.loads(result6)
        # Should only have the list item, not the header
        assert len(res6) == 1
        assert "Communication on 03 June 2015" in res6[0]["action"]
        assert res6[0]["dates"] == ["2015-06-03"]

        # TEST 7: Mixed paragraphs and list items
        html7 = """
        <h2>Follow-up</h2>
        <p>The Commission started work on a roadmap in the second half of 2023.</p>
        <ul>
            <li>Finalisation of the work is planned by early 2026.</li>
            <li>See the information on related workshops organised since 2023.</li>
        </ul>
        """
        soup7 = BeautifulSoup(html7, "html.parser")
        result7 = self.parser.structural_analysis.extract_followup_actions_with_dates(
            soup7
        )
        res7 = json.loads(result7)
        assert len(res7) == 3
        # First paragraph
        assert "2023-01-01" in res7[0]["dates"]
        assert "roadmap" in res7[0]["action"]
        # First list item with "early 2026" deadline
        assert "2026-03-31" in res7[1]["dates"]  # early = end of Q1
        assert "Finalisation" in res7[1]["action"]
        # Second list item
        assert "2023-01-01" in res7[2]["dates"]
        assert "workshops" in res7[2]["action"]

        # TEST 8: Date deduplication (avoid extracting Month YYYY when DD Month YYYY exists)
        html8 = """
        <h2>Follow-up</h2>
        <p>The proposal was adopted on 01 February 2018.</p>
        """
        soup8 = BeautifulSoup(html8, "html.parser")
        result8 = self.parser.structural_analysis.extract_followup_actions_with_dates(
            soup8
        )
        res8 = json.loads(result8)
        assert len(res8) == 1
        # Should only extract full date, not also "February 2018"
        assert res8[0]["dates"] == ["2018-02-01"]

        # TEST 9: No Follow-up section raises ValueError
        html9 = """
        <h2>Answer of the European Commission</h2>
        <p>This is the Commission's response.</p>
        """
        soup9 = BeautifulSoup(html9, "html.parser")
        result9 = self.parser.structural_analysis.extract_followup_actions_with_dates(
            soup9
        )
        assert result9 is None

        # TEST 10: Follow-up section with no valid content raises ValueError
        html10 = """
        <h2>Follow-up</h2>
        <p>This section provides information on the follow-up.</p>
        <p>Legislative action:</p>
        """
        soup10 = BeautifulSoup(html10, "html.parser")
        with pytest.raises(ValueError, match="No valid follow-up actions found"):
            self.parser.structural_analysis.extract_followup_actions_with_dates(soup10)

        # TEST 11: Follow-up section stops at next h2
        html11 = """
        <h2>Follow-up</h2>
        <p>A proposal was adopted on 11 April 2018 in response to the initiative.</p>
        <h2>More information</h2>
        <p>This should not be included in follow-up actions.</p>
        """
        soup11 = BeautifulSoup(html11, "html.parser")
        result11 = self.parser.structural_analysis.extract_followup_actions_with_dates(
            soup11
        )
        res11 = json.loads(result11)
        assert len(res11) == 1
        assert "2018-04-11" in res11[0]["dates"]
        assert "More information" not in res11[0]["action"]

        # TEST 12: Alternative h4 Follow-up section
        html12 = """
        <h4>Follow-up</h4>
        <p>The Commission organised a conference in Brussels on 6-7 December 2016.</p>
        """
        soup12 = BeautifulSoup(html12, "html.parser")
        result12 = self.parser.structural_analysis.extract_followup_actions_with_dates(
            soup12
        )
        res12 = json.loads(result12)
        assert len(res12) == 1
        assert "2016-12-07" in res12[0]["dates"]  # Should extract the later date
        assert "conference" in res12[0]["action"]

        # TEST 13: Very short content is filtered out
        html13 = """
        <h2>Follow-up</h2>
        <p>Short text.</p>
        <p>This is a longer paragraph that meets the minimum length requirement of 30 characters.</p>
        """
        soup13 = BeautifulSoup(html13, "html.parser")
        result13 = self.parser.structural_analysis.extract_followup_actions_with_dates(
            soup13
        )
        res13 = json.loads(result13)
        # Should only include the longer paragraph
        assert len(res13) == 1
        assert "longer paragraph" in res13[0]["action"]

        # TEST 14: Complex real-world example with nested lists
        html14 = """
        <h2>Follow-up</h2>
        <p>This section provides regularly updated information on follow-up actions.</p>
        <p>Legislative action:</p>
        <ul>
            <li>As a first step, an amendment to the Drinking Water Directive came 
                into force on 28 October 2015.</li>
            <li>A proposal for revision was adopted on 01 February 2018. On 
                16 December 2020, Parliament adopted the revised Directive.</li>
        </ul>
        <p>Implementation and review:</p>
        <ul>
            <li>Implementation reports were published in 2015, 2019 and 2021.</li>
        </ul>
        """
        soup14 = BeautifulSoup(html14, "html.parser")
        result14 = self.parser.structural_analysis.extract_followup_actions_with_dates(
            soup14
        )
        res14 = json.loads(result14)
        # Should have 3 actions (2 from first ul, 1 from second ul)
        assert len(res14) == 3
        # First action
        assert "2015-10-28" in res14[0]["dates"]
        assert "Drinking Water Directive" in res14[0]["action"]
        # Second action
        assert "2018-02-01" in res14[1]["dates"]
        assert "2020-12-16" in res14[1]["dates"]
        # Third action
        assert "2015-01-01" in res14[2]["dates"]
        assert "2019-01-01" in res14[2]["dates"]
        assert "2021-01-01" in res14[2]["dates"]

        # TEST 15: Empty soup raises ValueError
        soup15 = BeautifulSoup("", "html.parser")
        result15 = self.parser.structural_analysis.extract_followup_actions_with_dates(
            soup15
        )
        assert result15 is None

        # TEST 16: Deadline expressions "end of YYYY"
        html16 = """
        <h2>Follow-up</h2>
        <p>The Commission will publish its report by the end of 2024.</p>
        """
        soup16 = BeautifulSoup(html16, "html.parser")
        result16 = self.parser.structural_analysis.extract_followup_actions_with_dates(
            soup16
        )
        res16 = json.loads(result16)
        assert len(res16) == 1
        assert "2024-12-31" in res16[0]["dates"]  # end of year = Dec 31
        assert "report" in res16[0]["action"]

        # TEST 17: Deadline expression "end YYYY" (without "of")
        html17 = """
        <h2>Follow-up</h2>
        <p>Member States must comply by end 2025.</p>
        """
        soup17 = BeautifulSoup(html17, "html.parser")
        result17 = self.parser.structural_analysis.extract_followup_actions_with_dates(
            soup17
        )
        res17 = json.loads(result17)
        assert len(res17) == 1
        assert "2025-12-31" in res17[0]["dates"]
        assert "comply" in res17[0]["action"]

        # TEST 18: Month names convert to last day of month
        html18 = """
        <h2>Follow-up</h2>
        <p>The deadline for submissions is May 2018.</p>
        """
        soup18 = BeautifulSoup(html18, "html.parser")
        result18 = self.parser.structural_analysis.extract_followup_actions_with_dates(
            soup18
        )
        res18 = json.loads(result18)
        assert len(res18) == 1
        assert "2018-05-31" in res18[0]["dates"]  # Last day of May
        assert "submissions" in res18[0]["action"]

        # TEST 19: - Both explicit date and deadline expression with same month
        html19 = """
        <h2>Follow-up</h2>
        <p>The consultation started on 28 February 2018 and closed by end of February 2018.</p>
        """
        soup19 = BeautifulSoup(html19, "html.parser")
        result19 = self.parser.structural_analysis.extract_followup_actions_with_dates(
            soup19
        )
        res19 = json.loads(result19)
        assert len(res19) == 1
        # Should extract both dates: specific date and end of month
        assert (
            "2018-02-29" not in res19[0]["dates"]
        )  # 2018 is not a leap year, so Feb 28
        assert "2018-02-28" in res19[0]["dates"]
