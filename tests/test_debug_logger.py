"""
Unit tests for debug logging infrastructure.

Tests the configurable debug logging system with different levels,
output formats, and structured logging capabilities.
"""

import pytest
import json
import tempfile
import os
from unittest.mock import patch, MagicMock
from pathlib import Path
import logging

from modules.debug_logger import (
    DebugLogger, StructuredFormatter, DebugContextFilter,
    debug_logger, log_basic, log_detailed, log_verbose
)


class TestDebugContextFilter:
    """Test the debug context filter."""
    
    def test_filter_adds_default_context(self):
        """Test that filter adds default context and category."""
        filter_obj = DebugContextFilter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="test message", args=(), exc_info=None
        )
        
        result = filter_obj.filter(record)
        
        assert result is True
        assert hasattr(record, 'context')
        assert hasattr(record, 'category')
        assert record.category == 'general'
    
    def test_filter_preserves_existing_context(self):
        """Test that filter preserves existing context."""
        filter_obj = DebugContextFilter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="test message", args=(), exc_info=None
        )
        record.context = {"key": "value"}
        record.category = "test_category"
        
        result = filter_obj.filter(record)
        
        assert result is True
        assert record.context == '{"key": "value"}'
        assert record.category == "test_category"


class TestStructuredFormatter:
    """Test the structured formatter."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.format_dict = {
            "timestamp": "%(asctime)s",
            "level": "%(levelname)s",
            "module": "%(name)s",
            "message": "%(message)s",
            "context": "%(context)s",
            "category": "%(category)s"
        }
    
    def test_json_format(self):
        """Test JSON output format."""
        formatter = StructuredFormatter(self.format_dict, "json")
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="test message", args=(), exc_info=None
        )
        record.context = '{"key": "value"}'
        record.category = "test_category"
        
        result = formatter.format(record)
        parsed = json.loads(result)
        
        assert "timestamp" in parsed
        assert parsed["level"] == "INFO"
        assert parsed["module"] == "test"
        assert parsed["message"] == "test message"
        assert parsed["context"] == '{"key": "value"}'
        assert parsed["category"] == "test_category"
    
    def test_plain_format(self):
        """Test plain text output format."""
        formatter = StructuredFormatter(self.format_dict, "plain")
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="test message", args=(), exc_info=None
        )
        record.context = '{"key": "value"}'
        record.category = "test_category"
        
        result = formatter.format(record)
        
        assert "INFO" in result
        assert "test" in result
        assert "test message" in result
        assert "Category: test_category" in result
        assert "Context: " in result
    
    def test_structured_format(self):
        """Test structured output format."""
        formatter = StructuredFormatter(self.format_dict, "structured")
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="test message", args=(), exc_info=None
        )
        record.context = '{"key": "value"}'
        record.category = "test_category"
        
        result = formatter.format(record)
        
        assert "[INFO]" in result
        assert "[test]" in result
        assert "[test_category]" in result
        assert "test message" in result
        assert "Context: " in result


class TestDebugLogger:
    """Test the main debug logger class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Reset singleton instance for testing
        DebugLogger._instance = None
        
        # Mock config values
        self.config_patch = patch.multiple(
            'modules.debug_logger',
            DEBUG_LEVEL="DETAILED",
            DEBUG_LEVELS={"BASIC": 1, "DETAILED": 2, "VERBOSE": 3},
            DEBUG_OUTPUT_FORMAT="structured",
            DEBUG_CATEGORIES={
                "accessibility": True,
                "permissions": True,
                "element_search": True,
                "performance": True
            },
            DEBUG_LOG_TO_FILE=False,
            DEBUG_LOG_TO_CONSOLE=True
        )
        self.config_patch.start()
    
    def teardown_method(self):
        """Clean up after tests."""
        self.config_patch.stop()
        DebugLogger._instance = None
    
    def test_singleton_pattern(self):
        """Test that DebugLogger follows singleton pattern."""
        logger1 = DebugLogger()
        logger2 = DebugLogger()
        
        assert logger1 is logger2
    
    def test_debug_level_filtering(self):
        """Test that debug levels are filtered correctly."""
        logger = DebugLogger()
        mock_logger = MagicMock()
        logger.loggers["test"] = mock_logger
        
        # Should log BASIC and DETAILED (current level is DETAILED)
        logger.log("BASIC", "accessibility", "basic message", module="test")
        logger.log("DETAILED", "accessibility", "detailed message", module="test")
        logger.log("VERBOSE", "accessibility", "verbose message", module="test")
        
        # Should have 2 calls (BASIC and DETAILED)
        assert mock_logger.warning.call_count == 1  # BASIC
        assert mock_logger.info.call_count == 1     # DETAILED
        assert mock_logger.debug.call_count == 0    # VERBOSE filtered out
    
    def test_category_filtering(self):
        """Test that debug categories are filtered correctly."""
        logger = DebugLogger()
        mock_logger = MagicMock()
        logger.loggers["test"] = mock_logger
        
        # Disable element_search for this test
        logger.disable_category("element_search")
        
        # Should log accessibility (enabled) but not element_search (disabled)
        logger.log("BASIC", "accessibility", "accessibility message", module="test")
        logger.log("BASIC", "element_search", "element search message", module="test")
        
        # Should have 1 call (accessibility only, element_search filtered out)
        assert mock_logger.warning.call_count == 1
    
    def test_convenience_methods(self):
        """Test convenience logging methods."""
        logger = DebugLogger()
        mock_logger = MagicMock()
        logger.loggers["test"] = mock_logger
        
        logger.basic("accessibility", "basic message", module="test")
        logger.detailed("accessibility", "detailed message", module="test")
        logger.verbose("accessibility", "verbose message", module="test")
        
        assert mock_logger.warning.call_count == 1  # basic
        assert mock_logger.info.call_count == 1     # detailed
        assert mock_logger.debug.call_count == 0    # verbose filtered out
    
    def test_log_accessibility_tree(self):
        """Test accessibility tree logging."""
        logger = DebugLogger()
        mock_logger = MagicMock()
        logger.loggers["accessibility"] = mock_logger
        
        tree_data = {
            "total_elements": 10,
            "clickable_elements": [{"id": 1}, {"id": 2}],
            "tree_depth": 3
        }
        
        logger.log_accessibility_tree(tree_data, "TestApp")
        
        # Should log detailed level
        assert mock_logger.info.call_count == 1
        call_args = mock_logger.info.call_args
        assert "TestApp" in call_args[0][0]
        assert call_args[1]["extra"]["context"]["total_elements"] == 10
        assert call_args[1]["extra"]["context"]["clickable_elements"] == 2
    
    def test_log_element_search(self):
        """Test element search logging."""
        logger = DebugLogger()
        mock_logger = MagicMock()
        logger.loggers["accessibility"] = mock_logger
        
        search_params = {"role": "button", "timeout": 1000}
        results = {"found": True, "matches": [{"id": 1}], "duration_ms": 150}
        
        logger.log_element_search("Sign In", search_params, results, "TestApp")
        
        assert mock_logger.info.call_count == 1
        call_args = mock_logger.info.call_args
        assert "Sign In" in call_args[0][0]
        assert call_args[1]["extra"]["context"]["found"] is True
        assert call_args[1]["extra"]["context"]["match_count"] == 1
    
    def test_log_fuzzy_matching(self):
        """Test fuzzy matching logging."""
        logger = DebugLogger()
        mock_logger = MagicMock()
        logger.loggers["accessibility"] = mock_logger
        
        candidates = ["Sign In", "Sign Up", "Login"]
        scores = {"Sign In": 100.0, "Sign Up": 75.0, "Login": 60.0}
        best_match = {"text": "Sign In", "score": 100.0}
        
        logger.log_fuzzy_matching("Sign In", candidates, scores, 80.0, best_match)
        
        assert mock_logger.info.call_count == 1
        call_args = mock_logger.info.call_args
        assert "Sign In" in call_args[0][0]
        assert call_args[1]["extra"]["context"]["candidate_count"] == 3
        assert call_args[1]["extra"]["context"]["best_score"] == 100.0
    
    def test_log_permission_check(self):
        """Test permission check logging."""
        logger = DebugLogger()
        mock_logger = MagicMock()
        logger.loggers["permissions"] = mock_logger
        
        details = {"system_version": "macOS 14.0", "app_name": "TestApp"}
        
        logger.log_permission_check("accessibility", True, details)
        
        assert mock_logger.warning.call_count == 1
        call_args = mock_logger.warning.call_args
        assert "accessibility" in call_args[0][0]
        assert "GRANTED" in call_args[0][0]
        assert call_args[1]["extra"]["context"]["status"] is True
    
    def test_log_performance_metric(self):
        """Test performance metric logging."""
        logger = DebugLogger()
        mock_logger = MagicMock()
        logger.loggers["performance"] = mock_logger
        
        details = {"method": "fast_path", "retries": 0}
        
        logger.log_performance_metric("element_detection", 250.5, True, details)
        
        assert mock_logger.warning.call_count == 1
        call_args = mock_logger.warning.call_args
        assert "element_detection" in call_args[0][0]
        assert "250.50ms" in call_args[0][0]
        assert "SUCCESS" in call_args[0][0]
    
    def test_log_error_recovery(self):
        """Test error recovery logging."""
        logger = DebugLogger()
        mock_logger = MagicMock()
        logger.loggers["error_recovery"] = mock_logger
        
        details = {"original_error": "TimeoutError", "retry_count": 2}
        
        logger.log_error_recovery("timeout", "retry_with_backoff", True, details)
        
        assert mock_logger.warning.call_count == 1
        call_args = mock_logger.warning.call_args
        assert "timeout" in call_args[0][0]
        assert "retry_with_backoff" in call_args[0][0]
        assert "SUCCESS" in call_args[0][0]
    
    def test_log_failure_analysis(self):
        """Test failure analysis logging."""
        logger = DebugLogger()
        mock_logger = MagicMock()
        logger.loggers["failure_analysis"] = mock_logger
        
        failure_reasons = ["element_not_found", "permission_denied"]
        recommendations = ["check_permissions", "verify_element_exists"]
        
        logger.log_failure_analysis("Click Sign In", "Sign In", failure_reasons, recommendations, "TestApp")
        
        assert mock_logger.warning.call_count == 1
        call_args = mock_logger.warning.call_args
        assert "Click Sign In" in call_args[0][0]
        assert "Sign In" in call_args[0][0]
        assert call_args[1]["extra"]["context"]["failure_count"] == 2
    
    def test_log_diagnostic_result(self):
        """Test diagnostic result logging."""
        logger = DebugLogger()
        mock_logger = MagicMock()
        logger.loggers["diagnostics"] = mock_logger
        
        results = {"permissions_ok": False, "api_available": True}
        recommendations = ["grant_accessibility_permissions", "restart_application"]
        
        logger.log_diagnostic_result("accessibility_health", results, 1, recommendations)
        
        assert mock_logger.warning.call_count == 1
        call_args = mock_logger.warning.call_args
        assert "accessibility_health" in call_args[0][0]
        assert "found 1 issues" in call_args[0][0]
    
    def test_set_debug_level(self):
        """Test changing debug level."""
        logger = DebugLogger()
        mock_logger = MagicMock()
        logger.loggers["debug_logger"] = mock_logger
        
        logger.set_debug_level("VERBOSE")
        
        assert logger.current_level == 3
        assert mock_logger.warning.call_count == 1
    
    def test_enable_disable_category(self):
        """Test enabling and disabling categories."""
        logger = DebugLogger()
        mock_logger = MagicMock()
        logger.loggers["debug_logger"] = mock_logger
        
        logger.enable_category("test_category")
        logger.disable_category("accessibility")
        
        assert mock_logger.warning.call_count == 2
    
    def test_get_debug_status(self):
        """Test getting debug status."""
        logger = DebugLogger()
        
        status = logger.get_debug_status()
        
        assert "current_level" in status
        assert "level_num" in status
        assert "output_format" in status
        assert "enabled_categories" in status
        assert "disabled_categories" in status
        
        # Check that categories are correctly categorized
        assert "accessibility" in status["enabled_categories"]
        # Note: All categories are enabled in this test config


class TestConvenienceFunctions:
    """Test the convenience functions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Reset singleton instance for testing
        DebugLogger._instance = None
        
        # Mock config values
        self.config_patch = patch.multiple(
            'modules.debug_logger',
            DEBUG_LEVEL="VERBOSE",
            DEBUG_LEVELS={"BASIC": 1, "DETAILED": 2, "VERBOSE": 3},
            DEBUG_CATEGORIES={"test": True},
            DEBUG_LOG_TO_FILE=False,
            DEBUG_LOG_TO_CONSOLE=True
        )
        self.config_patch.start()
    
    def teardown_method(self):
        """Clean up after tests."""
        self.config_patch.stop()
        DebugLogger._instance = None
    
    def test_log_basic_function(self):
        """Test log_basic convenience function."""
        with patch.object(debug_logger, 'basic') as mock_basic:
            log_basic("test", "test message", {"key": "value"}, "test_module")
            
            mock_basic.assert_called_once_with(
                "test", "test message", {"key": "value"}, "test_module"
            )
    
    def test_log_detailed_function(self):
        """Test log_detailed convenience function."""
        with patch.object(debug_logger, 'detailed') as mock_detailed:
            log_detailed("test", "test message", {"key": "value"}, "test_module")
            
            mock_detailed.assert_called_once_with(
                "test", "test message", {"key": "value"}, "test_module"
            )
    
    def test_log_verbose_function(self):
        """Test log_verbose convenience function."""
        with patch.object(debug_logger, 'verbose') as mock_verbose:
            log_verbose("test", "test message", {"key": "value"}, "test_module")
            
            mock_verbose.assert_called_once_with(
                "test", "test message", {"key": "value"}, "test_module"
            )


class TestFileLogging:
    """Test file logging functionality."""
    
    def test_file_logging_setup(self):
        """Test that file logging can be set up correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, "test_debug.log")
            
            with patch.multiple(
                'modules.debug_logger',
                DEBUG_LOG_TO_FILE=True,
                DEBUG_LOG_FILE=log_file,
                DEBUG_LOG_TO_CONSOLE=False,
                DEBUG_LEVEL="BASIC",
                DEBUG_CATEGORIES={"test": True}
            ):
                # Reset singleton
                DebugLogger._instance = None
                
                logger = DebugLogger()
                logger.basic("test", "test message", module="test")
                
                # Force flush
                if logger.file_handler:
                    logger.file_handler.flush()
                
                # Check that log file was created and contains message
                assert os.path.exists(log_file)
                with open(log_file, 'r') as f:
                    content = f.read()
                    assert "test message" in content


if __name__ == "__main__":
    pytest.main([__file__])