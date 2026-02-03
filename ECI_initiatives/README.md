# European Citizens' Initiatives (ECI) Data Pipeline

Python-based data engineering pipeline to scrape, extract, merge, and analyze the full lifecycle of European Citizens' Initiatives (ECIs)—from initial signature collection to final Commission legislative responses.

## 🌟 Overview

This project builds a unified dataset to answer: **"Do citizens' initiatives actually lead to new EU laws?"**

It consists of four sequential stages:
1.  **🕵️ Scraper**: Downloads raw HTML pages (Registry, Commission Answers, Follow-up sites).
2.  **⛏️ Extractor**: Parses HTML into structured CSVs (Signatures, Deadlines, Legal Acts).
3.  **🔗 Merger**: Unifies disparate datasets into a single "Accountability Record".
4.  **📊 Analysis**: Visualizes campaign success rates and legislative impact using Jupyter Notebooks.

## 📂 Architecture

```text
ECI_initiatives/
├── data_pipeline/
│   ├── scraper/                     # [Stage 1] Selenium web scrapers
│   ├── extractor/                   # [Stage 2] BeautifulSoup parsers
│   └── csv_merger/                  # [Stage 3] CSV consolidation
├── exploratory_data_analysis/   # [Stage 4] Jupyter Notebooks & Visuals
├── data/                        # [Storage] Timestamped input/output folders
└── tests/                       # [QA] Pytest suite for all modules
```

## 🚀 Quick Start (End-to-End)

Run the entire pipeline in sequence. Each step detects the output of the previous step in the `data/` folder.

### 1. Setup Environment
```bash
# Recommended: Use uv for fast dependency management
cd ECI_initiatives
uv venv
uv pip install -r requirements.prod.txt
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
```

### 2. Run the Pipeline
```bash
# --- Step 1: SCRAPE ---
python -m scraper.initiatives               # Get registry data
python -m scraper.responses                 # Get Commission answers
python -m scraper.responses_followup_website # Get dedicated project sites

# --- Step 2: EXTRACT ---
python -m extractor.initiatives             # Parse signature counts & metadata
python -m extractor.responses               # Analyze legislative outcomes
python -m extractor.responses_followup_website # Extract implementation details

# --- Step 3: MERGE ---
python -m csv_merger.responses              # Create the final Master CSV
```

### 3. Analyze Results
Launch Jupyter to explore the notebooks in `exploratory_data_analysis/`:
```bash
# Install analysis dependencies
pip install -r exploratory_data_analysis/requirements.eda.txt

# Start Notebook
jupyter notebook
```

## 🧪 Testing

The project is protected by a unified test runner covering scraping logic, regex parsing, and data merging.

```bash
# Run all tests
python run_tests.py

# Run specific module tests
python run_tests.py --scraper
python run_tests.py --extractor
python run_tests.py --merger
```

## 📦 Data Output

All data is versioned in timestamped folders (e.g., `data/2025-12-15_15-33-12/`) containing:

- **Raw HTML**: `initiatives/`, `responses/`
- **Structured Data**:
  - `eci_initiatives_*.csv`: Campaign metrics & signature geography.
  - `eci_merger_responses_and_followup_*.csv`: **The Master Dataset** containing the full legislative accountability trail.

## 📚 Documentation

Detailed documentation for each sub-module:

- [**Scraper Documentation**](./data_pipeline/scraper/initiatives/README.md)
- [**Extractor Documentation**](./extractor/README.md)
- [**Merger Documentation**](./csv_merger/responses/README.md)
- [**Notebook Initiatives Documentation**](./exploratory_data_analysis/initiatives_campaigns/README.md)
- [**Notebook Responses Documentation**](./exploratory_data_analysis/initiatives_responses/README.md)
```