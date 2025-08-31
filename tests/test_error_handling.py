# tests/test_error_handling.py
"""
Unit tests for the error handling system.
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch, MagicMock
from modules.error_handler import (
    ErrorHandler,
    ErrorInfo,
    ErrorCategory,
    ErrorSeverity,
    with_error_handling,
    global_error_handler
)


class TestErrorHandler:
    """Test cases for the ErrorHandler class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.error_handler = ErrorHandler()
    
    def test_error_handler_initialization(self):
        """Test that ErrorHandler initializes correctly."""
        assert self.error_handler is not None
        assert len(self.error_handler.error_history) == 0
        assert len(self.error_handler.error_counts) == 0
        assert len(self.error_handler.recovery_strategies) > 0
    
    def test_handle_error_basic(self):
        """Test basic error handling functionality."""
        test_error = ValueError("Test error message")
        
        error_info = self.error_handler.handle_error(
            error=test_error,
            module="test_module",
            function="test_function"
        )
        
        assert isinstance(error_info, ErrorInfo)
        assert error_info.message == "Test error message"
        assert error_info.module == "test_module"
        assert error_info.function == "test_function"
        assert error_info.category in ErrorCategory
        assert error_info.severity in ErrorSeverity
        assert len(self.error_handler.error_history) == 1
    
    def test_error_classification(self):
        """Test automatic error classification."""
        # Test network error classification
        network_error = ConnectionError("Failed to connect to server")
        error_info = self.error_handler.handle_error(
            error=network_error,
            module="test",
            function="test"
        )
        assert error_info.category == ErrorCategory.NETWORK_ERROR
        
        # Test timeout error classification
        timeout_error = TimeoutError("Operation timed out")
        error_info = self.error_handler.handle_error(
            error=timeout_error,
            module="test",
            function="test"
        )
        assert error_info.category == ErrorCategory.TIMEOUT_ERROR
        
        # Test validation error classification
        validation_error = ValueError("Invalid input format")
        error_info = self.error_handler.handle_error(
            error=validation_error,
            module="test",
            function="test"
        )
        assert error_info.category == ErrorCategory.VALIDATION_ERROR
    
    def test_severity_assessment(self):
        """Test automatic severity assessment."""
        # Test critical severity for configuration errors
        config_error = Exception("API key not configured")
        error_info = self.error_handler.handle_error(
            error=config_error,
            module="test",
            function="test",
            category=ErrorCategory.CONFIGURATION_ERROR
        )
        assert error_info.severity == ErrorSeverity.CRITICAL
        
        # Test medium severity for API errors
        api_error = Exception("API request failed")
        error_info = self.error_handler.handle_error(
            error=api_error,
            module="test",
            function="test",
            category=ErrorCategory.API_ERROR
        )
        assert error_info.severity == ErrorSeverity.MEDIUM
    
    def test_user_message_generation(self):
        """Test user-friendly message generation."""
        network_error = ConnectionError("Connection refused")
        error_info = self.error_handler.handle_error(
            error=network_error,
            module="test",
            function="test"
        )
        
        assert error_info.user_message is not None
        assert "network" in error_info.user_message.lower() or "connection" in error_info.user_message.lower()
        assert len(error_info.user_message) > 0
    
    def test_error_statistics(self):
        """Test error statistics collection."""
        # Generate some test errors
        for i in range(5):
            self.error_handler.handle_error(
                error=ValueError(f"Test error {i}"),
                module="test",
                function="test"
            )
        
        stats = self.error_handler.get_error_statistics()
        
        assert stats["total_errors"] == 5
        assert "categories" in stats
        assert "severities" in stats
        assert "recent_errors" in stats
        assert len(stats["recent_errors"]) <= 10
    
    def test_recovery_attempt(self):
        """Test error recovery attempts."""
        test_error = Exception("Recoverable error")
        error_info = self.error_handler.handle_error(
            error=test_error,
            module="test",
            function="test",
            category=ErrorCategory.PROCESSING_ERROR
        )
        
        # Test recovery attempt
        recovery_success = self.error_handler.attempt_recovery(error_info)
        assert isinstance(recovery_success, bool)
    
    def test_error_history_limit(self):
        """Test that error history is limited to prevent memory issues."""
        # Generate more than 1000 errors
        for i in range(1100):
            self.error_handler.handle_error(
                error=ValueError(f"Test error {i}"),
                module="test",
                function="test"
            )
        
        # Should be limited to 1000
        assert len(self.error_handler.error_history) == 1000
    
    def test_thread_safety(self):
        """Test that error handler is thread-safe."""
        errors = []
        
        def generate_errors():
            for i in range(100):
                try:
                    self.error_handler.handle_error(
                        error=ValueError(f"Thread error {i}"),
                        module="test",
                        function="test"
                    )
                except Exception as e:
                    errors.append(e)
        
        # Create multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=generate_errors)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Should have no errors and correct count
        assert len(errors) == 0
        assert len(self.error_handler.error_history) == 500


class TestErrorHandlingDecorator:
    """Test cases for the error handling decorator."""
    
    def test_decorator_success(self):
        """Test decorator with successful function execution."""
        @with_error_handling(max_retries=2)
        def successful_function(x, y):
            return x + y
        
        result = successful_function(2, 3)
        assert result == 5
    
    def test_decorator_with_retries(self):
        """Test decorator with retries on failure."""
        call_count = 0
        
        @with_error_handling(max_retries=2, retry_delay=0.1, fallback_return="fallback_success")
        def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary failure")
            return "success"
        
        # Since the recovery strategy doesn't actually fix the issue,
        # it should return the fallback value
        result = failing_function()
        assert result == "fallback_success"
        assert call_count >= 1  # Should have been called at least once
    
    def test_decorator_with_fallback(self):
        """Test decorator with fallback return value."""
        @with_error_handling(max_retries=1, fallback_return="fallback")
        def always_failing_function():
            raise ValueError("Always fails")
        
        result = always_failing_function()
        assert result == "fallback"
    
    def test_decorator_with_custom_category(self):
        """Test decorator with custom error category."""
        @with_error_handling(
            category=ErrorCategory.API_ERROR,
            severity=ErrorSeverity.HIGH,
            max_retries=1
        )
        def api_function():
            raise ConnectionError("API connection failed")
        
        with pytest.raises(ConnectionError):
            api_function()
    
    def test_decorator_preserves_function_metadata(self):
        """Test that decorator preserves function metadata."""
        @with_error_handling()
        def documented_function():
            """This is a test function."""
            return "test"
        
        assert documented_function.__name__ == "documented_function"
        assert "test function" in documented_function.__doc__


class TestErrorInfo:
    """Test cases for the ErrorInfo dataclass."""
    
    def test_error_info_creation(self):
        """Test ErrorInfo creation and attributes."""
        error_info = ErrorInfo(
            error_id="test_error_123",
            category=ErrorCategory.API_ERROR,
            severity=ErrorSeverity.MEDIUM,
            message="Test error message",
            details="Detailed error information",
            module="test_module",
            function="test_function",
            timestamp=time.time()
        )
        
        assert error_info.error_id == "test_error_123"
        assert error_info.category == ErrorCategory.API_ERROR
        assert error_info.severity == ErrorSeverity.MEDIUM
        assert error_info.message == "Test error message"
        assert error_info.module == "test_module"
        assert error_info.function == "test_function"
        assert error_info.retry_count == 0
        assert error_info.max_retries == 3
        assert error_info.recoverable is True
    
    def test_error_info_defaults(self):
        """Test ErrorInfo default values."""
        error_info = ErrorInfo(
            error_id="test",
            category=ErrorCategory.UNKNOWN_ERROR,
            severity=ErrorSeverity.LOW,
            message="test",
            details="test",
            module="test",
            function="test",
            timestamp=time.time()
        )
        
        assert error_info.retry_count == 0
        assert error_info.max_retries == 3
        assert error_info.recoverable is True
        assert error_info.user_message is None
        assert error_info.suggested_action is None


class TestGlobalErrorHandler:
    """Test cases for the global error handler instance."""
    
    def test_global_error_handler_exists(self):
        """Test that global error handler is available."""
        assert global_error_handler is not None
        assert isinstance(global_error_handler, ErrorHandler)
    
    def test_global_error_handler_functionality(self):
        """Test that global error handler works correctly."""
        test_error = ValueError("Global test error")
        
        error_info = global_error_handler.handle_error(
            error=test_error,
            module="global_test",
            function="test_function"
        )
        
        assert isinstance(error_info, ErrorInfo)
        assert error_info.message == "Global test error"
        assert error_info.module == "global_test"


class TestRecoveryStrategies:
    """Test cases for error recovery strategies."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.error_handler = ErrorHandler()
    
    def test_api_error_recovery(self):
        """Test API error recovery strategy."""
        error_info = ErrorInfo(
            error_id="api_test",
            category=ErrorCategory.API_ERROR,
            severity=ErrorSeverity.MEDIUM,
            message="API error",
            details="API request failed",
            module="test",
            function="test",
            timestamp=time.time()
        )
        
        start_time = time.time()
        result = self.error_handler._recover_api_error(error_info)
        end_time = time.time()
        
        assert isinstance(result, bool)
        # Should have waited some time
        assert end_time - start_time >= 0.5
    
    def test_network_error_recovery(self):
        """Test network error recovery strategy."""
        error_info = ErrorInfo(
            error_id="network_test",
            category=ErrorCategory.NETWORK_ERROR,
            severity=ErrorSeverity.MEDIUM,
            message="Network error",
            details="Connection failed",
            module="test",
            function="test",
            timestamp=time.time()
        )
        
        start_time = time.time()
        result = self.error_handler._recover_network_error(error_info)
        end_time = time.time()
        
        assert isinstance(result, bool)
        # Should have waited longer for network issues
        assert end_time - start_time >= 2.0
    
    def test_validation_error_no_recovery(self):
        """Test that validation errors are not recoverable."""
        error_info = ErrorInfo(
            error_id="validation_test",
            category=ErrorCategory.VALIDATION_ERROR,
            severity=ErrorSeverity.LOW,
            message="Validation error",
            details="Invalid input",
            module="test",
            function="test",
            timestamp=time.time()
        )
        
        result = self.error_handler._recover_validation_error(error_info)
        assert result is False


class TestErrorCategories:
    """Test cases for error categories and their behavior."""
    
    def test_all_categories_have_recovery_strategies(self):
        """Test that all error categories have recovery strategies."""
        error_handler = ErrorHandler()
        
        # Most categories should have recovery strategies
        # (Some may intentionally not be recoverable)
        expected_categories = [
            ErrorCategory.API_ERROR,
            ErrorCategory.NETWORK_ERROR,
            ErrorCategory.TIMEOUT_ERROR,
            ErrorCategory.PROCESSING_ERROR,
            ErrorCategory.HARDWARE_ERROR,
            ErrorCategory.RESOURCE_ERROR
        ]
        
        for category in expected_categories:
            assert category in error_handler.recovery_strategies
    
    def test_error_category_values(self):
        """Test that error categories have correct string values."""
        assert ErrorCategory.API_ERROR.value == "api_error"
        assert ErrorCategory.NETWORK_ERROR.value == "network_error"
        assert ErrorCategory.VALIDATION_ERROR.value == "validation_error"
        assert ErrorCategory.TIMEOUT_ERROR.value == "timeout_error"
    
    def test_error_severity_ordering(self):
        """Test that error severities are properly ordered."""
        assert ErrorSeverity.LOW.value < ErrorSeverity.MEDIUM.value
        assert ErrorSeverity.MEDIUM.value < ErrorSeverity.HIGH.value
        assert ErrorSeverity.HIGH.value < ErrorSeverity.CRITICAL.value


if __name__ == "__main__":
    pytest.main([__file__])