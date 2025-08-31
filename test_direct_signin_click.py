#!/usr/bin/env python3
"""
Direct test of clicking the Render sign-in button without vision analysis
"""

from modules.automation import AutomationModule
import time

def test_direct_signin_click():
    """Test clicking directly on the sign-in button coordinates"""
    print("🎯 Direct Sign-In Button Click Test")
    print("=" * 45)
    
    print("📋 Setup:")
    print("1. Make sure the Render login page is open and visible")
    print("2. This will click directly at the Sign In button coordinates")
    print("3. No vision analysis - just pure clicking")
    print()
    
    # Wait for user to set up
    input("Press Enter when the Render login page is ready and visible...")
    
    # Initialize automation
    automation = AutomationModule()
    print("✅ Automation module initialized")
    
    # Based on your screenshot, these are the Sign In button coordinates
    # The button appears to be around the center-bottom area
    signin_x = 363  # X coordinate from your screenshot
    signin_y = 360  # Y coordinate from your screenshot
    
    print(f"🎯 Target coordinates: ({signin_x}, {signin_y})")
    print("⚠️  About to click the Sign In button!")
    
    # Give user time to position cursor/check
    for i in range(5, 0, -1):
        print(f"   Clicking in {i} seconds...")
        time.sleep(1)
    
    try:
        # Test the click action directly
        print("🔄 Executing click...")
        
        click_action = {
            "action": "click",
            "coordinates": [signin_x, signin_y]
        }
        
        # Execute the click
        automation.execute_action(click_action)
        
        print("✅ Click command executed successfully!")
        print("👀 Check the browser - did the Sign In button get clicked?")
        print("   - Did a menu appear?")
        print("   - Did the page change?")
        print("   - Did anything happen at that location?")
        
        return True
        
    except Exception as e:
        print(f"❌ Click failed: {e}")
        print("🔍 This indicates an issue with the click mechanism itself")
        return False

def test_alternative_coordinates():
    """Test clicking at alternative coordinates if first attempt fails"""
    print("\n🎯 Alternative Coordinates Test")
    print("=" * 35)
    
    # Alternative coordinates based on typical button positions
    alternatives = [
        (363, 360, "Original coordinates"),
        (400, 350, "Slightly right and up"),
        (350, 370, "Slightly left and down"),
        (363, 340, "Same X, higher Y"),
        (363, 380, "Same X, lower Y")
    ]
    
    automation = AutomationModule()
    
    for x, y, description in alternatives:
        print(f"\n🎯 Testing: {description} ({x}, {y})")
        
        response = input(f"Try clicking at ({x}, {y})? (y/n/q): ").lower().strip()
        
        if response == 'q':
            break
        elif response == 'y':
            try:
                click_action = {
                    "action": "click",
                    "coordinates": [x, y]
                }
                
                automation.execute_action(click_action)
                print(f"✅ Clicked at ({x}, {y})")
                
                result = input("Did this click work? (y/n): ").lower().strip()
                if result == 'y':
                    print(f"🎉 Success! Working coordinates: ({x}, {y})")
                    return True
                    
            except Exception as e:
                print(f"❌ Click failed: {e}")
    
    return False

def main():
    """Main test function"""
    print("🧪 Direct Click Test for Render Sign-In")
    print("=" * 50)
    
    # First test with original coordinates
    success = test_direct_signin_click()
    
    if not success:
        print("\n🔄 First test failed. Let's try alternative approaches...")
        test_alternative_coordinates()
    
    print("\n📊 Test Summary:")
    print("- This test bypasses vision analysis completely")
    print("- It tests only the click mechanism")
    print("- If clicks work here but not in AURA, the issue is vision timeout")
    print("- If clicks don't work here, the issue is with AppleScript clicking")

if __name__ == "__main__":
    main()