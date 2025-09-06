#!/usr/bin/env python3
"""
Simple test for the enhanced state management system.
"""

import sys
import time
from unittest.mock import Mock

# Add the project root to the path
sys.path.insert(0, '.')

from orchestrator import Orchestrator


def test_basic_state_management():
    """Test basic state management functionality."""
    print("Testing basic state management...")
    
    orchestrator = Orchestrator()
    
    # Test initialization
    assert orchestrator.system_mode == 'ready'
    assert orchestrator.is_waiting_for_user_action is False
    assert orchestrator.mouse_listener_active is False
    
    # Test state reset
    orchestrator.is_waiting_for_user_action = True
    orchestrator.pending_action_payload = "test"
    orchestrator.system_mode = 'waiting_for_user'
    
    orchestrator._reset_deferred_action_state()
    
    assert orchestrator.is_waiting_for_user_action is False
    assert orchestrator.pending_action_payload is None
    assert orchestrator.system_mode == 'ready'
    
    print("✓ Basic state management test passed")


def test_state_validation():
    """Test state validation."""
    print("Testing state validation...")
    
    orchestrator = Orchestrator()
    
    # Test clean state validation
    result = orchestrator._validate_deferred_action_state_consistency()
    assert result['is_consistent'] is True
    
    # Test inconsistent state
    orchestrator.is_waiting_for_user_action = True
    orchestrator.pending_action_payload = None  # Should have payload when waiting
    
    result = orchestrator._validate_deferred_action_state_consistency()
    assert result['is_consistent'] is False
    assert len(result['issues']) > 0
    
    print("✓ State validation test passed")


def test_timeout_detection():
    """Test timeout detection."""
    print("Testing timeout detection...")
    
    orchestrator = Orchestrator()
    
    # Set up timed out state
    current_time = time.time()
    orchestrator.is_waiting_for_user_action = True
    orchestrator.deferred_action_start_time = current_time - 400  # 400 seconds ago
    orchestrator.deferred_action_timeout_seconds = 300  # 5 minute timeout
    
    timeout_issues = orchestrator._check_timeout_conditions()
    assert len(timeout_issues) > 0
    assert any('timeout' in issue.lower() for issue in timeout_issues)
    
    print("✓ Timeout detection test passed")


def run_simple_tests():
    """Run simple state management tests."""
    print("Running simple state management tests...\n")
    
    try:
        test_basic_state_management()
        test_state_validation()
        test_timeout_detection()
        
        print("\n✅ All simple tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_simple_tests()
    sys.exit(0 if success else 1)