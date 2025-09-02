#!/usr/bin/env python3
"""
Unit tests for AccessibilityModule - Fast Path GUI Element Detection

Tests element detection accuracy, coordinate calculation, and validation logic
with mocked accessibility API responses for consistent testing.

Requirements: 5.1, 5.2
"""

import pytest
import unittest.mock as mock
from unittest.mock import Mock, MagicMock, patch, call
import logging
import time
from typing import Dict, Any, List, Optional

# Import the module under test
from modules.accessibility import (
    AccessibilityModule,
    AccessibilityElement,
    AccessibilityPermissionError,
    AccessibilityAPIUnavailableError,
    ElementNotFoundError,
    AccessibilityTimeoutError,
    AccessibilityTreeTraversalError,
    AccessibilityCoordinateError
)


class TestAccessibilityModule:
    """Test suite for AccessibilityModule functionality."""
    
    @pytest.fixture
    def mock_frameworks(self):
        """Mock all required frameworks for testing."""
        # Create mock workspace and app objects
        mock_workspace = Mock()
        mock_app = Mock()
        mock_app.localizedName.return_value = "TestApp"
        mock_app.bundleIdentifier.return_value = "com.test.app"
        mock_app.processIdentifier.return_value = 1234
        mock_workspace.frontmostApplication.return_value = mock_app
        mock_workspace.runningApplications.return_value = [mock_app]
        
        # Mock NSWorkspace class
        mock_nsworkspace_class = Mock()
        mock_nsworkspace_class.sharedWorkspace.return_value = mock_workspace
        
        # Mock AppKit module
        mock_appkit = Mock()
        mock_appkit.kAXFocusedApplicationAttribute = 'AXFocusedApplication'
        mock_appkit.kAXRoleAttribute = 'AXRole'
        mock_appkit.kAXTitleAttribute = 'AXTitle'
        mock_appkit.kAXDescriptionAttribute = 'AXDescription'
        mock_appkit.kAXEnabledAttribute = 'AXEnabled'
        mock_appkit.kAXChildrenAttribute = 'AXChildren'
        mock_appkit.kAXPositionAttribute = 'AXPosition'
        mock_appkit.kAXSizeAttribute = 'AXSize'
        mock_appkit.AXUIElementCreateSystemWide.return_value = Mock()
        mock_appkit.AXUIElementCreateApplication.return_value = Mock()
        mock_appkit.AXUIElementCopyAttributeValue.return_value = (0, Mock())
        
        # Apply patches
        patches = [
            patch('modules.accessibility.AppKit', mock_appkit),
            patch('modules.accessibility.Accessibility', Mock())
        ]
        
        # Patch NSWorkspace at the module level after import
        import modules.accessibility
        modules.accessibility.NSWorkspace = mock_nsworkspace_class
        
        for p in patches:
            p.start()
        
        yield mock_appkit
        
        for p in patches:
            p.stop()
    
    @pytest.fixture
    def mock_nsworkspace(self):
        """Mock NSWorkspace separately for better control."""
        # NSWorkspace is imported from AppKit, so we need to patch it there
        mock_workspace = Mock()
        mock_app = Mock()
        mock_app.localizedName.return_value = "TestApp"
        mock_app.bundleIdentifier.return_value = "com.test.app"
        mock_app.processIdentifier.return_value = 1234
        mock_workspace.frontmostApplication.return_value = mock_app
        mock_workspace.runningApplications.return_value = [mock_app]
        yield mock_workspace
    
    @pytest.fixture
    def mock_accessibility_available(self):
        """Mock accessibility framework availability."""
        with patch('modules.accessibility.ACCESSIBILITY_AVAILABLE', True):
            yield
    
    @pytest.fixture
    def accessibility_module(self, mock_frameworks, mock_accessibility_available):
        """Create AccessibilityModule instance with mocked dependencies."""
        return AccessibilityModule()
    
    @pytest.fixture
    def sample_element_info(self):
        """Sample element information for testing."""
        return {
            'element': Mock(),
            'role': 'AXButton',
            'title': 'Sign In',
            'enabled': True
        }
    
    @pytest.fixture
    def sample_coordinates(self):
        """Sample coordinates for testing."""
        return [100, 200, 150, 50]  # [x, y, width, height]


class TestAccessibilityModuleInitialization(TestAccessibilityModule):
    """Test AccessibilityModule initialization and setup."""
    
    def test_successful_initialization(self, mock_frameworks, mock_accessibility_available):
        """Test successful module initialization with proper permissions."""
        # Setup successful initialization
        mock_frameworks.AXUIElementCreateSystemWide.return_value = Mock()
        
        module = AccessibilityModule()
        
        assert module.accessibility_enabled is True
        assert module.degraded_mode is False
        assert module.workspace is not None
        assert module.error_count == 0
        assert module.recovery_attempts == 0
    
    def test_initialization_without_frameworks(self):
        """Test initialization when accessibility frameworks are not available."""
        with patch('modules.accessibility.ACCESSIBILITY_AVAILABLE', False):
            module = AccessibilityModule()
            
            assert module.accessibility_enabled is False
            assert module.degraded_mode is True
    
    def test_initialization_permission_denied(self, mock_frameworks, mock_accessibility_available):
        """Test initialization when accessibility permissions are denied."""
        # Mock permission denied scenario
        mock_frameworks.AXUIElementCreateSystemWide.return_value = None
        
        module = AccessibilityModule()
        
        assert module.accessibility_enabled is False
        assert module.degraded_mode is True
    
    def test_initialization_api_unavailable(self, mock_frameworks, mock_accessibility_available):
        """Test initialization when accessibility API is unavailable."""
        # Mock API unavailable scenario - workspace returns None
        with patch('modules.accessibility.NSWorkspace') as mock_nsworkspace_class:
            mock_nsworkspace_class.sharedWorkspace.return_value = None
            
            module = AccessibilityModule()
            
            assert module.accessibility_enabled is False
            assert module.degraded_mode is True


class TestElementDetection(TestAccessibilityModule):
    """Test element detection functionality."""
    
    def test_find_element_success(self, accessibility_module, mock_frameworks, sample_element_info):
        """Test successful element detection."""
        # Ensure module is in working state
        accessibility_module.accessibility_enabled = True
        accessibility_module.degraded_mode = False
        
        # Mock successful element traversal
        with patch.object(accessibility_module, '_get_target_application_element') as mock_get_app:
            with patch.object(accessibility_module, 'traverse_accessibility_tree') as mock_traverse:
                with patch.object(accessibility_module, 'filter_elements_by_criteria') as mock_filter:
                    with patch.object(accessibility_module, '_element_matches_criteria') as mock_matches:
                        with patch.object(accessibility_module, 'find_best_matching_element') as mock_best:
                            with patch.object(accessibility_module, '_calculate_element_coordinates') as mock_coords:
                                
                                # Setup mocks
                                mock_get_app.return_value = Mock()
                                mock_traverse.return_value = [sample_element_info]
                                mock_filter.return_value = [sample_element_info]
                                mock_matches.return_value = True
                                mock_best.return_value = sample_element_info
                                mock_coords.return_value = [100, 200, 150, 50]
                                
                                # Test element detection
                                result = accessibility_module.find_element('AXButton', 'Sign In')
                                
                                assert result is not None
                                assert result['role'] == 'AXButton'
                                assert result['title'] == 'Sign In'
                                assert result['coordinates'] == [100, 200, 150, 50]
                                assert result['center_point'] == [175, 225]  # center calculation
                                assert result['enabled'] is True
    
    def test_find_element_not_found(self, accessibility_module, mock_frameworks):
        """Test element detection when element is not found."""
        with patch.object(accessibility_module, '_get_target_application_element') as mock_get_app:
            with patch.object(accessibility_module, 'traverse_accessibility_tree') as mock_traverse:
                
                # Setup mocks for element not found
                mock_get_app.return_value = Mock()
                mock_traverse.return_value = []
                
                # Test element not found
                result = accessibility_module.find_element('AXButton', 'NonExistent')
                
                assert result is None
    
    def test_find_element_degraded_mode(self, accessibility_module):
        """Test element detection in degraded mode."""
        # Put module in degraded mode
        accessibility_module.degraded_mode = True
        accessibility_module.accessibility_enabled = False
        
        result = accessibility_module.find_element('AXButton', 'Sign In')
        
        assert result is None
    
    def test_find_element_with_app_name(self, accessibility_module, mock_frameworks, sample_element_info):
        """Test element detection with specific application name."""
        # Ensure module is in working state
        accessibility_module.accessibility_enabled = True
        accessibility_module.degraded_mode = False
        
        with patch.object(accessibility_module, '_get_target_application_element') as mock_get_app:
            with patch.object(accessibility_module, 'traverse_accessibility_tree') as mock_traverse:
                with patch.object(accessibility_module, 'filter_elements_by_criteria') as mock_filter:
                    with patch.object(accessibility_module, '_element_matches_criteria') as mock_matches:
                        with patch.object(accessibility_module, 'find_best_matching_element') as mock_best:
                            with patch.object(accessibility_module, '_calculate_element_coordinates') as mock_coords:
                                
                                # Setup mocks
                                mock_get_app.return_value = Mock()
                                mock_traverse.return_value = [sample_element_info]
                                mock_filter.return_value = [sample_element_info]
                                mock_matches.return_value = True
                                mock_best.return_value = sample_element_info
                                mock_coords.return_value = [100, 200, 150, 50]
                                
                                # Test with app name
                                result = accessibility_module.find_element('AXButton', 'Sign In', 'TestApp')
                                
                                assert result is not None
                                mock_get_app.assert_called_once_with('TestApp')
    
    def test_find_element_coordinate_calculation_failure(self, accessibility_module, mock_frameworks, sample_element_info):
        """Test element detection when coordinate calculation fails."""
        with patch.object(accessibility_module, '_get_target_application_element') as mock_get_app:
            with patch.object(accessibility_module, 'traverse_accessibility_tree') as mock_traverse:
                with patch.object(accessibility_module, 'filter_elements_by_criteria') as mock_filter:
                    with patch.object(accessibility_module, '_element_matches_criteria') as mock_matches:
                        with patch.object(accessibility_module, 'find_best_matching_element') as mock_best:
                            with patch.object(accessibility_module, '_calculate_element_coordinates') as mock_coords:
                                
                                # Setup mocks with coordinate failure
                                mock_get_app.return_value = Mock()
                                mock_traverse.return_value = [sample_element_info]
                                mock_filter.return_value = [sample_element_info]
                                mock_matches.return_value = True
                                mock_best.return_value = sample_element_info
                                mock_coords.return_value = None  # Coordinate calculation fails
                                
                                # Test coordinate failure
                                result = accessibility_module.find_element('AXButton', 'Sign In')
                                
                                assert result is None


class TestCoordinateCalculation(TestAccessibilityModule):
    """Test coordinate calculation and validation logic."""
    
    def test_calculate_element_coordinates_success(self, accessibility_module, mock_appkit):
        """Test successful coordinate calculation."""
        # Mock element with position and size
        mock_element = Mock()
        
        # Mock position result
        mock_position = Mock()
        mock_position.x = 100
        mock_position.y = 200
        
        # Mock size result
        mock_size = Mock()
        mock_size.width = 150
        mock_size.height = 50
        
        # Setup AppKit mock returns
        mock_appkit.AXUIElementCopyAttributeValue.side_effect = [
            (0, mock_position),  # Position call
            (0, mock_size)       # Size call
        ]
        
        coordinates = accessibility_module._calculate_element_coordinates(mock_element)
        
        assert coordinates == [100, 200, 150, 50]
        assert mock_appkit.AXUIElementCopyAttributeValue.call_count == 2
    
    def test_calculate_element_coordinates_position_failure(self, accessibility_module, mock_appkit):
        """Test coordinate calculation when position retrieval fails."""
        mock_element = Mock()
        
        # Mock position failure
        mock_appkit.AXUIElementCopyAttributeValue.return_value = (1, None)  # Error code 1
        
        coordinates = accessibility_module._calculate_element_coordinates(mock_element)
        
        assert coordinates is None
    
    def test_calculate_element_coordinates_size_failure(self, accessibility_module, mock_appkit):
        """Test coordinate calculation when size retrieval fails."""
        mock_element = Mock()
        
        # Mock position success, size failure
        mock_position = Mock()
        mock_position.x = 100
        mock_position.y = 200
        
        mock_appkit.AXUIElementCopyAttributeValue.side_effect = [
            (0, mock_position),  # Position success
            (1, None)            # Size failure
        ]
        
        coordinates = accessibility_module._calculate_element_coordinates(mock_element)
        
        assert coordinates is None
    
    def test_calculate_element_coordinates_invalid_values(self, accessibility_module, mock_appkit):
        """Test coordinate calculation with invalid coordinate values."""
        mock_element = Mock()
        
        # Mock negative coordinates
        mock_position = Mock()
        mock_position.x = -10
        mock_position.y = -20
        
        mock_size = Mock()
        mock_size.width = 0  # Invalid width
        mock_size.height = 50
        
        mock_appkit.AXUIElementCopyAttributeValue.side_effect = [
            (0, mock_position),
            (0, mock_size)
        ]
        
        coordinates = accessibility_module._calculate_element_coordinates(mock_element)
        
        assert coordinates is None


class TestTreeTraversal(TestAccessibilityModule):
    """Test accessibility tree traversal functionality."""
    
    def test_traverse_accessibility_tree_success(self, accessibility_module, mock_appkit):
        """Test successful accessibility tree traversal."""
        # Create mock elements
        root_element = Mock()
        child_element = Mock()
        
        # Mock element info extraction
        with patch.object(accessibility_module, '_extract_element_info') as mock_extract:
            with patch.object(accessibility_module, '_get_element_children') as mock_children:
                
                # Setup mocks
                mock_extract.side_effect = [
                    {'element': root_element, 'role': 'AXWindow', 'title': 'Test Window'},
                    {'element': child_element, 'role': 'AXButton', 'title': 'Test Button'}
                ]
                mock_children.return_value = [child_element]
                
                # Test traversal
                elements = accessibility_module.traverse_accessibility_tree(root_element, max_depth=2)
                
                assert len(elements) == 2
                assert elements[0]['role'] == 'AXWindow'
                assert elements[1]['role'] == 'AXButton'
    
    def test_traverse_accessibility_tree_max_depth(self, accessibility_module):
        """Test tree traversal respects max depth limit."""
        mock_element = Mock()
        
        # Test with max_depth = 0
        elements = accessibility_module.traverse_accessibility_tree(mock_element, max_depth=0)
        
        assert elements == []
    
    def test_traverse_accessibility_tree_no_element(self, accessibility_module):
        """Test tree traversal with None element."""
        elements = accessibility_module.traverse_accessibility_tree(None, max_depth=5)
        
        assert elements == []
    
    def test_traverse_accessibility_tree_error_handling(self, accessibility_module, mock_appkit):
        """Test tree traversal error handling."""
        mock_element = Mock()
        
        # Mock extraction that raises exception
        with patch.object(accessibility_module, '_extract_element_info') as mock_extract:
            mock_extract.side_effect = Exception("Test error")
            
            # Should not raise exception, just return empty list
            elements = accessibility_module.traverse_accessibility_tree(mock_element, max_depth=2)
            
            assert elements == []


class TestElementClassification(TestAccessibilityModule):
    """Test element classification and filtering functionality."""
    
    def test_classify_element_role_button(self, accessibility_module):
        """Test element role classification for buttons."""
        assert accessibility_module.classify_element_role('AXButton') == 'button'
        assert accessibility_module.classify_element_role('AXMenuButton') == 'button'
    
    def test_classify_element_role_menu(self, accessibility_module):
        """Test element role classification for menus."""
        assert accessibility_module.classify_element_role('AXMenu') == 'menu'
        assert accessibility_module.classify_element_role('AXMenuItem') == 'menu'
        assert accessibility_module.classify_element_role('AXMenuBar') == 'menu'
    
    def test_classify_element_role_text_field(self, accessibility_module):
        """Test element role classification for text fields."""
        assert accessibility_module.classify_element_role('AXTextField') == 'text_field'
        assert accessibility_module.classify_element_role('AXSecureTextField') == 'text_field'
        assert accessibility_module.classify_element_role('AXTextArea') == 'text_field'
    
    def test_classify_element_role_unknown(self, accessibility_module):
        """Test element role classification for unknown roles."""
        assert accessibility_module.classify_element_role('AXUnknownRole') == 'unknown'
        assert accessibility_module.classify_element_role('') == 'unknown'
    
    def test_is_element_actionable_enabled_button(self, accessibility_module):
        """Test actionable element detection for enabled buttons."""
        element_info = {
            'role': 'AXButton',
            'enabled': True,
            'element': Mock()
        }
        
        assert accessibility_module.is_element_actionable(element_info) is True
    
    def test_is_element_actionable_disabled_button(self, accessibility_module):
        """Test actionable element detection for disabled buttons."""
        element_info = {
            'role': 'AXButton',
            'enabled': False,
            'element': Mock()
        }
        
        assert accessibility_module.is_element_actionable(element_info) is False
    
    def test_is_element_actionable_non_actionable_role(self, accessibility_module):
        """Test actionable element detection for non-actionable roles."""
        element_info = {
            'role': 'AXStaticText',
            'enabled': True,
            'element': Mock()
        }
        
        assert accessibility_module.is_element_actionable(element_info) is False
    
    def test_is_element_actionable_text_field(self, accessibility_module):
        """Test actionable element detection for text fields."""
        element_info = {
            'role': 'AXTextField',
            'enabled': True,
            'element': Mock()
        }
        
        with patch.object(accessibility_module, '_is_text_field_editable') as mock_editable:
            mock_editable.return_value = True
            
            assert accessibility_module.is_element_actionable(element_info) is True
            mock_editable.assert_called_once_with(element_info['element'])


class TestFuzzyMatching(TestAccessibilityModule):
    """Test fuzzy matching functionality for element labels."""
    
    def test_fuzzy_match_exact_match(self, accessibility_module):
        """Test fuzzy matching with exact label match."""
        assert accessibility_module.fuzzy_match_label('Sign In', 'Sign In') is True
    
    def test_fuzzy_match_case_insensitive(self, accessibility_module):
        """Test fuzzy matching with case differences."""
        assert accessibility_module.fuzzy_match_label('SIGN IN', 'sign in') is True
        assert accessibility_module.fuzzy_match_label('Sign In', 'SIGN IN') is True
    
    def test_fuzzy_match_partial_match(self, accessibility_module):
        """Test fuzzy matching with partial matches."""
        # This depends on the actual implementation of fuzzy_match_label
        # Assuming it uses some similarity threshold
        assert accessibility_module.fuzzy_match_label('Sign In Button', 'Sign In') is True
        assert accessibility_module.fuzzy_match_label('Login', 'Sign In') is False
    
    def test_fuzzy_match_empty_strings(self, accessibility_module):
        """Test fuzzy matching with empty strings."""
        # Empty strings should return False according to implementation
        assert accessibility_module.fuzzy_match_label('', '') is False
        assert accessibility_module.fuzzy_match_label('Sign In', '') is False
        assert accessibility_module.fuzzy_match_label('', 'Sign In') is False


class TestErrorHandling(TestAccessibilityModule):
    """Test error handling and recovery mechanisms."""
    
    def test_handle_accessibility_error_permission_error(self, accessibility_module):
        """Test handling of accessibility permission errors."""
        error = AccessibilityPermissionError("Permission denied")
        
        accessibility_module._handle_accessibility_error(error, "test_operation")
        
        assert accessibility_module.error_count > 0
        assert accessibility_module.last_error_time is not None
        assert accessibility_module.degraded_mode is True
    
    def test_handle_accessibility_error_api_unavailable(self, accessibility_module):
        """Test handling of API unavailable errors."""
        error = AccessibilityAPIUnavailableError("API not available")
        
        accessibility_module._handle_accessibility_error(error, "test_operation")
        
        assert accessibility_module.error_count > 0
        assert accessibility_module.degraded_mode is True
    
    def test_handle_accessibility_error_generic_error(self, accessibility_module):
        """Test handling of generic errors."""
        error = Exception("Generic error")
        
        accessibility_module._handle_accessibility_error(error, "test_operation")
        
        assert accessibility_module.error_count > 0
        assert accessibility_module.last_error_time is not None
    
    def test_should_attempt_recovery_conditions(self, accessibility_module):
        """Test recovery attempt conditions."""
        # Not in degraded mode
        accessibility_module.degraded_mode = False
        assert accessibility_module._should_attempt_recovery() is False
        
        # In degraded mode but max attempts reached
        accessibility_module.degraded_mode = True
        accessibility_module.recovery_attempts = accessibility_module.max_recovery_attempts
        assert accessibility_module._should_attempt_recovery() is False
        
        # In degraded mode, recent error
        accessibility_module.degraded_mode = True
        accessibility_module.recovery_attempts = 0
        accessibility_module.last_error_time = time.time()
        assert accessibility_module._should_attempt_recovery() is False
        
        # In degraded mode, old error, attempts available
        accessibility_module.degraded_mode = True
        accessibility_module.recovery_attempts = 0
        accessibility_module.last_error_time = time.time() - accessibility_module.permission_check_interval - 1
        assert accessibility_module._should_attempt_recovery() is True
    
    def test_attempt_recovery_success(self, accessibility_module, mock_appkit):
        """Test successful recovery attempt."""
        accessibility_module.degraded_mode = True
        accessibility_module.accessibility_enabled = False
        
        with patch.object(accessibility_module, '_initialize_accessibility_api') as mock_init:
            mock_init.return_value = None  # Successful initialization
            
            result = accessibility_module._attempt_recovery()
            
            assert result is True
            assert accessibility_module.recovery_attempts == 1
            mock_init.assert_called_once()
    
    def test_attempt_recovery_failure(self, accessibility_module):
        """Test failed recovery attempt."""
        accessibility_module.degraded_mode = True
        accessibility_module.accessibility_enabled = False
        
        with patch.object(accessibility_module, '_initialize_accessibility_api') as mock_init:
            mock_init.side_effect = Exception("Recovery failed")
            
            result = accessibility_module._attempt_recovery()
            
            assert result is False
            assert accessibility_module.recovery_attempts == 1


class TestApplicationManagement(TestAccessibilityModule):
    """Test application management functionality."""
    
    def test_get_active_application_success(self, accessibility_module, mock_appkit):
        """Test successful active application retrieval."""
        # Ensure module is in working state
        accessibility_module.accessibility_enabled = True
        accessibility_module.degraded_mode = False
        
        result = accessibility_module.get_active_application()
        
        assert result is not None
        assert result['name'] == 'TestApp'
        assert result['bundle_id'] == 'com.test.app'
        assert result['pid'] == 1234
        assert 'accessible' in result
    
    def test_get_active_application_disabled(self, accessibility_module):
        """Test active application retrieval when accessibility is disabled."""
        accessibility_module.accessibility_enabled = False
        
        result = accessibility_module.get_active_application()
        
        assert result is None
    
    def test_get_active_application_no_frontmost(self, accessibility_module, mock_appkit):
        """Test active application retrieval when no frontmost app."""
        mock_appkit.NSWorkspace.sharedWorkspace.return_value.frontmostApplication.return_value = None
        
        result = accessibility_module.get_active_application()
        
        assert result is None


class TestStatusAndDiagnostics(TestAccessibilityModule):
    """Test status reporting and diagnostics functionality."""
    
    def test_is_accessibility_enabled(self, accessibility_module):
        """Test accessibility enabled status check."""
        accessibility_module.accessibility_enabled = True
        assert accessibility_module.is_accessibility_enabled() is True
        
        accessibility_module.accessibility_enabled = False
        assert accessibility_module.is_accessibility_enabled() is False
    
    def test_get_accessibility_status(self, accessibility_module):
        """Test comprehensive accessibility status retrieval."""
        status = accessibility_module.get_accessibility_status()
        
        assert 'frameworks_available' in status
        assert 'api_initialized' in status
        assert 'workspace_available' in status
        assert 'permissions_granted' in status
        assert 'degraded_mode' in status
        assert 'error_count' in status
        assert 'recovery_attempts' in status
        assert 'can_attempt_recovery' in status
    
    def test_get_error_diagnostics(self, accessibility_module):
        """Test error diagnostics retrieval."""
        diagnostics = accessibility_module.get_error_diagnostics()
        
        assert 'module_state' in diagnostics
        assert 'system_state' in diagnostics
        assert 'recovery_state' in diagnostics
        
        # Check module state details
        module_state = diagnostics['module_state']
        assert 'accessibility_enabled' in module_state
        assert 'degraded_mode' in module_state
        assert 'error_count' in module_state
        
        # Check system state details
        system_state = diagnostics['system_state']
        assert 'frameworks_available' in system_state
        assert 'workspace_initialized' in system_state
        
        # Check recovery state details
        recovery_state = diagnostics['recovery_state']
        assert 'can_attempt_recovery' in recovery_state
        assert 'next_retry_delay' in recovery_state


class TestCustomExceptions(TestAccessibilityModule):
    """Test custom exception classes."""
    
    def test_accessibility_permission_error(self):
        """Test AccessibilityPermissionError exception."""
        error = AccessibilityPermissionError("Permission denied")
        
        assert str(error) == "Permission denied"
        assert "System Preferences" in error.recovery_suggestion
    
    def test_accessibility_api_unavailable_error(self):
        """Test AccessibilityAPIUnavailableError exception."""
        error = AccessibilityAPIUnavailableError("API not available")
        
        assert str(error) == "API not available"
        assert "pip install" in error.recovery_suggestion
    
    def test_element_not_found_error(self):
        """Test ElementNotFoundError exception."""
        error = ElementNotFoundError("Element not found", "AXButton", "Sign In")
        
        assert str(error) == "Element not found"
        assert error.element_role == "AXButton"
        assert error.element_label == "Sign In"
    
    def test_accessibility_timeout_error(self):
        """Test AccessibilityTimeoutError exception."""
        error = AccessibilityTimeoutError("Operation timed out", "find_element")
        
        assert str(error) == "Operation timed out"
        assert error.operation == "find_element"
    
    def test_accessibility_tree_traversal_error(self):
        """Test AccessibilityTreeTraversalError exception."""
        error = AccessibilityTreeTraversalError("Traversal failed", 5)
        
        assert str(error) == "Traversal failed"
        assert error.depth == 5
    
    def test_accessibility_coordinate_error(self):
        """Test AccessibilityCoordinateError exception."""
        element_info = {'role': 'AXButton', 'title': 'Test'}
        error = AccessibilityCoordinateError("Coordinate calculation failed", element_info)
        
        assert str(error) == "Coordinate calculation failed"
        assert error.element_info == element_info


# Integration-style tests for more complex scenarios
class TestAccessibilityModuleIntegration(TestAccessibilityModule):
    """Integration-style tests for complex accessibility scenarios."""
    
    def test_find_element_full_workflow(self, accessibility_module, mock_appkit):
        """Test complete find_element workflow with realistic mocking."""
        # Ensure module is in working state
        accessibility_module.accessibility_enabled = True
        accessibility_module.degraded_mode = False
        
        # Setup complex mock scenario
        root_element = Mock()
        button_element = Mock()
        
        # Mock the full workflow
        with patch.object(accessibility_module, '_get_target_application_element') as mock_get_app:
            with patch.object(accessibility_module, '_extract_element_info') as mock_extract:
                with patch.object(accessibility_module, '_get_element_children') as mock_children:
                    with patch.object(accessibility_module, '_calculate_element_coordinates') as mock_coords:
                        
                        # Setup realistic mock responses
                        mock_get_app.return_value = root_element
                        mock_extract.side_effect = [
                            {'element': root_element, 'role': 'AXWindow', 'title': 'Test Window', 'enabled': True},
                            {'element': button_element, 'role': 'AXButton', 'title': 'Sign In', 'enabled': True}
                        ]
                        mock_children.return_value = [button_element]
                        mock_coords.return_value = [100, 200, 150, 50]
                        
                        # Test the full workflow
                        result = accessibility_module.find_element('AXButton', 'Sign In')
                        
                        # Verify result
                        assert result is not None
                        assert result['role'] == 'AXButton'
                        assert result['title'] == 'Sign In'
                        assert result['coordinates'] == [100, 200, 150, 50]
                        assert result['center_point'] == [175, 225]
                        assert result['enabled'] is True
                        
                        # Verify method calls
                        mock_get_app.assert_called_once_with(None)
                        assert mock_extract.call_count == 2
                        mock_children.assert_called_once_with(root_element)
                        mock_coords.assert_called_once_with(button_element)
    
    def test_error_recovery_workflow(self, accessibility_module, mock_appkit):
        """Test error recovery workflow."""
        # Start in degraded mode
        accessibility_module.degraded_mode = True
        accessibility_module.accessibility_enabled = False
        accessibility_module.last_error_time = time.time() - accessibility_module.permission_check_interval - 1
        
        # Mock successful recovery
        with patch.object(accessibility_module, '_initialize_accessibility_api') as mock_init:
            with patch.object(accessibility_module, '_get_target_application_element') as mock_get_app:
                
                mock_init.return_value = None  # Successful recovery
                mock_get_app.return_value = None  # Element not found after recovery
                
                # This should trigger recovery attempt
                result = accessibility_module.find_element('AXButton', 'Sign In')
                
                # Verify recovery was attempted
                mock_init.assert_called_once()
                assert accessibility_module.recovery_attempts == 1
                
                # Result should still be None (element not found)
                assert result is None


if __name__ == '__main__':
    pytest.main([__file__])