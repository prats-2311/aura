"""
Integration tests for enhanced fast path orchestrator integration.

Tests the integration between the orchestrator and enhanced accessibility module
for improved fast path execution with comprehensive result tracking.
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from dataclasses import dataclass
from typing import Dict, Any, Optional, List

from orchestrator import Orchestrator
from modules.accessibility import AccessibilityModule, ElementMatchResult
from modules.performance import PerformanceMetrics


@dataclass
class MockElementMatchResult:
    """Mock ElementMatchResult for testing."""
    element: Optional[Dict[str, Any]]
    found: bool
    confidence_score: float
    matched_attribute: str
    search_time_ms: float
    roles_checked: List[str]
    attributes_checked: List[str]
    fuzzy_matches: List[Dict[str, Any]]
    fallback_triggered: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging and debugging."""
        return {
            'found': self.found,
            'confidence_score': self.confidence_score,
            'matched_attribute': self.matched_attribute,
            'search_time_ms': self.search_time_ms,
            'roles_checked': self.roles_checked,
            'attributes_checked': self.attributes_checked,
            'fuzzy_match_count': len(self.fuzzy_matches),
            'fallback_triggered': self.fallback_triggered
        }


class TestEnhancedOrchestratorIntegration:
    """Test enhanced fast path orchestrator integration."""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator with mocked modules for testing."""
        with patch('orchestrator.VisionModule'), \
             patch('orchestrator.ReasoningModule'), \
             patch('orchestrator.AutomationModule'), \
             patch('orchestrator.AudioModule'), \
             patch('orchestrator.FeedbackModule'), \
             patch('orchestrator.AccessibilityModule'):
            
            orchestrator = Orchestrator()
            
            # Mock accessibility module with enhanced functionality
            orchestrator.accessibility_module = Mock(spec=AccessibilityModule)
            orchestrator.accessibility_module.get_accessibility_status.return_value = {
                'api_initialized': True,
                'degraded_mode': False
            }
            
            # Mock target extraction caching methods to return None (no cache hit)
            orchestrator.accessibility_module._get_cached_target_extraction = Mock(return_value=None)
            orchestrator.accessibility_module._cache_target_extraction_result = Mock(return_value=None)
            
            # Mock automation module
            orchestrator.automation_module = Mock()
            orchestrator.automation_module.execute_fast_path_action.return_value = {
                'success': True,
                'message': 'Action executed successfully'
            }
            
            # Enable fast path
            orchestrator.fast_path_enabled = True
            orchestrator.module_availability['accessibility'] = True
            orchestrator.module_availability['automation'] = True
            
            return orchestrator

    def test_enhanced_fast_path_execution_success(self, orchestrator):
        """Test successful enhanced fast path execution."""
        # Mock enhanced element finding
        mock_element = {
            'role': 'AXButton',
            'title': 'Submit',
            'center_point': (100, 200),
            'app_name': 'Safari'
        }
        
        mock_enhanced_result = MockElementMatchResult(
            element=mock_element,
            found=True,
            confidence_score=0.95,
            matched_attribute='AXTitle',
            search_time_ms=150.0,
            roles_checked=['AXButton', 'AXLink'],
            attributes_checked=['AXTitle', 'AXDescription'],
            fuzzy_matches=[{'text': 'Submit', 'score': 95}],
            fallback_triggered=False
        )
        
        orchestrator.accessibility_module.find_element_enhanced.return_value = mock_enhanced_result
        
        # Test command
        command = "Click on the Submit button"
        command_info = {'command_type': 'click', 'confidence': 0.9}
        
        # Execute fast path
        result = orchestrator._attempt_fast_path_execution(command, command_info)
        
        # Verify success
        assert result is not None
        assert result['success'] is True
        assert result['path_used'] == 'enhanced_fast'
        assert result['element_found'] == mock_element
        assert 'enhanced_search_result' in result
        assert result['enhanced_search_result']['found'] is True
        assert result['enhanced_search_result']['confidence_score'] == 0.95
        
        # Verify enhanced element finding was called correctly
        orchestrator.accessibility_module.find_element_enhanced.assert_called_once()
        call_args = orchestrator.accessibility_module.find_element_enhanced.call_args
        assert call_args[1]['role'] == ''  # Empty role for broader search
        assert 'submit button' in call_args[1]['label'].lower()
        
        # Verify automation was called
        orchestrator.automation_module.execute_fast_path_action.assert_called_once()

    def test_enhanced_fast_path_element_not_found(self, orchestrator):
        """Test enhanced fast path when element is not found."""
        # Mock enhanced element finding - element not found
        mock_enhanced_result = MockElementMatchResult(
            element=None,
            found=False,
            confidence_score=0.0,
            matched_attribute='',
            search_time_ms=200.0,
            roles_checked=['AXButton', 'AXLink', 'AXMenuItem'],
            attributes_checked=['AXTitle', 'AXDescription', 'AXValue'],
            fuzzy_matches=[],
            fallback_triggered=True
        )
        
        orchestrator.accessibility_module.find_element_enhanced.return_value = mock_enhanced_result
        
        # Test command
        command = "Click on the NonExistent button"
        command_info = {'command_type': 'click', 'confidence': 0.9}
        
        # Execute fast path
        result = orchestrator._attempt_fast_path_execution(command, command_info)
        
        # Verify failure with enhanced details
        assert result is not None
        assert result['success'] is False
        assert result['failure_reason'] == 'element_not_found'
        assert 'enhanced_search_details' in result['context']
        assert result['context']['enhanced_search_details']['found'] is False
        assert result['context']['enhanced_search_details']['roles_checked'] == ['AXButton', 'AXLink', 'AXMenuItem']
        
        # Verify automation was not called
        orchestrator.automation_module.execute_fast_path_action.assert_not_called()

    def test_enhanced_fast_path_performance_monitoring(self, orchestrator):
        """Test performance monitoring for enhanced fast path execution."""
        # Mock enhanced element finding
        mock_element = {
            'role': 'AXLink',
            'title': 'Gmail',
            'center_point': (150, 300),
            'app_name': 'Chrome'
        }
        
        mock_enhanced_result = MockElementMatchResult(
            element=mock_element,
            found=True,
            confidence_score=0.87,
            matched_attribute='AXDescription',
            search_time_ms=180.0,
            roles_checked=['AXButton', 'AXLink'],
            attributes_checked=['AXTitle', 'AXDescription'],
            fuzzy_matches=[{'text': 'Google Mail', 'score': 87}],
            fallback_triggered=False
        )
        
        orchestrator.accessibility_module.find_element_enhanced.return_value = mock_enhanced_result
        
        # Mock performance monitor
        with patch('orchestrator.performance_monitor') as mock_performance_monitor:
            # Test command
            command = "Click on the Gmail link"
            command_info = {'command_type': 'click', 'confidence': 0.9}
            
            # Execute fast path
            result = orchestrator._attempt_fast_path_execution(command, command_info)
            
            # Verify success
            assert result['success'] is True
            
            # Verify performance metrics were recorded
            assert mock_performance_monitor.record_metric.call_count >= 2  # Element search + execution success
            
            # Check element search metrics
            search_metric_call = None
            execution_metric_call = None
            
            for call in mock_performance_monitor.record_metric.call_args_list:
                metric = call[0][0]
                if metric.operation == "enhanced_fast_path_element_search":
                    search_metric_call = metric
                elif metric.operation == "enhanced_fast_path_execution_success":
                    execution_metric_call = metric
            
            # Verify element search metrics
            assert search_metric_call is not None
            assert search_metric_call.success is True
            assert search_metric_call.metadata['confidence_score'] == 0.87
            assert search_metric_call.metadata['matched_attribute'] == 'AXDescription'
            assert search_metric_call.metadata['roles_checked_count'] == 2
            assert search_metric_call.metadata['attributes_checked_count'] == 2
            assert search_metric_call.metadata['fuzzy_matches_count'] == 1
            
            # Verify execution success metrics
            assert execution_metric_call is not None
            assert execution_metric_call.success is True
            assert execution_metric_call.metadata['enhanced_search_confidence'] == 0.87
            assert execution_metric_call.metadata['matched_attribute'] == 'AXDescription'

    def test_enhanced_fast_path_with_fuzzy_matching(self, orchestrator):
        """Test enhanced fast path with fuzzy matching results."""
        # Mock enhanced element finding with fuzzy matching
        mock_element = {
            'role': 'AXButton',
            'title': 'Sign-In',
            'center_point': (200, 100),
            'app_name': 'Safari'
        }
        
        mock_enhanced_result = MockElementMatchResult(
            element=mock_element,
            found=True,
            confidence_score=0.89,
            matched_attribute='AXTitle',
            search_time_ms=220.0,
            roles_checked=['AXButton'],
            attributes_checked=['AXTitle'],
            fuzzy_matches=[
                {'text': 'Sign-In', 'score': 89, 'attribute': 'AXTitle'},
                {'text': 'Sign In Button', 'score': 75, 'attribute': 'AXDescription'}
            ],
            fallback_triggered=False
        )
        
        orchestrator.accessibility_module.find_element_enhanced.return_value = mock_enhanced_result
        
        # Test command with slight variation
        command = "Click on the Sign In button"
        command_info = {'command_type': 'click', 'confidence': 0.9}
        
        # Execute fast path
        result = orchestrator._attempt_fast_path_execution(command, command_info)
        
        # Verify success with fuzzy matching
        assert result['success'] is True
        assert result['enhanced_search_result']['fuzzy_match_count'] == 2
        assert result['enhanced_search_result']['confidence_score'] == 0.89
        assert result['enhanced_search_result']['matched_attribute'] == 'AXTitle'

    def test_enhanced_fast_path_with_fallback_triggered(self, orchestrator):
        """Test enhanced fast path when fallback is triggered."""
        # Mock enhanced element finding with fallback
        mock_element = {
            'role': 'AXButton',
            'title': 'OK',
            'center_point': (250, 150),
            'app_name': 'Dialog'
        }
        
        mock_enhanced_result = MockElementMatchResult(
            element=mock_element,
            found=True,
            confidence_score=0.70,
            matched_attribute='AXTitle',
            search_time_ms=300.0,
            roles_checked=['AXButton'],
            attributes_checked=['AXTitle'],
            fuzzy_matches=[],
            fallback_triggered=True  # Fallback was used
        )
        
        orchestrator.accessibility_module.find_element_enhanced.return_value = mock_enhanced_result
        
        # Test command
        command = "Click OK"
        command_info = {'command_type': 'click', 'confidence': 0.9}
        
        # Execute fast path
        result = orchestrator._attempt_fast_path_execution(command, command_info)
        
        # Verify success with fallback information
        assert result['success'] is True
        assert result['enhanced_search_result']['fallback_triggered'] is True
        assert result['enhanced_search_result']['confidence_score'] == 0.70

    def test_enhanced_fast_path_error_handling(self, orchestrator):
        """Test error handling in enhanced fast path execution."""
        # Mock enhanced element finding to raise an exception
        orchestrator.accessibility_module.find_element_enhanced.side_effect = Exception("Enhanced search failed")
        
        # Test command
        command = "Click on the Submit button"
        command_info = {'command_type': 'click', 'confidence': 0.9}
        
        # Execute fast path
        result = orchestrator._attempt_fast_path_execution(command, command_info)
        
        # Verify failure handling
        assert result is not None
        assert result['success'] is False
        assert result['failure_reason'] == 'execution_error'
        assert 'error' in result['context']
        assert 'Enhanced search failed' in result['context']['error']

    def test_enhanced_fast_path_retry_logic(self, orchestrator):
        """Test retry logic with enhanced fast path."""
        # Mock enhanced element finding to fail first, then succeed
        mock_element = {
            'role': 'AXButton',
            'title': 'Retry',
            'center_point': (300, 200),
            'app_name': 'App'
        }
        
        mock_enhanced_result = MockElementMatchResult(
            element=mock_element,
            found=True,
            confidence_score=0.85,
            matched_attribute='AXTitle',
            search_time_ms=100.0,
            roles_checked=['AXButton'],
            attributes_checked=['AXTitle'],
            fuzzy_matches=[],
            fallback_triggered=False
        )
        
        # Mock automation to fail first time, succeed second time
        orchestrator.accessibility_module.find_element_enhanced.return_value = mock_enhanced_result
        orchestrator.automation_module.execute_fast_path_action.side_effect = [
            {'success': False, 'error': 'Temporary automation failure'},
            {'success': True, 'message': 'Action executed successfully'}
        ]
        
        # Test command
        command = "Click on the Retry button"
        command_info = {'command_type': 'click', 'confidence': 0.9}
        
        # Execute fast path
        result = orchestrator._attempt_fast_path_execution(command, command_info)
        
        # Verify eventual success after retry
        assert result['success'] is True
        assert result['attempts'] == 2
        assert result['retry_used'] is True

    def test_enhanced_fast_path_target_extraction_integration(self, orchestrator):
        """Test integration with enhanced target extraction."""
        # Mock enhanced element finding
        mock_element = {
            'role': 'AXLink',
            'title': 'Gmail',
            'center_point': (400, 250),
            'app_name': 'Browser'
        }
        
        mock_enhanced_result = MockElementMatchResult(
            element=mock_element,
            found=True,
            confidence_score=0.92,
            matched_attribute='AXTitle',
            search_time_ms=120.0,
            roles_checked=['AXButton', 'AXLink'],
            attributes_checked=['AXTitle'],
            fuzzy_matches=[{'text': 'Gmail', 'score': 92}],
            fallback_triggered=False
        )
        
        orchestrator.accessibility_module.find_element_enhanced.return_value = mock_enhanced_result
        
        # Test command with articles and action words
        command = "Click on the Gmail link"
        command_info = {'command_type': 'click', 'confidence': 0.9}
        
        # Execute fast path
        result = orchestrator._attempt_fast_path_execution(command, command_info)
        
        # Verify success
        assert result['success'] is True
        
        # Verify that target extraction was used (empty role, cleaned label)
        call_args = orchestrator.accessibility_module.find_element_enhanced.call_args
        assert call_args[1]['role'] == ''  # Empty role for broader search
        # The label should be the extracted target (without "click on the")
        assert 'gmail' in call_args[1]['label'].lower()
        assert 'click' not in call_args[1]['label'].lower()
        assert 'the' not in call_args[1]['label'].lower()

    def test_enhanced_fast_path_performance_timeout_handling(self, orchestrator):
        """Test performance timeout handling in enhanced fast path."""
        # Mock enhanced element finding with long search time
        mock_element = {
            'role': 'AXButton',
            'title': 'Slow',
            'center_point': (500, 300),
            'app_name': 'SlowApp'
        }
        
        mock_enhanced_result = MockElementMatchResult(
            element=mock_element,
            found=True,
            confidence_score=0.80,
            matched_attribute='AXTitle',
            search_time_ms=2500.0,  # Exceeds typical timeout
            roles_checked=['AXButton'],
            attributes_checked=['AXTitle'],
            fuzzy_matches=[],
            fallback_triggered=False
        )
        
        orchestrator.accessibility_module.find_element_enhanced.return_value = mock_enhanced_result
        
        # Mock performance monitor to capture metrics
        with patch('orchestrator.performance_monitor') as mock_performance_monitor:
            # Test command
            command = "Click on the Slow button"
            command_info = {'command_type': 'click', 'confidence': 0.9}
            
            # Execute fast path
            result = orchestrator._attempt_fast_path_execution(command, command_info)
            
            # Verify success despite slow search
            assert result['success'] is True
            
            # Verify performance metrics include timing information
            search_metric_call = None
            for call in mock_performance_monitor.record_metric.call_args_list:
                metric = call[0][0]
                if metric.operation == "enhanced_fast_path_element_search":
                    search_metric_call = metric
                    break
            
            assert search_metric_call is not None
            # The search time is recorded in the duration field (converted from ms to seconds)
            assert search_metric_call.duration == 2.5  # 2500ms converted to seconds
            assert search_metric_call.metadata['confidence_score'] == 0.80

    def test_enhanced_fallback_coordination(self, orchestrator):
        """Test enhanced fallback coordination between fast path and vision."""
        # Mock enhanced element finding to fail
        mock_enhanced_result = MockElementMatchResult(
            element=None,
            found=False,
            confidence_score=0.0,
            matched_attribute='',
            search_time_ms=150.0,
            roles_checked=['AXButton', 'AXLink'],
            attributes_checked=['AXTitle', 'AXDescription'],
            fuzzy_matches=[],
            fallback_triggered=True
        )
        
        orchestrator.accessibility_module.find_element_enhanced.return_value = mock_enhanced_result
        
        # Mock the fallback handling method to capture the call
        with patch.object(orchestrator, '_handle_fast_path_fallback') as mock_fallback:
            # Test command
            command = "Click on the NonExistent button"
            command_info = {'command_type': 'click', 'confidence': 0.9}
            
            # Execute fast path (should fail and trigger fallback)
            result = orchestrator._attempt_fast_path_execution(command, command_info)
            
            # Verify fast path failed
            assert result['success'] is False
            assert result['failure_reason'] == 'element_not_found'
            
            # Verify fallback would be called in the main execution flow
            # (We can't test the actual fallback here without mocking the entire vision workflow)
            assert 'enhanced_search_details' in result['context']

    def test_enhanced_fallback_performance_comparison_logging(self, orchestrator):
        """Test performance comparison logging between enhanced fast path and vision fallback."""
        # Create execution context as if fast path failed
        execution_context = {
            'execution_id': 'test_123',
            'fast_path_attempted': True,
            'enhanced_fast_path_used': True,
            'fast_path_execution_time': 0.5,
            'fallback_reason': 'element_not_found',
            'fast_path_result': {
                'enhanced_search_result': {
                    'confidence_score': 0.75,
                    'roles_checked': ['AXButton', 'AXLink'],
                    'attributes_checked': ['AXTitle', 'AXDescription'],
                    'fuzzy_match_count': 2,
                    'fallback_triggered': True
                }
            }
        }
        
        # Mock performance monitor to capture metrics
        with patch('orchestrator.performance_monitor') as mock_performance_monitor:
            # Call performance comparison logging
            orchestrator._log_fallback_performance_comparison(
                'test_123', 
                execution_context, 
                2.5  # Vision execution time
            )
            
            # Verify performance comparison metric was recorded
            mock_performance_monitor.record_metric.assert_called_once()
            metric = mock_performance_monitor.record_metric.call_args[0][0]
            
            assert metric.operation == "enhanced_fast_path_vs_vision_comparison"
            assert metric.duration == 2.5
            assert metric.metadata['fast_path_time'] == 0.5
            assert metric.metadata['vision_time'] == 2.5
            assert metric.metadata['time_difference'] == 2.0
            assert metric.metadata['performance_ratio'] == 5.0
            assert metric.metadata['fallback_reason'] == 'element_not_found'
            assert metric.metadata['enhanced_search_confidence'] == 0.75
            assert metric.metadata['enhanced_search_roles_checked'] == 2
            assert metric.metadata['enhanced_search_attributes_checked'] == 2
            assert metric.metadata['enhanced_search_fuzzy_matches'] == 2
            assert metric.metadata['enhanced_search_fallback_triggered'] is True

    def test_enhanced_fallback_configuration_options(self, orchestrator):
        """Test that enhanced fallback respects configuration options."""
        # Test that configuration options are imported and accessible
        from config import (
            ENHANCED_FALLBACK_ENABLED,
            FALLBACK_PERFORMANCE_LOGGING,
            FALLBACK_RETRY_DELAY,
            MAX_FALLBACK_RETRIES,
            FALLBACK_TIMEOUT_THRESHOLD
        )
        
        # Verify configuration options exist and have reasonable defaults
        assert isinstance(ENHANCED_FALLBACK_ENABLED, bool)
        assert isinstance(FALLBACK_PERFORMANCE_LOGGING, bool)
        assert isinstance(FALLBACK_RETRY_DELAY, (int, float))
        assert isinstance(MAX_FALLBACK_RETRIES, int)
        assert isinstance(FALLBACK_TIMEOUT_THRESHOLD, (int, float))
        
        # Verify reasonable ranges
        assert 0.1 <= FALLBACK_RETRY_DELAY <= 5.0
        assert 0 <= MAX_FALLBACK_RETRIES <= 5
        assert 1.0 <= FALLBACK_TIMEOUT_THRESHOLD <= 10.0

    def test_enhanced_fallback_handles_missing_enhanced_result(self, orchestrator):
        """Test fallback handling when enhanced result is missing or malformed."""
        # Create execution context with minimal fast path result
        execution_context = {
            'execution_id': 'test_456',
            'fast_path_attempted': True,
            'enhanced_fast_path_used': True,
            'fast_path_execution_time': 0.3,
            'fallback_reason': 'execution_error',
            'fast_path_result': {}  # Missing enhanced_search_result
        }
        
        # Mock performance monitor
        with patch('orchestrator.performance_monitor') as mock_performance_monitor:
            # Should not crash even with missing enhanced result
            orchestrator._log_fallback_performance_comparison(
                'test_456', 
                execution_context, 
                1.8
            )
            
            # Verify metric was still recorded with default values
            mock_performance_monitor.record_metric.assert_called_once()
            metric = mock_performance_monitor.record_metric.call_args[0][0]
            
            assert metric.metadata['enhanced_search_confidence'] == 0
            assert metric.metadata['enhanced_search_roles_checked'] == 0
            assert metric.metadata['enhanced_search_attributes_checked'] == 0
            assert metric.metadata['enhanced_search_fuzzy_matches'] == 0
            assert metric.metadata['enhanced_search_fallback_triggered'] is False

    def test_enhanced_fallback_disabled_performance_logging(self, orchestrator):
        """Test that performance logging can be disabled via configuration."""
        execution_context = {
            'execution_id': 'test_789',
            'fast_path_attempted': True,
            'enhanced_fast_path_used': True,
            'fast_path_execution_time': 0.4,
            'fallback_reason': 'element_not_found'
        }
        
        # Mock the configuration to disable performance logging
        with patch('orchestrator.FALLBACK_PERFORMANCE_LOGGING', False):
            with patch('orchestrator.performance_monitor') as mock_performance_monitor:
                # Call performance comparison logging
                orchestrator._log_fallback_performance_comparison(
                    'test_789', 
                    execution_context, 
                    2.0
                )
                
                # Verify no metrics were recorded when logging is disabled
                mock_performance_monitor.record_metric.assert_not_called()