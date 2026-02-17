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
   Check `kaggle_output/` for clean `.ipynb` files and a `csv_files` folder ready for upload.

## 🔧 Maintenance

**Priority: Low**

The Kaggle migration tooling is designed for one-time or very infrequent use (typically once per major dataset publication). The migration scripts are self-contained and require minimal maintenance since:

- Notebooks are primarily developed and maintained in their original local format
- Kaggle versions are generated on-demand only when publishing/updating datasets
- The migration process is automated and doesn't require ongoing updates unless notebook structure changes significantly

Updates to the migration tool are only needed if:
- Kaggle changes its platform requirements
- New notebooks are added to the analysis suite
- Significant changes to notebook structure require path transformation updates

## Structure

```
exploratory_data_analysis/
├── README.md                    # This file
├── initiatives_campaigns/       # Signature campaign analysis
│   ├── eci_analysis_signatures.ipynb
│   └── README.md
├── initiatives_responses/       # Response data exploration
│   ├── eci_analysis_responses.ipynb
│   └── README.md
└── kaggle_output/               # Migration tools & output
    ├── kaggle_migration.py
    └── requirements.txt
```