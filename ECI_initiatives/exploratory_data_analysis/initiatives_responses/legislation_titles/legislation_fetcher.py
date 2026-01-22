"""
Legislation Title Fetcher Module

Master class that combines CELEX translation and title downloading.
"""

import json
import pandas as pd
from typing import List, Dict, Optional

from celex_translator import CelexTranslator
from celex_downloader import CelexTitleDownloader


class LegislationTitleFetcher:
    """
    Master class that combines CELEX translation and title downloading.
    """

    def __init__(self, referenced_legislation_by_id: List):
        """
        Initialize the fetcher with legislation references.

        Args:
            referenced_legislation_by_id: List of JSON strings with legislation references
        """
        self.referenced_legislation_by_id = referenced_legislation_by_id
        self.translator = CelexTranslator(referenced_legislation_by_id)
        self.downloader: Optional[CelexTitleDownloader] = None
        self.metadata: Dict = {}

    def fetch_titles(self, verbose: bool = True) -> tuple[pd.DataFrame, Dict]:
        """
        Extract CELEX IDs from references and download their titles.

        Args:
            verbose: If True, print diagnostic information

        Returns:
            Tuple of (DataFrame with titles, metadata dictionary)
        """
        celex_ids, unresolved = self.translator.extract_all_celex_ids()

        if verbose:
            print(f"Extracted {len(celex_ids)} unique CELEX IDs: {celex_ids}")
            if unresolved:
                print(f"Warning: {len(unresolved)} unresolved references: {unresolved}")

        if not celex_ids:
            print("No CELEX IDs found to query.")
            self.metadata = {"celex_ids": [], "unresolved": unresolved}
            return pd.DataFrame(), self.metadata

        self.downloader = CelexTitleDownloader(celex_ids)
        df_titles, raw_json = self.downloader.download_titles()

        self.metadata = {
            "celex_ids": celex_ids,
            "unresolved": unresolved,
            "total_results": len(df_titles),
            "raw_json": raw_json,
        }

        return df_titles, self.metadata

    def save_results(
        self,
        df: pd.DataFrame,
        csv_path: str = "data/legislation_titles.csv",
        json_path: str = "data/legislation_titles.json",
        metadata: Optional[Dict] = None,
    ):
        """
        Save results to CSV and optionally JSON.

        Args:
            df: DataFrame with title results
            csv_path: Path to save CSV file
            json_path: Path to save JSON file (only if metadata provided)
            metadata: Metadata dictionary containing raw JSON
        """
        df.to_csv(csv_path, index=False, encoding="utf-8")
        print(f"Results saved to {csv_path}")

        if metadata and metadata.get("raw_json"):
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(metadata["raw_json"], f, indent=2, ensure_ascii=False)
            print(f"Raw JSON saved to {json_path}")
