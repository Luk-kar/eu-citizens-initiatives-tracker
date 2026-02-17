#!/usr/bin/env python3

"""
Kaggle Notebook Migration Script for ECI Analysis
--------------------------------------------------
Converts local Jupyter notebooks to Kaggle-compatible format

Usage:
    python kaggle_migration.py
"""

import logging
from datetime import datetime
from pathlib import Path

from migration_modules import (
    DataFinder,
    NotebookProcessor,
    ReportGenerator,
    SUCCESS_LOG_MESSAGES,
)


class KaggleMigrator:
    """Orchestrates the complete migration process"""

    def __init__(self, base_path: Path = None):
        if base_path is None:
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

        # Data path
        self.eci_root = self.base_path.parent
        self.data_path = self.eci_root / "data"

        if not self.data_path.exists():
            raise FileNotFoundError(
                f"Data directory not found at {self.data_path}\n"
                f"Expected structure: ECI_initiatives/data/YYYY-MM-DD_HH-MM-SS/"
            )

        # Setup logging
        self.log_filename = None
        self.logger = self._setup_logging()

        # Initialize helper classes
        self.data_finder = DataFinder(self.data_path, self.logger)
        self.notebook_processor = NotebookProcessor(self.logger)
        self.report_generator = ReportGenerator(self.output_path, self.logger)

    def _setup_logging(self) -> logging.Logger:
        """Configure logging to console AND file"""
        self.log_filename = f"migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

        c_handler = logging.StreamHandler()
        f_handler = logging.FileHandler(self.log_filename, mode="w", encoding="utf-8")

        c_handler.setLevel(logging.INFO)
        f_handler.setLevel(logging.DEBUG)

        c_format = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S"
        )
        f_format = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
        )
        c_handler.setFormatter(c_format)
        f_handler.setFormatter(f_format)

        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)
        logger.addHandler(c_handler)
        logger.addHandler(f_handler)

        return logger

    def run(self):
        """Execute the complete migration process"""
        self.logger.info(SUCCESS_LOG_MESSAGES["header"])
        self.logger.info("ECI Notebooks → Kaggle Migration Tool")
        self.logger.info(SUCCESS_LOG_MESSAGES["header"])
        self.logger.info(f"Log file: {self.log_filename}")

        # Check for nbconvert
        has_nbconvert = self.notebook_processor.check_nbconvert_available()

        try:
            # Find latest data folder
            data_folder = self.data_finder.get_latest_data_folder()

            # Find most recent CSV files
            initiatives_csv, responses_csv = self.data_finder.find_required_csvs(
                data_folder
            )

            # Migrate notebooks
            self.logger.info("\nStarting notebook migration...")

            sig_output = self.notebook_processor.migrate_notebook(
                self.signatures_nb,
                initiatives_csv,
                "signatures",
                self.output_path / f"{self.signatures_nb.stem}.kaggle.ipynb",
            )

            resp_output = self.notebook_processor.migrate_notebook(
                self.responses_nb,
                responses_csv,
                "responses",
                self.output_path / f"{self.responses_nb.stem}.kaggle.ipynb",
            )

            # Clear outputs using nbconvert
            outputs_cleared = False
            if has_nbconvert:
                self.logger.info("\nClearing notebook outputs...")
                sig_cleared = self.notebook_processor.clear_notebook_outputs(sig_output)
                resp_cleared = self.notebook_processor.clear_notebook_outputs(
                    resp_output
                )
                outputs_cleared = sig_cleared and resp_cleared

                if outputs_cleared:
                    self.logger.info("All outputs cleared successfully")
                else:
                    self.logger.warning("Some outputs could not be cleared")

            # Create supporting files
            self.logger.info("\nCreating supporting files...")
            self.report_generator.create_dataset_metadata(
                initiatives_csv, responses_csv
            )
            csv_dir = self.report_generator.copy_csvs_to_output(
                initiatives_csv, responses_csv
            )
            self.report_generator.create_migration_report(
                data_folder,
                initiatives_csv,
                responses_csv,
                sig_output.name,
                resp_output.name,
                self.log_filename,
                outputs_cleared,
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
