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
from .error_handler import (
    global_error_handler,
    with_error_handling,
    ErrorCategory,
    ErrorSeverity
)

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
    
    @with_error_handling(
        category=ErrorCategory.HARDWARE_ERROR,
        severity=ErrorSeverity.MEDIUM,
        max_retries=0,  # We handle retries internally
        user_message="I'm having trouble controlling your computer. Please check if the application is responding."
    )
    def execute_action(self, action: Dict[str, Any]) -> None:
        """
        Execute a single GUI action with comprehensive error handling and retry logic.
        
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
        # Validate action structure
        if not isinstance(action, dict):
            raise ValueError("Action must be a dictionary")
        
        action_type = action.get("action")
        if not action_type:
            raise ValueError("Action type is required")
        
        # Validate action type
        valid_actions = {"click", "double_click", "type", "scroll"}
        if action_type not in valid_actions:
            raise ValueError(f"Unsupported action type: {action_type}. Valid types: {valid_actions}")
        
        # Pre-validate action parameters
        is_valid, error_msg = self.validate_action_format(action)
        if not is_valid:
            raise ValueError(f"Invalid action format: {error_msg}")
        
        # Record action attempt
        action_record = {
            "action": action.copy(),
            "timestamp": time.time(),
            "status": "attempting",
            "attempts": 0
        }
        self.action_history.append(action_record)
        
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                action_record["attempts"] = attempt + 1
                logger.info(f"Executing action: {action_type} (attempt {attempt + 1}/{self.max_retries + 1})")
                
                # Check for PyAutoGUI failsafe
                try:
                    current_pos = pyautogui.position()
                    if current_pos.x == 0 and current_pos.y == 0:
                        logger.warning("Mouse at failsafe position (0,0), aborting action")
                        raise pyautogui.FailSafeException("PyAutoGUI failsafe triggered")
                except pyautogui.FailSafeException:
                    error_info = global_error_handler.handle_error(
                        error=Exception("PyAutoGUI failsafe triggered"),
                        module="automation",
                        function="execute_action",
                        category=ErrorCategory.HARDWARE_ERROR,
                        context={"action_type": action_type, "attempt": attempt + 1}
                    )
                    raise RuntimeError(f"Automation stopped by failsafe: {error_info.user_message}")
                
                # Execute the specific action
                if action_type == "click":
                    self._execute_click(action)
                elif action_type == "double_click":
                    self._execute_double_click(action)
                elif action_type == "type":
                    self._execute_type(action)
                elif action_type == "scroll":
                    self._execute_scroll(action)
                
                # Success - update history and return
                action_record["status"] = "success"
                action_record["completion_time"] = time.time()
                logger.info(f"Successfully executed action: {action_type}")
                return
                
            except pyautogui.FailSafeException as e:
                # Don't retry failsafe exceptions
                last_exception = e
                error_info = global_error_handler.handle_error(
                    error=e,
                    module="automation",
                    function="execute_action",
                    category=ErrorCategory.HARDWARE_ERROR,
                    context={"action_type": action_type, "attempt": attempt + 1}
                )
                action_record["status"] = "failed"
                action_record["error"] = str(e)
                raise RuntimeError(f"Automation failsafe triggered: {error_info.user_message}")
                
            except Exception as e:
                last_exception = e
                
                # Log the error with context
                error_info = global_error_handler.handle_error(
                    error=e,
                    module="automation",
                    function="execute_action",
                    category=ErrorCategory.HARDWARE_ERROR,
                    context={
                        "action_type": action_type,
                        "attempt": attempt + 1,
                        "action_params": {k: v for k, v in action.items() if k != "text"}  # Don't log sensitive text
                    }
                )
                
                logger.warning(f"Action {action_type} failed on attempt {attempt + 1}: {error_info.message}")
                
                if attempt < self.max_retries:
                    logger.info(f"Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                    
                    # Try to recover by moving mouse to center of screen
                    try:
                        center_x = self.screen_width // 2
                        center_y = self.screen_height // 2
                        pyautogui.moveTo(center_x, center_y, duration=0.1)
                        logger.debug("Moved mouse to center for recovery")
                    except Exception as recovery_error:
                        logger.warning(f"Recovery action failed: {recovery_error}")
                        # Continue anyway
        
        # All retries failed
        action_record["status"] = "failed"
        action_record["error"] = str(last_exception)
        action_record["completion_time"] = time.time()
        
        # Log final failure
        final_error_info = global_error_handler.handle_error(
            error=last_exception or Exception("Unknown error"),
            module="automation",
            function="execute_action",
            category=ErrorCategory.HARDWARE_ERROR,
            context={
                "action_type": action_type,
                "total_attempts": self.max_retries + 1,
                "final_error": str(last_exception)
            }
        )
        
        logger.error(f"Action {action_type} failed after {self.max_retries + 1} attempts: {final_error_info.message}")
        raise RuntimeError(f"Action execution failed after {self.max_retries + 1} attempts: {final_error_info.user_message}")
    
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
    
    def fill_form(self, form_data: Dict[str, Any], form_values: Dict[str, str], 
                  confirm_before_submit: bool = True) -> Dict[str, Any]:
        """
        Fill a web form with provided values using sequential click and type actions.
        
        Args:
            form_data: Form structure data from vision analysis
            form_values: Dictionary mapping field labels to values
            confirm_before_submit: Whether to require confirmation before submitting
            
        Returns:
            Dict containing form filling results and any errors
        """
        try:
            logger.info(f"Starting form filling for {len(form_values)} fields")
            
            results = {
                "total_fields": 0,
                "filled_fields": 0,
                "skipped_fields": 0,
                "failed_fields": 0,
                "errors": [],
                "warnings": [],
                "form_submitted": False,
                "execution_time": 0.0
            }
            
            start_time = time.time()
            
            # Process each form in the form data
            forms = form_data.get('forms', [])
            if not forms:
                raise ValueError("No forms found in form data")
            
            for form in forms:
                form_id = form.get('form_id', 'unknown')
                logger.info(f"Processing form: {form_id}")
                
                fields = form.get('fields', [])
                results["total_fields"] += len(fields)
                
                # Fill each field
                for field in fields:
                    field_result = self._fill_form_field(field, form_values)
                    
                    if field_result["status"] == "filled":
                        results["filled_fields"] += 1
                    elif field_result["status"] == "skipped":
                        results["skipped_fields"] += 1
                    elif field_result["status"] == "failed":
                        results["failed_fields"] += 1
                        results["errors"].append(field_result["error"])
                    
                    if field_result.get("warning"):
                        results["warnings"].append(field_result["warning"])
            
            # Handle form submission if requested
            if confirm_before_submit:
                logger.info("Form filling completed. Submission requires manual confirmation.")
                results["warnings"].append("Form submission requires manual confirmation")
            else:
                submit_result = self._submit_form(form_data)
                results["form_submitted"] = submit_result["success"]
                if not submit_result["success"]:
                    results["errors"].append(submit_result["error"])
            
            results["execution_time"] = time.time() - start_time
            logger.info(f"Form filling completed: {results['filled_fields']}/{results['total_fields']} fields filled")
            
            return results
            
        except Exception as e:
            logger.error(f"Form filling failed: {e}")
            return {
                "total_fields": 0,
                "filled_fields": 0,
                "skipped_fields": 0,
                "failed_fields": 0,
                "errors": [str(e)],
                "warnings": [],
                "form_submitted": False,
                "execution_time": time.time() - start_time if 'start_time' in locals() else 0.0
            }
    
    def _fill_form_field(self, field: Dict[str, Any], form_values: Dict[str, str]) -> Dict[str, Any]:
        """
        Fill a single form field based on its type and provided value.
        
        Args:
            field: Field data from form analysis
            form_values: Dictionary mapping field labels to values
            
        Returns:
            Dict containing field filling result
        """
        field_label = field.get('label', '')
        field_type = field.get('type', 'text_input')
        coordinates = field.get('coordinates', [0, 0, 0, 0])
        
        # Check if we have a value for this field
        field_value = None
        for label_key, value in form_values.items():
            if label_key.lower() in field_label.lower() or field_label.lower() in label_key.lower():
                field_value = value
                break
        
        if field_value is None:
            return {
                "status": "skipped",
                "field": field_label,
                "reason": "No value provided for field"
            }
        
        try:
            # Calculate click coordinates (center of field)
            if len(coordinates) >= 4:
                click_x = (coordinates[0] + coordinates[2]) // 2
                click_y = (coordinates[1] + coordinates[3]) // 2
            else:
                logger.warning(f"Invalid coordinates for field {field_label}")
                return {
                    "status": "failed",
                    "field": field_label,
                    "error": "Invalid field coordinates"
                }
            
            # Handle different field types
            if field_type in ['text_input', 'email', 'password', 'number']:
                return self._fill_text_field(click_x, click_y, field_value, field_label)
            
            elif field_type == 'textarea':
                return self._fill_textarea_field(click_x, click_y, field_value, field_label)
            
            elif field_type == 'select':
                return self._fill_select_field(click_x, click_y, field_value, field_label, field.get('options', []))
            
            elif field_type == 'checkbox':
                return self._fill_checkbox_field(click_x, click_y, field_value, field_label)
            
            elif field_type == 'radio':
                return self._fill_radio_field(click_x, click_y, field_value, field_label)
            
            else:
                return {
                    "status": "skipped",
                    "field": field_label,
                    "reason": f"Unsupported field type: {field_type}"
                }
                
        except Exception as e:
            logger.error(f"Failed to fill field {field_label}: {e}")
            return {
                "status": "failed",
                "field": field_label,
                "error": str(e)
            }
    
    def _fill_text_field(self, x: int, y: int, value: str, field_label: str) -> Dict[str, Any]:
        """Fill a text input field."""
        try:
            # Click on the field to focus it
            self.execute_action({
                "action": "click",
                "coordinates": [x, y]
            })
            
            # Clear existing content (Ctrl+A, then type)
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.1)
            
            # Type the new value
            self.execute_action({
                "action": "type",
                "text": value
            })
            
            logger.debug(f"Filled text field '{field_label}' with value")
            return {
                "status": "filled",
                "field": field_label,
                "value": value
            }
            
        except Exception as e:
            return {
                "status": "failed",
                "field": field_label,
                "error": str(e)
            }
    
    def _fill_textarea_field(self, x: int, y: int, value: str, field_label: str) -> Dict[str, Any]:
        """Fill a textarea field (similar to text field but may handle newlines)."""
        try:
            # Click on the field to focus it
            self.execute_action({
                "action": "click",
                "coordinates": [x, y]
            })
            
            # Clear existing content
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.1)
            
            # Type the new value (preserve newlines)
            self.execute_action({
                "action": "type",
                "text": value
            })
            
            logger.debug(f"Filled textarea '{field_label}' with value")
            return {
                "status": "filled",
                "field": field_label,
                "value": value
            }
            
        except Exception as e:
            return {
                "status": "failed",
                "field": field_label,
                "error": str(e)
            }
    
    def _fill_select_field(self, x: int, y: int, value: str, field_label: str, options: List[str]) -> Dict[str, Any]:
        """Fill a select dropdown field."""
        try:
            # Click on the dropdown to open it
            self.execute_action({
                "action": "click",
                "coordinates": [x, y]
            })
            
            time.sleep(0.5)  # Wait for dropdown to open
            
            # Try to find matching option
            matching_option = None
            value_lower = value.lower()
            
            for option in options:
                if option.lower() == value_lower or value_lower in option.lower():
                    matching_option = option
                    break
            
            if matching_option:
                # Type the option value to select it
                self.execute_action({
                    "action": "type",
                    "text": matching_option
                })
                
                # Press Enter to confirm selection
                pyautogui.press('enter')
                
                logger.debug(f"Selected option '{matching_option}' in dropdown '{field_label}'")
                return {
                    "status": "filled",
                    "field": field_label,
                    "value": matching_option
                }
            else:
                # Try typing the value directly
                self.execute_action({
                    "action": "type",
                    "text": value
                })
                
                pyautogui.press('enter')
                
                return {
                    "status": "filled",
                    "field": field_label,
                    "value": value,
                    "warning": f"Option '{value}' not found in dropdown, typed directly"
                }
                
        except Exception as e:
            return {
                "status": "failed",
                "field": field_label,
                "error": str(e)
            }
    
    def _fill_checkbox_field(self, x: int, y: int, value: str, field_label: str) -> Dict[str, Any]:
        """Fill a checkbox field."""
        try:
            # Determine if checkbox should be checked
            should_check = value.lower() in ['true', '1', 'yes', 'on', 'checked']
            
            # Click the checkbox
            self.execute_action({
                "action": "click",
                "coordinates": [x, y]
            })
            
            logger.debug(f"{'Checked' if should_check else 'Unchecked'} checkbox '{field_label}'")
            return {
                "status": "filled",
                "field": field_label,
                "value": str(should_check)
            }
            
        except Exception as e:
            return {
                "status": "failed",
                "field": field_label,
                "error": str(e)
            }
    
    def _fill_radio_field(self, x: int, y: int, value: str, field_label: str) -> Dict[str, Any]:
        """Fill a radio button field."""
        try:
            # For radio buttons, we assume the value indicates this option should be selected
            should_select = value.lower() in ['true', '1', 'yes', 'selected']
            
            if should_select:
                self.execute_action({
                    "action": "click",
                    "coordinates": [x, y]
                })
                
                logger.debug(f"Selected radio button '{field_label}'")
                return {
                    "status": "filled",
                    "field": field_label,
                    "value": "selected"
                }
            else:
                return {
                    "status": "skipped",
                    "field": field_label,
                    "reason": "Radio button not selected based on value"
                }
                
        except Exception as e:
            return {
                "status": "failed",
                "field": field_label,
                "error": str(e)
            }
    
    def _submit_form(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """Submit the form by clicking the submit button."""
        try:
            submit_buttons = form_data.get('submit_buttons', [])
            
            if not submit_buttons:
                return {
                    "success": False,
                    "error": "No submit button found"
                }
            
            # Use the first submit button
            submit_button = submit_buttons[0]
            coordinates = submit_button.get('coordinates', [0, 0, 0, 0])
            
            if len(coordinates) >= 4:
                click_x = (coordinates[0] + coordinates[2]) // 2
                click_y = (coordinates[1] + coordinates[3]) // 2
                
                self.execute_action({
                    "action": "click",
                    "coordinates": [click_x, click_y]
                })
                
                logger.info("Form submitted successfully")
                return {
                    "success": True,
                    "button_text": submit_button.get('text', 'Submit')
                }
            else:
                return {
                    "success": False,
                    "error": "Invalid submit button coordinates"
                }
                
        except Exception as e:
            logger.error(f"Form submission failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def validate_form_data(self, form_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate form data structure for form filling.
        
        Args:
            form_data: Form data from vision analysis
            
        Returns:
            Tuple[bool, List[str]]: (is_valid, list_of_errors)
        """
        errors = []
        
        try:
            if not isinstance(form_data, dict):
                errors.append("Form data must be a dictionary")
                return False, errors
            
            forms = form_data.get('forms', [])
            if not forms:
                errors.append("No forms found in form data")
                return False, errors
            
            for i, form in enumerate(forms):
                if not isinstance(form, dict):
                    errors.append(f"Form {i} is not a dictionary")
                    continue
                
                fields = form.get('fields', [])
                if not isinstance(fields, list):
                    errors.append(f"Form {i} fields must be a list")
                    continue
                
                for j, field in enumerate(fields):
                    if not isinstance(field, dict):
                        errors.append(f"Form {i}, field {j} is not a dictionary")
                        continue
                    
                    # Check required field properties
                    if 'type' not in field:
                        errors.append(f"Form {i}, field {j} missing 'type'")
                    
                    if 'coordinates' not in field:
                        errors.append(f"Form {i}, field {j} missing 'coordinates'")
                    elif len(field['coordinates']) < 4:
                        errors.append(f"Form {i}, field {j} has invalid coordinates")
            
            return len(errors) == 0, errors
            
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
            return False, errors
    
    def handle_form_validation_errors(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect and attempt to handle form validation errors.
        
        Args:
            form_data: Current form data from vision analysis
            
        Returns:
            Dict containing error handling results
        """
        try:
            logger.info("Checking for form validation errors")
            
            results = {
                "errors_found": 0,
                "errors_handled": 0,
                "unhandled_errors": [],
                "actions_taken": []
            }
            
            # Check for form errors in the analysis
            form_errors = form_data.get('form_errors', [])
            results["errors_found"] = len(form_errors)
            
            for error in form_errors:
                error_message = error.get('message', '')
                associated_field = error.get('associated_field', '')
                coordinates = error.get('coordinates', [0, 0, 0, 0])
                
                logger.warning(f"Form validation error: {error_message} (field: {associated_field})")
                
                # Try to handle common validation errors
                if self._handle_validation_error(error_message, associated_field, coordinates):
                    results["errors_handled"] += 1
                    results["actions_taken"].append(f"Handled error for field '{associated_field}': {error_message}")
                else:
                    results["unhandled_errors"].append({
                        "message": error_message,
                        "field": associated_field
                    })
            
            # Check for field-level errors
            forms = form_data.get('forms', [])
            for form in forms:
                fields = form.get('fields', [])
                for field in fields:
                    if field.get('validation_state') == 'error':
                        field_label = field.get('label', 'Unknown')
                        error_message = field.get('error_message', 'Field validation error')
                        coordinates = field.get('coordinates', [0, 0, 0, 0])
                        
                        results["errors_found"] += 1
                        logger.warning(f"Field validation error: {error_message} (field: {field_label})")
                        
                        if self._handle_validation_error(error_message, field_label, coordinates):
                            results["errors_handled"] += 1
                            results["actions_taken"].append(f"Handled error for field '{field_label}': {error_message}")
                        else:
                            results["unhandled_errors"].append({
                                "message": error_message,
                                "field": field_label
                            })
            
            logger.info(f"Error handling completed: {results['errors_handled']}/{results['errors_found']} errors handled")
            return results
            
        except Exception as e:
            logger.error(f"Error handling failed: {e}")
            return {
                "errors_found": 0,
                "errors_handled": 0,
                "unhandled_errors": [{"message": str(e), "field": "system"}],
                "actions_taken": []
            }
    
    def _handle_validation_error(self, error_message: str, field_label: str, coordinates: List[int]) -> bool:
        """
        Attempt to handle a specific validation error.
        
        Args:
            error_message: The validation error message
            field_label: The associated field label
            coordinates: Field coordinates for interaction
            
        Returns:
            bool: True if error was handled, False otherwise
        """
        try:
            error_lower = error_message.lower()
            
            # Handle "required field" errors by focusing the field
            if 'required' in error_lower or 'mandatory' in error_lower:
                if len(coordinates) >= 4:
                    click_x = (coordinates[0] + coordinates[2]) // 2
                    click_y = (coordinates[1] + coordinates[3]) // 2
                    
                    self.execute_action({
                        "action": "click",
                        "coordinates": [click_x, click_y]
                    })
                    
                    logger.info(f"Focused required field '{field_label}'")
                    return True
            
            # Handle "invalid format" errors by clearing the field
            elif 'invalid' in error_lower or 'format' in error_lower:
                if len(coordinates) >= 4:
                    click_x = (coordinates[0] + coordinates[2]) // 2
                    click_y = (coordinates[1] + coordinates[3]) // 2
                    
                    self.execute_action({
                        "action": "click",
                        "coordinates": [click_x, click_y]
                    })
                    
                    # Clear the field
                    pyautogui.hotkey('ctrl', 'a')
                    pyautogui.press('delete')
                    
                    logger.info(f"Cleared field with invalid format: '{field_label}'")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to handle validation error: {e}")
            return False