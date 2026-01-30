"""
CELEX Title Downloader Module

Downloads English titles for CELEX documents via EUR-Lex SPARQL endpoint.
"""

import re
import requests
import pandas as pd
from typing import List, Dict, Optional

from legislation_titles.errors import InvalidCelexError


class CelexTitleDownloader:
    """
    Downloads English titles for CELEX documents via EUR-Lex SPARQL endpoint.
    """

    SPARQL_ENDPOINT = "https://publications.europa.eu/webapi/rdf/sparql"

    def __init__(self, celex_ids: List[str]):
        """
        Initialize the downloader with CELEX IDs.

        Args:
            celex_ids: List of CELEX identifiers (e.g., ['52020DC0015', '32010L0063'])
        """
        self.celex_ids = celex_ids
        self.df_titles: Optional[pd.DataFrame] = None
        self.raw_json: Optional[Dict] = None

    @staticmethod
    def create_batch_sparql_query(celex_ids: List[str]) -> str:
        """
        Create a SPARQL query to fetch English titles for multiple CELEX documents.

        Args:
            celex_ids: List of CELEX identifiers

        Returns:
            SPARQL query string
        """
        prefixes = """
PREFIX cdm: <http://publications.europa.eu/ontology/cdm#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX euvoc: <http://publications.europa.eu/ontology/euvoc#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
"""

        select_clause = """
SELECT ?celex_id (str(?ISO_639_1) AS ?lang) ?title
"""

        where_start = """
WHERE
{
"""

        values_clause = "  VALUES ?celex_id {\n"
        for celex_id in celex_ids:
            values_clause += f'    "celex:{celex_id}"^^xsd:string\n'
        values_clause += "  }\n"

        work_clause = """
  ?w cdm:work_id_document ?celex_id .
"""

        expression_clause = """
  ?expr cdm:expression_belongs_to_work ?w .
"""

        language_clause = """
  ?expr cdm:expression_uses_language ?lang .
  ?lang skos:notation ?ISO_639_1 .
"""

        title_clause = """
  ?expr cdm:expression_title ?title .
"""

        filter_clause = """
  FILTER(datatype(?ISO_639_1) = euvoc:ISO_639_1 && str(?ISO_639_1) = "en")
}
"""

        query = (
            prefixes
            + select_clause
            + where_start
            + values_clause
            + work_clause
            + expression_clause
            + language_clause
            + title_clause
            + filter_clause
        )

        return query

    @staticmethod
    def validate_celex(celex_id):
        """
        Validate CELEX format according to EUR-Lex numbering specifications.

        CELEX (Communitatis Europeae LEX) is the official identifier system for
        EU legal documents. Format: [Sector][Year][Type][Number]

        Args:
            celex_id: CELEX identifier (with or without 'celex:' prefix)

        Returns:
            Tuple of (is_valid, error_message)
            - is_valid: True if CELEX passes validation, False otherwise
            - error_message: None if valid, descriptive error string if invalid

        Validation Rules:
            - Minimum length: 8 characters (e.g., "32020R01")
            - Sector (position 0): Must be one of 0-9, C, or E
            - Sector-specific constraints:
                * Sector 9 (Parliamentary questions): Only 'E' (written), 'H' (question time),
                or 'O' (oral) allowed at position 5

        Valid Sectors:
            0: Consolidated acts
            1: Treaties
            2: International agreements
            3: Legislation (Regulations, Directives, Decisions)
            4: Complementary legislation
            5: Preparatory acts (COM documents, proposals)
            6: Case-law (Court judgments, opinions)
            7: National transposition measures
            8: National case-law references
            9: Parliamentary questions
            C: Official Journal C series documents
            E: EFTA documents

        Examples:
            >>> validate_celex("32010L0063")
            (True, None)

            >>> validate_celex("92020E1234")  # Valid parliamentary question
            (True, None)

            >>> validate_celex("92020X1234")  # Invalid - 'X' not allowed in Sector 9
            (False, "Sector 9 must use 'E' document type")

            >>> validate_celex("Z2020DC001")  # Invalid sector
            (False, "Invalid sector: Z")

        References:
            High-level overview:
            https://op.europa.eu/en/publication-detail/-/publication/4b2a89a1-8877-11f0-9af8-01aa75ed71a1/language-en

            Intermediate user guide:
            https://web.archive.org/web/20210922140227/https://eur-lex.europa.eu/content/help/faq/celex-number.html

            Detailed technical specification:
            http://www.justcite.com/kb/wp-content/uploads/2011/01/CELEX-Numbers.pdf
        """

        if not celex_id:
            return False, "CELEX is empty"

        if len(celex_id) < 8:
            return False, f"CELEX too short: {celex_id}"

        sector = celex_id[0]
        if sector not in {"0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "C", "E"}:
            return False, f"Invalid sector: {sector}"

        # Sector-specific validation
        if sector == "9" and celex_id[5] != "E":
            return False, f"Sector 9 must use 'E' document type"

        return True, None

    @staticmethod
    def parse_celex_to_readable_format(celex_id: str) -> tuple[str, str]:
        """
        Parse CELEX number to extract legislation type and human-readable document number.

        CELEX format: [Sector][Year][Type][Number]

        Args:
            celex_id: CELEX identifier

        Returns:
            Tuple of (legislation_type, document_number)
        """

        celex_clean = celex_id.replace("celex:", "")

        is_valid, error = CelexTitleDownloader.validate_celex(celex_clean)
        if not is_valid:
            raise InvalidCelexError(error)

        pattern = r"^(\d)(\d{4})([A-Z]{1,2})(\d{4,})$"
        match = re.match(pattern, celex_clean)

        if not match:
            # Validation passed but pattern doesn't match - unsupported format
            raise InvalidCelexError(
                f"Unsupported CELEX format: {celex_id}. "
                f"Pattern does not match expected structure [Sector][Year][Type][Number]"
            )

        sector, year, type_code, number = match.groups()

        if sector == "3":
            type_mapping = {
                "L": "Directive",
                "R": "Regulation",
                "D": "Decision",
                "H": "Recommendation",
                "X": "Opinion",
            }

            legislation_type = type_mapping.get(type_code, type_code)
            number_int = int(number)

            if type_code == "L":
                document_number = f"{year}/{number_int}/EU"
            elif type_code == "R":
                document_number = f"{number_int}/{year}"
            else:
                document_number = f"{number_int}/{year}"

        elif sector == "5":
            type_mapping = {
                "PC": "Proposal (Commission)",
                "DC": "Communication (Commission)",
                "SC": "Communication (Council)",
                "JC": "Communication (Joint)",
                "AC": "Action",
                "IG": "Interinstitutional Agreement",
            }

            legislation_type = type_mapping.get(
                type_code, f"Preparatory Document ({type_code})"
            )
            document_number = f"COM({year}) {int(number)}"

        elif sector == "6":
            type_mapping = {
                "CJ": "Court of Justice Judgment",
                "TJ": "General Court Judgment",
                "CA": "Court of Justice Advocate General's Opinion",
                "TA": "General Court Advocate General's Opinion",
            }

            legislation_type = type_mapping.get(type_code, f"Case Law ({type_code})")
            document_number = f"C-{int(number)}/{year[2:]}"

        elif sector == "9":
            # Parliamentary questions format: 9YYYYTNNNNN

            type_mapping = {
                "E": "European Parliament - Written Questions",
                "H": "European Parliament - Questions Asked During Question Time",
                "O": "European Parliament - Oral Questions",
            }

            legislation_type = type_mapping.get(type_code, "Parliamentary Question")
            document_number = f"{type_code}-{int(number)}/{year}"

        else:
            raise InvalidCelexError(
                f"Sector {sector} is valid but not yet implemented in parser: {celex_id}. "
                f"Supported sectors: 3 (Legislation), 5 (Preparatory), 6 (Case-law), 9 (Parliamentary)"
            )

        return legislation_type, document_number

    def download_titles(self) -> tuple[pd.DataFrame, Optional[Dict]]:
        """
        Download English titles for the initialized CELEX IDs from EUR-Lex SPARQL endpoint.

        Returns:
            Tuple of (DataFrame with results, raw JSON response or None if failed)
        """
        if not self.celex_ids:
            print("No CELEX IDs to query.")
            return pd.DataFrame(), None

        query = self.create_batch_sparql_query(self.celex_ids)

        response = requests.get(
            self.SPARQL_ENDPOINT,
            params={"query": query, "format": "application/sparql-results+json"},
        )

        if response.status_code != 200:
            print(f"Batch query failed with status {response.status_code}")
            print(f"Response: {response.text}")
            self.df_titles = pd.DataFrame()
            self.raw_json = None
            return self.df_titles, self.raw_json

        try:
            data = response.json()

            results = []
            for binding in data["results"]["bindings"]:
                celex_id = binding["celex_id"]["value"]
                legislation_type, document_number = self.parse_celex_to_readable_format(
                    celex_id
                )

                results.append(
                    {
                        "celex_id": celex_id,
                        "legislation_type": legislation_type,
                        "document_number": document_number,
                        "lang": binding["lang"]["value"],
                        "title": binding["title"]["value"],
                    }
                )

            self.df_titles = pd.DataFrame(results)
            self.raw_json = data
            return self.df_titles, self.raw_json

        except (requests.exceptions.JSONDecodeError, Exception) as e:
            print(f"Batch query returned invalid JSON: {response.text}")
            self.df_titles = pd.DataFrame()
            self.raw_json = None
            return self.df_titles, self.raw_json
