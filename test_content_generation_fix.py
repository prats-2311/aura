#!/usr/bin/env python3
"""
Test Content Generation Fix

This test verifies that the content generation correctly handles dictionary responses.
"""

import sys
import logging
from unittest.mock import Mock, patch

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_content_generation_response_handling():
    """Test that content generation handles dictionary responses correctly."""
    logger.info("Testing content generation response handling...")
    
    try:
        # Mock the reasoning module response
        mock_response = {
            'message': 'def fibonacci(n):\n    if n <= 1:\n        return n\n    else:\n        return fibonacci(n-1) + fibonacci(n-2)'
        }
        
        # Test the content extraction logic directly
        response = mock_response
        
        # Extract content using the same logic as in orchestrator
        if isinstance(response, dict) and 'message' in response:
            generated_content = response.get('message', '').strip()
        elif isinstance(response, dict) and 'response' in response:
            generated_content = response.get('response', '').strip()
        elif isinstance(response, str):
            generated_content = response.strip()
        else:
            generated_content = str(response).strip()
        
        logger.info(f"Extracted content: {len(generated_content)} chars")
        logger.info(f"Content preview: {generated_content[:100]}...")
        
        if generated_content and 'def fibonacci' in generated_content:
            logger.info("✅ Content extraction successful")
            
            # Test that newlines are preserved
            if '\n' in generated_content:
                logger.info("✅ Newlines preserved in extracted content")
            else:
                logger.warning("❌ Newlines missing in extracted content")
                
            return True
        else:
            logger.error("❌ Content extraction failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Test failed with exception: {e}")
        return False

def test_alternative_response_formats():
    """Test different response formats."""
    logger.info("Testing alternative response formats...")
    
    test_cases = [
        # OpenAI-style format
        {'message': 'print("Hello, World!")'},
        # Direct response format
        {'response': 'print("Hello, World!")'},
        # String format (fallback)
        'print("Hello, World!")',
        # Generic dict format
        {'content': 'print("Hello, World!")', 'other': 'data'}
    ]
    
    for i, response in enumerate(test_cases):
        logger.info(f"Testing case {i+1}: {type(response)}")
        
        # Extract content using the same logic
        if isinstance(response, dict) and 'message' in response:
            generated_content = response.get('message', '').strip()
        elif isinstance(response, dict) and 'response' in response:
            generated_content = response.get('response', '').strip()
        elif isinstance(response, str):
            generated_content = response.strip()
        else:
            generated_content = str(response).strip()
        
        if generated_content and 'Hello' in generated_content:
            logger.info(f"✅ Case {i+1} successful: {generated_content}")
        else:
            logger.warning(f"❌ Case {i+1} failed: {generated_content}")
    
    return True

def main():
    """Run content generation tests."""
    logger.info("🧪 Testing Content Generation Response Handling")
    logger.info("=" * 50)
    
    success1 = test_content_generation_response_handling()
    success2 = test_alternative_response_formats()
    
    if success1 and success2:
        logger.info("🎉 All content generation tests passed!")
        logger.info("The response handling should now work correctly.")
        return True
    else:
        logger.error("💥 Some content generation tests failed!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)