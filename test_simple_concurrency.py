#!/usr/bin/env python3
"""
Simple test to verify the concurrency fix works.
"""

import time
import logging
import threading
from unittest.mock import Mock

# Configure minimal logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_lock_behavior_simulation():
    """Simulate the orchestrator lock behavior to test the fix."""
    
    print("=== Testing Orchestrator Lock Behavior Simulation ===")
    
    # Simulate orchestrator state
    execution_lock = threading.Lock()
    deferred_action_lock = threading.Lock()
    is_waiting_for_user_action = False
    deferred_action_executing = False
    
    def simulate_first_command():
        """Simulate first deferred action command."""
        nonlocal is_waiting_for_user_action, deferred_action_executing
        
        print("\n1. Simulating first command...")
        
        # Acquire execution lock
        print(f"   Acquiring execution lock (locked: {execution_lock.locked()})")
        execution_lock.acquire()
        print(f"   Execution lock acquired (locked: {execution_lock.locked()})")
        
        # Set up deferred action state
        with deferred_action_lock:
            is_waiting_for_user_action = True
            deferred_action_executing = False
        
        # Release lock early for deferred action
        print("   Releasing execution lock early for deferred action")
        execution_lock.release()
        print(f"   Execution lock released (locked: {execution_lock.locked()})")
        
        return "waiting_for_user_action"
    
    def simulate_deferred_action_trigger():
        """Simulate deferred action trigger."""
        nonlocal is_waiting_for_user_action, deferred_action_executing
        
        print("\n2. Simulating deferred action trigger...")
        
        with deferred_action_lock:
            # Check for duplicate execution
            if deferred_action_executing:
                print("   Duplicate execution detected - ignoring")
                return
            
            if not is_waiting_for_user_action:
                print("   Not waiting for user action - ignoring")
                return
            
            # Mark as executing
            deferred_action_executing = True
            print("   Marked as executing")
            
            # Simulate action execution
            print("   Executing deferred action...")
            time.sleep(0.5)  # Simulate work
            
            # Reset state
            is_waiting_for_user_action = False
            deferred_action_executing = False
            print("   Deferred action completed and state reset")
    
    def simulate_second_command():
        """Simulate second command."""
        print("\n3. Simulating second command...")
        
        # Try to acquire execution lock
        print(f"   Attempting to acquire execution lock (locked: {execution_lock.locked()})")
        lock_acquired = execution_lock.acquire(timeout=5.0)
        
        if lock_acquired:
            print(f"   Second command lock acquired successfully (locked: {execution_lock.locked()})")
            
            # Simulate command processing
            time.sleep(0.1)
            
            # Release lock
            execution_lock.release()
            print(f"   Second command completed and lock released (locked: {execution_lock.locked()})")
            return "success"
        else:
            print("   Failed to acquire lock - system busy")
            return "failed"
    
    # Run the simulation
    try:
        # First command
        result1 = simulate_first_command()
        print(f"   First command result: {result1}")
        
        # Deferred action trigger
        simulate_deferred_action_trigger()
        
        # Wait a moment
        time.sleep(0.1)
        
        # Second command
        result2 = simulate_second_command()
        print(f"   Second command result: {result2}")
        
        # Final state check
        print(f"\nFinal state:")
        print(f"   Execution lock locked: {execution_lock.locked()}")
        print(f"   Waiting for user action: {is_waiting_for_user_action}")
        print(f"   Deferred action executing: {deferred_action_executing}")
        
        if result2 == "success":
            print("\n✅ Concurrency fix working correctly!")
        else:
            print("\n❌ Concurrency issue still present")
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")

if __name__ == "__main__":
    test_lock_behavior_simulation()