"""
Behavioural tests for structural analysis of follow-up website pages.

This module tests extraction of:
- Referenced EU legislation by formal identifiers (CELEX, Official Journal)
- Referenced EU legislation by their common names
"""

# Standard library
import json

# Third party
import pytest
from bs4 import BeautifulSoup

# Local
from ECI_initiatives.extractor.responses_followup_website.parser.extractors import (
    FollowupWebsiteExtractor,
)


class TestLegislativeReferences:
    """Tests for structural analysis fields."""

    def test_extract_referenced_legislation_by_id(self):
        """Test extraction of related EU legislation references."""

        # Test 1: CELEX from links
        html = """
        <html>
            <body>
                <a href="https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32025R1422">
                    Implementing Regulation
                </a>
            </body>
        </html>
        """

        extractor = FollowupWebsiteExtractor(html)
        result = extractor.extract_referenced_legislation_by_id()

        assert result is not None
        data = json.loads(result)
        assert "CELEX" in data
        assert "32025R1422" in data["CELEX"]

        # Test 2: CELEX from URL-encoded links
        html = """
        <html>
            <body>
                <a href="https://eur-lex.europa.eu/legal-content/EN/TXT?uri=CELEX%3A32025R1422">
                    Implementing Regulation
                </a>
            </body>
        </html>
        """
        extractor = FollowupWebsiteExtractor(html)
        result = extractor.extract_referenced_legislation_by_id()

        assert result is not None
        data = json.loads(result)
        assert "CELEX" in data
        assert "32025R1422" in data["CELEX"]

        # Test 3: CELEX from text
        html = """
        <html>
            <body>
                <p>See CELEX:32022R0868 for more details.</p>
            </body>
        </html>
        """
        extractor = FollowupWebsiteExtractor(html)
        result = extractor.extract_referenced_legislation_by_id()

        assert result is not None
        data = json.loads(result)
        assert "CELEX" in data
        assert "32022R0868" in data["CELEX"]

        # Test 4: Regulation references
        html = """
        <html>
            <body>
                <p>According to Regulation (EC) No 178/2002, animals must be protected.</p>
                <p>See also Regulation (EU) 2016/679 on data protection.</p>
            </body>
        </html>
        """
        extractor = FollowupWebsiteExtractor(html)
        result = extractor.extract_referenced_legislation_by_id()

        assert result is not None
        data = json.loads(result)
        assert "Regulation" in data
        assert "178/2002" in data["Regulation"]
        assert "2016/679" in data["Regulation"]

        # Test 5: Directive references
        html = """
        <html>
            <body>
                <p>Directive 2008/120/EC establishes minimum standards.</p>
                <p>See Directive 2010/63/EU on animal protection.</p>
            </body>
        </html>
        """
        extractor = FollowupWebsiteExtractor(html)
        result = extractor.extract_referenced_legislation_by_id()

        assert result is not None
        data = json.loads(result)
        assert "Directive" in data
        assert "2008/120/EC" in data["Directive"]
        assert "2010/63/EU" in data["Directive"]

        # Test 6: Decision references
        html = """
        <html>
            <body>
                <p>Commission Decision (EU) 2023/456 was adopted.</p>
                <p>Council Decision No 2015/123 is also relevant.</p>
            </body>
        </html>
        """
        extractor = FollowupWebsiteExtractor(html)
        result = extractor.extract_referenced_legislation_by_id()

        assert result is not None
        data = json.loads(result)
        assert "Decision" in data
        assert "2023/456" in data["Decision"]
        assert "2015/123" in data["Decision"]

        # Test 7: Article references
        html = """
        <html>
            <body>
                <p>Article 31 of Regulation 178/2002 requires a technical report.</p>
                <p>Article 29 provides the basis for scientific opinions.</p>
                <p>See Article 13(1) for more details.</p>
            </body>
        </html>
        """
        extractor = FollowupWebsiteExtractor(html)
        result = extractor.extract_referenced_legislation_by_id()

        assert result is not None
        data = json.loads(result)
        assert "Article" in data
        assert "31" in data["Article"]
        assert "29" in data["Article"]
        assert "13(1)" in data["Article"]

        # Test 8: Official Journal L series (legislation)
        html = """
        <html>
            <body>
                <a href="https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=uriserv:OJ.L_.2025.123.01.0001.01.ENG">
                    OJ L 123, 15.5.2025
                </a>
            </body>
        </html>
        """
        extractor = FollowupWebsiteExtractor(html)
        result = extractor.extract_referenced_legislation_by_id()

        assert result is not None
        data = json.loads(result)
        assert "official_journal" in data
        assert "legislation" in data["official_journal"]
        assert "2025, 123" in data["official_journal"]["legislation"]

        # Test 9: Official Journal C series (information)
        html = """
        <html>
            <body>
                <a href="https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=uriserv:OJ.C_.2024.456.01.0001.01.ENG">
                    OJ C 456, 12.11.2024
                </a>
            </body>
        </html>
        """
        extractor = FollowupWebsiteExtractor(html)
        result = extractor.extract_referenced_legislation_by_id()

        assert result is not None
        data = json.loads(result)
        assert "official_journal" in data
        assert "information_and_notices" in data["official_journal"]
        assert "2024, 456" in data["official_journal"]["information_and_notices"]

        # Test 10: Official Journal both L and C series
        html = """
        <html>
            <body>
                <a href="https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=uriserv:OJ.L_.2025.123.01.0001.01.ENG">
                    OJ L 123, 15.5.2025
                </a>
                <a href="https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=uriserv:OJ.C_.2024.456.01.0001.01.ENG">
                    OJ C 456, 12.11.2024
                </a>
            </body>
        </html>
        """
        extractor = FollowupWebsiteExtractor(html)
        result = extractor.extract_referenced_legislation_by_id()

        assert result is not None
        data = json.loads(result)
        assert "official_journal" in data
        assert "legislation" in data["official_journal"]
        assert "information_and_notices" in data["official_journal"]
        assert "2025, 123" in data["official_journal"]["legislation"]
        assert "2024, 456" in data["official_journal"]["information_and_notices"]

        # Test 11: No references
        html = """
        <html>
            <body>
                <p>This is a page about animal welfare with no specific legislation references.</p>
                <p>The Commission will consider future proposals.</p>
            </body>
        </html>
        """
        extractor = FollowupWebsiteExtractor(html)
        result = extractor.extract_referenced_legislation_by_id()

        assert result is None

        # Test 12: Duplicate handling
        html = """
        <html>
            <body>
                <p>Regulation (EC) No 178/2002 establishes standards.</p>
                <p>As mentioned, Regulation (EC) No 178/2002 is important.</p>
                <p>Article 29 and Article 31 are relevant.</p>
                <p>See Article 29 for more details.</p>
            </body>
        </html>
        """
        extractor = FollowupWebsiteExtractor(html)
        result = extractor.extract_referenced_legislation_by_id()

        assert result is not None
        data = json.loads(result)
        assert "Regulation" in data
        assert data["Regulation"].count("178/2002") == 1
        assert "Article" in data
        assert data["Article"].count("29") == 1
        assert data["Article"].count("31") == 1

        # Test 13: Combined references (multiple types)
        html = """
        <html>
            <body>
                <p>According to Article 31 of Regulation (EC) No 178/2002, EFSA must deliver a technical report.</p>
                <p>Article 29 of Regulation (EC) No 178/2002 requires a scientific opinion.</p>
                <p>See also Directive 2008/120/EC and Commission Decision (EU) 2023/456.</p>
                <a href="https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32025R1422">
                    Implementing Regulation
                </a>
                <a href="https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=uriserv:OJ.L_.2025.123.01.0001.01.ENG">
                    OJ L 123
                </a>
            </body>
        </html>
        """
        extractor = FollowupWebsiteExtractor(html)
        result = extractor.extract_referenced_legislation_by_id()

        assert result is not None
        data = json.loads(result)
        assert "Regulation" in data
        assert "178/2002" in data["Regulation"]
        assert "Article" in data
        assert "29" in data["Article"]
        assert "31" in data["Article"]
        assert "Directive" in data
        assert "2008/120/EC" in data["Directive"]
        assert "Decision" in data
        assert "2023/456" in data["Decision"]
        assert "CELEX" in data
        assert "32025R1422" in data["CELEX"]
        assert "official_journal" in data
        assert "legislation" in data["official_journal"]
        assert "2025, 123" in data["official_journal"]["legislation"]

        # Test 14: CELEX merge from text and links
        html = """
        <html>
            <body>
                <p>See CELEX:32022R0868 for details.</p>
                <a href="https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32025R1422">
                    Another regulation
                </a>
            </body>
        </html>
        """
        extractor = FollowupWebsiteExtractor(html)
        result = extractor.extract_referenced_legislation_by_id()

        assert result is not None
        data = json.loads(result)
        assert "CELEX" in data
        assert "32022R0868" in data["CELEX"]
        assert "32025R1422" in data["CELEX"]
        assert len(data["CELEX"]) == 2

        # Test 15: Real-world Fur Free Europe example
        html = """
        <html>
            <body>
                <p>The Commission mandated EFSA to deliver a technical report, 
                in accordance with Article 31 of Regulation EC No 178/2002 and 
                a scientific opinion in accordance with Article 29 of Regulation EC No 178/2002.</p>
                <p>Through an 
                <a href="https://eur-lex.europa.eu/legal-content/EN/TXT?uri=CELEX%3A32025R1422&qid=1753087782491">
                    Implementing Regulation adopted on 17 July 2025
                </a>, American mink is now listed under the Invasive Alien Species Regulation.</p>
            </body>
        </html>
        """
        extractor = FollowupWebsiteExtractor(html)
        result = extractor.extract_referenced_legislation_by_id()

        assert result is not None
        data = json.loads(result)
        assert "Regulation" in data
        assert "178/2002" in data["Regulation"]
        assert "Article" in data
        assert "31" in data["Article"]
        assert "29" in data["Article"]
        assert "CELEX" in data
        assert "32025R1422" in data["CELEX"]

        # Test 16: Regulation format variations
        html = """
        <html>
            <body>
                <p>Regulation (EU) 2016/679 on data protection.</p>
                <p>Regulation (EC) No. 178/2002 on food law.</p>
                <p>Regulation (EU) No 1169/2011 on food information.</p>
            </body>
        </html>
        """
        extractor = FollowupWebsiteExtractor(html)
        result = extractor.extract_referenced_legislation_by_id()

        assert result is not None
        data = json.loads(result)
        assert "Regulation" in data
        assert "2016/679" in data["Regulation"]
        assert "178/2002" in data["Regulation"]
        assert "1169/2011" in data["Regulation"]

        # Test 17: Article with subsections
        html = """
        <html>
            <body>
                <p>Article 13(1) specifies the requirements.</p>
                <p>See Article 5(2a) for exceptions.</p>
                <p>Article 22 applies generally.</p>
            </body>
        </html>
        """
        extractor = FollowupWebsiteExtractor(html)
        result = extractor.extract_referenced_legislation_by_id()

        assert result is not None
        data = json.loads(result)
        assert "Article" in data
        assert "13(1)" in data["Article"]
        assert "5(2a)" in data["Article"]
        assert "22" in data["Article"]

    def test_extract_referenced_legislation_by_name(self):
        """Test extraction of referenced EU legislation by name."""

        # Test 1: Single Directive name
        html = """
        <html>
            <body>
                <p>The Water Framework Directive establishes environmental objectives.</p>
            </body>
        </html>
        """
        extractor = FollowupWebsiteExtractor(html)
        result = extractor.extract_referenced_legislation_by_name()

        assert result is not None
        assert "directives" in result
        assert "Water Framework Directive" in result["directives"]

        # Test 2: Multiple Directive names
        html = """
        <html>
            <body>
                <p>The Birds Directive and Habitats Directive protect wildlife.</p>
                <p>The Nitrates Directive addresses water pollution.</p>
            </body>
        </html>
        """
        extractor = FollowupWebsiteExtractor(html)
        result = extractor.extract_referenced_legislation_by_name()

        assert result is not None
        assert "directives" in result
        assert "Birds Directive" in result["directives"]
        assert "Habitats Directive" in result["directives"]
        assert "Nitrates Directive" in result["directives"]
        assert len(result["directives"]) == 3

        # Test 3: Single Regulation name
        html = """
        <html>
            <body>
                <p>The REACH Regulation controls chemical substances.</p>
            </body>
        </html>
        """
        extractor = FollowupWebsiteExtractor(html)
        result = extractor.extract_referenced_legislation_by_name()

        assert result is not None
        assert "regulations" in result
        assert "REACH Regulation" in result["regulations"]

        # Test 4: Multiple Regulation names
        html = """
        <html>
            <body>
                <p>The GDPR and REACH Regulation are key laws.</p>
                <p>The Biocides Regulation controls product placement.</p>
            </body>
        </html>
        """
        extractor = FollowupWebsiteExtractor(html)
        result = extractor.extract_referenced_legislation_by_name()

        assert result is not None
        assert "regulations" in result
        assert "GDPR" in result["regulations"]
        assert "REACH" in result["regulations"]
        assert "Biocides Regulation" in result["regulations"]
        assert len(result["regulations"]) == 3

        # Test 5: Treaty names
        html = """
        <html>
            <body>
                <p>The Treaty on European Union (TEU) establishes the EU.</p>
                <p>The Lisbon Treaty amended the existing treaties.</p>
            </body>
        </html>
        """
        extractor = FollowupWebsiteExtractor(html)
        result = extractor.extract_referenced_legislation_by_name()

        assert result is not None
        assert "treaties" in result
        assert (
            "TEU" in result["treaties"]
            or "Treaty on European Union" in result["treaties"]
        )
        assert "Lisbon Treaty" in result["treaties"]

        # Test 6: Charter names
        html = """
        <html>
            <body>
                <p>The Charter of Fundamental Rights protects citizen rights.</p>
            </body>
        </html>
        """
        extractor = FollowupWebsiteExtractor(html)
        result = extractor.extract_referenced_legislation_by_name()

        assert result is not None
        assert "charters" in result
        assert "Charter of Fundamental Rights" in result["charters"]

        # Test 7: Mixed legislation types
        html = """
        <html>
            <body>
                <p>The Water Framework Directive and REACH Regulation are important.</p>
                <p>The Treaty on European Union provides the legal basis.</p>
                <p>The Charter of Fundamental Rights applies.</p>
            </body>
        </html>
        """
        extractor = FollowupWebsiteExtractor(html)
        result = extractor.extract_referenced_legislation_by_name()

        assert result is not None
        assert "directives" in result
        assert "Water Framework Directive" in result["directives"]
        assert "regulations" in result
        assert "REACH Regulation" in result["regulations"]
        assert "treaties" in result
        assert "charters" in result

        # Test 8: Filter generic "Implementing Regulation"
        html = """
        <html>
            <body>
                <p>An Implementing Regulation was adopted.</p>
                <p>The REACH Regulation is specific legislation.</p>
            </body>
        </html>
        """
        extractor = FollowupWebsiteExtractor(html)
        result = extractor.extract_referenced_legislation_by_name()

        assert result is not None
        assert "regulations" in result
        assert "Implementing Regulation" not in result["regulations"]
        assert "REACH Regulation" in result["regulations"]

        # Test 9: Filter generic "Directive" standalone
        html = """
        <html>
            <body>
                <p>A new Directive was proposed.</p>
                <p>The Birds Directive is specific.</p>
            </body>
        </html>
        """
        extractor = FollowupWebsiteExtractor(html)
        result = extractor.extract_referenced_legislation_by_name()

        assert result is not None
        if "directives" in result:
            assert "Directive" not in result["directives"]
            assert "new Directive" not in result["directives"]
            assert "Birds Directive" in result["directives"]

        # Test 10: Filter "Proposal for Regulation"
        html = """
        <html>
            <body>
                <p>The Commission presented a Proposal for Regulation.</p>
                <p>The GDPR is established law.</p>
            </body>
        </html>
        """
        extractor = FollowupWebsiteExtractor(html)
        result = extractor.extract_referenced_legislation_by_name()

        assert result is not None
        assert "regulations" in result
        assert "Proposal for Regulation" not in result["regulations"]
        assert "GDPR" in result["regulations"]

        # Test 11: Filter "Delegated Regulation"
        html = """
        <html>
            <body>
                <p>A Delegated Regulation was issued.</p>
                <p>The REACH Regulation applies.</p>
            </body>
        </html>
        """
        extractor = FollowupWebsiteExtractor(html)
        result = extractor.extract_referenced_legislation_by_name()

        assert result is not None
        assert "regulations" in result
        assert "Delegated Regulation" not in result["regulations"]
        assert "REACH Regulation" in result["regulations"]

        # Test 12: Filter "Amending Directive"
        html = """
        <html>
            <body>
                <p>An Amending Directive was adopted.</p>
                <p>The Water Framework Directive remains in force.</p>
            </body>
        </html>
        """
        extractor = FollowupWebsiteExtractor(html)
        result = extractor.extract_referenced_legislation_by_name()

        assert result is not None
        if "directives" in result:
            assert "Amending Directive" not in result["directives"]
            assert "Water Framework Directive" in result["directives"]

        # Test 13: Directive abbreviations (WFD, BHD, etc.)
        html = """
        <html>
            <body>
                <p>The WFD and BHD protect the environment.</p>
                <p>The UWWTD addresses waste water.</p>
            </body>
        </html>
        """
        extractor = FollowupWebsiteExtractor(html)
        result = extractor.extract_referenced_legislation_by_name()

        assert result is not None
        assert "directives" in result
        assert "WFD" in result["directives"]
        assert "BHD" in result["directives"]
        assert "UWWTD" in result["directives"]

        # Test 14: Regulation abbreviations (REACH, GDPR, etc.)
        html = """
        <html>
            <body>
                <p>REACH and GDPR are cornerstone regulations.</p>
                <p>The ETS controls emissions.</p>
            </body>
        </html>
        """
        extractor = FollowupWebsiteExtractor(html)
        result = extractor.extract_referenced_legislation_by_name()

        assert result is not None
        assert "regulations" in result
        assert "REACH" in result["regulations"]
        assert "GDPR" in result["regulations"]
        assert "ETS" in result["regulations"]

        # Test 15: Treaty abbreviations (TEU, TFEU)
        html = """
        <html>
            <body>
                <p>TEU and TFEU form the basis of EU law.</p>
            </body>
        </html>
        """
        extractor = FollowupWebsiteExtractor(html)
        result = extractor.extract_referenced_legislation_by_name()

        assert result is not None
        assert "treaties" in result
        assert "TEU" in result["treaties"]
        assert "TFEU" in result["treaties"]

        # Test 16: Charter abbreviations (CFR)
        html = """
        <html>
            <body>
                <p>The CFR protects fundamental rights.</p>
            </body>
        </html>
        """
        extractor = FollowupWebsiteExtractor(html)
        result = extractor.extract_referenced_legislation_by_name()

        assert result is not None
        assert "charters" in result
        assert "CFR" in result["charters"]

        # Test 17: Duplicate handling (case-insensitive)
        html = """
        <html>
            <body>
                <p>The Water Framework Directive is important.</p>
                <p>The water framework directive was amended.</p>
                <p>WFD implementation is ongoing.</p>
            </body>
        </html>
        """
        extractor = FollowupWebsiteExtractor(html)
        result = extractor.extract_referenced_legislation_by_name()

        assert result is not None
        assert "directives" in result
        # Should contain both full name and abbreviation, but not duplicates
        assert "Water Framework Directive" in result["directives"]
        assert "WFD" in result["directives"]
        # Check no case duplicates
        directive_lower = [d.lower() for d in result["directives"]]
        assert len(directive_lower) == len(set(directive_lower))

        # Test 18: Split multiple legislations with "and"
        html = """
        <html>
            <body>
                <p>The Birds Directive and Habitats Directive protect nature.</p>
            </body>
        </html>
        """
        extractor = FollowupWebsiteExtractor(html)
        result = extractor.extract_referenced_legislation_by_name()

        assert result is not None
        assert "directives" in result
        assert "Birds Directive" in result["directives"]
        assert "Habitats Directive" in result["directives"]
        # Should NOT contain the combined form
        assert "Birds Directive and Habitats Directive" not in result["directives"]

        # Test 19: Complex directive names with prepositions
        html = """
        <html>
            <body>
                <p>The Directive on Environmental Impact Assessment applies.</p>
                <p>The Regulation on Invasive Alien Species is relevant.</p>
            </body>
        </html>
        """
        extractor = FollowupWebsiteExtractor(html)
        result = extractor.extract_referenced_legislation_by_name()

        assert result is not None
        assert "directives" in result
        assert any("Environmental Impact Assessment" in d for d in result["directives"])
        assert "regulations" in result
        assert any("Invasive Alien Species" in r for r in result["regulations"])

        # Test 20: No legislation references
        html = """
        <html>
            <body>
                <p>This page discusses environmental policy.</p>
                <p>No specific legislation is mentioned.</p>
            </body>
        </html>
        """
        extractor = FollowupWebsiteExtractor(html)
        result = extractor.extract_referenced_legislation_by_name()

        assert result is None or result == {}

        # Test 21: Legislation with strong tags (preprocessing)
        html = """
        <html>
            <body>
                <p>The <strong>Water Framework Directive</strong> is important.</p>
                <p><strong>REACH Regulation</strong> controls chemicals.</p>
            </body>
        </html>
        """
        extractor = FollowupWebsiteExtractor(html)
        result = extractor.extract_referenced_legislation_by_name()

        assert result is not None
        assert "directives" in result
        assert "Water Framework Directive" in result["directives"]
        assert "regulations" in result
        assert "REACH Regulation" in result["regulations"]

        # Test 22: Remove "REACH" when "REACH Regulation" exists
        html = """
        <html>
            <body>
                <p>REACH applies to chemicals.</p>
                <p>The REACH Regulation establishes procedures.</p>
            </body>
        </html>
        """
        extractor = FollowupWebsiteExtractor(html)
        result = extractor.extract_referenced_legislation_by_name()

        assert result is not None
        assert "regulations" in result
        assert "REACH Regulation" in result["regulations"]
        # Should NOT contain standalone "REACH" if "REACH Regulation" exists
        if len(result["regulations"]) == 1:
            assert result["regulations"][0] == "REACH Regulation"

        # Test 23: Real-world Fur Free Europe example
        html = """
        <html>
            <body>
                <p>Through an Implementing Regulation adopted on 17 July 2025, 
                American mink is now listed under the Invasive Alien Species Regulation.</p>
                <p>The Charter of Fundamental Rights and TEU provide the legal basis.</p>
            </body>
        </html>
        """
        extractor = FollowupWebsiteExtractor(html)
        result = extractor.extract_referenced_legislation_by_name()

        assert result is not None
        assert "regulations" in result
        assert "Implementing Regulation" not in result["regulations"]
        assert "Invasive Alien Species Regulation" in result["regulations"]
        assert "charters" in result
        assert "Charter of Fundamental Rights" in result["charters"]
        assert "treaties" in result
        assert "TEU" in result["treaties"]

        # Test 24: Leading articles removal
        html = """
        <html>
            <body>
                <p>The Water Framework Directive is key.</p>
                <p>A new regulation was proposed.</p>
            </body>
        </html>
        """
        extractor = FollowupWebsiteExtractor(html)
        result = extractor.extract_referenced_legislation_by_name()

        assert result is not None
        assert "directives" in result
        # Should be "Water Framework Directive", not "The Water Framework Directive"
        assert "Water Framework Directive" in result["directives"]
        assert "The Water Framework Directive" not in result["directives"]
