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
from modules.accessibility import AccessibilityModule
from modules.error_handler import (
    global_error_handler,
    with_error_handling,
    ErrorCategory,
    ErrorSeverity,
    ErrorInfo
)
from modules.performance import (
    parallel_processor,
    measure_performance,
    PerformanceMetrics,
    performance_monitor
)

# Import debugging and diagnostic tools
from modules.diagnostic_tools import AccessibilityHealthChecker
from modules.error_recovery import ErrorRecoveryManager

# Import content extraction modules for fast path
from modules.browser_accessibility import BrowserAccessibilityHandler
from modules.pdf_handler import PDFHandler
from modules.application_detector import ApplicationType

# Import enhanced fallback configuration
from config import (
    ENHANCED_FALLBACK_ENABLED,
    FALLBACK_PERFORMANCE_LOGGING,
    FALLBACK_RETRY_DELAY,
    MAX_FALLBACK_RETRIES,
    FALLBACK_TIMEOUT_THRESHOLD
)

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
        self.accessibility_module = None
        
        # Debugging and diagnostic tools
        self.diagnostic_tools = None
        self.error_recovery_manager = None
        self.debug_mode_enabled = False
        
        # Content extraction modules for fast path
        self.browser_accessibility_handler = None
        self.pdf_handler = None
        
        # Fast path configuration
        self.fast_path_enabled = True
        
        # Command tracking
        self.current_command = None
        self.command_status = CommandStatus.PENDING
        self.command_history = []
        self.execution_lock = threading.Lock()
        
        # Progress tracking
        self.current_progress = None
        self.progress_callbacks = []
        self.progress_lock = threading.Lock()
        
        # Error handling and recovery
        self.max_retries = 2
        self.retry_delay = 1.0
        self.error_recovery_enabled = True
        self.graceful_degradation_enabled = True
        self.system_health_status = {}
        self.module_availability = {}
        
        # Parallel processing
        self.thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=3)
        self.enable_parallel_processing = True
        self.parallel_perception_reasoning = True
        
        # Conversational Enhancement State Management
        # Intent recognition and routing state
        self.intent_recognition_enabled = True
        self.last_recognized_intent = None
        
        # Deferred action state management
        self.is_waiting_for_user_action = False
        self.deferred_action_executing = False  # NEW: Prevents race conditions during execution
        self.pending_action_payload = None
        self.deferred_action_type = None
        self.deferred_action_start_time = None
        self.deferred_action_timeout_time = None
        self.current_deferred_content_type = None  # Track content type for enhanced feedback
        self.mouse_listener = None
        self.mouse_listener_active = False
        
        # Enhanced state tracking for validation and consistency
        self.system_mode = 'ready'  # 'ready', 'processing', 'waiting_for_user'
        self.current_execution_id = None
        self.state_transition_history = []
        self.last_state_validation_time = None
        
        # Conversational context state
        self.conversation_history = []
        self.current_conversation_context = {}
        
        # State management locks for thread safety
        self.intent_lock = threading.Lock()
        self.deferred_action_lock = threading.Lock()
        self.conversation_lock = threading.Lock()
        self.state_validation_lock = threading.Lock()
        
        # Configuration for state management
        self.deferred_action_timeout_seconds = 300.0  # 5 minutes default
        self.state_validation_interval = 30.0  # Validate state every 30 seconds
        self.max_state_history_entries = 50
        
        # Command validation patterns
        self._init_validation_patterns()
        
        # Initialize modules with error handling
        self._initialize_modules()
        
        # Initialize system health monitoring
        self._initialize_system_health()
        
        # Initialize command handlers
        self._initialize_handlers()
        
        # Background preloading state
        self.last_active_app = None
        self.background_preload_enabled = True
        
        # Start periodic state validation
        self._start_periodic_state_validation()
        
        logger.info("Orchestrator initialized successfully")
    
    def _initialize_handlers(self):
        """Initialize command handlers for the new modular architecture."""
        try:
            # Import handler classes
            from handlers.gui_handler import GUIHandler
            from handlers.conversation_handler import ConversationHandler
            from handlers.deferred_action_handler import DeferredActionHandler
            from handlers.question_answering_handler import QuestionAnsweringHandler
            
            # Initialize handlers with orchestrator reference
            self.gui_handler = GUIHandler(self)
            self.conversation_handler = ConversationHandler(self)
            self.deferred_action_handler = DeferredActionHandler(self)
            self.question_answering_handler = QuestionAnsweringHandler(self)
            
            logger.info("Command handlers initialized successfully")
            
        except ImportError as e:
            logger.error(f"Failed to import handler classes: {e}")
            # Set handlers to None so we can fall back to legacy methods
            self.gui_handler = None
            self.conversation_handler = None
            self.deferred_action_handler = None
            self.question_answering_handler = None
            
        except Exception as e:
            logger.error(f"Failed to initialize handlers: {e}")
            # Set handlers to None so we can fall back to legacy methods
            self.gui_handler = None
            self.conversation_handler = None
            self.deferred_action_handler = None
            self.question_answering_handler = None
    
    def _recognize_intent(self, command: str) -> Dict[str, Any]:
        """
        Recognize the intent of a user command using LLM-based classification.
        
        Args:
            command: The user command to classify
            
        Returns:
            Dictionary containing intent classification results
        """
        try:
            from config import INTENT_RECOGNITION_PROMPT
            # Set a reasonable timeout for intent recognition
            INTENT_RECOGNITION_TIMEOUT = 15.0
            
            logger.debug(f"Recognizing intent for command: {command}")
            
            # Check if reasoning module is available
            if not self.reasoning_module or not self.module_availability.get('reasoning', False):
                logger.warning("Reasoning module unavailable, defaulting to GUI interaction intent")
                return {
                    "intent": "gui_interaction",
                    "confidence": 0.5,
                    "parameters": {
                        "action_type": "unknown",
                        "target": command,
                        "content_type": "unknown"
                    },
                    "reasoning": "Reasoning module unavailable, using fallback"
                }
            
            # Format the prompt with the user command
            formatted_prompt = INTENT_RECOGNITION_PROMPT.format(command=command)
            
            # Use reasoning module to classify intent
            start_time = time.time()
            response = self.reasoning_module._make_api_request(formatted_prompt)
            
            # Parse JSON response from API
            try:
                import json
                
                # Extract content from API response
                if isinstance(response, dict):
                    # Handle different response formats
                    content = None
                    if 'choices' in response and response['choices']:
                        # OpenAI-style response
                        content = response['choices'][0].get('message', {}).get('content', '')
                    elif 'response' in response:
                        # Ollama-style response
                        content = response['response']
                    elif 'content' in response:
                        # Direct content response
                        content = response['content']
                    else:
                        # Try to use the response directly if it's a string
                        content = str(response)
                else:
                    content = str(response)
                
                if not content:
                    raise ValueError("Empty response content from reasoning module")
                
                # Try to extract JSON from the content
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    intent_result = json.loads(json_str)
                else:
                    # Try parsing the entire content
                    intent_result = json.loads(content)
                
                # Validate required fields
                required_fields = ["intent", "confidence", "parameters", "reasoning"]
                if not all(field in intent_result for field in required_fields):
                    raise ValueError("Missing required fields in intent recognition response")
                
                # Validate intent type
                valid_intents = ["gui_interaction", "conversational_chat", "deferred_action", "question_answering"]
                if intent_result["intent"] not in valid_intents:
                    logger.warning(f"Invalid intent type: {intent_result['intent']}, defaulting to gui_interaction")
                    intent_result["intent"] = "gui_interaction"
                
                # Ensure confidence is within valid range
                confidence = float(intent_result["confidence"])
                if confidence < 0.0 or confidence > 1.0:
                    confidence = max(0.0, min(1.0, confidence))
                    intent_result["confidence"] = confidence
                
                processing_time = time.time() - start_time
                logger.info(f"Intent recognized: {intent_result['intent']} (confidence: {confidence:.2f}, time: {processing_time:.2f}s)")
                
                return intent_result
                
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                logger.error(f"Failed to parse intent recognition response: {e}")
                logger.debug(f"Raw response: {response}")
                
                # Fallback to simple heuristic classification
                return self._fallback_intent_classification(command)
                
        except Exception as e:
            logger.error(f"Intent recognition failed: {e}")
            return self._fallback_intent_classification(command)
    
    def _fallback_intent_classification(self, command: str) -> Dict[str, Any]:
        """
        Fallback intent classification using simple heuristics.
        
        Args:
            command: The user command to classify
            
        Returns:
            Dictionary containing fallback intent classification
        """
        command_lower = command.lower().strip()
        
        # Conversational patterns
        conversational_patterns = [
            "hello", "hi", "hey", "good morning", "good afternoon", "good evening",
            "how are you", "what's up", "thanks", "thank you", "goodbye", "bye",
            "tell me about", "what do you think", "can you help", "i need help"
        ]
        
        # Deferred action patterns
        deferred_patterns = [
            "write code", "generate code", "create a function", "write a script",
            "write an essay", "create content", "generate text", "write a letter",
            "compose", "draft"
        ]
        
        # Question answering patterns
        question_patterns = [
            "what is", "what does", "how does", "why does", "where is",
            "when is", "who is", "explain", "describe", "summarize",
            "what's on the screen", "what do you see"
        ]
        
        # Check for conversational intent
        if any(pattern in command_lower for pattern in conversational_patterns):
            return {
                "intent": "conversational_chat",
                "confidence": 0.8,
                "parameters": {
                    "action_type": "general_conversation",
                    "target": command,
                    "content_type": "conversation"
                },
                "reasoning": "Matched conversational patterns in fallback classification"
            }
        
        # Check for deferred action intent
        if any(pattern in command_lower for pattern in deferred_patterns):
            return {
                "intent": "deferred_action",
                "confidence": 0.7,
                "parameters": {
                    "action_type": "generate_content",
                    "target": command,
                    "content_type": "code" if "code" in command_lower else "text"
                },
                "reasoning": "Matched content generation patterns in fallback classification"
            }
        
        # Check for question answering intent
        if any(pattern in command_lower for pattern in question_patterns):
            return {
                "intent": "question_answering",
                "confidence": 0.7,
                "parameters": {
                    "action_type": "general_question",
                    "target": command,
                    "content_type": "explanation"
                },
                "reasoning": "Matched question patterns in fallback classification"
            }
        
        # Default to GUI interaction
        return {
            "intent": "gui_interaction",
            "confidence": 0.6,
            "parameters": {
                "action_type": "unknown",
                "target": command,
                "content_type": "unknown"
            },
            "reasoning": "No specific patterns matched, defaulting to GUI interaction"
        }

    def _get_handler_for_intent(self, intent: str):
        """
        Get the appropriate handler for an intent.
        
        Args:
            intent: The recognized intent type
            
        Returns:
            Handler instance or None if not available
        """
        handler_map = {
            "gui_interaction": self.gui_handler,
            "conversational_chat": self.conversation_handler,
            "deferred_action": self.deferred_action_handler,
            "question_answering": self.question_answering_handler  # Use dedicated QuestionAnsweringHandler
        }
        
        handler = handler_map.get(intent)
        if handler is None:
            logger.warning(f"No handler available for intent '{intent}', falling back to GUI handler")
            return self.gui_handler
        
        return handler
    
    @measure_performance("parallel_perception_reasoning", include_system_metrics=True)
    def execute_parallel_perception_reasoning(self, command: str) -> Tuple[Optional[Dict], Optional[Dict]]:
        """
        Execute screen perception and command preprocessing in parallel.
        
        Args:
            command: User command to preprocess
            
        Returns:
            Tuple of (screen_context, preprocessed_command_info)
        """
        if not self.enable_parallel_processing or not self.parallel_perception_reasoning:
            # Fall back to sequential execution
            return None, None
        
        try:
            logger.debug("Starting parallel perception and reasoning preprocessing")
            
            # Define parallel tasks
            def capture_and_analyze_screen():
                """Capture and analyze screen in parallel."""
                try:
                    if not self.module_availability.get('vision', False):
                        return None
                    return self.vision_module.describe_screen(analysis_type="simple")
                except Exception as e:
                    logger.error(f"Parallel screen analysis failed: {e}")
                    # Return fallback context when vision fails
                    return self._create_fallback_screen_context(command)
            
            def preprocess_command():
                """Preprocess command in parallel."""
                try:
                    validation_result = self.validate_command(command)
                    return {
                        'validation': validation_result,
                        'normalized_command': validation_result.normalized_command,
                        'command_type': validation_result.command_type,
                        'confidence': validation_result.confidence
                    }
                except Exception as e:
                    logger.error(f"Parallel command preprocessing failed: {e}")
                    return None
            
            # Execute tasks in parallel
            tasks = [
                (capture_and_analyze_screen, (), {}),
                (preprocess_command, (), {})
            ]
            
            results = parallel_processor.execute_parallel_io(tasks)
            
            screen_context = results[0] if results and len(results) > 0 else None
            command_info = results[1] if results and len(results) > 1 else None
            
            # Record performance metrics
            if screen_context and command_info:
                metric = PerformanceMetrics(
                    operation="parallel_execution_success",
                    duration=0.0,  # Duration tracked by decorator
                    success=True,
                    parallel_execution=True,
                    metadata={
                        'screen_elements': len(screen_context.get('elements', [])) if screen_context else 0,
                        'command_type': command_info.get('command_type', 'unknown') if command_info else 'unknown'
                    }
                )
                performance_monitor.record_metric(metric)
            
            logger.debug(f"Parallel execution completed: screen_context={'available' if screen_context else 'failed'}, "
                        f"command_info={'available' if command_info else 'failed'}")
            
            return screen_context, command_info
            
        except Exception as e:
            logger.error(f"Parallel perception and reasoning failed: {e}")
            return None, None
    
    def _initialize_system_health(self) -> None:
        """Initialize system health monitoring."""
        try:
            self.system_health_status = {
                'overall_health': 'healthy',
                'last_health_check': time.time(),
                'module_health': {
                    'vision': 'healthy' if self.module_availability.get('vision', False) else 'unavailable',
                    'reasoning': 'healthy' if self.module_availability.get('reasoning', False) else 'unavailable',
                    'automation': 'healthy' if self.module_availability.get('automation', False) else 'unavailable',
                    'audio': 'healthy' if self.module_availability.get('audio', False) else 'unavailable',
                    'feedback': 'healthy' if self.module_availability.get('feedback', False) else 'unavailable',
                    'accessibility': 'healthy' if self.module_availability.get('accessibility', False) else 'unavailable'
                },
                'error_rates': {
                    'vision': 0.0,
                    'reasoning': 0.0,
                    'automation': 0.0,
                    'audio': 0.0,
                    'feedback': 0.0,
                    'accessibility': 0.0
                },
                'recovery_attempts': {
                    'vision': 0,
                    'reasoning': 0,
                    'automation': 0,
                    'audio': 0,
                    'feedback': 0,
                    'accessibility': 0
                }
            }
            
            logger.info("System health monitoring initialized")
            
        except Exception as e:
            error_info = global_error_handler.handle_error(
                error=e,
                module="orchestrator",
                function="_initialize_system_health",
                category=ErrorCategory.CONFIGURATION_ERROR,
                severity=ErrorSeverity.MEDIUM
            )
            logger.warning(f"System health monitoring initialization failed: {error_info.message}")
    
    def get_system_health(self) -> Dict[str, Any]:
        """
        Get current system health status.
        
        Returns:
            Dictionary containing system health information
        """
        try:
            # Update health check timestamp
            self.system_health_status['last_health_check'] = time.time()
            
            # Get error statistics from global error handler
            error_stats = global_error_handler.get_error_statistics()
            
            # Calculate overall health score
            available_modules = sum(1 for available in self.module_availability.values() if available)
            total_modules = len(self.module_availability)
            availability_score = available_modules / total_modules
            
            # Factor in error rates
            total_errors = error_stats.get('total_errors', 0)
            error_rate = error_stats.get('error_rate', 0)
            
            # Calculate health score (0-100)
            health_score = max(0, min(100, (availability_score * 70) + max(0, (30 - error_rate))))
            
            # Determine overall health status
            if health_score >= 80:
                overall_health = 'healthy'
            elif health_score >= 60:
                overall_health = 'degraded'
            elif health_score >= 40:
                overall_health = 'unhealthy'
            else:
                overall_health = 'critical'
            
            self.system_health_status['overall_health'] = overall_health
            self.system_health_status['health_score'] = health_score
            self.system_health_status['error_statistics'] = error_stats
            
            return self.system_health_status.copy()
            
        except Exception as e:
            error_info = global_error_handler.handle_error(
                error=e,
                module="orchestrator",
                function="get_system_health",
                category=ErrorCategory.PROCESSING_ERROR,
                severity=ErrorSeverity.LOW
            )
            logger.warning(f"Failed to get system health: {error_info.message}")
            
            return {
                'overall_health': 'unknown',
                'health_score': 0,
                'error': error_info.user_message,
                'last_health_check': time.time()
            }
    
    def attempt_system_recovery(self, failed_module: str = None) -> Dict[str, Any]:
        """
        Attempt to recover from system errors.
        
        Args:
            failed_module: Specific module to attempt recovery for (None for system-wide)
            
        Returns:
            Dictionary containing recovery results
        """
        recovery_results = {
            'recovery_attempted': True,
            'recovery_successful': False,
            'recovered_modules': [],
            'failed_modules': [],
            'errors': [],
            'timestamp': time.time()
        }
        
        try:
            logger.info(f"Attempting system recovery{f' for module: {failed_module}' if failed_module else ''}")
            
            modules_to_recover = [failed_module] if failed_module else list(self.module_availability.keys())
            
            for module_name in modules_to_recover:
                if not self.module_availability.get(module_name, False):
                    try:
                        logger.info(f"Attempting to recover {module_name} module")
                        
                        # Increment recovery attempt counter
                        self.system_health_status['recovery_attempts'][module_name] += 1
                        
                        # Attempt module recovery based on type
                        recovery_success = self._recover_module(module_name)
                        
                        if recovery_success:
                            self.module_availability[module_name] = True
                            self.system_health_status['module_health'][module_name] = 'healthy'
                            recovery_results['recovered_modules'].append(module_name)
                            logger.info(f"Successfully recovered {module_name} module")
                        else:
                            recovery_results['failed_modules'].append(module_name)
                            logger.warning(f"Failed to recover {module_name} module")
                            
                    except Exception as e:
                        error_info = global_error_handler.handle_error(
                            error=e,
                            module="orchestrator",
                            function="attempt_system_recovery",
                            category=ErrorCategory.PROCESSING_ERROR,
                            context={"module": module_name}
                        )
                        recovery_results['failed_modules'].append(module_name)
                        recovery_results['errors'].append(f"{module_name}: {error_info.user_message}")
                        logger.error(f"Recovery failed for {module_name}: {error_info.message}")
            
            # Determine overall recovery success
            recovery_results['recovery_successful'] = len(recovery_results['recovered_modules']) > 0
            
            # Update system health after recovery attempt
            self._update_system_health_after_recovery(recovery_results)
            
            logger.info(f"System recovery completed. Recovered: {len(recovery_results['recovered_modules'])}, "
                       f"Failed: {len(recovery_results['failed_modules'])}")
            
            return recovery_results
            
        except Exception as e:
            error_info = global_error_handler.handle_error(
                error=e,
                module="orchestrator",
                function="attempt_system_recovery",
                category=ErrorCategory.PROCESSING_ERROR,
                severity=ErrorSeverity.HIGH
            )
            
            recovery_results['recovery_successful'] = False
            recovery_results['errors'].append(f"Recovery system failure: {error_info.user_message}")
            logger.error(f"System recovery failed: {error_info.message}")
            
            return recovery_results
    
    def _recover_module(self, module_name: str) -> bool:
        """
        Attempt to recover a specific module.
        
        Args:
            module_name: Name of the module to recover
            
        Returns:
            True if recovery was successful, False otherwise
        """
        try:
            logger.debug(f"Attempting recovery for {module_name} module")
            
            if module_name == 'vision':
                # Attempt to reinitialize vision module
                self.vision_module = VisionModule()
                return True
                
            elif module_name == 'reasoning':
                # Attempt to reinitialize reasoning module
                self.reasoning_module = ReasoningModule()
                return True
                
            elif module_name == 'automation':
                # Attempt to reinitialize automation module
                self.automation_module = AutomationModule()
                return True
                
            elif module_name == 'audio':
                # Attempt to reinitialize audio module
                self.audio_module = AudioModule()
                return True
                
            elif module_name == 'feedback':
                # Attempt to reinitialize feedback module
                self.feedback_module = FeedbackModule(audio_module=self.audio_module)
                return True
                
            elif module_name == 'accessibility':
                # Attempt to reinitialize accessibility module
                self.accessibility_module = AccessibilityModule()
                # Re-enable fast path if accessibility module recovers
                self.fast_path_enabled = True
                return True
                
            else:
                logger.warning(f"Unknown module for recovery: {module_name}")
                return False
                
        except Exception as e:
            logger.warning(f"Module recovery failed for {module_name}: {e}")
            return False
    
    def _update_system_health_after_recovery(self, recovery_results: Dict[str, Any]) -> None:
        """
        Update system health status after recovery attempt.
        
        Args:
            recovery_results: Results from recovery attempt
        """
        try:
            # Update module health status
            for module in recovery_results['recovered_modules']:
                self.system_health_status['module_health'][module] = 'healthy'
            
            for module in recovery_results['failed_modules']:
                self.system_health_status['module_health'][module] = 'failed'
            
            # Recalculate overall health
            healthy_modules = sum(1 for status in self.system_health_status['module_health'].values() 
                                if status == 'healthy')
            total_modules = len(self.system_health_status['module_health'])
            
            if healthy_modules == total_modules:
                self.system_health_status['overall_health'] = 'healthy'
            elif healthy_modules >= total_modules * 0.8:
                self.system_health_status['overall_health'] = 'degraded'
            elif healthy_modules >= total_modules * 0.5:
                self.system_health_status['overall_health'] = 'unhealthy'
            else:
                self.system_health_status['overall_health'] = 'critical'
            
            self.system_health_status['last_recovery_attempt'] = time.time()
            
        except Exception as e:
            logger.warning(f"Failed to update system health after recovery: {e}")
    
    def handle_module_error(self, module_name: str, error: Exception, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Handle errors from specific modules with recovery attempts.
        
        Args:
            module_name: Name of the module that encountered the error
            error: The error that occurred
            context: Additional context about the error
            
        Returns:
            Dictionary containing error handling results
        """
        try:
            # Log the module error
            error_info = global_error_handler.handle_error(
                error=error,
                module=module_name,
                function="module_operation",
                context=context or {}
            )
            
            # Update module health status
            self.system_health_status['module_health'][module_name] = 'error'
            self.module_availability[module_name] = False
            
            # Determine if recovery should be attempted
            should_attempt_recovery = (
                self.error_recovery_enabled and
                error_info.recoverable and
                self.system_health_status['recovery_attempts'][module_name] < 3  # Max 3 recovery attempts
            )
            
            handling_result = {
                'error_handled': True,
                'error_info': {
                    'error_id': error_info.error_id,
                    'category': error_info.category.value,
                    'severity': error_info.severity.value,
                    'user_message': error_info.user_message
                },
                'recovery_attempted': False,
                'recovery_successful': False,
                'graceful_degradation': False
            }
            
            if should_attempt_recovery:
                logger.info(f"Attempting recovery for {module_name} after error: {error_info.message}")
                recovery_result = self.attempt_system_recovery(module_name)
                
                handling_result['recovery_attempted'] = True
                handling_result['recovery_successful'] = recovery_result['recovery_successful']
                
                if not recovery_result['recovery_successful'] and self.graceful_degradation_enabled:
                    # Attempt graceful degradation
                    degradation_result = self._attempt_graceful_degradation(module_name, error_info)
                    handling_result['graceful_degradation'] = degradation_result
            
            elif self.graceful_degradation_enabled:
                # Skip recovery, attempt graceful degradation
                degradation_result = self._attempt_graceful_degradation(module_name, error_info)
                handling_result['graceful_degradation'] = degradation_result
            
            return handling_result
            
        except Exception as e:
            logger.error(f"Failed to handle module error for {module_name}: {e}")
            return {
                'error_handled': False,
                'error': str(e),
                'recovery_attempted': False,
                'recovery_successful': False,
                'graceful_degradation': False
            }
    
    def _attempt_graceful_degradation(self, failed_module: str, error_info: ErrorInfo) -> bool:
        """
        Attempt graceful degradation when a module fails.
        
        Args:
            failed_module: Name of the failed module
            error_info: Information about the error
            
        Returns:
            True if graceful degradation was successful, False otherwise
        """
        try:
            logger.info(f"Attempting graceful degradation for {failed_module} module")
            
            if failed_module == 'vision':
                # Vision module failure - can't perform GUI automation
                logger.warning("Vision module unavailable. GUI automation commands will be disabled.")
                return True
                
            elif failed_module == 'reasoning':
                # Reasoning module failure - use fallback responses
                logger.warning("Reasoning module unavailable. Using fallback command processing.")
                return True
                
            elif failed_module == 'automation':
                # Automation module failure - can still answer questions
                logger.warning("Automation module unavailable. GUI actions will be disabled.")
                return True
                
            elif failed_module == 'audio':
                # Audio module failure - use text-based feedback only
                logger.warning("Audio module unavailable. Voice features will be disabled.")
                return True
                
            elif failed_module == 'feedback':
                # Feedback module failure - use basic logging for feedback
                logger.warning("Feedback module unavailable. Audio feedback will be disabled.")
                return True
                
            elif failed_module == 'accessibility':
                # Accessibility module failure - disable fast path, use vision fallback
                logger.warning("Accessibility module unavailable. Fast path GUI automation will be disabled.")
                self.fast_path_enabled = False
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Graceful degradation failed for {failed_module}: {e}")
            return False
    
    def _init_validation_patterns(self) -> None:
        """Initialize command validation patterns."""
        self.command_patterns = {
            'click': [
                r'click\s+(?:on\s+)?(?:the\s+)?(.+)',
                r'press\s+(?:the\s+)?(.+)',
                r'tap\s+(?:on\s+)?(?:the\s+)?(.+)'
            ],
            'type': [
                r'type\s+["\'](.+)["\']',  # Quoted text
                r'type\s+(.+)',  # Unquoted text (more flexible)
                r'enter\s+["\'](.+)["\']',
                r'enter\s+(.+)',  # Unquoted text
                r'input\s+["\'](.+)["\']',
                r'input\s+(.+)',  # Unquoted text
                r'write\s+["\'](.+)["\']',
                r'write\s+(.+)'  # Unquoted text
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
                r'explain\s+(.+)',
                r'what\'?s\s+on\s+(?:my\s+)?screen\??'
            ],
            'detailed_question': [
                r'tell\s+me\s+what\'?s\s+on\s+(?:my\s+)?screen\s+in\s+detail',
                r'describe\s+(?:my\s+)?screen\s+in\s+detail',
                r'give\s+me\s+a\s+detailed\s+(?:description|analysis)\s+of\s+(?:my\s+)?screen',
                r'analyze\s+(?:my\s+)?screen\s+(?:in\s+)?detail'
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
        """Initialize all required modules with comprehensive error handling."""
        logger.info("Initializing AURA modules...")
        
        # Track module initialization status
        module_init_status = {
            'vision': False,
            'reasoning': False,
            'automation': False,
            'audio': False,
            'feedback': False,
            'accessibility': False
        }
        
        initialization_errors = []
        
        # Initialize Vision Module
        try:
            logger.info("Initializing Vision Module...")
            self.vision_module = VisionModule()
            module_init_status['vision'] = True
            logger.info("Vision Module initialized successfully")
        except Exception as e:
            error_info = global_error_handler.handle_error(
                error=e,
                module="orchestrator",
                function="_initialize_modules",
                category=ErrorCategory.CONFIGURATION_ERROR,
                severity=ErrorSeverity.HIGH,
                context={"module": "vision"}
            )
            initialization_errors.append(f"Vision Module: {error_info.user_message}")
            logger.error(f"Vision Module initialization failed: {error_info.message}")
        
        # Initialize Reasoning Module
        try:
            logger.info("Initializing Reasoning Module...")
            self.reasoning_module = ReasoningModule()
            module_init_status['reasoning'] = True
            logger.info("Reasoning Module initialized successfully")
        except Exception as e:
            error_info = global_error_handler.handle_error(
                error=e,
                module="orchestrator",
                function="_initialize_modules",
                category=ErrorCategory.CONFIGURATION_ERROR,
                severity=ErrorSeverity.HIGH,
                context={"module": "reasoning"}
            )
            initialization_errors.append(f"Reasoning Module: {error_info.user_message}")
            logger.error(f"Reasoning Module initialization failed: {error_info.message}")
        
        # Initialize Automation Module
        try:
            logger.info("Initializing Automation Module...")
            self.automation_module = AutomationModule()
            module_init_status['automation'] = True
            logger.info("Automation Module initialized successfully")
        except Exception as e:
            error_info = global_error_handler.handle_error(
                error=e,
                module="orchestrator",
                function="_initialize_modules",
                category=ErrorCategory.HARDWARE_ERROR,
                severity=ErrorSeverity.HIGH,
                context={"module": "automation"}
            )
            initialization_errors.append(f"Automation Module: {error_info.user_message}")
            logger.error(f"Automation Module initialization failed: {error_info.message}")
        
        # Initialize Audio Module
        try:
            logger.info("Initializing Audio Module...")
            self.audio_module = AudioModule()
            module_init_status['audio'] = True
            logger.info("Audio Module initialized successfully")
        except Exception as e:
            error_info = global_error_handler.handle_error(
                error=e,
                module="orchestrator",
                function="_initialize_modules",
                category=ErrorCategory.HARDWARE_ERROR,
                severity=ErrorSeverity.MEDIUM,
                context={"module": "audio"}
            )
            initialization_errors.append(f"Audio Module: {error_info.user_message}")
            logger.warning(f"Audio Module initialization failed: {error_info.message}")
        
        # Initialize Feedback Module (depends on Audio Module)
        try:
            logger.info("Initializing Feedback Module...")
            self.feedback_module = FeedbackModule(audio_module=self.audio_module)
            module_init_status['feedback'] = True
            logger.info("Feedback Module initialized successfully")
        except Exception as e:
            error_info = global_error_handler.handle_error(
                error=e,
                module="orchestrator",
                function="_initialize_modules",
                category=ErrorCategory.HARDWARE_ERROR,
                severity=ErrorSeverity.MEDIUM,
                context={"module": "feedback"}
            )
            initialization_errors.append(f"Feedback Module: {error_info.user_message}")
            logger.warning(f"Feedback Module initialization failed: {error_info.message}")
        
        # Initialize Accessibility Module (for fast path GUI automation)
        try:
            logger.info("Initializing Accessibility Module...")
            self.accessibility_module = AccessibilityModule()
            module_init_status['accessibility'] = True
            logger.info("Accessibility Module initialized successfully")
        except Exception as e:
            error_info = global_error_handler.handle_error(
                error=e,
                module="orchestrator",
                function="_initialize_modules",
                category=ErrorCategory.CONFIGURATION_ERROR,
                severity=ErrorSeverity.MEDIUM,
                context={"module": "accessibility"}
            )
            initialization_errors.append(f"Accessibility Module: {error_info.user_message}")
            logger.warning(f"Accessibility Module initialization failed: {error_info.message}")
            # Disable fast path if accessibility module fails
            self.fast_path_enabled = False
        
        # Initialize content extraction modules for fast path
        try:
            logger.info("Initializing Browser Accessibility Handler...")
            self.browser_accessibility_handler = BrowserAccessibilityHandler()
            module_init_status['browser_accessibility'] = True
            logger.info("Browser Accessibility Handler initialized successfully")
        except Exception as e:
            error_info = global_error_handler.handle_error(
                error=e,
                module="orchestrator",
                function="_initialize_modules",
                category=ErrorCategory.CONFIGURATION_ERROR,
                severity=ErrorSeverity.LOW,
                context={"module": "browser_accessibility"}
            )
            initialization_errors.append(f"Browser Accessibility Handler: {error_info.user_message}")
            logger.warning(f"Browser Accessibility Handler initialization failed: {error_info.message}")
        
        try:
            logger.info("Initializing PDF Handler...")
            self.pdf_handler = PDFHandler()
            module_init_status['pdf_handler'] = True
            logger.info("PDF Handler initialized successfully")
        except Exception as e:
            error_info = global_error_handler.handle_error(
                error=e,
                module="orchestrator",
                function="_initialize_modules",
                category=ErrorCategory.CONFIGURATION_ERROR,
                severity=ErrorSeverity.LOW,
                context={"module": "pdf_handler"}
            )
            initialization_errors.append(f"PDF Handler: {error_info.user_message}")
            logger.warning(f"PDF Handler initialization failed: {error_info.message}")
        
        # Initialize debugging and diagnostic tools
        self._initialize_debugging_tools()
        
        # Store module availability for graceful degradation
        self.module_availability = module_init_status.copy()
        
        # Check if critical modules are available
        critical_modules = ['vision', 'reasoning', 'automation']
        critical_failures = [module for module in critical_modules if not module_init_status[module]]
        
        if critical_failures:
            error_msg = f"Critical modules failed to initialize: {', '.join(critical_failures)}"
            if initialization_errors:
                error_msg += f". Errors: {'; '.join(initialization_errors)}"
            
            error_info = global_error_handler.handle_error(
                error=Exception(error_msg),
                module="orchestrator",
                function="_initialize_modules",
                category=ErrorCategory.CONFIGURATION_ERROR,
                severity=ErrorSeverity.CRITICAL,
                context={"failed_modules": critical_failures, "all_errors": initialization_errors}
            )
            
            raise OrchestratorError(f"Critical module initialization failed: {error_info.user_message}")
        
        # Log warnings for non-critical module failures
        non_critical_failures = [module for module in ['audio', 'feedback', 'accessibility'] if not module_init_status[module]]
        if non_critical_failures:
            logger.warning(f"Non-critical modules failed to initialize: {', '.join(non_critical_failures)}. "
                          f"System will operate with reduced functionality.")
        
        # Log successful initialization
        successful_modules = [module for module, status in module_init_status.items() if status]
        logger.info(f"Successfully initialized modules: {', '.join(successful_modules)}")
        
        if initialization_errors:
            logger.warning(f"Module initialization completed with {len(initialization_errors)} errors")
        else:
            logger.info("All modules initialized successfully")
    
    def _initialize_debugging_tools(self) -> None:
        """Initialize debugging and diagnostic tools for enhanced troubleshooting."""
        try:
            logger.info("Initializing debugging and diagnostic tools...")
            
            # Initialize diagnostic tools
            diagnostic_config = {
                'auto_diagnostics': True,
                'performance_tracking': True,
                'comprehensive_reporting': True,
                'debug_level': 'DETAILED'
            }
            
            self.diagnostic_tools = AccessibilityHealthChecker(diagnostic_config)
            
            # Initialize error recovery manager
            from modules.error_recovery import RecoveryConfiguration
            recovery_config = RecoveryConfiguration(
                max_retries=self.max_retries,
                base_delay=self.retry_delay,
                max_delay=5.0,  # 5 seconds
                enable_alternative_strategies=True
            )
            
            self.error_recovery_manager = ErrorRecoveryManager(recovery_config)
            
            # Enable debug mode
            self.debug_mode_enabled = True
            
            logger.info("Debugging tools initialized successfully")
            
        except Exception as e:
            logger.warning(f"Failed to initialize debugging tools: {e}")
            # Continue without debugging tools - they are optional
            self.diagnostic_tools = None
            self.error_recovery_manager = None
            self.debug_mode_enabled = False
    
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
    
    @with_error_handling(
        category=ErrorCategory.PROCESSING_ERROR,
        severity=ErrorSeverity.MEDIUM,
        max_retries=1,
        retry_delay=2.0,
        user_message="I encountered an error while processing your command. Let me try again."
    )
    def execute_command(self, command: str) -> Dict[str, Any]:
        """
        Execute a user command using the perception-reasoning-action loop with comprehensive error handling.
        
        Args:
            command: Natural language command from user
            
        Returns:
            Dictionary containing execution results and metadata
            
        Raises:
            OrchestratorError: If command execution fails after retries
        """
        # Input validation
        if not command or not command.strip():
            error_info = global_error_handler.handle_error(
                error=ValueError("Command cannot be empty"),
                module="orchestrator",
                function="execute_command",
                category=ErrorCategory.VALIDATION_ERROR,
                severity=ErrorSeverity.LOW
            )
            raise ValueError(f"Invalid command: {error_info.user_message}")
        
        # Check system health before execution
        system_health = self.get_system_health()
        if system_health['overall_health'] == 'critical':
            error_info = global_error_handler.handle_error(
                error=Exception("System health is critical"),
                module="orchestrator",
                function="execute_command",
                category=ErrorCategory.RESOURCE_ERROR,
                severity=ErrorSeverity.HIGH,
                context={"system_health": system_health}
            )
            
            # Attempt system recovery before failing
            if self.error_recovery_enabled:
                logger.warning("System health critical, attempting recovery before command execution")
                recovery_result = self.attempt_system_recovery()
                
                if not recovery_result['recovery_successful']:
                    raise OrchestratorError(f"System unavailable: {error_info.user_message}")
            else:
                raise OrchestratorError(f"System unavailable: {error_info.user_message}")
        
        # Ensure only one command executes at a time with timeout-based lock acquisition
        lock_acquired = False
        try:
            # CONCURRENCY FIX: Use timeout-based lock acquisition to prevent indefinite blocking
            lock_acquired = self.execution_lock.acquire(timeout=30.0)
            if not lock_acquired:
                logger.warning("Failed to acquire execution lock within 30 seconds - system may be busy")
                raise OrchestratorError("System is currently busy processing another command. Please try again in a moment.")
            
            logger.debug("Execution lock acquired successfully")
            
            result = self._execute_command_internal(command.strip())
            
            # CONCURRENCY FIX: For deferred actions, release the lock early to allow subsequent commands
            if isinstance(result, dict) and result.get('status') == 'waiting_for_user_action':
                logger.info(f"Releasing execution lock early for deferred action: {result.get('execution_id')}")
                self.execution_lock.release()
                lock_acquired = False  # Mark as released to avoid double release
                return result
            else:
                # For non-deferred actions, keep the lock until we return
                logger.debug("Command execution completed, releasing lock")
                return result
                
        except Exception as e:
            # Handle execution errors with potential recovery
            error_info = global_error_handler.handle_error(
                error=e,
                module="orchestrator",
                function="execute_command",
                category=ErrorCategory.PROCESSING_ERROR,
                context={"command": command[:100]}  # Limit context size
            )
            
            # Attempt recovery if enabled and error is recoverable
            if self.error_recovery_enabled and error_info.recoverable:
                logger.warning(f"Command execution failed, attempting recovery: {error_info.message}")
                recovery_result = self.attempt_system_recovery()
                
                if recovery_result['recovery_successful']:
                    logger.info("Recovery successful, retrying command execution")
                    # Retry once after successful recovery
                    try:
                        return self._execute_command_internal(command.strip())
                    except Exception as retry_error:
                        logger.error(f"Command execution failed even after recovery: {retry_error}")
                        raise OrchestratorError(f"Command execution failed: {error_info.user_message}")
            
            # Re-raise with user-friendly message
            raise OrchestratorError(f"Command execution failed: {error_info.user_message}")
            
        finally:
            # CONCURRENCY FIX: Ensure lock is always released in finally block
            if lock_acquired and self.execution_lock.locked():
                try:
                    logger.debug("Releasing execution lock in finally block")
                    self.execution_lock.release()
                except Exception as lock_error:
                    logger.error(f"Failed to release execution lock in finally block: {lock_error}")


    
    def _handle_conversational_query(self, execution_id: str, query: str) -> Dict[str, Any]:
        """
        Handle conversational queries using natural language processing.
        
        Processes natural language conversations using the reasoning module with
        conversational prompts, extracts responses, and provides audio feedback.
        Enhanced with comprehensive error handling and recovery strategies.
        
        Args:
            execution_id (str): Unique execution identifier
            query (str): User's conversational query
            
        Returns:
            Dict[str, Any]: Execution result with conversational response
        """
        start_time = time.time()
        
        # Initialize execution context for conversational query
        execution_context = {
            "execution_id": execution_id,
            "command": query,
            "start_time": start_time,
            "status": CommandStatus.PROCESSING,
            "mode": "conversational_chat",
            "steps_completed": [],
            "errors": [],
            "warnings": [],
            "response": None,
            "audio_feedback_provided": False,
            "error_recovery_attempted": False,
            "fallback_strategy_used": None
        }
        
        try:
            logger.info(f"[{execution_id}] Processing conversational query: '{query}'")
            
            # Input validation
            if not query or not query.strip():
                raise ValueError("Empty conversational query provided")
            
            # Update progress
            self._update_progress(execution_id, CommandStatus.PROCESSING, ExecutionStep.REASONING, 30)
            
            # Check if reasoning module is available
            if not self.reasoning_module or not self.module_availability.get('reasoning', False):
                error_msg = "Reasoning module unavailable for conversational processing"
                execution_context["errors"].append(error_msg)
                execution_context["fallback_strategy_used"] = "reasoning_module_unavailable"
                logger.warning(f"[{execution_id}] {error_msg}")
                
                # Attempt module recovery if enabled
                if self.error_recovery_enabled:
                    logger.info(f"[{execution_id}] Attempting reasoning module recovery")
                    execution_context["error_recovery_attempted"] = True
                    
                    recovery_result = self.attempt_system_recovery("reasoning")
                    if recovery_result.get('recovery_successful', False):
                        logger.info(f"[{execution_id}] Reasoning module recovery successful, retrying")
                        # Retry the conversational processing
                        try:
                            response = self._process_conversational_query_with_reasoning(execution_id, query)
                            execution_context["response"] = response
                            execution_context["warnings"].append("Recovered from reasoning module failure")
                        except Exception as retry_error:
                            logger.error(f"[{execution_id}] Retry after recovery failed: {retry_error}")
                            execution_context["errors"].append(f"Recovery retry failed: {str(retry_error)}")
                            response = None
                    else:
                        logger.warning(f"[{execution_id}] Reasoning module recovery failed")
                        response = None
                else:
                    response = None
                
                # Use fallback response if no recovery or recovery failed
                if not execution_context.get("response"):
                    fallback_response = "I'm sorry, I'm having trouble processing conversations right now. Please try again later."
                    execution_context["response"] = fallback_response
                    execution_context["fallback_strategy_used"] = "static_fallback_response"
                
                # Provide enhanced conversational audio feedback if available
                if self.feedback_module and execution_context["response"]:
                    try:
                        self.feedback_module.provide_conversational_feedback(
                            message=execution_context["response"],
                            priority=FeedbackPriority.NORMAL,
                            include_thinking_sound=False  # Response already generated
                        )
                        execution_context["audio_feedback_provided"] = True
                    except Exception as audio_error:
                        logger.warning(f"[{execution_id}] Enhanced audio feedback failed, falling back to basic: {audio_error}")
                        try:
                            self.feedback_module.speak(execution_context["response"], FeedbackPriority.NORMAL)
                            execution_context["audio_feedback_provided"] = True
                        except Exception as fallback_error:
                            logger.warning(f"[{execution_id}] Fallback audio feedback also failed: {fallback_error}")
                            execution_context["warnings"].append(f"Audio feedback failed: {str(fallback_error)}")
                
                execution_context["status"] = CommandStatus.COMPLETED
                execution_context["warnings"].append("Used fallback response due to reasoning module unavailability")
                
            else:
                # Process conversational query using reasoning module with error handling
                try:
                    response = self._process_conversational_query_with_reasoning(execution_id, query)
                    execution_context["response"] = response
                    
                    # Validate response quality
                    if not response or len(response.strip()) < 3:
                        raise ValueError("Received empty or invalid response from reasoning module")
                    
                    # Provide enhanced conversational audio feedback
                    if self.feedback_module and response:
                        try:
                            logger.info(f"[{execution_id}] Providing enhanced conversational audio feedback")
                            self.feedback_module.provide_conversational_feedback(
                                message=response,
                                priority=FeedbackPriority.NORMAL,
                                include_thinking_sound=False  # Response already generated
                            )
                            execution_context["audio_feedback_provided"] = True
                        except Exception as audio_error:
                            logger.warning(f"[{execution_id}] Enhanced audio feedback failed, falling back to basic: {audio_error}")
                            try:
                                self.feedback_module.speak(response, FeedbackPriority.NORMAL)
                                execution_context["audio_feedback_provided"] = True
                            except Exception as fallback_error:
                                logger.warning(f"[{execution_id}] Fallback audio feedback also failed: {fallback_error}")
                                execution_context["warnings"].append(f"Audio feedback failed: {str(fallback_error)}")
                    
                    execution_context["status"] = CommandStatus.COMPLETED
                    logger.info(f"[{execution_id}] Conversational query processed successfully")
                    
                except Exception as processing_error:
                    logger.error(f"[{execution_id}] Conversational processing failed: {processing_error}")
                    execution_context["errors"].append(f"Processing error: {str(processing_error)}")
                    
                    # Attempt graceful degradation
                    execution_context["fallback_strategy_used"] = "processing_error_fallback"
                    fallback_response = "I encountered an issue while processing your question. Could you please try rephrasing it?"
                    execution_context["response"] = fallback_response
                    
                    # Provide error feedback
                    if self.feedback_module:
                        try:
                            self.feedback_module.speak(fallback_response, FeedbackPriority.NORMAL)
                            execution_context["audio_feedback_provided"] = True
                        except Exception as audio_error:
                            logger.warning(f"[{execution_id}] Error feedback audio failed: {audio_error}")
                    
                    execution_context["status"] = CommandStatus.COMPLETED
                    execution_context["warnings"].append("Used fallback response due to processing error")
            
            # Update conversation history for context (with error handling)
            try:
                with self.conversation_lock:
                    self._update_conversation_history(query, execution_context.get("response", ""))
            except Exception as history_error:
                logger.warning(f"[{execution_id}] Failed to update conversation history: {history_error}")
                execution_context["warnings"].append(f"Conversation history update failed: {str(history_error)}")
            
            # Final progress update
            self._update_progress(execution_id, CommandStatus.COMPLETED, None, 100)
            
            # Calculate execution time
            execution_context["end_time"] = time.time()
            execution_context["total_duration"] = execution_context["end_time"] - start_time
            execution_context["steps_completed"].append(ExecutionStep.REASONING)
            
            # Add to command history
            try:
                self.command_history.append(execution_context.copy())
            except Exception as history_error:
                logger.warning(f"[{execution_id}] Failed to add to command history: {history_error}")
            
            logger.info(f"[{execution_id}] Conversational query completed in {execution_context['total_duration']:.2f}s")
            
            return self._format_execution_result(execution_context)
            
        except Exception as e:
            # Handle conversational query failure with comprehensive error handling
            execution_context["status"] = CommandStatus.FAILED
            execution_context["end_time"] = time.time()
            execution_context["total_duration"] = execution_context["end_time"] - start_time
            execution_context["errors"].append(str(e))
            
            # Log error with context
            error_info = global_error_handler.handle_error(
                error=e,
                module="orchestrator",
                function="_handle_conversational_query",
                category=ErrorCategory.PROCESSING_ERROR,
                severity=ErrorSeverity.MEDIUM,
                context={
                    "execution_id": execution_id,
                    "query_length": len(query) if query else 0,
                    "reasoning_available": self.module_availability.get('reasoning', False),
                    "feedback_available": self.module_availability.get('feedback', False)
                }
            )
            
            logger.error(f"[{execution_id}] Conversational query failed: {error_info.message}")
            
            # Provide comprehensive error feedback
            if isinstance(e, ValueError) and "empty" in str(e).lower():
                error_response = "I didn't receive a valid question. Could you please ask me something?"
            elif "timeout" in str(e).lower():
                error_response = "I'm taking too long to respond. Please try asking a simpler question."
            elif "connection" in str(e).lower() or "api" in str(e).lower():
                error_response = "I'm having trouble connecting to my language processing service. Please try again in a moment."
            else:
                error_response = "I encountered an error while processing your question. Please try rephrasing or try again."
            
            execution_context["response"] = error_response
            execution_context["fallback_strategy_used"] = "comprehensive_error_fallback"
            
            # Provide enhanced audio error feedback
            if self.feedback_module:
                try:
                    self.feedback_module.provide_enhanced_error_feedback(
                        error_message=error_response,
                        error_context="conversational",
                        priority=FeedbackPriority.HIGH
                    )
                    execution_context["audio_feedback_provided"] = True
                    
                except Exception as audio_error:
                    logger.warning(f"[{execution_id}] Enhanced error feedback failed, falling back to basic: {audio_error}")
                    try:
                        self.feedback_module.play_with_message("failure", error_response, FeedbackPriority.HIGH)
                        execution_context["audio_feedback_provided"] = True
                    except Exception as fallback_error:
                        logger.warning(f"[{execution_id}] Basic error feedback also failed: {fallback_error}")
                        execution_context["warnings"].append(f"Error feedback audio failed: {str(fallback_error)}")
            
            # Update progress to failed
            self._update_progress(execution_id, CommandStatus.FAILED, None, 100, error=str(e))
            
            # Add to command history for debugging
            try:
                self.command_history.append(execution_context.copy())
            except Exception as history_error:
                logger.warning(f"[{execution_id}] Failed to add failed execution to command history: {history_error}")
            
            return self._format_execution_result(execution_context)
            
            return self._format_execution_result(execution_context)
    
    def _handle_deferred_action_request(self, execution_id: str, intent_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle deferred action requests that initiate multi-step workflows.
        
        This method implements the deferred action workflow with comprehensive error handling:
        1. Generate requested content using reasoning module
        2. Enter waiting state for user click
        3. Start global mouse listener with timeout management
        4. Provide audio instructions to user
        5. Handle timeouts and recovery scenarios
        
        Args:
            execution_id (str): Unique execution identifier
            intent_data (Dict[str, Any]): Intent recognition result with parameters
            
        Returns:
            Dict[str, Any]: Execution result indicating waiting state or error
        """
        start_time = time.time()
        
        try:
            logger.info(f"[{execution_id}] Starting deferred action workflow")
            
            # Input validation
            if not intent_data or not isinstance(intent_data, dict):
                raise ValueError("Invalid intent data provided for deferred action")
            
            # Check if system is already in deferred action mode
            if self.is_waiting_for_user_action:
                logger.warning(f"[{execution_id}] System already in deferred action mode, cancelling previous action")
                self._reset_deferred_action_state()
                
                # Provide audio feedback about cancellation
                if self.feedback_module:
                    try:
                        self.feedback_module.speak("Previous action cancelled. Starting new deferred action.", FeedbackPriority.NORMAL)
                    except Exception as audio_error:
                        logger.warning(f"[{execution_id}] Audio feedback failed: {audio_error}")
            
            # Extract parameters from intent data
            parameters = intent_data.get('parameters', {})
            content_request = parameters.get('target', '')
            content_type = parameters.get('content_type', 'code')
            original_command = intent_data.get('original_command', '')
            
            # Store content type for enhanced feedback
            self.current_deferred_content_type = content_type
            
            if not content_request:
                content_request = original_command
            
            # Validate content request
            if not content_request or not content_request.strip():
                raise ValueError("Empty content request for deferred action")
            
            logger.info(f"[{execution_id}] Content request: {content_request}, Type: {content_type}")
            
            # Step 1: Generate content using reasoning module with error handling
            self._update_progress(execution_id, CommandStatus.PROCESSING, ExecutionStep.REASONING, 30)
            
            try:
                # Check if reasoning module is available
                if not self.reasoning_module or not self.module_availability.get('reasoning', False):
                    # Attempt recovery if enabled
                    if self.error_recovery_enabled:
                        logger.info(f"[{execution_id}] Reasoning module unavailable, attempting recovery")
                        recovery_result = self.attempt_system_recovery("reasoning")
                        if not recovery_result.get('recovery_successful', False):
                            raise RuntimeError("Reasoning module unavailable and recovery failed")
                    else:
                        raise RuntimeError("Reasoning module unavailable for content generation")
                
                generated_content = self._generate_deferred_content(execution_id, content_request, content_type)
                
                # Validate generated content
                if not generated_content or not generated_content.strip():
                    raise ValueError("Content generation returned empty result")
                
                # Check content length for reasonableness
                if len(generated_content) > 10000:  # 10KB limit
                    logger.warning(f"[{execution_id}] Generated content is very large ({len(generated_content)} chars)")
                    # Truncate if too large
                    generated_content = generated_content[:10000] + "\n# ... (content truncated due to size)"
                
                logger.info(f"[{execution_id}] Content generated successfully ({len(generated_content)} characters)")
                
            except Exception as e:
                logger.error(f"[{execution_id}] Content generation failed: {e}")
                
                # Log error with context
                error_info = global_error_handler.handle_error(
                    error=e,
                    module="orchestrator",
                    function="_handle_deferred_action_request",
                    category=ErrorCategory.PROCESSING_ERROR,
                    severity=ErrorSeverity.MEDIUM,
                    context={
                        "execution_id": execution_id,
                        "content_request": content_request[:100],
                        "content_type": content_type
                    }
                )
                
                # Provide specific error feedback
                if "unavailable" in str(e).lower():
                    user_message = "Content generation service is unavailable. Please try again later."
                elif "timeout" in str(e).lower():
                    user_message = "Content generation timed out. Please try a simpler request."
                else:
                    user_message = "Failed to generate the requested content. Please try rephrasing your request."
                
                return self._create_error_result(
                    execution_id,
                    f"Content generation error: {error_info.message}",
                    user_message
                )
            
            # Step 2: Set up deferred action state with comprehensive error handling
            self._update_progress(execution_id, CommandStatus.PROCESSING, ExecutionStep.ACTION, 60)
            
            with self.deferred_action_lock:
                try:
                    # Store action state with enhanced tracking
                    current_time = time.time()
                    self.pending_action_payload = generated_content
                    self.deferred_action_type = 'type'  # Default action is typing
                    self.deferred_action_start_time = current_time
                    self.deferred_action_timeout_time = current_time + self.deferred_action_timeout_seconds
                    self.is_waiting_for_user_action = True
                    self.mouse_listener_active = False  # Will be set to True when listener starts
                    self.system_mode = 'waiting_for_user'
                    self.current_execution_id = execution_id
                    
                    logger.debug(f"[{execution_id}] Deferred action state configured (timeout: {self.deferred_action_timeout_seconds}s)")
                    
                    # Step 3: Start global mouse listener with error handling
                    try:
                        self._start_mouse_listener_for_deferred_action(execution_id)
                    except Exception as listener_error:
                        logger.error(f"[{execution_id}] Failed to start mouse listener: {listener_error}")
                        
                        # Clean up state and provide fallback
                        self._reset_deferred_action_state()
                        
                        # Check if pynput is available
                        from utils.mouse_listener import is_mouse_listener_available
                        if not is_mouse_listener_available():
                            return self._create_error_result(
                                execution_id,
                                "Mouse listener dependency not available",
                                "Mouse listener functionality is not available. Please install pynput: pip install pynput"
                            )
                        else:
                            return self._create_error_result(
                                execution_id,
                                f"Mouse listener failed to start: {listener_error}",
                                "Failed to start mouse listener. Please try again or check system permissions."
                            )
                    
                    # Step 4: Provide user instructions via audio feedback with error handling
                    try:
                        self._provide_deferred_action_instructions(execution_id, content_type)
                    except Exception as instruction_error:
                        logger.warning(f"[{execution_id}] Failed to provide audio instructions: {instruction_error}")
                        # Continue without audio instructions - not critical for functionality
                    
                    # Step 5: Start timeout monitoring
                    self._start_deferred_action_timeout_monitoring(execution_id)
                    
                    # Update progress to indicate waiting state
                    self._update_progress(execution_id, CommandStatus.PROCESSING, ExecutionStep.ACTION, 80)
                    
                    logger.info(f"[{execution_id}] Deferred action workflow initiated successfully")
                    
                    return {
                        'status': 'waiting_for_user_action',
                        'execution_id': execution_id,
                        'message': 'Content generated. Click where you want it placed.',
                        'content_preview': generated_content[:100] + '...' if len(generated_content) > 100 else generated_content,
                        'content_type': content_type,
                        'waiting_since': self.deferred_action_start_time,
                        'timeout_at': self.deferred_action_timeout_time,
                        'timeout_seconds': self.deferred_action_timeout_seconds,
                        'instructions': 'Click anywhere on the screen where you want the content to be typed.',
                        'success': True,
                        'duration': time.time() - start_time
                    }
                    
                except Exception as e:
                    logger.error(f"[{execution_id}] Failed to set up deferred action state: {e}")
                    
                    # Log error with context
                    error_info = global_error_handler.handle_error(
                        error=e,
                        module="orchestrator",
                        function="_handle_deferred_action_request",
                        category=ErrorCategory.PROCESSING_ERROR,
                        severity=ErrorSeverity.HIGH,
                        context={"execution_id": execution_id, "setup_phase": "state_configuration"}
                    )
                    
                    # Clean up on failure
                    self._reset_deferred_action_state()
                    
                    return self._create_error_result(
                        execution_id,
                        f"Deferred action setup failed: {error_info.message}",
                        "Failed to set up the deferred action. Please try again."
                    )
            
        except Exception as e:
            logger.error(f"[{execution_id}] Deferred action request failed: {e}")
            
            # Log comprehensive error information
            error_info = global_error_handler.handle_error(
                error=e,
                module="orchestrator",
                function="_handle_deferred_action_request",
                category=ErrorCategory.PROCESSING_ERROR,
                severity=ErrorSeverity.HIGH,
                context={
                    "execution_id": execution_id,
                    "duration": time.time() - start_time,
                    "system_mode": getattr(self, 'system_mode', 'unknown'),
                    "waiting_for_user": getattr(self, 'is_waiting_for_user_action', False)
                }
            )
            
            # Ensure state is clean on any failure
            self._reset_deferred_action_state()
            
            # Provide enhanced audio error feedback
            if self.feedback_module:
                try:
                    error_message = "The deferred action could not be started. Please try again."
                    self.feedback_module.provide_enhanced_error_feedback(
                        error_message=error_message,
                        error_context="deferred_action",
                        priority=FeedbackPriority.HIGH
                    )
                    
                except Exception as audio_error:
                    logger.warning(f"[{execution_id}] Enhanced error feedback failed, falling back to basic: {audio_error}")
                    try:
                        self.feedback_module.play_with_message("failure", error_message, FeedbackPriority.HIGH)
                    except Exception as fallback_error:
                        logger.warning(f"[{execution_id}] Basic error feedback also failed: {fallback_error}")
            
            # Provide specific error messages based on error type
            if isinstance(e, ValueError):
                user_message = "Invalid request for deferred action. Please check your command and try again."
            elif "timeout" in str(e).lower():
                user_message = "The deferred action setup timed out. Please try again."
            elif "permission" in str(e).lower():
                user_message = "Permission denied for deferred action. Please check system permissions."
            else:
                user_message = "The deferred action could not be completed. Please try again."
            
            return self._create_error_result(
                execution_id,
                f"Deferred action failed: {error_info.message}",
                user_message
            )
    
    def _process_conversational_query_with_reasoning(self, execution_id: str, query: str) -> str:
        """
        Process conversational query using the reasoning module with conversational prompts.
        
        Args:
            execution_id (str): Unique execution identifier
            query (str): User's conversational query
            
        Returns:
            str: Generated conversational response
            
        Raises:
            Exception: If reasoning module processing fails
        """
        try:
            # Import conversational prompt from config
            from config import CONVERSATIONAL_PROMPT
            
            # Prepare conversational prompt with user query
            conversational_prompt = CONVERSATIONAL_PROMPT.format(query=query)
            
            logger.debug(f"[{execution_id}] Sending conversational query to reasoning module")
            
            # Make API request using reasoning module's internal method
            api_response = self.reasoning_module._make_api_request(conversational_prompt)
            
            # Extract response text from API response
            response_text = self._extract_conversational_response(api_response)
            
            if not response_text or not response_text.strip():
                raise Exception("Empty response received from reasoning module")
            
            logger.info(f"[{execution_id}] Received conversational response: {response_text[:100]}...")
            
            return response_text.strip()
            
        except Exception as e:
            logger.error(f"[{execution_id}] Failed to process conversational query with reasoning module: {e}")
            raise Exception(f"Conversational processing failed: {str(e)}")
    
    def _extract_conversational_response(self, api_response: Dict[str, Any]) -> str:
        """
        Extract conversational response text from API response.
        
        Args:
            api_response (Dict[str, Any]): Raw API response from reasoning module
            
        Returns:
            str: Extracted response text
            
        Raises:
            Exception: If response extraction fails
        """
        try:
            # Handle different API response formats
            if 'message' in api_response and 'content' in api_response['message']:
                # Ollama format
                response_text = api_response['message']['content']
            elif 'choices' in api_response and len(api_response['choices']) > 0:
                # OpenAI format
                choice = api_response['choices'][0]
                if 'message' in choice and 'content' in choice['message']:
                    response_text = choice['message']['content']
                elif 'text' in choice:
                    response_text = choice['text']
                else:
                    raise Exception("Unexpected API response format in choices")
            elif 'response' in api_response:
                # Direct response format
                response_text = api_response['response']
            elif 'content' in api_response:
                # Simple content format
                response_text = api_response['content']
            else:
                raise Exception(f"Unrecognized API response format: {list(api_response.keys())}")
            
            if not isinstance(response_text, str):
                raise Exception(f"Response text is not a string: {type(response_text)}")
            
            return response_text
            
        except Exception as e:
            logger.error(f"Failed to extract conversational response: {e}")
            raise Exception(f"Response extraction failed: {str(e)}")
    
    def _update_conversation_history(self, user_query: str, assistant_response: str) -> None:
        """
        Update conversation history for context preservation.
        
        Args:
            user_query (str): User's input query
            assistant_response (str): Assistant's response
        """
        try:
            # Import conversation context size from config
            from config import CONVERSATION_CONTEXT_SIZE
            
            # Add new exchange to history
            exchange = (user_query, assistant_response)
            self.conversation_history.append(exchange)
            
            # Maintain context size limit
            if len(self.conversation_history) > CONVERSATION_CONTEXT_SIZE:
                self.conversation_history = self.conversation_history[-CONVERSATION_CONTEXT_SIZE:]
            
            logger.debug(f"Updated conversation history. Current size: {len(self.conversation_history)}")
            
        except Exception as e:
            logger.warning(f"Failed to update conversation history: {e}")
    
    def _generate_deferred_content(self, execution_id: str, content_request: str, content_type: str) -> Optional[str]:
        """
        Generate content for deferred actions using the reasoning module.
        
        Args:
            execution_id (str): Unique execution identifier
            content_request (str): User's content request
            content_type (str): Type of content to generate (code, text, etc.)
            
        Returns:
            Generated content string, or None if generation fails
        """
        try:
            logger.debug(f"[{execution_id}] Generating {content_type} content for: {content_request}")
            
            # Import config here to avoid circular imports
            from config import CODE_GENERATION_PROMPT, TEXT_GENERATION_PROMPT
            
            # Prepare context for content generation
            context = {
                'request_type': content_type,
                'execution_id': execution_id,
                'timestamp': time.time()
            }
            
            # Choose the appropriate prompt based on content type
            if content_type == 'code':
                prompt_template = CODE_GENERATION_PROMPT
            else:  # text, essay, article, etc.
                prompt_template = TEXT_GENERATION_PROMPT
            
            # Format the prompt with the user's request
            formatted_prompt = prompt_template.format(
                request=content_request,
                context=str(context)
            )
            
            # Use reasoning module to generate content
            if not self.module_availability.get('reasoning', False):
                logger.error(f"[{execution_id}] Reasoning module not available for content generation")
                return None
            
            # Generate content using reasoning module
            response = self.reasoning_module._make_api_request(formatted_prompt)
            
            # Debug logging to understand what we're getting
            logger.debug(f"[{execution_id}] Raw response type: {type(response)}")
            logger.debug(f"[{execution_id}] Raw response: {response}")
            
            if not response or not isinstance(response, dict):
                logger.warning(f"[{execution_id}] Empty or invalid response from reasoning module")
                return None
            
            # Extract the content from the response dictionary
            # Handle various API response formats
            if isinstance(response, dict) and 'choices' in response:
                # Handle OpenAI-style response format: {'choices': [{'message': {'content': 'text'}}]}
                choices = response.get('choices', [])
                if choices and isinstance(choices, list) and len(choices) > 0:
                    first_choice = choices[0]
                    if isinstance(first_choice, dict) and 'message' in first_choice:
                        message = first_choice.get('message', {})
                        if isinstance(message, dict) and 'content' in message:
                            generated_content = message.get('content', '').strip()
                        else:
                            generated_content = str(message).strip()
                    else:
                        generated_content = str(first_choice).strip()
                else:
                    generated_content = str(response).strip()
            elif isinstance(response, dict) and 'message' in response:
                # Handle direct message format: {'message': 'text'}
                generated_content = response.get('message', '').strip()
            elif isinstance(response, dict) and 'response' in response:
                # Handle direct response format: {'response': 'text'}
                generated_content = response.get('response', '').strip()
            elif isinstance(response, str):
                # Handle direct string response
                generated_content = response.strip()
            else:
                # Try to get the response as string from the dict
                generated_content = str(response).strip()
            
            logger.debug(f"[{execution_id}] Extracted content: {len(generated_content)} chars")
            logger.debug(f"[{execution_id}] Content preview: {generated_content[:200] if generated_content else 'Empty'}")
            
            # INDENTATION DEBUG: Check if extracted content has proper formatting
            if content_type == 'code' and generated_content:
                lines = generated_content.split('\n')
                indented_lines = [line for line in lines if line.startswith('    ')]
                logger.debug(f"[{execution_id}] INDENTATION CHECK - Total lines: {len(lines)}, Indented lines: {len(indented_lines)}")
                if len(lines) > 1:
                    logger.debug(f"[{execution_id}] INDENTATION SAMPLE - First 3 lines:")
                    for i, line in enumerate(lines[:3]):
                        spaces = len(line) - len(line.lstrip())
                        logger.debug(f"[{execution_id}]   Line {i+1}: {spaces} spaces | '{line}'")
                else:
                    logger.warning(f"[{execution_id}] INDENTATION WARNING - Content appears to be single line: {generated_content[:100]}...")
            
            # Clean up any unwanted formatting or metadata
            generated_content = self._clean_generated_content(generated_content, content_type)
            logger.debug(f"[{execution_id}] Content after cleaning: {len(generated_content)} chars")
            
            # CRITICAL FIX: Format single-line code to multi-line
            if content_type == 'code' and generated_content:
                lines = generated_content.split('\n')
                if len(lines) == 1 and len(generated_content) > 50:
                    logger.warning(f"[{execution_id}] SINGLE-LINE CODE DETECTED - Attempting to format")
                    formatted_content = self._format_single_line_code(generated_content)
                    if formatted_content != generated_content:
                        line_count = len(formatted_content.split('\n'))
                        logger.info(f"[{execution_id}] Successfully formatted single-line code to {line_count} lines")
                        generated_content = formatted_content
                    else:
                        logger.warning(f"[{execution_id}] Could not format single-line code - will type as-is")
            
            # INDENTATION DEBUG: Check if cleaning preserved formatting
            if content_type == 'code' and generated_content:
                lines = generated_content.split('\n')
                indented_lines = [line for line in lines if line.startswith('    ')]
                logger.debug(f"[{execution_id}] INDENTATION CHECK AFTER CLEANING - Total lines: {len(lines)}, Indented lines: {len(indented_lines)}")
                if len(lines) > 1:
                    logger.debug(f"[{execution_id}] INDENTATION SAMPLE AFTER CLEANING - First 3 lines:")
                    for i, line in enumerate(lines[:3]):
                        spaces = len(line) - len(line.lstrip())
                        logger.debug(f"[{execution_id}]   Line {i+1}: {spaces} spaces | '{line}'")
                else:
                    logger.warning(f"[{execution_id}] INDENTATION WARNING AFTER CLEANING - Content appears to be single line!")
            
            # Safety check for over-aggressive cleaning
            if not generated_content or len(generated_content.strip()) == 0:
                logger.warning(f"[{execution_id}] Generated content is empty after processing")
                # If cleaning made it empty, try to return the original content
                if isinstance(response, dict):
                    # Try OpenAI format first
                    if 'choices' in response:
                        choices = response.get('choices', [])
                        if choices and len(choices) > 0:
                            first_choice = choices[0]
                            if isinstance(first_choice, dict) and 'message' in first_choice:
                                message = first_choice.get('message', {})
                                if isinstance(message, dict) and 'content' in message:
                                    original_content = message.get('content', '').strip()
                                    if original_content:
                                        logger.info(f"[{execution_id}] Returning original OpenAI content due to over-aggressive cleaning")
                                        return original_content
                    # Try other formats
                    original_content = response.get('message', response.get('response', str(response)))
                    if original_content and original_content.strip():
                        logger.info(f"[{execution_id}] Returning original content due to over-aggressive cleaning")
                        return original_content.strip()
                elif isinstance(response, str) and response.strip():
                    logger.info(f"[{execution_id}] Returning original string content")
                    return response.strip()
                return None
            
            # Basic validation of generated content
            if len(generated_content) < 5:
                logger.warning(f"[{execution_id}] Generated content too short: {generated_content}")
                return None
            
            logger.info(f"[{execution_id}] Content generation successful ({len(generated_content)} chars)")
            return generated_content
            
        except Exception as e:
            logger.error(f"[{execution_id}] Content generation failed: {e}")
            return None
    
    def _format_single_line_code(self, code: str) -> str:
        """
        Format single-line code into properly indented multi-line code.
        
        Args:
            code (str): Single-line code string
            
        Returns:
            str: Formatted multi-line code
        """
        try:
            # Python-specific formatting
            if 'def ' in code and ':' in code:
                logger.debug("Formatting Python code")
                
                # Simple string-based approach for reliability
                formatted = code
                
                # Step 1: Handle function definition
                if 'def ' in formatted:
                    parts = formatted.split('def ', 1)
                    if len(parts) == 2:
                        func_part = parts[1]
                        colon_pos = func_part.find(':')
                        if colon_pos != -1:
                            func_def = 'def ' + func_part[:colon_pos+1]
                            rest = func_part[colon_pos+1:].strip()
                            formatted = func_def + '\n    ' + rest
                
                # Step 2: Handle common patterns
                formatted = formatted.replace(' result = []', '\n    result = []')
                formatted = formatted.replace(' for _ in range(', '\n    for _ in range(')
                formatted = formatted.replace(') result.append(', '):\n        result.append(')
                formatted = formatted.replace('append(a) a, b = ', 'append(a)\n        a, b = ')
                formatted = formatted.replace(' return result', '\n    return result')
                formatted = formatted.replace(" if __name__ == '__main__':", "\n\nif __name__ == '__main__':")
                formatted = formatted.replace(': n = ', ':\n    n = ')
                formatted = formatted.replace(' print(', '\n    print(')
                
                # Step 3: Clean up and fix indentation
                lines = []
                indent_level = 0
                for line in formatted.split('\n'):
                    line = line.strip()
                    if line:
                        # Determine proper indentation
                        if line.startswith('def ') or line.startswith('if __name__'):
                            lines.append(line)
                            indent_level = 1
                        elif line.endswith(':'):
                            lines.append('    ' * indent_level + line)
                            indent_level += 1
                        else:
                            lines.append('    ' * indent_level + line)
                
                formatted = '\n'.join(lines)
                
                # Basic validation - ensure it has multiple lines
                if len(formatted.split('\n')) > 1:
                    return formatted
                    
            # JavaScript-specific formatting
            elif 'function' in code and '{' in code:
                logger.debug("Formatting JavaScript code")
                
                formatted = code
                
                # Simple JavaScript formatting
                formatted = formatted.replace('{ return ', '{\n  return ')
                formatted = formatted.replace('; }', ';\n}')
                formatted = formatted.replace('} console.log', '}\n\nconsole.log')
                
                # Clean up and fix JavaScript indentation
                lines = []
                for line in formatted.split('\n'):
                    line = line.strip()
                    if line:
                        if line.startswith('function') or line.startswith('console.log') or line == '}':
                            lines.append(line)
                        else:
                            lines.append('  ' + line)
                
                formatted = '\n'.join(lines)
                
                if len(formatted.split('\n')) > 1:
                    return formatted
            
            # If no specific formatting applied, return original
            return code
            
        except Exception as e:
            logger.warning(f"Error formatting single-line code: {e}")
            return code
    
    def _clean_generated_content(self, content: str, content_type: str) -> str:
        """
        Clean generated content to remove unwanted formatting or metadata.
        
        This method delegates to the enhanced content cleaning logic in the 
        deferred action handler for consistency and improved functionality.
        
        Args:
            content: Raw generated content
            content_type: Type of content (code, text, etc.)
            
        Returns:
            Cleaned content ready for typing
        """
        try:
            # Use the enhanced content cleaning from the deferred action handler
            if hasattr(self, 'deferred_action_handler') and self.deferred_action_handler:
                return self.deferred_action_handler._clean_and_format_content(content, content_type)
            
            # Fallback to basic cleaning if handler not available
            logger.warning("Deferred action handler not available, using basic content cleaning")
            return self._basic_content_cleaning(content, content_type)
            
        except Exception as e:
            logger.warning(f"Error cleaning generated content: {e}")
            return content  # Return original content if cleaning fails
    
    def _basic_content_cleaning(self, content: str, content_type: str) -> str:
        """
        Basic content cleaning as fallback when handler is not available.
        
        Args:
            content: Raw generated content
            content_type: Type of content (code, text, etc.)
            
        Returns:
            Basic cleaned content
        """
        try:
            # Basic unwanted prefixes and suffixes
            unwanted_prefixes = [
                "Here is the code:", "Here's the code:", "```python", "```javascript", 
                "```", "Here is the text:", "Here's the text:"
            ]
            
            unwanted_suffixes = ["```", "**End of code**", "**End of text**"]
            
            # Clean the content
            cleaned_content = content.strip()
            
            # Remove unwanted prefixes
            for prefix in unwanted_prefixes:
                if cleaned_content.lower().startswith(prefix.lower()):
                    cleaned_content = cleaned_content[len(prefix):].strip()
                    break
            
            # Remove unwanted suffixes
            for suffix in unwanted_suffixes:
                if cleaned_content.lower().endswith(suffix.lower()):
                    cleaned_content = cleaned_content[:-len(suffix)].strip()
                    break
            
            # Basic formatting for code
            if content_type == 'code':
                cleaned_content = cleaned_content.replace('\t', '    ')
            
            return cleaned_content
            
        except Exception as e:
            logger.warning(f"Error in basic content cleaning: {e}")
            return content
    
    def _start_mouse_listener_for_deferred_action(self, execution_id: str) -> None:
        """
        Start the global mouse listener for deferred action completion with comprehensive error handling.
        
        Args:
            execution_id (str): Unique execution identifier
            
        Raises:
            RuntimeError: If mouse listener cannot be started
            ImportError: If required dependencies are not available
        """
        try:
            logger.debug(f"[{execution_id}] Starting mouse listener for deferred action")
            
            # Import mouse listener here to avoid circular imports
            try:
                from utils.mouse_listener import GlobalMouseListener, is_mouse_listener_available
            except ImportError as import_error:
                logger.error(f"[{execution_id}] Failed to import mouse listener: {import_error}")
                raise ImportError("Mouse listener module not available. Please check utils/mouse_listener.py")
            
            # Check if mouse listener functionality is available
            if not is_mouse_listener_available():
                logger.error(f"[{execution_id}] Mouse listener dependencies not available")
                raise RuntimeError(
                    "Mouse listener not available - pynput library required. "
                    "Install with: pip install pynput"
                )
            
            # Clean up any existing mouse listener
            if self.mouse_listener is not None:
                logger.warning(f"[{execution_id}] Cleaning up existing mouse listener")
                try:
                    self.mouse_listener.stop()
                except Exception as cleanup_error:
                    logger.warning(f"[{execution_id}] Error cleaning up existing listener: {cleanup_error}")
                finally:
                    self.mouse_listener = None
                    self.mouse_listener_active = False
            
            # Create callback for mouse clicks with error handling
            def on_deferred_action_trigger():
                try:
                    self._on_deferred_action_trigger(execution_id)
                except Exception as callback_error:
                    logger.error(f"[{execution_id}] Error in mouse click callback: {callback_error}")
                    # Ensure state is reset even if callback fails
                    try:
                        self._reset_deferred_action_state()
                    except Exception as reset_error:
                        logger.error(f"[{execution_id}] Failed to reset state after callback error: {reset_error}")
                    finally :
                        self._reset_deferred_action_state()
            
            # Create mouse listener with error handling
            try:
                self.mouse_listener = GlobalMouseListener(callback=on_deferred_action_trigger)
            except Exception as creation_error:
                logger.error(f"[{execution_id}] Failed to create mouse listener: {creation_error}")
                raise RuntimeError(f"Mouse listener creation failed: {str(creation_error)}")
            
            # Start mouse listener with timeout and error handling
            try:
                self.mouse_listener.start()
                
                # Give the listener a moment to start and verify it's active
                time.sleep(0.2)
                
                if not self.mouse_listener.is_active():
                    raise RuntimeError("Mouse listener failed to start properly")
                
                self.mouse_listener_active = True
                logger.info(f"[{execution_id}] Global mouse listener started successfully for deferred action")
                
            except Exception as start_error:
                logger.error(f"[{execution_id}] Failed to start mouse listener: {start_error}")
                
                # Clean up failed listener
                if self.mouse_listener:
                    try:
                        self.mouse_listener.stop()
                    except Exception as stop_error:
                        logger.warning(f"[{execution_id}] Error stopping failed listener: {stop_error}")
                    finally:
                        self.mouse_listener = None
                        self.mouse_listener_active = False
                
                # Provide specific error messages based on error type
                if "permission" in str(start_error).lower():
                    raise RuntimeError(
                        "Permission denied for mouse listener. Please grant accessibility permissions to the application."
                    )
                elif "already" in str(start_error).lower():
                    raise RuntimeError("Mouse listener is already running. Please try again.")
                else:
                    raise RuntimeError(f"Mouse listener startup failed: {str(start_error)}")
            
        except Exception as e:
            # Log comprehensive error information
            error_info = global_error_handler.handle_error(
                error=e,
                module="orchestrator",
                function="_start_mouse_listener_for_deferred_action",
                category=ErrorCategory.RESOURCE_ERROR,
                severity=ErrorSeverity.HIGH,
                context={
                    "execution_id": execution_id,
                    "mouse_listener_active": getattr(self, 'mouse_listener_active', False),
                    "existing_listener": self.mouse_listener is not None
                }
            )
            
            logger.error(f"[{execution_id}] Mouse listener startup failed: {error_info.message}")
            
            # Ensure cleanup state
            self.mouse_listener = None
            self.mouse_listener_active = False
            
            # Re-raise with enhanced error message
            raise RuntimeError(f"Failed to start mouse listener: {error_info.user_message}")
    
    def _provide_deferred_action_instructions(self, execution_id: str, content_type: str) -> None:
        """
        Provide audio instructions to the user for deferred action completion.
        
        Args:
            execution_id (str): Unique execution identifier
            content_type (str): Type of content that was generated
        """
        try:
            # Prepare instruction message based on content type
            if content_type == 'code':
                instruction_message = "Code generated successfully. Click where you want me to type it."
            elif content_type == 'text':
                instruction_message = "Text generated successfully. Click where you want me to type it."
            else:
                instruction_message = "Content generated successfully. Click where you want me to place it."
            
            # Use enhanced feedback module for audio instructions if available
            if self.module_availability.get('feedback', False):
                try:
                    self.feedback_module.provide_deferred_action_instructions(
                        content_type=content_type,
                        priority=FeedbackPriority.HIGH
                    )
                    logger.debug(f"[{execution_id}] Enhanced deferred action instructions provided")
                except Exception as e:
                    logger.warning(f"[{execution_id}] Enhanced instructions failed, falling back to basic: {e}")
                    # Fallback to basic instruction delivery
                    try:
                        self.feedback_module.speak(instruction_message, FeedbackPriority.HIGH)
                        logger.debug(f"[{execution_id}] Basic audio instructions provided via feedback module")
                    except Exception as fallback_error:
                        logger.warning(f"[{execution_id}] Basic feedback also failed: {fallback_error}")
            
            # Also use audio module directly as fallback
            elif self.module_availability.get('audio', False):
                try:
                    self.audio_module.text_to_speech(instruction_message)
                    logger.debug(f"[{execution_id}] Audio instructions provided via audio module")
                except Exception as e:
                    logger.warning(f"[{execution_id}] Failed to provide audio instructions: {e}")
            
            else:
                logger.warning(f"[{execution_id}] No audio modules available for instructions")
            
        except Exception as e:
            logger.error(f"[{execution_id}] Failed to provide deferred action instructions: {e}")
    
    def _on_deferred_action_trigger(self, execution_id: str) -> None:
        """
        Callback method triggered when user clicks during deferred action.
        
        This method executes the pending action at the click location and
        completes the deferred action workflow.
        
        Args:
            execution_id (str): Unique execution identifier
        """
        execution_lock_acquired = False
        try:
            logger.info(f"[{execution_id}] Deferred action triggered by user click")
            
            # CONCURRENCY FIX: Re-acquire execution lock before executing final action
            logger.debug(f"[{execution_id}] Attempting to re-acquire execution lock for deferred action completion")
            execution_lock_acquired = self.execution_lock.acquire(timeout=15.0)
            
            if not execution_lock_acquired:
                logger.error(f"[{execution_id}] Failed to acquire execution lock for deferred action completion")
                self._provide_deferred_action_completion_feedback(execution_id, False, "System busy - could not complete action")
                return
            
            logger.debug(f"[{execution_id}] Execution lock re-acquired successfully for deferred action")
            
            with self.deferred_action_lock:
                # STATE MANAGEMENT FIX: Check for duplicate triggers
                if self.deferred_action_executing:
                    logger.warning(f"[{execution_id}] Deferred action already executing, ignoring duplicate trigger")
                    return
                
                # Verify we're in the correct state
                if not self.is_waiting_for_user_action:
                    logger.warning(f"[{execution_id}] Deferred action trigger called but not waiting for user action")
                    return
                
                if not self.pending_action_payload:
                    logger.error(f"[{execution_id}] No pending action payload found")
                    return
                
                # STATE MANAGEMENT FIX: Set executing flag to prevent race conditions
                self.deferred_action_executing = True
                
                # Get click coordinates if available
                click_coordinates = None
                if self.mouse_listener:
                    click_coordinates = self.mouse_listener.get_last_click_coordinates()
                
                logger.info(f"[{execution_id}] Executing deferred action at coordinates: {click_coordinates}")
                
                # Execute the pending action
                try:
                    success = self._execute_pending_deferred_action(execution_id, click_coordinates)
                    
                    if success:
                        # Provide success feedback
                        self._provide_deferred_action_completion_feedback(execution_id, True)
                        logger.info(f"[{execution_id}] Deferred action completed successfully")
                    else:
                        # Provide failure feedback
                        self._provide_deferred_action_completion_feedback(execution_id, False)
                        logger.error(f"[{execution_id}] Deferred action execution failed")
                
                except Exception as e:
                    logger.error(f"[{execution_id}] Error executing pending deferred action: {e}")
                    self._provide_deferred_action_completion_feedback(execution_id, False)
            
        except Exception as e:
            logger.error(f"[{execution_id}] Error in deferred action trigger: {e}")
            self._provide_deferred_action_completion_feedback(execution_id, False)
            
        finally:
            # STATE MANAGEMENT FIX: Always reset state in finally block to guarantee cleanup
            self.deferred_action_executing = False
            self._reset_deferred_action_state()
            
            # CONCURRENCY FIX: Always release execution lock when deferred action completes
            if execution_lock_acquired and self.execution_lock.locked():
                try:
                    logger.debug(f"[{execution_id}] Releasing execution lock after deferred action completion")
                    self.execution_lock.release()
                except Exception as lock_error:
                    logger.error(f"[{execution_id}] Failed to release execution lock: {lock_error}")
    
    def _execute_pending_deferred_action(self, execution_id: str, click_coordinates: Optional[Tuple[int, int]]) -> bool:
        """
        Execute the pending deferred action with the generated content.
        
        Args:
            execution_id (str): Unique execution identifier
            click_coordinates (Optional[Tuple[int, int]]): Where the user clicked
            
        Returns:
            True if execution was successful, False otherwise
        """
        try:
            if not self.pending_action_payload:
                logger.error(f"[{execution_id}] No pending action payload to execute")
                return False
            
            action_type = self.deferred_action_type or 'type'
            content = self.pending_action_payload
            
            logger.info(f"[{execution_id}] Executing {action_type} action with {len(content)} characters")
            
            # If we have click coordinates, click there first to position cursor
            if click_coordinates and self.module_availability.get('automation', False):
                try:
                    x, y = click_coordinates
                    logger.debug(f"[{execution_id}] Clicking at coordinates ({x}, {y}) before typing")
                    
                    # Use automation module to click at the coordinates
                    click_action = {
                        "action": "click",
                        "coordinates": [int(x), int(y)]
                    }
                    
                    self.automation_module.execute_action(click_action)
                    logger.debug(f"[{execution_id}] Successfully clicked at coordinates ({x}, {y})")
                    
                    # Small delay to ensure click is processed
                    time.sleep(0.2)
                    
                except Exception as e:
                    logger.warning(f"[{execution_id}] Failed to click at coordinates: {e}")
            
            # Execute the main action (typically typing)
            if action_type == 'type' and self.module_availability.get('automation', False):
                try:
                    # Use automation module to type the content
                    type_action = {
                        "action": "type",
                        "text": content
                    }
                    
                    self.automation_module.execute_action(type_action)
                    logger.info(f"[{execution_id}] Successfully typed {len(content)} characters")
                    return True
                        
                except Exception as e:
                    logger.error(f"[{execution_id}] Error during type action: {e}")
                    return False
            
            else:
                logger.error(f"[{execution_id}] Unsupported action type '{action_type}' or automation module unavailable")
                return False
            
        except Exception as e:
            logger.error(f"[{execution_id}] Error executing pending deferred action: {e}")
            return False
    
    def _provide_deferred_action_completion_feedback(self, execution_id: str, success: bool, error_message: str = None) -> None:
        """
        Provide audio feedback when deferred action completes.
        
        Args:
            execution_id (str): Unique execution identifier
            success (bool): Whether the action completed successfully
            error_message (str, optional): Custom error message for failures
        """
        try:
            if success:
                message = "Content placed successfully."
                sound_type = "success"
            else:
                message = error_message or "Failed to place content. Please try again."
                sound_type = "failure"
            
            # Provide enhanced audio feedback
            if self.module_availability.get('feedback', False):
                try:
                    # Determine content type from current deferred action context
                    content_type = getattr(self, 'current_deferred_content_type', 'content')
                    
                    self.feedback_module.provide_deferred_action_completion_feedback(
                        success=success,
                        content_type=content_type,
                        priority=FeedbackPriority.HIGH
                    )
                    logger.debug(f"[{execution_id}] Enhanced completion feedback provided")
                except Exception as e:
                    logger.warning(f"[{execution_id}] Enhanced completion feedback failed, falling back to basic: {e}")
                    # Fallback to basic completion feedback
                    try:
                        self.feedback_module.play_with_message(sound_type, message, FeedbackPriority.HIGH)
                        logger.debug(f"[{execution_id}] Basic completion feedback provided via feedback module")
                    except Exception as fallback_error:
                        logger.warning(f"[{execution_id}] Basic completion feedback also failed: {fallback_error}")
            
            # Fallback to audio module
            elif self.module_availability.get('audio', False):
                try:
                    self.audio_module.text_to_speech(message)
                    logger.debug(f"[{execution_id}] Completion feedback provided via audio module")
                except Exception as e:
                    logger.warning(f"[{execution_id}] Failed to provide audio completion feedback: {e}")
            
        except Exception as e:
            logger.error(f"[{execution_id}] Error providing deferred action completion feedback: {e}")
    
    def _create_error_result(self, execution_id: str, error_message: str, user_message: str) -> Dict[str, Any]:
        """
        Create a standardized error result for deferred actions.
        
        Args:
            execution_id (str): Unique execution identifier
            error_message (str): Technical error message for logging
            user_message (str): User-friendly error message
            
        Returns:
            Dict containing error result information
        """
        return {
            'status': 'failed',
            'execution_id': execution_id,
            'error': error_message,
            'message': user_message,
            'success': False,
            'timestamp': time.time()
        }
    
    def _reset_deferred_action_state(self) -> None:
        """
        Reset all deferred action state variables and cleanup resources.
        
        This method provides comprehensive state cleanup including:
        - Mouse listener resource cleanup and validation
        - State variable reset with consistency checking
        - State transition logging and validation
        - Thread-safe cleanup operations
        
        This method should be called when:
        - A deferred action completes successfully
        - A deferred action is cancelled by a new command
        - An error occurs during deferred action processing
        - A timeout occurs while waiting for user action
        """
        with self.deferred_action_lock:
            try:
                logger.debug("Starting comprehensive deferred action state reset")
                
                # Record state transition for validation
                self._record_state_transition('deferred_action_reset', {
                    'was_waiting': self.is_waiting_for_user_action,
                    'had_payload': self.pending_action_payload is not None,
                    'had_listener': self.mouse_listener is not None,
                    'system_mode': self.system_mode
                })
                
                # Step 1: Stop and cleanup mouse listener with validation
                self._cleanup_mouse_listener()
                
                # Step 2: Reset all deferred action state variables
                self._reset_deferred_action_variables()
                
                # Step 3: Update system mode and execution state
                self._update_system_mode_after_reset()
                
                # Step 4: Validate state consistency after reset
                validation_result = self._validate_deferred_action_state_consistency()
                
                if validation_result['is_consistent']:
                    logger.debug("Deferred action state reset completed successfully")
                else:
                    logger.warning(f"State inconsistency detected after reset: {validation_result['issues']}")
                    # Attempt to fix inconsistencies
                    self._force_state_consistency()
                
                # Step 5: Update last validation time
                self.last_state_validation_time = time.time()
                
            except Exception as e:
                logger.error(f"Error during comprehensive deferred action state reset: {e}")
                # Force reset critical variables even if cleanup fails
                self._force_state_reset()
    
    def _cleanup_mouse_listener(self) -> None:
        """
        Cleanup mouse listener resources with proper validation and error handling.
        """
        try:
            if self.mouse_listener is not None:
                logger.debug("Stopping mouse listener")
                
                # Check if listener is actually active before stopping
                if hasattr(self.mouse_listener, 'is_active') and self.mouse_listener.is_active():
                    try:
                        self.mouse_listener.stop()
                        logger.debug("Mouse listener stopped successfully")
                    except Exception as e:
                        logger.warning(f"Error stopping active mouse listener: {e}")
                else:
                    logger.debug("Mouse listener was not active, skipping stop")
                
                # Always clear the reference
                self.mouse_listener = None
                self.mouse_listener_active = False
                
            else:
                logger.debug("No mouse listener to cleanup")
                
        except Exception as e:
            logger.error(f"Error during mouse listener cleanup: {e}")
            # Force cleanup
            self.mouse_listener = None
            self.mouse_listener_active = False
    
    def _reset_deferred_action_variables(self) -> None:
        """
        Reset all deferred action state variables to their default values.
        """
        try:
            logger.debug("Resetting deferred action state variables")
            
            # Reset primary state variables
            self.is_waiting_for_user_action = False
            self.deferred_action_executing = False  # STATE MANAGEMENT FIX: Reset executing flag
            self.pending_action_payload = None
            self.deferred_action_type = None
            self.deferred_action_start_time = None
            self.deferred_action_timeout_time = None
            self.current_deferred_content_type = None  # Reset content type for enhanced feedback
            
            # Reset tracking variables
            self.mouse_listener_active = False
            
            logger.debug("Deferred action variables reset completed")
            
        except Exception as e:
            logger.error(f"Error resetting deferred action variables: {e}")
            raise
    
    def _update_system_mode_after_reset(self) -> None:
        """
        Update system mode and execution state after deferred action reset.
        """
        try:
            # Update system mode back to ready if we were waiting for user
            if self.system_mode == 'waiting_for_user':
                self.system_mode = 'ready'
                logger.debug("System mode updated from 'waiting_for_user' to 'ready'")
            
            # Clear current execution ID if no other operations are running
            if not self._has_active_operations():
                self.current_execution_id = None
                logger.debug("Cleared current execution ID")
                
        except Exception as e:
            logger.error(f"Error updating system mode after reset: {e}")
    
    def _validate_deferred_action_state_consistency(self) -> Dict[str, Any]:
        """
        Validate the consistency of deferred action state after reset.
        
        Returns:
            Dictionary containing validation results and any issues found
        """
        try:
            issues = []
            
            # Check that all deferred action variables are properly reset
            if self.is_waiting_for_user_action:
                issues.append("is_waiting_for_user_action should be False after reset")
            
            if self.deferred_action_executing:
                issues.append("deferred_action_executing should be False after reset")
            
            if self.pending_action_payload is not None:
                issues.append("pending_action_payload should be None after reset")
            
            if self.deferred_action_type is not None:
                issues.append("deferred_action_type should be None after reset")
            
            if self.deferred_action_start_time is not None:
                issues.append("deferred_action_start_time should be None after reset")
            
            if self.deferred_action_timeout_time is not None:
                issues.append("deferred_action_timeout_time should be None after reset")
            
            if self.mouse_listener is not None:
                issues.append("mouse_listener should be None after reset")
            
            if self.mouse_listener_active:
                issues.append("mouse_listener_active should be False after reset")
            
            # Check system mode consistency
            if self.system_mode == 'waiting_for_user' and not self.is_waiting_for_user_action:
                issues.append("system_mode is 'waiting_for_user' but is_waiting_for_user_action is False")
            
            return {
                'is_consistent': len(issues) == 0,
                'issues': issues,
                'validation_time': time.time()
            }
            
        except Exception as e:
            logger.error(f"Error validating state consistency: {e}")
            return {
                'is_consistent': False,
                'issues': [f"Validation error: {str(e)}"],
                'validation_time': time.time()
            }
    
    def _force_state_consistency(self) -> None:
        """
        Force state consistency by resetting all variables to safe defaults.
        """
        try:
            logger.warning("Forcing state consistency due to detected inconsistencies")
            
            # Force reset all deferred action variables
            self.is_waiting_for_user_action = False
            self.deferred_action_executing = False  # STATE MANAGEMENT FIX: Reset executing flag
            self.pending_action_payload = None
            self.deferred_action_type = None
            self.deferred_action_start_time = None
            self.deferred_action_timeout_time = None
            self.mouse_listener = None
            self.mouse_listener_active = False
            
            # Force system mode to ready
            self.system_mode = 'ready'
            
            logger.warning("State consistency forced - all variables reset to safe defaults")
            
        except Exception as e:
            logger.error(f"Error forcing state consistency: {e}")
    
    def _force_state_reset(self) -> None:
        """
        Emergency state reset that forces all critical variables to safe values.
        Used when normal cleanup fails.
        """
        try:
            logger.error("Performing emergency state reset")
            
            # Force reset critical variables
            self.is_waiting_for_user_action = False
            self.deferred_action_executing = False  # STATE MANAGEMENT FIX: Reset executing flag
            self.mouse_listener = None
            self.mouse_listener_active = False
            self.system_mode = 'ready'
            
            # Clear other variables if possible
            try:
                self.pending_action_payload = None
                self.deferred_action_type = None
                self.deferred_action_start_time = None
                self.deferred_action_timeout_time = None
                self.current_execution_id = None
            except:
                pass  # Ignore errors during emergency reset
            
            logger.error("Emergency state reset completed")
            
        except Exception as e:
            logger.critical(f"Emergency state reset failed: {e}")
    
    def _record_state_transition(self, transition_type: str, context: Dict[str, Any]) -> None:
        """
        Record state transitions for debugging and validation purposes.
        
        Args:
            transition_type: Type of state transition
            context: Additional context about the transition
        """
        try:
            with self.state_validation_lock:
                transition_record = {
                    'timestamp': time.time(),
                    'transition_type': transition_type,
                    'context': context.copy(),
                    'system_mode': self.system_mode,
                    'execution_id': self.current_execution_id
                }
                
                self.state_transition_history.append(transition_record)
                
                # Limit history size
                if len(self.state_transition_history) > self.max_state_history_entries:
                    self.state_transition_history = self.state_transition_history[-self.max_state_history_entries:]
                
                logger.debug(f"Recorded state transition: {transition_type}")
                
        except Exception as e:
            logger.warning(f"Error recording state transition: {e}")
    
    def _has_active_operations(self) -> bool:
        """
        Check if there are any active operations running.
        
        Returns:
            True if there are active operations, False otherwise
        """
        try:
            # Check if we're currently processing a command
            if self.command_status in [CommandStatus.PROCESSING, CommandStatus.VALIDATING]:
                return True
            
            # Check if we're waiting for user action
            if self.is_waiting_for_user_action:
                return True
            
            # Check if system mode indicates active operation
            if self.system_mode in ['processing', 'waiting_for_user']:
                return True
            
            return False
            
        except Exception as e:
            logger.warning(f"Error checking active operations: {e}")
            return False
    
    def validate_system_state(self) -> Dict[str, Any]:
        """
        Validate the overall system state for consistency and detect potential issues.
        
        Returns:
            Dictionary containing validation results and recommendations
        """
        try:
            with self.state_validation_lock:
                logger.debug("Performing comprehensive system state validation")
                
                validation_result = {
                    'is_valid': True,
                    'issues': [],
                    'warnings': [],
                    'recommendations': [],
                    'validation_time': time.time(),
                    'state_summary': {}
                }
                
                # Validate deferred action state consistency (only when not actively waiting)
                if not self.is_waiting_for_user_action:
                    deferred_validation = self._validate_deferred_action_state_consistency()
                    if not deferred_validation['is_consistent']:
                        validation_result['is_valid'] = False
                        validation_result['issues'].extend(deferred_validation['issues'])
                
                # Validate system mode consistency
                mode_issues = self._validate_system_mode_consistency()
                if mode_issues:
                    validation_result['warnings'].extend(mode_issues)
                
                # Check for timeout conditions
                timeout_issues = self._check_timeout_conditions()
                if timeout_issues:
                    validation_result['issues'].extend(timeout_issues)
                    validation_result['is_valid'] = False
                
                # Validate mouse listener state
                listener_issues = self._validate_mouse_listener_state()
                if listener_issues:
                    validation_result['warnings'].extend(listener_issues)
                
                # Generate state summary
                validation_result['state_summary'] = self._generate_state_summary()
                
                # Generate recommendations based on issues
                if validation_result['issues'] or validation_result['warnings']:
                    validation_result['recommendations'] = self._generate_state_recommendations(
                        validation_result['issues'], validation_result['warnings']
                    )
                
                # Update last validation time
                self.last_state_validation_time = time.time()
                
                logger.debug(f"State validation completed: {'VALID' if validation_result['is_valid'] else 'INVALID'}")
                
                return validation_result
                
        except Exception as e:
            logger.error(f"Error during state validation: {e}")
            return {
                'is_valid': False,
                'issues': [f"Validation error: {str(e)}"],
                'warnings': [],
                'recommendations': ['Perform emergency state reset'],
                'validation_time': time.time(),
                'state_summary': {}
            }
    
    def _validate_system_mode_consistency(self) -> List[str]:
        """
        Validate that system mode is consistent with other state variables.
        
        Returns:
            List of consistency issues found
        """
        issues = []
        
        try:
            # Check mode vs waiting state consistency
            if self.system_mode == 'waiting_for_user' and not self.is_waiting_for_user_action:
                issues.append("System mode is 'waiting_for_user' but is_waiting_for_user_action is False")
            
            if self.is_waiting_for_user_action and self.system_mode != 'waiting_for_user':
                issues.append(f"is_waiting_for_user_action is True but system mode is '{self.system_mode}'")
            
            # Check processing state consistency
            if self.system_mode == 'processing' and self.command_status not in [CommandStatus.PROCESSING, CommandStatus.VALIDATING]:
                issues.append(f"System mode is 'processing' but command status is '{self.command_status.value}'")
            
            # Check ready state consistency
            if (self.system_mode == 'ready' and 
                (self.is_waiting_for_user_action or 
                 self.command_status in [CommandStatus.PROCESSING, CommandStatus.VALIDATING])):
                issues.append("System mode is 'ready' but there are active operations")
            
        except Exception as e:
            issues.append(f"Error validating system mode consistency: {str(e)}")
        
        return issues
    
    def _check_timeout_conditions(self) -> List[str]:
        """
        Check for timeout conditions in deferred actions.
        
        Returns:
            List of timeout issues found
        """
        issues = []
        
        try:
            current_time = time.time()
            
            # Check deferred action timeout
            if (self.is_waiting_for_user_action and 
                self.deferred_action_start_time is not None):
                
                elapsed_time = current_time - self.deferred_action_start_time
                
                if elapsed_time > self.deferred_action_timeout_seconds:
                    issues.append(f"Deferred action has timed out (elapsed: {elapsed_time:.1f}s, timeout: {self.deferred_action_timeout_seconds}s)")
                
                # Check if timeout time was set and exceeded
                if (self.deferred_action_timeout_time is not None and 
                    current_time > self.deferred_action_timeout_time):
                    issues.append("Deferred action timeout time has been exceeded")
            
            # Check for stale state validation
            if (self.last_state_validation_time is not None and 
                current_time - self.last_state_validation_time > self.state_validation_interval * 2):
                issues.append("State validation is overdue")
            
        except Exception as e:
            issues.append(f"Error checking timeout conditions: {str(e)}")
        
        return issues
    
    def _start_deferred_action_timeout_monitoring(self, execution_id: str) -> None:
        """
        Start timeout monitoring for deferred actions.
        
        Creates a background thread that monitors for timeout conditions
        and automatically handles timeout scenarios with proper cleanup.
        
        Args:
            execution_id (str): Current execution identifier
        """
        def timeout_monitor():
            """Background thread function for timeout monitoring."""
            try:
                logger.debug(f"[{execution_id}] Starting deferred action timeout monitoring")
                
                while self.is_waiting_for_user_action and self.deferred_action_timeout_time:
                    current_time = time.time()
                    
                    # Check if timeout has been reached
                    if current_time >= self.deferred_action_timeout_time:
                        logger.warning(f"[{execution_id}] Deferred action timeout reached")
                        self._handle_deferred_action_timeout(execution_id)
                        break
                    
                    # Check every 5 seconds
                    time.sleep(5.0)
                    
                logger.debug(f"[{execution_id}] Deferred action timeout monitoring ended")
                
            except Exception as e:
                logger.error(f"[{execution_id}] Error in timeout monitoring: {e}")
                # Ensure cleanup happens even if monitoring fails
                if self.is_waiting_for_user_action:
                    self._handle_deferred_action_timeout(execution_id)
        
        # Start timeout monitoring in a daemon thread
        timeout_thread = threading.Thread(
            target=timeout_monitor,
            daemon=True,
            name=f"DeferredActionTimeout-{execution_id}"
        )
        timeout_thread.start()
    
    def _handle_deferred_action_timeout(self, execution_id: str) -> None:
        """
        Handle timeout of deferred actions with proper cleanup and user feedback.
        
        Args:
            execution_id (str): Execution identifier of the timed-out action
        """
        try:
            logger.warning(f"[{execution_id}] Handling deferred action timeout")
            
            # Calculate how long the action was waiting
            elapsed_time = 0.0
            if self.deferred_action_start_time:
                elapsed_time = time.time() - self.deferred_action_start_time
            
            # Provide enhanced audio feedback about timeout
            if self.feedback_module:
                try:
                    # Use enhanced timeout feedback
                    self.feedback_module.provide_deferred_action_timeout_feedback(
                        elapsed_time=elapsed_time,
                        priority=FeedbackPriority.HIGH
                    )
                    logger.debug(f"[{execution_id}] Enhanced timeout feedback provided")
                    
                except Exception as audio_error:
                    logger.warning(f"[{execution_id}] Enhanced timeout feedback failed, falling back to basic: {audio_error}")
                    # Fallback to basic timeout feedback
                    try:
                        timeout_message = f"The deferred action has timed out after {elapsed_time:.0f} seconds. The action has been cancelled."
                        self.feedback_module.play_with_message("failure", timeout_message, FeedbackPriority.HIGH)
                    except Exception as fallback_error:
                        logger.warning(f"[{execution_id}] Basic timeout feedback also failed: {fallback_error}")
            
            # Log timeout event with context
            error_info = global_error_handler.handle_error(
                error=TimeoutError(f"Deferred action timed out after {elapsed_time:.1f} seconds"),
                module="orchestrator",
                function="_handle_deferred_action_timeout",
                category=ErrorCategory.TIMEOUT_ERROR,
                severity=ErrorSeverity.MEDIUM,
                context={
                    "execution_id": execution_id,
                    "elapsed_time": elapsed_time,
                    "timeout_threshold": self.deferred_action_timeout_seconds,
                    "pending_payload_size": len(self.pending_action_payload) if self.pending_action_payload else 0
                }
            )
            
            # Reset deferred action state with timeout-specific cleanup
            self._reset_deferred_action_state_with_timeout(execution_id, elapsed_time)
            
            logger.info(f"[{execution_id}] Deferred action timeout handled successfully")
            
        except Exception as e:
            logger.error(f"[{execution_id}] Error handling deferred action timeout: {e}")
            
            # Force state reset even if timeout handling fails
            try:
                self._reset_deferred_action_state()
            except Exception as reset_error:
                logger.error(f"[{execution_id}] Force state reset failed: {reset_error}")
    
    def _reset_deferred_action_state_with_timeout(self, execution_id: str, elapsed_time: float) -> None:
        """
        Reset deferred action state with timeout-specific handling.
        
        Args:
            execution_id (str): Execution identifier
            elapsed_time (float): How long the action was waiting before timeout
        """
        try:
            logger.info(f"[{execution_id}] Resetting deferred action state due to timeout (elapsed: {elapsed_time:.1f}s)")
            
            # Store timeout information before reset
            timeout_info = {
                "execution_id": execution_id,
                "elapsed_time": elapsed_time,
                "timeout_threshold": self.deferred_action_timeout_seconds,
                "payload_size": len(self.pending_action_payload) if self.pending_action_payload else 0,
                "timestamp": time.time()
            }
            
            # Perform standard state reset
            self._reset_deferred_action_state()
            
            # Add timeout event to command history
            try:
                timeout_event = {
                    "execution_id": execution_id,
                    "event_type": "deferred_action_timeout",
                    "status": CommandStatus.FAILED,
                    "mode": "deferred_action",
                    "timeout_info": timeout_info,
                    "timestamp": time.time()
                }
                self.command_history.append(timeout_event)
            except Exception as history_error:
                logger.warning(f"[{execution_id}] Failed to add timeout event to history: {history_error}")
            
            logger.info(f"[{execution_id}] Deferred action state reset completed for timeout")
            
        except Exception as e:
            logger.error(f"[{execution_id}] Error in timeout-specific state reset: {e}")
            # Fallback to force reset
            self._force_state_reset()
    
    def _validate_mouse_listener_state(self) -> List[str]:
        """
        Validate mouse listener state for consistency.
        
        Returns:
            List of mouse listener issues found
        """
        issues = []
        
        try:
            # Check listener state consistency
            if self.mouse_listener_active and self.mouse_listener is None:
                issues.append("mouse_listener_active is True but mouse_listener is None")
            
            if self.mouse_listener is not None and not self.mouse_listener_active:
                issues.append("mouse_listener exists but mouse_listener_active is False")
            
            # Check if listener should be active based on waiting state
            if self.is_waiting_for_user_action and self.mouse_listener is None:
                issues.append("Waiting for user action but no mouse listener is active")
            
            if not self.is_waiting_for_user_action and self.mouse_listener is not None:
                issues.append("Not waiting for user action but mouse listener is still active")
            
            # Check listener health if it exists
            if self.mouse_listener is not None:
                try:
                    if hasattr(self.mouse_listener, 'is_active'):
                        if not self.mouse_listener.is_active():
                            issues.append("Mouse listener exists but is not active")
                except Exception as e:
                    issues.append(f"Error checking mouse listener health: {str(e)}")
            
        except Exception as e:
            issues.append(f"Error validating mouse listener state: {str(e)}")
        
        return issues
    
    def _generate_state_summary(self) -> Dict[str, Any]:
        """
        Generate a summary of the current system state.
        
        Returns:
            Dictionary containing state summary information
        """
        try:
            return {
                'system_mode': self.system_mode,
                'command_status': self.command_status.value if self.command_status else None,
                'is_waiting_for_user_action': self.is_waiting_for_user_action,
                'has_pending_payload': self.pending_action_payload is not None,
                'deferred_action_type': self.deferred_action_type,
                'mouse_listener_active': self.mouse_listener_active,
                'current_execution_id': self.current_execution_id,
                'deferred_action_elapsed_time': (
                    time.time() - self.deferred_action_start_time 
                    if self.deferred_action_start_time else None
                ),
                'state_history_entries': len(self.state_transition_history),
                'last_validation_age': (
                    time.time() - self.last_state_validation_time 
                    if self.last_state_validation_time else None
                )
            }
        except Exception as e:
            logger.warning(f"Error generating state summary: {e}")
            return {'error': str(e)}
    
    def _generate_state_recommendations(self, issues: List[str], warnings: List[str]) -> List[str]:
        """
        Generate recommendations based on state validation issues.
        
        Args:
            issues: List of critical issues found
            warnings: List of warnings found
            
        Returns:
            List of recommended actions
        """
        recommendations = []
        
        try:
            # Recommendations for critical issues
            if any('timeout' in issue.lower() for issue in issues):
                recommendations.append("Reset deferred action state due to timeout")
            
            if any('mouse listener' in issue.lower() for issue in issues):
                recommendations.append("Cleanup and reset mouse listener")
            
            if any('consistency' in issue.lower() for issue in issues):
                recommendations.append("Force state consistency reset")
            
            if any('validation error' in issue.lower() for issue in issues):
                recommendations.append("Perform emergency state reset")
            
            # Recommendations for warnings
            if any('overdue' in warning.lower() for warning in warnings):
                recommendations.append("Increase state validation frequency")
            
            if any('mode' in warning.lower() for warning in warnings):
                recommendations.append("Verify system mode transitions")
            
            # General recommendations
            if issues and not recommendations:
                recommendations.append("Perform comprehensive state reset")
            
            if warnings and not issues:
                recommendations.append("Monitor state more closely")
            
        except Exception as e:
            logger.warning(f"Error generating recommendations: {e}")
            recommendations.append("Manual state inspection required")
        
        return recommendations
    
    def handle_deferred_action_timeout(self) -> Dict[str, Any]:
        """
        Handle timeout conditions for deferred actions.
        
        Returns:
            Dictionary containing timeout handling results
        """
        try:
            logger.warning("Handling deferred action timeout")
            
            timeout_result = {
                'timeout_handled': True,
                'was_waiting': self.is_waiting_for_user_action,
                'elapsed_time': None,
                'cleanup_successful': False,
                'timestamp': time.time()
            }
            
            # Calculate elapsed time if available
            if self.deferred_action_start_time:
                timeout_result['elapsed_time'] = time.time() - self.deferred_action_start_time
            
            # Provide timeout feedback to user
            try:
                if self.feedback_module and self.module_availability.get('feedback', False):
                    self.feedback_module.speak(
                        "Deferred action timed out. Returning to normal operation.",
                        priority=FeedbackPriority.HIGH
                    )
            except Exception as e:
                logger.warning(f"Error providing timeout feedback: {e}")
            
            # Reset deferred action state
            try:
                self._reset_deferred_action_state()
                timeout_result['cleanup_successful'] = True
                logger.info("Deferred action timeout handled successfully")
            except Exception as e:
                logger.error(f"Error during timeout cleanup: {e}")
                timeout_result['cleanup_successful'] = False
                # Force emergency reset
                self._force_state_reset()
            
            return timeout_result
            
        except Exception as e:
            logger.error(f"Error handling deferred action timeout: {e}")
            # Emergency cleanup
            self._force_state_reset()
            return {
                'timeout_handled': False,
                'error': str(e),
                'cleanup_successful': False,
                'timestamp': time.time()
            }
    
    def get_state_diagnostics(self) -> Dict[str, Any]:
        """
        Get comprehensive state diagnostics for debugging and monitoring.
        
        Returns:
            Dictionary containing detailed state information
        """
        try:
            with self.state_validation_lock:
                diagnostics = {
                    'timestamp': time.time(),
                    'state_summary': self._generate_state_summary(),
                    'validation_result': self.validate_system_state(),
                    'recent_transitions': self.state_transition_history[-10:] if self.state_transition_history else [],
                    'configuration': {
                        'deferred_action_timeout_seconds': self.deferred_action_timeout_seconds,
                        'state_validation_interval': self.state_validation_interval,
                        'max_state_history_entries': self.max_state_history_entries
                    },
                    'thread_info': {
                        'deferred_action_lock_acquired': not self.deferred_action_lock.acquire(blocking=False),
                        'state_validation_lock_acquired': not self.state_validation_lock.acquire(blocking=False)
                    }
                }
                
                # Release locks if we acquired them for testing
                try:
                    self.deferred_action_lock.release()
                except:
                    pass
                try:
                    self.state_validation_lock.release()
                except:
                    pass
                
                return diagnostics
                
        except Exception as e:
            logger.error(f"Error getting state diagnostics: {e}")
            return {
                'timestamp': time.time(),
                'error': str(e),
                'emergency_state': {
                    'is_waiting_for_user_action': getattr(self, 'is_waiting_for_user_action', None),
                    'system_mode': getattr(self, 'system_mode', None),
                    'mouse_listener': getattr(self, 'mouse_listener', None) is not None
                }
            }
    
    def _start_periodic_state_validation(self) -> None:
        """
        Start periodic state validation in a background thread.
        """
        try:
            def validation_worker():
                """Background worker for periodic state validation."""
                while True:
                    try:
                        time.sleep(self.state_validation_interval)
                        
                        # Only validate if we have active operations
                        if self._has_active_operations():
                            validation_result = self.validate_system_state()
                            
                            # Handle critical issues
                            if not validation_result['is_valid']:
                                logger.warning(f"State validation failed: {validation_result['issues']}")
                                
                                # Check for timeout conditions and handle them (only for actual timeouts, not state validation issues)
                                actual_timeout_issues = [issue for issue in validation_result['issues'] 
                                                       if 'timed out' in issue.lower() or 'timeout time has been exceeded' in issue.lower()]
                                if actual_timeout_issues:
                                    logger.warning(f"Handling actual timeout conditions: {actual_timeout_issues}")
                                    self.handle_deferred_action_timeout()
                                
                                # Handle other critical issues
                                elif any('consistency' in issue.lower() for issue in validation_result['issues']):
                                    logger.warning("Forcing state consistency due to validation failure")
                                    self._force_state_consistency()
                            
                            # Log warnings
                            if validation_result['warnings']:
                                logger.debug(f"State validation warnings: {validation_result['warnings']}")
                    
                    except Exception as e:
                        logger.error(f"Error in periodic state validation: {e}")
                        # Continue running despite errors
                        continue
            
            # Start validation thread as daemon
            validation_thread = threading.Thread(
                target=validation_worker,
                daemon=True,
                name="StateValidationWorker"
            )
            validation_thread.start()
            
            logger.debug("Periodic state validation started")
            
        except Exception as e:
            logger.warning(f"Failed to start periodic state validation: {e}")
    
    def cleanup_orchestrator_resources(self) -> None:
        """
        Cleanup all orchestrator resources when shutting down.
        """
        try:
            logger.info("Cleaning up orchestrator resources")
            
            # Reset deferred action state
            self._reset_deferred_action_state()
            
            # Cleanup thread pool
            if hasattr(self, 'thread_pool') and self.thread_pool:
                self.thread_pool.shutdown(wait=True)
            
            # Clear state history
            with self.state_validation_lock:
                self.state_transition_history.clear()
            
            logger.info("Orchestrator resources cleaned up successfully")
            
        except Exception as e:
            logger.error(f"Error cleaning up orchestrator resources: {e}")

    def _handle_gui_interaction(self, execution_id: str, command: str) -> Dict[str, Any]:
        """
        Handle GUI interaction commands using the preserved legacy execution logic.
        Enhanced with comprehensive error handling and recovery strategies.
        
        Args:
            execution_id (str): Unique execution identifier
            command (str): GUI command to execute
            
        Returns:
            Dict[str, Any]: Execution result from GUI command processing
        """
        start_time = time.time()
        
        try:
            logger.info(f"[{execution_id}] Processing GUI interaction command: '{command}'")
            
            # Input validation
            if not command or not command.strip():
                raise ValueError("Empty GUI command provided")
            
            # Check system health before GUI interaction
            system_health = self.get_system_health()
            if system_health['overall_health'] == 'critical':
                logger.warning(f"[{execution_id}] System health is critical, attempting recovery")
                
                if self.error_recovery_enabled:
                    recovery_result = self.attempt_system_recovery()
                    if not recovery_result.get('recovery_successful', False):
                        raise RuntimeError("System health is critical and recovery failed")
                else:
                    raise RuntimeError("System health is critical")
            
            # Create execution context for legacy processing
            execution_context = {
                "execution_id": execution_id,
                "command": command,
                "start_time": start_time,
                "status": CommandStatus.PROCESSING,
                "steps_completed": [],
                "errors": [],
                "warnings": [],
                "validation_result": None,
                "screen_context": None,
                "action_plan": None,
                "execution_results": None,
                "error_recovery_attempted": False,
                "fallback_strategy_used": None
            }
            
            # Check for required modules
            required_modules = ['vision', 'reasoning', 'automation']
            unavailable_modules = []
            
            for module in required_modules:
                if not self.module_availability.get(module, False):
                    unavailable_modules.append(module)
            
            # Attempt recovery for unavailable modules if enabled
            if unavailable_modules and self.error_recovery_enabled:
                logger.info(f"[{execution_id}] Attempting recovery for unavailable modules: {unavailable_modules}")
                execution_context["error_recovery_attempted"] = True
                
                for module in unavailable_modules:
                    recovery_result = self.attempt_system_recovery(module)
                    if recovery_result.get('recovery_successful', False):
                        execution_context["warnings"].append(f"Recovered {module} module")
                        unavailable_modules.remove(module)
            
            # Check if critical modules are still unavailable
            if unavailable_modules:
                critical_modules = [m for m in unavailable_modules if m in ['vision', 'automation']]
                if critical_modules:
                    execution_context["fallback_strategy_used"] = "critical_modules_unavailable"
                    execution_context["warnings"].append(f"Critical modules unavailable: {critical_modules}")
                    
                    # Provide user feedback about limitations
                    if self.feedback_module:
                        try:
                            limitation_message = f"Some system components are unavailable. GUI automation may be limited."
                            self.feedback_module.speak(limitation_message, FeedbackPriority.NORMAL)
                        except Exception as audio_error:
                            logger.warning(f"[{execution_id}] Audio feedback failed: {audio_error}")
            
            # Use the legacy execution logic for GUI commands with error handling
            try:
                result = self._legacy_execute_command_internal(command, execution_context)
                
                # Validate result
                if not result or not isinstance(result, dict):
                    raise ValueError("Invalid result from legacy execution")
                
                # Add error handling metadata to result
                result.update({
                    "error_recovery_attempted": execution_context.get("error_recovery_attempted", False),
                    "fallback_strategy_used": execution_context.get("fallback_strategy_used"),
                    "system_health": system_health.get('overall_health', 'unknown'),
                    "total_duration": time.time() - start_time
                })
                
                logger.info(f"[{execution_id}] GUI interaction completed successfully in {result.get('total_duration', 0):.2f}s")
                return result
                
            except Exception as execution_error:
                logger.error(f"[{execution_id}] Legacy execution failed: {execution_error}")
                execution_context["errors"].append(f"Execution error: {str(execution_error)}")
                
                # Attempt graceful degradation
                execution_context["fallback_strategy_used"] = "execution_error_fallback"
                
                # Provide user feedback about failure
                if self.feedback_module:
                    try:
                        if "vision" in str(execution_error).lower():
                            error_message = "I'm having trouble seeing the screen. Please try again or check if the application is visible."
                        elif "automation" in str(execution_error).lower():
                            error_message = "I'm having trouble controlling the interface. Please try again or check system permissions."
                        elif "timeout" in str(execution_error).lower():
                            error_message = "The command is taking too long to complete. Please try a simpler action."
                        else:
                            error_message = "I encountered an error while trying to perform that action. Please try again."
                        
                        self.feedback_module.speak(error_message, FeedbackPriority.HIGH)
                        
                        # Play failure sound
                        from config import SOUNDS
                        if "failure" in SOUNDS:
                            try:
                                self.feedback_module.play_sound(SOUNDS["failure"])
                            except Exception as sound_error:
                                logger.debug(f"[{execution_id}] Failed to play failure sound: {sound_error}")
                                
                    except Exception as audio_error:
                        logger.warning(f"[{execution_id}] Error feedback audio failed: {audio_error}")
                
                # Return error result
                return {
                    "status": "failed",
                    "execution_id": execution_id,
                    "command": command,
                    "error": str(execution_error),
                    "user_message": "The GUI command could not be completed. Please try again.",
                    "errors": execution_context["errors"],
                    "warnings": execution_context["warnings"],
                    "error_recovery_attempted": execution_context.get("error_recovery_attempted", False),
                    "fallback_strategy_used": execution_context.get("fallback_strategy_used"),
                    "total_duration": time.time() - start_time,
                    "success": False
                }
            
        except Exception as e:
            # Handle GUI interaction failure with comprehensive error handling
            error_info = global_error_handler.handle_error(
                error=e,
                module="orchestrator",
                function="_handle_gui_interaction",
                category=ErrorCategory.PROCESSING_ERROR,
                severity=ErrorSeverity.HIGH,
                context={
                    "execution_id": execution_id,
                    "command": command[:100] if command else "",
                    "duration": time.time() - start_time
                }
            )
            
            logger.error(f"[{execution_id}] GUI interaction handler failed: {error_info.message}")
            
            # Provide comprehensive error feedback
            if self.feedback_module:
                try:
                    if isinstance(e, ValueError) and "empty" in str(e).lower():
                        error_response = "I didn't receive a valid command. Please tell me what you'd like me to do."
                    elif "critical" in str(e).lower():
                        error_response = "System components are unavailable. Please try again later."
                    elif "permission" in str(e).lower():
                        error_response = "I don't have the necessary permissions. Please check system settings."
                    else:
                        error_response = "I encountered an error while processing your command. Please try again."
                    
                    self.feedback_module.speak(error_response, FeedbackPriority.HIGH)
                    
                    # Play failure sound
                    from config import SOUNDS
                    if "failure" in SOUNDS:
                        try:
                            self.feedback_module.play_sound(SOUNDS["failure"])
                        except Exception as sound_error:
                            logger.debug(f"[{execution_id}] Failed to play failure sound: {sound_error}")
                            
                except Exception as audio_error:
                    logger.warning(f"[{execution_id}] Error feedback audio failed: {audio_error}")
            
            # Return comprehensive error result
            return {
                "status": "failed",
                "execution_id": execution_id,
                "command": command,
                "error": error_info.message,
                "user_message": error_info.user_message,
                "error_category": error_info.category.value,
                "error_severity": error_info.severity.value,
                "total_duration": time.time() - start_time,
                "success": False,
                "recoverable": error_info.recoverable
            }
    
    def _execute_command_internal(self, command: str) -> Dict[str, Any]:
        """
        Internal command execution with intent-based routing and comprehensive error handling.
        
        Acts as an intelligent router that:
        1. Recognizes user intent using LLM-based classification
        2. Checks for deferred action interruptions
        3. Routes commands to appropriate handlers based on intent
        4. Preserves existing GUI interaction functionality
        """
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
            
            # Step 0: Check for deferred action interruption
            # CONCURRENCY FIX: Use timeout to prevent hanging on deferred action lock
            try:
                lock_acquired = self.deferred_action_lock.acquire(timeout=5.0)
                if lock_acquired:
                    try:
                        if self.is_waiting_for_user_action:
                            logger.info(f"[{execution_id}] Interrupting deferred action due to new command")
                            self._reset_deferred_action_state()
                            # Continue processing the new command
                    finally:
                        self.deferred_action_lock.release()
                else:
                    logger.warning(f"[{execution_id}] Could not acquire deferred action lock within timeout - proceeding anyway")
                    # Continue with command execution even if we couldn't check deferred action state
            except Exception as lock_error:
                logger.error(f"[{execution_id}] Error with deferred action lock: {lock_error}")
                # Continue with command execution
            
            # Step 1: Intent Recognition and Routing
            logger.info(f"[{execution_id}] Step 1: Intent recognition and routing")
            self._update_progress(execution_id, CommandStatus.VALIDATING, ExecutionStep.VALIDATION, 10)
            
            intent_result = self._recognize_intent(command)
            execution_context["intent_result"] = intent_result
            
            intent_type = intent_result.get('intent', 'gui_interaction')
            confidence = intent_result.get('confidence', 0.0)
            
            logger.info(f"[{execution_id}] Intent recognized: {intent_type} (confidence: {confidence:.2f})")
            
            # Route to appropriate handler based on intent type
            return self._route_command_by_intent(execution_id, command, intent_result, execution_context)
            
        except Exception as e:
            # Handle execution failure
            execution_context["status"] = CommandStatus.FAILED
            execution_context["end_time"] = time.time()
            execution_context["total_duration"] = execution_context["end_time"] - start_time
            execution_context["errors"].append(str(e))
            
            # Update progress with failure
            self._update_progress(execution_id, CommandStatus.FAILED, error=str(e))
            
            # Provide failure feedback
            if self.feedback_module:
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
    
    def _route_command_by_intent(self, execution_id: str, command: str, intent_result: Dict[str, Any], execution_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route command to appropriate handler based on recognized intent.
        
        Args:
            execution_id: Unique execution identifier
            command: Original user command
            intent_result: Result from intent recognition
            execution_context: Current execution context
            
        Returns:
            Execution result from the appropriate handler
        """
        intent_type = intent_result.get('intent', 'gui_interaction')
        
        try:
            # Get the appropriate handler for this intent
            handler = self._get_handler_for_intent(intent_type)
            
            if handler is not None:
                logger.info(f"[{execution_id}] Routing to {handler.__class__.__name__} for intent '{intent_type}'")
                
                # Prepare context for handler
                handler_context = {
                    'intent': intent_result,
                    'execution_id': execution_id,
                    'timestamp': time.time(),
                    'system_state': {
                        'mode': self.system_mode,
                        'is_waiting_for_user_action': self.is_waiting_for_user_action
                    }
                }
                
                # Call the handler's handle method
                result = handler.handle(command, handler_context)
                
                # Convert handler result to orchestrator format if needed
                return self._convert_handler_result_to_orchestrator_format(result, execution_context)
                
            else:
                # Fallback to legacy methods if handlers are not available
                logger.warning(f"[{execution_id}] Handler not available for intent '{intent_type}', using legacy methods")
                return self._fallback_to_legacy_handler(execution_id, command, intent_type, intent_result, execution_context)
                
        except Exception as e:
            logger.error(f"[{execution_id}] Handler routing failed for intent '{intent_type}': {e}")
            # Fallback to legacy methods for safety
            logger.info(f"[{execution_id}] Falling back to legacy handler methods")
            return self._fallback_to_legacy_handler(execution_id, command, intent_type, intent_result, execution_context)
    
    def _convert_handler_result_to_orchestrator_format(self, handler_result: Dict[str, Any], execution_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert handler result format to orchestrator execution result format.
        
        Args:
            handler_result: Result from handler.handle() method
            execution_context: Current execution context
            
        Returns:
            Orchestrator-formatted execution result
        """
        try:
            # Update execution context with handler result
            execution_context["status"] = CommandStatus.COMPLETED if handler_result.get("status") == "success" else CommandStatus.FAILED
            execution_context["end_time"] = time.time()
            execution_context["total_duration"] = execution_context["end_time"] - execution_context["start_time"]
            
            # Add handler-specific information
            if handler_result.get("status") == "success":
                execution_context["steps_completed"].append(ExecutionStep.ACTION)
                execution_context["execution_results"] = {
                    "success": True,
                    "message": handler_result.get("message", "Command executed successfully"),
                    "method": handler_result.get("method", "handler"),
                    "execution_time": handler_result.get("execution_time"),
                    "metadata": handler_result.get("metadata", {})
                }
                
                # Add conversational-specific fields if present
                if "response" in handler_result:
                    execution_context["execution_results"]["response"] = handler_result["response"]
                if "interaction_type" in handler_result:
                    execution_context["execution_results"]["interaction_type"] = handler_result["interaction_type"]
                if "conversation_context" in handler_result:
                    execution_context["execution_results"]["conversation_context"] = handler_result["conversation_context"]
                    
            else:
                execution_context["errors"].append(handler_result.get("message", "Handler execution failed"))
                execution_context["execution_results"] = {
                    "success": False,
                    "message": handler_result.get("message", "Command execution failed"),
                    "error": handler_result.get("message")
                }
            
            # Handle special case for deferred actions
            if handler_result.get("status") == "waiting_for_user_action":
                execution_context["status"] = CommandStatus.PROCESSING
                execution_context["execution_results"] = {
                    "success": True,
                    "message": handler_result.get("message", "Waiting for user action"),
                    "deferred_action": True,
                    "content_preview": handler_result.get("content_preview"),
                    "instructions": handler_result.get("instructions")
                }
                # Return the handler result directly for deferred actions
                return handler_result
            
            # Update progress
            final_status = CommandStatus.COMPLETED if handler_result.get("status") == "success" else CommandStatus.FAILED
            self._update_progress(execution_context["execution_id"], final_status)
            
            # Add to command history
            self.command_history.append(execution_context.copy())
            
            return self._format_execution_result(execution_context)
            
        except Exception as e:
            logger.error(f"Error converting handler result: {e}")
            # Return a basic error result
            execution_context["status"] = CommandStatus.FAILED
            execution_context["errors"].append(f"Result conversion failed: {str(e)}")
            return self._format_execution_result(execution_context)
    
    def _fallback_to_legacy_handler(self, execution_id: str, command: str, intent_type: str, intent_result: Dict[str, Any], execution_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fallback to legacy handler methods when new handlers are not available.
        
        Args:
            execution_id: Unique execution identifier
            command: Original user command
            intent_type: Recognized intent type
            intent_result: Result from intent recognition
            execution_context: Current execution context
            
        Returns:
            Execution result from legacy handler methods
        """
        try:
            if intent_type == 'conversational_chat':
                logger.info(f"[{execution_id}] Using legacy conversational handler")
                return self._handle_conversational_query(execution_id, command)
                
            elif intent_type == 'deferred_action':
                logger.info(f"[{execution_id}] Using legacy deferred action handler")
                return self._handle_deferred_action_request(execution_id, intent_result)
                
            elif intent_type == 'question_answering':
                logger.info(f"[{execution_id}] Using legacy question answering handler")
                return self._route_to_question_answering(command, execution_context)
                
            else:
                # For 'gui_interaction' or any other intent, use legacy GUI handler
                logger.info(f"[{execution_id}] Using legacy GUI interaction handler (intent: {intent_type})")
                return self._handle_gui_interaction(execution_id, command)
                
        except Exception as e:
            logger.error(f"[{execution_id}] Legacy handler fallback failed: {e}")
            # Final fallback - return error result
            execution_context["status"] = CommandStatus.FAILED
            execution_context["errors"].append(f"All handler methods failed: {str(e)}")
            return self._format_execution_result(execution_context)
    
    def _legacy_execute_command_internal(self, command: str, execution_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Legacy command execution logic preserved for GUI interactions.
        
        This method contains the original command processing logic that handles
        validation, perception, reasoning, and action execution for GUI commands.
        """
        execution_id = execution_context["execution_id"]
        start_time = execution_context["start_time"]
        
        try:
            # Step 2: Command Validation and Preprocessing
            logger.info(f"[{execution_id}] Step 2: Command validation")
            self._update_progress(execution_id, CommandStatus.VALIDATING, ExecutionStep.VALIDATION, 20)
            
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
            
            # Check if this is a question and route to answer_question method
            if validation_result.command_type in ["question", "detailed_question"]:
                logger.info(f"[{execution_id}] Detected {validation_result.command_type}, routing to information extraction mode")
                return self._route_to_question_answering(command, execution_context)
            
            # Step 2.5: Attempt Fast Path for GUI Commands
            fast_path_result = None
            if self._is_gui_command(normalized_command, validation_result.__dict__):
                logger.info(f"[{execution_id}] Attempting fast path execution for GUI command")
                self._update_progress(execution_id, CommandStatus.PROCESSING, ExecutionStep.PERCEPTION, 30)
                
                # Handle application focus changes and start background preloading
                self._handle_application_focus_change()
                
                fast_path_result = self._attempt_fast_path_execution(normalized_command, validation_result.__dict__)
                
                if fast_path_result and fast_path_result.get('success'):
                    # Fast path succeeded - complete execution
                    logger.info(f"[{execution_id}] Fast path execution successful")
                    
                    execution_context["status"] = CommandStatus.COMPLETED
                    execution_context["end_time"] = time.time()
                    execution_context["total_duration"] = execution_context["end_time"] - start_time
                    execution_context["fast_path_used"] = True
                    execution_context["fast_path_result"] = fast_path_result
                    execution_context["steps_completed"].extend([ExecutionStep.PERCEPTION, ExecutionStep.REASONING, ExecutionStep.ACTION])
                    
                    # Provide enhanced success feedback
                    if self.feedback_module:
                        self.feedback_module.provide_success_feedback(
                            success_context="gui_interaction",
                            priority=FeedbackPriority.HIGH
                        )
                    
                    # Final progress update
                    self._update_progress(execution_id, CommandStatus.COMPLETED, None, 100)
                    
                    # Add to command history
                    self.command_history.append(execution_context.copy())
                    
                    logger.info(f"[{execution_id}] Command completed via fast path in {execution_context['total_duration']:.2f}s")
                    return self._format_execution_result(execution_context)
                else:
                    # Fast path failed - continue with vision fallback
                    self._handle_fast_path_fallback(execution_id, execution_context, fast_path_result, normalized_command)
            
            # Provide initial feedback (if not already provided above)
            if not fast_path_result and self.feedback_module:
                self.feedback_module.play("thinking", FeedbackPriority.NORMAL)
            
            # Step 3: Parallel Perception and Reasoning Preparation
            execution_context["status"] = CommandStatus.PROCESSING
            self._update_progress(execution_id, CommandStatus.PROCESSING, ExecutionStep.PERCEPTION, 40)
            
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
            
            # Step 4: Action Execution
            logger.info(f"[{execution_id}] Step 4: Action execution")
            self._update_progress(execution_id, CommandStatus.PROCESSING, ExecutionStep.ACTION, 80)
            
            execution_results = self._perform_action_execution(execution_context)
            execution_context["execution_results"] = execution_results
            execution_context["steps_completed"].append(ExecutionStep.ACTION)
            
            # Command completed successfully
            execution_context["status"] = CommandStatus.COMPLETED
            execution_context["end_time"] = time.time()
            execution_context["total_duration"] = execution_context["end_time"] - start_time
            
            # Log performance comparison if this was a fallback from enhanced fast path
            if execution_context.get("fast_path_attempted") and execution_context.get("enhanced_fast_path_used"):
                self._log_fallback_performance_comparison(
                    execution_id, 
                    execution_context, 
                    execution_context["total_duration"]
                )
            
            # Final progress update
            self._update_progress(execution_id, CommandStatus.COMPLETED, ExecutionStep.CLEANUP, 100)
            
            # Provide enhanced success feedback
            if self.feedback_module:
                self.feedback_module.provide_success_feedback(
                    success_context="gui_interaction",
                    priority=FeedbackPriority.NORMAL
                )
            
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
            if self.feedback_module:
                self.feedback_module.play("failure", FeedbackPriority.HIGH)
                self.feedback_module.speak(
                    f"I encountered an error while executing your command: {str(e)}", 
                    FeedbackPriority.HIGH
                )
            
            # Add to history
            self.command_history.append(execution_context.copy())
            
            logger.error(f"[{execution_id}] Command execution failed: {e}")
            
            return self._format_execution_result(execution_context)
    
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
                
                # Capture and analyze screen using simple analysis for GUI commands
                screen_context = self.vision_module.describe_screen(analysis_type="simple")
                
                # Validate screen context
                if not screen_context or not screen_context.get("description"):
                    raise OrchestratorError("Invalid screen analysis result")
                
                # Count elements from different possible keys
                element_count = 0
                if "elements" in screen_context:
                    element_count = len(screen_context.get("elements", []))
                elif "main_elements" in screen_context:
                    element_count = len(screen_context.get("main_elements", []))
                
                logger.info(f"[{execution_id}] Screen perception successful: {element_count} elements found")
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
                
                if action_type in ["click", "double_click", "type"]:
                    # GUI automation actions
                    self.automation_module.execute_action(action)
                    action_result["status"] = "success"
                    execution_results["successful_actions"] += 1
                    
                elif action_type == "scroll":
                    # Enhanced scroll handling with context awareness
                    scroll_success = self._execute_enhanced_scroll(action, execution_id)
                    if scroll_success:
                        action_result["status"] = "success"
                        execution_results["successful_actions"] += 1
                    else:
                        action_result["status"] = "failed"
                        action_result["error"] = "Enhanced scroll execution failed"
                        execution_results["failed_actions"] += 1
                        execution_results["errors"].append("Enhanced scroll execution failed")
                    
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
            # Handle different result formats (GUI actions vs conversational responses)
            if "successful_actions" in exec_results:
                result["actions_executed"] = exec_results["successful_actions"]
                result["actions_failed"] = exec_results["failed_actions"]
                result["total_actions"] = exec_results["total_actions"]
            else:
                # For conversational and other non-action results
                result["success"] = exec_results.get("success", True)
                result["message"] = exec_results.get("message", "")
                if "response" in exec_results:
                    result["response"] = exec_results["response"]
                if "interaction_type" in exec_results:
                    result["interaction_type"] = exec_results["interaction_type"]
                if "conversation_context" in exec_results:
                    result["conversation_context"] = exec_results["conversation_context"]
                if "execution_time" in exec_results:
                    result["execution_time"] = exec_results["execution_time"]
        
        # Add errors and warnings if any
        if execution_context["errors"]:
            result["errors"] = execution_context["errors"]
        
        if execution_context["warnings"]:
            result["warnings"] = execution_context["warnings"]
        
        # Add conversational response if available
        if execution_context.get("response"):
            result["response"] = execution_context["response"]
            result["audio_feedback_provided"] = execution_context.get("audio_feedback_provided", False)
        
        # Add mode-specific information
        if execution_context.get("mode"):
            result["mode"] = execution_context["mode"]
        
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
                "normalized_command": validation_result.normalized_command if validation_result else execution_context["command"]
            } if validation_result else None
        }
        
        # Add hybrid execution path information
        if execution_context.get("fast_path_used"):
            result["execution_path"] = "fast"
            result["fast_path_result"] = execution_context.get("fast_path_result")
            
            # Record hybrid performance metrics
            fast_path_result = execution_context.get("fast_path_result", {})
            metric = PerformanceMetrics(
                operation="hybrid_execution_fast_path",
                duration=result["duration"],
                success=result["success"],
                parallel_execution=False,
                metadata={
                    'command_type': validation_result.command_type if validation_result else "unknown",
                    'element_found': bool(fast_path_result.get('element_found')),
                    'element_role': fast_path_result.get('element_found', {}).get('role', ''),
                    'element_title': fast_path_result.get('element_found', {}).get('title', ''),
                    'app_name': fast_path_result.get('element_found', {}).get('app_name', ''),
                    'execution_path': 'fast'
                }
            )
            performance_monitor.record_metric(metric)
            
        elif execution_context.get("fast_path_attempted"):
            result["execution_path"] = "slow"
            result["fallback_reason"] = execution_context.get("fallback_reason", "fast_path_failed")
            result["fast_path_attempted"] = True
            
            # Record hybrid performance metrics for fallback
            metric = PerformanceMetrics(
                operation="hybrid_execution_vision_fallback",
                duration=result["duration"],
                success=result["success"],
                parallel_execution=False,
                metadata={
                    'command_type': validation_result.command_type if validation_result else "unknown",
                    'fallback_reason': execution_context.get("fallback_reason", "unknown"),
                    'fast_path_attempted': True,
                    'execution_path': 'slow'
                }
            )
            performance_monitor.record_metric(metric)
            
        else:
            result["execution_path"] = "vision_only"
            
            # Record standard vision-only performance metrics
            metric = PerformanceMetrics(
                operation="standard_vision_execution",
                duration=result["duration"],
                success=result["success"],
                parallel_execution=execution_context.get("parallel_processing_used", False),
                metadata={
                    'command_type': validation_result.command_type if validation_result else "unknown",
                    'execution_path': 'vision_only'
                }
            )
            performance_monitor.record_metric(metric)
        
        return result
    
    def answer_question(self, question: str) -> Dict[str, Any]:
        """
        Answer a question about screen content using fast path content extraction with vision fallback.
        
        This method implements content type detection (browser vs PDF vs other applications)
        and uses text-based fast path extraction before falling back to vision-based analysis.
        
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
            
            # Try fast path content extraction first
            fast_path_result = self._try_fast_path_content_extraction(execution_id, question)
            
            if fast_path_result["success"]:
                logger.info(f"[{execution_id}] Fast path extraction successful, using text-based analysis")
                answer = fast_path_result["answer"]
                method_used = fast_path_result["method"]
                content_length = fast_path_result.get("content_length", 0)
                
                # Provide the answer via TTS and console output
                print(f"\n🤖 AURA: {answer}\n")
                logger.info(f"[{execution_id}] AURA Response (via {method_used}): {answer}")
                self.feedback_module.speak(answer, FeedbackPriority.NORMAL)
                
                # Format result with fast path metadata
                result = {
                    "execution_id": execution_id,
                    "question": question,
                    "answer": answer,
                    "status": "completed",
                    "duration": time.time() - start_time,
                    "success": True,
                    "metadata": {
                        "method": method_used,
                        "content_length": content_length,
                        "fast_path_used": True,
                        "vision_fallback_used": False,
                        "timestamp": start_time,
                        "extraction_time": fast_path_result.get("extraction_time", 0)
                    }
                }
                
                logger.info(f"[{execution_id}] Question answered successfully via fast path ({method_used})")
                return result
            
            # Fast path failed, fall back to vision-based analysis
            logger.info(f"[{execution_id}] Fast path failed ({fast_path_result.get('reason', 'unknown')}), falling back to vision analysis")
            
            # Determine analysis type based on question
            analysis_type = self._determine_analysis_type_for_question(question)
            
            # Capture and analyze screen for information extraction
            logger.info(f"[{execution_id}] Analyzing screen for information extraction (type: {analysis_type})")
            screen_context = self._analyze_screen_for_information(execution_id, analysis_type)
            
            # Create a specialized reasoning prompt for Q&A with enhanced context
            qa_command = self._create_qa_reasoning_prompt(question, screen_context)
            
            # Use reasoning module to generate answer with retry logic
            logger.info(f"[{execution_id}] Generating answer using reasoning module")
            action_plan = self._get_qa_action_plan(execution_id, qa_command, screen_context)
            
            # Extract and validate answer from action plan
            logger.debug(f"[{execution_id}] Action plan received: {action_plan}")
            answer = self._extract_and_validate_answer(action_plan, question)
            logger.debug(f"[{execution_id}] Extracted answer: '{answer}'")
            
            # Provide the answer via TTS and console output
            if answer and answer != "Information not available":
                # Print to console for user feedback (since TTS may not be working)
                print(f"\n🤖 AURA: {answer}\n")
                logger.info(f"[{execution_id}] AURA Response: {answer}")
                self.feedback_module.speak(answer, FeedbackPriority.NORMAL)
                success = True
            else:
                fallback_answer = "I couldn't find the information you're looking for on the current screen."
                print(f"\n🤖 AURA: {fallback_answer}\n")
                logger.info(f"[{execution_id}] AURA Fallback Response: {fallback_answer}")
                self.feedback_module.speak(fallback_answer, FeedbackPriority.NORMAL)
                answer = fallback_answer
                success = False
            
            # Format result with enhanced metadata
            result = {
                "execution_id": execution_id,
                "question": question,
                "answer": answer,
                "status": "completed",
                "duration": time.time() - start_time,
                "success": success,
                "metadata": {
                    "method": "vision_analysis",
                    "screen_elements_analyzed": len(screen_context.get("elements", [])),
                    "text_blocks_analyzed": len(screen_context.get("text_blocks", [])),
                    "confidence": action_plan.get("metadata", {}).get("confidence", 0.0),
                    "fast_path_used": False,
                    "vision_fallback_used": True,
                    "fast_path_failure_reason": fast_path_result.get("reason", "unknown"),
                    "timestamp": start_time,
                    "screen_resolution": screen_context.get("metadata", {}).get("screen_resolution", [0, 0])
                }
            }
            
            logger.info(f"[{execution_id}] Question answered successfully via vision fallback: {success}")
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
                    "timestamp": start_time,
                    "information_extraction_mode": True
                }
            }
    
    def _route_to_question_answering(self, question: str, execution_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route question to information extraction mode.
        
        Args:
            question: User's question
            execution_context: Current execution context
            
        Returns:
            Formatted execution result for question answering
        """
        execution_id = execution_context["execution_id"]
        
        try:
            logger.info(f"[{execution_id}] Processing question in information extraction mode")
            
            # Call the answer_question method
            qa_result = self.answer_question(question)
            
            # Convert Q&A result to execution result format
            execution_context["status"] = CommandStatus.COMPLETED if qa_result["success"] else CommandStatus.FAILED
            execution_context["end_time"] = time.time()
            execution_context["total_duration"] = execution_context["end_time"] - execution_context["start_time"]
            execution_context["steps_completed"] = ["validation", "perception", "reasoning"]
            
            if qa_result["success"]:
                execution_context["qa_result"] = qa_result
                self._update_progress(execution_id, CommandStatus.COMPLETED, progress_percentage=100)
            else:
                execution_context["errors"].append(qa_result.get("error", "Question answering failed"))
                self._update_progress(execution_id, CommandStatus.FAILED, error=qa_result.get("error"))
            
            # Add to history
            self.command_history.append(execution_context.copy())
            
            return self._format_execution_result(execution_context)
            
        except Exception as e:
            logger.error(f"[{execution_id}] Question routing failed: {e}")
            execution_context["status"] = CommandStatus.FAILED
            execution_context["errors"].append(str(e))
            self._update_progress(execution_id, CommandStatus.FAILED, error=str(e))
            
            # Add to history
            self.command_history.append(execution_context.copy())
            
            return self._format_execution_result(execution_context)

    def _try_fast_path_content_extraction(self, execution_id: str, question: str) -> Dict[str, Any]:
        """
        Try to extract content using fast path methods (browser/PDF text extraction).
        
        Args:
            execution_id: Unique execution identifier
            question: User's question
            
        Returns:
            Dictionary with success status, answer, method used, and metadata
        """
        try:
            # Get current application information
            if not self.accessibility_module:
                return {
                    "success": False,
                    "reason": "Accessibility module not available",
                    "answer": None,
                    "method": None
                }
            
            app_info = self.accessibility_module.get_active_application_info()
            if not app_info:
                return {
                    "success": False,
                    "reason": "Could not detect active application",
                    "answer": None,
                    "method": None
                }
            
            logger.info(f"[{execution_id}] Active application: {app_info.name} ({app_info.app_type.value})")
            
            # Try browser content extraction
            if app_info.app_type == ApplicationType.WEB_BROWSER and self.browser_accessibility_handler:
                return self._try_browser_content_extraction(execution_id, question, app_info)
            
            # Try PDF content extraction
            elif app_info.app_type == ApplicationType.PDF_READER and self.pdf_handler:
                return self._try_pdf_content_extraction(execution_id, question, app_info)
            
            # Application type not supported for fast path
            return {
                "success": False,
                "reason": f"Application type {app_info.app_type.value} not supported for fast path extraction",
                "answer": None,
                "method": None
            }
            
        except Exception as e:
            logger.error(f"[{execution_id}] Fast path content extraction failed: {e}")
            return {
                "success": False,
                "reason": f"Fast path extraction error: {str(e)}",
                "answer": None,
                "method": None
            }
    
    def _try_browser_content_extraction(self, execution_id: str, question: str, app_info) -> Dict[str, Any]:
        """Try to extract and analyze browser content."""
        try:
            extraction_start = time.time()
            
            # Extract page text content
            page_content = self.browser_accessibility_handler.get_page_text_content(app_info)
            
            if not page_content or len(page_content.strip()) < 50:
                return {
                    "success": False,
                    "reason": "No substantial content extracted from browser",
                    "answer": None,
                    "method": "browser_extraction"
                }
            
            extraction_time = time.time() - extraction_start
            logger.info(f"[{execution_id}] Extracted {len(page_content)} characters from browser in {extraction_time:.2f}s")
            
            # Use reasoning module to answer question based on extracted content
            reasoning_start = time.time()
            
            prompt = f"""Based on the following web page content, please answer this question: "{question}"

Web page content:
{page_content[:8000]}  # Limit content to avoid token limits

Please provide a direct, helpful answer based on the content above. If the answer cannot be found in the content, say "The information is not available in the current page content."
"""
            
            try:
                response = self.reasoning_module.process_query(prompt)
                reasoning_time = time.time() - reasoning_start
                
                if response and response.strip():
                    return {
                        "success": True,
                        "answer": response.strip(),
                        "method": "browser_text_extraction",
                        "content_length": len(page_content),
                        "extraction_time": extraction_time,
                        "reasoning_time": reasoning_time
                    }
                else:
                    return {
                        "success": False,
                        "reason": "Reasoning module returned empty response",
                        "answer": None,
                        "method": "browser_extraction"
                    }
                    
            except Exception as e:
                logger.error(f"[{execution_id}] Reasoning failed for browser content: {e}")
                return {
                    "success": False,
                    "reason": f"Reasoning failed: {str(e)}",
                    "answer": None,
                    "method": "browser_extraction"
                }
                
        except Exception as e:
            logger.error(f"[{execution_id}] Browser content extraction failed: {e}")
            return {
                "success": False,
                "reason": f"Browser extraction error: {str(e)}",
                "answer": None,
                "method": "browser_extraction"
            }
    
    def _try_pdf_content_extraction(self, execution_id: str, question: str, app_info) -> Dict[str, Any]:
        """Try to extract and analyze PDF content."""
        try:
            extraction_start = time.time()
            
            # Extract PDF text content
            pdf_content = self.pdf_handler.extract_text_from_open_document(app_info.name)
            
            if not pdf_content or len(pdf_content.strip()) < 50:
                return {
                    "success": False,
                    "reason": "No substantial content extracted from PDF",
                    "answer": None,
                    "method": "pdf_extraction"
                }
            
            extraction_time = time.time() - extraction_start
            logger.info(f"[{execution_id}] Extracted {len(pdf_content)} characters from PDF in {extraction_time:.2f}s")
            
            # Use reasoning module to answer question based on extracted content
            reasoning_start = time.time()
            
            prompt = f"""Based on the following PDF document content, please answer this question: "{question}"

PDF document content:
{pdf_content[:8000]}  # Limit content to avoid token limits

Please provide a direct, helpful answer based on the content above. If the answer cannot be found in the content, say "The information is not available in the current document."
"""
            
            try:
                response = self.reasoning_module.process_query(prompt)
                reasoning_time = time.time() - reasoning_start
                
                if response and response.strip():
                    return {
                        "success": True,
                        "answer": response.strip(),
                        "method": "pdf_text_extraction",
                        "content_length": len(pdf_content),
                        "extraction_time": extraction_time,
                        "reasoning_time": reasoning_time
                    }
                else:
                    return {
                        "success": False,
                        "reason": "Reasoning module returned empty response",
                        "answer": None,
                        "method": "pdf_extraction"
                    }
                    
            except Exception as e:
                logger.error(f"[{execution_id}] Reasoning failed for PDF content: {e}")
                return {
                    "success": False,
                    "reason": f"Reasoning failed: {str(e)}",
                    "answer": None,
                    "method": "pdf_extraction"
                }
                
        except Exception as e:
            logger.error(f"[{execution_id}] PDF content extraction failed: {e}")
            return {
                "success": False,
                "reason": f"PDF extraction error: {str(e)}",
                "answer": None,
                "method": "pdf_extraction"
            }

    def _determine_analysis_type_for_question(self, question: str) -> str:
        """
        Determine the appropriate analysis type based on the question.
        
        Args:
            question: User's question
            
        Returns:
            Analysis type: "simple", "detailed", or "form"
        """
        question_lower = question.lower()
        
        # Check for detailed analysis keywords
        detailed_keywords = [
            "in detail", "detailed", "analyze", "comprehensive", "everything",
            "all elements", "complete", "thorough", "full analysis"
        ]
        
        # Check for form-related keywords
        form_keywords = [
            "form", "input", "field", "submit", "button", "checkbox", 
            "dropdown", "select", "radio", "textarea"
        ]
        
        if any(keyword in question_lower for keyword in detailed_keywords):
            return "detailed"
        elif any(keyword in question_lower for keyword in form_keywords):
            return "form"
        else:
            return "simple"
    
    def _analyze_screen_for_information(self, execution_id: str, analysis_type: str = "simple") -> Dict[str, Any]:
        """
        Analyze screen content specifically for information extraction.
        
        Args:
            execution_id: Current execution ID for logging
            analysis_type: Type of analysis ("simple", "detailed", or "form")
            
        Returns:
            Enhanced screen context with information extraction focus
        """
        try:
            # Capture screen with appropriate analysis type
            logger.info(f"[{execution_id}] Using {analysis_type} analysis for screen capture")
            screen_context = self.vision_module.describe_screen(analysis_type=analysis_type)
            
            # Enhance context for information extraction
            if "elements" in screen_context:
                # Filter and categorize elements for better information extraction
                text_elements = []
                interactive_elements = []
                
                for element in screen_context["elements"]:
                    element_type = element.get("type", "")
                    element_text = element.get("text", "")
                    
                    if element_type in ["text", "label", "heading"] or element_text:
                        text_elements.append(element)
                    
                    if element_type in ["button", "link", "input", "dropdown"]:
                        interactive_elements.append(element)
                
                # Add categorized elements to context
                screen_context["text_elements"] = text_elements
                screen_context["interactive_elements"] = interactive_elements
                
                # Extract and summarize text content
                screen_context["extracted_text"] = self._extract_text_content(text_elements)
                screen_context["text_summary"] = self._summarize_text_content(screen_context["extracted_text"])
                
                logger.debug(f"[{execution_id}] Categorized {len(text_elements)} text elements and {len(interactive_elements)} interactive elements")
                logger.debug(f"[{execution_id}] Extracted {len(screen_context['extracted_text'])} text blocks")
            
            return screen_context
            
        except Exception as e:
            logger.error(f"[{execution_id}] Screen analysis for information extraction failed: {e}")
            raise
    
    def _extract_text_content(self, text_elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract and organize text content from screen elements.
        
        Args:
            text_elements: List of text-containing elements
            
        Returns:
            List of extracted text blocks with metadata
        """
        extracted_text = []
        
        for element in text_elements:
            text_content = element.get("text", "").strip()
            if text_content and len(text_content) > 1:  # Skip single characters
                text_block = {
                    "content": text_content,
                    "type": element.get("type", "text"),
                    "coordinates": element.get("coordinates", []),
                    "length": len(text_content),
                    "word_count": len(text_content.split()),
                    "is_heading": element.get("type") == "heading" or text_content.isupper(),
                    "contains_numbers": any(char.isdigit() for char in text_content),
                    "contains_special_chars": any(char in "!@#$%^&*()_+-=[]{}|;:,.<>?" for char in text_content)
                }
                extracted_text.append(text_block)
        
        # Sort by importance (headings first, then by length)
        extracted_text.sort(key=lambda x: (not x["is_heading"], -x["length"]))
        
        return extracted_text
    
    def _summarize_text_content(self, extracted_text: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create a summary of extracted text content.
        
        Args:
            extracted_text: List of extracted text blocks
            
        Returns:
            Summary of text content
        """
        if not extracted_text:
            return {
                "total_blocks": 0,
                "total_words": 0,
                "headings": [],
                "key_content": [],
                "has_forms": False,
                "has_navigation": False
            }
        
        headings = []
        key_content = []
        total_words = 0
        has_forms = False
        has_navigation = False
        
        # Analyze text blocks
        for block in extracted_text:
            content = block["content"].lower()
            total_words += block["word_count"]
            
            if block["is_heading"]:
                headings.append(block["content"])
            elif block["word_count"] >= 3:  # Meaningful content
                key_content.append(block["content"])
            
            # Detect forms
            if any(keyword in content for keyword in ["email", "password", "username", "login", "register", "submit"]):
                has_forms = True
            
            # Detect navigation
            if any(keyword in content for keyword in ["home", "about", "contact", "menu", "navigation", "back", "next"]):
                has_navigation = True
        
        return {
            "total_blocks": len(extracted_text),
            "total_words": total_words,
            "headings": headings[:5],  # Top 5 headings
            "key_content": key_content[:10],  # Top 10 content blocks
            "has_forms": has_forms,
            "has_navigation": has_navigation,
            "content_density": "high" if total_words > 100 else "medium" if total_words > 20 else "low"
        }
    
    def _create_qa_reasoning_prompt(self, question: str, screen_context: Dict[str, Any]) -> str:
        """
        Create a specialized reasoning prompt for question answering.
        
        Args:
            question: User's question
            screen_context: Screen analysis context
            
        Returns:
            Specialized Q&A prompt
        """
        # Count available information
        element_count = len(screen_context.get("elements", []))
        text_element_count = len(screen_context.get("text_elements", []))
        text_summary = screen_context.get("text_summary", {})
        
        # Create context-aware prompt based on screen content
        context_info = []
        
        # Add heading information if available
        if text_summary.get("headings"):
            headings_text = ", ".join(text_summary["headings"][:3])
            context_info.append(f"Main headings visible: {headings_text}")
        
        # Add content type information
        if text_summary.get("has_forms"):
            context_info.append("The screen contains form elements")
        
        if text_summary.get("has_navigation"):
            context_info.append("The screen contains navigation elements")
        
        # Add content density information
        content_density = text_summary.get("content_density", "unknown")
        context_info.append(f"Content density: {content_density}")
        
        # Build context string
        context_string = ". ".join(context_info) if context_info else "Limited context available"
        
        # Create enhanced prompt for information extraction
        qa_prompt = f"""Please analyze the screen content and answer this question: {question}

Screen Context: {context_string}

Available Information:
- {element_count} total screen elements
- {text_element_count} text elements
- {text_summary.get('total_words', 0)} words of text content

Instructions:
1. Look for information directly related to the question in the screen elements
2. Use the headings and key content to understand the page structure and purpose
3. If the exact information isn't visible, provide the closest relevant information available
4. Consider the context (forms, navigation, content type) when formulating your answer
5. If no relevant information is found, clearly state that the information is not available on the current screen
6. Keep the answer concise, accurate, and directly address the question
7. Use the 'speak' action to provide the answer to the user

Focus on being helpful while being honest about what information is actually visible on the screen."""
        
        return qa_prompt
    
    def _get_qa_action_plan(self, execution_id: str, qa_command: str, screen_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get action plan for question answering with retry logic.
        
        Args:
            execution_id: Current execution ID
            qa_command: Q&A reasoning prompt
            screen_context: Screen context
            
        Returns:
            Action plan from reasoning module
        """
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                logger.debug(f"[{execution_id}] Q&A reasoning attempt {attempt + 1}")
                
                action_plan = self.reasoning_module.get_action_plan(qa_command, screen_context)
                
                # Validate action plan for Q&A
                if not action_plan or "plan" not in action_plan:
                    raise OrchestratorError("Invalid Q&A action plan result")
                
                # Check if plan contains speak actions (required for Q&A)
                has_speak_action = any(action.get("action") == "speak" for action in action_plan["plan"])
                if not has_speak_action:
                    logger.warning(f"[{execution_id}] Q&A action plan missing speak actions, attempt {attempt + 1}")
                    if attempt < self.max_retries:
                        continue
                
                logger.info(f"[{execution_id}] Q&A reasoning successful")
                return action_plan
                
            except Exception as e:
                last_error = e
                logger.warning(f"[{execution_id}] Q&A reasoning attempt {attempt + 1} failed: {e}")
                
                if attempt < self.max_retries:
                    logger.info(f"[{execution_id}] Retrying Q&A reasoning in {self.retry_delay}s...")
                    time.sleep(self.retry_delay)
        
        # All attempts failed
        error_msg = f"Q&A reasoning failed after {self.max_retries + 1} attempts: {last_error}"
        raise OrchestratorError(error_msg)
    
    def _extract_and_validate_answer(self, action_plan: Dict[str, Any], question: str) -> str:
        """
        Extract and validate answer from action plan with enhanced fallback responses.
        
        Args:
            action_plan: Action plan from reasoning module
            question: Original question for validation
            
        Returns:
            Validated answer text with context-aware fallbacks
        """
        try:
            # Extract answer using existing method
            answer = self._extract_answer_from_plan(action_plan)
            
            # Validate answer quality
            if not answer:
                return self._generate_fallback_response(question, "no_answer")
            
            # Basic answer validation
            answer = answer.strip()
            
            # Check if answer is too generic or unhelpful
            generic_responses = [
                "i don't know",
                "i can't see",
                "not sure",
                "unclear",
                "unable to determine",
                "i cannot",
                "not visible",
                "can't tell"
            ]
            
            if any(generic in answer.lower() for generic in generic_responses):
                logger.warning("Answer appears to be generic, providing fallback response")
                return self._generate_fallback_response(question, "generic_answer")
            
            # Check minimum answer length (should be more than just "yes" or "no" for most questions)
            question_lower = question.lower()
            is_yes_no_question = question_lower.startswith(("is", "are", "can", "do", "does", "will", "would", "should"))
            
            if len(answer.split()) < 2 and not is_yes_no_question:
                logger.warning("Answer appears too short for the question type")
                return self._generate_fallback_response(question, "short_answer")
            
            # Check if answer actually addresses the question
            if not self._answer_addresses_question(answer, question):
                logger.warning("Answer doesn't seem to address the question")
                return self._generate_fallback_response(question, "irrelevant_answer")
            
            return answer
            
        except Exception as e:
            logger.error(f"Error validating answer: {e}")
            return self._generate_fallback_response(question, "error")
    
    def _generate_fallback_response(self, question: str, reason: str) -> str:
        """
        Generate context-aware fallback responses when information is not available.
        
        Args:
            question: Original question
            reason: Reason for fallback (no_answer, generic_answer, short_answer, irrelevant_answer, error)
            
        Returns:
            Context-aware fallback response
        """
        question_lower = question.lower()
        
        # Determine question type for better fallback
        if any(word in question_lower for word in ["what", "which"]):
            question_type = "what"
        elif any(word in question_lower for word in ["where", "location"]):
            question_type = "where"
        elif any(word in question_lower for word in ["how", "way"]):
            question_type = "how"
        elif any(word in question_lower for word in ["why", "reason"]):
            question_type = "why"
        elif any(word in question_lower for word in ["when", "time"]):
            question_type = "when"
        elif any(word in question_lower for word in ["who", "person"]):
            question_type = "who"
        else:
            question_type = "general"
        
        # Generate appropriate fallback based on question type and reason
        fallback_templates = {
            "what": [
                "I can't identify what you're asking about on the current screen.",
                "The specific information you're looking for isn't clearly visible to me.",
                "I don't see the details you're asking about on this screen."
            ],
            "where": [
                "I can't locate that item on the current screen.",
                "The location you're asking about isn't visible to me right now.",
                "I don't see that element on the screen at the moment."
            ],
            "how": [
                "I can't determine the process you're asking about from what's visible.",
                "The steps you're looking for aren't clear from the current screen.",
                "I don't see enough information to explain how to do that."
            ],
            "why": [
                "I can't determine the reason from what's currently visible.",
                "The explanation you're looking for isn't available on this screen.",
                "I don't see enough context to explain why that is."
            ],
            "when": [
                "I can't see any time or date information related to your question.",
                "The timing information you're asking about isn't visible.",
                "I don't see any schedule or time details on the screen."
            ],
            "who": [
                "I can't identify any person or contact information related to your question.",
                "The person you're asking about isn't mentioned on this screen.",
                "I don't see any names or contact details visible."
            ],
            "general": [
                "I couldn't find the information you're looking for on the current screen.",
                "The answer to your question isn't visible to me right now.",
                "I don't see enough relevant information to answer your question."
            ]
        }
        
        # Select appropriate template
        templates = fallback_templates.get(question_type, fallback_templates["general"])
        
        # Add helpful suggestions based on reason
        if reason == "error":
            return "I encountered an issue while trying to analyze the screen. Please try asking your question again."
        elif reason == "generic_answer":
            return f"{templates[0]} You might want to scroll or navigate to find more information."
        elif reason == "short_answer":
            return f"{templates[1]} Could you try rephrasing your question more specifically?"
        elif reason == "irrelevant_answer":
            return f"{templates[2]} The screen might not contain what you're looking for."
        else:
            return templates[0]
    
    def _answer_addresses_question(self, answer: str, question: str) -> bool:
        """
        Check if the answer actually addresses the question asked.
        
        Args:
            answer: Generated answer
            question: Original question
            
        Returns:
            True if answer seems relevant to question
        """
        try:
            # Extract key words from question (excluding common words)
            common_words = {"what", "where", "how", "why", "when", "who", "is", "are", "can", "do", "does", 
                          "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with",
                          "available", "screen"}  # Remove overly generic words
            
            # Clean and extract words, removing punctuation
            import re
            
            question_clean = re.sub(r'[^\w\s]', ' ', question.lower())
            answer_clean = re.sub(r'[^\w\s]', ' ', answer.lower())
            
            question_words = set(word for word in question_clean.split() 
                               if len(word) > 2 and word not in common_words)
            
            answer_words = set(word for word in answer_clean.split() 
                             if len(word) > 2)
            
            # Check if there's some overlap between question and answer keywords
            overlap = question_words.intersection(answer_words)
            
            # If there's meaningful overlap or the answer is substantial, consider it relevant
            has_overlap = len(overlap) > 0
            is_substantial = len(answer.split()) > 10
            
            return has_overlap or is_substantial
            
        except Exception as e:
            logger.warning(f"Error checking answer relevance: {e}")
            return True  # Default to accepting the answer if we can't validate

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
    
    def _create_fallback_screen_context(self, command: str) -> Dict[str, Any]:
        """
        Create fallback screen context when vision analysis fails.
        Uses predefined coordinates for common UI elements.
        
        Args:
            command: The user command to analyze
            
        Returns:
            Fallback screen context with estimated element locations
        """
        from config import FALLBACK_COORDINATES
        
        logger.info("Creating fallback screen context due to vision failure")
        
        # Extract potential button/element names from command
        command_lower = command.lower()
        fallback_elements = []
        
        # Check for known UI elements in the command
        for element_name, coordinates_list in FALLBACK_COORDINATES.items():
            if element_name in command_lower:
                # Create multiple element entries for different coordinate options
                for i, (x, y) in enumerate(coordinates_list):
                    element = {
                        "type": "button",
                        "text": element_name.title(),
                        "coordinates": [x, y, x + 100, y + 30],  # Estimated button size
                        "confidence": 0.7 - (i * 0.1),  # Decreasing confidence for alternatives
                        "clickable": True,
                        "fallback": True,
                        "source": "fallback_coordinates"
                    }
                    fallback_elements.append(element)
                
                logger.info(f"Added {len(coordinates_list)} fallback coordinates for '{element_name}'")
                break
        
        # If no specific element found, create generic clickable areas
        if not fallback_elements:
            logger.info("No specific element found, creating generic clickable areas")
            generic_areas = [
                (400, 300, "Center area"),
                (363, 360, "Common button area"),
                (500, 400, "Right center area"),
                (300, 400, "Left center area")
            ]
            
            for x, y, description in generic_areas:
                element = {
                    "type": "clickable_area",
                    "text": description,
                    "coordinates": [x, y, x + 100, y + 30],
                    "confidence": 0.5,
                    "clickable": True,
                    "fallback": True,
                    "source": "generic_fallback"
                }
                fallback_elements.append(element)
        
        # Create fallback context structure
        fallback_context = {
            "elements": fallback_elements,
            "text_blocks": [],
            "screen_info": {
                "width": 1440,  # Default screen width
                "height": 900,  # Default screen height
                "source": "fallback",
                "timestamp": time.time()
            },
            "analysis_type": "fallback",
            "fallback_reason": "vision_analysis_failed",
            "total_elements": len(fallback_elements)
        }
        
        logger.info(f"Created fallback context with {len(fallback_elements)} elements")
        return fallback_context
    
    def _handle_application_focus_change(self):
        """Handle application focus changes and start background preloading."""
        if not self.background_preload_enabled or not self.accessibility_module:
            return
        
        try:
            current_app = self.accessibility_module.get_active_application()
            if not current_app:
                return
            
            app_name = current_app.get('name')
            app_pid = current_app.get('pid')
            
            # Check if application focus changed
            if (self.last_active_app and 
                self.last_active_app.get('name') == app_name and 
                self.last_active_app.get('pid') == app_pid):
                return  # No change
            
            logger.debug(f"Application focus changed to: {app_name}")
            self.last_active_app = current_app
            
            # Start background tree loading for new application
            if current_app.get('accessible', False):
                task_id = self.accessibility_module.start_background_tree_loading(app_name, app_pid)
                logger.debug(f"Started background preloading for {app_name}: {task_id}")
                
                # Start predictive caching
                if self.accessibility_module.predictive_cache_enabled:
                    predictive_task_id = self.accessibility_module.start_predictive_caching(app_name, app_pid)
                    logger.debug(f"Started predictive caching for {app_name}: {predictive_task_id}")
            
            # Clean up old background tasks
            self.accessibility_module.cleanup_background_tasks()
            
        except Exception as e:
            logger.debug(f"Error handling application focus change: {e}")
    
    def get_parallel_processing_status(self) -> Dict[str, Any]:
        """
        Get status of parallel processing operations.
        
        Returns:
            Dictionary with parallel processing status and statistics
        """
        status = {
            'orchestrator': {
                'parallel_processing_enabled': self.enable_parallel_processing,
                'parallel_perception_reasoning': self.parallel_perception_reasoning,
                'background_preload_enabled': self.background_preload_enabled,
                'last_active_app': self.last_active_app
            }
        }
        
        # Add accessibility module parallel processing stats
        if self.accessibility_module:
            status['accessibility'] = self.accessibility_module.get_parallel_processing_stats()
            status['cache'] = self.accessibility_module.get_cache_statistics()
        
        return status
    
    def configure_parallel_processing(self, 
                                    orchestrator_parallel: Optional[bool] = None,
                                    background_preload: Optional[bool] = None,
                                    accessibility_parallel: Optional[bool] = None,
                                    predictive_cache: Optional[bool] = None):
        """
        Configure parallel processing settings across modules.
        
        Args:
            orchestrator_parallel: Enable/disable orchestrator parallel processing
            background_preload: Enable/disable background preloading
            accessibility_parallel: Enable/disable accessibility parallel processing
            predictive_cache: Enable/disable predictive caching
        """
        if orchestrator_parallel is not None:
            self.enable_parallel_processing = orchestrator_parallel
            self.parallel_perception_reasoning = orchestrator_parallel
            logger.info(f"Orchestrator parallel processing {'enabled' if orchestrator_parallel else 'disabled'}")
        
        if background_preload is not None:
            self.background_preload_enabled = background_preload
            logger.info(f"Background preloading {'enabled' if background_preload else 'disabled'}")
        
        if self.accessibility_module:
            self.accessibility_module.configure_parallel_processing(
                enabled=accessibility_parallel,
                predictive_cache=predictive_cache
            )
    
    def _attempt_fast_path_execution(self, command: str, command_info: Dict) -> Optional[Dict[str, Any]]:
        """
        Attempt to execute command using fast path accessibility detection with enhanced error recovery.
        
        Args:
            command: The user command
            command_info: Preprocessed command information
            
        Returns:
            Action result if successful, None if fast path fails
        """
        if not self.fast_path_enabled or not self.accessibility_module:
            logger.debug("Fast path disabled or accessibility module unavailable")
            
            # Run diagnostics if debugging is enabled
            if self.debug_mode_enabled and self.diagnostic_tools:
                try:
                    diagnostic_result = self.diagnostic_tools.run_quick_accessibility_check()
                    if diagnostic_result.get('issues'):
                        logger.debug(f"Accessibility diagnostic issues: {diagnostic_result['issues']}")
                except Exception as e:
                    logger.debug(f"Diagnostic check failed: {e}")
            
            return self._create_fast_path_failure_result("fast_path_disabled", command)
        
        # Check accessibility module status
        accessibility_status = self.accessibility_module.get_accessibility_status()
        if not accessibility_status.get('api_initialized', False):
            logger.debug("Accessibility API not initialized, skipping fast path")
            return self._create_fast_path_failure_result("accessibility_not_initialized", command, accessibility_status)
        
        # If in degraded mode, check if recovery is possible
        if accessibility_status.get('degraded_mode', False):
            if accessibility_status.get('can_attempt_recovery', False):
                logger.info("Accessibility module in degraded mode, attempting recovery")
                # The accessibility module will handle recovery internally
            else:
                logger.debug("Accessibility module in degraded mode, cannot recover")
                return self._create_fast_path_failure_result("accessibility_degraded", command, accessibility_status)
        
        # Attempt fast path execution with retry logic
        max_retries = 2
        retry_delay = 0.5  # seconds
        
        for attempt in range(max_retries + 1):
            try:
                logger.info(f"Attempting fast path execution (attempt {attempt + 1}/{max_retries + 1})")
                start_time = time.time()
                
                # Check if this is a direct typing command (no GUI element needed)
                command_type = command_info.get('command_type', 'unknown')
                if command_type == 'type':
                    # Handle direct typing without needing to find GUI elements
                    return self._execute_direct_typing_command(command, command_info)
                
                # Extract GUI elements from command for other types
                gui_elements = self._extract_gui_elements_from_command(command)
                if not gui_elements:
                    logger.debug("No GUI elements detected in command")
                    return self._create_fast_path_failure_result("no_gui_elements", command)
                
                logger.debug(f"Extracted GUI elements: {gui_elements}")
                
                # Use enhanced element finding with comprehensive result tracking
                logger.debug(f"Using enhanced element finding for: role='{gui_elements.get('role', '')}', label='{gui_elements.get('label', '')}', app_name='{gui_elements.get('app_name')}'")
                
                enhanced_result = self.accessibility_module.find_element_enhanced(
                    role=gui_elements.get('role', ''),
                    label=gui_elements.get('label', ''),
                    app_name=gui_elements.get('app_name')
                )
                
                # Extract element from enhanced result
                element_result = enhanced_result.element if enhanced_result and enhanced_result.found else None
                
                # Log enhanced search results for performance monitoring
                if enhanced_result:
                    logger.info(f"Enhanced element search completed: found={enhanced_result.found}, "
                               f"confidence={enhanced_result.confidence_score:.2f}, "
                               f"search_time={enhanced_result.search_time_ms:.1f}ms, "
                               f"matched_attribute='{enhanced_result.matched_attribute}', "
                               f"roles_checked={len(enhanced_result.roles_checked)}, "
                               f"attributes_checked={len(enhanced_result.attributes_checked)}")
                    
                    # Record enhanced fast path performance metrics
                    metric = PerformanceMetrics(
                        operation="enhanced_fast_path_element_search",
                        duration=enhanced_result.search_time_ms / 1000.0,  # Convert to seconds
                        success=enhanced_result.found,
                        parallel_execution=False,
                        metadata={
                            'confidence_score': enhanced_result.confidence_score,
                            'matched_attribute': enhanced_result.matched_attribute,
                            'roles_checked_count': len(enhanced_result.roles_checked),
                            'attributes_checked_count': len(enhanced_result.attributes_checked),
                            'fuzzy_matches_count': len(enhanced_result.fuzzy_matches),
                            'fallback_triggered': enhanced_result.fallback_triggered,
                            'element_role': element_result.get('role', '') if element_result else '',
                            'element_title': element_result.get('title', '') if element_result else '',
                            'app_name': gui_elements.get('app_name', ''),
                            'attempt': attempt + 1
                        }
                    )
                    performance_monitor.record_metric(metric)
                
                if not element_result:
                    logger.debug("Element not found via enhanced accessibility search")
                    
                    # Create detailed failure context from enhanced result
                    failure_context = {
                        'gui_elements': gui_elements,
                        'attempt': attempt + 1,
                        'enhanced_search_details': enhanced_result.to_dict() if enhanced_result else None
                    }
                    
                    # For element not found, don't retry - it's likely a legitimate miss
                    return self._create_fast_path_failure_result("element_not_found", command, failure_context)
                
                logger.info(f"Found element via enhanced accessibility search: {element_result}")
                
                # Execute the action using automation module
                action_type = gui_elements.get('action', 'click')
                coordinates = element_result['center_point']
                
                if not self.automation_module:
                    logger.error("Automation module not available for fast path execution")
                    return self._create_fast_path_failure_result("automation_unavailable", command)
                
                # Execute fast path action with enhanced element information
                action_result = self.automation_module.execute_fast_path_action(
                    action_type=action_type,
                    coordinates=coordinates,
                    element_info=element_result
                )
                
                execution_time = time.time() - start_time
                
                # Check if action was successful
                if not action_result.get('success', False):
                    logger.warning(f"Fast path action failed: {action_result.get('error', 'Unknown error')}")
                    
                    # For action failures, retry might help (transient issues)
                    if attempt < max_retries:
                        logger.info(f"Retrying fast path execution after action failure (attempt {attempt + 1})")
                        time.sleep(retry_delay)
                        continue
                    else:
                        return self._create_fast_path_failure_result("action_failed", command, {
                            'action_result': action_result,
                            'element_found': element_result,
                            'attempts': attempt + 1
                        })
                
                # Record successful performance metrics with enhanced details
                metric = PerformanceMetrics(
                    operation="enhanced_fast_path_execution_success",
                    duration=execution_time,
                    success=True,
                    parallel_execution=False,
                    metadata={
                        'element_role': element_result.get('role', ''),
                        'element_title': element_result.get('title', ''),
                        'action_type': action_type,
                        'app_name': element_result.get('app_name', ''),
                        'coordinates': coordinates,
                        'attempts': attempt + 1,
                        'retry_used': attempt > 0,
                        'enhanced_search_confidence': enhanced_result.confidence_score if enhanced_result else 0.0,
                        'enhanced_search_time_ms': enhanced_result.search_time_ms if enhanced_result else 0.0,
                        'matched_attribute': enhanced_result.matched_attribute if enhanced_result else '',
                        'roles_checked': len(enhanced_result.roles_checked) if enhanced_result else 0,
                        'attributes_checked': len(enhanced_result.attributes_checked) if enhanced_result else 0,
                        'fuzzy_matches': len(enhanced_result.fuzzy_matches) if enhanced_result else 0
                    }
                )
                performance_monitor.record_metric(metric)
                
                logger.info(f"Enhanced fast path execution successful in {execution_time:.2f}s (attempt {attempt + 1})")
                
                return {
                    'success': True,
                    'execution_time': execution_time,
                    'path_used': 'enhanced_fast',
                    'element_found': element_result,
                    'action_result': action_result,
                    'attempts': attempt + 1,
                    'retry_used': attempt > 0,
                    'enhanced_search_result': enhanced_result.to_dict() if enhanced_result else None,
                    'message': f"Successfully executed {action_type} on {element_result.get('title', 'element')} using enhanced fast path"
                }
                
            except Exception as e:
                error_info = global_error_handler.handle_error(
                    error=e,
                    module="orchestrator",
                    function="_attempt_fast_path_execution",
                    category=ErrorCategory.PROCESSING_ERROR,
                    severity=ErrorSeverity.MEDIUM,
                    context={
                        "command": command, 
                        "gui_elements": gui_elements if 'gui_elements' in locals() else None,
                        "enhanced_result": enhanced_result.to_dict() if 'enhanced_result' in locals() and enhanced_result else None,
                        "attempt": attempt + 1,
                        "max_retries": max_retries
                    }
                )
                
                logger.warning(f"Fast path execution failed on attempt {attempt + 1}: {error_info.message}")
                
                # Use error recovery manager if available
                should_retry = False
                if self.debug_mode_enabled and self.error_recovery_manager:
                    try:
                        recovery_result = self.error_recovery_manager.attempt_recovery(
                            error=e,
                            context={
                                'command': command,
                                'attempt': attempt + 1,
                                'max_retries': max_retries,
                                'gui_elements': gui_elements if 'gui_elements' in locals() else None
                            }
                        )
                        
                        should_retry = recovery_result.get('should_retry', False)
                        if recovery_result.get('actions_taken'):
                            logger.info(f"Recovery actions taken: {recovery_result['actions_taken']}")
                            
                    except Exception as recovery_error:
                        logger.debug(f"Error recovery failed: {recovery_error}")
                        # Fall back to original retry logic
                        should_retry = self._should_retry_fast_path_error(e, attempt, max_retries)
                else:
                    # Use original retry logic
                    should_retry = self._should_retry_fast_path_error(e, attempt, max_retries)
                
                if should_retry and attempt < max_retries:
                    logger.info(f"Retrying fast path execution after error (attempt {attempt + 1})")
                    time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
                    continue
                else:
                    # Record failed performance metrics with enhanced details
                    metric = PerformanceMetrics(
                        operation="enhanced_fast_path_execution_failed",
                        duration=time.time() - start_time if 'start_time' in locals() else 0,
                        success=False,
                        parallel_execution=False,
                        metadata={
                            'error_type': type(e).__name__,
                            'error_message': str(e),
                            'attempts': attempt + 1,
                            'final_failure': True,
                            'enhanced_search_attempted': 'enhanced_result' in locals(),
                            'enhanced_search_success': enhanced_result.found if 'enhanced_result' in locals() and enhanced_result else False,
                            'enhanced_search_confidence': enhanced_result.confidence_score if 'enhanced_result' in locals() and enhanced_result else 0.0
                        }
                    )
                    performance_monitor.record_metric(metric)
                    
                    return self._create_fast_path_failure_result("execution_error", command, {
                        'error': str(e),
                        'error_type': type(e).__name__,
                        'attempts': attempt + 1,
                        'error_info': error_info.__dict__ if error_info else None,
                        'enhanced_search_result': enhanced_result.to_dict() if 'enhanced_result' in locals() and enhanced_result else None
                    })
        
        # Should not reach here, but just in case
        return self._create_fast_path_failure_result("max_retries_exceeded", command)
    
    def _should_retry_fast_path_error(self, error: Exception, attempt: int, max_retries: int) -> bool:
        """
        Determine if a fast path error should trigger a retry.
        
        Args:
            error: The exception that occurred
            attempt: Current attempt number (0-based)
            max_retries: Maximum number of retries allowed
            
        Returns:
            True if retry should be attempted, False otherwise
        """
        if attempt >= max_retries:
            return False
        
        # Import accessibility exceptions for checking
        from modules.accessibility import (
            AccessibilityPermissionError, 
            AccessibilityAPIUnavailableError,
            ElementNotFoundError,
            AccessibilityTimeoutError,
            AccessibilityTreeTraversalError
        )
        
        # Don't retry for these error types (they're unlikely to resolve with retry)
        non_retryable_errors = (
            AccessibilityPermissionError,
            AccessibilityAPIUnavailableError,
            ElementNotFoundError
        )
        
        if isinstance(error, non_retryable_errors):
            return False
        
        # Retry for these error types (they might be transient)
        retryable_errors = (
            AccessibilityTimeoutError,
            AccessibilityTreeTraversalError,
            ConnectionError,
            TimeoutError
        )
        
        if isinstance(error, retryable_errors):
            return True
        
        # For other exceptions, retry once
        return attempt == 0
    
    def _create_fast_path_failure_result(self, failure_reason: str, command: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a standardized fast path failure result for logging and diagnostics.
        
        Args:
            failure_reason: Reason for failure
            command: Original command
            context: Additional context information
            
        Returns:
            Failure result dictionary
        """
        result = {
            'success': False,
            'path_used': 'fast',
            'failure_reason': failure_reason,
            'command': command,
            'timestamp': time.time(),
            'fallback_required': True
        }
        
        if context:
            result['context'] = context
        
        # Log failure for diagnostics
        logger.info(f"Fast path failure: {failure_reason} for command: '{command}'")
        if context:
            logger.debug(f"Fast path failure context: {context}")
        
        # Record failure metrics
        metric = PerformanceMetrics(
            operation="fast_path_failure",
            duration=0,
            success=False,
            parallel_execution=False,
            metadata={
                'failure_reason': failure_reason,
                'command_length': len(command),
                'has_context': bool(context)
            }
        )
        performance_monitor.record_metric(metric)
        
        return result
    
    def _handle_fast_path_fallback(self, execution_id: str, execution_context: Dict[str, Any], 
                                 fast_path_result: Dict[str, Any], command: str) -> None:
        """
        Handle fallback from enhanced fast path to vision workflow with comprehensive logging and performance comparison.
        
        Args:
            execution_id: Unique execution identifier
            execution_context: Current execution context
            fast_path_result: Result from failed enhanced fast path attempt
            command: Original command
        """
        # Extract failure details
        failure_reason = fast_path_result.get('failure_reason', 'unknown')
        failure_context = fast_path_result.get('context', {})
        fast_path_execution_time = fast_path_result.get('execution_time', 0)
        
        # Record fallback start time for performance comparison
        fallback_start_time = time.time()
        
        # Log detailed fallback information with enhanced context
        logger.info(f"[{execution_id}] Enhanced fast path failed, falling back to vision workflow")
        logger.info(f"[{execution_id}] Fallback reason: {failure_reason}")
        logger.info(f"[{execution_id}] Fast path execution time: {fast_path_execution_time:.3f}s")
        
        if failure_context:
            logger.debug(f"[{execution_id}] Fallback context: {failure_context}")
            
            # Log enhanced search details if available
            enhanced_search_details = failure_context.get('enhanced_search_details')
            if enhanced_search_details:
                logger.info(f"[{execution_id}] Enhanced search attempted: confidence={enhanced_search_details.get('confidence_score', 0):.2f}, "
                           f"roles_checked={len(enhanced_search_details.get('roles_checked', []))}, "
                           f"attributes_checked={len(enhanced_search_details.get('attributes_checked', []))}, "
                           f"fuzzy_matches={enhanced_search_details.get('fuzzy_match_count', 0)}")
        
        # Update execution context with enhanced fallback information
        execution_context["fast_path_attempted"] = True
        execution_context["enhanced_fast_path_used"] = True
        execution_context["fast_path_result"] = fast_path_result
        execution_context["fallback_reason"] = failure_reason
        execution_context["fallback_timestamp"] = fallback_start_time
        execution_context["fast_path_execution_time"] = fast_path_execution_time
        
        # Run comprehensive diagnostics if debugging is enabled
        if self.debug_mode_enabled and self.diagnostic_tools:
            try:
                logger.debug(f"[{execution_id}] Running automatic troubleshooting diagnostics")
                
                # Run targeted diagnostics based on failure reason
                diagnostic_result = self.diagnostic_tools.run_targeted_diagnostics(
                    failure_reason=failure_reason,
                    command=command,
                    context=failure_context
                )
                
                # Log diagnostic findings
                if diagnostic_result.get('issues'):
                    logger.info(f"[{execution_id}] Diagnostic issues found: {len(diagnostic_result['issues'])}")
                    for issue in diagnostic_result['issues'][:3]:  # Top 3 issues
                        logger.debug(f"[{execution_id}] Issue: {issue}")
                
                if diagnostic_result.get('recommendations'):
                    logger.info(f"[{execution_id}] Diagnostic recommendations: {len(diagnostic_result['recommendations'])}")
                    for recommendation in diagnostic_result['recommendations'][:2]:  # Top 2 recommendations
                        logger.info(f"[{execution_id}] Recommendation: {recommendation}")
                
                # Store diagnostic results for analysis
                execution_context["diagnostic_result"] = diagnostic_result
                
            except Exception as e:
                logger.debug(f"[{execution_id}] Automatic diagnostics failed: {e}")
        
        # Log accessibility diagnostics if available
        if self.accessibility_module:
            try:
                accessibility_status = self.accessibility_module.get_accessibility_status()
                diagnostics = self.accessibility_module.get_error_diagnostics()
                
                logger.debug(f"[{execution_id}] Accessibility status during fallback: {accessibility_status}")
                
                # Log specific diagnostic information
                if accessibility_status.get('degraded_mode'):
                    logger.warning(f"[{execution_id}] Accessibility module in degraded mode - error count: {accessibility_status.get('error_count', 0)}")
                
                if diagnostics.get('recovery_state', {}).get('can_attempt_recovery'):
                    logger.info(f"[{execution_id}] Accessibility recovery may be possible in future attempts")
                
                # Store diagnostics for later analysis
                execution_context["accessibility_diagnostics"] = {
                    'status': accessibility_status,
                    'diagnostics': diagnostics,
                    'fallback_timestamp': time.time()
                }
                
            except Exception as e:
                logger.warning(f"[{execution_id}] Could not retrieve accessibility diagnostics: {e}")
        
        # Categorize fallback reason for metrics
        fallback_category = self._categorize_fallback_reason(failure_reason)
        
        # Record enhanced fallback metrics with performance comparison
        metric = PerformanceMetrics(
            operation="enhanced_fast_path_fallback",
            duration=0,  # Fallback itself doesn't take time
            success=True,  # Fallback is successful if it happens
            parallel_execution=False,
            metadata={
                'failure_reason': failure_reason,
                'fallback_category': fallback_category,
                'command_type': getattr(execution_context.get('validation_result'), 'command_type', 'unknown'),
                'accessibility_degraded': self.accessibility_module.degraded_mode if self.accessibility_module else False,
                'has_context': bool(failure_context),
                'fast_path_execution_time': fast_path_execution_time,
                'enhanced_fast_path_used': True,
                'enhanced_search_attempted': bool(failure_context.get('enhanced_search_details')),
                'enhanced_search_confidence': failure_context.get('enhanced_search_details', {}).get('confidence_score', 0) if failure_context else 0,
                'roles_checked_count': len(failure_context.get('enhanced_search_details', {}).get('roles_checked', [])) if failure_context else 0,
                'attributes_checked_count': len(failure_context.get('enhanced_search_details', {}).get('attributes_checked', [])) if failure_context else 0,
                'fuzzy_matches_count': failure_context.get('enhanced_search_details', {}).get('fuzzy_match_count', 0) if failure_context else 0
            }
        )
        performance_monitor.record_metric(metric)
        
        # Provide appropriate feedback based on failure reason
        if self.feedback_module:
            if failure_reason in ['accessibility_degraded', 'accessibility_not_initialized']:
                # Subtle indication that we're using visual analysis due to accessibility issues
                self.feedback_module.play("thinking", FeedbackPriority.LOW)
            else:
                # Standard thinking sound for normal fallback
                self.feedback_module.play("thinking", FeedbackPriority.NORMAL)
        
        # Log user-friendly fallback message
        fallback_messages = {
            'element_not_found': f"Element not found via enhanced fast detection, using visual analysis",
            'accessibility_degraded': f"Using visual analysis due to accessibility limitations",
            'accessibility_not_initialized': f"Using visual analysis (accessibility unavailable)",
            'no_gui_elements': f"Command requires visual analysis",
            'action_failed': f"Enhanced fast action failed, retrying with visual analysis",
            'execution_error': f"Enhanced fast path error, using visual analysis as backup"
        }
        
        user_message = fallback_messages.get(failure_reason, f"Using visual analysis for command execution")
        logger.info(f"[{execution_id}] {user_message}")
    
    def _log_fallback_performance_comparison(self, execution_id: str, execution_context: Dict[str, Any], 
                                           vision_execution_time: float) -> None:
        """
        Log performance comparison between enhanced fast path and vision fallback.
        
        Args:
            execution_id: Unique execution identifier
            execution_context: Current execution context with fast path results
            vision_execution_time: Time taken by vision workflow in seconds
        """
        if not FALLBACK_PERFORMANCE_LOGGING:
            return
            
        try:
            fast_path_time = execution_context.get("fast_path_execution_time", 0)
            fast_path_result = execution_context.get("fast_path_result", {})
            fallback_reason = execution_context.get("fallback_reason", "unknown")
            
            # Calculate performance metrics
            time_difference = vision_execution_time - fast_path_time
            performance_ratio = vision_execution_time / fast_path_time if fast_path_time > 0 else float('inf')
            
            # Log detailed performance comparison
            logger.info(f"[{execution_id}] Performance Comparison - Enhanced Fast Path vs Vision Fallback:")
            logger.info(f"[{execution_id}]   Enhanced Fast Path: {fast_path_time:.3f}s (failed: {fallback_reason})")
            logger.info(f"[{execution_id}]   Vision Fallback: {vision_execution_time:.3f}s")
            logger.info(f"[{execution_id}]   Time Difference: {time_difference:+.3f}s")
            logger.info(f"[{execution_id}]   Performance Ratio: {performance_ratio:.2f}x")
            
            # Log enhanced search details if available
            enhanced_search_result = fast_path_result.get('enhanced_search_result')
            if enhanced_search_result:
                logger.info(f"[{execution_id}]   Enhanced Search Details:")
                logger.info(f"[{execution_id}]     - Confidence: {enhanced_search_result.get('confidence_score', 0):.2f}")
                logger.info(f"[{execution_id}]     - Roles Checked: {len(enhanced_search_result.get('roles_checked', []))}")
                logger.info(f"[{execution_id}]     - Attributes Checked: {len(enhanced_search_result.get('attributes_checked', []))}")
                logger.info(f"[{execution_id}]     - Fuzzy Matches: {enhanced_search_result.get('fuzzy_match_count', 0)}")
                logger.info(f"[{execution_id}]     - Fallback Triggered: {enhanced_search_result.get('fallback_triggered', False)}")
            
            # Record performance comparison metrics
            metric = PerformanceMetrics(
                operation="enhanced_fast_path_vs_vision_comparison",
                duration=vision_execution_time,
                success=True,
                parallel_execution=False,
                metadata={
                    'fast_path_time': fast_path_time,
                    'vision_time': vision_execution_time,
                    'time_difference': time_difference,
                    'performance_ratio': performance_ratio,
                    'fallback_reason': fallback_reason,
                    'enhanced_search_confidence': enhanced_search_result.get('confidence_score', 0) if enhanced_search_result else 0,
                    'enhanced_search_roles_checked': len(enhanced_search_result.get('roles_checked', [])) if enhanced_search_result else 0,
                    'enhanced_search_attributes_checked': len(enhanced_search_result.get('attributes_checked', [])) if enhanced_search_result else 0,
                    'enhanced_search_fuzzy_matches': enhanced_search_result.get('fuzzy_match_count', 0) if enhanced_search_result else 0,
                    'enhanced_search_fallback_triggered': enhanced_search_result.get('fallback_triggered', False) if enhanced_search_result else False
                }
            )
            performance_monitor.record_metric(metric)
            
            # Provide insights based on performance comparison
            if time_difference > FALLBACK_TIMEOUT_THRESHOLD:
                logger.warning(f"[{execution_id}] Vision fallback took significantly longer than fast path "
                              f"({time_difference:.1f}s difference). Consider optimizing accessibility detection.")
            elif time_difference < -1.0:  # Fast path was actually slower (shouldn't happen often)
                logger.info(f"[{execution_id}] Enhanced fast path was slower than expected. "
                           f"Vision fallback was more efficient by {abs(time_difference):.1f}s.")
            
            # Run performance analysis if debugging is enabled
            if self.debug_mode_enabled and self.diagnostic_tools:
                try:
                    performance_analysis = self.diagnostic_tools.analyze_performance_comparison(
                        fast_path_time=fast_path_time,
                        vision_time=vision_execution_time,
                        fallback_reason=fallback_reason,
                        enhanced_search_result=enhanced_search_result
                    )
                    
                    if performance_analysis.get('insights'):
                        logger.info(f"[{execution_id}] Performance insights: {performance_analysis['insights']}")
                    
                    if performance_analysis.get('optimization_suggestions'):
                        for suggestion in performance_analysis['optimization_suggestions'][:2]:
                            logger.info(f"[{execution_id}] Optimization suggestion: {suggestion}")
                            
                except Exception as debug_error:
                    logger.debug(f"[{execution_id}] Performance analysis failed: {debug_error}")
            
        except Exception as e:
            logger.warning(f"[{execution_id}] Failed to log fallback performance comparison: {e}")
    
    def _categorize_fallback_reason(self, failure_reason: str) -> str:
        """
        Categorize fallback reasons for metrics and analysis.
        
        Args:
            failure_reason: The specific failure reason
            
        Returns:
            General category of the failure
        """
        category_mapping = {
            'element_not_found': 'element_detection',
            'accessibility_degraded': 'accessibility_issue',
            'accessibility_not_initialized': 'accessibility_issue',
            'fast_path_disabled': 'configuration',
            'no_gui_elements': 'command_parsing',
            'action_failed': 'action_execution',
            'execution_error': 'system_error',
            'automation_unavailable': 'system_error',
            'max_retries_exceeded': 'retry_exhausted'
        }
        
        return category_mapping.get(failure_reason, 'unknown')
    
    def _execute_direct_typing_command(self, command: str, command_info: Dict) -> Dict[str, Any]:
        """
        Execute a direct typing command without needing to find GUI elements.
        
        Args:
            command: The user command
            command_info: Preprocessed command information
            
        Returns:
            Action result dictionary
        """
        try:
            logger.info(f"Executing direct typing command: {command}")
            start_time = time.time()
            
            # Extract text to type from command
            text_to_type = self._extract_text_from_type_command(command)
            if not text_to_type:
                logger.warning("Could not extract text from typing command")
                return self._create_fast_path_failure_result("no_text_to_type", command)
            
            logger.debug(f"Text to type: '{text_to_type}'")
            
            if not self.automation_module:
                logger.error("Automation module not available for direct typing")
                return self._create_fast_path_failure_result("automation_unavailable", command)
            
            # Execute direct typing using automation module
            type_action = {
                'action': 'type',
                'text': text_to_type
            }
            
            try:
                self.automation_module.execute_action(type_action)
                action_result = {'success': True}
            except Exception as e:
                action_result = {'success': False, 'error': str(e)}
            
            execution_time = time.time() - start_time
            
            if action_result.get('success', False):
                logger.info(f"Direct typing successful in {execution_time:.3f}s")
                
                # Record successful performance metrics
                metric = PerformanceMetrics(
                    operation="direct_typing_success",
                    duration=execution_time,
                    success=True,
                    parallel_execution=False,
                    metadata={
                        'text_length': len(text_to_type),
                        'command': command,
                        'method': 'direct_typing'
                    }
                )
                performance_monitor.record_metric(metric)
                
                return {
                    'success': True,
                    'path_used': 'fast',
                    'action_type': 'type',
                    'text_typed': text_to_type,
                    'execution_time': execution_time,
                    'command': command,
                    'timestamp': time.time()
                }
            else:
                logger.warning(f"Direct typing failed: {action_result.get('error', 'Unknown error')}")
                return self._create_fast_path_failure_result("typing_failed", command, {
                    'action_result': action_result,
                    'text_to_type': text_to_type
                })
                
        except Exception as e:
            logger.error(f"Error in direct typing execution: {e}")
            return self._create_fast_path_failure_result("typing_error", command, {'error': str(e)})
    
    def _extract_text_from_type_command(self, command: str) -> str:
        """
        Extract the text to type from a typing command.
        
        Args:
            command: The user command
            
        Returns:
            Text to type, or empty string if not found
        """
        command_lower = command.lower().strip()
        
        # Try patterns with quotes first
        quoted_patterns = [
            r'type\s+["\'](.+)["\']',
            r'enter\s+["\'](.+)["\']',
            r'input\s+["\'](.+)["\']',
            r'write\s+["\'](.+)["\']'
        ]
        
        for pattern in quoted_patterns:
            match = re.search(pattern, command_lower)
            if match:
                return match.group(1).strip()
        
        # Try patterns without quotes
        unquoted_patterns = [
            r'type\s+(.+)',
            r'enter\s+(.+)',
            r'input\s+(.+)',
            r'write\s+(.+)'
        ]
        
        for pattern in unquoted_patterns:
            match = re.search(pattern, command_lower)
            if match:
                text = match.group(1).strip()
                # Remove common trailing words that aren't part of the text
                text = re.sub(r'\s+(please|now|here)$', '', text)
                return text
        
        return ""
    
    def _extract_target_from_command(self, command: str) -> str:
        """
        Extract target element name from natural language command.
        
        Removes action words ("click", "type", "press") and articles ("the", "on", "a", "an")
        to isolate the target element name.
        
        Args:
            command: Natural language command
            
        Returns:
            Extracted target element name
            
        Examples:
            "Click on the Gmail link" -> "gmail link"
            "Press the Submit button" -> "submit button"
            "Type in the search box" -> "search box"
        """
        try:
            # Check cache first if accessibility module is available
            if self.accessibility_module:
                cached_result = self.accessibility_module._get_cached_target_extraction(command)
                if cached_result is not None:
                    target, action_type, confidence = cached_result
                    logger.debug(f"Target extraction cache hit: '{command}' -> '{target}' (confidence: {confidence:.2f})")
                    return target
            
            # Convert to lowercase for processing
            processed_command = command.lower().strip()
            
            # Define action words to remove
            action_words = [
                'click', 'press', 'tap', 'select', 'choose', 'hit',
                'type', 'enter', 'input', 'write', 'fill',
                'scroll', 'swipe', 'drag', 'move',
                'open', 'close', 'minimize', 'maximize',
                'double', 'right'  # For double-click, right-click
            ]
            
            # Define articles and prepositions to remove
            articles = [
                'the', 'a', 'an', 'on', 'in', 'at', 'to', 'for', 'with',
                'into', 'onto', 'upon', 'inside', 'within'
            ]
            
            # Split command into words
            words = processed_command.split()
            
            # Track removed words for confidence scoring
            removed_words = []
            
            # Remove action words
            filtered_words = []
            for word in words:
                if word in action_words:
                    removed_words.append(word)
                else:
                    filtered_words.append(word)
            
            # Remove articles and prepositions
            final_words = []
            for word in filtered_words:
                if word in articles:
                    removed_words.append(word)
                else:
                    final_words.append(word)
            
            # Join remaining words to form target (preserve original case)
            if final_words:
                # Reconstruct target preserving original case
                original_words = command.split()
                target_parts = []
                for word in final_words:
                    # Find the original case version of this word
                    for orig_word in original_words:
                        if orig_word.lower() == word:
                            target_parts.append(orig_word)
                            break
                    else:
                        # If not found, use the lowercase version
                        target_parts.append(word)
                target = ' '.join(target_parts).strip()
            else:
                target = ''
            
            # If target is empty or too short, fall back to original command
            if not target or len(target) < 2:
                logger.debug(f"Target extraction resulted in empty/short target, using original command")
                return command.strip()
            
            # Calculate confidence based on words removed and remaining text
            confidence = self._calculate_target_extraction_confidence(
                original_command=command,
                extracted_target=target,
                removed_words=removed_words
            )
            
            # Determine action type from removed words
            action_type = self._determine_action_type(removed_words)
            
            # Cache the result if accessibility module is available
            if self.accessibility_module:
                self.accessibility_module._cache_target_extraction_result(command, target, action_type, confidence)
            
            logger.debug(f"Target extraction: '{command}' -> '{target}' (confidence: {confidence:.2f}, action: {action_type})")
            
            return target
            
        except Exception as e:
            logger.error(f"Error extracting target from command '{command}': {e}")
            return command.strip()  # Fallback to original command
    
    def _determine_action_type(self, removed_words: List[str]) -> str:
        """
        Determine the primary action type from removed words.
        
        Args:
            removed_words: List of words that were removed during target extraction
            
        Returns:
            Primary action type ('click', 'type', 'scroll', etc.)
        """
        # Define action type mappings
        action_mappings = {
            'click': ['click', 'tap', 'select', 'choose', 'press', 'hit'],
            'type': ['type', 'enter', 'input', 'write', 'fill'],
            'scroll': ['scroll', 'swipe'],
            'drag': ['drag', 'move'],
            'open': ['open'],
            'close': ['close', 'minimize', 'maximize']
        }
        
        # Find the first matching action type
        for action_type, action_words in action_mappings.items():
            for word in removed_words:
                if word in action_words:
                    return action_type
        
        # Default to 'click' if no specific action found
        return 'click'
    
    def _calculate_target_extraction_confidence(self, original_command: str, extracted_target: str, removed_words: List[str]) -> float:
        """
        Calculate confidence score for target extraction.
        
        Args:
            original_command: Original user command
            extracted_target: Extracted target text
            removed_words: List of words that were removed
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        try:
            original_words = original_command.lower().split()
            target_words = extracted_target.lower().split()
            
            # Base confidence starts at 0.5
            confidence = 0.5
            
            # Increase confidence if we removed action words (good extraction)
            action_words_removed = sum(1 for word in removed_words if word in [
                'click', 'press', 'tap', 'select', 'type', 'enter', 'input', 'write'
            ])
            if action_words_removed > 0:
                confidence += 0.2 * min(action_words_removed, 2)  # Max +0.4
            
            # Increase confidence if we removed articles (good extraction)
            articles_removed = sum(1 for word in removed_words if word in [
                'the', 'a', 'an', 'on', 'in', 'at'
            ])
            if articles_removed > 0:
                confidence += 0.1 * min(articles_removed, 2)  # Max +0.2
            
            # Decrease confidence if target is too short relative to original
            if len(original_words) > 0 and len(target_words) < len(original_words) * 0.3:
                confidence -= 0.2
            
            # Increase confidence if target contains meaningful words
            if target_words:
                meaningful_words = [word for word in target_words if len(word) > 2]
                if len(meaningful_words) >= len(target_words) * 0.7:
                    confidence += 0.1
            
            # Ensure confidence is within bounds
            confidence = max(0.0, min(1.0, confidence))
            
            return confidence
            
        except Exception as e:
            logger.debug(f"Error calculating target extraction confidence: {e}")
            return 0.5  # Default confidence
    
    def _extract_gui_elements_from_command(self, command: str) -> Dict[str, str]:
        """
        Enhanced GUI element extraction with intelligent target parsing.
        
        Uses enhanced target extraction to isolate the target element name
        and returns empty role for broader element searching.
        
        Args:
            command: User command to parse
            
        Returns:
            Dictionary with 'role', 'label', 'action', and optionally 'app_name' keys
        """
        gui_elements = {
            'role': '',  # Empty for broader search
            'label': '',
            'action': 'click',
            'app_name': None
        }
        
        try:
            command_lower = command.lower().strip()
            
            # Extract action type
            action_patterns = {
                'click': [r'\b(?:click|press|tap)\b', r'\bselect\b'],
                'double_click': [r'\bdouble.?click\b', r'\bopen\b'],
                'type': [r'\btype\b', r'\benter\b', r'\binput\b', r'\bwrite\b'],
                'scroll': [r'\bscroll\b', r'\bpage\s+(?:up|down)\b']
            }
            
            for action, patterns in action_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, command_lower):
                        gui_elements['action'] = action
                        break
                if gui_elements['action'] != 'click':
                    break
            
            # Use enhanced target extraction to get the cleaned target
            extracted_target = self._extract_target_from_command(command)
            
            # If target extraction succeeded, use it as the label
            if extracted_target and extracted_target != command.strip():
                gui_elements['label'] = extracted_target
                logger.debug(f"Using enhanced target extraction: '{command}' -> '{extracted_target}'")
            else:
                # Fallback to full command text when target extraction fails
                logger.debug(f"Target extraction failed, using full command text as fallback")
                gui_elements['label'] = command.strip()
            
            # Extract application name if specified (improved logic)
            # Only look for explicit app name patterns that don't interfere with target extraction
            app_patterns = [
                r'in\s+(\w+)\s+app\b',  # "in Safari app"
                r'in\s+(\w+)\s+application\b',  # "in Chrome application"
                r'(?:on|in)\s+(\w+)\s+window\b',  # "in Safari window" - but only single word apps
            ]
            
            for pattern in app_patterns:
                match = re.search(pattern, command_lower)
                if match:
                    app_name = match.group(1).strip()
                    # Filter out common words that aren't app names
                    common_words = ['the', 'this', 'that', 'my', 'current', 'active', 'main', 'search', 'file']
                    if app_name not in common_words and len(app_name) > 2:
                        gui_elements['app_name'] = app_name.title()
                        break
            
            # Validate that we have enough information for GUI command
            if not gui_elements['label']:
                logger.debug("No label extracted from command")
                return {}
            
            # Note: We intentionally leave role empty for broader element searching
            # This allows the accessibility module to search all clickable element types
            
            logger.debug(f"Enhanced GUI elements extracted: {gui_elements}")
            return gui_elements
            
        except Exception as e:
            logger.error(f"Error extracting GUI elements from command: {e}")
            return {}
    
    def _is_gui_command(self, command: str, command_info: Dict) -> bool:
        """
        Determine if a command is a GUI interaction command suitable for fast path.
        
        Args:
            command: The user command
            command_info: Preprocessed command information
            
        Returns:
            True if command is a GUI command, False otherwise
        """
        try:
            command_type = command_info.get('command_type', 'unknown')
            
            # Check if command type indicates GUI interaction
            gui_command_types = ['click', 'type', 'scroll', 'form_fill']
            if command_type in gui_command_types:
                return True
            
            # Check for GUI-related keywords in the command
            command_lower = command.lower()
            gui_keywords = [
                'click', 'press', 'tap', 'select', 'button', 'menu', 'link',
                'type', 'enter', 'input', 'text field', 'checkbox', 'tab',
                'scroll', 'page up', 'page down', 'window', 'dialog'
            ]
            
            for keyword in gui_keywords:
                if keyword in command_lower:
                    return True
            
            # Check if we can extract GUI elements from the command
            gui_elements = self._extract_gui_elements_from_command(command)
            return bool(gui_elements.get('label') or gui_elements.get('role'))
            
        except Exception as e:
            logger.debug(f"Error determining if command is GUI command: {e}")
            return False
    
    def _execute_enhanced_scroll(self, action: Dict[str, Any], execution_id: str) -> bool:
        """
        Execute enhanced scroll command with context awareness and focusing.
        
        This method implements the enhanced scroll reliability required by
        Task 0.9 of the system stabilization plan.
        
        Args:
            action: Scroll action dictionary
            execution_id: Unique execution identifier
            
        Returns:
            True if scroll was successful, False otherwise
        """
        try:
            logger.debug(f"[{execution_id}] Starting enhanced scroll execution")
            
            # Extract scroll parameters
            direction = action.get("direction", "up")
            amount = action.get("amount", 100)
            
            # Step 1: Detect scroll context and identify scrollable areas
            scroll_context = self._detect_scroll_context(execution_id)
            
            # Step 2: Focus primary scrollable area if found
            if scroll_context.get("scrollable_areas"):
                focus_success = self._focus_primary_scrollable_area(
                    scroll_context["scrollable_areas"], 
                    execution_id
                )
                if focus_success:
                    logger.info(f"[{execution_id}] Successfully focused primary scrollable area")
                else:
                    logger.warning(f"[{execution_id}] Failed to focus scrollable area, using fallback")
            else:
                logger.info(f"[{execution_id}] No specific scrollable areas found, using current behavior")
            
            # Step 3: Execute scroll with enhanced error handling
            scroll_success = self._execute_scroll_with_fallback(action, execution_id)
            
            if scroll_success:
                logger.info(f"[{execution_id}] Enhanced scroll completed successfully")
                return True
            else:
                logger.error(f"[{execution_id}] Enhanced scroll failed")
                return False
                
        except Exception as e:
            logger.error(f"[{execution_id}] Enhanced scroll execution failed: {e}")
            return False
    
    def _detect_scroll_context(self, execution_id: str) -> Dict[str, Any]:
        """
        Detect scroll context and identify scrollable areas.
        
        Args:
            execution_id: Unique execution identifier
            
        Returns:
            Dictionary containing scroll context information
        """
        try:
            logger.debug(f"[{execution_id}] Detecting scroll context")
            
            scroll_context = {
                "scrollable_areas": [],
                "active_application": None,
                "detection_method": "none",
                "confidence": 0.0
            }
            
            # Get active application information
            if hasattr(self, 'application_detector') and self.application_detector:
                try:
                    app_info = self.application_detector.get_active_application_info()
                    if app_info:
                        scroll_context["active_application"] = app_info.to_dict()
                        logger.debug(f"[{execution_id}] Active application: {app_info.name}")
                except Exception as e:
                    logger.debug(f"[{execution_id}] Failed to get application info: {e}")
            
            # Try to detect scrollable areas using accessibility API
            if self.accessibility_module and self.module_availability.get('accessibility', False):
                try:
                    scrollable_areas = self._find_scrollable_areas_accessibility(execution_id)
                    if scrollable_areas:
                        scroll_context["scrollable_areas"] = scrollable_areas
                        scroll_context["detection_method"] = "accessibility"
                        scroll_context["confidence"] = 0.8
                        logger.debug(f"[{execution_id}] Found {len(scrollable_areas)} scrollable areas via accessibility")
                except Exception as e:
                    logger.debug(f"[{execution_id}] Accessibility-based detection failed: {e}")
            
            # Fallback: Try to detect scrollable areas using vision
            if not scroll_context["scrollable_areas"] and self.vision_module and self.module_availability.get('vision', False):
                try:
                    scrollable_areas = self._find_scrollable_areas_vision(execution_id)
                    if scrollable_areas:
                        scroll_context["scrollable_areas"] = scrollable_areas
                        scroll_context["detection_method"] = "vision"
                        scroll_context["confidence"] = 0.6
                        logger.debug(f"[{execution_id}] Found {len(scrollable_areas)} scrollable areas via vision")
                except Exception as e:
                    logger.debug(f"[{execution_id}] Vision-based detection failed: {e}")
            
            return scroll_context
            
        except Exception as e:
            logger.error(f"[{execution_id}] Error detecting scroll context: {e}")
            return {
                "scrollable_areas": [],
                "active_application": None,
                "detection_method": "error",
                "confidence": 0.0
            }
    
    def _find_scrollable_areas_accessibility(self, execution_id: str) -> List[Dict[str, Any]]:
        """
        Find scrollable areas using accessibility API.
        
        Args:
            execution_id: Unique execution identifier
            
        Returns:
            List of scrollable area information
        """
        try:
            scrollable_areas = []
            
            # Common scrollable roles in accessibility API
            scrollable_roles = [
                "AXScrollArea", "AXTable", "AXOutline", "AXList", 
                "AXWebArea", "AXTextArea", "AXGroup"
            ]
            
            # Try to find elements with scrollable roles
            for role in scrollable_roles:
                try:
                    elements = self.accessibility_module.find_elements_by_role(role)
                    for element in elements[:3]:  # Limit to first 3 for performance
                        if self._is_element_scrollable(element):
                            area_info = {
                                "role": role,
                                "coordinates": element.get("coordinates", [0, 0]),
                                "size": element.get("size", [100, 100]),
                                "title": element.get("title", ""),
                                "confidence": 0.8
                            }
                            scrollable_areas.append(area_info)
                            logger.debug(f"[{execution_id}] Found scrollable {role}: {area_info['title']}")
                except Exception as e:
                    logger.debug(f"[{execution_id}] Error finding {role} elements: {e}")
                    continue
            
            return scrollable_areas
            
        except Exception as e:
            logger.debug(f"[{execution_id}] Error in accessibility-based scrollable area detection: {e}")
            return []
    
    def _find_scrollable_areas_vision(self, execution_id: str) -> List[Dict[str, Any]]:
        """
        Find scrollable areas using vision analysis.
        
        Args:
            execution_id: Unique execution identifier
            
        Returns:
            List of scrollable area information
        """
        try:
            scrollable_areas = []
            
            # Use vision module to analyze screen for scrollable content
            screen_analysis = self.vision_module.describe_screen(analysis_type="detailed")
            
            if screen_analysis and "elements" in screen_analysis:
                for element in screen_analysis["elements"]:
                    # Look for elements that might be scrollable
                    element_text = element.get("text", "").lower()
                    element_type = element.get("type", "").lower()
                    
                    # Check for scrollable indicators
                    scrollable_indicators = [
                        "scroll", "list", "table", "content", "text area",
                        "document", "page", "feed", "timeline"
                    ]
                    
                    if any(indicator in element_text or indicator in element_type 
                           for indicator in scrollable_indicators):
                        area_info = {
                            "type": element_type,
                            "coordinates": element.get("coordinates", [0, 0]),
                            "size": element.get("size", [100, 100]),
                            "text": element.get("text", ""),
                            "confidence": 0.6
                        }
                        scrollable_areas.append(area_info)
                        logger.debug(f"[{execution_id}] Found potential scrollable area via vision: {element_text[:50]}")
            
            return scrollable_areas
            
        except Exception as e:
            logger.debug(f"[{execution_id}] Error in vision-based scrollable area detection: {e}")
            return []
    
    def _is_element_scrollable(self, element: Dict[str, Any]) -> bool:
        """
        Check if an accessibility element is scrollable.
        
        Args:
            element: Element information from accessibility API
            
        Returns:
            True if element appears to be scrollable
        """
        try:
            # Check for scrollable attributes
            if element.get("scrollable", False):
                return True
            
            # Check for scroll-related properties
            properties = element.get("properties", {})
            if properties.get("AXHorizontalScrollBar") or properties.get("AXVerticalScrollBar"):
                return True
            
            # Check size - large elements are more likely to be scrollable
            size = element.get("size", [0, 0])
            if len(size) >= 2 and size[0] > 200 and size[1] > 200:
                return True
            
            return False
            
        except Exception:
            return False
    
    def _focus_primary_scrollable_area(self, scrollable_areas: List[Dict[str, Any]], execution_id: str) -> bool:
        """
        Focus the primary scrollable area before scrolling.
        
        Args:
            scrollable_areas: List of detected scrollable areas
            execution_id: Unique execution identifier
            
        Returns:
            True if successfully focused a scrollable area
        """
        try:
            if not scrollable_areas:
                return False
            
            # Sort by confidence and size to find the best candidate
            sorted_areas = sorted(
                scrollable_areas, 
                key=lambda x: (x.get("confidence", 0), 
                              x.get("size", [0, 0])[0] * x.get("size", [0, 0])[1]),
                reverse=True
            )
            
            primary_area = sorted_areas[0]
            logger.debug(f"[{execution_id}] Attempting to focus primary scrollable area")
            
            # Click on the center of the scrollable area to focus it
            coordinates = primary_area.get("coordinates", [0, 0])
            size = primary_area.get("size", [100, 100])
            
            if len(coordinates) >= 2 and len(size) >= 2:
                # Calculate center point
                center_x = coordinates[0] + size[0] // 2
                center_y = coordinates[1] + size[1] // 2
                
                # Create a click action to focus the area
                focus_action = {
                    "action": "click",
                    "coordinates": [center_x, center_y]
                }
                
                # Execute the focus click
                self.automation_module.execute_action(focus_action)
                logger.info(f"[{execution_id}] Focused scrollable area at ({center_x}, {center_y})")
                
                # Small delay to ensure focus is established
                time.sleep(0.2)
                return True
            
            return False
            
        except Exception as e:
            logger.warning(f"[{execution_id}] Error focusing primary scrollable area: {e}")
            return False
    
    def _execute_scroll_with_fallback(self, action: Dict[str, Any], execution_id: str) -> bool:
        """
        Execute scroll with comprehensive fallback mechanisms.
        
        Args:
            action: Scroll action dictionary
            execution_id: Unique execution identifier
            
        Returns:
            True if scroll was successful
        """
        try:
            # Try primary scroll execution
            try:
                self.automation_module.execute_action(action)
                logger.debug(f"[{execution_id}] Primary scroll execution successful")
                return True
            except Exception as primary_error:
                logger.warning(f"[{execution_id}] Primary scroll failed: {primary_error}")
            
            # Fallback 1: Try with different scroll amounts
            original_amount = action.get("amount", 100)
            fallback_amounts = [original_amount // 2, original_amount * 2, 50, 200]
            
            for amount in fallback_amounts:
                try:
                    fallback_action = action.copy()
                    fallback_action["amount"] = amount
                    self.automation_module.execute_action(fallback_action)
                    logger.info(f"[{execution_id}] Fallback scroll successful with amount {amount}")
                    return True
                except Exception as fallback_error:
                    logger.debug(f"[{execution_id}] Fallback amount {amount} failed: {fallback_error}")
                    continue
            
            # Fallback 2: Try alternative scroll directions if original failed
            direction = action.get("direction", "up")
            if direction in ["up", "down"]:
                alternative_directions = ["down", "up"]
                alt_direction = alternative_directions[0] if direction == "up" else alternative_directions[1]
                
                try:
                    alt_action = action.copy()
                    alt_action["direction"] = alt_direction
                    alt_action["amount"] = original_amount // 2  # Smaller amount for alternative direction
                    self.automation_module.execute_action(alt_action)
                    logger.info(f"[{execution_id}] Alternative direction scroll successful: {alt_direction}")
                    return True
                except Exception as alt_error:
                    logger.debug(f"[{execution_id}] Alternative direction failed: {alt_error}")
            
            # All fallbacks failed
            logger.error(f"[{execution_id}] All scroll fallback methods failed")
            return False
            
        except Exception as e:
            logger.error(f"[{execution_id}] Error in scroll fallback execution: {e}")
            return False