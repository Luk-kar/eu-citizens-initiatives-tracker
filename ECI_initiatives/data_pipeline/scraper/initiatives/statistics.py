# Python Standard Library
import csv
import datetime
import os
from collections import Counter
from typing import Dict, List

# Local modules
from .consts import CSV_FILENAME, LOG_MESSAGES
from .scraper_logger import logger


def display_completion_summary(
    start_scraping: str,
    initiative_data: list[Dict[str, str]],
    saved_page_paths: list,
    failed_urls: list,
) -> None:
    """Display final completion summary with statistics."""
    stats = gather_scraping_statistics(start_scraping, initiative_data, failed_urls)
    display_summary_info(start_scraping, saved_page_paths, stats)
    display_results_and_files(start_scraping, saved_page_paths, failed_urls, stats)


LOG_SUMMARY = LOG_MESSAGES["summary_scraping"]


def gather_scraping_statistics(
    start_scraping: str, initiative_data: list, failed_urls: list
) -> dict:
    """Gather all statistics needed for the completion summary."""

    # Count initiatives by status from CSV
    current_status_counter = Counter()
    url_list_file = f"initiatives/{start_scraping}/list/{CSV_FILENAME}"

    if os.path.exists(url_list_file):

        with open(url_list_file, "r", encoding="utf-8") as file:

            reader = csv.DictReader(file)

            for row in reader:
                if row["current_status"]:
                    current_status_counter[row["current_status"]] += 1

    # Count downloaded files
    pages_dir = f"initiatives/{start_scraping}/initiatives"

    downloaded_files_count = 0

    if os.path.exists(pages_dir):

        # Iterate through year directories and count HTML files
        for year_dir in os.listdir(pages_dir):

            year_path = os.path.join(pages_dir, year_dir)

            if os.path.isdir(year_path):

                html_files = [f for f in os.listdir(year_path) if f.endswith(".html")]
                downloaded_files_count += len(html_files)

    return {
        "status_counter": current_status_counter,
        "downloaded_count": downloaded_files_count,
        "total_initiatives": len(initiative_data) if initiative_data else 0,
        "failed_count": len(failed_urls),
    }


def display_summary_info(
    start_scraping: str, saved_page_paths: list, stats: dict
) -> None:
    """Display the main summary information and statistics."""
    logger.info(LOG_SUMMARY["divider_line"])
    logger.info(LOG_SUMMARY["scraping_complete"])
    logger.info(LOG_SUMMARY["divider_line"])

    logger.info(
        LOG_SUMMARY["completion_timestamp"].format(
            timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
    )
    logger.info(LOG_SUMMARY["start_time"].format(start_scraping=start_scraping))
    logger.info(
        LOG_SUMMARY["total_pages_scraped"].format(page_count=len(saved_page_paths))
    )
    logger.info(
        LOG_SUMMARY["total_initiatives_found"].format(
            total_initiatives=stats["total_initiatives"]
        )
    )

    logger.info(LOG_SUMMARY["initiatives_by_category"])
    for status, count in stats["status_counter"].items():
        logger.info(f"- {status}: {count}")


def display_results_and_files(
    start_scraping: str, saved_page_paths: list, failed_urls: list, stats: dict
) -> None:
    """Display download results and file location information."""
    logger.info(
        LOG_SUMMARY["pages_downloaded"].format(
            downloaded_count=stats["downloaded_count"],
            total_initiatives=stats["total_initiatives"],
        )
    )

    if stats["failed_count"]:
        logger.error(
            LOG_SUMMARY["failed_downloads"].format(failed_count=stats["failed_count"])
        )
        for failed_url in failed_urls:
            logger.error(LOG_SUMMARY["failed_url"].format(failed_url=failed_url))
    else:
        logger.info(LOG_SUMMARY["all_downloads_successful"])

    logger.info(LOG_SUMMARY["files_saved_in"].format(start_scraping=start_scraping))
    logger.info(LOG_SUMMARY["main_page_sources"])
    for i, path in enumerate(saved_page_paths, 1):
        logger.info(LOG_SUMMARY["page_source"].format(page_num=i, path=path))

    logger.info(LOG_SUMMARY["divider_line"])
