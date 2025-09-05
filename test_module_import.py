#!/usr/bin/env python3
"""
Test module import to see what's happening.
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_module_import():
    """Test importing the accessibility module."""
    
    print("Testing module import...")
    
    try:
        # Import the module and check the availability flags
        import modules.accessibility as acc_module
        
        print(f"APPKIT_AVAILABLE: {acc_module.APPKIT_AVAILABLE}")
        print(f"ACCESSIBILITY_FUNCTIONS_AVAILABLE: {acc_module.ACCESSIBILITY_FUNCTIONS_AVAILABLE}")
        print(f"ACCESSIBILITY_AVAILABLE: {acc_module.ACCESSIBILITY_AVAILABLE}")
        print(f"FUZZY_MATCHING_AVAILABLE: {acc_module.FUZZY_MATCHING_AVAILABLE}")
        
        if acc_module.ACCESSIBILITY_AVAILABLE:
            print("✅ Module reports accessibility available")
            
            # Try to create the module
            try:
                accessibility = acc_module.AccessibilityModule()
                print("✅ AccessibilityModule created successfully")
                
                # Check if it's in degraded mode
                print(f"Degraded mode: {accessibility.degraded_mode}")
                print(f"Accessibility enabled: {accessibility.accessibility_enabled}")
                
            except Exception as e:
                print(f"❌ Error creating AccessibilityModule: {e}")
        else:
            print("❌ Module reports accessibility not available")
            
    except Exception as e:
        print(f"❌ Error importing module: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_module_import()