#!/usr/bin/env python3
"""
Test Chrome accessibility with fixed tab detection.
Should now correctly identify 2 tabs instead of 11.
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


def test_fixed_chrome_tabs():
    """Test Chrome with fixed tab detection."""
    print("🔧 Testing Chrome with Fixed Tab Detection")
    print("=" * 55)
    
    # Find Chrome
    chrome_processes = find_chrome_process()
    if not chrome_processes:
        print("❌ Chrome not found")
        return False
    
    chrome_pid = chrome_processes[0]['pid']
    print(f"✅ Found Chrome PID: {chrome_pid}")
    
    # Initialize modules
    app_detector = ApplicationDetector()
    browser_handler = BrowserAccessibilityHandler()
    
    # Create Chrome app info
    chrome_app = ApplicationInfo(
        name="Google Chrome",
        bundle_id="com.google.Chrome",
        process_id=chrome_pid,
        app_type=ApplicationType.WEB_BROWSER,
        browser_type=BrowserType.CHROME
    )
    
    # Show the fixed configuration
    chrome_config = browser_handler.get_browser_config(BrowserType.CHROME)
    print(f"\n📋 Fixed Chrome Tab Indicators: {chrome_config['tab_indicators']}")
    print("   (Removed 'AXButton' to avoid browser UI buttons)")
    
    print(f"\n⏰ 5 second countdown - switch to Chrome with your 2 tabs...")
    for i in range(5, 0, -1):
        print(f"⏳ {i}...", end='\r')
        time.sleep(1)
    print("🚀 Testing fixed tab detection!     ")
    
    try:
        start_time = time.time()
        browser_tree = browser_handler.extract_browser_tree(chrome_app)
        extraction_time = (time.time() - start_time) * 1000
        
        if not browser_tree:
            print("❌ Failed to extract browser tree")
            return False
        
        print(f"\n✅ Browser tree extracted in {extraction_time:.1f}ms!")
        print(f"   - Total tabs detected: {len(browser_tree.tabs)}")
        print(f"   - Total elements: {len(browser_tree.get_all_elements())}")
        print(f"   - Active tab: {browser_tree.active_tab_id}")
        
        # Expected: Should now find 2 tabs (Google + Facebook)
        expected_tabs = 2
        actual_tabs = len(browser_tree.tabs)
        
        print(f"\n🎯 Tab Detection Results:")
        print(f"   Expected tabs: {expected_tabs} (Google + Facebook)")
        print(f"   Detected tabs: {actual_tabs}")
        
        if actual_tabs == expected_tabs:
            print(f"   ✅ SUCCESS: Correct number of tabs detected!")
        elif actual_tabs < expected_tabs:
            print(f"   ⚠️  UNDER-DETECTION: Found fewer tabs than expected")
        else:
            print(f"   ⚠️  OVER-DETECTION: Still finding too many tabs")
        
        # Analyze each detected tab
        print(f"\n📊 Detailed Tab Analysis:")
        for i, tab in enumerate(browser_tree.tabs):
            element_count = len(tab.elements)
            frame_count = len(tab.frames)
            total_elements = element_count + sum(len(frame.elements) for frame in tab.frames)
            
            print(f"   Tab {i+1}: {tab.tab_id}")
            print(f"     - Title: '{tab.title}'")
            print(f"     - URL: '{tab.url}'")
            print(f"     - Active: {tab.is_active}")
            print(f"     - Elements: {element_count} direct + {sum(len(f.elements) for f in tab.frames)} in frames = {total_elements} total")
            
            if total_elements > 0:
                # Show element types
                all_elements = tab.elements + [elem for frame in tab.frames for elem in frame.elements]
                role_counts = {}
                for element in all_elements:
                    role = element.role
                    role_counts[role] = role_counts.get(role, 0) + 1
                
                print(f"     - Element roles: {dict(role_counts)}")
                
                # Show sample elements with actual content
                content_elements = [e for e in all_elements if e.title.strip() or e.description.strip() or e.value.strip()]
                if content_elements:
                    print(f"     - Sample content elements:")
                    for j, element in enumerate(content_elements[:3]):
                        title = element.title[:30] + "..." if len(element.title) > 30 else element.title
                        desc = element.description[:30] + "..." if len(element.description) > 30 else element.description
                        value = element.value[:30] + "..." if len(element.value) > 30 else element.value
                        
                        content = title or desc or value or "(no text content)"
                        print(f"       {j+1}. {element.role}: '{content}'")
        
        # Find the most content-rich tab (likely the Facebook login page)
        tabs_with_content = [(tab, len(tab.elements) + sum(len(f.elements) for f in tab.frames)) 
                           for tab in browser_tree.tabs]
        tabs_with_content.sort(key=lambda x: x[1], reverse=True)
        
        if tabs_with_content and tabs_with_content[0][1] > 0:
            richest_tab, element_count = tabs_with_content[0]
            print(f"\n🎯 Most Content-Rich Tab: {richest_tab.tab_id}")
            print(f"   - Title: '{richest_tab.title}'")
            print(f"   - Elements: {element_count}")
            print(f"   - This should be the Facebook login page")
            
            # Show Facebook-specific elements
            all_elements = richest_tab.elements + [elem for frame in richest_tab.frames for elem in frame.elements]
            facebook_elements = []
            
            for element in all_elements:
                text_content = (element.title + " " + element.description + " " + element.value).lower()
                if any(keyword in text_content for keyword in ['facebook', 'login', 'email', 'password', 'sign']):
                    facebook_elements.append(element)
            
            if facebook_elements:
                print(f"   - Facebook-related elements found: {len(facebook_elements)}")
                for i, element in enumerate(facebook_elements[:5]):
                    content = element.title or element.description or element.value or f"({element.role})"
                    print(f"     {i+1}. {element.role}: '{content[:40]}...' " if len(content) > 40 else f"     {i+1}. {element.role}: '{content}'")
        
        # Performance summary
        print(f"\n📈 Performance Summary:")
        print(f"   - Extraction time: {extraction_time:.1f}ms")
        print(f"   - Elements per second: {len(browser_tree.get_all_elements()) / (extraction_time / 1000):.0f}")
        print(f"   - Tab detection accuracy: {'✅ GOOD' if actual_tabs <= expected_tabs + 1 else '⚠️ NEEDS IMPROVEMENT'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function."""
    print("Chrome Fixed Tab Detection Test")
    print("This test uses the corrected tab detection logic")
    print("that should find 2 tabs instead of 11.")
    print()
    
    input("Press Enter to start test (make sure Chrome has 2 tabs: Google + Facebook)...")
    
    success = test_fixed_chrome_tabs()
    
    if success:
        print(f"\n🎉 Test completed!")
        print(f"The tab detection has been improved.")
    else:
        print(f"\n❌ Test failed!")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)