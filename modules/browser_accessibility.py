"""
Browser-Specific Accessibility Module for AURA

This module provides specialized accessibility handling for different web browsers,
including Chrome/Safari-specific element detection, web application tree navigation,
and browser tab/frame handling for complex web applications.
"""

import logging
import time
from typing import Dict, Any, Optional, List, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import re

from .application_detector import BrowserType, ApplicationInfo

# Import ApplicationServices for accessibility functions
try:
    from ApplicationServices import (
        AXUIElementCreateApplication,
        AXUIElementCopyAttributeValue,
        AXUIElementCopyAttributeNames,
        kAXChildrenAttribute,
        kAXRoleAttribute,
        kAXTitleAttribute,
        kAXDescriptionAttribute,
        kAXValueAttribute,
        kAXURLAttribute,
        kAXWindowsAttribute,
        kAXFocusedWindowAttribute,
        kAXMainWindowAttribute
    )
    ACCESSIBILITY_FUNCTIONS_AVAILABLE = True
except ImportError:
    ACCESSIBILITY_FUNCTIONS_AVAILABLE = False
    logging.warning("ApplicationServices not available for browser accessibility")


@dataclass
class WebElement:
    """Represents a web element with browser-specific attributes."""
    role: str
    title: str
    description: str
    value: str
    url: Optional[str] = None
    coordinates: Optional[List[int]] = None
    center_point: Optional[List[int]] = None
    enabled: bool = True
    frame_id: Optional[str] = None
    tab_id: Optional[str] = None
    element_id: Optional[str] = None
    attributes: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            'role': self.role,
            'title': self.title,
            'description': self.description,
            'value': self.value,
            'url': self.url,
            'coordinates': self.coordinates,
            'center_point': self.center_point,
            'enabled': self.enabled,
            'frame_id': self.frame_id,
            'tab_id': self.tab_id,
            'element_id': self.element_id,
            'has_attributes': bool(self.attributes)
        }


@dataclass
class BrowserTab:
    """Represents a browser tab with its accessibility tree."""
    tab_id: str
    title: str
    url: str
    is_active: bool
    elements: List[WebElement] = field(default_factory=list)
    frames: List['BrowserFrame'] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            'tab_id': self.tab_id,
            'title': self.title,
            'url': self.url,
            'is_active': self.is_active,
            'element_count': len(self.elements),
            'frame_count': len(self.frames)
        }


@dataclass
class BrowserFrame:
    """Represents a frame within a browser tab."""
    frame_id: str
    url: str
    title: str
    parent_frame_id: Optional[str] = None
    elements: List[WebElement] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            'frame_id': self.frame_id,
            'url': self.url,
            'title': self.title,
            'parent_frame_id': self.parent_frame_id,
            'element_count': len(self.elements)
        }


@dataclass
class BrowserAccessibilityTree:
    """Complete accessibility tree for a browser application."""
    browser_type: BrowserType
    app_name: str
    process_id: int
    tabs: List[BrowserTab] = field(default_factory=list)
    active_tab_id: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    
    def get_active_tab(self) -> Optional[BrowserTab]:
        """Get the currently active tab."""
        if self.active_tab_id:
            for tab in self.tabs:
                if tab.tab_id == self.active_tab_id:
                    return tab
        # Fallback to first active tab
        for tab in self.tabs:
            if tab.is_active:
                return tab
        return None
    
    def get_all_elements(self) -> List[WebElement]:
        """Get all elements from all tabs and frames."""
        all_elements = []
        for tab in self.tabs:
            all_elements.extend(tab.elements)
            for frame in tab.frames:
                all_elements.extend(frame.elements)
        return all_elements
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            'browser_type': self.browser_type.value,
            'app_name': self.app_name,
            'process_id': self.process_id,
            'tab_count': len(self.tabs),
            'active_tab_id': self.active_tab_id,
            'total_elements': len(self.get_all_elements()),
            'timestamp': self.timestamp
        }


class BrowserAccessibilityHandler:
    """
    Handles browser-specific accessibility operations.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the browser accessibility handler.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Browser-specific configurations
        self._init_browser_configs()
        
        # Cache for browser trees
        self._tree_cache: Dict[str, BrowserAccessibilityTree] = {}
        self._cache_ttl = self.config.get('cache_ttl', 30)  # 30 seconds default
        
        self.logger.info("BrowserAccessibilityHandler initialized")
    
    def _init_browser_configs(self):
        """Initialize browser-specific configurations."""
        
        # Chrome-specific configuration
        self.chrome_config = {
            'web_content_roles': [
                'AXButton', 'AXLink', 'AXTextField', 'AXStaticText', 
                'AXGenericElement', 'AXGroup', 'AXList', 'AXListItem'
            ],
            'navigation_roles': [
                'AXToolbar', 'AXMenuBar', 'AXMenu', 'AXMenuItem'
            ],
            'frame_indicators': [
                'AXWebArea', 'AXScrollArea', 'AXGroup'
            ],
            'tab_indicators': [
                'AXTab', 'AXTabGroup'  # Removed AXButton to avoid browser UI buttons
            ],
            'search_depth': 15,
            'timeout_ms': 3500,
            'fuzzy_threshold': 0.72
        }
        
        # Safari-specific configuration
        self.safari_config = {
            'web_content_roles': [
                'AXButton', 'AXLink', 'AXTextField', 'AXStaticText',
                'AXGroup', 'AXList', 'AXListItem'
            ],
            'navigation_roles': [
                'AXToolbar', 'AXMenuBar', 'AXMenu', 'AXMenuItem'
            ],
            'frame_indicators': [
                'AXWebArea', 'AXScrollArea'
            ],
            'tab_indicators': [
                'AXTab', 'AXTabGroup'
            ],
            'search_depth': 12,
            'timeout_ms': 2500,
            'fuzzy_threshold': 0.78
        }
        
        # Firefox-specific configuration
        self.firefox_config = {
            'web_content_roles': [
                'AXButton', 'AXLink', 'AXTextField', 'AXStaticText',
                'AXGenericElement', 'AXGroup'
            ],
            'navigation_roles': [
                'AXToolbar', 'AXMenuBar', 'AXMenu', 'AXMenuItem'
            ],
            'frame_indicators': [
                'AXWebArea', 'AXDocument', 'AXScrollArea'
            ],
            'tab_indicators': [
                'AXTab', 'AXTabGroup'
            ],
            'search_depth': 12,
            'timeout_ms': 3000,
            'fuzzy_threshold': 0.75
        }
    
    def get_browser_config(self, browser_type: BrowserType) -> Dict[str, Any]:
        """
        Get configuration for specific browser type.
        
        Args:
            browser_type: Type of browser
            
        Returns:
            Browser-specific configuration
        """
        if browser_type == BrowserType.CHROME:
            return self.chrome_config
        elif browser_type == BrowserType.SAFARI:
            return self.safari_config
        elif browser_type == BrowserType.FIREFOX:
            return self.firefox_config
        else:
            # Default to Chrome config for unknown browsers
            return self.chrome_config
    
    def extract_browser_tree(self, app_info: ApplicationInfo) -> Optional[BrowserAccessibilityTree]:
        """
        Extract complete accessibility tree for a browser application.
        
        Args:
            app_info: Application information
            
        Returns:
            BrowserAccessibilityTree if successful, None otherwise
        """
        if not ACCESSIBILITY_FUNCTIONS_AVAILABLE:
            self.logger.warning("Accessibility functions not available")
            return None
        
        if app_info.app_type.value != 'web_browser':
            self.logger.warning(f"Application {app_info.name} is not a web browser")
            return None
        
        cache_key = f"{app_info.name}_{app_info.process_id}"
        
        # Check cache first
        if cache_key in self._tree_cache:
            cached_tree = self._tree_cache[cache_key]
            if time.time() - cached_tree.timestamp < self._cache_ttl:
                self.logger.debug(f"Using cached browser tree for {app_info.name}")
                return cached_tree
        
        try:
            start_time = time.time()
            
            # Create accessibility element for the application
            app_element = AXUIElementCreateApplication(app_info.process_id)
            if not app_element:
                self.logger.error(f"Could not create accessibility element for {app_info.name}")
                return None
            
            # Extract browser tree
            browser_tree = self._extract_browser_structure(
                app_element, app_info.browser_type, app_info.name, app_info.process_id
            )
            
            if browser_tree:
                # Cache the result
                self._tree_cache[cache_key] = browser_tree
                
                extraction_time = (time.time() - start_time) * 1000
                self.logger.info(
                    f"Extracted browser tree for {app_info.name}: "
                    f"{len(browser_tree.tabs)} tabs, {len(browser_tree.get_all_elements())} elements "
                    f"(time: {extraction_time:.1f}ms)"
                )
            
            return browser_tree
            
        except Exception as e:
            self.logger.error(f"Error extracting browser tree for {app_info.name}: {e}")
            return None
    
    def _extract_browser_structure(
        self, 
        app_element: Any, 
        browser_type: Optional[BrowserType], 
        app_name: str, 
        process_id: int
    ) -> Optional[BrowserAccessibilityTree]:
        """
        Extract the browser structure including tabs and frames.
        
        Args:
            app_element: Root accessibility element
            browser_type: Type of browser
            app_name: Application name
            process_id: Process ID
            
        Returns:
            BrowserAccessibilityTree if successful, None otherwise
        """
        try:
            browser_tree = BrowserAccessibilityTree(
                browser_type=browser_type or BrowserType.UNKNOWN_BROWSER,
                app_name=app_name,
                process_id=process_id
            )
            
            # Get browser configuration
            config = self.get_browser_config(browser_type or BrowserType.UNKNOWN_BROWSER)
            
            # Extract windows
            windows = self._get_attribute_value(app_element, kAXWindowsAttribute)
            if not windows:
                self.logger.warning(f"No windows found for {app_name}")
                return browser_tree
            
            # Process each window
            all_tabs = []
            for window in windows:
                tabs = self._extract_tabs_from_window(window, config)
                all_tabs.extend(tabs)
            
            # Filter and clean up tabs
            browser_tree.tabs = self._filter_and_clean_tabs(all_tabs)
            
            # Determine active tab (prioritize content-rich tabs)
            browser_tree.active_tab_id = self._find_active_tab_smart(browser_tree.tabs)
            
            return browser_tree
            
        except Exception as e:
            self.logger.error(f"Error extracting browser structure: {e}")
            return None
    
    def _extract_tabs_from_window(self, window: Any, config: Dict[str, Any]) -> List[BrowserTab]:
        """
        Extract tabs from a browser window.
        
        Args:
            window: Window accessibility element
            config: Browser configuration
            
        Returns:
            List of BrowserTab objects
        """
        tabs = []
        
        try:
            # Look for tab groups and individual tabs
            tab_elements = self._find_elements_by_roles(
                window, config['tab_indicators'], max_depth=6
            )
            
            # Filter out duplicate or invalid tab elements
            valid_tab_elements = self._filter_valid_tabs(tab_elements)
            
            for i, tab_element in enumerate(valid_tab_elements):
                tab = self._create_tab_from_element(tab_element, f"tab_{i}", config)
                if tab:
                    tabs.append(tab)
            
            # If no tabs found, treat the entire window as a single tab
            if not tabs:
                window_tab = self._create_tab_from_window(window, "main_tab", config)
                if window_tab:
                    tabs.append(window_tab)
            
        except Exception as e:
            self.logger.error(f"Error extracting tabs from window: {e}")
        
        return tabs
    
    def _filter_valid_tabs(self, tab_elements: List[Any]) -> List[Any]:
        """
        Filter tab elements to remove duplicates and find actual individual tabs.
        
        Args:
            tab_elements: List of potential tab elements
            
        Returns:
            List of valid individual tab elements
        """
        if not tab_elements:
            return []
        
        # First, look for individual AXTab elements within AXTabGroup elements
        individual_tabs = []
        
        for element in tab_elements:
            try:
                role = self._get_attribute_value(element, kAXRoleAttribute)
                
                if role == 'AXTab':
                    # This is an individual tab - add it directly
                    individual_tabs.append(element)
                    
                elif role == 'AXTabGroup':
                    # This is a tab group - look for individual tabs inside it
                    children = self._get_attribute_value(element, kAXChildrenAttribute)
                    if children:
                        tabs_in_group = self._find_individual_tabs_in_group(children)
                        individual_tabs.extend(tabs_in_group)
                        
            except Exception as e:
                self.logger.debug(f"Error processing tab element: {e}")
                continue
        
        # Remove duplicates based on position and content
        unique_tabs = self._deduplicate_tabs(individual_tabs)
        
        # If we still don't have individual tabs, fall back to using one TabGroup
        if not unique_tabs and tab_elements:
            # Use the first TabGroup as a fallback
            for element in tab_elements:
                try:
                    role = self._get_attribute_value(element, kAXRoleAttribute)
                    if role == 'AXTabGroup':
                        unique_tabs = [element]
                        break
                except:
                    continue
        
        self.logger.debug(f"Filtered {len(tab_elements)} tab elements down to {len(unique_tabs)} unique tabs")
        return unique_tabs
    
    def _find_individual_tabs_in_group(self, children: List[Any]) -> List[Any]:
        """
        Find individual tab elements within a tab group.
        
        Args:
            children: List of child elements in a tab group
            
        Returns:
            List of individual tab elements
        """
        individual_tabs = []
        
        def search_for_tabs(elements, depth=0):
            if depth > 3:  # Limit recursion depth
                return
                
            for element in elements:
                try:
                    role = self._get_attribute_value(element, kAXRoleAttribute)
                    
                    if role == 'AXTab':
                        individual_tabs.append(element)
                    elif role in ['AXGroup', 'AXTabGroup'] and depth < 3:
                        # Recurse into groups to find tabs
                        grandchildren = self._get_attribute_value(element, kAXChildrenAttribute)
                        if grandchildren:
                            search_for_tabs(grandchildren, depth + 1)
                            
                except Exception as e:
                    continue
        
        search_for_tabs(children)
        return individual_tabs
    
    def _deduplicate_tabs(self, tabs: List[Any]) -> List[Any]:
        """
        Remove duplicate tab elements based on position and content.
        
        Args:
            tabs: List of tab elements
            
        Returns:
            List of unique tab elements
        """
        if not tabs:
            return []
        
        unique_tabs = []
        seen_signatures = set()
        
        for tab in tabs:
            try:
                # Create a signature for this tab based on position and content
                title = self._get_attribute_value(tab, kAXTitleAttribute) or ""
                coordinates = self._get_element_coordinates(tab)
                
                # Create signature
                if coordinates:
                    signature = (title, coordinates[0], coordinates[1])
                else:
                    signature = (title, "no_coords")
                
                if signature not in seen_signatures:
                    unique_tabs.append(tab)
                    seen_signatures.add(signature)
                    
            except Exception as e:
                # If we can't get signature, include it anyway
                unique_tabs.append(tab)
        
        return unique_tabs
    
    def _filter_and_clean_tabs(self, tabs: List[BrowserTab]) -> List[BrowserTab]:
        """
        Filter and clean up tabs to remove duplicates and empty browser UI containers.
        
        Args:
            tabs: List of raw browser tabs
            
        Returns:
            List of cleaned and filtered tabs
        """
        if not tabs:
            return []
        
        # Separate content tabs from empty UI containers
        content_tabs = []
        ui_containers = []
        
        for tab in tabs:
            total_elements = len(tab.elements) + sum(len(frame.elements) for frame in tab.frames)
            
            if total_elements > 0:
                content_tabs.append(tab)
            else:
                ui_containers.append(tab)
        
        # If we have content tabs, prioritize them
        if content_tabs:
            # Remove duplicate content tabs based on element count and title
            unique_content_tabs = self._deduplicate_content_tabs(content_tabs)
            
            # Add one UI container if we have multiple (to represent browser chrome)
            if ui_containers:
                # Pick the first UI container as representative
                unique_content_tabs.append(ui_containers[0])
            
            return unique_content_tabs
        
        # If no content tabs, return a single UI container
        elif ui_containers:
            return [ui_containers[0]]
        
        return tabs
    
    def _deduplicate_content_tabs(self, content_tabs: List[BrowserTab]) -> List[BrowserTab]:
        """
        Remove duplicate content tabs based on element count and characteristics.
        
        Args:
            content_tabs: List of tabs with content
            
        Returns:
            List of unique content tabs
        """
        if len(content_tabs) <= 1:
            return content_tabs
        
        unique_tabs = []
        seen_signatures = set()
        
        for tab in content_tabs:
            # Create signature based on element count and types
            total_elements = len(tab.elements) + sum(len(frame.elements) for frame in tab.frames)
            all_elements = tab.elements + [elem for frame in tab.frames for elem in frame.elements]
            
            # Count element types
            role_counts = {}
            for element in all_elements:
                role = element.role
                role_counts[role] = role_counts.get(role, 0) + 1
            
            # Create signature
            signature = (total_elements, tuple(sorted(role_counts.items())))
            
            if signature not in seen_signatures:
                unique_tabs.append(tab)
                seen_signatures.add(signature)
        
        return unique_tabs
    
    def _find_active_tab_smart(self, tabs: List[BrowserTab]) -> Optional[str]:
        """
        Smart active tab detection that prioritizes content-rich tabs.
        
        Args:
            tabs: List of browser tabs
            
        Returns:
            Active tab ID or None
        """
        if not tabs:
            return None
        
        # First, try to find a tab marked as active with content
        content_active_tabs = []
        for tab in tabs:
            total_elements = len(tab.elements) + sum(len(frame.elements) for frame in tab.frames)
            if tab.is_active and total_elements > 0:
                content_active_tabs.append((tab, total_elements))
        
        if content_active_tabs:
            # Return the active tab with the most content
            content_active_tabs.sort(key=lambda x: x[1], reverse=True)
            return content_active_tabs[0][0].tab_id
        
        # If no active content tabs, find the tab with the most content
        content_tabs = []
        for tab in tabs:
            total_elements = len(tab.elements) + sum(len(frame.elements) for frame in tab.frames)
            if total_elements > 0:
                content_tabs.append((tab, total_elements))
        
        if content_tabs:
            # Return the tab with the most content
            content_tabs.sort(key=lambda x: x[1], reverse=True)
            return content_tabs[0][0].tab_id
        
        # Fallback to first tab
        return tabs[0].tab_id
    
    def _create_tab_from_element(self, tab_element: Any, tab_id: str, config: Dict[str, Any]) -> Optional[BrowserTab]:
        """
        Create a BrowserTab from a tab accessibility element.
        
        Args:
            tab_element: Tab accessibility element
            tab_id: Unique tab identifier
            config: Browser configuration
            
        Returns:
            BrowserTab if successful, None otherwise
        """
        try:
            # Get tab title and URL
            raw_title = self._get_attribute_value(tab_element, kAXTitleAttribute) or "Untitled"
            raw_url = self._get_attribute_value(tab_element, kAXURLAttribute) or ""
            
            # Determine if tab is active (simplified check)
            is_active = self._is_element_focused_or_selected(tab_element)
            
            # Create tab
            tab = BrowserTab(
                tab_id=tab_id,
                title=raw_title,
                url=raw_url,
                is_active=is_active
            )
            
            # Extract elements from tab content
            tab.elements = self._extract_web_elements_from_container(tab_element, config, tab_id)
            
            # Extract frames
            tab.frames = self._extract_frames_from_container(tab_element, config, tab_id)
            
            # Try to improve title and URL based on content
            improved_title, improved_url = self._improve_tab_info_from_content(tab, raw_title, raw_url)
            tab.title = improved_title
            tab.url = improved_url
            
            return tab
            
        except Exception as e:
            self.logger.error(f"Error creating tab from element: {e}")
            return None
    
    def _create_tab_from_window(self, window: Any, tab_id: str, config: Dict[str, Any]) -> Optional[BrowserTab]:
        """
        Create a BrowserTab from a window (when no explicit tabs are found).
        
        Args:
            window: Window accessibility element
            tab_id: Unique tab identifier
            config: Browser configuration
            
        Returns:
            BrowserTab if successful, None otherwise
        """
        try:
            # Get window title and try to extract page info
            window_title = self._get_attribute_value(window, kAXTitleAttribute) or "Browser Window"
            
            # Try to extract actual page title and URL from window title
            page_title, page_url = self._parse_browser_window_title(window_title)
            
            # Create tab
            tab = BrowserTab(
                tab_id=tab_id,
                title=page_title,
                url=page_url,
                is_active=True  # Single window/tab is considered active
            )
            
            # Extract elements from window
            tab.elements = self._extract_web_elements_from_container(window, config, tab_id)
            
            # Extract frames
            tab.frames = self._extract_frames_from_container(window, config, tab_id)
            
            return tab
            
        except Exception as e:
            self.logger.error(f"Error creating tab from window: {e}")
            return None
    
    def _parse_browser_window_title(self, window_title: str) -> Tuple[str, str]:
        """
        Parse browser window title to extract page title and URL.
        
        Args:
            window_title: Browser window title (e.g., "Facebook - Google Chrome")
            
        Returns:
            Tuple of (page_title, page_url)
        """
        if not window_title or window_title == "Browser Window":
            return "Browser Window", ""
        
        # Common browser title patterns:
        # "Page Title - Google Chrome"
        # "Page Title - Safari"
        # "Page Title - Mozilla Firefox"
        
        browser_names = ["Google Chrome", "Safari", "Mozilla Firefox", "Microsoft Edge"]
        
        for browser_name in browser_names:
            if f" - {browser_name}" in window_title:
                page_title = window_title.replace(f" - {browser_name}", "").strip()
                
                # Try to infer URL from common page titles
                page_url = self._infer_url_from_title(page_title)
                
                return page_title, page_url
        
        # If no browser name found, use the whole title
        return window_title, ""
    
    def _infer_url_from_title(self, page_title: str) -> str:
        """
        Infer URL from page title for common sites.
        
        Args:
            page_title: Page title
            
        Returns:
            Inferred URL or empty string
        """
        title_lower = page_title.lower()
        
        # Common site patterns
        if "facebook" in title_lower:
            return "https://www.facebook.com"
        elif "google" in title_lower and ("search" in title_lower or title_lower == "google"):
            return "https://www.google.com"
        elif "gmail" in title_lower:
            return "https://mail.google.com"
        elif "youtube" in title_lower:
            return "https://www.youtube.com"
        elif "twitter" in title_lower:
            return "https://twitter.com"
        elif "linkedin" in title_lower:
            return "https://www.linkedin.com"
        elif "github" in title_lower:
            return "https://github.com"
        elif title_lower == "new tab":
            return "chrome://newtab/"
        elif "accessibility" in title_lower and "internals" in title_lower:
            return "chrome://accessibility/"
        
        return ""
    
    def _improve_tab_info_from_content(self, tab: BrowserTab, raw_title: str, raw_url: str) -> Tuple[str, str]:
        """
        Improve tab title and URL by analyzing the content elements.
        
        Args:
            tab: Browser tab with extracted elements
            raw_title: Raw title from tab element
            raw_url: Raw URL from tab element
            
        Returns:
            Tuple of (improved_title, improved_url)
        """
        # If we already have good info, use it
        if raw_title not in ["Untitled", "Browser Window", ""] and raw_url:
            return raw_title, raw_url
        
        # Analyze all elements in the tab
        all_elements = tab.elements + [elem for frame in tab.frames for elem in frame.elements]
        
        # Look for content that indicates the page type
        facebook_indicators = []
        google_indicators = []
        other_content = []
        
        for element in all_elements:
            text_content = (element.title + " " + element.description + " " + element.value).lower()
            
            if any(keyword in text_content for keyword in ['facebook', 'log in', 'sign up', 'email or phone']):
                facebook_indicators.append(element)
            elif any(keyword in text_content for keyword in ['google', 'search', 'gmail']):
                google_indicators.append(element)
            elif text_content.strip():
                other_content.append(element)
        
        # Determine page type and set appropriate title/URL
        if facebook_indicators:
            title = "Facebook - log in or sign up"
            url = "https://www.facebook.com"
        elif google_indicators:
            title = "Google"
            url = "https://www.google.com"
        elif raw_title not in ["Untitled", "Browser Window", ""]:
            title = raw_title
            url = self._infer_url_from_title(raw_title)
        else:
            # Try to extract meaningful title from content
            meaningful_titles = [e.title for e in other_content if e.title and len(e.title) > 3]
            if meaningful_titles:
                title = meaningful_titles[0][:50]  # Use first meaningful title, truncated
                url = self._infer_url_from_title(title)
            else:
                title = raw_title or "Web Page"
                url = raw_url
        
        return title, url
    
    def _extract_web_elements_from_container(
        self, 
        container: Any, 
        config: Dict[str, Any], 
        tab_id: str
    ) -> List[WebElement]:
        """
        Extract web elements from a container (tab or frame).
        
        Args:
            container: Container accessibility element
            config: Browser configuration
            tab_id: Tab identifier
            
        Returns:
            List of WebElement objects
        """
        elements = []
        
        try:
            # Find web content elements
            web_elements = self._find_elements_by_roles(
                container, 
                config['web_content_roles'], 
                max_depth=config['search_depth']
            )
            
            for element in web_elements:
                web_element = self._create_web_element_from_accessibility_element(
                    element, tab_id
                )
                if web_element:
                    elements.append(web_element)
            
        except Exception as e:
            self.logger.error(f"Error extracting web elements: {e}")
        
        return elements
    
    def _extract_frames_from_container(
        self, 
        container: Any, 
        config: Dict[str, Any], 
        tab_id: str
    ) -> List[BrowserFrame]:
        """
        Extract frames from a container.
        
        Args:
            container: Container accessibility element
            config: Browser configuration
            tab_id: Tab identifier
            
        Returns:
            List of BrowserFrame objects
        """
        frames = []
        
        try:
            # Find frame elements
            frame_elements = self._find_elements_by_roles(
                container, 
                config['frame_indicators'], 
                max_depth=8
            )
            
            for i, frame_element in enumerate(frame_elements):
                frame = self._create_frame_from_element(frame_element, f"{tab_id}_frame_{i}")
                if frame:
                    frames.append(frame)
            
        except Exception as e:
            self.logger.error(f"Error extracting frames: {e}")
        
        return frames
    
    def _create_frame_from_element(self, frame_element: Any, frame_id: str) -> Optional[BrowserFrame]:
        """
        Create a BrowserFrame from a frame accessibility element.
        
        Args:
            frame_element: Frame accessibility element
            frame_id: Unique frame identifier
            
        Returns:
            BrowserFrame if successful, None otherwise
        """
        try:
            # Get frame attributes
            title = self._get_attribute_value(frame_element, kAXTitleAttribute) or ""
            url = self._get_attribute_value(frame_element, kAXURLAttribute) or ""
            
            # Create frame
            frame = BrowserFrame(
                frame_id=frame_id,
                url=url,
                title=title
            )
            
            # Extract elements from frame
            frame.elements = self._extract_web_elements_from_container(
                frame_element, self.chrome_config, frame_id  # Use default config for frames
            )
            
            return frame
            
        except Exception as e:
            self.logger.error(f"Error creating frame from element: {e}")
            return None
    
    def _create_web_element_from_accessibility_element(
        self, 
        element: Any, 
        tab_id: str
    ) -> Optional[WebElement]:
        """
        Create a WebElement from an accessibility element.
        
        Args:
            element: Accessibility element
            tab_id: Tab identifier
            
        Returns:
            WebElement if successful, None otherwise
        """
        try:
            # Get basic attributes
            role = self._get_attribute_value(element, kAXRoleAttribute) or ""
            title = self._get_attribute_value(element, kAXTitleAttribute) or ""
            description = self._get_attribute_value(element, kAXDescriptionAttribute) or ""
            value = self._get_attribute_value(element, kAXValueAttribute) or ""
            url = self._get_attribute_value(element, kAXURLAttribute) or None
            
            # Get position and size (if available)
            coordinates = self._get_element_coordinates(element)
            center_point = self._calculate_center_point(coordinates) if coordinates else None
            
            # Create web element
            web_element = WebElement(
                role=role,
                title=title,
                description=description,
                value=value,
                url=url,
                coordinates=coordinates,
                center_point=center_point,
                tab_id=tab_id
            )
            
            return web_element
            
        except Exception as e:
            self.logger.error(f"Error creating web element: {e}")
            return None
    
    def _find_elements_by_roles(
        self, 
        container: Any, 
        roles: List[str], 
        max_depth: int = 10
    ) -> List[Any]:
        """
        Find elements by their accessibility roles.
        
        Args:
            container: Container element to search in
            roles: List of roles to search for
            max_depth: Maximum search depth
            
        Returns:
            List of matching accessibility elements
        """
        elements = []
        
        def search_recursive(element: Any, depth: int):
            if depth > max_depth:
                return
            
            try:
                # Check if current element matches
                element_role = self._get_attribute_value(element, kAXRoleAttribute)
                if element_role in roles:
                    elements.append(element)
                
                # Search children
                children = self._get_attribute_value(element, kAXChildrenAttribute)
                if children:
                    for child in children:
                        search_recursive(child, depth + 1)
                        
            except Exception as e:
                self.logger.debug(f"Error searching element at depth {depth}: {e}")
        
        search_recursive(container, 0)
        return elements
    
    def _get_attribute_value(self, element: Any, attribute: str) -> Any:
        """
        Get attribute value from accessibility element.
        
        Args:
            element: Accessibility element
            attribute: Attribute name
            
        Returns:
            Attribute value or None
        """
        try:
            return AXUIElementCopyAttributeValue(element, attribute, None)[1]
        except:
            return None
    
    def _get_element_coordinates(self, element: Any) -> Optional[List[int]]:
        """
        Get element coordinates [x, y, width, height].
        
        Args:
            element: Accessibility element
            
        Returns:
            Coordinates list or None
        """
        try:
            from ApplicationServices import kAXPositionAttribute, kAXSizeAttribute
            
            position = self._get_attribute_value(element, kAXPositionAttribute)
            size = self._get_attribute_value(element, kAXSizeAttribute)
            
            if position and size:
                return [int(position.x), int(position.y), int(size.width), int(size.height)]
        except:
            pass
        return None
    
    def _calculate_center_point(self, coordinates: List[int]) -> List[int]:
        """
        Calculate center point from coordinates.
        
        Args:
            coordinates: [x, y, width, height]
            
        Returns:
            [center_x, center_y]
        """
        x, y, width, height = coordinates
        return [x + width // 2, y + height // 2]
    
    def _is_element_focused_or_selected(self, element: Any) -> bool:
        """
        Check if element is focused or selected.
        
        Args:
            element: Accessibility element
            
        Returns:
            True if focused/selected, False otherwise
        """
        try:
            from ApplicationServices import kAXFocusedAttribute, kAXSelectedAttribute
            
            focused = self._get_attribute_value(element, kAXFocusedAttribute)
            selected = self._get_attribute_value(element, kAXSelectedAttribute)
            
            return bool(focused or selected)
        except:
            return False
    
    def _find_active_tab(self, tabs: List[BrowserTab]) -> Optional[str]:
        """
        Find the active tab ID.
        
        Args:
            tabs: List of browser tabs
            
        Returns:
            Active tab ID or None
        """
        for tab in tabs:
            if tab.is_active:
                return tab.tab_id
        
        # If no active tab found, return first tab
        if tabs:
            return tabs[0].tab_id
        
        return None
    
    def find_elements_in_browser(
        self, 
        app_info: ApplicationInfo, 
        target_text: str, 
        roles: Optional[List[str]] = None
    ) -> List[WebElement]:
        """
        Find elements in browser that match the target text.
        
        Args:
            app_info: Application information
            target_text: Text to search for
            roles: Optional list of roles to filter by
            
        Returns:
            List of matching WebElement objects
        """
        browser_tree = self.extract_browser_tree(app_info)
        if not browser_tree:
            return []
        
        matching_elements = []
        target_lower = target_text.lower()
        
        # Search in all elements
        for element in browser_tree.get_all_elements():
            # Filter by roles if specified
            if roles and element.role not in roles:
                continue
            
            # Check for text matches
            if (target_lower in element.title.lower() or 
                target_lower in element.description.lower() or 
                target_lower in element.value.lower()):
                matching_elements.append(element)
        
        self.logger.info(f"Found {len(matching_elements)} matching elements for '{target_text}'")
        return matching_elements
    
    def get_web_content_elements(self, app_info: ApplicationInfo) -> List[WebElement]:
        """
        Get all web content elements from the browser.
        
        Args:
            app_info: Application information
            
        Returns:
            List of web content WebElement objects
        """
        browser_tree = self.extract_browser_tree(app_info)
        if not browser_tree:
            return []
        
        config = self.get_browser_config(app_info.browser_type or BrowserType.UNKNOWN_BROWSER)
        web_content_roles = config['web_content_roles']
        
        # Filter elements by web content roles
        web_elements = []
        for element in browser_tree.get_all_elements():
            if element.role in web_content_roles:
                web_elements.append(element)
        
        return web_elements
    
    def clear_cache(self):
        """Clear the browser tree cache."""
        self._tree_cache.clear()
        self.logger.info("Browser accessibility cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            'cache_size': len(self._tree_cache),
            'cached_browsers': list(self._tree_cache.keys()),
            'cache_ttl': self._cache_ttl
        }