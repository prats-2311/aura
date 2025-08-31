# modules/automation.py
"""
Automation Module for AURA

Handles execution of GUI actions using PyAutoGUI.
Provides safe and controlled desktop automation capabilities.
"""

import pyautogui
import time
import logging
from typing import Dict, Any, Tuple, Optional, List
from config import MOUSE_MOVE_DURATION, TYPE_INTERVAL, SCROLL_AMOUNT

# Configure PyAutoGUI safety settings
pyautogui.FAILSAFE = True  # Move mouse to corner to abort
pyautogui.PAUSE = 0.1      # Small pause between actions

logger = logging.getLogger(__name__)


class AutomationModule:
    """
    Handles GUI automation using PyAutoGUI with safety controls and validation.
    
    Supports click, double_click, type, and scroll actions with coordinate validation,
    smooth cursor movement, error logging, and recovery mechanisms.
    """
    
    def __init__(self, max_retries: int = 3, retry_delay: float = 0.5):
        """
        Initialize the automation module with safety settings.
        
        Args:
            max_retries: Maximum number of retry attempts for failed actions
            retry_delay: Delay between retry attempts in seconds
        """
        self.screen_width, self.screen_height = pyautogui.size()
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.action_history = []  # Track executed actions for debugging
        logger.info(f"AutomationModule initialized. Screen size: {self.screen_width}x{self.screen_height}")
        logger.info(f"Retry settings: max_retries={max_retries}, retry_delay={retry_delay}s")
    
    def _validate_coordinates(self, x: int, y: int) -> bool:
        """
        Validate that coordinates are within screen bounds.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            bool: True if coordinates are valid, False otherwise
        """
        if not (0 <= x <= self.screen_width):
            logger.error(f"X coordinate {x} is out of bounds (0-{self.screen_width})")
            return False
        if not (0 <= y <= self.screen_height):
            logger.error(f"Y coordinate {y} is out of bounds (0-{self.screen_height})")
            return False
        return True
    
    def _validate_text_input(self, text: str) -> bool:
        """
        Validate text input for typing actions.
        
        Args:
            text: Text to validate
            
        Returns:
            bool: True if text is valid, False otherwise
        """
        if not isinstance(text, str):
            logger.error(f"Text input must be string, got {type(text)}")
            return False
        if len(text) > 10000:  # Reasonable limit
            logger.error(f"Text input too long: {len(text)} characters")
            return False
        return True
    
    def execute_action(self, action: Dict[str, Any]) -> None:
        """
        Execute a single GUI action with retry logic and error recovery.
        
        Args:
            action: Dictionary containing action type and parameters
                   Expected format:
                   {
                       "action": "click|double_click|type|scroll",
                       "coordinates": [x, y],  # for click actions
                       "text": "text to type",  # for type actions
                       "direction": "up|down|left|right",  # for scroll actions
                       "amount": 100  # for scroll actions
                   }
        
        Raises:
            ValueError: If action format is invalid
            RuntimeError: If action execution fails after all retries
        """
        action_type = action.get("action")
        if not action_type:
            raise ValueError("Action type is required")
        
        # Record action attempt
        self.action_history.append({
            "action": action.copy(),
            "timestamp": time.time(),
            "status": "attempting"
        })
        
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                logger.info(f"Executing action: {action_type} (attempt {attempt + 1}/{self.max_retries + 1})")
                
                if action_type == "click":
                    self._execute_click(action)
                elif action_type == "double_click":
                    self._execute_double_click(action)
                elif action_type == "type":
                    self._execute_type(action)
                elif action_type == "scroll":
                    self._execute_scroll(action)
                else:
                    raise ValueError(f"Unsupported action type: {action_type}")
                
                # Success - update history and return
                self.action_history[-1]["status"] = "success"
                logger.info(f"Successfully executed action: {action_type}")
                return
                
            except Exception as e:
                last_exception = e
                logger.warning(f"Action {action_type} failed on attempt {attempt + 1}: {str(e)}")
                
                if attempt < self.max_retries:
                    logger.info(f"Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                    # Try to recover by moving mouse to center of screen
                    try:
                        pyautogui.moveTo(self.screen_width // 2, self.screen_height // 2, duration=0.1)
                    except Exception:
                        pass  # Ignore recovery failures
        
        # All retries failed
        self.action_history[-1]["status"] = "failed"
        self.action_history[-1]["error"] = str(last_exception)
        logger.error(f"Action {action_type} failed after {self.max_retries + 1} attempts: {str(last_exception)}")
        raise RuntimeError(f"Action execution failed after {self.max_retries + 1} attempts: {str(last_exception)}")
    
    def execute_action_sequence(self, actions: List[Dict[str, Any]], stop_on_error: bool = False) -> Dict[str, Any]:
        """
        Execute a sequence of actions with comprehensive error handling.
        
        Args:
            actions: List of action dictionaries to execute
            stop_on_error: If True, stop execution on first error; if False, continue with remaining actions
            
        Returns:
            Dict containing execution results:
            {
                "total_actions": int,
                "successful_actions": int,
                "failed_actions": int,
                "errors": List[str],
                "execution_time": float
            }
        """
        start_time = time.time()
        results = {
            "total_actions": len(actions),
            "successful_actions": 0,
            "failed_actions": 0,
            "errors": [],
            "execution_time": 0.0
        }
        
        logger.info(f"Starting execution of {len(actions)} actions (stop_on_error={stop_on_error})")
        
        for i, action in enumerate(actions):
            try:
                self.execute_action(action)
                results["successful_actions"] += 1
                logger.debug(f"Action {i + 1}/{len(actions)} completed successfully")
                
            except Exception as e:
                results["failed_actions"] += 1
                error_msg = f"Action {i + 1} failed: {str(e)}"
                results["errors"].append(error_msg)
                logger.error(error_msg)
                
                if stop_on_error:
                    logger.info("Stopping execution due to error (stop_on_error=True)")
                    break
        
        results["execution_time"] = time.time() - start_time
        logger.info(f"Action sequence completed: {results['successful_actions']}/{results['total_actions']} successful")
        
        return results
    
    def _execute_click(self, action: Dict[str, Any]) -> None:
        """Execute a single click action."""
        coordinates = action.get("coordinates")
        if not coordinates or len(coordinates) != 2:
            raise ValueError("Click action requires coordinates [x, y]")
        
        x, y = int(coordinates[0]), int(coordinates[1])
        if not self._validate_coordinates(x, y):
            raise ValueError(f"Invalid coordinates: ({x}, {y})")
        
        # Move to coordinates with smooth movement
        pyautogui.moveTo(x, y, duration=MOUSE_MOVE_DURATION)
        pyautogui.click()
        logger.debug(f"Clicked at ({x}, {y})")
    
    def _execute_double_click(self, action: Dict[str, Any]) -> None:
        """Execute a double click action."""
        coordinates = action.get("coordinates")
        if not coordinates or len(coordinates) != 2:
            raise ValueError("Double click action requires coordinates [x, y]")
        
        x, y = int(coordinates[0]), int(coordinates[1])
        if not self._validate_coordinates(x, y):
            raise ValueError(f"Invalid coordinates: ({x}, {y})")
        
        # Move to coordinates with smooth movement
        pyautogui.moveTo(x, y, duration=MOUSE_MOVE_DURATION)
        pyautogui.doubleClick()
        logger.debug(f"Double-clicked at ({x}, {y})")
    
    def _execute_type(self, action: Dict[str, Any]) -> None:
        """Execute a type action."""
        text = action.get("text")
        if text is None:
            raise ValueError("Type action requires text parameter")
        
        if not self._validate_text_input(text):
            raise ValueError(f"Invalid text input")
        
        # Type with interval between keystrokes for reliability
        pyautogui.typewrite(text, interval=TYPE_INTERVAL)
        logger.debug(f"Typed text: {text[:50]}{'...' if len(text) > 50 else ''}")
    
    def _execute_scroll(self, action: Dict[str, Any]) -> None:
        """Execute a scroll action."""
        direction = action.get("direction", "up")
        amount = action.get("amount", SCROLL_AMOUNT)
        
        if direction not in ["up", "down", "left", "right"]:
            raise ValueError(f"Invalid scroll direction: {direction}")
        
        try:
            amount = int(amount)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid scroll amount: {amount}")
        
        # Convert direction to scroll parameters
        if direction == "up":
            pyautogui.scroll(amount)
        elif direction == "down":
            pyautogui.scroll(-amount)
        elif direction == "left":
            pyautogui.hscroll(-amount)
        elif direction == "right":
            pyautogui.hscroll(amount)
        
        logger.debug(f"Scrolled {direction} by {amount}")
    
    def get_screen_size(self) -> Tuple[int, int]:
        """
        Get the current screen size.
        
        Returns:
            Tuple[int, int]: Screen width and height
        """
        return self.screen_width, self.screen_height
    
    def get_mouse_position(self) -> Tuple[int, int]:
        """
        Get the current mouse position.
        
        Returns:
            Tuple[int, int]: Current mouse x, y coordinates
        """
        return pyautogui.position()
    
    def get_action_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get the history of executed actions for debugging and monitoring.
        
        Args:
            limit: Maximum number of recent actions to return (None for all)
            
        Returns:
            List of action history entries
        """
        if limit is None:
            return self.action_history.copy()
        return self.action_history[-limit:] if self.action_history else []
    
    def clear_action_history(self) -> None:
        """Clear the action history."""
        self.action_history.clear()
        logger.info("Action history cleared")
    
    def get_failure_rate(self) -> float:
        """
        Calculate the failure rate of recent actions.
        
        Returns:
            float: Failure rate as a percentage (0.0 to 100.0)
        """
        if not self.action_history:
            return 0.0
        
        failed_count = sum(1 for action in self.action_history if action.get("status") == "failed")
        return (failed_count / len(self.action_history)) * 100.0
    
    def validate_action_format(self, action: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate action format without executing it.
        
        Args:
            action: Action dictionary to validate
            
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        try:
            action_type = action.get("action")
            if not action_type:
                return False, "Action type is required"
            
            if action_type not in ["click", "double_click", "type", "scroll"]:
                return False, f"Unsupported action type: {action_type}"
            
            if action_type in ["click", "double_click"]:
                coordinates = action.get("coordinates")
                if not coordinates or len(coordinates) != 2:
                    return False, f"{action_type} action requires coordinates [x, y]"
                
                x, y = int(coordinates[0]), int(coordinates[1])
                if not self._validate_coordinates(x, y):
                    return False, f"Invalid coordinates: ({x}, {y})"
            
            elif action_type == "type":
                text = action.get("text")
                if text is None:
                    return False, "Type action requires text parameter"
                
                if not self._validate_text_input(text):
                    return False, "Invalid text input"
            
            elif action_type == "scroll":
                direction = action.get("direction", "up")
                if direction not in ["up", "down", "left", "right"]:
                    return False, f"Invalid scroll direction: {direction}"
                
                amount = action.get("amount", SCROLL_AMOUNT)
                try:
                    int(amount)
                except (ValueError, TypeError):
                    return False, f"Invalid scroll amount: {amount}"
            
            return True, "Action format is valid"
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def set_retry_settings(self, max_retries: int, retry_delay: float) -> None:
        """
        Update retry settings for action execution.
        
        Args:
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retry attempts in seconds
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        logger.info(f"Updated retry settings: max_retries={max_retries}, retry_delay={retry_delay}s")