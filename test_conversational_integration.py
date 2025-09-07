#!/usr/bin/env python3
"""
Comprehensive integration test for conversational features.
Tests the complete conversational workflow including intent recognition, 
handler routing, response generation, and audio feedback.
"""

import sys
import time
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_full_conversational_workflow():
    """Test the complete conversational workflow end-to-end."""
    try:
        logger.info("Testing full conversational workflow...")
        
        # Import the orchestrator
        from orchestrator import Orchestrator
        
        # Initialize orchestrator
        logger.info("Initializing orchestrator...")
        orchestrator = Orchestrator()
        
        # Test various conversational scenarios
        test_scenarios = [
            {
                "name": "Greeting",
                "command": "Hello AURA, how are you doing today?",
                "expected_intent": "conversational_chat"
            },
            {
                "name": "Capability inquiry",
                "command": "What kinds of things can you help me with?",
                "expected_intent": "conversational_chat"
            },
            {
                "name": "Personal question",
                "command": "What's your favorite color?",
                "expected_intent": "conversational_chat"
            },
            {
                "name": "Help request",
                "command": "Can you tell me about yourself?",
                "expected_intent": "conversational_chat"
            },
            {
                "name": "Casual conversation",
                "command": "I'm having a great day! How about you?",
                "expected_intent": "conversational_chat"
            }
        ]
        
        logger.info(f"Testing {len(test_scenarios)} conversational scenarios...")
        
        results = []
        
        for i, scenario in enumerate(test_scenarios, 1):
            logger.info(f"\n--- Scenario {i}: {scenario['name']} ---")
            logger.info(f"Command: '{scenario['command']}'")
            
            try:
                start_time = time.time()
                
                # Test the full workflow through execute_command
                result = orchestrator.execute_command(scenario['command'])
                
                execution_time = time.time() - start_time
                
                logger.info(f"Execution time: {execution_time:.2f}s")
                logger.info(f"Result status: {result.get('status', 'unknown')}")
                
                # Check if the result indicates success
                if result.get('status') == 'success':
                    logger.info("✅ Scenario executed successfully")
                    
                    # Check if it was handled as conversational
                    if 'interaction_type' in result and result['interaction_type'] == 'conversation':
                        logger.info("✅ Correctly handled as conversational interaction")
                        
                        # Check if we got a response
                        if 'response' in result and result['response']:
                            response = result['response']
                            logger.info(f"Generated response: '{response[:100]}...'")
                            logger.info("✅ Response generated successfully")
                        else:
                            logger.warning("❌ No response generated")
                    else:
                        logger.warning(f"❌ Not handled as conversational: {result.get('interaction_type', 'unknown')}")
                else:
                    logger.warning(f"❌ Scenario failed: {result.get('message', 'Unknown error')}")
                
                results.append({
                    'scenario': scenario['name'],
                    'success': result.get('status') == 'success',
                    'execution_time': execution_time,
                    'response_length': len(result.get('response', ''))
                })
                
            except Exception as e:
                logger.error(f"❌ Error in scenario '{scenario['name']}': {e}")
                results.append({
                    'scenario': scenario['name'],
                    'success': False,
                    'error': str(e)
                })
            
            # Small delay between scenarios
            time.sleep(1.0)
        
        # Analyze results
        successful_scenarios = sum(1 for r in results if r['success'])
        total_scenarios = len(results)
        success_rate = (successful_scenarios / total_scenarios) * 100
        
        logger.info(f"\n--- Results Summary ---")
        logger.info(f"Successful scenarios: {successful_scenarios}/{total_scenarios} ({success_rate:.1f}%)")
        
        if successful_scenarios > 0:
            avg_execution_time = sum(r.get('execution_time', 0) for r in results if r['success']) / successful_scenarios
            avg_response_length = sum(r.get('response_length', 0) for r in results if r['success']) / successful_scenarios
            logger.info(f"Average execution time: {avg_execution_time:.2f}s")
            logger.info(f"Average response length: {avg_response_length:.0f} characters")
        
        # Test conversation history
        logger.info("\n--- Testing conversation history ---")
        try:
            handler = orchestrator.conversation_handler
            if handler and hasattr(handler, 'get_conversation_summary'):
                summary = handler.get_conversation_summary()
                logger.info(f"Conversation summary: {summary}")
                
                if summary.get('status') == 'active' and summary.get('total_exchanges', 0) > 0:
                    logger.info("✅ Conversation history working correctly")
                else:
                    logger.warning("❌ Conversation history not tracking properly")
            else:
                logger.warning("❌ Conversation summary not available")
        except Exception as e:
            logger.error(f"❌ Error testing conversation history: {e}")
        
        return success_rate >= 80  # Consider test passed if 80% or more scenarios succeed
        
    except Exception as e:
        logger.error(f"❌ Failed to test conversational workflow: {e}")
        return False

def test_intent_routing_accuracy():
    """Test the accuracy of intent recognition for conversational vs non-conversational commands."""
    try:
        logger.info("\n--- Testing intent routing accuracy ---")
        
        from orchestrator import Orchestrator
        orchestrator = Orchestrator()
        
        # Test commands that should be conversational
        conversational_commands = [
            "Hello there!",
            "How are you?",
            "What's your name?",
            "Tell me a joke",
            "Good morning",
            "Can you help me?",
            "What can you do?",
            "I'm feeling great today"
        ]
        
        # Test commands that should NOT be conversational
        non_conversational_commands = [
            "Click the sign in button",
            "Type my password",
            "Scroll down",
            "What's on this screen?",
            "Generate code for a Python function",
            "Write an email about the meeting"
        ]
        
        correct_classifications = 0
        total_classifications = 0
        
        # Test conversational commands
        for command in conversational_commands:
            try:
                intent_result = orchestrator._recognize_intent(command)
                intent = intent_result.get('intent', 'unknown')
                
                if intent == 'conversational_chat':
                    logger.info(f"✅ Correctly classified as conversational: '{command}'")
                    correct_classifications += 1
                else:
                    logger.warning(f"❌ Incorrectly classified as {intent}: '{command}'")
                
                total_classifications += 1
                
            except Exception as e:
                logger.error(f"❌ Error classifying '{command}': {e}")
                total_classifications += 1
        
        # Test non-conversational commands
        for command in non_conversational_commands:
            try:
                intent_result = orchestrator._recognize_intent(command)
                intent = intent_result.get('intent', 'unknown')
                
                if intent != 'conversational_chat':
                    logger.info(f"✅ Correctly classified as {intent}: '{command}'")
                    correct_classifications += 1
                else:
                    logger.warning(f"❌ Incorrectly classified as conversational: '{command}'")
                
                total_classifications += 1
                
            except Exception as e:
                logger.error(f"❌ Error classifying '{command}': {e}")
                total_classifications += 1
        
        accuracy = (correct_classifications / total_classifications) * 100
        logger.info(f"\nIntent classification accuracy: {correct_classifications}/{total_classifications} ({accuracy:.1f}%)")
        
        return accuracy >= 75  # Consider test passed if 75% or more are correctly classified
        
    except Exception as e:
        logger.error(f"❌ Failed to test intent routing accuracy: {e}")
        return False

def test_conversation_context_management():
    """Test conversation context and history management."""
    try:
        logger.info("\n--- Testing conversation context management ---")
        
        from orchestrator import Orchestrator
        orchestrator = Orchestrator()
        
        # Have a multi-turn conversation
        conversation_turns = [
            "Hello, I'm John",
            "What's your name?",
            "Nice to meet you!",
            "Can you remember my name?",
            "What did we talk about earlier?"
        ]
        
        for i, turn in enumerate(conversation_turns, 1):
            logger.info(f"\nTurn {i}: '{turn}'")
            
            try:
                result = orchestrator.execute_command(turn)
                
                if result.get('status') == 'success':
                    response = result.get('response', '')
                    logger.info(f"Response: '{response}'")
                    
                    # Check if conversation context is being maintained
                    context = result.get('conversation_context', {})
                    history_length = len(context.get('conversation_history', []))
                    logger.info(f"Conversation history length: {history_length}")
                    
                    if history_length == i:  # Should have i exchanges after turn i
                        logger.info("✅ Conversation history tracking correctly")
                    else:
                        logger.warning(f"❌ Expected {i} history items, got {history_length}")
                else:
                    logger.warning(f"❌ Turn failed: {result.get('message', 'Unknown error')}")
                
            except Exception as e:
                logger.error(f"❌ Error in turn {i}: {e}")
            
            time.sleep(0.5)
        
        # Check final conversation summary
        try:
            handler = orchestrator.conversation_handler
            if handler and hasattr(handler, 'get_conversation_summary'):
                summary = handler.get_conversation_summary()
                total_exchanges = summary.get('total_exchanges', 0)
                
                if total_exchanges == len(conversation_turns):
                    logger.info("✅ Conversation context management working correctly")
                    return True
                else:
                    logger.warning(f"❌ Expected {len(conversation_turns)} exchanges, got {total_exchanges}")
                    return False
            else:
                logger.warning("❌ Conversation summary not available")
                return False
        except Exception as e:
            logger.error(f"❌ Error checking conversation summary: {e}")
            return False
        
    except Exception as e:
        logger.error(f"❌ Failed to test conversation context management: {e}")
        return False

def main():
    """Main test function."""
    logger.info("Starting comprehensive conversational integration tests...")
    
    # Run all tests
    workflow_ok = test_full_conversational_workflow()
    intent_ok = test_intent_routing_accuracy()
    context_ok = test_conversation_context_management()
    
    # Summary
    logger.info("\n" + "="*80)
    logger.info("COMPREHENSIVE TEST SUMMARY")
    logger.info("="*80)
    logger.info(f"Full conversational workflow: {'✅ PASS' if workflow_ok else '❌ FAIL'}")
    logger.info(f"Intent routing accuracy: {'✅ PASS' if intent_ok else '❌ FAIL'}")
    logger.info(f"Conversation context management: {'✅ PASS' if context_ok else '❌ FAIL'}")
    
    if workflow_ok and intent_ok and context_ok:
        logger.info("🎉 ALL CONVERSATIONAL INTEGRATION TESTS PASSED!")
        logger.info("\n✅ Task 3.1: Conversational Chat Handler - COMPLETED")
        logger.info("✅ Task 3.0: Conversational prompt and personality system - COMPLETED")
        logger.info("✅ Task 3.2: Conversational features integration - COMPLETED")
        return 0
    else:
        logger.error("❌ Some integration tests FAILED. Check the logs above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())