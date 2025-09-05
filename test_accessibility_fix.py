#!/usr/bin/env python3
"""
Test script to verify the accessibility fast path fix.
"""

import sys
import os
import logging

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(level=logging.DEBUG)

def test_accessibility_fix():
    """Test that the accessibility module can now properly detect enhanced role detection."""
    
    try:
        from modules.accessibility import AccessibilityModule
        
        print("Testing accessibility module fix...")
        
        # Initialize the module
        accessibility = AccessibilityModule()
        
        # Test enhanced role detection availability
        enhanced_available = accessibility.is_enhanced_role_detection_available()
        print(f"Enhanced role detection available: {enhanced_available}")
        
        if not enhanced_available:
            print("❌ Enhanced role detection is still not available!")
            return False
        
        # Test clickable role detection
        test_roles = [
            ('AXButton', True),
            ('AXLink', True),
            ('AXMenuItem', True),
            ('AXTextField', False),  # Should not be in clickable roles
            ('AXStaticText', False)  # Should not be in clickable roles
        ]
        
        print("\nTesting clickable role detection:")
        for role, expected in test_roles:
            result = accessibility.is_clickable_element_role(role)
            status = "✅" if result == expected else "❌"
            print(f"{status} {role}: {result} (expected: {expected})")
            if result != expected:
                return False
        
        # Test that we have the clickable_roles attribute
        if hasattr(accessibility, 'clickable_roles'):
            print(f"✅ clickable_roles attribute found: {len(accessibility.clickable_roles)} roles")
            print(f"   Roles: {sorted(accessibility.clickable_roles)}")
        else:
            print("❌ clickable_roles attribute not found!")
            return False
        
        print("\n✅ All tests passed! The accessibility fix is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Error testing accessibility fix: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_gmail_link_detection():
    """Test that the module can now detect Gmail links."""
    
    try:
        from modules.accessibility import AccessibilityModule
        
        print("\nTesting Gmail link detection capability...")
        
        accessibility = AccessibilityModule()
        
        # Test that AXLink is now considered clickable
        is_link_clickable = accessibility.is_clickable_element_role('AXLink')
        print(f"AXLink is clickable: {is_link_clickable}")
        
        if not is_link_clickable:
            print("❌ AXLink is not considered clickable - Gmail links won't be found!")
            return False
        
        # Test enhanced role detection
        enhanced_available = accessibility.is_enhanced_role_detection_available()
        print(f"Enhanced role detection available: {enhanced_available}")
        
        if not enhanced_available:
            print("❌ Enhanced role detection not available - will fall back to button-only!")
            return False
        
        print("✅ Gmail link detection should now work with enhanced role detection!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing Gmail link detection: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("ACCESSIBILITY FAST PATH FIX VERIFICATION")
    print("=" * 60)
    
    success = True
    
    # Test the basic fix
    if not test_accessibility_fix():
        success = False
    
    # Test Gmail link detection specifically
    if not test_gmail_link_detection():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 ALL TESTS PASSED! The accessibility fast path fix is working!")
        print("Gmail links should now be detectable via the fast path.")
    else:
        print("❌ SOME TESTS FAILED! The fix may not be complete.")
    print("=" * 60)
    
    sys.exit(0 if success else 1)