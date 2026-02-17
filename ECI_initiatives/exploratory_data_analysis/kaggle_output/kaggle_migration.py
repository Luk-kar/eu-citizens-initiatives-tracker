#!/usr/bin/env python3

"""

Kaggle Notebook Migration Script for ECI Analysis

--------------------------------------------------

Converts local Jupyter notebooks to Kaggle-compatible format by:

1. Replacing local file paths with Kaggle input paths

2. Replacing local image paths with hosted GitHub raw links

3. Removing dynamic folder detection logic

4. Clearing all notebook outputs using nbconvert

Requirements:

pip install jupyter nbconvert

Usage:

python kaggle_migration.py

Output:

- eci_analysis_signatures.kaggle.ipynb

- eci_analysis_responses.kaggle.ipynb

- dataset-metadata.json

- migration_report.txt

- migration.log

"""

import json
import logging
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import shutil
import csv
import re

# Image replacements mapping (Filename -> Raw GitHub URL)
IMAGE_REPLACEMENTS = {
    "eci_take_initiative_banner.png": "https://raw.githubusercontent.com/Luk-kar/eu-citizens-initiatives-tracker/main/ECI_initiatives/exploratory_data_analysis/initiatives_campaigns/images/eci_take_initiative_banner.png",
    "eci_participation_campaign.jpg": "https://raw.githubusercontent.com/Luk-kar/eu-citizens-initiatives-tracker/main/ECI_initiatives/exploratory_data_analysis/initiatives_responses/images/eci_participation_campaign.jpg",
    "european_commission_logo.svg": "https://raw.githubusercontent.com/Luk-kar/eu-citizens-initiatives-tracker/main/ECI_initiatives/exploratory_data_analysis/initiatives_responses/images/european_commission_logo.svg",
}

# Kaggle environment setup code injected into notebooks
KAGGLE_SETUP_CODE = [
    "# Kaggle Environment Setup\n",
    "from pathlib import Path\n",
    "import pandas as pd\n",
    "import numpy as np\n",
    "import plotly.graph_objects as go\n",
    "import plotly.express as px\n",
    "from datetime import datetime\n",
    "import warnings\n",
    "warnings.filterwarnings('ignore')\n",
    "\n",
    "# Data paths for Kaggle\n",
    "KAGGLE_INPUT = Path('/kaggle/input/eci-initiatives')\n",
    "\n",
]

# Kaggle dataset metadata template
DATASET_METADATA_TEMPLATE = {
    "title": "European Citizens' Initiatives (ECI) Data",
    "id": "YOUR_USERNAME/eci-initiatives",
    "licenses": [{"name": "CC-BY-4.0"}],
    "keywords": [
        "politics",
        "europe",
        "european-union",
        "democracy",
        "citizen-participation",
        "policy-analysis",
        "government",
        "european-citizen-initiative",
    ],
    "description": """# European Citizens' Initiatives Dataset

## About the Data

This dataset contains comprehensive information about **European Citizens' Initiatives (ECIs)** from 2012 to 2026. The ECI is a mechanism that allows EU citizens to directly propose legislation to the European Commission.

## Dataset Contents

### 1. ECI Initiatives (`eci_initiatives_*.csv`)
- **127 initiatives** across 15 years
- Registration dates, collection periods, signature counts
- Geographic distribution across 27 EU member states
- Policy areas, funding information, organizer details
- Success/failure status

### 2. Commission Responses (`eci_merger_responses_and_followup_*.csv`)
- **11 successful ECIs** that received Commission responses
- Legislative outcomes and policy changes
- Timeline of institutional progress (Commission, Parliament, Council)
- Hearing dates, plenary sessions, Commission decisions

## Data Source

Official European Commission ECI Register: [https://citizens-initiative.europa.eu/](https://citizens-initiative.europa.eu/)

## Update Schedule

This dataset is updated quarterly to include new initiatives and response updates.

## License

CC BY 4.0 - European Commission

## Related Resources

- **Analysis Notebooks**: 
  - [Signature Collection Analysis](https://www.kaggle.com/code/YOUR_USERNAME/eci-analysis-signatures)
  - [Commission Response Analysis](https://www.kaggle.com/code/YOUR_USERNAME/eci-analysis-responses)

## Data Dictionary

See the notebooks for detailed column descriptions and usage examples.
""",
}

# Migration report template
MIGRATION_REPORT_TEMPLATE = """
Kaggle Migration Report
=======================
Generated: {timestamp}

Data Sources:
-------------
Data Folder: {data_folder}
Initiatives CSV: {initiatives_csv}
Responses CSV: {responses_csv}

Output Cells:
-------------
Status: {outputs_status}

Post-Migration Steps:
---------------------
1. Upload CSV files to Kaggle:
   - Go to: [https://www.kaggle.com/datasets](https://www.kaggle.com/datasets)
   - Click "New Dataset"
   - Upload the CSV files from: kaggle_output/csv_files/
   - Use the dataset-metadata.json file for configuration

2. Create notebooks on Kaggle:
   - Upload: {sig_nb_name}
   - Upload: {resp_nb_name}
   - Kaggle will automatically configure metadata (accelerator, GPU, internet, dataset links)

3. Update placeholders:
   - Replace "YOUR_USERNAME" with your Kaggle username in:
     * dataset-metadata.json

4. Test notebooks:
   - Run "Restart & Run All" on Kaggle
   - Verify all visualizations render
   - Check data loading works correctly
   - Verify that images (banners/logos) load correctly from GitHub

Files Generated:
----------------
- {sig_nb_name}
- {resp_nb_name}
- dataset-metadata.json
- csv_files/{initiatives_csv}
- csv_files/{responses_csv}
- migration_report.txt (this file)
- {log_filename}

Notes:
------
- Original notebooks preserved in parent directories
- All local paths converted to Kaggle input paths
- Local image paths replaced with GitHub raw links
- Dynamic folder detection removed
- Most recent CSV files automatically selected
- Output cells cleared using nbconvert
- Kaggle metadata will be configured automatically when you upload
- CSV files copied to csv_files/ for easy upload

Success! ✓
"""

# Success log messages
SUCCESS_LOG_MESSAGES = {
    "header": "=" * 60,
    "title": "✓ Migration Complete!",
    "sections": {
        "generated_files": "\nGenerated Files:",
        "data_sources": "\nData Sources:",
        "next_steps": "\nNext Steps:",
    },
    "next_steps_items": [
        " → Review migration_report.txt for detailed instructions",
        " → Update 'YOUR_USERNAME' placeholders in all files",
        " → Upload CSV files from csv_files/ directory to Kaggle",
        " → Upload notebooks to Kaggle",
    ],
}


class KaggleMigrator:
    """Handles migration of ECI notebooks to Kaggle format"""

    def __init__(self, base_path: Path = None):
        if base_path is None:
            # Assume script is run from kaggle_output directory
            self.base_path = Path(__file__).parent.parent
        else:
            self.base_path = Path(base_path)

        self.output_path = Path(__file__).parent

        # Define paths
        self.signatures_nb = (
            self.base_path / "initiatives_campaigns" / "eci_analysis_signatures.ipynb"
        )
        self.responses_nb = (
            self.base_path / "initiatives_responses" / "eci_analysis_responses.ipynb"
        )

        # Look for data in parent ECI_initiatives directory
        self.eci_root = self.base_path.parent
        self.data_path = self.eci_root / "data"

        # Verify data path exists
        if not self.data_path.exists():
            raise FileNotFoundError(
                f"Data directory not found at {self.data_path}\n"
                f"Expected structure: ECI_initiatives/data/YYYY-MM-DD_HH-MM-SS/"
            )

        # Setup logging
        self.log_filename = None
        self.logger = self._setup_logging()

    def _setup_logging(self) -> logging.Logger:
        """Configure logging to console AND file"""
        self.log_filename = f"migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

        # Create handlers
        c_handler = logging.StreamHandler()
        f_handler = logging.FileHandler(self.log_filename, mode="w", encoding="utf-8")

        # Set levels
        c_handler.setLevel(logging.INFO)
        f_handler.setLevel(logging.DEBUG)

        # Create formatters and add it to handlers
        c_format = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S"
        )
        f_format = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
        )
        c_handler.setFormatter(c_format)
        f_handler.setFormatter(f_format)

        # Add handlers to the logger
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)
        logger.addHandler(c_handler)
        logger.addHandler(f_handler)

        return logger

    def check_nbconvert_available(self) -> bool:
        """Check if nbconvert is installed"""
        try:
            result = subprocess.run(
                ["jupyter", "nbconvert", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                version = result.stdout.strip()
                self.logger.info(f"Found nbconvert: {version}")
                return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        self.logger.warning("nbconvert not found - outputs will not be cleared")
        self.logger.warning("Install with: pip install jupyter nbconvert")
        return False

    def load_notebook(self, notebook_path: Path) -> Dict:
        """Load a Jupyter notebook as JSON"""
        with open(notebook_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_notebook(self, notebook: Dict, output_path: Path):
        """Save notebook with proper formatting"""
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(notebook, f, indent=1, ensure_ascii=False)

    def get_latest_data_folder(self) -> Path:
        """
        Find the latest timestamped data folder from ECI_initiatives/data/

        Returns:
            Path object to the most recent data folder (e.g., 2026-02-16_10-23-16)
        """
        data_folders = [d for d in self.data_path.iterdir() if d.is_dir()]
        if not data_folders:
            raise FileNotFoundError(
                f"No data folders found in {self.data_path}\n"
                f"Expected timestamped folders like: 2026-02-16_10-23-16"
            )

        # Sort by folder name (timestamp format ensures chronological order)
        latest = max(data_folders, key=lambda d: d.name)
        self.logger.info(f"Found latest data folder: {latest.name}")
        return latest

    def validate_csv(self, csv_path: Path) -> bool:
        """
        Validate that a CSV file is not empty and has valid format

        Args:
            csv_path: Path to the CSV file

        Returns:
            True if valid, raises ValueError if invalid
        """
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        if csv_path.stat().st_size == 0:
            raise ValueError(f"CSV file is empty: {csv_path.name}")

        try:
            with open(csv_path, "r", encoding="utf-8", newline="") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                if not header:
                    raise ValueError(f"CSV file has no header: {csv_path.name}")

                if len(header) < 2:
                    self.logger.warning(
                        f"CSV {csv_path.name} has only {len(header)} columns, suspicious format"
                    )

                try:
                    next(reader)
                except csv.Error:
                    pass
        except UnicodeDecodeError:
            raise ValueError(f"CSV file is not valid UTF-8: {csv_path.name}")
        except Exception as e:
            raise ValueError(f"CSV file error: {csv_path.name} ({e})")

        return True

    def find_most_recent_csv(self, data_folder: Path, pattern: str) -> Path:
        """
        Find the most recent CSV file matching a pattern in the data folder
        """
        csv_files = list(data_folder.glob(f"{pattern}*.csv"))
        if not csv_files:
            raise FileNotFoundError(
                f"No CSV files found matching pattern '{pattern}' in {data_folder}"
            )

        most_recent = max(csv_files, key=lambda f: f.name)
        self.validate_csv(most_recent)
        self.logger.info(f"Found most recent {pattern}CSV: {most_recent.name}")
        return most_recent

    def find_required_csvs(self, data_folder: Path) -> Tuple[Path, Path]:
        """
        Find the most recent required CSV files in the data folder
        """
        try:
            initiatives_csv = self.find_most_recent_csv(data_folder, "eci_initiatives_")
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Could not find eci_initiatives CSV in {data_folder}\n"
                f"Expected file like: eci_initiatives_2026-02-16_10-33-56.csv"
            )

        try:
            responses_csv = self.find_most_recent_csv(
                data_folder, "eci_merger_responses_and_followup_"
            )
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Could not find eci_merger_responses CSV in {data_folder}\n"
                f"Expected file like: eci_merger_responses_and_followup_2026-02-16_10-35-18.csv"
            )

        return initiatives_csv, responses_csv

    def replace_path_code(
        self, source_lines: List[str], csv_filename: str, notebook_type: str
    ) -> List[str]:
        """Replace local path detection code with Kaggle paths"""
        new_lines = []
        skip_until_imports = False

        for i, line in enumerate(source_lines):
            # Skip the entire path detection block
            if "from pathlib import Path" in line and i < 20:
                skip_until_imports = True
                # Add Kaggle-compatible imports and path setup
                new_lines.extend(KAGGLE_SETUP_CODE)
                continue

            # Skip original path detection logic
            if skip_until_imports:
                if "import" in line and "from" not in line and "Path" not in line:
                    skip_until_imports = False
                elif any(
                    keyword in line
                    for keyword in [
                        "root_path",
                        "data_directory",
                        "data_folder",
                        "latest_folder",
                        "folder_date",
                        "file_date",
                    ]
                ):
                    continue

            # Replace CSV loading
            if "pd.read_csv" in line and (
                "eci_initiatives" in line or "eci_merger" in line
            ):
                if "eci_initiatives" in line and "merger" not in line:
                    new_lines.append(
                        f"df_initiatives = pd.read_csv(KAGGLE_INPUT / '{csv_filename}')\n"
                    )
                    self.logger.debug(f"Replaced CSV loading: {line.strip()}")
                elif "eci_merger" in line:
                    new_lines.append(
                        f"df_responses = pd.read_csv(KAGGLE_INPUT / '{csv_filename}')\n"
                    )
                    self.logger.debug(f"Replaced CSV loading: {line.strip()}")
                continue

            # Replace path references in print statements
            if "base_data_path" in line or "path_initiatives" in line:
                new_lines.append(
                    line.replace("base_data_path.resolve()", "KAGGLE_INPUT").replace(
                        "path_initiatives.resolve()", "KAGGLE_INPUT"
                    )
                )
                continue

            # Skip folder/file date calculations
            if any(
                keyword in line
                for keyword in ["folder_date", "file_date", "datetime.strptime"]
            ):
                if "print" not in line:
                    continue

            new_lines.append(line)

        return new_lines

    def replace_image_links(self, source_lines: List[str]) -> List[str]:
        """
        Replace local image paths with raw GitHub URLs.
        Example: images/banner.png -> https://raw.githubusercontent.com/.../banner.png
        """
        new_lines = []

        for line in source_lines:
            updated_line = line
            for filename, raw_url in IMAGE_REPLACEMENTS.items():
                if filename in updated_line:
                    # Regex to match common markdown image patterns:
                    # 1. ![Alt](images/filename.png)
                    # 2. <img src="images/filename.png">
                    # We simply look for the filename and replace the whole path preceeding it if it looks like a path
                    # This naive replacement is safer: just replace the known filename if it's in a path context

                    # Check for markdown link: ](anything/filename)
                    if f"]" in updated_line and f"{filename})" in updated_line:
                        updated_line = re.sub(
                            r"\]\([^)]*" + re.escape(filename) + r"\)",
                            f"]({raw_url})",
                            updated_line,
                        )
                        self.logger.debug(
                            f"Replaced markdown image link for {filename}"
                        )

                    # Check for HTML src: src="anything/filename"
                    if f'src="' in updated_line and f'{filename}"' in updated_line:
                        updated_line = re.sub(
                            r'src="[^"]*' + re.escape(filename) + r'"',
                            f'src="{raw_url}"',
                            updated_line,
                        )
                        self.logger.debug(f"Replaced HTML image source for {filename}")

            new_lines.append(updated_line)

        return new_lines

    def clear_notebook_outputs(self, notebook_path: Path) -> bool:
        """Clear all outputs from a notebook using nbconvert"""
        try:
            result = subprocess.run(
                [
                    "jupyter",
                    "nbconvert",
                    "--ClearOutputPreprocessor.enabled=True",
                    "--inplace",
                    str(notebook_path),
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                self.logger.info(f"Cleared outputs: {notebook_path.name}")
                return True
            else:
                self.logger.warning(
                    f"Failed to clear outputs for {notebook_path.name}: {result.stderr}"
                )
                return False
        except subprocess.TimeoutExpired:
            self.logger.warning(f"Timeout clearing outputs for {notebook_path.name}")
            return False
        except Exception as e:
            self.logger.error(f"Error clearing outputs for {notebook_path.name}: {e}")
            return False

    def migrate_notebook(
        self, notebook_path: Path, csv_file: Path, notebook_type: str
    ) -> Path:
        """Migrate a single notebook to Kaggle format"""
        self.logger.info(f"Migrating {notebook_type} notebook: {notebook_path.name}")

        # Load notebook
        notebook = self.load_notebook(notebook_path)
        self.logger.debug(f"Loaded {notebook_path.name}")

        # Process cells
        cells_modified = 0
        images_modified = 0

        for i, cell in enumerate(notebook["cells"]):
            # Process Code Cells
            if cell["cell_type"] == "code":
                original_source = cell["source"]
                if any(
                    "Path" in line or "pd.read_csv" in line or "root_path" in line
                    for line in original_source
                ):
                    cell["source"] = self.replace_path_code(
                        original_source, csv_file.name, notebook_type
                    )
                    cells_modified += 1

            # Process Markdown Cells (Image Replacement)
            elif cell["cell_type"] == "markdown":
                original_source = cell["source"]
                new_source = self.replace_image_links(original_source)
                if new_source != original_source:
                    cell["source"] = new_source
                    images_modified += 1

        self.logger.info(
            f"Modified {cells_modified} code cells and {images_modified} markdown image links"
        )

        # Save migrated notebook with .kaggle.ipynb extension
        original_name = notebook_path.stem
        output_filename = f"{original_name}.kaggle.ipynb"
        output_path = self.output_path / output_filename

        self.save_notebook(notebook, output_path)
        self.logger.info(f"Saved migrated notebook: {output_filename}")

        return output_path

    def create_dataset_metadata(self, initiatives_csv: Path, responses_csv: Path):
        """Create Kaggle dataset metadata file"""
        metadata = DATASET_METADATA_TEMPLATE.copy()
        metadata["resources"] = [
            {
                "path": initiatives_csv.name,
                "description": "Complete dataset of all registered European Citizens' Initiatives with signatures, countries, dates, and outcomes",
            },
            {
                "path": responses_csv.name,
                "description": "Commission responses and follow-up actions for successful ECIs including legislative outcomes",
            },
        ]

        output_path = self.output_path / "dataset-metadata.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        self.logger.info("Created dataset metadata: dataset-metadata.json")
        return output_path

    def copy_csvs_to_output(self, initiatives_csv: Path, responses_csv: Path):
        """Copy CSV files to output directory for easy upload"""
        output_dir = self.output_path / "csv_files"
        output_dir.mkdir(exist_ok=True)

        # Copy files
        initiatives_dest = output_dir / initiatives_csv.name
        responses_dest = output_dir / responses_csv.name

        shutil.copy2(initiatives_csv, initiatives_dest)
        shutil.copy2(responses_csv, responses_dest)

        self.logger.info(f"Copied CSVs to: {output_dir.name}/")
        return output_dir

    def create_migration_report(
        self,
        data_folder: Path,
        initiatives_csv: Path,
        responses_csv: Path,
        outputs_cleared: bool,
    ):
        """Create a detailed migration report"""
        outputs_status = (
            "✓ Cleared using nbconvert"
            if outputs_cleared
            else "⚠️ Skipped (nbconvert not available)"
        )
        sig_nb_name = f"{self.signatures_nb.stem}.kaggle.ipynb"
        resp_nb_name = f"{self.responses_nb.stem}.kaggle.ipynb"

        report_content = MIGRATION_REPORT_TEMPLATE.format(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            data_folder=data_folder,
            initiatives_csv=initiatives_csv.name,
            responses_csv=responses_csv.name,
            outputs_status=outputs_status,
            sig_nb_name=sig_nb_name,
            resp_nb_name=resp_nb_name,
            log_filename=self.log_filename,
        )

        report_path = self.output_path / "migration_report.txt"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_content)

        self.logger.info("Migration report saved to: migration_report.txt")
        return report_path

    def run(self):
        """Execute the complete migration process"""
        self.logger.info(SUCCESS_LOG_MESSAGES["header"])
        self.logger.info("ECI Notebooks → Kaggle Migration Tool")
        self.logger.info(SUCCESS_LOG_MESSAGES["header"])
        self.logger.info(f"Log file: {self.log_filename}")

        # Check for nbconvert
        has_nbconvert = self.check_nbconvert_available()

        try:
            # Find latest data folder
            data_folder = self.get_latest_data_folder()

            # Find most recent CSV files
            initiatives_csv, responses_csv = self.find_required_csvs(data_folder)

            # Migrate notebooks
            self.logger.info("\nStarting notebook migration...")
            sig_output = self.migrate_notebook(
                self.signatures_nb, initiatives_csv, "signatures"
            )
            resp_output = self.migrate_notebook(
                self.responses_nb, responses_csv, "responses"
            )

            # Clear outputs using nbconvert
            outputs_cleared = False
            if has_nbconvert:
                self.logger.info("\nClearing notebook outputs...")
                sig_cleared = self.clear_notebook_outputs(sig_output)
                resp_cleared = self.clear_notebook_outputs(resp_output)
                outputs_cleared = sig_cleared and resp_cleared

                if outputs_cleared:
                    self.logger.info("All outputs cleared successfully")
                else:
                    self.logger.warning("Some outputs could not be cleared")

            # Create supporting files
            self.logger.info("\nCreating supporting files...")
            self.create_dataset_metadata(initiatives_csv, responses_csv)
            csv_dir = self.copy_csvs_to_output(initiatives_csv, responses_csv)
            self.create_migration_report(
                data_folder, initiatives_csv, responses_csv, outputs_cleared
            )

            # Summary
            self.logger.info("\n" + SUCCESS_LOG_MESSAGES["header"])
            self.logger.info(SUCCESS_LOG_MESSAGES["title"])
            self.logger.info(SUCCESS_LOG_MESSAGES["header"])
            self.logger.info(SUCCESS_LOG_MESSAGES["sections"]["generated_files"])
            self.logger.info(f"  1. {sig_output.name}")
            self.logger.info(f"  2. {resp_output.name}")
            self.logger.info(f"  3. dataset-metadata.json")
            self.logger.info(f"  4. {csv_dir.name}/{initiatives_csv.name}")
            self.logger.info(f"  5. {csv_dir.name}/{responses_csv.name}")
            self.logger.info(f"  6. migration_report.txt")
            self.logger.info(f"  7. {self.log_filename}")
            self.logger.info(SUCCESS_LOG_MESSAGES["sections"]["data_sources"])
            self.logger.info(f"  → Folder: {data_folder.name}")
            self.logger.info(f"  → Initiatives: {initiatives_csv.name}")
            self.logger.info(f"  → Responses: {responses_csv.name}")
            self.logger.info(SUCCESS_LOG_MESSAGES["sections"]["next_steps"])
            for step in SUCCESS_LOG_MESSAGES["next_steps_items"]:
                self.logger.info(f"  {step}")
            self.logger.info(SUCCESS_LOG_MESSAGES["header"] + "\n")

        except Exception as e:
            self.logger.error(f"Migration failed: {e}", exc_info=True)
            return False

        return True


def main():
    """Main execution function"""
    migrator = KaggleMigrator()
    success = migrator.run()
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
