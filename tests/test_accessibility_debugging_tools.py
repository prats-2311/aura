"""
Integration tests for AccessibilityModule debugging and diagnostic tools.

Tests the debugging functionality including:
- Verbose logging mode
- Fuzzy match score inspection
- Element attribute inspection
- Element search process logging
- Diagnostic report generation
"""

import pytest
import logging
import time
from unittest.mock import Mock, patch, MagicMock
from modules.accessibility import AccessibilityModule


class TestAccessibilityDebuggingTools:
    """Test suite for debugging and diagnostic tools in AccessibilityModule."""
    
    @pytest.fixture
    def mock_accessibility_module(self):
        """Create a mock AccessibilityModule for testing."""
        with patch('modules.accessibility.ACCESSIBILITY_AVAILABLE', True):
            with patch('modules.accessibility.FUZZY_MATCHING_AVAILABLE', True):
                with patch('modules.accessibility.AXUIElementCreateSystemWide'):
                    with patch('modules.accessibility.NSWorkspace'):
                        module = AccessibilityModule()
                        # Override loggers with mocks for testing
                        module.operation_logger = Mock()
                        module.performance_logger = Mock()
                        module.debug_logger = Mock()
                        module.logger = Mock()
                        return module
    
    def test_enable_verbose_logging(self, mock_accessibility_module):
        """Test enabling verbose logging mode."""
        module = mock_accessibility_module
        
        # Initially should not be in verbose mode
        assert not module.debug_logging
        assert not module.log_fuzzy_match_scores
        
        module.enable_verbose_logging()
        
        # Should now be in verbose mode
        assert module.debug_logging
        assert module.log_fuzzy_match_scores
        
        # Verify logging was called
        module.operation_logger.info.assert_called_once()
        info_call = module.operation_logger.info.call_args[0][0]
        assert "Verbose logging mode enabled" in info_call
        
        # Verify debug configuration was logged
        module.debug_logger.debug.assert_called_once()
        debug_call = module.debug_logger.debug.call_args[0][0]
        assert "Verbose mode configuration" in debug_call
    
    def test_disable_verbose_logging(self, mock_accessibility_module):
        """Test disabling verbose logging mode."""
        module = mock_accessibility_module
        
        # Enable verbose mode first
        module.enable_verbose_logging()
        module.operation_logger.reset_mock()  # Reset mock to clear previous calls
        
        module.disable_verbose_logging()
        
        # Should no longer be in verbose mode
        assert not module.debug_logging
        assert not module.log_fuzzy_match_scores
        
        # Verify logging was called
        module.operation_logger.info.assert_called_once()
        info_call = module.operation_logger.info.call_args[0][0]
        assert "Verbose logging mode disabled" in info_call
    
    @patch('modules.accessibility.fuzz')
    def test_inspect_fuzzy_match_scores(self, mock_fuzz, mock_accessibility_module):
        """Test fuzzy match score inspection."""
        module = mock_accessibility_module
        
        # Mock fuzzy matching results
        mock_fuzz.partial_ratio.side_effect = [95, 75, 60, 85]
        
        target_text = "sign in"
        element_texts = ["Sign In Button", "Login Form", "Register Link", "Sign In"]
        
        results = module.inspect_fuzzy_match_scores(target_text, element_texts)
        
        # Verify results structure
        assert len(results) == 4
        assert all('target_text' in result for result in results)
        assert all('element_text' in result for result in results)
        assert all('confidence_score' in result for result in results)
        assert all('would_match' in result for result in results)
        
        # Verify results are sorted by confidence score (highest first)
        scores = [result['confidence_score'] for result in results]
        assert scores == sorted(scores, reverse=True)
        
        # Verify specific results (sorted by score, so highest first)
        assert results[0]['confidence_score'] == 95
        assert results[0]['would_match'] == True  # Above threshold
        # Find the result with score 60 (should be lowest)
        score_60_result = next(r for r in results if r['confidence_score'] == 60)
        assert score_60_result['would_match'] == False  # Below threshold
        
        # Verify debug logging occurred
        assert module.debug_logger.debug.call_count == 4  # One for each element
        module.debug_logger.info.assert_called_once()
    
    def test_inspect_fuzzy_match_scores_no_library(self, mock_accessibility_module):
        """Test fuzzy match inspection when library is not available."""
        module = mock_accessibility_module
        
        with patch('modules.accessibility.FUZZY_MATCHING_AVAILABLE', False):
            results = module.inspect_fuzzy_match_scores("test", ["test1", "test2"])
            
            # Should return empty list
            assert results == []
            
            # Should log warning
            module.debug_logger.warning.assert_called_once()
            warning_call = module.debug_logger.warning.call_args[0][0]
            assert "Fuzzy matching library not available" in warning_call
    
    @patch('modules.accessibility.fuzz')
    def test_inspect_fuzzy_match_scores_with_error(self, mock_fuzz, mock_accessibility_module):
        """Test fuzzy match inspection with errors."""
        module = mock_accessibility_module
        
        # Mock fuzzy matching to raise an error for one element
        mock_fuzz.partial_ratio.side_effect = [85, Exception("Fuzzy match error"), 75]
        
        target_text = "test"
        element_texts = ["test1", "error_element", "test3"]
        
        results = module.inspect_fuzzy_match_scores(target_text, element_texts)
        
        # Should still return results for all elements
        assert len(results) == 3
        
        # Error element should have error information
        error_result = next(r for r in results if r['element_text'] == 'error_element')
        assert 'error' in error_result
        assert error_result['confidence_score'] == 0
        assert error_result['would_match'] == False
        
        # Verify error logging
        module.debug_logger.error.assert_called_once()
    
    def test_inspect_element_attributes(self, mock_accessibility_module):
        """Test element attribute inspection."""
        module = mock_accessibility_module
        
        # Mock element with various attributes
        element_info = {
            'AXTitle': 'Test Button',
            'AXDescription': 'A test button',
            'AXValue': None,
            'role': 'AXButton',
            'title': 'Alternative Title'
        }
        
        result = module.inspect_element_attributes(element_info)
        
        # Verify result structure
        assert 'element_info' in result
        assert 'attributes' in result
        assert 'attribute_access_times' in result
        assert 'attribute_errors' in result
        assert 'total_attributes_checked' in result
        assert 'successful_attributes' in result
        assert 'failed_attributes' in result
        assert 'attribute_success_rate' in result
        
        # Verify attributes were found
        assert result['attributes']['AXTitle'] == 'Test Button'
        assert result['attributes']['AXDescription'] == 'A test button'
        assert result['attributes']['AXValue'] is None
        
        # Verify alternative attributes were found
        assert 'alt_role' in result['attributes']
        assert 'alt_title' in result['attributes']
        
        # Verify success rate calculation
        assert result['attribute_success_rate'] > 0
        
        # Verify logging occurred
        assert module.debug_logger.debug.call_count > 0
        module.debug_logger.info.assert_called_once()
    
    def test_inspect_element_attributes_with_errors(self, mock_accessibility_module):
        """Test element attribute inspection with access errors."""
        module = mock_accessibility_module
        
        # Mock element that raises errors for some attributes
        class ErrorElement:
            def get(self, key):
                if key == 'AXTitle':
                    return 'Working Title'
                elif key == 'AXDescription':
                    raise Exception("Access denied")
                else:
                    return None
        
        element_info = ErrorElement()
        
        result = module.inspect_element_attributes(element_info)
        
        # Should handle errors gracefully
        assert 'attribute_errors' in result
        assert len(result['attribute_errors']) > 0
        assert result['failed_attributes'] > 0
        
        # Should still have some successful attributes
        assert result['successful_attributes'] > 0
        
        # Verify error logging
        assert module.debug_logger.error.call_count > 0
    
    def test_log_element_search_process(self, mock_accessibility_module):
        """Test element search process logging."""
        module = mock_accessibility_module
        
        target_text = "submit button"
        role_filter = "AXButton"
        app_name = "TestApp"
        
        search_log = module.log_element_search_process(target_text, role_filter, app_name)
        
        # Verify search log structure
        assert 'search_parameters' in search_log
        assert 'search_steps' in search_log
        assert 'performance_metrics' in search_log
        assert 'cache_operations' in search_log
        assert 'errors_encountered' in search_log
        assert 'final_result' in search_log
        assert 'configuration_used' in search_log
        assert 'cache_state' in search_log
        
        # Verify search parameters
        params = search_log['search_parameters']
        assert params['target_text'] == target_text
        assert params['role_filter'] == role_filter
        assert params['app_name'] == app_name
        assert 'timestamp' in params
        
        # Verify configuration was logged
        config = search_log['configuration_used']
        assert 'fuzzy_matching_enabled' in config
        assert 'clickable_roles' in config
        
        # Verify cache state was logged
        cache_state = search_log['cache_state']
        assert 'cache_entries' in cache_state
        assert 'cache_stats' in cache_state
        
        # Verify logging occurred
        module.debug_logger.info.assert_called_once()
        module.debug_logger.debug.assert_called()
    
    def test_log_search_step(self, mock_accessibility_module):
        """Test logging individual search steps."""
        module = mock_accessibility_module
        
        # Create initial search log
        search_log = {
            'search_steps': [],
            'search_parameters': {'target_text': 'test'}
        }
        
        step_name = "role_check"
        step_data = {'roles_checked': ['AXButton', 'AXLink'], 'matches_found': 2}
        duration_ms = 25.5
        
        module.log_search_step(search_log, step_name, step_data, duration_ms)
        
        # Verify step was added to log
        assert len(search_log['search_steps']) == 1
        
        step = search_log['search_steps'][0]
        assert step['step_name'] == step_name
        assert step['step_data'] == step_data
        assert step['duration_ms'] == 25.5
        assert 'timestamp' in step
        
        # Verify debug logging
        module.debug_logger.debug.assert_called_once()
        debug_call = module.debug_logger.debug.call_args[0][0]
        assert "Search step 'role_check'" in debug_call
    
    def test_finalize_search_log(self, mock_accessibility_module):
        """Test finalizing search log with results."""
        module = mock_accessibility_module
        
        # Create search log with some steps
        search_log = {
            'search_parameters': {'target_text': 'test button'},
            'search_steps': [
                {'step_name': 'role_check', 'duration_ms': 10.0},
                {'step_name': 'fuzzy_match', 'duration_ms': 25.0},
                {'step_name': 'role_check', 'duration_ms': 15.0}  # Duplicate step name
            ],
            'final_result': None
        }
        
        final_result = {'element': 'found', 'coordinates': [100, 200]}
        total_duration_ms = 150.5
        success = True
        
        result_log = module.finalize_search_log(search_log, final_result, total_duration_ms, success)
        
        # Verify finalization
        assert result_log['final_result'] == final_result
        assert result_log['total_duration_ms'] == 150.5
        assert result_log['success'] == success
        assert result_log['steps_count'] == 3
        
        # Verify step timing breakdown
        breakdown = result_log['step_timing_breakdown']
        assert breakdown['role_check'] == 25.0  # 10.0 + 15.0
        assert breakdown['fuzzy_match'] == 25.0
        
        # Verify success logging
        module.debug_logger.info.assert_called_once()
        info_call = module.debug_logger.info.call_args[0][0]
        assert "Element search completed successfully" in info_call
    
    def test_finalize_search_log_failure(self, mock_accessibility_module):
        """Test finalizing search log with failure."""
        module = mock_accessibility_module
        
        search_log = {
            'search_parameters': {'target_text': 'missing button'},
            'search_steps': [{'step_name': 'role_check', 'duration_ms': 30.0}],
            'final_result': None
        }
        
        final_result = None
        total_duration_ms = 75.2
        success = False
        
        result_log = module.finalize_search_log(search_log, final_result, total_duration_ms, success)
        
        # Verify failure logging
        module.debug_logger.warning.assert_called_once()
        warning_call = module.debug_logger.warning.call_args[0][0]
        assert "Element search failed" in warning_call
    
    def test_create_diagnostic_report(self, mock_accessibility_module):
        """Test creating comprehensive diagnostic report."""
        module = mock_accessibility_module
        
        # Set up some test data
        module.accessibility_enabled = True
        module.degraded_mode = False
        module.error_count = 2
        module.recovery_attempts = 1
        module.performance_stats['total_operations'] = 50
        module.performance_stats['successful_operations'] = 45
        module.performance_stats['performance_warnings'] = 3
        module.success_rates['fast_path_execution']['attempts'] = 20
        module.success_rates['fast_path_execution']['successes'] = 18
        module.cache_stats['hits'] = 30
        module.cache_stats['misses'] = 10
        
        report = module.create_diagnostic_report()
        
        # Verify report structure
        assert 'timestamp' in report
        assert 'system_status' in report
        assert 'configuration' in report
        assert 'performance_metrics' in report
        assert 'cache_status' in report
        assert 'recent_operations' in report
        assert 'recommendations' in report
        
        # Verify system status
        system_status = report['system_status']
        assert system_status['accessibility_enabled'] == True
        assert system_status['degraded_mode'] == False
        assert system_status['error_count'] == 2
        
        # Verify configuration
        config = report['configuration']
        assert 'fuzzy_matching_enabled' in config
        assert 'clickable_roles' in config
        
        # Verify recommendations are generated
        recommendations = report['recommendations']
        assert isinstance(recommendations, list)
        
        # Verify logging
        module.debug_logger.info.assert_called_once()
    
    def test_create_diagnostic_report_with_issues(self, mock_accessibility_module):
        """Test diagnostic report generation with various issues."""
        module = mock_accessibility_module
        
        # Set up problematic state
        module.degraded_mode = True
        module.fuzzy_matching_enabled = True
        module.performance_stats['performance_warnings'] = 10
        module.success_rates['element_detection']['attempts'] = 20
        module.success_rates['element_detection']['successes'] = 10  # 50% success rate
        module.cache_stats['hits'] = 5
        module.cache_stats['misses'] = 20  # 20% hit rate
        
        with patch('modules.accessibility.FUZZY_MATCHING_AVAILABLE', False):
            report = module.create_diagnostic_report()
        
        recommendations = report['recommendations']
        
        # Should have multiple recommendations
        assert len(recommendations) > 0
        
        # Check for specific recommendations
        rec_text = ' '.join(recommendations)
        assert "degraded mode" in rec_text
        assert "fuzzy matching" in rec_text or "library" in rec_text
        assert "Performance warnings detected" in rec_text  # Exact text from the code
        assert "success rate" in rec_text
        assert "cache hit rate" in rec_text
    
    def test_print_diagnostic_report(self, mock_accessibility_module, capsys):
        """Test printing diagnostic report to console."""
        module = mock_accessibility_module
        
        # Set up some test data
        module.accessibility_enabled = True
        module.degraded_mode = False
        module.performance_stats['total_operations'] = 10
        module.performance_stats['successful_operations'] = 9
        module.performance_stats['average_duration_ms'] = 125.5
        module.performance_stats['performance_warnings'] = 1
        
        module.print_diagnostic_report()
        
        # Capture printed output
        captured = capsys.readouterr()
        output = captured.out
        
        # Verify report sections are present
        assert "ACCESSIBILITY MODULE DIAGNOSTIC REPORT" in output
        assert "SYSTEM STATUS" in output
        assert "CONFIGURATION" in output
        assert "PERFORMANCE METRICS" in output
        assert "CACHE STATUS" in output
        assert "RECOMMENDATIONS" in output
        assert "END OF DIAGNOSTIC REPORT" in output
        
        # Verify specific content
        assert "Accessibility Enabled: ✅" in output
        assert "Degraded Mode: ✅ NO" in output
        assert "Total Operations: 10" in output
        assert "Success Rate: 90.0%" in output
        assert "Average Duration: 125.5ms" in output
    
    def test_print_diagnostic_report_no_operations(self, mock_accessibility_module, capsys):
        """Test printing diagnostic report with no operations recorded."""
        module = mock_accessibility_module
        
        # Ensure no operations recorded
        module.performance_stats['total_operations'] = 0
        
        module.print_diagnostic_report()
        
        captured = capsys.readouterr()
        output = captured.out
        
        # Should handle no operations gracefully
        assert "No operations recorded yet" in output
    
    def test_print_diagnostic_report_with_issues(self, mock_accessibility_module, capsys):
        """Test printing diagnostic report with issues detected."""
        module = mock_accessibility_module
        
        # Set up problematic state
        module.accessibility_enabled = False
        module.degraded_mode = True
        
        module.print_diagnostic_report()
        
        captured = capsys.readouterr()
        output = captured.out
        
        # Should show issues
        assert "Accessibility Enabled: ❌" in output
        assert "Degraded Mode: ⚠️ YES" in output
        
        # Should have recommendations
        assert "1." in output  # At least one recommendation
    
    def test_print_diagnostic_report_optimal_state(self, mock_accessibility_module, capsys):
        """Test printing diagnostic report in optimal state."""
        module = mock_accessibility_module
        
        # Set up optimal state
        module.accessibility_enabled = True
        module.degraded_mode = False
        module.error_count = 0
        module.recovery_attempts = 0
        
        # Mock create_diagnostic_report to return no recommendations
        with patch.object(module, 'create_diagnostic_report') as mock_create:
            mock_create.return_value = {
                'timestamp': time.time(),
                'system_status': {
                    'accessibility_enabled': True,
                    'degraded_mode': False,
                    'fuzzy_matching_available': True,
                    'error_count': 0,
                    'recovery_attempts': 0
                },
                'configuration': {
                    'fuzzy_matching_enabled': True,
                    'fuzzy_confidence_threshold': 85,
                    'fast_path_timeout_ms': 2000,
                    'debug_logging': False,
                    'clickable_roles': ['AXButton']
                },
                'performance_metrics': {
                    'overall_performance': {'total_operations': 0}
                },
                'cache_status': {
                    'element_cache_entries': 0,
                    'fuzzy_match_cache_entries': 0,
                    'cache_statistics': {'total_lookups': 0}
                },
                'recommendations': []
            }
            
            module.print_diagnostic_report()
        
        captured = capsys.readouterr()
        output = captured.out
        
        # Should show optimal message
        assert "No issues detected - system appears to be functioning optimally" in output