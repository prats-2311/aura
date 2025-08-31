# tests/test_automation_integration.py
"""
Integration tests for the AutomationModule.

Tests complete action sequences and advanced features like error recovery,
retry logic, and action history tracking.
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from modules.automation import AutomationModule


class TestAutomationModuleIntegration:
    """Integration test cases for AutomationModule advanced features."""
    
    @patch('modules.automation.pyautogui')
    def test_execute_action_sequence_success(self, mock_pyautogui):
        """Test successful execution of a complete action sequence."""
        mock_pyautogui.size.return_value = (1920, 1080)
        automation = AutomationModule()
        
        actions = [
            {"action": "click", "coordinates": [100, 200]},
            {"action": "type", "text": "Hello World"},
            {"action": "scroll", "direction": "down", "amount": 100},
            {"action": "double_click", "coordinates": [300, 400]}
        ]
        
        result = automation.execute_action_sequence(actions)
        
        assert result["total_actions"] == 4
        assert result["successful_actions"] == 4
        assert result["failed_actions"] == 0
        assert len(result["errors"]) == 0
        assert result["execution_time"] > 0
        
        # Verify all actions were called
        assert mock_pyautogui.moveTo.call_count == 2  # For click and double_click
        assert mock_pyautogui.click.call_count == 1
        assert mock_pyautogui.doubleClick.call_count == 1
        assert mock_pyautogui.typewrite.call_count == 1
        assert mock_pyautogui.scroll.call_count == 1
    
    @patch('modules.automation.pyautogui')
    def test_execute_action_sequence_with_failures_continue(self, mock_pyautogui):
        """Test action sequence execution with failures, continuing on error."""
        mock_pyautogui.size.return_value = (1920, 1080)
        mock_pyautogui.click.side_effect = [Exception("Click failed"), None]  # First click fails, second succeeds
        
        automation = AutomationModule(max_retries=0)  # No retries for faster testing
        
        actions = [
            {"action": "click", "coordinates": [100, 200]},  # This will fail
            {"action": "type", "text": "Hello"},  # This will succeed
            {"action": "click", "coordinates": [300, 400]}   # This will succeed
        ]
        
        result = automation.execute_action_sequence(actions, stop_on_error=False)
        
        assert result["total_actions"] == 3
        assert result["successful_actions"] == 2
        assert result["failed_actions"] == 1
        assert len(result["errors"]) == 1
        assert "Action 1 failed" in result["errors"][0]
    
    @patch('modules.automation.pyautogui')
    def test_execute_action_sequence_with_failures_stop_on_error(self, mock_pyautogui):
        """Test action sequence execution stopping on first error."""
        mock_pyautogui.size.return_value = (1920, 1080)
        mock_pyautogui.typewrite.side_effect = Exception("Type failed")
        
        automation = AutomationModule(max_retries=0)
        
        actions = [
            {"action": "click", "coordinates": [100, 200]},  # This will succeed
            {"action": "type", "text": "Hello"},  # This will fail
            {"action": "click", "coordinates": [300, 400]}   # This won't be executed
        ]
        
        result = automation.execute_action_sequence(actions, stop_on_error=True)
        
        assert result["total_actions"] == 3
        assert result["successful_actions"] == 1
        assert result["failed_actions"] == 1
        assert len(result["errors"]) == 1
        
        # Verify third action wasn't attempted
        assert mock_pyautogui.click.call_count == 1  # Only first click
    
    @patch('modules.automation.pyautogui')
    @patch('modules.automation.time.sleep')
    def test_retry_mechanism(self, mock_sleep, mock_pyautogui):
        """Test retry mechanism for failed actions."""
        mock_pyautogui.size.return_value = (1920, 1080)
        # First two attempts fail, third succeeds
        mock_pyautogui.click.side_effect = [Exception("Fail 1"), Exception("Fail 2"), None]
        
        automation = AutomationModule(max_retries=2, retry_delay=0.1)
        
        action = {"action": "click", "coordinates": [100, 200]}
        automation.execute_action(action)
        
        # Should have tried 3 times total (initial + 2 retries)
        assert mock_pyautogui.click.call_count == 3
        # Should have slept twice (between retries)
        assert mock_sleep.call_count == 2
        mock_sleep.assert_called_with(0.1)
    
    @patch('modules.automation.pyautogui')
    def test_retry_mechanism_all_fail(self, mock_pyautogui):
        """Test retry mechanism when all attempts fail."""
        mock_pyautogui.size.return_value = (1920, 1080)
        mock_pyautogui.click.side_effect = Exception("Always fails")
        
        automation = AutomationModule(max_retries=2)
        
        action = {"action": "click", "coordinates": [100, 200]}
        
        with pytest.raises(RuntimeError, match="Action execution failed after 3 attempts"):
            automation.execute_action(action)
        
        # Should have tried 3 times total
        assert mock_pyautogui.click.call_count == 3
    
    @patch('modules.automation.pyautogui')
    def test_action_history_tracking(self, mock_pyautogui):
        """Test action history tracking functionality."""
        mock_pyautogui.size.return_value = (1920, 1080)
        automation = AutomationModule()
        
        # Execute some actions
        actions = [
            {"action": "click", "coordinates": [100, 200]},
            {"action": "type", "text": "test"}
        ]
        
        for action in actions:
            automation.execute_action(action)
        
        history = automation.get_action_history()
        assert len(history) == 2
        assert history[0]["action"]["action"] == "click"
        assert history[1]["action"]["action"] == "type"
        assert all(entry["status"] == "success" for entry in history)
        assert all("timestamp" in entry for entry in history)
    
    @patch('modules.automation.pyautogui')
    def test_action_history_with_failures(self, mock_pyautogui):
        """Test action history tracking with failed actions."""
        mock_pyautogui.size.return_value = (1920, 1080)
        mock_pyautogui.click.side_effect = Exception("Click failed")
        
        automation = AutomationModule(max_retries=0)
        
        action = {"action": "click", "coordinates": [100, 200]}
        
        with pytest.raises(RuntimeError):
            automation.execute_action(action)
        
        history = automation.get_action_history()
        assert len(history) == 1
        assert history[0]["status"] == "failed"
        assert "error" in history[0]
    
    @patch('modules.automation.pyautogui')
    def test_get_action_history_with_limit(self, mock_pyautogui):
        """Test getting limited action history."""
        mock_pyautogui.size.return_value = (1920, 1080)
        automation = AutomationModule()
        
        # Execute multiple actions
        for i in range(5):
            action = {"action": "click", "coordinates": [100 + i, 200]}
            automation.execute_action(action)
        
        # Test getting limited history
        recent_history = automation.get_action_history(limit=3)
        assert len(recent_history) == 3
        
        # Test getting all history
        all_history = automation.get_action_history()
        assert len(all_history) == 5
    
    @patch('modules.automation.pyautogui')
    def test_clear_action_history(self, mock_pyautogui):
        """Test clearing action history."""
        mock_pyautogui.size.return_value = (1920, 1080)
        automation = AutomationModule()
        
        # Execute an action
        action = {"action": "click", "coordinates": [100, 200]}
        automation.execute_action(action)
        
        assert len(automation.get_action_history()) == 1
        
        automation.clear_action_history()
        assert len(automation.get_action_history()) == 0
    
    @patch('modules.automation.pyautogui')
    def test_failure_rate_calculation(self, mock_pyautogui):
        """Test failure rate calculation."""
        mock_pyautogui.size.return_value = (1920, 1080)
        # Set up mixed success/failure pattern
        mock_pyautogui.click.side_effect = [None, Exception("Fail"), None, Exception("Fail")]
        
        automation = AutomationModule(max_retries=0)
        
        actions = [
            {"action": "click", "coordinates": [100, 200]},  # Success
            {"action": "click", "coordinates": [200, 300]},  # Fail
            {"action": "click", "coordinates": [300, 400]},  # Success
            {"action": "click", "coordinates": [400, 500]}   # Fail
        ]
        
        for action in actions:
            try:
                automation.execute_action(action)
            except RuntimeError:
                pass  # Expected for failed actions
        
        failure_rate = automation.get_failure_rate()
        assert failure_rate == 50.0  # 2 out of 4 failed
    
    @patch('modules.automation.pyautogui')
    def test_validate_action_format(self, mock_pyautogui):
        """Test action format validation."""
        mock_pyautogui.size.return_value = (1920, 1080)
        automation = AutomationModule()
        
        # Valid actions
        valid_actions = [
            {"action": "click", "coordinates": [100, 200]},
            {"action": "double_click", "coordinates": [300, 400]},
            {"action": "type", "text": "Hello"},
            {"action": "scroll", "direction": "up", "amount": 100}
        ]
        
        for action in valid_actions:
            is_valid, message = automation.validate_action_format(action)
            assert is_valid, f"Action should be valid: {action}, Error: {message}"
        
        # Invalid actions
        invalid_actions = [
            {"action": "invalid_type"},
            {"action": "click"},  # Missing coordinates
            {"action": "click", "coordinates": [2000, 200]},  # Out of bounds
            {"action": "type"},  # Missing text
            {"action": "scroll", "direction": "diagonal"}  # Invalid direction
        ]
        
        for action in invalid_actions:
            is_valid, message = automation.validate_action_format(action)
            assert not is_valid, f"Action should be invalid: {action}"
    
    @patch('modules.automation.pyautogui')
    def test_set_retry_settings(self, mock_pyautogui):
        """Test updating retry settings."""
        mock_pyautogui.size.return_value = (1920, 1080)
        automation = AutomationModule()
        
        # Initial settings
        assert automation.max_retries == 3
        assert automation.retry_delay == 0.5
        
        # Update settings
        automation.set_retry_settings(max_retries=5, retry_delay=1.0)
        
        assert automation.max_retries == 5
        assert automation.retry_delay == 1.0
    
    @patch('modules.automation.pyautogui')
    def test_form_filling_workflow(self, mock_pyautogui):
        """Test a complete form filling workflow."""
        mock_pyautogui.size.return_value = (1920, 1080)
        automation = AutomationModule()
        
        # Simulate form filling actions
        form_actions = [
            {"action": "click", "coordinates": [300, 200]},  # Click first field
            {"action": "type", "text": "John Doe"},           # Enter name
            {"action": "click", "coordinates": [300, 250]},  # Click email field
            {"action": "type", "text": "john@example.com"},  # Enter email
            {"action": "click", "coordinates": [300, 300]},  # Click message field
            {"action": "type", "text": "Hello, this is a test message."},  # Enter message
            {"action": "click", "coordinates": [400, 350]}   # Click submit button
        ]
        
        result = automation.execute_action_sequence(form_actions)
        
        assert result["successful_actions"] == 7
        assert result["failed_actions"] == 0
        
        # Verify the sequence of calls
        assert mock_pyautogui.moveTo.call_count == 4  # 4 click actions
        assert mock_pyautogui.click.call_count == 4
        assert mock_pyautogui.typewrite.call_count == 3
    
    @patch('modules.automation.pyautogui')
    def test_web_navigation_workflow(self, mock_pyautogui):
        """Test a web navigation workflow with scrolling."""
        mock_pyautogui.size.return_value = (1920, 1080)
        automation = AutomationModule()
        
        # Simulate web navigation
        navigation_actions = [
            {"action": "click", "coordinates": [500, 100]},    # Click link
            {"action": "scroll", "direction": "down", "amount": 300},  # Scroll down
            {"action": "click", "coordinates": [600, 400]},    # Click another element
            {"action": "scroll", "direction": "up", "amount": 150},    # Scroll back up
            {"action": "double_click", "coordinates": [700, 200]}      # Double-click element
        ]
        
        result = automation.execute_action_sequence(navigation_actions)
        
        assert result["successful_actions"] == 5
        assert result["failed_actions"] == 0
        
        # Verify scroll actions
        mock_pyautogui.scroll.assert_any_call(-300)  # Scroll down
        mock_pyautogui.scroll.assert_any_call(150)   # Scroll up