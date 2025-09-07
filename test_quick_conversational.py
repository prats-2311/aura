#!/usr/bin/env python3
"""
Quick test for conversational integration fix.
"""

import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_quick_conversational():
    """Quick test of conversational integration."""
    try:
        logger.info("Testing conversational integration fix...")
        
        from orchestrator import Orchestrator
        
        # Initialize orchestrator
        orchestrator = Orchestrator()
        
        # Test a simple conversational command
        command = "Hello, how are you?"
        logger.info(f"Testing command: '{command}'")
        
        result = orchestrator.execute_command(command)
        
        logger.info(f"Result status: {result.get('status')}")
        logger.info(f"Result success: {result.get('success')}")
        
        if result.get('response'):
            logger.info(f"Response: '{result['response']}'")
        
        if result.get('interaction_type'):
            logger.info(f"Interaction type: {result['interaction_type']}")
        
        if result.get('status') == 'completed' and result.get('success'):
            logger.info("✅ Conversational integration working correctly!")
            return True
        else:
            logger.error(f"❌ Test failed: {result}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Test failed with exception: {e}")
        return False

if __name__ == "__main__":
    success = test_quick_conversational()
    sys.exit(0 if success else 1)