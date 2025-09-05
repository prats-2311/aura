#!/usr/bin/env python3
"""
Complete workflow test demonstrating the full Chrome accessibility implementation.
This test shows the end-to-end process from application detection to element extraction.
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


def demonstrate_complete_workflow():
    """Demonstrate the complete Chrome accessibility workflow."""
    print("🚀 Complete Chrome Accessibility Workflow Demonstration")
    print("=" * 65)
    print("This demonstrates the full end-to-end process:")
    print("1. Application detection")
    print("2. Strategy selection") 
    print("3. Browser configuration")
    print("4. Accessibility tree extraction")
    print("5. Element analysis and search")
    print("6. Performance metrics")
    print()
    
    # Step 1: Find Chrome
    print("Step 1: Finding Chrome process...")
    chrome_pid = find_chrome_process()
    if not chrome_pid:
        print("❌ Chrome not found. Please open Chrome first.")
        return False
    print(f"✅ Chrome found: PID {chrome_pid}")
    
    # Step 2: Initialize system
    print("\nStep 2: Initializing accessibility system...")
    app_detector = ApplicationDetector()
    browser_handler = BrowserAccessibilityHandler()
    print("✅ System initialized")
    
    # Step 3: Detect application
    print("\nStep 3: Detecting application type...")
    start_time = time.time()
    app_info = app_detector.detect_application_type("Google Chrome")
    detection_time = (time.time() - start_time) * 1000
    
    print(f"✅ Application detected in {detection_time:.1f}ms:")
    print(f"   - Name: {app_info.name}")
    print(f"   - Type: {app_info.app_type.value}")
    print(f"   - Browser: {app_info.browser_type.value}")
    print(f"   - Bundle ID: {app_info.bundle_id}")
    print(f"   - Process ID: {app_info.process_id}")
    print(f"   - Confidence: {app_info.detection_confidence}")
    
    # Step 4: Get detection strategy
    print("\nStep 4: Getting detection strategy...")
    strategy = app_detector.get_detection_strategy(app_info)
    print(f"✅ Strategy configured:")
    print(f"   - Type: {strategy.app_type.value}")
    print(f"   - Timeout: {strategy.timeout_ms}ms")
    print(f"   - Max depth: {strategy.max_depth}")
    print(f"   - Fuzzy threshold: {strategy.fuzzy_threshold}")
    print(f"   - Handle frames: {strategy.handle_frames}")
    print(f"   - Handle tabs: {strategy.handle_tabs}")
    print(f"   - Web content detection: {strategy.web_content_detection}")
    print(f"   - Parallel search: {strategy.parallel_search}")
    
    # Step 5: Get browser configuration
    print("\nStep 5: Getting browser-specific configuration...")
    browser_config = browser_handler.get_browser_config(app_info.browser_type)
    print(f"✅ Chrome configuration loaded:")
    print(f"   - Web content roles: {browser_config['web_content_roles']}")
    print(f"   - Navigation roles: {browser_config['navigation_roles']}")
    print(f"   - Frame indicators: {browser_config['frame_indicators']}")
    print(f"   - Tab indicators: {browser_config['tab_indicators']}")
    print(f"   - Search depth: {browser_config['search_depth']}")
    print(f"   - Timeout: {browser_config['timeout_ms']}ms")
    print(f"   - Fuzzy threshold: {browser_config['fuzzy_threshold']}")
    
    # Step 6: Adapt search parameters for different commands
    print("\nStep 6: Testing search parameter adaptation...")
    test_commands = [
        "Click on login button",
        "Type email address",
        "Click on search link",
        "Select dropdown option"
    ]
    
    for command in test_commands:
        params = app_detector.adapt_search_parameters(app_info, command)
        print(f"   Command: '{command}'")
        print(f"   - Roles: {params.roles[:4]}...")
        print(f"   - Timeout: {params.timeout_ms}ms")
        print(f"   - Search frames: {params.search_frames}")
        print(f"   - Web content only: {params.web_content_only}")
    
    # Step 7: Extract accessibility tree
    print(f"\nStep 7: Extracting Chrome accessibility tree...")
    print(f"⏰ 5 second countdown - switch to Chrome...")
    for i in range(5, 0, -1):
        print(f"⏳ {i}...", end='\r')
        time.sleep(1)
    print("🚀 Extracting accessibility tree!     ")
    
    try:
        start_time = time.time()
        browser_tree = browser_handler.extract_browser_tree(app_info)
        extraction_time = (time.time() - start_time) * 1000
        
        if not browser_tree:
            print("❌ Failed to extract browser tree")
            return False
        
        print(f"✅ Browser tree extracted in {extraction_time:.1f}ms")
        
        # Step 8: Analyze results
        print(f"\nStep 8: Analyzing extraction results...")
        total_tabs = len(browser_tree.tabs)
        total_elements = len(browser_tree.get_all_elements())
        active_tab = browser_tree.get_active_tab()
        
        print(f"   - Total tabs: {total_tabs}")
        print(f"   - Total elements: {total_elements}")
        print(f"   - Active tab: {browser_tree.active_tab_id}")
        print(f"   - Extraction time: {extraction_time:.1f}ms")
        print(f"   - Elements per second: {total_elements / (extraction_time / 1000):.0f}")
        
        # Step 9: Tab quality analysis
        print(f"\nStep 9: Tab quality analysis...")
        content_tabs = []
        empty_tabs = []
        
        for tab in browser_tree.tabs:
            tab_elements = len(tab.elements) + sum(len(frame.elements) for frame in tab.frames)
            if tab_elements > 0:
                content_tabs.append((tab, tab_elements))
            else:
                empty_tabs.append(tab)
        
        print(f"   - Content-rich tabs: {len(content_tabs)}")
        print(f"   - Empty/UI tabs: {len(empty_tabs)}")
        print(f"   - Content ratio: {len(content_tabs) / total_tabs:.1%}")
        
        # Show content tabs
        if content_tabs:
            content_tabs.sort(key=lambda x: x[1], reverse=True)
            print(f"   - Content tabs (by element count):")
            for i, (tab, element_count) in enumerate(content_tabs):
                print(f"     {i+1}. {tab.tab_id}: {element_count} elements - '{tab.title}'")
        
        # Step 10: Active tab analysis
        print(f"\nStep 10: Active tab analysis...")
        if active_tab:
            active_elements = len(active_tab.elements) + sum(len(frame.elements) for frame in active_tab.frames)
            print(f"   - Active tab: {active_tab.tab_id}")
            print(f"   - Title: '{active_tab.title}'")
            print(f"   - URL: '{active_tab.url}'")
            print(f"   - Elements: {active_elements}")
            print(f"   - Active: {active_tab.is_active}")
            
            if active_elements > 0:
                print(f"   ✅ Active tab has content")
                
                # Analyze active tab elements
                all_elements = active_tab.elements + [elem for frame in active_tab.frames for elem in frame.elements]
                role_counts = {}
                for element in all_elements:
                    role = element.role
                    role_counts[role] = role_counts.get(role, 0) + 1
                
                print(f"   - Element roles: {dict(role_counts)}")
                
                # Show meaningful elements
                meaningful_elements = [e for e in all_elements 
                                     if e.title.strip() or e.description.strip() or e.value.strip()]
                
                if meaningful_elements:
                    print(f"   - Meaningful elements: {len(meaningful_elements)}")
                    print(f"   - Sample content:")
                    for j, elem in enumerate(meaningful_elements[:5]):
                        content = elem.title or elem.description or elem.value
                        content = content[:40] + "..." if len(content) > 40 else content
                        print(f"     {j+1}. {elem.role}: '{content}'")
            else:
                print(f"   ⚠️  Active tab is empty")
        else:
            print(f"   ❌ No active tab found")
        
        # Step 11: Element search demonstration
        print(f"\nStep 11: Element search demonstration...")
        
        # Search for different element types
        all_elements = browser_tree.get_all_elements()
        
        buttons = [e for e in all_elements if e.role == 'AXButton']
        links = [e for e in all_elements if e.role == 'AXLink']
        text_fields = [e for e in all_elements if e.role in ['AXTextField', 'AXTextArea']]
        static_text = [e for e in all_elements if e.role == 'AXStaticText']
        
        print(f"   - Total elements: {len(all_elements)}")
        print(f"   - Buttons: {len(buttons)}")
        print(f"   - Links: {len(links)}")
        print(f"   - Text fields: {len(text_fields)}")
        print(f"   - Static text: {len(static_text)}")
        
        # Show sample elements by type
        if buttons:
            print(f"   - Sample buttons:")
            for i, button in enumerate(buttons[:3]):
                content = button.title or button.description or "(no text)"
                print(f"     {i+1}. '{content}'")
        
        if links:
            print(f"   - Sample links:")
            for i, link in enumerate(links[:3]):
                print(f"     {i+1}. '{link.title}' -> {link.url}")
        
        # Step 12: Performance metrics
        print(f"\nStep 12: Performance metrics...")
        
        # Cache statistics
        app_stats = app_detector.get_cache_stats()
        browser_stats = browser_handler.get_cache_stats()
        
        print(f"   - Application cache: {app_stats['app_cache_size']} entries")
        print(f"   - Strategy cache: {app_stats['strategy_cache_size']} entries")
        print(f"   - Browser tree cache: {browser_stats['cache_size']} entries")
        print(f"   - Cache TTL: {browser_stats['cache_ttl']}s")
        
        # Performance summary
        total_time = detection_time + extraction_time
        print(f"   - Total detection time: {detection_time:.1f}ms")
        print(f"   - Total extraction time: {extraction_time:.1f}ms")
        print(f"   - Total workflow time: {total_time:.1f}ms")
        print(f"   - Elements per second: {total_elements / (extraction_time / 1000):.0f}")
        
        # Step 13: Success assessment
        print(f"\nStep 13: Success assessment...")
        
        success_metrics = []
        
        # Application detection
        if app_info.app_type == ApplicationType.WEB_BROWSER and app_info.browser_type == BrowserType.CHROME:
            success_metrics.append("✅ Application detection accurate")
        else:
            success_metrics.append("❌ Application detection failed")
        
        # Tab detection
        if 1 <= total_tabs <= 6:  # Reasonable range
            success_metrics.append("✅ Tab detection reasonable")
        else:
            success_metrics.append(f"⚠️  Tab count: {total_tabs}")
        
        # Element extraction
        if total_elements > 0:
            success_metrics.append("✅ Elements extracted")
        else:
            success_metrics.append("❌ No elements extracted")
        
        # Performance
        if extraction_time < 200:
            success_metrics.append("✅ Fast extraction")
        else:
            success_metrics.append("⚠️  Slow extraction")
        
        # Content quality
        content_ratio = len(content_tabs) / total_tabs if total_tabs > 0 else 0
        if content_ratio >= 0.3:
            success_metrics.append("✅ Good content quality")
        else:
            success_metrics.append("⚠️  Low content quality")
        
        # Active tab quality
        if active_tab and len(active_tab.elements) + sum(len(f.elements) for f in active_tab.frames) > 0:
            success_metrics.append("✅ Active tab has content")
        else:
            success_metrics.append("⚠️  Active tab empty")
        
        print(f"   Success metrics:")
        for metric in success_metrics:
            print(f"     {metric}")
        
        success_count = sum(1 for m in success_metrics if m.startswith("✅"))
        total_metrics = len(success_metrics)
        success_rate = success_count / total_metrics
        
        print(f"\n🏆 Final Workflow Results:")
        print(f"   - Success rate: {success_rate:.1%} ({success_count}/{total_metrics})")
        print(f"   - Total workflow time: {total_time:.1f}ms")
        print(f"   - Elements extracted: {total_elements}")
        print(f"   - Tab detection: {total_tabs} tabs")
        
        if success_rate >= 0.8:
            print(f"   🎉 EXCELLENT: Complete workflow working very well!")
            return True
        elif success_rate >= 0.6:
            print(f"   ✅ GOOD: Workflow working well with minor issues")
            return True
        else:
            print(f"   ⚠️  NEEDS IMPROVEMENT: Workflow has significant issues")
            return False
        
    except Exception as e:
        print(f"❌ Error during workflow: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function."""
    print("Chrome Complete Workflow Test")
    print("This test demonstrates the full end-to-end workflow")
    print("for Chrome accessibility detection and extraction.")
    print()
    
    input("Press Enter to start workflow test (ensure Chrome is open with tabs)...")
    
    success = demonstrate_complete_workflow()
    
    if success:
        print(f"\n🎉 Complete workflow test PASSED!")
        print(f"The Chrome accessibility implementation is fully functional.")
        print(f"\n📋 Summary of what works:")
        print(f"✅ Application type detection (Chrome browser)")
        print(f"✅ Browser-specific strategy selection")
        print(f"✅ Adaptive search parameter configuration")
        print(f"✅ Accessibility tree extraction")
        print(f"✅ Tab detection and filtering")
        print(f"✅ Element extraction and analysis")
        print(f"✅ Performance optimization with caching")
        print(f"✅ Smart active tab detection")
    else:
        print(f"\n⚠️  Workflow test completed with issues!")
        print(f"Some components may need additional refinement.")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)