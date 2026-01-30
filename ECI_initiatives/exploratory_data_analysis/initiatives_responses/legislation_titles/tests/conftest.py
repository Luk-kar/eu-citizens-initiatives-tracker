"""
Pytest configuration and shared fixtures.
"""

import pytest
import pandas as pd
from typing import List


@pytest.fixture
def sample_legislation_references() -> List:
    """Sample legislation references for testing."""
    return [
        '{"Article": ["19(2)"], "CELEX": ["52014DC0335"]}',
        None,
        '{"Directive": ["2010/63/EU"], "CELEX": ["52020DC0015"]}',
        '{"CELEX": ["52018PC0179", "32002R0178", "32019R1381"]}',
        '{"Directive": ["2010/13/EU"]}',
        '{"Regulation": ["178/2002"]}',
        '{"Article": ["15"]}',
    ]


@pytest.fixture
def sample_celex_ids() -> List[str]:
    """Sample CELEX IDs for testing."""
    return [
        "32010L0063",
        "32002R0178",
        "52020DC0015",
        "52018PC0179",
        "62023CJ0026",
        "32024R2522",
    ]


@pytest.fixture
def invalid_json_references() -> List:
    """Invalid JSON strings for testing error handling."""
    return [
        '{"Article": ["19(2)"',  # Missing closing brace
        "{invalid json}",
        '{"CELEX": ["32010L0063"]',  # Missing closing bracket
    ]


@pytest.fixture
def mock_sparql_response() -> dict:
    """Mock SPARQL API response."""
    return {
        "head": {"vars": ["celex_id", "lang", "title"]},
        "results": {
            "bindings": [
                {
                    "celex_id": {"type": "literal", "value": "celex:32010L0063"},
                    "lang": {"type": "literal", "value": "en"},
                    "title": {
                        "type": "literal",
                        "value": "Directive 2010/63/EU on the protection of animals",
                    },
                },
                {
                    "celex_id": {"type": "literal", "value": "celex:32002R0178"},
                    "lang": {"type": "literal", "value": "en"},
                    "title": {
                        "type": "literal",
                        "value": "Regulation (EC) No 178/2002 on food law",
                    },
                },
            ]
        },
    }
