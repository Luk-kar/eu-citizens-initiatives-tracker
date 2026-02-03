#!/usr/bin/env python3
"""
ECI Data Scraper - European Citizens' Initiative HTML Parser
Processes scraped HTML files and extracts structured data to CSV
"""

# python
import os
import csv
import re
import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Union, Tuple
from dataclasses import dataclass, asdict

# third-party
from bs4 import BeautifulSoup

# initiatives extractor
from .initiatives_logger import InitiativesExtractorLogger
from .processor import ECIDataProcessor


def main():
    """Main entry point"""

    processor = ECIDataProcessor()
    processor.run()


if __name__ == "__main__":
    main()
