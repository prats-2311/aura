#!/usr/bin/env python3
"""
Check all active applications to debug focus issues
"""

import sys
import os
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from AppKit import NSWorkspace, NSRunningApplication
    APPKIT_AVAILABLE = True
except ImportError as e:
    APPKIT_AVAILABLE = False
    print(f"AppKit not available: {e}")

def check_all_active_apps():
    """Check all applications and their active status"""
    
    if not APPKIT_AVAILABLE:
        print("❌ AppKit not available")
        return
    
    print("🔍 All Applications Status Check")
    print("=" * 60)
    
    workspace = NSWorkspace.sharedWorkspace()
    running_apps = workspace.runningApplications()
    
    # Get frontmost app
    frontmost = workspace.frontmostApplication()
    frontmost_name = frontmost.localizedName() if frontmost else "None"
    
    print(f"📍 Frontmost Application: {frontmost_name}")
    print(f"📍 Frontmost Bundle ID: {frontmost.bundleIdentifier() if frontmost else 'None'}")
    print()
    
    print("📋 All Running Applications:")
    print("-" * 60)
    
    active_apps = []
    for app in running_apps:
        if app.localizedName():
            is_active = app.isActive()
            is_hidden = app.isHidden()
            is_frontmost = app == frontmost
            
            status_icons = []
            if is_frontmost:
                status_icons.append("🎯 FRONTMOST")
            if is_active:
                status_icons.append("🟢 ACTIVE")
            if is_hidden:
                status_icons.append("👻 HIDDEN")
            if not status_icons:
                status_icons.append("⚪ inactive")
            
            status = " ".join(status_icons)
            
            print(f"  {status} {app.localizedName()}")
            print(f"    Bundle: {app.bundleIdentifier()}")
            print(f"    PID: {app.processIdentifier()}")
            print()
            
            if is_active:
                active_apps.append(app.localizedName())
    
    print(f"📊 Summary:")
    print(f"   Total running apps: {len(running_apps)}")
    print(f"   Active apps: {len(active_apps)}")
    print(f"   Active app names: {', '.join(active_apps)}")

def continuous_monitoring():
    """Monitor application changes continuously"""
    
    if not APPKIT_AVAILABLE:
        return
    
    print("\n" + "=" * 60)
    print("🔄 Continuous Monitoring (Switch apps now!)")
    print("=" * 60)
    
    workspace = NSWorkspace.sharedWorkspace()
    last_frontmost = None
    
    for i in range(20):  # Monitor for 20 iterations
        frontmost = workspace.frontmostApplication()
        frontmost_name = frontmost.localizedName() if frontmost else "None"
        
        if frontmost_name != last_frontmost:
            print(f"🔄 App changed to: {frontmost_name}")
            if frontmost:
                print(f"   Bundle: {frontmost.bundleIdentifier()}")
                print(f"   PID: {frontmost.processIdentifier()}")
        else:
            print(f"📍 Still: {frontmost_name}")
        
        last_frontmost = frontmost_name
        time.sleep(2)

if __name__ == "__main__":
    check_all_active_apps()
    continuous_monitoring()