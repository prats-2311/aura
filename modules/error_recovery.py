# modules/error_recovery.py
"""
Error Recovery Manager for AURA Accessibility Operations

Provides intelligent error recovery mechanisms with retry strategies,
timeout handling, and alternative detection strategy fallback for
accessibility API failures.
"""

import logging
import time
import asyncio
from typing import Dict, Any, Optional, List, Callable, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
import threading
import random
from contextlib import contextmanager

# Import accessibility-specific exceptions
from .accessibility import (
    AccessibilityPermissionError,
    AccessibilityAPIUnavailableError,
    ElementNotFoundError,
    AccessibilityTimeoutError,
    AccessibilityTreeTraversalError,
    AccessibilityCoordinateError,
    FuzzyMatchingError,
    AttributeAccessError,
    EnhancedFastPathError
)


class RecoveryStrategy(Enum):
    """Recovery strategy types for different error scenarios."""
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    IMMEDIATE_RETRY = "immediate_retry"
    ALTERNATIVE_METHOD = "alternative_method"
    TIMEOUT_REDUCTION = "timeout_reduction"
    TREE_REFRESH = "tree_refresh"
    PERMISSION_RECHECK = "permission_recheck"
    NO_RECOVERY = "no_recovery"


class RecoveryResult(Enum):
    """Results of recovery attempts."""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILED = "failed"
    RETRY_NEEDED = "retry_needed"
    FALLBACK_REQUIRED = "fallback_required"


@dataclass
class RecoveryAttempt:
    """Information about a recovery attempt."""
    strategy: RecoveryStrategy
    attempt_number: int
    timestamp: float
    duration: float
    result: RecoveryResult
    error_before: Optional[Exception] = None
    error_after: Optional[Exception] = None
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RecoveryConfiguration:
    """Configuration for error recovery behavior."""
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0
    timeout_reduction_factor: float = 0.8
    enable_alternative_strategies: bool = True
    enable_tree_refresh: bool = True
    enable_permission_recheck: bool = True
    exponential_base: float = 2.0
    jitter_factor: float = 0.1
    
    def validate(self) -> None:
        """Validate configuration parameters."""
        if self.max_retries < 0:
            raise ValueError("max_retries must be non-negative")
        if self.base_delay < 0:
            raise ValueError("base_delay must be non-negative")
        if self.max_delay < self.base_delay:
            raise ValueError("max_delay must be >= base_delay")
        if not 0 < self.timeout_reduction_factor <= 1:
            raise ValueError("timeout_reduction_factor must be between 0 and 1")
        if self.exponential_base <= 1:
            raise ValueError("exponential_base must be > 1")
        if not 0 <= self.jitter_factor <= 1:
            raise ValueError("jitter_factor must be between 0 and 1")


class ErrorRecoveryManager:
    """
    Manages intelligent error recovery for accessibility operations.
    
    Provides exponential backoff retry logic, timeout handling with progressive
    timeout reduction, and alternative detection strategy fallback.
    """
    
    def __init__(self, config: Optional[RecoveryConfiguration] = None):
        """
        Initialize the ErrorRecoveryManager.
        
        Args:
            config: Recovery configuration (uses defaults if None)
        """
        self.config = config or RecoveryConfiguration()
        self.config.validate()
        
        self.logger = logging.getLogger(__name__)
        self.recovery_history: List[RecoveryAttempt] = []
        self.error_patterns: Dict[str, List[RecoveryStrategy]] = {}
        self.success_rates: Dict[RecoveryStrategy, float] = {}
        self.lock = threading.Lock()
        
        # Initialize strategy mappings
        self._initialize_strategy_mappings()
        
        # Track performance metrics
        self.total_recoveries = 0
        self.successful_recoveries = 0
        
        self.logger.info("ErrorRecoveryManager initialized")
    
    def _initialize_strategy_mappings(self) -> None:
        """Initialize error type to recovery strategy mappings."""
        self.error_patterns = {
            'AccessibilityPermissionError': [
                RecoveryStrategy.PERMISSION_RECHECK,
                RecoveryStrategy.LINEAR_BACKOFF
            ],
            'AccessibilityAPIUnavailableError': [
                RecoveryStrategy.EXPONENTIAL_BACKOFF,
                RecoveryStrategy.ALTERNATIVE_METHOD
            ],
            'ElementNotFoundError': [
                RecoveryStrategy.TREE_REFRESH,
                RecoveryStrategy.ALTERNATIVE_METHOD,
                RecoveryStrategy.TIMEOUT_REDUCTION
            ],
            'AccessibilityTimeoutError': [
                RecoveryStrategy.TIMEOUT_REDUCTION,
                RecoveryStrategy.EXPONENTIAL_BACKOFF,
                RecoveryStrategy.ALTERNATIVE_METHOD
            ],
            'AccessibilityTreeTraversalError': [
                RecoveryStrategy.TREE_REFRESH,
                RecoveryStrategy.LINEAR_BACKOFF,
                RecoveryStrategy.ALTERNATIVE_METHOD
            ],
            'AccessibilityCoordinateError': [
                RecoveryStrategy.IMMEDIATE_RETRY,
                RecoveryStrategy.ALTERNATIVE_METHOD
            ],
            'FuzzyMatchingError': [
                RecoveryStrategy.ALTERNATIVE_METHOD,
                RecoveryStrategy.IMMEDIATE_RETRY
            ],
            'AttributeAccessError': [
                RecoveryStrategy.EXPONENTIAL_BACKOFF,
                RecoveryStrategy.TREE_REFRESH
            ],
            'EnhancedFastPathError': [
                RecoveryStrategy.ALTERNATIVE_METHOD,
                RecoveryStrategy.TREE_REFRESH,
                RecoveryStrategy.EXPONENTIAL_BACKOFF
            ]
        }
        
        # Initialize success rates
        for strategy in RecoveryStrategy:
            self.success_rates[strategy] = 0.5  # Start with neutral success rate
    
    def attempt_recovery(
        self,
        error: Exception,
        operation: Callable,
        context: Optional[Dict[str, Any]] = None,
        custom_strategies: Optional[List[RecoveryStrategy]] = None
    ) -> Tuple[Any, List[RecoveryAttempt]]:
        """
        Attempt to recover from an error using appropriate strategies.
        
        Args:
            error: The exception that occurred
            operation: The operation to retry
            context: Additional context for recovery
            custom_strategies: Custom recovery strategies to use
            
        Returns:
            Tuple of (operation_result, recovery_attempts)
            
        Raises:
            The original exception if all recovery attempts fail
        """
        context = context or {}
        error_type = type(error).__name__
        
        # Get recovery strategies for this error type
        strategies = custom_strategies or self.error_patterns.get(error_type, [RecoveryStrategy.EXPONENTIAL_BACKOFF])
        
        recovery_attempts = []
        last_error = error
        
        self.logger.info(f"Starting recovery for {error_type}: {error}")
        
        for attempt_num in range(self.config.max_retries + 1):
            if attempt_num == 0:
                # First attempt is the original failure
                continue
            
            # Select strategy for this attempt
            strategy = self._select_strategy(strategies, attempt_num - 1, recovery_attempts)
            
            self.logger.debug(f"Recovery attempt {attempt_num} using strategy {strategy.value}")
            
            # Execute recovery strategy
            recovery_start = time.time()
            try:
                recovery_result = self._execute_recovery_strategy(
                    strategy, error, attempt_num, context
                )
                
                if recovery_result == RecoveryResult.FALLBACK_REQUIRED:
                    # Strategy indicates fallback is needed
                    break
                
                # Try the operation again
                result = operation()
                
                # Success!
                recovery_duration = time.time() - recovery_start
                attempt = RecoveryAttempt(
                    strategy=strategy,
                    attempt_number=attempt_num,
                    timestamp=recovery_start,
                    duration=recovery_duration,
                    result=RecoveryResult.SUCCESS,
                    error_before=last_error,
                    context=context.copy()
                )
                recovery_attempts.append(attempt)
                
                self._record_recovery_success(strategy, attempt)
                self.logger.info(f"Recovery successful after {attempt_num} attempts using {strategy.value}")
                
                return result, recovery_attempts
                
            except Exception as new_error:
                recovery_duration = time.time() - recovery_start
                attempt = RecoveryAttempt(
                    strategy=strategy,
                    attempt_number=attempt_num,
                    timestamp=recovery_start,
                    duration=recovery_duration,
                    result=RecoveryResult.FAILED,
                    error_before=last_error,
                    error_after=new_error,
                    context=context.copy()
                )
                recovery_attempts.append(attempt)
                
                self._record_recovery_failure(strategy, attempt)
                last_error = new_error
                
                self.logger.debug(f"Recovery attempt {attempt_num} failed: {new_error}")
        
        # All recovery attempts failed
        self.logger.warning(f"All recovery attempts failed for {error_type}")
        with self.lock:
            self.recovery_history.extend(recovery_attempts)
            self.total_recoveries += 1
        
        raise last_error
    
    def _select_strategy(
        self,
        strategies: List[RecoveryStrategy],
        attempt_index: int,
        previous_attempts: List[RecoveryAttempt]
    ) -> RecoveryStrategy:
        """
        Select the best recovery strategy for the current attempt.
        
        Args:
            strategies: Available strategies
            attempt_index: Current attempt index (0-based)
            previous_attempts: Previous recovery attempts
            
        Returns:
            Selected recovery strategy
        """
        if attempt_index < len(strategies):
            return strategies[attempt_index]
        
        # If we've exhausted the predefined strategies, use the most successful one
        if previous_attempts:
            successful_strategies = [
                attempt.strategy for attempt in previous_attempts
                if attempt.result == RecoveryResult.SUCCESS
            ]
            if successful_strategies:
                # Use the most recent successful strategy
                return successful_strategies[-1]
        
        # Fallback to exponential backoff
        return RecoveryStrategy.EXPONENTIAL_BACKOFF
    
    def _execute_recovery_strategy(
        self,
        strategy: RecoveryStrategy,
        error: Exception,
        attempt_num: int,
        context: Dict[str, Any]
    ) -> RecoveryResult:
        """
        Execute a specific recovery strategy.
        
        Args:
            strategy: Recovery strategy to execute
            error: The original error
            attempt_num: Current attempt number
            context: Recovery context
            
        Returns:
            Recovery result
        """
        if strategy == RecoveryStrategy.EXPONENTIAL_BACKOFF:
            return self._exponential_backoff(attempt_num)
        
        elif strategy == RecoveryStrategy.LINEAR_BACKOFF:
            return self._linear_backoff(attempt_num)
        
        elif strategy == RecoveryStrategy.IMMEDIATE_RETRY:
            return self._immediate_retry()
        
        elif strategy == RecoveryStrategy.ALTERNATIVE_METHOD:
            return self._try_alternative_method(error, context)
        
        elif strategy == RecoveryStrategy.TIMEOUT_REDUCTION:
            return self._reduce_timeout(context)
        
        elif strategy == RecoveryStrategy.TREE_REFRESH:
            return self._refresh_accessibility_tree(context)
        
        elif strategy == RecoveryStrategy.PERMISSION_RECHECK:
            return self._recheck_permissions(context)
        
        else:
            return RecoveryResult.FAILED
    
    def _exponential_backoff(self, attempt_num: int) -> RecoveryResult:
        """
        Implement exponential backoff with jitter.
        
        Args:
            attempt_num: Current attempt number
            
        Returns:
            Recovery result
        """
        delay = min(
            self.config.base_delay * (self.config.exponential_base ** (attempt_num - 1)),
            self.config.max_delay
        )
        
        # Add jitter to prevent thundering herd
        jitter = delay * self.config.jitter_factor * random.random()
        final_delay = delay + jitter
        
        self.logger.debug(f"Exponential backoff: waiting {final_delay:.2f} seconds")
        time.sleep(final_delay)
        
        return RecoveryResult.RETRY_NEEDED
    
    def _linear_backoff(self, attempt_num: int) -> RecoveryResult:
        """
        Implement linear backoff with jitter.
        
        Args:
            attempt_num: Current attempt number
            
        Returns:
            Recovery result
        """
        delay = min(
            self.config.base_delay * attempt_num,
            self.config.max_delay
        )
        
        # Add jitter
        jitter = delay * self.config.jitter_factor * random.random()
        final_delay = delay + jitter
        
        self.logger.debug(f"Linear backoff: waiting {final_delay:.2f} seconds")
        time.sleep(final_delay)
        
        return RecoveryResult.RETRY_NEEDED
    
    def _immediate_retry(self) -> RecoveryResult:
        """
        Immediate retry without delay.
        
        Returns:
            Recovery result
        """
        self.logger.debug("Immediate retry")
        return RecoveryResult.RETRY_NEEDED
    
    def _try_alternative_method(self, error: Exception, context: Dict[str, Any]) -> RecoveryResult:
        """
        Try alternative detection methods.
        
        Args:
            error: The original error
            context: Recovery context
            
        Returns:
            Recovery result
        """
        self.logger.debug("Trying alternative detection method")
        
        # Set flag in context to indicate alternative method should be used
        context['use_alternative_method'] = True
        context['alternative_method_reason'] = f"Recovery from {type(error).__name__}"
        
        return RecoveryResult.RETRY_NEEDED
    
    def _reduce_timeout(self, context: Dict[str, Any]) -> RecoveryResult:
        """
        Reduce timeout for faster failure detection.
        
        Args:
            context: Recovery context
            
        Returns:
            Recovery result
        """
        current_timeout = context.get('timeout', 10.0)
        new_timeout = current_timeout * self.config.timeout_reduction_factor
        
        # Don't go below a minimum threshold
        min_timeout = 0.5
        new_timeout = max(new_timeout, min_timeout)
        
        context['timeout'] = new_timeout
        context['timeout_reduced'] = True
        
        self.logger.debug(f"Reduced timeout from {current_timeout:.2f}s to {new_timeout:.2f}s")
        
        return RecoveryResult.RETRY_NEEDED
    
    def _refresh_accessibility_tree(self, context: Dict[str, Any]) -> RecoveryResult:
        """
        Request accessibility tree refresh.
        
        Args:
            context: Recovery context
            
        Returns:
            Recovery result
        """
        self.logger.debug("Requesting accessibility tree refresh")
        
        context['refresh_tree'] = True
        context['invalidate_cache'] = True
        
        # Small delay to allow tree to refresh
        time.sleep(0.1)
        
        return RecoveryResult.RETRY_NEEDED
    
    def _recheck_permissions(self, context: Dict[str, Any]) -> RecoveryResult:
        """
        Recheck accessibility permissions.
        
        Args:
            context: Recovery context
            
        Returns:
            Recovery result
        """
        self.logger.debug("Rechecking accessibility permissions")
        
        try:
            # Import here to avoid circular imports
            from modules.permission_validator import PermissionValidator
            
            validator = PermissionValidator()
            status = validator.check_accessibility_permissions()
            
            if status.has_permissions:
                self.logger.info("Permissions are now available")
                context['permissions_rechecked'] = True
                return RecoveryResult.RETRY_NEEDED
            else:
                self.logger.warning("Permissions still not available")
                return RecoveryResult.FALLBACK_REQUIRED
                
        except Exception as e:
            self.logger.error(f"Permission recheck failed: {e}")
            return RecoveryResult.FAILED
    
    def _record_recovery_success(self, strategy: RecoveryStrategy, attempt: RecoveryAttempt) -> None:
        """
        Record a successful recovery attempt.
        
        Args:
            strategy: The successful strategy
            attempt: The recovery attempt
        """
        with self.lock:
            self.recovery_history.append(attempt)
            self.total_recoveries += 1
            self.successful_recoveries += 1
            
            # Update success rate for this strategy
            current_rate = self.success_rates.get(strategy, 0.5)
            # Use exponential moving average
            self.success_rates[strategy] = 0.9 * current_rate + 0.1 * 1.0
    
    def _record_recovery_failure(self, strategy: RecoveryStrategy, attempt: RecoveryAttempt) -> None:
        """
        Record a failed recovery attempt.
        
        Args:
            strategy: The failed strategy
            attempt: The recovery attempt
        """
        with self.lock:
            self.recovery_history.append(attempt)
            
            # Update success rate for this strategy
            current_rate = self.success_rates.get(strategy, 0.5)
            # Use exponential moving average
            self.success_rates[strategy] = 0.9 * current_rate + 0.1 * 0.0
    
    def retry_with_backoff(
        self,
        operation: Callable,
        max_retries: Optional[int] = None,
        custom_config: Optional[RecoveryConfiguration] = None
    ) -> Any:
        """
        Retry an operation with exponential backoff.
        
        Args:
            operation: Operation to retry
            max_retries: Maximum number of retries (uses config default if None)
            custom_config: Custom configuration for this retry
            
        Returns:
            Operation result
            
        Raises:
            The last exception if all retries fail
        """
        config = custom_config or self.config
        max_retries = max_retries or config.max_retries
        
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                return operation()
            except Exception as e:
                last_error = e
                
                if attempt >= max_retries:
                    break
                
                # Calculate delay with exponential backoff
                delay = min(
                    config.base_delay * (config.exponential_base ** attempt),
                    config.max_delay
                )
                
                # Add jitter
                jitter = delay * config.jitter_factor * random.random()
                final_delay = delay + jitter
                
                self.logger.debug(f"Retry attempt {attempt + 1}/{max_retries} after {final_delay:.2f}s")
                time.sleep(final_delay)
        
        if last_error:
            raise last_error
    
    def get_recovery_statistics(self) -> Dict[str, Any]:
        """
        Get recovery statistics and performance metrics.
        
        Returns:
            Dictionary with recovery statistics
        """
        with self.lock:
            if not self.recovery_history:
                return {
                    "total_recoveries": 0,
                    "success_rate": 0.0,
                    "strategy_success_rates": {},
                    "average_attempts": 0.0,
                    "recent_attempts": []
                }
            
            successful_attempts = [
                attempt for attempt in self.recovery_history
                if attempt.result == RecoveryResult.SUCCESS
            ]
            
            # Calculate average attempts per recovery
            recovery_sessions = {}
            for attempt in self.recovery_history:
                session_key = f"{attempt.timestamp:.0f}"  # Group by second
                if session_key not in recovery_sessions:
                    recovery_sessions[session_key] = []
                recovery_sessions[session_key].append(attempt)
            
            total_attempts = sum(len(attempts) for attempts in recovery_sessions.values())
            avg_attempts = total_attempts / len(recovery_sessions) if recovery_sessions else 0
            
            # Get recent attempts (last 10)
            recent_attempts = [
                {
                    "strategy": attempt.strategy.value,
                    "result": attempt.result.value,
                    "duration": attempt.duration,
                    "timestamp": attempt.timestamp
                }
                for attempt in self.recovery_history[-10:]
            ]
            
            return {
                "total_recoveries": self.total_recoveries,
                "successful_recoveries": self.successful_recoveries,
                "success_rate": self.successful_recoveries / self.total_recoveries if self.total_recoveries > 0 else 0.0,
                "strategy_success_rates": dict(self.success_rates),
                "average_attempts": avg_attempts,
                "total_attempts": len(self.recovery_history),
                "recent_attempts": recent_attempts
            }


def with_error_recovery(
    max_retries: int = 3,
    config: Optional[RecoveryConfiguration] = None,
    custom_strategies: Optional[List[RecoveryStrategy]] = None
):
    """
    Decorator for automatic error recovery with retry strategies.
    
    Args:
        max_retries: Maximum number of retry attempts
        config: Custom recovery configuration
        custom_strategies: Custom recovery strategies to use
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            recovery_manager = ErrorRecoveryManager(config)
            
            def operation():
                return func(*args, **kwargs)
            
            try:
                result, attempts = recovery_manager.attempt_recovery(
                    error=Exception("Initial call"),  # Placeholder
                    operation=operation,
                    custom_strategies=custom_strategies
                )
                return result
            except Exception as e:
                # If it's the first call, just execute normally
                if not hasattr(e, '__recovery_attempted__'):
                    try:
                        return func(*args, **kwargs)
                    except Exception as original_error:
                        # Now attempt recovery
                        original_error.__recovery_attempted__ = True
                        result, attempts = recovery_manager.attempt_recovery(
                            error=original_error,
                            operation=operation,
                            custom_strategies=custom_strategies
                        )
                        return result
                else:
                    raise
        
        return wrapper
    return decorator


# Global error recovery manager instance
global_recovery_manager = ErrorRecoveryManager()