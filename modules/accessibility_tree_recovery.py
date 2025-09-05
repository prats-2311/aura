# modules/accessibility_tree_recovery.py
"""
Accessibility Tree Recovery and Refresh Mechanisms for AURA

Provides intelligent accessibility tree recovery, refresh mechanisms,
application focus detection, and element cache invalidation for
dynamic applications.
"""

import logging
import time
import threading
from typing import Dict, Any, Optional, List, Callable, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import weakref

# Import accessibility-specific modules
from .accessibility import (
    AccessibilityElement,
    CachedElementTree,
    AccessibilityPermissionError,
    AccessibilityTreeTraversalError,
    ElementNotFoundError
)

try:
    from AppKit import NSWorkspace, NSApplication, NSNotificationCenter
    APPKIT_AVAILABLE = True
except ImportError:
    APPKIT_AVAILABLE = False
    logging.warning("AppKit framework not available for application focus detection")


class TreeRefreshTrigger(Enum):
    """Triggers for accessibility tree refresh."""
    MANUAL = "manual"
    STALE_ELEMENT = "stale_element"
    APPLICATION_FOCUS_CHANGE = "application_focus_change"
    CACHE_EXPIRY = "cache_expiry"
    ELEMENT_NOT_FOUND = "element_not_found"
    TREE_TRAVERSAL_ERROR = "tree_traversal_error"
    PERIODIC_REFRESH = "periodic_refresh"


class TreeRefreshResult(Enum):
    """Results of tree refresh operations."""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILED = "failed"
    NO_CHANGE = "no_change"
    PERMISSION_DENIED = "permission_denied"


@dataclass
class TreeRefreshEvent:
    """Information about a tree refresh event."""
    trigger: TreeRefreshTrigger
    app_name: str
    app_pid: int
    timestamp: float
    result: TreeRefreshResult
    elements_before: int
    elements_after: int
    refresh_duration: float
    error: Optional[Exception] = None
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ApplicationFocusState:
    """State information for application focus tracking."""
    app_name: str
    app_pid: int
    bundle_id: str
    focus_timestamp: float
    previous_app: Optional[str] = None
    focus_duration: float = 0.0
    
    def update_focus_duration(self) -> None:
        """Update the focus duration based on current time."""
        self.focus_duration = time.time() - self.focus_timestamp


@dataclass
class CacheInvalidationRule:
    """Rule for cache invalidation based on application state changes."""
    app_pattern: str  # Pattern to match application names
    trigger_events: List[str]  # Events that trigger invalidation
    max_age_seconds: float  # Maximum age before forced invalidation
    invalidate_on_focus_change: bool = True
    invalidate_on_window_change: bool = True
    
    def matches_app(self, app_name: str) -> bool:
        """Check if this rule applies to the given application."""
        import re
        return bool(re.search(self.app_pattern, app_name, re.IGNORECASE))


class AccessibilityTreeRecoveryManager:
    """
    Manages accessibility tree recovery and refresh mechanisms.
    
    Provides intelligent tree refresh when elements become stale,
    application focus detection, and cache invalidation for dynamic applications.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the AccessibilityTreeRecoveryManager.
        
        Args:
            config: Configuration dictionary for recovery behavior
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Configuration parameters
        self.auto_refresh_enabled = self.config.get('auto_refresh_enabled', True)
        self.focus_tracking_enabled = self.config.get('focus_tracking_enabled', True)
        self.cache_invalidation_enabled = self.config.get('cache_invalidation_enabled', True)
        self.periodic_refresh_interval = self.config.get('periodic_refresh_interval', 300)  # 5 minutes
        self.stale_element_threshold = self.config.get('stale_element_threshold', 30)  # 30 seconds
        self.max_refresh_attempts = self.config.get('max_refresh_attempts', 3)
        self.refresh_backoff_factor = self.config.get('refresh_backoff_factor', 1.5)
        
        # State tracking
        self.current_focus_state: Optional[ApplicationFocusState] = None
        self.focus_history: List[ApplicationFocusState] = []
        self.refresh_history: List[TreeRefreshEvent] = []
        self.cache_registry: Dict[str, CachedElementTree] = {}
        self.invalidation_rules: List[CacheInvalidationRule] = []
        self.refresh_callbacks: List[Callable[[TreeRefreshEvent], None]] = []
        
        # Threading
        self.lock = threading.RLock()
        self.focus_monitor_thread: Optional[threading.Thread] = None
        self.periodic_refresh_thread: Optional[threading.Thread] = None
        self.shutdown_event = threading.Event()
        
        # Statistics
        self.total_refreshes = 0
        self.successful_refreshes = 0
        self.failed_refreshes = 0
        
        # Initialize default invalidation rules
        self._initialize_default_invalidation_rules()
        
        # Start monitoring if enabled
        if self.focus_tracking_enabled and APPKIT_AVAILABLE:
            self._start_focus_monitoring()
        
        if self.auto_refresh_enabled:
            self._start_periodic_refresh()
        
        self.logger.info("AccessibilityTreeRecoveryManager initialized")
    
    def _initialize_default_invalidation_rules(self) -> None:
        """Initialize default cache invalidation rules for common applications."""
        default_rules = [
            # Web browsers - invalidate frequently due to dynamic content
            CacheInvalidationRule(
                app_pattern=r"(Chrome|Safari|Firefox|Edge)",
                trigger_events=["focus_change", "window_change"],
                max_age_seconds=30,
                invalidate_on_focus_change=True,
                invalidate_on_window_change=True
            ),
            # Development tools - invalidate on focus change
            CacheInvalidationRule(
                app_pattern=r"(Xcode|Visual Studio|IntelliJ|PyCharm|Sublime)",
                trigger_events=["focus_change"],
                max_age_seconds=60,
                invalidate_on_focus_change=True,
                invalidate_on_window_change=False
            ),
            # System applications - less frequent invalidation
            CacheInvalidationRule(
                app_pattern=r"(Finder|System Preferences|Activity Monitor)",
                trigger_events=["focus_change"],
                max_age_seconds=120,
                invalidate_on_focus_change=False,
                invalidate_on_window_change=False
            ),
            # Default rule for all other applications
            CacheInvalidationRule(
                app_pattern=r".*",
                trigger_events=["focus_change", "cache_expiry"],
                max_age_seconds=90,
                invalidate_on_focus_change=True,
                invalidate_on_window_change=False
            )
        ]
        
        self.invalidation_rules.extend(default_rules)
    
    def refresh_accessibility_tree(
        self,
        app_name: str,
        trigger: TreeRefreshTrigger = TreeRefreshTrigger.MANUAL,
        force: bool = False,
        context: Optional[Dict[str, Any]] = None
    ) -> TreeRefreshEvent:
        """
        Refresh the accessibility tree for a specific application.
        
        Args:
            app_name: Name of the application
            trigger: What triggered this refresh
            force: Force refresh even if cache is still valid
            context: Additional context for the refresh
            
        Returns:
            TreeRefreshEvent with refresh results
        """
        context = context or {}
        refresh_start = time.time()
        
        self.logger.debug(f"Refreshing accessibility tree for {app_name} (trigger: {trigger.value})")
        
        # Get current cache state
        cached_tree = self.cache_registry.get(app_name)
        elements_before = len(cached_tree.elements) if cached_tree else 0
        app_pid = cached_tree.app_pid if cached_tree else 0
        
        try:
            # Check if refresh is needed
            if not force and cached_tree and not cached_tree.is_expired():
                refresh_duration = time.time() - refresh_start
                event = TreeRefreshEvent(
                    trigger=trigger,
                    app_name=app_name,
                    app_pid=app_pid,
                    timestamp=refresh_start,
                    result=TreeRefreshResult.NO_CHANGE,
                    elements_before=elements_before,
                    elements_after=elements_before,
                    refresh_duration=refresh_duration,
                    context=context
                )
                
                self._record_refresh_event(event)
                return event
            
            # Perform the actual refresh
            new_tree = self._perform_tree_refresh(app_name, app_pid, context)
            
            if new_tree:
                # Update cache
                with self.lock:
                    self.cache_registry[app_name] = new_tree
                
                elements_after = len(new_tree.elements)
                refresh_duration = time.time() - refresh_start
                
                result = TreeRefreshResult.SUCCESS
                if elements_after == 0:
                    result = TreeRefreshResult.PARTIAL_SUCCESS
                
                event = TreeRefreshEvent(
                    trigger=trigger,
                    app_name=app_name,
                    app_pid=new_tree.app_pid,
                    timestamp=refresh_start,
                    result=result,
                    elements_before=elements_before,
                    elements_after=elements_after,
                    refresh_duration=refresh_duration,
                    context=context
                )
                
                self._record_refresh_event(event)
                self.logger.info(f"Successfully refreshed tree for {app_name}: {elements_after} elements")
                
                return event
            else:
                # Refresh failed
                refresh_duration = time.time() - refresh_start
                event = TreeRefreshEvent(
                    trigger=trigger,
                    app_name=app_name,
                    app_pid=app_pid,
                    timestamp=refresh_start,
                    result=TreeRefreshResult.FAILED,
                    elements_before=elements_before,
                    elements_after=0,
                    refresh_duration=refresh_duration,
                    context=context
                )
                
                self._record_refresh_event(event)
                return event
                
        except AccessibilityPermissionError as e:
            refresh_duration = time.time() - refresh_start
            event = TreeRefreshEvent(
                trigger=trigger,
                app_name=app_name,
                app_pid=app_pid,
                timestamp=refresh_start,
                result=TreeRefreshResult.PERMISSION_DENIED,
                elements_before=elements_before,
                elements_after=0,
                refresh_duration=refresh_duration,
                error=e,
                context=context
            )
            
            self._record_refresh_event(event)
            self.logger.warning(f"Permission denied refreshing tree for {app_name}: {e}")
            return event
            
        except Exception as e:
            refresh_duration = time.time() - refresh_start
            event = TreeRefreshEvent(
                trigger=trigger,
                app_name=app_name,
                app_pid=app_pid,
                timestamp=refresh_start,
                result=TreeRefreshResult.FAILED,
                elements_before=elements_before,
                elements_after=0,
                refresh_duration=refresh_duration,
                error=e,
                context=context
            )
            
            self._record_refresh_event(event)
            self.logger.error(f"Error refreshing tree for {app_name}: {e}")
            return event
    
    def _perform_tree_refresh(
        self,
        app_name: str,
        app_pid: int,
        context: Dict[str, Any]
    ) -> Optional[CachedElementTree]:
        """
        Perform the actual accessibility tree refresh.
        
        Args:
            app_name: Application name
            app_pid: Application process ID
            context: Refresh context
            
        Returns:
            New CachedElementTree or None if refresh failed
        """
        try:
            # Import here to avoid circular imports
            from modules.accessibility import AccessibilityModule
            
            # Create a temporary accessibility module instance for refresh
            accessibility = AccessibilityModule()
            
            # Get fresh accessibility tree by searching for common elements
            # This is a simplified approach - in reality we'd traverse the full tree
            elements = self._get_all_elements_for_app(accessibility, app_name)
            
            if elements:
                # Create new cached tree
                new_tree = CachedElementTree(
                    app_name=app_name,
                    app_pid=app_pid or self._get_app_pid(app_name),
                    elements=elements,
                    timestamp=time.time(),
                    ttl=self.config.get('cache_ttl', 30.0)
                )
                
                return new_tree
            else:
                self.logger.warning(f"No elements found during refresh for {app_name}")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to perform tree refresh for {app_name}: {e}")
            return None
    
    def _get_all_elements_for_app(self, accessibility: Any, app_name: str) -> List[Dict[str, Any]]:
        """
        Get all elements for an application using the accessibility module.
        
        This is a simplified implementation that would be replaced with
        actual tree traversal in a real implementation.
        
        Args:
            accessibility: AccessibilityModule instance
            app_name: Application name
            
        Returns:
            List of element dictionaries
        """
        # This is a mock implementation for testing
        # In reality, this would traverse the accessibility tree
        elements = []
        
        # Try to find common element types
        common_roles = ['button', 'text', 'link', 'window', 'menu']
        
        for role in common_roles:
            try:
                # Use the accessibility module's find_element method
                element = accessibility.find_element(role, "", app_name)
                if element:
                    elements.append(element)
            except Exception:
                # Continue if element not found
                continue
        
        return elements
    
    def invalidate_cache(
        self,
        app_name: Optional[str] = None,
        trigger: str = "manual",
        context: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Invalidate cached accessibility trees.
        
        Args:
            app_name: Specific application to invalidate (None for all)
            trigger: What triggered the invalidation
            context: Additional context
            
        Returns:
            Number of caches invalidated
        """
        context = context or {}
        invalidated_count = 0
        
        with self.lock:
            if app_name:
                # Invalidate specific application
                if app_name in self.cache_registry:
                    del self.cache_registry[app_name]
                    invalidated_count = 1
                    self.logger.debug(f"Invalidated cache for {app_name} (trigger: {trigger})")
            else:
                # Invalidate all caches
                invalidated_count = len(self.cache_registry)
                self.cache_registry.clear()
                self.logger.debug(f"Invalidated all caches (trigger: {trigger})")
        
        return invalidated_count
    
    def detect_stale_elements(self, app_name: str) -> List[str]:
        """
        Detect stale elements in the cached tree.
        
        Args:
            app_name: Application name to check
            
        Returns:
            List of stale element identifiers
        """
        cached_tree = self.cache_registry.get(app_name)
        if not cached_tree:
            return []
        
        stale_elements = []
        current_time = time.time()
        
        # Check if the entire tree is stale
        if cached_tree.is_expired():
            stale_elements.append("entire_tree")
        
        # Check individual elements for staleness indicators
        for element in cached_tree.elements:
            element_age = current_time - cached_tree.timestamp
            
            # Consider elements stale if they're older than threshold
            if element_age > self.stale_element_threshold:
                element_id = element.get('element_id', f"element_{hash(str(element))}")
                stale_elements.append(element_id)
        
        return stale_elements
    
    def _start_focus_monitoring(self) -> None:
        """Start monitoring application focus changes."""
        if not APPKIT_AVAILABLE:
            self.logger.warning("Cannot start focus monitoring: AppKit not available")
            return
        
        def focus_monitor():
            """Monitor application focus changes."""
            try:
                # Set up notification observer for application activation
                notification_center = NSNotificationCenter.defaultCenter()
                
                def handle_app_activation(notification):
                    """Handle application activation notification."""
                    try:
                        app = notification.object()
                        if app:
                            app_name = app.localizedName() or "Unknown"
                            bundle_id = app.bundleIdentifier() or "unknown.bundle"
                            app_pid = app.processIdentifier()
                            
                            self._handle_focus_change(app_name, app_pid, bundle_id)
                    except Exception as e:
                        self.logger.error(f"Error handling app activation: {e}")
                
                # Add observer
                notification_center.addObserver_selector_name_object_(
                    self, 
                    handle_app_activation,
                    "NSApplicationDidBecomeActiveNotification",
                    None
                )
                
                # Monitor loop
                while not self.shutdown_event.is_set():
                    time.sleep(1)
                    
            except Exception as e:
                self.logger.error(f"Focus monitoring error: {e}")
        
        self.focus_monitor_thread = threading.Thread(target=focus_monitor, daemon=True)
        self.focus_monitor_thread.start()
        self.logger.info("Started application focus monitoring")
    
    def _handle_focus_change(self, app_name: str, app_pid: int, bundle_id: str) -> None:
        """
        Handle application focus change.
        
        Args:
            app_name: Name of the newly focused application
            app_pid: Process ID of the application
            bundle_id: Bundle identifier of the application
        """
        current_time = time.time()
        previous_app = self.current_focus_state.app_name if self.current_focus_state else None
        
        # Update previous focus state duration
        if self.current_focus_state:
            self.current_focus_state.update_focus_duration()
            self.focus_history.append(self.current_focus_state)
        
        # Create new focus state
        self.current_focus_state = ApplicationFocusState(
            app_name=app_name,
            app_pid=app_pid,
            bundle_id=bundle_id,
            focus_timestamp=current_time,
            previous_app=previous_app
        )
        
        self.logger.debug(f"Focus changed to {app_name} (PID: {app_pid})")
        
        # Trigger cache invalidation if needed
        if self.cache_invalidation_enabled:
            self._check_invalidation_rules(app_name, "focus_change")
        
        # Trigger tree refresh if needed
        if self.auto_refresh_enabled:
            self._trigger_focus_refresh(app_name)
    
    def _check_invalidation_rules(self, app_name: str, trigger: str) -> None:
        """
        Check and apply cache invalidation rules.
        
        Args:
            app_name: Application name
            trigger: Trigger event
        """
        for rule in self.invalidation_rules:
            if rule.matches_app(app_name) and trigger in rule.trigger_events:
                if trigger == "focus_change" and rule.invalidate_on_focus_change:
                    self.invalidate_cache(app_name, trigger=f"rule_{trigger}")
                elif trigger == "window_change" and rule.invalidate_on_window_change:
                    self.invalidate_cache(app_name, trigger=f"rule_{trigger}")
                elif trigger == "cache_expiry":
                    # Check age-based invalidation
                    cached_tree = self.cache_registry.get(app_name)
                    if cached_tree and cached_tree.get_age() > rule.max_age_seconds:
                        self.invalidate_cache(app_name, trigger="rule_age_expiry")
    
    def _trigger_focus_refresh(self, app_name: str) -> None:
        """
        Trigger tree refresh on focus change.
        
        Args:
            app_name: Application name
        """
        # Check if refresh is needed
        cached_tree = self.cache_registry.get(app_name)
        if not cached_tree or cached_tree.is_expired():
            self.refresh_accessibility_tree(
                app_name,
                trigger=TreeRefreshTrigger.APPLICATION_FOCUS_CHANGE
            )
    
    def _start_periodic_refresh(self) -> None:
        """Start periodic refresh of cached trees."""
        def periodic_refresh():
            """Perform periodic refresh of all cached trees."""
            while not self.shutdown_event.is_set():
                try:
                    # Wait for the refresh interval
                    if self.shutdown_event.wait(self.periodic_refresh_interval):
                        break
                    
                    # Refresh expired caches
                    with self.lock:
                        apps_to_refresh = []
                        for app_name, cached_tree in self.cache_registry.items():
                            if cached_tree.is_expired():
                                apps_to_refresh.append(app_name)
                    
                    # Refresh expired trees
                    for app_name in apps_to_refresh:
                        self.refresh_accessibility_tree(
                            app_name,
                            trigger=TreeRefreshTrigger.PERIODIC_REFRESH
                        )
                        
                except Exception as e:
                    self.logger.error(f"Error in periodic refresh: {e}")
        
        self.periodic_refresh_thread = threading.Thread(target=periodic_refresh, daemon=True)
        self.periodic_refresh_thread.start()
        self.logger.info(f"Started periodic refresh (interval: {self.periodic_refresh_interval}s)")
    
    def _record_refresh_event(self, event: TreeRefreshEvent) -> None:
        """
        Record a refresh event for statistics and history.
        
        Args:
            event: The refresh event to record
        """
        with self.lock:
            self.refresh_history.append(event)
            self.total_refreshes += 1
            
            if event.result == TreeRefreshResult.SUCCESS:
                self.successful_refreshes += 1
            elif event.result == TreeRefreshResult.FAILED:
                self.failed_refreshes += 1
            
            # Keep only recent history (last 1000 events)
            if len(self.refresh_history) > 1000:
                self.refresh_history = self.refresh_history[-1000:]
        
        # Notify callbacks
        for callback in self.refresh_callbacks:
            try:
                callback(event)
            except Exception as e:
                self.logger.error(f"Error in refresh callback: {e}")
    
    def _get_app_pid(self, app_name: str) -> int:
        """
        Get process ID for an application.
        
        Args:
            app_name: Application name
            
        Returns:
            Process ID or 0 if not found
        """
        if not APPKIT_AVAILABLE:
            return 0
        
        try:
            workspace = NSWorkspace.sharedWorkspace()
            running_apps = workspace.runningApplications()
            
            for app in running_apps:
                if app.localizedName() == app_name:
                    return app.processIdentifier()
            
            return 0
        except Exception as e:
            self.logger.error(f"Error getting PID for {app_name}: {e}")
            return 0
    
    def add_refresh_callback(self, callback: Callable[[TreeRefreshEvent], None]) -> None:
        """
        Add a callback to be notified of refresh events.
        
        Args:
            callback: Function to call on refresh events
        """
        self.refresh_callbacks.append(callback)
    
    def remove_refresh_callback(self, callback: Callable[[TreeRefreshEvent], None]) -> None:
        """
        Remove a refresh callback.
        
        Args:
            callback: Function to remove
        """
        if callback in self.refresh_callbacks:
            self.refresh_callbacks.remove(callback)
    
    def get_refresh_statistics(self) -> Dict[str, Any]:
        """
        Get refresh statistics and performance metrics.
        
        Returns:
            Dictionary with refresh statistics
        """
        with self.lock:
            if not self.refresh_history:
                return {
                    "total_refreshes": 0,
                    "successful_refreshes": 0,
                    "failed_refreshes": 0,
                    "success_rate": 0.0,
                    "average_refresh_time": 0.0,
                    "cache_hit_rate": 0.0,
                    "recent_events": []
                }
            
            # Calculate statistics
            total_refresh_time = sum(event.refresh_duration for event in self.refresh_history)
            avg_refresh_time = total_refresh_time / len(self.refresh_history)
            
            # Calculate cache hit rate (NO_CHANGE results indicate cache hits)
            cache_hits = sum(1 for event in self.refresh_history if event.result == TreeRefreshResult.NO_CHANGE)
            cache_hit_rate = cache_hits / len(self.refresh_history) if self.refresh_history else 0.0
            
            # Get recent events
            recent_events = [
                {
                    "trigger": event.trigger.value,
                    "app_name": event.app_name,
                    "result": event.result.value,
                    "duration": event.refresh_duration,
                    "elements_after": event.elements_after,
                    "timestamp": event.timestamp
                }
                for event in self.refresh_history[-10:]
            ]
            
            return {
                "total_refreshes": self.total_refreshes,
                "successful_refreshes": self.successful_refreshes,
                "failed_refreshes": self.failed_refreshes,
                "success_rate": self.successful_refreshes / self.total_refreshes if self.total_refreshes > 0 else 0.0,
                "average_refresh_time": avg_refresh_time,
                "cache_hit_rate": cache_hit_rate,
                "cached_apps": list(self.cache_registry.keys()),
                "current_focus": self.current_focus_state.app_name if self.current_focus_state else None,
                "recent_events": recent_events
            }
    
    def shutdown(self) -> None:
        """Shutdown the recovery manager and stop all monitoring threads."""
        self.logger.info("Shutting down AccessibilityTreeRecoveryManager")
        
        # Signal shutdown
        self.shutdown_event.set()
        
        # Wait for threads to finish
        if self.focus_monitor_thread and self.focus_monitor_thread.is_alive():
            self.focus_monitor_thread.join(timeout=5)
        
        if self.periodic_refresh_thread and self.periodic_refresh_thread.is_alive():
            self.periodic_refresh_thread.join(timeout=5)
        
        # Clear caches
        with self.lock:
            self.cache_registry.clear()
            self.refresh_callbacks.clear()


# Global tree recovery manager instance
global_tree_recovery_manager = AccessibilityTreeRecoveryManager()