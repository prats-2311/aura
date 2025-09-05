"""
Application Detection Module for AURA - Application-Specific Detection Strategies

This module provides application type detection and adaptive search strategies
for different types of applications (web browsers, native apps, system applications).
"""

import logging
import time
from typing import Dict, Any, Optional, List, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import re

# Import AppKit for application management
try:
    from AppKit import NSWorkspace, NSRunningApplication
    APPKIT_AVAILABLE = True
except ImportError as e:
    APPKIT_AVAILABLE = False
    logging.warning(f"AppKit framework not available: {e}")

# Import ApplicationServices for process information
try:
    from ApplicationServices import (
        AXUIElementCreateApplication,
        AXUIElementCopyAttributeValue,
        kAXTitleAttribute
    )
    ACCESSIBILITY_FUNCTIONS_AVAILABLE = True
except ImportError:
    ACCESSIBILITY_FUNCTIONS_AVAILABLE = False
    logging.warning("ApplicationServices not available for application detection")


class ApplicationType(Enum):
    """Types of applications with different accessibility characteristics."""
    WEB_BROWSER = "web_browser"
    NATIVE_APP = "native_app"
    SYSTEM_APP = "system_app"
    ELECTRON_APP = "electron_app"
    JAVA_APP = "java_app"
    UNKNOWN = "unknown"


class BrowserType(Enum):
    """Specific browser types with unique accessibility patterns."""
    CHROME = "chrome"
    SAFARI = "safari"
    FIREFOX = "firefox"
    EDGE = "edge"
    UNKNOWN_BROWSER = "unknown_browser"


@dataclass
class DetectionStrategy:
    """Detection strategy configuration for specific application types."""
    app_type: ApplicationType
    browser_type: Optional[BrowserType] = None
    
    # Search parameters
    preferred_roles: List[str] = field(default_factory=list)
    fallback_roles: List[str] = field(default_factory=list)
    search_attributes: List[str] = field(default_factory=list)
    
    # Timing and performance
    timeout_ms: int = 2000
    max_depth: int = 10
    cache_ttl: int = 30
    
    # Fuzzy matching
    fuzzy_threshold: float = 0.8
    fuzzy_enabled: bool = True
    
    # Browser-specific settings
    handle_frames: bool = False
    handle_tabs: bool = False
    web_content_detection: bool = False
    
    # Performance optimizations
    parallel_search: bool = False
    early_termination: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert strategy to dictionary for logging."""
        return {
            'app_type': self.app_type.value,
            'browser_type': self.browser_type.value if self.browser_type else None,
            'preferred_roles': self.preferred_roles,
            'fallback_roles': self.fallback_roles,
            'search_attributes': self.search_attributes,
            'timeout_ms': self.timeout_ms,
            'max_depth': self.max_depth,
            'fuzzy_threshold': self.fuzzy_threshold,
            'fuzzy_enabled': self.fuzzy_enabled,
            'handle_frames': self.handle_frames,
            'handle_tabs': self.handle_tabs,
            'web_content_detection': self.web_content_detection,
            'parallel_search': self.parallel_search,
            'early_termination': self.early_termination
        }


@dataclass
class ApplicationInfo:
    """Information about a detected application."""
    name: str
    bundle_id: str
    process_id: int
    app_type: ApplicationType
    browser_type: Optional[BrowserType] = None
    version: Optional[str] = None
    accessibility_enabled: bool = True
    detection_confidence: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            'name': self.name,
            'bundle_id': self.bundle_id,
            'process_id': self.process_id,
            'app_type': self.app_type.value,
            'browser_type': self.browser_type.value if self.browser_type else None,
            'version': self.version,
            'accessibility_enabled': self.accessibility_enabled,
            'detection_confidence': self.detection_confidence
        }


@dataclass
class SearchParameters:
    """Adaptive search parameters based on application type."""
    roles: List[str]
    attributes: List[str]
    timeout_ms: int
    max_depth: int
    fuzzy_threshold: float
    parallel_search: bool
    early_termination: bool
    
    # Browser-specific parameters
    search_frames: bool = False
    search_tabs: bool = False
    web_content_only: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            'roles': self.roles,
            'attributes': self.attributes,
            'timeout_ms': self.timeout_ms,
            'max_depth': self.max_depth,
            'fuzzy_threshold': self.fuzzy_threshold,
            'parallel_search': self.parallel_search,
            'early_termination': self.early_termination,
            'search_frames': self.search_frames,
            'search_tabs': self.search_tabs,
            'web_content_only': self.web_content_only
        }


class ApplicationDetector:
    """
    Detects application types and provides adaptive detection strategies.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the application detector.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Cache for application information
        self._app_cache: Dict[str, ApplicationInfo] = {}
        self._strategy_cache: Dict[str, DetectionStrategy] = {}
        
        # Initialize application type mappings
        self._init_application_mappings()
        
        # Initialize detection strategies
        self._init_detection_strategies()
        
        self.logger.info("ApplicationDetector initialized")
    
    def _init_application_mappings(self):
        """Initialize mappings for application type detection."""
        
        # Bundle ID patterns for different application types
        self.bundle_patterns = {
            # Web browsers
            ApplicationType.WEB_BROWSER: {
                'com.google.Chrome': BrowserType.CHROME,
                'com.apple.Safari': BrowserType.SAFARI,
                'org.mozilla.firefox': BrowserType.FIREFOX,
                'com.microsoft.edgemac': BrowserType.EDGE,
            },
            
            # System applications
            ApplicationType.SYSTEM_APP: [
                'com.apple.finder',
                'com.apple.systempreferences',
                'com.apple.ActivityMonitor',
                'com.apple.Console',
                'com.apple.Terminal',
                'com.apple.dock',
                'com.apple.controlcenter'
            ],
            
            # Electron applications (common patterns)
            ApplicationType.ELECTRON_APP: [
                'com.microsoft.VSCode',
                'com.slack.Slack',
                'com.spotify.client',
                'com.github.atom',
                'com.discord.Discord',
                'com.figma.Desktop'
            ],
            
            # Java applications (common patterns)
            ApplicationType.JAVA_APP: [
                'com.jetbrains.intellij',
                'org.eclipse.platform.ide',
                'com.oracle.jdeveloper'
            ]
        }
        
        # Process name patterns for additional detection
        self.process_patterns = {
            ApplicationType.WEB_BROWSER: [
                r'.*Chrome.*',
                r'.*Safari.*',
                r'.*Firefox.*',
                r'.*Edge.*'
            ],
            ApplicationType.ELECTRON_APP: [
                r'.*Electron.*',
                r'.*Helper.*'  # Many Electron apps use helper processes
            ],
            ApplicationType.JAVA_APP: [
                r'.*java.*',
                r'.*JavaApplicationStub.*'
            ]
        }
    
    def _init_detection_strategies(self):
        """Initialize detection strategies for different application types."""
        
        # Web browser strategy
        self.browser_strategy = DetectionStrategy(
            app_type=ApplicationType.WEB_BROWSER,
            preferred_roles=['AXButton', 'AXLink', 'AXTextField', 'AXStaticText'],
            fallback_roles=['AXGroup', 'AXGenericElement', 'AXUnknown'],
            search_attributes=['AXTitle', 'AXDescription', 'AXValue', 'AXHelp'],
            timeout_ms=3000,  # Longer timeout for web content
            max_depth=15,     # Deeper search for web content
            fuzzy_threshold=0.75,  # Lower threshold for web content
            handle_frames=True,
            handle_tabs=True,
            web_content_detection=True,
            parallel_search=True
        )
        
        # Native app strategy
        self.native_strategy = DetectionStrategy(
            app_type=ApplicationType.NATIVE_APP,
            preferred_roles=['AXButton', 'AXMenuItem', 'AXTextField', 'AXStaticText'],
            fallback_roles=['AXGroup', 'AXWindow'],
            search_attributes=['AXTitle', 'AXDescription', 'AXValue'],
            timeout_ms=2000,
            max_depth=10,
            fuzzy_threshold=0.8,
            parallel_search=False,
            early_termination=True
        )
        
        # System app strategy
        self.system_strategy = DetectionStrategy(
            app_type=ApplicationType.SYSTEM_APP,
            preferred_roles=['AXButton', 'AXMenuItem', 'AXCheckBox', 'AXPopUpButton'],
            fallback_roles=['AXGroup', 'AXWindow', 'AXToolbar'],
            search_attributes=['AXTitle', 'AXDescription'],
            timeout_ms=1500,  # Faster for system apps
            max_depth=8,
            fuzzy_threshold=0.85,  # Higher threshold for system apps
            parallel_search=False,
            early_termination=True
        )
        
        # Electron app strategy
        self.electron_strategy = DetectionStrategy(
            app_type=ApplicationType.ELECTRON_APP,
            preferred_roles=['AXButton', 'AXLink', 'AXTextField', 'AXStaticText'],
            fallback_roles=['AXGroup', 'AXGenericElement'],
            search_attributes=['AXTitle', 'AXDescription', 'AXValue'],
            timeout_ms=2500,
            max_depth=12,
            fuzzy_threshold=0.78,
            web_content_detection=True,  # Electron apps use web content
            parallel_search=True
        )
        
        # Java app strategy
        self.java_strategy = DetectionStrategy(
            app_type=ApplicationType.JAVA_APP,
            preferred_roles=['AXButton', 'AXMenuItem', 'AXTextField', 'AXList'],
            fallback_roles=['AXGroup', 'AXWindow', 'AXScrollArea'],
            search_attributes=['AXTitle', 'AXDescription', 'AXValue'],
            timeout_ms=2000,
            max_depth=10,
            fuzzy_threshold=0.82,
            parallel_search=False
        )
        
        # Default/unknown strategy
        self.default_strategy = DetectionStrategy(
            app_type=ApplicationType.UNKNOWN,
            preferred_roles=['AXButton', 'AXMenuItem', 'AXTextField', 'AXStaticText'],
            fallback_roles=['AXGroup', 'AXWindow', 'AXGenericElement'],
            search_attributes=['AXTitle', 'AXDescription', 'AXValue'],
            timeout_ms=2000,
            max_depth=10,
            fuzzy_threshold=0.8,
            parallel_search=False
        )
    
    def detect_application_type(self, app_name: str) -> ApplicationInfo:
        """
        Detect application type and characteristics.
        
        Args:
            app_name: Name of the application
            
        Returns:
            ApplicationInfo with detected type and characteristics
        """
        start_time = time.time()
        
        # Check cache first
        if app_name in self._app_cache:
            cached_info = self._app_cache[app_name]
            self.logger.debug(f"Using cached application info for {app_name}: {cached_info.app_type.value}")
            return cached_info
        
        try:
            # Get running application information
            app_info = self._get_application_info(app_name)
            if not app_info:
                # Create default info for unknown application
                app_info = ApplicationInfo(
                    name=app_name,
                    bundle_id="unknown",
                    process_id=0,
                    app_type=ApplicationType.UNKNOWN,
                    detection_confidence=0.5
                )
            
            # Detect application type based on bundle ID and process name
            app_type, browser_type, confidence = self._classify_application(app_info)
            
            # Update application info with detected type
            app_info.app_type = app_type
            app_info.browser_type = browser_type
            app_info.detection_confidence = confidence
            
            # Cache the result
            self._app_cache[app_name] = app_info
            
            detection_time = (time.time() - start_time) * 1000
            self.logger.info(
                f"Detected application type for {app_name}: {app_type.value} "
                f"(confidence: {confidence:.2f}, time: {detection_time:.1f}ms)"
            )
            
            return app_info
            
        except Exception as e:
            self.logger.error(f"Error detecting application type for {app_name}: {e}")
            # Return default info on error
            return ApplicationInfo(
                name=app_name,
                bundle_id="unknown",
                process_id=0,
                app_type=ApplicationType.UNKNOWN,
                detection_confidence=0.1
            )
    
    def _get_application_info(self, app_name: str) -> Optional[ApplicationInfo]:
        """
        Get detailed application information from the system.
        
        Args:
            app_name: Name of the application
            
        Returns:
            ApplicationInfo if found, None otherwise
        """
        if not APPKIT_AVAILABLE:
            self.logger.warning("AppKit not available, cannot get application info")
            return None
        
        try:
            workspace = NSWorkspace.sharedWorkspace()
            running_apps = workspace.runningApplications()
            
            for app in running_apps:
                if app.localizedName() == app_name or app.bundleIdentifier() == app_name:
                    return ApplicationInfo(
                        name=app.localizedName() or app_name,
                        bundle_id=app.bundleIdentifier() or "unknown",
                        process_id=app.processIdentifier(),
                        app_type=ApplicationType.UNKNOWN,  # Will be determined later
                        version=self._get_app_version(app),
                        accessibility_enabled=True  # Assume true, will be validated elsewhere
                    )
            
            self.logger.debug(f"Application {app_name} not found in running applications")
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting application info for {app_name}: {e}")
            return None
    
    def _get_app_version(self, app) -> Optional[str]:
        """Get application version if available."""
        try:
            bundle = app.bundleURL()
            if bundle:
                info_dict = bundle.resourceValuesForKeys_error_([
                    'NSBundleShortVersionString'
                ], None)[0]
                return info_dict.get('NSBundleShortVersionString')
        except:
            pass
        return None
    
    def _classify_application(self, app_info: ApplicationInfo) -> Tuple[ApplicationType, Optional[BrowserType], float]:
        """
        Classify application based on bundle ID and other characteristics.
        
        Args:
            app_info: Application information
            
        Returns:
            Tuple of (ApplicationType, BrowserType, confidence_score)
        """
        bundle_id = app_info.bundle_id.lower()
        app_name = app_info.name.lower()
        
        # If bundle_id is unknown, we have limited information
        if bundle_id == "unknown":
            # Try to classify based on name patterns only
            for app_type, patterns in self.process_patterns.items():
                for pattern in patterns:
                    if re.match(pattern, app_name, re.IGNORECASE):
                        browser_type = None
                        if app_type == ApplicationType.WEB_BROWSER:
                            browser_type = self._detect_browser_type_from_name(app_name)
                        return app_type, browser_type, 0.6
            
            # Check for browser patterns in name
            if any(browser in app_name for browser in ['chrome', 'safari', 'firefox', 'edge']):
                browser_type = self._detect_browser_type_from_name(app_name)
                return ApplicationType.WEB_BROWSER, browser_type, 0.75
            
            # If we can't classify, return unknown
            return ApplicationType.UNKNOWN, None, 0.3
        
        # Check web browsers first
        browser_mappings = self.bundle_patterns[ApplicationType.WEB_BROWSER]
        for pattern, browser_type in browser_mappings.items():
            if pattern.lower() in bundle_id:
                return ApplicationType.WEB_BROWSER, browser_type, 0.95
        
        # Check for browser patterns in name
        if any(browser in app_name for browser in ['chrome', 'safari', 'firefox', 'edge']):
            browser_type = self._detect_browser_type_from_name(app_name)
            return ApplicationType.WEB_BROWSER, browser_type, 0.85
        
        # Check system applications
        system_patterns = self.bundle_patterns[ApplicationType.SYSTEM_APP]
        for pattern in system_patterns:
            if pattern.lower() in bundle_id:
                return ApplicationType.SYSTEM_APP, None, 0.95
        
        # Check Electron applications
        electron_patterns = self.bundle_patterns[ApplicationType.ELECTRON_APP]
        for pattern in electron_patterns:
            if pattern.lower() in bundle_id:
                return ApplicationType.ELECTRON_APP, None, 0.90
        
        # Check Java applications
        java_patterns = self.bundle_patterns[ApplicationType.JAVA_APP]
        for pattern in java_patterns:
            if pattern.lower() in bundle_id:
                return ApplicationType.JAVA_APP, None, 0.90
        
        # Check process name patterns
        for app_type, patterns in self.process_patterns.items():
            for pattern in patterns:
                if re.match(pattern, app_name, re.IGNORECASE):
                    browser_type = None
                    if app_type == ApplicationType.WEB_BROWSER:
                        browser_type = self._detect_browser_type_from_name(app_name)
                    return app_type, browser_type, 0.75
        
        # Default to native app if we have a valid bundle ID
        return ApplicationType.NATIVE_APP, None, 0.6
    
    def _detect_browser_type_from_name(self, app_name: str) -> BrowserType:
        """Detect browser type from application name."""
        app_name = app_name.lower()
        if 'chrome' in app_name:
            return BrowserType.CHROME
        elif 'safari' in app_name:
            return BrowserType.SAFARI
        elif 'firefox' in app_name:
            return BrowserType.FIREFOX
        elif 'edge' in app_name:
            return BrowserType.EDGE
        else:
            return BrowserType.UNKNOWN_BROWSER
    
    def get_detection_strategy(self, app_info: ApplicationInfo) -> DetectionStrategy:
        """
        Get optimal detection strategy for application.
        
        Args:
            app_info: Application information
            
        Returns:
            DetectionStrategy optimized for the application type
        """
        cache_key = f"{app_info.app_type.value}_{app_info.browser_type.value if app_info.browser_type else 'none'}"
        
        # Check cache first
        if cache_key in self._strategy_cache:
            return self._strategy_cache[cache_key]
        
        # Select base strategy
        if app_info.app_type == ApplicationType.WEB_BROWSER:
            strategy = self._get_browser_strategy(app_info.browser_type)
        elif app_info.app_type == ApplicationType.SYSTEM_APP:
            strategy = self.system_strategy
        elif app_info.app_type == ApplicationType.ELECTRON_APP:
            strategy = self.electron_strategy
        elif app_info.app_type == ApplicationType.JAVA_APP:
            strategy = self.java_strategy
        else:
            strategy = self.default_strategy
        
        # Customize strategy based on specific application
        customized_strategy = self._customize_strategy(strategy, app_info)
        
        # Cache the strategy
        self._strategy_cache[cache_key] = customized_strategy
        
        self.logger.debug(f"Selected detection strategy for {app_info.name}: {customized_strategy.app_type.value}")
        
        return customized_strategy
    
    def _get_browser_strategy(self, browser_type: Optional[BrowserType]) -> DetectionStrategy:
        """Get browser-specific strategy."""
        base_strategy = self.browser_strategy
        
        if browser_type == BrowserType.CHROME:
            # Chrome-specific optimizations
            base_strategy.preferred_roles = ['AXButton', 'AXLink', 'AXTextField', 'AXStaticText', 'AXGenericElement']
            base_strategy.timeout_ms = 3500  # Chrome can be slower
            base_strategy.fuzzy_threshold = 0.72  # Chrome has more dynamic content
        elif browser_type == BrowserType.SAFARI:
            # Safari-specific optimizations
            base_strategy.preferred_roles = ['AXButton', 'AXLink', 'AXTextField', 'AXStaticText']
            base_strategy.timeout_ms = 2500
            base_strategy.fuzzy_threshold = 0.78
        elif browser_type == BrowserType.FIREFOX:
            # Firefox-specific optimizations
            base_strategy.preferred_roles = ['AXButton', 'AXLink', 'AXTextField', 'AXStaticText']
            base_strategy.timeout_ms = 3000
            base_strategy.fuzzy_threshold = 0.75
        
        return base_strategy
    
    def _customize_strategy(self, base_strategy: DetectionStrategy, app_info: ApplicationInfo) -> DetectionStrategy:
        """
        Customize strategy based on specific application characteristics.
        
        Args:
            base_strategy: Base detection strategy
            app_info: Application information
            
        Returns:
            Customized detection strategy
        """
        # Create a copy of the base strategy
        customized = DetectionStrategy(
            app_type=base_strategy.app_type,
            browser_type=base_strategy.browser_type,
            preferred_roles=base_strategy.preferred_roles.copy(),
            fallback_roles=base_strategy.fallback_roles.copy(),
            search_attributes=base_strategy.search_attributes.copy(),
            timeout_ms=base_strategy.timeout_ms,
            max_depth=base_strategy.max_depth,
            cache_ttl=base_strategy.cache_ttl,
            fuzzy_threshold=base_strategy.fuzzy_threshold,
            fuzzy_enabled=base_strategy.fuzzy_enabled,
            handle_frames=base_strategy.handle_frames,
            handle_tabs=base_strategy.handle_tabs,
            web_content_detection=base_strategy.web_content_detection,
            parallel_search=base_strategy.parallel_search,
            early_termination=base_strategy.early_termination
        )
        
        # Apply application-specific customizations
        if app_info.name.lower() in ['mail', 'messages']:
            # Mail and Messages apps have specific UI patterns
            customized.preferred_roles.insert(0, 'AXOutline')  # For message lists
            customized.search_attributes.append('AXRoleDescription')
        elif app_info.name.lower() in ['finder']:
            # Finder has specific navigation patterns
            customized.preferred_roles.extend(['AXOutline', 'AXTable', 'AXColumn'])
            customized.max_depth = 12  # Finder can have deep hierarchies
        elif app_info.name.lower() in ['terminal']:
            # Terminal has text-based interface
            customized.preferred_roles = ['AXStaticText', 'AXTextField', 'AXButton']
            customized.fuzzy_threshold = 0.9  # Terminal text should be exact
        
        return customized
    
    def adapt_search_parameters(self, app_info: ApplicationInfo, command: str) -> SearchParameters:
        """
        Adapt search parameters for specific application and command.
        
        Args:
            app_info: Application information
            command: User command
            
        Returns:
            Optimized search parameters
        """
        strategy = self.get_detection_strategy(app_info)
        
        # Extract command type and target
        command_lower = command.lower()
        
        # Determine search parameters based on command type
        if 'click' in command_lower:
            roles = strategy.preferred_roles
            if 'button' in command_lower:
                roles = ['AXButton'] + [r for r in roles if r != 'AXButton']
            elif 'link' in command_lower:
                roles = ['AXLink'] + [r for r in roles if r != 'AXLink']
        elif 'type' in command_lower or 'enter' in command_lower:
            roles = ['AXTextField', 'AXTextArea'] + strategy.preferred_roles
        elif 'select' in command_lower:
            roles = ['AXPopUpButton', 'AXComboBox', 'AXList'] + strategy.preferred_roles
        else:
            roles = strategy.preferred_roles
        
        # Add fallback roles
        all_roles = roles + [r for r in strategy.fallback_roles if r not in roles]
        
        # Browser-specific adaptations
        search_frames = strategy.handle_frames
        search_tabs = strategy.handle_tabs
        web_content_only = False
        
        if app_info.app_type == ApplicationType.WEB_BROWSER:
            # For web browsers, adapt based on command context
            if any(web_term in command_lower for web_term in ['search', 'google', 'website', 'page']):
                web_content_only = True
                search_frames = True
        
        return SearchParameters(
            roles=all_roles,
            attributes=strategy.search_attributes,
            timeout_ms=strategy.timeout_ms,
            max_depth=strategy.max_depth,
            fuzzy_threshold=strategy.fuzzy_threshold,
            parallel_search=strategy.parallel_search,
            early_termination=strategy.early_termination,
            search_frames=search_frames,
            search_tabs=search_tabs,
            web_content_only=web_content_only
        )
    
    def clear_cache(self):
        """Clear application and strategy caches."""
        self._app_cache.clear()
        self._strategy_cache.clear()
        self.logger.info("Application detector caches cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            'app_cache_size': len(self._app_cache),
            'strategy_cache_size': len(self._strategy_cache),
            'cached_applications': list(self._app_cache.keys())
        }