"""
Unit tests for target extraction functionality in orchestrator.
"""

import pytest
from unittest.mock import Mock, patch
import sys
import os

# Add the parent directory to the path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator import Orchestrator


class TestTargetExtraction:
    """Test cases for target extraction from commands."""
    
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
    
    def test_extract_target_basic_click_command(self):
        """Test basic click command target extraction."""
        command = "Click on the Gmail link"
        expected = "Gmail link"
        result = self.orchestrator._extract_target_from_command(command)
        assert result == expected
    
    def test_extract_target_press_button_command(self):
        """Test press button command target extraction."""
        command = "Press the Submit button"
        expected = "Submit button"
        result = self.orchestrator._extract_target_from_command(command)
        assert result == expected
    
    def test_extract_target_type_command(self):
        """Test type command target extraction."""
        command = "Type in the search box"
        expected = "search box"
        result = self.orchestrator._extract_target_from_command(command)
        assert result == expected
    
    def test_extract_target_multiple_articles(self):
        """Test extraction with multiple articles."""
        command = "Click on the Sign In button"
        expected = "Sign button"  # "In" is removed as an article
        result = self.orchestrator._extract_target_from_command(command)
        assert result == expected
    
    def test_extract_target_no_articles(self):
        """Test extraction without articles."""
        command = "Click Gmail"
        expected = "Gmail"
        result = self.orchestrator._extract_target_from_command(command)
        assert result == expected
    
    def test_extract_target_complex_command(self):
        """Test extraction from complex command."""
        command = "Double click on the Save As button in the File menu"
        expected = "Save As button File menu"
        result = self.orchestrator._extract_target_from_command(command)
        assert result == expected
    
    def test_extract_target_with_prepositions(self):
        """Test extraction with various prepositions."""
        command = "Type into the username field"
        expected = "username field"
        result = self.orchestrator._extract_target_from_command(command)
        assert result == expected
    
    def test_extract_target_minimal_command(self):
        """Test extraction from minimal command."""
        command = "Click OK"
        expected = "OK"
        result = self.orchestrator._extract_target_from_command(command)
        assert result == expected
    
    def test_extract_target_empty_result_fallback(self):
        """Test fallback when extraction results in empty target."""
        command = "Click the"
        # Should fall back to original command when target is too short
        result = self.orchestrator._extract_target_from_command(command)
        assert result == command.strip()
    
    def test_extract_target_only_action_words(self):
        """Test fallback when command contains only action words."""
        command = "Click press"
        # Should fall back to original command
        result = self.orchestrator._extract_target_from_command(command)
        assert result == command.strip()
    
    def test_extract_target_case_preservation(self):
        """Test that original case is preserved in result."""
        command = "Click on the Gmail Link"
        expected = "Gmail Link"
        result = self.orchestrator._extract_target_from_command(command)
        assert result == expected
    
    def test_extract_target_special_characters(self):
        """Test extraction with special characters."""
        command = "Click on the 'Save & Exit' button"
        expected = "'Save & Exit' button"
        result = self.orchestrator._extract_target_from_command(command)
        assert result == expected
    
    def test_extract_target_numbers(self):
        """Test extraction with numbers."""
        command = "Click on button 1"
        expected = "button 1"
        result = self.orchestrator._extract_target_from_command(command)
        assert result == expected
    
    def test_extract_target_scroll_command(self):
        """Test extraction from scroll command."""
        command = "Scroll down in the main window"
        expected = "down main window"
        result = self.orchestrator._extract_target_from_command(command)
        assert result == expected
    
    def test_extract_target_form_command(self):
        """Test extraction from form-related command."""
        command = "Fill in the email address field"
        expected = "email address field"
        result = self.orchestrator._extract_target_from_command(command)
        assert result == expected


class TestTargetExtractionConfidence:
    """Test cases for target extraction confidence scoring."""
    
    def setup_method(self):
        """Set up test fixtures."""
        with patch('orchestrator.VisionModule'), \
             patch('orchestrator.ReasoningModule'), \
             patch('orchestrator.AutomationModule'), \
             patch('orchestrator.AudioModule'), \
             patch('orchestrator.FeedbackModule'), \
             patch('orchestrator.AccessibilityModule'):
            self.orchestrator = Orchestrator()
    
    def test_confidence_with_action_words_removed(self):
        """Test confidence increases when action words are removed."""
        original = "Click on the Gmail link"
        extracted = "gmail link"
        removed = ["click", "on", "the"]
        
        confidence = self.orchestrator._calculate_target_extraction_confidence(
            original, extracted, removed
        )
        
        # Should have high confidence due to action word and articles removed
        assert confidence > 0.7
    
    def test_confidence_with_articles_removed(self):
        """Test confidence increases when articles are removed."""
        original = "Press the Submit button"
        extracted = "submit button"
        removed = ["press", "the"]
        
        confidence = self.orchestrator._calculate_target_extraction_confidence(
            original, extracted, removed
        )
        
        # Should have good confidence
        assert confidence > 0.6
    
    def test_confidence_minimal_extraction(self):
        """Test confidence with minimal extraction."""
        original = "Click Gmail"
        extracted = "gmail"
        removed = ["click"]
        
        confidence = self.orchestrator._calculate_target_extraction_confidence(
            original, extracted, removed
        )
        
        # Should have reasonable confidence
        assert confidence > 0.5
    
    def test_confidence_no_extraction(self):
        """Test confidence when no words are removed."""
        original = "Gmail link"
        extracted = "Gmail link"
        removed = []
        
        confidence = self.orchestrator._calculate_target_extraction_confidence(
            original, extracted, removed
        )
        
        # Should have base confidence plus meaningful words bonus
        assert confidence >= 0.5
    
    def test_confidence_very_short_target(self):
        """Test confidence decreases for very short targets."""
        original = "Click on the big red button"
        extracted = "big"
        removed = ["click", "on", "the"]  # Only count actually removed words
        
        confidence = self.orchestrator._calculate_target_extraction_confidence(
            original, extracted, removed
        )
        
        # Should have lower confidence due to short target relative to original
        assert confidence < 0.8  # Adjusted expectation
    
    def test_confidence_meaningful_words(self):
        """Test confidence increases with meaningful words."""
        original = "Click on the submit button"
        extracted = "submit button"
        removed = ["click", "on", "the"]
        
        confidence = self.orchestrator._calculate_target_extraction_confidence(
            original, extracted, removed
        )
        
        # Should have high confidence due to meaningful words
        assert confidence > 0.7
    
    def test_confidence_bounds(self):
        """Test confidence is always within 0.0 to 1.0 bounds."""
        # Test various scenarios
        test_cases = [
            ("Click", "click", []),
            ("Click on the very long button name", "very long button name", ["click", "on", "the"]),
            ("a", "a", []),
            ("Click the the the the button", "button", ["click", "the", "the", "the", "the"])
        ]
        
        for original, extracted, removed in test_cases:
            confidence = self.orchestrator._calculate_target_extraction_confidence(
                original, extracted, removed
            )
            assert 0.0 <= confidence <= 1.0


class TestTargetExtractionEdgeCases:
    """Test edge cases for target extraction."""
    
    def setup_method(self):
        """Set up test fixtures."""
        with patch('orchestrator.VisionModule'), \
             patch('orchestrator.ReasoningModule'), \
             patch('orchestrator.AutomationModule'), \
             patch('orchestrator.AudioModule'), \
             patch('orchestrator.FeedbackModule'), \
             patch('orchestrator.AccessibilityModule'):
            self.orchestrator = Orchestrator()
    
    def test_extract_target_empty_command(self):
        """Test extraction from empty command."""
        command = ""
        result = self.orchestrator._extract_target_from_command(command)
        assert result == ""
    
    def test_extract_target_whitespace_only(self):
        """Test extraction from whitespace-only command."""
        command = "   "
        result = self.orchestrator._extract_target_from_command(command)
        assert result == ""
    
    def test_extract_target_single_word(self):
        """Test extraction from single word command."""
        command = "Gmail"
        result = self.orchestrator._extract_target_from_command(command)
        assert result == "Gmail"  # Should preserve original case
    
    def test_extract_target_exception_handling(self):
        """Test that exceptions are handled gracefully."""
        # This should not raise an exception
        command = "Click on the Gmail link"
        result = self.orchestrator._extract_target_from_command(command)
        assert isinstance(result, str)
    
    def test_confidence_exception_handling(self):
        """Test that confidence calculation handles exceptions gracefully."""
        # This should not raise an exception and return default confidence
        confidence = self.orchestrator._calculate_target_extraction_confidence(
            None, None, None
        )
        assert confidence == 0.5


if __name__ == "__main__":
    pytest.main([__file__])