"""
ECI Responses Extractor Logger
Logging configuration for the responses extractor
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


class ResponsesExtractorLogger:
    """Logger for ECI responses extractor (non-singleton)"""
    
    def __init__(self):
        """Initialize logger instance"""
        self._logger = logging.getLogger('eci_extractor_responses')
        self._logger.setLevel(logging.INFO)
        # Clear any existing handlers
        self._logger.handlers = []
    
    def setup(self, log_dir: Optional[Path] = None) -> logging.Logger:
        """
        Configure logging with file and console handlers
        
        Args:
            log_dir: Directory for log files. If None, only console logging is used.
            
        Returns:
            Configured logger instance
            
        Raises:
            FileNotFoundError: If log_dir doesn't exist
            NotADirectoryError: If log_dir is not a directory
        """
        # Clear existing handlers to prevent duplicates
        self._logger.handlers = []
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Simple formatter for console
        simple_formatter = logging.Formatter('%(levelname)s - %(message)s')
        
        # Console handler (always active)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        self._logger.addHandler(console_handler)
        
        # File handler (optional, only if log_dir is provided)
        if log_dir:
            if not log_dir.exists():
                raise FileNotFoundError(f"Log directory does not exist: {log_dir}")
            if not log_dir.is_dir():
                raise NotADirectoryError(f"Log path is not a directory: {log_dir}")
            
            log_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            log_file = log_dir / f"extractor_responses_{timestamp}.log"
            
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            self._logger.addHandler(file_handler)
            
            self._logger.info(f"Logger initialized. Log file: {log_file}")
        
        return self._logger
    
    def get_logger(self) -> logging.Logger:
        """Get the configured logger instance"""
        return self._logger
