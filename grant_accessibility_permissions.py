#!/usr/bin/env python3
"""
Accessibility Permissions Helper

This script helps you grant accessibility permissions to enable AURA's fast path.
"""

import subprocess
import sys
import time

def check_accessibility_permissions():
    """Check if accessibility permissions are granted."""
    try:
        from modules.accessibility import AccessibilityModule
        module = AccessibilityModule()
        status = module.get_accessibility_status()
        return status.get('permissions_granted', False)
    except:
        return False

def get_current_terminal():
    """Get the current terminal application."""
    try:
        # Try to get the parent process name
        result = subprocess.run(['ps', '-p', str(os.getppid()), '-o', 'comm='], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
    except:
        pass
    
    # Default fallback
    return "Terminal"

def main():
    print("🔐 AURA Accessibility Permissions Helper")
    print("=" * 50)
    print()
    
    # Check current status
    print("📋 Checking current accessibility status...")
    has_permissions = check_accessibility_permissions()
    
    if has_permissions:
        print("✅ Accessibility permissions are already granted!")
        print("🚀 AURA's fast path should be working.")
        return
    
    print("❌ Accessibility permissions are NOT granted.")
    print()
    
    # Provide instructions
    print("📝 To enable AURA's fast path (< 2 second GUI commands), follow these steps:")
    print()
    print("1️⃣  Open System Preferences")
    print("   • Click the Apple menu → System Preferences")
    print("   • Or press Cmd+Space and type 'System Preferences'")
    print()
    
    print("2️⃣  Navigate to Privacy Settings")
    print("   • Click 'Security & Privacy'")
    print("   • Click the 'Privacy' tab")
    print("   • Select 'Accessibility' from the left sidebar")
    print()
    
    print("3️⃣  Grant Permissions")
    print("   • Click the lock icon (🔒) and enter your password")
    print("   • Click the '+' button to add an application")
    print("   • Navigate to Applications → Utilities → Terminal")
    print("   • Select Terminal and click 'Open'")
    print("   • Ensure the checkbox next to Terminal is CHECKED ✅")
    print()
    
    print("4️⃣  Alternative: Add your IDE")
    print("   • If you're using an IDE (like Kiro, VS Code, PyCharm):")
    print("   • Add your IDE instead of Terminal")
    print("   • This will give AURA permissions when run from the IDE")
    print()
    
    print("5️⃣  Restart and Test")
    print("   • Close this terminal/IDE and reopen it")
    print("   • Run this script again to verify permissions")
    print()
    
    # Wait for user to grant permissions
    print("⏳ Waiting for you to grant permissions...")
    print("   Press Enter after you've completed the steps above, or Ctrl+C to exit")
    
    try:
        input()
    except KeyboardInterrupt:
        print("\n👋 Exiting. Run this script again after granting permissions.")
        return
    
    # Check again
    print("\n🔄 Checking permissions again...")
    time.sleep(1)
    
    has_permissions = check_accessibility_permissions()
    
    if has_permissions:
        print("🎉 SUCCESS! Accessibility permissions are now granted!")
        print()
        print("✅ AURA's fast path is now enabled")
        print("✅ GUI commands will execute in < 2 seconds")
        print("✅ Performance improvement: 7-20x faster")
        print()
        print("🚀 You can now test AURA with:")
        print("   python test_aura_commands.py interactive")
        print("   python main.py")
        
    else:
        print("❌ Permissions still not detected.")
        print()
        print("🔧 Troubleshooting:")
        print("• Make sure you added the correct application (Terminal or your IDE)")
        print("• Ensure the checkbox is checked ✅")
        print("• Try restarting Terminal/IDE completely")
        print("• On some systems, you may need to restart your computer")
        print()
        print("💡 You can still use AURA without these permissions.")
        print("   It will use vision-based fallback (slower but still functional)")

if __name__ == "__main__":
    import os
    main()