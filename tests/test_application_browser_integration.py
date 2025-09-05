"""
Integration test for ApplicationDetector and BrowserAccessibilityHandler working together.
"""

import pytest
import unittest
from unittest.mock import Mock, patch

from modules.application_detector import (
    ApplicationDetector,
    ApplicationInfo,
    ApplicationType,
    BrowserType
)
from modules.browser_accessibility import BrowserAccessibilityHandler


class TestApplicationBrowserIntegration(unittest.TestCase):
    """Test integration between ApplicationDetector and BrowserAccessibilityHandler."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.app_detector = ApplicationDetector()
        self.browser_handler = BrowserAccessibilityHandler()
    
    @patch('modules.application_detector.NSWorkspace')
    def test_detect_and_handle_chrome(self, mock_workspace):
        """Test detecting Chrome and getting browser-specific handling."""
        # Mock Chrome application
        mock_app = Mock()
        mock_app.localizedName.return_value = "Google Chrome"
        mock_app.bundleIdentifier.return_value = "com.google.Chrome"
        mock_app.processIdentifier.return_value = 1234
        
        mock_workspace_instance = Mock()
        mock_workspace_instance.runningApplications.return_value = [mock_app]
        mock_workspace.sharedWorkspace.return_value = mock_workspace_instance
        
        # Detect application
        app_info = self.app_detector.detect_application_type("Google Chrome")
        
        # Verify detection
        self.assertEqual(app_info.app_type, ApplicationType.WEB_BROWSER)
        self.assertEqual(app_info.browser_type, BrowserType.CHROME)
        
        # Get browser configuration
        browser_config = self.browser_handler.get_browser_config(app_info.browser_type)
        
        # Verify Chrome-specific configuration
        self.assertEqual(browser_config['timeout_ms'], 3500)
        self.assertEqual(browser_config['fuzzy_threshold'], 0.72)
        self.assertIn('AXGenericElement', browser_config['web_content_roles'])
        
        # Get detection strategy
        strategy = self.app_detector.get_detection_strategy(app_info)
        
        # Verify strategy is optimized for Chrome
        self.assertEqual(strategy.app_type, ApplicationType.WEB_BROWSER)
        self.assertTrue(strategy.handle_frames)
        self.assertTrue(strategy.handle_tabs)
        self.assertTrue(strategy.web_content_detection)
    
    @patch('modules.application_detector.NSWorkspace')
    def test_detect_and_handle_safari(self, mock_workspace):
        """Test detecting Safari and getting browser-specific handling."""
        # Mock Safari application
        mock_app = Mock()
        mock_app.localizedName.return_value = "Safari"
        mock_app.bundleIdentifier.return_value = "com.apple.Safari"
        mock_app.processIdentifier.return_value = 5678
        
        mock_workspace_instance = Mock()
        mock_workspace_instance.runningApplications.return_value = [mock_app]
        mock_workspace.sharedWorkspace.return_value = mock_workspace_instance
        
        # Detect application
        app_info = self.app_detector.detect_application_type("Safari")
        
        # Verify detection
        self.assertEqual(app_info.app_type, ApplicationType.WEB_BROWSER)
        self.assertEqual(app_info.browser_type, BrowserType.SAFARI)
        
        # Get browser configuration
        browser_config = self.browser_handler.get_browser_config(app_info.browser_type)
        
        # Verify Safari-specific configuration
        self.assertEqual(browser_config['timeout_ms'], 2500)
        self.assertEqual(browser_config['fuzzy_threshold'], 0.78)
        self.assertNotIn('AXGenericElement', browser_config['web_content_roles'])  # Safari difference
    
    def test_adapt_search_for_browser_command(self):
        """Test adapting search parameters for browser-specific commands."""
        # Create Chrome app info
        chrome_app = ApplicationInfo(
            name="Google Chrome",
            bundle_id="com.google.Chrome",
            process_id=1234,
            app_type=ApplicationType.WEB_BROWSER,
            browser_type=BrowserType.CHROME
        )
        
        # Adapt search parameters for a web search command
        search_params = self.app_detector.adapt_search_parameters(
            chrome_app, "Click on Google search button"
        )
        
        # Verify parameters are optimized for web content
        self.assertTrue(search_params.search_frames)
        self.assertTrue(search_params.web_content_only)
        self.assertIn('AXButton', search_params.roles)
        
        # Verify timeout is appropriate for Chrome
        self.assertGreaterEqual(search_params.timeout_ms, 3000)
    
    def test_non_browser_app_handling(self):
        """Test that non-browser apps don't get browser-specific handling."""
        # Create system app info
        system_app = ApplicationInfo(
            name="Finder",
            bundle_id="com.apple.finder",
            process_id=100,
            app_type=ApplicationType.SYSTEM_APP
        )
        
        # Try to extract browser tree (should return None)
        browser_tree = self.browser_handler.extract_browser_tree(system_app)
        self.assertIsNone(browser_tree)
        
        # Get detection strategy (should be system app strategy)
        strategy = self.app_detector.get_detection_strategy(system_app)
        self.assertEqual(strategy.app_type, ApplicationType.SYSTEM_APP)
        self.assertFalse(strategy.handle_frames)
        self.assertFalse(strategy.handle_tabs)
        self.assertFalse(strategy.web_content_detection)
    
    def test_unknown_browser_fallback(self):
        """Test handling of unknown browser types."""
        # Create unknown browser app info
        unknown_browser = ApplicationInfo(
            name="Unknown Browser",
            bundle_id="com.unknown.browser",
            process_id=9999,
            app_type=ApplicationType.WEB_BROWSER,
            browser_type=BrowserType.UNKNOWN_BROWSER
        )
        
        # Get browser configuration (should fallback to Chrome config)
        browser_config = self.browser_handler.get_browser_config(unknown_browser.browser_type)
        
        # Should use Chrome config as fallback
        self.assertEqual(browser_config['timeout_ms'], 3500)
        self.assertEqual(browser_config['fuzzy_threshold'], 0.72)
    
    def test_caching_integration(self):
        """Test that both modules cache their results appropriately."""
        # Create app info
        app_info = ApplicationInfo(
            name="Test Chrome",
            bundle_id="com.google.Chrome",
            process_id=1111,
            app_type=ApplicationType.WEB_BROWSER,
            browser_type=BrowserType.CHROME
        )
        
        # Add to app detector cache
        self.app_detector._app_cache["Test Chrome"] = app_info
        
        # Verify cached retrieval
        cached_info = self.app_detector.detect_application_type("Test Chrome")
        self.assertEqual(cached_info, app_info)
        
        # Get strategy (should be cached after first call)
        strategy1 = self.app_detector.get_detection_strategy(app_info)
        strategy2 = self.app_detector.get_detection_strategy(app_info)
        self.assertIs(strategy1, strategy2)  # Same object reference
        
        # Check cache stats
        app_stats = self.app_detector.get_cache_stats()
        browser_stats = self.browser_handler.get_cache_stats()
        
        self.assertGreater(app_stats['app_cache_size'], 0)
        self.assertGreater(app_stats['strategy_cache_size'], 0)
        self.assertEqual(browser_stats['cache_size'], 0)  # No browser trees cached yet
    
    def test_clear_all_caches(self):
        """Test clearing caches in both modules."""
        # Add some test data to caches
        app_info = ApplicationInfo("Test", "test", 1, ApplicationType.UNKNOWN)
        self.app_detector._app_cache["test"] = app_info
        self.app_detector._strategy_cache["test"] = self.app_detector.default_strategy
        
        # Verify caches have data
        self.assertGreater(len(self.app_detector._app_cache), 0)
        self.assertGreater(len(self.app_detector._strategy_cache), 0)
        
        # Clear caches
        self.app_detector.clear_cache()
        self.browser_handler.clear_cache()
        
        # Verify caches are empty
        self.assertEqual(len(self.app_detector._app_cache), 0)
        self.assertEqual(len(self.app_detector._strategy_cache), 0)
        self.assertEqual(len(self.browser_handler._tree_cache), 0)


if __name__ == '__main__':
    unittest.main()