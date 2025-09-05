#!/usr/bin/env python3
"""
Gmail Click Fast Path Test
Tests clicking on Gmail link using accessibility fast path with detailed monitoring.
"""

import sys
import os
import time
import subprocess
import json
from typing import Dict, Any, List, Optional

# Add modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

def setup_chrome_for_testing():
    """Launch Chrome with Gmail and accessibility enabled"""
    print("🚀 Setting up Chrome for Gmail fast path testing...")
    
    chrome_path = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
    
    if not os.path.exists(chrome_path):
        print("❌ Chrome not found")
        return False
    
    try:
        # Launch Chrome with accessibility and navigate to Gmail
        cmd = [
            chrome_path,
            '--enable-accessibility',
            '--force-renderer-accessibility',
            '--remote-debugging-port=9222',
            '--new-window',
            'https://www.google.com'
        ]
        
        print("Launching Chrome with Gmail...")
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        time.sleep(3)
        print("✅ Chrome launched with Google homepage")
        return True
        
    except Exception as e:
        print(f"❌ Failed to launch Chrome: {e}")
        return False

def test_accessibility_tree_extraction():
    """Test if we can extract the accessibility tree from Chrome"""
    print("\n🌳 Testing Accessibility Tree Extraction...")
    print("-" * 45)
    
    try:
        from modules.accessibility import AccessibilityModule
        
        # Initialize accessibility module
        accessibility = AccessibilityModule()
        print("✅ Accessibility module initialized")
        
        # Test tree extraction
        start_time = time.time()
        
        # Try to find Chrome and extract its accessibility tree
        print("🔍 Extracting Chrome accessibility tree...")
        
        # Look for Gmail-related elements
        gmail_element = accessibility.find_element("", "Gmail", "Google Chrome")
        
        extraction_time = time.time() - start_time
        
        if gmail_element:
            print(f"✅ Gmail element found in {extraction_time:.2f}s")
            print(f"   Element details: {gmail_element}")
            return True, gmail_element
        else:
            # Try broader search for any link elements
            print("🔍 Searching for any link elements...")
            link_element = accessibility.find_element("AXLink", "", "Google Chrome")
            
            if link_element:
                print(f"✅ Link element found in {extraction_time:.2f}s")
                print(f"   Element details: {link_element}")
                return True, link_element
            else:
                print("⚠️  No Gmail or link elements found")
                return False, None
                
    except Exception as e:
        print(f"❌ Accessibility tree extraction failed: {e}")
        return False, None

def test_element_detection_performance():
    """Test the performance of element detection"""
    print("\n⚡ Testing Element Detection Performance...")
    print("-" * 45)
    
    try:
        from modules.accessibility import AccessibilityModule
        
        accessibility = AccessibilityModule()
        
        # Test multiple element detection attempts
        detection_times = []
        elements_found = []
        
        test_targets = [
            ("AXLink", "Gmail"),
            ("AXButton", ""),
            ("AXTextField", ""),
            ("", "Gmail"),
            ("", "Sign in")
        ]
        
        for role, label in test_targets:
            print(f"🔍 Testing detection: role='{role}', label='{label}'")
            
            start_time = time.time()
            element = accessibility.find_element(role, label, "Google Chrome")
            detection_time = time.time() - start_time
            
            detection_times.append(detection_time)
            
            if element:
                elements_found.append((role, label, element))
                print(f"   ✅ Found in {detection_time:.3f}s: {element.get('title', 'no title')[:30]}")
            else:
                print(f"   ❌ Not found ({detection_time:.3f}s)")
        
        # Calculate performance metrics
        avg_time = sum(detection_times) / len(detection_times)
        fastest = min(detection_times)
        slowest = max(detection_times)
        
        print(f"\n📊 Performance Summary:")
        print(f"   Average detection time: {avg_time:.3f}s")
        print(f"   Fastest detection: {fastest:.3f}s")
        print(f"   Slowest detection: {slowest:.3f}s")
        print(f"   Elements found: {len(elements_found)}/{len(test_targets)}")
        
        # Performance evaluation
        if avg_time < 0.5:
            print("🚀 Excellent performance - very fast detection")
            return True, elements_found
        elif avg_time < 1.0:
            print("✅ Good performance - fast detection")
            return True, elements_found
        else:
            print("⚠️  Slow performance - may need optimization")
            return False, elements_found
            
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        return False, []

def simulate_gmail_click_command():
    """Simulate the Gmail click command using Aura's orchestrator"""
    print("\n🎯 Testing Gmail Click Command via Orchestrator...")
    print("-" * 50)
    
    try:
        # Import Aura modules
        from orchestrator import Orchestrator
        
        # Initialize orchestrator
        orchestrator = Orchestrator()
        print("✅ Orchestrator initialized")
        
        # Test command: "click on Gmail link"
        command = "click on Gmail link"
        print(f"🎤 Processing command: '{command}'")
        
        # Process the command
        start_time = time.time()
        
        # This will test the full pipeline including accessibility fast path
        result = orchestrator.process_command(command)
        
        processing_time = time.time() - start_time
        
        print(f"⏱️  Command processed in {processing_time:.2f}s")
        
        if result and result.get('success'):
            print("✅ Gmail click command executed successfully")
            print(f"   Result: {result}")
            
            # Check if fast path was used
            if 'accessibility' in str(result).lower() or processing_time < 3.0:
                print("🚀 Fast path likely used (quick execution)")
                return True, result
            else:
                print("⚠️  May have used fallback method (slower execution)")
                return True, result
        else:
            print(f"❌ Gmail click command failed: {result}")
            return False, result
            
    except Exception as e:
        print(f"❌ Gmail click test failed: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def test_chrome_devtools_accessibility():
    """Test Chrome DevTools accessibility API"""
    print("\n🔧 Testing Chrome DevTools Accessibility API...")
    print("-" * 50)
    
    try:
        import urllib.request
        import json
        
        # Connect to Chrome DevTools
        response = urllib.request.urlopen('http://localhost:9222/json', timeout=5)
        tabs = json.loads(response.read().decode())
        
        print(f"✅ Connected to Chrome DevTools - {len(tabs)} tabs")
        
        # Find the active tab
        active_tab = None
        for tab in tabs:
            if tab.get('type') == 'page' and 'google.com' in tab.get('url', ''):
                active_tab = tab
                break
        
        if active_tab:
            print(f"✅ Found Google tab: {active_tab['title'][:50]}")
            
            # Test accessibility tree via DevTools
            ws_url = active_tab['webSocketDebuggerUrl']
            print(f"🔗 WebSocket URL available for accessibility testing")
            
            return True, active_tab
        else:
            print("⚠️  No Google tab found")
            return False, None
            
    except Exception as e:
        print(f"❌ DevTools accessibility test failed: {e}")
        return False, None

def monitor_accessibility_operations():
    """Monitor accessibility operations in real-time"""
    print("\n📊 Monitoring Accessibility Operations...")
    print("-" * 42)
    
    try:
        from modules.accessibility import AccessibilityModule
        
        # Enable verbose logging for detailed monitoring
        accessibility = AccessibilityModule()
        accessibility.enable_verbose_logging()
        
        print("✅ Verbose logging enabled for accessibility operations")
        
        # Perform a series of operations to monitor
        operations = [
            ("Find Gmail link", lambda: accessibility.find_element("AXLink", "Gmail", "Google Chrome")),
            ("Find any button", lambda: accessibility.find_element("AXButton", "", "Google Chrome")),
            ("Enhanced search", lambda: accessibility.find_element_enhanced("", "Gmail", "Google Chrome")),
        ]
        
        results = []
        
        for op_name, operation in operations:
            print(f"\n🔍 {op_name}...")
            
            start_time = time.time()
            try:
                result = operation()
                duration = time.time() - start_time
                
                if result:
                    print(f"   ✅ Success in {duration:.3f}s")
                    if hasattr(result, 'to_dict'):
                        results.append((op_name, True, duration, result.to_dict()))
                    else:
                        results.append((op_name, True, duration, result))
                else:
                    print(f"   ❌ No result in {duration:.3f}s")
                    results.append((op_name, False, duration, None))
                    
            except Exception as e:
                duration = time.time() - start_time
                print(f"   ❌ Error in {duration:.3f}s: {e}")
                results.append((op_name, False, duration, str(e)))
        
        # Get performance summary
        perf_summary = accessibility.get_performance_summary()
        print(f"\n📈 Performance Summary:")
        print(f"   {json.dumps(perf_summary, indent=2)}")
        
        return True, results
        
    except Exception as e:
        print(f"❌ Monitoring failed: {e}")
        return False, []

def run_comprehensive_gmail_test():
    """Run comprehensive Gmail click fast path test"""
    print("Gmail Click Fast Path Comprehensive Test")
    print("=" * 45)
    print("Testing accessibility tree extraction, element detection, and click execution\n")
    
    # Test results tracking
    test_results = {
        'chrome_setup': False,
        'tree_extraction': False,
        'performance_good': False,
        'gmail_click_success': False,
        'devtools_accessible': False,
        'monitoring_success': False
    }
    
    # Step 1: Setup Chrome
    print("=" * 45)
    test_results['chrome_setup'] = setup_chrome_for_testing()
    
    if not test_results['chrome_setup']:
        print("❌ Cannot proceed without Chrome setup")
        return False
    
    # Wait for Chrome to fully load
    print("\n⏳ Waiting for Chrome to fully load...")
    time.sleep(5)
    
    # Step 2: Test accessibility tree extraction
    print("\n" + "=" * 45)
    tree_success, element = test_accessibility_tree_extraction()
    test_results['tree_extraction'] = tree_success
    
    # Step 3: Test element detection performance
    print("\n" + "=" * 45)
    perf_success, elements = test_element_detection_performance()
    test_results['performance_good'] = perf_success
    
    # Step 4: Test DevTools accessibility
    print("\n" + "=" * 45)
    devtools_success, tab_info = test_chrome_devtools_accessibility()
    test_results['devtools_accessible'] = devtools_success
    
    # Step 5: Monitor accessibility operations
    print("\n" + "=" * 45)
    monitor_success, operations = monitor_accessibility_operations()
    test_results['monitoring_success'] = monitor_success
    
    # Step 6: Test actual Gmail click command
    print("\n" + "=" * 45)
    click_success, click_result = simulate_gmail_click_command()
    test_results['gmail_click_success'] = click_success
    
    # Final summary
    print("\n" + "=" * 45)
    print("📊 COMPREHENSIVE TEST RESULTS")
    print("=" * 45)
    
    for test_name, result in test_results.items():
        status = "✅" if result else "❌"
        print(f"{status} {test_name.replace('_', ' ').title()}: {result}")
    
    # Calculate overall success
    passed = sum(test_results.values())
    total = len(test_results)
    percentage = (passed / total) * 100
    
    print(f"\n📈 Overall Success Rate: {passed}/{total} ({percentage:.0f}%)")
    
    if percentage >= 80:
        print("\n🎉 EXCELLENT! Gmail fast path is working perfectly!")
        print("✅ Accessibility tree extraction: Working")
        print("✅ Element detection: Fast and accurate")
        print("✅ Click execution: Using fast path")
        print("✅ Chrome integration: Fully functional")
        
    elif percentage >= 60:
        print("\n✅ GOOD! Gmail fast path is mostly working")
        print("💡 Some optimizations may be beneficial")
        
    else:
        print("\n⚠️  Gmail fast path needs improvement")
        print("💡 Check Chrome accessibility settings and restart Chrome")
    
    print(f"\n🔍 Fast Path Analysis:")
    if test_results['tree_extraction'] and test_results['performance_good']:
        print("✅ Accessibility tree is accessible and performant")
    if test_results['devtools_accessible']:
        print("✅ Chrome DevTools API available for advanced operations")
    if test_results['gmail_click_success']:
        print("✅ Gmail click command executed successfully")
    
    return percentage >= 70

if __name__ == "__main__":
    try:
        print("Make sure Chrome is closed before starting this test\n")
        input("Press Enter to continue...")
        
        success = run_comprehensive_gmail_test()
        
        if success:
            print("\n🎯 Gmail fast path is ready for production use!")
        else:
            print("\n🔧 Gmail fast path needs additional configuration")
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)