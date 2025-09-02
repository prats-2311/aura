"""
AccessibilityModule for AURA - Fast Path GUI Element Detection

This module provides high-speed, non-visual interface for querying macOS UI elements
using the Accessibility API, enabling near-instantaneous GUI automation.
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import re

try:
    import AppKit
    from AppKit import NSWorkspace, NSApplication
    import Accessibility
    ACCESSIBILITY_AVAILABLE = True
except ImportError as e:
    ACCESSIBILITY_AVAILABLE = False
    logging.warning(f"Accessibility frameworks not available: {e}")


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


class AccessibilityPermissionError(Exception):
    """Raised when accessibility permissions are not granted."""
    pass


class AccessibilityAPIUnavailableError(Exception):
    """Raised when accessibility API is not available."""
    pass


class ElementNotFoundError(Exception):
    """Raised when requested element cannot be found."""
    pass


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
        
        try:
            self._initialize_accessibility_api()
        except Exception as e:
            self.logger.error(f"Failed to initialize AccessibilityModule: {e}")
            raise AccessibilityAPIUnavailableError(f"Accessibility API initialization failed: {e}")
    
    def _initialize_accessibility_api(self):
        """Initialize the accessibility API and check permissions."""
        if not ACCESSIBILITY_AVAILABLE:
            raise AccessibilityAPIUnavailableError("Accessibility frameworks not installed")
        
        try:
            # Initialize NSWorkspace for application management
            self.workspace = NSWorkspace.sharedWorkspace()
            
            # Test accessibility permissions by trying to get system-wide element
            system_wide = AppKit.AXUIElementCreateSystemWide()
            if system_wide is None:
                raise AccessibilityPermissionError("Cannot create system-wide accessibility element")
            
            # Try to get the focused application to test permissions
            focused_app = self._get_focused_application_element()
            if focused_app is None:
                self.logger.warning("Cannot access focused application - accessibility permissions may be limited")
            
            self.accessibility_enabled = True
            self.logger.info("AccessibilityModule initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Accessibility API initialization error: {e}")
            raise AccessibilityPermissionError(f"Accessibility permissions required: {e}")
    
    def _get_focused_application_element(self):
        """Get the accessibility element for the currently focused application."""
        try:
            system_wide = AppKit.AXUIElementCreateSystemWide()
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
            self.logger.error(f"Error getting active application: {e}")
            return None
    
    def is_accessibility_enabled(self) -> bool:
        """Check if accessibility API is enabled and functional."""
        return self.accessibility_enabled
    
    def get_accessibility_status(self) -> Dict[str, Any]:
        """
        Get detailed status of accessibility API availability.
        
        Returns:
            Dictionary with status information
        """
        status = {
            'frameworks_available': ACCESSIBILITY_AVAILABLE,
            'api_initialized': self.accessibility_enabled,
            'workspace_available': self.workspace is not None,
            'permissions_granted': False
        }
        
        if self.accessibility_enabled:
            # Test permissions by trying to access focused app
            focused_app = self._get_focused_application_element()
            status['permissions_granted'] = focused_app is not None
        
        return status
    
    def find_element(self, role: str, label: str, app_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Find UI element by role and label.
        
        Args:
            role: Accessibility role (e.g., 'AXButton', 'AXMenuItem')
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
        if not self.accessibility_enabled:
            return None
        
        try:
            # Get the target application element
            app_element = self._get_target_application_element(app_name)
            if not app_element:
                return None
            
            # Traverse the accessibility tree to find the element
            found_elements = self.traverse_accessibility_tree(app_element, max_depth=5)
            
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
                            'app_name': app_name or self._get_app_name_from_element(app_element)
                        }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding element {role}:'{label}': {e}")
            return None
    
    def traverse_accessibility_tree(self, element, max_depth: int = 5) -> List[Dict[str, Any]]:
        """
        Recursively traverse accessibility tree to find all elements.
        
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
            children = self._get_element_children(element)
            for child in children:
                child_elements = self.traverse_accessibility_tree(child, max_depth - 1)
                elements.extend(child_elements)
        
        except Exception as e:
            self.logger.debug(f"Error traversing element: {e}")
        
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
        """Check if element matches the search criteria."""
        # Check role match
        element_role = element_info.get('role', '')
        if role and role not in element_role:
            # Also check if role matches category
            element_category = self.classify_element_role(element_role)
            if role.lower() != element_category:
                return False
        
        # Check label match using fuzzy matching
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