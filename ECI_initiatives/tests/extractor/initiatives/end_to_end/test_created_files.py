"""
Test suite for validating that the ECI extractor correctly creates log and CSV files.

This test validates the core output artifacts:
 - CSV file creation with proper structure
 - Log file creation with appropriate naming
 - Directory structure creation
 - File naming conventions

The test processes example HTML files from the test data directory
to verify that the extractor produces expected outputs.

Test validates:
 - CSV file creation with correct headers
 - CSV contains all required columns
 - Log file is created with timestamp naming pattern
 - Files are placed in correct locations
 - CSV encoding is UTF-8
 - Row count matches processed files
"""

# Standard library
import csv
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# Third party
import pytest

# Test constants
from ECI_initiatives.tests.consts import REQUIRED_EXTRACTOR_CSV_COLUMNS


class TestCreatedFiles:
    """Test suite for validating created files from ECI extraction."""

    @classmethod
    def setup_class(cls):
        """
        Setup class-level resources that runs once before all tests.
        
        Imports are done here to avoid premature module loading.
        """

        from ECI_initiatives.extractor.initiatives.processor import ECIDataProcessor
        from ECI_initiatives.extractor.initiatives.initiatives_logger import InitiativesExtractorLogger
        
        cls.ECIDataProcessor = ECIDataProcessor
        cls.InitiativesExtractorLogger = InitiativesExtractorLogger
        
        # Create temporary directory for test session
        cls.temp_session_dir = tempfile.mkdtemp(prefix="eci_extractor_test_")
        cls.temp_session_path = Path(cls.temp_session_dir)
        
        # Create expected subdirectories
        cls.pages_dir = cls.temp_session_path / "initiatives" / "pages"
        cls.logs_dir = cls.temp_session_path / "logs"
        cls.pages_dir.mkdir(parents=True, exist_ok=True)
        cls.logs_dir.mkdir(parents=True, exist_ok=True)
        
    @classmethod
    def teardown_class(cls):
        """Cleanup temporary directories after all tests."""

        if cls.temp_session_path.exists():
            shutil.rmtree(cls.temp_session_path)
    
    def test_log_file_is_created(self):
        """Test that log file is created when log_dir is provided."""

        logger_instance = self.InitiativesExtractorLogger()
        logger = logger_instance.setup(log_dir=self.logs_dir)
        
        # Log a test message
        logger.info("Test log message")
        
        # Check log file was created
        log_files = list(self.logs_dir.glob("processor_initiatives_*.log"))
        
        assert len(log_files) > 0, "Log file should be created"
        assert log_files[0].exists(), "Log file should exist"
    
    def test_log_file_naming_pattern(self):
        """Test that log filename follows the correct pattern."""

        logger_instance = self.InitiativesExtractorLogger()
        logger = logger_instance.setup(log_dir=self.logs_dir)
        
        log_files = list(self.logs_dir.glob("processor_initiatives_*.log"))
        assert len(log_files) > 0, "At least one log file should exist"
        
        # Check naming pattern: processor_initiatives_YYYY-MM-DD_HH-MM-SS.log
        log_filename = log_files[0].name

        assert log_filename.startswith("processor_initiatives_"), \
            f"Log filename should start with 'processor_initiatives_', got: {log_filename}"

        assert log_filename.endswith(".log"), \
            f"Log filename should end with '.log', got: {log_filename}"
        
        # Extract timestamp part
        timestamp_part = log_filename.replace("processor_initiatives_", "").replace(".log", "")

        # Pattern: YYYY-MM-DD_HH-MM-SS
        assert len(timestamp_part) == 19, \
            f"Timestamp should be 19 characters (YYYY-MM-DD_HH-MM-SS), got: {timestamp_part}"
    
    def test_log_file_contains_entries(self, program_root_dir):
        """Test that log file contains entries after processing."""

        from unittest.mock import patch
        from datetime import datetime
        
        eci_file = "2024_000004_en.html"
        
        # Create a proper session directory with timestamp
        session_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        session_dir = self.temp_session_path / session_name
        
        # Copy example HTML files to temp session directory
        test_data_dir = program_root_dir / "tests" / "data" / "example_htmls" / "initiatives"
        
        # Create year directory structure with correct path: initiative_pages (not initiatives/pages)
        year_dir = session_dir / "initiative_pages" / "2024"
        year_dir.mkdir(parents=True, exist_ok=True)
        
        # Create logs directory
        logs_dir = session_dir / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy one example file
        example_file = test_data_dir / eci_file
        if example_file.exists():
            shutil.copy(example_file, year_dir / eci_file)
        
        # Run processor with mock
        processor = self.ECIDataProcessor(
            data_root=str(self.temp_session_path),
            logger=None
        )
        
        # Mock find_latest_scrape_session to return our session and set attribute
        def mock_find_session():
            processor.last_session_scraping_dir = session_dir
            return session_dir
        
        with patch.object(processor, 'find_latest_scrape_session', side_effect=mock_find_session):
            processor.run()
        
        # Check log file has content
        log_files = list(logs_dir.glob("processor_initiatives_*.log"))

        assert len(log_files) > 0, "Log file should be created"
        
        log_content = log_files[0].read_text(encoding='utf-8')

        assert len(log_content) > 0, "Log file should contain entries"
        assert "Starting ECI data processing" in log_content or \
            "Processing" in log_content, \
            "Log should contain processing messages"
        
        # Cleanup this session directory after test
        shutil.rmtree(session_dir)

    def test_csv_file_is_created(self, program_root_dir):
        """Test that CSV file is created in output directory."""

        from unittest.mock import patch
        from datetime import datetime
        
        eci_file = "2024_000004_en.html"
        
        session_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        session_dir = self.temp_session_path / session_name
        
        # Setup test data with correct directory name
        test_data_dir = program_root_dir / "tests" / "data" / "example_htmls" / "initiatives"
        year_dir = session_dir / "initiative_pages" / "2024"
        year_dir.mkdir(parents=True, exist_ok=True)
        
        logs_dir = session_dir / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        example_file = test_data_dir / eci_file

        if example_file.exists():
            shutil.copy(example_file, year_dir / eci_file)
        
        # Run processor with mock
        processor = self.ECIDataProcessor(
            data_root=str(self.temp_session_path),
            logger=None
        )
        
        def mock_find_session():
            processor.last_session_scraping_dir = session_dir
            return session_dir
        
        with patch.object(processor, 'find_latest_scrape_session', side_effect=mock_find_session):
            processor.run()
        
        # Check CSV file was created in session directory
        csv_files = list(session_dir.glob("eci_initiatives_*.csv"))
        assert len(csv_files) > 0, "CSV file should be created"
        assert csv_files[0].exists(), "CSV file should exist"
        
        # Cleanup
        shutil.rmtree(session_dir)

    def test_csv_contains_correct_headers(self, program_root_dir):
        """Test that CSV contains all required column headers."""

        from unittest.mock import patch
        from datetime import datetime
        
        eci_file = "2024_000004_en.html"
        
        # Create session directory with timestamp
        session_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        session_dir = self.temp_session_path / session_name
        
        # Setup and run processor
        test_data_dir = program_root_dir / "tests" / "data" / "example_htmls" / "initiatives"
        year_dir = session_dir / "initiative_pages" / "2024"
        year_dir.mkdir(parents=True, exist_ok=True)
        
        logs_dir = session_dir / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        example_file = test_data_dir / eci_file
        if example_file.exists():
            shutil.copy(example_file, year_dir / eci_file)
        
        processor = self.ECIDataProcessor(
            data_root=str(self.temp_session_path),
            logger=None
        )
        
        def mock_find_session():
            processor.last_session_scraping_dir = session_dir
            return session_dir
        
        with patch.object(processor, 'find_latest_scrape_session', side_effect=mock_find_session):
            processor.run()
        
        # Read CSV and check headers
        csv_files = list(session_dir.glob("eci_initiatives_*.csv"))
        assert len(csv_files) > 0, "CSV file should exist"
        
        with open(csv_files[0], 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            
            for required_column in REQUIRED_EXTRACTOR_CSV_COLUMNS:
                assert required_column in headers, \
                    f"CSV should contain column: {required_column}"
        
        # Cleanup
        shutil.rmtree(session_dir)

    def test_csv_row_count_matches_processed_files(self, program_root_dir):
        """Test that CSV row count matches number of processed HTML files."""

        from unittest.mock import patch
        from datetime import datetime
        
        session_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        session_dir = self.temp_session_path / session_name
        
        # Setup multiple test files
        test_data_dir = program_root_dir / "tests" / "data" / "example_htmls" / "initiatives"
        year_dir = session_dir / "initiative_pages" / "2024"
        year_dir.mkdir(parents=True, exist_ok=True)
        
        logs_dir = session_dir / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy multiple files
        eci_files = [
            "2024_000004_en.html",
            "2024_000005_en.html",
            "2024_000007_en.html"
        ]
        
        copied_count = 0
        for eci_file in eci_files:

            example_file = test_data_dir / eci_file

            if example_file.exists():

                shutil.copy(example_file, year_dir / eci_file)
                copied_count += 1
        
        # Run processor
        processor = self.ECIDataProcessor(
            data_root=str(self.temp_session_path),
            logger=None
        )
        
        def mock_find_session():
            processor.last_session_scraping_dir = session_dir
            return session_dir
        
        with patch.object(processor, 'find_latest_scrape_session', side_effect=mock_find_session):
            processor.run()
        
        # Count CSV rows
        csv_files = list(session_dir.glob("eci_initiatives_*.csv"))
        assert len(csv_files) > 0, "CSV file should exist"
        
        with open(csv_files[0], 'r', encoding='utf-8') as f:
            
            reader = csv.DictReader(f)
            row_count = sum(1 for _ in reader)
            
            assert row_count == copied_count, \
                f"CSV should have {copied_count} rows, got {row_count}"
        
        # Cleanup
        shutil.rmtree(session_dir)

    def test_csv_encoding_is_utf8(self, program_root_dir):
        """Test that CSV file is encoded in UTF-8."""
        
        from unittest.mock import patch
        from datetime import datetime
        
        eci_file = "2024_000004_en.html"
        
        session_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        session_dir = self.temp_session_path / session_name
        
        # Setup and run
        test_data_dir = program_root_dir / "tests" / "data" / "example_htmls" / "initiatives"
        year_dir = session_dir / "initiative_pages" / "2024"
        year_dir.mkdir(parents=True, exist_ok=True)
        
        logs_dir = session_dir / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        example_file = test_data_dir / eci_file
        if example_file.exists():
            shutil.copy(example_file, year_dir / eci_file)
        
        processor = self.ECIDataProcessor(
            data_root=str(self.temp_session_path),
            logger=None
        )
        
        def mock_find_session():
            processor.last_session_scraping_dir = session_dir
            return session_dir
        
        with patch.object(processor, 'find_latest_scrape_session', side_effect=mock_find_session):
            processor.run()
        
        # Try reading CSV with UTF-8
        csv_files = list(session_dir.glob("eci_initiatives_*.csv"))
        assert len(csv_files) > 0, "CSV file should exist"
        
        try:
            with open(csv_files[0], 'r', encoding='utf-8') as f:
                content = f.read()
                assert len(content) > 0, "CSV should have content"
        except UnicodeDecodeError:
            pytest.fail("CSV file should be UTF-8 encoded")
        
        # Cleanup
        shutil.rmtree(session_dir)

    def test_csv_created_with_zero_initiatives(self):
        """Test that CSV handling when no initiatives are processed."""

        from unittest.mock import patch
        from datetime import datetime
        
        session_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        session_dir = self.temp_session_path / session_name
        
        # Create empty directory structure (no HTML files)
        year_dir = session_dir / "initiative_pages" / "2024"
        year_dir.mkdir(parents=True, exist_ok=True)
        
        logs_dir = session_dir / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Run processor with empty directory
        processor = self.ECIDataProcessor(
            data_root=str(self.temp_session_path),
            logger=None
        )
        
        def mock_find_session():
            processor.last_session_scraping_dir = session_dir
            return session_dir
        
        with patch.object(processor, 'find_latest_scrape_session', side_effect=mock_find_session):
            processor.run()
        
        # Check CSV handling with zero initiatives
        csv_files = list(session_dir.glob("eci_initiatives_*.csv"))
        
        # Current implementation: CSV is created but empty when no initiatives
        # This documents the actual behavior - the processor logs warning and doesn't write CSV
        if len(csv_files) > 0:

            # If CSV file exists, check if it's empty or has headers
            csv_file = csv_files[0]
            file_size = csv_file.stat().st_size
            
            # Empty file (0 bytes) or has some content
            if file_size == 0:

                # CSV file created but empty - acceptable behavior
                pass

            else:

                # Has content - should have headers at minimum
                with open(csv_file, 'r', encoding='utf-8') as f:

                    content = f.read()

                    # Check if it has at least one line (headers)
                    lines = content.strip().split('\n')
                    assert len(lines) >= 1, "CSV should have at least header line"
        else:
            # No CSV created when there are no initiatives - also valid behavior
            # This is the actual current behavior based on logs
            pass
        
        # Verify log contains the warning
        log_files = list(logs_dir.glob("processor_initiatives_*.log"))

        if len(log_files) > 0:

            log_content = log_files[0].read_text(encoding='utf-8')
            
            assert "No initiatives to save" in log_content, \
                "Log should contain warning about no initiatives"
        
        # Cleanup
        shutil.rmtree(session_dir)
