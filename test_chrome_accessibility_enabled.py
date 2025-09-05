#!/usr/bin/env python3
"""
Test Chrome accessibility after enabling accessibility features.
"""

import sys
import time
import subprocess
from modules.accessibility import AccessibilityModule
from Cocoa import NSWorkspace

def test_chrome_with_accessibility():
    """Test Chrome accessibility after enabling features."""
    
    print("=== Chrome Accessibility Test (After Enabling Features) ===")
    print("Make sure you have enabled Chrome accessibility features:")
    print("1. Go to chrome://settings/accessibility")
    print("2. Enable 'Live Caption' or any accessibility feature")
    print("3. Or go to chrome://flags/ and enable 'Experimental Accessibility Features'")
    print("\nPress Enter when ready...")
    input()
    
    print("\n⏱️  Starting 5-second timer to switch to Chrome...")
    for i in range(5, 0, -1):
        print(f"   {i} seconds remaining - Switch to Chrome now!")
        time.sleep(1)
    print("   🚀 Starting accessibility test...")
    
    # Force focus to Chrome
    workspace = NSWorkspace.sharedWorkspace()
    apps = workspace.runningApplications()
    
    chrome_app = None
    for app in apps:
        bundle_id = app.bundleIdentifier()
        if bundle_id and 'chrome' in bundle_id.lower():
            chrome_app = app
            break
    
    if chrome_app:
        chrome_app.activateWithOptions_(1)
        time.sleep(2)
        print(f"Focused: {chrome_app.localizedName()}")
        
        # Test accessibility
        acc = AccessibilityModule()
        
        print("\n=== Testing Enhanced Fast Path Elements ===")
        
        # Test the exact elements from your commands
        test_elements = [
            ("", "Gmail"),           # Gmail link
            ("AXLink", "Gmail"),     # Gmail as link
            ("", "Google Search"),   # Google Search button  
            ("AXButton", "Google Search"),
            ("AXButton", "Search"),
            ("", "I'm Feeling Lucky"),
            ("AXButton", "I'm Feeling Lucky")
        ]
        
        found_any = False
        for role, label in test_elements:
            result = acc.find_element_enhanced(role, label, None)
            status = "✅ FOUND" if result.found else "❌ NOT FOUND"
            print(f"{status} | {role or 'any':12} | {label:20} | Confidence: {result.confidence_score:.2f}")
            
            if result.found:
                found_any = True
                print(f"         | Match: {result.matched_attribute} | Time: {result.search_time_ms:.1f}ms")
                print(f"         | Roles checked: {len(result.roles_checked)} | Attributes: {len(result.attributes_checked)}")
        
        # Check accessibility status
        print(f"\n=== Accessibility Status ===")
        status = acc.get_accessibility_status()
        for key, value in status.items():
            indicator = "✅" if (key == "permissions_granted" and value) else "ℹ️"
            print(f"{indicator} {key}: {value}")
        
        if found_any:
            print(f"\n🎉 SUCCESS! Enhanced fast path should now work!")
            print(f"Try running AURA again with 'Click on Gmail link' or 'Click on Google Search button'")
        else:
            print(f"\n⚠️  Still no elements found. Try:")
            print(f"1. Refresh the Google page")
            print(f"2. Make sure Chrome accessibility is fully enabled")
            print(f"3. Try Safari instead of Chrome")
            
    else:
        print("Chrome not found. Please open Chrome first.")

if __name__ == "__main__":
    test_chrome_with_accessibility()