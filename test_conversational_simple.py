#!/usr/bin/env python3
"""
Simple test for conversational query handler implementation.

This script tests the conversational handler directly without going through
the full orchestrator flow to avoid vision module dependencies.
"""

import sys
import logging
import time
from unittest.mock import Mock, patch, MagicMock

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_conversational_handler_direct():
    """Test the conversational query handler directly."""
    
    try:
        # Import the orchestrator
        from orchestrator import Orchestrator
        
        logger.info("Creating orchestrator instance...")
        orchestrator = Orchestrator()
        
        # Mock the reasoning module to simulate API responses
        mock_reasoning_module = Mock()
        mock_api_response = {
            'message': {
                'content': 'Hello! I\'m AURA, your AI assistant. I\'m doing well, thank you for asking! How can I help you today?'
            }
        }
        mock_reasoning_module._make_api_request.return_value = mock_api_response
        orchestrator.reasoning_module = mock_reasoning_module
        orchestrator.module_availability['reasoning'] = True
        
        # Mock the feedback module to avoid audio issues during testing
        mock_feedback_module = Mock()
        orchestrator.feedback_module = mock_feedback_module
        orchestrator.module_availability['feedback'] = True
        
        # Test 1: Direct conversational query handler
        logger.info("Test 1: Testing direct conversational query handler...")
        test_query = "Hello AURA, how are you today?"
        execution_id = "test_direct_001"
        
        result = orchestrator._handle_conversational_query(execution_id, test_query)
        
        # Verify the result structure
        assert result is not None, "Result should not be None"
        assert result.get('success') is True, f"Expected success=True, got {result.get('success')}"
        assert result.get('mode') == 'conversational_chat', f"Expected mode='conversational_chat', got {result.get('mode')}"
        assert result.get('response') is not None, "Response should not be None"
        assert result.get('audio_feedback_provided') is True, "Audio feedback should be provided"
        
        logger.info(f"✓ Test 1 passed. Response: {result.get('response')}")
        
        # Test 2: Verify reasoning module integration
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
        
        # Test 4: Test different response formats
        logger.info("Test 4: Testing different API response formats...")
        
        # Test OpenAI format
        openai_response = {
            'choices': [{
                'message': {
                    'content': 'This is an OpenAI format response'
                }
            }]
        }
        
        mock_reasoning_module._make_api_request.return_value = openai_response
        mock_reasoning_module._make_api_request.reset_mock()
        mock_feedback_module.speak.reset_mock()
        
        result_openai = orchestrator._handle_conversational_query("test_openai", "Test OpenAI format")
        
        assert result_openai.get('success') is True, "OpenAI format should work"
        assert result_openai.get('response') == 'This is an OpenAI format response', "Should extract OpenAI response correctly"
        
        # Test direct response format
        direct_response = {
            'response': 'This is a direct response format'
        }
        
        mock_reasoning_module._make_api_request.return_value = direct_response
        mock_reasoning_module._make_api_request.reset_mock()
        mock_feedback_module.speak.reset_mock()
        
        result_direct = orchestrator._handle_conversational_query("test_direct", "Test direct format")
        
        assert result_direct.get('success') is True, "Direct format should work"
        assert result_direct.get('response') == 'This is a direct response format', "Should extract direct response correctly"
        
        logger.info("✓ Test 4 passed. Different response formats handled correctly")
        
        # Test 5: Test error handling
        logger.info("Test 5: Testing error handling...")
        
        # Test with reasoning module unavailable
        orchestrator.module_availability['reasoning'] = False
        
        result_error = orchestrator._handle_conversational_query("test_error", "This should use fallback")
        
        assert result_error.get('success') is True, "Should succeed with fallback"
        assert "sorry" in result_error.get('response', '').lower(), "Should provide apologetic fallback response"
        
        # Test with API error
        orchestrator.module_availability['reasoning'] = True
        mock_reasoning_module._make_api_request.side_effect = Exception("Simulated API error")
        
        result_api_error = orchestrator._handle_conversational_query("test_api_error", "This should handle API error")
        
        assert result_api_error.get('success') is False, "Should indicate failure for API error"
        assert len(result_api_error.get('errors', [])) > 0, "Should have error information"
        
        logger.info("✓ Test 5 passed. Error handling works correctly")
        
        logger.info("🎉 All direct conversational handler tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_helper_methods_isolated():
    """Test the helper methods in isolation."""
    
    try:
        from orchestrator import Orchestrator
        
        logger.info("Testing helper methods in isolation...")
        orchestrator = Orchestrator()
        
        # Test _extract_conversational_response
        logger.info("Testing _extract_conversational_response...")
        
        # Test various response formats
        test_cases = [
            # Ollama format
            ({
                'message': {
                    'content': 'Ollama response content'
                }
            }, 'Ollama response content'),
            
            # OpenAI format
            ({
                'choices': [{
                    'message': {
                        'content': 'OpenAI response content'
                    }
                }]
            }, 'OpenAI response content'),
            
            # Direct response format
            ({
                'response': 'Direct response content'
            }, 'Direct response content'),
            
            # Simple content format
            ({
                'content': 'Simple content response'
            }, 'Simple content response')
        ]
        
        for i, (response_format, expected_content) in enumerate(test_cases):
            logger.info(f"Testing response format {i+1}...")
            extracted = orchestrator._extract_conversational_response(response_format)
            assert extracted == expected_content, f"Format {i+1} extraction failed: expected '{expected_content}', got '{extracted}'"
        
        logger.info("✓ Response extraction tests passed")
        
        # Test _update_conversation_history
        logger.info("Testing _update_conversation_history...")
        
        initial_length = len(orchestrator.conversation_history)
        
        orchestrator._update_conversation_history("Test user input", "Test assistant response")
        
        assert len(orchestrator.conversation_history) == initial_length + 1, "History should be updated"
        
        latest_entry = orchestrator.conversation_history[-1]
        assert latest_entry == ("Test user input", "Test assistant response"), "History entry should match input"
        
        logger.info("✓ Conversation history tests passed")
        
        # Test _process_conversational_query_with_reasoning
        logger.info("Testing _process_conversational_query_with_reasoning...")
        
        # Mock the reasoning module
        mock_reasoning_module = Mock()
        mock_api_response = {
            'message': {
                'content': 'Test reasoning response'
            }
        }
        mock_reasoning_module._make_api_request.return_value = mock_api_response
        orchestrator.reasoning_module = mock_reasoning_module
        
        response = orchestrator._process_conversational_query_with_reasoning("test_reasoning", "Test query")
        
        assert response == 'Test reasoning response', f"Expected 'Test reasoning response', got '{response}'"
        mock_reasoning_module._make_api_request.assert_called_once()
        
        logger.info("✓ Reasoning integration tests passed")
        
        logger.info("🎉 All helper method tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Helper method tests failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    logger.info("Starting simple conversational handler tests...")
    
    # Run direct handler tests
    direct_tests_passed = test_conversational_handler_direct()
    
    # Run helper method tests
    helper_tests_passed = test_helper_methods_isolated()
    
    if direct_tests_passed and helper_tests_passed:
        logger.info("🎉 All simple conversational handler tests completed successfully!")
        sys.exit(0)
    else:
        logger.error("❌ Some tests failed. Please check the implementation.")
        sys.exit(1)