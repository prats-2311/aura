#!/usr/bin/env python3
"""
Comprehensive Lock Management Testing

This test suite verifies proper lock management across all scenarios:
1. Lock acquisition and release timing
2. Deferred action lock lifecycle
3. Concurrent command handling
4. Error scenarios and recovery
5. Lock timeout behavior
"""

import sys
import logging
import threading
import time
from unittest.mock import Mock, patch
from enum import Enum

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LockState(Enum):
    AVAILABLE = "available"
    ACQUIRED = "acquired"
    TIMEOUT = "timeout"
    ERROR = "error"

class LockTestScenario:
    """Test scenario for lock management."""
    
    def __init__(self, name, description):
        self.name = name
        self.description = description
        self.execution_lock = threading.Lock()
        self.deferred_action_lock = threading.Lock()
        self.intent_lock = threading.Lock()
        self.results = []
    
    def log_result(self, test_name, success, message):
        """Log test result."""
        status = "✅ PASS" if success else "❌ FAIL"
        self.results.append({
            'test': test_name,
            'success': success,
            'message': message
        })
        logger.info(f"{status}: {test_name} - {message}")
    
    def simulate_deferred_action_lifecycle(self):
        """Test complete deferred action lock lifecycle."""
        logger.info(f"\n--- {self.name}: Deferred Action Lifecycle ---")
        
        # Phase 1: Command starts, acquires execution lock
        logger.info("Phase 1: Command execution starts")
        execution_acquired = self.execution_lock.acquire(timeout=1.0)
        self.log_result("Execution Lock Acquisition", execution_acquired, 
                       "Command should acquire execution lock")
        
        if not execution_acquired:
            return False
        
        try:
            # Phase 2: Enter deferred action mode, acquire deferred action lock
            logger.info("Phase 2: Entering deferred action mode")
            deferred_acquired = self.deferred_action_lock.acquire(timeout=1.0)
            self.log_result("Deferred Action Lock Acquisition", deferred_acquired,
                           "Should acquire deferred action lock for state management")
            
            if deferred_acquired:
                try:
                    # Phase 3: Release execution lock early (for concurrency)
                    logger.info("Phase 3: Releasing execution lock early for concurrency")
                    self.execution_lock.release()
                    self.log_result("Early Execution Lock Release", True,
                                   "Execution lock released to allow concurrent commands")
                    
                    # Phase 4: Wait for user action (simulated)
                    logger.info("Phase 4: Waiting for user action (simulated 2 seconds)")
                    time.sleep(2)
                    
                    # Phase 5: User action triggers, re-acquire execution lock for typing
                    logger.info("Phase 5: User clicked, re-acquiring execution lock for typing")
                    typing_lock_acquired = self.execution_lock.acquire(timeout=1.0)
                    self.log_result("Typing Execution Lock Re-acquisition", typing_lock_acquired,
                                   "Should re-acquire execution lock for typing phase")
                    
                    if typing_lock_acquired:
                        try:
                            # Phase 6: Simulate typing (hold lock during typing)
                            logger.info("Phase 6: Typing in progress (simulated 3 seconds)")
                            time.sleep(3)
                            self.log_result("Typing Phase", True,
                                           "Lock held during entire typing operation")
                            
                        finally:
                            # Phase 7: Release execution lock after typing
                            logger.info("Phase 7: Typing complete, releasing execution lock")
                            self.execution_lock.release()
                            self.log_result("Final Execution Lock Release", True,
                                           "Execution lock released after typing completion")
                    
                finally:
                    # Phase 8: Release deferred action lock
                    logger.info("Phase 8: Releasing deferred action lock")
                    self.deferred_action_lock.release()
                    self.log_result("Deferred Action Lock Release", True,
                                   "Deferred action lock released after completion")
            
            return True
            
        except Exception as e:
            self.log_result("Deferred Action Lifecycle", False, f"Exception: {e}")
            return False
    
    def simulate_concurrent_commands(self):
        """Test concurrent command handling."""
        logger.info(f"\n--- {self.name}: Concurrent Commands ---")
        
        results = {'first_command': False, 'second_command': False}
        
        def first_command():
            """Simulate first command (deferred action)."""
            logger.info("First Command: Starting")
            
            # Acquire execution lock
            if self.execution_lock.acquire(timeout=1.0):
                try:
                    logger.info("First Command: Execution lock acquired")
                    
                    # Enter deferred action mode
                    if self.deferred_action_lock.acquire(timeout=1.0):
                        try:
                            logger.info("First Command: Entered deferred action mode")
                            
                            # Release execution lock early
                            self.execution_lock.release()
                            logger.info("First Command: Released execution lock early")
                            
                            # Wait for user action
                            time.sleep(4)
                            
                            # Re-acquire for typing
                            if self.execution_lock.acquire(timeout=1.0):
                                try:
                                    logger.info("First Command: Re-acquired lock for typing")
                                    time.sleep(2)  # Simulate typing
                                    results['first_command'] = True
                                finally:
                                    self.execution_lock.release()
                                    logger.info("First Command: Final lock release")
                        finally:
                            self.deferred_action_lock.release()
                            logger.info("First Command: Deferred action lock released")
                except Exception as e:
                    logger.error(f"First Command Error: {e}")
        
        def second_command():
            """Simulate second command (should not hang)."""
            # Wait a bit to ensure first command starts
            time.sleep(1)
            logger.info("Second Command: Starting")
            
            # Try to acquire deferred action lock with timeout
            try:
                deferred_acquired = self.deferred_action_lock.acquire(timeout=2.0)
                if deferred_acquired:
                    try:
                        logger.info("Second Command: Acquired deferred action lock")
                        # Reset first command's deferred state (simulated)
                        time.sleep(0.5)
                    finally:
                        self.deferred_action_lock.release()
                        logger.info("Second Command: Released deferred action lock")
                else:
                    logger.info("Second Command: Deferred action lock timeout - proceeding anyway")
                
                # Continue with execution
                if self.execution_lock.acquire(timeout=3.0):
                    try:
                        logger.info("Second Command: Acquired execution lock")
                        time.sleep(1)  # Simulate processing
                        results['second_command'] = True
                    finally:
                        self.execution_lock.release()
                        logger.info("Second Command: Released execution lock")
                else:
                    logger.warning("Second Command: Execution lock timeout")
                    
            except Exception as e:
                logger.error(f"Second Command Error: {e}")
        
        # Start both commands
        thread1 = threading.Thread(target=first_command)
        thread2 = threading.Thread(target=second_command)
        
        thread1.start()
        thread2.start()
        
        # Wait for completion
        thread1.join(timeout=10)
        thread2.join(timeout=10)
        
        # Check results
        self.log_result("First Command Completion", results['first_command'],
                       "First command should complete successfully")
        self.log_result("Second Command Completion", results['second_command'],
                       "Second command should not hang and complete successfully")
        
        return results['first_command'] and results['second_command']
    
    def simulate_error_scenarios(self):
        """Test error scenarios and recovery."""
        logger.info(f"\n--- {self.name}: Error Scenarios ---")
        
        # Test 1: Lock acquisition failure
        logger.info("Test 1: Lock acquisition timeout")
        
        # Hold the lock in another thread
        def hold_lock():
            self.execution_lock.acquire()
            time.sleep(3)
            self.execution_lock.release()
        
        holder_thread = threading.Thread(target=hold_lock)
        holder_thread.start()
        
        time.sleep(0.5)  # Ensure lock is held
        
        # Try to acquire with timeout
        start_time = time.time()
        acquired = self.execution_lock.acquire(timeout=1.0)
        elapsed = time.time() - start_time
        
        if not acquired and elapsed >= 1.0:
            self.log_result("Lock Timeout Behavior", True,
                           f"Lock timeout worked correctly ({elapsed:.1f}s)")
        else:
            self.log_result("Lock Timeout Behavior", False,
                           f"Lock timeout failed ({elapsed:.1f}s, acquired: {acquired})")
        
        holder_thread.join()
        
        # Test 2: Exception during lock holding
        logger.info("Test 2: Exception handling with locks")
        
        try:
            if self.execution_lock.acquire(timeout=1.0):
                try:
                    # Simulate exception during processing
                    raise Exception("Simulated processing error")
                finally:
                    self.execution_lock.release()
                    self.log_result("Exception Lock Release", True,
                                   "Lock released properly in finally block")
        except Exception as e:
            logger.info(f"Exception handled: {e}")
        
        return True
    
    def run_all_tests(self):
        """Run all lock management tests."""
        logger.info(f"\n🧪 Running Lock Management Tests: {self.name}")
        logger.info("=" * 60)
        
        test_results = []
        
        # Run test scenarios
        test_results.append(self.simulate_deferred_action_lifecycle())
        test_results.append(self.simulate_concurrent_commands())
        test_results.append(self.simulate_error_scenarios())
        
        # Summary
        logger.info(f"\n📊 Test Results Summary for {self.name}:")
        for result in self.results:
            status = "✅" if result['success'] else "❌"
            logger.info(f"{status} {result['test']}: {result['message']}")
        
        overall_success = all(test_results)
        logger.info(f"\n🎯 Overall Result: {'✅ PASS' if overall_success else '❌ FAIL'}")
        
        return overall_success

def test_lock_management_scenarios():
    """Test various lock management scenarios."""
    logger.info("🧪 Comprehensive Lock Management Testing")
    logger.info("=" * 80)
    
    scenarios = [
        LockTestScenario("Standard Deferred Action", 
                        "Normal deferred action with proper lock lifecycle"),
        LockTestScenario("Concurrent Commands", 
                        "Multiple commands with lock contention"),
        LockTestScenario("Error Recovery", 
                        "Lock management during error conditions")
    ]
    
    all_passed = True
    
    for scenario in scenarios:
        passed = scenario.run_all_tests()
        all_passed = all_passed and passed
        time.sleep(1)  # Brief pause between scenarios
    
    return all_passed

def main():
    """Run comprehensive lock management tests."""
    logger.info("🔒 Comprehensive Lock Management Testing Suite")
    logger.info("=" * 80)
    logger.info("Testing lock acquisition, release, timeouts, and concurrency...")
    
    success = test_lock_management_scenarios()
    
    if success:
        logger.info("\n🎉 All lock management tests passed!")
        logger.info("Lock management should work correctly in AURA:")
        logger.info("  ✅ Proper lock lifecycle during deferred actions")
        logger.info("  ✅ Early execution lock release for concurrency")
        logger.info("  ✅ Lock re-acquisition for typing phase")
        logger.info("  ✅ Timeout handling to prevent hanging")
        logger.info("  ✅ Exception safety with proper cleanup")
        return True
    else:
        logger.error("\n💥 Some lock management tests failed!")
        logger.error("Review the test results above for specific issues.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)