# ECI Initiatives Analysis - Response Data Exploration

Exploratory data analysis of European Citizens' Initiatives (ECI) responses, including participation patterns, legislative linkages, and campaign outcomes.

## Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager

## Quick Start

```bash
# Create virtual environment with Python 3.11
uv venv --python 3.11

# Install dependencies
uv pip install -r requirements.prod.txt

# Register Jupyter kernel
.venv/bin/python -m ipykernel install --user --name=eci-analysis --display-name "ECI Analysis (3.11)"

# Launch Jupyter Lab
uv run jupyter lab
```

## Opening the Notebook

1. After running `uv run jupyter lab`, copy the URL from terminal output (e.g., `http://localhost:8888/lab?token=...`)
2. Paste the URL into your browser
3. In Jupyter Lab's file browser (left sidebar), click on `eci_analysis_responses.ipynb`
4. Select kernel **"ECI Analysis (3.11)"** from the top-right dropdown
5. Run cells using `Shift+Enter` or the play button

## Data Loading

The notebook uses dynamic data loading to automatically find and load the most recent ECI datasets from `../../data/`:

### Production Mode (Active)

The notebook includes helper functions that:
- Scan `ECI_initiatives/data/` for timestamped folders (format: `YYYY-MM-DD_HH-MM-SS`)
- Identify the most recent folder automatically
- Load both required CSV files from that folder:
  - `eci_initiatives_*.csv` - Core initiative data
  - `eci_merger_responses_and_followup_*.csv` - Commission responses and follow-up actions
- Display metadata about loaded files and directory

**Functions:**
- `find_latest_timestamp_folder()`: Locates the most recent data folder
- `find_latest_csv()`: Finds specific CSV files by prefix
- `load_latest_eci_data()`: Orchestrates loading and returns both dataframes plus folder path

This approach ensures the notebook always uses the freshest available data without manual path updates.

### Development Mode (Commented Out)

For debugging or testing with specific dataset versions, a commented-out block allows hardcoded paths:

```python
# data_folder = "../data/2025-09-18_16-33-57"
# df_initiatives = pd.read_csv(f'{data_folder}/eci_initiatives_2025-12-15_19-12-45.csv')
# df_responses = pd.read_csv(f'{data_folder}/eci_merger_responses_and_followup_2026-01-13_13-52-31.csv')
```

Uncomment this block and comment out the production loader when you need to pin to a specific data snapshot for reproducibility or comparison.

## Project Structure

```
initiatives_responses/
├── eci_analysis_responses.ipynb    # Main analysis notebook
├── requirements.prod.txt            # Python dependencies
├── legislation_titles/              # Legislation data fetcher module
│   ├── main.py
│   ├── requirements.prod.txt
│   └── tests/
└── images/                          # Visual assets
```

## Dependencies

Core libraries: numpy, pandas, scipy, matplotlib, plotly, seaborn, wordcloud

See `requirements.prod.txt` for complete list with pinned versions.

## Legislation Titles Module

The `legislation_titles/` subdirectory contains a standalone package for fetching EU legislation metadata. See its README for details.