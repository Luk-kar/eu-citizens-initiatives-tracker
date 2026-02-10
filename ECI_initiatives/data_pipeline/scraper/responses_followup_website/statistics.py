"""
Statistics gathering and display for scraping completion summary.
"""

import datetime
from typing import List, Dict
import logging

from .consts import LOG_MESSAGES


class ScrapingStatistics:
    """Gather and display statistics for scraping session."""

    def __init__(self, start_scraping: str, followup_website_dir: str):
        """
        Initialize statistics tracker.

        Args:
            start_scraping: Timestamp when scraping started
            followup_website_dir: Directory where followup websites were saved
        """
        self.start_scraping = start_scraping
        self.followup_website_dir = followup_website_dir
        self.logger = logging.getLogger("ECIFollowupWebsiteScraper")

    def display_completion_summary(
        self,
        followup_urls: List[Dict[str, str]],
        failed_items: List[Dict[str, str]],
        downloaded_count: int,
    ) -> None:
        """
        Display comprehensive completion summary.

        Args:
            followup_urls: List of all followup URL dictionaries
            failed_items: List of items that failed to download
            downloaded_count: Number of successfully downloaded pages
        """
        self._display_summary_header()
        self._display_download_results(
            len(followup_urls), downloaded_count, failed_items
        )
        self._display_file_locations()

    def _display_summary_header(self) -> None:
        """Display summary header with completion timestamp."""
        self.logger.info(LOG_MESSAGES["divider_line"])
        self.logger.info(LOG_MESSAGES["scraping_complete"])
        self.logger.info(LOG_MESSAGES["divider_line"])

        completion_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.logger.info(
            LOG_MESSAGES["completion_timestamp"].format(timestamp=completion_time)
        )
        self.logger.info(
            LOG_MESSAGES["start_time"].format(start_scraping=self.start_scraping)
        )

    def _display_download_results(
        self, total_urls: int, downloaded_count: int, failed_items: List[Dict[str, str]]
    ) -> None:
        """
        Display download results statistics.

        Args:
            total_urls: Total number of followup URLs found
            downloaded_count: Number of successful downloads
            failed_items: List of failed items
        """
        self.logger.info(LOG_MESSAGES["total_urls_found"].format(count=total_urls))
        self.logger.info(
            LOG_MESSAGES["pages_downloaded"].format(
                downloaded_count=downloaded_count, total_count=total_urls
            )
        )

        if failed_items:
            self.logger.warning(
                LOG_MESSAGES["failed_downloads"].format(failed_count=len(failed_items))
            )
            for item in failed_items:
                self.logger.warning(
                    LOG_MESSAGES["failed_url"].format(failed_url=item["url"])
                )
        else:
            self.logger.info(LOG_MESSAGES["all_downloads_successful"])

    def _display_file_locations(self) -> None:
        """Display information about where files were saved."""
        self.logger.info(
            LOG_MESSAGES["files_saved_in"].format(path=self.followup_website_dir)
        )
        self.logger.info(LOG_MESSAGES["divider_line"])


def display_completion_summary(
    start_scraping: str,
    followup_urls: List[Dict[str, str]],
    failed_items: List[Dict[str, str]],
    downloaded_count: int,
    followup_website_dir: str,
) -> None:
    """
    Convenience function to display completion summary.

    Args:
        start_scraping: Timestamp when scraping started
        followup_urls: List of all followup URL dictionaries
        failed_items: List of items that failed to download
        downloaded_count: Number of successfully downloaded pages
        followup_website_dir: Directory where followup websites were saved
    """
    stats = ScrapingStatistics(start_scraping, followup_website_dir)
    stats.display_completion_summary(followup_urls, failed_items, downloaded_count)
