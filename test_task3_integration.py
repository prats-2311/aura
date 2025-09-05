#!/usr/bin/env python3
"""
Integration test for Task 3: Intent-based command routing.

This test verifies that the complete command execution flow works correctly
with the new intent-based routing system.
"""

import sys
import logging
from unittest.mock import Mock, patch, MagicMock

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_command_execution_with_intent_routing():
    """Test that command execution works with the new intent-based routing."""
    try:
        from orchestrator import Orchestrator
        
        with patch('orchestrator.VisionModule') as mock_vision, \
             patch('orchestrator.ReasoningModule') as mock_reasoning, \
             patch('orchestrator.AutomationModule') as mock_automation, \
             patch('orchestrator.AudioModule') as mock_audio, \
             patch('orchestrator.FeedbackModule') as mock_feedback, \
             patch('orchestrator.AccessibilityModule') as mock_accessibility:
            
            # Set up mocks
            mock_vision_instance = Mock()
            mock_reasoning_instance = Mock()
            mock_automation_instance = Mock()
            mock_audio_instance = Mock()
            mock_feedback_instance = Mock()
            mock_accessibility_instance = Mock()
            
            mock_vision.return_value = mock_vision_instance
            mock_reasoning.return_value = mock_reasoning_instance
            mock_automation.return_value = mock_automation_instance
            mock_audio.return_value = mock_audio_instance
            mock_feedback.return_value = mock_feedback_instance
            mock_accessibility.return_value = mock_accessibility_instance
            
            # Mock the feedback module methods
            mock_feedback_instance.play = Mock()
            mock_feedback_instance.speak = Mock()
            
            orchestrator = Orchestrator()
            
            # Mock the intent recognition to return GUI interaction
            orchestrator._recognize_intent = Mock(return_value={
                'intent': 'gui_interaction',
                'confidence': 0.9,
                'parameters': {}
            })
            
            # Mock the validation
            mock_validation_result = Mock()
            mock_validation_result.is_valid = True
            mock_validation_result.normalized_command = "click button"
            mock_validation_result.command_type = "click"
            mock_validation_result.confidence = 0.9
            mock_validation_result.issues = []
            mock_validation_result.suggestions = []
            
            orchestrator.validate_command = Mock(return_value=mock_validation_result)
            
            # Mock other methods to avoid full execution
            orchestrator._is_gui_command = Mock(return_value=True)
            orchestrator._handle_application_focus_change = Mock()
            orchestrator._attempt_fast_path_execution = Mock(return_value={'success': False})
            orchestrator._handle_fast_path_fallback = Mock()
            orchestrator._perform_parallel_perception_reasoning = Mock(return_value=({}, {}))
            orchestrator._perform_screen_perception = Mock(return_value={'description': 'test screen'})
            orchestrator._perform_command_reasoning = Mock(return_value={'action': 'click'})
            orchestrator._perform_action_execution = Mock(return_value={'success': True})
            orchestrator._format_execution_result = Mock(return_value={'status': 'completed'})
            orchestrator._update_progress = Mock()
            
            # Test command execution
            result = orchestrator.execute_command("click button")
            
            # Verify intent recognition was called
            orchestrator._recognize_intent.assert_called_once_with("click button")
            
            # Verify the command was processed
            assert result is not None, "Command execution should return a result"
            
            logger.info("✓ Command execution with intent routing works correctly")
            return True
            
    except Exception as e:
        logger.error(f"✗ Command execution test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_deferred_action_interruption():
    """Test that new commands properly interrupt deferred actions."""
    try:
        from orchestrator import Orchestrator
        
        with patch('orchestrator.VisionModule'), \
             patch('orchestrator.ReasoningModule'), \
             patch('orchestrator.AutomationModule'), \
             patch('orchestrator.AudioModule'), \
             patch('orchestrator.FeedbackModule'), \
             patch('orchestrator.AccessibilityModule'):
            
            orchestrator = Orchestrator()
            
            # Set up a deferred action state
            orchestrator.is_waiting_for_user_action = True
            orchestrator.pending_action_payload = "test payload"
            orchestrator.deferred_action_type = "type"
            
            # Mock the intent recognition and handlers
            orchestrator._recognize_intent = Mock(return_value={
                'intent': 'gui_interaction',
                'confidence': 0.9,
                'parameters': {}
            })
            
            orchestrator._handle_gui_interaction = Mock(return_value={'status': 'completed'})
            
            # Mock the _execute_command_internal method to test interruption logic
            original_method = orchestrator._execute_command_internal
            
            def mock_execute_internal(command):
                # This should trigger the deferred action interruption
                return original_method(command)
            
            orchestrator._execute_command_internal = mock_execute_internal
            
            # Execute a new command - this should interrupt the deferred action
            try:
                orchestrator.execute_command("new command")
            except:
                # We expect this to fail due to mocking, but the interruption should still work
                pass
            
            # Verify that deferred action state was reset
            assert orchestrator.is_waiting_for_user_action == False, "Deferred action should be interrupted"
            assert orchestrator.pending_action_payload is None, "Payload should be cleared"
            assert orchestrator.deferred_action_type is None, "Action type should be cleared"
            
            logger.info("✓ Deferred action interruption works correctly")
            return True
            
    except Exception as e:
        logger.error(f"✗ Deferred action interruption test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_backward_compatibility():
    """Test that existing GUI functionality is preserved."""
    try:
        from orchestrator import Orchestrator
        
        with patch('orchestrator.VisionModule'), \
             patch('orchestrator.ReasoningModule'), \
             patch('orchestrator.AutomationModule'), \
             patch('orchestrator.AudioModule'), \
             patch('orchestrator.FeedbackModule'), \
             patch('orchestrator.AccessibilityModule'):
            
            orchestrator = Orchestrator()
            
            # Test that the legacy execution method exists and works
            execution_context = {
                "execution_id": "test_id",
                "command": "click button",
                "start_time": 1234567890,
                "status": "processing",
                "steps_completed": [],
                "errors": [],
                "warnings": [],
                "validation_result": None,
                "screen_context": None,
                "action_plan": None,
                "execution_results": None
            }
            
            # Mock all the methods that the legacy execution uses
            mock_validation_result = Mock()
            mock_validation_result.is_valid = True
            mock_validation_result.normalized_command = "click button"
            mock_validation_result.command_type = "click"
            mock_validation_result.confidence = 0.9
            mock_validation_result.issues = []
            mock_validation_result.suggestions = []
            
            orchestrator.validate_command = Mock(return_value=mock_validation_result)
            orchestrator._is_gui_command = Mock(return_value=True)
            orchestrator._handle_application_focus_change = Mock()
            orchestrator._attempt_fast_path_execution = Mock(return_value={'success': True})
            orchestrator._update_progress = Mock()
            orchestrator._format_execution_result = Mock(return_value={'status': 'completed'})
            
            # Test the legacy execution method
            result = orchestrator._legacy_execute_command_internal("click button", execution_context)
            
            # Verify it returns a result
            assert result is not None, "Legacy execution should return a result"
            
            logger.info("✓ Backward compatibility preserved")
            return True
            
    except Exception as e:
        logger.error(f"✗ Backward compatibility test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all integration tests for Task 3."""
    logger.info("Starting Task 3 integration tests...")
    
    tests = [
        ("Command Execution with Intent Routing", test_command_execution_with_intent_routing),
        ("Deferred Action Interruption", test_deferred_action_interruption),
        ("Backward Compatibility", test_backward_compatibility)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n--- Running: {test_name} ---")
        try:
            if test_func():
                passed += 1
            else:
                logger.error(f"Test failed: {test_name}")
        except Exception as e:
            logger.error(f"Test error in {test_name}: {e}")
    
    logger.info(f"\n=== Integration Test Results ===")
    logger.info(f"Passed: {passed}/{total}")
    logger.info(f"Failed: {total - passed}/{total}")
    
    if passed == total:
        logger.info("✓ All Task 3 integration tests passed!")
        return True
    else:
        logger.error("✗ Some Task 3 integration tests failed!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)