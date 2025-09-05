"""
AccessibilityModule for AURA - Fast Path GUI Element Detection

This module provides high-speed, non-visual interface for querying macOS UI elements
using the Accessibility API, enabling near-instantaneous GUI automation.
"""

import logging
import time
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
import re
import threading
from collections import defaultdict
import concurrent.futures
import asyncio
from functools import partial
from contextlib import contextmanager

# Import fuzzy matching library with error handling
try:
    from thefuzz import fuzz
    FUZZY_MATCHING_AVAILABLE = True
except ImportError as e:
    FUZZY_MATCHING_AVAILABLE = False
    logging.warning(f"Fuzzy matching library not available: {e}. Install with: pip install thefuzz[speedup]")

# Import AppKit for application management only (not accessibility functions)
try:
    from AppKit import NSWorkspace, NSApplication
    APPKIT_AVAILABLE = True
except ImportError as e:
    APPKIT_AVAILABLE = False
    logging.warning(f"AppKit framework not available: {e}")

# Import ALL accessibility functions exclusively from ApplicationServices
try:
    from ApplicationServices import (
        AXUIElementCreateSystemWide,
        AXUIElementCreateApplication,
        AXUIElementCopyAttributeValue,
        kAXFocusedApplicationAttribute,
        kAXRoleAttribute,
        kAXTitleAttribute,
        kAXDescriptionAttribute,
        kAXEnabledAttribute,
        kAXChildrenAttribute,
        kAXPositionAttribute,
        kAXSizeAttribute
    )
    ACCESSIBILITY_FUNCTIONS_AVAILABLE = True
except ImportError:
    # Fallback: try to load via objc bundle
    try:
        import objc
        bundle = objc.loadBundle('ApplicationServices', globals())
        ACCESSIBILITY_FUNCTIONS_AVAILABLE = 'AXUIElementCreateSystemWide' in globals()
    except:
        ACCESSIBILITY_FUNCTIONS_AVAILABLE = False

# Set overall availability flag
ACCESSIBILITY_AVAILABLE = APPKIT_AVAILABLE and ACCESSIBILITY_FUNCTIONS_AVAILABLE


@dataclass
class AccessibilityElement:
    """Represents a UI element found via Accessibility API."""
    role: str
    title: str
    coordinates: List[int]  # [x, y, width, height]
    center_point: List[int]  # [center_x, center_y]
    enabled: bool
    app_name: str
    element_id: Optional[str] = None
    attributes: Optional[Dict[str, Any]] = None


@dataclass
class CachedElementTree:
    """Represents a cached accessibility tree for an application."""
    app_name: str
    app_pid: int
    elements: List[Dict[str, Any]]
    timestamp: float
    ttl: float = 30.0  # Default TTL of 30 seconds
    
    def is_expired(self) -> bool:
        """Check if the cached tree has expired."""
        return time.time() - self.timestamp > self.ttl
    
    def get_age(self) -> float:
        """Get the age of the cache in seconds."""
        return time.time() - self.timestamp


@dataclass
class ElementIndex:
    """Index for fast element lookup by role and title."""
    role_index: Dict[str, List[Dict[str, Any]]]
    title_index: Dict[str, List[Dict[str, Any]]]
    normalized_title_index: Dict[str, List[Dict[str, Any]]]
    
    def __init__(self):
        self.role_index = defaultdict(list)
        self.title_index = defaultdict(list)
        self.normalized_title_index = defaultdict(list)


@dataclass
class ElementMatchResult:
    """Enhanced result from element matching with detailed metadata."""
    element: Optional[Dict[str, Any]]
    found: bool
    confidence_score: float
    matched_attribute: str
    search_time_ms: float
    roles_checked: List[str]
    attributes_checked: List[str]
    fuzzy_matches: List[Dict[str, Any]]  # All fuzzy matches with scores
    fallback_triggered: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging and debugging."""
        return {
            'found': self.found,
            'confidence_score': self.confidence_score,
            'matched_attribute': self.matched_attribute,
            'search_time_ms': self.search_time_ms,
            'roles_checked': self.roles_checked,
            'attributes_checked': self.attributes_checked,
            'fuzzy_match_count': len(self.fuzzy_matches),
            'fallback_triggered': self.fallback_triggered,
            'element_info': {
                'role': self.element.get('role') if self.element else None,
                'title': self.element.get('title') if self.element else None,
                'coordinates': self.element.get('coordinates') if self.element else None
            } if self.element else None
        }


@dataclass
class TargetExtractionResult:
    """Result from command target extraction."""
    original_command: str
    extracted_target: str
    action_type: str
    confidence: float
    removed_words: List[str]
    processing_time_ms: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            'original_command': self.original_command,
            'extracted_target': self.extracted_target,
            'action_type': self.action_type,
            'confidence': self.confidence,
            'removed_words': self.removed_words,
            'processing_time_ms': self.processing_time_ms
        }


@dataclass
class PerformanceMetrics:
    """Performance metrics for accessibility operations."""
    operation_name: str
    start_time: float
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    timeout_ms: Optional[float] = None
    timed_out: bool = False
    success: bool = True
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def finish(self, success: bool = True, error_message: Optional[str] = None):
        """Mark the operation as finished and calculate duration."""
        self.end_time = time.time()
        self.duration_ms = (self.end_time - self.start_time) * 1000
        self.success = success
        self.error_message = error_message
        
        # Check if operation timed out
        if self.timeout_ms and self.duration_ms > self.timeout_ms:
            self.timed_out = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            'operation': self.operation_name,
            'duration_ms': self.duration_ms,
            'timeout_ms': self.timeout_ms,
            'timed_out': self.timed_out,
            'success': self.success,
            'error_message': self.error_message,
            'metadata': self.metadata or {}
        }


@dataclass
class FastPathPerformanceReport:
    """Comprehensive performance report for fast path execution."""
    total_duration_ms: float
    target_extraction_ms: float
    element_search_ms: float
    fuzzy_matching_ms: float
    attribute_checking_ms: float
    cache_operations_ms: float
    success: bool
    fallback_triggered: bool
    timeout_warnings: List[str]
    performance_warnings: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            'total_duration_ms': self.total_duration_ms,
            'target_extraction_ms': self.target_extraction_ms,
            'element_search_ms': self.element_search_ms,
            'fuzzy_matching_ms': self.fuzzy_matching_ms,
            'attribute_checking_ms': self.attribute_checking_ms,
            'cache_operations_ms': self.cache_operations_ms,
            'success': self.success,
            'fallback_triggered': self.fallback_triggered,
            'timeout_warnings': self.timeout_warnings,
            'performance_warnings': self.performance_warnings,
            'meets_performance_target': self.total_duration_ms < 2000
        }


class AccessibilityPermissionError(Exception):
    """Raised when accessibility permissions are not granted."""
    def __init__(self, message: str, recovery_suggestion: Optional[str] = None):
        super().__init__(message)
        self.recovery_suggestion = recovery_suggestion or (
            "Please grant accessibility permissions in System Preferences > "
            "Security & Privacy > Privacy > Accessibility"
        )


class AccessibilityAPIUnavailableError(Exception):
    """Raised when accessibility API is not available."""
    def __init__(self, message: str, recovery_suggestion: Optional[str] = None):
        super().__init__(message)
        self.recovery_suggestion = recovery_suggestion or (
            "Install required accessibility frameworks: pip install pyobjc-framework-AppKit pyobjc-framework-Accessibility"
        )


class ElementNotFoundError(Exception):
    """Raised when requested element cannot be found."""
    def __init__(self, message: str, element_role: Optional[str] = None, element_label: Optional[str] = None):
        super().__init__(message)
        self.element_role = element_role
        self.element_label = element_label


class AccessibilityTimeoutError(Exception):
    """Raised when accessibility operations timeout."""
    def __init__(self, message: str, operation: Optional[str] = None):
        super().__init__(message)
        self.operation = operation


class AccessibilityTreeTraversalError(Exception):
    """Raised when accessibility tree traversal fails."""
    def __init__(self, message: str, depth: Optional[int] = None):
        super().__init__(message)
        self.depth = depth


class AccessibilityCoordinateError(Exception):
    """Raised when coordinate calculation fails."""
    def __init__(self, message: str, element_info: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.element_info = element_info


class FuzzyMatchingError(Exception):
    """Raised when fuzzy matching operations fail."""
    def __init__(self, message: str, target_text: str, element_text: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.target_text = target_text
        self.element_text = element_text
        self.original_error = original_error


class TargetExtractionError(Exception):
    """Raised when target extraction from command fails."""
    def __init__(self, message: str, command: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.command = command
        self.original_error = original_error


class AttributeAccessError(Exception):
    """Raised when accessibility attribute access fails."""
    def __init__(self, message: str, attribute: str, element_info: Dict[str, Any], original_error: Optional[Exception] = None):
        super().__init__(message)
        self.attribute = attribute
        self.element_info = element_info
        self.original_error = original_error


class EnhancedFastPathError(Exception):
    """Raised when enhanced fast path operations fail."""
    def __init__(self, message: str, operation: str, fallback_available: bool = True, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.operation = operation
        self.fallback_available = fallback_available
        self.original_error = original_error


class ConfigurationValidationError(Exception):
    """Raised when configuration validation fails."""
    def __init__(self, message: str, parameter: str, current_value: Any, expected_type: Optional[type] = None):
        super().__init__(message)
        self.parameter = parameter
        self.current_value = current_value
        self.expected_type = expected_type


class AccessibilityModule:
    """
    Provides high-speed, non-visual interface for querying macOS UI elements
    using the Accessibility API.
    """
    
    def __init__(self):
        """Initialize accessibility API connections with error handling."""
        self.logger = logging.getLogger(__name__)
        self.workspace = None
        self.accessibility_enabled = False
        self.degraded_mode = False
        self.last_error_time = None
        self.error_count = 0
        self.max_retries = 3
        self.retry_delay = 1.0  # seconds
        self.permission_check_interval = 30.0  # seconds
        
        # Error recovery state
        self.recovery_attempts = 0
        self.max_recovery_attempts = 5
        self.backoff_multiplier = 2.0
        
        # Element caching system
        self.element_cache: Dict[str, CachedElementTree] = {}
        self.cache_lock = threading.RLock()
        self.current_app_name = None
        self.current_app_pid = None
        self.cache_ttl = 30.0  # Default cache TTL in seconds
        self.max_cache_size = 10  # Maximum number of cached applications
        
        # Element indexing for fast lookup
        self.element_indexes: Dict[str, ElementIndex] = {}
        
        # Cache statistics
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'invalidations': 0,
            'expirations': 0,
            'total_lookups': 0
        }
        
        # Parallel processing configuration
        self.parallel_processing_enabled = True
        self.background_thread_pool = concurrent.futures.ThreadPoolExecutor(
            max_workers=2, 
            thread_name_prefix="accessibility_bg"
        )
        self.preload_thread_pool = concurrent.futures.ThreadPoolExecutor(
            max_workers=1,
            thread_name_prefix="accessibility_preload"
        )
        
        # Background processing state
        self.background_tasks = {}
        self.preload_tasks = {}
        self.predictive_cache_enabled = True
        
        # Common UI patterns for predictive caching
        self.common_ui_patterns = [
            {'role': 'AXButton', 'labels': ['OK', 'Cancel', 'Apply', 'Close', 'Save']},
            {'role': 'AXMenuItem', 'labels': ['File', 'Edit', 'View', 'Help', 'Preferences']},
            {'role': 'AXTextField', 'labels': ['Search', 'Username', 'Password', 'Email']},
            {'role': 'AXLink', 'labels': ['Home', 'About', 'Contact', 'Login', 'Sign Up']}
        ]
        
        # Load and validate configuration with fallback
        self.config = self._validate_configuration_with_fallback()
        
        # Performance monitoring configuration (load from config)
        try:
            from config import (
                PERFORMANCE_MONITORING_ENABLED, PERFORMANCE_WARNING_THRESHOLD,
                PERFORMANCE_HISTORY_SIZE
            )
            self.performance_monitoring_enabled = PERFORMANCE_MONITORING_ENABLED
            self.max_performance_history = PERFORMANCE_HISTORY_SIZE
            self.performance_warning_threshold_ms = PERFORMANCE_WARNING_THRESHOLD
        except ImportError:
            # Fallback defaults if config is not available
            self.performance_monitoring_enabled = True
            self.max_performance_history = 100
            self.performance_warning_threshold_ms = 1500
        
        # Use validated configuration values
        self.fast_path_timeout_ms = self.config['fast_path_timeout_ms']
        self.fuzzy_matching_timeout_ms = self.config['fuzzy_matching_timeout_ms']
        self.attribute_check_timeout_ms = self.config['attribute_check_timeout_ms']
        self.fuzzy_matching_enabled = self.config['fuzzy_matching_enabled']
        self.fuzzy_confidence_threshold = self.config['fuzzy_confidence_threshold']
        self.clickable_roles = set(self.config['clickable_roles'])
        self.accessibility_attributes = self.config['accessibility_attributes']
        self.debug_logging = self.config['debug_logging']
        self.log_fuzzy_match_scores = self.config['log_fuzzy_match_scores']
        
        self.performance_metrics: List[PerformanceMetrics] = []
        self.performance_lock = threading.RLock()
        
        # Performance statistics
        self.performance_stats = {
            'total_operations': 0,
            'successful_operations': 0,
            'timed_out_operations': 0,
            'average_duration_ms': 0.0,
            'fastest_operation_ms': float('inf'),
            'slowest_operation_ms': 0.0,
            'performance_warnings': 0
        }
        
        # Enhanced feature caching
        self.fuzzy_match_cache: Dict[str, Tuple[bool, float, float]] = {}  # key -> (match_found, confidence, timestamp)
        self.target_extraction_cache: Dict[str, Tuple[str, str, float, float]] = {}  # command -> (target, action_type, confidence, timestamp)
        self.cache_ttl_seconds = 300  # 5 minutes cache TTL
        self.max_cache_entries = 1000  # Maximum cache entries per type
        self.cache_cleanup_interval = 60  # Cleanup every 60 seconds
        self.last_cache_cleanup = time.time()
        
        try:
            self._initialize_accessibility_api()
        except AccessibilityPermissionError as e:
            self.logger.warning(f"Accessibility permissions not granted: {e}")
            self._enter_degraded_mode("permission_denied", str(e))
        except AccessibilityAPIUnavailableError as e:
            self.logger.error(f"Accessibility API unavailable: {e}")
            self._enter_degraded_mode("api_unavailable", str(e))
        except Exception as e:
            self.logger.error(f"Unexpected error initializing AccessibilityModule: {e}")
            self._enter_degraded_mode("initialization_failed", str(e))
    
    def _initialize_accessibility_api(self):
        """Initialize the accessibility API and check permissions."""
        if not ACCESSIBILITY_AVAILABLE:
            raise AccessibilityAPIUnavailableError(
                "Accessibility frameworks not installed",
                "Install required frameworks: pip install pyobjc-framework-AppKit pyobjc-framework-Accessibility"
            )
        
        try:
            # Initialize NSWorkspace for application management
            self.workspace = NSWorkspace.sharedWorkspace()
            if self.workspace is None:
                raise AccessibilityAPIUnavailableError("Cannot initialize NSWorkspace")
            
            # Test accessibility permissions by trying to get system-wide element
            system_wide = None
            if ACCESSIBILITY_FUNCTIONS_AVAILABLE:
                system_wide = AXUIElementCreateSystemWide()
            if system_wide is None:
                raise AccessibilityPermissionError(
                    "Cannot create system-wide accessibility element - permissions required"
                )
            
            # Try to get the focused application to test permissions
            focused_app = self._get_focused_application_element()
            if focused_app is None:
                self.logger.warning("Cannot access focused application - accessibility permissions may be limited")
                # Don't fail initialization, but note limited functionality
            
            self.accessibility_enabled = True
            self.degraded_mode = False
            self.error_count = 0
            self.recovery_attempts = 0
            self.logger.info("AccessibilityModule initialized successfully")
            
        except AccessibilityPermissionError:
            raise  # Re-raise permission errors as-is
        except Exception as e:
            self.logger.error(f"Accessibility API initialization error: {e}")
            raise AccessibilityAPIUnavailableError(f"Failed to initialize accessibility API: {e}")
    
    def _enter_degraded_mode(self, reason: str, error_message: str):
        """Enter degraded mode when accessibility API is not fully functional."""
        self.degraded_mode = True
        self.accessibility_enabled = False
        self.last_error_time = time.time()
        
        self.logger.warning(f"AccessibilityModule entering degraded mode: {reason}")
        self.logger.debug(f"Degraded mode details: {error_message}")
    
    def _attempt_recovery(self) -> bool:
        """Attempt to recover from accessibility errors."""
        if self.recovery_attempts >= self.max_recovery_attempts:
            self.logger.warning("Maximum recovery attempts reached, staying in degraded mode")
            return False
        
        self.recovery_attempts += 1
        delay = self.retry_delay * (self.backoff_multiplier ** (self.recovery_attempts - 1))
        
        self.logger.info(f"Attempting accessibility recovery (attempt {self.recovery_attempts}/{self.max_recovery_attempts})")
        
        try:
            time.sleep(delay)
            self._initialize_accessibility_api()
            self.logger.info("Accessibility recovery successful")
            return True
            
        except Exception as e:
            self.logger.warning(f"Recovery attempt {self.recovery_attempts} failed: {e}")
            return False
    
    def _should_attempt_recovery(self) -> bool:
        """Determine if recovery should be attempted based on current state."""
        if not self.degraded_mode:
            return False
        
        if self.recovery_attempts >= self.max_recovery_attempts:
            return False
        
        # Only attempt recovery if enough time has passed since last error
        if self.last_error_time and (time.time() - self.last_error_time) < self.permission_check_interval:
            return False
        
        return True
    
    def _handle_fuzzy_matching_error(self, error: Exception, target_text: str, element_text: str) -> Tuple[bool, float]:
        """
        Handle fuzzy matching errors with graceful degradation.
        
        Args:
            error: The original exception
            target_text: Text being matched against
            element_text: Element text being compared
            
        Returns:
            Tuple of (fallback_success, confidence_score)
        """
        self.logger.warning(f"Fuzzy matching failed, falling back to exact match: {error}")
        
        try:
            # Fall back to exact string matching
            exact_match = target_text.lower().strip() == element_text.lower().strip()
            confidence = 100.0 if exact_match else 0.0
            
            if exact_match:
                self.logger.debug(f"Exact match fallback successful: '{target_text}' == '{element_text}'")
            
            return exact_match, confidence
            
        except Exception as fallback_error:
            self.logger.error(f"Even exact match fallback failed: {fallback_error}")
            return False, 0.0
    
    def _handle_attribute_access_error(self, error: Exception, attribute: str, element_info: Dict[str, Any]) -> Optional[str]:
        """
        Handle attribute access errors with graceful degradation.
        
        Args:
            error: The original exception
            attribute: Attribute that failed to access
            element_info: Element information for context
            
        Returns:
            Fallback attribute value or None if no fallback available
        """
        self.logger.debug(f"Attribute access failed for {attribute}: {error}")
        
        try:
            # Try alternative attribute access methods
            if hasattr(element_info, 'get'):
                fallback_value = element_info.get(attribute)
                if fallback_value:
                    self.logger.debug(f"Retrieved {attribute} via dict access: {fallback_value}")
                    return str(fallback_value)
            
            # Try common attribute aliases
            attribute_aliases = {
                'AXTitle': ['title', 'name', 'label'],
                'AXDescription': ['description', 'help', 'tooltip'],
                'AXValue': ['value', 'text', 'content']
            }
            
            if attribute in attribute_aliases:
                for alias in attribute_aliases[attribute]:
                    try:
                        if hasattr(element_info, 'get'):
                            alias_value = element_info.get(alias)
                            if alias_value:
                                self.logger.debug(f"Retrieved {attribute} via alias {alias}: {alias_value}")
                                return str(alias_value)
                    except Exception:
                        continue
            
            return None
            
        except Exception as fallback_error:
            self.logger.error(f"Attribute access fallback failed: {fallback_error}")
            return None
    
    def _handle_target_extraction_error(self, error: Exception, command: str) -> str:
        """
        Handle target extraction errors with graceful degradation.
        
        Args:
            error: The original exception
            command: Original command that failed to parse
            
        Returns:
            Fallback target text (usually the full command)
        """
        self.logger.warning(f"Target extraction failed, using full command: {error}")
        
        try:
            # Simple fallback: remove common action words manually
            fallback_target = command.lower()
            
            # Remove common action words
            action_words = ['click', 'press', 'type', 'select', 'choose', 'tap']
            for word in action_words:
                fallback_target = fallback_target.replace(word, '').strip()
            
            # Remove common articles
            articles = ['the', 'a', 'an', 'on', 'in', 'at']
            words = fallback_target.split()
            filtered_words = [w for w in words if w not in articles]
            
            if filtered_words:
                result = ' '.join(filtered_words).strip()
                self.logger.debug(f"Fallback target extraction: '{command}' -> '{result}'")
                return result
            else:
                # If nothing left, return original command
                return command
                
        except Exception as fallback_error:
            self.logger.error(f"Target extraction fallback failed: {fallback_error}")
            return command
    
    def _validate_configuration_with_fallback(self) -> Dict[str, Any]:
        """
        Validate configuration parameters and provide fallback values for invalid settings.
        
        Returns:
            Dictionary of validated configuration values
        """
        config = {}
        
        try:
            # Import configuration with error handling
            try:
                from config import (
                    FUZZY_MATCHING_ENABLED, FUZZY_CONFIDENCE_THRESHOLD, FUZZY_MATCHING_TIMEOUT,
                    CLICKABLE_ROLES, ACCESSIBILITY_ATTRIBUTES, FAST_PATH_TIMEOUT,
                    ATTRIBUTE_CHECK_TIMEOUT, ACCESSIBILITY_DEBUG_LOGGING, LOG_FUZZY_MATCH_SCORES
                )
                
                # Validate fuzzy matching settings
                config['fuzzy_matching_enabled'] = bool(FUZZY_MATCHING_ENABLED) if isinstance(FUZZY_MATCHING_ENABLED, bool) else True
                
                if isinstance(FUZZY_CONFIDENCE_THRESHOLD, (int, float)) and 0 <= FUZZY_CONFIDENCE_THRESHOLD <= 100:
                    config['fuzzy_confidence_threshold'] = float(FUZZY_CONFIDENCE_THRESHOLD)
                else:
                    config['fuzzy_confidence_threshold'] = 85.0
                    self.logger.warning(f"Invalid FUZZY_CONFIDENCE_THRESHOLD, using default: 85.0")
                
                if isinstance(FUZZY_MATCHING_TIMEOUT, (int, float)) and FUZZY_MATCHING_TIMEOUT > 0:
                    config['fuzzy_matching_timeout_ms'] = float(FUZZY_MATCHING_TIMEOUT)
                else:
                    config['fuzzy_matching_timeout_ms'] = 200.0
                    self.logger.warning(f"Invalid FUZZY_MATCHING_TIMEOUT, using default: 200ms")
                
                # Validate clickable roles
                if isinstance(CLICKABLE_ROLES, list) and CLICKABLE_ROLES:
                    config['clickable_roles'] = list(CLICKABLE_ROLES)
                else:
                    config['clickable_roles'] = ["AXButton", "AXLink", "AXMenuItem", "AXCheckBox", "AXRadioButton"]
                    self.logger.warning("Invalid CLICKABLE_ROLES, using defaults")
                
                # Validate accessibility attributes
                if isinstance(ACCESSIBILITY_ATTRIBUTES, list) and ACCESSIBILITY_ATTRIBUTES:
                    config['accessibility_attributes'] = list(ACCESSIBILITY_ATTRIBUTES)
                else:
                    config['accessibility_attributes'] = ["AXTitle", "AXDescription", "AXValue"]
                    self.logger.warning("Invalid ACCESSIBILITY_ATTRIBUTES, using defaults")
                
                # Validate timeout settings
                if isinstance(FAST_PATH_TIMEOUT, (int, float)) and FAST_PATH_TIMEOUT > 0:
                    config['fast_path_timeout_ms'] = float(FAST_PATH_TIMEOUT)
                else:
                    config['fast_path_timeout_ms'] = 2000.0
                    self.logger.warning("Invalid FAST_PATH_TIMEOUT, using default: 2000ms")
                
                if isinstance(ATTRIBUTE_CHECK_TIMEOUT, (int, float)) and ATTRIBUTE_CHECK_TIMEOUT > 0:
                    config['attribute_check_timeout_ms'] = float(ATTRIBUTE_CHECK_TIMEOUT)
                else:
                    config['attribute_check_timeout_ms'] = 500.0
                    self.logger.warning("Invalid ATTRIBUTE_CHECK_TIMEOUT, using default: 500ms")
                
                # Validate logging settings
                config['debug_logging'] = bool(ACCESSIBILITY_DEBUG_LOGGING) if isinstance(ACCESSIBILITY_DEBUG_LOGGING, bool) else False
                config['log_fuzzy_match_scores'] = bool(LOG_FUZZY_MATCH_SCORES) if isinstance(LOG_FUZZY_MATCH_SCORES, bool) else False
                
            except ImportError as e:
                self.logger.warning(f"Could not import configuration, using defaults: {e}")
                config = self._get_default_configuration()
                
        except Exception as e:
            self.logger.error(f"Configuration validation failed, using defaults: {e}")
            config = self._get_default_configuration()
        
        return config
    
    def _get_default_configuration(self) -> Dict[str, Any]:
        """Get default configuration values when config import fails."""
        return {
            'fuzzy_matching_enabled': True,
            'fuzzy_confidence_threshold': 85.0,
            'fuzzy_matching_timeout_ms': 200.0,
            'clickable_roles': ["AXButton", "AXLink", "AXMenuItem", "AXCheckBox", "AXRadioButton"],
            'accessibility_attributes': ["AXTitle", "AXDescription", "AXValue"],
            'fast_path_timeout_ms': 2000.0,
            'attribute_check_timeout_ms': 500.0,
            'debug_logging': False,
            'log_fuzzy_match_scores': False
        }
    
    def _check_fuzzy_matching_availability(self) -> bool:
        """
        Check if fuzzy matching is available and handle graceful degradation.
        
        Returns:
            True if fuzzy matching is available, False if degraded to exact matching
        """
        if not FUZZY_MATCHING_AVAILABLE:
            if not hasattr(self, '_fuzzy_warning_logged'):
                self.logger.warning(
                    "Fuzzy matching library not available. Install with: pip install thefuzz[speedup]. "
                    "Falling back to exact string matching."
                )
                self._fuzzy_warning_logged = True
            return False
        
        return True
    
    def _safe_fuzzy_match(self, target_text: str, element_text: str, threshold: float = 85.0) -> Tuple[bool, float]:
        """
        Perform fuzzy matching with error handling and fallback.
        
        Args:
            target_text: Text to match against
            element_text: Element text to compare
            threshold: Minimum confidence threshold
            
        Returns:
            Tuple of (match_found, confidence_score)
        """
        try:
            if not self._check_fuzzy_matching_availability():
                # Fall back to exact matching
                return self._handle_fuzzy_matching_error(
                    Exception("Fuzzy matching library not available"), 
                    target_text, element_text
                )
            
            # Perform fuzzy matching with timeout
            start_time = time.time()
            
            try:
                confidence = fuzz.partial_ratio(target_text.lower(), element_text.lower())
                
                # Check for timeout
                elapsed_ms = (time.time() - start_time) * 1000
                if elapsed_ms > self.fuzzy_matching_timeout_ms:
                    raise AccessibilityTimeoutError(f"Fuzzy matching timeout after {elapsed_ms:.1f}ms")
                
                match_found = confidence >= threshold
                
                if self.performance_monitoring_enabled and hasattr(self, 'logger'):
                    self.logger.debug(f"Fuzzy match: '{target_text}' vs '{element_text}' = {confidence:.1f}% (threshold: {threshold}%)")
                
                return match_found, float(confidence)
                
            except Exception as fuzzy_error:
                # Fall back to exact matching
                return self._handle_fuzzy_matching_error(fuzzy_error, target_text, element_text)
                
        except Exception as e:
            self.logger.error(f"Safe fuzzy match failed: {e}")
            return False, 0.0
    
    # Element Caching System Methods
    
    def _get_cache_key(self, app_name: str, app_pid: int) -> str:
        """Generate cache key for application."""
        return f"{app_name}:{app_pid}"
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid."""
        with self.cache_lock:
            if cache_key not in self.element_cache:
                return False
            
            cached_tree = self.element_cache[cache_key]
            if cached_tree.is_expired():
                self.logger.debug(f"Cache expired for {cache_key}, age: {cached_tree.get_age():.2f}s")
                self.cache_stats['expirations'] += 1
                del self.element_cache[cache_key]
                if cache_key in self.element_indexes:
                    del self.element_indexes[cache_key]
                return False
            
            return True
    
    def _get_cached_elements(self, app_name: str, app_pid: int) -> Optional[List[Dict[str, Any]]]:
        """Retrieve cached elements for an application."""
        cache_key = self._get_cache_key(app_name, app_pid)
        
        with self.cache_lock:
            self.cache_stats['total_lookups'] += 1
            
            if self._is_cache_valid(cache_key):
                self.cache_stats['hits'] += 1
                cached_tree = self.element_cache[cache_key]
                self.logger.debug(f"Cache hit for {app_name} (age: {cached_tree.get_age():.2f}s)")
                return cached_tree.elements.copy()
            
            self.cache_stats['misses'] += 1
            self.logger.debug(f"Cache miss for {app_name}")
            return None
    
    def _cache_elements(self, app_name: str, app_pid: int, elements: List[Dict[str, Any]]):
        """Cache elements for an application with TTL."""
        cache_key = self._get_cache_key(app_name, app_pid)
        
        with self.cache_lock:
            # Enforce cache size limit
            if len(self.element_cache) >= self.max_cache_size:
                self._evict_oldest_cache_entry()
            
            # Create cached tree
            cached_tree = CachedElementTree(
                app_name=app_name,
                app_pid=app_pid,
                elements=elements.copy(),
                timestamp=time.time(),
                ttl=self.cache_ttl
            )
            
            self.element_cache[cache_key] = cached_tree
            
            # Build index for fast lookup
            self._build_element_index(cache_key, elements)
            
            self.logger.debug(f"Cached {len(elements)} elements for {app_name}")
    
    def _evict_oldest_cache_entry(self):
        """Remove the oldest cache entry to make room for new ones."""
        if not self.element_cache:
            return
        
        oldest_key = min(self.element_cache.keys(), 
                        key=lambda k: self.element_cache[k].timestamp)
        
        self.logger.debug(f"Evicting oldest cache entry: {oldest_key}")
        del self.element_cache[oldest_key]
        if oldest_key in self.element_indexes:
            del self.element_indexes[oldest_key]
    
    def _build_element_index(self, cache_key: str, elements: List[Dict[str, Any]]):
        """Build indexes for fast element lookup by role and title."""
        index = ElementIndex()
        
        for element_info in elements:
            role = element_info.get('role', '')
            title = element_info.get('title', '')
            
            # Index by role
            if role:
                index.role_index[role].append(element_info)
                # Also index by role category
                category = self.classify_element_role(role)
                if category != 'unknown':
                    index.role_index[category].append(element_info)
            
            # Index by title
            if title:
                index.title_index[title].append(element_info)
                # Index by normalized title for fuzzy matching
                normalized_title = self._normalize_text(title)
                if normalized_title:
                    index.normalized_title_index[normalized_title].append(element_info)
        
        self.element_indexes[cache_key] = index
        self.logger.debug(f"Built index for {cache_key}: {len(index.role_index)} roles, {len(index.title_index)} titles")
    
    def _search_cached_elements(self, app_name: str, app_pid: int, role: str, label: str) -> List[Dict[str, Any]]:
        """Search cached elements using indexes for fast lookup."""
        cache_key = self._get_cache_key(app_name, app_pid)
        
        with self.cache_lock:
            if cache_key not in self.element_indexes:
                return []
            
            index = self.element_indexes[cache_key]
            candidates = set()
            
            # Search by role
            if role:
                role_matches = index.role_index.get(role, [])
                candidates.update(id(elem) for elem in role_matches)
                
                # Also search by role category
                category_matches = index.role_index.get(role.lower(), [])
                candidates.update(id(elem) for elem in category_matches)
            
            # Search by exact title match
            if label:
                title_matches = index.title_index.get(label, [])
                if role:
                    # Intersect with role matches
                    title_ids = {id(elem) for elem in title_matches}
                    candidates = candidates.intersection(title_ids)
                else:
                    candidates.update(id(elem) for elem in title_matches)
                
                # Search by normalized title for fuzzy matching
                normalized_label = self._normalize_text(label)
                if normalized_label:
                    normalized_matches = index.normalized_title_index.get(normalized_label, [])
                    if role:
                        normalized_ids = {id(elem) for elem in normalized_matches}
                        candidates = candidates.union(normalized_ids)
                    else:
                        candidates.update(id(elem) for elem in normalized_matches)
            
            # Convert back to element objects
            all_elements = []
            for elements_list in [index.role_index.get(role, []), 
                                index.title_index.get(label, []),
                                index.normalized_title_index.get(self._normalize_text(label), [])]:
                all_elements.extend(elements_list)
            
            # Filter to only candidates and remove duplicates
            result = []
            seen_ids = set()
            for elem in all_elements:
                elem_id = id(elem)
                if elem_id in candidates and elem_id not in seen_ids:
                    result.append(elem)
                    seen_ids.add(elem_id)
            
            return result
    
    def invalidate_cache_for_app(self, app_name: str, app_pid: Optional[int] = None):
        """Invalidate cache for a specific application."""
        with self.cache_lock:
            keys_to_remove = []
            
            if app_pid is not None:
                # Remove specific app by name and PID
                cache_key = self._get_cache_key(app_name, app_pid)
                if cache_key in self.element_cache:
                    keys_to_remove.append(cache_key)
            else:
                # Remove all entries for app name (any PID)
                for cache_key in self.element_cache:
                    if self.element_cache[cache_key].app_name == app_name:
                        keys_to_remove.append(cache_key)
            
            for key in keys_to_remove:
                self.logger.debug(f"Invalidating cache for {key}")
                del self.element_cache[key]
                if key in self.element_indexes:
                    del self.element_indexes[key]
                self.cache_stats['invalidations'] += 1
    
    def invalidate_all_cache(self):
        """Clear all cached elements."""
        with self.cache_lock:
            cache_count = len(self.element_cache)
            self.element_cache.clear()
            self.element_indexes.clear()
            self.cache_stats['invalidations'] += cache_count
            self.logger.debug(f"Invalidated all cache ({cache_count} entries)")
    
    def _check_application_focus_change(self):
        """Check if application focus has changed and invalidate cache if needed."""
        try:
            current_app = self.get_active_application()
            if not current_app:
                return
            
            app_name = current_app.get('name')
            app_pid = current_app.get('pid')
            
            # Check if focus changed
            if (app_name != self.current_app_name or 
                app_pid != self.current_app_pid):
                
                self.logger.debug(f"Application focus changed: {self.current_app_name} -> {app_name}")
                
                # Update current app tracking
                self.current_app_name = app_name
                self.current_app_pid = app_pid
                
                # Optionally invalidate cache for previous app to save memory
                # (keeping cache for background apps can be useful for quick switching)
                
        except Exception as e:
            self.logger.debug(f"Error checking application focus: {e}")
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        with self.cache_lock:
            total_lookups = self.cache_stats['total_lookups']
            hit_rate = (self.cache_stats['hits'] / total_lookups * 100) if total_lookups > 0 else 0
            
            return {
                'cache_entries': len(self.element_cache),
                'total_lookups': total_lookups,
                'cache_hits': self.cache_stats['hits'],
                'cache_misses': self.cache_stats['misses'],
                'hit_rate_percent': round(hit_rate, 2),
                'invalidations': self.cache_stats['invalidations'],
                'expirations': self.cache_stats['expirations'],
                'cache_ttl_seconds': self.cache_ttl,
                'max_cache_size': self.max_cache_size,
                'current_app': self.current_app_name
            }
    
    def configure_cache(self, ttl: Optional[float] = None, max_size: Optional[int] = None):
        """Configure cache settings."""
        if ttl is not None:
            self.cache_ttl = ttl
            self.logger.info(f"Cache TTL set to {ttl} seconds")
        
        if max_size is not None:
            with self.cache_lock:
                self.max_cache_size = max_size
                # Evict entries if current size exceeds new limit
                while len(self.element_cache) > max_size:
                    self._evict_oldest_cache_entry()
            self.logger.info(f"Cache max size set to {max_size}")
    
    def clear_cache_statistics(self):
        """Reset cache statistics."""
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'invalidations': 0,
            'expirations': 0,
            'total_lookups': 0
        }
        self.logger.debug("Cache statistics cleared")
    
    # Performance Monitoring Methods
    
    @contextmanager
    def _performance_timer(self, operation_name: str, timeout_ms: Optional[float] = None, metadata: Optional[Dict[str, Any]] = None):
        """Context manager for timing operations with performance monitoring."""
        if not self.performance_monitoring_enabled:
            yield None
            return
        
        metrics = PerformanceMetrics(
            operation_name=operation_name,
            start_time=time.time(),
            timeout_ms=timeout_ms,
            metadata=metadata or {}
        )
        
        try:
            yield metrics
        except Exception as e:
            metrics.finish(success=False, error_message=str(e))
            self._record_performance_metrics(metrics)
            raise
        else:
            metrics.finish(success=True)
            self._record_performance_metrics(metrics)
    
    def _record_performance_metrics(self, metrics: PerformanceMetrics):
        """Record performance metrics and update statistics."""
        with self.performance_lock:
            # Add to history
            self.performance_metrics.append(metrics)
            
            # Maintain history size limit
            if len(self.performance_metrics) > self.max_performance_history:
                self.performance_metrics = self.performance_metrics[-self.max_performance_history:]
            
            # Update statistics
            self.performance_stats['total_operations'] += 1
            if metrics.success:
                self.performance_stats['successful_operations'] += 1
            
            if metrics.timed_out:
                self.performance_stats['timed_out_operations'] += 1
            
            if metrics.duration_ms is not None:
                # Update duration statistics
                self.performance_stats['fastest_operation_ms'] = min(
                    self.performance_stats['fastest_operation_ms'], 
                    metrics.duration_ms
                )
                self.performance_stats['slowest_operation_ms'] = max(
                    self.performance_stats['slowest_operation_ms'], 
                    metrics.duration_ms
                )
                
                # Calculate running average
                total_ops = self.performance_stats['total_operations']
                current_avg = self.performance_stats['average_duration_ms']
                self.performance_stats['average_duration_ms'] = (
                    (current_avg * (total_ops - 1) + metrics.duration_ms) / total_ops
                )
                
                # Check for performance warnings
                warning_triggered = False
                
                # Check timeout-based warnings
                if metrics.timeout_ms and metrics.duration_ms > metrics.timeout_ms:
                    self.performance_stats['performance_warnings'] += 1
                    self.logger.warning(
                        f"Performance warning: {metrics.operation_name} took {metrics.duration_ms:.1f}ms "
                        f"(timeout: {metrics.timeout_ms}ms)"
                    )
                    warning_triggered = True
                
                # Check general performance threshold warnings
                if (hasattr(self, 'performance_warning_threshold_ms') and 
                    metrics.duration_ms > self.performance_warning_threshold_ms):
                    if not warning_triggered:  # Don't double-count warnings
                        self.performance_stats['performance_warnings'] += 1
                    self.logger.warning(
                        f"Performance warning: {metrics.operation_name} took {metrics.duration_ms:.1f}ms "
                        f"(threshold: {self.performance_warning_threshold_ms}ms)"
                    )
        
        # Log performance details if debug logging is enabled
        if hasattr(self, 'accessibility_debug_logging') and self.accessibility_debug_logging:
            self.logger.debug(f"Performance: {metrics.to_dict()}")
    
    def get_performance_statistics(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics."""
        with self.performance_lock:
            stats = self.performance_stats.copy()
            
            # Add recent performance data
            recent_metrics = self.performance_metrics[-10:] if self.performance_metrics else []
            stats['recent_operations'] = [m.to_dict() for m in recent_metrics]
            
            # Calculate success rate
            total_ops = stats['total_operations']
            if total_ops > 0:
                stats['success_rate_percent'] = (stats['successful_operations'] / total_ops) * 100
                stats['timeout_rate_percent'] = (stats['timed_out_operations'] / total_ops) * 100
            else:
                stats['success_rate_percent'] = 0.0
                stats['timeout_rate_percent'] = 0.0
            
            # Fix infinite values for JSON serialization
            if stats['fastest_operation_ms'] == float('inf'):
                stats['fastest_operation_ms'] = 0.0
            
            return stats
    
    def clear_performance_statistics(self):
        """Reset performance statistics and metrics history."""
        with self.performance_lock:
            self.performance_metrics.clear()
            self.performance_stats = {
                'total_operations': 0,
                'successful_operations': 0,
                'timed_out_operations': 0,
                'average_duration_ms': 0.0,
                'fastest_operation_ms': float('inf'),
                'slowest_operation_ms': 0.0,
                'performance_warnings': 0
            }
        self.logger.debug("Performance statistics cleared")
    
    def configure_performance_monitoring(self, 
                                       enabled: Optional[bool] = None,
                                       fast_path_timeout_ms: Optional[float] = None,
                                       fuzzy_matching_timeout_ms: Optional[float] = None,
                                       attribute_check_timeout_ms: Optional[float] = None,
                                       max_history: Optional[int] = None):
        """Configure performance monitoring settings."""
        if enabled is not None:
            self.performance_monitoring_enabled = enabled
            self.logger.info(f"Performance monitoring {'enabled' if enabled else 'disabled'}")
        
        if fast_path_timeout_ms is not None:
            self.fast_path_timeout_ms = fast_path_timeout_ms
            self.logger.info(f"Fast path timeout set to {fast_path_timeout_ms}ms")
        
        if fuzzy_matching_timeout_ms is not None:
            self.fuzzy_matching_timeout_ms = fuzzy_matching_timeout_ms
            self.logger.info(f"Fuzzy matching timeout set to {fuzzy_matching_timeout_ms}ms")
        
        if attribute_check_timeout_ms is not None:
            self.attribute_check_timeout_ms = attribute_check_timeout_ms
            self.logger.info(f"Attribute check timeout set to {attribute_check_timeout_ms}ms")
        
        if max_history is not None:
            with self.performance_lock:
                self.max_performance_history = max_history
                # Trim existing history if needed
                if len(self.performance_metrics) > max_history:
                    self.performance_metrics = self.performance_metrics[-max_history:]
            self.logger.info(f"Performance history limit set to {max_history}")
    
    def _check_performance_thresholds(self, operation_name: str, duration_ms: float, threshold_ms: float) -> List[str]:
        """Check if operation duration exceeds performance thresholds and return warnings."""
        warnings = []
        
        if duration_ms > threshold_ms:
            warning_msg = f"{operation_name} exceeded threshold: {duration_ms:.1f}ms > {threshold_ms}ms"
            warnings.append(warning_msg)
            
            # Log performance warning
            self.logger.warning(f"Performance threshold exceeded: {warning_msg}")
        
        return warnings
    
    # Enhanced Feature Caching Methods
    
    def _generate_fuzzy_match_cache_key(self, element_text: str, target_text: str, confidence_threshold: int) -> str:
        """Generate cache key for fuzzy matching results."""
        # Normalize texts for consistent caching
        element_norm = self._normalize_text(element_text)
        target_norm = self._normalize_text(target_text)
        return f"{element_norm}|{target_norm}|{confidence_threshold}"
    
    def _get_cached_fuzzy_match(self, element_text: str, target_text: str, confidence_threshold: int) -> Optional[Tuple[bool, float]]:
        """Get cached fuzzy matching result if available and not expired."""
        cache_key = self._generate_fuzzy_match_cache_key(element_text, target_text, confidence_threshold)
        
        if cache_key in self.fuzzy_match_cache:
            match_found, confidence, timestamp = self.fuzzy_match_cache[cache_key]
            
            # Check if cache entry is still valid
            if time.time() - timestamp < self.cache_ttl_seconds:
                self.logger.debug(f"Fuzzy match cache hit: {cache_key}")
                return match_found, confidence
            else:
                # Remove expired entry
                del self.fuzzy_match_cache[cache_key]
                self.logger.debug(f"Fuzzy match cache expired: {cache_key}")
        
        return None
    
    def _cache_fuzzy_match_result(self, element_text: str, target_text: str, confidence_threshold: int, 
                                 match_found: bool, confidence: float):
        """Cache fuzzy matching result."""
        cache_key = self._generate_fuzzy_match_cache_key(element_text, target_text, confidence_threshold)
        
        # Enforce cache size limit
        if len(self.fuzzy_match_cache) >= self.max_cache_entries:
            self._cleanup_fuzzy_match_cache()
        
        self.fuzzy_match_cache[cache_key] = (match_found, confidence, time.time())
        self.logger.debug(f"Cached fuzzy match result: {cache_key} -> {match_found}, {confidence}")
    
    def _cleanup_fuzzy_match_cache(self):
        """Remove expired entries from fuzzy match cache."""
        current_time = time.time()
        expired_keys = []
        
        for cache_key, (match_found, confidence, timestamp) in self.fuzzy_match_cache.items():
            if current_time - timestamp >= self.cache_ttl_seconds:
                expired_keys.append(cache_key)
        
        for key in expired_keys:
            del self.fuzzy_match_cache[key]
        
        # If still too many entries, remove oldest ones
        if len(self.fuzzy_match_cache) >= self.max_cache_entries:
            # Sort by timestamp and keep only the newest entries
            sorted_items = sorted(self.fuzzy_match_cache.items(), 
                                key=lambda x: x[1][2], reverse=True)  # Sort by timestamp descending
            
            # Keep only the newest 80% of max entries
            keep_count = int(self.max_cache_entries * 0.8)
            self.fuzzy_match_cache = dict(sorted_items[:keep_count])
        
        self.logger.debug(f"Cleaned up fuzzy match cache, {len(expired_keys)} expired entries removed")
    
    def _generate_target_extraction_cache_key(self, command: str) -> str:
        """Generate cache key for target extraction results."""
        # Normalize command for consistent caching
        return self._normalize_text(command)
    
    def _get_cached_target_extraction(self, command: str) -> Optional[Tuple[str, str, float]]:
        """Get cached target extraction result if available and not expired."""
        cache_key = self._generate_target_extraction_cache_key(command)
        
        if cache_key in self.target_extraction_cache:
            target, action_type, confidence, timestamp = self.target_extraction_cache[cache_key]
            
            # Check if cache entry is still valid
            if time.time() - timestamp < self.cache_ttl_seconds:
                self.logger.debug(f"Target extraction cache hit: {cache_key}")
                return target, action_type, confidence
            else:
                # Remove expired entry
                del self.target_extraction_cache[cache_key]
                self.logger.debug(f"Target extraction cache expired: {cache_key}")
        
        return None
    
    def _cache_target_extraction_result(self, command: str, target: str, action_type: str, confidence: float):
        """Cache target extraction result."""
        cache_key = self._generate_target_extraction_cache_key(command)
        
        # Enforce cache size limit
        if len(self.target_extraction_cache) >= self.max_cache_entries:
            self._cleanup_target_extraction_cache()
        
        self.target_extraction_cache[cache_key] = (target, action_type, confidence, time.time())
        self.logger.debug(f"Cached target extraction result: {cache_key} -> {target}, {action_type}, {confidence}")
    
    def _cleanup_target_extraction_cache(self):
        """Remove expired entries from target extraction cache."""
        current_time = time.time()
        expired_keys = []
        
        for cache_key, (target, action_type, confidence, timestamp) in self.target_extraction_cache.items():
            if current_time - timestamp >= self.cache_ttl_seconds:
                expired_keys.append(cache_key)
        
        for key in expired_keys:
            del self.target_extraction_cache[key]
        
        # If still too many entries, remove oldest ones
        if len(self.target_extraction_cache) >= self.max_cache_entries:
            # Sort by timestamp and keep only the newest entries
            sorted_items = sorted(self.target_extraction_cache.items(), 
                                key=lambda x: x[1][3], reverse=True)  # Sort by timestamp descending
            
            # Keep only the newest 80% of max entries
            keep_count = int(self.max_cache_entries * 0.8)
            self.target_extraction_cache = dict(sorted_items[:keep_count])
        
        self.logger.debug(f"Cleaned up target extraction cache, {len(expired_keys)} expired entries removed")
    
    def _periodic_cache_cleanup(self):
        """Perform periodic cleanup of all caches."""
        current_time = time.time()
        
        if current_time - self.last_cache_cleanup > self.cache_cleanup_interval:
            self._cleanup_fuzzy_match_cache()
            self._cleanup_target_extraction_cache()
            self.last_cache_cleanup = current_time
            
            self.logger.debug("Performed periodic cache cleanup")
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics including enhanced feature caches."""
        base_stats = super().get_cache_statistics() if hasattr(super(), 'get_cache_statistics') else {}
        
        enhanced_stats = {
            'fuzzy_match_cache': {
                'entries': len(self.fuzzy_match_cache),
                'max_entries': self.max_cache_entries,
                'ttl_seconds': self.cache_ttl_seconds
            },
            'target_extraction_cache': {
                'entries': len(self.target_extraction_cache),
                'max_entries': self.max_cache_entries,
                'ttl_seconds': self.cache_ttl_seconds
            },
            'cache_cleanup': {
                'last_cleanup': self.last_cache_cleanup,
                'cleanup_interval': self.cache_cleanup_interval
            }
        }
        
        # Merge with base cache statistics
        if base_stats:
            base_stats['enhanced_caches'] = enhanced_stats
            return base_stats
        else:
            return {'enhanced_caches': enhanced_stats}
    
    def clear_enhanced_caches(self):
        """Clear all enhanced feature caches."""
        self.fuzzy_match_cache.clear()
        self.target_extraction_cache.clear()
        self.logger.debug("Cleared all enhanced feature caches")
    
    def configure_enhanced_caching(self, 
                                 ttl_seconds: Optional[int] = None,
                                 max_entries: Optional[int] = None,
                                 cleanup_interval: Optional[int] = None):
        """Configure enhanced feature caching settings."""
        if ttl_seconds is not None:
            self.cache_ttl_seconds = ttl_seconds
            self.logger.info(f"Enhanced cache TTL set to {ttl_seconds} seconds")
        
        if max_entries is not None:
            self.max_cache_entries = max_entries
            # Cleanup existing caches if they exceed new limit
            if len(self.fuzzy_match_cache) > max_entries:
                self._cleanup_fuzzy_match_cache()
            if len(self.target_extraction_cache) > max_entries:
                self._cleanup_target_extraction_cache()
            self.logger.info(f"Enhanced cache max entries set to {max_entries}")
        
        if cleanup_interval is not None:
            self.cache_cleanup_interval = cleanup_interval
            self.logger.info(f"Enhanced cache cleanup interval set to {cleanup_interval} seconds")
    
    def _handle_accessibility_error(self, error: Exception, operation: str) -> None:
        """Handle accessibility errors with appropriate recovery logic."""
        self.error_count += 1
        self.last_error_time = time.time()
        
        error_msg = f"Accessibility error in {operation}: {error}"
        self.logger.error(error_msg)
        
        # Determine if this is a recoverable error
        if isinstance(error, (AccessibilityPermissionError, AccessibilityAPIUnavailableError)):
            if not self.degraded_mode:
                self._enter_degraded_mode("api_error", str(error))
        
        # Log error details for diagnostics
        self.logger.debug(f"Error details - Count: {self.error_count}, Operation: {operation}, Type: {type(error).__name__}")
    
    def _with_error_recovery(self, operation_name: str):
        """Decorator for methods that should attempt error recovery."""
        def decorator(func):
            def wrapper(*args, **kwargs):
                # Attempt recovery if in degraded mode and conditions are met
                if self.degraded_mode and self._should_attempt_recovery():
                    if self._attempt_recovery():
                        self.logger.info(f"Recovery successful, retrying {operation_name}")
                
                # If still in degraded mode, return None or appropriate fallback
                if self.degraded_mode:
                    self.logger.debug(f"Skipping {operation_name} - in degraded mode")
                    return None
                
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    self._handle_accessibility_error(e, operation_name)
                    return None
            
            return wrapper
        return decorator
    
    def _get_focused_application_element(self):
        """Get the accessibility element for the currently focused application."""
        try:
            system_wide = None
            if ACCESSIBILITY_FUNCTIONS_AVAILABLE:
                system_wide = AXUIElementCreateSystemWide()
            focused_app_ref = AXUIElementCopyAttributeValue(
                system_wide, 
                kAXFocusedApplicationAttribute, 
                None
            )
            return focused_app_ref[1] if focused_app_ref[0] == 0 else None
        except Exception as e:
            self.logger.debug(f"Could not get focused application: {e}")
            return None
    
    def get_active_application(self) -> Optional[Dict[str, Any]]:
        """
        Get information about the currently active application.
        
        Returns:
            Dictionary with application details or None if not accessible:
            {
                'name': 'Safari',
                'bundle_id': 'com.apple.Safari',
                'pid': 1234,
                'accessible': True
            }
        """
        if not self.accessibility_enabled:
            return None
        
        try:
            # Get the frontmost application
            frontmost_app = self.workspace.frontmostApplication()
            if not frontmost_app:
                return None
            
            app_info = {
                'name': frontmost_app.localizedName(),
                'bundle_id': frontmost_app.bundleIdentifier(),
                'pid': frontmost_app.processIdentifier(),
                'accessible': False
            }
            
            # Test if the application is accessible
            focused_app_element = self._get_focused_application_element()
            if focused_app_element:
                app_info['accessible'] = True
            
            self.logger.debug(f"Active application: {app_info}")
            return app_info
            
        except Exception as e:
            self._handle_accessibility_error(e, "get_active_application")
            return None
    
    def is_accessibility_enabled(self) -> bool:
        """Check if accessibility API is enabled and functional."""
        return self.accessibility_enabled
    
    def get_accessibility_status(self) -> Dict[str, Any]:
        """
        Get detailed status of accessibility API availability.
        
        Returns:
            Dictionary with comprehensive status information
        """
        status = {
            'frameworks_available': ACCESSIBILITY_AVAILABLE,
            'api_initialized': self.accessibility_enabled,
            'workspace_available': self.workspace is not None,
            'permissions_granted': False,
            'degraded_mode': self.degraded_mode,
            'error_count': self.error_count,
            'recovery_attempts': self.recovery_attempts,
            'last_error_time': self.last_error_time,
            'can_attempt_recovery': self._should_attempt_recovery()
        }
        
        if self.accessibility_enabled:
            # Test permissions by trying to access focused app
            try:
                focused_app = self._get_focused_application_element()
                status['permissions_granted'] = focused_app is not None
            except Exception as e:
                status['permissions_granted'] = False
                status['permission_test_error'] = str(e)
        
        return status
    
    def get_error_diagnostics(self) -> Dict[str, Any]:
        """
        Get detailed error diagnostics for troubleshooting.
        
        Returns:
            Dictionary with diagnostic information
        """
        diagnostics = {
            'module_state': {
                'accessibility_enabled': self.accessibility_enabled,
                'degraded_mode': self.degraded_mode,
                'error_count': self.error_count,
                'recovery_attempts': self.recovery_attempts,
                'max_recovery_attempts': self.max_recovery_attempts,
                'last_error_time': self.last_error_time
            },
            'system_state': {
                'frameworks_available': ACCESSIBILITY_AVAILABLE,
                'workspace_initialized': self.workspace is not None
            },
            'recovery_state': {
                'can_attempt_recovery': self._should_attempt_recovery(),
                'next_retry_delay': self.retry_delay * (self.backoff_multiplier ** self.recovery_attempts),
                'time_since_last_error': time.time() - self.last_error_time if self.last_error_time else None
            }
        }
        
        # Test current accessibility state
        try:
            if self.workspace:
                app = self.workspace.frontmostApplication()
                diagnostics['current_app'] = {
                    'name': app.localizedName() if app else None,
                    'accessible': False
                }
                
                if app:
                    try:
                        focused_element = self._get_focused_application_element()
                        diagnostics['current_app']['accessible'] = focused_element is not None
                    except Exception as e:
                        diagnostics['current_app']['access_error'] = str(e)
        except Exception as e:
            diagnostics['app_test_error'] = str(e)
        
        return diagnostics
    
    def find_element_enhanced(self, role: str, label: str, app_name: Optional[str] = None) -> ElementMatchResult:
        """
        Enhanced element finding with multi-role detection and comprehensive result tracking.
        
        Args:
            role: Accessibility role (e.g., 'AXButton', 'AXMenuItem') or empty for broader search
            label: Element label or title
            app_name: Optional application name to limit search scope
        
        Returns:
            ElementMatchResult with detailed matching metadata
        """
        with self._performance_timer(
            "find_element_enhanced", 
            timeout_ms=self.fast_path_timeout_ms,
            metadata={'role': role, 'label': label, 'app_name': app_name}
        ) as perf_metrics:
            
            start_time = time.time()
            roles_checked = []
            attributes_checked = []
            fuzzy_matches = []
            fallback_triggered = False
        
        # Check if enhanced features are available
        if not self.is_enhanced_role_detection_available():
            self.logger.info("Enhanced role detection not available, falling back to original implementation")
            fallback_triggered = True
            
            # Try original fallback and wrap result
            original_result = self._find_element_original_fallback(role, label, app_name)
            search_time_ms = (time.time() - start_time) * 1000
            
            if original_result:
                roles_checked = [role] if role else ['AXButton']
                attributes_checked = ['AXTitle']  # Original implementation typically checks AXTitle
                
                return ElementMatchResult(
                    element=original_result,
                    found=True,
                    confidence_score=100.0,  # Original exact match
                    matched_attribute='AXTitle',
                    search_time_ms=search_time_ms,
                    roles_checked=roles_checked,
                    attributes_checked=attributes_checked,
                    fuzzy_matches=[],
                    fallback_triggered=fallback_triggered
                )
            else:
                return ElementMatchResult(
                    element=None,
                    found=False,
                    confidence_score=0.0,
                    matched_attribute='',
                    search_time_ms=search_time_ms,
                    roles_checked=roles_checked,
                    attributes_checked=attributes_checked,
                    fuzzy_matches=[],
                    fallback_triggered=fallback_triggered
                )
        
        try:
            # First attempt: Enhanced role detection with detailed tracking and error handling
            try:
                result, match_details = self._find_element_with_enhanced_roles_tracked(role, label, app_name)
                
                if result:
                    search_time_ms = (time.time() - start_time) * 1000
                    if self.debug_logging:
                        self.logger.debug(f"Enhanced role detection succeeded for {role} '{label}' in {search_time_ms:.1f}ms")
                    
                    return ElementMatchResult(
                        element=result,
                        found=True,
                        confidence_score=match_details.get('confidence_score', 100.0),
                        matched_attribute=match_details.get('matched_attribute', 'AXTitle'),
                        search_time_ms=search_time_ms,
                        roles_checked=match_details.get('roles_checked', [role] if role else []),
                        attributes_checked=match_details.get('attributes_checked', []),
                        fuzzy_matches=match_details.get('fuzzy_matches', []),
                        fallback_triggered=False
                    )
            
            except EnhancedFastPathError as fast_path_error:
                # Handle enhanced fast path specific errors
                self.logger.warning(f"Enhanced fast path error: {fast_path_error}")
                if not fast_path_error.fallback_available:
                    # If no fallback is available, return failure immediately
                    search_time_ms = (time.time() - start_time) * 1000
                    return ElementMatchResult(
                        element=None,
                        found=False,
                        confidence_score=0.0,
                        matched_attribute='',
                        search_time_ms=search_time_ms,
                        roles_checked=[role] if role else [],
                        attributes_checked=[],
                        fuzzy_matches=[],
                        fallback_triggered=True
                    )
                # Continue to fallback logic below
            
            except (FuzzyMatchingError, AttributeAccessError, TargetExtractionError) as specific_error:
                # Handle specific enhanced feature errors with appropriate fallbacks
                self.logger.debug(f"Enhanced feature error, continuing with fallback: {specific_error}")
                # Continue to fallback logic below
            
            except AccessibilityTimeoutError as timeout_error:
                # Handle timeout errors
                search_time_ms = (time.time() - start_time) * 1000
                self.logger.warning(f"Enhanced element detection timed out after {search_time_ms:.1f}ms: {timeout_error}")
                fallback_triggered = True
                # Continue to fallback logic below
            
            # Fallback: Original button-only detection for backward compatibility
            if not role or role.lower() in ['button', 'clickable']:
                if self.debug_logging:
                    self.logger.debug(f"Falling back to button-only detection for '{label}'")
                fallback_triggered = True
                
                try:
                    button_result = self._find_element_button_only_fallback(label, app_name)
                    search_time_ms = (time.time() - start_time) * 1000
                    
                    if button_result:
                        if self.debug_logging:
                            self.logger.debug(f"Button-only fallback succeeded for '{label}' in {search_time_ms:.1f}ms")
                        roles_checked = ['AXButton']
                        attributes_checked = ['AXTitle']
                        
                        return ElementMatchResult(
                            element=button_result,
                            found=True,
                            confidence_score=100.0,  # Exact match in fallback
                            matched_attribute='AXTitle',
                            search_time_ms=search_time_ms,
                            roles_checked=roles_checked,
                            attributes_checked=attributes_checked,
                            fuzzy_matches=[],
                            fallback_triggered=fallback_triggered
                        )
                
                except Exception as fallback_error:
                    self.logger.debug(f"Button-only fallback failed: {fallback_error}")
                    # Continue to final fallback
            
            # No element found
            search_time_ms = (time.time() - start_time) * 1000
            if self.debug_logging:
                self.logger.debug(f"Element not found for {role} '{label}' after {search_time_ms:.1f}ms")
            
            return ElementMatchResult(
                element=None,
                found=False,
                confidence_score=0.0,
                matched_attribute='',
                search_time_ms=search_time_ms,
                roles_checked=match_details.get('roles_checked', [role] if role else []) if 'match_details' in locals() else [],
                attributes_checked=match_details.get('attributes_checked', []) if 'match_details' in locals() else [],
                fuzzy_matches=match_details.get('fuzzy_matches', []) if 'match_details' in locals() else [],
                fallback_triggered=fallback_triggered
            )
            
        except Exception as e:
            search_time_ms = (time.time() - start_time) * 1000
            self.logger.warning(f"Enhanced element detection failed after {search_time_ms:.1f}ms: {e}")
            
            # Final fallback to original method with error context logging
            fallback_triggered = True
            
            try:
                original_result = self._find_element_original_fallback(role, label, app_name)
                
                if original_result:
                    self.logger.info(f"Original fallback succeeded after enhanced detection failure")
                    return ElementMatchResult(
                        element=original_result,
                        found=True,
                        confidence_score=100.0,
                        matched_attribute='AXTitle',
                        search_time_ms=search_time_ms,
                        roles_checked=[role] if role else ['AXButton'],
                        attributes_checked=['AXTitle'],
                        fuzzy_matches=[],
                        fallback_triggered=fallback_triggered
                    )
                else:
                    self.logger.debug(f"Original fallback also failed for {role} '{label}'")
                    return ElementMatchResult(
                        element=None,
                        found=False,
                        confidence_score=0.0,
                        matched_attribute='',
                        search_time_ms=search_time_ms,
                        roles_checked=[role] if role else [],
                        attributes_checked=[],
                        fuzzy_matches=[],
                        fallback_triggered=fallback_triggered
                    )
            
            except Exception as final_error:
                self.logger.error(f"Final fallback also failed: {final_error}")
                return ElementMatchResult(
                    element=None,
                    found=False,
                    confidence_score=0.0,
                    matched_attribute='',
                    search_time_ms=search_time_ms,
                    roles_checked=[],
                    attributes_checked=[],
                    fuzzy_matches=[],
                    fallback_triggered=fallback_triggered
                )
    
    def find_element(self, role: str, label: str, app_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Find UI element by role and label with enhanced role detection and backward compatibility.
        
        Args:
            role: Accessibility role (e.g., 'AXButton', 'AXMenuItem') or empty for broader search
            label: Element label or title
            app_name: Optional application name to limit search scope
        
        Returns:
            Dictionary with element details or None if not found:
            {
                'coordinates': [x, y, width, height],
                'center_point': [center_x, center_y],
                'role': 'AXButton',
                'title': 'Sign In',
                'enabled': True,
                'app_name': 'Safari'
            }
        """
        # Use enhanced element detection by default
        try:
            enhanced_result = self.find_element_enhanced(role, label, app_name)
            
            # Log detailed results for debugging
            if enhanced_result.found:
                self.logger.debug(f"Element found - Confidence: {enhanced_result.confidence_score:.1f}%, "
                                f"Attribute: {enhanced_result.matched_attribute}, "
                                f"Time: {enhanced_result.search_time_ms:.1f}ms, "
                                f"Roles checked: {len(enhanced_result.roles_checked)}, "
                                f"Fallback: {enhanced_result.fallback_triggered}")
            else:
                self.logger.debug(f"Element not found - Time: {enhanced_result.search_time_ms:.1f}ms, "
                                f"Roles checked: {enhanced_result.roles_checked}, "
                                f"Attributes checked: {enhanced_result.attributes_checked}")
            
            # Return the element dict for backward compatibility
            return enhanced_result.element
            
        except Exception as e:
            self.logger.debug(f"Enhanced element detection failed, using original logic: {e}")
        
        # Fallback to original implementation logic for maximum backward compatibility
        return self._find_element_original_implementation(role, label, app_name)
    
    def _find_element_original_implementation(self, role: str, label: str, app_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Original find_element implementation for backward compatibility.
        
        This preserves the exact original behavior when enhanced detection fails.
        """
        self.logger.debug("Using original implementation for backward compatibility")
        
        # For backward compatibility, default to AXButton if no role specified
        if not role:
            role = 'AXButton'
        
        # Use the existing logic but with original element matching criteria
        try:
            # Check for application focus changes
            self._check_application_focus_change()
            
            # Attempt recovery if in degraded mode
            if self.degraded_mode and self._should_attempt_recovery():
                if self._attempt_recovery():
                    self.logger.info("Recovery successful, retrying find_element")
            
            # If still in degraded mode, return None
            if self.degraded_mode:
                self.logger.debug("Skipping find_element - in degraded mode")
                return None
            
            if not self.accessibility_enabled:
                return None
            
            # Get the target application info
            if app_name:
                # Find specific application
                running_apps = self.workspace.runningApplications()
                target_app = None
                for app in running_apps:
                    if app.localizedName() == app_name:
                        target_app = app
                        break
                
                if not target_app:
                    self.logger.debug(f"Application '{app_name}' not found")
                    return None

                app_pid = target_app.processIdentifier()
                actual_app_name = app_name
            else:
                # Use focused application
                current_app = self.get_active_application()
                if not current_app:
                    self.logger.debug("No active application found")
                    return None
                
                app_pid = current_app['pid']
                actual_app_name = current_app['name']
            
            # Get the target application element
            app_element = self._get_target_application_element(app_name)
            if not app_element:
                self.logger.debug(f"Cannot access application: {app_name or 'focused app'}")
                return None
            
            # Traverse the accessibility tree to find elements
            found_elements = self.traverse_accessibility_tree(app_element, max_depth=5)
            
            # Find matching elements using original strict criteria
            matching_elements = []
            for element_info in found_elements:
                element_role = element_info.get('role', '')
                element_title = element_info.get('title', '')
                
                # Original logic: exact role match and fuzzy label match
                if role == element_role and self.fuzzy_match_label(element_title, label):
                    if self.is_element_actionable(element_info) and self._is_element_visible(element_info):
                        matching_elements.append(element_info)
            
            # Find the best match if multiple elements found
            if matching_elements:
                best_match = self.find_best_matching_element(matching_elements, label)
                if best_match:
                    coordinates = self._calculate_element_coordinates(best_match['element'])
                    if coordinates:
                        return {
                            'coordinates': coordinates,
                            'center_point': [
                                coordinates[0] + coordinates[2] // 2,
                                coordinates[1] + coordinates[3] // 2
                            ],
                            'role': best_match.get('role', ''),
                            'title': best_match.get('title', ''),
                            'enabled': best_match.get('enabled', True),
                            'app_name': actual_app_name
                        }
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Original implementation failed: {e}")
            return None
        # Check for application focus changes
        self._check_application_focus_change()
        
        # Attempt recovery if in degraded mode
        if self.degraded_mode and self._should_attempt_recovery():
            if self._attempt_recovery():
                self.logger.info("Recovery successful, retrying find_element")
        
        # If still in degraded mode, return None
        if self.degraded_mode:
            self.logger.debug("Skipping find_element - in degraded mode")
            return None
        
        if not self.accessibility_enabled:
            return None
        
        try:
            # Get the target application info
            if app_name:
                # Find specific application
                running_apps = self.workspace.runningApplications()
                target_app = None
                for app in running_apps:
                    if app.localizedName() == app_name:
                        target_app = app
                        break
                
                if not target_app:
                    raise ElementNotFoundError(f"Application '{app_name}' not found")
                
                app_pid = target_app.processIdentifier()
                actual_app_name = app_name
            else:
                # Use focused application
                current_app = self.get_active_application()
                if not current_app:
                    raise ElementNotFoundError("No active application found")
                
                app_pid = current_app['pid']
                actual_app_name = current_app['name']
            
            # Try to get elements from cache first
            cached_elements = self._get_cached_elements(actual_app_name, app_pid)
            
            if cached_elements is not None:
                # Search in cached elements using indexes
                matching_elements = self._search_cached_elements(actual_app_name, app_pid, role, label)
                
                # Filter by actionability and visibility
                actionable_elements = self.filter_elements_by_criteria(
                    matching_elements, 
                    actionable_only=True, 
                    visible_only=True
                )
                
                # Find best match from cached results
                if actionable_elements:
                    for element_info in actionable_elements:
                        if self._element_matches_criteria(element_info, role, label):
                            best_match = element_info
                            try:
                                coordinates = self._calculate_element_coordinates(best_match['element'])
                                if coordinates:
                                    self.logger.debug(f"Found element in cache: {role} '{label}'")
                                    return {
                                        'coordinates': coordinates,
                                        'center_point': [
                                            coordinates[0] + coordinates[2] // 2,
                                            coordinates[1] + coordinates[3] // 2
                                        ],
                                        'role': best_match.get('role', ''),
                                        'title': best_match.get('title', ''),
                                        'enabled': best_match.get('enabled', True),
                                        'app_name': actual_app_name
                                    }
                            except Exception as e:
                                self.logger.debug(f"Cached element coordinate calculation failed: {e}")
                                continue
            
            # Cache miss or no valid cached results - perform fresh traversal
            self.logger.debug(f"Performing fresh accessibility tree traversal for {actual_app_name}")
            
            # Get the target application element
            app_element = self._get_target_application_element(app_name)
            if not app_element:
                raise ElementNotFoundError(
                    f"Cannot access application: {app_name or 'focused app'}", 
                    element_role=role, 
                    element_label=label
                )
            
            # Traverse the accessibility tree to find elements
            try:
                found_elements = self.traverse_accessibility_tree(app_element, max_depth=5)
            except Exception as e:
                raise AccessibilityTreeTraversalError(f"Failed to traverse accessibility tree: {e}")
            
            # Cache the fresh results
            if found_elements:
                self._cache_elements(actual_app_name, app_pid, found_elements)
            
            # Filter elements by actionability and visibility
            actionable_elements = self.filter_elements_by_criteria(
                found_elements, 
                actionable_only=True, 
                visible_only=True
            )
            
            # Find matching elements
            matching_elements = []
            for element_info in actionable_elements:
                if self._element_matches_criteria(element_info, role, label):
                    matching_elements.append(element_info)
            
            # Find the best match if multiple elements found
            if matching_elements:
                best_match = self.find_best_matching_element(matching_elements, label)
                if best_match:
                    try:
                        coordinates = self._calculate_element_coordinates(best_match['element'])
                        if not coordinates:
                            raise AccessibilityCoordinateError(
                                f"Failed to calculate coordinates for element", 
                                element_info=best_match
                            )
                        
                        return {
                            'coordinates': coordinates,
                            'center_point': [
                                coordinates[0] + coordinates[2] // 2,
                                coordinates[1] + coordinates[3] // 2
                            ],
                            'role': best_match.get('role', ''),
                            'title': best_match.get('title', ''),
                            'enabled': best_match.get('enabled', True),
                            'app_name': actual_app_name
                        }
                    except AccessibilityCoordinateError as e:
                        self.logger.warning(f"Coordinate calculation failed: {e}")
                        return None
            
            # Element not found
            raise ElementNotFoundError(
                f"Element not found: {role} with label '{label}'", 
                element_role=role, 
                element_label=label
            )
            
        except (ElementNotFoundError, AccessibilityTreeTraversalError, AccessibilityCoordinateError) as e:
            # These are expected errors that don't indicate API problems
            self.logger.debug(f"Element search failed: {e}")
            return None
        except Exception as e:
            self._handle_accessibility_error(e, "find_element")
            return None
    
    def _find_element_with_enhanced_roles_tracked(self, role: str, label: str, app_name: Optional[str] = None) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
        """
        Find element using enhanced role detection with detailed tracking.
        
        Args:
            role: Target element role (can be empty for broader search)
            label: Target element label/text
            app_name: Optional application name for scoped search
        
        Returns:
            Tuple of (element_info_dict, match_details_dict)
        """
        match_details = {
            'roles_checked': [],
            'attributes_checked': [],
            'fuzzy_matches': [],
            'confidence_score': 0.0,
            'matched_attribute': ''
        }
        
        # Get the original result
        result = self._find_element_with_enhanced_roles(role, label, app_name)
        
        # For now, populate basic tracking info
        # This will be enhanced when we implement the full fuzzy matching and multi-attribute search
        if role:
            match_details['roles_checked'] = [role]
        else:
            # Default clickable roles when no specific role provided
            match_details['roles_checked'] = ['AXButton', 'AXLink', 'AXMenuItem', 'AXCheckBox', 'AXRadioButton']
        
        match_details['attributes_checked'] = ['AXTitle', 'AXDescription', 'AXValue']
        
        if result:
            match_details['confidence_score'] = 100.0  # Exact match for now
            match_details['matched_attribute'] = 'AXTitle'  # Default assumption
        
        return result, match_details
    
    def _find_element_with_enhanced_roles(self, role: str, label: str, app_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Find element using enhanced role detection with all clickable roles.
        
        Args:
            role: Target element role (can be empty for broader search)
            label: Target element label/text
            app_name: Optional application name for scoped search
        
        Returns:
            Element information dict or None if not found
        """
        # Check for application focus changes
        self._check_application_focus_change()
        
        # Attempt recovery if in degraded mode
        if self.degraded_mode and self._should_attempt_recovery():
            if self._attempt_recovery():
                self.logger.info("Recovery successful, retrying enhanced element search")
        
        # If still in degraded mode, return None
        if self.degraded_mode:
            self.logger.debug("Skipping enhanced element search - in degraded mode")
            return None
        
        if not self.accessibility_enabled:
            return None
        
        try:
            # Get the target application info
            if app_name:
                # Find specific application
                running_apps = self.workspace.runningApplications()
                target_app = None
                for app in running_apps:
                    if app.localizedName() == app_name:
                        target_app = app
                        break
                
                if not target_app:
                    raise ElementNotFoundError(f"Application '{app_name}' not found")
                
                app_pid = target_app.processIdentifier()
                actual_app_name = app_name
            else:
                # Use focused application
                current_app = self.get_active_application()
                if not current_app:
                    raise ElementNotFoundError("No active application found")
                
                app_pid = current_app['pid']
                actual_app_name = current_app['name']
            
            # Try to get elements from cache first
            cached_elements = self._get_cached_elements(actual_app_name, app_pid)
            
            if cached_elements is not None:
                # Search in cached elements using enhanced role detection
                matching_elements = self._search_cached_elements_enhanced(actual_app_name, app_pid, role, label)
                
                # Filter by actionability and visibility
                actionable_elements = self.filter_elements_by_criteria(
                    matching_elements, 
                    actionable_only=True, 
                    visible_only=True
                )
                
                # Find best match from cached results
                if actionable_elements:
                    for element_info in actionable_elements:
                        if self._element_matches_criteria(element_info, role, label):
                            try:
                                coordinates = self._calculate_element_coordinates(element_info['element'])
                                if coordinates:
                                    self.logger.debug(f"Found element in cache with enhanced roles: {role} '{label}'")
                                    return {
                                        'coordinates': coordinates,
                                        'center_point': [
                                            coordinates[0] + coordinates[2] // 2,
                                            coordinates[1] + coordinates[3] // 2
                                        ],
                                        'role': element_info.get('role', ''),
                                        'title': element_info.get('title', ''),
                                        'enabled': element_info.get('enabled', True),
                                        'app_name': actual_app_name
                                    }
                            except Exception as e:
                                self.logger.debug(f"Cached element coordinate calculation failed: {e}")
                                continue
            
            # Cache miss or no valid cached results - perform fresh traversal
            self.logger.debug(f"Performing fresh accessibility tree traversal with enhanced roles for {actual_app_name}")
            
            # Get the target application element
            app_element = self._get_target_application_element(app_name)
            if not app_element:
                raise ElementNotFoundError(
                    f"Cannot access application: {app_name or 'focused app'}", 
                    element_role=role, 
                    element_label=label
                )
            
            # Traverse the accessibility tree to find elements
            try:
                found_elements = self.traverse_accessibility_tree(app_element, max_depth=5)
            except Exception as e:
                raise AccessibilityTreeTraversalError(f"Failed to traverse accessibility tree: {e}")
            
            # Cache the fresh results
            if found_elements:
                self._cache_elements(actual_app_name, app_pid, found_elements)
            
            # Filter elements by actionability and visibility
            actionable_elements = self.filter_elements_by_criteria(
                found_elements, 
                actionable_only=True, 
                visible_only=True
            )
            
            # Find matching elements using enhanced criteria
            matching_elements = []
            for element_info in actionable_elements:
                if self._element_matches_criteria(element_info, role, label):
                    matching_elements.append(element_info)
            
            # Find the best match if multiple elements found
            if matching_elements:
                best_match = self.find_best_matching_element(matching_elements, label)
                if best_match:
                    try:
                        coordinates = self._calculate_element_coordinates(best_match['element'])
                        if not coordinates:
                            raise AccessibilityCoordinateError(
                                f"Failed to calculate coordinates for element", 
                                element_info=best_match
                            )
                        
                        return {
                            'coordinates': coordinates,
                            'center_point': [
                                coordinates[0] + coordinates[2] // 2,
                                coordinates[1] + coordinates[3] // 2
                            ],
                            'role': best_match.get('role', ''),
                            'title': best_match.get('title', ''),
                            'enabled': best_match.get('enabled', True),
                            'app_name': actual_app_name
                        }
                    except AccessibilityCoordinateError as e:
                        self.logger.warning(f"Coordinate calculation failed: {e}")
                        return None
            
            # Element not found
            return None
            
        except (ElementNotFoundError, AccessibilityTreeTraversalError, AccessibilityCoordinateError) as e:
            # These are expected errors that don't indicate API problems
            self.logger.debug(f"Enhanced element search failed: {e}")
            return None
        except Exception as e:
            self._handle_accessibility_error(e, "find_element_enhanced")
            return None
    
    def _find_element_button_only_fallback(self, label: str, app_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Fallback to original button-only detection for backward compatibility.
        
        Args:
            label: Element label to search for
            app_name: Optional application name
            
        Returns:
            Element information dict or None if not found
        """
        self.logger.info(f"Enhanced role detection failed, falling back to button-only detection for '{label}'")
        
        try:
            # Use original logic that only searches for AXButton elements
            result = self._find_element_original_fallback('AXButton', label, app_name)
            if result:
                self.logger.info(f"Button-only fallback succeeded for '{label}'")
            else:
                self.logger.debug(f"Button-only fallback found no results for '{label}'")
            return result
        except Exception as e:
            self.logger.warning(f"Button-only fallback failed for '{label}': {e}")
            return None
    
    def _find_element_original_fallback(self, role: str, label: str, app_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Final fallback to original element detection logic.
        
        Args:
            role: Element role
            label: Element label
            app_name: Optional application name
            
        Returns:
            Element information dict or None if not found
        """
        self.logger.info(f"Using original fallback detection for role '{role}', label '{label}'")
        
        # This implements the original find_element logic as a fallback
        try:
            if not role:
                role = 'AXButton'  # Default to button for backward compatibility
                self.logger.debug("No role specified, defaulting to AXButton for backward compatibility")
            
            # Use the original find_element implementation logic
            result = self._find_element_with_strict_role_matching(role, label, app_name)
            if result:
                self.logger.info(f"Original fallback succeeded for '{role}' '{label}'")
            else:
                self.logger.debug(f"Original fallback found no results for '{role}' '{label}'")
            return result
        except Exception as e:
            self.logger.warning(f"Original fallback failed for '{role}' '{label}': {e}")
            return None
    
    def _find_element_with_strict_role_matching(self, role: str, label: str, app_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Find element with strict role matching for backward compatibility.
        
        Args:
            role: Exact role to match
            label: Element label
            app_name: Optional application name
            
        Returns:
            Element information dict or None if not found
        """
        self.logger.debug(f"Using strict role matching for '{role}' '{label}'")
        
        try:
            # Get the target application info
            if app_name:
                # Find specific application
                running_apps = self.workspace.runningApplications()
                target_app = None
                for app in running_apps:
                    if app.localizedName() == app_name:
                        target_app = app
                        break
                
                if not target_app:
                    self.logger.debug(f"Application '{app_name}' not found")
                    return None

                app_pid = target_app.processIdentifier()
                actual_app_name = app_name
            else:
                # Use focused application
                current_app = self.get_active_application()
                if not current_app:
                    self.logger.debug("No active application found")
                    return None
                
                app_pid = current_app['pid']
                actual_app_name = current_app['name']
            
            # Get the target application element
            app_element = self._get_target_application_element(app_name)
            if not app_element:
                self.logger.debug(f"Cannot access application: {app_name or 'focused app'}")
                return None
            
            # Traverse the accessibility tree to find elements
            found_elements = self.traverse_accessibility_tree(app_element, max_depth=5)
            
            # Find matching elements using strict criteria (exact role match only)
            matching_elements = []
            for element_info in found_elements:
                element_role = element_info.get('role', '')
                element_title = element_info.get('title', '')
                
                # Strict logic: exact role match and fuzzy label match
                if role == element_role and self.fuzzy_match_label(element_title, label):
                    if self.is_element_actionable(element_info) and self._is_element_visible(element_info):
                        matching_elements.append(element_info)
                        self.logger.debug(f"Found strict match: {element_role} '{element_title}'")
            
            # Find the best match if multiple elements found
            if matching_elements:
                best_match = self.find_best_matching_element(matching_elements, label)
                if best_match:
                    coordinates = self._calculate_element_coordinates(best_match['element'])
                    if coordinates:
                        self.logger.debug(f"Strict role matching succeeded for '{role}' '{label}'")
                        return {
                            'coordinates': coordinates,
                            'center_point': [
                                coordinates[0] + coordinates[2] // 2,
                                coordinates[1] + coordinates[3] // 2
                            ],
                            'role': best_match.get('role', ''),
                            'title': best_match.get('title', ''),
                            'enabled': best_match.get('enabled', True),
                            'app_name': actual_app_name
                        }
            
            self.logger.debug(f"No strict matches found for '{role}' '{label}'")
            return None
            
        except Exception as e:
            self.logger.debug(f"Strict role matching failed for '{role}' '{label}': {e}")
            return None
    
    def _search_cached_elements_enhanced(self, app_name: str, app_pid: int, role: str, label: str) -> List[Dict[str, Any]]:
        """
        Search cached elements using enhanced role detection.
        
        Args:
            app_name: Application name
            app_pid: Application process ID
            role: Target role (can be empty for broader search)
            label: Target label
            
        Returns:
            List of matching elements
        """
        cache_key = self._get_cache_key(app_name, app_pid)
        
        with self.cache_lock:
            if cache_key not in self.element_indexes:
                return []
            
            index = self.element_indexes[cache_key]
            candidates = set()
            
            # Enhanced role searching
            if role:
                # Direct role matches
                role_matches = index.role_index.get(role, [])
                candidates.update(id(elem) for elem in role_matches)
                
                # Category matches
                category_matches = index.role_index.get(role.lower(), [])
                candidates.update(id(elem) for elem in category_matches)
            else:
                # If no role specified, search all clickable elements
                for clickable_role in self.CLICKABLE_ROLES:
                    clickable_matches = index.role_index.get(clickable_role, [])
                    candidates.update(id(elem) for elem in clickable_matches)
            
            # Search by exact title match
            if label:
                title_matches = index.title_index.get(label, [])
                if role or candidates:
                    # Intersect with role matches if we have role candidates
                    title_ids = {id(elem) for elem in title_matches}
                    if candidates:
                        candidates = candidates.intersection(title_ids)
                    else:
                        candidates = title_ids
                else:
                    candidates.update(id(elem) for elem in title_matches)
                
                # Search by normalized title for fuzzy matching
                normalized_label = self._normalize_text(label)
                if normalized_label:
                    normalized_matches = index.normalized_title_index.get(normalized_label, [])
                    normalized_ids = {id(elem) for elem in normalized_matches}
                    candidates = candidates.union(normalized_ids)
            
            # Convert back to element objects
            all_elements = []
            for elements_list in [index.role_index.get(role, []), 
                                index.title_index.get(label, []),
                                index.normalized_title_index.get(self._normalize_text(label), [])]:
                all_elements.extend(elements_list)
            
            # Add clickable elements if no specific role
            if not role:
                for clickable_role in self.CLICKABLE_ROLES:
                    clickable_elements = index.role_index.get(clickable_role, [])
                    all_elements.extend(clickable_elements)
            
            # Filter to only candidates and remove duplicates
            result = []
            seen_ids = set()
            for elem in all_elements:
                elem_id = id(elem)
                if elem_id in candidates and elem_id not in seen_ids:
                    result.append(elem)
                    seen_ids.add(elem_id)
            
            return result

    def traverse_accessibility_tree(self, element, max_depth: int = 5) -> List[Dict[str, Any]]:
        """
        Recursively traverse accessibility tree to find all elements with error handling.
        
        Args:
            element: Root accessibility element to start traversal
            max_depth: Maximum depth to traverse
        
        Returns:
            List of dictionaries containing element information
        """
        elements = []
        
        if max_depth <= 0 or not element:
            return elements
        
        try:
            # Get element information
            element_info = self._extract_element_info(element)
            if element_info:
                elements.append(element_info)
            
            # Get children and traverse recursively
            try:
                children = self._get_element_children(element)
                for child in children:
                    try:
                        child_elements = self.traverse_accessibility_tree(child, max_depth - 1)
                        elements.extend(child_elements)
                    except Exception as e:
                        # Log child traversal errors but continue with other children
                        self.logger.debug(f"Error traversing child element: {e}")
                        continue
            except Exception as e:
                # Log children access error but don't fail the entire traversal
                self.logger.debug(f"Error accessing element children: {e}")
        
        except Exception as e:
            self.logger.debug(f"Error traversing element: {e}")
            # Don't re-raise - return partial results
        
        return elements
    
    def _get_target_application_element(self, app_name: Optional[str]):
        """Get the accessibility element for the target application."""
        if app_name:
            # Find specific application by name
            running_apps = self.workspace.runningApplications()
            for app in running_apps:
                if app.localizedName() == app_name:
                    pid = app.processIdentifier()
                    return AXUIElementCreateApplication(pid)
        
        # Default to focused application
        return self._get_focused_application_element()
    
    def _extract_element_info(self, element) -> Optional[Dict[str, Any]]:
        """Extract information from an accessibility element."""
        try:
            info = {'element': element}
            
            # Get role
            role_result = AXUIElementCopyAttributeValue(
                element, kAXRoleAttribute, None
            )
            if role_result[0] == 0:
                info['role'] = role_result[1]
            
            # Get title/label
            title_result = AXUIElementCopyAttributeValue(
                element, kAXTitleAttribute, None
            )
            if title_result[0] == 0:
                info['title'] = title_result[1]
            
            # Try alternative label attributes if title is empty
            if not info.get('title'):
                label_result = AXUIElementCopyAttributeValue(
                    element, kAXDescriptionAttribute, None
                )
                if label_result[0] == 0:
                    info['title'] = label_result[1]
            
            # Get enabled state
            enabled_result = AXUIElementCopyAttributeValue(
                element, kAXEnabledAttribute, None
            )
            if enabled_result[0] == 0:
                info['enabled'] = bool(enabled_result[1])
            else:
                info['enabled'] = True  # Default to enabled
            
            return info if info.get('role') else None
            
        except Exception as e:
            self.logger.debug(f"Error extracting element info: {e}")
            return None
    
    def _get_element_children(self, element) -> List:
        """Get children of an accessibility element."""
        try:
            children_result = AXUIElementCopyAttributeValue(
                element, kAXChildrenAttribute, None
            )
            if children_result[0] == 0 and children_result[1]:
                return list(children_result[1])
            return []
        except Exception as e:
            self.logger.debug(f"Error getting element children: {e}")
            return []
    
    def _element_matches_criteria(self, element_info: Dict[str, Any], role: str, label: str) -> bool:
        """Check if element matches the search criteria with enhanced role detection and multi-attribute text matching."""
        element_role = element_info.get('role', '')
        
        # Enhanced role matching logic
        if role:
            # Direct role match
            if role == element_role:
                pass  # Continue to label check
            # Check if role matches category
            elif role.lower() == self.classify_element_role(element_role):
                pass  # Continue to label check
            # Check if searching for clickable elements and element is clickable
            elif role.lower() in ['button', 'clickable'] and self.is_clickable_element_role(element_role):
                pass  # Continue to label check
            else:
                return False
        else:
            # If no specific role requested, check if element is clickable for broad search
            if not self.is_clickable_element_role(element_role):
                return False
        
        # Use multi-attribute text matching instead of single attribute matching
        element = element_info.get('element')
        if element:
            # Use the new multi-attribute checking method
            match_found, confidence_score, matched_attribute = self._check_element_text_match(element, label)
            
            if match_found:
                self.logger.debug(f"Multi-attribute match found: {matched_attribute}='{element_info.get('title', '')}' matches '{label}' (score: {confidence_score:.2f})")
                return True
            else:
                self.logger.debug(f"No multi-attribute match for '{label}' in element with role '{element_role}'")
                return False
        else:
            # Fallback to original single-attribute matching if element is not available
            self.logger.debug(f"Element not available for multi-attribute checking, falling back to title-only matching")
            element_title = element_info.get('title', '')
            return self.fuzzy_match_label(element_title, label)
    
    def _calculate_element_coordinates(self, element) -> Optional[List[int]]:
        """Calculate coordinates and size for an accessibility element."""
        try:
            # Get position
            position_result = AXUIElementCopyAttributeValue(
                element, kAXPositionAttribute, None
            )
            if position_result[0] != 0:
                return None
            
            # Get size
            size_result = AXUIElementCopyAttributeValue(
                element, kAXSizeAttribute, None
            )
            if size_result[0] != 0:
                return None
            
            position = position_result[1]
            size = size_result[1]
            
            # Convert to [x, y, width, height] format
            coordinates = [
                int(position.x),
                int(position.y),
                int(size.width),
                int(size.height)
            ]
            
            # Validate coordinates
            if all(coord >= 0 for coord in coordinates) and coordinates[2] > 0 and coordinates[3] > 0:
                return coordinates
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Error calculating coordinates: {e}")
            return None
    
    def _get_app_name_from_element(self, app_element) -> str:
        """Get application name from accessibility element."""
        try:
            title_result = AXUIElementCopyAttributeValue(
                app_element, kAXTitleAttribute, None
            )
            if title_result[0] == 0:
                return title_result[1]
            return "Unknown"
        except Exception:
            return "Unknown"
    
    # Element Classification and Filtering Methods
    
    ROLE_MAPPINGS = {
        # Interactive elements
        'button': ['AXButton', 'AXMenuButton'],
        'menu': ['AXMenu', 'AXMenuBar', 'AXMenuItem', 'AXMenuBarItem'],
        'text_field': ['AXTextField', 'AXSecureTextField', 'AXTextArea'],
        'checkbox': ['AXCheckBox'],
        'radio': ['AXRadioButton'],
        'slider': ['AXSlider'],
        'popup': ['AXPopUpButton', 'AXComboBox'],
        'tab': ['AXTab', 'AXTabGroup'],
        'link': ['AXLink'],
        'image': ['AXImage'],
        'table': ['AXTable', 'AXOutline'],
        'cell': ['AXCell', 'AXRow', 'AXColumn'],
        'scroll': ['AXScrollArea', 'AXScrollBar'],
        'window': ['AXWindow', 'AXDialog', 'AXSheet'],
        'group': ['AXGroup', 'AXRadioGroup'],
        'toolbar': ['AXToolbar', 'AXToolbarButton'],
        'list': ['AXList', 'AXBrowser'],
        'web': ['AXWebArea'],
        'static': ['AXStaticText', 'AXHeading']
    }
    
    # Enhanced clickable element roles for comprehensive detection
    CLICKABLE_ROLES = {
        'AXButton', 'AXMenuButton', 'AXMenuItem', 'AXMenuBarItem',
        'AXLink', 'AXCheckBox', 'AXRadioButton', 'AXTab',
        'AXToolbarButton', 'AXPopUpButton', 'AXComboBox'
    }
    
    # Accessibility attributes to check in priority order for multi-attribute text searching
    ACCESSIBILITY_ATTRIBUTES = ['AXTitle', 'AXDescription', 'AXValue']
    
    # Fuzzy matching configuration
    FUZZY_MATCHING_ENABLED = True
    FUZZY_CONFIDENCE_THRESHOLD = 85  # Minimum confidence score (0-100) for fuzzy matches
    FUZZY_MATCHING_TIMEOUT = 200     # Maximum time in milliseconds for fuzzy matching operations
    LOG_FUZZY_MATCH_SCORES = False   # Enable detailed logging of fuzzy match scores
    
    ACTIONABLE_ROLES = {
        'AXButton', 'AXMenuButton', 'AXMenuItem', 'AXMenuBarItem',
        'AXTextField', 'AXSecureTextField', 'AXTextArea',
        'AXCheckBox', 'AXRadioButton', 'AXSlider',
        'AXPopUpButton', 'AXComboBox', 'AXTab',
        'AXLink', 'AXToolbarButton'
    }
    
    def classify_element_role(self, role: str) -> str:
        """
        Classify accessibility role into a general category.
        
        Args:
            role: Raw accessibility role (e.g., 'AXButton')
        
        Returns:
            General category (e.g., 'button', 'menu', 'text_field')
        """
        for category, roles in self.ROLE_MAPPINGS.items():
            if role in roles:
                return category
        return 'unknown'
    
    def is_clickable_element_role(self, role: str) -> bool:
        """
        Check if an element role is clickable based on CLICKABLE_ROLES.
        
        Args:
            role: Raw accessibility role (e.g., 'AXButton', 'AXLink')
        
        Returns:
            True if the role is in CLICKABLE_ROLES, False otherwise
        """
        try:
            return role in self.CLICKABLE_ROLES
        except AttributeError:
            # Graceful degradation when CLICKABLE_ROLES is not configured
            self.logger.debug("CLICKABLE_ROLES not configured, falling back to button-only detection")
            return role == 'AXButton'
    
    def categorize_element_type(self, role: str) -> str:
        """
        Categorize element type for enhanced role detection.
        
        Args:
            role: Raw accessibility role
            
        Returns:
            Element type category ('clickable', 'input', 'display', 'container', 'unknown')
        """
        try:
            if role in self.CLICKABLE_ROLES:
                return 'clickable'
            elif role in ['AXTextField', 'AXSecureTextField', 'AXTextArea']:
                return 'input'
            elif role in ['AXStaticText', 'AXHeading', 'AXImage']:
                return 'display'
            elif role in ['AXGroup', 'AXWindow', 'AXDialog', 'AXScrollArea']:
                return 'container'
            else:
                return 'unknown'
        except AttributeError:
            # Graceful degradation when CLICKABLE_ROLES is not configured
            self.logger.debug("CLICKABLE_ROLES not configured, using basic categorization")
            if role == 'AXButton':
                return 'clickable'
            elif role in ['AXTextField', 'AXSecureTextField', 'AXTextArea']:
                return 'input'
            elif role in ['AXStaticText', 'AXHeading', 'AXImage']:
                return 'display'
            elif role in ['AXGroup', 'AXWindow', 'AXDialog', 'AXScrollArea']:
                return 'container'
            else:
                return 'unknown'
    
    def is_enhanced_role_detection_available(self) -> bool:
        """
        Check if enhanced role detection features are properly configured.
        
        Returns:
            True if enhanced features are available, False if fallback is needed
        """
        try:
            # Check if CLICKABLE_ROLES is available and properly configured
            if not hasattr(self, 'CLICKABLE_ROLES') or not self.CLICKABLE_ROLES:
                return False
            
            # Check if enhanced methods are available
            if not hasattr(self, 'is_clickable_element_role'):
                return False
            
            return True
        except Exception as e:
            self.logger.debug(f"Enhanced role detection not available: {e}")
            return False
    
    def is_element_actionable(self, element_info: Dict[str, Any]) -> bool:
        """
        Determine if an element can be interacted with.
        
        Args:
            element_info: Dictionary containing element information
        
        Returns:
            True if element is actionable, False otherwise
        """
        role = element_info.get('role', '')
        enabled = element_info.get('enabled', False)
        
        # Must be enabled and have an actionable role
        if not enabled or role not in self.ACTIONABLE_ROLES:
            return False
        
        # Additional validation for specific roles
        if role in ['AXTextField', 'AXSecureTextField', 'AXTextArea']:
            # Text fields should be editable
            return self._is_text_field_editable(element_info.get('element'))
        
        return True
    
    def fuzzy_match_label(self, element_title: str, search_label: str, threshold: float = 0.7) -> bool:
        """
        Perform fuzzy matching for element labels and titles.
        
        Args:
            element_title: The element's actual title/label
            search_label: The label being searched for
            threshold: Minimum similarity score (0.0 to 1.0)
        
        Returns:
            True if labels match within threshold, False otherwise
        """
        if not element_title or not search_label:
            return False
        
        # Normalize strings
        title_norm = self._normalize_text(element_title)
        search_norm = self._normalize_text(search_label)
        
        # Exact match after normalization
        if title_norm == search_norm:
            return True
        
        # Contains match
        if search_norm in title_norm or title_norm in search_norm:
            return True
        
        # Word-based matching
        title_words = set(title_norm.split())
        search_words = set(search_norm.split())
        
        # Check if all search words are in title
        if search_words.issubset(title_words):
            return True
        
        # Calculate similarity score using Jaccard similarity
        intersection = len(title_words.intersection(search_words))
        union = len(title_words.union(search_words))
        
        if union == 0:
            return False
        
        similarity = intersection / union
        return similarity >= threshold
    
    def fuzzy_match_text(self, element_text: str, target_text: str, 
                        confidence_threshold: Optional[int] = None,
                        timeout_ms: Optional[int] = None) -> Tuple[bool, float]:
        """
        Perform fuzzy string matching using thefuzz library with confidence threshold.
        
        Args:
            element_text: Text from the accessibility element
            target_text: Text to match against
            confidence_threshold: Minimum confidence score (0-100), uses class default if None
            timeout_ms: Timeout in milliseconds, uses class default if None
        
        Returns:
            Tuple of (match_found, confidence_score)
        """
        start_time = time.time()
        
        # Use class defaults if not specified
        if confidence_threshold is None:
            confidence_threshold = self.FUZZY_CONFIDENCE_THRESHOLD
        if timeout_ms is None:
            timeout_ms = self.FUZZY_MATCHING_TIMEOUT
        
        # Perform periodic cache cleanup
        self._periodic_cache_cleanup()
        
        # Check cache first
        cached_result = self._get_cached_fuzzy_match(element_text, target_text, confidence_threshold)
        if cached_result is not None:
            return cached_result
        
        # Check if fuzzy matching is enabled and available
        if not self.FUZZY_MATCHING_ENABLED or not FUZZY_MATCHING_AVAILABLE:
            self.logger.debug("Fuzzy matching disabled or unavailable, falling back to exact matching")
            # Fallback to exact matching
            normalized_element = self._normalize_text(element_text)
            normalized_target = self._normalize_text(target_text)
            exact_match = normalized_element == normalized_target or normalized_target in normalized_element
            fallback_confidence = 100.0 if exact_match else 0.0
            
            # Cache the fallback result
            self._cache_fuzzy_match_result(element_text, target_text, confidence_threshold, exact_match, fallback_confidence)
            
            return exact_match, fallback_confidence
        
        if not element_text or not target_text:
            return False, 0.0
        
        try:
            # Check timeout
            elapsed_ms = (time.time() - start_time) * 1000
            if elapsed_ms > timeout_ms:
                timeout_error = AccessibilityTimeoutError(
                    f"Fuzzy matching timeout exceeded: {elapsed_ms:.1f}ms > {timeout_ms}ms",
                    "fuzzy_matching"
                )
                self.logger.warning(str(timeout_error))
                raise timeout_error
            
            # Use partial_ratio for better matching of substrings
            try:
                confidence_score = fuzz.partial_ratio(element_text.lower(), target_text.lower())
            except Exception as fuzzy_error:
                raise FuzzyMatchingError(
                    f"Fuzzy matching library error: {fuzzy_error}",
                    target_text, element_text, fuzzy_error
                )
            
            # Check timeout again after fuzzy matching
            elapsed_ms = (time.time() - start_time) * 1000
            if elapsed_ms > timeout_ms:
                timeout_error = AccessibilityTimeoutError(
                    f"Fuzzy matching completed but exceeded timeout: {elapsed_ms:.1f}ms > {timeout_ms}ms",
                    "fuzzy_matching"
                )
                self.logger.warning(str(timeout_error))
                raise timeout_error
            
            # Log performance monitoring
            if elapsed_ms > timeout_ms * 0.8:  # Warn if using more than 80% of timeout
                self.logger.warning(f"Fuzzy matching slow: {elapsed_ms:.1f}ms (threshold: {timeout_ms}ms)")
            
            match_found = confidence_score >= confidence_threshold
            
            # Log fuzzy match scores if enabled or in debug mode
            if self.log_fuzzy_match_scores or self.debug_logging:
                log_level = logging.INFO if self.log_fuzzy_match_scores else logging.DEBUG
                self.logger.log(log_level, f"Fuzzy match: '{element_text}' vs '{target_text}' = {confidence_score}% "
                               f"({'MATCH' if match_found else 'NO MATCH'}, threshold: {confidence_threshold}%, "
                               f"time: {elapsed_ms:.1f}ms)")
            
            # Cache the successful result
            try:
                self._cache_fuzzy_match_result(element_text, target_text, confidence_threshold, match_found, float(confidence_score))
            except Exception as cache_error:
                self.logger.debug(f"Failed to cache fuzzy match result: {cache_error}")
                # Don't fail the entire operation for caching errors
            
            return match_found, float(confidence_score)
            
        except (FuzzyMatchingError, AccessibilityTimeoutError):
            # Re-raise specific errors for proper handling upstream
            raise
            
        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            
            # Wrap unexpected errors in FuzzyMatchingError
            fuzzy_error = FuzzyMatchingError(
                f"Unexpected fuzzy matching error after {elapsed_ms:.1f}ms: {e}",
                target_text, element_text, e
            )
            self.logger.warning(str(fuzzy_error))
            
            # Use error handling infrastructure for fallback
            try:
                fallback_match, fallback_confidence = self._handle_fuzzy_matching_error(
                    fuzzy_error, target_text, element_text
                )
                
                # Cache the fallback result
                try:
                    self._cache_fuzzy_match_result(element_text, target_text, confidence_threshold, fallback_match, fallback_confidence)
                except Exception as cache_error:
                    self.logger.debug(f"Failed to cache fallback result: {cache_error}")
                
                return fallback_match, fallback_confidence
                
            except Exception as fallback_error:
                self.logger.error(f"Both fuzzy matching and fallback failed: {fallback_error}")
                
                # Cache the failure result
                try:
                    self._cache_fuzzy_match_result(element_text, target_text, confidence_threshold, False, 0.0)
                except Exception:
                    pass  # Ignore caching errors in final fallback
                
                return False, 0.0
    
    def filter_elements_by_criteria(self, elements: List[Dict[str, Any]], 
                                  role_filter: Optional[str] = None,
                                  actionable_only: bool = True,
                                  visible_only: bool = True) -> List[Dict[str, Any]]:
        """
        Filter elements based on various criteria.
        
        Args:
            elements: List of element information dictionaries
            role_filter: Filter by specific role category
            actionable_only: Only return actionable elements
            visible_only: Only return visible elements
        
        Returns:
            Filtered list of elements
        """
        filtered = []
        
        for element_info in elements:
            # Role filter
            if role_filter:
                element_category = self.classify_element_role(element_info.get('role', ''))
                if element_category != role_filter:
                    continue
            
            # Actionable filter
            if actionable_only and not self.is_element_actionable(element_info):
                continue
            
            # Visibility filter
            if visible_only and not self._is_element_visible(element_info):
                continue
            
            filtered.append(element_info)
        
        return filtered
    
    def find_best_matching_element(self, elements: List[Dict[str, Any]], 
                                 search_label: str) -> Optional[Dict[str, Any]]:
        """
        Find the best matching element from a list based on label similarity.
        
        Args:
            elements: List of element information dictionaries
            search_label: Label to search for
        
        Returns:
            Best matching element or None if no good match found
        """
        best_match = None
        best_score = 0.0
        
        for element_info in elements:
            element_title = element_info.get('title', '')
            
            # Calculate match score
            score = self._calculate_match_score(element_title, search_label)
            
            if score > best_score:
                best_score = score
                best_match = element_info
        
        # Return match only if score is above threshold
        return best_match if best_score >= 0.5 else None
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison."""
        if not text:
            return ""
        
        # Convert to lowercase and remove extra whitespace
        normalized = re.sub(r'\s+', ' ', text.lower().strip())
        
        # Remove common punctuation
        normalized = re.sub(r'[^\w\s]', '', normalized)
        
        return normalized
    
    def _calculate_match_score(self, element_title: str, search_label: str) -> float:
        """Calculate similarity score between element title and search label."""
        if not element_title or not search_label:
            return 0.0
        
        title_norm = self._normalize_text(element_title)
        search_norm = self._normalize_text(search_label)
        
        # Exact match
        if title_norm == search_norm:
            return 1.0
        
        # Contains match
        if search_norm in title_norm:
            return 0.9
        if title_norm in search_norm:
            return 0.8
        
        # Word-based similarity
        title_words = set(title_norm.split())
        search_words = set(search_norm.split())
        
        if not title_words or not search_words:
            return 0.0
        
        intersection = len(title_words.intersection(search_words))
        union = len(title_words.union(search_words))
        
        return intersection / union if union > 0 else 0.0
    
    def _check_element_text_match(self, element, target_text: str) -> tuple[bool, float, str]:
        """
        Check if element text matches target using multi-attribute checking with enhanced error handling.
        
        Examines multiple accessibility attributes in priority order:
        AXTitle, AXDescription, AXValue. Returns on first successful match.
        
        Args:
            element: Accessibility element to check
            target_text: Text to match against
        
        Returns:
            Tuple of (match_found, confidence_score, matched_attribute)
        """
        try:
            with self._performance_timer(
                "attribute_text_matching",
                timeout_ms=self.attribute_check_timeout_ms,
                metadata={'target_text': target_text}
            ) as perf_metrics:
                
                if not element or not target_text:
                    return False, 0.0, ""
                
                target_normalized = self._normalize_text(target_text)
                if not target_normalized:
                    return False, 0.0, ""
            
            # Check each attribute in priority order with enhanced error handling
            for attribute in self.accessibility_attributes:
                try:
                    # Get attribute value from element
                    attribute_result = AXUIElementCopyAttributeValue(
                        element, attribute, None
                    )
                    
                    if attribute_result[0] == 0 and attribute_result[1]:
                        attribute_value = str(attribute_result[1])
                        
                        if attribute_value:
                            try:
                                # Use safe fuzzy matching for this attribute
                                match_found, confidence_score = self._safe_fuzzy_match(
                                    target_text, attribute_value, self.fuzzy_confidence_threshold
                                )
                                
                                # Return first successful match
                                if match_found:
                                    if self.debug_logging:
                                        self.logger.debug(f"Multi-attribute fuzzy match found: {attribute}='{attribute_value}' matches '{target_text}' (confidence: {confidence_score:.1f}%)")
                                    return True, confidence_score / 100.0, attribute  # Convert to 0-1 scale for compatibility
                                
                                if self.debug_logging:
                                    self.logger.debug(f"Attribute {attribute}='{attribute_value}' low confidence: {confidence_score:.1f}%")
                            
                            except FuzzyMatchingError as fuzzy_error:
                                # Handle fuzzy matching error with fallback
                                self.logger.debug(f"Fuzzy matching failed for {attribute}, trying fallback: {fuzzy_error}")
                                fallback_match, fallback_confidence = self._handle_fuzzy_matching_error(
                                    fuzzy_error, target_text, attribute_value
                                )
                                if fallback_match:
                                    return True, fallback_confidence / 100.0, attribute
                    
                except AttributeAccessError as attr_error:
                    # Handle attribute access error with fallback
                    element_info = {'element': element, 'target_text': target_text}
                    fallback_value = self._handle_attribute_access_error(attr_error, attribute, element_info)
                    if fallback_value:
                        try:
                            match_found, confidence_score = self._safe_fuzzy_match(
                                target_text, fallback_value, self.fuzzy_confidence_threshold
                            )
                            if match_found:
                                return True, confidence_score / 100.0, attribute
                        except Exception as fallback_error:
                            self.logger.debug(f"Fallback matching failed for {attribute}: {fallback_error}")
                
                except Exception as e:
                    # Wrap unexpected errors in AttributeAccessError and handle
                    element_info = {'element': element, 'target_text': target_text}
                    attr_error = AttributeAccessError(
                        f"Unexpected error accessing {attribute}: {e}",
                        attribute, element_info, e
                    )
                    fallback_value = self._handle_attribute_access_error(attr_error, attribute, element_info)
                    if fallback_value:
                        try:
                            match_found, confidence_score = self._safe_fuzzy_match(
                                target_text, fallback_value, self.fuzzy_confidence_threshold
                            )
                            if match_found:
                                return True, confidence_score / 100.0, attribute
                        except Exception:
                            continue
            
            # No successful fuzzy matches found, try fallback to exact matching
            if self.debug_logging:
                self.logger.debug(f"No multi-attribute fuzzy matches found for '{target_text}', trying exact matching fallback")
            
            for attribute in self.accessibility_attributes:
                try:
                    # Get attribute value from element
                    attribute_result = AXUIElementCopyAttributeValue(
                        element, attribute, None
                    )
                    
                    if attribute_result[0] == 0 and attribute_result[1]:
                        attribute_value = str(attribute_result[1])
                        
                        if attribute_value:
                            # Fallback to exact matching
                            normalized_attribute = self._normalize_text(attribute_value)
                            normalized_target = self._normalize_text(target_text)
                            
                            # Exact match or contains match
                            if (normalized_attribute == normalized_target or 
                                normalized_target in normalized_attribute):
                                if self.debug_logging:
                                    self.logger.debug(f"Exact match fallback found: {attribute}='{attribute_value}' matches '{target_text}'")
                                return True, 1.0, attribute
                    
                except Exception as e:
                    # Log attribute access error but continue with next attribute
                    self.logger.debug(f"Error accessing attribute {attribute} in fallback: {e}")
                    continue
            
            # No matches found at all
            if self.debug_logging:
                self.logger.debug(f"No multi-attribute matches found for '{target_text}' (fuzzy or exact)")
            return False, 0.0, ""
        
        except Exception as e:
            # Handle any unexpected errors in the entire method
            self.logger.error(f"Unexpected error in _check_element_text_match: {e}")
            
            # Final fallback: try simple string comparison
            try:
                if hasattr(element, 'get'):
                    title = element.get('title', '') or element.get('AXTitle', '')
                    if title and target_text.lower() in title.lower():
                        return True, 1.0, 'title'
            except Exception:
                pass
            
            return False, 0.0, ""
    
    def _is_text_field_editable(self, element) -> bool:
        """Check if a text field is editable."""
        try:
            # Check if element has editable attribute
            editable_result = AXUIElementCopyAttributeValue(
                element, 'AXEditable', None
            )
            if editable_result[0] == 0:
                return bool(editable_result[1])
            
            # Default to True for text fields if attribute not available
            return True
            
        except Exception:
            return True
    
    def _is_element_visible(self, element_info: Dict[str, Any]) -> bool:
        """Check if an element is visible on screen."""
        element = element_info.get('element')
        if not element:
            return False
        
        try:
            # Check if element has position and size
            coordinates = self._calculate_element_coordinates(element)
            if not coordinates:
                return False
            
            # Check if element has reasonable size (not 0x0)
            width, height = coordinates[2], coordinates[3]
            if width <= 0 or height <= 0:
                return False
            
            # Check if element is on screen (basic check)
            x, y = coordinates[0], coordinates[1]
            if x < -1000 or y < -1000:  # Likely off-screen
                return False
            
            return True
            
        except Exception:
            return False
    
    def preload_active_application_tree(self) -> bool:
        """
        Preload accessibility tree for the currently active application.
        
        Returns:
            True if preloading was successful, False otherwise
        """
        try:
            current_app = self.get_active_application()
            if not current_app:
                return False
            
            app_name = current_app['name']
            app_pid = current_app['pid']
            
            # Check if already cached and valid
            if self._get_cached_elements(app_name, app_pid) is not None:
                self.logger.debug(f"Application {app_name} already cached")
                return True
            
            # Get application element and traverse tree
            app_element = self._get_target_application_element(app_name)
            if not app_element:
                return False
            
            # Perform background traversal
            self.logger.debug(f"Preloading accessibility tree for {app_name}")
            found_elements = self.traverse_accessibility_tree(app_element, max_depth=5)
            
            if found_elements:
                self._cache_elements(app_name, app_pid, found_elements)
                self.logger.info(f"Preloaded {len(found_elements)} elements for {app_name}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.debug(f"Error preloading application tree: {e}")
            return False
    
    # Parallel Processing and Background Operations
    
    def find_element_with_vision_preparation(self, role: str, label: str, 
                                           app_name: Optional[str] = None,
                                           vision_callback: Optional[callable] = None) -> Optional[Dict[str, Any]]:
        """
        Find element using accessibility API while preparing vision capture in parallel.
        
        Args:
            role: Accessibility role to search for
            label: Element label to search for
            app_name: Optional application name
            vision_callback: Optional callback to prepare vision capture
            
        Returns:
            Element information if found, None otherwise
        """
        if not self.parallel_processing_enabled or not vision_callback:
            # Fall back to regular find_element
            return self.find_element(role, label, app_name)
        
        try:
            # Start vision preparation in background
            vision_future = self.background_thread_pool.submit(vision_callback)
            
            # Attempt accessibility detection
            accessibility_result = self.find_element(role, label, app_name)
            
            if accessibility_result:
                # Cancel vision preparation if accessibility succeeds
                try:
                    vision_future.cancel()
                    self.logger.debug("Cancelled vision preparation - accessibility succeeded")
                except Exception as e:
                    self.logger.debug(f"Could not cancel vision preparation: {e}")
                
                return accessibility_result
            
            # If accessibility fails, wait for vision preparation to complete
            try:
                vision_result = vision_future.result(timeout=5.0)  # 5 second timeout
                self.logger.debug("Vision preparation completed as fallback")
                return None  # Let caller handle vision fallback
            except concurrent.futures.TimeoutError:
                self.logger.warning("Vision preparation timed out")
                return None
            except Exception as e:
                self.logger.debug(f"Vision preparation failed: {e}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error in parallel element detection: {e}")
            return self.find_element(role, label, app_name)  # Fallback to regular method
    
    def start_background_tree_loading(self, app_name: str, app_pid: int) -> str:
        """
        Start loading accessibility tree in background.
        
        Args:
            app_name: Application name
            app_pid: Application process ID
            
        Returns:
            Task ID for tracking the background operation
        """
        task_id = f"bg_load_{app_name}_{app_pid}_{int(time.time())}"
        
        def background_load():
            """Background task to load accessibility tree."""
            try:
                self.logger.debug(f"Starting background tree loading for {app_name}")
                
                # Check if already cached
                if self._get_cached_elements(app_name, app_pid) is not None:
                    self.logger.debug(f"Tree already cached for {app_name}")
                    return True
                
                # Get application element
                app_element = self._get_target_application_element(app_name)
                if not app_element:
                    self.logger.debug(f"Could not get application element for {app_name}")
                    return False
                
                # Traverse tree
                elements = self.traverse_accessibility_tree(app_element, max_depth=5)
                
                if elements:
                    self._cache_elements(app_name, app_pid, elements)
                    self.logger.info(f"Background loaded {len(elements)} elements for {app_name}")
                    return True
                
                return False
                
            except Exception as e:
                self.logger.debug(f"Background tree loading failed for {app_name}: {e}")
                return False
        
        # Submit background task
        future = self.background_thread_pool.submit(background_load)
        self.background_tasks[task_id] = {
            'future': future,
            'app_name': app_name,
            'app_pid': app_pid,
            'start_time': time.time()
        }
        
        self.logger.debug(f"Started background tree loading task: {task_id}")
        return task_id
    
    def get_background_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get status of a background task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Dictionary with task status information
        """
        if task_id not in self.background_tasks:
            return {'status': 'not_found'}
        
        task_info = self.background_tasks[task_id]
        future = task_info['future']
        
        status = {
            'task_id': task_id,
            'app_name': task_info['app_name'],
            'app_pid': task_info['app_pid'],
            'start_time': task_info['start_time'],
            'elapsed_time': time.time() - task_info['start_time']
        }
        
        if future.done():
            try:
                result = future.result()
                status['status'] = 'completed'
                status['success'] = result
                # Clean up completed task
                del self.background_tasks[task_id]
            except Exception as e:
                status['status'] = 'failed'
                status['error'] = str(e)
                del self.background_tasks[task_id]
        else:
            status['status'] = 'running'
        
        return status
    
    def start_predictive_caching(self, app_name: str, app_pid: int) -> str:
        """
        Start predictive caching for common UI patterns.
        
        Args:
            app_name: Application name
            app_pid: Application process ID
            
        Returns:
            Task ID for tracking the predictive caching operation
        """
        if not self.predictive_cache_enabled:
            return ""
        
        task_id = f"predictive_{app_name}_{app_pid}_{int(time.time())}"
        
        def predictive_cache():
            """Background task for predictive element caching."""
            try:
                self.logger.debug(f"Starting predictive caching for {app_name}")
                
                # Get cached elements or load fresh
                cached_elements = self._get_cached_elements(app_name, app_pid)
                if not cached_elements:
                    # Load tree first
                    if not self.preload_active_application_tree():
                        return False
                    cached_elements = self._get_cached_elements(app_name, app_pid)
                
                if not cached_elements:
                    return False
                
                # Pre-search for common UI patterns
                pattern_matches = {}
                for pattern in self.common_ui_patterns:
                    role = pattern['role']
                    for label in pattern['labels']:
                        matches = self._search_cached_elements(app_name, app_pid, role, label)
                        if matches:
                            pattern_key = f"{role}:{label}"
                            pattern_matches[pattern_key] = len(matches)
                
                self.logger.debug(f"Predictive caching found {len(pattern_matches)} pattern matches for {app_name}")
                return True
                
            except Exception as e:
                self.logger.debug(f"Predictive caching failed for {app_name}: {e}")
                return False
        
        # Submit predictive caching task
        future = self.preload_thread_pool.submit(predictive_cache)
        self.preload_tasks[task_id] = {
            'future': future,
            'app_name': app_name,
            'app_pid': app_pid,
            'start_time': time.time()
        }
        
        self.logger.debug(f"Started predictive caching task: {task_id}")
        return task_id
    
    def cleanup_background_tasks(self):
        """Clean up completed or failed background tasks."""
        completed_tasks = []
        
        # Check background loading tasks
        for task_id, task_info in self.background_tasks.items():
            if task_info['future'].done():
                completed_tasks.append(task_id)
        
        for task_id in completed_tasks:
            del self.background_tasks[task_id]
        
        # Check preload tasks
        completed_preload_tasks = []
        for task_id, task_info in self.preload_tasks.items():
            if task_info['future'].done():
                completed_preload_tasks.append(task_id)
        
        for task_id in completed_preload_tasks:
            del self.preload_tasks[task_id]
        
        if completed_tasks or completed_preload_tasks:
            self.logger.debug(f"Cleaned up {len(completed_tasks)} background tasks and {len(completed_preload_tasks)} preload tasks")
    
    def get_parallel_processing_stats(self) -> Dict[str, Any]:
        """
        Get statistics about parallel processing operations.
        
        Returns:
            Dictionary with parallel processing statistics
        """
        return {
            'parallel_processing_enabled': self.parallel_processing_enabled,
            'predictive_cache_enabled': self.predictive_cache_enabled,
            'active_background_tasks': len(self.background_tasks),
            'active_preload_tasks': len(self.preload_tasks),
            'background_thread_pool_size': self.background_thread_pool._max_workers,
            'preload_thread_pool_size': self.preload_thread_pool._max_workers,
            'common_ui_patterns_count': len(self.common_ui_patterns)
        }
    
    def configure_parallel_processing(self, 
                                    enabled: Optional[bool] = None,
                                    predictive_cache: Optional[bool] = None,
                                    max_background_workers: Optional[int] = None):
        """
        Configure parallel processing settings.
        
        Args:
            enabled: Enable/disable parallel processing
            predictive_cache: Enable/disable predictive caching
            max_background_workers: Maximum number of background worker threads
        """
        if enabled is not None:
            self.parallel_processing_enabled = enabled
            self.logger.info(f"Parallel processing {'enabled' if enabled else 'disabled'}")
        
        if predictive_cache is not None:
            self.predictive_cache_enabled = predictive_cache
            self.logger.info(f"Predictive caching {'enabled' if predictive_cache else 'disabled'}")
        
        if max_background_workers is not None:
            # Shutdown existing pool and create new one
            old_pool = self.background_thread_pool
            self.background_thread_pool = concurrent.futures.ThreadPoolExecutor(
                max_workers=max_background_workers,
                thread_name_prefix="accessibility_bg"
            )
            old_pool.shutdown(wait=False)
            self.logger.info(f"Background thread pool resized to {max_background_workers} workers")
    
    def shutdown_parallel_processing(self):
        """Shutdown parallel processing thread pools."""
        try:
            self.background_thread_pool.shutdown(wait=True)
            self.preload_thread_pool.shutdown(wait=True)
            self.logger.info("Parallel processing thread pools shut down")
        except Exception as e:
            self.logger.warning(f"Error shutting down thread pools: {e}")
    
    def __del__(self):
        """Cleanup when module is destroyed."""
        try:
            self.shutdown_parallel_processing()
        except Exception:
            pass  # Ignore errors during cleanup