#!/usr/bin/env python3
"""
Debug application detection at the AppKit level
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

def debug_appkit_detection():
    """Debug AppKit application detection directly"""
    
    if not APPKIT_AVAILABLE:
        print("❌ AppKit not available")
        return
    
    print("🔍 Direct AppKit Application Detection Debug")
    print("=" * 60)
    
    print("Instructions:")
    print("1. Make sure Chrome is active")
    print("2. Test will start in 5 seconds...")
    
    # Countdown timer
    for i in range(5, 0, -1):
        print(f"Starting in {i}...")
        time.sleep(1)
    
    print("\n📊 Testing Chrome Detection (Direct AppKit):")
    workspace = NSWorkspace.sharedWorkspace()
    active_app = workspace.frontmostApplication()
    
    if active_app:
        print(f"✅ AppKit frontmostApplication(): {active_app.localizedName()}")
        print(f"   Bundle ID: {active_app.bundleIdentifier()}")
        print(f"   Process ID: {active_app.processIdentifier()}")
        print(f"   Is Active: {active_app.isActive()}")
        print(f"   Is Hidden: {active_app.isHidden()}")
    else:
        print("❌ No frontmost application found")
    
    print("\n" + "=" * 60)
    print("Now switch to Preview with a PDF")
    print("Make sure Preview is CLICKED and FOCUSED")
    print("You have 10 seconds to switch...")
    
    # Countdown for switching
    for i in range(10, 0, -1):
        print(f"Testing Preview in {i}...")
        time.sleep(1)
    
    print("\n📊 Testing Preview Detection (Direct AppKit):")
    workspace = NSWorkspace.sharedWorkspace()
    active_app = workspace.frontmostApplication()
    
    if active_app:
        print(f"✅ AppKit frontmostApplication(): {active_app.localizedName()}")
        print(f"   Bundle ID: {active_app.bundleIdentifier()}")
        print(f"   Process ID: {active_app.processIdentifier()}")
        print(f"   Is Active: {active_app.isActive()}")
        print(f"   Is Hidden: {active_app.isHidden()}")
    else:
        print("❌ No frontmost application found")
    
    print("\n" + "=" * 60)
    print("Continuous monitoring - switch between apps:")
    
    for i in range(10):
        print(f"\nMonitoring #{i+1}:")
        workspace = NSWorkspace.sharedWorkspace()
        active_app = workspace.frontmostApplication()
        
        if active_app:
            print(f"  Current: {active_app.localizedName()} (PID: {active_app.processIdentifier()})")
        else:
            print("  No application detected")
        
        time.sleep(3)

def debug_running_applications():
    """Debug all running applications"""
    
    if not APPKIT_AVAILABLE:
        print("❌ AppKit not available")
        return
    
    print("\n🔍 All Running Applications:")
    print("=" * 60)
    
    workspace = NSWorkspace.sharedWorkspace()
    running_apps = workspace.runningApplications()
    
    print(f"Found {len(running_apps)} running applications:")
    
    for app in running_apps:
        if app.localizedName() and not app.isHidden():
            active_status = "🟢 ACTIVE" if app.isActive() else "⚪ inactive"
            print(f"  {active_status} {app.localizedName()} ({app.bundleIdentifier()})")

if __name__ == "__main__":
    debug_appkit_detection()
    debug_running_applications()