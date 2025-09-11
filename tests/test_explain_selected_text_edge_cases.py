#!/usr/bin/env python3
"""
Edge case tests for Explain Selected Text feature

Tests edge cases including no text selected, very long text, special characters,
different content types, and various failure scenarios.

Requirements: 1.2, 2.3, 2.4, 3.4, 3.5, 5.2, 5.5
"""

import pytest
import unittest.mock as mock
from unittest.mock import Mock, MagicMock, patch, call
import time
from typing import Dict, Any, Optional

# Import modules under test
from handlers.explain_selection_handler import ExplainSelectionHandler


class TestExplainSelectedTextEdgeCases:
    """Edge case tests for explain selected text functionality."""
    
    @pytest.fixture
    def mock_orchestrator(self):
        """Mock orchestrator with configurable module responses."""
        orchestrator = Mock()
        orchestrator.accessibility_module = Mock()
        orchestrator.reasoning_module = Mock()
        orchestrator.feedback_module = Mock()
        orchestrator.audio_module = Mock()
        return orchestrator
    
    @pytest.fixture
    def explain_handler(self, mock_orchestrator):
        """Create ExplainSelectionHandler with mocked dependencies."""
        return ExplainSelectionHandler(mock_orchestrator)

    def test_no_text_selected_scenarios(self, explain_handler, mock_orchestrator):
        """Test various no-text-selected scenarios."""
        command = "explain this"
        context = {"intent": {"intent": "explain_selected_text"}}
        
        no_text_scenarios = [
            None,           # Accessibility API returns None
            "",             # Empty string
            "   ",          # Whitespace only
            "\n\t\r",       # Various whitespace characters
        ]
        
        for scenario in no_text_scenarios:
            # Arrange
            mock_orchestrator.accessibility_module.get_selected_text.return_value = scenario
            
            # Act
            result = explain_handler.handle(command, context)
            
            # Assert
            assert result["success"] == False
            assert "no selected text" in result["message"].lower() or "couldn't find" in result["message"].lower()

    def test_very_long_text_scenarios(self, explain_handler, mock_orchestrator):
        """Test handling of very long text selections."""
        command = "explain this"
        context = {"intent": {"intent": "explain_selected_text"}}
        
        # Test different lengths of long text
        long_text_scenarios = [
            {
                "length": 1000,
                "description": "Medium long text",
                "should_succeed": True
            },
            {
                "length": 5000,
                "description": "Very long text at limit",
                "should_succeed": True
            },
            {
                "length": 10000,
                "description": "Extremely long text",
                "should_succeed": True  # Should be truncated
            },
            {
                "length": 50000,
                "description": "Massive text selection",
                "should_succeed": True  # Should be truncated
            }
        ]
        
        for scenario in long_text_scenarios:
            # Arrange
            long_text = "This is a test sentence. " * (scenario["length"] // 25)
            mock_orchestrator.accessibility_module.get_selected_text.return_value = long_text
            mock_orchestrator.reasoning_module.process_query.return_value = "This is a summary of the long text."
            
            # Act
            result = explain_handler.handle(command, context)
            
            # Assert
            if scenario["should_succeed"]:
                assert result["success"] == True
                assert result["selected_text_length"] <= len(long_text)
            else:
                assert result["success"] == False

    def test_special_characters_and_unicode(self, explain_handler, mock_orchestrator):
        """Test handling of special characters and Unicode content."""
        command = "explain this"
        context = {"intent": {"intent": "explain_selected_text"}}
        
        special_text_scenarios = [
            {
                "text": "àáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿ",
                "description": "Extended Latin characters"
            },
            {
                "text": "中文测试 日本語テスト 한국어 테스트",
                "description": "CJK characters"
            },
            {
                "text": "🚀🌟💡🔥⚡🎯🌈🎨🎭🎪",
                "description": "Emoji characters"
            },
            {
                "text": "∑∆∏∫∞≠≤≥±×÷√∂∇",
                "description": "Mathematical symbols"
            },
            {
                "text": "™®©℠℗§¶†‡•‰‱",
                "description": "Special symbols"
            },
            {
                "text": "<script>alert('xss')</script>",
                "description": "HTML/JavaScript content"
            },
            {
                "text": "SELECT * FROM users WHERE id = 1; DROP TABLE users;",
                "description": "SQL injection attempt"
            },
            {
                "text": "Line 1\nLine 2\r\nLine 3\tTabbed\n\nDouble newline",
                "description": "Various line breaks and tabs"
            }
        ]
        
        for scenario in special_text_scenarios:
            # Arrange
            mock_orchestrator.accessibility_module.get_selected_text.return_value = scenario["text"]
            mock_orchestrator.reasoning_module.process_query.return_value = f"This text contains {scenario['description']}."
            
            # Act
            result = explain_handler.handle(command, context)
            
            # Assert
            assert result["success"] == True, f"Failed for {scenario['description']}"
            assert result["selected_text_length"] == len(scenario["text"])

    def test_different_content_types_edge_cases(self, explain_handler, mock_orchestrator):
        """Test edge cases for different content types."""
        command = "explain this"
        context = {"intent": {"intent": "explain_selected_text"}}
        
        content_type_scenarios = [
            {
                "text": "def func():\n    pass\n\nclass MyClass:\n    def __init__(self):\n        self.value = None",
                "content_type": "code snippet",
                "description": "Complex Python code"
            },
            {
                "text": "function complexFunction(param1, param2) {\n    return param1.map(x => x * param2).filter(Boolean);\n}",
                "content_type": "code snippet", 
                "description": "Complex JavaScript code"
            },
            {
                "text": "The API endpoint /api/v1/users/{id}/preferences accepts PUT requests with Content-Type: application/json",
                "content_type": "technical documentation",
                "description": "API documentation"
            },
            {
                "text": "WHEREAS the parties hereto desire to enter into this Agreement, NOW THEREFORE, in consideration of the mutual covenants",
                "content_type": "legal/formal document",
                "description": "Legal text"
            },
            {
                "text": "The methodology employed a double-blind randomized controlled trial with n=500 participants across three treatment groups",
                "content_type": "academic/scientific text",
                "description": "Scientific methodology"
            },
            {
                "text": "Mixed content: def test(): return 'API endpoint /users accepts JSON' + research_methodology()",
                "content_type": "code snippet",  # Should detect as code due to def keyword
                "description": "Mixed content types"
            }
        ]
        
        for scenario in content_type_scenarios:
            # Arrange
            mock_orchestrator.accessibility_module.get_selected_text.return_value = scenario["text"]
            mock_orchestrator.reasoning_module.process_query.return_value = f"This {scenario['content_type']} does something specific."
            
            # Act
            result = explain_handler.handle(command, context)
            content_type = explain_handler._determine_content_type(scenario["text"])
            
            # Assert
            assert result["success"] == True, f"Failed for {scenario['description']}"
            assert content_type == scenario["content_type"], f"Wrong content type for {scenario['description']}"

    def test_explanation_quality_edge_cases(self, explain_handler, mock_orchestrator):
        """Test explanation quality validation edge cases."""
        command = "explain this"
        context = {"intent": {"intent": "explain_selected_text"}}
        original_text = "This is the original text to explain"
        
        # Test various explanation quality scenarios
        quality_scenarios = [
            {
                "explanation": "",
                "should_pass": False,
                "description": "Empty explanation"
            },
            {
                "explanation": "I cannot explain this text because it's unclear.",
                "should_pass": False,
                "description": "Failure pattern explanation"
            },
            {
                "explanation": "Unable to determine the meaning of this content.",
                "should_pass": False,
                "description": "Another failure pattern"
            },
            {
                "explanation": "x" * 1001,
                "should_pass": False,
                "description": "Too long explanation"
            },
            {
                "explanation": "ok",
                "should_pass": False,
                "description": "Too short explanation"
            },
            {
                "explanation": "This text means something important and describes a concept.",
                "should_pass": True,
                "description": "Valid explanation"
            },
            {
                "explanation": "This is the original text to explain",  # Exact repetition
                "should_pass": False,
                "description": "Repetition of original text"
            },
            {
                "explanation": "This code function calculates values and returns results for processing.",
                "should_pass": True,
                "description": "Valid code explanation"
            }
        ]
        
        for scenario in quality_scenarios:
            # Act
            is_valid = explain_handler._validate_explanation_quality(scenario["explanation"], original_text)
            
            # Assert
            assert is_valid == scenario["should_pass"], f"Quality validation failed for {scenario['description']}"

    def test_reasoning_module_edge_cases(self, explain_handler, mock_orchestrator):
        """Test edge cases with reasoning module responses."""
        command = "explain this"
        context = {"intent": {"intent": "explain_selected_text"}}
        selected_text = "Test text for reasoning edge cases"
        
        reasoning_scenarios = [
            {
                "response": None,
                "should_succeed": False,
                "description": "None response"
            },
            {
                "response": "",
                "should_succeed": False,
                "description": "Empty string response"
            },
            {
                "response": "   ",
                "should_succeed": False,
                "description": "Whitespace only response"
            },
            {
                "response": {"error": "API failed"},
                "should_succeed": False,
                "description": "Error response dict"
            },
            {
                "response": {"explanation": ""},
                "should_succeed": False,
                "description": "Dict with empty explanation"
            },
            {
                "response": {"explanation": "This is a valid explanation"},
                "should_succeed": True,
                "description": "Dict with valid explanation"
            },
            {
                "response": {"plan": [{"action": "speak", "message": "Valid plan explanation"}]},
                "should_succeed": True,
                "description": "Action plan response"
            },
            {
                "response": ["Valid list explanation"],
                "should_succeed": True,
                "description": "List response"
            },
            {
                "response": {"nested": {"explanation": "Nested explanation"}},
                "should_succeed": True,
                "description": "Nested dict response"
            }
        ]
        
        for scenario in reasoning_scenarios:
            # Arrange
            mock_orchestrator.accessibility_module.get_selected_text.return_value = selected_text
            mock_orchestrator.reasoning_module.process_query.return_value = scenario["response"]
            
            # Act
            result = explain_handler.handle(command, context)
            
            # Assert
            if scenario["should_succeed"]:
                assert result["success"] == True, f"Should succeed for {scenario['description']}"
            else:
                assert result["success"] == False, f"Should fail for {scenario['description']}"

    def test_audio_feedback_edge_cases(self, explain_handler, mock_orchestrator):
        """Test edge cases with audio feedback systems."""
        command = "explain this"
        context = {"intent": {"intent": "explain_selected_text"}}
        selected_text = "Audio feedback test text"
        explanation = "This is a test explanation"
        
        # Test various audio module availability scenarios
        audio_scenarios = [
            {
                "feedback_available": True,
                "audio_available": True,
                "description": "All audio modules available"
            },
            {
                "feedback_available": False,
                "audio_available": True,
                "description": "Only audio module available"
            },
            {
                "feedback_available": False,
                "audio_available": False,
                "description": "No audio modules available"
            }
        ]
        
        for scenario in audio_scenarios:
            # Arrange
            mock_orchestrator.accessibility_module.get_selected_text.return_value = selected_text
            mock_orchestrator.reasoning_module.process_query.return_value = explanation
            
            if not scenario["feedback_available"]:
                mock_orchestrator.feedback_module = None
            if not scenario["audio_available"]:
                mock_orchestrator.audio_module = None
            
            # Act
            result = explain_handler.handle(command, context)
            
            # Assert - Should succeed regardless of audio availability
            assert result["success"] == True, f"Should succeed for {scenario['description']}"

    def test_performance_edge_cases(self, explain_handler, mock_orchestrator):
        """Test performance-related edge cases."""
        command = "explain this"
        context = {"intent": {"intent": "explain_selected_text"}}
        
        # Test with simulated slow operations
        def slow_text_capture():
            time.sleep(0.1)  # Simulate slow capture
            return "Slow captured text"
        
        def slow_explanation_generation(prompt, **kwargs):
            time.sleep(0.1)  # Simulate slow reasoning
            return "Slow generated explanation"
        
        # Arrange
        mock_orchestrator.accessibility_module.get_selected_text.side_effect = slow_text_capture
        mock_orchestrator.reasoning_module.process_query.side_effect = slow_explanation_generation
        
        # Act
        start_time = time.time()
        result = explain_handler.handle(command, context)
        end_time = time.time()
        
        # Assert
        assert result["success"] == True
        assert "capture_time" in result
        assert "explanation_time" in result
        assert result["capture_time"] > 0
        assert result["explanation_time"] > 0
        
        total_time = end_time - start_time
        assert total_time > 0.2  # Should take at least 200ms due to simulated delays

    def test_concurrent_execution_edge_cases(self, explain_handler, mock_orchestrator):
        """Test edge cases with concurrent execution scenarios."""
        command = "explain this"
        context = {"intent": {"intent": "explain_selected_text"}}
        
        # Test rapid successive calls
        mock_orchestrator.accessibility_module.get_selected_text.return_value = "Concurrent test text"
        mock_orchestrator.reasoning_module.process_query.return_value = "Concurrent explanation"
        
        # Act - Make multiple rapid calls
        results = []
        for i in range(3):
            result = explain_handler.handle(command, context)
            results.append(result)
        
        # Assert - All should succeed
        for i, result in enumerate(results):
            assert result["success"] == True, f"Call {i} should succeed"
        
        # Verify statistics are tracked correctly
        assert explain_handler._explanation_attempts >= 3
        assert explain_handler._explanation_successes >= 3

    def test_memory_usage_edge_cases(self, explain_handler, mock_orchestrator):
        """Test edge cases related to memory usage."""
        command = "explain this"
        context = {"intent": {"intent": "explain_selected_text"}}
        
        # Test with very large text that should be handled efficiently
        large_text = "Large text content. " * 10000  # ~200KB of text
        mock_orchestrator.accessibility_module.get_selected_text.return_value = large_text
        mock_orchestrator.reasoning_module.process_query.return_value = "Summary of large text"
        
        # Act
        result = explain_handler.handle(command, context)
        
        # Assert - Should handle large text gracefully
        assert result["success"] == True
        # Text should be truncated for reasoning if too long
        reasoning_call = mock_orchestrator.reasoning_module.process_query.call_args
        if reasoning_call:
            prompt_text = reasoning_call[0][0]
            # Prompt should not contain the full large text if it was truncated
            assert len(prompt_text) < len(large_text) + 1000  # Allow for prompt template overhead

    def test_exception_handling_edge_cases(self, explain_handler, mock_orchestrator):
        """Test various exception scenarios."""
        command = "explain this"
        context = {"intent": {"intent": "explain_selected_text"}}
        
        exception_scenarios = [
            {
                "exception": Exception("Generic error"),
                "module": "accessibility_module",
                "method": "get_selected_text"
            },
            {
                "exception": KeyError("Missing key"),
                "module": "reasoning_module", 
                "method": "process_query"
            },
            {
                "exception": AttributeError("Missing attribute"),
                "module": "feedback_module",
                "method": "play"
            },
            {
                "exception": TypeError("Type error"),
                "module": "audio_module",
                "method": "text_to_speech"
            }
        ]
        
        for scenario in exception_scenarios:
            # Arrange
            module = getattr(mock_orchestrator, scenario["module"])
            method = getattr(module, scenario["method"])
            method.side_effect = scenario["exception"]
            
            # Act
            result = explain_handler.handle(command, context)
            
            # Assert - Should handle exceptions gracefully
            assert result["success"] == False
            assert "error" in result["message"].lower() or "issue" in result["message"].lower()
            
            # Reset for next test
            method.side_effect = None

    def test_state_consistency_edge_cases(self, explain_handler, mock_orchestrator):
        """Test state consistency in edge case scenarios."""
        command = "explain this"
        context = {"intent": {"intent": "explain_selected_text"}}
        
        # Test that statistics are consistent after failures
        initial_attempts = explain_handler._explanation_attempts
        initial_successes = explain_handler._explanation_successes
        initial_failures = explain_handler._text_capture_failures
        
        # Cause a text capture failure
        mock_orchestrator.accessibility_module.get_selected_text.return_value = None
        
        result = explain_handler.handle(command, context)
        
        # Assert state consistency
        assert result["success"] == False
        assert explain_handler._explanation_attempts == initial_attempts + 1
        assert explain_handler._explanation_successes == initial_successes  # No change
        assert explain_handler._text_capture_failures == initial_failures + 1
        
        # Test recovery after failure
        mock_orchestrator.accessibility_module.get_selected_text.return_value = "Recovery test"
        mock_orchestrator.reasoning_module.process_query.return_value = "Recovery explanation"
        
        result = explain_handler.handle(command, context)
        
        # Assert recovery
        assert result["success"] == True
        assert explain_handler._explanation_attempts == initial_attempts + 2
        assert explain_handler._explanation_successes == initial_successes + 1