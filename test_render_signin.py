#!/usr/bin/env python3
"""
Test clicking on the Render sign-in button specifically
"""

from modules.automation import AutomationModule
import time

def test_render_signin():
    """Test clicking the Render sign-in button"""
    print("🎯 Render Sign-In Button Test")
    print("=" * 40)
    
    print("📋 Setup Instructions:")
    print("1. Open your browser")
    print("2. Go to: https://dashboard.render.com/login")
    print("3. Make sure the sign-in page is visible")
    print("4. Position the browser window where you can see it")
    print()
    
    input("Press Enter when the Render login page is ready...")
    
    # Initialize automation
    automation = AutomationModule()
    print("✅ Automation module initialized")
    
    # Based on your screenshot, the Sign In button coordinates
    # You may need to adjust these based on your screen resolution
    signin_x = 363  # X coordinate of Sign In button
    signin_y = 360  # Y coordinate of Sign In button
    
    print(f"🎯 Target coordinates: ({signin_x}, {signin_y})")
    print("⚠️  About to click the Sign In button!")
    
    # Countdown
    for i in range(5, 0, -1):
        print(f"   Clicking in {i}...")
        time.sleep(1)
    
    try:
        click_action = {
            "action": "click",
            "coordinates": [signin_x, signin_y]
        }
        
        automation.execute_action(click_action)
        print("✅ Click executed!")
        print("👀 Check if the Sign In button was clicked")
        
        return True
        
    except Exception as e:
        print(f"❌ Click failed: {e}")
        return False

if __name__ == "__main__":
    test_render_signin()