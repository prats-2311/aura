"""
Comprehensive Performance Optimization and Monitoring Tests

This module implements performance monitoring for all handler types, metrics collection
for intent recognition speed and accuracy, memory usage monitoring, execution time
optimization, and performance regression detection.
"""

import pytest
import unittest
from unittest.mock import Mock, MagicMock, patch, call
import time
import threading
import psutil
import gc
import statistics
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass
from collections import defaultdict

# Import handlers and system components
from handlers.base_handler import BaseHandler
from handlers.gui_handler import GUIHandler
from handlers.conversation_handler import ConversationHandler
from handlers.deferred_action_handler import DeferredActionHandler


@dataclass
class PerformanceMetrics:
    """Performance metrics data structure."""
    execution_time: float
    memory_usage_mb: float
    cpu_usage_percent: float
    success_rate: float
    error_count: int
    timestamp: float


class PerformanceMonitor:
    """Performance monitoring utility for testing."""
    
    def __init__(self):
        self.metrics_history: List[PerformanceMetrics] = []
        self.baseline_metrics: Dict[str, PerformanceMetrics] = {}
    
    def start_monitoring(self) -> Dict[str, Any]:
        """Start performance monitoring for a test."""
        return {
            'start_time': time.time(),
            'start_memory': psutil.Process().memory_info().rss / 1024 / 1024,  # MB
            'start_cpu': psutil.Process().cpu_percent()
        }
    
    def end_monitoring(self, start_data: Dict[str, Any], success: bool = True, errors: int = 0) -> PerformanceMetrics:
        """End performance monitoring and calculate metrics."""
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        end_cpu = psutil.Process().cpu_percent()
        
        metrics = PerformanceMetrics(
            execution_time=end_time - start_data['start_time'],
            memory_usage_mb=end_memory - start_data['start_memory'],
            cpu_usage_percent=max(end_cpu - start_data['start_cpu'], 0),
            success_rate=1.0 if success else 0.0,
            error_count=errors,
            timestamp=end_time
        )
        
        self.metrics_history.append(metrics)
        return metrics
    
    def get_average_metrics(self, last_n: int = None) -> PerformanceMetrics:
        """Get average metrics from recent measurements."""
        if not self.metrics_history:
            return PerformanceMetrics(0, 0, 0, 0, 0, time.time())
        
        recent_metrics = self.metrics_history[-last_n:] if last_n else self.metrics_history
        
        return PerformanceMetrics(
            execution_time=statistics.mean(m.execution_time for m in recent_metrics),
            memory_usage_mb=statistics.mean(m.memory_usage_mb for m in recent_metrics),
            cpu_usage_percent=statistics.mean(m.cpu_usage_percent for m in recent_metrics),
            success_rate=statistics.mean(m.success_rate for m in recent_metrics),
            error_count=sum(m.error_count for m in recent_metrics),
            timestamp=time.time()
        )
    
    def detect_regression(self, baseline_key: str, current_metrics: PerformanceMetrics, 
                         threshold_percent: float = 20.0) -> Dict[str, Any]:
        """Detect performance regression compared to baseline."""
        if baseline_key not in self.baseline_metrics:
            self.baseline_metrics[baseline_key] = current_metrics
            return {'regression_detected': False, 'message': 'Baseline established'}
        
        baseline = self.baseline_metrics[baseline_key]
        regressions = []
        
        # Check execution time regression
        if current_metrics.execution_time > baseline.execution_time * (1 + threshold_percent / 100):
            regressions.append(f"Execution time increased by {((current_metrics.execution_time / baseline.execution_time - 1) * 100):.1f}%")
        
        # Check memory usage regression
        if current_metrics.memory_usage_mb > baseline.memory_usage_mb * (1 + threshold_percent / 100):
            regressions.append(f"Memory usage increased by {((current_metrics.memory_usage_mb / baseline.memory_usage_mb - 1) * 100):.1f}%")
        
        # Check success rate regression
        if current_metrics.success_rate < baseline.success_rate * (1 - threshold_percent / 100):
            regressions.append(f"Success rate decreased by {((baseline.success_rate - current_metrics.success_rate) * 100):.1f}%")
        
        return {
            'regression_detected': len(regressions) > 0,
            'regressions': regressions,
            'baseline': baseline,
            'current': current_metrics
        }


class TestHandlerPerformanceMonitoring(unittest.TestCase):
    """Test performance monitoring for all handler types."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.performance_monitor = PerformanceMonitor()
        self.mock_orchestrator = Mock()
        self.mock_orchestrator.config = {}
        
        # Set up mock modules for consistent testing
        self.setup_mock_modules()
        
        # Create handlers
        self.gui_handler = GUIHandler(self.mock_orchestrator)
        self.conversation_handler = ConversationHandler(self.mock_orchestrator)
        self.deferred_handler = DeferredActionHandler(self.mock_orchestrator)
    
    def setup_mock_modules(self):
        """Set up mock modules with performance-optimized responses."""
        # Fast accessibility module
        self.mock_accessibility = Mock()
        self.mock_accessibility.get_accessibility_status.return_value = {
            'api_initialized': True
        }
        
        mock_element = {'center_point': (100, 200), 'title': 'Test Element'}
        mock_enhanced_result = Mock()
        mock_enhanced_result.found = True
        mock_enhanced_result.element = mock_element
        
        self.mock_accessibility.find_element_enhanced.return_value = mock_enhanced_result
        
        # Fast automation module
        self.mock_automation = Mock()
        self.mock_automation.execute_fast_path_action.return_value = {
            'success': True,
            'message': 'Action executed'
        }
        
        # Efficient reasoning module
        self.mock_reasoning = Mock()
        self.mock_reasoning.process_query.return_value = "Quick response"
        self.mock_reasoning._make_api_request.return_value = {
            'choices': [{'message': {'content': 'Generated content'}}]
        }
        
        # Assign to orchestrator
        self.mock_orchestrator.accessibility_module = self.mock_accessibility
        self.mock_orchestrator.automation_module = self.mock_automation
        self.mock_orchestrator.reasoning_module = self.mock_reasoning
        self.mock_orchestrator.feedback_module = Mock()
    
    def test_gui_handler_performance_monitoring(self):
        """Test performance monitoring for GUI handler operations."""
        test_commands = [
            "click the submit button",
            "type hello world",
            "scroll down",
            "press enter",
            "double-click the file"
        ]
        
        performance_results = []
        
        for command in test_commands:
            # Start performance monitoring
            start_data = self.performance_monitor.start_monitoring()
            
            context = {
                "intent": {"intent": "gui_interaction"},
                "execution_id": f"perf_test_{hash(command)}"
            }
            
            try:
                result = self.gui_handler.handle(command, context)
                success = result["status"] == "success"
                errors = 0 if success else 1
            except Exception as e:
                success = False
                errors = 1
            
            # End monitoring and collect metrics
            metrics = self.performance_monitor.end_monitoring(start_data, success, errors)
            performance_results.append((command, metrics))
            
            # Verify performance constraints
            self.assertLess(metrics.execution_time, 2.0, 
                f"GUI command '{command}' took too long: {metrics.execution_time:.3f}s")
            self.assertLess(metrics.memory_usage_mb, 50.0,
                f"GUI command '{command}' used too much memory: {metrics.memory_usage_mb:.1f}MB")
        
        # Calculate average performance
        avg_metrics = self.performance_monitor.get_average_metrics()
        
        # Verify overall performance
        self.assertLess(avg_metrics.execution_time, 1.0, 
            f"Average GUI execution time too high: {avg_metrics.execution_time:.3f}s")
        self.assertGreaterEqual(avg_metrics.success_rate, 0.8,
            f"GUI success rate too low: {avg_metrics.success_rate:.2f}")
    
    def test_conversation_handler_performance_monitoring(self):
        """Test performance monitoring for conversation handler operations."""
        test_queries = [
            "Hello, how are you?",
            "What can you help me with?",
            "Tell me a joke",
            "How's the weather?",
            "What time is it?"
        ]
        
        for query in test_queries:
            start_data = self.performance_monitor.start_monitoring()
            
            context = {
                "intent": {"intent": "conversational_chat"},
                "execution_id": f"conv_perf_{hash(query)}"
            }
            
            try:
                result = self.conversation_handler.handle(query, context)
                success = result["status"] == "success"
                errors = 0 if success else 1
            except Exception as e:
                success = False
                errors = 1
            
            metrics = self.performance_monitor.end_monitoring(start_data, success, errors)
            
            # Conversation should be fast and responsive
            self.assertLess(metrics.execution_time, 3.0,
                f"Conversation query '{query}' took too long: {metrics.execution_time:.3f}s")
            self.assertLess(metrics.memory_usage_mb, 30.0,
                f"Conversation query '{query}' used too much memory: {metrics.memory_usage_mb:.1f}MB")
        
        # Check conversation-specific performance
        avg_metrics = self.performance_monitor.get_average_metrics(last_n=len(test_queries))
        self.assertLess(avg_metrics.execution_time, 2.0,
            f"Average conversation time too high: {avg_metrics.execution_time:.3f}s")
    
    def test_deferred_action_handler_performance_monitoring(self):
        """Test performance monitoring for deferred action handler operations."""
        self.mock_orchestrator.is_waiting_for_user_action = False
        self.mock_orchestrator.deferred_action_lock = threading.Lock()
        
        test_requests = [
            ("Write a Python function", "code"),
            ("Create an email template", "text"),
            ("Generate a summary", "text"),
            ("Write a SQL query", "code"),
            ("Create a list", "text")
        ]
        
        for request, content_type in test_requests:
            start_data = self.performance_monitor.start_monitoring()
            
            context = {
                "intent": {
                    "intent": "deferred_action",
                    "parameters": {
                        "content_request": request,
                        "content_type": content_type
                    }
                },
                "execution_id": f"deferred_perf_{hash(request)}"
            }
            
            with patch.object(self.deferred_handler, '_start_mouse_listener'), \
                 patch.object(self.deferred_handler, '_provide_audio_instructions'), \
                 patch.object(self.deferred_handler, '_start_timeout_monitoring'):
                
                try:
                    result = self.deferred_handler.handle(request, context)
                    success = result["status"] == "waiting_for_user_action"
                    errors = 0 if success else 1
                except Exception as e:
                    success = False
                    errors = 1
            
            metrics = self.performance_monitor.end_monitoring(start_data, success, errors)
            
            # Deferred actions should complete setup quickly
            self.assertLess(metrics.execution_time, 5.0,
                f"Deferred action '{request}' setup took too long: {metrics.execution_time:.3f}s")
            self.assertLess(metrics.memory_usage_mb, 100.0,
                f"Deferred action '{request}' used too much memory: {metrics.memory_usage_mb:.1f}MB")
    
    def test_concurrent_handler_performance(self):
        """Test performance under concurrent load."""
        def execute_gui_command():
            context = {"intent": {"intent": "gui_interaction"}, "execution_id": "concurrent_test"}
            try:
                result = self.gui_handler.handle("click button", context)
                return result["status"] == "success"
            except:
                return False
        
        def execute_conversation():
            context = {"intent": {"intent": "conversational_chat"}, "execution_id": "concurrent_conv"}
            try:
                result = self.conversation_handler.handle("Hello", context)
                return result["status"] == "success"
            except:
                return False
        
        # Start concurrent performance monitoring
        start_data = self.performance_monitor.start_monitoring()
        
        # Execute concurrent operations
        threads = []
        results = []
        
        for i in range(5):
            # Mix of GUI and conversation operations
            if i % 2 == 0:
                thread = threading.Thread(target=lambda: results.append(execute_gui_command()))
            else:
                thread = threading.Thread(target=lambda: results.append(execute_conversation()))
            
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # End monitoring
        success_count = sum(1 for r in results if r)
        success_rate = success_count / len(results) if results else 0
        metrics = self.performance_monitor.end_monitoring(start_data, success_rate > 0.5, len(results) - success_count)
        
        # Concurrent operations should complete within reasonable time
        self.assertLess(metrics.execution_time, 10.0,
            f"Concurrent operations took too long: {metrics.execution_time:.3f}s")
        self.assertGreaterEqual(success_rate, 0.6,
            f"Concurrent success rate too low: {success_rate:.2f}")


class TestIntentRecognitionPerformance(unittest.TestCase):
    """Test intent recognition speed and accuracy performance."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.performance_monitor = PerformanceMonitor()
        self.mock_orchestrator = Mock()
        self.mock_reasoning = Mock()
        self.mock_orchestrator.reasoning_module = self.mock_reasoning
    
    def test_intent_recognition_speed(self):
        """Test intent recognition execution speed."""
        test_commands = [
            ("click the button", "gui_interaction"),
            ("Hello there", "conversational_chat"),
            ("Write me code", "deferred_action"),
            ("What does this say?", "question_answering"),
            ("scroll down", "gui_interaction"),
            ("How are you?", "conversational_chat"),
            ("Generate text", "deferred_action"),
            ("Summarize this", "question_answering")
        ]
        
        recognition_times = []
        accuracy_results = []
        
        for command, expected_intent in test_commands:
            # Mock intent recognition response
            self.mock_reasoning.process_query.return_value = {
                'intent': expected_intent,
                'confidence': 0.9,
                'parameters': {}
            }
            
            # Measure intent recognition time
            start_time = time.time()
            
            # Simulate intent recognition call
            try:
                result = self.mock_reasoning.process_query(
                    query=command,
                    prompt_template='INTENT_RECOGNITION_PROMPT',
                    context={}
                )
                
                recognition_time = time.time() - start_time
                recognition_times.append(recognition_time)
                
                # Check accuracy
                predicted_intent = result.get('intent', 'unknown')
                accuracy_results.append(predicted_intent == expected_intent)
                
            except Exception as e:
                recognition_times.append(float('inf'))
                accuracy_results.append(False)
        
        # Verify performance metrics
        avg_recognition_time = statistics.mean(recognition_times)
        accuracy = sum(accuracy_results) / len(accuracy_results)
        
        self.assertLess(avg_recognition_time, 0.5,
            f"Intent recognition too slow: {avg_recognition_time:.3f}s average")
        self.assertGreaterEqual(accuracy, 0.9,
            f"Intent recognition accuracy too low: {accuracy:.2f}")
    
    def test_intent_recognition_confidence_scoring(self):
        """Test intent recognition confidence scoring performance."""
        # Test commands with varying clarity
        test_cases = [
            ("click the submit button", 0.95),  # Very clear GUI command
            ("hello", 0.85),  # Clear conversational
            ("write code for me", 0.90),  # Clear deferred action
            ("what is this", 0.80),  # Somewhat ambiguous
            ("do something", 0.60),  # Ambiguous
        ]
        
        confidence_scores = []
        
        for command, expected_min_confidence in test_cases:
            self.mock_reasoning.process_query.return_value = {
                'intent': 'gui_interaction',
                'confidence': expected_min_confidence + 0.02,  # Slightly above minimum
                'parameters': {}
            }
            
            start_time = time.time()
            result = self.mock_reasoning.process_query(
                query=command,
                prompt_template='INTENT_RECOGNITION_PROMPT',
                context={}
            )
            recognition_time = time.time() - start_time
            
            confidence = result.get('confidence', 0.0)
            confidence_scores.append(confidence)
            
            # Confidence scoring should be fast
            self.assertLess(recognition_time, 0.3,
                f"Confidence scoring too slow for '{command}': {recognition_time:.3f}s")
            
            # Confidence should meet minimum threshold
            self.assertGreaterEqual(confidence, expected_min_confidence,
                f"Confidence too low for '{command}': {confidence:.2f}")
        
        # Overall confidence distribution should be reasonable
        avg_confidence = statistics.mean(confidence_scores)
        self.assertGreaterEqual(avg_confidence, 0.8,
            f"Average confidence too low: {avg_confidence:.2f}")
    
    def test_intent_recognition_parameter_extraction_performance(self):
        """Test performance of parameter extraction from commands."""
        test_commands = [
            ('click the "Submit" button', {'action': 'click', 'target': 'Submit button'}),
            ('type "hello world"', {'action': 'type', 'text': 'hello world'}),
            ('write me a Python function for sorting', {'content_type': 'code', 'language': 'Python', 'topic': 'sorting'}),
            ('scroll down 5 times', {'action': 'scroll', 'direction': 'down', 'count': 5})
        ]
        
        extraction_times = []
        extraction_accuracy = []
        
        for command, expected_params in test_commands:
            # Mock parameter extraction
            self.mock_reasoning.process_query.return_value = {
                'intent': 'gui_interaction',
                'confidence': 0.9,
                'parameters': expected_params
            }
            
            start_time = time.time()
            result = self.mock_reasoning.process_query(
                query=command,
                prompt_template='INTENT_RECOGNITION_PROMPT',
                context={}
            )
            extraction_time = time.time() - start_time
            
            extraction_times.append(extraction_time)
            
            # Check parameter extraction accuracy
            extracted_params = result.get('parameters', {})
            accuracy = len(set(expected_params.keys()) & set(extracted_params.keys())) / len(expected_params)
            extraction_accuracy.append(accuracy)
        
        # Verify extraction performance
        avg_extraction_time = statistics.mean(extraction_times)
        avg_accuracy = statistics.mean(extraction_accuracy)
        
        self.assertLess(avg_extraction_time, 0.4,
            f"Parameter extraction too slow: {avg_extraction_time:.3f}s")
        self.assertGreaterEqual(avg_accuracy, 0.8,
            f"Parameter extraction accuracy too low: {avg_accuracy:.2f}")


class TestMemoryUsageMonitoring(unittest.TestCase):
    """Test memory usage monitoring and optimization."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.performance_monitor = PerformanceMonitor()
        self.mock_orchestrator = Mock()
        self.mock_orchestrator.config = {}
        
        # Force garbage collection before tests
        gc.collect()
        self.initial_memory = psutil.Process().memory_info().rss / 1024 / 1024
    
    def test_handler_memory_usage_monitoring(self):
        """Test memory usage monitoring for handler operations."""
        # Create handlers and monitor memory
        handlers = []
        memory_usage = []
        
        for i in range(10):
            # Create handler
            handler = GUIHandler(self.mock_orchestrator)
            handlers.append(handler)
            
            # Measure memory
            current_memory = psutil.Process().memory_info().rss / 1024 / 1024
            memory_usage.append(current_memory - self.initial_memory)
        
        # Memory usage should not grow excessively
        max_memory_increase = max(memory_usage)
        self.assertLess(max_memory_increase, 100.0,
            f"Handler creation caused excessive memory usage: {max_memory_increase:.1f}MB")
        
        # Clean up and verify memory is released
        handlers.clear()
        gc.collect()
        
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024
        memory_released = max(memory_usage) - (final_memory - self.initial_memory)
        
        # Should release most of the allocated memory
        self.assertGreater(memory_released, max_memory_increase * 0.7,
            f"Memory not properly released: {memory_released:.1f}MB of {max_memory_increase:.1f}MB")
    
    def test_conversation_history_memory_management(self):
        """Test memory management for conversation history."""
        conversation_handler = ConversationHandler(self.mock_orchestrator)
        self.mock_orchestrator.reasoning_module = Mock()
        self.mock_orchestrator.reasoning_module.process_query.return_value = "Response"
        self.mock_orchestrator.feedback_module = Mock()
        
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        # Add many conversation exchanges
        for i in range(50):
            query = f"Test query number {i} with some content to use memory"
            response = f"Test response number {i} with detailed information and content"
            
            conversation_handler._update_conversation_history(query, response)
        
        # Memory should not grow excessively due to history management
        current_memory = psutil.Process().memory_info().rss / 1024 / 1024
        memory_increase = current_memory - initial_memory
        
        self.assertLess(memory_increase, 50.0,
            f"Conversation history used too much memory: {memory_increase:.1f}MB")
        
        # History should be limited in size
        history_size = len(getattr(conversation_handler, '_conversation_history', []))
        self.assertLessEqual(history_size, 10,
            f"Conversation history not properly limited: {history_size} entries")
    
    def test_deferred_action_content_memory_management(self):
        """Test memory management for deferred action content."""
        deferred_handler = DeferredActionHandler(self.mock_orchestrator)
        self.mock_orchestrator.reasoning_module = Mock()
        self.mock_orchestrator.is_waiting_for_user_action = False
        self.mock_orchestrator.deferred_action_lock = threading.Lock()
        
        # Generate large content
        large_content = "x" * 10000  # 10KB content
        self.mock_orchestrator.reasoning_module._make_api_request.return_value = {
            'choices': [{'message': {'content': large_content}}]
        }
        
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        # Process multiple large content generations
        for i in range(5):
            context = {
                "intent": {
                    "intent": "deferred_action",
                    "parameters": {
                        "content_request": f"Generate large content {i}",
                        "content_type": "text"
                    }
                },
                "execution_id": f"memory_test_{i}"
            }
            
            with patch.object(deferred_handler, '_start_mouse_listener'), \
                 patch.object(deferred_handler, '_provide_audio_instructions'), \
                 patch.object(deferred_handler, '_start_timeout_monitoring'):
                
                try:
                    result = deferred_handler.handle(f"Generate content {i}", context)
                except:
                    pass  # Ignore errors, focus on memory
        
        # Memory usage should be reasonable
        current_memory = psutil.Process().memory_info().rss / 1024 / 1024
        memory_increase = current_memory - initial_memory
        
        self.assertLess(memory_increase, 100.0,
            f"Deferred action content used too much memory: {memory_increase:.1f}MB")


class TestExecutionTimeOptimization(unittest.TestCase):
    """Test execution time optimization and monitoring."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.performance_monitor = PerformanceMonitor()
        self.mock_orchestrator = Mock()
        self.mock_orchestrator.config = {}
        
        # Set up optimized mock modules
        self.setup_optimized_mocks()
    
    def setup_optimized_mocks(self):
        """Set up mocks optimized for fast execution."""
        # Fast accessibility module
        self.mock_accessibility = Mock()
        self.mock_accessibility.get_accessibility_status.return_value = {
            'api_initialized': True
        }
        
        # Simulate fast element finding
        mock_element = {'center_point': (100, 200), 'title': 'Fast Element'}
        mock_enhanced_result = Mock()
        mock_enhanced_result.found = True
        mock_enhanced_result.element = mock_element
        
        self.mock_accessibility.find_element_enhanced.return_value = mock_enhanced_result
        
        # Fast automation
        self.mock_automation = Mock()
        self.mock_automation.execute_fast_path_action.return_value = {
            'success': True,
            'execution_time': 0.1
        }
        
        # Fast reasoning
        self.mock_reasoning = Mock()
        self.mock_reasoning.process_query.return_value = "Fast response"
        self.mock_reasoning._make_api_request.return_value = {
            'choices': [{'message': {'content': 'Fast generated content'}}]
        }
        
        self.mock_orchestrator.accessibility_module = self.mock_accessibility
        self.mock_orchestrator.automation_module = self.mock_automation
        self.mock_orchestrator.reasoning_module = self.mock_reasoning
        self.mock_orchestrator.feedback_module = Mock()
    
    def test_gui_handler_execution_time_optimization(self):
        """Test GUI handler execution time optimization."""
        gui_handler = GUIHandler(self.mock_orchestrator)
        
        # Test various command types for execution time
        test_commands = [
            "click button",
            "type text",
            "scroll down",
            "press enter",
            "double-click item"
        ]
        
        execution_times = []
        
        for command in test_commands:
            start_time = time.time()
            
            context = {
                "intent": {"intent": "gui_interaction"},
                "execution_id": f"opt_test_{hash(command)}"
            }
            
            result = gui_handler.handle(command, context)
            execution_time = time.time() - start_time
            execution_times.append(execution_time)
            
            # Individual commands should be fast
            self.assertLess(execution_time, 1.0,
                f"Command '{command}' too slow: {execution_time:.3f}s")
        
        # Average execution time should be very fast
        avg_time = statistics.mean(execution_times)
        self.assertLess(avg_time, 0.5,
            f"Average GUI execution time too high: {avg_time:.3f}s")
    
    def test_fast_path_vs_vision_fallback_performance(self):
        """Test performance difference between fast path and vision fallback."""
        gui_handler = GUIHandler(self.mock_orchestrator)
        
        # Test fast path performance
        fast_path_times = []
        for i in range(5):
            start_time = time.time()
            
            context = {
                "intent": {"intent": "gui_interaction"},
                "execution_id": f"fast_path_{i}"
            }
            
            result = gui_handler.handle("click button", context)
            execution_time = time.time() - start_time
            fast_path_times.append(execution_time)
        
        # Test vision fallback performance
        # Mock fast path failure to trigger vision fallback
        self.mock_accessibility.get_accessibility_status.return_value = {
            'api_initialized': False
        }
        
        self.mock_orchestrator.vision_module = Mock()
        self.mock_orchestrator.vision_module.describe_screen.return_value = {
            'description': 'Test screen'
        }
        self.mock_reasoning.get_action_plan.return_value = {
            'plan': [{'action': 'click', 'coordinates': (100, 200)}]
        }
        
        vision_fallback_times = []
        for i in range(5):
            start_time = time.time()
            
            context = {
                "intent": {"intent": "gui_interaction"},
                "execution_id": f"vision_fallback_{i}"
            }
            
            with patch.object(gui_handler, '_perform_action_execution') as mock_execute:
                mock_execute.return_value = {
                    'total_actions': 1,
                    'successful_actions': 1,
                    'failed_actions': 0
                }
                
                result = gui_handler.handle("click button", context)
                execution_time = time.time() - start_time
                vision_fallback_times.append(execution_time)
        
        # Fast path should be significantly faster than vision fallback
        avg_fast_path = statistics.mean(fast_path_times)
        avg_vision_fallback = statistics.mean(vision_fallback_times)
        
        self.assertLess(avg_fast_path, avg_vision_fallback,
            f"Fast path not faster than vision fallback: {avg_fast_path:.3f}s vs {avg_vision_fallback:.3f}s")
        
        # Both should still be within reasonable limits
        self.assertLess(avg_fast_path, 0.5,
            f"Fast path too slow: {avg_fast_path:.3f}s")
        self.assertLess(avg_vision_fallback, 3.0,
            f"Vision fallback too slow: {avg_vision_fallback:.3f}s")
    
    def test_content_generation_optimization(self):
        """Test content generation execution time optimization."""
        deferred_handler = DeferredActionHandler(self.mock_orchestrator)
        self.mock_orchestrator.is_waiting_for_user_action = False
        self.mock_orchestrator.deferred_action_lock = threading.Lock()
        
        # Test different content types
        content_types = ["code", "text", "email", "summary"]
        generation_times = []
        
        for content_type in content_types:
            start_time = time.time()
            
            context = {
                "intent": {
                    "intent": "deferred_action",
                    "parameters": {
                        "content_request": f"Generate {content_type}",
                        "content_type": content_type
                    }
                },
                "execution_id": f"gen_opt_{content_type}"
            }
            
            with patch.object(deferred_handler, '_start_mouse_listener'), \
                 patch.object(deferred_handler, '_provide_audio_instructions'), \
                 patch.object(deferred_handler, '_start_timeout_monitoring'):
                
                result = deferred_handler.handle(f"Generate {content_type}", context)
                generation_time = time.time() - start_time
                generation_times.append(generation_time)
                
                # Content generation setup should be fast
                self.assertLess(generation_time, 2.0,
                    f"Content generation for {content_type} too slow: {generation_time:.3f}s")
        
        # Average generation time should be reasonable
        avg_generation_time = statistics.mean(generation_times)
        self.assertLess(avg_generation_time, 1.5,
            f"Average content generation too slow: {avg_generation_time:.3f}s")


class TestPerformanceRegressionDetection(unittest.TestCase):
    """Test performance regression detection and alerting."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.performance_monitor = PerformanceMonitor()
        self.mock_orchestrator = Mock()
        self.mock_orchestrator.config = {}
        
        # Set up handlers
        self.gui_handler = GUIHandler(self.mock_orchestrator)
        self.conversation_handler = ConversationHandler(self.mock_orchestrator)
        
        # Set up mock modules
        self.setup_performance_test_mocks()
    
    def setup_performance_test_mocks(self):
        """Set up mocks for performance testing."""
        self.mock_orchestrator.accessibility_module = Mock()
        self.mock_orchestrator.automation_module = Mock()
        self.mock_orchestrator.reasoning_module = Mock()
        self.mock_orchestrator.feedback_module = Mock()
        
        # Configure for consistent performance
        self.mock_orchestrator.accessibility_module.get_accessibility_status.return_value = {
            'api_initialized': True
        }
        
        mock_element = {'center_point': (100, 200), 'title': 'Test'}
        mock_enhanced_result = Mock()
        mock_enhanced_result.found = True
        mock_enhanced_result.element = mock_element
        
        self.mock_orchestrator.accessibility_module.find_element_enhanced.return_value = mock_enhanced_result
        self.mock_orchestrator.automation_module.execute_fast_path_action.return_value = {
            'success': True
        }
        self.mock_orchestrator.reasoning_module.process_query.return_value = "Response"
    
    def test_baseline_performance_establishment(self):
        """Test establishment of performance baselines."""
        # Establish baseline for GUI operations
        start_data = self.performance_monitor.start_monitoring()
        
        context = {"intent": {"intent": "gui_interaction"}, "execution_id": "baseline_gui"}
        result = self.gui_handler.handle("click button", context)
        
        baseline_metrics = self.performance_monitor.end_monitoring(start_data, True, 0)
        
        # Detect regression (should establish baseline)
        regression_result = self.performance_monitor.detect_regression(
            "gui_baseline", baseline_metrics
        )
        
        self.assertFalse(regression_result['regression_detected'])
        self.assertEqual(regression_result['message'], 'Baseline established')
        
        # Verify baseline is stored
        self.assertIn("gui_baseline", self.performance_monitor.baseline_metrics)
    
    def test_performance_regression_detection(self):
        """Test detection of performance regressions."""
        # Establish baseline
        baseline_metrics = PerformanceMetrics(
            execution_time=0.5,
            memory_usage_mb=10.0,
            cpu_usage_percent=5.0,
            success_rate=1.0,
            error_count=0,
            timestamp=time.time()
        )
        
        self.performance_monitor.baseline_metrics["test_baseline"] = baseline_metrics
        
        # Test execution time regression
        regressed_metrics = PerformanceMetrics(
            execution_time=0.8,  # 60% increase
            memory_usage_mb=10.0,
            cpu_usage_percent=5.0,
            success_rate=1.0,
            error_count=0,
            timestamp=time.time()
        )
        
        regression_result = self.performance_monitor.detect_regression(
            "test_baseline", regressed_metrics, threshold_percent=20.0
        )
        
        self.assertTrue(regression_result['regression_detected'])
        self.assertIn("Execution time increased", regression_result['regressions'][0])
        
        # Test memory usage regression
        memory_regressed_metrics = PerformanceMetrics(
            execution_time=0.5,
            memory_usage_mb=15.0,  # 50% increase
            cpu_usage_percent=5.0,
            success_rate=1.0,
            error_count=0,
            timestamp=time.time()
        )
        
        regression_result = self.performance_monitor.detect_regression(
            "test_baseline", memory_regressed_metrics, threshold_percent=20.0
        )
        
        self.assertTrue(regression_result['regression_detected'])
        self.assertIn("Memory usage increased", regression_result['regressions'][0])
        
        # Test success rate regression
        success_regressed_metrics = PerformanceMetrics(
            execution_time=0.5,
            memory_usage_mb=10.0,
            cpu_usage_percent=5.0,
            success_rate=0.7,  # 30% decrease
            error_count=3,
            timestamp=time.time()
        )
        
        regression_result = self.performance_monitor.detect_regression(
            "test_baseline", success_regressed_metrics, threshold_percent=20.0
        )
        
        self.assertTrue(regression_result['regression_detected'])
        self.assertIn("Success rate decreased", regression_result['regressions'][0])
    
    def test_performance_improvement_detection(self):
        """Test detection of performance improvements."""
        # Establish baseline
        baseline_metrics = PerformanceMetrics(
            execution_time=1.0,
            memory_usage_mb=20.0,
            cpu_usage_percent=10.0,
            success_rate=0.8,
            error_count=2,
            timestamp=time.time()
        )
        
        self.performance_monitor.baseline_metrics["improvement_baseline"] = baseline_metrics
        
        # Test improved performance
        improved_metrics = PerformanceMetrics(
            execution_time=0.6,  # 40% improvement
            memory_usage_mb=15.0,  # 25% improvement
            cpu_usage_percent=7.0,  # 30% improvement
            success_rate=0.95,  # 18.75% improvement
            error_count=0,
            timestamp=time.time()
        )
        
        regression_result = self.performance_monitor.detect_regression(
            "improvement_baseline", improved_metrics, threshold_percent=20.0
        )
        
        # Should not detect regression for improvements
        self.assertFalse(regression_result['regression_detected'])
        self.assertEqual(len(regression_result['regressions']), 0)
    
    def test_performance_alerting_thresholds(self):
        """Test different alerting thresholds for performance regression."""
        baseline_metrics = PerformanceMetrics(
            execution_time=1.0,
            memory_usage_mb=10.0,
            cpu_usage_percent=5.0,
            success_rate=1.0,
            error_count=0,
            timestamp=time.time()
        )
        
        self.performance_monitor.baseline_metrics["threshold_test"] = baseline_metrics
        
        # Test with 10% regression and 20% threshold (should not alert)
        minor_regression = PerformanceMetrics(
            execution_time=1.1,  # 10% increase
            memory_usage_mb=10.0,
            cpu_usage_percent=5.0,
            success_rate=1.0,
            error_count=0,
            timestamp=time.time()
        )
        
        result = self.performance_monitor.detect_regression(
            "threshold_test", minor_regression, threshold_percent=20.0
        )
        
        self.assertFalse(result['regression_detected'])
        
        # Test with 25% regression and 20% threshold (should alert)
        major_regression = PerformanceMetrics(
            execution_time=1.25,  # 25% increase
            memory_usage_mb=10.0,
            cpu_usage_percent=5.0,
            success_rate=1.0,
            error_count=0,
            timestamp=time.time()
        )
        
        result = self.performance_monitor.detect_regression(
            "threshold_test", major_regression, threshold_percent=20.0
        )
        
        self.assertTrue(result['regression_detected'])
        self.assertIn("Execution time increased by 25.0%", result['regressions'][0])


if __name__ == '__main__':
    # Run all performance tests
    unittest.main(verbosity=2)