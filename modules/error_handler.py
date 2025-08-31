# modules/error_handler.py
"""
Centralized Error Handling System for AURA

Provides structured error handling, logging, and recovery mechanisms
for all AURA modules with automatic retry logic and user-friendly messaging.
"""

import logging
import time
import traceback
from typing import Dict, Any, Optional, Callable, List, Union
from enum import Enum
from dataclasses import dataclass
from functools import wraps
import threading


class ErrorSeverity(Enum):
    """Error severity levels for classification and handling."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class ErrorCategory(Enum):
    """Categories of errors for better handling and recovery."""
    API_ERROR = "api_error"
    NETWORK_ERROR = "network_error"
    VALIDATION_ERROR = "validation_error"
    HARDWARE_ERROR = "hardware_error"
    CONFIGURATION_ERROR = "configuration_error"
    PROCESSING_ERROR = "processing_error"
    TIMEOUT_ERROR = "timeout_error"
    PERMISSION_ERROR = "permission_error"
    RESOURCE_ERROR = "resource_error"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class ErrorInfo:
    """Structured error information."""
    error_id: str
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    details: str
    module: str
    function: str
    timestamp: float
    retry_count: int = 0
    max_retries: int = 3
    recoverable: bool = True
    user_message: Optional[str] = None
    suggested_action: Optional[str] = None


class ErrorHandler:
    """
    Centralized error handling system with logging, retry logic, and recovery.
    """
    
    def __init__(self):
        """Initialize the error handler."""
        self.logger = logging.getLogger(__name__)
        self.error_history: List[ErrorInfo] = []
        self.error_counts: Dict[str, int] = {}
        self.recovery_strategies: Dict[ErrorCategory, Callable] = {}
        self.lock = threading.Lock()
        
        # Register default recovery strategies
        self._register_default_recovery_strategies()
        
        self.logger.info("ErrorHandler initialized")
    
    def _register_default_recovery_strategies(self) -> None:
        """Register default recovery strategies for different error categories."""
        self.recovery_strategies = {
            ErrorCategory.API_ERROR: self._recover_api_error,
            ErrorCategory.NETWORK_ERROR: self._recover_network_error,
            ErrorCategory.TIMEOUT_ERROR: self._recover_timeout_error,
            ErrorCategory.VALIDATION_ERROR: self._recover_validation_error,
            ErrorCategory.HARDWARE_ERROR: self._recover_hardware_error,
            ErrorCategory.CONFIGURATION_ERROR: self._recover_configuration_error,
            ErrorCategory.PROCESSING_ERROR: self._recover_processing_error,
            ErrorCategory.PERMISSION_ERROR: self._recover_permission_error,
            ErrorCategory.RESOURCE_ERROR: self._recover_resource_error,
        }
    
    def handle_error(
        self,
        error: Exception,
        module: str,
        function: str,
        category: Optional[ErrorCategory] = None,
        severity: Optional[ErrorSeverity] = None,
        context: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        suggested_action: Optional[str] = None
    ) -> ErrorInfo:
        """
        Handle an error with structured logging and classification.
        
        Args:
            error: The exception that occurred
            module: Name of the module where error occurred
            function: Name of the function where error occurred
            category: Error category (auto-detected if None)
            severity: Error severity (auto-detected if None)
            context: Additional context information
            user_message: User-friendly error message
            suggested_action: Suggested action for recovery
            
        Returns:
            ErrorInfo object with structured error details
        """
        try:
            # Auto-detect category and severity if not provided
            if category is None:
                category = self._classify_error(error)
            
            if severity is None:
                severity = self._assess_severity(error, category)
            
            # Generate error ID
            error_id = f"{module}_{function}_{int(time.time())}"
            
            # Create error info
            error_info = ErrorInfo(
                error_id=error_id,
                category=category,
                severity=severity,
                message=str(error),
                details=traceback.format_exc(),
                module=module,
                function=function,
                timestamp=time.time(),
                user_message=user_message or self._generate_user_message(error, category),
                suggested_action=suggested_action or self._generate_suggested_action(category)
            )
            
            # Add context if provided
            if context:
                error_info.details += f"\nContext: {context}"
            
            # Log the error
            self._log_error(error_info)
            
            # Update error statistics
            with self.lock:
                self.error_history.append(error_info)
                self.error_counts[category.value] = self.error_counts.get(category.value, 0) + 1
                
                # Keep only recent errors (last 1000)
                if len(self.error_history) > 1000:
                    self.error_history = self.error_history[-1000:]
            
            return error_info
            
        except Exception as e:
            # Fallback error handling
            self.logger.critical(f"Error handler itself failed: {e}")
            return ErrorInfo(
                error_id="error_handler_failure",
                category=ErrorCategory.UNKNOWN_ERROR,
                severity=ErrorSeverity.CRITICAL,
                message=f"Error handler failure: {e}",
                details=traceback.format_exc(),
                module="error_handler",
                function="handle_error",
                timestamp=time.time(),
                recoverable=False
            )
    
    def _classify_error(self, error: Exception) -> ErrorCategory:
        """
        Automatically classify an error based on its type and message.
        
        Args:
            error: The exception to classify
            
        Returns:
            ErrorCategory for the error
        """
        error_str = str(error).lower()
        error_type = type(error).__name__.lower()
        
        # Network-related errors
        if any(keyword in error_str for keyword in ['connection', 'network', 'dns', 'socket']):
            return ErrorCategory.NETWORK_ERROR
        
        # API-related errors
        if any(keyword in error_str for keyword in ['api', 'http', 'status', 'response']):
            return ErrorCategory.API_ERROR
        
        # Timeout errors
        if any(keyword in error_str for keyword in ['timeout', 'timed out']):
            return ErrorCategory.TIMEOUT_ERROR
        
        # Validation errors
        if any(keyword in error_str for keyword in ['validation', 'invalid', 'format', 'parse']):
            return ErrorCategory.VALIDATION_ERROR
        
        # Permission errors
        if any(keyword in error_str for keyword in ['permission', 'access', 'denied', 'forbidden']):
            return ErrorCategory.PERMISSION_ERROR
        
        # Hardware/device errors
        if any(keyword in error_str for keyword in ['device', 'hardware', 'microphone', 'speaker', 'screen']):
            return ErrorCategory.HARDWARE_ERROR
        
        # Configuration errors
        if any(keyword in error_str for keyword in ['config', 'setting', 'key', 'missing']):
            return ErrorCategory.CONFIGURATION_ERROR
        
        # Resource errors
        if any(keyword in error_str for keyword in ['memory', 'disk', 'resource', 'limit']):
            return ErrorCategory.RESOURCE_ERROR
        
        # Processing errors
        if any(keyword in error_str for keyword in ['process', 'compute', 'calculation']):
            return ErrorCategory.PROCESSING_ERROR
        
        # Check by exception type
        if 'timeout' in error_type:
            return ErrorCategory.TIMEOUT_ERROR
        elif 'connection' in error_type:
            return ErrorCategory.NETWORK_ERROR
        elif 'value' in error_type or 'type' in error_type:
            return ErrorCategory.VALIDATION_ERROR
        elif 'permission' in error_type:
            return ErrorCategory.PERMISSION_ERROR
        
        return ErrorCategory.UNKNOWN_ERROR
    
    def _assess_severity(self, error: Exception, category: ErrorCategory) -> ErrorSeverity:
        """
        Assess the severity of an error based on its type and category.
        
        Args:
            error: The exception
            category: Error category
            
        Returns:
            ErrorSeverity level
        """
        # Critical errors that prevent system operation
        if category in [ErrorCategory.CONFIGURATION_ERROR, ErrorCategory.PERMISSION_ERROR]:
            return ErrorSeverity.CRITICAL
        
        # High severity errors that significantly impact functionality
        if category in [ErrorCategory.HARDWARE_ERROR, ErrorCategory.RESOURCE_ERROR]:
            return ErrorSeverity.HIGH
        
        # Medium severity errors that may cause temporary issues
        if category in [ErrorCategory.API_ERROR, ErrorCategory.NETWORK_ERROR, ErrorCategory.TIMEOUT_ERROR]:
            return ErrorSeverity.MEDIUM
        
        # Low severity errors that are recoverable
        return ErrorSeverity.LOW
    
    def _log_error(self, error_info: ErrorInfo) -> None:
        """
        Log error information with appropriate severity level.
        
        Args:
            error_info: Structured error information
        """
        log_message = (
            f"[{error_info.error_id}] {error_info.category.value.upper()} in "
            f"{error_info.module}.{error_info.function}: {error_info.message}"
        )
        
        if error_info.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message)
            self.logger.critical(f"Details: {error_info.details}")
        elif error_info.severity == ErrorSeverity.HIGH:
            self.logger.error(log_message)
            self.logger.debug(f"Details: {error_info.details}")
        elif error_info.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(log_message)
            self.logger.debug(f"Details: {error_info.details}")
        else:
            self.logger.info(log_message)
            self.logger.debug(f"Details: {error_info.details}")
    
    def _generate_user_message(self, error: Exception, category: ErrorCategory) -> str:
        """
        Generate a user-friendly error message.
        
        Args:
            error: The exception
            category: Error category
            
        Returns:
            User-friendly error message
        """
        messages = {
            ErrorCategory.API_ERROR: "I'm having trouble communicating with my services. Please try again in a moment.",
            ErrorCategory.NETWORK_ERROR: "I'm having network connectivity issues. Please check your internet connection.",
            ErrorCategory.TIMEOUT_ERROR: "The operation is taking longer than expected. Please try again.",
            ErrorCategory.VALIDATION_ERROR: "I received invalid data. Please try rephrasing your request.",
            ErrorCategory.HARDWARE_ERROR: "I'm having trouble accessing your hardware. Please check your device settings.",
            ErrorCategory.CONFIGURATION_ERROR: "There's a configuration issue. Please check the system settings.",
            ErrorCategory.PROCESSING_ERROR: "I encountered an error while processing your request. Please try again.",
            ErrorCategory.PERMISSION_ERROR: "I don't have the necessary permissions. Please check your system settings.",
            ErrorCategory.RESOURCE_ERROR: "System resources are limited. Please try again in a moment.",
            ErrorCategory.UNKNOWN_ERROR: "An unexpected error occurred. Please try again."
        }
        
        return messages.get(category, "An error occurred. Please try again.")
    
    def _generate_suggested_action(self, category: ErrorCategory) -> str:
        """
        Generate suggested action for error recovery.
        
        Args:
            category: Error category
            
        Returns:
            Suggested action for recovery
        """
        actions = {
            ErrorCategory.API_ERROR: "Check API configuration and try again",
            ErrorCategory.NETWORK_ERROR: "Check internet connection and retry",
            ErrorCategory.TIMEOUT_ERROR: "Wait a moment and try again",
            ErrorCategory.VALIDATION_ERROR: "Verify input format and retry",
            ErrorCategory.HARDWARE_ERROR: "Check device connections and permissions",
            ErrorCategory.CONFIGURATION_ERROR: "Review configuration settings",
            ErrorCategory.PROCESSING_ERROR: "Try a simpler request or restart the system",
            ErrorCategory.PERMISSION_ERROR: "Grant necessary permissions and retry",
            ErrorCategory.RESOURCE_ERROR: "Close other applications and try again",
            ErrorCategory.UNKNOWN_ERROR: "Restart the application if problem persists"
        }
        
        return actions.get(category, "Try again or restart the application")
    
    def attempt_recovery(self, error_info: ErrorInfo) -> bool:
        """
        Attempt to recover from an error using registered strategies.
        
        Args:
            error_info: Error information
            
        Returns:
            True if recovery was successful, False otherwise
        """
        if not error_info.recoverable:
            self.logger.info(f"Error {error_info.error_id} marked as non-recoverable")
            return False
        
        recovery_strategy = self.recovery_strategies.get(error_info.category)
        if not recovery_strategy:
            self.logger.warning(f"No recovery strategy for category {error_info.category.value}")
            return False
        
        try:
            self.logger.info(f"Attempting recovery for error {error_info.error_id}")
            success = recovery_strategy(error_info)
            
            if success:
                self.logger.info(f"Recovery successful for error {error_info.error_id}")
            else:
                self.logger.warning(f"Recovery failed for error {error_info.error_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Recovery strategy failed for error {error_info.error_id}: {e}")
            return False
    
    # Recovery strategy implementations
    def _recover_api_error(self, error_info: ErrorInfo) -> bool:
        """Recovery strategy for API errors."""
        # Wait before retry
        time.sleep(min(2 ** error_info.retry_count, 10))
        return True
    
    def _recover_network_error(self, error_info: ErrorInfo) -> bool:
        """Recovery strategy for network errors."""
        # Wait longer for network issues
        time.sleep(min(5 * (error_info.retry_count + 1), 30))
        return True
    
    def _recover_timeout_error(self, error_info: ErrorInfo) -> bool:
        """Recovery strategy for timeout errors."""
        # Exponential backoff for timeouts
        time.sleep(min(3 ** error_info.retry_count, 15))
        return True
    
    def _recover_validation_error(self, error_info: ErrorInfo) -> bool:
        """Recovery strategy for validation errors."""
        # Validation errors usually need manual intervention
        return False
    
    def _recover_hardware_error(self, error_info: ErrorInfo) -> bool:
        """Recovery strategy for hardware errors."""
        # Brief wait for hardware to stabilize
        time.sleep(1)
        return True
    
    def _recover_configuration_error(self, error_info: ErrorInfo) -> bool:
        """Recovery strategy for configuration errors."""
        # Configuration errors usually need manual intervention
        return False
    
    def _recover_processing_error(self, error_info: ErrorInfo) -> bool:
        """Recovery strategy for processing errors."""
        # Brief wait and retry
        time.sleep(0.5)
        return True
    
    def _recover_permission_error(self, error_info: ErrorInfo) -> bool:
        """Recovery strategy for permission errors."""
        # Permission errors usually need manual intervention
        return False
    
    def _recover_resource_error(self, error_info: ErrorInfo) -> bool:
        """Recovery strategy for resource errors."""
        # Wait for resources to free up
        time.sleep(2)
        return True
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """
        Get error statistics and trends.
        
        Returns:
            Dictionary with error statistics
        """
        with self.lock:
            total_errors = len(self.error_history)
            
            if total_errors == 0:
                return {
                    "total_errors": 0,
                    "error_rate": 0.0,
                    "categories": {},
                    "severities": {},
                    "recent_errors": []
                }
            
            # Calculate error rates by category
            category_counts = {}
            severity_counts = {}
            
            for error in self.error_history:
                category_counts[error.category.value] = category_counts.get(error.category.value, 0) + 1
                severity_counts[error.severity.value] = severity_counts.get(error.severity.value, 0) + 1
            
            # Get recent errors (last 10)
            recent_errors = [
                {
                    "error_id": error.error_id,
                    "category": error.category.value,
                    "severity": error.severity.value,
                    "message": error.message,
                    "timestamp": error.timestamp,
                    "module": error.module
                }
                for error in self.error_history[-10:]
            ]
            
            return {
                "total_errors": total_errors,
                "error_rate": total_errors / max(time.time() - self.error_history[0].timestamp, 1) * 3600,  # errors per hour
                "categories": category_counts,
                "severities": severity_counts,
                "recent_errors": recent_errors
            }


def with_error_handling(
    category: Optional[ErrorCategory] = None,
    severity: Optional[ErrorSeverity] = None,
    max_retries: int = 3,
    retry_delay: float = 1.0,
    user_message: Optional[str] = None,
    fallback_return=None
):
    """
    Decorator for automatic error handling with retry logic.
    
    Args:
        category: Error category (auto-detected if None)
        severity: Error severity (auto-detected if None)
        max_retries: Maximum number of retry attempts
        retry_delay: Base delay between retries in seconds
        user_message: Custom user-friendly error message
        fallback_return: Value to return if all retries fail
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            error_handler = ErrorHandler()
            last_error = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                    
                except Exception as e:
                    last_error = e
                    
                    # Handle the error
                    error_info = error_handler.handle_error(
                        error=e,
                        module=func.__module__ or "unknown",
                        function=func.__name__,
                        category=category,
                        severity=severity,
                        user_message=user_message
                    )
                    
                    error_info.retry_count = attempt
                    error_info.max_retries = max_retries
                    
                    # If this is the last attempt, don't retry
                    if attempt >= max_retries:
                        break
                    
                    # Attempt recovery
                    if error_handler.attempt_recovery(error_info):
                        # Wait before retry with exponential backoff
                        wait_time = retry_delay * (2 ** attempt)
                        time.sleep(min(wait_time, 30))  # Cap at 30 seconds
                    else:
                        # Recovery failed, don't retry
                        break
            
            # All retries failed
            if last_error:
                if fallback_return is not None:
                    return fallback_return
                else:
                    raise last_error
            
            return fallback_return
        
        return wrapper
    return decorator


# Global error handler instance
global_error_handler = ErrorHandler()