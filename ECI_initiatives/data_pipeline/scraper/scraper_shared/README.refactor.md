# Refactoring scrapers
A refactoring plan to extract common scraping logic from three independent programs (`initiatives`, `responses`, `responses_followup_website`) into a shared library `scraper_shared`.

Advantages of doing so, from the most important to the least:
-  simplifying creating new scrapers
-  simplifying testing
-  simplifying maintenance of the scrapers
  
## Current State

### Code Duplication

The following logic patterns are duplicated across all three scraper programs:

1. **Browser Management** - Chrome WebDriver initialization, configuration, and lifecycle management
2. **Retry & Rate Limiting** - Exponential/quadratic backoff, rate limit detection, wait strategies
3. **File Operations** - Directory creation, HTML validation/prettification, CSV operations
4. **Logging Infrastructure** - Dual handlers (file + console), formatters
5. **Error Handling** - Custom exceptions, error categorization, structured logging
6. **HTML Processing** - BeautifulSoup parsing, validation, malformed content detection
7. **Wait & Timing Utilities** - Random interval generation, dynamic content waits
8.  **URL & Metadata Handling** - Registration number normalization, year extraction
9.  **Path Management** - Script directory detection, timestamp-based structure

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
├── initiatives/
├── responses/  
└── responses_followup_website/
```

**Test Categories:**
- **Behaviour Tests:** Unit/integration tests for specific functionality
- **End-to-End Tests:** Full workflow validation with file system verification, limited scraping scope to increase speed and avoid target server-side effects.