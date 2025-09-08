#!/usr/bin/env python3
"""
Test script to identify and verify fixes for cliclick text formatting issues.
This test demonstrates the specific problems with newlines and special characters.
"""

import sys
import os
import tempfile
import subprocess
import time

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.automation import AutomationModule

def test_current_formatting_issues():
    """Test current formatting issues in cliclick method."""
    
    # Test case 1: Multi-line code with indentation
    python_code = '''def calculate_fibonacci(n):
    """Calculate fibonacci number recursively."""
    if n <= 1:
        return n
    else:
        return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)
        
# Test the function
result = calculate_fibonacci(5)
print(f"Fibonacci(5) = {result}")'''

    # Test case 2: Special characters that need proper escaping
    special_chars = '''# Special characters test
name = "John's App"
path = "/home/user/documents"
command = `ls -la`
price = $29.99
regex = r"\\d+\\.\\d+"
escaped = "He said \\"Hello\\""'''

    # Test case 3: Mixed content with various formatting challenges
    mixed_content = '''#!/bin/bash
# Script with mixed content
echo "Starting process..."

for i in {1..3}; do
    echo "Processing item $i"
    if [ $i -eq 2 ]; then
        echo "Special case: 'middle item'"
    fi
done

echo "Process complete!"'''

    automation = AutomationModule()
    
    print("Testing Current cliclick Formatting Issues")
    print("=" * 60)
    
    test_cases = [
        ("Python Code with Indentation", python_code),
        ("Special Characters", special_chars),
        ("Mixed Shell Script", mixed_content)
    ]
    
    for test_name, test_text in test_cases:
        print(f"\n--- {test_name} ---")
        print(f"Original text ({len(test_text)} chars, {test_text.count(chr(10))} newlines):")
        print("First 100 chars:", repr(test_text[:100]))
        
        if automation.is_macos and automation.has_cliclick:
            # Test the current formatting method
            try:
                formatted = automation._format_text_for_typing(test_text, 'cliclick')
                print(f"Formatted text: {repr(formatted[:100])}...")
                
                # Test if the formatting preserves structure
                original_lines = test_text.split('\n')
                formatted_lines = formatted.split('\n')
                
                print(f"Original lines: {len(original_lines)}")
                print(f"Formatted lines: {len(formatted_lines)}")
                
                if len(original_lines) == len(formatted_lines):
                    print("✅ Line count preserved")
                else:
                    print("❌ Line count changed - formatting issue detected")
                
                # Check for proper indentation preservation
                for i, (orig, fmt) in enumerate(zip(original_lines[:3], formatted_lines[:3])):
                    orig_indent = len(orig) - len(orig.lstrip())
                    fmt_indent = len(fmt) - len(fmt.lstrip())
                    if orig_indent == fmt_indent:
                        print(f"✅ Line {i+1}: Indentation preserved ({orig_indent} spaces)")
                    else:
                        print(f"❌ Line {i+1}: Indentation changed ({orig_indent} -> {fmt_indent})")
                
            except Exception as e:
                print(f"❌ Formatting failed: {e}")
        else:
            print("⚠️  cliclick not available for testing")
        
        print("-" * 40)

def test_special_character_escaping():
    """Test specific special character escaping issues."""
    
    print("\n" + "=" * 60)
    print("Testing Special Character Escaping")
    print("=" * 60)
    
    # Characters that commonly cause issues in cliclick
    test_chars = {
        'double_quotes': 'echo "Hello World"',
        'single_quotes': "echo 'Hello World'",
        'backticks': 'result=`date`',
        'dollar_signs': 'price=$29.99',
        'backslashes': 'path=C:\\Users\\Name',
        'newlines': 'line1\nline2\nline3',
        'mixed': 'echo "Price: $29.99" && echo \'Done\''
    }
    
    automation = AutomationModule()
    
    for char_type, test_text in test_chars.items():
        print(f"\n--- Testing {char_type} ---")
        print(f"Original: {repr(test_text)}")
        
        if automation.is_macos and automation.has_cliclick:
            try:
                formatted = automation._format_text_for_typing(test_text, 'cliclick')
                print(f"Formatted: {repr(formatted)}")
                
                # Check if formatting is safe for cliclick
                if '"' in formatted and not '\\"' in formatted:
                    print("❌ Unescaped double quotes detected")
                elif "'" in formatted and not "\\'" in formatted:
                    print("❌ Unescaped single quotes detected")
                elif '$' in formatted and not '\\$' in formatted:
                    print("❌ Unescaped dollar signs detected")
                else:
                    print("✅ Special characters properly escaped")
                    
            except Exception as e:
                print(f"❌ Formatting failed: {e}")
        else:
            print("⚠️  cliclick not available for testing")

if __name__ == "__main__":
    try:
        test_current_formatting_issues()
        test_special_character_escaping()
        
        print("\n" + "=" * 60)
        print("Issue identification completed!")
        print("Next step: Implement fixes for identified problems")
        
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)