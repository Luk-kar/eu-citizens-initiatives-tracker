"""
Shared fixtures for browser and scraper behavior tests.
"""

import os
import sys
from pathlib import Path
import pytest


def pytest_configure(config):
    """
    Called before pytest starts collecting tests.
    This ensures sys.path is set up before any test modules are imported.
    """
    # Get the root directory (ECI_initiatives/)
    # From: ECI_initiatives/tests/conftest.py
    # Go up 2 levels: conftest.py -> tests/ -> ECI_initiatives/
    root_dir = Path(__file__).parent.parent.absolute()
    root_dir_str = str(root_dir)

    print("+++++++++++++++++++++++++++++++++++")
    print("root_dir_str\n", root_dir_str)
    print("+++++++++++++++++++++++++++++++++++")
    
    # Add to sys.path if not already there
    if root_dir_str not in sys.path:
        sys.path.insert(0, root_dir_str)


@pytest.fixture(scope="session")
def program_root_dir():
    """
    Provide the root directory of the ECI_initiatives program.
    
    This fixture calculates the path to the ECI_initiatives root directory
    from the conftest.py location. Since conftest.py is at:
    ECI_initiatives/tests/conftest.py
    
    We need to go up 2 levels to reach ECI_initiatives/
    
    Returns:
        Path: Absolute path to the ECI_initiatives root directory
    """
    # From ECI_initiatives/tests/conftest.py
    # Go up: conftest.py -> tests/ -> ECI_initiatives/
    root_dir = Path(__file__).parent.parent.absolute()
    return root_dir


@pytest.fixture(scope="session")
def data_dir(program_root_dir):
    """
    Provide the path to the data directory where scraping results are stored.
    
    Args:
        program_root_dir: Fixture providing the root directory path
        
    Returns:
        Path: Absolute path to the data directory (ECI_initiatives/data/)
    """
    return program_root_dir / "data"


@pytest.fixture(scope="session", autouse=True)
def cleanup_log_directories(data_dir):
    """Track and cleanup log directories created during the entire test session."""
    
    import shutil
    import re

    DIVIDER = "=" * 20
    DIVIDER_LINE = "\n" + DIVIDER + " {} " + DIVIDER + "\n"
    DIVIDER_START = DIVIDER_LINE.format("START TEST MESSAGE")
    DIVIDER_END = DIVIDER_LINE.format(" END TEST MESSAGE ")
    
    # Pattern for timestamp directories: YYYY-MM-DD_HH-MM-SS
    timestamp_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}$')
    
    # Use the data_dir fixture instead of calculating path here
    data_base_dir = data_dir

    print(f"\n{DIVIDER_START}")
    print("data directory:\n", data_base_dir)
    
    # Store existing timestamp directories before any tests run
    existing_timestamp_dirs = set()
    if data_base_dir.exists():
        for item in data_base_dir.iterdir():
            if item.is_dir() and timestamp_pattern.match(item.name):
                existing_timestamp_dirs.add(item.name)

    print("existing directories in data dir:\n" + str(existing_timestamp_dirs))
    print(DIVIDER_END)
    
    yield  # Run all tests
    
    # Cleanup: Remove any new timestamp directories created during test session
    if data_base_dir.exists():
        directories_removed = 0
        files_removed = 0

        print(f"\n{DIVIDER_START}\nRemoved test log directory:", end='')  # end='' to avoid extra new line

        for item in data_base_dir.iterdir():
            if (item.is_dir() and 
                timestamp_pattern.match(item.name) and 
                item.name not in existing_timestamp_dirs):
                
                try:
                    # Count files before removal
                    logs_dir = item / "logs"
                    if logs_dir.exists():
                        log_files = list(logs_dir.glob("scraper_initiatives*.log"))
                        files_removed += len(log_files)
                    
                    shutil.rmtree(item)
                    directories_removed += 1
                    print(f"\n - {item}")
                    
                except Exception as e:
                    print(f"Warning: Could not remove log directory {item}: {e}")
        
        if directories_removed > 0:
            print(f"Cleanup complete: removed {directories_removed} directories and {files_removed} log files")

        print(DIVIDER_END)
