# ECI Extraction Pipeline

Data processing pipeline that transforms raw HTML scraped from the **European Citizens' Initiatives (ECI)** registry into structured, analytical datasets (CSV).

## 📋 Extractors (Run in Sequence)

The extraction modules process data in the same order as the scrapers, building upon the previous steps' outputs.

| Module | Purpose | Source Data | Key Output |
|--------|---------|-------------|------------|
| `initiatives` | structured metadata & signature counts | `initiatives/` HTML | `eci_initiatives_{TIMESTAMP}.csv` |
| `responses` | Legislative analysis of Commission answers | `responses/` HTML | `eci_responses_{TIMESTAMP}.csv` |
| `responses_followup_website` | Deep-dive into dedicated follow-up pages | `responses_followup_website/` HTML | `eci_responses_followup_website_{TIMESTAMP}.csv` |

## 🧪 Testing

Comprehensive **pytest suite** available in `tests/extractor/`:

- **Unit tests**: Regex pattern validation, date parsing logic, text normalization.
- **Integration tests**: HTML file parsing, CSV schema verification.
- **Data Quality**: Checks for correct extraction of complex nested JSON fields.

Run tests:
```bash
# Run all extractor tests
python tests/run_tests.py --extractor

# Run specific component tests
python tests/run_tests.py --extractor --initiatives
```

## 🛠️ Prerequisites

- **Python 3.8+**
- Dependencies: `pip install -r ECI_initiatives/requirements.prod.txt`
  - Key library: **BeautifulSoup4** (for parsing)

## 🚀 Quick Start

Ensure you have already run the **Scraper Pipeline** so that the `data/` directory contains raw HTML files.

```bash
cd ECI_initiatives
uv venv && uv pip install -r requirements.prod.txt
source .venv/bin/activate  # Linux/macOS

# Run pipeline sequentially
# Each step automatically detects the latest timestamped data folder

python -m extractor.initiatives
python -m extractor.responses
python -m extractor.responses_followup_website
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

**Full details in each module's README.md**