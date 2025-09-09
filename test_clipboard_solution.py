#!/usr/bin/env python3
"""
Test the clipboard solution for multiline typing.
This bypasses Return key issues by using copy/paste.
"""

import subprocess
import time

def test_clipboard_method():
    """Test the clipboard copy/paste method for multiline content."""
    
    print("📋 Testing Clipboard Method for Multiline Content")
    print("=" * 55)
    print("This method bypasses Return key issues by using copy/paste.")
    print("Open a text editor and focus on it, then press Enter...")
    input()
    
    # Test content with multiple lines
    test_content = '''def fibonacci(n):
    """Calculate fibonacci sequence."""
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    else:
        a, b = 0, 1
        for _ in range(n):
            a, b = b, a + b
        return a

if __name__ == "__main__":
    print(fibonacci(10))'''
    
    print(f"Test content: {len(test_content)} chars, {len(test_content.split(chr(10)))} lines")
    print("Testing clipboard copy/paste method...")
    
    try:
        # Step 1: Copy to clipboard using pbcopy
        print("Step 1: Copying to clipboard...")
        process = subprocess.Popen(
            ['pbcopy'],
            stdin=subprocess.PIPE,
            text=True
        )
        
        process.communicate(input=test_content)
        
        if process.returncode != 0:
            print("   ❌ Failed to copy to clipboard")
            return False
        
        print("   ✅ Successfully copied to clipboard")
        
        # Step 2: Small delay
        time.sleep(0.2)
        
        # Step 3: Paste using Cmd+V with cliclick
        print("Step 2: Pasting with Cmd+V...")
        
        paste_commands = [
            (['cliclick', 'kd:cmd'], "Press Cmd down"),
            (['cliclick', 'kp:v'], "Press V key"),
            (['cliclick', 'ku:cmd'], "Release Cmd")
        ]
        
        for cmd, description in paste_commands:
            print(f"   {description}: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                print(f"   ❌ Failed: {result.stderr}")
                return False
            
            print(f"   ✅ Success")
            time.sleep(0.05)  # Brief delay between commands
        
        print("\nClipboard method completed!")
        print("Check your text editor:")
        print("- Do you see properly formatted code with multiple lines?")
        print("- Is the indentation preserved?")
        print("- Are there any syntax errors?")
        
        response = input("Did the clipboard method work correctly? (y/n): ").lower().strip()
        return response.startswith('y')
        
    except Exception as e:
        print(f"❌ Clipboard method failed with exception: {e}")
        return False

def compare_methods():
    """Compare Return key method vs clipboard method."""
    
    print("\n⚖️  Comparing Return Key vs Clipboard Methods")
    print("=" * 50)
    print("This will demonstrate the difference between the two approaches.")
    print("Focus on your text editor and press Enter...")
    input()
    
    # Test 1: Return key method (problematic)
    print("Test 1: Return Key Method (current AURA approach)")
    
    lines = ["Line 1 (Return key)", "Line 2 (Return key)", "Line 3 (Return key)"]
    
    for i, line in enumerate(lines):
        print(f"   Typing: {line}")
        subprocess.run(['cliclick', f't:{line}'], capture_output=True, timeout=5)
        
        if i < len(lines) - 1:
            print(f"   Pressing Return...")
            result = subprocess.run(['cliclick', 'kp:return'], capture_output=True, timeout=5)
            print(f"   Return result: {'SUCCESS' if result.returncode == 0 else 'FAILED'}")
        
        time.sleep(0.3)
    
    # Add separator
    time.sleep(1)
    subprocess.run(['cliclick', 'kp:return'], capture_output=True, timeout=5)
    subprocess.run(['cliclick', 't:--- SEPARATOR ---'], capture_output=True, timeout=5)
    subprocess.run(['cliclick', 'kp:return'], capture_output=True, timeout=5)
    time.sleep(1)
    
    # Test 2: Clipboard method
    print("\nTest 2: Clipboard Method (proposed solution)")
    
    clipboard_content = '''Line 1 (Clipboard)
Line 2 (Clipboard)
Line 3 (Clipboard)'''
    
    print("   Copying to clipboard...")
    process = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE, text=True)
    process.communicate(input=clipboard_content)
    
    print("   Pasting with Cmd+V...")
    subprocess.run(['cliclick', 'kd:cmd'], capture_output=True, timeout=5)
    subprocess.run(['cliclick', 'kp:v'], capture_output=True, timeout=5)
    subprocess.run(['cliclick', 'ku:cmd'], capture_output=True, timeout=5)
    
    print("\nComparison completed!")
    print("Check your text editor:")
    print("- Did the Return key method create separate lines?")
    print("- Did the clipboard method work better?")
    
    return_worked = input("Did Return key method work? (y/n): ").lower().startswith('y')
    clipboard_worked = input("Did clipboard method work? (y/n): ").lower().startswith('y')
    
    return return_worked, clipboard_worked

def main():
    """Test clipboard solution for AURA multiline typing issues."""
    
    print("🔧 Clipboard Solution Test for AURA")
    print("Testing alternative to problematic Return key typing")
    print("=" * 60)
    
    # Test clipboard method
    clipboard_result = test_clipboard_method()
    
    # Compare methods
    return_result, clipboard_result2 = compare_methods()
    
    print("\n" + "=" * 60)
    print("🎯 CLIPBOARD SOLUTION TEST RESULTS")
    print("=" * 60)
    
    print(f"Clipboard method test: {'✅ SUCCESS' if clipboard_result else '❌ FAILED'}")
    print(f"Return key method: {'✅ WORKS' if return_result else '❌ BROKEN'}")
    print(f"Clipboard method comparison: {'✅ WORKS' if clipboard_result2 else '❌ FAILED'}")
    
    if clipboard_result and not return_result:
        print("\n🎉 CLIPBOARD SOLUTION IS THE ANSWER!")
        print("✅ Clipboard method works where Return keys fail")
        print("✅ This explains why AURA's multiline typing isn't working")
        print("✅ The fix is to use clipboard paste for multiline content")
        
        print("\n🔧 Implementation in AURA:")
        print("1. Detect multiline content (>3 lines)")
        print("2. Copy content to clipboard using pbcopy")
        print("3. Paste using Cmd+V with cliclick")
        print("4. Bypass problematic Return key handling")
        
    elif return_result:
        print("\n🤔 Return keys work in this application")
        print("The issue might be specific to the application AURA was typing into")
        print("Try testing AURA in a different text editor")
        
    else:
        print("\n❌ Both methods failed")
        print("There may be a deeper system-level issue")
    
    return clipboard_result

if __name__ == "__main__":
    main()