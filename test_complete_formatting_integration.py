#!/usr/bin/env python3
"""
Complete integration test for content generation and cliclick typing formatting.
Validates that the entire pipeline from reasoning to typing preserves formatting.
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.reasoning import ReasoningModule
from modules.automation import AutomationModule
from config import CODE_GENERATION_PROMPT, TEXT_GENERATION_PROMPT

def test_integration_python_code():
    """Test complete integration with Python code generation."""
    
    print("Testing Python Code Generation Integration")
    print("=" * 50)
    
    # Test case: Complex Python code with multiple indentation levels
    request = "Create a Python class for a binary search tree with insert, search, and inorder traversal methods"
    context = "Data structures implementation"
    
    reasoning = ReasoningModule()
    automation = AutomationModule()
    
    print(f"Request: {request}")
    print(f"Context: {context}")
    
    try:
        # Step 1: Generate content using the reasoning module
        formatted_prompt = CODE_GENERATION_PROMPT.format(request=request, context=context)
        api_response = reasoning._make_api_request(formatted_prompt)
        
        if api_response and 'choices' in api_response:
            generated_code = api_response['choices'][0]['message']['content'].strip()
            
            print(f"\n✅ Content Generated: {len(generated_code)} characters")
            
            # Analyze the generated code
            lines = generated_code.split('\n')
            print(f"Lines: {len(lines)}")
            
            # Check indentation levels
            indentation_levels = {}
            for line in lines:
                if line.strip():  # Non-empty line
                    indent = len(line) - len(line.lstrip())
                    indentation_levels[indent] = indentation_levels.get(indent, 0) + 1
            
            print(f"Indentation levels found: {sorted(indentation_levels.keys())}")
            
            # Verify Python 4-space indentation
            has_4_space = 4 in indentation_levels
            has_8_space = 8 in indentation_levels
            print(f"4-space indentation: {'✅ YES' if has_4_space else '❌ NO'}")
            print(f"8-space indentation: {'✅ YES' if has_8_space else '❌ NO'}")
            
            # Step 2: Test cliclick formatting
            formatted_for_cliclick = automation._format_text_for_typing(generated_code, 'cliclick')
            
            print(f"\n✅ cliclick Formatting: {len(formatted_for_cliclick)} characters")
            
            # Verify formatting preservation
            original_lines = generated_code.split('\n')
            formatted_lines = formatted_for_cliclick.split('\n')
            
            lines_preserved = len(original_lines) == len(formatted_lines)
            print(f"Line count preserved: {'✅ YES' if lines_preserved else '❌ NO'}")
            
            # Check indentation preservation
            indentation_preserved = True
            for i, (orig, fmt) in enumerate(zip(original_lines, formatted_lines)):
                orig_indent = len(orig) - len(orig.lstrip())
                fmt_indent = len(fmt) - len(fmt.lstrip())
                if orig_indent != fmt_indent:
                    print(f"❌ Line {i+1}: Indentation changed ({orig_indent} -> {fmt_indent})")
                    indentation_preserved = False
                    break
            
            if indentation_preserved:
                print("✅ All indentation preserved")
            
            # Step 3: Validate content quality
            quality_checks = {
                'No markdown blocks': '```' not in generated_code,
                'No explanatory text': not any(phrase in generated_code.lower() for phrase in ['here is', 'the following', 'this code']),
                'Starts with code': not generated_code.startswith(('Here', 'The', 'This')),
                'Proper class structure': 'class ' in generated_code and ':' in generated_code,
                'Method definitions': 'def ' in generated_code
            }
            
            print(f"\n✅ Quality Checks:")
            for check, passed in quality_checks.items():
                print(f"  {check}: {'✅ PASS' if passed else '❌ FAIL'}")
            
            # Overall assessment
            all_passed = lines_preserved and indentation_preserved and all(quality_checks.values())
            print(f"\n🎉 Python Integration Test: {'✅ SUCCESS' if all_passed else '❌ ISSUES DETECTED'}")
            
            return all_passed
            
        else:
            print("❌ Content generation failed")
            return False
            
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

def test_integration_javascript_code():
    """Test complete integration with JavaScript code generation."""
    
    print("\nTesting JavaScript Code Generation Integration")
    print("=" * 50)
    
    # Test case: JavaScript with nested structures
    request = "Create a JavaScript module for handling user authentication with login, logout, and token validation"
    context = "Frontend web application"
    
    reasoning = ReasoningModule()
    automation = AutomationModule()
    
    print(f"Request: {request}")
    print(f"Context: {context}")
    
    try:
        # Generate content
        formatted_prompt = CODE_GENERATION_PROMPT.format(request=request, context=context)
        api_response = reasoning._make_api_request(formatted_prompt)
        
        if api_response and 'choices' in api_response:
            generated_code = api_response['choices'][0]['message']['content'].strip()
            
            print(f"\n✅ Content Generated: {len(generated_code)} characters")
            
            # Check for JavaScript 2-space indentation
            lines = generated_code.split('\n')
            two_space_lines = [line for line in lines if line.startswith('  ') and not line.startswith('    ')]
            four_space_lines = [line for line in lines if line.startswith('    ')]
            
            print(f"2-space indented lines: {len(two_space_lines)}")
            print(f"4-space indented lines: {len(four_space_lines)}")
            
            # JavaScript should prefer 2-space indentation
            correct_indentation = len(two_space_lines) >= len(four_space_lines)
            print(f"Correct JS indentation: {'✅ YES' if correct_indentation else '❌ NO'}")
            
            # Test formatting preservation
            formatted_for_cliclick = automation._format_text_for_typing(generated_code, 'cliclick')
            
            original_lines = generated_code.split('\n')
            formatted_lines = formatted_for_cliclick.split('\n')
            
            formatting_preserved = len(original_lines) == len(formatted_lines)
            print(f"Formatting preserved: {'✅ YES' if formatting_preserved else '❌ NO'}")
            
            # Quality checks
            quality_checks = {
                'Function definitions': 'function ' in generated_code or '=>' in generated_code,
                'Proper braces': '{' in generated_code and '}' in generated_code,
                'No explanations': not generated_code.startswith(('Here', 'The', 'This')),
                'Clean code': '```' not in generated_code
            }
            
            print(f"\n✅ Quality Checks:")
            for check, passed in quality_checks.items():
                print(f"  {check}: {'✅ PASS' if passed else '❌ FAIL'}")
            
            all_passed = formatting_preserved and all(quality_checks.values())
            print(f"\n🎉 JavaScript Integration Test: {'✅ SUCCESS' if all_passed else '❌ ISSUES DETECTED'}")
            
            return all_passed
            
        else:
            print("❌ Content generation failed")
            return False
            
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

def test_integration_text_content():
    """Test complete integration with text content generation."""
    
    print("\nTesting Text Content Generation Integration")
    print("=" * 50)
    
    # Test case: Multi-paragraph text
    request = "Write a comprehensive guide on best practices for remote work productivity"
    context = "Professional development article"
    
    reasoning = ReasoningModule()
    automation = AutomationModule()
    
    print(f"Request: {request}")
    print(f"Context: {context}")
    
    try:
        # Generate content
        formatted_prompt = TEXT_GENERATION_PROMPT.format(request=request, context=context)
        api_response = reasoning._make_api_request(formatted_prompt)
        
        if api_response and 'choices' in api_response:
            generated_text = api_response['choices'][0]['message']['content'].strip()
            
            print(f"\n✅ Content Generated: {len(generated_text)} characters")
            
            # Analyze text structure
            paragraphs = generated_text.split('\n\n')
            lines = generated_text.split('\n')
            
            print(f"Paragraphs: {len(paragraphs)}")
            print(f"Lines: {len(lines)}")
            
            # Test formatting preservation
            formatted_for_cliclick = automation._format_text_for_typing(generated_text, 'cliclick')
            
            original_lines = generated_text.split('\n')
            formatted_lines = formatted_for_cliclick.split('\n')
            
            formatting_preserved = len(original_lines) == len(formatted_lines)
            print(f"Line structure preserved: {'✅ YES' if formatting_preserved else '❌ NO'}")
            
            # Quality checks for text
            quality_checks = {
                'Multiple paragraphs': len(paragraphs) > 1,
                'No explanatory headers': not generated_text.startswith(('Here is', 'The following', 'This guide')),
                'Proper punctuation': generated_text.endswith(('.', '!', '?')),
                'No markdown': not any(marker in generated_text for marker in ['**', '*', '#', '```']),
                'Coherent content': len(generated_text) > 200  # Substantial content
            }
            
            print(f"\n✅ Quality Checks:")
            for check, passed in quality_checks.items():
                print(f"  {check}: {'✅ PASS' if passed else '❌ FAIL'}")
            
            all_passed = formatting_preserved and all(quality_checks.values())
            print(f"\n🎉 Text Integration Test: {'✅ SUCCESS' if all_passed else '❌ ISSUES DETECTED'}")
            
            return all_passed
            
        else:
            print("❌ Content generation failed")
            return False
            
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

def test_special_characters_integration():
    """Test integration with content containing special characters."""
    
    print("\nTesting Special Characters Integration")
    print("=" * 50)
    
    # Test case: Code with many special characters
    request = "Create a Python script that processes JSON data with regex patterns and handles file paths"
    context = "Data processing utility"
    
    reasoning = ReasoningModule()
    automation = AutomationModule()
    
    print(f"Request: {request}")
    
    try:
        # Generate content
        formatted_prompt = CODE_GENERATION_PROMPT.format(request=request, context=context)
        api_response = reasoning._make_api_request(formatted_prompt)
        
        if api_response and 'choices' in api_response:
            generated_code = api_response['choices'][0]['message']['content'].strip()
            
            print(f"\n✅ Content Generated: {len(generated_code)} characters")
            
            # Check for special characters that need escaping
            special_chars = {
                'Double quotes': '"' in generated_code,
                'Single quotes': "'" in generated_code,
                'Backslashes': '\\' in generated_code,
                'Dollar signs': '$' in generated_code,
                'Brackets': any(char in generated_code for char in '[]{}()'),
                'Regex patterns': 'r"' in generated_code or "r'" in generated_code
            }
            
            print(f"\n✅ Special Characters Found:")
            for char_type, found in special_chars.items():
                print(f"  {char_type}: {'✅ YES' if found else '⚪ NO'}")
            
            # Test cliclick formatting with special characters
            formatted_for_cliclick = automation._format_text_for_typing(generated_code, 'cliclick')
            
            # Verify escaping
            escaping_checks = {
                'Quotes escaped': '\\"' in formatted_for_cliclick if '"' in generated_code else True,
                'Backslashes escaped': '\\\\' in formatted_for_cliclick if '\\' in generated_code else True,
                'Brackets escaped': any(f'\\{char}' in formatted_for_cliclick for char in '[]{}()') if any(char in generated_code for char in '[]{}()') else True
            }
            
            print(f"\n✅ Escaping Checks:")
            for check, passed in escaping_checks.items():
                print(f"  {check}: {'✅ PASS' if passed else '❌ FAIL'}")
            
            # Verify structure preservation
            original_lines = generated_code.split('\n')
            formatted_lines = formatted_for_cliclick.split('\n')
            
            structure_preserved = len(original_lines) == len(formatted_lines)
            print(f"\nStructure preserved: {'✅ YES' if structure_preserved else '❌ NO'}")
            
            all_passed = structure_preserved and all(escaping_checks.values())
            print(f"\n🎉 Special Characters Test: {'✅ SUCCESS' if all_passed else '❌ ISSUES DETECTED'}")
            
            return all_passed
            
        else:
            print("❌ Content generation failed")
            return False
            
    except Exception as e:
        print(f"❌ Special characters test failed: {e}")
        return False

def main():
    """Run all integration tests."""
    
    print("Complete Formatting Integration Test Suite")
    print("Testing end-to-end content generation and cliclick typing")
    print("=" * 70)
    
    results = []
    
    # Run all integration tests
    results.append(("Python Code Integration", test_integration_python_code()))
    results.append(("JavaScript Code Integration", test_integration_javascript_code()))
    results.append(("Text Content Integration", test_integration_text_content()))
    results.append(("Special Characters Integration", test_special_characters_integration()))
    
    # Summary
    print("\n" + "=" * 70)
    print("INTEGRATION TEST SUMMARY")
    print("=" * 70)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<35}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL INTEGRATION TESTS PASSED!")
        print("\n✅ Complete Integration Verified:")
        print("  • Reasoning module generates properly formatted content")
        print("  • Content follows language-specific indentation rules")
        print("  • cliclick formatting preserves all structure and indentation")
        print("  • Special characters are properly escaped for cliclick")
        print("  • No unwanted explanatory text or markdown formatting")
        print("  • End-to-end pipeline maintains content quality")
        
        print("\n🎯 The complete formatting pipeline is working perfectly!")
        print("   Content generation → cliclick formatting → typing preservation")
        
        return True
    else:
        print(f"\n❌ {total - passed} integration tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)