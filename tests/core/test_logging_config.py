"""
Test logging configuration module for core shared components.

Tests the logging setup functionality including:
- Logging configuration initialization
- Handler creation and management
- Console and file logging behavior
- Filter functionality for different log levels
"""
import pytest
import logging
import os
import tempfile
from unittest.mock import patch, MagicMock
from src.core.logging_config import setup_logging, ConsoleFilter, LOGS_DIR, LOG_FILENAME


class TestLoggingConfig:
    """Test logging configuration functionality."""
    
    def test_console_filter_allows_warning_and_above(self):
        """Test that ConsoleFilter allows WARNING and above messages."""
        console_filter = ConsoleFilter()
        
        # Create mock log records
        warning_record = MagicMock()
        warning_record.levelno = logging.WARNING
        warning_record.name = 'test.module'
        
        error_record = MagicMock()
        error_record.levelno = logging.ERROR
        error_record.name = 'test.module'
        
        critical_record = MagicMock()
        critical_record.levelno = logging.CRITICAL
        critical_record.name = 'test.module'
        
        assert console_filter.filter(warning_record) is True
        assert console_filter.filter(error_record) is True
        assert console_filter.filter(critical_record) is True
    
    def test_console_filter_allows_main_api_info(self):
        """Test that ConsoleFilter allows INFO messages from src.api.app."""
        console_filter = ConsoleFilter()
        
        info_record = MagicMock()
        info_record.levelno = logging.INFO
        info_record.name = 'src.api.app'
        
        assert console_filter.filter(info_record) is True
    
    def test_console_filter_allows_main_info(self):
        """Test that ConsoleFilter allows INFO messages from __main__."""
        console_filter = ConsoleFilter()
        
        info_record = MagicMock()
        info_record.levelno = logging.INFO
        info_record.name = '__main__'
        
        assert console_filter.filter(info_record) is True
    
    def test_console_filter_blocks_httpx_info(self):
        """Test that ConsoleFilter blocks INFO messages from httpx."""
        console_filter = ConsoleFilter()
        
        info_record = MagicMock()
        info_record.levelno = logging.INFO
        info_record.name = 'httpx'
        
        assert console_filter.filter(info_record) is False
    
    def test_console_filter_blocks_httpx_completely(self):
        """Test that ConsoleFilter blocks all httpx messages."""
        console_filter = ConsoleFilter()
        
        debug_record = MagicMock()
        debug_record.levelno = logging.DEBUG
        debug_record.name = 'httpx'
        
        info_record = MagicMock()
        info_record.levelno = logging.INFO
        info_record.name = 'httpx'
        
        assert console_filter.filter(debug_record) is False
        assert console_filter.filter(info_record) is False
    
    def test_console_filter_blocks_regular_info_and_debug(self):
        """Test that ConsoleFilter blocks regular INFO and DEBUG messages."""
        console_filter = ConsoleFilter()
        
        info_record = MagicMock()
        info_record.levelno = logging.INFO
        info_record.name = 'some.other.module'
        
        debug_record = MagicMock()
        debug_record.levelno = logging.DEBUG
        debug_record.name = 'some.other.module'
        
        assert console_filter.filter(info_record) is False
        assert console_filter.filter(debug_record) is False
    
    @patch('src.core.logging_config.os.makedirs')
    def test_setup_logging_creates_logs_directory(self, mock_makedirs):
        """Test that setup_logging creates the logs directory."""
        setup_logging()
        mock_makedirs.assert_called_with(LOGS_DIR, exist_ok=True)
    
    def test_setup_logging_configures_root_logger(self):
        """Test that setup_logging configures the root logger properly."""
        # Clear any existing handlers
        root_logger = logging.getLogger()
        original_handlers = root_logger.handlers.copy()
        original_level = root_logger.level
        
        try:
            # Clear handlers for clean test
            root_logger.handlers.clear()
            
            setup_logging()
            
            assert root_logger.level == logging.INFO
            assert len(root_logger.handlers) >= 2  # Should have console and file handlers
            
        finally:
            # Restore original state
            root_logger.handlers = original_handlers
            root_logger.level = original_level
    
    def test_setup_logging_avoids_duplicate_handlers(self):
        """Test that setup_logging doesn't add duplicate handlers."""
        root_logger = logging.getLogger()
        original_handler_count = len(root_logger.handlers)
        
        # Call setup_logging multiple times
        setup_logging()
        first_count = len(root_logger.handlers)
        
        setup_logging()
        second_count = len(root_logger.handlers)
        
        # Should not add duplicate handlers
        assert first_count == second_count
    
    def test_setup_logging_configures_third_party_loggers(self):
        """Test that setup_logging configures third-party logger levels."""
        setup_logging()
        
        httpx_logger = logging.getLogger("httpx")
        uvicorn_logger = logging.getLogger("uvicorn")
        fastapi_logger = logging.getLogger("fastapi")
        
        assert httpx_logger.level == logging.WARNING
        assert uvicorn_logger.level == logging.WARNING
        assert fastapi_logger.level == logging.WARNING
    
    def test_setup_logging_configures_file_handler(self):
        """Test that setup_logging configures file handler with rotation."""
        # Clear any existing handlers for clean test
        root_logger = logging.getLogger()
        original_handlers = root_logger.handlers.copy()
        
        try:
            root_logger.handlers.clear()
            setup_logging()
            
            # Check that a RotatingFileHandler was added
            file_handlers = [h for h in root_logger.handlers 
                           if h.__class__.__name__ == 'RotatingFileHandler']
            assert len(file_handlers) > 0, "No RotatingFileHandler found"
            
            # Verify the file handler configuration
            file_handler = file_handlers[0]
            assert file_handler.level == logging.INFO
            assert file_handler.maxBytes == 1*1024*1024  # 1MB
            assert file_handler.backupCount == 5
            
        finally:
            # Restore original handlers
            root_logger.handlers = original_handlers
    
    def test_logs_directory_constant(self):
        """Test that LOGS_DIR constant is correct."""
        assert LOGS_DIR == "logs"
    
    def test_log_filename_constant(self):
        """Test that LOG_FILENAME constant is correct."""
        expected_filename = os.path.join("logs", "app.log")
        assert LOG_FILENAME == expected_filename
    
    def test_integration_logging_works_after_setup(self):
        """Integration test: verify logging works after setup."""
        setup_logging()
        
        # Create a test logger
        test_logger = logging.getLogger('test.integration')
        
        # This should not raise an exception
        test_logger.info("Test info message")
        test_logger.warning("Test warning message")
        test_logger.error("Test error message")
        
        # Verify the logger is properly configured
        assert test_logger.level <= logging.INFO or test_logger.parent.level <= logging.INFO


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 