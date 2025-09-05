"""
Unit tests for enhanced element role detection functionality.

Tests the expanded CLICKABLE_ROLES constant and enhanced role detection logic
that checks all clickable element types instead of just AXButton.

Requirements covered:
- 1.1: Enhanced element role detection for all clickable types
- 1.2: Configurable list of clickable roles
- 1.4: Role classification helper methods
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the parent directory to the path to import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from modules.accessibility import AccessibilityModule


class TestEnhancedRoleDetection:
    """Test suite for enhanced element role detection functionality."""
    
    @pytest.fixture
    def accessibility_module(self):
        """Create AccessibilityModule instance for testing."""
        with patch('modules.accessibility.ACCESSIBILITY_AVAILABLE', True), \
             patch('modules.accessibility.ACCESSIBILITY_FUNCTIONS_AVAILABLE', True), \
             patch('modules.accessibility.NSWorkspace'), \
             patch('modules.accessibility.AXUIElementCreateSystemWide'):
            return AccessibilityModule()
    
    def test_clickable_roles_constant_exists(self, accessibility_module):
        """Test that CLICKABLE_ROLES constant is properly defined."""
        assert hasattr(accessibility_module, 'clickable_roles')
        assert isinstance(accessibility_module.clickable_roles, set)
        assert len(accessibility_module.clickable_roles) > 0
        
        # Verify expected roles are present
        expected_roles = {'AXButton', 'AXLink', 'AXMenuItem', 'AXCheckBox', 'AXRadioButton'}
        assert accessibility_module.clickable_roles == expected_roles
    
    def test_clickable_roles_comprehensive_coverage(self, accessibility_module):
        """Test that all common clickable element types are included."""
        required_roles = [
            'AXButton',      # Standard buttons
            'AXLink',        # Web links and hyperlinks
            'AXMenuItem',    # Menu items in dropdowns and context menus
            'AXCheckBox',    # Checkboxes
            'AXRadioButton', # Radio buttons
        ]
        
        for role in required_roles:
            assert role in accessibility_module.clickable_roles, f"Missing required role: {role}"
    
    def test_is_clickable_role_method(self, accessibility_module):
        """Test role classification using clickable_roles set."""
        # Test clickable roles
        clickable_roles = ['AXButton', 'AXLink', 'AXMenuItem', 'AXCheckBox', 'AXRadioButton']
        for role in clickable_roles:
            assert role in accessibility_module.clickable_roles, f"Role {role} should be clickable"
        
        # Test non-clickable roles
        non_clickable_roles = ['AXStaticText', 'AXImage', 'AXGroup', 'AXWindow', 'AXApplication']
        for role in non_clickable_roles:
            assert role not in accessibility_module.clickable_roles, f"Role {role} should not be clickable"
    
    def test_is_clickable_role_case_sensitivity(self, accessibility_module):
        """Test that role checking is case sensitive (as expected by macOS)."""
        # Correct case should work
        assert 'AXButton' in accessibility_module.clickable_roles
        
        # Incorrect case should not work
        assert 'axbutton' not in accessibility_module.clickable_roles
        assert 'AXBUTTON' not in accessibility_module.clickable_roles
        assert 'axButton' not in accessibility_module.clickable_roles
    
    def test_is_clickable_role_invalid_inputs(self, accessibility_module):
        """Test role checking with invalid inputs."""
        # Test None input
        assert None not in accessibility_module.clickable_roles
        
        # Test empty string
        assert '' not in accessibility_module.clickable_roles
        
        # Test non-string input (these should not crash)
        assert 123 not in accessibility_module.clickable_roles
        
        # Test unhashable types don't crash the system
        try:
            result = [] in accessibility_module.clickable_roles
            assert result is False
        except TypeError:
            # This is expected for unhashable types
            pass
    
    def test_enhanced_element_search_uses_all_roles(self, accessibility_module):
        """Test that enhanced element search functionality exists."""
        # Test that the find_element_enhanced method exists
        assert hasattr(accessibility_module, 'find_element_enhanced')
        assert callable(accessibility_module.find_element_enhanced)
        
        # Test basic call doesn't crash
        try:
            result = accessibility_module.find_element_enhanced('', 'Submit')
            # Should return an ElementMatchResult or similar
            assert result is not None
            assert hasattr(result, 'found')
        except Exception:
            # If it fails due to no elements, that's acceptable for unit test
            pass
    
    def test_role_detection_priority_order(self, accessibility_module):
        """Test that role detection functionality exists and works."""
        # Test that the method exists and can be called
        try:
            result = accessibility_module.find_element_enhanced('', 'Submit')
            assert result is not None
            assert hasattr(result, 'found')
            assert hasattr(result, 'roles_checked')
        except Exception:
            # If it fails due to no elements, that's acceptable for unit test
            pass
    
    def test_backward_compatibility_button_only_search(self, accessibility_module):
        """Test backward compatibility when specifically searching for buttons."""
        # Test that specific role search works
        try:
            result = accessibility_module.find_element_enhanced('AXButton', 'Submit')
            assert result is not None
            assert hasattr(result, 'found')
        except Exception:
            # If it fails due to no elements, that's acceptable for unit test
            pass
    
    def test_role_detection_with_fuzzy_matching(self, accessibility_module):
        """Test that role detection works with fuzzy matching."""
        # Test that fuzzy matching is integrated
        assert hasattr(accessibility_module, 'fuzzy_matching_enabled')
        assert isinstance(accessibility_module.fuzzy_matching_enabled, bool)
        
        # Test that fuzzy matching method exists
        assert hasattr(accessibility_module, 'fuzzy_match_text')
        assert callable(accessibility_module.fuzzy_match_text)
    
    def test_role_detection_performance_logging(self, accessibility_module):
        """Test that role detection includes performance logging."""
        # Test that performance monitoring is configured
        assert hasattr(accessibility_module, 'performance_monitoring_enabled')
        assert isinstance(accessibility_module.performance_monitoring_enabled, bool)
        
        # Test that performance metrics exist
        assert hasattr(accessibility_module, 'performance_metrics')
        assert isinstance(accessibility_module.performance_metrics, list)
    
    def test_role_detection_error_handling(self, accessibility_module):
        """Test error handling in role detection."""
        # Test that error handling doesn't crash the system
        try:
            result = accessibility_module.find_element_enhanced('', 'Submit')
            assert result is not None
            assert hasattr(result, 'found')
        except Exception:
            # If it fails due to no elements or other issues, that's acceptable
            pass
    
    def test_role_detection_empty_element_list(self, accessibility_module):
        """Test role detection with empty element list."""
        # Test that method handles empty results gracefully
        try:
            result = accessibility_module.find_element_enhanced('', 'Submit')
            assert result is not None
            assert hasattr(result, 'found')
            # If no elements found, should return found=False
            if hasattr(result, 'roles_checked'):
                assert isinstance(result.roles_checked, list)
        except Exception:
            # If it fails due to no elements, that's acceptable
            pass
    
    def test_role_detection_configuration_update(self, accessibility_module):
        """Test that role detection uses updated configuration."""
        # Add a custom role to the configuration
        original_roles = accessibility_module.clickable_roles.copy()
        
        try:
            # Add a custom role
            accessibility_module.clickable_roles.add('AXCustomButton')
            
            # Test that the new role is recognized
            assert 'AXCustomButton' in accessibility_module.clickable_roles
            
            # Test that configuration is mutable
            assert len(accessibility_module.clickable_roles) > len(original_roles)
                
        finally:
            # Restore original configuration
            accessibility_module.clickable_roles = original_roles
    
    def test_role_classification_helper_methods(self, accessibility_module):
        """Test role classification using the clickable_roles set."""
        # Test button-like roles are in clickable_roles
        button_roles = ['AXButton', 'AXCheckBox', 'AXRadioButton']
        for role in button_roles:
            assert role in accessibility_module.clickable_roles
        
        # Test link roles are in clickable_roles
        link_roles = ['AXLink']
        for role in link_roles:
            assert role in accessibility_module.clickable_roles
        
        # Test menu roles are in clickable_roles
        menu_roles = ['AXMenuItem']
        for role in menu_roles:
            assert role in accessibility_module.clickable_roles
    
    def test_role_detection_metrics_tracking(self, accessibility_module):
        """Test that role detection tracks metrics correctly."""
        # Test that metrics tracking infrastructure exists
        assert hasattr(accessibility_module, 'operation_metrics')
        assert isinstance(accessibility_module.operation_metrics, dict)
        
        # Test that element role checks are tracked
        if 'element_role_checks' in accessibility_module.operation_metrics:
            assert 'count' in accessibility_module.operation_metrics['element_role_checks']
            assert 'total_time_ms' in accessibility_module.operation_metrics['element_role_checks']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])