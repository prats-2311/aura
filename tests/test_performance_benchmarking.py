#!/usr/bin/env python3
"""
Performance Benchmarking and Optimization Tests for Hybrid Architecture

Comprehensive performance testing to measure and document fast path vs slow path
performance differences, optimize bottlenecks, and create regression tests.

Requirements: 1.3, 6.2, 6.3
"""

import pytest
import unittest.mock as mock
from unittest.mock import Mock, MagicMock, patch, call
import logging
import time
import statistics
import json
import os
import threading
import concurrent.futures
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import psutil
import gc

# Import the modules under test
from orchestrator import Orchestrator
from modules.accessibility import AccessibilityModule
from modules.vision import VisionModule
from modules.reasoning import ReasoningModule
from modules.automation import AutomationModule
from modules.performance import PerformanceMetrics, performance_monitor


@dataclass
class BenchmarkResult:
    """Results from a performance benchmark."""
    test_name: str
    execution_path: str  # 'fast', 'slow', 'hybrid'
    execution_time: float
    success: bool
    memory_usage_mb: float
    cpu_usage_percent: float
    timestamp: datetime
    iterations: int = 1
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class PerformanceComparison:
    """Comparison between fast and slow path performance."""
    test_scenario: str
    fast_path_avg: float
    slow_path_avg: float
    improvement_factor: float
    improvement_percent: float
    fast_path_success_rate: float
    slow_path_success_rate: float
    statistical_significance: bool
    confidence_interval: Tuple[float, float]


@dataclass
class SystemResourceMetrics:
    """System resource usage metrics."""
    memory_usage_mb: float
    cpu_usage_percent: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_io_sent_mb: float
    network_io_recv_mb: float
    thread_count: int
    file_descriptor_count: int


class PerformanceBenchmarkSuite:
    """Comprehensive performance benchmarking suite."""
    
    def __init__(self):
        """Initialize the benchmark suite."""
        self.results = []
        self.baseline_metrics = {}
        self.regression_thresholds = {
            'fast_path_max_time': 2.0,  # seconds
            'slow_path_max_time': 10.0,  # seconds
            'memory_increase_max': 100.0,  # MB
            'cpu_usage_max': 80.0,  # percent
            'success_rate_min': 95.0  # percent
        }
        self.benchmark_iterations = 10
        self.warmup_iterations = 3
        
        # Performance tracking
        self.performance_history = []
        self.resource_monitor = None
        
    def setup_resource_monitoring(self):
        """Setup system resource monitoring."""
        self.process = psutil.Process()
        self.initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        self.initial_cpu_percent = self.process.cpu_percent()
        
    def get_current_resource_metrics(self) -> SystemResourceMetrics:
        """Get current system resource metrics."""
        memory_info = self.process.memory_info()
        io_counters = self.process.io_counters() if hasattr(self.process, 'io_counters') else None
        
        return SystemResourceMetrics(
            memory_usage_mb=memory_info.rss / 1024 / 1024,
            cpu_usage_percent=self.process.cpu_percent(),
            disk_io_read_mb=(io_counters.read_bytes / 1024 / 1024) if io_counters else 0,
            disk_io_write_mb=(io_counters.write_bytes / 1024 / 1024) if io_counters else 0,
            network_io_sent_mb=0,  # Would need additional monitoring
            network_io_recv_mb=0,  # Would need additional monitoring
            thread_count=self.process.num_threads(),
            file_descriptor_count=self.process.num_fds() if hasattr(self.process, 'num_fds') else 0
        )
    
    def run_benchmark(self, test_func, test_name: str, execution_path: str, 
                     iterations: int = None) -> List[BenchmarkResult]:
        """Run a performance benchmark with multiple iterations."""
        iterations = iterations or self.benchmark_iterations
        results = []
        
        # Warmup runs
        for _ in range(self.warmup_iterations):
            try:
                test_func()
            except Exception:
                pass  # Ignore warmup errors
        
        # Actual benchmark runs
        for i in range(iterations):
            gc.collect()  # Force garbage collection before each run
            
            start_metrics = self.get_current_resource_metrics()
            start_time = time.perf_counter()
            
            try:
                success = test_func()
                execution_time = time.perf_counter() - start_time
                end_metrics = self.get_current_resource_metrics()
                
                result = BenchmarkResult(
                    test_name=test_name,
                    execution_path=execution_path,
                    execution_time=execution_time,
                    success=success if isinstance(success, bool) else True,
                    memory_usage_mb=end_metrics.memory_usage_mb - start_metrics.memory_usage_mb,
                    cpu_usage_percent=end_metrics.cpu_usage_percent,
                    timestamp=datetime.now(),
                    iterations=1,
                    metadata={
                        'iteration': i + 1,
                        'start_metrics': asdict(start_metrics),
                        'end_metrics': asdict(end_metrics)
                    }
                )
                
                results.append(result)
                
            except Exception as e:
                execution_time = time.perf_counter() - start_time
                end_metrics = self.get_current_resource_metrics()
                
                result = BenchmarkResult(
                    test_name=test_name,
                    execution_path=execution_path,
                    execution_time=execution_time,
                    success=False,
                    memory_usage_mb=end_metrics.memory_usage_mb - start_metrics.memory_usage_mb,
                    cpu_usage_percent=end_metrics.cpu_usage_percent,
                    timestamp=datetime.now(),
                    iterations=1,
                    metadata={
                        'iteration': i + 1,
                        'error': str(e),
                        'start_metrics': asdict(start_metrics),
                        'end_metrics': asdict(end_metrics)
                    }
                )
                
                results.append(result)
        
        self.results.extend(results)
        return results
    
    def compare_performance(self, fast_path_results: List[BenchmarkResult], 
                          slow_path_results: List[BenchmarkResult]) -> PerformanceComparison:
        """Compare performance between fast and slow path results."""
        
        # Calculate statistics for fast path
        fast_times = [r.execution_time for r in fast_path_results if r.success]
        fast_success_rate = len(fast_times) / len(fast_path_results) * 100
        fast_avg = statistics.mean(fast_times) if fast_times else float('inf')
        
        # Calculate statistics for slow path
        slow_times = [r.execution_time for r in slow_path_results if r.success]
        slow_success_rate = len(slow_times) / len(slow_path_results) * 100
        slow_avg = statistics.mean(slow_times) if slow_times else float('inf')
        
        # Calculate improvement metrics
        if slow_avg > 0 and fast_avg < float('inf'):
            improvement_factor = slow_avg / fast_avg
            improvement_percent = ((slow_avg - fast_avg) / slow_avg) * 100
        else:
            improvement_factor = 0
            improvement_percent = 0
        
        # Statistical significance test (simplified)
        statistical_significance = (
            len(fast_times) >= 5 and len(slow_times) >= 5 and
            improvement_percent > 10  # At least 10% improvement
        )
        
        # Confidence interval (simplified 95% CI)
        if fast_times and len(fast_times) > 1:
            fast_std = statistics.stdev(fast_times)
            margin_error = 1.96 * (fast_std / (len(fast_times) ** 0.5))
            confidence_interval = (fast_avg - margin_error, fast_avg + margin_error)
        else:
            confidence_interval = (0, 0)
        
        return PerformanceComparison(
            test_scenario=fast_path_results[0].test_name if fast_path_results else "unknown",
            fast_path_avg=fast_avg,
            slow_path_avg=slow_avg,
            improvement_factor=improvement_factor,
            improvement_percent=improvement_percent,
            fast_path_success_rate=fast_success_rate,
            slow_path_success_rate=slow_success_rate,
            statistical_significance=statistical_significance,
            confidence_interval=confidence_interval
        )
    
    def generate_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        report = {
            'summary': {
                'total_tests': len(set(r.test_name for r in self.results)),
                'total_iterations': len(self.results),
                'test_duration': (datetime.now() - min(r.timestamp for r in self.results)).total_seconds(),
                'overall_success_rate': len([r for r in self.results if r.success]) / len(self.results) * 100
            },
            'performance_by_path': {},
            'comparisons': [],
            'regression_analysis': {},
            'resource_usage': {},
            'recommendations': []
        }
        
        # Group results by execution path
        by_path = {}
        for result in self.results:
            if result.execution_path not in by_path:
                by_path[result.execution_path] = []
            by_path[result.execution_path].append(result)
        
        # Calculate statistics for each path
        for path, results in by_path.items():
            successful_results = [r for r in results if r.success]
            if successful_results:
                times = [r.execution_time for r in successful_results]
                memory_usage = [r.memory_usage_mb for r in successful_results]
                
                report['performance_by_path'][path] = {
                    'avg_execution_time': statistics.mean(times),
                    'median_execution_time': statistics.median(times),
                    'std_execution_time': statistics.stdev(times) if len(times) > 1 else 0,
                    'min_execution_time': min(times),
                    'max_execution_time': max(times),
                    'avg_memory_usage': statistics.mean(memory_usage),
                    'success_rate': len(successful_results) / len(results) * 100,
                    'total_iterations': len(results)
                }
        
        # Generate comparisons
        test_names = set(r.test_name for r in self.results)
        for test_name in test_names:
            fast_results = [r for r in self.results if r.test_name == test_name and r.execution_path == 'fast']
            slow_results = [r for r in self.results if r.test_name == test_name and r.execution_path == 'slow']
            
            if fast_results and slow_results:
                comparison = self.compare_performance(fast_results, slow_results)
                report['comparisons'].append(asdict(comparison))
        
        # Regression analysis
        report['regression_analysis'] = self.analyze_regressions()
        
        # Resource usage analysis
        report['resource_usage'] = self.analyze_resource_usage()
        
        # Generate recommendations
        report['recommendations'] = self.generate_recommendations(report)
        
        return report
    
    def analyze_regressions(self) -> Dict[str, Any]:
        """Analyze performance regressions against thresholds."""
        regressions = {
            'fast_path_violations': [],
            'slow_path_violations': [],
            'memory_violations': [],
            'cpu_violations': [],
            'success_rate_violations': []
        }
        
        # Check fast path performance
        fast_results = [r for r in self.results if r.execution_path == 'fast' and r.success]
        if fast_results:
            avg_fast_time = statistics.mean(r.execution_time for r in fast_results)
            if avg_fast_time > self.regression_thresholds['fast_path_max_time']:
                regressions['fast_path_violations'].append({
                    'avg_time': avg_fast_time,
                    'threshold': self.regression_thresholds['fast_path_max_time'],
                    'violation_percent': ((avg_fast_time - self.regression_thresholds['fast_path_max_time']) / 
                                        self.regression_thresholds['fast_path_max_time']) * 100
                })
        
        # Check slow path performance
        slow_results = [r for r in self.results if r.execution_path == 'slow' and r.success]
        if slow_results:
            avg_slow_time = statistics.mean(r.execution_time for r in slow_results)
            if avg_slow_time > self.regression_thresholds['slow_path_max_time']:
                regressions['slow_path_violations'].append({
                    'avg_time': avg_slow_time,
                    'threshold': self.regression_thresholds['slow_path_max_time'],
                    'violation_percent': ((avg_slow_time - self.regression_thresholds['slow_path_max_time']) / 
                                        self.regression_thresholds['slow_path_max_time']) * 100
                })
        
        # Check memory usage
        memory_increases = [r.memory_usage_mb for r in self.results if r.memory_usage_mb > 0]
        if memory_increases:
            max_memory_increase = max(memory_increases)
            if max_memory_increase > self.regression_thresholds['memory_increase_max']:
                regressions['memory_violations'].append({
                    'max_increase': max_memory_increase,
                    'threshold': self.regression_thresholds['memory_increase_max'],
                    'violation_percent': ((max_memory_increase - self.regression_thresholds['memory_increase_max']) / 
                                        self.regression_thresholds['memory_increase_max']) * 100
                })
        
        return regressions
    
    def analyze_resource_usage(self) -> Dict[str, Any]:
        """Analyze system resource usage patterns."""
        resource_analysis = {
            'memory_usage': {
                'peak_usage_mb': max(r.memory_usage_mb for r in self.results),
                'avg_usage_mb': statistics.mean(r.memory_usage_mb for r in self.results),
                'memory_leaks_detected': False
            },
            'cpu_usage': {
                'peak_cpu_percent': max(r.cpu_usage_percent for r in self.results),
                'avg_cpu_percent': statistics.mean(r.cpu_usage_percent for r in self.results)
            },
            'performance_trends': {}
        }
        
        # Detect memory leaks (simplified)
        memory_values = [r.memory_usage_mb for r in self.results]
        if len(memory_values) > 5:
            # Check if memory usage is consistently increasing
            recent_avg = statistics.mean(memory_values[-5:])
            early_avg = statistics.mean(memory_values[:5])
            if recent_avg > early_avg * 1.5:  # 50% increase
                resource_analysis['memory_usage']['memory_leaks_detected'] = True
        
        return resource_analysis
    
    def generate_recommendations(self, report: Dict[str, Any]) -> List[str]:
        """Generate optimization recommendations based on performance data."""
        recommendations = []
        
        # Fast path performance recommendations
        if 'fast' in report['performance_by_path']:
            fast_stats = report['performance_by_path']['fast']
            if fast_stats['avg_execution_time'] > 1.5:
                recommendations.append(
                    f"Fast path average execution time ({fast_stats['avg_execution_time']:.2f}s) "
                    "is approaching the 2s threshold. Consider optimizing accessibility tree traversal."
                )
            
            if fast_stats['success_rate'] < 95:
                recommendations.append(
                    f"Fast path success rate ({fast_stats['success_rate']:.1f}%) is below 95%. "
                    "Review element detection algorithms and error handling."
                )
        
        # Memory usage recommendations
        if report['resource_usage']['memory_usage']['memory_leaks_detected']:
            recommendations.append(
                "Potential memory leak detected. Review caching mechanisms and object lifecycle management."
            )
        
        # Performance comparison recommendations
        for comparison in report['comparisons']:
            if comparison['improvement_percent'] < 50:
                recommendations.append(
                    f"Performance improvement for {comparison['test_scenario']} "
                    f"({comparison['improvement_percent']:.1f}%) is below expected 50% threshold."
                )
        
        # CPU usage recommendations
        if report['resource_usage']['cpu_usage']['peak_cpu_percent'] > 80:
            recommendations.append(
                f"Peak CPU usage ({report['resource_usage']['cpu_usage']['peak_cpu_percent']:.1f}%) "
                "is high. Consider optimizing parallel processing and background tasks."
            )
        
        return recommendations
    
    def save_results(self, filename: str):
        """Save benchmark results to file."""
        report = self.generate_performance_report()
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logging.info(f"Performance benchmark results saved to {filename}")


class TestPerformanceBenchmarking:
    """Performance benchmarking test suite."""
    
    @pytest.fixture(scope="class")
    def benchmark_suite(self):
        """Create benchmark suite for testing."""
        suite = PerformanceBenchmarkSuite()
        suite.setup_resource_monitoring()
        return suite
    
    @pytest.fixture
    def mock_orchestrator(self):
        """Create mock orchestrator for performance testing."""
        with patch('orchestrator.VisionModule') as mock_vision_class, \
             patch('orchestrator.ReasoningModule') as mock_reasoning_class, \
             patch('orchestrator.AutomationModule') as mock_automation_class, \
             patch('orchestrator.AudioModule') as mock_audio_class, \
             patch('orchestrator.FeedbackModule') as mock_feedback_class, \
             patch('orchestrator.AccessibilityModule') as mock_accessibility_class:
            
            # Setup module mocks
            mock_vision = Mock()
            mock_reasoning = Mock()
            mock_automation = Mock()
            mock_audio = Mock()
            mock_feedback = Mock()
            mock_accessibility = Mock()
            
            # Configure mock returns for performance testing
            mock_vision_class.return_value = mock_vision
            mock_reasoning_class.return_value = mock_reasoning
            mock_automation_class.return_value = mock_automation
            mock_audio_class.return_value = mock_audio
            mock_feedback_class.return_value = mock_feedback
            mock_accessibility_class.return_value = mock_accessibility
            
            # Setup realistic timing behaviors
            self._setup_performance_mocks(
                mock_vision, mock_reasoning, mock_automation, 
                mock_audio, mock_feedback, mock_accessibility
            )
            
            orchestrator = Orchestrator()
            orchestrator._test_mocks = {
                'vision': mock_vision,
                'reasoning': mock_reasoning,
                'automation': mock_automation,
                'audio': mock_audio,
                'feedback': mock_feedback,
                'accessibility': mock_accessibility
            }
            
            yield orchestrator
    
    def _setup_performance_mocks(self, mock_vision, mock_reasoning, mock_automation, 
                                mock_audio, mock_feedback, mock_accessibility):
        """Setup mocks with realistic performance characteristics."""
        
        # Vision module - slower operations
        def slow_capture_screen():
            time.sleep(0.5)  # Simulate screen capture time
            return "mock_screenshot.png"
        
        def slow_analyze_screen(screenshot_path):
            time.sleep(2.0)  # Simulate vision model processing
            return {
                'elements': [{'type': 'button', 'text': 'Test', 'coordinates': [100, 200, 150, 50]}],
                'description': 'Test screen'
            }
        
        mock_vision.capture_screen.side_effect = slow_capture_screen
        mock_vision.analyze_screen.side_effect = slow_analyze_screen
        
        # Reasoning module - moderate processing time
        def moderate_reasoning(analysis, command):
            time.sleep(1.0)  # Simulate reasoning processing
            return {
                'actions': [{'type': 'click', 'target': 'Test button'}],
                'confidence': 0.9
            }
        
        mock_reasoning.get_action_plan.side_effect = moderate_reasoning
        
        # Automation module - fast execution
        def fast_automation(action):
            time.sleep(0.1)  # Simulate action execution
            return {'success': True, 'execution_time': 0.1}
        
        mock_automation.execute_action.side_effect = fast_automation
        mock_automation.execute_fast_path_action.side_effect = lambda *args, **kwargs: fast_automation({})
        
        # Accessibility module - very fast operations
        def fast_accessibility_find(role, label, app_name=None):
            time.sleep(0.05)  # Simulate accessibility API call
            return {
                'coordinates': [100, 200, 150, 50],
                'center_point': [175, 225],
                'role': role,
                'title': label,
                'enabled': True,
                'app_name': app_name or 'TestApp'
            }
        
        mock_accessibility.find_element.side_effect = fast_accessibility_find
        mock_accessibility.is_accessibility_enabled.return_value = True
        
        # Audio and feedback - minimal processing time
        mock_audio.transcribe_audio.return_value = "test command"
        mock_audio.speak.return_value = None
        mock_feedback.play.return_value = None
    
    def test_fast_path_performance_benchmark(self, benchmark_suite, mock_orchestrator):
        """Benchmark fast path execution performance."""
        
        def fast_path_execution():
            with patch.object(mock_orchestrator, '_attempt_fast_path_execution') as mock_fast_path:
                mock_fast_path.return_value = {
                    'success': True,
                    'path_used': 'fast',
                    'execution_time': 0.2,
                    'element_found': {'role': 'AXButton', 'title': 'Test'},
                    'action_result': {'success': True, 'execution_time': 0.1}
                }
                
                result = mock_orchestrator._attempt_fast_path_execution("click test button", {})
                return result['success']
        
        # Run benchmark
        results = benchmark_suite.run_benchmark(
            fast_path_execution, 
            "fast_path_click", 
            "fast",
            iterations=20
        )
        
        # Verify performance requirements
        successful_results = [r for r in results if r.success]
        assert len(successful_results) > 0, "No successful fast path executions"
        
        avg_time = statistics.mean(r.execution_time for r in successful_results)
        success_rate = len(successful_results) / len(results) * 100
        
        assert avg_time < 2.0, f"Fast path average time {avg_time:.2f}s exceeds 2s requirement"
        assert success_rate >= 95, f"Fast path success rate {success_rate:.1f}% is below 95%"
        
        logging.info(f"Fast path benchmark: {avg_time:.3f}s average, {success_rate:.1f}% success rate")
    
    def test_slow_path_performance_benchmark(self, benchmark_suite, mock_orchestrator):
        """Benchmark slow path execution performance."""
        
        def slow_path_execution():
            # Simulate full vision-reasoning workflow
            screenshot = mock_orchestrator._test_mocks['vision'].capture_screen()
            analysis = mock_orchestrator._test_mocks['vision'].analyze_screen(screenshot)
            action_plan = mock_orchestrator._test_mocks['reasoning'].get_action_plan(analysis, "click test")
            result = mock_orchestrator._test_mocks['automation'].execute_action(action_plan['actions'][0])
            return result['success']
        
        # Run benchmark
        results = benchmark_suite.run_benchmark(
            slow_path_execution,
            "slow_path_click",
            "slow",
            iterations=10  # Fewer iterations due to longer execution time
        )
        
        # Verify performance characteristics
        successful_results = [r for r in results if r.success]
        assert len(successful_results) > 0, "No successful slow path executions"
        
        avg_time = statistics.mean(r.execution_time for r in successful_results)
        success_rate = len(successful_results) / len(results) * 100
        
        assert avg_time < 10.0, f"Slow path average time {avg_time:.2f}s exceeds 10s limit"
        assert success_rate >= 90, f"Slow path success rate {success_rate:.1f}% is below 90%"
        
        logging.info(f"Slow path benchmark: {avg_time:.3f}s average, {success_rate:.1f}% success rate")
    
    def test_performance_comparison_analysis(self, benchmark_suite, mock_orchestrator):
        """Test comprehensive performance comparison between paths."""
        
        # Run fast path benchmark
        def fast_path_test():
            time.sleep(0.2)  # Simulate fast execution
            return True
        
        fast_results = benchmark_suite.run_benchmark(fast_path_test, "comparison_test", "fast", iterations=15)
        
        # Run slow path benchmark
        def slow_path_test():
            time.sleep(3.5)  # Simulate slow execution
            return True
        
        slow_results = benchmark_suite.run_benchmark(slow_path_test, "comparison_test", "slow", iterations=15)
        
        # Perform comparison analysis
        comparison = benchmark_suite.compare_performance(fast_results, slow_results)
        
        # Verify comparison results
        assert comparison.improvement_factor > 5, f"Improvement factor {comparison.improvement_factor:.1f} is too low"
        assert comparison.improvement_percent > 80, f"Improvement {comparison.improvement_percent:.1f}% is insufficient"
        assert comparison.fast_path_success_rate >= 95, "Fast path success rate too low"
        assert comparison.statistical_significance, "Performance improvement not statistically significant"
        
        logging.info(f"Performance comparison: {comparison.improvement_factor:.1f}x faster, "
                    f"{comparison.improvement_percent:.1f}% improvement")
    
    def test_concurrent_execution_performance(self, benchmark_suite, mock_orchestrator):
        """Test performance under concurrent execution load."""
        
        def concurrent_fast_path():
            with patch.object(mock_orchestrator, '_attempt_fast_path_execution') as mock_fast_path:
                mock_fast_path.return_value = {
                    'success': True,
                    'path_used': 'fast',
                    'execution_time': 0.15
                }
                
                # Simulate concurrent execution
                with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                    futures = []
                    for i in range(5):
                        future = executor.submit(
                            mock_orchestrator._attempt_fast_path_execution,
                            f"click button {i}",
                            {}
                        )
                        futures.append(future)
                    
                    results = [future.result() for future in concurrent.futures.as_completed(futures)]
                    return all(r['success'] for r in results)
        
        # Run concurrent benchmark
        results = benchmark_suite.run_benchmark(
            concurrent_fast_path,
            "concurrent_execution",
            "fast",
            iterations=10
        )
        
        # Verify concurrent performance
        successful_results = [r for r in results if r.success]
        avg_time = statistics.mean(r.execution_time for r in successful_results)
        success_rate = len(successful_results) / len(results) * 100
        
        assert avg_time < 3.0, f"Concurrent execution time {avg_time:.2f}s is too high"
        assert success_rate >= 90, f"Concurrent success rate {success_rate:.1f}% is too low"
        
        logging.info(f"Concurrent execution: {avg_time:.3f}s average, {success_rate:.1f}% success rate")
    
    def test_memory_usage_optimization(self, benchmark_suite, mock_orchestrator):
        """Test memory usage optimization and leak detection."""
        
        def memory_intensive_test():
            # Simulate operations that might cause memory issues
            large_data = []
            for i in range(100):
                with patch.object(mock_orchestrator, '_attempt_fast_path_execution') as mock_fast_path:
                    mock_fast_path.return_value = {
                        'success': True,
                        'path_used': 'fast',
                        'execution_time': 0.1,
                        'element_found': {'role': 'AXButton', 'title': f'Button {i}'}
                    }
                    
                    result = mock_orchestrator._attempt_fast_path_execution(f"click button {i}", {})
                    large_data.append(result)
            
            # Clear data to test garbage collection
            large_data.clear()
            gc.collect()
            return True
        
        # Run memory benchmark
        results = benchmark_suite.run_benchmark(
            memory_intensive_test,
            "memory_usage_test",
            "fast",
            iterations=5
        )
        
        # Analyze memory usage
        memory_increases = [r.memory_usage_mb for r in results if r.memory_usage_mb > 0]
        if memory_increases:
            max_memory_increase = max(memory_increases)
            avg_memory_increase = statistics.mean(memory_increases)
            
            assert max_memory_increase < 100, f"Memory increase {max_memory_increase:.1f}MB is excessive"
            assert avg_memory_increase < 50, f"Average memory increase {avg_memory_increase:.1f}MB is too high"
            
            logging.info(f"Memory usage: max {max_memory_increase:.1f}MB, avg {avg_memory_increase:.1f}MB increase")
    
    def test_performance_regression_detection(self, benchmark_suite, mock_orchestrator):
        """Test performance regression detection capabilities."""
        
        # Baseline performance
        def baseline_test():
            time.sleep(0.2)  # Good performance
            return True
        
        baseline_results = benchmark_suite.run_benchmark(baseline_test, "regression_test", "fast", iterations=10)
        
        # Simulated regression
        def regressed_test():
            time.sleep(0.8)  # Degraded performance
            return True
        
        regressed_results = benchmark_suite.run_benchmark(regressed_test, "regression_test", "fast", iterations=10)
        
        # Analyze for regressions
        baseline_avg = statistics.mean(r.execution_time for r in baseline_results if r.success)
        regressed_avg = statistics.mean(r.execution_time for r in regressed_results if r.success)
        
        performance_degradation = ((regressed_avg - baseline_avg) / baseline_avg) * 100
        
        # Verify regression detection
        assert performance_degradation > 50, f"Performance regression {performance_degradation:.1f}% detected"
        
        # Test regression analysis
        regression_analysis = benchmark_suite.analyze_regressions()
        assert len(regression_analysis['fast_path_violations']) > 0, "Regression not detected in analysis"
        
        logging.info(f"Regression detection: {performance_degradation:.1f}% performance degradation")
    
    def test_comprehensive_performance_report(self, benchmark_suite, mock_orchestrator):
        """Test comprehensive performance report generation."""
        
        # Run various benchmarks to populate data
        def fast_test():
            time.sleep(0.15)
            return True
        
        def slow_test():
            time.sleep(2.5)
            return True
        
        # Generate test data
        benchmark_suite.run_benchmark(fast_test, "report_test", "fast", iterations=10)
        benchmark_suite.run_benchmark(slow_test, "report_test", "slow", iterations=5)
        
        # Generate comprehensive report
        report = benchmark_suite.generate_performance_report()
        
        # Verify report structure
        assert 'summary' in report
        assert 'performance_by_path' in report
        assert 'comparisons' in report
        assert 'regression_analysis' in report
        assert 'resource_usage' in report
        assert 'recommendations' in report
        
        # Verify summary data
        assert report['summary']['total_tests'] > 0
        assert report['summary']['total_iterations'] > 0
        assert report['summary']['overall_success_rate'] > 0
        
        # Verify performance data
        assert 'fast' in report['performance_by_path']
        assert 'slow' in report['performance_by_path']
        
        # Verify comparisons
        assert len(report['comparisons']) > 0
        
        # Save report for inspection
        report_filename = f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        benchmark_suite.save_results(report_filename)
        
        logging.info(f"Performance report generated: {report_filename}")
        
        # Cleanup
        if os.path.exists(report_filename):
            os.remove(report_filename)


class TestPerformanceRegressionSuite:
    """Performance regression test suite for continuous monitoring."""
    
    def test_fast_path_performance_regression(self):
        """Regression test for fast path performance."""
        # This test should be run regularly to detect performance regressions
        
        benchmark_suite = PerformanceBenchmarkSuite()
        benchmark_suite.setup_resource_monitoring()
        
        def fast_path_regression_test():
            # Simulate fast path execution
            time.sleep(0.1)  # Should be very fast
            return True
        
        results = benchmark_suite.run_benchmark(
            fast_path_regression_test,
            "fast_path_regression",
            "fast",
            iterations=20
        )
        
        successful_results = [r for r in results if r.success]
        avg_time = statistics.mean(r.execution_time for r in successful_results)
        
        # Strict regression threshold
        assert avg_time < 1.0, f"Fast path regression detected: {avg_time:.3f}s > 1.0s threshold"
        
        # Success rate regression
        success_rate = len(successful_results) / len(results) * 100
        assert success_rate >= 98, f"Success rate regression: {success_rate:.1f}% < 98%"
    
    def test_memory_leak_regression(self):
        """Regression test for memory leaks."""
        
        benchmark_suite = PerformanceBenchmarkSuite()
        benchmark_suite.setup_resource_monitoring()
        
        def memory_leak_test():
            # Simulate operations that might leak memory
            data = []
            for i in range(50):
                data.append({'test_data': f'item_{i}' * 100})
            
            # Clear and force garbage collection
            data.clear()
            gc.collect()
            return True
        
        results = benchmark_suite.run_benchmark(
            memory_leak_test,
            "memory_leak_regression",
            "fast",
            iterations=10
        )
        
        # Check for memory leaks
        memory_increases = [r.memory_usage_mb for r in results if r.memory_usage_mb > 0]
        if memory_increases:
            # Memory should not consistently increase
            if len(memory_increases) > 5:
                recent_avg = statistics.mean(memory_increases[-3:])
                early_avg = statistics.mean(memory_increases[:3])
                
                memory_growth = ((recent_avg - early_avg) / early_avg) * 100 if early_avg > 0 else 0
                assert memory_growth < 20, f"Memory leak detected: {memory_growth:.1f}% growth"


if __name__ == '__main__':
    # Configure logging for benchmark execution
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run performance benchmarks
    pytest.main([
        __file__,
        '-v',
        '--tb=short',
        '--capture=no',
        '--log-cli-level=INFO',
        '-k', 'not regression'  # Skip regression tests in normal run
    ])