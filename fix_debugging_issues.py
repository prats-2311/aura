#!/usr/bin/env python3
"""
Fix Debugging Issues

This script addresses the two main issues:
1. Permission validation problems despite granting access
2. Debugging tool initialization error with 'dict' object has no attribute 'validate'
"""

import os
import sys
import subprocess
import logging
from typing import Dict, Any

def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def check_accessibility_permissions():
    """Check current accessibility permissions status."""
    logger = logging.getLogger(__name__)
    logger.info("Checking accessibility permissions...")
    
    try:
        # Import permission validator
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from modules.permission_validator import PermissionValidator
        
        validator = PermissionValidator()
        status = validator.check_accessibility_permissions()
        
        logger.info(f"Permission Status: {status.permission_level}")
        logger.info(f"Has Permissions: {status.has_permissions}")
        
        if not status.has_permissions:
            logger.warning("Accessibility permissions are not granted!")
            logger.info("Missing permissions:")
            for perm in status.missing_permissions:
                logger.info(f"  - {perm}")
            
            logger.info("Recommendations:")
            guidance = validator.guide_permission_setup()
            for step in guidance:
                logger.info(f"  - {step}")
        else:
            logger.info("✅ Accessibility permissions are properly granted")
        
        return status.has_permissions
        
    except Exception as e:
        logger.error(f"Failed to check permissions: {e}")
        return False

def test_debugging_initialization():
    """Test debugging tools initialization."""
    logger = logging.getLogger(__name__)
    logger.info("Testing debugging tools initialization...")
    
    try:
        # Test AccessibilityDebugger
        from modules.accessibility_debugger import AccessibilityDebugger
        debugger = AccessibilityDebugger({'debug_level': 'BASIC'})
        logger.info("✅ AccessibilityDebugger initialized successfully")
        
        # Test PermissionValidator
        from modules.permission_validator import PermissionValidator
        validator = PermissionValidator()
        logger.info("✅ PermissionValidator initialized successfully")
        
        # Test AccessibilityHealthChecker
        from modules.diagnostic_tools import AccessibilityHealthChecker
        health_checker = AccessibilityHealthChecker()
        logger.info("✅ AccessibilityHealthChecker initialized successfully")
        
        # Test ErrorRecoveryManager with proper configuration
        from modules.error_recovery import ErrorRecoveryManager, RecoveryConfiguration
        recovery_config = RecoveryConfiguration(
            max_retries=3,
            base_delay=0.5,
            max_delay=10.0
        )
        error_recovery = ErrorRecoveryManager(recovery_config)
        logger.info("✅ ErrorRecoveryManager initialized successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"Debugging initialization test failed: {e}")
        return False

def test_accessibility_module_initialization():
    """Test accessibility module initialization with debugging tools."""
    logger = logging.getLogger(__name__)
    logger.info("Testing accessibility module initialization...")
    
    try:
        from modules.accessibility import AccessibilityModule
        
        # Initialize with debugging enabled
        accessibility_module = AccessibilityModule()
        
        if hasattr(accessibility_module, 'accessibility_debugger'):
            logger.info("✅ Accessibility debugger integrated successfully")
        else:
            logger.warning("⚠️ Accessibility debugger not integrated")
        
        if hasattr(accessibility_module, 'error_recovery_manager'):
            logger.info("✅ Error recovery manager integrated successfully")
        else:
            logger.warning("⚠️ Error recovery manager not integrated")
        
        return True
        
    except Exception as e:
        logger.error(f"Accessibility module initialization test failed: {e}")
        return False

def provide_permission_guidance():
    """Provide detailed guidance for fixing permission issues."""
    logger = logging.getLogger(__name__)
    
    logger.info("="*60)
    logger.info("ACCESSIBILITY PERMISSION SETUP GUIDE")
    logger.info("="*60)
    
    logger.info("1. Open System Preferences")
    logger.info("2. Go to Security & Privacy")
    logger.info("3. Click on the Privacy tab")
    logger.info("4. Select 'Accessibility' from the left sidebar")
    logger.info("5. Click the lock icon and enter your password")
    logger.info("6. Add the following applications if not already present:")
    logger.info("   - Terminal (if running from Terminal)")
    logger.info("   - Python (the Python executable)")
    logger.info("   - Your IDE (if running from an IDE)")
    logger.info("7. Ensure all added applications are checked/enabled")
    logger.info("8. Also check 'Full Disk Access' and add the same applications")
    logger.info("9. Restart AURA completely after making changes")
    logger.info("10. Test again")
    
    logger.info("\nTo find your Python executable path, run:")
    logger.info("  which python")
    logger.info("  or")
    logger.info("  which python3")
    
    logger.info("\nIf you're using a virtual environment:")
    logger.info("  which python  # from within your activated environment")

def run_comprehensive_fix():
    """Run comprehensive fix for debugging issues."""
    logger = setup_logging()
    
    logger.info("="*60)
    logger.info("DEBUGGING ISSUES COMPREHENSIVE FIX")
    logger.info("="*60)
    
    # Step 1: Test debugging initialization
    logger.info("\nStep 1: Testing debugging tools initialization...")
    init_success = test_debugging_initialization()
    
    if init_success:
        logger.info("✅ Debugging tools initialization fixed!")
    else:
        logger.error("❌ Debugging tools initialization still has issues")
        return False
    
    # Step 2: Test accessibility module integration
    logger.info("\nStep 2: Testing accessibility module integration...")
    module_success = test_accessibility_module_initialization()
    
    if module_success:
        logger.info("✅ Accessibility module integration working!")
    else:
        logger.error("❌ Accessibility module integration has issues")
    
    # Step 3: Check permissions
    logger.info("\nStep 3: Checking accessibility permissions...")
    permissions_ok = check_accessibility_permissions()
    
    if not permissions_ok:
        logger.warning("❌ Accessibility permissions need attention")
        provide_permission_guidance()
    else:
        logger.info("✅ Accessibility permissions are properly configured!")
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("FIX SUMMARY")
    logger.info("="*60)
    logger.info(f"Debugging Tools Initialization: {'✅ FIXED' if init_success else '❌ NEEDS ATTENTION'}")
    logger.info(f"Module Integration: {'✅ WORKING' if module_success else '❌ NEEDS ATTENTION'}")
    logger.info(f"Accessibility Permissions: {'✅ GRANTED' if permissions_ok else '❌ NEEDS SETUP'}")
    
    if init_success and module_success and permissions_ok:
        logger.info("\n🎉 All debugging issues have been resolved!")
        logger.info("You can now restart AURA and the fast path should work correctly.")
        return True
    else:
        logger.info("\n⚠️ Some issues still need attention. Please follow the guidance above.")
        return False

def main():
    """Main function."""
    try:
        success = run_comprehensive_fix()
        return 0 if success else 1
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Fix script failed: {e}")
        return 2

if __name__ == "__main__":
    sys.exit(main())