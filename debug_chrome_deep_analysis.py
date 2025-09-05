#!/usr/bin/env python3
"""
Deep analysis of Chrome accessibility structure to understand the real tab hierarchy.
"""

import sys
import time
import subprocess

# Add modules to path
sys.path.append('.')


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


def analyze_chrome_structure():
    """Analyze Chrome's accessibility structure in detail."""
    print("🔍 Deep Chrome Accessibility Structure Analysis")
    print("=" * 60)
    
    chrome_pid = find_chrome_process()
    if not chrome_pid:
        print("❌ Chrome not found")
        return False
    
    print(f"✅ Found Chrome PID: {chrome_pid}")
    
    print(f"\n⏰ 5 second countdown - switch to Chrome...")
    for i in range(5, 0, -1):
        print(f"⏳ {i}...", end='\r')
        time.sleep(1)
    print("🚀 Starting deep analysis!     ")
    
    try:
        from ApplicationServices import (
            AXUIElementCreateApplication,
            AXUIElementCopyAttributeValue,
            AXUIElementCopyAttributeNames,
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
        print(f"\n📊 Found {len(windows)} windows")
        
        # Find the main browser window (the one with content)
        main_window = None
        for i, window in enumerate(windows):
            title_result = AXUIElementCopyAttributeValue(window, kAXTitleAttribute, None)
            title = title_result[1] if title_result[0] == 0 else ""
            
            print(f"   Window {i+1}: '{title}'")
            
            # Look for the window with "Chrome" in the title (main browser window)
            if "Chrome" in title and "Google" in title:
                main_window = window
                print(f"     ✅ This is the main browser window")
        
        if not main_window:
            print("❌ Could not find main browser window")
            return False
        
        print(f"\n🔍 Analyzing Main Browser Window Structure:")
        
        def analyze_element(element, depth=0, max_depth=8, path=""):
            if depth > max_depth:
                return
            
            indent = "  " * depth
            
            try:
                # Get basic attributes
                role_result = AXUIElementCopyAttributeValue(element, kAXRoleAttribute, None)
                role = role_result[1] if role_result[0] == 0 else "Unknown"
                
                title_result = AXUIElementCopyAttributeValue(element, kAXTitleAttribute, None)
                title = title_result[1] if title_result[0] == 0 else ""
                
                desc_result = AXUIElementCopyAttributeValue(element, kAXDescriptionAttribute, None)
                description = desc_result[1] if desc_result[0] == 0 else ""
                
                value_result = AXUIElementCopyAttributeValue(element, kAXValueAttribute, None)
                value = value_result[1] if value_result[0] == 0 else ""
                
                # Create display text
                display_parts = []
                if title:
                    display_parts.append(f"title:'{title[:30]}'")
                if description:
                    display_parts.append(f"desc:'{description[:30]}'")
                if value:
                    display_parts.append(f"value:'{value[:30]}'")
                
                display_text = " | ".join(display_parts) if display_parts else "(no text)"
                
                # Highlight important elements
                highlight = ""
                if role in ['AXTab', 'AXTabGroup']:
                    highlight = " 🎯 TAB ELEMENT!"
                elif role == 'AXWebArea':
                    highlight = " 🌐 WEB CONTENT!"
                elif 'facebook' in (title + description + value).lower():
                    highlight = " 📘 FACEBOOK!"
                elif 'google' in (title + description + value).lower():
                    highlight = " 🔍 GOOGLE!"
                
                print(f"{indent}{role}: {display_text}{highlight}")
                
                # Get children
                children_result = AXUIElementCopyAttributeValue(element, kAXChildrenAttribute, None)
                if children_result[0] == 0 and children_result[1]:
                    children = children_result[1]
                    
                    # Only recurse into interesting elements or if we haven't found tabs yet
                    should_recurse = (
                        role in ['AXWindow', 'AXGroup', 'AXTabGroup', 'AXTab', 'AXWebArea', 'AXScrollArea'] or
                        depth < 3 or
                        highlight
                    )
                    
                    if should_recurse and len(children) < 20:  # Avoid huge lists
                        for i, child in enumerate(children):
                            child_path = f"{path}.{i}" if path else str(i)
                            analyze_element(child, depth + 1, max_depth, child_path)
                    elif len(children) >= 20:
                        print(f"{indent}  ... ({len(children)} children - too many to show)")
                
            except Exception as e:
                print(f"{indent}ERROR: {e}")
        
        # Start analysis from main window
        analyze_element(main_window)
        
        print(f"\n💡 Analysis Summary:")
        print(f"Look for the 🎯 TAB ELEMENT! markers above.")
        print(f"These show where the actual tab elements are in the hierarchy.")
        print(f"The issue might be that we're finding tab containers instead of individual tabs.")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function."""
    print("Chrome Deep Structure Analysis")
    print("This will show the complete accessibility hierarchy")
    print("to understand where the real tabs are located.")
    print()
    
    input("Press Enter to start analysis (make sure Chrome has 2 tabs open)...")
    
    success = analyze_chrome_structure()
    
    if success:
        print(f"\n✅ Analysis completed!")
    else:
        print(f"\n❌ Analysis failed!")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)