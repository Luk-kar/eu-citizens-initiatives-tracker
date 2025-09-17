import os
import datetime
import requests
from bs4 import BeautifulSoup
import time
import re
import random
import csv

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options


def scrape_eci_initiatives():

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

    initiative_data = parse_initiative_data(page_source)

    if initiative_data:
        downloaded_count = save_and_download_initiatives(
            list_dir, pages_dir, initiative_data
        )

    else:
        downloaded_count = 0
        print("No initiatives found to classify or download")

    display_completion_summary(
        start_scraping, initiative_data, downloaded_count, main_page_path
    )

    return start_scraping


def initialize_browser():

    # Setup Chrome options for headless browsing
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in background
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument(
        "--disable-dev-shm-usage"
    )  # https://stackoverflow.com/a/69175552

    print("Initializing browser...")
    driver = webdriver.Chrome(options=chrome_options)

    return driver


def setup_scraping_dirs(list_dir, pages_dir):
    os.makedirs(list_dir, exist_ok=True)
    os.makedirs(pages_dir, exist_ok=True)


def save_and_download_initiatives(list_dir, pages_dir, initiative_data):

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
    updated_data, downloaded_count = download_initiative_pages(
        pages_dir, initiative_data
    )

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

    return downloaded_count


def download_initiative_pages(pages_dir, initiative_data):
    """Download individual initiative pages and update datetime stamps"""

    downloaded_count = 0
    updated_data = []

    for i, row in enumerate(initiative_data):
        url = row["url"]
        try:
            print(f"Downloading {i+1}/{len(initiative_data)}: {url}")
            response = requests.get(url)
            response.raise_for_status()

            # Create safe filename from URL
            page_name = url.split("/")[-1] or url.split("/")[-2]

            if not page_name:
                page_name = f"unknown_initiative_{i+1}"

            page_name = re.sub(r"[^\w\-_.]", "_", page_name) + ".html"
            file_path = os.path.join(pages_dir, page_name)

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(response.text)

            successful_download_time = datetime.datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            row["datetime"] = successful_download_time
            downloaded_count += 1

            time.sleep(0.5)  # To avoid server overload

        except Exception as e:
            print(f"Error downloading {url}: {e}")

        updated_data.append(row)

    return updated_data, downloaded_count


def scrape_initiatives_page(driver, base_url, list_dir):
    """Load page, wait for elements, and save HTML source"""

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


def parse_initiative_data(page_source):
    """Parse HTML page source and extract initiative data"""

    print("Parsing saved main page for initiative links...")

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

        full_url = "https://citizens-initiative.europa.eu" + href

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
    start_scraping, initiative_data, downloaded_count, main_page_path
):
    """Display final completion summary with statistics"""

    ___ = "=" * 60

    print("\n" + ___)
    print("🎉 SCRAPING FINISHED! 🎉")
    print(___)
    print(
        f"Scraping completed at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    print(f"Start time: {start_scraping}")
    print(f"Total initiatives found: {len(initiative_data) if initiative_data else 0}")
    print(f"Pages downloaded: {downloaded_count}")
    print(f"Files saved in: initiatives/{start_scraping}/")
    print(f"Main page source: {main_page_path}")
    print(___)


# Run the scraper
if __name__ == "__main__":
    scrape_eci_initiatives()
