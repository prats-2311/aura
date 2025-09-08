#!/usr/bin/env python3
"""
Debug test for the newline issue in cliclick typing.
This test will help identify why newlines are not being preserved.
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.automation import AutomationModule

def test_newline_detection():
    """Test how the automation module detects and handles newlines."""
    
    print("Testing Newline Detection and Handling")
    print("=" * 50)
    
    # Test case with newlines
    test_text = '''def fibonacci(n):
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
    
    automation = AutomationModule()
    
    print(f"Original text:")
    print(f"  Length: {len(test_text)} chars")
    print(f"  Newlines: {test_text.count(chr(10))} (using chr(10))")
    newline_char = '\n'
    print(f"  Newlines: {test_text.count(newline_char)} (using \\n)")
    print(f"  Contains \\n: {newline_char in test_text}")
    print(f"  Lines when split: {len(test_text.split(chr(10)))}")
    
    # Test formatting
    if automation.is_macos and automation.has_cliclick:
        print(f"\n✅ Testing cliclick formatting:")
        formatted_text = automation._format_text_for_typing(test_text, 'cliclick')
        
        print(f"  Formatted length: {len(formatted_text)} chars")
        print(f"  Formatted newlines: {formatted_text.count(chr(10))} (using chr(10))")
        print(f"  Formatted newlines: {formatted_text.count(newline_char)} (using \\n)")
        print(f"  Formatted contains \\n: {newline_char in formatted_text}")
        print(f"  Formatted lines when split: {len(formatted_text.split(chr(10)))}")
        
        # Check if multiline detection works
        will_use_multiline = newline_char in test_text
        print(f"  Will use multiline method: {will_use_multiline}")
        
        # Show first few lines
        lines = formatted_text.split(newline_char)
        print(f"  First 3 formatted lines:")
        for i, line in enumerate(lines[:3]):
            print(f"    {i+1}: {repr(line)}")
    
    print("\n" + "=" * 50)
    print("Diagnosis:")
    
    # Check if the issue is in newline detection
    if newline_char in test_text:
        print("✅ Original text contains newlines")
    else:
        print("❌ Original text does NOT contain newlines - this is the problem!")
    
    if automation.is_macos and automation.has_cliclick:
        formatted_text = automation._format_text_for_typing(test_text, 'cliclick')
        if newline_char in formatted_text:
            print("✅ Formatted text contains newlines")
        else:
            print("❌ Formatted text does NOT contain newlines - formatting is removing them!")

def test_cliclick_single_vs_multiline():
    """Test the difference between single-line and multiline cliclick behavior."""
    
    print("\nTesting cliclick Single vs Multiline Behavior")
    print("=" * 50)
    
    # Single line test
    single_line = "def fibonacci(n): return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)"
    
    # Multi line test
    multi_line = '''def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)'''
    
    automation = AutomationModule()
    
    newline_char = '\n'
    print("Single line test:")
    print(f"  Text: {repr(single_line)}")
    print(f"  Contains \\n: {newline_char in single_line}")
    print(f"  Length: {len(single_line)} chars")
    
    print("\nMulti line test:")
    print(f"  Text: {repr(multi_line[:50])}...")
    print(f"  Contains \\n: {newline_char in multi_line}")
    print(f"  Length: {len(multi_line)} chars")
    print(f"  Lines: {len(multi_line.split(chr(10)))}")
    
    if automation.is_macos and automation.has_cliclick:
        print("\n✅ Testing method selection:")
        
        # Test single line
        formatted_single = automation._format_text_for_typing(single_line, 'cliclick')
        will_use_multiline_single = newline_char in single_line
        print(f"  Single line will use multiline: {will_use_multiline_single}")
        
        # Test multi line
        formatted_multi = automation._format_text_for_typing(multi_line, 'cliclick')
        will_use_multiline_multi = newline_char in multi_line
        print(f"  Multi line will use multiline: {will_use_multiline_multi}")
        
        if will_use_multiline_multi:
            print("  ✅ Multi-line text will use multiline method")
        else:
            print("  ❌ Multi-line text will NOT use multiline method - this is the problem!")

def test_actual_newline_characters():
    """Test what actual newline characters are in the text."""
    
    print("\nTesting Actual Newline Characters")
    print("=" * 50)
    
    # Create text with different types of newlines
    newline_char = '\n'
    test_cases = [
        ("Unix newlines", "line1" + newline_char + "line2" + newline_char + "line3"),
        ("Windows newlines", "line1\r" + newline_char + "line2\r" + newline_char + "line3"),
        ("Mac newlines", "line1\rline2\rline3"),
        ("Python multiline string", '''line1
line2
line3''')
    ]
    
    for name, text in test_cases:
        print(f"\n{name}:")
        print(f"  Text: {repr(text)}")
        print(f"  Contains \\n: {newline_char in text}")
        print(f"  Contains \\r: {chr(13) in text}")
        print(f"  chr(10) count: {text.count(chr(10))}")
        print(f"  chr(13) count: {text.count(chr(13))}")
        
        # Check what split produces
        lines_n = text.split(newline_char)
        lines_chr10 = text.split(chr(10))
        print(f"  Split by \\n: {len(lines_n)} parts")
        print(f"  Split by chr(10): {len(lines_chr10)} parts")

if __name__ == "__main__":
    print("Newline Issue Debug Test Suite")
    print("Investigating why newlines are not being preserved in cliclick typing")
    print("=" * 70)
    
    try:
        test_newline_detection()
        test_cliclick_single_vs_multiline()
        test_actual_newline_characters()
        
        print("\n" + "=" * 70)
        print("Debug test completed!")
        print("Check the output above to identify the newline handling issue.")
        
    except Exception as e:
        print(f"Debug test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)