#!/usr/bin/env python3
"""
Test script to open Chrome, fetch current tab web content into accessibility tree,
and display the results to verify element detection and role identification.
"""

import sys
import time
import json
from typing import Dict, Any, List

# Add modules to path
sys.path.append('.')

from modules.application_detector import ApplicationDetector, ApplicationInfo, ApplicationType, BrowserType
from modules.browser_accessibility import BrowserAccessibilityHandler, WebElement, BrowserTab


def find_chrome_process():
    """Find Chrome process information."""
    try:
        import subprocess
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        lines = result.stdout.split('\n')
        
        for line in lines:
            if 'Google Chrome' in line and 'Helper' not in line:
                parts = line.split()
                if len(parts) > 1:
                    pid = int(parts[1])
                    return pid
        return None
    except Exception as e:
        print(f"Error finding Chrome process: {e}")
        return None


def test_chrome_accessibility_tree():
    """Test Chrome accessibility tree extraction and display results."""
    print("🔍 Testing Chrome Accessibility Tree Extraction")
    print("=" * 60)
    
    # Initialize detectors
    app_detector = ApplicationDetector()
    browser_handler = BrowserAccessibilityHandler()
    
    # Find Chrome process
    print("1. Looking for Chrome process...")
    chrome_pid = find_chrome_process()
    
    if not chrome_pid:
        print("❌ Chrome not found. Please open Chrome and try again.")
        return False
    
    print(f"✅ Found Chrome process: PID {chrome_pid}")
    
    # Create Chrome application info
    chrome_app = ApplicationInfo(
        name="Google Chrome",
        bundle_id="com.google.Chrome",
        process_id=chrome_pid,
        app_type=ApplicationType.WEB_BROWSER,
        browser_type=BrowserType.CHROME
    )
    
    print(f"2. Chrome application info: {chrome_app.to_dict()}")
    
    # Get detection strategy
    print("\n3. Getting Chrome detection strategy...")
    strategy = app_detector.get_detection_strategy(chrome_app)
    print(f"✅ Strategy: {strategy.app_type.value}")
    print(f"   - Timeout: {strategy.timeout_ms}ms")
    print(f"   - Max depth: {strategy.max_depth}")
    print(f"   - Fuzzy threshold: {strategy.fuzzy_threshold}")
    print(f"   - Handle frames: {strategy.handle_frames}")
    print(f"   - Handle tabs: {strategy.handle_tabs}")
    print(f"   - Web content detection: {strategy.web_content_detection}")
    
    # Get browser configuration
    print("\n4. Getting Chrome browser configuration...")
    browser_config = browser_handler.get_browser_config(BrowserType.CHROME)
    print(f"✅ Browser config loaded:")
    print(f"   - Web content roles: {browser_config['web_content_roles'][:5]}... ({len(browser_config['web_content_roles'])} total)")
    print(f"   - Navigation roles: {browser_config['navigation_roles']}")
    print(f"   - Frame indicators: {browser_config['frame_indicators']}")
    print(f"   - Tab indicators: {browser_config['tab_indicators']}")
    
    # Extract browser accessibility tree
    print("\n5. Extracting Chrome accessibility tree...")
    try:
        browser_tree = browser_handler.extract_browser_tree(chrome_app)
        
        if not browser_tree:
            print("❌ Failed to extract browser tree")
            return False
        
        print(f"✅ Browser tree extracted successfully!")
        print(f"   - Browser type: {browser_tree.browser_type.value}")
        print(f"   - App name: {browser_tree.app_name}")
        print(f"   - Process ID: {browser_tree.process_id}")
        print(f"   - Number of tabs: {len(browser_tree.tabs)}")
        print(f"   - Active tab ID: {browser_tree.active_tab_id}")
        print(f"   - Total elements: {len(browser_tree.get_all_elements())}")
        
        # Display tab information
        print("\n6. Tab Information:")
        for i, tab in enumerate(browser_tree.tabs):
            print(f"   Tab {i+1}: {tab.tab_id}")
            print(f"     - Title: {tab.title}")
            print(f"     - URL: {tab.url}")
            print(f"     - Active: {tab.is_active}")
            print(f"     - Elements: {len(tab.elements)}")
            print(f"     - Frames: {len(tab.frames)}")
        
        # Get active tab
        active_tab = browser_tree.get_active_tab()
        if active_tab:
            print(f"\n7. Active Tab Details: {active_tab.tab_id}")
            print(f"   - Title: {active_tab.title}")
            print(f"   - URL: {active_tab.url}")
            print(f"   - Elements found: {len(active_tab.elements)}")
            
            # Display element details
            if active_tab.elements:
                print("\n8. Web Elements Found:")
                role_counts = {}
                
                for i, element in enumerate(active_tab.elements[:20]):  # Show first 20 elements
                    role = element.role
                    role_counts[role] = role_counts.get(role, 0) + 1
                    
                    print(f"   Element {i+1}:")
                    print(f"     - Role: {role}")
                    print(f"     - Title: '{element.title[:50]}{'...' if len(element.title) > 50 else ''}'")
                    print(f"     - Description: '{element.description[:50]}{'...' if len(element.description) > 50 else ''}'")
                    print(f"     - Value: '{element.value[:30]}{'...' if len(element.value) > 30 else ''}'")
                    if element.coordinates:
                        print(f"     - Coordinates: {element.coordinates}")
                    if element.url:
                        print(f"     - URL: {element.url}")
                    print()
                
                if len(active_tab.elements) > 20:
                    print(f"   ... and {len(active_tab.elements) - 20} more elements")
                
                # Display role summary
                print("\n9. Element Role Summary:")
                for role, count in sorted(role_counts.items()):
                    print(f"   - {role}: {count} elements")
                
                # Test finding specific elements
                print("\n10. Testing Element Search:")
                
                # Search for buttons
                button_elements = browser_handler.find_elements_in_browser(
                    chrome_app, "button", roles=['AXButton']
                )
                print(f"   - Found {len(button_elements)} button elements")
                
                # Search for links
                link_elements = browser_handler.find_elements_in_browser(
                    chrome_app, "link", roles=['AXLink']
                )
                print(f"   - Found {len(link_elements)} link elements")
                
                # Search for text fields
                text_elements = browser_handler.find_elements_in_browser(
                    chrome_app, "text", roles=['AXTextField', 'AXTextArea']
                )
                print(f"   - Found {len(text_elements)} text input elements")
                
                # Get all web content elements
                web_content = browser_handler.get_web_content_elements(chrome_app)
                print(f"   - Total web content elements: {len(web_content)}")
                
            else:
                print("   ⚠️  No elements found in active tab")
        else:
            print("   ⚠️  No active tab found")
        
        # Display frame information if any
        if any(tab.frames for tab in browser_tree.tabs):
            print("\n11. Frame Information:")
            for tab in browser_tree.tabs:
                if tab.frames:
                    print(f"   Tab {tab.tab_id} has {len(tab.frames)} frames:")
                    for frame in tab.frames:
                        print(f"     - Frame: {frame.frame_id}")
                        print(f"       URL: {frame.url}")
                        print(f"       Title: {frame.title}")
                        print(f"       Elements: {len(frame.elements)}")
        
        # Test search parameters adaptation
        print("\n12. Testing Search Parameter Adaptation:")
        search_params = app_detector.adapt_search_parameters(
            chrome_app, "Click on search button"
        )
        print(f"   - Adapted roles: {search_params.roles[:5]}... ({len(search_params.roles)} total)")
        print(f"   - Timeout: {search_params.timeout_ms}ms")
        print(f"   - Max depth: {search_params.max_depth}")
        print(f"   - Fuzzy threshold: {search_params.fuzzy_threshold}")
        print(f"   - Search frames: {search_params.search_frames}")
        print(f"   - Web content only: {search_params.web_content_only}")
        
        # Cache statistics
        print("\n13. Cache Statistics:")
        app_stats = app_detector.get_cache_stats()
        browser_stats = browser_handler.get_cache_stats()
        print(f"   - App detector cache: {app_stats['app_cache_size']} apps, {app_stats['strategy_cache_size']} strategies")
        print(f"   - Browser handler cache: {browser_stats['cache_size']} trees")
        
        print("\n✅ Chrome accessibility tree test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error extracting browser tree: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function to run the test."""
    print("Chrome Accessibility Tree Test")
    print("Please make sure Chrome is open with at least one tab")
    print()
    
    # Wait a moment for user to prepare
    input("Press Enter when Chrome is ready...")
    
    success = test_chrome_accessibility_tree()
    
    if success:
        print("\n🎉 Test completed successfully!")
        print("The accessibility tree extraction is working properly.")
    else:
        print("\n❌ Test failed!")
        print("There may be issues with accessibility permissions or Chrome setup.")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)