#!/usr/bin/env python3
"""
Specific test for Preview detection
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

def test_preview_specifically():
    """Test Preview detection specifically"""
    
    print("🔍 Preview Detection Test")
    print("=" * 50)
    
    if not APPKIT_AVAILABLE:
        print("❌ AppKit not available")
        return
    
    workspace = NSWorkspace.sharedWorkspace()
    running_apps = workspace.runningApplications()
    
    # Find Preview app
    preview_app = None
    for app in running_apps:
        if app.localizedName() == "Preview":
            preview_app = app
            break
    
    if not preview_app:
        print("❌ Preview app not found in running applications")
        print("Please make sure Preview is running with a PDF open")
        return
    
    print(f"✅ Found Preview app:")
    print(f"   Name: {preview_app.localizedName()}")
    print(f"   Bundle ID: {preview_app.bundleIdentifier()}")
    print(f"   PID: {preview_app.processIdentifier()}")
    print(f"   Is Active: {preview_app.isActive()}")
    print(f"   Is Hidden: {preview_app.isHidden()}")
    print(f"   Activation Policy: {preview_app.activationPolicy()}")
    
    # Test with ApplicationDetector
    print("\n📊 Testing with ApplicationDetector:")
    detector = ApplicationDetector()
    app_info = detector.get_active_application_info()
    
    if app_info:
        print(f"✅ Detected: {app_info.name}")
        print(f"   Type: {app_info.app_type.value}")
        print(f"   Bundle ID: {app_info.bundle_id}")
        print(f"   Confidence: {app_info.detection_confidence}")
    else:
        print("❌ No application detected")
    
    print("\n" + "=" * 50)
    print("Manual activation test:")
    print("I'll try to activate Preview programmatically...")
    
    try:
        # Try to activate Preview
        success = preview_app.activateWithOptions_(0)  # NSApplicationActivateAllWindows
        print(f"Activation result: {success}")
        
        time.sleep(2)  # Wait for activation
        
        # Test detection again
        print("\n📊 Testing after activation:")
        app_info = detector.get_active_application_info()
        
        if app_info:
            print(f"✅ Detected: {app_info.name}")
            print(f"   Type: {app_info.app_type.value}")
        else:
            print("❌ No application detected")
            
    except Exception as e:
        print(f"❌ Failed to activate Preview: {e}")

def show_all_user_apps():
    """Show all user applications"""
    
    if not APPKIT_AVAILABLE:
        return
    
    print("\n🔍 All User Applications:")
    print("=" * 50)
    
    workspace = NSWorkspace.sharedWorkspace()
    running_apps = workspace.runningApplications()
    
    user_apps = []
    for app in running_apps:
        if (app.localizedName() and 
            not app.isHidden() and 
            app.bundleIdentifier() and
            not app.bundleIdentifier().startswith('com.apple.') and
            app.activationPolicy() == 0):  # Regular apps
            user_apps.append(app)
    
    # Sort by recent activity (higher PID = more recent)
    user_apps.sort(key=lambda app: -app.processIdentifier())
    
    print(f"Found {len(user_apps)} user applications:")
    for i, app in enumerate(user_apps):
        active_status = "🟢 ACTIVE" if app.isActive() else "⚪ inactive"
        print(f"  {i+1}. {active_status} {app.localizedName()}")
        print(f"      Bundle: {app.bundleIdentifier()}")
        print(f"      PID: {app.processIdentifier()}")

if __name__ == "__main__":
    test_preview_specifically()
    show_all_user_apps()