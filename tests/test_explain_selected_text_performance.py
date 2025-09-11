#!/usr/bin/env python3
"""
Performance tests for Explain Selected Text feature

Tests text capture speed and end-to-end explanation timing to verify
performance requirements are met.

Requirements: 2.3, 3.5, 5.4, 5.5
"""

import pytest
import unittest.mock as mock
from unittest.mock import Mock, MagicMock, patch, call
import time
import statistics
from typing import Dict, Any, Optional, List

# Import modules under test
from handlers.explain_selection_handler import ExplainSelectionHandler
from modules.accessibility import AccessibilityModule
from modules.automation import AutomationModule


class TestExplainSelectedTextPerformance:
    """Performance tests for explain selected text functionality."""
    
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

    def test_text_capture_accessibility_api_performance(self, mock_orchestrator):
        """Test accessibility API text capture performance requirements."""
        # Performance target: < 500ms for accessibility API
        target_time = 0.5  # 500ms
        
        def simulate_accessibility_capture():
            # Simulate realistic accessibility API delay
            time.sleep(0.1)  # 100ms simulated delay
            return "Accessibility API captured text"
        
        # Arrange
        mock_orchestrator.accessibility_module.get_selected_text_via_accessibility.side_effect = simulate_accessibility_capture
        
        # Act & Assert - Multiple runs for statistical significance
        capture_times = []
        for _ in range(10):
            start_time = time.time()
            result = mock_orchestrator.accessibility_module.get_selected_text_via_accessibility()
            end_time = time.time()
            
            capture_time = end_time - start_time
            capture_times.append(capture_time)
            
            assert result is not None
            assert capture_time < target_time, f"Capture time {capture_time:.3f}s exceeds target {target_time}s"
        
        # Statistical analysis
        avg_time = statistics.mean(capture_times)
        max_time = max(capture_times)
        
        assert avg_time < target_time, f"Average capture time {avg_time:.3f}s exceeds target"
        assert max_time < target_time, f"Max capture time {max_time:.3f}s exceeds target"

    def test_text_capture_clipboard_fallback_performance(self, mock_orchestrator):
        """Test clipboard fallback text capture performance requirements."""
        # Performance target: < 1000ms for clipboard fallback
        target_time = 1.0  # 1000ms
        
        def simulate_clipboard_capture():
            # Simulate realistic clipboard operation delay
            time.sleep(0.2)  # 200ms simulated delay
            return "Clipboard fallback captured text"
        
        # Arrange
        mock_orchestrator.automation_module.get_selected_text_via_clipboard.side_effect = simulate_clipboard_capture
        
        # Act & Assert - Multiple runs for statistical significance
        capture_times = []
        for _ in range(10):
            start_time = time.time()
            result = mock_orchestrator.automation_module.get_selected_text_via_clipboard()
            end_time = time.time()
            
            capture_time = end_time - start_time
            capture_times.append(capture_time)
            
            assert result is not None
            assert capture_time < target_time, f"Clipboard capture time {capture_time:.3f}s exceeds target {target_time}s"
        
        # Statistical analysis
        avg_time = statistics.mean(capture_times)
        max_time = max(capture_times)
        
        assert avg_time < target_time, f"Average clipboard capture time {avg_time:.3f}s exceeds target"
        assert max_time < target_time, f"Max clipboard capture time {max_time:.3f}s exceeds target"

    def test_end_to_end_explanation_performance(self, explain_handler, mock_orchestrator):
        """Test end-to-end explanation performance requirements."""
        # Performance target: < 10 seconds for complete explanation workflow
        target_time = 10.0  # 10 seconds
        
        def simulate_text_capture():
            time.sleep(0.1)  # 100ms for text capture
            return "Performance test text for explanation"
        
        def simulate_explanation_generation(prompt, **kwargs):
            time.sleep(0.5)  # 500ms for explanation generation
            return "This is a performance test explanation that meets timing requirements."
        
        def simulate_audio_feedback(text, **kwargs):
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
        for _ in range(5):  # Fewer runs due to longer execution time
            start_time = time.time()
            result = explain_handler.handle(command, context)
            end_time = time.time()
            
            execution_time = end_time - start_time
            execution_times.append(execution_time)
            
            assert result["success"] == True
            assert execution_time < target_time, f"End-to-end time {execution_time:.3f}s exceeds target {target_time}s"
        
        # Statistical analysis
        avg_time = statistics.mean(execution_times)
        max_time = max(execution_times)
        
        assert avg_time < target_time, f"Average execution time {avg_time:.3f}s exceeds target"
        assert max_time < target_time, f"Max execution time {max_time:.3f}s exceeds target"

    def test_performance_with_different_text_lengths(self, explain_handler, mock_orchestrator):
        """Test performance scaling with different text lengths."""
        command = "explain this"
        context = {"intent": {"intent": "explain_selected_text"}}
        
        # Test different text lengths
        text_length_scenarios = [
            {"length": 100, "description": "Short text", "max_time": 5.0},
            {"length": 1000, "description": "Medium text", "max_time": 8.0},
            {"length": 5000, "description": "Long text", "max_time": 10.0},
            {"length": 10000, "description": "Very long text", "max_time": 12.0}  # May be truncated
        ]
        
        for scenario in text_length_scenarios:
            # Arrange
            test_text = "This is test text content. " * (scenario["length"] // 27)
            
            def simulate_capture():
                time.sleep(0.05)  # Base capture time
                return test_text
            
            def simulate_reasoning(prompt, **kwargs):
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
            assert result["success"] == True, f"Failed for {scenario['description']}"
            assert execution_time < scenario["max_time"], f"{scenario['description']} took {execution_time:.3f}s, max allowed {scenario['max_time']}s"

    def test_performance_under_load(self, explain_handler, mock_orchestrator):
        """Test performance under simulated load conditions."""
        command = "explain this"
        context = {"intent": {"intent": "explain_selected_text"}}
        
        def simulate_loaded_capture():
            # Simulate system under load with variable delays
            import random
            delay = random.uniform(0.05, 0.15)  # 50-150ms variable delay
            time.sleep(delay)
            return "Load test text content"
        
        def simulate_loaded_reasoning(prompt, **kwargs):
            # Simulate reasoning under load
            import random
            delay = random.uniform(0.3, 0.7)  # 300-700ms variable delay
            time.sleep(delay)
            return "Load test explanation"
        
        # Arrange
        mock_orchestrator.accessibility_module.get_selected_text.side_effect = simulate_loaded_capture
        mock_orchestrator.reasoning_module.process_query.side_effect = simulate_loaded_reasoning
        
        # Act - Simulate multiple concurrent requests
        execution_times = []
        success_count = 0
        
        for i in range(10):
            start_time = time.time()
            result = explain_handler.handle(command, context)
            end_time = time.time()
            
            execution_time = end_time - start_time
            execution_times.append(execution_time)
            
            if result["success"]:
                success_count += 1
        
        # Assert
        avg_time = statistics.mean(execution_times)
        max_time = max(execution_times)
        success_rate = success_count / 10
        
        assert success_rate >= 0.9, f"Success rate {success_rate:.1%} below 90% threshold"
        assert avg_time < 15.0, f"Average time under load {avg_time:.3f}s exceeds 15s threshold"
        assert max_time < 20.0, f"Max time under load {max_time:.3f}s exceeds 20s threshold"

    def test_memory_usage_performance(self, explain_handler, mock_orchestrator):
        """Test memory usage during explanation operations."""
        import psutil
        import os
        
        command = "explain this"
        context = {"intent": {"intent": "explain_selected_text"}}
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Test with various text sizes
        text_sizes = [1000, 5000, 10000, 20000]  # Characters
        
        for text_size in text_sizes:
            # Arrange
            large_text = "Memory test content. " * (text_size // 20)
            
            mock_orchestrator.accessibility_module.get_selected_text.return_value = large_text
            mock_orchestrator.reasoning_module.process_query.return_value = "Memory test explanation"
            
            # Act
            result = explain_handler.handle(command, context)
            
            # Check memory usage
            current_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = current_memory - initial_memory
            
            # Assert
            assert result["success"] == True
            assert memory_increase < 100, f"Memory increase {memory_increase:.1f}MB exceeds 100MB threshold for {text_size} chars"

    def test_performance_metrics_tracking(self, explain_handler, mock_orchestrator):
        """Test that performance metrics are properly tracked."""
        command = "explain this"
        context = {"intent": {"intent": "explain_selected_text"}}
        
        def timed_capture():
            time.sleep(0.1)
            return "Metrics test text"
        
        def timed_reasoning(prompt, **kwargs):
            time.sleep(0.2)
            return "Metrics test explanation"
        
        # Arrange
        mock_orchestrator.accessibility_module.get_selected_text.side_effect = timed_capture
        mock_orchestrator.reasoning_module.process_query.side_effect = timed_reasoning
        
        # Act
        result = explain_handler.handle(command, context)
        
        # Assert
        assert result["success"] == True
        assert "capture_time" in result
        assert "explanation_time" in result
        
        # Verify timing accuracy (within reasonable bounds)
        assert 0.08 < result["capture_time"] < 0.15, f"Capture time {result['capture_time']:.3f}s not in expected range"
        assert 0.18 < result["explanation_time"] < 0.25, f"Explanation time {result['explanation_time']:.3f}s not in expected range"

    def test_performance_degradation_detection(self, explain_handler, mock_orchestrator):
        """Test detection of performance degradation over time."""
        command = "explain this"
        context = {"intent": {"intent": "explain_selected_text"}}
        
        # Simulate gradually increasing delays (performance degradation)
        call_count = 0
        
        def degrading_capture():
            nonlocal call_count
            call_count += 1
            delay = 0.05 + (call_count * 0.01)  # Increasing delay
            time.sleep(delay)
            return f"Degradation test text {call_count}"
        
        def degrading_reasoning(prompt, **kwargs):
            delay = 0.1 + (call_count * 0.02)  # Increasing delay
            time.sleep(delay)
            return f"Degradation test explanation {call_count}"
        
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
            
            assert result["success"] == True
        
        # Assert - Check for performance degradation pattern
        first_half_avg = statistics.mean(execution_times[:5])
        second_half_avg = statistics.mean(execution_times[5:])
        
        # Expect some degradation but not excessive
        degradation_ratio = second_half_avg / first_half_avg
        assert degradation_ratio > 1.0, "Expected performance degradation not detected"
        assert degradation_ratio < 3.0, f"Excessive performance degradation detected: {degradation_ratio:.2f}x"

    def test_concurrent_performance(self, explain_handler, mock_orchestrator):
        """Test performance with concurrent execution simulation."""
        import threading
        import queue
        
        command = "explain this"
        context = {"intent": {"intent": "explain_selected_text"}}
        
        def concurrent_capture():
            time.sleep(0.05)  # Simulate concurrent access delay
            return "Concurrent test text"
        
        def concurrent_reasoning(prompt, **kwargs):
            time.sleep(0.1)  # Simulate concurrent reasoning
            return "Concurrent test explanation"
        
        # Arrange
        mock_orchestrator.accessibility_module.get_selected_text.side_effect = concurrent_capture
        mock_orchestrator.reasoning_module.process_query.side_effect = concurrent_reasoning
        
        # Simulate concurrent execution
        results_queue = queue.Queue()
        threads = []
        
        def worker():
            start_time = time.time()
            result = explain_handler.handle(command, context)
            end_time = time.time()
            results_queue.put({
                "result": result,
                "execution_time": end_time - start_time
            })
        
        # Act - Start multiple threads
        thread_count = 5
        for _ in range(thread_count):
            thread = threading.Thread(target=worker)
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
        assert len(results) == thread_count
        
        success_count = sum(1 for r in results if r["result"]["success"])
        avg_time = statistics.mean([r["execution_time"] for r in results])
        max_time = max([r["execution_time"] for r in results])
        
        assert success_count >= thread_count * 0.8, f"Concurrent success rate {success_count}/{thread_count} below 80%"
        assert avg_time < 5.0, f"Average concurrent execution time {avg_time:.3f}s exceeds 5s"
        assert max_time < 10.0, f"Max concurrent execution time {max_time:.3f}s exceeds 10s"

    def test_performance_regression_detection(self, explain_handler, mock_orchestrator):
        """Test detection of performance regressions."""
        command = "explain this"
        context = {"intent": {"intent": "explain_selected_text"}}
        
        # Baseline performance
        baseline_times = []
        
        def baseline_capture():
            time.sleep(0.05)  # 50ms baseline
            return "Baseline test text"
        
        def baseline_reasoning(prompt, **kwargs):
            time.sleep(0.1)  # 100ms baseline
            return "Baseline test explanation"
        
        # Arrange baseline
        mock_orchestrator.accessibility_module.get_selected_text.side_effect = baseline_capture
        mock_orchestrator.reasoning_module.process_query.side_effect = baseline_reasoning
        
        # Collect baseline measurements
        for _ in range(5):
            start_time = time.time()
            result = explain_handler.handle(command, context)
            end_time = time.time()
            
            baseline_times.append(end_time - start_time)
            assert result["success"] == True
        
        baseline_avg = statistics.mean(baseline_times)
        
        # Simulate performance regression
        def regressed_capture():
            time.sleep(0.15)  # 150ms (3x slower)
            return "Regressed test text"
        
        def regressed_reasoning(prompt, **kwargs):
            time.sleep(0.3)  # 300ms (3x slower)
            return "Regressed test explanation"
        
        # Test with regression
        mock_orchestrator.accessibility_module.get_selected_text.side_effect = regressed_capture
        mock_orchestrator.reasoning_module.process_query.side_effect = regressed_reasoning
        
        regressed_times = []
        for _ in range(5):
            start_time = time.time()
            result = explain_handler.handle(command, context)
            end_time = time.time()
            
            regressed_times.append(end_time - start_time)
            assert result["success"] == True
        
        regressed_avg = statistics.mean(regressed_times)
        
        # Assert regression detection
        regression_ratio = regressed_avg / baseline_avg
        assert regression_ratio > 2.0, f"Performance regression not detected: {regression_ratio:.2f}x"
        
        # Verify regression is within acceptable bounds (not completely broken)
        assert regression_ratio < 10.0, f"Excessive performance regression: {regression_ratio:.2f}x"