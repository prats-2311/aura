#!/usr/bin/env python3
"""
Unit tests for text preprocessing functionality in the automation module.
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.automation import AutomationModule

def test_cliclick_text_formatting():
    """Test text formatting for cliclick method."""
    
    automation = AutomationModule()
    
    test_cases = [
        # (input, expected_output, description)
        ('simple text', 'simple text', 'Simple text should remain unchanged'),
        ('text with "quotes"', 'text with \\"quotes\\"', 'Double quotes should be escaped'),
        ("text with 'single quotes'", "text with \\'single quotes\\'", 'Single quotes should be escaped'),
        ('text with \\backslash', 'text with \\\\backslash', 'Backslashes should be escaped'),
        ('text with $variable', 'text with \\$variable', 'Dollar signs should be escaped'),
        ('text with `backticks`', 'text with \\`backticks\\`', 'Backticks should be escaped'),
        ('line1\nline2', 'line1\nline2', 'Newlines should be preserved'),
        ('mixed\n"quotes"\n$vars', 'mixed\n\\"quotes\\"\n\\$vars', 'Complex text should be properly escaped'),
    ]
    
    print("Testing cliclick text formatting...")
    
    for input_text, expected, description in test_cases:
        result = automation._format_text_for_typing(input_text, 'cliclick')
        
        if result == expected:
            print(f"✅ {description}")
        else:
            print(f"❌ {description}")
            print(f"   Input: {repr(input_text)}")
            print(f"   Expected: {repr(expected)}")
            print(f"   Got: {repr(result)}")

def test_applescript_text_formatting():
    """Test text formatting for AppleScript method."""
    
    automation = AutomationModule()
    
    test_cases = [
        # (input, expected_output, description)
        ('simple text', 'simple text', 'Simple text should remain unchanged'),
        ('text with "quotes"', 'text with \\"quotes\\"', 'Double quotes should be escaped'),
        ('text with \\backslash', 'text with \\\\backslash', 'Backslashes should be escaped'),
        ('text with\rcarriage return', 'text with\\rcarriage return', 'Carriage returns should be escaped'),
        ('line1\nline2', 'line1\nline2', 'Newlines should be preserved'),
        ('mixed\n"quotes"\r\\backslash', 'mixed\n\\"quotes\\"\\r\\\\backslash', 'Complex text should be properly escaped'),
    ]
    
    print("\nTesting AppleScript text formatting...")
    
    for input_text, expected, description in test_cases:
        result = automation._format_text_for_typing(input_text, 'applescript')
        
        if result == expected:
            print(f"✅ {description}")
        else:
            print(f"❌ {description}")
            print(f"   Input: {repr(input_text)}")
            print(f"   Expected: {repr(expected)}")
            print(f"   Got: {repr(result)}")

def test_multiline_splitting():
    """Test that multi-line text is properly split and handled."""
    
    automation = AutomationModule()
    
    test_text = '''def hello():
    print("Hello")
    if True:
        print("World")'''
    
    print("\nTesting multi-line text splitting...")
    
    lines = test_text.split('\n')
    expected_lines = ['def hello():', '    print("Hello")', '    if True:', '        print("World")']
    
    if lines == expected_lines:
        print("✅ Multi-line text splits correctly")
    else:
        print("❌ Multi-line text splitting failed")
        print(f"   Expected: {expected_lines}")
        print(f"   Got: {lines}")
    
    # Test that each line preserves indentation
    for i, line in enumerate(lines):
        leading_spaces = len(line) - len(line.lstrip())
        expected_spaces = [0, 4, 4, 8][i]  # Expected indentation for each line
        
        if leading_spaces == expected_spaces:
            print(f"✅ Line {i+1} has correct indentation ({leading_spaces} spaces)")
        else:
            print(f"❌ Line {i+1} indentation mismatch: expected {expected_spaces}, got {leading_spaces}")

def test_performance_logging():
    """Test that performance logging includes formatting-related metrics."""
    
    automation = AutomationModule()
    
    # Clear any existing performance history
    if hasattr(automation, 'performance_history'):
        automation.performance_history = []
    
    test_text = "line1\nline2\nline3"
    
    print("\nTesting performance logging...")
    
    if automation.is_macos and automation.has_cliclick:
        # This will create performance log entries
        success = automation._cliclick_type(test_text)
        
        if hasattr(automation, 'performance_history') and automation.performance_history:
            latest_record = automation.performance_history[-1]
            
            # Check if newlines_count is logged
            if 'newlines_count' in latest_record:
                expected_newlines = test_text.count('\n')
                actual_newlines = latest_record['newlines_count']
                
                if actual_newlines == expected_newlines:
                    print(f"✅ Performance logging includes newlines count ({actual_newlines})")
                else:
                    print(f"❌ Newlines count mismatch: expected {expected_newlines}, got {actual_newlines}")
            else:
                print("❌ Performance logging missing newlines_count")
            
            # Check other expected fields
            expected_fields = ['timestamp', 'execution_time', 'path_type', 'success', 'action', 'text_length']
            for field in expected_fields:
                if field in latest_record:
                    print(f"✅ Performance logging includes {field}")
                else:
                    print(f"❌ Performance logging missing {field}")
        else:
            print("❌ No performance history recorded")
    else:
        print("⏭️  Skipping performance test (cliclick not available)")

if __name__ == "__main__":
    print("Text Preprocessing Unit Tests")
    print("=" * 50)
    
    try:
        test_cliclick_text_formatting()
        test_applescript_text_formatting()
        test_multiline_splitting()
        test_performance_logging()
        
        print("\n" + "=" * 50)
        print("Unit tests completed!")
        
    except Exception as e:
        print(f"Tests failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)