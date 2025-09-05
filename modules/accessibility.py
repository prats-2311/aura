"""
AccessibilityModule for AURA - Fast Path GUI Element Detection

This module provides high-speed, non-visual interface for querying macOS UI elements
using the Accessibility API, enabling near-instantaneous GUI automation.
"""

import logging
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import re
import threading
from collections import defaultdict
import concurrent.futures
import asyncio
from functools import partial

try:
    import AppKit
    from AppKit import NSWorkspace, NSApplication
    import Accessibility
    ACCESSIBILITY_AVAILABLE = True
except ImportError as e:
    ACCESSIBILITY_AVAILABLE = False
    logging.warning(f"Accessibility frameworks not available: {e}")

# Import accessibility functions
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
            focused_app_ref = AppKit.AXUIElementCopyAttributeValue(
                system_wide, 
                AppKit.kAXFocusedApplicationAttribute, 
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
    
    def find_element_enhanced(self, role: str, label: str, app_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Enhanced element finding with multi-role detection and backward compatibility.
        
        Args:
            role: Accessibility role (e.g., 'AXButton', 'AXMenuItem') or empty for broader search
            label: Element label or title
            app_name: Optional application name to limit search scope
        
        Returns:
            Dictionary with element details or None if not found
        """
        # Check if enhanced features are available
        if not self.is_enhanced_role_detection_available():
            self.logger.info("Enhanced role detection not available, falling back to original implementation")
            return self._find_element_original_fallback(role, label, app_name)
        
        try:
            # First attempt: Enhanced role detection
            result = self._find_element_with_enhanced_roles(role, label, app_name)
            if result:
                self.logger.debug(f"Enhanced role detection succeeded for {role} '{label}'")
                return result
            
            # Fallback: Original button-only detection for backward compatibility
            if not role or role.lower() in ['button', 'clickable']:
                self.logger.debug(f"Falling back to button-only detection for '{label}'")
                result = self._find_element_button_only_fallback(label, app_name)
                if result:
                    self.logger.debug(f"Button-only fallback succeeded for '{label}'")
                    return result
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Enhanced element detection failed: {e}")
            # Final fallback to original method
            return self._find_element_original_fallback(role, label, app_name)
    
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
            result = self.find_element_enhanced(role, label, app_name)
            if result:
                return result
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
                    return AppKit.AXUIElementCreateApplication(pid)
        
        # Default to focused application
        return self._get_focused_application_element()
    
    def _extract_element_info(self, element) -> Optional[Dict[str, Any]]:
        """Extract information from an accessibility element."""
        try:
            info = {'element': element}
            
            # Get role
            role_result = AppKit.AXUIElementCopyAttributeValue(
                element, AppKit.kAXRoleAttribute, None
            )
            if role_result[0] == 0:
                info['role'] = role_result[1]
            
            # Get title/label
            title_result = AppKit.AXUIElementCopyAttributeValue(
                element, AppKit.kAXTitleAttribute, None
            )
            if title_result[0] == 0:
                info['title'] = title_result[1]
            
            # Try alternative label attributes if title is empty
            if not info.get('title'):
                label_result = AppKit.AXUIElementCopyAttributeValue(
                    element, AppKit.kAXDescriptionAttribute, None
                )
                if label_result[0] == 0:
                    info['title'] = label_result[1]
            
            # Get enabled state
            enabled_result = AppKit.AXUIElementCopyAttributeValue(
                element, AppKit.kAXEnabledAttribute, None
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
            children_result = AppKit.AXUIElementCopyAttributeValue(
                element, AppKit.kAXChildrenAttribute, None
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
            position_result = AppKit.AXUIElementCopyAttributeValue(
                element, AppKit.kAXPositionAttribute, None
            )
            if position_result[0] != 0:
                return None
            
            # Get size
            size_result = AppKit.AXUIElementCopyAttributeValue(
                element, AppKit.kAXSizeAttribute, None
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
            title_result = AppKit.AXUIElementCopyAttributeValue(
                app_element, AppKit.kAXTitleAttribute, None
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
        Check if element text matches target using multi-attribute checking.
        
        Examines multiple accessibility attributes in priority order:
        AXTitle, AXDescription, AXValue. Returns on first successful match.
        
        Args:
            element: Accessibility element to check
            target_text: Text to match against
        
        Returns:
            Tuple of (match_found, confidence_score, matched_attribute)
        """
        if not element or not target_text:
            return False, 0.0, ""
        
        target_normalized = self._normalize_text(target_text)
        if not target_normalized:
            return False, 0.0, ""
        
        # Check each attribute in priority order
        for attribute in self.ACCESSIBILITY_ATTRIBUTES:
            try:
                # Get attribute value from element
                attribute_result = AppKit.AXUIElementCopyAttributeValue(
                    element, attribute, None
                )
                
                if attribute_result[0] == 0 and attribute_result[1]:
                    attribute_value = str(attribute_result[1])
                    
                    if attribute_value:
                        # Calculate match score for this attribute
                        match_score = self._calculate_match_score(attribute_value, target_text)
                        
                        # Return first successful match (score > 0.5)
                        if match_score > 0.5:
                            self.logger.debug(f"Multi-attribute match found: {attribute}='{attribute_value}' matches '{target_text}' (score: {match_score:.2f})")
                            return True, match_score, attribute
                        
                        self.logger.debug(f"Attribute {attribute}='{attribute_value}' low match score: {match_score:.2f}")
                
            except Exception as e:
                # Log attribute access error but continue with next attribute
                self.logger.debug(f"Error accessing attribute {attribute}: {e}")
                continue
        
        # No successful matches found
        self.logger.debug(f"No multi-attribute matches found for '{target_text}'")
        return False, 0.0, ""
    
    def _is_text_field_editable(self, element) -> bool:
        """Check if a text field is editable."""
        try:
            # Check if element has editable attribute
            editable_result = AppKit.AXUIElementCopyAttributeValue(
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