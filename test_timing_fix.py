#!/usr/bin/env python3
"""
Test the timing fix for cliclick multiline typing.
"""

import subprocess
import time

def test_timing_fix():
    """Test multiline typing with proper timing."""
    
    print("🕐 Testing Timing Fix for cliclick Multiline Typing")
    print("=" * 60)
    print("This test uses longer delays between operations.")
    print("Open a text editor (TextEdit, Sublime, VS Code, etc.) and focus on it.")
    print("Press Enter when ready...")
    input()
    
    # Test content
    lines = [
        "def fibonacci(n):",
        "    if n <= 0:",
        "        return []",
        "    elif n == 1:",
        "        return [0]",
        "    else:",
        "        return [0, 1]"
    ]
    
    print(f"Testing with {len(lines)} lines and proper timing...")
    print("Watch your text editor carefully!")
    print()
    
    for i, line in enumerate(lines):
        print(f"Step {i*2+1}: Typing line {i+1}: '{line}'")
        
        # Type the line
        try:
            result = subprocess.run(
                ['cliclick', f't:{line}'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                print(f"   ✅ Line typed successfully")
            else:
                print(f"   ❌ Line typing failed: {result.stderr}")
                continue
                
        except Exception as e:
            print(f"   ❌ Line typing exception: {e}")
            continue
        
        # CRITICAL: Longer delay after typing
        print(f"   ⏳ Waiting 0.2s for application to process...")
        time.sleep(0.2)
        
        # Add Return key if not the last line
        if i < len(lines) - 1:
            print(f"Step {i*2+2}: Pressing Return key")
            
            try:
                result = subprocess.run(
                    ['cliclick', 'kp:return'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0:
                    print(f"   ✅ Return key pressed successfully")
                else:
                    print(f"   ❌ Return key failed: {result.stderr}")
                    
            except Exception as e:
                print(f"   ❌ Return key exception: {e}")
            
            # CRITICAL: Longer delay after Return key
            print(f"   ⏳ Waiting 0.3s for line processing...")
            time.sleep(0.3)
        
        print()
    
    print("Test completed!")
    print("Check your text editor:")
    print("- Do you see 7 separate lines with proper indentation?")
    print("- Is the function definition properly formatted?")
    
    response = input("Did the multiline typing work correctly? (y/n): ").lower().strip()
    return response.startswith('y')

def test_fast_vs_slow_timing():
    """Compare fast vs slow timing to see the difference."""
    
    print("\n⚡ Comparing Fast vs Slow Timing")
    print("=" * 40)
    print("This will demonstrate the difference between fast and slow timing.")
    print("Focus on your text editor and press Enter...")
    input()
    
    # Test 1: Fast timing (old way)
    print("Test 1: FAST timing (0.01s delays)")
    fast_lines = ["Fast line 1", "Fast line 2", "Fast line 3"]
    
    for i, line in enumerate(fast_lines):
        subprocess.run(['cliclick', f't:{line}'], capture_output=True, timeout=5)
        if i < len(fast_lines) - 1:
            time.sleep(0.01)  # Very short delay
            subprocess.run(['cliclick', 'kp:return'], capture_output=True, timeout=5)
            time.sleep(0.01)  # Very short delay
    
    time.sleep(2)  # Pause between tests
    
    # Add separator
    subprocess.run(['cliclick', 'kp:return'], capture_output=True, timeout=5)
    subprocess.run(['cliclick', 't:--- SEPARATOR ---'], capture_output=True, timeout=5)
    subprocess.run(['cliclick', 'kp:return'], capture_output=True, timeout=5)
    
    time.sleep(1)
    
    # Test 2: Slow timing (new way)
    print("Test 2: SLOW timing (0.2s delays)")
    slow_lines = ["Slow line 1", "Slow line 2", "Slow line 3"]
    
    for i, line in enumerate(slow_lines):
        subprocess.run(['cliclick', f't:{line}'], capture_output=True, timeout=5)
        if i < len(slow_lines) - 1:
            time.sleep(0.2)  # Longer delay
            subprocess.run(['cliclick', 'kp:return'], capture_output=True, timeout=5)
            time.sleep(0.3)  # Even longer delay after Return
    
    print("\nComparison completed!")
    print("Check your text editor:")
    print("- Did the FAST timing create separate lines?")
    print("- Did the SLOW timing work better?")
    
    fast_worked = input("Did FAST timing work? (y/n): ").lower().startswith('y')
    slow_worked = input("Did SLOW timing work? (y/n): ").lower().startswith('y')
    
    return fast_worked, slow_worked

def main():
    """Run timing fix tests."""
    
    # Test 1: Basic timing fix
    basic_result = test_timing_fix()
    
    # Test 2: Compare timings
    fast_result, slow_result = test_fast_vs_slow_timing()
    
    print("\n" + "=" * 60)
    print("🎯 TIMING FIX TEST RESULTS")
    print("=" * 60)
    print(f"Basic timing fix test: {'✅ PASS' if basic_result else '❌ FAIL'}")
    print(f"Fast timing (0.01s): {'✅ WORKS' if fast_result else '❌ FAILS'}")
    print(f"Slow timing (0.2s+): {'✅ WORKS' if slow_result else '❌ FAILS'}")
    
    if basic_result and slow_result:
        print("\n🎉 TIMING FIX SUCCESSFUL!")
        print("✅ Longer delays solve the multiline typing issue")
        print("✅ Applications need time to process typed text before Return key")
        print("✅ The fix should work in AURA now")
    elif slow_result and not fast_result:
        print("\n✅ TIMING IS THE ISSUE!")
        print("✅ Slow timing works, fast timing doesn't")
        print("✅ The fix should resolve AURA's multiline typing problems")
    else:
        print("\n❌ TIMING IS NOT THE ONLY ISSUE")
        print("❌ Even slow timing doesn't work")
        print("❌ There may be other fundamental problems with cliclick")
    
    return basic_result

if __name__ == "__main__":
    main()