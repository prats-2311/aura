#!/usr/bin/env python3
"""
AURA Accessibility Permissions Fix

This script diagnoses and fixes accessibility permission issues on macOS,
specifically for PyObjC framework integration.
"""

import subprocess
import sys
import os
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def check_system_integrity_protection():
    """Check if System Integrity Protection is affecting accessibility."""
    logger.info("🔒 Checking System Integrity Protection (SIP) status...")
    
    try:
        result = subprocess.run(['csrutil', 'status'], capture_output=True, text=True)
        sip_status = result.stdout.strip()
        logger.info(f"SIP Status: {sip_status}")
        
        if "enabled" in sip_status.lower():
            logger.info("✅ SIP is enabled (normal)")
            return True
        else:
            logger.warning("⚠️  SIP is disabled - this may cause accessibility issues")
            return False
            
    except Exception as e:
        logger.warning(f"Could not check SIP status: {e}")
        return None

def check_tcc_database():
    """Check the TCC (Transparency, Consent, and Control) database for accessibility permissions."""
    logger.info("🗄️  Checking TCC database for accessibility permissions...")
    
    try:
        # Check current user's TCC database
        tcc_db = os.path.expanduser("~/Library/Application Support/com.apple.TCC/TCC.db")
        
        if os.path.exists(tcc_db):
            logger.info("✅ User TCC database found")
            
            # Try to query the database (requires sqlite3)
            try:
                result = subprocess.run([
                    'sqlite3', tcc_db,
                    "SELECT client, auth_value FROM access WHERE service='kTCCServiceAccessibility';"
                ], capture_output=True, text=True)
                
                if result.stdout:
                    logger.info("📋 Accessibility permissions in TCC database:")
                    for line in result.stdout.strip().split('\n'):
                        if line:
                            client, auth = line.split('|')
                            status = "✅ Allowed" if auth == '2' else "❌ Denied"
                            logger.info(f"  {client}: {status}")
                else:
                    logger.warning("⚠️  No accessibility permissions found in TCC database")
                    
            except Exception as e:
                logger.warning(f"Could not query TCC database: {e}")
        else:
            logger.warning("⚠️  User TCC database not found")
            
    except Exception as e:
        logger.error(f"Error checking TCC database: {e}")

def reset_accessibility_permissions():
    """Reset accessibility permissions for the current application."""
    logger.info("🔄 Attempting to reset accessibility permissions...")
    
    try:
        # Get the current application bundle ID or executable path
        current_app = None
        
        # Check if running from Terminal
        if 'Terminal' in os.environ.get('TERM_PROGRAM', ''):
            current_app = 'com.apple.Terminal'
            logger.info("Detected Terminal as current application")
        
        # Check if running from an IDE
        elif 'KIRO' in os.environ.get('TERM_PROGRAM', '').upper():
            current_app = 'Kiro'
            logger.info("Detected Kiro as current application")
        
        if current_app:
            # Try to reset permissions using tccutil
            logger.info(f"Resetting accessibility permissions for {current_app}...")
            
            # Remove existing permission
            subprocess.run([
                'tccutil', 'reset', 'Accessibility', current_app
            ], capture_output=True)
            
            logger.info("✅ Permissions reset. You'll need to re-grant them in System Preferences.")
            return True
        else:
            logger.warning("Could not determine current application for permission reset")
            return False
            
    except Exception as e:
        logger.error(f"Error resetting permissions: {e}")
        return False

def test_pyobjc_accessibility():
    """Test PyObjC accessibility framework step by step."""
    logger.info("🧪 Testing PyObjC accessibility framework...")
    
    test_results = {}
    
    # Test 1: Basic PyObjC import
    try:
        import objc
        logger.info("✅ Test 1: PyObjC core import successful")
        test_results['pyobjc_core'] = True
    except ImportError as e:
        logger.error(f"❌ Test 1: PyObjC core import failed: {e}")
        test_results['pyobjc_core'] = False
        return test_results
    
    # Test 2: AppKit import
    try:
        import AppKit
        logger.info("✅ Test 2: AppKit import successful")
        test_results['appkit'] = True
    except ImportError as e:
        logger.error(f"❌ Test 2: AppKit import failed: {e}")
        test_results['appkit'] = False
        return test_results
    
    # Test 3: NSWorkspace import
    try:
        from AppKit import NSWorkspace
        logger.info("✅ Test 3: NSWorkspace import successful")
        test_results['nsworkspace'] = True
    except ImportError as e:
        logger.error(f"❌ Test 3: NSWorkspace import failed: {e}")
        test_results['nsworkspace'] = False
        return test_results
    
    # Test 4: NSWorkspace instantiation
    try:
        workspace = NSWorkspace.sharedWorkspace()
        if workspace:
            logger.info("✅ Test 4: NSWorkspace instantiation successful")
            test_results['workspace_instance'] = True
        else:
            logger.error("❌ Test 4: NSWorkspace returned None")
            test_results['workspace_instance'] = False
    except Exception as e:
        logger.error(f"❌ Test 4: NSWorkspace instantiation failed: {e}")
        test_results['workspace_instance'] = False
    
    # Test 5: Accessibility framework import
    try:
        import Accessibility
        logger.info("✅ Test 5: Accessibility framework import successful")
        test_results['accessibility_framework'] = True
    except ImportError as e:
        logger.error(f"❌ Test 5: Accessibility framework import failed: {e}")
        test_results['accessibility_framework'] = False
    
    # Test 6: AXUIElement creation
    try:
        from AppKit import AXUIElementCreateSystemWide
        system_wide = AXUIElementCreateSystemWide()
        if system_wide:
            logger.info("✅ Test 6: AXUIElementCreateSystemWide successful")
            test_results['axui_element'] = True
        else:
            logger.error("❌ Test 6: AXUIElementCreateSystemWide returned None (permissions issue)")
            test_results['axui_element'] = False
    except Exception as e:
        logger.error(f"❌ Test 6: AXUIElementCreateSystemWide failed: {e}")
        test_results['axui_element'] = False
    
    return test_results

def fix_pyobjc_installation():
    """Fix PyObjC installation issues."""
    logger.info("🔧 Fixing PyObjC installation...")
    
    try:
        # Uninstall existing PyObjC
        logger.info("Uninstalling existing PyObjC packages...")
        subprocess.run([
            sys.executable, '-m', 'pip', 'uninstall', '-y',
            'pyobjc', 'pyobjc-core', 'pyobjc-framework-Cocoa', 
            'pyobjc-framework-AppKit', 'pyobjc-framework-ApplicationServices'
        ], capture_output=True)
        
        # Clear pip cache
        logger.info("Clearing pip cache...")
        subprocess.run([sys.executable, '-m', 'pip', 'cache', 'purge'], capture_output=True)
        
        # Reinstall PyObjC with specific version
        logger.info("Reinstalling PyObjC...")
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'install', '--no-cache-dir',
            'pyobjc==10.3.1'  # Use a stable version
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("✅ PyObjC reinstallation successful")
            return True
        else:
            logger.error(f"❌ PyObjC reinstallation failed: {result.stderr}")
            
            # Try alternative installation
            logger.info("Trying alternative PyObjC installation...")
            result2 = subprocess.run([
                sys.executable, '-m', 'pip', 'install', '--no-cache-dir',
                'pyobjc-core', 'pyobjc-framework-Cocoa', 'pyobjc-framework-ApplicationServices'
            ], capture_output=True, text=True)
            
            if result2.returncode == 0:
                logger.info("✅ Alternative PyObjC installation successful")
                return True
            else:
                logger.error(f"❌ Alternative installation also failed: {result2.stderr}")
                return False
                
    except Exception as e:
        logger.error(f"Error fixing PyObjC installation: {e}")
        return False

def create_accessibility_test_script():
    """Create a simple test script to verify accessibility works."""
    logger.info("📝 Creating accessibility test script...")
    
    test_script = '''#!/usr/bin/env python3
"""
Simple Accessibility Test Script
"""

def test_accessibility():
    print("🧪 Testing Accessibility API...")
    
    try:
        # Test PyObjC import
        import objc
        print("✅ PyObjC import: OK")
        
        # Test AppKit import
        from AppKit import NSWorkspace, AXUIElementCreateSystemWide
        print("✅ AppKit import: OK")
        
        # Test NSWorkspace
        workspace = NSWorkspace.sharedWorkspace()
        if workspace:
            print("✅ NSWorkspace: OK")
            
            # Get frontmost app
            app = workspace.frontmostApplication()
            if app:
                print(f"✅ Frontmost app: {app.localizedName()}")
            else:
                print("⚠️  No frontmost app detected")
        else:
            print("❌ NSWorkspace: Failed")
            return False
        
        # Test AXUIElement
        system_wide = AXUIElementCreateSystemWide()
        if system_wide:
            print("✅ AXUIElementCreateSystemWide: OK")
            print("🎉 Accessibility API is working!")
            return True
        else:
            print("❌ AXUIElementCreateSystemWide: Failed (permissions needed)")
            print("📋 Please grant accessibility permissions in System Preferences")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_accessibility()
'''
    
    try:
        with open('test_accessibility_simple.py', 'w') as f:
            f.write(test_script)
        logger.info("✅ Test script created: test_accessibility_simple.py")
        return True
    except Exception as e:
        logger.error(f"Error creating test script: {e}")
        return False

def provide_detailed_instructions():
    """Provide detailed step-by-step instructions for fixing accessibility."""
    logger.info("📋 Detailed Accessibility Fix Instructions:")
    
    print("""
🔧 COMPREHENSIVE ACCESSIBILITY FIX GUIDE
==========================================

STEP 1: Reset Accessibility Permissions
----------------------------------------
1. Open Terminal and run:
   tccutil reset Accessibility com.apple.Terminal
   tccutil reset Accessibility Kiro

2. If you get "command not found", that's normal on older macOS versions.

STEP 2: Remove and Re-add Applications
--------------------------------------
1. Open System Preferences → Security & Privacy → Privacy → Accessibility
2. Click the lock icon and enter your password
3. Select Terminal and Kiro, then click the "-" button to remove them
4. Click the "+" button and re-add:
   - Terminal: /System/Applications/Utilities/Terminal.app
   - Kiro: (browse to where Kiro is installed)
5. Ensure both checkboxes are checked ✅

STEP 3: Restart Applications
----------------------------
1. Completely quit Terminal (Cmd+Q)
2. Completely quit Kiro if using it
3. Restart both applications

STEP 4: Test Accessibility
--------------------------
Run this command to test:
   python test_accessibility_simple.py

STEP 5: Alternative - Use Different Terminal
--------------------------------------------
If Terminal still doesn't work, try:
1. Install iTerm2: https://iterm2.com/
2. Add iTerm2 to accessibility permissions
3. Run AURA from iTerm2

STEP 6: System-Level Reset (If Still Failing)
----------------------------------------------
1. Restart your Mac
2. Reset NVRAM: Hold Cmd+Option+P+R during startup
3. Re-grant permissions after restart

STEP 7: Check for Conflicting Software
---------------------------------------
Some security software can interfere with accessibility:
- Little Snitch
- Malware scanners
- VPN software with system-level access

Temporarily disable these and test again.
""")

def main():
    """Main function to diagnose and fix accessibility issues."""
    logger.info("🔐 AURA Accessibility Permissions Diagnostic & Fix")
    logger.info("=" * 60)
    
    # Step 1: Check system status
    check_system_integrity_protection()
    print()
    
    # Step 2: Check TCC database
    check_tcc_database()
    print()
    
    # Step 3: Test PyObjC accessibility
    test_results = test_pyobjc_accessibility()
    print()
    
    # Step 4: Analyze results and provide fixes
    if not test_results.get('pyobjc_core', False):
        logger.error("❌ PyObjC core is not working. Attempting to fix...")
        if fix_pyobjc_installation():
            logger.info("✅ PyObjC fixed. Please restart and try again.")
        else:
            logger.error("❌ Could not fix PyObjC. Manual intervention required.")
        return
    
    if not test_results.get('nsworkspace', False):
        logger.error("❌ NSWorkspace import is failing. This indicates a PyObjC framework issue.")
        logger.info("🔧 Attempting to fix PyObjC framework...")
        if fix_pyobjc_installation():
            logger.info("✅ Framework fixed. Please restart and try again.")
        else:
            logger.error("❌ Could not fix framework. Manual intervention required.")
        return
    
    if not test_results.get('axui_element', False):
        logger.warning("⚠️  AXUIElement creation failed. This is a permissions issue.")
        logger.info("🔄 Attempting to reset permissions...")
        reset_accessibility_permissions()
        print()
    
    # Step 5: Create test script
    create_accessibility_test_script()
    print()
    
    # Step 6: Provide detailed instructions
    provide_detailed_instructions()
    
    # Step 7: Final recommendations
    logger.info("🎯 NEXT STEPS:")
    logger.info("1. Follow the detailed instructions above")
    logger.info("2. Run: python test_accessibility_simple.py")
    logger.info("3. If still failing, try running AURA from a different terminal (iTerm2)")
    logger.info("4. As a last resort, restart your Mac and re-grant permissions")

if __name__ == "__main__":
    main()