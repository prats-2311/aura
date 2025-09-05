#!/usr/bin/env python3
"""
Integration test for conversational query handler with full orchestrator flow.

This script tests the complete flow from command execution through intent recognition
to conversational handling, ensuring the new functionality integrates properly with
the existing orchestrator architecture.
"""

import sys
import logging
import time
from unittest.mock import Mock, patch, MagicMock

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_full_conversational_flow():
    """Test the complete conversational flow through the orchestrator."""
    
    try:
        # Import the orchestrator
        from orchestrator import Orchestrator
        
        logger.info("Creating orchestrator instance for integration test...")
        orchestrator = Orchestrator()
        
        # Mock the reasoning module for both intent recognition and conversational responses
        mock_reasoning_module = Mock()
        
        # Mock intent recognition response (conversational_chat intent)
        mock_intent_response = {
            'message': {
                'content': '{"intent": "conversational_chat", "confidence": 0.95, "parameters": {}}'
            }
        }
        
        # Mock conversational response
        mock_conversational_response = {
            'message': {
                'content': 'Hello! I\'m AURA, your helpful AI assistant. I\'m doing great, thank you for asking! How can I assist you today?'
            }
        }
        
        # Set up the mock to return different responses based on the prompt content
        def mock_api_request(prompt):
            if "Intent categories:" in prompt:
                # This is an intent recognition request
                return mock_intent_response
            else:
                # This is a conversational request
                return mock_conversational_response
        
        mock_reasoning_module._make_api_request.side_effect = mock_api_request
        orchestrator.reasoning_module = mock_reasoning_module
        orchestrator.module_availability['reasoning'] = True
        
        # Mock the feedback module to avoid audio issues during testing
        mock_feedback_module = Mock()
        orchestrator.feedback_module = mock_feedback_module
        orchestrator.module_availability['feedback'] = True
        
        # Test 1: Full conversational flow through execute_command
        logger.info("Test 1: Testing full conversational flow through execute_command...")
        
        conversational_query = "Hello AURA, how are you doing today?"
        
        result = orchestrator.execute_command(conversational_query)
        
        # Verify the result structure
        assert result is not None, "Result should not be None"
        assert result.get('success') is True, f"Expected success=True, got {result.get('success')}"
        assert result.get('mode') == 'conversational_chat', f"Expected mode='conversational_chat', got {result.get('mode')}"
        assert result.get('response') is not None, "Response should not be None"
        assert result.get('audio_feedback_provided') is True, "Audio feedback should be provided"
        
        # Verify the response content
        response = result.get('response')
        assert "AURA" in response, "Response should mention AURA"
        assert len(response) > 10, "Response should be substantial"
        
        logger.info(f"✓ Test 1 passed. Full flow response: {response}")
        
        # Test 2: Verify intent recognition was called
        logger.info("Test 2: Verifying intent recognition integration...")
        
        # Check that _make_api_request was called multiple times (once for intent, once for response)
        assert mock_reasoning_module._make_api_request.call_count >= 2, "Should call API for both intent and response"
        
        # Check the calls
        call_args_list = mock_reasoning_module._make_api_request.call_args_list
        
        # First call should be intent recognition
        first_call_prompt = call_args_list[0][0][0]
        assert "Intent categories:" in first_call_prompt, "First call should be intent recognition"
        assert conversational_query in first_call_prompt, "Intent prompt should contain user query"
        
        # Second call should be conversational
        second_call_prompt = call_args_list[1][0][0]
        assert "AURA" in second_call_prompt, "Second call should be conversational prompt"
        assert conversational_query in second_call_prompt, "Conversational prompt should contain user query"
        
        logger.info("✓ Test 2 passed. Intent recognition and routing working correctly")
        
        # Test 3: Test different conversational queries
        logger.info("Test 3: Testing various conversational queries...")
        
        test_queries = [
            "What's your favorite color?",
            "Tell me a joke",
            "How's the weather?",
            "What can you help me with?",
            "Nice to meet you!"
        ]
        
        for i, query in enumerate(test_queries):
            logger.info(f"Testing query {i+1}: '{query}'")
            
            # Reset mock call count
            mock_reasoning_module._make_api_request.reset_mock()
            mock_reasoning_module._make_api_request.side_effect = mock_api_request
            
            result = orchestrator.execute_command(query)
            
            assert result.get('success') is True, f"Query '{query}' should succeed"
            assert result.get('mode') == 'conversational_chat', f"Query '{query}' should be conversational"
            assert result.get('response') is not None, f"Query '{query}' should have response"
            
        logger.info("✓ Test 3 passed. Various conversational queries handled correctly")
        
        # Test 4: Test conversation history tracking
        logger.info("Test 4: Testing conversation history tracking...")
        
        initial_history_length = len(orchestrator.conversation_history)
        
        # Execute a few conversational commands
        orchestrator.execute_command("Hello there!")
        orchestrator.execute_command("How are you?")
        orchestrator.execute_command("What's your name?")
        
        final_history_length = len(orchestrator.conversation_history)
        
        # Should have 3 new entries (plus any from previous tests)
        expected_new_entries = 3
        actual_new_entries = final_history_length - initial_history_length
        
        assert actual_new_entries >= expected_new_entries, f"Expected at least {expected_new_entries} new history entries, got {actual_new_entries}"
        
        # Check the latest entries
        recent_entries = orchestrator.conversation_history[-3:]
        
        for entry in recent_entries:
            assert len(entry) == 2, "Each history entry should have user query and assistant response"
            assert isinstance(entry[0], str), "User query should be string"
            assert isinstance(entry[1], str), "Assistant response should be string"
            assert len(entry[0]) > 0, "User query should not be empty"
            assert len(entry[1]) > 0, "Assistant response should not be empty"
        
        logger.info("✓ Test 4 passed. Conversation history tracking working correctly")
        
        # Test 5: Test error handling in full flow
        logger.info("Test 5: Testing error handling in full conversational flow...")
        
        # Simulate reasoning module failure
        mock_reasoning_module._make_api_request.side_effect = Exception("Simulated API failure")
        
        result = orchestrator.execute_command("This should fail gracefully")
        
        # Should still return a result, but with error handling
        assert result is not None, "Should return result even with API failure"
        assert result.get('success') is False, "Should indicate failure"
        assert len(result.get('errors', [])) > 0, "Should have error information"
        
        logger.info("✓ Test 5 passed. Error handling working correctly in full flow")
        
        logger.info("🎉 All integration tests passed! Conversational handler is fully integrated.")
        return True
        
    except Exception as e:
        logger.error(f"❌ Integration test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_conversational_vs_gui_routing():
    """Test that conversational queries are properly distinguished from GUI commands."""
    
    try:
        from orchestrator import Orchestrator
        
        logger.info("Testing conversational vs GUI command routing...")
        orchestrator = Orchestrator()
        
        # Mock the reasoning module for intent recognition
        mock_reasoning_module = Mock()
        orchestrator.reasoning_module = mock_reasoning_module
        orchestrator.module_availability['reasoning'] = True
        
        # Mock feedback module
        mock_feedback_module = Mock()
        orchestrator.feedback_module = mock_feedback_module
        orchestrator.module_availability['feedback'] = True
        
        # Test conversational queries (should route to conversational handler)
        conversational_queries = [
            "Hello, how are you?",
            "What's your favorite movie?",
            "Tell me about yourself",
            "Nice weather today, isn't it?",
            "What can you do for me?"
        ]
        
        # Mock intent response for conversational queries
        conversational_intent_response = {
            'message': {
                'content': '{"intent": "conversational_chat", "confidence": 0.95, "parameters": {}}'
            }
        }
        
        # Mock conversational response
        conversational_response = {
            'message': {
                'content': 'I\'m doing great, thank you for asking!'
            }
        }
        
        def mock_conversational_api_request(prompt):
            if "Intent categories:" in prompt:
                return conversational_intent_response
            else:
                return conversational_response
        
        mock_reasoning_module._make_api_request.side_effect = mock_conversational_api_request
        
        for query in conversational_queries:
            logger.info(f"Testing conversational query: '{query}'")
            
            # Reset mock
            mock_reasoning_module._make_api_request.reset_mock()
            mock_reasoning_module._make_api_request.side_effect = mock_conversational_api_request
            
            result = orchestrator.execute_command(query)
            
            assert result.get('mode') == 'conversational_chat', f"Query '{query}' should be routed to conversational handler"
            assert result.get('success') is True, f"Conversational query '{query}' should succeed"
        
        logger.info("✓ Conversational queries properly routed to conversational handler")
        
        # Test GUI commands (should route to GUI handler)
        gui_commands = [
            "click on the submit button",
            "type hello world",
            "scroll down",
            "press the enter key",
            "find the search box"
        ]
        
        # Mock intent response for GUI commands
        gui_intent_response = {
            'message': {
                'content': '{"intent": "gui_interaction", "confidence": 0.90, "parameters": {}}'
            }
        }
        
        def mock_gui_api_request(prompt):
            return gui_intent_response
        
        # Mock the GUI handler to avoid actual GUI operations
        original_gui_handler = orchestrator._handle_gui_interaction
        mock_gui_result = {
            'execution_id': 'test_gui',
            'command': 'test',
            'status': 'completed',
            'success': True,
            'mode': 'gui_interaction',
            'duration': 0.1,
            'steps_completed': [],
            'metadata': {}
        }
        orchestrator._handle_gui_interaction = Mock(return_value=mock_gui_result)
        
        mock_reasoning_module._make_api_request.side_effect = mock_gui_api_request
        
        for command in gui_commands:
            logger.info(f"Testing GUI command: '{command}'")
            
            # Reset mock
            mock_reasoning_module._make_api_request.reset_mock()
            mock_reasoning_module._make_api_request.side_effect = mock_gui_api_request
            
            result = orchestrator.execute_command(command)
            
            # Should be routed to GUI handler
            orchestrator._handle_gui_interaction.assert_called()
            
        logger.info("✓ GUI commands properly routed to GUI handler")
        
        # Restore original GUI handler
        orchestrator._handle_gui_interaction = original_gui_handler
        
        logger.info("🎉 All routing tests passed! Intent-based routing working correctly.")
        return True
        
    except Exception as e:
        logger.error(f"❌ Routing test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    logger.info("Starting conversational integration tests...")
    
    # Run full flow tests
    full_flow_passed = test_full_conversational_flow()
    
    # Run routing tests
    routing_passed = test_conversational_vs_gui_routing()
    
    if full_flow_passed and routing_passed:
        logger.info("🎉 All conversational integration tests completed successfully!")
        sys.exit(0)
    else:
        logger.error("❌ Some integration tests failed. Please check the implementation.")
        sys.exit(1)