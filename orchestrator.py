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
        
        # Command validation patterns
        self._init_validation_patterns()
        
        # Initialize modules with error handling
        self._initialize_modules()
        
        # Initialize system health monitoring
        self._initialize_system_health()
        
        logger.info("Orchestrator initialized successfully")
    
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
                    return None
            
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
                    'feedback': 'healthy' if self.module_availability.get('feedback', False) else 'unavailable'
                },
                'error_rates': {
                    'vision': 0.0,
                    'reasoning': 0.0,
                    'automation': 0.0,
                    'audio': 0.0,
                    'feedback': 0.0
                },
                'recovery_attempts': {
                    'vision': 0,
                    'reasoning': 0,
                    'automation': 0,
                    'audio': 0,
                    'feedback': 0
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
            'feedback': False
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
        non_critical_failures = [module for module in ['audio', 'feedback'] if not module_init_status[module]]
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
        
        # Ensure only one command executes at a time
        with self.execution_lock:
            try:
                return self._execute_command_internal(command.strip())
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
            
            # Check if this is a question and route to answer_question method
            if validation_result.command_type in ["question", "detailed_question"]:
                logger.info(f"[{execution_id}] Detected {validation_result.command_type}, routing to information extraction mode")
                return self._route_to_question_answering(command, execution_context)
            
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
                
                # Capture and analyze screen using simple analysis for GUI commands
                screen_context = self.vision_module.describe_screen(analysis_type="simple")
                
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
                    "screen_elements_analyzed": len(screen_context.get("elements", [])),
                    "text_blocks_analyzed": len(screen_context.get("text_blocks", [])),
                    "confidence": action_plan.get("metadata", {}).get("confidence", 0.0),
                    "information_extraction_mode": True,
                    "timestamp": start_time,
                    "screen_resolution": screen_context.get("metadata", {}).get("screen_resolution", [0, 0])
                }
            }
            
            logger.info(f"[{execution_id}] Question answered successfully: {success}")
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