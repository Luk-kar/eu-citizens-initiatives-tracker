# EU Legislation Title Fetcher

This package fetches English titles for EU legislation from EUR-Lex using CELEX identifiers.

## Features

- Converts Directives and Regulations to CELEX format
- Fetches titles via EUR-Lex SPARQL API
- Handles multiple document types (Directives, Regulations, Proposals, Communications, Court Judgments)
- Exports results to CSV and JSON

## Data Source

This tool queries the **Publications Office of the European Union SPARQL endpoint**:
- **Endpoint**: [https://publications.europa.eu/webapi/rdf/sparql](https://publications.europa.eu/webapi/rdf/sparql)
- **Documentation**: [Cellar Knowledge Graph](https://op.europa.eu/en/web/cellar/cellar-data/metadata/knowledge-graph)
- **Data model**: Uses the Common Data Model (CDM) ontology for EU publications

The SPARQL endpoint provides access to Cellar, the EU Publication Office's semantic repository containing metadata for all EU legal documents.

## Installation

```bash
pip install -r requirements.prod.txt
```

For development with testing dependencies:

```bash
pip install -r requirements.prod.txt -r requirements.tests.txt
```

## Usage

```python
from legislation_fetcher import LegislationTitleFetcher

referenced_legislation_by_id = [
    '{"CELEX": ["32010L0063"]}',
    '{"Directive": ["2010/13/EU"]}',
    '{"Regulation": ["178/2002"]}',
]

fetcher = LegislationTitleFetcher(referenced_legislation_by_id)
df_results, metadata = fetcher.fetch_titles()
fetcher.save_results(df_results, metadata=metadata)
```

Or run the example:

```bash
python main.py
```

## Output

Results are saved in the `data/` directory:
- `legislation_titles.csv` - Structured data with CELEX IDs, document types, and titles
- `legislation_titles.json` - Raw SPARQL response

## Testing

The project includes a comprehensive test suite using pytest.

### Running Tests

```bash
# Run all tests EXCEPT external API calls (default for development)
pytest -v -m "not external_api"

# Run only unit tests (fastest)
pytest -v tests/test_celex_downloader.py tests/test_celex_translator.py

# Run integration tests with mocks
pytest -v tests/test_integration.py -m "not external_api"

# Run tests with coverage report
pytest --cov=legislation_titles --cov-report=html

# Run ALL tests including real EUR-Lex API calls (slow, requires internet)
pytest -v -m external_api
```

IMPORTANT!: Do not abuse the `external_api`, your IP could be whitelisted for a while!

### Test Structure

```
tests/
├── __init__.py
├── conftest.py                    # Shared fixtures and configuration
├── test_celex_translator.py       # Tests for CELEX conversion logic
├── test_celex_downloader.py       # Tests for EUR-Lex API interactions
├── test_legislation_fetcher.py    # Tests for main orchestration class
└── test_integration.py            # End-to-end integration tests
```

The test suite covers:
- Unit tests for each component
- CELEX format parsing and validation
- API error handling with mocked responses
- Edge cases and invalid input handling

## Project Structure

```
legislation_titles/
├── celex_translator.py      # Converts legislation references to CELEX
├── celex_downloader.py       # Downloads titles from EUR-Lex
├── legislation_fetcher.py    # Master orchestration class
├── main.py                   # Example usage script
├── data/                     # Output directory
├── tests/                    # Test suite
├── requirements.prod.txt     # Production dependencies
├── requirements.tests.txt    # Testing dependencies
├── pytest.ini                # Pytest configuration
└── README.md
```

## CELEX Format

- **Directives**: `2010/63/EU` → CELEX `32010L0063`
- **Regulations**: `178/2002` → CELEX `32002R0178`
- **Proposals**: `COM(2018) 179` → CELEX `52018PC0179`
- **Court Judgments**: `C-26/23` → CELEX `62023CJ0026`