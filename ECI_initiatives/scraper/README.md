```markdown
# ECI Scraper Pipeline

Comprehensive web scraping pipeline for **European Citizens' Initiatives (ECI)** data, from core registry → Commission responses → dedicated follow-up websites.

## 📋 Scrapers (Run in Sequence)

| Module | Purpose | Dependencies | Key Output |
|--------|---------|--------------|------------|
| `initiatives` | Core ECI listings & detail pages | None | `initiatives_list.csv`, `initiatives/` HTML |
| `responses` | Commission response pages | `initiatives` | `responses_list.csv`, `responses/` HTML |
| `responses_followup_website` | Dedicated follow-up sites | `responses` | `responses_followup_website/` HTML |

## 🛠️ Prerequisites

- **Python 3.8+**
- **Google Chrome** + **ChromeDriver**
- Dependencies: `pip install -r ECI_initiatives/requirements.prod.txt`

## 🚀 Quick Start

```bash
cd ECI_initiatives
uv venv && uv pip install -r requirements.prod.txt
source .venv/bin/activate  # Linux/macOS

# Run pipeline sequentially
python -m scraper.initiatives
python -m scraper.responses
python -m scraper.responses_followup_website
```

## 📦 Data Pipeline

```
data/YYYY-MM-DD_HH-MM-SS/
├── initiatives_list.csv      # Core dataset
├── responses_list.csv        # Response metadata
├── initiatives/              # Raw initiative HTML
├── responses/                # Commission response HTML
└── responses_followup_website/  # Follow-up site HTML
└── logs/                     # Execution logs
```

**Full details in each module's README.md**