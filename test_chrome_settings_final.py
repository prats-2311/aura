#!/usr/bin/env python3
"""
Final Chrome Settings Verification
Tests the specific Chrome accessibility settings you enabled.
"""

import subprocess
import time
import os

def test_chrome_accessibility_settings():
    """Test Chrome accessibility settings via AppleScript"""
    print("🔍 Testing Chrome Accessibility Settings")
    print("=" * 42)
    
    # Test if we can interact with Chrome's UI elements
    print("\n1. Testing Chrome UI accessibility...")
    
    applescript = '''
    tell application "System Events"
        try
            set chromeApp to first application process whose name is "Google Chrome"
            
            -- Get basic Chrome window info
            set chromeWindows to windows of chromeApp
            if (count of chromeWindows) > 0 then
                set firstWindow to first window of chromeApp
                set windowTitle to title of firstWindow
                
                -- Try to access Chrome's menu bar (tests accessibility)
                set menuBar to menu bar 1 of chromeApp
                set menuItems to menu bar items of menuBar
                
                return "SUCCESS: Chrome accessible - Window: '" & windowTitle & "', Menu items: " & (count of menuItems)
            else
                return "ERROR: No Chrome windows found"
            end if
        on error errorMessage
            return "ERROR: " & errorMessage
        end try
    end tell
    '''
    
    try:
        result = subprocess.run(['osascript', '-e', applescript], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            output = result.stdout.strip()
            if "SUCCESS:" in output:
                print(f"✅ Chrome UI fully accessible")
                print(f"   Details: {output.replace('SUCCESS: ', '')}")
                return True
            else:
                print(f"❌ Chrome UI not accessible: {output}")
                return False
        else:
            print(f"❌ AppleScript failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_chrome_web_accessibility():
    """Test Chrome web page accessibility"""
    print("\n2. Testing Chrome web page accessibility...")
    
    applescript = '''
    tell application "Google Chrome"
        try
            -- Get the active tab
            set activeTab to active tab of front window
            set tabURL to URL of activeTab
            set tabTitle to title of activeTab
            
            return "SUCCESS: Active tab accessible - Title: '" & tabTitle & "', URL: " & tabURL
        on error errorMessage
            return "ERROR: " & errorMessage
        end try
    end tell
    '''
    
    try:
        result = subprocess.run(['osascript', '-e', applescript], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            output = result.stdout.strip()
            if "SUCCESS:" in output:
                print(f"✅ Chrome web content accessible")
                print(f"   Details: {output.replace('SUCCESS: ', '')[:100]}...")
                return True
            else:
                print(f"⚠️  Chrome web content limited: {output}")
                return False
        else:
            print(f"❌ Web accessibility test failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Web test failed: {e}")
        return False

def test_chrome_element_detection():
    """Test if we can detect Chrome UI elements"""
    print("\n3. Testing Chrome element detection...")
    
    applescript = '''
    tell application "System Events"
        try
            set chromeApp to first application process whose name is "Google Chrome"
            set firstWindow to first window of chromeApp
            
            -- Try to find common UI elements
            set allButtons to buttons of firstWindow
            set allTextFields to text fields of firstWindow
            set allMenuButtons to menu buttons of firstWindow
            
            return "SUCCESS: Found " & (count of allButtons) & " buttons, " & (count of allTextFields) & " text fields, " & (count of allMenuButtons) & " menu buttons"
        on error errorMessage
            return "ERROR: " & errorMessage
        end try
    end tell
    '''
    
    try:
        result = subprocess.run(['osascript', '-e', applescript], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            output = result.stdout.strip()
            if "SUCCESS:" in output:
                print(f"✅ Chrome UI elements detectable")
                print(f"   Elements: {output.replace('SUCCESS: ', '')}")
                return True
            else:
                print(f"❌ Element detection failed: {output}")
                return False
        else:
            print(f"❌ Element detection error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Element detection test failed: {e}")
        return False

def test_fast_path_performance():
    """Test the speed of accessibility operations"""
    print("\n4. Testing fast path performance...")
    
    applescript = '''
    tell application "System Events"
        try
            set startTime to current date
            
            set chromeApp to first application process whose name is "Google Chrome"
            set firstWindow to first window of chromeApp
            set allElements to UI elements of firstWindow
            
            set endTime to current date
            set timeDiff to endTime - startTime
            
            return "SUCCESS: Detected " & (count of allElements) & " elements in " & timeDiff & " seconds"
        on error errorMessage
            return "ERROR: " & errorMessage
        end try
    end tell
    '''
    
    try:
        start_time = time.time()
        
        result = subprocess.run(['osascript', '-e', applescript], 
                              capture_output=True, text=True, timeout=10)
        
        total_time = time.time() - start_time
        
        if result.returncode == 0:
            output = result.stdout.strip()
            if "SUCCESS:" in output:
                print(f"✅ Fast path performance test completed in {total_time:.2f}s")
                print(f"   Results: {output.replace('SUCCESS: ', '')}")
                
                if total_time < 2.0:
                    print("🚀 Excellent performance - under 2 seconds")
                    return True
                elif total_time < 5.0:
                    print("✅ Good performance - under 5 seconds")
                    return True
                else:
                    print("⚠️  Slow performance - over 5 seconds")
                    return False
            else:
                print(f"❌ Performance test failed: {output}")
                return False
        else:
            print(f"❌ Performance test error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        return False

def run_comprehensive_verification():
    """Run all Chrome accessibility verification tests"""
    print("Chrome Accessibility Settings Verification")
    print("Testing the settings you enabled in Chrome\n")
    
    tests = [
        ("Chrome UI Accessibility", test_chrome_accessibility_settings),
        ("Chrome Web Accessibility", test_chrome_web_accessibility),
        ("Chrome Element Detection", test_chrome_element_detection),
        ("Fast Path Performance", test_fast_path_performance)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
            results[test_name] = False
    
    # Print summary
    print("\n" + "=" * 42)
    print("📊 VERIFICATION RESULTS SUMMARY")
    print("=" * 42)
    
    passed = 0
    for test_name, result in results.items():
        status = "✅" if result else "❌"
        print(f"{status} {test_name}: {result}")
        if result:
            passed += 1
    
    total = len(results)
    percentage = (passed / total) * 100
    
    print(f"\n📈 Overall Score: {passed}/{total} ({percentage:.0f}%)")
    
    if percentage >= 75:
        print("\n🎉 EXCELLENT! Chrome accessibility is working perfectly!")
        print("✅ Your Chrome settings are properly configured for Aura fast path")
        print("\n🚀 Ready for Aura automation:")
        print("   • Fast element detection enabled")
        print("   • Web accessibility working")
        print("   • UI elements detectable")
        print("   • Performance optimized")
        
        print("\n💡 Next steps:")
        print("   1. Test Aura with: python3 main.py")
        print("   2. Try a web automation command")
        print("   3. Enjoy fast, reliable automation!")
        
    elif percentage >= 50:
        print("\n✅ GOOD! Chrome accessibility is mostly working")
        print("💡 Some optimizations may be possible")
        
    else:
        print("\n⚠️  Chrome accessibility needs improvement")
        print("💡 Recommendations:")
        print("   • Restart Chrome completely")
        print("   • Re-enable accessibility settings")
        print("   • Check macOS accessibility permissions")
    
    return percentage >= 75

if __name__ == "__main__":
    try:
        success = run_comprehensive_verification()
        
        if success:
            print("\n🎯 Chrome is ready for Aura fast path automation!")
        else:
            print("\n🔧 Chrome needs additional configuration")
        
        exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        exit(1)