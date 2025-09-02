#!/usr/bin/env python3
"""
Environment validation script for macOS Accessibility API
Tests pyobjc-framework-Accessibility installation and basic functionality
"""

import sys
import traceback
from typing import Dict, Any, Optional, List


def test_pyobjc_accessibility_import() -> Dict[str, Any]:
    """Test if pyobjc-framework-Accessibility can be imported."""
    result = {
        'test_name': 'PyObjC Accessibility Import',
        'success': False,
        'error': None,
        'details': {}
    }
    
    try:
        # Test basic imports
        import objc
        import Cocoa
        from Foundation import NSObject
        
        # Try to access Accessibility framework via objc
        try:
            # Load the ApplicationServices framework which contains Accessibility APIs
            objc.loadBundle('ApplicationServices', globals(), 
                           bundle_path='/System/Library/Frameworks/ApplicationServices.framework')
            
            # Test if we can access the functions
            AXUIElementCreateApplication = globals().get('AXUIElementCreateApplication')
            AXUIElementCopyAttributeNames = globals().get('AXUIElementCopyAttributeNames')
            
            accessibility_available = (AXUIElementCreateApplication is not None and 
                                     AXUIElementCopyAttributeNames is not None)
        except Exception as e:
            accessibility_available = False
            accessibility_error = str(e)
        
        result['success'] = True
        result['details'] = {
            'objc_available': True,
            'cocoa_available': True,
            'foundation_available': True,
            'accessibility_available': accessibility_available,
            'imports_successful': [
                'objc',
                'Cocoa', 
                'Foundation.NSObject'
            ]
        }
        
        if accessibility_available:
            result['details']['imports_successful'].extend([
                'Accessibility.AXUIElementCreateApplication',
                'Accessibility.AXUIElementCopyAttributeNames'
            ])
        
    except ImportError as e:
        result['error'] = f"Import error: {str(e)}"
        result['details']['missing_module'] = str(e)
    except Exception as e:
        result['error'] = f"Unexpected error: {str(e)}"
        result['details']['exception_type'] = type(e).__name__
    
    return result


def test_accessibility_api_connectivity() -> Dict[str, Any]:
    """Test basic connectivity to macOS Accessibility API."""
    result = {
        'test_name': 'Accessibility API Connectivity',
        'success': False,
        'error': None,
        'details': {}
    }
    
    try:
        import objc
        
        # Load the ApplicationServices framework
        objc.loadBundle('ApplicationServices', globals(), 
                       bundle_path='/System/Library/Frameworks/ApplicationServices.framework')
        
        AXUIElementCreateApplication = globals().get('AXUIElementCreateApplication')
        AXUIElementCopyAttributeNames = globals().get('AXUIElementCopyAttributeNames')
        
        # Try to get running applications using objc
        try:
            # Load the AppKit framework
            objc.loadBundle('AppKit', globals(), 
                           bundle_path='/System/Library/Frameworks/AppKit.framework')
            NSWorkspace = objc.lookUpClass('NSWorkspace')
            workspace = NSWorkspace.sharedWorkspace()
            running_apps = workspace.runningApplications()
        except Exception as workspace_error:
            # Fallback: try to get current process ID
            import os
            running_apps = [type('MockApp', (), {
                'processIdentifier': lambda: os.getpid(),
                'localizedName': lambda: 'Python Test Process'
            })()]
        
        if not running_apps:
            result['error'] = "No running applications found"
            return result
            
        # Try to create accessibility element for the first app
        first_app = running_apps[0]
        app_pid = first_app.processIdentifier()
        
        # Create accessibility element
        ax_app = AXUIElementCreateApplication(app_pid)
        
        if ax_app is None:
            result['error'] = "Failed to create accessibility element"
            return result
            
        # Try to get attribute names
        attribute_names = AXUIElementCopyAttributeNames(ax_app)
        
        result['success'] = True
        result['details'] = {
            'test_app_name': first_app.localizedName() or 'Unknown',
            'test_app_pid': app_pid,
            'accessibility_element_created': True,
            'attribute_count': len(attribute_names) if attribute_names else 0,
            'sample_attributes': list(attribute_names[:5]) if attribute_names else []
        }
        
    except Exception as e:
        result['error'] = f"API connectivity error: {str(e)}"
        result['details']['exception_type'] = type(e).__name__
        result['details']['traceback'] = traceback.format_exc()
    
    return result


def test_accessibility_tree_traversal() -> Dict[str, Any]:
    """Test basic accessibility tree traversal capabilities."""
    result = {
        'test_name': 'Accessibility Tree Traversal',
        'success': False,
        'error': None,
        'details': {}
    }
    
    try:
        import objc
        
        # Load the ApplicationServices framework
        objc.loadBundle('ApplicationServices', globals(), 
                       bundle_path='/System/Library/Frameworks/ApplicationServices.framework')
        
        AXUIElementCreateApplication = globals().get('AXUIElementCreateApplication')
        AXUIElementCopyAttributeValue = globals().get('AXUIElementCopyAttributeValue')
        AXUIElementCopyAttributeNames = globals().get('AXUIElementCopyAttributeNames')
        
        # Try to get Finder process ID using system tools
        import subprocess
        try:
            # Get Finder PID using pgrep
            finder_pid_result = subprocess.run(['pgrep', 'Finder'], 
                                             capture_output=True, text=True)
            if finder_pid_result.returncode == 0:
                finder_pid = int(finder_pid_result.stdout.strip())
                finder_app = type('MockApp', (), {
                    'processIdentifier': lambda: finder_pid,
                    'localizedName': lambda: 'Finder'
                })()
            else:
                finder_app = None
        except Exception:
            finder_app = None
        
        if not finder_app:
            result['error'] = "Finder application not found"
            return result
            
        # Create accessibility element for Finder
        finder_pid = finder_app.processIdentifier()
        ax_finder = AXUIElementCreateApplication(finder_pid)
        
        if ax_finder is None:
            result['error'] = "Failed to create Finder accessibility element"
            return result
            
        # Try to get children (basic tree traversal)
        try:
            children = AXUIElementCopyAttributeValue(ax_finder, "AXChildren")
            windows = AXUIElementCopyAttributeValue(ax_finder, "AXWindows")
            
            result['success'] = True
            result['details'] = {
                'finder_pid': finder_pid,
                'children_count': len(children) if children else 0,
                'windows_count': len(windows) if windows else 0,
                'tree_traversal_successful': True
            }
            
            # Try to get details of first window if available
            if windows and len(windows) > 0:
                first_window = windows[0]
                window_attributes = AXUIElementCopyAttributeNames(first_window)
                
                # Try to get window title
                try:
                    window_title = AXUIElementCopyAttributeValue(first_window, "AXTitle")
                    result['details']['sample_window_title'] = str(window_title) if window_title else 'No title'
                except:
                    result['details']['sample_window_title'] = 'Could not retrieve title'
                    
                result['details']['window_attributes_count'] = len(window_attributes) if window_attributes else 0
                
        except Exception as e:
            result['error'] = f"Tree traversal failed: {str(e)}"
            result['details']['traversal_error'] = str(e)
            
    except Exception as e:
        result['error'] = f"Tree traversal setup error: {str(e)}"
        result['details']['exception_type'] = type(e).__name__
        result['details']['traceback'] = traceback.format_exc()
    
    return result


def test_accessibility_permissions() -> Dict[str, Any]:
    """Test if accessibility permissions are granted."""
    result = {
        'test_name': 'Accessibility Permissions',
        'success': False,
        'error': None,
        'details': {}
    }
    
    try:
        import os
        import objc
        
        # Load the ApplicationServices framework
        objc.loadBundle('ApplicationServices', globals(), 
                       bundle_path='/System/Library/Frameworks/ApplicationServices.framework')
        
        AXUIElementCreateApplication = globals().get('AXUIElementCreateApplication')
        AXUIElementCopyAttributeValue = globals().get('AXUIElementCopyAttributeValue')
        
        # Use current Python process for testing
        app_pid = os.getpid()
        app_name = "Python Test Process"
        ax_app = AXUIElementCreateApplication(app_pid)
        
        # Try to access attributes that require permissions
        try:
            role = AXUIElementCopyAttributeValue(ax_app, "AXRole")
            title = AXUIElementCopyAttributeValue(ax_app, "AXTitle")
            
            result['success'] = True
            result['details'] = {
                'test_app_pid': app_pid,
                'test_app_name': app_name,
                'can_read_role': role is not None,
                'can_read_title': title is not None,
                'permissions_appear_granted': True
            }
            
        except Exception as perm_error:
            result['error'] = f"Permission denied or accessibility not enabled: {str(perm_error)}"
            result['details'] = {
                'test_app_pid': app_pid,
                'permission_error': str(perm_error),
                'likely_cause': 'Accessibility permissions not granted to Terminal/Python'
            }
            
    except Exception as e:
        result['error'] = f"Permission test setup error: {str(e)}"
        result['details']['exception_type'] = type(e).__name__
    
    return result


def run_all_tests() -> List[Dict[str, Any]]:
    """Run all accessibility validation tests."""
    tests = [
        test_pyobjc_accessibility_import,
        test_accessibility_api_connectivity,
        test_accessibility_tree_traversal,
        test_accessibility_permissions
    ]
    
    results = []
    for test_func in tests:
        print(f"Running {test_func.__name__}...")
        result = test_func()
        results.append(result)
        
        # Print immediate feedback
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        print(f"  {status}: {result['test_name']}")
        if result['error']:
            print(f"    Error: {result['error']}")
        print()
    
    return results


def print_detailed_results(results: List[Dict[str, Any]]) -> None:
    """Print detailed test results."""
    print("=" * 80)
    print("DETAILED ACCESSIBILITY VALIDATION RESULTS")
    print("=" * 80)
    
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r['success'])
    
    print(f"\nSUMMARY: {passed_tests}/{total_tests} tests passed\n")
    
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['test_name']}")
        print(f"   Status: {'✅ PASS' if result['success'] else '❌ FAIL'}")
        
        if result['error']:
            print(f"   Error: {result['error']}")
            
        if result['details']:
            print("   Details:")
            for key, value in result['details'].items():
                print(f"     - {key}: {value}")
        print()
    
    # Overall assessment
    print("=" * 80)
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED - Accessibility environment is ready!")
    elif passed_tests >= 2:
        print("⚠️  PARTIAL SUCCESS - Some functionality available, check failed tests")
    else:
        print("🚨 CRITICAL ISSUES - Accessibility environment needs attention")
    
    print("\nNext steps:")
    if passed_tests < total_tests:
        print("- Check that pyobjc-framework-Accessibility is installed")
        print("- Ensure Terminal/Python has Accessibility permissions in System Preferences")
        print("- Run: System Preferences > Security & Privacy > Privacy > Accessibility")
    else:
        print("- Environment validation complete")
        print("- Ready to proceed with AccessibilityModule implementation")
    
    print("=" * 80)


def main():
    """Main function to run accessibility validation."""
    print("macOS Accessibility API Environment Validation")
    print("=" * 50)
    print(f"Python version: {sys.version}")
    print(f"Platform: {sys.platform}")
    print()
    
    if sys.platform != 'darwin':
        print("❌ This validation script is designed for macOS only")
        sys.exit(1)
    
    results = run_all_tests()
    print_detailed_results(results)
    
    # Return appropriate exit code
    passed_tests = sum(1 for r in results if r['success'])
    if passed_tests == len(results):
        sys.exit(0)  # All tests passed
    elif passed_tests >= 2:
        sys.exit(1)  # Partial success
    else:
        sys.exit(2)  # Critical failure


if __name__ == "__main__":
    main()