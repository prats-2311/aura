#!/usr/bin/env python3
"""
Integration tests for Explain Selected Text feature

Tests the complete workflow including intent recognition, text capture,
explanation generation, and audio feedback integration.

Requirements: 1.1, 1.2, 3.1, 3.2, 3.3, 4.1, 4.2, 4.3, 4.4, 4.5, 5.1, 5.3, 5.4
"""

import pytest
import unittest.mock as mock
from unittest.mock import Mock, MagicMock, patch, call
import time
from typing import Dict, Any, Optional

# Import modules under test
from handlers.explain_selection_handler import ExplainSelectionHandler
from orchestrator import Orchestrator


class TestExplainSelectedTextIntegration:
    """Integration tests for the complete explain selected text workflow."""
    
    @pytest.fixture
    def mock_orchestrator(self):
        """Mock orchestrator with all required modules."""
        orchestrator = Mock(spec=Orchestrator)
        
        # Mock accessibility module
        orchestrator.accessibility_module = Mock()
        orchestrator.accessibility_module.get_selected_text.return_value = "Sample selected text"
        
        # Mock reasoning module
        orchestrator.reasoning_module = Mock()
        orchestrator.reasoning_module.process_query.return_value = "This is an explanation of the selected text."
        
        # Mock feedback module
        orchestrator.feedback_module = Mock()
        orchestrator.feedback_module.play = Mock()
        orchestrator.feedback_module.provide_conversational_feedback = Mock()
        orchestrator.feedback_module.speak = Mock()
        
        # Mock audio module
        orchestrator.audio_module = Mock()
        orchestrator.audio_module.text_to_speech = Mock()
        
        return orchestrator
    
    @pytest.fixture
    def explain_handler(self, mock_orchestrator):
        """Create ExplainSelectionHandler with mocked dependencies."""
        return ExplainSelectionHandler(mock_orchestrator)

    def test_complete_workflow_success(self, explain_handler, mock_orchestrator):
        """Test complete successful workflow from command to spoken explanation."""
        # Arrange
        command = "explain this"
        context = {
            "intent": {
                "intent": "explain_selected_text",
                "confidence": 0.95,
                "parameters": {"action_type": "explain_text"}
            },
            "execution_id": "test-123",
            "timestamp": time.time()
        }
        
        selected_text = "This is a function that calculates the sum of two numbers."
        explanation = "This code defines a function that takes two parameters and returns their sum."
        
        # Mock successful text capture
        mock_orchestrator.accessibility_module.get_selected_text.return_value = selected_text
        
        # Mock successful explanation generation
        mock_orchestrator.reasoning_module.process_query.return_value = explanation
        
        # Act
        result = explain_handler.handle(command, context)
        
        # Assert
        assert result["success"] == True
        assert result["method"] == "explain_selected_text"
        assert "explanation" in result
        
        # Verify text capture was called
        mock_orchestrator.accessibility_module.get_selected_text.assert_called_once()
        
        # Verify explanation generation was called
        mock_orchestrator.reasoning_module.process_query.assert_called_once()
        
        # Verify audio feedback was provided
        assert (mock_orchestrator.feedback_module.provide_conversational_feedback.called or
                mock_orchestrator.feedback_module.speak.called or
                mock_orchestrator.audio_module.text_to_speech.called)

    def test_workflow_no_text_selected(self, explain_handler, mock_orchestrator):
        """Test workflow when no text is selected."""
        # Arrange
        command = "explain this"
        context = {"intent": {"intent": "explain_selected_text"}}
        
        # Mock no text selected
        mock_orchestrator.accessibility_module.get_selected_text.return_value = None
        
        # Act
        result = explain_handler.handle(command, context)
        
        # Assert
        assert result["success"] == False
        assert result["method"] == "text_capture_failed"
        assert "no selected text" in result["message"].lower()
        
        # Verify text capture was attempted
        mock_orchestrator.accessibility_module.get_selected_text.assert_called_once()
        
        # Verify reasoning module was not called
        mock_orchestrator.reasoning_module.process_query.assert_not_called()

    def test_workflow_explanation_generation_failure(self, explain_handler, mock_orchestrator):
        """Test workflow when explanation generation fails."""
        # Arrange
        command = "explain this"
        context = {"intent": {"intent": "explain_selected_text"}}
        selected_text = "Some selected text"
        
        # Mock successful text capture
        mock_orchestrator.accessibility_module.get_selected_text.return_value = selected_text
        
        # Mock explanation generation failure
        mock_orchestrator.reasoning_module.process_query.return_value = None
        
        # Act
        result = explain_handler.handle(command, context)
        
        # Assert
        assert result["success"] == False
        assert result["method"] == "explanation_generation_failed"
        assert "issue generating" in result["message"].lower()
        
        # Verify both text capture and reasoning were called
        mock_orchestrator.accessibility_module.get_selected_text.assert_called_once()
        mock_orchestrator.reasoning_module.process_query.assert_called_once()

    def test_workflow_with_different_content_types(self, explain_handler, mock_orchestrator):
        """Test workflow with different types of content."""
        test_cases = [
            {
                "text": "def calculate_sum(a, b):\n    return a + b",
                "content_type": "code snippet",
                "expected_explanation": "This code defines a function that calculates the sum of two numbers."
            },
            {
                "text": "The API endpoint accepts POST requests with JSON payload",
                "content_type": "technical documentation", 
                "expected_explanation": "This describes a technical interface that receives data in JSON format."
            },
            {
                "text": "The research methodology involved randomized controlled trials",
                "content_type": "academic/scientific text",
                "expected_explanation": "This refers to a scientific research approach using controlled experiments."
            }
        ]
        
        for case in test_cases:
            # Arrange
            command = "explain this"
            context = {"intent": {"intent": "explain_selected_text"}}
            
            mock_orchestrator.accessibility_module.get_selected_text.return_value = case["text"]
            mock_orchestrator.reasoning_module.process_query.return_value = case["expected_explanation"]
            
            # Act
            result = explain_handler.handle(command, context)
            
            # Assert
            assert result["success"] == True
            assert result["selected_text_length"] == len(case["text"])

    def test_workflow_performance_tracking(self, explain_handler, mock_orchestrator):
        """Test that workflow tracks performance metrics."""
        # Arrange
        command = "explain this"
        context = {"intent": {"intent": "explain_selected_text"}}
        selected_text = "Performance test text"
        explanation = "This is a performance test explanation."
        
        mock_orchestrator.accessibility_module.get_selected_text.return_value = selected_text
        mock_orchestrator.reasoning_module.process_query.return_value = explanation
        
        # Act
        start_time = time.time()
        result = explain_handler.handle(command, context)
        end_time = time.time()
        
        # Assert
        assert result["success"] == True
        assert "capture_time" in result
        assert "explanation_time" in result
        assert result["capture_time"] >= 0
        assert result["explanation_time"] >= 0
        
        # Verify total execution time is reasonable
        total_time = end_time - start_time
        assert total_time < 5.0  # Should complete within 5 seconds for mocked calls

    def test_workflow_audio_feedback_integration(self, explain_handler, mock_orchestrator):
        """Test integration with audio feedback systems."""
        # Arrange
        command = "explain this"
        context = {"intent": {"intent": "explain_selected_text"}}
        selected_text = "Audio feedback test text"
        explanation = "This is an explanation for audio feedback testing."
        
        mock_orchestrator.accessibility_module.get_selected_text.return_value = selected_text
        mock_orchestrator.reasoning_module.process_query.return_value = explanation
        
        # Act
        result = explain_handler.handle(command, context)
        
        # Assert
        assert result["success"] == True
        
        # Verify thinking sound was played
        mock_orchestrator.feedback_module.play.assert_called()
        thinking_calls = [call for call in mock_orchestrator.feedback_module.play.call_args_list 
                         if call[0][0] == "thinking"]
        assert len(thinking_calls) > 0
        
        # Verify explanation was spoken
        feedback_called = (mock_orchestrator.feedback_module.provide_conversational_feedback.called or
                          mock_orchestrator.feedback_module.speak.called or
                          mock_orchestrator.audio_module.text_to_speech.called)
        assert feedback_called

    def test_workflow_error_audio_feedback(self, explain_handler, mock_orchestrator):
        """Test audio feedback for error scenarios."""
        # Arrange
        command = "explain this"
        context = {"intent": {"intent": "explain_selected_text"}}
        
        # Mock text capture failure
        mock_orchestrator.accessibility_module.get_selected_text.return_value = None
        
        # Act
        result = explain_handler.handle(command, context)
        
        # Assert
        assert result["success"] == False
        
        # Verify error feedback was provided (through any available audio method)
        feedback_called = (mock_orchestrator.feedback_module.provide_conversational_feedback.called or
                          mock_orchestrator.feedback_module.speak.called or
                          mock_orchestrator.audio_module.text_to_speech.called)
        assert feedback_called

    @patch('config.EXPLAIN_TEXT_PROMPT')
    def test_workflow_with_custom_prompt_template(self, mock_prompt, explain_handler, mock_orchestrator):
        """Test workflow with custom explanation prompt template."""
        # Arrange
        mock_prompt.format.return_value = "Custom prompt: {selected_text}"
        command = "explain this"
        context = {"intent": {"intent": "explain_selected_text"}}
        selected_text = "Custom prompt test text"
        explanation = "Custom explanation response"
        
        mock_orchestrator.accessibility_module.get_selected_text.return_value = selected_text
        mock_orchestrator.reasoning_module.process_query.return_value = explanation
        
        # Act
        result = explain_handler.handle(command, context)
        
        # Assert
        assert result["success"] == True
        mock_orchestrator.reasoning_module.process_query.assert_called_once()

    def test_workflow_with_very_long_text(self, explain_handler, mock_orchestrator):
        """Test workflow with very long selected text."""
        # Arrange
        command = "explain this"
        context = {"intent": {"intent": "explain_selected_text"}}
        long_text = "This is a very long text selection. " * 300  # ~10,500 characters
        explanation = "This is a summary of the long text content."
        
        mock_orchestrator.accessibility_module.get_selected_text.return_value = long_text
        mock_orchestrator.reasoning_module.process_query.return_value = explanation
        
        # Act
        result = explain_handler.handle(command, context)
        
        # Assert
        assert result["success"] == True
        assert result["selected_text_length"] == len(long_text)
        
        # Verify reasoning module was called with potentially truncated text
        mock_orchestrator.reasoning_module.process_query.assert_called_once()
        call_args = mock_orchestrator.reasoning_module.process_query.call_args
        # The prompt should contain the text (possibly truncated)
        assert call_args is not None

    def test_workflow_with_special_characters(self, explain_handler, mock_orchestrator):
        """Test workflow with special characters and Unicode."""
        # Arrange
        command = "explain this"
        context = {"intent": {"intent": "explain_selected_text"}}
        special_text = "Special chars: àáâãäå ñ 中文 🚀 ∑∆∏ <script>alert('test')</script>"
        explanation = "This text contains special characters and Unicode symbols."
        
        mock_orchestrator.accessibility_module.get_selected_text.return_value = special_text
        mock_orchestrator.reasoning_module.process_query.return_value = explanation
        
        # Act
        result = explain_handler.handle(command, context)
        
        # Assert
        assert result["success"] == True
        assert result["selected_text_length"] == len(special_text)

    def test_workflow_exception_handling(self, explain_handler, mock_orchestrator):
        """Test workflow exception handling."""
        # Arrange
        command = "explain this"
        context = {"intent": {"intent": "explain_selected_text"}}
        
        # Mock exception during text capture
        mock_orchestrator.accessibility_module.get_selected_text.side_effect = Exception("Test exception")
        
        # Act
        result = explain_handler.handle(command, context)
        
        # Assert
        assert result["success"] == False
        assert result["method"] == "exception_handling"
        assert "unexpected issue" in result["message"].lower()

    def test_workflow_statistics_tracking(self, explain_handler, mock_orchestrator):
        """Test that workflow tracks success/failure statistics."""
        # Arrange
        command = "explain this"
        context = {"intent": {"intent": "explain_selected_text"}}
        
        # Test successful execution
        mock_orchestrator.accessibility_module.get_selected_text.return_value = "Test text"
        mock_orchestrator.reasoning_module.process_query.return_value = "Test explanation"
        
        initial_attempts = explain_handler._explanation_attempts
        initial_successes = explain_handler._explanation_successes
        
        # Act
        result = explain_handler.handle(command, context)
        
        # Assert
        assert result["success"] == True
        assert explain_handler._explanation_attempts == initial_attempts + 1
        assert explain_handler._explanation_successes == initial_successes + 1

    def test_workflow_failure_statistics_tracking(self, explain_handler, mock_orchestrator):
        """Test that workflow tracks failure statistics."""
        # Arrange
        command = "explain this"
        context = {"intent": {"intent": "explain_selected_text"}}
        
        # Test text capture failure
        mock_orchestrator.accessibility_module.get_selected_text.return_value = None
        
        initial_attempts = explain_handler._explanation_attempts
        initial_failures = explain_handler._text_capture_failures
        
        # Act
        result = explain_handler.handle(command, context)
        
        # Assert
        assert result["success"] == False
        assert explain_handler._explanation_attempts == initial_attempts + 1
        assert explain_handler._text_capture_failures == initial_failures + 1

    def test_workflow_reasoning_failure_statistics(self, explain_handler, mock_orchestrator):
        """Test that workflow tracks reasoning failure statistics."""
        # Arrange
        command = "explain this"
        context = {"intent": {"intent": "explain_selected_text"}}
        
        # Test reasoning failure
        mock_orchestrator.accessibility_module.get_selected_text.return_value = "Test text"
        mock_orchestrator.reasoning_module.process_query.return_value = None
        
        initial_reasoning_failures = explain_handler._reasoning_failures
        
        # Act
        result = explain_handler.handle(command, context)
        
        # Assert
        assert result["success"] == False
        assert explain_handler._reasoning_failures == initial_reasoning_failures + 1

    def test_workflow_with_empty_explanation(self, explain_handler, mock_orchestrator):
        """Test workflow when explanation generation returns empty result."""
        # Arrange
        command = "explain this"
        context = {"intent": {"intent": "explain_selected_text"}}
        
        mock_orchestrator.accessibility_module.get_selected_text.return_value = "Test text"
        mock_orchestrator.reasoning_module.process_query.return_value = ""  # Empty explanation
        
        # Act
        result = explain_handler.handle(command, context)
        
        # Assert
        assert result["success"] == False
        assert result["method"] == "explanation_generation_failed"

    def test_workflow_with_invalid_command(self, explain_handler, mock_orchestrator):
        """Test workflow with invalid command."""
        # Arrange
        invalid_command = ""
        context = {"intent": {"intent": "explain_selected_text"}}
        
        # Act
        with patch.object(explain_handler, '_validate_command', return_value=False):
            result = explain_handler.handle(invalid_command, context)
        
        # Assert
        assert result["success"] == False
        assert result["method"] == "validation_failed"
        assert "valid explanation request" in result["message"].lower()

    def test_workflow_module_availability_checks(self, explain_handler, mock_orchestrator):
        """Test workflow behavior when modules are unavailable."""
        # Test accessibility module unavailable
        command = "explain this"
        context = {"intent": {"intent": "explain_selected_text"}}
        
        # Mock module unavailable
        with patch.object(explain_handler, '_get_module_safely', return_value=None):
            result = explain_handler.handle(command, context)
        
        # Should handle gracefully
        assert result["success"] == False