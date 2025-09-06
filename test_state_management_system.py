#!/usr/bin/env python3
"""
Test script for the enhanced state management and cleanup system.

This script tests the comprehensive state management implementation including:
- State variable management and validation
- Mouse listener cleanup and resource management
- State consistency checking
- Timeout handling
- State transition recording
"""

import sys
import time
import threading
from unittest.mock import Mock, patch

# Add the project root to the path
sys.path.insert(0, '.')

from orchestrator import Orchestrator


def test_state_management_initialization():
    """Test that state management variables are properly initialized."""
    print("Testing state management initialization...")
    
    orchestrator = Orchestrator()
    
    # Check that all new state variables are initialized
    assert hasattr(orchestrator, 'system_mode'), "system_mode not initialized"
    assert orchestrator.system_mode == 'ready', f"Expected system_mode 'ready', got '{orchestrator.system_mode}'"
    
    assert hasattr(orchestrator, 'deferred_action_timeout_time'), "deferred_action_timeout_time not initialized"
    assert orchestrator.deferred_action_timeout_time is None, "deferred_action_timeout_time should be None initially"
    
    assert hasattr(orchestrator, 'mouse_listener_active'), "mouse_listener_active not initialized"
    assert orchestrator.mouse_listener_active is False, "mouse_listener_active should be False initially"
    
    assert hasattr(orchestrator, 'state_transition_history'), "state_transition_history not initialized"
    assert isinstance(orchestrator.state_transition_history, list), "state_transition_history should be a list"
    
    assert hasattr(orchestrator, 'state_validation_lock'), "state_validation_lock not initialized"
    assert hasattr(orchestrator.state_validation_lock, 'acquire'), "state_validation_lock should be a Lock-like object"
    
    print("✓ State management initialization test passed")


def test_reset_deferred_action_state():
    """Test the enhanced _reset_deferred_action_state method."""
    print("Testing enhanced deferred action state reset...")
    
    orchestrator = Orchestrator()
    
    # Set up some deferred action state
    orchestrator.is_waiting_for_user_action = True
    orchestrator.pending_action_payload = "test content"
    orchestrator.deferred_action_type = "type"
    orchestrator.deferred_action_start_time = time.time()
    orchestrator.deferred_action_timeout_time = time.time() + 300
    orchestrator.system_mode = 'waiting_for_user'
    orchestrator.current_execution_id = "test_123"
    orchestrator.mouse_listener_active = True
    
    # Mock mouse listener
    mock_listener = Mock()
    mock_listener.is_active.return_value = True
    orchestrator.mouse_listener = mock_listener
    
    # Reset the state
    orchestrator._reset_deferred_action_state()
    
    # Verify all state variables are reset
    assert orchestrator.is_waiting_for_user_action is False, "is_waiting_for_user_action not reset"
    assert orchestrator.pending_action_payload is None, "pending_action_payload not reset"
    assert orchestrator.deferred_action_type is None, "deferred_action_type not reset"
    assert orchestrator.deferred_action_start_time is None, "deferred_action_start_time not reset"
    assert orchestrator.deferred_action_timeout_time is None, "deferred_action_timeout_time not reset"
    assert orchestrator.mouse_listener is None, "mouse_listener not reset"
    assert orchestrator.mouse_listener_active is False, "mouse_listener_active not reset"
    assert orchestrator.system_mode == 'ready', f"Expected system_mode 'ready', got '{orchestrator.system_mode}'"
    
    # Verify mouse listener was stopped
    mock_listener.stop.assert_called_once()
    
    print("✓ Enhanced deferred action state reset test passed")


def test_state_validation():
    """Test the state validation functionality."""
    print("Testing state validation...")
    
    orchestrator = Orchestrator()
    
    # Test validation with clean state
    validation_result = orchestrator.validate_system_state()
    assert validation_result['is_valid'] is True, "Clean state should be valid"
    assert len(validation_result['issues']) == 0, "Clean state should have no issues"
    
    # Test validation with inconsistent state
    orchestrator.is_waiting_for_user_action = True
    orchestrator.system_mode = 'ready'  # Inconsistent with waiting state
    
    validation_result = orchestrator.validate_system_state()
    assert validation_result['is_valid'] is False, "Inconsistent state should be invalid"
    assert len(validation_result['issues']) > 0, "Inconsistent state should have issues"
    
    # Reset state
    orchestrator._reset_deferred_action_state()
    
    print("✓ State validation test passed")


def test_timeout_handling():
    """Test timeout detection and handling."""
    print("Testing timeout handling...")
    
    orchestrator = Orchestrator()
    
    # Set up a timed-out deferred action
    current_time = time.time()
    orchestrator.is_waiting_for_user_action = True
    orchestrator.deferred_action_start_time = current_time - 400  # 400 seconds ago (past timeout)
    orchestrator.deferred_action_timeout_time = current_time - 100  # Timeout was 100 seconds ago
    orchestrator.system_mode = 'waiting_for_user'
    
    # Check timeout detection
    timeout_issues = orchestrator._check_timeout_conditions()
    assert len(timeout_issues) > 0, "Timeout should be detected"
    assert any('timeout' in issue.lower() for issue in timeout_issues), "Should detect timeout condition"
    
    # Test timeout handling
    timeout_result = orchestrator.handle_deferred_action_timeout()
    assert timeout_result['timeout_handled'] is True, "Timeout should be handled"
    assert timeout_result['was_waiting'] is True, "Should record that we were waiting"
    
    # Verify state is reset after timeout
    assert orchestrator.is_waiting_for_user_action is False, "Should not be waiting after timeout"
    assert orchestrator.system_mode == 'ready', "Should be in ready mode after timeout"
    
    print("✓ Timeout handling test passed")


def test_state_consistency_validation():
    """Test state consistency validation and correction."""
    print("Testing state consistency validation...")
    
    orchestrator = Orchestrator()
    
    # Create inconsistent state
    orchestrator.is_waiting_for_user_action = True
    orchestrator.pending_action_payload = None  # Inconsistent - should have payload when waiting
    orchestrator.mouse_listener_active = True
    orchestrator.mouse_listener = None  # Inconsistent - active but no listener
    
    # Validate consistency
    consistency_result = orchestrator._validate_deferred_action_state_consistency()
    assert consistency_result['is_consistent'] is False, "Inconsistent state should be detected"
    assert len(consistency_result['issues']) > 0, "Should have consistency issues"
    
    # Force consistency
    orchestrator._force_state_consistency()
    
    # Verify consistency is restored
    consistency_result = orchestrator._validate_deferred_action_state_consistency()
    assert consistency_result['is_consistent'] is True, "State should be consistent after force reset"
    
    print("✓ State consistency validation test passed")


def test_state_transition_recording():
    """Test state transition recording functionality."""
    print("Testing state transition recording...")
    
    orchestrator = Orchestrator()
    
    # Record some state transitions
    initial_count = len(orchestrator.state_transition_history)
    
    orchestrator._record_state_transition('test_transition', {'test': 'data'})
    assert len(orchestrator.state_transition_history) == initial_count + 1, "Transition should be recorded"
    
    # Check transition record structure
    last_transition = orchestrator.state_transition_history[-1]
    assert 'timestamp' in last_transition, "Transition should have timestamp"
    assert 'transition_type' in last_transition, "Transition should have type"
    assert 'context' in last_transition, "Transition should have context"
    assert last_transition['transition_type'] == 'test_transition', "Transition type should match"
    
    print("✓ State transition recording test passed")


def test_state_diagnostics():
    """Test state diagnostics functionality."""
    print("Testing state diagnostics...")
    
    orchestrator = Orchestrator()
    
    # Get diagnostics
    diagnostics = orchestrator.get_state_diagnostics()
    
    # Verify diagnostics structure
    assert 'timestamp' in diagnostics, "Diagnostics should have timestamp"
    assert 'state_summary' in diagnostics, "Diagnostics should have state summary"
    assert 'validation_result' in diagnostics, "Diagnostics should have validation result"
    assert 'configuration' in diagnostics, "Diagnostics should have configuration"
    
    # Verify state summary content
    state_summary = diagnostics['state_summary']
    assert 'system_mode' in state_summary, "State summary should include system mode"
    assert 'is_waiting_for_user_action' in state_summary, "State summary should include waiting status"
    
    print("✓ State diagnostics test passed")


def run_all_tests():
    """Run all state management tests."""
    print("Running state management system tests...\n")
    
    try:
        test_state_management_initialization()
        test_reset_deferred_action_state()
        test_state_validation()
        test_timeout_handling()
        test_state_consistency_validation()
        test_state_transition_recording()
        test_state_diagnostics()
        
        print("\n✅ All state management tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)