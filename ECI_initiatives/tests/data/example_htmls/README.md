# ECI Test Data

## Overview

This directory contains scraped HTML pages from the European Citizens' Initiative (ECI) website for **development and testing purposes only**.

## Purpose

- **Avoid server overload**: Prevents excessive requests to ECI servers during development
- **Consistent testing**: Provides stable test data for scraper development
- **Offline development**: Enables testing without internet connectivity

## Structure

```
├── initiatives/          # Individual ECI initiative pages
├── listings/             # ECI listing pages (first/last page examples)
└── eci_status_initiatives.csv  # Status classification data
```

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
- Integration testing
- or anything else needed static data

**Note**: Always verify scraper logic against live data before production deployment.