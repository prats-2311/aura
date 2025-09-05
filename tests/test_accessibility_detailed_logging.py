"""
Unit tests for AccessibilityModule detailed operation logging functionality.

Tests the comprehensive logging system including:
- Element role checking logs
- Attribute examination logs  
- Fuzzy matching operation logs
- Performance metrics logging
- Success rate tracking
"""

import pytest
import logging
import time
from unittest.mock import Mock, patch, MagicMock
from modules.accessibility import AccessibilityModule


class TestAccessibilityDetailedLogging:
    """Test suite for detailed operation logging in AccessibilityModule."""
    
    @pytest.fixture
    def mock_accessibility_module(self):
        """Create a mock AccessibilityModule for testing."""
        with patch('modules.accessibility.ACCESSIBILITY_AVAILABLE', True):
            with patch('modules.accessibility.AXUIElementCreateSystemWide'):
                with patch('modules.accessibility.NSWorkspace'):
                    module = AccessibilityModule()
                    # Override loggers with mocks for testing
                    module.operation_logger = Mock()
                    module.performance_logger = Mock()
                    module.debug_logger = Mock()
                    return module
    
    def test_log_initialization_success(self, mock_accessibility_module):
        """Test logging of successful initialization."""
        module = mock_accessibility_module
        module.debug_logging = True
        
        module._log_initialization_success()
        
        # Verify initialization success was logged
        module.operation_logger.info.assert_called_once()
        call_args = module.operation_logger.info.call_args[0][0]
        assert "AccessibilityModule initialized successfully" in call_args
        
        # Verify debug configuration was logged
        module.debug_logger.debug.assert_called_once()
        debug_call_args = module.debug_logger.debug.call_args[0][0]
        assert "Configuration loaded" in debug_call_args
    
    def test_log_element_role_check_success(self, mock_accessibility_module):
        """Test logging of successful element role check."""
        module = mock_accessibility_module
        module.debug_logging = True
        
        element_info = {'role': 'AXButton', 'title': 'Test Button'}
        role = 'AXButton'
        duration_ms = 25.5
        
        module._log_element_role_check(element_info, role, True, duration_ms)
        
        # Verify metrics were updated
        assert module.operation_metrics['element_role_checks']['count'] == 1
        assert module.operation_metrics['element_role_checks']['total_time_ms'] == duration_ms
        assert module.operation_metrics['element_role_checks']['success_count'] == 1
        
        # Verify debug logging
        module.debug_logger.debug.assert_called_once()
        debug_call = module.debug_logger.debug.call_args[0][0]
        assert "Role check" in debug_call
        assert "AXButton" in debug_call
    
    def test_log_element_role_check_failure(self, mock_accessibility_module):
        """Test logging of failed element role check."""
        module = mock_accessibility_module
        module.debug_logging = True
        
        element_info = {'role': 'AXTextField', 'title': 'Input Field'}
        role = 'AXButton'
        duration_ms = 15.2
        
        module._log_element_role_check(element_info, role, False, duration_ms)
        
        # Verify metrics were updated correctly
        assert module.operation_metrics['element_role_checks']['count'] == 1
        assert module.operation_metrics['element_role_checks']['success_count'] == 0
        
        # Verify debug logging occurred
        module.debug_logger.debug.assert_called_once()
    
    def test_log_element_role_check_performance_warning(self, mock_accessibility_module):
        """Test performance warning for slow role check."""
        module = mock_accessibility_module
        
        element_info = {'role': 'AXButton', 'title': 'Slow Button'}
        role = 'AXButton'
        duration_ms = 150.0  # Above 100ms threshold
        
        module._log_element_role_check(element_info, role, True, duration_ms)
        
        # Verify performance warning was logged
        module.performance_logger.warning.assert_called_once()
        warning_call = module.performance_logger.warning.call_args[0][0]
        assert "Slow role check" in warning_call
        assert "150.00ms" in warning_call
    
    def test_log_attribute_examination_success(self, mock_accessibility_module):
        """Test logging of successful attribute examination."""
        module = mock_accessibility_module
        module.debug_logging = True
        
        element_info = {'role': 'AXButton', 'title': 'Test Button'}
        attribute = 'AXTitle'
        attribute_value = 'Test Button'
        duration_ms = 12.3
        
        module._log_attribute_examination(element_info, attribute, attribute_value, True, duration_ms)
        
        # Verify metrics were updated
        assert module.operation_metrics['attribute_examinations']['count'] == 1
        assert module.operation_metrics['attribute_examinations']['success_count'] == 1
        
        # Verify debug logging
        module.debug_logger.debug.assert_called_once()
        debug_call = module.debug_logger.debug.call_args[0][0]
        assert "Attribute examination" in debug_call
        assert "AXTitle" in debug_call
    
    def test_log_attribute_examination_long_value_truncation(self, mock_accessibility_module):
        """Test truncation of long attribute values in logging."""
        module = mock_accessibility_module
        module.debug_logging = True
        
        element_info = {'role': 'AXTextField'}
        attribute = 'AXValue'
        long_value = 'A' * 50  # 50 character string
        duration_ms = 8.1
        
        module._log_attribute_examination(element_info, attribute, long_value, True, duration_ms)
        
        # Verify debug logging with truncation
        module.debug_logger.debug.assert_called_once()
        debug_call = module.debug_logger.debug.call_args[0][0]
        assert "..." in debug_call  # Should be truncated
    
    def test_log_attribute_examination_performance_warning(self, mock_accessibility_module):
        """Test performance warning for slow attribute access."""
        module = mock_accessibility_module
        
        element_info = {'role': 'AXButton'}
        attribute = 'AXDescription'
        duration_ms = 75.0  # Above 50ms threshold
        
        module._log_attribute_examination(element_info, attribute, None, False, duration_ms)
        
        # Verify performance warning was logged
        module.performance_logger.warning.assert_called_once()
        warning_call = module.performance_logger.warning.call_args[0][0]
        assert "Slow attribute access" in warning_call
        assert "75.00ms" in warning_call
    
    def test_log_fuzzy_matching_operation_success(self, mock_accessibility_module):
        """Test logging of successful fuzzy matching operation."""
        module = mock_accessibility_module
        module.log_fuzzy_match_scores = True
        module.fuzzy_confidence_threshold = 85.0
        
        target_text = "sign in"
        element_text = "Sign In Button"
        confidence_score = 92.5
        duration_ms = 45.2
        
        module._log_fuzzy_matching_operation(target_text, element_text, confidence_score, True, duration_ms)
        
        # Verify metrics were updated
        assert module.operation_metrics['fuzzy_matching_operations']['count'] == 1
        assert module.operation_metrics['fuzzy_matching_operations']['success_count'] == 1
        
        # Verify fuzzy match score logging
        module.operation_logger.info.assert_called_once()
        info_call = module.operation_logger.info.call_args[0][0]
        assert "Fuzzy match" in info_call
        assert "92.5" in info_call
    
    def test_log_fuzzy_matching_operation_debug_mode(self, mock_accessibility_module):
        """Test fuzzy matching logging in debug mode."""
        module = mock_accessibility_module
        module.debug_logging = True
        module.log_fuzzy_match_scores = False
        
        target_text = "submit"
        element_text = "Submit Form"
        confidence_score = 78.3
        duration_ms = 23.1
        
        module._log_fuzzy_matching_operation(target_text, element_text, confidence_score, False, duration_ms)
        
        # Should use debug logger instead of operation logger
        module.debug_logger.debug.assert_called_once()
        module.operation_logger.info.assert_not_called()
    
    def test_log_fuzzy_matching_timeout_warning(self, mock_accessibility_module):
        """Test timeout warning for fuzzy matching."""
        module = mock_accessibility_module
        module.fuzzy_matching_timeout_ms = 200.0
        
        target_text = "test"
        element_text = "test element"
        confidence_score = 95.0
        duration_ms = 250.0  # Above timeout threshold
        
        module._log_fuzzy_matching_operation(target_text, element_text, confidence_score, True, duration_ms)
        
        # Verify timeout warning was logged
        module.performance_logger.warning.assert_called_once()
        warning_call = module.performance_logger.warning.call_args[0][0]
        assert "Fuzzy matching timeout" in warning_call
        assert "250.00ms" in warning_call
    
    def test_log_fuzzy_matching_approaching_timeout_warning(self, mock_accessibility_module):
        """Test warning when fuzzy matching approaches timeout."""
        module = mock_accessibility_module
        module.fuzzy_matching_timeout_ms = 200.0
        
        target_text = "test"
        element_text = "test element"
        confidence_score = 88.0
        duration_ms = 170.0  # 85% of timeout (above 80% threshold)
        
        module._log_fuzzy_matching_operation(target_text, element_text, confidence_score, True, duration_ms)
        
        # Verify approaching timeout warning was logged
        module.performance_logger.warning.assert_called_once()
        warning_call = module.performance_logger.warning.call_args[0][0]
        assert "Slow fuzzy matching" in warning_call
        assert "approaching timeout" in warning_call
    
    def test_log_target_extraction_success(self, mock_accessibility_module):
        """Test logging of successful target extraction."""
        module = mock_accessibility_module
        module.debug_logging = True
        
        original_command = "Click on the submit button"
        extracted_target = "submit button"
        action_type = "click"
        confidence = 0.85
        removed_words = ["click", "on", "the"]
        duration_ms = 8.7
        
        module._log_target_extraction(original_command, extracted_target, action_type, 
                                    confidence, removed_words, duration_ms)
        
        # Verify metrics were updated
        assert module.operation_metrics['target_extractions']['count'] == 1
        assert module.operation_metrics['target_extractions']['success_count'] == 1
        
        # Verify debug logging
        module.debug_logger.debug.assert_called_once()
        debug_call = module.debug_logger.debug.call_args[0][0]
        assert "Target extraction" in debug_call
        assert "submit button" in debug_call
    
    def test_log_target_extraction_low_confidence_warning(self, mock_accessibility_module):
        """Test warning for low confidence target extraction."""
        module = mock_accessibility_module
        
        original_command = "Do something unclear"
        extracted_target = "something unclear"
        action_type = "unknown"
        confidence = 0.3  # Below 0.5 threshold
        removed_words = []
        duration_ms = 5.2
        
        module._log_target_extraction(original_command, extracted_target, action_type,
                                    confidence, removed_words, duration_ms)
        
        # Verify low confidence warning was logged
        module.operation_logger.warning.assert_called_once()
        warning_call = module.operation_logger.warning.call_args[0][0]
        assert "Low confidence target extraction" in warning_call
        assert "0.30" in warning_call
    
    def test_log_performance_metrics(self, mock_accessibility_module):
        """Test logging of performance metrics."""
        module = mock_accessibility_module
        module.performance_monitoring_enabled = True
        module.performance_warning_threshold_ms = 1000.0
        
        operation_name = "element_search"
        duration_ms = 750.0
        success = True
        metadata = {"elements_checked": 15}
        
        module._log_performance_metrics(operation_name, duration_ms, success, metadata)
        
        # Verify performance statistics were updated
        assert module.performance_stats['total_operations'] == 1
        assert module.performance_stats['successful_operations'] == 1
        assert module.performance_stats['fastest_operation_ms'] == duration_ms
        assert module.performance_stats['slowest_operation_ms'] == duration_ms
        
        # Verify performance logging
        module.performance_logger.info.assert_called_once()
        info_call = module.performance_logger.info.call_args[0][0]
        assert "Performance" in info_call
        assert "element_search" in info_call
    
    def test_log_performance_metrics_warning(self, mock_accessibility_module):
        """Test performance warning for slow operations."""
        module = mock_accessibility_module
        module.performance_warning_threshold_ms = 1000.0
        
        operation_name = "slow_operation"
        duration_ms = 1500.0  # Above threshold
        success = True
        
        module._log_performance_metrics(operation_name, duration_ms, success)
        
        # Verify performance warning was logged
        module.performance_logger.warning.assert_called_once()
        warning_call = module.performance_logger.warning.call_args[0][0]
        assert "Performance warning" in warning_call
        assert "1500.00ms" in warning_call
        
        # Verify warning count was incremented
        assert module.performance_stats['performance_warnings'] == 1
    
    def test_log_cache_operation_hit(self, mock_accessibility_module):
        """Test logging of cache hit operation."""
        module = mock_accessibility_module
        module.debug_logging = True
        
        operation_type = "lookup"
        cache_key = "fuzzy_match_sign_in_button"
        hit = True
        duration_ms = 2.1
        
        module._log_cache_operation(operation_type, cache_key, hit, duration_ms)
        
        # Verify metrics were updated
        assert module.operation_metrics['cache_operations']['count'] == 1
        assert module.operation_metrics['cache_operations']['hit_count'] == 1
        
        # Verify debug logging
        module.debug_logger.debug.assert_called_once()
        debug_call = module.debug_logger.debug.call_args[0][0]
        assert "Cache operation" in debug_call
        assert "lookup" in debug_call
    
    def test_log_cache_operation_miss(self, mock_accessibility_module):
        """Test logging of cache miss operation."""
        module = mock_accessibility_module
        module.debug_logging = True
        
        operation_type = "lookup"
        cache_key = "new_fuzzy_match_key"
        hit = False
        duration_ms = 1.8
        
        module._log_cache_operation(operation_type, cache_key, hit, duration_ms)
        
        # Verify metrics were updated correctly
        assert module.operation_metrics['cache_operations']['count'] == 1
        assert module.operation_metrics['cache_operations']['hit_count'] == 0
        
        # Verify debug logging
        module.debug_logger.debug.assert_called_once()
    
    def test_log_cache_operation_long_key_truncation(self, mock_accessibility_module):
        """Test truncation of long cache keys in logging."""
        module = mock_accessibility_module
        module.debug_logging = True
        
        operation_type = "store"
        long_cache_key = "very_long_cache_key_" + "x" * 50
        hit = False
        duration_ms = 3.2
        
        module._log_cache_operation(operation_type, long_cache_key, hit, duration_ms)
        
        # Verify debug logging with truncation
        module.debug_logger.debug.assert_called_once()
        debug_call = module.debug_logger.debug.call_args[0][0]
        assert "..." in debug_call  # Should be truncated
    
    def test_log_success_rates(self, mock_accessibility_module):
        """Test logging of success rates."""
        module = mock_accessibility_module
        module.debug_logging = True
        
        # Set up some success rate data
        module.success_rates['fast_path_execution']['attempts'] = 10
        module.success_rates['fast_path_execution']['successes'] = 8
        module.success_rates['fuzzy_matching']['attempts'] = 15
        module.success_rates['fuzzy_matching']['successes'] = 12
        
        module._log_success_rates()
        
        # Verify success rates were logged
        module.operation_logger.info.assert_called_once()
        info_call = module.operation_logger.info.call_args[0][0]
        assert "Success rates" in info_call
        assert "80.0" in info_call  # 8/10 = 80%
        assert "80.0" in info_call  # 12/15 = 80%
    
    def test_log_success_rates_no_debug(self, mock_accessibility_module):
        """Test that success rates are not logged when debug is disabled."""
        module = mock_accessibility_module
        module.debug_logging = False
        
        module._log_success_rates()
        
        # Verify no logging occurred
        module.operation_logger.info.assert_not_called()
    
    def test_log_operation_summary_success(self, mock_accessibility_module):
        """Test logging of successful operation summary."""
        module = mock_accessibility_module
        
        operation_name = "enhanced_element_search"
        total_duration_ms = 450.2
        steps_completed = ["role_check", "attribute_examination", "fuzzy_matching"]
        success = True
        
        module._log_operation_summary(operation_name, total_duration_ms, steps_completed, success)
        
        # Verify success logging
        module.operation_logger.info.assert_called_once()
        info_call = module.operation_logger.info.call_args[0][0]
        assert "Operation completed" in info_call
        assert "enhanced_element_search" in info_call
        assert "450.2" in info_call
    
    def test_log_operation_summary_failure(self, mock_accessibility_module):
        """Test logging of failed operation summary."""
        module = mock_accessibility_module
        
        operation_name = "element_search"
        total_duration_ms = 1200.5
        steps_completed = ["role_check"]
        success = False
        error_message = "Element not found"
        
        module._log_operation_summary(operation_name, total_duration_ms, steps_completed, success, error_message)
        
        # Verify failure logging
        module.operation_logger.warning.assert_called_once()
        warning_call = module.operation_logger.warning.call_args[0][0]
        assert "Operation failed" in warning_call
        assert "Element not found" in warning_call
    
    def test_log_operation_summary_timeout_warning(self, mock_accessibility_module):
        """Test timeout warning in operation summary."""
        module = mock_accessibility_module
        module.fast_path_timeout_ms = 2000.0
        
        operation_name = "slow_operation"
        total_duration_ms = 2500.0  # Above timeout
        steps_completed = ["step1", "step2"]
        success = True
        
        module._log_operation_summary(operation_name, total_duration_ms, steps_completed, success)
        
        # Verify timeout warning was logged
        module.performance_logger.warning.assert_called_once()
        warning_call = module.performance_logger.warning.call_args[0][0]
        assert "exceeded fast path timeout" in warning_call
        assert "2500.00ms" in warning_call
    
    def test_get_performance_summary(self, mock_accessibility_module):
        """Test getting comprehensive performance summary."""
        module = mock_accessibility_module
        
        # Set up some test data
        module.performance_stats['total_operations'] = 20
        module.performance_stats['successful_operations'] = 18
        module.success_rates['fast_path_execution']['attempts'] = 10
        module.success_rates['fast_path_execution']['successes'] = 9
        module.operation_metrics['fuzzy_matching_operations']['count'] = 15
        module.operation_metrics['fuzzy_matching_operations']['total_time_ms'] = 300.0
        module.operation_metrics['fuzzy_matching_operations']['success_count'] = 12
        
        summary = module.get_performance_summary()
        
        # Verify summary structure and content
        assert 'overall_performance' in summary
        assert 'success_rates' in summary
        assert 'operation_efficiency' in summary
        assert 'cache_statistics' in summary
        assert 'configuration' in summary
        
        # Verify success rate calculation
        assert summary['success_rates']['fast_path_execution']['success_rate_percent'] == 90.0
        
        # Verify operation efficiency calculation
        fuzzy_efficiency = summary['operation_efficiency']['fuzzy_matching_operations']
        assert fuzzy_efficiency['average_time_ms'] == 20.0  # 300/15
        assert fuzzy_efficiency['success_rate_percent'] == 80.0  # 12/15
    
    def test_performance_summary_empty_data(self, mock_accessibility_module):
        """Test performance summary with no operation data."""
        module = mock_accessibility_module
        
        summary = module.get_performance_summary()
        
        # Should return valid structure even with no data
        assert isinstance(summary, dict)
        assert 'overall_performance' in summary
        assert 'success_rates' in summary
        assert 'operation_efficiency' in summary
        assert 'configuration' in summary
        
        # Success rates should be empty
        assert summary['success_rates'] == {}
        assert summary['operation_efficiency'] == {}
    
    def test_log_message_formatting(self, mock_accessibility_module):
        """Test that log messages are properly formatted and contain expected information."""
        module = mock_accessibility_module
        module.debug_logging = True
        module.log_fuzzy_match_scores = True
        
        # Test various logging methods to ensure proper formatting
        element_info = {'role': 'AXButton', 'title': 'Test Button'}
        
        # Test role check logging
        module._log_element_role_check(element_info, 'AXButton', True, 25.0)
        debug_call = module.debug_logger.debug.call_args[0][0]
        assert isinstance(debug_call, str)
        assert len(debug_call) > 0
        
        # Test attribute examination logging
        module._log_attribute_examination(element_info, 'AXTitle', 'Test Button', True, 15.0)
        debug_call = module.debug_logger.debug.call_args[0][0]
        assert isinstance(debug_call, str)
        assert len(debug_call) > 0
        
        # Test fuzzy matching logging
        module._log_fuzzy_matching_operation('test', 'Test Button', 95.0, True, 30.0)
        info_call = module.operation_logger.info.call_args[0][0]
        assert isinstance(info_call, str)
        assert len(info_call) > 0