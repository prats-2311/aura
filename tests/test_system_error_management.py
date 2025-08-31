# tests/test_system_error_management.py
"""
Integration tests for system-wide error management in the Orchestrator.
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from orchestrator import Orchestrator, OrchestratorError, CommandStatus
from modules.error_handler import ErrorCategory, ErrorSeverity


class TestSystemErrorManagement:
    """Test system-wide error management functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Mock all modules to avoid initialization issues
        with patch('orchestrator.VisionModule'), \
             patch('orchestrator.ReasoningModule'), \
             patch('orchestrator.AutomationModule'), \
             patch('orchestrator.AudioModule'), \
             patch('orchestrator.FeedbackModule'):
            self.orchestrator = Orchestrator()
    
    def test_system_health_monitoring(self):
        """Test system health monitoring functionality."""
        health_status = self.orchestrator.get_system_health()
        
        assert isinstance(health_status, dict)
        assert 'overall_health' in health_status
        assert 'health_score' in health_status
        assert 'module_health' in health_status
        assert 'last_health_check' in health_status
        
        # Check that all expected modules are monitored
        expected_modules = ['vision', 'reasoning', 'automation', 'audio', 'feedback']
        for module in expected_modules:
            assert module in health_status['module_health']
    
    def test_module_availability_tracking(self):
        """Test that module availability is properly tracked."""
        assert isinstance(self.orchestrator.module_availability, dict)
        
        # All modules should be available after successful initialization
        for module, available in self.orchestrator.module_availability.items():
            assert isinstance(available, bool)
    
    def test_system_recovery_attempt(self):
        """Test system recovery functionality."""
        # Simulate a module failure
        self.orchestrator.module_availability['vision'] = False
        self.orchestrator.system_health_status['module_health']['vision'] = 'failed'
        
        recovery_result = self.orchestrator.attempt_system_recovery('vision')
        
        assert isinstance(recovery_result, dict)
        assert 'recovery_attempted' in recovery_result
        assert 'recovery_successful' in recovery_result
        assert 'recovered_modules' in recovery_result
        assert 'failed_modules' in recovery_result
        assert recovery_result['recovery_attempted'] is True
    
    def test_module_error_handling(self):
        """Test handling of module-specific errors."""
        test_error = Exception("Test module error")
        
        handling_result = self.orchestrator.handle_module_error('vision', test_error)
        
        assert isinstance(handling_result, dict)
        assert 'error_handled' in handling_result
        assert 'error_info' in handling_result
        assert 'recovery_attempted' in handling_result
        assert handling_result['error_handled'] is True
    
    def test_graceful_degradation(self):
        """Test graceful degradation when modules fail."""
        # Test graceful degradation for each module type
        modules_to_test = ['vision', 'reasoning', 'automation', 'audio', 'feedback']
        
        for module in modules_to_test:
            test_error = Exception(f"Test {module} error")
            error_info = Mock()
            error_info.recoverable = False
            
            degradation_result = self.orchestrator._attempt_graceful_degradation(module, error_info)
            
            # Should return True for all modules (graceful degradation possible)
            assert degradation_result is True
    
    def test_critical_system_health_handling(self):
        """Test handling when system health is critical."""
        # Mock get_system_health to return critical status
        with patch.object(self.orchestrator, 'get_system_health') as mock_health:
            mock_health.return_value = {'overall_health': 'critical', 'health_score': 10}
            
            # Mock recovery to fail
            with patch.object(self.orchestrator, 'attempt_system_recovery') as mock_recovery:
                mock_recovery.return_value = {'recovery_successful': False}
                
                with pytest.raises(OrchestratorError) as exc_info:
                    self.orchestrator.execute_command("test command")
                
                assert "System unavailable" in str(exc_info.value)
    
    def test_error_recovery_during_command_execution(self):
        """Test error recovery during command execution."""
        # Enable error recovery
        self.orchestrator.error_recovery_enabled = True
        
        # Mock command execution to fail initially
        with patch.object(self.orchestrator, '_execute_command_internal') as mock_execute:
            mock_execute.side_effect = [Exception("Initial failure"), {"status": "success"}]
            
            # Mock successful recovery
            with patch.object(self.orchestrator, 'attempt_system_recovery') as mock_recovery:
                mock_recovery.return_value = {'recovery_successful': True}
                
                result = self.orchestrator.execute_command("test command")
                
                # Should succeed after recovery
                assert result["status"] == "success"
                assert mock_execute.call_count == 2  # Initial failure + retry
                assert mock_recovery.call_count == 1
    
    def test_module_recovery_strategies(self):
        """Test individual module recovery strategies."""
        modules_to_test = ['vision', 'reasoning', 'automation', 'audio', 'feedback']
        
        for module in modules_to_test:
            # Mock the module class to avoid actual initialization
            with patch(f'orchestrator.{module.title()}Module'):
                recovery_success = self.orchestrator._recover_module(module)
                
                # Should return True for successful recovery
                assert recovery_success is True
    
    def test_recovery_attempt_limits(self):
        """Test that recovery attempts are limited to prevent infinite loops."""
        # Set recovery attempts to maximum
        self.orchestrator.system_health_status['recovery_attempts']['vision'] = 3
        
        test_error = Exception("Persistent error")
        handling_result = self.orchestrator.handle_module_error('vision', test_error)
        
        # Should not attempt recovery when limit is reached
        assert handling_result['recovery_attempted'] is False
    
    def test_system_health_score_calculation(self):
        """Test system health score calculation."""
        # Set some modules as unavailable
        self.orchestrator.module_availability['audio'] = False
        self.orchestrator.module_availability['feedback'] = False
        
        health_status = self.orchestrator.get_system_health()
        
        # Health score should be affected by unavailable modules
        assert 'health_score' in health_status
        assert 0 <= health_status['health_score'] <= 100
        assert health_status['overall_health'] in ['healthy', 'degraded', 'unhealthy', 'critical']
    
    def test_error_statistics_integration(self):
        """Test integration with global error handler statistics."""
        # Generate some errors
        for i in range(5):
            test_error = Exception(f"Test error {i}")
            self.orchestrator.handle_module_error('vision', test_error)
        
        health_status = self.orchestrator.get_system_health()
        
        # Should include error statistics
        assert 'error_statistics' in health_status
        assert health_status['error_statistics']['total_errors'] > 0
    
    def test_concurrent_error_handling(self):
        """Test error handling under concurrent conditions."""
        import threading
        import concurrent.futures
        
        errors = []
        
        def generate_module_error(module_name):
            try:
                test_error = Exception(f"Concurrent error in {module_name}")
                result = self.orchestrator.handle_module_error(module_name, test_error)
                return result
            except Exception as e:
                errors.append(e)
                return None
        
        # Generate concurrent errors
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            modules = ['vision', 'reasoning', 'automation', 'audio', 'feedback']
            
            for module in modules:
                future = executor.submit(generate_module_error, module)
                futures.append(future)
            
            # Wait for all to complete
            results = [future.result() for future in futures]
        
        # Should handle all errors without exceptions
        assert len(errors) == 0
        assert all(result is not None for result in results)
        assert all(result['error_handled'] for result in results)
    
    def test_system_health_update_after_recovery(self):
        """Test that system health is updated after recovery attempts."""
        # Simulate failed modules
        self.orchestrator.module_availability['vision'] = False
        self.orchestrator.module_availability['audio'] = False
        
        initial_health = self.orchestrator.get_system_health()
        
        # Attempt recovery
        recovery_result = self.orchestrator.attempt_system_recovery()
        
        updated_health = self.orchestrator.get_system_health()
        
        # Health should be updated after recovery attempt
        assert 'last_recovery_attempt' in self.orchestrator.system_health_status
        assert updated_health['last_health_check'] >= initial_health['last_health_check']
    
    def test_command_validation_error_handling(self):
        """Test error handling during command validation."""
        # Test empty command
        with pytest.raises(ValueError) as exc_info:
            self.orchestrator.execute_command("")
        
        assert "Invalid command" in str(exc_info.value)
        
        # Test whitespace-only command
        with pytest.raises(ValueError) as exc_info:
            self.orchestrator.execute_command("   ")
        
        assert "Invalid command" in str(exc_info.value)
    
    def test_error_recovery_disabled(self):
        """Test behavior when error recovery is disabled."""
        # Disable error recovery
        self.orchestrator.error_recovery_enabled = False
        
        # Mock command execution to fail
        with patch.object(self.orchestrator, '_execute_command_internal') as mock_execute:
            mock_execute.side_effect = Exception("Execution failure")
            
            with pytest.raises(OrchestratorError) as exc_info:
                self.orchestrator.execute_command("test command")
            
            assert "Command execution failed" in str(exc_info.value)
    
    def test_graceful_degradation_disabled(self):
        """Test behavior when graceful degradation is disabled."""
        # Disable graceful degradation
        self.orchestrator.graceful_degradation_enabled = False
        
        test_error = Exception("Test error")
        handling_result = self.orchestrator.handle_module_error('vision', test_error)
        
        # Should not attempt graceful degradation
        assert handling_result['graceful_degradation'] is False


class TestErrorRecoveryStrategies:
    """Test specific error recovery strategies."""
    
    def setup_method(self):
        """Set up test fixtures."""
        with patch('orchestrator.VisionModule'), \
             patch('orchestrator.ReasoningModule'), \
             patch('orchestrator.AutomationModule'), \
             patch('orchestrator.AudioModule'), \
             patch('orchestrator.FeedbackModule'):
            self.orchestrator = Orchestrator()
    
    def test_vision_module_recovery(self):
        """Test vision module recovery strategy."""
        with patch('orchestrator.VisionModule') as mock_vision:
            mock_vision.return_value = Mock()
            
            recovery_success = self.orchestrator._recover_module('vision')
            
            assert recovery_success is True
            assert mock_vision.called
    
    def test_reasoning_module_recovery(self):
        """Test reasoning module recovery strategy."""
        with patch('orchestrator.ReasoningModule') as mock_reasoning:
            mock_reasoning.return_value = Mock()
            
            recovery_success = self.orchestrator._recover_module('reasoning')
            
            assert recovery_success is True
            assert mock_reasoning.called
    
    def test_automation_module_recovery(self):
        """Test automation module recovery strategy."""
        with patch('orchestrator.AutomationModule') as mock_automation:
            mock_automation.return_value = Mock()
            
            recovery_success = self.orchestrator._recover_module('automation')
            
            assert recovery_success is True
            assert mock_automation.called
    
    def test_audio_module_recovery(self):
        """Test audio module recovery strategy."""
        with patch('orchestrator.AudioModule') as mock_audio:
            mock_audio.return_value = Mock()
            
            recovery_success = self.orchestrator._recover_module('audio')
            
            assert recovery_success is True
            assert mock_audio.called
    
    def test_feedback_module_recovery(self):
        """Test feedback module recovery strategy."""
        with patch('orchestrator.FeedbackModule') as mock_feedback:
            mock_feedback.return_value = Mock()
            
            recovery_success = self.orchestrator._recover_module('feedback')
            
            assert recovery_success is True
            assert mock_feedback.called
    
    def test_unknown_module_recovery(self):
        """Test recovery attempt for unknown module."""
        recovery_success = self.orchestrator._recover_module('unknown_module')
        
        assert recovery_success is False
    
    def test_module_recovery_failure(self):
        """Test handling of module recovery failures."""
        with patch('orchestrator.VisionModule') as mock_vision:
            mock_vision.side_effect = Exception("Recovery failed")
            
            recovery_success = self.orchestrator._recover_module('vision')
            
            assert recovery_success is False


if __name__ == "__main__":
    pytest.main([__file__])