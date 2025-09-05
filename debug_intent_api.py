#!/usr/bin/env python3
"""
Debug script to test the intent recognition API directly.
"""

import sys
import logging
from modules.reasoning import ReasoningModule
from config import INTENT_RECOGNITION_PROMPT

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_intent_api():
    """Test the intent recognition API directly."""
    
    print("Testing Intent Recognition API")
    print("=" * 50)
    
    try:
        # Initialize reasoning module
        reasoning = ReasoningModule()
        
        # Test command
        test_command = "click on the sign in button"
        
        # Build prompt
        prompt = INTENT_RECOGNITION_PROMPT.format(command=test_command)
        
        print(f"Prompt being sent:")
        print("-" * 30)
        print(prompt)
        print("-" * 30)
        
        # Make API request
        print("\nMaking API request...")
        response = reasoning._make_api_request(prompt)
        
        print(f"\nRaw API Response:")
        print("-" * 30)
        print(f"Type: {type(response)}")
        print(f"Content: {response}")
        print("-" * 30)
        
        # Try to extract content
        if isinstance(response, dict):
            if 'choices' in response and response['choices']:
                content = response['choices'][0].get('message', {}).get('content', '')
                print(f"\nExtracted content (OpenAI style): {content}")
            elif 'response' in response:
                content = response['response']
                print(f"\nExtracted content (Ollama style): {content}")
            elif 'content' in response:
                content = response['content']
                print(f"\nExtracted content (Direct): {content}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_intent_api()
    sys.exit(0 if success else 1)