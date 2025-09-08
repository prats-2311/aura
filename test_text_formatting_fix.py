#!/usr/bin/env python3
"""
Test script to verify text formatting fixes in cliclick typing method.
Tests multi-line code examples and special character handling.
"""

import sys
import os
import tempfile
import subprocess
import time

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.automation import AutomationModule

def test_multiline_code_formatting():
    """Test that multi-line code preserves formatting and indentation."""
    
    # Sample Python code with proper indentation
    python_code = '''def hello_world():
    print("Hello, World!")
    if True:
        print("Indented properly")
        for i in range(3):
            print(f"Loop {i}")'''
    
    # Sample JavaScript code with nested structures
    javascript_code = '''function calculateSum(a, b) {
    if (a && b) {
        return a + b;
    } else {
        console.log("Invalid input");
        return 0;
    }
}'''
    
    # Mixed content with special characters
    mixed_content = '''# Configuration
name = "test-app"
version = "1.0.0"

# Special characters: @#$%^&*()
email = "user@example.com"
path = "/home/user/documents"'''
    
    automation = AutomationModule()
    
    print("Testing multi-line code formatting...")
    
    # Test cases
    test_cases = [
        ("Python code", python_code),
        ("JavaScript code", javascript_code),
        ("Mixed content", mixed_content)
    ]
    
    for test_name, test_text in test_cases:
        print(f"\n--- Testing {test_name} ---")
        print(f"Original text ({len(test_text)} chars, {test_text.count(chr(10))} newlines):")
        print(repr(test_text))
        
        # Test cliclick typing if available
        if automation.is_macos and automation.has_cliclick:
            print("\nTesting cliclick typing...")
            success = automation._cliclick_type(test_text)
            print(f"cliclick result: {'SUCCESS' if success else 'FAILED'}")
        
        # Test AppleScript typing
        if automation.is_macos:
            print("\nTesting AppleScript typing...")
            success = automation._macos_type(test_text)
            print(f"AppleScript result: {'SUCCESS' if success else 'FAILED'}")
        
        print("-" * 50)

def test_special_characters():
    """Test handling of special characters that need escaping."""
    
    special_chars_test = '''Special characters test:
- Quotes: "double" and 'single'
- Backslashes: \\ and \\n and \\t
- Symbols: @#$%^&*()[]{}
- Unicode: café, naïve, résumé'''
    
    automation = AutomationModule()
    
    print("\n=== Testing Special Characters ===")
    print(f"Test text: {repr(special_chars_test)}")
    
    if automation.is_macos and automation.has_cliclick:
        print("\nTesting cliclick with special characters...")
        success = automation._cliclick_type(special_chars_test)
        print(f"cliclick result: {'SUCCESS' if success else 'FAILED'}")
    
    if automation.is_macos:
        print("\nTesting AppleScript with special characters...")
        success = automation._macos_type(special_chars_test)
        print(f"AppleScript result: {'SUCCESS' if success else 'FAILED'}")

def test_formatting_validation():
    """Test the new formatting validation functionality."""
    
    test_text = '''def example_function():
    # This is a comment
    x = 1
    y = 2
    return x + y'''
    
    automation = AutomationModule()
    
    print("\n=== Testing Formatting Validation ===")
    
    # Test the new text preprocessing method
    if hasattr(automation, '_format_text_for_typing'):
        print("Testing text preprocessing...")
        
        cliclick_formatted = automation._format_text_for_typing(test_text, 'cliclick')
        applescript_formatted = automation._format_text_for_typing(test_text, 'applescript')
        
        print(f"Original: {repr(test_text)}")
        print(f"Cliclick formatted: {repr(cliclick_formatted)}")
        print(f"AppleScript formatted: {repr(applescript_formatted)}")
    else:
        print("Text preprocessing method not yet implemented")

if __name__ == "__main__":
    print("Text Formatting Fix Test Suite")
    print("=" * 50)
    
    try:
        test_multiline_code_formatting()
        test_special_characters()
        test_formatting_validation()
        
        print("\n" + "=" * 50)
        print("Test suite completed!")
        
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)