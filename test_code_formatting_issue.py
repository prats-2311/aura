#!/usr/bin/env python3
"""
Test script to reproduce and fix the code formatting issue.
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orchestrator import Orchestrator

def test_single_line_formatter():
    """Test the single-line code formatter directly."""
    print("=== Testing Single-Line Code Formatter ===")
    
    orchestrator = Orchestrator()
    
    # Test case 1: Python fibonacci function (like in your image)
    single_line_python = "def fibonacci(n): a, b = 0, 1 result = [] for _ in range(n): result.append(a) a, b = b, a + b return result if __name__ == '__main__': n = 10 print(fibonacci(n))"
    
    print("Original single-line code:")
    print(repr(single_line_python))
    print()
    
    formatted = orchestrator._format_single_line_code(single_line_python)
    
    print("Formatted code:")
    print(formatted)
    print()
    
    # Test case 2: JavaScript function
    single_line_js = "function sortArray(arr) { return arr.sort((a, b) => a - b); } console.log(sortArray([3, 1, 4, 1, 5, 9, 2, 6]));"
    
    print("JavaScript single-line code:")
    print(repr(single_line_js))
    print()
    
    formatted_js = orchestrator._format_single_line_code(single_line_js)
    
    print("Formatted JavaScript:")
    print(formatted_js)
    print()
    
    return formatted != single_line_python or formatted_js != single_line_js

def test_content_generation_formatting():
    """Test the content generation with formatting."""
    print("=== Testing Content Generation Formatting ===")
    
    # Simulate what happens during content generation
    orchestrator = Orchestrator()
    
    # Test the content cleaning and formatting pipeline
    test_content = "def fibonacci(n): a, b = 0, 1 result = [] for _ in range(n): result.append(a) a, b = b, a + b return result"
    
    print("Test content before processing:")
    print(repr(test_content))
    print()
    
    # Simulate the content processing pipeline
    cleaned_content = orchestrator._clean_generated_content(test_content)
    print("After cleaning:")
    print(repr(cleaned_content))
    print()
    
    # Check if single-line formatting would be applied
    lines = cleaned_content.split('\n')
    if len(lines) == 1 and len(cleaned_content) > 50:
        print("SINGLE-LINE CODE DETECTED - Applying formatting")
        formatted_content = orchestrator._format_single_line_code(cleaned_content)
        print("After formatting:")
        print(formatted_content)
        return True
    else:
        print("No single-line formatting needed")
        return False

def main():
    """Run formatting tests."""
    print("Testing code formatting functionality...\n")
    
    try:
        test1_passed = test_single_line_formatter()
        test2_passed = test_content_generation_formatting()
        
        print("=== Test Results ===")
        print(f"Single-line formatter test: {'PASS' if test1_passed else 'FAIL'}")
        print(f"Content generation test: {'PASS' if test2_passed else 'FAIL'}")
        
        if test1_passed and test2_passed:
            print("✅ Formatting functionality is working")
        else:
            print("❌ Formatting functionality needs fixes")
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()