#!/usr/bin/env python3
"""
Performance Regression Tests for Hybrid Architecture

Automated tests to detect performance regressions and ensure the system
maintains speed improvements over time.

Requirements: 1.3, 6.2, 6.3
"""

import pytest
import time
import statistics
import logging
from typing import Dict, Any, List
from unittest.mock import Mock, patch
from dataclasses import dataclass
from datetime import datetime

from orchestrator import Orchestrator
from modules.accessibility import AccessibilityModule


@dataclass
class PerformanceBaseline:
    """Performance baseline for regression testing."""
    test_name: str
    max_execution_time: float
    min_success_rate: float
    max_memory_increase_mb: float
    baseline_date: str


class TestPerformanceRegression:
    """Performance regression test suite."""
    
    # Performance baselines (these would be updated as the system improves)
    PERFORMANCE_BASELINES = {
        'fast_path_click': PerformanceBaseline(
            test_name='fast_path_click',
            max_execution_time=2.0,  # seconds
            min_success_rate=95.0,   # percent
            max_memory_increase_mb=10.0,  # MB
            baseline_date='2024-01-01'
        ),
        'fast_path_type': PerformanceBaseline(
            test_name='fast_path_type',
            max_execution_time=2.5,  # seconds
            min_success_rate=95.0,   # percent
            max_memory_increase_mb=10.0,  # MB
            baseline_date='2024-01-01'
        ),
        'accessibility_element_detection': PerformanceBaseline(
            test_name='accessibility_element_detection',
            max_execution_time=1.0,  # seconds
            min_success_rate=98.0,   # percent
            max_memory_increase_mb=5.0,   # MB
            baseline_date='2024-01-01'
        ),
        'fallback_mechanism': PerformanceBaseline(
            test_name='fallback_mechanism',
            max_execution_time=1.0,  # seconds (just the fallback trigger time)
            min_success_rate=99.0,   # percent
            max_memory_increase_mb=5.0,   # MB
            baseline_date='2024-01-01'
        )
    }
    
    @pytest.fixture
    def mock_orchestrator(self):
        """Create mock orchestrator for regression testing."""
        with patch('orchestrator.VisionModule') as mock_vision_class, \
             patch('orchestrator.ReasoningModule') as mock_reasoning_class, \
             patch('orchestrator.AutomationModule') as mock_automation_class, \
             patch('orchestrator.AudioModule') as mock_audio_class, \
             patch('orchestrator.FeedbackModule') as mock_feedback_class, \
             patch('orchestrator.AccessibilityModule') as mock_accessibility_class:
            
            # Setup module mocks with realistic performance characteristics
            mock_vision = Mock()
            mock_reasoning = Mock()
            mock_automation = Mock()
            mock_audio = Mock()
            mock_feedback = Mock()
            mock_accessibility = Mock()
            
            # Configure mock returns
            mock_vision_class.return_value = mock_vision
            mock_reasoning_class.return_value = mock_reasoning
            mock_automation_class.return_value = mock_automation
            mock_audio_class.return_value = mock_audio
            mock_feedback_class.return_value = mock_feedback
            mock_accessibility_class.return_value = mock_accessibility
            
            # Setup fast path mocks
            mock_accessibility.find_element_with_vision_preparation.return_value = {
                'coordinates': [100, 200, 150, 50],
                'center_point': [175, 225],
                'role': 'AXButton',
                'title': 'Test Button',
                'enabled': True,
                'app_name': 'TestApp'
            }
            mock_accessibility.get_accessibility_status.return_value = {
                'api_initialized': True,
                'degraded_mode': False,
                'can_attempt_recovery': False
            }
            
            mock_automation.execute_fast_path_action.return_value = {
                'success': True,
                'action_type': 'click',
                'coordinates': [175, 225],
                'execution_time': 0.1
            }
            
            orchestrator = Orchestrator()
            yield orchestrator
    
    def _run_performance_test(self, test_func, baseline: PerformanceBaseline, 
                            iterations: int = 10) -> Dict[str, Any]:
        """Run a performance test and compare against baseline."""
        execution_times = []
        success_count = 0
        memory_increases = []
        
        import psutil
        process = psutil.Process()
        
        for i in range(iterations):
            # Get initial memory
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Run test
            start_time = time.perf_counter()
            try:
                success = test_func()
                execution_time = time.perf_counter() - start_time
                execution_times.append(execution_time)
                
                if success:
                    success_count += 1
                    
            except Exception as e:
                execution_time = time.perf_counter() - start_time
                execution_times.append(execution_time)
                logging.warning(f"Test iteration {i+1} failed: {e}")
            
            # Get final memory
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory
            memory_increases.append(memory_increase)
        
        # Calculate statistics
        avg_execution_time = statistics.mean(execution_times)
        max_execution_time = max(execution_times)
        success_rate = (success_count / iterations) * 100
        avg_memory_increase = statistics.mean(memory_increases) if memory_increases else 0
        max_memory_increase = max(memory_increases) if memory_increases else 0
        
        # Check against baseline
        performance_regression = max_execution_time > baseline.max_execution_time
        success_regression = success_rate < baseline.min_success_rate
        memory_regression = max_memory_increase > baseline.max_memory_increase_mb
        
        return {
            'test_name': baseline.test_name,
            'iterations': iterations,
            'avg_execution_time': avg_execution_time,
            'max_execution_time': max_execution_time,
            'success_rate': success_rate,
            'avg_memory_increase': avg_memory_increase,
            'max_memory_increase': max_memory_increase,
            'baseline': baseline,
            'performance_regression': performance_regression,
            'success_regression': success_regression,
            'memory_regression': memory_regression,
            'overall_regression': performance_regression or success_regression or memory_regression,
            'timestamp': datetime.now().isoformat()
        }
    
    def test_fast_path_click_performance_regression(self, mock_orchestrator):
        """Test for performance regression in fast path click operations."""
        baseline = self.PERFORMANCE_BASELINES['fast_path_click']
        
        def fast_path_click_test():
            # Simulate fast path click execution
            result = mock_orchestrator._attempt_fast_path_execution(
                "click the submit button", 
                {'command_type': 'gui_interaction'}
            )
            return result and result.get('success', False)
        
        # Run performance test
        results = self._run_performance_test(fast_path_click_test, baseline, iterations=15)
        
        # Assert no regression
        assert not results['performance_regression'], \
            f"Performance regression detected: {results['max_execution_time']:.3f}s > {baseline.max_execution_time}s"
        
        assert not results['success_regression'], \
            f"Success rate regression: {results['success_rate']:.1f}% < {baseline.min_success_rate}%"
        
        assert not results['memory_regression'], \
            f"Memory regression: {results['max_memory_increase']:.1f}MB > {baseline.max_memory_increase_mb}MB"
        
        logging.info(f"Fast path click performance: {results['avg_execution_time']:.3f}s avg, "
                    f"{results['success_rate']:.1f}% success rate")
    
    def test_fast_path_type_performance_regression(self, mock_orchestrator):
        """Test for performance regression in fast path type operations."""
        baseline = self.PERFORMANCE_BASELINES['fast_path_type']
        
        def fast_path_type_test():
            # Simulate fast path type execution
            result = mock_orchestrator._attempt_fast_path_execution(
                "type 'hello world'", 
                {'command_type': 'gui_interaction'}
            )
            return result and result.get('success', False)
        
        # Run performance test
        results = self._run_performance_test(fast_path_type_test, baseline, iterations=15)
        
        # Assert no regression
        assert not results['overall_regression'], \
            f"Regression detected in fast path type: {results}"
        
        logging.info(f"Fast path type performance: {results['avg_execution_time']:.3f}s avg, "
                    f"{results['success_rate']:.1f}% success rate")
    
    def test_accessibility_element_detection_regression(self, mock_orchestrator):
        """Test for regression in accessibility element detection."""
        baseline = self.PERFORMANCE_BASELINES['accessibility_element_detection']
        
        def element_detection_test():
            # Test direct accessibility module element detection
            if hasattr(mock_orchestrator, 'accessibility_module'):
                result = mock_orchestrator.accessibility_module.find_element_with_vision_preparation(
                    'AXButton', 'Test Button'
                )
                return result is not None
            return False
        
        # Run performance test
        results = self._run_performance_test(element_detection_test, baseline, iterations=20)
        
        # Assert no regression
        assert not results['overall_regression'], \
            f"Regression detected in element detection: {results}"
        
        logging.info(f"Element detection performance: {results['avg_execution_time']:.3f}s avg, "
                    f"{results['success_rate']:.1f}% success rate")
    
    def test_fallback_mechanism_performance_regression(self, mock_orchestrator):
        """Test for regression in fallback mechanism performance."""
        baseline = self.PERFORMANCE_BASELINES['fallback_mechanism']
        
        def fallback_test():
            # Configure accessibility to fail, triggering fallback
            mock_orchestrator.accessibility_module.find_element_with_vision_preparation.return_value = None
            
            # Attempt fast path (should fail and trigger fallback logic)
            result = mock_orchestrator._attempt_fast_path_execution(
                "click the hidden button", 
                {'command_type': 'gui_interaction'}
            )
            
            # Should fail gracefully and indicate fallback is needed
            return result and result.get('fallback_required', False)
        
        # Run performance test
        results = self._run_performance_test(fallback_test, baseline, iterations=15)
        
        # Assert no regression
        assert not results['overall_regression'], \
            f"Regression detected in fallback mechanism: {results}"
        
        logging.info(f"Fallback mechanism performance: {results['avg_execution_time']:.3f}s avg, "
                    f"{results['success_rate']:.1f}% success rate")
    
    def test_concurrent_execution_performance_regression(self, mock_orchestrator):
        """Test for regression in concurrent execution performance."""
        import concurrent.futures
        import threading
        
        def concurrent_execution_test():
            # Test concurrent fast path executions
            commands = [
                "click button 1",
                "click button 2", 
                "click button 3"
            ]
            
            start_time = time.perf_counter()
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                futures = []
                for cmd in commands:
                    future = executor.submit(
                        mock_orchestrator._attempt_fast_path_execution,
                        cmd,
                        {'command_type': 'gui_interaction'}
                    )
                    futures.append(future)
                
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
                
            execution_time = time.perf_counter() - start_time
            
            # Should complete all commands successfully in reasonable time
            successful_results = [r for r in results if r and r.get('success', False)]
            return len(successful_results) == len(commands) and execution_time < 5.0
        
        # Run test multiple times
        success_count = 0
        execution_times = []
        
        for _ in range(10):
            start_time = time.perf_counter()
            success = concurrent_execution_test()
            execution_time = time.perf_counter() - start_time
            
            execution_times.append(execution_time)
            if success:
                success_count += 1
        
        avg_time = statistics.mean(execution_times)
        success_rate = (success_count / 10) * 100
        
        # Assert performance requirements
        assert avg_time < 3.0, f"Concurrent execution too slow: {avg_time:.2f}s"
        assert success_rate >= 90, f"Concurrent execution success rate too low: {success_rate:.1f}%"
        
        logging.info(f"Concurrent execution performance: {avg_time:.3f}s avg, "
                    f"{success_rate:.1f}% success rate")
    
    def test_memory_leak_regression(self, mock_orchestrator):
        """Test for memory leaks in repeated operations."""
        import psutil
        import gc
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Perform many operations to detect memory leaks
        for i in range(100):
            result = mock_orchestrator._attempt_fast_path_execution(
                f"click button {i}",
                {'command_type': 'gui_interaction'}
            )
            
            # Periodically force garbage collection
            if i % 20 == 0:
                gc.collect()
        
        # Final garbage collection
        gc.collect()
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Assert no significant memory leak
        assert memory_increase < 50, f"Memory leak detected: {memory_increase:.1f}MB increase"
        
        logging.info(f"Memory leak test: {memory_increase:.1f}MB increase after 100 operations")
    
    def test_system_stability_under_load(self, mock_orchestrator):
        """Test system stability under sustained load."""
        import threading
        import queue
        
        # Test parameters
        duration_seconds = 10
        concurrent_threads = 5
        commands_per_thread = 20
        
        results_queue = queue.Queue()
        error_queue = queue.Queue()
        
        def worker_thread(thread_id):
            """Worker thread for load testing."""
            try:
                for i in range(commands_per_thread):
                    start_time = time.perf_counter()
                    
                    result = mock_orchestrator._attempt_fast_path_execution(
                        f"click button {thread_id}_{i}",
                        {'command_type': 'gui_interaction'}
                    )
                    
                    execution_time = time.perf_counter() - start_time
                    
                    results_queue.put({
                        'thread_id': thread_id,
                        'command_id': i,
                        'success': result and result.get('success', False),
                        'execution_time': execution_time
                    })
                    
                    # Small delay to simulate realistic usage
                    time.sleep(0.1)
                    
            except Exception as e:
                error_queue.put(f"Thread {thread_id} error: {e}")
        
        # Start worker threads
        threads = []
        start_time = time.perf_counter()
        
        for thread_id in range(concurrent_threads):
            thread = threading.Thread(target=worker_thread, args=(thread_id,))
            thread.start()
            threads.append(thread)
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        total_time = time.perf_counter() - start_time
        
        # Collect results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        errors = []
        while not error_queue.empty():
            errors.append(error_queue.get())
        
        # Analyze results
        total_commands = len(results)
        successful_commands = len([r for r in results if r['success']])
        success_rate = (successful_commands / total_commands) * 100 if total_commands > 0 else 0
        
        avg_execution_time = statistics.mean(r['execution_time'] for r in results) if results else 0
        
        # Assert stability requirements
        assert len(errors) == 0, f"Errors occurred during load test: {errors}"
        assert success_rate >= 95, f"Success rate under load too low: {success_rate:.1f}%"
        assert avg_execution_time < 2.0, f"Average execution time under load too high: {avg_execution_time:.3f}s"
        
        logging.info(f"Load test: {total_commands} commands in {total_time:.2f}s, "
                    f"{success_rate:.1f}% success rate, {avg_execution_time:.3f}s avg time")


if __name__ == '__main__':
    # Configure logging for regression tests
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run regression tests
    pytest.main([
        __file__,
        '-v',
        '--tb=short',
        '--capture=no',
        '--log-cli-level=INFO'
    ])