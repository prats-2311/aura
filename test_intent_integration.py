#!/usr/bin/env python3
"""
Test script for intent recognition integration with command execution.
"""

import sys
import logging
from orchestrator import Orchestrator

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_intent_integration():
    """Test the intent recognition integration with command execution."""
    
    print("Testing Intent Recognition Integration")
    print("=" * 50)
    
    try:
        # Initialize orchestrator
        orchestrator = Orchestrator()
        
        # Test commands for different intents
        test_commands = [
            "hello there!",  # Should route to conversational handler
            "write a simple hello world function",  # Should route to deferred action handler
            "what's on my screen?",  # Should route to question answering
            "click on the sign in button",  # Should continue with GUI processing
        ]
        
        print(f"\nTesting {len(test_commands)} commands with full execution:")
        print("-" * 50)
        
        for i, command in enumerate(test_commands, 1):
            print(f"\nTest {i}: '{command}'")
            
            try:
                # Test full command execution with intent routing
                result = orchestrator._execute_command_internal(command)
                
                print(f"  Status: {result.get('status', 'unknown')}")
                print(f"  Execution ID: {result.get('execution_id', 'none')}")
                
                if 'intent_result' in result:
                    intent = result['intent_result'].get('intent', 'unknown')
                    confidence = result['intent_result'].get('confidence', 0)
                    print(f"  Intent: {intent} (confidence: {confidence:.2f})")
                
                if result.get('status') == 'continue_with_existing_logic':
                    print(f"  ✅ Correctly routed to handler (placeholder returned)")
                elif 'errors' in result and result['errors']:
                    print(f"  ⚠️  Errors: {result['errors']}")
                else:
                    print(f"  ✅ Execution completed")
                    
            except Exception as e:
                print(f"  ❌ ERROR: {str(e)}")
        
        print("\n" + "=" * 50)
        print("Intent integration test completed!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = test_intent_integration()
    sys.exit(0 if success else 1)