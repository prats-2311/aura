#!/usr/bin/env python3
"""
Test the complete AURA system with our click fixes
"""

import time
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.getcwd())

def test_aura_click_command():
    """Test AURA with a simple click command"""
    print("🤖 Testing Complete AURA System")
    print("=" * 50)
    
    try:
        # Import AURA components
        from orchestrator import Orchestrator
        from modules.audio import AudioModule
        from modules.reasoning import ReasoningModule
        from modules.automation import AutomationModule
        from modules.vision import VisionModule
        
        print("✅ All AURA modules imported successfully")
        
        # Initialize orchestrator
        orchestrator = Orchestrator()
        print("✅ Orchestrator initialized")
        
        # Test a simple click command without audio
        test_command = "Click at coordinates 450, 400"
        
        print(f"\n🎯 Testing command: '{test_command}'")
        print("This should click at (450, 400) which we know works")
        
        response = input("Ready to test AURA click? (y/n): ").lower().strip()
        if response != 'y':
            return False
        
        print("Executing AURA command in 3 seconds...")
        for i in range(3, 0, -1):
            print(f"   {i}...")
            time.sleep(1)
        
        try:
            # Process the command through AURA
            result = orchestrator.process_command(test_command)
            
            print(f"✅ AURA command processed")
            print(f"Result: {result}")
            
            click_result = input("Did you see the click effect? (y/n): ").lower().strip()
            if click_result == 'y':
                print("🎉 SUCCESS! Complete AURA system works!")
                return True
            else:
                print("❌ AURA command didn't produce visible click")
                return False
                
        except Exception as e:
            print(f"❌ AURA command failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
    except Exception as e:
        print(f"❌ AURA system test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_aura_with_vision():
    """Test AURA with vision analysis"""
    print(f"\n👁️ Testing AURA with Vision Analysis")
    print("=" * 50)
    
    try:
        from orchestrator import Orchestrator
        
        orchestrator = Orchestrator()
        
        # Test a command that requires vision
        test_command = "Click on the sign in button"
        
        print(f"Testing command: '{test_command}'")
        print("This will use vision analysis + fallback coordinates")
        
        response = input("Ready to test AURA with vision? (y/n): ").lower().strip()
        if response != 'y':
            return False
        
        print("Executing AURA vision command...")
        print("This may take up to 3 minutes due to vision analysis...")
        
        try:
            result = orchestrator.process_command(test_command)
            
            print(f"✅ AURA vision command processed")
            print(f"Result: {result}")
            
            vision_result = input("Did AURA successfully click something? (y/n): ").lower().strip()
            if vision_result == 'y':
                print("🎉 SUCCESS! AURA with vision works!")
                return True
            else:
                print("❌ AURA vision command didn't work as expected")
                return False
                
        except Exception as e:
            print(f"❌ AURA vision command failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
    except Exception as e:
        print(f"❌ AURA vision test failed: {e}")
        return False

def test_automation_module_directly():
    """Test just the automation module directly"""
    print(f"\n🔧 Testing Automation Module Directly")
    print("=" * 50)
    
    try:
        from modules.automation import AutomationModule
        
        automation = AutomationModule()
        print("✅ Automation module initialized")
        
        # Test the working coordinates
        test_action = {
            "action": "click",
            "coordinates": [450, 400]
        }
        
        print("Testing direct automation click...")
        
        response = input("Ready to test direct automation? (y/n): ").lower().strip()
        if response != 'y':
            return False
        
        print("Direct click in 3 seconds...")
        for i in range(3, 0, -1):
            print(f"   {i}...")
            time.sleep(1)
        
        try:
            automation.execute_action(test_action)
            print("✅ Direct automation click executed")
            
            direct_result = input("Did you see the direct click? (y/n): ").lower().strip()
            if direct_result == 'y':
                print("🎉 SUCCESS! Direct automation works!")
                return True
            else:
                print("❌ Direct automation click not visible")
                return False
                
        except Exception as e:
            print(f"❌ Direct automation failed: {e}")
            return False
        
    except Exception as e:
        print(f"❌ Automation module test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Complete AURA System Test Suite")
    print("=" * 60)
    print("Testing the complete AURA system with our click fixes")
    print()
    
    tests = [
        ("Direct Automation Module", test_automation_module_directly),
        ("AURA Click Command", test_aura_click_command),
        ("AURA with Vision", test_aura_with_vision),
    ]
    
    print("Available tests:")
    for i, (name, _) in enumerate(tests, 1):
        print(f"{i}. {name}")
    print("4. Run all tests")
    
    choice = input("\nWhich test? (1-4): ").strip()
    
    if choice == "1":
        test_automation_module_directly()
    elif choice == "2":
        test_aura_click_command()
    elif choice == "3":
        test_aura_with_vision()
    elif choice == "4":
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
        print("🏁 COMPLETE AURA TEST RESULTS")
        print("=" * 60)
        
        for test_name, success in results.items():
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} {test_name}")
        
        # Overall assessment
        passed_tests = sum(1 for success in results.values() if success)
        total_tests = len(results)
        
        print(f"\n📊 Overall: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("🎉 ALL TESTS PASSED! AURA click system is working!")
        elif passed_tests > 0:
            print("⚠️ Some tests passed - AURA is partially working")
        else:
            print("❌ All tests failed - AURA needs more work")
    else:
        print("Invalid choice")
    
    print(f"\n💡 Summary of Fixes Applied:")
    print("✅ Fixed PyAutoGUI AppKit compatibility issues")
    print("✅ Prioritized cliclick over AppleScript for reliability")
    print("✅ Enhanced screen size detection for Retina displays")
    print("✅ Improved fallback coordinate system")
    print("✅ Added comprehensive error handling")
    print("✅ Enhanced automation module with multiple click methods")
    
    print(f"\n🎯 Next Steps:")
    print("• Use find_signin_coordinates.py to get exact button coordinates")
    print("• Test with real applications and websites")
    print("• Fine-tune vision analysis timeout and fallback behavior")

if __name__ == "__main__":
    main()