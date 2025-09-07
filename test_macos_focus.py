#!/usr/bin/env python3
"""
macOS Focus Detection Test

This test uses direct macOS system commands to check what
the system thinks is the active/focused application.
"""

import sys
import os
import subprocess
import time

def get_active_app_osascript():
    """Get active application using osascript (AppleScript)."""
    try:
        # Use AppleScript to get the frontmost application
        script = '''
        tell application "System Events"
            set frontApp to first process whose frontmost is true
            return name of frontApp
        end tell
        '''
        
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            print(f"osascript error: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"osascript exception: {e}")
        return None

def get_active_app_lsappinfo():
    """Get active application using lsappinfo command."""
    try:
        # Use lsappinfo to get frontmost application
        result = subprocess.run(
            ['lsappinfo', 'info', '-only', 'name', '-app', 'frontmost'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            # Parse the output to extract the app name
            output = result.stdout.strip()
            # Output format is usually: "name"="AppName"
            if '=' in output:
                app_name = output.split('=')[1].strip('"')
                return app_name
            return output
        else:
            print(f"lsappinfo error: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"lsappinfo exception: {e}")
        return None

def get_active_app_python_appkit():
    """Get active application using Python AppKit."""
    try:
        from AppKit import NSWorkspace
        
        workspace = NSWorkspace.sharedWorkspace()
        active_app = workspace.frontmostApplication()
        
        if active_app:
            return active_app.localizedName()
        else:
            return None
            
    except Exception as e:
        print(f"AppKit exception: {e}")
        return None

def test_all_methods():
    """Test all methods to detect active application."""
    
    print("🔍 macOS Focus Detection Test")
    print("=" * 50)
    print("Testing different methods to detect the active application")
    print("=" * 50)
    
    methods = [
        ("osascript (AppleScript)", get_active_app_osascript),
        ("lsappinfo command", get_active_app_lsappinfo),
        ("Python AppKit", get_active_app_python_appkit)
    ]
    
    while True:
        print(f"\nCurrent time: {time.strftime('%H:%M:%S')}")
        print("Testing all detection methods...")
        
        results = {}
        for method_name, method_func in methods:
            try:
                result = method_func()
                results[method_name] = result
                print(f"  {method_name}: {result}")
            except Exception as e:
                results[method_name] = f"ERROR: {e}"
                print(f"  {method_name}: ERROR - {e}")
        
        # Check if all methods agree
        unique_results = set(r for r in results.values() if r and not r.startswith("ERROR"))
        
        if len(unique_results) == 1:
            print(f"✅ All methods agree: {list(unique_results)[0]}")
        elif len(unique_results) > 1:
            print(f"⚠️ Methods disagree: {unique_results}")
        else:
            print("❌ No methods returned valid results")
        
        print("\n" + "-" * 50)
        print("Switch to a different application now...")
        
        choice = input("Press Enter to test again, or 'q' to quit: ").strip().lower()
        if choice == 'q':
            break

def test_with_timer():
    """Test with a timer to allow application switching."""
    
    print("⏰ Timed Application Detection Test")
    print("=" * 50)
    
    while True:
        print("\nYou have 10 seconds to switch to a different application...")
        
        # Show countdown
        for i in range(10, 0, -1):
            print(f"   {i} seconds remaining...", end='\r')
            time.sleep(1)
        print("   Testing now...                    ")
        
        # Test all methods
        print("\n📱 Detection results:")
        
        osascript_result = get_active_app_osascript()
        lsappinfo_result = get_active_app_lsappinfo()
        appkit_result = get_active_app_python_appkit()
        
        print(f"  osascript: {osascript_result}")
        print(f"  lsappinfo: {lsappinfo_result}")
        print(f"  AppKit: {appkit_result}")
        
        # Compare with our detector
        try:
            from modules.application_detector import ApplicationDetector
            detector = ApplicationDetector()
            app_info = detector.get_active_application_info()
            
            if app_info:
                print(f"  Our detector: {app_info.name}")
            else:
                print(f"  Our detector: None")
        except Exception as e:
            print(f"  Our detector: ERROR - {e}")
        
        choice = input("\nPress Enter to test again, or 'q' to quit: ").strip().lower()
        if choice == 'q':
            break

def main():
    """Main test function."""
    
    print("🧪 macOS Application Focus Detection Test")
    print("=" * 50)
    print("This test uses different methods to detect the active application")
    print("to help debug why application switching isn't being detected.")
    print("=" * 50)
    
    print("\nChoose test mode:")
    print("1. Manual testing (test whenever you want)")
    print("2. Timed testing (10-second countdown)")
    
    while True:
        choice = input("\nEnter choice (1-2): ").strip()
        
        if choice == '1':
            test_all_methods()
            break
        elif choice == '2':
            test_with_timer()
            break
        else:
            print("❌ Invalid choice. Please enter 1 or 2.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Test interrupted by user.")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()