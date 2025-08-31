#!/usr/bin/env python3
"""
Direct click test - Test clicking at specific coordinates
"""

from modules.automation import AutomationModule
import time

def test_direct_click():
    """Test clicking at a safe location"""
    print("🎯 Direct Click Test")
    print("=" * 30)
    
    # Initialize automation
    automation = AutomationModule()
    print("✅ Automation module initialized")
    
    # Get screen size
    width, height = automation.get_screen_size()
    print(f"📺 Screen size: {width}x{height}")
    
    # Calculate center of screen (safe location)
    center_x = width // 2
    center_y = height // 2
    
    print(f"🎯 Will click at center: ({center_x}, {center_y})")
    print("⚠️  This will perform an actual click!")
    
    # Countdown
    for i in range(3, 0, -1):
        print(f"   Clicking in {i}...")
        time.sleep(1)
    
    try:
        # Create and execute click action
        click_action = {
            "action": "click",
            "coordinates": [center_x, center_y]
        }
        
        automation.execute_action(click_action)
        print("✅ Click executed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Click failed: {e}")
        return False

if __name__ == "__main__":
    test_direct_click()