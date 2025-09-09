#!/usr/bin/env python3
"""
Test newline detection in the automation module.
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.automation import AutomationModule

def test_newline_detection():
    """Test if newline detection is working correctly."""
    
    print("🧪 Testing Newline Detection Logic")
    print("=" * 50)
    
    # Test case from the corrupted content
    test_text = '''import math

def big_nudge_sequence(initial=0.0, steps=10, base_magnitude=1.0):
    sequence = [initial]
    for i in range(1, steps + 1):
        nudge = base_magnitude * math.pow(2, i - 1)
        sequence.append(sequence[-1] + nudge)
    return sequence

if __name__ == "__main__":
    seq = big_nudge_sequence(initial=0.0, steps=8, base_magnitude=0.5)
    for value in seq:
        print(value)'''
    
    automation = AutomationModule()
    
    print(f"📊 Test Text Analysis:")
    print(f"   Length: {len(test_text)} characters")
    print(f"   Lines: {len(test_text.split(chr(10)))} lines")
    print(f"   Newline count (\\n): {test_text.count(chr(10))}")
    print(f"   Contains newlines: {'✅ YES' if chr(10) in test_text else '❌ NO'}")
    
    # Test the formatting
    print(f"\n🔧 Testing cliclick formatting:")
    formatted = automation._format_text_for_typing(test_text, 'cliclick')
    print(f"   Formatted length: {len(formatted)} characters")
    print(f"   Formatted lines: {len(formatted.split(chr(10)))} lines")
    print(f"   Formatted newline count: {formatted.count(chr(10))}")
    print(f"   Formatted contains newlines: {'✅ YES' if chr(10) in formatted else '❌ NO'}")
    
    # Test the detection logic
    print(f"\n🎯 Method Selection Test:")
    has_newlines = '\n' in formatted
    print(f"   Detection result: {'MULTILINE' if has_newlines else 'SINGLE-LINE'}")
    
    if has_newlines:
        print(f"   ✅ CORRECT: Will use multiline method")
        lines = formatted.split('\n')
        print(f"   Will type {len(lines)} lines with {len(lines)-1} Return key presses")
    else:
        print(f"   ❌ INCORRECT: Will use single-line method - THIS CAUSES CORRUPTION!")
        print(f"   This explains why everything gets typed on one line!")
    
    # Show first few lines that would be typed
    if has_newlines:
        print(f"\n📝 Lines that would be typed:")
        lines = formatted.split('\n')
        for i, line in enumerate(lines[:5]):
            print(f"   Line {i+1}: {repr(line)}")
            if i < len(lines) - 1:
                print(f"   Then: Return key press")
        if len(lines) > 5:
            print(f"   ... and {len(lines) - 5} more lines")
    
    return has_newlines

def main():
    """Run the newline detection test."""
    
    try:
        result = test_newline_detection()
        
        print(f"\n" + "=" * 50)
        print(f"🎯 TEST RESULT: {'✅ PASS' if result else '❌ FAIL'}")
        
        if result:
            print("✅ Newline detection is working correctly")
            print("✅ Should use multiline method")
            print("✅ The issue must be elsewhere in the pipeline")
        else:
            print("❌ Newline detection is BROKEN")
            print("❌ This explains the single-line corruption")
            print("❌ Need to fix the detection logic")
        
        return result
        
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)