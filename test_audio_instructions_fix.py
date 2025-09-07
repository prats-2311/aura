#!/usr/bin/env python3
"""
Test script for audio instructions fix in deferred actions.
"""

import sys
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_audio_instructions():
    """Test that audio instructions are provided during deferred actions."""
    try:
        logger.info("Testing audio instructions fix...")
        
        from orchestrator import Orchestrator
        
        # Initialize orchestrator
        orchestrator = Orchestrator()
        
        # Test a code generation command
        command = "Write me a Python function for bubble sort"
        logger.info(f"Testing command: '{command}'")
        
        result = orchestrator.execute_command(command)
        
        logger.info(f"Result status: {result.get('status')}")
        
        if result.get('status') == 'waiting_for_user_action':
            logger.info("✅ Deferred action setup successful!")
            logger.info(f"Content preview: {result.get('content_preview', 'No preview')}")
            logger.info(f"Instructions: {result.get('instructions', 'No instructions')}")
            
            # Wait a moment to see if audio instructions are provided
            logger.info("Waiting 3 seconds to check for audio instructions...")
            time.sleep(3)
            
            logger.info("✅ Test completed - check if you heard audio instructions!")
            return True
        else:
            logger.error(f"❌ Expected waiting_for_user_action status, got: {result.get('status')}")
            if result.get('errors'):
                logger.error(f"Errors: {result['errors']}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Test failed with exception: {e}")
        return False

if __name__ == "__main__":
    success = test_audio_instructions()
    sys.exit(0 if success else 1)