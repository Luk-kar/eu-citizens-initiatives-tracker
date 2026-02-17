"""
Notebook transformation and processing utilities
"""

import json
import logging
import re
import subprocess
from pathlib import Path
from typing import Dict, List

from .constants import KAGGLE_SETUP_CODE, IMAGE_REPLACEMENTS


class NotebookProcessor:
    """Handles notebook loading, transformation, and output clearing"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    # ──────────────────────────────
    # Low-level I/O
    # ──────────────────────────────

    def load_notebook(self, notebook_path: Path) -> Dict:
        """Load a Jupyter notebook as JSON"""
        with open(notebook_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_notebook(self, notebook: Dict, output_path: Path):
        """Save notebook with proper formatting"""
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(notebook, f, indent=1, ensure_ascii=False)

    # ──────────────────────────────
    # Cell transformation
    # ──────────────────────────────

    def replace_path_code(
        self, source_lines: List[str], csv_filename: str, notebook_type: str
    ) -> List[str]:
        """Replace local path detection code with Kaggle paths"""

        new_lines = []
        skip_mode = False
        inside_function = False
        function_indent = 0

        for i, line in enumerate(source_lines):

            # Skip commented-out lines (don't transform them)
            stripped = line.lstrip()
            if stripped.startswith("#"):
                new_lines.append(line)
                continue

            # Detect function definitions that should be skipped entirely
            if stripped.startswith("def ") and any(
                func_name in stripped
                for func_name in [
                    "find_latest_timestamp_folder",
                    "find_latest_csv",
                    "load_latest_eci_initiatives",
                    "load_latest_eci_data",
                ]
            ):
                inside_function = True
                function_indent = len(line) - len(stripped)
                self.logger.debug(f"Skipping function: {stripped[:50]}")
                continue

            # Skip everything inside the function until we exit
            if inside_function:
                current_indent = len(line) - len(line.lstrip())
                # Exit function when we hit a line at same or lower indentation
                if stripped and current_indent <= function_indent:
                    inside_function = False
                else:
                    continue

            # Detect start of path detection block to skip
            if "from pathlib import Path" in line and not skip_mode:
                skip_mode = True
                continue  # Skip this import line

            # End skipping when we hit another import that's not path-related
            if skip_mode:
                if "import" in line and "from" not in line and "Path" not in line:
                    skip_mode = False
                elif any(
                    keyword in line
                    for keyword in [
                        "root_path",
                        "data_directory",
                        "data_folder",
                    ]
                ):
                    continue  # Skip path-detection variable assignments

            # Skip or replace print statements that reference removed variables
            if "print(" in line and any(
                var in line
                for var in [
                    "latest_folder",
                    "path_initiatives",
                    "folder_date",
                    "file_date",
                    "base_data_path",
                ]
            ):
                # Replace with simplified print or skip
                if "Base Data Path" in line or "base_data_path" in line:
                    indent = len(line) - len(line.lstrip())
                    new_lines.append(
                        " " * indent + 'print(f"✓ Data loaded from: {KAGGLE_INPUT}")\n'
                    )
                    self.logger.debug(f"Replaced print statement: {line.strip()}")
                else:
                    self.logger.debug(f"Skipped print statement: {line.strip()}")
                continue

            # Replace the function call that loads data
            if any(
                pattern in line
                for pattern in ["load_latest_eci_initiatives(", "load_latest_eci_data("]
            ):
                indent = len(line) - len(line.lstrip())
                # Replace complex function call with simple CSV load
                new_lines.append(
                    " " * indent
                    + f"df = pd.read_csv(KAGGLE_INPUT / '{csv_filename}')\n"
                )
                self.logger.debug(f"Replaced function call: {line.strip()}")
                continue

            # Handle CSV file references (works for both single-line and multi-line calls)
            # Check for specific CSV filenames regardless of pd.read_csv presence
            csv_replacements = {
                "legislation_titles.csv": "legislation_titles.csv",
                "eci_categories.csv": "eci_categories.csv",
            }

            line_modified = False
            for csv_name, csv_file in csv_replacements.items():
                if csv_name in line and not line.lstrip().startswith("#"):
                    # Use regex to replace the quoted filename with KAGGLE_INPUT / filename
                    # Handles both "filename" and 'filename'
                    pattern = rf'(["\']){re.escape(csv_name)}\1'
                    replacement = rf"KAGGLE_INPUT / \1{csv_file}\1"
                    new_line = re.sub(pattern, replacement, line)
                    if new_line != line:
                        new_lines.append(new_line)
                        self.logger.debug(f"Replaced {csv_name} path: {line.strip()}")
                        line_modified = True
                        break

            if line_modified:
                continue

            # Replace CSV loading for main data files (only if pd.read_csv is on same line)
            if "pd.read_csv" in line and not line.lstrip().startswith("#"):
                # Handle main ECI data CSVs
                if "eci_initiatives" in line and "merger" not in line:
                    indent = len(line) - len(line.lstrip())
                    new_lines.append(
                        " " * indent
                        + f"df_initiatives = pd.read_csv(KAGGLE_INPUT / '{csv_filename}')\n"
                    )
                    self.logger.debug(f"Replaced CSV loading: {line.strip()}")
                    continue
                elif "eci_merger" in line:
                    indent = len(line) - len(line.lstrip())
                    new_lines.append(
                        " " * indent
                        + f"df_responses = pd.read_csv(KAGGLE_INPUT / '{csv_filename}')\n"
                    )
                    self.logger.debug(f"Replaced CSV loading: {line.strip()}")
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

    # ──────────────────────────────
    # nbconvert utilities
    # ──────────────────────────────

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

    # ──────────────────────────────
    # High-level orchestration
    # ──────────────────────────────

    def migrate_notebook(
        self, notebook_path: Path, csv_file: Path, notebook_type: str, output_path: Path
    ) -> Path:
        """Migrate a single notebook to Kaggle format"""
        self.logger.info(f"Migrating {notebook_type} notebook: {notebook_path.name}")

        # Load notebook
        notebook = self.load_notebook(notebook_path)
        self.logger.debug(f"Loaded {notebook_path.name}")

        # Insert Kaggle setup cell at the beginning
        setup_cell = {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": KAGGLE_SETUP_CODE,
        }
        notebook["cells"].insert(0, setup_cell)
        self.logger.info("Inserted Kaggle setup cell at beginning")

        # Process cells (starting from index 1, since 0 is now the setup cell)
        cells_modified = 0
        images_modified = 0

        for i, cell in enumerate(notebook["cells"]):
            # Skip the setup cell we just inserted
            if i == 0:
                continue

            # Process Code Cells
            if cell["cell_type"] == "code":
                original_source = cell["source"]
                # Enhanced detection to catch all problematic cells
                if any(
                    "Path" in line
                    or "pd.read_csv" in line
                    or "root_path" in line
                    or "def find_" in line
                    or "def load_" in line
                    or "legislation_titles.csv" in line
                    or "eci_categories.csv" in line
                    or (
                        "print(" in line
                        and any(
                            var in line
                            for var in [
                                "latest_folder",
                                "path_initiatives",
                                "folder_date",
                                "file_date",
                                "base_data_path",
                            ]
                        )
                    )
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

        # Save migrated notebook
        self.save_notebook(notebook, output_path)
        self.logger.info(f"Saved migrated notebook: {output_path.name}")

        return output_path
