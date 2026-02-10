"""
Behavioural tests for structural analysis of ECI response pages.

This module contains tests for extracting structured data based on the
HTML and text content of European Citizens' Initiative response pages.
It verifies the correct identification and extraction of:

- Referenced EU legislation by formal identifiers (CELEX, Official Journal).
- Referenced EU legislation by their common names (e.g., "Water Framework Directive").
- Referenced articles of legislation.
- follow-up with dates
"""

# Standard library
import json

# Third party
from bs4 import BeautifulSoup
import pytest

# Local
from ECI_initiatives.data_pipeline.extractor.responses.parser.main_parser import (
    ECIResponseHTMLParser,
)
from ECI_initiatives.data_pipeline.extractor.responses.responses_logger import (
    ResponsesExtractorLogger,
)


class TestLegislativeReferences:
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

        assert "CELEX" in result1
        assert result1["CELEX"] == ["32024R2522"]

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

        assert "CELEX" in result2
        assert result2["CELEX"] == ["52018PC0179"]

        # TEST 3: Directive references with standard format in text
        html3 = """
        <div>Directive 2010/63/EU on the protection of animals used for scientific purposes</div>
        """
        soup3 = BeautifulSoup(html3, "html.parser")
        result3 = self.parser.structural_analysis.extract_referenced_legislation_by_id(
            soup3
        )

        assert "Directive" in result3
        assert result3["Directive"] == ["2010/63/EU"]

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

        assert "official_journal" in result4
        assert "legislation" in result4["official_journal"]
        assert result4["official_journal"]["legislation"] == ["2015, 260"]

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

        assert "official_journal" in result5
        assert "information_and_notices" in result5["official_journal"]
        assert result5["official_journal"]["information_and_notices"] == ["2020, 145"]

        # TEST 6: Article references in text
        html6 = """
        <div>Pursuant to Article 19(2) and Article 15 of the Regulation</div>
        """
        soup6 = BeautifulSoup(html6, "html.parser")
        result6 = self.parser.structural_analysis.extract_referenced_legislation_by_id(
            soup6
        )

        assert "Article" in result6
        assert result6["Article"] == ["19(2)", "15"]

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

        assert "CELEX" in result7
        assert len(result7["CELEX"]) == 2
        assert result7["CELEX"] == ["32024R2522", "32010L0063"]

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

        assert "Directive" in result8
        assert result8["Directive"] == ["2010/13/EU"]

        assert "Regulation" in result8
        assert result8["Regulation"] == ["1234/2020"]

        assert "CELEX" in result8
        assert "32020R0852" in result8["CELEX"]

        assert "official_journal" in result8
        assert "legislation" in result8["official_journal"]
        assert result8["official_journal"]["legislation"] == ["2020, 45"]

        assert "Article" in result8
        assert result8["Article"] == ["15"]

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

        assert "official_journal" in result11
        assert "legislation" in result11["official_journal"]

        # TEST 12: Only OJ L series (no C series)
        html12 = """
        <a href="http://eur-lex.europa.eu/legal-content/EN/TXT/?uri=uriserv:OJ.L_.2015.260.01.0006.01.ENG">L</a>
        <a href="http://eur-lex.europa.eu/legal-content/EN/TXT/?uri=uriserv:OJ.L_.2020.45.01.0001.01.ENG">L2</a>
        """
        soup12 = BeautifulSoup(html12, "html.parser")
        result12 = self.parser.structural_analysis.extract_referenced_legislation_by_id(
            soup12
        )

        assert "official_journal" in result12
        assert "legislation" in result12["official_journal"]
        assert "information_and_notices" not in result12["official_journal"]

        # TEST 13: Only OJ C series (no L series)
        html13 = """
        <a href="http://eur-lex.europa.eu/legal-content/EN/TXT/?uri=uriserv:OJ.C_.2020.145.02.0003.02.ENG">C</a>
        """
        soup13 = BeautifulSoup(html13, "html.parser")
        result13 = self.parser.structural_analysis.extract_referenced_legislation_by_id(
            soup13
        )

        assert "official_journal" in result13
        assert "legislation" not in result13["official_journal"]
        assert "information_and_notices" in result13["official_journal"]

        # TEST 14: Directive without /EU suffix
        html14 = """
        <div>Directive 2010/63 applies here</div>
        """
        soup14 = BeautifulSoup(html14, "html.parser")
        result14 = self.parser.structural_analysis.extract_referenced_legislation_by_id(
            soup14
        )

        assert "Directive" in result14
        assert result14["Directive"] == ["2010/63"]

        # TEST 15: Regulation with standard format
        html15 = """
        <div>Regulation (EU) No. 1234/2020 on transparency requirements</div>
        """
        soup15 = BeautifulSoup(html15, "html.parser")
        result15 = self.parser.structural_analysis.extract_referenced_legislation_by_id(
            soup15
        )
        assert "Regulation" in result15
        assert result15["Regulation"] == ["1234/2020"]

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
        assert result1["directives"] == ["Water Framework Directive"]

        # 2. Basic extraction - Regulation and Charter
        html2 = "<div>This complies with the General Data Protection Regulation and the Charter of Fundamental Rights.</div>"
        soup2 = BeautifulSoup(html2, "html.parser")
        result2 = (
            self.parser.structural_analysis.extract_referenced_legislation_by_name(
                soup2
            )
        )

        assert result2 is not None
        assert "regulations" in result2 and result2["regulations"] == [
            "General Data Protection Regulation"
        ]
        assert "charters" in result2 and result2["charters"] == [
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

        assert sorted(result3["directives"]) == [
            "Birds Directive",
            "Habitats Directive",
        ]
        assert result3["regulations"] == ["Orchids Regulation"]

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
        assert sorted(result4["treaties"]) == [
            "Lisbon Treaty",
            "TEU",
            "TFEU",
            "Treaty on the Functioning of the European Union",
        ]

        assert result4["charters"] == ["Charter of Fundamental Rights"]

        # 5. Remove empty/standalone/generic - only real Directive kept
        html5 = "<div>Proposal for a Directive, the Directive, and the Animal Welfare Directive.</div>"
        soup5 = BeautifulSoup(html5, "html.parser")
        result5 = (
            self.parser.structural_analysis.extract_referenced_legislation_by_name(
                soup5
            )
        )

        assert result5["directives"] == ["Animal Welfare Directive"]

        # 6. Leading articles removed
        html6 = "<div>The Water Framework Directive, a Floods Directive and an Allergy Regulation.</div>"
        soup6 = BeautifulSoup(html6, "html.parser")
        result6 = (
            self.parser.structural_analysis.extract_referenced_legislation_by_name(
                soup6
            )
        )

        assert sorted(result6["directives"]) == [
            "Floods Directive",
            "Water Framework Directive",
        ]
        assert result6["regulations"] == ["Allergy Regulation"]

        # 7. Deduplication and non-inclusion of generic
        html7 = "<div>General Food Law Regulation and General Food Law Regulation and Proposal for Regulation</div>"
        soup7 = BeautifulSoup(html7, "html.parser")
        result7 = (
            self.parser.structural_analysis.extract_referenced_legislation_by_name(
                soup7
            )
        )

        assert result7["regulations"] == ["General Food Law Regulation"]

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

        assert sorted(result8["directives"]) == [
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

        assert sorted(result9["charters"]) == [
            "European Social Charter",
            "Youth Charter",
        ]

        # 10. No match returns None
        html10 = "<div>This sentence contains no legislation references at all.</div>"
        soup10 = BeautifulSoup(html10, "html.parser")
        result10 = (
            self.parser.structural_analysis.extract_referenced_legislation_by_name(
                soup10
            )
        )
        assert not result10  # Checks if falsy (None, {}, [], "", 0, False)

        # 11. Empty soup returns None
        soup11 = BeautifulSoup("", "html.parser")
        result11 = (
            self.parser.structural_analysis.extract_referenced_legislation_by_name(
                soup11
            )
        )
        assert not result11

        # 12. Tags inside strong are unwrapped and counted
        html12 = "<div><strong>Biodiversity Regulation</strong> is critical. The Water Framework Directive applies.</div>"
        soup12 = BeautifulSoup(html12, "html.parser")
        result12 = (
            self.parser.structural_analysis.extract_referenced_legislation_by_name(
                soup12
            )
        )

        assert result12["regulations"] == ["Biodiversity Regulation"]
        assert result12["directives"] == ["Water Framework Directive"]

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

        assert result13["charters"] == ["Charter of Fundamental Rights"]
        assert result13["treaties"] == ["Maastricht Treaty"]

        # 14. Case-insensitivity, weird spacing/hyphens
        html14 = "<div>The habitat   Directive and the general-data-protection Regulation apply.</div>"
        soup14 = BeautifulSoup(html14, "html.parser")
        result14 = (
            self.parser.structural_analysis.extract_referenced_legislation_by_name(
                soup14
            )
        )

        assert not result14, "Generic legislation terms should be filtered out"
