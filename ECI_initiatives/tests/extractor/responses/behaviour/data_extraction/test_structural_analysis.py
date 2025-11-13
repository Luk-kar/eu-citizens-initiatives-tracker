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

    def test_follow_up_duration_calculation(self):
        """Test calculation of follow-up duration in months."""
        # Placeholder - implement when date parsing is implemented
        pass
