"""
Notebook transformation and processing utilities
"""

import json
import logging
import re
import subprocess
from pathlib import Path
from typing import Dict, List

from .constants import (
    KAGGLE_SETUP_CODE,
    IMAGE_REPLACEMENTS,
    NOTEBOOK_LINK_REPLACEMENTS,
    HEADER_TITLE_REPLACEMENTS,
)


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
        self,
        source_lines: List[str],
        initiatives_csv_name: str,
        responses_csv_name: str,
        notebook_type: str,
    ) -> List[str]:
        """Replace local path detection code with Kaggle paths"""

        # Variables that only exist locally and have no Kaggle equivalent
        local_assign_vars = {"root_path", "data_directory", "base_data_path"}

        new_lines = []
        skip_mode = False
        inside_function = False
        function_indent = 0

        for i, line in enumerate(source_lines):

            stripped = line.lstrip()

            # Skip commented-out lines (don't transform them)
            if stripped.startswith("#"):
                new_lines.append(line)
                continue

            # Skip local filesystem variable assignments (no Kaggle equivalent)
            if (
                "=" in line
                and not stripped.startswith("print(")
                and any(stripped.startswith(var) for var in local_assign_vars)
            ):
                self.logger.debug(f"Skipped local var assignment: {stripped[:60]}")
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
                if stripped and current_indent <= function_indent:
                    inside_function = False
                else:
                    continue

            # Detect start of path detection block to skip
            if "from pathlib import Path" in line and not skip_mode:
                skip_mode = True
                continue

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
                    continue

            # Skip or replace print statements that reference removed variables
            if "print(" in line and any(
                var in line
                for var in [
                    "latest_folder",
                    "path_initiatives",
                    "folder_date",
                    "file_date",
                    "base_data_path",
                    "data_folder",
                ]
            ):
                # if "Base Data Path" in line or "base_data_path" in line:
                #     indent = len(line) - len(line.lstrip())
                #     new_lines.append(
                #         " " * indent + 'print(f"✓ Data loaded from: {KAGGLE_INPUT}")\n'
                #     )
                #     self.logger.debug(f"Replaced print statement: {line.strip()}")
                # else:
                #     self.logger.debug(f"Skipped print statement: {line.strip()}")
                continue

            # Replace the function call that loads data
            if any(
                pattern in line
                for pattern in ["load_latest_eci_initiatives(", "load_latest_eci_data("]
            ):
                indent = len(line) - len(line.lstrip())
                if notebook_type == "responses":
                    replacement = (
                        " " * indent
                        + f"df_initiatives = pd.read_csv(KAGGLE_INPUT / '{initiatives_csv_name}')\n"
                        + " " * indent
                        + f"df_responses = pd.read_csv(KAGGLE_INPUT / '{responses_csv_name}')\n"
                    )
                else:  # signatures
                    replacement = (
                        " " * indent
                        + f"df = pd.read_csv(KAGGLE_INPUT / '{initiatives_csv_name}')\n"
                    )
                new_lines.append(replacement)
                self.logger.debug(f"Replaced function call: {line.strip()}")
                continue

            # Handle specific secondary CSV references (legislation_titles, eci_categories)
            csv_replacements = {
                "legislation_titles.csv": "legislation_titles.csv",
                "eci_categories.csv": "eci_categories.csv",
            }

            line_modified = False
            for csv_name, csv_file in csv_replacements.items():
                if csv_name in line and not line.lstrip().startswith("#"):
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

            # Replace remaining inline pd.read_csv calls for main data files
            if "pd.read_csv" in line and not line.lstrip().startswith("#"):
                indent = len(line) - len(line.lstrip())
                if "eci_initiatives" in line and "merger" not in line:
                    new_lines.append(
                        " " * indent
                        + f"df_initiatives = pd.read_csv(KAGGLE_INPUT / '{initiatives_csv_name}')\n"
                    )
                    self.logger.debug(f"Replaced CSV loading: {line.strip()}")
                    continue
                elif "eci_merger" in line:
                    new_lines.append(
                        " " * indent
                        + f"df_responses = pd.read_csv(KAGGLE_INPUT / '{responses_csv_name}')\n"
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

    def enhance_header_styles(self, source_lines: List[str]) -> List[str]:
        """
        Enhance existing header styles for better Kaggle rendering (font-size:150%).

        Targets all <p style="...">Title</p> tags in markdown cells,
        appending font-size without altering structure, anchors, or content.

        Original: <p style="padding:15px;...font-family:'Arial',sans-serif;">🇪🇺 Title</p>
        Enhanced: <p style="padding:15px;...font-family:'Arial',sans-serif;font-size:150%;">🇪🇺 Title</p>
        """
        source = "".join(source_lines)

        # Split by quote type so inner quotes of the opposite kind are allowed:
        # "..." attribute → single quotes inside are valid (e.g. font-family:'Arial')
        # '...' attribute → double quotes inside are valid
        pattern = r"""<p\s+style=(?:"([^"]*?)"|'([^']*?)')>(.*?)</p>"""

        def style_enhancer(match: re.Match) -> str:

            style_attr = match.group(1) or match.group(2)
            quote = '"' if match.group(1) is not None else "'"
            content = match.group(3)

            if "font-size:" not in style_attr:

                # Ensure existing style ends with ; before appending
                if not style_attr.rstrip().endswith(";"):
                    style_attr = style_attr.rstrip() + ";"

                new_style = f"{style_attr}font-size:150%;"
            else:
                new_style = re.sub(
                    r"font-size:\s*[^;]+;", "font-size:150%;", style_attr
                )

            return f"<p style={quote}{new_style}{quote}>{content}</p>"

        result, n_enhanced = re.subn(pattern, style_enhancer, source, flags=re.DOTALL)

        if n_enhanced:
            self.logger.debug(
                f"Enhanced {n_enhanced} header style(s) with font-size:150%"
            )

        return result.splitlines(keepends=True)

    def replace_notebook_links(self, source_lines: List[str]) -> List[str]:
        """
        Replace GitHub notebook hrefs with published Kaggle notebook URLs.

        Applies to code cells containing cross-reference links between
        the signatures and responses companion notebooks.

        Targets href attributes only, leaving all surrounding HTML intact:
            href="https://github.com/.../eci_analysis_responses.ipynb"
            → href="https://www.kaggle.com/code/lukkardata/eci-commission-response"

            href="https://github.com/.../eci_analysis_signatures.ipynb"
            → href="https://www.kaggle.com/code/lukkardata/eci-signatures-collection"
        """
        source = "".join(source_lines)
        result = source

        for github_url, kaggle_url in NOTEBOOK_LINK_REPLACEMENTS.items():
            result = result.replace(github_url, kaggle_url)

        if result != source:
            n = sum(1 for url in NOTEBOOK_LINK_REPLACEMENTS if url not in result)
            self.logger.debug(
                f"Replaced {n} companion notebook link(s) with Kaggle URLs"
            )

        return result.splitlines(keepends=True)

    def demote_h1_headers(self, source_lines: List[str]) -> List[str]:
        """
        Demote H1 styled headers to H2 for Kaggle rendering consistency.

        On Kaggle, H1 renders disproportionately large relative to the styled <p>
        block. Demoting to H2 aligns the introduction header with all other
        section headers which already use ##.

        Targets only Markdown headings immediately followed by a styled <p> tag:
            # <p style="...">Title</p>   →   ## <p style="...">Title</p>

        Plain Markdown H1 headings (e.g. # Some Title) are left untouched.
        """
        source = "".join(source_lines)

        result, n = re.subn(
            r"^# (<p\s+style=)",
            r"## \1",
            source,
            flags=re.MULTILINE,
        )

        if n:
            self.logger.debug(f"Demoted {n} H1 styled header(s) to H2")

        return result.splitlines(keepends=True)

    def replace_header_titles(self, source_lines: List[str]) -> List[str]:
        """
        Replace specific notebook title strings inside <p> tags with
        line-broken versions for better two-line rendering on Kaggle.

        Targets only the exact title strings defined in HEADER_TITLE_REPLACEMENTS,
        leaving all surrounding HTML and style attributes intact.

            🇪🇺✍️ European Citizens' Initiatives: Signatures Collection
            → 🇪🇺✍️ European Citizens' Initiatives:<br>Signatures Collection

            🇪🇺🏛️ European Citizens' Initiatives: After the Signatures
            → 🇪🇺🏛️ European Citizens' Initiatives:<br>After the Signatures
        """
        source = "".join(source_lines)
        result = source

        for original, replacement in HEADER_TITLE_REPLACEMENTS.items():
            result = result.replace(original, replacement)

        if result != source:
            self.logger.debug("Replaced header title(s) with line-broken version")

        return result.splitlines(keepends=True)

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
        self,
        notebook_path: Path,
        initiatives_csv: Path,  # ← always needed (both notebooks use df_initiatives)
        responses_csv: Path,  # ← needed for responses notebook
        notebook_type: str,
        output_path: Path,
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
        markdown_modified = 0

        for i, cell in enumerate(notebook["cells"]):
            # Skip the setup cell we just inserted
            if i == 0:
                continue

            # Process Code Cells
            if cell["cell_type"] == "code":
                new_lines = cell["source"]

                # Cross-notebook links: GitHub → Kaggle
                new_lines = self.replace_notebook_links(new_lines)

                # Plotly renderer fix
                renderer_fixed = False
                updated_lines = []

                for line in new_lines:

                    if 'pio.renderers.default = "notebook_connected"' in line:

                        line = line.replace('"notebook_connected"', '"iframe"')
                        renderer_fixed = True
                        self.logger.debug("Fixed Plotly renderer to 'iframe'")

                    updated_lines.append(line)

                new_lines = updated_lines

                # Path replacements
                path_fixed = False
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
                            ]
                        )
                    )
                    for line in new_lines
                ):
                    new_lines = self.replace_path_code(
                        new_lines,
                        initiatives_csv.name,
                        responses_csv.name,
                        notebook_type,
                    )
                    path_fixed = True

                if new_lines != cell["source"]:
                    cell["source"] = new_lines
                    cells_modified += 1
                    if renderer_fixed:
                        self.logger.info("Plotly renderer updated to 'kaggle'")

            # Process Markdown Cells
            elif cell["cell_type"] == "markdown":
                original_source = cell["source"]

                new_source = self.replace_image_links(original_source)
                new_source = self.enhance_header_styles(new_source)
                new_source = self.demote_h1_headers(new_source)
                new_source = self.replace_header_titles(new_source)

                if new_source != original_source:
                    cell["source"] = new_source
                    markdown_modified += 1

        self.logger.info(
            f"Modified {cells_modified} code cells and {markdown_modified} markdown cells"
        )

        # Save migrated notebook
        self.save_notebook(notebook, output_path)
        self.logger.info(f"Saved migrated notebook: {output_path.name}")

        return output_path
