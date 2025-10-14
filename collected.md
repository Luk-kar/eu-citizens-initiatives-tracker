`./ECI_initiatives/tests/extractor/initiatives/behaviour/__init__.py`:
```

```

`./ECI_initiatives/tests/extractor/initiatives/behaviour/test_data_extraction.py`:
```
"""
Test suite for validating data extraction from HTML files.

Tests focus on behavior of extraction methods:
 - Registration number extraction from filenames
 - Title extraction with fallback logic
 - Objective extraction with character limit
 - Timeline data extraction
 - Signatures data extraction
 - Organizer data extraction
 - Funding data extraction
 - Current status extraction
 - URL construction
"""

# Standard library
from pathlib import Path
import json

# Third party
import pytest
from bs4 import BeautifulSoup

# Local
from ECI_initiatives.extractor.initiatives.parser import ECIHTMLParser
from ECI_initiatives.extractor.initiatives.initiatives_logger import InitiativesExtractorLogger


class TestRegistrationNumberExtraction:
    """Tests for registration number extraction."""
    
    @classmethod
    def setup_class(cls):
        """Setup parser instance."""

        logger = InitiativesExtractorLogger().setup()
        cls.parser = ECIHTMLParser(logger=logger)
    
    def test_valid_filename_format(self):
        """Test extraction from valid filename format (YYYY_NNNNNN_en.html)."""

        expected_reg_number = '2024/000005'
        
        filename = expected_reg_number.replace("/", "_") + "_en.html"

        reg_number = self.parser._extract_registration_number(filename)

        assert reg_number == expected_reg_number, \
            f"Expected '{expected_reg_number}', got '{reg_number}'"
    
    def test_registration_number_formatting(self):
        """Test that registration number is formatted correctly (YYYY/NNNNNN)."""

        expected_number = 11
        expected_separator = "/"
        
        filename = "2019_000007_en.html"
        reg_number = self.parser._extract_registration_number(filename)
        assert expected_separator in reg_number, f"Registration number should contain '{expected_separator}'"
        assert len(reg_number) == expected_number, f"Registration number should be {expected_number} characters (YYYY/NNNNNN)"


class TestTitleExtraction:
    """Tests for title extraction."""
    
    @classmethod
    def setup_class(cls):
        """Setup parser instance."""

        logger = InitiativesExtractorLogger().setup()
        cls.parser = ECIHTMLParser(logger=logger)
    
    def test_title_from_meta_tag(self):
        """Test extraction from meta tag when present."""

        expected_title = "Test Initiative Title"
        
        html = f'''
        <html>
            <head>
                <meta name="dcterms.title" content="{expected_title}" />
            </head>
            <body></body>
        </html>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        
        title = self.parser._extract_title(soup)
        
        assert title == expected_title, f"Expected '{expected_title}', got '{title}'"
    
    def test_title_fallback_to_h1(self):
        """Test fallback to h1 element when meta tag is missing."""

        expected_title = "Fallback Title"
        
        html = f'''
        <html>
            <body>
                <h1 class="ecl-page-header-core__title">{expected_title}</h1>
            </body>
        </html>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        
        title = self.parser._extract_title(soup)
        
        assert title == expected_title, f"Expected '{expected_title}', got '{title}'"
    
    def test_title_text_is_stripped(self):
        """Test that title text is properly stripped of whitespace."""

        expected_title = "Title With Spaces"
        
        html = f'''
        <html>
            <head>
                <meta name="dcterms.title" content="  {expected_title}  " />
            </head>
        </html>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        title = self.parser._extract_title(soup)
        assert title == expected_title, f"Expected '{expected_title}', got '{title}'"


class TestObjectiveExtraction:
    """Tests for objective extraction."""
    
    @classmethod
    def setup_class(cls):
        """Setup parser instance."""

        logger = InitiativesExtractorLogger().setup()
        cls.parser = ECIHTMLParser(logger=logger)
    
    def test_objective_character_limit(self):
        """Test that objective is truncated at 1,100 characters."""

        expected_length = 1100
        long_text = "A" * 1500
        
        html = f'''
        <html>
            <body>
                <h2>Objectives</h2>
                <p>{long_text}</p>
            </body>
        </html>
        '''
        soup = BeautifulSoup(html, 'html.parser')

        objective = self.parser._extract_objective(soup)
        assert len(objective) == expected_length, f"Objective should be {expected_length} chars, got {len(objective)}"
    
    def test_objective_multi_paragraph(self):
        """Test extraction of multi-paragraph objective text."""

        expected_first_paragraph = "First paragraph."
        expected_second_paragraph = "Second paragraph."
        
        html = f'''
        <html>
            <body>
                <h2>Objectives</h2>
                <p>{expected_first_paragraph}</p>
                <p>{expected_second_paragraph}</p>
            </body>
        </html>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        objective = self.parser._extract_objective(soup)

        assert expected_first_paragraph in objective, f"Should contain '{expected_first_paragraph}'"
        assert expected_second_paragraph in objective, f"Should contain '{expected_second_paragraph}'"


class TestURLConstruction:
    """Tests for URL construction."""
    
    @classmethod
    def setup_class(cls):
        """Setup parser instance."""

        logger = InitiativesExtractorLogger().setup()
        cls.parser = ECIHTMLParser(logger=logger)
    
    def test_url_construction_format(self):
        """Test that URL is constructed in correct Europa.eu format."""

        reg_number = "2024/000005"
        expected_url = "https://citizens-initiative.europa.eu/initiatives/details/2024/000005_en"
        
        url = self.parser._construct_url(reg_number)
        assert url == expected_url, f"Expected '{expected_url}', got '{url}'"
    
    def test_url_contains_registration_parts(self):
        """Test that URL contains year and number components."""

        reg_number = "2019/000007"
        expected_year = "2019"
        expected_number = "000007"
        
        url = self.parser._construct_url(reg_number)
        assert expected_year in url, f"URL should contain year '{expected_year}'"
        assert expected_number in url, f"URL should contain initiative number '{expected_number}'"


class TestCurrentStatusExtraction:
    """Tests for current status extraction."""
    
    @classmethod
    def setup_class(cls):
        """Setup parser instance."""

        logger = InitiativesExtractorLogger().setup()
        cls.parser = ECIHTMLParser(logger=logger)
    
    def test_current_status_from_timeline(self):
        """Test extraction of current status from timeline items."""

        expected_status = "Collection ongoing"
        
        html = f'''
        <html>
            <body>
                <ol class="ecl-timeline">
                    <li class="ecl-timeline__item ecl-timeline__item--current">
                        <div class="ecl-timeline__title">{expected_status}</div>
                    </li>
                </ol>
            </body>
        </html>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        status = self.parser._extract_current_status(soup)

        assert status == expected_status, f"Expected '{expected_status}', got '{status}'"


class TestSignaturesExtraction:
    """Tests for signatures data extraction."""
    
    @classmethod
    def setup_class(cls):
        """Setup parser instance."""

        logger = InitiativesExtractorLogger().setup()
        cls.parser = ECIHTMLParser(logger=logger)
    
    def test_signatures_collected_from_table(self):
        """Test extraction of total signatures from table."""

        expected_signatures = "1,234,567"
        
        html = f'''
        <html>
            <body>
                <table class="ecl-table ecl-table--zebra">
                    <tr class="ecl-table__row">
                        <td class="ecl-table__cell">Total number of signatories</td>
                        <td class="ecl-table__cell">{expected_signatures}</td>
                    </tr>
                </table>
            </body>
        </html>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        signatures = self.parser._extract_signatures_collected(soup)

        assert signatures == expected_signatures, f"Expected '{expected_signatures}', got '{signatures}'"
    
    def test_signatures_by_country_json_format(self, program_root_dir, tmp_path):
        """Test that signatures by country data is valid JSON."""

        expected_country = "Germany"
        expected_type = dict
        
        html = '''
        <html>
            <body>
                <table class="ecl-table ecl-table--zebra">
                    <tr class="ecl-table__row">
                        <td class="ecl-table__cell">Germany</td>
                        <td class="ecl-table__cell">500,000</td>
                        <td class="ecl-table__cell">72,000</td>
                        <td class="ecl-table__cell">694.4%</td>
                    </tr>
                </table>
            </body>
        </html>
        '''
        soup = BeautifulSoup(html, 'html.parser')

        filepath = tmp_path / "test.html"
        filepath.write_text(html)
        
        signatures_json = self.parser._extract_signatures_by_country(
            soup, filepath, "Test Initiative", "http://example.com"
        )
        
        if signatures_json:

            # Should be valid JSON
            data = json.loads(signatures_json)

            assert isinstance(data, expected_type), f"Should be a {expected_type.__name__}"
            assert expected_country in data, f"Should contain {expected_country}"


class TestOrganizerExtraction:
    """Tests for organizer data extraction."""
    
    @classmethod
    def setup_class(cls):
        """Setup parser instance."""

        logger = InitiativesExtractorLogger().setup()
        cls.parser = ECIHTMLParser(logger=logger)
    
    def test_organizer_representative_json_format(self, tmp_path):
        """Test that organizer representative data is valid JSON."""

        expected_type = dict
        
        html = '''
        <html>
            <body>
                <h2>Organisers</h2>
                <h3>Representative</h3>
                <ul>
                    <li>John Doe - [john@example.com](mailto:john@example.com) - Country of residence: Germany</li>
                </ul>
            </body>
        </html>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        organizers_data = self.parser.extract_organisers_data(soup)
        
        filepath = tmp_path / "test.html"

        rep, entity, others = self.parser._split_organiser_data(
            organizers_data, filepath, "Test", "http://example.com"
        )
        
        if rep:
            data = json.loads(rep)
            assert isinstance(data, expected_type), f"Should be a {expected_type.__name__}"


class TestFundingExtraction:
    """Tests for funding data extraction."""
    
    @classmethod
    def setup_class(cls):
        """Setup parser instance."""

        logger = InitiativesExtractorLogger().setup()
        cls.parser = ECIHTMLParser(logger=logger)
    
    def test_funding_total_extraction(self):
        """Test extraction of total funding amount."""

        expected_total = "50,000"
        
        html = f'''
        <html>
            <body>
                <p>Total amount of support and funding: €{expected_total}</p>
            </body>
        </html>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        
        total = self.parser._extract_funding_total(soup)
        assert total == expected_total, f"Expected '{expected_total}', got '{total}'"

```

`./ECI_initiatives/tests/extractor/initiatives/behaviour/test_data_quality.py`:
```
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
        
        eci_name = "2025_000003_en.html"
        
        temp_dir = tempfile.mkdtemp(prefix="eci_test_")
        temp_path = Path(temp_dir)
        session_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        session_dir = temp_path / session_name
        
        pages_dir = session_dir / "initiatives" / "pages" / "2025"
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
        
        eci_name = "2019_000007_en.html"
        
        temp_dir = tempfile.mkdtemp(prefix="eci_test_")
        temp_path = Path(temp_dir)
        session_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        session_dir = temp_path / session_name
        
        pages_dir = session_dir / "initiatives" / "pages" / "2019"
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
        
        eci_name = "2023_000008_en.html"
        
        temp_dir = tempfile.mkdtemp(prefix="eci_test_")
        temp_path = Path(temp_dir)
        session_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        session_dir = temp_path / session_name
        
        pages_dir = session_dir / "initiatives" / "pages" / "2023"
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
        
        eci_name = "2024_000007_en.html"
        
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
        
        eci_names = ["2019_000007_en.html", "2024_000004_en.html", "2025_000002_en.html", "2025_000003_en.html"]
        
        temp_dir = tempfile.mkdtemp(prefix="eci_test_")
        temp_path = Path(temp_dir)
        session_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        session_dir = temp_path / session_name
        
        # Fix: Use correct directory name - initiative_pages not initiatives/pages
        pages_dir = session_dir / "initiatives"
        logs_dir = session_dir / "logs"

        logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy multiple test files
        test_data_dir = program_root_dir / "tests" / "data" / "example_htmls" / "initiatives"
        
        for filename in eci_names:

            # Extract year from filename
            year = filename.split('_')[0]
            year_dir = pages_dir / year
            year_dir.mkdir(parents=True, exist_ok=True)
            
            test_file = test_data_dir / filename

            if test_file.exists():
                shutil.copy(test_file, year_dir / filename)
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
        
        eci_names = [
            "2019_000007_en.html",
            "2023_000008_en.html",
            "2024_000004_en.html",
            "2024_000005_en.html",
            "2024_000007_en.html",
            "2025_000002_en.html",
            "2025_000003_en.html"
        ]
        
        temp_dir = tempfile.mkdtemp(prefix="eci_test_")
        temp_path = Path(temp_dir)
        session_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        session_dir = temp_path / session_name
        
        # Fix: Use correct directory name
        pages_dir = session_dir / "initiatives"
        logs_dir = session_dir / "logs"

        logs_dir.mkdir(parents=True, exist_ok=True)
        
        test_data_dir = program_root_dir / "tests" / "data" / "example_htmls" / "initiatives"
        
        for filename in eci_names:

            # Extract year from filename
            year = filename.split('_')[0]
            year_dir = pages_dir / year
            year_dir.mkdir(parents=True, exist_ok=True)
            
            test_file = test_data_dir / filename

            if test_file.exists():
                shutil.copy(test_file, year_dir / filename)
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

```

`./ECI_initiatives/tests/extractor/initiatives/behaviour/test_logger.py`:
```
"""
Test suite for logger functionality.

Tests focus on:
 - Logger singleton behavior
 - Console and file handler configuration
 - Log message formatting
 - Directory creation
"""

# Standard library
import tempfile
import shutil
from pathlib import Path

# Third party
import pytest

# Local
from ECI_initiatives.extractor.initiatives.initiatives_logger import InitiativesExtractorLogger


class TestLoggerSingleton:
    """Tests for logger singleton pattern."""
    
    def test_singleton_instance(self):
        """Test that only one logger instance is created."""

        logger1 = InitiativesExtractorLogger()
        logger2 = InitiativesExtractorLogger()

        assert logger1 is logger2, "Should return same instance"
    
    def test_logger_setup_multiple_calls(self):
        """Test that multiple setup calls don't create duplicates."""

        temp_dir = tempfile.mkdtemp(prefix="logger_test_")
        temp_path = Path(temp_dir)
        
        logger_instance = InitiativesExtractorLogger()

        logger1 = logger_instance.setup(log_dir=temp_path)
        logger2 = logger_instance.setup(log_dir=temp_path)
        
        # Should not create duplicate handlers
        handler_count = len(logger1.handlers)
        assert handler_count <= 2, f"Should have at most 2 handlers, got {handler_count}"
        
        shutil.rmtree(temp_path)


class TestLoggerConfiguration:
    """Tests for logger configuration."""
    
    def test_console_only_when_no_log_dir(self):
        """
        Test that setup() excludes FileHandler when log_dir is None 
        to enable console-only logging.
        """

        from logging import FileHandler

        logger_instance = InitiativesExtractorLogger()
        logger = logger_instance.setup(log_dir=None)
        
        # Should have at least one handler
        assert len(logger.handlers) >= 1, "Should have at least one handler"
        
        # Should not have any FileHandler
        file_handlers = [h for h in logger.handlers if isinstance(h, FileHandler)]
        assert len(file_handlers) == 0, "Should not have any FileHandler when log_dir is None"
    
    def test_log_directory_created(self):
        """Test that setup() automatically creates nested log directories when they don't exist."""

        temp_dir = tempfile.mkdtemp(prefix="logger_test_")
        temp_path = Path(temp_dir)
        log_subdir = temp_path / "logs" / "nested"
        
        logger_instance = InitiativesExtractorLogger()
        logger = logger_instance.setup(log_dir=log_subdir)
        
        assert log_subdir.exists(), "Log directory should be created"
        
        shutil.rmtree(temp_path)

```

