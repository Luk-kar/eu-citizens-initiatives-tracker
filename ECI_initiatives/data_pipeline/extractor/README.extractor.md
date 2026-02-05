# ECI Extraction Pipeline

Data processing pipeline that transforms raw HTML scraped from the **European Citizens' Initiatives (ECI)** registry into structured, analytical datasets (CSV).

## 📋 Extractors (Run in Sequence)

The extraction modules process data in the same order as the scrapers, building upon the previous steps' outputs.

| Module | Purpose | Source Data | Key Output |
|--------|---------|-------------|------------|
| `initiatives` | Structured metadata & signature counts | `initiatives/` HTML | `eci_initiatives_{TIMESTAMP}.csv` |
| `responses` | Legislative analysis of Commission answers | `responses/` HTML | `eci_responses_{TIMESTAMP}.csv` |
| `responses_followup_website` | Deep-dive into dedicated follow-up pages | `responses_followup_website/` HTML | `eci_responses_followup_website_{TIMESTAMP}.csv` |

## 🧪 Testing

Each extractor module includes its own comprehensive **pytest suite** located in its `tests/` subdirectory:

- **`initiatives/tests/`**: Behavioral tests for metadata extraction, registration numbers, titles, objectives, timelines, signatures, organizers, and CSV processing.
- **`responses/tests/`**: Tests for legislative outcome classification, rejection reason parsing, and response data extraction.
- **`responses_followup_website/tests/`**: Tests for follow-up event detection, implementation tracking, and complex text analysis.

### Running Tests

From the project root, use the `run_tests.py` script:

```bash
# Run all extractor tests
python run_tests.py --extractor

# Run specific component tests
python run_tests.py --extractor --initiatives
python run_tests.py --extractor --responses
python run_tests.py --extractor --followup-website

# Run with specific test types
python run_tests.py --extractor --initiatives --behaviour
python run_tests.py --extractor --responses --end-to-end

# Run with verbose output and coverage
python run_tests.py --extractor --coverage -v
```

### Direct pytest Usage

You can also run tests directly with pytest:

```bash
# All extractor tests
pytest ECI_initiatives/data_pipeline/extractor

# Specific module tests
pytest ECI_initiatives/data_pipeline/extractor/initiatives/tests
pytest ECI_initiatives/data_pipeline/extractor/responses/tests
pytest ECI_initiatives/data_pipeline/extractor/responses_followup_website/tests
```

## 🛠️ Prerequisites

- **Python 3.8+**
- Dependencies: `pip install -r ECI_initiatives/data_pipeline/requirements.prod.txt`
  - Key library: **BeautifulSoup4** (for parsing)
- Test dependencies: `pip install -r ECI_initiatives/tests/requirements.test.txt`

## 🚀 Quick Start

Ensure you have already run the **Scraper Pipeline** so that the `data/` directory contains raw HTML files.

```bash
cd ECI_initiatives
uv venv && uv pip install -r data_pipeline/requirements.prod.txt
source .venv/bin/activate  # Linux/macOS
# Windows: .venv\Scripts\activate

# Run pipeline sequentially
# Each step automatically detects the latest timestamped data folder

python -m data_pipeline.extractor.initiatives
python -m data_pipeline.extractor.responses
python -m data_pipeline.extractor.responses_followup_website
```

## 📦 Data Pipeline Flow

The extractors read raw HTML from subdirectories and output enriched CSVs into the **same** timestamped run folder to keep input/output bundled together.

```text
data/YYYY-MM-DD_HH-MM-SS/
├── initiatives/                 # [INPUT] Raw HTML
├── responses/                   # [INPUT] Raw HTML
├── responses_followup_website/  # [INPUT] Raw HTML
│
├── eci_initiatives_....csv      # [OUTPUT] Metadata, signatures, funding
├── eci_responses_....csv        # [OUTPUT] Legislative status, rejection reasons
└── eci_responses_followup_....csv # [OUTPUT] Implementation details, events
```

## 📚 Module Documentation

Each extractor module has detailed documentation in its own README:

- **[initiatives/README.md](initiatives/README.md)**: Core metadata extraction, timeline parsing, signature analysis
- **[responses/README.md](responses/README.md)**: Legislative outcome classification, rejection analysis
- **[responses_followup_website/README.md](responses_followup_website/README.md)**: Implementation tracking, event detection, text analysis

## 🔗 Dependencies

The extractor modules have the following dependencies:

1. **`initiatives`**: Standalone (only requires scraped HTML)
2. **`responses`**: Requires `eci_initiatives_*.csv` from the initiatives extractor
3. **`responses_followup_website`**: Requires `eci_responses_*.csv` from the responses extractor

> [!IMPORTANT]
> Always run extractors in sequence: **initiatives** → **responses** → **responses_followup_website**
