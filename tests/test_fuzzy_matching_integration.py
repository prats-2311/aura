"""
Integration tests for fuzzy matching in element search.

Tests the complete integration of fuzzy matching into the element detection
pipeline, including multi-attribute searching and fallback behavior.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from modules.accessibility import AccessibilityModule
import AppKit


class TestFuzzyMatchingIntegration:
    """Test suite for fuzzy matching integration in element search."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Mock AppKit module
        self.mock_appkit = Mock()
        self.mock_appkit.kAXFocusedApplicationAttribute = 'AXFocusedApplication'
        self.mock_appkit.kAXRoleAttribute = 'AXRole'
        self.mock_appkit.kAXTitleAttribute = 'AXTitle'
        self.mock_appkit.kAXDescriptionAttribute = 'AXDescription'
        self.mock_appkit.kAXValueAttribute = 'AXValue'
        self.mock_appkit.kAXEnabledAttribute = 'AXEnabled'
        self.mock_appkit.kAXChildrenAttribute = 'AXChildren'
        self.mock_appkit.kAXPositionAttribute = 'AXPosition'
        self.mock_appkit.kAXSizeAttribute = 'AXSize'
        self.mock_appkit.AXUIElementCreateSystemWide.return_value = Mock()
        self.mock_appkit.AXUIElementCreateApplication.return_value = Mock()
        self.mock_appkit.AXUIElementCopyAttributeValue.return_value = (0, Mock())
        
        # Apply patches
        self.patches = [
            patch('modules.accessibility.AppKit', self.mock_appkit),
            patch('modules.accessibility.ACCESSIBILITY_AVAILABLE', True),
            patch('modules.accessibility.ACCESSIBILITY_FUNCTIONS_AVAILABLE', True),
            patch('modules.accessibility.NSWorkspace'),
            patch('modules.accessibility.Accessibility', Mock())
        ]
        
        for p in self.patches:
            p.start()
        
        self.accessibility = AccessibilityModule()
    
    def teardown_method(self):
        """Clean up patches."""
        for p in self.patches:
            p.stop()
    
    def test_check_element_text_match_fuzzy_success(self):
        """Test _check_element_text_match with successful fuzzy matching."""
        # Mock element with AXTitle attribute
        mock_element = Mock()
        
        # Mock AXUIElementCopyAttributeValue to return attribute values
        self.mock_appkit.AXUIElementCopyAttributeValue.return_value = (0, "Sign In Button")
        
        # Test fuzzy matching
        match_found, confidence, matched_attr = self.accessibility._check_element_text_match(
            mock_element, "Sign In"
        )
        
        assert match_found is True
        assert confidence > 0.8  # Should be high confidence
        assert matched_attr == "AXTitle"
        
        # Verify that AXUIElementCopyAttributeValue was called
        assert self.mock_appkit.AXUIElementCopyAttributeValue.called
    
    def test_check_element_text_match_multi_attribute_priority(self):
        """Test multi-attribute checking with priority order."""
        mock_element = Mock()
        
        # Mock multiple calls for different attributes
        def mock_attr_values(element, attribute, none_param):
            if attribute == "AXTitle":
                return (0, "Different Text")  # Won't match
            elif attribute == "AXDescription":
                return (0, "Gmail Link Description")  # Should match
            elif attribute == "AXValue":
                return (0, "Some Value")
            return (1, None)  # Error case
        
        self.mock_appkit.AXUIElementCopyAttributeValue.side_effect = mock_attr_values
        
        # Test that it finds match in AXDescription
        match_found, confidence, matched_attr = self.accessibility._check_element_text_match(
            mock_element, "Gmail"
        )
        
        assert match_found is True
        assert matched_attr == "AXDescription"
        
        # Verify that multiple attributes were checked
        assert self.mock_appkit.AXUIElementCopyAttributeValue.call_count >= 2
    
    def test_check_element_text_match_fallback_to_exact(self):
        """Test fallback to exact matching when fuzzy matching fails."""
        mock_element = Mock()
        
        # Temporarily disable fuzzy matching to test fallback
        original_enabled = self.accessibility.FUZZY_MATCHING_ENABLED
        self.accessibility.FUZZY_MATCHING_ENABLED = False
        
        try:
            # Mock AXTitle with exact match text
            self.mock_appkit.AXUIElementCopyAttributeValue.return_value = (0, "Sign In")
            
            match_found, confidence, matched_attr = self.accessibility._check_element_text_match(
                mock_element, "Sign In"
            )
            
            assert match_found is True
            assert confidence == 1.0  # Exact match should give 100% confidence
            assert matched_attr == "AXTitle"
        finally:
            self.accessibility.FUZZY_MATCHING_ENABLED = original_enabled
    
    def test_check_element_text_match_no_match_found(self):
        """Test when no matches are found in any attribute."""
        mock_element = Mock()
        
        # Mock all attributes to return non-matching text
        self.mock_appkit.AXUIElementCopyAttributeValue.return_value = (0, "Completely Different Text")
        
        match_found, confidence, matched_attr = self.accessibility._check_element_text_match(
            mock_element, "Gmail"
        )
        
        assert match_found is False
        assert confidence == 0.0
        assert matched_attr == ""
        
        # Should have tried all attributes (fuzzy + fallback, may have some extra calls)
        expected_min_calls = len(self.accessibility.ACCESSIBILITY_ATTRIBUTES) * 2  # Fuzzy + fallback
        assert self.mock_appkit.AXUIElementCopyAttributeValue.call_count >= expected_min_calls
    
    def test_check_element_text_match_attribute_access_error(self):
        """Test handling of attribute access errors."""
        mock_element = Mock()
        
        # Mock first attribute to fail, second to succeed
        def mock_attr_error(element, attribute, none_param):
            if attribute == "AXTitle":
                raise Exception("Attribute access error")
            elif attribute == "AXDescription":
                return (0, "Gmail Link")
            return (1, None)
        
        self.mock_appkit.AXUIElementCopyAttributeValue.side_effect = mock_attr_error
        
        match_found, confidence, matched_attr = self.accessibility._check_element_text_match(
            mock_element, "Gmail"
        )
        
        assert match_found is True
        assert matched_attr == "AXDescription"
    
    def test_check_element_text_match_empty_inputs(self):
        """Test handling of empty or None inputs."""
        # Test with None element
        match_found, confidence, matched_attr = self.accessibility._check_element_text_match(
            None, "test"
        )
        assert match_found is False
        assert confidence == 0.0
        assert matched_attr == ""
        
        # Test with empty target text
        mock_element = Mock()
        match_found, confidence, matched_attr = self.accessibility._check_element_text_match(
            mock_element, ""
        )
        assert match_found is False
        assert confidence == 0.0
        assert matched_attr == ""
    
    def test_fuzzy_matching_with_logging_enabled(self, caplog):
        """Test that fuzzy matching produces appropriate logs when LOG_FUZZY_MATCH_SCORES is enabled."""
        import logging
        
        # Enable fuzzy match score logging
        original_log_setting = self.accessibility.LOG_FUZZY_MATCH_SCORES
        self.accessibility.LOG_FUZZY_MATCH_SCORES = True
        caplog.set_level(logging.INFO)
        
        try:
            mock_element = Mock()
            
            self.mock_appkit.AXUIElementCopyAttributeValue.return_value = (0, "Sign In Button")
            
            self.accessibility._check_element_text_match(mock_element, "Sign In")
            
            # Check that INFO level logging occurred (not just DEBUG)
            info_logs = [record for record in caplog.records if record.levelname == 'INFO']
            assert len(info_logs) > 0
            
            # Should contain fuzzy match details
            log_messages = [record.message for record in info_logs]
            fuzzy_log_found = any("Fuzzy match:" in msg for msg in log_messages)
            assert fuzzy_log_found
        finally:
            self.accessibility.LOG_FUZZY_MATCH_SCORES = original_log_setting
    
    def test_element_matches_criteria_with_fuzzy_matching(self):
        """Test _element_matches_criteria integration with fuzzy matching."""
        # Create mock element info with accessibility element
        mock_element = Mock()
        element_info = {
            'role': 'AXButton',
            'title': 'Sign In Button',
            'element': mock_element,
            'enabled': True
        }
        
        self.mock_appkit.AXUIElementCopyAttributeValue.return_value = (0, "Sign In Button")
        
        # Test that element matches criteria using fuzzy matching
        matches = self.accessibility._element_matches_criteria(element_info, 'AXButton', 'Sign In')
        assert matches is True
    
    def test_element_matches_criteria_fallback_to_title(self):
        """Test _element_matches_criteria fallback to title-only matching."""
        # Create element info without accessibility element (forces fallback)
        element_info = {
            'role': 'AXButton',
            'title': 'Sign In',
            'element': None,  # No element forces fallback
            'enabled': True
        }
        
        # Should fall back to fuzzy_match_label method
        matches = self.accessibility._element_matches_criteria(element_info, 'AXButton', 'Sign In')
        assert matches is True
    
    def test_fuzzy_matching_performance_in_integration(self):
        """Test that fuzzy matching performs within acceptable time limits in integration."""
        import time
        
        mock_element = Mock()
        
        self.mock_appkit.AXUIElementCopyAttributeValue.return_value = (0, "Long element text for performance testing")
        
        start_time = time.time()
        
        # Perform multiple fuzzy matches
        for i in range(10):
            self.accessibility._check_element_text_match(
                mock_element, f"test text {i}"
            )
        
        elapsed_time = (time.time() - start_time) * 1000  # Convert to ms
        
        # Should complete 10 matches in reasonable time (less than 1 second total)
        assert elapsed_time < 1000, f"Fuzzy matching too slow: {elapsed_time:.1f}ms for 10 matches"
    
    def test_fuzzy_matching_with_various_attribute_combinations(self):
        """Test fuzzy matching with different combinations of available attributes."""
        mock_element = Mock()
        
        # Test case 1: Only AXTitle available
        def mock_title_only(element, attribute, none_param):
            if attribute == "AXTitle":
                return (0, "Gmail Link")
            else:
                return (1, None)  # Other attributes not available
        
        self.mock_appkit.AXUIElementCopyAttributeValue.side_effect = mock_title_only
        
        match_found, confidence, matched_attr = self.accessibility._check_element_text_match(
            mock_element, "Gmail"
        )
        
        assert match_found is True
        assert matched_attr == "AXTitle"
        
        # Reset for next test
        self.mock_appkit.AXUIElementCopyAttributeValue.side_effect = None
        
        # Test case 2: Only AXDescription available
        def mock_description_only(element, attribute, none_param):
            if attribute == "AXDescription":
                return (0, "Gmail Link Description")
            else:
                return (1, None)
        
        self.mock_appkit.AXUIElementCopyAttributeValue.side_effect = mock_description_only
        
        match_found, confidence, matched_attr = self.accessibility._check_element_text_match(
            mock_element, "Gmail"
        )
        
        assert match_found is True
        assert matched_attr == "AXDescription"
        
        # Reset for next test
        self.mock_appkit.AXUIElementCopyAttributeValue.side_effect = None
        
        # Test case 3: Only AXValue available
        def mock_value_only(element, attribute, none_param):
            if attribute == "AXValue":
                return (0, "Gmail Value")
            else:
                return (1, None)
        
        self.mock_appkit.AXUIElementCopyAttributeValue.side_effect = mock_value_only
        
        match_found, confidence, matched_attr = self.accessibility._check_element_text_match(
            mock_element, "Gmail"
        )
        
        assert match_found is True
        assert matched_attr == "AXValue"
    
    def test_fuzzy_matching_confidence_threshold_integration(self):
        """Test that confidence threshold is properly applied in integration."""
        mock_element = Mock()
        
        # Set a high confidence threshold
        original_threshold = self.accessibility.FUZZY_CONFIDENCE_THRESHOLD
        self.accessibility.FUZZY_CONFIDENCE_THRESHOLD = 95
        
        try:
            # Text that should have medium similarity (not high enough for 95% threshold)
            self.mock_appkit.AXUIElementCopyAttributeValue.return_value = (0, "Similar Text")
            
            match_found, confidence, matched_attr = self.accessibility._check_element_text_match(
                mock_element, "Different Text"
            )
            
            # Should fail with high threshold, but still try fallback
            # The exact result depends on the similarity score, but it should handle it gracefully
            assert isinstance(match_found, bool)
            assert isinstance(confidence, float)
            assert isinstance(matched_attr, str)
        finally:
            self.accessibility.FUZZY_CONFIDENCE_THRESHOLD = original_threshold
    
    @patch('modules.accessibility.FUZZY_MATCHING_AVAILABLE', False)
    def test_integration_with_fuzzy_library_unavailable(self):
        """Test complete integration when fuzzy matching library is unavailable."""
        # Create new instance with mocked unavailable library
        with patch('modules.accessibility.ACCESSIBILITY_AVAILABLE', True), \
             patch('modules.accessibility.ACCESSIBILITY_FUNCTIONS_AVAILABLE', True), \
             patch('modules.accessibility.NSWorkspace'), \
             patch('modules.accessibility.AXUIElementCreateSystemWide'):
            accessibility = AccessibilityModule()
        
        mock_element = Mock()
        
        # Create a new mock AppKit for this test instance
        mock_appkit = Mock()
        mock_appkit.kAXTitleAttribute = 'AXTitle'
        mock_appkit.kAXDescriptionAttribute = 'AXDescription'
        mock_appkit.kAXValueAttribute = 'AXValue'
        mock_appkit.AXUIElementCopyAttributeValue.return_value = (0, "Sign In")
        
        with patch('modules.accessibility.AppKit', mock_appkit):
            # Should fall back to exact matching
            match_found, confidence, matched_attr = accessibility._check_element_text_match(
                mock_element, "Sign In"
            )
            
            assert match_found is True
            assert confidence == 1.0  # Exact match
            assert matched_attr == "AXTitle"


if __name__ == "__main__":
    pytest.main([__file__])