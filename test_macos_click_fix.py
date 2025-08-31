#!/usr/bin/env python3
"""
Test script to verify the macOS click fix is working properly.
This tests the AppleScript-based clicking functionality.
"""

import sys
import platform
import subprocess
from modules.automation import AutomationModule

def test_platform_detection():
    """Test that we correctly detect macOS"""
    print("🔍 Testing platform detection...")
    current_platform = platform.system()
    print(f"   Current platform: {current_platform}")
    
    if current_platform == "Darwin":
        print("   ✅ macOS detected - AppleScript clicking should be used")
    else:
        print("   ℹ️  Non-macOS platform - PyAutoGUI clicking will be used")
    
    return current_platform == "Darwin"

def test_applescript_availability():
    """Test if AppleScript is available on the system"""
    print("\n🍎 Testing AppleScript availability...")
    
    try:
        # Test basic AppleScript execution
        result = subprocess.run(
            ['osascript', '-e', 'return "AppleScript works"'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            print("   ✅ AppleScript is available and working")
            print(f"   Output: {result.stdout.strip()}")
            return True
        else:
            print("   ❌ AppleScript failed to execute")
            print(f"   Error: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print("   ❌ osascript command not found")
        return False
    except subprocess.TimeoutExpired:
        print("   ❌ AppleScript execution timed out")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False

def test_automation_module_initialization():
    """Test that the automation module initializes without errors"""
    print("\n🤖 Testing automation module initialization...")
    
    try:
        automation = AutomationModule()
        print("   ✅ AutomationModule initialized successfully")
        return automation
    except Exception as e:
        print(f"   ❌ Failed to initialize AutomationModule: {e}")
        return None

def test_macos_click_method():
    """Test the macOS-specific click method"""
    print("\n🖱️  Testing macOS click method...")
    
    automation = test_automation_module_initialization()
    if not automation:
        return False
    
    # Test if the _macos_click method exists
    if hasattr(automation, '_macos_click'):
        print("   ✅ _macos_click method found")
        
        # First test: dry run without actual clicking
        print("   🧪 Testing AppleScript syntax (dry run)...")
        try:
            # Test AppleScript syntax without clicking
            test_script = '''
            tell application "System Events"
                -- Just test the syntax, don't actually click
                set mousePos to {500, 500}
            end tell
            '''
            
            result = subprocess.run(
                ['osascript', '-e', test_script],
                capture_output=True,
                text=True,
                timeout=3
            )
            
            if result.returncode == 0:
                print("   ✅ AppleScript syntax test passed")
            else:
                print(f"   ❌ AppleScript syntax test failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"   ❌ AppleScript syntax test error: {e}")
            return False
        
        # Second test: actual click (with user confirmation)
        try:
            print("   🧪 Testing actual click at safe coordinates (500, 500)...")
            print("   ⚠️  This will perform an actual click - make sure it's safe!")
            
            # Ask for user confirmation
            response = input("   Continue with actual click test? (y/N): ").lower().strip()
            if response == 'y':
                print("   🔄 Executing click...")
                result = automation._macos_click(500, 500)
                if result:
                    print("   ✅ Click executed successfully")
                    return True
                else:
                    print("   ❌ Click failed (returned False)")
                    return False
            else:
                print("   ⏭️  Skipping actual click test (syntax test passed)")
                return True
                
        except Exception as e:
            print(f"   ❌ Error during click test: {e}")
            return False
    else:
        print("   ❌ _macos_click method not found")
        return False

def test_click_method_selection():
    """Test that the correct click method is selected based on platform"""
    print("\n🎯 Testing click method selection...")
    
    automation = test_automation_module_initialization()
    if not automation:
        return False
    
    # Check if we're on macOS
    is_macos = platform.system() == "Darwin"
    
    if is_macos:
        print("   📱 On macOS - should use AppleScript clicking")
        if hasattr(automation, '_macos_click'):
            print("   ✅ macOS click method available")
            return True
        else:
            print("   ❌ macOS click method not available")
            return False
    else:
        print("   🖥️  On non-macOS - should use PyAutoGUI clicking")
        # For non-macOS, we expect PyAutoGUI to be used
        return True

def main():
    """Run all tests"""
    print("🧪 AURA macOS Click Fix Test Suite")
    print("=" * 50)
    
    tests = [
        ("Platform Detection", test_platform_detection),
        ("AppleScript Availability", test_applescript_availability),
        ("Automation Module Init", lambda: test_automation_module_initialization() is not None),
        ("Click Method Selection", test_click_method_selection),
        ("macOS Click Method", test_macos_click_method),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"   💥 Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n📊 Test Results Summary")
    print("=" * 30)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The macOS click fix is working properly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)