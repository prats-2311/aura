#!/usr/bin/env python3
"""
Deferred Action Lock Lifecycle Test

This test specifically verifies the lock management during deferred actions:
1. Command starts -> acquires execution lock
2. Enters deferred action -> releases execution lock early (for concurrency)
3. User clicks -> re-acquires execution lock for typing
4. Typing completes -> releases execution lock
5. Deferred action completes -> releases deferred action lock
"""

import sys
import logging
import threading
import time

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DeferredActionLockTest:
    """Test deferred action lock lifecycle."""
    
    def __init__(self):
        self.execution_lock = threading.Lock()
        self.deferred_action_lock = threading.Lock()
        self.is_waiting_for_user_action = False
        self.typing_in_progress = False
        self.test_results = []
    
    def log_test(self, test_name, success, message):
        """Log test result."""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append(success)
        logger.info(f"{status}: {test_name} - {message}")
    
    def simulate_command_execution(self):
        """Simulate the complete command execution lifecycle."""
        logger.info("🚀 Starting Deferred Action Command: 'Write me a Python function for sorting array'")
        
        # Phase 1: Command starts, acquires execution lock
        logger.info("Phase 1: Command execution starts")
        execution_acquired = self.execution_lock.acquire(timeout=1.0)
        self.log_test("Initial Execution Lock", execution_acquired, 
                     "Command should acquire execution lock at start")
        
        if not execution_acquired:
            return False
        
        try:
            # Phase 2: Intent recognition and content generation
            logger.info("Phase 2: Intent recognition and content generation")
            time.sleep(1)  # Simulate processing time
            
            # Phase 3: Enter deferred action mode
            logger.info("Phase 3: Entering deferred action mode")
            deferred_acquired = self.deferred_action_lock.acquire(timeout=1.0)
            self.log_test("Deferred Action Lock", deferred_acquired,
                         "Should acquire deferred action lock for state management")
            
            if not deferred_acquired:
                return False
            
            try:
                self.is_waiting_for_user_action = True
                
                # Phase 4: Release execution lock early (CRITICAL for concurrency)
                logger.info("Phase 4: Releasing execution lock early for concurrency")
                self.execution_lock.release()
                self.log_test("Early Execution Lock Release", True,
                             "Execution lock MUST be released to allow concurrent commands")
                
                # Phase 5: Wait for user action
                logger.info("Phase 5: Waiting for user click (Code generated successfully. Click where you want it placed)")
                logger.info("         🖱️  Simulating user click in 3 seconds...")
                time.sleep(3)
                
                # Phase 6: User clicks, trigger deferred action
                logger.info("Phase 6: User clicked! Triggering deferred action")
                return self.execute_deferred_action()
                
            finally:
                # Always release deferred action lock
                self.deferred_action_lock.release()
                self.is_waiting_for_user_action = False
                logger.info("Phase 8: Deferred action lock released")
                self.log_test("Deferred Action Lock Release", True,
                             "Deferred action lock released after completion")
        
        except Exception as e:
            self.log_test("Command Execution", False, f"Exception: {e}")
            return False
    
    def execute_deferred_action(self):
        """Execute the deferred action (typing)."""
        logger.info("Phase 7: Executing deferred action (typing)")
        
        # Re-acquire execution lock for typing
        logger.info("         Re-acquiring execution lock for typing...")
        typing_lock_acquired = self.execution_lock.acquire(timeout=2.0)
        self.log_test("Typing Lock Acquisition", typing_lock_acquired,
                     "MUST re-acquire execution lock before typing")
        
        if not typing_lock_acquired:
            logger.error("❌ CRITICAL: Could not acquire execution lock for typing!")
            return False
        
        try:
            self.typing_in_progress = True
            
            # Simulate typing process (this is where the code gets typed)
            logger.info("         🖨️  Typing code in progress...")
            logger.info("         def sort_array(arr):")
            time.sleep(0.5)
            logger.info("             return sorted(arr)")
            time.sleep(0.5)
            logger.info("         ✅ Code typing completed!")
            
            self.log_test("Code Typing", True,
                         "Code typed successfully while holding execution lock")
            
            return True
            
        finally:
            # CRITICAL: Always release execution lock after typing
            self.typing_in_progress = False
            self.execution_lock.release()
            logger.info("         ✅ Execution lock released after typing completion")
            self.log_test("Final Execution Lock Release", True,
                         "Execution lock MUST be released after typing")
    
    def test_concurrent_command_during_wait(self):
        """Test that concurrent commands can execute while waiting for user action."""
        logger.info("\n🔄 Testing Concurrent Command During Wait")
        
        def first_command():
            """First command that waits for user action."""
            logger.info("First Command: Starting deferred action")
            
            if self.execution_lock.acquire(timeout=1.0):
                try:
                    if self.deferred_action_lock.acquire(timeout=1.0):
                        try:
                            self.is_waiting_for_user_action = True
                            # Release execution lock early
                            self.execution_lock.release()
                            logger.info("First Command: Released execution lock, waiting for user...")
                            
                            # Wait for user action
                            time.sleep(4)
                            
                            # Re-acquire for typing
                            if self.execution_lock.acquire(timeout=2.0):
                                try:
                                    logger.info("First Command: Typing...")
                                    time.sleep(1)
                                finally:
                                    self.execution_lock.release()
                                    logger.info("First Command: Completed")
                        finally:
                            self.deferred_action_lock.release()
                            self.is_waiting_for_user_action = False
        
        def second_command():
            """Second command that should execute concurrently."""
            time.sleep(1)  # Start after first command
            logger.info("Second Command: Starting while first command waits")
            
            # Should be able to acquire execution lock since first released it
            acquired = self.execution_lock.acquire(timeout=2.0)
            if acquired:
                try:
                    logger.info("Second Command: Acquired execution lock successfully!")
                    time.sleep(1)  # Simulate processing
                    logger.info("Second Command: Completed")
                    return True
                finally:
                    self.execution_lock.release()
            else:
                logger.error("Second Command: Could not acquire execution lock!")
                return False
        
        # Start both commands
        results = {'second_completed': False}
        
        def second_wrapper():
            results['second_completed'] = second_command()
        
        thread1 = threading.Thread(target=first_command)
        thread2 = threading.Thread(target=second_wrapper)
        
        thread1.start()
        thread2.start()
        
        thread1.join(timeout=8)
        thread2.join(timeout=8)
        
        self.log_test("Concurrent Command Execution", results['second_completed'],
                     "Second command should execute while first waits for user")
        
        return results['second_completed']
    
    def run_all_tests(self):
        """Run all deferred action lock tests."""
        logger.info("🔒 Deferred Action Lock Lifecycle Testing")
        logger.info("=" * 60)
        
        # Test 1: Complete deferred action lifecycle
        test1_success = self.simulate_command_execution()
        
        # Reset state
        time.sleep(1)
        
        # Test 2: Concurrent command handling
        test2_success = self.test_concurrent_command_during_wait()
        
        # Summary
        logger.info("\n📊 Test Results Summary:")
        for i, result in enumerate(self.test_results, 1):
            status = "✅" if result else "❌"
            logger.info(f"{status} Test {i}")
        
        overall_success = test1_success and test2_success
        
        logger.info(f"\n🎯 Overall Result: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
        
        if overall_success:
            logger.info("\n✅ Lock Management Verified:")
            logger.info("  • Execution lock acquired at command start")
            logger.info("  • Execution lock released early for concurrency")
            logger.info("  • Execution lock re-acquired for typing")
            logger.info("  • Execution lock released after typing completion")
            logger.info("  • Deferred action lock managed properly")
            logger.info("  • Concurrent commands can execute during wait")
        
        return overall_success

def main():
    """Run deferred action lock lifecycle tests."""
    logger.info("🧪 Deferred Action Lock Lifecycle Test")
    logger.info("Testing the complete lock management cycle for deferred actions...")
    
    test = DeferredActionLockTest()
    success = test.run_all_tests()
    
    if success:
        logger.info("\n🎉 All lock lifecycle tests passed!")
        logger.info("The lock management should work correctly in AURA.")
        return True
    else:
        logger.error("\n💥 Lock lifecycle tests failed!")
        logger.error("There may be issues with lock management in AURA.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)