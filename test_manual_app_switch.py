#!/usr/bin/env python3
"""
Manual Application Switch Test

This test helps verify if application switching is working by
manually checking applications step by step.
"""

import sys
import os
import time
import logging

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_current_app():
    """Get current application using the detector."""
    try:
        from modules.application_detector import ApplicationDetector
        detector = ApplicationDetector()
        return detector.get_active_application_info()
    except Exception as e:
        print(f"Error detecting app: {e}")
        return None

def test_manual_switching():
    """Test manual application switching with user confirmation."""
    
    print("🔄 Manual Application Switch Test")
    print("=" * 50)
    print("This test will help us verify if application switching works.")
    print("We'll check the current app, then you switch, then we check again.")
    print("=" * 50)
    
    # Step 1: Check current application
    print("\n1️⃣ Checking current application...")
    current_app = get_current_app()
    
    if current_app:
        print(f"📱 Current app: {current_app.name} ({current_app.app_type.value})")
        print(f"   Bundle ID: {current_app.bundle_id}")
        print(f"   Process ID: {current_app.process_id}")
    else:
        print("❌ Could not detect current application")
        return False
    
    # Step 2: Ask user to switch to Chrome
    print("\n2️⃣ Now please do the following:")
    print("   • Open Chrome browser (if not already open)")
    print("   • Click on Chrome to make it the active window")
    print("   • Make sure Chrome is in the foreground")
    print("   • Wait for the countdown to finish")
    
    input("\nPress Enter when Chrome is ready and active...")
    
    print("\n⏰ Checking in 5 seconds...")
    for i in range(5, 0, -1):
        print(f"   {i}...", end=' ', flush=True)
        time.sleep(1)
    print("Now!")
    
    # Check if app changed
    new_app = get_current_app()
    
    if new_app:
        print(f"\n📱 New app: {new_app.name} ({new_app.app_type.value})")
        print(f"   Bundle ID: {new_app.bundle_id}")
        print(f"   Process ID: {new_app.process_id}")
        
        if new_app.name != current_app.name:
            print("✅ Application switch detected!")
            
            if 'chrome' in new_app.name.lower():
                print("✅ Chrome browser detected correctly!")
                return True
            else:
                print(f"⚠️ Different app detected: {new_app.name}")
                return True
        else:
            print("❌ No application switch detected")
            print("   The same application is still active")
            return False
    else:
        print("❌ Could not detect new application")
        return False

def test_multiple_switches():
    """Test switching between multiple applications."""
    
    print("\n🔄 Multiple Application Switch Test")
    print("=" * 50)
    
    apps_to_test = [
        ("Chrome", "web browser"),
        ("Safari", "web browser"),
        ("Preview", "PDF reader"),
        ("Finder", "file manager"),
        ("Terminal", "terminal")
    ]
    
    results = []
    
    for app_name, app_description in apps_to_test:
        print(f"\n🎯 Testing {app_name} ({app_description})")
        print(f"   Please switch to {app_name} now...")
        
        input(f"Press Enter when {app_name} is active...")
        
        print("⏰ Checking in 3 seconds...")
        for i in range(3, 0, -1):
            print(f"   {i}...", end=' ', flush=True)
            time.sleep(1)
        print("Now!")
        
        detected_app = get_current_app()
        
        if detected_app:
            print(f"📱 Detected: {detected_app.name}")
            
            if app_name.lower() in detected_app.name.lower():
                print(f"✅ {app_name} detected correctly!")
                results.append((app_name, True, detected_app.name))
            else:
                print(f"⚠️ Expected {app_name}, got {detected_app.name}")
                results.append((app_name, False, detected_app.name))
        else:
            print(f"❌ Could not detect any application")
            results.append((app_name, False, "None"))
    
    # Show results
    print("\n" + "=" * 50)
    print("📊 RESULTS SUMMARY")
    print("=" * 50)
    
    correct_count = 0
    for app_name, correct, detected_name in results:
        status = "✅" if correct else "❌"
        print(f"{status} {app_name}: detected as '{detected_name}'")
        if correct:
            correct_count += 1
    
    print(f"\n📈 Success rate: {correct_count}/{len(results)} ({correct_count/len(results)*100:.1f}%)")
    
    return correct_count > 0

def test_chrome_specifically():
    """Test Chrome detection specifically for our use case."""
    
    print("\n🌐 Chrome-Specific Detection Test")
    print("=" * 50)
    print("This test focuses specifically on Chrome detection")
    print("since that's what we need for the summarization feature.")
    print("=" * 50)
    
    # Step 1: Make sure Chrome is not active
    print("\n1️⃣ First, make sure Chrome is NOT the active application")
    print("   Click on any other application (Finder, Terminal, etc.)")
    
    input("Press Enter when Chrome is NOT active...")
    
    current_app = get_current_app()
    if current_app:
        print(f"📱 Current app: {current_app.name}")
        
        if 'chrome' in current_app.name.lower():
            print("⚠️ Chrome is still active. Please switch to another app first.")
            return False
    
    # Step 2: Now switch to Chrome
    print("\n2️⃣ Now switch to Chrome:")
    print("   • Open Chrome if it's not running")
    print("   • Click on Chrome window to make it active")
    print("   • Make sure a webpage is loaded")
    
    input("Press Enter when Chrome is active with a webpage...")
    
    print("⏰ Checking Chrome detection in 5 seconds...")
    for i in range(5, 0, -1):
        print(f"   {i}...", end=' ', flush=True)
        time.sleep(1)
    print("Now!")
    
    chrome_app = get_current_app()
    
    if chrome_app:
        print(f"📱 Detected app: {chrome_app.name}")
        print(f"   Type: {chrome_app.app_type.value}")
        print(f"   Bundle ID: {chrome_app.bundle_id}")
        
        if 'chrome' in chrome_app.name.lower():
            print("✅ Chrome detected successfully!")
            
            if chrome_app.app_type.value == 'web_browser':
                print("✅ Correctly identified as web browser!")
                
                # Test if we can extract content
                print("\n3️⃣ Testing content extraction...")
                try:
                    from modules.browser_accessibility import BrowserAccessibilityHandler
                    browser_handler = BrowserAccessibilityHandler()
                    
                    content = browser_handler.get_page_text_content(chrome_app)
                    
                    if content:
                        print(f"✅ Content extracted: {len(content)} characters")
                        print(f"   Preview: {content[:100]}...")
                        return True
                    else:
                        print("❌ No content extracted")
                        return False
                        
                except Exception as e:
                    print(f"❌ Content extraction failed: {e}")
                    return False
            else:
                print(f"⚠️ Wrong type detected: {chrome_app.app_type.value}")
                return False
        else:
            print(f"❌ Wrong application detected: {chrome_app.name}")
            return False
    else:
        print("❌ No application detected")
        return False

def main():
    """Main test function."""
    
    print("🧪 Manual Application Switch Test Suite")
    print("=" * 50)
    print("This test helps debug application detection issues")
    print("by manually verifying application switching works.")
    print("=" * 50)
    
    print("\nChoose a test:")
    print("1. Basic switch test (Kiro → Chrome)")
    print("2. Multiple applications test")
    print("3. Chrome-specific test")
    print("4. All tests")
    
    while True:
        choice = input("\nEnter choice (1-4): ").strip()
        
        if choice == '1':
            success = test_manual_switching()
            print(f"\n🎯 Basic switch test: {'✅ PASSED' if success else '❌ FAILED'}")
            break
        elif choice == '2':
            success = test_multiple_switches()
            print(f"\n🎯 Multiple switches test: {'✅ PASSED' if success else '❌ FAILED'}")
            break
        elif choice == '3':
            success = test_chrome_specifically()
            print(f"\n🎯 Chrome-specific test: {'✅ PASSED' if success else '❌ FAILED'}")
            break
        elif choice == '4':
            print("\n🔄 Running all tests...")
            
            basic_success = test_manual_switching()
            multiple_success = test_multiple_switches()
            chrome_success = test_chrome_specifically()
            
            print("\n" + "=" * 50)
            print("📊 FINAL RESULTS")
            print("=" * 50)
            print(f"Basic switch test: {'✅ PASSED' if basic_success else '❌ FAILED'}")
            print(f"Multiple switches: {'✅ PASSED' if multiple_success else '❌ FAILED'}")
            print(f"Chrome-specific: {'✅ PASSED' if chrome_success else '❌ FAILED'}")
            
            overall_success = basic_success or multiple_success or chrome_success
            print(f"\n🎯 Overall: {'✅ SOME TESTS PASSED' if overall_success else '❌ ALL TESTS FAILED'}")
            
            return overall_success
        else:
            print("❌ Invalid choice. Please enter 1-4.")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n👋 Test interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)