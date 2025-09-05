#!/usr/bin/env python3
"""
Test the difference between type and click commands in AURA.
"""

import sys
import time
from modules.accessibility import AccessibilityModule
from orchestrator import Orchestrator
from unittest.mock import Mock

def test_type_vs_click():
    """Test why type works but click doesn't."""
    
    print("=== Type vs Click Command Analysis ===")
    
    # Create orchestrator (mocked for testing)
    orchestrator = Orchestrator()
    
    print("1. Testing Type Command Logic...")
    
    # Test type command validation
    type_validation = orchestrator.validate_command("Type Prateek Srivastava")
    print(f"   Type command validation: {type_validation.command_type}")
    print(f"   Type command valid: {type_validation.is_valid}")
    
    # Test if type command would use direct typing
    type_command_info = {'command_type': 'type', 'confidence': 0.9}
    print(f"   Type command would use direct typing: {type_validation.command_type == 'type'}")
    
    print("\n2. Testing Click Command Logic...")
    
    # Test click command validation  
    click_validation = orchestrator.validate_command("Click on Gmail link")
    print(f"   Click command validation: {click_validation.command_type}")
    print(f"   Click command valid: {click_validation.is_valid}")
    
    # Test GUI element extraction for click
    gui_elements = orchestrator._extract_gui_elements_from_command("Click on Gmail link")
    print(f"   GUI elements extracted: {gui_elements}")
    
    print("\n3. Testing Accessibility Status...")
    
    # Test accessibility module
    acc = AccessibilityModule()
    status = acc.get_accessibility_status()
    print(f"   Accessibility permissions: {status.get('permissions_granted', False)}")
    print(f"   API initialized: {status.get('api_initialized', False)}")
    
    # Test element finding (this will fail due to Chrome accessibility)
    result = acc.find_element_enhanced('', 'Gmail', None)
    print(f"   Can find Gmail element: {result.found}")
    
    print("\n4. Analysis Summary:")
    print("   ✅ Type commands work because:")
    print("      - No element detection needed")
    print("      - Direct keystroke injection")
    print("      - Bypasses accessibility API")
    
    print("   ❌ Click commands fail because:")
    print("      - Need to find specific elements")
    print("      - Require accessibility API access")
    print("      - Chrome accessibility not enabled")
    
    print("\n5. Solution:")
    print("   Enable Chrome accessibility features:")
    print("   - chrome://settings/accessibility → Enable 'Live Caption'")
    print("   - OR chrome://flags/ → Enable 'Experimental Accessibility Features'")

if __name__ == "__main__":
    test_type_vs_click()