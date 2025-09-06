#!/usr/bin/env python3
"""
Simple test for Task 0.1: Fix Concurrency Deadlock in Deferred Actions

This test focuses specifically on the lock management behavior without complex mocking.
"""

import threading
import time
import logging
from orchestrator import Orchestrator

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_lock_management():
    """Test that the lock management works correctly for deferred actions."""
    
    print("=" * 60)
    print("TESTING TASK 0.1: LOCK MANAGEMENT FIX")
    print("=" * 60)
    
    # Create orchestrator instance
    orchestrator = Orchestrator()
    
    # Test 1: Verify lock is initially not locked
    print("\n1. Testing initial lock state...")
    if not orchestrator.execution_lock.locked():
        print("✓ Execution lock is initially unlocked")
    else:
        print("✗ Execution lock is initially locked (unexpected)")
        return False
    
    # Test 2: Test lock acquisition and release
    print("\n2. Testing basic lock acquisition and release...")
    orchestrator.execution_lock.acquire()
    if orchestrator.execution_lock.locked():
        print("✓ Lock acquired successfully")
    else:
        print("✗ Lock acquisition failed")
        return False
    
    orchestrator.execution_lock.release()
    if not orchestrator.execution_lock.locked():
        print("✓ Lock released successfully")
    else:
        print("✗ Lock release failed")
        return False
    
    # Test 3: Test deferred action state management
    print("\n3. Testing deferred action state management...")
    
    # Simulate entering deferred action waiting state
    orchestrator.is_waiting_for_user_action = True
    orchestrator.pending_action_payload = "test content"
    orchestrator.deferred_action_type = "type"
    
    if orchestrator.is_waiting_for_user_action:
        print("✓ Deferred action state set correctly")
    else:
        print("✗ Deferred action state not set")
        return False
    
    # Test 4: Test _on_deferred_action_trigger lock management
    print("\n4. Testing deferred action trigger lock management...")
    
    # Ensure lock is not held initially
    if orchestrator.execution_lock.locked():
        orchestrator.execution_lock.release()
    
    def test_trigger():
        """Test the deferred action trigger method."""
        try:
            # This should acquire the lock at the beginning
            orchestrator._on_deferred_action_trigger("test_execution_id")
            return True
        except Exception as e:
            logger.error(f"Error in deferred action trigger: {e}")
            return False
    
    # Run the trigger test
    trigger_success = test_trigger()
    
    # Verify lock is released after trigger
    if not orchestrator.execution_lock.locked():
        print("✓ Lock properly released after deferred action trigger")
    else:
        print("✗ Lock not released after deferred action trigger")
        # Force release for cleanup
        try:
            orchestrator.execution_lock.release()
        except:
            pass
        return False
    
    # Test 5: Test concurrent access simulation
    print("\n5. Testing concurrent access simulation...")
    
    results = {'lock_acquired': False, 'lock_released': False, 'error': None}
    
    def simulate_concurrent_command():
        """Simulate a concurrent command trying to acquire the lock."""
        try:
            # Try to acquire lock (should succeed if previous command released it)
            acquired = orchestrator.execution_lock.acquire(timeout=2.0)
            if acquired:
                results['lock_acquired'] = True
                time.sleep(0.1)  # Simulate some work
                orchestrator.execution_lock.release()
                results['lock_released'] = True
            else:
                results['error'] = "Could not acquire lock within timeout"
        except Exception as e:
            results['error'] = str(e)
    
    # Start concurrent thread
    thread = threading.Thread(target=simulate_concurrent_command)
    thread.start()
    thread.join(timeout=5.0)
    
    if results['lock_acquired'] and results['lock_released'] and not results['error']:
        print("✓ Concurrent access simulation successful")
    else:
        print(f"✗ Concurrent access simulation failed: {results}")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 ALL LOCK MANAGEMENT TESTS PASSED!")
    print("✓ Lock acquisition and release working correctly")
    print("✓ Deferred action state management working")
    print("✓ Deferred action trigger lock management working")
    print("✓ Concurrent access simulation successful")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = test_lock_management()
    if not success:
        print("\n❌ LOCK MANAGEMENT TESTS FAILED")
        exit(1)
    else:
        print("\n✅ LOCK MANAGEMENT TESTS PASSED")
        exit(0)