#!/usr/bin/env python3
"""
Comprehensive test of mouse functionality - PyAutoGUI vs AppleScript
"""

import subprocess
import time
import platform
import logging

# Set up logging to see what's happening
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_pyautogui_directly():
    """Test PyAutoGUI directly to see if it works"""
    print("🖱️ Testing PyAutoGUI Directly")
    print("=" * 35)
    
    try:
        import pyautogui
        print("✅ PyAutoGUI imported successfully")
        
        # Get current mouse position
        try:
            pos = pyautogui.position()
            print(f"📍 Current mouse position: {pos}")
        except Exception as e:
            print(f"❌ Failed to get mouse position: {e}")
            return False
        
        # Get screen size
        try:
            size = pyautogui.size()
            print(f"📺 Screen size: {size}")
        except Exception as e:
            print(f"❌ Failed to get screen size: {e}")
            return False
        
        # Test mouse movement
        print("\n🎯 Testing mouse movement...")
        test_x, test_y = 500, 400
        
        print(f"Moving mouse to ({test_x}, {test_y}) in 3 seconds...")
        for i in range(3, 0, -1):
            print(f"   {i}...")
            time.sleep(1)
        
        try:
            pyautogui.moveTo(test_x, test_y, duration=1.0)
            print("✅ Mouse movement executed")
            
            # Verify position
            new_pos = pyautogui.position()
            print(f"📍 New mouse position: {new_pos}")
            
            # Test click
            print("\n🖱️ Testing PyAutoGUI click in 2 seconds...")
            time.sleep(2)
            pyautogui.click()
            print("✅ PyAutoGUI click executed")
            
            return True
            
        except Exception as e:
            print(f"❌ PyAutoGUI mouse operations failed: {e}")
            return False
            
    except ImportError:
        print("❌ PyAutoGUI not available")
        return False
    except Exception as e:
        print(f"❌ PyAutoGUI test failed: {e}")
        return False

def test_applescript_mouse():
    """Test AppleScript mouse operations"""
    print("\n🍎 Testing AppleScript Mouse Operations")
    print("=" * 45)
    
    test_x, test_y = 500, 400
    
    # Test 1: Basic click
    print("🧪 Test 1: Basic AppleScript click")
    try:
        applescript = f'''
        tell application "System Events"
            click at {{{test_x}, {test_y}}}
        end tell
        '''
        
        print(f"Executing click at ({test_x}, {test_y}) in 3 seconds...")
        for i in range(3, 0, -1):
            print(f"   {i}...")
            time.sleep(1)
        
        result = subprocess.run(
            ['osascript', '-e', applescript],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        print(f"📊 Return code: {result.returncode}")
        print(f"📝 Stdout: '{result.stdout.strip()}'")
        print(f"📝 Stderr: '{result.stderr.strip()}'")
        
        if result.returncode == 0:
            print("✅ AppleScript click executed successfully")
        else:
            print("❌ AppleScript click failed")
            
    except Exception as e:
        print(f"❌ AppleScript click test failed: {e}")
    
    # Test 2: Mouse movement + click
    print("\n🧪 Test 2: AppleScript mouse movement + click")
    try:
        move_script = f'''
        tell application "System Events"
            -- Move mouse to position
            set mouseLoc to {{{test_x + 50}, {test_y + 50}}}
            -- Click at the position
            click at mouseLoc
        end tell
        '''
        
        print(f"Moving and clicking at ({test_x + 50}, {test_y + 50}) in 3 seconds...")
        for i in range(3, 0, -1):
            print(f"   {i}...")
            time.sleep(1)
        
        result = subprocess.run(
            ['osascript', '-e', move_script],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        print(f"📊 Return code: {result.returncode}")
        print(f"📝 Stdout: '{result.stdout.strip()}'")
        print(f"📝 Stderr: '{result.stderr.strip()}'")
        
        if result.returncode == 0:
            print("✅ AppleScript move+click executed successfully")
        else:
            print("❌ AppleScript move+click failed")
            
    except Exception as e:
        print(f"❌ AppleScript move+click test failed: {e}")
    
    # Test 3: Right click
    print("\n🧪 Test 3: AppleScript right click")
    try:
        right_click_script = f'''
        tell application "System Events"
            right click at {{{test_x}, {test_y}}}
        end tell
        '''
        
        print(f"Right clicking at ({test_x}, {test_y}) in 3 seconds...")
        for i in range(3, 0, -1):
            print(f"   {i}...")
            time.sleep(1)
        
        result = subprocess.run(
            ['osascript', '-e', right_click_script],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        print(f"📊 Return code: {result.returncode}")
        print(f"📝 Stdout: '{result.stdout.strip()}'")
        print(f"📝 Stderr: '{result.stderr.strip()}'")
        
        if result.returncode == 0:
            print("✅ AppleScript right click executed successfully")
        else:
            print("❌ AppleScript right click failed")
            
    except Exception as e:
        print(f"❌ AppleScript right click test failed: {e}")

def test_cliclick():
    """Test cliclick if available"""
    print("\n⚡ Testing cliclick")
    print("=" * 20)
    
    try:
        # Check if cliclick is available
        which_result = subprocess.run(
            ['which', 'cliclick'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if which_result.returncode != 0:
            print("❌ cliclick not installed")
            print("💡 Install with: brew install cliclick")
            return False
        
        print("✅ cliclick is available")
        
        # Test cliclick
        test_x, test_y = 500, 400
        
        print(f"Testing cliclick at ({test_x}, {test_y}) in 3 seconds...")
        for i in range(3, 0, -1):
            print(f"   {i}...")
            time.sleep(1)
        
        result = subprocess.run(
            ['cliclick', f'c:{test_x},{test_y}'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        print(f"📊 Return code: {result.returncode}")
        print(f"📝 Stdout: '{result.stdout.strip()}'")
        print(f"📝 Stderr: '{result.stderr.strip()}'")
        
        if result.returncode == 0:
            print("✅ cliclick executed successfully")
            return True
        else:
            print("❌ cliclick failed")
            return False
            
    except Exception as e:
        print(f"❌ cliclick test failed: {e}")
        return False

def test_automation_module():
    """Test our automation module"""
    print("\n🤖 Testing AURA Automation Module")
    print("=" * 40)
    
    try:
        from modules.automation import AutomationModule
        
        automation = AutomationModule()
        print("✅ AutomationModule initialized")
        
        # Check platform detection
        print(f"🖥️ Platform detected: {'macOS' if automation.is_macos else 'Other'}")
        
        # Test coordinate validation
        test_x, test_y = 500, 400
        is_valid = automation._validate_coordinates(test_x, test_y)
        print(f"✅ Coordinate validation ({test_x}, {test_y}): {is_valid}")
        
        # Test the click method directly
        print(f"\n🎯 Testing automation click at ({test_x}, {test_y})")
        
        click_action = {
            "action": "click",
            "coordinates": [test_x, test_y]
        }
        
        print("Executing automation click in 3 seconds...")
        for i in range(3, 0, -1):
            print(f"   {i}...")
            time.sleep(1)
        
        try:
            automation.execute_action(click_action)
            print("✅ Automation module click executed")
            return True
        except Exception as e:
            print(f"❌ Automation module click failed: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Automation module test failed: {e}")
        return False

def test_permissions():
    """Test macOS permissions"""
    print("\n🔐 Testing macOS Permissions")
    print("=" * 30)
    
    try:
        # Test accessibility permissions
        accessibility_script = '''
        tell application "System Events"
            try
                set frontApp to name of first application process whose frontmost is true
                return "Accessibility OK - Front app: " & frontApp
            on error errMsg
                return "Accessibility Error: " & errMsg
            end try
        end tell
        '''
        
        result = subprocess.run(
            ['osascript', '-e', accessibility_script],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        print(f"📊 Accessibility test result: {result.returncode}")
        print(f"📝 Output: {result.stdout.strip()}")
        
        if "Accessibility OK" in result.stdout:
            print("✅ Accessibility permissions are working")
        else:
            print("❌ Accessibility permissions may be missing")
            print("💡 Grant accessibility access to Terminal in System Preferences")
            
    except Exception as e:
        print(f"❌ Permission test failed: {e}")

def main():
    """Run comprehensive mouse tests"""
    print("🧪 Comprehensive Mouse Functionality Test")
    print("=" * 50)
    print(f"Platform: {platform.system()}")
    print(f"Platform version: {platform.platform()}")
    print()
    
    print("⚠️ WARNING: This will move your mouse and perform clicks!")
    print("Make sure you're ready and have a safe desktop environment.")
    print()
    
    response = input("Continue with mouse tests? (y/N): ").lower().strip()
    if response != 'y':
        print("Test cancelled.")
        return
    
    # Run all tests
    tests = [
        ("macOS Permissions", test_permissions),
        ("PyAutoGUI Direct", test_pyautogui_directly),
        ("AppleScript Mouse", test_applescript_mouse),
        ("cliclick", test_cliclick),
        ("AURA Automation Module", test_automation_module),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"🧪 RUNNING: {test_name}")
        print(f"{'='*60}")
        
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"💥 Test crashed: {e}")
            results[test_name] = False
        
        time.sleep(2)  # Brief pause between tests
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 TEST RESULTS SUMMARY")
    print(f"{'='*60}")
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    # Analysis
    print(f"\n{'='*60}")
    print("🔍 ANALYSIS")
    print(f"{'='*60}")
    
    if results.get("PyAutoGUI Direct"):
        print("✅ PyAutoGUI is working - AppKit issue is resolved")
    else:
        print("❌ PyAutoGUI has issues - need to use AppleScript")
    
    if results.get("AppleScript Mouse"):
        print("✅ AppleScript mouse operations work")
    else:
        print("❌ AppleScript mouse operations failing")
    
    if results.get("AURA Automation Module"):
        print("✅ AURA automation module is working")
    else:
        print("❌ AURA automation module has issues")
        
    print(f"\n💡 RECOMMENDATIONS:")
    if not any(results.values()):
        print("   🚨 No mouse methods are working - check permissions")
    elif results.get("AURA Automation Module"):
        print("   🎉 Everything is working! Issue might be elsewhere")
    else:
        print("   🔧 Individual methods work but automation module has issues")

if __name__ == "__main__":
    main()