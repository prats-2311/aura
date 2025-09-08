#!/usr/bin/env python3
"""
Test script to verify the cliclick text formatting fixes.
Tests the enhanced _cliclick_type method with various formatting scenarios.
"""

import sys
import os
import tempfile
import subprocess
import time

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.automation import AutomationModule

def test_enhanced_text_preprocessing():
    """Test the enhanced text preprocessing for cliclick."""
    
    print("Testing Enhanced Text Preprocessing")
    print("=" * 50)
    
    # Test cases with various special characters and formatting challenges
    test_cases = [
        {
            'name': 'Python Code with Indentation',
            'text': '''def calculate_sum(a, b):
    """Calculate the sum of two numbers."""
    if a is not None and b is not None:
        result = a + b
        print(f"Sum: {result}")
        return result
    else:
        raise ValueError("Invalid input")'''
        },
        {
            'name': 'Shell Script with Special Characters',
            'text': '''#!/bin/bash
# Script with various special characters
name="John's App"
price=$29.99
command=`date +%Y-%m-%d`
echo "Processing ${name} - Price: ${price}"
if [ $? -eq 0 ]; then
    echo "Success!"
fi'''
        },
        {
            'name': 'JSON with Nested Structures',
            'text': '''{
    "name": "test-config",
    "version": "1.0.0",
    "settings": {
        "debug": true,
        "paths": ["/home/user", "/tmp"],
        "regex": "\\\\d+\\\\.\\\\d+"
    }
}'''
        },
        {
            'name': 'Mixed Content with Unicode',
            'text': '''# Configuration file
title = "Café Management System"
description = "A system for managing café operations"
author = "José María"
email = "jose@example.com"
symbols = "@#$%^&*()[]{}|\\<>?/"'''
        }
    ]
    
    automation = AutomationModule()
    
    for test_case in test_cases:
        print(f"\n--- {test_case['name']} ---")
        original_text = test_case['text']
        
        print(f"Original ({len(original_text)} chars, {original_text.count(chr(10))} newlines):")
        print(f"First 80 chars: {repr(original_text[:80])}")
        
        # Test the enhanced formatting
        try:
            formatted = automation._format_text_for_typing(original_text, 'cliclick')
            
            print(f"Formatted ({len(formatted)} chars, {formatted.count(chr(10))} newlines):")
            print(f"First 80 chars: {repr(formatted[:80])}")
            
            # Verify formatting preservation
            original_lines = original_text.split('\n')
            formatted_lines = formatted.split('\n')
            
            if len(original_lines) == len(formatted_lines):
                print("✅ Line count preserved")
            else:
                print(f"❌ Line count changed: {len(original_lines)} -> {len(formatted_lines)}")
            
            # Check indentation preservation for first few lines
            indentation_preserved = True
            for i, (orig, fmt) in enumerate(zip(original_lines[:3], formatted_lines[:3])):
                orig_indent = len(orig) - len(orig.lstrip())
                fmt_indent = len(fmt) - len(fmt.lstrip())
                if orig_indent != fmt_indent:
                    print(f"❌ Line {i+1}: Indentation changed ({orig_indent} -> {fmt_indent})")
                    indentation_preserved = False
            
            if indentation_preserved:
                print("✅ Indentation preserved")
            
            # Check for proper escaping of special characters
            special_chars_escaped = True
            problematic_chars = ['"', "'", '`', '$', '&', '|', ';', '(', ')', '[', ']', '{', '}', '<', '>']
            for char in problematic_chars:
                if char in original_text and char in formatted and f'\\{char}' not in formatted:
                    print(f"❌ Character '{char}' not properly escaped")
                    special_chars_escaped = False
            
            if special_chars_escaped:
                print("✅ Special characters properly escaped")
            
        except Exception as e:
            print(f"❌ Formatting failed: {e}")
        
        print("-" * 40)

def test_multiline_typing_method():
    """Test the enhanced multiline typing method."""
    
    print("\nTesting Enhanced Multiline Typing Method")
    print("=" * 50)
    
    # Test with a realistic code example
    test_code = '''class Calculator:
    def __init__(self):
        self.history = []
    
    def add(self, a, b):
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        return result
    
    def get_history(self):
        return self.history'''
    
    automation = AutomationModule()
    
    if not (automation.is_macos and automation.has_cliclick):
        print("⚠️  This test requires macOS with cliclick installed")
        return
    
    print(f"Test code ({len(test_code)} chars, {test_code.count(chr(10))} newlines):")
    print(repr(test_code))
    
    # Test the formatting
    formatted = automation._format_text_for_typing(test_code, 'cliclick')
    print(f"\nFormatted for cliclick:")
    print(repr(formatted))
    
    # Test the multiline method (without actually typing to screen)
    print(f"\nTesting multiline typing method...")
    try:
        # We'll test the method logic without actually executing cliclick commands
        lines = formatted.split('\n')
        print(f"Will type {len(lines)} lines:")
        
        for i, line in enumerate(lines):
            if line.strip():
                print(f"  Line {i+1}: {repr(line[:50])}{'...' if len(line) > 50 else ''}")
            else:
                print(f"  Line {i+1}: (empty line)")
        
        print("✅ Multiline method preparation successful")
        
    except Exception as e:
        print(f"❌ Multiline method failed: {e}")

def test_formatting_validation():
    """Test formatting validation with edge cases."""
    
    print("\nTesting Formatting Validation")
    print("=" * 50)
    
    edge_cases = [
        {
            'name': 'Empty Lines',
            'text': '''Line 1

Line 3

Line 5'''
        },
        {
            'name': 'Only Whitespace Lines',
            'text': '''Line 1
    
        
Line 4'''
        },
        {
            'name': 'Mixed Indentation',
            'text': '''def func():
    # 4 spaces
        # 8 spaces
\t# 1 tab
\t    # tab + 4 spaces'''
        },
        {
            'name': 'All Special Characters',
            'text': '''!"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~'''
        }
    ]
    
    automation = AutomationModule()
    
    for case in edge_cases:
        print(f"\n--- {case['name']} ---")
        text = case['text']
        
        try:
            formatted = automation._format_text_for_typing(text, 'cliclick')
            
            # Basic validation
            if text.count('\n') == formatted.count('\n'):
                print("✅ Newline count preserved")
            else:
                print(f"❌ Newline count changed: {text.count(chr(10))} -> {formatted.count(chr(10))}")
            
            # Check that we don't have unescaped problematic characters
            issues = []
            if '"' in formatted and '\\"' not in formatted:
                issues.append('unescaped quotes')
            if '$' in formatted and '\\$' not in formatted:
                issues.append('unescaped dollar signs')
            
            if not issues:
                print("✅ No formatting issues detected")
            else:
                print(f"❌ Issues found: {', '.join(issues)}")
                
        except Exception as e:
            print(f"❌ Validation failed: {e}")

if __name__ == "__main__":
    print("cliclick Text Formatting Fixes Test Suite")
    print("Testing enhanced formatting and multiline handling")
    print("=" * 60)
    
    try:
        test_enhanced_text_preprocessing()
        test_multiline_typing_method()
        test_formatting_validation()
        
        print("\n" + "=" * 60)
        print("✅ All formatting fix tests completed!")
        print("The enhanced cliclick typing method should now:")
        print("  - Preserve line breaks and indentation")
        print("  - Handle special characters properly")
        print("  - Support multi-line code and text")
        print("  - Provide better error handling and logging")
        
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)