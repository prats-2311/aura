#!/usr/bin/env python3
"""
Test script for conversational query handler implementation.

This script tests the new _handle_conversational_query method in the orchestrator
to ensure it properly processes conversational queries and provides appropriate responses.
"""

import sys
import logging
import time
from unittest.mock import Mock, patch, MagicMock

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_conversational_handler():
    """Test the conversational query handler implementation."""
    
    try:
        # Import the orchestrator
        from orchestrator import Orchestrator
        
        logger.info("Creating orchestrator instance...")
        orchestrator = Orchestrator()
        
        # Mock the reasoning module to simulate API responses
        mock_reasoning_module = Mock()
        mock_api_response = {
            'message': {
                'content': 'Hello! I\'m AURA, your AI assistant. How can I help you today?'
            }
        }
        mock_reasoning_module._make_api_request.return_value = mock_api_response
        orchestrator.reasoning_module = mock_reasoning_module
        orchestrator.module_availability['reasoning'] = True
        
        # Mock the feedback module to avoid audio issues during testing
        mock_feedback_module = Mock()
        orchestrator.feedback_module = mock_feedback_module
        orchestrator.module_availability['feedback'] = True
        
        # Test 1: Basic conversational query
        logger.info("Test 1: Testing basic conversational query...")
        test_query = "Hello, how are you?"
        execution_id = "test_001"
        
        result = orchestrator._handle_conversational_query(execution_id, test_query)
        
        # Verify the result structure
        assert result is not None, "Result should not be None"
        assert result.get('success') is True, f"Expected success=True, got {result.get('success')}"
        assert result.get('mode') == 'conversational_chat', f"Expected mode='conversational_chat', got {result.get('mode')}"
        assert result.get('response') is not None, "Response should not be None"
        assert result.get('audio_feedback_provided') is True, "Audio feedback should be provided"
        
        logger.info(f"✓ Test 1 passed. Response: {result.get('response')}")
        
        # Test 2: Verify reasoning module was called correctly
        logger.info("Test 2: Verifying reasoning module integration...")
        
        # Check that _make_api_request was called
        mock_reasoning_module._make_api_request.assert_called_once()
        
        # Get the prompt that was sent
        call_args = mock_reasoning_module._make_api_request.call_args
        prompt_sent = call_args[0][0]  # First positional argument
        
        # Verify the prompt contains the conversational template
        assert "AURA" in prompt_sent, "Prompt should contain AURA identity"
        assert test_query in prompt_sent, "Prompt should contain the user query"
        
        logger.info("✓ Test 2 passed. Reasoning module called correctly")
        
        # Test 3: Verify feedback module integration
        logger.info("Test 3: Verifying feedback module integration...")
        
        # Check that speak was called
        mock_feedback_module.speak.assert_called_once()
        
        # Get the message that was spoken
        speak_call_args = mock_feedback_module.speak.call_args
        spoken_message = speak_call_args[0][0]  # First positional argument
        
        assert spoken_message == result.get('response'), "Spoken message should match response"
        
        logger.info("✓ Test 3 passed. Feedback module called correctly")
        
        # Test 4: Test error handling with unavailable reasoning module
        logger.info("Test 4: Testing error handling with unavailable reasoning module...")
        
        # Disable reasoning module
        orchestrator.module_availability['reasoning'] = False
        
        result_error = orchestrator._handle_conversational_query("test_002", "Another test query")
        
        # Verify fallback behavior
        assert result_error is not None, "Result should not be None even with error"
        assert result_error.get('success') is True, "Should still succeed with fallback"
        assert "sorry" in result_error.get('response', '').lower(), "Should provide apologetic fallback response"
        
        logger.info("✓ Test 4 passed. Error handling works correctly")
        
        # Test 5: Test conversation history update
        logger.info("Test 5: Testing conversation history update...")
        
        # Re-enable reasoning module for this test
        orchestrator.module_availability['reasoning'] = True
        
        initial_history_length = len(orchestrator.conversation_history)
        
        orchestrator._handle_conversational_query("test_003", "Test history update")
        
        final_history_length = len(orchestrator.conversation_history)
        
        assert final_history_length == initial_history_length + 1, "Conversation history should be updated"
        
        # Check the latest entry
        latest_entry = orchestrator.conversation_history[-1]
        assert latest_entry[0] == "Test history update", "User query should be stored"
        assert latest_entry[1] is not None, "Assistant response should be stored"
        
        logger.info("✓ Test 5 passed. Conversation history updated correctly")
        
        logger.info("🎉 All tests passed! Conversational handler implementation is working correctly.")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_helper_methods():
    """Test the helper methods for conversational processing."""
    
    try:
        from orchestrator import Orchestrator
        
        logger.info("Testing helper methods...")
        orchestrator = Orchestrator()
        
        # Test _extract_conversational_response with different API response formats
        logger.info("Testing _extract_conversational_response...")
        
        # Test Ollama format
        ollama_response = {
            'message': {
                'content': 'This is a test response from Ollama format'
            }
        }
        
        extracted = orchestrator._extract_conversational_response(ollama_response)
        assert extracted == 'This is a test response from Ollama format', "Ollama format extraction failed"
        
        # Test OpenAI format
        openai_response = {
            'choices': [{
                'message': {
                    'content': 'This is a test response from OpenAI format'
                }
            }]
        }
        
        extracted = orchestrator._extract_conversational_response(openai_response)
        assert extracted == 'This is a test response from OpenAI format', "OpenAI format extraction failed"
        
        # Test direct response format
        direct_response = {
            'response': 'This is a direct response format'
        }
        
        extracted = orchestrator._extract_conversational_response(direct_response)
        assert extracted == 'This is a direct response format', "Direct format extraction failed"
        
        logger.info("✓ Response extraction tests passed")
        
        # Test _update_conversation_history
        logger.info("Testing _update_conversation_history...")
        
        initial_length = len(orchestrator.conversation_history)
        
        orchestrator._update_conversation_history("Test user input", "Test assistant response")
        
        assert len(orchestrator.conversation_history) == initial_length + 1, "History should be updated"
        
        latest_entry = orchestrator.conversation_history[-1]
        assert latest_entry == ("Test user input", "Test assistant response"), "History entry should match input"
        
        logger.info("✓ Conversation history tests passed")
        
        logger.info("🎉 All helper method tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Helper method tests failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    logger.info("Starting conversational handler tests...")
    
    # Run main tests
    main_tests_passed = test_conversational_handler()
    
    # Run helper method tests
    helper_tests_passed = test_helper_methods()
    
    if main_tests_passed and helper_tests_passed:
        logger.info("🎉 All conversational handler tests completed successfully!")
        sys.exit(0)
    else:
        logger.error("❌ Some tests failed. Please check the implementation.")
        sys.exit(1)