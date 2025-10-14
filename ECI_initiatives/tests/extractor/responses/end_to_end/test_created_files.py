"""
Test suite for validating that the ECI responses extractor correctly creates log and CSV files.

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
from ECI_initiatives.tests.consts import REQUIRED_RESPONSES_CSV_COLUMNS


class TestCreatedFiles:
    """Test suite for validating created files from ECI responses extraction."""

    @classmethod
    def setup_class(cls):
        """
        Setup class-level resources that runs once before all tests.
        
        Imports are done here to avoid premature module loading.
        """
        from ECI_initiatives.extractor.responses.processor import ECIResponseDataProcessor
        from ECI_initiatives.extractor.responses.responses_logger import ResponsesExtractorLogger
        
        cls.ECIResponseDataProcessor = ECIResponseDataProcessor
        cls.ResponsesExtractorLogger = ResponsesExtractorLogger
        
        # Create temporary directory for test session
        cls.temp_session_dir = tempfile.mkdtemp(prefix="eci_responses_test_")
        cls.temp_session_path = Path(cls.temp_session_dir)
        
        # Create expected subdirectories
        cls.responses_dir = cls.temp_session_path / "responses"
        cls.logs_dir = cls.temp_session_path / "logs"
        cls.responses_dir.mkdir(parents=True, exist_ok=True)
        cls.logs_dir.mkdir(parents=True, exist_ok=True)
        
    @classmethod
    def teardown_class(cls):
        """Cleanup temporary directories after all tests."""
        if cls.temp_session_path.exists():
            shutil.rmtree(cls.temp_session_path)
    
    def test_log_file_is_created(self):
        """Test that log file is created when log_dir is provided."""
        logger_instance = self.ResponsesExtractorLogger()
        logger = logger_instance.setup(log_dir=self.logs_dir)
        
        # Log a test message
        logger.info("Test log message")
        
        # Check log file was created
        log_files = list(self.logs_dir.glob("extractor_responses_*.log"))
        
        assert len(log_files) > 0, "Log file should be created"
        assert log_files[0].exists(), "Log file should exist"
    
    def test_log_file_naming_pattern(self):
        """Test that log filename follows the correct pattern."""
        logger_instance = self.ResponsesExtractorLogger()
        logger = logger_instance.setup(log_dir=self.logs_dir)
        
        log_files = list(self.logs_dir.glob("extractor_responses_*.log"))
        assert len(log_files) > 0, "At least one log file should exist"
        
        # Check naming pattern: extractor_responses_YYYY-MM-DD_HH-MM-SS.log
        log_filename = log_files[0].name
        
        assert log_filename.startswith("extractor_responses_"), \
            f"Log filename should start with 'extractor_responses_', got: {log_filename}"
        
        assert log_filename.endswith(".log"), \
            f"Log filename should end with '.log', got: {log_filename}"
        
        # Extract timestamp part
        timestamp_part = log_filename.replace("extractor_responses_", "").replace(".log", "")
        
        # Validate datetime format: YYYY-MM-DD_HH-MM-SS
        try:
            datetime.strptime(timestamp_part, "%Y-%m-%d_%H-%M-%S")
        except ValueError:
            pytest.fail(f"Timestamp part '{timestamp_part}' doesn't match format YYYY-MM-DD_HH-MM-SS")
    
    def test_log_file_contains_entries(self, program_root_dir):
        """Test that log file contains entries after processing."""
        from unittest.mock import patch
        from datetime import datetime
        
        eci_file = "2019_000007_en.html"
        
        # Create a proper session directory with timestamp
        session_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        session_dir = self.temp_session_path / session_name
        
        # Copy example HTML files to temp session directory
        test_data_dir = program_root_dir / "tests" / "data" / "example_htmls" / "responses"
        
        # Create year directory structure
        year_dir = session_dir / "responses" / "2019"
        year_dir.mkdir(parents=True, exist_ok=True)
        
        # Create logs directory
        logs_dir = session_dir / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Create responses_list.csv in responses directory
        responses_list_path = year_dir.parent / "responses_list.csv"
        with open(responses_list_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["url_find_initiative", "registration_number", "title", "datetime"])
            writer.writeheader()
            writer.writerow({
                "url_find_initiative": "https://example.com/2019/000007",
                "registration_number": "2019/000007",
                "title": "Test Initiative",
                "datetime": "2024-10-09 14:00:00"
            })
        
        # Copy one example file from rejection subdirectory
        example_file = test_data_dir / "rejection" / "2019" / eci_file
        if example_file.exists():
            shutil.copy(example_file, year_dir / eci_file)
        else:
            raise FileNotFoundError(f"Example file not found:\n{str(example_file)}")
        
        # Run processor with mock
        processor = self.ECIResponseDataProcessor(
            data_root=str(self.temp_session_path),
            logger=None
        )
        
        # Mock find_latest_scrape_session to return our session
        def mock_find_session():
            processor.last_session_scraping_dir = session_dir
            return session_dir
        
        with patch.object(processor, 'find_latest_scrape_session', side_effect=mock_find_session):
            processor.run()
        
        # Check log file has content
        log_files = list(logs_dir.glob("extractor_responses_*.log"))
        assert len(log_files) > 0, "Log file should be created"
        
        log_content = log_files[0].read_text(encoding='utf-8')
        assert len(log_content) > 0, "Log file should contain entries"
        assert "Starting ECI responses" in log_content or \
               "Processing" in log_content, \
               "Log should contain processing messages"
        
        # Cleanup this session directory after test
        shutil.rmtree(session_dir)

    def test_csv_file_is_created(self, program_root_dir):
        """Test that CSV file is created in output directory."""
        from unittest.mock import patch
        from datetime import datetime
        
        eci_file = "2020_000001_en.html"
        
        session_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        session_dir = self.temp_session_path / session_name
        
        # Setup test data
        test_data_dir = program_root_dir / "tests" / "data" / "example_htmls" / "responses"
        year_dir = session_dir / "responses" / "2020"
        year_dir.mkdir(parents=True, exist_ok=True)
        
        logs_dir = session_dir / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Create responses_list.csv in responses directory
        responses_list_path = year_dir.parent / "responses_list.csv"
        with open(responses_list_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["url_find_initiative", "registration_number", "title", "datetime"])
            writer.writeheader()
            writer.writerow({
                "url_find_initiative": "https://example.com/2020/000001",
                "registration_number": "2020/000001",
                "title": "Test Initiative",
                "datetime": "2024-10-09 14:00:00"
            })
        
        # Copy example file from partial_success subdirectory
        example_file = test_data_dir / "partial_success" / "2020" / eci_file
        if example_file.exists():
            shutil.copy(example_file, year_dir / eci_file)
        else:
            raise FileNotFoundError(f"Example file not found:\n{str(example_file)}")
        
        # Run processor with mock
        processor = self.ECIResponseDataProcessor(
            data_root=str(self.temp_session_path),
            logger=None
        )
        
        def mock_find_session():
            processor.last_session_scraping_dir = session_dir
            return session_dir
        
        with patch.object(processor, 'find_latest_scrape_session', side_effect=mock_find_session):
            processor.run()
        
        # Check CSV file was created in session directory
        csv_files = list(session_dir.glob("eci_responses_*.csv"))
        assert len(csv_files) > 0, "CSV file should be created"
        assert csv_files[0].exists(), "CSV file should exist"
        
        # Cleanup
        shutil.rmtree(session_dir)

    def test_csv_contains_correct_headers(self, program_root_dir):
        """Test that CSV contains all required column headers."""
        from unittest.mock import patch
        from datetime import datetime
        
        eci_file = "2012_000003_en.html"
        
        # Create session directory with timestamp
        session_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        session_dir = self.temp_session_path / session_name
        
        # Setup and run processor
        test_data_dir = program_root_dir / "tests" / "data" / "example_htmls" / "responses"
        year_dir = session_dir / "responses" / "2012"
        year_dir.mkdir(parents=True, exist_ok=True)
        
        logs_dir = session_dir / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Create responses_list.csv in responses directory
        responses_list_path = year_dir.parent / "responses_list.csv"
        with open(responses_list_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["url_find_initiative", "registration_number", "title", "datetime"])
            writer.writeheader()
            writer.writerow({
                "url_find_initiative": "https://example.com/2012/000003",
                "registration_number": "2012/000003",
                "title": "Test Initiative",
                "datetime": "2024-10-09 14:00:00"
            })
        
        # Copy example file from strong_legislative_success subdirectory
        example_file = test_data_dir / "strong_legislative_success" / "2012" / eci_file
        if example_file.exists():
            shutil.copy(example_file, year_dir / eci_file)
        else:
            raise FileNotFoundError(f"Example file not found:\n{str(example_file)}")
        
        processor = self.ECIResponseDataProcessor(
            data_root=str(self.temp_session_path),
            logger=None
        )
        
        def mock_find_session():
            processor.last_session_scraping_dir = session_dir
            return session_dir
        
        with patch.object(processor, 'find_latest_scrape_session', side_effect=mock_find_session):
            processor.run()
        
        # Read CSV and check headers
        csv_files = list(session_dir.glob("eci_responses_*.csv"))
        assert len(csv_files) > 0, "CSV file should exist"
        
        with open(csv_files[0], 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            
            for required_column in REQUIRED_RESPONSES_CSV_COLUMNS:
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
        test_data_dir = program_root_dir / "tests" / "data" / "example_htmls" / "responses"
        
        # Create year directories for multiple years
        year_2017_dir = session_dir / "responses" / "2017"
        year_2017_dir.mkdir(parents=True, exist_ok=True)
        
        year_2018_dir = session_dir / "responses" / "2018"
        year_2018_dir.mkdir(parents=True, exist_ok=True)
        
        logs_dir = session_dir / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Create responses_list.csv with multiple entries in responses directory
        responses_list_path = year_2017_dir.parent / "responses_list.csv"
        with open(responses_list_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["url_find_initiative", "registration_number", "title", "datetime"])
            writer.writeheader()
            writer.writerows([
                {
                    "url_find_initiative": "https://example.com/2017/000002",
                    "registration_number": "2017/000002",
                    "title": "Test Initiative 1",
                    "datetime": "2024-10-09 14:00:00"
                },
                {
                    "url_find_initiative": "https://example.com/2018/000004",
                    "registration_number": "2018/000004",
                    "title": "Test Initiative 2",
                    "datetime": "2024-10-09 14:05:00"
                }
            ])
        
        # Copy multiple files from different categories
        eci_files = [
            ("partial_success", "2017", "2017_000002_en.html"),
            ("strong_commitment_delayed", "2018", "2018_000004_en.html")
        ]
        
        copied_count = 0
        for category, year, eci_file in eci_files:
            example_file = test_data_dir / category / year / eci_file
            year_dir = session_dir / "responses" / year
            
            if example_file.exists():
                shutil.copy(example_file, year_dir / eci_file)
                copied_count += 1
        
        # Run processor
        processor = self.ECIResponseDataProcessor(
            data_root=str(self.temp_session_path),
            logger=None
        )
        
        def mock_find_session():
            processor.last_session_scraping_dir = session_dir
            return session_dir
        
        with patch.object(processor, 'find_latest_scrape_session', side_effect=mock_find_session):
            processor.run()
        
        # Count CSV rows
        csv_files = list(session_dir.glob("eci_responses_*.csv"))
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
        
        eci_file = "2021_000006_en.html"
        
        session_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        session_dir = self.temp_session_path / session_name
        
        # Setup and run
        test_data_dir = program_root_dir / "tests" / "data" / "example_htmls" / "responses"
        year_dir = session_dir / "responses" / "2021"
        year_dir.mkdir(parents=True, exist_ok=True)
        
        logs_dir = session_dir / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Create responses_list.csv in responses directory
        responses_list_path = year_dir.parent / "responses_list.csv"
        with open(responses_list_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["url_find_initiative", "registration_number", "title", "datetime"])
            writer.writeheader()
            writer.writerow({
                "url_find_initiative": "https://example.com/2021/000006",
                "registration_number": "2021/000006",
                "title": "Test Initiative",
                "datetime": "2024-10-09 14:00:00"
            })
        
        # Copy example file from partial_success subdirectory
        example_file = test_data_dir / "partial_success" / "2021" / eci_file
        if example_file.exists():
            shutil.copy(example_file, year_dir / eci_file)
        else:
            raise FileNotFoundError(f"Example file not found:\n{str(example_file)}")
        
        processor = self.ECIResponseDataProcessor(
            data_root=str(self.temp_session_path),
            logger=None
        )
        
        def mock_find_session():
            processor.last_session_scraping_dir = session_dir
            return session_dir
        
        with patch.object(processor, 'find_latest_scrape_session', side_effect=mock_find_session):
            processor.run()
        
        # Try reading CSV with UTF-8
        csv_files = list(session_dir.glob("eci_responses_*.csv"))
        assert len(csv_files) > 0, "CSV file should exist"
        
        try:
            with open(csv_files[0], 'r', encoding='utf-8') as f:
                content = f.read()
                assert len(content) > 0, "CSV should have content"
        except UnicodeDecodeError:
            pytest.fail("CSV file should be UTF-8 encoded")
        
        # Cleanup
        shutil.rmtree(session_dir)

    def test_processor_raises_error_with_zero_responses(self):
        """Test that processor raises FileNotFoundError when no response HTML files exist.
        
        This validates the processor's actual behavior: it should fail fast with a clear
        error message when the responses directory is empty, rather than creating an
        empty CSV file.
        """
        from unittest.mock import patch
        from datetime import datetime
        
        session_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        session_dir = self.temp_session_path / session_name
        
        # Create empty directory structure (no HTML files)
        year_dir = session_dir / "responses" / "2024"
        year_dir.mkdir(parents=True, exist_ok=True)
        
        logs_dir = session_dir / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Create empty responses_list.csv in responses directory
        responses_list_path = year_dir.parent / "responses_list.csv"
        with open(responses_list_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["url_find_initiative", "registration_number", "title", "datetime"])
            writer.writeheader()
        
        # Run processor with empty directory
        processor = self.ECIResponseDataProcessor(
            data_root=str(self.temp_session_path),
            logger=None
        )
        
        def mock_find_session():
            processor.last_session_scraping_dir = session_dir
            return session_dir
        
        # The processor should raise FileNotFoundError when no HTML files are found
        with patch.object(processor, 'find_latest_scrape_session', side_effect=mock_find_session):
            with pytest.raises(FileNotFoundError) as exc_info:
                processor.run()
        
        # Verify the error message is informative
        assert "No HTML response files found" in str(exc_info.value), \
            "Error message should clearly state no HTML files were found"
        
        # Verify no CSV was created (correct behavior - fail fast instead of creating empty file)
        csv_files = list(session_dir.glob("eci_responses_*.csv"))
        assert len(csv_files) == 0, \
            "No CSV should be created when there are no HTML files to process"
        
        # Verify log was created and contains processing start messages
        log_files = list(logs_dir.glob("extractor_responses_*.log"))
        assert len(log_files) > 0, "Log file should be created even when processing fails"
        
        log_content = log_files[0].read_text(encoding='utf-8')
        assert "Starting ECI responses" in log_content, \
            "Log should contain processing start message"
        assert "Processing session:" in log_content, \
            "Log should contain session information"
        
        # Cleanup
        shutil.rmtree(session_dir)
