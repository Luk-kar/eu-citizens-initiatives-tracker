# ECI Scraper Pipeline

Comprehensive web scraping pipeline for **European Citizens' Initiatives (ECI)** data, from core registry → Commission responses → dedicated follow-up websites.

## 📋 Scrapers (Run in Sequence)

| Module | Purpose | Dependencies | Key Output |
|--------|---------|--------------|------------|
| `initiatives` | Core ECI listings & detail pages | None | `initiatives_list.csv`, `initiatives/` HTML |
| `responses` | Commission response pages | `initiatives` | `responses_list.csv`, `responses/` HTML |
| `responses_followup_website` | Dedicated follow-up sites | `responses` | `responses_followup_website/` HTML |

## 🧪 Testing

For comprehensive testing documentation and instructions, see the [main project testing documentation](../../README.ECI_initiatives.md#-testing).

**Quick test:**

```bash
cd ECI_initiatives/tests
deactivate  # Exit production venv if active
uv venv
uv pip install -r requirements.test.txt
python run_tests.py --scraper
```
## 🛠️ Prerequisites


- **Python 3.8+**
- **Google Chrome** + **ChromeDriver**
- Dependencies: `pip install -r ECI_initiatives/data_pipeline/requirements.prod.txt`

## 🚀 Quick Start

```bash
cd ECI_initiatives
uv venv && uv pip install -r data_pipeline/requirements.prod.txt
source .venv/bin/activate  # Linux/macOS

# Run pipeline sequentially
python -m data_pipeline.scraper.initiatives
python -m data_pipeline.scraper.responses
python -m data_pipeline.scraper.responses_followup_website
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

- [Initiatives Scraper](./initiatives/README.sc_initiatives.md)
- [Responses Scraper](./responses/README.sc_responses.md)
- [Follow-up Website Scraper](./responses_followup_website/README.sc_followup.md)