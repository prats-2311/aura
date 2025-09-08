"""
Application Detection Module for AURA - Application-Specific Detection Strategies

This module provides application type detection and adaptive search strategies
for different types of applications (web browsers, native apps, system applications).
"""

import logging
import time
import subprocess
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
    PDF_READER = "pdf_reader"
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
            
            # PDF readers and document viewers
            ApplicationType.PDF_READER: [
                'com.apple.Preview',
                'com.adobe.Reader',
                'com.adobe.Acrobat.Pro',
                'com.readdle.PDFExpert-Mac',
                'net.sourceforge.skim-app.skim',
                'com.smileonmymac.PDFpen',
                'com.smileonmymac.PDFpenPro',
                'com.goodreader.GoodReader',
                'com.pdfviewer.PDFViewer',
                'com.apple.iBooks',
                'com.culturedcode.ThingsMac'  # Things sometimes opens PDFs
            ],
            
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
            ApplicationType.PDF_READER: [
                r'.*Preview.*',
                r'.*Adobe.*',
                r'.*Acrobat.*',
                r'.*Reader.*',
                r'.*PDF.*',
                r'.*Skim.*',
                r'.*PDFpen.*'
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
        
        # Check PDF readers
        pdf_patterns = self.bundle_patterns[ApplicationType.PDF_READER]
        for pattern in pdf_patterns:
            if pattern.lower() in bundle_id:
                return ApplicationType.PDF_READER, None, 0.95
        
        # Check for PDF reader patterns in name
        if any(pdf_app in app_name for pdf_app in ['preview', 'adobe', 'acrobat', 'reader', 'pdf', 'skim']):
            return ApplicationType.PDF_READER, None, 0.85
        
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
    
    def get_active_application_info(self) -> Optional[ApplicationInfo]:
        """
        Get information about the currently active/focused application.
        
        This method implements robust application detection with comprehensive
        error handling and AppleScript fallback mechanisms.
        
        Returns:
            ApplicationInfo for the active application, or None if detection fails
        """
        try:
            self.logger.debug("Attempting to get active application info")
            
            # Try primary method using AppKit
            app_info = self._get_active_app_primary()
            if app_info:
                self.logger.debug(f"Primary method succeeded: {app_info.name}")
                return app_info
            
            # Fallback to AppleScript method
            self.logger.info("Primary method failed, trying AppleScript fallback")
            app_info = self._get_active_app_applescript_fallback()
            if app_info:
                self.logger.info(f"AppleScript fallback succeeded: {app_info.name}")
                return app_info
            
            # Final fallback - try to get any running application
            self.logger.warning("AppleScript fallback failed, trying final fallback")
            app_info = self._get_active_app_final_fallback()
            if app_info:
                self.logger.warning(f"Final fallback succeeded: {app_info.name}")
                return app_info
            
            self.logger.error("All application detection methods failed")
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting active application info: {e}")
            return None
    
    def _get_active_app_primary(self) -> Optional[ApplicationInfo]:
        """
        Primary method to get active application using AppKit.
        
        This method intelligently detects the user's intended active application
        by filtering out development tools and system applications.
        
        Returns:
            ApplicationInfo if successful, None otherwise
        """
        if not APPKIT_AVAILABLE:
            self.logger.debug("AppKit not available for primary detection")
            return None
        
        try:
            workspace = NSWorkspace.sharedWorkspace()
            
            # Get frontmost application first
            frontmost_app = workspace.frontmostApplication()
            
            # Define applications to ignore when detecting user's active app
            ignored_bundle_ids = {
                'dev.kiro.desktop',  # Kiro IDE
                'com.apple.Terminal',  # Terminal
                'com.microsoft.VSCode',  # VS Code
                'com.apple.dt.Xcode',  # Xcode
                'com.jetbrains.intellij',  # IntelliJ
                'com.sublimetext.4',  # Sublime Text
                'com.github.atom',  # Atom
                'com.apple.Console',  # Console
                'com.apple.ActivityMonitor',  # Activity Monitor
                'com.apple.systempreferences',  # System Preferences
            }
            
            # Check if frontmost app should be ignored
            if frontmost_app and frontmost_app.bundleIdentifier() not in ignored_bundle_ids:
                # Frontmost app is a valid user application
                active_app = frontmost_app
                self.logger.debug(f"Using frontmost application: {active_app.localizedName()}")
            else:
                # Frontmost app is a development tool, find the most recent user application
                self.logger.debug(f"Frontmost app is development tool ({frontmost_app.localizedName() if frontmost_app else 'None'}), finding user application")
                
                running_apps = workspace.runningApplications()
                user_apps = []
                
                for app in running_apps:
                    if (app.localizedName() and 
                        not app.isHidden() and 
                        app.bundleIdentifier() not in ignored_bundle_ids and
                        not self._is_system_app(app) and
                        app.activationPolicy() == 0):  # Only regular user applications
                        user_apps.append(app)
                
                # Find the most recently active user application
                # Priority: 1) Currently active apps, 2) Most recently launched apps
                active_user_apps = [app for app in user_apps if app.isActive()]
                
                if active_user_apps:
                    # If there are active user apps, pick the one with highest PID (most recent)
                    active_user_apps.sort(key=lambda app: -app.processIdentifier())
                    active_app = active_user_apps[0]
                    self.logger.debug(f"Found active user app: {active_app.localizedName()}")
                else:
                    # No active user apps, find the most recently launched one
                    # But prioritize common user applications over system apps like Music
                    priority_apps = []
                    other_apps = []
                    
                    for app in user_apps:
                        bundle_id = app.bundleIdentifier()
                        if bundle_id and any(bundle_id.startswith(prefix) for prefix in [
                            'com.google.Chrome',
                            'com.apple.Safari',
                            'org.mozilla.firefox',
                            'com.microsoft.edgemac',
                            'com.brave.Browser',
                            'com.apple.Preview',
                            'com.adobe.Reader',
                            'com.microsoft.VSCode',
                            'com.sublimetext',
                            'com.jetbrains.',
                        ]):
                            priority_apps.append(app)
                        else:
                            other_apps.append(app)
                    
                    # Sort priority apps by PID (most recent first)
                    priority_apps.sort(key=lambda app: -app.processIdentifier())
                    other_apps.sort(key=lambda app: -app.processIdentifier())
                    
                    # Choose from priority apps first, then others
                    if priority_apps:
                        active_app = priority_apps[0]
                        self.logger.debug(f"Selected priority user app: {active_app.localizedName()}")
                    elif other_apps:
                        active_app = other_apps[0]
                        self.logger.debug(f"Selected other user app: {active_app.localizedName()}")
                    else:
                        active_app = frontmost_app
                
                if active_app:
                    self.logger.debug(f"Selected user application: {active_app.localizedName()}")
                else:
                    self.logger.debug("No suitable user application found")
            
            if not active_app:
                self.logger.debug("No active application found")
                return None
            
            app_name = active_app.localizedName()
            bundle_id = active_app.bundleIdentifier()
            process_id = active_app.processIdentifier()
            
            if not app_name:
                self.logger.debug("Active application has no name")
                return None
            
            # Create ApplicationInfo
            app_info = ApplicationInfo(
                name=app_name,
                bundle_id=bundle_id or "unknown",
                process_id=process_id,
                app_type=ApplicationType.UNKNOWN,  # Will be determined later
                version=self._get_app_version(active_app),
                accessibility_enabled=True,
                detection_confidence=0.90 if active_app == frontmost_app else 0.75  # Lower confidence for inferred apps
            )
            
            # Detect application type
            app_type, browser_type, confidence = self._classify_application(app_info)
            app_info.app_type = app_type
            app_info.browser_type = browser_type
            app_info.detection_confidence = min(app_info.detection_confidence, confidence)
            
            return app_info
            
        except Exception as e:
            self.logger.debug(f"Primary detection method failed: {e}")
            return None
    
    def _is_system_app(self, app) -> bool:
        """
        Check if an application is a system application that should be ignored.
        
        Args:
            app: NSRunningApplication instance
            
        Returns:
            True if the app is a system app, False otherwise
        """
        bundle_id = app.bundleIdentifier()
        if not bundle_id:
            return True
        
        # System app patterns to ignore (but keep user-facing Apple apps like Preview, Safari, etc.)
        system_patterns = [
            'com.apple.dock',
            'com.apple.finder',
            'com.apple.systemuiserver',
            'com.apple.controlcenter',
            'com.apple.notificationcenterui',
            'com.apple.WindowManager',
            'com.apple.loginwindow',
            'com.apple.Spotlight',
            'com.apple.wifi',
            'com.apple.universalcontrol',
            'com.apple.PowerChime',
            'com.apple.UserNotificationCenter',
            'com.apple.CoreLocationAgent',
            'com.apple.chronod',
            'com.apple.security.',
            'com.apple.coreservices.',
            'com.apple.talagent',
            'com.apple.wallpaper.',
            'com.apple.ViewBridgeAuxiliary',
            'com.apple.TextInputMenuAgent',
            'com.apple.AirPlayUIAgent',
            'com.apple.PressAndHold',
        ]
        
        # Check if it's a system app pattern
        for pattern in system_patterns:
            if bundle_id.startswith(pattern):
                return True
        
        # Check activation policy - background apps should be ignored
        if app.activationPolicy() != 0:  # 0 = NSApplicationActivationPolicyRegular
            return True
        
        return False
    
    def _get_active_app_applescript_fallback(self) -> Optional[ApplicationInfo]:
        """
        AppleScript fallback method for application detection.
        
        Uses System Events to identify the focused application when
        primary methods fail.
        
        Returns:
            ApplicationInfo if successful, None otherwise
        """
        try:
            # AppleScript to get frontmost application
            script = '''
            tell application "System Events"
                set frontApp to first process whose frontmost is true
                set appName to name of frontApp
                set appPID to unix id of frontApp
                try
                    set appBundle to bundle identifier of frontApp
                on error
                    set appBundle to "unknown"
                end try
                return appName & "|" & appPID & "|" & appBundle
            end tell
            '''
            
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                self.logger.debug(f"AppleScript failed with return code {result.returncode}: {result.stderr}")
                return None
            
            # Parse the result
            parts = result.stdout.strip().split('|')
            if len(parts) < 3:
                self.logger.debug(f"AppleScript returned unexpected format: {result.stdout}")
                return None
            
            app_name = parts[0]
            try:
                process_id = int(parts[1])
            except ValueError:
                process_id = 0
            bundle_id = parts[2] if parts[2] != "unknown" else "unknown"
            
            if not app_name:
                self.logger.debug("AppleScript returned empty application name")
                return None
            
            # Create ApplicationInfo
            app_info = ApplicationInfo(
                name=app_name,
                bundle_id=bundle_id,
                process_id=process_id,
                app_type=ApplicationType.UNKNOWN,
                detection_confidence=0.85  # Lower confidence for fallback method
            )
            
            # Detect application type
            app_type, browser_type, confidence = self._classify_application(app_info)
            app_info.app_type = app_type
            app_info.browser_type = browser_type
            app_info.detection_confidence = min(confidence, 0.85)  # Cap confidence for fallback
            
            return app_info
            
        except subprocess.TimeoutExpired:
            self.logger.debug("AppleScript fallback timed out")
            return None
        except Exception as e:
            self.logger.debug(f"AppleScript fallback failed: {e}")
            return None
    
    def _get_active_app_final_fallback(self) -> Optional[ApplicationInfo]:
        """
        Final fallback method - try to get any reasonable application.
        
        This method attempts to find a suitable application when all other
        methods fail, prioritizing common applications.
        
        Returns:
            ApplicationInfo if any application found, None otherwise
        """
        try:
            # Try to get any running application, preferring common ones
            preferred_apps = [
                "Safari", "Google Chrome", "Firefox", "Microsoft Edge",
                "Finder", "Terminal", "TextEdit", "System Preferences"
            ]
            
            if APPKIT_AVAILABLE:
                workspace = NSWorkspace.sharedWorkspace()
                running_apps = workspace.runningApplications()
                
                # First, try preferred applications
                for app in running_apps:
                    app_name = app.localizedName()
                    if app_name in preferred_apps:
                        app_info = ApplicationInfo(
                            name=app_name,
                            bundle_id=app.bundleIdentifier() or "unknown",
                            process_id=app.processIdentifier(),
                            app_type=ApplicationType.UNKNOWN,
                            detection_confidence=0.5  # Low confidence for final fallback
                        )
                        
                        # Detect application type
                        app_type, browser_type, confidence = self._classify_application(app_info)
                        app_info.app_type = app_type
                        app_info.browser_type = browser_type
                        app_info.detection_confidence = min(confidence, 0.5)
                        
                        self.logger.debug(f"Final fallback found preferred app: {app_name}")
                        return app_info
                
                # If no preferred apps, try any user application
                for app in running_apps:
                    if app.activationPolicy() == 0:  # Regular application
                        app_name = app.localizedName()
                        if app_name and not app_name.startswith("com."):
                            app_info = ApplicationInfo(
                                name=app_name,
                                bundle_id=app.bundleIdentifier() or "unknown",
                                process_id=app.processIdentifier(),
                                app_type=ApplicationType.UNKNOWN,
                                detection_confidence=0.3
                            )
                            
                            # Detect application type
                            app_type, browser_type, confidence = self._classify_application(app_info)
                            app_info.app_type = app_type
                            app_info.browser_type = browser_type
                            app_info.detection_confidence = min(confidence, 0.3)
                            
                            self.logger.debug(f"Final fallback found any app: {app_name}")
                            return app_info
            
            # If AppKit is not available, try AppleScript as final attempt
            try:
                script = 'tell application "System Events" to get name of first process whose frontmost is true'
                result = subprocess.run(
                    ["osascript", "-e", script],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0:
                    app_name = result.stdout.strip()
                    if app_name:
                        app_info = ApplicationInfo(
                            name=app_name,
                            bundle_id="unknown",
                            process_id=0,
                            app_type=ApplicationType.UNKNOWN,
                            detection_confidence=0.2
                        )
                        
                        # Basic classification
                        app_type, browser_type, confidence = self._classify_application(app_info)
                        app_info.app_type = app_type
                        app_info.browser_type = browser_type
                        app_info.detection_confidence = min(confidence, 0.2)
                        
                        self.logger.debug(f"Final AppleScript fallback found: {app_name}")
                        return app_info
            except:
                pass
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Final fallback failed: {e}")
            return None
    
    def _ensure_application_focus(self) -> Dict[str, Any]:
        """
        Ensure we can identify the focused application with comprehensive fallback.
        
        This method implements the robust application detection strategy
        required by the system stabilization plan.
        
        Returns:
            Dictionary with success status and application information
        """
        try:
            self.logger.debug("Ensuring application focus detection")
            
            # Try to get active application info
            app_info = self.get_active_application_info()
            
            if app_info and app_info.name and app_info.name != "unknown":
                return {
                    "success": True,
                    "app_info": app_info.to_dict(),
                    "method": "primary_detection",
                    "confidence": app_info.detection_confidence,
                    "message": f"Successfully detected application: {app_info.name}"
                }
            
            # If primary detection failed, try enhanced AppleScript
            self.logger.info("Primary detection failed, trying enhanced AppleScript")
            enhanced_result = self._enhanced_applescript_detection()
            
            if enhanced_result["success"]:
                return enhanced_result
            
            # Final attempt with system process detection
            self.logger.warning("Enhanced AppleScript failed, trying system process detection")
            process_result = self._system_process_detection()
            
            if process_result["success"]:
                return process_result
            
            # All methods failed
            return {
                "success": False,
                "error": "Could not identify focused application using any method",
                "methods_tried": ["primary_detection", "enhanced_applescript", "system_process"],
                "message": "All application detection methods failed"
            }
            
        except Exception as e:
            self.logger.error(f"Error in _ensure_application_focus: {e}")
            return {
                "success": False,
                "error": f"Application focus detection failed: {str(e)}",
                "message": "Exception occurred during application detection"
            }
    
    def _enhanced_applescript_detection(self) -> Dict[str, Any]:
        """
        Enhanced AppleScript detection with multiple fallback strategies.
        
        Returns:
            Dictionary with detection results
        """
        try:
            # Try multiple AppleScript approaches
            scripts = [
                # Method 1: System Events frontmost process
                '''
                tell application "System Events"
                    set frontApp to first process whose frontmost is true
                    set appName to name of frontApp
                    try
                        set appBundle to bundle identifier of frontApp
                    on error
                        set appBundle to "unknown"
                    end try
                    try
                        set appPID to unix id of frontApp
                    on error
                        set appPID to 0
                    end try
                    return appName & "|" & appBundle & "|" & appPID
                end tell
                ''',
                
                # Method 2: NSWorkspace current application
                '''
                tell application "System Events"
                    set frontApp to name of first process whose frontmost is true
                    return frontApp
                end tell
                ''',
                
                # Method 3: Get active window title and infer application
                '''
                tell application "System Events"
                    set frontApp to first process whose frontmost is true
                    set appName to name of frontApp
                    try
                        set windowTitle to title of first window of frontApp
                        return appName & "|window:" & windowTitle
                    on error
                        return appName & "|window:unknown"
                    end try
                end tell
                '''
            ]
            
            for i, script in enumerate(scripts):
                try:
                    result = subprocess.run(
                        ["osascript", "-e", script],
                        capture_output=True,
                        text=True,
                        timeout=8
                    )
                    
                    if result.returncode == 0 and result.stdout.strip():
                        output = result.stdout.strip()
                        
                        # Parse the result based on script type
                        if i == 0:  # Full info script
                            parts = output.split('|')
                            if len(parts) >= 3:
                                app_name = parts[0]
                                bundle_id = parts[1] if parts[1] != "unknown" else "unknown"
                                try:
                                    process_id = int(parts[2])
                                except:
                                    process_id = 0
                                
                                app_info = ApplicationInfo(
                                    name=app_name,
                                    bundle_id=bundle_id,
                                    process_id=process_id,
                                    app_type=ApplicationType.UNKNOWN,
                                    detection_confidence=0.8
                                )
                                
                                # Classify the application
                                app_type, browser_type, confidence = self._classify_application(app_info)
                                app_info.app_type = app_type
                                app_info.browser_type = browser_type
                                app_info.detection_confidence = min(confidence, 0.8)
                                
                                return {
                                    "success": True,
                                    "app_info": app_info.to_dict(),
                                    "method": f"enhanced_applescript_method_{i+1}",
                                    "confidence": app_info.detection_confidence,
                                    "message": f"Enhanced AppleScript detection succeeded: {app_name}"
                                }
                        
                        elif i == 1:  # Simple name script
                            app_name = output
                            if app_name:
                                app_info = ApplicationInfo(
                                    name=app_name,
                                    bundle_id="unknown",
                                    process_id=0,
                                    app_type=ApplicationType.UNKNOWN,
                                    detection_confidence=0.7
                                )
                                
                                # Basic classification
                                app_type, browser_type, confidence = self._classify_application(app_info)
                                app_info.app_type = app_type
                                app_info.browser_type = browser_type
                                app_info.detection_confidence = min(confidence, 0.7)
                                
                                return {
                                    "success": True,
                                    "app_info": app_info.to_dict(),
                                    "method": f"enhanced_applescript_method_{i+1}",
                                    "confidence": app_info.detection_confidence,
                                    "message": f"Simple AppleScript detection succeeded: {app_name}"
                                }
                        
                        elif i == 2:  # Window title script
                            parts = output.split('|window:')
                            if len(parts) >= 2:
                                app_name = parts[0]
                                window_title = parts[1]
                                
                                app_info = ApplicationInfo(
                                    name=app_name,
                                    bundle_id="unknown",
                                    process_id=0,
                                    app_type=ApplicationType.UNKNOWN,
                                    detection_confidence=0.6
                                )
                                
                                # Basic classification
                                app_type, browser_type, confidence = self._classify_application(app_info)
                                app_info.app_type = app_type
                                app_info.browser_type = browser_type
                                app_info.detection_confidence = min(confidence, 0.6)
                                
                                return {
                                    "success": True,
                                    "app_info": app_info.to_dict(),
                                    "method": f"enhanced_applescript_method_{i+1}",
                                    "confidence": app_info.detection_confidence,
                                    "window_title": window_title,
                                    "message": f"Window-based AppleScript detection succeeded: {app_name}"
                                }
                
                except subprocess.TimeoutExpired:
                    self.logger.debug(f"AppleScript method {i+1} timed out")
                    continue
                except Exception as e:
                    self.logger.debug(f"AppleScript method {i+1} failed: {e}")
                    continue
            
            return {
                "success": False,
                "error": "All enhanced AppleScript methods failed",
                "message": "Enhanced AppleScript detection unsuccessful"
            }
            
        except Exception as e:
            self.logger.debug(f"Enhanced AppleScript detection failed: {e}")
            return {
                "success": False,
                "error": f"Enhanced AppleScript detection error: {str(e)}",
                "message": "Exception in enhanced AppleScript detection"
            }
    
    def _system_process_detection(self) -> Dict[str, Any]:
        """
        System process detection as final fallback.
        
        Uses system commands to detect running processes and infer
        the most likely active application.
        
        Returns:
            Dictionary with detection results
        """
        try:
            # Try to use ps command to find GUI applications
            result = subprocess.run(
                ["ps", "aux"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                
                # Look for common GUI applications in process list
                gui_apps = []
                for line in lines:
                    if any(app in line.lower() for app in [
                        'safari', 'chrome', 'firefox', 'edge', 'finder', 
                        'terminal', 'textedit', 'mail', 'messages'
                    ]):
                        # Extract process name
                        parts = line.split()
                        if len(parts) > 10:
                            process_name = parts[10].split('/')[-1]
                            if process_name and not process_name.startswith('-'):
                                gui_apps.append(process_name)
                
                if gui_apps:
                    # Use the first found GUI application
                    app_name = gui_apps[0]
                    
                    app_info = ApplicationInfo(
                        name=app_name,
                        bundle_id="unknown",
                        process_id=0,
                        app_type=ApplicationType.UNKNOWN,
                        detection_confidence=0.4
                    )
                    
                    # Basic classification
                    app_type, browser_type, confidence = self._classify_application(app_info)
                    app_info.app_type = app_type
                    app_info.browser_type = browser_type
                    app_info.detection_confidence = min(confidence, 0.4)
                    
                    return {
                        "success": True,
                        "app_info": app_info.to_dict(),
                        "method": "system_process_detection",
                        "confidence": app_info.detection_confidence,
                        "message": f"System process detection found: {app_name}",
                        "note": "Low confidence - inferred from process list"
                    }
            
            return {
                "success": False,
                "error": "No suitable GUI applications found in process list",
                "message": "System process detection unsuccessful"
            }
            
        except Exception as e:
            self.logger.debug(f"System process detection failed: {e}")
            return {
                "success": False,
                "error": f"System process detection error: {str(e)}",
                "message": "Exception in system process detection"
            }