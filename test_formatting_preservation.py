#!/usr/bin/env python3
"""
Test script to verify that text formatting is actually preserved when typing.
This test opens TextEdit and types multi-line code to verify formatting.
"""

import sys
import os
import subprocess
import time
import tempfile

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.automation import AutomationModule

def test_real_formatting_preservation():
    """Test formatting preservation by typing into TextEdit and checking the result."""
    
    # Sample code with specific indentation patterns
    test_code = '''def calculate_fibonacci(n):
    """Calculate fibonacci number recursively."""
    if n <= 1:
        return n
    else:
        return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)

# Test the function
for i in range(5):
    result = calculate_fibonacci(i)
    print(f"fibonacci({i}) = {result}")'''
    
    print("Testing real formatting preservation...")
    print(f"Test code ({len(test_code)} chars, {test_code.count(chr(10))} newlines):")
    print("=" * 50)
    print(test_code)
    print("=" * 50)
    
    automation = AutomationModule()
    
    if not automation.is_macos:
        print("This test requires macOS")
        return
    
    try:
        # Open TextEdit
        print("\nOpening TextEdit...")
        subprocess.run(['open', '-a', 'TextEdit'], check=True)
        time.sleep(2)  # Wait for TextEdit to open
        
        # Create a new document
        subprocess.run(['osascript', '-e', '''
        tell application "TextEdit"
            activate
            make new document
        end tell
        '''], check=True)
        time.sleep(1)
        
        print("Typing test code using cliclick...")
        
        # Test cliclick typing
        if automation.has_cliclick:
            success = automation._cliclick_type(test_code)
            print(f"Cliclick typing result: {'SUCCESS' if success else 'FAILED'}")
            
            if success:
                print("\nTest completed! Check TextEdit to verify formatting preservation.")
                print("The code should have proper indentation and line breaks.")
                
                # Wait a moment for user to see the result
                time.sleep(2)
                
                # Get the text from TextEdit to verify
                try:
                    result = subprocess.run(['osascript', '-e', '''
                    tell application "TextEdit"
                        get text of front document
                    end tell
                    '''], capture_output=True, text=True, check=True)
                    
                    typed_text = result.stdout.strip()
                    
                    print("\nVerifying formatting preservation...")
                    print(f"Original lines: {len(test_code.splitlines())}")
                    print(f"Typed lines: {len(typed_text.splitlines())}")
                    
                    # Check if indentation is preserved
                    original_lines = test_code.splitlines()
                    typed_lines = typed_text.splitlines()
                    
                    formatting_preserved = True
                    for i, (orig, typed) in enumerate(zip(original_lines, typed_lines)):
                        orig_indent = len(orig) - len(orig.lstrip())
                        typed_indent = len(typed) - len(typed.lstrip())
                        
                        if orig_indent != typed_indent:
                            print(f"Line {i+1}: Indentation mismatch! Original: {orig_indent} spaces, Typed: {typed_indent} spaces")
                            formatting_preserved = False
                    
                    if formatting_preserved:
                        print("✅ Formatting preservation: SUCCESS")
                    else:
                        print("❌ Formatting preservation: FAILED")
                        
                except Exception as e:
                    print(f"Could not verify text from TextEdit: {e}")
        else:
            print("cliclick not available, cannot test")
            
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Close TextEdit
        try:
            subprocess.run(['osascript', '-e', '''
            tell application "TextEdit"
                close front document without saving
                quit
            end tell
            '''], check=False)
        except:
            pass

def test_edge_cases():
    """Test edge cases for text formatting."""
    
    automation = AutomationModule()
    
    print("\n" + "=" * 50)
    print("Testing edge cases...")
    
    # Test cases with various edge conditions
    edge_cases = [
        ("Empty lines", "line1\n\nline3\n\nline5"),
        ("Only spaces", "    \n        \n    "),
        ("Mixed indentation", "\tdef func():\n    print('mixed')\n\t\treturn True"),
        ("Special chars in code", 'print("Hello \\"World\\"")'),
        ("Unicode characters", "# Café naïve résumé\nprint('Unicode test')"),
    ]
    
    for test_name, test_text in edge_cases:
        print(f"\nTesting {test_name}:")
        print(f"Text: {repr(test_text)}")
        
        if automation.is_macos and automation.has_cliclick:
            success = automation._cliclick_type(test_text)
            print(f"Result: {'SUCCESS' if success else 'FAILED'}")
        else:
            print("Skipping (cliclick not available)")

if __name__ == "__main__":
    print("Formatting Preservation Test Suite")
    print("=" * 50)
    
    try:
        test_real_formatting_preservation()
        test_edge_cases()
        
        print("\n" + "=" * 50)
        print("Test suite completed!")
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)