#!/usr/bin/env python3
"""
Test browser accessibility with explicit focus management.
"""

import sys
import time
import subprocess
from modules.accessibility import AccessibilityModule
from Cocoa import NSWorkspace

def test_browser_accessibility():
    """Test accessibility with browser focus."""
    
    print("=== Browser Accessibility Test ===")
    
    # Step 1: Open Chrome with Google
    print("1. Opening Chrome with Google...")
    try:
        subprocess.run(['open', '-a', 'Google Chrome', 'https://google.com'], check=True)
        time.sleep(3)  # Wait for Chrome to load
    except subprocess.CalledProcessError:
        print("Chrome not found, trying Safari...")
        subprocess.run(['open', '-a', 'Safari', 'https://google.com'], check=True)
        time.sleep(3)
    
    # Step 2: Force focus to browser
    print("2. Focusing browser window...")
    workspace = NSWorkspace.sharedWorkspace()
    
    # Get all running applications
    apps = workspace.runningApplications()
    browser_app = None
    
    for app in apps:
        bundle_id = app.bundleIdentifier()
        if bundle_id and ('chrome' in bundle_id.lower() or 'safari' in bundle_id.lower()):
            browser_app = app
            break
    
    if browser_app:
        # Force activate the browser
        browser_app.activateWithOptions_(1)  # NSApplicationActivateIgnoringOtherApps
        time.sleep(2)
        
        app_name = browser_app.localizedName()
        print(f"Activated: {app_name}")
        
        # Verify it's now active
        active_app = workspace.frontmostApplication()
        if active_app:
            print(f"Current active app: {active_app.localizedName()}")
        
        # Step 3: Test accessibility
        print("3. Testing accessibility...")
        acc = AccessibilityModule()
        
        # Test searches
        test_cases = [
            ("", "Google"),
            ("", "Gmail"), 
            ("AXButton", "Google Search"),
            ("AXButton", "I'm Feeling Lucky"),
            ("AXLink", "Gmail"),
            ("", "Search")
        ]
        
        print("\nAccessibility Test Results:")
        print("-" * 50)
        
        for role, label in test_cases:
            result = acc.find_element_enhanced(role, label, None)
            status = "✅ FOUND" if result.found else "❌ NOT FOUND"
            print(f"{status} | Role: {role or 'any':12} | Label: {label:20} | Confidence: {result.confidence_score:.2f}")
            
            if result.found:
                print(f"         | Matched: {result.matched_attribute} | Search time: {result.search_time_ms:.1f}ms")
        
        # Step 4: Get accessibility status
        print(f"\n4. Accessibility Status:")
        status = acc.get_accessibility_status()
        for key, value in status.items():
            print(f"   {key}: {value}")
            
    else:
        print("No browser found!")

if __name__ == "__main__":
    test_browser_accessibility()