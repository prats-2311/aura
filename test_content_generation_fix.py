#!/usr/bin/env python3
"""
Test script for Task 0.2: Resolve Deferred Action Content Generation Bugs

This script tests the enhanced content generation prompts and comprehensive
content cleaning and formatting functionality.
"""

import sys
import logging
from unittest.mock import Mock

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_content_cleaning():
    """Test the enhanced content cleaning functionality."""
    logger.info("Testing enhanced content cleaning functionality...")
    
    try:
        # Import the deferred action handler
        from handlers.deferred_action_handler import DeferredActionHandler
        
        # Create a mock orchestrator
        mock_orchestrator = Mock()
        
        # Create the handler
        handler = DeferredActionHandler(mock_orchestrator)
        
        # Test cases for content cleaning
        test_cases = [
            {
                "name": "Code with markdown blocks",
                "content": "```python\ndef hello_world():\n    print('Hello, World!')\n```",
                "content_type": "code",
                "expected_contains": ["def hello_world():", "print('Hello, World!')"],
                "expected_not_contains": ["```python", "```"]
            },
            {
                "name": "Code with explanatory prefix",
                "content": "Here is the code:\ndef calculate_sum(a, b):\n    return a + b",
                "content_type": "code",
                "expected_contains": ["def calculate_sum(a, b):", "return a + b"],
                "expected_not_contains": ["Here is the code:"]
            },
            {
                "name": "Text with unwanted prefix",
                "content": "Here is the essay:\n\nThis is a sample essay about technology. It discusses various aspects of modern computing.\n\nTechnology has revolutionized our world.",
                "content_type": "text",
                "expected_contains": ["This is a sample essay", "Technology has revolutionized"],
                "expected_not_contains": ["Here is the essay:"]
            },
            {
                "name": "Single line code formatting",
                "content": "def process_data(data): return [x * 2 for x in data if x > 0]",
                "content_type": "code",
                "expected_contains": ["def process_data(data):"],
                "expected_not_contains": []
            },
            {
                "name": "Multiple unwanted prefixes",
                "content": "Here's the code:\n```javascript\nfunction greet(name) {\n    console.log('Hello, ' + name);\n}\n```",
                "content_type": "code",
                "expected_contains": ["function greet(name)", "console.log"],
                "expected_not_contains": ["Here's the code:", "```javascript", "```"]
            }
        ]
        
        # Run test cases
        passed = 0
        failed = 0
        
        for test_case in test_cases:
            logger.info(f"\nTesting: {test_case['name']}")
            logger.info(f"Original content: {repr(test_case['content'])}")
            
            try:
                # Clean the content
                cleaned = handler._clean_and_format_content(
                    test_case['content'], 
                    test_case['content_type']
                )
                
                logger.info(f"Cleaned content: {repr(cleaned)}")
                
                # Check expected contains
                contains_passed = True
                for expected in test_case['expected_contains']:
                    if expected not in cleaned:
                        logger.error(f"Expected '{expected}' not found in cleaned content")
                        contains_passed = False
                
                # Check expected not contains
                not_contains_passed = True
                for not_expected in test_case['expected_not_contains']:
                    if not_expected in cleaned:
                        logger.error(f"Unwanted '{not_expected}' found in cleaned content")
                        not_contains_passed = False
                
                if contains_passed and not_contains_passed:
                    logger.info(f"✅ {test_case['name']} - PASSED")
                    passed += 1
                else:
                    logger.error(f"❌ {test_case['name']} - FAILED")
                    failed += 1
                    
            except Exception as e:
                logger.error(f"❌ {test_case['name']} - ERROR: {e}")
                failed += 1
        
        logger.info(f"\n=== Content Cleaning Test Results ===")
        logger.info(f"Passed: {passed}")
        logger.info(f"Failed: {failed}")
        logger.info(f"Total: {passed + failed}")
        
        return failed == 0
        
    except Exception as e:
        logger.error(f"Error testing content cleaning: {e}")
        return False

def test_prompt_enhancements():
    """Test that the enhanced prompts are properly configured."""
    logger.info("Testing enhanced prompt configurations...")
    
    try:
        import config
        
        # Check CODE_GENERATION_PROMPT enhancements
        code_prompt = config.CODE_GENERATION_PROMPT
        
        # Check for enhanced formatting requirements
        enhanced_features = [
            "CRITICAL FORMATTING REQUIREMENTS",
            "EXACTLY 4 spaces for indentation in Python",
            "EXACTLY 2 spaces for indentation in JavaScript",
            "FORBIDDEN ELEMENTS",
            "Do NOT include any markdown code blocks",
            "perfect formatting"
        ]
        
        prompt_passed = True
        for feature in enhanced_features:
            if feature not in code_prompt:
                logger.error(f"Enhanced feature '{feature}' not found in CODE_GENERATION_PROMPT")
                prompt_passed = False
        
        if prompt_passed:
            logger.info("✅ CODE_GENERATION_PROMPT enhancements - PASSED")
        else:
            logger.error("❌ CODE_GENERATION_PROMPT enhancements - FAILED")
        
        # Check TEXT_GENERATION_PROMPT enhancements
        text_prompt = config.TEXT_GENERATION_PROMPT
        
        text_features = [
            "CRITICAL FORMATTING REQUIREMENTS",
            "editor-ready text",
            "FORBIDDEN ELEMENTS",
            "perfect formatting"
        ]
        
        text_passed = True
        for feature in text_features:
            if feature not in text_prompt:
                logger.error(f"Enhanced feature '{feature}' not found in TEXT_GENERATION_PROMPT")
                text_passed = False
        
        if text_passed:
            logger.info("✅ TEXT_GENERATION_PROMPT enhancements - PASSED")
        else:
            logger.error("❌ TEXT_GENERATION_PROMPT enhancements - FAILED")
        
        # Check timeout configurations
        timeout_checks = [
            ("CODE_GENERATION_TIMEOUT", 120.0),
            ("DEFERRED_ACTION_TIMEOUT", 600.0),
            ("DEFERRED_ACTION_MAX_TIMEOUT", 900.0),
            ("DEFERRED_ACTION_MIN_TIMEOUT", 60.0)
        ]
        
        timeout_passed = True
        for timeout_name, expected_value in timeout_checks:
            actual_value = getattr(config, timeout_name, None)
            if actual_value != expected_value:
                logger.error(f"{timeout_name} expected {expected_value}, got {actual_value}")
                timeout_passed = False
            else:
                logger.info(f"✅ {timeout_name} = {actual_value}")
        
        if timeout_passed:
            logger.info("✅ Timeout configurations - PASSED")
        else:
            logger.error("❌ Timeout configurations - FAILED")
        
        return prompt_passed and text_passed and timeout_passed
        
    except Exception as e:
        logger.error(f"Error testing prompt enhancements: {e}")
        return False

def main():
    """Run all tests for Task 0.2."""
    logger.info("=== Task 0.2: Resolve Deferred Action Content Generation Bugs ===")
    logger.info("Testing enhanced content generation prompts and comprehensive content cleaning...")
    
    # Test prompt enhancements (Task 0.6)
    prompt_test_passed = test_prompt_enhancements()
    
    # Test content cleaning enhancements (Task 0.7)
    cleaning_test_passed = test_content_cleaning()
    
    # Overall results
    logger.info("\n=== Overall Test Results ===")
    if prompt_test_passed:
        logger.info("✅ Task 0.6 (Prompt Enhancements) - PASSED")
    else:
        logger.error("❌ Task 0.6 (Prompt Enhancements) - FAILED")
    
    if cleaning_test_passed:
        logger.info("✅ Task 0.7 (Content Cleaning) - PASSED")
    else:
        logger.error("❌ Task 0.7 (Content Cleaning) - FAILED")
    
    if prompt_test_passed and cleaning_test_passed:
        logger.info("🎉 Task 0.2: Resolve Deferred Action Content Generation Bugs - COMPLETED SUCCESSFULLY")
        return 0
    else:
        logger.error("💥 Task 0.2: Some tests failed - NEEDS ATTENTION")
        return 1

if __name__ == "__main__":
    sys.exit(main())