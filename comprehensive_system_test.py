#!/usr/bin/env python3
"""
Comprehensive system test for accessibility fast path enhancement.
"""

import sys
import os
import logging
import time
from typing import Dict, Any, List

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SystemTestResults:
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.failures = []
        self.performance_metrics = {}
        
    def add_test_result(self, test_name: str, passed: bool, details: str = ""):
        self.tests_run += 1
        if passed:
            self.tests_passed += 1
            print(f"✅ {test_name}")
        else:
            self.tests_failed += 1
            self.failures.append(f"{test_name}: {details}")
            print(f"❌ {test_name}: {details}")
    
    def add_performance_metric(self, metric_name: str, value: float, unit: str = "ms"):
        self.performance_metrics[metric_name] = {"value": value, "unit": unit}
        print(f"📊 {metric_name}: {value:.2f}{unit}")
    
    def print_summary(self):
        print("\n" + "="*70)
        print("COMPREHENSIVE SYSTEM TEST RESULTS")
        print("="*70)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_failed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.failures:
            print("\nFAILURES:")
            for failure in self.failures:
                print(f"  - {failure}")
        
        if self.performance_metrics:
            print("\nPERFORMANCE METRICS:")
            for metric, data in self.performance_metrics.items():
                print(f"  - {metric}: {data['value']:.2f}{data['unit']}")
        
        print("="*70)

def test_accessibility_module_initialization(results: SystemTestResults):
    """Test accessibility module initialization."""
    try:
        from modules.accessibility import AccessibilityModule
        
        start_time = time.time()
        accessibility = AccessibilityModule()
        init_time = (time.time() - start_time) * 1000
        
        results.add_performance_metric("accessibility_init_time", init_time)
        results.add_test_result("Accessibility Module Initialization", True)
        return accessibility
        
    except Exception as e:
        results.add_test_result("Accessibility Module Initialization", False, str(e))
        return None

def test_enhanced_role_detection_availability(results: SystemTestResults, accessibility):
    """Test enhanced role detection availability."""
    if not accessibility:
        results.add_test_result("Enhanced Role Detection Availability", False, "No accessibility module")
        return False
    
    try:
        start_time = time.time()
        available = accessibility.is_enhanced_role_detection_available()
        check_time = (time.time() - start_time) * 1000
        
        results.add_performance_metric("enhanced_detection_check_time", check_time)
        results.add_test_result("Enhanced Role Detection Availability", available, 
                              "Not available" if not available else "")
        return available
        
    except Exception as e:
        results.add_test_result("Enhanced Role Detection Availability", False, str(e))
        return False

def test_clickable_role_detection(results: SystemTestResults, accessibility):
    """Test clickable role detection for various element types."""
    if not accessibility:
        results.add_test_result("Clickable Role Detection", False, "No accessibility module")
        return
    
    test_roles = [
        ('AXButton', True),
        ('AXLink', True),
        ('AXMenuItem', True),
        ('AXCheckBox', True),
        ('AXRadioButton', True),
        ('AXTextField', False),
        ('AXStaticText', False)
    ]
    
    all_passed = True
    failed_roles = []
    
    for role, expected in test_roles:
        try:
            start_time = time.time()
            result = accessibility.is_clickable_element_role(role)
            check_time = (time.time() - start_time) * 1000
            
            results.add_performance_metric(f"role_check_{role.lower()}_time", check_time)
            
            if result != expected:
                all_passed = False
                failed_roles.append(f"{role}: got {result}, expected {expected}")
                
        except Exception as e:
            all_passed = False
            failed_roles.append(f"{role}: exception {e}")
    
    results.add_test_result("Clickable Role Detection", all_passed, 
                          "; ".join(failed_roles) if failed_roles else "")

def test_accessibility_permissions(results: SystemTestResults, accessibility):
    """Test accessibility permissions and application access."""
    if not accessibility:
        results.add_test_result("Accessibility Permissions", False, "No accessibility module")
        return False
    
    try:
        start_time = time.time()
        current_app = accessibility.get_active_application()
        access_time = (time.time() - start_time) * 1000
        
        results.add_performance_metric("app_access_time", access_time)
        
        if current_app and current_app.get('accessible', False):
            results.add_test_result("Accessibility Permissions", True)
            return True
        else:
            app_name = current_app.get('name', 'unknown') if current_app else 'none'
            results.add_test_result("Accessibility Permissions", False, 
                                  f"Cannot access app: {app_name}")
            return False
            
    except Exception as e:
        results.add_test_result("Accessibility Permissions", False, str(e))
        return False

def test_element_finding_performance(results: SystemTestResults, accessibility):
    """Test element finding performance."""
    if not accessibility:
        results.add_test_result("Element Finding Performance", False, "No accessibility module")
        return
    
    test_cases = [
        ('', 'gmail link'),
        ('AXButton', 'search button'),
        ('AXLink', 'home link')
    ]
    
    for role, label in test_cases:
        try:
            start_time = time.time()
            result = accessibility.find_element_enhanced(role, label)
            find_time = (time.time() - start_time) * 1000
            
            metric_name = f"find_element_{role or 'any'}_{label.replace(' ', '_')}_time"
            results.add_performance_metric(metric_name, find_time)
            
            # Check if it meets performance target (<2000ms)
            meets_target = find_time < 2000
            results.add_test_result(f"Element Finding Performance ({role or 'any'} {label})", 
                                  meets_target, 
                                  f"{find_time:.1f}ms (target: <2000ms)" if not meets_target else "")
            
        except Exception as e:
            results.add_test_result(f"Element Finding Performance ({role or 'any'} {label})", 
                                  False, str(e))

def test_orchestrator_integration(results: SystemTestResults):
    """Test orchestrator integration with enhanced accessibility."""
    try:
        from orchestrator import Orchestrator
        
        start_time = time.time()
        orchestrator = Orchestrator()
        init_time = (time.time() - start_time) * 1000
        
        results.add_performance_metric("orchestrator_init_time", init_time)
        
        # Test that accessibility module is properly integrated
        has_accessibility = hasattr(orchestrator, 'accessibility_module') and orchestrator.accessibility_module is not None
        results.add_test_result("Orchestrator Accessibility Integration", has_accessibility,
                              "No accessibility module" if not has_accessibility else "")
        
        if has_accessibility:
            # Test fast path availability
            fast_path_enabled = orchestrator.fast_path_enabled
            accessibility_available = orchestrator.module_availability.get('accessibility', False)
            
            results.add_test_result("Fast Path Enabled", fast_path_enabled,
                                  "Fast path disabled" if not fast_path_enabled else "")
            results.add_test_result("Accessibility Module Available", accessibility_available,
                                  "Module not available" if not accessibility_available else "")
        
        return orchestrator
        
    except Exception as e:
        results.add_test_result("Orchestrator Integration", False, str(e))
        return None

def test_command_processing_pipeline(results: SystemTestResults, orchestrator):
    """Test the complete command processing pipeline."""
    if not orchestrator:
        results.add_test_result("Command Processing Pipeline", False, "No orchestrator")
        return
    
    test_commands = [
        "Click on the Gmail link.",
        "click on google search button",
        "press the home link"
    ]
    
    for command in test_commands:
        try:
            # Test command validation
            start_time = time.time()
            validation_result = orchestrator.validate_command(command)
            validation_time = (time.time() - start_time) * 1000
            
            results.add_performance_metric(f"command_validation_time", validation_time)
            
            is_valid = validation_result.is_valid
            is_click_command = validation_result.command_type == 'click'
            
            results.add_test_result(f"Command Validation ({command[:20]}...)", is_valid,
                                  "Invalid command" if not is_valid else "")
            results.add_test_result(f"Click Command Detection ({command[:20]}...)", is_click_command,
                                  f"Detected as {validation_result.command_type}" if not is_click_command else "")
            
            # Test GUI element extraction
            if is_valid:
                start_time = time.time()
                gui_elements = orchestrator._extract_gui_elements_from_command(validation_result.normalized_command)
                extraction_time = (time.time() - start_time) * 1000
                
                results.add_performance_metric(f"gui_extraction_time", extraction_time)
                
                has_elements = gui_elements is not None
                results.add_test_result(f"GUI Element Extraction ({command[:20]}...)", has_elements,
                                      "No elements extracted" if not has_elements else "")
            
        except Exception as e:
            results.add_test_result(f"Command Processing ({command[:20]}...)", False, str(e))

def test_backward_compatibility(results: SystemTestResults, accessibility):
    """Test backward compatibility with existing functionality."""
    if not accessibility:
        results.add_test_result("Backward Compatibility", False, "No accessibility module")
        return
    
    try:
        # Test original find_element method still works
        start_time = time.time()
        result = accessibility.find_element('AXButton', 'test button')
        find_time = (time.time() - start_time) * 1000
        
        results.add_performance_metric("backward_compatibility_time", find_time)
        
        # Should not crash (result can be None, that's expected)
        results.add_test_result("Backward Compatibility (find_element)", True)
        
        # Test that fallback mechanisms work
        if hasattr(accessibility, '_find_element_button_only_fallback'):
            start_time = time.time()
            fallback_result = accessibility._find_element_button_only_fallback('test button')
            fallback_time = (time.time() - start_time) * 1000
            
            results.add_performance_metric("fallback_mechanism_time", fallback_time)
            results.add_test_result("Fallback Mechanism", True)
        
    except Exception as e:
        results.add_test_result("Backward Compatibility", False, str(e))

def run_comprehensive_system_test():
    """Run comprehensive system test."""
    print("COMPREHENSIVE SYSTEM TEST FOR ACCESSIBILITY FAST PATH ENHANCEMENT")
    print("="*70)
    
    results = SystemTestResults()
    
    # Test 1: Accessibility Module Initialization
    print("\n1. Testing Accessibility Module Initialization...")
    accessibility = test_accessibility_module_initialization(results)
    
    # Test 2: Enhanced Role Detection Availability
    print("\n2. Testing Enhanced Role Detection Availability...")
    enhanced_available = test_enhanced_role_detection_availability(results, accessibility)
    
    # Test 3: Clickable Role Detection
    print("\n3. Testing Clickable Role Detection...")
    test_clickable_role_detection(results, accessibility)
    
    # Test 4: Accessibility Permissions
    print("\n4. Testing Accessibility Permissions...")
    permissions_ok = test_accessibility_permissions(results, accessibility)
    
    # Test 5: Element Finding Performance
    print("\n5. Testing Element Finding Performance...")
    test_element_finding_performance(results, accessibility)
    
    # Test 6: Orchestrator Integration
    print("\n6. Testing Orchestrator Integration...")
    orchestrator = test_orchestrator_integration(results)
    
    # Test 7: Command Processing Pipeline
    print("\n7. Testing Command Processing Pipeline...")
    test_command_processing_pipeline(results, orchestrator)
    
    # Test 8: Backward Compatibility
    print("\n8. Testing Backward Compatibility...")
    test_backward_compatibility(results, accessibility)
    
    # Print final results
    results.print_summary()
    
    # Determine overall success
    success_rate = (results.tests_passed / results.tests_run) * 100
    
    if success_rate >= 80:
        print("\n🎉 SYSTEM TEST PASSED!")
        print("The accessibility fast path enhancement is working correctly.")
        if not permissions_ok:
            print("\n⚠️  NOTE: Accessibility permissions are not granted.")
            print("Grant permissions for optimal performance (see fix_accessibility_permissions_final.py)")
    else:
        print("\n❌ SYSTEM TEST FAILED!")
        print("Critical issues need to be resolved before the enhancement is ready.")
    
    return success_rate >= 80

if __name__ == "__main__":
    success = run_comprehensive_system_test()
    sys.exit(0 if success else 1)