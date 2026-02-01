# ECI Initiatives Test Suite

This directory contains a comprehensive **pytest** suite designed to validate the functionality, reliability, and resilience of the ECI scraping and extraction pipeline. The tests cover everything from unit-level behavior to full end-to-end integration.

## 📂 Test Structure

The test suite mirrors the source code structure, separated into `scraper`, `extractor`, and `merger` domains.

```text
tests/
├── conftest.py              # Global fixtures (temp dirs, logging)
├── consts.py                # Test constants & paths
├── run_tests.py             # Custom test runner script
├── requirements.test.txt    # Test-specific dependencies
│
├── data/                    # Static test data (fixtures)
│   └── example_htmls/       # Real HTML samples (initiatives, responses, errors)
│
├── scraper/                 # Scraper tests
│   ├── initiatives/         # Core scraper tests
│   │   ├── behaviour/       # Unit tests (parsing, navigation)
│   │   └── end_to_end/      # Integration tests (file creation)
│   ├── responses/           # Response scraper tests
│   └── responses_followup_website/
│
├── extractor/               # Extractor tests
│   ├── initiatives/         # Initiative data extraction
│   └── responses/           # Response analysis logic
│
└── merger/                  # Data merging tests
    └── responses/           # CSV merging logic
```

## 🧪 Test Categories

| Category | Path | Purpose |
| :--- | :--- | :--- |
| **Behaviour** | `*/behaviour/` | Unit tests for specific functions (e.g., regex parsing, error handling). Fast and isolated. |
| **End-to-End** | `*/end_to_end/` | Integration tests that verify file I/O, directory creation, and full workflow execution. |

## ⚠️ Critical Warning

**Use Caution with End-to-End Tests**

Some tests, particularly those in `*/end_to_end/`, may attempt to connect to live URLs to verify network logic. Running the full suite repeatedly can trigger the EU server's rate limiting (HTTP 429).

- **Preferred**: Run `behaviour` tests during development (offline/mocked).
- **Restricted**: Run `end-to-end` tests only when necessary (e.g., pre-merge checks).
- **Mocking**: Most network calls are mocked, but ensure you are not running live scraping loops unintentionally.

## 🛠️ Usage

A dedicated `run_tests.py` script simplifies test execution. It handles path resolution and argument combinations automatically.

### basic Usage

Navigate to the `tests` directory or run from the project root:

```bash
# Run ALL tests
python tests/run_tests.py

# Run all scraper tests
python tests/run_tests.py --scraper

# Run all extractor tests
python tests/run_tests.py --extractor
```

### Specific Scenarios

**By Component:**
```bash
# Run only initiative scraper tests
python tests/run_tests.py --scraper --initiatives

# Run only response scraper tests
python tests/run_tests.py --scraper --responses
```

**By Test Type:**
```bash
# Run only behaviour tests (fast)
python tests/run_tests.py --behaviour

# Run only end-to-end tests (slower, I/O heavy)
python tests/run_tests.py --end-to-end
```

**Advanced Filtering:**
```bash
# Run only behaviour tests for the responses scraper
python tests/run_tests.py --scraper --responses --behaviour

# Run a specific file directly
python tests/run_tests.py scraper/responses/behaviour/test_link_extraction.py
```

### Options

| Flag | Description |
| :--- | :--- |
| `--no-verbose` | Disable detailed output. |
| `--no-stop` | Don't stop on the first failure. |
| `--coverage` | Generate an HTML coverage report. |
| `--markers` | Run tests with specific pytest markers (e.g., `not slow`). |

## 📦 Dependencies

Install test-specific requirements before running:

```bash
pip install -r tests/requirements.test.txt
```

Key libraries:
- `pytest`: Core testing framework.
- `pytest-cov`: Coverage reporting.
- `beautifulsoup4`: HTML parsing for test assertions.
```