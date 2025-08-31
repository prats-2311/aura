#!/usr/bin/env python3
"""
Interactive tool to find the exact coordinates of the Render sign-in button
"""

import subprocess
import time

def get_mouse_position():
    """Get current mouse position using cliclick"""
    try:
        result = subprocess.run(
            ['cliclick', 'p'],
            capture_output=True,
            text=True,
            timeout=2
        )
        
        if result.returncode == 0:
            # cliclick returns position like "1234,567"
            coords = result.stdout.strip().split(',')
            if len(coords) == 2:
                return int(coords[0]), int(coords[1])
        return None, None
    except Exception as e:
        print(f"Error getting mouse position: {e}")
        return None, None

def test_coordinate(x, y):
    """Test clicking at specific coordinates"""
    print(f"Testing click at ({x}, {y})...")
    
    try:
        result = subprocess.run(
            ['cliclick', f'c:{x},{y}'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            print(f"✅ Click executed at ({x}, {y})")
            return True
        else:
            print(f"❌ Click failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Click error: {e}")
        return False

def find_signin_button():
    """Interactive tool to find sign-in button coordinates"""
    print("🎯 Render Sign-In Button Coordinate Finder")
    print("=" * 60)
    print()
    print("Instructions:")
    print("1. Open the Render login page: https://dashboard.render.com/login")
    print("2. Position your mouse over the Sign In button")
    print("3. Press Enter to capture the coordinates")
    print("4. Test the coordinates to verify they work")
    print()
    
    # Wait for user to position mouse
    input("Position your mouse over the Sign In button and press Enter...")
    
    # Get current mouse position
    x, y = get_mouse_position()
    
    if x is None or y is None:
        print("❌ Could not get mouse position")
        return
    
    print(f"📍 Captured coordinates: ({x}, {y})")
    
    # Test the coordinates
    response = input("Test these coordinates? (y/n): ").lower().strip()
    if response == 'y':
        print("Testing in 3 seconds...")
        for i in range(3, 0, -1):
            print(f"   {i}...")
            time.sleep(1)
        
        success = test_coordinate(x, y)
        
        if success:
            result = input("Did this click the Sign In button? (y/n): ").lower().strip()
            if result == 'y':
                print(f"🎉 SUCCESS! Sign In button is at ({x}, {y})")
                
                # Update config file
                update_config = input("Update config.py with these coordinates? (y/n): ").lower().strip()
                if update_config == 'y':
                    update_fallback_coordinates(x, y)
                
                return x, y
            else:
                print("❌ Coordinates don't click the Sign In button")
        else:
            print("❌ Click failed")
    
    return None, None

def update_fallback_coordinates(x, y):
    """Update the config.py file with new coordinates"""
    try:
        # Read current config
        with open('config.py', 'r') as f:
            content = f.read()
        
        # Find the FALLBACK_COORDINATES section
        if 'FALLBACK_COORDINATES' in content:
            # Update the sign in coordinates
            new_coords = f"({x}, {y})"
            
            # Add the new coordinates to the beginning of the sign in list
            import re
            pattern = r'("sign in":\s*\[)([^\]]*)'
            
            def replace_coords(match):
                existing_coords = match.group(2).strip()
                if existing_coords and not existing_coords.endswith(','):
                    existing_coords += ','
                return f'{match.group(1)}\n        {new_coords},{existing_coords}'
            
            updated_content = re.sub(pattern, replace_coords, content)
            
            # Write back to file
            with open('config.py', 'w') as f:
                f.write(updated_content)
            
            print(f"✅ Updated config.py with coordinates ({x}, {y})")
        else:
            print("❌ Could not find FALLBACK_COORDINATES in config.py")
    
    except Exception as e:
        print(f"❌ Error updating config: {e}")

def scan_area_around_point():
    """Scan area around a point to find clickable elements"""
    print("\n🔍 Area Scanning Mode")
    print("=" * 40)
    
    # Get center point
    input("Position mouse at center of search area and press Enter...")
    center_x, center_y = get_mouse_position()
    
    if center_x is None:
        print("❌ Could not get mouse position")
        return
    
    print(f"📍 Scanning around ({center_x}, {center_y})")
    
    # Define scan pattern (grid around center point)
    scan_radius = 50
    scan_step = 10
    
    found_coordinates = []
    
    for dx in range(-scan_radius, scan_radius + 1, scan_step):
        for dy in range(-scan_radius, scan_radius + 1, scan_step):
            test_x = center_x + dx
            test_y = center_y + dy
            
            print(f"Testing ({test_x}, {test_y})...", end=" ")
            
            # Quick test click
            try:
                result = subprocess.run(
                    ['cliclick', f'c:{test_x},{test_y}'],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                
                if result.returncode == 0:
                    print("✅")
                    
                    # Ask user if this worked
                    worked = input(f"Did ({test_x}, {test_y}) click the Sign In button? (y/n/s=skip): ").lower().strip()
                    if worked == 'y':
                        print(f"🎉 Found working coordinates: ({test_x}, {test_y})")
                        found_coordinates.append((test_x, test_y))
                        return test_x, test_y
                    elif worked == 's':
                        break
                else:
                    print("❌")
            except Exception:
                print("❌")
            
            time.sleep(0.1)  # Small delay between clicks
    
    if found_coordinates:
        print(f"Found {len(found_coordinates)} working coordinates:")
        for coord in found_coordinates:
            print(f"  • {coord}")
    else:
        print("No working coordinates found in scan area")

def manual_coordinate_entry():
    """Allow manual entry of coordinates to test"""
    print("\n✏️ Manual Coordinate Entry")
    print("=" * 40)
    
    try:
        x = int(input("Enter X coordinate: "))
        y = int(input("Enter Y coordinate: "))
        
        print(f"Testing manual coordinates ({x}, {y})...")
        
        response = input("Ready to test? (y/n): ").lower().strip()
        if response == 'y':
            print("Testing in 3 seconds...")
            for i in range(3, 0, -1):
                print(f"   {i}...")
                time.sleep(1)
            
            success = test_coordinate(x, y)
            
            if success:
                result = input("Did this click the Sign In button? (y/n): ").lower().strip()
                if result == 'y':
                    print(f"🎉 SUCCESS! Manual coordinates ({x}, {y}) work!")
                    
                    update_config = input("Update config.py? (y/n): ").lower().strip()
                    if update_config == 'y':
                        update_fallback_coordinates(x, y)
                    
                    return x, y
    
    except ValueError:
        print("❌ Invalid coordinates entered")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    return None, None

def main():
    """Main coordinate finder"""
    print("🎯 Render Sign-In Button Coordinate Finder")
    print("=" * 60)
    
    while True:
        print("\nOptions:")
        print("1. Find coordinates by mouse position")
        print("2. Scan area around point")
        print("3. Manual coordinate entry")
        print("4. Exit")
        
        choice = input("\nChoice (1-4): ").strip()
        
        if choice == "1":
            coords = find_signin_button()
            if coords[0] is not None:
                print(f"✅ Found working coordinates: {coords}")
                break
        elif choice == "2":
            coords = scan_area_around_point()
            if coords:
                print(f"✅ Found working coordinates: {coords}")
                break
        elif choice == "3":
            coords = manual_coordinate_entry()
            if coords and coords[0] is not None:
                print(f"✅ Found working coordinates: {coords}")
                break
        elif choice == "4":
            break
        else:
            print("Invalid choice")
    
    print("\n🎯 Coordinate finding complete!")
    print("The working coordinates have been identified and can be used in AURA.")

if __name__ == "__main__":
    main()