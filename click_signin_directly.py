#!/usr/bin/env python3
"""
Direct solution: Click the Render sign-in button without vision analysis
"""

from modules.automation import AutomationModule
import time

def click_signin_button():
    """Click the sign-in button directly using known coordinates"""
    print("🎯 Clicking Render Sign-In Button")
    print("=" * 40)
    
    # Initialize automation
    automation = AutomationModule()
    print("✅ Automation initialized")
    
    # Known coordinates for the Sign In button from your screenshot
    signin_coordinates = [
        (363, 360, "Main Sign In button"),
        (380, 360, "Slightly right"),
        (363, 350, "Slightly up"),
        (363, 370, "Slightly down")
    ]
    
    print("🎯 Available Sign In button locations:")
    for i, (x, y, desc) in enumerate(signin_coordinates, 1):
        print(f"   {i}. {desc}: ({x}, {y})")
    
    print("\n📋 Make sure:")
    print("   • Render login page is open and visible")
    print("   • Browser window is in the foreground")
    print("   • Sign In button is visible on screen")
    
    input("\nPress Enter when ready...")
    
    # Try each coordinate until one works
    for x, y, description in signin_coordinates:
        print(f"\n🎯 Trying: {description} at ({x}, {y})")
        
        try:
            click_action = {
                "action": "click",
                "coordinates": [x, y]
            }
            
            # Countdown
            for i in range(3, 0, -1):
                print(f"   Clicking in {i}...")
                time.sleep(1)
            
            # Execute click
            automation.execute_action(click_action)
            print("✅ Click executed!")
            
            # Check if it worked
            result = input("Did the Sign In button get clicked? (y/n/q to quit): ").lower().strip()
            
            if result == 'y':
                print(f"🎉 SUCCESS! Working coordinates: ({x}, {y})")
                print("💡 You can use these coordinates for future clicks")
                return True
            elif result == 'q':
                print("🛑 Stopping test")
                return False
            else:
                print("⏭️  Trying next coordinates...")
                continue
                
        except Exception as e:
            print(f"❌ Click failed: {e}")
            continue
    
    print("❌ None of the coordinates worked")
    return False

def create_custom_coordinates():
    """Let user input custom coordinates"""
    print("\n🎯 Custom Coordinates")
    print("=" * 25)
    
    print("To find exact coordinates:")
    print("1. Open browser developer tools (F12)")
    print("2. Right-click the Sign In button → Inspect")
    print("3. In console, type: $0.getBoundingClientRect()")
    print("4. Use the 'x' and 'y' values")
    
    try:
        x = int(input("\nEnter X coordinate: "))
        y = int(input("Enter Y coordinate: "))
        
        automation = AutomationModule()
        
        print(f"\n🎯 Testing custom coordinates: ({x}, {y})")
        
        for i in range(3, 0, -1):
            print(f"   Clicking in {i}...")
            time.sleep(1)
        
        click_action = {
            "action": "click",
            "coordinates": [x, y]
        }
        
        automation.execute_action(click_action)
        print("✅ Custom click executed!")
        
        return True
        
    except ValueError:
        print("❌ Invalid coordinates")
        return False
    except Exception as e:
        print(f"❌ Click failed: {e}")
        return False

def main():
    """Main function"""
    print("🚀 Direct Sign-In Button Clicker")
    print("=" * 40)
    print("This bypasses AURA's vision analysis and clicks directly")
    print()
    
    choice = input("Choose option:\n1. Try preset coordinates\n2. Use custom coordinates\nChoice (1/2): ").strip()
    
    if choice == "1":
        success = click_signin_button()
    elif choice == "2":
        success = create_custom_coordinates()
    else:
        print("Invalid choice")
        return
    
    if success:
        print("\n🎉 SUCCESS! The click mechanism is working!")
        print("\n💡 The issue with AURA is vision timeout, not clicking")
        print("   Solutions:")
        print("   • Fix LM Studio model performance")
        print("   • Increase vision timeout")
        print("   • Use direct coordinate mode")
    else:
        print("\n⚠️  If clicks aren't working, check:")
        print("   • Browser window is active and visible")
        print("   • Coordinates are correct for your screen resolution")
        print("   • macOS accessibility permissions are granted")

if __name__ == "__main__":
    main()