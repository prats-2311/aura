#!/usr/bin/env python3
"""
Simple browser content extraction using the implemented handler

This script uses the actual QuestionAnsweringHandler implementation
to extract content from browsers.
"""

import sys
import os
import logging
import subprocess

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_chrome_content_simple():
    """Get Chrome content using a simple AppleScript."""
    
    print("📄 Extracting content from Chrome...")
    
    try:
        # Simple AppleScript to get Chrome tab info
        applescript = '''
        tell application "Google Chrome"
            if (count of windows) > 0 then
                tell active tab of front window
                    set pageTitle to title
                    set pageURL to URL
                    return "TITLE:" & pageTitle & "\\nURL:" & pageURL
                end tell
            else
                return "No Chrome windows"
            end if
        end tell
        '''
        
        result = subprocess.run(
            ["osascript", "-e", applescript],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            output = result.stdout.strip()
            print(f"✓ Chrome tab info: {output}")
            return output
        else:
            print(f"❌ Chrome AppleScript failed: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"❌ Error getting Chrome content: {e}")
        return None

def test_browser_handler_with_mock():
    """Test the browser handler with a mock application."""
    
    print("\n" + "=" * 60)
    print("Testing Browser Handler Implementation")
    print("=" * 60)
    
    try:
        from handlers.question_answering_handler import QuestionAnsweringHandler
        from modules.application_detector import ApplicationInfo, ApplicationType, BrowserType
        from unittest.mock import Mock
        
        # Create handler
        handler = QuestionAnsweringHandler(Mock())
        print("✓ Handler created")
        
        # Create a mock Chrome application
        chrome_app = ApplicationInfo(
            name="Google Chrome",
            bundle_id="com.google.Chrome",
            process_id=12345,
            app_type=ApplicationType.WEB_BROWSER,
            browser_type=BrowserType.CHROME
        )
        
        print("✓ Mock Chrome application created")
        
        # Override the detection method to return our mock app
        handler._detect_active_application = lambda: chrome_app
        
        # Try to extract content
        print("\n📄 Testing browser content extraction...")
        content = handler._extract_browser_content()
        
        if content:
            print(f"✅ SUCCESS! Extracted {len(content)} characters")
            print("\n" + "=" * 60)
            print("EXTRACTED CONTENT:")
            print("=" * 60)
            print(content[:1000] + "..." if len(content) > 1000 else content)
            print("=" * 60)
            
            # Test validation
            is_valid = handler._validate_browser_content(content)
            print(f"\n✅ Content validation: {'PASSED' if is_valid else 'FAILED'}")
            
            # Show stats
            word_count = len(content.split())
            print(f"📊 Statistics:")
            print(f"  - Characters: {len(content)}")
            print(f"  - Words: {word_count}")
            print(f"  - Valid: {is_valid}")
            
            return True
        else:
            print("❌ No content extracted")
            print("This could mean:")
            print("  - Chrome is not running")
            print("  - No active tab with content")
            print("  - Accessibility permissions needed")
            print("  - Content extraction timed out")
            return False
            
    except Exception as e:
        print(f"❌ Error testing handler: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_browser_accessibility_direct():
    """Test BrowserAccessibilityHandler directly."""
    
    print("\n" + "=" * 60)
    print("Testing BrowserAccessibilityHandler Directly")
    print("=" * 60)
    
    try:
        from modules.browser_accessibility import BrowserAccessibilityHandler
        from modules.application_detector import ApplicationInfo, ApplicationType, BrowserType
        
        # Create handler
        browser_handler = BrowserAccessibilityHandler()
        print("✓ BrowserAccessibilityHandler created")
        
        # Create mock Chrome app
        chrome_app = ApplicationInfo(
            name="Google Chrome",
            bundle_id="com.google.Chrome",
            process_id=12345,
            app_type=ApplicationType.WEB_BROWSER,
            browser_type=BrowserType.CHROME
        )
        
        print("✓ Testing with mock Chrome application")
        
        # Try direct extraction
        content = browser_handler.get_page_text_content(chrome_app)
        
        if content:
            print(f"✅ SUCCESS! Direct extraction got {len(content)} characters")
            print("\nFirst 300 characters:")
            print("-" * 40)
            print(content[:300] + "..." if len(content) > 300 else content)
            print("-" * 40)
            return True
        else:
            print("❌ Direct extraction returned no content")
            return False
            
    except Exception as e:
        print(f"❌ Error in direct extraction: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_chrome_running():
    """Check if Chrome is running and has windows."""
    
    print("🔍 Checking Chrome status...")
    
    try:
        # Check if Chrome process is running
        result = subprocess.run(
            ["pgrep", "-f", "Google Chrome"],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print("❌ Chrome is not running")
            return False
        
        print("✓ Chrome process found")
        
        # Check if Chrome has windows
        applescript = '''
        tell application "Google Chrome"
            return count of windows
        end tell
        '''
        
        result = subprocess.run(
            ["osascript", "-e", applescript],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            window_count = int(result.stdout.strip())
            print(f"✓ Chrome has {window_count} window(s)")
            return window_count > 0
        else:
            print(f"⚠️  Could not check Chrome windows: {result.stderr}")
            return True  # Assume it's okay
            
    except Exception as e:
        print(f"⚠️  Error checking Chrome: {e}")
        return True  # Assume it's okay

def main():
    """Main function."""
    
    print("=" * 60)
    print("Browser Content Extraction Test")
    print("=" * 60)
    
    # Check Chrome status
    chrome_ok = check_chrome_running()
    
    if not chrome_ok:
        print("\n❌ Please open Chrome with a webpage and try again")
        return False
    
    # Get basic Chrome info
    chrome_info = get_chrome_content_simple()
    
    # Test the handler implementation
    print("\n" + "=" * 40)
    print("Testing Handler Implementation")
    print("=" * 40)
    
    handler_success = test_browser_handler_with_mock()
    
    # Test direct browser handler
    print("\n" + "=" * 40)
    print("Testing Direct Browser Handler")
    print("=" * 40)
    
    direct_success = test_browser_accessibility_direct()
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    if handler_success:
        print("✅ QuestionAnsweringHandler browser extraction: WORKING")
    else:
        print("❌ QuestionAnsweringHandler browser extraction: FAILED")
    
    if direct_success:
        print("✅ BrowserAccessibilityHandler direct extraction: WORKING")
    else:
        print("❌ BrowserAccessibilityHandler direct extraction: FAILED")
    
    if chrome_info:
        print("✅ Chrome communication: WORKING")
    else:
        print("❌ Chrome communication: FAILED")
    
    overall_success = handler_success or direct_success
    
    if overall_success:
        print("\n🎉 Browser content extraction is functional!")
    else:
        print("\n❌ Browser content extraction needs troubleshooting")
        print("\nTips:")
        print("1. Make sure Chrome is open with a webpage")
        print("2. Grant accessibility permissions to Terminal")
        print("3. Try running: System Preferences > Security & Privacy > Accessibility")
    
    return overall_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)