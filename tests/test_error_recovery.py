# tests/test_error_recovery.py
"""
Unit tests for ErrorRecoveryManager with retry strategies.

Tests exponential backoff retry logic, timeout handling with progressive
timeout reduction, and alternative detection strategy fallback.
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List

from modules.error_recovery import (
    ErrorRecoveryManager,
    RecoveryConfiguration,
    RecoveryStrategy,
    RecoveryResult,
    RecoveryAttempt,
    with_error_recovery
)

from modules.accessibility import (
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


class TestRecoveryConfiguration:
    """Test RecoveryConfiguration validation and behavior."""
    
    def test_default_configuration(self):
        """Test default configuration values."""
        config = RecoveryConfiguration()
        
        assert config.max_retries == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 30.0
        assert config.timeout_reduction_factor == 0.8
        assert config.enable_alternative_strategies is True
        assert config.enable_tree_refresh is True
        assert config.enable_permission_recheck is True
        assert config.exponential_base == 2.0
        assert config.jitter_factor == 0.1
    
    def test_configuration_validation_success(self):
        """Test successful configuration validation."""
        config = RecoveryConfiguration(
            max_retries=5,
            base_delay=0.5,
            max_delay=60.0,
            timeout_reduction_factor=0.7,
            exponential_base=1.5,
            jitter_factor=0.2
        )
        
        # Should not raise any exception
        config.validate()
    
    def test_configuration_validation_failures(self):
        """Test configuration validation failures."""
        # Negative max_retries
        with pytest.raises(ValueError, match="max_retries must be non-negative"):
            config = RecoveryConfiguration(max_retries=-1)
            config.validate()
        
        # Negative base_delay
        with pytest.raises(ValueError, match="base_delay must be non-negative"):
            config = RecoveryConfiguration(base_delay=-1.0)
            config.validate()
        
        # max_delay < base_delay
        with pytest.raises(ValueError, match="max_delay must be >= base_delay"):
            config = RecoveryConfiguration(base_delay=10.0, max_delay=5.0)
            config.validate()
        
        # Invalid timeout_reduction_factor
        with pytest.raises(ValueError, match="timeout_reduction_factor must be between 0 and 1"):
            config = RecoveryConfiguration(timeout_reduction_factor=1.5)
            config.validate()
        
        # Invalid exponential_base
        with pytest.raises(ValueError, match="exponential_base must be > 1"):
            config = RecoveryConfiguration(exponential_base=0.5)
            config.validate()
        
        # Invalid jitter_factor
        with pytest.raises(ValueError, match="jitter_factor must be between 0 and 1"):
            config = RecoveryConfiguration(jitter_factor=1.5)
            config.validate()


class TestErrorRecoveryManager:
    """Test ErrorRecoveryManager functionality."""
    
    @pytest.fixture
    def recovery_manager(self):
        """Create a recovery manager for testing."""
        config = RecoveryConfiguration(
            max_retries=3,
            base_delay=0.1,  # Short delays for testing
            max_delay=1.0,
            jitter_factor=0.0  # No jitter for predictable tests
        )
        return ErrorRecoveryManager(config)
    
    @pytest.fixture
    def mock_operation(self):
        """Create a mock operation for testing."""
        return Mock()
    
    def test_initialization(self, recovery_manager):
        """Test ErrorRecoveryManager initialization."""
        assert recovery_manager.config.max_retries == 3
        assert recovery_manager.config.base_delay == 0.1
        assert recovery_manager.total_recoveries == 0
        assert recovery_manager.successful_recoveries == 0
        assert len(recovery_manager.error_patterns) > 0
        assert len(recovery_manager.success_rates) > 0
    
    def test_strategy_mappings(self, recovery_manager):
        """Test error type to strategy mappings."""
        # Test that all accessibility error types have strategies
        assert 'AccessibilityPermissionError' in recovery_manager.error_patterns
        assert 'ElementNotFoundError' in recovery_manager.error_patterns
        assert 'AccessibilityTimeoutError' in recovery_manager.error_patterns
        
        # Test specific strategy mappings
        permission_strategies = recovery_manager.error_patterns['AccessibilityPermissionError']
        assert RecoveryStrategy.PERMISSION_RECHECK in permission_strategies
        
        timeout_strategies = recovery_manager.error_patterns['AccessibilityTimeoutError']
        assert RecoveryStrategy.TIMEOUT_REDUCTION in timeout_strategies
    
    def test_successful_recovery_on_first_retry(self, recovery_manager, mock_operation):
        """Test successful recovery on first retry attempt."""
        # Mock operation fails once, then succeeds
        mock_operation.side_effect = [ElementNotFoundError("Element not found"), "success"]
        
        result, attempts = recovery_manager.attempt_recovery(
            error=ElementNotFoundError("Element not found"),
            operation=mock_operation
        )
        
        assert result == "success"
        # May take multiple attempts depending on strategy order
        assert len(attempts) >= 1
        assert attempts[-1].result == RecoveryResult.SUCCESS
        assert attempts[-1].strategy in [RecoveryStrategy.TREE_REFRESH, RecoveryStrategy.ALTERNATIVE_METHOD, RecoveryStrategy.TIMEOUT_REDUCTION]
        assert recovery_manager.successful_recoveries == 1
    
    def test_recovery_failure_after_max_retries(self, recovery_manager, mock_operation):
        """Test recovery failure after exhausting max retries."""
        # Mock operation always fails
        error = AccessibilityTimeoutError("Timeout error")
        mock_operation.side_effect = error
        
        with pytest.raises(AccessibilityTimeoutError):
            recovery_manager.attempt_recovery(
                error=error,
                operation=mock_operation
            )
        
        assert recovery_manager.total_recoveries == 1
        assert recovery_manager.successful_recoveries == 0
    
    def test_exponential_backoff_strategy(self, recovery_manager):
        """Test exponential backoff strategy execution."""
        start_time = time.time()
        
        result = recovery_manager._execute_recovery_strategy(
            RecoveryStrategy.EXPONENTIAL_BACKOFF,
            ElementNotFoundError("Test error"),
            1,
            {}
        )
        
        elapsed = time.time() - start_time
        
        assert result == RecoveryResult.RETRY_NEEDED
        assert elapsed >= 0.1  # Should wait at least base_delay
    
    def test_linear_backoff_strategy(self, recovery_manager):
        """Test linear backoff strategy execution."""
        start_time = time.time()
        
        result = recovery_manager._execute_recovery_strategy(
            RecoveryStrategy.LINEAR_BACKOFF,
            ElementNotFoundError("Test error"),
            2,
            {}
        )
        
        elapsed = time.time() - start_time
        
        assert result == RecoveryResult.RETRY_NEEDED
        assert elapsed >= 0.2  # Should wait base_delay * attempt_num
    
    def test_immediate_retry_strategy(self, recovery_manager):
        """Test immediate retry strategy execution."""
        start_time = time.time()
        
        result = recovery_manager._execute_recovery_strategy(
            RecoveryStrategy.IMMEDIATE_RETRY,
            AccessibilityCoordinateError("Test error"),
            1,
            {}
        )
        
        elapsed = time.time() - start_time
        
        assert result == RecoveryResult.RETRY_NEEDED
        assert elapsed < 0.01  # Should be immediate
    
    def test_alternative_method_strategy(self, recovery_manager):
        """Test alternative method strategy execution."""
        context = {}
        
        result = recovery_manager._execute_recovery_strategy(
            RecoveryStrategy.ALTERNATIVE_METHOD,
            ElementNotFoundError("Test error"),
            1,
            context
        )
        
        assert result == RecoveryResult.RETRY_NEEDED
        assert context['use_alternative_method'] is True
        assert 'alternative_method_reason' in context
    
    def test_timeout_reduction_strategy(self, recovery_manager):
        """Test timeout reduction strategy execution."""
        context = {'timeout': 10.0}
        
        result = recovery_manager._execute_recovery_strategy(
            RecoveryStrategy.TIMEOUT_REDUCTION,
            AccessibilityTimeoutError("Test error"),
            1,
            context
        )
        
        assert result == RecoveryResult.RETRY_NEEDED
        assert context['timeout'] == 8.0  # 10.0 * 0.8
        assert context['timeout_reduced'] is True
    
    def test_timeout_reduction_minimum_threshold(self, recovery_manager):
        """Test timeout reduction respects minimum threshold."""
        context = {'timeout': 0.1}  # Very small timeout
        
        recovery_manager._execute_recovery_strategy(
            RecoveryStrategy.TIMEOUT_REDUCTION,
            AccessibilityTimeoutError("Test error"),
            1,
            context
        )
        
        assert context['timeout'] >= 0.5  # Should not go below minimum
    
    def test_tree_refresh_strategy(self, recovery_manager):
        """Test tree refresh strategy execution."""
        context = {}
        
        result = recovery_manager._execute_recovery_strategy(
            RecoveryStrategy.TREE_REFRESH,
            AccessibilityTreeTraversalError("Test error"),
            1,
            context
        )
        
        assert result == RecoveryResult.RETRY_NEEDED
        assert context['refresh_tree'] is True
        assert context['invalidate_cache'] is True
    
    @patch('modules.permission_validator.PermissionValidator')
    def test_permission_recheck_strategy_success(self, mock_validator_class, recovery_manager):
        """Test permission recheck strategy with successful recheck."""
        # Mock successful permission check
        mock_validator = Mock()
        mock_status = Mock()
        mock_status.has_permissions = True
        mock_validator.check_accessibility_permissions.return_value = mock_status
        mock_validator_class.return_value = mock_validator
        
        context = {}
        
        result = recovery_manager._execute_recovery_strategy(
            RecoveryStrategy.PERMISSION_RECHECK,
            AccessibilityPermissionError("Test error"),
            1,
            context
        )
        
        assert result == RecoveryResult.RETRY_NEEDED
        assert context['permissions_rechecked'] is True
    
    @patch('modules.permission_validator.PermissionValidator')
    def test_permission_recheck_strategy_failure(self, mock_validator_class, recovery_manager):
        """Test permission recheck strategy with failed recheck."""
        # Mock failed permission check
        mock_validator = Mock()
        mock_status = Mock()
        mock_status.has_permissions = False
        mock_validator.check_accessibility_permissions.return_value = mock_status
        mock_validator_class.return_value = mock_validator
        
        context = {}
        
        result = recovery_manager._execute_recovery_strategy(
            RecoveryStrategy.PERMISSION_RECHECK,
            AccessibilityPermissionError("Test error"),
            1,
            context
        )
        
        assert result == RecoveryResult.FALLBACK_REQUIRED
    
    def test_strategy_selection(self, recovery_manager):
        """Test strategy selection logic."""
        strategies = [RecoveryStrategy.TREE_REFRESH, RecoveryStrategy.ALTERNATIVE_METHOD]
        
        # First attempt should use first strategy
        strategy = recovery_manager._select_strategy(strategies, 0, [])
        assert strategy == RecoveryStrategy.TREE_REFRESH
        
        # Second attempt should use second strategy
        strategy = recovery_manager._select_strategy(strategies, 1, [])
        assert strategy == RecoveryStrategy.ALTERNATIVE_METHOD
        
        # Beyond available strategies should use exponential backoff
        strategy = recovery_manager._select_strategy(strategies, 2, [])
        assert strategy == RecoveryStrategy.EXPONENTIAL_BACKOFF
    
    def test_strategy_selection_with_successful_previous_attempt(self, recovery_manager):
        """Test strategy selection considers previous successful attempts."""
        strategies = [RecoveryStrategy.TREE_REFRESH, RecoveryStrategy.ALTERNATIVE_METHOD]
        
        # Create a successful previous attempt
        successful_attempt = RecoveryAttempt(
            strategy=RecoveryStrategy.ALTERNATIVE_METHOD,
            attempt_number=1,
            timestamp=time.time(),
            duration=0.1,
            result=RecoveryResult.SUCCESS
        )
        
        # Should prefer the previously successful strategy
        strategy = recovery_manager._select_strategy(strategies, 2, [successful_attempt])
        assert strategy == RecoveryStrategy.ALTERNATIVE_METHOD
    
    def test_retry_with_backoff_success(self, recovery_manager):
        """Test retry_with_backoff with successful operation."""
        call_count = 0
        
        def operation():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ElementNotFoundError("First attempt fails")
            return "success"
        
        result = recovery_manager.retry_with_backoff(operation, max_retries=2)
        
        assert result == "success"
        assert call_count == 2
    
    def test_retry_with_backoff_failure(self, recovery_manager):
        """Test retry_with_backoff with all attempts failing."""
        def operation():
            raise ElementNotFoundError("Always fails")
        
        with pytest.raises(ElementNotFoundError):
            recovery_manager.retry_with_backoff(operation, max_retries=2)
    
    def test_recovery_statistics_empty(self, recovery_manager):
        """Test recovery statistics with no recovery history."""
        stats = recovery_manager.get_recovery_statistics()
        
        assert stats['total_recoveries'] == 0
        assert stats['success_rate'] == 0.0
        assert stats['average_attempts'] == 0.0
        assert len(stats['recent_attempts']) == 0
    
    def test_recovery_statistics_with_data(self, recovery_manager, mock_operation):
        """Test recovery statistics with recovery history."""
        # Perform some recoveries
        mock_operation.side_effect = [ElementNotFoundError("Error"), "success"]
        
        recovery_manager.attempt_recovery(
            error=ElementNotFoundError("Error"),
            operation=mock_operation
        )
        
        stats = recovery_manager.get_recovery_statistics()
        
        assert stats['total_recoveries'] == 1
        assert stats['successful_recoveries'] == 1
        assert stats['success_rate'] == 1.0
        # May have multiple attempts depending on strategy order
        assert len(stats['recent_attempts']) >= 1
    
    def test_success_rate_tracking(self, recovery_manager):
        """Test success rate tracking for strategies."""
        # Record a successful recovery
        attempt = RecoveryAttempt(
            strategy=RecoveryStrategy.TREE_REFRESH,
            attempt_number=1,
            timestamp=time.time(),
            duration=0.1,
            result=RecoveryResult.SUCCESS
        )
        
        initial_rate = recovery_manager.success_rates[RecoveryStrategy.TREE_REFRESH]
        recovery_manager._record_recovery_success(RecoveryStrategy.TREE_REFRESH, attempt)
        
        # Success rate should increase
        new_rate = recovery_manager.success_rates[RecoveryStrategy.TREE_REFRESH]
        assert new_rate > initial_rate
    
    def test_thread_safety(self, recovery_manager):
        """Test thread safety of recovery manager."""
        results = []
        errors = []
        
        def worker():
            try:
                def operation():
                    time.sleep(0.01)
                    return "success"
                
                result = recovery_manager.retry_with_backoff(operation, max_retries=1)
                results.append(result)
            except Exception as e:
                errors.append(e)
        
        # Run multiple threads
        threads = [threading.Thread(target=worker) for _ in range(10)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        assert len(errors) == 0
        assert len(results) == 10
        assert all(result == "success" for result in results)


class TestErrorRecoveryDecorator:
    """Test the with_error_recovery decorator."""
    
    def test_decorator_success_without_error(self):
        """Test decorator with function that succeeds immediately."""
        @with_error_recovery(max_retries=2)
        def successful_function():
            return "success"
        
        result = successful_function()
        assert result == "success"
    
    def test_decorator_success_after_retry(self):
        """Test decorator with function that succeeds after retry."""
        call_count = 0
        
        @with_error_recovery(max_retries=2)
        def retry_function():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ElementNotFoundError("First attempt fails")
            return "success"
        
        result = retry_function()
        assert result == "success"
        assert call_count == 2
    
    def test_decorator_failure_after_max_retries(self):
        """Test decorator with function that always fails."""
        @with_error_recovery(max_retries=1)
        def failing_function():
            raise AccessibilityTimeoutError("Always fails")
        
        with pytest.raises(AccessibilityTimeoutError):
            failing_function()
    
    def test_decorator_with_custom_strategies(self):
        """Test decorator with custom recovery strategies."""
        call_count = 0
        
        @with_error_recovery(
            max_retries=2,
            custom_strategies=[RecoveryStrategy.IMMEDIATE_RETRY]
        )
        def custom_strategy_function():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise FuzzyMatchingError("Fuzzy matching failed", "target", "element")
            return "success"
        
        result = custom_strategy_function()
        assert result == "success"


class TestErrorRecoveryIntegration:
    """Integration tests for error recovery with simulated accessibility failures."""
    
    @pytest.fixture
    def recovery_manager(self):
        """Create a recovery manager with realistic configuration."""
        config = RecoveryConfiguration(
            max_retries=3,
            base_delay=0.05,  # Short delays for testing
            max_delay=0.5,
            timeout_reduction_factor=0.8,
            jitter_factor=0.0  # No jitter for predictable tests
        )
        return ErrorRecoveryManager(config)
    
    def test_permission_error_recovery_flow(self, recovery_manager):
        """Test complete recovery flow for permission errors."""
        call_count = 0
        
        def mock_accessibility_operation():
            nonlocal call_count
            call_count += 1
            
            if call_count == 1:
                raise AccessibilityPermissionError("Permissions not granted")
            elif call_count == 2:
                # Simulate permission recheck working
                return "permission_granted"
            else:
                return "success"
        
        with patch('modules.permission_validator.PermissionValidator') as mock_validator_class:
            # Mock successful permission recheck
            mock_validator = Mock()
            mock_status = Mock()
            mock_status.has_permissions = True
            mock_validator.check_accessibility_permissions.return_value = mock_status
            mock_validator_class.return_value = mock_validator
            
            result, attempts = recovery_manager.attempt_recovery(
                error=AccessibilityPermissionError("Permissions not granted"),
                operation=mock_accessibility_operation
            )
            
            assert result == "permission_granted"
            # May take multiple attempts depending on strategy order
            assert len(attempts) >= 1
            # Check that permission recheck was attempted
            permission_attempts = [a for a in attempts if a.strategy == RecoveryStrategy.PERMISSION_RECHECK]
            assert len(permission_attempts) >= 1
            # Check that the final attempt was successful
            assert attempts[-1].result == RecoveryResult.SUCCESS
    
    def test_timeout_error_recovery_with_timeout_reduction(self, recovery_manager):
        """Test timeout error recovery with progressive timeout reduction."""
        call_count = 0
        context = {'timeout': 10.0}
        
        def mock_timeout_operation():
            nonlocal call_count
            call_count += 1
            
            if call_count == 1:
                raise AccessibilityTimeoutError("Operation timed out")
            else:
                # Check that timeout was reduced
                assert context['timeout'] == 8.0  # 10.0 * 0.8
                return "success_with_reduced_timeout"
        
        result, attempts = recovery_manager.attempt_recovery(
            error=AccessibilityTimeoutError("Operation timed out"),
            operation=mock_timeout_operation,
            context=context
        )
        
        assert result == "success_with_reduced_timeout"
        assert context['timeout_reduced'] is True
    
    def test_element_not_found_recovery_with_tree_refresh(self, recovery_manager):
        """Test element not found recovery with tree refresh."""
        call_count = 0
        context = {}
        
        def mock_element_search():
            nonlocal call_count
            call_count += 1
            
            if call_count == 1:
                raise ElementNotFoundError("Element not found")
            else:
                # On second call, just return success (tree refresh would have been executed)
                return "element_found_after_refresh"
        
        result, attempts = recovery_manager.attempt_recovery(
            error=ElementNotFoundError("Element not found"),
            operation=mock_element_search,
            context=context
        )
        
        assert result == "element_found_after_refresh"
        # Find the tree refresh attempt and check its context
        tree_refresh_attempts = [a for a in attempts if a.strategy == RecoveryStrategy.TREE_REFRESH]
        assert len(tree_refresh_attempts) >= 1
        
        # Check that tree refresh was requested in the attempt context
        tree_refresh_attempt = tree_refresh_attempts[0]
        assert tree_refresh_attempt.context.get('refresh_tree') is True
        assert tree_refresh_attempt.context.get('invalidate_cache') is True
    
    def test_multiple_error_types_recovery_sequence(self, recovery_manager):
        """Test recovery sequence with multiple different error types."""
        call_count = 0
        context = {'timeout': 5.0}
        
        def mock_complex_operation():
            nonlocal call_count
            call_count += 1
            
            if call_count == 1:
                raise AccessibilityTimeoutError("First timeout")
            elif call_count == 2:
                raise ElementNotFoundError("Element not found after timeout fix")
            else:
                return "success_after_multiple_recoveries"
        
        # First recovery attempt for timeout error
        try:
            recovery_manager.attempt_recovery(
                error=AccessibilityTimeoutError("First timeout"),
                operation=mock_complex_operation,
                context=context
            )
        except ElementNotFoundError as e:
            # Second recovery attempt for element not found error
            result, attempts = recovery_manager.attempt_recovery(
                error=e,
                operation=mock_complex_operation,
                context=context
            )
            
            assert result == "success_after_multiple_recoveries"
            assert call_count == 3
    
    def test_recovery_performance_tracking(self, recovery_manager):
        """Test that recovery attempts are properly tracked for performance analysis."""
        def mock_operation():
            return "success"
        
        # Perform several recovery operations
        for i in range(5):
            try:
                recovery_manager.attempt_recovery(
                    error=ElementNotFoundError(f"Error {i}"),
                    operation=mock_operation
                )
            except:
                pass
        
        stats = recovery_manager.get_recovery_statistics()
        
        assert stats['total_recoveries'] == 5
        assert stats['successful_recoveries'] == 5
        assert stats['success_rate'] == 1.0
        assert len(stats['recent_attempts']) <= 10  # Should cap at 10 recent attempts


if __name__ == "__main__":
    pytest.main([__file__])