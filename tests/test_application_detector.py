"""
Unit tests for ApplicationDetector module.

Tests application type detection, strategy selection, and search parameter adaptation.
"""

import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
import time
from typing import Dict, Any, Optional

from modules.application_detector import (
    ApplicationDetector,
    ApplicationType,
    BrowserType,
    ApplicationInfo,
    DetectionStrategy,
    SearchParameters
)


class TestApplicationDetector(unittest.TestCase):
    """Test cases for ApplicationDetector class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.detector = ApplicationDetector()
    
    def test_init(self):
        """Test ApplicationDetector initialization."""
        detector = ApplicationDetector()
        
        # Check that mappings are initialized
        self.assertIn(ApplicationType.WEB_BROWSER, detector.bundle_patterns)
        self.assertIn(ApplicationType.SYSTEM_APP, detector.bundle_patterns)
        self.assertIn(ApplicationType.ELECTRON_APP, detector.bundle_patterns)
        
        # Check that strategies are initialized
        self.assertIsNotNone(detector.browser_strategy)
        self.assertIsNotNone(detector.native_strategy)
        self.assertIsNotNone(detector.system_strategy)
        
        # Check caches are empty
        self.assertEqual(len(detector._app_cache), 0)
        self.assertEqual(len(detector._strategy_cache), 0)
    
    def test_init_with_config(self):
        """Test ApplicationDetector initialization with config."""
        config = {'debug': True, 'cache_size': 100}
        detector = ApplicationDetector(config)
        
        self.assertEqual(detector.config, config)
    
    @patch('modules.application_detector.NSWorkspace')
    def test_detect_application_type_chrome(self, mock_workspace):
        """Test detection of Chrome browser."""
        # Mock running application
        mock_app = Mock()
        mock_app.localizedName.return_value = "Google Chrome"
        mock_app.bundleIdentifier.return_value = "com.google.Chrome"
        mock_app.processIdentifier.return_value = 1234
        
        mock_workspace_instance = Mock()
        mock_workspace_instance.runningApplications.return_value = [mock_app]
        mock_workspace.sharedWorkspace.return_value = mock_workspace_instance
        
        # Test detection
        app_info = self.detector.detect_application_type("Google Chrome")
        
        self.assertEqual(app_info.name, "Google Chrome")
        self.assertEqual(app_info.bundle_id, "com.google.Chrome")
        self.assertEqual(app_info.process_id, 1234)
        self.assertEqual(app_info.app_type, ApplicationType.WEB_BROWSER)
        self.assertEqual(app_info.browser_type, BrowserType.CHROME)
        self.assertGreater(app_info.detection_confidence, 0.9)
    
    @patch('modules.application_detector.NSWorkspace')
    def test_detect_application_type_safari(self, mock_workspace):
        """Test detection of Safari browser."""
        mock_app = Mock()
        mock_app.localizedName.return_value = "Safari"
        mock_app.bundleIdentifier.return_value = "com.apple.Safari"
        mock_app.processIdentifier.return_value = 5678
        
        mock_workspace_instance = Mock()
        mock_workspace_instance.runningApplications.return_value = [mock_app]
        mock_workspace.sharedWorkspace.return_value = mock_workspace_instance
        
        app_info = self.detector.detect_application_type("Safari")
        
        self.assertEqual(app_info.app_type, ApplicationType.WEB_BROWSER)
        self.assertEqual(app_info.browser_type, BrowserType.SAFARI)
        self.assertGreater(app_info.detection_confidence, 0.9)
    
    @patch('modules.application_detector.NSWorkspace')
    def test_detect_application_type_system_app(self, mock_workspace):
        """Test detection of system application."""
        mock_app = Mock()
        mock_app.localizedName.return_value = "Finder"
        mock_app.bundleIdentifier.return_value = "com.apple.finder"
        mock_app.processIdentifier.return_value = 100
        
        mock_workspace_instance = Mock()
        mock_workspace_instance.runningApplications.return_value = [mock_app]
        mock_workspace.sharedWorkspace.return_value = mock_workspace_instance
        
        app_info = self.detector.detect_application_type("Finder")
        
        self.assertEqual(app_info.app_type, ApplicationType.SYSTEM_APP)
        self.assertIsNone(app_info.browser_type)
        self.assertGreater(app_info.detection_confidence, 0.9)
    
    @patch('modules.application_detector.NSWorkspace')
    def test_detect_application_type_electron_app(self, mock_workspace):
        """Test detection of Electron application."""
        mock_app = Mock()
        mock_app.localizedName.return_value = "Visual Studio Code"
        mock_app.bundleIdentifier.return_value = "com.microsoft.VSCode"
        mock_app.processIdentifier.return_value = 2000
        
        mock_workspace_instance = Mock()
        mock_workspace_instance.runningApplications.return_value = [mock_app]
        mock_workspace.sharedWorkspace.return_value = mock_workspace_instance
        
        app_info = self.detector.detect_application_type("Visual Studio Code")
        
        self.assertEqual(app_info.app_type, ApplicationType.ELECTRON_APP)
        self.assertIsNone(app_info.browser_type)
        self.assertGreater(app_info.detection_confidence, 0.85)
    
    @patch('modules.application_detector.NSWorkspace')
    def test_detect_application_type_java_app(self, mock_workspace):
        """Test detection of Java application."""
        mock_app = Mock()
        mock_app.localizedName.return_value = "IntelliJ IDEA"
        mock_app.bundleIdentifier.return_value = "com.jetbrains.intellij"
        mock_app.processIdentifier.return_value = 3000
        
        mock_workspace_instance = Mock()
        mock_workspace_instance.runningApplications.return_value = [mock_app]
        mock_workspace.sharedWorkspace.return_value = mock_workspace_instance
        
        app_info = self.detector.detect_application_type("IntelliJ IDEA")
        
        self.assertEqual(app_info.app_type, ApplicationType.JAVA_APP)
        self.assertIsNone(app_info.browser_type)
        self.assertGreater(app_info.detection_confidence, 0.85)
    
    @patch('modules.application_detector.NSWorkspace')
    def test_detect_application_type_unknown_app(self, mock_workspace):
        """Test detection of unknown application."""
        mock_app = Mock()
        mock_app.localizedName.return_value = "Unknown App"
        mock_app.bundleIdentifier.return_value = "com.unknown.app"
        mock_app.processIdentifier.return_value = 4000
        
        mock_workspace_instance = Mock()
        mock_workspace_instance.runningApplications.return_value = [mock_app]
        mock_workspace.sharedWorkspace.return_value = mock_workspace_instance
        
        app_info = self.detector.detect_application_type("Unknown App")
        
        self.assertEqual(app_info.app_type, ApplicationType.NATIVE_APP)  # Default to native
        self.assertIsNone(app_info.browser_type)
        self.assertLess(app_info.detection_confidence, 0.8)
    
    @patch('modules.application_detector.NSWorkspace')
    def test_detect_application_type_not_running(self, mock_workspace):
        """Test detection when application is not running."""
        mock_workspace_instance = Mock()
        mock_workspace_instance.runningApplications.return_value = []
        mock_workspace.sharedWorkspace.return_value = mock_workspace_instance
        
        app_info = self.detector.detect_application_type("Non-existent App")
        
        self.assertEqual(app_info.name, "Non-existent App")
        self.assertEqual(app_info.bundle_id, "unknown")
        self.assertEqual(app_info.process_id, 0)
        self.assertEqual(app_info.app_type, ApplicationType.UNKNOWN)
        self.assertLess(app_info.detection_confidence, 0.6)
    
    def test_detect_application_type_caching(self):
        """Test that application detection results are cached."""
        # Create a mock app info
        app_info = ApplicationInfo(
            name="Test App",
            bundle_id="com.test.app",
            process_id=1000,
            app_type=ApplicationType.NATIVE_APP,
            detection_confidence=0.8
        )
        
        # Add to cache
        self.detector._app_cache["Test App"] = app_info
        
        # Should return cached result without calling system APIs
        result = self.detector.detect_application_type("Test App")
        
        self.assertEqual(result, app_info)
        self.assertEqual(result.name, "Test App")
        self.assertEqual(result.app_type, ApplicationType.NATIVE_APP)
    
    def test_classify_application_browser_patterns(self):
        """Test application classification based on bundle patterns."""
        # Test Chrome
        app_info = ApplicationInfo("Chrome", "com.google.Chrome", 1000, ApplicationType.UNKNOWN)
        app_type, browser_type, confidence = self.detector._classify_application(app_info)
        
        self.assertEqual(app_type, ApplicationType.WEB_BROWSER)
        self.assertEqual(browser_type, BrowserType.CHROME)
        self.assertGreater(confidence, 0.9)
        
        # Test Safari
        app_info = ApplicationInfo("Safari", "com.apple.Safari", 1001, ApplicationType.UNKNOWN)
        app_type, browser_type, confidence = self.detector._classify_application(app_info)
        
        self.assertEqual(app_type, ApplicationType.WEB_BROWSER)
        self.assertEqual(browser_type, BrowserType.SAFARI)
        self.assertGreater(confidence, 0.9)
    
    def test_classify_application_name_patterns(self):
        """Test application classification based on name patterns."""
        # Test browser detection by name
        app_info = ApplicationInfo("Chrome Helper", "unknown", 1000, ApplicationType.UNKNOWN)
        app_type, browser_type, confidence = self.detector._classify_application(app_info)
        
        self.assertEqual(app_type, ApplicationType.WEB_BROWSER)
        self.assertEqual(browser_type, BrowserType.CHROME)
        self.assertEqual(confidence, 0.6)  # Process pattern matching confidence
    
    def test_get_detection_strategy_browser(self):
        """Test getting detection strategy for browser."""
        app_info = ApplicationInfo(
            "Chrome", "com.google.Chrome", 1000, 
            ApplicationType.WEB_BROWSER, BrowserType.CHROME
        )
        
        strategy = self.detector.get_detection_strategy(app_info)
        
        self.assertEqual(strategy.app_type, ApplicationType.WEB_BROWSER)
        self.assertIn('AXButton', strategy.preferred_roles)
        self.assertIn('AXLink', strategy.preferred_roles)
        self.assertTrue(strategy.handle_frames)
        self.assertTrue(strategy.handle_tabs)
        self.assertTrue(strategy.web_content_detection)
        self.assertGreater(strategy.timeout_ms, 2000)  # Browsers need more time
    
    def test_get_detection_strategy_system_app(self):
        """Test getting detection strategy for system app."""
        app_info = ApplicationInfo(
            "Finder", "com.apple.finder", 100, 
            ApplicationType.SYSTEM_APP
        )
        
        strategy = self.detector.get_detection_strategy(app_info)
        
        self.assertEqual(strategy.app_type, ApplicationType.SYSTEM_APP)
        self.assertIn('AXButton', strategy.preferred_roles)
        self.assertIn('AXMenuItem', strategy.preferred_roles)
        self.assertFalse(strategy.handle_frames)
        self.assertFalse(strategy.handle_tabs)
        self.assertLess(strategy.timeout_ms, 2000)  # System apps should be faster
        self.assertGreater(strategy.fuzzy_threshold, 0.8)  # Higher threshold for system apps
    
    def test_get_detection_strategy_electron_app(self):
        """Test getting detection strategy for Electron app."""
        app_info = ApplicationInfo(
            "VS Code", "com.microsoft.VSCode", 2000, 
            ApplicationType.ELECTRON_APP
        )
        
        strategy = self.detector.get_detection_strategy(app_info)
        
        self.assertEqual(strategy.app_type, ApplicationType.ELECTRON_APP)
        self.assertTrue(strategy.web_content_detection)  # Electron uses web content
        self.assertTrue(strategy.parallel_search)
        self.assertGreater(strategy.max_depth, 10)  # Electron can have deep hierarchies
    
    def test_get_detection_strategy_caching(self):
        """Test that detection strategies are cached."""
        app_info = ApplicationInfo(
            "Test App", "com.test.app", 1000, 
            ApplicationType.NATIVE_APP
        )
        
        # First call should create and cache strategy
        strategy1 = self.detector.get_detection_strategy(app_info)
        
        # Second call should return cached strategy
        strategy2 = self.detector.get_detection_strategy(app_info)
        
        self.assertIs(strategy1, strategy2)  # Should be the same object
    
    def test_adapt_search_parameters_click_command(self):
        """Test search parameter adaptation for click commands."""
        app_info = ApplicationInfo(
            "Test App", "com.test.app", 1000, 
            ApplicationType.NATIVE_APP
        )
        
        # Test button click
        params = self.detector.adapt_search_parameters(app_info, "Click on Save button")
        
        self.assertIn('AXButton', params.roles)
        self.assertEqual(params.roles[0], 'AXButton')  # Should be first priority
        
        # Test link click
        params = self.detector.adapt_search_parameters(app_info, "Click on this link")
        
        self.assertIn('AXLink', params.roles)
        self.assertEqual(params.roles[0], 'AXLink')  # Should be first priority
    
    def test_adapt_search_parameters_type_command(self):
        """Test search parameter adaptation for type commands."""
        app_info = ApplicationInfo(
            "Test App", "com.test.app", 1000, 
            ApplicationType.NATIVE_APP
        )
        
        params = self.detector.adapt_search_parameters(app_info, "Type hello in the text field")
        
        self.assertIn('AXTextField', params.roles)
        self.assertIn('AXTextArea', params.roles)
        # Text fields should be prioritized
        self.assertTrue(params.roles[0] in ['AXTextField', 'AXTextArea'])
    
    def test_adapt_search_parameters_browser_web_content(self):
        """Test search parameter adaptation for browser web content."""
        app_info = ApplicationInfo(
            "Chrome", "com.google.Chrome", 1000, 
            ApplicationType.WEB_BROWSER, BrowserType.CHROME
        )
        
        params = self.detector.adapt_search_parameters(app_info, "Click on Google search button")
        
        self.assertTrue(params.search_frames)
        self.assertTrue(params.web_content_only)  # Should focus on web content
    
    def test_adapt_search_parameters_select_command(self):
        """Test search parameter adaptation for select commands."""
        app_info = ApplicationInfo(
            "Test App", "com.test.app", 1000, 
            ApplicationType.NATIVE_APP
        )
        
        params = self.detector.adapt_search_parameters(app_info, "Select option from dropdown")
        
        self.assertIn('AXPopUpButton', params.roles)
        self.assertIn('AXComboBox', params.roles)
        self.assertIn('AXList', params.roles)
    
    def test_customize_strategy_mail_app(self):
        """Test strategy customization for Mail app."""
        base_strategy = self.detector.native_strategy
        app_info = ApplicationInfo(
            "Mail", "com.apple.mail", 1000, 
            ApplicationType.NATIVE_APP
        )
        
        customized = self.detector._customize_strategy(base_strategy, app_info)
        
        self.assertIn('AXOutline', customized.preferred_roles)
        self.assertIn('AXRoleDescription', customized.search_attributes)
    
    def test_customize_strategy_finder_app(self):
        """Test strategy customization for Finder app."""
        base_strategy = self.detector.system_strategy
        app_info = ApplicationInfo(
            "Finder", "com.apple.finder", 100, 
            ApplicationType.SYSTEM_APP
        )
        
        customized = self.detector._customize_strategy(base_strategy, app_info)
        
        self.assertIn('AXOutline', customized.preferred_roles)
        self.assertIn('AXTable', customized.preferred_roles)
        self.assertIn('AXColumn', customized.preferred_roles)
        self.assertGreater(customized.max_depth, base_strategy.max_depth)
    
    def test_customize_strategy_terminal_app(self):
        """Test strategy customization for Terminal app."""
        base_strategy = self.detector.system_strategy
        app_info = ApplicationInfo(
            "Terminal", "com.apple.terminal", 200, 
            ApplicationType.SYSTEM_APP
        )
        
        customized = self.detector._customize_strategy(base_strategy, app_info)
        
        self.assertEqual(customized.preferred_roles[0], 'AXStaticText')
        self.assertIn('AXTextField', customized.preferred_roles)
        self.assertGreater(customized.fuzzy_threshold, 0.85)  # Terminal should be exact
    
    def test_clear_cache(self):
        """Test cache clearing functionality."""
        # Add some items to cache
        self.detector._app_cache["test"] = ApplicationInfo("test", "test", 0, ApplicationType.UNKNOWN)
        self.detector._strategy_cache["test"] = self.detector.default_strategy
        
        self.assertEqual(len(self.detector._app_cache), 1)
        self.assertEqual(len(self.detector._strategy_cache), 1)
        
        # Clear cache
        self.detector.clear_cache()
        
        self.assertEqual(len(self.detector._app_cache), 0)
        self.assertEqual(len(self.detector._strategy_cache), 0)
    
    def test_get_cache_stats(self):
        """Test cache statistics functionality."""
        # Add some items to cache
        self.detector._app_cache["app1"] = ApplicationInfo("app1", "test1", 0, ApplicationType.UNKNOWN)
        self.detector._app_cache["app2"] = ApplicationInfo("app2", "test2", 0, ApplicationType.UNKNOWN)
        self.detector._strategy_cache["strategy1"] = self.detector.default_strategy
        
        stats = self.detector.get_cache_stats()
        
        self.assertEqual(stats['app_cache_size'], 2)
        self.assertEqual(stats['strategy_cache_size'], 1)
        self.assertIn('app1', stats['cached_applications'])
        self.assertIn('app2', stats['cached_applications'])
    
    def test_detect_browser_type_from_name(self):
        """Test browser type detection from application name."""
        self.assertEqual(
            self.detector._detect_browser_type_from_name("Google Chrome"),
            BrowserType.CHROME
        )
        self.assertEqual(
            self.detector._detect_browser_type_from_name("Safari"),
            BrowserType.SAFARI
        )
        self.assertEqual(
            self.detector._detect_browser_type_from_name("Firefox"),
            BrowserType.FIREFOX
        )
        self.assertEqual(
            self.detector._detect_browser_type_from_name("Microsoft Edge"),
            BrowserType.EDGE
        )
        self.assertEqual(
            self.detector._detect_browser_type_from_name("Unknown Browser"),
            BrowserType.UNKNOWN_BROWSER
        )
    
    @patch('modules.application_detector.APPKIT_AVAILABLE', False)
    def test_detect_application_type_no_appkit(self):
        """Test application detection when AppKit is not available."""
        detector = ApplicationDetector()
        app_info = detector.detect_application_type("Test App")
        
        self.assertEqual(app_info.name, "Test App")
        self.assertEqual(app_info.bundle_id, "unknown")
        self.assertEqual(app_info.app_type, ApplicationType.UNKNOWN)
        self.assertLess(app_info.detection_confidence, 0.6)
    
    def test_application_info_to_dict(self):
        """Test ApplicationInfo to_dict conversion."""
        app_info = ApplicationInfo(
            name="Test App",
            bundle_id="com.test.app",
            process_id=1000,
            app_type=ApplicationType.WEB_BROWSER,
            browser_type=BrowserType.CHROME,
            version="1.0.0",
            accessibility_enabled=True,
            detection_confidence=0.95
        )
        
        result = app_info.to_dict()
        
        self.assertEqual(result['name'], "Test App")
        self.assertEqual(result['bundle_id'], "com.test.app")
        self.assertEqual(result['process_id'], 1000)
        self.assertEqual(result['app_type'], "web_browser")
        self.assertEqual(result['browser_type'], "chrome")
        self.assertEqual(result['version'], "1.0.0")
        self.assertTrue(result['accessibility_enabled'])
        self.assertEqual(result['detection_confidence'], 0.95)
    
    def test_detection_strategy_to_dict(self):
        """Test DetectionStrategy to_dict conversion."""
        strategy = DetectionStrategy(
            app_type=ApplicationType.WEB_BROWSER,
            browser_type=BrowserType.CHROME,
            preferred_roles=['AXButton', 'AXLink'],
            fallback_roles=['AXGroup'],
            search_attributes=['AXTitle', 'AXDescription'],
            timeout_ms=3000,
            max_depth=15,
            fuzzy_threshold=0.75,
            handle_frames=True,
            handle_tabs=True,
            web_content_detection=True,
            parallel_search=True
        )
        
        result = strategy.to_dict()
        
        self.assertEqual(result['app_type'], "web_browser")
        self.assertEqual(result['browser_type'], "chrome")
        self.assertEqual(result['preferred_roles'], ['AXButton', 'AXLink'])
        self.assertEqual(result['fallback_roles'], ['AXGroup'])
        self.assertEqual(result['timeout_ms'], 3000)
        self.assertTrue(result['handle_frames'])
        self.assertTrue(result['web_content_detection'])
    
    def test_search_parameters_to_dict(self):
        """Test SearchParameters to_dict conversion."""
        params = SearchParameters(
            roles=['AXButton', 'AXLink'],
            attributes=['AXTitle', 'AXDescription'],
            timeout_ms=2000,
            max_depth=10,
            fuzzy_threshold=0.8,
            parallel_search=True,
            early_termination=True,
            search_frames=True,
            search_tabs=False,
            web_content_only=True
        )
        
        result = params.to_dict()
        
        self.assertEqual(result['roles'], ['AXButton', 'AXLink'])
        self.assertEqual(result['attributes'], ['AXTitle', 'AXDescription'])
        self.assertEqual(result['timeout_ms'], 2000)
        self.assertEqual(result['max_depth'], 10)
        self.assertEqual(result['fuzzy_threshold'], 0.8)
        self.assertTrue(result['parallel_search'])
        self.assertTrue(result['early_termination'])
        self.assertTrue(result['search_frames'])
        self.assertFalse(result['search_tabs'])
        self.assertTrue(result['web_content_only'])


if __name__ == '__main__':
    unittest.main()