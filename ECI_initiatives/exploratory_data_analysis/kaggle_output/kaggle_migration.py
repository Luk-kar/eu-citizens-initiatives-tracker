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
    PROJECT_PATHS,
)


class KaggleMigrator:
    """Orchestrates the complete migration process"""

    def __init__(self):

        paths = PROJECT_PATHS

        self.base_path = paths.base_path
        self.output_path = paths.output_path
        self.signatures_nb = paths.signatures_nb
        self.responses_nb = paths.responses_nb
        self.eci_root = paths.eci_root
        self.data_path = paths.data_path

        # Verify data path exists
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
        self.log_filename = (
            f"migration_{datetime.now().strftime('%Y_%m_%d_%H-%M-%S')}.log"
        )

        console_handler = logging.StreamHandler()
        file_handler = logging.FileHandler(
            self.log_filename, mode="w", encoding="utf-8"
        )

        console_handler.setLevel(logging.INFO)
        file_handler.setLevel(logging.DEBUG)

        console_format = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S"
        )
        file_format = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
        )
        console_handler.setFormatter(console_format)
        file_handler.setFormatter(file_format)

        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

        return logger

    def run(self) -> bool:
        """Execute the complete migration process."""

        self._log_header()

        has_nbconvert = self.notebook_processor.check_nbconvert_available()

        try:
            data_folder, initiatives_csv, responses_csv = self._prepare_data()

            sig_output, resp_output = self._migrate_notebooks(
                initiatives_csv,
                responses_csv,
            )

            outputs_cleared = self._maybe_clear_outputs(
                has_nbconvert,
                sig_output,
                resp_output,
            )

            csv_dir = self._create_supporting_files(
                data_folder,
                initiatives_csv,
                responses_csv,
                sig_output,
                resp_output,
                outputs_cleared,
            )

            self._log_summary(
                data_folder,
                initiatives_csv,
                responses_csv,
                sig_output,
                resp_output,
                csv_dir,
            )

        except Exception as e:
            self.logger.error(f"Migration failed: {e}", exc_info=True)
            return False

        return True

    def _log_header(self) -> None:
        self.logger.info(SUCCESS_LOG_MESSAGES["header"])
        self.logger.info("ECI Notebooks → Kaggle Migration Tool")
        self.logger.info(SUCCESS_LOG_MESSAGES["header"])
        self.logger.info(f"Log file: {self.log_filename}")

    def _prepare_data(self):
        """Find latest data folder and required CSVs."""

        data_folder = self.data_finder.get_latest_data_folder()
        initiatives_csv, responses_csv = self.data_finder.find_required_csvs(
            data_folder
        )
        return data_folder, initiatives_csv, responses_csv

    def _migrate_notebooks(self, initiatives_csv, responses_csv):
        """Migrate signatures and responses notebooks."""

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

        return sig_output, resp_output

    def _maybe_clear_outputs(
        self, has_nbconvert: bool, sig_output, resp_output
    ) -> bool:
        """Clear notebook outputs if nbconvert is available."""

        outputs_cleared = False

        if not has_nbconvert:
            return False

        self.logger.info("\nClearing notebook outputs...")
        sig_cleared = self.notebook_processor.clear_notebook_outputs(sig_output)
        resp_cleared = self.notebook_processor.clear_notebook_outputs(resp_output)
        outputs_cleared = sig_cleared and resp_cleared

        if outputs_cleared:
            self.logger.info("All outputs cleared successfully")
        else:
            self.logger.warning("Some outputs could not be cleared")

        return outputs_cleared

    def _create_supporting_files(
        self,
        data_folder,
        initiatives_csv,
        responses_csv,
        sig_output,
        resp_output,
        outputs_cleared: bool,
    ):
        """Create metadata, copy CSVs, and write migration report."""

        self.logger.info("\nCreating supporting files...")

        self.report_generator.create_dataset_metadata(initiatives_csv, responses_csv)
        csv_dir = self.report_generator.copy_csvs_to_output(
            initiatives_csv,
            responses_csv,
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

        return csv_dir

    def _log_summary(
        self,
        data_folder,
        initiatives_csv,
        responses_csv,
        sig_output,
        resp_output,
        csv_dir,
    ) -> None:
        """Log final summary of generated files and next steps."""

        self.logger.info("\n" + SUCCESS_LOG_MESSAGES["header"])
        self.logger.info(SUCCESS_LOG_MESSAGES["title"])
        self.logger.info(SUCCESS_LOG_MESSAGES["header"])

        self.logger.info(SUCCESS_LOG_MESSAGES["sections"]["generated_files"])
        self.logger.info(f"  1. {sig_output.name}")
        self.logger.info(f"  2. {resp_output.name}")
        self.logger.info("  3. dataset-metadata.json")
        self.logger.info(f"  4. {csv_dir.name}/{initiatives_csv.name}")
        self.logger.info(f"  5. {csv_dir.name}/{responses_csv.name}")
        self.logger.info("  6. migration_report.txt")
        self.logger.info(f"  7. {self.log_filename}")

        self.logger.info(SUCCESS_LOG_MESSAGES["sections"]["data_sources"])
        self.logger.info(f"  → Folder: {data_folder.name}")
        self.logger.info(f"  → Initiatives: {initiatives_csv.name}")
        self.logger.info(f"  → Responses: {responses_csv.name}")

        self.logger.info(SUCCESS_LOG_MESSAGES["sections"]["next_steps"])
        for step in SUCCESS_LOG_MESSAGES["next_steps_items"]:
            self.logger.info(f"  {step}")

        self.logger.info(SUCCESS_LOG_MESSAGES["header"] + "\n")


def main():
    """Main execution function"""
    migrator = KaggleMigrator()
    success = migrator.run()
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
