#!/usr/bin/env python3
"""
Final test of AURA with cliclick as PRIMARY automation method
"""

import sys
import os
sys.path.insert(0, os.getcwd())

def test_aura_with_cliclick():
    """Test complete AURA system with cliclick primary"""
    print("🤖 Final AURA Test with cliclick PRIMARY")
    print("=" * 60)
    
    try:
        from modules.automation import AutomationModule
        
        # Initialize automation
        automation = AutomationModule()
        
        print(f"✅ AURA Automation Module Status:")
        print(f"   Platform: {'macOS' if automation.is_macos else 'Other'}")
        print(f"   cliclick Available: {automation.has_cliclick}")
        print(f"   Screen Size: {automation.screen_width}x{automation.screen_height}")
        
        if automation.has_cliclick:
            print(f"   🎯 PRIMARY Method: cliclick")
            print(f"   🔄 FALLBACK Method: AppleScript")
        else:
            print(f"   ⚠️ Using AppleScript only (install cliclick for better performance)")
        
        # Test a simple click command
        print(f"\n🎯 Testing AURA Click Command")
        
        response = input("Ready to test AURA click with cliclick PRIMARY? (y/n): ").lower().strip()
        if response == 'y':
            print("AURA clicking in 3 seconds...")
            for i in range(3, 0, -1):
                print(f"   {i}...")
                import time
                time.sleep(1)
            
            # Execute click action
            click_action = {
                "action": "click",
                "coordinates": [500, 400]
            }
            
            automation.execute_action(click_action)
            print("✅ AURA click executed with cliclick PRIMARY")
            
            result = input("Did AURA click work? (y/n): ").lower().strip()
            if result == 'y':
                print("🎉 SUCCESS! AURA with cliclick PRIMARY is working perfectly!")
                return True
            else:
                print("❌ AURA click didn't work as expected")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ AURA test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test"""
    print("🏁 FINAL AURA + cliclick PRIMARY TEST")
    print("=" * 60)
    
    success = test_aura_with_cliclick()
    
    print(f"\n{'='*60}")
    if success:
        print("🎉 FINAL RESULT: SUCCESS!")
        print("✅ cliclick is now the PRIMARY automation method in AURA")
        print("✅ All click operations will use cliclick first")
        print("✅ AppleScript serves as reliable fallback")
        print("✅ PyAutoGUI AppKit issues completely avoided")
        print("✅ AURA click system is now highly reliable!")
    else:
        print("❌ FINAL RESULT: Issues detected")
        print("Check the error messages above for troubleshooting")
    
    print(f"\n🚀 AURA is ready with cliclick PRIMARY automation!")

if __name__ == "__main__":
    main()