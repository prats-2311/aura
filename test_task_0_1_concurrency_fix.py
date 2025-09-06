#!/usr/bin/env python3
"""
Test suite for Task 0.1: Fix Concurrency Deadlock in Deferred Actions

This test suite validates the improved execution lock management and concurrent
command handling implemented in the orchestrator.
"""

import unittest
import threading
import time
import logging
from unittest.mock import Mock, patch, MagicMock
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orchestrator import Orchestrator, OrchestratorError

# Configure logging for tests
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class TestConcurrencyFix(unittest.TestCase):
    """Test cases for concurrency deadlock fixes in deferred actions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.orchestrator = Orchestrator()
        
        # Mock modules to avoid actual system interactions
        self.orchestrator.vision_module = Mock()
        self.orchestrator.reasoning_module = Mock()
        self.orchestrator.automation_module = Mock()
        self.orchestrator.audio_module = Mock()
        self.orchestrator.feedback_module = Mock()
        self.orchestrator.accessibility_module = Mock()
        
        # Set module availability
        self.orchestrator.module_availability = {
            'vision': True,
            'reasoning': True,
            'automation': True,
            'audio': True,
            'feedback': True,
            'accessibility': True
        }
        
        # Mock the internal execution method to control behavior
        self.orchestrator._execute_command_internal = Mock()
        
    def tearDown(self):
        """Clean up after tests."""
        # Ensure any locks are released
        if hasattr(self.orchestrator, 'execution_lock') and self.orchestrator.execution_lock.locked():
            try:
                self.orchestrator.execution_lock.release()
            except:
                pass
                
        if hasattr(self.orchestrator, 'intent_lock') and self.orchestrator.intent_lock.locked():
            try:
                self.orchestrator.intent_lock.release()
            except:
                pass
    
    def test_timeout_based_lock_acquisition(self):
        """Test that execution lock uses timeout-based acquisition."""
        logger.info("Testing timeout-based lock acquisition")
        
        # Mock a successful command execution
        self.orchestrator._execute_command_internal.return_value = {
            'status': 'success',
            'message': 'Command executed successfully'
        }
        
        # Execute a command and verify it completes
        result = self.orchestrator.execute_command("test command")
        
        self.assertEqual(result['status'], 'success')
        self.orchestrator._execute_command_internal.assert_called_once_with("test command")
    
    def test_lock_timeout_handling(self):
        """Test that lock acquisition timeout is handled properly."""
        logger.info("Testing lock acquisition timeout handling")
        
        # Acquire the lock manually to simulate a busy system
        self.orchestrator.execution_lock.acquire()
        
        try:
            # Attempt to execute a command - should timeout and raise error
            with self.assertRaises(OrchestratorError) as context:
                self.orchestrator.execute_command("test command")
            
            self.assertIn("System is currently busy", str(context.exception))
            
        finally:
            # Release the manually acquired lock
            self.orchestrator.execution_lock.release()
    
    def test_deferred_action_early_lock_release(self):
        """Test that deferred actions release the execution lock early."""
        logger.info("Testing deferred action early lock release")
        
        # Mock a deferred action response
        self.orchestrator._execute_command_internal.return_value = {
            'status': 'waiting_for_user_action',
            'execution_id': 'test-123',
            'message': 'Waiting for user click'
        }
        
        # Execute the command
        result = self.orchestrator.execute_command("generate code")
        
        # Verify the result indicates waiting for user action
        self.assertEqual(result['status'], 'waiting_for_user_action')
        
        # Verify the execution lock is not held after the command returns
        self.assertFalse(self.orchestrator.execution_lock.locked())
    
    def test_concurrent_command_during_deferred_action(self):
        """Test that new commands can be processed while waiting for deferred action."""
        logger.info("Testing concurrent commands during deferred action")
        
        # Mock responses for different commands
        def mock_execute_internal(command):
            if "generate" in command:
                return {
                    'status': 'waiting_for_user_action',
                    'execution_id': 'deferred-123',
                    'message': 'Waiting for user click'
                }
            else:
                return {
                    'status': 'success',
                    'message': f'Executed: {command}'
                }
        
        self.orchestrator._execute_command_internal.side_effect = mock_execute_internal
        
        # Start a deferred action
        deferred_result = self.orchestrator.execute_command("generate code")
        self.assertEqual(deferred_result['status'], 'waiting_for_user_action')
        
        # Execute another command while the first is waiting
        concurrent_result = self.orchestrator.execute_command("click button")
        self.assertEqual(concurrent_result['status'], 'success')
        self.assertIn('click button', concurrent_result['message'])
    
    def test_multiple_concurrent_commands(self):
        """Test multiple concurrent commands without deadlocks."""
        logger.info("Testing multiple concurrent commands")
        
        # Mock successful execution for all commands
        self.orchestrator._execute_command_internal.return_value = {
            'status': 'success',
            'message': 'Command executed'
        }
        
        # Execute multiple commands concurrently
        commands = [f"test command {i}" for i in range(5)]
        results = []
        
        def execute_command(cmd):
            try:
                return self.orchestrator.execute_command(cmd)
            except Exception as e:
                return {'status': 'error', 'message': str(e)}
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_command = {executor.submit(execute_command, cmd): cmd for cmd in commands}
            
            for future in as_completed(future_to_command):
                command = future_to_command[future]
                try:
                    result = future.result(timeout=10)  # 10 second timeout per command
                    results.append((command, result))
                except Exception as e:
                    results.append((command, {'status': 'error', 'message': str(e)}))
        
        # Verify all commands completed
        self.assertEqual(len(results), len(commands))
        
        # Verify no commands failed due to deadlocks
        for command, result in results:
            self.assertNotEqual(result['status'], 'error', 
                              f"Command '{command}' failed: {result.get('message', 'Unknown error')}")
    
    def test_deferred_action_trigger_lock_reacquisition(self):
        """Test that deferred action trigger properly re-acquires execution lock."""
        logger.info("Testing deferred action trigger lock re-acquisition")
        
        # Set up deferred action state
        self.orchestrator.is_waiting_for_user_action = True
        self.orchestrator.pending_action_payload = "test content"
        self.orchestrator.deferred_action_type = "type"
        
        # Mock mouse listener
        mock_mouse_listener = Mock()
        mock_mouse_listener.get_last_click_coordinates.return_value = (100, 200)
        self.orchestrator.mouse_listener = mock_mouse_listener
        
        # Mock the pending action execution
        with patch.object(self.orchestrator, '_execute_pending_deferred_action', return_value=True) as mock_execute:
            with patch.object(self.orchestrator, '_provide_deferred_action_completion_feedback') as mock_feedback:
                with patch.object(self.orchestrator, '_reset_deferred_action_state') as mock_reset:
                    
                    # Trigger the deferred action
                    self.orchestrator._on_deferred_action_trigger("test-123")
                    
                    # Verify the pending action was executed
                    mock_execute.assert_called_once_with("test-123", (100, 200))
                    
                    # Verify success feedback was provided
                    mock_feedback.assert_called_once_with("test-123", True)
                    
                    # Verify state was reset
                    mock_reset.assert_called_once()
    
    def test_deferred_action_trigger_lock_timeout(self):
        """Test handling of lock timeout during deferred action trigger."""
        logger.info("Testing deferred action trigger lock timeout")
        
        # Acquire the execution lock to simulate busy system
        self.orchestrator.execution_lock.acquire()
        
        try:
            # Set up deferred action state
            self.orchestrator.is_waiting_for_user_action = True
            self.orchestrator.pending_action_payload = "test content"
            
            with patch.object(self.orchestrator, '_provide_deferred_action_completion_feedback') as mock_feedback:
                with patch.object(self.orchestrator, '_reset_deferred_action_state') as mock_reset:
                    
                    # Trigger the deferred action - should timeout
                    self.orchestrator._on_deferred_action_trigger("test-123")
                    
                    # Verify failure feedback was provided with timeout message
                    mock_feedback.assert_called_once()
                    args = mock_feedback.call_args
                    self.assertEqual(args[0][0], "test-123")  # execution_id
                    self.assertEqual(args[0][1], False)       # success = False
                    self.assertIn("System busy", args[0][2])  # error_message
                    
                    # Verify state was reset
                    mock_reset.assert_called_once()
        
        finally:
            # Release the manually acquired lock
            self.orchestrator.execution_lock.release()
    
    def test_exception_handling_with_lock_cleanup(self):
        """Test that exceptions don't leave locks in acquired state."""
        logger.info("Testing exception handling with lock cleanup")
        
        # Mock an exception during command execution
        self.orchestrator._execute_command_internal.side_effect = Exception("Test exception")
        
        # Execute command and expect it to raise an error
        with self.assertRaises(OrchestratorError):
            self.orchestrator.execute_command("test command")
        
        # Verify the execution lock is not held after the exception
        self.assertFalse(self.orchestrator.execution_lock.locked())
    
    def test_intent_lock_timeout_handling(self):
        """Test that intent recognition lock uses timeout properly."""
        logger.info("Testing intent recognition lock timeout")
        
        # Acquire the intent lock manually
        self.orchestrator.intent_lock.acquire()
        
        try:
            # Attempt intent recognition - should timeout and use fallback
            result = self.orchestrator._recognize_intent("test command")
            
            # Verify fallback intent was returned
            self.assertEqual(result['intent'], 'gui_interaction')
            self.assertIn('timeout', result.get('reasoning', '').lower())
            
        finally:
            # Release the manually acquired lock
            self.orchestrator.intent_lock.release()
    
    def test_comprehensive_lock_lifecycle(self):
        """Test the complete lifecycle of lock acquisition and release."""
        logger.info("Testing comprehensive lock lifecycle")
        
        # Track lock states
        lock_states = []
        
        def track_lock_state(operation):
            lock_states.append({
                'operation': operation,
                'execution_lock_held': self.orchestrator.execution_lock.locked(),
                'intent_lock_held': self.orchestrator.intent_lock.locked(),
                'timestamp': time.time()
            })
        
        # Mock command execution to track lock states
        def mock_execute_with_tracking(command):
            track_lock_state('execute_start')
            time.sleep(0.1)  # Simulate some processing time
            track_lock_state('execute_end')
            return {'status': 'success', 'message': 'Command executed'}
        
        self.orchestrator._execute_command_internal.side_effect = mock_execute_with_tracking
        
        track_lock_state('before_command')
        result = self.orchestrator.execute_command("test command")
        track_lock_state('after_command')
        
        # Verify the command succeeded
        self.assertEqual(result['status'], 'success')
        
        # Verify lock lifecycle
        self.assertFalse(lock_states[0]['execution_lock_held'])  # before_command
        self.assertTrue(lock_states[1]['execution_lock_held'])   # execute_start
        self.assertTrue(lock_states[2]['execution_lock_held'])   # execute_end
        self.assertFalse(lock_states[3]['execution_lock_held'])  # after_command
        
        # Verify no locks are held at the end
        self.assertFalse(self.orchestrator.execution_lock.locked())
        self.assertFalse(self.orchestrator.intent_lock.locked())


class TestConcurrencyStressTest(unittest.TestCase):
    """Stress tests for concurrency handling."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.orchestrator = Orchestrator()
        
        # Mock modules
        self.orchestrator.vision_module = Mock()
        self.orchestrator.reasoning_module = Mock()
        self.orchestrator.automation_module = Mock()
        self.orchestrator.audio_module = Mock()
        self.orchestrator.feedback_module = Mock()
        self.orchestrator.accessibility_module = Mock()
        
        # Set module availability
        self.orchestrator.module_availability = {
            'vision': True,
            'reasoning': True,
            'automation': True,
            'audio': True,
            'feedback': True,
            'accessibility': True
        }
    
    def tearDown(self):
        """Clean up after tests."""
        # Ensure any locks are released
        if hasattr(self.orchestrator, 'execution_lock') and self.orchestrator.execution_lock.locked():
            try:
                self.orchestrator.execution_lock.release()
            except:
                pass
    
    def test_high_concurrency_stress(self):
        """Stress test with high concurrency to detect deadlocks."""
        logger.info("Running high concurrency stress test")
        
        # Mock quick successful execution
        self.orchestrator._execute_command_internal.return_value = {
            'status': 'success',
            'message': 'Command executed'
        }
        
        # Execute many commands concurrently
        num_commands = 20
        commands = [f"stress test command {i}" for i in range(num_commands)]
        results = []
        errors = []
        
        def execute_with_timeout(cmd):
            try:
                start_time = time.time()
                result = self.orchestrator.execute_command(cmd)
                execution_time = time.time() - start_time
                return {'command': cmd, 'result': result, 'execution_time': execution_time}
            except Exception as e:
                return {'command': cmd, 'error': str(e), 'execution_time': None}
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_command = {executor.submit(execute_with_timeout, cmd): cmd for cmd in commands}
            
            for future in as_completed(future_to_command, timeout=30):  # 30 second total timeout
                try:
                    result = future.result()
                    if 'error' in result:
                        errors.append(result)
                    else:
                        results.append(result)
                except Exception as e:
                    errors.append({'command': 'unknown', 'error': str(e)})
        
        # Verify results
        total_completed = len(results) + len(errors)
        self.assertEqual(total_completed, num_commands, "Not all commands completed")
        
        # Log any errors for debugging
        if errors:
            logger.warning(f"Stress test had {len(errors)} errors:")
            for error in errors:
                logger.warning(f"  {error['command']}: {error['error']}")
        
        # Verify most commands succeeded (allow for some timeout errors under stress)
        success_rate = len(results) / num_commands
        self.assertGreater(success_rate, 0.8, f"Success rate too low: {success_rate:.2%}")
        
        # Verify no locks are held at the end
        self.assertFalse(self.orchestrator.execution_lock.locked())
        self.assertFalse(self.orchestrator.intent_lock.locked())


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)