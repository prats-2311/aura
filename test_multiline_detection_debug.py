#!/usr/bin/env python3
"""
Debug test to check if multiline detection is working correctly.
This will help identify why cliclick is using single-line method for multiline content.
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.automation import AutomationModule

def test_multiline_detection_logic():
    """Test the exact logic used for multiline detection."""
    
    print("Testing Multiline Detection Logic")
    print("=" * 50)
    
    # Test the exact text that was causing issues
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
    
    print(f"Test text analysis:")
    print(f"  Length: {len(test_text)} chars")
    newline_char = '\n'
    print(f"  Raw newlines (\\n in text): {newline_char in test_text}")
    print(f"  chr(10) count: {test_text.count(chr(10))}")
    
    # Show the exact characters
    print(f"  First 100 chars: {repr(test_text[:100])}")
    
    # Test the exact condition used in _cliclick_type
    newline_condition = '\n' in test_text
    print(f"  Multiline condition ('\\n' in text): {newline_condition}")
    
    if newline_condition:
        print("  ✅ Should use multiline method")
    else:
        print("  ❌ Will use single-line method - THIS IS THE PROBLEM!")
    
    # Test formatting
    if automation.is_macos and automation.has_cliclick:
        formatted_text = automation._format_text_for_typing(test_text, 'cliclick')
        
        print(f"\nFormatted text analysis:")
        print(f"  Formatted length: {len(formatted_text)} chars")
        print(f"  Formatted newlines: {newline_char in formatted_text}")
        print(f"  First 100 formatted chars: {repr(formatted_text[:100])}")
        
        # Test the condition after formatting
        formatted_condition = '\n' in formatted_text
        print(f"  Multiline condition after formatting: {formatted_condition}")
        
        if formatted_condition:
            print("  ✅ Formatted text should use multiline method")
        else:
            print("  ❌ Formatted text will use single-line method - FORMATTING IS REMOVING NEWLINES!")

def test_cliclick_command_simulation():
    """Simulate what cliclick commands would be generated."""
    
    print("\nTesting cliclick Command Simulation")
    print("=" * 50)
    
    test_text = '''def fibonacci(n):
    if n <= 0:
        return []
    return n'''
    
    automation = AutomationModule()
    
    if automation.is_macos and automation.has_cliclick:
        formatted_text = automation._format_text_for_typing(test_text, 'cliclick')
        
        print(f"Original text: {repr(test_text)}")
        print(f"Formatted text: {repr(formatted_text)}")
        
        # Simulate the decision logic from _cliclick_type
        if '\n' in test_text:
            print("\\n✅ Using multiline method:")
            lines = formatted_text.split('\n')
            print(f"  Will type {len(lines)} lines:")
            for i, line in enumerate(lines):
                if line.strip():
                    print(f"    Line {i+1}: cliclick t:{repr(line)}")
                else:
                    print(f"    Line {i+1}: (empty line)")
                if i < len(lines) - 1:
                    print(f"    Then: cliclick kp:return")
        else:
            print("\\n❌ Using single-line method:")
            print(f"  Command: cliclick t:{repr(formatted_text)}")
            print("  This will type everything on one line!")

def test_backend_log_correlation():
    """Correlate with the backend logs to understand what's happening."""
    
    print("\\nBackend Log Correlation Analysis")
    print("=" * 50)
    
    print("From the backend logs:")
    print("  'cliclick SLOW PATH: Typing succeeded on 'unknown' in 18.393s'")
    print("  'def fibonacci(n):\\n    if n <= 0:\\n        return []...'")
    print()
    print("Analysis:")
    print("  ✅ cliclick received text with newlines (\\n visible in log)")
    print("  ❌ Took 18+ seconds (should be much faster with multiline method)")
    print("  ❌ Result in touch.py shows single-line output")
    print()
    print("Conclusion:")
    print("  The issue is likely that cliclick is using single-line method")
    print("  instead of multiline method, causing all text to be typed as one line.")
    print()
    print("Expected behavior:")
    print("  - Multiline method: Fast typing, preserves newlines")
    print("  - Single-line method: Slow typing, loses newlines")

if __name__ == "__main__":
    print("Multiline Detection Debug Test Suite")
    print("Investigating why cliclick is not preserving newlines")
    print("=" * 70)
    
    try:
        test_multiline_detection_logic()
        test_cliclick_command_simulation()
        test_backend_log_correlation()
        
        print("\\n" + "=" * 70)
        print("Debug analysis completed!")
        
    except Exception as e:
        print(f"Debug test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)