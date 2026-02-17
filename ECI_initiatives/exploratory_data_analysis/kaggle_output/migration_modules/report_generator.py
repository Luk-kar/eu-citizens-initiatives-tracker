"""
Report and metadata generation utilities
"""

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path

from .constants import DATASET_METADATA_TEMPLATE, MIGRATION_REPORT_TEMPLATE


class ReportGenerator:
    """Handles creation of migration reports and Kaggle metadata"""

    def __init__(self, output_path: Path, logger: logging.Logger):
        self.output_path = output_path
        self.logger = logger

    def create_dataset_metadata(self, initiatives_csv: Path, responses_csv: Path) -> Path:
        """Create Kaggle dataset metadata file"""
        metadata = DATASET_METADATA_TEMPLATE.copy()
        metadata["resources"] = [
            {
                "path": initiatives_csv.name,
                "description": "Complete dataset of all registered European Citizens' Initiatives with signatures, countries, dates, and outcomes"
            },
            {
                "path": responses_csv.name,
                "description": "Commission responses and follow-up actions for successful ECIs including legislative outcomes"
            }
        ]

        output_path = self.output_path / "dataset-metadata.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)

        self.logger.info("Created dataset metadata: dataset-metadata.json")
        return output_path

    def copy_csvs_to_output(self, initiatives_csv: Path, responses_csv: Path) -> Path:
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

    def create_migration_report(self,
                                data_folder: Path,
                                initiatives_csv: Path,
                                responses_csv: Path,
                                sig_nb_name: str,
                                resp_nb_name: str,
                                log_filename: str,
                                outputs_cleared: bool) -> Path:
        """Create a detailed migration report"""
        outputs_status = (
            "✓ Cleared using nbconvert" if outputs_cleared 
            else "⚠️ Skipped (nbconvert not available)"
        )

        report_content = MIGRATION_REPORT_TEMPLATE.format(
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            data_folder=data_folder,
            initiatives_csv=initiatives_csv.name,
            responses_csv=responses_csv.name,
            outputs_status=outputs_status,
            sig_nb_name=sig_nb_name,
            resp_nb_name=resp_nb_name,
            log_filename=log_filename
        )

        report_path = self.output_path / "migration_report.txt"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)

        self.logger.info("Migration report saved to: migration_report.txt")
        return report_path
