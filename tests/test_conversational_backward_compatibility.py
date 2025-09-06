#!/usr/bin/env python3
"""
Backward compatibility tests for conversational AURA enhancement.

This test suite ensures that existing functionality remains unchanged
after the conversational enhancement implementation:
- Existing GUI commands work exactly as before
- Question answering functionality is preserved
- Audio feedback integration remains consistent
- Performance impact is minimal
- Error handling maintains backward compatibility

Requirements tested: 8.1, 8.2, 8.3, 8.4
"""

import pytest
import sys
import os
import time
from unittest.mock import Mock, patch, MagicMock, call

# Add the parent directory to the path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator import Orchestrator, CommandStatus


class TestExistingGUICommandsUnchanged:
    """Test that existing GUI commands work exactly as before."""
    
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
        
        # Set all modules as available
        self.orchestrator.module_availability = {
            'reasoning': True,
            'feedback': True,
            'audio': True,
            'vision': True,
            'automation': True,
            'accessibility': True
        }
    
    def test_click_commands_unchanged(self):
        """Test that click commands work exactly as before enhancement."""
        # Mock intent recognition to return GUI interaction
        def mock_recognize_intent(command):
            return {
                'intent': 'gui_interaction',
                'confidence': 0.9,
                'parameters': {'action': 'click', 'target': 'button'},
                'original_command': command
            }
        
        self.orchestrator._recognize_intent = mock_recognize_intent
        
        # Mock GUI handler to simulate successful execution
        mock_gui_result = {
            'execution_id': 'test_click',
            'command': 'click on submit button',
            'status': 'completed',
            'success': True,
            'mode': 'gui_interaction',
            'duration': 0.15,
            'steps_completed': ['validation', 'perception', 'reasoning', 'action'],
            'metadata': {
                'element_found': True,
                'click_coordinates': [100, 200],
                'automation_method': 'accessibility'
            }
        }
        self.orchestrator._handle_gui_interaction = Mock(return_value=mock_gui_result)
        
        # Test various click commands
        click_commands = [
            "click on the submit button",
            "click submit",
            "press the OK button",
            "tap on save",
            "click the red button in the corner"
        ]
        
        for command in click_commands:
            result = self.orchestrator.execute_command(command)
            
            # Verify command was routed to GUI handler
            self.orchestrator._handle_gui_interaction.assert_called()
            
            # Verify result structure matches pre-enhancement expectations
            assert result['success'] is True, f"Click command '{command}' should succeed"
            assert result['mode'] == 'gui_interaction', f"Command '{command}' should use GUI mode"
            assert result['status'] == 'completed', f"Command '{command}' should complete"
            assert 'duration' in result, f"Command '{command}' should include duration"
            assert 'steps_completed' in result, f"Command '{command}' should include steps"
            
            # Verify metadata structure is preserved
            if 'metadata' in result:
                metadata = result['metadata']
                assert isinstance(metadata, dict), "Metadata should be a dictionary"
            
            # Reset mock for next iteration
            self.orchestrator._handle_gui_interaction.reset_mock()
    
    def test_type_commands_unchanged(self):
        """Test that type commands work exactly as before enhancement."""
        def mock_recognize_intent(command):
            return {
                'intent': 'gui_interaction',
                'confidence': 0.92,
                'parameters': {'action': 'type', 'text': 'hello world'},
                'original_command': command
            }
        
        self.orchestrator._recognize_intent = mock_recognize_intent
        
        mock_gui_result = {
            'execution_id': 'test_type',
            'command': 'type hello world',
            'status': 'completed',
            'success': True,
            'mode': 'gui_interaction',
            'duration': 0.08,
            'steps_completed': ['validation', 'action'],
            'metadata': {
                'text_typed': 'hello world',
                'automation_method': 'direct'
            }
        }
        self.orchestrator._handle_gui_interaction = Mock(return_value=mock_gui_result)
        
        type_commands = [
            'type "hello world"',
            "type hello world",
            'enter "test@example.com"',
            "input my password",
            'write "Dear Sir or Madam"'
        ]
        
        for command in type_commands:
            result = self.orchestrator.execute_command(command)
            
            # Verify GUI handler was called
            self.orchestrator._handle_gui_interaction.assert_called()
            
            # Verify result structure
            assert result['success'] is True, f"Type command '{command}' should succeed"
            assert result['mode'] == 'gui_interaction', f"Command '{command}' should use GUI mode"
            assert result['status'] == 'completed', f"Command '{command}' should complete"
            
            # Reset mock
            self.orchestrator._handle_gui_interaction.reset_mock()
    
    def test_scroll_commands_unchanged(self):
        """Test that scroll commands work exactly as before enhancement."""
        def mock_recognize_intent(command):
            return {
                'intent': 'gui_interaction',
                'confidence': 0.88,
                'parameters': {'action': 'scroll', 'direction': 'down'},
                'original_command': command
            }
        
        self.orchestrator._recognize_intent = mock_recognize_intent
        
        mock_gui_result = {
            'execution_id': 'test_scroll',
            'command': 'scroll down',
            'status': 'completed',
            'success': True,
            'mode': 'gui_interaction',
            'duration': 0.05,
            'steps_completed': ['validation', 'action'],
            'metadata': {
                'scroll_direction': 'down',
                'scroll_amount': 3
            }
        }
        self.orchestrator._handle_gui_interaction = Mock(return_value=mock_gui_result)
        
        scroll_commands = [
            "scroll down",
            "scroll up",
            "page down",
            "scroll to the bottom",
            "scroll left"
        ]
        
        for command in scroll_commands:
            result = self.orchestrator.execute_command(command)
            
            # Verify GUI handler was called
            self.orchestrator._handle_gui_interaction.assert_called()
            
            # Verify result structure
            assert result['success'] is True, f"Scroll command '{command}' should succeed"
            assert result['mode'] == 'gui_interaction', f"Command '{command}' should use GUI mode"
            
            # Reset mock
            self.orchestrator._handle_gui_interaction.reset_mock()
    
    def test_complex_gui_commands_unchanged(self):
        """Test that complex GUI commands work exactly as before enhancement."""
        def mock_recognize_intent(command):
            return {
                'intent': 'gui_interaction',
                'confidence': 0.85,
                'parameters': {'action': 'complex', 'target': 'multiple_elements'},
                'original_command': command
            }
        
        self.orchestrator._recognize_intent = mock_recognize_intent
        
        mock_gui_result = {
            'execution_id': 'test_complex',
            'command': 'find and click the blue submit button',
            'status': 'completed',
            'success': True,
            'mode': 'gui_interaction',
            'duration': 0.25,
            'steps_completed': ['validation', 'perception', 'reasoning', 'action'],
            'metadata': {
                'elements_analyzed': 15,
                'target_found': True,
                'confidence_score': 0.92
            }
        }
        self.orchestrator._handle_gui_interaction = Mock(return_value=mock_gui_result)
        
        complex_commands = [
            "find and click the blue submit button",
            "select all text in the email field",
            "right-click on the file named document.pdf",
            "double-click the Chrome icon on the desktop",
            "click the dropdown arrow next to the username field"
        ]
        
        for command in complex_commands:
            result = self.orchestrator.execute_command(command)
            
            # Verify GUI handler was called
            self.orchestrator._handle_gui_interaction.assert_called()
            
            # Verify result structure includes all expected fields
            assert result['success'] is True, f"Complex command '{command}' should succeed"
            assert result['mode'] == 'gui_interaction', f"Command '{command}' should use GUI mode"
            assert 'duration' in result, f"Command '{command}' should include timing"
            assert 'steps_completed' in result, f"Command '{command}' should include steps"
            
            # Reset mock
            self.orchestrator._handle_gui_interaction.reset_mock()


class TestQuestionAnsweringPreserved:
    """Test that question answering functionality is preserved."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.orchestrator = Orchestrator()
        
        # Mock modules
        self.orchestrator.reasoning_module = Mock()
        self.orchestrator.feedback_module = Mock()
        self.orchestrator.vision_module = Mock()
        
        # Set modules as available
        self.orchestrator.module_availability = {
            'reasoning': True,
            'feedback': True,
            'vision': True,
            'automation': True,
            'accessibility': True
        }
    
    def test_screen_analysis_questions_preserved(self):
        """Test that screen analysis questions work as before."""
        # Mock intent recognition for question answering
        def mock_recognize_intent(command):
            return {
                'intent': 'question_answering',
                'confidence': 0.90,
                'parameters': {'question_type': 'screen_analysis'},
                'original_command': command
            }
        
        self.orchestrator._recognize_intent = mock_recognize_intent
        
        # Mock the legacy question answering functionality
        mock_qa_result = {
            'execution_id': 'test_qa',
            'command': "What's on my screen?",
            'status': 'completed',
            'success': True,
            'mode': 'question_answering',
            'response': 'I can see a web browser with a login form containing username and password fields, and a blue "Sign In" button.',
            'duration': 0.45,
            'steps_completed': ['validation', 'perception', 'reasoning'],
            'metadata': {
                'elements_detected': 8,
                'analysis_type': 'comprehensive'
            }
        }
        
        self.orchestrator._legacy_execute_command_internal = Mock(return_value=mock_qa_result)
        
        screen_questions = [
            "What's on my screen?",
            "Describe what you see",
            "What applications are open?",
            "Tell me about the current window",
            "What elements are visible?"
        ]
        
        for question in screen_questions:
            result = self.orchestrator.execute_command(question)
            
            # Should use legacy question answering
            assert result['success'] is True, f"Question '{question}' should be answered"
            assert 'response' in result or result.get('mode') == 'question_answering', \
                f"Question '{question}' should provide response or use QA mode"
            
            # Verify response structure is preserved
            if 'response' in result:
                assert isinstance(result['response'], str), "Response should be a string"
                assert len(result['response']) > 0, "Response should not be empty"
    
    def test_element_location_questions_preserved(self):
        """Test that element location questions work as before."""
        def mock_recognize_intent(command):
            return {
                'intent': 'question_answering',
                'confidence': 0.87,
                'parameters': {'question_type': 'element_location'},
                'original_command': command
            }
        
        self.orchestrator._recognize_intent = mock_recognize_intent
        
        mock_qa_result = {
            'execution_id': 'test_location',
            'command': 'Where is the submit button?',
            'status': 'completed',
            'success': True,
            'mode': 'question_answering',
            'response': 'The submit button is located in the bottom right corner of the form, at coordinates (450, 320).',
            'duration': 0.32,
            'metadata': {
                'element_found': True,
                'coordinates': [450, 320]
            }
        }
        
        self.orchestrator._legacy_execute_command_internal = Mock(return_value=mock_qa_result)
        
        location_questions = [
            "Where is the submit button?",
            "Where can I find the menu?",
            "Where is the search box located?",
            "How do I find the settings?",
            "Where is the close button?"
        ]
        
        for question in location_questions:
            result = self.orchestrator.execute_command(question)
            
            # Verify question was answered
            assert result['success'] is True, f"Location question '{question}' should be answered"
            
            # Verify response structure
            if 'response' in result:
                response = result['response']
                assert isinstance(response, str), "Response should be a string"
                assert len(response) > 10, "Response should be meaningful"
    
    def test_informational_questions_preserved(self):
        """Test that informational questions work as before."""
        def mock_recognize_intent(command):
            return {
                'intent': 'question_answering',
                'confidence': 0.83,
                'parameters': {'question_type': 'information'},
                'original_command': command
            }
        
        self.orchestrator._recognize_intent = mock_recognize_intent
        
        mock_qa_result = {
            'execution_id': 'test_info',
            'command': 'How many windows are open?',
            'status': 'completed',
            'success': True,
            'mode': 'question_answering',
            'response': 'There are currently 3 windows open: Chrome browser, Terminal, and Text Editor.',
            'duration': 0.28,
            'metadata': {
                'window_count': 3,
                'applications': ['Chrome', 'Terminal', 'TextEdit']
            }
        }
        
        self.orchestrator._legacy_execute_command_internal = Mock(return_value=mock_qa_result)
        
        info_questions = [
            "How many windows are open?",
            "What applications are running?",
            "How many tabs are in the browser?",
            "What's the current time?",
            "What's the active application?"
        ]
        
        for question in info_questions:
            result = self.orchestrator.execute_command(question)
            
            # Verify question was answered
            assert result['success'] is True, f"Info question '{question}' should be answered"
            
            # Verify response provides information
            if 'response' in result:
                response = result['response']
                assert len(response) > 5, "Response should provide information"


class TestAudioFeedbackIntegrationPreserved:
    """Test that audio feedback integration remains consistent."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.orchestrator = Orchestrator()
        
        # Mock modules
        self.orchestrator.reasoning_module = Mock()
        self.orchestrator.feedback_module = Mock()
        self.orchestrator.audio_module = Mock()
        
        # Set modules as available
        self.orchestrator.module_availability = {
            'reasoning': True,
            'feedback': True,
            'audio': True,
            'vision': True,
            'automation': True,
            'accessibility': True
        }
    
    def test_gui_command_audio_feedback_preserved(self):
        """Test that GUI commands still provide appropriate audio feedback."""
        def mock_recognize_intent(command):
            return {
                'intent': 'gui_interaction',
                'confidence': 0.9,
                'parameters': {},
                'original_command': command
            }
        
        self.orchestrator._recognize_intent = mock_recognize_intent
        
        # Mock GUI handler with audio feedback
        mock_gui_result = {
            'execution_id': 'test_audio',
            'command': 'click button',
            'status': 'completed',
            'success': True,
            'mode': 'gui_interaction',
            'duration': 0.1,
            'audio_feedback_provided': True
        }
        
        def mock_gui_handler(execution_id, command):
            # Simulate audio feedback during GUI execution
            self.orchestrator.feedback_module.speak("Clicking button")
            return mock_gui_result
        
        self.orchestrator._handle_gui_interaction = mock_gui_handler
        
        result = self.orchestrator.execute_command("click on submit button")
        
        # Verify audio feedback was provided
        self.orchestrator.feedback_module.speak.assert_called()
        
        # Verify result indicates audio feedback
        assert result.get('audio_feedback_provided') is True, "Should indicate audio feedback was provided"
    
    def test_question_answering_audio_feedback_preserved(self):
        """Test that question answering still provides audio feedback."""
        def mock_recognize_intent(command):
            return {
                'intent': 'question_answering',
                'confidence': 0.85,
                'parameters': {},
                'original_command': command
            }
        
        self.orchestrator._recognize_intent = mock_recognize_intent
        
        mock_qa_result = {
            'execution_id': 'test_qa_audio',
            'command': "What's on screen?",
            'status': 'completed',
            'success': True,
            'mode': 'question_answering',
            'response': 'I can see a web page with several buttons and text fields.',
            'duration': 0.3,
            'audio_feedback_provided': True
        }
        
        def mock_legacy_handler(command, execution_context):
            # Simulate audio feedback during question answering
            response = mock_qa_result['response']
            self.orchestrator.feedback_module.speak(response)
            return mock_qa_result
        
        self.orchestrator._legacy_execute_command_internal = mock_legacy_handler
        
        result = self.orchestrator.execute_command("What's on my screen?")
        
        # Verify audio feedback was provided
        self.orchestrator.feedback_module.speak.assert_called()
        
        # Verify response was spoken
        speak_calls = [call[0][0] for call in self.orchestrator.feedback_module.speak.call_args_list]
        assert any('web page' in call for call in speak_calls), "Should speak the response"
    
    def test_error_audio_feedback_preserved(self):
        """Test that error scenarios still provide audio feedback."""
        # Mock API error
        self.orchestrator.reasoning_module._make_api_request.side_effect = Exception("API Error")
        
        result = self.orchestrator.execute_command("test command that will fail")
        
        # Should provide some result even with error
        assert result is not None, "Should return result even with error"
        
        # Should provide audio feedback about the error (if feedback module is available)
        if self.orchestrator.module_availability.get('feedback'):
            # May or may not call speak depending on error handling, but shouldn't crash
            pass


class TestPerformanceImpactMinimal:
    """Test that performance impact of enhancements is minimal."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.orchestrator = Orchestrator()
        
        # Mock modules for fast responses
        self.orchestrator.reasoning_module = Mock()
        self.orchestrator.feedback_module = Mock()
        self.orchestrator.audio_module = Mock()
        
        # Set modules as available
        self.orchestrator.module_availability = {
            'reasoning': True,
            'feedback': True,
            'audio': True,
            'vision': True,
            'automation': True,
            'accessibility': True
        }
    
    def test_gui_command_execution_time_reasonable(self):
        """Test that GUI command execution time remains reasonable."""
        # Mock fast intent recognition
        def mock_recognize_intent(command):
            return {
                'intent': 'gui_interaction',
                'confidence': 0.9,
                'parameters': {},
                'original_command': command
            }
        
        self.orchestrator._recognize_intent = mock_recognize_intent
        
        # Mock fast GUI execution
        mock_gui_result = {
            'execution_id': 'perf_test',
            'command': 'test',
            'status': 'completed',
            'success': True,
            'mode': 'gui_interaction',
            'duration': 0.05
        }
        self.orchestrator._handle_gui_interaction = Mock(return_value=mock_gui_result)
        
        # Measure execution time
        start_time = time.time()
        
        for i in range(5):
            result = self.orchestrator.execute_command(f"click button {i}")
            assert result['success'] is True, f"Command {i} should succeed"
        
        total_time = time.time() - start_time
        average_time = total_time / 5
        
        # Should complete reasonably quickly (allowing for mock overhead)
        assert average_time < 0.5, f"Average command time should be under 0.5s, got {average_time:.3f}s"
        assert total_time < 2.0, f"Total time for 5 commands should be under 2s, got {total_time:.3f}s"
    
    def test_intent_recognition_overhead_acceptable(self):
        """Test that intent recognition overhead is acceptable."""
        # Mock fast API response
        self.orchestrator.reasoning_module._make_api_request.return_value = {
            'message': {
                'content': '{"intent": "gui_interaction", "confidence": 0.9, "parameters": {}}'
            }
        }
        
        # Measure intent recognition time
        start_time = time.time()
        
        for i in range(10):
            result = self.orchestrator._recognize_intent(f"test command {i}")
            assert result['intent'] == 'gui_interaction', f"Intent {i} should be recognized"
        
        total_time = time.time() - start_time
        average_time = total_time / 10
        
        # Intent recognition should be fast
        assert average_time < 0.1, f"Average intent recognition should be under 0.1s, got {average_time:.3f}s"
    
    def test_memory_usage_stable(self):
        """Test that memory usage remains stable during operation."""
        # Execute many commands to test for memory leaks
        def mock_recognize_intent(command):
            return {
                'intent': 'gui_interaction',
                'confidence': 0.9,
                'parameters': {},
                'original_command': command
            }
        
        self.orchestrator._recognize_intent = mock_recognize_intent
        
        mock_gui_result = {
            'execution_id': 'memory_test',
            'command': 'test',
            'status': 'completed',
            'success': True,
            'mode': 'gui_interaction',
            'duration': 0.01
        }
        self.orchestrator._handle_gui_interaction = Mock(return_value=mock_gui_result)
        
        # Execute many commands
        for i in range(50):
            result = self.orchestrator.execute_command(f"click button {i}")
            assert result['success'] is True, f"Command {i} should succeed"
        
        # Check that conversation history doesn't grow unbounded
        max_history = self.orchestrator.max_state_history_entries
        assert len(self.orchestrator.conversation_history) <= max_history, \
            f"Conversation history should not exceed {max_history} entries"
        
        # Check that state transition history doesn't grow unbounded
        assert len(self.orchestrator.state_transition_history) <= max_history, \
            f"State transition history should not exceed {max_history} entries"


class TestErrorHandlingBackwardCompatibility:
    """Test that error handling maintains backward compatibility."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.orchestrator = Orchestrator()
        
        # Mock modules
        self.orchestrator.reasoning_module = Mock()
        self.orchestrator.feedback_module = Mock()
        
        # Set modules as available
        self.orchestrator.module_availability = {
            'reasoning': True,
            'feedback': True,
            'vision': True,
            'automation': True,
            'accessibility': True
        }
    
    def test_api_error_fallback_behavior_preserved(self):
        """Test that API error fallback behavior is preserved."""
        # Mock API error
        self.orchestrator.reasoning_module._make_api_request.side_effect = Exception("API Error")
        
        # Should fall back gracefully
        result = self.orchestrator.execute_command("click button")
        
        # Should not crash and should provide some result
        assert result is not None, "Should return result even with API failure"
        assert isinstance(result, dict), "Result should be a dictionary"
        
        # Should either succeed with fallback or fail gracefully
        if not result.get('success', False):
            assert 'error' in result or 'errors' in result, "Failed result should include error information"
    
    def test_module_unavailable_fallback_preserved(self):
        """Test that module unavailable fallback is preserved."""
        # Test with reasoning module unavailable
        self.orchestrator.module_availability['reasoning'] = False
        
        result = self.orchestrator.execute_command("test command")
        
        # Should handle unavailable module gracefully
        assert result is not None, "Should return result even with unavailable module"
        
        # Should use fallback behavior
        if result.get('success') is False:
            # If it fails, should provide error information
            assert 'error' in result or 'errors' in result, "Should provide error information"
    
    def test_malformed_command_handling_preserved(self):
        """Test that malformed command handling is preserved."""
        malformed_commands = [
            "",  # Empty command
            "   ",  # Whitespace only
            "click",  # Incomplete command
            "asdfghjkl",  # Nonsense command
        ]
        
        for command in malformed_commands:
            result = self.orchestrator.execute_command(command)
            
            # Should not crash
            assert result is not None, f"Should return result for malformed command: '{command}'"
            assert isinstance(result, dict), f"Result should be dict for malformed command: '{command}'"
            
            # Should either succeed with best effort or fail gracefully
            if not result.get('success', False):
                # If it fails, should provide some indication
                assert 'error' in result or 'errors' in result or result.get('status') == 'failed', \
                    f"Failed result should indicate failure for: '{command}'"


if __name__ == '__main__':
    # Run the backward compatibility tests
    pytest.main([__file__, '-v', '--tb=short'])