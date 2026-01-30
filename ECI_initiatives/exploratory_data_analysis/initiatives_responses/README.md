Here's the updated README.md with notebook opening instructions:

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