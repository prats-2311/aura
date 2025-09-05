#!/usr/bin/env python3
"""
Simple Chrome Fast Path Test
Tests Chrome accessibility without complex dependencies.
"""

import subprocess
import time
import json
import os
import sys

def test_chrome_accessibility_enabled():
    """Test if Chrome accessibility is properly enabled"""
    print("🔍 Testing Chrome Accessibility Fast Path")
    print("=" * 45)
    
    results = {
        'chrome_running': False,
        'accessibility_flags': False,
        'chrome_accessible': False,
        'fast_path_ready': False
    }
    
    # Test 1: Check Chrome processes
    print("\n1. Checking Chrome processes...")
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        chrome_lines = [line for line in result.stdout.split('\n') if 'Google Chrome' in line]
        
        if chrome_lines:
            print(f"✅ Chrome is running ({len(chrome_lines)} processes)")
            results['chrome_running'] = True
            
            # Check for accessibility flags
            accessibility_flags = ['--enable-accessibility', '--force-renderer-accessibility']
            flags_found = []
            
            for line in chrome_lines:
                for flag in accessibility_flags:
                    if flag in line:
                        flags_found.append(flag)
            
            if flags_found:
                print(f"✅ Accessibility flags detected: {', '.join(set(flags_found))}")
                results['accessibility_flags'] = True
            else:
                print("⚠️  No accessibility flags found")
        else:
            print("❌ Chrome is not running")
            
    except Exception as e:
        print(f"❌ Error checking Chrome processes: {e}")
    
    # Test 2: Test Chrome accessibility via AppleScript
    print("\n2. Testing Chrome accessibility via system...")
    try:
        applescript = '''
        tell application "System Events"
            try
                set chromeApp to first application process whose name is "Google Chrome"
                set chromeWindows to windows of chromeApp
                if (count of chromeWindows) > 0 then
                    set firstWindow to first window of chromeApp
                    set windowTitle to title of firstWindow
                    return "SUCCESS: " & windowTitle
                else
                    return "Chrome running but no accessible windows"
                end if
            on error errorMessage
                return "ERROR: " & errorMessage
            end try
        end tell
        '''
        
        result = subprocess.run(['osascript', '-e', applescript], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            output = result.stdout.strip()
            if "SUCCESS:" in output:
                window_title = output.replace("SUCCESS: ", "")
                print(f"✅ Chrome window accessible: '{window_title[:50]}...'")
                results['chrome_accessible'] = True
            else:
                print(f"⚠️  Chrome accessibility limited: {output}")
        else:
            print(f"❌ Chrome not accessible: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Accessibility test failed: {e}")
    
    # Test 3: Test Chrome DevTools (if available)
    print("\n3. Testing Chrome DevTools accessibility...")
    try:
        import urllib.request
        
        response = urllib.request.urlopen('http://localhost:9222/json', timeout=3)
        data = json.loads(response.read().decode())
        
        print(f"✅ Chrome DevTools accessible - {len(data)} tabs")
        
        # Check for accessibility-related tabs
        accessibility_tabs = [tab for tab in data if 'accessibility' in tab.get('url', '').lower()]
        if accessibility_tabs:
            print(f"✅ Found {len(accessibility_tabs)} accessibility-related tabs")
        
    except Exception as e:
        print(f"ℹ️  Chrome DevTools not available: {e}")
    
    # Test 4: Test basic macOS accessibility
    print("\n4. Testing macOS accessibility permissions...")
    try:
        # Check if we can access System Events (basic accessibility test)
        applescript = '''
        tell application "System Events"
            try
                set appList to name of every application process
                return "SUCCESS: Found " & (count of appList) & " applications"
            on error errorMessage
                return "ERROR: " & errorMessage
            end try
        end tell
        '''
        
        result = subprocess.run(['osascript', '-e', applescript], 
                              capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0 and "SUCCESS:" in result.stdout:
            app_count = result.stdout.strip().replace("SUCCESS: Found ", "").replace(" applications", "")
            print(f"✅ macOS accessibility working - {app_count} apps accessible")
        else:
            print(f"❌ macOS accessibility limited: {result.stdout}")
            
    except Exception as e:
        print(f"❌ macOS accessibility test failed: {e}")
    
    # Calculate fast path readiness
    critical_tests = ['chrome_running', 'chrome_accessible']
    passed_critical = sum(1 for test in critical_tests if results[test])
    
    if passed_critical >= 2 and results['accessibility_flags']:
        results['fast_path_ready'] = True
    
    # Print summary
    print("\n" + "=" * 45)
    print("📊 FAST PATH READINESS SUMMARY")
    print("=" * 45)
    
    for key, value in results.items():
        status = "✅" if value else "❌"
        print(f"{status} {key.replace('_', ' ').title()}: {value}")
    
    # Calculate score
    score = sum(results.values())
    total = len(results)
    percentage = (score / total) * 100
    
    print(f"\n📈 Readiness Score: {score}/{total} ({percentage:.0f}%)")
    
    if results['fast_path_ready']:
        print("\n🎉 Chrome Fast Path is READY!")
        print("✅ Your Aura system should be able to use fast accessibility-based automation")
        print("\n🚀 Next steps:")
        print("   1. Test with a simple Aura command")
        print("   2. Try: python3 main.py")
        print("   3. Give it a web automation task")
    elif percentage >= 50:
        print("\n⚠️  Chrome Fast Path is PARTIALLY ready")
        print("💡 Recommendations:")
        if not results['chrome_running']:
            print("   • Start Google Chrome")
        if not results['accessibility_flags']:
            print("   • Restart Chrome (it should auto-enable accessibility)")
        if not results['chrome_accessible']:
            print("   • Check macOS accessibility permissions")
    else:
        print("\n❌ Chrome Fast Path needs setup")
        print("💡 Required actions:")
        print("   1. Start Google Chrome")
        print("   2. Go to chrome://accessibility/ and enable 'Web accessibility'")
        print("   3. Go to chrome://settings/accessibility and enable text cursor navigation")
        print("   4. Restart Chrome")
    
    return results['fast_path_ready']

def launch_chrome_for_testing():
    """Launch Chrome with accessibility for testing"""
    print("\n🚀 Would you like to launch Chrome with accessibility enabled?")
    response = input("This will help test the fast path functionality (y/n): ")
    
    if response.lower() != 'y':
        return False
    
    chrome_paths = [
        '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
    ]
    
    chrome_path = None
    for path in chrome_paths:
        if os.path.exists(path):
            chrome_path = path
            break
    
    if not chrome_path:
        print("❌ Chrome not found")
        return False
    
    try:
        cmd = [
            chrome_path,
            '--enable-accessibility',
            '--force-renderer-accessibility',
            '--remote-debugging-port=9222',
            '--new-window',
            'https://www.google.com'
        ]
        
        print("Launching Chrome with accessibility...")
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        print("✅ Chrome launched! Waiting for it to start...")
        time.sleep(3)
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to launch Chrome: {e}")
        return False

if __name__ == "__main__":
    print("Chrome Fast Path Verification for Aura")
    print("This test checks if Chrome accessibility is ready for fast automation\n")
    
    # Run the test
    ready = test_chrome_accessibility_enabled()
    
    # If not ready, offer to launch Chrome
    if not ready:
        if launch_chrome_for_testing():
            print("\nRe-testing after Chrome launch...")
            time.sleep(2)
            ready = test_chrome_accessibility_enabled()
    
    if ready:
        print("\n🎉 SUCCESS: Chrome Fast Path is ready for Aura!")
    else:
        print("\n⚠️  Chrome Fast Path needs additional setup")
    
    sys.exit(0 if ready else 1)