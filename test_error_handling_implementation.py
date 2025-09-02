#!/usr/bin/env python3
"""
Test script to verify the enhanced error handling implementation for the hybrid architecture.

This script tests:
1. Accessibility-specific error handling
2. Fast path failure recovery
3. Automatic fallback triggering
4. Retry logic for transient errors
5. Logging and diagnostics for fast path failures
"""

import sys
import logging
import time
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_accessibility_error_handling():
    """Test accessibility-specific error handling."""
    logger.info("Testing accessibility error handling...")
    
    try:
        from modules.accessibility import (
            AccessibilityModule, 
            AccessibilityPermissionError,
            AccessibilityAPIUnavailableError,
            ElementNotFoundError,
            AccessibilityTimeoutError,
            AccessibilityTreeTraversalError,
            AccessibilityCoordinateError
        )
        
        # Test 1: Custom exception classes
        logger.info("✓ Custom exception classes imported successfully")
        
        # Test 2: Exception with recovery suggestions
        try:
            raise AccessibilityPermissionError("Test permission error", "Test recovery suggestion")
        except AccessibilityPermissionError as e:
            assert hasattr(e, 'recovery_suggestion')
            assert e.recovery_suggestion == "Test recovery suggestion"
            logger.info("✓ AccessibilityPermissionError with recovery suggestion works")
        
        # Test 3: ElementNotFoundError with element details
        try:
            raise ElementNotFoundError("Test element not found", "AXButton", "Test Button")
        except ElementNotFoundError as e:
            assert hasattr(e, 'element_role')
            assert hasattr(e, 'element_label')
            assert e.element_role == "AXButton"
            assert e.element_label == "Test Button"
            logger.info("✓ ElementNotFoundError with element details works")
        
        # Test 4: Mock accessibility module initialization with error handling
        with patch('modules.accessibility.ACCESSIBILITY_AVAILABLE', False):
            try:
                module = AccessibilityModule()
                assert module.degraded_mode == True
                assert module.accessibility_enabled == False
                logger.info("✓ AccessibilityModule handles missing frameworks gracefully")
            except Exception as e:
                logger.error(f"✗ AccessibilityModule initialization failed: {e}")
                return False
        
        return True
        
    except ImportError as e:
        logger.error(f"✗ Failed to import accessibility modules: {e}")
        return False
    except Exception as e:
        logger.error(f"✗ Accessibility error handling test failed: {e}")
        return False

def test_fast_path_retry_logic():
    """Test fast path retry logic and error recovery."""
    logger.info("Testing fast path retry logic...")
    
    try:
        from orchestrator import Orchestrator
        from modules.accessibility import AccessibilityTimeoutError, ElementNotFoundError
        
        # Create mock orchestrator
        orchestrator = Mock(spec=Orchestrator)
        
        # Test 1: Should retry logic
        orchestrator._should_retry_fast_path_error = Orchestrator._should_retry_fast_path_error.__get__(orchestrator)
        
        # Test retryable errors
        timeout_error = AccessibilityTimeoutError("Test timeout")
        assert orchestrator._should_retry_fast_path_error(timeout_error, 0, 2) == True
        logger.info("✓ Timeout errors are retryable")
        
        # Test non-retryable errors
        element_error = ElementNotFoundError("Test element not found")
        assert orchestrator._should_retry_fast_path_error(element_error, 0, 2) == False
        logger.info("✓ Element not found errors are not retryable")
        
        # Test max retries exceeded
        assert orchestrator._should_retry_fast_path_error(timeout_error, 2, 2) == False
        logger.info("✓ Max retries limit is respected")
        
        return True
        
    except ImportError as e:
        logger.error(f"✗ Failed to import orchestrator: {e}")
        return False
    except Exception as e:
        logger.error(f"✗ Fast path retry logic test failed: {e}")
        return False

def test_fallback_diagnostics():
    """Test fallback diagnostics and logging."""
    logger.info("Testing fallback diagnostics...")
    
    try:
        from orchestrator import Orchestrator
        
        # Create mock orchestrator
        orchestrator = Mock(spec=Orchestrator)
        orchestrator._categorize_fallback_reason = Orchestrator._categorize_fallback_reason.__get__(orchestrator)
        
        # Test fallback reason categorization
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
        logger.error(f"✗ Fallback diagnostics test failed: {e}")
        return False

def test_accessibility_status_and_diagnostics():
    """Test accessibility status and diagnostics methods."""
    logger.info("Testing accessibility status and diagnostics...")
    
    try:
        from modules.accessibility import AccessibilityModule
        
        # Mock the accessibility module to avoid actual system dependencies
        with patch('modules.accessibility.ACCESSIBILITY_AVAILABLE', True), \
             patch('modules.accessibility.AppKit') as mock_appkit, \
             patch('modules.accessibility.NSWorkspace') as mock_workspace:
            
            # Setup mocks
            mock_workspace.sharedWorkspace.return_value = Mock()
            mock_appkit.AXUIElementCreateSystemWide.return_value = Mock()
            
            module = AccessibilityModule()
            
            # Test status method
            status = module.get_accessibility_status()
            assert isinstance(status, dict)
            assert 'frameworks_available' in status
            assert 'api_initialized' in status
            assert 'degraded_mode' in status
            logger.info("✓ get_accessibility_status returns proper structure")
            
            # Test diagnostics method
            diagnostics = module.get_error_diagnostics()
            assert isinstance(diagnostics, dict)
            assert 'module_state' in diagnostics
            assert 'system_state' in diagnostics
            assert 'recovery_state' in diagnostics
            logger.info("✓ get_error_diagnostics returns proper structure")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Accessibility status and diagnostics test failed: {e}")
        return False

def test_error_recovery_mechanisms():
    """Test error recovery mechanisms."""
    logger.info("Testing error recovery mechanisms...")
    
    try:
        from modules.accessibility import AccessibilityModule
        
        # Mock the accessibility module
        with patch('modules.accessibility.ACCESSIBILITY_AVAILABLE', True), \
             patch('modules.accessibility.AppKit') as mock_appkit, \
             patch('modules.accessibility.NSWorkspace') as mock_workspace:
            
            # Setup mocks to simulate initial failure then success
            mock_workspace.sharedWorkspace.return_value = Mock()
            
            # First call fails, second succeeds
            mock_appkit.AXUIElementCreateSystemWide.side_effect = [None, Mock()]
            
            module = AccessibilityModule()
            
            # Should be in degraded mode initially
            assert module.degraded_mode == True
            logger.info("✓ Module enters degraded mode on initialization failure")
            
            # Test recovery attempt
            assert module._should_attempt_recovery() == False  # Too soon
            logger.info("✓ Recovery respects timing constraints")
            
            # Simulate time passing
            module.last_error_time = time.time() - 31  # More than permission_check_interval
            assert module._should_attempt_recovery() == True
            logger.info("✓ Recovery becomes available after time interval")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Error recovery mechanisms test failed: {e}")
        return False

def main():
    """Run all error handling tests."""
    logger.info("Starting error handling implementation tests...")
    
    tests = [
        ("Accessibility Error Handling", test_accessibility_error_handling),
        ("Fast Path Retry Logic", test_fast_path_retry_logic),
        ("Fallback Diagnostics", test_fallback_diagnostics),
        ("Accessibility Status and Diagnostics", test_accessibility_status_and_diagnostics),
        ("Error Recovery Mechanisms", test_error_recovery_mechanisms)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        logger.info(f"\n--- Running {test_name} ---")
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
    
    logger.info(f"\n--- Test Results ---")
    logger.info(f"Passed: {passed}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Total: {passed + failed}")
    
    if failed == 0:
        logger.info("🎉 All error handling tests passed!")
        return True
    else:
        logger.error(f"❌ {failed} test(s) failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)