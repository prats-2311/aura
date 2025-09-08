#!/usr/bin/env python3
"""
Test script for QuestionAnsweringHandler performance monitoring functionality.

This script tests the performance monitoring and logging capabilities
implemented for task 11 of the content comprehension fast path feature.
"""

import sys
import time
import logging
from unittest.mock import Mock, MagicMock

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_performance_monitoring_initialization():
    """Test that performance monitoring is properly initialized."""
    print("🔧 Testing performance monitoring initialization...")
    
    try:
        from handlers.question_answering_handler import QuestionAnsweringHandler, QuestionAnsweringMetric
        
        # Create mock orchestrator
        mock_orchestrator = Mock()
        
        # Create handler
        handler = QuestionAnsweringHandler(mock_orchestrator)
        
        # Check that performance monitoring attributes are initialized
        assert hasattr(handler, '_performance_metrics'), "Performance metrics storage not initialized"
        assert hasattr(handler, '_metrics_lock'), "Metrics lock not initialized"
        assert hasattr(handler, '_app_performance_stats'), "App performance stats not initialized"
        assert hasattr(handler, '_last_health_check'), "Health check timestamp not initialized"
        assert hasattr(handler, '_browser_handler_available'), "Browser handler availability not initialized"
        assert hasattr(handler, '_pdf_handler_available'), "PDF handler availability not initialized"
        assert hasattr(handler, '_reasoning_module_available'), "Reasoning module availability not initialized"
        
        print("✅ Performance monitoring initialization: PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Performance monitoring initialization: FAILED - {e}")
        return False

def test_performance_metrics_data_structure():
    """Test the QuestionAnsweringMetric data structure."""
    print("📊 Testing performance metrics data structure...")
    
    try:
        from handlers.question_answering_handler import QuestionAnsweringMetric
        
        # Create a test metric
        metric = QuestionAnsweringMetric(
            command="what's on my screen",
            app_name="Chrome",
            app_type="browser",
            extraction_method="browser",
            total_execution_time=2.5,
            extraction_time=1.0,
            summarization_time=1.5,
            content_size=1000,
            summary_size=200,
            success=True,
            fast_path_used=True
        )
        
        # Verify all fields are accessible
        assert metric.command == "what's on my screen"
        assert metric.app_name == "Chrome"
        assert metric.total_execution_time == 2.5
        assert metric.success == True
        assert metric.fast_path_used == True
        assert isinstance(metric.metadata, dict)
        
        print("✅ Performance metrics data structure: PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Performance metrics data structure: FAILED - {e}")
        return False

def test_health_check_functionality():
    """Test health check functionality."""
    print("🏥 Testing health check functionality...")
    
    try:
        from handlers.question_answering_handler import QuestionAnsweringHandler
        
        # Create mock orchestrator
        mock_orchestrator = Mock()
        
        # Create handler
        handler = QuestionAnsweringHandler(mock_orchestrator)
        
        # Test health check methods
        health_status = handler._get_health_status()
        
        # Verify health status structure
        assert isinstance(health_status, dict), "Health status should be a dictionary"
        assert 'browser_handler_available' in health_status
        assert 'pdf_handler_available' in health_status
        assert 'reasoning_module_available' in health_status
        assert 'overall_health' in health_status
        assert 'last_health_check' in health_status
        
        # Test overall health calculation
        overall_health = handler._calculate_overall_health()
        assert overall_health in ['excellent', 'good', 'degraded', 'critical']
        
        print("✅ Health check functionality: PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Health check functionality: FAILED - {e}")
        return False

def test_performance_statistics():
    """Test performance statistics collection and analysis."""
    print("📈 Testing performance statistics...")
    
    try:
        from handlers.question_answering_handler import QuestionAnsweringHandler, QuestionAnsweringMetric
        
        # Create mock orchestrator
        mock_orchestrator = Mock()
        
        # Create handler
        handler = QuestionAnsweringHandler(mock_orchestrator)
        
        # Add some test metrics
        test_metrics = [
            QuestionAnsweringMetric(
                command="test command 1",
                app_name="Chrome",
                extraction_method="browser",
                total_execution_time=2.0,
                success=True,
                fast_path_used=True
            ),
            QuestionAnsweringMetric(
                command="test command 2",
                app_name="Safari",
                extraction_method="browser",
                total_execution_time=3.5,
                success=True,
                fast_path_used=True
            ),
            QuestionAnsweringMetric(
                command="test command 3",
                app_name="Unknown",
                extraction_method="vision_fallback",
                total_execution_time=12.0,
                success=True,
                fast_path_used=False,
                fallback_reason="unsupported_application"
            )
        ]
        
        # Add metrics to handler
        with handler._metrics_lock:
            handler._performance_metrics.extend(test_metrics)
        
        # Get performance statistics
        stats = handler.get_performance_statistics(time_window_minutes=60)
        
        # Verify statistics structure
        assert isinstance(stats, dict), "Statistics should be a dictionary"
        assert 'total_requests' in stats
        assert 'fast_path_success_rate' in stats
        assert 'avg_response_time' in stats
        assert 'target_compliance_rate' in stats
        assert 'fallback_rate' in stats
        assert 'health_status' in stats
        
        # Verify calculated values
        assert stats['total_requests'] == 3
        assert stats['fast_path_requests'] == 2
        assert stats['fallback_rate'] > 0  # Should have fallback requests
        
        print("✅ Performance statistics: PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Performance statistics: FAILED - {e}")
        return False

def test_performance_logging():
    """Test performance logging functionality."""
    print("📝 Testing performance logging...")
    
    try:
        from handlers.question_answering_handler import QuestionAnsweringHandler
        from modules.application_detector import ApplicationInfo, ApplicationType
        
        # Create mock orchestrator
        mock_orchestrator = Mock()
        
        # Create handler
        handler = QuestionAnsweringHandler(mock_orchestrator)
        
        # Create mock application info
        mock_app_info = Mock()
        mock_app_info.name = "Chrome"
        mock_app_info.app_type = ApplicationType.WEB_BROWSER
        mock_app_info.browser_type = None
        
        # Test fast path performance logging
        handler._log_fast_path_performance(
            app_info=mock_app_info,
            extraction_method="browser",
            extraction_time=1.0,
            summarization_time=1.5,
            total_time=2.5,
            content_size=1000,
            summary_size=200
        )
        
        # Test fallback performance logging
        handler._log_fallback_performance(
            fallback_reason="unsupported_application",
            fallback_time=10.0,
            success=True,
            app_name="Unknown App"
        )
        
        # Verify metrics were stored
        with handler._metrics_lock:
            assert len(handler._performance_metrics) == 2, "Should have 2 metrics stored"
            
            # Check fast path metric
            fast_path_metric = handler._performance_metrics[0]
            assert fast_path_metric.app_name == "Chrome"
            assert fast_path_metric.fast_path_used == True
            assert fast_path_metric.success == True
            
            # Check fallback metric
            fallback_metric = handler._performance_metrics[1]
            assert fallback_metric.app_name == "Unknown App"
            assert fallback_metric.fast_path_used == False
            assert fallback_metric.fallback_reason == "unsupported_application"
        
        print("✅ Performance logging: PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Performance logging: FAILED - {e}")
        return False

def test_performance_recommendations():
    """Test performance recommendations functionality."""
    print("💡 Testing performance recommendations...")
    
    try:
        from handlers.question_answering_handler import QuestionAnsweringHandler
        
        # Create mock orchestrator
        mock_orchestrator = Mock()
        
        # Create handler
        handler = QuestionAnsweringHandler(mock_orchestrator)
        
        # Get recommendations (should work even with no data)
        recommendations = handler.get_performance_recommendations()
        
        # Verify recommendations structure
        assert isinstance(recommendations, list), "Recommendations should be a list"
        assert len(recommendations) > 0, "Should have at least one recommendation"
        assert all(isinstance(rec, str) for rec in recommendations), "All recommendations should be strings"
        
        print("✅ Performance recommendations: PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Performance recommendations: FAILED - {e}")
        return False

def test_system_performance_impact_logging():
    """Test system performance impact logging."""
    print("🎯 Testing system performance impact logging...")
    
    try:
        from handlers.question_answering_handler import QuestionAnsweringHandler
        
        # Create mock orchestrator
        mock_orchestrator = Mock()
        
        # Create handler
        handler = QuestionAnsweringHandler(mock_orchestrator)
        
        # Test system performance impact logging (should not crash)
        handler.log_system_performance_impact()
        
        print("✅ System performance impact logging: PASSED")
        return True
        
    except Exception as e:
        print(f"❌ System performance impact logging: FAILED - {e}")
        return False

def main():
    """Run all performance monitoring tests."""
    print("🚀 Starting QuestionAnsweringHandler Performance Monitoring Tests")
    print("=" * 70)
    
    tests = [
        test_performance_monitoring_initialization,
        test_performance_metrics_data_structure,
        test_health_check_functionality,
        test_performance_statistics,
        test_performance_logging,
        test_performance_recommendations,
        test_system_performance_impact_logging
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
    
    print("=" * 70)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All performance monitoring tests passed!")
        return True
    else:
        print(f"⚠️  {failed} test(s) failed. Please review the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)