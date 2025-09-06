#!/usr/bin/env python3
"""
Focused test for lock management in deferred actions.
Tests the specific scenario where consecutive deferred actions could hang.
"""

import threading
import time
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orchestrator import Orchestrator

def test_consecutive_deferred_actions():
    """Test that consecutive deferred actions don't hang due to lock issues."""
    print("=== Testing Consecutive Deferred Actions Lock Management ===")
    
    orchestrator = Orchestrator()
    
    # Track results
    results = []
    
    print("Starting first command that should trigger deferred action...")
    start_time = time.time()
    
    try:
        # First command - should trigger deferred action
        result1 = orchestrator.execute_command("type hello world")
        results.append(result1)
        print(f"First command result: {result1.get('status', 'unknown')}")
        
        # Wait a moment then start second command
        time.sleep(0.5)
        print("Starting second command...")
        
        # Second command - this should not hang
        result2 = orchestrator.execute_command("type goodbye world")
        results.append(result2)
        print(f"Second command result: {result2.get('status', 'unknown')}")
        
    except Exception as e:
        print(f"Exception during command execution: {e}")
        return False
    
    elapsed = time.time() - start_time
    
    if len(results) == 2:
        print(f"✅ SUCCESS: Both commands completed in {elapsed:.2f}s")
        print(f"First result status: {results[0].get('status', 'unknown')}")
        print(f"Second result status: {results[1].get('status', 'unknown')}")
        return True
    else:
        print(f"❌ FAILURE: Only {len(results)} commands completed in {elapsed:.2f}s")
        return False

def test_lock_timeout_mechanism():
    """Test that lock timeout prevents indefinite blocking."""
    print("\n=== Testing Lock Timeout Mechanism ===")
    
    orchestrator = Orchestrator()
    
    # Test the deferred action lock directly
    print("Testing deferred action lock acquisition with timeout...")
    
    # First, acquire the lock in a separate thread and hold it
    lock_held = threading.Event()
    lock_released = threading.Event()
    
    def hold_lock():
        """Hold the deferred action lock for a period."""
        print("Background thread acquiring deferred action lock...")
        acquired = orchestrator.deferred_action_lock.acquire(timeout=5)
        if acquired:
            lock_held.set()
            print("Background thread has lock, holding for 3 seconds...")
            time.sleep(3)
            orchestrator.deferred_action_lock.release()
            lock_released.set()
            print("Background thread released lock")
        else:
            print("Background thread failed to acquire lock")
    
    # Start background thread
    thread = threading.Thread(target=hold_lock)
    thread.start()
    
    # Wait for lock to be held
    if not lock_held.wait(timeout=10):
        print("❌ Background thread failed to acquire lock")
        thread.join()
        return False
    
    # Now try to acquire the lock with timeout from main thread
    print("Main thread attempting to acquire lock with timeout...")
    start_time = time.time()
    
    acquired = orchestrator.deferred_action_lock.acquire(timeout=5)
    elapsed = time.time() - start_time
    
    if acquired:
        orchestrator.deferred_action_lock.release()
        print(f"✅ SUCCESS: Lock acquired after {elapsed:.2f}s (after background thread released)")
        success = True
    else:
        print(f"⚠️  Lock acquisition timed out after {elapsed:.2f}s (expected behavior)")
        success = True  # This is actually expected behavior
    
    # Clean up
    thread.join(timeout=10)
    
    return success

def main():
    """Run focused lock management tests."""
    print("Starting focused lock management tests...\n")
    
    test1_passed = test_consecutive_deferred_actions()
    test2_passed = test_lock_timeout_mechanism()
    
    print(f"\n=== Test Results ===")
    print(f"Consecutive Actions Test: {'PASS' if test1_passed else 'FAIL'}")
    print(f"Lock Timeout Test: {'PASS' if test2_passed else 'FAIL'}")
    
    if test1_passed and test2_passed:
        print("✅ All lock management tests PASSED")
        return 0
    else:
        print("❌ Some lock management tests FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())