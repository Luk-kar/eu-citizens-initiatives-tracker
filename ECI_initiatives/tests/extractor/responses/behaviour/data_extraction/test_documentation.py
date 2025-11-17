"""Tests for extracting multimedia and documentation links from ECI responses."""

# Third party
import pytest
from bs4 import BeautifulSoup

# Local
from ECI_initiatives.extractor.responses.parser.main_parser import ECIResponseHTMLParser
from ECI_initiatives.extractor.responses.responses_logger import (
    ResponsesExtractorLogger,
)


class TestMultimediaDocumentation:
    """Tests for multimedia and documentation extraction."""

    @classmethod
    def setup_class(cls):
        """Setup parser instance."""
        logger = ResponsesExtractorLogger().setup()
        cls.parser = ECIResponseHTMLParser(logger=logger)

    def test_commission_factsheet_url(self):
        """Test extraction of Commission factsheet PDF URL."""

        # Test case 1: Standard factsheet with valid download link
        html_1 = """
        <html>
            <div class="ecl-file" data-ecl-file="">
                <div class="ecl-file__container">
                    <picture class="ecl-picture ecl-file__picture">
                        <img alt="Picture of the first page of the factsheet" 
                            src="https://citizens-initiative.europa.eu/sites/default/files/thumbnail.png"/>
                    </picture>
                    <div class="ecl-file__info">
                        <div class="ecl-file__title">Factsheet - Successful Initiatives - Fur Free Europe</div>
                        <div class="ecl-file__language">English</div>
                        <div class="ecl-file__meta">(234.58 KB - PDF)</div>
                    </div>
                    <div class="ecl-file__action">
                        <a href="https://citizens-initiative.europa.eu/sites/default/files/2023-12/Factsheet.pdf" 
                        class="ecl-link ecl-link--standalone ecl-link--icon ecl-file__download">
                            Download
                        </a>
                    </div>
                </div>
            </div>
        </html>
        """

        soup_1 = BeautifulSoup(html_1, "html.parser")
        parser_1 = ECIResponseHTMLParser(soup_1)
        parser_1.registration_number = "2022/000002"

        result_1 = parser_1.multimedia_docs.extract_commission_factsheet_url(soup_1)

        assert result_1 is not None
        assert (
            result_1
            == "https://citizens-initiative.europa.eu/sites/default/files/2023-12/Factsheet.pdf"
        )
        assert "citizens-initiative.europa.eu" in result_1
        assert result_1.endswith(".pdf")

        # Test case 2: No factsheet element present (returns None)
        html_2 = """
        <html>
            <div class="ecl-file">
                <div class="ecl-file__container">
                    <div class="ecl-file__info">
                        <div class="ecl-file__title">Communication Document</div>
                        <div class="ecl-file__language">English</div>
                    </div>
                    <div class="ecl-file__action">
                        <a href="https://ec.europa.eu/transparency/documents-register/detail?ref=COM(2023)123" 
                        class="ecl-file__download">
                            Download
                        </a>
                    </div>
                </div>
            </div>
        </html>
        """

        soup_2 = BeautifulSoup(html_2, "html.parser")
        parser_2 = ECIResponseHTMLParser(soup_2)
        parser_2.registration_number = "2012/000003"

        result_2 = parser_2.multimedia_docs.extract_commission_factsheet_url(soup_2)

        assert result_2 is None

        # Test case 3: Factsheet title exists but download link is missing (error)
        html_3 = """
        <html>
            <div class="ecl-file">
                <div class="ecl-file__container">
                    <div class="ecl-file__info">
                        <div class="ecl-file__title">Factsheet - Save Bees and Farmers</div>
                        <div class="ecl-file__language">English</div>
                    </div>
                    <div class="ecl-file__action">
                        <!-- No download link here -->
                    </div>
                </div>
            </div>
        </html>
        """

        soup_3 = BeautifulSoup(html_3, "html.parser")
        parser_3 = ECIResponseHTMLParser(soup_3)
        parser_3.registration_number = "2019/000016"

        with pytest.raises(
            ValueError,
            match="Factsheet element found but download link is missing for 2019/000016",
        ):
            parser_3.multimedia_docs.extract_commission_factsheet_url(soup_3)

        # Test case 4: Factsheet exists but href is empty (error)
        html_4 = """
        <html>
            <div class="ecl-file">
                <div class="ecl-file__container">
                    <div class="ecl-file__info">
                        <div class="ecl-file__title">Factsheet - End Cage Age</div>
                        <div class="ecl-file__language">English</div>
                    </div>
                    <div class="ecl-file__action">
                        <a href="" class="ecl-link ecl-file__download">
                            Download
                        </a>
                    </div>
                </div>
            </div>
        </html>
        """

        soup_4 = BeautifulSoup(html_4, "html.parser")
        parser_4 = ECIResponseHTMLParser(soup_4)
        parser_4.registration_number = "2018/000004"

        with pytest.raises(
            ValueError,
            match="Factsheet download link found but href is empty for 2018/000004",
        ):
            parser_4.multimedia_docs.extract_commission_factsheet_url(soup_4)

        # Test case 5: Multiple file divs, only one is factsheet
        html_5 = """
        <html>
            <div class="ecl-file">
                <div class="ecl-file__container">
                    <div class="ecl-file__info">
                        <div class="ecl-file__title">Communication Document</div>
                    </div>
                    <div class="ecl-file__action">
                        <a href="https://ec.europa.eu/transparency/documents-register/communication.pdf" 
                        class="ecl-file__download">Download</a>
                    </div>
                </div>
            </div>
            <div class="ecl-file">
                <div class="ecl-file__container">
                    <div class="ecl-file__info">
                        <div class="ecl-file__title">Annex Document</div>
                    </div>
                    <div class="ecl-file__action">
                        <a href="https://ec.europa.eu/transparency/documents-register/annex.pdf" 
                        class="ecl-file__download">Download</a>
                    </div>
                </div>
            </div>
            <div class="ecl-file">
                <div class="ecl-file__container">
                    <div class="ecl-file__info">
                        <div class="ecl-file__title">Factsheet - Minority SafePack</div>
                        <div class="ecl-file__language">English</div>
                    </div>
                    <div class="ecl-file__action">
                        <a href="https://citizens-initiative.europa.eu/sites/default/files/factsheet_minority.pdf" 
                        class="ecl-file__download">Download</a>
                    </div>
                </div>
            </div>
        </html>
        """

        soup_5 = BeautifulSoup(html_5, "html.parser")
        parser_5 = ECIResponseHTMLParser(soup_5)
        parser_5.registration_number = "2017/000004"

        result_5 = parser_5.multimedia_docs.extract_commission_factsheet_url(soup_5)

        assert result_5 is not None
        assert "factsheet_minority.pdf" in result_5
        # Should return the factsheet, not the other documents
        assert "communication.pdf" not in result_5
        assert "annex.pdf" not in result_5

        # Test case 6: Case-insensitive factsheet detection
        html_6 = """
        <html>
            <div class="ecl-file">
                <div class="ecl-file__container">
                    <div class="ecl-file__info">
                        <div class="ecl-file__title">FACTSHEET - Stop Finning</div>
                    </div>
                    <div class="ecl-file__action">
                        <a href="https://citizens-initiative.europa.eu/sites/default/files/stop_finning.pdf" 
                        class="ecl-file__download">Download</a>
                    </div>
                </div>
            </div>
        </html>
        """

        soup_6 = BeautifulSoup(html_6, "html.parser")
        parser_6 = ECIResponseHTMLParser(soup_6)
        parser_6.registration_number = "2020/000001"

        result_6 = parser_6.multimedia_docs.extract_commission_factsheet_url(soup_6)

        assert result_6 is not None
        assert "stop_finning.pdf" in result_6

        # Test case 7: Factsheet with translations (should only get main English version)
        html_7 = """
        <html>
            <div class="ecl-file ecl-file--has-translation">
                <div class="ecl-file__container">
                    <div class="ecl-file__info">
                        <div class="ecl-file__title">Factsheet - Save Cruelty Free Cosmetics</div>
                        <div class="ecl-file__language">English</div>
                        <div class="ecl-file__meta">(1.31 MB - PDF)</div>
                    </div>
                    <div class="ecl-file__action">
                        <a href="https://citizens-initiative.europa.eu/sites/default/files/2023-08/factsheet_EN.pdf" 
                        class="ecl-link ecl-file__download">Download</a>
                    </div>
                </div>
                <div class="ecl-file__translation-container">
                    <button class="ecl-file__translation-toggle">Available translations (23)</button>
                    <ul class="ecl-file__translation-list">
                        <li class="ecl-file__translation-item">
                            <a href="https://citizens-initiative.europa.eu/sites/default/files/2023-08/factsheet_BG.pdf" 
                            class="ecl-link ecl-file__translation-download">
                                <div class="ecl-file__language" lang="bg">български</div>
                            </a>
                        </li>
                        <li class="ecl-file__translation-item">
                            <a href="https://citizens-initiative.europa.eu/sites/default/files/2023-08/factsheet_ES.pdf" 
                            class="ecl-link ecl-file__translation-download">
                                <div class="ecl-file__language" lang="es">Español</div>
                            </a>
                        </li>
                    </ul>
                </div>
            </div>
        </html>
        """

        soup_7 = BeautifulSoup(html_7, "html.parser")
        parser_7 = ECIResponseHTMLParser(soup_7)
        parser_7.registration_number = "2021/000006"

        result_7 = parser_7.multimedia_docs.extract_commission_factsheet_url(soup_7)

        assert result_7 is not None
        assert "factsheet_EN.pdf" in result_7
        # Should not return translations
        assert "factsheet_BG.pdf" not in result_7
        assert "factsheet_ES.pdf" not in result_7

        # Test case 8: Empty page (no ecl-file divs at all)
        html_8 = """
        <html>
            <body>
                <h2>Submission and examination</h2>
                <p>The initiative was submitted on some date.</p>
            </body>
        </html>
        """

        soup_8 = BeautifulSoup(html_8, "html.parser")
        parser_8 = ECIResponseHTMLParser(soup_8)
        parser_8.registration_number = "2012/000005"

        result_8 = parser_8.multimedia_docs.extract_commission_factsheet_url(soup_8)

        assert result_8 is None

    def test_followup_dedicated_website_detection(self):
        """Test detection of dedicated ECI campaign website by URL pattern."""

        # Test case 1: Valid ECI dedicated website URL
        html_1 = """
        <html>
            <body>
                <p>For more information, please visit the 
                    <a class="Hyperlink SCXW169299639 BCX8" 
                    href="https://food.ec.europa.eu/animals/animal-welfare/eci/eci-end-cage-age_en">
                        campaign website
                    </a>
                </p>
            </body>
        </html>
        """

        soup_1 = BeautifulSoup(html_1, "html.parser")
        parser_1 = ECIResponseHTMLParser(soup_1)
        parser_1.registration_number = "2018/000004"

        result_1 = parser_1.multimedia_docs.extract_followup_dedicated_website(soup_1)

        assert result_1 is not None
        assert (
            result_1
            == "https://food.ec.europa.eu/animals/animal-welfare/eci/eci-end-cage-age_en"
        )
        assert "eci-end-cage-age" in result_1

        # Test case 2: Another valid ECI URL pattern
        html_2 = """
        <html>
            <body>
                <p>More details are available on the 
                    <a href="https://ec.europa.eu/info/law/better-regulation/eci/eci-water_en">
                        dedicated page.
                    </a>
                </p>
            </body>
        </html>
        """

        soup_2 = BeautifulSoup(html_2, "html.parser")
        parser_2 = ECIResponseHTMLParser(soup_2)
        parser_2.registration_number = "2012/000003"

        result_2 = parser_2.multimedia_docs.extract_followup_dedicated_website(soup_2)

        assert result_2 is not None
        assert "eci-water" in result_2
        assert "eci/eci-" in result_2

        # Test case 3: Valid URL with different subdomain
        html_3 = """
        <html>
            <body>
                <p>Check the 
                    <a href="https://single-market-economy.ec.europa.eu/sectors/chemicals/eci/eci-stop-vivisection_en">
                        initiative page
                    </a>
                    for updates.
                </p>
            </body>
        </html>
        """

        soup_3 = BeautifulSoup(html_3, "html.parser")
        parser_3 = ECIResponseHTMLParser(soup_3)
        parser_3.registration_number = "2015/000007"

        result_3 = parser_3.multimedia_docs.extract_followup_dedicated_website(soup_3)

        assert result_3 is not None
        assert "eci-stop-vivisection" in result_3
        assert "single-market-economy" in result_3

        # Test case 4: No matching URL pattern (returns None)
        html_4 = """
        <html>
            <body>
                <p>The Commission has published its response.</p>
                <a href="https://ec.europa.eu/transparency/documents-register/detail?ref=COM(2023)123">
                    Communication document
                </a>
            </body>
        </html>
        """

        soup_4 = BeautifulSoup(html_4, "html.parser")
        parser_4 = ECIResponseHTMLParser(soup_4)
        parser_4.registration_number = "2021/000008"

        result_4 = parser_4.multimedia_docs.extract_followup_dedicated_website(soup_4)

        assert result_4 is None

        # Test case 5: Wrong language code (_de instead of _en)
        html_5 = """
        <html>
            <body>
                <p>Visit the 
                    <a href="https://ec.europa.eu/info/eci/eci-water_de">German version</a>
                    for details.
                </p>
            </body>
        </html>
        """

        soup_5 = BeautifulSoup(html_5, "html.parser")
        parser_5 = ECIResponseHTMLParser(soup_5)
        parser_5.registration_number = "2020/000012"

        result_5 = parser_5.multimedia_docs.extract_followup_dedicated_website(soup_5)

        # Should return None because it's _de, not _en
        assert result_5 is None

        # Test case 6: Multiple links, only one matches pattern
        html_6 = """
        <html>
            <body>
                <p>
                    <a href="https://ec.europa.eu/commission/presscorner/">Press corner</a>
                </p>
                <p>
                    <a href="https://ec.europa.eu/transparency/">Transparency register</a>
                </p>
                <p>For more information, see the 
                    <a href="https://food.ec.europa.eu/animals/animal-welfare/eci/eci-fur-free-europe_en">
                        campaign website
                    </a>
                </p>
                <p>
                    <a href="https://ec.europa.eu/contact/">Contact</a>
                </p>
            </body>
        </html>
        """

        soup_6 = BeautifulSoup(html_6, "html.parser")
        parser_6 = ECIResponseHTMLParser(soup_6)
        parser_6.registration_number = "2022/000009"

        result_6 = parser_6.multimedia_docs.extract_followup_dedicated_website(soup_6)

        assert result_6 is not None
        assert (
            "https://food.ec.europa.eu/animals/animal-welfare/eci/eci-fur-free-europe_en"
            == result_6
        )
        # Should return ECI link, not other links
        assert "presscorner" not in result_6
        assert "transparency" not in result_6
        assert "contact" not in result_6

        # Test case 7: URL without "eci-" prefix (should not match)
        html_7 = """
        <html>
            <body>
                <p>Please check the 
                    <a href="https://citizens-initiative.europa.eu/campaign_en">
                        campaign website
                    </a>
                </p>
            </body>
        </html>
        """

        soup_7 = BeautifulSoup(html_7, "html.parser")
        parser_7 = ECIResponseHTMLParser(soup_7)
        parser_7.registration_number = "2019/000015"

        result_7 = parser_7.multimedia_docs.extract_followup_dedicated_website(soup_7)

        assert result_7 is None  # No "eci-" prefix

        # Test case 8: URL with extra path after _en (should not match)
        html_8 = """
        <html>
            <body>
                <p>Further information on the 
                    <a href="https://ec.europa.eu/environment/eci/eci-chemicals_en/details">
                        details page
                    </a>
                </p>
            </body>
        </html>
        """

        soup_8 = BeautifulSoup(html_8, "html.parser")
        parser_8 = ECIResponseHTMLParser(soup_8)
        parser_8.registration_number = "2018/000003"

        result_8 = parser_8.multimedia_docs.extract_followup_dedicated_website(soup_8)

        assert result_8 is None  # URL doesn't end with _en

        # Test case 9: Valid URL with hyphens in identifier
        html_9 = """
        <html>
            <body>
                <p>Visit our 
                    <a href="https://environment.ec.europa.eu/topics/nature-and-biodiversity/eci/eci-save-bees-and-farmers_en">
                        initiative page
                    </a>
                </p>
            </body>
        </html>
        """

        soup_9 = BeautifulSoup(html_9, "html.parser")
        parser_9 = ECIResponseHTMLParser(soup_9)
        parser_9.registration_number = "2019/000016"

        result_9 = parser_9.multimedia_docs.extract_followup_dedicated_website(soup_9)

        assert result_9 is not None
        assert "eci-save-bees-and-farmers" in result_9

        # Test case 10: Empty page (no links at all)
        html_10 = """
        <html>
            <body>
                <h2>Commission Response</h2>
                <p>The initiative was submitted on some date.</p>
            </body>
        </html>
        """

        soup_10 = BeautifulSoup(html_10, "html.parser")
        parser_10 = ECIResponseHTMLParser(soup_10)
        parser_10.registration_number = "2017/000011"

        result_10 = parser_10.multimedia_docs.extract_followup_dedicated_website(
            soup_10
        )

        assert result_10 is None

        # Test case 11: Non-matching URL patterns
        html_11 = """
        <html>
            <body>
                <a href="https://ec.europa.eu/some-page_en">website information</a>
                <a href="https://ec.europa.eu/another-page/eci-section">dedicated section</a>
            </body>
        </html>
        """

        soup_11 = BeautifulSoup(html_11, "html.parser")
        parser_11 = ECIResponseHTMLParser(soup_11)
        parser_11.registration_number = "2016/000007"

        result_11 = parser_11.multimedia_docs.extract_followup_dedicated_website(
            soup_11
        )

        assert result_11 is None

        # Test case 12: Returns first match when multiple matching URLs exist
        html_12 = """
        <html>
            <body>
                <p>First link: 
                    <a href="https://ec.europa.eu/first/eci/eci-first-initiative_en">first ECI</a>
                </p>
                <p>Second link: 
                    <a href="https://ec.europa.eu/second/eci/eci-second-initiative_en">second ECI</a>
                </p>
            </body>
        </html>
        """

        soup_12 = BeautifulSoup(html_12, "html.parser")
        parser_12 = ECIResponseHTMLParser(soup_12)
        parser_12.registration_number = "2024/000001"

        result_12 = parser_12.multimedia_docs.extract_followup_dedicated_website(
            soup_12
        )

        assert result_12 is not None
        assert "eci-first-initiative" in result_12
        # Should return first match, not second
        assert "eci-second-initiative" not in result_12

        # Test case 13: Empty href attribute (should be skipped)
        html_13 = """
        <html>
            <body>
                <p>
                    <a href="">empty link</a>
                    <a href="https://ec.europa.eu/valid/eci/eci-valid-initiative_en">valid link</a>
                </p>
            </body>
        </html>
        """

        soup_13 = BeautifulSoup(html_13, "html.parser")
        parser_13 = ECIResponseHTMLParser(soup_13)
        parser_13.registration_number = "2023/000010"

        result_13 = parser_13.multimedia_docs.extract_followup_dedicated_website(
            soup_13
        )

        assert result_13 is not None
        assert "eci-valid-initiative" in result_13

        # Test case 14: Case insensitive pattern matching (URL with uppercase)
        html_14 = """
        <html>
            <body>
                <p>
                    <a href="https://ec.europa.eu/INFO/ECI/eci-test_EN">
                        uppercase URL
                    </a>
                </p>
            </body>
        </html>
        """

        soup_14 = BeautifulSoup(html_14, "html.parser")
        parser_14 = ECIResponseHTMLParser(soup_14)
        parser_14.registration_number = "2023/000011"

        result_14 = parser_14.multimedia_docs.extract_followup_dedicated_website(
            soup_14
        )

        assert result_14 is not None
        assert "eci-test" in result_14.lower()

        # Test case 15: HTTP instead of HTTPS (should not match)
        html_15 = """
        <html>
            <body>
                <p>
                    <a href="http://ec.europa.eu/test/eci/eci-http-test_en">
                        HTTP link
                    </a>
                </p>
            </body>
        </html>
        """

        soup_15 = BeautifulSoup(html_15, "html.parser")
        parser_15 = ECIResponseHTMLParser(soup_15)
        parser_15.registration_number = "2023/000012"

        result_15 = parser_15.multimedia_docs.extract_followup_dedicated_website(
            soup_15
        )

        assert result_15 is None  # Pattern requires https://
