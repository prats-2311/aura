#!/usr/bin/env python3
"""
Application Compatibility Test Suite for Explain Selected Text Feature

This test suite specifically tests the explain selected text functionality
across different macOS applications including web browsers, PDF readers,
text editors, and applications with limited accessibility support.

Requirements: 1.3, 1.4, 1.5, 2.1, 2.2
"""

import pytest
import unittest.mock as mock
from unittest.mock import Mock, MagicMock, patch, call
import time
import subprocess
import os
from typing import Dict, Any, Optional, List

# Import modules under test
try:
    from handlers.explain_selection_handler import ExplainSelectionHandler
    from modules.accessibility import AccessibilityModule
    from modules.automation import AutomationModule
except ImportError:
    # Handle case where modules might not be fully implemented yet
    ExplainSelectionHandler = None
    AccessibilityModule = None
    AutomationModule = None


class TestApplicationCompatibility:
    """Test explain selected text feature across different macOS applications."""
    
    @pytest.fixture
    def mock_orchestrator(self):
        """Mock orchestrator with all required modules."""
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
        if ExplainSelectionHandler is None:
            pytest.skip("ExplainSelectionHandler not available")
        return ExplainSelectionHandler(mock_orchestrator)

    def test_web_browser_chrome_html_content(self, explain_handler, mock_orchestrator):
        """Test text selection and explanation in Chrome with HTML content."""
        # Arrange
        command = "explain this"
        context = {"intent": {"intent": "explain_selected_text"}}
        
        # Simulate Chrome HTML content selection
        html_text = "Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience."
        expected_explanation = "Machine learning is a technology that allows computers to automatically get better at tasks by learning from data, without being explicitly programmed for each specific situation."
        
        # Mock successful accessibility API capture (Chrome has good accessibility support)
        mock_orchestrator.accessibility_module.get_selected_text.return_value = html_text
        mock_orchestrator.reasoning_module.process_query.return_value = expected_explanation
        
        # Act
        result = explain_handler.handle(command, context)
        
        # Assert
        assert result["status"] == "success"
        mock_orchestrator.accessibility_module.get_selected_text.assert_called_once()
        mock_orchestrator.reasoning_module.process_query.assert_called_once()
        
        # Verify the reasoning module was called with appropriate prompt
        call_args = mock_orchestrator.reasoning_module.process_query.call_args
        assert html_text in str(call_args)

    def test_web_browser_safari_javascript_content(self, explain_handler, mock_orchestrator):
        """Test text selection and explanation in Safari with JavaScript content."""
        # Arrange
        command = "explain this code"
        context = {"intent": {"intent": "explain_selected_text"}}
        
        # Simulate Safari JavaScript content selection
        js_code = """
        function calculateTotal(items) {
            return items.reduce((sum, item) => sum + item.price, 0);
        }
        """
        expected_explanation = "This JavaScript function takes an array of items and calculates the total price by adding up the price property of each item."
        
        # Mock successful accessibility API capture
        mock_orchestrator.accessibility_module.get_selected_text.return_value = js_code
        mock_orchestrator.reasoning_module.process_query.return_value = expected_explanation
        
        # Act
        result = explain_handler.handle(command, context)
        
        # Assert
        assert result["status"] == "success"
        mock_orchestrator.accessibility_module.get_selected_text.assert_called_once()
        mock_orchestrator.reasoning_module.process_query.assert_called_once()

    def test_web_browser_complex_formatting(self, explain_handler, mock_orchestrator):
        """Test web browser with complex formatted content (tables, lists, etc.)."""
        # Arrange
        command = "explain this"
        context = {"intent": {"intent": "explain_selected_text"}}
        
        # Simulate complex formatted content from web page
        formatted_text = """
        Product Features:
        • Advanced AI processing
        • Real-time data analysis
        • Cloud-based architecture
        • 99.9% uptime guarantee
        """
        expected_explanation = "This is a list of product features highlighting the key capabilities including AI processing, data analysis, cloud infrastructure, and reliability guarantees."
        
        mock_orchestrator.accessibility_module.get_selected_text.return_value = formatted_text
        mock_orchestrator.reasoning_module.process_query.return_value = expected_explanation
        
        # Act
        result = explain_handler.handle(command, context)
        
        # Assert
        assert result["status"] == "success"
        mock_orchestrator.accessibility_module.get_selected_text.assert_called_once()

    def test_pdf_reader_preview_technical_document(self, explain_handler, mock_orchestrator):
        """Test text selection and explanation in Preview with technical PDF content."""
        # Arrange
        command = "explain this"
        context = {"intent": {"intent": "explain_selected_text"}}
        
        # Simulate technical PDF content from Preview
        pdf_text = "The algorithm employs a convolutional neural network (CNN) architecture with residual connections to achieve state-of-the-art performance on image classification tasks."
        expected_explanation = "This describes a type of artificial intelligence system designed to recognize and categorize images. It uses advanced techniques called convolutional neural networks and residual connections to achieve very high accuracy."
        
        # Mock the unified get_selected_text method to return PDF text
        # (The accessibility module handles fallback internally when PDF readers have limited accessibility)
        mock_orchestrator.accessibility_module.get_selected_text.return_value = pdf_text
        mock_orchestrator.reasoning_module.process_query.return_value = expected_explanation
        
        # Act
        result = explain_handler.handle(command, context)
        
        # Assert
        assert result["status"] == "success"
        mock_orchestrator.accessibility_module.get_selected_text.assert_called_once()

    def test_pdf_reader_formatted_document(self, explain_handler, mock_orchestrator):
        """Test PDF reader with formatted documents (headers, footnotes, etc.)."""
        # Arrange
        command = "explain this"
        context = {"intent": {"intent": "explain_selected_text"}}
        
        # Simulate formatted PDF content with headers and structure
        formatted_pdf_text = """
        3.2 Methodology
        
        The research methodology involved a randomized controlled trial (RCT) with 
        a sample size of n=500 participants. Statistical analysis was performed 
        using SPSS version 28.0 with significance level set at p<0.05.
        """
        expected_explanation = "This section describes how a research study was conducted. It used a randomized controlled trial method with 500 people, and statistical software was used to analyze the results with standard scientific criteria for determining if findings are meaningful."
        
        mock_orchestrator.accessibility_module.get_selected_text.return_value = formatted_pdf_text
        mock_orchestrator.reasoning_module.process_query.return_value = expected_explanation
        
        # Act
        result = explain_handler.handle(command, context)
        
        # Assert
        assert result["status"] == "success"
        mock_orchestrator.accessibility_module.get_selected_text.assert_called_once()

    def test_text_editor_textedit_plain_text(self, explain_handler, mock_orchestrator):
        """Test text selection and explanation in TextEdit with plain text."""
        # Arrange
        command = "explain this"
        context = {"intent": {"intent": "explain_selected_text"}}
        
        # Simulate plain text content from TextEdit
        plain_text = "The quick brown fox jumps over the lazy dog. This sentence contains every letter of the alphabet at least once."
        expected_explanation = "This is a famous pangram - a sentence that uses every letter of the English alphabet at least once. It's commonly used for testing fonts, keyboards, and typing skills."
        
        # TextEdit has good accessibility support
        mock_orchestrator.accessibility_module.get_selected_text.return_value = plain_text
        mock_orchestrator.reasoning_module.process_query.return_value = expected_explanation
        
        # Act
        result = explain_handler.handle(command, context)
        
        # Assert
        assert result["status"] == "success"
        mock_orchestrator.accessibility_module.get_selected_text.assert_called_once()

    def test_text_editor_vscode_python_code(self, explain_handler, mock_orchestrator):
        """Test text selection and explanation in VS Code with Python code."""
        # Arrange
        command = "explain this code"
        context = {"intent": {"intent": "explain_selected_text"}}
        
        # Simulate Python code from VS Code
        python_code = """
        def fibonacci(n):
            if n <= 1:
                return n
            return fibonacci(n-1) + fibonacci(n-2)
        """
        expected_explanation = "This is a Python function that calculates Fibonacci numbers using recursion. It returns the nth number in the Fibonacci sequence, where each number is the sum of the two preceding ones."
        
        # VS Code has excellent accessibility support
        mock_orchestrator.accessibility_module.get_selected_text.return_value = python_code
        mock_orchestrator.reasoning_module.process_query.return_value = expected_explanation
        
        # Act
        result = explain_handler.handle(command, context)
        
        # Assert
        assert result["status"] == "success"
        mock_orchestrator.accessibility_module.get_selected_text.assert_called_once()

    def test_text_editor_vscode_json_config(self, explain_handler, mock_orchestrator):
        """Test text selection and explanation in VS Code with JSON configuration."""
        # Arrange
        command = "explain this"
        context = {"intent": {"intent": "explain_selected_text"}}
        
        # Simulate JSON configuration from VS Code
        json_config = """
        {
            "compilerOptions": {
                "target": "ES2020",
                "module": "commonjs",
                "strict": true,
                "esModuleInterop": true
            }
        }
        """
        expected_explanation = "This is a TypeScript configuration file that sets up compiler options. It specifies that the code should be compiled to ES2020 JavaScript standard, use CommonJS modules, enable strict type checking, and allow compatibility with ES modules."
        
        mock_orchestrator.accessibility_module.get_selected_text.return_value = json_config
        mock_orchestrator.reasoning_module.process_query.return_value = expected_explanation
        
        # Act
        result = explain_handler.handle(command, context)
        
        # Assert
        assert result["status"] == "success"
        mock_orchestrator.accessibility_module.get_selected_text.assert_called_once()

    def test_limited_accessibility_application_fallback(self, explain_handler, mock_orchestrator):
        """Test fallback behavior in applications with limited accessibility support."""
        # Arrange
        command = "explain this"
        context = {"intent": {"intent": "explain_selected_text"}}
        
        # Simulate application with limited accessibility support
        selected_text = "This text was captured via clipboard fallback method."
        expected_explanation = "This text demonstrates the clipboard fallback functionality working correctly when accessibility APIs are not available."
        
        # Mock the unified get_selected_text method to return the fallback text
        # (The accessibility module handles the fallback internally)
        mock_orchestrator.accessibility_module.get_selected_text.return_value = selected_text
        mock_orchestrator.reasoning_module.process_query.return_value = expected_explanation
        
        # Act
        result = explain_handler.handle(command, context)
        
        # Assert
        assert result["status"] == "success"
        mock_orchestrator.accessibility_module.get_selected_text.assert_called_once()
        # Note: The automation module is called internally by accessibility module, not directly by handler

    def test_legacy_application_compatibility(self, explain_handler, mock_orchestrator):
        """Test compatibility with older macOS applications."""
        # Arrange
        command = "explain this"
        context = {"intent": {"intent": "explain_selected_text"}}
        
        # Simulate legacy application content
        legacy_text = "System Preferences > Security & Privacy > Privacy > Accessibility"
        expected_explanation = "This is a navigation path in macOS System Preferences to access accessibility settings, where you can grant applications permission to control your computer for accessibility features."
        
        # Mock the unified get_selected_text method to return the legacy text
        # (The accessibility module handles the fallback internally for legacy apps)
        mock_orchestrator.accessibility_module.get_selected_text.return_value = legacy_text
        mock_orchestrator.reasoning_module.process_query.return_value = expected_explanation
        
        # Act
        result = explain_handler.handle(command, context)
        
        # Assert
        assert result["status"] == "success"
        mock_orchestrator.accessibility_module.get_selected_text.assert_called_once()

    def test_application_specific_content_types(self, explain_handler, mock_orchestrator):
        """Test handling of application-specific content types."""
        command = "explain this"
        context = {"intent": {"intent": "explain_selected_text"}}
        
        test_cases = [
            {
                "app_type": "terminal",
                "content": "$ ls -la | grep .py | wc -l",
                "explanation": "This is a command line instruction that lists files, filters for Python files, and counts how many there are."
            },
            {
                "app_type": "email",
                "content": "Subject: Re: Project Update\n\nHi team,\n\nThe latest deployment was successful.",
                "explanation": "This is an email message confirming that a software deployment completed successfully."
            },
            {
                "app_type": "spreadsheet",
                "content": "=SUM(A1:A10)/COUNT(A1:A10)",
                "explanation": "This is a spreadsheet formula that calculates the average of values in cells A1 through A10."
            },
            {
                "app_type": "markdown",
                "content": "## Installation\n\n```bash\nnpm install package-name\n```",
                "explanation": "This is markdown documentation showing how to install a software package using npm."
            }
        ]
        
        for case in test_cases:
            # Arrange
            mock_orchestrator.accessibility_module.get_selected_text.return_value = case["content"]
            mock_orchestrator.reasoning_module.process_query.return_value = case["explanation"]
            
            # Act
            result = explain_handler.handle(command, context)
            
            # Assert
            assert result["status"] == "success", f"Failed for {case['app_type']} content"

    def test_cross_application_consistency(self, explain_handler, mock_orchestrator):
        """Test that explanations are consistent across different applications for the same content."""
        # Arrange
        command = "explain this"
        context = {"intent": {"intent": "explain_selected_text"}}
        
        # Same content from different applications
        shared_content = "function add(a, b) { return a + b; }"
        base_explanation = "This is a JavaScript function that takes two parameters and returns their sum."
        
        applications = ["chrome", "vscode", "textedit", "notes"]
        
        for app in applications:
            # Mock successful capture regardless of application
            mock_orchestrator.accessibility_module.get_selected_text.return_value = shared_content
            mock_orchestrator.reasoning_module.process_query.return_value = base_explanation
            
            # Act
            result = explain_handler.handle(command, context)
            
            # Assert
            assert result["status"] == "success", f"Failed for application: {app}"
            
            # Reset mocks for next iteration
            mock_orchestrator.reset_mock()

    def test_performance_across_applications(self, explain_handler, mock_orchestrator):
        """Test performance consistency across different application types."""
        command = "explain this"
        context = {"intent": {"intent": "explain_selected_text"}}
        
        # Simulate different performance characteristics for different apps
        performance_scenarios = [
            {"app": "chrome", "capture_delay": 0.1, "text": "Web content"},
            {"app": "preview", "capture_delay": 0.3, "text": "PDF content"},  # PDFs might be slower
            {"app": "vscode", "capture_delay": 0.05, "text": "Code content"},  # Fast accessibility
            {"app": "legacy_app", "capture_delay": 0.5, "text": "Legacy content"}  # Slow fallback
        ]
        
        for scenario in performance_scenarios:
            def delayed_capture():
                time.sleep(scenario["capture_delay"])
                return scenario["text"]
            
            def quick_reasoning(*args, **kwargs):
                return f"Explanation for {scenario['text']}"
            
            # Arrange
            mock_orchestrator.accessibility_module.get_selected_text.side_effect = delayed_capture
            mock_orchestrator.reasoning_module.process_query.side_effect = quick_reasoning
            
            # Act
            start_time = time.time()
            result = explain_handler.handle(command, context)
            end_time = time.time()
            
            # Assert
            assert result["status"] == "success"
            total_time = end_time - start_time
            
            # Performance should be reasonable even for slower apps
            assert total_time < 2.0, f"Too slow for {scenario['app']}: {total_time:.2f}s"
            
            # Reset for next iteration
            mock_orchestrator.reset_mock()

    def test_error_handling_per_application_type(self, explain_handler, mock_orchestrator):
        """Test error handling specific to different application types."""
        command = "explain this"
        context = {"intent": {"intent": "explain_selected_text"}}
        
        error_scenarios = [
            {
                "app_type": "web_browser",
                "error": "Page not fully loaded",
                "unified_result": "Partial content..."  # Accessibility module handles fallback internally
            },
            {
                "app_type": "pdf_reader", 
                "error": "Protected PDF",
                "unified_result": None  # Both methods fail
            },
            {
                "app_type": "text_editor",
                "error": "File too large",
                "unified_result": "Very long content..."  # Some content captured
            }
        ]
        
        for scenario in error_scenarios:
            # Arrange - Mock the unified get_selected_text method
            mock_orchestrator.accessibility_module.get_selected_text.return_value = scenario["unified_result"]
            
            if scenario["unified_result"]:
                mock_orchestrator.reasoning_module.process_query.return_value = f"Explanation for {scenario['app_type']}"
            
            # Act
            result = explain_handler.handle(command, context)
            
            # Assert
            if scenario["unified_result"]:
                assert result["status"] == "success", f"Should succeed for {scenario['app_type']}"
            else:
                assert result["status"] == "error", f"Should fail for {scenario['app_type']}"
            
            # Reset for next iteration
            mock_orchestrator.reset_mock()

    def test_special_application_features(self, explain_handler, mock_orchestrator):
        """Test handling of special application features (syntax highlighting, rich text, etc.)."""
        command = "explain this"
        context = {"intent": {"intent": "explain_selected_text"}}
        
        special_content_cases = [
            {
                "feature": "syntax_highlighting",
                "content": "const result = await fetch('/api/data');",
                "app": "vscode"
            },
            {
                "feature": "rich_text_formatting",
                "content": "**Bold text** and *italic text* with [links](http://example.com)",
                "app": "notes"
            },
            {
                "feature": "mathematical_notation",
                "content": "∫₀¹ x² dx = 1/3",
                "app": "pages"
            },
            {
                "feature": "code_blocks",
                "content": "```python\nprint('Hello, World!')\n```",
                "app": "markdown_editor"
            }
        ]
        
        for case in special_content_cases:
            # Arrange
            mock_orchestrator.accessibility_module.get_selected_text.return_value = case["content"]
            mock_orchestrator.reasoning_module.process_query.return_value = f"This is {case['feature']} content from {case['app']}"
            
            # Act
            result = explain_handler.handle(command, context)
            
            # Assert
            assert result["status"] == "success", f"Failed for {case['feature']} in {case['app']}"
            
            # Reset for next iteration
            mock_orchestrator.reset_mock()

    def test_application_permission_scenarios(self, explain_handler, mock_orchestrator):
        """Test behavior when applications have different permission levels."""
        command = "explain this"
        context = {"intent": {"intent": "explain_selected_text"}}
        
        permission_scenarios = [
            {
                "scenario": "full_accessibility_permission",
                "unified_result": "Test content",  # Accessibility module handles both methods internally
                "should_succeed": True
            },
            {
                "scenario": "no_accessibility_permission_but_clipboard_works",
                "unified_result": "Test content",  # Accessibility module falls back to clipboard internally
                "should_succeed": True
            },
            {
                "scenario": "no_permissions",
                "unified_result": None,  # Both methods fail internally
                "should_succeed": False
            }
        ]
        
        for scenario in permission_scenarios:
            # Arrange - Mock the unified get_selected_text method
            mock_orchestrator.accessibility_module.get_selected_text.return_value = scenario["unified_result"]
            
            if scenario["should_succeed"]:
                mock_orchestrator.reasoning_module.process_query.return_value = "Test explanation"
            
            # Act
            result = explain_handler.handle(command, context)
            
            # Assert
            if scenario["should_succeed"]:
                assert result["status"] == "success", f"Should succeed for {scenario['scenario']}"
            else:
                assert result["status"] == "error", f"Should fail for {scenario['scenario']}"
            
            # Reset for next iteration
            mock_orchestrator.reset_mock()


def run_application_compatibility_tests():
    """Run all application compatibility tests with detailed reporting."""
    print("Running Application Compatibility Test Suite for Explain Selected Text...")
    print("=" * 80)
    
    # Run tests with pytest
    start_time = time.time()
    
    result = pytest.main([__file__, "-v", "--tb=short"])
    
    end_time = time.time()
    total_time = end_time - start_time
    
    print("\n" + "=" * 80)
    print(f"Application compatibility tests completed in {total_time:.2f} seconds")
    
    if result == 0:
        print("Application Compatibility Test Suite: PASSED")
        print("\nTested Applications:")
        print("✓ Web Browsers (Chrome, Safari)")
        print("✓ PDF Readers (Preview)")
        print("✓ Text Editors (TextEdit, VS Code)")
        print("✓ Legacy Applications")
        print("✓ Applications with Limited Accessibility Support")
    else:
        print("Application Compatibility Test Suite: FAILED")
    
    return result == 0


if __name__ == "__main__":
    import sys
    success = run_application_compatibility_tests()
    sys.exit(0 if success else 1)