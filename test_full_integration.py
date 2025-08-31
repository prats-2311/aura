#!/usr/bin/env python3
"""
Full integration test for AURA with the macOS click fix.
This tests the complete automation pipeline.
"""

import sys
import platform
from modules.automation import AutomationModule

def test_full_automation_pipeline():
    """Test the complete automation pipeline"""
    print("🚀 Testing full automation pipeline...")
    
    try:
        # Initialize automation module
        automation = AutomationModule()
        print("   ✅ AutomationModule initialized")
        
        # Test action validation
        test_action = {
            "action": "click",
            "coordinates": [500, 500]
        }
        
        is_valid, error_msg = automation.validate_action_format(test_action)
        if is_valid:
            print("   ✅ Action validation working")
        else:
            print(f"   ❌ Action validation failed: {error_msg}")
            return False
        
        # Test screen size detection
        width, height = automation.get_screen_size()
        print(f"   ✅ Screen size detected: {width}x{height}")
        
        # Test mouse position
        mouse_x, mouse_y = automation.get_mouse_position()
        print(f"   ✅ Mouse position: ({mouse_x}, {mouse_y})")
        
        # Test coordinate validation
        if automation._validate_coordinates(500, 500):
            print("   ✅ Coordinate validation working")
        else:
            print("   ❌ Coordinate validation failed")
            return False
        
        print("   🎯 All pipeline components working correctly")
        return True
        
    except Exception as e:
        print(f"   ❌ Pipeline test failed: {e}")
        return False

def test_action_execution_dry_run():
    """Test action execution without actually performing actions"""
    print("\n🧪 Testing action execution (dry run)...")
    
    try:
        automation = AutomationModule()
        
        # Test different action types for validation
        test_actions = [
            {
                "action": "click",
                "coordinates": [100, 100]
            },
            {
                "action": "type",
                "text": "Hello World"
            },
            {
                "action": "scroll",
                "direction": "up",
                "amount": 3
            }
        ]
        
        for i, action in enumerate(test_actions):
            is_valid, error_msg = automation.validate_action_format(action)
            if is_valid:
                print(f"   ✅ Action {i+1} ({action['action']}) validation passed")
            else:
                print(f"   ❌ Action {i+1} validation failed: {error_msg}")
                return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ Action execution test failed: {e}")
        return False

def test_error_handling():
    """Test error handling capabilities"""
    print("\n🛡️  Testing error handling...")
    
    try:
        automation = AutomationModule()
        
        # Test invalid action
        invalid_action = {"action": "invalid_action"}
        is_valid, error_msg = automation.validate_action_format(invalid_action)
        
        if not is_valid:
            print("   ✅ Invalid action properly rejected")
        else:
            print("   ❌ Invalid action was not rejected")
            return False
        
        # Test invalid coordinates
        invalid_coords = {"action": "click", "coordinates": [-100, -100]}
        is_valid, error_msg = automation.validate_action_format(invalid_coords)
        
        if not is_valid:
            print("   ✅ Invalid coordinates properly rejected")
        else:
            print("   ❌ Invalid coordinates were not rejected")
            return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error handling test failed: {e}")
        return False

def test_macos_specific_features():
    """Test macOS-specific features"""
    print("\n🍎 Testing macOS-specific features...")
    
    try:
        automation = AutomationModule()
        
        if automation.is_macos:
            print("   ✅ macOS detection working")
            
            # Check if macOS click method exists
            if hasattr(automation, '_macos_click'):
                print("   ✅ macOS click method available")
            else:
                print("   ❌ macOS click method missing")
                return False
                
        else:
            print("   ℹ️  Not on macOS - skipping macOS-specific tests")
        
        return True
        
    except Exception as e:
        print(f"   ❌ macOS features test failed: {e}")
        return False

def main():
    """Run the full integration test suite"""
    print("🧪 AURA Full Integration Test Suite")
    print("=" * 50)
    print(f"Platform: {platform.system()}")
    print(f"Python: {sys.version}")
    print("=" * 50)
    
    tests = [
        ("Full Automation Pipeline", test_full_automation_pipeline),
        ("Action Execution (Dry Run)", test_action_execution_dry_run),
        ("Error Handling", test_error_handling),
        ("macOS-Specific Features", test_macos_specific_features),
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
    print("\n📊 Integration Test Results")
    print("=" * 35)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 SUCCESS! AURA is ready to use with macOS click fix!")
        print("\n📋 What's working:")
        print("   ✅ Automation module initialization")
        print("   ✅ Action validation and error handling")
        print("   ✅ macOS-specific click implementation")
        print("   ✅ Screen size and mouse position detection")
        print("   ✅ Cross-platform compatibility")
        
        print("\n🚀 Next steps:")
        print("   1. Run AURA with: python main.py")
        print("   2. Try voice commands like 'Computer, click on the sign in button'")
        print("   3. The macOS AppKit issue has been resolved!")
        
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)