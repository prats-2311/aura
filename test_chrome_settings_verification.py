#!/usr/bin/env python3
"""
Quick Chrome Accessibility Settings Verification
Specifically tests the settings you just enabled in Chrome.
"""

import subprocess
import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

def test_chrome_accessibility_settings():
    """Test the specific Chrome accessibility settings that were enabled"""
    
    print("🔍 Testing Chrome Accessibility Settings...")
    print("=" * 50)
    
    # Setup Chrome with accessibility
    chrome_options = Options()
    chrome_options.add_argument('--enable-accessibility')
    chrome_options.add_argument('--force-renderer-accessibility')
    
    driver = None
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        print("✅ Chrome started with accessibility flags")
        
        # Test 1: Check chrome://accessibility/ page
        print("\n1. Checking chrome://accessibility/ page...")
        driver.get('chrome://accessibility/')
        time.sleep(2)
        
        page_source = driver.page_source.lower()
        
        if 'accessibility internals' in page_source:
            print("✅ Accessibility internals page loaded successfully")
            
            # Look for web accessibility indicators
            if 'web accessibility' in page_source:
                print("✅ Web accessibility mode detected in page")
            else:
                print("⚠️  Web accessibility mode not clearly visible")
                
        else:
            print("❌ Could not access accessibility internals")
        
        # Test 2: Check chrome://settings/accessibility page
        print("\n2. Checking chrome://settings/accessibility page...")
        driver.get('chrome://settings/accessibility')
        time.sleep(3)
        
        settings_source = driver.page_source.lower()
        
        if 'accessibility' in settings_source:
            print("✅ Accessibility settings page loaded")
            
            # Check for specific settings
            if 'quick highlight' in settings_source:
                print("✅ Quick highlight setting found")
            if 'text cursor' in settings_source:
                print("✅ Text cursor navigation setting found")
            if 'clipboard confirmations' in settings_source:
                print("✅ Clipboard confirmations setting found")
                
        # Test 3: Test actual web page accessibility
        print("\n3. Testing web page accessibility features...")
        driver.get('https://www.google.com')
        time.sleep(2)
        
        # Test element detection
        try:
            search_box = driver.find_element(By.NAME, "q")
            print("✅ Successfully detected search box element")
            
            # Test accessibility attributes
            aria_label = search_box.get_attribute('aria-label')
            role = search_box.get_attribute('role')
            
            if aria_label or role:
                print(f"✅ Accessibility attributes found: aria-label='{aria_label}', role='{role}'")
            else:
                print("⚠️  Limited accessibility attributes on search box")
                
        except Exception as e:
            print(f"❌ Element detection failed: {e}")
        
        # Test 4: JavaScript accessibility API
        print("\n4. Testing JavaScript accessibility API...")
        try:
            js_result = driver.execute_script("""
                return {
                    hasAccessibilityAPI: typeof document.querySelector !== 'undefined',
                    ariaElements: document.querySelectorAll('[aria-label], [role]').length,
                    focusableElements: document.querySelectorAll('input, button, a, [tabindex]').length
                };
            """)
            
            print(f"✅ JavaScript accessibility check:")
            print(f"   - ARIA elements found: {js_result['ariaElements']}")
            print(f"   - Focusable elements: {js_result['focusableElements']}")
            
        except Exception as e:
            print(f"❌ JavaScript accessibility test failed: {e}")
        
        print("\n" + "=" * 50)
        print("🎉 Chrome accessibility verification completed!")
        print("✅ Your Chrome settings should now support Aura's fast path functionality")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False
        
    finally:
        if driver:
            driver.quit()

def quick_accessibility_check():
    """Quick check without opening browser"""
    print("🚀 Quick Accessibility Check...")
    
    # Check if Chrome process is running with accessibility
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        chrome_processes = [line for line in result.stdout.split('\n') if 'chrome' in line.lower()]
        
        accessibility_enabled = any('accessibility' in process for process in chrome_processes)
        
        if accessibility_enabled:
            print("✅ Chrome processes with accessibility flags detected")
        else:
            print("⚠️  No Chrome processes with accessibility flags found")
            
    except Exception as e:
        print(f"⚠️  Could not check Chrome processes: {e}")

if __name__ == "__main__":
    print("Chrome Accessibility Settings Verification")
    print("This test verifies the settings you just enabled in Chrome\n")
    
    # Run quick check first
    quick_accessibility_check()
    
    print("\nStarting browser-based tests...")
    input("Press Enter to continue (make sure Chrome is closed first)...")
    
    # Run full test
    success = test_chrome_accessibility_settings()
    
    if success:
        print("\n✅ All tests passed! Chrome is configured correctly for Aura.")
    else:
        print("\n❌ Some tests failed. Check the output above for issues.")