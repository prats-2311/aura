#!/usr/bin/env python3
"""
Thread safety and state management tests for conversational AURA enhancement.

This test suite validates:
- Thread-safe state access and modification
- Proper cleanup and resource management
- State consistency under concurrent access
- Lock behavior and deadlock prevention
- State validation and recovery

Requirements tested: 8.3, 8.4, 9.3, 9.4
"""

import pytest
import sys
import os
import time
import threading
import concurrent.futures
from unittest.mock import Mock, patch, MagicMock

# Add the parent directory to the path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator import Orchestrator


class TestStateManagementThreadSafety:
    """Test thread safety of state management operations."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.orchestrator = Orchestrator()
        
        # Mock modules to avoid external dependencies
        self.orchestrator.reasoning_module = Mock()
        self.orchestrator.feedback_module = Mock()
        self.orchestrator.audio_module = Mock()
        self.orchestrator.automation_module = Mock()
        
        # Set modules as available
        self.orchestrator.module_availability = {
            'reasoning': True,
            'feedback': True,
            'audio': True,
            'automation': True,
            'vision': True,
            'accessibility': True
        }
    
    def test_concurrent_state_modification(self):
        """Test concurrent modification of deferred action state."""
        results = []
        errors = []
        num_threads = 10
        operations_per_thread = 20
        
        def state_modifier_thread(thread_id):
            """Thread function that modifies state concurrently."""
            try:
                for i in range(operations_per_thread):
                    # Simulate deferred action state changes
                    with self.orchestrator.deferred_action_lock:
                        # Set state
                        self.orchestrator.is_waiting_for_user_action = True
                        self.orchestrator.pending_action_payload = f"content_{thread_id}_{i}"
                        self.orchestrator.deferred_action_type = "type"
                        self.orchestrator.system_mode = 'waiting_for_user'
                        
                        # Small delay to increase chance of race conditions
                        time.sleep(0.001)
                        
                        # Verify state consistency within lock
                        if self.orchestrator.is_waiting_for_user_action:
                            assert self.orchestrator.pending_action_payload is not None, \
                                f"Thread {thread_id}: Inconsistent state - waiting but no payload"
                            assert self.orchestrator.system_mode == 'waiting_for_user', \
                                f"Thread {thread_id}: Inconsistent state - waiting but wrong mode"
                        
                        # Reset state
                        self.orchestrator._reset_deferred_action_state()
                        
                        # Verify reset
                        assert self.orchestrator.is_waiting_for_user_action is False, \
                            f"Thread {thread_id}: State not properly reset"
                        assert self.orchestrator.pending_action_payload is None, \
                            f"Thread {thread_id}: Payload not cleared"
                    
                    # Small delay between operations
                    time.sleep(0.0001)
                
                results.append(f"Thread {thread_id} completed successfully")
                
            except Exception as e:
                errors.append(f"Thread {thread_id} error: {e}")
        
        # Start multiple threads
        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=state_modifier_thread, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=10.0)
            if thread.is_alive():
                errors.append(f"Thread {thread.name} did not complete in time")
        
        # Verify results
        assert len(errors) == 0, f"Thread safety errors occurred: {errors}"
        assert len(results) == num_threads, f"Expected {num_threads} successful completions, got {len(results)}"
        
        # Verify final state is consistent
        validation_result = self.orchestrator.validate_system_state()
        assert validation_result['is_valid'] is True, f"Final state inconsistent: {validation_result['issues']}"
    
    def test_concurrent_conversation_history_access(self):
        """Test concurrent access to conversation history."""
        results = []
        errors = []
        num_threads = 8
        entries_per_thread = 15
        
        def conversation_thread(thread_id):
            """Thread function that modifies conversation history."""
            try:
                for i in range(entries_per_thread):
                    user_input = f"User message {thread_id}-{i}"
                    assistant_response = f"Assistant response {thread_id}-{i}"
                    
                    # Use conversation lock for thread safety
                    with self.orchestrator.conversation_lock:
                        initial_length = len(self.orchestrator.conversation_history)
                        
                        # Add conversation entry
                        self.orchestrator._update_conversation_history(user_input, assistant_response)
                        
                        # Verify addition
                        new_length = len(self.orchestrator.conversation_history)
                        assert new_length == initial_length + 1, \
                            f"Thread {thread_id}: History length not incremented correctly"
                        
                        # Verify latest entry
                        latest_entry = self.orchestrator.conversation_history[-1]
                        assert latest_entry == (user_input, assistant_response), \
                            f"Thread {thread_id}: Latest entry incorrect"
                    
                    time.sleep(0.0001)  # Small delay
                
                results.append(f"Conversation thread {thread_id} completed")
                
            except Exception as e:
                errors.append(f"Conversation thread {thread_id} error: {e}")
        
        # Start threads
        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=conversation_thread, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join(timeout=5.0)
        
        # Verify results
        assert len(errors) == 0, f"Conversation history errors: {errors}"
        assert len(results) == num_threads, "All conversation threads should complete"
        
        # Verify total entries
        expected_total = num_threads * entries_per_thread
        actual_total = len(self.orchestrator.conversation_history)
        assert actual_total == expected_total, \
            f"Expected {expected_total} conversation entries, got {actual_total}"
    
    def test_concurrent_state_validation(self):
        """Test concurrent state validation operations."""
        results = []
        errors = []
        num_threads = 6
        validations_per_thread = 25
        
        def validation_thread(thread_id):
            """Thread function that performs state validation."""
            try:
                for i in range(validations_per_thread):
                    # Perform state validation
                    validation_result = self.orchestrator.validate_system_state()
                    
                    # Validation should always succeed for clean state
                    assert validation_result['is_valid'] is True, \
                        f"Thread {thread_id}: Validation failed: {validation_result['issues']}"
                    
                    # Test state diagnostics
                    diagnostics = self.orchestrator.get_state_diagnostics()
                    assert 'timestamp' in diagnostics, f"Thread {thread_id}: Missing timestamp in diagnostics"
                    assert 'state_summary' in diagnostics, f"Thread {thread_id}: Missing state summary"
                    
                    time.sleep(0.0001)
                
                results.append(f"Validation thread {thread_id} completed")
                
            except Exception as e:
                errors.append(f"Validation thread {thread_id} error: {e}")
        
        # Start validation threads
        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=validation_thread, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join(timeout=5.0)
        
        # Verify results
        assert len(errors) == 0, f"State validation errors: {errors}"
        assert len(results) == num_threads, "All validation threads should complete"
    
    def test_mixed_concurrent_operations(self):
        """Test mixed concurrent operations on different state components."""
        results = []
        errors = []
        
        def deferred_action_operations(thread_id):
            """Perform deferred action state operations."""
            try:
                for i in range(10):
                    with self.orchestrator.deferred_action_lock:
                        self.orchestrator.is_waiting_for_user_action = True
                        self.orchestrator.pending_action_payload = f"payload_{thread_id}_{i}"
                        time.sleep(0.001)
                        self.orchestrator._reset_deferred_action_state()
                    time.sleep(0.0001)
                results.append(f"Deferred action thread {thread_id} completed")
            except Exception as e:
                errors.append(f"Deferred action thread {thread_id} error: {e}")
        
        def conversation_operations(thread_id):
            """Perform conversation history operations."""
            try:
                for i in range(10):
                    with self.orchestrator.conversation_lock:
                        self.orchestrator._update_conversation_history(
                            f"User {thread_id}-{i}",
                            f"Assistant {thread_id}-{i}"
                        )
                    time.sleep(0.0001)
                results.append(f"Conversation thread {thread_id} completed")
            except Exception as e:
                errors.append(f"Conversation thread {thread_id} error: {e}")
        
        def validation_operations(thread_id):
            """Perform validation operations."""
            try:
                for i in range(15):
                    validation_result = self.orchestrator.validate_system_state()
                    assert validation_result is not None, f"Validation thread {thread_id}: Null result"
                    time.sleep(0.0001)
                results.append(f"Validation thread {thread_id} completed")
            except Exception as e:
                errors.append(f"Validation thread {thread_id} error: {e}")
        
        def state_transition_operations(thread_id):
            """Perform state transition recording."""
            try:
                for i in range(12):
                    self.orchestrator._record_state_transition(
                        f'test_transition_{thread_id}_{i}',
                        {'thread_id': thread_id, 'iteration': i}
                    )
                    time.sleep(0.0001)
                results.append(f"State transition thread {thread_id} completed")
            except Exception as e:
                errors.append(f"State transition thread {thread_id} error: {e}")
        
        # Start mixed operation threads
        threads = []
        
        # 2 deferred action threads
        for i in range(2):
            thread = threading.Thread(target=deferred_action_operations, args=(f"da_{i}",))
            threads.append(thread)
        
        # 2 conversation threads
        for i in range(2):
            thread = threading.Thread(target=conversation_operations, args=(f"conv_{i}",))
            threads.append(thread)
        
        # 2 validation threads
        for i in range(2):
            thread = threading.Thread(target=validation_operations, args=(f"val_{i}",))
            threads.append(thread)
        
        # 2 state transition threads
        for i in range(2):
            thread = threading.Thread(target=state_transition_operations, args=(f"st_{i}",))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join(timeout=10.0)
        
        # Verify results
        assert len(errors) == 0, f"Mixed operation errors: {errors}"
        assert len(results) == 8, f"Expected 8 completed operations, got {len(results)}"
        
        # Verify final state consistency
        validation_result = self.orchestrator.validate_system_state()
        assert validation_result['is_valid'] is True, "Final state should be consistent after mixed operations"
    
    def test_deadlock_prevention(self):
        """Test that lock ordering prevents deadlocks."""
        results = []
        errors = []
        
        def lock_order_thread_1(thread_id):
            """Thread that acquires locks in order: deferred_action -> conversation."""
            try:
                for i in range(5):
                    with self.orchestrator.deferred_action_lock:
                        time.sleep(0.01)  # Hold lock for a bit
                        with self.orchestrator.conversation_lock:
                            # Do some work
                            self.orchestrator.is_waiting_for_user_action = True
                            self.orchestrator._update_conversation_history(f"User {thread_id}-{i}", f"Response {thread_id}-{i}")
                            time.sleep(0.01)
                            self.orchestrator._reset_deferred_action_state()
                    time.sleep(0.001)
                results.append(f"Lock order thread 1-{thread_id} completed")
            except Exception as e:
                errors.append(f"Lock order thread 1-{thread_id} error: {e}")
        
        def lock_order_thread_2(thread_id):
            """Thread that acquires locks in same order: deferred_action -> conversation."""
            try:
                for i in range(5):
                    with self.orchestrator.deferred_action_lock:
                        time.sleep(0.01)  # Hold lock for a bit
                        with self.orchestrator.conversation_lock:
                            # Do some work
                            self.orchestrator.pending_action_payload = f"payload_{thread_id}_{i}"
                            self.orchestrator._update_conversation_history(f"User2 {thread_id}-{i}", f"Response2 {thread_id}-{i}")
                            time.sleep(0.01)
                            self.orchestrator._reset_deferred_action_state()
                    time.sleep(0.001)
                results.append(f"Lock order thread 2-{thread_id} completed")
            except Exception as e:
                errors.append(f"Lock order thread 2-{thread_id} error: {e}")
        
        # Start threads that could potentially deadlock if lock ordering is wrong
        threads = []
        
        for i in range(3):
            thread1 = threading.Thread(target=lock_order_thread_1, args=(i,))
            thread2 = threading.Thread(target=lock_order_thread_2, args=(i,))
            threads.extend([thread1, thread2])
        
        # Start all threads simultaneously
        for thread in threads:
            thread.start()
        
        # Wait for completion with timeout to detect deadlocks
        for thread in threads:
            thread.join(timeout=15.0)  # Generous timeout
            if thread.is_alive():
                errors.append(f"Thread {thread.name} appears to be deadlocked")
        
        # Verify no deadlocks occurred
        assert len(errors) == 0, f"Deadlock or other errors detected: {errors}"
        assert len(results) == 6, f"Expected 6 completed threads, got {len(results)}"
    
    def test_resource_cleanup_thread_safety(self):
        """Test thread-safe resource cleanup operations."""
        results = []
        errors = []
        
        def cleanup_thread(thread_id):
            """Thread that performs cleanup operations."""
            try:
                for i in range(8):
                    # Set up some state
                    with self.orchestrator.deferred_action_lock:
                        self.orchestrator.is_waiting_for_user_action = True
                        self.orchestrator.pending_action_payload = f"cleanup_test_{thread_id}_{i}"
                        self.orchestrator.deferred_action_type = "type"
                        
                        # Mock mouse listener
                        mock_listener = Mock()
                        mock_listener.is_active.return_value = True
                        self.orchestrator.mouse_listener = mock_listener
                        self.orchestrator.mouse_listener_active = True
                        
                        # Perform cleanup
                        self.orchestrator._reset_deferred_action_state()
                        
                        # Verify cleanup
                        assert self.orchestrator.is_waiting_for_user_action is False, \
                            f"Thread {thread_id}: Cleanup failed - still waiting"
                        assert self.orchestrator.pending_action_payload is None, \
                            f"Thread {thread_id}: Cleanup failed - payload not cleared"
                        assert self.orchestrator.mouse_listener is None, \
                            f"Thread {thread_id}: Cleanup failed - mouse listener not cleared"
                        
                        # Verify mock was called
                        mock_listener.stop.assert_called()
                    
                    time.sleep(0.001)
                
                results.append(f"Cleanup thread {thread_id} completed")
                
            except Exception as e:
                errors.append(f"Cleanup thread {thread_id} error: {e}")
        
        # Start cleanup threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=cleanup_thread, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join(timeout=5.0)
        
        # Verify results
        assert len(errors) == 0, f"Cleanup thread safety errors: {errors}"
        assert len(results) == 5, "All cleanup threads should complete"
    
    def test_state_consistency_under_load(self):
        """Test state consistency under high concurrent load."""
        results = []
        errors = []
        consistency_checks = []
        
        def high_load_operations(thread_id):
            """Perform high-frequency state operations."""
            try:
                for i in range(50):  # High frequency operations
                    # Rapid state changes
                    with self.orchestrator.deferred_action_lock:
                        self.orchestrator.is_waiting_for_user_action = True
                        self.orchestrator.pending_action_payload = f"load_test_{thread_id}_{i}"
                        self.orchestrator.system_mode = 'waiting_for_user'
                        
                        # Verify consistency
                        if self.orchestrator.is_waiting_for_user_action:
                            assert self.orchestrator.pending_action_payload is not None, \
                                f"Thread {thread_id}: Inconsistent state at iteration {i}"
                        
                        # Reset
                        self.orchestrator._reset_deferred_action_state()
                    
                    # No delay - maximum load
                
                results.append(f"High load thread {thread_id} completed")
                
            except Exception as e:
                errors.append(f"High load thread {thread_id} error: {e}")
        
        def consistency_checker(checker_id):
            """Continuously check state consistency."""
            try:
                for i in range(100):  # Many consistency checks
                    validation_result = self.orchestrator.validate_system_state()
                    consistency_checks.append(validation_result['is_valid'])
                    
                    if not validation_result['is_valid']:
                        errors.append(f"Consistency checker {checker_id}: State inconsistent at check {i}: {validation_result['issues']}")
                    
                    time.sleep(0.0001)  # Brief pause
                
                results.append(f"Consistency checker {checker_id} completed")
                
            except Exception as e:
                errors.append(f"Consistency checker {checker_id} error: {e}")
        
        # Start high load threads
        threads = []
        
        # 8 high-load operation threads
        for i in range(8):
            thread = threading.Thread(target=high_load_operations, args=(i,))
            threads.append(thread)
        
        # 2 consistency checker threads
        for i in range(2):
            thread = threading.Thread(target=consistency_checker, args=(i,))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join(timeout=15.0)
        
        # Verify results
        assert len(errors) == 0, f"High load errors: {errors}"
        assert len(results) == 10, f"Expected 10 completed threads, got {len(results)}"
        
        # Verify consistency checks
        total_checks = len(consistency_checks)
        valid_checks = sum(consistency_checks)
        consistency_rate = valid_checks / total_checks if total_checks > 0 else 0
        
        assert consistency_rate == 1.0, f"State consistency rate should be 100%, got {consistency_rate:.2%}"
        assert total_checks > 0, "Should have performed consistency checks"


class TestStateManagementCleanup:
    """Test proper cleanup and resource management."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.orchestrator = Orchestrator()
    
    def test_comprehensive_state_reset(self):
        """Test comprehensive state reset functionality."""
        # Set up complex state
        self.orchestrator.is_waiting_for_user_action = True
        self.orchestrator.pending_action_payload = "test content"
        self.orchestrator.deferred_action_type = "type"
        self.orchestrator.deferred_action_start_time = time.time()
        self.orchestrator.deferred_action_timeout_time = time.time() + 300
        self.orchestrator.system_mode = 'waiting_for_user'
        self.orchestrator.current_execution_id = "test_123"
        self.orchestrator.mouse_listener_active = True
        
        # Mock mouse listener
        mock_listener = Mock()
        mock_listener.is_active.return_value = True
        self.orchestrator.mouse_listener = mock_listener
        
        # Add some conversation history
        self.orchestrator.conversation_history.append(("test user", "test response"))
        
        # Add state transitions
        self.orchestrator.state_transition_history.append({
            'timestamp': time.time(),
            'transition_type': 'test_transition',
            'context': {'test': 'data'}
        })
        
        # Perform comprehensive reset
        self.orchestrator._reset_deferred_action_state()
        
        # Verify all deferred action state is reset
        assert self.orchestrator.is_waiting_for_user_action is False, "Should not be waiting"
        assert self.orchestrator.pending_action_payload is None, "Payload should be cleared"
        assert self.orchestrator.deferred_action_type is None, "Action type should be cleared"
        assert self.orchestrator.deferred_action_start_time is None, "Start time should be cleared"
        assert self.orchestrator.deferred_action_timeout_time is None, "Timeout time should be cleared"
        assert self.orchestrator.mouse_listener is None, "Mouse listener should be cleared"
        assert self.orchestrator.mouse_listener_active is False, "Mouse listener should not be active"
        assert self.orchestrator.system_mode == 'ready', "Should return to ready mode"
        
        # Verify mouse listener was stopped
        mock_listener.stop.assert_called_once()
        
        # Verify other state is preserved (conversation history, transitions)
        assert len(self.orchestrator.conversation_history) > 0, "Conversation history should be preserved"
        assert len(self.orchestrator.state_transition_history) > 0, "State transitions should be preserved"
    
    def test_resource_cleanup_with_exceptions(self):
        """Test resource cleanup when exceptions occur."""
        # Set up state with mock listener that raises exception on stop
        mock_listener = Mock()
        mock_listener.stop.side_effect = Exception("Stop failed")
        mock_listener.is_active.return_value = True
        
        self.orchestrator.is_waiting_for_user_action = True
        self.orchestrator.pending_action_payload = "test"
        self.orchestrator.mouse_listener = mock_listener
        self.orchestrator.mouse_listener_active = True
        
        # Reset should handle exception gracefully
        self.orchestrator._reset_deferred_action_state()
        
        # State should still be reset despite exception
        assert self.orchestrator.is_waiting_for_user_action is False, "Should reset despite exception"
        assert self.orchestrator.pending_action_payload is None, "Should clear payload despite exception"
        assert self.orchestrator.mouse_listener is None, "Should clear listener despite exception"
        assert self.orchestrator.mouse_listener_active is False, "Should deactivate despite exception"
    
    def test_memory_cleanup_conversation_history(self):
        """Test memory cleanup for conversation history."""
        # Fill conversation history beyond limit
        max_entries = self.orchestrator.max_state_history_entries
        
        # Add more entries than the limit
        for i in range(max_entries + 20):
            self.orchestrator._update_conversation_history(f"User {i}", f"Response {i}")
        
        # Should not exceed the maximum
        assert len(self.orchestrator.conversation_history) <= max_entries, \
            f"Conversation history should not exceed {max_entries} entries"
        
        # Should keep the most recent entries
        latest_entry = self.orchestrator.conversation_history[-1]
        assert f"User {max_entries + 19}" in latest_entry[0], "Should keep most recent entries"
    
    def test_state_transition_history_cleanup(self):
        """Test cleanup of state transition history."""
        # Add many state transitions
        max_entries = self.orchestrator.max_state_history_entries
        
        for i in range(max_entries + 15):
            self.orchestrator._record_state_transition(f'transition_{i}', {'index': i})
        
        # Should not exceed maximum
        assert len(self.orchestrator.state_transition_history) <= max_entries, \
            f"State transition history should not exceed {max_entries} entries"
        
        # Should keep most recent transitions
        latest_transition = self.orchestrator.state_transition_history[-1]
        assert latest_transition['transition_type'] == f'transition_{max_entries + 14}', \
            "Should keep most recent transitions"


if __name__ == '__main__':
    # Run the thread safety and state management tests
    pytest.main([__file__, '-v', '--tb=short'])