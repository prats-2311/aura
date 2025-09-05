"""
Test suite for accessibility performance monitoring and optimization features.

Tests performance timing, monitoring, timeout handling, and optimization features
for the enhanced accessibility fast path.
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch, MagicMock
from modules.accessibility import AccessibilityModule, PerformanceMetrics, FastPathPerformanceReport
from modules.error_handler import ErrorHandler


class TestPerformanceMonitoring:
    """Test performance monitoring functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.error_handler = ErrorHandler()
        self.accessibility = AccessibilityModule()
        
        # Enable performance monitoring for tests
        self.accessibility.configure_performance_monitoring(
            enabled=True,
            fast_path_timeout_ms=2000,
            fuzzy_matching_timeout_ms=200,
            attribute_check_timeout_ms=500,
            max_history=50
        )
    
    def test_performance_timer_context_manager(self):
        """Test the performance timer context manager."""
        # Test successful operation
        with self.accessibility._performance_timer("test_operation", timeout_ms=1000) as metrics:
            time.sleep(0.01)  # Simulate work
            assert metrics is not None
            assert metrics.operation_name == "test_operation"
            assert metrics.timeout_ms == 1000
        
        # Check that metrics were recorded
        stats = self.accessibility.get_performance_statistics()
        assert stats['total_operations'] >= 1
        assert stats['successful_operations'] >= 1
        
        # Find our test operation
        recent_ops = stats['recent_operations']
        test_ops = [op for op in recent_ops if op['operation'] == 'test_operation']
        assert len(test_ops) >= 1
        
        test_op = test_ops[-1]  # Get the most recent
        assert test_op['success'] is True
        assert test_op['duration_ms'] >= 10  # At least 10ms from sleep
        assert test_op['timed_out'] is False
    
    def test_performance_timer_with_exception(self):
        """Test performance timer when operation raises exception."""
        with pytest.raises(ValueError):
            with self.accessibility._performance_timer("failing_operation") as metrics:
                raise ValueError("Test error")
        
        # Check that failure was recorded
        stats = self.accessibility.get_performance_statistics()
        recent_ops = stats['recent_operations']
        failing_ops = [op for op in recent_ops if op['operation'] == 'failing_operation']
        assert len(failing_ops) >= 1
        
        failing_op = failing_ops[-1]
        assert failing_op['success'] is False
        assert failing_op['error_message'] == "Test error"
    
    def test_performance_timeout_detection(self):
        """Test timeout detection in performance monitoring."""
        with self.accessibility._performance_timer("slow_operation", timeout_ms=50) as metrics:
            time.sleep(0.1)  # Sleep longer than timeout
        
        # Check that timeout was detected
        stats = self.accessibility.get_performance_statistics()
        recent_ops = stats['recent_operations']
        slow_ops = [op for op in recent_ops if op['operation'] == 'slow_operation']
        assert len(slow_ops) >= 1
        
        slow_op = slow_ops[-1]
        assert slow_op['timed_out'] is True
        assert slow_op['duration_ms'] >= 100  # At least 100ms from sleep
    
    def test_performance_statistics_calculation(self):
        """Test performance statistics calculation."""
        # Clear existing stats
        self.accessibility.clear_performance_statistics()
        
        # Perform several operations with known durations
        durations = [10, 20, 30, 40, 50]  # ms
        for i, duration_ms in enumerate(durations):
            with self.accessibility._performance_timer(f"test_op_{i}") as metrics:
                time.sleep(duration_ms / 1000)  # Convert to seconds
        
        stats = self.accessibility.get_performance_statistics()
        
        # Check basic counts
        assert stats['total_operations'] == 5
        assert stats['successful_operations'] == 5
        assert stats['timed_out_operations'] == 0
        assert stats['success_rate_percent'] == 100.0
        assert stats['timeout_rate_percent'] == 0.0
        
        # Check duration statistics
        assert stats['fastest_operation_ms'] >= 10
        assert stats['slowest_operation_ms'] >= 50
        assert 20 <= stats['average_duration_ms'] <= 40  # Should be around 30ms
    
    def test_performance_warning_threshold(self):
        """Test performance warning when operations exceed thresholds."""
        # Configure a low warning threshold
        self.accessibility.performance_warning_threshold_ms = 50
        
        with patch.object(self.accessibility.logger, 'warning') as mock_warning:
            with self.accessibility._performance_timer("slow_operation", timeout_ms=100) as metrics:
                time.sleep(0.08)  # 80ms - should trigger warning
        
        # Check that warning was logged
        mock_warning.assert_called()
        warning_calls = [call for call in mock_warning.call_args_list 
                        if 'Performance warning' in str(call)]
        assert len(warning_calls) >= 1
    
    def test_performance_history_size_limit(self):
        """Test that performance history respects size limits."""
        # Set a small history limit
        self.accessibility.configure_performance_monitoring(max_history=3)
        
        # Perform more operations than the limit
        for i in range(5):
            with self.accessibility._performance_timer(f"test_op_{i}"):
                time.sleep(0.001)
        
        # Check that only the last 3 operations are kept
        assert len(self.accessibility.performance_metrics) <= 3
        
        # Check that the most recent operations are kept
        operation_names = [m.operation_name for m in self.accessibility.performance_metrics]
        assert 'test_op_4' in operation_names  # Most recent should be kept
        assert 'test_op_0' not in operation_names  # Oldest should be evicted
    
    def test_performance_monitoring_disable(self):
        """Test disabling performance monitoring."""
        # Disable monitoring
        self.accessibility.configure_performance_monitoring(enabled=False)
        
        with self.accessibility._performance_timer("disabled_test") as metrics:
            assert metrics is None  # Should return None when disabled
        
        # No metrics should be recorded
        stats = self.accessibility.get_performance_statistics()
        disabled_ops = [op for op in stats['recent_operations'] 
                       if op['operation'] == 'disabled_test']
        assert len(disabled_ops) == 0


class TestFuzzyMatchingPerformance:
    """Test fuzzy matching performance and timeout handling."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.error_handler = ErrorHandler()
        self.accessibility = AccessibilityModule()
        
        # Mock fuzzy matching availability
        self.accessibility.FUZZY_MATCHING_ENABLED = True
        
        # Configure short timeouts for testing
        self.accessibility.configure_performance_monitoring(
            fuzzy_matching_timeout_ms=100
        )
    
    @patch('modules.accessibility.FUZZY_MATCHING_AVAILABLE', True)
    @patch('modules.accessibility.fuzz')
    def test_fuzzy_matching_timeout_handling(self, mock_fuzz):
        """Test fuzzy matching timeout handling."""
        # Mock slow fuzzy matching
        def slow_partial_ratio(*args, **kwargs):
            time.sleep(0.2)  # 200ms - longer than 100ms timeout
            return 90
        
        mock_fuzz.partial_ratio = slow_partial_ratio
        
        with patch.object(self.accessibility.logger, 'warning') as mock_warning:
            match_found, confidence = self.accessibility.fuzzy_match_text(
                "test element", "test", timeout_ms=100
            )
        
        # Should timeout and return False
        assert match_found is False
        assert confidence == 0.0
        
        # Should log timeout warning
        mock_warning.assert_called()
        timeout_warnings = [call for call in mock_warning.call_args_list 
                           if 'timeout' in str(call).lower()]
        assert len(timeout_warnings) >= 1
    
    @patch('modules.accessibility.FUZZY_MATCHING_AVAILABLE', True)
    @patch('modules.accessibility.fuzz')
    def test_fuzzy_matching_performance_warning(self, mock_fuzz):
        """Test fuzzy matching performance warnings."""
        # Mock moderately slow fuzzy matching (80% of timeout)
        def slow_partial_ratio(*args, **kwargs):
            time.sleep(0.08)  # 80ms - 80% of 100ms timeout
            return 90
        
        mock_fuzz.partial_ratio = slow_partial_ratio
        
        with patch.object(self.accessibility.logger, 'warning') as mock_warning:
            match_found, confidence = self.accessibility.fuzzy_match_text(
                "test element", "test", timeout_ms=100
            )
        
        # Should succeed but warn about slow performance
        assert match_found is True
        assert confidence == 90.0
        
        # Should log performance warning
        mock_warning.assert_called()
        perf_warnings = [call for call in mock_warning.call_args_list 
                        if 'slow' in str(call).lower()]
        assert len(perf_warnings) >= 1
    
    @patch('modules.accessibility.FUZZY_MATCHING_AVAILABLE', False)
    def test_fuzzy_matching_fallback_when_unavailable(self):
        """Test fallback to exact matching when fuzzy matching is unavailable."""
        # Test exact match
        match_found, confidence = self.accessibility.fuzzy_match_text(
            "Sign In", "sign in"
        )
        assert match_found is True
        assert confidence == 100.0
        
        # Test no match
        match_found, confidence = self.accessibility.fuzzy_match_text(
            "Different Text", "sign in"
        )
        assert match_found is False
        assert confidence == 0.0


class TestAttributeCheckingPerformance:
    """Test attribute checking performance monitoring."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.error_handler = ErrorHandler()
        self.accessibility = AccessibilityModule()
        
        # Configure short timeout for testing
        self.accessibility.configure_performance_monitoring(
            attribute_check_timeout_ms=200
        )
    
    @patch('modules.accessibility.AXUIElementCopyAttributeValue')
    def test_attribute_checking_performance_monitoring(self, mock_ax_copy):
        """Test performance monitoring for attribute checking."""
        # Mock element and successful attribute access
        mock_element = Mock()
        mock_ax_copy.return_value = (0, "Test Button")
        
        # Mock fuzzy matching to be fast
        with patch.object(self.accessibility, 'fuzzy_match_text', return_value=(True, 85.0)):
            match_found, confidence, attribute = self.accessibility._check_element_text_match(
                mock_element, "test"
            )
        
        assert match_found is True
        assert confidence == 0.85  # Converted from percentage
        assert attribute in self.accessibility.ACCESSIBILITY_ATTRIBUTES
        
        # Check that performance was monitored
        stats = self.accessibility.get_performance_statistics()
        attr_ops = [op for op in stats['recent_operations'] 
                   if op['operation'] == 'attribute_text_matching']
        assert len(attr_ops) >= 1
    
    def test_attribute_checking_performance_timing(self):
        """Test that attribute checking performance timing works correctly."""
        # Test with a simple slow operation using the performance timer directly
        with self.accessibility._performance_timer("slow_attribute_test", timeout_ms=200) as metrics:
            time.sleep(0.1)  # 100ms delay
        
        # Check performance monitoring recorded the operation
        stats = self.accessibility.get_performance_statistics()
        slow_ops = [op for op in stats['recent_operations'] 
                   if op['operation'] == 'slow_attribute_test']
        assert len(slow_ops) >= 1
        
        slow_op = slow_ops[-1]
        assert slow_op['duration_ms'] >= 100  # Should be at least 100ms from sleep
        assert slow_op['success'] is True
        assert slow_op['timed_out'] is False  # Should not timeout with 200ms limit


class TestFastPathPerformanceReport:
    """Test comprehensive fast path performance reporting."""
    
    def test_fast_path_performance_report_creation(self):
        """Test creation and serialization of fast path performance reports."""
        report = FastPathPerformanceReport(
            total_duration_ms=1500.0,
            target_extraction_ms=50.0,
            element_search_ms=800.0,
            fuzzy_matching_ms=150.0,
            attribute_checking_ms=300.0,
            cache_operations_ms=200.0,
            success=True,
            fallback_triggered=False,
            timeout_warnings=[],
            performance_warnings=["Fuzzy matching slow: 150ms"]
        )
        
        report_dict = report.to_dict()
        
        # Check all fields are present
        assert report_dict['total_duration_ms'] == 1500.0
        assert report_dict['target_extraction_ms'] == 50.0
        assert report_dict['element_search_ms'] == 800.0
        assert report_dict['fuzzy_matching_ms'] == 150.0
        assert report_dict['attribute_checking_ms'] == 300.0
        assert report_dict['cache_operations_ms'] == 200.0
        assert report_dict['success'] is True
        assert report_dict['fallback_triggered'] is False
        assert report_dict['meets_performance_target'] is True  # < 2000ms
        assert len(report_dict['performance_warnings']) == 1
    
    def test_fast_path_performance_target_check(self):
        """Test performance target checking in reports."""
        # Test meeting performance target
        fast_report = FastPathPerformanceReport(
            total_duration_ms=1800.0,
            target_extraction_ms=100.0,
            element_search_ms=1000.0,
            fuzzy_matching_ms=200.0,
            attribute_checking_ms=300.0,
            cache_operations_ms=200.0,
            success=True,
            fallback_triggered=False,
            timeout_warnings=[],
            performance_warnings=[]
        )
        
        assert fast_report.to_dict()['meets_performance_target'] is True
        
        # Test exceeding performance target
        slow_report = FastPathPerformanceReport(
            total_duration_ms=2500.0,
            target_extraction_ms=100.0,
            element_search_ms=1500.0,
            fuzzy_matching_ms=400.0,
            attribute_checking_ms=300.0,
            cache_operations_ms=200.0,
            success=True,
            fallback_triggered=False,
            timeout_warnings=["Total execution exceeded 2000ms"],
            performance_warnings=["Element search slow", "Fuzzy matching slow"]
        )
        
        assert slow_report.to_dict()['meets_performance_target'] is False


class TestPerformanceConfiguration:
    """Test performance monitoring configuration."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.error_handler = ErrorHandler()
        self.accessibility = AccessibilityModule()
    
    def test_performance_configuration_update(self):
        """Test updating performance monitoring configuration."""
        # Test configuration update
        self.accessibility.configure_performance_monitoring(
            enabled=True,
            fast_path_timeout_ms=3000,
            fuzzy_matching_timeout_ms=300,
            attribute_check_timeout_ms=600,
            max_history=200
        )
        
        # Check that settings were updated
        assert self.accessibility.performance_monitoring_enabled is True
        assert self.accessibility.fast_path_timeout_ms == 3000
        assert self.accessibility.fuzzy_matching_timeout_ms == 300
        assert self.accessibility.attribute_check_timeout_ms == 600
        assert self.accessibility.max_performance_history == 200
    
    def test_performance_statistics_reset(self):
        """Test resetting performance statistics."""
        # Generate some performance data
        with self.accessibility._performance_timer("test_op"):
            time.sleep(0.01)
        
        # Verify data exists
        stats_before = self.accessibility.get_performance_statistics()
        assert stats_before['total_operations'] >= 1
        
        # Clear statistics
        self.accessibility.clear_performance_statistics()
        
        # Verify data was cleared
        stats_after = self.accessibility.get_performance_statistics()
        assert stats_after['total_operations'] == 0
        assert stats_after['successful_operations'] == 0
        assert len(stats_after['recent_operations']) == 0


if __name__ == "__main__":
    pytest.main([__file__])