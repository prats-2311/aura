#!/usr/bin/env python3
"""
Test Chrome accessibility focusing on web content rather than tab structure.
This approach looks for actual web page content instead of trying to parse Chrome's UI.
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
        
        for line in lines:
            if 'Google Chrome' in line and 'Helper' not in line and 'Renderer' not in line:
                parts = line.split()
                if len(parts) > 1:
                    return int(parts[1])
        return None
    except Exception as e:
        print(f"Error finding Chrome process: {e}")
        return None


def find_web_content_directly():
    """Find web content directly without relying on tab structure."""
    print("🌐 Direct Web Content Detection Test")
    print("=" * 50)
    
    chrome_pid = find_chrome_process()
    if not chrome_pid:
        print("❌ Chrome not found")
        return False
    
    print(f"✅ Found Chrome PID: {chrome_pid}")
    
    print(f"\n⏰ 5 second countdown - switch to Chrome...")
    for i in range(5, 0, -1):
        print(f"⏳ {i}...", end='\r')
        time.sleep(1)
    print("🚀 Looking for web content!     ")
    
    try:
        from ApplicationServices import (
            AXUIElementCreateApplication,
            AXUIElementCopyAttributeValue,
            kAXWindowsAttribute,
            kAXTitleAttribute,
            kAXRoleAttribute,
            kAXChildrenAttribute,
            kAXDescriptionAttribute,
            kAXValueAttribute
        )
        
        # Create app element
        app_element = AXUIElementCreateApplication(chrome_pid)
        if not app_element:
            print("❌ Failed to create app element")
            return False
        
        # Get windows
        windows_result = AXUIElementCopyAttributeValue(app_element, kAXWindowsAttribute, None)
        if windows_result[0] != 0:
            print("❌ Failed to get windows")
            return False
        
        windows = windows_result[1]
        
        # Find main browser window
        main_window = None
        for window in windows:
            title_result = AXUIElementCopyAttributeValue(window, kAXTitleAttribute, None)
            title = title_result[1] if title_result[0] == 0 else ""
            
            if "Chrome" in title:
                main_window = window
                break
        
        if not main_window:
            print("❌ Could not find main browser window")
            return False
        
        print(f"\n🔍 Searching for web content areas...")
        
        # Look for web content areas (AXWebArea) which represent actual web pages
        web_areas = []
        
        def find_web_areas(element, depth=0, max_depth=10):
            if depth > max_depth:
                return
            
            try:
                role_result = AXUIElementCopyAttributeValue(element, kAXRoleAttribute, None)
                role = role_result[1] if role_result[0] == 0 else ""
                
                if role == 'AXWebArea':
                    # This is a web content area - get its details
                    title_result = AXUIElementCopyAttributeValue(element, kAXTitleAttribute, None)
                    title = title_result[1] if title_result[0] == 0 else ""
                    
                    desc_result = AXUIElementCopyAttributeValue(element, kAXDescriptionAttribute, None)
                    description = desc_result[1] if desc_result[0] == 0 else ""
                    
                    web_areas.append({
                        'element': element,
                        'title': title,
                        'description': description,
                        'depth': depth
                    })
                    
                    print(f"   Found AXWebArea: '{title}' (depth {depth})")
                
                # Continue searching in children
                children_result = AXUIElementCopyAttributeValue(element, kAXChildrenAttribute, None)
                if children_result[0] == 0 and children_result[1]:
                    children = children_result[1]
                    if len(children) < 50:  # Avoid huge lists
                        for child in children:
                            find_web_areas(child, depth + 1, max_depth)
                            
            except Exception as e:
                pass
        
        # Search for web areas
        find_web_areas(main_window)
        
        print(f"\n📊 Web Content Analysis:")
        print(f"   Found {len(web_areas)} web content areas")
        
        if not web_areas:
            print("   ❌ No web content areas found")
            return False
        
        # Analyze each web area
        for i, web_area in enumerate(web_areas):
            print(f"\n   Web Area {i+1}:")
            print(f"     Title: '{web_area['title']}'")
            print(f"     Description: '{web_area['description']}'")
            print(f"     Depth: {web_area['depth']}")
            
            # Look for interactive elements in this web area
            interactive_elements = []
            
            def find_interactive_elements(element, depth=0, max_depth=5):
                if depth > max_depth:
                    return
                
                try:
                    role_result = AXUIElementCopyAttributeValue(element, kAXRoleAttribute, None)
                    role = role_result[1] if role_result[0] == 0 else ""
                    
                    # Look for interactive web elements
                    if role in ['AXButton', 'AXLink', 'AXTextField', 'AXTextArea', 'AXStaticText']:
                        title_result = AXUIElementCopyAttributeValue(element, kAXTitleAttribute, None)
                        title = title_result[1] if title_result[0] == 0 else ""
                        
                        value_result = AXUIElementCopyAttributeValue(element, kAXValueAttribute, None)
                        value = value_result[1] if value_result[0] == 0 else ""
                        
                        desc_result = AXUIElementCopyAttributeValue(element, kAXDescriptionAttribute, None)
                        description = desc_result[1] if desc_result[0] == 0 else ""
                        
                        if title or value or description:  # Only include elements with content
                            interactive_elements.append({
                                'role': role,
                                'title': title,
                                'value': value,
                                'description': description
                            })
                    
                    # Continue searching
                    children_result = AXUIElementCopyAttributeValue(element, kAXChildrenAttribute, None)
                    if children_result[0] == 0 and children_result[1]:
                        children = children_result[1]
                        if len(children) < 30:  # Limit to avoid huge lists
                            for child in children:
                                find_interactive_elements(child, depth + 1, max_depth)
                                
                except Exception as e:
                    pass
            
            # Search for interactive elements in this web area
            find_interactive_elements(web_area['element'])
            
            print(f"     Interactive elements: {len(interactive_elements)}")
            
            if interactive_elements:
                # Group by role
                role_counts = {}
                for elem in interactive_elements:
                    role = elem['role']
                    role_counts[role] = role_counts.get(role, 0) + 1
                
                print(f"     Element types: {dict(role_counts)}")
                
                # Show sample elements
                print(f"     Sample elements:")
                for j, elem in enumerate(interactive_elements[:5]):
                    content = elem['title'] or elem['value'] or elem['description'] or "(no text)"
                    content = content[:40] + "..." if len(content) > 40 else content
                    print(f"       {j+1}. {elem['role']}: '{content}'")
                
                # Look for Facebook or Google specific content
                facebook_elements = [e for e in interactive_elements 
                                   if 'facebook' in (e['title'] + e['value'] + e['description']).lower()]
                google_elements = [e for e in interactive_elements 
                                 if 'google' in (e['title'] + e['value'] + e['description']).lower()]
                
                if facebook_elements:
                    print(f"     🎯 Facebook elements: {len(facebook_elements)}")
                    for elem in facebook_elements[:3]:
                        content = elem['title'] or elem['value'] or elem['description']
                        print(f"       📘 {elem['role']}: '{content[:30]}...'")
                
                if google_elements:
                    print(f"     🎯 Google elements: {len(google_elements)}")
                    for elem in google_elements[:3]:
                        content = elem['title'] or elem['value'] or elem['description']
                        print(f"       🔍 {elem['role']}: '{content[:30]}...'")
        
        print(f"\n✅ Web Content Detection Summary:")
        print(f"   - Found {len(web_areas)} distinct web content areas")
        print(f"   - This likely represents {len(web_areas)} actual browser tabs")
        print(f"   - Each web area contains the content of one web page")
        print(f"   - This is more accurate than trying to parse Chrome's tab UI")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during web content detection: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function."""
    print("Chrome Web Content Focus Test")
    print("This approach looks for actual web page content (AXWebArea)")
    print("instead of trying to parse Chrome's complex tab UI structure.")
    print()
    
    input("Press Enter to start test (make sure Chrome has 2 tabs: Google + Facebook)...")
    
    success = find_web_content_directly()
    
    if success:
        print(f"\n🎉 Test completed!")
        print(f"This approach focuses on actual web content rather than UI structure.")
    else:
        print(f"\n❌ Test failed!")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)