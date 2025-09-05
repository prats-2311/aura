"""
Tests for backward compatibility and graceful degradation in enhanced role detection.

Verifies that existing functionality continues to work and appropriate logging
occurs during fallback scenarios.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the parent directory to the path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.accessibility import AccessibilityModule


class TestBackwardCompatibility:
    """Test backward compatibility for enhanced role detection."""
    
    def setup_method(self):
        """Set up test fixtures."""
        with patch('modules.accessibility.ACCESSIBILITY_AVAILABLE', True), \
             patch('modules.accessibility.ACCESSIBILITY_FUNCTIONS_AVAILABLE', True):
            self.accessibility = AccessibilityModule()
    
    def test_enhanced_role_detection_availability_check(self):
        """Test the availability check for enhanced role detection."""
        # Should be available by default
        assert self.accessibility.is_enhanced_role_detection_available() is True
        
        # Test when CLICKABLE_ROLES is missing
        original_roles = AccessibilityModule.CLICKABLE_ROLES
        delattr(AccessibilityModule, 'CLICKABLE_ROLES')
        
        try:
            assert self.accessibility.is_enhanced_role_detection_available() is False
        finally:
            AccessibilityModule.CLICKABLE_ROLES = original_roles
    
    def test_graceful_degradation_when_enhanced_not_available(self):
        """Test graceful degradation when enhanced features are not available."""
        with patch.object(self.accessibility, 'is_enhanced_role_detection_available', return_value=False):
            with patch.object(self.accessibility, '_find_element_original_fallback') as mock_fallback:
                mock_fallback.return_value = {'role': 'AXButton', 'title': 'Test'}
                
                result = self.accessibility.find_element_enhanced('AXButton', 'Test')
                
                mock_fallback.assert_called_once_with('AXButton', 'Test', None)
                assert result['role'] == 'AXButton'
    
    def test_logging_for_enhanced_detection_failure(self):
        """Test that appropriate logging occurs when enhanced detection fails."""
        with patch.object(self.accessibility.logger, 'warning') as mock_warning:
            with patch.object(self.accessibility.logger, 'info') as mock_info:
                with patch.object(self.accessibility, '_find_element_with_enhanced_roles', side_effect=Exception("Test error")):
                    with patch.object(self.accessibility, '_find_element_original_fallback', return_value=None):
                        
                        self.accessibility.find_element_enhanced('AXButton', 'Test')
                        
                        # Should log the failure
                        mock_warning.assert_called()
                        warning_calls = [call[0][0] for call in mock_warning.call_args_list]
                        assert any('Enhanced element detection failed' in call for call in warning_calls)
    
    def test_logging_for_button_only_fallback(self):
        """Test logging during button-only fallback scenarios."""
        with patch.object(self.accessibility.logger, 'info') as mock_info:
            with patch.object(self.accessibility, '_find_element_with_enhanced_roles', return_value=None):
                with patch.object(self.accessibility, '_find_element_original_fallback', return_value={'role': 'AXButton', 'title': 'Test'}):
                    
                    result = self.accessibility.find_element_enhanced('', 'Test')
                    
                    # Should log the fallback
                    mock_info.assert_called()
                    info_calls = [call[0][0] for call in mock_info.call_args_list]
                    assert any('falling back to button-only detection' in call for call in info_calls)
    
    def test_logging_for_original_fallback(self):
        """Test logging during original implementation fallback."""
        with patch.object(self.accessibility.logger, 'info') as mock_info:
            with patch.object(self.accessibility, '_find_element_with_strict_role_matching', return_value={'role': 'AXButton', 'title': 'Test'}):
                
                result = self.accessibility._find_element_original_fallback('AXButton', 'Test')
                
                # Should log the fallback usage
                mock_info.assert_called()
                info_calls = [call[0][0] for call in mock_info.call_args_list]
                assert any('Using original fallback detection' in call for call in info_calls)
                assert any('Original fallback succeeded' in call for call in info_calls)
    
    def test_strict_role_matching_functionality(self):
        """Test that strict role matching works correctly."""
        mock_element = Mock()
        mock_elements = [
            {'role': 'AXButton', 'title': 'Submit', 'enabled': True, 'element': mock_element},
            {'role': 'AXLink', 'title': 'Submit', 'enabled': True, 'element': mock_element},  # Same title, different role
            {'role': 'AXButton', 'title': 'Cancel', 'enabled': True, 'element': mock_element}  # Same role, different title
        ]
        
        with patch.object(self.accessibility, 'get_active_application', return_value={'name': 'TestApp', 'pid': 1234}):
            with patch.object(self.accessibility, '_get_target_application_element', return_value=mock_element):
                with patch.object(self.accessibility, 'traverse_accessibility_tree', return_value=mock_elements):
                    with patch.object(self.accessibility, '_calculate_element_coordinates', return_value=[100, 100, 50, 30]):
                        
                        # Should find only the exact role match
                        result = self.accessibility._find_element_with_strict_role_matching('AXButton', 'Submit')
                        
                        assert result is not None
                        assert result['role'] == 'AXButton'
                        assert result['title'] == 'Submit'
    
    def test_existing_functionality_preserved(self):
        """Test that existing find_element functionality is preserved."""
        # Mock the enhanced method to fail, forcing fallback
        with patch.object(self.accessibility, 'find_element_enhanced', side_effect=Exception("Enhanced failed")):
            with patch.object(self.accessibility, '_find_element_original_implementation') as mock_original:
                mock_original.return_value = {
                    'role': 'AXButton',
                    'title': 'OK',
                    'coordinates': [0, 0, 50, 30],
                    'center_point': [25, 15],
                    'enabled': True,
                    'app_name': 'TestApp'
                }
                
                # This should work exactly as before
                result = self.accessibility.find_element('AXButton', 'OK')
                
                assert result is not None
                assert result['role'] == 'AXButton'
                assert result['title'] == 'OK'
                mock_original.assert_called_once_with('AXButton', 'OK', None)
    
    def test_categorize_element_type_graceful_degradation(self):
        """Test that element type categorization degrades gracefully."""
        # Test normal operation
        assert self.accessibility.categorize_element_type('AXButton') == 'clickable'
        
        # Test graceful degradation when CLICKABLE_ROLES is missing
        original_roles = AccessibilityModule.CLICKABLE_ROLES
        delattr(AccessibilityModule, 'CLICKABLE_ROLES')
        
        try:
            # Should still work for basic button detection
            assert self.accessibility.categorize_element_type('AXButton') == 'clickable'
            assert self.accessibility.categorize_element_type('AXTextField') == 'input'
            assert self.accessibility.categorize_element_type('AXLink') == 'unknown'  # Not in fallback
        finally:
            AccessibilityModule.CLICKABLE_ROLES = original_roles
    
    def test_is_clickable_element_role_graceful_degradation(self):
        """Test that clickable role checking degrades gracefully."""
        # Test normal operation
        assert self.accessibility.is_clickable_element_role('AXButton') is True
        assert self.accessibility.is_clickable_element_role('AXLink') is True
        
        # Test graceful degradation when CLICKABLE_ROLES is missing
        original_roles = AccessibilityModule.CLICKABLE_ROLES
        delattr(AccessibilityModule, 'CLICKABLE_ROLES')
        
        try:
            with patch.object(self.accessibility.logger, 'debug') as mock_debug:
                # Should fall back to button-only detection
                assert self.accessibility.is_clickable_element_role('AXButton') is True
                assert self.accessibility.is_clickable_element_role('AXLink') is False
                
                # Should log the fallback
                mock_debug.assert_called()
                debug_calls = [call[0][0] for call in mock_debug.call_args_list]
                assert any('CLICKABLE_ROLES not configured' in call for call in debug_calls)
        finally:
            AccessibilityModule.CLICKABLE_ROLES = original_roles
    
    def test_integration_with_existing_caching_system(self):
        """Test that enhanced role detection integrates properly with existing caching."""
        mock_element = Mock()
        cached_elements = [
            {'role': 'AXButton', 'title': 'Submit', 'enabled': True, 'element': mock_element},
            {'role': 'AXLink', 'title': 'Home', 'enabled': True, 'element': mock_element}
        ]
        
        with patch.object(self.accessibility, 'get_active_application', return_value={'name': 'TestApp', 'pid': 1234}):
            with patch.object(self.accessibility, '_get_cached_elements', return_value=cached_elements):
                with patch.object(self.accessibility, '_search_cached_elements_enhanced', return_value=[cached_elements[1]]):
                    with patch.object(self.accessibility, 'filter_elements_by_criteria', return_value=[cached_elements[1]]):
                        with patch.object(self.accessibility, '_element_matches_criteria', return_value=True):
                            with patch.object(self.accessibility, '_calculate_element_coordinates', return_value=[100, 100, 50, 30]):
                                
                                # Should use cached elements with enhanced detection
                                result = self.accessibility.find_element_enhanced('AXLink', 'Home')
                                
                                assert result is not None
                                assert result['role'] == 'AXLink'
                                assert result['title'] == 'Home'
    
    def test_error_recovery_in_fallback_scenarios(self):
        """Test error recovery during various fallback scenarios."""
        # Test recovery when enhanced detection throws exception
        with patch.object(self.accessibility, '_find_element_with_enhanced_roles', side_effect=Exception("Enhanced error")):
            with patch.object(self.accessibility, '_find_element_original_fallback') as mock_fallback:
                mock_fallback.return_value = {'role': 'AXButton', 'title': 'Recovered'}
                
                result = self.accessibility.find_element_enhanced('AXButton', 'Test')
                
                assert result is not None
                assert result['title'] == 'Recovered'
                mock_fallback.assert_called_once()
        
        # Test recovery when button-only fallback throws exception
        with patch.object(self.accessibility, '_find_element_with_enhanced_roles', return_value=None):
            with patch.object(self.accessibility, '_find_element_button_only_fallback', side_effect=Exception("Button fallback error")):
                with patch.object(self.accessibility, '_find_element_original_fallback') as mock_original:
                    mock_original.return_value = {'role': 'AXButton', 'title': 'Final Recovery'}
                    
                    # This should trigger the final fallback in the exception handler
                    result = self.accessibility.find_element_enhanced('', 'Test')
                    
                    # The exception should be caught and final fallback called
                    mock_original.assert_called()


if __name__ == '__main__':
    pytest.main([__file__])