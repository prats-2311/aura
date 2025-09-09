#!/usr/bin/env python3
"""
Debug what application AURA is typing into and test its newline handling.
"""

import subprocess
import time
import sys
import os

def get_active_application():
    """Get the currently active application on macOS."""
    try:
        # Get the active application using AppleScript
        applescript = '''
        tell application "System Events"
            set activeApp to name of first application process whose frontmost is true
            return activeApp
        end tell
        '''
        
        result = subprocess.run(
            ['osascript', '-e', applescript],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return "Unknown"
            
    except Exception as e:
        print(f"Error getting active application: {e}")
        return "Unknown"

def test_application_newline_handling(app_name):
    """Test if the target application handles newlines correctly."""
    
    print(f"🧪 Testing newline handling in: {app_name}")
    print("=" * 50)
    
    print("This test will type some text with newlines.")
    print("Watch the target application to see if newlines appear correctly.")
    print("")
    print("Press Enter to start the test (make sure the target app is focused)...")
    input()
    
    # Test sequence
    test_commands = [
        "Test line 1",
        "RETURN_KEY",
        "Test line 2", 
        "RETURN_KEY",
        "Test line 3"
    ]
    
    print("Starting test sequence...")
    
    for i, command in enumerate(test_commands):
        if command == "RETURN_KEY":
            print(f"Step {i+1}: Pressing Return key")
            result = subprocess.run(
                ['cliclick', 'kp:return'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                print(f"   ❌ Return key failed: {result.stderr}")
            else:
                print(f"   ✅ Return key succeeded")
        else:
            print(f"Step {i+1}: Typing '{command}'")
            result = subprocess.run(
                ['cliclick', f't:{command}'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                print(f"   ❌ Typing failed: {result.stderr}")
            else:
                print(f"   ✅ Typing succeeded")
        
        time.sleep(0.5)  # Pause between commands
    
    print("\nTest completed!")
    print("Check the target application:")
    print("- Did you see 3 separate lines?")
    print("- Or did everything appear on one line?")
    
    response = input("\nDid the newlines work correctly? (y/n): ").lower().strip()
    return response.startswith('y')

def test_cliclick_basic_functionality():
    """Test basic cliclick functionality."""
    
    print("\n🔧 Testing Basic cliclick Functionality")
    print("=" * 50)
    
    # Test 1: Simple typing
    print("Test 1: Simple typing")
    result = subprocess.run(
        ['cliclick', 't:Hello World'],
        capture_output=True,
        text=True,
        timeout=5
    )
    
    if result.returncode == 0:
        print("   ✅ Simple typing works")
    else:
        print(f"   ❌ Simple typing failed: {result.stderr}")
        return False
    
    time.sleep(0.5)
    
    # Test 2: Return key
    print("Test 2: Return key")
    result = subprocess.run(
        ['cliclick', 'kp:return'],
        capture_output=True,
        text=True,
        timeout=5
    )
    
    if result.returncode == 0:
        print("   ✅ Return key works")
    else:
        print(f"   ❌ Return key failed: {result.stderr}")
        return False
    
    time.sleep(0.5)
    
    # Test 3: More typing
    print("Test 3: More typing after Return")
    result = subprocess.run(
        ['cliclick', 't:Second Line'],
        capture_output=True,
        text=True,
        timeout=5
    )
    
    if result.returncode == 0:
        print("   ✅ Typing after Return works")
        return True
    else:
        print(f"   ❌ Typing after Return failed: {result.stderr}")
        return False

def analyze_aura_logs():
    """Analyze AURA logs for clues about the issue."""
    
    print("\n📊 Analyzing AURA Logs")
    print("=" * 50)
    
    try:
        # Look for recent typing operations
        with open('aura.log', 'r') as f:
            lines = f.readlines()
        
        # Find recent cliclick operations
        recent_cliclick = []
        for line in reversed(lines[-200:]):  # Last 200 lines
            if 'cliclick' in line and ('EXECUTING' in line or 'Typing succeeded' in line):
                recent_cliclick.append(line.strip())
        
        if recent_cliclick:
            print("Recent cliclick operations (most recent first):")
            for i, line in enumerate(recent_cliclick[:10]):  # Show last 10
                print(f"   {i+1}: {line}")
        else:
            print("No recent cliclick operations found in logs")
            
        # Look for multiline vs single-line method usage
        multiline_usage = []
        for line in reversed(lines[-100:]):
            if 'multiline typing' in line.lower() or 'single-line typing' in line.lower():
                multiline_usage.append(line.strip())
        
        if multiline_usage:
            print(f"\nMethod usage (last few operations):")
            for line in multiline_usage[:5]:
                print(f"   {line}")
        
    except Exception as e:
        print(f"Error analyzing logs: {e}")

def main():
    """Main debugging function."""
    
    print("🔍 AURA Target Application Debug")
    print("This will help identify why newlines aren't working")
    print("=" * 60)
    
    # Step 1: Identify target application
    app_name = get_active_application()
    print(f"Currently active application: {app_name}")
    
    # Step 2: Test basic cliclick functionality
    cliclick_works = test_cliclick_basic_functionality()
    
    if not cliclick_works:
        print("\n❌ CRITICAL: Basic cliclick functionality is broken!")
        print("This explains why AURA typing isn't working.")
        return False
    
    # Step 3: Test application-specific newline handling
    print(f"\n🎯 Now we'll test if {app_name} handles newlines correctly...")
    newlines_work = test_application_newline_handling(app_name)
    
    # Step 4: Analyze logs
    analyze_aura_logs()
    
    # Step 5: Summary
    print(f"\n" + "=" * 60)
    print("🎯 DEBUG SUMMARY")
    print("=" * 60)
    print(f"Target application: {app_name}")
    print(f"cliclick basic functionality: {'✅ WORKS' if cliclick_works else '❌ BROKEN'}")
    print(f"Application newline handling: {'✅ WORKS' if newlines_work else '❌ BROKEN'}")
    
    if cliclick_works and newlines_work:
        print("\n✅ Both cliclick and the application work correctly!")
        print("The issue must be in AURA's implementation or timing.")
        print("Recommendation: Add more detailed logging to AURA's multiline typing.")
    elif cliclick_works and not newlines_work:
        print(f"\n❌ The application '{app_name}' doesn't handle newlines correctly!")
        print("This explains why AURA's multiline typing appears to work but results in single-line output.")
        print("Recommendation: Try typing into a different application (like TextEdit).")
    else:
        print("\n❌ cliclick itself is not working correctly!")
        print("This is a system-level issue that needs to be resolved first.")
    
    return cliclick_works and newlines_work

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Debug failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)