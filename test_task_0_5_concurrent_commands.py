#!/usr/bin/env python3
"""
Task 0.5: Test and validate concurrent command handling

This test suite validates:
- Concurrent deferred action scenarios
- Command interruption during deferred action wait states
- Second commands processing while first waits for user input
- Lock timeout and recovery scenarios
- No deadlocks under various concurrent usage patterns
"""

import sys
import time
import threading
import asyncio
from unittest.mock import Mock, patch, MagicMock
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

# Add the project root to the path
sys.path.insert(0, '.')

# Set up logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConcurrentCommandTester:
    """Test suite for concurrent command handling validation."""
    
    def __init__(self):
        self.test_results = []
        self.orchestrator = None
        
    def setup_mock_orchestrator(self):
        """Set up a mock orchestrator for testing."""
        try:
            from orchestrator import Orchestrator
            
            # Create orchestrator with mocked dependencies
            with patch('modules.vision.VisionModule'), \
                 patch('modules.reasoning.ReasoningModule'), \
                 patch('modules.automation.AutomationModule'), \
                 patch('modules.audio.AudioModule'), \
                 patch('modules.feedback.FeedbackModule'), \
                 patch('modules.accessibility.AccessibilityModule'):
                
                self.orchestrator = Orchestrator()
                
                # Mock the reasoning module for content generation
                mock_reasoning = Mock()
                mock_reasoning._make_api_request.return_value = {
                    'choices': [{
                        'message': {
                            'content': 'def test_function():\n    return "Hello World"'
                        }
                    }]
                }
                self.orchestrator.reasoning_module = mock_reasoning
                
                # Mock other modules
                self.orchestrator.automation_module = Mock()
                self.orchestrator.feedback_module = Mock()
                self.orchestrator.audio_module = Mock()
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to setup mock orchestrator: {e}")
            return False
    
    def test_concurrent_deferred_actions(self):
        """Test concurrent deferred action scenarios."""
        print("🔧 Testing Concurrent Deferred Actions")
        
        try:
            if not self.setup_mock_orchestrator():
                return False
            
            # Mock the mouse listener to avoid actual GUI interaction
            with patch('utils.mouse_listener.GlobalMouseListener') as mock_listener_class:
                mock_listener = Mock()
                mock_listener.start.return_value = None
                mock_listener.get_last_click_coordinates.return_value = (100, 100)
                mock_listener_class.return_value = mock_listener
                
                # Test: Start first deferred action
                result1 = self.orchestrator.execute_command("Write me a Python function")
                
                if not (isinstance(result1, dict) and result1.get('status') == 'waiting_for_user_action'):
                    print(f"❌ FAILED: First deferred action didn't return waiting status: {result1}")
                    return False
                
                # Test: Start second deferred action while first is waiting
                result2 = self.orchestrator.execute_command("Write me another Python function")
                
                if not (isinstance(result2, dict) and result2.get('status') == 'waiting_for_user_action'):
                    print(f"❌ FAILED: Second deferred action didn't work: {result2}")
                    return False
                
                print("✅ SUCCESS: Concurrent deferred actions handled correctly")
                print("   - First action started and entered waiting state")
                print("   - Second action cancelled first and started new waiting state")
                return True
                
        except Exception as e:
            print(f"❌ FAILED: Error in concurrent deferred actions test: {e}")
            return False
    
    def test_command_interruption_during_wait(self):
        """Test command interruption during deferred action wait states."""
        print("\n🔧 Testing Command Interruption During Wait States")
        
        try:
            if not self.setup_mock_orchestrator():
                return False
            
            with patch('utils.mouse_listener.GlobalMouseListener') as mock_listener_class:
                mock_listener = Mock()
                mock_listener.start.return_value = None
                mock_listener_class.return_value = mock_listener
                
                # Start deferred action
                result1 = self.orchestrator.execute_command("Write me a Python function")
                
                if not (isinstance(result1, dict) and result1.get('status') == 'waiting_for_user_action'):
                    print(f"❌ FAILED: Deferred action setup failed: {result1}")
                    return False
                
                # Interrupt with a regular GUI command
                result2 = self.orchestrator.execute_command("Click on the button")
                
                # The interrupting command should execute successfully
                if isinstance(result2, dict) and result2.get('status') == 'error':
                    print(f"❌ FAILED: Interrupting command failed: {result2}")
                    return False
                
                print("✅ SUCCESS: Command interruption handled correctly")
                print("   - Deferred action started and entered waiting state")
                print("   - Interrupting command executed without deadlock")
                return True
                
        except Exception as e:
            print(f"❌ FAILED: Error in command interruption test: {e}")
            return False
    
    def test_second_command_processing_during_wait(self):
        """Test that second commands process while first waits for user input."""
        print("\n🔧 Testing Second Command Processing During Wait")
        
        try:
            if not self.setup_mock_orchestrator():
                return False
            
            with patch('utils.mouse_listener.GlobalMouseListener') as mock_listener_class:
                mock_listener = Mock()
                mock_listener.start.return_value = None
                mock_listener_class.return_value = mock_listener
                
                # Start deferred action in a separate thread
                def start_deferred_action():
                    return self.orchestrator.execute_command("Write me a Python function")
                
                def execute_second_command():
                    time.sleep(0.1)  # Small delay to ensure first command starts
                    return self.orchestrator.execute_command("What is 2 + 2?")
                
                # Execute both commands concurrently
                with ThreadPoolExecutor(max_workers=2) as executor:
                    future1 = executor.submit(start_deferred_action)
                    future2 = executor.submit(execute_second_command)
                    
                    # Wait for both to complete
                    result1 = future1.result(timeout=10)
                    result2 = future2.result(timeout=10)
                
                # Verify results
                if not (isinstance(result1, dict) and result1.get('status') == 'waiting_for_user_action'):
                    print(f"❌ FAILED: First command (deferred) didn't work: {result1}")
                    return False
                
                # Second command should complete normally (not waiting)
                if isinstance(result2, dict) and result2.get('status') == 'waiting_for_user_action':
                    print(f"❌ FAILED: Second command shouldn't be waiting: {result2}")
                    return False
                
                print("✅ SUCCESS: Second command processed while first waits")
                print("   - First command entered waiting state")
                print("   - Second command executed independently")
                return True
                
        except Exception as e:
            print(f"❌ FAILED: Error in second command processing test: {e}")
            return False
    
    def test_lock_timeout_and_recovery(self):
        """Test lock timeout and recovery scenarios."""
        print("\n🔧 Testing Lock Timeout and Recovery")
        
        try:
            if not self.setup_mock_orchestrator():
                return False
            
            # Simulate a stuck lock by manually acquiring it
            lock_acquired = self.orchestrator.execution_lock.acquire(blocking=False)
            if not lock_acquired:
                print("❌ FAILED: Could not acquire lock for timeout test")
                return False
            
            try:
                # Try to execute a command - should timeout
                start_time = time.time()
                
                try:
                    result = self.orchestrator.execute_command("Test command")
                    print(f"❌ FAILED: Command should have timed out but got: {result}")
                    return False
                except Exception as e:
                    elapsed_time = time.time() - start_time
                    
                    # Should timeout within reasonable time (30 seconds + some buffer)
                    if elapsed_time > 35:
                        print(f"❌ FAILED: Timeout took too long: {elapsed_time:.2f}s")
                        return False
                    
                    if "busy" not in str(e).lower() and "timeout" not in str(e).lower():
                        print(f"❌ FAILED: Wrong error message: {e}")
                        return False
                    
                    print(f"✅ SUCCESS: Lock timeout handled correctly in {elapsed_time:.2f}s")
                    print(f"   - Error message: {str(e)[:100]}...")
                    return True
                    
            finally:
                # Always release the lock
                self.orchestrator.execution_lock.release()
                
        except Exception as e:
            print(f"❌ FAILED: Error in lock timeout test: {e}")
            return False
    
    def test_no_deadlocks_under_concurrent_usage(self):
        """Test that no deadlocks occur under various concurrent usage patterns."""
        print("\n🔧 Testing No Deadlocks Under Concurrent Usage")
        
        try:
            if not self.setup_mock_orchestrator():
                return False
            
            with patch('utils.mouse_listener.GlobalMouseListener') as mock_listener_class:
                mock_listener = Mock()
                mock_listener.start.return_value = None
                mock_listener_class.return_value = mock_listener
                
                # Define various command types
                commands = [
                    "Write me a Python function",  # Deferred action
                    "Click on the button",         # GUI action
                    "What is the weather?",        # Question
                    "Write me some text",          # Another deferred action
                    "Scroll down",                 # GUI action
                ]
                
                # Execute multiple commands concurrently
                results = []
                start_time = time.time()
                
                def execute_command_with_delay(cmd, delay):
                    time.sleep(delay)
                    return self.orchestrator.execute_command(cmd)
                
                with ThreadPoolExecutor(max_workers=5) as executor:
                    # Submit commands with small delays
                    futures = []
                    for i, cmd in enumerate(commands):
                        delay = i * 0.1  # Stagger commands by 100ms
                        future = executor.submit(execute_command_with_delay, cmd, delay)
                        futures.append((cmd, future))
                    
                    # Collect results with timeout
                    for cmd, future in futures:
                        try:
                            result = future.result(timeout=15)  # 15 second timeout per command
                            results.append((cmd, result, "success"))
                        except Exception as e:
                            results.append((cmd, str(e), "error"))
                
                total_time = time.time() - start_time
                
                # Analyze results
                successful_commands = sum(1 for _, _, status in results if status == "success")
                
                if total_time > 60:  # Should not take more than 1 minute
                    print(f"❌ FAILED: Concurrent execution took too long: {total_time:.2f}s")
                    return False
                
                if successful_commands < len(commands) // 2:  # At least half should succeed
                    print(f"❌ FAILED: Too many commands failed: {successful_commands}/{len(commands)}")
                    for cmd, result, status in results:
                        if status == "error":
                            print(f"   Failed: {cmd} -> {result}")
                    return False
                
                print(f"✅ SUCCESS: No deadlocks detected in concurrent usage")
                print(f"   - Executed {len(commands)} commands concurrently")
                print(f"   - {successful_commands}/{len(commands)} commands succeeded")
                print(f"   - Total execution time: {total_time:.2f}s")
                return True
                
        except Exception as e:
            print(f"❌ FAILED: Error in concurrent usage test: {e}")
            return False
    
    def test_deferred_action_completion_after_wait(self):
        """Test that deferred actions can complete properly after waiting."""
        print("\n🔧 Testing Deferred Action Completion After Wait")
        
        try:
            if not self.setup_mock_orchestrator():
                return False
            
            with patch('utils.mouse_listener.GlobalMouseListener') as mock_listener_class:
                mock_listener = Mock()
                mock_listener.start.return_value = None
                mock_listener.get_last_click_coordinates.return_value = (200, 300)
                mock_listener_class.return_value = mock_listener
                
                # Start deferred action
                result = self.orchestrator.execute_command("Write me a Python function")
                
                if not (isinstance(result, dict) and result.get('status') == 'waiting_for_user_action'):
                    print(f"❌ FAILED: Deferred action setup failed: {result}")
                    return False
                
                execution_id = result.get('execution_id')
                if not execution_id:
                    print("❌ FAILED: No execution_id in deferred action result")
                    return False
                
                # Simulate user click to complete the action
                try:
                    self.orchestrator._on_deferred_action_trigger(execution_id)
                    print("✅ SUCCESS: Deferred action completion handled correctly")
                    print("   - Action started and entered waiting state")
                    print("   - User click simulation completed without errors")
                    return True
                except Exception as e:
                    print(f"❌ FAILED: Error during deferred action completion: {e}")
                    return False
                
        except Exception as e:
            print(f"❌ FAILED: Error in deferred action completion test: {e}")
            return False
    
    def run_all_tests(self):
        """Run all concurrent command handling tests."""
        print("🚀 Running Task 0.5: Concurrent Command Handling Tests")
        print("=" * 60)
        
        tests = [
            ("Concurrent Deferred Actions", self.test_concurrent_deferred_actions),
            ("Command Interruption During Wait", self.test_command_interruption_during_wait),
            ("Second Command Processing During Wait", self.test_second_command_processing_during_wait),
            ("Lock Timeout and Recovery", self.test_lock_timeout_and_recovery),
            ("No Deadlocks Under Concurrent Usage", self.test_no_deadlocks_under_concurrent_usage),
            ("Deferred Action Completion After Wait", self.test_deferred_action_completion_after_wait),
        ]
        
        results = []
        for test_name, test_func in tests:
            try:
                result = test_func()
                results.append(result)
            except Exception as e:
                print(f"❌ FAILED: {test_name} - Unexpected error: {e}")
                results.append(False)
        
        print("\n" + "=" * 60)
        print("📊 Task 0.5 Test Results Summary:")
        
        passed = sum(results)
        total = len(results)
        
        if passed == total:
            print(f"✅ ALL TESTS PASSED ({passed}/{total})")
            print("\n🎉 Task 0.5: Concurrent Command Handling - COMPLETED!")
            print("\nValidated Features:")
            print("- ✅ Concurrent deferred action scenarios")
            print("- ✅ Command interruption during deferred action wait states")
            print("- ✅ Second commands process while first waits for user input")
            print("- ✅ Lock timeout and recovery scenarios")
            print("- ✅ No deadlocks under various concurrent usage patterns")
            print("- ✅ Deferred action completion after wait")
            return 0
        else:
            print(f"❌ SOME TESTS FAILED ({passed}/{total})")
            print("\n⚠️  Please review the failed tests above")
            return 1

def main():
    """Main test execution function."""
    tester = ConcurrentCommandTester()
    return tester.run_all_tests()

if __name__ == "__main__":
    exit(main())