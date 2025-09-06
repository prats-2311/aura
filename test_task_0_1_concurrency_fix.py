#!/usr/bin/env python3
"""
Test script for Task 0.1: Fix Concurrency Deadlock in Deferred Actions

This test verifies that the concurrency deadlock fix works properly by:
1. Starting a deferred action that enters waiting state
2. Issuing a new command while the deferred action is waiting
3. Verifying that the new command can be processed without deadlock
4. Ensuring proper lock management throughout the process
"""

import threading
import time
import logging
from unittest.mock import Mock, patch
from orchestrator import Orchestrator

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_concurrency_fix():
    """Test that the concurrency deadlock fix works properly."""
    
    print("=" * 60)
    print("TESTING TASK 0.1: CONCURRENCY DEADLOCK FIX")
    print("=" * 60)
    
    # Create orchestrator instance
    orchestrator = Orchestrator()
    
    # Mock the modules to avoid actual GUI interactions
    orchestrator.reasoning_module = Mock()
    orchestrator.automation_module = Mock()
    orchestrator.vision_module = Mock()
    orchestrator.audio_module = Mock()
    orchestrator.feedback_module = Mock()
    orchestrator.accessibility_module = Mock()
    
    # Mock the mouse listener to avoid actual mouse events
    mock_mouse_listener = Mock()
    mock_mouse_listener.get_last_click_coordinates.return_value = (100, 100)
    
    # Test results tracking
    test_results = {
        'deferred_action_started': False,
        'deferred_action_waiting': False,
        'new_command_processed': False,
        'deadlock_occurred': False,
        'lock_properly_managed': True
    }
    
    def mock_deferred_action_command():
        """Simulate a deferred action command that should enter waiting state."""
        try:
            # Mock reasoning module to return deferred action intent
            orchestrator.reasoning_module.get_response.return_value = {
                'intent': 'deferred_action',
                'confidence': 0.9,
                'content_request': 'generate some code',
                'action_type': 'type'
            }
            
            # Mock content generation
            orchestrator.reasoning_module.get_response.side_effect = [
                # First call for intent recognition
                {
                    'intent': 'deferred_action',
                    'confidence': 0.9,
                    'content_request': 'generate some code',
                    'action_type': 'type'
                },
                # Second call for content generation
                'def hello_world():\n    print("Hello, World!")'
            ]
            
            logger.info("Starting deferred action command...")
            result = orchestrator.execute_command("generate a hello world function")
            
            test_results['deferred_action_started'] = True
            
            if result.get('status') == 'waiting_for_user_action':
                test_results['deferred_action_waiting'] = True
                logger.info("✓ Deferred action entered waiting state successfully")
                
                # Verify that execution lock was released
                if not orchestrator.execution_lock.locked():
                    logger.info("✓ Execution lock was properly released during waiting state")
                else:
                    logger.error("✗ Execution lock was NOT released during waiting state")
                    test_results['lock_properly_managed'] = False
            else:
                logger.error(f"✗ Deferred action did not enter waiting state. Status: {result.get('status')}")
                
        except Exception as e:
            logger.error(f"✗ Error in deferred action command: {e}")
            test_results['deadlock_occurred'] = True
    
    def mock_new_command():
        """Simulate a new command issued while deferred action is waiting."""
        try:
            # Wait a bit to ensure deferred action is in waiting state
            time.sleep(1)
            
            # Mock reasoning module for new command
            orchestrator.reasoning_module.get_response.return_value = {
                'intent': 'gui_interaction',
                'confidence': 0.8,
                'action': 'click',
                'target': 'button'
            }
            
            logger.info("Starting new command while deferred action is waiting...")
            
            # This should NOT deadlock
            start_time = time.time()
            result = orchestrator.execute_command("click the submit button")
            end_time = time.time()
            
            # If this takes more than 10 seconds, we likely have a deadlock
            if end_time - start_time > 10:
                logger.error("✗ New command took too long - possible deadlock")
                test_results['deadlock_occurred'] = True
            else:
                test_results['new_command_processed'] = True
                logger.info("✓ New command processed successfully without deadlock")
                
        except Exception as e:
            logger.error(f"✗ Error in new command: {e}")
            test_results['deadlock_occurred'] = True
    
    # Start deferred action in a separate thread
    deferred_thread = threading.Thread(target=mock_deferred_action_command)
    deferred_thread.daemon = True
    deferred_thread.start()
    
    # Wait for deferred action to start
    time.sleep(0.5)
    
    # Start new command in another thread
    new_command_thread = threading.Thread(target=mock_new_command)
    new_command_thread.daemon = True
    new_command_thread.start()
    
    # Wait for both threads to complete (with timeout to detect deadlock)
    deferred_thread.join(timeout=15)
    new_command_thread.join(timeout=15)
    
    # Check if threads are still alive (indicating possible deadlock)
    if deferred_thread.is_alive() or new_command_thread.is_alive():
        logger.error("✗ Threads did not complete - possible deadlock detected")
        test_results['deadlock_occurred'] = True
    
    # Test deferred action trigger (simulate user click)
    if test_results['deferred_action_waiting']:
        try:
            logger.info("Simulating user click to trigger deferred action...")
            orchestrator.mouse_listener = mock_mouse_listener
            orchestrator._on_deferred_action_trigger("test_execution_id")
            logger.info("✓ Deferred action trigger completed successfully")
            
            # Verify lock is released after trigger
            if not orchestrator.execution_lock.locked():
                logger.info("✓ Execution lock properly released after deferred action completion")
            else:
                logger.error("✗ Execution lock NOT released after deferred action completion")
                test_results['lock_properly_managed'] = False
                
        except Exception as e:
            logger.error(f"✗ Error in deferred action trigger: {e}")
    
    # Print test results
    print("\n" + "=" * 60)
    print("TEST RESULTS:")
    print("=" * 60)
    
    all_passed = True
    
    if test_results['deferred_action_started']:
        print("✓ Deferred action started successfully")
    else:
        print("✗ Deferred action failed to start")
        all_passed = False
    
    if test_results['deferred_action_waiting']:
        print("✓ Deferred action entered waiting state")
    else:
        print("✗ Deferred action did not enter waiting state")
        all_passed = False
    
    if test_results['new_command_processed']:
        print("✓ New command processed without deadlock")
    else:
        print("✗ New command was not processed or deadlocked")
        all_passed = False
    
    if not test_results['deadlock_occurred']:
        print("✓ No deadlock detected")
    else:
        print("✗ Deadlock occurred")
        all_passed = False
    
    if test_results['lock_properly_managed']:
        print("✓ Execution lock properly managed")
    else:
        print("✗ Execution lock not properly managed")
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED - CONCURRENCY FIX WORKING!")
    else:
        print("❌ SOME TESTS FAILED - CONCURRENCY ISSUES REMAIN")
    print("=" * 60)
    
    return all_passed

if __name__ == "__main__":
    test_concurrency_fix()