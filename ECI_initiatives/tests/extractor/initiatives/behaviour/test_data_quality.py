"""
Test suite for validating data quality in extracted data.

Tests focus on:
 - Required fields are never None
 - Optional fields handle None correctly
 - JSON fields are valid
 - No duplicate registration numbers
 - CSV structure integrity
"""

# Standard library
import csv
import tempfile
import shutil
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# Third party
import pytest

# Test data
from ECI_initiatives.tests.consts import REQUIRED_EXTRACTOR_CSV_COLUMNS


class TestRequiredFieldValidation:
    """Tests for required field validation."""
    
    def test_registration_number_never_none(self, program_root_dir):
        """Test that registration_number is never None in CSV."""

        from ECI_initiatives.extractor.initiatives.processor import ECIDataProcessor
        from datetime import datetime
        
        eci_name = "2024_000004_en.html"
        
        # Setup temp environment
        temp_dir = tempfile.mkdtemp(prefix="eci_test_")
        temp_path = Path(temp_dir)
        
        # Create session directory with timestamp pattern
        session_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        session_dir = temp_path / session_name
        
        pages_dir = session_dir / "initiatives" / "pages" / "2024"
        logs_dir = session_dir / "logs"
        pages_dir.mkdir(parents=True, exist_ok=True)
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy test file
        test_file = program_root_dir / "tests" / "data" / "example_htmls" / "initiatives" / eci_name
        
        if test_file.exists():
            shutil.copy(test_file, pages_dir / eci_name)
        else:
            raise FileNotFoundError(f"Test data file not found: {test_file}")
        
        # Mock find_latest_scrape_session to return our test session
        with patch.object(ECIDataProcessor, 'find_latest_scrape_session', return_value=session_dir):

            # Run processor
            processor = ECIDataProcessor(data_root=str(temp_path), logger=None)
            processor.run()
        
        # Check CSV in the session directory
        csv_files = list(session_dir.glob("eci_initiatives_*.csv"))
        assert len(csv_files) > 0, "CSV should be created"
        
        with open(csv_files[0], 'r', encoding='utf-8') as f:

            reader = csv.DictReader(f)

            for row in reader:
                assert row['registration_number'], "registration_number should not be None or empty"
                assert row['registration_number'] != "None", "registration_number should not be literal 'None'"
        
        # Cleanup
        shutil.rmtree(temp_path)
    
    def test_title_never_none(self, program_root_dir):
        """Test that title is never None in CSV."""

        from ECI_initiatives.extractor.initiatives.processor import ECIDataProcessor
        from datetime import datetime
        
        eci_name = "2024_000004_en.html"
        
        temp_dir = tempfile.mkdtemp(prefix="eci_test_")
        temp_path = Path(temp_dir)
        session_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        session_dir = temp_path / session_name
        
        pages_dir = session_dir / "initiatives" / "pages" / "2024"
        logs_dir = session_dir / "logs"

        pages_dir.mkdir(parents=True, exist_ok=True)
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        test_file = program_root_dir / "tests" / "data" / "example_htmls" / "initiatives" / eci_name
        if test_file.exists():
            shutil.copy(test_file, pages_dir / eci_name)
        else:
            raise FileNotFoundError(f"Test data file not found: {test_file}")
        
        with patch.object(ECIDataProcessor, 'find_latest_scrape_session', return_value=session_dir):

            processor = ECIDataProcessor(data_root=str(temp_path), logger=None)
            processor.run()
        
        csv_files = list(session_dir.glob("eci_initiatives_*.csv"))

        with open(csv_files[0], 'r', encoding='utf-8') as f:

            reader = csv.DictReader(f)
            for row in reader:
                assert row['title'], "title should not be None or empty"
        
        shutil.rmtree(temp_path)
    
    def test_url_never_none(self, program_root_dir):
        """Test that url is never None in CSV."""

        from ECI_initiatives.extractor.initiatives.processor import ECIDataProcessor
        from datetime import datetime
        
        eci_name = "2024_000004_en.html"
        
        temp_dir = tempfile.mkdtemp(prefix="eci_test_")
        temp_path = Path(temp_dir)
        session_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        session_dir = temp_path / session_name
        
        pages_dir = session_dir / "initiatives" / "pages" / "2024"
        pages_dir.mkdir(parents=True, exist_ok=True)
        
        test_file = program_root_dir / "tests" / "data" / "example_htmls" / "initiatives" / eci_name

        if test_file.exists():
            shutil.copy(test_file, pages_dir / eci_name)
        else:
            raise FileNotFoundError(f"Test data file not found: {test_file}")

        with patch.object(ECIDataProcessor, 'find_latest_scrape_session', return_value=session_dir):
            processor = ECIDataProcessor(data_root=str(temp_path), logger=None)
            processor.run()
        
        csv_files = list(session_dir.glob("eci_initiatives_*.csv"))

        with open(csv_files[0], 'r', encoding='utf-8') as f:

            reader = csv.DictReader(f)
            for row in reader:
                assert row['url'], "url should not be None or empty"
        
        shutil.rmtree(temp_path)
    
    def test_timestamps_never_none(self, program_root_dir):
        """Test that timestamps are never None."""

        from ECI_initiatives.extractor.initiatives.processor import ECIDataProcessor
        from datetime import datetime
        
        eci_name = "2024_000004_en.html"
        
        temp_dir = tempfile.mkdtemp(prefix="eci_test_")
        temp_path = Path(temp_dir)
        session_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        session_dir = temp_path / session_name
        
        pages_dir = session_dir / "initiatives" / "pages" / "2024"
        pages_dir.mkdir(parents=True, exist_ok=True)
        
        test_file = program_root_dir / "tests" / "data" / "example_htmls" / "initiatives" / eci_name

        if test_file.exists():
            shutil.copy(test_file, pages_dir / eci_name)
        else:
            raise FileNotFoundError(f"Test data file not found: {test_file}")

        with patch.object(ECIDataProcessor, 'find_latest_scrape_session', return_value=session_dir):
            processor = ECIDataProcessor(data_root=str(temp_path), logger=None)
            processor.run()
        
        csv_files = list(session_dir.glob("eci_initiatives_*.csv"))

        with open(csv_files[0], 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                assert row['created_timestamp'], "created_timestamp should not be None"
                assert row['last_updated'], "last_updated should not be None"
        
        shutil.rmtree(temp_path)


class TestJSONFieldValidation:
    """Tests for JSON field validation."""
    
    def test_json_fields_are_valid_or_none(self, program_root_dir):
        """Test that JSON fields are either valid JSON or empty."""

        from ECI_initiatives.extractor.initiatives.processor import ECIDataProcessor
        from datetime import datetime
        
        eci_name = "2024_000004_en.html"
        
        temp_dir = tempfile.mkdtemp(prefix="eci_test_")
        temp_path = Path(temp_dir)
        session_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        session_dir = temp_path / session_name
        
        pages_dir = session_dir / "initiatives" / "pages" / "2024"
        pages_dir.mkdir(parents=True, exist_ok=True)
        
        test_file = program_root_dir / "tests" / "data" / "example_htmls" / "initiatives" / eci_name

        if test_file.exists():
            shutil.copy(test_file, pages_dir / eci_name)
        else:
            raise FileNotFoundError(f"Test data file not found: {test_file}")

        with patch.object(ECIDataProcessor, 'find_latest_scrape_session', return_value=session_dir):
            processor = ECIDataProcessor(data_root=str(temp_path), logger=None)
            processor.run()
        
        json_fields = ['signatures_collected_by_country', 'funding_by', 'organizer_representative']
        
        csv_files = list(session_dir.glob("eci_initiatives_*.csv"))

        with open(csv_files[0], 'r', encoding='utf-8') as f:

            reader = csv.DictReader(f)

            for row in reader:

                for field in json_fields:
                    value = row.get(field, '')

                    if value and value != 'None':

                        try:
                            json.loads(value)

                        except json.JSONDecodeError:
                            pytest.fail(f"Field {field} contains invalid JSON: {value}")
        
        shutil.rmtree(temp_path)


class TestCSVStructure:
    """Tests for CSV structure integrity."""
    
    def test_all_rows_same_column_count(self, program_root_dir):
        """Test that all CSV rows have same column count as headers."""
        
        from ECI_initiatives.extractor.initiatives.processor import ECIDataProcessor
        from datetime import datetime
        
        eci_names = ["2024_000004_en.html", "2024_000005_en.html"]
        
        temp_dir = tempfile.mkdtemp(prefix="eci_test_")
        temp_path = Path(temp_dir)
        session_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        session_dir = temp_path / session_name
        
        # Fix: Use correct directory name - initiative_pages not initiatives/pages
        pages_dir = session_dir / "initiative_pages" / "2024"
        logs_dir = session_dir / "logs"

        pages_dir.mkdir(parents=True, exist_ok=True)
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy multiple test files
        test_data_dir = program_root_dir / "tests" / "data" / "example_htmls" / "initiatives"
        
        for filename in eci_names:

            test_file = test_data_dir / filename

            if test_file.exists():
                shutil.copy(test_file, pages_dir / filename)
            else:
                raise FileNotFoundError(f"Test data file not found: {test_file}")

        # Create processor
        processor = ECIDataProcessor(data_root=str(temp_path), logger=None)
        
        # Mock that sets the attribute
        def mock_find_session():
            processor.last_session_scraping_dir = session_dir
            return session_dir
        
        with patch.object(processor, 'find_latest_scrape_session', side_effect=mock_find_session):
            processor.run()
        
        csv_files = list(session_dir.glob("eci_initiatives_*.csv"))
        assert len(csv_files) > 0, "CSV should be created"
        
        with open(csv_files[0], 'r', encoding='utf-8') as f:

            reader = csv.DictReader(f)
            header_count = len(reader.fieldnames)
            
            # Verify we have headers
            assert header_count > 0, "CSV should have headers"
            
            for row in reader:
                row_count = len(row)
                assert row_count == header_count, \
                    f"Row has {row_count} columns but header has {header_count}"
        
        shutil.rmtree(temp_path)
    
    def test_no_duplicate_registration_numbers(self, program_root_dir):
        """Test that no duplicate registration numbers appear in CSV."""

        from ECI_initiatives.extractor.initiatives.processor import ECIDataProcessor
        from datetime import datetime
        
        eci_names = ["2024_000004_en.html", "2024_000005_en.html", "2024_000007_en.html"]
        
        temp_dir = tempfile.mkdtemp(prefix="eci_test_")
        temp_path = Path(temp_dir)
        session_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        session_dir = temp_path / session_name
        
        # Fix: Use correct directory name
        pages_dir = session_dir / "initiative_pages" / "2024"
        logs_dir = session_dir / "logs"

        pages_dir.mkdir(parents=True, exist_ok=True)
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        test_data_dir = program_root_dir / "tests" / "data" / "example_htmls" / "initiatives"
        
        for filename in eci_names:

            test_file = test_data_dir / filename

            if test_file.exists():
                shutil.copy(test_file, pages_dir / filename)
            else:
                raise FileNotFoundError(f"Test data file not found: {test_file}")
                
        # Create processor
        processor = ECIDataProcessor(data_root=str(temp_path), logger=None)
        
        # Mock that sets the attribute
        def mock_find_session():
            processor.last_session_scraping_dir = session_dir
            return session_dir
        
        with patch.object(processor, 'find_latest_scrape_session', side_effect=mock_find_session):
            processor.run()
        
        csv_files = list(session_dir.glob("eci_initiatives_*.csv"))
        assert len(csv_files) > 0, "CSV should be created"
        
        with open(csv_files[0], 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            reg_numbers = []
            for row in reader:
                reg_numbers.append(row['registration_number'])
            
            assert len(reg_numbers) == len(set(reg_numbers)), \
                "CSV contains duplicate registration numbers"
        
        shutil.rmtree(temp_path)
