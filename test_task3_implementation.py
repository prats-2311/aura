#!/usr/bin/env python3
"""
Test script for Task 3: Intent-based command routing implementation.

This script tests the refactored orchestrator command routing to ensure:
1. Intent recognition is properly integrated
2. Command routing works for different intent types
3. State checking for deferred action interruption works
4. GUI interaction functionality is preserved
"""

import sys
import logging
from unittest.mock import Mock, patch

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_orchestrator_import():
    """Test that the orchestrator can be imported successfully."""
    try:
        from orchestrator import Orchestrator
        logger.info("✓ Orchestrator import successful")
        return True
    except Exception as e:
        logger.error(f"✗ Orchestrator import failed: {e}")
        return False

def test_orchestrator_initialization():
    """Test that the orchestrator can be initialized with new state variables."""
    try:
        from orchestrator import Orchestrator
        
        # Mock the modules to avoid initialization issues
        with patch('orchestrator.VisionModule'), \
             patch('orchestrator.ReasoningModule'), \
             patch('orchestrator.AutomationModule'), \
             patch('orchestrator.AudioModule'), \
             patch('orchestrator.FeedbackModule'), \
             patch('orchestrator.AccessibilityModule'):
            
            orchestrator = Orchestrator()
            
            # Check that new state variables exist
            assert hasattr(orchestrator, 'is_waiting_for_user_action'), "Missing is_waiting_for_user_action"
            assert hasattr(orchestrator, 'pending_action_payload'), "Missing pending_action_payload"
            assert hasattr(orchestrator, 'deferred_action_type'), "Missing deferred_action_type"
            assert hasattr(orchestrator, 'intent_recognition_enabled'), "Missing intent_recognition_enabled"
            
            # Check initial state
            assert orchestrator.is_waiting_for_user_action == False, "Initial deferred action state should be False"
            assert orchestrator.pending_action_payload is None, "Initial payload should be None"
            assert orchestrator.deferred_action_type is None, "Initial action type should be None"
            
            logger.info("✓ Orchestrator initialization successful with new state variables")
            return True
            
    except Exception as e:
        logger.error(f"✗ Orchestrator initialization failed: {e}")
        return False

def test_new_methods_exist():
    """Test that the new routing methods exist."""
    try:
        from orchestrator import Orchestrator
        
        with patch('orchestrator.VisionModule'), \
             patch('orchestrator.ReasoningModule'), \
             patch('orchestrator.AutomationModule'), \
             patch('orchestrator.AudioModule'), \
             patch('orchestrator.FeedbackModule'), \
             patch('orchestrator.AccessibilityModule'):
            
            orchestrator = Orchestrator()
            
            # Check that new methods exist
            assert hasattr(orchestrator, '_route_command_by_intent'), "Missing _route_command_by_intent method"
            assert hasattr(orchestrator, '_reset_deferred_action_state'), "Missing _reset_deferred_action_state method"
            assert hasattr(orchestrator, '_legacy_execute_command_internal'), "Missing _legacy_execute_command_internal method"
            
            # Check that methods are callable
            assert callable(getattr(orchestrator, '_route_command_by_intent')), "_route_command_by_intent not callable"
            assert callable(getattr(orchestrator, '_reset_deferred_action_state')), "_reset_deferred_action_state not callable"
            assert callable(getattr(orchestrator, '_legacy_execute_command_internal')), "_legacy_execute_command_internal not callable"
            
            logger.info("✓ New routing methods exist and are callable")
            return True
            
    except Exception as e:
        logger.error(f"✗ New methods check failed: {e}")
        return False

def test_deferred_action_state_reset():
    """Test the deferred action state reset functionality."""
    try:
        from orchestrator import Orchestrator
        
        with patch('orchestrator.VisionModule'), \
             patch('orchestrator.ReasoningModule'), \
             patch('orchestrator.AutomationModule'), \
             patch('orchestrator.AudioModule'), \
             patch('orchestrator.FeedbackModule'), \
             patch('orchestrator.AccessibilityModule'):
            
            orchestrator = Orchestrator()
            
            # Set up some deferred action state
            orchestrator.is_waiting_for_user_action = True
            orchestrator.pending_action_payload = "test payload"
            orchestrator.deferred_action_type = "type"
            orchestrator.mouse_listener = Mock()
            
            # Test reset
            orchestrator._reset_deferred_action_state()
            
            # Verify state is reset
            assert orchestrator.is_waiting_for_user_action == False, "Waiting state not reset"
            assert orchestrator.pending_action_payload is None, "Payload not reset"
            assert orchestrator.deferred_action_type is None, "Action type not reset"
            assert orchestrator.mouse_listener is None, "Mouse listener not reset"
            
            logger.info("✓ Deferred action state reset works correctly")
            return True
            
    except Exception as e:
        logger.error(f"✗ Deferred action state reset test failed: {e}")
        return False

def test_intent_routing_structure():
    """Test that the intent routing structure is properly implemented."""
    try:
        from orchestrator import Orchestrator
        
        with patch('orchestrator.VisionModule'), \
             patch('orchestrator.ReasoningModule'), \
             patch('orchestrator.AutomationModule'), \
             patch('orchestrator.AudioModule'), \
             patch('orchestrator.FeedbackModule'), \
             patch('orchestrator.AccessibilityModule'):
            
            orchestrator = Orchestrator()
            
            # Mock the intent recognition to return different intents
            mock_intent_result = {
                'intent': 'gui_interaction',
                'confidence': 0.9,
                'parameters': {}
            }
            
            # Mock the handler methods to avoid actual execution
            orchestrator._handle_gui_interaction = Mock(return_value={'status': 'completed'})
            orchestrator._handle_conversational_query = Mock(return_value={'status': 'completed'})
            orchestrator._handle_deferred_action_request = Mock(return_value={'status': 'completed'})
            orchestrator._route_to_question_answering = Mock(return_value={'status': 'completed'})
            
            # Test routing for different intent types
            test_cases = [
                ('gui_interaction', orchestrator._handle_gui_interaction),
                ('conversational_chat', orchestrator._handle_conversational_query),
                ('deferred_action', orchestrator._handle_deferred_action_request),
                ('question_answering', orchestrator._route_to_question_answering)
            ]
            
            for intent_type, expected_handler in test_cases:
                mock_intent_result['intent'] = intent_type
                
                # Test the routing
                result = orchestrator._route_command_by_intent(
                    "test_id", 
                    "test command", 
                    mock_intent_result, 
                    {}
                )
                
                # Verify the correct handler was called
                expected_handler.assert_called()
                assert result['status'] == 'completed', f"Handler for {intent_type} didn't return expected result"
                
                # Reset mocks for next test
                for _, handler in test_cases:
                    if hasattr(handler, 'reset_mock'):
                        handler.reset_mock()
            
            logger.info("✓ Intent routing structure works correctly")
            return True
            
    except Exception as e:
        logger.error(f"✗ Intent routing structure test failed: {e}")
        return False

def main():
    """Run all tests for Task 3 implementation."""
    logger.info("Starting Task 3 implementation tests...")
    
    tests = [
        ("Orchestrator Import", test_orchestrator_import),
        ("Orchestrator Initialization", test_orchestrator_initialization),
        ("New Methods Exist", test_new_methods_exist),
        ("Deferred Action State Reset", test_deferred_action_state_reset),
        ("Intent Routing Structure", test_intent_routing_structure)
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
    
    logger.info(f"\n=== Test Results ===")
    logger.info(f"Passed: {passed}/{total}")
    logger.info(f"Failed: {total - passed}/{total}")
    
    if passed == total:
        logger.info("✓ All Task 3 implementation tests passed!")
        return True
    else:
        logger.error("✗ Some Task 3 implementation tests failed!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)