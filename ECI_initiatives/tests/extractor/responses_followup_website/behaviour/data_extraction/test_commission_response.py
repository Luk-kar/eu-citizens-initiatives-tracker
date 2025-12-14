"""
Behavioural tests for Commission response content extraction.

This module tests extraction of:
- Commission answer text
- Official communication document URLs
- Follow-up dedicated website URLs
"""

# Third party
import pytest
from bs4 import BeautifulSoup

# Local
from ECI_initiatives.extractor.responses_followup_website.parser.extractors import (
    FollowupWebsiteExtractor,
)


class TestCommissionResponseContent:
    """Tests for Commission response content extraction."""

    @pytest.fixture
    def html_with_commission_response_paragraphs(self):
        """HTML with Commission response containing multiple paragraphs."""
        return """
        <div>
            <div class="ecl">
                <h2 class="ecl-u-type-heading-2" id="response-of-the-commission">
                    Response of the Commission
                </h2>
            </div>
            <div class="ecl">
                <p>
                    On 30 June 2021, the Commission decided to positively respond to the ECI.
                    <a href="https://ec.europa.eu/transparency/documents-register/detail?ref=C(2021)4747&amp;lang=en">
                        In its communication
                    </a>
                    <button aria-controls="laco-modal" class="wt-unselected wt-laco wt-laco--button wt-offprint" title="Search for available translations" type="button">
                        <svg aria-hidden="true" focusable="false" height="20" viewBox="0 0 82.205 82.205" width="20">
                            ircle cx="40.98" cy="41.103" fill="#fff" r="22.347"></circle>
                        </svg>
                    </button>
                    the Commission sets out plans for a legislative proposal.
                </p>
                <p>
                    The Commission has asked the European Food Safety Authority (EFSA) to complement the existing scientific evidence.
                </p>
            </div>
        </div>
        """

    @pytest.fixture
    def html_with_commission_response_and_list(self):
        """HTML with Commission response containing paragraphs and lists."""
        return """
        <div>
            <div class="ecl">
                <h2 class="ecl-u-type-heading-2" id="response-of-the-commission">
                    Response of the Commission
                </h2>
            </div>
            <div class="ecl">
                <p>
                    The Commission published the response to this initiative on 7 December 2023 in the form of
                    <a href="https://citizens-initiative.europa.eu/initiatives/details/2022/000002_en">
                        a Communication
                    </a>
                    <button aria-controls="laco-modal" class="wt-unselected" type="button">
                        <svg></svg>
                    </button>
                    , setting out the Commission's legal and political conclusions on the initiative.
                </p>
                <p>
                    The Commission's actions will concern:
                </p>
                <ul>
                    <li>The welfare of animals kept for fur production;</li>
                    <li>
                        The
                        <a href="https://health.ec.europa.eu/one-health_en">
                            One health dimension;
                        </a>
                        <button type="button">
                            <svg></svg>
                        </button>
                    </li>
                    <li>the environmental aspects linked to Invasive alien species; and</li>
                    <li>labelling aspects related to the animals kept for fur production.</li>
                </ul>
                <p>
                    The European Commission also mandated EFSA to give an independent view.
                </p>
            </div>
        </div>
        """

    @pytest.fixture
    def html_without_commission_response(self):
        """HTML without Commission response section."""
        return """
        <div>
            <div class="ecl">
                <h2 class="ecl-u-type-heading-2" id="some-other-section">
                    Some Other Section
                </h2>
            </div>
            <div class="ecl">
                <p>This is not the Commission response section.</p>
            </div>
        </div>
        """

    @pytest.fixture
    def html_with_empty_commission_response(self):
        """HTML with Commission response header but no content."""
        return """
        <div>
            <div class="ecl">
                <h2 class="ecl-u-type-heading-2" id="response-of-the-commission">
                    Response of the Commission
                </h2>
            </div>
        </div>
        """

    @pytest.fixture
    def html_with_multiple_links(self):
        """HTML with multiple document URLs in Commission response."""
        return """
        <div>
            <div class="ecl">
                <h2 class="ecl-u-type-heading-2" id="response-of-the-commission">
                    Response of the Commission
                </h2>
            </div>
            <div class="ecl">
                <p>
                    The Commission published
                    <a href="https://ec.europa.eu/doc1.pdf">Communication 1</a>
                    and
                    <a href="https://ec.europa.eu/doc2.pdf">Communication 2</a>
                    on this matter.
                </p>
            </div>
        </div>
        """

    def test_extract_commission_answer_text_with_paragraphs(
        self, html_with_commission_response_paragraphs
    ):
        """Test extraction of Commission answer text with multiple paragraphs."""
        extractor = FollowupWebsiteExtractor(html_with_commission_response_paragraphs)

        result = extractor.extract_commission_answer_text()

        assert result != ""
        assert "30 June 2021" in result
        assert "positively respond to the ECI" in result
        assert (
            "[In its communication](https://ec.europa.eu/transparency/documents-register/detail?ref=C(2021)4747&lang=en)"
            in result
        )
        assert "European Food Safety Authority (EFSA)" in result
        # Ensure buttons and SVG are not in output
        assert "button" not in result.lower()
        assert "svg" not in result.lower()

    def test_extract_commission_answer_text_with_list(
        self, html_with_commission_response_and_list
    ):
        """Test extraction includes list items from Commission response."""
        extractor = FollowupWebsiteExtractor(html_with_commission_response_and_list)

        result = extractor.extract_commission_answer_text()

        assert result != ""
        assert "7 December 2023" in result
        assert (
            "[a Communication](https://citizens-initiative.europa.eu/initiatives/details/2022/000002_en)"
            in result
        )
        assert "welfare of animals kept for fur production" in result
        assert (
            "[One health dimension;](https://health.ec.europa.eu/one-health_en)"
            in result
        )
        assert "environmental aspects linked to Invasive alien species" in result
        assert "labelling aspects" in result
        assert "European Commission also mandated EFSA" in result

    def test_extract_commission_answer_text_missing_section(
        self, html_without_commission_response
    ):
        """Test returns empty string when Commission response section not found."""
        extractor = FollowupWebsiteExtractor(html_without_commission_response)

        result = extractor.extract_commission_answer_text()

        assert result == ""

    def test_extract_commission_answer_text_empty_content(
        self, html_with_empty_commission_response
    ):
        """Test returns empty string when Commission response has no content."""
        extractor = FollowupWebsiteExtractor(html_with_empty_commission_response)

        result = extractor.extract_commission_answer_text()

        assert result == ""

    def test_extract_commission_answer_text_preserves_multiple_links(
        self, html_with_multiple_links
    ):
        """Test that multiple links are preserved in markdown format."""
        extractor = FollowupWebsiteExtractor(html_with_multiple_links)

        result = extractor.extract_commission_answer_text()

        assert "[Communication 1](https://ec.europa.eu/doc1.pdf)" in result
        assert "[Communication 2](https://ec.europa.eu/doc2.pdf)" in result

    def test_extract_commission_answer_text_no_extra_whitespace(
        self, html_with_commission_response_paragraphs
    ):
        """Test that excessive whitespace is cleaned up."""

        extractor = FollowupWebsiteExtractor(html_with_commission_response_paragraphs)

        result = extractor.extract_commission_answer_text()

        # Should not have multiple consecutive spaces
        assert "  " not in result
        # Should not have excessive newlines
        assert "\n\n\n" not in result

    def test_extract_official_communication_document_urls_transparency_register(self):
        """Test extraction of EC transparency register Communication URLs."""

        html = """
        <div>
            <div class="ecl">
                <h2 id="response-of-the-commission">Response of the Commission</h2>
            </div>
            <div class="ecl">
                <p>
                    See
                    <a href="https://ec.europa.eu/transparency/documents-register/detail?ref=C(2021)4747">
                        Communication
                    </a>
                    for details.
                </p>
            </div>
        </div>
        """
        extractor = FollowupWebsiteExtractor(html)

        result = extractor.extract_official_communication_document_urls()

        assert result is not None
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["text"] == "Communication"
        assert (
            result[0]["url"]
            == "https://ec.europa.eu/transparency/documents-register/detail?ref=C(2021)4747"
        )

    def test_extract_official_communication_document_urls_with_annex(self):
        """Test extraction includes Annex documents."""

        html = """
        <div>
            <p>
                Read the
                <a href="https://ec.europa.eu/transparency/documents-register/detail?ref=C(2021)4747">
                    Communication
                </a>
                and its
                <a href="https://ec.europa.eu/transparency/documents-register/detail?ref=C(2021)4747-annex">
                    Annex
                </a>
                .
            </p>
        </div>
        """
        extractor = FollowupWebsiteExtractor(html)

        result = extractor.extract_official_communication_document_urls()

        assert result is not None
        assert len(result) == 2

        # Check that both documents are present
        texts = [item["text"] for item in result]
        assert "Communication" in texts
        assert "Annex" in texts

    def test_extract_official_communication_document_urls_presscorner(self):
        """Test extraction of presscorner press release URLs."""

        html = """
        <div>
            <p>
                See
                <a href="https://ec.europa.eu/commission/presscorner/detail/en/ip_21_3297">
                    Press release
                </a>
                about this Communication.
            </p>
        </div>
        """
        extractor = FollowupWebsiteExtractor(html)

        result = extractor.extract_official_communication_document_urls()

        assert result is not None
        texts = [item["text"] for item in result]
        assert "Press release" in texts

        # Verify URL
        press_release_item = next(
            item for item in result if item["text"] == "Press release"
        )
        assert (
            press_release_item["url"]
            == "https://ec.europa.eu/commission/presscorner/detail/en/ip_21_3297"
        )

    def test_extract_official_communication_document_urls_multiple_sources(self):
        """Test extraction from multiple URL patterns (transparency + presscorner)."""

        html = """
        <div>
            <p>
                The Commission published
                <a href="https://ec.europa.eu/transparency/documents-register/detail?ref=C(2023)5000">
                    a Communication
                </a>
                and issued a
                <a href="https://ec.europa.eu/commission/presscorner/detail/en/ip_23_1234">
                    press release
                </a>
                .
            </p>
        </div>
        """

        extractor = FollowupWebsiteExtractor(html)

        result = extractor.extract_official_communication_document_urls()

        assert result is not None
        assert len(result) == 2

        texts = [item["text"] for item in result]
        assert "a Communication" in texts
        assert "press release" in texts

        def test_extract_official_communication_document_urls_excludes_initiative_page(
            self,
        ):
            """Test that initiative overview pages are filtered out."""
            html = """
            <div>
                <p>
                    Read
                    <a href="https://citizens-initiative.europa.eu/initiatives/details/2022/000002_en">
                        a Communication
                    </a>
                    for more details.
                </p>
            </div>
            """
            extractor = FollowupWebsiteExtractor(html)

            result = extractor.extract_official_communication_document_urls()

            # Should be filtered out by exclusion pattern
            assert result is None or "a Communication" not in result

    def test_extract_official_communication_document_urls_duplicate_removal(self):
        """Test that duplicate URLs are removed."""

        html = """
        <div>
            <p>
                See the
                <a href="https://ec.europa.eu/transparency/documents-register/detail?ref=C(2021)4747">
                    Communication
                </a>
                and refer to the
                <a href="https://ec.europa.eu/transparency/documents-register/detail?ref=C(2021)4747">
                    same document
                </a>
                again.
            </p>
        </div>
        """
        extractor = FollowupWebsiteExtractor(html)

        result = extractor.extract_official_communication_document_urls()

        assert result is not None

        # Should have only one entry for the URL (first text wins)
        assert len(result) == 1
        assert result[0]["text"] == "Communication", (
            f"Key 'same document' not found in result. "
            f"Available keys: {[item['text'] for item in result]}, "
            f"Full result: {result}"
        )

    def test_extract_official_communication_document_urls_case_insensitive(self):
        """Test that 'communication', 'Communication', 'COMMUNICATION' all work."""
        html = """
        <div>
            <p>
                <a href="https://ec.europa.eu/transparency/documents-register/detail?ref=C(2021)1">
                    communication
                </a>
                <a href="https://ec.europa.eu/transparency/documents-register/detail?ref=C(2021)2">
                    Communication
                </a>
                <a href="https://ec.europa.eu/transparency/documents-register/detail?ref=C(2021)3">
                    COMMUNICATION
                </a>
            </p>
        </div>
        """
        extractor = FollowupWebsiteExtractor(html)

        result = extractor.extract_official_communication_document_urls()

        assert result is not None
        assert len(result) == 3

    def test_extract_official_communication_document_urls_annexes_plural(self):
        """Test extraction of 'Annexes' (plural form)."""
        html = """
        <div>
            <p>
                See the
                <a href="https://ec.europa.eu/transparency/documents-register/detail?ref=C(2021)4747-annexes">
                    Annexes
                </a>
                for supporting documents.
            </p>
        </div>
        """
        extractor = FollowupWebsiteExtractor(html)

        result = extractor.extract_official_communication_document_urls()

        assert result is not None
        texts = [item["text"] for item in result]
        assert "Annexes" in texts

    def test_extract_official_communication_document_urls_no_matches(self):
        """Test returns None when no Communication links found."""
        html = """
        <div>
            <p>
                This page has
                <a href="https://example.com">
                    no official documents
                </a>
                at all.
            </p>
        </div>
        """
        extractor = FollowupWebsiteExtractor(html)

        result = extractor.extract_official_communication_document_urls()

        assert result is None

    def test_extract_official_communication_document_urls_empty_html(self):
        """Test returns None for empty HTML."""
        extractor = FollowupWebsiteExtractor("")

        result = extractor.extract_official_communication_document_urls()

        assert result is None

    def test_extract_official_communication_document_urls_mixed_content(self):
        """Test extraction from realistic mixed content with various link types."""
        html = """
        <div>
            <h2 id="response-of-the-commission">Response of the Commission</h2>
            <p>
                The Commission published
                <a href="https://ec.europa.eu/transparency/documents-register/detail?ref=C(2023)5000&lang=en">
                    In its communication
                </a>
                the Commission sets out plans.
            </p>
            <p>
                See also the
                <a href="https://ec.europa.eu/commission/presscorner/detail/en/qanda_23_6254">
                    Questions and Answers
                </a>
                press release.
            </p>
            <p>
                Visit the
                <a href="https://example.com/organizers-page">
                    organisers' website
                </a>
                for more information.
            </p>
        </div>
        """
        extractor = FollowupWebsiteExtractor(html)

        result = extractor.extract_official_communication_document_urls()

        assert result is not None
        texts = [item["text"] for item in result]
        assert "In its communication" in texts
        assert "Questions and Answers" in texts
        assert "organisers' website" not in texts  # Should not match
        assert len(result) == 2
