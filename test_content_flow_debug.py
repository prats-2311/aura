#!/usr/bin/env python3
"""
Comprehensive test to trace the exact content flow from reasoning to typing.
This will help identify where newlines are being lost in the pipeline.
"""

import sys
import os
import json

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.reasoning import ReasoningModule
from modules.automation import AutomationModule

def test_reasoning_content_generation():
    """Test what content the reasoning module would generate."""
    
    print("Testing Reasoning Module Content Generation")
    print("=" * 60)
    
    # Simulate a typical code generation request
    user_command = "write a fibonacci function in python"
    screen_context = {
        "application": "TextEdit",
        "window_title": "touch.py",
        "cursor_position": {"x": 100, "y": 200}
    }
    
    reasoning = ReasoningModule()
    
    # Test the prompt building
    try:
        prompt = reasoning._build_prompt(user_command, screen_context)
        print(f"Generated prompt length: {len(prompt)} chars")
        newline_char = '\n'
        print(f"Prompt contains newlines: {newline_char in prompt}")
        print(f"First 200 chars of prompt: {repr(prompt[:200])}")
    except Exception as e:
        print(f"Prompt building failed: {e}")
        return
    
    # Simulate what a typical API response would look like
    simulated_api_response = {
        "choices": [
            {
                "message": {
                    "content": '''```json
{
    "plan": [
        {
            "action": "type",
            "text": "def fibonacci(n):\\n    if n <= 0:\\n        return []\\n    if n == 1:\\n        return [0]\\n    seq = [0, 1]\\n    while len(seq) < n:\\n        seq.append(seq[-1] + seq[-2])\\n    return seq\\n\\nif __name__ == \\"__main__\\":\\n    n = int(input())\\n    print(fibonacci(n))"
        }
    ],
    "metadata": {
        "confidence": 0.9,
        "estimated_duration": 5.0
    }
}
```'''
                }
            }
        ]
    }
    
    print(f"\\nSimulated API response content:")
    content = simulated_api_response["choices"][0]["message"]["content"]
    print(f"  Raw content length: {len(content)} chars")
    escaped_newline = '\\n'
    print(f"  Raw content contains \\\\n: {escaped_newline in content}")
    print(f"  Raw content contains actual newlines: {newline_char in content}")
    print(f"  First 200 chars: {repr(content[:200])}")
    
    # Test the response parsing
    try:
        action_plan = reasoning._parse_response(simulated_api_response)
        print(f"\\nParsed action plan:")
        print(f"  Plan has {len(action_plan.get('plan', []))} actions")
        
        if action_plan.get('plan'):
            first_action = action_plan['plan'][0]
            if first_action.get('action') == 'type':
                text_content = first_action.get('text', '')
                print(f"  Type action text length: {len(text_content)} chars")
                print(f"  Type action text contains \\\\n: {escaped_newline in text_content}")
                print(f"  Type action text contains actual newlines: {newline_char in text_content}")
                print(f"  First 100 chars of text: {repr(text_content[:100])}")
                
                # Test if \\n sequences are properly converted to actual newlines
                if escaped_newline in text_content:
                    print(f"  ⚠️  Text contains escaped newlines (\\\\n) - these need to be converted!")
                    converted_text = text_content.replace(escaped_newline, newline_char)
                    print(f"  After conversion: {len(converted_text)} chars, {converted_text.count(chr(10))} actual newlines")
                    print(f"  Converted first 100 chars: {repr(converted_text[:100])}")
                    return converted_text
                else:
                    print(f"  ✅ Text contains actual newlines")
                    return text_content
                    
    except Exception as e:
        print(f"Response parsing failed: {e}")
        return None

def test_automation_content_processing(text_content):
    """Test how the automation module processes the text content."""
    
    print(f"\\nTesting Automation Module Content Processing")
    print("=" * 60)
    
    if not text_content:
        print("No text content to test")
        return
    
    automation = AutomationModule()
    
    # Test the action format that would be passed to execute_action
    type_action = {
        "action": "type",
        "text": text_content
    }
    
    print(f"Type action format:")
    print(f"  Action type: {type_action['action']}")
    print(f"  Text length: {len(type_action['text'])} chars")
    newline_char = '\n'
    print(f"  Text contains actual newlines: {newline_char in type_action['text']}")
    print(f"  Text newline count: {type_action['text'].count(chr(10))}")
    print(f"  First 100 chars: {repr(type_action['text'][:100])}")
    
    # Test the validation
    try:
        is_valid, error_msg = automation.validate_action_format(type_action)
        if is_valid:
            print(f"  ✅ Action format is valid")
        else:
            print(f"  ❌ Action format invalid: {error_msg}")
            return
    except Exception as e:
        print(f"  ❌ Validation failed: {e}")
        return
    
    # Test the text validation
    try:
        is_valid_text = automation._validate_text_input(type_action['text'])
        if is_valid_text:
            print(f"  ✅ Text input is valid")
        else:
            print(f"  ❌ Text input is invalid")
            return
    except Exception as e:
        print(f"  ❌ Text validation failed: {e}")
        return
    
    # Test the cliclick formatting
    if automation.is_macos and automation.has_cliclick:
        print(f"\\n  Testing cliclick text formatting:")
        
        try:
            formatted_text = automation._format_text_for_typing(type_action['text'], 'cliclick')
            print(f"    Formatted length: {len(formatted_text)} chars")
            print(f"    Formatted contains newlines: {newline_char in formatted_text}")
            print(f"    Formatted newline count: {formatted_text.count(chr(10))}")
            print(f"    First 100 formatted chars: {repr(formatted_text[:100])}")
            
            if formatted_text.count(newline_char) == type_action['text'].count(newline_char):
                print(f"    ✅ Newlines preserved in formatting")
            else:
                print(f"    ❌ Newlines lost in formatting!")
                print(f"    Original: {type_action['text'].count(newline_char)} newlines")
                print(f"    Formatted: {formatted_text.count(newline_char)} newlines")
            
            # Test the multiline detection
            print(f"\\n  Testing multiline detection:")
            will_use_multiline = newline_char in type_action['text']
            print(f"    Original text has newlines: {will_use_multiline}")
            
            if will_use_multiline:
                print(f"    ✅ Will use _cliclick_type_multiline() method")
                
                # Simulate the multiline method
                lines = formatted_text.split(newline_char)
                print(f"    Will split into {len(lines)} lines")
                print(f"    Will need {len(lines) - 1} Return key presses")
                
                # Show first few lines
                for i, line in enumerate(lines[:3]):
                    if line.strip():
                        print(f"      Line {i+1}: {repr(line)}")
                    else:
                        print(f"      Line {i+1}: (empty)")
                
                if len(lines) > 3:
                    print(f"      ... and {len(lines) - 3} more lines")
                    
            else:
                print(f"    ❌ Will use single-line method (this would lose newlines!)")
                
        except Exception as e:
            print(f"    ❌ cliclick formatting failed: {e}")
    
    else:
        print(f"  ⚠️  cliclick not available for testing")

def test_json_parsing_edge_cases():
    """Test edge cases in JSON parsing that might affect newlines."""
    
    print(f"\\nTesting JSON Parsing Edge Cases")
    print("=" * 60)
    
    # Test different ways newlines might be encoded in JSON
    test_cases = [
        {
            'name': 'Properly escaped newlines in JSON',
            'json_content': '{"text": "line1\\\\nline2\\\\nline3"}',
            'expected_newlines': 2
        },
        {
            'name': 'Double-escaped newlines',
            'json_content': '{"text": "line1\\\\\\\\nline2\\\\\\\\nline3"}',
            'expected_newlines': 0  # These would be literal \\n characters
        },
        {
            'name': 'Actual newlines in JSON (invalid but might happen)',
            'json_content': '{"text": "line1\\nline2\\nline3"}',
            'expected_newlines': 2
        }
    ]
    
    for test_case in test_cases:
        print(f"\\n  {test_case['name']}:")
        print(f"    JSON: {repr(test_case['json_content'])}")
        
        try:
            parsed = json.loads(test_case['json_content'])
            text = parsed['text']
            actual_newlines = text.count('\n')
            
            print(f"    Parsed text: {repr(text)}")
            print(f"    Actual newlines: {actual_newlines}")
            print(f"    Expected newlines: {test_case['expected_newlines']}")
            
            if actual_newlines == test_case['expected_newlines']:
                print(f"    ✅ Newline count matches expectation")
            else:
                print(f"    ❌ Newline count mismatch!")
                
        except json.JSONDecodeError as e:
            print(f"    ❌ JSON parsing failed: {e}")

def main():
    """Run the complete content flow debug test."""
    
    print("Content Flow Debug Test Suite")
    print("Tracing content from reasoning to typing")
    print("=" * 80)
    
    try:
        # Test reasoning content generation
        text_content = test_reasoning_content_generation()
        
        # Test automation content processing
        test_automation_content_processing(text_content)
        
        # Test JSON parsing edge cases
        test_json_parsing_edge_cases()
        
        print("\\n" + "=" * 80)
        print("🔍 CONTENT FLOW ANALYSIS COMPLETE")
        
        print("\\n🎯 Key Findings:")
        print("  1. Check if reasoning module generates proper newlines")
        print("  2. Verify JSON parsing preserves newlines correctly")
        print("  3. Confirm automation module receives newlines intact")
        print("  4. Validate cliclick formatting preserves newlines")
        print("  5. Ensure multiline detection works correctly")
        
        print("\\n⚠️  Common Issues to Look For:")
        print("  - Escaped newlines (\\\\n) not being converted to actual newlines (\\n)")
        print("  - JSON parsing removing or corrupting newlines")
        print("  - Text formatting step removing newlines")
        print("  - Multiline detection failing due to missing newlines")
        
    except Exception as e:
        print(f"Content flow test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)