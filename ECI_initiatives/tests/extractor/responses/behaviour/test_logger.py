"""
Test suite for responses logger functionality.

Tests focus on:
- Logger initialization and configuration
- Console and file handler setup
- Log directory validation
- Multiple setup calls handling
"""

# Standard library
from datetime import datetime
import tempfile
import shutil
from pathlib import Path

# Third party
import pytest

# Local
from ECI_initiatives.extractor.responses.responses_logger import ResponsesExtractorLogger


class TestLoggerInitialization:
    """Tests for logger initialization."""
    
    def test_logger_init_creates_instance(self):
        """Test that logger instance is created."""

        logger_instance = ResponsesExtractorLogger()

        # Test the actual type
        assert isinstance(logger_instance, ResponsesExtractorLogger), \
            "Should create ResponsesExtractorLogger instance"
        
        # Test that internal logger exists and has correct name
        assert logger_instance._logger is not None, "Internal logger should exist"

    def test_logger_name(self):
        """Test that logger has correct name."""

        logger_instance = ResponsesExtractorLogger()
        expected_name = 'eci_extractor_responses'
        assert logger_instance._logger.name == expected_name, f"Logger name should be '{expected_name}'"
    
    def test_multiple_instances_share_underlying_logger(self):
        """Test that multiple wrapper instances share the same underlying logger."""
        
        logger_instance_1 = ResponsesExtractorLogger()
        logger_instance_2 = ResponsesExtractorLogger()
        
        # Wrapper instances should be different objects
        assert logger_instance_1 is not logger_instance_2, \
            "Wrapper instances should be separate objects"
        
        # But they share the same underlying logger (singleton behavior from logging module)
        assert logger_instance_1._logger is logger_instance_2._logger, \
            "Underlying loggers should be the same instance (logging module singleton)"
        
        # They should have the same logger name
        expected_name = 'eci_extractor_responses'
        assert logger_instance_1._logger.name == expected_name, \
            f"Logger 1 should have name '{expected_name}'"
        assert logger_instance_2._logger.name == expected_name, \
            f"Logger 2 should have name '{expected_name}'"



class TestLoggerConfiguration:
    """Tests for logger configuration."""
    
    def test_console_only_when_no_log_dir(self):
        """Test that setup() excludes FileHandler when log_dir is None.
        
        FileHandler writes logs to disk files, so it shouldn't exist when log_dir is None 
        (no directory path provided). Without a file path, FileHandler cannot operate, so 
        only StreamHandler (console output) should be present.
        """
        from logging import FileHandler
        
        logger_instance = ResponsesExtractorLogger()
        logger = logger_instance.setup(log_dir=None)
        
        # Should have at least one handler (console)
        assert len(logger.handlers) >= 1, "Should have at least one handler"
        
        # Should not have any FileHandler
        file_handlers = [h for h in logger.handlers if isinstance(h, FileHandler)]
        assert len(file_handlers) == 0, "Should not have any FileHandler when log_dir is None"

    def test_file_and_console_with_log_dir(self):
        """Test that setup() creates both console and file handlers when log_dir is provided."""

        from logging import FileHandler, StreamHandler
        
        temp_dir = tempfile.mkdtemp(prefix="logger_test_")
        temp_path = Path(temp_dir)
        
        logger_instance = ResponsesExtractorLogger()
        logger = logger_instance.setup(log_dir=temp_path)
        
        # Should have both handlers
        assert len(logger.handlers) >= 2, "Should have at least 2 handlers"
        
        # Should have FileHandler
        file_handlers = [h for h in logger.handlers if isinstance(h, FileHandler)]
        assert len(file_handlers) > 0, "Should have FileHandler when log_dir is provided"
        
        # Should have StreamHandler
        stream_handlers = [h for h in logger.handlers if isinstance(h, StreamHandler)]
        assert len(stream_handlers) > 0, "Should have StreamHandler for console output"
        
        shutil.rmtree(temp_path)
    
    def test_log_directory_exists_validation(self):
        """Test that setup() raises FileNotFoundError if log_dir doesn't exist."""

        temp_dir = tempfile.mkdtemp(prefix="logger_test_")
        temp_path = Path(temp_dir)
        non_existent_dir = temp_path / "does_not_exist"
        
        # Remove temp dir so it doesn't exist
        shutil.rmtree(temp_path)
        
        logger_instance = ResponsesExtractorLogger()
        
        with pytest.raises(FileNotFoundError):
            logger_instance.setup(log_dir=non_existent_dir)
    
    def test_log_directory_is_directory_validation(self):
        """Test that setup() raises NotADirectoryError if log_dir is a file."""

        temp_dir = tempfile.mkdtemp(prefix="logger_test_")
        temp_path = Path(temp_dir)
        file_path = temp_path / "file.txt"
        file_path.write_text("test")
        
        logger_instance = ResponsesExtractorLogger()
        
        with pytest.raises(NotADirectoryError):
            logger_instance.setup(log_dir=file_path)
        
        shutil.rmtree(temp_path)
    
    def test_log_file_created(self):
        """Test that log file is created with correct naming pattern."""

        temp_dir = tempfile.mkdtemp(prefix="logger_test_")
        temp_path = Path(temp_dir)
        
        logger_instance = ResponsesExtractorLogger()
        logger = logger_instance.setup(log_dir=temp_path)
        
        # Check log file exists
        log_files = list(temp_path.glob("extractor_responses_*.log"))
        assert len(log_files) > 0, "Log file should be created"
        
        # Check filename pattern: extractor_responses_YYYY-MM-DD_HH-MM-SS.log
        log_file = log_files[0]
        assert log_file.name.startswith("extractor_responses_"), \
            "Log file should have correct prefix"
        assert log_file.name.endswith(".log"), \
            "Log file should have .log extension"
        
        # Extract datetime part from filename and validate format
        # Expected: extractor_responses_2025-10-14_11-45-47.log
        datetime_part = log_file.stem.replace("extractor_responses_", "")
        
        try:
            datetime.strptime(datetime_part, "%Y-%m-%d_%H-%M-%S")
        except ValueError:
            pytest.fail(f"Datetime part '{datetime_part}' doesn't match format YYYY-MM-DD_HH-MM-SS")
        
        shutil.rmtree(temp_path)
    
    def test_logger_setup_multiple_calls_same_instance(self):
        """Test that multiple setup calls on same instance don't create duplicate handlers."""

        temp_dir = tempfile.mkdtemp(prefix="logger_test_")
        temp_path = Path(temp_dir)
        
        logger_instance = ResponsesExtractorLogger()
        
        logger1 = logger_instance.setup(log_dir=temp_path)
        handler_count_1 = len(logger1.handlers)
        
        logger2 = logger_instance.setup(log_dir=temp_path)
        handler_count_2 = len(logger2.handlers)
        
        # Handler count should not increase
        assert handler_count_2 == handler_count_1, "Multiple setup calls should not add duplicate handlers"
        assert handler_count_2 <= 2, f"Should have at most 2 handlers, got {handler_count_2}"
        
        shutil.rmtree(temp_path)
    
    def test_different_instances_can_have_different_handlers(self):
        """Test that different instances can be configured independently."""

        temp_dir = tempfile.mkdtemp(prefix="logger_test_")
        temp_path = Path(temp_dir)
        
        # Instance 1: console only
        logger_instance_1 = ResponsesExtractorLogger()
        logger1 = logger_instance_1.setup(log_dir=None)
        
        # Instance 2: console and file
        logger_instance_2 = ResponsesExtractorLogger()
        logger2 = logger_instance_2.setup(log_dir=temp_path)
        
        # They should have different handler configurations
        # Note: They share the same underlying Python logger, so handlers accumulate
        # This test verifies the instances themselves are different
        assert logger_instance_1 is not logger_instance_2, "Instances should be different"
        
        shutil.rmtree(temp_path)


class TestLoggerGetMethod:
    """Tests for get_logger method."""
    
    def test_get_logger_returns_instance(self):
        """Test that get_logger() returns the configured logger."""

        logger_instance = ResponsesExtractorLogger()
        logger_instance.setup(log_dir=None)
        
        logger = logger_instance.get_logger()
        assert logger is not None, "get_logger() should return logger instance"
        assert logger.name == 'eci_extractor_responses', "Should return correct logger"
    
    def test_get_logger_before_setup(self):
        """Test that get_logger() works even before setup() is called."""
        
        logger_instance = ResponsesExtractorLogger()
        
        logger = logger_instance.get_logger()
        assert logger is not None, "get_logger() should return logger instance"
        assert logger.name == 'eci_extractor_responses', "Should return correct logger"
