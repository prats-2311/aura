#!/usr/bin/env python3
"""
Test accessibility specifically in the aura environment
"""

import sys
import os

def test_pyobjc_import():
    """Test PyObjC import in aura environment."""
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {sys.version}")
    
    try:
        from ApplicationServices import (
            AXIsProcessTrusted, 
            AXIsProcessTrustedWithOptions,
            AXUIElementCreateSystemWide,
            AXUIElementCopyAttributeValue,
            kAXFocusedApplicationAttribute
        )
        print("✅ ApplicationServices imported successfully")
        
        # Test basic trust check
        is_trusted = AXIsProcessTrusted()
        print(f"AXIsProcessTrusted(): {is_trusted}")
        
        if is_trusted:
            # Test system element access
            try:
                system_element = AXUIElementCreateSystemWide()
                print("✅ AXUIElementCreateSystemWide() successful")
                
                # Test focused app access
                focused_app = AXUIElementCopyAttributeValue(system_element, kAXFocusedApplicationAttribute)
                print("✅ AXUIElementCopyAttributeValue() successful")
                print("🎉 ALL ACCESSIBILITY FUNCTIONS WORKING!")
                return True
                
            except Exception as e:
                print(f"❌ Accessibility function failed: {e}")
                return False
        else:
            print("❌ Process not trusted - permissions not granted")
            return False
            
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_aura_permission_validator():
    """Test AURA's permission validator."""
    try:
        from modules.permission_validator import PermissionValidator
        
        validator = PermissionValidator()
        status = validator.check_accessibility_permissions()
        
        print(f"\nAURA Permission Status:")
        print(f"  Has permissions: {status.has_permissions}")
        print(f"  Permission level: {status.permission_level}")
        print(f"  Missing permissions: {status.missing_permissions}")
        print(f"  Granted permissions: {status.granted_permissions}")
        
        return status.has_permissions
        
    except Exception as e:
        print(f"❌ AURA permission validator failed: {e}")
        return False

if __name__ == "__main__":
    print("="*60)
    print("TESTING ACCESSIBILITY IN AURA ENVIRONMENT")
    print("="*60)
    
    # Test PyObjC directly
    print("\n1. Testing PyObjC directly:")
    pyobjc_works = test_pyobjc_import()
    
    # Test AURA's permission validator
    print("\n2. Testing AURA's permission validator:")
    aura_works = test_aura_permission_validator()
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"PyObjC working: {'✅' if pyobjc_works else '❌'}")
    print(f"AURA validator working: {'✅' if aura_works else '❌'}")
    
    if pyobjc_works and aura_works:
        print("\n🎉 ACCESSIBILITY IS WORKING!")
        print("The issue might be elsewhere in AURA.")
    elif pyobjc_works and not aura_works:
        print("\n⚠️ PyObjC works but AURA validator doesn't.")
        print("There might be an issue with AURA's permission checking logic.")
    else:
        print("\n❌ ACCESSIBILITY PERMISSIONS NOT WORKING")
        print("You need to add the correct Python executable to System Preferences.")
        print(f"Add this to Accessibility: {sys.executable}")