#!/usr/bin/env python3
"""
Test accessibility with proper function calls
"""

import sys
import os

def test_accessibility_properly():
    """Test accessibility with correct function calls."""
    print(f"Python executable: {sys.executable}")
    
    try:
        from ApplicationServices import (
            AXIsProcessTrusted, 
            AXUIElementCreateSystemWide,
            AXUIElementCopyAttributeValue,
            kAXFocusedApplicationAttribute
        )
        from CoreFoundation import CFRelease
        import objc
        
        print("✅ ApplicationServices imported successfully")
        
        # Test basic trust check
        is_trusted = AXIsProcessTrusted()
        print(f"AXIsProcessTrusted(): {is_trusted}")
        
        if is_trusted:
            # Test system element access
            try:
                system_element = AXUIElementCreateSystemWide()
                print("✅ AXUIElementCreateSystemWide() successful")
                
                # Test focused app access with proper error handling
                error = objc.NULL
                focused_app = AXUIElementCopyAttributeValue(system_element, kAXFocusedApplicationAttribute, error)
                
                if focused_app is not None:
                    print("✅ AXUIElementCopyAttributeValue() successful")
                    print("🎉 ALL ACCESSIBILITY FUNCTIONS WORKING!")
                    return True
                else:
                    print(f"❌ AXUIElementCopyAttributeValue() returned None")
                    return False
                    
            except Exception as e:
                print(f"❌ Accessibility function failed: {e}")
                return False
        else:
            print("❌ Process not trusted - permissions not granted")
            return False
            
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def check_what_aura_needs():
    """Check what AURA's permission validator is actually testing."""
    try:
        from modules.permission_validator import PermissionValidator
        
        # Let's look at the source to see what it's checking
        validator = PermissionValidator()
        
        # Check the actual permission validation logic
        print("\nChecking AURA's permission validation logic...")
        
        # Try to call the internal methods to see what's failing
        if hasattr(validator, '_check_system_wide_element_access'):
            try:
                system_access = validator._check_system_wide_element_access()
                print(f"System-wide element access: {system_access}")
            except Exception as e:
                print(f"System-wide element access failed: {e}")
        
        if hasattr(validator, '_check_focused_application_access'):
            try:
                focused_access = validator._check_focused_application_access()
                print(f"Focused application access: {focused_access}")
            except Exception as e:
                print(f"Focused application access failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking AURA's permission logic: {e}")
        return False

if __name__ == "__main__":
    print("="*60)
    print("TESTING ACCESSIBILITY WITH PROPER FUNCTION CALLS")
    print("="*60)
    
    # Test PyObjC with proper calls
    print("\n1. Testing PyObjC with correct function calls:")
    pyobjc_works = test_accessibility_properly()
    
    # Check what AURA is actually testing
    print("\n2. Checking AURA's permission validation logic:")
    check_what_aura_needs()
    
    print(f"\nThe correct Python executable to add to System Preferences:")
    print(f"📁 {sys.executable}")
    
    if pyobjc_works:
        print("\n✅ Basic accessibility is working!")
        print("The issue is likely in AURA's permission validation logic.")
    else:
        print("\n❌ Need to fix accessibility permissions first.")