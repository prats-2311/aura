#!/usr/bin/env python3
"""
Final accessibility permissions fix for AURA.
"""

import sys
import os
import subprocess
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_accessibility_permissions():
    """Check if accessibility permissions are granted."""
    
    try:
        # Try to import and test accessibility
        from modules.accessibility import AccessibilityModule
        
        print("Testing accessibility permissions...")
        
        accessibility = AccessibilityModule()
        
        # Test if we can get the focused application
        try:
            current_app = accessibility.get_active_application()
            if current_app and current_app.get('accessible', False):
                print("✅ Accessibility permissions are working!")
                print(f"   Current app: {current_app['name']}")
                return True
            else:
                print("❌ Accessibility permissions are limited")
                if current_app:
                    print(f"   Current app: {current_app['name']} (not accessible)")
                else:
                    print("   Cannot detect current app")
                return False
                
        except Exception as e:
            print(f"❌ Accessibility test failed: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Cannot test accessibility: {e}")
        return False

def get_current_terminal_app():
    """Get the current terminal application name."""
    try:
        # Get the parent process (terminal)
        result = subprocess.run(['ps', '-p', str(os.getppid()), '-o', 'comm='], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            terminal_name = result.stdout.strip()
            # Map common terminal executables to app names
            terminal_map = {
                'Terminal': 'Terminal',
                'iTerm2': 'iTerm2', 
                'iTerm': 'iTerm2',
                'zsh': 'Terminal',  # Default terminal
                'bash': 'Terminal'  # Default terminal
            }
            return terminal_map.get(terminal_name, 'Terminal')
    except:
        pass
    return 'Terminal'

def show_accessibility_instructions():
    """Show instructions for granting accessibility permissions."""
    
    terminal_app = get_current_terminal_app()
    
    print("\n" + "="*70)
    print("ACCESSIBILITY PERMISSIONS REQUIRED")
    print("="*70)
    print()
    print("AURA needs accessibility permissions to use the fast path for GUI automation.")
    print("Without these permissions, AURA will fall back to slower vision-based detection.")
    print()
    print("TO GRANT PERMISSIONS:")
    print("1. Open System Preferences/Settings")
    print("2. Go to Security & Privacy → Privacy → Accessibility")
    print("3. Click the lock icon and enter your password")
    print(f"4. Add and enable: {terminal_app}")
    print("5. Add and enable: Python (if listed)")
    print("6. Restart this terminal session")
    print()
    print("ALTERNATIVE METHOD:")
    print("1. Open System Preferences/Settings")
    print("2. Go to Privacy & Security → Accessibility")
    print(f"3. Toggle ON: {terminal_app}")
    print("4. Toggle ON: Python (if listed)")
    print("5. Restart this terminal session")
    print()
    print("After granting permissions, the fast path should work and you'll see:")
    print("  ✅ Enhanced role detection available: True")
    print("  ✅ Fast path execution successful")
    print("  ✅ Commands execute in <2 seconds instead of 17+ seconds")
    print()
    print("="*70)

def test_fast_path_after_permissions():
    """Test if fast path works after permissions are granted."""
    
    print("\nTesting fast path functionality...")
    
    try:
        from modules.accessibility import AccessibilityModule
        
        accessibility = AccessibilityModule()
        
        # Test enhanced role detection
        enhanced_available = accessibility.is_enhanced_role_detection_available()
        print(f"Enhanced role detection available: {enhanced_available}")
        
        if not enhanced_available:
            print("❌ Enhanced role detection still not available")
            return False
        
        # Test role detection
        button_clickable = accessibility.is_clickable_element_role('AXButton')
        link_clickable = accessibility.is_clickable_element_role('AXLink')
        
        print(f"AXButton clickable: {button_clickable}")
        print(f"AXLink clickable: {link_clickable}")
        
        if not (button_clickable and link_clickable):
            print("❌ Role detection not working properly")
            return False
        
        # Test application access
        try:
            current_app = accessibility.get_active_application()
            if current_app and current_app.get('accessible', False):
                print(f"✅ Can access current application: {current_app['name']}")
                return True
            else:
                print("❌ Still cannot access applications - permissions may not be fully granted")
                return False
                
        except Exception as e:
            print(f"❌ Application access test failed: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Fast path test failed: {e}")
        return False

def main():
    """Main function to check and fix accessibility permissions."""
    
    print("AURA Accessibility Permissions Checker")
    print("="*50)
    
    # Check current permissions
    permissions_ok = check_accessibility_permissions()
    
    if permissions_ok:
        print("\n✅ Accessibility permissions are working correctly!")
        print("The fast path should work for GUI automation commands.")
        
        # Test fast path functionality
        if test_fast_path_after_permissions():
            print("\n🎉 Fast path is fully functional!")
            print("Commands like 'click on the gmail link' should now work quickly.")
        else:
            print("\n⚠️  Permissions are granted but fast path has issues.")
            
    else:
        print("\n❌ Accessibility permissions need to be granted.")
        show_accessibility_instructions()
        
        print("\nAfter granting permissions, run this script again to verify.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())