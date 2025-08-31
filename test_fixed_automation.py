#!/usr/bin/env python3
"""
Test the fixed automation module with cliclick priority
"""

import time
from modules.automation import AutomationModule

def test_fixed_clicks():
    """Test the fixed click functionality"""
    print("🔧 Testing Fixed Automation Module")
    print("=" * 50)
    
    try:
        # Initialize automation module
        automation = AutomationModule()
        print(f"✅ AutomationModule initialized")
        print(f"   Platform: {'macOS' if automation.is_macos else 'Other'}")
        print(f"   Screen size: {automation.screen_width}x{automation.screen_height}")
        print(f"   Has cliclick: {getattr(automation, 'has_cliclick', False)}")
        
        # Test the sign-in button coordinates from our fallback system
        from config import FALLBACK_COORDINATES
        
        if "sign in" in FALLBACK_COORDINATES:
            signin_coords = FALLBACK_COORDINATES["sign in"]
            print(f"\n🎯 Testing Sign In button coordinates:")
            for i, coord in enumerate(signin_coords):
                print(f"   {i+1}. {coord}")
        
        # Test a few key coordinates
        test_coords = [
            (450, 400),   # This worked in our visual test
            (363, 360),   # Sign in button area
            (400, 350),   # Alternative area
        ]
        
        for i, (x, y) in enumerate(test_coords):
            print(f"\n🎯 Test {i+1}: Fixed click at ({x}, {y})")
            
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
                print(f"✅ Fixed click executed at ({x}, {y})")
                
                result = input("Did you see the click effect? (y/n): ").lower().strip()
                if result == 'y':
                    print(f"🎉 SUCCESS! Fixed click works at ({x}, {y})")
                else:
                    print(f"❌ No visible effect at ({x}, {y})")
                    
            except Exception as e:
                print(f"❌ Fixed click failed at ({x}, {y}): {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Fixed automation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_render_signin_button():
    """Test clicking the actual Render sign-in button"""
    print(f"\n🌐 Testing Render Sign-In Button")
    print("=" * 50)
    
    print("Make sure you have the Render login page open!")
    print("URL: https://dashboard.render.com/login")
    
    response = input("Is the Render login page visible? (y/n): ").lower().strip()
    if response != 'y':
        print("Please open the Render login page first")
        return False
    
    try:
        automation = AutomationModule()
        
        # Use our fallback coordinates for sign in
        from config import FALLBACK_COORDINATES
        
        if "sign in" in FALLBACK_COORDINATES:
            signin_coords = FALLBACK_COORDINATES["sign in"]
            
            print(f"Testing {len(signin_coords)} sign-in coordinates...")
            
            for i, (x, y) in enumerate(signin_coords):
                print(f"\n🎯 Attempt {i+1}/{len(signin_coords)}: ({x}, {y})")
                
                response = input(f"Try coordinate {i+1}? (y/n/q): ").lower().strip()
                if response == 'q':
                    break
                elif response != 'y':
                    continue
                
                print("Clicking sign-in button in 3 seconds...")
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
                    
                    result = input("Did this click the Sign In button? (y/n): ").lower().strip()
                    if result == 'y':
                        print(f"🎉 SUCCESS! Sign In button clicked at ({x}, {y})")
                        return True
                    else:
                        print(f"❌ Didn't click Sign In button at ({x}, {y})")
                        
                except Exception as e:
                    print(f"❌ Click failed at ({x}, {y}): {e}")
        
        return False
        
    except Exception as e:
        print(f"❌ Render sign-in test failed: {e}")
        return False

def test_double_click_and_type():
    """Test double-click and typing functionality"""
    print(f"\n⌨️ Testing Double-Click and Typing")
    print("=" * 50)
    
    try:
        automation = AutomationModule()
        
        # Test double-click
        print("Testing double-click...")
        response = input("Ready to test double-click at (500, 400)? (y/n): ").lower().strip()
        if response == 'y':
            print("Double-clicking in 3 seconds...")
            for i in range(3, 0, -1):
                print(f"   {i}...")
                time.sleep(1)
            
            try:
                double_click_action = {
                    "action": "double_click",
                    "coordinates": [500, 400]
                }
                
                automation.execute_action(double_click_action)
                print("✅ Double-click executed")
                
                double_result = input("Did you see double-click effect? (y/n): ").lower().strip()
                if double_result == 'y':
                    print("🎉 Double-click works!")
                else:
                    print("❌ Double-click not visible")
                    
            except Exception as e:
                print(f"❌ Double-click failed: {e}")
        
        # Test typing
        print("\nTesting typing...")
        response = input("Ready to test typing? (y/n): ").lower().strip()
        if response == 'y':
            test_text = "Hello AURA!"
            print(f"Typing '{test_text}' in 3 seconds...")
            for i in range(3, 0, -1):
                print(f"   {i}...")
                time.sleep(1)
            
            try:
                type_action = {
                    "action": "type",
                    "text": test_text
                }
                
                automation.execute_action(type_action)
                print("✅ Typing executed")
                
                type_result = input("Did you see the text appear? (y/n): ").lower().strip()
                if type_result == 'y':
                    print("🎉 Typing works!")
                else:
                    print("❌ Typing not visible")
                    
            except Exception as e:
                print(f"❌ Typing failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Double-click/typing test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🔧 Fixed Automation Module Test")
    print("=" * 60)
    print("Testing the automation module with cliclick priority")
    print()
    
    tests = [
        ("Fixed Click Test", test_fixed_clicks),
        ("Render Sign-In Button", test_render_signin_button),
        ("Double-Click and Typing", test_double_click_and_type),
    ]
    
    print("Available tests:")
    for i, (name, _) in enumerate(tests, 1):
        print(f"{i}. {name}")
    print("4. Run all tests")
    
    choice = input("\nWhich test? (1-4): ").strip()
    
    if choice == "1":
        test_fixed_clicks()
    elif choice == "2":
        test_render_signin_button()
    elif choice == "3":
        test_double_click_and_type()
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
        print("🏁 FIXED AUTOMATION TEST RESULTS")
        print("=" * 60)
        
        for test_name, success in results.items():
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} {test_name}")
    else:
        print("Invalid choice")
    
    print(f"\n💡 Key Fixes Applied:")
    print("✅ Prioritized cliclick over AppleScript")
    print("✅ Enhanced screen size detection")
    print("✅ Added cliclick support for all actions")
    print("✅ Improved error handling and fallbacks")
    print("✅ Fixed coordinate validation")

if __name__ == "__main__":
    main()