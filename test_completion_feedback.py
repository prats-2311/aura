#!/usr/bin/env python3
"""
Test script for completion feedback in deferred actions.
"""

import sys
import logging
import time
import threading

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_completion_feedback():
    """Test that completion feedback is provided after deferred action completes."""
    try:
        logger.info("Testing completion feedback...")
        
        from orchestrator import Orchestrator
        from handlers.deferred_action_handler import DeferredActionHandler
        
        # Initialize orchestrator
        orchestrator = Orchestrator()
        
        # Get the deferred action handler
        handler = orchestrator.deferred_action_handler
        
        # Test the completion feedback method directly
        logger.info("Testing completion feedback methods...")
        
        # Test success feedback
        logger.info("Testing success feedback...")
        handler._provide_completion_feedback("test_exec_1", True)
        
        # Wait a moment for audio to play
        time.sleep(2)
        
        # Test failure feedback
        logger.info("Testing failure feedback...")
        handler._provide_completion_feedback("test_exec_2", False)
        
        # Wait a moment for audio to play
        time.sleep(2)
        
        logger.info("✅ Completion feedback test completed!")
        logger.info("Check if you heard 'Content placed successfully' and 'Failed to place content' messages")
        
        return True
            
    except Exception as e:
        logger.error(f"❌ Test failed with exception: {e}")
        return False

def test_audio_instructions():
    """Test that audio instructions are provided."""
    try:
        logger.info("Testing audio instructions...")
        
        from orchestrator import Orchestrator
        
        # Initialize orchestrator
        orchestrator = Orchestrator()
        
        # Get the deferred action handler
        handler = orchestrator.deferred_action_handler
        
        # Test the audio instructions method directly
        logger.info("Testing audio instructions for code...")
        handler._provide_audio_instructions("code", "test_exec_3")
        
        # Wait a moment for audio to play
        time.sleep(3)
        
        logger.info("Testing audio instructions for text...")
        handler._provide_audio_instructions("text", "test_exec_4")
        
        # Wait a moment for audio to play
        time.sleep(3)
        
        logger.info("✅ Audio instructions test completed!")
        logger.info("Check if you heard the instruction messages")
        
        return True
            
    except Exception as e:
        logger.error(f"❌ Test failed with exception: {e}")
        return False

if __name__ == "__main__":
    logger.info("Starting audio feedback tests...")
    
    # Test audio instructions
    instructions_ok = test_audio_instructions()
    
    # Test completion feedback
    completion_ok = test_completion_feedback()
    
    logger.info("\n" + "="*60)
    logger.info("TEST SUMMARY")
    logger.info("="*60)
    logger.info(f"Audio instructions: {'✅ PASS' if instructions_ok else '❌ FAIL'}")
    logger.info(f"Completion feedback: {'✅ PASS' if completion_ok else '❌ FAIL'}")
    
    if instructions_ok and completion_ok:
        logger.info("🎉 All audio feedback tests completed!")
        sys.exit(0)
    else:
        logger.error("❌ Some tests failed. Check the logs above for details.")
        sys.exit(1)