#!/usr/bin/env python3
"""
Simple Chrome Accessibility Verification
Tests Chrome accessibility without external dependencies.
"""

import subprocess
import json
import time
import os
import sys

def check_chrome_processes():
    """Check if Chrome is running with accessibility flags"""
    print("🔍 Checking Chrome processes...")
    
    try:
        # Check running Chrome processes
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        chrome_lines = [line for line in result.stdout.split('\n') if 'Google Chrome' in line or '/Chrome' in line]
        
        if chrome_lines:
            print(f"✅ Found {len(chrome_lines)} Chrome processes running")
            
            # Check for accessibility flags
            accessibility_flags = ['--enable-accessibility', '--force-renderer-accessibility']
            flags_found = []
            
            for line in chrome_lines:
                for flag in accessibility_flags:
                    if flag in line:
                        flags_found.append(flag)
            
            if flags_found:
                print(f"✅ Accessibility flags detected: {', '.join(set(flags_found))}")
                return True
            else:
                print("⚠️  No accessibility flags found in running Chrome processes")
                return False
        else:
            print("ℹ️  No Chrome processes currently running")
            return None
            
    except Exception as e:
        print(f"❌ Error checking processes: {e}")
        return False

def test_chrome_accessibility_api():
    """Test Chrome accessibility via AppleScript (macOS specific)"""
    print("\n🔍 Testing Chrome accessibility API...")
    
    applescript = '''
    tell application "System Events"
        try
            set chromeApp to first application process whose name is "Google Chrome"
            set chromeWindows to windows of chromeApp
            if (count of chromeWindows) > 0 then
                return "Chrome accessible via System Events"
            else
                return "Chrome running but no windows accessible"
            end if
        on error
            return "Chrome not accessible via System Events"
        end try
    end tell
    '''
    
    try:
        result = subprocess.run(['osascript', '-e', applescript], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            output = result.stdout.strip()
            print(f"✅ AppleScript test: {output}")
            return "accessible" in output.lower()
        else:
            print(f"❌ AppleScript failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("⚠️  AppleScript test timed out")
        return False
    except Exception as e:
        print(f"❌ AppleScript test error: {e}")
        return False

def test_chrome_devtools_accessibility():
    """Test if Chrome DevTools accessibility is available"""
    print("\n🔍 Testing Chrome DevTools accessibility...")
    
    try:
        import urllib.request
        import json
        
        # Try to connect to Chrome DevTools (if running with --remote-debugging-port)
        try:
            response = urllib.request.urlopen('http://localhost:9222/json', timeout=5)
            data = json.loads(response.read().decode())
            
            print(f"✅ Chrome DevTools accessible - {len(data)} tabs found")
            
            # Check if any tabs have accessibility info
            for tab in data[:3]:  # Check first 3 tabs
                if 'url' in tab and tab['url'].startswith('http'):
                    print(f"   - Tab: {tab['url'][:50]}...")
            
            return True
            
        except Exception as e:
            print(f"ℹ️  Chrome DevTools not accessible (normal if not started with debug port): {e}")
            return False
            
    except ImportError:
        print("ℹ️  urllib not available for DevTools test")
        return False

def launch_chrome_with_accessibility():
    """Launch Chrome with accessibility flags for testing"""
    print("\n🚀 Launching Chrome with accessibility flags...")
    
    chrome_paths = [
        '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
        '/usr/bin/google-chrome',
        '/usr/bin/chromium-browser'
    ]
    
    chrome_path = None
    for path in chrome_paths:
        if os.path.exists(path):
            chrome_path = path
            break
    
    if not chrome_path:
        print("❌ Chrome not found in standard locations")
        return False
    
    try:
        # Launch Chrome with accessibility flags
        cmd = [
            chrome_path,
            '--enable-accessibility',
            '--force-renderer-accessibility',
            '--remote-debugging-port=9222',
            '--new-window',
            'chrome://accessibility/'
        ]
        
        print(f"Launching: {' '.join(cmd)}")
        
        # Start Chrome in background
        process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        print("✅ Chrome launched with accessibility flags")
        print("ℹ️  Chrome should open to chrome://accessibility/ page")
        print("ℹ️  Check that 'Web accessibility' is enabled on that page")
        
        # Wait a moment for Chrome to start
        time.sleep(3)
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to launch Chrome: {e}")
        return False

def run_accessibility_verification():
    """Run complete accessibility verification"""
    print("Chrome Accessibility Verification for Aura Fast Path")
    print("=" * 55)
    
    results = {
        'chrome_running': False,
        'accessibility_flags': False,
        'system_accessibility': False,
        'devtools_accessible': False
    }
    
    # Test 1: Check running Chrome processes
    chrome_status = check_chrome_processes()
    if chrome_status is True:
        results['chrome_running'] = True
        results['accessibility_flags'] = True
    elif chrome_status is False:
        results['chrome_running'] = True
        results['accessibility_flags'] = False
    
    # Test 2: Test system accessibility
    if test_chrome_accessibility_api():
        results['system_accessibility'] = True
    
    # Test 3: Test DevTools accessibility
    if test_chrome_devtools_accessibility():
        results['devtools_accessible'] = True
    
    # If Chrome isn't running with proper flags, offer to launch it
    if not results['accessibility_flags']:
        print("\n" + "=" * 55)
        response = input("Would you like to launch Chrome with accessibility flags? (y/n): ")
        if response.lower() == 'y':
            launch_chrome_with_accessibility()
            
            # Re-test after launch
            time.sleep(2)
            if test_chrome_devtools_accessibility():
                results['devtools_accessible'] = True
    
    # Print summary
    print("\n" + "=" * 55)
    print("📊 ACCESSIBILITY VERIFICATION SUMMARY")
    print("=" * 55)
    
    for key, value in results.items():
        status = "✅" if value else "❌"
        print(f"{status} {key.replace('_', ' ').title()}: {value}")
    
    # Calculate overall score
    score = sum(results.values())
    total = len(results)
    percentage = (score / total) * 100
    
    print(f"\n📈 Overall Score: {score}/{total} ({percentage:.0f}%)")
    
    if percentage >= 75:
        print("\n🎉 Chrome accessibility is properly configured for Aura!")
        print("✅ Your fast path functionality should work correctly.")
    elif percentage >= 50:
        print("\n⚠️  Chrome accessibility is partially configured.")
        print("💡 Consider restarting Chrome with accessibility flags enabled.")
    else:
        print("\n❌ Chrome accessibility needs configuration.")
        print("💡 Please enable 'Web accessibility' in chrome://accessibility/")
    
    print("\n📋 Next Steps:")
    print("1. Ensure Chrome has 'Web accessibility' enabled in chrome://accessibility/")
    print("2. Enable 'Navigate pages with a text cursor' in chrome://settings/accessibility")
    print("3. Restart Chrome after making changes")
    print("4. Test Aura commands to verify fast path functionality")
    
    return percentage >= 75

if __name__ == "__main__":
    try:
        success = run_accessibility_verification()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)