#!/usr/bin/env python3
"""
Test the real click functionality with the Render sign-in button.
"""

from modules.automation import AutomationModule
import time

def test_render_signin_click():
    """Test clicking on the Render sign-in button"""
    print("🎯 Testing real click on Render sign-in button...")
    
    try:
        # Initialize automation module
        automation = AutomationModule()
        print("   ✅ AutomationModule initialized")
        
        # Based on the screenshot, the Sign In button appears to be around coordinates (363, 360)
        # Let's use the center of the button area
        sign_in_x = 363
        sign_in_y = 360
        
        print(f"   🖱️  Attempting to click at ({sign_in_x}, {sign_in_y})")
        print("   ⚠️  Make sure the Render login page is visible!")
        
        # Give user time to position the window
        for i in range(3, 0, -1):
            print(f"   Clicking in {i} seconds...")
            time.sleep(1)
        
        # Create click action
        click_action = {
            "action": "click",
            "coordinates": [sign_in_x, sign_in_y]
        }
        
        # Execute the click
        automation.execute_action(click_action)
        print("   ✅ Click executed successfully!")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Click failed: {e}")
        return False

def main():
    """Run the real click test"""
    print("🧪 Real Click Test for Render Sign-In Button")
    print("=" * 50)
    
    # Ask for confirmation
    response = input("Make sure the Render login page is open and visible. Continue? (y/N): ").lower().strip()
    if response != 'y':
        print("Test cancelled.")
        return
    
    success = test_render_signin_click()
    
    if success:
        print("\n🎉 SUCCESS! The click was executed.")
        print("Check if the Sign In button was actually clicked on the Render page.")
    else:
        print("\n❌ FAILED! The click could not be executed.")

if __name__ == "__main__":
    main()