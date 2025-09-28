"""
Shared fixtures for browser and scraping behavior tests.
"""

import pytest


@pytest.fixture(scope="session", autouse=True)
def cleanup_log_directories():
    """Track and cleanup log directories created during the entire test session."""
    
    import shutil
    import re
    from pathlib import Path

    DIVIDER = "=" * 20
    DIVIDER_LINE = "\n" + DIVIDER + " {} " + DIVIDER + "\n"
    DIVIDER_START = DIVIDER_LINE.format("START TEST MESSAGE")
    DIVIDER_END = DIVIDER_LINE.format(" END TEST MESSAGE ")
    
    # Pattern for timestamp directories: YYYY-MM-DD_HH-MM-SS
    timestamp_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}$')
    
    # Get the base directory where log directories are created
    script_dir = Path(__file__).parent.parent.parent.parent.absolute()
    data_base_dir = script_dir / "data"

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

        print(f"\n{DIVIDER_START}\nRemoved test log directory:", end='') # end='' to avoid extra new line

        for item in data_base_dir.iterdir():
            if (item.is_dir() and 
                timestamp_pattern.match(item.name) and 
                item.name not in existing_timestamp_dirs):
                
                try:
                    # Count files before removal
                    logs_dir = item / "logs"
                    if logs_dir.exists():
                        log_files = list(logs_dir.glob("scraper_*.log"))
                        files_removed += len(log_files)
                    
                    shutil.rmtree(item)
                    directories_removed += 1
                    print(f"\n - {item}")
                    
                except Exception as e:
                    print(f"Warning: Could not remove log directory {item}: {e}")
        
        if directories_removed > 0:
            print(f"Cleanup complete: removed {directories_removed} directories and {files_removed} log files")

        print(DIVIDER_END)
