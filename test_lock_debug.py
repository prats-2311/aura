#!/usr/bin/env python3
"""
Simple test to debug the execution lock issue.
"""

import threading
import time
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_lock_behavior():
    """Test the basic lock behavior to understand the issue."""
    
    print("Testing basic lock behavior...")
    
    # Create a lock similar to the orchestrator
    execution_lock = threading.Lock()
    
    print(f"Initial lock state: {execution_lock.locked()}")
    
    # Test 1: Normal acquire and release
    print("\n=== Test 1: Normal acquire and release ===")
    lock_acquired = execution_lock.acquire(timeout=5.0)
    print(f"Lock acquired: {lock_acquired}, Lock state: {execution_lock.locked()}")
    
    if lock_acquired:
        execution_lock.release()
        print(f"Lock released, Lock state: {execution_lock.locked()}")
    
    # Test 2: Early release scenario (like deferred actions)
    print("\n=== Test 2: Early release scenario ===")
    lock_acquired = execution_lock.acquire(timeout=5.0)
    print(f"Lock acquired: {lock_acquired}, Lock state: {execution_lock.locked()}")
    
    if lock_acquired:
        # Simulate early release for deferred action
        execution_lock.release()
        lock_acquired = False  # Mark as released
        print(f"Early release done, Lock state: {execution_lock.locked()}")
    
    # Test 3: Try to acquire again (like second command)
    print("\n=== Test 3: Second acquisition ===")
    print(f"Lock state before second acquire: {execution_lock.locked()}")
    lock_acquired2 = execution_lock.acquire(timeout=5.0)
    print(f"Second lock acquired: {lock_acquired2}, Lock state: {execution_lock.locked()}")
    
    if lock_acquired2:
        execution_lock.release()
        print(f"Second lock released, Lock state: {execution_lock.locked()}")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    test_lock_behavior()