"""
Integration tests for Orchestrator with debugging capabilities enabled.

Tests the integration of debugging tools with the orchestrator fast path execution,
including diagnostic tool integration, error recovery, and performance monitoring.
"""

import pytest
import unittest.mock as mock
import time
from unittest.mock import MagicMock, patch, call
from dataclasses import dataclass
from typing import Dict, Any, Optional, List

# Import the modules to test
from orchestrator import Orchestrator, CommandStatus, ExecutionStep
from modules.accessibility import ElementMatchResult


@dataclass
class MockDiagnosticResult:
    """Mock diagnostic result for testing."""
    issues: List[str] = None
    recommendations: List[str] = None
    performance_insights: str = ""
    optimization_suggestions: List[str] = None
    
    def __post_init__(self):
        if self.issues is None:
            self.issues = ["Accessibility permissions may be insufficient", "Element detection timeout"]
        if self.recommendations is None:
            self.recommendations = [
                "Check accessibility permissions in System Preferences",
                "Verify the target application is in focus"
            ]
        if self.optimization_suggestions is None:
            self.optimization_suggestions = [
                "Consider using more specific element selectors",
                "Optimize fuzzy matching thresholds"
            ]


@dataclass
class MockRecoveryResult:
    """Mock recovery result for testing."""
    should_retry: bool = True
    actions_taken: List[str] = None
    success: bool = True
    
    def __post_init__(self):
        if self.actions_taken is None:
            self.actions_taken = ["retry_with_backoff", "refresh_accessibility_tree"]


class TestOrchestratorDebuggingIntegration:
    """Test suite for orchestrator debugging integration."""
    
    @pytest.fixture
    def mock_diagnostic_tools(self):
        """Mock diagnostic tools for testing."""
        tools = MagicMock()
        tools.run_quick_accessibility_check.return_value = {
            'issues': ['Accessibility API not initialized'],
            'status': 'degraded'
        }
        tools.run_targeted_diagnostics.return_value = MockDiagnosticResult().__dict__
        tools.analyze_performance_comparison.return_value = {
            'insights': 'Fast path failed due to element detection timeout',
            'optimization_suggestions': [
                'Increase timeout threshold',
                'Use more specific element attributes'
            ]
        }
        return tools
    
    @pytest.fixture
    def mock_error_recovery_manager(self):
        """Mock error recovery manager for testing."""
        manager = MagicMock()
        manager.attempt_recovery.return_value = MockRecoveryResult().__dict__
        return manager
    
    @pytest.fixture
    def mock_accessibility_module(self):
        """Mock accessibility module for testing."""
        module = MagicMock()
        module.find_element_enhanced.return_value = ElementMatchResult(
            element=None,
            found=False,
            confidence_score=0.0,
            matched_attribute='',
            search_time_ms=150.0,
            roles_checked=['AXButton'],
            attributes_checked=['AXTitle'],
            fuzzy_matches=[],
            fallback_triggered=True
        )
        module.get_accessibility_status.return_value = {
            'api_initialized': True,
            'degraded_mode': False,
            'error_count': 0
        }
        module.get_error_diagnostics.return_value = {
            'recovery_state': {'can_attempt_recovery': True}
        }
        module.degraded_mode = False
        return module
    
    @pytest.fixture
    def mock_automation_module(self):
        """Mock automation module for testing."""
        module = MagicMock()
        module.execute_fast_path_action.return_value = {
            'success': False,
            'error': 'Element not clickable'
        }
        return module
    
    @patch('orchestrator.VisionModule')
    @patch('orchestrator.ReasoningModule')
    @patch('orchestrator.AutomationModule')
    @patch('orchestrator.AudioModule')
    @patch('orchestrator.FeedbackModule')
    @patch('orchestrator.AccessibilityModule')
    @patch('orchestrator.AccessibilityHealthChecker')
    @patch('orchestrator.ErrorRecoveryManager')
    def test_debugging_tools_initialization(self, mock_recovery_class, mock_diagnostic_class,
                                          mock_accessibility_class, mock_feedback_class,
                                          mock_audio_class, mock_automation_class,
                                          mock_reasoning_class, mock_vision_class):
        """Test that debugging tools are properly initialized in orchestrator."""
        # Setup mocks
        mock_diagnostic_class.return_value = self.mock_diagnostic_tools()
        mock_recovery_class.return_value = self.mock_error_recovery_manager()
        mock_accessibility_class.return_value = self.mock_accessibility_module()
        
        # Create orchestrator
        orchestrator = Orchestrator()
        
        # Verify debugging tools were initialized
        assert orchestrator.debug_mode_enabled is True
        assert orchestrator.diagnostic_tools is not None
        assert orchestrator.error_recovery_manager is not None
        
        # Verify diagnostic tools were initialized with correct config
        mock_diagnostic_class.assert_called_once()
        diagnostic_config = mock_diagnostic_class.call_args[0][0]
        assert diagnostic_config['auto_diagnostics'] is True
        assert diagnostic_config['performance_tracking'] is True
        assert diagnostic_config['debug_level'] == 'DETAILED'
    
    @patch('orchestrator.VisionModule')
    @patch('orchestrator.ReasoningModule')
    @patch('orchestrator.AutomationModule')
    @patch('orchestrator.AudioModule')
    @patch('orchestrator.FeedbackModule')
    @patch('orchestrator.AccessibilityModule')
    def test_fast_path_diagnostic_integration(self, mock_accessibility_class, mock_feedback_class,
                                            mock_audio_class, mock_automation_class,
                                            mock_reasoning_class, mock_vision_class):
        """Test diagnostic integration when fast path is disabled."""
        # Setup mocks
        mock_accessibility_class.return_value = self.mock_accessibility_module()
        
        with patch.object(Orchestrator, '_initialize_debugging_tools'):
            orchestrator = Orchestrator()
            orchestrator.debug_mode_enabled = True
            orchestrator.diagnostic_tools = self.mock_diagnostic_tools()
            orchestrator.fast_path_enabled = False
            
            # Test fast path execution with diagnostics
            result = orchestrator._attempt_fast_path_execution("click Sign In", {})
            
            # Verify diagnostic check was performed
            orchestrator.diagnostic_tools.run_quick_accessibility_check.assert_called_once()
            
            # Verify result indicates fast path was disabled
            assert result['success'] is False
            assert result['failure_reason'] == 'fast_path_disabled'
    
    @patch('orchestrator.VisionModule')
    @patch('orchestrator.ReasoningModule')
    @patch('orchestrator.AutomationModule')
    @patch('orchestrator.AudioModule')
    @patch('orchestrator.FeedbackModule')
    @patch('orchestrator.AccessibilityModule')
    def test_error_recovery_integration(self, mock_accessibility_class, mock_feedback_class,
                                      mock_audio_class, mock_automation_class,
                                      mock_reasoning_class, mock_vision_class):
        """Test error recovery integration in fast path execution."""
        # Setup mocks
        accessibility_module = self.mock_accessibility_module()
        automation_module = self.mock_automation_module()
        
        mock_accessibility_class.return_value = accessibility_module
        mock_automation_class.return_value = automation_module
        
        with patch.object(Orchestrator, '_initialize_debugging_tools'):
            orchestrator = Orchestrator()
            orchestrator.debug_mode_enabled = True
            orchestrator.error_recovery_manager = self.mock_error_recovery_manager()
            orchestrator.accessibility_module = accessibility_module
            orchestrator.automation_module = automation_module
            
            # Mock element finding to succeed but action to fail
            accessibility_module.find_element_enhanced.return_value = ElementMatchResult(
                element={'role': 'AXButton', 'title': 'Sign In', 'center_point': [100, 200]},
                found=True,
                confidence_score=95.0,
                matched_attribute='AXTitle',
                search_time_ms=50.0,
                roles_checked=['AXButton'],
                attributes_checked=['AXTitle'],
                fuzzy_matches=[],
                fallback_triggered=False
            )
            
            # Mock GUI element extraction
            with patch.object(orchestrator, '_extract_gui_elements_from_command') as mock_extract:
                mock_extract.return_value = {
                    'role': 'AXButton',
                    'label': 'Sign In',
                    'action': 'click',
                    'app_name': 'TestApp'
                }
                
                # Mock performance timer
                mock_perf_timer = MagicMock()
                mock_perf_timer.__enter__ = MagicMock(return_value=mock_perf_timer)
                mock_perf_timer.__exit__ = MagicMock(return_value=None)
                
                with patch.object(accessibility_module, '_performance_timer', return_value=mock_perf_timer):
                    # Test fast path execution with error recovery
                    result = orchestrator._attempt_fast_path_execution("click Sign In", {'command_type': 'click'})
                    
                    # Verify error recovery was attempted
                    orchestrator.error_recovery_manager.attempt_recovery.assert_called()
                    
                    # Verify recovery context was provided
                    recovery_call = orchestrator.error_recovery_manager.attempt_recovery.call_args
                    assert 'command' in recovery_call[1]['context']
                    assert 'attempt' in recovery_call[1]['context']
    
    @patch('orchestrator.VisionModule')
    @patch('orchestrator.ReasoningModule')
    @patch('orchestrator.AutomationModule')
    @patch('orchestrator.AudioModule')
    @patch('orchestrator.FeedbackModule')
    @patch('orchestrator.AccessibilityModule')
    def test_fallback_diagnostic_integration(self, mock_accessibility_class, mock_feedback_class,
                                           mock_audio_class, mock_automation_class,
                                           mock_reasoning_class, mock_vision_class):
        """Test diagnostic integration during fast path fallback."""
        # Setup mocks
        mock_accessibility_class.return_value = self.mock_accessibility_module()
        
        with patch.object(Orchestrator, '_initialize_debugging_tools'):
            orchestrator = Orchestrator()
            orchestrator.debug_mode_enabled = True
            orchestrator.diagnostic_tools = self.mock_diagnostic_tools()
            orchestrator.accessibility_module = self.mock_accessibility_module()
            
            # Test fallback handling with diagnostics
            execution_context = {}
            fast_path_result = {
                'success': False,
                'failure_reason': 'element_not_found',
                'context': {'gui_elements': {'role': 'AXButton', 'label': 'Sign In'}},
                'execution_time': 0.15
            }
            
            orchestrator._handle_fast_path_fallback(
                execution_id="test_123",
                execution_context=execution_context,
                fast_path_result=fast_path_result,
                command="click Sign In"
            )
            
            # Verify targeted diagnostics were run
            orchestrator.diagnostic_tools.run_targeted_diagnostics.assert_called_once_with(
                failure_reason='element_not_found',
                command='click Sign In',
                context={'gui_elements': {'role': 'AXButton', 'label': 'Sign In'}}
            )
            
            # Verify diagnostic result was stored in execution context
            assert 'diagnostic_result' in execution_context
            assert execution_context['diagnostic_result']['issues'] is not None
    
    @patch('orchestrator.VisionModule')
    @patch('orchestrator.ReasoningModule')
    @patch('orchestrator.AutomationModule')
    @patch('orchestrator.AudioModule')
    @patch('orchestrator.FeedbackModule')
    @patch('orchestrator.AccessibilityModule')
    def test_performance_monitoring_integration(self, mock_accessibility_class, mock_feedback_class,
                                              mock_audio_class, mock_automation_class,
                                              mock_reasoning_class, mock_vision_class):
        """Test performance monitoring integration for fast path vs vision comparison."""
        # Setup mocks
        mock_accessibility_class.return_value = self.mock_accessibility_module()
        
        with patch.object(Orchestrator, '_initialize_debugging_tools'):
            orchestrator = Orchestrator()
            orchestrator.debug_mode_enabled = True
            orchestrator.diagnostic_tools = self.mock_diagnostic_tools()
            
            # Test performance comparison logging
            execution_context = {
                'fast_path_execution_time': 0.15,
                'fast_path_result': {
                    'enhanced_search_result': {
                        'confidence_score': 85.0,
                        'roles_checked': ['AXButton', 'AXMenuItem'],
                        'attributes_checked': ['AXTitle', 'AXDescription'],
                        'fuzzy_match_count': 2,
                        'fallback_triggered': True
                    }
                },
                'fallback_reason': 'element_not_found'
            }
            
            orchestrator._log_fallback_performance_comparison(
                execution_id="test_123",
                execution_context=execution_context,
                vision_execution_time=2.5
            )
            
            # Verify performance analysis was performed
            orchestrator.diagnostic_tools.analyze_performance_comparison.assert_called_once()
            
            # Verify analysis parameters
            analysis_call = orchestrator.diagnostic_tools.analyze_performance_comparison.call_args
            assert analysis_call[1]['fast_path_time'] == 0.15
            assert analysis_call[1]['vision_time'] == 2.5
            assert analysis_call[1]['fallback_reason'] == 'element_not_found'
    
    @patch('orchestrator.VisionModule')
    @patch('orchestrator.ReasoningModule')
    @patch('orchestrator.AutomationModule')
    @patch('orchestrator.AudioModule')
    @patch('orchestrator.FeedbackModule')
    @patch('orchestrator.AccessibilityModule')
    def test_debugging_graceful_degradation(self, mock_accessibility_class, mock_feedback_class,
                                          mock_audio_class, mock_automation_class,
                                          mock_reasoning_class, mock_vision_class):
        """Test graceful degradation when debugging tools fail."""
        # Setup mocks
        mock_accessibility_class.return_value = self.mock_accessibility_module()
        
        # Mock debugging tools to fail during initialization
        with patch('orchestrator.DiagnosticTools', side_effect=Exception("Debug init failed")):
            orchestrator = Orchestrator()
            
            # Verify orchestrator still works without debugging tools
            assert orchestrator.debug_mode_enabled is False
            assert orchestrator.diagnostic_tools is None
            assert orchestrator.error_recovery_manager is None
            
            # Verify fast path execution still works
            result = orchestrator._attempt_fast_path_execution("click Sign In", {})
            assert result is not None  # Should return a result even without debugging
    
    @patch('orchestrator.VisionModule')
    @patch('orchestrator.ReasoningModule')
    @patch('orchestrator.AutomationModule')
    @patch('orchestrator.AudioModule')
    @patch('orchestrator.FeedbackModule')
    @patch('orchestrator.AccessibilityModule')
    def test_diagnostic_error_handling(self, mock_accessibility_class, mock_feedback_class,
                                     mock_audio_class, mock_automation_class,
                                     mock_reasoning_class, mock_vision_class):
        """Test error handling in diagnostic operations."""
        # Setup mocks
        mock_accessibility_class.return_value = self.mock_accessibility_module()
        
        with patch.object(Orchestrator, '_initialize_debugging_tools'):
            orchestrator = Orchestrator()
            orchestrator.debug_mode_enabled = True
            
            # Mock diagnostic tools that throw errors
            diagnostic_tools = MagicMock()
            diagnostic_tools.run_targeted_diagnostics.side_effect = Exception("Diagnostic failed")
            orchestrator.diagnostic_tools = diagnostic_tools
            orchestrator.accessibility_module = self.mock_accessibility_module()
            
            # Test fallback handling with failing diagnostics
            execution_context = {}
            fast_path_result = {
                'success': False,
                'failure_reason': 'element_not_found',
                'context': {},
                'execution_time': 0.15
            }
            
            # Should not raise exception despite diagnostic failure
            orchestrator._handle_fast_path_fallback(
                execution_id="test_123",
                execution_context=execution_context,
                fast_path_result=fast_path_result,
                command="click Sign In"
            )
            
            # Verify execution context was still updated
            assert execution_context['fast_path_attempted'] is True
            assert execution_context['fallback_reason'] == 'element_not_found'
    
    @patch('orchestrator.VisionModule')
    @patch('orchestrator.ReasoningModule')
    @patch('orchestrator.AutomationModule')
    @patch('orchestrator.AudioModule')
    @patch('orchestrator.FeedbackModule')
    @patch('orchestrator.AccessibilityModule')
    def test_comprehensive_debugging_workflow(self, mock_accessibility_class, mock_feedback_class,
                                            mock_audio_class, mock_automation_class,
                                            mock_reasoning_class, mock_vision_class):
        """Test complete debugging workflow integration."""
        # Setup mocks
        accessibility_module = self.mock_accessibility_module()
        mock_accessibility_class.return_value = accessibility_module
        
        with patch.object(Orchestrator, '_initialize_debugging_tools'):
            orchestrator = Orchestrator()
            orchestrator.debug_mode_enabled = True
            orchestrator.diagnostic_tools = self.mock_diagnostic_tools()
            orchestrator.error_recovery_manager = self.mock_error_recovery_manager()
            orchestrator.accessibility_module = accessibility_module
            
            # Mock GUI element extraction
            with patch.object(orchestrator, '_extract_gui_elements_from_command') as mock_extract:
                mock_extract.return_value = {
                    'role': 'AXButton',
                    'label': 'Sign In',
                    'action': 'click',
                    'app_name': 'TestApp'
                }
                
                # Mock performance timer
                mock_perf_timer = MagicMock()
                mock_perf_timer.__enter__ = MagicMock(return_value=mock_perf_timer)
                mock_perf_timer.__exit__ = MagicMock(return_value=None)
                
                with patch.object(accessibility_module, '_performance_timer', return_value=mock_perf_timer):
                    # Test complete workflow
                    result = orchestrator._attempt_fast_path_execution("click Sign In", {'command_type': 'click'})
                    
                    # Verify all debugging components were used
                    assert orchestrator.diagnostic_tools.run_quick_accessibility_check.called
                    assert orchestrator.error_recovery_manager.attempt_recovery.called
                    
                    # Verify result contains debugging information
                    assert result is not None
                    assert 'failure_reason' in result


if __name__ == '__main__':
    pytest.main([__file__])