# orchestrator.py
"""
AURA Orchestrator

Central coordinator that manages the perception-reasoning-action loop.
Coordinates all modules to execute user commands and answer questions.
"""

import logging
import time
import threading
import asyncio
import concurrent.futures
import re
from typing import Dict, Any, Optional, List, Callable, Tuple
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime

from modules.vision import VisionModule
from modules.reasoning import ReasoningModule
from modules.automation import AutomationModule
from modules.audio import AudioModule
from modules.feedback import FeedbackModule, FeedbackPriority

logger = logging.getLogger(__name__)


class CommandStatus(Enum):
    """Status of command execution."""
    PENDING = "pending"
    VALIDATING = "validating"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExecutionStep(Enum):
    """Individual execution steps."""
    VALIDATION = "validation"
    PERCEPTION = "perception"
    REASONING = "reasoning"
    ACTION = "action"
    CLEANUP = "cleanup"


@dataclass
class ProgressReport:
    """Progress report for command execution."""
    execution_id: str
    command: str
    status: CommandStatus
    current_step: Optional[ExecutionStep]
    steps_completed: List[ExecutionStep] = field(default_factory=list)
    progress_percentage: float = 0.0
    estimated_remaining_time: Optional[float] = None
    start_time: float = field(default_factory=time.time)
    last_update: float = field(default_factory=time.time)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class CommandValidationResult:
    """Result of command validation."""
    is_valid: bool
    normalized_command: str
    command_type: str
    confidence: float
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


class OrchestratorError(Exception):
    """Custom exception for orchestrator errors."""
    pass


class Orchestrator:
    """
    Central coordinator for AURA system.
    
    Manages the perception-reasoning-action loop by coordinating all modules
    to execute user commands and answer questions with comprehensive error handling.
    """
    
    def __init__(self):
        """Initialize the Orchestrator with all required modules."""
        self.vision_module = None
        self.reasoning_module = None
        self.automation_module = None
        self.audio_module = None
        self.feedback_module = None
        
        # Command tracking
        self.current_command = None
        self.command_status = CommandStatus.PENDING
        self.command_history = []
        self.execution_lock = threading.Lock()
        
        # Progress tracking
        self.current_progress = None
        self.progress_callbacks = []
        self.progress_lock = threading.Lock()
        
        # Error handling
        self.max_retries = 2
        self.retry_delay = 1.0
        
        # Parallel processing
        self.thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=3)
        self.enable_parallel_processing = True
        
        # Command validation patterns
        self._init_validation_patterns()
        
        # Initialize modules
        self._initialize_modules()
        
        logger.info("Orchestrator initialized successfully")
    
    def _init_validation_patterns(self) -> None:
        """Initialize command validation patterns."""
        self.command_patterns = {
            'click': [
                r'click\s+(?:on\s+)?(?:the\s+)?(.+)',
                r'press\s+(?:the\s+)?(.+)',
                r'tap\s+(?:on\s+)?(?:the\s+)?(.+)'
            ],
            'type': [
                r'type\s+["\'](.+)["\']',
                r'enter\s+["\'](.+)["\']',
                r'input\s+["\'](.+)["\']',
                r'write\s+["\'](.+)["\']'
            ],
            'scroll': [
                r'scroll\s+(up|down|left|right)',
                r'scroll\s+(up|down|left|right)\s+(\d+)',
                r'page\s+(up|down)'
            ],
            'question': [
                r'what\s+(?:is|are|does|do)\s+(.+)\?',
                r'where\s+(?:is|are)\s+(.+)\?',
                r'how\s+(?:do|can)\s+(?:i|you)\s+(.+)\?',
                r'tell\s+me\s+about\s+(.+)',
                r'explain\s+(.+)'
            ],
            'form_fill': [
                r'fill\s+(?:out\s+)?(?:the\s+)?form',
                r'complete\s+(?:the\s+)?form',
                r'submit\s+(?:the\s+)?form'
            ]
        }
        
        # Common command preprocessing rules
        self.preprocessing_rules = [
            (r'(?i)\b(?:please|could you|can you|would you)\b', ''),  # Remove politeness words
            (r'(?i)\b(?:the|a|an)\b', ''),  # Remove articles for better matching
            (r'[^\w\s\'".,!?-]', ''),  # Remove special characters except basic punctuation
            (r'\s+', ' '),  # Normalize whitespace (must be last)
        ]
    
    def _initialize_modules(self) -> None:
        """Initialize all required modules with error handling."""
        try:
            logger.info("Initializing AURA modules...")
            
            # Initialize modules in dependency order
            self.vision_module = VisionModule()
            self.reasoning_module = ReasoningModule()
            self.automation_module = AutomationModule()
            self.audio_module = AudioModule()
            self.feedback_module = FeedbackModule(audio_module=self.audio_module)
            
            logger.info("All modules initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize modules: {e}")
            raise OrchestratorError(f"Module initialization failed: {e}")
    
    def validate_command(self, command: str) -> CommandValidationResult:
        """
        Validate and preprocess a user command.
        
        Args:
            command: Raw user command
            
        Returns:
            CommandValidationResult with validation details
        """
        if not command or not command.strip():
            return CommandValidationResult(
                is_valid=False,
                normalized_command="",
                command_type="invalid",
                confidence=0.0,
                issues=["Command is empty or contains only whitespace"]
            )
        
        # Preprocess command
        normalized_command = self._preprocess_command(command.strip())
        
        # Detect command type and validate
        command_type, confidence = self._detect_command_type(normalized_command)
        
        # Check for common issues
        issues = []
        suggestions = []
        
        # Length validation
        if len(normalized_command) > 500:
            issues.append("Command is too long (>500 characters)")
            suggestions.append("Try breaking down your request into smaller commands")
        
        if len(normalized_command) < 3:
            issues.append("Command is too short to be meaningful")
            suggestions.append("Please provide more specific instructions")
        
        # Content validation
        if command_type == "unknown" and confidence < 0.3:
            issues.append("Command intent is unclear")
            suggestions.append("Try using more specific action words like 'click', 'type', or 'scroll'")
        
        # Check for potentially dangerous commands
        dangerous_patterns = [
            r'(?i)\b(?:delete|remove|format|shutdown|restart)\b',
            r'(?i)\b(?:sudo|admin|administrator)\b',
            r'(?i)\b(?:password|credit card|ssn|social security)\b'
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, normalized_command):
                issues.append("Command may contain sensitive or dangerous operations")
                suggestions.append("Please be cautious with system-level operations")
                break
        
        # Only consider critical issues as invalid (too long, dangerous operations)
        critical_issues = [issue for issue in issues if "too long" in issue or "dangerous" in issue]
        is_valid = len(critical_issues) == 0
        
        return CommandValidationResult(
            is_valid=is_valid,
            normalized_command=normalized_command,
            command_type=command_type,
            confidence=confidence,
            issues=issues,
            suggestions=suggestions
        )
    
    def _preprocess_command(self, command: str) -> str:
        """
        Preprocess command text for better parsing.
        
        Args:
            command: Raw command text
            
        Returns:
            Preprocessed command text
        """
        processed = command.lower()
        
        # Apply preprocessing rules
        for pattern, replacement in self.preprocessing_rules:
            processed = re.sub(pattern, replacement, processed)
        
        return processed.strip()
    
    def _detect_command_type(self, command: str) -> Tuple[str, float]:
        """
        Detect the type of command and confidence level.
        
        Args:
            command: Preprocessed command text
            
        Returns:
            Tuple of (command_type, confidence_score)
        """
        best_match = ("unknown", 0.0)
        
        for cmd_type, patterns in self.command_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, command)
                if match:
                    # Calculate confidence based on match quality
                    match_length = len(match.group(0))
                    command_length = len(command)
                    confidence = min(0.9, match_length / command_length + 0.1)
                    
                    if confidence > best_match[1]:
                        best_match = (cmd_type, confidence)
        
        return best_match
    
    def add_progress_callback(self, callback: Callable[[ProgressReport], None]) -> None:
        """
        Add a callback function to receive progress updates.
        
        Args:
            callback: Function to call with progress updates
        """
        with self.progress_lock:
            self.progress_callbacks.append(callback)
    
    def remove_progress_callback(self, callback: Callable[[ProgressReport], None]) -> None:
        """
        Remove a progress callback function.
        
        Args:
            callback: Function to remove from callbacks
        """
        with self.progress_lock:
            if callback in self.progress_callbacks:
                self.progress_callbacks.remove(callback)
    
    def _update_progress(self, execution_id: str, status: CommandStatus, 
                        current_step: Optional[ExecutionStep] = None,
                        progress_percentage: float = None,
                        error: str = None, warning: str = None) -> None:
        """
        Update progress and notify callbacks.
        
        Args:
            execution_id: Current execution ID
            status: Current status
            current_step: Current execution step
            progress_percentage: Progress percentage (0-100)
            error: Error message to add
            warning: Warning message to add
        """
        with self.progress_lock:
            if not self.current_progress or self.current_progress.execution_id != execution_id:
                return
            
            # Update progress
            self.current_progress.status = status
            if current_step:
                self.current_progress.current_step = current_step
                if current_step not in self.current_progress.steps_completed:
                    self.current_progress.steps_completed.append(current_step)
            
            if progress_percentage is not None:
                self.current_progress.progress_percentage = progress_percentage
            
            if error:
                self.current_progress.errors.append(error)
            
            if warning:
                self.current_progress.warnings.append(warning)
            
            self.current_progress.last_update = time.time()
            
            # Notify callbacks
            for callback in self.progress_callbacks:
                try:
                    callback(self.current_progress)
                except Exception as e:
                    logger.warning(f"Progress callback failed: {e}")
    
    def get_current_progress(self) -> Optional[ProgressReport]:
        """
        Get current execution progress.
        
        Returns:
            Current progress report or None if no execution in progress
        """
        with self.progress_lock:
            return self.current_progress
    
    def execute_command(self, command: str) -> Dict[str, Any]:
        """
        Execute a user command using the perception-reasoning-action loop with validation and parallel processing.
        
        Args:
            command: Natural language command from user
            
        Returns:
            Dictionary containing execution results and metadata
            
        Raises:
            OrchestratorError: If command execution fails
        """
        if not command or not command.strip():
            raise ValueError("Command cannot be empty")
        
        # Ensure only one command executes at a time
        with self.execution_lock:
            return self._execute_command_internal(command.strip())
    
    def _execute_command_internal(self, command: str) -> Dict[str, Any]:
        """Internal command execution with validation, parallel processing, and comprehensive error handling."""
        execution_id = f"cmd_{int(time.time() * 1000)}"
        start_time = time.time()
        
        # Initialize execution context
        execution_context = {
            "execution_id": execution_id,
            "command": command,
            "start_time": start_time,
            "status": CommandStatus.VALIDATING,
            "steps_completed": [],
            "errors": [],
            "warnings": [],
            "validation_result": None,
            "screen_context": None,
            "action_plan": None,
            "execution_results": None
        }
        
        self.current_command = execution_context
        self.command_status = CommandStatus.VALIDATING
        
        # Initialize progress tracking
        with self.progress_lock:
            self.current_progress = ProgressReport(
                execution_id=execution_id,
                command=command,
                status=CommandStatus.VALIDATING,
                current_step=ExecutionStep.VALIDATION
            )
        
        try:
            logger.info(f"Starting command execution [{execution_id}]: '{command}'")
            
            # Step 1: Command Validation and Preprocessing
            logger.info(f"[{execution_id}] Step 1: Command validation")
            self._update_progress(execution_id, CommandStatus.VALIDATING, ExecutionStep.VALIDATION, 10)
            
            validation_result = self.validate_command(command)
            execution_context["validation_result"] = validation_result
            execution_context["steps_completed"].append(ExecutionStep.VALIDATION)
            
            if not validation_result.is_valid:
                error_msg = f"Command validation failed: {'; '.join(validation_result.issues)}"
                execution_context["errors"].append(error_msg)
                raise OrchestratorError(error_msg)
            
            # Use normalized command for processing
            normalized_command = validation_result.normalized_command
            logger.info(f"[{execution_id}] Command validated and normalized: '{normalized_command}'")
            
            # Provide initial feedback
            self.feedback_module.play("thinking", FeedbackPriority.NORMAL)
            
            # Step 2: Parallel Perception and Reasoning Preparation
            execution_context["status"] = CommandStatus.PROCESSING
            self._update_progress(execution_id, CommandStatus.PROCESSING, ExecutionStep.PERCEPTION, 25)
            
            if self.enable_parallel_processing and validation_result.command_type in ['click', 'type', 'scroll']:
                # For GUI commands, we can start perception and prepare reasoning in parallel
                logger.info(f"[{execution_id}] Using parallel processing for perception and reasoning")
                screen_context, action_plan = self._perform_parallel_perception_reasoning(execution_context, normalized_command)
            else:
                # Sequential processing for complex commands or when parallel processing is disabled
                logger.info(f"[{execution_id}] Using sequential processing")
                screen_context = self._perform_screen_perception(execution_context)
                self._update_progress(execution_id, CommandStatus.PROCESSING, ExecutionStep.REASONING, 60)
                action_plan = self._perform_command_reasoning(execution_context, normalized_command)
            
            execution_context["screen_context"] = screen_context
            execution_context["action_plan"] = action_plan
            execution_context["steps_completed"].extend([ExecutionStep.PERCEPTION, ExecutionStep.REASONING])
            
            # Step 3: Action Execution
            logger.info(f"[{execution_id}] Step 3: Action execution")
            self._update_progress(execution_id, CommandStatus.PROCESSING, ExecutionStep.ACTION, 80)
            
            execution_results = self._perform_action_execution(execution_context)
            execution_context["execution_results"] = execution_results
            execution_context["steps_completed"].append(ExecutionStep.ACTION)
            
            # Command completed successfully
            execution_context["status"] = CommandStatus.COMPLETED
            execution_context["end_time"] = time.time()
            execution_context["total_duration"] = execution_context["end_time"] - start_time
            
            # Final progress update
            self._update_progress(execution_id, CommandStatus.COMPLETED, ExecutionStep.CLEANUP, 100)
            
            # Provide success feedback
            self.feedback_module.play("success", FeedbackPriority.NORMAL)
            
            # Add to history
            self.command_history.append(execution_context.copy())
            
            logger.info(f"[{execution_id}] Command completed successfully in {execution_context['total_duration']:.2f}s")
            
            return self._format_execution_result(execution_context)
            
        except Exception as e:
            # Handle execution failure
            execution_context["status"] = CommandStatus.FAILED
            execution_context["end_time"] = time.time()
            execution_context["total_duration"] = execution_context["end_time"] - start_time
            execution_context["errors"].append(str(e))
            
            # Update progress with failure
            self._update_progress(execution_id, CommandStatus.FAILED, error=str(e))
            
            # Provide failure feedback
            self.feedback_module.play("failure", FeedbackPriority.HIGH)
            self.feedback_module.speak(
                f"I encountered an error while executing your command: {str(e)}", 
                FeedbackPriority.HIGH
            )
            
            # Add to history
            self.command_history.append(execution_context.copy())
            
            logger.error(f"[{execution_id}] Command execution failed: {e}")
            
            return self._format_execution_result(execution_context)
        
        finally:
            self.current_command = None
            self.command_status = CommandStatus.PENDING
            # Clear progress tracking
            with self.progress_lock:
                self.current_progress = None
    
    def _perform_screen_perception(self, execution_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform screen perception step with retry logic.
        
        Args:
            execution_context: Current execution context
            
        Returns:
            Screen analysis results
            
        Raises:
            OrchestratorError: If perception fails after retries
        """
        execution_id = execution_context["execution_id"]
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                logger.debug(f"[{execution_id}] Screen perception attempt {attempt + 1}")
                
                # Capture and analyze screen
                screen_context = self.vision_module.describe_screen()
                
                # Validate screen context
                if not screen_context or "elements" not in screen_context:
                    raise OrchestratorError("Invalid screen analysis result")
                
                logger.info(f"[{execution_id}] Screen perception successful: {len(screen_context.get('elements', []))} elements found")
                return screen_context
                
            except Exception as e:
                last_error = e
                logger.warning(f"[{execution_id}] Screen perception attempt {attempt + 1} failed: {e}")
                
                if attempt < self.max_retries:
                    logger.info(f"[{execution_id}] Retrying screen perception in {self.retry_delay}s...")
                    time.sleep(self.retry_delay)
        
        # All attempts failed
        error_msg = f"Screen perception failed after {self.max_retries + 1} attempts: {last_error}"
        execution_context["errors"].append(error_msg)
        raise OrchestratorError(error_msg)
    
    def _perform_parallel_perception_reasoning(self, execution_context: Dict[str, Any], 
                                             normalized_command: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Perform perception and reasoning in parallel where possible.
        
        Args:
            execution_context: Current execution context
            normalized_command: Preprocessed command
            
        Returns:
            Tuple of (screen_context, action_plan)
            
        Raises:
            OrchestratorError: If parallel processing fails
        """
        execution_id = execution_context["execution_id"]
        
        try:
            logger.debug(f"[{execution_id}] Starting parallel perception and reasoning")
            
            # Submit both tasks to thread pool
            perception_future = self.thread_pool.submit(self._perform_screen_perception, execution_context)
            
            # Wait for perception to complete first (reasoning needs screen context)
            screen_context = perception_future.result(timeout=30)  # 30 second timeout
            
            # Now start reasoning with screen context
            reasoning_future = self.thread_pool.submit(
                self._perform_command_reasoning, execution_context, normalized_command, screen_context
            )
            
            # Update progress after perception completes
            self._update_progress(execution_id, CommandStatus.PROCESSING, ExecutionStep.REASONING, 60)
            
            # Wait for reasoning to complete
            action_plan = reasoning_future.result(timeout=30)  # 30 second timeout
            
            logger.info(f"[{execution_id}] Parallel processing completed successfully")
            return screen_context, action_plan
            
        except concurrent.futures.TimeoutError as e:
            error_msg = f"Parallel processing timed out: {e}"
            execution_context["errors"].append(error_msg)
            raise OrchestratorError(error_msg)
        except Exception as e:
            error_msg = f"Parallel processing failed: {e}"
            execution_context["errors"].append(error_msg)
            raise OrchestratorError(error_msg)
    
    def _perform_command_reasoning(self, execution_context: Dict[str, Any], 
                                 command: str = None, screen_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Perform command reasoning step with retry logic.
        
        Args:
            execution_context: Current execution context
            command: Command to process (uses context command if not provided)
            screen_context: Screen context (uses context screen_context if not provided)
            
        Returns:
            Action plan from reasoning module
            
        Raises:
            OrchestratorError: If reasoning fails after retries
        """
        execution_id = execution_context["execution_id"]
        command = command or execution_context["command"]
        screen_context = screen_context or execution_context["screen_context"]
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                logger.debug(f"[{execution_id}] Command reasoning attempt {attempt + 1}")
                
                # Generate action plan
                action_plan = self.reasoning_module.get_action_plan(command, screen_context)
                
                # Validate action plan
                if not action_plan or "plan" not in action_plan:
                    raise OrchestratorError("Invalid action plan result")
                
                if not action_plan["plan"]:
                    raise OrchestratorError("Empty action plan received")
                
                logger.info(f"[{execution_id}] Command reasoning successful: {len(action_plan['plan'])} actions planned")
                return action_plan
                
            except Exception as e:
                last_error = e
                logger.warning(f"[{execution_id}] Command reasoning attempt {attempt + 1} failed: {e}")
                
                if attempt < self.max_retries:
                    logger.info(f"[{execution_id}] Retrying command reasoning in {self.retry_delay}s...")
                    time.sleep(self.retry_delay)
        
        # All attempts failed
        error_msg = f"Command reasoning failed after {self.max_retries + 1} attempts: {last_error}"
        execution_context["errors"].append(error_msg)
        raise OrchestratorError(error_msg)
    
    def _perform_action_execution(self, execution_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform action execution step.
        
        Args:
            execution_context: Current execution context
            
        Returns:
            Action execution results
            
        Raises:
            OrchestratorError: If critical actions fail
        """
        execution_id = execution_context["execution_id"]
        action_plan = execution_context["action_plan"]
        actions = action_plan["plan"]
        
        logger.info(f"[{execution_id}] Executing {len(actions)} actions")
        
        execution_results = {
            "total_actions": len(actions),
            "successful_actions": 0,
            "failed_actions": 0,
            "action_details": [],
            "errors": []
        }
        
        for i, action in enumerate(actions):
            action_start_time = time.time()
            action_result = {
                "index": i,
                "action": action.copy(),
                "start_time": action_start_time,
                "status": "pending"
            }
            
            try:
                logger.debug(f"[{execution_id}] Executing action {i + 1}/{len(actions)}: {action.get('action', 'unknown')}")
                
                # Handle different action types
                action_type = action.get("action")
                
                if action_type in ["click", "double_click", "type", "scroll"]:
                    # GUI automation actions
                    self.automation_module.execute_action(action)
                    action_result["status"] = "success"
                    execution_results["successful_actions"] += 1
                    
                elif action_type == "speak":
                    # TTS feedback action
                    message = action.get("message", "")
                    if message:
                        self.feedback_module.speak(message, FeedbackPriority.NORMAL)
                    action_result["status"] = "success"
                    execution_results["successful_actions"] += 1
                    
                elif action_type == "finish":
                    # Task completion marker
                    action_result["status"] = "success"
                    execution_results["successful_actions"] += 1
                    logger.info(f"[{execution_id}] Task completion marker reached")
                    
                else:
                    # Unknown action type
                    error_msg = f"Unknown action type: {action_type}"
                    action_result["status"] = "failed"
                    action_result["error"] = error_msg
                    execution_results["failed_actions"] += 1
                    execution_results["errors"].append(error_msg)
                    logger.warning(f"[{execution_id}] {error_msg}")
                
                action_result["end_time"] = time.time()
                action_result["duration"] = action_result["end_time"] - action_start_time
                
                logger.debug(f"[{execution_id}] Action {i + 1} completed: {action_result['status']}")
                
            except Exception as e:
                # Action execution failed
                action_result["status"] = "failed"
                action_result["error"] = str(e)
                action_result["end_time"] = time.time()
                action_result["duration"] = action_result["end_time"] - action_start_time
                
                execution_results["failed_actions"] += 1
                execution_results["errors"].append(f"Action {i + 1} failed: {str(e)}")
                
                logger.error(f"[{execution_id}] Action {i + 1} failed: {e}")
                
                # Decide whether to continue or stop
                if self._is_critical_action_failure(action, e):
                    logger.error(f"[{execution_id}] Critical action failure, stopping execution")
                    execution_context["warnings"].append("Execution stopped due to critical action failure")
                    break
                else:
                    logger.info(f"[{execution_id}] Non-critical action failure, continuing execution")
            
            execution_results["action_details"].append(action_result)
        
        logger.info(f"[{execution_id}] Action execution completed: {execution_results['successful_actions']}/{execution_results['total_actions']} successful")
        
        return execution_results
    
    def _is_critical_action_failure(self, action: Dict[str, Any], error: Exception) -> bool:
        """
        Determine if an action failure is critical enough to stop execution.
        
        Args:
            action: The failed action
            error: The error that occurred
            
        Returns:
            True if failure is critical, False otherwise
        """
        action_type = action.get("action", "")
        error_str = str(error).lower()
        
        # Critical failures that should stop execution
        critical_conditions = [
            # System-level failures
            "failsafe" in error_str,
            "permission denied" in error_str,
            "access denied" in error_str,
            
            # Screen/coordinate failures for click actions
            action_type in ["click", "double_click"] and "coordinate" in error_str,
            
            # Multiple consecutive failures (would need additional tracking)
        ]
        
        return any(critical_conditions)
    
    def _format_execution_result(self, execution_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format execution context into a clean result dictionary.
        
        Args:
            execution_context: Complete execution context
            
        Returns:
            Formatted execution result
        """
        result = {
            "execution_id": execution_context["execution_id"],
            "command": execution_context["command"],
            "status": execution_context["status"].value,
            "duration": execution_context.get("total_duration", 0.0),
            "steps_completed": execution_context["steps_completed"],
            "success": execution_context["status"] == CommandStatus.COMPLETED
        }
        
        # Add execution details if available
        if execution_context.get("execution_results"):
            exec_results = execution_context["execution_results"]
            result["actions_executed"] = exec_results["successful_actions"]
            result["actions_failed"] = exec_results["failed_actions"]
            result["total_actions"] = exec_results["total_actions"]
        
        # Add errors and warnings if any
        if execution_context["errors"]:
            result["errors"] = execution_context["errors"]
        
        if execution_context["warnings"]:
            result["warnings"] = execution_context["warnings"]
        
        # Add metadata
        screen_context = execution_context.get("screen_context") or {}
        action_plan = execution_context.get("action_plan") or {}
        validation_result = execution_context.get("validation_result")
        
        result["metadata"] = {
            "screen_elements_found": len(screen_context.get("elements", [])),
            "action_plan_confidence": action_plan.get("metadata", {}).get("confidence", 0.0),
            "execution_timestamp": execution_context["start_time"],
            "command_validation": {
                "command_type": validation_result.command_type if validation_result else "unknown",
                "confidence": validation_result.confidence if validation_result else 0.0,
                "normalized_command": validation_result.normalized_command if validation_result else command
            } if validation_result else None
        }
        
        return result
    
    def answer_question(self, question: str) -> Dict[str, Any]:
        """
        Answer a question about screen content using information extraction mode.
        
        Args:
            question: User's question about screen content
            
        Returns:
            Dictionary containing answer and metadata
            
        Raises:
            OrchestratorError: If question answering fails
        """
        if not question or not question.strip():
            raise ValueError("Question cannot be empty")
        
        question = question.strip()
        execution_id = f"qa_{int(time.time() * 1000)}"
        start_time = time.time()
        
        try:
            logger.info(f"[{execution_id}] Processing question: '{question}'")
            
            # Provide thinking feedback
            self.feedback_module.play("thinking", FeedbackPriority.NORMAL)
            
            # Capture and analyze screen for information
            logger.info(f"[{execution_id}] Analyzing screen for information")
            screen_context = self.vision_module.describe_screen()
            
            # Create a special reasoning prompt for Q&A
            qa_command = f"Please analyze the screen content and answer this question: {question}"
            
            # Use reasoning module to generate answer
            logger.info(f"[{execution_id}] Generating answer using reasoning module")
            action_plan = self.reasoning_module.get_action_plan(qa_command, screen_context)
            
            # Extract answer from action plan (should contain speak actions with the answer)
            answer = self._extract_answer_from_plan(action_plan)
            
            # Provide the answer via TTS
            if answer:
                self.feedback_module.speak(answer, FeedbackPriority.NORMAL)
            else:
                fallback_answer = "I couldn't find the information you're looking for on the current screen."
                self.feedback_module.speak(fallback_answer, FeedbackPriority.NORMAL)
                answer = fallback_answer
            
            # Format result
            result = {
                "execution_id": execution_id,
                "question": question,
                "answer": answer,
                "status": "completed",
                "duration": time.time() - start_time,
                "success": True,
                "metadata": {
                    "screen_elements_analyzed": len(screen_context.get("elements", [])),
                    "confidence": action_plan.get("metadata", {}).get("confidence", 0.0),
                    "timestamp": start_time
                }
            }
            
            logger.info(f"[{execution_id}] Question answered successfully")
            return result
            
        except Exception as e:
            logger.error(f"[{execution_id}] Question answering failed: {e}")
            
            # Provide error feedback
            self.feedback_module.play("failure", FeedbackPriority.HIGH)
            error_message = f"I encountered an error while trying to answer your question: {str(e)}"
            self.feedback_module.speak(error_message, FeedbackPriority.HIGH)
            
            # Return error result
            return {
                "execution_id": execution_id,
                "question": question,
                "answer": error_message,
                "status": "failed",
                "duration": time.time() - start_time,
                "success": False,
                "error": str(e),
                "metadata": {
                    "timestamp": start_time
                }
            }
    
    def _extract_answer_from_plan(self, action_plan: Dict[str, Any]) -> str:
        """
        Extract answer text from an action plan generated for Q&A.
        
        Args:
            action_plan: Action plan from reasoning module
            
        Returns:
            Extracted answer text
        """
        try:
            actions = action_plan.get("plan", [])
            
            # Look for speak actions that contain the answer
            answer_parts = []
            for action in actions:
                if action.get("action") == "speak":
                    message = action.get("message", "")
                    if message:
                        answer_parts.append(message)
            
            # Combine all speak messages into a single answer
            if answer_parts:
                return " ".join(answer_parts)
            
            return ""
            
        except Exception as e:
            logger.error(f"Error extracting answer from action plan: {e}")
            return ""
    
    def get_current_status(self) -> Dict[str, Any]:
        """
        Get current orchestrator status and execution information.
        
        Returns:
            Dictionary containing current status
        """
        status = {
            "status": self.command_status.value,
            "modules_initialized": {
                "vision": self.vision_module is not None,
                "reasoning": self.reasoning_module is not None,
                "automation": self.automation_module is not None,
                "audio": self.audio_module is not None,
                "feedback": self.feedback_module is not None
            },
            "command_history_count": len(self.command_history),
            "current_command": None
        }
        
        # Add current command info if executing
        if self.current_command:
            status["current_command"] = {
                "execution_id": self.current_command["execution_id"],
                "command": self.current_command["command"],
                "steps_completed": self.current_command["steps_completed"],
                "duration": time.time() - self.current_command["start_time"]
            }
        
        return status
    
    def get_command_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get command execution history.
        
        Args:
            limit: Maximum number of recent commands to return
            
        Returns:
            List of command execution results
        """
        if limit is None:
            return [self._format_execution_result(ctx) for ctx in self.command_history]
        else:
            recent_history = self.command_history[-limit:] if self.command_history else []
            return [self._format_execution_result(ctx) for ctx in recent_history]
    
    def clear_command_history(self) -> int:
        """
        Clear command execution history.
        
        Returns:
            Number of commands cleared
        """
        count = len(self.command_history)
        self.command_history.clear()
        logger.info(f"Cleared {count} commands from history")
        return count
    
    def validate_modules(self) -> Dict[str, Any]:
        """
        Validate that all modules are properly initialized and functional.
        
        Returns:
            Dictionary containing validation results
        """
        validation_result = {
            "overall_status": "unknown",
            "modules": {},
            "errors": [],
            "warnings": []
        }
        
        try:
            # Check each module
            modules_to_check = [
                ("vision", self.vision_module),
                ("reasoning", self.reasoning_module),
                ("automation", self.automation_module),
                ("audio", self.audio_module),
                ("feedback", self.feedback_module)
            ]
            
            all_modules_ok = True
            
            for module_name, module_instance in modules_to_check:
                module_status = {
                    "initialized": module_instance is not None,
                    "functional": False,
                    "errors": [],
                    "warnings": []
                }
                
                if module_instance is not None:
                    # Try to validate module functionality
                    try:
                        if hasattr(module_instance, 'validate_audio_input') and module_name == "audio":
                            # Audio module has specific validation
                            audio_validation = module_instance.validate_audio_input()
                            module_status["functional"] = not audio_validation.get("errors", [])
                            module_status["errors"] = audio_validation.get("errors", [])
                            module_status["warnings"] = audio_validation.get("warnings", [])
                        
                        elif hasattr(module_instance, 'validate_sound_files') and module_name == "feedback":
                            # Feedback module has specific validation
                            feedback_validation = module_instance.validate_sound_files()
                            module_status["functional"] = not feedback_validation.get("errors", [])
                            module_status["errors"] = feedback_validation.get("errors", [])
                            module_status["warnings"] = feedback_validation.get("warnings", [])
                        
                        else:
                            # Basic functionality check
                            module_status["functional"] = True
                    
                    except Exception as e:
                        module_status["functional"] = False
                        module_status["errors"].append(f"Validation failed: {str(e)}")
                        all_modules_ok = False
                else:
                    all_modules_ok = False
                    module_status["errors"].append("Module not initialized")
                
                validation_result["modules"][module_name] = module_status
                
                # Aggregate errors and warnings
                validation_result["errors"].extend([f"{module_name}: {err}" for err in module_status["errors"]])
                validation_result["warnings"].extend([f"{module_name}: {warn}" for warn in module_status["warnings"]])
            
            # Determine overall status
            if all_modules_ok and not validation_result["errors"]:
                validation_result["overall_status"] = "healthy"
            elif all_modules_ok and validation_result["errors"]:
                validation_result["overall_status"] = "degraded"
            else:
                validation_result["overall_status"] = "unhealthy"
            
        except Exception as e:
            validation_result["overall_status"] = "error"
            validation_result["errors"].append(f"Validation process failed: {str(e)}")
        
        return validation_result
    
    def cleanup(self) -> None:
        """Clean up orchestrator and all modules."""
        try:
            logger.info("Cleaning up Orchestrator...")
            
            # Shutdown thread pool
            if hasattr(self, 'thread_pool'):
                logger.info("Shutting down thread pool...")
                self.thread_pool.shutdown(wait=True)
            
            # Clear progress tracking
            with self.progress_lock:
                self.current_progress = None
                self.progress_callbacks.clear()
            
            # Clear command history
            self.command_history.clear()
            self.current_command = None
            self.command_status = CommandStatus.PENDING
            
            # Clean up modules in reverse order
            modules_to_cleanup = [
                ("feedback", self.feedback_module),
                ("audio", self.audio_module),
                ("automation", self.automation_module),
                ("reasoning", self.reasoning_module),
                ("vision", self.vision_module)
            ]
            
            for module_name, module_instance in modules_to_cleanup:
                if module_instance and hasattr(module_instance, 'cleanup'):
                    try:
                        logger.info(f"Cleaning up {module_name} module...")
                        module_instance.cleanup()
                    except Exception as e:
                        logger.error(f"Error cleaning up {module_name} module: {e}")
            
            # Clear command history
            self.command_history.clear()
            self.current_command = None
            self.command_status = CommandStatus.PENDING
            
            logger.info("Orchestrator cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during Orchestrator cleanup: {e}")