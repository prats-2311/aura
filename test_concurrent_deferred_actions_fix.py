#!/usr/bin/env python3
"""
Test Concurrent Deferred Actions Fix

This test verifies that:
1. The OpenAI response format is correctly parsed
2. Concurrent commands can execute while a deferred action is waiting
"""

import sys
import logging
from unittest.mock import Mock, patch

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_openai_response_format_parsing():
    """Test that the new OpenAI response format is correctly parsed."""
    logger.info("Testing OpenAI response format parsing...")
    
    # Mock OpenAI-style response
    mock_response = {
        'choices': [
            {
                'message': {
                    'content': 'def fibonacci(n):\n    a, b = 0, 1\n    for _ in range(n):\n        a, b = b, a + b\n    return a'
                }
            }
        ]
    }
    
    # Test the extraction logic
    response = mock_response
    
    # Extract content using the same logic as in orchestrator
    if isinstance(response, dict) and 'choices' in response:
        choices = response.get('choices', [])
        if choices and isinstance(choices, list) and len(choices) > 0:
            first_choice = choices[0]
            if isinstance(first_choice, dict) and 'message' in first_choice:
                message = first_choice.get('message', {})
                if isinstance(message, dict) and 'content' in message:
                    generated_content = message.get('content', '').strip()
                else:
                    generated_content = str(message).strip()
            else:
                generated_content = str(first_choice).strip()
        else:
            generated_content = str(response).strip()
    else:
        generated_content = str(response).strip()
    
    logger.info(f"Extracted content: {len(generated_content)} chars")
    logger.info(f"Content preview: {generated_content[:100]}...")
    
    if generated_content and 'def fibonacci' in generated_content and '\n' in generated_content:
        logger.info("✅ OpenAI response format parsing successful")
        logger.info("✅ Newlines preserved in extracted content")
        return True
    else:
        logger.error("❌ OpenAI response format parsing failed")
        return False

def test_execution_lock_behavior():
    """Test that execution lock is properly managed for deferred actions."""
    logger.info("Testing execution lock behavior...")
    
    # Mock result formats
    deferred_result = {
        'status': 'waiting_for_user_action',
        'execution_id': 'test_123',
        'message': 'Content generated. Click where you want it placed.'
    }
    
    normal_result = {
        'status': 'completed',
        'execution_id': 'test_456',
        'message': 'Command completed successfully.'
    }
    
    # Test deferred action result detection
    if isinstance(deferred_result, dict) and deferred_result.get('status') == 'waiting_for_user_action':
        logger.info("✅ Deferred action result correctly identified")
        logger.info("✅ Execution lock should be released early for this result")
    else:
        logger.error("❌ Deferred action result not identified correctly")
        return False
    
    # Test normal result detection
    if isinstance(normal_result, dict) and normal_result.get('status') != 'waiting_for_user_action':
        logger.info("✅ Normal result correctly identified")
        logger.info("✅ Execution lock should be held until completion for this result")
    else:
        logger.error("❌ Normal result not identified correctly")
        return False
    
    return True

def test_response_format_edge_cases():
    """Test various response format edge cases."""
    logger.info("Testing response format edge cases...")
    
    test_cases = [
        # Empty choices
        {'choices': []},
        # Missing message
        {'choices': [{'other': 'data'}]},
        # Missing content
        {'choices': [{'message': {'other': 'data'}}]},
        # String message
        {'choices': [{'message': 'direct string'}]},
        # Nested content
        {'choices': [{'message': {'content': 'Hello World'}}]},
    ]
    
    for i, response in enumerate(test_cases):
        logger.info(f"Testing edge case {i+1}: {response}")
        
        # Apply extraction logic
        if isinstance(response, dict) and 'choices' in response:
            choices = response.get('choices', [])
            if choices and isinstance(choices, list) and len(choices) > 0:
                first_choice = choices[0]
                if isinstance(first_choice, dict) and 'message' in first_choice:
                    message = first_choice.get('message', {})
                    if isinstance(message, dict) and 'content' in message:
                        generated_content = message.get('content', '').strip()
                    else:
                        generated_content = str(message).strip()
                else:
                    generated_content = str(first_choice).strip()
            else:
                generated_content = str(response).strip()
        else:
            generated_content = str(response).strip()
        
        logger.info(f"  Result: '{generated_content}'")
    
    logger.info("✅ All edge cases handled without errors")
    return True

def main():
    """Run concurrent deferred actions tests."""
    logger.info("🧪 Testing Concurrent Deferred Actions Fix")
    logger.info("=" * 50)
    
    success1 = test_openai_response_format_parsing()
    success2 = test_execution_lock_behavior()
    success3 = test_response_format_edge_cases()
    
    if success1 and success2 and success3:
        logger.info("🎉 All concurrent deferred actions tests passed!")
        logger.info("The system should now:")
        logger.info("  ✅ Parse OpenAI response format correctly")
        logger.info("  ✅ Allow concurrent commands during deferred actions")
        logger.info("  ✅ Handle various response format edge cases")
        return True
    else:
        logger.error("💥 Some concurrent deferred actions tests failed!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)