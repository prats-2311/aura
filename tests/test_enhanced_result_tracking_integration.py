"""
Integration tests for enhanced result tracking in AccessibilityModule.

Tests the integration of ElementMatchResult tracking into element finding
with timing measurements and comprehensive logging.
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from modules.accessibility import AccessibilityModule, ElementMatchResult


class TestEnhancedResultTrackingIntegration:
    """Integration tests for enhanced result tracking."""
    
    @pytest.fixture
    def accessibility_module(self):
        """Create AccessibilityModule instance for testing."""
        with patch('modules.accessibility.ACCESSIBILITY_AVAILABLE', True):
            with patch('modules.accessibility.NSWorkspace') as mock_workspace:
                mock_workspace.sharedWorkspace.return_value = Mock()
                module = AccessibilityModule()
                module.accessibility_enabled = True
                module.degraded_mode = False
                return module
    
    def test_find_element_enhanced_returns_element_match_result(self, accessibility_module):
        """Test that find_element_enhanced returns ElementMatchResult."""
        # Mock the enhanced role detection to be available
        accessibility_module.is_enhanced_role_detection_available = Mock(return_value=True)
        
        # Mock the tracked method to return a successful result
        mock_element = {
            'coordinates': [100, 200, 80, 30],
            'center_point': [140, 215],
            'role': 'AXButton',
            'title': 'Submit',
            'enabled': True,
            'app_name': 'Safari'
        }
        
        mock_details = {
            'roles_checked': ['AXButton'],
            'attributes_checked': ['AXTitle'],
            'fuzzy_matches': [{'text': 'Submit', 'score': 100.0, 'attribute': 'AXTitle'}],
            'confidence_score': 100.0,
            'matched_attribute': 'AXTitle'
        }
        
        accessibility_module._find_element_with_enhanced_roles_tracked = Mock(
            return_value=(mock_element, mock_details)
        )
        
        # Call the method
        result = accessibility_module.find_element_enhanced('AXButton', 'Submit', 'Safari')
        
        # Verify it returns ElementMatchResult
        assert isinstance(result, ElementMatchResult)
        assert result.found is True
        assert result.element == mock_element
        assert result.confidence_score == 100.0
        assert result.matched_attribute == 'AXTitle'
        assert result.roles_checked == ['AXButton']
        assert result.attributes_checked == ['AXTitle']
        assert len(result.fuzzy_matches) == 1
        assert result.fallback_triggered is False
        assert result.search_time_ms > 0
    
    def test_find_element_enhanced_tracks_timing(self, accessibility_module):
        """Test that find_element_enhanced tracks search timing."""
        accessibility_module.is_enhanced_role_detection_available = Mock(return_value=True)
        
        # Mock a slow operation
        def slow_tracked_method(*args, **kwargs):
            time.sleep(0.1)  # 100ms delay
            return None, {
                'roles_checked': ['AXButton'],
                'attributes_checked': ['AXTitle'],
                'fuzzy_matches': [],
                'confidence_score': 0.0,
                'matched_attribute': ''
            }
        
        accessibility_module._find_element_with_enhanced_roles_tracked = slow_tracked_method
        
        start_time = time.time()
        result = accessibility_module.find_element_enhanced('AXButton', 'NonExistent')
        end_time = time.time()
        
        # Verify timing is tracked
        assert isinstance(result, ElementMatchResult)
        assert result.found is False
        assert result.search_time_ms >= 100  # At least 100ms due to sleep
        assert result.search_time_ms <= (end_time - start_time) * 1000 + 10  # Allow small margin
    
    def test_find_element_enhanced_handles_fallback_to_original(self, accessibility_module):
        """Test fallback to original implementation when enhanced features unavailable."""
        # Mock enhanced features as unavailable
        accessibility_module.is_enhanced_role_detection_available = Mock(return_value=False)
        
        # Mock original fallback to return a result
        mock_element = {
            'coordinates': [50, 100, 60, 20],
            'center_point': [80, 110],
            'role': 'AXButton',
            'title': 'OK',
            'enabled': True,
            'app_name': 'TestApp'
        }
        
        accessibility_module._find_element_original_fallback = Mock(return_value=mock_element)
        
        result = accessibility_module.find_element_enhanced('AXButton', 'OK')
        
        # Verify fallback was triggered and result is properly wrapped
        assert isinstance(result, ElementMatchResult)
        assert result.found is True
        assert result.element == mock_element
        assert result.fallback_triggered is True
        assert result.confidence_score == 100.0  # Original exact match
        assert result.matched_attribute == 'AXTitle'
        assert result.roles_checked == ['AXButton']
        assert result.attributes_checked == ['AXTitle']
        assert result.search_time_ms > 0
    
    def test_find_element_enhanced_handles_button_fallback(self, accessibility_module):
        """Test fallback to button-only detection."""
        accessibility_module.is_enhanced_role_detection_available = Mock(return_value=True)
        
        # Mock enhanced roles to return no result
        accessibility_module._find_element_with_enhanced_roles_tracked = Mock(
            return_value=(None, {
                'roles_checked': ['AXButton', 'AXLink'],
                'attributes_checked': ['AXTitle', 'AXDescription'],
                'fuzzy_matches': [],
                'confidence_score': 0.0,
                'matched_attribute': ''
            })
        )
        
        # Mock button fallback to succeed
        mock_element = {
            'coordinates': [200, 300, 100, 40],
            'center_point': [250, 320],
            'role': 'AXButton',
            'title': 'Click Me',
            'enabled': True,
            'app_name': 'TestApp'
        }
        
        accessibility_module._find_element_button_only_fallback = Mock(return_value=mock_element)
        
        result = accessibility_module.find_element_enhanced('', 'Click Me')  # Empty role triggers fallback
        
        # Verify button fallback was used
        assert isinstance(result, ElementMatchResult)
        assert result.found is True
        assert result.element == mock_element
        assert result.fallback_triggered is True
        assert result.confidence_score == 100.0
        assert result.matched_attribute == 'AXTitle'
        assert result.roles_checked == ['AXButton']
        assert result.attributes_checked == ['AXTitle']
    
    def test_find_element_enhanced_handles_exceptions(self, accessibility_module):
        """Test exception handling in find_element_enhanced."""
        accessibility_module.is_enhanced_role_detection_available = Mock(return_value=True)
        
        # Mock enhanced roles to raise an exception
        accessibility_module._find_element_with_enhanced_roles_tracked = Mock(
            side_effect=Exception("Test exception")
        )
        
        # Mock final fallback to return a result
        mock_element = {
            'coordinates': [10, 20, 30, 40],
            'center_point': [25, 40],
            'role': 'AXButton',
            'title': 'Fallback',
            'enabled': True,
            'app_name': 'TestApp'
        }
        
        accessibility_module._find_element_original_fallback = Mock(return_value=mock_element)
        
        result = accessibility_module.find_element_enhanced('AXButton', 'Test')
        
        # Verify exception was handled and fallback was used
        assert isinstance(result, ElementMatchResult)
        assert result.found is True
        assert result.element == mock_element
        assert result.fallback_triggered is True
        assert result.search_time_ms > 0
    
    def test_find_element_enhanced_no_element_found(self, accessibility_module):
        """Test when no element is found anywhere."""
        accessibility_module.is_enhanced_role_detection_available = Mock(return_value=True)
        
        # Mock all methods to return None/no results
        accessibility_module._find_element_with_enhanced_roles_tracked = Mock(
            return_value=(None, {
                'roles_checked': ['AXButton', 'AXLink'],
                'attributes_checked': ['AXTitle', 'AXDescription'],
                'fuzzy_matches': [],
                'confidence_score': 0.0,
                'matched_attribute': ''
            })
        )
        
        accessibility_module._find_element_button_only_fallback = Mock(return_value=None)
        
        result = accessibility_module.find_element_enhanced('AXButton', 'NonExistent')
        
        # Verify no element found result
        assert isinstance(result, ElementMatchResult)
        assert result.found is False
        assert result.element is None
        assert result.confidence_score == 0.0
        assert result.matched_attribute == ''
        assert result.roles_checked == ['AXButton', 'AXLink']
        assert result.attributes_checked == ['AXTitle', 'AXDescription']
        assert result.fuzzy_matches == []
        assert result.search_time_ms > 0
    
    def test_find_element_backward_compatibility(self, accessibility_module):
        """Test that find_element maintains backward compatibility."""
        accessibility_module.is_enhanced_role_detection_available = Mock(return_value=True)
        
        # Mock enhanced method to return a successful result
        mock_element = {
            'coordinates': [100, 200, 80, 30],
            'center_point': [140, 215],
            'role': 'AXButton',
            'title': 'Submit',
            'enabled': True,
            'app_name': 'Safari'
        }
        
        mock_details = {
            'roles_checked': ['AXButton'],
            'attributes_checked': ['AXTitle'],
            'fuzzy_matches': [],
            'confidence_score': 100.0,
            'matched_attribute': 'AXTitle'
        }
        
        accessibility_module._find_element_with_enhanced_roles_tracked = Mock(
            return_value=(mock_element, mock_details)
        )
        
        # Call the backward-compatible method
        result = accessibility_module.find_element('AXButton', 'Submit', 'Safari')
        
        # Verify it returns the element dict (not ElementMatchResult)
        assert result == mock_element
        assert isinstance(result, dict)
        assert not isinstance(result, ElementMatchResult)
    
    def test_find_element_logs_detailed_results(self, accessibility_module):
        """Test that find_element logs detailed results."""
        accessibility_module.is_enhanced_role_detection_available = Mock(return_value=True)
        
        mock_element = {
            'coordinates': [100, 200, 80, 30],
            'center_point': [140, 215],
            'role': 'AXButton',
            'title': 'Submit',
            'enabled': True,
            'app_name': 'Safari'
        }
        
        mock_details = {
            'roles_checked': ['AXButton', 'AXLink'],
            'attributes_checked': ['AXTitle', 'AXDescription'],
            'fuzzy_matches': [{'text': 'Submit', 'score': 95.0}],
            'confidence_score': 95.0,
            'matched_attribute': 'AXTitle'
        }
        
        accessibility_module._find_element_with_enhanced_roles_tracked = Mock(
            return_value=(mock_element, mock_details)
        )
        
        # Mock logger to capture log messages
        with patch.object(accessibility_module.logger, 'debug') as mock_debug:
            result = accessibility_module.find_element('AXButton', 'Submit')
            
            # Verify detailed logging occurred
            assert mock_debug.called
            log_calls = [call.args[0] for call in mock_debug.call_args_list]
            
            # Check that confidence, attribute, timing, and roles are logged
            found_detailed_log = False
            for log_msg in log_calls:
                if 'Confidence:' in log_msg and 'Attribute:' in log_msg and 'Time:' in log_msg:
                    found_detailed_log = True
                    assert '95.0%' in log_msg
                    assert 'AXTitle' in log_msg
                    break
            
            assert found_detailed_log, f"Expected detailed log not found in: {log_calls}"
    
    def test_tracked_method_populates_basic_info(self, accessibility_module):
        """Test that _find_element_with_enhanced_roles_tracked populates basic tracking info."""
        # Mock the original method to return a result
        mock_element = {
            'role': 'AXButton',
            'title': 'Test',
            'coordinates': [0, 0, 100, 50]
        }
        
        accessibility_module._find_element_with_enhanced_roles = Mock(return_value=mock_element)
        
        result, details = accessibility_module._find_element_with_enhanced_roles_tracked('AXButton', 'Test')
        
        # Verify result and details
        assert result == mock_element
        assert details['roles_checked'] == ['AXButton']
        assert details['attributes_checked'] == ['AXTitle', 'AXDescription', 'AXValue']
        assert details['confidence_score'] == 100.0
        assert details['matched_attribute'] == 'AXTitle'
        assert details['fuzzy_matches'] == []
    
    def test_tracked_method_handles_empty_role(self, accessibility_module):
        """Test tracked method with empty role (broader search)."""
        accessibility_module._find_element_with_enhanced_roles = Mock(return_value=None)
        
        result, details = accessibility_module._find_element_with_enhanced_roles_tracked('', 'Test')
        
        # Verify broader role search is tracked
        assert result is None
        assert details['roles_checked'] == ['AXButton', 'AXLink', 'AXMenuItem', 'AXCheckBox', 'AXRadioButton']
        assert details['attributes_checked'] == ['AXTitle', 'AXDescription', 'AXValue']
        assert details['confidence_score'] == 0.0
        assert details['matched_attribute'] == ''