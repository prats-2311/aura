"""
Base Handler for AURA Command Processing

This module defines the abstract base class that all AURA command handlers must inherit from.
It provides a standardized interface for command processing, error handling, and result formatting.
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class HandlerResult:
    """Standardized result format for all handler operations."""
    status: str  # success, error, waiting_for_user_action
    message: str
    timestamp: float
    execution_time: Optional[float] = None
    method: Optional[str] = None  # fast_path, vision_fallback, etc.
    metadata: Optional[Dict[str, Any]] = None


class BaseHandler(ABC):
    """
    Abstract base class for all AURA command handlers.
    
    This class defines the standard interface that all handlers must implement,
    including the main handle() method, standardized result creation, and
    consistent error handling and logging patterns.
    
    All handlers receive a reference to the orchestrator to access shared
    modules (vision, reasoning, automation, audio, etc.) and system state.
    """
    
    def __init__(self, orchestrator_ref):
        """
        Initialize the handler with orchestrator reference.
        
        Args:
            orchestrator_ref: Reference to the main Orchestrator instance
                             for accessing shared modules and system state
        """
        self.orchestrator = orchestrator_ref
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info(f"{self.__class__.__name__} initialized")
    
    @abstractmethod
    def handle(self, command: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a command and return execution results.
        
        This is the main entry point for all command processing. Each handler
        must implement this method to process commands of their specific type.
        
        Args:
            command: The user command to process (e.g., "click the button")
            context: Additional context including:
                    - intent: Intent recognition results
                    - timestamp: Command timestamp
                    - execution_id: Unique execution identifier
                    - system_state: Current system state information
            
        Returns:
            Dictionary containing execution results and metadata:
            {
                "status": "success|error|waiting_for_user_action",
                "message": "Human-readable result message",
                "timestamp": float,
                "execution_time": float (optional),
                "method": "execution_method" (optional),
                "metadata": {...} (optional)
            }
        """
        pass
    
    def _create_success_result(self, message: str, **kwargs) -> Dict[str, Any]:
        """
        Create a standardized success result.
        
        Args:
            message: Success message for the user
            **kwargs: Additional metadata to include in the result
            
        Returns:
            Standardized success result dictionary
        """
        result = {
            "status": "success",
            "message": message,
            "timestamp": time.time()
        }
        
        # Add any additional metadata
        if kwargs:
            result.update(kwargs)
            
        self.logger.info(f"Success: {message}")
        return result
    
    def _create_error_result(self, message: str, error: Optional[Exception] = None, **kwargs) -> Dict[str, Any]:
        """
        Create a standardized error result.
        
        Args:
            message: Error message for the user
            error: Optional exception that caused the error
            **kwargs: Additional metadata to include in the result
            
        Returns:
            Standardized error result dictionary
        """
        result = {
            "status": "error",
            "message": message,
            "timestamp": time.time()
        }
        
        # Add any additional metadata
        if kwargs:
            result.update(kwargs)
            
        # Log the error with appropriate level
        if error:
            self.logger.error(f"Error: {message} - Exception: {str(error)}")
        else:
            self.logger.error(f"Error: {message}")
            
        return result
    
    def _create_waiting_result(self, message: str, **kwargs) -> Dict[str, Any]:
        """
        Create a standardized waiting result for deferred actions.
        
        Args:
            message: Message explaining what the system is waiting for
            **kwargs: Additional metadata to include in the result
            
        Returns:
            Standardized waiting result dictionary
        """
        result = {
            "status": "waiting_for_user_action",
            "message": message,
            "timestamp": time.time()
        }
        
        # Add any additional metadata
        if kwargs:
            result.update(kwargs)
            
        self.logger.info(f"Waiting for user action: {message}")
        return result
    
    def _log_execution_start(self, command: str, context: Dict[str, Any]) -> float:
        """
        Log the start of command execution and return start time.
        
        Args:
            command: The command being executed
            context: Execution context
            
        Returns:
            Start time for execution timing
        """
        execution_id = context.get('execution_id', 'unknown')
        intent = context.get('intent', {}).get('intent', 'unknown')
        
        self.logger.info(f"[{execution_id}] Starting {self.__class__.__name__} execution")
        self.logger.debug(f"[{execution_id}] Command: '{command[:100]}...'")
        self.logger.debug(f"[{execution_id}] Intent: {intent}")
        
        return time.time()
    
    def _log_execution_end(self, start_time: float, result: Dict[str, Any], context: Dict[str, Any]) -> None:
        """
        Log the end of command execution with timing and result information.
        
        Args:
            start_time: Execution start time
            result: Execution result
            context: Execution context
        """
        execution_time = time.time() - start_time
        execution_id = context.get('execution_id', 'unknown')
        status = result.get('status', 'unknown')
        
        self.logger.info(f"[{execution_id}] {self.__class__.__name__} execution completed")
        self.logger.info(f"[{execution_id}] Status: {status}, Time: {execution_time:.3f}s")
        
        # Add execution time to result if not already present
        if 'execution_time' not in result:
            result['execution_time'] = execution_time
    
    def _validate_command(self, command: str) -> bool:
        """
        Validate that a command is not empty or invalid.
        
        Args:
            command: Command to validate
            
        Returns:
            True if command is valid, False otherwise
        """
        if not command or not command.strip():
            self.logger.error("Command validation failed: empty or whitespace-only command")
            return False
        
        if len(command.strip()) > 1000:  # Reasonable length limit
            self.logger.warning(f"Command is very long ({len(command)} chars), may cause issues")
        
        return True
    
    def _get_module_safely(self, module_name: str):
        """
        Safely get a module from the orchestrator with error handling.
        
        Args:
            module_name: Name of the module to retrieve
            
        Returns:
            Module instance or None if not available
        """
        try:
            module = getattr(self.orchestrator, module_name, None)
            if module is None:
                self.logger.warning(f"Module '{module_name}' not available in orchestrator")
            return module
        except Exception as e:
            self.logger.error(f"Error accessing module '{module_name}': {e}")
            return None
    
    def _handle_module_error(self, module_name: str, error: Exception, operation: str) -> Dict[str, Any]:
        """
        Handle errors from module operations with consistent logging and error reporting.
        
        Args:
            module_name: Name of the module that failed
            error: The exception that occurred
            operation: Description of the operation that failed
            
        Returns:
            Standardized error result
        """
        error_message = f"{module_name} module failed during {operation}: {str(error)}"
        self.logger.error(error_message)
        
        return self._create_error_result(
            f"I encountered an issue with {operation}. Please try again.",
            error=error,
            module=module_name,
            operation=operation
        )