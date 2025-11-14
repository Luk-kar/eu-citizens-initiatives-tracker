"""
Behavioural tests for submission data and procedural timeline extraction.

This module contains tests for parsing the 'Submission and examination'
section of European Citizens' Initiative (ECI) response pages. It verifies
the accurate extraction of key data points related to the submission and
procedural timeline of an initiative, including:

- Date of submission to the Commission.
- URL for the submission news or press release.
- Names of Commission officials who met with the organisers.
- Date of the public hearing at the European Parliament.
- Video URLs for the Parliament hearing.
- Date of the plenary debate at the European Parliament.
- Video and document URLs related to the plenary debate.
- Date of the official Commission Communication adoption.
- URLs for official documents related to the Communication.
"""

# Standard library
import json
from datetime import date as date_type

# Third party
import pytest
from bs4 import BeautifulSoup

# Local
from ECI_initiatives.extractor.responses.parser.main_parser import ECIResponseHTMLParser
from ECI_initiatives.extractor.responses.responses_logger import (
    ResponsesExtractorLogger,
)
from .test_base import BaseParserTest


class TestSubmissionDataExtraction(BaseParserTest):
    """Tests for submission and verification data extraction."""

    def _create_submission_html(self, submission_text: str) -> str:
        """Helper to create HTML with submission section.

        Args:
            submission_text: Text content for submission paragraph

        Returns:
            Complete HTML string with submission section
        """
        return f"""
        <html>
            <body>
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>{submission_text}</p>
            </body>
        </html>
        """

    def test_commission_submission_date_extraction(self):
        """Test extraction of submission date."""
        # Test Case 1: DD Month YYYY format (most common)
        html = self._create_submission_html(
            """
            <a href="https://citizens-initiative.europa.eu/initiatives/details/2017/000002_en">
                Ban glyphosate and protect people and the environment from toxic pesticides
            </a>
            was submitted to the Commission on 6 October 2017, having gathered 1,070,865 statements of support.
        """
        )

        soup = self.create_soup(html)
        date = self.parser.submission_data.extract_commission_submission_date(soup)

        expected_date = date_type(2017, 10, 6)
        assert date == expected_date, f"Expected date {expected_date}, got {date}"
        assert isinstance(date, date_type), "Should return datetime.date object"

        # Test Case 2: DD/MM/YYYY format
        html_ddmmyyyy = self._create_submission_html(
            "One of us was submitted to the Commission on 28/02/2014 having gathered 1,721,626 statements of support."
        )

        soup = self.create_soup(html_ddmmyyyy)
        date = self.parser.submission_data.extract_commission_submission_date(soup)

        expected_date = date_type(2014, 2, 28)
        assert date == expected_date, f"Expected date {expected_date}, got {date}"

        # Test Case 3: With "European Commission" variation
        html_european = self._create_submission_html(
            "The 'Cohesion policy' initiative was submitted to the European Commission on 4 March 2025, "
            "after having gathered 1,269,351 verified statements of support."
        )

        soup = self.create_soup(html_european)
        date = self.parser.submission_data.extract_commission_submission_date(soup)

        expected_date = date_type(2025, 3, 4)
        assert date == expected_date, f"Expected date {expected_date}, got {date}"

        # Test Case 4: Missing date should raise ValueError
        html_no_date = self._create_submission_html("No date information here.")

        soup = self.create_soup(html_no_date)

        # Mock the registration_number instance variable
        self.parser.registration_number = "2099/999999"

        with pytest.raises(
            ValueError, match="No submission date found for initiative 2099/999999"
        ):
            self.parser.submission_data.extract_commission_submission_date(soup)

    def test_submission_news_url(self):
        """Test extraction of submission news URL."""
        test_cases = [
            # (description, submission_text, expected_url)
            (
                "Standard press release with presscorner URL",
                """
                <a href="https://citizens-initiative.europa.eu/initiatives/details/2012/000003_en">Right2Water</a>
                was submitted to the Commission on 20 December 2013. See
                <a href="https://ec.europa.eu/commission/presscorner/detail/en/mex_13_1223">press release</a>.
                """,
                "https://ec.europa.eu/commission/presscorner/detail/en/mex_13_1223",
            ),
            (
                "Press announcement variation",
                """
                The 'Stop Finning' initiative was submitted to the Commission on 11 January 2023. See
                <a href="https://ec.europa.eu/commission/presscorner/detail/en/mex_23_143">press announcement</a>.
                """,
                "https://ec.europa.eu/commission/presscorner/detail/en/mex_23_143",
            ),
            (
                "European Commission news variation",
                """
                The initiative was submitted to the European Commission on 4 March 2025. See
                <a href="https://ec.europa.eu/commission/presscorner/detail/en/mex_25_680">European Commission news</a>.
                """,
                "https://ec.europa.eu/commission/presscorner/detail/en/mex_25_680",
            ),
            (
                "Old europa.eu/rapid format",
                """
                Ban glyphosate was submitted to the Commission on 6 October 2017. See
                <a href="http://europa.eu/rapid/press-release_MEX-17-3748_en.htm">press release</a>.
                """,
                "http://europa.eu/rapid/press-release_MEX-17-3748_en.htm",
            ),
            (
                "Case insensitive matching",
                """
                Initiative submitted. See
                <a href="https://ec.europa.eu/commission/presscorner/detail/en/mex_20_1000">PRESS RELEASE</a>.
                """,
                "https://ec.europa.eu/commission/presscorner/detail/en/mex_20_1000",
            ),
        ]

        for description, submission_text, expected_url in test_cases:
            html = self._create_submission_html(submission_text)
            soup = self.create_soup(html)
            url = self.parser.submission_data.extract_submission_news_url(soup)

            self.assert_url_matches(url, expected_url, f"Failed for: {description}")

        # Test Case: Multiple links - should skip initiative link and get press link
        html_multiple = self._create_submission_html(
            """
            <a href="https://citizens-initiative.europa.eu/initiatives/details/2018/000004_en">'End the Cage Age'</a>
            initiative was submitted to the Commission on 2 October 2020. See
            <a href="https://ec.europa.eu/commission/presscorner/detail/en/MEX_20_1810">press release</a>.
        """
        )

        soup = self.create_soup(html_multiple)
        url = self.parser.submission_data.extract_submission_news_url(soup)

        # Should get the presscorner URL, not the initiative URL
        self.assert_url_contains(
            url, "presscorner", "Should extract presscorner URL, not initiative URL"
        )
        self.assert_url_matches(
            url, "https://ec.europa.eu/commission/presscorner/detail/en/MEX_20_1810"
        )

        # Test Case: Missing news URL should raise ValueError
        html_no_news = self._create_submission_html(
            """
            <a href="https://citizens-initiative.europa.eu/initiatives/details/2020/000001_en">Initiative</a>
            was submitted but no press release link here.
        """
        )

        soup = self.create_soup(html_no_news)

        with pytest.raises(
            ValueError, match="No submission news URL found for initiative"
        ):
            self.parser.submission_data.extract_submission_news_url(soup)


class TestProceduralTimelineExtraction:
    """Tests for procedural timeline milestones extraction."""

    @classmethod
    def setup_class(cls):
        """Setup parser instance."""
        logger = ResponsesExtractorLogger().setup()
        cls.parser = ECIResponseHTMLParser(logger=logger)

    def test_commission_meeting_date(self):
        """Test extraction of Commission meeting date."""

        test_cases = [
            # Test case 1: Post-2020 format with Article 15 and month name
            (
                """
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>The initiative was submitted to the Commission on 4 March 2025.</p>
                <p>On 25 March 2025, the initiative organisers were given the opportunity to present 
                the objectives of their initiative in the meeting with Executive Vice-President 
                Raffaele Fitto and European Commission officials, in line with Article 15 of the 
                ECI Regulation. See the photo news.</p>
                <p>A public hearing took place at the European Parliament on 25 June 2025.</p>
                """,
                "2025-03-25",
                "post_2020_article_15",
                False,  # should not raise
            ),
            # Test case 2: Pre-2020 format with month name at end
            (
                """
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>Right2Water was submitted to the Commission on 20 December 2013.</p>
                <p>The organisers met with Commission Vice-President Maroš Šefčovič on 17 February 2014. 
                See press release.</p>
                <p>A public hearing took place at the European Parliament on 17 February 2014.</p>
                """,
                "2014-02-17",
                "pre_2020_month_name",
                False,
            ),
            # Test case 3: Slash format DD/MM/YYYY
            (
                """
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>One of us was submitted to the Commission on 28/02/2014.</p>
                <p>The organisers met with the Commissioner responsible for Research, Innovation and Science, 
                Ms Geoghegan-Quinn, and the Deputy Director-General responsible for Development and Cooperation, 
                Mr. Cornaro on 09/04/2014. See press release.</p>
                <p>A public hearing took place at the European Parliament on 10/04/2014.</p>
                """,
                "2014-04-09",
                "slash_format",
                False,
            ),
            # Test case 4: Multiple officials mentioned
            (
                """
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>The initiative was submitted on 6 October 2017.</p>
                <p>The organisers met with European Commission First Vice-President Frans Timmermans 
                and Commissioner for Health & Food Safety Vytenis Andriukaitis on 23/10/2017. 
                See press release.</p>
                """,
                "2017-10-23",
                "multiple_officials",
                False,
            ),
            # Test case 5: Recent format with European Commission officials
            (
                """
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>The initiative was submitted to the Commission on 14 June 2023.</p>
                <p>The organisers met with the European Commission Vice-President for Values and Transparency, 
                Věra Jourová and the Commissioner for Health and Food Safety, Stella Kyriakides on 20 July 2023. 
                See press announcement and photos.</p>
                """,
                "2023-07-20",
                "recent_format",
                False,
            ),
            # Test case 6: No commission meeting (raises ValueError)
            (
                """
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>The initiative was submitted to the Commission on 15 May 2024.</p>
                <p>A public hearing took place at the European Parliament on 20 June 2024.</p>
                """,
                None,
                "no_meeting",
                True,  # should_raise
            ),
            # Test case 7: No submission section (raises ValueError)
            (
                """
                <h2 id="Other-section">Other section</h2>
                <p>Some content here.</p>
                """,
                None,
                "no_section",
                True,  # should_raise
            ),
            # Test case 8: Long format with responsibilities
            (
                """
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>Stop Vivisection was submitted to the Commission on 3 March 2015.</p>
                <p>The organisers met with European Commission Vice-President Jyrki Katainen, 
                responsible for Jobs, Growth, Investment and Competitiveness and Director-General 
                Karl Falkenberg, responsible for DG Environment, on 11 May 2015. See press release.</p>
                """,
                "2015-05-11",
                "long_format_with_responsibilities",
                False,
            ),
        ]

        for html, expected, test_id, should_raise in test_cases:

            soup = BeautifulSoup(html, "html.parser")
            parser = ECIResponseHTMLParser(soup)
            parser.registration_number = "2024/000001"

            if should_raise:

                # Expect ValueError to be raised
                with pytest.raises(ValueError) as exc_info:
                    parser.procedural_timeline.extract_commission_meeting_date(soup)
                assert (
                    "commission meeting date" in str(exc_info.value).lower()
                ), f"Failed for test case: {test_id}"

            else:
                # Normal case - should return expected value
                result = parser.procedural_timeline.extract_commission_meeting_date(
                    soup
                )
                assert result == expected, f"Failed for test case: {test_id}"

    def test_submission_text(self):
        """Test extraction of submission section text."""

        test_cases = [
            # Test case 1: Simple single paragraph
            (
                """
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>The initiative was submitted to the Commission on 14 June 2023.</p>
                """,
                "The initiative was submitted to the Commission on 14 June 2023.",
                "single_paragraph",
            ),
            # Test case 2: Multiple paragraphs
            (
                """
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>The initiative was submitted on 14 June 2023, having gathered 1,502,319 statements of support.</p>
                <p>The organisers met with Commission officials on 20 July 2023.</p>
                <p>A public hearing took place on 10 October 2023.</p>
                """,
                "The initiative was submitted on 14 June 2023, having gathered 1,502,319 statements of support. The organisers met with Commission officials on 20 July 2023. A public hearing took place on 10 October 2023.",
                "multiple_paragraphs",
            ),
            # Test case 3: Paragraphs with links (space preservation)
            (
                """
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p><a href="/url">Right2Water</a> was the first <a href="/url2">European Citizens' Initiative</a> having gathered signatures.</p>
                """,
                "Right2Water was the first European Citizens' Initiative having gathered signatures.",
                "with_links",
            ),
            # Test case 4: Multiple spaces and newlines normalization
            (
                """
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>The initiative    was   submitted
                on 14 June  2023.</p>
                """,
                "The initiative was submitted on 14 June 2023.",
                "whitespace_normalization",
            ),
            # Test case 5: Stops at next section
            (
                """
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>First paragraph in submission section.</p>
                <p>Second paragraph in submission section.</p>
                <h2 id="Answer">Answer of the Commission</h2>
                <p>This should not be included.</p>
                """,
                "First paragraph in submission section. Second paragraph in submission section.",
                "stops_at_next_section",
            ),
            # Test case 6: Empty paragraphs ignored
            (
                """
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>First paragraph.</p>
                <p>   </p>
                <p>Third paragraph.</p>
                """,
                "First paragraph. Third paragraph.",
                "empty_paragraphs_ignored",
            ),
        ]

        for html, expected, test_id in test_cases:
            soup = BeautifulSoup(html, "html.parser")
            parser = ECIResponseHTMLParser(soup)
            parser.registration_number = "2024/000001"

            try:
                result = parser.submission_data.extract_submission_text(soup)
                assert result == expected, (
                    f"Failed for test case: {test_id}\n"
                    f"Expected: {expected}\n"
                    f"Got: {result}\n"
                    f"HTML:\n{html}"
                )
            except Exception as e:
                raise AssertionError(
                    f"Error in test case: {test_id}\n"
                    f"Expected: {expected}\n"
                    f"HTML:\n{html}\n"
                    f"Error: {str(e)}\n"
                ) from e

    def test_commission_officials_met(self):
        """Test extraction of Commission officials who met organizers."""

        test_cases = [
            # Test case 1: Simple format - single Vice-President
            (
                """
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>The organisers met with Commission Vice-President Maroš Šefčovič on 17 February 2014.</p>
                """,
                "Vice-President Maroš Šefčovič",
                "single_vice_president",
                False,
            ),
            # Test case 2: Post-2020 format with Executive Vice-President
            (
                """
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>  On 25 March 2025, the initiative organisers were given the opportunity to present the objectives of their initiative in the meeting with Executive Vice-President Raffaele Fitto and European Commission officials, in line with Article 15 of the ECI Regulation.</p>
                """,
                "Executive Vice-President Raffaele Fitto",
                "executive_vp_post_2020",
                False,
            ),
            # Test case 3: Multiple officials with portfolios
            (
                """
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>The organisers met with the European Commission Vice-President for Values and Transparency, Věra Jourová and the Commissioner for Health and Food Safety, Stella Kyriakides on 30 October 2020.</p>
                """,
                "Vice-President for Values and Transparency, Věra Jourová; Commissioner for Health and Food Safety, Stella Kyriakides",
                "multiple_with_portfolios",
                False,
            ),
            # Test case 4: Officials with responsibilities
            (
                """
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>The organisers met with European Commission Vice-President Jyrki Katainen, responsible for Jobs, Growth, Investment and Competitiveness and Director-General Karl Falkenberg, responsible for DG Environment, on 11 May 2015. See press release.</p>
                """,
                "Vice-President Jyrki Katainen, responsible for Jobs, Growth, Investment and Competitiveness; Director-General Karl Falkenberg, responsible for DG Environment",
                "with_responsibilities",
                False,
            ),
            # Test case 5: Slash date format
            (
                """
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>The organisers met with the Commissioner responsible for Research, Innovation and Science, 
                The organisers met with the Commissioner responsible for Research, Innovation and Science, Ms Geoghegan-Quinn, and the Deputy Director-General responsible for Development and Cooperation, Mr. Cornaro on 09/04/2014. See press release.</p>
                """,
                "the Commissioner responsible for Research, Innovation and Science, Ms Geoghegan-Quinn; Deputy Director-General responsible for Development and Cooperation, Mr. Cornaro",
                "slash_date_format",
                False,
            ),
            # Test case 6: First Vice-President (normalized)
            (
                """
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>The organisers met with European Commission First Vice-President Frans Timmermans and Commissioner for Health & Food Safety Vytenis Andriukaitis on 23/10/2017.</p>
                """,
                "Vice-President Frans Timmermans; Commissioner for Health & Food Safety Vytenis Andriukaitis",
                "first_vp_normalized",
                False,
            ),
            # Test case 7: Two Commissioners
            (
                """
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>The organisers met with the European Commission Vice-President for Values and Transparency, Věra Jourová and the Commissioner for Environment, Oceans and Fisheries, Virginijus Sinkevičius on 6 February 2023.</p>
                """,
                "Vice-President for Values and Transparency, Věra Jourová; Commissioner for Environment, Oceans and Fisheries, Virginijus Sinkevičius",
                "two_commissioners",
                False,
            ),
            (
                """
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>The initiative was submitted to the Commission on 15 May 2024.</p>
                <p>A public hearing took place at the European Parliament on 20 June 2024.</p>
                """,
                None,
                "no_meeting",
                True,
            ),
            # Test case 9: No submission section (raises error)
            (
                """
                <h2 id="Other-section">Other section</h2>
                <p>Some content here.</p>
                """,
                None,
                "no_section",
                True,
            ),
        ]

        for html, expected, test_id, should_raise in test_cases:
            soup = BeautifulSoup(html, "html.parser")
            parser = ECIResponseHTMLParser(soup)
            parser.registration_number = "2024/000001"

            if should_raise:
                # Expect ValueError to be raised
                with pytest.raises(ValueError) as exc_info:
                    parser.procedural_timeline.extract_commission_officials_met(soup)
                assert (
                    "commission official" in str(exc_info.value).lower()
                ), f"Failed for test case: {test_id}"
            else:
                # Normal case - should return expected value
                try:
                    result = (
                        parser.procedural_timeline.extract_commission_officials_met(
                            soup
                        )
                    )
                    assert result == expected, (
                        f"Failed for test case: {test_id}\n"
                        f"Expected: {expected}\n"
                        f"Got: {result}\n"
                        f"HTML:\n{html}"
                    )
                except Exception as e:
                    # Re-raise with HTML context
                    raise AssertionError(
                        f"Error in test case: {test_id}\n"
                        f"Expected: {expected}\n"
                        f"HTML:\n{html}\n"
                        f"Error: {str(e)}\n"
                    ) from e

    def test_parliament_hearing_date(self):
        """Test extraction of Parliament hearing date."""

        test_cases = [
            # Test case 1: Standard format with full month name
            (
                """
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>A public hearing took place at the European Parliament on 24 January 2023.</p>
                """,
                "2023-01-24",
                "standard_full_month",
                False,
            ),
            # Test case 2: Slash date format
            (
                """
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>A public hearing took place at the European Parliament on 17/02/2014.</p>
                """,
                "2014-02-17",
                "slash_date_format",
                False,
            ),
            # Test case 3: New format - "The presentation of this initiative..."
            (
                """
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>The presentation of this initiative in a public hearing at the European Parliament took place on 25 June 2025.</p>
                """,
                "2025-06-25",
                "new_presentation_format",
                False,
            ),
            # Test case 4: Single digit day
            (
                """
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>A public hearing took place at the European Parliament on 5 April 2023.</p>
                """,
                "2023-04-05",
                "single_digit_day",
                False,
            ),
            # Test case 5: Case insensitive month name
            (
                """
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>A public hearing took place at the European Parliament on 10 OCTOBER 2023.</p>
                """,
                "2023-10-10",
                "uppercase_month",
                False,
            ),
            # Test case 6: Mixed case
            (
                """
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>A public hearing took place at the European Parliament on 15 February 2020.</p>
                """,
                "2020-02-15",
                "mixed_case_month",
                False,
            ),
            # Test case 7: Slash format with new phrasing
            (
                """
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>The presentation of this initiative in a public hearing at the European Parliament took place on 11/05/2015.</p>
                """,
                "2015-05-11",
                "new_format_slash",
                False,
            ),
            # Test case 8: Multiple paragraphs, hearing in second paragraph
            (
                """
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>The initiative was submitted on 10 January 2020.</p>
                <p>A public hearing took place at the European Parliament on 15 October 2020.</p>
                """,
                "2020-10-15",
                "multiple_paragraphs",
                False,
            ),
            # Test case 9: No hearing date found (raises error)
            (
                """
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>The initiative was submitted to the Commission on 15 May 2024.</p>
                <p>The organisers met with Commission officials on 20 June 2024.</p>
                """,
                None,
                "no_hearing_date",
                True,
            ),
            # Test case 11: No submission section (raises error)
            (
                """
                <h2 id="Other-section">Other section</h2>
                <p>Some content here.</p>
                """,
                None,
                "no_section",
                True,
            ),
        ]

        for html, expected, test_id, should_raise in test_cases:
            soup = BeautifulSoup(html, "html.parser")
            parser = ECIResponseHTMLParser(soup)
            parser.registration_number = "2024/000001"

            if should_raise:
                # Expect ValueError to be raised
                with pytest.raises(ValueError) as exc_info:
                    parser.parliament_activity.extract_parliament_hearing_date(soup)
                assert (
                    "parliament hearing date" in str(exc_info.value).lower()
                ), f"Failed for test case: {test_id}"
            else:
                # Normal case - should return expected value
                try:
                    result = parser.parliament_activity.extract_parliament_hearing_date(
                        soup
                    )
                    assert result == expected, (
                        f"Failed for test case: {test_id}\n"
                        f"Expected: {expected}\n"
                        f"Got: {result}\n"
                        f"HTML:\n{html}"
                    )
                except Exception as e:
                    # Re-raise with HTML context
                    raise AssertionError(
                        f"Error in test case: {test_id}\n"
                        f"Expected: {expected}\n"
                        f"HTML:\n{html}\n"
                        f"Error: {str(e)}\n"
                    ) from e

    def test_parliament_hearing_video_urls(self):
        """Test extraction of Parliament hearing video URLs (as dict)."""

        test_cases = [
            # Test case 1: Link wrapping "public hearing" text
            (
                """
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>A <a href="http://www.europarl.europa.eu/news/en/news-room/20140210IPR35552/hearing">public hearing</a> took place at the European Parliament on 17 February 2014.</p>
                """,
                {
                    "public hearing": "http://www.europarl.europa.eu/news/en/news-room/20140210IPR35552/hearing"
                },
                "link_wrapping_public_hearing",
                False,
            ),
            # Test case 2: "See recording" pattern
            (
                """
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>A public hearing took place at the European Parliament on 24 January 2023. See <a href="https://multimedia.europarl.europa.eu/video/recording123">recording</a>.</p>
                """,
                {
                    "recording": "https://multimedia.europarl.europa.eu/video/recording123"
                },
                "see_recording_pattern",
                False,
            ),
            # Test case 3: "Watch the recording" pattern
            (
                """
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>The presentation of this initiative in a public hearing at the European Parliament took place on 25 June 2025. Watch the <a href="https://multimedia.europarl.europa.eu/video/recording456">recording</a>.</p>
                """,
                {
                    "recording": "https://multimedia.europarl.europa.eu/video/recording456"
                },
                "watch_recording_pattern",
                False,
            ),
            # Test case 4: Multiple links (recording + extracts)
            (
                """
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>A&nbsp;public hearing&nbsp;took place at the European Parliament on 25 May 2023. See
                <a href="https://multimedia.europarl.europa.eu/en/webstreaming/peti-envi-agri-committee-meeting_20230525-0900-COMMITTEE-ENVI-AGRI-PETI">recording</a>
                and
                <a href="https://multimedia.europarl.europa.eu/en/video/extracts_I241450">extracts</a>.</p>
                """,
                {
                    "recording": "https://multimedia.europarl.europa.eu/en/webstreaming/peti-envi-agri-committee-meeting_20230525-0900-COMMITTEE-ENVI-AGRI-PETI",
                    "extracts": "https://multimedia.europarl.europa.eu/en/video/extracts_I241450",
                },
                "multiple_links_recording_extracts",
                False,
            ),
            # Test case 5: Error when no relevant link
            (
                """
                <h2 id="Submission-and-examination">Submission and examination</h2>
                <p>The initiative was submitted to the Commission on 15 May 2024.</p>
                """,
                None,
                "no_links",
                True,
            ),
        ]

        for html, expected, test_id, should_raise in test_cases:
            soup = BeautifulSoup(html, "html.parser")
            parser = ECIResponseHTMLParser(soup)
            parser.registration_number = "2024/000001"

            if should_raise:
                with pytest.raises(ValueError):
                    parser.parliament_activity.extract_parliament_hearing_video_urls(
                        soup
                    )
            else:
                result = (
                    parser.parliament_activity.extract_parliament_hearing_video_urls(
                        soup
                    )
                )
                assert result == expected, (
                    f"Failed for test case: {test_id}\n"
                    f"Expected: {expected}\n"
                    f"Got: {result}\n"
                    f"HTML:\n{html}"
                )

    def test_plenary_debate_date(self):
        """Test extraction of plenary debate date."""

        # Test case 1: Standard format "initiative was debated at the European Parliament's plenary session on"
        html_1 = """
        <html>
            <h2 id="Submission-and-examination">Submission and examination</h2>
            <p>Some other text.</p>
            <p>
                The initiative was debated at the European Parliament's plenary session on 10 June 2021. In the
                <a href="https://example.com">resolution</a>
                adopted on the same day, the European Parliament expressed its support for the initiative.
            </p>
        </html>
        """
        soup_1 = BeautifulSoup(html_1, "html.parser")
        parser_1 = ECIResponseHTMLParser(soup_1)
        result_1 = parser_1.parliament_activity.extract_plenary_debate_date(soup_1)
        assert result_1 == "2021-06-10"

        # Test case 2: Alternative format "A debate on this initiative was held"
        html_2 = """
        <html>
            <h2 id="Submission-and-examination">Submission and examination</h2>
            <p>
                A debate on this initiative was held in the plenary session of the&nbsp;European Parliament on 10 July 2025. See the
                <a href="https://example.com">video recording</a>.
            </p>
        </html>
        """
        soup_2 = BeautifulSoup(html_2, "html.parser")
        parser_2 = ECIResponseHTMLParser(soup_2)
        result_2 = parser_2.parliament_activity.extract_plenary_debate_date(soup_2)
        assert result_2 == "2025-07-10"

        # Test case 3: With various month names
        html_3 = """
        <html>
            <h2 id="Submission-and-examination">Submission and examination</h2>
            <p>
                The initiative was debated at the European Parliament's plenary session on 16 March 2023.
                See <a href="https://example.com">recording</a>.
            </p>
        </html>
        """
        soup_3 = BeautifulSoup(html_3, "html.parser")
        parser_3 = ECIResponseHTMLParser(soup_3)
        result_3 = parser_3.parliament_activity.extract_plenary_debate_date(soup_3)
        assert result_3 == "2023-03-16"

        # Test case 4: Single digit day
        html_4 = """
        <html>
            <h2 id="Submission-and-examination">Submission and examination</h2>
            <p>
                The initiative was debated at the European Parliament's plenary session on 5 April 2023.
            </p>
        </html>
        """
        soup_4 = BeautifulSoup(html_4, "html.parser")
        parser_4 = ECIResponseHTMLParser(soup_4)
        result_4 = parser_4.parliament_activity.extract_plenary_debate_date(soup_4)
        assert result_4 == "2023-04-05"

        # Test case 5: No plenary debate date (older initiatives from 2017 and earlier)
        html_5 = """
        <html>
            <h2 id="Submission-and-examination">Submission and examination</h2>
            <p>
                The organisers met with Commission Vice-President on 17 February 2014.
                A public hearing took place at the European Parliament on 17 February 2014.
            </p>
        </html>
        """
        soup_5 = BeautifulSoup(html_5, "html.parser")
        parser_5 = ECIResponseHTMLParser(soup_5)
        result_5 = parser_5.parliament_activity.extract_plenary_debate_date(soup_5)
        assert result_5 is None

        # Test case 6: Slash format (if exists)
        html_6 = """
        <html>
            <h2 id="Submission-and-examination">Submission and examination</h2>
            <p>
                The initiative was debated at the European Parliament's plenary session on 14/12/2020.
            </p>
        </html>
        """
        soup_6 = BeautifulSoup(html_6, "html.parser")
        parser_6 = ECIResponseHTMLParser(soup_6)
        result_6 = parser_6.parliament_activity.extract_plenary_debate_date(soup_6)
        assert result_6 == "2020-12-14"

    def test_plenary_debate_video_urls(self):
        """Test extraction of plenary debate recording URLs."""

        # Test case 1: Single recording link
        html_1 = """
        <html>
            <h2 id="Submission-and-examination">Submission and examination</h2>
            <p>
                The initiative was debated at the European Parliament's plenary session on 11 May 2023. See
                <a href="https://multimedia.europarl.europa.eu/en/video/example">recording</a>.
            </p>
        </html>
        """
        soup_1 = BeautifulSoup(html_1, "html.parser")
        parser_1 = ECIResponseHTMLParser(soup_1)
        result_1 = parser_1.parliament_activity.extract_plenary_debate_video_urls(
            soup_1
        )
        expected_1 = json.dumps(
            {"recording": "https://multimedia.europarl.europa.eu/en/video/example"}
        )
        assert result_1 == expected_1

        # Test case 2: Multiple links (resolution and press release)
        html_2 = """
        <html>
            <h2 id="Submission-and-examination">Submission and examination</h2>
            <p>
                The initiative was debated at the European Parliament's plenary session on 10 June 2021. In the
                <a href="https://www.europarl.europa.eu/doceo/document/TA-9-2021-0295_EN.html">resolution</a>
                adopted on the same day, the European Parliament expressed its support for the initiative. See European Parliament's
                <a href="https://www.europarl.europa.eu/news/en/press-room/20210604IPR05532/meps-endorse-eu-citizens-call-for-gradual-end-to-caged-farming">press release</a>.
            </p>
        </html>
        """
        soup_2 = BeautifulSoup(html_2, "html.parser")
        parser_2 = ECIResponseHTMLParser(soup_2)
        result_2 = parser_2.parliament_activity.extract_plenary_debate_video_urls(
            soup_2
        )
        expected_2 = json.dumps(
            {
                "resolution": "https://www.europarl.europa.eu/doceo/document/TA-9-2021-0295_EN.html",
                "press release": "https://www.europarl.europa.eu/news/en/press-room/20210604IPR05532/meps-endorse-eu-citizens-call-for-gradual-end-to-caged-farming",
            }
        )
        assert result_2 == expected_2

        # Test case 3: Alternative format with video recording link
        html_3 = """
        <html>
            <h2 id="Submission-and-examination">Submission and examination</h2>
            <p>
                A debate on this initiative was held in the plenary session of the&nbsp;European Parliament on 10 July 2025. See the
                <a href="https://www.europarl.europa.eu/plenary/en/vod.html?mode=chapter">video recording</a>.
            </p>
        </html>
        """
        soup_3 = BeautifulSoup(html_3, "html.parser")
        parser_3 = ECIResponseHTMLParser(soup_3)
        result_3 = parser_3.parliament_activity.extract_plenary_debate_video_urls(
            soup_3
        )
        expected_3 = json.dumps(
            {
                "video recording": "https://www.europarl.europa.eu/plenary/en/vod.html?mode=chapter"
            }
        )
        assert result_3 == expected_3

        # Test case 4: Multiple links with "part 1 and part 2"
        html_4 = """
        <html>
            <h2 id="Submission-and-examination">Submission and examination</h2>
            <p>
                The initiative was debated at the European Parliament's plenary session on 19 October 2023. See recording (
                <a href="https://example.com/part1">part 1</a> and
                <a href="https://example.com/part2">part 2</a>).
            </p>
        </html>
        """
        soup_4 = BeautifulSoup(html_4, "html.parser")
        parser_4 = ECIResponseHTMLParser(soup_4)
        result_4 = parser_4.parliament_activity.extract_plenary_debate_video_urls(
            soup_4
        )
        expected_4 = json.dumps(
            {
                "part 1": "https://example.com/part1",
                "part 2": "https://example.com/part2",
            }
        )
        assert result_4 == expected_4

        # Test case 5: No links in debate paragraph
        html_5 = """
        <html>
            <h2 id="Submission-and-examination">Submission and examination</h2>
            <p>
                The initiative was debated at the European Parliament's plenary session on 14 December 2020.
            </p>
        </html>
        """
        soup_5 = BeautifulSoup(html_5, "html.parser")
        parser_5 = ECIResponseHTMLParser(soup_5)
        result_5 = parser_5.parliament_activity.extract_plenary_debate_video_urls(
            soup_5
        )
        assert result_5 is None

        # Test case 6: No plenary debate paragraph at all
        html_6 = """
        <html>
            <h2 id="Submission-and-examination">Submission and examination</h2>
            <p>
                The organisers met with Commission Vice-President on 17 February 2014.
            </p>
        </html>
        """
        soup_6 = BeautifulSoup(html_6, "html.parser")
        parser_6 = ECIResponseHTMLParser(soup_6)
        result_6 = parser_6.parliament_activity.extract_plenary_debate_video_urls(
            soup_6
        )
        assert result_6 is None

    def test_official_communication_adoption_date(self):
        """Test extraction of Commission communication date."""

        # Test case 1: Text format with full month name
        html_1 = """
        <html>
            <h2 id="Submission-and-examination">Submission and examination</h2>
            <p>
                The Commission adopted a Communication on 19 March 2014 setting out the actions it intends to take in response to the initiative.
                See <a href="https://example.com">press release</a>.
            </p>
        </html>
        """
        soup_1 = BeautifulSoup(html_1, "html.parser")
        parser_1 = ECIResponseHTMLParser(soup_1)
        result_1 = (
            parser_1.commission_response.extract_official_communication_adoption_date(
                soup_1
            )
        )
        assert result_1 == "2014-03-19"

        # Test case 2: Slash format
        html_2 = """
        <html>
            <h2 id="Submission-and-examination">Submission and examination</h2>
            <p>
                The Commission adopted a Communication on 12/12/2017 setting out the actions it intends to take in response to the initiative.
            </p>
        </html>
        """
        soup_2 = BeautifulSoup(html_2, "html.parser")
        parser_2 = ECIResponseHTMLParser(soup_2)
        result_2 = (
            parser_2.commission_response.extract_official_communication_adoption_date(
                soup_2
            )
        )
        assert result_2 == "2017-12-12"

        # Test case 3: Different month name
        html_3 = """
        <html>
            <h2 id="Submission-and-examination">Submission and examination</h2>
            <p>
                The Commission adopted a Communication on 30 June 2021 setting out the actions it intends to take in response to the initiative 'End the Cage Age'.
                See <a href="https://example.com">press release</a> and <a href="https://example.com">Questions & Answers</a>.
            </p>
        </html>
        """
        soup_3 = BeautifulSoup(html_3, "html.parser")
        parser_3 = ECIResponseHTMLParser(soup_3)
        result_3 = (
            parser_3.commission_response.extract_official_communication_adoption_date(
                soup_3
            )
        )
        assert result_3 == "2021-06-30"

        # Test case 4: Single digit day
        html_4 = """
        <html>
            <h2 id="Submission-and-examination">Submission and examination</h2>
            <p>
                The Commission adopted a Communication on 5 April 2023 setting out its response to the initiative.
            </p>
        </html>
        """
        soup_4 = BeautifulSoup(html_4, "html.parser")
        parser_4 = ECIResponseHTMLParser(soup_4)
        result_4 = (
            parser_4.commission_response.extract_official_communication_adoption_date(
                soup_4
            )
        )
        assert result_4 == "2023-04-05"

        # Test case 5: Recent format with "its response"
        html_5 = """
        <html>
            <h2 id="Submission-and-examination">Submission and examination</h2>
            <p>
                The Commission adopted a Communication on 3 September 2025 setting out its response to this initiative.
                See the <a href="https://example.com">Commission's news</a>.
            </p>
        </html>
        """
        soup_5 = BeautifulSoup(html_5, "html.parser")
        parser_5 = ECIResponseHTMLParser(soup_5)
        result_5 = (
            parser_5.commission_response.extract_official_communication_adoption_date(
                soup_5
            )
        )
        assert result_5 == "2025-09-03"

        # Test case 6: No Commission communication (some older initiatives)
        html_6 = """
        <html>
            <h2 id="Submission-and-examination">Submission and examination</h2>
            <p>
                The organisers met with Commission Vice-President on 17 February 2014.
                A public hearing took place at the European Parliament on 17 February 2014.
            </p>
        </html>
        """
        soup_6 = BeautifulSoup(html_6, "html.parser")
        parser_6 = ECIResponseHTMLParser(soup_6)
        result_6 = (
            parser_6.commission_response.extract_official_communication_adoption_date(
                soup_6
            )
        )
        assert result_6 is None

        # Test case 7: Alternative pattern - "Communication adopted on" (without "Commission")
        html_7 = """
        <html>
            <h2 id="Submission-and-examination">Submission and examination</h2>
            <p>
                <a href="https://citizens-initiative.europa.eu/initiatives/details/2012/000005_en">One of us</a>
                was submitted to the Commission on 28/02/2014 having gathered 1,721,626 statements of support.
            </p>
            <h2 id="Follow-up">Follow-up</h2>
            <p>
                In the Communication adopted on 28/05/2014, the Commission explains that it has decided not to submit a legislative proposal.
                See <a href="https://example.com">press release</a>.
            </p>
        </html>
        """
        soup_7 = BeautifulSoup(html_7, "html.parser")
        parser_7 = ECIResponseHTMLParser(soup_7)
        result_7 = (
            parser_7.commission_response.extract_official_communication_adoption_date(
                soup_7
            )
        )
        assert result_7 == "2014-05-28"

    def test_official_communication_document_urls(self):
        """Test extraction of Commission Communication PDF URL."""

        # Test case 1: Single press release link
        html_1 = """
        <html>
            <h2 id="Submission-and-examination">Submission and examination</h2>
            <p>
                The Commission adopted a Communication on 19 March 2014 setting out the actions it intends to take in response to the initiative.
                See <a href="http://europa.eu/rapid/press-release_IP-14-277_en.htm">press release</a>.
            </p>
        </html>
        """
        soup_1 = BeautifulSoup(html_1, "html.parser")
        parser_1 = ECIResponseHTMLParser(soup_1)
        result_1 = (
            parser_1.commission_response.extract_official_communication_document_urls(
                soup_1
            )
        )
        expected_1 = json.dumps(
            {"press release": "http://europa.eu/rapid/press-release_IP-14-277_en.htm"}
        )
        assert result_1 == expected_1

        # Test case 2: Multiple links (press release and Q&A)
        html_2 = """
        <html>
            <h2 id="Submission-and-examination">Submission and examination</h2>
            <p>
                The Commission adopted a Communication on 30 June 2021 setting out the actions it intends to take in response to the initiative 'End the Cage Age'.
                See <a href="https://ec.europa.eu/commission/presscorner/detail/en/ip_21_3297">press release</a> and 
                <a href="https://ec.europa.eu/commission/presscorner/detail/en/qanda_21_3298">Questions & Answers.</a>
            </p>
        </html>
        """
        soup_2 = BeautifulSoup(html_2, "html.parser")
        parser_2 = ECIResponseHTMLParser(soup_2)
        result_2 = (
            parser_2.commission_response.extract_official_communication_document_urls(
                soup_2
            )
        )
        expected_2 = json.dumps(
            {
                "press release": "https://ec.europa.eu/commission/presscorner/detail/en/ip_21_3297",
                "Questions & Answers.": "https://ec.europa.eu/commission/presscorner/detail/en/qanda_21_3298",
            }
        )
        assert result_2 == expected_2

        # Test case 3: Commission's news link
        html_3 = """
        <html>
            <h2 id="Submission-and-examination">Submission and examination</h2>
            <p>
                The Commission adopted a Communication on 3 September 2025 setting out its response to this initiative.
                See the <a href="https://ec.europa.eu/commission/presscorner/detail/en/mex_25_2018">Commission's news</a>.
            </p>
        </html>
        """
        soup_3 = BeautifulSoup(html_3, "html.parser")
        parser_3 = ECIResponseHTMLParser(soup_3)
        result_3 = (
            parser_3.commission_response.extract_official_communication_document_urls(
                soup_3
            )
        )
        expected_3 = json.dumps(
            {
                "Commission's news": "https://ec.europa.eu/commission/presscorner/detail/en/mex_25_2018"
            }
        )
        assert result_3 == expected_3

        # Test case 4: Filter out initiative name link (old URL format) - keep press release
        html_4 = """
        <html>
            <h2 id="Submission-and-examination">Submission and examination</h2>
            <p>
                The Commission adopted a Communication on 12/12/2017 setting out the actions it intends to take in response to the initiative
                <a href="http://ec.citizens-initiative.europa.eu/public/initiatives/successful/details/2017/000002">
                Ban glyphosate and protect people and the environment from toxic pesticides
                </a>. See
                <a href="http://europa.eu/rapid/press-release_IP-17-5191_en.htm">press release</a>.
            </p>
        </html>
        """
        soup_4 = BeautifulSoup(html_4, "html.parser")
        parser_4 = ECIResponseHTMLParser(soup_4)
        result_4 = (
            parser_4.commission_response.extract_official_communication_document_urls(
                soup_4
            )
        )
        expected_4 = json.dumps(
            {"press release": "http://europa.eu/rapid/press-release_IP-17-5191_en.htm"}
        )
        assert result_4 == expected_4

        # Test case 5: Filter out initiative name link (new URL format) - keep press release
        html_5 = """
        <html>
            <h2 id="Submission-and-examination">Submission and examination</h2>
            <p>
                The Commission adopted a Communication on 14 January 2021 setting out how existing and recently adopted EU legislation supports the different aspects of the
                <a href="https://citizens-initiative.europa.eu/initiatives/details/2017/000004_en">Minority SafePack</a>
                Initiative. The reply outlined further follow-up actions. See
                <a href="https://ec.europa.eu/commission/presscorner/detail/en/ip_21_81">press release</a>.
            </p>
        </html>
        """
        soup_5 = BeautifulSoup(html_5, "html.parser")
        parser_5 = ECIResponseHTMLParser(soup_5)
        result_5 = (
            parser_5.commission_response.extract_official_communication_document_urls(
                soup_5
            )
        )
        expected_5 = json.dumps(
            {
                "press release": "https://ec.europa.eu/commission/presscorner/detail/en/ip_21_81"
            }
        )
        assert result_5 == expected_5

        # Test case 6: Press release and questions and answers (lowercase)
        html_6 = """
        <html>
            <h2 id="Submission-and-examination">Submission and examination</h2>
            <p>
                The Commission adopted a Communication on 7 December 2023 setting out its response to the initiative 'Fur Free Europe'.
                See <a href="https://ec.europa.eu/commission/presscorner/detail/en/ip_23_6251">press release</a> and 
                <a href="https://ec.europa.eu/commission/presscorner/detail/en/QANDA_23_6254">questions and answers</a>.
            </p>
        </html>
        """
        soup_6 = BeautifulSoup(html_6, "html.parser")
        parser_6 = ECIResponseHTMLParser(soup_6)
        result_6 = (
            parser_6.commission_response.extract_official_communication_document_urls(
                soup_6
            )
        )
        expected_6 = json.dumps(
            {
                "press release": "https://ec.europa.eu/commission/presscorner/detail/en/ip_23_6251",
                "questions and answers": "https://ec.europa.eu/commission/presscorner/detail/en/QANDA_23_6254",
            }
        )
        assert result_6 == expected_6

        # Test case 7: No links in commission paragraph
        html_7 = """
        <html>
            <h2 id="Submission-and-examination">Submission and examination</h2>
            <p>
                The Commission adopted a Communication on 12/12/2017 setting out the actions it intends to take in response to the initiative.
            </p>
        </html>
        """
        soup_7 = BeautifulSoup(html_7, "html.parser")
        parser_7 = ECIResponseHTMLParser(soup_7)
        result_7 = (
            parser_7.commission_response.extract_official_communication_document_urls(
                soup_7
            )
        )
        assert result_7 is None

        # Test case 8: No commission communication paragraph
        html_8 = """
        <html>
            <h2 id="Submission-and-examination">Submission and examination</h2>
            <p>
                The organisers met with Commission Vice-President on 17 February 2014.
            </p>
        </html>
        """
        soup_8 = BeautifulSoup(html_8, "html.parser")
        parser_8 = ECIResponseHTMLParser(soup_8)
        result_8 = (
            parser_8.commission_response.extract_official_communication_document_urls(
                soup_8
            )
        )
        assert result_8 is None

        # Test case 9: Only initiative detail link (should return None after filtering)
        html_9 = """
        <html>
            <h2 id="Submission-and-examination">Submission and examination</h2>
            <p id="2012/000003">
                The Commission adopted a Communication on 19 March 2014 about
                <a href="https://citizens-initiative.europa.eu/initiatives/details/2012/000003_en">Right2Water</a>.
            </p>
        </html>
        """
        soup_9 = BeautifulSoup(html_9, "html.parser")
        parser_9 = ECIResponseHTMLParser(soup_9)
        result_9 = (
            parser_9.commission_response.extract_official_communication_document_urls(
                soup_9
            )
        )
        assert result_9 is None

        # Test case 10: Communication and Annex links (Strategy 2)
        html_10 = """
        <html>
            <h2 id="Submission-and-examination">Submission and examination</h2>
            <p id="2020/000001">
                The Commission adopted a Communication on 15 May 2023.
            </p>
            <p>
                <a href="https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=COM:2023:234:FIN">Communication</a>
                <a href="https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=COM:2023:234:FIN:ANNEX">Annex</a>
            </p>
        </html>
        """
        soup_10 = BeautifulSoup(html_10, "html.parser")
        parser_10 = ECIResponseHTMLParser(soup_10)
        result_10 = (
            parser_10.commission_response.extract_official_communication_document_urls(
                soup_10
            )
        )
        expected_10 = json.dumps(
            {
                "Communication": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=COM:2023:234:FIN",
                "Annex": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=COM:2023:234:FIN:ANNEX",
            }
        )
        assert result_10 == expected_10

        # Test case 11: Follow-up section (Strategy 3)
        html_11 = """
        <html>
            <h2 id="Submission-and-examination">Submission and examination</h2>
            <h2 id="Follow-up">Follow-up</h2>
            <p>
                Communication adopted on 25 October 2024.
                See <a href="https://ec.europa.eu/commission/presscorner/detail/en/ip_24_5432">press release</a>.
            </p>
        </html>
        """
        soup_11 = BeautifulSoup(html_11, "html.parser")
        parser_11 = ECIResponseHTMLParser(soup_11)
        result_11 = (
            parser_11.commission_response.extract_official_communication_document_urls(
                soup_11
            )
        )
        expected_11 = json.dumps(
            {
                "press release": "https://ec.europa.eu/commission/presscorner/detail/en/ip_24_5432"
            }
        )
        assert result_11 == expected_11

        # Test case 12: Duplicate URLs (should keep only first occurrence)
        html_12 = """
        <html>
            <h2 id="Submission-and-examination">Submission and examination</h2>
            <p id="2021/000001">
                The Commission adopted a Communication on 20 June 2024.
                See <a href="https://ec.europa.eu/commission/presscorner/detail/en/ip_24_1234">press release</a> and
                <a href="https://ec.europa.eu/commission/presscorner/detail/en/ip_24_1234">press info</a>.
            </p>
        </html>
        """
        soup_12 = BeautifulSoup(html_12, "html.parser")
        parser_12 = ECIResponseHTMLParser(soup_12)
        result_12 = (
            parser_12.commission_response.extract_official_communication_document_urls(
                soup_12
            )
        )
        expected_12 = json.dumps(
            {
                "press release": "https://ec.europa.eu/commission/presscorner/detail/en/ip_24_1234"
            }
        )
        assert result_12 == expected_12
