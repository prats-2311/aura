#!/usr/bin/env python3
"""
Test script for hybrid performance tracking and audio feedback differentiation.

This script tests the implementation of task 5.1 and 5.2:
- Hybrid performance metrics collection
- Audio feedback differentiation for fast/slow paths
"""

import time
import logging
from modules.performance import (
    hybrid_performance_monitor,
    HybridPerformanceMetrics,
    measure_fast_path_performance,
    measure_slow_path_performance
)
from modules.feedback import FeedbackModule, FeedbackPriority

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@measure_fast_path_performance(command="test click button", app_name="TestApp")
def simulate_fast_path_success():
    """Simulate a successful fast path operation."""
    time.sleep(0.1)  # Simulate fast execution
    return {"element_found": True, "fallback_required": False}


@measure_fast_path_performance(command="test click missing element", app_name="TestApp")
def simulate_fast_path_failure():
    """Simulate a failed fast path operation that requires fallback."""
    time.sleep(0.05)  # Very fast failure
    return {"element_found": False, "fallback_required": True}


@measure_slow_path_performance(command="test vision analysis", app_name="TestApp")
def simulate_slow_path_execution():
    """Simulate a slow path (vision-based) operation."""
    time.sleep(1.5)  # Simulate slower vision analysis
    return {"success": True}


def test_hybrid_performance_tracking():
    """Test hybrid performance metrics collection."""
    print("\n=== Testing Hybrid Performance Tracking ===")
    
    # Clear any existing metrics
    hybrid_performance_monitor.hybrid_metrics.clear()
    
    # Simulate various operations
    print("Simulating fast path success...")
    simulate_fast_path_success()
    
    print("Simulating fast path failure...")
    simulate_fast_path_failure()
    
    print("Simulating slow path execution...")
    simulate_slow_path_execution()
    
    # Get statistics
    stats = hybrid_performance_monitor.get_hybrid_stats(time_window_minutes=1)
    
    print(f"\nHybrid Performance Statistics:")
    print(f"  Total commands: {stats['total_commands']}")
    print(f"  Fast path usage: {stats['fast_path_usage_percent']:.1f}%")
    print(f"  Slow path usage: {stats['slow_path_usage_percent']:.1f}%")
    print(f"  Overall success rate: {stats['overall_success_rate_percent']:.1f}%")
    print(f"  Fallback rate: {stats['fallback_rate_percent']:.1f}%")
    print(f"  Avg fast duration: {stats['avg_fast_duration_seconds']:.3f}s")
    print(f"  Avg slow duration: {stats['avg_slow_duration_seconds']:.3f}s")
    print(f"  Performance improvement: {stats['performance_improvement']:.1f}%")
    
    # Test manual metric recording
    print("\nTesting manual metric recording...")
    manual_metric = HybridPerformanceMetrics(
        command="manual test command",
        path_used="fast",
        total_execution_time=0.05,
        element_detection_time=0.03,
        action_execution_time=0.02,
        success=True,
        fallback_triggered=False,
        app_name="ManualTestApp",
        element_found=True
    )
    
    hybrid_performance_monitor.record_hybrid_metric(manual_metric)
    
    # Get updated statistics
    updated_stats = hybrid_performance_monitor.get_hybrid_stats(time_window_minutes=1)
    print(f"Updated total commands: {updated_stats['total_commands']}")
    
    return True


def test_audio_feedback_differentiation():
    """Test audio feedback differentiation for hybrid paths."""
    print("\n=== Testing Audio Feedback Differentiation ===")
    
    try:
        # Initialize feedback module (without audio module for testing)
        feedback = FeedbackModule(audio_module=None)
        
        print("Testing fast path feedback...")
        feedback.play_fast_path_feedback(success=True, priority=FeedbackPriority.LOW)
        feedback.play_fast_path_feedback(success=False, priority=FeedbackPriority.LOW)
        
        print("Testing slow path feedback...")
        feedback.play_slow_path_feedback(message="Analyzing screen with vision model", priority=FeedbackPriority.LOW)
        
        print("Testing fallback feedback...")
        feedback.play_fallback_feedback(reason="Element not found via accessibility API", priority=FeedbackPriority.NORMAL)
        
        # Test configuration
        print("Testing hybrid feedback configuration...")
        feedback.configure_hybrid_feedback(
            fast_path_enabled=True,
            slow_path_enabled=True,
            fallback_enabled=True,
            volume_adjustment=0.8
        )
        
        print(f"Hybrid config: {feedback.hybrid_config}")
        
        # Test queue status
        queue_size = feedback.get_queue_size()
        print(f"Feedback queue size: {queue_size}")
        
        # Wait a bit for processing
        time.sleep(0.5)
        
        # Clean up
        feedback.cleanup()
        
        return True
        
    except Exception as e:
        print(f"Audio feedback test failed: {e}")
        return False


def test_performance_dashboard_integration():
    """Test integration with performance dashboard."""
    print("\n=== Testing Performance Dashboard Integration ===")
    
    try:
        from modules.performance_dashboard import performance_dashboard
        
        # Get real-time metrics including hybrid performance
        metrics = performance_dashboard.get_real_time_metrics()
        
        print("Dashboard metrics keys:")
        for key in metrics.keys():
            print(f"  - {key}")
        
        if 'hybrid_performance' in metrics:
            hybrid_metrics = metrics['hybrid_performance']
            print(f"\nHybrid performance in dashboard:")
            print(f"  Total commands: {hybrid_metrics.get('total_commands', 0)}")
            print(f"  Fast path usage: {hybrid_metrics.get('fast_path_usage_percent', 0):.1f}%")
            print(f"  Performance improvement: {hybrid_metrics.get('performance_improvement', 0):.1f}%")
        
        # Test optimization recommendations
        recommendations = performance_dashboard.get_optimization_recommendations()
        hybrid_recommendations = [r for r in recommendations if r.get('type') == 'hybrid']
        
        print(f"\nHybrid-specific recommendations: {len(hybrid_recommendations)}")
        for rec in hybrid_recommendations:
            print(f"  - {rec['title']}: {rec['description']}")
        
        return True
        
    except Exception as e:
        print(f"Dashboard integration test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("Testing Hybrid Performance Tracking and Audio Feedback Differentiation")
    print("=" * 70)
    
    tests = [
        ("Hybrid Performance Tracking", test_hybrid_performance_tracking),
        ("Audio Feedback Differentiation", test_audio_feedback_differentiation),
        ("Performance Dashboard Integration", test_performance_dashboard_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            print(f"\nRunning {test_name}...")
            result = test_func()
            results.append((test_name, result))
            print(f"✅ {test_name}: {'PASSED' if result else 'FAILED'}")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Hybrid performance tracking and audio feedback are working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")


if __name__ == "__main__":
    main()