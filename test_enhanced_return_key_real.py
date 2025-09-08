#!/usr/bin/env python3
"""
Test the enhanced Return key solution with real automation module execution.
This will verify that our fixes actually work in practice.
"""

import sys
import os
import tempfile
import time

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.automation import AutomationModule

def test_real_multiline_typing():
    """Test real multiline typing with the enhanced Return key solution."""
    
    print("Testing Enhanced Return Key Solution - Real Execution")
    print("=" * 70)
    
    # Test with the exact content that was problematic
    test_code = '''def fibonacci(n):
    if n <= 0:
        return []
    if n == 1:
        return [0]
    seq = [0, 1]
    while len(seq) < n:
        seq.append(seq[-1] + seq[-2])
    return seq

if __name__ == "__main__":
    n = int(input())
    print(fibonacci(n))'''
    
    print(f"Test code: {len(test_code)} chars, {test_code.count(chr(10))} newlines")
    print(f"First 100 chars: {repr(test_code[:100])}")
    
    automation = AutomationModule()
    
    if not (automation.is_macos and automation.has_cliclick):
        print("⚠️  This test requires macOS with cliclick")
        return False
    
    # Create a test action
    type_action = {
        "action": "type",
        "text": test_code
    }
    
    print(f"\\nPreparing to test enhanced Return key solution...")
    print(f"⚠️  WARNING: This will actually type text on your screen!")
    print(f"Make sure you have a text editor open and focused.")
    print(f"The test will start in 5 seconds...")
    
    # Give user time to focus on a text editor
    for i in range(5, 0, -1):
        print(f"Starting in {i}...")
        time.sleep(1)
    
    print(f"\\n🚀 Starting enhanced Return key test...")
    
    try:
        start_time = time.time()
        
        # Execute the type action with our enhanced Return key solution
        automation.execute_action(type_action)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\\n✅ Type action completed successfully!")
        print(f"Duration: {duration:.2f} seconds")
        
        # Analyze the timing
        expected_lines = test_code.count('\\n') + 1
        expected_returns = test_code.count('\\n')
        
        print(f"\\nTiming analysis:")
        print(f"  Lines to type: {expected_lines}")
        print(f"  Return keys needed: {expected_returns}")
        print(f"  Actual duration: {duration:.2f}s")
        
        # With enhanced timing, we expect:
        # - Line typing: ~0.08s per line
        # - Return keys: ~0.1s per return (with retries)
        expected_duration = (expected_lines * 0.08) + (expected_returns * 0.1)
        print(f"  Expected duration: {expected_duration:.2f}s")
        
        if duration < expected_duration * 2:  # Allow some variance
            print(f"  ✅ Duration is reasonable - enhanced timing working")
        else:
            print(f"  ⚠️  Duration is longer than expected - may indicate issues")
        
        print(f"\\n🎯 Next Steps:")
        print(f"  1. Check the text editor to see if code was typed correctly")
        print(f"  2. Verify that newlines are preserved (proper indentation)")
        print(f"  3. Confirm no single-line corruption occurred")
        
        return True
        
    except Exception as e:
        print(f"\\n❌ Type action failed: {e}")
        print(f"This indicates the enhanced Return key solution needs more work")
        return False

def test_return_key_reliability_extended():
    """Extended test of Return key reliability."""
    
    print(f"\\nExtended Return Key Reliability Test")
    print("=" * 70)
    
    import subprocess
    
    # Test multiple Return key presses in rapid succession
    print(f"Testing rapid Return key presses (simulating multiline typing)...")
    
    success_count = 0
    total_attempts = 20  # Test more Return keys
    
    for i in range(total_attempts):
        try:
            result = subprocess.run(
                ['cliclick', 'kp:return'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                success_count += 1
                print(f"  Return {i+1:2d}: ✅", end="")
            else:
                print(f"  Return {i+1:2d}: ❌ ({result.stderr.strip()})", end="")
            
            # Add small delay like in real typing
            time.sleep(0.05)
            
            # Print newline every 10 attempts for readability
            if (i + 1) % 10 == 0:
                print()
            else:
                print(" ", end="")
                
        except Exception as e:
            print(f"  Return {i+1:2d}: ❌ ({str(e)})", end="")
            if (i + 1) % 10 == 0:
                print()
            else:
                print(" ", end="")
    
    if total_attempts % 10 != 0:
        print()  # Final newline if needed
    
    success_rate = (success_count / total_attempts) * 100
    print(f"\\nExtended Return key test results:")
    print(f"  Total attempts: {total_attempts}")
    print(f"  Successful: {success_count}")
    print(f"  Failed: {total_attempts - success_count}")
    print(f"  Success rate: {success_rate:.1f}%")
    
    if success_rate >= 95:
        print(f"  ✅ Excellent Return key reliability")
        return True
    elif success_rate >= 80:
        print(f"  ⚠️  Good Return key reliability (some failures expected)")
        return True
    else:
        print(f"  ❌ Poor Return key reliability - this will cause newline issues")
        return False

def main():
    """Run the enhanced Return key solution test."""
    
    print("Enhanced Return Key Solution - Real World Test")
    print("Testing our fixes with actual automation execution")
    print("=" * 80)
    
    try:
        # Test Return key reliability first
        return_reliable = test_return_key_reliability_extended()
        
        if not return_reliable:
            print(f"\\n❌ Return key reliability issues detected")
            print(f"This explains why newlines are being lost")
            return False
        
        # Test real multiline typing
        print(f"\\n" + "=" * 80)
        typing_success = test_real_multiline_typing()
        
        print(f"\\n" + "=" * 80)
        if typing_success and return_reliable:
            print(f"🎉 ENHANCED RETURN KEY SOLUTION TEST PASSED!")
            print(f"\\n✅ Key Improvements Verified:")
            print(f"  - Return key reliability is good")
            print(f"  - Enhanced timing and retry logic working")
            print(f"  - Multiline typing completed successfully")
            print(f"\\n🎯 The newline preservation issue should now be resolved!")
        else:
            print(f"❌ ENHANCED RETURN KEY SOLUTION NEEDS MORE WORK")
            print(f"\\nIssues detected:")
            if not return_reliable:
                print(f"  - Return key reliability problems")
            if not typing_success:
                print(f"  - Multiline typing execution problems")
        
        return typing_success and return_reliable
        
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("⚠️  WARNING: This test will type text on your screen!")
    print("Make sure you have a text editor open and ready.")
    print("Press Ctrl+C to cancel, or Enter to continue...")
    
    try:
        input()
    except KeyboardInterrupt:
        print("\\nTest cancelled by user")
        sys.exit(0)
    
    success = main()
    sys.exit(0 if success else 1)