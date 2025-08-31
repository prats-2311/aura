#!/usr/bin/env python3
"""
Comprehensive Click Analysis Test

This script will test all click mechanisms and help diagnose the issue.
"""

import pyautogui
import subprocess
import time
import platform
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_pyautogui_basic():
    """Test basic PyAutoGUI functionality"""
    print("🔍 Testing PyAutoGUI Basic Functionality")
    print("=" * 50)
    
    try:
        # Get screen size
        screen_size = pyautogui.size()
        print(f"✅ Screen size: {screen_size}")
        
        # Get current mouse position
        current_pos = pyautogui.position()
        print(f"✅ Current mouse position: {current_pos}")
        
        # Test mouse movement
        print("\n🖱️ Testing mouse movement...")
        print("Moving mouse to center of screen in 3 seconds...")
        
        for i in range(3, 0, -1):
            print(f"   {i}...")
            time.sleep(1)
        
        center_x = screen_size.width // 2
        center_y = screen_size.height // 2
        
        pyautogui.moveTo(center_x, center_y, duration=1.0)
        new_pos = pyautogui.position()
        print(f"✅ Mouse moved to: {new_pos}")
        
        return True
        
    except Exception as e:
        print(f"❌ PyAutoGUI basic test failed: {e}")
        return False

def test_pyautogui_click():
    """Test PyAutoGUI click functionality"""
    print("\n🖱️ Testing PyAutoGUI Click")
    print("=" * 50)
    
    try:
        # Get current position
        current_pos = pyautogui.position()
        print(f"Current position: {current_pos}")
        
        # Test click at current position
        print("Testing click at current position in 3 seconds...")
        for i in range(3, 0, -1):
            print(f"   {i}...")
            time.sleep(1)
        
        pyautogui.click()
        print("✅ PyAutoGUI click executed")
        
        # Test right click
        print("\nTesting right click in 3 seconds...")
        for i in range(3, 0, -1):
            print(f"   {i}...")
            time.sleep(1)
        
        pyautogui.rightClick()
        print("✅ PyAutoGUI right click executed")
        
        return True
        
    except Exception as e:
        print(f"❌ PyAutoGUI click test failed: {e}")
        return False

def test_applescript_click():
    """Test AppleScript click functionality"""
    print("\n🍎 Testing AppleScript Click")
    print("=" * 50)
    
    if platform.system() != "Darwin":
        print("⏭️ Skipping AppleScript test (not on macOS)")
        return True
    
    try:
        # Get current mouse position first
        current_pos = pyautogui.position()
        x, y = current_pos.x, current_pos.y
        
        print(f"Testing AppleScript click at current position: ({x}, {y})")
        print("Clicking in 3 seconds...")
        
        for i in range(3, 0, -1):
            print(f"   {i}...")
            time.sleep(1)
        
        # Test basic AppleScript click
        applescript = f'''
        tell application "System Events"
            click at {{{x}, {y}}}
        end tell
        '''
        
        result = subprocess.run(
            ['osascript', '-e', applescript],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print("✅ AppleScript click executed successfully")
        else:
            print(f"❌ AppleScript click failed: {result.stderr}")
            return False
        
        # Test right click
        print("\nTesting AppleScript right click in 3 seconds...")
        for i in range(3, 0, -1):
            print(f"   {i}...")
            time.sleep(1)
        
        right_click_script = f'''
        tell application "System Events"
            -- Right click using control+click
            click at {{{x}, {y}}} with control down
        end tell
        '''
        
        result = subprocess.run(
            ['osascript', '-e', right_click_script],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print("✅ AppleScript right click executed successfully")
        else:
            print(f"❌ AppleScript right click failed: {result.stderr}")
        
        return True
        
    except Exception as e:
        print(f"❌ AppleScript test failed: {e}")
        return False

def test_cliclick():
    """Test cliclick if available"""
    print("\n⚡ Testing cliclick")
    print("=" * 50)
    
    try:
        # Check if cliclick is available
        which_result = subprocess.run(
            ['which', 'cliclick'],
            capture_output=True,
            text=True,
            timeout=2
        )
        
        if which_result.returncode != 0:
            print("⏭️ cliclick not available (install with: brew install cliclick)")
            return True
        
        print("✅ cliclick is available")
        
        # Get current position
        current_pos = pyautogui.position()
        x, y = current_pos.x, current_pos.y
        
        print(f"Testing cliclick at position: ({x}, {y})")
        print("Clicking in 3 seconds...")
        
        for i in range(3, 0, -1):
            print(f"   {i}...")
            time.sleep(1)
        
        # Test cliclick
        result = subprocess.run(
            ['cliclick', f'c:{x},{y}'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            print("✅ cliclick executed successfully")
        else:
            print(f"❌ cliclick failed: {result.stderr}")
        
        # Test right click
        print("\nTesting cliclick right click in 3 seconds...")
        for i in range(3, 0, -1):
            print(f"   {i}...")
            time.sleep(1)
        
        result = subprocess.run(
            ['cliclick', f'rc:{x},{y}'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            print("✅ cliclick right click executed successfully")
        else:
            print(f"❌ cliclick right click failed: {result.stderr}")
        
        return True
        
    except Exception as e:
        print(f"❌ cliclick test failed: {e}")
        return False

def test_automation_module():
    """Test our automation module"""
    print("\n🤖 Testing AURA Automation Module")
    print("=" * 50)
    
    try:
        from modules.automation import AutomationModule
        
        automation = AutomationModule()
        print(f"✅ AutomationModule initialized")
        print(f"   Platform: {'macOS' if automation.is_macos else 'Other'}")
        print(f"   Screen size: {automation.screen_width}x{automation.screen_height}")
        
        # Get current position for test
        current_pos = pyautogui.position()
        x, y = current_pos.x, current_pos.y
        
        print(f"\nTesting automation click at current position: ({x}, {y})")
        print("Clicking in 3 seconds...")
        
        for i in range(3, 0, -1):
            print(f"   {i}...")
            time.sleep(1)
        
        # Test click action
        click_action = {
            "action": "click",
            "coordinates": [x, y]
        }
        
        automation.execute_action(click_action)
        print("✅ Automation module click executed")
        
        return True
        
    except Exception as e:
        print(f"❌ Automation module test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_specific_coordinates():
    """Test clicking at specific coordinates"""
    print("\n🎯 Testing Specific Coordinates")
    print("=" * 50)
    
    # Test coordinates from our fallback system
    test_coords = [
        (400, 350),  # Center-ish
        (363, 360),  # Sign in button area
        (450, 400),  # Alternative area
    ]
    
    try:
        from modules.automation import AutomationModule
        automation = AutomationModule()
        
        for i, (x, y) in enumerate(test_coords):
            print(f"\n🎯 Test {i+1}: Clicking at ({x}, {y})")
            print("Make sure you can see the result of this click!")
            
            response = input("Ready to test this coordinate? (y/n/q): ").lower().strip()
            if response == 'q':
                break
            elif response != 'y':
                continue
            
            print("Clicking in 3 seconds...")
            for j in range(3, 0, -1):
                print(f"   {j}...")
                time.sleep(1)
            
            try:
                click_action = {
                    "action": "click",
                    "coordinates": [x, y]
                }
                
                automation.execute_action(click_action)
                print(f"✅ Click executed at ({x}, {y})")
                
                result = input("Did you see the click effect? (y/n): ").lower().strip()
                if result == 'y':
                    print(f"🎉 SUCCESS! Coordinates ({x}, {y}) work!")
                else:
                    print(f"❌ No visible effect at ({x}, {y})")
                    
            except Exception as e:
                print(f"❌ Click failed at ({x}, {y}): {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Coordinate test failed: {e}")
        return False

def main():
    """Run all click analysis tests"""
    print("🔬 AURA Click Analysis Test Suite")
    print("=" * 60)
    print("This will test all click mechanisms to diagnose the issue.")
    print("Make sure you have a visible window/desktop to see click effects!")
    print()
    
    input("Press Enter to start testing...")
    
    tests = [
        ("PyAutoGUI Basic", test_pyautogui_basic),
        ("PyAutoGUI Click", test_pyautogui_click),
        ("AppleScript Click", test_applescript_click),
        ("cliclick", test_cliclick),
        ("AURA Automation Module", test_automation_module),
        ("Specific Coordinates", test_specific_coordinates),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        try:
            results[test_name] = test_func()
        except KeyboardInterrupt:
            print(f"\n⏹️ Test interrupted by user")
            break
        except Exception as e:
            print(f"❌ Test '{test_name}' crashed: {e}")
            results[test_name] = False
    
    # Summary
    print(f"\n{'='*60}")
    print("🏁 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
    
    # Analysis
    print(f"\n📊 ANALYSIS:")
    
    if results.get("PyAutoGUI Basic", False):
        print("✅ PyAutoGUI is working for basic operations")
    else:
        print("❌ PyAutoGUI has basic issues - this is the root problem")
    
    if results.get("PyAutoGUI Click", False):
        print("✅ PyAutoGUI clicks are working")
    else:
        print("❌ PyAutoGUI clicks are failing")
    
    if results.get("AppleScript Click", False):
        print("✅ AppleScript clicks are working")
    else:
        print("❌ AppleScript clicks are failing")
    
    if results.get("AURA Automation Module", False):
        print("✅ AURA automation module is working")
    else:
        print("❌ AURA automation module has issues")
    
    print(f"\n💡 RECOMMENDATIONS:")
    
    if not results.get("PyAutoGUI Basic", False):
        print("1. Check PyAutoGUI installation: pip install pyautogui")
        print("2. Check macOS accessibility permissions")
        print("3. Try running with sudo (not recommended but for testing)")
    
    if not results.get("AppleScript Click", False):
        print("1. Check macOS System Preferences > Security & Privacy > Accessibility")
        print("2. Make sure Terminal/Python has accessibility permissions")
    
    if not results.get("cliclick", True):
        print("1. Install cliclick: brew install cliclick")
        print("2. This provides an alternative click mechanism")
    
    print(f"\n🎯 Next steps: Based on the results above, we can focus on the failing mechanisms.")

if __name__ == "__main__":
    main()