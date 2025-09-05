#!/usr/bin/env python3
"""
Test enhanced role detection in the actual runtime context.
"""

import sys
import os
import logging

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up logging to see debug messages
logging.basicConfig(level=logging.DEBUG)

def test_runtime_enhanced_detection():
    """Test enhanced role detection in the orchestrator context."""
    
    try:
        from orchestrator import Orchestrator
        
        print("Testing enhanced role detection in runtime context...")
        
        # Initialize orchestrator (this is what AURA does)
        orchestrator = Orchestrator()
        
        # Get the accessibility module from orchestrator
        accessibility = orchestrator.accessibility_module
        
        print(f"Accessibility module: {accessibility}")
        print(f"Enhanced role detection available: {accessibility.is_enhanced_role_detection_available()}")
        
        # Test the find_element_enhanced method directly
        print("\nTesting find_element_enhanced method:")
        
        # This should trigger the enhanced role detection
        result = accessibility.find_element_enhanced('', 'google search button')
        
        print(f"Result: {result}")
        print(f"Found: {result.found}")
        print(f"Fallback triggered: {result.fallback_triggered}")
        
        return True
        
    except Exception as e:
        print(f"Error testing runtime enhanced detection: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_runtime_enhanced_detection()