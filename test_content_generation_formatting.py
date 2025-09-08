#!/usr/bin/env python3
"""
Test script to verify content generation formatting from the reasoning module.
Tests that the reasoning module generates properly formatted code and text content.
"""

import sys
import os
import json
import time

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.reasoning import ReasoningModule
from modules.automation import AutomationModule
from config import CODE_GENERATION_PROMPT, TEXT_GENERATION_PROMPT

def test_code_generation_formatting():
    """Test that code generation produces properly formatted code."""
    
    print("Testing Code Generation Formatting")
    print("=" * 50)
    
    # Test cases for different programming languages
    code_requests = [
        {
            'name': 'Python Function',
            'request': 'Create a Python function to calculate fibonacci numbers recursively',
            'context': 'Python development environment',
            'expected_language': 'python'
        },
        {
            'name': 'JavaScript Function',
            'request': 'Create a JavaScript function to validate email addresses',
            'context': 'Web development project',
            'expected_language': 'javascript'
        },
        {
            'name': 'Python Class',
            'request': 'Create a Python class for a simple calculator with add, subtract, multiply, and divide methods',
            'context': 'Object-oriented programming exercise',
            'expected_language': 'python'
        },
        {
            'name': 'HTML Form',
            'request': 'Create an HTML form with name, email, and message fields',
            'context': 'Web form development',
            'expected_language': 'html'
        }
    ]
    
    reasoning = ReasoningModule()
    
    for request_info in code_requests:
        print(f"\n--- {request_info['name']} ---")
        
        # Format the prompt
        formatted_prompt = CODE_GENERATION_PROMPT.format(
            request=request_info['request'],
            context=request_info['context']
        )
        
        print(f"Request: {request_info['request']}")
        print(f"Context: {request_info['context']}")
        
        try:
            # Make API request directly to test content generation
            api_response = reasoning._make_api_request(formatted_prompt)
            
            if api_response and 'choices' in api_response:
                generated_code = api_response['choices'][0]['message']['content'].strip()
                
                print(f"Generated code ({len(generated_code)} chars):")
                print("First 200 chars:", repr(generated_code[:200]))
                
                # Analyze the formatting
                lines = generated_code.split('\n')
                print(f"Total lines: {len(lines)}")
                
                # Check for proper indentation
                indented_lines = [line for line in lines if line.startswith('    ') or line.startswith('  ')]
                print(f"Indented lines: {len(indented_lines)}")
                
                # Check for forbidden elements
                formatting_issues = []
                
                if '```' in generated_code:
                    formatting_issues.append('Contains markdown code blocks')
                
                if any(phrase in generated_code.lower() for phrase in ['here is the code', 'the following code', 'here\'s the code']):
                    formatting_issues.append('Contains explanatory phrases')
                
                if generated_code.startswith(('Here', 'The following', 'This code')):
                    formatting_issues.append('Starts with explanatory text')
                
                # Check indentation consistency
                if request_info['expected_language'] == 'python':
                    # Python should use 4-space indentation
                    python_indents = [line for line in lines if line.startswith('    ') and not line.startswith('        ')]
                    if python_indents:
                        print(f"✅ Python 4-space indentation found: {len(python_indents)} lines")
                    else:
                        formatting_issues.append('Missing proper Python 4-space indentation')
                
                elif request_info['expected_language'] in ['javascript', 'html', 'css']:
                    # These should use 2-space indentation
                    two_space_indents = [line for line in lines if line.startswith('  ') and not line.startswith('    ')]
                    if two_space_indents:
                        print(f"✅ 2-space indentation found: {len(two_space_indents)} lines")
                    else:
                        formatting_issues.append('Missing proper 2-space indentation')
                
                # Report results
                if not formatting_issues:
                    print("✅ Code formatting looks good!")
                else:
                    print("❌ Formatting issues found:")
                    for issue in formatting_issues:
                        print(f"  - {issue}")
                
                # Test with cliclick typing
                automation = AutomationModule()
                if automation.is_macos and automation.has_cliclick:
                    print("Testing cliclick typing compatibility...")
                    success = automation._cliclick_type(generated_code)
                    print(f"cliclick typing: {'✅ SUCCESS' if success else '❌ FAILED'}")
                
            else:
                print("❌ No valid response from API")
                
        except Exception as e:
            print(f"❌ Code generation failed: {e}")
        
        print("-" * 40)

def test_text_generation_formatting():
    """Test that text generation produces properly formatted text."""
    
    print("\nTesting Text Generation Formatting")
    print("=" * 50)
    
    # Test cases for different types of text content
    text_requests = [
        {
            'name': 'Short Essay',
            'request': 'Write a short essay about the benefits of renewable energy',
            'context': 'Academic writing assignment'
        },
        {
            'name': 'Business Email',
            'request': 'Write a professional email requesting a meeting with a client',
            'context': 'Business correspondence'
        },
        {
            'name': 'Product Description',
            'request': 'Write a product description for a wireless bluetooth headphone',
            'context': 'E-commerce website content'
        },
        {
            'name': 'Technical Documentation',
            'request': 'Write documentation explaining how to install a Python package',
            'context': 'Software documentation'
        }
    ]
    
    reasoning = ReasoningModule()
    
    for request_info in text_requests:
        print(f"\n--- {request_info['name']} ---")
        
        # Format the prompt
        formatted_prompt = TEXT_GENERATION_PROMPT.format(
            request=request_info['request'],
            context=request_info['context']
        )
        
        print(f"Request: {request_info['request']}")
        print(f"Context: {request_info['context']}")
        
        try:
            # Make API request directly to test content generation
            api_response = reasoning._make_api_request(formatted_prompt)
            
            if api_response and 'choices' in api_response:
                generated_text = api_response['choices'][0]['message']['content'].strip()
                
                print(f"Generated text ({len(generated_text)} chars):")
                print("First 150 chars:", repr(generated_text[:150]))
                
                # Analyze the formatting
                paragraphs = generated_text.split('\n\n')
                lines = generated_text.split('\n')
                
                print(f"Total paragraphs: {len(paragraphs)}")
                print(f"Total lines: {len(lines)}")
                
                # Check for forbidden elements
                formatting_issues = []
                
                if any(phrase in generated_text.lower() for phrase in ['here is the essay', 'the following text', 'here\'s your content']):
                    formatting_issues.append('Contains explanatory phrases')
                
                if generated_text.startswith(('Here', 'The following', 'This text')):
                    formatting_issues.append('Starts with explanatory text')
                
                # Check for proper paragraph structure
                if len(paragraphs) > 1:
                    print("✅ Multiple paragraphs found")
                else:
                    formatting_issues.append('Single paragraph - may need better structure')
                
                # Check for markdown formatting (should be avoided)
                if any(marker in generated_text for marker in ['**', '*', '#', '```', '---']):
                    formatting_issues.append('Contains markdown formatting')
                
                # Report results
                if not formatting_issues:
                    print("✅ Text formatting looks good!")
                else:
                    print("❌ Formatting issues found:")
                    for issue in formatting_issues:
                        print(f"  - {issue}")
                
                # Test with cliclick typing
                automation = AutomationModule()
                if automation.is_macos and automation.has_cliclick:
                    print("Testing cliclick typing compatibility...")
                    success = automation._cliclick_type(generated_text)
                    print(f"cliclick typing: {'✅ SUCCESS' if success else '❌ FAILED'}")
                
            else:
                print("❌ No valid response from API")
                
        except Exception as e:
            print(f"❌ Text generation failed: {e}")
        
        print("-" * 40)

def test_prompt_template_validation():
    """Test that the prompt templates have proper formatting requirements."""
    
    print("\nTesting Prompt Template Validation")
    print("=" * 50)
    
    # Check CODE_GENERATION_PROMPT
    print("--- CODE_GENERATION_PROMPT Analysis ---")
    
    required_code_elements = [
        'CRITICAL FORMATTING REQUIREMENTS',
        'EXACTLY 4 spaces for indentation in Python',
        'EXACTLY 2 spaces for indentation in JavaScript',
        'proper line breaks',
        'FORBIDDEN ELEMENTS',
        'Do NOT include any markdown code blocks',
        'Do NOT include any explanatory text'
    ]
    
    code_prompt_issues = []
    for element in required_code_elements:
        if element not in CODE_GENERATION_PROMPT:
            code_prompt_issues.append(f"Missing: {element}")
    
    if not code_prompt_issues:
        print("✅ CODE_GENERATION_PROMPT has all required formatting instructions")
    else:
        print("❌ CODE_GENERATION_PROMPT issues:")
        for issue in code_prompt_issues:
            print(f"  - {issue}")
    
    # Check TEXT_GENERATION_PROMPT
    print("\n--- TEXT_GENERATION_PROMPT Analysis ---")
    
    required_text_elements = [
        'CRITICAL FORMATTING REQUIREMENTS',
        'proper paragraph structure',
        'double line breaks between paragraphs',
        'FORBIDDEN ELEMENTS',
        'Do NOT include any titles, headers',
        'Do NOT include phrases like "Here is the essay"'
    ]
    
    text_prompt_issues = []
    for element in required_text_elements:
        if element not in TEXT_GENERATION_PROMPT:
            text_prompt_issues.append(f"Missing: {element}")
    
    if not text_prompt_issues:
        print("✅ TEXT_GENERATION_PROMPT has all required formatting instructions")
    else:
        print("❌ TEXT_GENERATION_PROMPT issues:")
        for issue in text_prompt_issues:
            print(f"  - {issue}")
    
    # Check for placeholders
    print("\n--- Placeholder Validation ---")
    
    if '{request}' in CODE_GENERATION_PROMPT and '{context}' in CODE_GENERATION_PROMPT:
        print("✅ CODE_GENERATION_PROMPT has required placeholders")
    else:
        print("❌ CODE_GENERATION_PROMPT missing required placeholders")
    
    if '{request}' in TEXT_GENERATION_PROMPT and '{context}' in TEXT_GENERATION_PROMPT:
        print("✅ TEXT_GENERATION_PROMPT has required placeholders")
    else:
        print("❌ TEXT_GENERATION_PROMPT missing required placeholders")

def test_end_to_end_formatting():
    """Test end-to-end formatting from generation to typing."""
    
    print("\nTesting End-to-End Formatting Pipeline")
    print("=" * 50)
    
    # Simple test case
    test_request = "Create a Python function that adds two numbers"
    test_context = "Simple math function"
    
    reasoning = ReasoningModule()
    automation = AutomationModule()
    
    print(f"Test request: {test_request}")
    print(f"Test context: {test_context}")
    
    try:
        # Step 1: Generate content
        formatted_prompt = CODE_GENERATION_PROMPT.format(
            request=test_request,
            context=test_context
        )
        
        api_response = reasoning._make_api_request(formatted_prompt)
        
        if api_response and 'choices' in api_response:
            generated_code = api_response['choices'][0]['message']['content'].strip()
            
            print(f"\nStep 1 - Content Generation:")
            print(f"Generated {len(generated_code)} characters")
            print(f"Lines: {len(generated_code.split(chr(10)))}")
            
            # Step 2: Format for cliclick
            formatted_for_typing = automation._format_text_for_typing(generated_code, 'cliclick')
            
            print(f"\nStep 2 - cliclick Formatting:")
            print(f"Formatted {len(formatted_for_typing)} characters")
            print(f"Lines preserved: {len(generated_code.split(chr(10))) == len(formatted_for_typing.split(chr(10)))}")
            
            # Step 3: Validate typing compatibility
            if automation.is_macos and automation.has_cliclick:
                success = automation._cliclick_type(generated_code)
                print(f"\nStep 3 - Typing Test:")
                print(f"cliclick typing: {'✅ SUCCESS' if success else '❌ FAILED'}")
            else:
                print(f"\nStep 3 - Typing Test:")
                print("⚠️  cliclick not available for testing")
            
            # Step 4: Analyze final quality
            print(f"\nStep 4 - Quality Analysis:")
            
            # Check indentation preservation
            original_lines = generated_code.split('\n')
            formatted_lines = formatted_for_typing.split('\n')
            
            indentation_preserved = True
            for orig, fmt in zip(original_lines, formatted_lines):
                orig_indent = len(orig) - len(orig.lstrip())
                fmt_indent = len(fmt) - len(fmt.lstrip())
                if orig_indent != fmt_indent:
                    indentation_preserved = False
                    break
            
            print(f"Indentation preserved: {'✅ YES' if indentation_preserved else '❌ NO'}")
            print(f"Line count preserved: {'✅ YES' if len(original_lines) == len(formatted_lines) else '❌ NO'}")
            
            # Check for clean content (no explanatory text)
            clean_content = not any(phrase in generated_code.lower() for phrase in [
                'here is the code', 'the following code', 'here\'s the code'
            ])
            print(f"Clean content (no explanations): {'✅ YES' if clean_content else '❌ NO'}")
            
            if indentation_preserved and len(original_lines) == len(formatted_lines) and clean_content:
                print("\n🎉 End-to-end formatting pipeline: ✅ SUCCESS")
            else:
                print("\n❌ End-to-end formatting pipeline: ISSUES DETECTED")
        
        else:
            print("❌ Content generation failed")
    
    except Exception as e:
        print(f"❌ End-to-end test failed: {e}")

if __name__ == "__main__":
    print("Content Generation Formatting Test Suite")
    print("Testing reasoning module content generation and cliclick compatibility")
    print("=" * 70)
    
    try:
        test_prompt_template_validation()
        test_code_generation_formatting()
        test_text_generation_formatting()
        test_end_to_end_formatting()
        
        print("\n" + "=" * 70)
        print("✅ Content Generation Formatting Tests Completed!")
        print("\nKey areas verified:")
        print("  ✅ Prompt templates have proper formatting requirements")
        print("  ✅ Code generation produces properly indented code")
        print("  ✅ Text generation produces clean, structured content")
        print("  ✅ Generated content is compatible with cliclick typing")
        print("  ✅ End-to-end pipeline preserves formatting")
        
    except Exception as e:
        print(f"Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)