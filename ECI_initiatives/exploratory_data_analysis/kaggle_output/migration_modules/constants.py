"""
Constants and templates for Kaggle migration
"""

from pathlib import Path
from typing import NamedTuple


class ProjectPaths(NamedTuple):
    """Container for project path configuration"""

    base_path: Path
    output_path: Path
    signatures_nb: Path
    responses_nb: Path
    eci_root: Path
    data_path: Path


def setup_project_paths(script_file: Path, base_path: Path = None) -> ProjectPaths:
    """
    Setup all project paths based on the script location

    Args:
        script_file: Path to the main script (__file__)
        base_path: Optional override for base_path

    Returns:
        ProjectPaths namedtuple with all configured paths
    """
    if base_path is None:
        base_path = script_file.parent.parent
    else:
        base_path = Path(base_path)

    output_path = script_file.parent

    # Define notebook paths
    signatures_nb = (
        base_path / "initiatives_campaigns" / "eci_analysis_signatures.ipynb"
    )
    responses_nb = base_path / "initiatives_responses" / "eci_analysis_responses.ipynb"

    # Data path
    eci_root = base_path.parent
    data_path = eci_root / "data"

    return ProjectPaths(
        base_path=base_path,
        output_path=output_path,
        signatures_nb=signatures_nb,
        responses_nb=responses_nb,
        eci_root=eci_root,
        data_path=data_path,
    )


# Default project paths - calculated directly from this module's location
# constants.py is in: ECI_initiatives/exploratory_data_analysis/kaggle_output/migration_modules/constants.py
_CONSTANTS_FILE = Path(__file__)  # constants.py
_MIGRATION_MODULES_DIR = _CONSTANTS_FILE.parent  # migration_modules/
_KAGGLE_OUTPUT_DIR = _MIGRATION_MODULES_DIR.parent  # kaggle_output/
_EXPLORATORY_DIR = _KAGGLE_OUTPUT_DIR.parent  # exploratory_data_analysis/
_ECI_ROOT = _EXPLORATORY_DIR.parent  # ECI_initiatives/

PROJECT_PATHS = ProjectPaths(
    base_path=_EXPLORATORY_DIR,
    output_path=_KAGGLE_OUTPUT_DIR,
    signatures_nb=_EXPLORATORY_DIR
    / "initiatives_campaigns"
    / "eci_analysis_signatures.ipynb",
    responses_nb=_EXPLORATORY_DIR
    / "initiatives_responses"
    / "eci_analysis_responses.ipynb",
    eci_root=_ECI_ROOT,
    data_path=_ECI_ROOT / "data",
)


# Image replacements mapping (Filename -> Raw GitHub URL)
IMAGE_REPLACEMENTS = {
    "eci_take_initiative_banner.png": "https://raw.githubusercontent.com/Luk-kar/eu-citizens-initiatives-tracker/main/ECI_initiatives/exploratory_data_analysis/initiatives_campaigns/images/eci_take_initiative_banner.png",
    "eci_participation_campaign.jpg": "https://raw.githubusercontent.com/Luk-kar/eu-citizens-initiatives-tracker/main/ECI_initiatives/exploratory_data_analysis/initiatives_responses/images/eci_participation_campaign.jpg",
    "european_commission_logo.svg": "https://raw.githubusercontent.com/Luk-kar/eu-citizens-initiatives-tracker/main/ECI_initiatives/exploratory_data_analysis/initiatives_responses/images/european_commission_logo.svg",
}

# Kaggle environment setup code injected into notebooks
# Simplified: Only includes Path import and path detection logic
KAGGLE_SETUP_CODE = [
    "# Kaggle Environment Setup\n",
    "from pathlib import Path\n",
    "\n",
    "\n",
    "# Data paths - supports both Kaggle and local environments\n",
    "kaggle_path = Path('/kaggle/input/european-citizens-initiatives-2026')\n",
    "local_path = Path('./csv_files')\n",
    "\n",
    "\n",
    "if kaggle_path.exists():\n",
    "    KAGGLE_INPUT = kaggle_path\n",
    "elif local_path.exists():\n",
    "    KAGGLE_INPUT = local_path\n",
    "else:\n",
    "    raise FileNotFoundError(\n",
    "        'Data directory not found. Expected one of:\\n'\n",
    "        f'  - Kaggle: {kaggle_path}\\n'\n",
    "        f'  - Local: {local_path}\\n'\n",
    "        'Please ensure CSV files are available in one of these locations.'\n",
    "    )\n",
    "\n",
    "\n",
    "if KAGGLE_INPUT == local_path:\n",
    "    print(f'📁 Using data from: {KAGGLE_INPUT}')\n",
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
1. Update placeholders:
   - Replace "YOUR_USERNAME" with your Kaggle username in:
     * dataset-metadata.json

2. Upload CSV files to Kaggle:
   - Go to: [https://www.kaggle.com/datasets](https://www.kaggle.com/datasets)
   - Click "New Dataset"
   - Upload the CSV files from: kaggle_output/csv_files/
   - Use the dataset-metadata.json file for configuration

3. Create notebooks on Kaggle:
   - Upload: {sig_nb_name}
   - Upload: {resp_nb_name}
   - Kaggle will automatically configure metadata (accelerator, GPU, internet, dataset links)

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
- Notebooks support both Kaggle and local environments (./csv_files/)

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

NOTEBOOK_LINK_REPLACEMENTS = {
    "https://github.com/Luk-kar/eu-citizens-initiatives-tracker/blob/main"
    "/ECI_initiatives/exploratory_data_analysis"
    "/initiatives_responses/eci_analysis_responses.ipynb": (
        "https://www.kaggle.com/code/lukkardata/eci-commission-response"
    ),
    "https://github.com/Luk-kar/eu-citizens-initiatives-tracker/blob/main"
    "/ECI_initiatives/exploratory_data_analysis"
    "/initiatives_campaigns/eci_analysis_signatures.ipynb": (
        "https://www.kaggle.com/code/lukkardata/eci-signatures-collection"
    ),
}
