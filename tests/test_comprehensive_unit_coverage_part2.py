# tests/test_comprehensive_unit_coverage_part2.py
"""
Comprehensive Unit Test Coverage for AURA Modules - Part 2

This file continues comprehensive unit test coverage for AutomationModule,
ErrorHandler, and other components with proper mocking and edge case testing.
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch, MagicMock, call
import pyautogui
from dataclasses import dataclass
from typing import Dict, Any, List

# Import modules to test
from modules.automation import AutomationModule
from modules.error_handler import (
    ErrorHandler, ErrorSeverity, ErrorCategory, ErrorInfo,
    with_error_handling, global_error_handler
)
from orchestrator import Orchestrator, ExecutionStep


class TestAutomationModuleComprehensive:
    """Comprehensive unit tests for AutomationModule."""
    
    @pytest.fixture
    def automation_module(self):
        """Create AutomationModule instance for testing."""
        with patch('modules.automation.pyautogui.size', return_value=(1920, 1080)):
            return AutomationModule(max_retries=2, retry_delay=0.1)
    
    def test_initialization(self, automation_module):
        """Test AutomationModule initialization."""
        assert automation_module.screen_width == 1920
        assert automation_module.screen_height == 1080
        assert automation_module.max_retries == 2
        assert automation_module.retry_delay == 0.1
        assert automation_module.action_history == []
    
    def test_validate_coordinates_valid(self, automation_module):
        """Test coordinate validation with valid coordinates."""
        assert automation_module._validate_coordinates(100, 200) is True
        assert automation_module._validate_coordinates(0, 0) is True
        assert automation_module._validate_coordinates(1920, 1080) is True
    
    def test_validate_coordinates_invalid(self, automation_module):
        """Test coordinate validation with invalid coordinates."""
        assert automation_module._validate_coordinates(-1, 200) is False
        assert automation_module._validate_coordinates(100, -1) is False
        assert automation_module._validate_coordinates(1921, 200) is False
        assert automation_module._validate_coordinates(100, 1081) is False
    
    def test_validate_text_input_valid(self, automation_module):
        """Test text input validation with valid text."""
        assert automation_module._validate_text_input("Hello World") is True
        assert automation_module._validate_text_input("") is True
        assert automation_module._validate_text_input("A" * 1000) is True
    
    def test_validate_text_input_invalid(self, automation_module):
        """Test text input validation with invalid text."""
        assert automation_module._validate_text_input(123) is False
        assert automation_module._validate_text_input(None) is False
        assert automation_module._validate_text_input("A" * 10001) is False
    
    def test_execute_action_invalid_structure(self, automation_module):
        """Test execute_action with invalid action structure."""
        # Test non-dict action
        with pytest.raises(ValueError, match="Action must be a dictionary"):
            automation_module.execute_action("invalid")
        
        # Test missing action type
        with pytest.raises(ValueError, match="Action type is required"):
            automation_module.execute_action({})
        
        # Test invalid action type
        with pytest.raises(ValueError, match="Unsupported action type"):
            automation_module.execute_action({"action": "invalid_action"})
    
    @patch('modules.automation.pyautogui.moveTo')
    @patch('modules.automation.pyautogui.click')
    @patch('modules.automation.pyautogui.position')
    def test_execute_click_success(self, mock_position, mock_click, mock_moveTo, automation_module):
        """Test successful click action execution."""
        mock_position.return_value = Mock(x=100, y=100)  # Not at failsafe position
        
        action = {
            "action": "click",
            "coordinates": [500, 300]
        }
        
        automation_module.execute_action(action)
        
        mock_moveTo.assert_called_once_with(500, 300, duration=0.25)
        mock_click.assert_called_once()
        
        # Check action history
        assert len(automation_module.action_history) == 1
        assert automation_module.action_history[0]["status"] == "success"
    
    @patch('modules.automation.pyautogui.moveTo')
    @patch('modules.automation.pyautogui.doubleClick')
    @patch('modules.automation.pyautogui.position')
    def test_execute_double_click_success(self, mock_position, mock_double_click, mock_moveTo, automation_module):
        """Test successful double click action execution."""
        mock_position.return_value = Mock(x=100, y=100)
        
        action = {
            "action": "double_click",
            "coordinates": [600, 400]
        }
        
        automation_module.execute_action(action)
        
        mock_moveTo.assert_called_once_with(600, 400, duration=0.25)
        mock_double_click.assert_called_once()
    
    @patch('modules.automation.pyautogui.typewrite')
    @patch('modules.automation.pyautogui.position')
    def test_execute_type_success(self, mock_position, mock_typewrite, automation_module):
        """Test successful type action execution."""
        mock_position.return_value = Mock(x=100, y=100)
        
        action = {
            "action": "type",
            "text": "Hello World"
        }
        
        automation_module.execute_action(action)
        
        mock_typewrite.assert_called_once_with("Hello World", interval=0.05)
    
    @patch('modules.automation.pyautogui.scroll')
    @patch('modules.automation.pyautogui.position')
    def test_execute_scroll_directions(self, mock_position, mock_scroll, automation_module):
        """Test scroll action in different directions."""
        mock_position.return_value = Mock(x=100, y=100)
        
        # Test scroll up
        action = {"action": "scroll", "direction": "up", "amount": 200}
        automation_module.execute_action(action)
        mock_scroll.assert_called_with(200)
        
        # Test scroll down
        action = {"action": "scroll", "direction": "down", "amount": 150}
        automation_module.execute_action(action)
        mock_scroll.assert_called_with(-150)
    
    @patch('modules.automation.pyautogui.hscroll')
    @patch('modules.automation.pyautogui.position')
    def test_execute_scroll_horizontal(self, mock_position, mock_hscroll, automation_module):
        """Test horizontal scroll actions."""
        mock_position.return_value = Mock(x=100, y=100)
        
        # Test scroll left
        action = {"action": "scroll", "direction": "left", "amount": 100}
        automation_module.execute_action(action)
        mock_hscroll.assert_called_with(-100)
        
        # Test scroll right
        action = {"action": "scroll", "direction": "right", "amount": 75}
        automation_module.execute_action(action)
        mock_hscroll.assert_called_with(75)
    
    @patch('modules.automation.pyautogui.scroll')
    @patch('modules.automation.pyautogui.position')
    def test_execute_scroll_default_values(self, mock_position, mock_scroll, automation_module):
        """Test scroll action with default values."""
        mock_position.return_value = Mock(x=100, y=100)
        
        action = {"action": "scroll"}  # No direction or amount specified
        
        automation_module.execute_action(action)
        
        # Should use default direction "up" and amount from config
        mock_scroll.assert_called_once_with(100)  # Default SCROLL_AMOUNT
    
    @patch('modules.automation.pyautogui.position')
    def test_execute_action_failsafe_triggered(self, mock_position, automation_module):
        """Test action execution when PyAutoGUI failsafe is triggered."""
        mock_position.return_value = Mock(x=0, y=0)  # Failsafe position
        
        action = {"action": "click", "coordinates": [100, 200]}
        
        with pytest.raises(RuntimeError, match="Automation stopped by failsafe"):
            automation_module.execute_action(action)
    
    @patch('modules.automation.pyautogui.position')
    @patch('modules.automation.pyautogui.moveTo')
    @patch('modules.automation.pyautogui.click')
    def test_execute_action_retry_mechanism(self, mock_click, mock_moveTo, mock_position, automation_module):
        """Test action execution retry mechanism."""
        mock_position.return_value = Mock(x=100, y=100)
        
        # First attempt fails, second succeeds
        mock_click.side_effect = [Exception("Click failed"), None]
        
        action = {"action": "click", "coordinates": [100, 200]}
        
        with patch('modules.automation.time.sleep'):  # Speed up test
            automation_module.execute_action(action)
        
        # Should have been called twice (initial + 1 retry)
        assert mock_click.call_count == 2
        
        # Check action history shows success after retry
        assert len(automation_module.action_history) == 1
        assert automation_module.action_history[0]["status"] == "success"
        assert automation_module.action_history[0]["attempts"] == 2
    
    @patch('modules.automation.pyautogui.position')
    @patch('modules.automation.pyautogui.moveTo')
    @patch('modules.automation.pyautogui.click')
    def test_execute_action_all_retries_fail(self, mock_click, mock_moveTo, mock_position, automation_module):
        """Test action execution when all retries fail."""
        mock_position.return_value = Mock(x=100, y=100)
        mock_click.side_effect = Exception("Click always fails")
        
        action = {"action": "click", "coordinates": [100, 200]}
        
        with patch('modules.automation.time.sleep'):  # Speed up test
            with pytest.raises(RuntimeError, match="Action execution failed after"):
                automation_module.execute_action(action)
        
        # Should have tried max_retries + 1 times
        assert mock_click.call_count == automation_module.max_retries + 1
        
        # Check action history shows failure
        assert len(automation_module.action_history) == 1
        assert automation_module.action_history[0]["status"] == "failed"
    
    def test_execute_action_sequence_success(self, automation_module):
        """Test successful action sequence execution."""
        actions = [
            {"action": "click", "coordinates": [100, 200]},
            {"action": "type", "text": "test"},
            {"action": "scroll", "direction": "up", "amount": 100}
        ]
        
        with patch.object(automation_module, 'execute_action') as mock_execute:
            result = automation_module.execute_action_sequence(actions)
        
        assert result["total_actions"] == 3
        assert result["successful_actions"] == 3
        assert result["failed_actions"] == 0
        assert len(result["errors"]) == 0
        assert mock_execute.call_count == 3
    
    def test_execute_action_sequence_with_failures(self, automation_module):
        """Test action sequence execution with some failures."""
        actions = [
            {"action": "click", "coordinates": [100, 200]},
            {"action": "invalid_action"},  # This will fail
            {"action": "type", "text": "test"}
        ]
        
        with patch.object(automation_module, 'execute_action') as mock_execute:
            # First and third succeed, second fails
            mock_execute.side_effect = [None, Exception("Invalid action"), None]
            
            result = automation_module.execute_action_sequence(actions, stop_on_error=False)
        
        assert result["total_actions"] == 3
        assert result["successful_actions"] == 2
        assert result["failed_actions"] == 1
        assert len(result["errors"]) == 1
        assert "Action 2 failed" in result["errors"][0]
    
    def test_execute_action_sequence_stop_on_error(self, automation_module):
        """Test action sequence execution with stop_on_error=True."""
        actions = [
            {"action": "click", "coordinates": [100, 200]},
            {"action": "invalid_action"},  # This will fail
            {"action": "type", "text": "test"}  # This won't be executed
        ]
        
        with patch.object(automation_module, 'execute_action') as mock_execute:
            mock_execute.side_effect = [None, Exception("Invalid action"), None]
            
            result = automation_module.execute_action_sequence(actions, stop_on_error=True)
        
        assert result["total_actions"] == 3
        assert result["successful_actions"] == 1
        assert result["failed_actions"] == 1
        assert mock_execute.call_count == 2  # Third action not executed
    
    def test_get_screen_size(self, automation_module):
        """Test getting screen size."""
        width, height = automation_module.get_screen_size()
        assert width == 1920
        assert height == 1080
    
    @patch('modules.automation.pyautogui.position')
    def test_get_mouse_position(self, mock_position, automation_module):
        """Test getting mouse position."""
        mock_position.return_value = (500, 300)
        
        x, y = automation_module.get_mouse_position()
        assert x == 500
        assert y == 300
    
    def test_get_action_history(self, automation_module):
        """Test getting action history."""
        # Add some mock history
        automation_module.action_history = [
            {"action": "click", "status": "success"},
            {"action": "type", "status": "failed"},
            {"action": "scroll", "status": "success"}
        ]
        
        # Test getting all history
        history = automation_module.get_action_history()
        assert len(history) == 3
        
        # Test getting limited history
        limited_history = automation_module.get_action_history(limit=2)
        assert len(limited_history) == 2
        assert limited_history == automation_module.action_history[-2:]
    
    def test_clear_action_history(self, automation_module):
        """Test clearing action history."""
        automation_module.action_history = [{"action": "test"}]
        
        automation_module.clear_action_history()
        
        assert len(automation_module.action_history) == 0
    
    def test_get_failure_rate(self, automation_module):
        """Test calculating failure rate."""
        # Test with no history
        assert automation_module.get_failure_rate() == 0.0
        
        # Test with mixed success/failure
        automation_module.action_history = [
            {"status": "success"},
            {"status": "failed"},
            {"status": "success"},
            {"status": "failed"}
        ]
        
        failure_rate = automation_module.get_failure_rate()
        assert failure_rate == 50.0  # 2 failures out of 4 actions
    
    def test_validate_action_format_valid_actions(self, automation_module):
        """Test action format validation with valid actions."""
        # Valid click action
        is_valid, error = automation_module.validate_action_format({
            "action": "click",
            "coordinates": [100, 200]
        })
        assert is_valid is True
        assert "valid" in error
        
        # Valid type action
        is_valid, error = automation_module.validate_action_format({
            "action": "type",
            "text": "Hello"
        })
        assert is_valid is True
        
        # Valid scroll action
        is_valid, error = automation_module.validate_action_format({
            "action": "scroll",
            "direction": "up",
            "amount": 100
        })
        assert is_valid is True
    
    def test_validate_action_format_invalid_actions(self, automation_module):
        """Test action format validation with invalid actions."""
        # Missing action type
        is_valid, error = automation_module.validate_action_format({})
        assert is_valid is False
        assert "Action type is required" in error
        
        # Invalid action type
        is_valid, error = automation_module.validate_action_format({
            "action": "invalid_action"
        })
        assert is_valid is False
        assert "Unsupported action type" in error
        
        # Click without coordinates
        is_valid, error = automation_module.validate_action_format({
            "action": "click"
        })
        assert is_valid is False
        assert "requires coordinates" in error
        
        # Type without text
        is_valid, error = automation_module.validate_action_format({
            "action": "type"
        })
        assert is_valid is False
        assert "requires text parameter" in error
    
    def test_set_retry_settings(self, automation_module):
        """Test updating retry settings."""
        automation_module.set_retry_settings(max_retries=5, retry_delay=0.5)
        
        assert automation_module.max_retries == 5
        assert automation_module.retry_delay == 0.5
    
    def test_fill_form_no_forms(self, automation_module):
        """Test form filling with no forms in data."""
        form_data = {"forms": []}
        form_values = {"username": "test"}
        
        result = automation_module.fill_form(form_data, form_values)
        
        assert result["total_fields"] == 0
        assert len(result["errors"]) > 0
        assert "No forms found" in result["errors"][0]
    
    def test_fill_form_success(self, automation_module):
        """Test successful form filling."""
        form_data = {
            "forms": [{
                "form_id": "login_form",
                "fields": [
                    {
                        "type": "text_input",
                        "label": "username",
                        "coordinates": [100, 200, 300, 230]
                    },
                    {
                        "type": "password",
                        "label": "password",
                        "coordinates": [100, 250, 300, 280]
                    }
                ]
            }]
        }
        form_values = {
            "username": "testuser",
            "password": "testpass"
        }
        
        with patch.object(automation_module, '_fill_form_field') as mock_fill:
            mock_fill.return_value = {"status": "filled", "field": "test"}
            
            with patch.object(automation_module, '_submit_form') as mock_submit:
                mock_submit.return_value = {"success": True}
                
                result = automation_module.fill_form(form_data, form_values, confirm_before_submit=False)
        
        assert result["total_fields"] == 2
        assert result["filled_fields"] == 2
        assert result["form_submitted"] is True
        assert mock_fill.call_count == 2
    
    def test_fill_text_field_success(self, automation_module):
        """Test successful text field filling."""
        with patch.object(automation_module, 'execute_action') as mock_execute:
            with patch('modules.automation.pyautogui.hotkey') as mock_hotkey:
                with patch('modules.automation.time.sleep'):
                    result = automation_module._fill_text_field(100, 200, "test value", "username")
        
        assert result["status"] == "filled"
        assert result["field"] == "username"
        assert result["value"] == "test value"
        
        # Should have called click and type actions
        assert mock_execute.call_count == 2
        mock_hotkey.assert_called_with('ctrl', 'a')  # Clear existing content
    
    def test_fill_text_field_failure(self, automation_module):
        """Test text field filling failure."""
        with patch.object(automation_module, 'execute_action', side_effect=Exception("Action failed")):
            result = automation_module._fill_text_field(100, 200, "test value", "username")
        
        assert result["status"] == "failed"
        assert result["field"] == "username"
        assert "Action failed" in result["error"]
    
    def test_fill_select_field_with_matching_option(self, automation_module):
        """Test select field filling with matching option."""
        options = ["Option 1", "Option 2", "Option 3"]
        
        with patch.object(automation_module, 'execute_action') as mock_execute:
            with patch('modules.automation.pyautogui.press') as mock_press:
                with patch('modules.automation.time.sleep'):
                    result = automation_module._fill_select_field(100, 200, "option 2", "dropdown", options)
        
        assert result["status"] == "filled"
        assert result["field"] == "dropdown"
        assert result["value"] == "Option 2"  # Should match case-insensitively
        
        mock_press.assert_called_with('enter')
    
    def test_fill_select_field_no_matching_option(self, automation_module):
        """Test select field filling with no matching option."""
        options = ["Option 1", "Option 2", "Option 3"]
        
        with patch.object(automation_module, 'execute_action') as mock_execute:
            with patch('modules.automation.pyautogui.press') as mock_press:
                with patch('modules.automation.time.sleep'):
                    result = automation_module._fill_select_field(100, 200, "Option 4", "dropdown", options)
        
        assert result["status"] == "filled"
        assert result["field"] == "dropdown"
        assert result["value"] == "Option 4"
        assert "warning" in result
        assert "not found in dropdown" in result["warning"]


class TestErrorHandlerComprehensive:
    """Comprehensive unit tests for ErrorHandler."""
    
    @pytest.fixture
    def error_handler(self):
        """Create ErrorHandler instance for testing."""
        return ErrorHandler()
    
    def test_initialization(self, error_handler):
        """Test ErrorHandler initialization."""
        assert error_handler.error_history == []
        assert error_handler.error_counts == {}
        assert len(error_handler.recovery_strategies) > 0
        assert error_handler.lock is not None
    
    def test_classify_error_network_errors(self, error_handler):
        """Test error classification for network-related errors."""
        assert error_handler._classify_error(Exception("Connection failed")) == ErrorCategory.NETWORK_ERROR
        assert error_handler._classify_error(Exception("DNS resolution failed")) == ErrorCategory.NETWORK_ERROR
        assert error_handler._classify_error(Exception("Socket error")) == ErrorCategory.NETWORK_ERROR
    
    def test_classify_error_api_errors(self, error_handler):
        """Test error classification for API-related errors."""
        assert error_handler._classify_error(Exception("API request failed")) == ErrorCategory.API_ERROR
        assert error_handler._classify_error(Exception("HTTP 500 error")) == ErrorCategory.API_ERROR
        assert error_handler._classify_error(Exception("Invalid response status")) == ErrorCategory.API_ERROR
    
    def test_classify_error_timeout_errors(self, error_handler):
        """Test error classification for timeout errors."""
        assert error_handler._classify_error(Exception("Request timed out")) == ErrorCategory.TIMEOUT_ERROR
        assert error_handler._classify_error(Exception("Operation timeout")) == ErrorCategory.TIMEOUT_ERROR
    
    def test_classify_error_validation_errors(self, error_handler):
        """Test error classification for validation errors."""
        assert error_handler._classify_error(Exception("Invalid format")) == ErrorCategory.VALIDATION_ERROR
        assert error_handler._classify_error(Exception("Parse error")) == ErrorCategory.VALIDATION_ERROR
        assert error_handler._classify_error(Exception("Validation failed")) == ErrorCategory.VALIDATION_ERROR
    
    def test_classify_error_permission_errors(self, error_handler):
        """Test error classification for permission errors."""
        assert error_handler._classify_error(Exception("Access denied")) == ErrorCategory.PERMISSION_ERROR
        assert error_handler._classify_error(Exception("Permission denied")) == ErrorCategory.PERMISSION_ERROR
        assert error_handler._classify_error(Exception("Forbidden")) == ErrorCategory.PERMISSION_ERROR
    
    def test_classify_error_hardware_errors(self, error_handler):
        """Test error classification for hardware errors."""
        assert error_handler._classify_error(Exception("Microphone not found")) == ErrorCategory.HARDWARE_ERROR
        assert error_handler._classify_error(Exception("Device error")) == ErrorCategory.HARDWARE_ERROR
        assert error_handler._classify_error(Exception("Screen capture failed")) == ErrorCategory.HARDWARE_ERROR
    
    def test_classify_error_configuration_errors(self, error_handler):
        """Test error classification for configuration errors."""
        assert error_handler._classify_error(Exception("Config file missing")) == ErrorCategory.CONFIGURATION_ERROR
        assert error_handler._classify_error(Exception("API key not set")) == ErrorCategory.CONFIGURATION_ERROR
        assert error_handler._classify_error(Exception("Setting invalid")) == ErrorCategory.CONFIGURATION_ERROR
    
    def test_classify_error_resource_errors(self, error_handler):
        """Test error classification for resource errors."""
        assert error_handler._classify_error(Exception("Out of memory")) == ErrorCategory.RESOURCE_ERROR
        assert error_handler._classify_error(Exception("Disk full")) == ErrorCategory.RESOURCE_ERROR
        assert error_handler._classify_error(Exception("Resource limit exceeded")) == ErrorCategory.RESOURCE_ERROR
    
    def test_classify_error_processing_errors(self, error_handler):
        """Test error classification for processing errors."""
        assert error_handler._classify_error(Exception("Processing failed")) == ErrorCategory.PROCESSING_ERROR
        assert error_handler._classify_error(Exception("Computation error")) == ErrorCategory.PROCESSING_ERROR
        assert error_handler._classify_error(Exception("Calculation failed")) == ErrorCategory.PROCESSING_ERROR
    
    def test_classify_error_by_exception_type(self, error_handler):
        """Test error classification by exception type."""
        import requests
        
        # Test timeout exception type
        timeout_error = requests.exceptions.Timeout("Timeout")
        assert error_handler._classify_error(timeout_error) == ErrorCategory.TIMEOUT_ERROR
        
        # Test connection exception type
        connection_error = requests.exceptions.ConnectionError("Connection failed")
        assert error_handler._classify_error(connection_error) == ErrorCategory.NETWORK_ERROR
        
        # Test value error type
        value_error = ValueError("Invalid value")
        assert error_handler._classify_error(value_error) == ErrorCategory.VALIDATION_ERROR
        
        # Test type error
        type_error = TypeError("Invalid type")
        assert error_handler._classify_error(type_error) == ErrorCategory.VALIDATION_ERROR
    
    def test_classify_error_unknown(self, error_handler):
        """Test error classification for unknown errors."""
        assert error_handler._classify_error(Exception("Something weird happened")) == ErrorCategory.UNKNOWN_ERROR
    
    def test_assess_severity_critical(self, error_handler):
        """Test severity assessment for critical errors."""
        assert error_handler._assess_severity(Exception("test"), ErrorCategory.CONFIGURATION_ERROR) == ErrorSeverity.CRITICAL
        assert error_handler._assess_severity(Exception("test"), ErrorCategory.PERMISSION_ERROR) == ErrorSeverity.CRITICAL
    
    def test_assess_severity_high(self, error_handler):
        """Test severity assessment for high severity errors."""
        assert error_handler._assess_severity(Exception("test"), ErrorCategory.HARDWARE_ERROR) == ErrorSeverity.HIGH
        assert error_handler._assess_severity(Exception("test"), ErrorCategory.RESOURCE_ERROR) == ErrorSeverity.HIGH
    
    def test_assess_severity_medium(self, error_handler):
        """Test severity assessment for medium severity errors."""
        assert error_handler._assess_severity(Exception("test"), ErrorCategory.API_ERROR) == ErrorSeverity.MEDIUM
        assert error_handler._assess_severity(Exception("test"), ErrorCategory.NETWORK_ERROR) == ErrorSeverity.MEDIUM
        assert error_handler._assess_severity(Exception("test"), ErrorCategory.TIMEOUT_ERROR) == ErrorSeverity.MEDIUM
    
    def test_assess_severity_low(self, error_handler):
        """Test severity assessment for low severity errors."""
        assert error_handler._assess_severity(Exception("test"), ErrorCategory.VALIDATION_ERROR) == ErrorSeverity.LOW
        assert error_handler._assess_severity(Exception("test"), ErrorCategory.PROCESSING_ERROR) == ErrorSeverity.LOW
        assert error_handler._assess_severity(Exception("test"), ErrorCategory.UNKNOWN_ERROR) == ErrorSeverity.LOW
    
    def test_generate_user_message(self, error_handler):
        """Test user-friendly message generation."""
        messages = {
            ErrorCategory.API_ERROR: "communicating with my services",
            ErrorCategory.NETWORK_ERROR: "network connectivity issues",
            ErrorCategory.TIMEOUT_ERROR: "taking longer than expected",
            ErrorCategory.VALIDATION_ERROR: "invalid data",
            ErrorCategory.HARDWARE_ERROR: "accessing your hardware",
            ErrorCategory.CONFIGURATION_ERROR: "configuration issue",
            ErrorCategory.PROCESSING_ERROR: "processing your request",
            ErrorCategory.PERMISSION_ERROR: "necessary permissions",
            ErrorCategory.RESOURCE_ERROR: "resources are limited",
            ErrorCategory.UNKNOWN_ERROR: "unexpected error"
        }
        
        for category, expected_text in messages.items():
            message = error_handler._generate_user_message(Exception("test"), category)
            assert expected_text in message.lower()
    
    def test_generate_suggested_action(self, error_handler):
        """Test suggested action generation."""
        actions = {
            ErrorCategory.API_ERROR: "API configuration",
            ErrorCategory.NETWORK_ERROR: "internet connection",
            ErrorCategory.TIMEOUT_ERROR: "Wait a moment",
            ErrorCategory.VALIDATION_ERROR: "input format",
            ErrorCategory.HARDWARE_ERROR: "device connections",
            ErrorCategory.CONFIGURATION_ERROR: "configuration settings",
            ErrorCategory.PROCESSING_ERROR: "simpler request",
            ErrorCategory.PERMISSION_ERROR: "permissions",
            ErrorCategory.RESOURCE_ERROR: "other applications",
            ErrorCategory.UNKNOWN_ERROR: "restart"
        }
        
        for category, expected_text in actions.items():
            action = error_handler._generate_suggested_action(category)
            assert expected_text.lower() in action.lower()
    
    def test_handle_error_basic(self, error_handler):
        """Test basic error handling."""
        test_error = Exception("Test error")
        
        error_info = error_handler.handle_error(
            error=test_error,
            module="test_module",
            function="test_function"
        )
        
        assert error_info.message == "Test error"
        assert error_info.module == "test_module"
        assert error_info.function == "test_function"
        assert error_info.category is not None
        assert error_info.severity is not None
        assert error_info.timestamp > 0
        assert error_info.user_message is not None
    
    def test_handle_error_with_context(self, error_handler):
        """Test error handling with context information."""
        test_error = Exception("Test error")
        context = {"param1": "value1", "param2": 123}
        
        error_info = error_handler.handle_error(
            error=test_error,
            module="test_module",
            function="test_function",
            context=context
        )
        
        assert "Context: " in error_info.details
        assert "param1" in error_info.details
        assert "value1" in error_info.details
    
    def test_handle_error_with_custom_category_severity(self, error_handler):
        """Test error handling with custom category and severity."""
        test_error = Exception("Test error")
        
        error_info = error_handler.handle_error(
            error=test_error,
            module="test_module",
            function="test_function",
            category=ErrorCategory.API_ERROR,
            severity=ErrorSeverity.HIGH
        )
        
        assert error_info.category == ErrorCategory.API_ERROR
        assert error_info.severity == ErrorSeverity.HIGH
    
    def test_handle_error_with_custom_messages(self, error_handler):
        """Test error handling with custom user message and suggested action."""
        test_error = Exception("Test error")
        custom_user_message = "Custom user message"
        custom_suggested_action = "Custom suggested action"
        
        error_info = error_handler.handle_error(
            error=test_error,
            module="test_module",
            function="test_function",
            user_message=custom_user_message,
            suggested_action=custom_suggested_action
        )
        
        assert error_info.user_message == custom_user_message
        assert error_info.suggested_action == custom_suggested_action
    
    def test_handle_error_updates_statistics(self, error_handler):
        """Test that error handling updates error statistics."""
        initial_count = len(error_handler.error_history)
        
        test_error = Exception("Test error")
        error_handler.handle_error(
            error=test_error,
            module="test_module",
            function="test_function",
            category=ErrorCategory.API_ERROR
        )
        
        assert len(error_handler.error_history) == initial_count + 1
        assert error_handler.error_counts.get(ErrorCategory.API_ERROR.value, 0) >= 1
    
    def test_handle_error_history_limit(self, error_handler):
        """Test that error history is limited to prevent memory issues."""
        # Add many errors to test history limit
        for i in range(1005):  # More than the 1000 limit
            error_handler.handle_error(
                error=Exception(f"Test error {i}"),
                module="test_module",
                function="test_function"
            )
        
        # Should be limited to 1000
        assert len(error_handler.error_history) == 1000
    
    def test_handle_error_handler_failure(self, error_handler):
        """Test error handler behavior when it fails internally."""
        # Simulate error handler failure by patching a method to raise exception
        with patch.object(error_handler, '_classify_error', side_effect=Exception("Handler failed")):
            error_info = error_handler.handle_error(
                error=Exception("Original error"),
                module="test_module",
                function="test_function"
            )
        
        # Should return fallback error info
        assert error_info.error_id == "error_handler_failure"
        assert error_info.category == ErrorCategory.UNKNOWN_ERROR
        assert error_info.severity == ErrorSeverity.CRITICAL
        assert not error_info.recoverable
    
    def test_attempt_recovery_success(self, error_handler):
        """Test successful error recovery."""
        error_info = ErrorInfo(
            error_id="test_error",
            category=ErrorCategory.API_ERROR,
            severity=ErrorSeverity.MEDIUM,
            message="Test error",
            details="Test details",
            module="test_module",
            function="test_function",
            timestamp=time.time(),
            recoverable=True
        )
        
        # Mock recovery strategy to return success
        with patch.object(error_handler, '_recover_api_error', return_value=True):
            result = error_handler.attempt_recovery(error_info)
        
        assert result is True
    
    def test_attempt_recovery_failure(self, error_handler):
        """Test failed error recovery."""
        error_info = ErrorInfo(
            error_id="test_error",
            category=ErrorCategory.API_ERROR,
            severity=ErrorSeverity.MEDIUM,
            message="Test error",
            details="Test details",
            module="test_module",
            function="test_function",
            timestamp=time.time(),
            recoverable=True
        )
        
        # Mock recovery strategy to return failure
        with patch.object(error_handler, '_recover_api_error', return_value=False):
            result = error_handler.attempt_recovery(error_info)
        
        assert result is False
    
    def test_attempt_recovery_non_recoverable(self, error_handler):
        """Test recovery attempt on non-recoverable error."""
        error_info = ErrorInfo(
            error_id="test_error",
            category=ErrorCategory.API_ERROR,
            severity=ErrorSeverity.MEDIUM,
            message="Test error",
            details="Test details",
            module="test_module",
            function="test_function",
            timestamp=time.time(),
            recoverable=False
        )
        
        result = error_handler.attempt_recovery(error_info)
        assert result is False
    
    def test_attempt_recovery_no_strategy(self, error_handler):
        """Test recovery attempt with no registered strategy."""
        error_info = ErrorInfo(
            error_id="test_error",
            category=ErrorCategory.UNKNOWN_ERROR,
            severity=ErrorSeverity.MEDIUM,
            message="Test error",
            details="Test details",
            module="test_module",
            function="test_function",
            timestamp=time.time(),
            recoverable=True
        )
        
        # Remove strategy for unknown errors
        if ErrorCategory.UNKNOWN_ERROR in error_handler.recovery_strategies:
            del error_handler.recovery_strategies[ErrorCategory.UNKNOWN_ERROR]
        
        result = error_handler.attempt_recovery(error_info)
        assert result is False
    
    def test_attempt_recovery_strategy_exception(self, error_handler):
        """Test recovery attempt when strategy raises exception."""
        error_info = ErrorInfo(
            error_id="test_error",
            category=ErrorCategory.API_ERROR,
            severity=ErrorSeverity.MEDIUM,
            message="Test error",
            details="Test details",
            module="test_module",
            function="test_function",
            timestamp=time.time(),
            recoverable=True
        )
        
        # Mock recovery strategy to raise exception
        with patch.object(error_handler, '_recover_api_error', side_effect=Exception("Recovery failed")):
            result = error_handler.attempt_recovery(error_info)
        
        assert result is False
    
    def test_recovery_strategies_exist(self, error_handler):
        """Test that recovery strategies are registered for all categories."""
        expected_categories = [
            ErrorCategory.API_ERROR,
            ErrorCategory.NETWORK_ERROR,
            ErrorCategory.TIMEOUT_ERROR,
            ErrorCategory.VALIDATION_ERROR,
            ErrorCategory.HARDWARE_ERROR,
            ErrorCategory.CONFIGURATION_ERROR,
            ErrorCategory.PROCESSING_ERROR,
            ErrorCategory.PERMISSION_ERROR,
            ErrorCategory.RESOURCE_ERROR
        ]
        
        for category in expected_categories:
            assert category in error_handler.recovery_strategies
            assert callable(error_handler.recovery_strategies[category])
    
    def test_recovery_strategy_api_error(self, error_handler):
        """Test API error recovery strategy."""
        error_info = Mock()
        error_info.retry_count = 1
        
        with patch('modules.error_handler.time.sleep') as mock_sleep:
            result = error_handler._recover_api_error(error_info)
        
        assert result is True
        mock_sleep.assert_called_once()
    
    def test_recovery_strategy_network_error(self, error_handler):
        """Test network error recovery strategy."""
        error_info = Mock()
        error_info.retry_count = 0
        
        with patch('modules.error_handler.time.sleep') as mock_sleep:
            result = error_handler._recover_network_error(error_info)
        
        assert result is True
        mock_sleep.assert_called_once_with(5)  # 5 * (0 + 1)
    
    def test_recovery_strategy_timeout_error(self, error_handler):
        """Test timeout error recovery strategy."""
        error_info = Mock()
        error_info.retry_count = 2
        
        with patch('modules.error_handler.time.sleep') as mock_sleep:
            result = error_handler._recover_timeout_error(error_info)
        
        assert result is True
        mock_sleep.assert_called_once_with(9)  # 3 ** 2
    
    def test_recovery_strategy_validation_error(self, error_handler):
        """Test validation error recovery strategy."""
        error_info = Mock()
        
        result = error_handler._recover_validation_error(error_info)
        
        # Validation errors usually need manual intervention
        assert result is False
    
    def test_recovery_strategy_hardware_error(self, error_handler):
        """Test hardware error recovery strategy."""
        error_info = Mock()
        
        with patch('modules.error_handler.time.sleep') as mock_sleep:
            result = error_handler._recover_hardware_error(error_info)
        
        assert result is True
        mock_sleep.assert_called_once_with(1)
    
    def test_recovery_strategy_configuration_error(self, error_handler):
        """Test configuration error recovery strategy."""
        error_info = Mock()
        
        result = error_handler._recover_configuration_error(error_info)
        
        # Configuration errors usually need manual intervention
        assert result is False
    
    def test_recovery_strategy_processing_error(self, error_handler):
        """Test processing error recovery strategy."""
        error_info = Mock()
        
        with patch('modules.error_handler.time.sleep') as mock_sleep:
            result = error_handler._recover_processing_error(error_info)
        
        assert result is True
        mock_sleep.assert_called_once_with(0.5)
    
    def test_recovery_strategy_permission_error(self, error_handler):
        """Test permission error recovery strategy."""
        error_info = Mock()
        
        result = error_handler._recover_permission_error(error_info)
        
        # Permission errors usually need manual intervention
        assert result is False
    
    def test_recovery_strategy_resource_error(self, error_handler):
        """Test resource error recovery strategy."""
        error_info = Mock()
        
        with patch('modules.error_handler.time.sleep') as mock_sleep:
            result = error_handler._recover_resource_error(error_info)
        
        assert result is True
        mock_sleep.assert_called_once_with(2)
    
    def test_get_error_statistics_empty(self, error_handler):
        """Test error statistics with no errors."""
        stats = error_handler.get_error_statistics()
        
        assert stats["total_errors"] == 0
        assert stats["error_rate"] == 0.0
        assert stats["categories"] == {}
        assert stats["severities"] == {}
        assert stats["recent_errors"] == []
    
    def test_get_error_statistics_with_errors(self, error_handler):
        """Test error statistics with some errors."""
        # Add some test errors
        for i in range(5):
            error_handler.handle_error(
                error=Exception(f"Test error {i}"),
                module="test_module",
                function="test_function",
                category=ErrorCategory.API_ERROR,
                severity=ErrorSeverity.MEDIUM
            )
        
        stats = error_handler.get_error_statistics()
        
        assert stats["total_errors"] == 5
        assert stats["error_rate"] > 0
        assert ErrorCategory.API_ERROR.value in stats["categories"]
        assert stats["categories"][ErrorCategory.API_ERROR.value] == 5
        assert ErrorSeverity.MEDIUM.value in stats["severities"]
        assert stats["severities"][ErrorSeverity.MEDIUM.value] == 5
        assert len(stats["recent_errors"]) == 5
    
    def test_get_error_statistics_recent_errors_limit(self, error_handler):
        """Test that recent errors are limited to last 10."""
        # Add 15 test errors
        for i in range(15):
            error_handler.handle_error(
                error=Exception(f"Test error {i}"),
                module="test_module",
                function="test_function"
            )
        
        stats = error_handler.get_error_statistics()
        
        assert stats["total_errors"] == 15
        assert len(stats["recent_errors"]) == 10  # Limited to last 10


class TestWithErrorHandlingDecorator:
    """Test the with_error_handling decorator."""
    
    def test_decorator_success(self):
        """Test decorator with successful function execution."""
        @with_error_handling(max_retries=2)
        def test_function():
            return "success"
        
        result = test_function()
        assert result == "success"
    
    def test_decorator_with_retries(self):
        """Test decorator with retries."""
        call_count = 0
        
        @with_error_handling(max_retries=2, retry_delay=0.01)
        def test_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("Temporary failure")
            return "success"
        
        result = test_function()
        assert result == "success"
        assert call_count == 2
    
    def test_decorator_all_retries_fail(self):
        """Test decorator when all retries fail."""
        @with_error_handling(max_retries=2, retry_delay=0.01)
        def test_function():
            raise Exception("Always fails")
        
        with pytest.raises(Exception, match="Always fails"):
            test_function()
    
    def test_decorator_with_fallback_return(self):
        """Test decorator with fallback return value."""
        @with_error_handling(max_retries=1, fallback_return="fallback")
        def test_function():
            raise Exception("Always fails")
        
        result = test_function()
        assert result == "fallback"
    
    def test_decorator_with_custom_category_severity(self):
        """Test decorator with custom category and severity."""
        @with_error_handling(
            category=ErrorCategory.API_ERROR,
            severity=ErrorSeverity.HIGH,
            max_retries=1,
            fallback_return="fallback"
        )
        def test_function():
            raise Exception("API error")
        
        result = test_function()
        assert result == "fallback"
    
    def test_decorator_with_custom_user_message(self):
        """Test decorator with custom user message."""
        @with_error_handling(
            user_message="Custom error message",
            max_retries=1,
            fallback_return="fallback"
        )
        def test_function():
            raise Exception("Error")
        
        result = test_function()
        assert result == "fallback"
    
    def test_decorator_preserves_function_metadata(self):
        """Test that decorator preserves function metadata."""
        @with_error_handling()
        def test_function():
            """Test function docstring."""
            return "success"
        
        assert test_function.__name__ == "test_function"
        assert test_function.__doc__ == "Test function docstring."


if __name__ == "__main__":
    pytest.main([__file__, "-v"])