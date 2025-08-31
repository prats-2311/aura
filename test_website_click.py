#!/usr/bin/env python3
"""
Interactive test for clicking on any website element
"""

from modules.automation import AutomationModule
import time

def get_click_coordinates():
    """Get coordinates from user input"""
    print("🎯 Click Coordinate Setup")
    print("=" * 30)
    
    print("How to find coordinates:")
    print("1. Open browser developer tools (F12)")
    print("2. Use the element inspector (click the arrow icon)")
    print("3. Hover over the button you want to click")
    print("4. Note the position or use browser console:")
    print("   - Right-click the element → Inspect")
    print("   - In console, type: $0.getBoundingClientRect()")
    print("   - Use the 'x' and 'y' values")
    print()
    
    try:
        x = int(input("Enter X coordinate: "))
        y = int(input("Enter Y coordinate: "))
        return x, y
    except ValueError:
        print("❌ Invalid coordinates. Using default center.")
        return 500, 400

def test_website_click():
    """Test clicking on any website element"""
    print("🌐 Website Click Test")
    print("=" * 25)
    
    print("📋 Setup Instructions:")
    print("1. Open the website you want to test")
    print("2. Find the button/link you want to click")
    print("3. Get its coordinates (see instructions below)")
    print()
    
    # Get target coordinates
    x, y = get_click_coordinates()
    
    print(f"\n🎯 Will click at: ({x}, {y})")
    print("⚠️  Make sure the target element is visible!")
    
    input("\nPress Enter when ready to click...")
    
    # Initialize automation
    automation = AutomationModule()
    print("✅ Automation module initialized")
    
    # Countdown
    for i in range(3, 0, -1):
        print(f"   Clicking in {i}...")
        time.sleep(1)
    
    try:
        click_action = {
            "action": "click",
            "coordinates": [x, y]
        }
        
        automation.execute_action(click_action)
        print("✅ Click executed!")
        print("👀 Check if the element was clicked")
        
        return True
        
    except Exception as e:
        print(f"❌ Click failed: {e}")
        return False

if __name__ == "__main__":
    test_website_click()