#!/usr/bin/env python3
"""
Visual click test - shows where clicks are happening
"""

from modules.automation import AutomationModule
import time

def test_visual_clicks():
    """Test clicks with visual feedback"""
    print("👁️ Visual Click Test")
    print("=" * 25)
    
    print("This test will click at various locations to help you see where clicks are landing")
    print()
    
    automation = AutomationModule()
    
    # Test locations around the expected sign-in button area
    test_locations = [
        (200, 200, "Top-left area"),
        (400, 200, "Top-center area"),
        (600, 200, "Top-right area"),
        (200, 400, "Middle-left area"),
        (400, 400, "Center area"),
        (600, 400, "Middle-right area"),
        (363, 360, "Expected Sign In button"),
        (363, 340, "Above expected button"),
        (363, 380, "Below expected button"),
        (343, 360, "Left of expected button"),
        (383, 360, "Right of expected button"),
    ]
    
    print("🎯 Test locations:")
    for i, (x, y, desc) in enumerate(test_locations, 1):
        print(f"   {i:2d}. {desc}: ({x}, {y})")
    
    print("\n📋 Instructions:")
    print("• Watch your screen carefully")
    print("• Look for any visual feedback (menus, highlights, etc.)")
    print("• Note which clicks seem to hit interactive elements")
    print()
    
    input("Press Enter to start visual click test...")
    
    for i, (x, y, description) in enumerate(test_locations, 1):
        print(f"\n🎯 Test {i}/{len(test_locations)}: {description}")
        print(f"   Coordinates: ({x}, {y})")
        
        # Countdown
        for j in range(3, 0, -1):
            print(f"   Clicking in {j}...")
            time.sleep(1)
        
        try:
            click_action = {
                "action": "click",
                "coordinates": [x, y]
            }
            
            automation.execute_action(click_action)
            print("   ✅ Click executed")
            
            # Ask for feedback
            feedback = input("   What happened? (describe or press Enter for next): ").strip()
            if feedback:
                print(f"   📝 Feedback: {feedback}")
            
            if "sign" in feedback.lower() or "button" in feedback.lower() or "menu" in feedback.lower():
                print(f"   🎉 POTENTIAL HIT! Coordinates: ({x}, {y})")
            
        except Exception as e:
            print(f"   ❌ Click failed: {e}")
        
        # Brief pause between tests
        time.sleep(1)
    
    print("\n📊 Test completed!")
    print("Did any of the clicks hit the Sign In button or show visual feedback?")

def test_specific_coordinates():
    """Test specific coordinates provided by user"""
    print("\n🎯 Test Specific Coordinates")
    print("=" * 35)
    
    automation = AutomationModule()
    
    while True:
        try:
            print("\nEnter coordinates to test (or 'q' to quit):")
            x_input = input("X coordinate: ").strip()
            if x_input.lower() == 'q':
                break
            
            y_input = input("Y coordinate: ").strip()
            if y_input.lower() == 'q':
                break
            
            x = int(x_input)
            y = int(y_input)
            
            print(f"\n🎯 Testing click at ({x}, {y})")
            
            for i in range(3, 0, -1):
                print(f"   Clicking in {i}...")
                time.sleep(1)
            
            click_action = {
                "action": "click",
                "coordinates": [x, y]
            }
            
            automation.execute_action(click_action)
            print("   ✅ Click executed")
            
            result = input("   Did this click the Sign In button? (y/n): ").lower().strip()
            if result == 'y':
                print(f"   🎉 SUCCESS! Working coordinates: ({x}, {y})")
                break
            
        except ValueError:
            print("   ❌ Invalid coordinates")
        except Exception as e:
            print(f"   ❌ Click failed: {e}")

def main():
    """Main visual test"""
    print("👁️ Visual Click Testing Tool")
    print("=" * 35)
    
    print("This tool helps you see exactly where clicks are happening")
    print()
    
    print("Choose test:")
    print("1. Visual grid test (multiple locations)")
    print("2. Test specific coordinates")
    
    choice = input("\nChoice (1-2): ").strip()
    
    if choice == "1":
        test_visual_clicks()
    elif choice == "2":
        test_specific_coordinates()
    else:
        print("Invalid choice")

if __name__ == "__main__":
    main()