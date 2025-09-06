#!/usr/bin/env python3
"""
Comprehensive test suite for conversational AURA enhancement functionality.

This test suite covers:
1. Intent recognition accuracy and fallback behavior
2. Complete deferred action workflows from start to finish
3. State management tests for proper cleanup and thread safety
4. Backward compatibility tests to ensure existing functionality remains unchanged

Requirements tested: 8.1, 8.2, 8.3, 8.4, 9.1, 9.2, 9.3, 9.4
"""

import pytest
import sys
import os
import time
import threading
import logging
from unittest.mock import Mock, patch, MagicMock, call
from typing import Dict, Any, List

# Add the parent directory to the path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator import Orchestrator, CommandStatus, ExecutionStep
from utils.mouse_listener import GlobalMouseListener, is_mouse_listener_available

# Configure logging for tests
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TestIntentRecognition:
    """Test intent recognition accuracy and fallback behavior."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.orchestrator = Orchestrator()
        
        # Mock modules to avoid external dependencies
        self.orchestrator.reasoning_module = Mock()
        self.orchestrator.feedback_module = Mock()
        self.orchestrator.audio_module = Mock()
        self.orchestrator.vision_module = Mock()
        self.orchestrator.automation_module = Mock()
        self.orchestrator.accessibility_module = Mock()
        
        # Set all modules as available
        self.orchestrator.module_availability = {
            'reasoning': True,
            'feedback': True,
            'audio': True,
            'vision': True,
            'automation': True,
            'accessibility': True
        }
    
    def test_intent_recognition_conversational_queries(self):
        """Test intent recognition for conversational queries."""
        # Mock reasoning module to return conversational intent
        mock_response = {
            'message': {
                'content': '{"intent": "conversational_chat", "confidence": 0.95, "parameters": {}}'
            }
        }
        self.orchestrator.reasoning_module._make_api_request.return_value = mock_response
        
        conversational_queries = [
            "Hello, how are you?",
            "What's your favorite color?",
            "Tell me a joke",
            "Nice to meet you!",
            "How's the weather today?"
        ]
        
        for query in conversational_queries:
            result = self.orchestrator._recognize_intent(query)
            
            assert result['intent'] == 'conversational_chat', f"Query '{query}' should be recognized as conversational"
            assert result['confidence'] >= 0.8, f"Confidence should be high for conversational query '{query}'"
            assert 'parameters' in result, "Result should include parameters"
    
    def test_intent_recognition_gui_commands(self):
        """Test intent recognition for GUI interaction commands."""
        # Mock reasoning module to return GUI intent
        mock_response = {
            'message': {
                'content': '{"intent": "gui_interaction", "confidence": 0.90, "parameters": {"action": "click", "target": "button"}}'
            }
        }
        self.orchestrator.reasoning_module._make_api_request.return_value = mock_response
        
        gui_commands = [
            "click on the submit button",
            "type hello world",
            "scroll down",
            "press the enter key",
            "find the search box"
        ]
        
        for command in gui_commands:
            result = self.orchestrator._recognize_intent(command)
            
            assert result['intent'] == 'gui_interaction', f"Command '{command}' should be recognized as GUI interaction"
            assert result['confidence'] >= 0.8, f"Confidence should be high for GUI command '{command}'"
    
    def test_intent_recognition_deferred_actions(self):
        """Test intent recognition for deferred action requests."""
        # Mock reasoning module to return deferred action intent
        mock_response = {
            'message': {
                'content': '{"intent": "deferred_action", "confidence": 0.92, "parameters": {"content_type": "code", "action_type": "generate"}}'
            }
        }
        self.orchestrator.reasoning_module._make_api_request.return_value = mock_response
        
        deferred_commands = [
            "write code for a fibonacci function",
            "generate a Python script to sort a list",
            "create HTML for a contact form",
            "write CSS for a navigation menu",
            "generate JavaScript for form validation"
        ]
        
        for command in deferred_commands:
            result = self.orchestrator._recognize_intent(command)
            
            assert result['intent'] == 'deferred_action', f"Command '{command}' should be recognized as deferred action"
            assert result['confidence'] >= 0.8, f"Confidence should be high for deferred command '{command}'"
    
    def test_intent_recognition_fallback_behavior(self):
        """Test fallback behavior when intent recognition fails."""
        # Test with invalid JSON response
        invalid_responses = [
            {'message': {'content': 'invalid json'}},
            {'message': {'content': '{"incomplete": "json"'}},
            {'message': {'content': ''}},
            None
        ]
        
        for invalid_response in invalid_responses:
            self.orchestrator.reasoning_module._make_api_request.return_value = invalid_response
            
            result = self.orchestrator._recognize_intent("test command")
            
            assert result['intent'] == 'gui_interaction', "Should fallback to gui_interaction for invalid responses"
            assert result['confidence'] == 0.5, "Fallback confidence should be 0.5"
            assert result['fallback_used'] is True, "Should indicate fallback was used"
    
    def test_intent_recognition_api_error_fallback(self):
        """Test fallback behavior when API request fails."""
        # Mock API error
        self.orchestrator.reasoning_module._make_api_request.side_effect = Exception("API Error")
        
        result = self.orchestrator._recognize_intent("test command")
        
        assert result['intent'] == 'gui_interaction', "Should fallback to gui_interaction on API error"
        assert result['confidence'] == 0.5, "Fallback confidence should be 0.5"
        assert result['fallback_used'] is True, "Should indicate fallback was used"
        assert 'error' in result, "Should include error information"
    
    def test_intent_recognition_reasoning_module_unavailable(self):
        """Test fallback when reasoning module is unavailable."""
        self.orchestrator.module_availability['reasoning'] = False
        
        result = self.orchestrator._recognize_intent("test command")
        
        assert result['intent'] == 'gui_interaction', "Should fallback to gui_interaction when reasoning unavailable"
        assert result['confidence'] == 0.5, "Fallback confidence should be 0.5"
        assert result['fallback_used'] is True, "Should indicate fallback was used"


class TestDeferredActionWorkflows:
    """Test complete deferred action workflows from start to finish."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.orchestrator = Orchestrator()
        
        # Mock modules
        self.orchestrator.reasoning_module = Mock()
        self.orchestrator.feedback_module = Mock()
        self.orchestrator.audio_module = Mock()
        self.orchestrator.automation_module = Mock()
        
        # Set modules as available
        self.orchestrator.module_availability = {
            'reasoning': True,
            'feedback': True,
            'audio': True,
            'automation': True,
            'vision': True,
            'accessibility': True
        }
    
    @patch('utils.mouse_listener.is_mouse_listener_available', return_value=True)
    @patch('utils.mouse_listener.GlobalMouseListener')
    def test_complete_deferred_action_workflow(self, mock_listener_class, mock_availability):
        """Test complete deferred action workflow from initiation to completion."""
        # Mock mouse listener
        mock_listener = Mock()
        mock_listener_class.return_value = mock_listener
        mock_listener.get_last_click_coordinates.return_value = (500, 300)
        
        # Mock reasoning module for content generation
        self.orchestrator.reasoning_module.reason.return_value = {
            'response': 'def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)'
        }
        
        # Mock automation module
        self.orchestrator.automation_module.click.return_value = {'success': True}
        self.orchestrator.automation_module.type_text.return_value = {'success': True}
        
        # Step 1: Initiate deferred action
        intent_data = {
            'intent': 'deferred_action',
            'parameters': {
                'target': 'write a fibonacci function',
                'content_type': 'code'
            },
            'original_command': 'write a fibonacci function'
        }
        
        result = self.orchestrator._handle_deferred_action_request("test-001", intent_data)
        
        # Verify deferred action was initiated
        assert result['status'] == 'waiting_for_user_action', "Should be waiting for user action"
        assert result['success'] is True, "Deferred action initiation should succeed"
        assert self.orchestrator.is_waiting_for_user_action is True, "Should be in waiting state"
        assert self.orchestrator.pending_action_payload is not None, "Should have pending content"
        
        # Verify mouse listener was started
        mock_listener.start.assert_called_once()
        
        # Step 2: Simulate user click to complete action
        self.orchestrator._on_deferred_action_trigger("test-001")
        
        # Verify automation was called
        mock_listener.get_last_click_coordinates.assert_called()
        self.orchestrator.automation_module.click.assert_called_with(500, 300)
        self.orchestrator.automation_module.type_text.assert_called()
        
        # Verify state was reset
        assert self.orchestrator.is_waiting_for_user_action is False, "Should not be waiting after completion"
        assert self.orchestrator.pending_action_payload is None, "Payload should be cleared"
        
        # Verify mouse listener was stopped
        mock_listener.stop.assert_called()
    
    @patch('utils.mouse_listener.is_mouse_listener_available', return_value=True)
    @patch('utils.mouse_listener.GlobalMouseListener')
    def test_deferred_action_timeout_handling(self, mock_listener_class, mock_availability):
        """Test deferred action timeout handling."""
        mock_listener = Mock()
        mock_listener_class.return_value = mock_listener
        
        # Set up deferred action with short timeout
        self.orchestrator.is_waiting_for_user_action = True
        self.orchestrator.pending_action_payload = "test content"
        self.orchestrator.deferred_action_type = "type"
        self.orchestrator.deferred_action_start_time = time.time() - 400  # 400 seconds ago
        self.orchestrator.deferred_action_timeout_time = time.time() - 100  # Timed out 100 seconds ago
        self.orchestrator.mouse_listener = mock_listener
        
        # Handle timeout
        self.orchestrator._handle_deferred_action_timeout("test-timeout")
        
        # Verify state was reset
        assert self.orchestrator.is_waiting_for_user_action is False, "Should not be waiting after timeout"
        assert self.orchestrator.pending_action_payload is None, "Payload should be cleared after timeout"
        
        # Verify mouse listener was stopped
        mock_listener.stop.assert_called()
        
        # Verify audio feedback was provided
        self.orchestrator.feedback_module.speak.assert_called()
    
    @patch('utils.mouse_listener.is_mouse_listener_available', return_value=True)
    @patch('utils.mouse_listener.GlobalMouseListener')
    def test_deferred_action_interruption(self, mock_listener_class, mock_availability):
        """Test deferred action interruption by new commands."""
        mock_listener = Mock()
        mock_listener_class.return_value = mock_listener
        
        # Set up active deferred action
        self.orchestrator.is_waiting_for_user_action = True
        self.orchestrator.pending_action_payload = "test content"
        self.orchestrator.deferred_action_type = "type"
        self.orchestrator.mouse_listener = mock_listener
        
        # Mock intent recognition for new GUI command
        def mock_recognize_intent(command):
            return {
                'intent': 'gui_interaction',
                'confidence': 0.9,
                'parameters': {},
                'original_command': command
            }
        
        self.orchestrator._recognize_intent = mock_recognize_intent
        
        # Mock GUI handler to avoid actual GUI operations
        mock_gui_result = {
            'execution_id': 'test_gui',
            'command': 'click button',
            'status': 'completed',
            'success': True,
            'mode': 'gui_interaction',
            'duration': 0.1
        }
        self.orchestrator._handle_gui_interaction = Mock(return_value=mock_gui_result)
        
        # Execute new command (should interrupt deferred action)
        result = self.orchestrator.execute_command("click on button")
        
        # Verify deferred action was interrupted
        assert self.orchestrator.is_waiting_for_user_action is False, "Deferred action should be interrupted"
        assert self.orchestrator.pending_action_payload is None, "Payload should be cleared on interruption"
        
        # Verify mouse listener was stopped
        mock_listener.stop.assert_called()
    
    def test_deferred_action_content_generation_error(self):
        """Test error handling during content generation."""
        # Mock reasoning module to fail
        self.orchestrator.reasoning_module.reason.side_effect = Exception("Content generation failed")
        
        intent_data = {
            'intent': 'deferred_action',
            'parameters': {
                'target': 'write some code',
                'content_type': 'code'
            },
            'original_command': 'write some code'
        }
        
        result = self.orchestrator._handle_deferred_action_request("test-error", intent_data)
        
        # Verify error handling
        assert result['status'] == 'failed', "Should indicate failure"
        assert result['success'] is False, "Should not succeed"
        assert 'error' in result, "Should include error information"
        
        # Verify state was not set to waiting
        assert self.orchestrator.is_waiting_for_user_action is False, "Should not be waiting on error"
    
    @patch('utils.mouse_listener.is_mouse_listener_available', return_value=False)
    def test_deferred_action_mouse_listener_unavailable(self, mock_availability):
        """Test deferred action when mouse listener is unavailable."""
        intent_data = {
            'intent': 'deferred_action',
            'parameters': {
                'target': 'write some code',
                'content_type': 'code'
            },
            'original_command': 'write some code'
        }
        
        # Mock successful content generation
        self.orchestrator.reasoning_module.reason.return_value = {
            'response': 'print("Hello, World!")'
        }
        
        result = self.orchestrator._handle_deferred_action_request("test-no-mouse", intent_data)
        
        # Should fall back to immediate execution or provide alternative
        assert result['status'] in ['completed', 'failed'], "Should handle mouse listener unavailability"
        if result['status'] == 'failed':
            assert 'mouse listener' in result.get('error', '').lower(), "Should mention mouse listener issue"


class TestStateManagement:
    """Test state management for proper cleanup and thread safety."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.orchestrator = Orchestrator()
    
    def test_state_initialization(self):
        """Test proper state initialization."""
        # Verify all state variables are properly initialized
        assert self.orchestrator.system_mode == 'ready', "System should start in ready mode"
        assert self.orchestrator.is_waiting_for_user_action is False, "Should not be waiting initially"
        assert self.orchestrator.pending_action_payload is None, "No pending payload initially"
        assert self.orchestrator.deferred_action_type is None, "No action type initially"
        assert self.orchestrator.mouse_listener is None, "No mouse listener initially"
        assert self.orchestrator.mouse_listener_active is False, "Mouse listener not active initially"
        
        # Verify locks are initialized
        assert hasattr(self.orchestrator, 'intent_lock'), "Intent lock should be initialized"
        assert hasattr(self.orchestrator, 'deferred_action_lock'), "Deferred action lock should be initialized"
        assert hasattr(self.orchestrator, 'conversation_lock'), "Conversation lock should be initialized"
        assert hasattr(self.orchestrator, 'state_validation_lock'), "State validation lock should be initialized"
    
    def test_state_reset_comprehensive(self):
        """Test comprehensive state reset functionality."""
        # Set up complex state
        self.orchestrator.is_waiting_for_user_action = True
        self.orchestrator.pending_action_payload = "test content"
        self.orchestrator.deferred_action_type = "type"
        self.orchestrator.deferred_action_start_time = time.time()
        self.orchestrator.deferred_action_timeout_time = time.time() + 300
        self.orchestrator.system_mode = 'waiting_for_user'
        self.orchestrator.current_execution_id = "test_123"
        self.orchestrator.mouse_listener_active = True
        
        # Mock mouse listener
        mock_listener = Mock()
        mock_listener.is_active.return_value = True
        self.orchestrator.mouse_listener = mock_listener
        
        # Reset state
        self.orchestrator._reset_deferred_action_state()
        
        # Verify all state is reset
        assert self.orchestrator.is_waiting_for_user_action is False, "Should not be waiting"
        assert self.orchestrator.pending_action_payload is None, "Payload should be cleared"
        assert self.orchestrator.deferred_action_type is None, "Action type should be cleared"
        assert self.orchestrator.deferred_action_start_time is None, "Start time should be cleared"
        assert self.orchestrator.deferred_action_timeout_time is None, "Timeout time should be cleared"
        assert self.orchestrator.mouse_listener is None, "Mouse listener should be cleared"
        assert self.orchestrator.mouse_listener_active is False, "Mouse listener should not be active"
        assert self.orchestrator.system_mode == 'ready', "Should return to ready mode"
        
        # Verify mouse listener was stopped
        mock_listener.stop.assert_called_once()
    
    def test_state_validation_consistency(self):
        """Test state validation and consistency checking."""
        # Test valid state
        validation_result = self.orchestrator.validate_system_state()
        assert validation_result['is_valid'] is True, "Clean state should be valid"
        assert len(validation_result['issues']) == 0, "Clean state should have no issues"
        
        # Test inconsistent state
        self.orchestrator.is_waiting_for_user_action = True
        self.orchestrator.system_mode = 'ready'  # Inconsistent
        
        validation_result = self.orchestrator.validate_system_state()
        assert validation_result['is_valid'] is False, "Inconsistent state should be invalid"
        assert len(validation_result['issues']) > 0, "Should detect inconsistencies"
        
        # Test state correction
        self.orchestrator._force_state_consistency()
        validation_result = self.orchestrator.validate_system_state()
        assert validation_result['is_valid'] is True, "State should be consistent after correction"
    
    def test_thread_safety_state_access(self):
        """Test thread safety of state access and modification."""
        results = []
        errors = []
        
        def state_modifier_thread(thread_id):
            """Thread function that modifies state."""
            try:
                for i in range(10):
                    # Acquire lock and modify state
                    with self.orchestrator.deferred_action_lock:
                        self.orchestrator.is_waiting_for_user_action = True
                        self.orchestrator.pending_action_payload = f"content_{thread_id}_{i}"
                        time.sleep(0.001)  # Small delay to increase chance of race conditions
                        self.orchestrator._reset_deferred_action_state()
                    
                    time.sleep(0.001)
                
                results.append(f"Thread {thread_id} completed")
            except Exception as e:
                errors.append(f"Thread {thread_id} error: {e}")
        
        # Start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=state_modifier_thread, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=5.0)
        
        # Verify no errors occurred
        assert len(errors) == 0, f"Thread safety errors: {errors}"
        assert len(results) == 5, "All threads should complete successfully"
        
        # Verify final state is consistent
        validation_result = self.orchestrator.validate_system_state()
        assert validation_result['is_valid'] is True, "Final state should be consistent"
    
    def test_timeout_detection_and_handling(self):
        """Test timeout detection and automatic handling."""
        # Set up timed-out state
        current_time = time.time()
        self.orchestrator.is_waiting_for_user_action = True
        self.orchestrator.deferred_action_start_time = current_time - 400  # 400 seconds ago
        self.orchestrator.deferred_action_timeout_time = current_time - 100  # Timed out 100 seconds ago
        self.orchestrator.system_mode = 'waiting_for_user'
        
        # Check timeout detection
        timeout_issues = self.orchestrator._check_timeout_conditions()
        assert len(timeout_issues) > 0, "Should detect timeout"
        assert any('timeout' in issue.lower() for issue in timeout_issues), "Should identify timeout issue"
        
        # Handle timeout
        timeout_result = self.orchestrator.handle_deferred_action_timeout()
        assert timeout_result['timeout_handled'] is True, "Should handle timeout"
        assert timeout_result['was_waiting'] is True, "Should record waiting state"
        
        # Verify state is reset
        assert self.orchestrator.is_waiting_for_user_action is False, "Should not be waiting after timeout"
        assert self.orchestrator.system_mode == 'ready', "Should return to ready mode"
    
    def test_state_transition_recording(self):
        """Test state transition recording and history."""
        initial_count = len(self.orchestrator.state_transition_history)
        
        # Record some transitions
        self.orchestrator._record_state_transition('test_transition_1', {'data': 'test1'})
        self.orchestrator._record_state_transition('test_transition_2', {'data': 'test2'})
        
        # Verify transitions were recorded
        assert len(self.orchestrator.state_transition_history) == initial_count + 2, "Should record transitions"
        
        # Check transition structure
        latest_transition = self.orchestrator.state_transition_history[-1]
        assert 'timestamp' in latest_transition, "Should have timestamp"
        assert 'transition_type' in latest_transition, "Should have transition type"
        assert 'context' in latest_transition, "Should have context"
        assert latest_transition['transition_type'] == 'test_transition_2', "Should record correct type"


class TestBackwardCompatibility:
    """Test backward compatibility to ensure existing functionality remains unchanged."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.orchestrator = Orchestrator()
        
        # Mock modules
        self.orchestrator.reasoning_module = Mock()
        self.orchestrator.feedback_module = Mock()
        self.orchestrator.audio_module = Mock()
        self.orchestrator.vision_module = Mock()
        self.orchestrator.automation_module = Mock()
        self.orchestrator.accessibility_module = Mock()
        
        # Set modules as available
        self.orchestrator.module_availability = {
            'reasoning': True,
            'feedback': True,
            'audio': True,
            'vision': True,
            'automation': True,
            'accessibility': True
        }
    
    def test_existing_gui_commands_unchanged(self):
        """Test that existing GUI commands work exactly as before."""
        # Mock intent recognition to return GUI interaction
        def mock_recognize_intent(command):
            return {
                'intent': 'gui_interaction',
                'confidence': 0.9,
                'parameters': {},
                'original_command': command
            }
        
        self.orchestrator._recognize_intent = mock_recognize_intent
        
        # Mock GUI handler to simulate successful execution
        mock_gui_result = {
            'execution_id': 'test_gui',
            'command': 'test',
            'status': 'completed',
            'success': True,
            'mode': 'gui_interaction',
            'duration': 0.1,
            'steps_completed': ['validation', 'perception', 'reasoning', 'action'],
            'metadata': {}
        }
        self.orchestrator._handle_gui_interaction = Mock(return_value=mock_gui_result)
        
        # Test traditional GUI commands
        gui_commands = [
            "click on the submit button",
            "type hello world",
            "scroll down",
            "press enter",
            "find the search box"
        ]
        
        for command in gui_commands:
            result = self.orchestrator.execute_command(command)
            
            # Verify command was routed to GUI handler
            self.orchestrator._handle_gui_interaction.assert_called()
            
            # Verify result structure matches expectations
            assert result['success'] is True, f"GUI command '{command}' should succeed"
            assert result['mode'] == 'gui_interaction', f"Command '{command}' should use GUI mode"
            
            # Reset mock for next iteration
            self.orchestrator._handle_gui_interaction.reset_mock()
    
    def test_question_answering_preserved(self):
        """Test that question answering functionality is preserved."""
        # Mock intent recognition for question answering
        def mock_recognize_intent(command):
            if any(word in command.lower() for word in ['what', 'where', 'how', 'why', 'when']):
                return {
                    'intent': 'question_answering',
                    'confidence': 0.85,
                    'parameters': {},
                    'original_command': command
                }
            return {
                'intent': 'gui_interaction',
                'confidence': 0.7,
                'parameters': {},
                'original_command': command
            }
        
        self.orchestrator._recognize_intent = mock_recognize_intent
        
        # Mock the legacy question answering functionality
        mock_qa_result = {
            'execution_id': 'test_qa',
            'command': 'test question',
            'status': 'completed',
            'success': True,
            'mode': 'question_answering',
            'response': 'This is a test answer',
            'duration': 0.2
        }
        
        # Mock the legacy execute command internal method
        self.orchestrator._legacy_execute_command_internal = Mock(return_value=mock_qa_result)
        
        questions = [
            "What's on my screen?",
            "Where is the submit button?",
            "How do I save this file?",
            "What applications are running?"
        ]
        
        for question in questions:
            result = self.orchestrator.execute_command(question)
            
            # Should use legacy question answering
            assert result['success'] is True, f"Question '{question}' should be answered"
            assert 'response' in result or result.get('mode') in ['question_answering', 'gui_interaction'], \
                f"Question '{question}' should provide response or use appropriate mode"
    
    def test_error_handling_backward_compatibility(self):
        """Test that error handling maintains backward compatibility."""
        # Test with reasoning module failure
        self.orchestrator.reasoning_module._make_api_request.side_effect = Exception("API Error")
        
        # Should fall back to GUI interaction gracefully
        result = self.orchestrator.execute_command("click button")
        
        # Should not crash and should provide some result
        assert result is not None, "Should return result even with API failure"
        assert isinstance(result, dict), "Result should be a dictionary"
        
        # Should either succeed with fallback or fail gracefully
        if not result.get('success', False):
            assert 'error' in result or 'errors' in result, "Failed result should include error information"
    
    def test_module_availability_fallback(self):
        """Test fallback behavior when modules are unavailable."""
        # Test with various modules unavailable
        module_combinations = [
            {'reasoning': False, 'vision': True, 'automation': True},
            {'reasoning': True, 'vision': False, 'automation': True},
            {'reasoning': True, 'vision': True, 'automation': False},
            {'reasoning': False, 'vision': False, 'automation': True}
        ]
        
        for availability in module_combinations:
            # Set module availability
            self.orchestrator.module_availability.update(availability)
            
            # Test command execution
            result = self.orchestrator.execute_command("test command")
            
            # Should not crash regardless of module availability
            assert result is not None, f"Should return result with availability: {availability}"
            assert isinstance(result, dict), "Result should be a dictionary"
    
    def test_audio_feedback_integration_preserved(self):
        """Test that audio feedback integration is preserved."""
        # Mock conversational response
        self.orchestrator.reasoning_module._make_api_request.return_value = {
            'message': {
                'content': '{"intent": "conversational_chat", "confidence": 0.95, "parameters": {}}'
            }
        }
        
        # Test conversational query that should trigger audio feedback
        result = self.orchestrator._handle_conversational_query("test-audio", "Hello AURA")
        
        # Verify audio feedback was called
        if result.get('success'):
            self.orchestrator.feedback_module.speak.assert_called()
    
    def test_performance_impact_minimal(self):
        """Test that performance impact of enhancements is minimal."""
        # Measure execution time for simple commands
        start_time = time.time()
        
        # Mock quick responses
        self.orchestrator.reasoning_module._make_api_request.return_value = {
            'message': {
                'content': '{"intent": "gui_interaction", "confidence": 0.9, "parameters": {}}'
            }
        }
        
        mock_gui_result = {
            'execution_id': 'perf_test',
            'command': 'test',
            'status': 'completed',
            'success': True,
            'mode': 'gui_interaction',
            'duration': 0.05
        }
        self.orchestrator._handle_gui_interaction = Mock(return_value=mock_gui_result)
        
        # Execute multiple commands
        for i in range(10):
            result = self.orchestrator.execute_command(f"click button {i}")
            assert result['success'] is True, f"Command {i} should succeed"
        
        total_time = time.time() - start_time
        
        # Should complete reasonably quickly (allowing for mock overhead)
        assert total_time < 5.0, f"10 commands should complete in under 5 seconds, took {total_time:.2f}s"


class TestIntegrationScenarios:
    """Test integration scenarios combining multiple features."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.orchestrator = Orchestrator()
        
        # Mock modules
        self.orchestrator.reasoning_module = Mock()
        self.orchestrator.feedback_module = Mock()
        self.orchestrator.audio_module = Mock()
        self.orchestrator.automation_module = Mock()
        
        # Set modules as available
        self.orchestrator.module_availability = {
            'reasoning': True,
            'feedback': True,
            'audio': True,
            'automation': True,
            'vision': True,
            'accessibility': True
        }
    
    @patch('utils.mouse_listener.is_mouse_listener_available', return_value=True)
    @patch('utils.mouse_listener.GlobalMouseListener')
    def test_mixed_interaction_session(self, mock_listener_class, mock_availability):
        """Test a session with mixed interaction types."""
        mock_listener = Mock()
        mock_listener_class.return_value = mock_listener
        
        # Set up different intent responses
        def mock_api_request(prompt):
            if "Intent categories:" in prompt:
                if "hello" in prompt.lower():
                    return {'message': {'content': '{"intent": "conversational_chat", "confidence": 0.95, "parameters": {}}'}}
                elif "write code" in prompt.lower():
                    return {'message': {'content': '{"intent": "deferred_action", "confidence": 0.92, "parameters": {"content_type": "code"}}'}}
                else:
                    return {'message': {'content': '{"intent": "gui_interaction", "confidence": 0.88, "parameters": {}}'}}
            else:
                return {'message': {'content': 'Hello! I\'m AURA, nice to meet you!'}}
        
        self.orchestrator.reasoning_module._make_api_request.side_effect = mock_api_request
        self.orchestrator.reasoning_module.reason.return_value = {'response': 'print("Hello, World!")'}
        
        # Mock GUI handler
        mock_gui_result = {
            'execution_id': 'test_gui',
            'command': 'test',
            'status': 'completed',
            'success': True,
            'mode': 'gui_interaction',
            'duration': 0.1
        }
        self.orchestrator._handle_gui_interaction = Mock(return_value=mock_gui_result)
        
        # Session: Conversation -> GUI -> Deferred Action
        
        # 1. Conversational query
        result1 = self.orchestrator.execute_command("Hello AURA, how are you?")
        assert result1['mode'] == 'conversational_chat', "Should handle conversation"
        assert result1['success'] is True, "Conversation should succeed"
        
        # 2. GUI command
        result2 = self.orchestrator.execute_command("click on submit button")
        assert result2['mode'] == 'gui_interaction', "Should handle GUI interaction"
        assert result2['success'] is True, "GUI command should succeed"
        
        # 3. Deferred action
        result3 = self.orchestrator.execute_command("write code for hello world")
        assert result3['status'] == 'waiting_for_user_action', "Should initiate deferred action"
        assert result3['success'] is True, "Deferred action should start"
        
        # Verify state management across interactions
        assert len(self.orchestrator.conversation_history) > 0, "Should maintain conversation history"
        assert self.orchestrator.is_waiting_for_user_action is True, "Should be waiting for user action"


if __name__ == '__main__':
    # Run the comprehensive test suite
    pytest.main([__file__, '-v', '--tb=short'])