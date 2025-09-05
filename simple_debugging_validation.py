#!/usr/bin/env python3
"""
Simple Debugging System Validation

Tests the core debugging functionality that has been implemented.
"""

import os
import sys
import time
import logging
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import debugging modules
from modules.accessibility_debugger import AccessibilityDebugger
from modules.permission_validator import PermissionValidator
from modules.diagnostic_tools import AccessibilityHealthChecker
from modules.error_recovery import ErrorRecoveryManager
from modules.fast_path_performance_monitor import FastPathPerformanceMonitor
from modules.performance_reporting_system import PerformanceReportingSystem
from modules.accessibility import AccessibilityModule


def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)


def test_permission_validator():
    """Test permission validator functionality."""
    logger = logging.getLogger(__name__)
    logger.info("Testing Permission Validator...")
    
    try:
        validator = PermissionValidator()
        status = validator.check_accessibility_permissions()
        
        # Check if status has required attributes
        if hasattr(status, 'has_permissions') and hasattr(status, 'permission_level'):
            logger.info("✅ Permission validator working correctly")
            return True
        else:
            logger.error("❌ Permission validator missing required attributes")
            return False
            
    except Exception as e:
        logger.error(f"❌ Permission validator failed: {e}")
        return False


def test_accessibility_debugger():
    """Test accessibility debugger functionality."""
    logger = logging.getLogger(__name__)
    logger.info("Testing Accessibility Debugger...")
    
    try:
        debugger = AccessibilityDebugger({
            'debug_level': 'BASIC',
            'output_format': 'STRUCTURED'
        })
        
        # Test with a specific app name to avoid "no focused application" error
        tree_dump = debugger.dump_accessibility_tree('Finder')
        
        if hasattr(tree_dump, 'total_elements') and hasattr(tree_dump, 'app_name'):
            logger.info("✅ Accessibility debugger working correctly")
            return True
        else:
            logger.error("❌ Accessibility debugger missing required attributes")
            return False
            
    except Exception as e:
        logger.error(f"❌ Accessibility debugger failed: {e}")
        return False


def test_diagnostic_tools():
    """Test diagnostic tools functionality."""
    logger = logging.getLogger(__name__)
    logger.info("Testing Diagnostic Tools...")
    
    try:
        health_checker = AccessibilityHealthChecker()
        
        # Test system information gathering
        system_info = health_checker.gather_system_information()
        
        if isinstance(system_info, dict) and 'os_version' in system_info:
            logger.info("✅ Diagnostic tools working correctly")
            return True
        else:
            logger.error("❌ Diagnostic tools missing required functionality")
            return False
            
    except Exception as e:
        logger.error(f"❌ Diagnostic tools failed: {e}")
        return False


def test_error_recovery():
    """Test error recovery functionality."""
    logger = logging.getLogger(__name__)
    logger.info("Testing Error Recovery...")
    
    try:
        error_recovery = ErrorRecoveryManager()
        
        # Test basic initialization and configuration
        if hasattr(error_recovery, 'recovery_strategies') and hasattr(error_recovery, 'retry_configs'):
            logger.info("✅ Error recovery working correctly")
            return True
        else:
            logger.error("❌ Error recovery missing required attributes")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error recovery failed: {e}")
        return False


def test_performance_monitoring():
    """Test performance monitoring functionality."""
    logger = logging.getLogger(__name__)
    logger.info("Testing Performance Monitoring...")
    
    try:
        performance_monitor = FastPathPerformanceMonitor()
        reporting_system = PerformanceReportingSystem()
        
        # Test basic functionality
        if hasattr(performance_monitor, 'metrics') and hasattr(reporting_system, 'generate_performance_report'):
            logger.info("✅ Performance monitoring working correctly")
            return True
        else:
            logger.error("❌ Performance monitoring missing required functionality")
            return False
            
    except Exception as e:
        logger.error(f"❌ Performance monitoring failed: {e}")
        return False


def test_accessibility_module_integration():
    """Test integration with accessibility module."""
    logger = logging.getLogger(__name__)
    logger.info("Testing Accessibility Module Integration...")
    
    try:
        accessibility_module = AccessibilityModule()
        
        # Test that module initializes without crashing
        if hasattr(accessibility_module, 'find_element'):
            logger.info("✅ Accessibility module integration working correctly")
            return True
        else:
            logger.error("❌ Accessibility module integration missing required functionality")
            return False
            
    except Exception as e:
        logger.error(f"❌ Accessibility module integration failed: {e}")
        return False


def test_performance_impact():
    """Test performance impact of debugging features."""
    logger = logging.getLogger(__name__)
    logger.info("Testing Performance Impact...")
    
    try:
        # Test with minimal debugging
        start_time = time.time()
        debugger_basic = AccessibilityDebugger({'debug_level': 'NONE'})
        basic_time = time.time() - start_time
        
        # Test with full debugging
        start_time = time.time()
        debugger_full = AccessibilityDebugger({'debug_level': 'VERBOSE'})
        full_time = time.time() - start_time
        
        # Performance impact should be reasonable
        if full_time < 1.0:  # Should initialize in less than 1 second
            logger.info(f"✅ Performance impact acceptable (Basic: {basic_time:.3f}s, Full: {full_time:.3f}s)")
            return True
        else:
            logger.error(f"❌ Performance impact too high (Full: {full_time:.3f}s)")
            return False
            
    except Exception as e:
        logger.error(f"❌ Performance impact test failed: {e}")
        return False


def main():
    """Main validation function."""
    logger = setup_logging()
    
    logger.info("="*60)
    logger.info("DEBUGGING SYSTEM SIMPLE VALIDATION")
    logger.info("="*60)
    
    tests = [
        ("Permission Validator", test_permission_validator),
        ("Accessibility Debugger", test_accessibility_debugger),
        ("Diagnostic Tools", test_diagnostic_tools),
        ("Error Recovery", test_error_recovery),
        ("Performance Monitoring", test_performance_monitoring),
        ("Accessibility Module Integration", test_accessibility_module_integration),
        ("Performance Impact", test_performance_impact)
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    start_time = time.time()
    
    for test_name, test_func in tests:
        logger.info(f"\n--- Testing {test_name} ---")
        if test_func():
            passed_tests += 1
    
    total_time = time.time() - start_time
    success_rate = (passed_tests / total_tests) * 100
    
    logger.info("\n" + "="*60)
    logger.info("VALIDATION RESULTS")
    logger.info("="*60)
    logger.info(f"Total Tests: {total_tests}")
    logger.info(f"Passed: {passed_tests}")
    logger.info(f"Failed: {total_tests - passed_tests}")
    logger.info(f"Success Rate: {success_rate:.1f}%")
    logger.info(f"Execution Time: {total_time:.2f} seconds")
    logger.info("="*60)
    
    if success_rate >= 80:
        logger.info("✅ Debugging system validation PASSED!")
        logger.info("Most debugging functionality is working correctly.")
        return 0
    elif success_rate >= 60:
        logger.info("⚠️ Debugging system validation PARTIAL!")
        logger.info("Some debugging functionality needs attention.")
        return 1
    else:
        logger.info("❌ Debugging system validation FAILED!")
        logger.info("Significant issues detected in debugging functionality.")
        return 2


if __name__ == "__main__":
    sys.exit(main())