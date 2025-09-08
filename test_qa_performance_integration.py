#!/usr/bin/env python3
"""
Integration test for QuestionAnsweringHandler performance monitoring.

This script tests the integration of the performance monitoring system
with the existing AURA performance infrastructure.
"""

import sys
import time
import logging
from unittest.mock import Mock, patch

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_integration_with_existing_performance_system():
    """Test integration with existing performance monitoring system."""
    print("🔗 Testing integration with existing performance system...")
    
    try:
        from handlers.question_answering_handler import QuestionAnsweringHandler
        from modules.performance import performance_monitor, PerformanceMetrics
        
        # Create mock orchestrator
        mock_orchestrator = Mock()
        
        # Create handler
        handler = QuestionAnsweringHandler(mock_orchestrator)
        
        # Test that handler can access global performance monitor
        assert performance_monitor is not None, "Global performance monitor should be available"
        
        # Test that handler's performance monitoring works alongside global system
        initial_metrics_count = len(performance_monitor.metrics)
        
        # Simulate some performance metrics
        test_metric = PerformanceMetrics(
            operation="question_answering_test",
            duration=2.5,
            success=True
        )
        performance_monitor.record_metric(test_metric)
        
        # Verify metric was recorded
        assert len(performance_monitor.metrics) == initial_metrics_count + 1
        
        print("✅ Integration with existing performance system: PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Integration with existing performance system: FAILED - {e}")
        return False

def test_health_check_integration():
    """Test health check integration with module availability."""
    print("🏥 Testing health check integration...")
    
    try:
        from handlers.question_answering_handler import QuestionAnsweringHandler
        
        # Create mock orchestrator
        mock_orchestrator = Mock()
        
        # Create handler
        handler = QuestionAnsweringHandler(mock_orchestrator)
        
        # Force a health check
        handler._perform_health_check()
        
        # Get health status
        health_status = handler._get_health_status()
        
        # Verify health check results
        print(f"Browser handler available: {health_status['browser_handler_available']}")
        print(f"PDF handler available: {health_status['pdf_handler_available']}")
        print(f"Reasoning module available: {health_status['reasoning_module_available']}")
        print(f"Overall health: {health_status['overall_health']}")
        
        # All should be available in test environment
        assert health_status['browser_handler_available'] == True, "Browser handler should be available"
        assert health_status['pdf_handler_available'] == True, "PDF handler should be available"
        assert health_status['reasoning_module_available'] == True, "Reasoning module should be available"
        assert health_status['overall_health'] == "excellent", "Overall health should be excellent"
        
        print("✅ Health check integration: PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Health check integration: FAILED - {e}")
        return False

def test_performance_monitoring_with_real_workflow():
    """Test performance monitoring with a simulated real workflow."""
    print("🔄 Testing performance monitoring with real workflow simulation...")
    
    try:
        from handlers.question_answering_handler import QuestionAnsweringHandler
        from modules.application_detector import ApplicationInfo, ApplicationType, BrowserType
        
        # Create mock orchestrator
        mock_orchestrator = Mock()
        
        # Create handler
        handler = QuestionAnsweringHandler(mock_orchestrator)
        
        # Simulate a successful fast path execution
        mock_app_info = Mock()
        mock_app_info.name = "Chrome"
        mock_app_info.app_type = ApplicationType.WEB_BROWSER
        mock_app_info.browser_type = BrowserType.CHROME
        
        # Log fast path performance
        handler._log_fast_path_performance(
            app_info=mock_app_info,
            extraction_method="browser",
            extraction_time=0.8,
            summarization_time=1.2,
            total_time=2.0,
            content_size=1500,
            summary_size=300
        )
        
        # Simulate a fallback execution
        handler._log_fallback_performance(
            fallback_reason="extraction_failed",
            fallback_time=8.5,
            success=True,
            app_name="Safari"
        )
        
        # Get performance statistics
        stats = handler.get_performance_statistics(time_window_minutes=1)
        
        # Verify statistics
        assert stats['total_requests'] == 2, f"Expected 2 requests, got {stats['total_requests']}"
        assert stats['fast_path_requests'] == 1, f"Expected 1 fast path request, got {stats['fast_path_requests']}"
        assert stats['fallback_rate'] == 50.0, f"Expected 50% fallback rate, got {stats['fallback_rate']}"
        
        # Check application performance breakdown
        assert 'Chrome' in stats['app_performance'], "Chrome should be in app performance stats"
        assert 'Safari' in stats['app_performance'], "Safari should be in app performance stats"
        
        # Get recommendations
        recommendations = handler.get_performance_recommendations()
        assert len(recommendations) > 0, "Should have performance recommendations"
        
        print("✅ Performance monitoring with real workflow simulation: PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Performance monitoring with real workflow simulation: FAILED - {e}")
        return False

def test_performance_trends_analysis():
    """Test performance trends analysis functionality."""
    print("📈 Testing performance trends analysis...")
    
    try:
        from handlers.question_answering_handler import QuestionAnsweringHandler, QuestionAnsweringMetric
        
        # Create mock orchestrator
        mock_orchestrator = Mock()
        
        # Create handler
        handler = QuestionAnsweringHandler(mock_orchestrator)
        
        # Create metrics showing improving performance
        improving_metrics = []
        for i in range(20):
            # Simulate improving performance over time
            execution_time = 5.0 - (i * 0.1)  # Getting faster
            success = i > 5  # More successes over time
            
            metric = QuestionAnsweringMetric(
                timestamp=time.time() - (20 - i) * 60,  # Spread over time
                total_execution_time=execution_time,
                success=success,
                fast_path_used=True
            )
            improving_metrics.append(metric)
        
        # Add metrics to handler
        with handler._metrics_lock:
            handler._performance_metrics.extend(improving_metrics)
        
        # Analyze trends
        trends = handler._analyze_performance_trends(improving_metrics)
        
        # Verify trend analysis
        assert 'trend' in trends, "Trends should include trend direction"
        assert 'confidence' in trends, "Trends should include confidence level"
        assert trends['trend'] in ['improving', 'degrading', 'stable'], f"Invalid trend: {trends['trend']}"
        
        print(f"Detected trend: {trends['trend']} (confidence: {trends['confidence']:.2f})")
        
        print("✅ Performance trends analysis: PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Performance trends analysis: FAILED - {e}")
        return False

def test_fallback_reason_categorization():
    """Test fallback reason categorization."""
    print("🏷️ Testing fallback reason categorization...")
    
    try:
        from handlers.question_answering_handler import QuestionAnsweringHandler
        
        # Create mock orchestrator
        mock_orchestrator = Mock()
        
        # Create handler
        handler = QuestionAnsweringHandler(mock_orchestrator)
        
        # Test different fallback reason categories
        test_cases = [
            ("application_detection_failed", "detection_failure"),
            ("unsupported_application", "unsupported_app"),
            ("browser_extraction_failed", "extraction_failure"),
            ("pdf_extraction_timeout", "timeout"),
            ("content_validation_failed", "content_validation"),
            ("unknown_error", "other")
        ]
        
        for reason, expected_category in test_cases:
            category = handler._categorize_fallback_reason(reason)
            assert category == expected_category, f"Expected {expected_category} for {reason}, got {category}"
        
        print("✅ Fallback reason categorization: PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Fallback reason categorization: FAILED - {e}")
        return False

def main():
    """Run all integration tests."""
    print("🚀 Starting QuestionAnsweringHandler Performance Monitoring Integration Tests")
    print("=" * 80)
    
    tests = [
        test_integration_with_existing_performance_system,
        test_health_check_integration,
        test_performance_monitoring_with_real_workflow,
        test_performance_trends_analysis,
        test_fallback_reason_categorization
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            failed += 1
        print()
    
    print("=" * 80)
    print(f"📊 Integration Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All integration tests passed!")
        print("\n📋 Performance Monitoring Features Implemented:")
        print("  ✅ Performance metrics collection for fast path success rates and timing")
        print("  ✅ Detailed logging for extraction methods, content sizes, and fallback reasons")
        print("  ✅ Health check validation for browser and PDF handler availability")
        print("  ✅ Monitoring for overall system performance impact")
        print("  ✅ Performance trends analysis and recommendations")
        print("  ✅ Integration with existing AURA performance infrastructure")
        return True
    else:
        print(f"⚠️  {failed} integration test(s) failed. Please review the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)