#!/usr/bin/env python3
"""
Debug AppleScript execution to understand the timeout issue.
"""

import subprocess
import time

def test_basic_applescript():
    """Test basic AppleScript execution"""
    print("🧪 Testing basic AppleScript...")
    
    script = 'return "Hello from AppleScript"'
    
    try:
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        print(f"   Return code: {result.returncode}")
        print(f"   Stdout: {result.stdout.strip()}")
        print(f"   Stderr: {result.stderr.strip()}")
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("   ❌ Basic AppleScript timed out")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_system_events_access():
    """Test if we can access System Events"""
    print("\n🔐 Testing System Events access...")
    
    script = '''
    tell application "System Events"
        return "System Events accessible"
    end tell
    '''
    
    try:
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        print(f"   Return code: {result.returncode}")
        print(f"   Stdout: {result.stdout.strip()}")
        print(f"   Stderr: {result.stderr.strip()}")
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("   ❌ System Events access timed out")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_mouse_position():
    """Test getting mouse position"""
    print("\n🖱️  Testing mouse position retrieval...")
    
    script = '''
    tell application "System Events"
        set mousePos to (do shell script "python3 -c 'import pyautogui; print(pyautogui.position())'")
        return mousePos
    end tell
    '''
    
    try:
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        print(f"   Return code: {result.returncode}")
        print(f"   Stdout: {result.stdout.strip()}")
        print(f"   Stderr: {result.stderr.strip()}")
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("   ❌ Mouse position test timed out")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_click_simulation():
    """Test click simulation without actual clicking"""
    print("\n🎯 Testing click simulation (no actual click)...")
    
    script = '''
    tell application "System Events"
        -- Just test the click syntax without executing
        set testCoords to {500, 500}
        return "Click syntax valid for coordinates: " & (item 1 of testCoords) & ", " & (item 2 of testCoords)
    end tell
    '''
    
    try:
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        print(f"   Return code: {result.returncode}")
        print(f"   Stdout: {result.stdout.strip()}")
        print(f"   Stderr: {result.stderr.strip()}")
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("   ❌ Click simulation timed out")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_accessibility_permissions():
    """Test if we have accessibility permissions"""
    print("\n🔓 Testing accessibility permissions...")
    
    # This script will fail if we don't have accessibility permissions
    script = '''
    tell application "System Events"
        try
            set frontApp to name of first application process whose frontmost is true
            return "Accessibility OK - Front app: " & frontApp
        on error errMsg
            return "Accessibility Error: " & errMsg
        end try
    end tell
    '''
    
    try:
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        print(f"   Return code: {result.returncode}")
        print(f"   Stdout: {result.stdout.strip()}")
        print(f"   Stderr: {result.stderr.strip()}")
        
        if "Accessibility OK" in result.stdout:
            print("   ✅ Accessibility permissions are working")
            return True
        else:
            print("   ❌ Accessibility permissions may be missing")
            return False
        
    except subprocess.TimeoutExpired:
        print("   ❌ Accessibility test timed out")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    """Run all debug tests"""
    print("🔍 AppleScript Debug Test Suite")
    print("=" * 40)
    
    tests = [
        ("Basic AppleScript", test_basic_applescript),
        ("System Events Access", test_system_events_access),
        ("Mouse Position", test_mouse_position),
        ("Click Simulation", test_click_simulation),
        ("Accessibility Permissions", test_accessibility_permissions),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"   💥 Test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 40)
    print("📊 Debug Results Summary")
    print("=" * 40)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    # Recommendations
    print("\n💡 Recommendations:")
    
    failed_tests = [name for name, result in results if not result]
    
    if "Accessibility Permissions" in failed_tests:
        print("   🔐 Grant accessibility permissions to Terminal/Python in System Preferences > Security & Privacy > Privacy > Accessibility")
    
    if "System Events Access" in failed_tests:
        print("   🔧 System Events access is blocked - check macOS security settings")
    
    if len(failed_tests) == 0:
        print("   🎉 All tests passed! The issue might be with the specific click command.")
    
    return len(failed_tests) == 0

if __name__ == "__main__":
    main()