#!/usr/bin/env python3
"""
Debug Chrome tab detection to understand why it's finding 11 tabs instead of 2.
"""

import sys
import time
import subprocess
from typing import Dict, Any, List, Optional

# Add modules to path
sys.path.append('.')

from modules.application_detector import ApplicationDetector, ApplicationInfo, ApplicationType, BrowserType
from modules.browser_accessibility import BrowserAccessibilityHandler


def find_chrome_process():
    """Find Chrome process information."""
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        lines = result.stdout.split('\n')
        
        chrome_processes = []
        for line in lines:
            if 'Google Chrome' in line and 'Helper' not in line and 'Renderer' not in line:
                parts = line.split()
                if len(parts) > 1:
                    pid = int(parts[1])
                    chrome_processes.append({'pid': pid})
        
        return chrome_processes
    except Exception as e:
        print(f"Error finding Chrome process: {e}")
        return []


def debug_tab_detection():
    """Debug the tab detection process step by step."""
    print("🔍 Debug Chrome Tab Detection")
    print("=" * 50)
    
    # Find Chrome
    chrome_processes = find_chrome_process()
    if not chrome_processes:
        print("❌ Chrome not found")
        return False
    
    chrome_pid = chrome_processes[0]['pid']
    print(f"✅ Found Chrome PID: {chrome_pid}")
    
    # Initialize handler
    browser_handler = BrowserAccessibilityHandler()
    
    # Get Chrome config
    chrome_config = browser_handler.get_browser_config(BrowserType.CHROME)
    print(f"\n📋 Chrome Tab Indicators: {chrome_config['tab_indicators']}")
    
    # Create app info
    chrome_app = ApplicationInfo(
        name="Google Chrome",
        bundle_id="com.google.Chrome",
        process_id=chrome_pid,
        app_type=ApplicationType.WEB_BROWSER,
        browser_type=BrowserType.CHROME
    )
    
    print(f"\n⏰ 5 second countdown - switch to Chrome...")
    for i in range(5, 0, -1):
        print(f"⏳ {i}...", end='\r')
        time.sleep(1)
    print("🚀 Starting debug!     ")
    
    try:
        # Try to access Chrome accessibility directly
        from ApplicationServices import (
            AXUIElementCreateApplication,
            AXUIElementCopyAttributeValue,
            kAXWindowsAttribute,
            kAXTitleAttribute,
            kAXRoleAttribute,
            kAXChildrenAttribute
        )
        
        print(f"\n1. Creating accessibility element...")
        app_element = AXUIElementCreateApplication(chrome_pid)
        if not app_element:
            print("❌ Failed to create app element")
            return False
        
        print(f"✅ App element created")
        
        # Get windows
        print(f"\n2. Getting windows...")
        windows_result = AXUIElementCopyAttributeValue(app_element, kAXWindowsAttribute, None)
        if windows_result[0] != 0:
            print(f"❌ Failed to get windows")
            return False
        
        windows = windows_result[1]
        print(f"✅ Found {len(windows)} windows")
        
        # Analyze each window
        for i, window in enumerate(windows):
            print(f"\n3. Analyzing Window {i+1}:")
            
            # Get window title
            title_result = AXUIElementCopyAttributeValue(window, kAXTitleAttribute, None)
            title = title_result[1] if title_result[0] == 0 else "Unknown"
            print(f"   Title: '{title}'")
            
            # Get window children
            children_result = AXUIElementCopyAttributeValue(window, kAXChildrenAttribute, None)
            if children_result[0] != 0:
                print(f"   ❌ No children found")
                continue
            
            children = children_result[1]
            print(f"   Children: {len(children)}")
            
            # Look for tab indicators in this window
            print(f"\n4. Searching for tab indicators in Window {i+1}:")
            tab_candidates = []
            
            def search_for_tabs(element, depth=0, max_depth=5):
                if depth > max_depth:
                    return
                
                try:
                    # Get role
                    role_result = AXUIElementCopyAttributeValue(element, kAXRoleAttribute, None)
                    if role_result[0] != 0:
                        return
                    
                    role = role_result[1]
                    
                    # Check if this is a tab indicator
                    if role in chrome_config['tab_indicators']:
                        # Get title
                        title_result = AXUIElementCopyAttributeValue(element, kAXTitleAttribute, None)
                        title = title_result[1] if title_result[0] == 0 else ""
                        
                        tab_candidates.append({
                            'role': role,
                            'title': title,
                            'depth': depth
                        })
                        
                        print(f"     Found {role}: '{title}' (depth {depth})")
                    
                    # Search children
                    children_result = AXUIElementCopyAttributeValue(element, kAXChildrenAttribute, None)
                    if children_result[0] == 0 and children_result[1]:
                        for child in children_result[1]:
                            search_for_tabs(child, depth + 1, max_depth)
                            
                except Exception as e:
                    pass  # Skip elements that can't be accessed
            
            # Search this window
            search_for_tabs(window)
            
            print(f"   Total tab candidates found: {len(tab_candidates)}")
            
            # Analyze the candidates
            if tab_candidates:
                print(f"\n5. Tab Candidate Analysis for Window {i+1}:")
                
                role_counts = {}
                for candidate in tab_candidates:
                    role = candidate['role']
                    role_counts[role] = role_counts.get(role, 0) + 1
                
                for role, count in role_counts.items():
                    print(f"   - {role}: {count} candidates")
                    
                    # Show examples
                    examples = [c for c in tab_candidates if c['role'] == role]
                    for j, example in enumerate(examples[:5]):  # Show first 5
                        print(f"     {j+1}. '{example['title']}' (depth {example['depth']})")
        
        print(f"\n🔍 Analysis Summary:")
        print(f"The issue is likely that 'AXButton' in tab_indicators is matching")
        print(f"browser UI buttons (Close, New Tab, etc.) instead of actual tabs.")
        print(f"")
        print(f"Expected: Only 2 actual tabs (Google, Facebook)")
        print(f"Found: Multiple buttons being treated as tabs")
        print(f"")
        print(f"Solution: Remove 'AXButton' from tab_indicators or add better filtering")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during debug: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function."""
    print("Chrome Tab Detection Debug")
    print("This will help identify why 11 tabs are detected instead of 2")
    print()
    
    input("Press Enter to start debug (make sure Chrome is open)...")
    
    success = debug_tab_detection()
    
    if success:
        print(f"\n✅ Debug completed!")
    else:
        print(f"\n❌ Debug failed!")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)