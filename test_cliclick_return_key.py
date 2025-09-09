#!/usr/bin/env python3
"""
Test cliclick Return key functionality directly to identify the issue.
"""

import subprocess
import time

def test_cliclick_return_variants():
    """Test different ways to send Return key with cliclick."""
    
    print("🧪 Testing cliclick Return Key Variants")
    print("=" * 50)
    print("Open a text editor and focus on it, then press Enter to start...")
    input()
    
    variants = [
        ("kp:return", "Standard Return key press"),
        ("kp:enter", "Enter key press"),  
        ("kp:0x24", "Return key by hex code"),
        ("kd:return ku:return", "Return key down/up"),
        ("t:\\n", "Literal newline character"),
        ("t:\\r", "Carriage return"),
        ("t:\\r\\n", "Windows-style newline"),
    ]
    
    print("Testing different Return key methods...")
    print("Watch your text editor to see which ones create actual newlines.")
    print()
    
    for i, (command, description) in enumerate(variants):
        print(f"Test {i+1}: {description}")
        print(f"Command: cliclick {command}")
        
        # Type a line identifier first
        type_cmd = f"cliclick t:Line{i+1}"
        print(f"Typing: {type_cmd}")
        
        try:
            # Type the line identifier
            result = subprocess.run(
                type_cmd.split(),
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                print(f"   ❌ Typing failed: {result.stderr}")
                continue
            
            time.sleep(0.2)  # Brief pause
            
            # Try the Return key variant
            if command.startswith('t:'):
                # For literal characters, use single command
                return_cmd = ['cliclick', command]
            else:
                # For key presses, split by spaces
                return_cmd = ['cliclick'] + command.split()
            
            print(f"Return command: {' '.join(return_cmd)}")
            
            result = subprocess.run(
                return_cmd,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                print(f"   ✅ Command succeeded")
            else:
                print(f"   ❌ Command failed: {result.stderr}")
            
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        
        time.sleep(1)  # Pause between tests
        print()
    
    print("Test completed!")
    print("Check your text editor:")
    print("- Which methods created actual newlines?")
    print("- Did any method work correctly?")

def test_cliclick_multiline_simulation():
    """Simulate the exact multiline typing that AURA does."""
    
    print("\n🔄 Simulating AURA's Multiline Typing")
    print("=" * 50)
    print("This will simulate exactly what AURA does for multiline typing.")
    print("Focus on a text editor and press Enter to start...")
    input()
    
    # Simple test content
    lines = [
        "def test():",
        "    print('hello')",
        "    return True"
    ]
    
    print("Simulating AURA's multiline typing process...")
    
    for i, line in enumerate(lines):
        print(f"\nStep {i*2+1}: Typing line {i+1}: {repr(line)}")
        
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
        
        time.sleep(0.5)  # Pause between operations
    
    print("\nSimulation completed!")
    print("Check your text editor - did you see 3 separate lines?")

def test_manual_verification():
    """Manual verification of what should happen."""
    
    print("\n✋ Manual Verification")
    print("=" * 50)
    print("Now let's verify what SHOULD happen:")
    print("1. Open a text editor")
    print("2. Manually type: def test():")
    print("3. Press Return")
    print("4. Type:     print('hello')")
    print("5. Press Return") 
    print("6. Type:     return True")
    print()
    print("You should see 3 separate lines with proper indentation.")
    print("This is what AURA should produce but currently doesn't.")

def main():
    """Run all cliclick Return key tests."""
    
    print("🔍 cliclick Return Key Diagnostic")
    print("This will help identify why Return keys aren't creating newlines")
    print("=" * 70)
    
    test_cliclick_return_variants()
    test_cliclick_multiline_simulation()
    test_manual_verification()
    
    print("\n" + "=" * 70)
    print("🎯 ANALYSIS QUESTIONS")
    print("=" * 70)
    print("After running these tests, please answer:")
    print("1. Did ANY of the Return key variants create actual newlines?")
    print("2. Did the multiline simulation work correctly?")
    print("3. What's the difference between manual typing and cliclick?")
    print()
    print("This will help identify if the issue is:")
    print("- cliclick Return key syntax")
    print("- System-level cliclick configuration")
    print("- Application-specific handling")
    print("- Timing or sequencing issues")

if __name__ == "__main__":
    main()