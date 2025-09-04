#!/usr/bin/env python3
"""
Test script to verify the ACCESSIBILITY_FUNCTIONS_AVAILABLE fix
"""

import sys
import logging

# Set up logging to see initialization messages
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

try:
    # Import the fixed accessibility module
    from modules.accessibility import AccessibilityModule, ACCESSIBILITY_FUNCTIONS_AVAILABLE
    
    print(f"✓ Successfully imported AccessibilityModule")
    print(f"✓ ACCESSIBILITY_FUNCTIONS_AVAILABLE = {ACCESSIBILITY_FUNCTIONS_AVAILABLE}")
    
    # Try to initialize the module
    print("\nInitializing AccessibilityModule...")
    accessibility = AccessibilityModule()
    
    # Check the status
    status = accessibility.get_accessibility_status()
    print(f"\nAccessibility Status:")
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    # Test if it's working
    if accessibility.is_accessibility_enabled():
        print("\n✓ AccessibilityModule is fully functional!")
        
        # Try to get active application
        app = accessibility.get_active_application()
        if app:
            print(f"✓ Active application: {app['name']} (PID: {app['pid']})")
        else:
            print("⚠ Could not get active application (may need permissions)")
    else:
        print(f"\n⚠ AccessibilityModule is in degraded mode")
        print("This means the system will fall back to vision-based automation")
    
    print(f"\nTest completed successfully!")
    
except Exception as e:
    print(f"✗ Error during test: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)