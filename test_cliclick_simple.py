#!/usr/bin/env python3
"""
Simple test for cliclick text formatting fix.
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.automation import AutomationModule

def test_simple_multiline():
    """Test simple multi-line text."""
    
    test_text = """line 1
line 2
line 3"""
    
    automation = AutomationModule()
    
    print("Testing simple multi-line text...")
    print(f"Text: {repr(test_text)}")
    
    if automation.is_macos and automation.has_cliclick:
        print("Testing cliclick...")
        success = automation._cliclick_type(test_text)
        print(f"Result: {'SUCCESS' if success else 'FAILED'}")
    else:
        print("cliclick not available")

def test_text_preprocessing():
    """Test the text preprocessing method."""
    
    test_text = '''def hello():
    print("Hello")
    return True'''
    
    automation = AutomationModule()
    
    print("\nTesting text preprocessing...")
    
    if hasattr(automation, '_format_text_for_typing'):
        cliclick_formatted = automation._format_text_for_typing(test_text, 'cliclick')
        applescript_formatted = automation._format_text_for_typing(test_text, 'applescript')
        
        print(f"Original: {repr(test_text)}")
        print(f"Cliclick: {repr(cliclick_formatted)}")
        print(f"AppleScript: {repr(applescript_formatted)}")
    else:
        print("_format_text_for_typing method not found")

if __name__ == "__main__":
    test_simple_multiline()
    test_text_preprocessing()