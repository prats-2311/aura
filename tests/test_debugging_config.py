"""
Unit tests for debugging configuration validation and loading.

Tests the debugging configuration options added to config.py including:
- Configuration validation
- Default value handling
- Configuration loading
- Error handling for invalid configurations
"""

import pytest
import os
import sys
from unittest.mock import patch, MagicMock

# Add the parent directory to the path to import config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config


class TestDebuggingConfigValidation:
    """Test debugging configuration validation."""
    
    def test_validate_debugging_config_valid_defaults(self):
        """Test that default debugging configuration is valid."""
        is_valid, errors, warnings = config.validate_debugging_config()
        
        assert is_valid, f"Default config should be valid. Errors: {errors}"
        assert isinstance(errors, list)
        assert isinstance(warnings, list)
    
    def test_validate_debug_level_valid(self):
        """Test validation of valid debug levels."""
        original_level = config.DEBUG_LEVEL
        
        try:
            for level in config.DEBUG_LEVELS.keys():
                config.DEBUG_LEVEL = level
                is_valid, errors, warnings = config.validate_debugging_config()
                assert is_valid or level not in errors[0] if errors else True
        finally:
            config.DEBUG_LEVEL = original_level
    
    def test_validate_debug_level_invalid(self):
        """Test validation of invalid debug levels."""
        original_level = config.DEBUG_LEVEL
        
        try:
            config.DEBUG_LEVEL = "INVALID_LEVEL"
            is_valid, errors, warnings = config.validate_debugging_config()
            assert not is_valid
            assert any("DEBUG_LEVEL" in error for error in errors)
        finally:
            config.DEBUG_LEVEL = original_level
    
    def test_validate_output_format_valid(self):
        """Test validation of valid output formats."""
        original_format = config.DEBUG_OUTPUT_FORMAT
        
        try:
            for fmt in ["structured", "json", "plain"]:
                config.DEBUG_OUTPUT_FORMAT = fmt
                is_valid, errors, warnings = config.validate_debugging_config()
                # Should be valid or not fail specifically on format
                format_errors = [e for e in errors if "DEBUG_OUTPUT_FORMAT" in e]
                assert len(format_errors) == 0
        finally:
            config.DEBUG_OUTPUT_FORMAT = original_format
    
    def test_validate_output_format_invalid(self):
        """Test validation of invalid output formats."""
        original_format = config.DEBUG_OUTPUT_FORMAT
        
        try:
            config.DEBUG_OUTPUT_FORMAT = "invalid_format"
            is_valid, errors, warnings = config.validate_debugging_config()
            assert not is_valid
            assert any("DEBUG_OUTPUT_FORMAT" in error for error in errors)
        finally:
            config.DEBUG_OUTPUT_FORMAT = original_format
    
    def test_validate_permission_timeout_valid(self):
        """Test validation of valid permission timeout values."""
        original_timeout = config.PERMISSION_VALIDATION_TIMEOUT
        
        try:
            for timeout in [1.0, 5.0, 15.0, 30.0]:
                config.PERMISSION_VALIDATION_TIMEOUT = timeout
                is_valid, errors, warnings = config.validate_debugging_config()
                timeout_errors = [e for e in errors if "PERMISSION_VALIDATION_TIMEOUT" in e]
                assert len(timeout_errors) == 0
        finally:
            config.PERMISSION_VALIDATION_TIMEOUT = original_timeout
    
    def test_validate_permission_timeout_invalid(self):
        """Test validation of invalid permission timeout values."""
        original_timeout = config.PERMISSION_VALIDATION_TIMEOUT
        
        try:
            config.PERMISSION_VALIDATION_TIMEOUT = -1.0
            is_valid, errors, warnings = config.validate_debugging_config()
            assert not is_valid
            assert any("PERMISSION_VALIDATION_TIMEOUT" in error for error in errors)
        finally:
            config.PERMISSION_VALIDATION_TIMEOUT = original_timeout
    
    def test_validate_tree_dump_max_depth_valid(self):
        """Test validation of valid tree dump max depth values."""
        original_depth = config.TREE_DUMP_MAX_DEPTH
        
        try:
            for depth in [1, 5, 10, 15]:
                config.TREE_DUMP_MAX_DEPTH = depth
                is_valid, errors, warnings = config.validate_debugging_config()
                depth_errors = [e for e in errors if "TREE_DUMP_MAX_DEPTH" in e]
                assert len(depth_errors) == 0
        finally:
            config.TREE_DUMP_MAX_DEPTH = original_depth
    
    def test_validate_tree_dump_max_depth_invalid(self):
        """Test validation of invalid tree dump max depth values."""
        original_depth = config.TREE_DUMP_MAX_DEPTH
        
        try:
            config.TREE_DUMP_MAX_DEPTH = 0
            is_valid, errors, warnings = config.validate_debugging_config()
            assert not is_valid
            assert any("TREE_DUMP_MAX_DEPTH" in error for error in errors)
        finally:
            config.TREE_DUMP_MAX_DEPTH = original_depth
    
    def test_validate_similarity_threshold_valid(self):
        """Test validation of valid similarity threshold values."""
        original_threshold = config.SIMILARITY_SCORE_THRESHOLD
        
        try:
            for threshold in [0.0, 0.3, 0.6, 0.9, 1.0]:
                config.SIMILARITY_SCORE_THRESHOLD = threshold
                is_valid, errors, warnings = config.validate_debugging_config()
                threshold_errors = [e for e in errors if "SIMILARITY_SCORE_THRESHOLD" in e]
                assert len(threshold_errors) == 0
        finally:
            config.SIMILARITY_SCORE_THRESHOLD = original_threshold
    
    def test_validate_similarity_threshold_invalid(self):
        """Test validation of invalid similarity threshold values."""
        original_threshold = config.SIMILARITY_SCORE_THRESHOLD
        
        try:
            for invalid_threshold in [-0.1, 1.1, 2.0]:
                config.SIMILARITY_SCORE_THRESHOLD = invalid_threshold
                is_valid, errors, warnings = config.validate_debugging_config()
                assert not is_valid
                assert any("SIMILARITY_SCORE_THRESHOLD" in error for error in errors)
        finally:
            config.SIMILARITY_SCORE_THRESHOLD = original_threshold
    
    def test_validate_error_recovery_settings(self):
        """Test validation of error recovery settings."""
        original_retries = config.ERROR_RECOVERY_MAX_RETRIES
        original_backoff = config.ERROR_RECOVERY_BACKOFF_FACTOR
        original_base_delay = config.ERROR_RECOVERY_BASE_DELAY
        original_max_delay = config.ERROR_RECOVERY_MAX_DELAY
        
        try:
            # Test valid settings
            config.ERROR_RECOVERY_MAX_RETRIES = 3
            config.ERROR_RECOVERY_BACKOFF_FACTOR = 2.0
            config.ERROR_RECOVERY_BASE_DELAY = 0.5
            config.ERROR_RECOVERY_MAX_DELAY = 5.0
            
            is_valid, errors, warnings = config.validate_debugging_config()
            recovery_errors = [e for e in errors if "ERROR_RECOVERY" in e]
            assert len(recovery_errors) == 0
            
            # Test invalid max delay (less than base delay)
            config.ERROR_RECOVERY_MAX_DELAY = 0.1
            is_valid, errors, warnings = config.validate_debugging_config()
            assert not is_valid
            assert any("ERROR_RECOVERY_MAX_DELAY" in error for error in errors)
            
        finally:
            config.ERROR_RECOVERY_MAX_RETRIES = original_retries
            config.ERROR_RECOVERY_BACKOFF_FACTOR = original_backoff
            config.ERROR_RECOVERY_BASE_DELAY = original_base_delay
            config.ERROR_RECOVERY_MAX_DELAY = original_max_delay
    
    def test_validate_export_formats_valid(self):
        """Test validation of valid export formats."""
        original_formats = config.DEBUG_REPORT_EXPORT_FORMATS
        
        try:
            valid_formats = [["json"], ["html"], ["json", "html"], ["json", "html", "text"]]
            for formats in valid_formats:
                config.DEBUG_REPORT_EXPORT_FORMATS = formats
                is_valid, errors, warnings = config.validate_debugging_config()
                format_errors = [e for e in errors if "export format" in e]
                assert len(format_errors) == 0
        finally:
            config.DEBUG_REPORT_EXPORT_FORMATS = original_formats
    
    def test_validate_export_formats_invalid(self):
        """Test validation of invalid export formats."""
        original_formats = config.DEBUG_REPORT_EXPORT_FORMATS
        
        try:
            config.DEBUG_REPORT_EXPORT_FORMATS = ["invalid_format"]
            is_valid, errors, warnings = config.validate_debugging_config()
            assert not is_valid
            assert any("export format" in error for error in errors)
        finally:
            config.DEBUG_REPORT_EXPORT_FORMATS = original_formats


class TestDebuggingConfigDefaults:
    """Test debugging configuration default values."""
    
    def test_get_debugging_config_defaults(self):
        """Test that debugging config defaults are returned correctly."""
        defaults = config.get_debugging_config_defaults()
        
        assert isinstance(defaults, dict)
        assert 'debug_level' in defaults
        assert 'output_format' in defaults
        assert 'permission_validation_enabled' in defaults
        assert 'tree_inspection_enabled' in defaults
        assert 'element_analysis_enabled' in defaults
        assert 'error_recovery_enabled' in defaults
        assert 'diagnostic_tools_enabled' in defaults
    
    def test_defaults_are_valid_types(self):
        """Test that default values have correct types."""
        defaults = config.get_debugging_config_defaults()
        
        # String values
        assert isinstance(defaults['debug_level'], str)
        assert isinstance(defaults['output_format'], str)
        
        # Boolean values
        assert isinstance(defaults['permission_validation_enabled'], bool)
        assert isinstance(defaults['permission_auto_request'], bool)
        assert isinstance(defaults['tree_inspection_enabled'], bool)
        assert isinstance(defaults['element_analysis_enabled'], bool)
        assert isinstance(defaults['error_recovery_enabled'], bool)
        assert isinstance(defaults['diagnostic_tools_enabled'], bool)
        
        # Numeric values
        assert isinstance(defaults['permission_validation_timeout'], (int, float))
        assert isinstance(defaults['tree_dump_max_depth'], int)
        assert isinstance(defaults['element_search_timeout'], (int, float))
        assert isinstance(defaults['similarity_score_threshold'], (int, float))
    
    def test_defaults_are_valid_values(self):
        """Test that default values are within valid ranges."""
        defaults = config.get_debugging_config_defaults()
        
        # Debug level should be valid
        assert defaults['debug_level'] in config.DEBUG_LEVELS
        
        # Output format should be valid
        assert defaults['output_format'] in ['structured', 'json', 'plain']
        
        # Numeric values should be in valid ranges
        assert defaults['permission_validation_timeout'] > 0
        assert defaults['tree_dump_max_depth'] > 0
        assert defaults['element_search_timeout'] > 0
        assert 0 <= defaults['similarity_score_threshold'] <= 1
        assert 0 <= defaults['debug_performance_degradation_threshold'] <= 1


class TestConfigSummaryDebugging:
    """Test debugging configuration in config summary."""
    
    def test_config_summary_includes_debugging(self):
        """Test that config summary includes debugging configuration."""
        summary = config.get_config_summary()
        
        assert 'debugging' in summary
        debugging_config = summary['debugging']
        
        # Check main debugging sections
        assert 'debug_level' in debugging_config
        assert 'output_format' in debugging_config
        assert 'categories' in debugging_config
        assert 'permission_validation' in debugging_config
        assert 'tree_inspection' in debugging_config
        assert 'element_analysis' in debugging_config
        assert 'application_detection' in debugging_config
        assert 'error_recovery' in debugging_config
        assert 'diagnostic_tools' in debugging_config
        assert 'performance_tracking' in debugging_config
        assert 'interactive_debugging' in debugging_config
        assert 'cli_tools' in debugging_config
        assert 'reporting' in debugging_config
        assert 'security' in debugging_config
    
    def test_debugging_subsections_complete(self):
        """Test that debugging subsections contain expected keys."""
        summary = config.get_config_summary()
        debugging_config = summary['debugging']
        
        # Permission validation section
        perm_config = debugging_config['permission_validation']
        expected_perm_keys = ['enabled', 'auto_request', 'timeout', 'monitoring_enabled', 'guide_enabled']
        for key in expected_perm_keys:
            assert key in perm_config
        
        # Tree inspection section
        tree_config = debugging_config['tree_inspection']
        expected_tree_keys = ['enabled', 'max_depth', 'include_hidden', 'cache_enabled', 'cache_ttl']
        for key in expected_tree_keys:
            assert key in tree_config
        
        # Element analysis section
        element_config = debugging_config['element_analysis']
        expected_element_keys = ['enabled', 'search_timeout', 'comparison_enabled', 'fuzzy_match_analysis', 'similarity_threshold', 'search_strategies']
        for key in expected_element_keys:
            assert key in element_config
        
        # Error recovery section
        recovery_config = debugging_config['error_recovery']
        expected_recovery_keys = ['enabled', 'max_retries', 'backoff_factor', 'base_delay', 'max_delay', 'tree_refresh_enabled', 'cache_invalidation_enabled']
        for key in expected_recovery_keys:
            assert key in recovery_config


class TestEnvironmentVariableHandling:
    """Test environment variable handling for debugging configuration."""
    
    @patch.dict(os.environ, {'AURA_DEBUG_LEVEL': 'VERBOSE'})
    def test_debug_level_from_environment(self):
        """Test that debug level can be set from environment variable."""
        # Reload the config module to pick up environment variable
        import importlib
        importlib.reload(config)
        
        assert config.DEBUG_LEVEL == 'VERBOSE'
    
    @patch.dict(os.environ, {'AURA_DEBUG_LEVEL': 'INVALID'})
    def test_invalid_debug_level_from_environment(self):
        """Test handling of invalid debug level from environment."""
        # Reload the config module to pick up environment variable
        import importlib
        importlib.reload(config)
        
        # Should use the invalid value (validation will catch it)
        assert config.DEBUG_LEVEL == 'INVALID'
        
        # Validation should fail
        is_valid, errors, warnings = config.validate_debugging_config()
        assert not is_valid
        assert any("DEBUG_LEVEL" in error for error in errors)
    
    def test_default_debug_level_when_no_environment(self):
        """Test that default debug level is used when no environment variable is set."""
        # Ensure environment variable is not set
        if 'AURA_DEBUG_LEVEL' in os.environ:
            del os.environ['AURA_DEBUG_LEVEL']
        
        # Reload the config module
        import importlib
        importlib.reload(config)
        
        assert config.DEBUG_LEVEL == 'BASIC'


class TestConfigurationDocumentation:
    """Test that configuration has proper documentation."""
    
    def test_debug_levels_documented(self):
        """Test that debug levels have proper documentation."""
        assert isinstance(config.DEBUG_LEVELS, dict)
        assert len(config.DEBUG_LEVELS) > 0
        
        # Each level should have a numeric value
        for level, value in config.DEBUG_LEVELS.items():
            assert isinstance(level, str)
            assert isinstance(value, int)
            assert value > 0
    
    def test_debug_categories_documented(self):
        """Test that debug categories are properly documented."""
        assert isinstance(config.DEBUG_CATEGORIES, dict)
        assert len(config.DEBUG_CATEGORIES) > 0
        
        # Each category should have a boolean value
        for category, enabled in config.DEBUG_CATEGORIES.items():
            assert isinstance(category, str)
            assert isinstance(enabled, bool)
    
    def test_element_search_strategies_documented(self):
        """Test that element search strategies are documented."""
        assert isinstance(config.ELEMENT_SEARCH_STRATEGIES, list)
        assert len(config.ELEMENT_SEARCH_STRATEGIES) > 0
        
        # Each strategy should be a string
        for strategy in config.ELEMENT_SEARCH_STRATEGIES:
            assert isinstance(strategy, str)
            assert len(strategy) > 0


if __name__ == '__main__':
    pytest.main([__file__])