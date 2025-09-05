"""
Integration tests for BrowserAccessibilityHandler module.

Tests browser-specific accessibility handling with real web pages and applications.
"""

import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
import time
from typing import Dict, Any, Optional, List

from modules.browser_accessibility import (
    BrowserAccessibilityHandler,
    WebElement,
    BrowserTab,
    BrowserFrame,
    BrowserAccessibilityTree
)
from modules.application_detector import (
    ApplicationInfo,
    ApplicationType,
    BrowserType
)


class TestBrowserAccessibilityIntegration(unittest.TestCase):
    """Integration test cases for BrowserAccessibilityHandler."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.handler = BrowserAccessibilityHandler()
        
        # Create mock application info for different browsers
        self.chrome_app = ApplicationInfo(
            name="Google Chrome",
            bundle_id="com.google.Chrome",
            process_id=1234,
            app_type=ApplicationType.WEB_BROWSER,
            browser_type=BrowserType.CHROME
        )
        
        self.safari_app = ApplicationInfo(
            name="Safari",
            bundle_id="com.apple.Safari",
            process_id=5678,
            app_type=ApplicationType.WEB_BROWSER,
            browser_type=BrowserType.SAFARI
        )
        
        self.firefox_app = ApplicationInfo(
            name="Firefox",
            bundle_id="org.mozilla.firefox",
            process_id=9012,
            app_type=ApplicationType.WEB_BROWSER,
            browser_type=BrowserType.FIREFOX
        )
    
    def test_init(self):
        """Test BrowserAccessibilityHandler initialization."""
        handler = BrowserAccessibilityHandler()
        
        # Check that browser configs are initialized
        self.assertIsNotNone(handler.chrome_config)
        self.assertIsNotNone(handler.safari_config)
        self.assertIsNotNone(handler.firefox_config)
        
        # Check cache is empty
        self.assertEqual(len(handler._tree_cache), 0)
        
        # Check default cache TTL
        self.assertEqual(handler._cache_ttl, 30)
    
    def test_init_with_config(self):
        """Test initialization with custom config."""
        config = {'cache_ttl': 60, 'debug': True}
        handler = BrowserAccessibilityHandler(config)
        
        self.assertEqual(handler.config, config)
        self.assertEqual(handler._cache_ttl, 60)
    
    def test_get_browser_config_chrome(self):
        """Test getting Chrome-specific configuration."""
        config = self.handler.get_browser_config(BrowserType.CHROME)
        
        self.assertIn('web_content_roles', config)
        self.assertIn('navigation_roles', config)
        self.assertIn('frame_indicators', config)
        self.assertIn('tab_indicators', config)
        self.assertEqual(config['timeout_ms'], 3500)
        self.assertEqual(config['fuzzy_threshold'], 0.72)
        self.assertIn('AXButton', config['web_content_roles'])
        self.assertIn('AXGenericElement', config['web_content_roles'])
    
    def test_get_browser_config_safari(self):
        """Test getting Safari-specific configuration."""
        config = self.handler.get_browser_config(BrowserType.SAFARI)
        
        self.assertEqual(config['timeout_ms'], 2500)
        self.assertEqual(config['fuzzy_threshold'], 0.78)
        self.assertEqual(config['search_depth'], 12)
        self.assertIn('AXButton', config['web_content_roles'])
        self.assertNotIn('AXGenericElement', config['web_content_roles'])  # Safari difference
    
    def test_get_browser_config_firefox(self):
        """Test getting Firefox-specific configuration."""
        config = self.handler.get_browser_config(BrowserType.FIREFOX)
        
        self.assertEqual(config['timeout_ms'], 3000)
        self.assertEqual(config['fuzzy_threshold'], 0.75)
        self.assertIn('AXDocument', config['frame_indicators'])  # Firefox-specific
    
    def test_get_browser_config_unknown(self):
        """Test getting config for unknown browser (defaults to Chrome)."""
        config = self.handler.get_browser_config(BrowserType.UNKNOWN_BROWSER)
        
        # Should default to Chrome config
        self.assertEqual(config['timeout_ms'], 3500)
        self.assertEqual(config['fuzzy_threshold'], 0.72)
    
    @patch('modules.browser_accessibility.ACCESSIBILITY_FUNCTIONS_AVAILABLE', False)
    def test_extract_browser_tree_no_accessibility(self):
        """Test browser tree extraction when accessibility is not available."""
        result = self.handler.extract_browser_tree(self.chrome_app)
        
        self.assertIsNone(result)
    
    def test_extract_browser_tree_non_browser(self):
        """Test browser tree extraction for non-browser application."""
        non_browser_app = ApplicationInfo(
            name="TextEdit",
            bundle_id="com.apple.TextEdit",
            process_id=1111,
            app_type=ApplicationType.NATIVE_APP
        )
        
        result = self.handler.extract_browser_tree(non_browser_app)
        
        self.assertIsNone(result)
    
    @patch('modules.browser_accessibility.AXUIElementCreateApplication')
    def test_extract_browser_tree_no_app_element(self, mock_create_app):
        """Test browser tree extraction when app element creation fails."""
        mock_create_app.return_value = None
        
        result = self.handler.extract_browser_tree(self.chrome_app)
        
        self.assertIsNone(result)
        mock_create_app.assert_called_once_with(1234)
    
    @patch('modules.browser_accessibility.AXUIElementCreateApplication')
    @patch('modules.browser_accessibility.AXUIElementCopyAttributeValue')
    def test_extract_browser_tree_success(self, mock_copy_attr, mock_create_app):
        """Test successful browser tree extraction."""
        # Mock app element
        mock_app_element = Mock()
        mock_create_app.return_value = mock_app_element
        
        # Mock window
        mock_window = Mock()
        mock_copy_attr.return_value = (None, [mock_window])
        
        # Mock the extraction process
        with patch.object(self.handler, '_extract_browser_structure') as mock_extract:
            mock_tree = BrowserAccessibilityTree(
                browser_type=BrowserType.CHROME,
                app_name="Google Chrome",
                process_id=1234
            )
            mock_extract.return_value = mock_tree
            
            result = self.handler.extract_browser_tree(self.chrome_app)
            
            self.assertIsNotNone(result)
            self.assertEqual(result.browser_type, BrowserType.CHROME)
            self.assertEqual(result.app_name, "Google Chrome")
            self.assertEqual(result.process_id, 1234)
            
            # Check that result is cached
            cache_key = "Google Chrome_1234"
            self.assertIn(cache_key, self.handler._tree_cache)
    
    def test_extract_browser_tree_caching(self):
        """Test that browser tree extraction results are cached."""
        # Create a mock tree
        mock_tree = BrowserAccessibilityTree(
            browser_type=BrowserType.CHROME,
            app_name="Google Chrome",
            process_id=1234
        )
        
        # Add to cache
        cache_key = "Google Chrome_1234"
        self.handler._tree_cache[cache_key] = mock_tree
        
        # Should return cached result
        result = self.handler.extract_browser_tree(self.chrome_app)
        
        self.assertEqual(result, mock_tree)
    
    def test_extract_browser_tree_cache_expiry(self):
        """Test that expired cache entries are not used."""
        # Create an expired mock tree
        mock_tree = BrowserAccessibilityTree(
            browser_type=BrowserType.CHROME,
            app_name="Google Chrome",
            process_id=1234,
            timestamp=time.time() - 100  # 100 seconds ago (expired)
        )
        
        # Add to cache
        cache_key = "Google Chrome_1234"
        self.handler._tree_cache[cache_key] = mock_tree
        
        # Should not use expired cache
        with patch.object(self.handler, '_extract_browser_structure') as mock_extract:
            mock_extract.return_value = None
            result = self.handler.extract_browser_tree(self.chrome_app)
            
            # Should have attempted fresh extraction
            mock_extract.assert_called_once()
    
    def test_create_web_element_from_accessibility_element(self):
        """Test creating WebElement from accessibility element."""
        # Mock accessibility element
        mock_element = Mock()
        
        with patch.object(self.handler, '_get_attribute_value') as mock_get_attr:
            # Mock attribute values - use a simple mapping approach
            def mock_attr_side_effect(elem, attr):
                # Create mock constants for testing
                mock_constants = {
                    'role': 'AXButton',
                    'title': 'Click Me', 
                    'description': 'A clickable button',
                    'value': 'button_value',
                    'url': 'https://example.com'
                }
                
                # Map attribute to mock value based on string representation
                attr_str = str(attr).lower()
                if 'role' in attr_str:
                    return mock_constants['role']
                elif 'title' in attr_str:
                    return mock_constants['title']
                elif 'description' in attr_str:
                    return mock_constants['description']
                elif 'value' in attr_str:
                    return mock_constants['value']
                elif 'url' in attr_str:
                    return mock_constants['url']
                return ''
            
            mock_get_attr.side_effect = mock_attr_side_effect
            
            with patch.object(self.handler, '_get_element_coordinates') as mock_coords:
                mock_coords.return_value = [100, 200, 50, 30]
                
                result = self.handler._create_web_element_from_accessibility_element(
                    mock_element, "tab_1"
                )
                
                self.assertIsNotNone(result)
                self.assertEqual(result.role, 'AXButton')
                self.assertEqual(result.title, 'Click Me')
                self.assertEqual(result.description, 'A clickable button')
                self.assertEqual(result.value, 'button_value')
                self.assertEqual(result.url, 'https://example.com')
                self.assertEqual(result.tab_id, "tab_1")
                self.assertEqual(result.coordinates, [100, 200, 50, 30])
                self.assertEqual(result.center_point, [125, 215])  # Center calculation
    
    def test_find_elements_by_roles(self):
        """Test finding elements by accessibility roles."""
        # Mock container element
        mock_container = Mock()
        
        # Mock child elements
        mock_button = Mock()
        mock_link = Mock()
        mock_text = Mock()
        
        with patch.object(self.handler, '_get_attribute_value') as mock_get_attr:
            # Mock the recursive search
            def mock_attr_side_effect(element, attribute):
                attr_str = str(attribute).lower()
                if 'role' in attr_str:
                    if element == mock_button:
                        return 'AXButton'
                    elif element == mock_link:
                        return 'AXLink'
                    elif element == mock_text:
                        return 'AXStaticText'
                    else:
                        return 'AXGroup'
                elif 'children' in attr_str:
                    if element == mock_container:
                        return [mock_button, mock_link, mock_text]
                    else:
                        return []
                return None
            
            mock_get_attr.side_effect = mock_attr_side_effect
            
            # Search for buttons and links
            results = self.handler._find_elements_by_roles(
                mock_container, ['AXButton', 'AXLink'], max_depth=2
            )
            
            self.assertEqual(len(results), 2)
            self.assertIn(mock_button, results)
            self.assertIn(mock_link, results)
            self.assertNotIn(mock_text, results)
    
    def test_find_elements_in_browser(self):
        """Test finding elements in browser by text."""
        # Create mock browser tree
        mock_tree = BrowserAccessibilityTree(
            browser_type=BrowserType.CHROME,
            app_name="Google Chrome",
            process_id=1234
        )
        
        # Create mock elements
        button_element = WebElement(
            role='AXButton',
            title='Search Button',
            description='Click to search',
            value='',
            tab_id='tab_1'
        )
        
        link_element = WebElement(
            role='AXLink',
            title='Home Link',
            description='Go to homepage',
            value='',
            tab_id='tab_1'
        )
        
        text_element = WebElement(
            role='AXStaticText',
            title='Search Results',
            description='',
            value='Found 10 results',
            tab_id='tab_1'
        )
        
        # Add elements to mock tab
        mock_tab = BrowserTab(
            tab_id='tab_1',
            title='Test Page',
            url='https://example.com',
            is_active=True,
            elements=[button_element, link_element, text_element]
        )
        
        mock_tree.tabs = [mock_tab]
        
        # Mock the extract_browser_tree method
        with patch.object(self.handler, 'extract_browser_tree') as mock_extract:
            mock_extract.return_value = mock_tree
            
            # Search for "search"
            results = self.handler.find_elements_in_browser(
                self.chrome_app, "search"
            )
            
            self.assertEqual(len(results), 2)  # button and text elements
            self.assertIn(button_element, results)
            self.assertIn(text_element, results)
            self.assertNotIn(link_element, results)
    
    def test_find_elements_in_browser_with_role_filter(self):
        """Test finding elements in browser with role filtering."""
        # Create mock browser tree with elements
        mock_tree = BrowserAccessibilityTree(
            browser_type=BrowserType.CHROME,
            app_name="Google Chrome",
            process_id=1234
        )
        
        button_element = WebElement(
            role='AXButton',
            title='Search Button',
            description='',
            value='',
            tab_id='tab_1'
        )
        
        link_element = WebElement(
            role='AXLink',
            title='Search Link',
            description='',
            value='',
            tab_id='tab_1'
        )
        
        mock_tab = BrowserTab(
            tab_id='tab_1',
            title='Test Page',
            url='https://example.com',
            is_active=True,
            elements=[button_element, link_element]
        )
        
        mock_tree.tabs = [mock_tab]
        
        with patch.object(self.handler, 'extract_browser_tree') as mock_extract:
            mock_extract.return_value = mock_tree
            
            # Search for "search" but only buttons
            results = self.handler.find_elements_in_browser(
                self.chrome_app, "search", roles=['AXButton']
            )
            
            self.assertEqual(len(results), 1)
            self.assertIn(button_element, results)
            self.assertNotIn(link_element, results)
    
    def test_get_web_content_elements(self):
        """Test getting web content elements from browser."""
        # Create mock browser tree
        mock_tree = BrowserAccessibilityTree(
            browser_type=BrowserType.CHROME,
            app_name="Google Chrome",
            process_id=1234
        )
        
        # Create elements with different roles
        button_element = WebElement(role='AXButton', title='Button', description='', value='', tab_id='tab_1')
        toolbar_element = WebElement(role='AXToolbar', title='Toolbar', description='', value='', tab_id='tab_1')
        link_element = WebElement(role='AXLink', title='Link', description='', value='', tab_id='tab_1')
        
        mock_tab = BrowserTab(
            tab_id='tab_1',
            title='Test Page',
            url='https://example.com',
            is_active=True,
            elements=[button_element, toolbar_element, link_element]
        )
        
        mock_tree.tabs = [mock_tab]
        
        with patch.object(self.handler, 'extract_browser_tree') as mock_extract:
            mock_extract.return_value = mock_tree
            
            results = self.handler.get_web_content_elements(self.chrome_app)
            
            # Should only return web content elements (not toolbar)
            self.assertEqual(len(results), 2)
            self.assertIn(button_element, results)
            self.assertIn(link_element, results)
            self.assertNotIn(toolbar_element, results)
    
    def test_clear_cache(self):
        """Test cache clearing functionality."""
        # Add some items to cache
        mock_tree = BrowserAccessibilityTree(
            browser_type=BrowserType.CHROME,
            app_name="Chrome",
            process_id=1234
        )
        self.handler._tree_cache["test_key"] = mock_tree
        
        self.assertEqual(len(self.handler._tree_cache), 1)
        
        # Clear cache
        self.handler.clear_cache()
        
        self.assertEqual(len(self.handler._tree_cache), 0)
    
    def test_get_cache_stats(self):
        """Test cache statistics functionality."""
        # Add some items to cache
        mock_tree1 = BrowserAccessibilityTree(
            browser_type=BrowserType.CHROME,
            app_name="Chrome",
            process_id=1234
        )
        mock_tree2 = BrowserAccessibilityTree(
            browser_type=BrowserType.SAFARI,
            app_name="Safari",
            process_id=5678
        )
        
        self.handler._tree_cache["chrome_1234"] = mock_tree1
        self.handler._tree_cache["safari_5678"] = mock_tree2
        
        stats = self.handler.get_cache_stats()
        
        self.assertEqual(stats['cache_size'], 2)
        self.assertIn('chrome_1234', stats['cached_browsers'])
        self.assertIn('safari_5678', stats['cached_browsers'])
        self.assertEqual(stats['cache_ttl'], 30)
    
    def test_web_element_to_dict(self):
        """Test WebElement to_dict conversion."""
        element = WebElement(
            role='AXButton',
            title='Test Button',
            description='A test button',
            value='button_value',
            url='https://example.com',
            coordinates=[100, 200, 50, 30],
            center_point=[125, 215],
            enabled=True,
            frame_id='frame_1',
            tab_id='tab_1',
            element_id='elem_1',
            attributes={'custom': 'value'}
        )
        
        result = element.to_dict()
        
        self.assertEqual(result['role'], 'AXButton')
        self.assertEqual(result['title'], 'Test Button')
        self.assertEqual(result['description'], 'A test button')
        self.assertEqual(result['value'], 'button_value')
        self.assertEqual(result['url'], 'https://example.com')
        self.assertEqual(result['coordinates'], [100, 200, 50, 30])
        self.assertEqual(result['center_point'], [125, 215])
        self.assertTrue(result['enabled'])
        self.assertEqual(result['frame_id'], 'frame_1')
        self.assertEqual(result['tab_id'], 'tab_1')
        self.assertEqual(result['element_id'], 'elem_1')
        self.assertTrue(result['has_attributes'])
    
    def test_browser_tab_to_dict(self):
        """Test BrowserTab to_dict conversion."""
        tab = BrowserTab(
            tab_id='tab_1',
            title='Test Page',
            url='https://example.com',
            is_active=True
        )
        
        # Add some elements and frames
        tab.elements = [Mock(), Mock()]
        tab.frames = [Mock()]
        
        result = tab.to_dict()
        
        self.assertEqual(result['tab_id'], 'tab_1')
        self.assertEqual(result['title'], 'Test Page')
        self.assertEqual(result['url'], 'https://example.com')
        self.assertTrue(result['is_active'])
        self.assertEqual(result['element_count'], 2)
        self.assertEqual(result['frame_count'], 1)
    
    def test_browser_frame_to_dict(self):
        """Test BrowserFrame to_dict conversion."""
        frame = BrowserFrame(
            frame_id='frame_1',
            url='https://frame.example.com',
            title='Frame Title',
            parent_frame_id='parent_frame'
        )
        
        # Add some elements
        frame.elements = [Mock(), Mock(), Mock()]
        
        result = frame.to_dict()
        
        self.assertEqual(result['frame_id'], 'frame_1')
        self.assertEqual(result['url'], 'https://frame.example.com')
        self.assertEqual(result['title'], 'Frame Title')
        self.assertEqual(result['parent_frame_id'], 'parent_frame')
        self.assertEqual(result['element_count'], 3)
    
    def test_browser_accessibility_tree_get_active_tab(self):
        """Test getting active tab from browser tree."""
        tree = BrowserAccessibilityTree(
            browser_type=BrowserType.CHROME,
            app_name="Chrome",
            process_id=1234
        )
        
        # Create tabs
        tab1 = BrowserTab('tab_1', 'Tab 1', 'https://example1.com', False)
        tab2 = BrowserTab('tab_2', 'Tab 2', 'https://example2.com', True)
        tab3 = BrowserTab('tab_3', 'Tab 3', 'https://example3.com', False)
        
        tree.tabs = [tab1, tab2, tab3]
        tree.active_tab_id = 'tab_2'
        
        active_tab = tree.get_active_tab()
        
        self.assertEqual(active_tab, tab2)
        self.assertEqual(active_tab.tab_id, 'tab_2')
    
    def test_browser_accessibility_tree_get_active_tab_fallback(self):
        """Test getting active tab fallback when active_tab_id is not set."""
        tree = BrowserAccessibilityTree(
            browser_type=BrowserType.CHROME,
            app_name="Chrome",
            process_id=1234
        )
        
        # Create tabs with one marked as active
        tab1 = BrowserTab('tab_1', 'Tab 1', 'https://example1.com', False)
        tab2 = BrowserTab('tab_2', 'Tab 2', 'https://example2.com', True)
        
        tree.tabs = [tab1, tab2]
        # Don't set active_tab_id
        
        active_tab = tree.get_active_tab()
        
        self.assertEqual(active_tab, tab2)
    
    def test_browser_accessibility_tree_get_all_elements(self):
        """Test getting all elements from browser tree."""
        tree = BrowserAccessibilityTree(
            browser_type=BrowserType.CHROME,
            app_name="Chrome",
            process_id=1234
        )
        
        # Create elements
        elem1 = WebElement('AXButton', 'Button 1', '', '', tab_id='tab_1')
        elem2 = WebElement('AXLink', 'Link 1', '', '', tab_id='tab_1')
        elem3 = WebElement('AXButton', 'Button 2', '', '', tab_id='tab_2')
        elem4 = WebElement('AXStaticText', 'Text 1', '', '', frame_id='frame_1')
        
        # Create tab with elements
        tab1 = BrowserTab('tab_1', 'Tab 1', 'https://example1.com', True)
        tab1.elements = [elem1, elem2]
        
        tab2 = BrowserTab('tab_2', 'Tab 2', 'https://example2.com', False)
        tab2.elements = [elem3]
        
        # Create frame with elements
        frame1 = BrowserFrame('frame_1', 'https://frame.com', 'Frame 1')
        frame1.elements = [elem4]
        tab1.frames = [frame1]
        
        tree.tabs = [tab1, tab2]
        
        all_elements = tree.get_all_elements()
        
        self.assertEqual(len(all_elements), 4)
        self.assertIn(elem1, all_elements)
        self.assertIn(elem2, all_elements)
        self.assertIn(elem3, all_elements)
        self.assertIn(elem4, all_elements)
    
    def test_browser_accessibility_tree_to_dict(self):
        """Test BrowserAccessibilityTree to_dict conversion."""
        tree = BrowserAccessibilityTree(
            browser_type=BrowserType.CHROME,
            app_name="Chrome",
            process_id=1234,
            active_tab_id='tab_1',
            timestamp=1234567890.0
        )
        
        # Add tabs with elements
        tab1 = BrowserTab('tab_1', 'Tab 1', 'https://example.com', True)
        tab1.elements = [Mock(), Mock()]
        tree.tabs = [tab1]
        
        result = tree.to_dict()
        
        self.assertEqual(result['browser_type'], 'chrome')
        self.assertEqual(result['app_name'], 'Chrome')
        self.assertEqual(result['process_id'], 1234)
        self.assertEqual(result['tab_count'], 1)
        self.assertEqual(result['active_tab_id'], 'tab_1')
        self.assertEqual(result['total_elements'], 2)
        self.assertEqual(result['timestamp'], 1234567890.0)


if __name__ == '__main__':
    unittest.main()