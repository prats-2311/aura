#!/usr/bin/env python3
"""
AppleScript Application Detection Test

This test forces the use of AppleScript for application detection
to see if that method works correctly for our use case.
"""

import sys
import os
import subprocess
import time
import logging

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_active_app_applescript():
    """Get active application using AppleScript method."""
    try:
        # AppleScript to get frontmost application with detailed info
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
            print(f"AppleScript failed: {result.stderr}")
            return None
        
        # Parse the result
        parts = result.stdout.strip().split('|')
        if len(parts) < 3:
            print(f"Unexpected AppleScript format: {result.stdout}")
            return None
        
        app_name = parts[0]
        try:
            process_id = int(parts[1])
        except ValueError:
            process_id = 0
        bundle_id = parts[2] if parts[2] != "unknown" else "unknown"
        
        return {
            'name': app_name,
            'process_id': process_id,
            'bundle_id': bundle_id
        }
        
    except Exception as e:
        print(f"AppleScript exception: {e}")
        return None

def classify_application_simple(app_info):
    """Simple application classification."""
    app_name = app_info['name'].lower()
    bundle_id = app_info['bundle_id'].lower()
    
    # Browser detection
    browser_indicators = [
        'chrome', 'safari', 'firefox', 'edge', 'brave', 'opera'
    ]
    
    for browser in browser_indicators:
        if browser in app_name or browser in bundle_id:
            return 'web_browser', browser
    
    # PDF reader detection
    pdf_indicators = [
        'preview', 'acrobat', 'pdf', 'skim'
    ]
    
    for pdf_app in pdf_indicators:
        if pdf_app in app_name or pdf_app in bundle_id:
            return 'pdf_reader', None
    
    return 'native_app', None

def test_applescript_detection():
    """Test AppleScript-based application detection."""
    
    print("🍎 AppleScript Application Detection Test")
    print("=" * 50)
    print("This test uses AppleScript to detect applications")
    print("and classify them for fast path support.")
    print("=" * 50)
    
    while True:
        print(f"\nCurrent time: {time.strftime('%H:%M:%S')}")
        
        # Get application info using AppleScript
        app_info = get_active_app_applescript()
        
        if app_info:
            print(f"📱 Detected app: {app_info['name']}")
            print(f"   Process ID: {app_info['process_id']}")
            print(f"   Bundle ID: {app_info['bundle_id']}")
            
            # Classify the application
            app_type, browser_type = classify_application_simple(app_info)
            print(f"   Type: {app_type}")
            
            if browser_type:
                print(f"   Browser: {browser_type}")
            
            # Check if supported for fast path
            supported = app_type in ['web_browser', 'pdf_reader']
            print(f"   Fast Path: {'✅ Supported' if supported else '❌ Not supported'}")
            
        else:
            print("❌ Could not detect active application")
        
        print("\n" + "-" * 50)
        choice = input("Press Enter to test again, or 'q' to quit: ").strip().lower()
        if choice == 'q':
            break

def test_with_timer_applescript():
    """Test AppleScript detection with timer for switching."""
    
    print("⏰ Timed AppleScript Detection Test")
    print("=" * 50)
    
    while True:
        print("\nYou have 10 seconds to switch to a different application...")
        print("Try switching to Chrome, Safari, Preview, or any other app.")
        
        # Show countdown
        for i in range(10, 0, -1):
            print(f"   {i} seconds remaining...", end='\r')
            time.sleep(1)
        print("   Testing now...                    ")
        
        # Test AppleScript detection
        app_info = get_active_app_applescript()
        
        if app_info:
            print(f"\n📱 AppleScript detected: {app_info['name']}")
            
            # Classify the application
            app_type, browser_type = classify_application_simple(app_info)
            print(f"   Type: {app_type}")
            
            if browser_type:
                print(f"   Browser: {browser_type}")
            
            # Check if this would work for fast path
            if app_type == 'web_browser':
                print("   ✅ This is a web browser - fast path would work!")
                print("   🌐 Browser content extraction would be attempted")
            elif app_type == 'pdf_reader':
                print("   ✅ This is a PDF reader - fast path would work!")
                print("   📄 PDF content extraction would be attempted")
            else:
                print("   ❌ Not supported for fast path")
                print("   🔄 Would fall back to vision processing")
        else:
            print("\n❌ AppleScript detection failed")
        
        choice = input("\nPress Enter to test again, or 'q' to quit: ").strip().lower()
        if choice == 'q':
            break

def test_chrome_detection_applescript():
    """Test Chrome detection specifically using AppleScript."""
    
    print("🌐 Chrome Detection Test (AppleScript)")
    print("=" * 50)
    print("This test focuses on Chrome detection for summarization.")
    print("=" * 50)
    
    print("\n1️⃣ Please switch to Chrome browser now...")
    print("   • Open Chrome if not running")
    print("   • Load any webpage")
    print("   • Make sure Chrome is the active window")
    
    print("\n⏰ You have 10 seconds to switch to Chrome...")
    
    # Countdown
    for i in range(10, 0, -1):
        print(f"   {i} seconds remaining...", end='\r')
        time.sleep(1)
    print("   Testing Chrome detection now...    ")
    
    # Test detection
    app_info = get_active_app_applescript()
    
    if app_info:
        print(f"\n📱 Detected: {app_info['name']}")
        print(f"   Bundle ID: {app_info['bundle_id']}")
        
        # Check if it's Chrome
        app_name_lower = app_info['name'].lower()
        bundle_id_lower = app_info['bundle_id'].lower()
        
        is_chrome = 'chrome' in app_name_lower or 'chrome' in bundle_id_lower
        
        if is_chrome:
            print("✅ Chrome detected successfully!")
            
            # Test if we can use this for content extraction
            print("\n2️⃣ Testing content extraction simulation...")
            
            # Create a mock ApplicationInfo object
            try:
                from modules.application_detector import ApplicationInfo, ApplicationType, BrowserType
                
                mock_app_info = ApplicationInfo(
                    name=app_info['name'],
                    bundle_id=app_info['bundle_id'],
                    process_id=app_info['process_id'],
                    app_type=ApplicationType.WEB_BROWSER,
                    browser_type=BrowserType.CHROME,
                    detection_confidence=0.95
                )
                
                print(f"✅ Mock ApplicationInfo created")
                print(f"   Name: {mock_app_info.name}")
                print(f"   Type: {mock_app_info.app_type.value}")
                print(f"   Browser: {mock_app_info.browser_type.value}")
                
                # Test with QuestionAnsweringHandler
                print("\n3️⃣ Testing with QuestionAnsweringHandler...")
                
                from handlers.question_answering_handler import QuestionAnsweringHandler
                
                class MockOrchestrator:
                    pass
                
                handler = QuestionAnsweringHandler(MockOrchestrator())
                
                # Test application support
                is_supported = handler._is_supported_application(mock_app_info)
                print(f"   Supported: {'✅ Yes' if is_supported else '❌ No'}")
                
                # Test extraction method
                extraction_method = handler._get_extraction_method(mock_app_info)
                print(f"   Extraction method: {extraction_method}")
                
                if is_supported and extraction_method == 'browser':
                    print("✅ Chrome would be supported for fast path summarization!")
                    return True
                else:
                    print("❌ Chrome support test failed")
                    return False
                    
            except Exception as e:
                print(f"❌ Content extraction test failed: {e}")
                return False
        else:
            print(f"❌ Chrome not detected. Got: {app_info['name']}")
            return False
    else:
        print("❌ No application detected")
        return False

def main():
    """Main test function."""
    
    print("🧪 AppleScript Application Detection Test Suite")
    print("=" * 50)
    print("This test uses AppleScript to detect applications,")
    print("bypassing the AppKit issues we've been seeing.")
    print("=" * 50)
    
    print("\nChoose test mode:")
    print("1. Manual testing")
    print("2. Timed testing (10-second countdown)")
    print("3. Chrome-specific test")
    
    while True:
        choice = input("\nEnter choice (1-3): ").strip()
        
        if choice == '1':
            test_applescript_detection()
            break
        elif choice == '2':
            test_with_timer_applescript()
            break
        elif choice == '3':
            success = test_chrome_detection_applescript()
            print(f"\n🎯 Chrome test: {'✅ PASSED' if success else '❌ FAILED'}")
            break
        else:
            print("❌ Invalid choice. Please enter 1-3.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Test interrupted by user.")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()