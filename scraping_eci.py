import os
import datetime
import requests
from bs4 import BeautifulSoup
import time
import re
import random
import csv
from typing import Dict, Tuple
from collections import Counter

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options


def scrape_eci_initiatives() -> str:
    """Main function to scrape European Citizens' Initiative data.

    Returns:
        str: Timestamp string of when scraping started
    """

    start_scraping = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    print(f"Starting scraping at: {start_scraping}")

    base_url = "https://citizens-initiative.europa.eu"

    list_dir = f"initiatives/{start_scraping}/list"
    pages_dir = f"initiatives/{start_scraping}/pages"
    setup_scraping_dirs(list_dir, pages_dir)

    driver = initialize_browser()

    try:
        page_source, main_page_path = scrape_initiatives_page(
            driver, base_url, list_dir
        )

    finally:
        driver.quit()  # Close the browser

    initiative_data = parse_initiatives_list_data(page_source, base_url)

    if initiative_data:
        failed_urls = save_and_download_initiatives(
            list_dir, pages_dir, initiative_data
        )
    else:
        print("No initiatives found to classify or download")
        failed_urls = []

    display_completion_summary(
        start_scraping, initiative_data, main_page_path, failed_urls
    )

    return start_scraping


def initialize_browser() -> webdriver.Chrome:
    """Initialize Chrome WebDriver with headless options.

    Returns:
        webdriver.Chrome: Configured Chrome WebDriver instance
    """

    # Setup Chrome options for headless browsing
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in background
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument(
        "--disable-dev-shm-usage"
    )  # https://stackoverflow.com/a/69175552 # VM's limitations

    print("Initializing browser...")
    driver = webdriver.Chrome(options=chrome_options)

    return driver


def setup_scraping_dirs(list_dir: str, pages_dir: str) -> None:
    """Create necessary directories for scraping output.

    Args:
        list_dir: Path to directory for storing list files
        pages_dir: Path to directory for storing individual page files
    """

    os.makedirs(list_dir, exist_ok=True)
    os.makedirs(pages_dir, exist_ok=True)


def save_and_download_initiatives(
    list_dir: str, pages_dir: str, initiative_data: list[Dict[str, str]]
) -> Tuple[int, list]:
    """Save initiative data to CSV and download individual pages.

    Args:
        list_dir: Directory path for saving CSV files
        pages_dir: Directory path for saving HTML pages
        initiative_data: List of initiative dictionaries

    Returns:
        Tuple containing number of successful downloads and list of failed URLs
    """

    url_list_file = os.path.join(list_dir, "initiatives_list.csv")

    with open(url_list_file, "w", encoding="utf-8", newline="") as f:
        header = [
            "url",
            "current_status",
            "registration_number",
            "signature_collection",
            "datetime",
        ]
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerows(initiative_data)

    print(f"Initiative data saved to: {url_list_file}")

    print("\nDownloading individual initiative pages...")
    updated_data, failed_urls = download_initiative_pages(pages_dir, initiative_data)

    # Update CSV with download timestamps
    with open(url_list_file, "w", encoding="utf-8", newline="") as f:
        header = [
            "url",
            "current_status",
            "registration_number",
            "signature_collection",
            "datetime",
        ]
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerows(updated_data)

    return failed_urls


def download_initiative_pages(pages_dir, initiative_data):
    """Download individual initiative pages and update datetime stamps with retry logic.

    Args:
        pages_dir: Directory path for saving HTML pages
        initiative_data: List of initiative dictionaries

    Returns:
        Tuple containing updated data list, count of successful downloads, and list of failed URLs
    """

    updated_data = []
    failed_urls = []  # New: track failed download URLs

    for i, row in enumerate(initiative_data):
        url = row["url"]
        max_retries = 5
        retry_wait_base = 1 * random.uniform(0.7, 1.0)  # initial wait time in seconds
        retry_count = 0
        success = False

        while retry_count <= max_retries and not success:
            try:
                print(f"Downloading {i+1}/{len(initiative_data)}: {url}")
                response = requests.get(url)
                response.raise_for_status()

                # Extract year and number from URL for filename
                parts = url.rstrip("/").split("/")
                year = parts[-2]
                number = parts[-1]

                # Generate directory under pages_dir for year
                year_dir = os.path.join(pages_dir, year)
                os.makedirs(year_dir, exist_ok=True)

                # Create filename with year and number to avoid overwriting
                file_name = f"{year}_{number}.html"
                file_path = os.path.join(year_dir, file_name)

                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(response.text)

                successful_download_time = datetime.datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                row["datetime"] = successful_download_time

                success = True
                print(f"✅ Successfully downloaded: {file_name}")

            except requests.exceptions.HTTPError as e:
                if response.status_code == 429:
                    retry_count += 1
                    if retry_count <= max_retries:
                        wait_time = retry_wait_base * retry_count
                        print(
                            f"⚠️  Received 429 Too Many Requests. Retrying {retry_count}/{max_retries} in {wait_time} seconds..."
                        )
                        time.sleep(wait_time)
                    else:
                        print(
                            f"❌ Failed to download after {max_retries} retries (429 errors): {url}"
                        )
                        failed_urls.append(url)
                else:
                    print(f"❌ HTTP error downloading {url}: {e}")
                    failed_urls.append(url)
                    break
            except Exception as e:
                print(f"❌ Error downloading {url}: {e}")
                failed_urls.append(url)
                break

        if not success and retry_count > max_retries:
            print(f"❌ Exhausted all {max_retries} retries for: {url}")
            if url not in failed_urls:  # Avoid duplicates
                failed_urls.append(url)

        # Append the updated row regardless of success
        updated_data.append(row)

        # Sleep after each successful attempt to avoid overload
        if success:
            time.sleep(0.5)

    return updated_data, failed_urls


def scrape_initiatives_page(
    driver: webdriver.Chrome, base_url: str, list_dir: str
) -> Tuple[str, str]:
    """Load page, wait for elements, and save HTML source.

    Args:
        driver: Chrome WebDriver instance
        base_url: Base URL for the website
        list_dir: Directory path for saving the main page

    Returns:
        Tuple containing page source HTML and path to saved file
    """

    route_find_initiative = "/find-initiative_en"
    url_find_initiative = base_url + route_find_initiative

    print(f"Loading page: {url_find_initiative}")
    driver.get(url_find_initiative)

    # Wait for the page to load
    wait = WebDriverWait(driver, 30)

    # Wait for initiative elements to be present
    try:
        cards_initiative_selector = "div.ecl-content-block__title a.ecl-link"
        wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, cards_initiative_selector))
        )

        pagination_for_other_cards = (
            "ul.ecl-pagination__list li.ecl-pagination__item a.ecl-pagination__link"
        )
        wait.until(
            EC.presence_of_element_located(
                (
                    By.CSS_SELECTOR,
                    pagination_for_other_cards,
                )
            )
        )
        print("Initiatives loaded successfully")
    except:
        print("No initiatives found or timeout - continuing with current content")

    # Additional wait to ensure all dynamic content is loaded
    random_time = random.uniform(1.5, 1.9)
    time.sleep(random_time)

    # Save the main page HTML source

    page_source = driver.page_source
    initiative_list_page_name = "Find_initiative_European_Citizens_Initiative"
    main_page_path = os.path.join(list_dir, f"{initiative_list_page_name}.html")

    with open(main_page_path, "w", encoding="utf-8") as f:
        pretty_html = BeautifulSoup(page_source, "html.parser").prettify()
        f.write(pretty_html)

    print(f"Main page saved to: {main_page_path}")
    return page_source, main_page_path


def parse_initiatives_list_data(
    page_source: str, base_url: str
) -> list[Dict[str, str]]:
    """Parse HTML page source and extract initiatives data.

    Args:
        page_source: HTML source code of the page
        base_url: Base URL for the website

    Returns:
        List of dictionaries containing initiatives data
    """

    print("Parsing saved main page for initiatives links...")

    soup = BeautifulSoup(page_source, "html.parser")
    initiative_data = []

    for content_block in soup.select(
        "div.ecl-content-block.ecl-content-item__content-block"
    ):
        # Extract URL from title link
        title_link = content_block.select_one("div.ecl-content-block__title a.ecl-link")
        if not title_link or not title_link.get("href"):
            continue

        href = title_link.get("href")
        if not href.startswith("/initiatives/details/"):
            continue

        # TODO "https://citizens-initiative.europa.eu" as global const
        full_url = base_url + href

        # Extract metadata
        current_status = ""
        registration_number = ""
        signature_collection = ""

        meta_labels = content_block.select(
            "span.ecl-content-block__secondary-meta-label"
        )

        for label in meta_labels:

            text = label.get_text(strip=True)

            if text.startswith("Current status:"):
                current_status = text.replace("Current status:", "").strip()

            elif text.startswith("Registration number:"):
                registration_number = text.replace("Registration number:", "").strip()

            elif "signature collection" in text.lower():
                signature_collection = text.strip()

        initiative_data.append(
            {
                "url": full_url,
                "current_status": current_status,
                "registration_number": registration_number,
                "signature_collection": signature_collection,
                "datetime": "",  # Empty during scraping
            }
        )

    print(f"Found {len(initiative_data)} initiative entries")
    return initiative_data


def display_completion_summary(
    start_scraping: str,
    initiative_data: list[Dict[str, str]],
    main_page_path: str,
    failed_urls: list,
) -> None:
    """Display final completion summary with statistics.

    Args:
        start_scraping: Start time timestamp string
        initiative_data: List of initiative data dictionaries
        main_page_path: Path to the saved main page file
        failed_urls: List of URLs that failed to download
    """
    from collections import Counter

    # Display total of initiatives by categories as `current_status` from the csv file
    current_status_counter = Counter()
    url_list_file = f"initiatives/{start_scraping}/list/initiatives_list.csv"

    # Read categories 'current_status' from the CSV
    if os.path.exists(url_list_file):
        with open(url_list_file, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row["current_status"]:
                    current_status_counter[row["current_status"]] += 1

    # Read the downloaded_count data directly from the directory with downloaded pages
    pages_dir = f"initiatives/{start_scraping}/pages"
    downloaded_files_count = 0

    if os.path.exists(pages_dir):

        downloaded_files_count = len(
            [
                f
                for subdir, _, files in os.walk(pages_dir)
                for f in files
                if f.endswith(".html")
            ]
        )

    total_initiatives_count = len(initiative_data) if initiative_data else 0
    failed_downloads_count = len(failed_urls)
    div_line = "=" * 60

    print("\n" + div_line)
    print("🎉 SCRAPING FINISHED! 🎉")
    print(div_line)
    print(
        f"Scraping completed at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    print(f"Start time: {start_scraping}")
    print(f"Total initiatives found: {total_initiatives_count}")

    # Display the counts by current_status category
    print("Initiatives by category (current_status):")
    for status, count in current_status_counter.items():
        print(f"- {status}: {count}")

    print(f"Pages downloaded: {downloaded_files_count}/{total_initiatives_count}")

    if failed_downloads_count:
        print(f"Failed downloads: {failed_downloads_count}")
        for failed_url in failed_urls:
            print(f" - {failed_url}")
    else:
        print("✅ All downloads successful!")

    print(f"Files saved in: initiatives/{start_scraping}")
    print(f"Main page source: {main_page_path}")
    print(div_line)


# Run the scraper
if __name__ == "__main__":
    scrape_eci_initiatives()
