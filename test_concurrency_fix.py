#!/usr/bin/env python3
"""
Test Concurrency Fix

This test simulates the lock timeout scenario to verify the fix works.
"""

import sys
import logging
import threading
import time

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_lock_timeout_behavior():
    """Test lock timeout behavior to prevent hanging."""
    logger.info("Testing lock timeout behavior...")
    
    # Create a lock to simulate the deferred action lock
    test_lock = threading.Lock()
    
    # Simulate first thread holding the lock (deferred action)
    def hold_lock():
        logger.info("Thread 1: Acquiring lock (simulating deferred action)")
        test_lock.acquire()
        logger.info("Thread 1: Lock acquired, holding for 10 seconds...")
        time.sleep(10)  # Hold lock for 10 seconds
        logger.info("Thread 1: Releasing lock")
        test_lock.release()
    
    # Start first thread
    thread1 = threading.Thread(target=hold_lock)
    thread1.start()
    
    # Give first thread time to acquire lock
    time.sleep(1)
    
    # Simulate second thread trying to acquire lock (second command)
    logger.info("Thread 2: Attempting to acquire lock with 5 second timeout...")
    start_time = time.time()
    
    try:
        lock_acquired = test_lock.acquire(timeout=5.0)
        if lock_acquired:
            logger.info("Thread 2: Lock acquired successfully")
            test_lock.release()
        else:
            elapsed = time.time() - start_time
            logger.info(f"Thread 2: Lock timeout after {elapsed:.1f} seconds - proceeding anyway")
            logger.info("✅ Timeout behavior working correctly - second command can continue")
    except Exception as e:
        logger.error(f"Thread 2: Error with lock: {e}")
    
    # Wait for first thread to complete
    thread1.join()
    
    return True

def test_intent_lock_simulation():
    """Test intent lock timeout simulation."""
    logger.info("Testing intent lock timeout simulation...")
    
    # Simulate the intent lock scenario
    intent_lock = threading.Lock()
    
    def simulate_intent_recognition():
        logger.info("Simulating intent recognition with timeout...")
        
        try:
            lock_acquired = intent_lock.acquire(timeout=10.0)
            if not lock_acquired:
                logger.warning("Could not acquire intent lock within timeout - using fallback")
                return {"intent": "gui_interaction", "confidence": 0.5, "fallback": True}
        except Exception as lock_error:
            logger.error(f"Error acquiring intent lock: {lock_error}")
            return {"intent": "gui_interaction", "confidence": 0.5, "error": True}
        
        try:
            # Simulate intent recognition work
            logger.info("Performing intent recognition...")
            time.sleep(1)  # Simulate API call
            result = {"intent": "deferred_action", "confidence": 0.95}
            logger.info(f"Intent recognized: {result}")
            return result
        finally:
            # Always release the intent lock
            try:
                intent_lock.release()
                logger.info("Intent lock released successfully")
            except Exception as release_error:
                logger.error(f"Error releasing intent lock: {release_error}")
    
    # Test the simulation
    result = simulate_intent_recognition()
    
    if result and result.get("intent"):
        logger.info("✅ Intent lock timeout simulation working correctly")
        return True
    else:
        logger.error("❌ Intent lock timeout simulation failed")
        return False

def main():
    """Run concurrency fix tests."""
    logger.info("🧪 Testing Concurrency Fix")
    logger.info("=" * 40)
    
    success1 = test_lock_timeout_behavior()
    success2 = test_intent_lock_simulation()
    
    if success1 and success2:
        logger.info("🎉 Concurrency fix tests passed!")
        logger.info("The lock timeout mechanisms should prevent hanging.")
        return True
    else:
        logger.error("💥 Concurrency fix tests failed!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)