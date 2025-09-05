"""
Unit tests for enhanced error handling infrastructure in AccessibilityModule.

Tests cover:
- New exception types
- Graceful degradation when thefuzz library is unavailable
- Error recovery logic for attribute access failures and timeout scenarios
- Configuration validation with fallback values
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
    ConfigurationValidationError
)


class TestEnhancedExceptionTypes:
    """Test the new exception types for enhanced error handling."""
    
    def test_fuzzy_matching_error_creation(self):
        """Test FuzzyMatchingError exception creation and attributes."""
        original_error = ValueError("Test error")
        error = FuzzyMatchingError(
            "Fuzzy matching failed",
            target_text="test target",
            element_text="test element",
            original_error=original_error
        )
        
        assert str(error) == "Fuzzy matching failed"
        assert error.target_text == "test target"
        assert error.element_text == "test element"
        assert error.original_error == original_error
    
    def test_target_extraction_error_creation(self):
        """Test TargetExtractionError exception creation and attributes."""
        original_error = RuntimeError("Parsing failed")
        error = TargetExtractionError(
            "Target extraction failed",
            command="click on button",
            original_error=original_error
        )
        
        assert str(error) == "Target extraction failed"
        assert error.command == "click on button"
        assert error.original_error == original_error
    
    def test_attribute_access_error_creation(self):
        """Test AttributeAccessError exception creation and attributes."""
        element_info = {"role": "AXButton", "title": "Test"}
        original_error = AttributeError("Attribute not found")
        error = AttributeAccessError(
            "Attribute access failed",
            attribute="AXTitle",
            element_info=element_info,
            original_error=original_error
        )
        
        assert str(error) == "Attribute access failed"
        assert error.attribute == "AXTitle"
        assert error.element_info == element_info
        assert error.original_error == original_error
    
    def test_enhanced_fast_path_error_creation(self):
        """Test EnhancedFastPathError exception creation and attributes."""
        original_error = TimeoutError("Operation timed out")
        error = EnhancedFastPathError(
            "Fast path operation failed",
            operation="element_search",
            fallback_available=True,
            original_error=original_error
        )
        
        assert str(error) == "Fast path operation failed"
        assert error.operation == "element_search"
        assert error.fallback_available is True
        assert error.original_error == original_error
    
    def test_configuration_validation_error_creation(self):
        """Test ConfigurationValidationError exception creation and attributes."""
        error = ConfigurationValidationError(
            "Invalid configuration value",
            parameter="FUZZY_CONFIDENCE_THRESHOLD",
            current_value=150,
            expected_type=int
        )
        
        assert str(error) == "Invalid configuration value"
        assert error.parameter == "FUZZY_CONFIDENCE_THRESHOLD"
        assert error.current_value == 150
        assert error.expected_type == int


class TestFuzzyMatchingErrorHandling:
    """Test fuzzy matching error handling and graceful degradation."""
    
    @patch('modules.accessibility.FUZZY_MATCHING_AVAILABLE', False)
    def test_fuzzy_matching_unavailable_graceful_degradation(self):
        """Test graceful degradation when fuzzy matching library is unavailable."""
        accessibility = AccessibilityModule()
        
        # Should fall back to exact matching
        match_found, confidence = accessibility._safe_fuzzy_match("test", "test")
        assert match_found is True
        assert confidence == 100.0
        
        match_found, confidence = accessibility._safe_fuzzy_match("test", "different")
        assert match_found is False
        assert confidence == 0.0
    
    @patch('modules.accessibility.FUZZY_MATCHING_AVAILABLE', True)
    @patch('modules.accessibility.fuzz')
    def test_fuzzy_matching_timeout_handling(self, mock_fuzz):
        """Test timeout handling in fuzzy matching operations."""
        accessibility = AccessibilityModule()
        accessibility.fuzzy_matching_timeout_ms = 100  # Short timeout for testing
        
        # Mock fuzz.partial_ratio to simulate slow operation
        def slow_fuzzy_match(*args, **kwargs):
            time.sleep(0.2)  # Simulate slow operation
            return 90
        
        mock_fuzz.partial_ratio = slow_fuzzy_match
        
        # Should handle timeout and fall back to exact matching
        match_found, confidence = accessibility._safe_fuzzy_match("test", "test")
        assert match_found is True  # Exact match fallback
        assert confidence == 100.0
    
    @patch('modules.accessibility.FUZZY_MATCHING_AVAILABLE', True)
    @patch('modules.accessibility.fuzz')
    def test_fuzzy_matching_exception_handling(self, mock_fuzz):
        """Test exception handling in fuzzy matching operations."""
        accessibility = AccessibilityModule()
        
        # Mock fuzz.partial_ratio to raise an exception
        mock_fuzz.partial_ratio.side_effect = RuntimeError("Fuzzy matching error")
        
        # Should handle exception and fall back to exact matching
        match_found, confidence = accessibility._safe_fuzzy_match("test", "test")
        assert match_found is True  # Exact match fallback
        assert confidence == 100.0
        
        match_found, confidence = accessibility._safe_fuzzy_match("test", "different")
        assert match_found is False
        assert confidence == 0.0
    
    def test_handle_fuzzy_matching_error_exact_match_success(self):
        """Test fuzzy matching error handler with successful exact match."""
        accessibility = AccessibilityModule()
        
        error = RuntimeError("Fuzzy matching failed")
        match_found, confidence = accessibility._handle_fuzzy_matching_error(
            error, "test", "test"
        )
        
        assert match_found is True
        assert confidence == 100.0
    
    def test_handle_fuzzy_matching_error_exact_match_failure(self):
        """Test fuzzy matching error handler with failed exact match."""
        accessibility = AccessibilityModule()
        
        error = RuntimeError("Fuzzy matching failed")
        match_found, confidence = accessibility._handle_fuzzy_matching_error(
            error, "test", "different"
        )
        
        assert match_found is False
        assert confidence == 0.0


class TestAttributeAccessErrorHandling:
    """Test attribute access error handling and recovery."""
    
    def test_handle_attribute_access_error_dict_fallback(self):
        """Test attribute access error handling with dictionary fallback."""
        accessibility = AccessibilityModule()
        
        element_info = {"AXTitle": "Test Button", "title": "Fallback Title"}
        error = AttributeError("Attribute not accessible")
        
        result = accessibility._handle_attribute_access_error(
            error, "AXTitle", element_info
        )
        
        assert result == "Test Button"
    
    def test_handle_attribute_access_error_alias_fallback(self):
        """Test attribute access error handling with alias fallback."""
        accessibility = AccessibilityModule()
        
        element_info = {"title": "Fallback Title"}  # No AXTitle, but has alias
        error = AttributeError("AXTitle not accessible")
        
        result = accessibility._handle_attribute_access_error(
            error, "AXTitle", element_info
        )
        
        assert result == "Fallback Title"
    
    def test_handle_attribute_access_error_no_fallback(self):
        """Test attribute access error handling when no fallback is available."""
        accessibility = AccessibilityModule()
        
        element_info = {}  # No attributes available
        error = AttributeError("Attribute not accessible")
        
        result = accessibility._handle_attribute_access_error(
            error, "AXTitle", element_info
        )
        
        assert result is None
    
    def test_handle_attribute_access_error_fallback_exception(self):
        """Test attribute access error handling when fallback also fails."""
        accessibility = AccessibilityModule()
        
        # Mock element_info to raise exception on access
        element_info = MagicMock()
        element_info.get.side_effect = RuntimeError("Fallback failed")
        
        error = AttributeError("Attribute not accessible")
        
        result = accessibility._handle_attribute_access_error(
            error, "AXTitle", element_info
        )
        
        assert result is None


class TestTargetExtractionErrorHandling:
    """Test target extraction error handling and recovery."""
    
    def test_handle_target_extraction_error_simple_fallback(self):
        """Test target extraction error handling with simple word removal."""
        accessibility = AccessibilityModule()
        
        error = RuntimeError("Target extraction failed")
        result = accessibility._handle_target_extraction_error(
            error, "click on the submit button"
        )
        
        # Should remove "click", "on", "the" and return "submit button"
        assert result == "submit button"
    
    def test_handle_target_extraction_error_multiple_actions(self):
        """Test target extraction error handling with multiple action words."""
        accessibility = AccessibilityModule()
        
        error = RuntimeError("Target extraction failed")
        result = accessibility._handle_target_extraction_error(
            error, "press and click the login button"
        )
        
        # Should remove action words and articles
        assert "login button" in result
        assert "press" not in result
        assert "click" not in result
    
    def test_handle_target_extraction_error_no_words_left(self):
        """Test target extraction error handling when no words remain."""
        accessibility = AccessibilityModule()
        
        error = RuntimeError("Target extraction failed")
        result = accessibility._handle_target_extraction_error(
            error, "click on the"
        )
        
        # Should return original command when nothing is left
        assert result == "click on the"
    
    def test_handle_target_extraction_error_fallback_exception(self):
        """Test target extraction error handling when fallback fails."""
        accessibility = AccessibilityModule()
        
        error = RuntimeError("Target extraction failed")
        
        # Create a mock command that will cause an exception during processing
        # We'll simulate the exception by creating a command that causes issues
        # in the string processing logic
        with patch.object(accessibility, 'logger') as mock_logger:
            # Mock the logger.debug method to raise an exception
            mock_logger.debug.side_effect = RuntimeError("Logging failed")
            
            # The method should still return the original command even if logging fails
            result = accessibility._handle_target_extraction_error(
                error, "click button"
            )
            
            # Should return processed result even when logging fails
            assert "button" in result  # Should still process the command


class TestConfigurationValidation:
    """Test configuration validation and fallback mechanisms."""
    
    @patch('modules.accessibility.AccessibilityModule._validate_configuration_with_fallback')
    def test_configuration_validation_called_during_init(self, mock_validate):
        """Test that configuration validation is called during initialization."""
        mock_validate.return_value = {
            'fuzzy_matching_enabled': True,
            'fuzzy_confidence_threshold': 85.0,
            'fuzzy_matching_timeout_ms': 200.0,
            'clickable_roles': ["AXButton"],
            'accessibility_attributes': ["AXTitle"],
            'fast_path_timeout_ms': 2000.0,
            'attribute_check_timeout_ms': 500.0,
            'debug_logging': False,
            'log_fuzzy_match_scores': False
        }
        
        with patch('modules.accessibility.AccessibilityModule._initialize_accessibility_api'):
            accessibility = AccessibilityModule()
            
        mock_validate.assert_called_once()
        assert accessibility.fuzzy_matching_enabled is True
        assert accessibility.fuzzy_confidence_threshold == 85.0
    
    @patch('modules.accessibility.logging')
    def test_validate_configuration_with_valid_config(self, mock_logging):
        """Test configuration validation with valid configuration values."""
        with patch('modules.accessibility.AccessibilityModule._initialize_accessibility_api'):
            accessibility = AccessibilityModule()
        
        # Mock valid configuration import
        with patch.dict('sys.modules', {
            'config': MagicMock(
                FUZZY_MATCHING_ENABLED=True,
                FUZZY_CONFIDENCE_THRESHOLD=90,
                FUZZY_MATCHING_TIMEOUT=300,
                CLICKABLE_ROLES=["AXButton", "AXLink"],
                ACCESSIBILITY_ATTRIBUTES=["AXTitle", "AXDescription"],
                FAST_PATH_TIMEOUT=1500,
                ATTRIBUTE_CHECK_TIMEOUT=400,
                ACCESSIBILITY_DEBUG_LOGGING=True,
                LOG_FUZZY_MATCH_SCORES=False
            )
        }):
            config = accessibility._validate_configuration_with_fallback()
        
        assert config['fuzzy_matching_enabled'] is True
        assert config['fuzzy_confidence_threshold'] == 90.0
        assert config['fuzzy_matching_timeout_ms'] == 300.0
        assert config['clickable_roles'] == ["AXButton", "AXLink"]
        assert config['accessibility_attributes'] == ["AXTitle", "AXDescription"]
        assert config['fast_path_timeout_ms'] == 1500.0
        assert config['attribute_check_timeout_ms'] == 400.0
        assert config['debug_logging'] is True
        assert config['log_fuzzy_match_scores'] is False
    
    @patch('modules.accessibility.logging')
    def test_validate_configuration_with_invalid_values(self, mock_logging):
        """Test configuration validation with invalid values uses defaults."""
        with patch('modules.accessibility.AccessibilityModule._initialize_accessibility_api'):
            accessibility = AccessibilityModule()
        
        # Mock invalid configuration import
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
            config = accessibility._validate_configuration_with_fallback()
        
        # Should use defaults for invalid values
        assert config['fuzzy_matching_enabled'] is True  # Default
        assert config['fuzzy_confidence_threshold'] == 85.0  # Default
        assert config['fuzzy_matching_timeout_ms'] == 200.0  # Default
        assert config['clickable_roles'] == ["AXButton", "AXLink", "AXMenuItem", "AXCheckBox", "AXRadioButton"]
        assert config['accessibility_attributes'] == ["AXTitle", "AXDescription", "AXValue"]
        assert config['fast_path_timeout_ms'] == 2000.0  # Default
        assert config['attribute_check_timeout_ms'] == 500.0  # Default
        assert config['debug_logging'] is False  # Default
        assert config['log_fuzzy_match_scores'] is False  # Default
    
    @patch('modules.accessibility.logging')
    def test_validate_configuration_import_error(self, mock_logging):
        """Test configuration validation when config import fails."""
        with patch('modules.accessibility.AccessibilityModule._initialize_accessibility_api'):
            accessibility = AccessibilityModule()
        
        # Mock import error
        with patch('builtins.__import__', side_effect=ImportError("Config not found")):
            config = accessibility._validate_configuration_with_fallback()
        
        # Should use all defaults
        default_config = accessibility._get_default_configuration()
        assert config == default_config
    
    def test_get_default_configuration(self):
        """Test that default configuration contains all required keys."""
        with patch('modules.accessibility.AccessibilityModule._initialize_accessibility_api'):
            accessibility = AccessibilityModule()
        
        config = accessibility._get_default_configuration()
        
        required_keys = [
            'fuzzy_matching_enabled', 'fuzzy_confidence_threshold', 'fuzzy_matching_timeout_ms',
            'clickable_roles', 'accessibility_attributes', 'fast_path_timeout_ms',
            'attribute_check_timeout_ms', 'debug_logging', 'log_fuzzy_match_scores'
        ]
        
        for key in required_keys:
            assert key in config
        
        # Verify default values are reasonable
        assert isinstance(config['fuzzy_matching_enabled'], bool)
        assert 0 <= config['fuzzy_confidence_threshold'] <= 100
        assert config['fuzzy_matching_timeout_ms'] > 0
        assert isinstance(config['clickable_roles'], list)
        assert len(config['clickable_roles']) > 0
        assert isinstance(config['accessibility_attributes'], list)
        assert len(config['accessibility_attributes']) > 0
        assert config['fast_path_timeout_ms'] > 0
        assert config['attribute_check_timeout_ms'] > 0


class TestFuzzyMatchingAvailabilityCheck:
    """Test fuzzy matching availability checking and warning logging."""
    
    @patch('modules.accessibility.FUZZY_MATCHING_AVAILABLE', False)
    def test_check_fuzzy_matching_availability_unavailable(self):
        """Test fuzzy matching availability check when library is unavailable."""
        with patch('modules.accessibility.AccessibilityModule._initialize_accessibility_api'):
            accessibility = AccessibilityModule()
        
        # First call should log warning
        with patch.object(accessibility, 'logger') as mock_logger:
            result = accessibility._check_fuzzy_matching_availability()
            assert result is False
            mock_logger.warning.assert_called_once()
        
        # Second call should not log warning again
        with patch.object(accessibility, 'logger') as mock_logger:
            result = accessibility._check_fuzzy_matching_availability()
            assert result is False
            mock_logger.warning.assert_not_called()  # Should not log again
    
    @patch('modules.accessibility.FUZZY_MATCHING_AVAILABLE', True)
    def test_check_fuzzy_matching_availability_available(self):
        """Test fuzzy matching availability check when library is available."""
        with patch('modules.accessibility.AccessibilityModule._initialize_accessibility_api'):
            accessibility = AccessibilityModule()
        
        result = accessibility._check_fuzzy_matching_availability()
        assert result is True


if __name__ == '__main__':
    pytest.main([__file__])