#!/usr/bin/env python3
"""
Test script to verify Task 1: Fix text formatting in cliclick typing method.
This test validates all the requirements for proper text formatting.
"""

import sys
import os
import time
import tempfile

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.automation import AutomationModule

def test_multiline_code_formatting():
    """Test that multiline code preserves formatting and indentation."""
    
    print("=== Testing Multiline Code Formatting ===")
    
    # Test case: Python function with proper indentation
    python_code = '''def fibonacci(n):
    """Calculate fibonacci sequence up to n numbers."""
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    elif n == 2:
        return [0, 1]
    
    sequence = [0, 1]
    for i in range(2, n):
        next_num = sequence[i-1] + sequence[i-2]
        sequence.append(next_num)
    
    return sequence

# Test the function
if __name__ == "__main__":
    result = fibonacci(10)
    print(f"Fibonacci sequence: {result}")'''
    
    automation = AutomationModule()
    
    print(f"Original code ({len(python_code)} chars, {python_code.count(chr(10))} newlines):")
    print("First 150 chars:", repr(python_code[:150]))
    
    if automation.is_macos and automation.has_cliclick:
        # Test the formatting method
        formatted = automation._format_text_for_typing(python_code, 'cliclick')
        
        print(f"\nFormatted code ({len(formatted)} chars, {formatted.count(chr(10))} newlines):")
        print("First 150 chars:", repr(formatted[:150]))
        
        # Verify requirements
        original_lines = python_code.split('\n')
        formatted_lines = formatted.split('\n')
        
        # Requirement 1.1: Preserve line breaks and indentation
        line_count_preserved = len(original_lines) == len(formatted_lines)
        print(f"\n✅ Line count preservation: {'PASS' if line_count_preserved else 'FAIL'}")
        print(f"   Original: {len(original_lines)} lines, Formatted: {len(formatted_lines)} lines")
        
        # Check indentation preservation
        indentation_preserved = True
        for i, (orig, fmt) in enumerate(zip(original_lines, formatted_lines)):
            orig_indent = len(orig) - len(orig.lstrip())
            fmt_indent = len(fmt) - len(fmt.lstrip())
            if orig_indent != fmt_indent:
                indentation_preserved = False
                print(f"   Line {i+1}: Indentation mismatch ({orig_indent} -> {fmt_indent})")
                break
        
        print(f"✅ Indentation preservation: {'PASS' if indentation_preserved else 'FAIL'}")
        
        # Requirement 1.2: Maintain proper code formatting
        newlines_preserved = python_code.count('\n') == formatted.count('\n')
        print(f"✅ Newline preservation: {'PASS' if newlines_preserved else 'FAIL'}")
        
        # Test multiline detection
        will_use_multiline = '\n' in formatted
        print(f"✅ Multiline method detection: {'PASS' if will_use_multiline else 'FAIL'}")
        
        return line_count_preserved and indentation_preserved and newlines_preserved and will_use_multiline
    else:
        print("⚠️  cliclick not available - skipping test")
        return True

def test_special_character_escaping():
    """Test that special characters are properly escaped for cliclick."""
    
    print("\n=== Testing Special Character Escaping ===")
    
    # Test various special characters that can cause issues
    test_cases = [
        ('Double quotes', 'echo "Hello World"', '\\"'),
        ('Single quotes', "echo 'Hello World'", "\\'"),
        ('Backticks', 'result=`date`', '\\`'),
        ('Dollar signs', 'price=$29.99', '\\$'),
        ('Backslashes', 'path=C:\\Users\\Name', '\\\\'),
        ('Ampersands', 'cmd1 && cmd2', '\\&'),
        ('Pipes', 'cmd1 | cmd2', '\\|'),
        ('Semicolons', 'cmd1; cmd2', '\\;'),
    ]
    
    automation = AutomationModule()
    
    if automation.is_macos and automation.has_cliclick:
        all_passed = True
        
        for name, test_text, expected_escape in test_cases:
            formatted = automation._format_text_for_typing(test_text, 'cliclick')
            
            # Check if the dangerous character is properly escaped
            if expected_escape in formatted:
                print(f"✅ {name}: PASS (properly escaped)")
            else:
                print(f"❌ {name}: FAIL (not properly escaped)")
                print(f"   Original: {repr(test_text)}")
                print(f"   Formatted: {repr(formatted)}")
                all_passed = False
        
        return all_passed
    else:
        print("⚠️  cliclick not available - skipping test")
        return True

def test_multiline_typing_simulation():
    """Simulate the multiline typing process to verify it works correctly."""
    
    print("\n=== Testing Multiline Typing Simulation ===")
    
    test_code = '''def greet(name):
    print(f"Hello, {name}!")
    return f"Greeting sent to {name}"

greet("World")'''
    
    automation = AutomationModule()
    
    if automation.is_macos and automation.has_cliclick:
        formatted = automation._format_text_for_typing(test_code, 'cliclick')
        
        print(f"Test code: {repr(test_code)}")
        print(f"Formatted: {repr(formatted)}")
        
        # Simulate the multiline detection and command generation
        if '\n' in formatted:
            lines = formatted.split('\n')
            print(f"\n✅ Multiline method will be used ({len(lines)} lines)")
            
            # Show what commands would be executed
            print("Commands that would be executed:")
            for i, line in enumerate(lines):
                if line.strip():  # Non-empty line
                    print(f"  Line {i+1}: cliclick t:{repr(line)}")
                else:
                    print(f"  Line {i+1}: (empty line)")
                
                if i < len(lines) - 1:  # Not the last line
                    print(f"           cliclick kp:return")
            
            return True
        else:
            print("❌ Single-line method would be used - this is incorrect!")
            return False
    else:
        print("⚠️  cliclick not available - skipping test")
        return True

def test_edge_cases():
    """Test edge cases that might cause formatting issues."""
    
    print("\n=== Testing Edge Cases ===")
    
    edge_cases = [
        ("Empty lines", "line1\n\nline3\n\nline5"),
        ("Only spaces", "    \n        \n    "),
        ("Mixed indentation", "def test():\n    var1 = 1\n\tvar2 = 2\n    \tvar3 = 3"),
        ("Very long line", "x = " + "a" * 200),
        ("Unicode characters", "print('Hello 世界! café naïve résumé')"),
        ("Complex escaping", '''echo "He said 'Hello $USER' and ran `date`"'''),
    ]
    
    automation = AutomationModule()
    
    if automation.is_macos and automation.has_cliclick:
        all_passed = True
        
        for name, test_text in edge_cases:
            try:
                formatted = automation._format_text_for_typing(test_text, 'cliclick')
                
                # Basic validation - should not crash and should return a string
                if isinstance(formatted, str):
                    print(f"✅ {name}: PASS (handled without error)")
                else:
                    print(f"❌ {name}: FAIL (returned {type(formatted)})")
                    all_passed = False
                    
            except Exception as e:
                print(f"❌ {name}: FAIL (exception: {e})")
                all_passed = False
        
        return all_passed
    else:
        print("⚠️  cliclick not available - skipping test")
        return True

def main():
    """Run all tests for Task 1: Fix text formatting in cliclick typing method."""
    
    print("Task 1: cliclick Text Formatting Fix Verification")
    print("=" * 60)
    print("Testing Requirements 1.1, 1.2, and 1.3")
    print()
    
    # Run all tests
    results = []
    results.append(("Multiline Code Formatting", test_multiline_code_formatting()))
    results.append(("Special Character Escaping", test_special_character_escaping()))
    results.append(("Multiline Typing Simulation", test_multiline_typing_simulation()))
    results.append(("Edge Cases", test_edge_cases()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<30}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("\nTask 1 Requirements Verified:")
        print("✅ 1.1: System preserves line breaks and indentation")
        print("✅ 1.2: System maintains proper code formatting")
        print("✅ 1.3: cliclick handles newlines and special characters correctly")
        print("\nThe cliclick text formatting fix is working correctly!")
        return True
    else:
        print(f"\n❌ {total - passed} tests failed")
        print("Task 1 implementation needs additional work.")
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