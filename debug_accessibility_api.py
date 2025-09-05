#!/usr/bin/env python3
"""
Debug accessibility API availability.
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def debug_accessibility_api():
    """Debug accessibility API availability."""
    
    print("Debugging Accessibility API Availability...")
    print("="*50)
    
    # Check AppKit availability
    try:
        from AppKit import NSWorkspace, NSApplication
        print("✅ AppKit available")
        APPKIT_AVAILABLE = True
    except ImportError as e:
        print(f"❌ AppKit not available: {e}")
        APPKIT_AVAILABLE = False
    
    # Check ApplicationServices availability
    try:
        from ApplicationServices import (
            AXUIElementCreateSystemWide,
            AXUIElementCreateApplication,
            AXUIElementCopyAttributeValue,
            kAXFocusedApplicationAttribute,
            kAXRoleAttribute,
            kAXTitleAttribute,
            kAXDescriptionAttribute,
            kAXEnabledAttribute,
            kAXChildrenAttribute,
            kAXPositionAttribute,
            kAXSizeAttribute
        )
        print("✅ ApplicationServices available")
        ACCESSIBILITY_FUNCTIONS_AVAILABLE = True
    except ImportError as e:
        print(f"❌ ApplicationServices not available: {e}")
        
        # Try fallback
        try:
            import objc
            print("✅ objc available, trying bundle load...")
            bundle = objc.loadBundle('ApplicationServices', globals())
            ACCESSIBILITY_FUNCTIONS_AVAILABLE = 'AXUIElementCreateSystemWide' in globals()
            print(f"Bundle load result: {ACCESSIBILITY_FUNCTIONS_AVAILABLE}")
        except Exception as e2:
            print(f"❌ objc fallback failed: {e2}")
            ACCESSIBILITY_FUNCTIONS_AVAILABLE = False
    
    # Check thefuzz availability
    try:
        from thefuzz import fuzz
        print("✅ thefuzz available")
        FUZZY_MATCHING_AVAILABLE = True
    except ImportError as e:
        print(f"❌ thefuzz not available: {e}")
        FUZZY_MATCHING_AVAILABLE = False
    
    # Overall availability
    ACCESSIBILITY_AVAILABLE = APPKIT_AVAILABLE and ACCESSIBILITY_FUNCTIONS_AVAILABLE
    
    print(f"\nOverall Results:")
    print(f"APPKIT_AVAILABLE: {APPKIT_AVAILABLE}")
    print(f"ACCESSIBILITY_FUNCTIONS_AVAILABLE: {ACCESSIBILITY_FUNCTIONS_AVAILABLE}")
    print(f"FUZZY_MATCHING_AVAILABLE: {FUZZY_MATCHING_AVAILABLE}")
    print(f"ACCESSIBILITY_AVAILABLE: {ACCESSIBILITY_AVAILABLE}")
    
    if ACCESSIBILITY_AVAILABLE:
        print("\n✅ Accessibility API should be working!")
        
        # Test basic functionality
        try:
            system_wide = AXUIElementCreateSystemWide()
            if system_wide:
                print("✅ Can create system-wide accessibility element")
            else:
                print("❌ Cannot create system-wide accessibility element")
        except Exception as e:
            print(f"❌ Error creating system-wide element: {e}")
    else:
        print("\n❌ Accessibility API is not available!")
        
        if not APPKIT_AVAILABLE:
            print("Install AppKit: pip install pyobjc-framework-AppKit")
        if not ACCESSIBILITY_FUNCTIONS_AVAILABLE:
            print("Install ApplicationServices: pip install pyobjc-framework-ApplicationServices")

if __name__ == "__main__":
    debug_accessibility_api()