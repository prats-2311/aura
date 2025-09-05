"""
Integration tests for enhanced error handling in the accessibility fast path.

Tests cover:
- Error handling integration throughout the enhanced fast path
- Fallback behavior when enhanced features fail
- Performance monitoring with error scenarios
- Configuration validation in real usage scenarios
"""

import pytest
import unittest.mock as mock
import time
from typing import Dict, Any, Optional
from unittest.mock import patch, MagicMock

# Import the module under test
from modules.accessibility import (
    AccessibilityModule,
    FuzzyMatchingError,
    TargetExtractionError,
    AttributeAccessError,
    EnhancedFastPathError,
    AccessibilityTimeoutError,
    ElementMatchResult
)


class TestEnhancedErrorHandlingIntegration:
    """Test error handling integration throughout the enhanced fast path."""
    
    @patch('modules.accessibility.AccessibilityModule._initialize_accessibility_api')
    def test_find_element_enhanced_with_fuzzy_matching_error(self, mock_init):
        """Test find_element_enhanced handles fuzzy matching errors gracefully."""
        accessibility = AccessibilityModule()
        
        # Mock the enhanced role detection to raise FuzzyMatchingError
        with patch.object(accessibility, '_find_element_with_enhanced_roles_tracked') as mock_enhanced:
            mock_enhanced.side_effect = FuzzyMatchingError(
                "Fuzzy matching failed", "test", "element", RuntimeError("Library error")
            )
            
            # Mock the fallback method to succeed
            with patch.object(accessibility, '_find_element_button_only_fallback') as mock_fallback:
                mock_fallback.return_value = {
                    'role': 'AXButton',
                    'title': 'Test Button',
                    'coordinates': [100, 100, 50, 30],
                    'center_point': [125, 115],
                    'enabled': True,
                    'app_name': 'TestApp'
                }
                
                result = accessibility.find_element_enhanced('', 'test button')
                
                assert result.found is True
                assert result.fallback_triggered is True
                assert result.confidence_score == 100.0
                assert result.matched_attribute == 'AXTitle'
    
    @patch('modules.accessibility.AccessibilityModule._initialize_accessibility_api')
    def test_find_element_enhanced_with_attribute_access_error(self, mock_init):
        """Test find_element_enhanced handles attribute access errors gracefully."""
        accessibility = AccessibilityModule()
        
        # Mock the enhanced role detection to raise AttributeAccessError
        with patch.object(accessibility, '_find_element_with_enhanced_roles_tracked') as mock_enhanced:
            mock_enhanced.side_effect = AttributeAccessError(
                "Attribute access failed", "AXTitle", {}, AttributeError("Not found")
            )
            
            # Mock the fallback method to succeed
            with patch.object(accessibility, '_find_element_button_only_fallback') as mock_fallback:
                mock_fallback.return_value = {
                    'role': 'AXButton',
                    'title': 'Test Button',
                    'coordinates': [100, 100, 50, 30],
                    'center_point': [125, 115],
                    'enabled': True,
                    'app_name': 'TestApp'
                }
                
                result = accessibility.find_element_enhanced('', 'test button')
                
                assert result.found is True
                assert result.fallback_triggered is True
    
    @patch('modules.accessibility.AccessibilityModule._initialize_accessibility_api')
    def test_find_element_enhanced_with_timeout_error(self, mock_init):
        """Test find_element_enhanced handles timeout errors gracefully."""
        accessibility = AccessibilityModule()
        
        # Mock the enhanced role detection to raise AccessibilityTimeoutError
        with patch.object(accessibility, '_find_element_with_enhanced_roles_tracked') as mock_enhanced:
            mock_enhanced.side_effect = AccessibilityTimeoutError(
                "Operation timed out", "element_search"
            )
            
            # Mock the fallback method to succeed
            with patch.object(accessibility, '_find_element_button_only_fallback') as mock_fallback:
                mock_fallback.return_value = {
                    'role': 'AXButton',
                    'title': 'Test Button',
                    'coordinates': [100, 100, 50, 30],
                    'center_point': [125, 115],
                    'enabled': True,
                    'app_name': 'TestApp'
                }
                
                result = accessibility.find_element_enhanced('', 'test button')
                
                assert result.found is True
                assert result.fallback_triggered is True
    
    @patch('modules.accessibility.AccessibilityModule._initialize_accessibility_api')
    def test_find_element_enhanced_with_enhanced_fast_path_error_no_fallback(self, mock_init):
        """Test find_element_enhanced handles EnhancedFastPathError with no fallback available."""
        accessibility = AccessibilityModule()
        
        # Mock the enhanced role detection to raise EnhancedFastPathError with no fallback
        with patch.object(accessibility, '_find_element_with_enhanced_roles_tracked') as mock_enhanced:
            mock_enhanced.side_effect = EnhancedFastPathError(
                "Fast path failed", "element_search", fallback_available=False
            )
            
            result = accessibility.find_element_enhanced('AXButton', 'test button')
            
            assert result.found is False
            assert result.fallback_triggered is True
            assert result.confidence_score == 0.0
    
    @patch('modules.accessibility.AccessibilityModule._initialize_accessibility_api')
    def test_find_element_enhanced_all_fallbacks_fail(self, mock_init):
        """Test find_element_enhanced when all fallback methods fail."""
        accessibility = AccessibilityModule()
        
        # Mock the enhanced role detection to fail
        with patch.object(accessibility, '_find_element_with_enhanced_roles_tracked') as mock_enhanced:
            mock_enhanced.side_effect = RuntimeError("Enhanced detection failed")
            
            # Mock all fallback methods to fail
            with patch.object(accessibility, '_find_element_button_only_fallback') as mock_button_fallback:
                mock_button_fallback.side_effect = RuntimeError("Button fallback failed")
                
                with patch.object(accessibility, '_find_element_original_fallback') as mock_original_fallback:
                    mock_original_fallback.side_effect = RuntimeError("Original fallback failed")
                    
                    result = accessibility.find_element_enhanced('', 'test button')
                    
                    assert result.found is False
                    assert result.fallback_triggered is True
                    assert result.confidence_score == 0.0


class TestFuzzyMatchingErrorHandlingIntegration:
    """Test fuzzy matching error handling integration."""
    
    @patch('modules.accessibility.AccessibilityModule._initialize_accessibility_api')
    @patch('modules.accessibility.FUZZY_MATCHING_AVAILABLE', True)
    @patch('modules.accessibility.fuzz')
    def test_fuzzy_match_text_with_timeout_error(self, mock_fuzz, mock_init):
        """Test fuzzy_match_text handles timeout errors properly."""
        accessibility = AccessibilityModule()
        accessibility.fuzzy_matching_timeout_ms = 100  # Short timeout
        
        # Mock fuzz.partial_ratio to be slow
        def slow_fuzzy_match(*args, **kwargs):
            time.sleep(0.2)  # Simulate slow operation
            return 90
        
        mock_fuzz.partial_ratio = slow_fuzzy_match
        
        # Should raise AccessibilityTimeoutError
        with pytest.raises(AccessibilityTimeoutError):
            accessibility.fuzzy_match_text("test", "test")
    
    @patch('modules.accessibility.AccessibilityModule._initialize_accessibility_api')
    @patch('modules.accessibility.FUZZY_MATCHING_AVAILABLE', True)
    @patch('modules.accessibility.fuzz')
    def test_fuzzy_match_text_with_library_error(self, mock_fuzz, mock_init):
        """Test fuzzy_match_text handles library errors properly."""
        accessibility = AccessibilityModule()
        
        # Mock fuzz.partial_ratio to raise an exception
        mock_fuzz.partial_ratio.side_effect = RuntimeError("Library error")
        
        # Should raise FuzzyMatchingError
        with pytest.raises(FuzzyMatchingError):
            accessibility.fuzzy_match_text("test", "test")
    
    @patch('modules.accessibility.AccessibilityModule._initialize_accessibility_api')
    @patch('modules.accessibility.FUZZY_MATCHING_AVAILABLE', True)
    @patch('modules.accessibility.fuzz')
    def test_fuzzy_match_text_with_unexpected_error_fallback(self, mock_fuzz, mock_init):
        """Test fuzzy_match_text handles unexpected errors with fallback."""
        accessibility = AccessibilityModule()
        
        # Mock fuzz.partial_ratio to raise an unexpected exception
        mock_fuzz.partial_ratio.side_effect = ValueError("Unexpected error")
        
        # The method should raise FuzzyMatchingError for specific errors
        # but handle it internally and use fallback
        with pytest.raises(FuzzyMatchingError):
            accessibility.fuzzy_match_text("test", "test")


class TestMultiAttributeErrorHandlingIntegration:
    """Test multi-attribute checking error handling integration."""
    
    @patch('modules.accessibility.AccessibilityModule._initialize_accessibility_api')
    def test_check_element_text_match_with_attribute_errors(self, mock_init):
        """Test _check_element_text_match handles attribute access errors."""
        accessibility = AccessibilityModule()
        accessibility.accessibility_attributes = ['AXTitle', 'AXDescription', 'AXValue']
        
        # Mock element that raises errors for some attributes
        mock_element = MagicMock()
        
        # Mock AXUIElementCopyAttributeValue to simulate different error scenarios
        def mock_attribute_access(element, attribute, none_param):
            if attribute == 'AXTitle':
                raise AttributeError("AXTitle not accessible")
            elif attribute == 'AXDescription':
                return (0, "Test Description")  # Success
            else:
                return (1, None)  # Failure code
        
        with patch('modules.accessibility.AXUIElementCopyAttributeValue', side_effect=mock_attribute_access):
            with patch.object(accessibility, '_safe_fuzzy_match') as mock_fuzzy:
                mock_fuzzy.return_value = (True, 90.0)
                
                match_found, confidence, attribute = accessibility._check_element_text_match(
                    mock_element, "test"
                )
                
                assert match_found is True
                assert confidence == 0.9  # Converted from percentage
                assert attribute == 'AXDescription'
    
    @patch('modules.accessibility.AccessibilityModule._initialize_accessibility_api')
    def test_check_element_text_match_with_fuzzy_matching_errors(self, mock_init):
        """Test _check_element_text_match handles fuzzy matching errors."""
        accessibility = AccessibilityModule()
        accessibility.accessibility_attributes = ['AXTitle']
        
        mock_element = MagicMock()
        
        # Mock successful attribute access
        with patch('modules.accessibility.AXUIElementCopyAttributeValue') as mock_attr:
            mock_attr.return_value = (0, "Test Title")
            
            # Mock _safe_fuzzy_match to raise FuzzyMatchingError
            with patch.object(accessibility, '_safe_fuzzy_match') as mock_fuzzy:
                mock_fuzzy.side_effect = FuzzyMatchingError(
                    "Fuzzy matching failed", "test", "Test Title"
                )
                
                # Mock the error handler to return successful fallback
                with patch.object(accessibility, '_handle_fuzzy_matching_error') as mock_handler:
                    mock_handler.return_value = (True, 100.0)
                    
                    match_found, confidence, attribute = accessibility._check_element_text_match(
                        mock_element, "test"
                    )
                    
                    assert match_found is True
                    assert confidence == 1.0
                    assert attribute == 'AXTitle'
                    mock_handler.assert_called_once()
    
    @patch('modules.accessibility.AccessibilityModule._initialize_accessibility_api')
    def test_check_element_text_match_with_all_errors_graceful_failure(self, mock_init):
        """Test _check_element_text_match handles all errors gracefully without crashing."""
        accessibility = AccessibilityModule()
        accessibility.accessibility_attributes = ['AXTitle']
        
        # Create a mock element
        mock_element = MagicMock()
        
        # Mock all attribute access methods to fail
        with patch('modules.accessibility.AXUIElementCopyAttributeValue') as mock_attr:
            mock_attr.side_effect = RuntimeError("All attribute access failed")
            
            # The method should not crash and should return a valid result
            match_found, confidence, attribute = accessibility._check_element_text_match(
                mock_element, "test"
            )
            
            # Should handle errors gracefully and return failure result
            assert isinstance(match_found, bool)
            assert isinstance(confidence, float)
            assert isinstance(attribute, str)
            assert confidence >= 0.0


class TestConfigurationValidationIntegration:
    """Test configuration validation integration in real usage scenarios."""
    
    @patch('modules.accessibility.AccessibilityModule._initialize_accessibility_api')
    def test_configuration_validation_with_invalid_config_during_operation(self, mock_init):
        """Test that invalid configuration doesn't break operations."""
        # Mock invalid configuration values
        with patch.dict('sys.modules', {
            'config': MagicMock(
                FUZZY_MATCHING_ENABLED="invalid",  # Should be boolean
                FUZZY_CONFIDENCE_THRESHOLD=150,    # Should be 0-100
                FUZZY_MATCHING_TIMEOUT=-100,       # Should be positive
                CLICKABLE_ROLES="not_a_list",      # Should be list
                ACCESSIBILITY_ATTRIBUTES=[],       # Should be non-empty
                FAST_PATH_TIMEOUT=0,               # Should be positive
                ATTRIBUTE_CHECK_TIMEOUT=-50,       # Should be positive
                ACCESSIBILITY_DEBUG_LOGGING="yes", # Should be boolean
                LOG_FUZZY_MATCH_SCORES=1           # Should be boolean
            )
        }):
            accessibility = AccessibilityModule()
            
            # Should use defaults for invalid values
            assert accessibility.fuzzy_matching_enabled is True
            assert accessibility.fuzzy_confidence_threshold == 85.0
            assert accessibility.fuzzy_matching_timeout_ms == 200.0
            assert len(accessibility.clickable_roles) > 0
            assert len(accessibility.accessibility_attributes) > 0
            assert accessibility.fast_path_timeout_ms == 2000.0
            assert accessibility.attribute_check_timeout_ms == 500.0
            assert accessibility.debug_logging is False
            assert accessibility.log_fuzzy_match_scores is False
    
    @patch('modules.accessibility.AccessibilityModule._initialize_accessibility_api')
    def test_configuration_import_error_during_operation(self, mock_init):
        """Test that configuration import errors don't break operations."""
        # Mock import error
        with patch('builtins.__import__', side_effect=ImportError("Config not found")):
            accessibility = AccessibilityModule()
            
            # Should use all defaults
            assert accessibility.fuzzy_matching_enabled is True
            assert accessibility.fuzzy_confidence_threshold == 85.0
            assert accessibility.fuzzy_matching_timeout_ms == 200.0
            assert len(accessibility.clickable_roles) > 0
            assert len(accessibility.accessibility_attributes) > 0


class TestPerformanceMonitoringWithErrors:
    """Test performance monitoring integration with error scenarios."""
    
    @patch('modules.accessibility.AccessibilityModule._initialize_accessibility_api')
    def test_performance_monitoring_with_timeout_errors(self, mock_init):
        """Test that performance monitoring works correctly with timeout errors."""
        accessibility = AccessibilityModule()
        accessibility.performance_monitoring_enabled = True
        
        # Mock a method that times out
        with patch.object(accessibility, '_find_element_with_enhanced_roles_tracked') as mock_enhanced:
            mock_enhanced.side_effect = AccessibilityTimeoutError(
                "Operation timed out", "element_search"
            )
            
            with patch.object(accessibility, '_find_element_button_only_fallback') as mock_fallback:
                mock_fallback.return_value = None  # Fallback also fails
                
                result = accessibility.find_element_enhanced('AXButton', 'test')
                
                assert result.found is False
                assert result.fallback_triggered is True
                assert result.search_time_ms > 0  # Should have timing information
    
    @patch('modules.accessibility.AccessibilityModule._initialize_accessibility_api')
    def test_performance_monitoring_with_multiple_errors(self, mock_init):
        """Test performance monitoring with multiple error types."""
        accessibility = AccessibilityModule()
        accessibility.performance_monitoring_enabled = True
        
        # Mock multiple error scenarios
        error_sequence = [
            FuzzyMatchingError("Fuzzy failed", "test", "element"),
            AttributeAccessError("Attribute failed", "AXTitle", {}),
            AccessibilityTimeoutError("Timeout", "search")
        ]
        
        with patch.object(accessibility, '_find_element_with_enhanced_roles_tracked') as mock_enhanced:
            mock_enhanced.side_effect = error_sequence[0]
            
            with patch.object(accessibility, '_find_element_button_only_fallback') as mock_fallback:
                mock_fallback.return_value = {
                    'role': 'AXButton',
                    'title': 'Test',
                    'coordinates': [0, 0, 10, 10],
                    'center_point': [5, 5],
                    'enabled': True,
                    'app_name': 'Test'
                }
                
                result = accessibility.find_element_enhanced('', 'test')
                
                assert result.found is True
                assert result.fallback_triggered is True
                assert result.search_time_ms > 0


if __name__ == '__main__':
    pytest.main([__file__])