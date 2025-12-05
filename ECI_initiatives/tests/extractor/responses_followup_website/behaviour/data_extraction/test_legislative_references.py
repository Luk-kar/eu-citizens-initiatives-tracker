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
        # TODO: Test Directive names
        # TODO: Test Regulation names
        # TODO: Test Treaty names
        # TODO: Test Charter names
        pass
