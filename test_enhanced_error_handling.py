#!/usr/bin/env python3
"""
Test Enhanced Error Handling and Recovery for Conversational AURA Enhancement

This test suite validates the comprehensive error handling and recovery mechanisms
implemented for all new interaction modes including conversational queries,
deferred actions, and GUI interactions.

Test Coverage:
- Conversational query error handling and recovery
- Deferred action timeout handling and state reset
- Mouse listener error handling and cleanup
- GUI interaction error handling with fallback strategies
- System health monitoring and recovery
- Audio feedback for error scenarios
"""

import unittest
import time
import threading
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orchestrator import Orchestrator, CommandStatus, ExecutionStep
from modules.error_handler import ErrorCategory, ErrorSeverity


class TestEnhancedErrorHandling(unittest.TestCase):
    """Test suite for enhanced error handling and recovery mechanisms."""
    
    def setUp(self):
        """Set up test environment with mocked dependencies."""
        self.orchestrator = Orchestrator()
        
        # Mock all modules to control their behavior
        self.orchestrator.vision_module = Mock()
        self.orchestrator.reasoning_module = Mock()
        self.orchestrator.automation_module = Mock()
        self.orchestrator.audio_module = Mock()
        self.orchestrator.feedback_module = Mock()
        self.orchestrator.accessibility_module = Mock()
        
        # Set module availability
        self.orchestrator.module_availability = {
            'vision': True,
            'reasoning': True,
            'automation': True,
            'audio': True,
            'feedback': True,
            'accessibility': True
        }
        
        # Mock error recovery settings
        self.orchestrator.error_recovery_enabled = True
        self.orchestrator.graceful_degradation_enabled = True
        
        # Reduce timeout for testing
        self.orchestrator.deferred_action_timeout_seconds = 5.0
    
    def test_conversational_query_error_handling(self):
        """Test error handling in conversational queries."""
        execution_id = "test_conv_001"
        query = "Hello, how are you?"
        
        # Test 1: Reasoning module unavailable
        self.orchestrator.module_availability['reasoning'] = False
        
        result = self.orchestrator._handle_conversational_query(execution_id, query)
        
        self.assertEqual(result['status'], 'completed')
        self.assertIn('fallback_strategy_used', result)
        self.assertEqual(result['fallback_strategy_used'], 'reasoning_module_unavailable')
        self.assertIsNotNone(result['response'])
        
        # Test 2: Empty query handling
        with self.assertRaises(ValueError):
            self.orchestrator._handle_conversational_query(execution_id, "")
        
        # Test 3: Processing error with recovery
        self.orchestrator.module_availability['reasoning'] = True
        self.orchestrator.reasoning_module._make_api_request.side_effect = Exception("API Error")
        
        result = self.orchestrator._handle_conversational_query(execution_id, query)
        
        self.assertEqual(result['status'], 'completed')
        self.assertIn('fallback_strategy_used', result)
        self.assertEqual(result['fallback_strategy_used'], 'processing_error_fallback')
        
        print("✓ Conversational query error handling tests passed")
    
    def test_deferred_action_timeout_handling(self):
        """Test timeout handling for deferred actions."""
        execution_id = "test_def_001"
        
        # Mock content generation
        self.orchestrator._generate_deferred_content = Mock(return_value="test content")
        
        # Mock mouse listener to avoid actual listener startup
        with patch('utils.mouse_listener.GlobalMouseListener') as mock_listener_class:
            mock_listener = Mock()
            mock_listener.is_active.return_value = True
            mock_listener_class.return_value = mock_listener
            
            # Start deferred action
            intent_data = {
                'parameters': {'target': 'test code', 'content_type': 'code'},
                'original_command': 'write test code'
            }
            
            result = self.orchestrator._handle_deferred_action_request(execution_id, intent_data)
            
            self.assertEqual(result['status'], 'waiting_for_user_action')
            self.assertTrue(self.orchestrator.is_waiting_for_user_action)
            
            # Test timeout handling
            self.orchestrator._handle_deferred_action_timeout(execution_id)
            
            self.assertFalse(self.orchestrator.is_waiting_for_user_action)
            self.assertIsNone(self.orchestrator.pending_action_payload)
            self.assertIsNone(self.orchestrator.deferred_action_start_time)
        
        print("✓ Deferred action timeout handling tests passed")
    
    def test_mouse_listener_error_handling(self):
        """Test mouse listener error handling and recovery."""
        execution_id = "test_mouse_001"
        
        # Test 1: Mouse listener unavailable
        with patch('utils.mouse_listener.is_mouse_listener_available', return_value=False):
            with self.assertRaises(RuntimeError) as context:
                self.orchestrator._start_mouse_listener_for_deferred_action(execution_id)
            
            self.assertIn("pynput library required", str(context.exception))
        
        # Test 2: Mouse listener startup failure
        with patch('utils.mouse_listener.GlobalMouseListener') as mock_listener_class:
            mock_listener = Mock()
            mock_listener.start.side_effect = Exception("Permission denied")
            mock_listener_class.return_value = mock_listener
            
            with patch('utils.mouse_listener.is_mouse_listener_available', return_value=True):
                with self.assertRaises(RuntimeError) as context:
                    self.orchestrator._start_mouse_listener_for_deferred_action(execution_id)
                
                self.assertIn("Permission denied", str(context.exception))
        
        # Test 3: Successful startup with cleanup
        with patch('utils.mouse_listener.GlobalMouseListener') as mock_listener_class:
            mock_listener = Mock()
            mock_listener.is_active.return_value = True
            mock_listener_class.return_value = mock_listener
            
            with patch('utils.mouse_listener.is_mouse_listener_available', return_value=True):
                self.orchestrator._start_mouse_listener_for_deferred_action(execution_id)
                
                self.assertTrue(self.orchestrator.mouse_listener_active)
                self.assertIsNotNone(self.orchestrator.mouse_listener)
        
        print("✓ Mouse listener error handling tests passed")
    
    def test_gui_interaction_error_handling(self):
        """Test GUI interaction error handling and fallback strategies."""
        execution_id = "test_gui_001"
        command = "click on button"
        
        # Mock legacy execution method
        self.orchestrator._legacy_execute_command_internal = Mock()
        
        # Test 1: Successful execution
        self.orchestrator._legacy_execute_command_internal.return_value = {
            'status': 'completed',
            'success': True
        }
        
        result = self.orchestrator._handle_gui_interaction(execution_id, command)
        
        self.assertEqual(result['status'], 'completed')
        self.assertTrue(result['success'])
        self.assertIn('total_duration', result)
        
        # Test 2: Empty command handling
        with self.assertRaises(ValueError):
            self.orchestrator._handle_gui_interaction(execution_id, "")
        
        # Test 3: Execution failure with recovery
        self.orchestrator._legacy_execute_command_internal.side_effect = Exception("Vision module error")
        
        result = self.orchestrator._handle_gui_interaction(execution_id, command)
        
        self.assertEqual(result['status'], 'failed')
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        self.assertIn('fallback_strategy_used', result)
        
        print("✓ GUI interaction error handling tests passed")
    
    def test_system_health_monitoring(self):
        """Test system health monitoring and recovery."""
        # Test 1: Healthy system
        health = self.orchestrator.get_system_health()
        
        self.assertIn('overall_health', health)
        self.assertIn('health_score', health)
        self.assertIn('module_health', health)
        
        # Test 2: Module failure and recovery
        self.orchestrator.module_availability['vision'] = False
        
        recovery_result = self.orchestrator.attempt_system_recovery('vision')
        
        self.assertIn('recovery_attempted', recovery_result)
        self.assertIn('recovered_modules', recovery_result)
        self.assertIn('failed_modules', recovery_result)
        
        print("✓ System health monitoring tests passed")
    
    def test_timeout_monitoring_thread(self):
        """Test timeout monitoring thread functionality."""
        execution_id = "test_timeout_001"
        
        # Set up deferred action state
        self.orchestrator.is_waiting_for_user_action = True
        self.orchestrator.deferred_action_start_time = time.time()
        self.orchestrator.deferred_action_timeout_time = time.time() + 1.0  # 1 second timeout
        
        # Start timeout monitoring
        self.orchestrator._start_deferred_action_timeout_monitoring(execution_id)
        
        # Wait for timeout to trigger
        time.sleep(1.5)
        
        # Check that timeout was handled
        self.assertFalse(self.orchestrator.is_waiting_for_user_action)
        
        print("✓ Timeout monitoring thread tests passed")
    
    def test_audio_feedback_error_handling(self):
        """Test audio feedback error handling."""
        execution_id = "test_audio_001"
        
        # Test 1: Audio feedback failure in conversational query
        self.orchestrator.feedback_module.speak.side_effect = Exception("Audio error")
        
        result = self.orchestrator._handle_conversational_query(execution_id, "test query")
        
        # Should complete despite audio failure
        self.assertEqual(result['status'], 'completed')
        self.assertIn('warnings', result)
        
        # Test 2: Audio feedback in error scenarios
        self.orchestrator.feedback_module.speak.side_effect = None  # Reset
        self.orchestrator.feedback_module.speak.return_value = None
        
        # Should not raise exception when providing error feedback
        try:
            self.orchestrator._handle_deferred_action_timeout(execution_id)
        except Exception as e:
            self.fail(f"Audio error feedback should not raise exception: {e}")
        
        print("✓ Audio feedback error handling tests passed")
    
    def test_state_reset_on_errors(self):
        """Test proper state reset on various error conditions."""
        execution_id = "test_state_001"
        
        # Set up deferred action state
        self.orchestrator.is_waiting_for_user_action = True
        self.orchestrator.pending_action_payload = "test content"
        self.orchestrator.deferred_action_start_time = time.time()
        self.orchestrator.mouse_listener = Mock()
        self.orchestrator.mouse_listener_active = True
        
        # Test 1: Reset on timeout
        self.orchestrator._handle_deferred_action_timeout(execution_id)
        
        self.assertFalse(self.orchestrator.is_waiting_for_user_action)
        self.assertIsNone(self.orchestrator.pending_action_payload)
        self.assertIsNone(self.orchestrator.deferred_action_start_time)
        self.assertFalse(self.orchestrator.mouse_listener_active)
        
        # Test 2: Reset on error
        self.orchestrator.is_waiting_for_user_action = True
        self.orchestrator.pending_action_payload = "test content"
        
        self.orchestrator._reset_deferred_action_state()
        
        self.assertFalse(self.orchestrator.is_waiting_for_user_action)
        self.assertIsNone(self.orchestrator.pending_action_payload)
        
        print("✓ State reset on errors tests passed")
    
    def test_error_logging_and_context(self):
        """Test comprehensive error logging with context."""
        execution_id = "test_logging_001"
        
        # Mock global error handler
        with patch('orchestrator.global_error_handler') as mock_error_handler:
            mock_error_info = Mock()
            mock_error_info.message = "Test error message"
            mock_error_info.user_message = "User-friendly error message"
            mock_error_info.category = ErrorCategory.PROCESSING_ERROR
            mock_error_info.severity = ErrorSeverity.MEDIUM
            mock_error_info.recoverable = True
            mock_error_handler.handle_error.return_value = mock_error_info
            
            # Trigger an error in conversational query
            self.orchestrator.reasoning_module._make_api_request.side_effect = Exception("Test API error")
            
            result = self.orchestrator._handle_conversational_query(execution_id, "test query")
            
            # Verify error handler was called with proper context
            mock_error_handler.handle_error.assert_called()
            call_args = mock_error_handler.handle_error.call_args
            
            self.assertIn('context', call_args.kwargs)
            context = call_args.kwargs['context']
            self.assertIn('execution_id', context)
            self.assertEqual(context['execution_id'], execution_id)
        
        print("✓ Error logging and context tests passed")


def run_error_handling_tests():
    """Run all error handling tests."""
    print("Running Enhanced Error Handling Tests...")
    print("=" * 60)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestEnhancedErrorHandling)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("✅ All enhanced error handling tests passed!")
        print(f"Tests run: {result.testsRun}")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
    else:
        print("❌ Some tests failed!")
        print(f"Tests run: {result.testsRun}")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
        
        if result.failures:
            print("\nFailures:")
            for test, traceback in result.failures:
                print(f"- {test}: {traceback}")
        
        if result.errors:
            print("\nErrors:")
            for test, traceback in result.errors:
                print(f"- {test}: {traceback}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_error_handling_tests()
    sys.exit(0 if success else 1)