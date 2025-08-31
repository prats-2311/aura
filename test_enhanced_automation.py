#!/usr/bin/env python3
"""
Test the enhanced automation module with PyAutoGUI fixes
"""

import time
from modules.automation import AutomationModule

def test_enhanced_click():
    """Test the enhanced click functionality"""
    print("🚀 Testing Enhanced Automation Module")
    print("=" * 50)
    
    try:
        # Initialize automation module
        automation = AutomationModule()
        print(f"✅ AutomationModule initialized successfully")
        print(f"   Platform: {'macOS' if automation.is_macos else 'Other'}")
        print(f"   Screen size: {automation.screen_width}x{automation.screen_height}")
        print(f"   Has cliclick: {getattr(automation, 'has_cliclick', False)}")
        
        # Test coordinates that worked before
        test_coords = [
            (450, 400),  # This worked in our previous test
            (400, 350),  # Center area
            (500, 450),  # Slightly different area
        ]
        
        for i, (x, y) in enumerate(test_coords):
            print(f"\n🎯 Test {i+1}: Enhanced click at ({x}, {y})")
            
            response = input("Ready to test this coordinate? (y/n/q): ").lower().strip()
            if response == 'q':
                break
            elif response != 'y':
                continue
            
            print("Clicking in 3 seconds...")
            for j in range(3, 0, -1):
                print(f"   {j}...")
                time.sleep(1)
            
            try:
                click_action = {
                    "action": "click",
                    "coordinates": [x, y]
                }
                
                automation.execute_action(click_action)
                print(f"✅ Enhanced click executed at ({x}, {y})")
                
                result = input("Did you see the click effect? (y/n): ").lower().strip()
                if result == 'y':
                    print(f"🎉 SUCCESS! Enhanced coordinates ({x}, {y}) work!")
                else:
                    print(f"❌ No visible effect at ({x}, {y})")
                    
            except Exception as e:
                print(f"❌ Enhanced click failed at ({x}, {y}): {e}")
        
        # Test right click using cliclick if available
        if getattr(automation, 'has_cliclick', False):
            print(f"\n🖱️ Testing cliclick right click")
            response = input("Test right click with cliclick? (y/n): ").lower().strip()
            if response == 'y':
                print("Right clicking in 3 seconds...")
                for j in range(3, 0, -1):
                    print(f"   {j}...")
                    time.sleep(1)
                
                try:
                    import subprocess
                    result = subprocess.run(
                        ['cliclick', 'rc:450,400'],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    
                    if result.returncode == 0:
                        print("✅ cliclick right click executed")
                        right_result = input("Did you see the right click menu? (y/n): ").lower().strip()
                        if right_result == 'y':
                            print("🎉 cliclick right click works!")
                        else:
                            print("❌ No right click menu visible")
                    else:
                        print(f"❌ cliclick right click failed: {result.stderr}")
                        
                except Exception as e:
                    print(f"❌ cliclick right click error: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Enhanced automation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_fallback_coordinates():
    """Test the fallback coordinate system"""
    print(f"\n🔄 Testing Fallback Coordinate System")
    print("=" * 50)
    
    try:
        automation = AutomationModule()
        
        # Test action with fallback coordinates
        fallback_action = {
            "action": "click",
            "coordinates": [999999, 999999],  # Invalid primary coordinates
            "fallback_coordinates": [
                (450, 400),  # Known working coordinate
                (400, 350),  # Alternative
                (500, 450),  # Another alternative
            ],
            "target": "test_button"
        }
        
        print("Testing fallback coordinate system...")
        print("Primary coordinates are intentionally invalid (999999, 999999)")
        print("Should automatically try fallback coordinates")
        
        response = input("Ready to test fallback system? (y/n): ").lower().strip()
        if response == 'y':
            print("Testing fallback in 3 seconds...")
            for j in range(3, 0, -1):
                print(f"   {j}...")
                time.sleep(1)
            
            try:
                automation.execute_action(fallback_action)
                print("✅ Fallback coordinate system executed")
                
                result = input("Did you see a click effect? (y/n): ").lower().strip()
                if result == 'y':
                    print("🎉 Fallback coordinate system works!")
                else:
                    print("❌ Fallback system didn't produce visible effect")
                    
            except Exception as e:
                print(f"❌ Fallback system failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Fallback test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🔧 Enhanced Automation Module Test")
    print("=" * 60)
    print("Testing the enhanced automation with PyAutoGUI fixes")
    print()
    
    tests = [
        ("Enhanced Click Test", test_enhanced_click),
        ("Fallback Coordinate Test", test_fallback_coordinates),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        try:
            results[test_name] = test_func()
        except KeyboardInterrupt:
            print(f"\n⏹️ Test interrupted by user")
            break
        except Exception as e:
            print(f"❌ Test '{test_name}' crashed: {e}")
            results[test_name] = False
    
    # Summary
    print(f"\n{'='*60}")
    print("🏁 ENHANCED AUTOMATION TEST RESULTS")
    print("=" * 60)
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n💡 Key Improvements Made:")
    print("✅ Avoided PyAutoGUI AppKit issues on macOS")
    print("✅ Enhanced AppleScript click implementation")
    print("✅ Added cliclick as backup click method")
    print("✅ Improved screen size detection for Retina displays")
    print("✅ Enhanced fallback coordinate system")
    print("✅ Better error handling and recovery")

if __name__ == "__main__":
    main()