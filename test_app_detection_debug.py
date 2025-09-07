#!/usr/bin/env python3
"""
Application Detection Debug Test

This script helps debug application detection issues by continuously
monitoring the active application and showing detailed information.
"""

import sys
import os
import time
import logging

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def continuous_app_detection():
    """Continuously monitor active application."""
    
    print("🔍 Application Detection Debug Tool")
    print("=" * 50)
    print("This tool will continuously show the active application.")
    print("Switch between applications to test detection.")
    print("Press Ctrl+C to stop.")
    print("=" * 50)
    
    try:
        from modules.application_detector import ApplicationDetector
        detector = ApplicationDetector()
        
        last_app_name = None
        
        while True:
            try:
                app_info = detector.get_active_application_info()
                
                if app_info:
                    current_app_name = f"{app_info.name} ({app_info.app_type.value})"
                    
                    # Only print if application changed
                    if current_app_name != last_app_name:
                        print(f"\n📱 Active App: {app_info.name}")
                        print(f"   Type: {app_info.app_type.value}")
                        
                        if hasattr(app_info, 'browser_type') and app_info.browser_type:
                            print(f"   Browser: {app_info.browser_type.value}")
                        
                        if hasattr(app_info, 'bundle_id') and app_info.bundle_id:
                            print(f"   Bundle ID: {app_info.bundle_id}")
                        
                        # Check if supported for fast path
                        from modules.application_detector import ApplicationType
                        supported = app_info.app_type in [ApplicationType.WEB_BROWSER, ApplicationType.PDF_READER]
                        print(f"   Fast Path: {'✅ Supported' if supported else '❌ Not supported'}")
                        
                        last_app_name = current_app_name
                else:
                    if last_app_name != "None":
                        print("\n📱 No active application detected")
                        last_app_name = "None"
                
                time.sleep(1)  # Check every second
                
            except Exception as e:
                print(f"❌ Detection error: {e}")
                time.sleep(2)
                
    except KeyboardInterrupt:
        print("\n\n👋 Monitoring stopped by user.")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()

def test_specific_applications():
    """Test detection of specific applications."""
    
    print("\n🎯 Specific Application Detection Test")
    print("=" * 50)
    
    applications_to_test = [
        ("Chrome", "web_browser"),
        ("Safari", "web_browser"), 
        ("Firefox", "web_browser"),
        ("Preview", "pdf_reader"),
        ("Adobe Acrobat Reader", "pdf_reader"),
        ("Kiro", "native_app")
    ]
    
    try:
        from modules.application_detector import ApplicationDetector
        detector = ApplicationDetector()
        
        for app_name, expected_type in applications_to_test:
            print(f"\n🔍 Switch to {app_name} now...")
            print(f"⏰ You have 10 seconds to switch to {app_name}...")
            
            # Countdown timer for switching
            for i in range(10, 0, -1):
                print(f"   Switching to {app_name} in {i} seconds...", end='\r')
                time.sleep(1)
            print(f"   Checking {app_name} application now...        ")
            
            app_info = detector.get_active_application_info()
            
            if app_info:
                print(f"✅ Detected: {app_info.name} ({app_info.app_type.value})")
                
                if app_name.lower() in app_info.name.lower():
                    print(f"✅ Correct application detected")
                else:
                    print(f"⚠️ Expected {app_name}, got {app_info.name}")
                
                if app_info.app_type.value == expected_type:
                    print(f"✅ Correct type: {expected_type}")
                else:
                    print(f"⚠️ Expected type {expected_type}, got {app_info.app_type.value}")
            else:
                print(f"❌ No application detected")
    
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

def test_browser_accessibility():
    """Test browser accessibility detection."""
    
    print("\n🌐 Browser Accessibility Test")
    print("=" * 50)
    
    try:
        from modules.application_detector import ApplicationDetector
        from modules.browser_accessibility import BrowserAccessibilityHandler
        
        detector = ApplicationDetector()
        browser_handler = BrowserAccessibilityHandler()
        
        print("Switch to a browser with a webpage loaded...")
        print("⏰ You have 10 seconds to switch to a browser...")
        
        # Countdown timer for switching to browser
        for i in range(10, 0, -1):
            print(f"   Switching to browser in {i} seconds...", end='\r')
            time.sleep(1)
        print("   Checking browser application now...        ")
        
        app_info = detector.get_active_application_info()
        
        if app_info:
            print(f"📱 Detected: {app_info.name} ({app_info.app_type.value})")
            
            if app_info.app_type.value == 'web_browser':
                print("🔍 Testing content extraction...")
                
                try:
                    content = browser_handler.get_page_text_content(app_info)
                    
                    if content:
                        print(f"✅ Content extracted: {len(content)} characters")
                        print(f"📝 Preview: {content[:200]}...")
                    else:
                        print("❌ No content extracted")
                        
                except Exception as e:
                    print(f"❌ Content extraction failed: {e}")
            else:
                print("⚠️ Not a browser application")
        else:
            print("❌ No application detected")
    
    except Exception as e:
        print(f"❌ Browser test failed: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main debug function."""
    
    print("🔧 Application Detection Debug Suite")
    print("=" * 50)
    print("1. Continuous monitoring")
    print("2. Test specific applications")
    print("3. Test browser accessibility")
    print("4. Exit")
    print("=" * 50)
    
    while True:
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == '1':
            continuous_app_detection()
        elif choice == '2':
            test_specific_applications()
        elif choice == '3':
            test_browser_accessibility()
        elif choice == '4':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please enter 1-4.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Debug session interrupted by user.")
    except Exception as e:
        print(f"\n❌ Debug session failed: {e}")
        import traceback
        traceback.print_exc()