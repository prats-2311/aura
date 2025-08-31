#!/usr/bin/env python3
"""
Quick diagnosis of click functionality
"""

from modules.automation import AutomationModule
import time

def test_simple_click():
    """Test the most basic click functionality"""
    print("🔧 Click Diagnosis Test")
    print("=" * 25)
    
    try:
        # Initialize automation
        automation = AutomationModule()
        print("✅ Automation module initialized")
        
        # Get screen info
        width, height = automation.get_screen_size()
        print(f"📺 Screen size: {width}x{height}")
        
        # Test coordinates validation
        test_x, test_y = 500, 400
        is_valid = automation._validate_coordinates(test_x, test_y)
        print(f"✅ Coordinate validation: {is_valid}")
        
        # Test the macOS click method directly
        print(f"🎯 Testing direct macOS click at ({test_x}, {test_y})")
        print("⚠️  This will click at the center-ish area of your screen!")
        
        for i in range(3, 0, -1):
            print(f"   Clicking in {i}...")
            time.sleep(1)
        
        # Call the macOS click method directly
        if hasattr(automation, '_macos_click'):
            result = automation._macos_click(test_x, test_y)
            print(f"📊 Direct macOS click result: {result}")
            
            if result:
                print("✅ macOS click method is working!")
            else:
                print("❌ macOS click method failed")
                
        else:
            print("❌ _macos_click method not found")
        
        return True
        
    except Exception as e:
        print(f"❌ Diagnosis failed: {e}")
        return False

def test_applescript_directly():
    """Test AppleScript execution directly"""
    print("\n🍎 Direct AppleScript Test")
    print("=" * 30)
    
    import subprocess
    
    try:
        # Test basic AppleScript
        print("🧪 Testing basic AppleScript...")
        
        script = '''
        tell application "System Events"
            return "AppleScript is working"
        end tell
        '''
        
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        print(f"📊 AppleScript result: {result.returncode}")
        print(f"📝 Output: {result.stdout.strip()}")
        
        if result.returncode == 0:
            print("✅ AppleScript is working")
            
            # Test click script (but don't actually click)
            print("\n🧪 Testing click script syntax...")
            
            click_script = '''
            tell application "System Events"
                -- Just test syntax, don't click
                set testCoords to {500, 400}
                return "Click script syntax OK for " & (item 1 of testCoords) & "," & (item 2 of testCoords)
            end tell
            '''
            
            click_result = subprocess.run(
                ['osascript', '-e', click_script],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            print(f"📊 Click script result: {click_result.returncode}")
            print(f"📝 Output: {click_result.stdout.strip()}")
            
            if click_result.returncode == 0:
                print("✅ Click script syntax is valid")
                return True
            else:
                print("❌ Click script has syntax errors")
                return False
        else:
            print("❌ AppleScript is not working")
            return False
            
    except Exception as e:
        print(f"❌ AppleScript test failed: {e}")
        return False

def main():
    """Run diagnosis tests"""
    print("🔍 AURA Click Functionality Diagnosis")
    print("=" * 45)
    
    print("This will help identify where the click issue is occurring:\n")
    
    # Test 1: Basic click functionality
    print("TEST 1: Basic Click Functionality")
    print("-" * 35)
    basic_result = test_simple_click()
    
    # Test 2: AppleScript functionality
    print("\nTEST 2: AppleScript Functionality")
    print("-" * 35)
    applescript_result = test_applescript_directly()
    
    # Summary
    print("\n" + "=" * 45)
    print("📊 DIAGNOSIS SUMMARY")
    print("=" * 45)
    
    if basic_result and applescript_result:
        print("✅ GOOD: Click mechanism is working")
        print("🔍 ISSUE: The problem is likely vision timeout")
        print("\n💡 SOLUTIONS:")
        print("   1. Use direct coordinate clicking (bypass vision)")
        print("   2. Fix vision timeout issue")
        print("   3. Check LM Studio model performance")
        
    elif applescript_result and not basic_result:
        print("⚠️  MIXED: AppleScript works but automation wrapper has issues")
        print("\n💡 SOLUTIONS:")
        print("   1. Check automation module implementation")
        print("   2. Debug coordinate validation")
        
    elif not applescript_result:
        print("❌ CRITICAL: AppleScript is not working")
        print("\n💡 SOLUTIONS:")
        print("   1. Check macOS permissions")
        print("   2. Grant accessibility access to Terminal")
        print("   3. Check System Events access")
        
    else:
        print("❌ UNKNOWN: Unexpected test results")

if __name__ == "__main__":
    main()