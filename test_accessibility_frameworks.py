#!/usr/bin/env python3
"""
Test Accessibility Frameworks

This script tests if the PyObjC accessibility frameworks are working correctly.
"""

import logging
import sys

def setup_logging():
    """Setup logging for the test."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def test_pyobjc_imports():
    """Test PyObjC framework imports."""
    logger = logging.getLogger(__name__)
    logger.info("Testing PyObjC framework imports...")
    
    tests = [
        ("import objc", "PyObjC core"),
        ("from AppKit import NSWorkspace, NSApplication", "AppKit framework"),
        ("from ApplicationServices import AXUIElementCreateSystemWide, AXUIElementCopyAttributeValue", "ApplicationServices framework"),
    ]
    
    success_count = 0
    
    for import_statement, description in tests:
        try:
            exec(import_statement)
            logger.info(f"✅ {description} - SUCCESS")
            success_count += 1
        except ImportError as e:
            logger.error(f"❌ {description} - FAILED: {e}")
        except Exception as e:
            logger.error(f"❌ {description} - ERROR: {e}")
    
    return success_count == len(tests)

def test_accessibility_api():
    """Test basic accessibility API functionality."""
    logger = logging.getLogger(__name__)
    logger.info("Testing accessibility API functionality...")
    
    try:
        from ApplicationServices import (
            AXUIElementCreateSystemWide,
            AXUIElementCopyAttributeValue,
            kAXFocusedApplicationAttribute
        )
        
        # Test system-wide element creation
        system_wide = AXUIElementCreateSystemWide()
        if system_wide:
            logger.info("✅ System-wide element created successfully")
        else:
            logger.error("❌ Failed to create system-wide element")
            return False
        
        # Test focused application access
        try:
            focused_app_ref = AXUIElementCopyAttributeValue(
                system_wide, 
                kAXFocusedApplicationAttribute, 
                None
            )
            
            if focused_app_ref and focused_app_ref[0] == 0:
                logger.info("✅ Focused application access successful")
                return True
            else:
                logger.warning("⚠️  Focused application access returned no result")
                logger.info("This may be normal if no application has accessibility focus")
                return True
                
        except Exception as e:
            logger.error(f"❌ Focused application access failed: {e}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Accessibility API test failed: {e}")
        return False

def test_workspace_access():
    """Test NSWorkspace functionality."""
    logger = logging.getLogger(__name__)
    logger.info("Testing NSWorkspace functionality...")
    
    try:
        from AppKit import NSWorkspace
        
        # Get shared workspace
        workspace = NSWorkspace.sharedWorkspace()
        if not workspace:
            logger.error("❌ Failed to get shared workspace")
            return False
        
        # Get running applications
        running_apps = workspace.runningApplications()
        if running_apps:
            logger.info(f"✅ Found {len(running_apps)} running applications")
            
            # List some applications
            app_names = []
            for app in running_apps[:5]:  # Show first 5
                app_name = app.localizedName()
                if app_name:
                    app_names.append(app_name)
            
            if app_names:
                logger.info(f"Sample applications: {', '.join(app_names)}")
            
            return True
        else:
            logger.warning("⚠️  No running applications found")
            return False
            
    except Exception as e:
        logger.error(f"❌ NSWorkspace test failed: {e}")
        return False

def test_aura_accessibility_module():
    """Test AURA's accessibility module initialization."""
    logger = logging.getLogger(__name__)
    logger.info("Testing AURA accessibility module...")
    
    try:
        # Add project root to path
        from pathlib import Path
        project_root = Path(__file__).parent
        sys.path.insert(0, str(project_root))
        
        from modules.accessibility import AccessibilityModule
        
        # Initialize the module
        accessibility = AccessibilityModule()
        
        if accessibility.accessibility_enabled:
            logger.info("✅ AURA AccessibilityModule initialized successfully")
            
            # Test getting active application
            current_app = accessibility.get_active_application()
            if current_app:
                logger.info(f"✅ Active application: {current_app.get('name', 'Unknown')}")
            else:
                logger.warning("⚠️  No active application detected")
            
            return True
        else:
            logger.error("❌ AURA AccessibilityModule failed to initialize")
            return False
            
    except Exception as e:
        logger.error(f"❌ AURA accessibility module test failed: {e}")
        return False

def main():
    """Main test function."""
    logger = setup_logging()
    
    logger.info("Accessibility Frameworks Test")
    logger.info("=" * 40)
    
    tests = [
        ("PyObjC Imports", test_pyobjc_imports),
        ("Accessibility API", test_accessibility_api),
        ("NSWorkspace Access", test_workspace_access),
        ("AURA Accessibility Module", test_aura_accessibility_module),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n--- {test_name} ---")
        try:
            results[test_name] = test_func()
        except Exception as e:
            logger.error(f"❌ {test_name} failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    logger.info("\n" + "=" * 40)
    logger.info("TEST SUMMARY")
    logger.info("=" * 40)
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        logger.info("\n🎉 All accessibility framework tests passed!")
        logger.info("Your system is ready for Gmail click functionality.")
        logger.info("\nNext steps:")
        logger.info("1. Open Chrome with Google homepage")
        logger.info("2. Run: python test_gmail_click_with_chrome.py")
    else:
        logger.info("\n⚠️  Some tests failed.")
        logger.info("Please check the error messages above.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)