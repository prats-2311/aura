#!/usr/bin/env python3
"""
Interactive tool to find the exact coordinates of the sign-in button
"""

import subprocess
import time
from modules.automation import AutomationModule

def get_mouse_position_applescript():
    """Get current mouse position using AppleScript"""
    try:
        script = '''
        tell application "System Events"
            set mousePos to (do shell script "python3 -c \\"
                import Quartz
                pos = Quartz.NSEvent.mouseLocation()
                print(int(pos.x), int(pos.y))
            \\"")
            return mousePos
        end tell
        '''
        
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            coords = result.stdout.strip().split()
            if len(coords) == 2:
                return int(coords[0]), int(coords[1])
    except:
        pass
    
    return None, None

def test_click_at_coordinates(x, y):
    """Test clicking at specific coordinates"""
    automation = AutomationModule()
    
    try:
        click_action = {
            "action": "click",
            "coordinates": [x, y]
        }
        
        print(f"🎯 Clicking at ({x}, {y})...")
        automation.execute_action(click_action)
        print("✅ Click executed")
        return True
    except Exception as e:
        print(f"❌ Click failed: {e}")
        return False

def interactive_coordinate_finder():
    """Interactive tool to find button coordinates"""
    print("🎯 Interactive Coordinate Finder")
    print("=" * 40)
    
    print("📋 Instructions:")
    print("1. Position your mouse over the Sign In button")
    print("2. Press Enter to capture the coordinates")
    print("3. We'll test clicking at those coordinates")
    print("4. Repeat until we find the right spot")
    print()
    
    print("🌐 Make sure:")
    print("• Render login page is open and visible")
    print("• Browser window is in the foreground")
    print("• Sign In button is clearly visible")
    print()
    
    while True:
        input("Position mouse over Sign In button and press Enter...")
        
        # Try to get mouse position
        x, y = get_mouse_position_applescript()
        
        if x is None:
            print("❌ Could not get mouse position")
            # Ask user to input coordinates manually
            try:
                x = int(input("Enter X coordinate: "))
                y = int(input("Enter Y coordinate: "))
            except ValueError:
                print("Invalid coordinates")
                continue
        else:
            print(f"📍 Mouse position captured: ({x}, {y})")
        
        # Test the click
        print(f"\n🧪 Testing click at ({x}, {y})")
        
        # Countdown
        for i in range(3, 0, -1):
            print(f"   Clicking in {i}...")
            time.sleep(1)
        
        success = test_click_at_coordinates(x, y)
        
        if success:
            result = input("\n👀 Did the Sign In button get clicked? (y/n/q): ").lower().strip()
            
            if result == 'y':
                print(f"🎉 SUCCESS! Working coordinates: ({x}, {y})")
                print(f"💾 Save these coordinates: x={x}, y={y}")
                return x, y
            elif result == 'q':
                break
            else:
                print("⏭️ Let's try another position...")
        else:
            print("❌ Click execution failed")
        
        print()
    
    return None, None

def test_grid_around_area():
    """Test clicking in a grid around the expected button area"""
    print("\n🎯 Grid Search Around Button Area")
    print("=" * 40)
    
    # Expected area around the sign-in button
    center_x, center_y = 363, 360
    
    # Create a grid of test points
    offsets = [
        (0, 0),      # Center
        (-20, 0),    # Left
        (20, 0),     # Right
        (0, -20),    # Up
        (0, 20),     # Down
        (-20, -20),  # Top-left
        (20, -20),   # Top-right
        (-20, 20),   # Bottom-left
        (20, 20),    # Bottom-right
    ]
    
    print(f"Testing {len(offsets)} positions around ({center_x}, {center_y})")
    print("Make sure the Render login page is visible!")
    input("Press Enter to start grid test...")
    
    for i, (dx, dy) in enumerate(offsets):
        test_x = center_x + dx
        test_y = center_y + dy
        
        print(f"\n🧪 Test {i+1}/{len(offsets)}: ({test_x}, {test_y})")
        
        # Brief pause
        time.sleep(1)
        
        success = test_click_at_coordinates(test_x, test_y)
        
        if success:
            result = input("Did this click the Sign In button? (y/n/s to skip): ").lower().strip()
            
            if result == 'y':
                print(f"🎉 SUCCESS! Working coordinates: ({test_x}, {test_y})")
                return test_x, test_y
            elif result == 's':
                break
        
        time.sleep(0.5)  # Brief pause between tests
    
    return None, None

def main():
    """Main coordinate finding tool"""
    print("🔍 Sign-In Button Coordinate Finder")
    print("=" * 45)
    
    print("Choose method:")
    print("1. Interactive (position mouse manually)")
    print("2. Grid search (test area around expected location)")
    print("3. Manual coordinate input")
    
    choice = input("\nChoice (1-3): ").strip()
    
    if choice == "1":
        x, y = interactive_coordinate_finder()
    elif choice == "2":
        x, y = test_grid_around_area()
    elif choice == "3":
        try:
            x = int(input("Enter X coordinate: "))
            y = int(input("Enter Y coordinate: "))
            
            print(f"Testing coordinates ({x}, {y})...")
            success = test_click_at_coordinates(x, y)
            
            if success:
                result = input("Did this work? (y/n): ").lower().strip()
                if result == 'y':
                    print(f"🎉 SUCCESS! Working coordinates: ({x}, {y})")
                else:
                    x, y = None, None
            else:
                x, y = None, None
                
        except ValueError:
            print("Invalid coordinates")
            return
    else:
        print("Invalid choice")
        return
    
    if x is not None and y is not None:
        print(f"\n🎉 FOUND WORKING COORDINATES: ({x}, {y})")
        print("\n💡 Next steps:")
        print(f"   • Use these coordinates: x={x}, y={y}")
        print("   • The click mechanism is working!")
        print("   • The issue was coordinate accuracy")
    else:
        print("\n❌ Could not find working coordinates")
        print("\n🔍 Troubleshooting:")
        print("   • Make sure browser window is active")
        print("   • Check if button is actually visible")
        print("   • Try different browser zoom levels")
        print("   • Verify accessibility permissions")

if __name__ == "__main__":
    main()