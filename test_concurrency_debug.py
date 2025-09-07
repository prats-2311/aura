#!/usr/bin/env python3
"""
Debug script to test the concurrency issue with back-to-back deferred actions.
"""

import time
import logging
from orchestrator import Orchestrator

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_back_to_back_deferred_actions():
    """Test back-to-back deferred action commands to reproduce the lock issue."""
    
    print("Initializing orchestrator...")
    orchestrator = Orchestrator()
    
    print("\n=== Testing Back-to-Back Deferred Actions ===")
    
    # First command - should work
    print("\n1. Executing first deferred action command...")
    try:
        result1 = orchestrator.execute_command("Write me a Python function for factorial")
        print(f"First command result: {result1.get('status', 'unknown')}")
        
        if result1.get('status') == 'waiting_for_user_action':
            print("First command is waiting for user action - simulating completion...")
            
            # Simulate the deferred action completion
            time.sleep(1)  # Give it a moment
            
            # Check lock state
            print(f"Lock state after first command: {orchestrator.execution_lock.locked()}")
            
            # Simulate mouse click by calling the trigger directly
            execution_id = result1.get('execution_id', 'test-123')
            if hasattr(orchestrator, '_on_deferred_action_trigger'):
                print("Simulating mouse click to complete first deferred action...")
                orchestrator._on_deferred_action_trigger(execution_id)
                
                # Wait for completion and check state
                print("Waiting for deferred action to complete...")
                for i in range(10):  # Wait up to 10 seconds
                    time.sleep(1)
                    if not orchestrator.is_waiting_for_user_action:
                        print(f"Deferred action completed after {i+1} seconds")
                        break
                    print(f"Still waiting... ({i+1}/10)")
                
                print(f"Lock state after first deferred action completion: {orchestrator.execution_lock.locked()}")
                print(f"Waiting for user action: {orchestrator.is_waiting_for_user_action}")
                print(f"Deferred action executing: {orchestrator.deferred_action_executing}")
            
    except Exception as e:
        print(f"First command failed: {e}")
        return
    
    # Wait a moment
    time.sleep(1)
    
    # Second command - this should also work but currently fails
    print("\n2. Executing second deferred action command...")
    try:
        print(f"Lock state before second command: {orchestrator.execution_lock.locked()}")
        result2 = orchestrator.execute_command("Write me a JavaScript function for sorting")
        print(f"Second command result: {result2.get('status', 'unknown')}")
        
    except Exception as e:
        print(f"Second command failed: {e}")
        print(f"Lock state after second command failure: {orchestrator.execution_lock.locked()}")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    test_back_to_back_deferred_actions()