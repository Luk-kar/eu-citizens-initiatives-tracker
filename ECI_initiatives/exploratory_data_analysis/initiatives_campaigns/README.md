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

## Data Loading

The notebook uses dynamic data loading to automatically find and load the most recent ECI datasets from `../../data/`:

### Production Mode (Active)

The notebook includes helper functions that:
- Scan `ECI_initiatives/data/` for timestamped folders (format: `YYYY-MM-DD_HH-MM-SS`)
- Identify the most recent folder automatically
- Load the latest `eci_initiatives_*.csv` file from that folder
- Extract and display metadata (folder creation date, file extraction date)

**Functions:**
- `find_latest_timestamp_folder()`: Locates the most recent data folder
- `find_latest_csv()`: Finds specific CSV files by prefix
- `load_latest_eci_initiatives()`: Orchestrates loading and returns dataframe with timestamps

This approach ensures the notebook always uses the freshest available data without manual path updates.

### Development Mode (Commented Out)

For debugging or testing with specific dataset versions, a commented-out block allows hardcoded paths:

```python
# data_folder = "../data/2025-09-18_16-33-57"
# data_file = f'{data_folder}/eci_initiatives_2025-11-04_11-59-38.csv'
# df = pd.read_csv(data_file)
```

Uncomment this block and comment out the production loader when you need to pin to a specific data snapshot.

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