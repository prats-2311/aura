"""
Integration tests for enhanced element role detection.

Tests that verify existing functionality continues to work while new enhanced
features are properly integrated.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the parent directory to the path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.accessibility import AccessibilityModule


class TestEnhancedRoleIntegration:
    """Integration tests for enhanced role detection."""
    
    def setup_method(self):
        """Set up test fixtures."""
        with patch('modules.accessibility.ACCESSIBILITY_AVAILABLE', True), \
             patch('modules.accessibility.ACCESSIBILITY_FUNCTIONS_AVAILABLE', True):
            self.accessibility = AccessibilityModule()
    
    def test_existing_button_detection_still_works(self):
        """Test that existing button detection functionality is preserved."""
        # Mock the necessary components for a complete test
        mock_app = Mock()
        mock_app.localizedName.return_value = "TestApp"
        mock_app.processIdentifier.return_value = 1234
        
        mock_element = Mock()
        mock_button_info = {
            'role': 'AXButton',
            'title': 'Submit',
            'enabled': True,
            'element': mock_element
        }
        
        with patch.object(self.accessibility, 'get_active_application', return_value={'name': 'TestApp', 'pid': 1234}):
            with patch.object(self.accessibility, '_get_cached_elements', return_value=None):
                with patch.object(self.accessibility, '_get_target_application_element', return_value=mock_element):
                    with patch.object(self.accessibility, 'traverse_accessibility_tree', return_value=[mock_button_info]):
                        with patch.object(self.accessibility, '_calculate_element_coordinates', return_value=[100, 200, 50, 30]):
                            
                            # Test that we can still find buttons using the original method signature
                            result = self.accessibility.find_element('AXButton', 'Submit')
                            
                            assert result is not None
                            assert result['role'] == 'AXButton'
                            assert result['title'] == 'Submit'
                            assert result['coordinates'] == [100, 200, 50, 30]
    
    def test_enhanced_detection_finds_links(self):
        """Test that enhanced detection can find link elements."""
        mock_app = Mock()
        mock_app.localizedName.return_value = "Safari"
        mock_app.processIdentifier.return_value = 5678
        
        mock_element = Mock()
        mock_link_info = {
            'role': 'AXLink',
            'title': 'Gmail',
            'enabled': True,
            'element': mock_element
        }
        
        with patch.object(self.accessibility, 'get_active_application', return_value={'name': 'Safari', 'pid': 5678}):
            with patch.object(self.accessibility, '_get_cached_elements', return_value=None):
                with patch.object(self.accessibility, '_get_target_application_element', return_value=mock_element):
                    with patch.object(self.accessibility, 'traverse_accessibility_tree', return_value=[mock_link_info]):
                        with patch.object(self.accessibility, '_calculate_element_coordinates', return_value=[200, 300, 80, 25]):
                            
                            # Test that enhanced detection can find links
                            result = self.accessibility.find_element('AXLink', 'Gmail')
                            
                            assert result is not None
                            assert result['role'] == 'AXLink'
                            assert result['title'] == 'Gmail'
                            assert result['coordinates'] == [200, 300, 80, 25]
    
    def test_broad_search_with_empty_role(self):
        """Test that broad search (empty role) finds clickable elements."""
        mock_element = Mock()
        mock_elements = [
            {'role': 'AXButton', 'title': 'OK', 'enabled': True, 'element': mock_element},
            {'role': 'AXLink', 'title': 'Home', 'enabled': True, 'element': mock_element},
            {'role': 'AXMenuItem', 'title': 'File', 'enabled': True, 'element': mock_element},
            {'role': 'AXStaticText', 'title': 'Welcome', 'enabled': True, 'element': mock_element}  # Not clickable
        ]
        
        with patch.object(self.accessibility, 'get_active_application', return_value={'name': 'TestApp', 'pid': 1234}):
            with patch.object(self.accessibility, '_get_cached_elements', return_value=None):
                with patch.object(self.accessibility, '_get_target_application_element', return_value=mock_element):
                    with patch.object(self.accessibility, 'traverse_accessibility_tree', return_value=mock_elements):
                        with patch.object(self.accessibility, '_calculate_element_coordinates', return_value=[100, 100, 50, 30]):
                            
                            # Test broad search finds clickable elements
                            result = self.accessibility.find_element('', 'OK')
                            
                            assert result is not None
                            assert result['role'] == 'AXButton'
                            assert result['title'] == 'OK'
    
    def test_fallback_when_enhanced_fails(self):
        """Test that system falls back to original logic when enhanced detection fails."""
        with patch.object(self.accessibility, 'find_element_enhanced', side_effect=Exception("Enhanced failed")):
            with patch.object(self.accessibility, '_find_element_original_implementation') as mock_original:
                mock_original.return_value = {
                    'role': 'AXButton',
                    'title': 'Fallback Button',
                    'coordinates': [50, 50, 100, 40],
                    'center_point': [100, 70],
                    'enabled': True,
                    'app_name': 'TestApp'
                }
                
                result = self.accessibility.find_element('AXButton', 'Fallback Button')
                
                assert result is not None
                assert result['title'] == 'Fallback Button'
                mock_original.assert_called_once_with('AXButton', 'Fallback Button', None)
    
    def test_enhanced_role_matching_with_categories(self):
        """Test that enhanced role matching works with role categories."""
        mock_element = Mock()
        mock_button_info = {
            'role': 'AXButton',
            'title': 'Submit',
            'enabled': True,
            'element': mock_element
        }
        
        # Test that searching for 'button' category finds AXButton elements
        assert self.accessibility._element_matches_criteria(mock_button_info, 'button', 'Submit')
        
        # Test that searching for 'clickable' finds clickable elements
        assert self.accessibility._element_matches_criteria(mock_button_info, 'clickable', 'Submit')
    
    def test_performance_with_large_element_tree(self):
        """Test that enhanced detection performs well with large element trees."""
        # Create a large mock element tree
        mock_element = Mock()
        large_element_tree = []
        
        # Add many non-matching elements
        for i in range(100):
            large_element_tree.append({
                'role': 'AXStaticText',
                'title': f'Text {i}',
                'enabled': True,
                'element': mock_element
            })
        
        # Add the target element
        target_element = {
            'role': 'AXLink',
            'title': 'Target Link',
            'enabled': True,
            'element': mock_element
        }
        large_element_tree.append(target_element)
        
        with patch.object(self.accessibility, 'get_active_application', return_value={'name': 'TestApp', 'pid': 1234}):
            with patch.object(self.accessibility, '_get_cached_elements', return_value=None):
                with patch.object(self.accessibility, '_get_target_application_element', return_value=mock_element):
                    with patch.object(self.accessibility, 'traverse_accessibility_tree', return_value=large_element_tree):
                        with patch.object(self.accessibility, '_calculate_element_coordinates', return_value=[300, 400, 100, 25]):
                            
                            # Should still find the target element efficiently
                            result = self.accessibility.find_element('AXLink', 'Target Link')
                            
                            assert result is not None
                            assert result['role'] == 'AXLink'
                            assert result['title'] == 'Target Link'
    
    def test_cache_integration_with_enhanced_roles(self):
        """Test that caching works properly with enhanced role detection."""
        mock_element = Mock()
        mock_elements = [
            {'role': 'AXButton', 'title': 'Button1', 'enabled': True, 'element': mock_element},
            {'role': 'AXLink', 'title': 'Link1', 'enabled': True, 'element': mock_element},
            {'role': 'AXMenuItem', 'title': 'Menu1', 'enabled': True, 'element': mock_element}
        ]
        
        with patch.object(self.accessibility, 'get_active_application', return_value={'name': 'TestApp', 'pid': 1234}):
            # First call - cache miss
            with patch.object(self.accessibility, '_get_cached_elements', return_value=None):
                with patch.object(self.accessibility, '_get_target_application_element', return_value=mock_element):
                    with patch.object(self.accessibility, 'traverse_accessibility_tree', return_value=mock_elements):
                        with patch.object(self.accessibility, '_calculate_element_coordinates', return_value=[100, 100, 50, 30]):
                            
                            result1 = self.accessibility.find_element('AXLink', 'Link1')
                            assert result1 is not None
                            assert result1['role'] == 'AXLink'
            
            # Second call - should use cache
            with patch.object(self.accessibility, '_get_cached_elements', return_value=mock_elements):
                with patch.object(self.accessibility, '_search_cached_elements_enhanced', return_value=[mock_elements[1]]):
                    with patch.object(self.accessibility, '_calculate_element_coordinates', return_value=[100, 100, 50, 30]):
                        
                        result2 = self.accessibility.find_element('AXLink', 'Link1')
                        assert result2 is not None
                        assert result2['role'] == 'AXLink'


if __name__ == '__main__':
    pytest.main([__file__])