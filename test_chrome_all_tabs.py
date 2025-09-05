#!/usr/bin/env python3
"""
Enhanced Chrome accessibility test that shows ALL tabs and their elements,
not just the "active" tab, to better understand the element distribution.
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
                    chrome_processes.append({
                        'pid': pid,
                        'command': ' '.join(parts[10:]) if len(parts) > 10 else 'Chrome'
                    })
        
        return chrome_processes
    except Exception as e:
        print(f"Error finding Chrome process: {e}")
        return []


def countdown_timer(seconds: int):
    """Display a countdown timer."""
    print(f"\n⏰ You have {seconds} seconds to switch to Chrome and open a web page...")
    print("Make sure Chrome is the active application with a web page loaded.")
    print()
    
    for i in range(seconds, 0, -1):
        print(f"⏳ {i} seconds remaining...", end='\r')
        time.sleep(1)
    
    print("🚀 Starting accessibility tree extraction!     ")
    print()


def analyze_all_tabs(browser_tree):
    """Analyze all tabs and their elements, not just the active one."""
    print(f"\n🔍 Comprehensive Tab Analysis:")
    print(f"   Total tabs found: {len(browser_tree.tabs)}")
    print(f"   Total elements across all tabs: {len(browser_tree.get_all_elements())}")
    
    # Analyze each tab
    tabs_with_content = []
    for i, tab in enumerate(browser_tree.tabs):
        element_count = len(tab.elements)
        frame_count = len(tab.frames)
        total_elements = element_count + sum(len(frame.elements) for frame in tab.frames)
        
        print(f"\n   Tab {i+1}: {tab.tab_id}")
        print(f"     - Title: '{tab.title}'")
        print(f"     - URL: '{tab.url}'")
        print(f"     - Active: {tab.is_active}")
        print(f"     - Direct elements: {element_count}")
        print(f"     - Frames: {frame_count}")
        print(f"     - Total elements (including frames): {total_elements}")
        
        if total_elements > 0:
            tabs_with_content.append((tab, total_elements))
            
            # Show element roles in this tab
            all_tab_elements = tab.elements + [elem for frame in tab.frames for elem in frame.elements]
            role_counts = {}
            for element in all_tab_elements:
                role = element.role
                role_counts[role] = role_counts.get(role, 0) + 1
            
            if role_counts:
                print(f"     - Element roles: {dict(role_counts)}")
                
                # Show sample elements
                print(f"     - Sample elements:")
                for j, element in enumerate(all_tab_elements[:5]):  # Show first 5
                    title = element.title[:30] + "..." if len(element.title) > 30 else element.title
                    desc = element.description[:30] + "..." if len(element.description) > 30 else element.description
                    print(f"       {j+1}. {element.role}: '{title}' - '{desc}'")
                    if element.coordinates:
                        print(f"          Position: {element.coordinates}")
    
    # Find the tab with the most content
    if tabs_with_content:
        tabs_with_content.sort(key=lambda x: x[1], reverse=True)  # Sort by element count
        richest_tab, element_count = tabs_with_content[0]
        
        print(f"\n🎯 Tab with Most Content: {richest_tab.tab_id}")
        print(f"   - Title: '{richest_tab.title}'")
        print(f"   - URL: '{richest_tab.url}'")
        print(f"   - Total elements: {element_count}")
        print(f"   - Marked as active: {richest_tab.is_active}")
        
        # Detailed analysis of the richest tab
        all_elements = richest_tab.elements + [elem for frame in richest_tab.frames for elem in frame.elements]
        
        print(f"\n📊 Detailed Element Analysis for {richest_tab.tab_id}:")
        
        # Group by role
        role_groups = {}
        for element in all_elements:
            role = element.role
            if role not in role_groups:
                role_groups[role] = []
            role_groups[role].append(element)
        
        for role, elements in sorted(role_groups.items()):
            print(f"   {role}: {len(elements)} elements")
            
            # Show examples for each role
            for i, element in enumerate(elements[:3]):  # Show first 3 of each role
                title = element.title[:40] + "..." if len(element.title) > 40 else element.title
                desc = element.description[:40] + "..." if len(element.description) > 40 else element.description
                print(f"     {i+1}. '{title}' - '{desc}'")
                if element.value:
                    value = element.value[:30] + "..." if len(element.value) > 30 else element.value
                    print(f"        Value: '{value}'")
                if element.url:
                    print(f"        URL: {element.url}")
                if element.coordinates:
                    print(f"        Position: {element.coordinates} (center: {element.center_point})")
        
        return richest_tab
    else:
        print(f"\n⚠️  No tabs with content found")
        return None


def test_enhanced_chrome_accessibility():
    """Enhanced test that analyzes all tabs properly."""
    print("🌐 Enhanced Chrome Accessibility Tree Test")
    print("=" * 60)
    
    # Find Chrome processes
    print("1. Looking for Chrome processes...")
    chrome_processes = find_chrome_process()
    
    if not chrome_processes:
        print("❌ Chrome not found. Please open Chrome and try again.")
        return False
    
    print(f"✅ Found {len(chrome_processes)} Chrome process(es)")
    chrome_pid = chrome_processes[0]['pid']
    print(f"   Using Chrome PID: {chrome_pid}")
    
    # Start countdown timer
    countdown_timer(5)
    
    # Initialize modules
    print("2. Initializing accessibility modules...")
    app_detector = ApplicationDetector()
    browser_handler = BrowserAccessibilityHandler()
    
    # Create Chrome application info
    chrome_app = ApplicationInfo(
        name="Google Chrome",
        bundle_id="com.google.Chrome",
        process_id=chrome_pid,
        app_type=ApplicationType.WEB_BROWSER,
        browser_type=BrowserType.CHROME
    )
    
    print(f"✅ Chrome app info created")
    
    # Extract browser tree
    print("\n3. Extracting Chrome accessibility tree...")
    start_time = time.time()
    
    try:
        browser_tree = browser_handler.extract_browser_tree(chrome_app)
        extraction_time = (time.time() - start_time) * 1000
        
        if not browser_tree:
            print("❌ Failed to extract browser tree")
            return False
        
        print(f"✅ Browser tree extracted in {extraction_time:.1f}ms!")
        print(f"   - Total tabs: {len(browser_tree.tabs)}")
        print(f"   - Total elements: {len(browser_tree.get_all_elements())}")
        print(f"   - Detected active tab: {browser_tree.active_tab_id}")
        
        # Analyze ALL tabs, not just the "active" one
        richest_tab = analyze_all_tabs(browser_tree)
        
        # Test element searching on the richest tab
        if richest_tab:
            print(f"\n🔍 Element Search Test on {richest_tab.tab_id}:")
            
            all_elements = richest_tab.elements + [elem for frame in richest_tab.frames for elem in frame.elements]
            
            # Search for different element types
            buttons = [e for e in all_elements if e.role == 'AXButton']
            links = [e for e in all_elements if e.role == 'AXLink']
            text_inputs = [e for e in all_elements if e.role in ['AXTextField', 'AXTextArea']]
            static_text = [e for e in all_elements if e.role == 'AXStaticText' and e.title.strip()]
            
            print(f"   - Buttons: {len(buttons)}")
            for button in buttons[:3]:
                print(f"     • '{button.title}' - {button.description}")
            
            print(f"   - Links: {len(links)}")
            for link in links[:3]:
                print(f"     • '{link.title}' -> {link.url}")
            
            print(f"   - Text inputs: {len(text_inputs)}")
            for text_input in text_inputs[:3]:
                print(f"     • {text_input.role}: '{text_input.title}' - {text_input.description}")
            
            print(f"   - Text content: {len(static_text)}")
            for text in static_text[:3]:
                title = text.title[:50] + "..." if len(text.title) > 50 else text.title
                print(f"     • '{title}'")
        
        # Performance summary
        print(f"\n📈 Performance Summary:")
        print(f"   - Extraction time: {extraction_time:.1f}ms")
        print(f"   - Elements per second: {len(browser_tree.get_all_elements()) / (extraction_time / 1000):.0f}")
        print(f"   - Unique roles found: {len(set(e.role for e in browser_tree.get_all_elements()))}")
        print(f"   - Elements with coordinates: {sum(1 for e in browser_tree.get_all_elements() if e.coordinates)}")
        
        print(f"\n✅ Enhanced Chrome accessibility test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error during browser tree extraction: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function to run the enhanced test."""
    print("Enhanced Chrome Accessibility Tree Test")
    print("This test analyzes ALL tabs and their elements,")
    print("not just the 'active' tab, to show the full picture.")
    print()
    
    # Check if Chrome is running
    chrome_processes = find_chrome_process()
    if not chrome_processes:
        print("❌ Chrome is not running. Please open Chrome first.")
        return False
    
    print("Instructions:")
    print("1. Make sure Chrome is open with multiple tabs/web pages")
    print("2. When the countdown starts, switch to Chrome")
    print("3. The test will analyze ALL tabs and show which ones have content")
    print()
    
    input("Press Enter when ready to start the test...")
    
    success = test_enhanced_chrome_accessibility()
    
    if success:
        print(f"\n🎉 Test completed successfully!")
        print(f"This shows the real distribution of elements across all Chrome tabs.")
    else:
        print(f"\n❌ Test failed!")
        print(f"Check accessibility permissions and Chrome setup.")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)