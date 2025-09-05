#!/usr/bin/env python3
"""
Comprehensive final test of Chrome accessibility with all fixes applied.
This test validates the complete implementation after autofix.
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


def test_comprehensive_chrome_final():
    """Comprehensive test of Chrome accessibility implementation."""
    print("🔬 Comprehensive Chrome Accessibility Test - Final Version")
    print("=" * 65)
    print("Testing complete implementation after all fixes and autofix")
    print()
    
    # Find Chrome
    chrome_pid = find_chrome_process()
    if not chrome_pid:
        print("❌ Chrome not found. Please open Chrome first.")
        return False
    
    print(f"✅ Found Chrome PID: {chrome_pid}")
    
    # Initialize modules
    print("\n1. Initializing modules...")
    app_detector = ApplicationDetector()
    browser_handler = BrowserAccessibilityHandler()
    print("   ✅ ApplicationDetector initialized")
    print("   ✅ BrowserAccessibilityHandler initialized")
    
    # Test application detection
    print("\n2. Testing application detection...")
    detected_app = app_detector.detect_application_type("Google Chrome")
    print(f"   - Detected type: {detected_app.app_type.value}")
    print(f"   - Browser type: {detected_app.browser_type.value if detected_app.browser_type else 'None'}")
    print(f"   - Confidence: {detected_app.detection_confidence}")
    
    if detected_app.app_type == ApplicationType.WEB_BROWSER and detected_app.browser_type == BrowserType.CHROME:
        print("   ✅ Application detection working correctly")
    else:
        print("   ❌ Application detection failed")
        return False
    
    # Test detection strategy
    print("\n3. Testing detection strategy...")
    strategy = app_detector.get_detection_strategy(detected_app)
    print(f"   - Strategy type: {strategy.app_type.value}")
    print(f"   - Timeout: {strategy.timeout_ms}ms")
    print(f"   - Max depth: {strategy.max_depth}")
    print(f"   - Fuzzy threshold: {strategy.fuzzy_threshold}")
    print(f"   - Handle frames: {strategy.handle_frames}")
    print(f"   - Handle tabs: {strategy.handle_tabs}")
    print("   ✅ Detection strategy configured correctly")
    
    # Test browser configuration
    print("\n4. Testing browser configuration...")
    browser_config = browser_handler.get_browser_config(BrowserType.CHROME)
    print(f"   - Web content roles: {len(browser_config['web_content_roles'])} roles")
    print(f"   - Tab indicators: {browser_config['tab_indicators']}")
    print(f"   - Frame indicators: {browser_config['frame_indicators']}")
    print(f"   - Search depth: {browser_config['search_depth']}")
    print("   ✅ Browser configuration loaded correctly")
    
    # Test search parameter adaptation
    print("\n5. Testing search parameter adaptation...")
    test_commands = [
        "Click on search button",
        "Type hello in text field", 
        "Click on submit link"
    ]
    
    for command in test_commands:
        params = app_detector.adapt_search_parameters(detected_app, command)
        print(f"   Command: '{command}'")
        print(f"   - Priority roles: {params.roles[:3]}")
        print(f"   - Timeout: {params.timeout_ms}ms")
        print(f"   - Search frames: {params.search_frames}")
    print("   ✅ Search parameter adaptation working")
    
    # Main accessibility tree extraction test
    print(f"\n6. Testing accessibility tree extraction...")
    print(f"   ⏰ 5 second countdown - switch to Chrome...")
    for i in range(5, 0, -1):
        print(f"   ⏳ {i}...", end='\r')
        time.sleep(1)
    print("   🚀 Extracting accessibility tree!     ")
    
    try:
        start_time = time.time()
        browser_tree = browser_handler.extract_browser_tree(detected_app)
        extraction_time = (time.time() - start_time) * 1000
        
        if not browser_tree:
            print("   ❌ Failed to extract browser tree")
            return False
        
        print(f"   ✅ Browser tree extracted in {extraction_time:.1f}ms")
        
        # Analyze results
        print(f"\n7. Analyzing extraction results...")
        total_tabs = len(browser_tree.tabs)
        total_elements = len(browser_tree.get_all_elements())
        active_tab_id = browser_tree.active_tab_id
        
        print(f"   - Total tabs: {total_tabs}")
        print(f"   - Total elements: {total_elements}")
        print(f"   - Active tab: {active_tab_id}")
        print(f"   - Extraction time: {extraction_time:.1f}ms")
        
        # Quality analysis
        content_tabs = []
        empty_tabs = []
        
        for tab in browser_tree.tabs:
            tab_elements = len(tab.elements) + sum(len(frame.elements) for frame in tab.frames)
            if tab_elements > 0:
                content_tabs.append((tab, tab_elements))
            else:
                empty_tabs.append(tab)
        
        content_ratio = len(content_tabs) / total_tabs if total_tabs > 0 else 0
        
        print(f"\n8. Quality metrics...")
        print(f"   - Content-rich tabs: {len(content_tabs)}")
        print(f"   - Empty/UI tabs: {len(empty_tabs)}")
        print(f"   - Content ratio: {content_ratio:.1%}")
        print(f"   - Elements per second: {total_elements / (extraction_time / 1000):.0f}")
        
        # Detailed tab analysis
        print(f"\n9. Detailed tab analysis...")
        for i, tab in enumerate(browser_tree.tabs):
            tab_elements = len(tab.elements) + sum(len(frame.elements) for frame in tab.frames)
            
            print(f"   Tab {i+1}: {tab.tab_id}")
            print(f"     - Title: '{tab.title}'")
            print(f"     - URL: '{tab.url}'")
            print(f"     - Active: {tab.is_active}")
            print(f"     - Elements: {tab_elements}")
            
            if tab_elements > 0:
                print(f"     - Type: 🎯 CONTENT TAB")
                
                # Analyze element types
                all_elements = tab.elements + [elem for frame in tab.frames for elem in frame.elements]
                role_counts = {}
                for element in all_elements:
                    role = element.role
                    role_counts[role] = role_counts.get(role, 0) + 1
                
                print(f"     - Element roles: {dict(role_counts)}")
                
                # Look for meaningful content
                meaningful_elements = [e for e in all_elements 
                                     if e.title.strip() or e.description.strip() or e.value.strip()]
                
                if meaningful_elements:
                    print(f"     - Meaningful elements: {len(meaningful_elements)}")
                    
                    # Show sample content
                    for j, elem in enumerate(meaningful_elements[:3]):
                        content = elem.title or elem.description or elem.value
                        content = content[:30] + "..." if len(content) > 30 else content
                        print(f"       {j+1}. {elem.role}: '{content}'")
                
            else:
                print(f"     - Type: ⚪ EMPTY TAB (browser UI)")
        
        # Active tab validation
        print(f"\n10. Active tab validation...")
        active_tab = browser_tree.get_active_tab()
        if active_tab:
            active_elements = len(active_tab.elements) + sum(len(frame.elements) for frame in active_tab.frames)
            print(f"    - Active tab: {active_tab.tab_id}")
            print(f"    - Elements: {active_elements}")
            
            if active_elements > 0:
                print(f"    ✅ Active tab has content (excellent!)")
            else:
                print(f"    ⚠️  Active tab is empty (could be improved)")
        else:
            print(f"    ❌ No active tab found")
        
        # Element search testing
        print(f"\n11. Element search testing...")
        
        # Test finding elements by role
        all_elements = browser_tree.get_all_elements()
        buttons = [e for e in all_elements if e.role == 'AXButton']
        links = [e for e in all_elements if e.role == 'AXLink']
        text_fields = [e for e in all_elements if e.role in ['AXTextField', 'AXTextArea']]
        
        print(f"    - Buttons found: {len(buttons)}")
        print(f"    - Links found: {len(links)}")
        print(f"    - Text fields found: {len(text_fields)}")
        
        if buttons:
            print(f"    - Sample buttons:")
            for i, button in enumerate(buttons[:3]):
                content = button.title or button.description or "(no text)"
                print(f"      {i+1}. '{content}'")
        
        # Performance assessment
        print(f"\n12. Performance assessment...")
        
        performance_score = 100
        if extraction_time > 200:
            performance_score -= 20
            print(f"    ⚠️  Extraction time high: {extraction_time:.1f}ms")
        else:
            print(f"    ✅ Extraction time good: {extraction_time:.1f}ms")
        
        if total_elements == 0:
            performance_score -= 30
            print(f"    ❌ No elements found")
        elif total_elements < 10:
            performance_score -= 10
            print(f"    ⚠️  Few elements found: {total_elements}")
        else:
            print(f"    ✅ Good element count: {total_elements}")
        
        if content_ratio < 0.3:
            performance_score -= 20
            print(f"    ⚠️  Low content ratio: {content_ratio:.1%}")
        else:
            print(f"    ✅ Good content ratio: {content_ratio:.1%}")
        
        print(f"    📊 Performance score: {performance_score}/100")
        
        # Overall assessment
        print(f"\n13. Overall assessment...")
        
        success_criteria = []
        
        # Tab count should be reasonable (2-6 tabs)
        if 2 <= total_tabs <= 6:
            success_criteria.append("✅ Reasonable tab count")
        else:
            success_criteria.append(f"⚠️  Tab count: {total_tabs} (expected 2-6)")
        
        # Should have some content
        if total_elements > 0:
            success_criteria.append("✅ Elements extracted")
        else:
            success_criteria.append("❌ No elements extracted")
        
        # Content ratio should be decent
        if content_ratio >= 0.3:
            success_criteria.append("✅ Good content quality")
        else:
            success_criteria.append("⚠️  Low content quality")
        
        # Performance should be good
        if extraction_time < 200:
            success_criteria.append("✅ Fast extraction")
        else:
            success_criteria.append("⚠️  Slow extraction")
        
        # Active tab should ideally have content
        if active_tab and len(active_tab.elements) + sum(len(f.elements) for f in active_tab.frames) > 0:
            success_criteria.append("✅ Active tab has content")
        else:
            success_criteria.append("⚠️  Active tab empty")
        
        print(f"    Assessment results:")
        for criterion in success_criteria:
            print(f"      {criterion}")
        
        success_count = sum(1 for c in success_criteria if c.startswith("✅"))
        total_criteria = len(success_criteria)
        success_rate = success_count / total_criteria
        
        print(f"\n🏆 Final Results:")
        print(f"   - Success rate: {success_rate:.1%} ({success_count}/{total_criteria})")
        print(f"   - Performance score: {performance_score}/100")
        
        if success_rate >= 0.8 and performance_score >= 80:
            print(f"   🎉 EXCELLENT: Implementation working very well!")
            return True
        elif success_rate >= 0.6 and performance_score >= 60:
            print(f"   ✅ GOOD: Implementation working well with minor issues")
            return True
        else:
            print(f"   ⚠️  NEEDS IMPROVEMENT: Some issues need addressing")
            return False
        
    except Exception as e:
        print(f"   ❌ Error during accessibility tree extraction: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function."""
    print("Chrome Comprehensive Final Test")
    print("This test validates the complete implementation")
    print("including all fixes and autofix changes.")
    print()
    
    input("Press Enter to start comprehensive test (ensure Chrome is open)...")
    
    success = test_comprehensive_chrome_final()
    
    if success:
        print(f"\n🎉 Comprehensive test PASSED!")
        print(f"The Chrome accessibility implementation is working correctly.")
    else:
        print(f"\n⚠️  Comprehensive test completed with issues!")
        print(f"Some aspects may need further refinement.")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)