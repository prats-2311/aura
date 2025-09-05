#!/usr/bin/env python3
"""
Chrome Accessibility Tree Monitor with Countdown Timer

This script monitors Chrome's accessibility tree in real-time to detect when
the "Native accessibility API support" setting takes effect.
"""

import sys
import time
import subprocess
from datetime import datetime, timedelta

def clear_screen():
    """Clear the terminal screen."""
    print("\033[2J\033[H", end="")

def print_header():
    """Print the header with current time."""
    now = datetime.now().strftime("%H:%M:%S")
    print("🔍 Chrome Accessibility Tree Monitor")
    print("=" * 50)
    print(f"⏰ Current Time: {now}")
    print()

def check_chrome_focus():
    """Check if Chrome is the focused application."""
    try:
        result = subprocess.run([
            'python3', '-c', 
            '''
from Cocoa import NSWorkspace
workspace = NSWorkspace.sharedWorkspace()
active_app = workspace.frontmostApplication()
if active_app:
    bundle_id = active_app.bundleIdentifier() or ""
    app_name = active_app.localizedName()
    is_chrome = "chrome" in bundle_id.lower()
    print(f"app:{app_name}")
    print(f"chrome:{is_chrome}")
else:
    print("app:Unknown")
    print("chrome:False")
'''
        ], capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            app_name = "Unknown"
            is_chrome = False
            
            for line in lines:
                if line.startswith("app:"):
                    app_name = line.split(":", 1)[1]
                elif line.startswith("chrome:"):
                    is_chrome = line.split(":", 1)[1] == "True"
            
            return is_chrome, app_name
        else:
            return False, "Unknown"
            
    except Exception as e:
        return False, f"Error: {e}"

def test_accessibility_tree():
    """Test if Chrome's accessibility tree is accessible."""
    try:
        sys.path.append('.')
        from modules.accessibility import AccessibilityModule
        
        acc = AccessibilityModule()
        
        # Get accessibility status
        status = acc.get_accessibility_status()
        permissions_granted = status.get('permissions_granted', False)
        api_initialized = status.get('api_initialized', False)
        
        # Test element detection
        test_searches = [
            ("", "Google"),
            ("", "Gmail"), 
            ("AXButton", "Google Search"),
            ("AXLink", "Gmail"),
            ("", "Search")
        ]
        
        elements_found = []
        total_confidence = 0
        
        for role, label in test_searches:
            result = acc.find_element_enhanced(role, label, None)
            if result.found:
                elements_found.append({
                    'label': label,
                    'role': role or 'any',
                    'confidence': result.confidence_score,
                    'matched_attribute': result.matched_attribute,
                    'search_time': result.search_time_ms
                })
                total_confidence += result.confidence_score
        
        avg_confidence = total_confidence / len(elements_found) if elements_found else 0
        
        return {
            'permissions_granted': permissions_granted,
            'api_initialized': api_initialized,
            'elements_found': len(elements_found),
            'total_elements_tested': len(test_searches),
            'elements_details': elements_found,
            'avg_confidence': avg_confidence,
            'accessibility_working': len(elements_found) > 0
        }
        
    except ImportError:
        return {
            'error': 'AURA modules not available',
            'accessibility_working': False
        }
    except Exception as e:
        return {
            'error': str(e),
            'accessibility_working': False
        }

def print_status(chrome_focused, app_name, accessibility_result, countdown):
    """Print the current status."""
    
    # Chrome focus status
    if chrome_focused:
        print("🌐 Chrome Status: ✅ FOCUSED")
    else:
        print(f"🌐 Chrome Status: ❌ NOT FOCUSED (Current: {app_name})")
        print("   📋 Please make Chrome the active window")
    
    print()
    
    # Accessibility status
    if 'error' in accessibility_result:
        print(f"🔧 Accessibility Status: ❌ ERROR")
        print(f"   Error: {accessibility_result['error']}")
    else:
        permissions = accessibility_result.get('permissions_granted', False)
        api_init = accessibility_result.get('api_initialized', False)
        elements_found = accessibility_result.get('elements_found', 0)
        total_tested = accessibility_result.get('total_elements_tested', 0)
        working = accessibility_result.get('accessibility_working', False)
        
        print("🔧 Accessibility Status:")
        print(f"   Permissions: {'✅' if permissions else '❌'} {permissions}")
        print(f"   API Ready: {'✅' if api_init else '❌'} {api_init}")
        print(f"   Elements Found: {'✅' if elements_found > 0 else '❌'} {elements_found}/{total_tested}")
        
        if working:
            print("   🎉 CHROME ACCESSIBILITY TREE IS WORKING!")
            avg_conf = accessibility_result.get('avg_confidence', 0)
            print(f"   📊 Average Confidence: {avg_conf:.2f}")
            
            print("\n   📋 Elements Detected:")
            for elem in accessibility_result.get('elements_details', []):
                print(f"      ✅ {elem['label']} ({elem['role']}) - {elem['confidence']:.2f} confidence")
        else:
            print("   ⏳ Waiting for Chrome accessibility tree to load...")
    
    print()
    
    # Countdown
    if countdown > 0:
        mins, secs = divmod(countdown, 60)
        print(f"⏱️  Monitoring: {mins:02d}:{secs:02d} remaining")
    else:
        print("⏱️  Monitoring: Time's up!")
    
    print()
    
    # Instructions
    if not chrome_focused:
        print("📋 Next Steps:")
        print("   1. Make Chrome the active window")
        print("   2. Go to google.com")
    elif not accessibility_result.get('accessibility_working', False):
        print("📋 Next Steps:")
        print("   1. Enable 'Native accessibility API support' in Chrome")
        print("   2. Restart Chrome if prompted")
        print("   3. Navigate to google.com")
    else:
        print("🎉 SUCCESS! Your enhanced fast path should now work!")
        print("📋 Test with AURA:")
        print("   - Say: 'Click on Gmail link'")
        print("   - Should complete in ~200ms instead of 27s!")

def main():
    """Run the Chrome accessibility monitor."""
    
    print("🔍 Chrome Accessibility Tree Monitor")
    print("=" * 50)
    print("This will monitor Chrome's accessibility tree for 5 minutes")
    print("Enable 'Native accessibility API support' in Chrome and watch!")
    print()
    print("Press Ctrl+C to stop monitoring")
    print()
    
    # Wait for user to be ready
    try:
        input("Press Enter to start monitoring...")
    except KeyboardInterrupt:
        print("\nMonitoring cancelled.")
        return
    
    # Monitor for 5 minutes (300 seconds)
    total_time = 300
    start_time = time.time()
    
    try:
        while True:
            current_time = time.time()
            elapsed = current_time - start_time
            countdown = max(0, total_time - int(elapsed))
            
            # Clear screen and show status
            clear_screen()
            print_header()
            
            # Check Chrome focus
            chrome_focused, app_name = check_chrome_focus()
            
            # Test accessibility tree
            accessibility_result = test_accessibility_tree()
            
            # Print status
            print_status(chrome_focused, app_name, accessibility_result, countdown)
            
            # Check if we found elements (success!)
            if accessibility_result.get('accessibility_working', False):
                print("🎊 CHROME ACCESSIBILITY TREE DETECTED!")
                print("🚀 Enhanced fast path is now ready!")
                
                # Show success for 10 seconds then exit
                for i in range(10, 0, -1):
                    print(f"\r✨ Exiting in {i} seconds... ", end="", flush=True)
                    time.sleep(1)
                print("\n")
                break
            
            # Check if time is up
            if countdown <= 0:
                print("⏰ Monitoring time completed.")
                print("💡 If accessibility tree is still not working:")
                print("   - Make sure 'Native accessibility API support' is enabled")
                print("   - Try restarting Chrome completely")
                print("   - Run this monitor again")
                break
            
            # Wait 2 seconds before next check
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Monitoring stopped by user.")
        print("💡 Run again anytime with: python chrome_accessibility_monitor.py")

if __name__ == "__main__":
    main()