# ECI Exploratory Data Analysis

Exploratory data analysis of European Citizens' Initiatives (ECI), examining signature campaigns, Commission responses, and policy outcomes.

## Analyses

This directory contains two complementary Jupyter notebook analyses:

### 1. Campaign Signatures Analysis
**Location:** `initiatives_campaigns/`  
**Notebook:** `eci_analysis_signatures.ipynb`

Analyzes ECI signature campaigns including participation trends, geographic distribution, success rates, and campaign categories.

→ See `initiatives_campaigns/README.md` for setup and usage instructions.

### 2. Response Data Exploration
**Location:** `initiatives_responses/`  
**Notebook:** `eci_analysis_responses.ipynb`

Explores Commission responses to ECIs, including legislative linkages, follow-up actions, and campaign outcomes.

→ See `initiatives_responses/README.md` for setup and usage instructions.

## Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager
- `jupyter nbconvert` (required for clearing notebook outputs during Kaggle migration)

## Data

Both notebooks automatically load the most recent datasets from `../../data/` (timestamped folders like `YYYY-MM-DD_HH-MM-SS`). No manual path configuration required.

**Data sources:**
- `eci_initiatives_*.csv` - Core initiative and signature data
- `eci_merger_responses_and_followup_*.csv` - Commission responses (used by responses notebook)

## 🚀 Kaggle Migration

To prepare these notebooks for publication on Kaggle:

1. **Navigate to the migration tool directory**:
   ```bash
   cd kaggle_output
   ```

2. **Setup environment & run migration**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   python kaggle_migration.py
   ```

3. **Result**: 
   The automated migration tool will package all requirements. Check the `kaggle_output/` directory for the following generated artifacts:
   - **Clean `.ipynb` files**: Notebook outputs are automatically cleared via `nbconvert` and internal data paths/image links are rewritten for the Kaggle environment.
   - **`csv_files/`**: A subdirectory containing the validated `.csv` datasets ready for Kaggle upload.
   - **`dataset-metadata.json`**: Auto-generated metadata for easy Kaggle dataset creation.
   - **`migration_report.txt`**: A detailed summary detailing source paths, dataset row/column shapes, and file sizes.
   - **`migration_run_YYYYMMDD_HHMMSS.log`**: Detailed execution logs of the run.

## 🔧 Maintenance

**Priority: Low**

The Kaggle migration tooling is designed for infrequent use (typically once per major dataset publication). The process is highly automated and does not require ongoing updates unless the underlying notebook structures change significantly.

### Modular Architecture
The migration logic has been refactored into the `migration_modules/` package to ensure clean separation of concerns and easy maintainability:

- **`constants.py`**: Centralizes configuration, handling dynamic Kaggle and local path setups securely.
- **`data_finder.py`**: Automatically identifies and validates the most recent timestamped dataset folder.
- **`notebook_processor.py`**: Manages reading the notebooks, transforming path implementations, replacing image URLs, and systematically clearing outputs.
- **`report_generator.py`**: Orchestrates final dataset packaging, metadata creation, and logging summaries.

## Structure

```text
exploratory_data_analysis/
├── README.md                    # This file
├── initiatives_campaigns/       # Signature campaign analysis
│   ├── eci_analysis_signatures.ipynb
│   └── README.md
├── initiatives_responses/       # Response data exploration
│   ├── eci_analysis_responses.ipynb
│   └── README.md
└── kaggle_output/               # Migration tools & output
    ├── migration_modules/       # Modular migration logic components
    │   ├── __init__.py
    │   ├── constants.py         # Project paths and Kaggle setups
    │   ├── data_finder.py       # Data discovery and validation logic
    │   ├── notebook_processor.py # Cell transformations & nbconvert clearing
    │   └── report_generator.py  # Metadata JSON and report creation
    ├── kaggle_migration.py      # Main migration orchestrator script
    └── requirements.txt
```