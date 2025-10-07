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
