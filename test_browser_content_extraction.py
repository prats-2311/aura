#!/usr/bin/env python3
"""
Test script for browser content extraction fast path functionality.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.browser_accessibility import BrowserAccessibilityHandler
from modules.application_detector import ApplicationInfo, BrowserType, ApplicationType

def test_browser_content_extraction():
    """Test browser content extraction functionality."""
    print("Testing browser content extraction fast path...")
    
    # Initialize handler
    handler = BrowserAccessibilityHandler()
    
    # Create mock application info for Chrome
    chrome_app_info = ApplicationInfo(
        name="Google Chrome",
        bundle_id="com.google.Chrome",
        process_id=12345,  # Mock PID
        app_type=ApplicationType.WEB_BROWSER,
        browser_type=BrowserType.CHROME
    )
    
    # Test the get_page_text_content method
    print("Testing Chrome content extraction...")
    try:
        content = handler.get_page_text_content(chrome_app_info)
        if content:
            print(f"✓ Chrome extraction successful: {len(content)} characters")
            print(f"Sample content: {content[:200]}...")
        else:
            print("✗ Chrome extraction returned None (expected if no Chrome window open)")
    except Exception as e:
        print(f"✗ Chrome extraction failed: {e}")
    
    # Create mock application info for Safari
    safari_app_info = ApplicationInfo(
        name="Safari",
        bundle_id="com.apple.Safari",
        process_id=12346,  # Mock PID
        app_type=ApplicationType.WEB_BROWSER,
        browser_type=BrowserType.SAFARI
    )
    
    # Test Safari content extraction
    print("\nTesting Safari content extraction...")
    try:
        content = handler.get_page_text_content(safari_app_info)
        if content:
            print(f"✓ Safari extraction successful: {len(content)} characters")
            print(f"Sample content: {content[:200]}...")
        else:
            print("✗ Safari extraction returned None (expected if no Safari window open)")
    except Exception as e:
        print(f"✗ Safari extraction failed: {e}")
    
    print("\nBrowser content extraction test completed.")

if __name__ == "__main__":
    test_browser_content_extraction()