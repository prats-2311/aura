#!/usr/bin/env python3
"""
Test the fixed clipboard method with correct cliclick syntax.
"""

import subprocess
import time

def test_fixed_clipboard_method():
    """Test the corrected clipboard method."""
    
    print("🔧 Testing Fixed Clipboard Method")
    print("=" * 40)
    print("Testing the corrected cliclick Cmd+V syntax.")
    print("Open a text editor and focus on it, then press Enter...")
    input()
    
    # Test content
    test_content = '''def fibonacci(n):
    if n <= 0:
        return []
    a, b = 0, 1
    result = []
    for _ in range(n):
        result.append(a)
        a, b = b, a + b
    return result

print(fibonacci(10))'''
    
    print(f"Test content: {len(test_content)} chars, {len(test_content.split(chr(10)))} lines")
    
    try:
        # Step 1: Copy to clipboard
        print("Step 1: Copying to clipboard with pbcopy...")
        process = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE, text=True)
        process.communicate(input=test_content)
        
        if process.returncode != 0:
            print("   ❌ Failed to copy to clipboard")
            return False
        
        print("   ✅ Successfully copied to clipboard")
        time.sleep(0.1)
        
        # Step 2: Paste with corrected cliclick syntax
        print("Step 2: Pasting with corrected cliclick Cmd+V...")
        print("   Command: cliclick kd:cmd t:v ku:cmd")
        
        result = subprocess.run(
            ['cliclick', 'kd:cmd', 't:v', 'ku:cmd'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            print(f"   ❌ Paste failed: {result.stderr}")
            return False
        
        print("   ✅ Paste command succeeded")
        
        print("\nFixed clipboard method completed!")
        print("Check your text editor:")
        print("- Do you see properly formatted code?")
        print("- Are there multiple lines with correct indentation?")
        print("- Is there any 'delete' text or corruption?")
        
        response = input("Did the fixed method work correctly? (y/n): ").lower().strip()
        return response.startswith('y')
        
    except Exception as e:
        print(f"❌ Fixed clipboard method failed: {e}")
        return False

def test_cliclick_cmd_v_variants():
    """Test different ways to do Cmd+V with cliclick."""
    
    print("\n🧪 Testing Different Cmd+V Methods")
    print("=" * 40)
    print("Focus on your text editor and press Enter...")
    input()
    
    # Set up test content in clipboard
    test_text = "Clipboard test content"
    process = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE, text=True)
    process.communicate(input=test_text)
    
    methods = [
        (['cliclick', 'kd:cmd', 't:v', 'ku:cmd'], "Single command: kd:cmd t:v ku:cmd"),
        (['cliclick', 'kd:cmd'], ['cliclick', 't:v'], ['cliclick', 'ku:cmd'], "Separate commands"),
    ]
    
    for i, method in enumerate(methods):
        print(f"\nMethod {i+1}: {method[-1]}")
        
        try:
            if isinstance(method[0], list) and len(method) == 2:
                # Single command method
                cmd = method[0]
                print(f"   Command: {' '.join(cmd)}")
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                
                if result.returncode == 0:
                    print("   ✅ Command succeeded")
                else:
                    print(f"   ❌ Command failed: {result.stderr}")
            else:
                # Multiple command method
                commands = method[:-1]  # All but the description
                print(f"   Commands: {[' '.join(cmd) for cmd in commands]}")
                
                for cmd in commands:
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                    if result.returncode != 0:
                        print(f"   ❌ Command failed: {' '.join(cmd)} - {result.stderr}")
                        break
                    time.sleep(0.05)
                else:
                    print("   ✅ All commands succeeded")
                    
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        
        time.sleep(1)  # Pause between methods
    
    print("\nCheck which method successfully pasted the content.")

def main():
    """Test the fixed clipboard implementation."""
    
    print("🔧 Fixed Clipboard Method Test")
    print("Testing corrected cliclick syntax for Cmd+V")
    print("=" * 50)
    
    # Test the fixed method
    fixed_result = test_fixed_clipboard_method()
    
    # Test different variants
    test_cliclick_cmd_v_variants()
    
    print("\n" + "=" * 50)
    print("🎯 FIXED CLIPBOARD METHOD RESULTS")
    print("=" * 50)
    
    if fixed_result:
        print("✅ FIXED CLIPBOARD METHOD WORKS!")
        print("✅ The corrected cliclick syntax resolves the issue")
        print("✅ AURA should now use clipboard method successfully")
        print("✅ No more 'delete' text corruption")
        
        print("\n🎉 Expected AURA behavior:")
        print("1. Detect multiline content (>3 lines)")
        print("2. Copy to clipboard with pbcopy")
        print("3. Paste with: cliclick kd:cmd t:v ku:cmd")
        print("4. Properly formatted code in touch.py")
        
    else:
        print("❌ Fixed clipboard method still has issues")
        print("❌ May need alternative approach")
    
    return fixed_result

if __name__ == "__main__":
    main()