#!/usr/bin/env python3
"""
Environment validation script for macOS Accessibility API integration.
Tests pyobjc-framework-Accessibility installation and basic functionality.
"""

import sys
import platform
import subprocess
from typing import Dict, Any, List, Optional


def check_platform() -> Dict[str, Any]:
    """Verify we're running on macOS."""
    result = {
        'platform': platform.system(),
        'version': platform.mac_ver()[0] if platform.system() == 'Darwin' else None,
        'is_macos': platform.system() == 'Darwin',
        'status': 'pass' if platform.system() == 'Darwin' else 'fail'
    }
    
    print(f"Platform Check: {result['status'].upper()}")
    print(f"  System: {result['platform']}")
    if result['is_macos']:
        print(f"  macOS Version: {result['version']}")
    else:
        print("  ERROR: This script requires macOS")
    
    return result


def check_pyobjc_installation() -> Dict[str, Any]:
    """Check if pyobjc and required frameworks are installed."""
    result = {
        'pyobjc_core': False,
        'appkit': False,
        'accessibility': False,
        'status': 'fail'
    }
    
    print("\nPyObjC Installation Check:")
    
    # Check pyobjc core
    try:
        import objc
        result['pyobjc_core'] = True
        print(f"  ✓ pyobjc core: {objc.__version__}")
    except ImportError as e:
        print(f"  ✗ pyobjc core: Not installed ({e})")
        return result
    
    # Check AppKit framework
    try:
        import AppKit
        result['appkit'] = True
        print("  ✓ AppKit framework: Available")
    except ImportError as e:
        print(f"  ✗ AppKit framework: Not available ({e})")
    
    # Check Accessibility framework
    try:
        from ApplicationServices import AXUIElementCreateSystemWide, AXIsProcessTrusted
        result['accessibility'] = True
        print("  ✓ Accessibility framework: Available")
    except ImportError as e:
        print(f"  ✗ Accessibility framework: Not available ({e})")
        # Try alternative import paths
        try:
            from Accessibility import AXUIElementCreateSystemWide
            result['accessibility'] = True
            print("  ✓ Accessibility framework: Available via Accessibility module")
        except ImportError as e2:
            try:
                import Quartz
                from Quartz import CGWindowListCopyWindowInfo
                result['accessibility'] = True
                print("  ✓ Accessibility framework: Available via Quartz (limited)")
            except ImportError as e3:
                print(f"  ✗ All accessibility imports failed: {e}, {e2}, {e3}")
    
    result['status'] = 'pass' if all([result['pyobjc_core'], result['appkit'], result['accessibility']]) else 'fail'
    return result


def check_accessibility_permissions() -> Dict[str, Any]:
    """Check if the application has accessibility permissions."""
    result = {
        'has_permission': False,
        'status': 'fail'
    }
    
    print("\nAccessibility Permissions Check:")
    
    try:
        from ApplicationServices import AXIsProcessTrusted, AXIsProcessTrustedWithOptions
        from CoreFoundation import kCFBooleanTrue
        
        # Check if process is trusted
        is_trusted = AXIsProcessTrusted()
        result['has_permission'] = bool(is_trusted)
        
        if is_trusted:
            print("  ✓ Process has accessibility permissions")
            result['status'] = 'pass'
        else:
            print("  ⚠ Process does not have accessibility permissions")
            print("    To grant permissions:")
            print("    1. Open System Preferences > Security & Privacy > Privacy")
            print("    2. Select 'Accessibility' from the left panel")
            print("    3. Add your terminal application or Python interpreter")
            print("    4. Ensure it's checked/enabled")
            result['status'] = 'warning'
            
    except Exception as e:
        print(f"  ✗ Error checking permissions: {e}")
        result['status'] = 'fail'
    
    return result


def test_basic_accessibility_api() -> Dict[str, Any]:
    """Test basic accessibility API functionality."""
    result = {
        'can_get_frontmost_app': False,
        'can_traverse_elements': False,
        'status': 'fail'
    }
    
    print("\nBasic Accessibility API Test:")
    
    try:
        from ApplicationServices import (
            AXUIElementCreateSystemWide,
            AXUIElementCreateApplication,
            AXUIElementCopyAttributeNames,
            AXUIElementCopyAttributeValue
        )
        from Cocoa import NSWorkspace
        
        # Test getting frontmost application
        try:
            workspace = NSWorkspace.sharedWorkspace()
            frontmost_app = workspace.frontmostApplication()
            if frontmost_app:
                app_name = frontmost_app.localizedName()
                pid = frontmost_app.processIdentifier()
                print(f"  ✓ Can get frontmost app: {app_name} (PID: {pid})")
                result['can_get_frontmost_app'] = True
            else:
                print("  ✗ Cannot get frontmost application")
        except Exception as e:
            print(f"  ✗ Error getting frontmost app: {e}")
        
        # Test basic element traversal
        try:
            system_element = AXUIElementCreateSystemWide()
            if system_element:
                # Try to get attribute names
                error_code, attr_names = AXUIElementCopyAttributeNames(system_element, None)
                if error_code == 0 and attr_names:
                    print(f"  ✓ Can traverse elements: Found {len(attr_names)} system attributes")
                    result['can_traverse_elements'] = True
                else:
                    print(f"  ✗ Cannot get system element attributes (error: {error_code})")
            else:
                print("  ✗ Cannot create system-wide accessibility element")
        except Exception as e:
            print(f"  ✗ Error traversing elements: {e}")
            
    except ImportError as e:
        print(f"  ✗ Cannot import accessibility APIs: {e}")
    except Exception as e:
        print(f"  ✗ Unexpected error: {e}")
    
    result['status'] = 'pass' if all([result['can_get_frontmost_app'], result['can_traverse_elements']]) else 'fail'
    return result


def test_accessibility_tree_traversal() -> Dict[str, Any]:
    """Test more advanced accessibility tree traversal."""
    result = {
        'can_find_elements': False,
        'element_count': 0,
        'status': 'fail'
    }
    
    print("\nAccessibility Tree Traversal Test:")
    
    try:
        from ApplicationServices import (
            AXUIElementCreateApplication,
            AXUIElementCopyAttributeNames,
            AXUIElementCopyAttributeValue
        )
        from Cocoa import NSWorkspace
        
        # Get frontmost application
        workspace = NSWorkspace.sharedWorkspace()
        frontmost_app = workspace.frontmostApplication()
        
        if not frontmost_app:
            print("  ✗ No frontmost application available")
            return result
            
        pid = frontmost_app.processIdentifier()
        app_name = frontmost_app.localizedName()
        
        # Create accessibility element for the application
        app_element = AXUIElementCreateApplication(pid)
        if not app_element:
            print(f"  ✗ Cannot create accessibility element for {app_name}")
            return result
            
        print(f"  Testing with application: {app_name}")
        
        # Try to get children using string constants
        try:
            error_code, children = AXUIElementCopyAttributeValue(app_element, "AXChildren", None)
            if error_code == 0 and children:
                result['element_count'] = len(children)
                print(f"  ✓ Found {len(children)} top-level elements")
                
                # Try to examine first few elements
                examined = 0
                for i, child in enumerate(children[:3]):  # Limit to first 3 elements
                    try:
                        error_code1, role = AXUIElementCopyAttributeValue(child, "AXRole", None)
                        error_code2, title = AXUIElementCopyAttributeValue(child, "AXTitle", None)
                        
                        role_str = str(role) if (error_code1 == 0 and role) else "Unknown"
                        title_str = str(title) if (error_code2 == 0 and title) else "No title"
                        
                        print(f"    Element {i+1}: {role_str} - {title_str}")
                        examined += 1
                    except Exception as e:
                        print(f"    Element {i+1}: Error examining element - {e}")
                
                if examined > 0:
                    result['can_find_elements'] = True
                    result['status'] = 'pass'
                    print(f"  ✓ Successfully examined {examined} elements")
                else:
                    print("  ✗ Could not examine any elements")
            else:
                print(f"  ✗ No children found for application (error: {error_code})")
                
        except Exception as e:
            print(f"  ✗ Error getting application children: {e}")
            
    except Exception as e:
        print(f"  ✗ Error in tree traversal test: {e}")
    
    return result


def install_missing_dependencies() -> bool:
    """Attempt to install missing pyobjc dependencies."""
    print("\nAttempting to install missing dependencies...")
    
    try:
        # Install pyobjc-framework-Accessibility specifically
        subprocess.run([
            sys.executable, "-m", "pip", "install", 
            "pyobjc-framework-Accessibility>=10.0"
        ], check=True, capture_output=True, text=True)
        
        print("  ✓ Successfully installed pyobjc-framework-Accessibility")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"  ✗ Failed to install dependencies: {e}")
        print(f"    stdout: {e.stdout}")
        print(f"    stderr: {e.stderr}")
        return False
    except Exception as e:
        print(f"  ✗ Unexpected error during installation: {e}")
        return False


def main():
    """Run all environment validation tests."""
    print("=" * 60)
    print("AURA Hybrid Architecture - Environment Validation")
    print("=" * 60)
    
    results = {}
    
    # 1. Platform check
    results['platform'] = check_platform()
    if results['platform']['status'] == 'fail':
        print("\n❌ CRITICAL: This system is not compatible with macOS Accessibility APIs")
        return False
    
    # 2. PyObjC installation check
    results['pyobjc'] = check_pyobjc_installation()
    if results['pyobjc']['status'] == 'fail':
        print("\n⚠️  Missing dependencies detected. Attempting installation...")
        if install_missing_dependencies():
            # Re-check after installation
            results['pyobjc'] = check_pyobjc_installation()
        
        if results['pyobjc']['status'] == 'fail':
            print("\n❌ CRITICAL: Required PyObjC frameworks are not available")
            return False
    
    # 3. Accessibility permissions check
    results['permissions'] = check_accessibility_permissions()
    
    # 4. Basic API functionality test
    results['basic_api'] = test_basic_accessibility_api()
    
    # 5. Tree traversal test
    results['tree_traversal'] = test_accessibility_tree_traversal()
    
    # Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    
    all_passed = True
    critical_failed = False
    
    for test_name, test_result in results.items():
        status = test_result['status']
        if status == 'pass':
            print(f"✓ {test_name.replace('_', ' ').title()}: PASS")
        elif status == 'warning':
            print(f"⚠ {test_name.replace('_', ' ').title()}: WARNING")
            all_passed = False
        else:
            print(f"✗ {test_name.replace('_', ' ').title()}: FAIL")
            all_passed = False
            if test_name in ['platform', 'pyobjc']:
                critical_failed = True
    
    print("\n" + "-" * 60)
    
    if critical_failed:
        print("❌ CRITICAL FAILURES: Environment is not ready for Accessibility API integration")
        print("   Please resolve the critical issues above before proceeding.")
        return False
    elif not all_passed:
        print("⚠️  WARNINGS DETECTED: Environment has some issues but may still work")
        print("   Consider resolving warnings for optimal performance.")
        if results['permissions']['status'] == 'warning':
            print("   Accessibility permissions are required for full functionality.")
        return True
    else:
        print("✅ ALL TESTS PASSED: Environment is ready for Accessibility API integration")
        return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)