#!/usr/bin/env python3
"""
Focused test for Task 0.1: Test only the lock behavior changes

This test focuses specifically on the lock management behavior without triggering actual automation.
"""

import threading
import time
import logging
from unittest.mock import patch, Mock

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_lock_behavior():
    """Test that the lock management changes work correctly."""
    
    print("=" * 60)
    print("TESTING TASK 0.1: LOCK BEHAVIOR CHANGES")
    print("=" * 60)
    
    # Import after setting up logging
    from orchestrator import Orchestrator
    
    # Create orchestrator instance with minimal initialization
    orchestrator = Orchestrator()
    
    # Test 1: Verify execute_command releases lock for deferred actions
    print("\n1. Testing execute_command lock release for deferred actions...")
    
    # Mock the internal method to return a deferred action result
    def mock_execute_internal(command):
        return {
            'status': 'waiting_for_user_action',
            'execution_id': 'test_123',
            'message': 'Waiting for user click'
        }
    
    with patch.object(orchestrator, '_execute_command_internal', side_effect=mock_execute_internal):
        try:
            result = orchestrator.execute_command("test command")
            
            # Verify the result indicates waiting state
            if result.get('status') == 'waiting_for_user_action':
                print("✓ Command returned waiting_for_user_action status")
            else:
                print(f"✗ Command returned unexpected status: {result.get('status')}")
                return False
            
            # Verify lock was released
            if not orchestrator.execution_lock.locked():
                print("✓ Execution lock was released for deferred action")
            else:
                print("✗ Execution lock was NOT released for deferred action")
                return False
                
        except Exception as e:
            print(f"✗ Error in execute_command test: {e}")
            return False
    
    # Test 2: Test _on_deferred_action_trigger lock acquisition
    print("\n2. Testing _on_deferred_action_trigger lock acquisition...")
    
    # Set up deferred action state
    orchestrator.is_waiting_for_user_action = True
    orchestrator.pending_action_payload = "test content"
    orchestrator.deferred_action_type = "type"
    
    # Mock the actual execution methods to avoid real automation
    with patch.object(orchestrator, '_execute_pending_deferred_action', return_value=True), \
         patch.object(orchestrator, '_provide_deferred_action_completion_feedback'), \
         patch.object(orchestrator, '_reset_deferred_action_state'):
        
        # Ensure lock is not held initially
        if orchestrator.execution_lock.locked():
            orchestrator.execution_lock.release()
        
        # Track lock states
        lock_states = []
        
        # Mock the lock to track acquire/release calls
        original_acquire = orchestrator.execution_lock.acquire
        original_release = orchestrator.execution_lock.release
        
        def track_acquire(*args, **kwargs):
            lock_states.append('acquired')
            return original_acquire(*args, **kwargs)
        
        def track_release(*args, **kwargs):
            lock_states.append('released')
            return original_release(*args, **kwargs)
        
        with patch.object(orchestrator.execution_lock, 'acquire', side_effect=track_acquire), \
             patch.object(orchestrator.execution_lock, 'release', side_effect=track_release):
            
            try:
                orchestrator._on_deferred_action_trigger("test_execution_id")
                
                # Check that lock was acquired and then released
                if 'acquired' in lock_states and 'released' in lock_states:
                    print("✓ Lock was acquired and released in deferred action trigger")
                else:
                    print(f"✗ Lock states not as expected: {lock_states}")
                    return False
                
                # Verify final state - lock should be released
                if not orchestrator.execution_lock.locked():
                    print("✓ Lock is released after deferred action trigger")
                else:
                    print("✗ Lock is still held after deferred action trigger")
                    return False
                    
            except Exception as e:
                print(f"✗ Error in deferred action trigger test: {e}")
                return False
    
    # Test 3: Test concurrent command execution
    print("\n3. Testing concurrent command execution...")
    
    def mock_execute_internal_normal(command):
        time.sleep(0.1)  # Simulate some processing time
        return {
            'status': 'completed',
            'execution_id': 'test_456',
            'message': 'Command completed'
        }
    
    results = {'commands_completed': 0, 'errors': []}
    
    def run_command(cmd_id):
        try:
            with patch.object(orchestrator, '_execute_command_internal', side_effect=mock_execute_internal_normal):
                result = orchestrator.execute_command(f"test command {cmd_id}")
                if result.get('status') == 'completed':
                    results['commands_completed'] += 1
        except Exception as e:
            results['errors'].append(str(e))
    
    # Run multiple commands concurrently
    threads = []
    for i in range(3):
        thread = threading.Thread(target=run_command, args=(i,))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join(timeout=5.0)
    
    if results['commands_completed'] == 3 and len(results['errors']) == 0:
        print("✓ Concurrent commands executed successfully")
    else:
        print(f"✗ Concurrent execution failed: {results['commands_completed']} completed, {len(results['errors'])} errors")
        for error in results['errors']:
            print(f"   Error: {error}")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 ALL LOCK BEHAVIOR TESTS PASSED!")
    print("✓ execute_command releases lock for deferred actions")
    print("✓ _on_deferred_action_trigger acquires and releases lock properly")
    print("✓ Concurrent command execution works correctly")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = test_lock_behavior()
    if not success:
        print("\n❌ LOCK BEHAVIOR TESTS FAILED")
        exit(1)
    else:
        print("\n✅ LOCK BEHAVIOR TESTS PASSED - CONCURRENCY FIX WORKING!")
        exit(0)