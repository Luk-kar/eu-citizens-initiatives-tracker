#!/usr/bin/env python3
"""
ECI Responses Data Scraper - European Citizens' Initiative Response HTML Parser
Processes scraped response HTML files and extracts Commission response data to CSV
"""

from .processor import ECIResponseDataProcessor


def main():
    """Main entry point"""
    
    processor = ECIResponseDataProcessor()
    processor.run()


if __name__ == "__main__":
    main()
