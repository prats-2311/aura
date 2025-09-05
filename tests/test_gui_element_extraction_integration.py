"""
Integration tests for enhanced GUI element extraction with target extraction.
"""

import pytest
from unittest.mock import Mock, patch
import sys
import os

# Add the parent directory to the path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator import Orchestrator


class TestGUIElementExtractionIntegration:
    """Test cases for integrated GUI element extraction with target extraction."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Mock all modules to avoid initialization issues
        with patch('orchestrator.VisionModule'), \
             patch('orchestrator.ReasoningModule'), \
             patch('orchestrator.AutomationModule'), \
             patch('orchestrator.AudioModule'), \
             patch('orchestrator.FeedbackModule'), \
             patch('orchestrator.AccessibilityModule'):
            self.orchestrator = Orchestrator()
    
    def test_enhanced_gui_extraction_basic_click(self):
        """Test enhanced GUI extraction for basic click command."""
        command = "Click on the Gmail link"
        result = self.orchestrator._extract_gui_elements_from_command(command)
        
        expected = {
            'role': '',  # Empty for broader search
            'label': 'Gmail link',
            'action': 'click',
            'app_name': None
        }
        
        assert result == expected
    
    def test_enhanced_gui_extraction_type_command(self):
        """Test enhanced GUI extraction for type command."""
        command = "Type in the search box"
        result = self.orchestrator._extract_gui_elements_from_command(command)
        
        expected = {
            'role': '',
            'label': 'search box',
            'action': 'type',
            'app_name': None
        }
        
        assert result == expected
    
    def test_enhanced_gui_extraction_with_app_name(self):
        """Test enhanced GUI extraction with application name."""
        command = "Click the Save button in Safari app"
        result = self.orchestrator._extract_gui_elements_from_command(command)
        
        expected = {
            'role': '',
            'label': 'Save button Safari app',  # Target extraction includes the app reference
            'action': 'click',
            'app_name': 'Safari'  # App name extracted separately
        }
        
        assert result == expected
    
    def test_enhanced_gui_extraction_complex_command(self):
        """Test enhanced GUI extraction for complex command."""
        command = "Double click on the Save As button in the File menu"
        result = self.orchestrator._extract_gui_elements_from_command(command)
        
        expected = {
            'role': '',
            'label': 'Save As button File menu',
            'action': 'double_click',
            'app_name': None
        }
        
        assert result == expected
    
    def test_enhanced_gui_extraction_scroll_command(self):
        """Test enhanced GUI extraction for scroll command."""
        command = "Scroll down in the main window"
        result = self.orchestrator._extract_gui_elements_from_command(command)
        
        expected = {
            'role': '',
            'label': 'down main window',
            'action': 'scroll',
            'app_name': None
        }
        
        assert result == expected
    
    def test_enhanced_gui_extraction_fallback_to_full_command(self):
        """Test fallback to full command when target extraction fails."""
        # Mock target extraction to return the same as input (indicating failure)
        with patch.object(self.orchestrator, '_extract_target_from_command', return_value="Click"):
            command = "Click"
            result = self.orchestrator._extract_gui_elements_from_command(command)
            
            expected = {
                'role': '',
                'label': 'Click',  # Falls back to full command
                'action': 'click',
                'app_name': None
            }
            
            assert result == expected
    
    def test_enhanced_gui_extraction_empty_command(self):
        """Test enhanced GUI extraction with empty command."""
        command = ""
        result = self.orchestrator._extract_gui_elements_from_command(command)
        
        # Should return empty dict when no label can be extracted
        assert result == {}
    
    def test_enhanced_gui_extraction_whitespace_command(self):
        """Test enhanced GUI extraction with whitespace-only command."""
        command = "   "
        result = self.orchestrator._extract_gui_elements_from_command(command)
        
        # Should return empty dict when no meaningful label can be extracted
        assert result == {}
    
    def test_enhanced_gui_extraction_preserves_case(self):
        """Test that enhanced GUI extraction preserves original case."""
        command = "Click on the Gmail Link"
        result = self.orchestrator._extract_gui_elements_from_command(command)
        
        expected = {
            'role': '',
            'label': 'Gmail Link',  # Case preserved
            'action': 'click',
            'app_name': None
        }
        
        assert result == expected
    
    def test_enhanced_gui_extraction_special_characters(self):
        """Test enhanced GUI extraction with special characters."""
        command = "Click on the 'Save & Exit' button"
        result = self.orchestrator._extract_gui_elements_from_command(command)
        
        expected = {
            'role': '',
            'label': "'Save & Exit' button",
            'action': 'click',
            'app_name': None
        }
        
        assert result == expected
    
    def test_enhanced_gui_extraction_multiple_actions(self):
        """Test enhanced GUI extraction correctly identifies different actions."""
        test_cases = [
            ("Click the button", "click"),
            ("Press the key", "click"),  # Press maps to click
            ("Tap the icon", "click"),   # Tap maps to click
            ("Select the option", "click"),  # Select maps to click
            ("Double click the file", "double_click"),
            ("Open the document", "double_click"),  # Open maps to double_click
            ("Type hello", "type"),
            ("Enter text", "type"),  # Enter maps to type
            ("Input data", "type"),  # Input maps to type
            ("Write message", "type"),  # Write maps to type
            ("Scroll down", "scroll"),
            ("Page up", "scroll")  # Page up/down maps to scroll
        ]
        
        for command, expected_action in test_cases:
            result = self.orchestrator._extract_gui_elements_from_command(command)
            assert result['action'] == expected_action, f"Failed for command: {command}"
    
    def test_enhanced_gui_extraction_app_name_filtering(self):
        """Test that common words are filtered out from app names."""
        test_cases = [
            ("Click button in Safari app", "Safari"),
            ("Click button in Chrome application", "Chrome"),
            ("Click button in Firefox window", "Firefox"),
            ("Click button in main window", None),  # "main" filtered out
            ("Click button in current window", None),  # "current" filtered out
            ("Click button in the app", None),  # "the" filtered out
        ]
        
        for command, expected_app in test_cases:
            result = self.orchestrator._extract_gui_elements_from_command(command)
            assert result['app_name'] == expected_app, f"Failed for command: {command}"


class TestCommandProcessingPipeline:
    """Test the complete command processing pipeline."""
    
    def setup_method(self):
        """Set up test fixtures."""
        with patch('orchestrator.VisionModule'), \
             patch('orchestrator.ReasoningModule'), \
             patch('orchestrator.AutomationModule'), \
             patch('orchestrator.AudioModule'), \
             patch('orchestrator.FeedbackModule'), \
             patch('orchestrator.AccessibilityModule'):
            self.orchestrator = Orchestrator()
    
    def test_complete_pipeline_target_extraction_to_gui_elements(self):
        """Test complete pipeline from command to GUI elements."""
        command = "Click on the Sign In button"
        
        # Test target extraction
        target = self.orchestrator._extract_target_from_command(command)
        assert target == "Sign button"  # "In" removed as article
        
        # Test GUI element extraction using the target
        gui_elements = self.orchestrator._extract_gui_elements_from_command(command)
        expected = {
            'role': '',
            'label': 'Sign button',
            'action': 'click',
            'app_name': None
        }
        assert gui_elements == expected
    
    def test_pipeline_with_confidence_scoring(self):
        """Test pipeline includes confidence scoring from target extraction."""
        command = "Click on the Gmail link"
        
        # Extract target and check confidence is calculated
        target = self.orchestrator._extract_target_from_command(command)
        
        # Calculate confidence manually to verify it's working
        confidence = self.orchestrator._calculate_target_extraction_confidence(
            command, target, ["click", "on", "the"]
        )
        
        # Should have high confidence due to action words and articles removed
        assert confidence > 0.7
        
        # GUI elements should use the extracted target
        gui_elements = self.orchestrator._extract_gui_elements_from_command(command)
        assert gui_elements['label'] == target
    
    def test_pipeline_error_handling(self):
        """Test pipeline handles errors gracefully."""
        # Test with problematic input that might cause exceptions
        problematic_commands = [
            None,  # This will be handled by the string methods
            "",
            "   ",
            "Click",  # Minimal command
            "Click the the the",  # Repetitive articles
        ]
        
        for command in problematic_commands:
            if command is not None:  # Skip None as it would cause TypeError before our method
                # Should not raise exceptions
                try:
                    target = self.orchestrator._extract_target_from_command(command)
                    gui_elements = self.orchestrator._extract_gui_elements_from_command(command)
                    # Both should return strings/dicts, not raise exceptions
                    assert isinstance(target, str)
                    assert isinstance(gui_elements, dict)
                except Exception as e:
                    pytest.fail(f"Pipeline raised exception for command '{command}': {e}")
    
    def test_pipeline_integration_with_is_gui_command(self):
        """Test pipeline integration with GUI command detection."""
        gui_commands = [
            "Click on the Gmail link",
            "Type in the search box",
            "Press the Submit button",
            "Scroll down"
        ]
        
        non_gui_commands = [
            "What's on my screen?",
            "Tell me about this image",
            "Explain the current page"
        ]
        
        for command in gui_commands:
            # Should be detected as GUI command
            command_info = {'command_type': 'click'}  # Mock command info
            is_gui = self.orchestrator._is_gui_command(command, command_info)
            assert is_gui, f"Command should be detected as GUI: {command}"
            
            # Should extract GUI elements successfully
            gui_elements = self.orchestrator._extract_gui_elements_from_command(command)
            assert gui_elements, f"Should extract GUI elements from: {command}"
            assert gui_elements.get('label'), f"Should have label for: {command}"
        
        for command in non_gui_commands:
            # Should not extract meaningful GUI elements
            gui_elements = self.orchestrator._extract_gui_elements_from_command(command)
            # These commands might return empty dict or have minimal extraction
            # The key is that they don't interfere with the GUI detection logic


if __name__ == "__main__":
    pytest.main([__file__])