# tests/test_automation.py
"""
Unit tests for the AutomationModule.

Tests GUI automation functionality with mocked PyAutoGUI to avoid
actual mouse/keyboard actions during testing.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from modules.automation import AutomationModule


class TestAutomationModule:
    """Test cases for AutomationModule class."""
    
    @patch('modules.automation.pyautogui')
    def test_init(self, mock_pyautogui):
        """Test AutomationModule initialization."""
        mock_pyautogui.size.return_value = (1920, 1080)
        
        automation = AutomationModule()
        
        assert automation.screen_width == 1920
        assert automation.screen_height == 1080
        mock_pyautogui.size.assert_called_once()
    
    def test_validate_coordinates_valid(self):
        """Test coordinate validation with valid coordinates."""
        with patch('modules.automation.pyautogui.size', return_value=(1920, 1080)):
            automation = AutomationModule()
            
            assert automation._validate_coordinates(100, 200) is True
            assert automation._validate_coordinates(0, 0) is True
            assert automation._validate_coordinates(1920, 1080) is True
    
    def test_validate_coordinates_invalid(self):
        """Test coordinate validation with invalid coordinates."""
        with patch('modules.automation.pyautogui.size', return_value=(1920, 1080)):
            automation = AutomationModule()
            
            assert automation._validate_coordinates(-1, 200) is False
            assert automation._validate_coordinates(100, -1) is False
            assert automation._validate_coordinates(1921, 200) is False
            assert automation._validate_coordinates(100, 1081) is False
    
    def test_validate_text_input_valid(self):
        """Test text input validation with valid text."""
        with patch('modules.automation.pyautogui.size', return_value=(1920, 1080)):
            automation = AutomationModule()
            
            assert automation._validate_text_input("Hello World") is True
            assert automation._validate_text_input("") is True
            assert automation._validate_text_input("A" * 1000) is True
    
    def test_validate_text_input_invalid(self):
        """Test text input validation with invalid text."""
        with patch('modules.automation.pyautogui.size', return_value=(1920, 1080)):
            automation = AutomationModule()
            
            assert automation._validate_text_input(123) is False
            assert automation._validate_text_input(None) is False
            assert automation._validate_text_input("A" * 10001) is False
    
    @patch('modules.automation.pyautogui')
    def test_execute_click_action(self, mock_pyautogui):
        """Test execution of click action."""
        mock_pyautogui.size.return_value = (1920, 1080)
        automation = AutomationModule()
        
        action = {
            "action": "click",
            "coordinates": [500, 300]
        }
        
        automation.execute_action(action)
        
        mock_pyautogui.moveTo.assert_called_once_with(500, 300, duration=0.25)
        mock_pyautogui.click.assert_called_once()
    
    @patch('modules.automation.pyautogui')
    def test_execute_double_click_action(self, mock_pyautogui):
        """Test execution of double click action."""
        mock_pyautogui.size.return_value = (1920, 1080)
        automation = AutomationModule()
        
        action = {
            "action": "double_click",
            "coordinates": [600, 400]
        }
        
        automation.execute_action(action)
        
        mock_pyautogui.moveTo.assert_called_once_with(600, 400, duration=0.25)
        mock_pyautogui.doubleClick.assert_called_once()
    
    @patch('modules.automation.pyautogui')
    def test_execute_type_action(self, mock_pyautogui):
        """Test execution of type action."""
        mock_pyautogui.size.return_value = (1920, 1080)
        automation = AutomationModule()
        
        action = {
            "action": "type",
            "text": "Hello World"
        }
        
        automation.execute_action(action)
        
        mock_pyautogui.typewrite.assert_called_once_with("Hello World", interval=0.05)
    
    @patch('modules.automation.pyautogui')
    def test_execute_scroll_up_action(self, mock_pyautogui):
        """Test execution of scroll up action."""
        mock_pyautogui.size.return_value = (1920, 1080)
        automation = AutomationModule()
        
        action = {
            "action": "scroll",
            "direction": "up",
            "amount": 200
        }
        
        automation.execute_action(action)
        
        mock_pyautogui.scroll.assert_called_once_with(200)
    
    @patch('modules.automation.pyautogui')
    def test_execute_scroll_down_action(self, mock_pyautogui):
        """Test execution of scroll down action."""
        mock_pyautogui.size.return_value = (1920, 1080)
        automation = AutomationModule()
        
        action = {
            "action": "scroll",
            "direction": "down",
            "amount": 150
        }
        
        automation.execute_action(action)
        
        mock_pyautogui.scroll.assert_called_once_with(-150)
    
    @patch('modules.automation.pyautogui')
    def test_execute_scroll_left_action(self, mock_pyautogui):
        """Test execution of scroll left action."""
        mock_pyautogui.size.return_value = (1920, 1080)
        automation = AutomationModule()
        
        action = {
            "action": "scroll",
            "direction": "left",
            "amount": 100
        }
        
        automation.execute_action(action)
        
        mock_pyautogui.hscroll.assert_called_once_with(-100)
    
    @patch('modules.automation.pyautogui')
    def test_execute_scroll_right_action(self, mock_pyautogui):
        """Test execution of scroll right action."""
        mock_pyautogui.size.return_value = (1920, 1080)
        automation = AutomationModule()
        
        action = {
            "action": "scroll",
            "direction": "right",
            "amount": 75
        }
        
        automation.execute_action(action)
        
        mock_pyautogui.hscroll.assert_called_once_with(75)
    
    @patch('modules.automation.pyautogui')
    def test_execute_action_invalid_type(self, mock_pyautogui):
        """Test execution with invalid action type."""
        mock_pyautogui.size.return_value = (1920, 1080)
        automation = AutomationModule()
        
        action = {
            "action": "invalid_action"
        }
        
        with pytest.raises(RuntimeError, match="Action execution failed"):
            automation.execute_action(action)
    
    @patch('modules.automation.pyautogui')
    def test_execute_action_missing_type(self, mock_pyautogui):
        """Test execution with missing action type."""
        mock_pyautogui.size.return_value = (1920, 1080)
        automation = AutomationModule()
        
        action = {}
        
        with pytest.raises(ValueError, match="Action type is required"):
            automation.execute_action(action)
    
    @patch('modules.automation.pyautogui')
    def test_execute_click_invalid_coordinates(self, mock_pyautogui):
        """Test click action with invalid coordinates."""
        mock_pyautogui.size.return_value = (1920, 1080)
        automation = AutomationModule()
        
        action = {
            "action": "click",
            "coordinates": [2000, 300]  # Out of bounds
        }
        
        with pytest.raises(RuntimeError, match="Action execution failed"):
            automation.execute_action(action)
    
    @patch('modules.automation.pyautogui')
    def test_execute_click_missing_coordinates(self, mock_pyautogui):
        """Test click action with missing coordinates."""
        mock_pyautogui.size.return_value = (1920, 1080)
        automation = AutomationModule()
        
        action = {
            "action": "click"
        }
        
        with pytest.raises(RuntimeError, match="Action execution failed"):
            automation.execute_action(action)
    
    @patch('modules.automation.pyautogui')
    def test_execute_type_missing_text(self, mock_pyautogui):
        """Test type action with missing text."""
        mock_pyautogui.size.return_value = (1920, 1080)
        automation = AutomationModule()
        
        action = {
            "action": "type"
        }
        
        with pytest.raises(RuntimeError, match="Action execution failed"):
            automation.execute_action(action)
    
    @patch('modules.automation.pyautogui')
    def test_execute_scroll_invalid_direction(self, mock_pyautogui):
        """Test scroll action with invalid direction."""
        mock_pyautogui.size.return_value = (1920, 1080)
        automation = AutomationModule()
        
        action = {
            "action": "scroll",
            "direction": "diagonal",
            "amount": 100
        }
        
        with pytest.raises(RuntimeError, match="Action execution failed"):
            automation.execute_action(action)
    
    @patch('modules.automation.pyautogui')
    def test_execute_scroll_default_values(self, mock_pyautogui):
        """Test scroll action with default values."""
        mock_pyautogui.size.return_value = (1920, 1080)
        automation = AutomationModule()
        
        action = {
            "action": "scroll"
        }
        
        automation.execute_action(action)
        
        # Should use default direction "up" and amount from config
        mock_pyautogui.scroll.assert_called_once_with(100)
    
    @patch('modules.automation.pyautogui')
    def test_get_screen_size(self, mock_pyautogui):
        """Test getting screen size."""
        mock_pyautogui.size.return_value = (1920, 1080)
        automation = AutomationModule()
        
        width, height = automation.get_screen_size()
        
        assert width == 1920
        assert height == 1080
    
    @patch('modules.automation.pyautogui')
    def test_get_mouse_position(self, mock_pyautogui):
        """Test getting mouse position."""
        mock_pyautogui.size.return_value = (1920, 1080)
        mock_pyautogui.position.return_value = (500, 300)
        automation = AutomationModule()
        
        x, y = automation.get_mouse_position()
        
        assert x == 500
        assert y == 300
        mock_pyautogui.position.assert_called_once()