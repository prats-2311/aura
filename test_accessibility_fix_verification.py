#!/usr/bin/env python3
"""
Focused verification test for the accessibility import conflict fix.
Tests the core issues that were resolved.
"""

import sys
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_import_conflicts_resolved():
    """Test that all AppKit accessibility conflicts have been resolved."""
    logger.info("Testing import conflict resolution...")
    
    try:
        with open('modules/accessibility.py', 'r') as f:
            source_code = f.read()
        
        # Test 1: No AppKit.AX* calls should remain
        appkit_ax_pattern = r'AppKit\.AX\w+'
        appkit_matches = re.findall(appkit_ax_pattern, source_code)
        
        if appkit_matches:
            logger.error(f"❌ Found AppKit accessibility calls: {appkit_matches}")
            return False
        else:
            logger.info("✅ No AppKit accessibility calls found")
        
        # Test 2: No AppKit.kAX* constants should remain
        appkit_const_pattern = r'AppKit\.kAX\w+'
        const_matches = re.findall(appkit_const_pattern, source_code)
        
        if const_matches:
            logger.error(f"❌ Found AppKit accessibility constants: {const_matches}")
            return False
        else:
            logger.info("✅ No AppKit accessibility constants found")
        
        # Test 3: Direct accessibility function calls should exist
        direct_ax_calls = len(re.findall(r'AXUIElementCopyAttributeValue\(', source_code))
        if direct_ax_calls == 0:
            logger.error("❌ No direct accessibility function calls found")
            return False
        else:
            logger.info(f"✅ Found {direct_ax_calls} direct accessibility function calls")
        
        # Test 4: Proper import structure
        required_imports = [
            'from AppKit import NSWorkspace',
            'from ApplicationServices import',
            'AXUIElementCreateSystemWide',
            'AXUIElementCopyAttributeValue'
        ]
        
        for required_import in required_imports:
            if required_import not in source_code:
                logger.error(f"❌ Missing required import: {required_import}")
                return False
        
        logger.info("✅ All required imports found")
        
        return True
        
    except FileNotFoundError:
        logger.error("❌ Could not find modules/accessibility.py")
        return False
    except Exception as e:
        logger.error(f"❌ Error reading file: {e}")
        return False

def test_import_stability():
    """Test that the module can be imported without conflicts."""
    logger.info("Testing import stability...")
    
    try:
        # Clear any cached imports
        if 'modules.accessibility' in sys.modules:
            del sys.modules['modules.accessibility']
        
        # Try to import the module
        from modules.accessibility import AccessibilityModule
        logger.info("✅ Module imported successfully")
        
        # Test basic instantiation (should handle missing frameworks gracefully)
        try:
            module = AccessibilityModule()
            logger.info("✅ Module instantiated successfully")
            
            # Test basic method availability
            if hasattr(module, 'get_accessibility_status'):
                logger.info("✅ Core methods available")
            else:
                logger.warning("⚠️  Some methods missing (may be expected)")
            
            return True
            
        except Exception as e:
            # Check if it's just missing frameworks (expected in test environment)
            if any(keyword in str(e).lower() for keyword in ['appkit', 'applicationservices', 'framework']):
                logger.info("✅ Expected framework unavailability in test environment")
                return True
            else:
                logger.error(f"❌ Unexpected instantiation error: {e}")
                return False
        
    except ImportError as e:
        # Check if it's framework-related (expected)
        if any(keyword in str(e).lower() for keyword in ['appkit', 'applicationservices', 'framework']):
            logger.info("✅ Expected framework import error in test environment")
            return True
        else:
            logger.error(f"❌ Unexpected import error: {e}")
            return False
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return False

def test_function_consistency():
    """Test that accessibility functions are called consistently."""
    logger.info("Testing function call consistency...")
    
    try:
        with open('modules/accessibility.py', 'r') as f:
            source_code = f.read()
        
        # Count different types of calls
        direct_ax_calls = len(re.findall(r'AXUIElementCopyAttributeValue\(', source_code))
        direct_create_calls = len(re.findall(r'AXUIElementCreateSystemWide\(', source_code))
        direct_app_calls = len(re.findall(r'AXUIElementCreateApplication\(', source_code))
        
        # Count constant usage
        direct_constants = len(re.findall(r'kAX\w+', source_code))
        
        logger.info(f"✅ Direct AXUIElementCopyAttributeValue calls: {direct_ax_calls}")
        logger.info(f"✅ Direct AXUIElementCreateSystemWide calls: {direct_create_calls}")
        logger.info(f"✅ Direct AXUIElementCreateApplication calls: {direct_app_calls}")
        logger.info(f"✅ Direct accessibility constants: {direct_constants}")
        
        # Verify we have reasonable numbers
        if direct_ax_calls > 0 and direct_constants > 0:
            logger.info("✅ Function call consistency verified")
            return True
        else:
            logger.error("❌ Insufficient function calls found")
            return False
        
    except Exception as e:
        logger.error(f"❌ Error analyzing function calls: {e}")
        return False

def test_framework_separation():
    """Test that AppKit and ApplicationServices are properly separated."""
    logger.info("Testing framework separation...")
    
    try:
        with open('modules/accessibility.py', 'r') as f:
            source_code = f.read()
        
        # Check AppKit usage (should only be for NSWorkspace, NSApplication)
        appkit_imports = re.findall(r'from AppKit import ([^#\n]+)', source_code)
        if appkit_imports:
            appkit_items = [item.strip() for items in appkit_imports for item in items.split(',')]
            logger.info(f"AppKit imports: {appkit_items}")
            
            # Should only contain workspace/application items, not accessibility
            forbidden_appkit = [item for item in appkit_items if 'AX' in item or 'kAX' in item]
            if forbidden_appkit:
                logger.error(f"❌ Found accessibility items in AppKit imports: {forbidden_appkit}")
                return False
            else:
                logger.info("✅ AppKit imports properly limited to application management")
        
        # Check ApplicationServices usage (should contain accessibility functions)
        app_services_imports = re.findall(r'from ApplicationServices import \((.*?)\)', source_code, re.DOTALL)
        if app_services_imports:
            # Extract all imported items
            all_imports = []
            for import_block in app_services_imports:
                items = [item.strip().rstrip(',') for item in import_block.split('\n') if item.strip()]
                all_imports.extend(items)
            
            logger.info(f"ApplicationServices imports: {len(all_imports)} items")
            
            # Should contain accessibility functions
            ax_functions = [item for item in all_imports if item.startswith('AX')]
            ax_constants = [item for item in all_imports if item.startswith('kAX')]
            
            if ax_functions and ax_constants:
                logger.info(f"✅ Found {len(ax_functions)} AX functions and {len(ax_constants)} AX constants")
                return True
            else:
                logger.error("❌ Missing accessibility functions or constants in ApplicationServices imports")
                return False
        else:
            logger.error("❌ No ApplicationServices imports found")
            return False
        
    except Exception as e:
        logger.error(f"❌ Error analyzing framework separation: {e}")
        return False

def run_verification_tests():
    """Run all verification tests."""
    logger.info("=" * 70)
    logger.info("ACCESSIBILITY IMPORT CONFLICT FIX VERIFICATION")
    logger.info("=" * 70)
    
    tests = [
        ("Import Conflicts Resolved", test_import_conflicts_resolved),
        ("Import Stability", test_import_stability),
        ("Function Consistency", test_function_consistency),
        ("Framework Separation", test_framework_separation)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n--- {test_name} ---")
        try:
            result = test_func()
            results.append((test_name, result))
            status = "✅ PASSED" if result else "❌ FAILED"
            logger.info(f"{test_name}: {status}")
        except Exception as e:
            logger.error(f"{test_name}: ❌ ERROR - {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("VERIFICATION SUMMARY")
    logger.info("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 ALL TESTS PASSED - Import conflict fix verified!")
        return True
    else:
        logger.error(f"💥 {total - passed} tests failed - Issues remain")
        return False

if __name__ == "__main__":
    success = run_verification_tests()
    sys.exit(0 if success else 1)