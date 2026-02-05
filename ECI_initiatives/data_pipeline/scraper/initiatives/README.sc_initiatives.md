# ECI Initiatives Scraper

Web scraper designed to extract data from the **European Citizens' Initiative (ECI)** register. It automates the retrieval of initiative details, status updates, and signature collection data using a hybrid approach of **Selenium** (for dynamic content navigation) and **BeautifulSoup** (for parsing).

## 📂 Project Structure

The module is organized as a Python package with the following key components:

- **`crawler.py`**: Core logic for navigating the pagination and extracting data.
- **`browser.py`**: Manages the Selenium WebDriver instance (Headless Chrome).
- **`consts.py`**: Configuration for URLs, timeouts, file paths, and scraping parameters.
- **`data_parser.py`**: Parsers for extracting structured data from raw HTML.
- **`file_ops.py`**: Handles file system operations (saving HTML, CSVs).
- **`css_selectors.py`**: Centralized storage for CSS selectors for the site.
- **`scraper_logger.py`**: Custom logging configuration.
- 
## 🚀 Flow

1. **Initialization**:
   - Generates a unique run timestamp (e.g., `2024-02-01_10-00-00`) to create a dedicated output directory.
   - Launches a headless Chrome browser with anti-detection options.

2. **Listings navigation & extraction loop**:
   - Navigates to the ECI "Find initiative" listing page.
   - **Waits** for dynamic JavaScript content to load (configurable via `WAIT_DYNAMIC_CONTENT`).
   - **Saves** the raw HTML of the current listing page into the `listings/` folder for traceability.
   - **Parses** the listing HTML to extract structured fields (URL, status, registration number, signature counts) into memory.

3. **Initiative page downloads**:
   - For each initiative URL discovered from the listings, requests/opens the initiative detail page.
   - **Saves** each initiative’s raw HTML into the `initiatives/` folder (typically named using a `{year}_{number}.html` pattern).

4. **Pagination strategy**:
   - Scans for the "Next" page button using centralized CSS selectors.
   - If found: Clicks the button, waits a random interval (to mimic human behavior), and repeats the loop.
   - If not found: Assumes the last page is reached and terminates.

5. **Resilience & recovery**:
   - Monitors page content for rate-limiting indicators (e.g., "429 - Too Many Requests").
   - Triggers a retry/backoff mechanism if blocking is detected.

6. **Finalization**:
   - Writes the accumulated dataset to `initiatives_list.csv`.
   - Closes the browser and logs a summary of the run.


## 🛠️ Prerequisites

Ensure you have the following installed:
- **Python 3.8+**
- **Google Chrome** (latest version)
- **ChromeDriver** (matching your Chrome version)

### Python Dependencies

Install the required libraries using the production requirements file:

```bash
pip install -r ECI_initiatives/data_pipeline/requirements.prod.txt
```

## ⚙️ Configuration

Key settings can be modified in `consts.py`:

| Constant | Description | Default |
| :--- | :--- | :--- |
| `WAIT_DYNAMIC_CONTENT` | Time to wait for JS to load | `1.5 - 1.9s` |
| `WAIT_BETWEEN_PAGES` | Delay between pagination clicks | `1.0 - 2.0s` |
| `CHROME_OPTIONS` | Selenium flags (headless, etc.) | `['--headless', '--no-sandbox']` |
| `CSV_FILENAME` | Output filename for data | `initiatives_list.csv` |

## 📦 Output Structure

When the scraper runs, it generates a `data` directory (relative to the script root) with the following structure:

```text
data/
└── YYYY-MM-DD_HH-MM-SS/         # Timestamped run folder
    ├── logs/
    │   └── scraper.log          # Execution logs
    ├── listings/                # Raw HTML of listing pages
    │   ├── Find_initiative_..._page_001.html
    │   └── ...
    ├── initiatives/             # Individual initiatives
    │   ├── 2012/
    │   │   ├── 2012_000001_en.html
    │   │   └── ...
    │   └── ...
    └── initiatives_list.csv     # Main dataset
```

## 📊 Data Fields

**Purpose**: The `initiatives_list.csv` serves as the **primary analysis dataset** for ECI initiatives, providing a complete catalog of all initiatives with status, progress metrics, and timestamps for quantitative analysis and dashboard development.

The generated CSV (`initiatives_list.csv`) typically includes:
- `url`: Direct link to the initiative.
- `current_status`: E.g., "Open for collection", "Registered".
- `registration_number`: Unique ECI ID.
- `signature_collection`: Count of verified signatures.
- `datetime`: Date of registration or status change.

Here is the updated **Usage** section, showing how to activate the shell environment first and then run the scraper.

## 🖥️ Usage

It is recommended to use **[uv](https://github.com/astral-sh/uv)** for fast dependency management and execution.

Navigate to the `ECI_initiatives` directory:
```bash
cd ECI_initiatives
```

### 1. Setup Environment
Create the virtual environment and install dependencies:
```bash
uv venv
uv pip install -r /ECI_initiatives/data_pipeline/requirements.prod.txt
```

### 2. Activate Shell
Load the virtual environment into your current shell session:

**Linux/macOS:**
```bash
source .venv/bin/activate
```

**Windows:**
```powershell
.venv\Scripts\activate
```

### 3. Run the Scraper
Once the environment is active (you should see `(.venv)` in your prompt), run the module:

```bash
python -m data_pipeline.scraper.initiatives
```