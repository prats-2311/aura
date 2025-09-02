#!/usr/bin/env python3
"""
Simple test to verify the enhanced error handling implementation.
"""

import logging
import sys

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_accessibility_exceptions():
    """Test that accessibility exceptions work correctly."""
    logger.info("Testing accessibility exception classes...")
    
    try:
        from modules.accessibility import (
            AccessibilityPermissionError,
            AccessibilityAPIUnavailableError,
            ElementNotFoundError,
            AccessibilityTimeoutError,
            AccessibilityTreeTraversalError,
            AccessibilityCoordinateError
        )
        
        # Test AccessibilityPermissionError
        try:
            raise AccessibilityPermissionError("Test error", "Test recovery")
        except AccessibilityPermissionError as e:
            assert hasattr(e, 'recovery_suggestion')
            assert e.recovery_suggestion == "Test recovery"
            logger.info("✓ AccessibilityPermissionError works correctly")
        
        # Test ElementNotFoundError
        try:
            raise ElementNotFoundError("Test error", "AXButton", "Test Button")
        except ElementNotFoundError as e:
            assert hasattr(e, 'element_role')
            assert hasattr(e, 'element_label')
            assert e.element_role == "AXButton"
            assert e.element_label == "Test Button"
            logger.info("✓ ElementNotFoundError works correctly")
        
        # Test other exceptions
        for exc_class in [AccessibilityAPIUnavailableError, AccessibilityTimeoutError, 
                         AccessibilityTreeTraversalError, AccessibilityCoordinateError]:
            try:
                raise exc_class("Test error")
            except exc_class:
                logger.info(f"✓ {exc_class.__name__} works correctly")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Exception test failed: {e}")
        return False

def test_accessibility_module_degraded_mode():
    """Test that accessibility module handles degraded mode correctly."""
    logger.info("Testing accessibility module degraded mode...")
    
    try:
        from modules.accessibility import AccessibilityModule
        
        # The module should handle missing frameworks gracefully
        module = AccessibilityModule()
        
        # Check that it has the new attributes
        assert hasattr(module, 'degraded_mode')
        assert hasattr(module, 'error_count')
        assert hasattr(module, 'recovery_attempts')
        assert hasattr(module, 'max_recovery_attempts')
        
        logger.info("✓ AccessibilityModule has degraded mode attributes")
        
        # Check that it has the new methods
        assert hasattr(module, 'get_error_diagnostics')
        assert hasattr(module, '_attempt_recovery')
        assert hasattr(module, '_should_attempt_recovery')
        assert hasattr(module, '_handle_accessibility_error')
        
        logger.info("✓ AccessibilityModule has error recovery methods")
        
        # Test status method
        status = module.get_accessibility_status()
        assert isinstance(status, dict)
        assert 'degraded_mode' in status
        assert 'error_count' in status
        assert 'recovery_attempts' in status
        
        logger.info("✓ get_accessibility_status includes new fields")
        
        # Test diagnostics method
        diagnostics = module.get_error_diagnostics()
        assert isinstance(diagnostics, dict)
        assert 'module_state' in diagnostics
        assert 'recovery_state' in diagnostics
        
        logger.info("✓ get_error_diagnostics works correctly")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Degraded mode test failed: {e}")
        return False

def test_orchestrator_retry_logic():
    """Test orchestrator retry logic methods."""
    logger.info("Testing orchestrator retry logic...")
    
    try:
        from orchestrator import Orchestrator
        from modules.accessibility import (
            AccessibilityPermissionError,
            ElementNotFoundError,
            AccessibilityTimeoutError
        )
        
        # Create a mock orchestrator instance to test the methods
        class TestOrchestrator:
            def _should_retry_fast_path_error(self, error, attempt, max_retries):
                return Orchestrator._should_retry_fast_path_error(self, error, attempt, max_retries)
            
            def _categorize_fallback_reason(self, failure_reason):
                return Orchestrator._categorize_fallback_reason(self, failure_reason)
        
        orchestrator = TestOrchestrator()
        
        # Test retry logic
        timeout_error = AccessibilityTimeoutError("Test timeout")
        assert orchestrator._should_retry_fast_path_error(timeout_error, 0, 2) == True
        logger.info("✓ Timeout errors are retryable")
        
        permission_error = AccessibilityPermissionError("Test permission")
        assert orchestrator._should_retry_fast_path_error(permission_error, 0, 2) == False
        logger.info("✓ Permission errors are not retryable")
        
        element_error = ElementNotFoundError("Test element not found")
        assert orchestrator._should_retry_fast_path_error(element_error, 0, 2) == False
        logger.info("✓ Element not found errors are not retryable")
        
        # Test max retries
        assert orchestrator._should_retry_fast_path_error(timeout_error, 2, 2) == False
        logger.info("✓ Max retries limit is respected")
        
        # Test fallback categorization
        test_cases = [
            ('element_not_found', 'element_detection'),
            ('accessibility_degraded', 'accessibility_issue'),
            ('action_failed', 'action_execution'),
            ('unknown_reason', 'unknown')
        ]
        
        for reason, expected_category in test_cases:
            category = orchestrator._categorize_fallback_reason(reason)
            assert category == expected_category
            logger.info(f"✓ Fallback reason '{reason}' categorized as '{category}'")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Orchestrator retry logic test failed: {e}")
        return False

def main():
    """Run all tests."""
    logger.info("Starting error handling implementation verification...")
    
    tests = [
        ("Accessibility Exceptions", test_accessibility_exceptions),
        ("Accessibility Module Degraded Mode", test_accessibility_module_degraded_mode),
        ("Orchestrator Retry Logic", test_orchestrator_retry_logic)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        logger.info(f"\n--- {test_name} ---")
        try:
            if test_func():
                logger.info(f"✓ {test_name} PASSED")
                passed += 1
            else:
                logger.error(f"✗ {test_name} FAILED")
                failed += 1
        except Exception as e:
            logger.error(f"✗ {test_name} FAILED with exception: {e}")
            failed += 1
    
    logger.info(f"\n--- Results ---")
    logger.info(f"Passed: {passed}/{len(tests)}")
    
    if failed == 0:
        logger.info("🎉 All error handling implementation tests passed!")
        return True
    else:
        logger.error(f"❌ {failed} test(s) failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)