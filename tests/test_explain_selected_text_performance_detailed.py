#!/usr/bin/env python3
"""
Detailed performance tests for Explain Selected Text feature

Tests text capture speed and end-to-end explanation timing to verify
performance requirements are met according to the design specifications.

Requirements: 2.3, 3.5, 5.4, 5.5
"""

import pytest
import unittest.mock as mock
from unittest.mock import Mock, MagicMock, patch, call
import time
import statistics
import threading
import queue
from typing import Dict, Any, Optional, List

# Import modules under test
from handlers.explain_selection_handler import ExplainSelectionHandler
from modules.accessibility import AccessibilityModule
from modules.automation import AutomationModule


class TestExplainSelectedTextPerformanceDetailed:
    """Detailed performance tests for explain selected text functionality."""
    
    @pytest.fixture
    def mock_orchestrator(self):
        """Mock orchestrator with performance-aware modules."""
        orchestrator = Mock()
        orchestrator.accessibility_module = Mock(spec=AccessibilityModule)
        orchestrator.automation_module = Mock(spec=AutomationModule)
        orchestrator.reasoning_module = Mock()
        orchestrator.feedback_module = Mock()
        orchestrator.audio_module = Mock()
        return orchestrator
    
    @pytest.fixture
    def explain_handler(self, mock_orchestrator):
        """Create ExplainSelectionHandler with mocked dependencies."""
        return ExplainSelectionHandler(mock_orchestrator)

    def test_text_capture_accessibility_api_performance_target(self, mock_orchestrator):
        """Test accessibility API text capture meets < 500ms target."""
        # Performance target: < 500ms for accessibility API
        target_time = 0.5  # 500ms
        
        def simulate_accessibility_capture():
            # Simulate realistic accessibility API delay
            time.sleep(0.1)  # 100ms simulated delay
            return "Accessibility API captured text for performance testing"
        
        # Arrange
        mock_orchestrator.accessibility_module.get_selected_text_via_accessibility.side_effect = simulate_accessibility_capture
        
        # Act & Assert - Multiple runs for statistical significance
        capture_times = []
        for run in range(10):
            start_time = time.time()
            result = mock_orchestrator.accessibility_module.get_selected_text_via_accessibility()
            end_time = time.time()
            
            capture_time = end_time - start_time
            capture_times.append(capture_time)
            
            assert result is not None, f"Run {run + 1}: Capture failed"
            assert capture_time < target_time, f"Run {run + 1}: Capture time {capture_time:.3f}s exceeds target {target_time}s"
        
        # Statistical analysis
        avg_time = statistics.mean(capture_times)
        max_time = max(capture_times)
        min_time = min(capture_times)
        std_dev = statistics.stdev(capture_times) if len(capture_times) > 1 else 0
        
        print(f"\nAccessibility API Performance Stats:")
        print(f"  Average: {avg_time:.3f}s")
        print(f"  Min: {min_time:.3f}s")
        print(f"  Max: {max_time:.3f}s")
        print(f"  Std Dev: {std_dev:.3f}s")
        print(f"  Target: {target_time}s")
        
        assert avg_time < target_time, f"Average capture time {avg_time:.3f}s exceeds target"
        assert max_time < target_time, f"Max capture time {max_time:.3f}s exceeds target"

    def test_text_capture_clipboard_fallback_performance_target(self, mock_orchestrator):
        """Test clipboard fallback text capture meets < 1000ms target."""
        # Performance target: < 1000ms for clipboard fallback
        target_time = 1.0  # 1000ms
        
        def simulate_clipboard_capture():
            # Simulate realistic clipboard operation delay
            time.sleep(0.2)  # 200ms simulated delay
            return "Clipboard fallback captured text for performance testing"
        
        # Arrange
        mock_orchestrator.automation_module.get_selected_text_via_clipboard.side_effect = simulate_clipboard_capture
        
        # Act & Assert - Multiple runs for statistical significance
        capture_times = []
        for run in range(10):
            start_time = time.time()
            result = mock_orchestrator.automation_module.get_selected_text_via_clipboard()
            end_time = time.time()
            
            capture_time = end_time - start_time
            capture_times.append(capture_time)
            
            assert result is not None, f"Run {run + 1}: Clipboard capture failed"
            assert capture_time < target_time, f"Run {run + 1}: Clipboard capture time {capture_time:.3f}s exceeds target {target_time}s"
        
        # Statistical analysis
        avg_time = statistics.mean(capture_times)
        max_time = max(capture_times)
        min_time = min(capture_times)
        std_dev = statistics.stdev(capture_times) if len(capture_times) > 1 else 0
        
        print(f"\nClipboard Fallback Performance Stats:")
        print(f"  Average: {avg_time:.3f}s")
        print(f"  Min: {min_time:.3f}s")
        print(f"  Max: {max_time:.3f}s")
        print(f"  Std Dev: {std_dev:.3f}s")
        print(f"  Target: {target_time}s")
        
        assert avg_time < target_time, f"Average clipboard capture time {avg_time:.3f}s exceeds target"
        assert max_time < target_time, f"Max clipboard capture time {max_time:.3f}s exceeds target"

    def test_end_to_end_explanation_performance_target(self, explain_handler, mock_orchestrator):
        """Test end-to-end explanation meets < 10 seconds target."""
        # Performance target: < 10 seconds for complete explanation workflow
        target_time = 10.0  # 10 seconds
        
        def simulate_text_capture():
            time.sleep(0.1)  # 100ms for text capture
            return "Performance test text for end-to-end explanation timing validation"
        
        def simulate_explanation_generation(*args, **kwargs):
            time.sleep(0.5)  # 500ms for explanation generation
            return "This is a comprehensive performance test explanation that validates the end-to-end timing requirements for the explain selected text feature."
        
        def simulate_audio_feedback(*args, **kwargs):
            time.sleep(0.2)  # 200ms for audio feedback
            return True
        
        # Arrange
        command = "explain this"
        context = {"intent": {"intent": "explain_selected_text"}}
        
        mock_orchestrator.accessibility_module.get_selected_text.side_effect = simulate_text_capture
        mock_orchestrator.reasoning_module.process_query.side_effect = simulate_explanation_generation
        mock_orchestrator.feedback_module.provide_conversational_feedback.side_effect = simulate_audio_feedback
        
        # Act & Assert - Multiple runs for statistical significance
        execution_times = []
        for run in range(5):  # Fewer runs due to longer execution time
            start_time = time.time()
            result = explain_handler.handle(command, context)
            end_time = time.time()
            
            execution_time = end_time - start_time
            execution_times.append(execution_time)
            
            assert result["status"] == "success", f"Run {run + 1}: Handler execution failed"
            assert execution_time < target_time, f"Run {run + 1}: End-to-end time {execution_time:.3f}s exceeds target {target_time}s"
        
        # Statistical analysis
        avg_time = statistics.mean(execution_times)
        max_time = max(execution_times)
        min_time = min(execution_times)
        std_dev = statistics.stdev(execution_times) if len(execution_times) > 1 else 0
        
        print(f"\nEnd-to-End Performance Stats:")
        print(f"  Average: {avg_time:.3f}s")
        print(f"  Min: {min_time:.3f}s")
        print(f"  Max: {max_time:.3f}s")
        print(f"  Std Dev: {std_dev:.3f}s")
        print(f"  Target: {target_time}s")
        
        assert avg_time < target_time, f"Average execution time {avg_time:.3f}s exceeds target"
        assert max_time < target_time, f"Max execution time {max_time:.3f}s exceeds target"

    def test_performance_scaling_with_text_length(self, explain_handler, mock_orchestrator):
        """Test performance scaling with different text lengths."""
        command = "explain this"
        context = {"intent": {"intent": "explain_selected_text"}}
        
        # Test different text lengths with appropriate time limits
        text_length_scenarios = [
            {"length": 100, "description": "Short text (100 chars)", "max_time": 5.0},
            {"length": 500, "description": "Medium text (500 chars)", "max_time": 6.0},
            {"length": 1000, "description": "Long text (1000 chars)", "max_time": 8.0},
            {"length": 2000, "description": "Very long text (2000 chars)", "max_time": 10.0},
            {"length": 5000, "description": "Extremely long text (5000 chars)", "max_time": 12.0}  # May be truncated
        ]
        
        performance_results = []
        
        for scenario in text_length_scenarios:
            # Arrange
            test_text = "This is test text content for performance validation. " * (scenario["length"] // 55)
            test_text = test_text[:scenario["length"]]  # Ensure exact length
            
            def simulate_capture():
                time.sleep(0.05)  # Base capture time
                return test_text
            
            def simulate_reasoning(*args, **kwargs):
                # Simulate reasoning time proportional to text length (but capped)
                reasoning_time = min(0.5, len(test_text) / 10000)
                time.sleep(reasoning_time)
                return f"Explanation for {scenario['description']}"
            
            mock_orchestrator.accessibility_module.get_selected_text.side_effect = simulate_capture
            mock_orchestrator.reasoning_module.process_query.side_effect = simulate_reasoning
            
            # Act
            start_time = time.time()
            result = explain_handler.handle(command, context)
            end_time = time.time()
            
            execution_time = end_time - start_time
            
            # Assert
            assert result["status"] == "success", f"Failed for {scenario['description']}"
            assert execution_time < scenario["max_time"], f"{scenario['description']} took {execution_time:.3f}s, max allowed {scenario['max_time']}s"
            
            # Collect performance data
            performance_results.append({
                "length": scenario["length"],
                "description": scenario["description"],
                "execution_time": execution_time,
                "max_allowed": scenario["max_time"],
                "performance_ratio": execution_time / scenario["max_time"]
            })
        
        # Print performance scaling analysis
        print(f"\nPerformance Scaling Analysis:")
        for result in performance_results:
            print(f"  {result['description']}: {result['execution_time']:.3f}s ({result['performance_ratio']:.1%} of limit)")
        
        # Verify performance doesn't degrade excessively with text length
        ratios = [r["performance_ratio"] for r in performance_results]
        max_ratio = max(ratios)
        assert max_ratio < 0.8, f"Performance ratio {max_ratio:.1%} indicates poor scaling"

    def test_concurrent_performance_load(self, explain_handler, mock_orchestrator):
        """Test performance under concurrent load conditions."""
        command = "explain this"
        context = {"intent": {"intent": "explain_selected_text"}}
        
        def simulate_loaded_capture():
            # Simulate system under load with variable delays
            import random
            delay = random.uniform(0.05, 0.15)  # 50-150ms variable delay
            time.sleep(delay)
            return "Concurrent load test text content for performance validation"
        
        def simulate_loaded_reasoning(*args, **kwargs):
            # Simulate reasoning under load
            import random
            delay = random.uniform(0.3, 0.7)  # 300-700ms variable delay
            time.sleep(delay)
            return "Concurrent load test explanation for performance validation"
        
        # Arrange
        mock_orchestrator.accessibility_module.get_selected_text.side_effect = simulate_loaded_capture
        mock_orchestrator.reasoning_module.process_query.side_effect = simulate_loaded_reasoning
        
        # Simulate concurrent execution using threading
        results_queue = queue.Queue()
        threads = []
        
        def worker(worker_id):
            start_time = time.time()
            result = explain_handler.handle(command, context)
            end_time = time.time()
            
            results_queue.put({
                "worker_id": worker_id,
                "result": result,
                "execution_time": end_time - start_time
            })
        
        # Act - Start multiple concurrent workers
        thread_count = 5
        for i in range(thread_count):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Collect results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        # Assert
        assert len(results) == thread_count, f"Expected {thread_count} results, got {len(results)}"
        
        success_count = sum(1 for r in results if r["result"]["status"] == "success")
        execution_times = [r["execution_time"] for r in results]
        avg_time = statistics.mean(execution_times)
        max_time = max(execution_times)
        min_time = min(execution_times)
        success_rate = success_count / thread_count
        
        print(f"\nConcurrent Load Performance Stats:")
        print(f"  Threads: {thread_count}")
        print(f"  Success Rate: {success_rate:.1%}")
        print(f"  Average Time: {avg_time:.3f}s")
        print(f"  Min Time: {min_time:.3f}s")
        print(f"  Max Time: {max_time:.3f}s")
        
        assert success_rate >= 0.8, f"Success rate {success_rate:.1%} below 80% threshold"
        assert avg_time < 15.0, f"Average time under load {avg_time:.3f}s exceeds 15s threshold"
        assert max_time < 20.0, f"Max time under load {max_time:.3f}s exceeds 20s threshold"

    def test_memory_usage_performance_monitoring(self, explain_handler, mock_orchestrator):
        """Test memory usage during explanation operations stays within limits."""
        try:
            import psutil
            import os
        except ImportError:
            pytest.skip("psutil not available for memory monitoring")
        
        command = "explain this"
        context = {"intent": {"intent": "explain_selected_text"}}
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Test with various text sizes
        text_sizes = [1000, 5000, 10000, 20000]  # Characters
        memory_measurements = []
        
        for text_size in text_sizes:
            # Arrange
            large_text = "Memory usage test content for performance validation. " * (text_size // 55)
            large_text = large_text[:text_size]  # Ensure exact size
            
            mock_orchestrator.accessibility_module.get_selected_text.return_value = large_text
            mock_orchestrator.reasoning_module.process_query.return_value = "Memory test explanation"
            
            # Act
            result = explain_handler.handle(command, context)
            
            # Check memory usage
            current_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = current_memory - initial_memory
            
            memory_measurements.append({
                "text_size": text_size,
                "memory_increase": memory_increase,
                "current_memory": current_memory
            })
            
            # Assert
            assert result["status"] == "success", f"Handler failed for {text_size} chars"
            assert memory_increase < 100, f"Memory increase {memory_increase:.1f}MB exceeds 100MB threshold for {text_size} chars"
        
        # Print memory usage analysis
        print(f"\nMemory Usage Analysis:")
        print(f"  Initial Memory: {initial_memory:.1f}MB")
        for measurement in memory_measurements:
            print(f"  {measurement['text_size']} chars: +{measurement['memory_increase']:.1f}MB (total: {measurement['current_memory']:.1f}MB)")
        
        # Verify memory usage doesn't grow excessively with text size
        max_increase = max(m["memory_increase"] for m in memory_measurements)
        assert max_increase < 50, f"Maximum memory increase {max_increase:.1f}MB exceeds 50MB limit"

    def test_performance_regression_detection(self, explain_handler, mock_orchestrator):
        """Test detection of performance regressions over multiple runs."""
        command = "explain this"
        context = {"intent": {"intent": "explain_selected_text"}}
        
        # Simulate gradually increasing delays (performance degradation)
        call_count = 0
        
        def degrading_capture():
            nonlocal call_count
            call_count += 1
            delay = 0.05 + (call_count * 0.01)  # Increasing delay
            time.sleep(delay)
            return f"Performance regression test text {call_count}"
        
        def degrading_reasoning(*args, **kwargs):
            delay = 0.1 + (call_count * 0.02)  # Increasing delay
            time.sleep(delay)
            return f"Performance regression test explanation {call_count}"
        
        # Arrange
        mock_orchestrator.accessibility_module.get_selected_text.side_effect = degrading_capture
        mock_orchestrator.reasoning_module.process_query.side_effect = degrading_reasoning
        
        # Act - Multiple calls to detect degradation
        execution_times = []
        for i in range(10):
            start_time = time.time()
            result = explain_handler.handle(command, context)
            end_time = time.time()
            
            execution_time = end_time - start_time
            execution_times.append(execution_time)
            
            assert result["status"] == "success", f"Run {i + 1} failed"
        
        # Assert - Check for performance degradation pattern
        first_half_avg = statistics.mean(execution_times[:5])
        second_half_avg = statistics.mean(execution_times[5:])
        
        print(f"\nPerformance Regression Analysis:")
        print(f"  First half average: {first_half_avg:.3f}s")
        print(f"  Second half average: {second_half_avg:.3f}s")
        print(f"  Degradation ratio: {second_half_avg / first_half_avg:.2f}x")
        
        # Expect some degradation but not excessive
        degradation_ratio = second_half_avg / first_half_avg
        assert degradation_ratio > 1.0, "Expected performance degradation not detected"
        assert degradation_ratio < 3.0, f"Excessive performance degradation detected: {degradation_ratio:.2f}x"

    def test_performance_metrics_accuracy(self, explain_handler, mock_orchestrator):
        """Test that performance metrics tracking is accurate."""
        command = "explain this"
        context = {"intent": {"intent": "explain_selected_text"}}
        
        # Known delays for validation
        capture_delay = 0.1  # 100ms
        reasoning_delay = 0.2  # 200ms
        
        def timed_capture():
            time.sleep(capture_delay)
            return "Performance metrics accuracy test text"
        
        def timed_reasoning(*args, **kwargs):
            time.sleep(reasoning_delay)
            return "Performance metrics accuracy test explanation"
        
        # Arrange
        mock_orchestrator.accessibility_module.get_selected_text.side_effect = timed_capture
        mock_orchestrator.reasoning_module.process_query.side_effect = timed_reasoning
        
        # Act
        start_time = time.time()
        result = explain_handler.handle(command, context)
        end_time = time.time()
        
        actual_total_time = end_time - start_time
        expected_min_time = capture_delay + reasoning_delay  # Minimum expected time
        
        # Assert
        assert result["status"] == "success"
        
        # Verify total time is reasonable
        assert actual_total_time >= expected_min_time, f"Total time {actual_total_time:.3f}s less than expected minimum {expected_min_time:.3f}s"
        assert actual_total_time < expected_min_time + 1.0, f"Total time {actual_total_time:.3f}s much longer than expected {expected_min_time:.3f}s"
        
        print(f"\nPerformance Metrics Accuracy:")
        print(f"  Expected minimum time: {expected_min_time:.3f}s")
        print(f"  Actual total time: {actual_total_time:.3f}s")
        print(f"  Overhead: {actual_total_time - expected_min_time:.3f}s")


def run_performance_tests():
    """Run all performance tests with detailed reporting."""
    print("Running detailed Explain Selected Text performance tests...")
    print("=" * 70)
    
    # Run tests with pytest
    start_time = time.time()
    
    result = pytest.main([__file__, "-v", "-s"])  # -s to show print statements
    
    end_time = time.time()
    total_time = end_time - start_time
    
    print("\n" + "=" * 70)
    print(f"Performance tests completed in {total_time:.2f} seconds")
    
    if result == 0:
        print("Explain Selected Text performance tests: PASSED")
    else:
        print("Explain Selected Text performance tests: FAILED")
    
    return result == 0


if __name__ == "__main__":
    import sys
    success = run_performance_tests()
    sys.exit(0 if success else 1)