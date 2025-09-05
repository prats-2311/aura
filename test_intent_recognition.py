#!/usr/bin/env python3
"""
Test script for intent recognition system implementation.
"""

import sys
import logging
from orchestrator import Orchestrator

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_intent_recognition():
    """Test the intent recognition system with various commands."""
    
    print("Testing Intent Recognition System")
    print("=" * 50)
    
    try:
        # Initialize orchestrator
        orchestrator = Orchestrator()
        
        # Test commands for different intents
        test_commands = [
            ("click on the sign in button", "gui_interaction"),
            ("hello, how are you today?", "conversational_chat"),
            ("write a Python function to calculate fibonacci", "deferred_action"),
            ("what's on my screen?", "question_answering"),
            ("type hello world", "gui_interaction"),
            ("", "gui_interaction"),  # Empty command should fallback
        ]
        
        print(f"\nTesting {len(test_commands)} commands:")
        print("-" * 50)
        
        for i, (command, expected_intent) in enumerate(test_commands, 1):
            print(f"\nTest {i}: '{command}'")
            
            try:
                # Test intent recognition
                intent_result = orchestrator._recognize_intent(command)
                
                recognized_intent = intent_result.get('intent', 'unknown')
                confidence = intent_result.get('confidence', 0)
                is_fallback = intent_result.get('is_fallback', False)
                
                print(f"  Recognized: {recognized_intent}")
                print(f"  Confidence: {confidence:.2f}")
                print(f"  Fallback: {is_fallback}")
                
                if expected_intent == recognized_intent:
                    print(f"  ✅ PASS - Expected {expected_intent}")
                else:
                    print(f"  ⚠️  DIFFERENT - Expected {expected_intent}, got {recognized_intent}")
                    
            except Exception as e:
                print(f"  ❌ ERROR: {str(e)}")
        
        print("\n" + "=" * 50)
        print("Intent recognition test completed!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = test_intent_recognition()
    sys.exit(0 if success else 1)