#!/usr/bin/env python3
"""
Integration test for deferred action workflow.

This test verifies that the deferred action workflow integrates properly
with the orchestrator's command execution system.
"""

import sys
import time
import logging
from unittest.mock import Mock, patch

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_deferred_action_integration():
    """Test deferred action integration with orchestrator command execution."""
    
    try:
        from orchestrator import Orchestrator
        
        logger.info("Creating orchestrator for integration test...")
        orchestrator = Orchestrator()
        
        # Mock the modules to avoid actual API calls
        orchestrator.reasoning_module = Mock()
        orchestrator.automation_module = Mock()
        orchestrator.feedback_module = Mock()
        orchestrator.audio_module = Mock()
        
        # Set module availability
        orchestrator.module_availability = {
            'reasoning': True,
            'automation': True,
            'feedback': True,
            'audio': True,
            'vision': True,
            'accessibility': True
        }
        
        # Mock intent recognition to return deferred action intent
        def mock_recognize_intent(command):
            if "write code" in command.lower() or "generate" in command.lower():
                return {
                    'intent': 'deferred_action',
                    'confidence': 0.95,
                    'parameters': {
                        'action_type': 'generate_code',
                        'target': command,
                        'content_type': 'code'
                    },
                    'reasoning': 'User is requesting code generation',
                    'original_command': command
                }
            else:
                return {
                    'intent': 'gui_interaction',
                    'confidence': 0.8,
                    'parameters': {},
                    'original_command': command
                }
        
        orchestrator._recognize_intent = mock_recognize_intent
        
        # Mock reasoning module to return code
        orchestrator.reasoning_module.reason.return_value = {
            'response': '''def fibonacci(n):
    """Calculate fibonacci number recursively."""
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)'''
        }
        
        # Test 1: Execute deferred action command through main interface
        logger.info("Testing deferred action through execute_command...")
        
        with patch('utils.mouse_listener.GlobalMouseListener') as mock_listener_class:
            mock_listener = Mock()
            mock_listener_class.return_value = mock_listener
            
            with patch('utils.mouse_listener.is_mouse_listener_available', return_value=True):
                
                command = "write code for a fibonacci function"
                result = orchestrator.execute_command(command)
                
                assert result is not None, "Command execution should return a result"
                assert result.get('status') == 'waiting_for_user_action', f"Expected waiting status, got {result.get('status')}"
                assert result.get('success') is True, "Command should succeed"
                
                # Verify orchestrator state
                assert orchestrator.is_waiting_for_user_action is True, "Should be waiting for user action"
                assert orchestrator.pending_action_payload is not None, "Should have pending content"
                
                logger.info("✅ Deferred action command execution successful")
        
        # Test 2: Simulate user click to complete deferred action
        logger.info("Testing deferred action completion...")
        
        # Mock automation module for execution
        orchestrator.automation_module.click.return_value = {'success': True}
        orchestrator.automation_module.type_text.return_value = {'success': True}
        
        # Create a mock mouse listener with coordinates
        mock_listener = Mock()
        mock_listener.get_last_click_coordinates.return_value = (500, 300)
        orchestrator.mouse_listener = mock_listener
        
        # Trigger the deferred action
        orchestrator._on_deferred_action_trigger("integration-test")
        
        # Verify automation was called
        orchestrator.automation_module.click.assert_called_with(500, 300)
        assert orchestrator.automation_module.type_text.called, "Type text should have been called"
        
        # Verify state was reset
        assert orchestrator.is_waiting_for_user_action is False, "Should not be waiting after completion"
        assert orchestrator.pending_action_payload is None, "Payload should be cleared"
        
        logger.info("✅ Deferred action completion successful")
        
        # Test 3: Command interruption during deferred action
        logger.info("Testing command interruption...")
        
        # Set up deferred action state
        orchestrator.is_waiting_for_user_action = True
        orchestrator.pending_action_payload = "some content"
        orchestrator.deferred_action_type = "type"
        
        # Execute a new command (should interrupt)
        with patch('utils.mouse_listener.GlobalMouseListener'):
            with patch('utils.mouse_listener.is_mouse_listener_available', return_value=True):
                
                # Mock intent recognition for GUI command
                def mock_gui_intent(command):
                    return {
                        'intent': 'gui_interaction',
                        'confidence': 0.9,
                        'parameters': {},
                        'original_command': command
                    }
                
                orchestrator._recognize_intent = mock_gui_intent
                
                # This should interrupt the deferred action
                result = orchestrator.execute_command("click on button")
                
                # Verify deferred action was interrupted
                assert orchestrator.is_waiting_for_user_action is False, "Deferred action should be interrupted"
                assert orchestrator.pending_action_payload is None, "Payload should be cleared on interruption"
                
                logger.info("✅ Command interruption working correctly")
        
        logger.info("🎉 All integration tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run integration test."""
    logger.info("Starting deferred action integration test...")
    
    if test_deferred_action_integration():
        logger.info("🎉 Integration test passed successfully!")
        return 0
    else:
        logger.error("❌ Integration test failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())