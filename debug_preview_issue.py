#!/usr/bin/env python3
"""
Debug why Preview isn't being detected
"""

import sys
import os
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.application_detector import ApplicationDetector

try:
    from AppKit import NSWorkspace, NSRunningApplication
    APPKIT_AVAILABLE = True
except ImportError as e:
    APPKIT_AVAILABLE = False

def debug_preview_detection():
    """Debug Preview detection step by step"""
    
    print("🔍 Debug Preview Detection")
    print("=" * 60)
    
    if not APPKIT_AVAILABLE:
        print("❌ AppKit not available")
        return
    
    workspace = NSWorkspace.sharedWorkspace()
    running_apps = workspace.runningApplications()
    
    # Find all Apple apps
    apple_apps = []
    for app in running_apps:
        if (app.localizedName() and 
            app.bundleIdentifier() and 
            app.bundleIdentifier().startswith('com.apple.')):
            apple_apps.append(app)
    
    print(f"📋 Found {len(apple_apps)} Apple applications:")
    for app in apple_apps:
        is_hidden = app.isHidden()
        is_active = app.isActive()
        activation_policy = app.activationPolicy()
        
        status = []
        if is_active:
            status.append("🟢 ACTIVE")
        if is_hidden:
            status.append("👻 HIDDEN")
        if activation_policy != 0:
            status.append(f"📋 Policy:{activation_policy}")
        if not status:
            status.append("⚪ inactive")
        
        status_str = " ".join(status)
        
        print(f"  {status_str} {app.localizedName()}")
        print(f"    Bundle: {app.bundleIdentifier()}")
        print(f"    PID: {app.processIdentifier()}")
        
        # Check if it would be filtered by _is_system_app
        detector = ApplicationDetector()
        is_system = detector._is_system_app(app)
        print(f"    System app: {is_system}")
        print()
    
    print("=" * 60)
    print("🔍 Testing ApplicationDetector logic step by step:")
    
    detector = ApplicationDetector()
    
    # Get frontmost app
    frontmost = workspace.frontmostApplication()
    print(f"📍 Frontmost app: {frontmost.localizedName() if frontmost else 'None'}")
    
    # Check if frontmost should be ignored
    ignored_bundle_ids = {
        'dev.kiro.desktop',  # Kiro IDE
        'com.apple.Terminal',  # Terminal
        'com.microsoft.VSCode',  # VS Code
        'com.apple.dt.Xcode',  # Xcode
        'com.jetbrains.intellij',  # IntelliJ
        'com.sublimetext.4',  # Sublime Text
        'com.github.atom',  # Atom
        'com.apple.Console',  # Console
        'com.apple.ActivityMonitor',  # Activity Monitor
        'com.apple.systempreferences',  # System Preferences
    }
    
    should_ignore_frontmost = frontmost and frontmost.bundleIdentifier() in ignored_bundle_ids
    print(f"📍 Should ignore frontmost: {should_ignore_frontmost}")
    
    if should_ignore_frontmost:
        print("🔍 Looking for user applications...")
        
        user_apps = []
        for app in running_apps:
            if (app.localizedName() and 
                not app.isHidden() and 
                app.bundleIdentifier() not in ignored_bundle_ids and
                not detector._is_system_app(app) and
                app.activationPolicy() == 0):
                user_apps.append(app)
        
        print(f"📋 Found {len(user_apps)} user applications:")
        for app in user_apps:
            print(f"  {app.localizedName()} (PID: {app.processIdentifier()})")
        
        # Sort by PID (more recent first)
        user_apps.sort(key=lambda app: -app.processIdentifier())
        
        if user_apps:
            selected_app = user_apps[0]
            print(f"🎯 Selected: {selected_app.localizedName()}")
        else:
            print("❌ No user applications found")

if __name__ == "__main__":
    debug_preview_detection()