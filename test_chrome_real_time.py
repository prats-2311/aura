#!/usr/bin/env python3
"""
Real-time Chrome accessibility tree test with timer.
This test gives you 5 seconds to switch to Chrome, then attempts to extract
the current tab's web content and display all elements and their roles.
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


def test_real_chrome_accessibility():
    """Test real Chrome accessibility tree extraction."""
    print("🌐 Real-Time Chrome Accessibility Tree Test")
    print("=" * 60)
    
    # Find Chrome processes
    print("1. Looking for Chrome processes...")
    chrome_processes = find_chrome_process()
    
    if not chrome_processes:
        print("❌ Chrome not found. Please open Chrome and try again.")
        return False
    
    print(f"✅ Found {len(chrome_processes)} Chrome process(es):")
    for i, proc in enumerate(chrome_processes):
        print(f"   {i+1}. PID {proc['pid']}: {proc['command'][:60]}...")
    
    # Use the first Chrome process
    chrome_pid = chrome_processes[0]['pid']
    print(f"\n2. Using Chrome PID: {chrome_pid}")
    
    # Start countdown timer
    countdown_timer(5)
    
    # Initialize modules
    print("3. Initializing accessibility modules...")
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
    
    print(f"✅ Chrome app info created: {chrome_app.name} (PID: {chrome_app.process_id})")
    
    # Get detection strategy
    print("\n4. Getting Chrome detection strategy...")
    strategy = app_detector.get_detection_strategy(chrome_app)
    print(f"✅ Strategy configured:")
    print(f"   - Timeout: {strategy.timeout_ms}ms")
    print(f"   - Max depth: {strategy.max_depth}")
    print(f"   - Fuzzy threshold: {strategy.fuzzy_threshold}")
    print(f"   - Handle frames: {strategy.handle_frames}")
    print(f"   - Handle tabs: {strategy.handle_tabs}")
    
    # Attempt to extract browser tree
    print("\n5. Extracting Chrome accessibility tree...")
    start_time = time.time()
    
    try:
        browser_tree = browser_handler.extract_browser_tree(chrome_app)
        extraction_time = (time.time() - start_time) * 1000
        
        if not browser_tree:
            print("❌ Failed to extract browser tree")
            print("This could be due to:")
            print("   - Accessibility permissions not granted")
            print("   - Chrome not in focus")
            print("   - No accessible content available")
            return False
        
        print(f"✅ Browser tree extracted in {extraction_time:.1f}ms!")
        print(f"   - Browser type: {browser_tree.browser_type.value}")
        print(f"   - App name: {browser_tree.app_name}")
        print(f"   - Process ID: {browser_tree.process_id}")
        print(f"   - Number of tabs: {len(browser_tree.tabs)}")
        print(f"   - Active tab ID: {browser_tree.active_tab_id}")
        print(f"   - Total elements: {len(browser_tree.get_all_elements())}")
        
        # Display detailed tab information
        print("\n6. Tab Information:")
        if browser_tree.tabs:
            for i, tab in enumerate(browser_tree.tabs):
                print(f"   Tab {i+1}: {tab.tab_id}")
                print(f"     - Title: {tab.title}")
                print(f"     - URL: {tab.url}")
                print(f"     - Active: {tab.is_active}")
                print(f"     - Elements: {len(tab.elements)}")
                print(f"     - Frames: {len(tab.frames)}")
        else:
            print("   ⚠️  No tabs found")
        
        # Get active tab and analyze elements
        active_tab = browser_tree.get_active_tab()
        if active_tab:
            print(f"\n7. Active Tab Analysis: {active_tab.tab_id}")
            print(f"   - Title: {active_tab.title}")
            print(f"   - URL: {active_tab.url}")
            print(f"   - Elements found: {len(active_tab.elements)}")
            
            if active_tab.elements:
                # Analyze elements by role
                print(f"\n8. Element Role Analysis:")
                role_counts = {}
                role_examples = {}
                
                for element in active_tab.elements:
                    role = element.role
                    role_counts[role] = role_counts.get(role, 0) + 1
                    
                    # Keep first example of each role
                    if role not in role_examples:
                        role_examples[role] = element
                
                print(f"   Found {len(active_tab.elements)} elements across {len(role_counts)} different roles:")
                
                for role, count in sorted(role_counts.items()):
                    example = role_examples[role]
                    print(f"   - {role}: {count} elements")
                    title = example.title[:40] + "..." if len(example.title) > 40 else example.title
                    desc = example.description[:40] + "..." if len(example.description) > 40 else example.description
                    print(f"     Example: '{title}' - '{desc}'")
                    if example.coordinates:
                        print(f"     Position: {example.coordinates}")
                
                # Show detailed element information
                print(f"\n9. Detailed Element Information (first 15 elements):")
                for i, element in enumerate(active_tab.elements[:15]):
                    print(f"   Element {i+1}:")
                    print(f"     - Role: {element.role}")
                    print(f"     - Title: '{element.title}'")
                    print(f"     - Description: '{element.description}'")
                    if element.value:
                        print(f"     - Value: '{element.value}'")
                    if element.url:
                        print(f"     - URL: {element.url}")
                    if element.coordinates:
                        print(f"     - Coordinates: {element.coordinates} (center: {element.center_point})")
                    print()
                
                if len(active_tab.elements) > 15:
                    print(f"   ... and {len(active_tab.elements) - 15} more elements")
                
                # Test element searching
                print(f"\n10. Element Search Testing:")
                
                # Search for buttons
                button_elements = [e for e in active_tab.elements if e.role == 'AXButton']
                print(f"   - Buttons found: {len(button_elements)}")
                for button in button_elements[:5]:  # Show first 5
                    print(f"     • '{button.title}' - {button.description}")
                
                # Search for links
                link_elements = [e for e in active_tab.elements if e.role == 'AXLink']
                print(f"   - Links found: {len(link_elements)}")
                for link in link_elements[:5]:  # Show first 5
                    print(f"     • '{link.title}' -> {link.url}")
                
                # Search for text inputs
                text_elements = [e for e in active_tab.elements if e.role in ['AXTextField', 'AXTextArea']]
                print(f"   - Text inputs found: {len(text_elements)}")
                for text_elem in text_elements[:3]:  # Show first 3
                    print(f"     • {text_elem.role}: '{text_elem.title}' - {text_elem.description}")
                
                # Search for static text
                static_text = [e for e in active_tab.elements if e.role == 'AXStaticText' and e.title.strip()]
                print(f"   - Text content found: {len(static_text)}")
                for text_elem in static_text[:3]:  # Show first 3
                    title = text_elem.title[:50] + "..." if len(text_elem.title) > 50 else text_elem.title
                    print(f"     • '{title}'")
                
            else:
                print("   ⚠️  No elements found in active tab")
        
        # Display frame information
        if any(tab.frames for tab in browser_tree.tabs):
            print(f"\n11. Frame Information:")
            for tab in browser_tree.tabs:
                if tab.frames:
                    print(f"   Tab {tab.tab_id} has {len(tab.frames)} frames:")
                    for frame in tab.frames:
                        print(f"     - Frame: {frame.frame_id}")
                        print(f"       URL: {frame.url}")
                        print(f"       Title: {frame.title}")
                        print(f"       Elements: {len(frame.elements)}")
                        
                        # Show frame elements
                        for elem in frame.elements[:3]:  # Show first 3
                            print(f"         • {elem.role}: '{elem.title}'")
        
        # Test search parameter adaptation
        print(f"\n12. Search Parameter Adaptation Test:")
        test_commands = [
            "Click on search button",
            "Type hello in text field",
            "Click on submit link"
        ]
        
        for command in test_commands:
            params = app_detector.adapt_search_parameters(chrome_app, command)
            print(f"   Command: '{command}'")
            print(f"   - Priority roles: {params.roles[:3]}")
            print(f"   - Timeout: {params.timeout_ms}ms")
            print(f"   - Search frames: {params.search_frames}")
            print(f"   - Web content only: {params.web_content_only}")
        
        # Performance summary
        print(f"\n13. Performance Summary:")
        print(f"   - Extraction time: {extraction_time:.1f}ms")
        print(f"   - Elements per second: {len(browser_tree.get_all_elements()) / (extraction_time / 1000):.0f}")
        print(f"   - Roles identified: {len(set(e.role for e in browser_tree.get_all_elements()))}")
        print(f"   - Elements with coordinates: {sum(1 for e in browser_tree.get_all_elements() if e.coordinates)}")
        
        print(f"\n✅ Real-time Chrome accessibility tree test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error during browser tree extraction: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function to run the real-time test."""
    print("Real-Time Chrome Accessibility Tree Test")
    print("This test will give you 5 seconds to switch to Chrome,")
    print("then attempt to extract the current tab's web content.")
    print()
    
    # Check if Chrome is running
    chrome_processes = find_chrome_process()
    if not chrome_processes:
        print("❌ Chrome is not running. Please open Chrome first.")
        return False
    
    print("Instructions:")
    print("1. Make sure Chrome is open with a web page loaded")
    print("2. When the countdown starts, switch to Chrome")
    print("3. Make sure Chrome is the active/focused application")
    print("4. The test will then extract the accessibility tree")
    print()
    
    input("Press Enter when ready to start the test...")
    
    success = test_real_chrome_accessibility()
    
    if success:
        print(f"\n🎉 Test completed successfully!")
        print(f"The accessibility tree was extracted and analyzed.")
    else:
        print(f"\n❌ Test failed!")
        print(f"This could be due to accessibility permissions or Chrome not being active.")
        print(f"Try granting accessibility permissions to Terminal in:")
        print(f"System Preferences > Security & Privacy > Privacy > Accessibility")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)