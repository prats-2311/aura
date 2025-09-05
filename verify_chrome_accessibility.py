#!/usr/bin/env python3
"""
Chrome Accessibility Verification Guide
Step-by-step verification of Chrome accessibility settings.
"""

import subprocess
import time
import os

def check_chrome_status():
    """Check if Chrome is running"""
    print("🔍 Step 1: Checking Chrome Status")
    print("-" * 35)
    
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        chrome_processes = [line for line in result.stdout.split('\n') if 'Google Chrome' in line]
        
        if chrome_processes:
            print(f"✅ Chrome is running ({len(chrome_processes)} processes)")
            
            # Check for accessibility flags
            accessibility_flags = ['--enable-accessibility', '--force-renderer-accessibility']
            flags_found = []
            
            for line in chrome_processes:
                for flag in accessibility_flags:
                    if flag in line:
                        flags_found.append(flag)
            
            if flags_found:
                print(f"✅ Accessibility flags detected: {', '.join(set(flags_found))}")
                return True, True
            else:
                print("⚠️  No accessibility flags detected")
                return True, False
        else:
            print("❌ Chrome is not running")
            return False, False
            
    except Exception as e:
        print(f"❌ Error checking Chrome: {e}")
        return False, False

def test_basic_accessibility():
    """Test basic macOS accessibility"""
    print("\n🔍 Step 2: Testing macOS Accessibility")
    print("-" * 40)
    
    applescript = '''
    tell application "System Events"
        try
            set appList to name of every application process
            return "SUCCESS: " & (count of appList)
        on error errorMessage
            return "ERROR: " & errorMessage
        end try
    end tell
    '''
    
    try:
        result = subprocess.run(['osascript', '-e', applescript], 
                              capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0 and "SUCCESS:" in result.stdout:
            app_count = result.stdout.strip().replace("SUCCESS: ", "")
            print(f"✅ macOS accessibility working - {app_count} apps accessible")
            return True
        else:
            print(f"❌ macOS accessibility issue: {result.stdout}")
            return False
            
    except Exception as e:
        print(f"❌ Accessibility test failed: {e}")
        return False

def provide_setup_instructions():
    """Provide step-by-step setup instructions"""
    print("\n📋 Chrome Accessibility Setup Instructions")
    print("=" * 45)
    
    print("\n1. 🌐 Open Chrome and navigate to:")
    print("   chrome://accessibility/")
    print("   ✓ Enable 'Web accessibility' checkbox")
    
    print("\n2. ⚙️  Navigate to:")
    print("   chrome://settings/accessibility")
    print("   ✓ Enable 'Navigate pages with a text cursor'")
    print("   ✓ Verify 'Show a quick highlight on the focused object' is enabled")
    
    print("\n3. 🔄 Restart Chrome completely:")
    print("   • Quit Chrome (Cmd+Q)")
    print("   • Reopen Chrome")
    
    print("\n4. 🧪 Test the setup:")
    print("   • Run this script again")
    print("   • Or test with Aura: python3 main.py")

def launch_chrome_with_accessibility():
    """Launch Chrome with proper accessibility flags"""
    print("\n🚀 Launch Chrome with Accessibility")
    print("-" * 38)
    
    chrome_path = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
    
    if not os.path.exists(chrome_path):
        print("❌ Chrome not found at standard location")
        return False
    
    try:
        cmd = [
            chrome_path,
            '--enable-accessibility',
            '--force-renderer-accessibility',
            '--new-window',
            'chrome://accessibility/'
        ]
        
        print("Launching Chrome with accessibility flags...")
        print("This will open chrome://accessibility/ page")
        
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        print("✅ Chrome launched!")
        print("📝 Please enable 'Web accessibility' on the page that opens")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to launch Chrome: {e}")
        return False

def test_chrome_accessibility_final():
    """Final test of Chrome accessibility"""
    print("\n🧪 Step 3: Testing Chrome Accessibility")
    print("-" * 40)
    
    # Simple test to see if Chrome is accessible
    applescript = '''
    tell application "System Events"
        try
            set chromeApps to (every application process whose name contains "Chrome")
            if (count of chromeApps) > 0 then
                set chromeApp to first item of chromeApps
                set appName to name of chromeApp
                return "SUCCESS: Found " & appName
            else
                return "ERROR: No Chrome processes found"
            end if
        on error errorMessage
            return "ERROR: " & errorMessage
        end try
    end tell
    '''
    
    try:
        result = subprocess.run(['osascript', '-e', applescript], 
                              capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0:
            output = result.stdout.strip()
            if "SUCCESS:" in output:
                print(f"✅ Chrome process accessible via System Events")
                print(f"   {output.replace('SUCCESS: ', '')}")
                return True
            else:
                print(f"⚠️  Chrome accessibility limited: {output}")
                return False
        else:
            print(f"❌ Chrome not accessible: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Chrome accessibility test failed: {e}")
        return False

def main():
    """Main verification process"""
    print("Chrome Accessibility Verification for Aura")
    print("=" * 42)
    print("This will verify that Chrome is properly configured for fast path automation\n")
    
    # Step 1: Check Chrome status
    chrome_running, accessibility_flags = check_chrome_status()
    
    # Step 2: Test basic accessibility
    macos_accessibility = test_basic_accessibility()
    
    if not macos_accessibility:
        print("\n❌ CRITICAL: macOS accessibility permissions not granted")
        print("💡 Please grant accessibility permissions to Terminal/iTerm in:")
        print("   System Preferences > Security & Privacy > Privacy > Accessibility")
        return False
    
    # Step 3: Test Chrome accessibility
    chrome_accessible = False
    if chrome_running:
        chrome_accessible = test_chrome_accessibility_final()
    
    # Provide recommendations
    print("\n" + "=" * 42)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 42)
    
    print(f"✅ macOS Accessibility: {macos_accessibility}")
    print(f"{'✅' if chrome_running else '❌'} Chrome Running: {chrome_running}")
    print(f"{'✅' if accessibility_flags else '❌'} Accessibility Flags: {accessibility_flags}")
    print(f"{'✅' if chrome_accessible else '❌'} Chrome Accessible: {chrome_accessible}")
    
    # Calculate readiness
    total_score = sum([macos_accessibility, chrome_running, accessibility_flags, chrome_accessible])
    
    if total_score >= 3:
        print(f"\n🎉 READY! Score: {total_score}/4")
        print("✅ Chrome accessibility is configured for Aura fast path")
        print("\n🚀 You can now test Aura automation:")
        print("   python3 main.py")
        return True
    elif total_score >= 2:
        print(f"\n⚠️  PARTIAL: Score: {total_score}/4")
        if not chrome_running:
            response = input("\nWould you like to launch Chrome with accessibility? (y/n): ")
            if response.lower() == 'y':
                launch_chrome_with_accessibility()
                time.sleep(3)
                print("\nPlease enable 'Web accessibility' in the opened tab, then restart Chrome")
        else:
            provide_setup_instructions()
        return False
    else:
        print(f"\n❌ NEEDS SETUP: Score: {total_score}/4")
        provide_setup_instructions()
        return False

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Verification interrupted")
        exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        exit(1)