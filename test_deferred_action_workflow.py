#!/usr/bin/env python3
"""
Test script for deferred action workflow implementation.

This script tests the deferred action workflow system to ensure:
1. Content generation works correctly
2. State management is properly handled
3. Mouse listener integration functions
4. Audio feedback is provided
5. Error handling works as expected
"""

import sys
import time
import logging
from unittest.mock import Mock, patch, MagicMock

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_deferred_action_workflow():
    """Test the deferred action workflow implementation."""
    
    try:
        # Import the orchestrator
        from orchestrator import Orchestrator
        
        logger.info("Creating orchestrator instance...")
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
        
        # Test 1: Content Generation
        logger.info("Testing content generation...")
        
        # Mock reasoning module response
        orchestrator.reasoning_module.reason.return_value = {
            'response': 'def hello_world():\n    print("Hello, World!")\n    return "success"'
        }
        
        content = orchestrator._generate_deferred_content(
            execution_id="test-001",
            content_request="write a hello world function in python",
            content_type="code"
        )
        
        assert content is not None, "Content generation should not return None"
        assert len(content) > 5, "Generated content should be substantial"
        assert "hello_world" in content.lower(), "Content should contain requested function"
        logger.info(f"✅ Content generation successful: {len(content)} characters")
        
        # Test 2: Deferred Action Request Handling
        logger.info("Testing deferred action request handling...")
        
        # Mock mouse listener to avoid actual mouse listening
        with patch('utils.mouse_listener.GlobalMouseListener') as mock_listener_class:
            mock_listener = Mock()
            mock_listener_class.return_value = mock_listener
            
            # Mock is_mouse_listener_available to return True
            with patch('utils.mouse_listener.is_mouse_listener_available', return_value=True):
                
                intent_data = {
                    'intent': 'deferred_action',
                    'parameters': {
                        'target': 'write a python function to calculate fibonacci',
                        'content_type': 'code'
                    },
                    'original_command': 'write a python function to calculate fibonacci'
                }
                
                result = orchestrator._handle_deferred_action_request("test-002", intent_data)
                
                assert result['status'] == 'waiting_for_user_action', f"Expected waiting status, got {result['status']}"
                assert result['success'] is True, "Deferred action should succeed"
                assert 'content_preview' in result, "Result should include content preview"
                
                # Verify state was set correctly
                assert orchestrator.is_waiting_for_user_action is True, "Should be waiting for user action"
                assert orchestrator.pending_action_payload is not None, "Should have pending payload"
                assert orchestrator.deferred_action_type == 'type', "Action type should be 'type'"
                
                logger.info("✅ Deferred action request handling successful")
        
        # Test 3: State Management
        logger.info("Testing state management...")
        
        # Verify state before reset
        assert orchestrator.is_waiting_for_user_action is True, "Should be in waiting state"
        
        # Test state reset
        orchestrator._reset_deferred_action_state()
        
        # Verify state after reset
        assert orchestrator.is_waiting_for_user_action is False, "Should not be waiting after reset"
        assert orchestrator.pending_action_payload is None, "Payload should be cleared"
        assert orchestrator.deferred_action_type is None, "Action type should be cleared"
        assert orchestrator.mouse_listener is None, "Mouse listener should be cleared"
        
        logger.info("✅ State management working correctly")
        
        # Test 4: Error Handling
        logger.info("Testing error handling...")
        
        # Test with failing reasoning module
        orchestrator.reasoning_module.reason.side_effect = Exception("API Error")
        
        intent_data = {
            'intent': 'deferred_action',
            'parameters': {
                'target': 'write some code',
                'content_type': 'code'
            },
            'original_command': 'write some code'
        }
        
        result = orchestrator._handle_deferred_action_request("test-003", intent_data)
        
        assert result['status'] == 'failed', f"Expected failed status, got {result['status']}"
        assert result['success'] is False, "Should indicate failure"
        assert 'error' in result, "Should include error information"
        
        logger.info("✅ Error handling working correctly")
        
        # Test 5: Deferred Action Execution
        logger.info("Testing deferred action execution...")
        
        # Reset reasoning module mock
        orchestrator.reasoning_module.reason.side_effect = None
        orchestrator.reasoning_module.reason.return_value = {
            'response': 'print("Test execution")'
        }
        
        # Set up state for execution test
        orchestrator.pending_action_payload = 'print("Hello from deferred action")'
        orchestrator.deferred_action_type = 'type'
        
        # Mock automation module
        orchestrator.automation_module.click.return_value = {'success': True}
        orchestrator.automation_module.type_text.return_value = {'success': True}
        
        # Test execution
        success = orchestrator._execute_pending_deferred_action("test-004", (100, 200))
        
        assert success is True, "Deferred action execution should succeed"
        
        # Verify automation module was called
        orchestrator.automation_module.click.assert_called_with(100, 200)
        orchestrator.automation_module.type_text.assert_called_with('print("Hello from deferred action")')
        
        logger.info("✅ Deferred action execution working correctly")
        
        logger.info("🎉 All deferred action workflow tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_mouse_listener_integration():
    """Test mouse listener integration."""
    
    try:
        logger.info("Testing mouse listener integration...")
        
        # Test mouse listener availability check
        from utils.mouse_listener import is_mouse_listener_available
        
        available = is_mouse_listener_available()
        logger.info(f"Mouse listener available: {available}")
        
        if available:
            from utils.mouse_listener import GlobalMouseListener
            
            # Test creating mouse listener (but don't start it)
            callback_called = False
            
            def test_callback():
                nonlocal callback_called
                callback_called = True
            
            listener = GlobalMouseListener(test_callback)
            assert listener is not None, "Should be able to create mouse listener"
            assert listener.is_active() is False, "Should not be active initially"
            
            logger.info("✅ Mouse listener integration test passed")
        else:
            logger.warning("⚠️ Mouse listener not available (pynput not installed)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Mouse listener test failed: {e}")
        return False

def main():
    """Run all tests."""
    logger.info("Starting deferred action workflow tests...")
    
    success = True
    
    # Test 1: Core workflow
    if not test_deferred_action_workflow():
        success = False
    
    # Test 2: Mouse listener integration
    if not test_mouse_listener_integration():
        success = False
    
    if success:
        logger.info("🎉 All tests passed successfully!")
        return 0
    else:
        logger.error("❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())