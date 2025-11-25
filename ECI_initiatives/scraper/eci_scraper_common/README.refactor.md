# Refactoring scrapers
A refactoring plan to extract common scraping logic from three independent programs (`initiatives`, `responses`, `responses_followup_website`) into a shared library `eci_scraper_common`.

Advantages of doing so, from the most important to the least:
-  simplifying creating new scrapers
-  simplifying testing
-  simplifying maintenance
  
## Current State

### Code Duplication

The following logic patterns are duplicated across all three scraper programs:

1. **Browser Management** - Chrome WebDriver initialization, configuration, and lifecycle management
2. **Retry & Rate Limiting** - Exponential/quadratic backoff, rate limit detection, wait strategies
3. **File Operations** - Directory creation, HTML validation/prettification, CSV operations
4. **Logging Infrastructure** - Dual handlers (file + console), formatters
5. **Configuration Management** - Timing constants, browser options, rate limit indicators
6. **Error Handling** - Custom exceptions, error categorization, structured logging
7. **HTML Processing** - BeautifulSoup parsing, validation, malformed content detection
8. **Wait & Timing Utilities** - Random interval generation, dynamic content waits
9.  **URL & Metadata Handling** - Registration number normalization, year extraction
10. **Path Management** - Script directory detection, timestamp-based structure

### Code parts that will NOT be covered as a shared library by design
  
**Rather DO NOT** extract to common logic:
- **HTML/DOM selectors** - CSS selectors, XPath expressions (website-specific)
- **Data extraction logic** - Field mapping, text parsing rules unique to each page
- **Navigation patterns** - Click sequences, form submissions specific to each workflow
- **Validation rules** - Data quality checks specific to each data source
- **Business logic** - Initiative/response/followup-specific processing rules

Due to:
- Over-abstraction risks: Some logic is too specific to each scraper's target website structure, even if it **now** looks the same
- Brittle nature: Web scraping code changes frequently when websites update their HTML/DOM structure
- Maintenance overhead: Abstracting frequently-changing code can create more problems than it solves
  
### Existing Test Coverage

```
ECI_initiatives/tests/scraper/
├── initiatives/           # 6 test files
├── responses/            # 7 test files  
└── responses_followup_website/  # 6 test files
Total: 16 behaviour tests + 3 end-to-end tests
```

**Test Categories:**
- **Behaviour Tests:** Unit/integration tests for specific functionality
- **End-to-End Tests:** Full workflow validation with file system verification, limited scraping scope to increase speed and avoid target server-side effects.

### Targeted Test Coverage

Creating `ECI_initiatives/tests/scraper/eci_scraper_common/` for shared library tests, then refactor existing test suites to remove duplicated coverage of common functionality, keeping only scraper-specific tests.

## Proposed Architecture

### Common Library Structure

```
ECI_initiatives/scraper/eci_scraper_common/
├── __init__.py
├── browser/
│   ├── __init__.py
│   ├── initialization.py      # Browser setup and configuration
│   └── management.py           # Lifecycle management, context managers
├── config/
│   ├── __init__.py
│   ├── constants.py            # Shared constants (timing, limits)
│   └── chrome_options.py       # Browser option configurations
├── retry/
│   ├── __init__.py
│   ├── strategies.py           # Retry logic with backoff algorithms
│   └── rate_limiting.py        # Rate limit detection and handling
├── file_ops/
│   ├── __init__.py
│   ├── directories.py          # Directory creation and management
│   ├── html_operations.py      # HTML validation, prettification, saving
│   └── csv_operations.py       # CSV reading/writing utilities
├── logging/
│   ├── __init__.py
│   ├── logger_factory.py       # Logger initialization patterns
│   └── formatters.py           # Log format configurations
├── errors/
│   ├── __init__.py
│   └── exceptions.py           # Custom exception classes
└── utils/
    ├── __init__.py
    ├── # Whatever fits
    ...
```