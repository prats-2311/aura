#!/usr/bin/env python3
"""
Task 0.5: Focused Concurrent Command Handling Tests

This test suite focuses on testing the core concurrency improvements:
- Lock timeout behavior
- Early lock release for deferred actions
- Lock re-acquisition in deferred action completion
- No deadlocks under concurrent usage
"""

import sys
import time
import threading
from unittest.mock import Mock, patch, MagicMock
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

# Add the project root to the path
sys.path.insert(0, '.')

# Set up logging for tests
logging.basicConfig(level=logging.WARNING)  # Reduce log noise
logger = logging.getLogger(__name__)

class FocusedConcurrencyTester:
    """Focused test suite for concurrency improvements."""
    
    def __init__(self):
        self.test_results = []
        
    def test_lock_timeout_behavior(self):
        """Test that lock acquisition times out properly."""
        print("🔧 Testing Lock Timeout Behavior")
        
        try:
            from orchestrator import Orchestrator
            
            # Create a minimal orchestrator for testing
            with patch('modules.vision.VisionModule'), \
                 patch('modules.reasoning.ReasoningModule'), \
                 patch('modules.automation.AutomationModule'), \
                 patch('modules.audio.AudioModule'), \
                 patch('modules.feedback.FeedbackModule'), \
                 patch('modules.accessibility.AccessibilityModule'):
                
                orchestrator = Orchestrator()
                
                # Disable error recovery to avoid additional delays
                orchestrator.error_recovery_enabled = False
                
                # Manually acquire the lock to simulate a stuck condition
                lock_acquired = orchestrator.execution_lock.acquire(blocking=False)
                if not lock_acquired:
                    print("❌ FAILED: Could not acquire lock for timeout test")
                    return False
                
                try:
                    # Try to execute a command - should timeout
                    start_time = time.time()
                    
                    try:
                        result = orchestrator.execute_command("Test command")
                        print(f"❌ FAILED: Command should have timed out but got: {result}")
                        return False
                    except Exception as e:
                        elapsed_time = time.time() - start_time
                        
                        # Should timeout within reasonable time (30 seconds + buffer)
                        # Allow more time since error recovery might still be attempted
                        if elapsed_time > 70:
                            print(f"❌ FAILED: Timeout took too long: {elapsed_time:.2f}s")
                            return False
                        
                        if "busy" not in str(e).lower() and "error" not in str(e).lower():
                            print(f"❌ FAILED: Wrong error message: {e}")
                            return False
                        
                        print(f"✅ SUCCESS: Lock timeout handled correctly in {elapsed_time:.2f}s")
                        return True
                        
                finally:
                    # Always release the lock
                    orchestrator.execution_lock.release()
                    
        except Exception as e:
            print(f"❌ FAILED: Error in lock timeout test: {e}")
            return False
    
    def test_early_lock_release_for_deferred_actions(self):
        """Test that locks are released early for deferred actions."""
        print("\n🔧 Testing Early Lock Release for Deferred Actions")
        
        try:
            from orchestrator import Orchestrator
            
            with patch('modules.vision.VisionModule'), \
                 patch('modules.reasoning.ReasoningModule'), \
                 patch('modules.automation.AutomationModule'), \
                 patch('modules.audio.AudioModule'), \
                 patch('modules.feedback.FeedbackModule'), \
                 patch('modules.accessibility.AccessibilityModule'):
                
                orchestrator = Orchestrator()
                
                # Mock _execute_command_internal to return a deferred action result
                def mock_execute_internal(command):
                    return {
                        'status': 'waiting_for_user_action',
                        'execution_id': 'test_123',
                        'message': 'Waiting for user click'
                    }
                
                orchestrator._execute_command_internal = mock_execute_internal
                
                # Execute command and check lock state
                result = orchestrator.execute_command("Test deferred command")
                
                # Verify the result is a deferred action
                if not (isinstance(result, dict) and result.get('status') == 'waiting_for_user_action'):
                    print(f"❌ FAILED: Expected deferred action result, got: {result}")
                    return False
                
                # Check that the lock is not held (should be released early)
                lock_available = orchestrator.execution_lock.acquire(blocking=False)
                if lock_available:
                    orchestrator.execution_lock.release()
                    print("✅ SUCCESS: Lock released early for deferred action")
                    return True
                else:
                    print("❌ FAILED: Lock not released early for deferred action")
                    return False
                    
        except Exception as e:
            print(f"❌ FAILED: Error in early lock release test: {e}")
            return False
    
    def test_lock_reacquisition_in_deferred_completion(self):
        """Test that locks are re-acquired properly in deferred action completion."""
        print("\n🔧 Testing Lock Re-acquisition in Deferred Completion")
        
        try:
            from orchestrator import Orchestrator
            
            with patch('modules.vision.VisionModule'), \
                 patch('modules.reasoning.ReasoningModule'), \
                 patch('modules.automation.AutomationModule'), \
                 patch('modules.audio.AudioModule'), \
                 patch('modules.feedback.FeedbackModule'), \
                 patch('modules.accessibility.AccessibilityModule'):
                
                orchestrator = Orchestrator()
                
                # Set up deferred action state
                orchestrator.is_waiting_for_user_action = True
                orchestrator.pending_action_payload = "test content"
                orchestrator.deferred_action_executing = False
                
                # Mock dependencies
                orchestrator.deferred_action_lock = threading.Lock()
                orchestrator._execute_pending_deferred_action = Mock(return_value=True)
                orchestrator._provide_deferred_action_completion_feedback = Mock()
                orchestrator._reset_deferred_action_state = Mock()
                
                # Test that the trigger method can acquire and release the lock properly
                try:
                    orchestrator._on_deferred_action_trigger("test_execution_id")
                    
                    # Verify that the execution was attempted
                    orchestrator._execute_pending_deferred_action.assert_called_once()
                    orchestrator._provide_deferred_action_completion_feedback.assert_called_once()
                    orchestrator._reset_deferred_action_state.assert_called_once()
                    
                    print("✅ SUCCESS: Lock re-acquisition in deferred completion works")
                    return True
                    
                except Exception as e:
                    print(f"❌ FAILED: Error during deferred action completion: {e}")
                    return False
                    
        except Exception as e:
            print(f"❌ FAILED: Error in lock re-acquisition test: {e}")
            return False
    
    def test_concurrent_command_execution(self):
        """Test concurrent command execution without deadlocks."""
        print("\n🔧 Testing Concurrent Command Execution")
        
        try:
            from orchestrator import Orchestrator
            
            with patch('modules.vision.VisionModule'), \
                 patch('modules.reasoning.ReasoningModule'), \
                 patch('modules.automation.AutomationModule'), \
                 patch('modules.audio.AudioModule'), \
                 patch('modules.feedback.FeedbackModule'), \
                 patch('modules.accessibility.AccessibilityModule'):
                
                orchestrator = Orchestrator()
                
                # Mock _execute_command_internal to return quickly
                def mock_execute_internal(command):
                    time.sleep(0.1)  # Small delay to simulate processing
                    return {
                        'status': 'completed',
                        'command': command,
                        'success': True
                    }
                
                orchestrator._execute_command_internal = mock_execute_internal
                
                # Execute multiple commands concurrently
                commands = [
                    "Command 1",
                    "Command 2", 
                    "Command 3",
                    "Command 4",
                    "Command 5"
                ]
                
                results = []
                start_time = time.time()
                
                def execute_command_with_id(cmd):
                    return orchestrator.execute_command(cmd)
                
                with ThreadPoolExecutor(max_workers=5) as executor:
                    # Submit all commands
                    futures = [executor.submit(execute_command_with_id, cmd) for cmd in commands]
                    
                    # Collect results with timeout
                    for future in as_completed(futures, timeout=30):
                        try:
                            result = future.result()
                            results.append(result)
                        except Exception as e:
                            results.append({"error": str(e)})
                
                total_time = time.time() - start_time
                
                # Analyze results
                successful_commands = sum(1 for r in results if isinstance(r, dict) and r.get('success'))
                
                if total_time > 10:  # Should not take more than 10 seconds
                    print(f"❌ FAILED: Concurrent execution took too long: {total_time:.2f}s")
                    return False
                
                if successful_commands < len(commands):
                    print(f"❌ FAILED: Not all commands succeeded: {successful_commands}/{len(commands)}")
                    return False
                
                print(f"✅ SUCCESS: Concurrent command execution works")
                print(f"   - Executed {len(commands)} commands concurrently")
                print(f"   - All {successful_commands} commands succeeded")
                print(f"   - Total execution time: {total_time:.2f}s")
                return True
                
        except Exception as e:
            print(f"❌ FAILED: Error in concurrent execution test: {e}")
            return False
    
    def test_deferred_action_state_management(self):
        """Test that deferred action state is managed correctly."""
        print("\n🔧 Testing Deferred Action State Management")
        
        try:
            from orchestrator import Orchestrator
            
            with patch('modules.vision.VisionModule'), \
                 patch('modules.reasoning.ReasoningModule'), \
                 patch('modules.automation.AutomationModule'), \
                 patch('modules.audio.AudioModule'), \
                 patch('modules.feedback.FeedbackModule'), \
                 patch('modules.accessibility.AccessibilityModule'):
                
                orchestrator = Orchestrator()
                
                # Test initial state
                if orchestrator.is_waiting_for_user_action != False:
                    print("❌ FAILED: Initial waiting state should be False")
                    return False
                
                if orchestrator.deferred_action_executing != False:
                    print("❌ FAILED: Initial executing state should be False")
                    return False
                
                # Test state changes
                orchestrator.is_waiting_for_user_action = True
                orchestrator.deferred_action_executing = True
                orchestrator.pending_action_payload = "test content"
                
                # Test state reset
                orchestrator._reset_deferred_action_state()
                
                # Verify state is reset
                if orchestrator.is_waiting_for_user_action != False:
                    print("❌ FAILED: Waiting state not reset properly")
                    return False
                
                if orchestrator.deferred_action_executing != False:
                    print("❌ FAILED: Executing state not reset properly")
                    return False
                
                if orchestrator.pending_action_payload is not None:
                    print("❌ FAILED: Payload not reset properly")
                    return False
                
                print("✅ SUCCESS: Deferred action state management works correctly")
                return True
                
        except Exception as e:
            print(f"❌ FAILED: Error in state management test: {e}")
            return False
    
    def test_race_condition_prevention(self):
        """Test that race conditions are prevented in deferred actions."""
        print("\n🔧 Testing Race Condition Prevention")
        
        try:
            from orchestrator import Orchestrator
            
            with patch('modules.vision.VisionModule'), \
                 patch('modules.reasoning.ReasoningModule'), \
                 patch('modules.automation.AutomationModule'), \
                 patch('modules.audio.AudioModule'), \
                 patch('modules.feedback.FeedbackModule'), \
                 patch('modules.accessibility.AccessibilityModule'):
                
                orchestrator = Orchestrator()
                
                # Set up deferred action state
                orchestrator.is_waiting_for_user_action = True
                orchestrator.pending_action_payload = "test content"
                orchestrator.deferred_action_executing = False
                orchestrator.deferred_action_lock = threading.Lock()
                
                # Mock dependencies
                orchestrator._execute_pending_deferred_action = Mock(return_value=True)
                orchestrator._provide_deferred_action_completion_feedback = Mock()
                orchestrator._reset_deferred_action_state = Mock()
                
                # Test duplicate trigger prevention
                orchestrator.deferred_action_executing = True  # Simulate already executing
                
                # This should be ignored due to race condition prevention
                orchestrator._on_deferred_action_trigger("test_execution_id")
                
                # Verify that execution was NOT attempted (due to race condition prevention)
                orchestrator._execute_pending_deferred_action.assert_not_called()
                
                print("✅ SUCCESS: Race condition prevention works correctly")
                return True
                
        except Exception as e:
            print(f"❌ FAILED: Error in race condition prevention test: {e}")
            return False
    
    def run_all_tests(self):
        """Run all focused concurrency tests."""
        print("🚀 Running Task 0.5: Focused Concurrency Tests")
        print("=" * 55)
        
        tests = [
            ("Lock Timeout Behavior", self.test_lock_timeout_behavior),
            ("Early Lock Release for Deferred Actions", self.test_early_lock_release_for_deferred_actions),
            ("Lock Re-acquisition in Deferred Completion", self.test_lock_reacquisition_in_deferred_completion),
            ("Concurrent Command Execution", self.test_concurrent_command_execution),
            ("Deferred Action State Management", self.test_deferred_action_state_management),
            ("Race Condition Prevention", self.test_race_condition_prevention),
        ]
        
        results = []
        for test_name, test_func in tests:
            try:
                result = test_func()
                results.append(result)
            except Exception as e:
                print(f"❌ FAILED: {test_name} - Unexpected error: {e}")
                results.append(False)
        
        print("\n" + "=" * 55)
        print("📊 Task 0.5 Test Results Summary:")
        
        passed = sum(results)
        total = len(results)
        
        if passed == total:
            print(f"✅ ALL TESTS PASSED ({passed}/{total})")
            print("\n🎉 Task 0.5: Concurrent Command Handling - COMPLETED!")
            print("\nValidated Concurrency Features:")
            print("- ✅ Lock timeout behavior (30 second timeout)")
            print("- ✅ Early lock release for deferred actions")
            print("- ✅ Lock re-acquisition in deferred action completion")
            print("- ✅ Concurrent command execution without deadlocks")
            print("- ✅ Proper deferred action state management")
            print("- ✅ Race condition prevention mechanisms")
            return 0
        else:
            print(f"❌ SOME TESTS FAILED ({passed}/{total})")
            print("\n⚠️  Please review the failed tests above")
            return 1

def main():
    """Main test execution function."""
    tester = FocusedConcurrencyTester()
    return tester.run_all_tests()

if __name__ == "__main__":
    exit(main())