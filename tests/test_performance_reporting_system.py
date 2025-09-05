# tests/test_performance_reporting_system.py
"""
Integration tests for Performance Reporting System.
"""

import pytest
import time
import json
from unittest.mock import Mock, patch

from modules.performance_reporting_system import (
    PerformanceReportingSystem,
    PerformanceImprovementDetector,
    PerformanceReport,
    FeedbackMessage
)
from modules.fast_path_performance_monitor import (
    FastPathPerformanceMonitor,
    FastPathMetric
)


class TestPerformanceImprovementDetector:
    """Test cases for PerformanceImprovementDetector."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.detector = PerformanceImprovementDetector()
    
    def test_initialization(self):
        """Test detector initialization."""
        assert len(self.detector.improvement_history) == 0
        assert len(self.detector.degradation_history) == 0
        assert self.detector.last_analysis_time > 0
    
    def test_analyze_no_previous_stats(self):
        """Test analysis with no previous statistics."""
        current_stats = {
            'success_rate_percent': 80.0,
            'avg_execution_time_seconds': 1.0
        }
        
        analysis = self.detector.analyze_performance_changes(current_stats)
        
        assert analysis['overall_trend'] == 'stable'
        assert len(analysis['improvements']) == 0
        assert len(analysis['degradations']) == 0
    
    def test_analyze_success_rate_improvement(self):
        """Test detection of success rate improvement."""
        previous_stats = {
            'success_rate_percent': 60.0,
            'avg_execution_time_seconds': 1.5,
            'fallback_rate_percent': 40.0
        }
        
        current_stats = {
            'success_rate_percent': 80.0,  # 33% improvement
            'avg_execution_time_seconds': 1.5,
            'fallback_rate_percent': 40.0
        }
        
        analysis = self.detector.analyze_performance_changes(current_stats, previous_stats)
        
        assert analysis['overall_trend'] == 'improving'
        assert len(analysis['improvements']) == 1
        assert analysis['improvements'][0]['metric'] == 'success_rate'
        assert analysis['improvements'][0]['improvement_percent'] > 30
    
    def test_analyze_execution_time_improvement(self):
        """Test detection of execution time improvement."""
        previous_stats = {
            'success_rate_percent': 70.0,
            'avg_execution_time_seconds': 2.0,
            'fallback_rate_percent': 30.0
        }
        
        current_stats = {
            'success_rate_percent': 70.0,
            'avg_execution_time_seconds': 1.0,  # 50% improvement (faster)
            'fallback_rate_percent': 30.0
        }
        
        analysis = self.detector.analyze_performance_changes(current_stats, previous_stats)
        
        assert analysis['overall_trend'] == 'improving'
        assert len(analysis['improvements']) == 1
        assert analysis['improvements'][0]['metric'] == 'execution_time'
        assert analysis['improvements'][0]['improvement_percent'] == 50.0
    
    def test_analyze_performance_degradation(self):
        """Test detection of performance degradation."""
        previous_stats = {
            'success_rate_percent': 80.0,
            'avg_execution_time_seconds': 1.0,
            'fallback_rate_percent': 20.0
        }
        
        current_stats = {
            'success_rate_percent': 50.0,  # 37.5% degradation
            'avg_execution_time_seconds': 2.5,  # 150% degradation (slower)
            'fallback_rate_percent': 50.0  # 150% degradation (more fallbacks)
        }
        
        analysis = self.detector.analyze_performance_changes(current_stats, previous_stats)
        
        assert analysis['overall_trend'] == 'degrading'
        assert len(analysis['degradations']) == 3  # All metrics degraded
        
        # Check specific degradations
        degradation_metrics = [d['metric'] for d in analysis['degradations']]
        assert 'success_rate' in degradation_metrics
        assert 'execution_time' in degradation_metrics
        assert 'fallback_rate' in degradation_metrics
    
    def test_analyze_stable_performance(self):
        """Test detection of stable performance."""
        previous_stats = {
            'success_rate_percent': 75.0,
            'avg_execution_time_seconds': 1.2,
            'fallback_rate_percent': 25.0
        }
        
        current_stats = {
            'success_rate_percent': 76.0,  # Small improvement, within stable range
            'avg_execution_time_seconds': 1.1,  # Small improvement, within stable range
            'fallback_rate_percent': 24.0  # Small improvement, within stable range
        }
        
        analysis = self.detector.analyze_performance_changes(current_stats, previous_stats)
        
        assert analysis['overall_trend'] == 'stable'
        assert len(analysis['stable_metrics']) >= 2  # Most metrics should be stable
    
    def test_confidence_calculation(self):
        """Test confidence calculation based on data quality."""
        # Low confidence with few executions
        current_stats = {'total_executions': 10}
        previous_stats = {'total_executions': 5}
        
        analysis = self.detector.analyze_performance_changes(current_stats, previous_stats)
        assert analysis['confidence'] < 0.5
        
        # High confidence with many executions
        current_stats = {'total_executions': 100}
        analysis = self.detector.analyze_performance_changes(current_stats, previous_stats)
        assert analysis['confidence'] >= 1.0


class TestPerformanceReportingSystem:
    """Test cases for PerformanceReportingSystem."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.monitor = FastPathPerformanceMonitor()
        self.reporting_system = PerformanceReportingSystem(monitor=self.monitor)
    
    def test_initialization(self):
        """Test reporting system initialization."""
        assert self.reporting_system.monitor == self.monitor
        assert len(self.reporting_system.reports_history) == 0
        assert len(self.reporting_system.feedback_history) == 0
        assert self.reporting_system.excellent_threshold == 90.0
    
    def test_generate_real_time_feedback_no_data(self):
        """Test feedback generation with no execution data."""
        feedback = self.reporting_system.generate_real_time_feedback()
        
        assert feedback.message_type == "info"
        assert feedback.title == "No Recent Activity"
        assert "No fast path executions" in feedback.message
    
    def test_generate_real_time_feedback_excellent_performance(self):
        """Test feedback generation for excellent performance."""
        # Add excellent performance metrics
        for i in range(10):
            metric = FastPathMetric(
                command=f"test {i}",
                execution_time=0.3,
                success=True,
                element_found=True,
                fallback_triggered=False
            )
            self.monitor.record_fast_path_execution(metric)
        
        feedback = self.reporting_system.generate_real_time_feedback()
        
        assert feedback.message_type == "success"
        assert feedback.title == "Excellent Performance"
        assert "excellently" in feedback.message.lower()
        assert feedback.details['performance_level'] == 'excellent'
        assert feedback.details['success_rate'] >= 90.0
    
    def test_generate_real_time_feedback_poor_performance(self):
        """Test feedback generation for poor performance."""
        # Add poor performance metrics
        for i in range(10):
            metric = FastPathMetric(
                command=f"test {i}",
                execution_time=3.0,
                success=False,
                element_found=False,
                fallback_triggered=True,
                error_message="Element not found"
            )
            self.monitor.record_fast_path_execution(metric)
        
        feedback = self.reporting_system.generate_real_time_feedback()
        
        assert feedback.message_type == "warning" or feedback.message_type == "error"
        assert feedback.action_required == True
        assert len(feedback.suggested_actions) > 0
        assert feedback.details['success_rate'] < 50.0
    
    def test_generate_real_time_feedback_critical_performance(self):
        """Test feedback generation for critical performance."""
        # Add critical performance metrics (very low success rate)
        for i in range(20):
            success = i < 2  # Only 10% success rate
            metric = FastPathMetric(
                command=f"test {i}",
                execution_time=4.0,
                success=success,
                element_found=success,
                fallback_triggered=not success
            )
            self.monitor.record_fast_path_execution(metric)
        
        feedback = self.reporting_system.generate_real_time_feedback()
        
        assert feedback.message_type == "error"
        assert feedback.title == "Critical Performance Issues"
        assert feedback.action_required == True
        assert "immediate action required" in feedback.message.lower()
        assert "diagnostics immediately" in ' '.join(feedback.suggested_actions).lower()
    
    def test_detect_performance_improvements(self):
        """Test performance improvement detection."""
        # Create initial poor performance
        for i in range(10):
            metric = FastPathMetric(
                command=f"test {i}",
                execution_time=2.0,
                success=False,
                fallback_triggered=True
            )
            self.monitor.record_fast_path_execution(metric)
        
        # Generate initial report
        initial_report = self.reporting_system.generate_performance_summary_report(time_period_hours=1.0)
        
        # Add improved performance
        for i in range(15):
            metric = FastPathMetric(
                command=f"test improved {i}",
                execution_time=0.5,
                success=True,
                fallback_triggered=False
            )
            self.monitor.record_fast_path_execution(metric)
        
        # Detect improvements
        improvements = self.reporting_system.detect_performance_improvements()
        
        assert improvements['has_improvements'] == True
        assert improvements['overall_trend'] == 'improving'
        assert len(improvements['improvements']) > 0
        assert len(improvements['recommendations']) > 0
    
    def test_generate_performance_summary_report(self):
        """Test comprehensive performance report generation."""
        # Add mixed performance data
        for i in range(20):
            success = i % 3 != 0  # 2/3 success rate
            metric = FastPathMetric(
                command=f"test {i}",
                app_name="TestApp" if i % 2 == 0 else "OtherApp",
                execution_time=1.0 + (i * 0.1),
                success=success,
                element_found=success,
                fallback_triggered=not success
            )
            self.monitor.record_fast_path_execution(metric)
        
        report = self.reporting_system.generate_performance_summary_report(time_period_hours=1.0)
        
        # Verify report structure
        assert report.report_id.startswith("perf_report_")
        assert report.time_period_hours == 1.0
        assert report.summary['total_executions'] == 20
        assert 0 <= report.health_score <= 100
        assert len(report.recommendations) > 0
        
        # Verify app performance tracking
        assert 'TestApp' in report.app_performance
        assert 'OtherApp' in report.app_performance
        
        # Verify trends
        assert 'overall_trend' in report.trends
        assert 'confidence' in report.trends
    
    def test_health_score_calculation(self):
        """Test health score calculation."""
        # Test excellent performance
        for i in range(10):
            metric = FastPathMetric(
                command=f"test {i}",
                execution_time=0.5,
                success=True,
                fallback_triggered=False
            )
            self.monitor.record_fast_path_execution(metric)
        
        stats = self.monitor.get_performance_statistics()
        health_score = self.reporting_system._calculate_health_score(stats)
        
        assert health_score >= 90.0  # Should be excellent
        
        # Test poor performance
        self.monitor = FastPathPerformanceMonitor()  # Reset
        self.reporting_system.monitor = self.monitor
        
        for i in range(10):
            metric = FastPathMetric(
                command=f"test {i}",
                execution_time=5.0,  # Very slow
                success=False,      # Always fails
                fallback_triggered=True
            )
            self.monitor.record_fast_path_execution(metric)
        
        stats = self.monitor.get_performance_statistics()
        health_score = self.reporting_system._calculate_health_score(stats)
        
        assert health_score <= 30.0  # Should be poor
    
    def test_export_performance_report_json(self):
        """Test JSON export of performance report."""
        # Generate a report
        for i in range(5):
            metric = FastPathMetric(
                command=f"test {i}",
                execution_time=1.0,
                success=True
            )
            self.monitor.record_fast_path_execution(metric)
        
        report = self.reporting_system.generate_performance_summary_report()
        json_export = self.reporting_system.export_performance_report(report, format='json')
        
        # Should be valid JSON
        data = json.loads(json_export)
        assert 'report_id' in data
        assert 'summary' in data
        assert 'recommendations' in data
    
    def test_export_performance_report_html(self):
        """Test HTML export of performance report."""
        # Generate a report
        for i in range(5):
            metric = FastPathMetric(
                command=f"test {i}",
                execution_time=1.0,
                success=True
            )
            self.monitor.record_fast_path_execution(metric)
        
        report = self.reporting_system.generate_performance_summary_report()
        html_export = self.reporting_system.export_performance_report(report, format='html')
        
        # Should contain HTML elements
        assert '<html>' in html_export
        assert '<title>' in html_export
        assert 'Fast Path Performance Report' in html_export
        assert 'Success Rate:' in html_export
    
    def test_export_performance_report_text(self):
        """Test text export of performance report."""
        # Generate a report
        for i in range(5):
            metric = FastPathMetric(
                command=f"test {i}",
                execution_time=1.0,
                success=True
            )
            self.monitor.record_fast_path_execution(metric)
        
        report = self.reporting_system.generate_performance_summary_report()
        text_export = self.reporting_system.export_performance_report(report, format='text')
        
        # Should contain expected text elements
        assert 'AURA Fast Path Performance Report' in text_export
        assert 'Summary:' in text_export
        assert 'Recommendations:' in text_export
        assert 'Success Rate:' in text_export
    
    def test_comprehensive_recommendations_generation(self):
        """Test comprehensive recommendation generation."""
        # Create scenario with various issues
        apps_and_performance = [
            ("GoodApp", True, 0.5),
            ("BadApp", False, 3.0),
            ("GoodApp", True, 0.6),
            ("BadApp", False, 2.8),
            ("GoodApp", True, 0.4),
            ("BadApp", False, 3.2),
        ]
        
        for app, success, exec_time in apps_and_performance:
            metric = FastPathMetric(
                command="test",
                app_name=app,
                execution_time=exec_time,
                success=success,
                fallback_triggered=not success
            )
            self.monitor.record_fast_path_execution(metric)
        
        report = self.reporting_system.generate_performance_summary_report()
        
        # Should have recommendations for problematic apps
        recommendations_text = ' '.join(report.recommendations).lower()
        assert 'badapp' in recommendations_text or 'problematic' in recommendations_text
        
        # Should have general performance recommendations
        assert len(report.recommendations) > 0
    
    def test_feedback_history_tracking(self):
        """Test feedback history tracking."""
        # Generate multiple feedback messages
        for i in range(5):
            # Add some metrics
            metric = FastPathMetric(
                command=f"test {i}",
                execution_time=1.0,
                success=i % 2 == 0
            )
            self.monitor.record_fast_path_execution(metric)
            
            # Generate feedback
            feedback = self.reporting_system.generate_real_time_feedback()
            self.reporting_system.feedback_history.append(feedback)
        
        # Get feedback history
        history = self.reporting_system.get_feedback_history(hours=24)
        
        assert len(history) == 5
        assert all('timestamp' in item for item in history)
        assert all('message_type' in item for item in history)
    
    def test_should_generate_report_timing(self):
        """Test report generation timing logic."""
        # Initially should not need to generate report (just initialized)
        assert not self.reporting_system.should_generate_report()
        
        # Simulate time passing
        self.reporting_system.last_report_time = time.time() - 400  # 400 seconds ago
        assert self.reporting_system.should_generate_report()
    
    def test_error_handling_in_feedback_generation(self):
        """Test error handling in feedback generation."""
        # Mock the monitor to raise an exception
        with patch.object(self.reporting_system.monitor, 'get_performance_statistics', 
                         side_effect=Exception("Test error")):
            feedback = self.reporting_system.generate_real_time_feedback()
            
            assert feedback.message_type == "error"
            assert "Feedback Generation Error" in feedback.title
            assert "Test error" in feedback.message
    
    def test_error_handling_in_report_generation(self):
        """Test error handling in report generation."""
        # Mock the monitor to raise an exception
        with patch.object(self.reporting_system.monitor, 'get_performance_statistics', 
                         side_effect=Exception("Test error")):
            report = self.reporting_system.generate_performance_summary_report()
            
            assert report.report_id.startswith("error_report_")
            assert 'error' in report.summary
            assert any("Report generation failed" in rec for rec in report.recommendations)


if __name__ == '__main__':
    pytest.main([__file__])