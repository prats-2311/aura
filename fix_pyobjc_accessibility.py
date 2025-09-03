#!/usr/bin/env python3
"""
PyObjC Accessibility Fix

This script fixes the specific PyObjC import issue with AXUIElementCreateSystemWide
and other accessibility functions.
"""

import subprocess
import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def fix_pyobjc_accessibility_imports():
    """Fix PyObjC accessibility import issues."""
    logger.info("🔧 Fixing PyObjC accessibility imports...")
    
    try:
        # The issue is that AXUIElementCreateSystemWide is in ApplicationServices, not AppKit
        logger.info("Testing correct import path...")
        
        # Test the correct import
        test_code = '''
try:
    # Correct way to import accessibility functions
    from ApplicationServices import AXUIElementCreateSystemWide
    print("✅ AXUIElementCreateSystemWide imported from ApplicationServices")
    
    # Test creating system-wide element
    system_wide = AXUIElementCreateSystemWide()
    if system_wide:
        print("✅ AXUIElementCreateSystemWide() successful - Accessibility permissions granted!")
    else:
        print("❌ AXUIElementCreateSystemWide() returned None - Permissions needed")
        
except ImportError as e:
    print(f"❌ Import failed: {e}")
    
    # Try alternative import
    try:
        import Accessibility
        print("✅ Accessibility framework available")
        
        # Try to access the function through objc
        import objc
        ApplicationServices = objc.loadBundle('ApplicationServices', globals())
        print("✅ ApplicationServices bundle loaded")
        
    except Exception as e2:
        print(f"❌ Alternative import failed: {e2}")
        
except Exception as e:
    print(f"❌ Error: {e}")
'''
        
        # Run the test
        result = subprocess.run([sys.executable, '-c', test_code], 
                              capture_output=True, text=True)
        
        print("Test Results:")
        print(result.stdout)
        if result.stderr:
            print("Errors:")
            print(result.stderr)
        
        return result.returncode == 0
        
    except Exception as e:
        logger.error(f"Error testing imports: {e}")
        return False

def create_fixed_accessibility_module():
    """Create a fixed version of the accessibility module."""
    logger.info("📝 Creating fixed accessibility module...")
    
    fixed_code = '''#!/usr/bin/env python3
"""
Fixed Accessibility Module Test

This version uses the correct import paths for macOS accessibility functions.
"""

def test_accessibility_fixed():
    print("🧪 Testing Fixed Accessibility Implementation...")
    
    try:
        # Method 1: Import from ApplicationServices (correct way)
        try:
            from ApplicationServices import AXUIElementCreateSystemWide
            print("✅ Method 1: AXUIElementCreateSystemWide imported from ApplicationServices")
            
            # Test system-wide element creation
            system_wide = AXUIElementCreateSystemWide()
            if system_wide:
                print("✅ System-wide element created successfully!")
                print("🎉 Accessibility permissions are working!")
                return True
            else:
                print("❌ System-wide element creation returned None")
                print("📋 This means accessibility permissions are not granted")
                return False
                
        except ImportError:
            print("⚠️  Method 1 failed, trying Method 2...")
            
            # Method 2: Load bundle manually
            import objc
            bundle = objc.loadBundle('ApplicationServices', globals())
            
            if 'AXUIElementCreateSystemWide' in globals():
                print("✅ Method 2: AXUIElementCreateSystemWide loaded via bundle")
                
                system_wide = AXUIElementCreateSystemWide()
                if system_wide:
                    print("✅ System-wide element created successfully!")
                    print("🎉 Accessibility permissions are working!")
                    return True
                else:
                    print("❌ System-wide element creation returned None")
                    return False
            else:
                print("❌ Method 2: Could not load AXUIElementCreateSystemWide")
                return False
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_nsworkspace():
    print("\\n🧪 Testing NSWorkspace...")
    
    try:
        from AppKit import NSWorkspace
        workspace = NSWorkspace.sharedWorkspace()
        
        if workspace:
            print("✅ NSWorkspace created successfully")
            
            # Get frontmost application
            app = workspace.frontmostApplication()
            if app:
                print(f"✅ Frontmost app: {app.localizedName()}")
            else:
                print("⚠️  No frontmost app detected")
            
            return True
        else:
            print("❌ NSWorkspace creation failed")
            return False
            
    except Exception as e:
        print(f"❌ NSWorkspace error: {e}")
        return False

def main():
    print("🔧 AURA Accessibility Fix Test")
    print("=" * 40)
    
    # Test accessibility
    accessibility_works = test_accessibility_fixed()
    
    # Test NSWorkspace
    nsworkspace_works = test_nsworkspace()
    
    print("\\n" + "=" * 40)
    print("📊 RESULTS:")
    print(f"Accessibility API: {'✅ Working' if accessibility_works else '❌ Not Working'}")
    print(f"NSWorkspace API: {'✅ Working' if nsworkspace_works else '❌ Not Working'}")
    
    if accessibility_works and nsworkspace_works:
        print("\\n🎉 All tests passed! AURA accessibility should work now.")
    elif nsworkspace_works:
        print("\\n⚠️  NSWorkspace works but accessibility permissions needed.")
        print("Please grant accessibility permissions in System Preferences.")
    else:
        print("\\n❌ Tests failed. PyObjC installation may need fixing.")

if __name__ == "__main__":
    main()
'''
    
    try:
        with open('test_accessibility_fixed.py', 'w') as f:
            f.write(fixed_code)
        logger.info("✅ Fixed test script created: test_accessibility_fixed.py")
        return True
    except Exception as e:
        logger.error(f"Error creating fixed script: {e}")
        return False

def update_aura_accessibility_module():
    """Update AURA's accessibility module with the correct imports."""
    logger.info("🔄 Updating AURA accessibility module...")
    
    try:
        # Read the current accessibility module
        with open('modules/accessibility.py', 'r') as f:
            content = f.read()
        
        # Check if it needs updating
        if 'from ApplicationServices import' in content:
            logger.info("✅ Accessibility module already has correct imports")
            return True
        
        # Create a backup
        with open('modules/accessibility.py.backup', 'w') as f:
            f.write(content)
        logger.info("✅ Backup created: modules/accessibility.py.backup")
        
        # Update the imports
        updated_content = content.replace(
            'import AppKit\nfrom AppKit import NSWorkspace, NSApplication\nimport Accessibility',
            '''import AppKit
from AppKit import NSWorkspace, NSApplication
import Accessibility

# Import accessibility functions from the correct framework
try:
    from ApplicationServices import (
        AXUIElementCreateSystemWide,
        AXUIElementCreateApplication,
        AXUIElementCopyAttributeValue,
        kAXFocusedApplicationAttribute,
        kAXRoleAttribute,
        kAXTitleAttribute,
        kAXDescriptionAttribute,
        kAXEnabledAttribute,
        kAXChildrenAttribute,
        kAXPositionAttribute,
        kAXSizeAttribute
    )
    ACCESSIBILITY_FUNCTIONS_AVAILABLE = True
except ImportError:
    # Fallback: try to load via objc bundle
    try:
        import objc
        bundle = objc.loadBundle('ApplicationServices', globals())
        ACCESSIBILITY_FUNCTIONS_AVAILABLE = 'AXUIElementCreateSystemWide' in globals()
    except:
        ACCESSIBILITY_FUNCTIONS_AVAILABLE = False'''
        )
        
        # Update the initialization check
        updated_content = updated_content.replace(
            'system_wide = AppKit.AXUIElementCreateSystemWide()',
            '''system_wide = None
            if ACCESSIBILITY_FUNCTIONS_AVAILABLE:
                system_wide = AXUIElementCreateSystemWide()'''
        )
        
        # Write the updated content
        with open('modules/accessibility.py', 'w') as f:
            f.write(updated_content)
        
        logger.info("✅ Accessibility module updated with correct imports")
        return True
        
    except Exception as e:
        logger.error(f"Error updating accessibility module: {e}")
        return False

def main():
    """Main function."""
    logger.info("🔧 PyObjC Accessibility Fix")
    logger.info("=" * 40)
    
    # Step 1: Test current imports
    logger.info("Step 1: Testing current PyObjC imports...")
    fix_pyobjc_accessibility_imports()
    print()
    
    # Step 2: Create fixed test script
    logger.info("Step 2: Creating fixed test script...")
    create_fixed_accessibility_module()
    print()
    
    # Step 3: Update AURA's accessibility module
    logger.info("Step 3: Updating AURA's accessibility module...")
    update_aura_accessibility_module()
    print()
    
    # Step 4: Test the fix
    logger.info("Step 4: Testing the fix...")
    logger.info("Run this command to test: python test_accessibility_fixed.py")
    print()
    
    logger.info("🎯 NEXT STEPS:")
    logger.info("1. Run: python test_accessibility_fixed.py")
    logger.info("2. If that works, try: python test_aura_commands.py health")
    logger.info("3. Grant accessibility permissions if prompted")

if __name__ == "__main__":
    main()