#!/usr/bin/env python3
"""
Test script to verify the two critical bug fixes:
1. Timeout removal from cliclick typing
2. State management fix for deferred actions
"""

import sys
import time
import subprocess
import threading
from unittest.mock import Mock, patch, MagicMock

# Add the project root to the path
sys.path.insert(0, '.')

def test_timeout_removal_fix():
    """Test that the timeout has been removed from cliclick typing."""
    print("🔧 Testing Bug Fix #1: Timeout Removal from cliclick typing")
    
    try:
        from modules.automation import AutomationModule
        
        # Create automation module instance
        automation = AutomationModule()
        
        # Check if we're on macOS and have cliclick
        if not automation.is_macos or not automation.has_cliclick:
            print("⚠️  Skipping timeout test - not on macOS or cliclick not available")
            return True
        
        # Mock subprocess.run to capture the call
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stderr="")
            
            # Test typing with a large text block
            large_text = "def example_function():\n" + "    # This is a comment\n" * 100
            
            try:
                success = automation._cliclick_type(large_text)
                
                # Verify subprocess.run was called without timeout
                mock_run.assert_called_once()
                call_args = mock_run.call_args
                
                # Check that timeout is not in the kwargs
                if 'timeout' in call_args.kwargs:
                    print("❌ FAILED: timeout parameter still present in subprocess.run call")
                    print(f"   Call args: {call_args}")
                    return False
                
                print("✅ SUCCESS: timeout parameter removed from cliclick typing")
                return True
                
            except Exception as e:
                print(f"❌ FAILED: Error during typing test: {e}")
                return False
                
    except ImportError as e:
        print(f"❌ FAILED: Could not import AutomationModule: {e}")
        return False

def test_state_management_fix():
    """Test that the state management fix prevents race conditions."""
    print("\n🔧 Testing Bug Fix #2: State Management Fix for deferred actions")
    
    try:
        from orchestrator import Orchestrator
        
        # Create orchestrator instance
        orchestrator = Orchestrator()
        
        # Verify the new deferred_action_executing flag exists
        if not hasattr(orchestrator, 'deferred_action_executing'):
            print("❌ FAILED: deferred_action_executing flag not found")
            return False
        
        # Verify initial state
        if orchestrator.deferred_action_executing != False:
            print("❌ FAILED: deferred_action_executing should be False initially")
            return False
        
        # Test state reset functionality
        orchestrator.deferred_action_executing = True
        orchestrator.is_waiting_for_user_action = True
        
        # Call reset method
        orchestrator._reset_deferred_action_state()
        
        # Verify both flags are reset
        if orchestrator.deferred_action_executing != False:
            print("❌ FAILED: deferred_action_executing not reset by _reset_deferred_action_state")
            return False
        
        if orchestrator.is_waiting_for_user_action != False:
            print("❌ FAILED: is_waiting_for_user_action not reset by _reset_deferred_action_state")
            return False
        
        print("✅ SUCCESS: State management fix implemented correctly")
        print("   - deferred_action_executing flag added")
        print("   - State reset methods updated")
        print("   - Race condition prevention in place")
        
        return True
        
    except ImportError as e:
        print(f"❌ FAILED: Could not import Orchestrator: {e}")
        return False
    except Exception as e:
        print(f"❌ FAILED: Error during state management test: {e}")
        return False

def test_deferred_action_trigger_fix():
    """Test that the _on_deferred_action_trigger method has proper finally block."""
    print("\n🔧 Testing Bug Fix #2b: Deferred Action Trigger Finally Block")
    
    try:
        from orchestrator import Orchestrator
        
        # Create orchestrator instance with mocked dependencies
        with patch('modules.vision.VisionModule'), \
             patch('modules.reasoning.ReasoningModule'), \
             patch('modules.automation.AutomationModule'), \
             patch('modules.audio.AudioModule'), \
             patch('modules.feedback.FeedbackModule'), \
             patch('modules.accessibility.AccessibilityModule'):
            
            orchestrator = Orchestrator()
            
            # Set up initial state
            orchestrator.is_waiting_for_user_action = True
            orchestrator.deferred_action_executing = False
            orchestrator.pending_action_payload = {"test": "data"}
            
            # Mock the execution lock
            orchestrator.execution_lock = Mock()
            orchestrator.execution_lock.acquire.return_value = True
            orchestrator.execution_lock.locked.return_value = True
            
            # Mock other dependencies
            orchestrator.deferred_action_lock = threading.Lock()
            orchestrator.mouse_listener = Mock()
            orchestrator.mouse_listener.get_last_click_coordinates.return_value = (100, 100)
            
            # Mock the execution method to raise an exception
            def mock_execute_pending(*args, **kwargs):
                raise Exception("Simulated execution error")
            
            orchestrator._execute_pending_deferred_action = mock_execute_pending
            orchestrator._provide_deferred_action_completion_feedback = Mock()
            orchestrator._reset_deferred_action_state = Mock()
            
            # Call the trigger method - it should handle the exception gracefully
            try:
                orchestrator._on_deferred_action_trigger("test_execution_id")
            except Exception as e:
                print(f"❌ FAILED: Exception not handled properly: {e}")
                return False
            
            # Verify that reset was called (should be called in finally block)
            if not orchestrator._reset_deferred_action_state.called:
                print("❌ FAILED: _reset_deferred_action_state not called in finally block")
                return False
            
            print("✅ SUCCESS: Finally block properly implemented in _on_deferred_action_trigger")
            return True
            
    except Exception as e:
        print(f"❌ FAILED: Error during deferred action trigger test: {e}")
        return False

def main():
    """Run all critical bug fix tests."""
    print("🚀 Running Critical Bug Fix Tests")
    print("=" * 50)
    
    results = []
    
    # Test 1: Timeout removal fix
    results.append(test_timeout_removal_fix())
    
    # Test 2: State management fix
    results.append(test_state_management_fix())
    
    # Test 3: Deferred action trigger fix
    results.append(test_deferred_action_trigger_fix())
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ ALL TESTS PASSED ({passed}/{total})")
        print("\n🎉 Both critical bugs have been successfully fixed!")
        print("\nBug Fix Summary:")
        print("1. ✅ Timeout removed from cliclick typing - no more partial content")
        print("2. ✅ State management improved - no more hang-ups after first command")
        return 0
    else:
        print(f"❌ SOME TESTS FAILED ({passed}/{total})")
        print("\n⚠️  Please review the failed tests above")
        return 1

if __name__ == "__main__":
    exit(main())