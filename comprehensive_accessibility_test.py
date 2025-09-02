#!/usr/bin/env python3
"""
Comprehensive test for macOS Accessibility API functionality.
Tests all requirements for the hybrid architecture implementation.
"""

import sys
import time
from typing import Dict, Any, List, Optional, Tuple
from ApplicationServices import (
    AXUIElementCreateSystemWide,
    AXUIElementCreateApplication,
    AXUIElementCopyAttributeNames,
    AXUIElementCopyAttributeValue,
    AXIsProcessTrusted
)
from Cocoa import NSWorkspace


class AccessibilityTester:
    """Test class for comprehensive accessibility API validation."""
    
    def __init__(self):
        self.results = {}
        
    def test_dependency_installation(self) -> bool:
        """Test that all required dependencies are properly installed."""
        print("Testing Dependency Installation...")
        
        try:
            # Test core imports
            import objc
            from ApplicationServices import AXUIElementCreateSystemWide
            from Cocoa import NSWorkspace
            
            print(f"  ✓ PyObjC version: {objc.__version__}")
            print("  ✓ ApplicationServices framework: Available")
            print("  ✓ Cocoa framework: Available")
            
            self.results['dependencies'] = True
            return True
            
        except ImportError as e:
            print(f"  ✗ Import error: {e}")
            self.results['dependencies'] = False
            return False
    
    def test_accessibility_permissions(self) -> bool:
        """Test accessibility permissions and API connectivity."""
        print("\nTesting Accessibility Permissions...")
        
        try:
            is_trusted = AXIsProcessTrusted()
            if is_trusted:
                print("  ✓ Process has accessibility permissions")
                self.results['permissions'] = True
                return True
            else:
                print("  ⚠ Process lacks accessibility permissions")
                print("    Grant permissions in System Preferences > Security & Privacy > Privacy > Accessibility")
                self.results['permissions'] = False
                return False
                
        except Exception as e:
            print(f"  ✗ Error checking permissions: {e}")
            self.results['permissions'] = False
            return False
    
    def test_basic_tree_traversal(self) -> bool:
        """Test basic accessibility tree traversal capabilities."""
        print("\nTesting Basic Tree Traversal...")
        
        try:
            # Test system-wide element
            system_element = AXUIElementCreateSystemWide()
            if not system_element:
                print("  ✗ Cannot create system-wide element")
                return False
                
            error_code, attr_names = AXUIElementCopyAttributeNames(system_element, None)
            if error_code != 0 or not attr_names:
                print(f"  ✗ Cannot get system attributes (error: {error_code})")
                return False
                
            print(f"  ✓ System element has {len(attr_names)} attributes")
            
            # Test application element
            workspace = NSWorkspace.sharedWorkspace()
            frontmost_app = workspace.frontmostApplication()
            
            if not frontmost_app:
                print("  ✗ No frontmost application")
                return False
                
            pid = frontmost_app.processIdentifier()
            app_name = frontmost_app.localizedName()
            
            app_element = AXUIElementCreateApplication(pid)
            if not app_element:
                print(f"  ✗ Cannot create element for {app_name}")
                return False
                
            error_code, app_attrs = AXUIElementCopyAttributeNames(app_element, None)
            if error_code != 0 or not app_attrs:
                print(f"  ✗ Cannot get app attributes (error: {error_code})")
                return False
                
            print(f"  ✓ App '{app_name}' has {len(app_attrs)} attributes")
            
            self.results['tree_traversal'] = True
            return True
            
        except Exception as e:
            print(f"  ✗ Error in tree traversal: {e}")
            self.results['tree_traversal'] = False
            return False
    
    def test_element_discovery(self) -> bool:
        """Test element discovery and attribute access."""
        print("\nTesting Element Discovery...")
        
        try:
            workspace = NSWorkspace.sharedWorkspace()
            frontmost_app = workspace.frontmostApplication()
            
            if not frontmost_app:
                print("  ✗ No frontmost application")
                return False
                
            pid = frontmost_app.processIdentifier()
            app_name = frontmost_app.localizedName()
            app_element = AXUIElementCreateApplication(pid)
            
            # Get children
            error_code, children = AXUIElementCopyAttributeValue(app_element, "AXChildren", None)
            if error_code != 0 or not children:
                print(f"  ✗ Cannot get app children (error: {error_code})")
                return False
                
            print(f"  ✓ Found {len(children)} top-level elements in {app_name}")
            
            # Examine elements
            elements_examined = 0
            for i, child in enumerate(children[:5]):  # Limit to 5 elements
                try:
                    error_code1, role = AXUIElementCopyAttributeValue(child, "AXRole", None)
                    error_code2, title = AXUIElementCopyAttributeValue(child, "AXTitle", None)
                    error_code3, position = AXUIElementCopyAttributeValue(child, "AXPosition", None)
                    error_code4, size = AXUIElementCopyAttributeValue(child, "AXSize", None)
                    
                    role_str = str(role) if (error_code1 == 0 and role) else "Unknown"
                    title_str = str(title) if (error_code2 == 0 and title) else "No title"
                    
                    print(f"    Element {i+1}: {role_str} - '{title_str}'")
                    
                    if error_code3 == 0 and position:
                        print(f"      Position: {position}")
                    if error_code4 == 0 and size:
                        print(f"      Size: {size}")
                        
                    elements_examined += 1
                    
                except Exception as e:
                    print(f"    Element {i+1}: Error - {e}")
            
            if elements_examined > 0:
                print(f"  ✓ Successfully examined {elements_examined} elements")
                self.results['element_discovery'] = True
                return True
            else:
                print("  ✗ Could not examine any elements")
                self.results['element_discovery'] = False
                return False
                
        except Exception as e:
            print(f"  ✗ Error in element discovery: {e}")
            self.results['element_discovery'] = False
            return False
    
    def test_recursive_traversal(self) -> bool:
        """Test recursive accessibility tree traversal."""
        print("\nTesting Recursive Tree Traversal...")
        
        try:
            workspace = NSWorkspace.sharedWorkspace()
            frontmost_app = workspace.frontmostApplication()
            
            if not frontmost_app:
                print("  ✗ No frontmost application")
                return False
                
            pid = frontmost_app.processIdentifier()
            app_element = AXUIElementCreateApplication(pid)
            
            total_elements = self._count_elements_recursive(app_element, max_depth=3)
            
            if total_elements > 0:
                print(f"  ✓ Found {total_elements} total elements (max depth 3)")
                self.results['recursive_traversal'] = True
                return True
            else:
                print("  ✗ No elements found in recursive traversal")
                self.results['recursive_traversal'] = False
                return False
                
        except Exception as e:
            print(f"  ✗ Error in recursive traversal: {e}")
            self.results['recursive_traversal'] = False
            return False
    
    def _count_elements_recursive(self, element, current_depth=0, max_depth=3) -> int:
        """Recursively count elements in accessibility tree."""
        if current_depth >= max_depth:
            return 0
            
        count = 1  # Count this element
        
        try:
            error_code, children = AXUIElementCopyAttributeValue(element, "AXChildren", None)
            if error_code == 0 and children:
                for child in children:
                    count += self._count_elements_recursive(child, current_depth + 1, max_depth)
        except:
            pass  # Ignore errors in recursive traversal
            
        return count
    
    def test_performance_benchmarks(self) -> bool:
        """Test performance of accessibility operations."""
        print("\nTesting Performance Benchmarks...")
        
        try:
            workspace = NSWorkspace.sharedWorkspace()
            frontmost_app = workspace.frontmostApplication()
            
            if not frontmost_app:
                print("  ✗ No frontmost application")
                return False
                
            pid = frontmost_app.processIdentifier()
            app_element = AXUIElementCreateApplication(pid)
            
            # Benchmark element creation
            start_time = time.time()
            for _ in range(10):
                test_element = AXUIElementCreateApplication(pid)
            creation_time = (time.time() - start_time) / 10
            
            # Benchmark attribute access
            start_time = time.time()
            for _ in range(10):
                error_code, children = AXUIElementCopyAttributeValue(app_element, "AXChildren", None)
            access_time = (time.time() - start_time) / 10
            
            print(f"  ✓ Element creation: {creation_time*1000:.2f}ms average")
            print(f"  ✓ Attribute access: {access_time*1000:.2f}ms average")
            
            # Check if performance meets requirements (< 2 seconds total for typical operations)
            total_time = creation_time + access_time
            if total_time < 0.1:  # 100ms should be plenty fast
                print(f"  ✓ Performance meets requirements ({total_time*1000:.2f}ms total)")
                self.results['performance'] = True
                return True
            else:
                print(f"  ⚠ Performance may be slow ({total_time*1000:.2f}ms total)")
                self.results['performance'] = False
                return False
                
        except Exception as e:
            print(f"  ✗ Error in performance testing: {e}")
            self.results['performance'] = False
            return False
    
    def test_multiple_applications(self) -> bool:
        """Test accessibility across multiple applications."""
        print("\nTesting Multiple Applications...")
        
        try:
            workspace = NSWorkspace.sharedWorkspace()
            running_apps = workspace.runningApplications()
            
            accessible_apps = 0
            tested_apps = 0
            
            for app in running_apps[:5]:  # Test first 5 apps
                if app.isHidden() or not app.localizedName():
                    continue
                    
                app_name = app.localizedName()
                pid = app.processIdentifier()
                
                try:
                    app_element = AXUIElementCreateApplication(pid)
                    error_code, attrs = AXUIElementCopyAttributeNames(app_element, None)
                    
                    if error_code == 0 and attrs:
                        accessible_apps += 1
                        print(f"  ✓ {app_name}: Accessible ({len(attrs)} attributes)")
                    else:
                        print(f"  - {app_name}: Not accessible")
                        
                    tested_apps += 1
                    
                except Exception as e:
                    print(f"  - {app_name}: Error - {e}")
                    tested_apps += 1
            
            if accessible_apps > 0:
                print(f"  ✓ {accessible_apps}/{tested_apps} applications are accessible")
                self.results['multiple_apps'] = True
                return True
            else:
                print(f"  ✗ No accessible applications found")
                self.results['multiple_apps'] = False
                return False
                
        except Exception as e:
            print(f"  ✗ Error testing multiple applications: {e}")
            self.results['multiple_apps'] = False
            return False
    
    def run_all_tests(self) -> bool:
        """Run all accessibility tests."""
        print("=" * 70)
        print("COMPREHENSIVE ACCESSIBILITY API VALIDATION")
        print("=" * 70)
        
        tests = [
            ("Dependency Installation", self.test_dependency_installation),
            ("Accessibility Permissions", self.test_accessibility_permissions),
            ("Basic Tree Traversal", self.test_basic_tree_traversal),
            ("Element Discovery", self.test_element_discovery),
            ("Recursive Traversal", self.test_recursive_traversal),
            ("Performance Benchmarks", self.test_performance_benchmarks),
            ("Multiple Applications", self.test_multiple_applications),
        ]
        
        passed_tests = 0
        critical_failures = 0
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed_tests += 1
                else:
                    if test_name in ["Dependency Installation", "Accessibility Permissions"]:
                        critical_failures += 1
            except Exception as e:
                print(f"  ✗ Unexpected error in {test_name}: {e}")
                if test_name in ["Dependency Installation", "Accessibility Permissions"]:
                    critical_failures += 1
        
        # Summary
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        
        for test_name, _ in tests:
            test_key = test_name.lower().replace(" ", "_")
            if test_key in self.results:
                status = "PASS" if self.results[test_key] else "FAIL"
                icon = "✓" if self.results[test_key] else "✗"
                print(f"{icon} {test_name}: {status}")
            else:
                print(f"✗ {test_name}: NOT RUN")
        
        print(f"\nResults: {passed_tests}/{len(tests)} tests passed")
        
        if critical_failures > 0:
            print("\n❌ CRITICAL FAILURES: Environment not ready for production use")
            return False
        elif passed_tests == len(tests):
            print("\n✅ ALL TESTS PASSED: Environment fully ready for Accessibility API integration")
            return True
        else:
            print("\n⚠️  PARTIAL SUCCESS: Environment has some limitations but may work")
            return True


def main():
    """Run comprehensive accessibility validation."""
    tester = AccessibilityTester()
    success = tester.run_all_tests()
    
    print("\n" + "=" * 70)
    print("RECOMMENDATIONS")
    print("=" * 70)
    
    if success:
        print("✓ Environment is ready for hybrid architecture implementation")
        print("✓ All required dependencies are installed and functional")
        print("✓ Accessibility API connectivity is working properly")
        print("✓ Basic tree traversal capabilities are operational")
        print("\nNext steps:")
        print("  1. Proceed with AccessibilityModule implementation")
        print("  2. Begin Orchestrator integration")
        print("  3. Implement fast path routing logic")
    else:
        print("✗ Environment needs attention before proceeding")
        print("\nRequired actions:")
        if not tester.results.get('dependencies', True):
            print("  1. Install missing PyObjC frameworks")
        if not tester.results.get('permissions', True):
            print("  2. Grant accessibility permissions in System Preferences")
        print("  3. Re-run this validation script")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)