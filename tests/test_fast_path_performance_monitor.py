# tests/test_fast_path_performance_monitor.py
"""
Unit tests for Fast Path Performance Monitor.
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch

from modules.fast_path_performance_monitor import (
    FastPathPerformanceMonitor,
    FastPathMetric,
    PerformanceAlert,
    RollingAverageCalculator
)


class TestRollingAverageCalculator:
    """Test cases for RollingAverageCalculator."""
    
    def test_initialization(self):
        """Test calculator initialization."""
        calc = RollingAverageCalculator(window_size=10)
        assert calc.window_size == 10
        assert len(calc.values) == 0
        assert calc.get_average() == 0.0
    
    def test_add_value_and_average(self):
        """Test adding values and calculating average."""
        calc = RollingAverageCalculator(window_size=5)
        
        # Add values
        calc.add_value(10.0)
        calc.add_value(20.0)
        calc.add_value(30.0)
        
        # Check average
        expected_avg = (10.0 + 20.0 + 30.0) / 3
        assert calc.get_average() == expected_avg
    
    def test_window_size_limit(self):
        """Test that window size is respected."""
        calc = RollingAverageCalculator(window_size=3)
        
        # Add more values than window size
        for i in range(5):
            calc.add_value(float(i))
        
        # Should only keep last 3 values
        assert len(calc.values) == 3
        assert list(calc.values) == [2.0, 3.0, 4.0]
        assert calc.get_average() == 3.0
    
    def test_trend_detection(self):
        """Test trend detection functionality."""
        calc = RollingAverageCalculator(window_size=20)
        
        # Not enough data
        for i in range(5):
            calc.add_value(float(i))
        assert calc.get_trend() == "insufficient_data"
        
        # Stable trend - add exactly the same values
        calc = RollingAverageCalculator(window_size=20)
        for i in range(20):
            calc.add_value(10.0)
        assert calc.get_trend() == "stable"
        
        # Improving trend - significant improvement
        calc = RollingAverageCalculator(window_size=20)
        for i in range(14):
            calc.add_value(5.0)  # Older values (70% of data)
        for i in range(6):
            calc.add_value(20.0)  # Recent values (30% of data) - 4x higher
        assert calc.get_trend() == "improving"
        
        # Degrading trend - significant degradation
        calc = RollingAverageCalculator(window_size=20)
        for i in range(14):
            calc.add_value(20.0)  # Older values (70% of data)
        for i in range(6):
            calc.add_value(5.0)   # Recent values (30% of data) - 4x lower
        assert calc.get_trend() == "degrading"
    
    def test_thread_safety(self):
        """Test thread safety of calculator."""
        calc = RollingAverageCalculator(window_size=100)
        
        def add_values():
            for i in range(50):
                calc.add_value(float(i))
        
        # Run multiple threads
        threads = [threading.Thread(target=add_values) for _ in range(4)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        # Should have 100 values (window size limit)
        assert len(calc.values) == 100
        assert calc.get_average() > 0


class TestFastPathPerformanceMonitor:
    """Test cases for FastPathPerformanceMonitor."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.alert_callback = Mock()
        self.monitor = FastPathPerformanceMonitor(
            max_metrics=100,
            alert_callback=self.alert_callback
        )
    
    def test_initialization(self):
        """Test monitor initialization."""
        assert self.monitor.max_metrics == 100
        assert self.monitor.alert_callback == self.alert_callback
        assert len(self.monitor.metrics) == 0
        assert self.monitor.success_rate_warning_threshold == 70.0
        assert self.monitor.success_rate_critical_threshold == 50.0
    
    def test_record_successful_execution(self):
        """Test recording successful fast path execution."""
        metric = FastPathMetric(
            command="click on button",
            app_name="TestApp",
            execution_time=0.5,
            element_detection_time=0.3,
            matching_time=0.1,
            success=True,
            element_found=True,
            fallback_triggered=False
        )
        
        self.monitor.record_fast_path_execution(metric)
        
        # Check metric was stored
        assert len(self.monitor.metrics) == 1
        assert self.monitor.metrics[0] == metric
        
        # Check rolling averages updated
        assert self.monitor.success_rate_calculator.get_average() == 100.0
        assert self.monitor.execution_time_calculator.get_average() == 0.5
    
    def test_record_failed_execution(self):
        """Test recording failed fast path execution."""
        metric = FastPathMetric(
            command="click on button",
            app_name="TestApp",
            execution_time=2.0,
            element_detection_time=1.5,
            matching_time=0.3,
            success=False,
            element_found=False,
            fallback_triggered=True,
            error_message="Element not found"
        )
        
        self.monitor.record_fast_path_execution(metric)
        
        # Check metric was stored
        assert len(self.monitor.metrics) == 1
        
        # Check rolling averages updated
        assert self.monitor.success_rate_calculator.get_average() == 0.0
        assert self.monitor.execution_time_calculator.get_average() == 2.0
    
    def test_application_specific_tracking(self):
        """Test application-specific performance tracking."""
        # Record metrics for different apps
        apps = ["App1", "App2", "App1", "App1"]
        successes = [True, False, True, False]
        
        for app, success in zip(apps, successes):
            metric = FastPathMetric(
                command="test command",
                app_name=app,
                execution_time=1.0,
                success=success,
                fallback_triggered=not success
            )
            self.monitor.record_fast_path_execution(metric)
        
        # Check App1 stats (3 attempts, 2 successes)
        app1_stats = self.monitor.app_performance["App1"]
        assert app1_stats['total_attempts'] == 3
        assert app1_stats['successful_attempts'] == 2
        assert app1_stats['consecutive_failures'] == 1  # Last attempt failed
        
        # Check App2 stats (1 attempt, 0 successes)
        app2_stats = self.monitor.app_performance["App2"]
        assert app2_stats['total_attempts'] == 1
        assert app2_stats['successful_attempts'] == 0
        assert app2_stats['consecutive_failures'] == 1
    
    def test_success_rate_calculation(self):
        """Test success rate calculation."""
        # Record mixed results
        results = [True, True, False, True, False, False, True, True]
        
        for success in results:
            metric = FastPathMetric(
                command="test",
                execution_time=1.0,
                success=success,
                fallback_triggered=not success
            )
            self.monitor.record_fast_path_execution(metric)
        
        # Expected success rate: 5/8 = 62.5%
        success_rate = self.monitor.get_current_success_rate(time_window_minutes=60)
        assert abs(success_rate - 62.5) < 0.1
    
    def test_performance_statistics(self):
        """Test comprehensive performance statistics."""
        # Record some test metrics
        for i in range(10):
            success = i % 3 != 0  # 2/3 success rate
            metric = FastPathMetric(
                command=f"test command {i}",
                app_name="TestApp",
                execution_time=1.0 + (i * 0.1),
                element_detection_time=0.5 + (i * 0.05),
                matching_time=0.2 + (i * 0.02),
                success=success,
                element_found=success,
                fallback_triggered=not success
            )
            self.monitor.record_fast_path_execution(metric)
        
        stats = self.monitor.get_performance_statistics(time_window_minutes=60)
        
        # Check basic statistics
        assert stats['total_executions'] == 10
        assert stats['successful_executions'] == 7  # 7 out of 10 succeeded
        assert abs(stats['success_rate_percent'] - 70.0) < 0.1
        assert stats['fallback_rate_percent'] == 30.0
        
        # Check timing statistics
        assert stats['avg_execution_time_seconds'] > 1.0
        assert stats['avg_element_detection_time_seconds'] > 0.5
        assert stats['avg_matching_time_seconds'] > 0.2
        
        # Check app performance
        assert 'TestApp' in stats['app_performance']
        app_stats = stats['app_performance']['TestApp']
        assert app_stats['total_attempts'] == 10
        assert app_stats['successful_attempts'] == 7
    
    def test_critical_success_rate_alert(self):
        """Test critical success rate alert triggering."""
        # Record mostly failed executions to trigger critical alert
        for i in range(20):
            success = i < 5  # Only first 5 succeed (25% success rate)
            metric = FastPathMetric(
                command="test",
                execution_time=1.0,
                success=success,
                fallback_triggered=not success
            )
            self.monitor.record_fast_path_execution(metric)
        
        # Should have triggered critical alert
        assert self.alert_callback.called
        
        # Check alert details
        alert_calls = self.alert_callback.call_args_list
        critical_alerts = [
            call[0][0] for call in alert_calls 
            if call[0][0].severity == "critical"
        ]
        assert len(critical_alerts) > 0
        
        critical_alert = critical_alerts[0]
        assert critical_alert.alert_type == "success_rate_critical"
        assert "critically low" in critical_alert.message.lower()
    
    def test_execution_time_alert(self):
        """Test execution time alert triggering."""
        # Record slow executions to trigger alert
        for i in range(10):
            metric = FastPathMetric(
                command="test",
                execution_time=6.0,  # Above critical threshold
                success=True
            )
            self.monitor.record_fast_path_execution(metric)
        
        # Should have triggered execution time alert
        assert self.alert_callback.called
        
        # Check for execution time alert
        alert_calls = self.alert_callback.call_args_list
        time_alerts = [
            call[0][0] for call in alert_calls 
            if "execution_time" in call[0][0].alert_type
        ]
        assert len(time_alerts) > 0
    
    def test_consecutive_failures_alert(self):
        """Test consecutive failures alert for specific app."""
        # Record consecutive failures for same app
        for i in range(6):  # Above threshold of 5
            metric = FastPathMetric(
                command="test",
                app_name="ProblematicApp",
                execution_time=1.0,
                success=False,
                fallback_triggered=True
            )
            self.monitor.record_fast_path_execution(metric)
        
        # Should have triggered consecutive failures alert
        assert self.alert_callback.called
        
        # Check for app-specific alert
        alert_calls = self.alert_callback.call_args_list
        app_alerts = [
            call[0][0] for call in alert_calls 
            if call[0][0].alert_type == "app_consecutive_failures"
        ]
        assert len(app_alerts) > 0
        
        app_alert = app_alerts[0]
        assert "ProblematicApp" in app_alert.message
        assert app_alert.metadata['app_name'] == "ProblematicApp"
    
    def test_alert_cooldown(self):
        """Test alert cooldown mechanism."""
        # Trigger same alert type multiple times quickly
        for i in range(5):
            metric = FastPathMetric(
                command="test",
                execution_time=1.0,
                success=False,
                fallback_triggered=True
            )
            self.monitor.record_fast_path_execution(metric)
        
        # Should only trigger alert once due to cooldown
        initial_call_count = self.alert_callback.call_count
        
        # Add more failures immediately
        for i in range(5):
            metric = FastPathMetric(
                command="test",
                execution_time=1.0,
                success=False,
                fallback_triggered=True
            )
            self.monitor.record_fast_path_execution(metric)
        
        # Call count should not increase significantly due to cooldown
        assert self.alert_callback.call_count <= initial_call_count + 1
    
    def test_should_suggest_diagnostics(self):
        """Test diagnostic suggestion logic."""
        # High success rate - should not suggest diagnostics
        for i in range(10):
            metric = FastPathMetric(
                command="test",
                execution_time=1.0,
                success=True
            )
            self.monitor.record_fast_path_execution(metric)
        
        assert not self.monitor.should_suggest_diagnostics()
        
        # Low success rate - should suggest diagnostics
        for i in range(20):
            metric = FastPathMetric(
                command="test",
                execution_time=1.0,
                success=False,
                fallback_triggered=True
            )
            self.monitor.record_fast_path_execution(metric)
        
        assert self.monitor.should_suggest_diagnostics()
    
    def test_performance_feedback_message(self):
        """Test performance feedback message generation."""
        # Excellent performance
        for i in range(10):
            metric = FastPathMetric(
                command="test",
                execution_time=0.5,
                success=True
            )
            self.monitor.record_fast_path_execution(metric)
        
        message = self.monitor.get_performance_feedback_message()
        assert "excellently" in message.lower()
        assert "✅" in message
        
        # Poor performance
        self.monitor = FastPathPerformanceMonitor()  # Reset
        for i in range(10):
            metric = FastPathMetric(
                command="test",
                execution_time=2.0,
                success=False,
                fallback_triggered=True
            )
            self.monitor.record_fast_path_execution(metric)
        
        message = self.monitor.get_performance_feedback_message()
        assert "critical" in message.lower()
        assert "❌" in message
        assert "diagnostics recommended" in message.lower()
    
    def test_export_performance_data_json(self):
        """Test JSON export of performance data."""
        # Add some test data
        for i in range(5):
            metric = FastPathMetric(
                command=f"test {i}",
                execution_time=1.0,
                success=i % 2 == 0
            )
            self.monitor.record_fast_path_execution(metric)
        
        json_data = self.monitor.export_performance_data(format='json')
        
        # Should be valid JSON
        import json
        data = json.loads(json_data)
        
        assert 'success_rate_percent' in data
        assert 'total_executions' in data
        assert data['total_executions'] == 5
    
    def test_export_performance_data_csv(self):
        """Test CSV export of performance data."""
        # Add some test data
        for i in range(3):
            metric = FastPathMetric(
                command=f"test {i}",
                execution_time=1.0,
                success=True
            )
            self.monitor.record_fast_path_execution(metric)
        
        csv_data = self.monitor.export_performance_data(format='csv')
        
        # Should contain CSV headers and data
        lines = csv_data.strip().split('\n')
        assert len(lines) >= 2  # Header + at least one data line
        assert lines[0] == "metric,value,timestamp"
        assert "success_rate_percent" in csv_data
    
    def test_performance_improvement_detection(self):
        """Test detection of performance improvements."""
        # Start with poor performance
        for i in range(10):
            metric = FastPathMetric(
                command="test",
                execution_time=3.0,
                success=False,
                fallback_triggered=True
            )
            self.monitor.record_fast_path_execution(metric)
        
        # Then improve performance significantly
        for i in range(20):
            metric = FastPathMetric(
                command="test",
                execution_time=0.5,
                success=True
            )
            self.monitor.record_fast_path_execution(metric)
        
        # Should detect improvement trend
        success_trend = self.monitor.success_rate_calculator.get_trend()
        time_trend = self.monitor.execution_time_calculator.get_trend()
        
        assert success_trend == "improving"
        assert time_trend == "improving"
    
    def test_thread_safety(self):
        """Test thread safety of performance monitor."""
        def record_metrics():
            for i in range(50):
                metric = FastPathMetric(
                    command=f"test {i}",
                    execution_time=1.0,
                    success=i % 2 == 0
                )
                self.monitor.record_fast_path_execution(metric)
        
        # Run multiple threads
        threads = [threading.Thread(target=record_metrics) for _ in range(4)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        # Should have recorded all metrics safely
        assert len(self.monitor.metrics) == min(200, self.monitor.max_metrics)
        
        # Statistics should be consistent
        stats = self.monitor.get_performance_statistics()
        assert stats['total_executions'] > 0
        assert 0 <= stats['success_rate_percent'] <= 100


if __name__ == '__main__':
    pytest.main([__file__])