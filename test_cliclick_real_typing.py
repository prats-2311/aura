#!/usr/bin/env python3
"""
Test script to verify actual cliclick typing behavior with real output.
This will help identify if there are issues with the actual typing process.
"""

import sys
import os
import tempfile
import subprocess
import time

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.automation import AutomationModule

def test_cliclick_typing_with_file_output():
    """Test cliclick typing by writing to a temporary file."""
    
    # Test content with various formatting challenges
    test_content = '''def fibonacci(n):
    """Calculate fibonacci number."""
    if n <= 1:
        return n
    else:
        return fibonacci(n-1) + fibonacci(n-2)

# Test with special characters
name = "John's Test"
path = "/home/user"
price = $29.99'''

    automation = AutomationModule()
    
    if not (automation.is_macos and automation.has_cliclick):
        print("⚠️  This test requires macOS with cliclick installed")
        return
    
    print("Testing cliclick typing with real file output")
    print("=" * 50)
    
    # Create a temporary file to type into
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
        temp_path = temp_file.name
    
    try:
        # Open the file in TextEdit for typing
        subprocess.run(['open', '-a', 'TextEdit', temp_path], check=True)
        time.sleep(2)  # Wait for TextEdit to open
        
        print(f"Typing test content to: {temp_path}")
        print(f"Original content ({len(test_content)} chars, {test_content.count(chr(10))} newlines):")
        print(repr(test_content))
        
        # Test the cliclick typing
        success = automation._cliclick_type(test_content)
        print(f"Typing result: {'SUCCESS' if success else 'FAILED'}")
        
        # Wait a moment for typing to complete
        time.sleep(1)
        
        # Read back the file content to verify formatting
        try:
            with open(temp_path, 'r') as f:
                typed_content = f.read()
            
            print(f"\nTyped content ({len(typed_content)} chars, {typed_content.count(chr(10))} newlines):")
            print(repr(typed_content))
            
            # Compare original vs typed
            original_lines = test_content.split('\n')
            typed_lines = typed_content.split('\n')
            
            print(f"\nComparison:")
            print(f"Original lines: {len(original_lines)}")
            print(f"Typed lines: {len(typed_lines)}")
            
            if test_content.strip() == typed_content.strip():
                print("✅ Content matches exactly!")
            else:
                print("❌ Content differs")
                
                # Show differences line by line
                for i, (orig, typed) in enumerate(zip(original_lines, typed_lines)):
                    if orig != typed:
                        print(f"  Line {i+1} differs:")
                        print(f"    Original: {repr(orig)}")
                        print(f"    Typed:    {repr(typed)}")
            
        except Exception as e:
            print(f"❌ Failed to read typed content: {e}")
        
    except Exception as e:
        print(f"❌ Test setup failed: {e}")
    
    finally:
        # Clean up
        try:
            os.unlink(temp_path)
        except:
            pass
        
        # Close TextEdit
        try:
            subprocess.run(['pkill', 'TextEdit'], capture_output=True)
        except:
            pass

def test_cliclick_multiline_method():
    """Test the multiline typing method specifically."""
    
    test_text = '''Line 1: Simple text
Line 2: With "quotes" and 'apostrophes'
Line 3: With $pecial characters
Line 4: Final line'''

    automation = AutomationModule()
    
    if not (automation.is_macos and automation.has_cliclick):
        print("⚠️  This test requires macOS with cliclick installed")
        return
    
    print("\nTesting cliclick multiline method")
    print("=" * 50)
    
    print(f"Test text: {repr(test_text)}")
    
    # Test the formatting first
    formatted = automation._format_text_for_typing(test_text, 'cliclick')
    print(f"Formatted: {repr(formatted)}")
    
    # Test the multiline method
    try:
        success = automation._cliclick_type_multiline(formatted)
        print(f"Multiline typing result: {'SUCCESS' if success else 'FAILED'}")
    except Exception as e:
        print(f"❌ Multiline typing failed: {e}")

if __name__ == "__main__":
    print("cliclick Real Typing Test Suite")
    print("This test will open TextEdit and type content")
    print("Make sure you have cliclick installed: brew install cliclick")
    print()
    
    try:
        test_cliclick_multiline_method()
        
        # Ask user if they want to run the file output test
        response = input("\nRun file output test? This will open TextEdit (y/n): ").lower()
        if response == 'y':
            test_cliclick_typing_with_file_output()
        
        print("\nTest completed!")
        
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)