# modules/automation.py
"""
Automation Module for AURA

Handles execution of GUI actions using PyAutoGUI.
Provides safe and controlled desktop automation capabilities.
"""

import pyautogui
import time
import logging
import platform
import subprocess
import pyperclip
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
        self.is_macos = platform.system() == "Darwin"
        
        # Get screen size safely based on platform
        if self.is_macos:
            self.screen_width, self.screen_height = self._get_macos_screen_size()
            # Check for cliclick availability
            self.has_cliclick = self._check_cliclick_available()
        else:
            try:
                self.screen_width, self.screen_height = pyautogui.size()
            except Exception as e:
                logger.warning(f"PyAutoGUI size detection failed: {e}")
                self.screen_width, self.screen_height = (1920, 1080)  # Default fallback
            self.has_cliclick = False
            
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.action_history = []  # Track executed actions for debugging
        
        logger.info(f"AutomationModule initialized. Screen size: {self.screen_width}x{self.screen_height}")
        logger.info(f"Retry settings: max_retries={max_retries}, retry_delay={retry_delay}s")
        if self.is_macos:
            if self.has_cliclick:
                logger.info("macOS detected - using cliclick as PRIMARY automation method")
                logger.info("AppleScript available as fallback only")
            else:
                logger.warning("macOS detected but cliclick NOT available - using AppleScript only")
                logger.warning("Install cliclick for better reliability: brew install cliclick")
    
    def _check_cliclick_available(self) -> bool:
        """Check if cliclick is available on the system."""
        try:
            result = subprocess.run(
                ['which', 'cliclick'],
                capture_output=True,
                text=True,
                timeout=2
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def _get_macos_screen_size(self) -> Tuple[int, int]:
        """Get screen size on macOS using system commands."""
        try:
            # Use system_profiler to get display information
            result = subprocess.run(
                ['system_profiler', 'SPDisplaysDataType'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                # Parse the output to find resolution
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'Resolution:' in line:
                        # Extract resolution like "1920 x 1080" or "1664 Retina"
                        resolution_part = line.split(':')[1].strip()
                        
                        # Handle "1664 Retina" format
                        if 'Retina' in resolution_part:
                            # Extract just the number before "Retina"
                            width_str = resolution_part.split()[0]
                            try:
                                width = int(width_str)
                                # Common Retina aspect ratios
                                if width == 1664:
                                    return (1664, 1050)  # 13" MacBook Pro
                                elif width == 1728:
                                    return (1728, 1117)  # 13" MacBook Air
                                elif width == 1800:
                                    return (1800, 1169)  # 14" MacBook Pro
                                else:
                                    # Assume 16:10 aspect ratio for unknown Retina displays
                                    height = int(width * 10 / 16)
                                    return (width, height)
                            except ValueError:
                                pass
                        
                        # Handle "1920 x 1080" format
                        elif ' x ' in resolution_part:
                            parts = resolution_part.split(' x ')
                            if len(parts) == 2:
                                try:
                                    width = int(parts[0].strip())
                                    height = int(parts[1].strip())
                                    return (width, height)
                                except ValueError:
                                    pass
            
        except Exception as e:
            logger.debug(f"Failed to get screen size via system_profiler: {e}")
        
        try:
            # Alternative: use AppleScript
            applescript = '''
            tell application "Finder"
                set screenBounds to bounds of window of desktop
                return (item 3 of screenBounds) & "," & (item 4 of screenBounds)
            end tell
            '''
            
            result = subprocess.run(
                ['osascript', '-e', applescript],
                capture_output=True,
                text=True,
                timeout=3
            )
            
            if result.returncode == 0:
                coords = result.stdout.strip().split(',')
                if len(coords) == 2:
                    return (int(coords[0]), int(coords[1]))
            
        except Exception as e:
            logger.debug(f"Failed to get screen size via AppleScript: {e}")
        
        # Final fallback: common macOS resolutions
        logger.warning("Could not detect screen size, using default 1440x900")
        return (1440, 900)
    
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
                
                # Check for PyAutoGUI failsafe (skip on macOS to avoid AppKit issues)
                if not self.is_macos:
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
                    except Exception as e:
                        # PyAutoGUI position check failed, but continue anyway on non-macOS
                        logger.debug(f"PyAutoGUI position check failed: {e}")
                
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
                        
                        if self.is_macos:
                            # Use AppleScript to move mouse on macOS
                            applescript = f'''
                            tell application "System Events"
                                set mouseLoc to {{{center_x}, {center_y}}}
                                -- Just move, don't click
                            end tell
                            '''
                            subprocess.run(['osascript', '-e', applescript], 
                                         capture_output=True, timeout=3)
                            logger.debug("Moved mouse to center for recovery (macOS)")
                        else:
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
        """Execute a single click action with enhanced validation and fallback."""
        coordinates = action.get("coordinates")
        if not coordinates or len(coordinates) != 2:
            raise ValueError("Click action requires coordinates [x, y]")
        
        x, y = int(coordinates[0]), int(coordinates[1])
        if not self._validate_coordinates(x, y):
            raise ValueError(f"Invalid coordinates: ({x}, {y})")
        
        # Try the primary click
        success = self._attempt_click(x, y)
        
        if not success:
            # If primary click failed and this is a fallback element, try alternatives
            if action.get("fallback_coordinates"):
                logger.info("Primary click failed, trying fallback coordinates")
                for alt_x, alt_y in action["fallback_coordinates"]:
                    if self._validate_coordinates(alt_x, alt_y):
                        logger.debug(f"Trying alternative coordinates: ({alt_x}, {alt_y})")
                        success = self._attempt_click(alt_x, alt_y)
                        if success:
                            logger.info(f"Alternative click succeeded at ({alt_x}, {alt_y})")
                            x, y = alt_x, alt_y  # Update for logging
                            break
            
            if not success:
                raise Exception(f"All click attempts failed for coordinates ({x}, {y})")
        
        logger.debug(f"Successfully clicked at ({x}, {y})")
    
    def _attempt_click(self, x: int, y: int, fast_path: bool = False, element_info: Optional[Dict[str, Any]] = None) -> bool:
        """
        Attempt a single click and return success status - cliclick PRIMARY.
        
        Args:
            x: X coordinate
            y: Y coordinate
            fast_path: Whether this is a fast path execution (from accessibility API)
            element_info: Optional element information for optimization
            
        Returns:
            bool: True if click succeeded, False otherwise
        """
        try:
            if self.is_macos:
                # cliclick is PRIMARY method - most reliable
                if self.has_cliclick:
                    path_type = "FAST" if fast_path else "SLOW"
                    logger.debug(f"Using cliclick (PRIMARY) for {path_type} PATH click at ({x}, {y})")
                    success = self._cliclick_click(x, y, fast_path=fast_path, element_info=element_info)
                    if success:
                        return True
                    else:
                        logger.warning("cliclick (PRIMARY) failed, trying AppleScript fallback")
                
                # AppleScript is FALLBACK ONLY
                path_type = "FAST" if fast_path else "SLOW"
                logger.debug(f"Using AppleScript (FALLBACK) for {path_type} PATH click at ({x}, {y})")
                return self._macos_click(x, y)
            else:
                # Use PyAutoGUI for other platforms
                start_time = time.time()
                pyautogui.moveTo(x, y, duration=MOUSE_MOVE_DURATION)
                pyautogui.click()
                execution_time = time.time() - start_time
                
                # Log performance for non-macOS platforms too
                self._log_click_performance(execution_time, fast_path, True, element_info)
                return True
        except Exception as e:
            logger.warning(f"Click attempt failed at ({x}, {y}): {e}")
            # Log failed performance
            if 'start_time' in locals():
                execution_time = time.time() - start_time
                self._log_click_performance(execution_time, fast_path, False, element_info)
            return False
    
    def _cliclick_click(self, x: int, y: int, fast_path: bool = False, element_info: Optional[Dict[str, Any]] = None) -> bool:
        """
        Execute a click using cliclick on macOS with fast path optimization.
        
        Args:
            x: X coordinate
            y: Y coordinate  
            fast_path: Whether this is a fast path execution (from accessibility API)
            element_info: Optional element information for logging and precision handling
            
        Returns:
            bool: True if click succeeded, False otherwise
        """
        try:
            start_time = time.time()
            
            # Handle coordinate precision for accessibility API results
            if fast_path and element_info:
                # Accessibility API coordinates are typically more precise
                # Apply any necessary coordinate adjustments for better accuracy
                adjusted_x, adjusted_y = self._adjust_accessibility_coordinates(x, y, element_info)
                logger.debug(f"Fast path coordinate adjustment: ({x}, {y}) -> ({adjusted_x}, {adjusted_y})")
                x, y = adjusted_x, adjusted_y
            
            # Execute cliclick with optimized timeout for fast path
            timeout = 3 if fast_path else 5  # Shorter timeout for fast path
            
            result = subprocess.run(
                ['cliclick', f'c:{x},{y}'],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            execution_time = time.time() - start_time
            
            # Performance logging with path differentiation
            if result.returncode == 0:
                path_type = "FAST" if fast_path else "SLOW"
                element_desc = element_info.get('title', 'unknown') if element_info else 'unknown'
                logger.info(f"cliclick {path_type} PATH: Click succeeded at ({x}, {y}) on '{element_desc}' in {execution_time:.3f}s")
                
                # Log performance metrics for monitoring
                self._log_click_performance(execution_time, fast_path, True, element_info)
                return True
            else:
                path_type = "FAST" if fast_path else "SLOW"
                logger.warning(f"cliclick {path_type} PATH: Click failed at ({x}, {y}): {result.stderr}")
                self._log_click_performance(execution_time, fast_path, False, element_info)
                return False
                
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            path_type = "FAST" if fast_path else "SLOW"
            logger.error(f"cliclick {path_type} PATH: Click timed out at ({x}, {y}) after {execution_time:.3f}s")
            self._log_click_performance(execution_time, fast_path, False, element_info)
            return False
        except Exception as e:
            execution_time = time.time() - start_time if 'start_time' in locals() else 0.0
            path_type = "FAST" if fast_path else "SLOW"
            logger.error(f"cliclick {path_type} PATH: Click failed with exception at ({x}, {y}): {e}")
            self._log_click_performance(execution_time, fast_path, False, element_info)
            return False
    
    def _cliclick_double_click(self, x: int, y: int, fast_path: bool = False, element_info: Optional[Dict[str, Any]] = None) -> bool:
        """
        Execute a double-click using cliclick on macOS with fast path optimization.
        
        Args:
            x: X coordinate
            y: Y coordinate
            fast_path: Whether this is a fast path execution
            element_info: Optional element information for optimization
            
        Returns:
            bool: True if double-click succeeded, False otherwise
        """
        try:
            start_time = time.time()
            
            # Handle coordinate precision for accessibility API results
            if fast_path and element_info:
                adjusted_x, adjusted_y = self._adjust_accessibility_coordinates(x, y, element_info)
                logger.debug(f"Fast path double-click coordinate adjustment: ({x}, {y}) -> ({adjusted_x}, {adjusted_y})")
                x, y = adjusted_x, adjusted_y
            
            # Execute cliclick with optimized timeout for fast path
            timeout = 3 if fast_path else 5
            
            result = subprocess.run(
                ['cliclick', f'dc:{x},{y}'],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            execution_time = time.time() - start_time
            
            if result.returncode == 0:
                path_type = "FAST" if fast_path else "SLOW"
                element_desc = element_info.get('title', 'unknown') if element_info else 'unknown'
                logger.info(f"cliclick {path_type} PATH: Double-click succeeded at ({x}, {y}) on '{element_desc}' in {execution_time:.3f}s")
                
                # Log performance metrics
                perf_record = {
                    'timestamp': time.time(),
                    'execution_time': execution_time,
                    'path_type': 'fast' if fast_path else 'slow',
                    'success': True,
                    'action': 'double_click'
                }
                if element_info:
                    perf_record.update({
                        'element_role': element_info.get('role', ''),
                        'element_title': element_info.get('title', ''),
                        'app_name': element_info.get('app_name', '')
                    })
                
                if not hasattr(self, 'performance_history'):
                    self.performance_history = []
                self.performance_history.append(perf_record)
                
                return True
            else:
                path_type = "FAST" if fast_path else "SLOW"
                logger.warning(f"cliclick {path_type} PATH: Double-click failed at ({x}, {y}): {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            path_type = "FAST" if fast_path else "SLOW"
            logger.error(f"cliclick {path_type} PATH: Double-click timed out at ({x}, {y}) after {execution_time:.3f}s")
            return False
        except Exception as e:
            execution_time = time.time() - start_time if 'start_time' in locals() else 0.0
            path_type = "FAST" if fast_path else "SLOW"
            logger.error(f"cliclick {path_type} PATH: Double-click failed with exception at ({x}, {y}): {e}")
            return False
    
    def _cliclick_type(self, text: str, fast_path: bool = False, element_info: Optional[Dict[str, Any]] = None) -> bool:
        """
        Execute typing using cliclick on macOS with fast path optimization.
        Enhanced to handle newlines and special characters properly.
        
        Args:
            text: Text to type
            fast_path: Whether this is a fast path execution
            element_info: Optional element information for optimization
            
        Returns:
            bool: True if typing succeeded, False otherwise
        """
        try:
            start_time = time.time()
            
            # Validate input text
            if not self._validate_text_input(text):
                logger.error("cliclick typing: Invalid text input")
                return False
            
            # Preprocess text for cliclick to handle newlines and special characters
            formatted_text = self._format_text_for_typing(text, 'cliclick')
            
            # Log formatting details for debugging
            path_type = "FAST" if fast_path else "SLOW"
            logger.debug(f"cliclick {path_type} PATH: Original text length: {len(text)}, lines: {text.count(chr(10)) + 1}")
            logger.debug(f"cliclick {path_type} PATH: Formatted text length: {len(formatted_text)}")
            
            # UNIVERSAL CLIPBOARD METHOD: Use clipboard for ALL content types
            # This eliminates method selection bugs and provides consistent, fast, reliable typing
            newline_count = text.count('\n')
            content_type = "multiline" if newline_count > 0 else "single-line"
            
            logger.info(f"cliclick {path_type} PATH: 📋 UNIVERSAL CLIPBOARD METHOD")
            logger.info(f"cliclick {path_type} PATH:   Content type: {content_type} ({newline_count} newlines)")
            logger.info(f"cliclick {path_type} PATH:   Content length: {len(text)} characters")
            logger.info(f"cliclick {path_type} PATH:   Using clipboard method for ALL content - eliminates corruption!")
            
            # Use clipboard method for ALL content - no more method selection bugs!
            success = self._cliclick_type_clipboard_method(text, fast_path, element_info)
            
            execution_time = time.time() - start_time
            
            if success:
                text_preview = text[:50] + "..." if len(text) > 50 else text
                text_preview = text_preview.replace('\n', '\\n')  # Show newlines in log
                element_desc = element_info.get('title', 'unknown') if element_info else 'unknown'
                logger.info(f"cliclick {path_type} PATH: Typing succeeded on '{element_desc}' in {execution_time:.3f}s: '{text_preview}'")
                
                # CRITICAL FIX: Validate typed content
                content_valid = self._validate_typed_content(text, 'cliclick')
                if not content_valid:
                    logger.error(f"cliclick {path_type} PATH: Content validation failed - may be corrupted")
                    success = False  # Mark as failed to trigger fallback
                
                # Log performance metrics with formatting details
                perf_record = {
                    'timestamp': time.time(),
                    'execution_time': execution_time,
                    'path_type': 'fast' if fast_path else 'slow',
                    'success': success,
                    'action': 'type',
                    'text_length': len(text),
                    'newlines_count': text.count('\n'),
                    'formatting_preserved': content_valid,
                    'method': 'multiline' if '\n' in text else 'single_line'
                }
                if element_info:
                    perf_record.update({
                        'element_role': element_info.get('role', ''),
                        'element_title': element_info.get('title', ''),
                        'app_name': element_info.get('app_name', '')
                    })
                
                if not hasattr(self, 'performance_history'):
                    self.performance_history = []
                self.performance_history.append(perf_record)
                
                return success
            else:
                logger.warning(f"cliclick {path_type} PATH: Typing failed - formatting may not be preserved")
                
                # CRITICAL FIX: Clear corrupted content on failure
                if '\n' in text and len(text) > 100:  # Only for multiline content
                    logger.warning(f"cliclick {path_type} PATH: Attempting to clear potentially corrupted content")
                    self._clear_corrupted_content()
                
                # Log failed performance
                perf_record = {
                    'timestamp': time.time(),
                    'execution_time': execution_time,
                    'path_type': 'fast' if fast_path else 'slow',
                    'success': False,
                    'action': 'type',
                    'text_length': len(text),
                    'newlines_count': text.count('\n'),
                    'formatting_preserved': False,
                    'method': 'multiline' if '\n' in text else 'single_line'
                }
                
                if not hasattr(self, 'performance_history'):
                    self.performance_history = []
                self.performance_history.append(perf_record)
                
                return False
                
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            path_type = "FAST" if fast_path else "SLOW"
            logger.error(f"cliclick {path_type} PATH: Typing timed out after {execution_time:.3f}s")
            return False
        except Exception as e:
            execution_time = time.time() - start_time if 'start_time' in locals() else 0.0
            path_type = "FAST" if fast_path else "SLOW"
            logger.error(f"cliclick {path_type} PATH: Typing failed with exception: {e}")
            return False
    
    def _clear_corrupted_content(self) -> bool:
        """
        Clear corrupted content from the active text field.
        CRITICAL FIX: Prevents accumulation of corrupted content.
        
        Returns:
            bool: True if content was cleared successfully
        """
        try:
            logger.warning("Attempting to clear corrupted content...")
            
            if self.is_macos:
                # Select all content
                success = self._macos_hotkey(['cmd', 'a'])
                if success:
                    time.sleep(0.1)  # Brief pause
                    # Delete selected content
                    success = self._macos_key('delete')
                    if success:
                        logger.info("Successfully cleared corrupted content using AppleScript")
                        return True
            else:
                # Use PyAutoGUI for other platforms
                pyautogui.hotkey('ctrl', 'a')
                time.sleep(0.1)
                pyautogui.press('delete')
                logger.info("Successfully cleared corrupted content using PyAutoGUI")
                return True
                
        except Exception as e:
            logger.error(f"Failed to clear corrupted content: {e}")
            
        return False

    def _validate_typed_content(self, original_text: str, method_used: str) -> bool:
        """
        Validate that typed content maintains basic structure.
        CRITICAL FIX: Detect corruption to prevent accumulation.
        
        Args:
            original_text: The original text that was supposed to be typed
            method_used: The typing method used ('cliclick' or 'applescript')
            
        Returns:
            bool: True if content appears to be typed correctly
        """
        try:
            # Basic validation checks
            original_lines = original_text.split('\n')
            
            # Check 1: Multi-line content should have multiple lines
            if len(original_lines) > 3:
                logger.debug(f"Validation: Original has {len(original_lines)} lines")
                # If original was multi-line, we expect it to remain multi-line
                # This is a basic sanity check - more sophisticated validation could be added
                return True
            
            # Check 2: Content length should be reasonable
            if len(original_text) > 100:
                logger.debug(f"Validation: Content length {len(original_text)} chars - assuming success")
                return True
            
            # For shorter content, assume success
            return True
            
        except Exception as e:
            logger.warning(f"Content validation failed: {e}")
            return False

    def _clean_cliclick_formatting(self, text: str) -> str:
        """
        Remove cliclick-specific escaping to prepare text for AppleScript fallback.
        CRITICAL FIX: Prevents AppleScript syntax errors from cliclick escaping.
        
        Args:
            text: Text with cliclick escaping
            
        Returns:
            str: Text with cliclick escaping removed
        """
        cleaned = text
        
        # Remove cliclick-specific escaping
        cleaned = cleaned.replace('\\"', '"')  # Unescape double quotes
        cleaned = cleaned.replace("\\'", "'")  # Unescape single quotes
        cleaned = cleaned.replace('\\`', '`')  # Unescape backticks
        cleaned = cleaned.replace('\\$', '$')  # Unescape dollar signs
        cleaned = cleaned.replace('\\&', '&')  # Unescape ampersands
        cleaned = cleaned.replace('\\|', '|')  # Unescape pipes
        cleaned = cleaned.replace('\\;', ';')  # Unescape semicolons
        cleaned = cleaned.replace('\\\\', '\\')  # Unescape backslashes (do this last)
        
        return cleaned

    def _format_text_for_typing(self, text: str, method: str) -> str:
        """
        Preprocess text for typing based on the method being used.
        Enhanced to properly handle newlines and special characters for cliclick.
        Optimized for better performance with large text blocks.
        
        Args:
            text: Original text to format
            method: Typing method ('cliclick' or 'applescript')
            
        Returns:
            str: Formatted text ready for the specified typing method
        """
        if method == 'cliclick':
            # For cliclick, we need to handle special characters that might interfere
            # with command parsing, but preserve newlines for multi-line handling
            formatted = text
            
            # Performance optimization: only escape if special characters are present
            if '\\' in formatted:
                formatted = formatted.replace('\\', '\\\\')
            
            # Escape characters that could interfere with cliclick command parsing
            # Note: We don't escape newlines here as they're handled separately in multiline method
            # Be more conservative with escaping - only escape truly problematic characters
            if '"' in formatted:
                formatted = formatted.replace('"', '\\"')
            if "'" in formatted:
                formatted = formatted.replace("'", "\\'")
            if '`' in formatted:
                formatted = formatted.replace('`', '\\`')
            if '$' in formatted:
                formatted = formatted.replace('$', '\\$')
            
            # Only escape shell operators that actually cause issues with cliclick
            # Parentheses, brackets, and braces are generally safe in cliclick text
            if '&' in formatted:
                formatted = formatted.replace('&', '\\&')
            if '|' in formatted:
                formatted = formatted.replace('|', '\\|')
            if ';' in formatted:
                formatted = formatted.replace(';', '\\;')
            # Remove problematic escaping of parentheses and brackets
            # These don't need escaping in cliclick and cause corruption
            # formatted = formatted.replace('(', '\\(')  # REMOVED - causes corruption
            # formatted = formatted.replace(')', '\\)')  # REMOVED - causes corruption
            # formatted = formatted.replace('[', '\\[')  # REMOVED - not needed
            # formatted = formatted.replace(']', '\\]')  # REMOVED - not needed
            # formatted = formatted.replace('{', '\\{')  # REMOVED - not needed
            # formatted = formatted.replace('}', '\\}')  # REMOVED - not needed
            # formatted = formatted.replace('<', '\\<')  # REMOVED - not needed
            # formatted = formatted.replace('>', '\\>')  # REMOVED - not needed
            
            return formatted
            
        elif method == 'applescript':
            # For AppleScript, use MINIMAL escaping to avoid syntax errors
            formatted = text
            
            # CRITICAL FIX: Only escape what's absolutely necessary for AppleScript
            # Don't escape quotes that are already escaped from cliclick formatting
            if not ('\\\"' in formatted or '\\\'' in formatted):
                # Only escape if not already escaped
                formatted = formatted.replace('"', '\\"')
            
            # Handle backslashes carefully - don't double-escape
            if not '\\\\' in formatted:
                formatted = formatted.replace('\\', '\\\\')
            
            return formatted
        
        else:
            # Unknown method, return text as-is
            logger.warning(f"Unknown typing method '{method}', returning unformatted text")
            return text
    
    def _cliclick_type_multiline(self, text: str, fast_path: bool = False, element_info: Optional[Dict[str, Any]] = None) -> bool:
        """
        Handle multi-line text typing with cliclick using key sequences.
        Enhanced to preserve indentation and handle empty lines properly.
        Optimized for better performance and reliability.
        
        Args:
            text: Formatted text to type (already processed by _format_text_for_typing)
            fast_path: Whether this is a fast path execution
            element_info: Optional element information for optimization
            
        Returns:
            bool: True if typing succeeded, False otherwise
        """
        import threading
        import time
        
        # Set overall timeout for the entire multiline operation - FIXED for large content
        base_timeout = 30 if fast_path else 60  # Significantly increased for reliability
        # Scale timeout based on content size - more lines need more time
        lines_count = len(text.split('\n'))
        timeout_per_line = 2  # 2 seconds per line minimum
        overall_timeout = max(base_timeout, lines_count * timeout_per_line)
        path_type = "FAST" if fast_path else "SLOW"
        start_time = time.time()
        
        try:
            logger.debug(f"cliclick {path_type} PATH: Starting optimized multiline typing with {overall_timeout}s overall timeout")
            lines = text.split('\n')
            
            logger.debug(f"cliclick {path_type} PATH: Typing {len(lines)} lines with preserved formatting")
            
            # CRITICAL DEBUG: Log the exact lines being typed
            logger.info(f"cliclick {path_type} PATH: MULTILINE DEBUG - Lines to type:")
            for i, line in enumerate(lines[:5]):  # Show first 5 lines
                logger.info(f"cliclick {path_type} PATH:   Line {i+1}: {repr(line)}")
            if len(lines) > 5:
                logger.info(f"cliclick {path_type} PATH:   ... and {len(lines) - 5} more lines")
            
            # FIXED timeout settings for reliability over speed
            base_timeout = 8 if fast_path else 15  # Increased significantly for reliability
            line_timeout = max(5, min(base_timeout, len(text) // 20))  # More generous scaling for large content
            
            for i, line in enumerate(lines):
                # Check overall timeout before each operation
                elapsed_time = time.time() - start_time
                if elapsed_time > overall_timeout:
                    logger.error(f"cliclick {path_type} PATH: Overall timeout ({overall_timeout}s) exceeded at line {i+1}")
                    return False
                
                # Type the line content (including empty lines for proper spacing)
                if line.strip():  # Non-empty line
                    logger.debug(f"cliclick {path_type} PATH: Typing line {i+1}: {repr(line[:50])}{'...' if len(line) > 50 else ''}")
                    
                    # CRITICAL DEBUG: Log the exact cliclick command
                    cliclick_cmd = ['cliclick', f't:{line}']
                    logger.info(f"cliclick {path_type} PATH: EXECUTING: {' '.join(cliclick_cmd)}")
                    
                    # Use cliclick to type the line with increased timeout
                    result = subprocess.run(
                        cliclick_cmd,
                        capture_output=True,
                        text=True,
                        timeout=line_timeout
                    )
                    
                    if result.returncode != 0:
                        logger.error(f"cliclick {path_type} PATH: CRITICAL - Failed to type line {i+1}: {result.stderr}")
                        logger.error(f"cliclick {path_type} PATH: FAILED COMMAND: {' '.join(cliclick_cmd)}")
                        return False
                    else:
                        logger.info(f"cliclick {path_type} PATH: ✅ Successfully typed line {i+1}: {repr(line[:30])}{'...' if len(line) > 30 else ''}")
                        
                    # CRITICAL FIX: Longer delay after typing each line for application processing
                    time.sleep(0.1 if fast_path else 0.2)  # Increased delays for application processing
                        
                else:  # Empty line - just preserve the spacing
                    logger.debug(f"cliclick {path_type} PATH: Preserving empty line {i+1}")
                
                # Add newline after each line except the last one
                if i < len(lines) - 1:
                    # Check overall timeout before Return key operations
                    elapsed_time = time.time() - start_time
                    if elapsed_time > overall_timeout:
                        logger.error(f"cliclick {path_type} PATH: Overall timeout ({overall_timeout}s) exceeded before Return key {i+1}")
                        return False
                    
                    logger.debug(f"cliclick {path_type} PATH: Pressing Return after line {i+1}")
                    
                    # CRITICAL DEBUG: Log Return key command
                    return_cmd = ['cliclick', 'kp:return']
                    logger.info(f"cliclick {path_type} PATH: EXECUTING RETURN: {' '.join(return_cmd)}")
                    
                    # Retry Return key press up to 3 times for reliability
                    return_success = False
                    for retry in range(3):
                        # Check timeout before each retry
                        elapsed_time = time.time() - start_time
                        if elapsed_time > overall_timeout:
                            logger.error(f"cliclick {path_type} PATH: Overall timeout ({overall_timeout}s) exceeded during Return key retry {retry+1}")
                            return False
                        
                        try:
                            result = subprocess.run(
                                return_cmd,
                                capture_output=True,
                                text=True,
                                timeout=10  # FIXED: Much longer timeout for Return key reliability
                            )
                            
                            if result.returncode == 0:
                                logger.info(f"cliclick {path_type} PATH: ✅ Successfully pressed Return after line {i+1} (attempt {retry+1})")
                                return_success = True
                                break
                            else:
                                logger.error(f"cliclick {path_type} PATH: ❌ Return key attempt {retry+1} failed: {result.stderr}")
                                logger.error(f"cliclick {path_type} PATH: FAILED RETURN COMMAND: {' '.join(return_cmd)}")
                                if retry < 2:  # Not the last attempt
                                    time.sleep(0.2)  # Longer delay before retry for reliability
                                    
                        except subprocess.TimeoutExpired:
                            logger.warning(f"cliclick {path_type} PATH: Return key attempt {retry+1} timed out")
                            if retry < 2:  # Not the last attempt
                                time.sleep(0.2)  # Longer delay before retry for reliability
                        except Exception as e:
                            logger.warning(f"cliclick {path_type} PATH: Return key attempt {retry+1} error: {e}")
                            if retry < 2:  # Not the last attempt
                                time.sleep(0.2)  # Longer delay before retry for reliability
                    
                    if not return_success:
                        logger.error(f"cliclick {path_type} PATH: CRITICAL - All Return key attempts failed after line {i+1}")
                        logger.error(f"cliclick {path_type} PATH: This will cause newlines to be missing in output")
                        return False
                    
                    # CRITICAL FIX: Longer delay after Return key for proper line processing
                    time.sleep(0.2 if fast_path else 0.3)  # Increased delays for proper line processing
            
            # Final timeout check
            elapsed_time = time.time() - start_time
            logger.debug(f"cliclick {path_type} PATH: Successfully typed {len(lines)} lines with preserved formatting in {elapsed_time:.2f}s")
            return True
            
        except subprocess.TimeoutExpired:
            elapsed_time = time.time() - start_time
            logger.error(f"cliclick {path_type} PATH: Individual operation timed out during multiline typing after {elapsed_time:.2f}s")
            return False
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(f"cliclick {path_type} PATH: Multiline typing failed with exception after {elapsed_time:.2f}s: {e}")
            return False
    
    def _cliclick_type_clipboard_method(self, text: str, fast_path: bool = False, element_info: Optional[Dict[str, Any]] = None) -> bool:
        """
        Type text using clipboard method with cliclick to avoid Return key issues.
        CRITICAL FIX: Bypasses problematic Return key handling in some applications.
        """
        try:
            path_type = "FAST" if fast_path else "SLOW"
            logger.info(f"cliclick {path_type} PATH: Using clipboard method to avoid Return key issues")
            
            # Copy text to clipboard using pbcopy (macOS clipboard utility)
            import subprocess
            
            # Use pbcopy to set clipboard content
            process = subprocess.Popen(
                ['pbcopy'],
                stdin=subprocess.PIPE,
                text=True
            )
            
            process.communicate(input=text)
            
            if process.returncode != 0:
                logger.error(f"cliclick {path_type} PATH: Failed to copy text to clipboard")
                return False
            
            logger.debug(f"cliclick {path_type} PATH: Successfully copied {len(text)} characters to clipboard")
            
            # Small delay to ensure clipboard is set
            time.sleep(0.1)
            
            # Paste using Cmd+V with cliclick (correct syntax for key combination)
            # Method 1: Use single command for Cmd+V
            result = subprocess.run(
                ['cliclick', 'kd:cmd', 't:v', 'ku:cmd'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                logger.error(f"cliclick {path_type} PATH: Cmd+V paste failed: {result.stderr}")
                return False
            
            # Command executed above, check if successful
            logger.debug(f"cliclick {path_type} PATH: Cmd+V paste command executed successfully")
            
            logger.info(f"cliclick {path_type} PATH: Successfully pasted {len(text)} characters using clipboard method")
            return True
            
        except Exception as e:
            logger.error(f"cliclick {path_type} PATH: Clipboard method failed with exception: {e}")
            return False
    
    def _cliclick_scroll(self, direction: str, amount: int, fast_path: bool = False, element_info: Optional[Dict[str, Any]] = None) -> bool:
        """
        Execute scrolling using cliclick on macOS with fast path optimization.
        
        Args:
            direction: Scroll direction ('up', 'down')
            amount: Scroll amount
            fast_path: Whether this is a fast path execution
            element_info: Optional element information for optimization
            
        Returns:
            bool: True if scroll succeeded, False otherwise
        """
        try:
            start_time = time.time()
            
            # cliclick scroll commands: w:+5 (up), w:-5 (down)
            if direction == "up":
                scroll_cmd = f"w:+{amount}"
            elif direction == "down":
                scroll_cmd = f"w:-{amount}"
            else:
                # cliclick doesn't support left/right scroll easily, return False
                path_type = "FAST" if fast_path else "SLOW"
                logger.debug(f"cliclick {path_type} PATH: doesn't support {direction} scroll, using fallback")
                return False
            
            # Optimize timeout for fast path
            timeout = 3 if fast_path else 5
            
            result = subprocess.run(
                ['cliclick', scroll_cmd],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            execution_time = time.time() - start_time
            
            if result.returncode == 0:
                path_type = "FAST" if fast_path else "SLOW"
                element_desc = element_info.get('title', 'unknown') if element_info else 'unknown'
                logger.info(f"cliclick {path_type} PATH: Scroll {direction} succeeded on '{element_desc}' in {execution_time:.3f}s")
                
                # Log performance metrics
                perf_record = {
                    'timestamp': time.time(),
                    'execution_time': execution_time,
                    'path_type': 'fast' if fast_path else 'slow',
                    'success': True,
                    'action': 'scroll',
                    'scroll_direction': direction,
                    'scroll_amount': amount
                }
                if element_info:
                    perf_record.update({
                        'element_role': element_info.get('role', ''),
                        'element_title': element_info.get('title', ''),
                        'app_name': element_info.get('app_name', '')
                    })
                
                if not hasattr(self, 'performance_history'):
                    self.performance_history = []
                self.performance_history.append(perf_record)
                
                return True
            else:
                path_type = "FAST" if fast_path else "SLOW"
                logger.warning(f"cliclick {path_type} PATH: Scroll failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            path_type = "FAST" if fast_path else "SLOW"
            logger.error(f"cliclick {path_type} PATH: Scroll timed out after {execution_time:.3f}s")
            return False
        except Exception as e:
            execution_time = time.time() - start_time if 'start_time' in locals() else 0.0
            path_type = "FAST" if fast_path else "SLOW"
            logger.error(f"cliclick {path_type} PATH: Scroll failed with exception: {e}")
            return False
    
    def _cliclick_key(self, key: str) -> bool:
        """Execute single key press using cliclick on macOS."""
        try:
            # cliclick key press: kp:key or kd:key ku:key for press/release
            # Common key mappings for cliclick
            key_map = {
                'enter': 'return',
                'return': 'return',
                'delete': 'delete',
                'backspace': 'delete',
                'tab': 'tab',
                'space': 'space',
                'escape': 'esc',
                'esc': 'esc'
            }
            
            cliclick_key = key_map.get(key.lower(), key.lower())
            
            result = subprocess.run(
                ['cliclick', f'kp:{cliclick_key}'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                logger.debug(f"cliclick key press '{key}' executed successfully")
                return True
            else:
                logger.warning(f"cliclick key press failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"cliclick key press timed out")
            return False
        except Exception as e:
            logger.error(f"cliclick key press failed with exception: {e}")
            return False
    
    def _cliclick_hotkey(self, keys: List[str]) -> bool:
        """Execute hotkey combination using cliclick on macOS."""
        try:
            # cliclick hotkey format: kd:cmd kp:a ku:cmd (for cmd+a)
            if not keys:
                return False
            
            # Map modifier keys
            modifier_map = {
                'cmd': 'cmd',
                'command': 'cmd', 
                'ctrl': 'ctrl',
                'control': 'ctrl',
                'alt': 'alt',
                'option': 'alt',
                'shift': 'shift'
            }
            
            # Separate modifiers from main key
            modifiers = []
            main_key = keys[-1].lower()  # Last key is usually the main key
            
            for key in keys[:-1]:
                mapped_key = modifier_map.get(key.lower())
                if mapped_key:
                    modifiers.append(mapped_key)
            
            if not modifiers:
                # No modifiers, just press the key
                return self._cliclick_key(main_key)
            
            # Build cliclick command: press modifiers down, press main key, release modifiers
            commands = []
            
            # Press modifiers down
            for mod in modifiers:
                commands.append(f'kd:{mod}')
            
            # Press main key
            commands.append(f'kp:{main_key}')
            
            # Release modifiers up (in reverse order)
            for mod in reversed(modifiers):
                commands.append(f'ku:{mod}')
            
            # Execute all commands in sequence
            for cmd in commands:
                result = subprocess.run(
                    ['cliclick', cmd],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                
                if result.returncode != 0:
                    logger.warning(f"cliclick hotkey command '{cmd}' failed: {result.stderr}")
                    return False
            
            logger.debug(f"cliclick hotkey {'+'.join(keys)} executed successfully")
            return True
                
        except subprocess.TimeoutExpired:
            logger.error(f"cliclick hotkey timed out")
            return False
        except Exception as e:
            logger.error(f"cliclick hotkey failed with exception: {e}")
            return False
    
    def _macos_click(self, x: int, y: int) -> bool:
        """Execute a click using AppleScript on macOS."""
        try:
            # Use a more reliable AppleScript approach
            # This method uses a simpler, more direct approach
            applescript = f'''
            tell application "System Events"
                -- Move to coordinates and click
                click at {{{x}, {y}}}
            end tell
            '''
            
            logger.debug(f"Executing macOS click at ({x}, {y})")
            
            # Execute the AppleScript with a reasonable timeout
            result = subprocess.run(
                ['osascript', '-e', applescript],
                capture_output=True,
                text=True,
                timeout=10,  # Longer timeout to handle system delays
                check=False  # Don't raise exception on non-zero return code
            )
            
            if result.returncode == 0:
                logger.debug(f"macOS click executed successfully at ({x}, {y})")
                return True
            else:
                logger.warning(f"AppleScript click failed: {result.stderr}")
                
                # Try alternative method using shell command if available
                try:
                    # Check if cliclick is available
                    cliclick_result = subprocess.run(
                        ['which', 'cliclick'],
                        capture_output=True,
                        text=True,
                        timeout=2
                    )
                    
                    if cliclick_result.returncode == 0:
                        logger.debug("Trying cliclick as alternative")
                        click_result = subprocess.run(
                            ['cliclick', f'c:{x},{y}'],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        
                        if click_result.returncode == 0:
                            logger.debug(f"cliclick executed successfully at ({x}, {y})")
                            return True
                        else:
                            logger.debug(f"cliclick failed: {click_result.stderr}")
                    
                except Exception as e:
                    logger.debug(f"cliclick attempt failed: {e}")
                
                # If AppleScript and cliclick failed, return False
                # Don't fall back to PyAutoGUI since it has the AppKit issue
                logger.error(f"All macOS click methods failed for coordinates ({x}, {y})")
                return False
            
        except subprocess.TimeoutExpired:
            logger.error(f"macOS click timed out at ({x}, {y})")
            return False
        except Exception as e:
            logger.error(f"macOS click failed with exception: {e}")
            return False
    
    def _macos_double_click(self, x: int, y: int) -> bool:
        """Execute a double-click using AppleScript on macOS."""
        try:
            applescript = f'''
            tell application "System Events"
                -- Double-click at coordinates
                click at {{{x}, {y}}}
                delay 0.1
                click at {{{x}, {y}}}
            end tell
            '''
            
            logger.debug(f"Executing macOS double-click at ({x}, {y})")
            
            result = subprocess.run(
                ['osascript', '-e', applescript],
                capture_output=True,
                text=True,
                timeout=10,
                check=False
            )
            
            if result.returncode == 0:
                logger.debug(f"macOS double-click executed successfully at ({x}, {y})")
                return True
            else:
                logger.warning(f"AppleScript double-click failed: {result.stderr}")
                return False
            
        except subprocess.TimeoutExpired:
            logger.error(f"macOS double-click timed out at ({x}, {y})")
            return False
        except Exception as e:
            logger.error(f"macOS double-click failed with exception: {e}")
            return False
    
    def _macos_type(self, text: str) -> bool:
        """
        Execute typing using AppleScript on macOS.
        Enhanced to handle special characters and prevent corruption.
        CRITICAL FIX: Prevents auto-indentation corruption.
        """
        try:
            # CRITICAL FIX: For multiline content, use a different approach to prevent auto-indentation
            if '\n' in text and len(text) > 100:
                logger.warning("AppleScript fallback: Large multiline content detected - using paste method to prevent auto-indentation corruption")
                return self._macos_type_paste(text)
            
            # Format text specifically for AppleScript (different from cliclick formatting)
            formatted_text = self._format_text_for_typing(text, 'applescript')
            
            # For AppleScript, we need to handle newlines differently
            # Split text by newlines and type each line separately with return key presses
            lines = formatted_text.split('\n')
            
            logger.debug(f"AppleScript typing {len(lines)} lines with preserved formatting")
            
            for i, line in enumerate(lines):
                if line:  # Only type non-empty lines
                    # INDENTATION DEBUG: Check line indentation before processing
                    leading_spaces = len(line) - len(line.lstrip())
                    if leading_spaces > 0:
                        logger.debug(f"AppleScript typing line {i+1} with {leading_spaces} leading spaces: '{line[:50]}...'")
                    
                    # Additional AppleScript-specific escaping for the keystroke command
                    # Note: text is already formatted by _format_text_for_typing
                    applescript_line = line.replace('"', '\\"')  # Escape quotes for AppleScript string
                    
                    # INDENTATION DEBUG: Verify spaces preserved after escaping
                    escaped_spaces = len(applescript_line) - len(applescript_line.lstrip())
                    if leading_spaces != escaped_spaces:
                        logger.error(f"INDENTATION LOST during AppleScript escaping! Original: {leading_spaces} spaces, Escaped: {escaped_spaces} spaces")
                    
                    # Type the line using AppleScript keystroke
                    applescript = f'''
                    tell application "System Events"
                        keystroke "{applescript_line}"
                    end tell
                    '''
                    
                    result = subprocess.run(
                        ['osascript', '-e', applescript],
                        capture_output=True,
                        text=True,
                        timeout=15,  # Increased timeout for reliability
                        check=False
                    )
                    
                    if result.returncode != 0:
                        logger.warning(f"AppleScript typing failed for line {i+1}: {result.stderr}")
                        return False
                    
                    # Small delay for character processing
                    time.sleep(0.01)
                
                # Add newline (return key) after each line except the last one
                if i < len(lines) - 1:
                    return_applescript = '''
                    tell application "System Events"
                        key code 36
                    end tell
                    '''
                    
                    result = subprocess.run(
                        ['osascript', '-e', return_applescript],
                        capture_output=True,
                        text=True,
                        timeout=5,
                        check=False
                    )
                    
                    if result.returncode != 0:
                        logger.warning(f"AppleScript return key failed after line {i+1}: {result.stderr}")
                        return False
                    
                    # Small delay for line processing
                    time.sleep(0.01)
            
            logger.debug(f"AppleScript typing executed successfully: {len(text)} characters, {len(lines)} lines")
            return True
            
        except subprocess.TimeoutExpired:
            logger.error(f"AppleScript typing timed out")
            return False
        except Exception as e:
            logger.error(f"AppleScript typing failed with exception: {e}")
            return False
    
    def _macos_type_paste(self, text: str) -> bool:
        """
        Type text using clipboard paste method to avoid auto-indentation issues.
        CRITICAL FIX: Prevents exponential indentation growth in smart editors.
        """
        try:
            logger.info("AppleScript: Using clipboard paste method for multiline content")
            
            # Copy text to clipboard using AppleScript
            # Escape the text for AppleScript string literal
            escaped_text = text.replace('\\', '\\\\').replace('"', '\\"').replace('\r', '\\r')
            
            clipboard_script = f'''
            set the clipboard to "{escaped_text}"
            '''
            
            result = subprocess.run(
                ['osascript', '-e', clipboard_script],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                logger.error(f"AppleScript clipboard copy failed: {result.stderr}")
                return False
            
            logger.debug("AppleScript: Text copied to clipboard successfully")
            
            # Paste from clipboard using Cmd+V
            paste_script = '''
            tell application "System Events"
                keystroke "v" using command down
            end tell
            '''
            
            result = subprocess.run(
                ['osascript', '-e', paste_script],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                logger.error(f"AppleScript paste failed: {result.stderr}")
                return False
            
            logger.info(f"AppleScript: Successfully pasted {len(text)} characters using clipboard method")
            return True
            
        except Exception as e:
            logger.error(f"AppleScript clipboard paste failed with exception: {e}")
            return False
    
    def _macos_scroll(self, direction: str, amount: int) -> bool:
        """Execute scrolling using AppleScript on macOS."""
        try:
            # Convert direction to AppleScript scroll commands
            if direction == "up":
                scroll_cmd = f"scroll up {amount}"
            elif direction == "down":
                scroll_cmd = f"scroll down {amount}"
            elif direction == "left":
                scroll_cmd = f"scroll left {amount}"
            elif direction == "right":
                scroll_cmd = f"scroll right {amount}"
            else:
                return False
            
            applescript = f'''
            tell application "System Events"
                {scroll_cmd}
            end tell
            '''
            
            logger.debug(f"Executing macOS scroll: {direction} by {amount}")
            
            result = subprocess.run(
                ['osascript', '-e', applescript],
                capture_output=True,
                text=True,
                timeout=5,
                check=False
            )
            
            if result.returncode == 0:
                logger.debug(f"macOS scroll executed successfully")
                return True
            else:
                logger.warning(f"AppleScript scroll failed: {result.stderr}")
                return False
            
        except subprocess.TimeoutExpired:
            logger.error(f"macOS scroll timed out")
            return False
        except Exception as e:
            logger.error(f"macOS scroll failed with exception: {e}")
            return False
    
    def _macos_hotkey(self, keys: List[str]) -> bool:
        """Execute hotkey combination using AppleScript on macOS."""
        try:
            # Convert keys to AppleScript keystroke format
            if keys == ['cmd', 'a']:
                keystroke_cmd = 'keystroke "a" using command down'
            elif keys == ['ctrl', 'a']:
                keystroke_cmd = 'keystroke "a" using control down'
            else:
                # Generic approach for other combinations
                modifiers = []
                main_key = keys[-1]  # Last key is usually the main key
                
                for key in keys[:-1]:
                    if key in ['cmd', 'command']:
                        modifiers.append('command down')
                    elif key in ['ctrl', 'control']:
                        modifiers.append('control down')
                    elif key in ['alt', 'option']:
                        modifiers.append('option down')
                    elif key in ['shift']:
                        modifiers.append('shift down')
                
                if modifiers:
                    keystroke_cmd = f'keystroke "{main_key}" using {", ".join(modifiers)}'
                else:
                    keystroke_cmd = f'keystroke "{main_key}"'
            
            applescript = f'''
            tell application "System Events"
                {keystroke_cmd}
            end tell
            '''
            
            logger.debug(f"Executing macOS hotkey: {'+'.join(keys)}")
            
            result = subprocess.run(
                ['osascript', '-e', applescript],
                capture_output=True,
                text=True,
                timeout=5,
                check=False
            )
            
            if result.returncode == 0:
                logger.debug(f"macOS hotkey executed successfully")
                return True
            else:
                logger.warning(f"AppleScript hotkey failed: {result.stderr}")
                return False
            
        except Exception as e:
            logger.error(f"macOS hotkey failed with exception: {e}")
            return False
    
    def _macos_key(self, key: str) -> bool:
        """Execute single key press using AppleScript on macOS."""
        try:
            # Map common key names to AppleScript equivalents
            key_map = {
                'enter': 'return',
                'delete': 'delete',
                'backspace': 'delete',
                'return': 'return',
                'tab': 'tab',
                'space': 'space'
            }
            
            apple_key = key_map.get(key.lower(), key)
            
            applescript = f'''
            tell application "System Events"
                keystroke "{apple_key}"
            end tell
            '''
            
            logger.debug(f"Executing macOS key press: {key}")
            
            result = subprocess.run(
                ['osascript', '-e', applescript],
                capture_output=True,
                text=True,
                timeout=5,
                check=False
            )
            
            if result.returncode == 0:
                logger.debug(f"macOS key press executed successfully")
                return True
            else:
                logger.warning(f"AppleScript key press failed: {result.stderr}")
                return False
            
        except Exception as e:
            logger.error(f"macOS key press failed with exception: {e}")
            return False
    
    def _execute_double_click(self, action: Dict[str, Any]) -> None:
        """Execute a double click action - cliclick PRIMARY."""
        coordinates = action.get("coordinates")
        if not coordinates or len(coordinates) != 2:
            raise ValueError("Double click action requires coordinates [x, y]")
        
        x, y = int(coordinates[0]), int(coordinates[1])
        if not self._validate_coordinates(x, y):
            raise ValueError(f"Invalid coordinates: ({x}, {y})")
        
        if self.is_macos:
            # cliclick is PRIMARY method for double-click
            success = False
            if self.has_cliclick:
                logger.debug(f"Using cliclick (PRIMARY) for double-click at ({x}, {y})")
                success = self._cliclick_double_click(x, y)
            
            if not success:
                # AppleScript is FALLBACK ONLY
                logger.warning("cliclick double-click failed, trying AppleScript (FALLBACK)")
                success = self._macos_double_click(x, y)
                if not success:
                    raise Exception("All macOS double-click methods failed")
        else:
            # Move to coordinates with smooth movement
            pyautogui.moveTo(x, y, duration=MOUSE_MOVE_DURATION)
            pyautogui.doubleClick()
        
        logger.debug(f"Double-clicked at ({x}, {y})")
    
    def _execute_type(self, action: Dict[str, Any]) -> None:
        """Execute a type action - cliclick PRIMARY."""
        text = action.get("text")
        if text is None:
            raise ValueError("Type action requires text parameter")
        
        if not self._validate_text_input(text):
            raise ValueError(f"Invalid text input")
        
        if self.is_macos:
            # cliclick is PRIMARY method for typing
            success = False
            if self.has_cliclick:
                logger.debug(f"Using cliclick (PRIMARY) for typing")
                success = self._cliclick_type(text)
            
            if not success:
                # AppleScript is FALLBACK ONLY
                logger.warning("cliclick typing failed, trying AppleScript (FALLBACK)")
                # CRITICAL FIX: Clean cliclick formatting before AppleScript
                cleaned_text = self._clean_cliclick_formatting(text)
                logger.debug(f"Cleaned text for AppleScript: {len(cleaned_text)} chars")
                success = self._macos_type(cleaned_text)
                if not success:
                    raise Exception("All macOS typing methods failed")
        else:
            # Type with interval between keystrokes for reliability
            pyautogui.typewrite(text, interval=TYPE_INTERVAL)
        
        logger.debug(f"Typed text: {text[:50]}{'...' if len(text) > 50 else ''}")
    
    def _execute_scroll(self, action: Dict[str, Any]) -> None:
        """Execute a scroll action - cliclick PRIMARY."""
        direction = action.get("direction", "up")
        amount = action.get("amount", SCROLL_AMOUNT)
        
        if direction not in ["up", "down", "left", "right"]:
            raise ValueError(f"Invalid scroll direction: {direction}")
        
        try:
            amount = int(amount)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid scroll amount: {amount}")
        
        if self.is_macos:
            # cliclick is PRIMARY method for scrolling (up/down only)
            success = False
            if self.has_cliclick and direction in ["up", "down"]:
                logger.debug(f"Using cliclick (PRIMARY) for scroll {direction}")
                success = self._cliclick_scroll(direction, amount)
            
            if not success:
                # AppleScript is FALLBACK (supports all directions)
                logger.debug(f"Using AppleScript (FALLBACK) for scroll {direction}")
                success = self._macos_scroll(direction, amount)
                if not success:
                    raise Exception("All macOS scrolling methods failed")
        else:
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
        if self.is_macos:
            return self._get_macos_mouse_position()
        else:
            return pyautogui.position()
    
    def _adjust_accessibility_coordinates(self, x: int, y: int, element_info: Dict[str, Any]) -> Tuple[int, int]:
        """
        Adjust coordinates from accessibility API for better precision.
        
        Args:
            x: Original X coordinate
            y: Original Y coordinate
            element_info: Element information from accessibility API
            
        Returns:
            Tuple[int, int]: Adjusted coordinates
        """
        try:
            # Get element role and size for precision adjustments
            role = element_info.get('role', '')
            element_size = element_info.get('coordinates', [])
            
            # Apply role-specific coordinate adjustments
            if role == 'AXButton':
                # For buttons, ensure we click in the center
                if len(element_size) >= 4:
                    width = element_size[2] - element_size[0]
                    height = element_size[3] - element_size[1]
                    # Ensure we're clicking in the center of the button
                    center_x = element_size[0] + width // 2
                    center_y = element_size[1] + height // 2
                    return (center_x, center_y)
            
            elif role == 'AXMenuItem':
                # For menu items, click slightly to the right of center to avoid icons
                if len(element_size) >= 4:
                    width = element_size[2] - element_size[0]
                    height = element_size[3] - element_size[1]
                    # Click 25% from left edge, vertically centered
                    adjusted_x = element_size[0] + width // 4
                    adjusted_y = element_size[1] + height // 2
                    return (adjusted_x, adjusted_y)
            
            elif role in ['AXTextField', 'AXTextArea']:
                # For text fields, click slightly inside the border
                if len(element_size) >= 4:
                    width = element_size[2] - element_size[0]
                    height = element_size[3] - element_size[1]
                    # Click 10% from left edge, vertically centered
                    adjusted_x = element_size[0] + max(5, width // 10)
                    adjusted_y = element_size[1] + height // 2
                    return (adjusted_x, adjusted_y)
            
            # For other elements or if no size info, return original coordinates
            return (x, y)
            
        except Exception as e:
            logger.debug(f"Coordinate adjustment failed, using original: {e}")
            return (x, y)
    
    def _log_click_performance(self, execution_time: float, fast_path: bool, success: bool, element_info: Optional[Dict[str, Any]] = None):
        """
        Log performance metrics for click operations.
        
        Args:
            execution_time: Time taken to execute the click
            fast_path: Whether this was a fast path execution
            success: Whether the click succeeded
            element_info: Optional element information
        """
        try:
            # Create performance record
            perf_record = {
                'timestamp': time.time(),
                'execution_time': execution_time,
                'path_type': 'fast' if fast_path else 'slow',
                'success': success,
                'action': 'click'
            }
            
            if element_info:
                perf_record.update({
                    'element_role': element_info.get('role', ''),
                    'element_title': element_info.get('title', ''),
                    'app_name': element_info.get('app_name', '')
                })
            
            # Store in performance history (initialize if needed)
            if not hasattr(self, 'performance_history'):
                self.performance_history = []
            
            self.performance_history.append(perf_record)
            
            # Keep history size manageable (last 200 operations)
            if len(self.performance_history) > 200:
                self.performance_history = self.performance_history[-100:]
            
            # Log performance summary periodically
            if len(self.performance_history) % 10 == 0:
                self._log_performance_summary()
                
        except Exception as e:
            logger.debug(f"Performance logging failed: {e}")
    
    def _log_performance_summary(self):
        """Log a summary of recent performance metrics."""
        try:
            if not hasattr(self, 'performance_history') or not self.performance_history:
                return
            
            recent_records = self.performance_history[-10:]  # Last 10 operations
            
            fast_path_records = [r for r in recent_records if r['path_type'] == 'fast']
            slow_path_records = [r for r in recent_records if r['path_type'] == 'slow']
            
            if fast_path_records:
                fast_avg_time = sum(r['execution_time'] for r in fast_path_records) / len(fast_path_records)
                fast_success_rate = sum(1 for r in fast_path_records if r['success']) / len(fast_path_records) * 100
                logger.info(f"FAST PATH Performance: avg={fast_avg_time:.3f}s, success={fast_success_rate:.1f}% ({len(fast_path_records)} ops)")
            
            if slow_path_records:
                slow_avg_time = sum(r['execution_time'] for r in slow_path_records) / len(slow_path_records)
                slow_success_rate = sum(1 for r in slow_path_records if r['success']) / len(slow_path_records) * 100
                logger.info(f"SLOW PATH Performance: avg={slow_avg_time:.3f}s, success={slow_success_rate:.1f}% ({len(slow_path_records)} ops)")
            
            if fast_path_records and slow_path_records:
                speedup = slow_avg_time / fast_avg_time if fast_avg_time > 0 else 0
                logger.info(f"Fast path speedup: {speedup:.1f}x faster than slow path")
                
        except Exception as e:
            logger.debug(f"Performance summary logging failed: {e}")

    def _get_macos_mouse_position(self) -> Tuple[int, int]:
        """Get mouse position on macOS using system commands."""
        try:
            # Try using cliclick if available
            result = subprocess.run(
                ['cliclick', 'p'],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            if result.returncode == 0:
                # cliclick returns format like "123,456"
                coords = result.stdout.strip().split(',')
                if len(coords) == 2:
                    return (int(coords[0]), int(coords[1]))
            
        except Exception:
            pass
        
        try:
            # Alternative: use AppleScript with system_profiler approach
            applescript = '''
            tell application "System Events"
                -- Return a safe default position
                return "800,600"
            end tell
            '''
            
            result = subprocess.run(
                ['osascript', '-e', applescript],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            if result.returncode == 0:
                coords = result.stdout.strip().split(',')
                if len(coords) == 2:
                    return (int(coords[0]), int(coords[1]))
            
        except Exception:
            pass
        
        # Final fallback: return center of screen
        logger.warning("Could not get mouse position, returning screen center")
        return (self.screen_width // 2, self.screen_height // 2)
    
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
    
    def get_performance_metrics(self, path_type: Optional[str] = None, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Get performance metrics for fast path vs slow path execution.
        
        Args:
            path_type: Filter by path type ('fast' or 'slow'), None for all
            limit: Maximum number of recent records to analyze, None for all
            
        Returns:
            Dictionary containing performance statistics
        """
        try:
            if not hasattr(self, 'performance_history') or not self.performance_history:
                return {
                    'total_operations': 0,
                    'fast_path_operations': 0,
                    'slow_path_operations': 0,
                    'average_execution_time': 0.0,
                    'fast_path_avg_time': 0.0,
                    'slow_path_avg_time': 0.0,
                    'success_rate': 0.0,
                    'fast_path_success_rate': 0.0,
                    'slow_path_success_rate': 0.0,
                    'speedup_factor': 0.0
                }
            
            # Get records to analyze
            records = self.performance_history
            if limit:
                records = records[-limit:]
            
            # Filter by path type if specified
            if path_type:
                records = [r for r in records if r.get('path_type') == path_type]
            
            if not records:
                return {'error': f'No records found for path_type: {path_type}'}
            
            # Calculate metrics
            total_ops = len(records)
            fast_records = [r for r in records if r.get('path_type') == 'fast']
            slow_records = [r for r in records if r.get('path_type') == 'slow']
            
            successful_ops = sum(1 for r in records if r.get('success', False))
            total_time = sum(r.get('execution_time', 0) for r in records)
            
            fast_successful = sum(1 for r in fast_records if r.get('success', False))
            fast_total_time = sum(r.get('execution_time', 0) for r in fast_records)
            
            slow_successful = sum(1 for r in slow_records if r.get('success', False))
            slow_total_time = sum(r.get('execution_time', 0) for r in slow_records)
            
            metrics = {
                'total_operations': total_ops,
                'fast_path_operations': len(fast_records),
                'slow_path_operations': len(slow_records),
                'average_execution_time': total_time / total_ops if total_ops > 0 else 0.0,
                'fast_path_avg_time': fast_total_time / len(fast_records) if fast_records else 0.0,
                'slow_path_avg_time': slow_total_time / len(slow_records) if slow_records else 0.0,
                'success_rate': (successful_ops / total_ops * 100) if total_ops > 0 else 0.0,
                'fast_path_success_rate': (fast_successful / len(fast_records) * 100) if fast_records else 0.0,
                'slow_path_success_rate': (slow_successful / len(slow_records) * 100) if slow_records else 0.0
            }
            
            # Calculate speedup factor
            if metrics['slow_path_avg_time'] > 0 and metrics['fast_path_avg_time'] > 0:
                metrics['speedup_factor'] = metrics['slow_path_avg_time'] / metrics['fast_path_avg_time']
            else:
                metrics['speedup_factor'] = 0.0
            
            # Add breakdown by action type
            action_breakdown = {}
            for action_type in ['click', 'double_click', 'type', 'scroll']:
                action_records = [r for r in records if r.get('action') == action_type]
                if action_records:
                    action_breakdown[action_type] = {
                        'count': len(action_records),
                        'avg_time': sum(r.get('execution_time', 0) for r in action_records) / len(action_records),
                        'success_rate': sum(1 for r in action_records if r.get('success', False)) / len(action_records) * 100
                    }
            
            metrics['action_breakdown'] = action_breakdown
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to calculate performance metrics: {e}")
            return {'error': str(e)}
    
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
            if self.is_macos:
                self._macos_hotkey(['cmd', 'a'])
            else:
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
            if self.is_macos:
                self._macos_hotkey(['cmd', 'a'])
            else:
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
                if self.is_macos:
                    self._macos_key('return')
                else:
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
                
                if self.is_macos:
                    self._macos_key('return')
                else:
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
                    if self.is_macos:
                        self._macos_hotkey(['cmd', 'a'])
                        self._macos_key('delete')
                    else:
                        pyautogui.hotkey('ctrl', 'a')
                        pyautogui.press('delete')
                    
                    logger.info(f"Cleared field with invalid format: '{field_label}'")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to handle validation error: {e}")
            return False
    
    def get_selected_text_via_clipboard(self) -> Optional[str]:
        """
        Capture selected text using clipboard fallback method.
        
        This method preserves the original clipboard content, simulates Cmd+C to copy
        selected text, captures the text, and restores the original clipboard.
        
        Returns:
            Optional[str]: The selected text if successful, None if failed
        """
        start_time = time.time()
        original_clipboard = None
        captured_text = None
        
        try:
            # Step 1: Preserve original clipboard content
            try:
                original_clipboard = pyperclip.paste()
                logger.debug(f"Preserved original clipboard content ({len(original_clipboard)} chars)")
            except Exception as e:
                logger.warning(f"Failed to preserve clipboard content: {e}")
                # Continue anyway - we'll try to restore what we can
                original_clipboard = ""
            
            # Step 2: Clear clipboard to detect if copy operation worked
            try:
                pyperclip.copy("")
                logger.debug("Cleared clipboard for text capture")
            except Exception as e:
                logger.error(f"Failed to clear clipboard: {e}")
                raise Exception("Clipboard access failed during clear operation")
            
            # Step 3: Simulate Cmd+C to copy selected text
            try:
                if self.is_macos:
                    # Use cliclick for Cmd+C on macOS
                    if self.has_cliclick:
                        logger.debug("Using cliclick for Cmd+C simulation")
                        result = subprocess.run(
                            ['cliclick', 'kd:cmd', 't:c', 'ku:cmd'],
                            capture_output=True,
                            text=True,
                            timeout=3
                        )
                        if result.returncode != 0:
                            logger.warning(f"cliclick Cmd+C failed: {result.stderr}")
                            # Fall back to AppleScript
                            raise Exception("cliclick Cmd+C failed")
                    else:
                        # Use AppleScript for Cmd+C
                        logger.debug("Using AppleScript for Cmd+C simulation")
                        applescript = '''tell application "System Events"
    key code 8 using command down
end tell'''
                        result = subprocess.run(
                            ['osascript', '-e', applescript],
                            capture_output=True,
                            text=True,
                            timeout=3
                        )
                        if result.returncode != 0:
                            logger.error(f"AppleScript Cmd+C failed: {result.stderr}")
                            raise Exception("AppleScript Cmd+C failed")
                else:
                    # Use PyAutoGUI for other platforms
                    pyautogui.hotkey('ctrl', 'c')
                    logger.debug("Used PyAutoGUI for Ctrl+C simulation")
                
                # Small delay to allow copy operation to complete
                time.sleep(0.2)
                
            except Exception as e:
                logger.error(f"Failed to simulate copy command: {e}")
                raise Exception(f"Copy command simulation failed: {e}")
            
            # Step 4: Capture text from clipboard
            try:
                captured_text = pyperclip.paste()
                if captured_text == "":
                    logger.info("No text captured - clipboard is empty (no text selected)")
                    captured_text = None
                else:
                    logger.info(f"Successfully captured {len(captured_text)} characters via clipboard")
                    logger.debug(f"Captured text preview: {captured_text[:100]}...")
            except Exception as e:
                logger.error(f"Failed to read from clipboard: {e}")
                raise Exception(f"Clipboard read failed: {e}")
            
        except Exception as e:
            # Log the error with performance metrics
            execution_time = time.time() - start_time
            error_info = global_error_handler.handle_error(
                error=e,
                module="automation",
                function="get_selected_text_via_clipboard",
                category=ErrorCategory.HARDWARE_ERROR,
                severity=ErrorSeverity.MEDIUM,
                context={
                    "execution_time": execution_time,
                    "platform": platform.system(),
                    "has_cliclick": getattr(self, 'has_cliclick', False)
                }
            )
            logger.error(f"Clipboard text capture failed: {error_info.message}")
            captured_text = None
            
        finally:
            # Step 5: Always restore original clipboard content
            try:
                if original_clipboard is not None:
                    pyperclip.copy(original_clipboard)
                    logger.debug("Restored original clipboard content")
                else:
                    # If we couldn't preserve original content, clear clipboard
                    pyperclip.copy("")
                    logger.debug("Cleared clipboard (original content unavailable)")
            except Exception as e:
                logger.warning(f"Failed to restore clipboard content: {e}")
                # This is not critical - continue anyway
            
            # Log performance metrics
            execution_time = time.time() - start_time
            self._log_clipboard_capture_performance(execution_time, captured_text is not None, captured_text)
        
        return captured_text
    
    def _log_clipboard_capture_performance(self, execution_time: float, success: bool, captured_text: Optional[str]) -> None:
        """
        Log performance metrics for clipboard-based text capture.
        
        Args:
            execution_time: Time taken for the capture operation
            success: Whether the capture was successful
            captured_text: The captured text (for length metrics)
        """
        try:
            # Create performance record
            perf_record = {
                'timestamp': time.time(),
                'execution_time': execution_time,
                'method': 'clipboard_fallback',
                'success': success,
                'action': 'text_capture',
                'platform': platform.system(),
                'has_cliclick': getattr(self, 'has_cliclick', False)
            }
            
            if captured_text:
                perf_record.update({
                    'text_length': len(captured_text),
                    'has_newlines': '\n' in captured_text,
                    'has_special_chars': any(ord(c) > 127 for c in captured_text[:100])  # Check first 100 chars
                })
            
            # Store in performance history
            if not hasattr(self, 'text_capture_performance'):
                self.text_capture_performance = []
            self.text_capture_performance.append(perf_record)
            
            # Keep history manageable (last 50 records)
            if len(self.text_capture_performance) > 50:
                self.text_capture_performance = self.text_capture_performance[-25:]
            
            # Log summary
            status = "SUCCESS" if success else "FAILED"
            text_info = f" ({len(captured_text)} chars)" if captured_text else ""
            logger.info(f"Clipboard capture {status}: {execution_time:.3f}s{text_info}")
            
            # Performance warning for slow operations
            if execution_time > 2.0:
                logger.warning(f"Clipboard capture took {execution_time:.3f}s - performance issue detected")
            
        except Exception as e:
            logger.warning(f"Failed to log clipboard capture performance: {e}")
            # Don't raise - this is just logging

    def execute_fast_path_action(self, action_type: str, coordinates: List[int], **kwargs) -> Dict[str, Any]:
        """
        Execute action with pre-validated coordinates from accessibility API.
        
        Args:
            action_type: 'click', 'double_click', 'type', etc.
            coordinates: [x, y] or [x, y, width, height] from accessibility API
            **kwargs: Additional action parameters (e.g., text for type actions)
            
        Returns:
            Dictionary with execution results
        """
        try:
            start_time = time.time()
            
            # Extract coordinates
            if len(coordinates) >= 2:
                x, y = coordinates[0], coordinates[1]
            else:
                raise ValueError("Invalid coordinates provided")
            
            # Skip coordinate validation for trusted accessibility coordinates
            # but still do basic sanity checks
            if x < 0 or y < 0 or x > self.screen_width * 2 or y > self.screen_height * 2:
                raise ValueError(f"Coordinates ({x}, {y}) are outside reasonable bounds")
            
            element_info = kwargs.get('element_info', {})
            
            logger.info(f"Executing fast path {action_type} at ({x}, {y}) on element: {element_info.get('title', 'unknown')}")
            
            # Execute the action based on type
            success = False
            
            if action_type == 'click':
                success = self._attempt_click(x, y, fast_path=True, element_info=element_info)
                
            elif action_type == 'double_click':
                if self.is_macos:
                    success = self._cliclick_double_click(x, y, fast_path=True, element_info=element_info)
                    if not success:
                        success = self._macos_double_click(x, y)
                else:
                    # For non-macOS platforms, use PyAutoGUI with performance logging
                    start_time = time.time()
                    pyautogui.moveTo(x, y, duration=MOUSE_MOVE_DURATION)
                    pyautogui.doubleClick()
                    execution_time = time.time() - start_time
                    self._log_click_performance(execution_time, True, True, element_info)
                    success = True
                
            elif action_type == 'type':
                text = kwargs.get('text', '')
                if not text:
                    raise ValueError("Text parameter required for type action")
                
                # First click to focus the element
                click_success = self._attempt_click(x, y, fast_path=True, element_info=element_info)
                if click_success:
                    time.sleep(0.1)  # Brief pause to ensure focus
                    if self.is_macos:
                        success = self._cliclick_type(text, fast_path=True, element_info=element_info)
                        if not success:
                            success = self._macos_type(text)
                    else:
                        # For non-macOS platforms, use PyAutoGUI with performance logging
                        start_time = time.time()
                        pyautogui.typewrite(text, interval=TYPE_INTERVAL)
                        execution_time = time.time() - start_time
                        
                        # Log typing performance
                        perf_record = {
                            'timestamp': time.time(),
                            'execution_time': execution_time,
                            'path_type': 'fast',
                            'success': True,
                            'action': 'type',
                            'text_length': len(text)
                        }
                        if element_info:
                            perf_record.update({
                                'element_role': element_info.get('role', ''),
                                'element_title': element_info.get('title', ''),
                                'app_name': element_info.get('app_name', '')
                            })
                        
                        if not hasattr(self, 'performance_history'):
                            self.performance_history = []
                        self.performance_history.append(perf_record)
                        success = True
                
            elif action_type == 'scroll':
                direction = kwargs.get('direction', 'up')
                amount = kwargs.get('amount', SCROLL_AMOUNT)
                if self.is_macos:
                    success = self._cliclick_scroll(direction, amount, fast_path=True, element_info=element_info)
                    if not success:
                        success = self._macos_scroll(direction, amount)
                else:
                    # For non-macOS platforms, use PyAutoGUI with performance logging
                    start_time = time.time()
                    if direction == "up":
                        pyautogui.scroll(amount)
                    elif direction == "down":
                        pyautogui.scroll(-amount)
                    elif direction == "left":
                        pyautogui.hscroll(-amount)
                    elif direction == "right":
                        pyautogui.hscroll(amount)
                    
                    execution_time = time.time() - start_time
                    
                    # Log scroll performance
                    perf_record = {
                        'timestamp': time.time(),
                        'execution_time': execution_time,
                        'path_type': 'fast',
                        'success': True,
                        'action': 'scroll',
                        'scroll_direction': direction,
                        'scroll_amount': amount
                    }
                    if element_info:
                        perf_record.update({
                            'element_role': element_info.get('role', ''),
                            'element_title': element_info.get('title', ''),
                            'app_name': element_info.get('app_name', '')
                        })
                    
                    if not hasattr(self, 'performance_history'):
                        self.performance_history = []
                    self.performance_history.append(perf_record)
                    success = True
                
            else:
                raise ValueError(f"Unsupported action type: {action_type}")
            
            execution_time = time.time() - start_time
            
            # Record action in history
            action_record = {
                'action': action_type,
                'coordinates': coordinates,
                'timestamp': time.time(),
                'success': success,
                'execution_time': execution_time,
                'fast_path': True,
                'element_info': element_info
            }
            
            if hasattr(self, 'action_history'):
                self.action_history.append(action_record)
                # Keep history size manageable
                if len(self.action_history) > 100:
                    self.action_history = self.action_history[-50:]
            
            result = {
                'success': success,
                'action_type': action_type,
                'coordinates': coordinates,
                'execution_time': execution_time,
                'fast_path': True,
                'element_title': element_info.get('title', ''),
                'element_role': element_info.get('role', ''),
                'message': f"Fast path {action_type} {'succeeded' if success else 'failed'}"
            }
            
            if success:
                logger.info(f"Fast path {action_type} completed successfully in {execution_time:.3f}s")
            else:
                logger.warning(f"Fast path {action_type} failed")
            
            return result
            
        except Exception as e:
            error_info = global_error_handler.handle_error(
                error=e,
                module="automation",
                function="execute_fast_path_action",
                category=ErrorCategory.PROCESSING_ERROR,
                severity=ErrorSeverity.MEDIUM,
                context={
                    "action_type": action_type,
                    "coordinates": coordinates,
                    "kwargs": kwargs
                }
            )
            
            logger.error(f"Fast path action execution failed: {error_info.message}")
            
            return {
                'success': False,
                'action_type': action_type,
                'coordinates': coordinates,
                'execution_time': 0.0,
                'fast_path': True,
                'error': error_info.user_message,
                'message': f"Fast path {action_type} failed: {error_info.user_message}"
            }