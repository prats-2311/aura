#!/usr/bin/env python3
"""
Simple test to verify cliclick Return key functionality.
"""

import subprocess
import time

def test_basic_cliclick():
    """Test basic cliclick functionality."""
    
    print("🧪 Basic cliclick Test")
    print("=" * 30)
    print("Open TextEdit or any text editor and focus on it.")
    print("Press Enter when ready...")
    input()
    
    print("Testing sequence:")
    print("1. Type 'Line 1'")
    print("2. Press Return")
    print("3. Type 'Line 2'")
    print("4. Press Return") 
    print("5. Type 'Line 3'")
    print()
    
    commands = [
        (['cliclick', 't:Line 1'], "Type 'Line 1'"),
        (['cliclick', 'kp:return'], "Press Return"),
        (['cliclick', 't:Line 2'], "Type 'Line 2'"),
        (['cliclick', 'kp:return'], "Press Return"),
        (['cliclick', 't:Line 3'], "Type 'Line 3'"),
    ]
    
    for i, (cmd, description) in enumerate(commands):
        print(f"Step {i+1}: {description}")
        print(f"Command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                print(f"   ✅ SUCCESS")
            else:
                print(f"   ❌ FAILED: {result.stderr}")
                
        except Exception as e:
            print(f"   ❌ EXCEPTION: {e}")
        
        time.sleep(1)  # 1 second between commands
        print()
    
    print("Test completed!")
    print("Check your text editor:")
    print("- Do you see 3 separate lines?")
    print("- Or is everything on one line?")
    
    response = input("Did you see 3 separate lines? (y/n): ").lower().strip()
    return response.startswith('y')

def main():
    """Run the basic test."""
    
    result = test_basic_cliclick()
    
    print(f"\n🎯 RESULT: {'✅ PASS' if result else '❌ FAIL'}")
    
    if result:
        print("✅ cliclick Return key works correctly!")
        print("✅ The issue must be in AURA's implementation")
    else:
        print("❌ cliclick Return key is NOT working!")
        print("❌ This is a system-level issue")
        print()
        print("Possible causes:")
        print("- cliclick version issue")
        print("- macOS security settings")
        print("- Application-specific handling")
        print("- System configuration")
    
    return result

if __name__ == "__main__":
    main()