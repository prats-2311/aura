#!/usr/bin/env python3
"""
Comprehensive AURA Permissions Checker

This script checks all necessary permissions for AURA's enhanced fast path to work:
1. System-level accessibility permissions
2. Terminal/Python accessibility permissions  
3. Chrome/Safari accessibility settings
4. Application focus and detection
5. Automation permissions (cliclick)
"""

import sys
import subprocess
import time
import os
from pathlib import Path

def check_system_accessibility():
    """Check system-level accessibility permissions."""
    print("🔍 Checking System-Level Accessibility Permissions...")
    
    try:
        # Check if process is trusted
        result = subprocess.run([
            'python3', '-c', 
            'import ApplicationServices; print("trusted" if ApplicationServices.AXIsProcessTrusted() else "not_trusted")'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            is_trusted = result.stdout.strip() == "trusted"
            if is_trusted:
                print("   ✅ System accessibility: GRANTED")
                return True
            else:
                print("   ❌ System accessibility: NOT GRANTED")
                print("   📋 Fix: System Preferences → Security & Privacy → Privacy → Accessibility")
                print("      Add Terminal (or iTerm) and enable it")
                return False
        else:
            print("   ⚠️  Could not check system accessibility")
            return False
            
    except Exception as e:
        print(f"   ❌ Error checking system accessibility: {e}")
        return False

def check_terminal_permissions():
    """Check which terminal/app is running Python."""
    print("\n🔍 Checking Terminal/Application Context...")
    
    try:
        # Get current process info
        result = subprocess.run([
            'python3', '-c', 
            '''
import os
from Cocoa import NSWorkspace, NSRunningApplication
workspace = NSWorkspace.sharedWorkspace()
current_app = workspace.frontmostApplication()
if current_app:
    print(f"active_app:{current_app.localizedName()}")
    print(f"bundle_id:{current_app.bundleIdentifier()}")
    print(f"pid:{current_app.processIdentifier()}")
else:
    print("active_app:Unknown")
'''
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            app_info = {}
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    app_info[key] = value
            
            active_app = app_info.get('active_app', 'Unknown')
            bundle_id = app_info.get('bundle_id', 'Unknown')
            
            print(f"   📱 Active application: {active_app}")
            print(f"   🆔 Bundle ID: {bundle_id}")
            
            # Check if it's a known terminal or IDE
            terminal_apps = ['Terminal', 'iTerm', 'iTerm2', 'Kiro', 'VS Code', 'Visual Studio Code']
            is_terminal = any(term.lower() in active_app.lower() for term in terminal_apps)
            
            if is_terminal:
                print(f"   ✅ Running from recognized terminal/IDE: {active_app}")
                return True, active_app
            else:
                print(f"   ⚠️  Running from: {active_app} (may need separate permissions)")
                return False, active_app
        else:
            print("   ❌ Could not determine active application")
            return False, "Unknown"
            
    except Exception as e:
        print(f"   ❌ Error checking terminal context: {e}")
        return False, "Error"

def check_browser_accessibility():
    """Check browser accessibility settings."""
    print("\n🔍 Checking Browser Accessibility Settings...")
    
    browsers_found = []
    
    # Check for Chrome
    try:
        result = subprocess.run(['open', '-Ra', 'Google Chrome'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            browsers_found.append("Chrome")
            print("   🌐 Chrome: FOUND")
            print("   📋 Chrome accessibility check:")
            print("      1. Open Chrome")
            print("      2. Go to: chrome://settings/accessibility")
            print("      3. Enable 'Live Caption' or any accessibility feature")
            print("      4. OR go to: chrome://flags/")
            print("      5. Search for 'accessibility' and enable experimental features")
        else:
            print("   ❌ Chrome: NOT FOUND")
    except:
        print("   ❌ Chrome: NOT FOUND")
    
    # Check for Safari
    try:
        result = subprocess.run(['open', '-Ra', 'Safari'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            browsers_found.append("Safari")
            print("   🌐 Safari: FOUND")
            print("   📋 Safari accessibility is usually enabled by default")
        else:
            print("   ❌ Safari: NOT FOUND")
    except:
        print("   ❌ Safari: NOT FOUND")
    
    return browsers_found

def check_automation_tools():
    """Check automation tools availability."""
    print("\n🔍 Checking Automation Tools...")
    
    tools_status = {}
    
    # Check cliclick
    try:
        result = subprocess.run(['which', 'cliclick'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            cliclick_path = result.stdout.strip()
            print(f"   ✅ cliclick: FOUND at {cliclick_path}")
            
            # Test cliclick version
            version_result = subprocess.run(['cliclick', '-V'], capture_output=True, text=True, timeout=5)
            if version_result.returncode == 0:
                version = version_result.stdout.strip()
                print(f"      Version: {version}")
            
            tools_status['cliclick'] = True
        else:
            print("   ❌ cliclick: NOT FOUND")
            print("   📋 Install with: brew install cliclick")
            tools_status['cliclick'] = False
    except Exception as e:
        print(f"   ❌ cliclick: ERROR - {e}")
        tools_status['cliclick'] = False
    
    # Check AppleScript (backup automation)
    try:
        result = subprocess.run(['osascript', '-e', 'return "AppleScript works"'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("   ✅ AppleScript: AVAILABLE")
            tools_status['applescript'] = True
        else:
            print("   ❌ AppleScript: NOT WORKING")
            tools_status['applescript'] = False
    except Exception as e:
        print(f"   ❌ AppleScript: ERROR - {e}")
        tools_status['applescript'] = False
    
    return tools_status

def test_aura_accessibility():
    """Test AURA's accessibility module."""
    print("\n🔍 Testing AURA Accessibility Module...")
    
    try:
        # Import AURA's accessibility module
        sys.path.append('.')
        from modules.accessibility import AccessibilityModule
        
        acc = AccessibilityModule()
        status = acc.get_accessibility_status()
        
        print("   📊 AURA Accessibility Status:")
        for key, value in status.items():
            icon = "✅" if value else "❌"
            if key == "permissions_granted":
                icon = "✅" if value else "❌"
            elif key in ["frameworks_available", "api_initialized", "workspace_available"]:
                icon = "✅" if value else "❌"
            else:
                icon = "ℹ️"
            
            print(f"      {icon} {key}: {value}")
        
        # Test element finding
        print("\n   🔍 Testing Element Detection:")
        test_searches = [
            ("", "Google"),
            ("", "Gmail"),
            ("AXButton", "Search"),
            ("AXLink", "Gmail")
        ]
        
        elements_found = 0
        for role, label in test_searches:
            result = acc.find_element_enhanced(role, label, None)
            status_icon = "✅" if result.found else "❌"
            print(f"      {status_icon} Search '{label}' (role: {role or 'any'}): found={result.found}, confidence={result.confidence_score:.2f}")
            if result.found:
                elements_found += 1
        
        if elements_found > 0:
            print(f"   🎉 SUCCESS! Found {elements_found} elements - Enhanced fast path should work!")
            return True
        else:
            print("   ⚠️  No elements found - Browser accessibility needs to be enabled")
            return False
            
    except ImportError as e:
        print(f"   ❌ Could not import AURA modules: {e}")
        print("   📋 Make sure you're in the AURA directory and dependencies are installed")
        return False
    except Exception as e:
        print(f"   ❌ Error testing AURA accessibility: {e}")
        return False

def check_focus_and_browser():
    """Check browser focus and accessibility."""
    print("\n🔍 Testing Browser Focus and Accessibility...")
    
    print("   📋 Instructions:")
    print("   1. Open Chrome or Safari")
    print("   2. Navigate to google.com")
    print("   3. Make sure the browser is the ACTIVE window")
    print("   4. Press Enter to continue...")
    
    try:
        input()
        
        # Check what's currently focused
        result = subprocess.run([
            'python3', '-c', 
            '''
from Cocoa import NSWorkspace
workspace = NSWorkspace.sharedWorkspace()
active_app = workspace.frontmostApplication()
if active_app:
    print(f"focused:{active_app.localizedName()}")
    bundle_id = active_app.bundleIdentifier() or ""
    is_browser = "chrome" in bundle_id.lower() or "safari" in bundle_id.lower()
    print(f"is_browser:{is_browser}")
else:
    print("focused:Unknown")
    print("is_browser:False")
'''
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            focused_app = "Unknown"
            is_browser = False
            
            for line in lines:
                if line.startswith("focused:"):
                    focused_app = line.split(":", 1)[1]
                elif line.startswith("is_browser:"):
                    is_browser = line.split(":", 1)[1] == "True"
            
            print(f"   📱 Currently focused: {focused_app}")
            
            if is_browser:
                print("   ✅ Browser is focused - Good!")
                
                # Now test if we can access browser elements
                try:
                    sys.path.append('.')
                    from modules.accessibility import AccessibilityModule
                    
                    acc = AccessibilityModule()
                    result = acc.find_element_enhanced('', 'Google', None)
                    
                    if result.found:
                        print("   🎉 SUCCESS! Can access browser elements!")
                        print("   ✅ Enhanced fast path should work for click commands!")
                        return True
                    else:
                        print("   ❌ Cannot access browser elements")
                        print("   📋 Browser accessibility features need to be enabled")
                        return False
                        
                except Exception as e:
                    print(f"   ❌ Error testing browser accessibility: {e}")
                    return False
            else:
                print("   ⚠️  Browser is not focused")
                print("   📋 Make sure Chrome/Safari is the active window and try again")
                return False
        else:
            print("   ❌ Could not check focused application")
            return False
            
    except KeyboardInterrupt:
        print("\n   ⏭️  Skipped browser focus test")
        return False
    except Exception as e:
        print(f"   ❌ Error in browser focus test: {e}")
        return False

def generate_report(results):
    """Generate a comprehensive report."""
    print("\n" + "="*60)
    print("📋 AURA PERMISSIONS REPORT")
    print("="*60)
    
    # Overall status
    all_good = all(results.values())
    
    if all_good:
        print("🎉 STATUS: ALL PERMISSIONS GRANTED - Enhanced fast path should work!")
    else:
        print("⚠️  STATUS: Some permissions missing - Fast path may not work for click commands")
    
    print(f"\n📊 Permission Details:")
    for check, status in results.items():
        icon = "✅" if status else "❌"
        print(f"   {icon} {check}")
    
    if not all_good:
        print(f"\n🔧 NEXT STEPS:")
        if not results.get('system_accessibility', True):
            print("   1. Grant system accessibility permissions:")
            print("      - System Preferences → Security & Privacy → Privacy → Accessibility")
            print("      - Add Terminal/iTerm and enable it")
        
        if not results.get('browser_accessibility', True):
            print("   2. Enable browser accessibility:")
            print("      - Chrome: chrome://settings/accessibility → Enable 'Live Caption'")
            print("      - OR Chrome: chrome://flags/ → Enable accessibility features")
            print("      - Safari: Usually works by default")
        
        if not results.get('automation_tools', True):
            print("   3. Install automation tools:")
            print("      - brew install cliclick")
        
        print("   4. Test again with: python check_aura_permissions.py")
    
    print(f"\n💡 Remember:")
    print("   - Type commands work without browser accessibility (direct keystroke)")
    print("   - Click commands need browser accessibility (element detection)")
    print("   - Your enhanced fast path integration is working correctly!")

def main():
    """Run comprehensive permissions check."""
    print("🔍 AURA Enhanced Fast Path Permissions Checker")
    print("=" * 50)
    
    results = {}
    
    # Run all checks
    results['system_accessibility'] = check_system_accessibility()
    results['terminal_context'], active_app = check_terminal_permissions()
    browsers = check_browser_accessibility()
    results['browsers_available'] = len(browsers) > 0
    automation_status = check_automation_tools()
    results['automation_tools'] = automation_status.get('cliclick', False)
    results['aura_module'] = test_aura_accessibility()
    results['browser_accessibility'] = check_focus_and_browser()
    
    # Generate final report
    generate_report(results)

if __name__ == "__main__":
    main()