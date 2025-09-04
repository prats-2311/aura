#!/usr/bin/env python3
"""
Detailed debugging of accessibility module initialization
"""

import logging
import sys

# Enable debug logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(name)s - %(message)s')

print("🔍 Debugging Accessibility Module Initialization...")

# Check what's available at import time
print("\n1. Checking imports...")
try:
    import AppKit
    print("✓ AppKit imported successfully")
except ImportError as e:
    print(f"✗ AppKit import failed: {e}")

try:
    import Accessibility
    print("✓ Accessibility imported successfully")
except ImportError as e:
    print(f"✗ Accessibility import failed: {e}")

try:
    from ApplicationServices import AXUIElementCreateSystemWide
    print("✓ ApplicationServices functions imported successfully")
    FUNCTIONS_AVAILABLE = True
except ImportError as e:
    print(f"✗ ApplicationServices import failed: {e}")
    FUNCTIONS_AVAILABLE = False

print(f"\n2. ACCESSIBILITY_FUNCTIONS_AVAILABLE should be: {FUNCTIONS_AVAILABLE}")

# Now test the actual module
print("\n3. Testing AccessibilityModule...")
try:
    from modules.accessibility import AccessibilityModule, ACCESSIBILITY_FUNCTIONS_AVAILABLE
    print(f"✓ Module imported, ACCESSIBILITY_FUNCTIONS_AVAILABLE = {ACCESSIBILITY_FUNCTIONS_AVAILABLE}")
    
    # Create instance with detailed logging
    print("\n4. Creating AccessibilityModule instance...")
    accessibility = AccessibilityModule()
    
    print("\n5. Module status:")
    status = accessibility.get_accessibility_status()
    for key, value in status.items():
        print(f"   {key}: {value}")
    
    # Try to manually test the system-wide element creation
    print("\n6. Manual test of system-wide element creation...")
    if FUNCTIONS_AVAILABLE:
        try:
            from ApplicationServices import AXUIElementCreateSystemWide
            system_wide = AXUIElementCreateSystemWide()
            print(f"✓ System-wide element created: {system_wide}")
            
            # Try to get focused application
            try:
                import AppKit
                focused_app_ref = AppKit.AXUIElementCopyAttributeValue(
                    system_wide, 
                    AppKit.kAXFocusedApplicationAttribute, 
                    None
                )
                print(f"✓ Focused app reference: {focused_app_ref}")
            except Exception as e:
                print(f"✗ Failed to get focused app: {e}")
                
        except Exception as e:
            print(f"✗ System-wide element creation failed: {e}")
    else:
        print("⚠ Functions not available, skipping manual test")

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()