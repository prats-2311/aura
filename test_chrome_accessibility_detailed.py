#!/usr/bin/env python3
"""
Detailed test script to diagnose Chrome accessibility tree extraction.
"""

import sys
import time
import subprocess
from typing import Dict, Any, List, Optional

# Add modules to path
sys.path.append('.')

from modules.application_detector import ApplicationDetector, ApplicationInfo, ApplicationType, BrowserType
from modules.browser_accessibility import BrowserAccessibilityHandler


def check_accessibility_permissions():
    """Check if accessibility permissions are granted."""
    try:
        # Try to import and use accessibility functions
        from ApplicationServices import (
            AXUIElementCreateSystemWide,
            AXUIElementCopyAttributeValue,
            kAXFocusedApplicationAttribute
        )
        
        # Try to get the focused application
        system_element = AXUIElementCreateSystemWide()
        if system_element:
            focused_app = AXUIElementCopyAttributeValue(system_element, kAXFocusedApplicationAttribute, None)
            if focused_app[0] == 0:  # Success
                print("✅ Accessibility permissions are working")
                return True
        
        print("⚠️  Accessibility permissions may not be granted")
        return False
        
    except Exception as e:
        print(f"❌ Accessibility functions not available: {e}")
        return False


def get_running_applications():
    """Get list of running applications."""
    try:
        from AppKit import NSWorkspace
        workspace = NSWorkspace.sharedWorkspace()
        running_apps = workspace.runningApplications()
        
        apps = []
        for app in running_apps:
            app_info = {
                'name': app.localizedName(),
                'bundle_id': app.bundleIdentifier(),
                'pid': app.processIdentifier(),
                'active': app.isActive()
            }
            apps.append(app_info)
        
        return apps
    except Exception as e:
        print(f"Error getting running applications: {e}")
        return []


def test_accessibility_element_creation(pid: int):
    """Test creating accessibility element for a specific PID."""
    try:
        from ApplicationServices import (
            AXUIElementCreateApplication,
            AXUIElementCopyAttributeValue,
            AXUIElementCopyAttributeNames,
            kAXWindowsAttribute,
            kAXTitleAttribute,
            kAXChildrenAttribute
        )
        
        print(f"Creating accessibility element for PID {pid}...")
        app_element = AXUIElementCreateApplication(pid)
        
        if not app_element:
            print("❌ Failed to create accessibility element")
            return None
        
        print("✅ Accessibility element created")
        
        # Try to get available attributes
        print("Getting available attributes...")
        try:
            attributes = AXUIElementCopyAttributeNames(app_element, None)[1]
            print(f"✅ Available attributes: {list(attributes)}")
        except Exception as e:
            print(f"⚠️  Could not get attributes: {e}")
        
        # Try to get windows
        print("Getting windows...")
        try:
            windows_result = AXUIElementCopyAttributeValue(app_element, kAXWindowsAttribute, None)
            if windows_result[0] == 0:  # Success
                windows = windows_result[1]
                print(f"✅ Found {len(windows) if windows else 0} windows")
                
                if windows:
                    for i, window in enumerate(windows):
                        try:
                            title_result = AXUIElementCopyAttributeValue(window, kAXTitleAttribute, None)
                            title = title_result[1] if title_result[0] == 0 else "Unknown"
                            print(f"   Window {i+1}: {title}")
                            
                            # Try to get children of first window
                            if i == 0:
                                children_result = AXUIElementCopyAttributeValue(window, kAXChildrenAttribute, None)
                                if children_result[0] == 0:
                                    children = children_result[1]
                                    print(f"     Children: {len(children) if children else 0}")
                                    
                                    if children:
                                        # Show first few children
                                        for j, child in enumerate(children[:5]):
                                            try:
                                                child_attrs = AXUIElementCopyAttributeNames(child, None)[1]
                                                print(f"       Child {j+1} attributes: {len(child_attrs) if child_attrs else 0}")
                                            except:
                                                print(f"       Child {j+1}: Could not get attributes")
                                
                        except Exception as e:
                            print(f"   Window {i+1}: Error getting details - {e}")
                
                return app_element
            else:
                print(f"❌ Failed to get windows (error code: {windows_result[0]})")
                return app_element
                
        except Exception as e:
            print(f"❌ Error getting windows: {e}")
            return app_element
            
    except Exception as e:
        print(f"❌ Error creating accessibility element: {e}")
        return None


def main():
    """Main function to run detailed Chrome accessibility test."""
    print("🔍 Detailed Chrome Accessibility Diagnostics")
    print("=" * 60)
    
    # Check accessibility permissions
    print("1. Checking accessibility permissions...")
    has_permissions = check_accessibility_permissions()
    
    if not has_permissions:
        print("\n❌ Accessibility permissions not available!")
        print("Please grant accessibility permissions to Terminal/Python in:")
        print("System Preferences > Security & Privacy > Privacy > Accessibility")
        return False
    
    # Get running applications
    print("\n2. Getting running applications...")
    apps = get_running_applications()
    
    chrome_apps = [app for app in apps if 'chrome' in app['name'].lower()]
    
    if not chrome_apps:
        print("❌ Chrome not found in running applications")
        print("Available applications:")
        for app in apps[:10]:  # Show first 10
            print(f"   - {app['name']} (PID: {app['pid']})")
        return False
    
    print(f"✅ Found {len(chrome_apps)} Chrome-related applications:")
    for app in chrome_apps:
        print(f"   - {app['name']} (PID: {app['pid']}, Active: {app['active']})")
    
    # Use the main Chrome process (not helpers)
    main_chrome = None
    for app in chrome_apps:
        if 'helper' not in app['name'].lower() and 'renderer' not in app['name'].lower():
            main_chrome = app
            break
    
    if not main_chrome:
        print("❌ Could not find main Chrome process")
        return False
    
    print(f"\n3. Using Chrome process: {main_chrome['name']} (PID: {main_chrome['pid']})")
    
    # Test accessibility element creation
    print("\n4. Testing accessibility element creation...")
    app_element = test_accessibility_element_creation(main_chrome['pid'])
    
    if not app_element:
        print("❌ Failed to create accessibility element")
        return False
    
    # Test with our modules
    print("\n5. Testing with our modules...")
    
    # Initialize detectors
    app_detector = ApplicationDetector()
    browser_handler = BrowserAccessibilityHandler()
    
    # Create Chrome application info
    chrome_app = ApplicationInfo(
        name=main_chrome['name'],
        bundle_id=main_chrome['bundle_id'],
        process_id=main_chrome['pid'],
        app_type=ApplicationType.WEB_BROWSER,
        browser_type=BrowserType.CHROME
    )
    
    print(f"Chrome app info: {chrome_app.to_dict()}")
    
    # Test browser tree extraction with detailed logging
    print("\n6. Extracting browser tree with detailed logging...")
    
    # Enable debug logging
    import logging
    logging.basicConfig(level=logging.DEBUG)
    
    try:
        browser_tree = browser_handler.extract_browser_tree(chrome_app)
        
        if browser_tree:
            print(f"✅ Browser tree extracted!")
            print(f"   - Tabs: {len(browser_tree.tabs)}")
            print(f"   - Elements: {len(browser_tree.get_all_elements())}")
            
            if browser_tree.tabs:
                for i, tab in enumerate(browser_tree.tabs):
                    print(f"   Tab {i+1}: {tab.title} ({len(tab.elements)} elements)")
            
            # Test element finding
            print("\n7. Testing element finding...")
            all_elements = browser_tree.get_all_elements()
            
            if all_elements:
                print(f"Found {len(all_elements)} total elements:")
                
                # Group by role
                role_counts = {}
                for element in all_elements:
                    role = element.role
                    role_counts[role] = role_counts.get(role, 0) + 1
                
                for role, count in sorted(role_counts.items()):
                    print(f"   - {role}: {count}")
                
                # Show sample elements
                print("\nSample elements:")
                for i, element in enumerate(all_elements[:10]):
                    print(f"   {i+1}. {element.role}: '{element.title}' - '{element.description}'")
            
            else:
                print("⚠️  No elements found")
        
        else:
            print("❌ Failed to extract browser tree")
            return False
    
    except Exception as e:
        print(f"❌ Error during browser tree extraction: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n✅ Detailed Chrome accessibility test completed!")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)