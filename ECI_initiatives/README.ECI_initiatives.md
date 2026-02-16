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
# Requires Python 3.8+
# Recommended: Use uv for fast dependency management
cd ECI_initiatives
uv venv
uv pip install -r data_pipeline/requirements.prod.txt
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
```

### 2. Run the Pipeline
```bash
echo "--- Step 1: Initiatives ---" && \
python -m data_pipeline.scraper.initiatives && \
python -m data_pipeline.extractor.initiatives && \
echo "--- Step 2: Commission Responses ---" && \
python -m data_pipeline.scraper.responses && \
python -m data_pipeline.extractor.responses && \
echo "--- Step 3: Followup Websites ---" && \
python -m data_pipeline.scraper.responses_followup_website && \
python -m data_pipeline.extractor.responses_followup_website && \
echo "--- Step 4: Merge ---" && \
python -m data_pipeline.csv_merger.responses
```
Note: 
The pipeline alternates between scraping and extraction to provide natural delays between scraping sessions.
This approach gives the server time to "forget" your requests between sessions, reducing the risk of blacklisting.

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
cd ECI_initiatives/tests
deactivate # if virtual environment remove current one
uv venv
uv pip install -r requirements.test.txt
source .venv/bin/activate  # or .venv\Scripts\activate on Windows


# Check args
python run_tests.py --help

# Run specific module tests
python run_tests.py --scraper
python run_tests.py --extractor
python run_tests.py --merger

# ATTENTION!
# Run individually if encountering failures with missing files
python run_tests.py
```
more details in the [run_tests.py](./tests/run_tests.py)

## 📦 Data Output

All data is versioned in timestamped folders (e.g., `data/2025-12-15_15-33-12/`) containing:

- **Raw HTML**: `initiatives/`, `responses/`, `responses_followup_website/`
- **Structured Data**:
  - `eci_initiatives_*.csv`: Campaign metrics & signature geography.
  - `eci_merger_responses_and_followup_*.csv`: **The Master Dataset** containing the full legislative accountability trail.

## 📚 Documentation

Detailed documentation for each sub-module:

- [**Scraper Documentation**](./data_pipeline/scraper/README.scraper.md)
- [**Extractor Documentation**](./data_pipeline/extractor/README.extractor.md)
- [**Merger Documentation**](./data_pipeline/csv_merger/README.merger.md)
- [**Notebook Initiatives Documentation**](./exploratory_data_analysis/initiatives_campaigns/README.eda.signatures.md)
- [**Notebook Responses Documentation**](./exploratory_data_analysis/initiatives_responses/README.eda_responses.md)