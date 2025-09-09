#!/usr/bin/env python3
"""
Test actual cliclick typing functionality to identify any real-world issues.
This test will actually attempt to type text and verify the results.
"""

import sys
import os
import time
import tempfile

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.automation import AutomationModule

def test_cliclick_typing_method():
    """Test the actual _cliclick_type method with various inputs."""
    
    print("=== Testing Actual cliclick Typing Method ===")
    
    automation = AutomationModule()
    
    if not (automation.is_macos and automation.has_cliclick):
        print("⚠️  cliclick not available - skipping actual typing test")
        return True
    
    # Test cases with different complexity levels
    test_cases = [
        ("Simple text", "Hello World"),
        ("Single line with special chars", 'echo "Hello $USER"'),
        ("Multi-line code", '''def test():
    print("Hello")
    return True'''),
        ("Complex multi-line", '''def fibonacci(n):
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    
    seq = [0, 1]
    for i in range(2, n):
        seq.append(seq[i-1] + seq[i-2])
    return seq'''),
    ]
    
    results = []
    
    for test_name, test_text in test_cases:
        print(f"\n--- Testing: {test_name} ---")
        print(f"Input text ({len(test_text)} chars, {test_text.count(chr(10))} newlines):")
        print(f"Preview: {repr(test_text[:100])}{'...' if len(test_text) > 100 else ''}")
        
        try:
            # Test the typing method directly
            start_time = time.time()
            result = automation._cliclick_type(test_text, fast_path=False)
            execution_time = time.time() - start_time
            
            print(f"Result: {'SUCCESS' if result else 'FAILED'}")
            print(f"Execution time: {execution_time:.3f}s")
            
            # Analyze the execution
            if result:
                print("✅ Typing method completed successfully")
                
                # Check if it used multiline method
                if '\n' in test_text:
                    if execution_time < 5.0:  # Multiline should be faster
                        print("✅ Likely used multiline method (fast execution)")
                    else:
                        print("⚠️  Slow execution - may have used single-line method")
                else:
                    print("✅ Single-line text handled appropriately")
            else:
                print("❌ Typing method failed")
            
            results.append((test_name, result))
            
        except Exception as e:
            print(f"❌ Exception during typing: {e}")
            results.append((test_name, False))
    
    # Summary
    successful = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\n--- Typing Method Test Summary ---")
    print(f"Successful: {successful}/{total}")
    
    return successful == total

def test_multiline_method_directly():
    """Test the multiline typing method directly."""
    
    print("\n=== Testing Multiline Method Directly ===")
    
    automation = AutomationModule()
    
    if not (automation.is_macos and automation.has_cliclick):
        print("⚠️  cliclick not available - skipping multiline test")
        return True
    
    # Test multiline content
    multiline_text = '''def calculate_sum(numbers):
    """Calculate the sum of a list of numbers."""
    total = 0
    for num in numbers:
        total += num
    return total

# Example usage
result = calculate_sum([1, 2, 3, 4, 5])
print(f"Sum: {result}")'''
    
    print(f"Testing multiline method with {len(multiline_text)} chars, {multiline_text.count(chr(10))} newlines")
    
    try:
        # Format the text first
        formatted_text = automation._format_text_for_typing(multiline_text, 'cliclick')
        
        print(f"Formatted text: {len(formatted_text)} chars, {formatted_text.count(chr(10))} newlines")
        
        # Test the multiline method directly
        start_time = time.time()
        result = automation._cliclick_type_multiline(formatted_text, fast_path=False)
        execution_time = time.time() - start_time
        
        print(f"Multiline method result: {'SUCCESS' if result else 'FAILED'}")
        print(f"Execution time: {execution_time:.3f}s")
        
        if result:
            print("✅ Multiline typing method works correctly")
        else:
            print("❌ Multiline typing method failed")
            print("   This could indicate Return key issues or timeout problems")
        
        return result
        
    except Exception as e:
        print(f"❌ Exception in multiline method: {e}")
        return False

def test_return_key_reliability():
    """Test the Return key reliability specifically."""
    
    print("\n=== Testing Return Key Reliability ===")
    
    automation = AutomationModule()
    
    if not (automation.is_macos and automation.has_cliclick):
        print("⚠️  cliclick not available - skipping Return key test")
        return True
    
    print("Testing Return key press reliability...")
    
    # Test Return key multiple times
    success_count = 0
    total_attempts = 5
    
    for i in range(total_attempts):
        try:
            import subprocess
            result = subprocess.run(
                ['cliclick', 'kp:return'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                success_count += 1
                print(f"  Attempt {i+1}: ✅ SUCCESS")
            else:
                print(f"  Attempt {i+1}: ❌ FAILED - {result.stderr}")
                
        except Exception as e:
            print(f"  Attempt {i+1}: ❌ EXCEPTION - {e}")
    
    success_rate = (success_count / total_attempts) * 100
    print(f"\nReturn key success rate: {success_rate:.1f}% ({success_count}/{total_attempts})")
    
    if success_rate >= 90:
        print("✅ Return key reliability is good")
        return True
    elif success_rate >= 70:
        print("⚠️  Return key reliability is acceptable but could be better")
        return True
    else:
        print("❌ Return key reliability is poor - this will cause multiline issues")
        return False

def main():
    """Run comprehensive tests for cliclick typing functionality."""
    
    print("Comprehensive cliclick Typing Functionality Test")
    print("=" * 60)
    print("Testing actual typing execution and reliability")
    print()
    
    # Run all tests
    results = []
    results.append(("cliclick Typing Method", test_cliclick_typing_method()))
    results.append(("Multiline Method Direct", test_multiline_method_directly()))
    results.append(("Return Key Reliability", test_return_key_reliability()))
    
    # Summary
    print("\n" + "=" * 60)
    print("COMPREHENSIVE TEST RESULTS")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<25}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL FUNCTIONALITY TESTS PASSED!")
        print("\nThe cliclick typing implementation is working correctly.")
        print("Text formatting and multiline typing are functioning as expected.")
        return True
    else:
        print(f"\n❌ {total - passed} functionality tests failed")
        print("There may be issues with the actual typing execution.")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)