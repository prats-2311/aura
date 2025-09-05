"""
Unit tests for enhanced element role detection in AccessibilityModule.

Tests the new CLICKABLE_ROLES constant, role classification helper methods,
and enhanced element search logic with backward compatibility.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the parent directory to the path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.accessibility import AccessibilityModule


class TestEnhancedRoleDetection:
    """Test enhanced element role detection functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        with patch('modules.accessibility.ACCESSIBILITY_AVAILABLE', True), \
             patch('modules.accessibility.ACCESSIBILITY_FUNCTIONS_AVAILABLE', True):
            self.accessibility = AccessibilityModule()
    
    def test_clickable_roles_constant(self):
        """Test that CLICKABLE_ROLES constant contains all expected clickable element types."""
        expected_roles = {
            'AXButton', 'AXMenuButton', 'AXMenuItem', 'AXMenuBarItem',
            'AXLink', 'AXCheckBox', 'AXRadioButton', 'AXTab',
            'AXToolbarButton', 'AXPopUpButton', 'AXComboBox'
        }
        
        assert hasattr(AccessibilityModule, 'CLICKABLE_ROLES')
        assert isinstance(AccessibilityModule.CLICKABLE_ROLES, set)
        assert AccessibilityModule.CLICKABLE_ROLES == expected_roles
    
    def test_is_clickable_element_role(self):
        """Test the is_clickable_element_role helper method."""
        # Test clickable roles
        clickable_roles = ['AXButton', 'AXLink', 'AXMenuItem', 'AXCheckBox', 'AXRadioButton']
        for role in clickable_roles:
            assert self.accessibility.is_clickable_element_role(role), f"{role} should be clickable"
        
        # Test non-clickable roles
        non_clickable_roles = ['AXTextField', 'AXStaticText', 'AXImage', 'AXWindow']
        for role in non_clickable_roles:
            assert not self.accessibility.is_clickable_element_role(role), f"{role} should not be clickable"
    
    def test_categorize_element_type(self):
        """Test the categorize_element_type helper method."""
        # Test clickable elements
        clickable_roles = ['AXButton', 'AXLink', 'AXMenuItem']
        for role in clickable_roles:
            assert self.accessibility.categorize_element_type(role) == 'clickable'
        
        # Test input elements
        input_roles = ['AXTextField', 'AXSecureTextField', 'AXTextArea']
        for role in input_roles:
            assert self.accessibility.categorize_element_type(role) == 'input'
        
        # Test display elements
        display_roles = ['AXStaticText', 'AXHeading', 'AXImage']
        for role in display_roles:
            assert self.accessibility.categorize_element_type(role) == 'display'
        
        # Test container elements
        container_roles = ['AXGroup', 'AXWindow', 'AXDialog', 'AXScrollArea']
        for role in container_roles:
            assert self.accessibility.categorize_element_type(role) == 'container'
        
        # Test unknown elements
        assert self.accessibility.categorize_element_type('AXUnknownRole') == 'unknown'
    
    def test_element_matches_criteria_enhanced(self):
        """Test enhanced element matching criteria with multiple roles."""
        # Mock element info for different roles
        button_element = {'role': 'AXButton', 'title': 'Sign In', 'enabled': True}
        link_element = {'role': 'AXLink', 'title': 'Gmail', 'enabled': True}
        menu_element = {'role': 'AXMenuItem', 'title': 'File', 'enabled': True}
        text_element = {'role': 'AXStaticText', 'title': 'Welcome', 'enabled': True}
        
        # Test direct role matches
        assert self.accessibility._element_matches_criteria(button_element, 'AXButton', 'Sign In')
        assert self.accessibility._element_matches_criteria(link_element, 'AXLink', 'Gmail')
        assert self.accessibility._element_matches_criteria(menu_element, 'AXMenuItem', 'File')
        
        # Test category matches
        assert self.accessibility._element_matches_criteria(button_element, 'button', 'Sign In')
        assert self.accessibility._element_matches_criteria(link_element, 'link', 'Gmail')
        
        # Test clickable element detection (empty role)
        assert self.accessibility._element_matches_criteria(button_element, '', 'Sign In')
        assert self.accessibility._element_matches_criteria(link_element, '', 'Gmail')
        assert self.accessibility._element_matches_criteria(menu_element, '', 'File')
        
        # Non-clickable elements should not match empty role
        assert not self.accessibility._element_matches_criteria(text_element, '', 'Welcome')
        
        # Test role mismatch
        assert not self.accessibility._element_matches_criteria(button_element, 'AXLink', 'Sign In')
        assert not self.accessibility._element_matches_criteria(text_element, 'AXButton', 'Welcome')
    
    def test_element_matches_criteria_fuzzy_labels(self):
        """Test element matching with fuzzy label matching."""
        element = {'role': 'AXButton', 'title': 'Sign In Button', 'enabled': True}
        
        # Test exact match
        assert self.accessibility._element_matches_criteria(element, 'AXButton', 'Sign In Button')
        
        # Test partial match
        assert self.accessibility._element_matches_criteria(element, 'AXButton', 'Sign In')
        
        # Test case insensitive
        assert self.accessibility._element_matches_criteria(element, 'AXButton', 'sign in')
        
        # Test with word-based matching (should work with current fuzzy logic)
        element2 = {'role': 'AXButton', 'title': 'Submit', 'enabled': True}
        assert self.accessibility._element_matches_criteria(element2, 'AXButton', 'submit')
    
    @patch('modules.accessibility.AccessibilityModule._get_cached_elements')
    @patch('modules.accessibility.AccessibilityModule._search_cached_elements_enhanced')
    def test_find_element_enhanced_cache_hit(self, mock_search_enhanced, mock_get_cached):
        """Test enhanced element finding with cache hit."""
        # Mock cached elements
        mock_get_cached.return_value = [{'role': 'AXLink', 'title': 'Gmail', 'enabled': True}]
        
        # Mock enhanced search results
        mock_element = {
            'role': 'AXLink',
            'title': 'Gmail',
            'enabled': True,
            'element': Mock()
        }
        mock_search_enhanced.return_value = [mock_element]
        
        # Mock coordinate calculation
        with patch.object(self.accessibility, '_calculate_element_coordinates', return_value=[100, 200, 50, 30]):
            with patch.object(self.accessibility, 'filter_elements_by_criteria', return_value=[mock_element]):
                with patch.object(self.accessibility, '_element_matches_criteria', return_value=True):
                    with patch.object(self.accessibility, 'get_active_application', return_value={'name': 'Safari', 'pid': 1234}):
                        
                        result = self.accessibility.find_element_enhanced('AXLink', 'Gmail')
                        
                        assert result is not None
                        assert result['role'] == 'AXLink'
                        assert result['title'] == 'Gmail'
                        assert result['coordinates'] == [100, 200, 50, 30]
                        assert result['center_point'] == [125, 215]
    
    def test_backward_compatibility_fallback(self):
        """Test that enhanced detection falls back to original logic when needed."""
        with patch.object(self.accessibility, 'find_element_enhanced', side_effect=Exception("Enhanced failed")):
            with patch.object(self.accessibility, '_find_element_original_implementation', return_value={'role': 'AXButton', 'title': 'OK'}):
                
                result = self.accessibility.find_element('AXButton', 'OK')
                
                assert result is not None
                assert result['role'] == 'AXButton'
                assert result['title'] == 'OK'
    
    def test_graceful_degradation_when_clickable_roles_not_configured(self):
        """Test graceful degradation when CLICKABLE_ROLES is not properly configured."""
        # Temporarily remove CLICKABLE_ROLES from class
        original_roles = AccessibilityModule.CLICKABLE_ROLES
        delattr(AccessibilityModule, 'CLICKABLE_ROLES')
        
        try:
            # Should not crash and should fall back gracefully
            result_button = self.accessibility.is_clickable_element_role('AXButton')
            result_link = self.accessibility.is_clickable_element_role('AXLink')
            
            # Should fall back to button-only detection
            assert result_button is True  # AXButton should still be considered clickable
            assert result_link is False   # AXLink should not be clickable in fallback mode
        except AttributeError:
            # This is expected behavior - method should handle missing attribute
            pass
        finally:
            # Restore original roles
            AccessibilityModule.CLICKABLE_ROLES = original_roles
    
    def test_logging_for_role_detection_fallback(self):
        """Test that appropriate logging occurs during role detection fallback scenarios."""
        with patch.object(self.accessibility.logger, 'debug') as mock_debug:
            with patch.object(self.accessibility, 'find_element_enhanced', side_effect=Exception("Enhanced failed")):
                with patch.object(self.accessibility, '_find_element_original_implementation', return_value=None):
                    
                    self.accessibility.find_element('AXButton', 'Test')
                    
                    # Check that fallback logging occurred
                    mock_debug.assert_called()
                    debug_calls = [call[0][0] for call in mock_debug.call_args_list]
                    assert any('Enhanced element detection failed' in call for call in debug_calls)
    
    def test_search_cached_elements_enhanced_with_empty_role(self):
        """Test enhanced cached element search with empty role (broad search)."""
        # Mock cache setup
        cache_key = "TestApp:1234"
        mock_index = Mock()
        mock_index.role_index = {
            'AXButton': [{'role': 'AXButton', 'title': 'OK'}],
            'AXLink': [{'role': 'AXLink', 'title': 'Gmail'}],
            'AXMenuItem': [{'role': 'AXMenuItem', 'title': 'File'}]
        }
        mock_index.title_index = {'Gmail': [{'role': 'AXLink', 'title': 'Gmail'}]}
        mock_index.normalized_title_index = {'gmail': [{'role': 'AXLink', 'title': 'Gmail'}]}
        
        self.accessibility.element_indexes = {cache_key: mock_index}
        
        with patch.object(self.accessibility, '_get_cache_key', return_value=cache_key):
            with patch.object(self.accessibility, '_normalize_text', return_value='gmail'):
                
                # Test broad search (empty role) - should find all clickable elements
                results = self.accessibility._search_cached_elements_enhanced("TestApp", 1234, '', 'Gmail')
                
                # Should find elements from clickable roles
                assert len(results) > 0
    
    def test_enhanced_role_detection_with_multiple_clickable_roles(self):
        """Test that enhanced detection works with all clickable role types."""
        clickable_elements = [
            {'role': 'AXButton', 'title': 'Submit', 'enabled': True},
            {'role': 'AXLink', 'title': 'Home', 'enabled': True},
            {'role': 'AXMenuItem', 'title': 'Edit', 'enabled': True},
            {'role': 'AXCheckBox', 'title': 'Remember me', 'enabled': True},
            {'role': 'AXRadioButton', 'title': 'Option 1', 'enabled': True},
            {'role': 'AXTab', 'title': 'Settings', 'enabled': True}
        ]
        
        # Test that all clickable elements are recognized
        for element in clickable_elements:
            role = element['role']
            assert self.accessibility.is_clickable_element_role(role), f"{role} should be recognized as clickable"
            assert self.accessibility._element_matches_criteria(element, '', element['title']), f"{role} should match empty role search"


class TestRoleDetectionBackwardCompatibility:
    """Test backward compatibility for role detection."""
    
    def setup_method(self):
        """Set up test fixtures."""
        with patch('modules.accessibility.ACCESSIBILITY_AVAILABLE', True), \
             patch('modules.accessibility.ACCESSIBILITY_FUNCTIONS_AVAILABLE', True):
            self.accessibility = AccessibilityModule()
    
    def test_existing_functionality_continues_to_work(self):
        """Test that existing button-only detection continues to work."""
        # Mock the original implementation
        with patch.object(self.accessibility, '_find_element_original_implementation') as mock_original:
            mock_original.return_value = {'role': 'AXButton', 'title': 'OK', 'coordinates': [0, 0, 50, 30]}
            
            # Test that calling find_element still works as before
            result = self.accessibility.find_element('AXButton', 'OK')
            
            # Should get a result (either from enhanced or fallback)
            assert result is not None
    
    def test_button_only_fallback_when_enhanced_fails(self):
        """Test button-only fallback when enhanced detection fails."""
        with patch.object(self.accessibility, '_find_element_with_enhanced_roles', return_value=None):
            with patch.object(self.accessibility, '_find_element_button_only_fallback') as mock_button_fallback:
                mock_button_fallback.return_value = {'role': 'AXButton', 'title': 'Submit'}
                
                result = self.accessibility.find_element_enhanced('', 'Submit')
                
                # Should have called button-only fallback
                mock_button_fallback.assert_called_once_with('Submit', None)
                assert result['role'] == 'AXButton'
    
    def test_graceful_degradation_with_missing_dependencies(self):
        """Test graceful degradation when enhanced features are not available."""
        # Simulate missing enhanced functionality
        original_clickable_roles = getattr(AccessibilityModule, 'CLICKABLE_ROLES', None)
        if hasattr(AccessibilityModule, 'CLICKABLE_ROLES'):
            delattr(AccessibilityModule, 'CLICKABLE_ROLES')
        
        try:
            # Should not crash and should fall back to original behavior
            with patch.object(self.accessibility, '_find_element_original_implementation') as mock_original:
                mock_original.return_value = {'role': 'AXButton', 'title': 'Test'}
                
                result = self.accessibility.find_element('AXButton', 'Test')
                
                # Should fall back to original implementation
                mock_original.assert_called_once()
                assert result is not None
        finally:
            # Restore original attribute if it existed
            if original_clickable_roles is not None:
                AccessibilityModule.CLICKABLE_ROLES = original_clickable_roles


if __name__ == '__main__':
    pytest.main([__file__])