# utils/mouse_listener.py
"""
Global Mouse Listener for AURA Deferred Actions

Provides cross-platform global mouse event detection for deferred action workflows.
Uses pynput library for reliable mouse event capture across all applications.
"""

import logging
import threading
import time
from typing import Callable, Optional, Tuple
from enum import Enum

try:
    from pynput import mouse
    from pynput.mouse import Button, Listener
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False
    mouse = None
    Button = None
    Listener = None

logger = logging.getLogger(__name__)


class MouseButton(Enum):
    """Mouse button enumeration."""
    LEFT = "left"
    RIGHT = "right"
    MIDDLE = "middle"


class GlobalMouseListener:
    """
    Global mouse event listener for deferred action workflows.
    
    Captures mouse clicks across all applications and triggers callbacks
    when clicks are detected. Designed for use in deferred action scenarios
    where the user needs to specify a target location by clicking.
    """
    
    def __init__(self, callback: Callable[[], None]):
        """
        Initialize the global mouse listener.
        
        Args:
            callback: Function to call when a mouse click is detected
        """
        if not PYNPUT_AVAILABLE:
            raise ImportError(
                "pynput library is required for GlobalMouseListener. "
                "Install it with: pip install pynput"
            )
        
        self.callback = callback
        self.listener = None
        self.is_listening = False
        self.listener_thread = None
        self.start_time = None
        self.click_coordinates = None
        
        # Configuration
        self.sensitivity = 1.0  # Click detection sensitivity
        self.auto_stop_after_click = True  # Stop listening after first click
        
        logger.debug("GlobalMouseListener initialized")
    
    def start(self) -> None:
        """
        Start listening for mouse events in a background daemon thread.
        
        The listener runs in a separate daemon thread to avoid blocking
        the main application. It will automatically stop after the first
        click if auto_stop_after_click is True.
        """
        if self.is_listening:
            logger.warning("Mouse listener is already running")
            return
        
        if not PYNPUT_AVAILABLE:
            logger.error("Cannot start mouse listener: pynput not available")
            raise RuntimeError("pynput library not available")
        
        try:
            logger.info("Starting global mouse listener")
            
            # Create and configure the listener
            self.listener = Listener(
                on_click=self._on_click_internal,
                suppress=False  # Don't suppress mouse events
            )
            
            # Start the listener in a daemon thread
            self.listener_thread = threading.Thread(
                target=self._listener_thread_worker,
                daemon=True,
                name="GlobalMouseListener"
            )
            
            self.is_listening = True
            self.start_time = time.time()
            self.click_coordinates = None
            
            self.listener_thread.start()
            logger.info("Global mouse listener started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start mouse listener: {e}")
            self.is_listening = False
            raise
    
    def stop(self) -> None:
        """
        Stop listening for mouse events and cleanup resources.
        
        Properly stops the listener thread and cleans up all resources.
        Safe to call multiple times.
        """
        if not self.is_listening:
            logger.debug("Mouse listener is not running")
            return
        
        try:
            logger.info("Stopping global mouse listener")
            
            self.is_listening = False
            
            # Stop the pynput listener
            if self.listener:
                self.listener.stop()
                self.listener = None
            
            # Wait for thread to finish (with timeout)
            if self.listener_thread and self.listener_thread.is_alive():
                self.listener_thread.join(timeout=2.0)
                if self.listener_thread.is_alive():
                    logger.warning("Mouse listener thread did not stop gracefully")
            
            self.listener_thread = None
            
            # Calculate listening duration
            if self.start_time:
                duration = time.time() - self.start_time
                logger.info(f"Mouse listener stopped after {duration:.2f} seconds")
                self.start_time = None
            
            logger.info("Global mouse listener stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping mouse listener: {e}")
            # Force cleanup
            self.is_listening = False
            self.listener = None
            self.listener_thread = None
    
    def _listener_thread_worker(self) -> None:
        """
        Worker function for the listener thread.
        
        Starts the pynput listener and handles any exceptions that occur
        during listener operation.
        """
        try:
            logger.debug("Mouse listener thread started")
            
            if self.listener:
                # This call blocks until the listener is stopped
                self.listener.join()
            
            logger.debug("Mouse listener thread finished")
            
        except Exception as e:
            logger.error(f"Mouse listener thread error: {e}")
            self.is_listening = False
        finally:
            # Ensure cleanup happens
            if self.listener:
                try:
                    self.listener.stop()
                except:
                    pass
                self.listener = None
    
    def _on_click_internal(self, x: int, y: int, button: Button, pressed: bool) -> Optional[bool]:
        """
        Internal click handler that processes mouse events.
        
        Args:
            x: X coordinate of the click
            y: Y coordinate of the click
            button: Mouse button that was clicked
            pressed: True if button was pressed, False if released
            
        Returns:
            False to stop the listener, None to continue listening
        """
        try:
            # Only process button press events (not releases)
            if not pressed:
                return None
            
            # Store click coordinates
            self.click_coordinates = (x, y)
            
            # Convert pynput button to our enum
            if button == Button.left:
                mouse_button = MouseButton.LEFT
            elif button == Button.right:
                mouse_button = MouseButton.RIGHT
            elif button == Button.middle:
                mouse_button = MouseButton.MIDDLE
            else:
                mouse_button = MouseButton.LEFT  # Default fallback
            
            logger.info(f"Mouse click detected at ({x}, {y}) with {mouse_button.value} button")
            
            # Call the user-provided callback
            try:
                self.callback()
            except Exception as e:
                logger.error(f"Error in mouse click callback: {e}")
            
            # Stop listening after first click if configured to do so
            if self.auto_stop_after_click:
                logger.debug("Auto-stopping mouse listener after click")
                return False  # This stops the listener
            
            return None  # Continue listening
            
        except Exception as e:
            logger.error(f"Error processing mouse click: {e}")
            return False  # Stop listener on error
    
    def get_last_click_coordinates(self) -> Optional[Tuple[int, int]]:
        """
        Get the coordinates of the last detected click.
        
        Returns:
            Tuple of (x, y) coordinates, or None if no click detected
        """
        return self.click_coordinates
    
    def is_active(self) -> bool:
        """
        Check if the mouse listener is currently active.
        
        Returns:
            True if listening for mouse events, False otherwise
        """
        return self.is_listening and self.listener is not None
    
    def get_listening_duration(self) -> Optional[float]:
        """
        Get the duration the listener has been active.
        
        Returns:
            Duration in seconds, or None if not currently listening
        """
        if self.start_time and self.is_listening:
            return time.time() - self.start_time
        return None
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        try:
            self.stop()
        except:
            pass  # Ignore errors during cleanup


# Utility function for quick mouse listener setup
def create_mouse_listener(callback: Callable[[], None], auto_start: bool = False) -> GlobalMouseListener:
    """
    Create a GlobalMouseListener with the specified callback.
    
    Args:
        callback: Function to call when a mouse click is detected
        auto_start: Whether to automatically start listening
        
    Returns:
        Configured GlobalMouseListener instance
    """
    listener = GlobalMouseListener(callback)
    
    if auto_start:
        listener.start()
    
    return listener


# Check if pynput is available for mouse listening
def is_mouse_listener_available() -> bool:
    """
    Check if mouse listener functionality is available.
    
    Returns:
        True if pynput is available and mouse listening is supported
    """
    return PYNPUT_AVAILABLE