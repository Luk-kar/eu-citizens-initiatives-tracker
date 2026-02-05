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

## Quick Start

Navigate to the specific analysis directory and follow its README for environment setup and notebook launch instructions.

## Structure

```
exploratory_data_analysis/
├── README.md                    # This file
├── initiatives_campaigns/       # Signature campaign analysis
│   ├── eci_analysis_signatures.ipynb
│   └── README.md
└── initiatives_responses/       # Response data exploration
    ├── eci_analysis_responses.ipynb
    └── README.md
```