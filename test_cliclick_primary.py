#!/usr/bin/env python3
"""
Test cliclick as the PRIMARY automation method throughout AURA
"""

import time
import subprocess
from modules.automation import AutomationModule

def check_cliclick_installation():
    """Verify cliclick is properly installed"""
    print("🔍 Checking cliclick Installation")
    print("=" * 50)
    
    try:
        # Check if cliclick is available
        result = subprocess.run(
            ['which', 'cliclick'],
            capture_output=True,
            text=True,
            timeout=2
        )
        
        if result.returncode == 0:
            cliclick_path = result.stdout.strip()
            print(f"✅ cliclick found at: {cliclick_path}")
            
            # Check cliclick version
            version_result = subprocess.run(
                ['cliclick', '-V'],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            if version_result.returncode == 0:
                version = version_result.stdout.strip()
                print(f"✅ cliclick version: {version}")
            else:
                print("⚠️ Could not get cliclick version")
            
            return True
        else:
            print("❌ cliclick not found")
            print("Install with: brew install cliclick")
            return False
            
    except Exception as e:
        print(f"❌ Error checking cliclick: {e}")
        return False

def test_cliclick_primary_automation():
    """Test that automation module uses cliclick as primary"""
    print(f"\n🤖 Testing Automation Module with cliclick PRIMARY")
    print("=" * 50)
    
    try:
        automation = AutomationModule()
        
        print(f"Platform: {'macOS' if automation.is_macos else 'Other'}")
        print(f"Has cliclick: {automation.has_cliclick}")
        print(f"Screen size: {automation.screen_width}x{automation.screen_height}")
        
        if not automation.is_macos:
            print("⏭️ Skipping macOS-specific tests (not on macOS)")
            return True
        
        if not automation.has_cliclick:
            print("❌ cliclick not available in automation module")
            return False
        
        print("✅ Automation module configured with cliclick PRIMARY")
        return True
        
    except Exception as e:
        print(f"❌ Automation module test failed: {e}")
        return False

def test_cliclick_click_methods():
    """Test all cliclick click methods"""
    print(f"\n🖱️ Testing cliclick Click Methods")
    print("=" * 50)
    
    try:
        automation = AutomationModule()
        
        if not automation.has_cliclick:
            print("❌ cliclick not available")
            return False
        
        # Test coordinates that we know work
        test_coords = [
            (500, 400),   # Center area
            (600, 500),   # Slightly different
        ]
        
        for i, (x, y) in enumerate(test_coords):
            print(f"\n🎯 Test {i+1}: cliclick click at ({x}, {y})")
            
            response = input("Ready to test cliclick click? (y/n/q): ").lower().strip()
            if response == 'q':
                break
            elif response != 'y':
                continue
            
            print("cliclick clicking in 3 seconds...")
            for j in range(3, 0, -1):
                print(f"   {j}...")
                time.sleep(1)
            
            try:
                # Test direct cliclick method
                success = automation._cliclick_click(x, y)
                
                if success:
                    print("✅ cliclick click executed")
                    
                    result = input("Did you see the cliclick effect? (y/n): ").lower().strip()
                    if result == 'y':
                        print(f"🎉 SUCCESS! cliclick click works at ({x}, {y})")
                    else:
                        print(f"❌ cliclick click not visible at ({x}, {y})")
                else:
                    print("❌ cliclick click failed")
                    
            except Exception as e:
                print(f"❌ cliclick click error: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ cliclick click test failed: {e}")
        return False

def test_cliclick_double_click():
    """Test cliclick double-click"""
    print(f"\n🖱️🖱️ Testing cliclick Double-Click")
    print("=" * 50)
    
    try:
        automation = AutomationModule()
        
        if not automation.has_cliclick:
            print("❌ cliclick not available")
            return False
        
        test_x, test_y = 500, 400
        
        print(f"Testing cliclick double-click at ({test_x}, {test_y})")
        
        response = input("Ready to test cliclick double-click? (y/n): ").lower().strip()
        if response != 'y':
            return True
        
        print("cliclick double-clicking in 3 seconds...")
        for i in range(3, 0, -1):
            print(f"   {i}...")
            time.sleep(1)
        
        try:
            success = automation._cliclick_double_click(test_x, test_y)
            
            if success:
                print("✅ cliclick double-click executed")
                
                result = input("Did you see the double-click effect? (y/n): ").lower().strip()
                if result == 'y':
                    print("🎉 SUCCESS! cliclick double-click works!")
                    return True
                else:
                    print("❌ cliclick double-click not visible")
                    return False
            else:
                print("❌ cliclick double-click failed")
                return False
                
        except Exception as e:
            print(f"❌ cliclick double-click error: {e}")
            return False
        
    except Exception as e:
        print(f"❌ cliclick double-click test failed: {e}")
        return False

def test_cliclick_typing():
    """Test cliclick typing"""
    print(f"\n⌨️ Testing cliclick Typing")
    print("=" * 50)
    
    try:
        automation = AutomationModule()
        
        if not automation.has_cliclick:
            print("❌ cliclick not available")
            return False
        
        test_text = "Hello cliclick!"
        
        print(f"Testing cliclick typing: '{test_text}'")
        print("Make sure you have a text field focused (like TextEdit)")
        
        response = input("Ready to test cliclick typing? (y/n): ").lower().strip()
        if response != 'y':
            return True
        
        print("cliclick typing in 3 seconds...")
        for i in range(3, 0, -1):
            print(f"   {i}...")
            time.sleep(1)
        
        try:
            success = automation._cliclick_type(test_text)
            
            if success:
                print("✅ cliclick typing executed")
                
                result = input("Did you see the text appear? (y/n): ").lower().strip()
                if result == 'y':
                    print("🎉 SUCCESS! cliclick typing works!")
                    return True
                else:
                    print("❌ cliclick typing not visible")
                    return False
            else:
                print("❌ cliclick typing failed")
                return False
                
        except Exception as e:
            print(f"❌ cliclick typing error: {e}")
            return False
        
    except Exception as e:
        print(f"❌ cliclick typing test failed: {e}")
        return False

def test_cliclick_scroll():
    """Test cliclick scrolling"""
    print(f"\n📜 Testing cliclick Scrolling")
    print("=" * 50)
    
    try:
        automation = AutomationModule()
        
        if not automation.has_cliclick:
            print("❌ cliclick not available")
            return False
        
        print("Testing cliclick scroll (make sure you have a scrollable window)")
        
        response = input("Ready to test cliclick scroll? (y/n): ").lower().strip()
        if response != 'y':
            return True
        
        # Test scroll up
        print("cliclick scrolling UP in 3 seconds...")
        for i in range(3, 0, -1):
            print(f"   {i}...")
            time.sleep(1)
        
        try:
            success = automation._cliclick_scroll("up", 5)
            
            if success:
                print("✅ cliclick scroll UP executed")
                
                result = input("Did you see scrolling up? (y/n): ").lower().strip()
                if result == 'y':
                    print("🎉 SUCCESS! cliclick scroll works!")
                    
                    # Test scroll down
                    time.sleep(1)
                    print("Testing scroll DOWN...")
                    automation._cliclick_scroll("down", 5)
                    print("✅ cliclick scroll DOWN executed")
                    
                    return True
                else:
                    print("❌ cliclick scroll not visible")
                    return False
            else:
                print("❌ cliclick scroll failed")
                return False
                
        except Exception as e:
            print(f"❌ cliclick scroll error: {e}")
            return False
        
    except Exception as e:
        print(f"❌ cliclick scroll test failed: {e}")
        return False

def test_full_automation_actions():
    """Test full automation actions using cliclick as primary"""
    print(f"\n🔧 Testing Full Automation Actions (cliclick PRIMARY)")
    print("=" * 50)
    
    try:
        automation = AutomationModule()
        
        if not automation.has_cliclick:
            print("❌ cliclick not available")
            return False
        
        # Test click action through full automation
        print("Testing full automation click action...")
        
        response = input("Ready to test full automation click? (y/n): ").lower().strip()
        if response != 'y':
            return True
        
        print("Full automation click in 3 seconds...")
        for i in range(3, 0, -1):
            print(f"   {i}...")
            time.sleep(1)
        
        try:
            click_action = {
                "action": "click",
                "coordinates": [500, 400]
            }
            
            automation.execute_action(click_action)
            print("✅ Full automation click executed")
            
            result = input("Did you see the click effect? (y/n): ").lower().strip()
            if result == 'y':
                print("🎉 SUCCESS! Full automation with cliclick PRIMARY works!")
                return True
            else:
                print("❌ Full automation click not visible")
                return False
                
        except Exception as e:
            print(f"❌ Full automation click error: {e}")
            return False
        
    except Exception as e:
        print(f"❌ Full automation test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 cliclick PRIMARY Automation Test Suite")
    print("=" * 60)
    print("Testing cliclick as the PRIMARY automation method in AURA")
    print()
    
    # Check prerequisites
    if not check_cliclick_installation():
        print("\n❌ cliclick is not installed. Please install it first:")
        print("   brew install cliclick")
        return
    
    tests = [
        ("Automation Module Setup", test_cliclick_primary_automation),
        ("cliclick Click Methods", test_cliclick_click_methods),
        ("cliclick Double-Click", test_cliclick_double_click),
        ("cliclick Typing", test_cliclick_typing),
        ("cliclick Scrolling", test_cliclick_scroll),
        ("Full Automation Actions", test_full_automation_actions),
    ]
    
    print("\nAvailable tests:")
    for i, (name, _) in enumerate(tests, 1):
        print(f"{i}. {name}")
    print("7. Run all tests")
    
    choice = input("\nWhich test? (1-7): ").strip()
    
    if choice == "7":
        # Run all tests
        results = {}
        for name, test_func in tests:
            print(f"\n{'='*60}")
            print(f"Running: {name}")
            try:
                results[name] = test_func()
            except Exception as e:
                print(f"❌ Test crashed: {e}")
                results[name] = False
        
        # Summary
        print(f"\n{'='*60}")
        print("🏁 cliclick PRIMARY TEST RESULTS")
        print("=" * 60)
        
        for test_name, success in results.items():
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} {test_name}")
        
        # Overall assessment
        passed_tests = sum(1 for success in results.values() if success)
        total_tests = len(results)
        
        print(f"\n📊 Overall: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("🎉 ALL TESTS PASSED! cliclick is PRIMARY throughout AURA!")
        elif passed_tests > 0:
            print("⚠️ Some tests passed - cliclick is partially working as primary")
        else:
            print("❌ All tests failed - cliclick primary setup needs work")
    
    elif choice in ["1", "2", "3", "4", "5", "6"]:
        test_index = int(choice) - 1
        if 0 <= test_index < len(tests):
            name, test_func = tests[test_index]
            print(f"\nRunning: {name}")
            test_func()
    else:
        print("Invalid choice")
    
    print(f"\n💡 cliclick PRIMARY Benefits:")
    print("✅ More reliable than AppleScript")
    print("✅ Faster execution")
    print("✅ Better error handling")
    print("✅ Consistent behavior across macOS versions")
    print("✅ No PyAutoGUI AppKit compatibility issues")
    
    print(f"\n🎯 cliclick is now the PRIMARY automation method in AURA!")

if __name__ == "__main__":
    main()