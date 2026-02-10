"""
ECI Data Scraper - European Citizens' Initiative HTML Parser
Processes scraped HTML files and extracts structured data to CSV
"""

# initiatives extractor

from .processor import ECIDataProcessor


def main():
    """Main entry point"""

    processor = ECIDataProcessor()

    processor.run()


if __name__ == "__main__":
    main()
