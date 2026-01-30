# ECI Initiatives Analysis - Campaign Signatures

Analysis of European Citizens' Initiatives (ECI) signature campaigns, exploring participation trends, geographic distribution, success rates, and campaign categories.

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
.venv/bin/python -m ipykernel install --user --name=eci-signatures --display-name "ECI Signatures (3.11)"

# Launch Jupyter Lab
uv run jupyter lab
```

## Opening the Notebook

1. After running `uv run jupyter lab`, copy the URL from terminal output (e.g., `http://localhost:8888/lab?token=...`)
2. Paste the URL into your browser
3. In Jupyter Lab's file browser (left sidebar), click on `eci_analysis_signatures.ipynb`
4. Select kernel **"ECI Signatures (3.11)"** from the top-right dropdown
5. Run cells using `Shift+Enter` or the play button

## Project Structure

```
./initiatives_campaigns
├── eci_analysis_signatures.ipynb
├── eci_categories.csv
├── images
│   └── eci_take_initiative_banner.png
├── README.md
└── requirements.prod.txt
```

## Dependencies

Core libraries: numpy, pandas, plotly (interactive visualizations)

See `requirements.prod.txt` for complete list with pinned versions.