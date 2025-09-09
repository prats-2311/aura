#!/usr/bin/env python3
"""
Direct test of cliclick Return key functionality.
This will help determine if the issue is with cliclick itself or the application.
"""

import subprocess
import time

def test_cliclick_return_direct():
    """Test cliclick Return key directly to see if it creates newlines."""
    
    print("🧪 Direct cliclick Return Key Test")
    print("=" * 40)
    print("This will test if cliclick Return keys work at all.")
    print("Open TextEdit (or any simple text editor) and focus on it.")
    print("Press Enter when ready...")
    input()
    
    print("Testing sequence:")
    print("1. Type 'Line 1'")
    print("2. Press Return")
    print("3. Type 'Line 2'")
    print("4. Press Return")
    print("5. Type 'Line 3'")
    print()
    
    # Test sequence with detailed logging
    commands = [
        (['cliclick', 't:Line 1'], "Type 'Line 1'"),
        (['cliclick', 'kp:return'], "Press Return"),
        (['cliclick', 't:Line 2'], "Type 'Line 2'"),
        (['cliclick', 'kp:return'], "Press Return"),
        (['cliclick', 't:Line 3'], "Type 'Line 3'"),
    ]
    
    for i, (cmd, description) in enumerate(commands):
        print(f"Step {i+1}: {description}")
        print(f"Command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                print(f"   ✅ SUCCESS - Command executed")
            else:
                print(f"   ❌ FAILED - {result.stderr}")
                
        except Exception as e:
            print(f"   ❌ EXCEPTION - {e}")
        
        # Wait between commands (like AURA does)
        time.sleep(0.3)
        print()
    
    print("Test completed!")
    print("Check your text editor:")
    print("- Do you see 3 separate lines?")
    print("- Or is everything on one line?")
    
    response = input("Did you see 3 separate lines? (y/n): ").lower().strip()
    return response.startswith('y')

def test_different_return_methods():
    """Test different ways to create newlines with cliclick."""
    
    print("\n🔧 Testing Different Return Methods")
    print("=" * 40)
    print("Focus on your text editor and press Enter...")
    input()
    
    methods = [
        (['cliclick', 'kp:return'], "Standard Return (kp:return)"),
        (['cliclick', 'kp:enter'], "Enter key (kp:enter)"),
        (['cliclick', 'key', 'return'], "Key command (key return)"),
        (['cliclick', 't:\n'], "Literal newline (t:\\n)"),
    ]
    
    print("Testing different Return key methods...")
    
    for i, (cmd, description) in enumerate(methods):
        print(f"\nMethod {i+1}: {description}")
        
        # Type identifier
        type_cmd = ['cliclick', f't:Method{i+1}']
        print(f"Typing: {' '.join(type_cmd)}")
        
        try:
            subprocess.run(type_cmd, capture_output=True, text=True, timeout=5)
            time.sleep(0.2)
            
            # Try the Return method
            print(f"Return: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                print(f"   ✅ Command succeeded")
            else:
                print(f"   ❌ Command failed: {result.stderr}")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        
        time.sleep(0.5)
    
    print("\nCheck your editor - which methods created actual newlines?")

def test_application_focus():
    """Test if the issue is related to application focus."""
    
    print("\n🎯 Testing Application Focus")
    print("=" * 30)
    print("This will test if Return keys are being sent to the right application.")
    print("Focus on your text editor and press Enter...")
    input()
    
    # Get the current application name
    try:
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
            app_name = result.stdout.strip()
            print(f"Active application: {app_name}")
        else:
            app_name = "Unknown"
            print("Could not detect active application")
            
    except Exception as e:
        app_name = "Unknown"
        print(f"Error detecting application: {e}")
    
    # Test typing in this specific application
    print(f"\nTesting cliclick in {app_name}...")
    
    test_sequence = [
        "Focus test line 1",
        "Focus test line 2", 
        "Focus test line 3"
    ]
    
    for i, line in enumerate(test_sequence):
        print(f"Typing: {line}")
        subprocess.run(['cliclick', f't:{line}'], capture_output=True, timeout=5)
        
        if i < len(test_sequence) - 1:
            print("Pressing Return...")
            result = subprocess.run(['cliclick', 'kp:return'], capture_output=True, timeout=5)
            print(f"Return result: {'SUCCESS' if result.returncode == 0 else 'FAILED'}")
        
        time.sleep(0.3)
    
    print(f"\nDid the Return keys work in {app_name}?")

def main():
    """Run all direct cliclick tests."""
    
    print("🔍 Direct cliclick Return Key Diagnostic")
    print("This will determine if the issue is with cliclick or the application")
    print("=" * 70)
    
    # Test 1: Basic Return key functionality
    basic_works = test_cliclick_return_direct()
    
    # Test 2: Different Return methods
    test_different_return_methods()
    
    # Test 3: Application focus
    test_application_focus()
    
    print("\n" + "=" * 70)
    print("🎯 DIAGNOSTIC RESULTS")
    print("=" * 70)
    
    if basic_works:
        print("✅ cliclick Return keys work correctly!")
        print("✅ The issue is NOT with cliclick itself")
        print("✅ The problem must be application-specific or timing-related")
        
        print("\n🔧 Possible Solutions:")
        print("1. Try a different text editor (TextEdit, Sublime, VS Code)")
        print("2. Check if the application has auto-formatting enabled")
        print("3. Test with even longer delays between operations")
        print("4. Use clipboard paste method instead of typing")
        
    else:
        print("❌ cliclick Return keys are NOT working!")
        print("❌ This is a system-level issue with cliclick")
        
        print("\n🔧 Possible Causes:")
        print("1. cliclick version or installation issue")
        print("2. macOS security settings blocking Return keys")
        print("3. System-level keyboard interception")
        print("4. Accessibility permissions issue")
    
    return basic_works

if __name__ == "__main__":
    main()