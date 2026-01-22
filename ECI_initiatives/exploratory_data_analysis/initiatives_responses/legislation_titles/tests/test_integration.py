"""
Integration tests for the complete legislation title fetching workflow.

These tests verify end-to-end functionality but use mocked external dependencies
by default. Real API tests are marked with @pytest.mark.external_api.
"""

import pytest
import pandas as pd
from unittest.mock import patch, Mock
from legislation_titles.legislation_fetcher import LegislationTitleFetcher


@pytest.mark.external_api
def test_real_eurlex_api_integration():
    """
    Integration test with REAL EUR-Lex SPARQL endpoint.

    This test makes actual HTTP requests to:
    https://publications.europa.eu/webapi/rdf/sparql

    WARNING: This test:
    - Requires internet connection
    - Takes ~5-10 seconds to complete
    - May fail due to EUR-Lex downtime or rate limiting
    - Should NOT be run in CI/CD pipelines

    Run with: pytest -v -m external_api
    Skip with: pytest -v -m "not external_api"
    """
    import json

    # Real CELEX IDs from actual ECI references (as JSON strings)
    sample_references = [
        json.dumps({"CELEX": ["32010L0063"], "Directive": ["2010/63/EU"]}),
        json.dumps(
            {
                "CELEX": ["52020DC0015"],
                "official_journal": {"legislation": ["2020, 381"]},
            }
        ),
    ]

    # Initialize fetcher with real references
    fetcher = LegislationTitleFetcher(sample_references)

    # Execute real API call
    df_titles = fetcher.fetch_titles(verbose=True)

    # Verify results
    assert not df_titles.empty, "Should retrieve titles from EUR-Lex"
    assert len(df_titles) >= 2, "Should fetch at least 2 titles"
    assert "celex_id" in df_titles.columns
    assert "title" in df_titles.columns
    assert "legislation_type" in df_titles.columns

    # Verify specific CELEX IDs were fetched
    celex_ids = df_titles["celex_id"].tolist()
    assert "32010L0063" in celex_ids
    assert "52020DC0015" in celex_ids

    # Verify titles are in English and non-empty
    for title in df_titles["title"]:
        assert isinstance(title, str)
        assert len(title) > 10, f"Title too short: {title}"

    # Verify legislation types were parsed correctly
    types = df_titles["legislation_type"].tolist()
    assert "Directive" in types or "Communication (Commission)" in types

    # Verify raw JSON was stored
    assert fetcher.downloader is not None
    assert fetcher.downloader.raw_json is not None
    assert "results" in fetcher.downloader.raw_json

    print("\n✓ Successfully fetched real data from EUR-Lex")
    print(f"✓ Retrieved {len(df_titles)} titles")
    print(df_titles[["celex_id", "legislation_type", "title"]].to_string())


class TestIntegration:
    """Integration test suite for end-to-end workflows."""

    @patch("celex_downloader.requests.get")
    def test_complete_workflow_with_real_classes(
        self, mock_get, sample_legislation_references, mock_sparql_response
    ):
        """Test complete workflow from references to titles using real classes."""
        # Mock only the HTTP request
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_sparql_response
        mock_get.return_value = mock_response

        # Use real classes
        fetcher = LegislationTitleFetcher(sample_legislation_references)
        df, metadata = fetcher.fetch_titles(verbose=False)

        # Verify translator extracted CELEX IDs
        assert len(metadata["celex_ids"]) > 0

        # Verify downloader was created
        assert fetcher.downloader is not None

        # Verify results structure
        assert "celex_ids" in metadata
        assert "unresolved" in metadata
        assert "total_results" in metadata

    @patch("celex_downloader.requests.get")
    def test_workflow_with_directives_and_regulations(
        self, mock_get, mock_sparql_response
    ):
        """Test workflow converting Directives and Regulations to CELEX."""
        references = [
            '{"Directive": ["2010/63/EU"]}',
            '{"Regulation": ["178/2002"]}',
        ]

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_sparql_response
        mock_get.return_value = mock_response

        fetcher = LegislationTitleFetcher(references)
        df, metadata = fetcher.fetch_titles(verbose=False)

        # Should have converted both to CELEX
        assert "32010L0063" in metadata["celex_ids"]
        assert "32002R0178" in metadata["celex_ids"]

    @patch("celex_downloader.requests.get")
    def test_workflow_with_mixed_valid_invalid(self, mock_get, mock_sparql_response):
        """Test workflow with mix of valid and invalid references."""
        references = [
            '{"CELEX": ["32010L0063"]}',
            '{"Article": ["15"]}',  # Should be unresolved
            None,
            '{"Directive": ["invalid-format"]}',  # Should be unresolved
        ]

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_sparql_response
        mock_get.return_value = mock_response

        fetcher = LegislationTitleFetcher(references)
        df, metadata = fetcher.fetch_titles(verbose=False)

        # Should have valid CELEX
        assert "32010L0063" in metadata["celex_ids"]

        # Should have unresolved references
        assert len(metadata["unresolved"]) > 0

    @patch("celex_downloader.requests.get")
    def test_workflow_api_failure(self, mock_get):
        """Test workflow when API request fails."""
        references = ['{"CELEX": ["32010L0063"]}']

        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Server Error"
        mock_get.return_value = mock_response

        fetcher = LegislationTitleFetcher(references)
        df, metadata = fetcher.fetch_titles(verbose=False)

        # Should handle error gracefully
        assert df.empty
        assert metadata["total_results"] == 0

    @patch("celex_downloader.requests.get")
    @patch("builtins.open", create=True)
    def test_complete_workflow_with_save(
        self, mock_open, mock_get, sample_legislation_references, mock_sparql_response
    ):
        """Test complete workflow including saving results."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_sparql_response
        mock_get.return_value = mock_response

        fetcher = LegislationTitleFetcher(sample_legislation_references)
        df, metadata = fetcher.fetch_titles(verbose=False)

        # Mock file operations
        with patch.object(df, "to_csv") as mock_to_csv:
            with patch("json.dump") as mock_json_dump:
                fetcher.save_results(
                    df, csv_path="test.csv", json_path="test.json", metadata=metadata
                )

                # Verify save was called
                mock_to_csv.assert_called_once()

    @pytest.mark.integration
    def test_workflow_empty_references(self):
        """Test workflow with empty reference list."""
        fetcher = LegislationTitleFetcher([])
        df, metadata = fetcher.fetch_titles(verbose=False)

        assert df.empty
        assert metadata["celex_ids"] == []

    @patch("celex_downloader.requests.get")
    def test_workflow_deduplication(self, mock_get, mock_sparql_response):
        """Test that duplicate CELEX IDs are deduplicated."""
        references = [
            '{"CELEX": ["32010L0063"]}',
            '{"CELEX": ["32010L0063"]}',
            '{"Directive": ["2010/63/EU"]}',  # Converts to same CELEX
        ]

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_sparql_response
        mock_get.return_value = mock_response

        fetcher = LegislationTitleFetcher(references)
        df, metadata = fetcher.fetch_titles(verbose=False)

        # Should have only one unique CELEX ID
        assert metadata["celex_ids"] == ["32010L0063"]

    @patch("celex_downloader.requests.get")
    def test_workflow_metadata_persistence(
        self, mock_get, sample_legislation_references, mock_sparql_response
    ):
        """Test that metadata is properly stored across workflow."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_sparql_response
        mock_get.return_value = mock_response

        fetcher = LegislationTitleFetcher(sample_legislation_references)
        df, metadata = fetcher.fetch_titles(verbose=False)

        # Metadata should be stored in instance
        assert fetcher.metadata == metadata

        # Should contain all expected keys
        required_keys = ["celex_ids", "unresolved", "total_results", "raw_json"]
        for key in required_keys:
            assert key in metadata
