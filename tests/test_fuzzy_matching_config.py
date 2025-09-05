"""
Unit tests for fuzzy matching configuration validation.

Tests configuration loading, validation, and default values for the
accessibility fast path enhancement fuzzy matching features.
"""

import pytest
import sys
import os
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add the project root to the path so we can import config
sys.path.insert(0, str(Path(__file__).parent.parent))

import config


class TestFuzzyMatchingConfiguration:
    """Test fuzzy matching configuration parameters."""
    
    def test_fuzzy_matching_enabled_default(self):
        """Test that fuzzy matching is enabled by default."""
        assert config.FUZZY_MATCHING_ENABLED is True
        assert isinstance(config.FUZZY_MATCHING_ENABLED, bool)
    
    def test_fuzzy_confidence_threshold_default(self):
        """Test fuzzy confidence threshold default value."""
        assert config.FUZZY_CONFIDENCE_THRESHOLD == 85
        assert isinstance(config.FUZZY_CONFIDENCE_THRESHOLD, int)
        assert 0 <= config.FUZZY_CONFIDENCE_THRESHOLD <= 100
    
    def test_fuzzy_matching_timeout_default(self):
        """Test fuzzy matching timeout default value."""
        assert config.FUZZY_MATCHING_TIMEOUT == 200
        assert isinstance(config.FUZZY_MATCHING_TIMEOUT, int)
        assert config.FUZZY_MATCHING_TIMEOUT > 0
    
    def test_clickable_roles_default(self):
        """Test clickable roles list default values."""
        expected_roles = [
            "AXButton", "AXLink", "AXMenuItem", 
            "AXCheckBox", "AXRadioButton"
        ]
        assert config.CLICKABLE_ROLES == expected_roles
        assert isinstance(config.CLICKABLE_ROLES, list)
        assert len(config.CLICKABLE_ROLES) > 0
        assert all(isinstance(role, str) for role in config.CLICKABLE_ROLES)
    
    def test_accessibility_attributes_default(self):
        """Test accessibility attributes list default values."""
        expected_attributes = ["AXTitle", "AXDescription", "AXValue"]
        assert config.ACCESSIBILITY_ATTRIBUTES == expected_attributes
        assert isinstance(config.ACCESSIBILITY_ATTRIBUTES, list)
        assert len(config.ACCESSIBILITY_ATTRIBUTES) > 0
        assert all(isinstance(attr, str) for attr in config.ACCESSIBILITY_ATTRIBUTES)
    
    def test_fast_path_timeout_default(self):
        """Test fast path timeout default value."""
        assert config.FAST_PATH_TIMEOUT == 2000
        assert isinstance(config.FAST_PATH_TIMEOUT, int)
        assert config.FAST_PATH_TIMEOUT > 0
    
    def test_attribute_check_timeout_default(self):
        """Test attribute check timeout default value."""
        assert config.ATTRIBUTE_CHECK_TIMEOUT == 500
        assert isinstance(config.ATTRIBUTE_CHECK_TIMEOUT, int)
        assert config.ATTRIBUTE_CHECK_TIMEOUT > 0
    
    def test_accessibility_debug_logging_default(self):
        """Test accessibility debug logging default value."""
        assert config.ACCESSIBILITY_DEBUG_LOGGING is False
        assert isinstance(config.ACCESSIBILITY_DEBUG_LOGGING, bool)
    
    def test_log_fuzzy_match_scores_default(self):
        """Test log fuzzy match scores default value."""
        assert config.LOG_FUZZY_MATCH_SCORES is False
        assert isinstance(config.LOG_FUZZY_MATCH_SCORES, bool)


class TestConfigurationValidation:
    """Test configuration validation for fuzzy matching parameters."""
    
    def test_validate_config_with_valid_fuzzy_settings(self):
        """Test that validate_config passes with valid fuzzy matching settings."""
        # Mock print to capture output
        with patch('builtins.print') as mock_print:
            result = config.validate_config()
            
            # Should return True for valid config
            assert result is True
            
            # Check that no fuzzy matching errors were printed
            printed_output = ' '.join([str(call) for call in mock_print.call_args_list])
            assert "FUZZY_CONFIDENCE_THRESHOLD" not in printed_output
            assert "FUZZY_MATCHING_TIMEOUT" not in printed_output
            assert "CLICKABLE_ROLES" not in printed_output
            assert "ACCESSIBILITY_ATTRIBUTES" not in printed_output
    
    @patch('config.FUZZY_CONFIDENCE_THRESHOLD', 150)
    def test_validate_config_with_invalid_confidence_threshold(self):
        """Test validation fails with invalid confidence threshold."""
        with patch('builtins.print') as mock_print:
            result = config.validate_config()
            
            # Should return False due to invalid threshold
            assert result is False
            
            # Check that the specific error was printed
            printed_output = ' '.join([str(call) for call in mock_print.call_args_list])
            assert "FUZZY_CONFIDENCE_THRESHOLD must be between 0 and 100" in printed_output
    
    @patch('config.FUZZY_CONFIDENCE_THRESHOLD', -10)
    def test_validate_config_with_negative_confidence_threshold(self):
        """Test validation fails with negative confidence threshold."""
        with patch('builtins.print') as mock_print:
            result = config.validate_config()
            
            assert result is False
            printed_output = ' '.join([str(call) for call in mock_print.call_args_list])
            assert "FUZZY_CONFIDENCE_THRESHOLD must be between 0 and 100" in printed_output
    
    @patch('config.FUZZY_MATCHING_TIMEOUT', 10)
    def test_validate_config_with_low_timeout_warning(self):
        """Test validation warns about very low timeout."""
        with patch('builtins.print') as mock_print:
            result = config.validate_config()
            
            # Should still return True but with warnings
            printed_output = ' '.join([str(call) for call in mock_print.call_args_list])
            assert "FUZZY_MATCHING_TIMEOUT should be between 50-5000 milliseconds" in printed_output
    
    @patch('config.FUZZY_MATCHING_TIMEOUT', 10000)
    def test_validate_config_with_high_timeout_warning(self):
        """Test validation warns about very high timeout."""
        with patch('builtins.print') as mock_print:
            result = config.validate_config()
            
            printed_output = ' '.join([str(call) for call in mock_print.call_args_list])
            assert "FUZZY_MATCHING_TIMEOUT should be between 50-5000 milliseconds" in printed_output
    
    @patch('config.CLICKABLE_ROLES', [])
    def test_validate_config_with_empty_clickable_roles(self):
        """Test validation fails with empty clickable roles list."""
        with patch('builtins.print') as mock_print:
            result = config.validate_config()
            
            assert result is False
            printed_output = ' '.join([str(call) for call in mock_print.call_args_list])
            assert "CLICKABLE_ROLES must be a non-empty list" in printed_output
    
    @patch('config.CLICKABLE_ROLES', "not_a_list")
    def test_validate_config_with_invalid_clickable_roles_type(self):
        """Test validation fails with invalid clickable roles type."""
        with patch('builtins.print') as mock_print:
            result = config.validate_config()
            
            assert result is False
            printed_output = ' '.join([str(call) for call in mock_print.call_args_list])
            assert "CLICKABLE_ROLES must be a non-empty list" in printed_output
    
    @patch('config.ACCESSIBILITY_ATTRIBUTES', [])
    def test_validate_config_with_empty_accessibility_attributes(self):
        """Test validation fails with empty accessibility attributes list."""
        with patch('builtins.print') as mock_print:
            result = config.validate_config()
            
            assert result is False
            printed_output = ' '.join([str(call) for call in mock_print.call_args_list])
            assert "ACCESSIBILITY_ATTRIBUTES must be a non-empty list" in printed_output
    
    @patch('config.ACCESSIBILITY_ATTRIBUTES', "not_a_list")
    def test_validate_config_with_invalid_accessibility_attributes_type(self):
        """Test validation fails with invalid accessibility attributes type."""
        with patch('builtins.print') as mock_print:
            result = config.validate_config()
            
            assert result is False
            printed_output = ' '.join([str(call) for call in mock_print.call_args_list])
            assert "ACCESSIBILITY_ATTRIBUTES must be a non-empty list" in printed_output
    
    @patch('config.FAST_PATH_TIMEOUT', 100)
    def test_validate_config_with_low_fast_path_timeout_warning(self):
        """Test validation warns about low fast path timeout."""
        with patch('builtins.print') as mock_print:
            result = config.validate_config()
            
            printed_output = ' '.join([str(call) for call in mock_print.call_args_list])
            assert "FAST_PATH_TIMEOUT should be between 500-10000 milliseconds" in printed_output
    
    @patch('config.ATTRIBUTE_CHECK_TIMEOUT', 50)
    def test_validate_config_with_low_attribute_check_timeout_warning(self):
        """Test validation warns about low attribute check timeout."""
        with patch('builtins.print') as mock_print:
            result = config.validate_config()
            
            printed_output = ' '.join([str(call) for call in mock_print.call_args_list])
            assert "ATTRIBUTE_CHECK_TIMEOUT should be between 100-2000 milliseconds" in printed_output
    
    @patch('config.FUZZY_MATCHING_ENABLED', "not_a_bool")
    def test_validate_config_with_invalid_fuzzy_enabled_type(self):
        """Test validation fails with invalid fuzzy matching enabled type."""
        with patch('builtins.print') as mock_print:
            result = config.validate_config()
            
            assert result is False
            printed_output = ' '.join([str(call) for call in mock_print.call_args_list])
            assert "FUZZY_MATCHING_ENABLED must be a boolean" in printed_output
    
    @patch('config.ACCESSIBILITY_DEBUG_LOGGING', "not_a_bool")
    def test_validate_config_with_invalid_debug_logging_type(self):
        """Test validation fails with invalid debug logging type."""
        with patch('builtins.print') as mock_print:
            result = config.validate_config()
            
            assert result is False
            printed_output = ' '.join([str(call) for call in mock_print.call_args_list])
            assert "ACCESSIBILITY_DEBUG_LOGGING must be a boolean" in printed_output
    
    @patch('config.LOG_FUZZY_MATCH_SCORES', "not_a_bool")
    def test_validate_config_with_invalid_log_scores_type(self):
        """Test validation fails with invalid log scores type."""
        with patch('builtins.print') as mock_print:
            result = config.validate_config()
            
            assert result is False
            printed_output = ' '.join([str(call) for call in mock_print.call_args_list])
            assert "LOG_FUZZY_MATCH_SCORES must be a boolean" in printed_output


class TestConfigurationSummary:
    """Test configuration summary includes fuzzy matching settings."""
    
    def test_get_config_summary_includes_fuzzy_matching(self):
        """Test that get_config_summary includes fuzzy matching configuration."""
        summary = config.get_config_summary()
        
        assert 'fuzzy_matching' in summary
        fuzzy_config = summary['fuzzy_matching']
        
        # Check all expected keys are present
        expected_keys = [
            'enabled', 'confidence_threshold', 'timeout_ms',
            'clickable_roles', 'accessibility_attributes',
            'fast_path_timeout_ms', 'attribute_check_timeout_ms',
            'debug_logging', 'log_match_scores'
        ]
        
        for key in expected_keys:
            assert key in fuzzy_config, f"Missing key: {key}"
        
        # Check values match configuration
        assert fuzzy_config['enabled'] == config.FUZZY_MATCHING_ENABLED
        assert fuzzy_config['confidence_threshold'] == config.FUZZY_CONFIDENCE_THRESHOLD
        assert fuzzy_config['timeout_ms'] == config.FUZZY_MATCHING_TIMEOUT
        assert fuzzy_config['clickable_roles'] == config.CLICKABLE_ROLES
        assert fuzzy_config['accessibility_attributes'] == config.ACCESSIBILITY_ATTRIBUTES
        assert fuzzy_config['fast_path_timeout_ms'] == config.FAST_PATH_TIMEOUT
        assert fuzzy_config['attribute_check_timeout_ms'] == config.ATTRIBUTE_CHECK_TIMEOUT
        assert fuzzy_config['debug_logging'] == config.ACCESSIBILITY_DEBUG_LOGGING
        assert fuzzy_config['log_match_scores'] == config.LOG_FUZZY_MATCH_SCORES
    
    def test_config_summary_types(self):
        """Test that config summary values have correct types."""
        summary = config.get_config_summary()
        fuzzy_config = summary['fuzzy_matching']
        
        assert isinstance(fuzzy_config['enabled'], bool)
        assert isinstance(fuzzy_config['confidence_threshold'], int)
        assert isinstance(fuzzy_config['timeout_ms'], int)
        assert isinstance(fuzzy_config['clickable_roles'], list)
        assert isinstance(fuzzy_config['accessibility_attributes'], list)
        assert isinstance(fuzzy_config['fast_path_timeout_ms'], int)
        assert isinstance(fuzzy_config['attribute_check_timeout_ms'], int)
        assert isinstance(fuzzy_config['debug_logging'], bool)
        assert isinstance(fuzzy_config['log_match_scores'], bool)


class TestConfigurationDefaults:
    """Test that configuration provides sensible defaults."""
    
    def test_fuzzy_matching_sensible_defaults(self):
        """Test that fuzzy matching has sensible default values."""
        # Fuzzy matching should be enabled by default
        assert config.FUZZY_MATCHING_ENABLED is True
        
        # Confidence threshold should be high enough to avoid false positives
        # but low enough to catch reasonable variations
        assert 80 <= config.FUZZY_CONFIDENCE_THRESHOLD <= 90
        
        # Timeout should be reasonable for performance
        assert 100 <= config.FUZZY_MATCHING_TIMEOUT <= 500
        
        # Should include common clickable roles
        assert "AXButton" in config.CLICKABLE_ROLES
        assert "AXLink" in config.CLICKABLE_ROLES
        assert len(config.CLICKABLE_ROLES) >= 3
        
        # Should include primary accessibility attributes
        assert "AXTitle" in config.ACCESSIBILITY_ATTRIBUTES
        assert len(config.ACCESSIBILITY_ATTRIBUTES) >= 2
        
        # Performance timeouts should be reasonable
        assert 1000 <= config.FAST_PATH_TIMEOUT <= 5000
        assert 200 <= config.ATTRIBUTE_CHECK_TIMEOUT <= 1000
        
        # Debug logging should be off by default for performance
        assert config.ACCESSIBILITY_DEBUG_LOGGING is False
        assert config.LOG_FUZZY_MATCH_SCORES is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])