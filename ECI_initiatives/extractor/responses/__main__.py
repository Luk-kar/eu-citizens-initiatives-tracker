#!/usr/bin/env python3
"""
ECI Responses Data Scraper - European Citizens' Initiative Response HTML Parser
Processes scraped response HTML files and extracts Commission response data to CSV
"""

import os
import csv
import re
import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Union, Tuple
from dataclasses import dataclass, asdict

from bs4 import BeautifulSoup

from .responses_logger import ResponsesExtractorLogger
from .processor import ECIResponseDataProcessor


def main():
    """Main entry point"""
    
    processor = ECIResponseDataProcessor()
    processor.run()


if __name__ == "__main__":
    main()
