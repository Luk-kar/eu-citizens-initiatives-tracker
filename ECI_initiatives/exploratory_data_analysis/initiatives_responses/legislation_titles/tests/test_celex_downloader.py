"""
Tests for CELEX Downloader Module.
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch
from legislation_titles.celex_downloader import CelexTitleDownloader
from legislation_titles.errors import InvalidCelexError


class TestCelexTitleDownloader:
    """Test suite for CelexTitleDownloader class."""

    def test_init(self, sample_celex_ids):
        """Test initialization with CELEX IDs."""

        downloader = CelexTitleDownloader(sample_celex_ids)
        assert downloader.celex_ids == sample_celex_ids
        assert downloader.df_titles is None
        assert downloader.raw_json is None
        assert (
            downloader.SPARQL_ENDPOINT
            == "https://publications.europa.eu/webapi/rdf/sparql"
        )

    def test_create_batch_sparql_query_single_id(self):
        """Test SPARQL query generation with single CELEX ID."""

        celex_ids = ["32010L0063"]
        query = CelexTitleDownloader.create_batch_sparql_query(celex_ids)

        assert "PREFIX cdm:" in query
        assert "SELECT ?celex_id" in query
        assert '"celex:32010L0063"^^xsd:string' in query
        assert (
            'FILTER(datatype(?ISO_639_1) = euvoc:ISO_639_1 && str(?ISO_639_1) = "en")'
            in query
        )

    def test_create_batch_sparql_query_multiple_ids(self, sample_celex_ids):
        """Test SPARQL query generation with multiple CELEX IDs."""

        query = CelexTitleDownloader.create_batch_sparql_query(sample_celex_ids)

        for celex_id in sample_celex_ids:
            assert f'"celex:{celex_id}"^^xsd:string' in query

    def test_parse_celex_to_readable_format_directive(self):
        """Test parsing CELEX to readable format for Directives."""

        celex_id = "celex:32010L0063"
        legislation_type, document_number = (
            CelexTitleDownloader.parse_celex_to_readable_format(celex_id)
        )

        assert legislation_type == "Directive"
        assert document_number == "2010/63/EU"

    def test_parse_celex_to_readable_format_regulation(self):
        """Test parsing CELEX to readable format for Regulations."""

        celex_id = "32002R0178"
        legislation_type, document_number = (
            CelexTitleDownloader.parse_celex_to_readable_format(celex_id)
        )

        assert legislation_type == "Regulation"
        assert document_number == "178/2002"

    def test_parse_celex_to_readable_format_decision(self):
        """Test parsing CELEX to readable format for Decisions."""

        celex_id = "32020D1234"
        legislation_type, document_number = (
            CelexTitleDownloader.parse_celex_to_readable_format(celex_id)
        )

        assert legislation_type == "Decision"
        assert document_number == "1234/2020"

    def test_parse_celex_to_readable_format_commission_proposal(self):
        """Test parsing CELEX to readable format for Commission Proposals."""

        celex_id = "52018PC0179"
        legislation_type, document_number = (
            CelexTitleDownloader.parse_celex_to_readable_format(celex_id)
        )

        assert legislation_type == "Proposal (Commission)"
        assert document_number == "COM(2018) 179"

    def test_parse_celex_to_readable_format_commission_communication(self):
        """Test parsing CELEX to readable format for Commission Communications."""

        celex_id = "52020DC0015"
        legislation_type, document_number = (
            CelexTitleDownloader.parse_celex_to_readable_format(celex_id)
        )

        assert legislation_type == "Communication (Commission)"
        assert document_number == "COM(2020) 15"

    def test_parse_celex_to_readable_format_court_judgment(self):
        """Test parsing CELEX to readable format for Court Judgments."""

        celex_id = "62023CJ0026"
        legislation_type, document_number = (
            CelexTitleDownloader.parse_celex_to_readable_format(celex_id)
        )

        assert legislation_type == "Court of Justice Judgment"
        assert document_number == "C-26/23"

    def test_invalid_sector_raises_error(self):
        """Test that invalid sector raises error."""

        celex_id = "Z2020DC1234"

        with pytest.raises(InvalidCelexError, match="Invalid sector"):
            CelexTitleDownloader.parse_celex_to_readable_format(celex_id)

    def test_invalid_sector_9_type_raises_error(self):
        """Test that invalid Sector 9 document type raises error."""

        celex_id = "92020X1234"

        with pytest.raises(InvalidCelexError, match="Sector 9 must use"):
            CelexTitleDownloader.parse_celex_to_readable_format(celex_id)

    def test_valid_sector_9_celex(self):
        """Test valid Sector 9 CELEX (Parliamentary question)."""

        celex_id = "92020E1234"
        legislation_type, doc_num = CelexTitleDownloader.parse_celex_to_readable_format(
            celex_id
        )
        assert legislation_type == "European Parliament - Written Questions"
        assert doc_num == "E-1234/2020"

    def test_celex_too_short_raises_error(self):
        """Test that too-short CELEX raises error."""

        celex_id = "320"

        with pytest.raises(InvalidCelexError, match="too short"):
            CelexTitleDownloader.parse_celex_to_readable_format(celex_id)

    def test_empty_celex_raises_error(self):
        """Test that empty CELEX raises error."""

        celex_id = ""

        with pytest.raises(InvalidCelexError, match="empty"):
            CelexTitleDownloader.parse_celex_to_readable_format(celex_id)

    @patch("celex_downloader.requests.get")
    def test_download_titles_success(self, mock_get, mock_sparql_response):
        """Test successful title download."""

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_sparql_response
        mock_get.return_value = mock_response

        downloader = CelexTitleDownloader(["32010L0063", "32002R0178"])
        df, raw_json = downloader.download_titles()

        assert not df.empty
        assert len(df) == 2
        assert "celex_id" in df.columns
        assert "title" in df.columns
        assert "legislation_type" in df.columns
        assert "document_number" in df.columns
        assert raw_json == mock_sparql_response

    @patch("celex_downloader.requests.get")
    def test_download_titles_http_error(self, mock_get):
        """Test download with HTTP error response."""

        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_get.return_value = mock_response

        downloader = CelexTitleDownloader(["32010L0063"])
        df, raw_json = downloader.download_titles()

        assert df.empty
        assert raw_json is None

    @patch("celex_downloader.requests.get")
    def test_download_titles_invalid_json(self, mock_get):
        """Test download with invalid JSON response."""

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = Exception("Invalid JSON")
        mock_response.text = "Invalid response"
        mock_get.return_value = mock_response

        downloader = CelexTitleDownloader(["32010L0063"])
        df, raw_json = downloader.download_titles()

        assert df.empty
        assert raw_json is None

    def test_download_titles_empty_celex_ids(self):
        """Test download with empty CELEX ID list."""

        downloader = CelexTitleDownloader([])
        df, raw_json = downloader.download_titles()

        assert df.empty
        assert raw_json is None

    @patch("celex_downloader.requests.get")
    def test_download_titles_stores_results(self, mock_get, mock_sparql_response):
        """Test that download stores results in instance variables."""

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_sparql_response
        mock_get.return_value = mock_response

        downloader = CelexTitleDownloader(["32010L0063"])
        df, raw_json = downloader.download_titles()

        assert downloader.df_titles is not None
        assert downloader.raw_json is not None
        pd.testing.assert_frame_equal(downloader.df_titles, df)
        assert downloader.raw_json == raw_json

    @patch("celex_downloader.requests.get")
    def test_download_titles_request_parameters(self, mock_get, mock_sparql_response):
        """Test that correct parameters are sent to SPARQL endpoint."""

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_sparql_response
        mock_get.return_value = mock_response

        downloader = CelexTitleDownloader(["32010L0063"])
        downloader.download_titles()

        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert call_args[0][0] == downloader.SPARQL_ENDPOINT
        assert "query" in call_args[1]["params"]
        assert call_args[1]["params"]["format"] == "application/sparql-results+json"


class TestCelexUnsupportedSectors:
    """Test valid but unimplemented sectors raise appropriate errors."""

    def test_parse_celex_sector_0_not_implemented(self):
        """Test that Sector 0 (Consolidated acts) raises not implemented error."""
        # Sector 0 format: 0YYYYXNNNN-YYYYMMDD (has date suffix, won't match pattern)
        celex_id = "02010L0063"

        # This will raise "Unsupported CELEX format" not "not yet implemented"
        with pytest.raises(
            InvalidCelexError, match="Sector 0 is valid but not yet implemented"
        ):
            CelexTitleDownloader.parse_celex_to_readable_format(celex_id)

    def test_parse_celex_sector_1_not_implemented(self):
        """Test that Sector 1 (Treaties) raises not implemented error."""
        # Valid format: 1YYYYXNNNN (X=treaty type, NNNN must be 4+ digits)
        celex_id = "12012M0001"  # Changed to 4 digits

        with pytest.raises(
            InvalidCelexError, match="Sector 1 is valid but not yet implemented"
        ):
            CelexTitleDownloader.parse_celex_to_readable_format(celex_id)

    def test_parse_celex_sector_2_not_implemented(self):
        """Test that Sector 2 (International agreements) raises not implemented error."""
        # Valid format: 2YYYYXNNNN
        celex_id = "22020A1234"  # Changed to 4 digits

        with pytest.raises(
            InvalidCelexError, match="Sector 2 is valid but not yet implemented"
        ):
            CelexTitleDownloader.parse_celex_to_readable_format(celex_id)

    def test_parse_celex_sector_4_not_implemented(self):
        """Test that Sector 4 (Complementary legislation) raises not implemented error."""
        # Valid format: 4YYYYXNNNN
        celex_id = "42020R0001"  # Should work if properly formatted

        with pytest.raises(
            InvalidCelexError, match="Sector 4 is valid but not yet implemented"
        ):
            CelexTitleDownloader.parse_celex_to_readable_format(celex_id)

    def test_parse_celex_sector_7_not_implemented(self):
        """Test that Sector 7 (National transposition) raises not implemented error."""
        celex_id = "72020L1234"

        with pytest.raises(
            InvalidCelexError, match="Sector 7 is valid but not yet implemented"
        ):
            CelexTitleDownloader.parse_celex_to_readable_format(celex_id)

    def test_parse_celex_sector_8_not_implemented(self):
        """Test that Sector 8 (National case-law) raises not implemented error."""
        celex_id = "82020C1234"

        with pytest.raises(
            InvalidCelexError, match="Sector 8 is valid but not yet implemented"
        ):
            CelexTitleDownloader.parse_celex_to_readable_format(celex_id)
