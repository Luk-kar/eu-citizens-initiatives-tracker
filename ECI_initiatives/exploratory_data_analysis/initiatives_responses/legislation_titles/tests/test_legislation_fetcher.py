"""
Tests for Legislation Title Fetcher Module.
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch, mock_open
import json
from legislation_titles.legislation_fetcher import LegislationTitleFetcher


class TestLegislationTitleFetcher:
    """Test suite for LegislationTitleFetcher class."""

    def test_init(self, sample_legislation_references):
        """Test initialization with legislation references."""
        fetcher = LegislationTitleFetcher(sample_legislation_references)
        assert fetcher.referenced_legislation_by_id == sample_legislation_references
        assert fetcher.translator is not None
        assert fetcher.downloader is None
        assert fetcher.metadata == {}

    @patch("legislation_titles.legislation_fetcher.CelexTitleDownloader")
    def test_fetch_titles_success(
        self, mock_downloader_class, sample_legislation_references, mock_sparql_response
    ):
        """Test successful title fetching."""
        # Mock translator
        mock_celex_ids = ["32010L0063", "32002R0178"]
        mock_unresolved = []

        # Mock downloader instance
        mock_downloader_instance = Mock()
        mock_df = pd.DataFrame(
            {
                "celex_id": ["celex:32010L0063", "celex:32002R0178"],
                "title": ["Title 1", "Title 2"],
                "lang": ["en", "en"],
            }
        )
        mock_downloader_instance.download_titles.return_value = (
            mock_df,
            mock_sparql_response,
        )
        mock_downloader_class.return_value = mock_downloader_instance

        fetcher = LegislationTitleFetcher(sample_legislation_references)

        # Patch the translator's method
        with patch.object(
            fetcher.translator,
            "extract_all_celex_ids",
            return_value=(mock_celex_ids, mock_unresolved),
        ):
            df, metadata = fetcher.fetch_titles(verbose=False)

        # Verify the downloader was instantiated with correct IDs
        mock_downloader_class.assert_called_once_with(mock_celex_ids)

        assert not df.empty
        assert len(df) == 2
        assert metadata["celex_ids"] == mock_celex_ids
        assert metadata["unresolved"] == mock_unresolved
        assert metadata["total_results"] == 2
        assert metadata["raw_json"] == mock_sparql_response

    @patch("legislation_titles.legislation_fetcher.CelexTitleDownloader")
    def test_fetch_titles_no_celex_ids(
        self, mock_downloader_class, sample_legislation_references
    ):
        """Test fetching with no CELEX IDs found."""
        mock_unresolved = [{"type": "Article", "value": "15"}]

        fetcher = LegislationTitleFetcher(sample_legislation_references)

        with patch.object(
            fetcher.translator,
            "extract_all_celex_ids",
            return_value=([], mock_unresolved),
        ):
            df, metadata = fetcher.fetch_titles(verbose=False)

        assert df.empty
        assert metadata["celex_ids"] == []
        assert metadata["unresolved"] == mock_unresolved
        assert fetcher.downloader is None

    @patch("legislation_titles.legislation_fetcher.CelexTitleDownloader")
    def test_fetch_titles_verbose_output(
        self, mock_downloader_class, sample_legislation_references, capsys
    ):
        """Test verbose output during fetching."""
        mock_celex_ids = ["32010L0063"]
        mock_unresolved = [{"type": "Article", "value": "15"}]

        mock_downloader_instance = Mock()
        mock_downloader_instance.download_titles.return_value = (pd.DataFrame(), None)
        mock_downloader_class.return_value = mock_downloader_instance

        fetcher = LegislationTitleFetcher(sample_legislation_references)

        with patch.object(
            fetcher.translator,
            "extract_all_celex_ids",
            return_value=(mock_celex_ids, mock_unresolved),
        ):
            fetcher.fetch_titles(verbose=True)

        captured = capsys.readouterr()
        assert "Extracted 1 unique CELEX IDs" in captured.out
        assert "Warning: 1 unresolved references" in captured.out

    @patch("legislation_titles.legislation_fetcher.CelexTitleDownloader")
    def test_fetch_titles_stores_downloader(
        self, mock_downloader_class, sample_legislation_references
    ):
        """Test that downloader instance is stored."""
        mock_celex_ids = ["32010L0063"]
        mock_unresolved = []

        # Mock downloader instance
        mock_downloader_instance = Mock()
        mock_downloader_instance.download_titles.return_value = (
            pd.DataFrame({"celex_id": ["32010L0063"], "title": ["Test"]}),
            {"results": {"bindings": []}},
        )
        mock_downloader_class.return_value = mock_downloader_instance

        fetcher = LegislationTitleFetcher(sample_legislation_references)

        with patch.object(
            fetcher.translator,
            "extract_all_celex_ids",
            return_value=(mock_celex_ids, mock_unresolved),
        ):
            fetcher.fetch_titles(verbose=False)

    @patch("builtins.open", new_callable=mock_open)
    def test_save_results_csv(self, mock_file):
        """Test saving results to CSV."""
        df = pd.DataFrame({"celex_id": ["32010L0063"], "title": ["Test Title"]})

        fetcher = LegislationTitleFetcher([])

        with patch.object(df, "to_csv") as mock_to_csv:
            fetcher.save_results(df, csv_path="test.csv")
            mock_to_csv.assert_called_once_with(
                "test.csv", index=False, encoding="utf-8"
            )

    @patch("builtins.open", new_callable=mock_open)
    def test_save_results_json(self, mock_file):
        """Test saving results with JSON metadata."""
        df = pd.DataFrame({"celex_id": ["32010L0063"]})
        metadata = {"raw_json": {"test": "data"}}

        fetcher = LegislationTitleFetcher([])

        with patch.object(df, "to_csv"):
            with patch("json.dump") as mock_json_dump:
                fetcher.save_results(
                    df, csv_path="test.csv", json_path="test.json", metadata=metadata
                )
                mock_json_dump.assert_called_once()

    @patch("builtins.open", new_callable=mock_open)
    def test_save_results_no_metadata(self, mock_file):
        """Test saving results without metadata."""
        df = pd.DataFrame({"celex_id": ["32010L0063"]})

        fetcher = LegislationTitleFetcher([])

        with patch.object(df, "to_csv"):
            with patch("json.dump") as mock_json_dump:
                fetcher.save_results(
                    df, csv_path="test.csv", json_path="test.json", metadata=None
                )
                mock_json_dump.assert_not_called()

    @patch("builtins.open", new_callable=mock_open)
    def test_save_results_metadata_without_raw_json(self, mock_file):
        """Test saving with metadata but no raw_json field."""
        df = pd.DataFrame({"celex_id": ["32010L0063"]})
        metadata = {"celex_ids": ["32010L0063"]}

        fetcher = LegislationTitleFetcher([])

        with patch.object(df, "to_csv"):
            with patch("json.dump") as mock_json_dump:
                fetcher.save_results(
                    df, csv_path="test.csv", json_path="test.json", metadata=metadata
                )
                mock_json_dump.assert_not_called()

    @patch("legislation_titles.legislation_fetcher.CelexTitleDownloader")
    def test_fetch_titles_metadata(
        self, mock_downloader_class, sample_legislation_references, mock_sparql_response
    ):
        """Test that metadata is correctly populated."""
        mock_celex_ids = ["32010L0063"]
        mock_unresolved = [{"type": "Article", "value": "15"}]

        mock_downloader_instance = Mock()
        mock_df = pd.DataFrame(
            {
                "celex_id": ["celex:32010L0063"],
                "title": ["Test Title"],
            }
        )
        mock_downloader_instance.download_titles.return_value = (
            mock_df,
            mock_sparql_response,
        )
        mock_downloader_class.return_value = mock_downloader_instance

        fetcher = LegislationTitleFetcher(sample_legislation_references)

        with patch.object(
            fetcher.translator,
            "extract_all_celex_ids",
            return_value=(mock_celex_ids, mock_unresolved),
        ):
            df, metadata = fetcher.fetch_titles(verbose=False)

        assert metadata["celex_ids"] == mock_celex_ids
        assert metadata["unresolved"] == mock_unresolved
        assert metadata["total_results"] == 1
        assert metadata["raw_json"] == mock_sparql_response
