"""
Statistics gathering and display for scraping completion summary.
"""
import datetime
from typing import List, Dict

from .consts import LOG_MESSAGES, RESPONSES_DIR
from .scraper_logger import logger


class ScrapingStatistics:
    """Gather and display statistics for scraping session."""
    
    def __init__(self, start_scraping: str):
        """
        Initialize statistics tracker.
        
        Args:
            start_scraping: Timestamp when scraping started
        """
        self.start_scraping = start_scraping
    
    def display_completion_summary(
        self,
        response_links: List[Dict[str, str]],
        failed_urls: List[str],
        downloaded_count: int
    ) -> None:
        """
        Display comprehensive completion summary.
        
        Args:
            response_links: List of all response link dictionaries
            failed_urls: List of URLs that failed to download
            downloaded_count: Number of successfully downloaded pages
        """
        self._display_summary_header()
        self._display_download_results(len(response_links), downloaded_count, failed_urls)
        self._display_file_locations()
    
    def _display_summary_header(self) -> None:
        """Display summary header with completion timestamp."""
        logger.info(LOG_MESSAGES["divider_line"])
        logger.info(LOG_MESSAGES["scraping_complete"])
        logger.info(LOG_MESSAGES["divider_line"])
        
        completion_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info(LOG_MESSAGES["completion_timestamp"].format(timestamp=completion_time))
        logger.info(LOG_MESSAGES["start_time"].format(start_scraping=self.start_scraping))
    
    def _display_download_results(
        self,
        total_links: int,
        downloaded_count: int,
        failed_urls: List[str]
    ) -> None:
        """
        Display download results statistics.
        
        Args:
            total_links: Total number of response links found
            downloaded_count: Number of successful downloads
            failed_urls: List of failed URLs
        """
        logger.info(LOG_MESSAGES["total_links_found"].format(count=total_links))
        logger.info(LOG_MESSAGES["pages_downloaded"].format(
            downloaded_count=downloaded_count,
            total_count=total_links
        ))
        
        if failed_urls:
            logger.warning(LOG_MESSAGES["failed_downloads"].format(failed_count=len(failed_urls)))
            for url in failed_urls:
                logger.warning(LOG_MESSAGES["failed_url"].format(failed_url=url))
        else:
            logger.info(LOG_MESSAGES["all_downloads_successful"])
    
    def _display_file_locations(self) -> None:
        """Display information about where files were saved."""
        logger.info(LOG_MESSAGES["files_saved_in"].format(path=RESPONSES_DIR))
        logger.info(LOG_MESSAGES["divider_line"])


def display_completion_summary(
    start_scraping: str,
    response_links: List[Dict[str, str]],
    failed_urls: List[str],
    downloaded_count: int
) -> None:
    """
    Convenience function to display completion summary.
    
    Args:
        start_scraping: Timestamp when scraping started
        response_links: List of all response link dictionaries
        failed_urls: List of URLs that failed to download
        downloaded_count: Number of successfully downloaded pages
    """
    stats = ScrapingStatistics(start_scraping)
    stats.display_completion_summary(response_links, failed_urls, downloaded_count)
