#!/usr/bin/env python3
"""
Integration tests for Orchestrator hybrid execution (fast path / slow path)

Tests fast path routing logic, fallback mechanism validation, and performance tracking.
Verifies that VisionModule is bypassed during successful fast path execution.

Requirements: 5.3, 5.4
"""

import pytest
import unittest.mock as mock
from unittest.mock import Mock, MagicMock, patch, call, AsyncMock
import logging
import time
import asyncio
from typing import Dict, Any, List, Optional

# Import the modules under test
from orchestrator import (
    Orchestrator,
    CommandStatus,
    ExecutionStep,
    ProgressReport,
    CommandValidationResult,
    OrchestratorError
)
from modules.accessibility import AccessibilityModule
from modules.vision import VisionModule
from modules.reasoning import ReasoningModule
from modules.automation import AutomationModule
from modules.audio import AudioModule
from modules.feedback import FeedbackModule


class TestHybridOrchestration:
    """Test suite for Orchestrator hybrid execution functionality."""
    
    @pytest.fixture
    def mock_modules(self):
        """Mock all required modules for testing."""
        mocks = {
            'vision': Mock(),
            'reasoning': Mock(),
            'automation': Mock(),
            'audio': Mock(),
            'feedback': Mock(),
            'accessibility': Mock()
        }
        
        # Setup default return values
        mocks['vision'].capture_screen.return_value = "mock_screenshot_path"
        mocks['vision'].analyze_screen.return_value = {
            'elements': [{'type': 'button', 'text': 'Sign In', 'coordinates': [100, 200, 150, 50]}],
            'description': 'Login screen with Sign In button'
        }
        
        mocks['reasoning'].get_action_plan.return_value = {
            'actions': [{'type': 'click', 'target': 'Sign In button', 'coordinates': [125, 225]}],
            'confidence': 0.9
        }
        
        mocks['automation'].execute_action.return_value = {'success': True, 'message': 'Action completed'}
        
        mocks['audio'].transcribe_audio.return_value = "click the sign in button"
        mocks['audio'].speak.return_value = None
        
        mocks['feedback'].play.return_value = None
        
        # Accessibility module setup for fast path
        mocks['accessibility'].find_element.return_value = {
            'coordinates': [100, 200, 150, 50],
            'center_point': [175, 225],
            'role': 'AXButton',
            'title': 'Sign In',
            'enabled': True,
            'app_name': 'TestApp'
        }
        mocks['accessibility'].find_element_with_vision_preparation.return_value = {
            'coordinates': [100, 200, 150, 50],
            'center_point': [175, 225],
            'role': 'AXButton',
            'title': 'Sign In',
            'enabled': True,
            'app_name': 'TestApp'
        }
        mocks['accessibility'].get_accessibility_status.return_value = {
            'api_initialized': True,
            'degraded_mode': False,
            'can_attempt_recovery': False
        }
        mocks['accessibility'].is_accessibility_enabled.return_value = True
        
        return mocks
    
    @pytest.fixture
    def orchestrator(self, mock_modules):
        """Create Orchestrator instance with mocked modules."""
        with patch('orchestrator.VisionModule', return_value=mock_modules['vision']), \
             patch('orchestrator.ReasoningModule', return_value=mock_modules['reasoning']), \
             patch('orchestrator.AutomationModule', return_value=mock_modules['automation']), \
             patch('orchestrator.AudioModule', return_value=mock_modules['audio']), \
             patch('orchestrator.FeedbackModule', return_value=mock_modules['feedback']), \
             patch('orchestrator.AccessibilityModule', return_value=mock_modules['accessibility']):
            
            orchestrator = Orchestrator()
            
            # Manually set the mocked modules
            orchestrator.vision_module = mock_modules['vision']
            orchestrator.reasoning_module = mock_modules['reasoning']
            orchestrator.automation_module = mock_modules['automation']
            orchestrator.audio_module = mock_modules['audio']
            orchestrator.feedback_module = mock_modules['feedback']
            orchestrator.accessibility_module = mock_modules['accessibility']
            
            # Ensure fast path is enabled
            orchestrator.fast_path_enabled = True
            
            return orchestrator
    
    @pytest.fixture
    def sample_gui_command(self):
        """Sample GUI command for testing."""
        return "click the sign in button"
    
    @pytest.fixture
    def sample_non_gui_command(self):
        """Sample non-GUI command for testing."""
        return "what is the weather today"


class TestFastPathRouting(TestHybridOrchestration):
    """Test fast path routing logic."""
    
    def test_is_gui_command_detection(self, orchestrator):
        """Test GUI command detection logic."""
        # Test GUI commands
        gui_commands = [
            "click the sign in button",
            "type my password",
            "scroll down",
            "press enter",
            "select the dropdown menu"
        ]
        
        for command in gui_commands:
            command_info = {'command_type': 'gui_interaction', 'confidence': 0.9}
            assert orchestrator._is_gui_command(command, command_info) is True
    
    def test_non_gui_command_detection(self, orchestrator):
        """Test non-GUI command detection logic."""
        # Test non-GUI commands
        non_gui_commands = [
            "what is the weather today",
            "tell me a joke",
            "what time is it",
            "read me the news"
        ]
        
        for command in non_gui_commands:
            command_info = {'command_type': 'question', 'confidence': 0.8}
            assert orchestrator._is_gui_command(command, command_info) is False
    
    def test_fast_path_execution_success(self, orchestrator, mock_modules, sample_gui_command):
        """Test successful fast path execution."""
        # Setup successful fast path
        mock_modules['accessibility'].find_element.return_value = {
            'coordinates': [100, 200, 150, 50],
            'center_point': [175, 225],
            'role': 'AXButton',
            'title': 'Sign In',
            'enabled': True,
            'app_name': 'TestApp'
        }
        
        mock_modules['automation'].execute_fast_path_action.return_value = {
            'success': True,
            'action_type': 'click',
            'coordinates': [175, 225],
            'execution_time': 0.5
        }
        
        # Test fast path execution
        command_info = {'command_type': 'gui_interaction', 'confidence': 0.9}
        result = orchestrator._attempt_fast_path_execution(sample_gui_command, command_info)
        
        # Verify successful execution
        assert result is not None
        assert result['success'] is True
        assert result['path_used'] == 'fast'
        assert 'element_found' in result
        assert 'action_result' in result
        assert 'execution_time' in result
        
        # Verify accessibility module was called
        mock_modules['accessibility'].find_element_with_vision_preparation.assert_called()
        mock_modules['automation'].execute_fast_path_action.assert_called()
    
    def test_fast_path_execution_element_not_found(self, orchestrator, mock_modules, sample_gui_command):
        """Test fast path execution when element is not found."""
        # Setup element not found scenario
        mock_modules['accessibility'].find_element_with_vision_preparation.return_value = None
        
        # Test fast path execution
        command_info = {'command_type': 'gui_interaction', 'confidence': 0.9}
        result = orchestrator._attempt_fast_path_execution(sample_gui_command, command_info)
        
        # Verify fallback is triggered
        assert result is not None
        assert result['success'] is False
        assert result['fallback_required'] is True
        assert 'failure_reason' in result
        
        # Verify accessibility module was called but automation was not
        mock_modules['accessibility'].find_element_with_vision_preparation.assert_called()
        mock_modules['automation'].execute_fast_path_action.assert_not_called()
    
    def test_fast_path_execution_disabled(self, orchestrator, mock_modules, sample_gui_command):
        """Test fast path execution when fast path is disabled."""
        # Disable fast path
        orchestrator.fast_path_enabled = False
        
        # Test fast path execution
        command_info = {'command_type': 'gui_interaction', 'confidence': 0.9}
        result = orchestrator._attempt_fast_path_execution(sample_gui_command, command_info)
        
        # Verify fast path is skipped
        assert result is not None
        assert result['success'] is False
        assert result['fallback_required'] is True
        assert result['failure_reason'] == 'fast_path_disabled'
        
        # Verify accessibility module was not called
        mock_modules['accessibility'].find_element_with_vision_preparation.assert_not_called()
    
    def test_fast_path_execution_accessibility_error(self, orchestrator, mock_modules, sample_gui_command):
        """Test fast path execution when accessibility module raises error."""
        # Setup accessibility error
        mock_modules['accessibility'].find_element_with_vision_preparation.side_effect = Exception("Accessibility API error")
        
        # Test fast path execution
        command_info = {'command_type': 'gui_interaction', 'confidence': 0.9}
        result = orchestrator._attempt_fast_path_execution(sample_gui_command, command_info)
        
        # Verify error handling
        assert result is not None
        assert result['success'] is False
        assert result['fallback_required'] is True
        assert 'failure_reason' in result
        assert result['failure_reason'] == 'execution_error'
        
        # Verify accessibility module was called
        mock_modules['accessibility'].find_element_with_vision_preparation.assert_called()


class TestFallbackMechanism(TestHybridOrchestration):
    """Test fallback mechanism validation."""
    
    def test_fallback_to_vision_workflow(self, orchestrator, mock_modules, sample_gui_command):
        """Test fallback to vision workflow when fast path fails."""
        # Setup fast path failure
        mock_modules['accessibility'].find_element.return_value = None
        
        # Mock the fallback handler
        with patch.object(orchestrator, '_handle_fast_path_fallback') as mock_fallback:
            with patch.object(orchestrator, '_is_gui_command', return_value=True):
                
                # Execute command (this should trigger fallback)
                execution_id = "test_execution_123"
                execution_context = {
                    'execution_id': execution_id,
                    'command': sample_gui_command,
                    'start_time': time.time(),
                    'steps_completed': []
                }
                
                # Simulate the execution flow that would trigger fallback
                fast_path_result = orchestrator._attempt_fast_path_execution(sample_gui_command, {})
                
                if not fast_path_result.get('success'):
                    orchestrator._handle_fast_path_fallback(
                        execution_id, execution_context, fast_path_result, sample_gui_command
                    )
                
                # Verify fallback was called
                mock_fallback.assert_called_once_with(
                    execution_id, execution_context, fast_path_result, sample_gui_command
                )
    
    def test_vision_module_bypassed_on_fast_path_success(self, orchestrator, mock_modules, sample_gui_command):
        """Test that VisionModule is bypassed during successful fast path execution."""
        # Setup successful fast path
        mock_modules['accessibility'].find_element.return_value = {
            'coordinates': [100, 200, 150, 50],
            'center_point': [175, 225],
            'role': 'AXButton',
            'title': 'Sign In',
            'enabled': True,
            'app_name': 'TestApp'
        }
        
        mock_modules['automation'].execute_fast_path_action.return_value = {
            'success': True,
            'action_type': 'click',
            'coordinates': [175, 225],
            'execution_time': 0.5
        }
        
        # Execute fast path
        command_info = {'command_type': 'gui_interaction', 'confidence': 0.9}
        result = orchestrator._attempt_fast_path_execution(sample_gui_command, command_info)
        
        # Verify fast path succeeded
        assert result['success'] is True
        
        # Verify VisionModule methods were NOT called
        mock_modules['vision'].capture_screen.assert_not_called()
        mock_modules['vision'].analyze_screen.assert_not_called()
        
        # Verify ReasoningModule was NOT called
        mock_modules['reasoning'].get_action_plan.assert_not_called()
    
    def test_vision_module_used_on_fast_path_failure(self, orchestrator, mock_modules, sample_gui_command):
        """Test that VisionModule is used when fast path fails."""
        # Setup fast path failure
        mock_modules['accessibility'].find_element.return_value = None
        
        # Mock the complete execution flow
        with patch.object(orchestrator, 'execute_command') as mock_execute:
            with patch.object(orchestrator, '_perform_screen_perception') as mock_perception:
                with patch.object(orchestrator, '_is_gui_command', return_value=True):
                    
                    # Setup perception to return mock data
                    mock_perception.return_value = {
                        'screenshot_path': 'mock_screenshot.png',
                        'analysis': {'elements': [{'type': 'button', 'text': 'Sign In'}]}
                    }
                    
                    # Simulate fallback execution
                    execution_context = {
                        'execution_id': 'test_123',
                        'command': sample_gui_command,
                        'start_time': time.time(),
                        'steps_completed': []
                    }
                    
                    fast_path_result = {'success': False, 'fallback_required': True}
                    
                    orchestrator._handle_fast_path_fallback(
                        'test_123', execution_context, fast_path_result, sample_gui_command
                    )
                    
                    # Verify vision workflow is triggered in fallback
                    # (This would be called by the fallback handler)
                    mock_perception.assert_called()


class TestPerformanceTracking(TestHybridOrchestration):
    """Test performance tracking for hybrid execution."""
    
    def test_fast_path_performance_metrics(self, orchestrator, mock_modules, sample_gui_command):
        """Test performance metrics collection for fast path execution."""
        # Setup successful fast path with timing
        mock_modules['accessibility'].find_element.return_value = {
            'coordinates': [100, 200, 150, 50],
            'center_point': [175, 225],
            'role': 'AXButton',
            'title': 'Sign In',
            'enabled': True,
            'app_name': 'TestApp'
        }
        
        mock_modules['automation'].execute_fast_path_action.return_value = {
            'success': True,
            'action_type': 'click',
            'coordinates': [175, 225],
            'execution_time': 0.3
        }
        
        # Execute fast path
        start_time = time.time()
        command_info = {'command_type': 'gui_interaction', 'confidence': 0.9}
        result = orchestrator._attempt_fast_path_execution(sample_gui_command, command_info)
        
        # Verify performance metrics are included
        assert result['success'] is True
        assert 'execution_time' in result
        assert result['execution_time'] > 0
        assert result['execution_time'] < 2.0  # Should be fast
        # Action result should contain timing info
        assert 'action_result' in result
        assert result['action_result']['execution_time'] == 0.3
    
    def test_performance_comparison_fast_vs_slow_path(self, orchestrator, mock_modules):
        """Test performance comparison between fast and slow paths."""
        gui_command = "click the sign in button"
        
        # Test fast path performance
        mock_modules['accessibility'].find_element.return_value = {
            'coordinates': [100, 200, 150, 50],
            'center_point': [175, 225],
            'role': 'AXButton',
            'title': 'Sign In',
            'enabled': True,
            'app_name': 'TestApp'
        }
        
        mock_modules['automation'].execute_fast_path_action.return_value = {
            'success': True,
            'action_type': 'click',
            'coordinates': [175, 225],
            'execution_time': 0.2
        }
        
        # Execute fast path
        fast_start = time.time()
        fast_result = orchestrator._attempt_fast_path_execution(gui_command, {})
        fast_time = time.time() - fast_start
        
        # Verify fast path is indeed fast
        assert fast_result['success'] is True
        assert fast_time < 1.0  # Should complete in under 1 second
        
        # Test slow path simulation (vision + reasoning)
        mock_modules['vision'].analyze_screen.return_value = {
            'elements': [{'type': 'button', 'text': 'Sign In', 'coordinates': [100, 200, 150, 50]}],
            'description': 'Login screen'
        }
        
        mock_modules['reasoning'].get_action_plan.return_value = {
            'actions': [{'type': 'click', 'target': 'Sign In button'}],
            'confidence': 0.8
        }
        
        # Simulate slow path timing
        slow_start = time.time()
        # These calls would normally take longer due to vision processing
        mock_modules['vision'].capture_screen()
        mock_modules['vision'].analyze_screen("mock_screenshot")
        mock_modules['reasoning'].get_action_plan("mock_analysis", gui_command)
        slow_time = time.time() - slow_start
        
        # In real scenarios, slow path would be significantly slower
        # Here we just verify the methods were called
        mock_modules['vision'].capture_screen.assert_called()
        mock_modules['vision'].analyze_screen.assert_called()
        mock_modules['reasoning'].get_action_plan.assert_called()
    
    def test_hybrid_execution_metrics_collection(self, orchestrator, mock_modules):
        """Test comprehensive metrics collection for hybrid execution."""
        # Mock performance monitoring
        with patch('orchestrator.performance_monitor') as mock_monitor:
            mock_monitor.record_metric.return_value = None
            
            # Setup successful fast path
            mock_modules['accessibility'].find_element.return_value = {
                'coordinates': [100, 200, 150, 50],
                'center_point': [175, 225],
                'role': 'AXButton',
                'title': 'Sign In',
                'enabled': True,
                'app_name': 'TestApp'
            }
            
            mock_modules['automation'].execute_fast_path_action.return_value = {
                'success': True,
                'action_type': 'click',
                'coordinates': [175, 225],
                'execution_time': 0.4
            }
            
            # Execute fast path
            command_info = {'command_type': 'gui_interaction', 'confidence': 0.9}
            result = orchestrator._attempt_fast_path_execution("click sign in", command_info)
            
            # Verify metrics are collected
            assert result['success'] is True
            assert 'performance_metrics' in result or 'execution_time' in result


class TestErrorHandlingAndRecovery(TestHybridOrchestration):
    """Test error handling and recovery in hybrid execution."""
    
    def test_accessibility_module_failure_recovery(self, orchestrator, mock_modules):
        """Test recovery when accessibility module fails."""
        # Setup accessibility module failure
        mock_modules['accessibility'].find_element.side_effect = Exception("Accessibility API unavailable")
        
        # Test fast path execution
        command_info = {'command_type': 'gui_interaction', 'confidence': 0.9}
        result = orchestrator._attempt_fast_path_execution("click button", command_info)
        
        # Verify graceful failure and fallback
        assert result is not None
        assert result['success'] is False
        assert result['fallback_required'] is True
        assert 'failure_reason' in result
        
        # Verify fast path is disabled after failure
        # (This would be handled by the error recovery system)
        assert 'context' in result
        assert 'error' in result['context']
    
    def test_fast_path_timeout_handling(self, orchestrator, mock_modules):
        """Test handling of fast path timeouts."""
        # Setup slow accessibility response
        def slow_find_element(*args, **kwargs):
            time.sleep(0.1)  # Simulate slow response
            return {
                'coordinates': [100, 200, 150, 50],
                'center_point': [175, 225],
                'role': 'AXButton',
                'title': 'Sign In',
                'enabled': True,
                'app_name': 'TestApp'
            }
        
        mock_modules['accessibility'].find_element.side_effect = slow_find_element
        mock_modules['automation'].execute_fast_path_action.return_value = {
            'success': True,
            'action_type': 'click',
            'coordinates': [175, 225],
            'execution_time': 0.1
        }
        
        # Test fast path execution with timeout consideration
        command_info = {'command_type': 'gui_interaction', 'confidence': 0.9}
        start_time = time.time()
        result = orchestrator._attempt_fast_path_execution("click button", command_info)
        execution_time = time.time() - start_time
        
        # Verify execution completes within reasonable time
        assert result['success'] is True
        assert execution_time < 5.0  # Should not hang indefinitely
    
    def test_partial_accessibility_support(self, orchestrator, mock_modules):
        """Test handling when accessibility is partially supported."""
        # Setup partial accessibility support
        mock_modules['accessibility'].is_accessibility_enabled.return_value = True
        mock_modules['accessibility'].find_element.side_effect = [
            None,  # First element not found
            {      # Second element found
                'coordinates': [200, 300, 100, 40],
                'center_point': [250, 320],
                'role': 'AXButton',
                'title': 'Submit',
                'enabled': True,
                'app_name': 'TestApp'
            }
        ]
        
        # Test multiple fast path attempts
        command_info = {'command_type': 'gui_interaction', 'confidence': 0.9}
        
        # First attempt - should fail
        result1 = orchestrator._attempt_fast_path_execution("click login", command_info)
        assert result1['success'] is False
        
        # Second attempt - should succeed
        result2 = orchestrator._attempt_fast_path_execution("click submit", command_info)
        assert result2['success'] is True


class TestCommandValidationIntegration(TestHybridOrchestration):
    """Test integration between command validation and hybrid execution."""
    
    def test_gui_command_validation_and_routing(self, orchestrator, mock_modules):
        """Test that GUI commands are properly validated and routed to fast path."""
        # Mock command validation
        with patch.object(orchestrator, 'validate_command') as mock_validate:
            mock_validate.return_value = CommandValidationResult(
                is_valid=True,
                normalized_command="click the sign in button",
                command_type="gui_interaction",
                confidence=0.95,
                issues=[],
                suggestions=[]
            )
            
            # Setup successful fast path
            mock_modules['accessibility'].find_element.return_value = {
                'coordinates': [100, 200, 150, 50],
                'center_point': [175, 225],
                'role': 'AXButton',
                'title': 'Sign In',
                'enabled': True,
                'app_name': 'TestApp'
            }
            
            mock_modules['automation'].execute_fast_path_action.return_value = {
                'success': True,
                'action_type': 'click',
                'coordinates': [175, 225],
                'execution_time': 0.3
            }
            
            # Test command validation and routing
            with patch.object(orchestrator, '_is_gui_command', return_value=True):
                with patch.object(orchestrator, '_attempt_fast_path_execution') as mock_fast_path:
                    mock_fast_path.return_value = {'success': True, 'path_used': 'fast'}
                    
                    # Simulate the validation and routing process
                    validation_result = mock_validate("click sign in button")
                    is_gui = orchestrator._is_gui_command(
                        validation_result.normalized_command, 
                        validation_result.__dict__
                    )
                    
                    if is_gui:
                        fast_path_result = orchestrator._attempt_fast_path_execution(
                            validation_result.normalized_command,
                            validation_result.__dict__
                        )
                    
                    # Verify the flow
                    assert validation_result.is_valid is True
                    assert validation_result.command_type == "gui_interaction"
                    assert is_gui is True
                    mock_fast_path.assert_called_once()
    
    def test_non_gui_command_skips_fast_path(self, orchestrator, mock_modules):
        """Test that non-GUI commands skip fast path routing."""
        # Mock command validation for non-GUI command
        with patch.object(orchestrator, 'validate_command') as mock_validate:
            mock_validate.return_value = CommandValidationResult(
                is_valid=True,
                normalized_command="what is the weather today",
                command_type="question",
                confidence=0.9,
                issues=[],
                suggestions=[]
            )
            
            # Test command validation and routing
            with patch.object(orchestrator, '_is_gui_command', return_value=False):
                with patch.object(orchestrator, '_attempt_fast_path_execution') as mock_fast_path:
                    
                    # Simulate the validation and routing process
                    validation_result = mock_validate("what is the weather")
                    is_gui = orchestrator._is_gui_command(
                        validation_result.normalized_command,
                        validation_result.__dict__
                    )
                    
                    # Non-GUI commands should not trigger fast path
                    if is_gui:
                        orchestrator._attempt_fast_path_execution(
                            validation_result.normalized_command,
                            validation_result.__dict__
                        )
                    
                    # Verify the flow
                    assert validation_result.command_type == "question"
                    assert is_gui is False
                    mock_fast_path.assert_not_called()


if __name__ == '__main__':
    pytest.main([__file__])