#!/usr/bin/env python3
"""
Debug script to check current deferred action state and reset if needed.
"""

import sys
import os
import threading
import time

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orchestrator import Orchestrator

def debug_current_state():
    """Check the current state of the orchestrator."""
    print("=== Debugging Current Orchestrator State ===")
    
    orchestrator = Orchestrator()
    
    print(f"Is waiting for user action: {orchestrator.is_waiting_for_user_action}")
    print(f"Current execution ID: {orchestrator.current_execution_id}")
    print(f"Pending action payload: {orchestrator.pending_action_payload is not None}")
    print(f"Deferred action type: {orchestrator.deferred_action_type}")
    print(f"Mouse listener active: {orchestrator.mouse_listener_active}")
    
    # Check if deferred action lock is held
    lock_acquired = orchestrator.deferred_action_lock.acquire(blocking=False)
    if lock_acquired:
        print("✅ Deferred action lock is FREE")
        orchestrator.deferred_action_lock.release()
    else:
        print("❌ Deferred action lock is HELD")
    
    # Check execution lock
    exec_lock_acquired = orchestrator.execution_lock.acquire(blocking=False)
    if exec_lock_acquired:
        print("✅ Execution lock is FREE")
        orchestrator.execution_lock.release()
    else:
        print("❌ Execution lock is HELD")
    
    return orchestrator

def reset_deferred_state(orchestrator):
    """Reset the deferred action state."""
    print("\n=== Resetting Deferred Action State ===")
    
    try:
        # Force reset the deferred action state
        orchestrator._reset_deferred_action_state()
        print("✅ Deferred action state reset successfully")
        
        # Verify reset
        print(f"After reset - Is waiting: {orchestrator.is_waiting_for_user_action}")
        print(f"After reset - Execution ID: {orchestrator.current_execution_id}")
        print(f"After reset - Pending payload: {orchestrator.pending_action_payload is not None}")
        
    except Exception as e:
        print(f"❌ Error resetting state: {e}")

def test_simple_command(orchestrator):
    """Test a simple command to see if it works."""
    print("\n=== Testing Simple Command ===")
    
    try:
        result = orchestrator.execute_command("type hello")
        print(f"Command result: {result.get('status', 'unknown')}")
        print(f"Execution ID: {result.get('execution_id', 'none')}")
        return True
    except Exception as e:
        print(f"❌ Command failed: {e}")
        return False

def main():
    """Main debug function."""
    orchestrator = debug_current_state()
    
    # If system is stuck in deferred action mode, reset it
    if orchestrator.is_waiting_for_user_action:
        print("\n⚠️  System is stuck in deferred action mode!")
        reset_deferred_state(orchestrator)
        
        # Test if reset worked
        time.sleep(1)
        if test_simple_command(orchestrator):
            print("✅ System is now working normally")
        else:
            print("❌ System still has issues")
    else:
        print("\n✅ System appears to be in normal state")
        test_simple_command(orchestrator)

if __name__ == "__main__":
    main()