#!/usr/bin/env python3
"""
Test script for Task 3: Browser Content Extraction

This script tests the _extract_browser_content() method implementation
to verify it meets the requirements:
- Uses BrowserAccessibilityHandler
- Includes browser type detection
- Validates content is substantial (>50 characters)
- Implements timeout handling (2 second limit)
- Provides error recovery for extraction failures
"""

import sys
import os
import time
import logging
from unittest.mock import Mock, patch, MagicMock

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_browser_content_extraction():
    """Test the browser content extraction implementation."""
    
    print("=" * 60)
    print("Testing Task 3: Browser Content Extraction")
    print("=" * 60)
    
    try:
        # Import the handler
        from handlers.question_answering_handler import QuestionAnsweringHandler
        from modules.application_detector import ApplicationInfo, ApplicationType, BrowserType
        
        # Create a mock orchestrator
        mock_orchestrator = Mock()
        
        # Create handler instance
        handler = QuestionAnsweringHandler(mock_orchestrator)
        
        print("✓ QuestionAnsweringHandler created successfully")
        
        # Test 1: Test with no active application
        print("\n1. Testing with no active application...")
        with patch.object(handler, '_detect_active_application', return_value=None):
            result = handler._extract_browser_content()
            assert result is None, "Should return None when no application detected"
            print("✓ Correctly handles no active application")
        
        # Test 2: Test with non-browser application
        print("\n2. Testing with non-browser application...")
        non_browser_app = ApplicationInfo(
            name="TextEdit",
            bundle_id="com.apple.TextEdit",
            process_id=12345,
            app_type=ApplicationType.NATIVE_APP,
            browser_type=None
        )
        with patch.object(handler, '_detect_active_application', return_value=non_browser_app):
            result = handler._extract_browser_content()
            assert result is None, "Should return None for non-browser applications"
            print("✓ Correctly rejects non-browser applications")
        
        # Test 3: Test with browser application but extraction failure
        print("\n3. Testing browser application with extraction failure...")
        browser_app = ApplicationInfo(
            name="Google Chrome",
            bundle_id="com.google.Chrome",
            process_id=12345,
            app_type=ApplicationType.WEB_BROWSER,
            browser_type=BrowserType.CHROME
        )
        
        # Mock BrowserAccessibilityHandler to return None (extraction failure)
        with patch.object(handler, '_detect_active_application', return_value=browser_app):
            # Reset the handler's browser handler to None so it gets re-initialized with our mock
            handler._browser_handler = None
            with patch('modules.browser_accessibility.BrowserAccessibilityHandler') as mock_handler_class:
                mock_handler_instance = Mock()
                mock_handler_instance.get_page_text_content.return_value = None
                mock_handler_class.return_value = mock_handler_instance
                
                result = handler._extract_browser_content()
                assert result is None, "Should return None when extraction fails"
                print("✓ Correctly handles extraction failure")
        
        # Test 4: Test with content too short (validation failure)
        print("\n4. Testing with content too short...")
        short_content = "Short"  # Only 5 characters, less than 50 required
        
        with patch.object(handler, '_detect_active_application', return_value=browser_app):
            handler._browser_handler = None
            with patch('modules.browser_accessibility.BrowserAccessibilityHandler') as mock_handler_class:
                mock_handler_instance = Mock()
                mock_handler_instance.get_page_text_content.return_value = short_content
                mock_handler_class.return_value = mock_handler_instance
                
                result = handler._extract_browser_content()
                assert result is None, "Should return None when content is too short"
                print("✓ Correctly validates content length (>50 characters)")
        
        # Test 5: Test with invalid content (fails validation)
        print("\n5. Testing with invalid content...")
        invalid_content = "Page not found 404 error this page cannot be displayed connection failed"
        
        with patch.object(handler, '_detect_active_application', return_value=browser_app):
            handler._browser_handler = None
            with patch('modules.browser_accessibility.BrowserAccessibilityHandler') as mock_handler_class:
                mock_handler_instance = Mock()
                mock_handler_instance.get_page_text_content.return_value = invalid_content
                mock_handler_class.return_value = mock_handler_instance
                
                result = handler._extract_browser_content()
                assert result is None, "Should return None when content fails validation"
                print("✓ Correctly validates content quality")
        
        # Test 6: Test with valid content
        print("\n6. Testing with valid substantial content...")
        valid_content = """
        Welcome to our website! This is a comprehensive guide about artificial intelligence 
        and machine learning. Here you will find detailed information about various topics 
        including natural language processing, computer vision, and deep learning algorithms.
        Our content is designed to help both beginners and advanced practitioners understand
        the fundamental concepts and practical applications of AI technology.
        """
        
        with patch.object(handler, '_detect_active_application', return_value=browser_app):
            handler._browser_handler = None
            with patch('modules.browser_accessibility.BrowserAccessibilityHandler') as mock_handler_class:
                mock_handler_instance = Mock()
                mock_handler_instance.get_page_text_content.return_value = valid_content
                mock_handler_class.return_value = mock_handler_instance
                
                result = handler._extract_browser_content()
                assert result is not None, "Should return content when extraction succeeds"
                assert len(result) > 50, "Returned content should be substantial"
                assert result == valid_content, "Should return the extracted content"
                print(f"✓ Successfully extracted {len(result)} characters of valid content")
        
        # Test 7: Test timeout handling
        print("\n7. Testing timeout handling...")
        
        def slow_extraction(*args, **kwargs):
            time.sleep(3)  # Sleep longer than 2 second timeout
            return "This should timeout"
        
        with patch.object(handler, '_detect_active_application', return_value=browser_app):
            handler._browser_handler = None
            with patch('modules.browser_accessibility.BrowserAccessibilityHandler') as mock_handler_class:
                mock_handler_instance = Mock()
                mock_handler_instance.get_page_text_content.side_effect = slow_extraction
                mock_handler_class.return_value = mock_handler_instance
                
                start_time = time.time()
                result = handler._extract_browser_content()
                end_time = time.time()
                
                assert result is None, "Should return None when extraction times out"
                assert end_time - start_time < 3, "Should timeout before 3 seconds"
                print("✓ Correctly handles timeout (2 second limit)")
        
        # Test 8: Test different browser types
        print("\n8. Testing different browser types...")
        
        browser_types = [
            (BrowserType.CHROME, "Google Chrome"),
            (BrowserType.SAFARI, "Safari"),
            (BrowserType.FIREFOX, "Mozilla Firefox")
        ]
        
        for browser_type, browser_name in browser_types:
            bundle_ids = {
                "Google Chrome": "com.google.Chrome",
                "Safari": "com.apple.Safari", 
                "Mozilla Firefox": "org.mozilla.firefox"
            }
            test_app = ApplicationInfo(
                name=browser_name,
                bundle_id=bundle_ids[browser_name],
                process_id=12345,
                app_type=ApplicationType.WEB_BROWSER,
                browser_type=browser_type
            )
            
            with patch.object(handler, '_detect_active_application', return_value=test_app):
                handler._browser_handler = None
                with patch('modules.browser_accessibility.BrowserAccessibilityHandler') as mock_handler_class:
                    mock_handler_instance = Mock()
                    mock_handler_instance.get_page_text_content.return_value = valid_content
                    mock_handler_class.return_value = mock_handler_instance
                    
                    result = handler._extract_browser_content()
                    assert result is not None, f"Should work with {browser_name}"
                    print(f"✓ Successfully handles {browser_name}")
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("Task 3: Browser Content Extraction implementation is working correctly")
        print("=" * 60)
        
        # Test content validation method separately
        print("\n9. Testing content validation method...")
        
        # Test valid content
        valid_test_content = "This is a substantial piece of content with multiple words and meaningful information about various topics."
        assert handler._validate_browser_content(valid_test_content) == True, "Should validate good content"
        
        # Test empty content
        assert handler._validate_browser_content("") == False, "Should reject empty content"
        assert handler._validate_browser_content(None) == False, "Should reject None content"
        
        # Test error content
        error_content = "Page not found 404 error"
        assert handler._validate_browser_content(error_content) == False, "Should reject error content"
        
        # Test too short content
        short_content = "Short"
        assert handler._validate_browser_content(short_content) == False, "Should reject short content"
        
        print("✓ Content validation method works correctly")
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_browser_content_extraction()
    sys.exit(0 if success else 1)