#!/usr/bin/env python3
"""
Final test of Chrome accessibility with all fixes applied.
This should now correctly identify and prioritize actual web content tabs.
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


def test_chrome_final_fixes():
    """Test Chrome with all fixes applied."""
    print("🔧 Chrome Accessibility - Final Fixed Version")
    print("=" * 55)
    print("Expected improvements:")
    print("✅ Filter out empty browser UI containers")
    print("✅ Prioritize content-rich tabs")
    print("✅ Better page title and URL extraction")
    print("✅ Smart active tab detection")
    print("✅ Deduplicate similar tabs")
    print()
    
    # Find Chrome
    chrome_pid = find_chrome_process()
    if not chrome_pid:
        print("❌ Chrome not found")
        return False
    
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
    
    print(f"\n⏰ 5 second countdown - switch to Chrome...")
    for i in range(5, 0, -1):
        print(f"⏳ {i}...", end='\r')
        time.sleep(1)
    print("🚀 Testing final fixes!     ")
    
    try:
        start_time = time.time()
        browser_tree = browser_handler.extract_browser_tree(chrome_app)
        extraction_time = (time.time() - start_time) * 1000
        
        if not browser_tree:
            print("❌ Failed to extract browser tree")
            return False
        
        print(f"\n📊 Extraction Results:")
        print(f"   - Extraction time: {extraction_time:.1f}ms")
        print(f"   - Total tabs detected: {len(browser_tree.tabs)}")
        print(f"   - Total elements: {len(browser_tree.get_all_elements())}")
        print(f"   - Active tab: {browser_tree.active_tab_id}")
        
        # Analyze improvement
        content_tabs = []
        empty_tabs = []
        
        for tab in browser_tree.tabs:
            total_elements = len(tab.elements) + sum(len(frame.elements) for frame in tab.frames)
            if total_elements > 0:
                content_tabs.append((tab, total_elements))
            else:
                empty_tabs.append(tab)
        
        print(f"\n🎯 Tab Quality Analysis:")
        print(f"   - Content-rich tabs: {len(content_tabs)}")
        print(f"   - Empty/UI tabs: {len(empty_tabs)}")
        
        improvement_score = len(content_tabs) / len(browser_tree.tabs) if browser_tree.tabs else 0
        print(f"   - Content ratio: {improvement_score:.1%}")
        
        if improvement_score >= 0.5:
            print(f"   ✅ GOOD: Majority of tabs have content")
        else:
            print(f"   ⚠️  NEEDS WORK: Too many empty tabs")
        
        # Detailed tab analysis
        print(f"\n📋 Detailed Tab Analysis:")
        
        for i, tab in enumerate(browser_tree.tabs):
            total_elements = len(tab.elements) + sum(len(frame.elements) for frame in tab.frames)
            
            print(f"\n   Tab {i+1}: {tab.tab_id}")
            print(f"     - Title: '{tab.title}'")
            print(f"     - URL: '{tab.url}'")
            print(f"     - Active: {tab.is_active}")
            print(f"     - Elements: {total_elements}")
            
            if total_elements > 0:
                print(f"     - 🎯 CONTENT TAB")
                
                # Analyze element types
                all_elements = tab.elements + [elem for frame in tab.frames for elem in frame.elements]
                role_counts = {}
                for element in all_elements:
                    role = element.role
                    role_counts[role] = role_counts.get(role, 0) + 1
                
                print(f"     - Element types: {dict(role_counts)}")
                
                # Look for meaningful content
                meaningful_elements = [e for e in all_elements 
                                     if e.title.strip() or e.description.strip() or e.value.strip()]
                
                if meaningful_elements:
                    print(f"     - Meaningful content: {len(meaningful_elements)} elements")
                    
                    # Check for specific site content
                    facebook_content = [e for e in meaningful_elements 
                                      if 'facebook' in (e.title + e.description + e.value).lower()]
                    google_content = [e for e in meaningful_elements
                                    if 'google' in (e.title + e.description + e.value).lower()]
                    
                    if facebook_content:
                        print(f"     - 📘 Facebook content: {len(facebook_content)} elements")
                        for elem in facebook_content[:2]:
                            content = elem.title or elem.description or elem.value
                            print(f"       • {elem.role}: '{content[:30]}...'")
                    
                    if google_content:
                        print(f"     - 🔍 Google content: {len(google_content)} elements")
                        for elem in google_content[:2]:
                            content = elem.title or elem.description or elem.value
                            print(f"       • {elem.role}: '{content[:30]}...'")
                    
                    # Show sample meaningful elements
                    if not facebook_content and not google_content:
                        print(f"     - Sample content:")
                        for j, elem in enumerate(meaningful_elements[:3]):
                            content = elem.title or elem.description or elem.value
                            content = content[:30] + "..." if len(content) > 30 else content
                            print(f"       {j+1}. {elem.role}: '{content}'")
                
            else:
                print(f"     - ⚪ EMPTY TAB (browser UI)")
        
        # Active tab analysis
        active_tab = browser_tree.get_active_tab()
        if active_tab:
            active_elements = len(active_tab.elements) + sum(len(frame.elements) for frame in active_tab.frames)
            print(f"\n🎯 Active Tab Analysis:")
            print(f"   - Active tab: {active_tab.tab_id}")
            print(f"   - Title: '{active_tab.title}'")
            print(f"   - URL: '{active_tab.url}'")
            print(f"   - Elements: {active_elements}")
            
            if active_elements > 0:
                print(f"   ✅ Active tab has content (good!)")
            else:
                print(f"   ⚠️  Active tab is empty (should prioritize content tabs)")
        
        # Overall assessment
        print(f"\n📈 Overall Assessment:")
        
        fixes_working = []
        fixes_needed = []
        
        # Check if empty tabs are filtered
        if len(empty_tabs) <= 1:
            fixes_working.append("✅ Empty tabs filtered (≤1 empty tab)")
        else:
            fixes_needed.append("❌ Too many empty tabs still present")
        
        # Check if content tabs are prioritized
        if content_tabs and active_tab and len(active_tab.elements) + sum(len(f.elements) for f in active_tab.frames) > 0:
            fixes_working.append("✅ Content tab is active")
        elif content_tabs:
            fixes_needed.append("❌ Content tab should be active")
        
        # Check if page titles are extracted
        meaningful_titles = [tab for tab in browser_tree.tabs if tab.title not in ["Browser Window", "Untitled", ""]]
        if meaningful_titles:
            fixes_working.append("✅ Page titles extracted")
        else:
            fixes_needed.append("❌ Page titles not extracted")
        
        # Check if URLs are inferred
        tabs_with_urls = [tab for tab in browser_tree.tabs if tab.url]
        if tabs_with_urls:
            fixes_working.append("✅ URLs inferred")
        else:
            fixes_needed.append("❌ URLs not inferred")
        
        print(f"\n   Fixes Working:")
        for fix in fixes_working:
            print(f"     {fix}")
        
        if fixes_needed:
            print(f"\n   Fixes Still Needed:")
            for fix in fixes_needed:
                print(f"     {fix}")
        
        # Success criteria
        success_score = len(fixes_working) / (len(fixes_working) + len(fixes_needed)) if (fixes_working or fixes_needed) else 0
        
        print(f"\n🏆 Success Score: {success_score:.1%}")
        
        if success_score >= 0.75:
            print(f"   🎉 EXCELLENT: Most fixes are working!")
        elif success_score >= 0.5:
            print(f"   ✅ GOOD: Majority of fixes are working")
        else:
            print(f"   ⚠️  NEEDS IMPROVEMENT: More fixes needed")
        
        return success_score >= 0.5
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function."""
    print("Chrome Final Fixes Test")
    print("This test validates all the fixes applied to resolve")
    print("the tab detection and content extraction issues.")
    print()
    
    input("Press Enter to start test (make sure Chrome has Google + Facebook tabs)...")
    
    success = test_chrome_final_fixes()
    
    if success:
        print(f"\n🎉 Test completed successfully!")
        print(f"The fixes have significantly improved Chrome accessibility handling.")
    else:
        print(f"\n⚠️  Test completed with issues!")
        print(f"Some fixes may need additional refinement.")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)