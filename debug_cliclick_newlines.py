#!/usr/bin/env python3
"""
Debug test to identify why cliclick newlines aren't working.
"""

import subprocess
import time

def test_cliclick_newlines():
    """Test cliclick newline handling directly."""
    
    print("Testing cliclick newline handling...")
    
    # Test 1: Simple multiline
    print("\n1. Testing simple multiline:")
    commands = [
        ['cliclick', 't:line1'],
        ['cliclick', 'kp:return'],
        ['cliclick', 't:line2'],
        ['cliclick', 'kp:return'],
        ['cliclick', 't:line3']
    ]
    
    for i, cmd in enumerate(commands):
        print(f"   Executing: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            print(f"   ❌ Command {i+1} failed: {result.stderr}")
        else:
            print(f"   ✅ Command {i+1} succeeded")
        time.sleep(0.1)  # Brief delay
    
    print("\nCheck the target application to see if newlines appeared correctly.")

if __name__ == "__main__":
    test_cliclick_newlines()
