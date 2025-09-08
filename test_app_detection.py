#!/usr/bin/env python3
"""
Real application detection test to debug the issue
"""

import sys
import os
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.application_detector import ApplicationDetector

def test_application_detection():
    """Test real-time application detection with automatic timing"""
    
    print("🔍 Testing Application Detection")
    print("=" * 50)
    
    detector = ApplicationDetector()
    
    print("Instructions:")
    print("1. Make sure Chrome is the active window")
    print("2. Test will start in 5 seconds...")
    
    # Countdown timer
    for i in range(5, 0, -1):
        print(f"Starting in {i}...")
        time.sleep(1)
    
    # Test Chrome detection
    print("\n📊 Testing Chrome Detection:")
    app_info = detector.get_active_application_info()
    if app_info:
        print(f"✅ Detected: {app_info.name}")
        print(f"   Type: {app_info.app_type.value}")
        if hasattr(app_info, 'bundle_id'):
            print(f"   Bundle ID: {app_info.bundle_id}")
        if hasattr(app_info, 'pid'):
            print(f"   Process ID: {app_info.pid}")
        if hasattr(app_info, 'browser_type') and app_info.browser_type:
            print(f"   Browser Type: {app_info.browser_type.value}")
    else:
        print("❌ No application detected")
    
    print("\n" + "=" * 50)
    print("Now switch to Preview with a PDF open")
    print("Make sure Preview is the ACTIVE/FOCUSED window")
    print("You have 10 seconds to switch...")
    
    # Countdown for switching
    for i in range(10, 0, -1):
        print(f"Testing Preview in {i}...")
        time.sleep(1)
    
    # Test Preview detection
    print("\n📊 Testing Preview Detection:")
    app_info = detector.get_active_application_info()
    if app_info:
        print(f"✅ Detected: {app_info.name}")
        print(f"   Type: {app_info.app_type.value}")
        if hasattr(app_info, 'bundle_id'):
            print(f"   Bundle ID: {app_info.bundle_id}")
        if hasattr(app_info, 'pid'):
            print(f"   Process ID: {app_info.pid}")
    else:
        print("❌ No application detected")
    
    print("\n" + "=" * 50)
    print("Testing multiple rapid detections (simulating AURA behavior):")
    
    for i in range(5):
        print(f"\nDetection #{i+1}:")
        app_info = detector.get_active_application_info()
        if app_info:
            print(f"  Detected: {app_info.name} ({app_info.app_type.value})")
        else:
            print("  No application detected")
        time.sleep(2)
    
    print("\n🔍 Testing with fresh detector instance:")
    # Create a new detector instance to test for caching issues
    fresh_detector = ApplicationDetector()
    app_info = fresh_detector.get_active_application_info()
    if app_info:
        print(f"✅ Fresh detector detected: {app_info.name} ({app_info.app_type.value})")
    else:
        print("❌ Fresh detector found no application")
    
    print("\n" + "=" * 50)
    print("Final test - switch between apps during detection:")
    print("Switch between Chrome and Preview every few seconds...")
    
    for i in range(10):
        print(f"\nContinuous Detection #{i+1}:")
        app_info = detector.get_active_application_info()
        if app_info:
            print(f"  Current app: {app_info.name} ({app_info.app_type.value})")
        else:
            print("  No application detected")
        time.sleep(3)

if __name__ == "__main__":
    test_application_detection()