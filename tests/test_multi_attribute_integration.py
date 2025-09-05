"""
Integration tests for multi-attribute element finding in AccessibilityModule.

Tests the complete integration of multi-attribute text searching into the
element finding process, including priority logic and detailed logging.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the parent directory to the path to import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from modules.accessibility import AccessibilityModule


class TestMultiAttributeIntegration:
    """Test suite for multi-attribute element finding integration."""
    
    @pytest.fixture
    def accessibility_module(self):
        """Create AccessibilityModule instance for testing."""
        with patch('modules.accessibility.ACCESSIBILITY_AVAILABLE', True), \
             patch('modules.accessibility.ACCESSIBILITY_FUNCTIONS_AVAILABLE', True):
            module = AccessibilityModule()
            return module
    
    def test_element_matches_criteria_with_multi_attribute_checking(self, accessibility_module):
        """Test that _element_matches_criteria uses multi-attribute checking."""
        # Create mock element info with element reference
        mock_element = Mock()
        element_info = {
            'role': 'AXButton',
            'title': 'Sign In',
            'element': mock_element,
            'enabled': True
        }
        
        # Mock the multi-attribute checking method to return a successful match
        with patch.object(accessibility_module, '_check_element_text_match') as mock_check:
            mock_check.return_value = (True, 0.95, 'AXTitle')
            
            # Test that element matches criteria
            result = accessibility_module._element_matches_criteria(element_info, 'AXButton', 'Sign In')
            
            assert result is True
            # Verify that multi-attribute checking was called
            mock_check.assert_called_once_with(mock_element, 'Sign In')
    
    def test_element_matches_criteria_fallback_to_single_attribute(self, accessibility_module):
        """Test fallback to single-attribute matching when element is not available."""
        # Create mock element info without element reference
        element_info = {
            'role': 'AXButton',
            'title': 'Sign In',
            'enabled': True
            # No 'element' key - should trigger fallback
        }
        
        # Mock the fuzzy_match_label method
        with patch.object(accessibility_module, 'fuzzy_match_label') as mock_fuzzy:
            mock_fuzzy.return_value = True
            
            # Test that element matches criteria using fallback
            result = accessibility_module._element_matches_criteria(element_info, 'AXButton', 'Sign In')
            
            assert result is True
            # Verify that fuzzy matching was called as fallback
            mock_fuzzy.assert_called_once_with('Sign In', 'Sign In')
    
    def test_element_matches_criteria_no_match(self, accessibility_module):
        """Test when multi-attribute checking finds no match."""
        # Create mock element info with element reference
        mock_element = Mock()
        element_info = {
            'role': 'AXButton',
            'title': 'Different Text',
            'element': mock_element,
            'enabled': True
        }
        
        # Mock the multi-attribute checking method to return no match
        with patch.object(accessibility_module, '_check_element_text_match') as mock_check:
            mock_check.return_value = (False, 0.0, '')
            
            # Test that element does not match criteria
            result = accessibility_module._element_matches_criteria(element_info, 'AXButton', 'Sign In')
            
            assert result is False
            # Verify that multi-attribute checking was called
            mock_check.assert_called_once_with(mock_element, 'Sign In')
    
    def test_element_matches_criteria_role_filtering(self, accessibility_module):
        """Test that role filtering works before multi-attribute checking."""
        # Create mock element info with wrong role
        mock_element = Mock()
        element_info = {
            'role': 'AXTextField',  # Wrong role
            'title': 'Sign In',
            'element': mock_element,
            'enabled': True
        }
        
        # Mock the multi-attribute checking method (should not be called)
        with patch.object(accessibility_module, '_check_element_text_match') as mock_check:
            mock_check.return_value = (True, 0.95, 'AXTitle')
            
            # Test that element does not match due to role mismatch
            result = accessibility_module._element_matches_criteria(element_info, 'AXButton', 'Sign In')
            
            assert result is False
            # Verify that multi-attribute checking was NOT called due to role mismatch
            mock_check.assert_not_called()
    
    def test_element_matches_criteria_clickable_role_matching(self, accessibility_module):
        """Test that clickable role matching works with multi-attribute checking."""
        # Create mock element info with clickable role
        mock_element = Mock()
        element_info = {
            'role': 'AXLink',  # Clickable role
            'title': 'Gmail',
            'element': mock_element,
            'enabled': True
        }
        
        # Mock the multi-attribute checking method
        with patch.object(accessibility_module, '_check_element_text_match') as mock_check:
            mock_check.return_value = (True, 0.85, 'AXDescription')
            
            # Test with empty role (should match clickable elements)
            result = accessibility_module._element_matches_criteria(element_info, '', 'Gmail')
            
            assert result is True
            # Verify that multi-attribute checking was called
            mock_check.assert_called_once_with(mock_element, 'Gmail')
    
    def test_element_matches_criteria_detailed_logging(self, accessibility_module):
        """Test that detailed logging is added for attribute checking process."""
        # Create mock element info
        mock_element = Mock()
        element_info = {
            'role': 'AXButton',
            'title': 'Sign In Button',
            'element': mock_element,
            'enabled': True
        }
        
        # Mock the multi-attribute checking method
        with patch.object(accessibility_module, '_check_element_text_match') as mock_check:
            mock_check.return_value = (True, 0.92, 'AXTitle')
            
            # Mock the logger to capture log messages
            with patch.object(accessibility_module, 'logger') as mock_logger:
                # Test element matching
                result = accessibility_module._element_matches_criteria(element_info, 'AXButton', 'Sign In')
                
                assert result is True
                
                # Verify that detailed logging was called
                mock_logger.debug.assert_called()
                
                # Check that the log message contains relevant information
                log_calls = mock_logger.debug.call_args_list
                log_messages = [call[0][0] for call in log_calls]
                
                # Should have a log message about the successful match
                success_logs = [msg for msg in log_messages if 'Multi-attribute match found' in msg]
                assert len(success_logs) > 0
                
                # The log should contain the matched attribute, confidence score, and search terms
                success_log = success_logs[0]
                assert 'AXTitle' in success_log
                assert '0.92' in success_log
                assert 'Sign In' in success_log
    
    def test_element_matches_criteria_no_match_logging(self, accessibility_module):
        """Test logging when no multi-attribute match is found."""
        # Create mock element info
        mock_element = Mock()
        element_info = {
            'role': 'AXButton',
            'title': 'Different Text',
            'element': mock_element,
            'enabled': True
        }
        
        # Mock the multi-attribute checking method to return no match
        with patch.object(accessibility_module, '_check_element_text_match') as mock_check:
            mock_check.return_value = (False, 0.0, '')
            
            # Mock the logger to capture log messages
            with patch.object(accessibility_module, 'logger') as mock_logger:
                # Test element matching
                result = accessibility_module._element_matches_criteria(element_info, 'AXButton', 'Target Text')
                
                assert result is False
                
                # Verify that detailed logging was called
                mock_logger.debug.assert_called()
                
                # Check that the log message contains relevant information about no match
                log_calls = mock_logger.debug.call_args_list
                log_messages = [call[0][0] for call in log_calls]
                
                # Should have a log message about no match found
                no_match_logs = [msg for msg in log_messages if 'No multi-attribute match' in msg]
                assert len(no_match_logs) > 0
                
                # The log should contain the search term and element role
                no_match_log = no_match_logs[0]
                assert 'Target Text' in no_match_log
                assert 'AXButton' in no_match_log
    
    def test_element_matches_criteria_fallback_logging(self, accessibility_module):
        """Test logging when falling back to single-attribute matching."""
        # Create mock element info without element reference
        element_info = {
            'role': 'AXButton',
            'title': 'Sign In',
            'enabled': True
            # No 'element' key - should trigger fallback
        }
        
        # Mock the fuzzy_match_label method
        with patch.object(accessibility_module, 'fuzzy_match_label') as mock_fuzzy:
            mock_fuzzy.return_value = True
            
            # Mock the logger to capture log messages
            with patch.object(accessibility_module, 'logger') as mock_logger:
                # Test element matching with fallback
                result = accessibility_module._element_matches_criteria(element_info, 'AXButton', 'Sign In')
                
                assert result is True
                
                # Verify that fallback logging was called
                mock_logger.debug.assert_called()
                
                # Check that the log message mentions fallback
                log_calls = mock_logger.debug.call_args_list
                log_messages = [call[0][0] for call in log_calls]
                
                # Should have a log message about fallback
                fallback_logs = [msg for msg in log_messages if 'falling back to title-only matching' in msg]
                assert len(fallback_logs) > 0
    
    def test_attribute_priority_logic_first_match_wins(self, accessibility_module):
        """Test that first successful match is used (priority logic)."""
        # Create mock element info
        mock_element = Mock()
        element_info = {
            'role': 'AXButton',
            'title': 'Button Title',
            'element': mock_element,
            'enabled': True
        }
        
        # Mock the multi-attribute checking to simulate finding match in first attribute
        with patch.object(accessibility_module, '_check_element_text_match') as mock_check:
            # Simulate finding match in AXTitle (first attribute checked)
            mock_check.return_value = (True, 0.88, 'AXTitle')
            
            # Test element matching
            result = accessibility_module._element_matches_criteria(element_info, 'AXButton', 'Button')
            
            assert result is True
            
            # Verify that multi-attribute checking was called once
            mock_check.assert_called_once_with(mock_element, 'Button')
    
    def test_integration_with_enhanced_role_detection(self, accessibility_module):
        """Test integration of multi-attribute checking with enhanced role detection."""
        # Test that clickable roles work with multi-attribute checking
        mock_element = Mock()
        element_info = {
            'role': 'AXMenuItem',  # Clickable role from CLICKABLE_ROLES
            'title': 'File Menu',
            'element': mock_element,
            'enabled': True
        }
        
        # Mock the multi-attribute checking method
        with patch.object(accessibility_module, '_check_element_text_match') as mock_check:
            mock_check.return_value = (True, 0.95, 'AXTitle')
            
            # Test with broad clickable search
            result = accessibility_module._element_matches_criteria(element_info, 'clickable', 'File')
            
            assert result is True
            mock_check.assert_called_once_with(mock_element, 'File')


if __name__ == '__main__':
    pytest.main([__file__])