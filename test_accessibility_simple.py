#!/usr/bin/env python3
"""
Simple test for macOS Accessibility API functionality
"""

import sys
import os

def test_accessibility_framework():
    """Test if we can load and use the Accessibility framework."""
    print("Testing macOS Accessibility Framework...")
    
    try:
        from ApplicationServices import (
            AXUIElementCreateApplication,
            AXUIElementCopyAttributeNames, 
            AXUIElementCopyAttributeValue,
            AXIsProcessTrusted
        )
        print("✅ ApplicationServices accessibility functions imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import ApplicationServices accessibility functions: {e}")
        return False
    
    # Check if accessibility functions are available
    ax_functions = {
        'AXUIElementCreateApplication': AXUIElementCreateApplication,
        'AXUIElementCopyAttributeNames': AXUIElementCopyAttributeNames, 
        'AXUIElementCopyAttributeValue': AXUIElementCopyAttributeValue,
        'AXIsProcessTrusted': AXIsProcessTrusted
    }
    
    available_functions = []
    for func_name, func in ax_functions.items():
        if func is not None:
            available_functions.append(func_name)
            print(f"✅ {func_name} is available")
        else:
            print(f"❌ {func_name} is not available")
    
    if len(available_functions) >= 3:  # Need at least basic functions
        print(f"✅ Accessibility framework functional ({len(available_functions)}/{len(ax_functions)} functions available)")
        return True
    else:
        print(f"❌ Accessibility framework not functional ({len(available_functions)}/{len(ax_functions)} functions available)")
        return False

def test_basic_accessibility_usage():
    """Test basic accessibility API usage."""
    print("\nTesting basic Accessibility API usage...")
    
    try:
        from ApplicationServices import (
            AXUIElementCreateApplication,
            AXUIElementCopyAttributeNames
        )
        
        print("✅ Accessibility functions imported successfully")
            
        # Try to create an accessibility element for the current process
        current_pid = os.getpid()
        print(f"Testing with current process PID: {current_pid}")
        
        ax_app = AXUIElementCreateApplication(current_pid)
        if ax_app is None:
            print("❌ Failed to create accessibility element")
            return False
        
        print("✅ Successfully created accessibility element")
        
        # Try to get attribute names
        if AXUIElementCopyAttributeNames:
            try:
                attributes = AXUIElementCopyAttributeNames(ax_app)
                if attributes:
                    print(f"✅ Retrieved {len(attributes)} attributes")
                    print(f"Sample attributes: {list(attributes[:3])}")
                else:
                    print("⚠️  No attributes returned (may indicate permission issues)")
            except Exception as e:
                print(f"⚠️  Error getting attributes: {e} (may indicate permission issues)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in basic usage test: {e}")
        return False

def test_permissions():
    """Test if accessibility permissions are granted."""
    print("\nTesting Accessibility permissions...")
    
    try:
        from ApplicationServices import AXIsProcessTrusted
        
        print("✅ AXIsProcessTrusted function imported successfully")
        is_trusted = AXIsProcessTrusted()
        if is_trusted:
            print("✅ Process is trusted for accessibility")
            return True
        else:
            print("❌ Process is NOT trusted for accessibility")
            print("   Please grant accessibility permissions in System Preferences:")
            print("   System Preferences > Security & Privacy > Privacy > Accessibility")
            return False
            
    except Exception as e:
        print(f"❌ Error checking permissions: {e}")
        return False

def main():
    """Run all tests."""
    print("macOS Accessibility API Validation")
    print("=" * 50)
    print(f"Python version: {sys.version}")
    print(f"Platform: {sys.platform}")
    print()
    
    if sys.platform != 'darwin':
        print("❌ This test is designed for macOS only")
        return 1
    
    # Run tests
    tests = [
        ("Framework Loading", test_accessibility_framework),
        ("Basic API Usage", test_basic_accessibility_usage),
        ("Permissions Check", test_permissions)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        result = test_func()
        results.append((test_name, result))
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result is True)
    total = len([r for _, r in results if r is not None])
    
    for test_name, result in results:
        if result is True:
            status = "✅ PASS"
        elif result is False:
            status = "❌ FAIL"
        else:
            status = "⚠️  SKIP"
        print(f"{status}: {test_name}")
    
    print(f"\nResult: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Accessibility environment is ready.")
        return 0
    elif passed > 0:
        print("\n⚠️  Some tests passed. Check failed tests above.")
        return 1
    else:
        print("\n🚨 All tests failed. Accessibility environment needs setup.")
        return 2

if __name__ == "__main__":
    sys.exit(main())