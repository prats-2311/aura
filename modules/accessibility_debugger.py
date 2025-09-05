"""
AccessibilityDebugger for AURA - Comprehensive debugging and diagnostic tools

This module provides comprehensive debugging tools for accessibility issues,
including tree inspection, element analysis, and diagnostic reporting.
"""

import logging
import time
import json
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import threading
from collections import defaultdict

# Import accessibility frameworks with error handling
try:
    from ApplicationServices import (
        AXUIElementCreateSystemWide,
        AXUIElementCreateApplication,
        AXUIElementCopyAttributeValue,
        AXUIElementCopyAttributeNames,
        AXUIElementGetAttributeValueCount,
        kAXFocusedApplicationAttribute,
        kAXRoleAttribute,
        kAXTitleAttribute,
        kAXDescriptionAttribute,
        kAXValueAttribute,
        kAXEnabledAttribute,
        kAXChildrenAttribute,
        kAXPositionAttribute,
        kAXSizeAttribute,
        kAXWindowAttribute,
        kAXApplicationAttribute,
        kAXParentAttribute,
        kAXHelpAttribute,
        kAXIdentifierAttribute
    )
    ACCESSIBILITY_FUNCTIONS_AVAILABLE = True
except ImportError:
    ACCESSIBILITY_FUNCTIONS_AVAILABLE = False

try:
    from AppKit import NSWorkspace, NSRunningApplication
    APPKIT_AVAILABLE = True
except ImportError:
    APPKIT_AVAILABLE = False

# Import fuzzy matching with error handling
try:
    from thefuzz import fuzz, process
    FUZZY_MATCHING_AVAILABLE = True
except ImportError:
    FUZZY_MATCHING_AVAILABLE = False


@dataclass
class AccessibilityTreeElement:
    """Represents a single element in the accessibility tree."""
    role: str
    title: Optional[str] = None
    description: Optional[str] = None
    value: Optional[str] = None
    identifier: Optional[str] = None
    enabled: bool = True
    position: Optional[Tuple[int, int]] = None
    size: Optional[Tuple[int, int]] = None
    children_count: int = 0
    parent_role: Optional[str] = None
    depth: int = 0
    element_id: Optional[str] = None
    all_attributes: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    def get_searchable_text(self) -> List[str]:
        """Get all searchable text from this element."""
        texts = []
        if self.title:
            texts.append(self.title)
        if self.description:
            texts.append(self.description)
        if self.value:
            texts.append(self.value)
        if self.identifier:
            texts.append(self.identifier)
        return [text for text in texts if text and text.strip()]


@dataclass
class AccessibilityTreeDump:
    """Complete accessibility tree structure."""
    app_name: str
    app_pid: Optional[int]
    timestamp: datetime
    root_element: Dict[str, Any]
    total_elements: int
    clickable_elements: List[Dict[str, Any]]
    searchable_elements: List[Dict[str, Any]]
    element_roles: Dict[str, int]  # Role counts
    attribute_coverage: Dict[str, int]  # Attribute availability
    tree_depth: int
    generation_time_ms: float

    def find_elements_by_text(self, text: str, fuzzy: bool = True, threshold: float = 80.0) -> List[Dict[str, Any]]:
        """Find elements matching text with optional fuzzy matching."""
        matches = []
        
        for element in self.searchable_elements:
            element_texts = []
            if element.get('title'):
                element_texts.append(element['title'])
            if element.get('description'):
                element_texts.append(element['description'])
            if element.get('value'):
                element_texts.append(element['value'])
            
            for element_text in element_texts:
                if fuzzy and FUZZY_MATCHING_AVAILABLE:
                    score = fuzz.ratio(text.lower(), element_text.lower())
                    if score >= threshold:
                        match_info = element.copy()
                        match_info['match_score'] = score
                        match_info['matched_text'] = element_text
                        matches.append(match_info)
                else:
                    if text.lower() in element_text.lower():
                        match_info = element.copy()
                        match_info['match_score'] = 100.0
                        match_info['matched_text'] = element_text
                        matches.append(match_info)
        
        # Sort by match score (highest first)
        matches.sort(key=lambda x: x.get('match_score', 0), reverse=True)
        return matches

    def get_elements_by_role(self, role: str) -> List[Dict[str, Any]]:
        """Get all elements with specific role."""
        return [elem for elem in self.searchable_elements if elem.get('role') == role]

    def to_json(self) -> str:
        """Export tree dump as JSON for analysis."""
        # Convert datetime to string for JSON serialization
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return json.dumps(data, indent=2, default=str)

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the tree dump."""
        return {
            'app_name': self.app_name,
            'total_elements': self.total_elements,
            'clickable_elements': len(self.clickable_elements),
            'searchable_elements': len(self.searchable_elements),
            'tree_depth': self.tree_depth,
            'generation_time_ms': self.generation_time_ms,
            'top_roles': dict(sorted(self.element_roles.items(), key=lambda x: x[1], reverse=True)[:10]),
            'attribute_coverage': self.attribute_coverage
        }


@dataclass
class ElementAnalysisResult:
    """Result from element analysis and search operations."""
    target_text: str
    search_strategy: str
    matches_found: int
    best_match: Optional[Dict[str, Any]]
    all_matches: List[Dict[str, Any]]
    similarity_scores: Dict[str, float]
    search_time_ms: float
    recommendations: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return asdict(self)


class AccessibilityDebugger:
    """
    Comprehensive debugging and diagnostic tools for accessibility issues.
    """

    # Standard accessibility attributes to inspect
    STANDARD_ATTRIBUTES = [
        'AXRole', 'AXTitle', 'AXDescription', 'AXValue', 'AXEnabled',
        'AXPosition', 'AXSize', 'AXChildren', 'AXParent', 'AXWindow',
        'AXApplication', 'AXHelp', 'AXIdentifier', 'AXFocused',
        'AXSelected', 'AXExpanded', 'AXMinimized'
    ]

    # Clickable element roles for analysis
    CLICKABLE_ROLES = {
        'AXButton', 'AXMenuButton', 'AXMenuItem', 'AXMenuBarItem',
        'AXLink', 'AXCheckBox', 'AXRadioButton', 'AXTab',
        'AXToolbarButton', 'AXPopUpButton', 'AXComboBox'
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the AccessibilityDebugger.

        Args:
            config: Configuration dictionary with debugging options
        """
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        
        # Configuration options
        self.debug_level = self.config.get('debug_level', 'BASIC')
        self.output_format = self.config.get('output_format', 'STRUCTURED')
        self.auto_diagnostics = self.config.get('auto_diagnostics', True)
        self.performance_tracking = self.config.get('performance_tracking', True)
        self.max_tree_depth = self.config.get('max_tree_depth', 10)
        self.max_elements_per_level = self.config.get('max_elements_per_level', 100)
        self.include_invisible_elements = self.config.get('include_invisible_elements', False)
        
        # Threading for concurrent operations
        self.tree_lock = threading.RLock()
        
        # Cache for tree dumps
        self.tree_cache: Dict[str, AccessibilityTreeDump] = {}
        self.cache_ttl = self.config.get('cache_ttl_seconds', 60)
        
        # Workspace for application management
        self.workspace = None
        if APPKIT_AVAILABLE:
            self.workspace = NSWorkspace.sharedWorkspace()
        
        # Validate availability
        if not ACCESSIBILITY_FUNCTIONS_AVAILABLE:
            self.logger.warning("Accessibility functions not available - debugging capabilities limited")
        if not APPKIT_AVAILABLE:
            self.logger.warning("AppKit not available - application detection limited")
        if not FUZZY_MATCHING_AVAILABLE:
            self.logger.warning("Fuzzy matching not available - using exact matching only")

    def dump_accessibility_tree(self, app_name: Optional[str] = None, 
                              force_refresh: bool = False) -> AccessibilityTreeDump:
        """
        Generate complete accessibility tree dump for analysis.

        Args:
            app_name: Optional application name to focus on (defaults to focused app)
            force_refresh: Force refresh even if cached version exists

        Returns:
            Structured accessibility tree with all elements and attributes
        """
        start_time = time.time()
        
        try:
            # Determine target application
            if not app_name:
                app_name = self._get_focused_application_name()
                if not app_name:
                    raise ValueError("No focused application found and no app_name specified")
            
            # Check cache first
            cache_key = f"{app_name}_{self.debug_level}"
            if not force_refresh and cache_key in self.tree_cache:
                cached_dump = self.tree_cache[cache_key]
                cache_age = (datetime.now() - cached_dump.timestamp).total_seconds()
                if cache_age < self.cache_ttl:
                    self.logger.debug(f"Using cached tree dump for {app_name} (age: {cache_age:.1f}s)")
                    return cached_dump
            
            self.logger.info(f"Generating accessibility tree dump for application: {app_name}")
            
            # Get application element
            app_element = self._get_application_element(app_name)
            if not app_element:
                raise ValueError(f"Cannot access application element for {app_name}")
            
            # Get application PID
            app_pid = self._get_application_pid(app_name)
            
            # Traverse the accessibility tree
            root_element_data, all_elements = self._traverse_accessibility_tree(
                app_element, max_depth=self.max_tree_depth
            )
            
            # Analyze elements
            clickable_elements = [elem for elem in all_elements 
                                if elem.get('role') in self.CLICKABLE_ROLES]
            
            searchable_elements = [elem for elem in all_elements 
                                 if self._has_searchable_content(elem)]
            
            # Count roles and attributes
            element_roles = defaultdict(int)
            attribute_coverage = defaultdict(int)
            max_depth = 0
            
            for elem in all_elements:
                if elem.get('role'):
                    element_roles[elem['role']] += 1
                if elem.get('depth', 0) > max_depth:
                    max_depth = elem['depth']
                
                # Count available attributes
                if elem.get('all_attributes'):
                    for attr in elem['all_attributes'].keys():
                        attribute_coverage[attr] += 1
            
            generation_time_ms = (time.time() - start_time) * 1000
            
            # Create tree dump
            tree_dump = AccessibilityTreeDump(
                app_name=app_name,
                app_pid=app_pid,
                timestamp=datetime.now(),
                root_element=root_element_data,
                total_elements=len(all_elements),
                clickable_elements=clickable_elements,
                searchable_elements=searchable_elements,
                element_roles=dict(element_roles),
                attribute_coverage=dict(attribute_coverage),
                tree_depth=max_depth,
                generation_time_ms=generation_time_ms
            )
            
            # Cache the result
            with self.tree_lock:
                self.tree_cache[cache_key] = tree_dump
                # Clean old cache entries
                self._cleanup_tree_cache()
            
            self.logger.info(f"Tree dump completed: {len(all_elements)} elements, "
                           f"{len(clickable_elements)} clickable, {generation_time_ms:.1f}ms")
            
            return tree_dump
            
        except Exception as e:
            self.logger.error(f"Failed to dump accessibility tree: {e}")
            raise

    def analyze_element_detection_failure(self, command: str, target: str, 
                                        app_name: Optional[str] = None) -> ElementAnalysisResult:
        """
        Analyze why element detection failed for a specific command.

        Args:
            command: Original user command
            target: Extracted target text
            app_name: Optional application name

        Returns:
            Detailed analysis of failure reasons and potential solutions
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"Analyzing element detection failure for target: '{target}'")
            
            # Get tree dump for analysis
            tree_dump = self.dump_accessibility_tree(app_name)
            
            # Try different search strategies
            search_results = {}
            
            # Strategy 1: Exact text matching
            exact_matches = self._find_exact_matches(tree_dump, target)
            search_results['exact'] = exact_matches
            
            # Strategy 2: Fuzzy text matching
            if FUZZY_MATCHING_AVAILABLE:
                fuzzy_matches = tree_dump.find_elements_by_text(target, fuzzy=True, threshold=60.0)
                search_results['fuzzy'] = fuzzy_matches
            else:
                search_results['fuzzy'] = []
            
            # Strategy 3: Partial text matching
            partial_matches = self._find_partial_matches(tree_dump, target)
            search_results['partial'] = partial_matches
            
            # Strategy 4: Role-based matching
            role_matches = self._find_role_based_matches(tree_dump, target)
            search_results['role_based'] = role_matches
            
            # Combine all matches and calculate similarity scores
            all_matches = []
            similarity_scores = {}
            
            for strategy, matches in search_results.items():
                for match in matches:
                    match['search_strategy'] = strategy
                    all_matches.append(match)
                    
                    # Calculate similarity score
                    match_text = match.get('matched_text', match.get('title', ''))
                    if match_text and FUZZY_MATCHING_AVAILABLE:
                        score = fuzz.ratio(target.lower(), match_text.lower())
                        similarity_scores[f"{strategy}_{match.get('element_id', len(all_matches))}"] = score
            
            # Remove duplicates and sort by relevance
            unique_matches = self._deduplicate_matches(all_matches)
            unique_matches.sort(key=lambda x: x.get('match_score', 0), reverse=True)
            
            # Determine best match
            best_match = unique_matches[0] if unique_matches else None
            
            # Generate recommendations
            recommendations = self._generate_search_recommendations(
                target, tree_dump, search_results, unique_matches
            )
            
            search_time_ms = (time.time() - start_time) * 1000
            
            result = ElementAnalysisResult(
                target_text=target,
                search_strategy="multi_strategy",
                matches_found=len(unique_matches),
                best_match=best_match,
                all_matches=unique_matches[:10],  # Limit to top 10
                similarity_scores=similarity_scores,
                search_time_ms=search_time_ms,
                recommendations=recommendations
            )
            
            self.logger.info(f"Analysis completed: {len(unique_matches)} matches found, "
                           f"best score: {best_match.get('match_score', 0) if best_match else 0}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to analyze element detection failure: {e}")
            raise

    def _get_focused_application_name(self) -> Optional[str]:
        """Get the name of the currently focused application."""
        try:
            if not ACCESSIBILITY_FUNCTIONS_AVAILABLE:
                return None
            
            system_wide = AXUIElementCreateSystemWide()
            if not system_wide:
                return None
            
            focused_app = AXUIElementCopyAttributeValue(system_wide, kAXFocusedApplicationAttribute)
            if not focused_app:
                return None
            
            app_name = AXUIElementCopyAttributeValue(focused_app, kAXTitleAttribute)
            return str(app_name) if app_name else None
            
        except Exception as e:
            self.logger.debug(f"Failed to get focused application name: {e}")
            return None

    def _get_application_element(self, app_name: str):
        """Get the accessibility element for a specific application."""
        try:
            if not ACCESSIBILITY_FUNCTIONS_AVAILABLE or not self.workspace:
                return None
            
            # Find running application
            running_apps = self.workspace.runningApplications()
            target_app = None
            
            for app in running_apps:
                if app.localizedName() == app_name or app.bundleIdentifier() == app_name:
                    target_app = app
                    break
            
            if not target_app:
                self.logger.warning(f"Application '{app_name}' not found in running applications")
                return None
            
            # Create accessibility element for the application
            app_element = AXUIElementCreateApplication(target_app.processIdentifier())
            return app_element
            
        except Exception as e:
            self.logger.error(f"Failed to get application element for {app_name}: {e}")
            return None

    def _get_application_pid(self, app_name: str) -> Optional[int]:
        """Get the process ID for a specific application."""
        try:
            if not self.workspace:
                return None
            
            running_apps = self.workspace.runningApplications()
            for app in running_apps:
                if app.localizedName() == app_name or app.bundleIdentifier() == app_name:
                    return app.processIdentifier()
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Failed to get PID for {app_name}: {e}")
            return None

    def _traverse_accessibility_tree(self, element, max_depth: int = 10, 
                                   current_depth: int = 0, parent_role: Optional[str] = None) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Traverse the accessibility tree and extract all elements.

        Args:
            element: Root accessibility element
            max_depth: Maximum depth to traverse
            current_depth: Current traversal depth
            parent_role: Role of parent element

        Returns:
            Tuple of (root_element_data, all_elements_list)
        """
        all_elements = []
        
        try:
            # Extract element information
            element_data = self._extract_element_info(element, current_depth, parent_role)
            all_elements.append(element_data)
            
            # Stop if we've reached max depth
            if current_depth >= max_depth:
                return element_data, all_elements
            
            # Get children if available
            children = None
            try:
                children = AXUIElementCopyAttributeValue(element, kAXChildrenAttribute)
            except Exception as e:
                self.logger.debug(f"Failed to get children at depth {current_depth}: {e}")
            
            if children and len(children) > 0:
                element_data['children'] = []
                
                # Limit children to prevent excessive processing
                children_to_process = children[:self.max_elements_per_level]
                if len(children) > self.max_elements_per_level:
                    self.logger.debug(f"Limiting children from {len(children)} to {self.max_elements_per_level}")
                
                for child in children_to_process:
                    try:
                        child_data, child_elements = self._traverse_accessibility_tree(
                            child, max_depth, current_depth + 1, element_data.get('role')
                        )
                        element_data['children'].append(child_data)
                        all_elements.extend(child_elements)
                        
                    except Exception as e:
                        self.logger.debug(f"Failed to process child at depth {current_depth + 1}: {e}")
                        continue
            
            return element_data, all_elements
            
        except Exception as e:
            self.logger.error(f"Failed to traverse accessibility tree at depth {current_depth}: {e}")
            # Return minimal element data with error information
            minimal_data = {
                'role': 'unknown',
                'title': None,
                'depth': current_depth,
                'parent_role': parent_role,
                'element_id': f"error_elem_{current_depth}",
                'all_attributes': {},
                'description': None,
                'value': None,
                'enabled': True,
                'children_count': 0,
                'error': str(e)
            }
            return minimal_data, [minimal_data]

    def _extract_element_info(self, element, depth: int, parent_role: Optional[str]) -> Dict[str, Any]:
        """Extract comprehensive information from an accessibility element."""
        element_data = {
            'depth': depth,
            'parent_role': parent_role,
            'element_id': f"elem_{id(element)}_{depth}",
            'all_attributes': {}
        }
        
        # Track if any attributes were successfully extracted
        successful_attributes = 0
        total_errors = []
        
        # Extract standard attributes
        for attr_name in self.STANDARD_ATTRIBUTES:
            try:
                attr_value = AXUIElementCopyAttributeValue(element, attr_name)
                if attr_value is not None:
                    successful_attributes += 1
                    # Convert to appropriate Python type
                    if attr_name in ['AXPosition', 'AXSize']:
                        if hasattr(attr_value, 'x') and hasattr(attr_value, 'y'):
                            element_data[attr_name.lower().replace('ax', '')] = (attr_value.x, attr_value.y)
                        elif hasattr(attr_value, 'width') and hasattr(attr_value, 'height'):
                            element_data[attr_name.lower().replace('ax', '')] = (attr_value.width, attr_value.height)
                        else:
                            element_data[attr_name.lower().replace('ax', '')] = str(attr_value)
                    elif attr_name == 'AXChildren':
                        element_data['children_count'] = len(attr_value) if attr_value else 0
                    else:
                        element_data[attr_name.lower().replace('ax', '')] = str(attr_value)
                    
                    element_data['all_attributes'][attr_name] = str(attr_value)
                    
            except Exception as e:
                total_errors.append(f"{attr_name}: {str(e)}")
                self.logger.debug(f"Failed to get attribute {attr_name}: {e}")
                continue
        
        # If no attributes were successfully extracted, add error information
        if successful_attributes == 0 and total_errors:
            element_data['error'] = f"Failed to extract any attributes: {'; '.join(total_errors[:3])}"
        
        # Ensure required fields have defaults
        element_data.setdefault('role', 'unknown')
        element_data.setdefault('title', None)
        element_data.setdefault('description', None)
        element_data.setdefault('value', None)
        element_data.setdefault('enabled', True)
        element_data.setdefault('children_count', 0)
        
        return element_data

    def _has_searchable_content(self, element: Dict[str, Any]) -> bool:
        """Check if an element has searchable text content."""
        searchable_fields = ['title', 'description', 'value', 'identifier']
        return any(element.get(field) and str(element[field]).strip() 
                  for field in searchable_fields)

    def _find_exact_matches(self, tree_dump: AccessibilityTreeDump, target: str) -> List[Dict[str, Any]]:
        """Find elements with exact text matches."""
        matches = []
        target_lower = target.lower().strip()
        
        for element in tree_dump.searchable_elements:
            searchable_texts = []
            if element.get('title'):
                searchable_texts.append(element['title'])
            if element.get('description'):
                searchable_texts.append(element['description'])
            if element.get('value'):
                searchable_texts.append(element['value'])
            
            for text in searchable_texts:
                if text and text.lower().strip() == target_lower:
                    match = element.copy()
                    match['match_score'] = 100.0
                    match['matched_text'] = text
                    matches.append(match)
        
        return matches

    def _find_partial_matches(self, tree_dump: AccessibilityTreeDump, target: str) -> List[Dict[str, Any]]:
        """Find elements with partial text matches."""
        matches = []
        target_lower = target.lower().strip()
        
        for element in tree_dump.searchable_elements:
            searchable_texts = []
            if element.get('title'):
                searchable_texts.append(element['title'])
            if element.get('description'):
                searchable_texts.append(element['description'])
            if element.get('value'):
                searchable_texts.append(element['value'])
            
            for text in searchable_texts:
                if text and target_lower in text.lower():
                    match = element.copy()
                    # Calculate partial match score
                    match_score = (len(target_lower) / len(text.lower())) * 100
                    match['match_score'] = min(match_score, 95.0)  # Cap at 95% for partial matches
                    match['matched_text'] = text
                    matches.append(match)
        
        return matches

    def _find_role_based_matches(self, tree_dump: AccessibilityTreeDump, target: str) -> List[Dict[str, Any]]:
        """Find elements based on role and context."""
        matches = []
        
        # Look for clickable elements that might match the target
        for element in tree_dump.clickable_elements:
            if element.get('role') in self.CLICKABLE_ROLES:
                # Check if any text content partially matches
                searchable_texts = []
                if element.get('title'):
                    searchable_texts.append(element['title'])
                if element.get('description'):
                    searchable_texts.append(element['description'])
                
                for text in searchable_texts:
                    if text and any(word in text.lower() for word in target.lower().split()):
                        match = element.copy()
                        match['match_score'] = 70.0  # Lower score for role-based matches
                        match['matched_text'] = text
                        matches.append(match)
        
        return matches

    def _deduplicate_matches(self, matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate matches based on element position and content."""
        unique_matches = []
        seen_elements = set()
        
        for match in matches:
            # Create a unique key based on position and text
            position = match.get('position', (0, 0))
            text = match.get('matched_text', match.get('title', ''))
            role = match.get('role', '')
            
            element_key = f"{position}_{text}_{role}"
            
            if element_key not in seen_elements:
                seen_elements.add(element_key)
                unique_matches.append(match)
        
        return unique_matches

    def _generate_search_recommendations(self, target: str, tree_dump: AccessibilityTreeDump,
                                       search_results: Dict[str, List], matches: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations for improving element detection."""
        recommendations = []
        
        # Analyze search results
        total_matches = sum(len(results) for results in search_results.values())
        
        if total_matches == 0:
            recommendations.append(f"No elements found matching '{target}'. Consider:")
            recommendations.append("- Check if the target text is exactly as displayed in the UI")
            recommendations.append("- Try a shorter or more specific portion of the text")
            recommendations.append("- Verify the application is in the correct state")
            
            # Suggest similar elements
            if tree_dump.clickable_elements:
                recommendations.append("Available clickable elements:")
                for elem in tree_dump.clickable_elements[:5]:
                    title = elem.get('title', 'No title')
                    role = elem.get('role', 'Unknown')
                    recommendations.append(f"  - {role}: '{title}'")
        
        elif total_matches == 1:
            recommendations.append("Single match found - this should work for element detection")
        
        elif total_matches > 1:
            recommendations.append(f"Multiple matches found ({total_matches}). Consider:")
            recommendations.append("- Use more specific text to narrow down the match")
            recommendations.append("- Check if there are duplicate elements in the UI")
            
            # Show top matches
            if matches:
                recommendations.append("Top matches found:")
                for i, match in enumerate(matches[:3]):
                    title = match.get('matched_text', match.get('title', 'No title'))
                    role = match.get('role', 'Unknown')
                    score = match.get('match_score', 0)
                    recommendations.append(f"  {i+1}. {role}: '{title}' (score: {score:.1f})")
        
        # Analyze attribute coverage
        if tree_dump.attribute_coverage:
            missing_attrs = []
            for attr in ['AXTitle', 'AXDescription', 'AXValue']:
                if attr not in tree_dump.attribute_coverage:
                    missing_attrs.append(attr)
            
            if missing_attrs:
                recommendations.append(f"Some elements may be missing attributes: {', '.join(missing_attrs)}")
        
        return recommendations

    def _cleanup_tree_cache(self):
        """Clean up expired entries from the tree cache."""
        current_time = datetime.now()
        expired_keys = []
        
        for key, tree_dump in self.tree_cache.items():
            age = (current_time - tree_dump.timestamp).total_seconds()
            if age > self.cache_ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.tree_cache[key]
        
        if expired_keys:
            self.logger.debug(f"Cleaned up {len(expired_keys)} expired tree cache entries")

    def interactive_element_search(self, target_text: str, app_name: Optional[str] = None,
                                 search_strategies: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Interactive element search with multiple strategies and detailed analysis.

        Args:
            target_text: Text to search for
            app_name: Optional application name
            search_strategies: List of strategies to use ['exact', 'fuzzy', 'partial', 'role_based']

        Returns:
            Comprehensive search results with analysis
        """
        start_time = time.time()
        
        if search_strategies is None:
            search_strategies = ['exact', 'fuzzy', 'partial', 'role_based']
        
        try:
            self.logger.info(f"Starting interactive element search for: '{target_text}'")
            
            # Get tree dump
            tree_dump = self.dump_accessibility_tree(app_name)
            
            # Execute search strategies
            search_results = {}
            total_matches = 0
            
            for strategy in search_strategies:
                strategy_start = time.time()
                
                if strategy == 'exact':
                    matches = self._find_exact_matches(tree_dump, target_text)
                elif strategy == 'fuzzy' and FUZZY_MATCHING_AVAILABLE:
                    matches = tree_dump.find_elements_by_text(target_text, fuzzy=True, threshold=60.0)
                elif strategy == 'partial':
                    matches = self._find_partial_matches(tree_dump, target_text)
                elif strategy == 'role_based':
                    matches = self._find_role_based_matches(tree_dump, target_text)
                else:
                    matches = []
                
                strategy_time = (time.time() - strategy_start) * 1000
                search_results[strategy] = {
                    'matches': matches,
                    'count': len(matches),
                    'time_ms': strategy_time
                }
                total_matches += len(matches)
                
                self.logger.debug(f"Strategy '{strategy}': {len(matches)} matches in {strategy_time:.1f}ms")
            
            # Analyze and rank all matches
            all_matches = []
            for strategy, results in search_results.items():
                for match in results['matches']:
                    match['search_strategy'] = strategy
                    all_matches.append(match)
            
            # Remove duplicates and rank
            unique_matches = self._deduplicate_matches(all_matches)
            ranked_matches = self._rank_matches_by_relevance(unique_matches, target_text)
            
            # Generate detailed analysis
            analysis = self._generate_detailed_match_analysis(target_text, ranked_matches, tree_dump)
            
            search_time_ms = (time.time() - start_time) * 1000
            
            result = {
                'target_text': target_text,
                'app_name': tree_dump.app_name,
                'search_strategies_used': search_strategies,
                'total_search_time_ms': search_time_ms,
                'strategy_results': search_results,
                'total_unique_matches': len(unique_matches),
                'ranked_matches': ranked_matches[:10],  # Top 10 matches
                'best_match': ranked_matches[0] if ranked_matches else None,
                'analysis': analysis,
                'tree_summary': tree_dump.get_summary()
            }
            
            self.logger.info(f"Interactive search completed: {len(unique_matches)} unique matches in {search_time_ms:.1f}ms")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Interactive element search failed: {e}")
            raise

    def compare_elements(self, element1: Dict[str, Any], element2: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare two elements for debugging failed matches.

        Args:
            element1: First element to compare
            element2: Second element to compare

        Returns:
            Detailed comparison analysis
        """
        try:
            comparison = {
                'elements': {
                    'element1': element1,
                    'element2': element2
                },
                'similarities': {},
                'differences': {},
                'match_potential': 0.0,
                'recommendations': []
            }
            
            # Compare basic attributes
            basic_attrs = ['role', 'title', 'description', 'value', 'enabled']
            for attr in basic_attrs:
                val1 = element1.get(attr)
                val2 = element2.get(attr)
                
                if val1 == val2:
                    comparison['similarities'][attr] = val1
                else:
                    comparison['differences'][attr] = {'element1': val1, 'element2': val2}
            
            # Compare positions if available
            pos1 = element1.get('position')
            pos2 = element2.get('position')
            if pos1 and pos2:
                distance = ((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2) ** 0.5
                comparison['position_distance'] = distance
                if distance < 50:  # Close positions
                    comparison['similarities']['nearby_position'] = True
                else:
                    comparison['differences']['position'] = {'element1': pos1, 'element2': pos2}
            
            # Text similarity analysis
            text1 = self._get_element_text_content(element1)
            text2 = self._get_element_text_content(element2)
            
            if text1 and text2 and FUZZY_MATCHING_AVAILABLE:
                similarity_score = fuzz.ratio(text1.lower(), text2.lower())
                comparison['text_similarity_score'] = similarity_score
                comparison['text_content'] = {'element1': text1, 'element2': text2}
                
                if similarity_score > 80:
                    comparison['similarities']['high_text_similarity'] = similarity_score
                elif similarity_score > 50:
                    comparison['similarities']['moderate_text_similarity'] = similarity_score
                else:
                    comparison['differences']['low_text_similarity'] = similarity_score
            
            # Calculate overall match potential
            similarity_count = len(comparison['similarities'])
            difference_count = len(comparison['differences'])
            total_comparisons = similarity_count + difference_count
            
            if total_comparisons > 0:
                comparison['match_potential'] = (similarity_count / total_comparisons) * 100
            
            # Generate recommendations
            if comparison['match_potential'] > 70:
                comparison['recommendations'].append("Elements are very similar - likely the same element")
            elif comparison['match_potential'] > 40:
                comparison['recommendations'].append("Elements have some similarities - could be related")
                if 'role' in comparison['similarities']:
                    comparison['recommendations'].append("Same role - check if text content differs")
            else:
                comparison['recommendations'].append("Elements are quite different")
                if 'role' in comparison['differences']:
                    comparison['recommendations'].append("Different roles - may need different detection strategy")
            
            return comparison
            
        except Exception as e:
            self.logger.error(f"Element comparison failed: {e}")
            raise

    def analyze_fuzzy_matching_scores(self, target_text: str, elements: List[Dict[str, Any]],
                                    threshold_range: Tuple[float, float] = (50.0, 95.0)) -> Dict[str, Any]:
        """
        Analyze fuzzy matching scores across different thresholds.

        Args:
            target_text: Text to match against
            elements: List of elements to analyze
            threshold_range: Range of thresholds to test (min, max)

        Returns:
            Detailed fuzzy matching analysis
        """
        if not FUZZY_MATCHING_AVAILABLE:
            return {
                'error': 'Fuzzy matching not available',
                'recommendation': 'Install thefuzz library: pip install thefuzz[speedup]'
            }
        
        try:
            analysis = {
                'target_text': target_text,
                'total_elements': len(elements),
                'threshold_analysis': {},
                'score_distribution': {},
                'best_matches': [],
                'recommendations': []
            }
            
            # Test different thresholds
            thresholds = [50.0, 60.0, 70.0, 80.0, 90.0, 95.0]
            thresholds = [t for t in thresholds if threshold_range[0] <= t <= threshold_range[1]]
            
            all_scores = []
            
            for element in elements:
                element_texts = []
                if element.get('title'):
                    element_texts.append(element['title'])
                if element.get('description'):
                    element_texts.append(element['description'])
                if element.get('value'):
                    element_texts.append(element['value'])
                
                best_score = 0.0
                best_text = None
                
                for text in element_texts:
                    if text:
                        score = fuzz.ratio(target_text.lower(), text.lower())
                        all_scores.append(score)
                        if score > best_score:
                            best_score = score
                            best_text = text
                
                if best_score > 0:
                    element_copy = element.copy()
                    element_copy['fuzzy_score'] = best_score
                    element_copy['matched_text'] = best_text
                    analysis['best_matches'].append(element_copy)
            
            # Sort by score
            analysis['best_matches'].sort(key=lambda x: x.get('fuzzy_score', 0), reverse=True)
            
            # Analyze threshold effectiveness
            for threshold in thresholds:
                matches_at_threshold = [m for m in analysis['best_matches'] 
                                      if m.get('fuzzy_score', 0) >= threshold]
                analysis['threshold_analysis'][threshold] = {
                    'matches': len(matches_at_threshold),
                    'percentage': (len(matches_at_threshold) / len(elements)) * 100 if elements else 0
                }
            
            # Score distribution
            if all_scores:
                analysis['score_distribution'] = {
                    'min': min(all_scores),
                    'max': max(all_scores),
                    'average': sum(all_scores) / len(all_scores),
                    'scores_above_80': len([s for s in all_scores if s >= 80]),
                    'scores_above_60': len([s for s in all_scores if s >= 60]),
                    'scores_below_50': len([s for s in all_scores if s < 50])
                }
            
            # Generate recommendations
            if analysis['best_matches']:
                best_score = analysis['best_matches'][0].get('fuzzy_score', 0)
                if best_score >= 90:
                    analysis['recommendations'].append(f"Excellent match found (score: {best_score:.1f}) - should work reliably")
                elif best_score >= 70:
                    analysis['recommendations'].append(f"Good match found (score: {best_score:.1f}) - likely to work")
                elif best_score >= 50:
                    analysis['recommendations'].append(f"Moderate match found (score: {best_score:.1f}) - may need adjustment")
                else:
                    analysis['recommendations'].append(f"Low match scores (best: {best_score:.1f}) - consider different text")
            
            # Threshold recommendations
            good_thresholds = [t for t, data in analysis['threshold_analysis'].items() 
                             if 1 <= data['matches'] <= 3]
            if good_thresholds:
                analysis['recommendations'].append(f"Recommended thresholds: {good_thresholds}")
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Fuzzy matching analysis failed: {e}")
            raise

    def get_element_context(self, element: Dict[str, Any], tree_dump: AccessibilityTreeDump,
                          context_radius: int = 2) -> Dict[str, Any]:
        """
        Get contextual information about an element (parent, siblings, children).

        Args:
            element: Element to analyze
            tree_dump: Tree dump containing the element
            context_radius: How many levels up/down to include

        Returns:
            Contextual information about the element
        """
        try:
            context = {
                'target_element': element,
                'parent_elements': [],
                'sibling_elements': [],
                'child_elements': [],
                'context_summary': {}
            }
            
            element_depth = element.get('depth', 0)
            element_position = element.get('position')
            
            # Find related elements by depth and position
            for other_element in tree_dump.searchable_elements:
                other_depth = other_element.get('depth', 0)
                other_position = other_element.get('position')
                
                # Skip the element itself
                if other_element.get('element_id') == element.get('element_id'):
                    continue
                
                # Parent elements (higher in tree, lower depth)
                if other_depth < element_depth and other_depth >= element_depth - context_radius:
                    context['parent_elements'].append(other_element)
                
                # Sibling elements (same depth, similar position)
                elif other_depth == element_depth:
                    if element_position and other_position:
                        # Check if positions are reasonably close (within 200 pixels)
                        distance = ((element_position[0] - other_position[0]) ** 2 + 
                                  (element_position[1] - other_position[1]) ** 2) ** 0.5
                        if distance < 200:
                            context['sibling_elements'].append(other_element)
                    else:
                        # If no position info, include all siblings
                        context['sibling_elements'].append(other_element)
                
                # Child elements (lower in tree, higher depth)
                elif other_depth > element_depth and other_depth <= element_depth + context_radius:
                    context['child_elements'].append(other_element)
            
            # Generate context summary
            context['context_summary'] = {
                'parent_count': len(context['parent_elements']),
                'sibling_count': len(context['sibling_elements']),
                'child_count': len(context['child_elements']),
                'element_depth': element_depth,
                'has_position_info': element_position is not None
            }
            
            # Add parent roles for context
            parent_roles = [p.get('role') for p in context['parent_elements']]
            context['context_summary']['parent_roles'] = list(set(parent_roles))
            
            # Add sibling roles
            sibling_roles = [s.get('role') for s in context['sibling_elements']]
            context['context_summary']['sibling_roles'] = list(set(sibling_roles))
            
            return context
            
        except Exception as e:
            self.logger.error(f"Failed to get element context: {e}")
            raise

    def _rank_matches_by_relevance(self, matches: List[Dict[str, Any]], target_text: str) -> List[Dict[str, Any]]:
        """Rank matches by relevance using multiple criteria."""
        def calculate_relevance_score(match):
            score = 0.0
            
            # Base score from match_score if available
            base_score = match.get('match_score', 0.0)
            score += base_score * 0.4  # 40% weight
            
            # Bonus for exact matches
            matched_text = match.get('matched_text', match.get('title', ''))
            if matched_text and matched_text.lower().strip() == target_text.lower().strip():
                score += 30.0
            
            # Bonus for clickable elements
            if match.get('role') in self.CLICKABLE_ROLES:
                score += 20.0
            
            # Bonus for enabled elements
            if match.get('enabled', True):
                score += 10.0
            
            # Penalty for very long text (less likely to be the target)
            if matched_text and len(matched_text) > len(target_text) * 3:
                score -= 10.0
            
            # Bonus for search strategy
            strategy = match.get('search_strategy', '')
            if strategy == 'exact':
                score += 15.0
            elif strategy == 'fuzzy':
                score += 10.0
            elif strategy == 'partial':
                score += 5.0
            
            return max(0.0, score)  # Ensure non-negative
        
        # Calculate relevance scores
        for match in matches:
            match['relevance_score'] = calculate_relevance_score(match)
        
        # Sort by relevance score (highest first)
        return sorted(matches, key=lambda x: x.get('relevance_score', 0), reverse=True)

    def _generate_detailed_match_analysis(self, target_text: str, matches: List[Dict[str, Any]], 
                                        tree_dump: AccessibilityTreeDump) -> Dict[str, Any]:
        """Generate detailed analysis of search matches."""
        analysis = {
            'match_quality': 'unknown',
            'confidence_level': 'low',
            'issues_found': [],
            'recommendations': [],
            'statistics': {}
        }
        
        if not matches:
            analysis['match_quality'] = 'no_matches'
            analysis['issues_found'].append('No elements found matching the target text')
            analysis['recommendations'].extend([
                'Verify the target text is exactly as displayed in the UI',
                'Try a shorter or more specific portion of the text',
                'Check if the application is in the correct state'
            ])
            return analysis
        
        # Analyze match quality
        best_match = matches[0]
        best_score = best_match.get('relevance_score', 0)
        
        if best_score >= 80:
            analysis['match_quality'] = 'excellent'
            analysis['confidence_level'] = 'high'
        elif best_score >= 60:
            analysis['match_quality'] = 'good'
            analysis['confidence_level'] = 'medium'
        elif best_score >= 40:
            analysis['match_quality'] = 'fair'
            analysis['confidence_level'] = 'medium'
        else:
            analysis['match_quality'] = 'poor'
            analysis['confidence_level'] = 'low'
        
        # Check for multiple high-scoring matches
        high_score_matches = [m for m in matches if m.get('relevance_score', 0) >= 70]
        if len(high_score_matches) > 1:
            analysis['issues_found'].append(f'Multiple high-scoring matches found ({len(high_score_matches)})')
            analysis['recommendations'].append('Use more specific text to narrow down the match')
        
        # Check for clickable elements
        clickable_matches = [m for m in matches if m.get('role') in self.CLICKABLE_ROLES]
        if not clickable_matches:
            analysis['issues_found'].append('No clickable elements found in matches')
            analysis['recommendations'].append('Target may not be a clickable element')
        
        # Statistics
        analysis['statistics'] = {
            'total_matches': len(matches),
            'clickable_matches': len(clickable_matches),
            'enabled_matches': len([m for m in matches if m.get('enabled', True)]),
            'exact_matches': len([m for m in matches if m.get('search_strategy') == 'exact']),
            'fuzzy_matches': len([m for m in matches if m.get('search_strategy') == 'fuzzy']),
            'average_relevance_score': sum(m.get('relevance_score', 0) for m in matches) / len(matches)
        }
        
        return analysis

    def _get_element_text_content(self, element: Dict[str, Any]) -> Optional[str]:
        """Get the primary text content of an element."""
        for field in ['title', 'description', 'value']:
            text = element.get(field)
            if text and text.strip():
                return text.strip()
        return None