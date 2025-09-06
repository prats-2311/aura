#!/usr/bin/env python3
"""
Complete workflow tests for deferred action functionality.

This test suite validates complete deferred action workflows from initiation
to completion, including:
- Content generation and validation
- Mouse listener integration and coordination
- User interaction simulation
- Error recovery and timeout handling
- State transitions and cleanup

Requirements tested: 8.1, 8.2, 9.3, 9.4
"""

import pytest
import sys
import os
import time
import threading
from unittest.mock import Mock, patch, MagicMock, call

# Add the parent directory to the path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator import Orchestrator
from utils.mouse_listener import GlobalMouseListener, is_mouse_listener_available


class TestDeferredActionCompleteWorkflows:
    """Test complete deferred action workflows from start to finish."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.orchestrator = Orchestrator()
        
        # Mock all modules
        self.orchestrator.reasoning_module = Mock()
        self.orchestrator.feedback_module = Mock()
        self.orchestrator.audio_module = Mock()
        self.orchestrator.automation_module = Mock()
        self.orchestrator.vision_module = Mock()
        self.orchestrator.accessibility_module = Mock()
        
        # Set all modules as available
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
    def test_code_generation_workflow_complete(self, mock_listener_class, mock_availability):
        """Test complete code generation workflow."""
        # Setup mock mouse listener
        mock_listener = Mock()
        mock_listener_class.return_value = mock_listener
        mock_listener.get_last_click_coordinates.return_value = (400, 250)
        
        # Mock content generation
        generated_code = '''def fibonacci(n):
    """Calculate fibonacci number recursively."""
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# Example usage
print(fibonacci(10))'''
        
        self.orchestrator.reasoning_module.reason.return_value = {
            'response': generated_code
        }
        
        # Mock automation module
        self.orchestrator.automation_module.click.return_value = {'success': True}
        self.orchestrator.automation_module.type_text.return_value = {'success': True}
        
        # Step 1: Initiate deferred action
        intent_data = {
            'intent': 'deferred_action',
            'parameters': {
                'target': 'write a fibonacci function in Python with example usage',
                'content_type': 'code'
            },
            'original_command': 'write a fibonacci function in Python with example usage'
        }
        
        result = self.orchestrator._handle_deferred_action_request("workflow-001", intent_data)
        
        # Verify initiation
        assert result['status'] == 'waiting_for_user_action', "Should be waiting for user action"
        assert result['success'] is True, "Initiation should succeed"
        assert 'content_preview' in result, "Should provide content preview"
        assert len(result['content_preview']) > 0, "Content preview should not be empty"
        
        # Verify state
        assert self.orchestrator.is_waiting_for_user_action is True, "Should be in waiting state"
        assert self.orchestrator.pending_action_payload is not None, "Should have pending content"
        assert self.orchestrator.deferred_action_type == 'type', "Action type should be 'type'"
        
        # Verify content generation was called
        self.orchestrator.reasoning_module.reason.assert_called_once()
        
        # Verify mouse listener was started
        mock_listener.start.assert_called_once()
        
        # Verify audio feedback for instructions
        self.orchestrator.feedback_module.speak.assert_called()
        speak_calls = [call[0][0] for call in self.orchestrator.feedback_module.speak.call_args_list]
        assert any('click' in call.lower() for call in speak_calls), "Should provide click instructions"
        
        # Step 2: Simulate user click
        self.orchestrator._on_deferred_action_trigger("workflow-001")
        
        # Verify execution
        mock_listener.get_last_click_coordinates.assert_called()
        self.orchestrator.automation_module.click.assert_called_with(400, 250)
        
        # Verify content was typed
        type_call_args = self.orchestrator.automation_module.type_text.call_args
        typed_content = type_call_args[0][0]
        assert 'fibonacci' in typed_content, "Should type the generated fibonacci function"
        assert 'def fibonacci(n):' in typed_content, "Should include function definition"
        
        # Verify state cleanup
        assert self.orchestrator.is_waiting_for_user_action is False, "Should not be waiting after completion"
        assert self.orchestrator.pending_action_payload is None, "Payload should be cleared"
        assert self.orchestrator.deferred_action_type is None, "Action type should be cleared"
        
        # Verify mouse listener was stopped
        mock_listener.stop.assert_called()
        
        # Verify success feedback
        success_calls = [call[0][0] for call in self.orchestrator.feedback_module.speak.call_args_list]
        assert any('completed' in call.lower() or 'done' in call.lower() for call in success_calls), \
            "Should provide completion feedback"
    
    @patch('utils.mouse_listener.is_mouse_listener_available', return_value=True)
    @patch('utils.mouse_listener.GlobalMouseListener')
    def test_html_generation_workflow_complete(self, mock_listener_class, mock_availability):
        """Test complete HTML generation workflow."""
        mock_listener = Mock()
        mock_listener_class.return_value = mock_listener
        mock_listener.get_last_click_coordinates.return_value = (300, 400)
        
        # Mock HTML content generation
        generated_html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Contact Form</title>
</head>
<body>
    <form id="contact-form">
        <label for="name">Name:</label>
        <input type="text" id="name" name="name" required>
        
        <label for="email">Email:</label>
        <input type="email" id="email" name="email" required>
        
        <label for="message">Message:</label>
        <textarea id="message" name="message" required></textarea>
        
        <button type="submit">Send Message</button>
    </form>
</body>
</html>'''
        
        self.orchestrator.reasoning_module.reason.return_value = {
            'response': generated_html
        }
        
        # Mock automation
        self.orchestrator.automation_module.click.return_value = {'success': True}
        self.orchestrator.automation_module.type_text.return_value = {'success': True}
        
        # Initiate HTML generation
        intent_data = {
            'intent': 'deferred_action',
            'parameters': {
                'target': 'create HTML for a contact form with name, email, and message fields',
                'content_type': 'html'
            },
            'original_command': 'create HTML for a contact form'
        }
        
        result = self.orchestrator._handle_deferred_action_request("html-001", intent_data)
        
        # Verify initiation
        assert result['success'] is True, "HTML generation should initiate successfully"
        assert self.orchestrator.pending_action_payload is not None, "Should have HTML content"
        
        # Verify content contains expected HTML elements
        content = self.orchestrator.pending_action_payload
        assert '<!DOCTYPE html>' in content, "Should generate proper HTML document"
        assert '<form' in content, "Should include form element"
        assert 'name="name"' in content, "Should include name field"
        assert 'name="email"' in content, "Should include email field"
        assert 'name="message"' in content, "Should include message field"
        
        # Complete the workflow
        self.orchestrator._on_deferred_action_trigger("html-001")
        
        # Verify HTML was typed
        type_call_args = self.orchestrator.automation_module.type_text.call_args
        typed_content = type_call_args[0][0]
        assert '<!DOCTYPE html>' in typed_content, "Should type the complete HTML"
        assert '<form' in typed_content, "Should type the form structure"
    
    @patch('utils.mouse_listener.is_mouse_listener_available', return_value=True)
    @patch('utils.mouse_listener.GlobalMouseListener')
    def test_css_generation_workflow_complete(self, mock_listener_class, mock_availability):
        """Test complete CSS generation workflow."""
        mock_listener = Mock()
        mock_listener_class.return_value = mock_listener
        mock_listener.get_last_click_coordinates.return_value = (500, 200)
        
        # Mock CSS content generation
        generated_css = '''.navigation {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 2rem;
    background-color: #333;
    color: white;
}

.nav-logo {
    font-size: 1.5rem;
    font-weight: bold;
}

.nav-links {
    display: flex;
    list-style: none;
    gap: 2rem;
    margin: 0;
    padding: 0;
}

.nav-links a {
    color: white;
    text-decoration: none;
    transition: color 0.3s ease;
}

.nav-links a:hover {
    color: #007bff;
}'''
        
        self.orchestrator.reasoning_module.reason.return_value = {
            'response': generated_css
        }
        
        # Mock automation
        self.orchestrator.automation_module.click.return_value = {'success': True}
        self.orchestrator.automation_module.type_text.return_value = {'success': True}
        
        # Initiate CSS generation
        intent_data = {
            'intent': 'deferred_action',
            'parameters': {
                'target': 'write CSS for a responsive navigation menu with hover effects',
                'content_type': 'css'
            },
            'original_command': 'write CSS for a responsive navigation menu'
        }
        
        result = self.orchestrator._handle_deferred_action_request("css-001", intent_data)
        
        # Verify initiation
        assert result['success'] is True, "CSS generation should initiate successfully"
        
        # Verify content contains expected CSS
        content = self.orchestrator.pending_action_payload
        assert '.navigation' in content, "Should include navigation class"
        assert 'display: flex' in content, "Should include flexbox layout"
        assert 'hover' in content, "Should include hover effects"
        
        # Complete the workflow
        self.orchestrator._on_deferred_action_trigger("css-001")
        
        # Verify CSS was typed
        type_call_args = self.orchestrator.automation_module.type_text.call_args
        typed_content = type_call_args[0][0]
        assert '.navigation' in typed_content, "Should type the CSS classes"
        assert 'display: flex' in typed_content, "Should type the CSS properties"
    
    @patch('utils.mouse_listener.is_mouse_listener_available', return_value=True)
    @patch('utils.mouse_listener.GlobalMouseListener')
    def test_workflow_with_content_validation(self, mock_listener_class, mock_availability):
        """Test workflow with content validation and quality checks."""
        mock_listener = Mock()
        mock_listener_class.return_value = mock_listener
        mock_listener.get_last_click_coordinates.return_value = (350, 300)
        
        # Mock content generation with validation
        generated_content = '''function validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function validateForm(formData) {
    const errors = [];
    
    if (!formData.name || formData.name.trim().length < 2) {
        errors.push("Name must be at least 2 characters long");
    }
    
    if (!validateEmail(formData.email)) {
        errors.push("Please enter a valid email address");
    }
    
    if (!formData.message || formData.message.trim().length < 10) {
        errors.push("Message must be at least 10 characters long");
    }
    
    return {
        isValid: errors.length === 0,
        errors: errors
    };
}'''
        
        self.orchestrator.reasoning_module.reason.return_value = {
            'response': generated_content
        }
        
        # Mock automation
        self.orchestrator.automation_module.click.return_value = {'success': True}
        self.orchestrator.automation_module.type_text.return_value = {'success': True}
        
        # Initiate JavaScript validation generation
        intent_data = {
            'intent': 'deferred_action',
            'parameters': {
                'target': 'write JavaScript form validation functions with email validation and error handling',
                'content_type': 'javascript'
            },
            'original_command': 'write JavaScript form validation functions'
        }
        
        result = self.orchestrator._handle_deferred_action_request("js-validation-001", intent_data)
        
        # Verify initiation and content quality
        assert result['success'] is True, "JavaScript generation should succeed"
        
        content = self.orchestrator.pending_action_payload
        assert 'function validateEmail' in content, "Should include email validation function"
        assert 'function validateForm' in content, "Should include form validation function"
        assert 'emailRegex' in content, "Should include email regex validation"
        assert 'errors.push' in content, "Should include error handling"
        
        # Verify content preview is meaningful
        preview = result['content_preview']
        assert len(preview) > 50, "Preview should be substantial"
        assert 'validation' in preview.lower(), "Preview should mention validation"
        
        # Complete workflow
        self.orchestrator._on_deferred_action_trigger("js-validation-001")
        
        # Verify complete content was typed
        type_call_args = self.orchestrator.automation_module.type_text.call_args
        typed_content = type_call_args[0][0]
        assert len(typed_content) > 200, "Should type substantial content"
        assert 'function validateEmail' in typed_content, "Should type validation functions"
    
    @patch('utils.mouse_listener.is_mouse_listener_available', return_value=True)
    @patch('utils.mouse_listener.GlobalMouseListener')
    def test_workflow_interruption_and_cleanup(self, mock_listener_class, mock_availability):
        """Test workflow interruption by new commands and proper cleanup."""
        mock_listener = Mock()
        mock_listener_class.return_value = mock_listener
        
        # Mock content generation
        self.orchestrator.reasoning_module.reason.return_value = {
            'response': 'print("Hello, World!")'
        }
        
        # Initiate deferred action
        intent_data = {
            'intent': 'deferred_action',
            'parameters': {
                'target': 'write a hello world program',
                'content_type': 'code'
            },
            'original_command': 'write a hello world program'
        }
        
        result = self.orchestrator._handle_deferred_action_request("interrupt-001", intent_data)
        
        # Verify deferred action is active
        assert result['success'] is True, "Deferred action should start"
        assert self.orchestrator.is_waiting_for_user_action is True, "Should be waiting"
        assert mock_listener.start.called, "Mouse listener should be started"
        
        # Mock intent recognition for interrupting command
        def mock_recognize_intent(command):
            return {
                'intent': 'gui_interaction',
                'confidence': 0.9,
                'parameters': {},
                'original_command': command
            }
        
        self.orchestrator._recognize_intent = mock_recognize_intent
        
        # Mock GUI handler
        mock_gui_result = {
            'execution_id': 'interrupt_gui',
            'command': 'click button',
            'status': 'completed',
            'success': True,
            'mode': 'gui_interaction',
            'duration': 0.1
        }
        self.orchestrator._handle_gui_interaction = Mock(return_value=mock_gui_result)
        
        # Execute interrupting command
        interrupt_result = self.orchestrator.execute_command("click on submit button")
        
        # Verify interruption and cleanup
        assert self.orchestrator.is_waiting_for_user_action is False, "Should not be waiting after interruption"
        assert self.orchestrator.pending_action_payload is None, "Payload should be cleared"
        assert self.orchestrator.deferred_action_type is None, "Action type should be cleared"
        
        # Verify mouse listener was stopped
        mock_listener.stop.assert_called()
        
        # Verify interrupting command was executed
        self.orchestrator._handle_gui_interaction.assert_called()
        assert interrupt_result['success'] is True, "Interrupting command should succeed"
    
    @patch('utils.mouse_listener.is_mouse_listener_available', return_value=True)
    @patch('utils.mouse_listener.GlobalMouseListener')
    def test_workflow_timeout_handling(self, mock_listener_class, mock_availability):
        """Test workflow timeout handling and cleanup."""
        mock_listener = Mock()
        mock_listener_class.return_value = mock_listener
        
        # Mock content generation
        self.orchestrator.reasoning_module.reason.return_value = {
            'response': 'console.log("Test timeout");'
        }
        
        # Set short timeout for testing
        original_timeout = self.orchestrator.deferred_action_timeout_seconds
        self.orchestrator.deferred_action_timeout_seconds = 0.1  # 100ms timeout
        
        try:
            # Initiate deferred action
            intent_data = {
                'intent': 'deferred_action',
                'parameters': {
                    'target': 'write a console log statement',
                    'content_type': 'javascript'
                },
                'original_command': 'write a console log statement'
            }
            
            result = self.orchestrator._handle_deferred_action_request("timeout-001", intent_data)
            
            # Verify deferred action started
            assert result['success'] is True, "Deferred action should start"
            assert self.orchestrator.is_waiting_for_user_action is True, "Should be waiting"
            
            # Wait for timeout to occur
            time.sleep(0.2)  # Wait longer than timeout
            
            # Manually trigger timeout handling (in real scenario this would be automatic)
            self.orchestrator._handle_deferred_action_timeout("timeout-001")
            
            # Verify timeout cleanup
            assert self.orchestrator.is_waiting_for_user_action is False, "Should not be waiting after timeout"
            assert self.orchestrator.pending_action_payload is None, "Payload should be cleared after timeout"
            
            # Verify mouse listener was stopped
            mock_listener.stop.assert_called()
            
            # Verify timeout feedback was provided
            self.orchestrator.feedback_module.speak.assert_called()
            speak_calls = [call[0][0] for call in self.orchestrator.feedback_module.speak.call_args_list]
            assert any('timeout' in call.lower() or 'cancelled' in call.lower() for call in speak_calls), \
                "Should provide timeout feedback"
            
        finally:
            # Restore original timeout
            self.orchestrator.deferred_action_timeout_seconds = original_timeout
    
    def test_workflow_content_generation_error_handling(self):
        """Test error handling during content generation phase."""
        # Mock reasoning module to fail
        self.orchestrator.reasoning_module.reason.side_effect = Exception("Content generation failed")
        
        intent_data = {
            'intent': 'deferred_action',
            'parameters': {
                'target': 'write some code that will fail to generate',
                'content_type': 'code'
            },
            'original_command': 'write some code that will fail'
        }
        
        result = self.orchestrator._handle_deferred_action_request("error-001", intent_data)
        
        # Verify error handling
        assert result['status'] == 'failed', "Should indicate failure"
        assert result['success'] is False, "Should not succeed"
        assert 'error' in result, "Should include error information"
        assert 'Content generation failed' in str(result['error']), "Should include specific error"
        
        # Verify state was not set to waiting
        assert self.orchestrator.is_waiting_for_user_action is False, "Should not be waiting on error"
        assert self.orchestrator.pending_action_payload is None, "Should not have payload on error"
        
        # Verify error feedback was provided
        self.orchestrator.feedback_module.speak.assert_called()
        speak_calls = [call[0][0] for call in self.orchestrator.feedback_module.speak.call_args_list]
        assert any('error' in call.lower() or 'failed' in call.lower() for call in speak_calls), \
            "Should provide error feedback"
    
    @patch('utils.mouse_listener.is_mouse_listener_available', return_value=False)
    def test_workflow_mouse_listener_unavailable(self, mock_availability):
        """Test workflow when mouse listener is unavailable."""
        # Mock content generation
        self.orchestrator.reasoning_module.reason.return_value = {
            'response': 'def test(): pass'
        }
        
        intent_data = {
            'intent': 'deferred_action',
            'parameters': {
                'target': 'write a test function',
                'content_type': 'code'
            },
            'original_command': 'write a test function'
        }
        
        result = self.orchestrator._handle_deferred_action_request("no-mouse-001", intent_data)
        
        # Should handle unavailable mouse listener gracefully
        assert result['status'] in ['failed', 'completed'], "Should handle mouse listener unavailability"
        
        if result['status'] == 'failed':
            assert 'mouse listener' in result.get('error', '').lower(), "Should mention mouse listener issue"
        elif result['status'] == 'completed':
            # If it falls back to immediate execution, that's acceptable
            assert result['success'] is True, "Fallback execution should succeed"
    
    @patch('utils.mouse_listener.is_mouse_listener_available', return_value=True)
    @patch('utils.mouse_listener.GlobalMouseListener')
    def test_workflow_automation_error_handling(self, mock_listener_class, mock_availability):
        """Test error handling during automation execution phase."""
        mock_listener = Mock()
        mock_listener_class.return_value = mock_listener
        mock_listener.get_last_click_coordinates.return_value = (100, 100)
        
        # Mock content generation success
        self.orchestrator.reasoning_module.reason.return_value = {
            'response': 'print("Test automation error")'
        }
        
        # Mock automation failure
        self.orchestrator.automation_module.click.return_value = {'success': False, 'error': 'Click failed'}
        self.orchestrator.automation_module.type_text.side_effect = Exception("Type text failed")
        
        # Initiate deferred action
        intent_data = {
            'intent': 'deferred_action',
            'parameters': {
                'target': 'write a test print statement',
                'content_type': 'code'
            },
            'original_command': 'write a test print statement'
        }
        
        result = self.orchestrator._handle_deferred_action_request("auto-error-001", intent_data)
        
        # Verify deferred action started
        assert result['success'] is True, "Deferred action should start despite future automation error"
        
        # Trigger execution (this should handle automation errors)
        self.orchestrator._on_deferred_action_trigger("auto-error-001")
        
        # Verify state cleanup even with automation errors
        assert self.orchestrator.is_waiting_for_user_action is False, "Should clean up state even on automation error"
        assert self.orchestrator.pending_action_payload is None, "Should clear payload even on automation error"
        
        # Verify mouse listener was stopped
        mock_listener.stop.assert_called()
        
        # Verify error feedback was provided
        self.orchestrator.feedback_module.speak.assert_called()
        speak_calls = [call[0][0] for call in self.orchestrator.feedback_module.speak.call_args_list]
        # Should have both instruction and error feedback
        assert len(speak_calls) >= 2, "Should provide both instruction and error feedback"


if __name__ == '__main__':
    # Run the deferred action workflow tests
    pytest.main([__file__, '-v', '--tb=short'])