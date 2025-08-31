#!/usr/bin/env python3
"""
Test clicking on macOS application elements
"""

from modules.automation import AutomationModule
import time
import subprocess

def get_app_info():
    """Get information about running applications"""
    try:
        result = subprocess.run(
            ['osascript', '-e', '''
            tell application "System Events"
                set appList to name of every application process whose visible is true
                return appList as string
            end tell
            '''],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            apps = result.stdout.strip().split(', ')
            return apps
        
    except Exception as e:
        print(f"Could not get app list: {e}")
    
    return []

def test_finder_click():
    """Test clicking in Finder (safe test)"""
    print("🗂️ Finder Click Test")
    print("=" * 25)
    
    print("📋 This will:")
    print("1. Open Finder if not already open")
    print("2. Click in the Finder window")
    print("3. This is a safe test - won't break anything")
    print()
    
    input("Press Enter to continue...")
    
    # Open Finder
    try:
        subprocess.run(['open', '-a', 'Finder'], check=True)
        print("✅ Finder opened")
        time.sleep(2)
    except Exception as e:
        print(f"⚠️ Could not open Finder: {e}")
    
    # Initialize automation
    automation = AutomationModule()
    print("✅ Automation module initialized")
    
    # Get screen size and click in upper area (Finder toolbar area)
    width, height = automation.get_screen_size()
    finder_x = width // 2
    finder_y = height // 4  # Upper portion of screen
    
    print(f"🎯 Will click in Finder area: ({finder_x}, {finder_y})")
    
    # Countdown
    for i in range(3, 0, -1):
        print(f"   Clicking in {i}...")
        time.sleep(1)
    
    try:
        click_action = {
            "action": "click",
            "coordinates": [finder_x, finder_y]
        }
        
        automation.execute_action(click_action)
        print("✅ Click executed in Finder!")
        
        return True
        
    except Exception as e:
        print(f"❌ Click failed: {e}")
        return False

def test_menu_bar_click():
    """Test clicking on menu bar (very safe)"""
    print("📋 Menu Bar Click Test")
    print("=" * 25)
    
    print("This will click on the Apple menu (top-left corner)")
    print("This is completely safe and will just open the Apple menu")
    print()
    
    input("Press Enter to continue...")
    
    # Initialize automation
    automation = AutomationModule()
    print("✅ Automation module initialized")
    
    # Apple menu is always at top-left
    apple_menu_x = 20
    apple_menu_y = 10
    
    print(f"🎯 Will click Apple menu: ({apple_menu_x}, {apple_menu_y})")
    
    # Countdown
    for i in range(3, 0, -1):
        print(f"   Clicking in {i}...")
        time.sleep(1)
    
    try:
        click_action = {
            "action": "click",
            "coordinates": [apple_menu_x, apple_menu_y]
        }
        
        automation.execute_action(click_action)
        print("✅ Click executed on Apple menu!")
        print("👀 You should see the Apple menu open")
        
        # Click elsewhere to close menu
        time.sleep(2)
        close_click = {
            "action": "click",
            "coordinates": [200, 200]
        }
        automation.execute_action(close_click)
        print("✅ Menu closed")
        
        return True
        
    except Exception as e:
        print(f"❌ Click failed: {e}")
        return False

def main():
    """Main test menu"""
    print("🧪 macOS Application Click Tests")
    print("=" * 40)
    
    print("Available tests:")
    print("1. Finder click test (safe)")
    print("2. Apple menu click test (very safe)")
    print("3. Show running applications")
    print()
    
    choice = input("Choose test (1-3): ").strip()
    
    if choice == "1":
        test_finder_click()
    elif choice == "2":
        test_menu_bar_click()
    elif choice == "3":
        apps = get_app_info()
        print("\n📱 Running applications:")
        for app in apps:
            print(f"   • {app}")
    else:
        print("Invalid choice")

if __name__ == "__main__":
    main()