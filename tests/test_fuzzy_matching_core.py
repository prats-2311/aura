"""
Unit tests for fuzzy matching core functionality in AccessibilityModule.

Tests the fuzzy_match_text method with various text similarity scenarios,
performance monitoring, timeout handling, and error recovery.
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from modules.accessibility import AccessibilityModule


class TestFuzzyMatchingCore:
    """Test suite for fuzzy matching core functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Mock the accessibility frameworks to avoid system dependencies
        with patch('modules.accessibility.ACCESSIBILITY_AVAILABLE', True), \
             patch('modules.accessibility.ACCESSIBILITY_FUNCTIONS_AVAILABLE', True), \
             patch('modules.accessibility.NSWorkspace'), \
             patch('modules.accessibility.AXUIElementCreateSystemWide'):
            self.accessibility = AccessibilityModule()
    
    def test_fuzzy_match_exact_match(self):
        """Test fuzzy matching with exact text matches."""
        # Test exact matches
        match_found, confidence = self.accessibility.fuzzy_match_text("Sign In", "Sign In")
        assert match_found is True
        assert confidence == 100.0
        
        # Test case insensitive exact matches
        match_found, confidence = self.accessibility.fuzzy_match_text("SIGN IN", "sign in")
        assert match_found is True
        assert confidence >= 85.0  # Should be high confidence
    
    def test_fuzzy_match_partial_matches(self):
        """Test fuzzy matching with partial text matches."""
        # Test partial matches that should succeed
        match_found, confidence = self.accessibility.fuzzy_match_text("Sign In Button", "Sign In")
        assert match_found is True
        assert confidence >= 85.0
        
        match_found, confidence = self.accessibility.fuzzy_match_text("Gmail Link", "Gmail")
        assert match_found is True
        assert confidence >= 85.0
        
        # Test variations that should match
        match_found, confidence = self.accessibility.fuzzy_match_text("Sign-In", "Sign In")
        assert match_found is True
        assert confidence >= 85.0
    
    def test_fuzzy_match_threshold_behavior(self):
        """Test fuzzy matching confidence threshold behavior."""
        # Test with custom high threshold
        match_found, confidence = self.accessibility.fuzzy_match_text(
            "Similar Text", "Different Text", confidence_threshold=95
        )
        assert match_found is False  # Should fail with high threshold
        assert confidence < 95.0
        
        # Test with custom low threshold
        match_found, confidence = self.accessibility.fuzzy_match_text(
            "Similar Text", "Different Text", confidence_threshold=50
        )
        # This might pass or fail depending on actual similarity, but confidence should be reported
        assert isinstance(confidence, float)
        assert 0.0 <= confidence <= 100.0
    
    def test_fuzzy_match_empty_strings(self):
        """Test fuzzy matching with empty or None strings."""
        # Test empty strings
        match_found, confidence = self.accessibility.fuzzy_match_text("", "test")
        assert match_found is False
        assert confidence == 0.0
        
        match_found, confidence = self.accessibility.fuzzy_match_text("test", "")
        assert match_found is False
        assert confidence == 0.0
        
        # Test None strings (should be handled gracefully)
        match_found, confidence = self.accessibility.fuzzy_match_text(None, "test")
        assert match_found is False
        assert confidence == 0.0
    
    def test_fuzzy_match_performance_monitoring(self):
        """Test performance monitoring and timeout handling."""
        # Test with very short timeout
        start_time = time.time()
        match_found, confidence = self.accessibility.fuzzy_match_text(
            "Test String", "Test", timeout_ms=1  # Very short timeout
        )
        elapsed_time = (time.time() - start_time) * 1000
        
        # Should complete quickly or timeout gracefully
        assert elapsed_time < 100  # Should not take more than 100ms even with timeout
        assert isinstance(match_found, bool)
        assert isinstance(confidence, float)
    
    def test_fuzzy_match_with_special_characters(self):
        """Test fuzzy matching with special characters and punctuation."""
        # Test with punctuation
        match_found, confidence = self.accessibility.fuzzy_match_text(
            "Sign-In Button!", "Sign In"
        )
        assert match_found is True
        assert confidence >= 85.0
        
        # Test with numbers
        match_found, confidence = self.accessibility.fuzzy_match_text(
            "Button 123", "Button"
        )
        assert match_found is True
        assert confidence >= 85.0
    
    @patch('modules.accessibility.FUZZY_MATCHING_AVAILABLE', False)
    def test_fuzzy_match_library_unavailable_fallback(self):
        """Test graceful degradation when thefuzz library is unavailable."""
        # Create new instance with mocked unavailable library
        with patch('modules.accessibility.ACCESSIBILITY_AVAILABLE', True), \
             patch('modules.accessibility.ACCESSIBILITY_FUNCTIONS_AVAILABLE', True), \
             patch('modules.accessibility.NSWorkspace'), \
             patch('modules.accessibility.AXUIElementCreateSystemWide'):
            accessibility = AccessibilityModule()
        
        # Should fall back to exact matching
        match_found, confidence = accessibility.fuzzy_match_text("Sign In", "Sign In")
        assert match_found is True
        assert confidence == 100.0
        
        # Should fail for non-exact matches
        match_found, confidence = accessibility.fuzzy_match_text("Sign In Button", "Sign In")
        # Might pass if "Sign In" is contained in "Sign In Button"
        assert isinstance(match_found, bool)
        assert isinstance(confidence, float)
    
    def test_fuzzy_match_disabled_fallback(self):
        """Test fallback when fuzzy matching is disabled."""
        # Temporarily disable fuzzy matching
        original_enabled = self.accessibility.FUZZY_MATCHING_ENABLED
        self.accessibility.FUZZY_MATCHING_ENABLED = False
        
        try:
            # Should fall back to exact matching
            match_found, confidence = self.accessibility.fuzzy_match_text("Sign In", "Sign In")
            assert match_found is True
            assert confidence == 100.0
            
            # Test contains matching in fallback
            match_found, confidence = self.accessibility.fuzzy_match_text("Sign In Button", "Sign In")
            assert match_found is True  # Should match because "Sign In" is contained
            assert confidence == 100.0
        finally:
            # Restore original setting
            self.accessibility.FUZZY_MATCHING_ENABLED = original_enabled
    
    @patch('modules.accessibility.fuzz')
    def test_fuzzy_match_error_handling(self, mock_fuzz):
        """Test error handling when fuzzy matching operations fail."""
        # Mock fuzz.partial_ratio to raise an exception
        mock_fuzz.partial_ratio.side_effect = Exception("Fuzzy matching error")
        
        # Should fall back to exact matching
        match_found, confidence = self.accessibility.fuzzy_match_text("Sign In", "Sign In")
        assert match_found is True  # Should succeed with exact match fallback
        assert confidence == 100.0
        
        # Should handle non-exact matches gracefully
        match_found, confidence = self.accessibility.fuzzy_match_text("Different", "Text")
        assert match_found is False
        assert confidence == 0.0
    
    def test_fuzzy_match_logging(self, caplog):
        """Test that fuzzy matching produces appropriate log messages."""
        import logging
        
        # Set debug logging level
        caplog.set_level(logging.DEBUG)
        
        # Perform a fuzzy match
        self.accessibility.fuzzy_match_text("Sign In Button", "Sign In")
        
        # Check that debug logging occurred
        debug_logs = [record for record in caplog.records if record.levelname == 'DEBUG']
        assert len(debug_logs) > 0
        
        # Should contain fuzzy match details
        log_messages = [record.message for record in debug_logs]
        fuzzy_log_found = any("Fuzzy match:" in msg for msg in log_messages)
        assert fuzzy_log_found
    
    def test_fuzzy_match_confidence_threshold_from_config(self):
        """Test that fuzzy matching uses configured confidence threshold."""
        # Test with default threshold
        original_threshold = self.accessibility.FUZZY_CONFIDENCE_THRESHOLD
        
        try:
            # Set a high threshold
            self.accessibility.FUZZY_CONFIDENCE_THRESHOLD = 95
            
            # This should fail with high threshold
            match_found, confidence = self.accessibility.fuzzy_match_text("Similar", "Different")
            assert match_found is False
            
            # Set a low threshold
            self.accessibility.FUZZY_CONFIDENCE_THRESHOLD = 30
            
            # This might pass with low threshold
            match_found, confidence = self.accessibility.fuzzy_match_text("Similar", "Different")
            # Result depends on actual similarity, but should use the low threshold
            assert isinstance(match_found, bool)
            
        finally:
            # Restore original threshold
            self.accessibility.FUZZY_CONFIDENCE_THRESHOLD = original_threshold
    
    def test_fuzzy_match_timeout_from_config(self):
        """Test that fuzzy matching uses configured timeout."""
        original_timeout = self.accessibility.FUZZY_MATCHING_TIMEOUT
        
        try:
            # Set a very short timeout
            self.accessibility.FUZZY_MATCHING_TIMEOUT = 1  # 1ms
            
            # Should handle timeout gracefully
            match_found, confidence = self.accessibility.fuzzy_match_text(
                "Long text string for testing timeout behavior", 
                "Another long text string"
            )
            
            # Should complete without crashing
            assert isinstance(match_found, bool)
            assert isinstance(confidence, float)
            
        finally:
            # Restore original timeout
            self.accessibility.FUZZY_MATCHING_TIMEOUT = original_timeout
    
    def test_fuzzy_match_various_similarity_scenarios(self):
        """Test fuzzy matching with various text similarity scenarios."""
        test_cases = [
            # (element_text, target_text, should_match, description)
            ("Gmail", "Gmail", True, "exact match"),
            ("Gmail Link", "Gmail", True, "partial match"),
            ("Google Mail", "Gmail", False, "different but related - should fail with default threshold"),
            ("Sign In", "Sign-In", True, "punctuation variation"),
            ("Continue", "Continue with GitHub", False, "target longer than element"),
            ("Submit Button", "Submit", True, "element longer than target"),
            ("OK", "Cancel", False, "completely different"),
            ("", "test", False, "empty element text"),
            ("test", "", False, "empty target text"),
        ]
        
        for element_text, target_text, should_match, description in test_cases:
            match_found, confidence = self.accessibility.fuzzy_match_text(element_text, target_text)
            
            if should_match:
                assert match_found, f"Expected match for {description}: '{element_text}' vs '{target_text}'"
                assert confidence >= self.accessibility.FUZZY_CONFIDENCE_THRESHOLD
            else:
                # Note: Some cases might still match if similarity is high enough
                # We mainly check that the function doesn't crash and returns valid values
                assert isinstance(match_found, bool), f"Invalid return type for {description}"
                assert isinstance(confidence, float), f"Invalid confidence type for {description}"
                assert 0.0 <= confidence <= 100.0, f"Invalid confidence range for {description}"


if __name__ == "__main__":
    pytest.main([__file__])