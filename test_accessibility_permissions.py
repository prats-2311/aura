#!/usr/bin/env python3
"""
Test accessibility permissions and provide guidance for enabling them
"""

import subprocess
import sys
import os

def check_accessibility_permissions():
    """Check if accessibility permissions are granted"""
    try:
        # Try to use AppleScript to check accessibility permissions
        script = '''
        tell application "System Events"
            try
                set frontApp to name of first application process whose frontmost is true
                return "accessible"
            on error
                return "not_accessible"
            end try
        end tell
        '''
        
        result = subprocess.run(['osascript', '-e', script], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            if "accessible" in result.stdout:
                return True, "Accessibility permissions are granted"
            else:
                return False, "Accessibility permissions are not granted"
        else:
            return False, f"Permission check failed: {result.stderr}"
            
    except Exception as e:
        return False, f"Error checking permissions: {e}"

def get_terminal_app_name():
    """Get the name of the current terminal application"""
    try:
        # Get the parent process (terminal app)
        ppid = os.getppid()
        result = subprocess.run(['ps', '-p', str(ppid), '-o', 'comm='], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
    except:
        pass
    return "Terminal"

def main():
    print("🔍 Checking Accessibility Permissions...")
    
    has_permissions, message = check_accessibility_permissions()
    print(f"Status: {message}")
    
    if not has_permissions:
        terminal_name = get_terminal_app_name()
        print(f"\n❌ Accessibility permissions are required for AURA to work properly.")
        print(f"\n📋 To grant permissions:")
        print(f"1. Open System Preferences/Settings")
        print(f"2. Go to Security & Privacy → Privacy → Accessibility")
        print(f"3. Click the lock icon and enter your password")
        print(f"4. Add and enable: {terminal_name}")
        print(f"5. If using an IDE, also add your IDE (e.g., VS Code, PyCharm)")
        print(f"6. Restart your terminal/IDE after granting permissions")
        
        print(f"\n🔧 Alternative: Run this command to open System Preferences:")
        print(f"   open 'x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility'")
        
        return False
    else:
        print(f"\n✅ Accessibility permissions are properly configured!")
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)