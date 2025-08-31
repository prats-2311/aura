#!/usr/bin/env python3
"""
Visual Click Debug Test

This will help us see exactly where clicks are landing
"""

import subprocess
import time

def test_click_with_visual_feedback():
    """Test clicks with visual feedback to see where they land"""
    print("🎯 Visual Click Debug Test")
    print("=" * 50)
    print("This test will:")
    print("1. Move the mouse to specific coordinates")
    print("2. Show you where the mouse is")
    print("3. Click at that location")
    print("4. Help identify if clicks are offset")
    print()
    
    test_coordinates = [
        (100, 100),   # Top-left area
        (500, 300),   # Mid-left area
        (1000, 500),  # Center area
        (1500, 800),  # Right area
    ]
    
    for i, (x, y) in enumerate(test_coordinates):
        print(f"\n🎯 Test {i+1}: Coordinates ({x}, {y})")
        
        response = input(f"Test coordinate ({x}, {y})? (y/n/q): ").lower().strip()
        if response == 'q':
            break
        elif response != 'y':
            continue
        
        print(f"Moving mouse to ({x}, {y}) in 3 seconds...")
        print("Watch where the mouse cursor goes!")
        
        for j in range(3, 0, -1):
            print(f"   {j}...")
            time.sleep(1)
        
        try:
            # Move mouse using cliclick (more reliable)
            move_result = subprocess.run(
                ['cliclick', f'm:{x},{y}'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if move_result.returncode == 0:
                print(f"✅ Mouse moved to ({x}, {y})")
                
                # Wait a moment for user to see
                time.sleep(1)
                
                # Ask user to confirm mouse position
                mouse_ok = input("Is the mouse cursor where you expected? (y/n): ").lower().strip()
                
                if mouse_ok == 'y':
                    print("Great! Now clicking at this position...")
                    time.sleep(1)
                    
                    # Click at current position
                    click_result = subprocess.run(
                        ['cliclick', f'c:{x},{y}'],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    
                    if click_result.returncode == 0:
                        print(f"✅ Click executed at ({x}, {y})")
                        
                        click_visible = input("Did you see any click effect? (y/n): ").lower().strip()
                        if click_visible == 'y':
                            print(f"🎉 SUCCESS! Click is visible at ({x}, {y})")
                        else:
                            print(f"❌ Click not visible at ({x}, {y})")
                    else:
                        print(f"❌ Click failed: {click_result.stderr}")
                else:
                    print(f"❌ Mouse position incorrect - there may be a coordinate offset issue")
            else:
                print(f"❌ Mouse move failed: {move_result.stderr}")
                
        except Exception as e:
            print(f"❌ Test failed: {e}")

def test_applescript_vs_cliclick():
    """Compare AppleScript vs cliclick behavior"""
    print(f"\n🔍 AppleScript vs cliclick Comparison")
    print("=" * 50)
    
    test_x, test_y = 800, 400  # Mid-screen position
    
    print(f"Testing both methods at ({test_x}, {test_y})")
    
    # Test 1: cliclick
    print(f"\n1️⃣ Testing cliclick method")
    response = input("Ready to test cliclick? (y/n): ").lower().strip()
    if response == 'y':
        print("cliclick clicking in 3 seconds...")
        for i in range(3, 0, -1):
            print(f"   {i}...")
            time.sleep(1)
        
        try:
            result = subprocess.run(
                ['cliclick', f'c:{test_x},{test_y}'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                print("✅ cliclick executed")
                cliclick_visible = input("Did you see the cliclick effect? (y/n): ").lower().strip()
            else:
                print(f"❌ cliclick failed: {result.stderr}")
                cliclick_visible = 'n'
        except Exception as e:
            print(f"❌ cliclick error: {e}")
            cliclick_visible = 'n'
    else:
        cliclick_visible = 'skip'
    
    # Test 2: AppleScript
    print(f"\n2️⃣ Testing AppleScript method")
    response = input("Ready to test AppleScript? (y/n): ").lower().strip()
    if response == 'y':
        print("AppleScript clicking in 3 seconds...")
        for i in range(3, 0, -1):
            print(f"   {i}...")
            time.sleep(1)
        
        try:
            applescript = f'''
            tell application "System Events"
                click at {{{test_x}, {test_y}}}
            end tell
            '''
            
            result = subprocess.run(
                ['osascript', '-e', applescript],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                print("✅ AppleScript executed")
                applescript_visible = input("Did you see the AppleScript effect? (y/n): ").lower().strip()
            else:
                print(f"❌ AppleScript failed: {result.stderr}")
                applescript_visible = 'n'
        except Exception as e:
            print(f"❌ AppleScript error: {e}")
            applescript_visible = 'n'
    else:
        applescript_visible = 'skip'
    
    # Summary
    print(f"\n📊 Comparison Results:")
    print(f"   cliclick: {'✅ Visible' if cliclick_visible == 'y' else '❌ Not visible' if cliclick_visible == 'n' else '⏭️ Skipped'}")
    print(f"   AppleScript: {'✅ Visible' if applescript_visible == 'y' else '❌ Not visible' if applescript_visible == 'n' else '⏭️ Skipped'}")

def test_screen_coordinate_mapping():
    """Test if there's a coordinate system mismatch"""
    print(f"\n🗺️ Screen Coordinate Mapping Test")
    print("=" * 50)
    
    print("This test checks if our coordinate system matches the actual screen")
    print("We'll click at the four corners and center")
    
    # Get screen size from our automation module
    try:
        from modules.automation import AutomationModule
        automation = AutomationModule()
        width = automation.screen_width
        height = automation.screen_height
        print(f"Detected screen size: {width}x{height}")
    except Exception as e:
        print(f"Failed to get screen size: {e}")
        width, height = 2560, 1600  # Fallback
    
    # Test coordinates: corners and center
    test_points = [
        ("Top-left", 50, 50),
        ("Top-right", width - 50, 50),
        ("Center", width // 2, height // 2),
        ("Bottom-left", 50, height - 50),
        ("Bottom-right", width - 50, height - 50),
    ]
    
    for name, x, y in test_points:
        print(f"\n📍 Testing {name}: ({x}, {y})")
        
        response = input(f"Test {name} corner? (y/n/q): ").lower().strip()
        if response == 'q':
            break
        elif response != 'y':
            continue
        
        print(f"Moving to {name} in 3 seconds...")
        for i in range(3, 0, -1):
            print(f"   {i}...")
            time.sleep(1)
        
        try:
            # Move first, then click
            move_result = subprocess.run(
                ['cliclick', f'm:{x},{y}'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if move_result.returncode == 0:
                print(f"✅ Moved to {name}")
                
                position_ok = input(f"Is mouse at the {name} of screen? (y/n): ").lower().strip()
                if position_ok == 'y':
                    print(f"✅ Coordinate mapping correct for {name}")
                else:
                    print(f"❌ Coordinate mapping incorrect for {name}")
                    actual_pos = input("Where is the mouse actually? (describe): ")
                    print(f"   Expected: {name} ({x}, {y})")
                    print(f"   Actual: {actual_pos}")
            else:
                print(f"❌ Failed to move to {name}: {move_result.stderr}")
                
        except Exception as e:
            print(f"❌ Error testing {name}: {e}")

def main():
    """Main debug function"""
    print("🔬 Visual Click Debug Suite")
    print("=" * 60)
    print("This will help diagnose exactly what's happening with clicks")
    print()
    
    tests = [
        ("Visual Click Test", test_click_with_visual_feedback),
        ("AppleScript vs cliclick", test_applescript_vs_cliclick),
        ("Coordinate Mapping", test_screen_coordinate_mapping),
    ]
    
    print("Available tests:")
    for i, (name, _) in enumerate(tests, 1):
        print(f"{i}. {name}")
    print("4. Run all tests")
    
    choice = input("\nWhich test? (1-4): ").strip()
    
    if choice == "1":
        test_click_with_visual_feedback()
    elif choice == "2":
        test_applescript_vs_cliclick()
    elif choice == "3":
        test_screen_coordinate_mapping()
    elif choice == "4":
        for name, test_func in tests:
            print(f"\n{'='*60}")
            print(f"Running: {name}")
            test_func()
    else:
        print("Invalid choice")
    
    print(f"\n🎯 Debug Summary:")
    print("Use the results above to identify:")
    print("• Whether clicks are happening at all")
    print("• If there's a coordinate offset issue")
    print("• Which click method works best")
    print("• If screen coordinate mapping is correct")

if __name__ == "__main__":
    main()