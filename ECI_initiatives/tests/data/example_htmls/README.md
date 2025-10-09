# ECI Test Data

## Overview

This directory contains scraped HTML pages from the European Citizens' Initiative (ECI) website for **development and testing purposes only**.

## Purpose

- **Avoid server overload**: Prevents excessive requests to ECI servers during development
- **Consistent testing**: Provides stable test data for scraper development
- **Offline development**: Enables testing without internet connectivity
- **Commission response analysis**: Categorized responses for outcome evaluation

## Structure

```
├── errors/
│   └── 429_too_many_requests_error.html    # Simplified rate limiting error page for testing
├── initiatives/                             # Individual ECI initiative pages
│   ├── 2019_000007_en.html
│   ├── 2023_000008_en.html
│   ├── 2024_000004_en.html
│   ├── 2024_000005_en.html
│   ├── 2024_000007_en.html
│   ├── 2025_000002_en.html
│   ├── 2025_000003_en.html
│   └── eci_status_initiatives.csv          # Status classification data
├── listings/                                # ECI listing pages
│   ├── first_page.html                     # First page of initiatives list
│   ├── last_page.html                      # Last page of initiatives list
│   └── initiatives_list.csv                # Parsed listing data
└── responses/                               # Commission response pages by outcome
    ├── eci_initiatives_commission_responses.csv
    ├── partial_success/                    # Initiatives with limited success
    │   ├── 2012/2012_000007_en.html       # Stop vivisection
    │   ├── 2017/2017_000002_en.html       # Ban glyphosate
    │   ├── 2019/2019_000016_en.html       # Save bees and farmers
    │   ├── 2020/2020_000001_en.html       # Stop Finning
    │   ├── 2021/2021_000006_en.html       # Save Cruelty Free Cosmetics
    │   └── 2022/2022_000002_en.html       # Fur Free Europe
    ├── rejection/                          # Initiatives rejected by Commission
    │   ├── 2012/2012_000005_en.html       # One of us
    │   ├── 2017/2017_000004_en.html       # Minority SafePack
    │   └── 2019/2019_000007_en.html       # Cohesion policy
    ├── strong_commitment_delayed/          # Positive but delayed responses
    │   └── 2018/2018_000004_en.html       # End the Cage Age
    └── strong_legislative_success/         # Successful with new legislation
        └── 2012/2012_000003_en.html       # Right2Water
```

## Response Categories

### Partial Success (6 initiatives)
Initiatives where the Commission provided commitments or limited action without full legislative proposals.

### Rejection (3 initiatives)
Initiatives where the Commission concluded no new legislation would be proposed.

### Strong Legislative Success (1 initiative)
Initiatives that resulted in actual new legislation being adopted.

### Strong Commitment Delayed (1 initiative)
Initiatives where the Commission committed to legislation but missed deadlines.

## Maintenance

**⚠️ Manual updates required**
- Pages should be refreshed periodically during active development
- No automated updating logic implemented due to:
  - Unpredictable website structure
  - Unpredictable website behavior
  - Rate limiting considerations

## Usage

These files serve as fixtures for:
- Parser testing
- CSS selector validation
- Data extraction verification
- Error handling testing (rate limiting, malformed HTML)
- Integration testing
- Commission response categorization
- Statistical analysis of ECI outcomes
- Any other needs requiring static data

## CSV Files

### initiatives/eci_status_initiatives.csv
Contains status classification data for individual initiatives.

### listings/initiatives_list.csv
Parsed data from initiative listing pages.

### responses/eci_initiatives_commission_responses.csv
Complete categorization of Commission responses including:
- URL
- Registration number
- Title
- Category (Partial Success, Rejection, etc.)
- Success level assessment
- Commission response summary

**Note**: Always verify scraper logic against live data before production deployment.
