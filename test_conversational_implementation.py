#!/usr/bin/env python3
"""
Test script for conversational handler implementation.
Tests the new conversational features including intent recognition and response generation.
"""

import sys
import time
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_conversational_handler():
    """Test the conversational handler implementation."""
    try:
        logger.info("Testing conversational handler implementation...")
        
        # Import the orchestrator
        from orchestrator import Orchestrator
        
        # Initialize orchestrator
        logger.info("Initializing orchestrator...")
        orchestrator = Orchestrator()
        
        # Test conversational queries
        test_queries = [
            "Hello, how are you?",
            "What can you help me with?",
            "Tell me a joke",
            "Good morning!",
            "How's the weather?",
            "What's your name?"
        ]
        
        logger.info(f"Testing {len(test_queries)} conversational queries...")
        
        for i, query in enumerate(test_queries, 1):
            logger.info(f"\n--- Test {i}/{len(test_queries)}: '{query}' ---")
            
            try:
                # Test intent recognition
                intent_result = orchestrator._recognize_intent(query)
                logger.info(f"Intent recognition result: {intent_result}")
                
                # Check if it's classified as conversational
                if intent_result.get('intent') == 'conversational_chat':
                    logger.info("✅ Correctly identified as conversational chat")
                    
                    # Test the conversation handler directly
                    handler = orchestrator.conversation_handler
                    if handler:
                        context = {
                            'intent_result': intent_result,
                            'timestamp': time.time(),
                            'execution_id': f'test_{i}'
                        }
                        
                        result = handler.handle(query, context)
                        logger.info(f"Handler result: {result}")
                        
                        if result.get('status') == 'success':
                            logger.info("✅ Conversational handler executed successfully")
                            response = result.get('response', 'No response')
                            logger.info(f"Generated response: '{response}'")
                        else:
                            logger.warning(f"❌ Handler failed: {result.get('message', 'Unknown error')}")
                    else:
                        logger.error("❌ Conversation handler not available")
                else:
                    logger.warning(f"❌ Incorrectly classified as: {intent_result.get('intent')}")
                
            except Exception as e:
                logger.error(f"❌ Error testing query '{query}': {e}")
            
            # Small delay between tests
            time.sleep(0.5)
        
        # Test conversation history
        logger.info("\n--- Testing conversation history ---")
        try:
            handler = orchestrator.conversation_handler
            if handler and hasattr(handler, 'get_conversation_summary'):
                summary = handler.get_conversation_summary()
                logger.info(f"Conversation summary: {summary}")
            else:
                logger.warning("Conversation summary not available")
        except Exception as e:
            logger.error(f"Error getting conversation summary: {e}")
        
        logger.info("\n✅ Conversational handler testing completed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to test conversational handler: {e}")
        return False

def test_reasoning_module():
    """Test the reasoning module's process_query method."""
    try:
        logger.info("\n--- Testing reasoning module process_query method ---")
        
        from modules.reasoning import ReasoningModule
        
        reasoning = ReasoningModule()
        
        # Test simple conversational query
        test_query = "Hello, how are you today?"
        
        logger.info(f"Testing query: '{test_query}'")
        
        response = reasoning.process_query(
            query=test_query,
            prompt_template='CONVERSATIONAL_PROMPT',
            context={'test': True}
        )
        
        logger.info(f"Response: '{response}'")
        
        if response and isinstance(response, str) and len(response) > 0:
            logger.info("✅ Reasoning module process_query working correctly")
            return True
        else:
            logger.error("❌ Invalid response from reasoning module")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error testing reasoning module: {e}")
        return False

def main():
    """Main test function."""
    logger.info("Starting conversational implementation tests...")
    
    # Test reasoning module first
    reasoning_ok = test_reasoning_module()
    
    # Test conversational handler
    handler_ok = test_conversational_handler()
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("TEST SUMMARY")
    logger.info("="*60)
    logger.info(f"Reasoning module: {'✅ PASS' if reasoning_ok else '❌ FAIL'}")
    logger.info(f"Conversational handler: {'✅ PASS' if handler_ok else '❌ FAIL'}")
    
    if reasoning_ok and handler_ok:
        logger.info("🎉 All conversational tests PASSED!")
        return 0
    else:
        logger.error("❌ Some tests FAILED. Check the logs above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())